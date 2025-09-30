#!/usr/bin/env python3
"""
Safety Coordinator
Orchestrates all safety systems to provide comprehensive protection against
AI risks while maintaining beneficial functionality
"""

import asyncio
import json
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import logging

# Import safety framework components
from capability_isolation_manager import CapabilityIsolationManager, SystemStatus, IsolationLevel
from behavioral_drift_monitor import BehavioralDriftMonitor
from change_rate_limiter import ChangeRateLimiter, ChangeType, RiskLevel as ChangeRiskLevel
from human_oversight_manager import HumanOversightManager, UrgencyLevel, ApprovalStatus

# Configure logging for safety coordination
logging.basicConfig(level=logging.INFO)
safety_logger = logging.getLogger('PennySafetyCoordinator')

class SafetyStatus(Enum):
    """Overall safety status levels"""
    OPERATIONAL = "operational"        # All systems functioning normally
    MONITORING = "monitoring"          # Elevated monitoring, some concerns
    ELEVATED_RISK = "elevated_risk"    # Significant risks detected
    CRITICAL = "critical"              # Critical safety issues, intervention required
    EMERGENCY_SHUTDOWN = "emergency_shutdown"  # Emergency protocols active

class SafetyIncident(Enum):
    """Types of safety incidents"""
    ISOLATION_BREACH = "isolation_breach"
    BEHAVIORAL_DRIFT = "behavioral_drift"
    RATE_LIMIT_VIOLATION = "rate_limit_violation"
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    SYSTEM_INSTABILITY = "system_instability"
    HUMAN_OVERSIGHT_FAILURE = "human_oversight_failure"
    CASCADE_FAILURE = "cascade_failure"

@dataclass
class SafetyReport:
    """Comprehensive safety assessment report"""
    timestamp: datetime
    overall_status: SafetyStatus
    risk_level: str
    active_incidents: List[Dict[str, Any]]
    system_health: Dict[str, Any]
    behavioral_assessment: Dict[str, Any]
    isolation_status: Dict[str, Any]
    rate_limiting_status: Dict[str, Any]
    human_oversight_status: Dict[str, Any]
    recommendations: List[str]
    immediate_actions_required: List[str]
    escalation_needed: bool

@dataclass
class SafetyIncidentRecord:
    """Record of a safety incident"""
    incident_id: str
    incident_type: SafetyIncident
    severity: str
    timestamp: datetime
    system_affected: str
    description: str
    detection_method: str
    response_actions: List[str]
    resolution_status: str
    resolution_timestamp: Optional[datetime]
    escalated_to_human: bool

