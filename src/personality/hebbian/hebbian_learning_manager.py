"""
Hebbian Learning Manager
Central orchestrator for all Hebbian learning components
Week 10 Day 8-9: Unified interface with safety features

Safety Features (Day 9):
- Learning Quarantine: Patterns must prove themselves over time
- Turn Budget: Hard limits on operations per turn
- Mini-Observability: Visibility into learning events
"""

import time
import json
import hashlib
import logging
import sqlite3
from datetime import datetime, timedelta
from functools import lru_cache
from typing import Dict, List, Optional, Any, Tuple

from .hebbian_vocabulary_associator import HebbianVocabularyAssociator
from .hebbian_dimension_associator import HebbianDimensionAssociator
from .hebbian_sequence_learner import HebbianSequenceLearner
from .hebbian_config import HebbianConfig, HEBBIAN_DEFAULT_CONFIG
from .hebbian_types import CONTEXT_DEFINITIONS, DEFAULT_CONFIDENCE_THRESHOLD

logger = logging.getLogger(__name__)


# ============================================================================
# TURN BUDGET SYSTEM
# ============================================================================

class TurnBudget:
    """
    Enforces per-turn operation limits to prevent latency balloon.

    Prevents runaway learning operations from degrading response time.
    """

    def __init__(
        self,
        max_turn_time_ms: int = 15000,
        max_learning_writes: int = 5,
        max_cache_lookups: int = 20,
        max_db_queries: int = 10
    ):
        # Time budgets
        self.MAX_TURN_TIME_MS = max_turn_time_ms

        # Operation budgets
        self.MAX_LEARNING_WRITES = max_learning_writes
        self.MAX_CACHE_LOOKUPS = max_cache_lookups
        self.MAX_DB_QUERIES = max_db_queries

        # Turn state
        self.turn_start: Optional[float] = None
        self.operations = {
            'writes': 0,
            'lookups': 0,
            'queries': 0
        }

    def start_turn(self) -> None:
        """Begin new turn."""
        self.turn_start = time.time()
        self.operations = {
            'writes': 0,
            'lookups': 0,
            'queries': 0
        }

    def can_write(self) -> bool:
        """Check if more writes allowed."""
        return self.operations['writes'] < self.MAX_LEARNING_WRITES

    def can_lookup(self) -> bool:
        """Check if more cache lookups allowed."""
        return self.operations['lookups'] < self.MAX_CACHE_LOOKUPS

    def can_query(self) -> bool:
        """Check if more DB queries allowed."""
        return self.operations['queries'] < self.MAX_DB_QUERIES

    def record_write(self) -> None:
        """Record a learning write."""
        self.operations['writes'] += 1

    def record_lookup(self) -> None:
        """Record a cache lookup."""
        self.operations['lookups'] += 1

    def record_query(self) -> None:
        """Record a DB query."""
        self.operations['queries'] += 1

    def time_remaining_ms(self) -> int:
        """Get remaining time in milliseconds."""
        if not self.turn_start:
            return self.MAX_TURN_TIME_MS

        elapsed_ms = (time.time() - self.turn_start) * 1000
        return max(0, int(self.MAX_TURN_TIME_MS - elapsed_ms))

    def is_time_exhausted(self) -> bool:
        """Check if turn time budget exhausted."""
        return self.time_remaining_ms() <= 0

    def get_summary(self) -> Dict[str, Any]:
        """Get budget usage summary."""
        return {
            'writes': f"{self.operations['writes']}/{self.MAX_LEARNING_WRITES}",
            'lookups': f"{self.operations['lookups']}/{self.MAX_CACHE_LOOKUPS}",
            'queries': f"{self.operations['queries']}/{self.MAX_DB_QUERIES}",
            'time_remaining_ms': self.time_remaining_ms()
        }


# ============================================================================
# MAIN MANAGER CLASS
# ============================================================================

