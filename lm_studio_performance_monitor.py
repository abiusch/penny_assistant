#!/usr/bin/env python3
"""
LM Studio Performance Monitoring System for Penny AI Assistant
Task A1.5.4: Performance Monitoring Integration (Day 4)

This system provides comprehensive LM Studio performance monitoring with:
- Real-time response time tracking
- Connection health monitoring
- Token usage analytics
- Error rate monitoring
- Performance degradation alerts
- Integration with security logging system

Supports 70% reduction in security decision latency and 90% connection uptime targets.
"""

import asyncio
import json
import sqlite3
import time
import statistics
import aiohttp
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Callable
from enum import Enum, IntEnum
from dataclasses import dataclass, asdict, field
from pathlib import Path
import threading
from collections import deque, defaultdict
import psutil
import queue

# Import existing security components
try:
    from enhanced_security_logging import EnhancedSecurityLogging, SecurityEventType, SecuritySeverity
    from integrated_security_optimizer import IntegratedSecurityOptimizer
except ImportError as e:
    print(f"Warning: Could not import security components: {e}")


class PerformanceMetricType(Enum):
    """Types of performance metrics tracked"""
    RESPONSE_TIME = "response_time"
    CONNECTION_HEALTH = "connection_health"
    TOKEN_USAGE = "token_usage"
    ERROR_RATE = "error_rate"
    THROUGHPUT = "throughput"
    LATENCY = "latency"
    AVAILABILITY = "availability"
    MEMORY_USAGE = "memory_usage"
    CPU_USAGE = "cpu_usage"
    QUEUE_DEPTH = "queue_depth"


class AlertSeverity(IntEnum):
    """Performance alert severity levels"""
    INFO = 1
    WARNING = 2
    CRITICAL = 3
    EMERGENCY = 4


