#!/usr/bin/env python3
"""
Runaway Process Detection and Termination System
Phase B1: Operational Security - Task B1 (Part 4)

This system provides comprehensive runaway process detection:
- Process resource consumption monitoring
- Automatic detection of runaway processes
- Configurable termination policies
- Integration with security logging and rate limiting
- Process lifecycle tracking and analysis
"""

import asyncio
import psutil
import signal
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Set
from enum import Enum
from dataclasses import dataclass, field
import threading
import sqlite3
import json

# Import existing security components
try:
    from enhanced_security_logging import EnhancedSecurityLogging, SecurityEventType, SecuritySeverity
    from rate_limiting_resource_control import RateLimitingResourceControl
except ImportError as e:
    print(f"Warning: Could not import security components: {e}")


class ProcessState(Enum):
    """Process monitoring states"""
    NORMAL = "normal"
    SUSPICIOUS = "suspicious"
    RUNAWAY = "runaway"
    TERMINATED = "terminated"
    ZOMBIE = "zombie"


class TerminationMethod(Enum):
    """Process termination methods"""
    SIGTERM = "sigterm"    # Graceful termination
    SIGKILL = "sigkill"    # Force kill
    TIMEOUT = "timeout"    # Timeout-based termination
    RESOURCE = "resource"  # Resource-based termination


class DetectionTrigger(Enum):
    """What triggered runaway detection"""
    CPU_USAGE = "cpu_usage"
    MEMORY_USAGE = "memory_usage"
    EXECUTION_TIME = "execution_time"
    FILE_HANDLES = "file_handles"
    NETWORK_CONNECTIONS = "network_connections"
    CHILD_PROCESSES = "child_processes"
    DISK_IO = "disk_io"


@dataclass
class ProcessInfo:
    """Comprehensive process information"""
    pid: int
    name: str
    cmdline: List[str]
    cpu_percent: float
    memory_percent: float
    memory_rss: int  # Resident Set Size in bytes
    num_threads: int
    num_fds: int  # File descriptors
    create_time: datetime
    status: str
    ppid: int  # Parent process ID
    children_pids: List[int] = field(default_factory=list)


@dataclass
class ProcessAlert:
    """Process alert information"""
    pid: int
    process_name: str
    trigger: DetectionTrigger
    current_value: float
    threshold_value: float
    severity: str
    description: str
    timestamp: datetime
    recommended_action: str


@dataclass
class ProcessTermination:
    """Process termination record"""
    pid: int
    process_name: str
    termination_method: TerminationMethod
    termination_reason: str
    cpu_usage_at_termination: float
    memory_usage_at_termination: float
    execution_time_seconds: float
    timestamp: datetime
    success: bool
    error_message: Optional[str] = None


