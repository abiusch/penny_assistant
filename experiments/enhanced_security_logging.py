#!/usr/bin/env python3
"""
Enhanced Security Logging System for Penny AI Assistant
Phase A3: Critical Security Foundations - Enhanced Security Logging

This system provides comprehensive security event logging with:
- Detailed trigger analysis logging
- Security event classification
- Structured log storage for analysis
- Log review tools and utilities
- Privacy-preserving audit trails
- Real-time security analytics
- Integration with existing security systems

Builds on Phase A1 (Command Whitelist) and Phase A2 (Emergency Stop) systems.
"""

import json
import sqlite3
import hashlib
import logging
import threading
import time
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Callable
from enum import Enum, IntEnum
from dataclasses import dataclass, asdict
from pathlib import Path
import uuid

# Import existing security components
try:
    from command_whitelist_system import CommandWhitelistSystem, PermissionLevel, SecurityRisk
    from multi_channel_emergency_stop import MultiChannelEmergencyStop, EmergencyTrigger, EmergencyState
    from security_violation_handler import SecurityViolationHandler, ViolationType
except ImportError as e:
    print(f"Warning: Could not import existing security components: {e}")


class SecurityEventType(Enum):
    """Enhanced security event classification"""
    # Access Control Events
    PERMISSION_CHECK = "permission_check"
    ACCESS_GRANTED = "access_granted"
    ACCESS_DENIED = "access_denied"
    PRIVILEGE_ESCALATION = "privilege_escalation"

    # Security Violations
    SECURITY_VIOLATION = "security_violation"
    POLICY_VIOLATION = "policy_violation"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"

    # Emergency Events
    EMERGENCY_TRIGGERED = "emergency_triggered"
    EMERGENCY_RESOLVED = "emergency_resolved"
    SYSTEM_LOCKDOWN = "system_lockdown"
    RECOVERY_INITIATED = "recovery_initiated"

    # Authentication & Authorization
    USER_AUTHENTICATION = "user_authentication"
    SESSION_CREATED = "session_created"
    SESSION_TERMINATED = "session_terminated"
    CREDENTIAL_VALIDATION = "credential_validation"

    # System Events
    SYSTEM_STARTUP = "system_startup"
    SYSTEM_SHUTDOWN = "system_shutdown"
    CONFIGURATION_CHANGE = "configuration_change"
    SECURITY_UPDATE = "security_update"

    # Data Protection
    DATA_ACCESS = "data_access"
    DATA_MODIFICATION = "data_modification"
    DATA_EXPORT = "data_export"
    PRIVACY_VIOLATION = "privacy_violation"

    # Monitoring & Analysis
    ANOMALY_DETECTED = "anomaly_detected"
    PATTERN_IDENTIFIED = "pattern_identified"
    THREAT_DETECTED = "threat_detected"
    FALSE_POSITIVE = "false_positive"


class SecuritySeverity(IntEnum):
    """Security event severity levels"""
    TRACE = 0      # Detailed execution traces
    DEBUG = 1      # Debug information
    INFO = 2       # General information
    NOTICE = 3     # Notable events
    WARNING = 4    # Warning conditions
    ERROR = 5      # Error conditions
    CRITICAL = 6   # Critical conditions
    ALERT = 7      # Action must be taken immediately
    EMERGENCY = 8  # System is unusable


class LogRetentionPolicy(Enum):
    """Log retention policies"""
    IMMEDIATE = "immediate"        # Delete immediately (for sensitive data)
    SHORT_TERM = "short_term"      # 24 hours
    MEDIUM_TERM = "medium_term"    # 7 days
    LONG_TERM = "long_term"        # 30 days
    PERMANENT = "permanent"        # Indefinite retention
    COMPLIANCE = "compliance"      # Regulatory compliance periods


@dataclass
class SecurityEvent:
    """Comprehensive security event structure"""
    event_id: str
    timestamp: str
    event_type: SecurityEventType
    severity: SecuritySeverity
    source_component: str
    source_function: str

    # Event Details
    description: str
    user_id: Optional[str]
    session_id: Optional[str]

    # Context Information
    operation: Optional[str]
    resource: Optional[str]
    parameters: Dict[str, Any]
    context: Dict[str, Any]

    # Security Analysis
    risk_score: float              # 0.0 - 1.0
    confidence_score: float        # 0.0 - 1.0
    threat_indicators: List[str]

    # Decision Information
    decision: Optional[str]        # allowed/denied/escalated
    reason: Optional[str]
    alternatives_suggested: List[str]

    # Privacy & Compliance
    contains_pii: bool
    retention_policy: LogRetentionPolicy
    anonymization_applied: bool

    # Correlation & Analysis
    correlation_id: Optional[str]
    parent_event_id: Optional[str]
    related_events: List[str]

    # Performance Metrics
    processing_time_ms: Optional[float]
    system_load: Optional[Dict[str, float]]


