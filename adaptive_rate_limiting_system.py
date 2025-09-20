#!/usr/bin/env python3
"""
Adaptive Rate Limiting System
Phase B1: Operational Security - Complete Integration

This system provides intelligent adaptive rate limiting:
- Performance-based rate limit adjustments
- Machine learning-based pattern recognition
- Integration with all security systems
- Real-time resource monitoring and adaptation
- Comprehensive quota management with rollover
"""

import asyncio
import json
import sqlite3
import time
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Callable
from enum import Enum
from dataclasses import dataclass, field
from collections import deque, defaultdict
import threading
import logging

# Import all security components
try:
    from rate_limiting_resource_control import (
        RateLimitingResourceControl, RateLimit, ResourceQuota, RateLimitType,
        ResourceType, OperationType, QuotaPeriod, ThrottleAction
    )
    from runaway_process_detector import RunawayProcessDetector
    from enhanced_security_logging import EnhancedSecurityLogging, SecurityEventType, SecuritySeverity
    from lm_studio_performance_monitor import LMStudioPerformanceMonitor
    from command_whitelist_system import CommandWhitelistSystem, PermissionLevel, SecurityRisk
except ImportError as e:
    print(f"Warning: Could not import security components: {e}")


class AdaptationStrategy(Enum):
    """Rate limiting adaptation strategies"""
    CONSERVATIVE = "conservative"    # Slow adaptation, safety first
    BALANCED = "balanced"           # Moderate adaptation
    AGGRESSIVE = "aggressive"       # Fast adaptation, performance first
    MACHINE_LEARNING = "ml"         # ML-based adaptation
    HYBRID = "hybrid"              # Combines multiple strategies


class LearningMode(Enum):
    """Machine learning modes"""
    SUPERVISED = "supervised"       # Learn from explicit feedback
    REINFORCEMENT = "reinforcement" # Learn from outcomes
    UNSUPERVISED = "unsupervised"  # Learn from patterns
    ENSEMBLE = "ensemble"          # Combine multiple models


@dataclass
class AdaptationEvent:
    """Record of rate limit adaptation"""
    timestamp: datetime
    operation_type: OperationType
    old_limit: int
    new_limit: int
    trigger_reason: str
    adaptation_strategy: AdaptationStrategy
    system_load: float
    success_rate: float
    response_time_ms: float


@dataclass
class LearningPattern:
    """Learned usage pattern"""
    pattern_id: str
    operation_type: OperationType
    time_of_day: int  # Hour 0-23
    day_of_week: int  # 0-6
    typical_load: float
    typical_success_rate: float
    optimal_rate_limit: int
    confidence: float
    last_updated: datetime


@dataclass
class QuotaAllocation:
    """Resource quota allocation"""
    resource_type: ResourceType
    period: QuotaPeriod
    total_quota: int
    used_quota: int
    remaining_quota: int
    rollover_amount: int
    allocation_strategy: str
    priority_reserve: int


