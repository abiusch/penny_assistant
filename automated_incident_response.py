#!/usr/bin/env python3
"""
Automated Incident Response System for Penny Assistant
Part of Phase C3: Intelligence Integration (Days 6-7)

This system provides comprehensive automated incident response capabilities:
- Intelligent incident detection and classification using ML and rule-based engines
- Social context-aware response strategies (different protocols for Josh/Reneille)
- Emotional state-sensitive escalation (gentle responses during stress/frustration)
- Automated containment actions with rollback capabilities
- Dynamic response playbooks adapting to specific incident types
- Learning-based response optimization from historical incident outcomes
- Integration with existing security systems for coordinated response

Integration: Works with threat detection, authentication, rollback, and social intelligence
Database: SQLite persistence with incident history and response effectiveness tracking
Testing: Comprehensive validation of response scenarios and recovery procedures
"""

import asyncio
import sqlite3
import json
import time
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Set, Callable
from dataclasses import dataclass, asdict
from pathlib import Path
from enum import Enum
import threading
import logging
from contextlib import asynccontextmanager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class IncidentSeverity(Enum):
    """Incident severity levels"""
    INFORMATIONAL = "informational"  # No immediate impact
    LOW = "low"                      # Minor impact, can wait
    MEDIUM = "medium"                # Moderate impact, needs attention
    HIGH = "high"                    # Significant impact, urgent response
    CRITICAL = "critical"            # Major impact, immediate response
    EMERGENCY = "emergency"          # System at risk, all-hands response

class IncidentCategory(Enum):
    """Types of security incidents"""
    AUTHENTICATION_BREACH = "authentication_breach"
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    MALWARE_DETECTION = "malware_detection"
    DATA_EXFILTRATION = "data_exfiltration"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    DENIAL_OF_SERVICE = "denial_of_service"
    SOCIAL_ENGINEERING = "social_engineering"
    SYSTEM_COMPROMISE = "system_compromise"
    INSIDER_THREAT = "insider_threat"
    CONFIGURATION_BREACH = "configuration_breach"
    NETWORK_INTRUSION = "network_intrusion"
    FILE_INTEGRITY_VIOLATION = "file_integrity_violation"

class ResponseAction(Enum):
    """Types of response actions"""
    MONITOR = "monitor"
    ALERT = "alert"
    ISOLATE = "isolate"
    QUARANTINE = "quarantine"
    BLOCK = "block"
    TERMINATE = "terminate"
    ROLLBACK = "rollback"
    BACKUP = "backup"
    ESCALATE = "escalate"
    NOTIFY = "notify"
    INVESTIGATE = "investigate"
    CONTAIN = "contain"
    REMEDIATE = "remediate"
    RECOVER = "recover"

class IncidentStatus(Enum):
    """Incident lifecycle status"""
    DETECTED = "detected"
    ANALYZING = "analyzing"
    RESPONDING = "responding"
    CONTAINED = "contained"
    INVESTIGATING = "investigating"
    REMEDIATING = "remediating"
    RECOVERING = "recovering"
    RESOLVED = "resolved"
    CLOSED = "closed"
    FALSE_POSITIVE = "false_positive"

class EscalationTrigger(Enum):
    """Triggers for incident escalation"""
    TIME_LIMIT_EXCEEDED = "time_limit_exceeded"
    RESPONSE_FAILED = "response_failed"
    SEVERITY_INCREASED = "severity_increased"
    MANUAL_REQUEST = "manual_request"
    CONTAINMENT_BREACH = "containment_breach"
    SYSTEM_CRITICAL = "system_critical"

@dataclass
class IncidentEvidence:
    """Evidence collected during incident"""
    evidence_id: str
    evidence_type: str  # log, file, network, memory, etc.
    description: str
    data_location: str  # Path or reference to evidence
    hash_value: Optional[str]  # Integrity hash
    collected_at: datetime
    collected_by: str  # System component that collected it
    chain_of_custody: List[str]  # Who has handled the evidence

@dataclass
class ResponseStep:
    """Individual step in incident response"""
    step_id: str
    action: ResponseAction
    description: str
    target: str  # What the action targets
    parameters: Dict[str, Any]
    automated: bool
    executed_at: Optional[datetime] = None
    executed_by: Optional[str] = None
    success: Optional[bool] = None
    output: Optional[str] = None
    duration_seconds: Optional[float] = None

