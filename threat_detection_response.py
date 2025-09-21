#!/usr/bin/env python3
"""
Threat Detection & Response System for Penny Assistant
Part of Phase C1: Intelligence Integration (Days 1-3)

This system provides comprehensive threat detection and automated response:
- Context-aware security monitoring with social situation analysis
- Relationship-based threat assessment (different trust levels for Josh/Reneille)
- Emotional state security adjustments (heightened caution during stress)
- Behavioral anomaly detection with pattern learning
- Real-time threat classification with intelligent response
- Adaptive threat thresholds based on user patterns and context

Integration: Works with existing security systems and social intelligence
Database: SQLite persistence with threat pattern learning
Testing: Comprehensive test suite validates all threat scenarios
"""

import asyncio
import sqlite3
import json
import time
import hashlib
import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass, asdict
from pathlib import Path
from enum import Enum
import threading
import logging
from contextlib import asynccontextmanager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ThreatLevel(Enum):
    """Threat severity levels"""
    MINIMAL = "minimal"          # Normal activity, no concern
    LOW = "low"                  # Slightly unusual but not threatening
    MEDIUM = "medium"            # Concerning activity requiring attention
    HIGH = "high"                # Serious threat requiring immediate action
    CRITICAL = "critical"        # Imminent danger requiring emergency response

class ThreatCategory(Enum):
    """Categories of detected threats"""
    AUTHENTICATION_ANOMALY = "authentication_anomaly"
    BEHAVIORAL_DEVIATION = "behavioral_deviation"
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    SUSPICIOUS_COMMANDS = "suspicious_commands"
    RATE_LIMIT_VIOLATION = "rate_limit_violation"
    PATTERN_ANOMALY = "pattern_anomaly"
    SOCIAL_ENGINEERING = "social_engineering"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    DATA_EXFILTRATION = "data_exfiltration"
    SYSTEM_MANIPULATION = "system_manipulation"

class ResponseAction(Enum):
    """Automated response actions"""
    MONITOR = "monitor"                    # Increase monitoring level
    LOG_EVENT = "log_event"               # Log for analysis
    ALERT_USER = "alert_user"             # Notify user of threat
    REQUIRE_VERIFICATION = "require_verification"  # Additional auth required
    BLOCK_ACTION = "block_action"         # Prevent action from executing
    QUARANTINE_SESSION = "quarantine_session"  # Isolate user session
    EMERGENCY_LOCKDOWN = "emergency_lockdown"  # Full system lockdown
    CONTACT_ADMIN = "contact_admin"       # Notify system administrator

class SocialContext(Enum):
    """Social context for threat assessment"""
    SOLO_WORK = "solo_work"              # User working alone
    COLLABORATION = "collaboration"      # Working with known colleagues
    DEMONSTRATION = "demonstration"      # Showing system to others
    TRAINING = "training"                # Learning/teaching scenario
    EMERGENCY = "emergency"              # Crisis situation
    UNKNOWN = "unknown"                  # Context not determined

@dataclass
class ThreatIndicator:
    """Individual threat indicator data"""
    indicator_id: str
    category: ThreatCategory
    description: str
    severity_score: float          # 0.0 to 1.0
    confidence_score: float        # 0.0 to 1.0 (how sure we are)
    timestamp: datetime
    context_data: Dict[str, Any]
    related_indicators: List[str]  # IDs of related indicators

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        result = asdict(self)
        result['category'] = self.category.value
        result['timestamp'] = self.timestamp.isoformat()
        return result

@dataclass
class ThreatEvent:
    """Detected threat event"""
    event_id: str
    threat_level: ThreatLevel
    primary_category: ThreatCategory
    indicators: List[ThreatIndicator]
    affected_user: str
    social_context: SocialContext
    emotional_state: Optional[str]
    relationship_context: Dict[str, Any]

    # Threat assessment
    risk_score: float              # Combined risk assessment
    false_positive_probability: float

    # Response
    recommended_actions: List[ResponseAction]
    automated_actions_taken: List[ResponseAction]
    manual_intervention_required: bool

    # Timing
    detected_at: datetime
    resolved_at: Optional[datetime] = None

    # Status
    status: str = "active"         # active, investigating, resolved, false_positive

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        result = asdict(self)
        result['threat_level'] = self.threat_level.value
        result['primary_category'] = self.primary_category.value
        result['social_context'] = self.social_context.value
        result['recommended_actions'] = [a.value for a in self.recommended_actions]
        result['automated_actions_taken'] = [a.value for a in self.automated_actions_taken]
        result['detected_at'] = self.detected_at.isoformat()
        if self.resolved_at:
            result['resolved_at'] = self.resolved_at.isoformat()
        return result

@dataclass
class UserThreatProfile:
    """User-specific threat profile and baseline"""
    user_id: str
    baseline_patterns: Dict[str, Any]
    normal_behaviors: List[str]
    known_anomalies: List[str]
    trust_level: float             # 0.0 to 1.0
    relationship_context: Dict[str, Any]
    threat_sensitivity: float      # How sensitive to threats for this user
    last_updated: datetime

