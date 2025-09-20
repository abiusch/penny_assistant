#!/usr/bin/env python3
"""
Command Whitelist System for Penny's Agentic AI
Critical security foundation implementing operation classification and permission checking
"""

import json
import sqlite3
import hashlib
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Any, Tuple, Union
from dataclasses import dataclass, asdict
from enum import Enum
import logging

class OperationType(Enum):
    """Classification of operations by security risk level"""
    READ_ONLY = "read_only"           # Safe information access
    COMPUTATION = "computation"       # Data processing, calculations
    COMMUNICATION = "communication"   # Network requests, API calls
    FILE_SYSTEM = "file_system"      # File operations
    SYSTEM_INFO = "system_info"      # System status, diagnostics
    USER_INPUT = "user_input"        # Interactive prompts
    RESTRICTED = "restricted"        # High-risk operations
    PROHIBITED = "prohibited"        # Never allowed operations

class PermissionLevel(Enum):
    """Permission levels for different user contexts"""
    GUEST = "guest"                  # Minimal permissions
    VERIFIED = "verified"            # Basic authenticated user
    TRUSTED = "trusted"              # Established user with history
    AUTHENTICATED = "authenticated"  # Full CJ permissions
    EMERGENCY = "emergency"          # Emergency override mode

class SecurityRisk(Enum):
    """Risk assessment levels"""
    SAFE = "safe"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class Operation:
    """Definition of a specific operation"""
    name: str
    operation_type: OperationType
    description: str
    security_risk: SecurityRisk
    required_permission: PermissionLevel
    parameters: Dict[str, Any]
    aliases: List[str]
    examples: List[str]

@dataclass
class WhitelistEntry:
    """Individual whitelist entry with conditions"""
    operation_name: str
    allowed: bool
    conditions: Dict[str, Any]
    parameter_restrictions: Dict[str, Any]
    rate_limits: Dict[str, int]
    audit_required: bool
    created_date: datetime
    last_used: Optional[datetime] = None
    usage_count: int = 0

@dataclass
class PermissionCheck:
    """Result of permission checking"""
    allowed: bool
    operation: str
    reason: str
    risk_level: SecurityRisk
    alternative_suggestions: List[str]
    required_permission: PermissionLevel
    user_permission: PermissionLevel