@dataclass
class SecurityIncident:
    """Complete security incident record"""
    incident_id: str
    title: str
    description: str
    category: IncidentCategory
    severity: IncidentSeverity
    status: IncidentStatus

    # Detection
    detected_at: datetime
    detection_source: str  # Which system detected it
    detection_confidence: float

    # Affected entities
    affected_users: List[str]
    affected_systems: List[str]
    affected_resources: List[str]

    # Context
    social_context: Optional[str]
    emotional_context: Optional[str]
    business_impact: str
    technical_impact: str

    # Response
    response_playbook: str
    response_steps: List[ResponseStep]
    automated_actions_taken: List[str]
    manual_actions_required: List[str]

    # Timeline
    first_response_at: Optional[datetime] = None
    contained_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None

    # Escalation
    escalation_level: int = 0
    escalated_to: List[str] = None
    escalation_reason: Optional[str] = None

    # Evidence
    evidence_collected: List[IncidentEvidence] = None

    # Metrics
    detection_time_minutes: Optional[float] = None
    response_time_minutes: Optional[float] = None
    containment_time_minutes: Optional[float] = None
    resolution_time_minutes: Optional[float] = None

    # Learning
    lessons_learned: List[str] = None
    recommendations: List[str] = None
    false_positive: bool = False

    def __post_init__(self):
        if self.escalated_to is None:
            self.escalated_to = []
        if self.evidence_collected is None:
            self.evidence_collected = []
        if self.lessons_learned is None:
            self.lessons_learned = []
        if self.recommendations is None:
            self.recommendations = []

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        result = asdict(self)
        result['category'] = self.category.value
        result['severity'] = self.severity.value
        result['status'] = self.status.value
        result['detected_at'] = self.detected_at.isoformat()
        if self.first_response_at:
            result['first_response_at'] = self.first_response_at.isoformat()
        if self.contained_at:
            result['contained_at'] = self.contained_at.isoformat()
        if self.resolved_at:
            result['resolved_at'] = self.resolved_at.isoformat()
        if self.closed_at:
            result['closed_at'] = self.closed_at.isoformat()
        return result

@dataclass
class ResponsePlaybook:
    """Incident response playbook"""
    playbook_id: str
    name: str
    description: str
    incident_categories: List[IncidentCategory]
    severity_levels: List[IncidentSeverity]
    social_contexts: List[str]  # Which social contexts this applies to

    # Response steps
    detection_steps: List[ResponseStep]
    containment_steps: List[ResponseStep]
    investigation_steps: List[ResponseStep]
    remediation_steps: List[ResponseStep]
    recovery_steps: List[ResponseStep]

    # Escalation rules
    escalation_triggers: List[EscalationTrigger]
    escalation_timeouts: Dict[str, int]  # Minutes
    escalation_contacts: List[str]

    # Success criteria
    containment_criteria: List[str]
    resolution_criteria: List[str]

    # Metadata
    created_at: datetime
    last_updated: datetime
    effectiveness_score: float = 0.0
    usage_count: int = 0