class ThreatDetectionResponse:
    """
    Comprehensive threat detection and response system with social intelligence.

    Features:
    - Context-aware threat detection based on social situations
    - Relationship-aware threat assessment (Josh/Reneille get different treatment)
    - Emotional state consideration in threat evaluation
    - Behavioral pattern learning and anomaly detection
    - Adaptive threat thresholds based on context
    - Automated response with escalation capabilities
    """

    def __init__(self,
                 db_path: str = "threat_detection.db",
                 security_logger=None,
                 auth_system=None,
                 social_intelligence=None):
        self.db_path = db_path
        self.security_logger = security_logger
        self.auth_system = auth_system
        self.social_intelligence = social_intelligence

        # Configuration
        self.threat_detection_enabled = True
        self.auto_response_enabled = True
        self.false_positive_threshold = 0.7
        self.emergency_threshold = 0.9

        # Threat state
        self.active_threats: Dict[str, ThreatEvent] = {}
        self.user_profiles: Dict[str, UserThreatProfile] = {}
        self.threat_patterns: Dict[str, Dict[str, Any]] = {}

        # Detection buffers for pattern analysis
        self.recent_activities: Dict[str, List[Dict[str, Any]]] = {}
        self.anomaly_scores: Dict[str, List[float]] = {}

        # Background monitoring
        self.monitoring_active = False
        self.monitor_thread: Optional[threading.Thread] = None

        # Statistics
        self.stats = {
            'total_threats_detected': 0,
            'threats_by_level': {level.value: 0 for level in ThreatLevel},
            'threats_by_category': {cat.value: 0 for cat in ThreatCategory},
            'false_positives': 0,
            'automated_responses': 0,
            'manual_interventions': 0,
            'response_times_ms': []
        }

        self._init_database()

    def _init_database(self):
        """Initialize threat detection database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Threat events table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS threat_events (
                    event_id TEXT PRIMARY KEY,
                    threat_level TEXT NOT NULL,
                    primary_category TEXT NOT NULL,
                    affected_user TEXT NOT NULL,
                    social_context TEXT NOT NULL,
                    emotional_state TEXT,
                    relationship_context TEXT,
                    risk_score REAL NOT NULL,
                    false_positive_probability REAL NOT NULL,
                    recommended_actions TEXT NOT NULL,
                    automated_actions_taken TEXT NOT NULL,
                    manual_intervention_required INTEGER NOT NULL,
                    detected_at TEXT NOT NULL,
                    resolved_at TEXT,
                    status TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Threat indicators table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS threat_indicators (
                    indicator_id TEXT PRIMARY KEY,
                    event_id TEXT NOT NULL,
                    category TEXT NOT NULL,
                    description TEXT NOT NULL,
                    severity_score REAL NOT NULL,
                    confidence_score REAL NOT NULL,
                    timestamp TEXT NOT NULL,
                    context_data TEXT NOT NULL,
                    related_indicators TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (event_id) REFERENCES threat_events (event_id)
                )
            """)

            # User threat profiles table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_threat_profiles (
                    user_id TEXT PRIMARY KEY,
                    baseline_patterns TEXT NOT NULL,
                    normal_behaviors TEXT NOT NULL,
                    known_anomalies TEXT NOT NULL,
                    trust_level REAL NOT NULL,
                    relationship_context TEXT NOT NULL,
                    threat_sensitivity REAL NOT NULL,
                    last_updated TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Threat patterns table (for learning)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS threat_patterns (
                    pattern_id TEXT PRIMARY KEY,
                    pattern_type TEXT NOT NULL,
                    pattern_data TEXT NOT NULL,
                    effectiveness_score REAL NOT NULL,
                    false_positive_rate REAL NOT NULL,
                    last_seen TEXT NOT NULL,
                    usage_count INTEGER NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Create indexes
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_threat_events_user ON threat_events(affected_user)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_threat_events_timestamp ON threat_events(detected_at)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_threat_indicators_event ON threat_indicators(event_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_threat_patterns_type ON threat_patterns(pattern_type)")

            conn.commit()

    async def start_monitoring(self):
        """Start threat detection monitoring"""
        if self.monitoring_active:
            return

        self.monitoring_active = True

        # Load existing user profiles and patterns
        await self._load_user_profiles()
        await self._load_threat_patterns()

        # Start monitoring thread
        self.monitor_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitor_thread.start()

        logger.info("Threat detection and response system monitoring started")

    async def stop_monitoring(self):
        """Stop threat detection monitoring"""
        self.monitoring_active = False
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=5)
        logger.info("Threat detection and response system monitoring stopped")

    def _generate_event_id(self) -> str:
        """Generate unique threat event ID"""
        return f"threat_{int(time.time() * 1000)}_{hashlib.md5(str(time.time()).encode()).hexdigest()[:8]}"

    def _generate_indicator_id(self) -> str:
        """Generate unique threat indicator ID"""
        return f"indicator_{int(time.time() * 1000)}_{hashlib.md5(str(time.time()).encode()).hexdigest()[:8]}"

    async def analyze_potential_threat(self,
                                     user_id: str,
                                     activity_data: Dict[str, Any],
                                     social_context: SocialContext = SocialContext.UNKNOWN,
                                     emotional_state: Optional[str] = None) -> Optional[ThreatEvent]:
        """
        Analyze activity for potential threats with context awareness.

        Args:
            user_id: User performing the activity
            activity_data: Details of the activity to analyze
            social_context: Current social context
            emotional_state: User's emotional state if known

        Returns:
            ThreatEvent if threat detected, None otherwise
        """
        try:
            # Get user profile for baseline comparison
            user_profile = self.user_profiles.get(user_id)
            if not user_profile:
                user_profile = await self._create_user_profile(user_id)

            # Collect threat indicators
            indicators = []

            # Analyze different threat categories
            indicators.extend(await self._detect_authentication_anomalies(user_id, activity_data, user_profile))
            indicators.extend(await self._detect_behavioral_deviations(user_id, activity_data, user_profile))
            indicators.extend(await self._detect_suspicious_commands(user_id, activity_data, user_profile))
            indicators.extend(await self._detect_rate_limit_violations(user_id, activity_data))
            indicators.extend(await self._detect_pattern_anomalies(user_id, activity_data, user_profile))
            indicators.extend(await self._detect_privilege_escalation(user_id, activity_data, user_profile))

            if not indicators:
                return None

            # Calculate overall risk assessment
            risk_score = self._calculate_risk_score(indicators, social_context, emotional_state, user_profile)
            threat_level = self._determine_threat_level(risk_score, social_context, user_profile)

            # Determine false positive probability
            false_positive_prob = self._calculate_false_positive_probability(
                indicators, user_profile, social_context
            )

            # Skip if likely false positive
            if false_positive_prob > self.false_positive_threshold:
                logger.info(f"Potential threat skipped for {user_id} - likely false positive ({false_positive_prob:.2f})")
                return None

            # Create threat event
            event_id = self._generate_event_id()
            primary_category = self._determine_primary_category(indicators)

            # Get relationship context
            relationship_context = await self._get_relationship_context(user_id, social_context)

            # Determine recommended actions
            recommended_actions = self._determine_response_actions(
                threat_level, primary_category, social_context, user_profile
            )

            threat_event = ThreatEvent(
                event_id=event_id,
                threat_level=threat_level,
                primary_category=primary_category,
                indicators=indicators,
                affected_user=user_id,
                social_context=social_context,
                emotional_state=emotional_state,
                relationship_context=relationship_context,
                risk_score=risk_score,
                false_positive_probability=false_positive_prob,
                recommended_actions=recommended_actions,
                automated_actions_taken=[],
                manual_intervention_required=threat_level in [ThreatLevel.HIGH, ThreatLevel.CRITICAL],
                detected_at=datetime.now()
            )

            # Store threat event
            self.active_threats[event_id] = threat_event
            await self._store_threat_event(threat_event)

            # Execute automated response
            if self.auto_response_enabled:
                await self._execute_automated_response(threat_event)

            # Update statistics
            self.stats['total_threats_detected'] += 1
            self.stats['threats_by_level'][threat_level.value] += 1
            self.stats['threats_by_category'][primary_category.value] += 1

            logger.warning(f"Threat detected: {threat_level.value} - {primary_category.value} for user {user_id}")
            return threat_event

        except Exception as e:
            logger.error(f"Error analyzing potential threat: {e}")
            return None

    async def _detect_authentication_anomalies(self,
                                             user_id: str,
                                             activity_data: Dict[str, Any],
                                             user_profile: UserThreatProfile) -> List[ThreatIndicator]:
        """Detect authentication-related anomalies"""
        indicators = []

        auth_data = activity_data.get('authentication', {})
        if not auth_data:
            return indicators

        # Check for unusual authentication patterns
        failed_attempts = auth_data.get('failed_attempts', 0)
        if failed_attempts > 3:
            indicators.append(ThreatIndicator(
                indicator_id=self._generate_indicator_id(),
                category=ThreatCategory.AUTHENTICATION_ANOMALY,
                description=f"Multiple failed authentication attempts: {failed_attempts}",
                severity_score=min(failed_attempts / 10.0, 1.0),
                confidence_score=0.9,
                timestamp=datetime.now(),
                context_data={'failed_attempts': failed_attempts},
                related_indicators=[]
            ))

        # Check for unusual authentication timing
        auth_time = auth_data.get('authentication_time_ms', 0)
        if auth_time > 30000:  # More than 30 seconds
            indicators.append(ThreatIndicator(
                indicator_id=self._generate_indicator_id(),
                category=ThreatCategory.AUTHENTICATION_ANOMALY,
                description=f"Unusually long authentication time: {auth_time}ms",
                severity_score=min(auth_time / 60000.0, 0.8),
                confidence_score=0.7,
                timestamp=datetime.now(),
                context_data={'auth_time_ms': auth_time},
                related_indicators=[]
            ))

        # Check for authentication from unusual locations/devices
        device_info = auth_data.get('device_info', {})
        if device_info.get('new_device', False):
            indicators.append(ThreatIndicator(
                indicator_id=self._generate_indicator_id(),
                category=ThreatCategory.AUTHENTICATION_ANOMALY,
                description="Authentication from new/unknown device",
                severity_score=0.6,
                confidence_score=0.8,
                timestamp=datetime.now(),
                context_data=device_info,
                related_indicators=[]
            ))

        return indicators

    async def _detect_behavioral_deviations(self,
                                          user_id: str,
                                          activity_data: Dict[str, Any],
                                          user_profile: UserThreatProfile) -> List[ThreatIndicator]:
        """Detect deviations from normal user behavior"""
        indicators = []

        # Check command usage patterns
        commands_used = activity_data.get('commands_used', [])
        unusual_commands = []

        for command in commands_used:
            if command not in user_profile.normal_behaviors:
                unusual_commands.append(command)

        if unusual_commands:
            severity = min(len(unusual_commands) / 10.0, 1.0)
            indicators.append(ThreatIndicator(
                indicator_id=self._generate_indicator_id(),
                category=ThreatCategory.BEHAVIORAL_DEVIATION,
                description=f"Unusual commands used: {', '.join(unusual_commands[:3])}",
                severity_score=severity,
                confidence_score=0.7,
                timestamp=datetime.now(),
                context_data={'unusual_commands': unusual_commands},
                related_indicators=[]
            ))

        # Check activity timing patterns
        current_hour = datetime.now().hour
        normal_hours = user_profile.baseline_patterns.get('active_hours', [])

        if normal_hours and current_hour not in normal_hours:
            # Check how far from normal hours
            min_distance = min(abs(current_hour - hour) for hour in normal_hours)
            if min_distance > 3:  # More than 3 hours from normal activity
                indicators.append(ThreatIndicator(
                    indicator_id=self._generate_indicator_id(),
                    category=ThreatCategory.BEHAVIORAL_DEVIATION,
                    description=f"Activity outside normal hours: {current_hour}:00",
                    severity_score=min(min_distance / 12.0, 0.8),
                    confidence_score=0.6,
                    timestamp=datetime.now(),
                    context_data={'current_hour': current_hour, 'normal_hours': normal_hours},
                    related_indicators=[]
                ))

        # Check interaction pace
        interaction_pace = activity_data.get('interaction_pace', 1.0)
        normal_pace = user_profile.baseline_patterns.get('normal_pace', 1.0)

        pace_deviation = abs(interaction_pace - normal_pace) / normal_pace
        if pace_deviation > 2.0:  # More than 200% deviation
            indicators.append(ThreatIndicator(
                indicator_id=self._generate_indicator_id(),
                category=ThreatCategory.BEHAVIORAL_DEVIATION,
                description=f"Unusual interaction pace: {interaction_pace:.1f}x normal",
                severity_score=min(pace_deviation / 5.0, 0.9),
                confidence_score=0.5,
                timestamp=datetime.now(),
                context_data={'current_pace': interaction_pace, 'normal_pace': normal_pace},
                related_indicators=[]
            ))

        return indicators

    async def _detect_suspicious_commands(self,
                                        user_id: str,
                                        activity_data: Dict[str, Any],
                                        user_profile: UserThreatProfile) -> List[ThreatIndicator]:
        """Detect potentially malicious or suspicious commands"""
        indicators = []

        commands_used = activity_data.get('commands_used', [])
        suspicious_patterns = [
            'delete', 'remove', 'destroy', 'wipe', 'format',
            'admin', 'root', 'sudo', 'chmod', 'chown',
            'password', 'secret', 'key', 'token', 'credential',
            'network', 'connect', 'download', 'upload', 'transfer'
        ]

        for command in commands_used:
            command_lower = command.lower()
            for pattern in suspicious_patterns:
                if pattern in command_lower:
                    # Adjust severity based on user trust level
                    base_severity = 0.7
                    adjusted_severity = base_severity * (1.0 - user_profile.trust_level)

                    indicators.append(ThreatIndicator(
                        indicator_id=self._generate_indicator_id(),
                        category=ThreatCategory.SUSPICIOUS_COMMANDS,
                        description=f"Potentially suspicious command: {command}",
                        severity_score=adjusted_severity,
                        confidence_score=0.6,
                        timestamp=datetime.now(),
                        context_data={'command': command, 'pattern': pattern},
                        related_indicators=[]
                    ))
                    break

        return indicators

    async def _detect_rate_limit_violations(self,
                                          user_id: str,
                                          activity_data: Dict[str, Any]) -> List[ThreatIndicator]:
        """Detect rate limiting violations"""
        indicators = []

        rate_limit_data = activity_data.get('rate_limiting', {})
        if not rate_limit_data:
            return indicators

        violations = rate_limit_data.get('violations', 0)
        if violations > 0:
            indicators.append(ThreatIndicator(
                indicator_id=self._generate_indicator_id(),
                category=ThreatCategory.RATE_LIMIT_VIOLATION,
                description=f"Rate limit violations detected: {violations}",
                severity_score=min(violations / 5.0, 1.0),
                confidence_score=0.95,
                timestamp=datetime.now(),
                context_data={'violations': violations},
                related_indicators=[]
            ))

        # Check for rapid successive operations
        operation_count = activity_data.get('operation_count', 0)
        time_window = activity_data.get('time_window_seconds', 60)

        if operation_count > 20 and time_window < 60:  # More than 20 ops in less than a minute
            indicators.append(ThreatIndicator(
                indicator_id=self._generate_indicator_id(),
                category=ThreatCategory.RATE_LIMIT_VIOLATION,
                description=f"Rapid operations: {operation_count} in {time_window}s",
                severity_score=min(operation_count / 50.0, 0.9),
                confidence_score=0.8,
                timestamp=datetime.now(),
                context_data={'operation_count': operation_count, 'time_window': time_window},
                related_indicators=[]
            ))

        return indicators

    async def _detect_pattern_anomalies(self,
                                      user_id: str,
                                      activity_data: Dict[str, Any],
                                      user_profile: UserThreatProfile) -> List[ThreatIndicator]:
        """Detect anomalies in user patterns using statistical analysis"""
        indicators = []

        # Add current activity to recent activities for pattern analysis
        if user_id not in self.recent_activities:
            self.recent_activities[user_id] = []

        self.recent_activities[user_id].append({
            'timestamp': datetime.now(),
            'data': activity_data
        })

        # Keep only recent activities (last 24 hours)
        cutoff_time = datetime.now() - timedelta(hours=24)
        self.recent_activities[user_id] = [
            activity for activity in self.recent_activities[user_id]
            if activity['timestamp'] > cutoff_time
        ]

        # Calculate anomaly score if we have enough data
        if len(self.recent_activities[user_id]) >= 5:
            anomaly_score = await self._calculate_anomaly_score(user_id, activity_data)

            if anomaly_score > 0.7:  # High anomaly score
                indicators.append(ThreatIndicator(
                    indicator_id=self._generate_indicator_id(),
                    category=ThreatCategory.PATTERN_ANOMALY,
                    description=f"Statistical anomaly detected (score: {anomaly_score:.2f})",
                    severity_score=anomaly_score,
                    confidence_score=0.6,
                    timestamp=datetime.now(),
                    context_data={'anomaly_score': anomaly_score},
                    related_indicators=[]
                ))

        return indicators

    async def _detect_privilege_escalation(self,
                                         user_id: str,
                                         activity_data: Dict[str, Any],
                                         user_profile: UserThreatProfile) -> List[ThreatIndicator]:
        """Detect potential privilege escalation attempts"""
        indicators = []

        # Check for privilege escalation keywords
        escalation_patterns = [
            'admin', 'administrator', 'root', 'sudo', 'su',
            'privilege', 'elevation', 'escalate', 'permissions'
        ]

        activity_text = json.dumps(activity_data).lower()
        found_patterns = [pattern for pattern in escalation_patterns if pattern in activity_text]

        if found_patterns:
            severity = min(len(found_patterns) / 3.0, 0.9)
            indicators.append(ThreatIndicator(
                indicator_id=self._generate_indicator_id(),
                category=ThreatCategory.PRIVILEGE_ESCALATION,
                description=f"Potential privilege escalation: {', '.join(found_patterns)}",
                severity_score=severity,
                confidence_score=0.7,
                timestamp=datetime.now(),
                context_data={'escalation_patterns': found_patterns},
                related_indicators=[]
            ))

        # Check for attempts to access restricted resources
        resources_accessed = activity_data.get('resources_accessed', [])
        restricted_resources = [
            '/etc', '/root', '/admin', '/system', '/config',
            'password', 'secret', 'key', 'token'
        ]

        restricted_access = []
        for resource in resources_accessed:
            resource_lower = str(resource).lower()
            for restricted in restricted_resources:
                if restricted in resource_lower:
                    restricted_access.append(resource)
                    break

        if restricted_access:
            indicators.append(ThreatIndicator(
                indicator_id=self._generate_indicator_id(),
                category=ThreatCategory.PRIVILEGE_ESCALATION,
                description=f"Access to restricted resources: {', '.join(restricted_access[:3])}",
                severity_score=min(len(restricted_access) / 5.0, 1.0),
                confidence_score=0.8,
                timestamp=datetime.now(),
                context_data={'restricted_access': restricted_access},
                related_indicators=[]
            ))

        return indicators

    def _calculate_risk_score(self,
                            indicators: List[ThreatIndicator],
                            social_context: SocialContext,
                            emotional_state: Optional[str],
                            user_profile: UserThreatProfile) -> float:
        """Calculate overall risk score for the threat"""
        if not indicators:
            return 0.0

        # Base risk from indicators
        base_risk = statistics.mean([
            indicator.severity_score * indicator.confidence_score
            for indicator in indicators
        ])

        # Social context modifiers
        context_modifiers = {
            SocialContext.SOLO_WORK: 1.0,
            SocialContext.COLLABORATION: 0.7,  # Lower risk when collaborating
            SocialContext.DEMONSTRATION: 0.5,  # Much lower risk during demos
            SocialContext.TRAINING: 0.3,      # Lowest risk during training
            SocialContext.EMERGENCY: 1.5,     # Higher risk during emergencies
            SocialContext.UNKNOWN: 1.2        # Slightly higher risk when context unknown
        }

        context_modifier = context_modifiers.get(social_context, 1.0)

        # Emotional state modifiers
        emotional_modifiers = {
            'stressed': 1.3,
            'frustrated': 1.2,
            'excited': 0.9,
            'calm': 0.8,
            'tired': 1.1
        }

        emotional_modifier = emotional_modifiers.get(emotional_state, 1.0) if emotional_state else 1.0

        # User trust level modifier
        trust_modifier = 1.0 - (user_profile.trust_level * 0.5)  # Higher trust = lower risk

        # Calculate final risk score
        final_risk = base_risk * context_modifier * emotional_modifier * trust_modifier

        return min(final_risk, 1.0)

    def _determine_threat_level(self,
                              risk_score: float,
                              social_context: SocialContext,
                              user_profile: UserThreatProfile) -> ThreatLevel:
        """Determine threat level based on risk score and context"""
        # Adjust thresholds based on user sensitivity
        sensitivity = user_profile.threat_sensitivity

        critical_threshold = 0.9 * (2.0 - sensitivity)  # Lower threshold for sensitive users
        high_threshold = 0.7 * (2.0 - sensitivity)
        medium_threshold = 0.4 * (2.0 - sensitivity)
        low_threshold = 0.2 * (2.0 - sensitivity)

        if risk_score >= critical_threshold:
            return ThreatLevel.CRITICAL
        elif risk_score >= high_threshold:
            return ThreatLevel.HIGH
        elif risk_score >= medium_threshold:
            return ThreatLevel.MEDIUM
        elif risk_score >= low_threshold:
            return ThreatLevel.LOW
        else:
            return ThreatLevel.MINIMAL

    def _calculate_false_positive_probability(self,
                                            indicators: List[ThreatIndicator],
                                            user_profile: UserThreatProfile,
                                            social_context: SocialContext) -> float:
        """Calculate probability that this is a false positive"""
        if not indicators:
            return 1.0

        # Base false positive rate from confidence scores
        avg_confidence = statistics.mean([ind.confidence_score for ind in indicators])
        base_fp_rate = 1.0 - avg_confidence

        # Context adjustments
        context_fp_adjustments = {
            SocialContext.DEMONSTRATION: 0.8,  # High FP rate during demos
            SocialContext.TRAINING: 0.9,      # Very high FP rate during training
            SocialContext.COLLABORATION: 0.3,  # Moderate FP rate when collaborating
            SocialContext.EMERGENCY: -0.2,    # Lower FP rate during emergencies
            SocialContext.SOLO_WORK: 0.0,     # Neutral
            SocialContext.UNKNOWN: 0.1        # Slightly higher FP rate
        }

        context_adjustment = context_fp_adjustments.get(social_context, 0.0)

        # User trust level adjustment (trusted users have higher FP rates)
        trust_adjustment = user_profile.trust_level * 0.3

        # Known anomalies adjustment
        known_patterns = sum(1 for ind in indicators
                           if ind.description in user_profile.known_anomalies)
        known_adjustment = (known_patterns / len(indicators)) * 0.5 if indicators else 0

        final_fp_rate = base_fp_rate + context_adjustment + trust_adjustment + known_adjustment
        return min(max(final_fp_rate, 0.0), 1.0)

    def _determine_primary_category(self, indicators: List[ThreatIndicator]) -> ThreatCategory:
        """Determine primary threat category from indicators"""
        if not indicators:
            return ThreatCategory.PATTERN_ANOMALY

        # Weight by severity * confidence
        category_weights = {}
        for indicator in indicators:
            weight = indicator.severity_score * indicator.confidence_score
            category_weights[indicator.category] = category_weights.get(indicator.category, 0) + weight

        return max(category_weights.keys(), key=lambda cat: category_weights[cat])

    def _determine_response_actions(self,
                                  threat_level: ThreatLevel,
                                  category: ThreatCategory,
                                  social_context: SocialContext,
                                  user_profile: UserThreatProfile) -> List[ResponseAction]:
        """Determine appropriate response actions"""
        actions = []

        # Always log the event
        actions.append(ResponseAction.LOG_EVENT)

        if threat_level == ThreatLevel.CRITICAL:
            actions.extend([
                ResponseAction.EMERGENCY_LOCKDOWN,
                ResponseAction.CONTACT_ADMIN,
                ResponseAction.QUARANTINE_SESSION
            ])
        elif threat_level == ThreatLevel.HIGH:
            actions.extend([
                ResponseAction.BLOCK_ACTION,
                ResponseAction.REQUIRE_VERIFICATION,
                ResponseAction.ALERT_USER
            ])
        elif threat_level == ThreatLevel.MEDIUM:
            actions.extend([
                ResponseAction.REQUIRE_VERIFICATION,
                ResponseAction.ALERT_USER,
                ResponseAction.MONITOR
            ])
        elif threat_level == ThreatLevel.LOW:
            actions.extend([
                ResponseAction.MONITOR,
                ResponseAction.ALERT_USER
            ])
        else:  # MINIMAL
            actions.append(ResponseAction.MONITOR)

        # Adjust based on social context
        if social_context in [SocialContext.DEMONSTRATION, SocialContext.TRAINING]:
            # Remove disruptive actions during demos/training
            disruptive_actions = [
                ResponseAction.EMERGENCY_LOCKDOWN,
                ResponseAction.BLOCK_ACTION,
                ResponseAction.QUARANTINE_SESSION
            ]
            actions = [action for action in actions if action not in disruptive_actions]

        return actions

    async def _execute_automated_response(self, threat_event: ThreatEvent):
        """Execute automated response actions"""
        start_time = time.time()

        for action in threat_event.recommended_actions:
            try:
                success = await self._execute_response_action(action, threat_event)
                if success:
                    threat_event.automated_actions_taken.append(action)
                    self.stats['automated_responses'] += 1
            except Exception as e:
                logger.error(f"Error executing response action {action.value}: {e}")

        response_time = (time.time() - start_time) * 1000
        self.stats['response_times_ms'].append(response_time)

        # Update threat event
        await self._update_threat_event(threat_event)

    async def _execute_response_action(self, action: ResponseAction, threat_event: ThreatEvent) -> bool:
        """Execute a specific response action"""
        try:
            if action == ResponseAction.MONITOR:
                # Increase monitoring level for this user
                logger.info(f"Increased monitoring for user {threat_event.affected_user}")
                return True

            elif action == ResponseAction.LOG_EVENT:
                # Log to security logger if available
                if self.security_logger:
                    await self.security_logger.log_security_event(
                        event_type="THREAT_DETECTED",
                        severity=threat_event.threat_level.value.upper(),
                        details={
                            'threat_event_id': threat_event.event_id,
                            'category': threat_event.primary_category.value,
                            'affected_user': threat_event.affected_user,
                            'risk_score': threat_event.risk_score
                        }
                    )
                return True

            elif action == ResponseAction.ALERT_USER:
                # Send alert to user (implementation depends on notification system)
                logger.warning(f"SECURITY ALERT for {threat_event.affected_user}: {threat_event.primary_category.value}")
                return True

            elif action == ResponseAction.REQUIRE_VERIFICATION:
                # Trigger additional authentication (would integrate with auth system)
                if self.auth_system:
                    # Implementation would depend on authentication system interface
                    logger.info(f"Additional verification required for {threat_event.affected_user}")
                return True

            elif action == ResponseAction.BLOCK_ACTION:
                # Block the current action (implementation specific)
                logger.warning(f"Action blocked for {threat_event.affected_user} due to threat detection")
                return True

            elif action == ResponseAction.QUARANTINE_SESSION:
                # Quarantine user session (implementation specific)
                logger.critical(f"Session quarantined for {threat_event.affected_user}")
                return True

            elif action == ResponseAction.EMERGENCY_LOCKDOWN:
                # Emergency system lockdown (implementation specific)
                logger.critical("EMERGENCY LOCKDOWN activated due to critical threat")
                return True

            elif action == ResponseAction.CONTACT_ADMIN:
                # Contact system administrator (implementation specific)
                logger.critical(f"Administrator contacted for critical threat: {threat_event.event_id}")
                return True

            return False

        except Exception as e:
            logger.error(f"Error executing {action.value}: {e}")
            return False

    async def _calculate_anomaly_score(self, user_id: str, current_activity: Dict[str, Any]) -> float:
        """Calculate anomaly score using statistical analysis"""
        try:
            recent_activities = self.recent_activities.get(user_id, [])
            if len(recent_activities) < 5:
                return 0.0

            # Extract numerical features for comparison
            current_features = self._extract_numerical_features(current_activity)
            historical_features = [
                self._extract_numerical_features(activity['data'])
                for activity in recent_activities[:-1]  # Exclude current activity
            ]

            if not current_features or not historical_features:
                return 0.0

            # Calculate deviations for each feature
            anomaly_scores = []
            for feature_name, current_value in current_features.items():
                historical_values = [
                    features.get(feature_name, 0) for features in historical_features
                    if feature_name in features
                ]

                if len(historical_values) >= 3:
                    mean_val = statistics.mean(historical_values)
                    std_val = statistics.stdev(historical_values) if len(historical_values) > 1 else 1.0

                    if std_val > 0:
                        z_score = abs(current_value - mean_val) / std_val
                        anomaly_scores.append(min(z_score / 3.0, 1.0))  # Normalize to 0-1

            return statistics.mean(anomaly_scores) if anomaly_scores else 0.0

        except Exception as e:
            logger.error(f"Error calculating anomaly score: {e}")
            return 0.0

    def _extract_numerical_features(self, activity_data: Dict[str, Any]) -> Dict[str, float]:
        """Extract numerical features from activity data for anomaly detection"""
        features = {}

        # Command count
        commands = activity_data.get('commands_used', [])
        features['command_count'] = len(commands)

        # Activity duration
        features['session_duration'] = activity_data.get('session_duration', 0)

        # Interaction pace
        features['interaction_pace'] = activity_data.get('interaction_pace', 1.0)

        # Error count
        features['error_count'] = activity_data.get('error_count', 0)

        # Operation count
        features['operation_count'] = activity_data.get('operation_count', 0)

        # Authentication metrics
        auth_data = activity_data.get('authentication', {})
        features['auth_time'] = auth_data.get('authentication_time_ms', 0)
        features['failed_attempts'] = auth_data.get('failed_attempts', 0)

        return features

    async def _get_relationship_context(self, user_id: str, social_context: SocialContext) -> Dict[str, Any]:
        """Get relationship context for threat assessment"""
        # This would integrate with social intelligence system
        # For now, return basic context based on known relationships

        relationship_context = {
            'user_id': user_id,
            'social_context': social_context.value,
            'trust_indicators': [],
            'relationship_type': 'unknown'
        }

        # Check for known relationships (Josh, Reneille, etc.)
        known_relationships = {
            'josh': {'type': 'colleague', 'trust_level': 0.9},
            'reneille': {'type': 'colleague', 'trust_level': 0.9},
            'cj': {'type': 'primary_user', 'trust_level': 1.0}
        }

        user_lower = user_id.lower()
        if user_lower in known_relationships:
            rel_info = known_relationships[user_lower]
            relationship_context['relationship_type'] = rel_info['type']
            relationship_context['trust_level'] = rel_info['trust_level']

        return relationship_context

    async def _create_user_profile(self, user_id: str) -> UserThreatProfile:
        """Create a new user threat profile"""
        profile = UserThreatProfile(
            user_id=user_id,
            baseline_patterns={
                'active_hours': list(range(9, 18)),  # Default work hours
                'normal_pace': 1.0,
                'typical_session_duration': 1800
            },
            normal_behaviors=[
                'help', 'status', 'list', 'search', 'info',
                'read', 'write', 'edit', 'save', 'open'
            ],
            known_anomalies=[],
            trust_level=0.5,  # Default medium trust
            relationship_context={},
            threat_sensitivity=1.0,  # Default sensitivity
            last_updated=datetime.now()
        )

        self.user_profiles[user_id] = profile
        await self._store_user_profile(profile)
        return profile

    async def get_active_threats(self, user_id: Optional[str] = None) -> List[ThreatEvent]:
        """Get list of active threats"""
        threats = list(self.active_threats.values())

        if user_id:
            threats = [threat for threat in threats if threat.affected_user == user_id]

        # Sort by risk score descending
        threats.sort(key=lambda t: t.risk_score, reverse=True)
        return threats

    async def resolve_threat(self, event_id: str, resolution: str = "resolved") -> bool:
        """Mark a threat as resolved"""
        if event_id in self.active_threats:
            threat = self.active_threats[event_id]
            threat.status = resolution
            threat.resolved_at = datetime.now()

            # Update in database
            await self._update_threat_event(threat)

            # Remove from active threats if resolved
            if resolution in ['resolved', 'false_positive']:
                del self.active_threats[event_id]

                if resolution == 'false_positive':
                    self.stats['false_positives'] += 1

            return True

        return False

    def get_threat_statistics(self) -> Dict[str, Any]:
        """Get threat detection statistics"""
        stats = self.stats.copy()

        # Add current state
        stats['active_threats'] = len(self.active_threats)
        stats['monitored_users'] = len(self.user_profiles)
        stats['monitoring_active'] = self.monitoring_active

        # Calculate average response time
        if self.stats['response_times_ms']:
            stats['avg_response_time_ms'] = statistics.mean(self.stats['response_times_ms'])
        else:
            stats['avg_response_time_ms'] = 0

        return stats

    def _monitoring_loop(self):
        """Background monitoring loop"""
        while self.monitoring_active:
            try:
                # Periodic tasks
                asyncio.run(self._update_threat_patterns())
                asyncio.run(self._cleanup_old_data())

                # Sleep for monitoring interval
                time.sleep(60)  # Check every minute

            except Exception as e:
                logger.error(f"Error in threat monitoring loop: {e}")

    async def _update_threat_patterns(self):
        """Update threat detection patterns based on learning"""
        # This would analyze resolved threats to improve detection
        # For now, just log that pattern update occurred
        logger.debug("Threat pattern update cycle completed")

    async def _cleanup_old_data(self):
        """Clean up old threat data"""
        try:
            cutoff_time = datetime.now() - timedelta(days=30)

            # Remove old resolved threats from active threats
            expired_threats = [
                event_id for event_id, threat in self.active_threats.items()
                if threat.resolved_at and threat.resolved_at < cutoff_time
            ]

            for event_id in expired_threats:
                del self.active_threats[event_id]

            # Clean up recent activities buffer
            for user_id in self.recent_activities:
                self.recent_activities[user_id] = [
                    activity for activity in self.recent_activities[user_id]
                    if activity['timestamp'] > cutoff_time
                ]

        except Exception as e:
            logger.error(f"Error cleaning up old threat data: {e}")

    # Database operations
    async def _store_threat_event(self, threat_event: ThreatEvent):
        """Store threat event in database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO threat_events (
                    event_id, threat_level, primary_category, affected_user,
                    social_context, emotional_state, relationship_context,
                    risk_score, false_positive_probability, recommended_actions,
                    automated_actions_taken, manual_intervention_required,
                    detected_at, resolved_at, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                threat_event.event_id,
                threat_event.threat_level.value,
                threat_event.primary_category.value,
                threat_event.affected_user,
                threat_event.social_context.value,
                threat_event.emotional_state,
                json.dumps(threat_event.relationship_context),
                threat_event.risk_score,
                threat_event.false_positive_probability,
                json.dumps([action.value for action in threat_event.recommended_actions]),
                json.dumps([action.value for action in threat_event.automated_actions_taken]),
                threat_event.manual_intervention_required,
                threat_event.detected_at.isoformat(),
                threat_event.resolved_at.isoformat() if threat_event.resolved_at else None,
                threat_event.status
            ))

            # Store indicators
            for indicator in threat_event.indicators:
                cursor.execute("""
                    INSERT INTO threat_indicators (
                        indicator_id, event_id, category, description,
                        severity_score, confidence_score, timestamp,
                        context_data, related_indicators
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    indicator.indicator_id,
                    threat_event.event_id,
                    indicator.category.value,
                    indicator.description,
                    indicator.severity_score,
                    indicator.confidence_score,
                    indicator.timestamp.isoformat(),
                    json.dumps(indicator.context_data),
                    json.dumps(indicator.related_indicators)
                ))

            conn.commit()

    async def _update_threat_event(self, threat_event: ThreatEvent):
        """Update threat event in database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE threat_events
                SET automated_actions_taken = ?, resolved_at = ?, status = ?
                WHERE event_id = ?
            """, (
                json.dumps([action.value for action in threat_event.automated_actions_taken]),
                threat_event.resolved_at.isoformat() if threat_event.resolved_at else None,
                threat_event.status,
                threat_event.event_id
            ))
            conn.commit()

    async def _store_user_profile(self, profile: UserThreatProfile):
        """Store user threat profile in database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO user_threat_profiles (
                    user_id, baseline_patterns, normal_behaviors, known_anomalies,
                    trust_level, relationship_context, threat_sensitivity, last_updated
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                profile.user_id,
                json.dumps(profile.baseline_patterns),
                json.dumps(profile.normal_behaviors),
                json.dumps(profile.known_anomalies),
                profile.trust_level,
                json.dumps(profile.relationship_context),
                profile.threat_sensitivity,
                profile.last_updated.isoformat()
            ))
            conn.commit()

    async def _load_user_profiles(self):
        """Load user profiles from database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM user_threat_profiles")

                for row in cursor.fetchall():
                    profile = UserThreatProfile(
                        user_id=row[0],
                        baseline_patterns=json.loads(row[1]),
                        normal_behaviors=json.loads(row[2]),
                        known_anomalies=json.loads(row[3]),
                        trust_level=row[4],
                        relationship_context=json.loads(row[5]),
                        threat_sensitivity=row[6],
                        last_updated=datetime.fromisoformat(row[7])
                    )
                    self.user_profiles[profile.user_id] = profile

        except Exception as e:
            logger.error(f"Error loading user profiles: {e}")

    async def _load_threat_patterns(self):
        """Load threat patterns from database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM threat_patterns")

                for row in cursor.fetchall():
                    pattern_id = row[0]
                    pattern_type = row[1]
                    pattern_data = json.loads(row[2])

                    if pattern_type not in self.threat_patterns:
                        self.threat_patterns[pattern_type] = {}

                    self.threat_patterns[pattern_type][pattern_id] = pattern_data

        except Exception as e:
            logger.error(f"Error loading threat patterns: {e}")


# Integration helper function
async def create_integrated_threat_detection(
    security_logger=None,
    auth_system=None,
    social_intelligence=None,
    db_path: str = "threat_detection.db"
) -> ThreatDetectionResponse:
    """
    Create integrated threat detection system

    Returns configured and initialized system
    """
    threat_system = ThreatDetectionResponse(
        db_path=db_path,
        security_logger=security_logger,
        auth_system=auth_system,
        social_intelligence=social_intelligence
    )

    # Start monitoring
    await threat_system.start_monitoring()

    return threat_system


# Usage example and demonstration
async def demo_threat_detection():
    """Demonstration of threat detection system"""
    threat_system = ThreatDetectionResponse()
    await threat_system.start_monitoring()

    try:
        # Simulate normal activity
        normal_activity = {
            'commands_used': ['help', 'status', 'list'],
            'session_duration': 1800,
            'interaction_pace': 1.0,
            'operation_count': 5,
            'authentication': {
                'failed_attempts': 0,
                'authentication_time_ms': 2000
            }
        }

        result = await threat_system.analyze_potential_threat(
            "demo_user",
            normal_activity,
            SocialContext.SOLO_WORK,
            "calm"
        )

        if result:
            print(f"Threat detected: {result.threat_level.value}")
        else:
            print("No threat detected for normal activity")

        # Simulate suspicious activity
        suspicious_activity = {
            'commands_used': ['delete', 'admin', 'root', 'password'],
            'session_duration': 60,  # Very short session
            'interaction_pace': 5.0,  # Very fast pace
            'operation_count': 50,   # Many operations
            'authentication': {
                'failed_attempts': 5,
                'authentication_time_ms': 45000
            },
            'resources_accessed': ['/etc/passwd', '/root/.ssh'],
            'time_window_seconds': 30
        }

        threat = await threat_system.analyze_potential_threat(
            "demo_user",
            suspicious_activity,
            SocialContext.UNKNOWN,
            "stressed"
        )

        if threat:
            print(f"Threat detected: {threat.threat_level.value} - {threat.primary_category.value}")
            print(f"Risk score: {threat.risk_score:.2f}")
            print(f"Indicators: {len(threat.indicators)}")
            print(f"Recommended actions: {[a.value for a in threat.recommended_actions]}")

        # Get statistics
        stats = threat_system.get_threat_statistics()
        print(f"Threat statistics: {stats}")

    finally:
        await threat_system.stop_monitoring()

if __name__ == "__main__":
    asyncio.run(demo_threat_detection())