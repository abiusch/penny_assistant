#!/usr/bin/env python3
"""
Multi-Channel Emergency Stop System for Penny AI Assistant
Phase A2: Critical Security Foundations - Emergency Stop Implementation

This system provides comprehensive emergency stop capabilities across all interfaces:
- Voice phrase detection ("emergency stop", "halt penny", "abort")
- Enhanced keyboard interrupt handling (Ctrl+C, Ctrl+Break)
- Timeout-based auto-stop triggers (30+ second operations)
- Process termination capabilities
- Emergency state management
- Multi-interface coordination

Integrates with existing security framework and maintains audit trails.
"""

import asyncio
import signal
import threading
import time
import json
import logging
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable, Any, Set
from enum import Enum
from dataclasses import dataclass, asdict
import concurrent.futures
import subprocess
import psutil
import os

# Import existing security components
from security_ethics_foundation import SecurityEthicsFoundation, EthicalBoundary
from command_whitelist_system import CommandWhitelistSystem, PermissionLevel


class EmergencyTrigger(Enum):
    """Types of emergency stop triggers"""
    VOICE_COMMAND = "voice_command"
    KEYBOARD_INTERRUPT = "keyboard_interrupt"
    TIMEOUT_AUTO = "timeout_auto"
    PROCESS_MONITOR = "process_monitor"
    RESOURCE_LIMIT = "resource_limit"
    SECURITY_VIOLATION = "security_violation"
    USER_MANUAL = "user_manual"
    SYSTEM_ERROR = "system_error"


class EmergencyState(Enum):
    """Emergency system states"""
    NORMAL = "normal"
    WARNING = "warning"
    EMERGENCY = "emergency"
    LOCKDOWN = "lockdown"
    RECOVERY = "recovery"


@dataclass
class EmergencyEvent:
    """Emergency stop event record"""
    timestamp: str
    trigger_type: EmergencyTrigger
    trigger_source: str
    description: str
    session_id: str
    context: Dict[str, Any]
    processes_terminated: List[int]
    recovery_required: bool
    severity: str  # LOW, MEDIUM, HIGH, CRITICAL


@dataclass
class ProcessMonitor:
    """Monitor for long-running processes"""
    pid: int
    command: str
    start_time: datetime
    timeout_seconds: int
    operation_name: str
    session_id: str