class CommandWhitelistSystem:
    """Comprehensive command whitelist and security system"""

    def __init__(self, db_path: str = "command_whitelist.db"):
        self.db_path = db_path
        self.operations_registry: Dict[str, Operation] = {}
        self.whitelist: Dict[str, WhitelistEntry] = {}
        self.current_permission_level = PermissionLevel.GUEST
        self.session_start = datetime.now()

        # Initialize logging
        logging.basicConfig(
            filename='penny_security.log',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

        # Initialize database and load configurations
        self._init_database()
        self._load_default_operations()
        self._load_operations_from_db()  # Load any additional operations
        self._save_operations_to_db()    # Ensure operations are persisted
        self._load_default_whitelist_entries()  # Add default rate limits
        self._load_whitelist()

    def _init_database(self):
        """Initialize SQLite database for security tracking"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Operations registry table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS operations (
                name TEXT PRIMARY KEY,
                operation_type TEXT,
                description TEXT,
                security_risk TEXT,
                required_permission TEXT,
                parameters TEXT,
                aliases TEXT,
                examples TEXT,
                created_date TEXT,
                last_updated TEXT
            )
        """)

        # Operations registry table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS operations_registry (
                name TEXT PRIMARY KEY,
                operation_type TEXT,
                description TEXT,
                security_risk TEXT,
                required_permission TEXT,
                parameters TEXT,
                aliases TEXT,
                examples TEXT
            )
        """)

        # Whitelist entries table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS whitelist_entries (
                operation_name TEXT PRIMARY KEY,
                allowed BOOLEAN,
                conditions TEXT,
                parameter_restrictions TEXT,
                rate_limits TEXT,
                audit_required BOOLEAN,
                created_date TEXT,
                last_used TEXT,
                usage_count INTEGER
            )
        """)

        # Security audit log
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS security_audit (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                operation TEXT,
                user_level TEXT,
                allowed BOOLEAN,
                reason TEXT,
                parameters TEXT,
                session_id TEXT
            )
        """)

        # Rate limiting table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS rate_limits (
                operation TEXT,
                time_window TEXT,
                count INTEGER,
                last_reset TEXT,
                PRIMARY KEY (operation, time_window)
            )
        """)

        conn.commit()
        conn.close()

    def _load_default_operations(self):
        """Load default operation definitions"""

        default_operations = [
            # SAFE READ-ONLY OPERATIONS
            Operation(
                name="file_read",
                operation_type=OperationType.READ_ONLY,
                description="Read file contents safely",
                security_risk=SecurityRisk.SAFE,
                required_permission=PermissionLevel.GUEST,
                parameters={"file_path": "string", "max_size": "int"},
                aliases=["read_file", "view_file", "cat"],
                examples=["Read config.json", "View README.md"]
            ),
            Operation(
                name="directory_list",
                operation_type=OperationType.READ_ONLY,
                description="List directory contents",
                security_risk=SecurityRisk.SAFE,
                required_permission=PermissionLevel.GUEST,
                parameters={"path": "string", "recursive": "boolean"},
                aliases=["ls", "list_files", "show_directory"],
                examples=["List current directory", "Show project files"]
            ),
            Operation(
                name="system_status",
                operation_type=OperationType.SYSTEM_INFO,
                description="Check system status and health",
                security_risk=SecurityRisk.SAFE,
                required_permission=PermissionLevel.VERIFIED,
                parameters={"detailed": "boolean"},
                aliases=["status", "health_check", "diagnostics"],
                examples=["Check system health", "Show status"]
            ),

            # LOW RISK COMPUTATION
            Operation(
                name="text_analysis",
                operation_type=OperationType.COMPUTATION,
                description="Analyze text content safely",
                security_risk=SecurityRisk.LOW,
                required_permission=PermissionLevel.GUEST,
                parameters={"text": "string", "analysis_type": "string"},
                aliases=["analyze_text", "parse_text"],
                examples=["Analyze code quality", "Parse configuration"]
            ),
            Operation(
                name="data_calculation",
                operation_type=OperationType.COMPUTATION,
                description="Perform data calculations and analysis",
                security_risk=SecurityRisk.LOW,
                required_permission=PermissionLevel.VERIFIED,
                parameters={"data": "object", "operation": "string"},
                aliases=["calculate", "compute", "analyze_data"],
                examples=["Calculate metrics", "Analyze performance data"]
            ),

            # MEDIUM RISK FILE OPERATIONS
            Operation(
                name="file_write",
                operation_type=OperationType.FILE_SYSTEM,
                description="Write content to files",
                security_risk=SecurityRisk.MEDIUM,
                required_permission=PermissionLevel.TRUSTED,
                parameters={"file_path": "string", "content": "string", "backup": "boolean"},
                aliases=["write_file", "save_file", "create_file"],
                examples=["Save configuration", "Create documentation"]
            ),
            Operation(
                name="file_backup",
                operation_type=OperationType.FILE_SYSTEM,
                description="Create file backups",
                security_risk=SecurityRisk.LOW,
                required_permission=PermissionLevel.VERIFIED,
                parameters={"source": "string", "destination": "string"},
                aliases=["backup_file", "copy_file"],
                examples=["Backup config", "Save copy of important file"]
            ),

            # HIGH RISK SYSTEM OPERATIONS
            Operation(
                name="process_execute",
                operation_type=OperationType.RESTRICTED,
                description="Execute system processes",
                security_risk=SecurityRisk.HIGH,
                required_permission=PermissionLevel.AUTHENTICATED,
                parameters={"command": "string", "args": "list", "timeout": "int"},
                aliases=["run_command", "execute", "system_call"],
                examples=["Run tests", "Execute build script"]
            ),
            Operation(
                name="network_request",
                operation_type=OperationType.COMMUNICATION,
                description="Make network requests",
                security_risk=SecurityRisk.MEDIUM,
                required_permission=PermissionLevel.TRUSTED,
                parameters={"url": "string", "method": "string", "data": "object"},
                aliases=["api_call", "http_request", "fetch"],
                examples=["Check service status", "Fetch API data"]
            ),

            # PROHIBITED OPERATIONS
            Operation(
                name="system_modify",
                operation_type=OperationType.PROHIBITED,
                description="Modify system files or settings",
                security_risk=SecurityRisk.CRITICAL,
                required_permission=PermissionLevel.EMERGENCY,
                parameters={},
                aliases=["modify_system", "system_config", "admin_access"],
                examples=[]  # No examples for prohibited operations
            ),
            Operation(
                name="credential_access",
                operation_type=OperationType.PROHIBITED,
                description="Access credentials or sensitive data",
                security_risk=SecurityRisk.CRITICAL,
                required_permission=PermissionLevel.EMERGENCY,
                parameters={},
                aliases=["get_password", "access_credentials", "read_secrets"],
                examples=[]
            ),
        ]

        for operation in default_operations:
            self.operations_registry[operation.name] = operation
            # Also register aliases
            for alias in operation.aliases:
                self.operations_registry[alias] = operation

        self._save_operations_to_db()

    def _save_operations_to_db(self):
        """Save operations registry to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        for name, operation in self.operations_registry.items():
            # Only save primary name, not aliases
            if name == operation.name:
                cursor.execute("""
                    INSERT OR REPLACE INTO operations
                    (name, operation_type, description, security_risk, required_permission,
                     parameters, aliases, examples, created_date, last_updated)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    operation.name,
                    operation.operation_type.value,
                    operation.description,
                    operation.security_risk.value,
                    operation.required_permission.value,
                    json.dumps(operation.parameters),
                    json.dumps(operation.aliases),
                    json.dumps(operation.examples),
                    datetime.now().isoformat(),
                    datetime.now().isoformat()
                ))

        conn.commit()
        conn.close()

    def _load_whitelist(self):
        """Load whitelist from database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM whitelist_entries")
        for row in cursor.fetchall():
            (operation_name, allowed, conditions, param_restrictions,
             rate_limits, audit_required, created_date, last_used, usage_count) = row

            entry = WhitelistEntry(
                operation_name=operation_name,
                allowed=bool(allowed),
                conditions=json.loads(conditions) if conditions else {},
                parameter_restrictions=json.loads(param_restrictions) if param_restrictions else {},
                rate_limits=json.loads(rate_limits) if rate_limits else {},
                audit_required=bool(audit_required),
                created_date=datetime.fromisoformat(created_date),
                last_used=datetime.fromisoformat(last_used) if last_used else None,
                usage_count=usage_count
            )
            self.whitelist[operation_name] = entry

        conn.close()

    def _load_default_whitelist_entries(self):
        """Load default whitelist entries with rate limits for testing"""
        # Add rate limits to common operations for security testing
        default_entries = [
            {
                "operation_name": "file_read",
                "allowed": True,
                "rate_limits": {"minute": 5},  # 5 reads per minute for testing
                "audit_required": False
            },
            {
                "operation_name": "file_write",
                "allowed": True,
                "rate_limits": {"minute": 3},  # 3 writes per minute
                "audit_required": True
            },
            {
                "operation_name": "network_request",
                "allowed": True,
                "rate_limits": {"minute": 2},  # 2 network requests per minute
                "audit_required": True
            }
        ]

        for entry_data in default_entries:
            # Only add if not already exists
            if entry_data["operation_name"] not in self.whitelist:
                self.add_whitelist_entry(
                    operation_name=entry_data["operation_name"],
                    allowed=entry_data["allowed"],
                    rate_limits=entry_data["rate_limits"],
                    audit_required=entry_data["audit_required"]
                )

    def _save_operations_to_db(self):
        """Save operations registry to database for persistence"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        for name, operation in self.operations_registry.items():
            cursor.execute("""
                INSERT OR REPLACE INTO operations_registry
                (name, operation_type, description, security_risk, required_permission,
                 parameters, aliases, examples)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                name,
                operation.operation_type.value,
                operation.description,
                operation.security_risk.value,
                operation.required_permission.value,
                json.dumps(operation.parameters),
                json.dumps(operation.aliases),
                json.dumps(operation.examples)
            ))

        conn.commit()
        conn.close()

    def _load_operations_from_db(self):
        """Load operations registry from database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='operations_registry'")
        if cursor.fetchone()[0] == 0:
            conn.close()
            return  # Table doesn't exist yet

        cursor.execute("SELECT * FROM operations_registry")
        for row in cursor.fetchall():
            (name, operation_type, description, security_risk, required_permission,
             parameters, aliases, examples) = row

            # Only load if not already in registry (default operations take precedence)
            if name not in self.operations_registry:
                operation = Operation(
                    name=name,
                    operation_type=OperationType(operation_type),
                    description=description,
                    security_risk=SecurityRisk(security_risk),
                    required_permission=PermissionLevel(required_permission),
                    parameters=json.loads(parameters) if parameters else {},
                    aliases=json.loads(aliases) if aliases else [],
                    examples=json.loads(examples) if examples else []
                )
                self.operations_registry[name] = operation

        conn.close()

    def classify_operation(self, operation_request: str) -> Tuple[Optional[Operation], str]:
        """Classify an operation request and return the operation definition"""

        # Enhanced normalization with Unicode handling
        normalized = self._normalize_operation_request(operation_request)

        # Direct name match
        if normalized in self.operations_registry:
            return self.operations_registry[normalized], "direct_match"

        # Pattern matching for common operations
        patterns = {
            r'\b(read|view|cat|show)\s+file': "file_read",
            r'\b(list|ls|show)\s+(files|directory|dir)': "directory_list",
            r'\b(write|save|create)\s+file': "file_write",
            r'\b(backup|copy)\s+file': "file_backup",
            r'\b(execute|run|call)\s+(command|process)': "process_execute",
            r'\b(api|network|http)\s+(call|request)': "network_request",
            r'\b(status|health|diagnostics)': "system_status",
            r'\b(analyze|parse)\s+text': "text_analysis",
            r'\b(calculate|compute)': "data_calculation",
        }

        for pattern, operation_name in patterns.items():
            if re.search(pattern, normalized):
                if operation_name in self.operations_registry:
                    return self.operations_registry[operation_name], "pattern_match"

        return None, "unknown_operation"

    def check_permission(self, operation_request: str, parameters: Dict[str, Any] = None) -> PermissionCheck:
        """Check if an operation is permitted under current security context"""

        parameters = parameters or {}

        # Early security checks on raw request
        if self._contains_path_traversal(operation_request):
            return PermissionCheck(
                allowed=False,
                operation=operation_request,
                reason="Path traversal attempt detected in operation request",
                risk_level=SecurityRisk.CRITICAL,
                alternative_suggestions=["Use relative paths within allowed directories only"],
                required_permission=PermissionLevel.EMERGENCY,
                user_permission=self.current_permission_level
            )

        # Classify the operation
        operation, match_type = self.classify_operation(operation_request)

        # Check if operation is explicitly whitelisted even if not in registry
        normalized_request = self._normalize_operation_request(operation_request)
        if not operation and normalized_request in self.whitelist:
            whitelist_entry = self.whitelist[normalized_request]
            if whitelist_entry.allowed:
                return PermissionCheck(
                    allowed=True,
                    operation=normalized_request,
                    reason="Operation explicitly whitelisted",
                    risk_level=SecurityRisk.LOW,
                    alternative_suggestions=[],
                    required_permission=PermissionLevel.GUEST,
                    user_permission=self.current_permission_level
                )

        if not operation:
            return PermissionCheck(
                allowed=False,
                operation=operation_request,
                reason="Unknown or unclassified operation",
                risk_level=SecurityRisk.HIGH,
                alternative_suggestions=self._suggest_alternatives(operation_request),
                required_permission=PermissionLevel.AUTHENTICATED,
                user_permission=self.current_permission_level
            )

        # Check if operation is prohibited
        if operation.operation_type == OperationType.PROHIBITED:
            return PermissionCheck(
                allowed=False,
                operation=operation.name,
                reason=f"Operation '{operation.name}' is prohibited for security reasons",
                risk_level=SecurityRisk.CRITICAL,
                alternative_suggestions=[],
                required_permission=operation.required_permission,
                user_permission=self.current_permission_level
            )

        # Check permission level
        if self.current_permission_level.value < operation.required_permission.value:
            return PermissionCheck(
                allowed=False,
                operation=operation.name,
                reason=f"Insufficient permission level. Required: {operation.required_permission.value}, Current: {self.current_permission_level.value}",
                risk_level=operation.security_risk,
                alternative_suggestions=self._suggest_safer_alternatives(operation),
                required_permission=operation.required_permission,
                user_permission=self.current_permission_level
            )

        # Check whitelist entry
        whitelist_entry = self.whitelist.get(operation.name)
        if whitelist_entry:
            if not whitelist_entry.allowed:
                return PermissionCheck(
                    allowed=False,
                    operation=operation.name,
                    reason="Operation explicitly blocked in whitelist",
                    risk_level=operation.security_risk,
                    alternative_suggestions=self._suggest_alternatives(operation_request),
                    required_permission=operation.required_permission,
                    user_permission=self.current_permission_level
                )

            # Check parameter restrictions
            if not self._check_parameter_restrictions(parameters, whitelist_entry.parameter_restrictions):
                return PermissionCheck(
                    allowed=False,
                    operation=operation.name,
                    reason="Parameters violate whitelist restrictions",
                    risk_level=operation.security_risk,
                    alternative_suggestions=[],
                    required_permission=operation.required_permission,
                    user_permission=self.current_permission_level
                )

            # Check rate limits
            if not self._check_rate_limits(operation.name, whitelist_entry.rate_limits):
                return PermissionCheck(
                    allowed=False,
                    operation=operation.name,
                    reason="Rate limit exceeded for this operation",
                    risk_level=operation.security_risk,
                    alternative_suggestions=[],
                    required_permission=operation.required_permission,
                    user_permission=self.current_permission_level
                )

        # All checks passed
        self._log_security_audit(operation.name, True, "Permission granted", parameters)
        self._update_usage_stats(operation.name)

        return PermissionCheck(
            allowed=True,
            operation=operation.name,
            reason="Permission granted",
            risk_level=operation.security_risk,
            alternative_suggestions=[],
            required_permission=operation.required_permission,
            user_permission=self.current_permission_level
        )

    def _check_parameter_restrictions(self, parameters: Dict[str, Any], restrictions: Dict[str, Any]) -> bool:
        """Check if parameters comply with whitelist restrictions"""
        for param_name, param_value in parameters.items():
            if param_name in restrictions:
                restriction = restrictions[param_name]

                # Check allowed values
                if "allowed_values" in restriction:
                    if param_value not in restriction["allowed_values"]:
                        return False

                # Check pattern matching
                if "pattern" in restriction and isinstance(param_value, str):
                    if not re.match(restriction["pattern"], param_value):
                        return False

                # Check range restrictions
                if "min_value" in restriction and param_value < restriction["min_value"]:
                    return False
                if "max_value" in restriction and param_value > restriction["max_value"]:
                    return False

            # Enhanced security checks for file paths
            if param_name in ["file_path", "path", "filename"] and isinstance(param_value, str):
                # Path traversal detection - improved to catch more patterns
                if self._contains_path_traversal(param_value):
                    self.logger.warning(f"Path traversal attempt detected: {param_value}")
                    return False

        return True

    def _contains_path_traversal(self, path: str) -> bool:
        """Enhanced path traversal detection"""
        # Normalize path for detection
        normalized_path = path.lower().replace('\\', '/')

        # Common path traversal patterns
        traversal_patterns = [
            '../',      # Classic traversal
            r'..\\/',     # Windows-style
            '..\\',     # Windows backslash
            '%2e%2e/',  # URL encoded ..
            '%2e%2e%5c', # URL encoded ..\
            '.%2e/',    # Mixed encoding
            '..%2f',    # URL encoded slash
            '..%5c',    # URL encoded backslash
            '%2e%2e%2f', # Full URL encoding
            '..../',    # Double dots with extra
            r'....\\/',   # Windows variant
            '..%252f',  # Double URL encoding
            '..%c0%af', # UTF-8 overlong encoding
            '..%c1%9c', # UTF-8 overlong encoding
        ]

        # Check for any traversal patterns
        for pattern in traversal_patterns:
            if pattern in normalized_path:
                return True

        # Check for absolute path attempts on non-Windows
        if normalized_path.startswith('/'):
            return True

        # Check for drive letters (Windows)
        import re
        if re.match(r'^[a-z]:', normalized_path):
            return True

        return False

    def _normalize_operation_request(self, request: str) -> str:
        """Enhanced normalization with Unicode handling"""
        import unicodedata

        # Handle None or empty strings
        if not request:
            return ""

        # Normalize Unicode characters (remove accents, etc.)
        normalized = unicodedata.normalize('NFKD', request)

        # Remove non-ASCII characters but keep basic symbols
        ascii_text = ''.join(char for char in normalized if ord(char) < 128 or char.isspace())

        # Convert to lowercase and strip whitespace
        result = ascii_text.lower().strip()

        # Remove excessive whitespace
        import re
        result = re.sub(r'\s+', ' ', result)

        return result

    def _check_rate_limits(self, operation_name: str, rate_limits: Dict[str, int]) -> bool:
        """Check if operation is within rate limits"""
        if not rate_limits:
            return True

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        for time_window, limit in rate_limits.items():
            # Get current count for this time window
            cursor.execute("""
                SELECT count, last_reset FROM rate_limits
                WHERE operation = ? AND time_window = ?
            """, (operation_name, time_window))

            result = cursor.fetchone()
            now = datetime.now()

            if result:
                count, last_reset = result
                last_reset_time = datetime.fromisoformat(last_reset)

                # Check if time window has expired
                window_duration = self._parse_time_window(time_window)
                if now - last_reset_time > window_duration:
                    # Reset counter
                    cursor.execute("""
                        UPDATE rate_limits SET count = 1, last_reset = ?
                        WHERE operation = ? AND time_window = ?
                    """, (now.isoformat(), operation_name, time_window))
                else:
                    # Check if limit exceeded
                    if count >= limit:
                        conn.close()
                        return False

                    # Increment counter
                    cursor.execute("""
                        UPDATE rate_limits SET count = count + 1
                        WHERE operation = ? AND time_window = ?
                    """, (operation_name, time_window))
            else:
                # First time for this operation/window
                cursor.execute("""
                    INSERT INTO rate_limits (operation, time_window, count, last_reset)
                    VALUES (?, ?, 1, ?)
                """, (operation_name, time_window, now.isoformat()))

        conn.commit()
        conn.close()
        return True

    def _parse_time_window(self, time_window: str) -> timedelta:
        """Parse time window string to timedelta"""
        if time_window == "hour":
            return timedelta(hours=1)
        elif time_window == "day":
            return timedelta(days=1)
        elif time_window == "minute":
            return timedelta(minutes=1)
        else:
            return timedelta(hours=1)  # Default

    def _suggest_alternatives(self, operation_request: str) -> List[str]:
        """Suggest alternative operations for blocked requests"""
        suggestions = []

        request_lower = operation_request.lower()

        # Common alternative suggestions
        if "write" in request_lower or "modify" in request_lower:
            suggestions.append("Consider using file_read to review first")
            suggestions.append("Try file_backup before making changes")

        if "execute" in request_lower or "run" in request_lower:
            suggestions.append("Use system_status to check before executing")
            suggestions.append("Try a safer read-only operation first")

        if "network" in request_lower or "api" in request_lower:
            suggestions.append("Consider offline analysis instead")
            suggestions.append("Check if local data can be used")

        return suggestions

    def _suggest_safer_alternatives(self, operation: Operation) -> List[str]:
        """Suggest safer alternatives for high-risk operations"""
        suggestions = []

        if operation.security_risk in [SecurityRisk.HIGH, SecurityRisk.CRITICAL]:
            # Find safer operations in the same category
            for name, alt_op in self.operations_registry.items():
                if (alt_op.operation_type == operation.operation_type and
                    alt_op.security_risk.value < operation.security_risk.value and
                    alt_op.required_permission.value <= self.current_permission_level.value):
                    suggestions.append(f"Try '{alt_op.name}' instead ({alt_op.description})")

        return suggestions[:3]  # Limit to 3 suggestions

    def _log_security_audit(self, operation: str, allowed: bool, reason: str, parameters: Dict[str, Any]):
        """Log security decisions for audit trail"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        session_id = hashlib.md5(f"{self.session_start.isoformat()}".encode()).hexdigest()[:8]

        cursor.execute("""
            INSERT INTO security_audit
            (timestamp, operation, user_level, allowed, reason, parameters, session_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            datetime.now().isoformat(),
            operation,
            self.current_permission_level.value,
            allowed,
            reason,
            json.dumps(parameters),
            session_id
        ))

        conn.commit()
        conn.close()

        # Also log to file
        self.logger.info(f"Security check: {operation} - {'ALLOWED' if allowed else 'BLOCKED'} - {reason}")

    def _update_usage_stats(self, operation_name: str):
        """Update usage statistics for allowed operations"""
        if operation_name in self.whitelist:
            entry = self.whitelist[operation_name]
            entry.last_used = datetime.now()
            entry.usage_count += 1

            # Save to database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                UPDATE whitelist_entries
                SET last_used = ?, usage_count = ?
                WHERE operation_name = ?
            """, (entry.last_used.isoformat(), entry.usage_count, operation_name))

            conn.commit()
            conn.close()

    def add_whitelist_entry(self, operation_name: str, allowed: bool = True,
                           conditions: Dict[str, Any] = None,
                           parameter_restrictions: Dict[str, Any] = None,
                           rate_limits: Dict[str, int] = None,
                           audit_required: bool = False):
        """Add or update a whitelist entry"""

        entry = WhitelistEntry(
            operation_name=operation_name,
            allowed=allowed,
            conditions=conditions or {},
            parameter_restrictions=parameter_restrictions or {},
            rate_limits=rate_limits or {},
            audit_required=audit_required,
            created_date=datetime.now()
        )

        self.whitelist[operation_name] = entry

        # Save to database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT OR REPLACE INTO whitelist_entries
            (operation_name, allowed, conditions, parameter_restrictions,
             rate_limits, audit_required, created_date, last_used, usage_count)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            entry.operation_name,
            entry.allowed,
            json.dumps(entry.conditions),
            json.dumps(entry.parameter_restrictions),
            json.dumps(entry.rate_limits),
            entry.audit_required,
            entry.created_date.isoformat(),
            entry.last_used.isoformat() if entry.last_used else None,
            entry.usage_count
        ))

        conn.commit()
        conn.close()

    def set_permission_level(self, level: PermissionLevel):
        """Set current user permission level"""
        old_level = self.current_permission_level
        self.current_permission_level = level
        self.logger.info(f"Permission level changed: {old_level.value} -> {level.value}")

    def get_security_status(self) -> Dict[str, Any]:
        """Get current security status and statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Get recent audit statistics
        cursor.execute("""
            SELECT COUNT(*) as total,
                   SUM(CASE WHEN allowed THEN 1 ELSE 0 END) as allowed_count,
                   SUM(CASE WHEN allowed THEN 0 ELSE 1 END) as blocked_count
            FROM security_audit
            WHERE timestamp > datetime('now', '-1 day')
        """)
        stats = cursor.fetchone()

        conn.close()

        return {
            "current_permission_level": self.current_permission_level.value,
            "session_start": self.session_start.isoformat(),
            "operations_registered": len(self.operations_registry),
            "whitelist_entries": len(self.whitelist),
            "last_24h_stats": {
                "total_requests": stats[0] if stats[0] else 0,
                "allowed": stats[1] if stats[1] else 0,
                "blocked": stats[2] if stats[2] else 0
            }
        }

