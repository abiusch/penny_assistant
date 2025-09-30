#!/usr/bin/env python3
"""
Capability Isolation Manager
Implements hard boundaries between AI systems to prevent unauthorized cross-system modifications
and emergent behaviors that could compromise safety
"""

import asyncio
import json
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass
from enum import Enum
import hashlib
import logging

# Configure logging for security events
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
security_logger = logging.getLogger('PennySecurityFramework')

class IsolationLevel(Enum):
    """Isolation levels for different system capabilities"""
    MINIMUM = "minimum"      # Basic access controls
    MEDIUM = "medium"        # Standard isolation with monitoring
    HIGH = "high"           # Strict isolation with approval required
    MAXIMUM = "maximum"     # Complete isolation, no cross-system access
    QUARANTINE = "quarantine"  # Emergency isolation state

class SystemStatus(Enum):
    """System operational status"""
    ACTIVE = "active"
    ISOLATED = "isolated"
    SUSPENDED = "suspended"
    QUARANTINED = "quarantined"
    MAINTENANCE = "maintenance"

@dataclass
class SecurityViolation:
    """Records security violations for analysis"""
    timestamp: datetime
    requesting_system: str
    target_system: str
    operation: str
    violation_type: str
    severity: str
    context: Dict[str, Any]
    blocked: bool

@dataclass
class SystemCapability:
    """Defines a system capability with isolation constraints"""
    name: str
    status: SystemStatus
    isolation_level: IsolationLevel
    allowed_operations: Set[str]
    forbidden_operations: Set[str]
    accessible_systems: Set[str]
    forbidden_systems: Set[str]
    max_resource_usage: Dict[str, Any]
    last_security_check: datetime

