#!/usr/bin/env python3
"""
Security Batch Processing System
Optimized batch processing for multiple security events with intelligent grouping
"""

import asyncio
import json
import logging
import sqlite3
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable, AsyncIterator, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
from concurrent.futures import ThreadPoolExecutor, Future
import hashlib

try:
    from security_event_templates import (
        SecurityEventClassifier, ContextCompressor, EventCategory,
        AnalysisComplexity, TokenOptimization
    )
    from enhanced_security_logging import SecurityEvent, SecurityEventType, SecuritySeverity
except ImportError as e:
    print(f"Warning: Could not import security components: {e}")

class BatchStrategy(Enum):
    """Batch processing strategies"""
    TEMPORAL = "temporal"           # Group by time windows
    CATEGORICAL = "categorical"     # Group by event category
    SIMILARITY = "similarity"       # Group by event similarity
    PRIORITY = "priority"           # Group by priority/severity
    HYBRID = "hybrid"              # Intelligent combination

class ProcessingMode(Enum):
    """Processing mode for different scenarios"""
    REAL_TIME = "real_time"        # Immediate processing
    BATCH_SMALL = "batch_small"    # Small batches (5-10 events)
    BATCH_MEDIUM = "batch_medium"  # Medium batches (10-50 events)
    BATCH_LARGE = "batch_large"    # Large batches (50-200 events)
    BULK = "bulk"                  # Bulk processing (200+ events)

@dataclass
class BatchConfig:
    """Configuration for batch processing"""
    strategy: BatchStrategy
    mode: ProcessingMode
    max_batch_size: int
    max_wait_time_seconds: float
    similarity_threshold: float
    priority_weights: Dict[str, float]
    token_budget: int
    quality_threshold: float

@dataclass
class EventBatch:
    """Batch of related security events"""
    batch_id: str
    events: List[Dict[str, Any]]
    category: EventCategory
    complexity: AnalysisComplexity
    priority_score: float
    estimated_tokens: int
    created_at: datetime
    processing_strategy: str

@dataclass
class BatchResult:
    """Result of batch processing"""
    batch_id: str
    events_processed: int
    analysis_summary: str
    individual_decisions: List[Dict[str, Any]]
    patterns_detected: List[str]
    risk_assessment: Dict[str, float]
    recommendations: List[str]
    processing_time_ms: float
    token_usage: int
    quality_score: float

@dataclass
class ProcessingMetrics:
    """Metrics for batch processing performance"""
    total_batches: int
    total_events: int
    avg_batch_size: float
    avg_processing_time_ms: float
    avg_token_usage: int
    token_efficiency: float  # events per token
    quality_average: float
    throughput_events_per_second: float

class EventSimilarityCalculator:
    """Calculates similarity between security events for intelligent batching"""

    def __init__(self):
        self.feature_weights = {
            'event_type': 0.3,
            'operation': 0.25,
            'resource_type': 0.2,
            'user_pattern': 0.15,
            'parameters': 0.1
        }

    def calculate_similarity(self, event1: Dict[str, Any], event2: Dict[str, Any]) -> float:
        """Calculate similarity score between two events (0.0 to 1.0)"""

        similarity_score = 0.0

        # Event type similarity
        if event1.get('event_type') == event2.get('event_type'):
            similarity_score += self.feature_weights['event_type']

        # Operation similarity
        if event1.get('operation') == event2.get('operation'):
            similarity_score += self.feature_weights['operation']

        # Resource type similarity
        resource1_type = self._get_resource_type(event1.get('resource', ''))
        resource2_type = self._get_resource_type(event2.get('resource', ''))
        if resource1_type == resource2_type:
            similarity_score += self.feature_weights['resource_type']

        # User pattern similarity
        if event1.get('user_id') == event2.get('user_id'):
            similarity_score += self.feature_weights['user_pattern']

        # Parameter similarity
        param_similarity = self._calculate_parameter_similarity(
            event1.get('parameters', {}), event2.get('parameters', {})
        )
        similarity_score += param_similarity * self.feature_weights['parameters']

        return min(similarity_score, 1.0)

    def _get_resource_type(self, resource: str) -> str:
        """Extract resource type from resource string"""
        if not resource:
            return 'unknown'

        resource_lower = resource.lower()

        if any(ext in resource_lower for ext in ['.json', '.xml', '.yaml', '.config']):
            return 'config'
        elif any(ext in resource_lower for ext in ['.txt', '.log', '.md']):
            return 'text'
        elif any(ext in resource_lower for ext in ['.py', '.js', '.java', '.cpp']):
            return 'code'
        elif 'database' in resource_lower or 'db' in resource_lower:
            return 'database'
        elif any(term in resource_lower for term in ['network', 'http', 'url']):
            return 'network'
        elif any(term in resource_lower for term in ['system', 'admin', 'root']):
            return 'system'
        else:
            return 'file'

    def _calculate_parameter_similarity(self, params1: Dict[str, Any], params2: Dict[str, Any]) -> float:
        """Calculate similarity between parameter sets"""
        if not params1 and not params2:
            return 1.0
        if not params1 or not params2:
            return 0.0

        # Compare common keys
        common_keys = set(params1.keys()) & set(params2.keys())
        if not common_keys:
            return 0.0

        matches = 0
        for key in common_keys:
            if params1[key] == params2[key]:
                matches += 1

        return matches / len(common_keys)