class RunawayProcessDetector:
    """
    Comprehensive runaway process detection and termination system

    Monitors system processes for excessive resource usage and automatically
    terminates runaway processes based on configurable policies.
    """

    def __init__(self,
                 db_path: str = "process_monitoring.db",
                 security_logger: Optional[EnhancedSecurityLogging] = None,
                 rate_limiter: Optional[RateLimitingResourceControl] = None):

        self.db_path = db_path
        self.security_logger = security_logger
        self.rate_limiter = rate_limiter

        # Detection thresholds
        self.cpu_threshold = 80.0  # CPU percentage
        self.memory_threshold = 80.0  # Memory percentage
        self.execution_time_threshold = 300  # 5 minutes
        self.file_handle_threshold = 500  # Number of file handles
        self.process_count_threshold = 50  # Number of child processes

        # Monitoring configuration
        self.monitoring_interval = 10  # seconds
        self.alert_cooldown = 60  # seconds between similar alerts
        self.termination_grace_period = 30  # seconds before force kill

        # Process tracking
        self.monitored_processes: Dict[int, ProcessInfo] = {}
        self.process_history: Dict[int, List[ProcessInfo]] = {}
        self.recent_alerts: Dict[int, datetime] = {}
        self.terminated_processes: List[ProcessTermination] = []

        # Monitoring state
        self.monitoring_active = False
        self.monitor_thread: Optional[threading.Thread] = None

        # Protected processes (never terminate)
        self.protected_processes = {
            'systemd', 'kernel', 'init', 'launchd', 'WindowServer',
            'loginwindow', 'Finder', 'Dock', 'SystemUIServer'
        }

        # Penny's own processes (special handling)
        self.penny_processes: Set[int] = set()

        self._init_database()

    def _init_database(self):
        """Initialize process monitoring database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS process_monitoring (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pid INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    cmdline TEXT,
                    cpu_percent REAL,
                    memory_percent REAL,
                    memory_rss INTEGER,
                    num_threads INTEGER,
                    num_fds INTEGER,
                    create_time TEXT,
                    status TEXT,
                    ppid INTEGER,
                    timestamp TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS process_alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pid INTEGER NOT NULL,
                    process_name TEXT NOT NULL,
                    trigger_type TEXT NOT NULL,
                    current_value REAL NOT NULL,
                    threshold_value REAL NOT NULL,
                    severity TEXT NOT NULL,
                    description TEXT NOT NULL,
                    recommended_action TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS process_terminations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pid INTEGER NOT NULL,
                    process_name TEXT NOT NULL,
                    termination_method TEXT NOT NULL,
                    termination_reason TEXT NOT NULL,
                    cpu_usage_at_termination REAL,
                    memory_usage_at_termination REAL,
                    execution_time_seconds REAL,
                    success INTEGER NOT NULL,
                    error_message TEXT,
                    timestamp TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                );

                CREATE INDEX IF NOT EXISTS idx_process_monitoring_pid_time ON process_monitoring(pid, timestamp);
                CREATE INDEX IF NOT EXISTS idx_process_alerts_time ON process_alerts(timestamp);
                CREATE INDEX IF NOT EXISTS idx_process_terminations_time ON process_terminations(timestamp);
            """)

    async def start_monitoring(self):
        """Start process monitoring"""
        if self.monitoring_active:
            return

        self.monitoring_active = True

        # Identify Penny's processes
        self._identify_penny_processes()

        # Start monitoring thread
        self.monitor_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitor_thread.start()

        if self.security_logger:
            await self.security_logger.log_security_event(
                event_type=SecurityEventType.SYSTEM_STARTUP,
                severity=SecuritySeverity.INFO,
                details={
                    'component': 'Runaway Process Detector',
                    'action': 'monitoring_started',
                    'cpu_threshold': self.cpu_threshold,
                    'memory_threshold': self.memory_threshold,
                    'execution_time_threshold': self.execution_time_threshold
                }
            )

    def stop_monitoring(self):
        """Stop process monitoring"""
        self.monitoring_active = False
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=5)

    def _identify_penny_processes(self):
        """Identify processes related to Penny"""
        try:
            current_process = psutil.Process()
            self.penny_processes.add(current_process.pid)

            # Add parent and child processes
            try:
                parent = current_process.parent()
                if parent:
                    self.penny_processes.add(parent.pid)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

            try:
                for child in current_process.children(recursive=True):
                    self.penny_processes.add(child.pid)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

            # Look for processes with Penny-related names
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    proc_info = proc.info
                    proc_name = proc_info['name'].lower()
                    cmdline = ' '.join(proc_info['cmdline'] or []).lower()

                    if any(term in proc_name or term in cmdline for term in [
                        'penny', 'python', 'claude', 'assistant'
                    ]):
                        self.penny_processes.add(proc_info['pid'])
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

        except Exception as e:
            logging.error(f"Error identifying Penny processes: {e}")

    def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.monitoring_active:
            try:
                # Update process information
                self._update_process_info()

                # Check for runaway processes
                self._check_runaway_processes()

                # Clean up old data
                self._cleanup_old_data()

                time.sleep(self.monitoring_interval)

            except Exception as e:
                logging.error(f"Error in runaway process monitoring loop: {e}")

    def _update_process_info(self):
        """Update information for all monitored processes"""
        current_time = datetime.now()
        active_pids = set()

        try:
            for proc in psutil.process_iter([
                'pid', 'name', 'cmdline', 'cpu_percent', 'memory_percent',
                'memory_info', 'num_threads', 'num_fds', 'create_time',
                'status', 'ppid'
            ]):
                try:
                    proc_info = proc.info
                    pid = proc_info['pid']
                    active_pids.add(pid)

                    # Create ProcessInfo object
                    process_info = ProcessInfo(
                        pid=pid,
                        name=proc_info['name'],
                        cmdline=proc_info['cmdline'] or [],
                        cpu_percent=proc_info['cpu_percent'] or 0.0,
                        memory_percent=proc_info['memory_percent'] or 0.0,
                        memory_rss=proc_info['memory_info'].rss if proc_info['memory_info'] else 0,
                        num_threads=proc_info['num_threads'] or 0,
                        num_fds=proc_info['num_fds'] or 0,
                        create_time=datetime.fromtimestamp(proc_info['create_time']) if proc_info['create_time'] else current_time,
                        status=proc_info['status'] or 'unknown',
                        ppid=proc_info['ppid'] or 0
                    )

                    # Add child processes
                    try:
                        children = proc.children()
                        process_info.children_pids = [child.pid for child in children]
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        process_info.children_pids = []

                    # Store process info
                    self.monitored_processes[pid] = process_info

                    # Add to history
                    if pid not in self.process_history:
                        self.process_history[pid] = []
                    self.process_history[pid].append(process_info)

                    # Limit history size
                    if len(self.process_history[pid]) > 100:
                        self.process_history[pid] = self.process_history[pid][-50:]

                    # Log to database (sample every 10th monitoring cycle to reduce data)
                    if len(self.process_history[pid]) % 10 == 0:
                        self._log_process_info(process_info, current_time)

                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue

            # Remove processes that no longer exist
            dead_pids = set(self.monitored_processes.keys()) - active_pids
            for pid in dead_pids:
                del self.monitored_processes[pid]

        except Exception as e:
            logging.error(f"Error updating process info: {e}")

    def _log_process_info(self, process_info: ProcessInfo, timestamp: datetime):
        """Log process information to database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO process_monitoring
                    (pid, name, cmdline, cpu_percent, memory_percent, memory_rss,
                     num_threads, num_fds, create_time, status, ppid, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    process_info.pid,
                    process_info.name,
                    json.dumps(process_info.cmdline),
                    process_info.cpu_percent,
                    process_info.memory_percent,
                    process_info.memory_rss,
                    process_info.num_threads,
                    process_info.num_fds,
                    process_info.create_time.isoformat(),
                    process_info.status,
                    process_info.ppid,
                    timestamp.isoformat()
                ))
        except Exception as e:
            logging.error(f"Error logging process info: {e}")

    def _check_runaway_processes(self):
        """Check for runaway processes and handle them"""
        current_time = datetime.now()

        for pid, process_info in self.monitored_processes.items():
            # Skip protected processes
            if process_info.name in self.protected_processes:
                continue

            # Check for runaway conditions
            alerts = self._detect_runaway_conditions(process_info)

            for alert in alerts:
                # Check alert cooldown
                if pid in self.recent_alerts:
                    time_since_last_alert = (current_time - self.recent_alerts[pid]).total_seconds()
                    if time_since_last_alert < self.alert_cooldown:
                        continue

                # Log alert
                asyncio.run(self._log_process_alert(alert))
                self.recent_alerts[pid] = current_time

                # Determine if termination is needed
                if alert.severity == "critical":
                    asyncio.run(self._handle_runaway_process(process_info, alert))

    def _detect_runaway_conditions(self, process_info: ProcessInfo) -> List[ProcessAlert]:
        """Detect various runaway conditions for a process"""
        alerts = []
        current_time = datetime.now()

        # CPU usage check
        if process_info.cpu_percent > self.cpu_threshold:
            alerts.append(ProcessAlert(
                pid=process_info.pid,
                process_name=process_info.name,
                trigger=DetectionTrigger.CPU_USAGE,
                current_value=process_info.cpu_percent,
                threshold_value=self.cpu_threshold,
                severity="critical" if process_info.cpu_percent > 95 else "warning",
                description=f"High CPU usage: {process_info.cpu_percent:.1f}%",
                timestamp=current_time,
                recommended_action="Consider terminating process" if process_info.cpu_percent > 95 else "Monitor closely"
            ))

        # Memory usage check
        if process_info.memory_percent > self.memory_threshold:
            alerts.append(ProcessAlert(
                pid=process_info.pid,
                process_name=process_info.name,
                trigger=DetectionTrigger.MEMORY_USAGE,
                current_value=process_info.memory_percent,
                threshold_value=self.memory_threshold,
                severity="critical" if process_info.memory_percent > 90 else "warning",
                description=f"High memory usage: {process_info.memory_percent:.1f}%",
                timestamp=current_time,
                recommended_action="Consider terminating process" if process_info.memory_percent > 90 else "Monitor closely"
            ))

        # Execution time check
        execution_time = (current_time - process_info.create_time).total_seconds()
        if execution_time > self.execution_time_threshold:
            alerts.append(ProcessAlert(
                pid=process_info.pid,
                process_name=process_info.name,
                trigger=DetectionTrigger.EXECUTION_TIME,
                current_value=execution_time,
                threshold_value=self.execution_time_threshold,
                severity="warning",
                description=f"Long execution time: {execution_time:.0f} seconds",
                timestamp=current_time,
                recommended_action="Review process necessity"
            ))

        # File handle check
        if process_info.num_fds > self.file_handle_threshold:
            alerts.append(ProcessAlert(
                pid=process_info.pid,
                process_name=process_info.name,
                trigger=DetectionTrigger.FILE_HANDLES,
                current_value=process_info.num_fds,
                threshold_value=self.file_handle_threshold,
                severity="critical" if process_info.num_fds > 1000 else "warning",
                description=f"High file descriptor usage: {process_info.num_fds}",
                timestamp=current_time,
                recommended_action="Check for file descriptor leaks"
            ))

        # Child process count check
        if len(process_info.children_pids) > self.process_count_threshold:
            alerts.append(ProcessAlert(
                pid=process_info.pid,
                process_name=process_info.name,
                trigger=DetectionTrigger.CHILD_PROCESSES,
                current_value=len(process_info.children_pids),
                threshold_value=self.process_count_threshold,
                severity="warning",
                description=f"High child process count: {len(process_info.children_pids)}",
                timestamp=current_time,
                recommended_action="Review process spawning behavior"
            ))

        return alerts

    async def _log_process_alert(self, alert: ProcessAlert):
        """Log process alert to database and security logger"""
        try:
            # Log to database
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO process_alerts
                    (pid, process_name, trigger_type, current_value, threshold_value,
                     severity, description, recommended_action, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    alert.pid,
                    alert.process_name,
                    alert.trigger.value,
                    alert.current_value,
                    alert.threshold_value,
                    alert.severity,
                    alert.description,
                    alert.recommended_action,
                    alert.timestamp.isoformat()
                ))

            # Log to security logger
            if self.security_logger:
                await self.security_logger.log_security_event(
                    event_type=SecurityEventType.ANOMALY_DETECTED,
                    severity=SecuritySeverity.CRITICAL if alert.severity == "critical" else SecuritySeverity.WARNING,
                    details={
                        'component': 'Runaway Process Detector',
                        'alert_type': 'process_runaway',
                        'pid': alert.pid,
                        'process_name': alert.process_name,
                        'trigger': alert.trigger.value,
                        'current_value': alert.current_value,
                        'threshold_value': alert.threshold_value,
                        'description': alert.description,
                        'recommended_action': alert.recommended_action
                    }
                )

        except Exception as e:
            logging.error(f"Error logging process alert: {e}")

    async def _handle_runaway_process(self, process_info: ProcessInfo, alert: ProcessAlert):
        """Handle a detected runaway process"""
        # Special handling for Penny's own processes
        if process_info.pid in self.penny_processes:
            await self._handle_penny_process_runaway(process_info, alert)
            return

        # Determine termination method
        termination_method = self._determine_termination_method(process_info, alert)

        # Attempt termination
        termination_result = await self._terminate_process(
            process_info.pid,
            termination_method,
            f"Runaway process detected: {alert.description}"
        )

        # Log termination attempt
        termination_record = ProcessTermination(
            pid=process_info.pid,
            process_name=process_info.name,
            termination_method=termination_method,
            termination_reason=f"Runaway process: {alert.trigger.value}",
            cpu_usage_at_termination=process_info.cpu_percent,
            memory_usage_at_termination=process_info.memory_percent,
            execution_time_seconds=(datetime.now() - process_info.create_time).total_seconds(),
            timestamp=datetime.now(),
            success=termination_result[0],
            error_message=termination_result[1] if not termination_result[0] else None
        )

        await self._log_termination(termination_record)

    async def _handle_penny_process_runaway(self, process_info: ProcessInfo, alert: ProcessAlert):
        """Special handling for Penny's own processes"""
        # Log but don't terminate Penny's main processes
        if self.security_logger:
            await self.security_logger.log_security_event(
                event_type=SecurityEventType.SECURITY_VIOLATION,
                severity=SecuritySeverity.CRITICAL,
                details={
                    'component': 'Runaway Process Detector',
                    'alert_type': 'penny_process_runaway',
                    'pid': process_info.pid,
                    'process_name': process_info.name,
                    'trigger': alert.trigger.value,
                    'current_value': alert.current_value,
                    'description': alert.description,
                    'action': 'monitored_but_not_terminated'
                }
            )

        # Could implement self-optimization here
        # For now, just log and monitor

    def _determine_termination_method(self, process_info: ProcessInfo, alert: ProcessAlert) -> TerminationMethod:
        """Determine appropriate termination method"""
        # Very high resource usage - force kill
        if (alert.trigger == DetectionTrigger.CPU_USAGE and alert.current_value > 95) or \
           (alert.trigger == DetectionTrigger.MEMORY_USAGE and alert.current_value > 95):
            return TerminationMethod.SIGKILL

        # File descriptor leak - graceful termination
        if alert.trigger == DetectionTrigger.FILE_HANDLES:
            return TerminationMethod.SIGTERM

        # Long running process - timeout-based termination
        if alert.trigger == DetectionTrigger.EXECUTION_TIME:
            return TerminationMethod.TIMEOUT

        # Default to graceful termination
        return TerminationMethod.SIGTERM

    async def _terminate_process(self, pid: int, method: TerminationMethod, reason: str) -> Tuple[bool, Optional[str]]:
        """Terminate a process using specified method"""
        try:
            process = psutil.Process(pid)

            if method == TerminationMethod.SIGTERM:
                # Graceful termination
                process.terminate()

                # Wait for graceful termination
                try:
                    process.wait(timeout=self.termination_grace_period)
                    return True, None
                except psutil.TimeoutExpired:
                    # Force kill if graceful termination fails
                    process.kill()
                    return True, "Graceful termination failed, used force kill"

            elif method == TerminationMethod.SIGKILL:
                # Force kill
                process.kill()
                return True, None

            elif method == TerminationMethod.TIMEOUT:
                # Timeout-based termination
                process.terminate()
                try:
                    process.wait(timeout=10)  # Shorter timeout
                    return True, None
                except psutil.TimeoutExpired:
                    process.kill()
                    return True, "Timeout termination failed, used force kill"

            else:
                return False, f"Unknown termination method: {method}"

        except psutil.NoSuchProcess:
            return True, "Process already terminated"
        except psutil.AccessDenied:
            return False, "Access denied - cannot terminate process"
        except Exception as e:
            return False, f"Termination failed: {str(e)}"

    async def _log_termination(self, termination: ProcessTermination):
        """Log process termination"""
        try:
            # Log to database
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO process_terminations
                    (pid, process_name, termination_method, termination_reason,
                     cpu_usage_at_termination, memory_usage_at_termination,
                     execution_time_seconds, success, error_message, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    termination.pid,
                    termination.process_name,
                    termination.termination_method.value,
                    termination.termination_reason,
                    termination.cpu_usage_at_termination,
                    termination.memory_usage_at_termination,
                    termination.execution_time_seconds,
                    termination.success,
                    termination.error_message,
                    termination.timestamp.isoformat()
                ))

            # Add to local history
            self.terminated_processes.append(termination)

            # Log to security logger
            if self.security_logger:
                await self.security_logger.log_security_event(
                    event_type=SecurityEventType.SYSTEM_UPDATE,
                    severity=SecuritySeverity.WARNING,
                    details={
                        'component': 'Runaway Process Detector',
                        'action': 'process_terminated',
                        'pid': termination.pid,
                        'process_name': termination.process_name,
                        'termination_method': termination.termination_method.value,
                        'reason': termination.termination_reason,
                        'success': termination.success,
                        'error_message': termination.error_message,
                        'cpu_usage': termination.cpu_usage_at_termination,
                        'memory_usage': termination.memory_usage_at_termination
                    }
                )

        except Exception as e:
            logging.error(f"Error logging termination: {e}")

    def _cleanup_old_data(self):
        """Clean up old monitoring data"""
        try:
            cleanup_date = (datetime.now() - timedelta(days=7)).isoformat()

            with sqlite3.connect(self.db_path) as conn:
                # Keep only last 7 days of process monitoring data
                conn.execute("""
                    DELETE FROM process_monitoring
                    WHERE timestamp < ?
                """, (cleanup_date,))

                # Keep alerts for 30 days
                alert_cleanup_date = (datetime.now() - timedelta(days=30)).isoformat()
                conn.execute("""
                    DELETE FROM process_alerts
                    WHERE timestamp < ?
                """, (alert_cleanup_date,))

                # Keep termination records for 90 days
                termination_cleanup_date = (datetime.now() - timedelta(days=90)).isoformat()
                conn.execute("""
                    DELETE FROM process_terminations
                    WHERE timestamp < ?
                """, (termination_cleanup_date,))

        except Exception as e:
            logging.error(f"Error cleaning up old data: {e}")

    def get_current_stats(self) -> Dict[str, Any]:
        """Get current process monitoring statistics"""
        return {
            'monitored_processes': len(self.monitored_processes),
            'penny_processes': len(self.penny_processes),
            'terminated_processes': len(self.terminated_processes),
            'recent_alerts': len(self.recent_alerts),
            'monitoring_active': self.monitoring_active,
            'thresholds': {
                'cpu_threshold': self.cpu_threshold,
                'memory_threshold': self.memory_threshold,
                'execution_time_threshold': self.execution_time_threshold,
                'file_handle_threshold': self.file_handle_threshold,
                'process_count_threshold': self.process_count_threshold
            }
        }

    async def get_process_alerts(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get recent process alerts"""
        start_time = (datetime.now() - timedelta(hours=hours)).isoformat()

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT pid, process_name, trigger_type, current_value, threshold_value,
                       severity, description, recommended_action, timestamp
                FROM process_alerts
                WHERE timestamp >= ?
                ORDER BY timestamp DESC
            """, (start_time,))

            return [
                {
                    'pid': row[0],
                    'process_name': row[1],
                    'trigger_type': row[2],
                    'current_value': row[3],
                    'threshold_value': row[4],
                    'severity': row[5],
                    'description': row[6],
                    'recommended_action': row[7],
                    'timestamp': row[8]
                }
                for row in cursor.fetchall()
            ]

    async def get_termination_history(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get recent process terminations"""
        start_time = (datetime.now() - timedelta(hours=hours)).isoformat()

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT pid, process_name, termination_method, termination_reason,
                       cpu_usage_at_termination, memory_usage_at_termination,
                       execution_time_seconds, success, error_message, timestamp
                FROM process_terminations
                WHERE timestamp >= ?
                ORDER BY timestamp DESC
            """, (start_time,))

            return [
                {
                    'pid': row[0],
                    'process_name': row[1],
                    'termination_method': row[2],
                    'termination_reason': row[3],
                    'cpu_usage_at_termination': row[4],
                    'memory_usage_at_termination': row[5],
                    'execution_time_seconds': row[6],
                    'success': bool(row[7]),
                    'error_message': row[8],
                    'timestamp': row[9]
                }
                for row in cursor.fetchall()
            ]

    def update_thresholds(self, **kwargs):
        """Update detection thresholds"""
        for attr, value in kwargs.items():
            if hasattr(self, attr) and isinstance(value, (int, float)):
                setattr(self, attr, value)

    def add_protected_process(self, process_name: str):
        """Add a process to the protected list"""
        self.protected_processes.add(process_name)

    def remove_protected_process(self, process_name: str):
        """Remove a process from the protected list"""
        self.protected_processes.discard(process_name)


# Integration helper function
async def create_integrated_runaway_detector(
    security_logger: Optional[EnhancedSecurityLogging] = None,
    rate_limiter: Optional[RateLimitingResourceControl] = None
) -> RunawayProcessDetector:
    """
    Create integrated runaway process detector

    Returns configured and initialized detector
    """
    detector = RunawayProcessDetector(
        security_logger=security_logger,
        rate_limiter=rate_limiter
    )

    # Start monitoring
    await detector.start_monitoring()

    return detector


if __name__ == "__main__":
    # Example usage
    async def main():
        # Create runaway process detector
        detector = await create_integrated_runaway_detector()

        # Get current statistics
        stats = detector.get_current_stats()
        print(f"Current stats: {stats}")

        # Monitor for 30 seconds
        await asyncio.sleep(30)

        # Get recent alerts
        alerts = await detector.get_process_alerts(hours=1)
        print(f"Recent alerts: {len(alerts)}")

        # Stop monitoring
        detector.stop_monitoring()

    asyncio.run(main())