class MultiChannelEmergencyStop:
    """
    Comprehensive emergency stop system supporting multiple trigger channels
    """

    def __init__(self, database_path: str = "emergency_system.db"):
        self.database_path = database_path
        self.logger = logging.getLogger("emergency_stop")

        # Emergency state management
        self.current_state = EmergencyState.NORMAL
        self.emergency_active = False
        self.last_activity = datetime.now()

        # Voice phrase detection
        self.emergency_phrases = {
            "emergency stop": EmergencyTrigger.VOICE_COMMAND,
            "halt penny": EmergencyTrigger.VOICE_COMMAND,
            "abort": EmergencyTrigger.VOICE_COMMAND,
            "stop everything": EmergencyTrigger.VOICE_COMMAND,
            "emergency abort": EmergencyTrigger.VOICE_COMMAND,
            "kill all": EmergencyTrigger.VOICE_COMMAND
        }

        # Process monitoring
        self.monitored_processes: Dict[int, ProcessMonitor] = {}
        self.process_lock = threading.Lock()

        # Callback registration
        self.emergency_callbacks: List[Callable[[EmergencyEvent], None]] = []
        self.state_change_callbacks: List[Callable[[EmergencyState, EmergencyState], None]] = []

        # Configuration
        self.config = {
            "default_timeout_seconds": 30,
            "voice_phrase_timeout": 5.0,
            "keyboard_interrupt_timeout": 2.0,
            "resource_monitor_interval": 1.0,
            "max_cpu_percent": 90.0,
            "max_memory_mb": 2048,
            "auto_recovery_timeout": 300  # 5 minutes
        }

        # Initialize components
        self._setup_database()
        self._setup_signal_handlers()
        self._start_monitoring_threads()

        # Integration with existing security
        self.security_foundation = SecurityEthicsFoundation()
        self.command_whitelist = None  # Will be set by parent system

        self.logger.info("Multi-channel emergency stop system initialized")

    def _setup_database(self) -> None:
        """Initialize emergency system database"""
        try:
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS emergency_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    trigger_type TEXT NOT NULL,
                    trigger_source TEXT NOT NULL,
                    description TEXT NOT NULL,
                    session_id TEXT NOT NULL,
                    context TEXT NOT NULL,
                    processes_terminated TEXT NOT NULL,
                    recovery_required BOOLEAN NOT NULL,
                    severity TEXT NOT NULL
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS process_monitors (
                    pid INTEGER PRIMARY KEY,
                    command TEXT NOT NULL,
                    start_time TEXT NOT NULL,
                    timeout_seconds INTEGER NOT NULL,
                    operation_name TEXT NOT NULL,
                    session_id TEXT NOT NULL
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS system_state (
                    timestamp TEXT PRIMARY KEY,
                    state TEXT NOT NULL,
                    previous_state TEXT,
                    trigger_event_id INTEGER,
                    context TEXT
                )
            ''')

            conn.commit()
            conn.close()

        except Exception as e:
            self.logger.error(f"Database setup failed: {e}")
            raise

    def _setup_signal_handlers(self) -> None:
        """Setup enhanced keyboard interrupt handling"""
        # Track interrupt frequency to detect rapid/repeated interrupts
        self.interrupt_history = []
        self.max_interrupt_history = 10

        def enhanced_sigint_handler(signum, frame):
            current_time = datetime.now()
            self.interrupt_history.append(current_time)

            # Keep only recent history
            if len(self.interrupt_history) > self.max_interrupt_history:
                self.interrupt_history.pop(0)

            # Check for rapid successive interrupts (emergency escalation)
            recent_interrupts = [
                t for t in self.interrupt_history
                if (current_time - t).total_seconds() < 5.0  # Within 5 seconds
            ]

            interrupt_frequency = len(recent_interrupts)

            self.logger.warning(f"Enhanced SIGINT (Ctrl+C) detected - frequency: {interrupt_frequency}")

            # Escalate to immediate shutdown if multiple rapid interrupts
            if interrupt_frequency >= 3:
                description = f"Rapid Ctrl+C interrupts detected ({interrupt_frequency}x in 5s) - Force shutdown"
                severity = "CRITICAL"
            else:
                description = "Enhanced Ctrl+C emergency stop"
                severity = "HIGH"

            self._trigger_emergency_stop(
                trigger_type=EmergencyTrigger.KEYBOARD_INTERRUPT,
                trigger_source="SIGINT",
                description=description,
                session_id="keyboard_interrupt",
                context={
                    "signal": signum,
                    "frame": str(frame)[:200],  # Limit frame info
                    "interrupt_frequency": interrupt_frequency,
                    "rapid_escalation": interrupt_frequency >= 3,
                    "interrupt_history": [t.isoformat() for t in recent_interrupts]
                }
            )

            # For rapid interrupts, also terminate immediately
            if interrupt_frequency >= 3:
                self.logger.critical("FORCE SHUTDOWN due to rapid interrupts")
                os._exit(1)  # Force immediate exit

        def sigterm_handler(signum, frame):
            self.logger.warning("SIGTERM detected - System termination requested")
            self._trigger_emergency_stop(
                trigger_type=EmergencyTrigger.KEYBOARD_INTERRUPT,
                trigger_source="SIGTERM",
                description="System termination signal (SIGTERM)",
                session_id="system_termination",
                context={
                    "signal": signum,
                    "clean_shutdown": True,
                    "initiated_by": "system"
                }
            )

        def sigusr1_handler(signum, frame):
            """Custom emergency signal for manual triggers"""
            self.logger.warning("SIGUSR1 detected - Manual emergency trigger")
            self._trigger_emergency_stop(
                trigger_type=EmergencyTrigger.USER_MANUAL,
                trigger_source="SIGUSR1",
                description="Manual emergency signal (SIGUSR1)",
                session_id="manual_signal",
                context={
                    "signal": signum,
                    "manual_trigger": True
                }
            )

        # Register enhanced signal handlers
        try:
            signal.signal(signal.SIGINT, enhanced_sigint_handler)
            signal.signal(signal.SIGTERM, sigterm_handler)

            # Platform-specific handlers
            if hasattr(signal, 'SIGBREAK'):
                signal.signal(signal.SIGBREAK, enhanced_sigint_handler)

            # Manual emergency trigger (Unix-like systems)
            if hasattr(signal, 'SIGUSR1'):
                signal.signal(signal.SIGUSR1, sigusr1_handler)

            self.logger.info("Enhanced signal handlers registered successfully")

        except Exception as e:
            self.logger.error(f"Failed to register signal handlers: {e}")

    def send_manual_emergency_signal(self) -> bool:
        """Send manual emergency signal (for testing or external triggers)"""
        try:
            if hasattr(signal, 'SIGUSR1'):
                os.kill(os.getpid(), signal.SIGUSR1)
                return True
            else:
                # Fallback for systems without SIGUSR1
                self._trigger_emergency_stop(
                    trigger_type=EmergencyTrigger.USER_MANUAL,
                    trigger_source="manual_call",
                    description="Manual emergency stop call",
                    session_id="manual_trigger",
                    context={"method": "direct_call"}
                )
                return True
        except Exception as e:
            self.logger.error(f"Failed to send manual emergency signal: {e}")
            return False

    def _start_monitoring_threads(self) -> None:
        """Start background monitoring threads"""
        # Process timeout monitoring
        self.timeout_thread = threading.Thread(
            target=self._monitor_process_timeouts,
            daemon=True,
            name="EmergencyTimeoutMonitor"
        )
        self.timeout_thread.start()

        # Resource monitoring
        self.resource_thread = threading.Thread(
            target=self._monitor_system_resources,
            daemon=True,
            name="EmergencyResourceMonitor"
        )
        self.resource_thread.start()

        # Activity monitoring
        self.activity_thread = threading.Thread(
            target=self._monitor_system_activity,
            daemon=True,
            name="EmergencyActivityMonitor"
        )
        self.activity_thread.start()

    def register_process(self, pid: int, command: str, operation_name: str,
                        session_id: str, timeout_seconds: int = None) -> None:
        """Register a process for timeout monitoring"""
        if timeout_seconds is None:
            timeout_seconds = self.config["default_timeout_seconds"]

        monitor = ProcessMonitor(
            pid=pid,
            command=command,
            start_time=datetime.now(),
            timeout_seconds=timeout_seconds,
            operation_name=operation_name,
            session_id=session_id
        )

        with self.process_lock:
            self.monitored_processes[pid] = monitor

        # Store in database
        try:
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO process_monitors
                (pid, command, start_time, timeout_seconds, operation_name, session_id)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                pid, command, monitor.start_time.isoformat(),
                timeout_seconds, operation_name, session_id
            ))
            conn.commit()
            conn.close()
        except Exception as e:
            self.logger.error(f"Failed to store process monitor: {e}")

        self.logger.info(f"Registered process {pid} for monitoring: {operation_name}")

    def unregister_process(self, pid: int) -> None:
        """Remove a process from monitoring"""
        with self.process_lock:
            if pid in self.monitored_processes:
                del self.monitored_processes[pid]

        try:
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()
            cursor.execute('DELETE FROM process_monitors WHERE pid = ?', (pid,))
            conn.commit()
            conn.close()
        except Exception as e:
            self.logger.error(f"Failed to remove process monitor: {e}")

        self.logger.debug(f"Unregistered process {pid} from monitoring")

    def check_voice_phrase(self, transcribed_text: str, session_id: str) -> bool:
        """Check if transcribed voice contains emergency phrases"""
        if not transcribed_text:
            return False

        text_lower = transcribed_text.lower().strip()

        for phrase, trigger_type in self.emergency_phrases.items():
            if phrase in text_lower:
                self.logger.warning(f"Emergency voice phrase detected: '{phrase}'")

                self._trigger_emergency_stop(
                    trigger_type=trigger_type,
                    trigger_source="voice_interface",
                    description=f"Voice emergency phrase: '{phrase}'",
                    session_id=session_id,
                    context={
                        "transcribed_text": transcribed_text,
                        "detected_phrase": phrase,
                        "confidence": 1.0  # Would be from speech recognition
                    }
                )
                return True

        return False

    def _monitor_process_timeouts(self) -> None:
        """Background thread to monitor process timeouts"""
        while not self.emergency_active:
            try:
                current_time = datetime.now()
                timed_out_processes = []

                with self.process_lock:
                    for pid, monitor in list(self.monitored_processes.items()):
                        runtime = current_time - monitor.start_time

                        if runtime.total_seconds() > monitor.timeout_seconds:
                            # Check if process is still running
                            try:
                                process = psutil.Process(pid)
                                if process.is_running():
                                    timed_out_processes.append((pid, monitor))
                            except psutil.NoSuchProcess:
                                # Process already ended, remove from monitoring
                                del self.monitored_processes[pid]

                # Handle timed out processes
                for pid, monitor in timed_out_processes:
                    self.logger.warning(f"Process {pid} timed out after {monitor.timeout_seconds}s")

                    self._trigger_emergency_stop(
                        trigger_type=EmergencyTrigger.TIMEOUT_AUTO,
                        trigger_source="timeout_monitor",
                        description=f"Process timeout: {monitor.operation_name}",
                        session_id=monitor.session_id,
                        context={
                            "pid": pid,
                            "command": monitor.command,
                            "runtime_seconds": (current_time - monitor.start_time).total_seconds(),
                            "timeout_limit": monitor.timeout_seconds
                        }
                    )

                time.sleep(1.0)  # Check every second

            except Exception as e:
                self.logger.error(f"Error in timeout monitoring: {e}")
                time.sleep(5.0)

    def _monitor_system_resources(self) -> None:
        """Background thread to monitor system resource usage"""
        while not self.emergency_active:
            try:
                # CPU usage check
                cpu_percent = psutil.cpu_percent(interval=1)
                if cpu_percent > self.config["max_cpu_percent"]:
                    self.logger.warning(f"High CPU usage detected: {cpu_percent}%")

                    self._trigger_emergency_stop(
                        trigger_type=EmergencyTrigger.RESOURCE_LIMIT,
                        trigger_source="resource_monitor",
                        description=f"High CPU usage: {cpu_percent}%",
                        session_id="resource_emergency",
                        context={"cpu_percent": cpu_percent, "limit": self.config["max_cpu_percent"]}
                    )

                # Memory usage check
                memory = psutil.virtual_memory()
                memory_mb = memory.used / (1024 * 1024)
                if memory_mb > self.config["max_memory_mb"]:
                    self.logger.warning(f"High memory usage detected: {memory_mb:.1f}MB")

                    self._trigger_emergency_stop(
                        trigger_type=EmergencyTrigger.RESOURCE_LIMIT,
                        trigger_source="resource_monitor",
                        description=f"High memory usage: {memory_mb:.1f}MB",
                        session_id="resource_emergency",
                        context={"memory_mb": memory_mb, "limit": self.config["max_memory_mb"]}
                    )

                time.sleep(self.config["resource_monitor_interval"])

            except Exception as e:
                self.logger.error(f"Error in resource monitoring: {e}")
                time.sleep(5.0)

    def _monitor_system_activity(self) -> None:
        """Background thread to monitor system activity and health"""
        while not self.emergency_active:
            try:
                # Update last activity timestamp
                self.last_activity = datetime.now()

                # Check for system errors or anomalies
                # This could be expanded to check log files, process status, etc.

                time.sleep(10.0)  # Check every 10 seconds

            except Exception as e:
                self.logger.error(f"Error in activity monitoring: {e}")
                time.sleep(15.0)

    def _trigger_emergency_stop(self, trigger_type: EmergencyTrigger, trigger_source: str,
                               description: str, session_id: str, context: Dict[str, Any]) -> None:
        """Core emergency stop activation logic"""
        if self.emergency_active:
            self.logger.info(f"Emergency already active, ignoring new trigger: {description}")
            return

        self.emergency_active = True
        old_state = self.current_state
        self.current_state = EmergencyState.EMERGENCY

        # Create emergency event
        event = EmergencyEvent(
            timestamp=datetime.now().isoformat(),
            trigger_type=trigger_type,
            trigger_source=trigger_source,
            description=description,
            session_id=session_id,
            context=context,
            processes_terminated=[],
            recovery_required=True,
            severity="HIGH"
        )

        self.logger.critical(f"EMERGENCY STOP ACTIVATED: {description}")

        # Terminate monitored processes
        terminated_pids = self._terminate_all_processes()
        event.processes_terminated = terminated_pids

        # Call existing security foundation emergency stop
        self.security_foundation.emergency_stop(f"{trigger_type.value}: {description}")

        # Store emergency event
        self._store_emergency_event(event)

        # Notify callbacks
        for callback in self.emergency_callbacks:
            try:
                callback(event)
            except Exception as e:
                self.logger.error(f"Emergency callback failed: {e}")

        # Notify state change callbacks
        for callback in self.state_change_callbacks:
            try:
                callback(old_state, self.current_state)
            except Exception as e:
                self.logger.error(f"State change callback failed: {e}")

        # Enter lockdown mode
        self._enter_lockdown_mode(event)

    def _terminate_all_processes(self) -> List[int]:
        """Terminate all monitored processes"""
        terminated_pids = []

        with self.process_lock:
            for pid, monitor in list(self.monitored_processes.items()):
                try:
                    process = psutil.Process(pid)
                    if process.is_running():
                        self.logger.warning(f"Terminating process {pid}: {monitor.operation_name}")

                        # Graceful termination first
                        process.terminate()

                        # Wait briefly for graceful shutdown
                        try:
                            process.wait(timeout=3)
                        except psutil.TimeoutExpired:
                            # Force kill if graceful termination fails
                            self.logger.warning(f"Force killing process {pid}")
                            process.kill()

                        terminated_pids.append(pid)

                except psutil.NoSuchProcess:
                    # Process already ended
                    pass
                except Exception as e:
                    self.logger.error(f"Failed to terminate process {pid}: {e}")

            # Clear all monitored processes
            self.monitored_processes.clear()

        return terminated_pids

    def _enter_lockdown_mode(self, triggering_event: EmergencyEvent) -> None:
        """Enter system lockdown mode after emergency stop"""
        self.current_state = EmergencyState.LOCKDOWN

        self.logger.critical("ENTERING LOCKDOWN MODE - System operations suspended")

        # Clear any pending operations
        if self.command_whitelist:
            # Could clear pending operations or set emergency permission level
            pass

        # Set emergency state in security foundation
        self.security_foundation.security_context = None

        # Log lockdown entry - convert to JSON-serializable format
        triggering_event_dict = asdict(triggering_event)
        triggering_event_dict["trigger_type"] = triggering_event.trigger_type.value

        lockdown_context = {
            "triggering_event": triggering_event_dict,
            "lockdown_timestamp": datetime.now().isoformat(),
            "recovery_timeout": self.config["auto_recovery_timeout"]
        }

        try:
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO system_state (timestamp, state, previous_state, context)
                VALUES (?, ?, ?, ?)
            ''', (
                datetime.now().isoformat(),
                EmergencyState.LOCKDOWN.value,
                EmergencyState.EMERGENCY.value,
                json.dumps(lockdown_context)
            ))
            conn.commit()
            conn.close()
        except Exception as e:
            self.logger.error(f"Failed to log lockdown state: {e}")

    def _store_emergency_event(self, event: EmergencyEvent) -> None:
        """Store emergency event in database"""
        try:
            # Convert context to JSON-serializable format
            context_serializable = {}
            for key, value in event.context.items():
                if isinstance(value, datetime):
                    context_serializable[key] = value.isoformat()
                elif isinstance(value, list) and value and isinstance(value[0], dict):
                    # Handle list of dictionaries with datetime objects
                    serializable_list = []
                    for item in value:
                        if isinstance(item, dict):
                            serializable_item = {}
                            for k, v in item.items():
                                if isinstance(v, datetime):
                                    serializable_item[k] = v.isoformat()
                                else:
                                    serializable_item[k] = v
                            serializable_list.append(serializable_item)
                        else:
                            serializable_list.append(item)
                    context_serializable[key] = serializable_list
                else:
                    context_serializable[key] = value

            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()

            cursor.execute('''
                INSERT INTO emergency_events
                (timestamp, trigger_type, trigger_source, description, session_id,
                 context, processes_terminated, recovery_required, severity)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                event.timestamp,
                event.trigger_type.value,
                event.trigger_source,
                event.description,
                event.session_id,
                json.dumps(context_serializable),
                json.dumps(event.processes_terminated),
                event.recovery_required,
                event.severity
            ))

            conn.commit()
            conn.close()

        except Exception as e:
            self.logger.error(f"Failed to store emergency event: {e}")

    def initiate_recovery(self, recovery_code: str, session_id: str) -> bool:
        """Initiate recovery from emergency state"""
        if self.current_state not in [EmergencyState.EMERGENCY, EmergencyState.LOCKDOWN]:
            self.logger.warning("Recovery attempted but system not in emergency state")
            return False

        self.logger.info(f"Initiating recovery with code: {recovery_code}")

        # Validate recovery conditions
        if not self._validate_recovery_conditions():
            self.logger.error("Recovery validation failed")
            return False

        # Change state to recovery
        old_state = self.current_state
        self.current_state = EmergencyState.RECOVERY

        # Log recovery initiation
        recovery_context = {
            "recovery_code": recovery_code,
            "session_id": session_id,
            "recovery_timestamp": datetime.now().isoformat(),
            "previous_state": old_state.value
        }

        try:
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO system_state (timestamp, state, previous_state, context)
                VALUES (?, ?, ?, ?)
            ''', (
                datetime.now().isoformat(),
                EmergencyState.RECOVERY.value,
                old_state.value,
                json.dumps(recovery_context)
            ))
            conn.commit()
            conn.close()
        except Exception as e:
            self.logger.error(f"Failed to log recovery state: {e}")

        # Perform recovery steps
        success = self._perform_recovery_steps()

        if success:
            self.current_state = EmergencyState.NORMAL
            self.emergency_active = False
            self.logger.info("Recovery completed successfully")
        else:
            self.current_state = EmergencyState.LOCKDOWN
            self.logger.error("Recovery failed, returning to lockdown")

        return success

    def _validate_recovery_conditions(self) -> bool:
        """Validate conditions for recovery"""
        # Check system resources
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()

            if cpu_percent > 50:  # Lower threshold for recovery
                self.logger.warning(f"CPU usage too high for recovery: {cpu_percent}%")
                return False

            if memory.percent > 80:  # Memory check
                self.logger.warning(f"Memory usage too high for recovery: {memory.percent}%")
                return False

            return True

        except Exception as e:
            self.logger.error(f"Failed to validate recovery conditions: {e}")
            return False

    def _perform_recovery_steps(self) -> bool:
        """Perform actual recovery operations"""
        try:
            # Clear process monitors database
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()
            cursor.execute('DELETE FROM process_monitors')
            conn.commit()
            conn.close()

            # Reset monitoring state
            with self.process_lock:
                self.monitored_processes.clear()

            # Reset security foundation if needed
            # self.security_foundation could be reset here

            self.logger.info("Recovery steps completed")
            return True

        except Exception as e:
            self.logger.error(f"Recovery steps failed: {e}")
            return False

    def register_emergency_callback(self, callback: Callable[[EmergencyEvent], None]) -> None:
        """Register callback for emergency events"""
        self.emergency_callbacks.append(callback)

    def register_state_callback(self, callback: Callable[[EmergencyState, EmergencyState], None]) -> None:
        """Register callback for state changes"""
        self.state_change_callbacks.append(callback)

    def get_emergency_status(self) -> Dict[str, Any]:
        """Get current emergency system status"""
        return {
            "state": self.current_state.value,
            "emergency_active": self.emergency_active,
            "monitored_processes": len(self.monitored_processes),
            "last_activity": self.last_activity.isoformat(),
            "config": self.config.copy()
        }

    def get_emergency_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent emergency events"""
        try:
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()

            cursor.execute('''
                SELECT * FROM emergency_events
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (limit,))

            columns = [desc[0] for desc in cursor.description]
            events = [dict(zip(columns, row)) for row in cursor.fetchall()]

            conn.close()
            return events

        except Exception as e:
            self.logger.error(f"Failed to get emergency history: {e}")
            return []


def test_emergency_system():
    """Test the emergency stop system"""
    emergency_system = MultiChannelEmergencyStop("test_emergency.db")

    print("Testing emergency stop system...")

    # Test voice phrase detection
    test_phrases = [
        "Please help me with something",
        "emergency stop right now",
        "halt penny immediately",
        "abort the current operation"
    ]

    for phrase in test_phrases:
        result = emergency_system.check_voice_phrase(phrase, "test_session")
        print(f"Phrase: '{phrase}' -> Emergency: {result}")

    # Test process registration
    fake_pid = 99999
    emergency_system.register_process(
        pid=fake_pid,
        command="test_command",
        operation_name="test_operation",
        session_id="test_session",
        timeout_seconds=5
    )

    print(f"Registered fake process {fake_pid}")

    # Check status
    status = emergency_system.get_emergency_status()
    print(f"Emergency status: {status}")

    # Simulate emergency
    emergency_system._trigger_emergency_stop(
        trigger_type=EmergencyTrigger.USER_MANUAL,
        trigger_source="test",
        description="Manual test emergency",
        session_id="test_session",
        context={"test": True}
    )

    # Check history
    history = emergency_system.get_emergency_history(limit=5)
    print(f"Emergency history: {len(history)} events")

    # Test recovery
    success = emergency_system.initiate_recovery("test_recovery", "test_session")
    print(f"Recovery success: {success}")


class VoiceEmergencyDetector:
    """
    Enhanced voice phrase detection for emergency stop commands
    Integrates with existing voice interface components
    """

    def __init__(self, emergency_system: MultiChannelEmergencyStop):
        self.emergency_system = emergency_system
        self.logger = logging.getLogger("voice_emergency")

        # Enhanced emergency phrases with confidence thresholds
        self.emergency_phrases = {
            # Primary emergency phrases
            "emergency stop": 0.9,
            "halt penny": 0.9,
            "abort": 0.8,
            "stop everything": 0.9,
            "emergency abort": 0.9,
            "kill all": 0.7,

            # Alternative phrasings
            "stop now": 0.8,
            "cancel everything": 0.8,
            "shut down": 0.7,
            "stop all operations": 0.9,
            "emergency halt": 0.9,
            "abort all": 0.8,

            # Quick/urgent variants
            "stop": 0.6,  # Lower confidence due to common usage
            "halt": 0.7,
            "quit": 0.5,
            "exit": 0.5
        }

        # Context-aware detection
        self.recent_transcriptions = []
        self.max_history = 5

    def process_voice_input(self, transcribed_text: str, confidence: float, session_id: str) -> bool:
        """
        Process voice input for emergency phrases with context awareness

        Args:
            transcribed_text: The transcribed voice input
            confidence: Speech recognition confidence (0.0-1.0)
            session_id: Current session identifier

        Returns:
            bool: True if emergency stop was triggered
        """
        if not transcribed_text or confidence < 0.5:
            return False

        # Store in recent history for context
        self.recent_transcriptions.append({
            "text": transcribed_text,
            "confidence": confidence,
            "timestamp": datetime.now()
        })

        # Keep only recent history
        if len(self.recent_transcriptions) > self.max_history:
            self.recent_transcriptions.pop(0)

        # Normalize text for detection
        normalized_text = transcribed_text.lower().strip()

        # Check for emergency phrases
        for phrase, min_confidence in self.emergency_phrases.items():
            if phrase in normalized_text:
                # Calculate total confidence (speech recognition + phrase confidence)
                total_confidence = confidence * min_confidence

                self.logger.warning(f"Emergency phrase detected: '{phrase}' (confidence: {total_confidence:.2f})")

                # Trigger emergency stop if confidence is high enough
                if total_confidence >= 0.6:  # Adjustable threshold
                    self.emergency_system._trigger_emergency_stop(
                        trigger_type=EmergencyTrigger.VOICE_COMMAND,
                        trigger_source="voice_interface",
                        description=f"Voice emergency phrase: '{phrase}'",
                        session_id=session_id,
                        context={
                            "transcribed_text": transcribed_text,
                            "detected_phrase": phrase,
                            "speech_confidence": confidence,
                            "phrase_confidence": min_confidence,
                            "total_confidence": total_confidence,
                            "recent_history": self.recent_transcriptions[-3:]  # Last 3 for context
                        }
                    )
                    return True
                else:
                    self.logger.info(f"Emergency phrase detected but confidence too low: {total_confidence:.2f}")

        return False

    def check_contextual_emergency(self, session_id: str) -> bool:
        """
        Check for emergency patterns across recent transcriptions
        Detects things like repeated "stop" commands or escalating urgency
        """
        if len(self.recent_transcriptions) < 2:
            return False

        recent_texts = [t["text"].lower() for t in self.recent_transcriptions[-3:]]

        # Check for repeated emergency-adjacent words
        emergency_words = ["stop", "halt", "abort", "quit", "cancel", "kill"]
        word_counts = {}

        for text in recent_texts:
            for word in emergency_words:
                if word in text:
                    word_counts[word] = word_counts.get(word, 0) + 1

        # If multiple recent uses of emergency words, trigger stop
        total_emergency_words = sum(word_counts.values())
        if total_emergency_words >= 3:
            self.logger.warning(f"Contextual emergency pattern detected: {word_counts}")

            self.emergency_system._trigger_emergency_stop(
                trigger_type=EmergencyTrigger.VOICE_COMMAND,
                trigger_source="voice_context_analysis",
                description="Repeated emergency words detected in voice input",
                session_id=session_id,
                context={
                    "pattern_type": "repeated_emergency_words",
                    "word_counts": word_counts,
                    "recent_transcriptions": recent_texts,
                    "trigger_threshold": total_emergency_words
                }
            )
            return True

        return False

    def get_detection_stats(self) -> Dict[str, Any]:
        """Get voice emergency detection statistics"""
        return {
            "phrases_monitored": len(self.emergency_phrases),
            "recent_transcriptions": len(self.recent_transcriptions),
            "last_detection": self.recent_transcriptions[-1] if self.recent_transcriptions else None
        }


def integrate_with_voice_interface():
    """
    Integration example with existing voice interface
    Shows how to connect the emergency system with voice processing
    """

    # Initialize emergency system
    emergency_system = MultiChannelEmergencyStop()
    voice_detector = VoiceEmergencyDetector(emergency_system)

    def enhanced_voice_callback(transcribed_text: str, confidence: float, session_id: str):
        """Enhanced voice callback that includes emergency detection"""

        # First check for emergency phrases
        emergency_triggered = voice_detector.process_voice_input(
            transcribed_text, confidence, session_id
        )

        if emergency_triggered:
            return "Emergency stop activated."

        # Check contextual patterns
        contextual_emergency = voice_detector.check_contextual_emergency(session_id)

        if contextual_emergency:
            return "Emergency stop activated due to repeated stop commands."

        # Continue with normal voice processing
        return process_normal_voice_command(transcribed_text, session_id)

    def process_normal_voice_command(text: str, session_id: str) -> str:
        """Placeholder for normal voice command processing"""
        return f"Processed: {text}"

    return enhanced_voice_callback


if __name__ == "__main__":
    # Setup logging for testing
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Test basic emergency system
    test_emergency_system()

    print("\n" + "="*60)
    print("Testing Voice Emergency Detection...")

    # Test voice emergency detection
    emergency_system = MultiChannelEmergencyStop("test_voice_emergency.db")
    voice_detector = VoiceEmergencyDetector(emergency_system)

    # Test various voice inputs
    test_inputs = [
        ("Please help me with something", 0.9, "test_session"),
        ("emergency stop right now", 0.95, "test_session"),
        ("halt penny immediately", 0.9, "test_session"),
        ("stop stop stop", 0.8, "test_session"),  # Should trigger contextual detection
    ]

    for text, confidence, session_id in test_inputs:
        print(f"\nTesting: '{text}' (confidence: {confidence})")
        result = voice_detector.process_voice_input(text, confidence, session_id)
        print(f"Emergency triggered: {result}")

        if not result:
            contextual = voice_detector.check_contextual_emergency(session_id)
            print(f"Contextual emergency: {contextual}")

    # Show stats
    stats = voice_detector.get_detection_stats()
    print(f"\nDetection stats: {stats}")

    print("\n✅ Voice emergency detection testing completed!")