class SecurityBatchProcessor:
    """Intelligent batch processor for security events"""

    def __init__(self, db_path: str = "security_batch_processing.db"):
        self.db_path = db_path
        self.logger = logging.getLogger("security_batch_processor")

        # Initialize components
        self.classifier = SecurityEventClassifier()
        self.compressor = ContextCompressor()
        self.similarity_calc = EventSimilarityCalculator()

        # Processing state
        self.pending_events: List[Dict[str, Any]] = []
        self.active_batches: Dict[str, EventBatch] = {}
        self.completed_batches: List[BatchResult] = []

        # Thread management
        self.processing_lock = threading.RLock()
        self.executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="batch_processor")
        self.stop_processing = False

        # Performance metrics
        self.metrics = ProcessingMetrics(
            total_batches=0, total_events=0, avg_batch_size=0.0,
            avg_processing_time_ms=0.0, avg_token_usage=0, token_efficiency=0.0,
            quality_average=0.0, throughput_events_per_second=0.0
        )

        # Default configurations
        self.batch_configs = self._create_default_configs()

        # Initialize database
        self._init_database()

        self.logger.info("Security Batch Processor initialized")

    def _create_default_configs(self) -> Dict[str, BatchConfig]:
        """Create default batch processing configurations"""
        return {
            "real_time": BatchConfig(
                strategy=BatchStrategy.PRIORITY,
                mode=ProcessingMode.REAL_TIME,
                max_batch_size=1,
                max_wait_time_seconds=0.1,
                similarity_threshold=0.8,
                priority_weights={"critical": 1.0, "high": 0.8, "medium": 0.5, "low": 0.2},
                token_budget=200,
                quality_threshold=0.8
            ),
            "batch_small": BatchConfig(
                strategy=BatchStrategy.SIMILARITY,
                mode=ProcessingMode.BATCH_SMALL,
                max_batch_size=10,
                max_wait_time_seconds=5.0,
                similarity_threshold=0.7,
                priority_weights={"critical": 1.0, "high": 0.8, "medium": 0.5, "low": 0.2},
                token_budget=800,
                quality_threshold=0.75
            ),
            "batch_medium": BatchConfig(
                strategy=BatchStrategy.CATEGORICAL,
                mode=ProcessingMode.BATCH_MEDIUM,
                max_batch_size=50,
                max_wait_time_seconds=30.0,
                similarity_threshold=0.6,
                priority_weights={"critical": 1.0, "high": 0.8, "medium": 0.5, "low": 0.2},
                token_budget=2000,
                quality_threshold=0.7
            ),
            "batch_large": BatchConfig(
                strategy=BatchStrategy.TEMPORAL,
                mode=ProcessingMode.BATCH_LARGE,
                max_batch_size=200,
                max_wait_time_seconds=300.0,
                similarity_threshold=0.5,
                priority_weights={"critical": 1.0, "high": 0.8, "medium": 0.5, "low": 0.2},
                token_budget=5000,
                quality_threshold=0.65
            ),
            "bulk": BatchConfig(
                strategy=BatchStrategy.HYBRID,
                mode=ProcessingMode.BULK,
                max_batch_size=1000,
                max_wait_time_seconds=0.0,  # No waiting for bulk
                similarity_threshold=0.4,
                priority_weights={"critical": 1.0, "high": 0.8, "medium": 0.5, "low": 0.2},
                token_budget=10000,
                quality_threshold=0.6
            )
        }

    def _init_database(self):
        """Initialize database for batch processing tracking"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS batch_processing_history (
                batch_id TEXT PRIMARY KEY,
                created_at TEXT,
                processed_at TEXT,
                event_count INTEGER,
                strategy TEXT,
                processing_time_ms REAL,
                token_usage INTEGER,
                quality_score REAL,
                patterns_detected TEXT,
                risk_summary TEXT
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS processing_metrics (
                timestamp TEXT PRIMARY KEY,
                total_batches INTEGER,
                total_events INTEGER,
                avg_batch_size REAL,
                avg_processing_time REAL,
                token_efficiency REAL,
                throughput_eps REAL
            )
        """)

        conn.commit()
        conn.close()

    async def add_event(self, event_data: Dict[str, Any]) -> str:
        """Add event to processing queue"""

        event_id = event_data.get('event_id', f"evt_{int(time.time() * 1000)}")

        with self.processing_lock:
            self.pending_events.append(event_data)

        # Trigger batch formation if conditions are met
        await self._trigger_batch_formation()

        return event_id

    async def add_events_bulk(self, events: List[Dict[str, Any]]) -> List[str]:
        """Add multiple events for bulk processing"""

        event_ids = []

        with self.processing_lock:
            for event in events:
                event_id = event.get('event_id', f"evt_{int(time.time() * 1000)}")
                event_ids.append(event_id)
                self.pending_events.append(event)

        # Process as bulk immediately
        await self._trigger_batch_formation(force_bulk=True)

        return event_ids

    async def _trigger_batch_formation(self, force_bulk: bool = False):
        """Trigger batch formation based on current conditions"""

        with self.processing_lock:
            if not self.pending_events:
                return

            # Determine appropriate configuration
            config_name = self._select_processing_config(len(self.pending_events), force_bulk)
            config = self.batch_configs[config_name]

            # Form batches based on strategy
            batches = self._form_batches(self.pending_events, config)

            # Submit batches for processing
            for batch in batches:
                asyncio.create_task(self._process_batch(batch, config))

            # Clear processed events
            self.pending_events.clear()

    def _select_processing_config(self, event_count: int, force_bulk: bool = False) -> str:
        """Select optimal processing configuration based on conditions"""

        if force_bulk or event_count >= 200:
            return "bulk"
        elif event_count >= 50:
            return "batch_large"
        elif event_count >= 10:
            return "batch_medium"
        elif event_count >= 2:
            return "batch_small"
        else:
            return "real_time"

    def _form_batches(self, events: List[Dict[str, Any]], config: BatchConfig) -> List[EventBatch]:
        """Form batches based on strategy"""

        if config.strategy == BatchStrategy.TEMPORAL:
            return self._form_temporal_batches(events, config)
        elif config.strategy == BatchStrategy.CATEGORICAL:
            return self._form_categorical_batches(events, config)
        elif config.strategy == BatchStrategy.SIMILARITY:
            return self._form_similarity_batches(events, config)
        elif config.strategy == BatchStrategy.PRIORITY:
            return self._form_priority_batches(events, config)
        else:  # HYBRID
            return self._form_hybrid_batches(events, config)

    def _form_temporal_batches(self, events: List[Dict[str, Any]], config: BatchConfig) -> List[EventBatch]:
        """Form batches based on temporal proximity"""
        batches = []

        # Sort events by timestamp
        sorted_events = sorted(events, key=lambda e: e.get('timestamp', ''))

        current_batch = []
        batch_start_time = None

        for event in sorted_events:
            event_time = datetime.fromisoformat(event.get('timestamp', datetime.now().isoformat()))

            if (not current_batch or
                (event_time - batch_start_time).total_seconds() <= config.max_wait_time_seconds):

                current_batch.append(event)
                if batch_start_time is None:
                    batch_start_time = event_time
            else:
                # Create batch and start new one
                if current_batch:
                    batches.append(self._create_batch(current_batch, config))
                current_batch = [event]
                batch_start_time = event_time

            # Check size limit
            if len(current_batch) >= config.max_batch_size:
                batches.append(self._create_batch(current_batch, config))
                current_batch = []
                batch_start_time = None

        # Add remaining events
        if current_batch:
            batches.append(self._create_batch(current_batch, config))

        return batches

    def _form_categorical_batches(self, events: List[Dict[str, Any]], config: BatchConfig) -> List[EventBatch]:
        """Form batches based on event categories"""
        batches = []
        category_groups: Dict[EventCategory, List[Dict[str, Any]]] = {}

        # Group by category
        for event in events:
            template = self.classifier.classify_event(event)
            category = template.category if template else EventCategory.ANOMALY_DETECTION

            if category not in category_groups:
                category_groups[category] = []
            category_groups[category].append(event)

        # Create batches for each category
        for category, category_events in category_groups.items():
            # Split large categories into smaller batches
            for i in range(0, len(category_events), config.max_batch_size):
                batch_events = category_events[i:i + config.max_batch_size]
                batches.append(self._create_batch(batch_events, config))

        return batches

    def _form_similarity_batches(self, events: List[Dict[str, Any]], config: BatchConfig) -> List[EventBatch]:
        """Form batches based on event similarity"""
        batches = []
        remaining_events = events.copy()

        while remaining_events:
            # Start new batch with first event
            current_batch = [remaining_events.pop(0)]

            # Find similar events
            to_remove = []
            for i, event in enumerate(remaining_events):
                if len(current_batch) >= config.max_batch_size:
                    break

                # Check similarity with batch events
                max_similarity = 0.0
                for batch_event in current_batch:
                    similarity = self.similarity_calc.calculate_similarity(batch_event, event)
                    max_similarity = max(max_similarity, similarity)

                if max_similarity >= config.similarity_threshold:
                    current_batch.append(event)
                    to_remove.append(i)

            # Remove added events (in reverse order to maintain indices)
            for i in reversed(to_remove):
                remaining_events.pop(i)

            batches.append(self._create_batch(current_batch, config))

        return batches

    def _form_priority_batches(self, events: List[Dict[str, Any]], config: BatchConfig) -> List[EventBatch]:
        """Form batches based on priority/severity"""
        batches = []

        # Sort by priority score
        def get_priority_score(event):
            severity = event.get('severity', 2)  # Default to INFO
            risk_score = event.get('risk_score', 0.5)
            return severity * 0.7 + risk_score * 0.3

        sorted_events = sorted(events, key=get_priority_score, reverse=True)

        # Create batches maintaining priority order
        for i in range(0, len(sorted_events), config.max_batch_size):
            batch_events = sorted_events[i:i + config.max_batch_size]
            batches.append(self._create_batch(batch_events, config))

        return batches

    def _form_hybrid_batches(self, events: List[Dict[str, Any]], config: BatchConfig) -> List[EventBatch]:
        """Form batches using hybrid strategy"""
        # First group by category, then by similarity within categories
        category_groups: Dict[EventCategory, List[Dict[str, Any]]] = {}

        for event in events:
            template = self.classifier.classify_event(event)
            category = template.category if template else EventCategory.ANOMALY_DETECTION

            if category not in category_groups:
                category_groups[category] = []
            category_groups[category].append(event)

        batches = []
        for category, category_events in category_groups.items():
            # Use similarity batching within each category
            temp_config = BatchConfig(
                strategy=BatchStrategy.SIMILARITY,
                mode=config.mode,
                max_batch_size=config.max_batch_size,
                max_wait_time_seconds=config.max_wait_time_seconds,
                similarity_threshold=config.similarity_threshold * 0.8,  # Slightly lower threshold
                priority_weights=config.priority_weights,
                token_budget=config.token_budget,
                quality_threshold=config.quality_threshold
            )

            category_batches = self._form_similarity_batches(category_events, temp_config)
            batches.extend(category_batches)

        return batches

    def _create_batch(self, events: List[Dict[str, Any]], config: BatchConfig) -> EventBatch:
        """Create an EventBatch from a list of events"""

        batch_id = hashlib.md5(f"{len(events)}_{time.time()}".encode()).hexdigest()[:12]

        # Determine batch characteristics
        categories = []
        complexities = []
        total_tokens = 0

        for event in events:
            template = self.classifier.classify_event(event)
            if template:
                categories.append(template.category)
                complexities.append(template.analysis_complexity)
                # Estimate tokens for this event
                compressed = self.compressor.compress_event_context(event, template)
                total_tokens += compressed.token_count

        # Determine primary category and complexity
        primary_category = max(set(categories), key=categories.count) if categories else EventCategory.ANOMALY_DETECTION
        primary_complexity = max(set(complexities), key=complexities.count) if complexities else AnalysisComplexity.SIMPLE

        # Calculate priority score
        priority_score = sum(
            event.get('severity', 2) * 0.5 + event.get('risk_score', 0.5) * 0.5
            for event in events
        ) / len(events)

        return EventBatch(
            batch_id=batch_id,
            events=events,
            category=primary_category,
            complexity=primary_complexity,
            priority_score=priority_score,
            estimated_tokens=total_tokens,
            created_at=datetime.now(),
            processing_strategy=config.strategy.value
        )

    async def _process_batch(self, batch: EventBatch, config: BatchConfig) -> BatchResult:
        """Process a batch of events"""

        start_time = time.time()

        try:
            with self.processing_lock:
                self.active_batches[batch.batch_id] = batch

            # Generate batch analysis
            batch_analysis = await self._analyze_batch(batch, config)

            # Process individual events
            individual_results = []
            for event in batch.events:
                result = await self._process_single_event(event, batch_analysis)
                individual_results.append(result)

            # Detect patterns across batch
            patterns = self._detect_batch_patterns(batch.events)

            # Generate risk assessment
            risk_assessment = self._assess_batch_risk(batch.events)

            # Generate recommendations
            recommendations = self._generate_batch_recommendations(batch.events, patterns, risk_assessment)

            processing_time = (time.time() - start_time) * 1000

            # Create result
            result = BatchResult(
                batch_id=batch.batch_id,
                events_processed=len(batch.events),
                analysis_summary=batch_analysis,
                individual_decisions=individual_results,
                patterns_detected=patterns,
                risk_assessment=risk_assessment,
                recommendations=recommendations,
                processing_time_ms=processing_time,
                token_usage=batch.estimated_tokens,
                quality_score=self._calculate_quality_score(batch, individual_results)
            )

            # Update metrics
            self._update_metrics(result)

            # Store result
            self._store_batch_result(result)

            with self.processing_lock:
                self.active_batches.pop(batch.batch_id, None)
                self.completed_batches.append(result)

            self.logger.info(f"Processed batch {batch.batch_id}: {len(batch.events)} events in {processing_time:.1f}ms")

            return result

        except Exception as e:
            self.logger.error(f"Error processing batch {batch.batch_id}: {e}")
            with self.processing_lock:
                self.active_batches.pop(batch.batch_id, None)
            raise

    async def _analyze_batch(self, batch: EventBatch, config: BatchConfig) -> str:
        """Generate batch-level analysis"""

        # Create summary of batch characteristics
        event_types = [event.get('event_type', 'unknown') for event in batch.events]
        operations = [event.get('operation', 'unknown') for event in batch.events]
        users = [event.get('user_id', 'unknown') for event in batch.events]

        # Count occurrences
        type_counts = {t: event_types.count(t) for t in set(event_types)}
        operation_counts = {o: operations.count(o) for o in set(operations)}
        user_counts = {u: users.count(u) for u in set(users)}

        # Generate analysis summary
        analysis = f"""
Batch Analysis Summary:
- Events: {len(batch.events)}
- Category: {batch.category.value}
- Complexity: {batch.complexity.value}
- Priority Score: {batch.priority_score:.2f}

Event Distribution:
- Types: {dict(list(type_counts.items())[:3])}
- Operations: {dict(list(operation_counts.items())[:3])}
- Users: {len(set(users))} unique users

Processing Strategy: {batch.processing_strategy}
Estimated Tokens: {batch.estimated_tokens}
""".strip()

        return analysis

    async def _process_single_event(self, event: Dict[str, Any], batch_context: str) -> Dict[str, Any]:
        """Process individual event within batch context"""

        # Classify event
        template = self.classifier.classify_event(event)

        if not template:
            return {
                "event_id": event.get('event_id', 'unknown'),
                "decision": "allow",
                "confidence": "low",
                "reasoning": "No template matched - default allow",
                "template_used": None
            }

        # Compress context
        compressed = self.compressor.compress_event_context(event, template)

        # Generate decision based on template and batch context
        decision_info = self._make_template_decision(event, template, compressed, batch_context)

        return {
            "event_id": event.get('event_id', 'unknown'),
            "template_id": template.template_id,
            "decision": decision_info["decision"],
            "confidence": decision_info["confidence"],
            "reasoning": decision_info["reasoning"],
            "alternatives": decision_info.get("alternatives", []),
            "template_used": template.name,
            "tokens_used": compressed.token_count
        }

    def _make_template_decision(self, event: Dict[str, Any], template, compressed, batch_context: str) -> Dict[str, Any]:
        """Make decision using template logic"""

        operation = event.get('operation', '')
        resource = event.get('resource', '')
        risk_score = event.get('risk_score', 0.5)

        # Check for immediate decisions based on template
        decision = template.common_decisions.get('safe_read', 'allow')
        confidence = "medium"
        reasoning = f"Template-based decision using {template.name}"

        # Risk-based adjustments
        if risk_score > 0.8:
            decision = "block"
            confidence = "high"
            reasoning = f"High risk score ({risk_score:.2f}) - blocked by template"
        elif risk_score > 0.6:
            decision = "allow_with_monitoring"
            confidence = "medium"
            reasoning = f"Medium risk score ({risk_score:.2f}) - allowed with monitoring"

        # Check for risk indicators
        for indicator in compressed.risk_indicators:
            if indicator in template.risk_indicators:
                if decision == "allow":
                    decision = "allow_with_monitoring"
                reasoning += f" Risk indicator detected: {indicator}"

        return {
            "decision": decision,
            "confidence": confidence,
            "reasoning": reasoning,
            "alternatives": template.typical_mitigations[:2]
        }

    def _detect_batch_patterns(self, events: List[Dict[str, Any]]) -> List[str]:
        """Detect patterns across the batch"""
        patterns = []

        # Check for repeated operations
        operations = [event.get('operation', '') for event in events]
        operation_counts = {op: operations.count(op) for op in set(operations)}

        for operation, count in operation_counts.items():
            if count > len(events) * 0.5:  # More than 50% same operation
                patterns.append(f"Repeated operation: {operation} ({count} times)")

        # Check for user behavior patterns
        users = [event.get('user_id', '') for event in events]
        user_counts = {user: users.count(user) for user in set(users)}

        for user, count in user_counts.items():
            if count > 5:  # User appears in many events
                patterns.append(f"High activity user: {user} ({count} events)")

        # Check for time-based patterns
        timestamps = [event.get('timestamp', '') for event in events if event.get('timestamp')]
        if len(timestamps) > 1:
            time_diffs = []
            for i in range(1, len(timestamps)):
                try:
                    t1 = datetime.fromisoformat(timestamps[i-1])
                    t2 = datetime.fromisoformat(timestamps[i])
                    time_diffs.append((t2 - t1).total_seconds())
                except:
                    continue

            if time_diffs and max(time_diffs) < 60:  # All within 1 minute
                patterns.append("Rapid sequence of events (< 1 minute)")

        return patterns

    def _assess_batch_risk(self, events: List[Dict[str, Any]]) -> Dict[str, float]:
        """Assess overall risk for the batch"""
        risk_scores = [event.get('risk_score', 0.5) for event in events]

        return {
            "average_risk": sum(risk_scores) / len(risk_scores),
            "maximum_risk": max(risk_scores),
            "minimum_risk": min(risk_scores),
            "risk_variance": self._calculate_variance(risk_scores),
            "high_risk_events": len([r for r in risk_scores if r > 0.7]) / len(risk_scores)
        }

    def _calculate_variance(self, values: List[float]) -> float:
        """Calculate variance of values"""
        if len(values) < 2:
            return 0.0

        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return variance

    def _generate_batch_recommendations(self, events: List[Dict[str, Any]],
                                      patterns: List[str], risk_assessment: Dict[str, float]) -> List[str]:
        """Generate recommendations for the batch"""
        recommendations = []

        # Risk-based recommendations
        if risk_assessment["average_risk"] > 0.7:
            recommendations.append("High average risk detected - review security policies")

        if risk_assessment["high_risk_events"] > 0.3:
            recommendations.append("Many high-risk events - consider enhanced monitoring")

        # Pattern-based recommendations
        for pattern in patterns:
            if "rapid sequence" in pattern.lower():
                recommendations.append("Rapid event sequence detected - check for automated attacks")
            elif "high activity user" in pattern.lower():
                recommendations.append("High user activity detected - verify legitimate usage")
            elif "repeated operation" in pattern.lower():
                recommendations.append("Repeated operations detected - monitor for anomalous behavior")

        # Event type recommendations
        event_types = [event.get('event_type', '') for event in events]
        violation_count = event_types.count('security_violation')

        if violation_count > len(events) * 0.2:  # More than 20% violations
            recommendations.append("High violation rate - review access controls")

        if not recommendations:
            recommendations.append("No significant security concerns detected in this batch")

        return recommendations

    def _calculate_quality_score(self, batch: EventBatch, results: List[Dict[str, Any]]) -> float:
        """Calculate quality score for batch processing"""

        # Factors affecting quality:
        # 1. Template match rate
        # 2. Confidence levels
        # 3. Processing consistency

        template_matches = len([r for r in results if r.get('template_used')])
        match_rate = template_matches / len(results) if results else 0.0

        confidence_scores = {
            "high": 1.0,
            "medium": 0.7,
            "low": 0.4
        }

        avg_confidence = sum(
            confidence_scores.get(r.get('confidence', 'low'), 0.4)
            for r in results
        ) / len(results) if results else 0.0

        # Combine factors
        quality_score = (match_rate * 0.4 + avg_confidence * 0.6)

        return min(quality_score, 1.0)

    def _update_metrics(self, result: BatchResult):
        """Update processing metrics"""

        with self.processing_lock:
            self.metrics.total_batches += 1
            self.metrics.total_events += result.events_processed

            # Update averages
            total_batches = self.metrics.total_batches

            self.metrics.avg_batch_size = (
                (self.metrics.avg_batch_size * (total_batches - 1) + result.events_processed) / total_batches
            )

            self.metrics.avg_processing_time_ms = (
                (self.metrics.avg_processing_time_ms * (total_batches - 1) + result.processing_time_ms) / total_batches
            )

            self.metrics.avg_token_usage = (
                (self.metrics.avg_token_usage * (total_batches - 1) + result.token_usage) / total_batches
            )

            self.metrics.token_efficiency = (
                self.metrics.total_events /
                (self.metrics.avg_token_usage * total_batches) if self.metrics.avg_token_usage > 0 else 0.0
            )

            self.metrics.quality_average = (
                (self.metrics.quality_average * (total_batches - 1) + result.quality_score) / total_batches
            )

            # Calculate throughput (events per second)
            total_time_seconds = (self.metrics.avg_processing_time_ms * total_batches) / 1000
            self.metrics.throughput_events_per_second = (
                self.metrics.total_events / total_time_seconds if total_time_seconds > 0 else 0.0
            )

    def _store_batch_result(self, result: BatchResult):
        """Store batch result in database"""

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO batch_processing_history
            (batch_id, created_at, processed_at, event_count, strategy,
             processing_time_ms, token_usage, quality_score, patterns_detected, risk_summary)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            result.batch_id,
            datetime.now().isoformat(),
            datetime.now().isoformat(),
            result.events_processed,
            "unknown",  # Would be passed from config
            result.processing_time_ms,
            result.token_usage,
            result.quality_score,
            json.dumps(result.patterns_detected),
            json.dumps(result.risk_assessment)
        ))

        conn.commit()
        conn.close()

    def get_processing_metrics(self) -> ProcessingMetrics:
        """Get current processing metrics"""
        return self.metrics

    def get_batch_status(self) -> Dict[str, Any]:
        """Get current batch processing status"""

        with self.processing_lock:
            return {
                "pending_events": len(self.pending_events),
                "active_batches": len(self.active_batches),
                "completed_batches": len(self.completed_batches),
                "total_events_processed": self.metrics.total_events,
                "average_batch_size": self.metrics.avg_batch_size,
                "processing_efficiency": self.metrics.token_efficiency,
                "quality_average": self.metrics.quality_average
            }

    def shutdown(self):
        """Shutdown batch processor"""
        self.stop_processing = True
        self.executor.shutdown(wait=True)
        self.logger.info("Security Batch Processor shutdown complete")

