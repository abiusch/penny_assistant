#!/usr/bin/env python3
"""
Security Decision Cache System
Advanced caching for repeated security scenarios with intelligent invalidation
"""

import hashlib
import json
import logging
import sqlite3
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Set, Union
from dataclasses import dataclass, asdict
from enum import Enum
import pickle
import zlib

class CacheEvictionPolicy(Enum):
    """Cache eviction policies"""
    LRU = "lru"          # Least Recently Used
    LFU = "lfu"          # Least Frequently Used
    TTL = "ttl"          # Time To Live
    PRIORITY = "priority" # Priority-based
    ADAPTIVE = "adaptive" # Adaptive based on access patterns

class CacheEntryStatus(Enum):
    """Status of cache entries"""
    ACTIVE = "active"
    EXPIRED = "expired"
    INVALIDATED = "invalidated"
    PENDING = "pending"
    ERROR = "error"

class DecisionConfidence(Enum):
    """Confidence levels for cached decisions"""
    VERY_HIGH = "very_high"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNCERTAIN = "uncertain"

@dataclass
class CacheKey:
    """Structured cache key for security decisions"""
    operation: str
    parameters_hash: str
    user_context_hash: str
    session_context_hash: str
    security_level: str

    def to_string(self) -> str:
        """Convert to string representation"""
        return f"{self.operation}:{self.parameters_hash}:{self.user_context_hash}:{self.session_context_hash}:{self.security_level}"

@dataclass
class SecurityCacheEntry:
    """Cache entry for security decisions"""
    key: CacheKey
    decision: str
    confidence: DecisionConfidence
    reasoning: str
    alternatives: List[str]
    restrictions: List[str]
    metadata: Dict[str, Any]

    # Cache management
    created_at: datetime
    last_accessed: datetime
    access_count: int
    ttl_seconds: int
    priority: int
    status: CacheEntryStatus

    # Security attributes
    security_context: Dict[str, Any]
    invalidation_triggers: List[str]
    requires_revalidation: bool
    original_processing_time_ms: float

    def is_expired(self) -> bool:
        """Check if entry is expired"""
        if self.ttl_seconds <= 0:
            return False
        return (datetime.now() - self.created_at).total_seconds() > self.ttl_seconds

    def is_valid(self) -> bool:
        """Check if entry is valid for use"""
        return (self.status == CacheEntryStatus.ACTIVE and
                not self.is_expired() and
                not self.requires_revalidation)

    def update_access(self):
        """Update access statistics"""
        self.last_accessed = datetime.now()
        self.access_count += 1

@dataclass
class CacheInvalidationRule:
    """Rule for cache invalidation"""
    rule_id: str
    name: str
    trigger_patterns: List[str]
    affected_operations: List[str]
    invalidation_scope: str  # "specific", "pattern", "global"
    priority: int
    enabled: bool = True

@dataclass
class CacheStatistics:
    """Cache performance statistics"""
    total_requests: int
    cache_hits: int
    cache_misses: int
    hit_rate: float
    avg_response_time_ms: float
    total_entries: int
    expired_entries: int
    invalidated_entries: int
    memory_usage_bytes: int
    evictions_performed: int

