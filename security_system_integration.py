#!/usr/bin/env python3
"""
Security System Integration
Part of Phase A3: Enhanced Security Logging

Integrates enhanced logging with existing security components:
- Command Whitelist System integration
- Emergency Stop System integration
- Security Violation Handler integration
- Real-time event correlation
- Automated response triggers
"""

import logging
import threading
import time
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable

try:
    from enhanced_security_logging import (
        EnhancedSecurityLogger, SecurityEventType, SecuritySeverity,
        LogRetentionPolicy
    )
    from command_whitelist_system import (
        CommandWhitelistSystem, PermissionLevel, PermissionCheck
    )
    from multi_channel_emergency_stop import (
        MultiChannelEmergencyStop, EmergencyTrigger, EmergencyState
    )
    from security_violation_handler import (
        SecurityViolationHandler, ViolationType
    )
except ImportError as e:
    print(f"Warning: Could not import security components: {e}")


class SecurityEventCorrelator:
    """Correlates security events across different systems"""

    def __init__(self):
        self.event_sequences = []
        self.correlation_rules = {}
        self.max_sequence_length = 100

        self._load_correlation_rules()

    def _load_correlation_rules(self):
        """Load event correlation rules"""
        self.correlation_rules = {
            "failed_auth_sequence": {
                "pattern": ["access_denied", "access_denied", "access_denied"],
                "time_window_seconds": 300,
                "response": "escalate_security"
            },
            "emergency_escalation": {
                "pattern": ["security_violation", "emergency_triggered"],
                "time_window_seconds": 60,
                "response": "investigate_cause"
            },
            "privilege_escalation_attempt": {
                "pattern": ["access_denied", "privilege_escalation", "access_denied"],
                "time_window_seconds": 120,
                "response": "security_alert"
            },
            "data_access_anomaly": {
                "pattern": ["data_access", "data_access", "data_export"],
                "time_window_seconds": 600,
                "response": "monitor_closely"
            }
        }

    def add_event(self, event_type: str, session_id: str, context: Dict[str, Any]) -> Optional[str]:
        """Add event and check for correlations"""
        event_data = {
            "event_type": event_type,
            "session_id": session_id,
            "timestamp": datetime.now(),
            "context": context
        }

        self.event_sequences.append(event_data)

        # Maintain sequence size
        if len(self.event_sequences) > self.max_sequence_length:
            self.event_sequences.pop(0)

        # Check for correlations
        return self._check_correlations()

    def _check_correlations(self) -> Optional[str]:
        """Check if recent events match correlation patterns"""
        for rule_name, rule in self.correlation_rules.items():
            if self._matches_pattern(rule["pattern"], rule["time_window_seconds"]):
                return rule_name
        return None

    def _matches_pattern(self, pattern: List[str], time_window_seconds: int) -> bool:
        """Check if recent events match a specific pattern"""
        if len(self.event_sequences) < len(pattern):
            return False

        # Check recent events in reverse order
        recent_events = self.event_sequences[-len(pattern):]
        cutoff_time = datetime.now().timestamp() - time_window_seconds

        # Check if all events are within time window
        if any(event["timestamp"].timestamp() < cutoff_time for event in recent_events):
            return False

        # Check if pattern matches
        for i, required_type in enumerate(pattern):
            if recent_events[i]["event_type"] != required_type:
                return False

        return True