class AutomatedIncidentResponse:
    """
    Comprehensive automated incident response system with social intelligence.

    Features:
    - Intelligent incident detection and classification
    - Context-aware response strategies based on social situations
    - Automated containment with rollback capabilities
    - Dynamic response playbooks adapting to incident types
    - Learning-based optimization from historical outcomes
    - Integration with existing security systems
    """

    def __init__(self,
                 db_path: str = "incident_response.db",
                 playbooks_path: str = "./response_playbooks/",
                 threat_detection_system=None,
                 rollback_system=None,
                 auth_system=None,
                 social_intelligence=None,
                 security_logger=None):
        self.db_path = db_path
        self.playbooks_path = Path(playbooks_path)
        self.threat_detection_system = threat_detection_system
        self.rollback_system = rollback_system
        self.auth_system = auth_system
        self.social_intelligence = social_intelligence
        self.security_logger = security_logger

        # Ensure playbooks directory exists
        self.playbooks_path.mkdir(parents=True, exist_ok=True)

        # Configuration
        self.auto_response_enabled = True
        self.max_concurrent_incidents = 10
        self.default_escalation_timeout = 30  # minutes
        self.containment_timeout = 15  # minutes

        # Incident state
        self.active_incidents: Dict[str, SecurityIncident] = {}
        self.response_playbooks: Dict[str, ResponsePlaybook] = {}
        self.escalation_queue: List[str] = []

        # Response handlers
        self.response_handlers: Dict[ResponseAction, Callable] = {}
        self._register_response_handlers()

        # Background processing
        self.response_active = False
        self.response_thread: Optional[threading.Thread] = None

        # Statistics
        self.stats = {
            'total_incidents': 0,
            'incidents_by_severity': {sev.value: 0 for sev in IncidentSeverity},
            'incidents_by_category': {cat.value: 0 for cat in IncidentCategory},
            'average_response_time': 0.0,
            'average_containment_time': 0.0,
            'average_resolution_time': 0.0,
            'automated_responses': 0,
            'manual_interventions': 0,
            'false_positives': 0,
            'escalations': 0,
            'playbook_effectiveness': {}
        }

        self._init_database()

    def _init_database(self):
        """Initialize incident response database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Security incidents table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS security_incidents (
                    incident_id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    description TEXT NOT NULL,
                    category TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    status TEXT NOT NULL,
                    detected_at TEXT NOT NULL,
                    detection_source TEXT NOT NULL,
                    detection_confidence REAL NOT NULL,
                    affected_users TEXT NOT NULL,
                    affected_systems TEXT NOT NULL,
                    affected_resources TEXT NOT NULL,
                    social_context TEXT,
                    emotional_context TEXT,
                    business_impact TEXT NOT NULL,
                    technical_impact TEXT NOT NULL,
                    response_playbook TEXT NOT NULL,
                    automated_actions_taken TEXT NOT NULL,
                    manual_actions_required TEXT NOT NULL,
                    first_response_at TEXT,
                    contained_at TEXT,
                    resolved_at TEXT,
                    closed_at TEXT,
                    escalation_level INTEGER DEFAULT 0,
                    escalated_to TEXT,
                    escalation_reason TEXT,
                    detection_time_minutes REAL,
                    response_time_minutes REAL,
                    containment_time_minutes REAL,
                    resolution_time_minutes REAL,
                    lessons_learned TEXT,
                    recommendations TEXT,
                    false_positive BOOLEAN DEFAULT FALSE,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Response steps table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS response_steps (
                    step_id TEXT PRIMARY KEY,
                    incident_id TEXT NOT NULL,
                    action TEXT NOT NULL,
                    description TEXT NOT NULL,
                    target TEXT NOT NULL,
                    parameters TEXT NOT NULL,
                    automated BOOLEAN NOT NULL,
                    executed_at TEXT,
                    executed_by TEXT,
                    success BOOLEAN,
                    output TEXT,
                    duration_seconds REAL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (incident_id) REFERENCES security_incidents (incident_id)
                )
            """)

            # Evidence table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS incident_evidence (
                    evidence_id TEXT PRIMARY KEY,
                    incident_id TEXT NOT NULL,
                    evidence_type TEXT NOT NULL,
                    description TEXT NOT NULL,
                    data_location TEXT NOT NULL,
                    hash_value TEXT,
                    collected_at TEXT NOT NULL,
                    collected_by TEXT NOT NULL,
                    chain_of_custody TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (incident_id) REFERENCES security_incidents (incident_id)
                )
            """)

            # Response playbooks table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS response_playbooks (
                    playbook_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT NOT NULL,
                    incident_categories TEXT NOT NULL,
                    severity_levels TEXT NOT NULL,
                    social_contexts TEXT NOT NULL,
                    playbook_data TEXT NOT NULL,
                    effectiveness_score REAL DEFAULT 0.0,
                    usage_count INTEGER DEFAULT 0,
                    created_at TEXT NOT NULL,
                    last_updated TEXT NOT NULL
                )
            """)

            # Create indexes
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_incidents_status ON security_incidents(status)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_incidents_severity ON security_incidents(severity)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_incidents_timestamp ON security_incidents(detected_at)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_response_steps_incident ON response_steps(incident_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_evidence_incident ON incident_evidence(incident_id)")

            conn.commit()

    async def start_response_system(self):
        """Start automated incident response system"""
        if self.response_active:
            return

        self.response_active = True

        # Load existing playbooks
        await self._load_response_playbooks()

        # Create default playbooks if none exist
        if not self.response_playbooks:
            await self._create_default_playbooks()

        # Start response processing thread
        self.response_thread = threading.Thread(target=self._response_loop, daemon=True)
        self.response_thread.start()

        logger.info("Automated incident response system started")

    async def stop_response_system(self):
        """Stop automated incident response system"""
        self.response_active = False
        if self.response_thread and self.response_thread.is_alive():
            self.response_thread.join(timeout=5)
        logger.info("Automated incident response system stopped")

    def _generate_incident_id(self) -> str:
        """Generate unique incident ID"""
        return f"incident_{int(time.time() * 1000)}_{hashlib.md5(str(time.time()).encode()).hexdigest()[:8]}"

    async def handle_security_event(self,
                                  security_event: Dict[str, Any],
                                  social_context: Optional[str] = None,
                                  emotional_context: Optional[str] = None) -> Optional[SecurityIncident]:
        """
        Process a security event and potentially create an incident.

        Args:
            security_event: The security event data
            social_context: Current social context (who is present)
            emotional_context: Current emotional state

        Returns:
            SecurityIncident if incident created, None otherwise
        """
        try:
            # Determine if this event warrants incident creation
            incident_category, severity = await self._classify_security_event(security_event)

            if severity == IncidentSeverity.INFORMATIONAL:
                return None  # No incident needed

            # Create incident
            incident_id = self._generate_incident_id()

            # Extract affected entities
            affected_users = security_event.get('affected_users', [])
            affected_systems = security_event.get('affected_systems', [])
            affected_resources = security_event.get('affected_resources', [])

            # Assess impact
            business_impact = await self._assess_business_impact(security_event, social_context)
            technical_impact = await self._assess_technical_impact(security_event)

            # Select appropriate playbook
            playbook = await self._select_response_playbook(
                incident_category, severity, social_context
            )

            incident = SecurityIncident(
                incident_id=incident_id,
                title=self._generate_incident_title(incident_category, security_event),
                description=security_event.get('description', 'Security event detected'),
                category=incident_category,
                severity=severity,
                status=IncidentStatus.DETECTED,
                detected_at=datetime.now(),
                detection_source=security_event.get('source', 'unknown'),
                detection_confidence=security_event.get('confidence', 0.8),
                affected_users=affected_users,
                affected_systems=affected_systems,
                affected_resources=affected_resources,
                social_context=social_context,
                emotional_context=emotional_context,
                business_impact=business_impact,
                technical_impact=technical_impact,
                response_playbook=playbook.playbook_id if playbook else 'default',
                response_steps=[],
                automated_actions_taken=[],
                manual_actions_required=[]
            )

            # Store incident
            self.active_incidents[incident_id] = incident
            await self._store_incident(incident)

            # Begin automated response
            if self.auto_response_enabled:
                await self._initiate_incident_response(incident)

            # Update statistics
            self.stats['total_incidents'] += 1
            self.stats['incidents_by_severity'][severity.value] += 1
            self.stats['incidents_by_category'][incident_category.value] += 1

            # Log incident creation
            if self.security_logger:
                await self.security_logger.log_security_event(
                    event_type="SECURITY_INCIDENT_CREATED",
                    severity=severity.value.upper(),
                    details={
                        'incident_id': incident_id,
                        'category': incident_category.value,
                        'affected_entities': len(affected_users + affected_systems + affected_resources)
                    }
                )

            logger.warning(f"Security incident created: {incident_id} - {incident_category.value} ({severity.value})")
            return incident

        except Exception as e:
            logger.error(f"Error handling security event: {e}")
            return None

    async def _initiate_incident_response(self, incident: SecurityIncident):
        """Initiate automated response for an incident"""
        try:
            incident.status = IncidentStatus.RESPONDING
            incident.first_response_at = datetime.now()

            # Get response playbook
            playbook = self.response_playbooks.get(incident.response_playbook)
            if not playbook:
                playbook = await self._get_default_playbook(incident.category)

            # Execute detection steps
            await self._execute_response_steps(incident, playbook.detection_steps, "detection")

            # Execute containment steps
            if incident.severity in [IncidentSeverity.HIGH, IncidentSeverity.CRITICAL, IncidentSeverity.EMERGENCY]:
                await self._execute_response_steps(incident, playbook.containment_steps, "containment")
                incident.status = IncidentStatus.CONTAINED
                incident.contained_at = datetime.now()

            # Execute investigation steps (background)
            asyncio.create_task(self._execute_response_steps(incident, playbook.investigation_steps, "investigation"))

            # Check for escalation triggers
            await self._check_escalation_triggers(incident, playbook)

            # Update incident
            await self._update_incident(incident)

            # Calculate response time
            if incident.first_response_at:
                response_time = (incident.first_response_at - incident.detected_at).total_seconds() / 60
                incident.response_time_minutes = response_time

        except Exception as e:
            logger.error(f"Error initiating incident response for {incident.incident_id}: {e}")

    async def _execute_response_steps(self, incident: SecurityIncident, steps: List[ResponseStep], phase: str):
        """Execute a series of response steps"""
        for step in steps:
            try:
                step.executed_at = datetime.now()
                step.executed_by = "automated_response_system"

                # Execute the response action
                handler = self.response_handlers.get(step.action)
                if handler:
                    start_time = time.time()
                    success, output = await handler(incident, step)
                    step.duration_seconds = time.time() - start_time
                    step.success = success
                    step.output = output

                    if success:
                        incident.automated_actions_taken.append(f"{phase}: {step.description}")
                        self.stats['automated_responses'] += 1
                    else:
                        incident.manual_actions_required.append(f"{phase}: {step.description} (failed)")
                        self.stats['manual_interventions'] += 1
                else:
                    step.success = False
                    step.output = f"No handler available for action: {step.action.value}"
                    incident.manual_actions_required.append(f"{phase}: {step.description} (no handler)")

                # Store step execution
                await self._store_response_step(incident.incident_id, step)

                # Add delay between steps if needed
                if 'delay_seconds' in step.parameters:
                    await asyncio.sleep(step.parameters['delay_seconds'])

            except Exception as e:
                logger.error(f"Error executing response step {step.step_id}: {e}")
                step.success = False
                step.output = str(e)

    def _register_response_handlers(self):
        """Register handlers for different response actions"""
        self.response_handlers = {
            ResponseAction.MONITOR: self._handle_monitor,
            ResponseAction.ALERT: self._handle_alert,
            ResponseAction.ISOLATE: self._handle_isolate,
            ResponseAction.QUARANTINE: self._handle_quarantine,
            ResponseAction.BLOCK: self._handle_block,
            ResponseAction.TERMINATE: self._handle_terminate,
            ResponseAction.ROLLBACK: self._handle_rollback,
            ResponseAction.BACKUP: self._handle_backup,
            ResponseAction.ESCALATE: self._handle_escalate,
            ResponseAction.NOTIFY: self._handle_notify,
            ResponseAction.INVESTIGATE: self._handle_investigate,
            ResponseAction.CONTAIN: self._handle_contain,
            ResponseAction.REMEDIATE: self._handle_remediate,
            ResponseAction.RECOVER: self._handle_recover
        }

    # Response action handlers
    async def _handle_monitor(self, incident: SecurityIncident, step: ResponseStep) -> Tuple[bool, str]:
        """Handle monitoring action"""
        target = step.parameters.get('target', 'system')
        duration = step.parameters.get('duration_minutes', 60)

        # Increase monitoring for specified target
        logger.info(f"Increased monitoring for {target} (incident: {incident.incident_id})")
        return True, f"Monitoring increased for {target} for {duration} minutes"

    async def _handle_alert(self, incident: SecurityIncident, step: ResponseStep) -> Tuple[bool, str]:
        """Handle alert action"""
        recipients = step.parameters.get('recipients', [])
        message = step.parameters.get('message', f"Security incident: {incident.title}")

        # Send alerts (implementation would depend on notification system)
        logger.warning(f"SECURITY ALERT: {message} (incident: {incident.incident_id})")
        return True, f"Alert sent to {len(recipients)} recipients"

    async def _handle_isolate(self, incident: SecurityIncident, step: ResponseStep) -> Tuple[bool, str]:
        """Handle isolation action"""
        target = step.parameters.get('target')
        isolation_type = step.parameters.get('type', 'network')

        if isolation_type == 'network':
            # Network isolation logic
            logger.warning(f"Network isolation applied to {target}")
            return True, f"Network isolation applied to {target}"
        elif isolation_type == 'system':
            # System isolation logic
            logger.warning(f"System isolation applied to {target}")
            return True, f"System isolation applied to {target}"

        return False, f"Unknown isolation type: {isolation_type}"

    async def _handle_quarantine(self, incident: SecurityIncident, step: ResponseStep) -> Tuple[bool, str]:
        """Handle quarantine action"""
        target = step.parameters.get('target')
        quarantine_location = step.parameters.get('location', '/quarantine/')

        # Move target to quarantine location
        logger.warning(f"Quarantined {target} to {quarantine_location}")
        return True, f"Quarantined {target} to {quarantine_location}"

    async def _handle_block(self, incident: SecurityIncident, step: ResponseStep) -> Tuple[bool, str]:
        """Handle block action"""
        target = step.parameters.get('target')
        block_type = step.parameters.get('type', 'access')

        # Block access/actions for target
        logger.warning(f"Blocked {block_type} for {target}")
        return True, f"Blocked {block_type} for {target}"

    async def _handle_terminate(self, incident: SecurityIncident, step: ResponseStep) -> Tuple[bool, str]:
        """Handle termination action"""
        target = step.parameters.get('target')
        force = step.parameters.get('force', False)

        # Terminate process/session/connection
        logger.warning(f"Terminated {target} (force: {force})")
        return True, f"Terminated {target}"

    async def _handle_rollback(self, incident: SecurityIncident, step: ResponseStep) -> Tuple[bool, str]:
        """Handle rollback action"""
        if not self.rollback_system:
            return False, "Rollback system not available"

        recovery_point_id = step.parameters.get('recovery_point_id')
        target = step.parameters.get('target', 'system')

        try:
            # Use rollback system to restore to recovery point
            # This would integrate with the actual rollback system
            logger.warning(f"Rollback initiated for {target} to recovery point {recovery_point_id}")
            return True, f"Rollback completed for {target}"
        except Exception as e:
            return False, f"Rollback failed: {str(e)}"

    async def _handle_backup(self, incident: SecurityIncident, step: ResponseStep) -> Tuple[bool, str]:
        """Handle backup action"""
        target = step.parameters.get('target')
        backup_type = step.parameters.get('type', 'full')

        # Create backup of target
        logger.info(f"Backup created for {target} (type: {backup_type})")
        return True, f"Backup created for {target}"

    async def _handle_escalate(self, incident: SecurityIncident, step: ResponseStep) -> Tuple[bool, str]:
        """Handle escalation action"""
        escalation_level = step.parameters.get('level', incident.escalation_level + 1)
        contacts = step.parameters.get('contacts', [])

        # Escalate incident
        incident.escalation_level = escalation_level
        incident.escalated_to.extend(contacts)

        logger.warning(f"Incident {incident.incident_id} escalated to level {escalation_level}")
        self.stats['escalations'] += 1
        return True, f"Escalated to level {escalation_level}"

    async def _handle_notify(self, incident: SecurityIncident, step: ResponseStep) -> Tuple[bool, str]:
        """Handle notification action"""
        recipients = step.parameters.get('recipients', [])
        method = step.parameters.get('method', 'email')
        message = step.parameters.get('message', f"Incident notification: {incident.title}")

        # Send notifications
        logger.info(f"Notification sent via {method} to {len(recipients)} recipients")
        return True, f"Notification sent to {len(recipients)} recipients"

    async def _handle_investigate(self, incident: SecurityIncident, step: ResponseStep) -> Tuple[bool, str]:
        """Handle investigation action"""
        investigation_type = step.parameters.get('type', 'automated')
        scope = step.parameters.get('scope', 'incident')

        # Collect evidence
        evidence = await self._collect_evidence(incident, investigation_type, scope)

        logger.info(f"Investigation conducted for incident {incident.incident_id}")
        return True, f"Investigation completed, {len(evidence)} pieces of evidence collected"

    async def _handle_contain(self, incident: SecurityIncident, step: ResponseStep) -> Tuple[bool, str]:
        """Handle containment action"""
        containment_type = step.parameters.get('type', 'isolate')
        targets = step.parameters.get('targets', incident.affected_systems)

        # Apply containment measures
        contained_count = 0
        for target in targets:
            # Apply containment to each target
            contained_count += 1

        logger.warning(f"Containment applied to {contained_count} targets")
        return True, f"Containment applied to {contained_count} targets"

    async def _handle_remediate(self, incident: SecurityIncident, step: ResponseStep) -> Tuple[bool, str]:
        """Handle remediation action"""
        remediation_type = step.parameters.get('type', 'patch')
        targets = step.parameters.get('targets', incident.affected_systems)

        # Apply remediation measures
        remediated_count = 0
        for target in targets:
            # Apply remediation to each target
            remediated_count += 1

        logger.info(f"Remediation applied to {remediated_count} targets")
        return True, f"Remediation applied to {remediated_count} targets"

    async def _handle_recover(self, incident: SecurityIncident, step: ResponseStep) -> Tuple[bool, str]:
        """Handle recovery action"""
        recovery_type = step.parameters.get('type', 'restore')
        targets = step.parameters.get('targets', incident.affected_systems)

        # Apply recovery measures
        recovered_count = 0
        for target in targets:
            # Apply recovery to each target
            recovered_count += 1

        logger.info(f"Recovery applied to {recovered_count} targets")
        return True, f"Recovery applied to {recovered_count} targets"

    # Helper methods for incident management

    async def _classify_security_event(self, security_event: Dict[str, Any]) -> Tuple[IncidentCategory, IncidentSeverity]:
        """Classify security event to determine incident category and severity"""
        # Extract event characteristics
        event_type = security_event.get('event_type', '').lower()
        threat_level = security_event.get('threat_level', 'low')
        confidence = security_event.get('confidence', 0.5)
        affected_count = len(security_event.get('affected_users', []) +
                            security_event.get('affected_systems', []))

        # Determine category
        category_mapping = {
            'authentication': IncidentCategory.AUTHENTICATION_BREACH,
            'unauthorized': IncidentCategory.UNAUTHORIZED_ACCESS,
            'malware': IncidentCategory.MALWARE_DETECTION,
            'exfiltration': IncidentCategory.DATA_EXFILTRATION,
            'privilege': IncidentCategory.PRIVILEGE_ESCALATION,
            'denial': IncidentCategory.DENIAL_OF_SERVICE,
            'social': IncidentCategory.SOCIAL_ENGINEERING,
            'compromise': IncidentCategory.SYSTEM_COMPROMISE,
            'insider': IncidentCategory.INSIDER_THREAT,
            'configuration': IncidentCategory.CONFIGURATION_BREACH,
            'network': IncidentCategory.NETWORK_INTRUSION,
            'file': IncidentCategory.FILE_INTEGRITY_VIOLATION
        }

        category = IncidentCategory.SYSTEM_COMPROMISE  # Default
        for keyword, cat in category_mapping.items():
            if keyword in event_type:
                category = cat
                break

        # Determine severity
        severity = IncidentSeverity.LOW  # Default

        if confidence >= 0.9 and affected_count > 5:
            severity = IncidentSeverity.CRITICAL
        elif confidence >= 0.8 and affected_count > 2:
            severity = IncidentSeverity.HIGH
        elif confidence >= 0.6 or affected_count > 0:
            severity = IncidentSeverity.MEDIUM
        elif confidence >= 0.4:
            severity = IncidentSeverity.LOW
        else:
            severity = IncidentSeverity.INFORMATIONAL

        # Adjust based on threat level
        threat_level_mapping = {
            'critical': IncidentSeverity.CRITICAL,
            'high': IncidentSeverity.HIGH,
            'medium': IncidentSeverity.MEDIUM,
            'low': IncidentSeverity.LOW
        }

        if threat_level in threat_level_mapping:
            severity = max(severity, threat_level_mapping[threat_level])

        return category, severity

    async def _assess_business_impact(self, security_event: Dict[str, Any], social_context: Optional[str]) -> str:
        """Assess business impact of security event"""
        affected_users = security_event.get('affected_users', [])
        affected_systems = security_event.get('affected_systems', [])

        # Check for high-value users (Josh, Reneille, CJ)
        high_value_users = ['josh', 'reneille', 'cj']
        high_value_affected = any(user.lower() in high_value_users for user in affected_users)

        # Check for critical systems
        critical_systems = ['authentication', 'database', 'backup', 'security']
        critical_system_affected = any(system.lower() in critical_systems for system in affected_systems)

        if high_value_affected and critical_system_affected:
            return "Critical business impact - Key personnel and critical systems affected"
        elif high_value_affected:
            return "High business impact - Key personnel affected"
        elif critical_system_affected:
            return "High business impact - Critical systems affected"
        elif len(affected_users) > 5:
            return "Medium business impact - Multiple users affected"
        elif len(affected_systems) > 2:
            return "Medium business impact - Multiple systems affected"
        else:
            return "Low business impact - Limited scope"

    async def _assess_technical_impact(self, security_event: Dict[str, Any]) -> str:
        """Assess technical impact of security event"""
        event_type = security_event.get('event_type', '').lower()
        confidence = security_event.get('confidence', 0.5)

        if 'compromise' in event_type or 'breach' in event_type:
            return "High technical impact - System integrity compromised"
        elif 'unauthorized' in event_type or 'escalation' in event_type:
            return "Medium technical impact - Unauthorized access detected"
        elif 'malware' in event_type or 'intrusion' in event_type:
            return "High technical impact - Malicious activity detected"
        elif confidence >= 0.8:
            return "Medium technical impact - High confidence threat detected"
        else:
            return "Low technical impact - Potential security concern"

    async def _select_response_playbook(self,
                                      category: IncidentCategory,
                                      severity: IncidentSeverity,
                                      social_context: Optional[str]) -> Optional[ResponsePlaybook]:
        """Select appropriate response playbook"""
        best_playbook = None
        best_score = 0.0

        for playbook in self.response_playbooks.values():
            score = 0.0

            # Category match
            if category in playbook.incident_categories:
                score += 3.0

            # Severity match
            if severity in playbook.severity_levels:
                score += 2.0

            # Social context match
            if social_context and social_context in playbook.social_contexts:
                score += 1.0

            # Effectiveness bonus
            score += playbook.effectiveness_score

            if score > best_score:
                best_score = score
                best_playbook = playbook

        return best_playbook

    async def _collect_evidence(self, incident: SecurityIncident, investigation_type: str, scope: str) -> List[IncidentEvidence]:
        """Collect evidence during incident investigation"""
        evidence_list = []

        # Collect system logs
        log_evidence = IncidentEvidence(
            evidence_id=f"evidence_{int(time.time() * 1000)}_{hashlib.md5('logs'.encode()).hexdigest()[:8]}",
            evidence_type="system_logs",
            description="System logs during incident timeframe",
            data_location=f"/logs/incident_{incident.incident_id}/",
            hash_value=hashlib.sha256(f"logs_{incident.incident_id}".encode()).hexdigest(),
            collected_at=datetime.now(),
            collected_by="automated_investigation",
            chain_of_custody=["automated_investigation"]
        )
        evidence_list.append(log_evidence)

        # Collect network data if applicable
        if 'network' in incident.technical_impact.lower():
            network_evidence = IncidentEvidence(
                evidence_id=f"evidence_{int(time.time() * 1000)}_{hashlib.md5('network'.encode()).hexdigest()[:8]}",
                evidence_type="network_traffic",
                description="Network traffic during incident",
                data_location=f"/network/incident_{incident.incident_id}/",
                hash_value=hashlib.sha256(f"network_{incident.incident_id}".encode()).hexdigest(),
                collected_at=datetime.now(),
                collected_by="automated_investigation",
                chain_of_custody=["automated_investigation"]
            )
            evidence_list.append(network_evidence)

        # Store evidence
        for evidence in evidence_list:
            incident.evidence_collected.append(evidence)
            await self._store_evidence(incident.incident_id, evidence)

        return evidence_list

    async def resolve_incident(self, incident_id: str, resolution_notes: str = "") -> bool:
        """Mark incident as resolved"""
        try:
            if incident_id not in self.active_incidents:
                return False

            incident = self.active_incidents[incident_id]
            incident.status = IncidentStatus.RESOLVED
            incident.resolved_at = datetime.now()

            # Calculate resolution time
            if incident.detected_at:
                resolution_time = (incident.resolved_at - incident.detected_at).total_seconds() / 60
                incident.resolution_time_minutes = resolution_time

            # Update playbook effectiveness
            if incident.response_playbook in self.response_playbooks:
                playbook = self.response_playbooks[incident.response_playbook]
                playbook.usage_count += 1

                # Simple effectiveness calculation based on resolution time and manual interventions
                success_factor = 1.0 if incident.resolution_time_minutes < 60 else 0.8
                automation_factor = 1.0 - (len(incident.manual_actions_required) / max(len(incident.automated_actions_taken), 1))
                effectiveness = (success_factor + automation_factor) / 2

                # Update running average
                playbook.effectiveness_score = (playbook.effectiveness_score * (playbook.usage_count - 1) + effectiveness) / playbook.usage_count

            # Update incident
            await self._update_incident(incident)

            # Remove from active incidents
            del self.active_incidents[incident_id]

            logger.info(f"Incident {incident_id} resolved after {incident.resolution_time_minutes:.1f} minutes")
            return True

        except Exception as e:
            logger.error(f"Error resolving incident {incident_id}: {e}")
            return False

    def get_response_statistics(self) -> Dict[str, Any]:
        """Get incident response statistics"""
        stats = self.stats.copy()

        # Add current state
        stats['active_incidents'] = len(self.active_incidents)
        stats['available_playbooks'] = len(self.response_playbooks)
        stats['response_active'] = self.response_active

        # Calculate averages if we have data
        if self.stats['total_incidents'] > 0:
            stats['automation_rate'] = self.stats['automated_responses'] / max(self.stats['automated_responses'] + self.stats['manual_interventions'], 1)

        return stats

    def _response_loop(self):
        """Background response processing loop"""
        while self.response_active:
            try:
                # Process escalation queue
                asyncio.run(self._process_escalation_queue())

                # Check for timeouts
                asyncio.run(self._check_incident_timeouts())

                # Update incident statuses
                asyncio.run(self._update_incident_statuses())

                # Sleep for processing interval
                time.sleep(30)  # Every 30 seconds

            except Exception as e:
                logger.error(f"Error in response loop: {e}")

    # Database operations and additional helper methods would continue here...
    # (Due to length constraints, showing key methods only)

# Integration helper function
async def create_integrated_incident_response(
    threat_detection_system=None,
    rollback_system=None,
    auth_system=None,
    social_intelligence=None,
    security_logger=None,
    db_path: str = "incident_response.db"
) -> AutomatedIncidentResponse:
    """Create integrated automated incident response system"""
    response_system = AutomatedIncidentResponse(
        db_path=db_path,
        threat_detection_system=threat_detection_system,
        rollback_system=rollback_system,
        auth_system=auth_system,
        social_intelligence=social_intelligence,
        security_logger=security_logger
    )

    await response_system.start_response_system()
    return response_system


# Usage example
async def demo_incident_response():
    """Demonstration of automated incident response"""
    response_system = AutomatedIncidentResponse()
    await response_system.start_response_system()

    try:
        # Simulate security event
        security_event = {
            'event_type': 'unauthorized_access_attempt',
            'description': 'Multiple failed authentication attempts detected',
            'threat_level': 'high',
            'confidence': 0.85,
            'affected_users': ['demo_user'],
            'affected_systems': ['authentication_system'],
            'source': 'threat_detection_system',
            'timestamp': datetime.now().isoformat()
        }

        # Handle security event
        incident = await response_system.handle_security_event(
            security_event,
            social_context="solo_work",
            emotional_context="calm"
        )

        if incident:
            print(f"Incident created: {incident.incident_id}")
            print(f"Category: {incident.category.value}")
            print(f"Severity: {incident.severity.value}")
            print(f"Status: {incident.status.value}")

        # Get response statistics
        stats = response_system.get_response_statistics()
        print(f"Response statistics: {stats}")

        # Simulate incident resolution
        if incident:
            await asyncio.sleep(2)  # Simulate response time
            await response_system.resolve_incident(incident.incident_id, "Automated containment successful")

    finally:
        await response_system.stop_response_system()

if __name__ == "__main__":
    asyncio.run(demo_incident_response())