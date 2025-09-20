#!/usr/bin/env python3
"""
Security Violation Handler for Penny's Agentic AI
Handles whitelist violations, security incidents, and appropriate responses
"""

import json
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import logging

from command_whitelist_system import PermissionCheck, SecurityRisk, PermissionLevel
from security_ethics_foundation import EthicalViolation, EthicalBoundary

class ViolationType(Enum):
    """Types of security violations"""
    PERMISSION_DENIED = "permission_denied"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    PARAMETER_VIOLATION = "parameter_violation"
    ETHICAL_BOUNDARY = "ethical_boundary"
    UNKNOWN_OPERATION = "unknown_operation"
    SUSPICIOUS_PATTERN = "suspicious_pattern"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    SYSTEM_INTEGRITY = "system_integrity"

class ResponseAction(Enum):
    """Possible responses to violations"""
    DENY_WITH_EXPLANATION = "deny_with_explanation"
    SUGGEST_ALTERNATIVE = "suggest_alternative"
    REQUEST_CLARIFICATION = "request_clarification"
    ESCALATE_TO_HUMAN = "escalate_to_human"
    TEMPORARY_RESTRICTION = "temporary_restriction"
    SESSION_TERMINATION = "session_termination"
    EMERGENCY_LOCKDOWN = "emergency_lockdown"
    LOG_AND_CONTINUE = "log_and_continue"

class ViolationSeverity(Enum):
    """Severity levels for violations"""
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class SecurityViolation:
    """Record of a security violation"""
    violation_type: ViolationType
    severity: ViolationSeverity
    operation_requested: str
    parameters: Dict[str, Any]
    user_permission: PermissionLevel
    timestamp: datetime
    description: str
    context: Dict[str, Any]
    session_id: str

@dataclass
class ViolationResponse:
    """Response to a security violation"""
    action: ResponseAction
    message: str
    suggested_alternatives: List[str]
    restrictions_applied: List[str]
    escalation_required: bool
    follow_up_actions: List[str]