@dataclass
class SecurityPattern:
    """Security pattern for anomaly detection"""
    pattern_id: str
    pattern_type: str
    description: str
    indicators: List[str]
    threshold: float
    time_window_minutes: int
    severity: SecuritySeverity
    auto_response: Optional[str]


class PrivacyFilter:
    """Privacy-preserving filter for sensitive data"""

    def __init__(self):
        # PII patterns to detect and anonymize
        self.pii_patterns = {
            'email': re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
            'phone': re.compile(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'),
            'ssn': re.compile(r'\b\d{3}-?\d{2}-?\d{4}\b'),
            'credit_card': re.compile(r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b'),
            'api_key': re.compile(r'\b[A-Za-z0-9]{32,}\b'),
            'password': re.compile(r'password["\s]*[:=]["\s]*[^\s"]+', re.IGNORECASE),
            'token': re.compile(r'token["\s]*[:=]["\s]*[^\s"]+', re.IGNORECASE)
        }

        # Anonymization cache for consistency
        self.anonymization_cache = {}

    def anonymize_data(self, data: Any) -> tuple[Any, bool]:
        """
        Anonymize PII in data while maintaining utility
        Returns: (anonymized_data, contains_pii)
        """
        if isinstance(data, str):
            return self._anonymize_string(data)
        elif isinstance(data, dict):
            return self._anonymize_dict(data)
        elif isinstance(data, list):
            return self._anonymize_list(data)
        else:
            return data, False

    def _anonymize_string(self, text: str) -> tuple[str, bool]:
        """Anonymize PII in string"""
        anonymized = text
        contains_pii = False

        for pii_type, pattern in self.pii_patterns.items():
            matches = pattern.findall(text)
            for match in matches:
                if match not in self.anonymization_cache:
                    # Generate consistent anonymized value
                    hash_obj = hashlib.sha256(match.encode())
                    anon_value = f"[{pii_type.upper()}_{hash_obj.hexdigest()[:8]}]"
                    self.anonymization_cache[match] = anon_value

                anonymized = anonymized.replace(match, self.anonymization_cache[match])
                contains_pii = True

        return anonymized, contains_pii

    def _anonymize_dict(self, data: dict) -> tuple[dict, bool]:
        """Anonymize PII in dictionary"""
        anonymized = {}
        overall_pii = False

        for key, value in data.items():
            anon_value, has_pii = self.anonymize_data(value)
            anonymized[key] = anon_value
            overall_pii = overall_pii or has_pii

        return anonymized, overall_pii

    def _anonymize_list(self, data: list) -> tuple[list, bool]:
        """Anonymize PII in list"""
        anonymized = []
        overall_pii = False

        for item in data:
            anon_item, has_pii = self.anonymize_data(item)
            anonymized.append(anon_item)
            overall_pii = overall_pii or has_pii

        return anonymized, overall_pii


class SecurityAnalyzer:
    """Real-time security analysis and pattern detection"""

    def __init__(self):
        self.patterns = {}
        self.event_history = []
        self.max_history = 1000
        self.anomaly_threshold = 0.8

        # Load default security patterns
        self._load_default_patterns()

    def _load_default_patterns(self):
        """Load default security patterns for detection"""
        default_patterns = [
            SecurityPattern(
                pattern_id="rapid_failures",
                pattern_type="authentication",
                description="Rapid authentication failures",
                indicators=["access_denied", "permission_check"],
                threshold=5.0,
                time_window_minutes=5,
                severity=SecuritySeverity.WARNING,
                auto_response="rate_limit"
            ),
            SecurityPattern(
                pattern_id="privilege_escalation_attempt",
                pattern_type="authorization",
                description="Potential privilege escalation",
                indicators=["privilege_escalation", "access_denied"],
                threshold=3.0,
                time_window_minutes=10,
                severity=SecuritySeverity.CRITICAL,
                auto_response="alert"
            ),
            SecurityPattern(
                pattern_id="emergency_pattern",
                pattern_type="emergency",
                description="Repeated emergency triggers",
                indicators=["emergency_triggered", "system_lockdown"],
                threshold=2.0,
                time_window_minutes=30,
                severity=SecuritySeverity.ALERT,
                auto_response="investigate"
            ),
            SecurityPattern(
                pattern_id="data_exfiltration",
                pattern_type="data_protection",
                description="Potential data exfiltration",
                indicators=["data_export", "data_access"],
                threshold=10.0,
                time_window_minutes=15,
                severity=SecuritySeverity.CRITICAL,
                auto_response="block"
            )
        ]

        for pattern in default_patterns:
            self.patterns[pattern.pattern_id] = pattern

    def analyze_event(self, event: SecurityEvent) -> Dict[str, Any]:
        """
        Analyze security event for patterns and anomalies
        Returns analysis results with risk assessment
        """
        analysis = {
            "risk_score": self._calculate_risk_score(event),
            "confidence_score": self._calculate_confidence_score(event),
            "threat_indicators": self._identify_threat_indicators(event),
            "pattern_matches": self._check_patterns(event),
            "anomaly_score": self._calculate_anomaly_score(event),
            "recommendations": self._generate_recommendations(event)
        }

        # Update event history for pattern detection
        self.event_history.append({
            "timestamp": event.timestamp,
            "event_type": event.event_type.value,
            "severity": event.severity.value,
            "risk_score": analysis["risk_score"]
        })

        # Maintain history size
        if len(self.event_history) > self.max_history:
            self.event_history.pop(0)

        return analysis

    def _calculate_risk_score(self, event: SecurityEvent) -> float:
        """Calculate risk score based on event characteristics"""
        base_score = 0.0

        # Severity contribution
        base_score += event.severity.value / 8.0 * 0.4

        # Event type risk
        high_risk_events = {
            SecurityEventType.SECURITY_VIOLATION: 0.3,
            SecurityEventType.EMERGENCY_TRIGGERED: 0.4,
            SecurityEventType.PRIVILEGE_ESCALATION: 0.5,
            SecurityEventType.THREAT_DETECTED: 0.6,
            SecurityEventType.PRIVACY_VIOLATION: 0.4
        }
        base_score += high_risk_events.get(event.event_type, 0.1)

        # Context risk factors
        if event.contains_pii:
            base_score += 0.2

        if "admin" in str(event.parameters).lower():
            base_score += 0.1

        return min(base_score, 1.0)

    def _calculate_confidence_score(self, event: SecurityEvent) -> float:
        """Calculate confidence in the security assessment"""
        confidence = 0.5  # Base confidence

        # More details increase confidence
        if event.parameters:
            confidence += 0.1
        if event.context:
            confidence += 0.1
        if event.reason:
            confidence += 0.1

        # Well-known event types increase confidence
        if event.event_type in [SecurityEventType.ACCESS_DENIED, SecurityEventType.PERMISSION_CHECK]:
            confidence += 0.2

        return min(confidence, 1.0)

    def _identify_threat_indicators(self, event: SecurityEvent) -> List[str]:
        """Identify threat indicators in the event"""
        indicators = []

        # Check for suspicious patterns in parameters
        if event.parameters:
            param_str = str(event.parameters).lower()
            if any(indicator in param_str for indicator in ['../', 'script', 'eval', 'exec']):
                indicators.append("injection_attempt")
            if 'admin' in param_str and event.event_type == SecurityEventType.ACCESS_DENIED:
                indicators.append("privilege_escalation_attempt")

        # Check for anomalous timing
        if hasattr(self, 'last_event_time'):
            time_diff = datetime.fromisoformat(event.timestamp) - self.last_event_time
            if time_diff.total_seconds() < 0.1:  # Very rapid events
                indicators.append("automated_attack")

        self.last_event_time = datetime.fromisoformat(event.timestamp)

        return indicators

    def _check_patterns(self, event: SecurityEvent) -> List[str]:
        """Check event against known security patterns"""
        matches = []
        current_time = datetime.fromisoformat(event.timestamp)

        for pattern_id, pattern in self.patterns.items():
            if event.event_type.value in pattern.indicators:
                # Check if pattern threshold is exceeded in time window
                window_start = current_time - timedelta(minutes=pattern.time_window_minutes)
                relevant_events = [
                    e for e in self.event_history
                    if datetime.fromisoformat(e["timestamp"]) >= window_start
                    and e["event_type"] in pattern.indicators
                ]

                if len(relevant_events) >= pattern.threshold:
                    matches.append(pattern_id)

        return matches

    def _calculate_anomaly_score(self, event: SecurityEvent) -> float:
        """Calculate anomaly score based on historical patterns"""
        if len(self.event_history) < 10:
            return 0.0  # Not enough history

        # Simple anomaly detection based on event frequency
        recent_events = self.event_history[-10:]
        event_type_counts = {}

        for hist_event in recent_events:
            event_type = hist_event["event_type"]
            event_type_counts[event_type] = event_type_counts.get(event_type, 0) + 1

        # Calculate expected frequency
        total_events = len(recent_events)
        expected_freq = event_type_counts.get(event.event_type.value, 0) / total_events

        # Higher anomaly score for rare events
        anomaly_score = 1.0 - expected_freq

        return min(anomaly_score, 1.0)

    def _generate_recommendations(self, event: SecurityEvent) -> List[str]:
        """Generate security recommendations based on event analysis"""
        recommendations = []

        if event.severity >= SecuritySeverity.WARNING:
            recommendations.append("Review security logs for related events")

        if event.event_type == SecurityEventType.ACCESS_DENIED:
            recommendations.append("Verify user permissions and access requirements")

        if event.contains_pii:
            recommendations.append("Ensure PII handling compliance")

        if event.event_type == SecurityEventType.EMERGENCY_TRIGGERED:
            recommendations.append("Investigate emergency trigger cause")
            recommendations.append("Review system stability")

        return recommendations


class EnhancedSecurityLogger:
    """
    Comprehensive security logging system with analysis and privacy protection
    """

    def __init__(self, database_path: str = "enhanced_security.db"):
        self.database_path = database_path
        self.logger = logging.getLogger("enhanced_security")

        # Initialize components
        self.privacy_filter = PrivacyFilter()
        self.analyzer = SecurityAnalyzer()

        # Event processing
        self.event_queue = []
        self.queue_lock = threading.Lock()
        self.processing_thread = None
        self.stop_processing = False

        # Event callbacks
        self.event_callbacks: List[Callable[[SecurityEvent], None]] = []

        # Performance tracking
        self.performance_metrics = {
            "events_processed": 0,
            "processing_time_total": 0.0,
            "last_processing_time": 0.0
        }

        # Initialize database and start processing
        self._init_database()
        self._start_event_processing()

        self.logger.info("Enhanced Security Logger initialized")

    def _init_database(self):
        """Initialize enhanced security logging database"""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()

        # Main security events table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS security_events (
                event_id TEXT PRIMARY KEY,
                timestamp TEXT NOT NULL,
                event_type TEXT NOT NULL,
                severity INTEGER NOT NULL,
                source_component TEXT NOT NULL,
                source_function TEXT NOT NULL,
                description TEXT NOT NULL,
                user_id TEXT,
                session_id TEXT,
                operation TEXT,
                resource TEXT,
                parameters TEXT,
                context TEXT,
                risk_score REAL,
                confidence_score REAL,
                threat_indicators TEXT,
                decision TEXT,
                reason TEXT,
                alternatives_suggested TEXT,
                contains_pii BOOLEAN,
                retention_policy TEXT,
                anonymization_applied BOOLEAN,
                correlation_id TEXT,
                parent_event_id TEXT,
                related_events TEXT,
                processing_time_ms REAL,
                system_load TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Security patterns table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS security_patterns (
                pattern_id TEXT PRIMARY KEY,
                pattern_type TEXT NOT NULL,
                description TEXT NOT NULL,
                indicators TEXT NOT NULL,
                threshold REAL NOT NULL,
                time_window_minutes INTEGER NOT NULL,
                severity INTEGER NOT NULL,
                auto_response TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                last_triggered TEXT
            )
        """)

        # Security analytics table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS security_analytics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                metric_name TEXT NOT NULL,
                metric_value REAL NOT NULL,
                metric_type TEXT NOT NULL,
                time_window TEXT NOT NULL,
                context TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create indexes for performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_timestamp ON security_events(timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_type ON security_events(event_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_severity ON security_events(severity)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_session ON security_events(session_id)")

        conn.commit()
        conn.close()

    def _start_event_processing(self):
        """Start background event processing thread"""
        self.processing_thread = threading.Thread(
            target=self._process_events,
            daemon=True,
            name="SecurityEventProcessor"
        )
        self.processing_thread.start()

    def _process_events(self):
        """Background event processing loop"""
        while not self.stop_processing:
            try:
                # Process queued events
                events_to_process = []
                with self.queue_lock:
                    if self.event_queue:
                        events_to_process = self.event_queue.copy()
                        self.event_queue.clear()

                for event in events_to_process:
                    self._process_single_event(event)

                # Sleep briefly to avoid excessive CPU usage
                time.sleep(0.1)

            except Exception as e:
                self.logger.error(f"Error in event processing: {e}")
                time.sleep(1.0)

    def _process_single_event(self, event: SecurityEvent):
        """Process a single security event"""
        start_time = time.time()

        try:
            # Analyze event
            analysis = self.analyzer.analyze_event(event)

            # Update event with analysis results
            event.risk_score = analysis["risk_score"]
            event.confidence_score = analysis["confidence_score"]
            event.threat_indicators = analysis["threat_indicators"]

            # Apply privacy filtering
            if event.contains_pii:
                event.parameters, _ = self.privacy_filter.anonymize_data(event.parameters)
                event.context, _ = self.privacy_filter.anonymize_data(event.context)
                event.anonymization_applied = True

            # Store event in database
            self._store_event(event)

            # Call registered callbacks
            for callback in self.event_callbacks:
                try:
                    callback(event)
                except Exception as e:
                    self.logger.error(f"Event callback failed: {e}")

            # Update performance metrics
            processing_time = (time.time() - start_time) * 1000
            self.performance_metrics["events_processed"] += 1
            self.performance_metrics["processing_time_total"] += processing_time
            self.performance_metrics["last_processing_time"] = processing_time

            event.processing_time_ms = processing_time

        except Exception as e:
            self.logger.error(f"Failed to process security event: {e}")

    def _store_event(self, event: SecurityEvent):
        """Store security event in database"""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO security_events (
                event_id, timestamp, event_type, severity, source_component, source_function,
                description, user_id, session_id, operation, resource, parameters, context,
                risk_score, confidence_score, threat_indicators, decision, reason,
                alternatives_suggested, contains_pii, retention_policy, anonymization_applied,
                correlation_id, parent_event_id, related_events, processing_time_ms, system_load
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            event.event_id,
            event.timestamp,
            event.event_type.value,
            event.severity.value,
            event.source_component,
            event.source_function,
            event.description,
            event.user_id,
            event.session_id,
            event.operation,
            event.resource,
            json.dumps(event.parameters),
            json.dumps(event.context),
            event.risk_score,
            event.confidence_score,
            json.dumps(event.threat_indicators),
            event.decision,
            event.reason,
            json.dumps(event.alternatives_suggested),
            event.contains_pii,
            event.retention_policy.value,
            event.anonymization_applied,
            event.correlation_id,
            event.parent_event_id,
            json.dumps(event.related_events),
            event.processing_time_ms,
            json.dumps(event.system_load) if event.system_load else None
        ))

        conn.commit()
        conn.close()

    def log_security_event(self,
                          event_type: SecurityEventType,
                          severity: SecuritySeverity,
                          description: str,
                          source_component: str,
                          source_function: str,
                          user_id: Optional[str] = None,
                          session_id: Optional[str] = None,
                          operation: Optional[str] = None,
                          resource: Optional[str] = None,
                          parameters: Optional[Dict[str, Any]] = None,
                          context: Optional[Dict[str, Any]] = None,
                          decision: Optional[str] = None,
                          reason: Optional[str] = None,
                          alternatives_suggested: Optional[List[str]] = None,
                          correlation_id: Optional[str] = None,
                          parent_event_id: Optional[str] = None) -> str:
        """
        Log a security event with comprehensive details
        Returns: event_id for correlation
        """

        # Create unique event ID
        event_id = str(uuid.uuid4())

        # Check for PII in parameters and context
        contains_pii = False
        if parameters:
            _, contains_pii_params = self.privacy_filter.anonymize_data(parameters)
            contains_pii = contains_pii or contains_pii_params
        if context:
            _, contains_pii_context = self.privacy_filter.anonymize_data(context)
            contains_pii = contains_pii or contains_pii_context

        # Determine retention policy based on severity and content
        if contains_pii:
            retention_policy = LogRetentionPolicy.COMPLIANCE
        elif severity >= SecuritySeverity.CRITICAL:
            retention_policy = LogRetentionPolicy.LONG_TERM
        elif severity >= SecuritySeverity.WARNING:
            retention_policy = LogRetentionPolicy.MEDIUM_TERM
        else:
            retention_policy = LogRetentionPolicy.SHORT_TERM

        # Create security event
        event = SecurityEvent(
            event_id=event_id,
            timestamp=datetime.now().isoformat(),
            event_type=event_type,
            severity=severity,
            source_component=source_component,
            source_function=source_function,
            description=description,
            user_id=user_id,
            session_id=session_id,
            operation=operation,
            resource=resource,
            parameters=parameters or {},
            context=context or {},
            risk_score=0.0,  # Will be calculated during processing
            confidence_score=0.0,  # Will be calculated during processing
            threat_indicators=[],  # Will be identified during processing
            decision=decision,
            reason=reason,
            alternatives_suggested=alternatives_suggested or [],
            contains_pii=contains_pii,
            retention_policy=retention_policy,
            anonymization_applied=False,
            correlation_id=correlation_id,
            parent_event_id=parent_event_id,
            related_events=[],
            processing_time_ms=None,
            system_load=None
        )

        # Queue event for processing
        with self.queue_lock:
            self.event_queue.append(event)

        return event_id

    def register_event_callback(self, callback: Callable[[SecurityEvent], None]):
        """Register callback for security events"""
        self.event_callbacks.append(callback)

    def get_security_events(self,
                           start_time: Optional[str] = None,
                           end_time: Optional[str] = None,
                           event_types: Optional[List[SecurityEventType]] = None,
                           min_severity: Optional[SecuritySeverity] = None,
                           session_id: Optional[str] = None,
                           limit: int = 100) -> List[Dict[str, Any]]:
        """Query security events with filtering"""

        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()

        # Build query with filters
        query = "SELECT * FROM security_events WHERE 1=1"
        params = []

        if start_time:
            query += " AND timestamp >= ?"
            params.append(start_time)

        if end_time:
            query += " AND timestamp <= ?"
            params.append(end_time)

        if event_types:
            placeholders = ",".join("?" for _ in event_types)
            query += f" AND event_type IN ({placeholders})"
            params.extend([et.value for et in event_types])

        if min_severity:
            query += " AND severity >= ?"
            params.append(min_severity.value)

        if session_id:
            query += " AND session_id = ?"
            params.append(session_id)

        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)

        cursor.execute(query, params)
        columns = [desc[0] for desc in cursor.description]
        events = [dict(zip(columns, row)) for row in cursor.fetchall()]

        conn.close()
        return events

    def get_security_analytics(self, time_window: str = "24h") -> Dict[str, Any]:
        """Get security analytics and metrics"""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()

        # Calculate time window
        if time_window == "1h":
            start_time = (datetime.now() - timedelta(hours=1)).isoformat()
        elif time_window == "24h":
            start_time = (datetime.now() - timedelta(days=1)).isoformat()
        elif time_window == "7d":
            start_time = (datetime.now() - timedelta(days=7)).isoformat()
        else:
            start_time = (datetime.now() - timedelta(days=1)).isoformat()

        # Event counts by type
        cursor.execute("""
            SELECT event_type, COUNT(*) as count
            FROM security_events
            WHERE timestamp >= ?
            GROUP BY event_type
            ORDER BY count DESC
        """, (start_time,))
        event_counts = dict(cursor.fetchall())

        # Severity distribution
        cursor.execute("""
            SELECT severity, COUNT(*) as count
            FROM security_events
            WHERE timestamp >= ?
            GROUP BY severity
            ORDER BY severity DESC
        """, (start_time,))
        severity_counts = dict(cursor.fetchall())

        # Risk score statistics
        cursor.execute("""
            SELECT AVG(risk_score) as avg_risk, MAX(risk_score) as max_risk,
                   COUNT(CASE WHEN risk_score >= 0.8 THEN 1 END) as high_risk_events
            FROM security_events
            WHERE timestamp >= ? AND risk_score IS NOT NULL
        """, (start_time,))
        risk_stats = cursor.fetchone()

        # Top threat indicators
        cursor.execute("""
            SELECT threat_indicators, COUNT(*) as count
            FROM security_events
            WHERE timestamp >= ? AND threat_indicators != '[]'
            GROUP BY threat_indicators
            ORDER BY count DESC
            LIMIT 10
        """, (start_time,))
        threat_indicators = cursor.fetchall()

        conn.close()

        return {
            "time_window": time_window,
            "total_events": sum(event_counts.values()),
            "event_counts": event_counts,
            "severity_distribution": severity_counts,
            "risk_statistics": {
                "average_risk": risk_stats[0] if risk_stats[0] else 0.0,
                "maximum_risk": risk_stats[1] if risk_stats[1] else 0.0,
                "high_risk_events": risk_stats[2] if risk_stats[2] else 0
            },
            "top_threat_indicators": threat_indicators,
            "performance_metrics": self.performance_metrics.copy()
        }

    def cleanup_old_events(self):
        """Clean up old events based on retention policies"""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()

        current_time = datetime.now()

        # Define cleanup thresholds
        cleanup_rules = {
            LogRetentionPolicy.IMMEDIATE.value: timedelta(0),
            LogRetentionPolicy.SHORT_TERM.value: timedelta(days=1),
            LogRetentionPolicy.MEDIUM_TERM.value: timedelta(days=7),
            LogRetentionPolicy.LONG_TERM.value: timedelta(days=30),
            # PERMANENT and COMPLIANCE are not cleaned up automatically
        }

        total_deleted = 0

        for policy, threshold in cleanup_rules.items():
            cutoff_time = (current_time - threshold).isoformat()

            cursor.execute("""
                DELETE FROM security_events
                WHERE retention_policy = ? AND timestamp < ?
            """, (policy, cutoff_time))

            deleted = cursor.rowcount
            total_deleted += deleted

            if deleted > 0:
                self.logger.info(f"Cleaned up {deleted} events with {policy} retention policy")

        conn.commit()
        conn.close()

        return total_deleted

    def stop(self):
        """Stop the security logger and cleanup"""
        self.stop_processing = True
        if self.processing_thread:
            self.processing_thread.join(timeout=5.0)

        self.logger.info("Enhanced Security Logger stopped")


if __name__ == "__main__":
    # Test the enhanced security logging system
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Create enhanced security logger
    security_logger = EnhancedSecurityLogger("test_enhanced_security.db")

    # Test various security events
    print("Testing Enhanced Security Logging System...")

    # Test permission check
    event_id1 = security_logger.log_security_event(
        event_type=SecurityEventType.PERMISSION_CHECK,
        severity=SecuritySeverity.INFO,
        description="User attempted file access",
        source_component="command_whitelist",
        source_function="check_permission",
        user_id="test_user",
        session_id="session_123",
        operation="file_read",
        resource="config.json",
        parameters={"file_path": "config.json"},
        decision="allowed",
        reason="User has read permission"
    )

    # Test security violation with PII
    event_id2 = security_logger.log_security_event(
        event_type=SecurityEventType.SECURITY_VIOLATION,
        severity=SecuritySeverity.WARNING,
        description="Potential path traversal attempt",
        source_component="command_whitelist",
        source_function="check_permission",
        user_id="test_user",
        session_id="session_123",
        operation="file_read",
        resource="../etc/passwd",
        parameters={"file_path": "../etc/passwd", "email": "user@example.com"},
        decision="denied",
        reason="Path traversal detected"
    )

    # Test emergency event
    event_id3 = security_logger.log_security_event(
        event_type=SecurityEventType.EMERGENCY_TRIGGERED,
        severity=SecuritySeverity.CRITICAL,
        description="Emergency stop activated",
        source_component="emergency_stop",
        source_function="voice_detection",
        session_id="session_123",
        operation="emergency_stop",
        context={"trigger": "voice_command", "phrase": "emergency stop"},
        decision="emergency_stop",
        reason="Voice emergency phrase detected"
    )

    # Wait a moment for processing
    time.sleep(2)

    # Get analytics
    analytics = security_logger.get_security_analytics("1h")
    print(f"\nSecurity Analytics:")
    print(f"Total events: {analytics['total_events']}")
    print(f"Event counts: {analytics['event_counts']}")
    print(f"Average risk: {analytics['risk_statistics']['average_risk']:.2f}")
    print(f"High risk events: {analytics['risk_statistics']['high_risk_events']}")

    # Get recent events
    events = security_logger.get_security_events(limit=5)
    print(f"\nRecent events: {len(events)}")
    for event in events:
        print(f"- {event['event_type']} ({event['severity']}) - {event['description']}")

    # Stop the logger
    security_logger.stop()

    print("\n✅ Enhanced Security Logging System testing completed!")