class IntegratedSecuritySystem:
    """
    Integrated security system that coordinates all security components
    with enhanced logging and real-time analysis
    """

    def __init__(self,
                 whitelist_db: str = "command_whitelist.db",
                 emergency_db: str = "emergency_system.db",
                 logging_db: str = "enhanced_security.db"):

        self.logger = logging.getLogger("integrated_security")

        # Initialize core components
        self.enhanced_logger = EnhancedSecurityLogger(logging_db)
        self.command_whitelist = CommandWhitelistSystem(whitelist_db)
        self.emergency_stop = MultiChannelEmergencyStop(emergency_db)
        self.violation_handler = SecurityViolationHandler("violations.db")

        # Event correlation
        self.correlator = SecurityEventCorrelator()

        # Integration state
        self.active_sessions = {}
        self.response_handlers = {}

        # Setup integrations
        self._setup_integrations()

        self.logger.info("Integrated Security System initialized")

    def _setup_integrations(self):
        """Setup integrations between security components"""

        # Register event callbacks
        self.enhanced_logger.register_event_callback(self._handle_security_event)
        self.emergency_stop.register_emergency_callback(self._handle_emergency_event)

        # Setup automated response handlers
        self._setup_response_handlers()

        # Patch existing systems to log events
        self._patch_command_whitelist()
        self._patch_emergency_stop()
        self._patch_violation_handler()

    def _setup_response_handlers(self):
        """Setup automated response handlers for correlated events"""
        self.response_handlers = {
            "failed_auth_sequence": self._handle_failed_auth_sequence,
            "emergency_escalation": self._handle_emergency_escalation,
            "privilege_escalation_attempt": self._handle_privilege_escalation,
            "data_access_anomaly": self._handle_data_access_anomaly
        }

    def _patch_command_whitelist(self):
        """Patch command whitelist to emit security events"""
        original_check_permission = self.command_whitelist.check_permission

        def enhanced_check_permission(operation_request: str, parameters: Dict[str, Any] = None) -> PermissionCheck:
            # Call original method
            result = original_check_permission(operation_request, parameters)

            # Log security event
            event_type = SecurityEventType.ACCESS_GRANTED if result.allowed else SecurityEventType.ACCESS_DENIED
            severity = SecuritySeverity.INFO if result.allowed else SecuritySeverity.WARNING

            event_id = self.enhanced_logger.log_security_event(
                event_type=event_type,
                severity=severity,
                description=f"Permission check: {operation_request}",
                source_component="command_whitelist",
                source_function="check_permission",
                user_id=getattr(self.command_whitelist, 'current_user_id', None),
                session_id=getattr(self.command_whitelist, 'current_session_id', None),
                operation=operation_request,
                resource=result.operation,
                parameters=parameters or {},
                context={
                    "permission_level": result.user_permission.value if result.user_permission else None,
                    "required_permission": result.required_permission.value if result.required_permission else None,
                    "risk_level": result.risk_level.value if result.risk_level else None
                },
                decision="allowed" if result.allowed else "denied",
                reason=result.reason,
                alternatives_suggested=result.alternative_suggestions
            )

            # Check for correlations
            correlation = self.correlator.add_event(
                event_type.value,
                getattr(self.command_whitelist, 'current_session_id', 'unknown'),
                {"operation": operation_request, "allowed": result.allowed}
            )

            if correlation:
                self._handle_correlation(correlation, event_id)

            return result

        # Replace method
        self.command_whitelist.check_permission = enhanced_check_permission

    def _patch_emergency_stop(self):
        """Patch emergency stop to emit security events"""
        original_trigger = self.emergency_stop._trigger_emergency_stop

        def enhanced_trigger_emergency_stop(trigger_type, trigger_source, description, session_id, context):
            # Call original method
            result = original_trigger(trigger_type, trigger_source, description, session_id, context)

            # Log security event
            event_id = self.enhanced_logger.log_security_event(
                event_type=SecurityEventType.EMERGENCY_TRIGGERED,
                severity=SecuritySeverity.CRITICAL,
                description=f"Emergency stop: {description}",
                source_component="emergency_stop",
                source_function="trigger_emergency_stop",
                session_id=session_id,
                operation="emergency_stop",
                context=context or {},
                decision="emergency_stop",
                reason=description
            )

            # Check for correlations
            correlation = self.correlator.add_event(
                SecurityEventType.EMERGENCY_TRIGGERED.value,
                session_id,
                {"trigger": trigger_type.value if hasattr(trigger_type, 'value') else str(trigger_type)}
            )

            if correlation:
                self._handle_correlation(correlation, event_id)

            return result

        # Replace method
        self.emergency_stop._trigger_emergency_stop = enhanced_trigger_emergency_stop

    def _patch_violation_handler(self):
        """Patch violation handler to emit security events"""
        if hasattr(self.violation_handler, 'handle_permission_violation'):
            original_handle = self.violation_handler.handle_permission_violation

            def enhanced_handle_violation(permission_check, session_id, context=None):
                # Call original method
                result = original_handle(permission_check, session_id, context)

                # Log security event
                event_id = self.enhanced_logger.log_security_event(
                    event_type=SecurityEventType.SECURITY_VIOLATION,
                    severity=SecuritySeverity.WARNING,
                    description=f"Security violation: {permission_check.reason}",
                    source_component="violation_handler",
                    source_function="handle_permission_violation",
                    session_id=session_id,
                    operation=permission_check.operation,
                    context=context or {},
                    decision="violation_handled",
                    reason=permission_check.reason
                )

                # Check for correlations
                correlation = self.correlator.add_event(
                    SecurityEventType.SECURITY_VIOLATION.value,
                    session_id,
                    {"violation_type": "permission_violation", "operation": permission_check.operation}
                )

                if correlation:
                    self._handle_correlation(correlation, event_id)

                return result

            # Replace method
            self.violation_handler.handle_permission_violation = enhanced_handle_violation

    def _handle_security_event(self, event):
        """Handle security events from enhanced logger"""
        # Update session tracking
        if event.session_id:
            self.active_sessions[event.session_id] = {
                "last_activity": datetime.now(),
                "risk_score": event.risk_score,
                "event_count": self.active_sessions.get(event.session_id, {}).get("event_count", 0) + 1
            }

        # Trigger automated responses based on event severity
        if event.severity >= SecuritySeverity.CRITICAL:
            self._handle_critical_event(event)

    def _handle_emergency_event(self, emergency_event):
        """Handle emergency events from emergency stop system"""
        self.enhanced_logger.log_security_event(
            event_type=SecurityEventType.EMERGENCY_TRIGGERED,
            severity=SecuritySeverity.CRITICAL,
            description=f"Emergency event: {emergency_event.description}",
            source_component="emergency_stop",
            source_function="emergency_callback",
            session_id=emergency_event.session_id,
            context=emergency_event.context,
            decision="emergency_handled"
        )

    def _handle_correlation(self, correlation_name: str, triggering_event_id: str):
        """Handle detected event correlations"""
        self.logger.warning(f"Security correlation detected: {correlation_name}")

        # Log correlation event
        self.enhanced_logger.log_security_event(
            event_type=SecurityEventType.PATTERN_IDENTIFIED,
            severity=SecuritySeverity.WARNING,
            description=f"Security pattern detected: {correlation_name}",
            source_component="event_correlator",
            source_function="correlation_analysis",
            context={"correlation_type": correlation_name, "triggering_event": triggering_event_id},
            parent_event_id=triggering_event_id
        )

        # Execute automated response
        if correlation_name in self.response_handlers:
            try:
                self.response_handlers[correlation_name](triggering_event_id)
            except Exception as e:
                self.logger.error(f"Automated response failed for {correlation_name}: {e}")

    def _handle_critical_event(self, event):
        """Handle critical security events"""
        self.logger.critical(f"Critical security event: {event.description}")

        # Escalate based on event type
        if event.event_type == SecurityEventType.EMERGENCY_TRIGGERED:
            self._escalate_emergency(event)
        elif event.event_type == SecurityEventType.THREAT_DETECTED:
            self._escalate_threat(event)

    def _handle_failed_auth_sequence(self, triggering_event_id: str):
        """Handle failed authentication sequence"""
        self.logger.warning("Failed authentication sequence detected - implementing rate limiting")

        # Could implement session rate limiting here
        self.enhanced_logger.log_security_event(
            event_type=SecurityEventType.SUSPICIOUS_ACTIVITY,
            severity=SecuritySeverity.WARNING,
            description="Failed authentication sequence - rate limiting applied",
            source_component="automated_response",
            source_function="handle_failed_auth_sequence",
            parent_event_id=triggering_event_id
        )

    def _handle_emergency_escalation(self, triggering_event_id: str):
        """Handle emergency escalation pattern"""
        self.logger.critical("Emergency escalation pattern detected - investigating")

        self.enhanced_logger.log_security_event(
            event_type=SecurityEventType.ANOMALY_DETECTED,
            severity=SecuritySeverity.CRITICAL,
            description="Emergency escalation pattern requires investigation",
            source_component="automated_response",
            source_function="handle_emergency_escalation",
            parent_event_id=triggering_event_id
        )

    def _handle_privilege_escalation(self, triggering_event_id: str):
        """Handle privilege escalation attempt"""
        self.logger.warning("Privilege escalation attempt detected")

        self.enhanced_logger.log_security_event(
            event_type=SecurityEventType.PRIVILEGE_ESCALATION,
            severity=SecuritySeverity.ERROR,
            description="Privilege escalation attempt detected and blocked",
            source_component="automated_response",
            source_function="handle_privilege_escalation",
            parent_event_id=triggering_event_id
        )

    def _handle_data_access_anomaly(self, triggering_event_id: str):
        """Handle data access anomaly"""
        self.logger.warning("Data access anomaly detected - monitoring closely")

        self.enhanced_logger.log_security_event(
            event_type=SecurityEventType.ANOMALY_DETECTED,
            severity=SecuritySeverity.WARNING,
            description="Data access anomaly detected - enhanced monitoring active",
            source_component="automated_response",
            source_function="handle_data_access_anomaly",
            parent_event_id=triggering_event_id
        )

    def _escalate_emergency(self, event):
        """Escalate emergency events"""
        # Could trigger additional emergency responses
        pass

    def _escalate_threat(self, event):
        """Escalate threat events"""
        # Could trigger threat response procedures
        pass

    def get_security_status(self) -> Dict[str, Any]:
        """Get comprehensive security status"""
        # Get analytics from enhanced logger
        analytics = self.enhanced_logger.get_security_analytics("24h")

        # Get emergency system status
        emergency_status = self.emergency_stop.get_emergency_status()

        # Get active sessions
        active_session_count = len([
            s for s in self.active_sessions.values()
            if (datetime.now() - s["last_activity"]).total_seconds() < 3600  # Active in last hour
        ])

        return {
            "timestamp": datetime.now().isoformat(),
            "overall_status": "NORMAL" if emergency_status["state"] == "normal" else emergency_status["state"].upper(),
            "security_events": analytics,
            "emergency_system": emergency_status,
            "active_sessions": active_session_count,
            "correlation_patterns": len(self.correlator.correlation_rules),
            "performance_metrics": analytics.get("performance_metrics", {})
        }

    def generate_security_report(self, time_period: str = "24h") -> Dict[str, Any]:
        """Generate comprehensive security report"""
        from security_log_analyzer import SecurityLogAnalyzer

        analyzer = SecurityLogAnalyzer(self.enhanced_logger.database_path)
        report = analyzer.generate_comprehensive_report(time_period)

        # Add integration-specific information
        integration_info = {
            "integration_status": {
                "command_whitelist": "active",
                "emergency_stop": "active",
                "violation_handler": "active",
                "event_correlation": "active"
            },
            "active_sessions": len(self.active_sessions),
            "correlation_rules": len(self.correlator.correlation_rules)
        }

        report_dict = report.__dict__.copy()
        report_dict["integration_info"] = integration_info

        return report_dict

    def stop(self):
        """Stop integrated security system"""
        self.enhanced_logger.stop()
        self.emergency_stop.stop()
        self.logger.info("Integrated Security System stopped")