class ConnectionStatus(Enum):
    """LM Studio connection status"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNSTABLE = "unstable"
    DISCONNECTED = "disconnected"
    RECOVERING = "recovering"


@dataclass
class PerformanceMetric:
    """Individual performance metric data point"""
    metric_id: str
    metric_type: PerformanceMetricType
    value: float
    timestamp: datetime
    context: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)


@dataclass
class PerformanceAlert:
    """Performance degradation alert"""
    alert_id: str
    severity: AlertSeverity
    metric_type: PerformanceMetricType
    threshold_breached: str
    current_value: float
    threshold_value: float
    timestamp: datetime
    description: str
    recommended_action: str
    auto_resolved: bool = False


@dataclass
class ConnectionHealthStatus:
    """LM Studio connection health status"""
    status: ConnectionStatus
    last_successful_request: Optional[datetime]
    consecutive_failures: int
    average_response_time: float
    error_rate: float
    uptime_percentage: float
    last_error: Optional[str]


class LMStudioPerformanceMonitor:
    """
    Comprehensive LM Studio performance monitoring system

    Tracks response times, connection health, token usage, and error rates
    with real-time alerts and dashboard metrics.
    """

    def __init__(self,
                 lm_studio_url: str = "http://localhost:1234",
                 db_path: str = "lm_studio_performance.db",
                 alert_thresholds: Optional[Dict[str, float]] = None,
                 security_logger: Optional[EnhancedSecurityLogging] = None):
        self.lm_studio_url = lm_studio_url
        self.db_path = db_path
        self.security_logger = security_logger

        # Performance thresholds for alerts
        self.alert_thresholds = alert_thresholds or {
            'response_time_ms': 5000,  # 5 seconds
            'error_rate_percent': 10,   # 10% error rate
            'connection_timeout_ms': 10000,  # 10 seconds
            'token_rate_per_second': 1000,   # High token usage
            'memory_usage_percent': 85,      # 85% memory usage
            'cpu_usage_percent': 90,         # 90% CPU usage
            'queue_depth': 50               # Queue backlog
        }

        # Real-time metrics storage (circular buffers)
        self.metrics_buffer_size = 1000
        self.response_times = deque(maxlen=self.metrics_buffer_size)
        self.error_counts = deque(maxlen=self.metrics_buffer_size)
        self.token_usage = deque(maxlen=self.metrics_buffer_size)
        self.connection_events = deque(maxlen=self.metrics_buffer_size)

        # Connection health tracking
        self.connection_health = ConnectionHealthStatus(
            status=ConnectionStatus.DISCONNECTED,
            last_successful_request=None,
            consecutive_failures=0,
            average_response_time=0.0,
            error_rate=0.0,
            uptime_percentage=0.0,
            last_error=None
        )

        # Alert system
        self.active_alerts = {}
        self.alert_callbacks = []
        self.alert_history = deque(maxlen=100)

        # Monitoring state
        self.monitoring_active = False
        self.monitor_thread = None
        self.request_queue = queue.Queue()

        # Performance statistics
        self.stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'total_tokens_processed': 0,
            'total_response_time': 0.0,
            'monitoring_start_time': datetime.now()
        }

        self._init_database()

    def _init_database(self):
        """Initialize performance monitoring database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS performance_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    metric_id TEXT UNIQUE NOT NULL,
                    metric_type TEXT NOT NULL,
                    value REAL NOT NULL,
                    timestamp TEXT NOT NULL,
                    context TEXT,
                    tags TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS performance_alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    alert_id TEXT UNIQUE NOT NULL,
                    severity INTEGER NOT NULL,
                    metric_type TEXT NOT NULL,
                    threshold_breached TEXT NOT NULL,
                    current_value REAL NOT NULL,
                    threshold_value REAL NOT NULL,
                    timestamp TEXT NOT NULL,
                    description TEXT NOT NULL,
                    recommended_action TEXT NOT NULL,
                    resolved_at TEXT,
                    auto_resolved INTEGER DEFAULT 0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS connection_health_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    status TEXT NOT NULL,
                    response_time REAL,
                    error_message TEXT,
                    uptime_percentage REAL,
                    timestamp TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                );

                CREATE INDEX IF NOT EXISTS idx_metrics_type_time ON performance_metrics(metric_type, timestamp);
                CREATE INDEX IF NOT EXISTS idx_alerts_severity_time ON performance_alerts(severity, timestamp);
                CREATE INDEX IF NOT EXISTS idx_health_status_time ON connection_health_log(status, timestamp);
            """)

    async def start_monitoring(self):
        """Start performance monitoring"""
        if self.monitoring_active:
            return

        self.monitoring_active = True
        self.stats['monitoring_start_time'] = datetime.now()

        # Start monitoring thread
        self.monitor_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitor_thread.start()

        # Initial connection health check
        await self._check_connection_health()

        if self.security_logger:
            await self.security_logger.log_security_event(
                event_type=SecurityEventType.SYSTEM_STARTUP,
                severity=SecuritySeverity.INFO,
                details={
                    'component': 'LM Studio Performance Monitor',
                    'action': 'monitoring_started',
                    'lm_studio_url': self.lm_studio_url
                }
            )

    def stop_monitoring(self):
        """Stop performance monitoring"""
        self.monitoring_active = False
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=5)

    def _monitoring_loop(self):
        """Main monitoring loop running in background thread"""
        while self.monitoring_active:
            try:
                # Check connection health every 30 seconds
                asyncio.run(self._check_connection_health())

                # Update system metrics
                self._update_system_metrics()

                # Process alert conditions
                self._check_alert_conditions()

                # Clean up old metrics
                self._cleanup_old_metrics()

                time.sleep(30)  # 30-second monitoring interval

            except Exception as e:
                if self.security_logger:
                    asyncio.run(self.security_logger.log_security_event(
                        event_type=SecurityEventType.SYSTEM_ERROR,
                        severity=SecuritySeverity.ERROR,
                        details={
                            'component': 'LM Studio Performance Monitor',
                            'error': str(e),
                            'action': 'monitoring_loop_error'
                        }
                    ))

    async def _check_connection_health(self):
        """Check LM Studio connection health"""
        start_time = time.time()

        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                async with session.get(f"{self.lm_studio_url}/v1/models") as response:
                    response_time = (time.time() - start_time) * 1000  # Convert to ms

                    if response.status == 200:
                        # Successful connection
                        self.connection_health.status = ConnectionStatus.HEALTHY
                        self.connection_health.last_successful_request = datetime.now()
                        self.connection_health.consecutive_failures = 0

                        # Update response time average
                        self.response_times.append(response_time)
                        if self.response_times:
                            self.connection_health.average_response_time = statistics.mean(self.response_times)

                        # Log health status
                        await self._log_connection_health(response_time=response_time)

                    else:
                        # HTTP error
                        await self._handle_connection_failure(f"HTTP {response.status}")

        except asyncio.TimeoutError:
            await self._handle_connection_failure("Connection timeout")
        except Exception as e:
            await self._handle_connection_failure(str(e))

    async def _handle_connection_failure(self, error_message: str):
        """Handle connection failure"""
        self.connection_health.consecutive_failures += 1
        self.connection_health.last_error = error_message

        # Update connection status based on failure count
        if self.connection_health.consecutive_failures >= 5:
            self.connection_health.status = ConnectionStatus.DISCONNECTED
        elif self.connection_health.consecutive_failures >= 3:
            self.connection_health.status = ConnectionStatus.UNSTABLE
        else:
            self.connection_health.status = ConnectionStatus.DEGRADED

        # Log health status
        await self._log_connection_health(error_message=error_message)

        # Create alert for connection issues
        await self._create_alert(
            AlertSeverity.CRITICAL if self.connection_health.consecutive_failures >= 5 else AlertSeverity.WARNING,
            PerformanceMetricType.CONNECTION_HEALTH,
            f"consecutive_failures >= {self.connection_health.consecutive_failures}",
            self.connection_health.consecutive_failures,
            3.0,
            f"LM Studio connection failing: {error_message}",
            "Check LM Studio service status and network connectivity"
        )

    async def _log_connection_health(self, response_time: Optional[float] = None, error_message: Optional[str] = None):
        """Log connection health to database"""
        # Calculate uptime percentage
        uptime_percentage = self._calculate_uptime_percentage()
        self.connection_health.uptime_percentage = uptime_percentage

        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO connection_health_log
                (status, response_time, error_message, uptime_percentage, timestamp)
                VALUES (?, ?, ?, ?, ?)
            """, (
                self.connection_health.status.value,
                response_time,
                error_message,
                uptime_percentage,
                datetime.now().isoformat()
            ))

    def _calculate_uptime_percentage(self) -> float:
        """Calculate uptime percentage over last 24 hours"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT status, COUNT(*) as count
                    FROM connection_health_log
                    WHERE timestamp > datetime('now', '-24 hours')
                    GROUP BY status
                """)

                status_counts = dict(cursor.fetchall())
                total_checks = sum(status_counts.values())

                if total_checks == 0:
                    return 0.0

                healthy_checks = status_counts.get('healthy', 0)
                return (healthy_checks / total_checks) * 100.0

        except Exception:
            return 0.0

    async def track_llm_request(self,
                              request_data: Dict[str, Any],
                              response_data: Optional[Dict[str, Any]] = None,
                              error: Optional[str] = None) -> Dict[str, Any]:
        """
        Track LLM request performance metrics

        Args:
            request_data: LLM request information
            response_data: LLM response data (if successful)
            error: Error message (if failed)

        Returns:
            Performance metrics for this request
        """
        start_time = time.time()
        request_id = f"req_{int(start_time * 1000000)}"

        # Extract request metrics
        prompt_tokens = request_data.get('prompt_tokens', 0)
        max_tokens = request_data.get('max_tokens', 0)

        metrics = {
            'request_id': request_id,
            'start_time': start_time,
            'prompt_tokens': prompt_tokens,
            'max_tokens': max_tokens,
            'success': error is None
        }

        if response_data:
            # Successful request
            response_time = time.time() - start_time
            completion_tokens = response_data.get('completion_tokens', 0)
            total_tokens = response_data.get('total_tokens', prompt_tokens + completion_tokens)

            metrics.update({
                'response_time_ms': response_time * 1000,
                'completion_tokens': completion_tokens,
                'total_tokens': total_tokens,
                'tokens_per_second': total_tokens / response_time if response_time > 0 else 0
            })

            # Update statistics
            self.stats['total_requests'] += 1
            self.stats['successful_requests'] += 1
            self.stats['total_tokens_processed'] += total_tokens
            self.stats['total_response_time'] += response_time

            # Store in buffers
            self.response_times.append(response_time * 1000)
            self.token_usage.append(total_tokens)

            # Log performance metrics
            await self._log_performance_metric(
                PerformanceMetricType.RESPONSE_TIME,
                response_time * 1000,
                {'request_id': request_id, 'tokens': total_tokens}
            )

            await self._log_performance_metric(
                PerformanceMetricType.TOKEN_USAGE,
                total_tokens,
                {'request_id': request_id, 'response_time_ms': response_time * 1000}
            )

            # Check for performance degradation
            await self._check_response_time_alert(response_time * 1000)

        else:
            # Failed request
            response_time = time.time() - start_time
            metrics.update({
                'response_time_ms': response_time * 1000,
                'error': error
            })

            # Update statistics
            self.stats['total_requests'] += 1
            self.stats['failed_requests'] += 1

            # Store error
            self.error_counts.append(1)

            # Log error metric
            await self._log_performance_metric(
                PerformanceMetricType.ERROR_RATE,
                1.0,
                {'request_id': request_id, 'error': error}
            )

            # Check for error rate alerts
            await self._check_error_rate_alert()

        return metrics

    async def _log_performance_metric(self,
                                    metric_type: PerformanceMetricType,
                                    value: float,
                                    context: Optional[Dict[str, Any]] = None):
        """Log performance metric to database"""
        metric = PerformanceMetric(
            metric_id=f"{metric_type.value}_{int(time.time() * 1000000)}",
            metric_type=metric_type,
            value=value,
            timestamp=datetime.now(),
            context=context or {}
        )

        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO performance_metrics
                (metric_id, metric_type, value, timestamp, context, tags)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                metric.metric_id,
                metric.metric_type.value,
                metric.value,
                metric.timestamp.isoformat(),
                json.dumps(metric.context),
                json.dumps(metric.tags)
            ))

    async def _check_response_time_alert(self, response_time_ms: float):
        """Check if response time exceeds thresholds"""
        threshold = self.alert_thresholds['response_time_ms']

        if response_time_ms > threshold:
            await self._create_alert(
                AlertSeverity.WARNING if response_time_ms < threshold * 2 else AlertSeverity.CRITICAL,
                PerformanceMetricType.RESPONSE_TIME,
                f"response_time > {threshold}ms",
                response_time_ms,
                threshold,
                f"LLM response time ({response_time_ms:.0f}ms) exceeds threshold ({threshold}ms)",
                "Check LM Studio performance and system resources"
            )

    async def _check_error_rate_alert(self):
        """Check if error rate exceeds thresholds"""
        if len(self.error_counts) < 10:  # Need minimum samples
            return

        recent_errors = sum(list(self.error_counts)[-10:])  # Last 10 requests
        error_rate = (recent_errors / 10) * 100

        threshold = self.alert_thresholds['error_rate_percent']

        if error_rate > threshold:
            await self._create_alert(
                AlertSeverity.CRITICAL,
                PerformanceMetricType.ERROR_RATE,
                f"error_rate > {threshold}%",
                error_rate,
                threshold,
                f"LLM error rate ({error_rate:.1f}%) exceeds threshold ({threshold}%)",
                "Check LM Studio logs and connection stability"
            )

    def _update_system_metrics(self):
        """Update system resource metrics"""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            asyncio.run(self._log_performance_metric(
                PerformanceMetricType.CPU_USAGE,
                cpu_percent
            ))

            # Memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            asyncio.run(self._log_performance_metric(
                PerformanceMetricType.MEMORY_USAGE,
                memory_percent
            ))

            # Check system resource alerts
            if cpu_percent > self.alert_thresholds['cpu_usage_percent']:
                asyncio.run(self._create_alert(
                    AlertSeverity.WARNING,
                    PerformanceMetricType.CPU_USAGE,
                    f"cpu_usage > {self.alert_thresholds['cpu_usage_percent']}%",
                    cpu_percent,
                    self.alert_thresholds['cpu_usage_percent'],
                    f"High CPU usage ({cpu_percent:.1f}%)",
                    "Monitor system load and consider resource optimization"
                ))

            if memory_percent > self.alert_thresholds['memory_usage_percent']:
                asyncio.run(self._create_alert(
                    AlertSeverity.WARNING,
                    PerformanceMetricType.MEMORY_USAGE,
                    f"memory_usage > {self.alert_thresholds['memory_usage_percent']}%",
                    memory_percent,
                    self.alert_thresholds['memory_usage_percent'],
                    f"High memory usage ({memory_percent:.1f}%)",
                    "Monitor memory usage and consider resource optimization"
                ))

        except Exception as e:
            print(f"Error updating system metrics: {e}")

    def _check_alert_conditions(self):
        """Check various alert conditions"""
        try:
            # Check queue depth
            queue_depth = self.request_queue.qsize()
            if queue_depth > self.alert_thresholds['queue_depth']:
                asyncio.run(self._create_alert(
                    AlertSeverity.WARNING,
                    PerformanceMetricType.QUEUE_DEPTH,
                    f"queue_depth > {self.alert_thresholds['queue_depth']}",
                    queue_depth,
                    self.alert_thresholds['queue_depth'],
                    f"Request queue backlog ({queue_depth} requests)",
                    "Consider scaling LM Studio or reducing request rate"
                ))

            # Auto-resolve alerts if conditions improve
            self._auto_resolve_alerts()

        except Exception as e:
            print(f"Error checking alert conditions: {e}")

    def _auto_resolve_alerts(self):
        """Auto-resolve alerts when conditions improve"""
        current_time = datetime.now()
        resolved_alerts = []

        for alert_id, alert in self.active_alerts.items():
            # Check if alert condition has been resolved
            should_resolve = False

            if alert.metric_type == PerformanceMetricType.RESPONSE_TIME:
                if self.response_times and statistics.mean(list(self.response_times)[-5:]) < alert.threshold_value:
                    should_resolve = True
            elif alert.metric_type == PerformanceMetricType.ERROR_RATE:
                if len(self.error_counts) >= 5 and sum(list(self.error_counts)[-5:]) == 0:
                    should_resolve = True
            elif alert.metric_type == PerformanceMetricType.CONNECTION_HEALTH:
                if self.connection_health.status == ConnectionStatus.HEALTHY:
                    should_resolve = True

            if should_resolve:
                alert.auto_resolved = True
                resolved_alerts.append(alert_id)

                # Update database
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute("""
                        UPDATE performance_alerts
                        SET resolved_at = ?, auto_resolved = 1
                        WHERE alert_id = ?
                    """, (current_time.isoformat(), alert_id))

        # Remove resolved alerts
        for alert_id in resolved_alerts:
            del self.active_alerts[alert_id]

    async def _create_alert(self,
                          severity: AlertSeverity,
                          metric_type: PerformanceMetricType,
                          threshold_breached: str,
                          current_value: float,
                          threshold_value: float,
                          description: str,
                          recommended_action: str):
        """Create performance alert"""
        alert_id = f"alert_{metric_type.value}_{int(time.time() * 1000)}"

        # Check if similar alert already exists
        existing_alert_key = f"{metric_type.value}_{threshold_breached}"
        if existing_alert_key in [f"{alert.metric_type.value}_{alert.threshold_breached}"
                                 for alert in self.active_alerts.values()]:
            return  # Don't create duplicate alerts

        alert = PerformanceAlert(
            alert_id=alert_id,
            severity=severity,
            metric_type=metric_type,
            threshold_breached=threshold_breached,
            current_value=current_value,
            threshold_value=threshold_value,
            timestamp=datetime.now(),
            description=description,
            recommended_action=recommended_action
        )

        # Store active alert
        self.active_alerts[alert_id] = alert
        self.alert_history.append(alert)

        # Log to database
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO performance_alerts
                (alert_id, severity, metric_type, threshold_breached, current_value,
                 threshold_value, timestamp, description, recommended_action)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                alert.alert_id,
                alert.severity,
                alert.metric_type.value,
                alert.threshold_breached,
                alert.current_value,
                alert.threshold_value,
                alert.timestamp.isoformat(),
                alert.description,
                alert.recommended_action
            ))

        # Trigger alert callbacks
        for callback in self.alert_callbacks:
            try:
                await callback(alert)
            except Exception as e:
                print(f"Error in alert callback: {e}")

        # Log to security system
        if self.security_logger:
            await self.security_logger.log_security_event(
                event_type=SecurityEventType.ANOMALY_DETECTED,
                severity=SecuritySeverity.WARNING if severity <= AlertSeverity.WARNING else SecuritySeverity.CRITICAL,
                details={
                    'component': 'LM Studio Performance Monitor',
                    'alert_id': alert_id,
                    'metric_type': metric_type.value,
                    'description': description,
                    'current_value': current_value,
                    'threshold_value': threshold_value,
                    'recommended_action': recommended_action
                }
            )

    def _cleanup_old_metrics(self):
        """Clean up old metrics to prevent database bloat"""
        try:
            cleanup_date = (datetime.now() - timedelta(days=7)).isoformat()

            with sqlite3.connect(self.db_path) as conn:
                # Keep only last 7 days of detailed metrics
                conn.execute("""
                    DELETE FROM performance_metrics
                    WHERE timestamp < ? AND metric_type IN ('response_time', 'token_usage')
                """, (cleanup_date,))

                # Keep connection health logs for 30 days
                health_cleanup_date = (datetime.now() - timedelta(days=30)).isoformat()
                conn.execute("""
                    DELETE FROM connection_health_log
                    WHERE timestamp < ?
                """, (health_cleanup_date,))

                # Keep resolved alerts for 30 days
                conn.execute("""
                    DELETE FROM performance_alerts
                    WHERE resolved_at IS NOT NULL AND resolved_at < ?
                """, (health_cleanup_date,))

        except Exception as e:
            print(f"Error cleaning up old metrics: {e}")

    def add_alert_callback(self, callback: Callable[[PerformanceAlert], None]):
        """Add callback function for performance alerts"""
        self.alert_callbacks.append(callback)

    def get_current_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics for dashboard"""
        return {
            'connection_health': asdict(self.connection_health),
            'statistics': self.stats.copy(),
            'current_metrics': {
                'average_response_time_ms': statistics.mean(self.response_times) if self.response_times else 0,
                'recent_error_rate': (sum(list(self.error_counts)[-10:]) / min(10, len(self.error_counts))) * 100 if self.error_counts else 0,
                'tokens_per_minute': sum(list(self.token_usage)[-10:]) * 6 if self.token_usage else 0,  # Approximate
                'active_alerts': len(self.active_alerts),
                'queue_depth': self.request_queue.qsize()
            },
            'active_alerts': [asdict(alert) for alert in self.active_alerts.values()],
            'uptime_percentage': self.connection_health.uptime_percentage
        }

    async def get_historical_metrics(self,
                                   metric_type: PerformanceMetricType,
                                   hours: int = 24) -> List[Dict[str, Any]]:
        """Get historical metrics for analysis"""
        start_time = (datetime.now() - timedelta(hours=hours)).isoformat()

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT metric_id, value, timestamp, context
                FROM performance_metrics
                WHERE metric_type = ? AND timestamp >= ?
                ORDER BY timestamp DESC
            """, (metric_type.value, start_time))

            return [
                {
                    'metric_id': row[0],
                    'value': row[1],
                    'timestamp': row[2],
                    'context': json.loads(row[3]) if row[3] else {}
                }
                for row in cursor.fetchall()
            ]

    async def generate_performance_report(self, hours: int = 24) -> Dict[str, Any]:
        """Generate comprehensive performance report"""
        start_time = (datetime.now() - timedelta(hours=hours)).isoformat()

        with sqlite3.connect(self.db_path) as conn:
            # Response time statistics
            cursor = conn.execute("""
                SELECT AVG(value), MIN(value), MAX(value), COUNT(*)
                FROM performance_metrics
                WHERE metric_type = 'response_time' AND timestamp >= ?
            """, (start_time,))

            response_stats = cursor.fetchone()

            # Error rate
            cursor = conn.execute("""
                SELECT COUNT(CASE WHEN metric_type = 'error_rate' THEN 1 END) as errors,
                       COUNT(*) as total
                FROM performance_metrics
                WHERE timestamp >= ?
            """, (start_time,))

            error_stats = cursor.fetchone()

            # Alert summary
            cursor = conn.execute("""
                SELECT severity, COUNT(*) as count
                FROM performance_alerts
                WHERE timestamp >= ?
                GROUP BY severity
            """, (start_time,))

            alert_stats = dict(cursor.fetchall())

        return {
            'report_period_hours': hours,
            'response_time_stats': {
                'average_ms': response_stats[0] or 0,
                'min_ms': response_stats[1] or 0,
                'max_ms': response_stats[2] or 0,
                'total_requests': response_stats[3] or 0
            },
            'error_stats': {
                'error_count': error_stats[0] or 0,
                'total_requests': error_stats[1] or 0,
                'error_rate_percent': ((error_stats[0] or 0) / max(error_stats[1] or 1, 1)) * 100
            },
            'alert_summary': alert_stats,
            'connection_health': asdict(self.connection_health),
            'uptime_percentage': self.connection_health.uptime_percentage,
            'generated_at': datetime.now().isoformat()
        }


