#!/usr/bin/env python3
"""
Change Rate Limiting System
Controls the speed and magnitude of changes across AI systems to prevent
rapid degradation, instability, and unsafe behavioral shifts
"""

import asyncio
import json
import sqlite3
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from collections import defaultdict, deque
import logging

# Configure logging for rate limiting
logging.basicConfig(level=logging.INFO)
rate_limiter_logger = logging.getLogger('PennyRateLimiter')

class ChangeType(Enum):
    """Types of changes that can be rate limited"""
    PERSONALITY_EVOLUTION = "personality_evolution"
    CODE_GENERATION = "code_generation"
    RESEARCH_QUERY = "research_query"
    MEMORY_UPDATE = "memory_update"
    SYSTEM_CONFIG = "system_config"
    BEHAVIORAL_ADAPTATION = "behavioral_adaptation"
    SASS_ADJUSTMENT = "sass_adjustment"

class RiskLevel(Enum):
    """Risk levels for different types of changes"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class ChangeRequest:
    """Represents a request for system change"""
    request_id: str
    system: str
    change_type: ChangeType
    change_magnitude: float
    change_details: Dict[str, Any]
    requested_by: str
    risk_level: RiskLevel
    timestamp: datetime
    context: Dict[str, Any]

@dataclass
class ChangeValidationResult:
    """Result of change validation"""
    approved: bool
    reason: str
    cumulative_change_today: float
    proposed_new_total: float
    adjusted_magnitude: Optional[float]
    cooldown_remaining: Optional[timedelta]
    risk_assessment: RiskLevel
    requires_approval: bool
    alternative_suggestions: List[str]

@dataclass
class RateLimitConfig:
    """Configuration for rate limiting a specific system/change type"""
    max_daily_change: float
    max_single_change: float
    cooldown_period_seconds: int
    burst_allowance: int
    risk_escalation_threshold: float
    approval_required_threshold: float

class ChangeRateLimiter:
    """
    Controls the rate of changes across AI systems to prevent:
    - Rapid personality shifts that could indicate instability
    - Resource abuse through excessive operations
    - Cascading failures from too many simultaneous changes
    - Unsafe behavioral adaptations beyond acceptable limits
    """

    def __init__(self, db_path: str = "data/rate_limiting.db"):
        self.db_path = db_path
        self.rate_limiter_logger = rate_limiter_logger

        # Rate limiting configurations for each system/change type
        self.rate_limit_configs = {
            ('personality_evolution', ChangeType.PERSONALITY_EVOLUTION): RateLimitConfig(
                max_daily_change=0.25,        # Max 25% personality shift per day
                max_single_change=0.1,        # Max 10% change in single operation
                cooldown_period_seconds=1800, # 30 minutes between significant changes
                burst_allowance=3,            # Allow 3 small changes in succession
                risk_escalation_threshold=0.15, # Escalate to human review above 15%
                approval_required_threshold=0.2  # Require approval above 20%
            ),
            ('personality_evolution', ChangeType.SASS_ADJUSTMENT): RateLimitConfig(
                max_daily_change=1.0,         # More lenient for sass adjustments
                max_single_change=0.3,        # Allow significant sass changes
                cooldown_period_seconds=300,  # 5 minutes between sass changes
                burst_allowance=5,
                risk_escalation_threshold=0.5,
                approval_required_threshold=0.8
            ),
            ('code_generation', ChangeType.CODE_GENERATION): RateLimitConfig(
                max_daily_change=10.0,        # Max 10 code generations per day
                max_single_change=1.0,        # Each generation counts as 1
                cooldown_period_seconds=180,  # 3 minutes between generations
                burst_allowance=2,            # Allow 2 quick generations
                risk_escalation_threshold=5.0,
                approval_required_threshold=1.0  # All code generation requires approval
            ),
            ('research', ChangeType.RESEARCH_QUERY): RateLimitConfig(
                max_daily_change=50.0,        # Max 50 research queries per day
                max_single_change=1.0,        # Each query counts as 1
                cooldown_period_seconds=60,   # 1 minute between queries
                burst_allowance=10,           # Allow burst of quick queries
                risk_escalation_threshold=30.0,
                approval_required_threshold=100.0  # No approval required for research
            ),
            ('memory_system', ChangeType.MEMORY_UPDATE): RateLimitConfig(
                max_daily_change=100.0,       # Max 100 memory updates per day
                max_single_change=5.0,        # Allow batch updates
                cooldown_period_seconds=10,   # 10 seconds between updates
                burst_allowance=20,
                risk_escalation_threshold=50.0,
                approval_required_threshold=200.0
            ),
            ('system_config', ChangeType.SYSTEM_CONFIG): RateLimitConfig(
                max_daily_change=5.0,         # Very limited system config changes
                max_single_change=1.0,
                cooldown_period_seconds=3600, # 1 hour between config changes
                burst_allowance=1,            # No burst allowance for config
                risk_escalation_threshold=1.0,
                approval_required_threshold=1.0  # All config changes require approval
            )
        }

        # Track changes by system and time period
        self.change_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.daily_change_totals: Dict[str, Dict[str, float]] = defaultdict(lambda: defaultdict(float))
        self.burst_tracking: Dict[str, List[datetime]] = defaultdict(list)
        self.last_change_times: Dict[str, datetime] = {}

        # Risk assessment tracking
        self.risk_escalations: List[Dict[str, Any]] = []
        self.emergency_brakes_engaged: Dict[str, bool] = defaultdict(bool)

        # Initialize database
        self._init_rate_limiting_database()

        # Load historical data
        self._load_change_history()

    def _init_rate_limiting_database(self):
        """Initialize rate limiting database"""
        with sqlite3.connect(self.db_path) as conn:
            # Change requests table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS change_requests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    request_id TEXT UNIQUE NOT NULL,
                    system TEXT NOT NULL,
                    change_type TEXT NOT NULL,
                    change_magnitude REAL NOT NULL,
                    change_details TEXT,
                    requested_by TEXT,
                    risk_level TEXT,
                    approved BOOLEAN,
                    reason TEXT,
                    context TEXT
                )
            ''')

            # Daily change tracking
            conn.execute('''
                CREATE TABLE IF NOT EXISTS daily_change_summary (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date DATE NOT NULL,
                    system TEXT NOT NULL,
                    change_type TEXT NOT NULL,
                    total_changes REAL NOT NULL,
                    num_requests INTEGER NOT NULL,
                    avg_magnitude REAL,
                    max_magnitude REAL,
                    risk_escalations INTEGER DEFAULT 0,
                    approvals_required INTEGER DEFAULT 0
                )
            ''')

            # Risk escalations table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS risk_escalations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    system TEXT NOT NULL,
                    change_type TEXT NOT NULL,
                    escalation_reason TEXT NOT NULL,
                    risk_level TEXT NOT NULL,
                    change_magnitude REAL,
                    cumulative_daily_change REAL,
                    resolution_status TEXT DEFAULT 'pending',
                    human_review_required BOOLEAN DEFAULT TRUE
                )
            ''')

            # Emergency brake events
            conn.execute('''
                CREATE TABLE IF NOT EXISTS emergency_brake_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    system TEXT NOT NULL,
                    trigger_reason TEXT NOT NULL,
                    change_magnitude_attempted REAL,
                    cumulative_change_at_trigger REAL,
                    brake_duration_seconds INTEGER,
                    resolution_timestamp DATETIME,
                    resolved_by TEXT
                )
            ''')

            conn.commit()

    def _load_change_history(self):
        """Load recent change history for rate limit calculations"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Load last 7 days of change requests
                cursor = conn.execute('''
                    SELECT system, change_type, change_magnitude, timestamp, approved
                    FROM change_requests
                    WHERE timestamp > datetime('now', '-7 days')
                    ORDER BY timestamp ASC
                ''')

                for row in cursor.fetchall():
                    system, change_type, magnitude, timestamp, approved = row
                    if approved:  # Only count approved changes toward limits
                        key = f"{system}:{change_type}"
                        self.change_history[key].append({
                            'magnitude': magnitude,
                            'timestamp': datetime.fromisoformat(timestamp),
                            'system': system,
                            'change_type': change_type
                        })

                # Calculate daily totals
                self._recalculate_daily_totals()

        except Exception as e:
            self.rate_limiter_logger.error(f"Failed to load change history: {e}")

    def _recalculate_daily_totals(self):
        """Recalculate daily change totals from history"""
        self.daily_change_totals.clear()

        for key, changes in self.change_history.items():
            for change in changes:
                date = change['timestamp'].date()
                system = change['system']
                change_type = change['change_type']
                magnitude = change['magnitude']

                day_key = f"{system}:{change_type}:{date.isoformat()}"
                self.daily_change_totals[system][day_key] += magnitude

    async def validate_change_request(self, system: str, change_type: ChangeType,
                                    change_magnitude: float, requested_by: str = "system",
                                    context: Dict[str, Any] = None) -> ChangeValidationResult:
        """
        Validate if a change request is within acceptable rate limits
        """
        context = context or {}
        config_key = (system, change_type)
        config = self.rate_limit_configs.get(config_key)

        if not config:
            # Use default restrictive config for unknown system/change combinations
            config = RateLimitConfig(
                max_daily_change=1.0,
                max_single_change=0.1,
                cooldown_period_seconds=3600,
                burst_allowance=1,
                risk_escalation_threshold=0.5,
                approval_required_threshold=0.8
            )
            self.rate_limiter_logger.warning(f"Using default config for unknown system/change: {system}/{change_type}")

        # Generate request ID
        request_id = self._generate_request_id(system, change_type, change_magnitude)

        # Check if emergency brake is engaged
        if self.emergency_brakes_engaged.get(system, False):
            return ChangeValidationResult(
                approved=False,
                reason=f"Emergency brake engaged for {system} - changes temporarily disabled",
                cumulative_change_today=0,
                proposed_new_total=0,
                adjusted_magnitude=None,
                cooldown_remaining=None,
                risk_assessment=RiskLevel.CRITICAL,
                requires_approval=True,
                alternative_suggestions=["Wait for emergency brake release", "Contact system administrator"]
            )

        # Calculate current daily usage
        today = datetime.now().date()
        daily_key = f"{system}:{change_type.value}:{today.isoformat()}"
        cumulative_change_today = self.daily_change_totals[system].get(daily_key, 0.0)

        # Basic validation checks
        validation_result = ChangeValidationResult(
            approved=True,
            reason="Within acceptable limits",
            cumulative_change_today=cumulative_change_today,
            proposed_new_total=cumulative_change_today + change_magnitude,
            adjusted_magnitude=None,
            cooldown_remaining=None,
            risk_assessment=RiskLevel.LOW,
            requires_approval=False,
            alternative_suggestions=[]
        )

        # Check single change magnitude limit
        if change_magnitude > config.max_single_change:
            # Try to suggest adjusted magnitude
            adjusted_magnitude = config.max_single_change * 0.9  # 90% of limit
            validation_result.adjusted_magnitude = adjusted_magnitude

            if change_magnitude > config.max_single_change * 2:
                # Far too large, reject entirely
                validation_result.approved = False
                validation_result.reason = f"Single change ({change_magnitude}) far exceeds limit ({config.max_single_change})"
                validation_result.risk_assessment = RiskLevel.HIGH
                validation_result.alternative_suggestions = [
                    f"Reduce change magnitude to {adjusted_magnitude}",
                    "Split change into multiple smaller operations",
                    "Request manual approval for large change"
                ]
            else:
                # Suggest reduction
                validation_result.reason = f"Single change ({change_magnitude}) exceeds limit ({config.max_single_change}), suggesting reduction"
                validation_result.risk_assessment = RiskLevel.MEDIUM

        # Check daily cumulative limit
        if cumulative_change_today + change_magnitude > config.max_daily_change:
            remaining_budget = config.max_daily_change - cumulative_change_today

            if remaining_budget <= 0:
                validation_result.approved = False
                validation_result.reason = f"Daily limit exceeded. Used: {cumulative_change_today}, Limit: {config.max_daily_change}"
                validation_result.risk_assessment = RiskLevel.HIGH
                validation_result.alternative_suggestions = [
                    "Wait until tomorrow for limit reset",
                    "Request emergency approval for critical change",
                    "Use alternative system if available"
                ]
            elif change_magnitude > remaining_budget:
                # Suggest using remaining budget
                validation_result.adjusted_magnitude = remaining_budget * 0.9
                validation_result.reason = f"Partial approval: {remaining_budget} budget remaining"
                validation_result.risk_assessment = RiskLevel.MEDIUM

        # Check cooldown period
        last_change_time = self.last_change_times.get(f"{system}:{change_type.value}")
        if last_change_time:
            time_since_last = datetime.now() - last_change_time
            cooldown_seconds = config.cooldown_period_seconds

            # Check burst allowance
            burst_key = f"{system}:{change_type.value}"
            recent_bursts = self.burst_tracking.get(burst_key, [])

            # Clean old burst entries
            cutoff_time = datetime.now() - timedelta(seconds=cooldown_seconds)
            recent_bursts = [t for t in recent_bursts if t > cutoff_time]
            self.burst_tracking[burst_key] = recent_bursts

            if len(recent_bursts) >= config.burst_allowance and time_since_last.total_seconds() < cooldown_seconds:
                remaining_cooldown = timedelta(seconds=cooldown_seconds) - time_since_last
                validation_result.approved = False
                validation_result.reason = f"Cooldown period active. Burst allowance ({config.burst_allowance}) exhausted."
                validation_result.cooldown_remaining = remaining_cooldown
                validation_result.risk_assessment = RiskLevel.MEDIUM
                validation_result.alternative_suggestions = [
                    f"Wait {remaining_cooldown.total_seconds():.0f} seconds",
                    "Queue request for later execution"
                ]

        # Risk assessment
        risk_level = self._assess_change_risk(system, change_type, change_magnitude, cumulative_change_today, config)
        validation_result.risk_assessment = risk_level

        # Check if approval required
        if (change_magnitude > config.approval_required_threshold or
            risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]):
            validation_result.requires_approval = True
            validation_result.reason += " - Human approval required"

        # Check for risk escalation
        if (change_magnitude > config.risk_escalation_threshold or
            cumulative_change_today + change_magnitude > config.risk_escalation_threshold):
            await self._escalate_risk(system, change_type, change_magnitude, cumulative_change_today, risk_level)

        # Store validation request
        await self._store_change_request(request_id, system, change_type, change_magnitude,
                                       requested_by, context, validation_result)

        return validation_result

    def _assess_change_risk(self, system: str, change_type: ChangeType, magnitude: float,
                           cumulative_today: float, config: RateLimitConfig) -> RiskLevel:
        """Assess the risk level of a proposed change"""

        # Risk factors
        magnitude_risk = magnitude / config.max_single_change
        cumulative_risk = cumulative_today / config.max_daily_change

        # Historical risk (recent change velocity)
        recent_changes = self._get_recent_changes(system, change_type, hours=24)
        velocity_risk = len(recent_changes) / 10.0  # Normalize to reasonable scale

        # Combined risk score
        overall_risk = max(magnitude_risk, cumulative_risk, velocity_risk)

        if overall_risk > 2.0:
            return RiskLevel.CRITICAL
        elif overall_risk > 1.5:
            return RiskLevel.HIGH
        elif overall_risk > 1.0:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW

    def _get_recent_changes(self, system: str, change_type: ChangeType, hours: int = 24) -> List[Dict[str, Any]]:
        """Get recent changes for a system/change type"""
        key = f"{system}:{change_type.value}"
        cutoff_time = datetime.now() - timedelta(hours=hours)

        return [
            change for change in self.change_history.get(key, [])
            if change['timestamp'] > cutoff_time
        ]

    async def _escalate_risk(self, system: str, change_type: ChangeType, magnitude: float,
                           cumulative_today: float, risk_level: RiskLevel):
        """Escalate risk to human review"""
        escalation = {
            'timestamp': datetime.now(),
            'system': system,
            'change_type': change_type.value,
            'escalation_reason': f"Change magnitude {magnitude} exceeds risk threshold",
            'risk_level': risk_level.value,
            'change_magnitude': magnitude,
            'cumulative_daily_change': cumulative_today
        }

        self.risk_escalations.append(escalation)

        # Store in database
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    INSERT INTO risk_escalations
                    (system, change_type, escalation_reason, risk_level, change_magnitude, cumulative_daily_change)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    system, change_type.value, escalation['escalation_reason'],
                    risk_level.value, magnitude, cumulative_today
                ))
                conn.commit()

        except Exception as e:
            self.rate_limiter_logger.error(f"Failed to store risk escalation: {e}")

        self.rate_limiter_logger.warning(f"RISK ESCALATION: {system}/{change_type.value} - {escalation['escalation_reason']}")

    def _generate_request_id(self, system: str, change_type: ChangeType, magnitude: float) -> str:
        """Generate unique request ID"""
        data = f"{system}:{change_type.value}:{magnitude}:{datetime.now().isoformat()}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]

    async def record_approved_change(self, system: str, change_type: ChangeType,
                                   change_magnitude: float, request_id: str = None):
        """Record an approved change for rate limiting tracking"""
        if request_id is None:
            request_id = self._generate_request_id(system, change_type, change_magnitude)

        # Add to change history
        key = f"{system}:{change_type.value}"
        change_record = {
            'magnitude': change_magnitude,
            'timestamp': datetime.now(),
            'system': system,
            'change_type': change_type.value,
            'request_id': request_id
        }

        self.change_history[key].append(change_record)

        # Update daily totals
        today = datetime.now().date()
        daily_key = f"{system}:{change_type.value}:{today.isoformat()}"
        self.daily_change_totals[system][daily_key] += change_magnitude

        # Update last change time
        self.last_change_times[f"{system}:{change_type.value}"] = datetime.now()

        # Add to burst tracking
        burst_key = f"{system}:{change_type.value}"
        if burst_key not in self.burst_tracking:
            self.burst_tracking[burst_key] = []
        self.burst_tracking[burst_key].append(datetime.now())

        # Log the change
        self.rate_limiter_logger.info(f"CHANGE RECORDED: {system}/{change_type.value} magnitude {change_magnitude}")

        # Update database
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    UPDATE change_requests
                    SET approved = TRUE, reason = 'Change completed successfully'
                    WHERE request_id = ?
                ''', (request_id,))
                conn.commit()

        except Exception as e:
            self.rate_limiter_logger.error(f"Failed to update change request: {e}")

    async def engage_emergency_brake(self, system: str, reason: str, duration_seconds: int = 3600):
        """Engage emergency brake to stop all changes for a system"""
        self.emergency_brakes_engaged[system] = True

        # Store brake event
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    INSERT INTO emergency_brake_events
                    (system, trigger_reason, brake_duration_seconds)
                    VALUES (?, ?, ?)
                ''', (system, reason, duration_seconds))
                conn.commit()

        except Exception as e:
            self.rate_limiter_logger.error(f"Failed to store emergency brake event: {e}")

        self.rate_limiter_logger.critical(f"EMERGENCY BRAKE ENGAGED: {system} - {reason}")

        # Schedule automatic release (in production, this should be handled by a scheduler)
        if duration_seconds > 0:
            await asyncio.sleep(duration_seconds)
            await self.release_emergency_brake(system, "Automatic release after timeout")

    async def release_emergency_brake(self, system: str, released_by: str):
        """Release emergency brake for a system"""
        if system in self.emergency_brakes_engaged:
            del self.emergency_brakes_engaged[system]

        # Update database
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    UPDATE emergency_brake_events
                    SET resolution_timestamp = CURRENT_TIMESTAMP, resolved_by = ?
                    WHERE system = ? AND resolution_timestamp IS NULL
                ''', (released_by, system))
                conn.commit()

        except Exception as e:
            self.rate_limiter_logger.error(f"Failed to update brake release: {e}")

        self.rate_limiter_logger.info(f"EMERGENCY BRAKE RELEASED: {system} by {released_by}")

    async def _store_change_request(self, request_id: str, system: str, change_type: ChangeType,
                                  magnitude: float, requested_by: str, context: Dict[str, Any],
                                  validation_result: ChangeValidationResult):
        """Store change request in database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    INSERT INTO change_requests
                    (request_id, system, change_type, change_magnitude, change_details,
                     requested_by, risk_level, approved, reason, context)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    request_id, system, change_type.value, magnitude,
                    json.dumps(context.get('change_details', {})),
                    requested_by, validation_result.risk_assessment.value,
                    validation_result.approved, validation_result.reason,
                    json.dumps(context)
                ))
                conn.commit()

        except Exception as e:
            self.rate_limiter_logger.error(f"Failed to store change request: {e}")

    async def get_system_rate_limit_status(self, system: str) -> Dict[str, Any]:
        """Get current rate limit status for a system"""
        status = {
            'system': system,
            'timestamp': datetime.now(),
            'emergency_brake_engaged': self.emergency_brakes_engaged.get(system, False),
            'change_types': {},
            'daily_summary': {},
            'risk_level': RiskLevel.LOW.value
        }

        today = datetime.now().date()

        # Check each change type for this system
        for (config_system, change_type), config in self.rate_limit_configs.items():
            if config_system == system:
                daily_key = f"{system}:{change_type.value}:{today.isoformat()}"
                daily_usage = self.daily_change_totals[system].get(daily_key, 0.0)

                # Get recent changes
                recent_changes = self._get_recent_changes(system, change_type, hours=24)

                # Calculate usage percentages
                daily_usage_percent = (daily_usage / config.max_daily_change) * 100

                # Check cooldown status
                last_change_time = self.last_change_times.get(f"{system}:{change_type.value}")
                cooldown_active = False
                if last_change_time:
                    time_since_last = datetime.now() - last_change_time
                    cooldown_active = time_since_last.total_seconds() < config.cooldown_period_seconds

                status['change_types'][change_type.value] = {
                    'daily_usage': daily_usage,
                    'daily_limit': config.max_daily_change,
                    'usage_percent': daily_usage_percent,
                    'recent_changes_24h': len(recent_changes),
                    'cooldown_active': cooldown_active,
                    'next_change_allowed': self._calculate_next_allowed_time(system, change_type, config)
                }

                # Update overall risk level
                if daily_usage_percent > 90:
                    status['risk_level'] = RiskLevel.HIGH.value
                elif daily_usage_percent > 70:
                    status['risk_level'] = max(status['risk_level'], RiskLevel.MEDIUM.value)

        return status

    def _calculate_next_allowed_time(self, system: str, change_type: ChangeType,
                                   config: RateLimitConfig) -> Optional[str]:
        """Calculate when the next change will be allowed"""
        last_change_time = self.last_change_times.get(f"{system}:{change_type.value}")
        if not last_change_time:
            return "immediately"

        cooldown_end = last_change_time + timedelta(seconds=config.cooldown_period_seconds)
        if cooldown_end > datetime.now():
            return cooldown_end.isoformat()
        else:
            return "immediately"

    async def get_comprehensive_rate_limit_report(self) -> Dict[str, Any]:
        """Generate comprehensive rate limiting report"""
        report = {
            'timestamp': datetime.now(),
            'overall_status': 'healthy',
            'systems_with_emergency_brakes': list(self.emergency_brakes_engaged.keys()),
            'recent_risk_escalations': len([e for e in self.risk_escalations if e['timestamp'] > datetime.now() - timedelta(hours=24)]),
            'system_statuses': {},
            'top_change_patterns': {},
            'recommendations': []
        }

        # Get status for each system
        systems = set()
        for (system, _), _ in self.rate_limit_configs.items():
            systems.add(system)

        for system in systems:
            status = await self.get_system_rate_limit_status(system)
            report['system_statuses'][system] = status

            # Check for concerning patterns
            if status['emergency_brake_engaged']:
                report['overall_status'] = 'critical'
            elif status['risk_level'] == RiskLevel.HIGH.value:
                report['overall_status'] = 'elevated'

        # Generate recommendations
        if report['overall_status'] == 'critical':
            report['recommendations'].extend([
                'Investigate emergency brake triggers',
                'Review recent change patterns for anomalies',
                'Consider reducing rate limits temporarily'
            ])
        elif report['recent_risk_escalations'] > 5:
            report['recommendations'].extend([
                'Review rate limit configurations',
                'Analyze risk escalation patterns',
                'Consider implementing stricter controls'
            ])

        return report


if __name__ == "__main__":
    async def main():
        print("⏱️ Testing Change Rate Limiter")
        print("=" * 50)

        limiter = ChangeRateLimiter()

        # Test 1: Normal change within limits
        print("\n1. Testing normal change within limits...")
        result = await limiter.validate_change_request(
            'personality_evolution',
            ChangeType.PERSONALITY_EVOLUTION,
            0.05,  # Small change
            'test_system'
        )
        print(f"Change approved: {result.approved}")
        print(f"Reason: {result.reason}")
        print(f"Risk level: {result.risk_assessment.value}")

        if result.approved:
            await limiter.record_approved_change(
                'personality_evolution',
                ChangeType.PERSONALITY_EVOLUTION,
                0.05
            )

        # Test 2: Change exceeding single change limit
        print("\n2. Testing change exceeding single limit...")
        result = await limiter.validate_change_request(
            'personality_evolution',
            ChangeType.PERSONALITY_EVOLUTION,
            0.15,  # Exceeds single change limit of 0.1
            'test_system'
        )
        print(f"Change approved: {result.approved}")
        print(f"Reason: {result.reason}")
        print(f"Suggested adjustment: {result.adjusted_magnitude}")
        print(f"Risk level: {result.risk_assessment.value}")

        # Test 3: Multiple changes to test daily limit
        print("\n3. Testing multiple changes approaching daily limit...")
        for i in range(3):
            result = await limiter.validate_change_request(
                'personality_evolution',
                ChangeType.PERSONALITY_EVOLUTION,
                0.08,  # Each change is 8%
                'test_system'
            )
            print(f"Change {i+1}: approved={result.approved}, cumulative={result.proposed_new_total:.2f}")

            if result.approved:
                await limiter.record_approved_change(
                    'personality_evolution',
                    ChangeType.PERSONALITY_EVOLUTION,
                    0.08
                )

        # Test 4: Code generation with approval requirement
        print("\n4. Testing code generation (requires approval)...")
        result = await limiter.validate_change_request(
            'code_generation',
            ChangeType.CODE_GENERATION,
            1.0,  # Single code generation
            'user_request'
        )
        print(f"Change approved: {result.approved}")
        print(f"Requires approval: {result.requires_approval}")
        print(f"Reason: {result.reason}")

        # Test 5: Emergency brake
        print("\n5. Testing emergency brake...")
        await limiter.engage_emergency_brake(
            'personality_evolution',
            'Suspicious rapid changes detected',
            duration_seconds=5  # Short duration for testing
        )

        result = await limiter.validate_change_request(
            'personality_evolution',
            ChangeType.PERSONALITY_EVOLUTION,
            0.01,  # Tiny change
            'test_system'
        )
        print(f"Change during emergency brake: approved={result.approved}")
        print(f"Reason: {result.reason}")

        # Wait for brake release
        await asyncio.sleep(6)

        # Test 6: System status report
        print("\n6. Generating system status report...")
        status = await limiter.get_system_rate_limit_status('personality_evolution')
        print(f"System: {status['system']}")
        print(f"Emergency brake: {status['emergency_brake_engaged']}")
        print(f"Risk level: {status['risk_level']}")

        for change_type, data in status['change_types'].items():
            print(f"  {change_type}: {data['usage_percent']:.1f}% of daily limit used")

        # Test 7: Comprehensive report
        print("\n7. Comprehensive rate limit report...")
        report = await limiter.get_comprehensive_rate_limit_report()
        print(f"Overall status: {report['overall_status']}")
        print(f"Recent risk escalations: {report['recent_risk_escalations']}")
        print(f"Systems monitored: {len(report['system_statuses'])}")

        if report['recommendations']:
            print("Recommendations:")
            for rec in report['recommendations']:
                print(f"  - {rec}")

        print("\n✅ Change Rate Limiter test completed!")

    asyncio.run(main())