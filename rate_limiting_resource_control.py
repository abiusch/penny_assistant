#!/usr/bin/env python3
"""
Rate Limiting & Resource Control System for Penny AI Assistant
Phase B1: Operational Security (Days 1-3)

This system provides comprehensive rate limiting and resource monitoring:
- Operation frequency limits to prevent spam/loops
- Resource usage monitoring (CPU, memory, disk, network)
- Automatic throttling for operations approaching resource limits
- Runaway process detection and termination
- Adaptive rate limiting based on system performance
- Resource quota management with daily/hourly limits
"""

import asyncio
import json
import sqlite3
import time
import psutil
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Callable
from enum import Enum, IntEnum
from dataclasses import dataclass, asdict, field
from pathlib import Path
import logging
from collections import deque, defaultdict
import weakref

# Import existing security components
try:
    from command_whitelist_system import CommandWhitelistSystem, OperationType, PermissionLevel, SecurityRisk
    from enhanced_security_logging import EnhancedSecurityLogging, SecurityEventType, SecuritySeverity
    from lm_studio_performance_monitor import LMStudioPerformanceMonitor
except ImportError as e:
    print(f"Warning: Could not import security components: {e}")


class RateLimitType(Enum):
    """Types of rate limiting"""
    OPERATIONS_PER_MINUTE = "operations_per_minute"
    OPERATIONS_PER_HOUR = "operations_per_hour"
    OPERATIONS_PER_DAY = "operations_per_day"
    RESOURCE_BASED = "resource_based"
    ADAPTIVE = "adaptive"
    BURST_CONTROL = "burst_control"


class ResourceType(Enum):
    """System resources to monitor"""
    CPU = "cpu"
    MEMORY = "memory"
    DISK_IO = "disk_io"
    NETWORK_IO = "network_io"
    PROCESS_COUNT = "process_count"
    FILE_HANDLES = "file_handles"


class ThrottleAction(Enum):
    """Actions to take when throttling"""
    DELAY = "delay"
    QUEUE = "queue"
    REJECT = "reject"
    SCALE_DOWN = "scale_down"
    EMERGENCY_STOP = "emergency_stop"


class QuotaPeriod(Enum):
    """Quota time periods"""
    MINUTE = "minute"
    HOUR = "hour"
    DAY = "day"
    WEEK = "week"
    MONTH = "month"


@dataclass
class RateLimit:
    """Rate limit configuration"""
    limit_type: RateLimitType
    operation_type: OperationType
    max_operations: int
    time_window_seconds: int
    burst_allowance: int = 0
    adaptive_scaling: bool = False
    priority_bypass: bool = False


@dataclass
class ResourceQuota:
    """Resource usage quota"""
    resource_type: ResourceType
    max_usage_percent: float
    period: QuotaPeriod
    quota_limit: int
    warning_threshold: float = 0.8
    critical_threshold: float = 0.9


@dataclass
class OperationAttempt:
    """Record of operation attempt"""
    operation_type: OperationType
    operation_name: str
    timestamp: datetime
    user_id: str
    allowed: bool
    throttle_reason: Optional[str] = None
    resource_usage: Dict[str, float] = field(default_factory=dict)
    processing_time_ms: float = 0.0


@dataclass
class ResourceUsage:
    """Current system resource usage"""
    cpu_percent: float
    memory_percent: float
    disk_io_mbps: float
    network_io_mbps: float
    process_count: int
    file_handles: int
    timestamp: datetime


@dataclass
class ThrottleState:
    """Current throttling state"""
    active: bool
    throttle_action: ThrottleAction
    delay_seconds: float
    reason: str
    started_at: datetime
    operations_queued: int = 0
    operations_rejected: int = 0