class PerformanceDashboard:
    """
    Real-time performance monitoring dashboard
    """

    def __init__(self, monitor: LMStudioPerformanceMonitor):
        self.monitor = monitor
        self.dashboard_data = {}

    async def get_dashboard_data(self) -> Dict[str, Any]:
        """Get real-time dashboard data"""
        current_metrics = self.monitor.get_current_metrics()

        # Add trend analysis
        response_times = list(self.monitor.response_times)
        if len(response_times) >= 10:
            recent_avg = statistics.mean(response_times[-10:])
            older_avg = statistics.mean(response_times[-20:-10]) if len(response_times) >= 20 else recent_avg
            response_trend = "improving" if recent_avg < older_avg else "degrading" if recent_avg > older_avg else "stable"
        else:
            response_trend = "insufficient_data"

        dashboard_data = {
            **current_metrics,
            'trends': {
                'response_time': response_trend,
                'error_rate': self._calculate_error_trend(),
                'connection_stability': self._calculate_connection_trend()
            },
            'health_score': self._calculate_health_score(),
            'recommendations': self._generate_recommendations()
        }

        self.dashboard_data = dashboard_data
        return dashboard_data

    def _calculate_error_trend(self) -> str:
        """Calculate error rate trend"""
        error_counts = list(self.monitor.error_counts)
        if len(error_counts) >= 10:
            recent_errors = sum(error_counts[-5:])
            older_errors = sum(error_counts[-10:-5])
            if recent_errors < older_errors:
                return "improving"
            elif recent_errors > older_errors:
                return "degrading"
            else:
                return "stable"
        return "insufficient_data"

    def _calculate_connection_trend(self) -> str:
        """Calculate connection stability trend"""
        if self.monitor.connection_health.consecutive_failures == 0:
            return "stable"
        elif self.monitor.connection_health.consecutive_failures <= 2:
            return "minor_issues"
        else:
            return "unstable"

    def _calculate_health_score(self) -> float:
        """Calculate overall health score (0-100)"""
        score = 100.0

        # Response time impact
        if self.monitor.response_times:
            avg_response = statistics.mean(self.monitor.response_times)
            if avg_response > 5000:  # > 5 seconds
                score -= 30
            elif avg_response > 2000:  # > 2 seconds
                score -= 15

        # Error rate impact
        if self.monitor.error_counts:
            recent_errors = sum(list(self.monitor.error_counts)[-10:])
            error_rate = (recent_errors / min(10, len(self.monitor.error_counts))) * 100
            score -= error_rate * 2  # 2 points per percent error rate

        # Connection health impact
        if self.monitor.connection_health.status != ConnectionStatus.HEALTHY:
            score -= 25

        # Active alerts impact
        critical_alerts = sum(1 for alert in self.monitor.active_alerts.values()
                            if alert.severity >= AlertSeverity.CRITICAL)
        score -= critical_alerts * 15

        # Uptime impact
        uptime = self.monitor.connection_health.uptime_percentage
        if uptime < 90:
            score -= (90 - uptime) * 2

        return max(0.0, min(100.0, score))

    def _generate_recommendations(self) -> List[str]:
        """Generate performance recommendations"""
        recommendations = []

        # Response time recommendations
        if self.monitor.response_times:
            avg_response = statistics.mean(self.monitor.response_times)
            if avg_response > 3000:
                recommendations.append("Consider optimizing LM Studio model or increasing hardware resources")

        # Error rate recommendations
        if self.monitor.error_counts:
            recent_errors = sum(list(self.monitor.error_counts)[-10:])
            if recent_errors > 2:
                recommendations.append("Investigate connection stability and LM Studio logs")

        # Connection health recommendations
        if self.monitor.connection_health.status != ConnectionStatus.HEALTHY:
            recommendations.append("Check LM Studio service status and network connectivity")

        # Resource recommendations
        health_score = self._calculate_health_score()
        if health_score < 70:
            recommendations.append("Consider scaling infrastructure or reducing request load")

        if not recommendations:
            recommendations.append("System performance is optimal")

        return recommendations


