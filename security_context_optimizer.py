#!/usr/bin/env python3
"""
Security Context Optimizer
Advanced context compression and token optimization for repetitive security tasks
"""

import hashlib
import json
import logging
import re
import sqlite3
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Set, Union
from dataclasses import dataclass, asdict
from enum import Enum
from collections import defaultdict, Counter
import pickle
import zlib

try:
    from security_event_templates import SecurityEventClassifier, EventCategory, AnalysisComplexity
    from enhanced_security_logging import SecurityEventType, SecuritySeverity
except ImportError as e:
    print(f"Warning: Could not import security components: {e}")

class CompressionStrategy(Enum):
    """Context compression strategies"""
    TEMPLATE_BASED = "template_based"        # Use pre-defined templates
    PATTERN_LEARNING = "pattern_learning"    # Learn from repeated patterns
    SEMANTIC_GROUPING = "semantic_grouping"  # Group semantically similar content
    FREQUENCY_BASED = "frequency_based"      # Compress based on frequency
    HIERARCHICAL = "hierarchical"            # Multi-level compression
    ADAPTIVE = "adaptive"                    # Adaptive strategy selection

class OptimizationTarget(Enum):
    """Optimization targets"""
    TOKEN_MINIMIZATION = "token_minimization"    # Minimize token usage
    QUALITY_PRESERVATION = "quality_preservation" # Preserve analysis quality
    SPEED_OPTIMIZATION = "speed_optimization"     # Optimize processing speed
    BALANCED = "balanced"                         # Balance all factors

class CompressionLevel(Enum):
    """Compression levels"""
    NONE = 0      # No compression
    LIGHT = 1     # Light compression (90% of original)
    MODERATE = 2  # Moderate compression (70% of original)
    HEAVY = 3     # Heavy compression (50% of original)
    EXTREME = 4   # Extreme compression (30% of original)

@dataclass
class CompressionPattern:
    """Learned compression pattern"""
    pattern_id: str
    pattern_type: str
    source_template: str
    compressed_form: str
    original_tokens: int
    compressed_tokens: int
    compression_ratio: float
    usage_count: int
    quality_impact: float
    last_used: datetime

@dataclass
class ContextSnapshot:
    """Snapshot of context for compression analysis"""
    snapshot_id: str
    event_signature: str
    original_context: str
    compressed_context: str
    compression_metadata: Dict[str, Any]
    token_savings: int
    quality_score: float
    processing_time_ms: float
    created_at: datetime

@dataclass
class RepeatedSequence:
    """Identified repeated sequence for compression"""
    sequence_id: str
    content: str
    frequency: int
    contexts: List[str]
    compression_potential: float
    first_seen: datetime
    last_seen: datetime