class HebbianLearningManager:
    """
    Central manager for all Hebbian learning components with safety features.

    Features:
    - Unified interface for all components
    - Performance optimization via caching
    - Learning quarantine (staging -> permanent)
    - Turn budgets (operation limits)
    - Mini-observability (learning reports)

    Example:
        >>> manager = HebbianLearningManager()
        >>> result = manager.process_conversation_turn(
        ...     user_message="ngl this async stuff is confusing",
        ...     assistant_response="I hear you! Let me break it down...",
        ...     context={'formality': 0.3, 'technical_depth': 0.5},
        ...     active_dimensions={'emotional_support_style': 0.8}
        ... )
        >>> print(f"Staging: {result['staging_count']}, Permanent: {result['permanent_count']}")
    """

    def __init__(
        self,
        db_path: str = "data/personality_tracking.db",
        enable_caching: bool = True,
        cache_size: int = 200,
        cache_refresh_interval: int = 100,
        # Safety configuration
        promotion_min_observations: int = 5,
        promotion_min_days: int = 7,
        max_staging_age_days: int = 30,
        turn_budget_max_writes: int = 5,
        turn_budget_max_time_ms: int = 15000
    ):
        """
        Initialize Hebbian learning manager with safety features.

        Args:
            db_path: Path to database
            enable_caching: Whether to use LRU caches for performance
            cache_size: Size of LRU caches
            cache_refresh_interval: Conversations between cache refreshes
            promotion_min_observations: Min observations before promotion
            promotion_min_days: Min days span before promotion
            max_staging_age_days: Max age before staging patterns expire
            turn_budget_max_writes: Max writes per turn
            turn_budget_max_time_ms: Max time per turn in ms
        """
        self.db_path = db_path
        self.enable_caching = enable_caching
        self.cache_size = cache_size
        self.cache_refresh_interval = cache_refresh_interval

        # Initialize components
        self.vocab_associator = HebbianVocabularyAssociator(db_path)
        self.dim_associator = HebbianDimensionAssociator(db_path)
        self.sequence_learner = HebbianSequenceLearner(db_path)

        # State tracking
        self.previous_state: Optional[str] = None
        self.conversation_count = 0

        # Performance tracking
        self._total_latency_ms = 0.0
        self._cache_hits = 0
        self._cache_misses = 0

        # ====================================================================
        # SAFETY SYSTEM 1: Learning Quarantine
        # ====================================================================
        self.staging_patterns: Dict[str, Dict] = {}
        self.permanent_patterns: Dict[str, Dict] = {}

        # Promotion criteria
        self.PROMOTION_MIN_OBSERVATIONS = promotion_min_observations
        self.PROMOTION_MIN_DAYS = promotion_min_days
        self.MAX_STAGING_AGE_DAYS = max_staging_age_days

        # ====================================================================
        # SAFETY SYSTEM 2: Turn Budget
        # ====================================================================
        self.budget = TurnBudget(
            max_turn_time_ms=turn_budget_max_time_ms,
            max_learning_writes=turn_budget_max_writes
        )

        # ====================================================================
        # SAFETY SYSTEM 3: Mini-Observability
        # ====================================================================
        self._promotion_log: List[Dict] = []
        self._recent_events: List[Dict] = []
        self._max_event_history = 100

        # Initialize caches
        self._init_caches()

        # Initialize safety tables and load staging patterns
        self._init_safety_tables()
        self._load_staging_patterns()
        self._load_permanent_patterns()

        logger.info(
            f"HebbianLearningManager initialized "
            f"(caching={enable_caching}, quarantine=enabled, budget=enabled)"
        )

    def _init_caches(self) -> None:
        """Initialize LRU caches with configured size"""
        if self.enable_caching:
            self.should_use_term_cached = lru_cache(maxsize=self.cache_size)(
                self._should_use_term_impl
            )
            self.predict_coactivations_cached = lru_cache(maxsize=self.cache_size // 4)(
                self._predict_coactivations_impl
            )

    def _init_safety_tables(self) -> None:
        """Initialize safety-related database tables"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Staging patterns table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS hebbian_staging_patterns (
                        pattern_key TEXT PRIMARY KEY,
                        pattern_type TEXT NOT NULL,
                        pattern_data TEXT NOT NULL,
                        observation_count INTEGER DEFAULT 0,
                        first_seen TIMESTAMP NOT NULL,
                        last_seen TIMESTAMP NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)

                # Permanent patterns table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS hebbian_permanent_patterns (
                        pattern_key TEXT PRIMARY KEY,
                        pattern_type TEXT NOT NULL,
                        pattern_data TEXT NOT NULL,
                        observation_count INTEGER NOT NULL,
                        first_seen TIMESTAMP NOT NULL,
                        last_seen TIMESTAMP NOT NULL,
                        promoted_at TIMESTAMP NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)

                # Promotion log
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS hebbian_promotion_log (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        pattern_key TEXT NOT NULL,
                        pattern_type TEXT NOT NULL,
                        observation_count INTEGER NOT NULL,
                        days_span INTEGER NOT NULL,
                        promoted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)

                # Create indexes
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_staging_type
                    ON hebbian_staging_patterns(pattern_type)
                """)
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_staging_first_seen
                    ON hebbian_staging_patterns(first_seen)
                """)
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_permanent_type
                    ON hebbian_permanent_patterns(pattern_type)
                """)
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_promotion_log_time
                    ON hebbian_promotion_log(promoted_at)
                """)

                conn.commit()
        except Exception as e:
            logger.warning(f"Could not initialize safety tables: {e}")

    # ========================================================================
    # MAIN PROCESSING METHOD (with safety)
    # ========================================================================

    def process_conversation_turn(
        self,
        user_message: str,
        assistant_response: str,
        context: Optional[Dict[str, Any]] = None,
        active_dimensions: Optional[Dict[str, float]] = None,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process a complete conversation turn with safety features.

        This is the main entry point for Hebbian learning updates.
        Patterns go to staging first, then promote after proving themselves.

        Args:
            user_message: User's message
            assistant_response: Assistant's response
            context: Conversation context (formality, technical_depth, etc.)
            active_dimensions: Current personality dimension values
            session_id: Optional session identifier

        Returns:
            Dict with learning updates, predictions, and safety stats
        """
        # Start turn budget
        self.budget.start_turn()
        start_time = time.time()

        context = context or {}
        active_dimensions = active_dimensions or {}

        result = {
            'vocab_observations': 0,
            'coactivations_updated': 0,
            'state_transitions': 0,
            'current_state': None,
            'predictions': {},
            'latency_ms': 0,
            # Safety stats
            'staging_count': len(self.staging_patterns),
            'permanent_count': len(self.permanent_patterns),
            'promotions_this_turn': 0,
            'budget_summary': {}
        }

        try:
            # 1. Classify conversation state
            conversation_state = self.sequence_learner.classify_conversation_state(
                user_message, context
            )
            result['current_state'] = conversation_state

            # 2. Determine context type for vocabulary
            context_type = self._determine_context_type(user_message, context)

            # 3. Extract and learn patterns (with budget checks)
            patterns_learned = 0

            # Vocabulary patterns
            if self.budget.can_write():
                vocab_pattern = self._extract_vocabulary_pattern(
                    user_message, context_type
                )
                if vocab_pattern:
                    self._observe_to_staging('vocabulary', vocab_pattern, context)
                    self.budget.record_write()
                    patterns_learned += 1

            # Dimension patterns
            if active_dimensions and self.budget.can_write():
                dim_pattern = self._extract_dimension_pattern(active_dimensions)
                if dim_pattern:
                    self._observe_to_staging('dimension', dim_pattern, context)
                    self.budget.record_write()
                    patterns_learned += 1

            # Sequence patterns
            if self.previous_state and self.budget.can_write():
                seq_pattern = self._extract_sequence_pattern(
                    self.previous_state, conversation_state
                )
                if seq_pattern:
                    self._observe_to_staging('sequence', seq_pattern, context)
                    self.budget.record_write()
                    patterns_learned += 1

            result['vocab_observations'] = patterns_learned

            # 4. Also update underlying components (direct learning)
            if self.budget.can_write():
                observed_terms = self.vocab_associator.observe_conversation(
                    user_message, context_type, session_id
                )
                result['vocab_observations'] = len(observed_terms)

            if active_dimensions and self.budget.can_write():
                updates = self.dim_associator.observe_activations(
                    active_dimensions, session_id
                )
                result['coactivations_updated'] = updates

            if self.previous_state and self.budget.can_write():
                self.sequence_learner.observe_transition(
                    self.previous_state,
                    conversation_state,
                    session_id=session_id
                )
                result['state_transitions'] = 1

            self.previous_state = conversation_state

            # 5. Check for promotions (staging -> permanent)
            promoted = self._check_promotions()
            result['promotions_this_turn'] = len(promoted)

            # 6. Generate predictions for next turn
            result['predictions'] = self._generate_predictions(
                conversation_state, active_dimensions
            )

            # 7. Update statistics
            self.conversation_count += 1

            # 8. Refresh caches if needed
            if self.enable_caching and self.conversation_count % self.cache_refresh_interval == 0:
                self.refresh_caches()

            # 9. Update counts
            result['staging_count'] = len(self.staging_patterns)
            result['permanent_count'] = len(self.permanent_patterns)

        except Exception as e:
            logger.error(f"Error processing conversation turn: {e}")
            result['error'] = str(e)

        result['latency_ms'] = (time.time() - start_time) * 1000
        result['budget_summary'] = self.budget.get_summary()
        self._total_latency_ms += result['latency_ms']

        # Log event for observability
        self._log_event('conversation_turn', {
            'patterns_learned': patterns_learned,
            'promotions': result['promotions_this_turn'],
            'latency_ms': result['latency_ms']
        })

        return result

    # ========================================================================
    # PATTERN EXTRACTION
    # ========================================================================

    def _extract_vocabulary_pattern(
        self,
        message: str,
        context_type: str
    ) -> Optional[Dict]:
        """Extract vocabulary pattern from message."""
        words = message.lower().split()
        if len(words) < 2:
            return None

        # Extract meaningful terms (skip common words)
        meaningful = [w for w in words if len(w) > 2]
        if not meaningful:
            return None

        return {
            'terms': meaningful[:5],  # Top 5 terms
            'context_type': context_type
        }

    def _extract_dimension_pattern(
        self,
        dimensions: Dict[str, float]
    ) -> Optional[Dict]:
        """Extract dimension co-activation pattern."""
        # Only track non-neutral dimensions
        active = {
            k: v for k, v in dimensions.items()
            if abs(v - 0.5) > 0.15
        }

        if len(active) < 2:
            return None

        return {
            'dimensions': active
        }

    def _extract_sequence_pattern(
        self,
        from_state: str,
        to_state: str
    ) -> Optional[Dict]:
        """Extract sequence transition pattern."""
        return {
            'from_state': from_state,
            'to_state': to_state
        }

    # ========================================================================
    # LEARNING QUARANTINE SYSTEM
    # ========================================================================

    def _observe_to_staging(
        self,
        pattern_type: str,
        pattern: Dict,
        context: Dict
    ) -> None:
        """Add observation to staging (quarantine)."""
        # Create unique key for pattern
        pattern_key = f"{pattern_type}:{self._pattern_hash(pattern)}"

        now = datetime.now()

        # Initialize staging entry if new
        if pattern_key not in self.staging_patterns:
            self.staging_patterns[pattern_key] = {
                'pattern_type': pattern_type,
                'pattern': pattern,
                'observations': [],
                'first_seen': now,
                'last_seen': now
            }

        # Add observation
        self.staging_patterns[pattern_key]['observations'].append({
            'timestamp': now,
            'context': context
        })
        self.staging_patterns[pattern_key]['last_seen'] = now

        # Persist to database
        self._save_staging_pattern(pattern_key)

    def _check_promotions(self) -> List[str]:
        """Check if staging patterns should be promoted to permanent."""
        promoted = []
        expired = []

        for key, staging in list(self.staging_patterns.items()):
            # Check promotion criteria
            if self._should_promote(staging):
                self._promote_to_permanent(key, staging)
                promoted.append(key)

            # Check expiration
            elif self._should_expire(staging):
                expired.append(key)

        # Clean up expired
        for key in expired:
            self._expire_staging_pattern(key)

        return promoted

    def _should_promote(self, staging: Dict) -> bool:
        """Check if pattern meets promotion criteria."""
        # Criterion 1: Minimum observations
        if len(staging['observations']) < self.PROMOTION_MIN_OBSERVATIONS:
            return False

        # Criterion 2: Minimum time span
        days_span = self._days_span(staging)
        if days_span < self.PROMOTION_MIN_DAYS:
            return False

        # Criterion 3: Observations distributed over time
        observation_dates = set(
            obs['timestamp'].date() if isinstance(obs['timestamp'], datetime)
            else datetime.fromisoformat(str(obs['timestamp'])).date()
            for obs in staging['observations']
        )
        if len(observation_dates) < 3:  # Need observations on 3+ different days
            return False

        return True

    def _should_expire(self, staging: Dict) -> bool:
        """Check if staging pattern should be removed."""
        first_seen = staging['first_seen']
        if isinstance(first_seen, str):
            first_seen = datetime.fromisoformat(first_seen)

        age_days = (datetime.now() - first_seen).days
        return age_days > self.MAX_STAGING_AGE_DAYS

    def _promote_to_permanent(self, key: str, staging: Dict) -> None:
        """Move pattern from staging to permanent."""
        now = datetime.now()

        # Add promotion metadata
        staging['promoted_at'] = now

        # Move to permanent
        self.permanent_patterns[key] = staging

        # Remove from staging
        del self.staging_patterns[key]

        # Persist to database
        self._save_permanent_pattern(key)
        self._delete_staging_pattern(key)

        # Log promotion
        promotion_record = {
            'pattern_key': key,
            'pattern_type': staging['pattern_type'],
            'observation_count': len(staging['observations']),
            'days_span': self._days_span(staging),
            'promoted_at': now
        }
        self._promotion_log.append(promotion_record)
        self._log_promotion(promotion_record)

        logger.info(
            f"Promoted pattern: {key} "
            f"(observations={len(staging['observations'])}, "
            f"days={self._days_span(staging)})"
        )

    def _expire_staging_pattern(self, key: str) -> None:
        """Remove expired staging pattern."""
        if key in self.staging_patterns:
            del self.staging_patterns[key]
        self._delete_staging_pattern(key)
        logger.info(f"Expired staging pattern: {key}")

    def _pattern_hash(self, pattern: Dict) -> str:
        """Create unique hash for pattern."""
        return hashlib.md5(
            json.dumps(pattern, sort_keys=True, default=str).encode()
        ).hexdigest()[:8]

    def _days_span(self, staging: Dict) -> int:
        """Calculate days between first and last observation."""
        first = staging['first_seen']
        last = staging['last_seen']

        if isinstance(first, str):
            first = datetime.fromisoformat(first)
        if isinstance(last, str):
            last = datetime.fromisoformat(last)

        return (last - first).days

    # ========================================================================
    # DATABASE PERSISTENCE FOR QUARANTINE
    # ========================================================================

    def _load_staging_patterns(self) -> None:
        """Load staging patterns from database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT pattern_key, pattern_type, pattern_data,
                           observation_count, first_seen, last_seen
                    FROM hebbian_staging_patterns
                """)

                for row in cursor.fetchall():
                    key, ptype, pdata, obs_count, first, last = row
                    self.staging_patterns[key] = {
                        'pattern_type': ptype,
                        'pattern': json.loads(pdata),
                        'observations': [{}] * obs_count,  # Placeholder
                        'first_seen': datetime.fromisoformat(first) if first else datetime.now(),
                        'last_seen': datetime.fromisoformat(last) if last else datetime.now()
                    }
        except Exception as e:
            logger.debug(f"Could not load staging patterns: {e}")

    def _load_permanent_patterns(self) -> None:
        """Load permanent patterns from database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT pattern_key, pattern_type, pattern_data,
                           observation_count, first_seen, last_seen, promoted_at
                    FROM hebbian_permanent_patterns
                """)

                for row in cursor.fetchall():
                    key, ptype, pdata, obs_count, first, last, promoted = row
                    self.permanent_patterns[key] = {
                        'pattern_type': ptype,
                        'pattern': json.loads(pdata),
                        'observations': [{}] * obs_count,
                        'first_seen': datetime.fromisoformat(first) if first else datetime.now(),
                        'last_seen': datetime.fromisoformat(last) if last else datetime.now(),
                        'promoted_at': datetime.fromisoformat(promoted) if promoted else datetime.now()
                    }
        except Exception as e:
            logger.debug(f"Could not load permanent patterns: {e}")

    def _save_staging_pattern(self, key: str) -> None:
        """Save staging pattern to database."""
        try:
            staging = self.staging_patterns.get(key)
            if not staging:
                return

            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO hebbian_staging_patterns
                    (pattern_key, pattern_type, pattern_data, observation_count,
                     first_seen, last_seen)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    key,
                    staging['pattern_type'],
                    json.dumps(staging['pattern'], default=str),
                    len(staging['observations']),
                    staging['first_seen'].isoformat() if isinstance(staging['first_seen'], datetime) else staging['first_seen'],
                    staging['last_seen'].isoformat() if isinstance(staging['last_seen'], datetime) else staging['last_seen']
                ))
                conn.commit()
        except Exception as e:
            logger.warning(f"Could not save staging pattern: {e}")

    def _save_permanent_pattern(self, key: str) -> None:
        """Save permanent pattern to database."""
        try:
            pattern = self.permanent_patterns.get(key)
            if not pattern:
                return

            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO hebbian_permanent_patterns
                    (pattern_key, pattern_type, pattern_data, observation_count,
                     first_seen, last_seen, promoted_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    key,
                    pattern['pattern_type'],
                    json.dumps(pattern['pattern'], default=str),
                    len(pattern['observations']),
                    pattern['first_seen'].isoformat() if isinstance(pattern['first_seen'], datetime) else pattern['first_seen'],
                    pattern['last_seen'].isoformat() if isinstance(pattern['last_seen'], datetime) else pattern['last_seen'],
                    pattern['promoted_at'].isoformat() if isinstance(pattern.get('promoted_at'), datetime) else pattern.get('promoted_at', datetime.now().isoformat())
                ))
                conn.commit()
        except Exception as e:
            logger.warning(f"Could not save permanent pattern: {e}")

    def _delete_staging_pattern(self, key: str) -> None:
        """Delete staging pattern from database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "DELETE FROM hebbian_staging_patterns WHERE pattern_key = ?",
                    (key,)
                )
                conn.commit()
        except Exception as e:
            logger.warning(f"Could not delete staging pattern: {e}")

    def _log_promotion(self, record: Dict) -> None:
        """Log promotion to database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO hebbian_promotion_log
                    (pattern_key, pattern_type, observation_count, days_span, promoted_at)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    record['pattern_key'],
                    record['pattern_type'],
                    record['observation_count'],
                    record['days_span'],
                    record['promoted_at'].isoformat() if isinstance(record['promoted_at'], datetime) else record['promoted_at']
                ))
                conn.commit()
        except Exception as e:
            logger.warning(f"Could not log promotion: {e}")

    # ========================================================================
    # MINI-OBSERVABILITY SYSTEM
    # ========================================================================

    def _log_event(self, event_type: str, data: Dict) -> None:
        """Log event for observability."""
        event = {
            'timestamp': datetime.now(),
            'type': event_type,
            'data': data
        }
        self._recent_events.append(event)

        # Keep only recent events
        if len(self._recent_events) > self._max_event_history:
            self._recent_events = self._recent_events[-self._max_event_history:]

    def get_learning_report(self, last_n: int = 20) -> Dict[str, Any]:
        """
        Generate mini-observability report.

        Returns:
            Dict with summary, recent events, and drift warnings
        """
        return {
            'summary': {
                'staging_patterns': len(self.staging_patterns),
                'permanent_patterns': len(self.permanent_patterns),
                'total_observations': self._count_total_observations(),
                'conversation_count': self.conversation_count
            },
            'recent_events': self._get_recent_events(last_n),
            'recent_promotions': self._get_recent_promotions(last_n),
            'drift_warnings': self._check_drift(),
            'top_staging_patterns': self._get_top_staging_patterns(10)
        }

    def _count_total_observations(self) -> int:
        """Count all observations across staging + permanent."""
        total = 0
        for pattern in self.staging_patterns.values():
            total += len(pattern.get('observations', []))
        for pattern in self.permanent_patterns.values():
            total += len(pattern.get('observations', []))
        return total

    def _get_recent_events(self, n: int) -> List[Dict]:
        """Get last N learning events."""
        events = []

        # Add recent internal events
        for event in self._recent_events[-n:]:
            events.append({
                'timestamp': event['timestamp'].isoformat() if isinstance(event['timestamp'], datetime) else event['timestamp'],
                'type': event['type'],
                'data': event['data']
            })

        return events[-n:]

    def _get_recent_promotions(self, n: int) -> List[Dict]:
        """Get last N promotions."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT pattern_key, pattern_type, observation_count,
                           days_span, promoted_at
                    FROM hebbian_promotion_log
                    ORDER BY promoted_at DESC
                    LIMIT ?
                """, (n,))

                return [
                    {
                        'pattern_key': row[0],
                        'pattern_type': row[1],
                        'observation_count': row[2],
                        'days_span': row[3],
                        'promoted_at': row[4]
                    }
                    for row in cursor.fetchall()
                ]
        except Exception:
            return self._promotion_log[-n:]

    def _check_drift(self) -> List[str]:
        """Detect potential drift indicators."""
        warnings = []

        # Warning 1: Too many staging patterns
        if len(self.staging_patterns) > 100:
            warnings.append(
                f"High staging count: {len(self.staging_patterns)} patterns "
                f"(threshold: 100)"
            )

        # Warning 2: Low promotion rate
        total_patterns = len(self.staging_patterns) + len(self.permanent_patterns)
        if total_patterns > 0 and len(self.permanent_patterns) > 0:
            promotion_rate = len(self.permanent_patterns) / total_patterns
            if promotion_rate < 0.1:
                warnings.append(
                    f"Low promotion rate: {promotion_rate:.1%} "
                    f"(threshold: 10%)"
                )

        # Warning 3: Old staging patterns not expiring
        old_staging = [
            s for s in self.staging_patterns.values()
            if self._days_span(s) > 20
        ]
        if len(old_staging) > 10:
            warnings.append(
                f"{len(old_staging)} staging patterns > 20 days old "
                f"(not promoting or expiring)"
            )

        return warnings

    def _get_top_staging_patterns(self, n: int) -> List[Dict]:
        """Get top N staging patterns by observation count."""
        patterns = [
            {
                'key': key,
                'type': p['pattern_type'],
                'observations': len(p.get('observations', [])),
                'days_old': self._days_span(p),
                'close_to_promotion': self._promotion_progress(p)
            }
            for key, p in self.staging_patterns.items()
        ]

        patterns.sort(key=lambda x: x['observations'], reverse=True)
        return patterns[:n]

    def _promotion_progress(self, staging: Dict) -> str:
        """Calculate how close pattern is to promotion."""
        obs_count = len(staging.get('observations', []))
        days_span = self._days_span(staging)

        obs_progress = f"{obs_count}/{self.PROMOTION_MIN_OBSERVATIONS}"
        days_progress = f"{days_span}/{self.PROMOTION_MIN_DAYS}"

        return f"obs:{obs_progress} days:{days_progress}"

    def export_learning_log(self, filepath: str) -> None:
        """Export complete learning log for analysis."""
        log = {
            'export_metadata': {
                'timestamp': datetime.now().isoformat(),
                'staging_count': len(self.staging_patterns),
                'permanent_count': len(self.permanent_patterns),
                'conversation_count': self.conversation_count
            },
            'staging_patterns': self._serialize_patterns(self.staging_patterns),
            'permanent_patterns': self._serialize_patterns(self.permanent_patterns),
            'drift_warnings': self._check_drift(),
            'recent_promotions': self._get_recent_promotions(20)
        }

        with open(filepath, 'w') as f:
            json.dump(log, f, indent=2, default=str)

        logger.info(f"Exported learning log to {filepath}")

    def _serialize_patterns(self, patterns: Dict) -> Dict:
        """Serialize patterns for JSON export."""
        return {
            key: {
                'pattern_type': p['pattern_type'],
                'observation_count': len(p.get('observations', [])),
                'first_seen': p['first_seen'].isoformat() if isinstance(p['first_seen'], datetime) else p['first_seen'],
                'last_seen': p['last_seen'].isoformat() if isinstance(p['last_seen'], datetime) else p['last_seen'],
                'days_span': self._days_span(p)
            }
            for key, p in patterns.items()
        }

    # ========================================================================
    # ORIGINAL METHODS (preserved from Day 8)
    # ========================================================================

    def _generate_predictions(
        self,
        current_state: str,
        active_dimensions: Dict[str, float]
    ) -> Dict[str, Any]:
        """Generate predictions for next turn"""
        predictions = {}

        try:
            # Predict next states
            next_states = self.sequence_learner.predict_next_states(
                current_state,
                self.sequence_learner.conversation_history,
                n=3
            )
            predictions['next_states'] = next_states

            # Predict co-activations for high-confidence dimensions
            high_confidence_dims = {
                k: v for k, v in active_dimensions.items()
                if abs(v - 0.5) > 0.15
            }
            if high_confidence_dims:
                coact_predictions = self.dim_associator.predict_coactivations(
                    high_confidence_dims,
                    threshold=0.15
                )
                predictions['coactivations'] = {
                    dim: {
                        'predicted_value': pred.predicted_value,
                        'confidence': pred.confidence
                    }
                    for dim, pred in coact_predictions.items()
                }
            else:
                predictions['coactivations'] = {}

            # Anticipate user need
            anticipation = self.sequence_learner.anticipate_user_need(
                current_state,
                self.sequence_learner.conversation_history
            )
            if anticipation:
                predictions['anticipation'] = {
                    'suggested_action': anticipation.suggested_action,
                    'confidence': anticipation.confidence
                }

        except Exception as e:
            logger.warning(f"Error generating predictions: {e}")

        return predictions

    def _determine_context_type(
        self,
        user_message: str,
        context: Dict[str, Any]
    ) -> str:
        """Determine conversation context type for vocabulary association"""
        message_lower = user_message.lower()
        formality = context.get('formality', 0.5)
        technical = context.get('technical_depth', 0.5)

        if any(word in message_lower for word in ['stressed', 'confused', 'frustrated', 'help', 'struggling']):
            return 'emotional_support'

        if any(word in message_lower for word in ['stuck', 'error', 'broken', 'bug', 'issue', 'problem']):
            return 'problem_solving'

        if any(word in message_lower for word in ['quick', 'briefly', 'tldr', 'short', 'summary']):
            return 'quick_query'

        if any(word in message_lower for word in ['idea', 'what if', 'thinking', 'brainstorm', 'design']):
            return 'creative_discussion'

        if formality > 0.7 and technical > 0.6:
            return 'formal_technical'
        elif formality < 0.4 and technical < 0.5:
            return 'casual_chat'

        casual_indicators = ['yo', 'ngl', 'tbh', 'lol', 'dude', 'honestly', 'kinda', 'sorta']
        if any(word in message_lower for word in casual_indicators):
            return 'casual_chat'

        return 'creative_discussion'

    # ========================================================================
    # CACHED QUERY METHODS
    # ========================================================================

    def _should_use_term_impl(
        self,
        term: str,
        context: str,
        threshold: float = DEFAULT_CONFIDENCE_THRESHOLD
    ) -> bool:
        """Internal implementation for cached term lookup"""
        return self.vocab_associator.should_use_term(term, context, threshold)

    def _predict_coactivations_impl(
        self,
        known_dims_tuple: Tuple[Tuple[str, float], ...],
        threshold: float = DEFAULT_CONFIDENCE_THRESHOLD
    ) -> Dict[str, Any]:
        """Internal implementation for cached coactivation prediction"""
        known_dims = dict(known_dims_tuple)
        predictions = self.dim_associator.predict_coactivations(known_dims, threshold)
        return {
            dim: {
                'predicted_value': pred.predicted_value,
                'confidence': pred.confidence,
                'sources': pred.sources
            }
            for dim, pred in predictions.items()
        }

    def should_use_term(
        self,
        term: str,
        context: str,
        threshold: float = DEFAULT_CONFIDENCE_THRESHOLD
    ) -> bool:
        """Check if term should be used in context (with caching)"""
        if self.enable_caching:
            self.budget.record_lookup()
            return self.should_use_term_cached(term, context, threshold)
        return self._should_use_term_impl(term, context, threshold)

    def predict_coactivations(
        self,
        known_dimensions: Dict[str, float],
        threshold: float = DEFAULT_CONFIDENCE_THRESHOLD
    ) -> Dict[str, Any]:
        """Predict coactivations (with caching)"""
        if self.enable_caching:
            dims_tuple = tuple(sorted(known_dimensions.items()))
            return self.predict_coactivations_cached(dims_tuple, threshold)
        return self._predict_coactivations_impl(
            tuple(sorted(known_dimensions.items())), threshold
        )

    # ========================================================================
    # MAINTENANCE METHODS
    # ========================================================================

    def apply_temporal_decay_all(
        self,
        days_inactive: float = 1.0
    ) -> Dict[str, int]:
        """Apply temporal decay to all components"""
        results = {
            'vocab_associations': self.vocab_associator.apply_temporal_decay(days_inactive),
            'transitions': self.sequence_learner.apply_temporal_decay(days_inactive)
        }
        logger.info(f"Applied temporal decay: {results}")
        return results

    def refresh_caches(self) -> None:
        """Refresh all caches (call periodically)"""
        if self.enable_caching:
            try:
                self.should_use_term_cached.cache_clear()
                self.predict_coactivations_cached.cache_clear()
                logger.debug("Hebbian caches refreshed")
            except AttributeError:
                pass

    def prune_all(
        self,
        min_strength: float = 0.1,
        min_observations: int = 2
    ) -> Dict[str, int]:
        """Prune weak data from all components"""
        results = {
            'vocab_associations': self.vocab_associator.prune_weak_associations(
                min_strength, min_observations
            )
        }
        logger.info(f"Pruned weak associations: {results}")
        return results

    def reset_session(self) -> None:
        """Reset session state (call at start of new conversation)"""
        self.previous_state = None
        self.sequence_learner.reset_history()
        logger.debug("Session reset")

    # ========================================================================
    # EXPORT & MONITORING METHODS
    # ========================================================================

    def export_all_data(self) -> Dict[str, Any]:
        """Export all Hebbian learning data"""
        return {
            'vocab_associations': self.vocab_associator.export_association_matrix(),
            'coactivations': self.dim_associator.export_coactivation_matrix(),
            'transitions': self.sequence_learner.export_transition_matrix(),
            'staging_patterns': self._serialize_patterns(self.staging_patterns),
            'permanent_patterns': self._serialize_patterns(self.permanent_patterns)
        }

    def get_system_stats(self) -> Dict[str, Any]:
        """Get comprehensive statistics about Hebbian learning system"""
        return {
            'vocab': self.vocab_associator.get_statistics(),
            'dimensions': self.dim_associator.get_statistics(),
            'sequences': self.sequence_learner.get_statistics(),
            'safety': {
                'staging_patterns': len(self.staging_patterns),
                'permanent_patterns': len(self.permanent_patterns),
                'promotion_min_observations': self.PROMOTION_MIN_OBSERVATIONS,
                'promotion_min_days': self.PROMOTION_MIN_DAYS
            },
            'performance': {
                'conversation_count': self.conversation_count,
                'caching_enabled': self.enable_caching,
                'avg_latency_ms': (
                    self._total_latency_ms / self.conversation_count
                    if self.conversation_count > 0 else 0
                ),
                'cache_refresh_interval': self.cache_refresh_interval
            }
        }

    def get_health_summary(self) -> Dict[str, Any]:
        """Get system health summary (for dashboard/monitoring)"""
        health = {
            'status': 'healthy',
            'components': {
                'vocab_associator': 'ok',
                'dim_associator': 'ok',
                'sequence_learner': 'ok',
                'quarantine_system': 'ok',
                'turn_budget': 'ok'
            },
            'issues': [],
            'drift_warnings': self._check_drift()
        }

        # Check vocab associator
        try:
            vocab_stats = self.vocab_associator.get_statistics()
            if vocab_stats.get('total_associations', 0) == 0:
                health['components']['vocab_associator'] = 'no_data'
        except Exception as e:
            health['components']['vocab_associator'] = 'error'
            health['issues'].append(f"Vocab: {str(e)}")

        # Check dimension associator
        try:
            dim_stats = self.dim_associator.get_statistics()
            if dim_stats.get('total_coactivations', 0) == 0:
                health['components']['dim_associator'] = 'no_data'
        except Exception as e:
            health['components']['dim_associator'] = 'error'
            health['issues'].append(f"Dim: {str(e)}")

        # Check sequence learner
        try:
            seq_stats = self.sequence_learner.get_statistics()
            if seq_stats.get('total_transitions', 0) == 0:
                health['components']['sequence_learner'] = 'no_data'
        except Exception as e:
            health['components']['sequence_learner'] = 'error'
            health['issues'].append(f"Seq: {str(e)}")

        # Add drift warnings to issues
        health['issues'].extend(health['drift_warnings'])

        # Overall status
        if any(v == 'error' for v in health['components'].values()):
            health['status'] = 'degraded'
        elif all(v == 'no_data' for v in health['components'].values()):
            health['status'] = 'initializing'
        elif health['drift_warnings']:
            health['status'] = 'warning'

        return health

    # ========================================================================
    # CONVENIENCE METHODS
    # ========================================================================

    def get_vocabulary_for_context(
        self,
        context: str,
        min_strength: float = DEFAULT_CONFIDENCE_THRESHOLD,
        limit: int = 20
    ) -> List[Tuple[str, float]]:
        """Get recommended vocabulary for a context"""
        return self.vocab_associator.get_terms_for_context(context, min_strength, limit)

    def get_dimension_predictions_for(
        self,
        known_dimension: str,
        value: float
    ) -> Dict[str, Any]:
        """Get dimension predictions given a single known dimension"""
        return self.predict_coactivations({known_dimension: value})

    def get_likely_next_states(
        self,
        current_state: Optional[str] = None,
        n: int = 3
    ) -> List[Tuple[str, float]]:
        """Get likely next conversation states"""
        state = current_state or self.previous_state or 'casual_chat'
        return self.sequence_learner.predict_next_states(
            state,
            self.sequence_learner.conversation_history,
            n
        )