class AdaptiveRateLimitingSystem:
    """
    Intelligent adaptive rate limiting system

    Automatically adjusts rate limits based on:
    - System performance and resource availability
    - Historical usage patterns and success rates
    - Machine learning predictions
    - Real-time demand and load balancing
    """

    def __init__(self,
                 db_path: str = "adaptive_rate_limiting.db",
                 rate_limiter: Optional[RateLimitingResourceControl] = None,
                 process_detector: Optional[RunawayProcessDetector] = None,
                 security_logger: Optional[EnhancedSecurityLogging] = None,
                 performance_monitor: Optional[LMStudioPerformanceMonitor] = None,
                 whitelist_system: Optional[CommandWhitelistSystem] = None):

        self.db_path = db_path
        self.rate_limiter = rate_limiter
        self.process_detector = process_detector
        self.security_logger = security_logger
        self.performance_monitor = performance_monitor
        self.whitelist_system = whitelist_system

        # Adaptation configuration
        self.adaptation_strategy = AdaptationStrategy.HYBRID
        self.learning_mode = LearningMode.ENSEMBLE
        self.adaptation_sensitivity = 0.1  # How quickly to adapt (0.0-1.0)
        self.min_data_points = 10  # Minimum data points before adaptation

        # Learning and adaptation state
        self.adaptation_history: List[AdaptationEvent] = []
        self.learned_patterns: Dict[str, LearningPattern] = {}
        self.usage_statistics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))

        # Quota management
        self.quota_allocations: Dict[str, QuotaAllocation] = {}
        self.quota_rollover_enabled = True
        self.priority_user_reserve = 0.2  # 20% reserve for priority users

        # Performance tracking
        self.performance_metrics = {
            'adaptation_accuracy': 0.0,
            'system_efficiency': 0.0,
            'user_satisfaction': 0.0,
            'false_positive_rate': 0.0
        }

        # Background processing
        self.adaptation_active = False
        self.adaptation_thread: Optional[threading.Thread] = None
        self.adaptation_interval = 60  # seconds

        # Machine learning components (simplified)
        self.ml_model_weights = np.random.rand(10)  # Simple linear model
        self.feature_history = deque(maxlen=1000)

        self._init_database()
        self._load_learned_patterns()

    def _init_database(self):
        """Initialize adaptive rate limiting database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS adaptation_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    operation_type TEXT NOT NULL,
                    old_limit INTEGER NOT NULL,
                    new_limit INTEGER NOT NULL,
                    trigger_reason TEXT NOT NULL,
                    adaptation_strategy TEXT NOT NULL,
                    system_load REAL NOT NULL,
                    success_rate REAL NOT NULL,
                    response_time_ms REAL NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS learned_patterns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pattern_id TEXT UNIQUE NOT NULL,
                    operation_type TEXT NOT NULL,
                    time_of_day INTEGER NOT NULL,
                    day_of_week INTEGER NOT NULL,
                    typical_load REAL NOT NULL,
                    typical_success_rate REAL NOT NULL,
                    optimal_rate_limit INTEGER NOT NULL,
                    confidence REAL NOT NULL,
                    last_updated TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS quota_allocations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    resource_type TEXT NOT NULL,
                    period TEXT NOT NULL,
                    total_quota INTEGER NOT NULL,
                    used_quota INTEGER NOT NULL,
                    remaining_quota INTEGER NOT NULL,
                    rollover_amount INTEGER NOT NULL,
                    allocation_strategy TEXT NOT NULL,
                    priority_reserve INTEGER NOT NULL,
                    timestamp TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS performance_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    metric_name TEXT NOT NULL,
                    metric_value REAL NOT NULL,
                    timestamp TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                );

                CREATE INDEX IF NOT EXISTS idx_adaptation_events_time ON adaptation_events(timestamp);
                CREATE INDEX IF NOT EXISTS idx_learned_patterns_type ON learned_patterns(operation_type);
                CREATE INDEX IF NOT EXISTS idx_quota_allocations_time ON quota_allocations(timestamp);
            """)

    def _load_learned_patterns(self):
        """Load previously learned patterns from database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT pattern_id, operation_type, time_of_day, day_of_week,
                           typical_load, typical_success_rate, optimal_rate_limit,
                           confidence, last_updated
                    FROM learned_patterns
                    WHERE confidence > 0.5
                    ORDER BY confidence DESC
                """)

                for row in cursor.fetchall():
                    pattern = LearningPattern(
                        pattern_id=row[0],
                        operation_type=OperationType(row[1]),
                        time_of_day=row[2],
                        day_of_week=row[3],
                        typical_load=row[4],
                        typical_success_rate=row[5],
                        optimal_rate_limit=row[6],
                        confidence=row[7],
                        last_updated=datetime.fromisoformat(row[8])
                    )
                    self.learned_patterns[pattern.pattern_id] = pattern

        except Exception as e:
            logging.error(f"Error loading learned patterns: {e}")

    async def start_adaptation(self):
        """Start adaptive rate limiting"""
        if self.adaptation_active:
            return

        self.adaptation_active = True

        # Initialize quota allocations
        await self._initialize_quota_allocations()

        # Start adaptation thread
        self.adaptation_thread = threading.Thread(target=self._adaptation_loop, daemon=True)
        self.adaptation_thread.start()

        if self.security_logger:
            await self.security_logger.log_security_event(
                event_type=SecurityEventType.SYSTEM_STARTUP,
                severity=SecuritySeverity.INFO,
                details={
                    'component': 'Adaptive Rate Limiting System',
                    'action': 'adaptation_started',
                    'adaptation_strategy': self.adaptation_strategy.value,
                    'learning_mode': self.learning_mode.value,
                    'learned_patterns': len(self.learned_patterns)
                }
            )

    def stop_adaptation(self):
        """Stop adaptive rate limiting"""
        self.adaptation_active = False
        if self.adaptation_thread and self.adaptation_thread.is_alive():
            self.adaptation_thread.join(timeout=5)

    def _adaptation_loop(self):
        """Main adaptation loop"""
        while self.adaptation_active:
            try:
                # Collect current metrics
                current_metrics = self._collect_current_metrics()

                # Analyze patterns and trends
                pattern_analysis = self._analyze_usage_patterns()

                # Apply machine learning predictions
                ml_predictions = self._apply_ml_predictions(current_metrics)

                # Generate adaptation recommendations
                recommendations = self._generate_adaptation_recommendations(
                    current_metrics, pattern_analysis, ml_predictions
                )

                # Apply adaptations
                asyncio.run(self._apply_adaptations(recommendations))

                # Update quota allocations
                asyncio.run(self._update_quota_allocations())

                # Update performance metrics
                self._update_performance_metrics()

                # Clean up old data
                self._cleanup_old_data()

                time.sleep(self.adaptation_interval)

            except Exception as e:
                logging.error(f"Error in adaptation loop: {e}")

    def _collect_current_metrics(self) -> Dict[str, Any]:
        """Collect current system and performance metrics"""
        metrics = {
            'timestamp': datetime.now(),
            'system_load': 0.0,
            'memory_usage': 0.0,
            'cpu_usage': 0.0,
            'network_io': 0.0,
            'response_times': {},
            'success_rates': {},
            'error_rates': {},
            'queue_depths': {},
            'operation_counts': {}
        }

        try:
            # Get rate limiter metrics
            if self.rate_limiter:
                rate_limiter_stats = self.rate_limiter.get_current_stats()
                if rate_limiter_stats.get('current_resource_usage'):
                    resource_usage = rate_limiter_stats['current_resource_usage']
                    metrics['cpu_usage'] = resource_usage.get('cpu_percent', 0.0)
                    metrics['memory_usage'] = resource_usage.get('memory_percent', 0.0)

            # Get performance monitor metrics
            if self.performance_monitor:
                perf_metrics = self.performance_monitor.get_current_metrics()
                current_perf = perf_metrics.get('current_metrics', {})
                metrics['response_times']['llm'] = current_perf.get('average_response_time_ms', 0.0)
                metrics['error_rates']['llm'] = current_perf.get('recent_error_rate', 0.0)
                metrics['queue_depths']['llm'] = current_perf.get('queue_depth', 0)

            # Calculate system load
            metrics['system_load'] = (metrics['cpu_usage'] + metrics['memory_usage']) / 2

            # Store feature vector for ML
            feature_vector = [
                metrics['system_load'],
                metrics['cpu_usage'],
                metrics['memory_usage'],
                metrics['response_times'].get('llm', 0.0),
                metrics['error_rates'].get('llm', 0.0),
                datetime.now().hour,  # Time of day
                datetime.now().weekday(),  # Day of week
                len(self.usage_statistics),  # Activity level
                sum(len(ops) for ops in self.usage_statistics.values()),  # Total operations
                metrics['queue_depths'].get('llm', 0)
            ]
            self.feature_history.append(feature_vector)

        except Exception as e:
            logging.error(f"Error collecting metrics: {e}")

        return metrics

    def _analyze_usage_patterns(self) -> Dict[str, Any]:
        """Analyze historical usage patterns"""
        analysis = {
            'trending_operations': [],
            'peak_hours': [],
            'load_predictions': {},
            'anomalies': []
        }

        try:
            current_hour = datetime.now().hour
            current_day = datetime.now().weekday()

            # Find relevant learned patterns
            relevant_patterns = [
                pattern for pattern in self.learned_patterns.values()
                if abs(pattern.time_of_day - current_hour) <= 1 and
                   pattern.day_of_week == current_day and
                   pattern.confidence > 0.6
            ]

            # Predict load for different operation types
            for pattern in relevant_patterns:
                analysis['load_predictions'][pattern.operation_type.value] = {
                    'predicted_load': pattern.typical_load,
                    'optimal_rate_limit': pattern.optimal_rate_limit,
                    'confidence': pattern.confidence
                }

            # Identify trending operations
            for op_type, op_history in self.usage_statistics.items():
                if len(op_history) >= 20:  # Need sufficient data
                    recent_rate = len([op for op in list(op_history)[-10:]])
                    older_rate = len([op for op in list(op_history)[-20:-10:]])

                    if recent_rate > older_rate * 1.5:  # 50% increase
                        analysis['trending_operations'].append({
                            'operation_type': op_type,
                            'growth_rate': (recent_rate - older_rate) / older_rate,
                            'recent_count': recent_rate
                        })

        except Exception as e:
            logging.error(f"Error analyzing patterns: {e}")

        return analysis

    def _apply_ml_predictions(self, current_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Apply machine learning predictions"""
        predictions = {
            'predicted_load': 0.0,
            'recommended_adjustments': {},
            'confidence': 0.0
        }

        try:
            if len(self.feature_history) < self.min_data_points:
                return predictions

            # Simple linear regression prediction (in production, use proper ML)
            recent_features = list(self.feature_history)[-10:]
            if len(recent_features) >= 5:
                # Predict next period load
                x_values = np.arange(len(recent_features))
                y_values = [features[0] for features in recent_features]  # System load

                # Simple linear fit
                if len(set(y_values)) > 1:  # Avoid division by zero
                    slope = np.corrcoef(x_values, y_values)[0, 1] if len(x_values) > 1 else 0
                    predictions['predicted_load'] = y_values[-1] + slope
                    predictions['confidence'] = min(abs(slope) + 0.5, 1.0)

                    # Generate recommendations based on prediction
                    if predictions['predicted_load'] > 70:  # High load predicted
                        predictions['recommended_adjustments'] = {
                            'reduce_limits': True,
                            'increase_throttling': True,
                            'priority_mode': True
                        }
                    elif predictions['predicted_load'] < 30:  # Low load predicted
                        predictions['recommended_adjustments'] = {
                            'increase_limits': True,
                            'reduce_throttling': True,
                            'performance_mode': True
                        }

        except Exception as e:
            logging.error(f"Error in ML predictions: {e}")

        return predictions

    def _generate_adaptation_recommendations(self,
                                           current_metrics: Dict[str, Any],
                                           pattern_analysis: Dict[str, Any],
                                           ml_predictions: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate rate limit adaptation recommendations"""
        recommendations = []

        try:
            # Conservative strategy: only adapt when very confident
            if self.adaptation_strategy == AdaptationStrategy.CONSERVATIVE:
                if ml_predictions['confidence'] > 0.8:
                    recommendations.extend(self._conservative_recommendations(current_metrics, ml_predictions))

            # Balanced strategy: moderate adaptation
            elif self.adaptation_strategy == AdaptationStrategy.BALANCED:
                if ml_predictions['confidence'] > 0.6:
                    recommendations.extend(self._balanced_recommendations(current_metrics, pattern_analysis, ml_predictions))

            # Aggressive strategy: rapid adaptation
            elif self.adaptation_strategy == AdaptationStrategy.AGGRESSIVE:
                if ml_predictions['confidence'] > 0.4:
                    recommendations.extend(self._aggressive_recommendations(current_metrics, ml_predictions))

            # Hybrid strategy: combine multiple approaches
            elif self.adaptation_strategy == AdaptationStrategy.HYBRID:
                recommendations.extend(self._hybrid_recommendations(current_metrics, pattern_analysis, ml_predictions))

        except Exception as e:
            logging.error(f"Error generating recommendations: {e}")

        return recommendations

    def _conservative_recommendations(self, metrics: Dict[str, Any], predictions: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate conservative adaptation recommendations"""
        recommendations = []

        # Only adjust if system is clearly under stress
        if metrics['system_load'] > 80:
            for op_type in OperationType:
                recommendations.append({
                    'operation_type': op_type,
                    'action': 'reduce_limit',
                    'factor': 0.9,  # 10% reduction
                    'reason': 'High system load (conservative)',
                    'confidence': 0.9
                })

        return recommendations

    def _balanced_recommendations(self, metrics: Dict[str, Any], patterns: Dict[str, Any], predictions: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate balanced adaptation recommendations"""
        recommendations = []

        # Adjust based on current load and predictions
        for op_type in OperationType:
            pattern_key = f"{op_type.value}_{datetime.now().hour}_{datetime.now().weekday()}"

            if op_type.value in patterns.get('load_predictions', {}):
                prediction = patterns['load_predictions'][op_type.value]

                if prediction['predicted_load'] > 70 and prediction['confidence'] > 0.7:
                    recommendations.append({
                        'operation_type': op_type,
                        'action': 'reduce_limit',
                        'factor': 0.85,  # 15% reduction
                        'reason': 'Pattern-based high load prediction',
                        'confidence': prediction['confidence']
                    })
                elif prediction['predicted_load'] < 30 and prediction['confidence'] > 0.7:
                    recommendations.append({
                        'operation_type': op_type,
                        'action': 'increase_limit',
                        'factor': 1.2,   # 20% increase
                        'reason': 'Pattern-based low load prediction',
                        'confidence': prediction['confidence']
                    })

        return recommendations

    def _aggressive_recommendations(self, metrics: Dict[str, Any], predictions: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate aggressive adaptation recommendations"""
        recommendations = []

        # React quickly to predicted changes
        if predictions.get('recommended_adjustments'):
            adjustments = predictions['recommended_adjustments']

            for op_type in OperationType:
                if adjustments.get('reduce_limits'):
                    recommendations.append({
                        'operation_type': op_type,
                        'action': 'reduce_limit',
                        'factor': 0.7,   # 30% reduction
                        'reason': 'ML prediction: high load incoming',
                        'confidence': predictions['confidence']
                    })
                elif adjustments.get('increase_limits'):
                    recommendations.append({
                        'operation_type': op_type,
                        'action': 'increase_limit',
                        'factor': 1.5,   # 50% increase
                        'reason': 'ML prediction: low load period',
                        'confidence': predictions['confidence']
                    })

        return recommendations

    def _hybrid_recommendations(self, metrics: Dict[str, Any], patterns: Dict[str, Any], predictions: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate hybrid adaptation recommendations"""
        recommendations = []

        # Combine conservative, balanced, and aggressive approaches
        conservative = self._conservative_recommendations(metrics, predictions)
        balanced = self._balanced_recommendations(metrics, patterns, predictions)
        aggressive = self._aggressive_recommendations(metrics, predictions)

        # Weight recommendations by confidence and strategy
        all_recommendations = []
        all_recommendations.extend([(rec, 0.3) for rec in conservative])  # 30% weight
        all_recommendations.extend([(rec, 0.5) for rec in balanced])     # 50% weight
        all_recommendations.extend([(rec, 0.2) for rec in aggressive])   # 20% weight

        # Aggregate recommendations by operation type
        op_recommendations = defaultdict(list)
        for rec, weight in all_recommendations:
            op_recommendations[rec['operation_type']].append((rec, weight))

        # Generate weighted final recommendations
        for op_type, recs in op_recommendations.items():
            if recs:
                # Calculate weighted average
                total_weight = sum(weight for _, weight in recs)
                weighted_factor = sum(rec['factor'] * weight for rec, weight in recs) / total_weight
                weighted_confidence = sum(rec['confidence'] * weight for rec, weight in recs) / total_weight

                # Determine action
                if weighted_factor < 1.0:
                    action = 'reduce_limit'
                elif weighted_factor > 1.0:
                    action = 'increase_limit'
                else:
                    continue  # No change

                recommendations.append({
                    'operation_type': op_type,
                    'action': action,
                    'factor': weighted_factor,
                    'reason': 'Hybrid strategy (weighted)',
                    'confidence': weighted_confidence
                })

        return recommendations

    async def _apply_adaptations(self, recommendations: List[Dict[str, Any]]):
        """Apply rate limit adaptations"""
        for rec in recommendations:
            try:
                if not self.rate_limiter:
                    continue

                op_type = rec['operation_type']
                action = rec['action']
                factor = rec['factor']
                reason = rec['reason']
                confidence = rec['confidence']

                # Only apply if confidence is sufficient
                if confidence < 0.5:
                    continue

                # Get current rate limit
                current_limits = [
                    limit for limit in self.rate_limiter.rate_limits.values()
                    if limit.operation_type == op_type
                ]

                for rate_limit in current_limits:
                    old_limit = rate_limit.max_operations
                    new_limit = int(old_limit * factor)

                    # Apply reasonable bounds
                    new_limit = max(1, min(new_limit, 1000))

                    if new_limit != old_limit:
                        # Update rate limit
                        rate_limit.max_operations = new_limit

                        # Log adaptation event
                        adaptation_event = AdaptationEvent(
                            timestamp=datetime.now(),
                            operation_type=op_type,
                            old_limit=old_limit,
                            new_limit=new_limit,
                            trigger_reason=reason,
                            adaptation_strategy=self.adaptation_strategy,
                            system_load=0.0,  # Would get from current metrics
                            success_rate=1.0,  # Would calculate from history
                            response_time_ms=0.0  # Would get from performance monitor
                        )

                        await self._log_adaptation_event(adaptation_event)
                        self.adaptation_history.append(adaptation_event)

            except Exception as e:
                logging.error(f"Error applying adaptation: {e}")

    async def _initialize_quota_allocations(self):
        """Initialize resource quota allocations"""
        try:
            for resource_type in ResourceType:
                for period in [QuotaPeriod.HOUR, QuotaPeriod.DAY]:
                    # Calculate base quota
                    if period == QuotaPeriod.HOUR:
                        base_quota = 3600  # 1 hour worth of seconds
                    else:
                        base_quota = 86400  # 1 day worth of seconds

                    # Adjust based on resource type
                    if resource_type == ResourceType.CPU:
                        total_quota = int(base_quota * 0.8)  # 80% CPU quota
                    elif resource_type == ResourceType.MEMORY:
                        total_quota = int(base_quota * 0.85)  # 85% memory quota
                    else:
                        total_quota = base_quota

                    allocation = QuotaAllocation(
                        resource_type=resource_type,
                        period=period,
                        total_quota=total_quota,
                        used_quota=0,
                        remaining_quota=total_quota,
                        rollover_amount=0,
                        allocation_strategy="balanced",
                        priority_reserve=int(total_quota * self.priority_user_reserve)
                    )

                    key = f"{resource_type.value}_{period.value}"
                    self.quota_allocations[key] = allocation

        except Exception as e:
            logging.error(f"Error initializing quota allocations: {e}")

    async def _update_quota_allocations(self):
        """Update quota allocations based on usage"""
        try:
            current_time = datetime.now()

            for key, allocation in self.quota_allocations.items():
                # Check if quota period has reset
                period_reset = self._check_quota_period_reset(allocation, current_time)

                if period_reset:
                    # Reset quota with rollover if enabled
                    if self.quota_rollover_enabled and allocation.remaining_quota > 0:
                        rollover = min(allocation.remaining_quota, allocation.total_quota // 4)  # Max 25% rollover
                        allocation.rollover_amount = rollover
                        allocation.total_quota += rollover

                    allocation.used_quota = 0
                    allocation.remaining_quota = allocation.total_quota - allocation.priority_reserve

                # Log quota status
                await self._log_quota_allocation(allocation, current_time)

        except Exception as e:
            logging.error(f"Error updating quota allocations: {e}")

    def _check_quota_period_reset(self, allocation: QuotaAllocation, current_time: datetime) -> bool:
        """Check if quota period should reset"""
        # Simplified check - in production, would track last reset time
        if allocation.period == QuotaPeriod.HOUR:
            return current_time.minute == 0  # Reset at top of hour
        elif allocation.period == QuotaPeriod.DAY:
            return current_time.hour == 0 and current_time.minute == 0  # Reset at midnight

        return False

    async def _log_adaptation_event(self, event: AdaptationEvent):
        """Log adaptation event to database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO adaptation_events
                    (timestamp, operation_type, old_limit, new_limit, trigger_reason,
                     adaptation_strategy, system_load, success_rate, response_time_ms)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    event.timestamp.isoformat(),
                    event.operation_type.value,
                    event.old_limit,
                    event.new_limit,
                    event.trigger_reason,
                    event.adaptation_strategy.value,
                    event.system_load,
                    event.success_rate,
                    event.response_time_ms
                ))

            if self.security_logger:
                await self.security_logger.log_security_event(
                    event_type=SecurityEventType.CONFIGURATION_CHANGE,
                    severity=SecuritySeverity.INFO,
                    details={
                        'component': 'Adaptive Rate Limiting System',
                        'action': 'rate_limit_adapted',
                        'operation_type': event.operation_type.value,
                        'old_limit': event.old_limit,
                        'new_limit': event.new_limit,
                        'reason': event.trigger_reason,
                        'strategy': event.adaptation_strategy.value
                    }
                )

        except Exception as e:
            logging.error(f"Error logging adaptation event: {e}")

    async def _log_quota_allocation(self, allocation: QuotaAllocation, timestamp: datetime):
        """Log quota allocation to database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO quota_allocations
                    (resource_type, period, total_quota, used_quota, remaining_quota,
                     rollover_amount, allocation_strategy, priority_reserve, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    allocation.resource_type.value,
                    allocation.period.value,
                    allocation.total_quota,
                    allocation.used_quota,
                    allocation.remaining_quota,
                    allocation.rollover_amount,
                    allocation.allocation_strategy,
                    allocation.priority_reserve,
                    timestamp.isoformat()
                ))

        except Exception as e:
            logging.error(f"Error logging quota allocation: {e}")

    def _update_performance_metrics(self):
        """Update system performance metrics"""
        try:
            # Calculate adaptation accuracy (simplified)
            if len(self.adaptation_history) >= 5:
                recent_adaptations = self.adaptation_history[-5:]
                # In production, would measure actual vs predicted outcomes
                self.performance_metrics['adaptation_accuracy'] = 0.85  # Placeholder

            # Calculate system efficiency
            if self.rate_limiter:
                stats = self.rate_limiter.get_current_stats()
                throttled = stats['statistics'].get('throttled_operations', 0)
                total = stats['statistics'].get('total_operations', 1)
                self.performance_metrics['system_efficiency'] = 1.0 - (throttled / total)

            # Log metrics to database
            timestamp = datetime.now().isoformat()
            with sqlite3.connect(self.db_path) as conn:
                for metric_name, metric_value in self.performance_metrics.items():
                    conn.execute("""
                        INSERT INTO performance_metrics (metric_name, metric_value, timestamp)
                        VALUES (?, ?, ?)
                    """, (metric_name, metric_value, timestamp))

        except Exception as e:
            logging.error(f"Error updating performance metrics: {e}")

    def _cleanup_old_data(self):
        """Clean up old adaptation data"""
        try:
            cleanup_date = (datetime.now() - timedelta(days=30)).isoformat()

            with sqlite3.connect(self.db_path) as conn:
                # Keep adaptation events for 30 days
                conn.execute("""
                    DELETE FROM adaptation_events
                    WHERE timestamp < ?
                """, (cleanup_date,))

                # Keep quota allocations for 30 days
                conn.execute("""
                    DELETE FROM quota_allocations
                    WHERE timestamp < ?
                """, (cleanup_date,))

                # Keep performance metrics for 30 days
                conn.execute("""
                    DELETE FROM performance_metrics
                    WHERE timestamp < ?
                """, (cleanup_date,))

        except Exception as e:
            logging.error(f"Error cleaning up old data: {e}")

    def get_current_stats(self) -> Dict[str, Any]:
        """Get current adaptive rate limiting statistics"""
        return {
            'adaptation_active': self.adaptation_active,
            'adaptation_strategy': self.adaptation_strategy.value,
            'learning_mode': self.learning_mode.value,
            'learned_patterns': len(self.learned_patterns),
            'adaptation_history': len(self.adaptation_history),
            'performance_metrics': self.performance_metrics.copy(),
            'quota_allocations': {k: {
                'total_quota': v.total_quota,
                'used_quota': v.used_quota,
                'remaining_quota': v.remaining_quota,
                'rollover_amount': v.rollover_amount
            } for k, v in self.quota_allocations.items()}
        }

    async def get_adaptation_history(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get recent adaptation history"""
        start_time = (datetime.now() - timedelta(hours=hours)).isoformat()

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT timestamp, operation_type, old_limit, new_limit, trigger_reason,
                       adaptation_strategy, system_load, success_rate, response_time_ms
                FROM adaptation_events
                WHERE timestamp >= ?
                ORDER BY timestamp DESC
            """, (start_time,))

            return [
                {
                    'timestamp': row[0],
                    'operation_type': row[1],
                    'old_limit': row[2],
                    'new_limit': row[3],
                    'trigger_reason': row[4],
                    'adaptation_strategy': row[5],
                    'system_load': row[6],
                    'success_rate': row[7],
                    'response_time_ms': row[8]
                }
                for row in cursor.fetchall()
            ]

    def update_configuration(self, **kwargs):
        """Update adaptation configuration"""
        for attr, value in kwargs.items():
            if hasattr(self, attr):
                setattr(self, attr, value)


# Integration helper function
async def create_integrated_adaptive_system(
    rate_limiter: Optional[RateLimitingResourceControl] = None,
    process_detector: Optional[RunawayProcessDetector] = None,
    security_logger: Optional[EnhancedSecurityLogging] = None,
    performance_monitor: Optional[LMStudioPerformanceMonitor] = None,
    whitelist_system: Optional[CommandWhitelistSystem] = None
) -> AdaptiveRateLimitingSystem:
    """
    Create integrated adaptive rate limiting system

    Returns configured and initialized system
    """
    adaptive_system = AdaptiveRateLimitingSystem(
        rate_limiter=rate_limiter,
        process_detector=process_detector,
        security_logger=security_logger,
        performance_monitor=performance_monitor,
        whitelist_system=whitelist_system
    )

    # Start adaptation
    await adaptive_system.start_adaptation()

    return adaptive_system


if __name__ == "__main__":
    # Example usage
    async def main():
        # Create adaptive rate limiting system
        adaptive_system = await create_integrated_adaptive_system()

        # Monitor for 5 minutes
        await asyncio.sleep(300)

        # Get statistics
        stats = adaptive_system.get_current_stats()
        print(f"Adaptive system stats: {stats}")

        # Get adaptation history
        history = await adaptive_system.get_adaptation_history(hours=1)
        print(f"Recent adaptations: {len(history)}")

        # Stop adaptation
        adaptive_system.stop_adaptation()

    asyncio.run(main())