# Integration helper function
async def create_integrated_performance_monitor(
    lm_studio_url: str = "http://localhost:1234",
    security_logger: Optional[EnhancedSecurityLogging] = None
) -> Tuple[LMStudioPerformanceMonitor, PerformanceDashboard]:
    """
    Create integrated performance monitoring system

    Returns:
        Tuple of (monitor, dashboard) for easy setup
    """
    monitor = LMStudioPerformanceMonitor(
        lm_studio_url=lm_studio_url,
        security_logger=security_logger
    )

    dashboard = PerformanceDashboard(monitor)

    # Start monitoring
    await monitor.start_monitoring()

    return monitor, dashboard


if __name__ == "__main__":
    # Example usage
    async def main():
        # Create performance monitor
        monitor, dashboard = await create_integrated_performance_monitor()

        # Example LLM request tracking
        request_data = {
            'prompt_tokens': 150,
            'max_tokens': 500
        }

        response_data = {
            'completion_tokens': 300,
            'total_tokens': 450
        }

        # Track successful request
        metrics = await monitor.track_llm_request(request_data, response_data)
        print(f"Request metrics: {metrics}")

        # Get dashboard data
        dashboard_data = await dashboard.get_dashboard_data()
        print(f"Dashboard health score: {dashboard_data['health_score']}")

        # Generate performance report
        report = await monitor.generate_performance_report(hours=1)
        print(f"Performance report: {report}")

        # Stop monitoring
        monitor.stop_monitoring()

    asyncio.run(main())