async def demo_batch_processor():
    """Demonstrate batch processing capabilities"""

    print("⚡ Security Batch Processor Demo")
    print("=" * 60)

    processor = SecurityBatchProcessor("demo_batch_processing.db")

    # Create test events
    test_events = [
        {
            "event_id": f"evt_{i}",
            "event_type": "permission_check",
            "operation": "file_read",
            "resource": f"/home/user/file_{i}.txt",
            "user_id": f"user_{i % 3}",
            "timestamp": datetime.now().isoformat(),
            "risk_score": 0.2 + (i % 10) * 0.05,
            "severity": 2
        }
        for i in range(15)
    ]

    # Add some security violations
    test_events.extend([
        {
            "event_id": "evt_violation_1",
            "event_type": "security_violation",
            "operation": "file_access",
            "resource": "../../../etc/passwd",
            "user_id": "user_1",
            "timestamp": datetime.now().isoformat(),
            "risk_score": 0.9,
            "severity": 5
        },
        {
            "event_id": "evt_violation_2",
            "event_type": "privilege_escalation",
            "operation": "sudo_request",
            "resource": "system_admin",
            "user_id": "user_2",
            "timestamp": datetime.now().isoformat(),
            "risk_score": 0.8,
            "severity": 4
        }
    ])

    print(f"Processing {len(test_events)} test events...")

    # Test bulk processing
    start_time = time.time()
    await processor.add_events_bulk(test_events)

    # Wait for processing to complete
    await asyncio.sleep(2)

    processing_time = (time.time() - start_time) * 1000

    # Get results
    metrics = processor.get_processing_metrics()
    status = processor.get_batch_status()

    print(f"\n📊 Processing Results:")
    print(f"Total Processing Time: {processing_time:.1f}ms")
    print(f"Events Processed: {metrics.total_events}")
    print(f"Batches Created: {metrics.total_batches}")
    print(f"Average Batch Size: {metrics.avg_batch_size:.1f}")
    print(f"Average Processing Time: {metrics.avg_processing_time_ms:.1f}ms per batch")
    print(f"Token Efficiency: {metrics.token_efficiency:.2f} events/token")
    print(f"Quality Average: {metrics.quality_average:.2%}")
    print(f"Throughput: {metrics.throughput_events_per_second:.1f} events/second")

    print(f"\n🎯 Batch Status:")
    print(f"Completed Batches: {status['completed_batches']}")
    print(f"Processing Efficiency: {status['processing_efficiency']:.3f}")

    # Show sample results
    if processor.completed_batches:
        sample_batch = processor.completed_batches[0]
        print(f"\n📋 Sample Batch Result:")
        print(f"Batch ID: {sample_batch.batch_id}")
        print(f"Events Processed: {sample_batch.events_processed}")
        print(f"Processing Time: {sample_batch.processing_time_ms:.1f}ms")
        print(f"Token Usage: {sample_batch.token_usage}")
        print(f"Quality Score: {sample_batch.quality_score:.2%}")
        print(f"Patterns Detected: {sample_batch.patterns_detected}")

    processor.shutdown()

    # Cleanup
    import os
    if os.path.exists("demo_batch_processing.db"):
        os.remove("demo_batch_processing.db")

    print("\n✅ Security Batch Processor Demo Complete!")

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    asyncio.run(demo_batch_processor())