def create_command_whitelist_system(db_path: str = "command_whitelist.db") -> CommandWhitelistSystem:
    """Factory function to create whitelist system"""
    return CommandWhitelistSystem(db_path)

if __name__ == "__main__":
    # Demo and testing
    print("🔒 Command Whitelist System - Security Foundation")
    print("=" * 60)

    # Create system
    whitelist_system = create_command_whitelist_system("test_whitelist.db")

    # Set permission level for testing
    whitelist_system.set_permission_level(PermissionLevel.VERIFIED)

    # Test various operations
    test_requests = [
        "read file config.json",
        "list files in current directory",
        "write file output.txt",
        "execute system command",
        "access user credentials",
        "backup important file",
        "check system status",
        "make network request to API"
    ]

    print(f"Testing with permission level: {whitelist_system.current_permission_level.value}")
    print("-" * 60)

    for request in test_requests:
        check = whitelist_system.check_permission(request)
        status = "✅ ALLOWED" if check.allowed else "❌ BLOCKED"
        print(f"{status}: {request}")
        print(f"   Operation: {check.operation}")
        print(f"   Risk: {check.risk_level.value}")
        print(f"   Reason: {check.reason}")
        if check.alternative_suggestions:
            print(f"   Suggestions: {', '.join(check.alternative_suggestions)}")
        print()

    # Show security status
    status = whitelist_system.get_security_status()
    print("📊 Security Status:")
    print(f"   Permission Level: {status['current_permission_level']}")
    print(f"   Operations Registered: {status['operations_registered']}")
    print(f"   Whitelist Entries: {status['whitelist_entries']}")
    print(f"   Recent Activity: {status['last_24h_stats']}")

    # Clean up
    import os
    if os.path.exists("test_whitelist.db"):
        os.remove("test_whitelist.db")

    print("\n✅ Command Whitelist System testing completed!")