class PatternLearner:
    """Learns compression patterns from security event history"""

    def __init__(self, min_frequency: int = 3, min_length: int = 10):
        self.min_frequency = min_frequency
        self.min_length = min_length
        self.learned_patterns: Dict[str, CompressionPattern] = {}
        self.sequence_tracker: Dict[str, RepeatedSequence] = {}
        self.ngram_frequencies: Dict[Tuple[str, ...], int] = defaultdict(int)
        self.logger = logging.getLogger("pattern_learner")

    def analyze_context_history(self, contexts: List[str]) -> List[CompressionPattern]:
        """Analyze context history to learn compression patterns"""

        # Extract n-grams of various sizes
        all_tokens = []
        for context in contexts:
            tokens = self._tokenize_context(context)
            all_tokens.extend(tokens)
            self._extract_ngrams(tokens)

        # Identify repeated sequences
        repeated_sequences = self._find_repeated_sequences(contexts)

        # Generate compression patterns
        patterns = []
        for sequence in repeated_sequences:
            if sequence.compression_potential > 0.3:  # Minimum compression threshold
                pattern = self._create_compression_pattern(sequence)
                patterns.append(pattern)

        return patterns

    def _tokenize_context(self, context: str) -> List[str]:
        """Tokenize context into meaningful units"""
        # Split on common delimiters
        tokens = re.split(r'[,\s\n\t:={}"\[\]]+', context)
        return [token.strip() for token in tokens if token.strip()]

    def _extract_ngrams(self, tokens: List[str], max_n: int = 5):
        """Extract n-grams from tokens"""
        for n in range(2, min(max_n + 1, len(tokens) + 1)):
            for i in range(len(tokens) - n + 1):
                ngram = tuple(tokens[i:i + n])
                self.ngram_frequencies[ngram] += 1

    def _find_repeated_sequences(self, contexts: List[str]) -> List[RepeatedSequence]:
        """Find repeated sequences across contexts"""
        sequences = []

        # Use sliding window to find common substrings
        for window_size in range(self.min_length, 100, 10):
            sequence_counts = defaultdict(list)

            for i, context in enumerate(contexts):
                for j in range(len(context) - window_size + 1):
                    substring = context[j:j + window_size]
                    sequence_counts[substring].append(i)

            # Create RepeatedSequence objects for frequent patterns
            for sequence, context_indices in sequence_counts.items():
                if len(context_indices) >= self.min_frequency:
                    sequence_id = hashlib.md5(sequence.encode()).hexdigest()[:12]

                    sequences.append(RepeatedSequence(
                        sequence_id=sequence_id,
                        content=sequence,
                        frequency=len(context_indices),
                        contexts=[contexts[i] for i in context_indices],
                        compression_potential=self._calculate_compression_potential(sequence, len(context_indices)),
                        first_seen=datetime.now() - timedelta(days=30),  # Simulate historical data
                        last_seen=datetime.now()
                    ))

        return sequences

    def _calculate_compression_potential(self, sequence: str, frequency: int) -> float:
        """Calculate compression potential for a sequence"""
        # Factors: length, frequency, uniqueness
        length_factor = min(len(sequence) / 100, 1.0)
        frequency_factor = min(frequency / 10, 1.0)

        # Check for common patterns that compress well
        pattern_bonus = 0.0
        if re.search(r'\b(event_type|operation|user_id|timestamp)\b', sequence):
            pattern_bonus = 0.2
        if re.search(r'\b(allow|block|deny|granted|access)\b', sequence):
            pattern_bonus += 0.15

        return min(length_factor * 0.4 + frequency_factor * 0.4 + pattern_bonus, 1.0)

    def _create_compression_pattern(self, sequence: RepeatedSequence) -> CompressionPattern:
        """Create compression pattern from repeated sequence"""

        # Generate compressed form
        compressed_form = self._compress_sequence(sequence.content)

        # Estimate token counts
        original_tokens = len(sequence.content.split())
        compressed_tokens = len(compressed_form.split())

        compression_ratio = compressed_tokens / original_tokens if original_tokens > 0 else 1.0

        return CompressionPattern(
            pattern_id=sequence.sequence_id,
            pattern_type="repeated_sequence",
            source_template=compressed_form,
            compressed_form=compressed_form,
            original_tokens=original_tokens,
            compressed_tokens=compressed_tokens,
            compression_ratio=compression_ratio,
            usage_count=sequence.frequency,
            quality_impact=0.95,  # Minimal quality impact for exact matches
            last_used=sequence.last_seen
        )

    def _compress_sequence(self, sequence: str) -> str:
        """Compress a sequence using learned patterns"""

        # Replace common security terms with abbreviations
        abbreviations = {
            "permission_check": "perm_chk",
            "access_granted": "acc_ok",
            "access_denied": "acc_deny",
            "security_violation": "sec_viol",
            "event_type": "type",
            "operation": "op",
            "resource": "res",
            "user_id": "user",
            "session_id": "sess",
            "timestamp": "ts",
            "parameters": "params",
            "description": "desc"
        }

        compressed = sequence
        for full_form, abbrev in abbreviations.items():
            compressed = compressed.replace(full_form, abbrev)

        # Remove redundant words
        redundant_words = ["the", "a", "an", "is", "was", "were", "has", "have", "had"]
        words = compressed.split()
        filtered_words = [word for word in words if word.lower() not in redundant_words]

        return " ".join(filtered_words)

