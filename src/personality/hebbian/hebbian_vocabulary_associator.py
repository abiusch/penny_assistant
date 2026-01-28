"""
Hebbian Vocabulary Associator
Learns which vocabulary terms belong in which conversational contexts
through Hebbian learning with competitive inhibition
"""

import sqlite3
import re
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Set
from collections import defaultdict
from functools import lru_cache
import logging

from .hebbian_types import (
    VocabularyAssociation,
    VocabularyObservation,
    ContextType,
    CONTEXT_DEFINITIONS,
    STOPWORDS,
    DEFAULT_LEARNING_RATE,
    DEFAULT_COMPETITIVE_RATE,
    DEFAULT_DECAY_RATE_PER_DAY,
    DEFAULT_CONFIDENCE_THRESHOLD
)

logger = logging.getLogger(__name__)


class HebbianVocabularyAssociator:
    """
    Learns vocabulary-context associations through Hebbian learning

    Core Algorithm:
    1. Strengthen association when term appears in context (Hebbian rule)
    2. Weaken competing associations (competitive learning)
    3. Apply temporal decay to unused associations
    4. Provide predictions for term appropriateness

    Example:
        >>> associator = HebbianVocabularyAssociator()
        >>> # Observe "ngl" in casual context
        >>> associator.observe_term_in_context("ngl", "casual_chat")
        >>> # Check if appropriate
        >>> associator.should_use_term("ngl", "casual_chat")
        True
        >>> associator.should_use_term("ngl", "formal_technical")
        False
    """

    def __init__(
        self,
        db_path: str = "data/personality_tracking.db",
        learning_rate: float = DEFAULT_LEARNING_RATE,
        competitive_rate: float = DEFAULT_COMPETITIVE_RATE,
        decay_rate_per_day: float = DEFAULT_DECAY_RATE_PER_DAY
    ):
        """
        Initialize vocabulary associator

        Args:
            db_path: Path to SQLite database
            learning_rate: Rate of association strengthening (0.0-1.0)
            competitive_rate: Rate of competitive weakening (0.0-1.0)
            decay_rate_per_day: Daily decay rate for unused associations
        """
        self.db_path = db_path
        self.learning_rate = learning_rate
        self.competitive_rate = competitive_rate
        self.decay_rate_per_day = decay_rate_per_day

        # All valid context types
        self._context_types = list(CONTEXT_DEFINITIONS.keys())

        # Initialize database
        self._init_db()

        logger.info(f"HebbianVocabularyAssociator initialized (lr={learning_rate})")

    def _init_db(self) -> None:
        """Ensure database tables exist"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            # Tables should already exist from schema, but verify
            cursor.execute("""
                SELECT name FROM sqlite_master
                WHERE type='table' AND name='vocab_associations'
            """)
            if not cursor.fetchone():
                logger.warning("vocab_associations table not found - schema may need to be applied")

    # ========================================================================
    # CORE LEARNING METHODS
    # ========================================================================

    def observe_term_in_context(
        self,
        term: str,
        context: str,
        session_id: Optional[str] = None
    ) -> float:
        """
        Observe term in context, update associations via Hebbian learning

        Algorithm:
        1. Get current strength for term-context pair
        2. Apply Hebbian strengthening: new_strength = old + η * (1 - old)
        3. Apply competitive weakening to other contexts
        4. Update database with new strengths
        5. Log observation

        Args:
            term: The vocabulary term (normalized to lowercase)
            context: The conversation context type
            session_id: Optional session identifier

        Returns:
            float: New association strength
        """
        term = self._normalize_term(term)
        if not term or context not in self._context_types:
            return 0.0

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Get current strength
            current_strength = self._get_strength_from_db(cursor, term, context)

            # Apply Hebbian strengthening: Δw = η * (1 - w)
            # This ensures strength approaches 1.0 asymptotically
            delta = self.learning_rate * (1.0 - current_strength)
            new_strength = self._cap_strength(current_strength + delta)

            # Update or insert the strengthened association
            cursor.execute("""
                INSERT INTO vocab_associations (term, context_type, strength, observation_count, last_updated, first_observed)
                VALUES (?, ?, ?, 1, datetime('now'), datetime('now'))
                ON CONFLICT(term, context_type) DO UPDATE SET
                    strength = ?,
                    observation_count = observation_count + 1,
                    last_updated = datetime('now')
            """, (term, context, new_strength, new_strength))

            # Apply competitive weakening to OTHER contexts
            for other_context in self._context_types:
                if other_context != context:
                    other_strength = self._get_strength_from_db(cursor, term, other_context)
                    if other_strength > 0.0:
                        # Weaken: Δw = -competitive_rate * w
                        weakened = self._cap_strength(other_strength * (1.0 - self.competitive_rate))
                        cursor.execute("""
                            UPDATE vocab_associations
                            SET strength = ?, last_updated = datetime('now')
                            WHERE term = ? AND context_type = ?
                        """, (weakened, term, other_context))

            # Log the observation
            cursor.execute("""
                INSERT INTO vocab_context_observations (term, context_type, timestamp, session_id)
                VALUES (?, ?, datetime('now'), ?)
            """, (term, context, session_id))

            conn.commit()

        return new_strength

    def observe_conversation(
        self,
        user_message: str,
        context: str,
        session_id: Optional[str] = None
    ) -> List[str]:
        """
        Extract terms from message and observe all associations

        Args:
            user_message: User's message text
            context: Conversation context type
            session_id: Optional session identifier

        Returns:
            List of terms observed
        """
        terms = self._extract_terms(user_message)
        observed = []

        for term in terms:
            self.observe_term_in_context(term, context, session_id)
            observed.append(term)

        logger.debug(f"Observed {len(observed)} terms in {context} context")
        return observed

    # ========================================================================
    # QUERY METHODS
    # ========================================================================

    def get_association_strength(
        self,
        term: str,
        context: str
    ) -> float:
        """
        Get current association strength between term and context

        Args:
            term: The vocabulary term
            context: The conversation context type

        Returns:
            float: Association strength (0.0-1.0), default 0.5 if not observed
        """
        term = self._normalize_term(term)
        if not term:
            return 0.5

        # Check for manual override first
        override = self._get_override(term, context)
        if override is not None:
            return override

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            return self._get_strength_from_db(cursor, term, context)

    def should_use_term(
        self,
        term: str,
        context: str,
        threshold: float = DEFAULT_CONFIDENCE_THRESHOLD
    ) -> bool:
        """
        Determine if term is appropriate for context

        Args:
            term: The vocabulary term
            context: The conversation context type
            threshold: Minimum strength to recommend usage

        Returns:
            bool: True if term should be used in this context
        """
        # Check for blocked terms (override with 0.0)
        override = self._get_override(term, context)
        if override is not None and override < 0.1:
            return False

        strength = self.get_association_strength(term, context)
        return strength >= threshold

    def get_top_contexts_for_term(
        self,
        term: str,
        n: int = 3
    ) -> List[Tuple[str, float]]:
        """
        Get top N contexts where term is most appropriate

        Args:
            term: The vocabulary term
            n: Number of top contexts to return

        Returns:
            List of (context, strength) tuples, sorted by strength desc
        """
        term = self._normalize_term(term)
        if not term:
            return []

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT context_type, strength
                FROM vocab_associations
                WHERE term = ?
                ORDER BY strength DESC
                LIMIT ?
            """, (term, n))
            return cursor.fetchall()

    def get_terms_for_context(
        self,
        context: str,
        min_strength: float = DEFAULT_CONFIDENCE_THRESHOLD,
        limit: int = 50
    ) -> List[Tuple[str, float]]:
        """
        Get terms strongly associated with a context

        Args:
            context: The conversation context type
            min_strength: Minimum association strength
            limit: Maximum terms to return

        Returns:
            List of (term, strength) tuples
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT term, strength
                FROM vocab_associations
                WHERE context_type = ? AND strength >= ?
                ORDER BY strength DESC
                LIMIT ?
            """, (context, min_strength, limit))
            return cursor.fetchall()

    # ========================================================================
    # FILTERING METHODS
    # ========================================================================

    def filter_response_vocabulary(
        self,
        response: str,
        context: str,
        threshold: float = DEFAULT_CONFIDENCE_THRESHOLD
    ) -> str:
        """
        Filter out inappropriate vocabulary from response

        This is used to ensure responses don't use slang in formal contexts
        or overly formal language in casual contexts.

        Args:
            response: Assistant's generated response
            context: Conversation context type
            threshold: Minimum strength to allow usage

        Returns:
            str: Filtered response with inappropriate terms handled
        """
        # For now, we don't remove terms but log warnings
        # In production, could replace with alternatives
        terms = self._extract_terms(response)
        flagged = []

        for term in terms:
            strength = self.get_association_strength(term, context)
            # Check if term is strongly associated with a DIFFERENT context
            top_contexts = self.get_top_contexts_for_term(term, n=1)
            if top_contexts:
                top_context, top_strength = top_contexts[0]
                # Flag if term is much stronger in another context
                if top_context != context and top_strength > threshold and strength < 0.4:
                    flagged.append((term, top_context, top_strength))

        if flagged:
            logger.debug(f"Potentially mismatched terms in {context}: {flagged}")

        # Currently return unchanged - could implement replacement logic
        return response

    # ========================================================================
    # MAINTENANCE METHODS
    # ========================================================================

    def apply_temporal_decay(
        self,
        days_inactive: float = 1.0
    ) -> int:
        """
        Apply time-based decay to unused associations

        Decay formula: strength *= (1 - decay_rate * days_inactive)

        Args:
            days_inactive: Number of days since last update for decay

        Returns:
            int: Number of associations decayed
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Calculate decay factor
            decay_factor = 1.0 - (self.decay_rate_per_day * days_inactive)

            # Update associations not updated in last N days
            cursor.execute("""
                UPDATE vocab_associations
                SET strength = MAX(0.0, strength * ?)
                WHERE julianday('now') - julianday(last_updated) >= ?
            """, (decay_factor, days_inactive))

            count = cursor.rowcount
            conn.commit()

        logger.info(f"Applied temporal decay to {count} associations")
        return count

    def prune_weak_associations(
        self,
        min_strength: float = 0.1,
        min_observations: int = 2
    ) -> int:
        """
        Remove weak, rarely-observed associations to save space

        Args:
            min_strength: Minimum strength to keep
            min_observations: Minimum observation count to keep

        Returns:
            int: Number of associations pruned
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                DELETE FROM vocab_associations
                WHERE strength < ? AND observation_count < ?
            """, (min_strength, min_observations))

            count = cursor.rowcount
            conn.commit()

        logger.info(f"Pruned {count} weak associations")
        return count

    # ========================================================================
    # EXPORT & DEBUG METHODS
    # ========================================================================

    def export_association_matrix(self) -> List[Dict]:
        """
        Export all associations for analysis

        Returns:
            List of dicts with keys: term, context, strength, observations
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT term, context_type, strength, observation_count, last_updated
                FROM vocab_associations
                ORDER BY strength DESC
            """)
            return [
                {
                    'term': row[0],
                    'context': row[1],
                    'strength': row[2],
                    'observations': row[3],
                    'last_updated': row[4]
                }
                for row in cursor.fetchall()
            ]

    def get_statistics(self) -> Dict[str, any]:
        """
        Get system statistics

        Returns:
            Dict with counts, averages, etc.
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Total associations
            cursor.execute("SELECT COUNT(*) FROM vocab_associations")
            total = cursor.fetchone()[0]

            # Strong associations
            cursor.execute("""
                SELECT COUNT(*) FROM vocab_associations WHERE strength >= ?
            """, (DEFAULT_CONFIDENCE_THRESHOLD,))
            strong = cursor.fetchone()[0]

            # Average strength
            cursor.execute("SELECT AVG(strength) FROM vocab_associations")
            avg_strength = cursor.fetchone()[0] or 0.0

            # Most observed term
            cursor.execute("""
                SELECT term, SUM(observation_count) as total
                FROM vocab_associations
                GROUP BY term
                ORDER BY total DESC
                LIMIT 1
            """)
            most_observed = cursor.fetchone()

            # Context distribution
            cursor.execute("""
                SELECT context_type, COUNT(*) as count
                FROM vocab_associations
                GROUP BY context_type
            """)
            context_dist = dict(cursor.fetchall())

            return {
                'total_associations': total,
                'strong_associations': strong,
                'average_strength': round(avg_strength, 3),
                'most_observed_term': most_observed[0] if most_observed else None,
                'context_distribution': context_dist
            }

    # ========================================================================
    # OVERRIDE METHODS
    # ========================================================================

    def add_override(
        self,
        term: str,
        context: str,
        strength: float,
        reason: str = ""
    ) -> None:
        """
        Add manual override for a term-context association

        Use this to block inappropriate terms (strength=0.0) or
        force appropriate ones (strength=1.0)

        Args:
            term: The vocabulary term
            context: The conversation context type
            strength: Override strength (0.0-1.0)
            reason: Reason for override
        """
        term = self._normalize_term(term)
        strength = self._cap_strength(strength)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO vocab_overrides
                (term, context_type, override_strength, reason, created_at)
                VALUES (?, ?, ?, ?, datetime('now'))
            """, (term, context, strength, reason))
            conn.commit()

        logger.info(f"Added override: {term}/{context} = {strength} ({reason})")

    def remove_override(self, term: str, context: str) -> bool:
        """
        Remove a manual override

        Args:
            term: The vocabulary term
            context: The conversation context type

        Returns:
            bool: True if override was removed
        """
        term = self._normalize_term(term)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                DELETE FROM vocab_overrides
                WHERE term = ? AND context_type = ?
            """, (term, context))
            removed = cursor.rowcount > 0
            conn.commit()

        return removed

    def _get_override(self, term: str, context: str) -> Optional[float]:
        """Get override strength if exists"""
        term = self._normalize_term(term)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT override_strength FROM vocab_overrides
                WHERE term = ? AND context_type = ?
            """, (term, context))
            result = cursor.fetchone()
            return result[0] if result else None

    # ========================================================================
    # PRIVATE HELPER METHODS
    # ========================================================================

    def _normalize_term(self, term: str) -> str:
        """Normalize term to lowercase, trimmed"""
        if not term:
            return ""
        return term.lower().strip()

    def _cap_strength(self, strength: float) -> float:
        """Cap strength to valid range [0.0, 1.0]"""
        return max(0.0, min(1.0, strength))

    def _extract_terms(self, message: str) -> List[str]:
        """Extract terms from message (tokenize, filter)"""
        if not message:
            return []

        # Tokenize on whitespace and punctuation
        tokens = re.findall(r'\b[a-zA-Z]+\b', message.lower())

        # Filter stopwords and very short terms
        terms = [
            t for t in tokens
            if t not in STOPWORDS and len(t) >= 2
        ]

        return terms

    def _get_strength_from_db(
        self,
        cursor: sqlite3.Cursor,
        term: str,
        context: str
    ) -> float:
        """Get strength from database, default 0.5 if not found"""
        cursor.execute("""
            SELECT strength FROM vocab_associations
            WHERE term = ? AND context_type = ?
        """, (term, context))
        result = cursor.fetchone()
        return result[0] if result else 0.5

    def _get_all_contexts(self) -> List[str]:
        """Get list of all context types"""
        return self._context_types.copy()