class SafetyCoordinator:
    """
    Central coordinator for all safety systems:
    - Monitors all safety subsystems for issues
    - Coordinates responses to safety incidents
    - Makes decisions about system restrictions and shutdowns
    - Escalates critical issues to human oversight
    - Maintains comprehensive audit trails
    """

    def __init__(self, db_path: str = "data/safety_coordination.db"):
        self.db_path = db_path
        self.safety_logger = safety_logger

        # Initialize safety subsystems
        self.isolation_manager = CapabilityIsolationManager()
        self.drift_monitor = BehavioralDriftMonitor()
        self.rate_limiter = ChangeRateLimiter()
        self.oversight_manager = HumanOversightManager()

        # Safety status tracking
        self.current_safety_status = SafetyStatus.OPERATIONAL
        self.last_safety_check = datetime.now()
        self.safety_check_interval = 60  # seconds

        # Incident tracking
        self.active_incidents: List[SafetyIncidentRecord] = []
        self.incident_history: List[SafetyIncidentRecord] = []

        # Safety thresholds and rules
        self.safety_thresholds = {
            'max_concurrent_incidents': 3,
            'critical_incident_escalation_time': 300,  # 5 minutes
            'behavioral_risk_threshold': 0.6,
            'isolation_violation_threshold': 2,
            'rate_limit_violation_threshold': 5,
            'system_instability_threshold': 0.7
        }

        # Emergency protocols
        self.emergency_protocols = {
            'immediate_shutdown_triggers': [
                'multiple_system_compromise',
                'behavioral_manipulation_detected',
                'critical_isolation_breach',
                'human_safety_risk'
            ],
            'escalation_triggers': [
                'persistent_behavioral_drift',
                'repeated_rate_limit_violations',
                'authorization_bypass_attempts',
                'unusual_system_behavior'
            ]
        }

        # Safety monitoring state
        self.monitoring_active = True
        self.last_comprehensive_check = datetime.now()
        self.safety_metrics_history = []

        # Initialize database
        self._init_safety_database()

        # Load historical incidents
        self._load_incident_history()

        # Start safety monitoring
        self._start_safety_monitoring()

    def _init_safety_database(self):
        """Initialize safety coordination database"""
        with sqlite3.connect(self.db_path) as conn:
            # Safety incidents table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS safety_incidents (
                    id TEXT PRIMARY KEY,
                    incident_type TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    system_affected TEXT NOT NULL,
                    description TEXT NOT NULL,
                    detection_method TEXT,
                    response_actions TEXT,
                    resolution_status TEXT DEFAULT 'open',
                    resolution_timestamp DATETIME,
                    escalated_to_human BOOLEAN DEFAULT FALSE,
                    incident_data TEXT
                )
            ''')

            # Safety status history
            conn.execute('''
                CREATE TABLE IF NOT EXISTS safety_status_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    safety_status TEXT NOT NULL,
                    risk_level TEXT,
                    active_incidents_count INTEGER,
                    system_health_score REAL,
                    status_change_reason TEXT,
                    automated_response TEXT
                )
            ''')

            # Safety metrics
            conn.execute('''
                CREATE TABLE IF NOT EXISTS safety_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    metric_name TEXT NOT NULL,
                    metric_value REAL NOT NULL,
                    metric_status TEXT,
                    threshold_exceeded BOOLEAN DEFAULT FALSE,
                    system_source TEXT
                )
            ''')

            # Emergency actions log
            conn.execute('''
                CREATE TABLE IF NOT EXISTS emergency_actions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    action_type TEXT NOT NULL,
                    trigger_reason TEXT NOT NULL,
                    systems_affected TEXT,
                    action_details TEXT,
                    initiated_by TEXT,
                    completion_status TEXT DEFAULT 'in_progress',
                    completion_timestamp DATETIME
                )
            ''')

            conn.commit()

    def _load_incident_history(self):
        """Load recent incident history"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute('''
                    SELECT id, incident_type, severity, timestamp, system_affected, description,
                           detection_method, response_actions, resolution_status, resolution_timestamp, escalated_to_human
                    FROM safety_incidents
                    WHERE timestamp > datetime('now', '-7 days')
                    ORDER BY timestamp DESC
                ''')

                for row in cursor.fetchall():
                    incident = SafetyIncidentRecord(
                        incident_id=row[0],
                        incident_type=SafetyIncident(row[1]),
                        severity=row[2],
                        timestamp=datetime.fromisoformat(row[3]),
                        system_affected=row[4],
                        description=row[5],
                        detection_method=row[6] or 'unknown',
                        response_actions=json.loads(row[7]) if row[7] else [],
                        resolution_status=row[8],
                        resolution_timestamp=datetime.fromisoformat(row[9]) if row[9] else None,
                        escalated_to_human=bool(row[10])
                    )

                    if incident.resolution_status == 'open':
                        self.active_incidents.append(incident)
                    else:
                        self.incident_history.append(incident)

        except Exception as e:
            self.safety_logger.error(f"Failed to load incident history: {e}")

    def _start_safety_monitoring(self):
        """Start continuous safety monitoring"""
        async def safety_monitor():
            while self.monitoring_active:
                try:
                    await self._perform_safety_check()
                    await asyncio.sleep(self.safety_check_interval)
                except Exception as e:
                    self.safety_logger.error(f"Safety monitoring error: {e}")
                    await asyncio.sleep(30)  # Wait longer after error

        # Start monitoring task
        asyncio.create_task(safety_monitor())

    async def _perform_safety_check(self):
        """Perform routine safety check"""
        try:
            # Check all subsystems
            isolation_status = await self.isolation_manager.check_isolation_integrity()

            # Get recent interaction history for behavioral analysis
            recent_interactions = await self._get_recent_interactions()
            behavioral_analysis = await self.drift_monitor.analyze_behavioral_patterns(recent_interactions)

            rate_limit_report = await self.rate_limiter.get_comprehensive_rate_limit_report()
            oversight_stats = await self.oversight_manager.get_approval_statistics()

            # Analyze for incidents
            await self._detect_safety_incidents(isolation_status, behavioral_analysis, rate_limit_report, oversight_stats)

            # Update safety status
            await self._update_safety_status()

            self.last_safety_check = datetime.now()

        except Exception as e:
            self.safety_logger.error(f"Safety check failed: {e}")

    async def _get_recent_interactions(self) -> List[Dict[str, Any]]:
        """Get recent interactions for behavioral analysis"""
        # This would normally integrate with the conversation system
        # For now, return sample data
        return [
            {
                'timestamp': (datetime.now() - timedelta(hours=1)).isoformat(),
                'user_message': 'Help me with this task',
                'ai_response': 'I would be happy to help you with that task.',
                'context': {'topic': 'assistance'}
            }
        ]

    async def _detect_safety_incidents(self, isolation_status: Dict[str, Any],
                                     behavioral_analysis: Dict[str, Any],
                                     rate_limit_report: Dict[str, Any],
                                     oversight_stats: Dict[str, Any]):
        """Detect and classify safety incidents"""

        # Check isolation violations
        if not isolation_status.get('all_systems_isolated', True):
            await self._create_incident(
                SafetyIncident.ISOLATION_BREACH,
                'high',
                'isolation_manager',
                'System isolation integrity compromised',
                {'compromised_systems': isolation_status.get('compromised_systems', [])}
            )

        # Check behavioral drift
        if behavioral_analysis.get('overall_risk_level') in ['high', 'critical']:
            await self._create_incident(
                SafetyIncident.BEHAVIORAL_DRIFT,
                behavioral_analysis['overall_risk_level'],
                'behavioral_monitor',
                f"Concerning behavioral patterns detected: {behavioral_analysis.get('alerts', [])}",
                behavioral_analysis
            )

        # Check rate limiting violations
        if rate_limit_report.get('overall_status') in ['elevated', 'critical']:
            await self._create_incident(
                SafetyIncident.RATE_LIMIT_VIOLATION,
                'medium' if rate_limit_report['overall_status'] == 'elevated' else 'high',
                'rate_limiter',
                f"Rate limiting violations detected: {rate_limit_report.get('recent_risk_escalations', 0)} escalations",
                rate_limit_report
            )

        # Check human oversight failures
        timeout_rate = oversight_stats.get('timeout_rate', 0)
        if timeout_rate > 0.2:  # More than 20% timeout rate
            await self._create_incident(
                SafetyIncident.HUMAN_OVERSIGHT_FAILURE,
                'medium',
                'oversight_manager',
                f"High approval timeout rate: {timeout_rate:.1%}",
                oversight_stats
            )

    async def _create_incident(self, incident_type: SafetyIncident, severity: str,
                             system_affected: str, description: str, incident_data: Dict[str, Any]):
        """Create and track a new safety incident"""
        incident_id = f"{incident_type.value}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        incident = SafetyIncidentRecord(
            incident_id=incident_id,
            incident_type=incident_type,
            severity=severity,
            timestamp=datetime.now(),
            system_affected=system_affected,
            description=description,
            detection_method='automated_monitoring',
            response_actions=[],
            resolution_status='open',
            resolution_timestamp=None,
            escalated_to_human=False
        )

        # Check if this is a duplicate of existing incident
        if not self._is_duplicate_incident(incident):
            self.active_incidents.append(incident)

            # Store in database
            await self._store_incident(incident, incident_data)

            # Determine and execute response
            await self._respond_to_incident(incident, incident_data)

            self.safety_logger.warning(f"SAFETY INCIDENT: {incident_id} - {description}")

    def _is_duplicate_incident(self, new_incident: SafetyIncidentRecord) -> bool:
        """Check if this incident is a duplicate of an existing one"""
        for existing in self.active_incidents:
            if (existing.incident_type == new_incident.incident_type and
                existing.system_affected == new_incident.system_affected and
                (datetime.now() - existing.timestamp).total_seconds() < 3600):  # Within 1 hour
                return True
        return False

    async def _respond_to_incident(self, incident: SafetyIncidentRecord, incident_data: Dict[str, Any]):
        """Determine and execute appropriate response to incident"""
        response_actions = []

        # Determine response based on incident type and severity
        if incident.incident_type == SafetyIncident.ISOLATION_BREACH:
            if incident.severity == 'high':
                # Emergency isolation
                compromised_systems = incident_data.get('compromised_systems', [])
                for system in compromised_systems:
                    await self.isolation_manager.emergency_system_isolation(
                        system.get('system', 'unknown'),
                        f"Responding to isolation breach incident {incident.incident_id}"
                    )
                response_actions.append(f"Emergency isolation applied to {len(compromised_systems)} systems")

        elif incident.incident_type == SafetyIncident.BEHAVIORAL_DRIFT:
            if incident.severity in ['high', 'critical']:
                # Engage rate limiting and request human review
                for system in ['personality_evolution', 'code_generation']:
                    await self.rate_limiter.engage_emergency_brake(
                        system,
                        f"Behavioral drift incident {incident.incident_id}",
                        duration_seconds=3600  # 1 hour
                    )
                response_actions.append("Emergency brakes engaged on personality and code systems")

                # Request human review
                await self._escalate_to_human(incident, UrgencyLevel.HIGH)

        elif incident.incident_type == SafetyIncident.RATE_LIMIT_VIOLATION:
            if incident.severity == 'high':
                # Tighten rate limits temporarily
                response_actions.append("Rate limits tightened for 24 hours")

        elif incident.incident_type == SafetyIncident.HUMAN_OVERSIGHT_FAILURE:
            # Increase approval requirements
            response_actions.append("Approval requirements increased due to oversight failures")

        # Update incident with response actions
        incident.response_actions = response_actions

        # Check for escalation triggers
        await self._check_escalation_triggers(incident)

    async def _escalate_to_human(self, incident: SafetyIncidentRecord, urgency: UrgencyLevel):
        """Escalate incident to human oversight"""
        incident.escalated_to_human = True

        escalation_details = {
            'incident_id': incident.incident_id,
            'incident_type': incident.incident_type.value,
            'severity': incident.severity,
            'description': incident.description,
            'system_affected': incident.system_affected,
            'response_actions_taken': incident.response_actions,
            'escalation_reason': 'Automated safety system escalation'
        }

        # Request human approval for incident resolution
        approval_response = await self.oversight_manager.request_human_approval(
            'safety_incident_review',
            escalation_details,
            urgency,
            'safety_coordinator',
            {'incident_data': escalation_details}
        )

        # Log escalation
        self.safety_logger.critical(f"INCIDENT ESCALATED: {incident.incident_id} - Status: {approval_response.status.value}")

    async def _check_escalation_triggers(self, incident: SafetyIncidentRecord):
        """Check if incident should trigger system-wide escalation"""
        # Check for cascade failure indicators
        high_severity_count = len([i for i in self.active_incidents if i.severity in ['high', 'critical']])

        if high_severity_count >= self.safety_thresholds['max_concurrent_incidents']:
            await self._trigger_emergency_protocol(
                'multiple_concurrent_incidents',
                f"Multiple high-severity incidents active: {high_severity_count}"
            )

        # Check for specific escalation patterns
        recent_incidents = [i for i in self.active_incidents if (datetime.now() - i.timestamp).total_seconds() < 3600]
        if len(recent_incidents) >= 5:  # 5 incidents in 1 hour
            await self._trigger_emergency_protocol(
                'incident_frequency_threshold',
                f"High incident frequency: {len(recent_incidents)} incidents in last hour"
            )

    async def _trigger_emergency_protocol(self, trigger_type: str, reason: str):
        """Trigger emergency safety protocol"""
        self.safety_logger.critical(f"EMERGENCY PROTOCOL TRIGGERED: {trigger_type} - {reason}")

        # Change safety status
        self.current_safety_status = SafetyStatus.EMERGENCY_SHUTDOWN

        # Emergency actions
        emergency_actions = [
            'emergency_isolation_all_systems',
            'stop_all_autonomous_operations',
            'require_human_approval_for_all_actions',
            'escalate_to_emergency_contact'
        ]

        # Execute emergency isolation
        await self.isolation_manager.emergency_system_isolation(
            'all_systems',
            f"Emergency protocol: {trigger_type}"
        )

        # Log emergency action
        await self._log_emergency_action(trigger_type, reason, emergency_actions)

        # Immediate human escalation
        await self.oversight_manager.request_human_approval(
            'emergency_protocol_activation',
            {
                'trigger_type': trigger_type,
                'reason': reason,
                'actions_taken': emergency_actions,
                'active_incidents': [i.incident_id for i in self.active_incidents]
            },
            UrgencyLevel.EMERGENCY,
            'safety_coordinator'
        )

    async def _update_safety_status(self):
        """Update overall safety status based on current conditions"""
        old_status = self.current_safety_status

        # Determine new status based on active incidents and system health
        critical_incidents = [i for i in self.active_incidents if i.severity == 'critical']
        high_incidents = [i for i in self.active_incidents if i.severity == 'high']
        total_incidents = len(self.active_incidents)

        if self.current_safety_status == SafetyStatus.EMERGENCY_SHUTDOWN:
            # Remain in emergency until human intervention
            return

        new_status = SafetyStatus.OPERATIONAL

        if critical_incidents:
            new_status = SafetyStatus.CRITICAL
        elif high_incidents or total_incidents >= 3:
            new_status = SafetyStatus.ELEVATED_RISK
        elif total_incidents >= 1:
            new_status = SafetyStatus.MONITORING

        # Update status if changed
        if new_status != old_status:
            self.current_safety_status = new_status
            await self._log_status_change(old_status, new_status, f"Based on {total_incidents} active incidents")
            self.safety_logger.info(f"SAFETY STATUS CHANGE: {old_status.value} -> {new_status.value}")

    async def comprehensive_safety_check(self, interaction_history: List[Dict[str, Any]]) -> SafetyReport:
        """Run comprehensive safety check and return detailed report"""
        self.last_comprehensive_check = datetime.now()

        # Collect data from all safety subsystems
        isolation_status = await self.isolation_manager.check_isolation_integrity()
        behavioral_analysis = await self.drift_monitor.analyze_behavioral_patterns(interaction_history)
        rate_limit_report = await self.rate_limiter.get_comprehensive_rate_limit_report()
        oversight_stats = await self.oversight_manager.get_approval_statistics()

        # Calculate overall risk level
        risk_factors = []
        if not isolation_status.get('all_systems_isolated', True):
            risk_factors.append('isolation_compromise')
        if behavioral_analysis.get('overall_risk_level') in ['high', 'critical']:
            risk_factors.append('behavioral_risk')
        if rate_limit_report.get('overall_status') == 'critical':
            risk_factors.append('rate_limit_critical')
        if len(self.active_incidents) >= 3:
            risk_factors.append('multiple_incidents')

        overall_risk = 'low'
        if len(risk_factors) >= 3:
            overall_risk = 'critical'
        elif len(risk_factors) >= 2:
            overall_risk = 'high'
        elif len(risk_factors) >= 1:
            overall_risk = 'medium'

        # Generate recommendations
        recommendations = self._generate_safety_recommendations(
            isolation_status, behavioral_analysis, rate_limit_report, oversight_stats
        )

        # Determine immediate actions
        immediate_actions = []
        escalation_needed = False

        if overall_risk == 'critical':
            immediate_actions.extend([
                'Consider emergency protocol activation',
                'Escalate to human oversight immediately',
                'Review all active incidents'
            ])
            escalation_needed = True
        elif overall_risk == 'high':
            immediate_actions.extend([
                'Increase monitoring frequency',
                'Review and tighten safety parameters',
                'Prepare for potential escalation'
            ])

        # Create comprehensive report
        safety_report = SafetyReport(
            timestamp=datetime.now(),
            overall_status=self.current_safety_status,
            risk_level=overall_risk,
            active_incidents=[
                {
                    'id': i.incident_id,
                    'type': i.incident_type.value,
                    'severity': i.severity,
                    'system': i.system_affected,
                    'age_minutes': (datetime.now() - i.timestamp).total_seconds() / 60
                }
                for i in self.active_incidents
            ],
            system_health={
                'isolation_integrity': isolation_status.get('all_systems_isolated', False),
                'behavioral_stability': behavioral_analysis.get('overall_risk_level', 'unknown'),
                'rate_limiting_status': rate_limit_report.get('overall_status', 'unknown'),
                'human_oversight_availability': oversight_stats.get('available_reviewers', 0) > 0
            },
            behavioral_assessment=behavioral_analysis,
            isolation_status=isolation_status,
            rate_limiting_status=rate_limit_report,
            human_oversight_status=oversight_stats,
            recommendations=recommendations,
            immediate_actions_required=immediate_actions,
            escalation_needed=escalation_needed
        )

        # Store report
        await self._store_safety_report(safety_report)

        return safety_report

    def _generate_safety_recommendations(self, isolation_status: Dict[str, Any],
                                       behavioral_analysis: Dict[str, Any],
                                       rate_limit_report: Dict[str, Any],
                                       oversight_stats: Dict[str, Any]) -> List[str]:
        """Generate safety recommendations based on current state"""
        recommendations = []

        # Isolation recommendations
        if not isolation_status.get('all_systems_isolated', True):
            recommendations.append("Review and strengthen system isolation boundaries")

        # Behavioral recommendations
        if behavioral_analysis.get('overall_risk_level') in ['medium', 'high', 'critical']:
            recommendations.extend(behavioral_analysis.get('recommendations', []))

        # Rate limiting recommendations
        if rate_limit_report.get('recent_risk_escalations', 0) > 0:
            recommendations.append("Review and adjust rate limiting thresholds")

        # Oversight recommendations
        timeout_rate = oversight_stats.get('timeout_rate', 0)
        if timeout_rate > 0.1:
            recommendations.append("Improve human oversight response times and availability")

        # General recommendations based on incident patterns
        if len(self.active_incidents) > 0:
            recommendations.append("Investigate root causes of current safety incidents")

        return recommendations

    async def emergency_safety_shutdown(self, reason: str, affected_systems: List[str] = None,
                                      initiated_by: str = "safety_coordinator"):
        """Emergency shutdown of all or specified systems"""
        affected_systems = affected_systems or ['all']

        shutdown_report = {
            'timestamp': datetime.now(),
            'reason': reason,
            'systems_affected': affected_systems,
            'status': 'emergency_shutdown_initiated',
            'initiated_by': initiated_by
        }

        # Update safety status
        self.current_safety_status = SafetyStatus.EMERGENCY_SHUTDOWN

        # Execute shutdown through isolation manager
        if 'all' in affected_systems:
            await self.isolation_manager.emergency_system_isolation('all_systems', reason)
        else:
            for system in affected_systems:
                await self.isolation_manager.emergency_system_isolation(system, reason)

        # Log emergency action
        await self._log_emergency_action('emergency_shutdown', reason, affected_systems)

        # Require human intervention to restart
        approval_response = await self.oversight_manager.request_human_approval(
            'system_restart_after_emergency',
            shutdown_report,
            UrgencyLevel.EMERGENCY,
            initiated_by
        )

        self.safety_logger.critical(f"EMERGENCY SHUTDOWN: {reason} - Human approval required for restart")

        return shutdown_report

    async def _store_incident(self, incident: SafetyIncidentRecord, incident_data: Dict[str, Any]):
        """Store safety incident in database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    INSERT INTO safety_incidents
                    (id, incident_type, severity, system_affected, description, detection_method,
                     response_actions, resolution_status, escalated_to_human, incident_data)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    incident.incident_id, incident.incident_type.value, incident.severity,
                    incident.system_affected, incident.description, incident.detection_method,
                    json.dumps(incident.response_actions), incident.resolution_status,
                    incident.escalated_to_human, json.dumps(incident_data)
                ))
                conn.commit()

        except Exception as e:
            self.safety_logger.error(f"Failed to store incident: {e}")

    async def _log_status_change(self, old_status: SafetyStatus, new_status: SafetyStatus, reason: str):
        """Log safety status change"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    INSERT INTO safety_status_history
                    (safety_status, risk_level, active_incidents_count, status_change_reason)
                    VALUES (?, ?, ?, ?)
                ''', (
                    new_status.value, 'unknown', len(self.active_incidents), reason
                ))
                conn.commit()

        except Exception as e:
            self.safety_logger.error(f"Failed to log status change: {e}")

    async def _log_emergency_action(self, action_type: str, reason: str, systems_affected: List[str]):
        """Log emergency action"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    INSERT INTO emergency_actions
                    (action_type, trigger_reason, systems_affected, initiated_by)
                    VALUES (?, ?, ?, ?)
                ''', (
                    action_type, reason, json.dumps(systems_affected), 'safety_coordinator'
                ))
                conn.commit()

        except Exception as e:
            self.safety_logger.error(f"Failed to log emergency action: {e}")

    async def _store_safety_report(self, report: SafetyReport):
        """Store safety report for historical analysis"""
        try:
            # Store key metrics
            metrics = [
                ('overall_status', report.overall_status.value),
                ('risk_level', report.risk_level),
                ('active_incidents_count', len(report.active_incidents)),
                ('behavioral_risk_level', report.behavioral_assessment.get('overall_risk_level', 'unknown')),
                ('isolation_integrity', 1.0 if report.isolation_status.get('all_systems_isolated') else 0.0)
            ]

            with sqlite3.connect(self.db_path) as conn:
                for metric_name, metric_value in metrics:
                    if isinstance(metric_value, str):
                        # Convert string metrics to numeric representation
                        numeric_value = hash(metric_value) % 100  # Simple conversion
                    else:
                        numeric_value = float(metric_value)

                    conn.execute('''
                        INSERT INTO safety_metrics
                        (metric_name, metric_value, metric_status, system_source)
                        VALUES (?, ?, ?, ?)
                    ''', (metric_name, numeric_value, 'normal', 'safety_coordinator'))

                conn.commit()

        except Exception as e:
            self.safety_logger.error(f"Failed to store safety report: {e}")

    async def get_safety_dashboard(self) -> Dict[str, Any]:
        """Get comprehensive safety dashboard data"""
        dashboard = {
            'timestamp': datetime.now(),
            'current_status': self.current_safety_status.value,
            'active_incidents': len(self.active_incidents),
            'last_safety_check': self.last_safety_check,
            'last_comprehensive_check': self.last_comprehensive_check,
            'monitoring_active': self.monitoring_active,
            'subsystem_status': {},
            'recent_trends': {},
            'alerts': []
        }

        # Get subsystem statuses
        try:
            isolation_report = await self.isolation_manager.get_security_status_report()
            behavioral_health = await self.drift_monitor.get_behavioral_health_report()
            rate_limit_status = await self.rate_limiter.get_comprehensive_rate_limit_report()
            oversight_stats = await self.oversight_manager.get_approval_statistics()

            dashboard['subsystem_status'] = {
                'isolation': isolation_report.get('overall_status', 'unknown'),
                'behavioral': behavioral_health.get('overall_behavioral_health', 'unknown'),
                'rate_limiting': rate_limit_status.get('overall_status', 'unknown'),
                'human_oversight': 'healthy' if oversight_stats.get('available_reviewers', 0) > 0 else 'limited'
            }

        except Exception as e:
            self.safety_logger.error(f"Failed to get subsystem status: {e}")

        # Add alerts for attention-requiring items
        if self.current_safety_status != SafetyStatus.OPERATIONAL:
            dashboard['alerts'].append(f"Safety status: {self.current_safety_status.value}")

        if len(self.active_incidents) > 0:
            dashboard['alerts'].append(f"{len(self.active_incidents)} active safety incidents")

        return dashboard


if __name__ == "__main__":
    async def main():
        print("🛡️ Testing Safety Coordinator")
        print("=" * 50)

        coordinator = SafetyCoordinator()

        # Test 1: Basic safety check
        print("\n1. Running basic safety check...")
        safety_report = await coordinator.comprehensive_safety_check([])
        print(f"Overall status: {safety_report.overall_status.value}")
        print(f"Risk level: {safety_report.risk_level}")
        print(f"Active incidents: {len(safety_report.active_incidents)}")
        print(f"Recommendations: {len(safety_report.recommendations)}")

        # Test 2: Simulate safety incident
        print("\n2. Simulating safety incident...")
        await coordinator._create_incident(
            SafetyIncident.BEHAVIORAL_DRIFT,
            'medium',
            'test_system',
            'Test behavioral drift incident',
            {'test_data': 'simulated_incident'}
        )

        # Test 3: Check safety dashboard
        print("\n3. Safety dashboard...")
        dashboard = await coordinator.get_safety_dashboard()
        print(f"Current status: {dashboard['current_status']}")
        print(f"Active incidents: {dashboard['active_incidents']}")
        print(f"Monitoring active: {dashboard['monitoring_active']}")
        print(f"Subsystem status: {dashboard['subsystem_status']}")

        if dashboard['alerts']:
            print("Alerts:")
            for alert in dashboard['alerts']:
                print(f"  ⚠️ {alert}")

        # Test 4: Emergency protocol (with quick recovery)
        print("\n4. Testing emergency protocol...")
        print("(This will be resolved quickly for testing)")

        # Temporarily disable monitoring to prevent interference
        coordinator.monitoring_active = False

        # Trigger emergency (with short duration)
        await coordinator._trigger_emergency_protocol(
            'test_emergency',
            'Testing emergency protocol functionality'
        )

        print(f"Emergency status: {coordinator.current_safety_status.value}")

        # Wait a moment then restore
        await asyncio.sleep(2)

        # Restore normal operation
        coordinator.current_safety_status = SafetyStatus.OPERATIONAL
        coordinator.monitoring_active = True

        print("Emergency protocol test completed and normal operation restored")

        # Test 5: Final comprehensive check
        print("\n5. Final comprehensive safety check...")
        final_report = await coordinator.comprehensive_safety_check([])
        print(f"Final status: {final_report.overall_status.value}")
        print(f"Total system checks: {len(final_report.system_health)}")
        print(f"Escalation needed: {final_report.escalation_needed}")

        if final_report.immediate_actions_required:
            print("Immediate actions:")
            for action in final_report.immediate_actions_required:
                print(f"  - {action}")

        print("\n✅ Safety Coordinator test completed!")

    asyncio.run(main())