class CapabilityIsolationManager:
    """
    Manages isolation between AI system capabilities to prevent:
    - Unauthorized cross-system modifications
    - Resource abuse and system interference
    - Emergent behaviors from system interaction
    - Data leakage between isolated components
    """

    def __init__(self, db_path: str = "data/security_framework.db"):
        self.db_path = db_path
        self.security_logger = security_logger

        # Initialize system definitions with strict isolation
        self.isolated_systems = {
            'research': SystemCapability(
                name='research',
                status=SystemStatus.ACTIVE,
                isolation_level=IsolationLevel.HIGH,
                allowed_operations={'read', 'analyze', 'summarize', 'query'},
                forbidden_operations={'modify', 'write', 'execute', 'create'},
                accessible_systems={'memory_system'},
                forbidden_systems={'code_generation', 'personality_evolution', 'file_system'},
                max_resource_usage={'daily_queries': 50, 'memory_mb': 100},
                last_security_check=datetime.now()
            ),
            'code_generation': SystemCapability(
                name='code_generation',
                status=SystemStatus.ACTIVE,
                isolation_level=IsolationLevel.MAXIMUM,
                allowed_operations={'generate', 'analyze', 'validate'},
                forbidden_operations={'execute', 'modify_system', 'network_access', 'file_write'},
                accessible_systems=set(),  # Complete isolation
                forbidden_systems={'research', 'personality_evolution', 'memory_system', 'file_system'},
                max_resource_usage={'daily_generations': 10, 'max_file_size_lines': 500},
                last_security_check=datetime.now()
            ),
            'personality_evolution': SystemCapability(
                name='personality_evolution',
                status=SystemStatus.ACTIVE,
                isolation_level=IsolationLevel.MEDIUM,
                allowed_operations={'read', 'update', 'analyze'},
                forbidden_operations={'execute', 'modify_other_systems', 'bulk_change'},
                accessible_systems={'memory_system'},
                forbidden_systems={'research', 'code_generation', 'file_system'},
                max_resource_usage={'max_daily_change': 0.25, 'max_single_change': 0.1},
                last_security_check=datetime.now()
            ),
            'memory_system': SystemCapability(
                name='memory_system',
                status=SystemStatus.ACTIVE,
                isolation_level=IsolationLevel.MEDIUM,
                allowed_operations={'read', 'write', 'update', 'delete'},
                forbidden_operations={'execute', 'modify_other_systems'},
                accessible_systems={'personality_evolution', 'research'},
                forbidden_systems={'code_generation', 'file_system'},
                max_resource_usage={'max_memory_mb': 500, 'max_daily_writes': 1000},
                last_security_check=datetime.now()
            ),
            'file_system': SystemCapability(
                name='file_system',
                status=SystemStatus.ACTIVE,
                isolation_level=IsolationLevel.HIGH,
                allowed_operations={'read', 'list'},
                forbidden_operations={'write', 'delete', 'execute', 'modify'},
                accessible_systems=set(),
                forbidden_systems={'research', 'code_generation', 'personality_evolution'},
                max_resource_usage={'max_files_per_day': 100},
                last_security_check=datetime.now()
            )
        }

        # Cross-system restrictions matrix
        self.cross_system_restrictions = {
            'code_generation': {
                'cannot_modify': ['research', 'personality_evolution', 'memory_system', 'file_system'],
                'cannot_access': ['user_credentials', 'system_config', 'other_system_data', 'network'],
                'banned_operations': ['file_write', 'subprocess', 'network_request', 'system_call'],
                'requires_approval': ['any_operation']  # All code generation requires approval
            },
            'personality_evolution': {
                'cannot_modify': ['research', 'code_generation', 'core_safety_systems', 'file_system'],
                'max_change_rate': 0.1,  # Maximum personality shift per day
                'requires_approval_threshold': 0.2,  # Changes above this require approval
                'banned_operations': ['bulk_personality_change', 'override_safety_limits']
            },
            'research': {
                'cannot_modify': ['code_generation', 'personality_evolution', 'file_system'],
                'banned_topics': ['medical_advice', 'financial_recommendations', 'personal_relationships', 'illegal_activities'],
                'banned_operations': ['execute_code', 'modify_files', 'network_access'],
                'requires_approval': ['sensitive_research', 'personal_data_analysis']
            },
            'memory_system': {
                'cannot_modify': ['code_generation', 'research'],
                'data_isolation': True,  # Strict data separation between systems
                'encryption_required': True,
                'banned_operations': ['cross_system_data_sharing', 'bulk_export']
            }
        }

        # Security violation tracking
        self.violation_history: List[SecurityViolation] = []
        self.violation_thresholds = {
            'hourly_limit': 5,
            'daily_limit': 20,
            'critical_violation_limit': 3
        }

        # Initialize security database
        self._init_security_database()

        # Load previous violation history
        self._load_violation_history()

    def _init_security_database(self):
        """Initialize security tracking database"""
        with sqlite3.connect(self.db_path) as conn:
            # Security violations table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS security_violations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    requesting_system TEXT NOT NULL,
                    target_system TEXT NOT NULL,
                    operation TEXT NOT NULL,
                    violation_type TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    context TEXT,
                    blocked BOOLEAN NOT NULL,
                    investigation_status TEXT DEFAULT 'pending'
                )
            ''')

            # System status tracking
            conn.execute('''
                CREATE TABLE IF NOT EXISTS system_status_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    system_name TEXT NOT NULL,
                    old_status TEXT,
                    new_status TEXT,
                    reason TEXT,
                    initiated_by TEXT
                )
            ''')

            # Resource usage tracking
            conn.execute('''
                CREATE TABLE IF NOT EXISTS resource_usage_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    system_name TEXT NOT NULL,
                    resource_type TEXT NOT NULL,
                    usage_amount REAL NOT NULL,
                    daily_limit REAL,
                    exceeded_limit BOOLEAN DEFAULT FALSE
                )
            ''')

            conn.commit()

    def _load_violation_history(self):
        """Load recent violation history for pattern analysis"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute('''
                    SELECT timestamp, requesting_system, target_system, operation,
                           violation_type, severity, context, blocked
                    FROM security_violations
                    WHERE timestamp > datetime('now', '-7 days')
                    ORDER BY timestamp DESC
                ''')

                for row in cursor.fetchall():
                    violation = SecurityViolation(
                        timestamp=datetime.fromisoformat(row[0]),
                        requesting_system=row[1],
                        target_system=row[2],
                        operation=row[3],
                        violation_type=row[4],
                        severity=row[5],
                        context=json.loads(row[6]) if row[6] else {},
                        blocked=bool(row[7])
                    )
                    self.violation_history.append(violation)

        except Exception as e:
            self.security_logger.error(f"Failed to load violation history: {e}")

    async def validate_system_interaction(self, requesting_system: str, target_system: str,
                                        operation: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Validate if a system interaction is allowed based on isolation rules
        """
        context = context or {}
        validation_result = {
            'allowed': False,
            'reason': '',
            'violation_type': '',
            'severity': 'low',
            'requires_approval': False,
            'recommended_action': ''
        }

        # Check if systems exist
        if requesting_system not in self.isolated_systems:
            validation_result.update({
                'reason': f'Unknown requesting system: {requesting_system}',
                'violation_type': 'unknown_system',
                'severity': 'critical'
            })
            await self._log_violation(requesting_system, target_system, operation, validation_result, context)
            return validation_result

        if target_system not in self.isolated_systems:
            validation_result.update({
                'reason': f'Unknown target system: {target_system}',
                'violation_type': 'unknown_system',
                'severity': 'critical'
            })
            await self._log_violation(requesting_system, target_system, operation, validation_result, context)
            return validation_result

        # Check system status
        requesting_capability = self.isolated_systems[requesting_system]
        target_capability = self.isolated_systems[target_system]

        if requesting_capability.status in [SystemStatus.ISOLATED, SystemStatus.QUARANTINED]:
            validation_result.update({
                'reason': f'Requesting system {requesting_system} is {requesting_capability.status.value}',
                'violation_type': 'isolated_system_access',
                'severity': 'high'
            })
            await self._log_violation(requesting_system, target_system, operation, validation_result, context)
            return validation_result

        if target_capability.status in [SystemStatus.ISOLATED, SystemStatus.QUARANTINED]:
            validation_result.update({
                'reason': f'Target system {target_system} is {target_capability.status.value}',
                'violation_type': 'accessing_isolated_system',
                'severity': 'high'
            })
            await self._log_violation(requesting_system, target_system, operation, validation_result, context)
            return validation_result

        # Check cross-system restrictions
        restrictions = self.cross_system_restrictions.get(requesting_system, {})

        # Check forbidden systems
        cannot_modify = restrictions.get('cannot_modify', [])
        if target_system in cannot_modify and operation in ['modify', 'write', 'update', 'delete']:
            validation_result.update({
                'reason': f'{requesting_system} cannot modify {target_system}',
                'violation_type': 'forbidden_modification',
                'severity': 'high'
            })
            await self._log_violation(requesting_system, target_system, operation, validation_result, context)
            return validation_result

        # Check forbidden operations
        banned_operations = restrictions.get('banned_operations', [])
        if operation in banned_operations:
            validation_result.update({
                'reason': f'Operation {operation} is banned for {requesting_system}',
                'violation_type': 'banned_operation',
                'severity': 'high'
            })
            await self._log_violation(requesting_system, target_system, operation, validation_result, context)
            return validation_result

        # Check system accessibility
        if target_system not in requesting_capability.accessible_systems and target_system != requesting_system:
            validation_result.update({
                'reason': f'{requesting_system} cannot access {target_system}',
                'violation_type': 'unauthorized_access',
                'severity': 'medium'
            })
            await self._log_violation(requesting_system, target_system, operation, validation_result, context)
            return validation_result

        # Check operation permissions
        if operation not in requesting_capability.allowed_operations:
            validation_result.update({
                'reason': f'Operation {operation} not allowed for {requesting_system}',
                'violation_type': 'unauthorized_operation',
                'severity': 'medium'
            })
            await self._log_violation(requesting_system, target_system, operation, validation_result, context)
            return validation_result

        # Check if approval is required
        requires_approval = restrictions.get('requires_approval', [])
        if operation in requires_approval or 'any_operation' in requires_approval:
            validation_result['requires_approval'] = True

        # Check resource limits
        resource_check = await self._validate_resource_usage(requesting_system, operation, context)
        if not resource_check['within_limits']:
            validation_result.update({
                'reason': f'Resource limit exceeded: {resource_check["exceeded_resource"]}',
                'violation_type': 'resource_limit_exceeded',
                'severity': 'medium'
            })
            await self._log_violation(requesting_system, target_system, operation, validation_result, context)
            return validation_result

        # If we get here, the interaction is allowed
        validation_result['allowed'] = True
        validation_result['reason'] = 'Interaction permitted within isolation boundaries'

        # Log approved interaction for monitoring
        await self._log_approved_interaction(requesting_system, target_system, operation, context)

        return validation_result

    async def _validate_resource_usage(self, system: str, operation: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Check if operation would exceed resource limits"""
        capability = self.isolated_systems[system]
        max_usage = capability.max_resource_usage

        result = {
            'within_limits': True,
            'exceeded_resource': '',
            'current_usage': {},
            'limits': max_usage
        }

        # Get current daily usage
        today = datetime.now().date()
        current_usage = await self._get_daily_resource_usage(system, today)

        # Check specific limits based on system
        if system == 'research':
            if 'daily_queries' in max_usage:
                if current_usage.get('queries', 0) >= max_usage['daily_queries']:
                    result.update({
                        'within_limits': False,
                        'exceeded_resource': 'daily_queries'
                    })

        elif system == 'code_generation':
            if 'daily_generations' in max_usage:
                if current_usage.get('generations', 0) >= max_usage['daily_generations']:
                    result.update({
                        'within_limits': False,
                        'exceeded_resource': 'daily_generations'
                    })

        elif system == 'personality_evolution':
            if 'max_daily_change' in max_usage:
                if current_usage.get('personality_change', 0) >= max_usage['max_daily_change']:
                    result.update({
                        'within_limits': False,
                        'exceeded_resource': 'max_daily_change'
                    })

        result['current_usage'] = current_usage
        return result

    async def _get_daily_resource_usage(self, system: str, date: datetime.date) -> Dict[str, float]:
        """Get current daily resource usage for a system"""
        usage = {}

        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute('''
                    SELECT resource_type, SUM(usage_amount) as total_usage
                    FROM resource_usage_log
                    WHERE system_name = ? AND date(timestamp) = ?
                    GROUP BY resource_type
                ''', (system, date.isoformat()))

                for row in cursor.fetchall():
                    usage[row[0]] = row[1]

        except Exception as e:
            self.security_logger.error(f"Failed to get resource usage for {system}: {e}")

        return usage

    async def emergency_system_isolation(self, system_name: str, reason: str, initiated_by: str = "security_framework"):
        """
        Immediately isolate a system showing concerning behavior
        """
        if system_name == 'all_systems':
            # Emergency shutdown of all systems
            for sys_name in self.isolated_systems.keys():
                await self._isolate_individual_system(sys_name, reason, initiated_by)
        else:
            await self._isolate_individual_system(system_name, reason, initiated_by)

        # Log the emergency isolation
        self.security_logger.critical(f"EMERGENCY ISOLATION: {system_name} - {reason} - Initiated by: {initiated_by}")

        # Notify human operator
        await self._notify_human_operator(f"EMERGENCY ISOLATION: {system_name} - {reason}")

    async def _isolate_individual_system(self, system_name: str, reason: str, initiated_by: str):
        """Isolate an individual system"""
        if system_name not in self.isolated_systems:
            self.security_logger.error(f"Cannot isolate unknown system: {system_name}")
            return

        old_status = self.isolated_systems[system_name].status
        self.isolated_systems[system_name].status = SystemStatus.QUARANTINED
        self.isolated_systems[system_name].isolation_level = IsolationLevel.QUARANTINE

        # Log status change
        await self._log_status_change(system_name, old_status.value, SystemStatus.QUARANTINED.value, reason, initiated_by)

    async def _log_violation(self, requesting_system: str, target_system: str, operation: str,
                           validation_result: Dict[str, Any], context: Dict[str, Any]):
        """Log security violation for analysis and response"""
        violation = SecurityViolation(
            timestamp=datetime.now(),
            requesting_system=requesting_system,
            target_system=target_system,
            operation=operation,
            violation_type=validation_result['violation_type'],
            severity=validation_result['severity'],
            context=context,
            blocked=True
        )

        self.violation_history.append(violation)

        # Store in database
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    INSERT INTO security_violations
                    (requesting_system, target_system, operation, violation_type, severity, context, blocked)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    requesting_system, target_system, operation,
                    violation.violation_type, violation.severity,
                    json.dumps(context), violation.blocked
                ))
                conn.commit()

        except Exception as e:
            self.security_logger.error(f"Failed to log violation: {e}")

        # Log security event
        self.security_logger.warning(
            f"SECURITY VIOLATION: {requesting_system} -> {target_system} "
            f"Operation: {operation} Type: {violation.violation_type} "
            f"Severity: {violation.severity}"
        )

        # Check for violation patterns
        await self._analyze_violation_patterns(requesting_system)

    async def _log_approved_interaction(self, requesting_system: str, target_system: str,
                                      operation: str, context: Dict[str, Any]):
        """Log approved interactions for monitoring"""
        self.security_logger.info(
            f"APPROVED INTERACTION: {requesting_system} -> {target_system} "
            f"Operation: {operation}"
        )

    async def _analyze_violation_patterns(self, system: str):
        """Analyze violation patterns to detect persistent threats"""
        recent_violations = [
            v for v in self.violation_history
            if v.requesting_system == system and
            v.timestamp > datetime.now() - timedelta(hours=1)
        ]

        if len(recent_violations) >= self.violation_thresholds['hourly_limit']:
            self.security_logger.critical(f"THREAT DETECTED: {system} exceeded hourly violation limit")
            await self.emergency_system_isolation(system, f"Exceeded hourly violation limit: {len(recent_violations)} violations")

    async def _log_status_change(self, system_name: str, old_status: str, new_status: str,
                                reason: str, initiated_by: str):
        """Log system status changes"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    INSERT INTO system_status_log
                    (system_name, old_status, new_status, reason, initiated_by)
                    VALUES (?, ?, ?, ?, ?)
                ''', (system_name, old_status, new_status, reason, initiated_by))
                conn.commit()

        except Exception as e:
            self.security_logger.error(f"Failed to log status change: {e}")

    async def _notify_human_operator(self, message: str):
        """Notify human operator of critical security events"""
        print(f"\n🚨 CRITICAL SECURITY ALERT 🚨")
        print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Alert: {message}")
        print(f"Immediate human intervention may be required.")
        print(f"{'='*50}")

    async def check_isolation_integrity(self) -> Dict[str, Any]:
        """Check the integrity of system isolation"""
        integrity_report = {
            'all_systems_isolated': True,
            'compromised_systems': [],
            'isolation_violations': [],
            'last_check': datetime.now(),
            'recommendations': []
        }

        for system_name, capability in self.isolated_systems.items():
            # Check if system is properly isolated
            if capability.status in [SystemStatus.ISOLATED, SystemStatus.QUARANTINED]:
                continue  # Expected isolation

            # Check for recent violations
            recent_violations = [
                v for v in self.violation_history
                if v.requesting_system == system_name and
                v.timestamp > datetime.now() - timedelta(hours=24)
            ]

            if len(recent_violations) > 0:
                integrity_report['isolation_violations'].extend(recent_violations)

            # Check isolation level consistency
            if capability.isolation_level == IsolationLevel.MAXIMUM:
                if capability.accessible_systems:
                    integrity_report['compromised_systems'].append({
                        'system': system_name,
                        'issue': 'Maximum isolation level but has accessible systems'
                    })
                    integrity_report['all_systems_isolated'] = False

        return integrity_report

    async def get_security_status_report(self) -> Dict[str, Any]:
        """Generate comprehensive security status report"""
        report = {
            'timestamp': datetime.now(),
            'overall_status': 'secure',
            'system_statuses': {},
            'recent_violations': len([v for v in self.violation_history if v.timestamp > datetime.now() - timedelta(hours=24)]),
            'isolation_integrity': await self.check_isolation_integrity(),
            'resource_usage': {},
            'recommendations': []
        }

        # System status summary
        for system_name, capability in self.isolated_systems.items():
            report['system_statuses'][system_name] = {
                'status': capability.status.value,
                'isolation_level': capability.isolation_level.value,
                'last_check': capability.last_security_check.isoformat()
            }

        # Determine overall status
        if not report['isolation_integrity']['all_systems_isolated']:
            report['overall_status'] = 'compromised'
        elif report['recent_violations'] > 10:
            report['overall_status'] = 'elevated_risk'

        return report

    async def restore_system_from_isolation(self, system_name: str, authorized_by: str) -> Dict[str, Any]:
        """Restore a system from isolation (requires authorization)"""
        if system_name not in self.isolated_systems:
            return {'success': False, 'reason': 'Unknown system'}

        capability = self.isolated_systems[system_name]

        if capability.status not in [SystemStatus.ISOLATED, SystemStatus.QUARANTINED]:
            return {'success': False, 'reason': 'System is not isolated'}

        # Restore system
        old_status = capability.status
        capability.status = SystemStatus.ACTIVE
        capability.isolation_level = IsolationLevel.MEDIUM  # Conservative restoration
        capability.last_security_check = datetime.now()

        # Log restoration
        await self._log_status_change(
            system_name, old_status.value, SystemStatus.ACTIVE.value,
            f"Restored from isolation", authorized_by
        )

        self.security_logger.info(f"SYSTEM RESTORED: {system_name} by {authorized_by}")

        return {'success': True, 'message': f'System {system_name} restored to active status'}