class RateLimitingResourceControl:
    """
    Comprehensive rate limiting and resource control system

    Prevents operation spam/loops, monitors system resources,
    and implements intelligent throttling and quota management.
    """

    def __init__(self,
                 db_path: str = "rate_limiting.db",
                 whitelist_system: Optional[CommandWhitelistSystem] = None,
                 security_logger: Optional[EnhancedSecurityLogging] = None,
                 performance_monitor: Optional[LMStudioPerformanceMonitor] = None):

        self.db_path = db_path
        self.whitelist_system = whitelist_system
        self.security_logger = security_logger
        self.performance_monitor = performance_monitor

        # Rate limiting configuration
        self.rate_limits: Dict[str, RateLimit] = {}
        self.resource_quotas: Dict[str, ResourceQuota] = {}

        # Operation tracking
        self.operation_history = deque(maxlen=10000)  # Last 10k operations
        self.operation_counts: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))

        # Resource monitoring
        self.resource_history = deque(maxlen=1000)  # Last 1000 resource samples
        self.current_resource_usage: Optional[ResourceUsage] = None

        # Throttling state
        self.throttle_state = ThrottleState(
            active=False,
            throttle_action=ThrottleAction.DELAY,
            delay_seconds=0.0,
            reason="",
            started_at=datetime.now()
        )

        # Background monitoring
        self.monitoring_active = False
        self.monitor_thread: Optional[threading.Thread] = None
        self.resource_update_interval = 5  # seconds

        # Callbacks
        self.throttle_callbacks: List[Callable] = []
        self.quota_exceeded_callbacks: List[Callable] = []

        # Performance statistics
        self.stats = {
            'total_operations': 0,
            'throttled_operations': 0,
            'rejected_operations': 0,
            'queued_operations': 0,
            'quota_violations': 0,
            'resource_alerts': 0
        }

        self._init_database()
        self._load_default_configurations()

    def _init_database(self):
        """Initialize rate limiting database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS rate_limits (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    limit_type TEXT NOT NULL,
                    operation_type TEXT NOT NULL,
                    max_operations INTEGER NOT NULL,
                    time_window_seconds INTEGER NOT NULL,
                    burst_allowance INTEGER DEFAULT 0,
                    adaptive_scaling INTEGER DEFAULT 0,
                    priority_bypass INTEGER DEFAULT 0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS resource_quotas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    resource_type TEXT NOT NULL,
                    max_usage_percent REAL NOT NULL,
                    period TEXT NOT NULL,
                    quota_limit INTEGER NOT NULL,
                    warning_threshold REAL DEFAULT 0.8,
                    critical_threshold REAL DEFAULT 0.9,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS operation_attempts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    operation_type TEXT NOT NULL,
                    operation_name TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    allowed INTEGER NOT NULL,
                    throttle_reason TEXT,
                    resource_usage TEXT,
                    processing_time_ms REAL DEFAULT 0.0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS resource_usage_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cpu_percent REAL NOT NULL,
                    memory_percent REAL NOT NULL,
                    disk_io_mbps REAL NOT NULL,
                    network_io_mbps REAL NOT NULL,
                    process_count INTEGER NOT NULL,
                    file_handles INTEGER NOT NULL,
                    timestamp TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS throttle_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    throttle_action TEXT NOT NULL,
                    delay_seconds REAL NOT NULL,
                    reason TEXT NOT NULL,
                    operations_affected INTEGER DEFAULT 0,
                    started_at TEXT NOT NULL,
                    ended_at TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                );

                CREATE INDEX IF NOT EXISTS idx_operation_attempts_time ON operation_attempts(timestamp);
                CREATE INDEX IF NOT EXISTS idx_resource_usage_time ON resource_usage_log(timestamp);
                CREATE INDEX IF NOT EXISTS idx_throttle_events_time ON throttle_events(started_at);
            """)

    def _load_default_configurations(self):
        """Load default rate limits and resource quotas"""
        # Default rate limits for different operation types
        default_rate_limits = [
            RateLimit(
                limit_type=RateLimitType.OPERATIONS_PER_MINUTE,
                operation_type=OperationType.READ_ONLY,
                max_operations=60,  # 60 reads per minute
                time_window_seconds=60,
                burst_allowance=10,
                adaptive_scaling=True
            ),
            RateLimit(
                limit_type=RateLimitType.OPERATIONS_PER_MINUTE,
                operation_type=OperationType.FILE_SYSTEM,
                max_operations=20,  # 20 file ops per minute
                time_window_seconds=60,
                burst_allowance=5,
                adaptive_scaling=True
            ),
            RateLimit(
                limit_type=RateLimitType.OPERATIONS_PER_MINUTE,
                operation_type=OperationType.COMMUNICATION,
                max_operations=30,  # 30 network requests per minute
                time_window_seconds=60,
                burst_allowance=5,
                adaptive_scaling=False
            ),
            RateLimit(
                limit_type=RateLimitType.OPERATIONS_PER_HOUR,
                operation_type=OperationType.SYSTEM_INFO,
                max_operations=200,  # 200 system checks per hour
                time_window_seconds=3600,
                burst_allowance=20
            ),
            RateLimit(
                limit_type=RateLimitType.OPERATIONS_PER_DAY,
                operation_type=OperationType.RESTRICTED,
                max_operations=10,  # Only 10 restricted ops per day
                time_window_seconds=86400,
                burst_allowance=0,
                priority_bypass=True
            )
        ]

        # Default resource quotas
        default_resource_quotas = [
            ResourceQuota(
                resource_type=ResourceType.CPU,
                max_usage_percent=80.0,  # 80% CPU limit
                period=QuotaPeriod.MINUTE,
                quota_limit=60,  # 60 seconds of high CPU per minute
                warning_threshold=0.7,
                critical_threshold=0.9
            ),
            ResourceQuota(
                resource_type=ResourceType.MEMORY,
                max_usage_percent=85.0,  # 85% memory limit
                period=QuotaPeriod.HOUR,
                quota_limit=3600,  # 1 hour of high memory per hour
                warning_threshold=0.75,
                critical_threshold=0.9
            ),
            ResourceQuota(
                resource_type=ResourceType.DISK_IO,
                max_usage_percent=90.0,  # 90% disk I/O limit
                period=QuotaPeriod.MINUTE,
                quota_limit=60,
                warning_threshold=0.8,
                critical_threshold=0.95
            ),
            ResourceQuota(
                resource_type=ResourceType.PROCESS_COUNT,
                max_usage_percent=100.0,  # 100 processes max
                period=QuotaPeriod.HOUR,
                quota_limit=1000,
                warning_threshold=0.8,
                critical_threshold=0.9
            )
        ]

        # Store configurations
        for rate_limit in default_rate_limits:
            self.rate_limits[f"{rate_limit.operation_type.value}_{rate_limit.limit_type.value}"] = rate_limit

        for quota in default_resource_quotas:
            self.resource_quotas[f"{quota.resource_type.value}_{quota.period.value}"] = quota

        # Save to database
        self._save_configurations()

    def _save_configurations(self):
        """Save rate limits and quotas to database"""
        with sqlite3.connect(self.db_path) as conn:
            # Clear existing configurations
            conn.execute("DELETE FROM rate_limits")
            conn.execute("DELETE FROM resource_quotas")

            # Save rate limits
            for rate_limit in self.rate_limits.values():
                conn.execute("""
                    INSERT INTO rate_limits
                    (limit_type, operation_type, max_operations, time_window_seconds,
                     burst_allowance, adaptive_scaling, priority_bypass)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    rate_limit.limit_type.value,
                    rate_limit.operation_type.value,
                    rate_limit.max_operations,
                    rate_limit.time_window_seconds,
                    rate_limit.burst_allowance,
                    rate_limit.adaptive_scaling,
                    rate_limit.priority_bypass
                ))

            # Save resource quotas
            for quota in self.resource_quotas.values():
                conn.execute("""
                    INSERT INTO resource_quotas
                    (resource_type, max_usage_percent, period, quota_limit,
                     warning_threshold, critical_threshold)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    quota.resource_type.value,
                    quota.max_usage_percent,
                    quota.period.value,
                    quota.quota_limit,
                    quota.warning_threshold,
                    quota.critical_threshold
                ))

    async def start_monitoring(self):
        """Start background resource monitoring"""
        if self.monitoring_active:
            return

        self.monitoring_active = True
        self.monitor_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitor_thread.start()

        if self.security_logger:
            await self.security_logger.log_security_event(
                event_type=SecurityEventType.SYSTEM_STARTUP,
                severity=SecuritySeverity.INFO,
                details={
                    'component': 'Rate Limiting Resource Control',
                    'action': 'monitoring_started',
                    'rate_limits_configured': len(self.rate_limits),
                    'resource_quotas_configured': len(self.resource_quotas)
                }
            )

    def stop_monitoring(self):
        """Stop background resource monitoring"""
        self.monitoring_active = False
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=5)

    def _monitoring_loop(self):
        """Background monitoring loop"""
        while self.monitoring_active:
            try:
                # Update resource usage
                self._update_resource_usage()

                # Check for throttling conditions
                self._check_throttling_conditions()

                # Check quota violations
                self._check_quota_violations()

                # Cleanup old data
                self._cleanup_old_data()

                time.sleep(self.resource_update_interval)

            except Exception as e:
                logging.error(f"Error in rate limiting monitoring loop: {e}")

    def _update_resource_usage(self):
        """Update current system resource usage"""
        try:
            # Get CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)

            # Get memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent

            # Get disk I/O (simplified)
            disk_io = psutil.disk_io_counters()
            disk_io_mbps = 0.0  # Would need historical data for rate calculation

            # Get network I/O (simplified)
            network_io = psutil.net_io_counters()
            network_io_mbps = 0.0  # Would need historical data for rate calculation

            # Get process count
            process_count = len(psutil.pids())

            # Get file handles (approximate)
            file_handles = 0
            try:
                for proc in psutil.process_iter(['num_fds']):
                    try:
                        file_handles += proc.info['num_fds'] or 0
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue
            except Exception:
                file_handles = 0

            # Create resource usage record
            resource_usage = ResourceUsage(
                cpu_percent=cpu_percent,
                memory_percent=memory_percent,
                disk_io_mbps=disk_io_mbps,
                network_io_mbps=network_io_mbps,
                process_count=process_count,
                file_handles=file_handles,
                timestamp=datetime.now()
            )

            self.current_resource_usage = resource_usage
            self.resource_history.append(resource_usage)

            # Log to database
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO resource_usage_log
                    (cpu_percent, memory_percent, disk_io_mbps, network_io_mbps,
                     process_count, file_handles, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    cpu_percent, memory_percent, disk_io_mbps, network_io_mbps,
                    process_count, file_handles, resource_usage.timestamp.isoformat()
                ))

        except Exception as e:
            logging.error(f"Error updating resource usage: {e}")

    def _check_throttling_conditions(self):
        """Check if throttling should be activated"""
        if not self.current_resource_usage:
            return

        should_throttle = False
        throttle_reason = ""
        throttle_action = ThrottleAction.DELAY
        delay_seconds = 1.0

        # Check CPU usage
        if self.current_resource_usage.cpu_percent > 90:
            should_throttle = True
            throttle_reason = f"High CPU usage ({self.current_resource_usage.cpu_percent:.1f}%)"
            throttle_action = ThrottleAction.DELAY
            delay_seconds = 2.0

        # Check memory usage
        elif self.current_resource_usage.memory_percent > 95:
            should_throttle = True
            throttle_reason = f"High memory usage ({self.current_resource_usage.memory_percent:.1f}%)"
            throttle_action = ThrottleAction.QUEUE
            delay_seconds = 1.0

        # Check process count
        elif self.current_resource_usage.process_count > 200:
            should_throttle = True
            throttle_reason = f"High process count ({self.current_resource_usage.process_count})"
            throttle_action = ThrottleAction.SCALE_DOWN

        # Update throttling state
        if should_throttle and not self.throttle_state.active:
            self._activate_throttling(throttle_action, delay_seconds, throttle_reason)
        elif not should_throttle and self.throttle_state.active:
            self._deactivate_throttling()

    def _activate_throttling(self, action: ThrottleAction, delay: float, reason: str):
        """Activate throttling"""
        self.throttle_state = ThrottleState(
            active=True,
            throttle_action=action,
            delay_seconds=delay,
            reason=reason,
            started_at=datetime.now()
        )

        # Log throttle activation
        asyncio.run(self._log_throttle_event("activated"))

        # Notify callbacks
        for callback in self.throttle_callbacks:
            try:
                callback(self.throttle_state)
            except Exception as e:
                logging.error(f"Error in throttle callback: {e}")

    def _deactivate_throttling(self):
        """Deactivate throttling"""
        # Log throttle deactivation
        asyncio.run(self._log_throttle_event("deactivated"))

        self.throttle_state.active = False

    async def _log_throttle_event(self, event_type: str):
        """Log throttling events"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO throttle_events
                (throttle_action, delay_seconds, reason, started_at, ended_at)
                VALUES (?, ?, ?, ?, ?)
            """, (
                self.throttle_state.throttle_action.value,
                self.throttle_state.delay_seconds,
                self.throttle_state.reason,
                self.throttle_state.started_at.isoformat(),
                datetime.now().isoformat() if event_type == "deactivated" else None
            ))

        if self.security_logger:
            await self.security_logger.log_security_event(
                event_type=SecurityEventType.SYSTEM_UPDATE,
                severity=SecuritySeverity.WARNING if event_type == "activated" else SecuritySeverity.INFO,
                details={
                    'component': 'Rate Limiting Resource Control',
                    'action': f'throttling_{event_type}',
                    'throttle_action': self.throttle_state.throttle_action.value,
                    'reason': self.throttle_state.reason,
                    'delay_seconds': self.throttle_state.delay_seconds
                }
            )

    def _check_quota_violations(self):
        """Check for resource quota violations"""
        if not self.current_resource_usage:
            return

        for quota_key, quota in self.resource_quotas.items():
            current_usage = self._get_current_quota_usage(quota)
            quota_percentage = current_usage / quota.quota_limit

            if quota_percentage > quota.critical_threshold:
                asyncio.run(self._handle_quota_violation(quota, current_usage, "critical"))
            elif quota_percentage > quota.warning_threshold:
                asyncio.run(self._handle_quota_violation(quota, current_usage, "warning"))

    def _get_current_quota_usage(self, quota: ResourceQuota) -> float:
        """Get current usage for a specific quota"""
        if not self.current_resource_usage:
            return 0.0

        if quota.resource_type == ResourceType.CPU:
            return self.current_resource_usage.cpu_percent
        elif quota.resource_type == ResourceType.MEMORY:
            return self.current_resource_usage.memory_percent
        elif quota.resource_type == ResourceType.PROCESS_COUNT:
            return self.current_resource_usage.process_count
        elif quota.resource_type == ResourceType.DISK_IO:
            return self.current_resource_usage.disk_io_mbps
        elif quota.resource_type == ResourceType.NETWORK_IO:
            return self.current_resource_usage.network_io_mbps
        elif quota.resource_type == ResourceType.FILE_HANDLES:
            return self.current_resource_usage.file_handles

        return 0.0

    async def _handle_quota_violation(self, quota: ResourceQuota, current_usage: float, severity: str):
        """Handle quota violations"""
        self.stats['quota_violations'] += 1

        if self.security_logger:
            await self.security_logger.log_security_event(
                event_type=SecurityEventType.SECURITY_VIOLATION,
                severity=SecuritySeverity.CRITICAL if severity == "critical" else SecuritySeverity.WARNING,
                details={
                    'component': 'Rate Limiting Resource Control',
                    'violation_type': f'quota_{severity}',
                    'resource_type': quota.resource_type.value,
                    'current_usage': current_usage,
                    'quota_limit': quota.quota_limit,
                    'usage_percentage': (current_usage / quota.quota_limit) * 100
                }
            )

        # Notify callbacks
        for callback in self.quota_exceeded_callbacks:
            try:
                callback(quota, current_usage, severity)
            except Exception as e:
                logging.error(f"Error in quota callback: {e}")

    async def check_operation_allowed(self,
                                    operation_type: OperationType,
                                    operation_name: str,
                                    user_id: str = "default") -> Tuple[bool, str, float]:
        """
        Check if an operation is allowed under current rate limits and resource constraints

        Returns:
            Tuple of (allowed, reason, delay_seconds)
        """
        start_time = time.time()

        try:
            # Check if throttling is active
            if self.throttle_state.active:
                if self.throttle_state.throttle_action == ThrottleAction.REJECT:
                    await self._log_operation_attempt(
                        operation_type, operation_name, user_id, False,
                        f"Throttled: {self.throttle_state.reason}", start_time
                    )
                    return False, f"Operation rejected due to throttling: {self.throttle_state.reason}", 0.0

                elif self.throttle_state.throttle_action == ThrottleAction.DELAY:
                    await self._log_operation_attempt(
                        operation_type, operation_name, user_id, True,
                        f"Delayed: {self.throttle_state.reason}", start_time
                    )
                    return True, f"Operation delayed due to throttling: {self.throttle_state.reason}", self.throttle_state.delay_seconds

            # Check rate limits
            rate_limit_result = self._check_rate_limits(operation_type, user_id)
            if not rate_limit_result[0]:
                await self._log_operation_attempt(
                    operation_type, operation_name, user_id, False,
                    rate_limit_result[1], start_time
                )
                return rate_limit_result

            # Check resource availability
            resource_check_result = self._check_resource_availability(operation_type)
            if not resource_check_result[0]:
                await self._log_operation_attempt(
                    operation_type, operation_name, user_id, False,
                    resource_check_result[1], start_time
                )
                return resource_check_result

            # Operation allowed
            await self._log_operation_attempt(
                operation_type, operation_name, user_id, True,
                "Allowed", start_time
            )

            # Track operation for rate limiting
            self._record_operation(operation_type, user_id)

            return True, "Operation allowed", 0.0

        except Exception as e:
            await self._log_operation_attempt(
                operation_type, operation_name, user_id, False,
                f"Error during rate limit check: {str(e)}", start_time
            )
            return False, f"Rate limit check failed: {str(e)}", 0.0

    def _check_rate_limits(self, operation_type: OperationType, user_id: str) -> Tuple[bool, str, float]:
        """Check operation against configured rate limits"""
        # Find applicable rate limits
        applicable_limits = [
            limit for key, limit in self.rate_limits.items()
            if limit.operation_type == operation_type
        ]

        for rate_limit in applicable_limits:
            # Count recent operations
            cutoff_time = datetime.now() - timedelta(seconds=rate_limit.time_window_seconds)

            user_operations = self.operation_counts.get(f"{user_id}:{operation_type.value}", deque())
            recent_operations = [
                op_time for op_time in user_operations
                if op_time > cutoff_time
            ]

            # Check if limit exceeded
            if len(recent_operations) >= rate_limit.max_operations:
                # Check burst allowance
                if rate_limit.burst_allowance > 0:
                    burst_cutoff = datetime.now() - timedelta(seconds=10)  # 10-second burst window
                    burst_operations = [
                        op_time for op_time in user_operations
                        if op_time > burst_cutoff
                    ]

                    if len(burst_operations) < rate_limit.burst_allowance:
                        return True, "Allowed via burst allowance", 0.0

                # Calculate delay until next operation allowed
                oldest_operation = min(recent_operations)
                delay_until = oldest_operation + timedelta(seconds=rate_limit.time_window_seconds)
                delay_seconds = (delay_until - datetime.now()).total_seconds()

                return False, f"Rate limit exceeded for {operation_type.value} ({len(recent_operations)}/{rate_limit.max_operations} in {rate_limit.time_window_seconds}s)", max(0, delay_seconds)

        return True, "Rate limit check passed", 0.0

    def _check_resource_availability(self, operation_type: OperationType) -> Tuple[bool, str, float]:
        """Check if sufficient resources are available for operation"""
        if not self.current_resource_usage:
            return True, "Resource check skipped (no data)", 0.0

        # Define resource requirements for different operation types
        resource_requirements = {
            OperationType.COMPUTATION: {'cpu': 70, 'memory': 80},
            OperationType.FILE_SYSTEM: {'disk_io': 80, 'file_handles': 90},
            OperationType.COMMUNICATION: {'network_io': 80, 'memory': 70},
            OperationType.SYSTEM_INFO: {'cpu': 50},
            OperationType.READ_ONLY: {'memory': 60},
        }

        requirements = resource_requirements.get(operation_type, {})

        for resource, threshold in requirements.items():
            if resource == 'cpu' and self.current_resource_usage.cpu_percent > threshold:
                return False, f"Insufficient CPU (current: {self.current_resource_usage.cpu_percent:.1f}%, required: <{threshold}%)", 2.0
            elif resource == 'memory' and self.current_resource_usage.memory_percent > threshold:
                return False, f"Insufficient memory (current: {self.current_resource_usage.memory_percent:.1f}%, required: <{threshold}%)", 1.0
            elif resource == 'file_handles' and self.current_resource_usage.file_handles > threshold:
                return False, f"Too many file handles (current: {self.current_resource_usage.file_handles}, threshold: {threshold})", 0.5

        return True, "Resource availability check passed", 0.0

    def _record_operation(self, operation_type: OperationType, user_id: str):
        """Record an operation for rate limiting tracking"""
        operation_key = f"{user_id}:{operation_type.value}"
        self.operation_counts[operation_key].append(datetime.now())
        self.stats['total_operations'] += 1

    async def _log_operation_attempt(self,
                                   operation_type: OperationType,
                                   operation_name: str,
                                   user_id: str,
                                   allowed: bool,
                                   reason: str,
                                   start_time: float):
        """Log operation attempt to database"""
        processing_time = (time.time() - start_time) * 1000  # Convert to milliseconds

        # Create operation attempt record
        attempt = OperationAttempt(
            operation_type=operation_type,
            operation_name=operation_name,
            timestamp=datetime.now(),
            user_id=user_id,
            allowed=allowed,
            throttle_reason=reason if not allowed else None,
            resource_usage=asdict(self.current_resource_usage) if self.current_resource_usage else {},
            processing_time_ms=processing_time
        )

        self.operation_history.append(attempt)

        # Log to database
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO operation_attempts
                (operation_type, operation_name, timestamp, user_id, allowed,
                 throttle_reason, resource_usage, processing_time_ms)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                operation_type.value,
                operation_name,
                attempt.timestamp.isoformat(),
                user_id,
                allowed,
                attempt.throttle_reason,
                json.dumps(attempt.resource_usage),
                processing_time
            ))

        # Update statistics
        if not allowed:
            self.stats['throttled_operations'] += 1

    def _cleanup_old_data(self):
        """Clean up old data to prevent database bloat"""
        try:
            cleanup_date = (datetime.now() - timedelta(days=7)).isoformat()

            with sqlite3.connect(self.db_path) as conn:
                # Keep only last 7 days of operation attempts
                conn.execute("""
                    DELETE FROM operation_attempts
                    WHERE timestamp < ?
                """, (cleanup_date,))

                # Keep only last 7 days of resource usage
                conn.execute("""
                    DELETE FROM resource_usage_log
                    WHERE timestamp < ?
                """, (cleanup_date,))

                # Keep throttle events for 30 days
                throttle_cleanup_date = (datetime.now() - timedelta(days=30)).isoformat()
                conn.execute("""
                    DELETE FROM throttle_events
                    WHERE started_at < ?
                """, (throttle_cleanup_date,))

        except Exception as e:
            logging.error(f"Error cleaning up old data: {e}")

    def add_throttle_callback(self, callback: Callable[[ThrottleState], None]):
        """Add callback for throttling events"""
        self.throttle_callbacks.append(callback)

    def add_quota_callback(self, callback: Callable[[ResourceQuota, float, str], None]):
        """Add callback for quota violations"""
        self.quota_exceeded_callbacks.append(callback)

    def get_current_stats(self) -> Dict[str, Any]:
        """Get current rate limiting and resource statistics"""
        return {
            'statistics': self.stats.copy(),
            'throttle_state': asdict(self.throttle_state),
            'current_resource_usage': asdict(self.current_resource_usage) if self.current_resource_usage else {},
            'active_rate_limits': len(self.rate_limits),
            'active_quotas': len(self.resource_quotas),
            'recent_operations': len(self.operation_history),
            'monitoring_active': self.monitoring_active
        }

    async def get_operation_history(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get operation history for analysis"""
        start_time = (datetime.now() - timedelta(hours=hours)).isoformat()

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT operation_type, operation_name, timestamp, user_id,
                       allowed, throttle_reason, processing_time_ms
                FROM operation_attempts
                WHERE timestamp >= ?
                ORDER BY timestamp DESC
            """, (start_time,))

            return [
                {
                    'operation_type': row[0],
                    'operation_name': row[1],
                    'timestamp': row[2],
                    'user_id': row[3],
                    'allowed': bool(row[4]),
                    'throttle_reason': row[5],
                    'processing_time_ms': row[6]
                }
                for row in cursor.fetchall()
            ]

    async def get_resource_history(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get resource usage history"""
        start_time = (datetime.now() - timedelta(hours=hours)).isoformat()

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT cpu_percent, memory_percent, disk_io_mbps, network_io_mbps,
                       process_count, file_handles, timestamp
                FROM resource_usage_log
                WHERE timestamp >= ?
                ORDER BY timestamp DESC
            """, (start_time,))

            return [
                {
                    'cpu_percent': row[0],
                    'memory_percent': row[1],
                    'disk_io_mbps': row[2],
                    'network_io_mbps': row[3],
                    'process_count': row[4],
                    'file_handles': row[5],
                    'timestamp': row[6]
                }
                for row in cursor.fetchall()
            ]

    def update_rate_limit(self, operation_type: OperationType, **kwargs):
        """Update rate limit configuration"""
        # Find and update existing rate limit
        for key, rate_limit in self.rate_limits.items():
            if rate_limit.operation_type == operation_type:
                for attr, value in kwargs.items():
                    if hasattr(rate_limit, attr):
                        setattr(rate_limit, attr, value)
                break

        # Save updated configuration
        self._save_configurations()

    def update_resource_quota(self, resource_type: ResourceType, **kwargs):
        """Update resource quota configuration"""
        # Find and update existing quota
        for key, quota in self.resource_quotas.items():
            if quota.resource_type == resource_type:
                for attr, value in kwargs.items():
                    if hasattr(quota, attr):
                        setattr(quota, attr, value)
                break

        # Save updated configuration
        self._save_configurations()


# Integration helper function
async def create_integrated_rate_limiting_system(
    whitelist_system: Optional[CommandWhitelistSystem] = None,
    security_logger: Optional[EnhancedSecurityLogging] = None,
    performance_monitor: Optional[LMStudioPerformanceMonitor] = None
) -> RateLimitingResourceControl:
    """
    Create integrated rate limiting and resource control system

    Returns configured and initialized system
    """
    rate_limiter = RateLimitingResourceControl(
        whitelist_system=whitelist_system,
        security_logger=security_logger,
        performance_monitor=performance_monitor
    )

    # Start monitoring
    await rate_limiter.start_monitoring()

    return rate_limiter


if __name__ == "__main__":
    # Example usage
    async def main():
        # Create rate limiting system
        rate_limiter = await create_integrated_rate_limiting_system()

        # Test operation checking
        result = await rate_limiter.check_operation_allowed(
            OperationType.FILE_SYSTEM,
            "read_file",
            "test_user"
        )
        print(f"Operation allowed: {result}")

        # Get current statistics
        stats = rate_limiter.get_current_stats()
        print(f"Current stats: {stats}")

        # Stop monitoring
        rate_limiter.stop_monitoring()

    asyncio.run(main())