class SecurityDecisionCache:
    """Advanced caching system for security decisions"""

    def __init__(self,
                 db_path: str = "security_decision_cache.db",
                 max_entries: int = 10000,
                 default_ttl_seconds: int = 3600,
                 eviction_policy: CacheEvictionPolicy = CacheEvictionPolicy.ADAPTIVE):

        self.db_path = db_path
        self.max_entries = max_entries
        self.default_ttl = default_ttl_seconds
        self.eviction_policy = eviction_policy

        # In-memory cache for fast access
        self.memory_cache: Dict[str, SecurityCacheEntry] = {}
        self.access_order: List[str] = []  # For LRU
        self.access_frequency: Dict[str, int] = {}  # For LFU

        # Invalidation rules
        self.invalidation_rules: Dict[str, CacheInvalidationRule] = {}

        # Statistics
        self.stats = CacheStatistics(
            total_requests=0, cache_hits=0, cache_misses=0, hit_rate=0.0,
            avg_response_time_ms=0.0, total_entries=0, expired_entries=0,
            invalidated_entries=0, memory_usage_bytes=0, evictions_performed=0
        )

        # Thread safety
        self.lock = threading.RLock()

        # Logger
        self.logger = logging.getLogger("security_cache")

        # Initialize
        self._init_database()
        self._load_invalidation_rules()
        self._load_cache_from_database()

        self.logger.info(f"Security Decision Cache initialized with {len(self.memory_cache)} entries")

    def _init_database(self):
        """Initialize SQLite database for persistent cache"""

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Cache entries table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cache_entries (
                cache_key TEXT PRIMARY KEY,
                operation TEXT NOT NULL,
                parameters_hash TEXT,
                user_context_hash TEXT,
                session_context_hash TEXT,
                security_level TEXT,
                decision TEXT NOT NULL,
                confidence TEXT NOT NULL,
                reasoning TEXT,
                alternatives TEXT,
                restrictions TEXT,
                metadata TEXT,
                created_at TEXT NOT NULL,
                last_accessed TEXT NOT NULL,
                access_count INTEGER DEFAULT 1,
                ttl_seconds INTEGER DEFAULT 3600,
                priority INTEGER DEFAULT 0,
                status TEXT DEFAULT 'active',
                security_context TEXT,
                invalidation_triggers TEXT,
                requires_revalidation BOOLEAN DEFAULT 0,
                original_processing_time_ms REAL
            )
        """)

        # Cache statistics table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cache_statistics (
                timestamp TEXT PRIMARY KEY,
                total_requests INTEGER,
                cache_hits INTEGER,
                cache_misses INTEGER,
                hit_rate REAL,
                avg_response_time_ms REAL,
                total_entries INTEGER,
                expired_entries INTEGER,
                invalidated_entries INTEGER,
                memory_usage_bytes INTEGER,
                evictions_performed INTEGER
            )
        """)

        # Invalidation rules table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS invalidation_rules (
                rule_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                trigger_patterns TEXT,
                affected_operations TEXT,
                invalidation_scope TEXT,
                priority INTEGER DEFAULT 0,
                enabled BOOLEAN DEFAULT 1
            )
        """)

        # Invalidation log
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS invalidation_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                rule_id TEXT,
                trigger_reason TEXT,
                affected_entries INTEGER,
                invalidation_scope TEXT
            )
        """)

        # Create indexes for performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_operation ON cache_entries(operation)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_created_at ON cache_entries(created_at)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_last_accessed ON cache_entries(last_accessed)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_status ON cache_entries(status)")

        conn.commit()
        conn.close()

    def _load_invalidation_rules(self):
        """Load default invalidation rules"""

        default_rules = [
            CacheInvalidationRule(
                rule_id="security_level_change",
                name="Security Level Change",
                trigger_patterns=["security_level_updated", "user_permissions_changed"],
                affected_operations=["*"],
                invalidation_scope="global",
                priority=1
            ),
            CacheInvalidationRule(
                rule_id="user_context_change",
                name="User Context Change",
                trigger_patterns=["user_login", "user_logout", "session_timeout"],
                affected_operations=["*"],
                invalidation_scope="pattern",
                priority=2
            ),
            CacheInvalidationRule(
                rule_id="system_config_change",
                name="System Configuration Change",
                trigger_patterns=["config_updated", "policy_changed", "rules_modified"],
                affected_operations=["system_command", "privilege_operation"],
                invalidation_scope="pattern",
                priority=3
            ),
            CacheInvalidationRule(
                rule_id="file_system_change",
                name="File System Change",
                trigger_patterns=["file_modified", "directory_changed", "permissions_updated"],
                affected_operations=["file_read", "file_write", "file_access"],
                invalidation_scope="specific",
                priority=4
            ),
            CacheInvalidationRule(
                rule_id="network_policy_change",
                name="Network Policy Change",
                trigger_patterns=["network_policy_updated", "firewall_changed"],
                affected_operations=["network_access", "external_request"],
                invalidation_scope="pattern",
                priority=5
            )
        ]

        with self.lock:
            for rule in default_rules:
                self.invalidation_rules[rule.rule_id] = rule

    def _load_cache_from_database(self):
        """Load cache entries from database to memory"""

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM cache_entries
            WHERE status = 'active'
            ORDER BY last_accessed DESC
            LIMIT ?
        """, (self.max_entries // 2,))  # Load half the cache from DB

        for row in cursor.fetchall():
            try:
                entry = self._row_to_cache_entry(row)
                if entry.is_valid():
                    cache_key = entry.key.to_string()
                    self.memory_cache[cache_key] = entry
                    self.access_order.append(cache_key)
                    self.access_frequency[cache_key] = entry.access_count

            except Exception as e:
                self.logger.error(f"Error loading cache entry: {e}")

        conn.close()

    def _row_to_cache_entry(self, row) -> SecurityCacheEntry:
        """Convert database row to cache entry"""

        key = CacheKey(
            operation=row[1],
            parameters_hash=row[2],
            user_context_hash=row[3],
            session_context_hash=row[4],
            security_level=row[5]
        )

        return SecurityCacheEntry(
            key=key,
            decision=row[6],
            confidence=DecisionConfidence(row[7]),
            reasoning=row[8] or "",
            alternatives=json.loads(row[9]) if row[9] else [],
            restrictions=json.loads(row[10]) if row[10] else [],
            metadata=json.loads(row[11]) if row[11] else {},
            created_at=datetime.fromisoformat(row[12]),
            last_accessed=datetime.fromisoformat(row[13]),
            access_count=row[14],
            ttl_seconds=row[15],
            priority=row[16],
            status=CacheEntryStatus(row[17]),
            security_context=json.loads(row[18]) if row[18] else {},
            invalidation_triggers=json.loads(row[19]) if row[19] else [],
            requires_revalidation=bool(row[20]),
            original_processing_time_ms=row[21] or 0.0
        )

    def generate_cache_key(self,
                          operation: str,
                          parameters: Dict[str, Any],
                          user_context: Dict[str, Any] = None,
                          session_context: Dict[str, Any] = None,
                          security_level: str = "default") -> CacheKey:
        """Generate a structured cache key"""

        # Normalize and hash parameters
        normalized_params = self._normalize_parameters(parameters)
        params_hash = hashlib.sha256(json.dumps(normalized_params, sort_keys=True).encode()).hexdigest()[:16]

        # Hash user context (excluding volatile fields)
        user_ctx = user_context or {}
        stable_user_ctx = {k: v for k, v in user_ctx.items() if k not in ['timestamp', 'last_activity']}
        user_hash = hashlib.sha256(json.dumps(stable_user_ctx, sort_keys=True).encode()).hexdigest()[:16]

        # Hash session context (excluding volatile fields)
        session_ctx = session_context or {}
        stable_session_ctx = {k: v for k, v in session_ctx.items() if k not in ['timestamp', 'request_id']}
        session_hash = hashlib.sha256(json.dumps(stable_session_ctx, sort_keys=True).encode()).hexdigest()[:16]

        return CacheKey(
            operation=operation,
            parameters_hash=params_hash,
            user_context_hash=user_hash,
            session_context_hash=session_hash,
            security_level=security_level
        )

    def _normalize_parameters(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize parameters for consistent caching"""

        normalized = {}
        for key, value in parameters.items():
            if isinstance(value, str):
                # Normalize file paths
                if key in ['path', 'file', 'directory']:
                    normalized[key] = value.strip().rstrip('/')
                else:
                    normalized[key] = value.strip()
            elif isinstance(value, (int, float, bool)):
                normalized[key] = value
            elif isinstance(value, (list, dict)):
                normalized[key] = json.dumps(value, sort_keys=True)
            else:
                normalized[key] = str(value)

        return normalized

    def get(self, cache_key: CacheKey) -> Optional[SecurityCacheEntry]:
        """Get entry from cache"""

        start_time = time.time()
        key_str = cache_key.to_string()

        with self.lock:
            self.stats.total_requests += 1

            entry = self.memory_cache.get(key_str)
            if entry is None:
                # Try loading from database
                entry = self._load_from_database(key_str)
                if entry:
                    self.memory_cache[key_str] = entry

            if entry and entry.is_valid():
                # Update access statistics
                entry.update_access()
                self._update_access_tracking(key_str)

                self.stats.cache_hits += 1
                response_time = (time.time() - start_time) * 1000
                self._update_response_time(response_time)

                self.logger.debug(f"Cache hit for {cache_key.operation}")
                return entry
            else:
                self.stats.cache_misses += 1
                self.logger.debug(f"Cache miss for {cache_key.operation}")
                return None

    def _load_from_database(self, cache_key: str) -> Optional[SecurityCacheEntry]:
        """Load entry from database"""

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM cache_entries WHERE cache_key = ?", (cache_key,))
        row = cursor.fetchone()
        conn.close()

        if row:
            try:
                return self._row_to_cache_entry(row)
            except Exception as e:
                self.logger.error(f"Error loading cache entry from DB: {e}")

        return None

    def put(self,
            cache_key: CacheKey,
            decision: str,
            confidence: DecisionConfidence,
            reasoning: str,
            alternatives: List[str] = None,
            restrictions: List[str] = None,
            metadata: Dict[str, Any] = None,
            security_context: Dict[str, Any] = None,
            ttl_seconds: Optional[int] = None,
            priority: int = 0,
            processing_time_ms: float = 0.0) -> bool:
        """Store entry in cache"""

        if alternatives is None:
            alternatives = []
        if restrictions is None:
            restrictions = []
        if metadata is None:
            metadata = {}
        if security_context is None:
            security_context = {}

        key_str = cache_key.to_string()

        # Create cache entry
        entry = SecurityCacheEntry(
            key=cache_key,
            decision=decision,
            confidence=confidence,
            reasoning=reasoning,
            alternatives=alternatives,
            restrictions=restrictions,
            metadata=metadata,
            created_at=datetime.now(),
            last_accessed=datetime.now(),
            access_count=1,
            ttl_seconds=ttl_seconds or self.default_ttl,
            priority=priority,
            status=CacheEntryStatus.ACTIVE,
            security_context=security_context,
            invalidation_triggers=self._determine_invalidation_triggers(cache_key.operation),
            requires_revalidation=False,
            original_processing_time_ms=processing_time_ms
        )

        with self.lock:
            # Check if we need to evict entries
            if len(self.memory_cache) >= self.max_entries:
                self._evict_entries()

            # Store in memory cache
            self.memory_cache[key_str] = entry
            self._update_access_tracking(key_str)

            # Store in database
            success = self._save_to_database(entry)

            if success:
                self.logger.debug(f"Cached decision for {cache_key.operation}")
                return True
            else:
                # Remove from memory if DB save failed
                self.memory_cache.pop(key_str, None)
                return False

    def _determine_invalidation_triggers(self, operation: str) -> List[str]:
        """Determine which events should invalidate this cache entry"""

        triggers = []

        # Always include global triggers
        triggers.extend(["security_policy_change", "system_restart"])

        # Operation-specific triggers
        if "file" in operation:
            triggers.extend(["file_system_change", "permissions_change"])
        elif "network" in operation:
            triggers.extend(["network_policy_change", "firewall_update"])
        elif "system" in operation:
            triggers.extend(["system_config_change", "privilege_change"])
        elif "user" in operation:
            triggers.extend(["user_context_change", "authentication_change"])

        return triggers

    def _evict_entries(self):
        """Evict entries based on eviction policy"""

        if self.eviction_policy == CacheEvictionPolicy.LRU:
            self._evict_lru()
        elif self.eviction_policy == CacheEvictionPolicy.LFU:
            self._evict_lfu()
        elif self.eviction_policy == CacheEvictionPolicy.TTL:
            self._evict_expired()
        elif self.eviction_policy == CacheEvictionPolicy.PRIORITY:
            self._evict_low_priority()
        else:  # ADAPTIVE
            self._evict_adaptive()

    def _evict_lru(self):
        """Evict least recently used entries"""

        entries_to_remove = max(1, len(self.memory_cache) // 10)  # Remove 10%

        with self.lock:
            # Sort by last accessed time
            sorted_keys = sorted(
                self.memory_cache.keys(),
                key=lambda k: self.memory_cache[k].last_accessed
            )

            for key in sorted_keys[:entries_to_remove]:
                self.memory_cache.pop(key, None)
                self.access_order = [k for k in self.access_order if k != key]
                self.access_frequency.pop(key, None)

            self.stats.evictions_performed += entries_to_remove

    def _evict_lfu(self):
        """Evict least frequently used entries"""

        entries_to_remove = max(1, len(self.memory_cache) // 10)

        with self.lock:
            # Sort by access count
            sorted_keys = sorted(
                self.memory_cache.keys(),
                key=lambda k: self.memory_cache[k].access_count
            )

            for key in sorted_keys[:entries_to_remove]:
                self.memory_cache.pop(key, None)
                self.access_order = [k for k in self.access_order if k != key]
                self.access_frequency.pop(key, None)

            self.stats.evictions_performed += entries_to_remove

    def _evict_expired(self):
        """Evict expired entries"""

        with self.lock:
            expired_keys = [
                key for key, entry in self.memory_cache.items()
                if entry.is_expired() or entry.status != CacheEntryStatus.ACTIVE
            ]

            for key in expired_keys:
                self.memory_cache.pop(key, None)
                self.access_order = [k for k in self.access_order if k != key]
                self.access_frequency.pop(key, None)

            self.stats.evictions_performed += len(expired_keys)

    def _evict_low_priority(self):
        """Evict low priority entries"""

        entries_to_remove = max(1, len(self.memory_cache) // 10)

        with self.lock:
            # Sort by priority (lower number = lower priority)
            sorted_keys = sorted(
                self.memory_cache.keys(),
                key=lambda k: self.memory_cache[k].priority
            )

            for key in sorted_keys[:entries_to_remove]:
                self.memory_cache.pop(key, None)
                self.access_order = [k for k in self.access_order if k != key]
                self.access_frequency.pop(key, None)

            self.stats.evictions_performed += entries_to_remove

    def _evict_adaptive(self):
        """Adaptive eviction based on multiple factors"""

        # First, remove expired entries
        self._evict_expired()

        # If still over limit, use composite scoring
        if len(self.memory_cache) >= self.max_entries:
            entries_to_remove = max(1, len(self.memory_cache) // 10)

            with self.lock:
                # Calculate composite scores
                scored_entries = []
                now = datetime.now()

                for key, entry in self.memory_cache.items():
                    age_hours = (now - entry.created_at).total_seconds() / 3600
                    recency_hours = (now - entry.last_accessed).total_seconds() / 3600

                    # Lower score = more likely to evict
                    score = (
                        entry.access_count * 0.3 +           # Frequency
                        (1 / max(recency_hours, 0.1)) * 0.3 + # Recency
                        entry.priority * 0.2 +               # Priority
                        (1 / max(age_hours, 0.1)) * 0.2      # Age
                    )

                    scored_entries.append((key, score))

                # Sort by score and evict lowest
                scored_entries.sort(key=lambda x: x[1])

                for key, _ in scored_entries[:entries_to_remove]:
                    self.memory_cache.pop(key, None)
                    self.access_order = [k for k in self.access_order if k != key]
                    self.access_frequency.pop(key, None)

                self.stats.evictions_performed += entries_to_remove

    def _update_access_tracking(self, key: str):
        """Update access tracking for eviction policies"""

        # Update LRU order
        if key in self.access_order:
            self.access_order.remove(key)
        self.access_order.append(key)

        # Update LFU frequency
        self.access_frequency[key] = self.access_frequency.get(key, 0) + 1

    def _save_to_database(self, entry: SecurityCacheEntry) -> bool:
        """Save entry to database"""

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                INSERT OR REPLACE INTO cache_entries VALUES (
                    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                )
            """, (
                entry.key.to_string(),
                entry.key.operation,
                entry.key.parameters_hash,
                entry.key.user_context_hash,
                entry.key.session_context_hash,
                entry.key.security_level,
                entry.decision,
                entry.confidence.value,
                entry.reasoning,
                json.dumps(entry.alternatives),
                json.dumps(entry.restrictions),
                json.dumps(entry.metadata),
                entry.created_at.isoformat(),
                entry.last_accessed.isoformat(),
                entry.access_count,
                entry.ttl_seconds,
                entry.priority,
                entry.status.value,
                json.dumps(entry.security_context),
                json.dumps(entry.invalidation_triggers),
                entry.requires_revalidation,
                entry.original_processing_time_ms
            ))

            conn.commit()
            conn.close()
            return True

        except Exception as e:
            self.logger.error(f"Error saving cache entry to database: {e}")
            return False

    def invalidate(self, pattern: str, reason: str = "manual"):
        """Invalidate cache entries matching pattern"""

        invalidated_count = 0

        with self.lock:
            keys_to_invalidate = []

            if pattern == "*":  # Global invalidation
                keys_to_invalidate = list(self.memory_cache.keys())
            else:
                # Pattern matching
                for key in self.memory_cache.keys():
                    if pattern in key:
                        keys_to_invalidate.append(key)

            # Remove from memory
            for key in keys_to_invalidate:
                if key in self.memory_cache:
                    self.memory_cache[key].status = CacheEntryStatus.INVALIDATED
                    self.memory_cache.pop(key, None)
                    self.access_order = [k for k in self.access_order if k != key]
                    self.access_frequency.pop(key, None)
                    invalidated_count += 1

            # Update database
            if keys_to_invalidate:
                self._invalidate_in_database(keys_to_invalidate, reason)

            self.stats.invalidated_entries += invalidated_count

        self.logger.info(f"Invalidated {invalidated_count} cache entries (pattern: {pattern}, reason: {reason})")

    def _invalidate_in_database(self, keys: List[str], reason: str):
        """Mark entries as invalidated in database"""

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Update status
        for key in keys:
            cursor.execute(
                "UPDATE cache_entries SET status = 'invalidated' WHERE cache_key = ?",
                (key,)
            )

        # Log invalidation
        cursor.execute("""
            INSERT INTO invalidation_log (timestamp, rule_id, trigger_reason, affected_entries, invalidation_scope)
            VALUES (?, ?, ?, ?, ?)
        """, (
            datetime.now().isoformat(),
            "manual",
            reason,
            len(keys),
            "pattern"
        ))

        conn.commit()
        conn.close()

    def _update_response_time(self, response_time_ms: float):
        """Update average response time statistics"""

        current_avg = self.stats.avg_response_time_ms
        total_hits = self.stats.cache_hits

        if total_hits <= 1:
            self.stats.avg_response_time_ms = response_time_ms
        else:
            self.stats.avg_response_time_ms = (
                (current_avg * (total_hits - 1) + response_time_ms) / total_hits
            )

    def get_statistics(self) -> CacheStatistics:
        """Get current cache statistics"""

        with self.lock:
            # Update current stats
            self.stats.hit_rate = (
                self.stats.cache_hits / max(self.stats.total_requests, 1)
            )
            self.stats.total_entries = len(self.memory_cache)
            self.stats.expired_entries = sum(
                1 for entry in self.memory_cache.values() if entry.is_expired()
            )

            # Estimate memory usage
            estimated_size = 0
            for entry in list(self.memory_cache.values())[:10]:  # Sample for estimation
                try:
                    estimated_size += len(pickle.dumps(entry))
                except:
                    estimated_size += 1000  # Rough estimate

            self.stats.memory_usage_bytes = estimated_size * len(self.memory_cache) // max(10, 1)

            return self.stats

    def cleanup_expired(self):
        """Remove expired entries"""

        removed_count = 0

        with self.lock:
            expired_keys = [
                key for key, entry in self.memory_cache.items()
                if entry.is_expired()
            ]

            for key in expired_keys:
                self.memory_cache.pop(key, None)
                self.access_order = [k for k in self.access_order if k != key]
                self.access_frequency.pop(key, None)
                removed_count += 1

        self.logger.info(f"Cleaned up {removed_count} expired cache entries")

    def get_cache_info(self) -> Dict[str, Any]:
        """Get detailed cache information"""

        with self.lock:
            return {
                "total_entries": len(self.memory_cache),
                "max_entries": self.max_entries,
                "eviction_policy": self.eviction_policy.value,
                "default_ttl": self.default_ttl,
                "memory_cache_keys": len(self.memory_cache),
                "access_order_length": len(self.access_order),
                "access_frequency_tracked": len(self.access_frequency),
                "invalidation_rules": len(self.invalidation_rules),
                "database_path": self.db_path
            }

def demo_security_cache():
    """Demonstrate security decision cache"""

    cache = SecurityDecisionCache(
        db_path="demo_security_cache.db",
        max_entries=100,
        default_ttl_seconds=300,
        eviction_policy=CacheEvictionPolicy.ADAPTIVE
    )

    print("💾 Security Decision Cache Demo")
    print("=" * 60)

    # Test caching decisions
    test_scenarios = [
        ("file_read", {"path": "/home/user/document.txt"}, "allow", DecisionConfidence.HIGH),
        ("system_command", {"cmd": "rm -rf /"}, "block", DecisionConfidence.VERY_HIGH),
        ("network_access", {"url": "https://example.com"}, "allow", DecisionConfidence.MEDIUM),
        ("file_read", {"path": "/home/user/document.txt"}, "allow", DecisionConfidence.HIGH),  # Duplicate
        ("privilege_operation", {"action": "sudo"}, "block", DecisionConfidence.HIGH),
    ]

    # Store decisions
    for i, (operation, parameters, decision, confidence) in enumerate(test_scenarios):
        key = cache.generate_cache_key(
            operation=operation,
            parameters=parameters,
            user_context={"user_id": "demo_user"},
            session_context={"session_id": f"demo_session_{i}"},
            security_level="standard"
        )

        success = cache.put(
            cache_key=key,
            decision=decision,
            confidence=confidence,
            reasoning=f"Test decision for {operation}",
            alternatives=["alternative1", "alternative2"],
            processing_time_ms=50.0 + i * 10
        )

        print(f"{i+1}. Stored: {operation} -> {decision} (success: {success})")

    # Test retrieval
    print(f"\n📥 Testing Cache Retrieval:")
    for i, (operation, parameters, expected_decision, _) in enumerate(test_scenarios):
        key = cache.generate_cache_key(
            operation=operation,
            parameters=parameters,
            user_context={"user_id": "demo_user"},
            session_context={"session_id": f"demo_session_{i}"},
            security_level="standard"
        )

        cached_entry = cache.get(key)
        if cached_entry:
            print(f"   ✅ {operation}: {cached_entry.decision} (accessed {cached_entry.access_count} times)")
        else:
            print(f"   ❌ {operation}: Not found in cache")

    # Test invalidation
    print(f"\n🗑️ Testing Cache Invalidation:")
    cache.invalidate("file_read", "test invalidation")

    # Check stats
    print(f"\n📊 Cache Statistics:")
    stats = cache.get_statistics()
    print(f"   Total Requests: {stats.total_requests}")
    print(f"   Cache Hits: {stats.cache_hits}")
    print(f"   Hit Rate: {stats.hit_rate:.2%}")
    print(f"   Total Entries: {stats.total_entries}")
    print(f"   Avg Response Time: {stats.avg_response_time_ms:.2f}ms")

    # Cleanup
    import os
    if os.path.exists("demo_security_cache.db"):
        os.remove("demo_security_cache.db")

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    demo_security_cache()