class SecurityViolationHandler:
    """Handles security violations with appropriate responses"""

    def __init__(self, db_path: str = "security_violations.db"):
        self.db_path = db_path
        self.violation_history: List[SecurityViolation] = []
        self.active_restrictions: Dict[str, Dict[str, Any]] = {}
        self.escalation_thresholds = self._load_escalation_thresholds()

        # Initialize logging
        logging.basicConfig(
            filename='penny_security_violations.log',
            level=logging.WARNING,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

        # Initialize database
        self._init_database()

    def _init_database(self):
        """Initialize database for violation tracking"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Violations table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS security_violations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                violation_type TEXT,
                severity TEXT,
                operation_requested TEXT,
                parameters TEXT,
                user_permission TEXT,
                timestamp TEXT,
                description TEXT,
                context TEXT,
                session_id TEXT,
                response_action TEXT,
                response_message TEXT
            )
        """)

        # Active restrictions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS active_restrictions (
                session_id TEXT,
                restriction_type TEXT,
                start_time TEXT,
                end_time TEXT,
                details TEXT,
                PRIMARY KEY (session_id, restriction_type)
            )
        """)

        # Escalation log
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS escalation_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                violation_id INTEGER,
                escalation_reason TEXT,
                escalation_level TEXT,
                human_notified BOOLEAN,
                resolution TEXT,
                resolved_at TEXT
            )
        """)

        conn.commit()
        conn.close()

    def _load_escalation_thresholds(self) -> Dict[str, Any]:
        """Load escalation thresholds and rules"""
        return {
            "rate_limits": {
                "violations_per_hour": 5,
                "violations_per_day": 20,
                "privilege_escalation_attempts": 3
            },
            "severity_escalation": {
                ViolationSeverity.CRITICAL: 1,  # Immediate escalation
                ViolationSeverity.HIGH: 3,      # After 3 violations
                ViolationSeverity.MEDIUM: 10,   # After 10 violations
                ViolationSeverity.LOW: 50       # After 50 violations
            },
            "pattern_detection": {
                "suspicious_patterns": [
                    "repeated_permission_denied",
                    "parameter_probing",
                    "privilege_escalation_sequence",
                    "rapid_fire_requests"
                ]
            }
        }

    def handle_permission_violation(self, permission_check: PermissionCheck,
                                  session_id: str, context: Dict[str, Any] = None) -> ViolationResponse:
        """Handle permission-based violations"""

        context = context or {}

        # Determine violation type and severity
        violation_type = self._classify_permission_violation(permission_check)
        severity = self._assess_violation_severity(permission_check, context)

        # Create violation record
        violation = SecurityViolation(
            violation_type=violation_type,
            severity=severity,
            operation_requested=permission_check.operation,
            parameters=context.get('parameters', {}),
            user_permission=permission_check.user_permission,
            timestamp=datetime.now(),
            description=permission_check.reason,
            context=context,
            session_id=session_id
        )

        # Log violation
        self._log_violation(violation)

        # Generate appropriate response
        response = self._generate_violation_response(violation, permission_check)

        # Check for escalation
        if self._should_escalate(violation):
            response.escalation_required = True
            response.follow_up_actions.append("escalate_to_human")
            self._escalate_violation(violation)

        # Apply any restrictions
        self._apply_restrictions(violation, response)

        return response

    def handle_ethical_violation(self, ethical_violation: EthicalViolation,
                                operation: str, session_id: str,
                                context: Dict[str, Any] = None) -> ViolationResponse:
        """Handle ethical boundary violations"""

        context = context or {}

        # Map ethical violation to security violation
        violation = SecurityViolation(
            violation_type=ViolationType.ETHICAL_BOUNDARY,
            severity=self._map_ethical_severity(ethical_violation.severity),
            operation_requested=operation,
            parameters=context.get('parameters', {}),
            user_permission=PermissionLevel.GUEST,  # Assume lowest for ethical violations
            timestamp=datetime.now(),
            description=f"Ethical boundary violation: {ethical_violation.description}",
            context={"ethical_boundary": ethical_violation.boundary_type.value, **context},
            session_id=session_id
        )

        # Log violation
        self._log_violation(violation)

        # Generate firm but respectful response
        response = ViolationResponse(
            action=ResponseAction.DENY_WITH_EXPLANATION,
            message=self._generate_ethical_refusal(ethical_violation),
            suggested_alternatives=self._suggest_ethical_alternatives(ethical_violation),
            restrictions_applied=[],
            escalation_required=ethical_violation.severity == "critical",
            follow_up_actions=[]
        )

        # Critical ethical violations require immediate escalation
        if ethical_violation.severity == "critical":
            response.follow_up_actions.append("emergency_lockdown")
            self._escalate_violation(violation)

        return response

    def handle_suspicious_pattern(self, pattern_type: str, details: Dict[str, Any],
                                session_id: str) -> ViolationResponse:
        """Handle detected suspicious patterns"""

        violation = SecurityViolation(
            violation_type=ViolationType.SUSPICIOUS_PATTERN,
            severity=ViolationSeverity.MEDIUM,
            operation_requested=details.get('last_operation', 'unknown'),
            parameters=details.get('parameters', {}),
            user_permission=PermissionLevel.GUEST,
            timestamp=datetime.now(),
            description=f"Suspicious pattern detected: {pattern_type}",
            context={"pattern_type": pattern_type, **details},
            session_id=session_id
        )

        self._log_violation(violation)

        # Generate appropriate response based on pattern
        if pattern_type == "rapid_fire_requests":
            response = ViolationResponse(
                action=ResponseAction.TEMPORARY_RESTRICTION,
                message="I've noticed a rapid sequence of requests. Please slow down to ensure I can process each request properly.",
                suggested_alternatives=["Wait a moment between requests", "Be more specific about what you need"],
                restrictions_applied=["rate_limit_enhanced"],
                escalation_required=False,
                follow_up_actions=["apply_temporary_rate_limit"]
            )
        elif pattern_type == "privilege_escalation_sequence":
            response = ViolationResponse(
                action=ResponseAction.ESCALATE_TO_HUMAN,
                message="I've detected multiple attempts to access restricted operations. For security, I need to verify your authorization.",
                suggested_alternatives=["Provide proper authentication", "Use available lower-privilege operations"],
                restrictions_applied=["privilege_verification_required"],
                escalation_required=True,
                follow_up_actions=["escalate_to_human", "require_authentication"]
            )
        else:
            response = ViolationResponse(
                action=ResponseAction.LOG_AND_CONTINUE,
                message="I'm monitoring this session for security. Please continue with your requests.",
                suggested_alternatives=[],
                restrictions_applied=[],
                escalation_required=False,
                follow_up_actions=["enhanced_monitoring"]
            )

        return response

    def _classify_permission_violation(self, permission_check: PermissionCheck) -> ViolationType:
        """Classify the type of permission violation"""

        if "rate limit" in permission_check.reason.lower():
            return ViolationType.RATE_LIMIT_EXCEEDED
        elif "parameter" in permission_check.reason.lower():
            return ViolationType.PARAMETER_VIOLATION
        elif "unknown" in permission_check.reason.lower():
            return ViolationType.UNKNOWN_OPERATION
        elif "permission" in permission_check.reason.lower():
            return ViolationType.PERMISSION_DENIED
        else:
            return ViolationType.SYSTEM_INTEGRITY

    def _assess_violation_severity(self, permission_check: PermissionCheck,
                                 context: Dict[str, Any]) -> ViolationSeverity:
        """Assess the severity of a violation"""

        # Base severity on security risk
        if permission_check.risk_level == SecurityRisk.CRITICAL:
            return ViolationSeverity.CRITICAL
        elif permission_check.risk_level == SecurityRisk.HIGH:
            return ViolationSeverity.HIGH
        elif permission_check.risk_level == SecurityRisk.MEDIUM:
            return ViolationSeverity.MEDIUM
        elif permission_check.risk_level == SecurityRisk.LOW:
            return ViolationSeverity.LOW
        else:
            return ViolationSeverity.INFO

    def _map_ethical_severity(self, ethical_severity: str) -> ViolationSeverity:
        """Map ethical violation severity to security violation severity"""
        mapping = {
            "critical": ViolationSeverity.CRITICAL,
            "high": ViolationSeverity.HIGH,
            "medium": ViolationSeverity.MEDIUM,
            "low": ViolationSeverity.LOW
        }
        return mapping.get(ethical_severity, ViolationSeverity.MEDIUM)

    def _generate_violation_response(self, violation: SecurityViolation,
                                   permission_check: PermissionCheck) -> ViolationResponse:
        """Generate appropriate response to violation"""

        if violation.severity == ViolationSeverity.CRITICAL:
            return ViolationResponse(
                action=ResponseAction.SESSION_TERMINATION,
                message="Critical security violation detected. Session terminated for safety.",
                suggested_alternatives=[],
                restrictions_applied=["session_terminated"],
                escalation_required=True,
                follow_up_actions=["terminate_session", "escalate_to_human"]
            )

        elif violation.severity == ViolationSeverity.HIGH:
            return ViolationResponse(
                action=ResponseAction.ESCALATE_TO_HUMAN,
                message=f"I cannot perform '{violation.operation_requested}' due to security restrictions. {permission_check.reason}",
                suggested_alternatives=permission_check.alternative_suggestions,
                restrictions_applied=["enhanced_monitoring"],
                escalation_required=True,
                follow_up_actions=["escalate_to_human"]
            )

        elif violation.violation_type == ViolationType.RATE_LIMIT_EXCEEDED:
            return ViolationResponse(
                action=ResponseAction.TEMPORARY_RESTRICTION,
                message="You've made too many requests too quickly. Please wait a moment before trying again.",
                suggested_alternatives=["Wait 60 seconds", "Reduce request frequency"],
                restrictions_applied=["temporary_rate_limit"],
                escalation_required=False,
                follow_up_actions=["apply_rate_limit"]
            )

        elif violation.violation_type == ViolationType.UNKNOWN_OPERATION:
            return ViolationResponse(
                action=ResponseAction.REQUEST_CLARIFICATION,
                message=f"I don't recognize the operation '{violation.operation_requested}'. Could you clarify what you'd like me to do?",
                suggested_alternatives=self._suggest_known_operations(),
                restrictions_applied=[],
                escalation_required=False,
                follow_up_actions=["provide_help"]
            )

        else:
            return ViolationResponse(
                action=ResponseAction.DENY_WITH_EXPLANATION,
                message=f"I cannot perform '{violation.operation_requested}': {permission_check.reason}",
                suggested_alternatives=permission_check.alternative_suggestions,
                restrictions_applied=[],
                escalation_required=False,
                follow_up_actions=[]
            )

    def _generate_ethical_refusal(self, ethical_violation: EthicalViolation) -> str:
        """Generate respectful but firm ethical refusal"""

        base_messages = {
            EthicalBoundary.HUMAN_SAFETY: "I can't help with anything that could potentially harm people. That's a core principle I can't compromise on.",
            EthicalBoundary.DECEPTION: "I can't assist with deception or misleading others. Being honest and trustworthy is fundamental to who I am.",
            EthicalBoundary.PRIVACY: "I can't help with activities that would violate privacy or security. Respecting boundaries is important.",
            EthicalBoundary.ILLEGAL_ACTIVITY: "I can't assist with illegal activities. I'm designed to be helpful within legal boundaries.",
            EthicalBoundary.MANIPULATION: "I can't help with manipulation or taking advantage of others. That goes against my values.",
            EthicalBoundary.SYSTEM_INTEGRITY: "I can't help with actions that would compromise system security or integrity."
        }

        base_message = base_messages.get(ethical_violation.boundary_type,
                                       "I can't help with that request as it conflicts with my ethical guidelines.")

        if ethical_violation.severity == "critical":
            addendum = " This is a firm boundary I cannot cross under any circumstances."
        else:
            addendum = " I'd be happy to help you find an alternative approach that works within ethical guidelines."

        return base_message + addendum

    def _suggest_ethical_alternatives(self, ethical_violation: EthicalViolation) -> List[str]:
        """Suggest ethical alternatives"""

        alternatives = {
            EthicalBoundary.HUMAN_SAFETY: [
                "I can help with safety information instead",
                "Let me suggest resources for staying safe"
            ],
            EthicalBoundary.DECEPTION: [
                "I can help you communicate honestly and effectively",
                "Let me suggest ways to address your concerns directly"
            ],
            EthicalBoundary.PRIVACY: [
                "I can help with publicly available information",
                "Let me suggest privacy-respecting approaches"
            ],
            EthicalBoundary.ILLEGAL_ACTIVITY: [
                "I can provide information about legal alternatives",
                "Let me help you understand the legal framework"
            ]
        }

        return alternatives.get(ethical_violation.boundary_type, [
            "I can help you find an ethical approach to your goal"
        ])

    def _suggest_known_operations(self) -> List[str]:
        """Suggest known safe operations"""
        return [
            "Read files or documents",
            "List directory contents",
            "Check system status",
            "Analyze text or data",
            "Get help with available operations"
        ]

    def _should_escalate(self, violation: SecurityViolation) -> bool:
        """Determine if violation should be escalated"""

        # Always escalate critical violations
        if violation.severity == ViolationSeverity.CRITICAL:
            return True

        # Count recent violations of this type
        recent_violations = self._count_recent_violations(violation.session_id,
                                                        violation.violation_type,
                                                        hours=1)

        # Check escalation thresholds
        threshold = self.escalation_thresholds["severity_escalation"].get(
            violation.severity, 10
        )

        return recent_violations >= threshold

    def _count_recent_violations(self, session_id: str, violation_type: ViolationType,
                               hours: int = 1) -> int:
        """Count recent violations for escalation decisions"""

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        since_time = datetime.now() - timedelta(hours=hours)

        cursor.execute("""
            SELECT COUNT(*) FROM security_violations
            WHERE session_id = ? AND violation_type = ? AND timestamp > ?
        """, (session_id, violation_type.value, since_time.isoformat()))

        count = cursor.fetchone()[0]
        conn.close()

        return count

    def _escalate_violation(self, violation: SecurityViolation):
        """Escalate violation to human oversight"""

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO escalation_log
            (timestamp, violation_id, escalation_reason, escalation_level, human_notified)
            VALUES (?, ?, ?, ?, ?)
        """, (
            datetime.now().isoformat(),
            0,  # Would link to violation ID in production
            f"Severity: {violation.severity.value}, Pattern: {violation.violation_type.value}",
            "human_review",
            False  # Would trigger notification system
        ))

        conn.commit()
        conn.close()

        # Log critical escalation
        self.logger.critical(f"ESCALATION: {violation.violation_type.value} - {violation.description}")

    def _apply_restrictions(self, violation: SecurityViolation, response: ViolationResponse):
        """Apply temporary restrictions based on violation"""

        if not response.restrictions_applied:
            return

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        for restriction in response.restrictions_applied:
            end_time = datetime.now() + timedelta(minutes=self._get_restriction_duration(restriction))

            cursor.execute("""
                INSERT OR REPLACE INTO active_restrictions
                (session_id, restriction_type, start_time, end_time, details)
                VALUES (?, ?, ?, ?, ?)
            """, (
                violation.session_id,
                restriction,
                datetime.now().isoformat(),
                end_time.isoformat(),
                json.dumps({"violation_type": violation.violation_type.value})
            ))

        conn.commit()
        conn.close()

    def _get_restriction_duration(self, restriction_type: str) -> int:
        """Get duration in minutes for restriction type"""
        durations = {
            "temporary_rate_limit": 5,
            "enhanced_monitoring": 60,
            "privilege_verification_required": 120,
            "session_terminated": 0  # Permanent until manual reset
        }
        return durations.get(restriction_type, 10)

    def _log_violation(self, violation: SecurityViolation):
        """Log violation to database and file"""

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO security_violations
            (violation_type, severity, operation_requested, parameters, user_permission,
             timestamp, description, context, session_id, response_action, response_message)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            violation.violation_type.value,
            violation.severity.value,
            violation.operation_requested,
            json.dumps(violation.parameters),
            violation.user_permission.value,
            violation.timestamp.isoformat(),
            violation.description,
            json.dumps(violation.context),
            violation.session_id,
            "",  # Will be updated after response generation
            ""   # Will be updated after response generation
        ))

        conn.commit()
        conn.close()

        # File logging
        log_level = {
            ViolationSeverity.CRITICAL: logging.CRITICAL,
            ViolationSeverity.HIGH: logging.ERROR,
            ViolationSeverity.MEDIUM: logging.WARNING,
            ViolationSeverity.LOW: logging.INFO,
            ViolationSeverity.INFO: logging.INFO
        }[violation.severity]

        self.logger.log(log_level,
                       f"VIOLATION: {violation.violation_type.value} - {violation.operation_requested} - {violation.description}")

    def get_active_restrictions(self, session_id: str) -> List[Dict[str, Any]]:
        """Get active restrictions for a session"""

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        now = datetime.now().isoformat()

        cursor.execute("""
            SELECT restriction_type, start_time, end_time, details
            FROM active_restrictions
            WHERE session_id = ? AND end_time > ?
        """, (session_id, now))

        restrictions = []
        for row in cursor.fetchall():
            restrictions.append({
                "type": row[0],
                "start_time": row[1],
                "end_time": row[2],
                "details": json.loads(row[3]) if row[3] else {}
            })

        conn.close()
        return restrictions

    def get_violation_summary(self, session_id: str = None, hours: int = 24) -> Dict[str, Any]:
        """Get summary of violations"""

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        since_time = datetime.now() - timedelta(hours=hours)

        where_clause = "WHERE timestamp > ?"
        params = [since_time.isoformat()]

        if session_id:
            where_clause += " AND session_id = ?"
            params.append(session_id)

        cursor.execute(f"""
            SELECT violation_type, severity, COUNT(*) as count
            FROM security_violations
            {where_clause}
            GROUP BY violation_type, severity
        """, params)

        violations_by_type = {}
        for row in cursor.fetchall():
            violation_type, severity, count = row
            if violation_type not in violations_by_type:
                violations_by_type[violation_type] = {}
            violations_by_type[violation_type][severity] = count

        conn.close()

        return {
            "timeframe_hours": hours,
            "session_id": session_id,
            "violations_by_type": violations_by_type,
            "total_violations": sum(
                sum(severities.values()) for severities in violations_by_type.values()
            )
        }

def create_security_violation_handler(db_path: str = "security_violations.db") -> SecurityViolationHandler:
    """Factory function"""
    return SecurityViolationHandler(db_path)

if __name__ == "__main__":
    # Demo and testing
    print("🚨 Security Violation Handler Testing")
    print("=" * 60)

    handler = create_security_violation_handler("test_violations.db")

    # Simulate some violations
    from command_whitelist_system import PermissionCheck, SecurityRisk, PermissionLevel

    # Test permission violation
    permission_check = PermissionCheck(
        allowed=False,
        operation="system_modify",
        reason="Insufficient permission level. Required: authenticated, Current: guest",
        risk_level=SecurityRisk.CRITICAL,
        alternative_suggestions=["Try read-only operations", "Request proper authentication"],
        required_permission=PermissionLevel.AUTHENTICATED,
        user_permission=PermissionLevel.GUEST
    )

    response = handler.handle_permission_violation(permission_check, "test_session_001")
    print(f"Permission Violation Response:")
    print(f"   Action: {response.action.value}")
    print(f"   Message: {response.message}")
    print(f"   Escalation Required: {response.escalation_required}")
    print()

    # Test suspicious pattern
    pattern_response = handler.handle_suspicious_pattern(
        "rapid_fire_requests",
        {"request_count": 10, "time_window": 30},
        "test_session_001"
    )
    print(f"Suspicious Pattern Response:")
    print(f"   Action: {pattern_response.action.value}")
    print(f"   Message: {pattern_response.message}")
    print(f"   Restrictions: {pattern_response.restrictions_applied}")
    print()

    # Show violation summary
    summary = handler.get_violation_summary("test_session_001")
    print(f"Violation Summary:")
    print(f"   Total Violations: {summary['total_violations']}")
    print(f"   By Type: {summary['violations_by_type']}")

    # Clean up
    import os
    if os.path.exists("test_violations.db"):
        os.remove("test_violations.db")

    print("\n✅ Security Violation Handler testing completed!")