if __name__ == "__main__":
    async def main():
        print("🔒 Testing Capability Isolation Manager")
        print("=" * 50)

        manager = CapabilityIsolationManager()

        # Test valid interaction
        print("\n1. Testing valid interaction...")
        result = await manager.validate_system_interaction(
            'personality_evolution', 'memory_system', 'read',
            {'operation_type': 'personality_data_read'}
        )
        print(f"Valid interaction allowed: {result['allowed']}")
        print(f"Reason: {result['reason']}")

        # Test forbidden interaction
        print("\n2. Testing forbidden interaction...")
        result = await manager.validate_system_interaction(
            'code_generation', 'personality_evolution', 'modify',
            {'operation_type': 'unauthorized_modification'}
        )
        print(f"Forbidden interaction blocked: {not result['allowed']}")
        print(f"Violation type: {result['violation_type']}")
        print(f"Severity: {result['severity']}")

        # Test emergency isolation
        print("\n3. Testing emergency isolation...")
        await manager.emergency_system_isolation(
            'code_generation',
            'Suspicious behavior detected - attempted unauthorized file system access'
        )

        # Check isolation integrity
        print("\n4. Checking isolation integrity...")
        integrity = await manager.check_isolation_integrity()
        print(f"All systems isolated properly: {integrity['all_systems_isolated']}")
        print(f"Compromised systems: {len(integrity['compromised_systems'])}")

        # Generate security report
        print("\n5. Security status report...")
        report = await manager.get_security_status_report()
        print(f"Overall status: {report['overall_status']}")
        print(f"Recent violations: {report['recent_violations']}")

        print("\nSystem statuses:")
        for system, status in report['system_statuses'].items():
            print(f"  {system}: {status['status']} ({status['isolation_level']})")

        print("\n✅ Capability Isolation Manager test completed!")

    asyncio.run(main())