class ContextCompressor:
    """Advanced context compression with multiple strategies"""

    def __init__(self, db_path: str = "context_optimization.db"):
        self.db_path = db_path
        self.logger = logging.getLogger("context_compressor")

        # Components
        self.pattern_learner = PatternLearner()
        self.classifier = SecurityEventClassifier()

        # Compression state
        self.compression_cache: Dict[str, ContextSnapshot] = {}
        self.compression_patterns: Dict[str, CompressionPattern] = {}
        self.optimization_stats = {
            "total_compressions": 0,
            "avg_compression_ratio": 0.0,
            "avg_token_savings": 0,
            "avg_quality_score": 0.0,
            "cache_hit_rate": 0.0
        }

        # Thread safety
        self.lock = threading.RLock()

        # Initialize database
        self._init_database()

        # Load existing patterns
        self._load_compression_patterns()

    def _init_database(self):
        """Initialize database for compression tracking"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS compression_patterns (
                pattern_id TEXT PRIMARY KEY,
                pattern_type TEXT,
                source_template TEXT,
                compressed_form TEXT,
                original_tokens INTEGER,
                compressed_tokens INTEGER,
                compression_ratio REAL,
                usage_count INTEGER,
                quality_impact REAL,
                last_used TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS context_snapshots (
                snapshot_id TEXT PRIMARY KEY,
                event_signature TEXT,
                original_context TEXT,
                compressed_context TEXT,
                compression_metadata TEXT,
                token_savings INTEGER,
                quality_score REAL,
                processing_time_ms REAL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS optimization_metrics (
                timestamp TEXT PRIMARY KEY,
                total_compressions INTEGER,
                avg_compression_ratio REAL,
                avg_token_savings INTEGER,
                avg_quality_score REAL,
                cache_hit_rate REAL
            )
        """)

        conn.commit()
        conn.close()

    def _load_compression_patterns(self):
        """Load existing compression patterns from database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM compression_patterns")
        rows = cursor.fetchall()

        for row in rows:
            pattern = CompressionPattern(
                pattern_id=row[0],
                pattern_type=row[1],
                source_template=row[2],
                compressed_form=row[3],
                original_tokens=row[4],
                compressed_tokens=row[5],
                compression_ratio=row[6],
                usage_count=row[7],
                quality_impact=row[8],
                last_used=datetime.fromisoformat(row[9]) if row[9] else datetime.now()
            )
            self.compression_patterns[pattern.pattern_id] = pattern

        conn.close()
        self.logger.info(f"Loaded {len(self.compression_patterns)} compression patterns")

    def compress_context(self, context: Dict[str, Any], target: OptimizationTarget = OptimizationTarget.BALANCED,
                        level: CompressionLevel = CompressionLevel.MODERATE) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """Compress context with specified optimization target and level"""

        start_time = time.time()

        # Create context signature for caching
        context_signature = self._create_context_signature(context)

        with self.lock:
            # Check cache first
            if context_signature in self.compression_cache:
                cached = self.compression_cache[context_signature]
                self._update_cache_stats(True)
                return json.loads(cached.compressed_context), json.loads(cached.compression_metadata)

        # Apply compression strategy
        compressed_context, metadata = self._apply_compression_strategy(context, target, level)

        # Calculate metrics
        processing_time = (time.time() - start_time) * 1000
        original_size = len(json.dumps(context))
        compressed_size = len(json.dumps(compressed_context))
        token_savings = self._estimate_token_savings(original_size, compressed_size)

        # Create snapshot
        snapshot = ContextSnapshot(
            snapshot_id=f"snap_{int(time.time() * 1000)}",
            event_signature=context_signature,
            original_context=json.dumps(context),
            compressed_context=json.dumps(compressed_context),
            compression_metadata=json.dumps(metadata),
            token_savings=token_savings,
            quality_score=metadata.get("quality_score", 0.8),
            processing_time_ms=processing_time,
            created_at=datetime.now()
        )

        # Cache result
        with self.lock:
            self.compression_cache[context_signature] = snapshot
            self._update_cache_stats(False)

        # Store in database
        self._store_snapshot(snapshot)

        # Update statistics
        self._update_optimization_stats(snapshot)

        return compressed_context, metadata

    def _create_context_signature(self, context: Dict[str, Any]) -> str:
        """Create unique signature for context"""
        # Use relevant fields for signature
        signature_fields = ['event_type', 'operation', 'resource', 'user_id']
        signature_data = {k: context.get(k) for k in signature_fields if k in context}

        signature_str = json.dumps(signature_data, sort_keys=True)
        return hashlib.md5(signature_str.encode()).hexdigest()[:16]

    def _apply_compression_strategy(self, context: Dict[str, Any], target: OptimizationTarget,
                                  level: CompressionLevel) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """Apply compression strategy based on target and level"""

        if target == OptimizationTarget.TOKEN_MINIMIZATION:
            return self._minimize_tokens(context, level)
        elif target == OptimizationTarget.QUALITY_PRESERVATION:
            return self._preserve_quality(context, level)
        elif target == OptimizationTarget.SPEED_OPTIMIZATION:
            return self._optimize_speed(context, level)
        else:  # BALANCED
            return self._balanced_compression(context, level)

    def _minimize_tokens(self, context: Dict[str, Any], level: CompressionLevel) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """Aggressive token minimization"""
        compressed = {}
        metadata = {"strategy": "token_minimization", "level": level.value}

        # Essential fields only
        essential_fields = ["event_type", "operation", "decision"]

        if level.value >= CompressionLevel.LIGHT.value:
            essential_fields.extend(["user_id", "risk_score"])

        if level.value >= CompressionLevel.MODERATE.value:
            essential_fields.extend(["resource", "severity"])

        if level.value >= CompressionLevel.HEAVY.value:
            essential_fields.extend(["reason", "timestamp"])

        # Copy essential fields with abbreviation
        for field in essential_fields:
            if field in context:
                compressed[self._abbreviate_field_name(field)] = self._compress_field_value(context[field])

        # Compress parameters aggressively
        if "parameters" in context and level.value < CompressionLevel.EXTREME.value:
            compressed["params"] = self._compress_parameters(context["parameters"], level)

        metadata.update({
            "fields_kept": len(compressed),
            "fields_removed": len(context) - len(compressed),
            "quality_score": max(0.5, 1.0 - level.value * 0.1)
        })

        return compressed, metadata

    def _preserve_quality(self, context: Dict[str, Any], level: CompressionLevel) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """Quality-preserving compression"""
        compressed = context.copy()
        metadata = {"strategy": "quality_preservation", "level": level.value}

        # Only compress values, keep structure
        for key, value in context.items():
            if isinstance(value, str) and len(value) > 50:
                compressed[key] = self._compress_text_value(value, level)
            elif isinstance(value, dict):
                compressed[key] = self._compress_dict_value(value, level)

        metadata.update({
            "quality_score": max(0.8, 1.0 - level.value * 0.05),
            "structure_preserved": True
        })

        return compressed, metadata

    def _optimize_speed(self, context: Dict[str, Any], level: CompressionLevel) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """Speed-optimized compression"""
        compressed = {}
        metadata = {"strategy": "speed_optimization", "level": level.value}

        # Use pre-compiled patterns for fast compression
        for key, value in context.items():
            if key in ["event_type", "operation", "user_id", "decision"]:
                compressed[key] = value  # Keep as-is for speed
            elif isinstance(value, str):
                compressed[key] = value[:50] if len(value) > 50 else value
            elif isinstance(value, dict) and level.value < CompressionLevel.HEAVY.value:
                # Keep only first few items
                compressed[key] = dict(list(value.items())[:3])

        metadata.update({
            "quality_score": max(0.6, 1.0 - level.value * 0.08),
            "processing_optimized": True
        })

        return compressed, metadata

    def _balanced_compression(self, context: Dict[str, Any], level: CompressionLevel) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """Balanced compression strategy"""
        compressed = {}
        metadata = {"strategy": "balanced", "level": level.value}

        # Prioritize fields by importance
        field_importance = {
            "event_type": 1.0, "operation": 0.9, "user_id": 0.8, "decision": 0.8,
            "resource": 0.7, "reason": 0.6, "risk_score": 0.6, "severity": 0.5,
            "parameters": 0.4, "context": 0.3, "timestamp": 0.2
        }

        compression_threshold = 1.0 - level.value * 0.2

        for field, value in context.items():
            importance = field_importance.get(field, 0.3)

            if importance >= compression_threshold:
                if isinstance(value, str) and len(value) > 100:
                    compressed[field] = self._compress_text_value(value, level)
                elif isinstance(value, dict):
                    compressed[field] = self._compress_dict_value(value, level)
                else:
                    compressed[field] = value
            elif importance >= compression_threshold - 0.2:
                # Include but compress more aggressively
                if isinstance(value, str):
                    compressed[self._abbreviate_field_name(field)] = value[:30]
                elif isinstance(value, dict):
                    compressed[self._abbreviate_field_name(field)] = dict(list(value.items())[:2])

        metadata.update({
            "quality_score": max(0.7, 1.0 - level.value * 0.06),
            "balance_optimized": True,
            "compression_threshold": compression_threshold
        })

        return compressed, metadata

    def _abbreviate_field_name(self, field_name: str) -> str:
        """Abbreviate field names for compression"""
        abbreviations = {
            "event_type": "type",
            "operation": "op",
            "user_id": "user",
            "session_id": "sess",
            "resource": "res",
            "parameters": "params",
            "timestamp": "ts",
            "description": "desc",
            "risk_score": "risk",
            "severity": "sev"
        }
        return abbreviations.get(field_name, field_name)

    def _compress_field_value(self, value: Any) -> Any:
        """Compress individual field values"""
        if isinstance(value, str):
            # Common security term abbreviations
            abbreviations = {
                "permission_check": "perm_chk",
                "access_granted": "granted",
                "access_denied": "denied",
                "security_violation": "violation",
                "file_read": "read",
                "file_write": "write",
                "network_request": "net_req"
            }

            compressed_value = value
            for full, abbrev in abbreviations.items():
                compressed_value = compressed_value.replace(full, abbrev)

            return compressed_value
        return value

    def _compress_parameters(self, parameters: Dict[str, Any], level: CompressionLevel) -> Dict[str, Any]:
        """Compress parameters dictionary"""
        if level.value >= CompressionLevel.EXTREME.value:
            # Keep only most important parameters
            important_keys = ["path", "file", "url", "command", "user", "permission"]
            return {k: v for k, v in parameters.items() if any(imp in k.lower() for imp in important_keys)}

        elif level.value >= CompressionLevel.HEAVY.value:
            # Limit to 3 most relevant parameters
            return dict(list(parameters.items())[:3])

        elif level.value >= CompressionLevel.MODERATE.value:
            # Compress string values
            compressed = {}
            for k, v in parameters.items():
                if isinstance(v, str) and len(v) > 50:
                    compressed[k] = v[:50] + "..."
                else:
                    compressed[k] = v
            return compressed

        return parameters

    def _compress_text_value(self, text: str, level: CompressionLevel) -> str:
        """Compress text values"""
        if level.value >= CompressionLevel.HEAVY.value:
            # Extract key terms only
            important_words = re.findall(r'\b(?:allow|block|deny|grant|access|security|violation|user|file|system)\b', text, re.IGNORECASE)
            return " ".join(important_words) if important_words else text[:20]

        elif level.value >= CompressionLevel.MODERATE.value:
            # Truncate with important words preserved
            if len(text) > 100:
                return text[:100] + "..."

        return text

    def _compress_dict_value(self, dict_value: Dict[str, Any], level: CompressionLevel) -> Dict[str, Any]:
        """Compress dictionary values"""
        if level.value >= CompressionLevel.HEAVY.value:
            return dict(list(dict_value.items())[:2])
        elif level.value >= CompressionLevel.MODERATE.value:
            return dict(list(dict_value.items())[:5])
        return dict_value

    def _estimate_token_savings(self, original_size: int, compressed_size: int) -> int:
        """Estimate token savings from compression"""
        # Rough estimation: 4 characters per token
        original_tokens = original_size // 4
        compressed_tokens = compressed_size // 4
        return max(0, original_tokens - compressed_tokens)

    def _update_cache_stats(self, was_hit: bool):
        """Update cache statistics"""
        if was_hit:
            cache_hits = getattr(self, '_cache_hits', 0) + 1
            setattr(self, '_cache_hits', cache_hits)
        else:
            cache_misses = getattr(self, '_cache_misses', 0) + 1
            setattr(self, '_cache_misses', cache_misses)

        total_requests = getattr(self, '_cache_hits', 0) + getattr(self, '_cache_misses', 0)
        self.optimization_stats["cache_hit_rate"] = getattr(self, '_cache_hits', 0) / max(total_requests, 1)

    def _store_snapshot(self, snapshot: ContextSnapshot):
        """Store context snapshot in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO context_snapshots
            (snapshot_id, event_signature, original_context, compressed_context,
             compression_metadata, token_savings, quality_score, processing_time_ms, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            snapshot.snapshot_id,
            snapshot.event_signature,
            snapshot.original_context,
            snapshot.compressed_context,
            snapshot.compression_metadata,
            snapshot.token_savings,
            snapshot.quality_score,
            snapshot.processing_time_ms,
            snapshot.created_at.isoformat()
        ))

        conn.commit()
        conn.close()

    def _update_optimization_stats(self, snapshot: ContextSnapshot):
        """Update optimization statistics"""
        with self.lock:
            self.optimization_stats["total_compressions"] += 1

            # Update averages
            total = self.optimization_stats["total_compressions"]

            # Compression ratio
            original_size = len(snapshot.original_context)
            compressed_size = len(snapshot.compressed_context)
            compression_ratio = compressed_size / original_size if original_size > 0 else 1.0

            self.optimization_stats["avg_compression_ratio"] = (
                (self.optimization_stats["avg_compression_ratio"] * (total - 1) + compression_ratio) / total
            )

            # Token savings
            self.optimization_stats["avg_token_savings"] = (
                (self.optimization_stats["avg_token_savings"] * (total - 1) + snapshot.token_savings) / total
            )

            # Quality score
            self.optimization_stats["avg_quality_score"] = (
                (self.optimization_stats["avg_quality_score"] * (total - 1) + snapshot.quality_score) / total
            )

    def learn_from_context_history(self, contexts: List[Dict[str, Any]]) -> int:
        """Learn compression patterns from context history"""
        context_strings = [json.dumps(ctx, sort_keys=True) for ctx in contexts]
        patterns = self.pattern_learner.analyze_context_history(context_strings)

        new_patterns = 0
        for pattern in patterns:
            if pattern.pattern_id not in self.compression_patterns:
                self.compression_patterns[pattern.pattern_id] = pattern
                self._store_compression_pattern(pattern)
                new_patterns += 1

        self.logger.info(f"Learned {new_patterns} new compression patterns from {len(contexts)} contexts")
        return new_patterns

    def _store_compression_pattern(self, pattern: CompressionPattern):
        """Store compression pattern in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT OR REPLACE INTO compression_patterns
            (pattern_id, pattern_type, source_template, compressed_form,
             original_tokens, compressed_tokens, compression_ratio,
             usage_count, quality_impact, last_used)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            pattern.pattern_id,
            pattern.pattern_type,
            pattern.source_template,
            pattern.compressed_form,
            pattern.original_tokens,
            pattern.compressed_tokens,
            pattern.compression_ratio,
            pattern.usage_count,
            pattern.quality_impact,
            pattern.last_used.isoformat()
        ))

        conn.commit()
        conn.close()

    def get_optimization_stats(self) -> Dict[str, Any]:
        """Get optimization statistics"""
        with self.lock:
            stats = self.optimization_stats.copy()
            stats.update({
                "cache_size": len(self.compression_cache),
                "learned_patterns": len(self.compression_patterns),
                "token_efficiency": (
                    self.optimization_stats["avg_token_savings"] /
                    max(self.optimization_stats["avg_compression_ratio"], 0.1)
                )
            })
            return stats

    def cleanup_cache(self, max_age_hours: int = 24):
        """Clean up old cache entries"""
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)

        with self.lock:
            to_remove = [
                key for key, snapshot in self.compression_cache.items()
                if snapshot.created_at < cutoff_time
            ]

            for key in to_remove:
                del self.compression_cache[key]

        self.logger.info(f"Cleaned up {len(to_remove)} old cache entries")

def demo_context_optimizer():
    """Demonstrate context optimization capabilities"""

    print("🎯 Security Context Optimizer Demo")
    print("=" * 60)

    optimizer = ContextCompressor("demo_context_optimization.db")

    # Test contexts
    test_contexts = [
        {
            "event_type": "permission_check",
            "operation": "file_read",
            "resource": "/home/user/documents/confidential_report.pdf",
            "user_id": "user123",
            "session_id": "sess_abc_123",
            "timestamp": "2024-01-15T10:30:00Z",
            "parameters": {
                "file_path": "/home/user/documents/confidential_report.pdf",
                "access_mode": "read",
                "file_size": "2.5MB",
                "file_type": "PDF document",
                "permissions_required": "read_documents"
            },
            "context": {
                "user_role": "employee",
                "department": "finance",
                "security_clearance": "standard",
                "previous_access": "approved",
                "access_time": "business_hours"
            },
            "risk_score": 0.3,
            "severity": 2,
            "decision": "allow",
            "reason": "User has appropriate permissions for document access",
            "alternatives": ["Request temporary access", "Use document viewer"]
        },
        {
            "event_type": "security_violation",
            "operation": "file_access",
            "resource": "../../../etc/passwd",
            "user_id": "user456",
            "session_id": "sess_def_456",
            "timestamp": "2024-01-15T10:31:00Z",
            "parameters": {
                "attempted_path": "../../../etc/passwd",
                "access_method": "direct_file_access",
                "traversal_pattern": "detected",
                "blocked_by": "security_system"
            },
            "context": {
                "attack_type": "path_traversal",
                "severity_level": "high",
                "automatic_block": True,
                "source_ip": "192.168.1.100",
                "user_agent": "suspicious_client"
            },
            "risk_score": 0.9,
            "severity": 5,
            "decision": "block",
            "reason": "Path traversal attack detected - attempting to access system files",
            "alternatives": []
        }
    ]

    # Test different optimization targets and levels
    test_scenarios = [
        (OptimizationTarget.TOKEN_MINIMIZATION, CompressionLevel.HEAVY),
        (OptimizationTarget.QUALITY_PRESERVATION, CompressionLevel.MODERATE),
        (OptimizationTarget.SPEED_OPTIMIZATION, CompressionLevel.LIGHT),
        (OptimizationTarget.BALANCED, CompressionLevel.MODERATE)
    ]

    print(f"Testing {len(test_contexts)} contexts with {len(test_scenarios)} optimization scenarios...\n")

    for i, context in enumerate(test_contexts, 1):
        print(f"{i}. Original Context:")
        print(f"   Event: {context['event_type']}")
        print(f"   Operation: {context['operation']}")
        print(f"   Size: {len(json.dumps(context))} characters")

        for target, level in test_scenarios:
            compressed, metadata = optimizer.compress_context(context, target, level)

            original_size = len(json.dumps(context))
            compressed_size = len(json.dumps(compressed))
            compression_ratio = compressed_size / original_size

            print(f"\n   {target.value} ({level.name}):")
            print(f"     Compressed Size: {compressed_size} chars ({compression_ratio:.2%} of original)")
            print(f"     Quality Score: {metadata['quality_score']:.2%}")
            print(f"     Token Savings: ~{(original_size - compressed_size) // 4} tokens")
            print(f"     Strategy: {metadata['strategy']}")

        print()

    # Test pattern learning
    print("🧠 Testing Pattern Learning:")
    patterns_learned = optimizer.learn_from_context_history(test_contexts)
    print(f"Learned {patterns_learned} new patterns from context history")

    # Show statistics
    print(f"\n📊 Optimization Statistics:")
    stats = optimizer.get_optimization_stats()
    for key, value in stats.items():
        if isinstance(value, float):
            print(f"   {key}: {value:.3f}")
        else:
            print(f"   {key}: {value}")

    # Cleanup
    import os
    if os.path.exists("demo_context_optimization.db"):
        os.remove("demo_context_optimization.db")

    print("\n✅ Security Context Optimizer Demo Complete!")

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    demo_context_optimizer()