def test_integrated_security_system():
    """Test the integrated security system"""
    print("Testing Integrated Security System...")

    # Create integrated system
    security_system = IntegratedSecuritySystem(
        whitelist_db="test_whitelist.db",
        emergency_db="test_emergency.db",
        logging_db="test_enhanced_security.db"
    )

    # Test permission checks
    print("\n1. Testing permission checks...")
    result1 = security_system.command_whitelist.check_permission("file_read config.json")
    print(f"File read allowed: {result1.allowed}")

    result2 = security_system.command_whitelist.check_permission("../etc/passwd")
    print(f"Path traversal blocked: {not result2.allowed}")

    # Test multiple denied access (should trigger correlation)
    print("\n2. Testing failed access sequence...")
    for i in range(3):
        security_system.command_whitelist.check_permission("admin_command")

    # Wait for event processing
    time.sleep(2)

    # Test emergency trigger
    print("\n3. Testing emergency trigger...")
    security_system.emergency_stop._trigger_emergency_stop(
        EmergencyTrigger.USER_MANUAL,
        "test",
        "Test emergency",
        "test_session",
        {"test": True}
    )

    # Wait for event processing
    time.sleep(2)

    # Get security status
    print("\n4. Getting security status...")
    status = security_system.get_security_status()
    print(f"Overall status: {status['overall_status']}")
    print(f"Total events: {status['security_events']['total_events']}")
    print(f"Active sessions: {status['active_sessions']}")

    # Generate report
    print("\n5. Generating security report...")
    report = security_system.generate_security_report("1h")
    print(f"Report ID: {report['report_id']}")
    print(f"Total events in report: {report['total_events']}")

    # Cleanup
    security_system.stop()

    print("\n✅ Integrated Security System testing completed!")


if __name__ == "__main__":
    # Setup logging for testing
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    test_integrated_security_system()