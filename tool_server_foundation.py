"""
Essential Tool Server Foundation
Provides secure base infrastructure for file system, web search, calendar, and task management tools
"""

import asyncio
import json
import sqlite3
import time
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any, Union, Callable
import aiohttp
import aiosqlite
import logging

# Security system imports
from command_whitelist_system import CommandWhitelistSystem
from emergency_stop import MultiChannelEmergencyStop
from enhanced_security_logging import EnhancedSecurityLogging


class ToolServerType(Enum):
    """Types of essential tool servers"""
    FILE_SYSTEM = "file_system"
    WEB_SEARCH = "web_search"
    CALENDAR = "calendar"
    TASK_MANAGEMENT = "task_management"


class SecurityLevel(Enum):
    """Security levels for tool operations"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ToolOperation:
    """Represents a tool operation with security context"""
    operation_id: str
    tool_type: ToolServerType
    operation_name: str
    parameters: Dict[str, Any]
    user_id: Optional[str]
    security_level: SecurityLevel
    timestamp: datetime
    session_id: Optional[str] = None
    rollback_data: Optional[Dict[str, Any]] = None
    audit_metadata: Optional[Dict[str, Any]] = None


@dataclass
class ToolOperationResult:
    """Result of a tool operation"""
    operation_id: str
    success: bool
    result: Optional[Dict[str, Any]]
    error_message: Optional[str]
    execution_time: float
    security_validated: bool
    rollback_id: Optional[str] = None
    audit_trail: Optional[List[Dict[str, Any]]] = None


@dataclass
class SecurityContext:
    """Security context for tool operations"""
    user_id: Optional[str]
    session_id: Optional[str]
    permission_level: str
    rate_limit_remaining: int
    authentication_valid: bool
    emergency_stop_active: bool
    whitelist_validated: bool
    audit_required: bool


class ToolServerSecurityError(Exception):
    """Security-related errors in tool servers"""
    pass


class ToolServerRateLimitError(Exception):
    """Rate limiting errors"""
    pass


class ToolServerAuthenticationError(Exception):
    """Authentication errors"""
    pass


class BaseToolServer(ABC):
    """Base class for all essential tool servers"""

    def __init__(self,
                 server_type: ToolServerType,
                 db_path: str = "tool_servers.db",
                 security_system: Optional[CommandWhitelistSystem] = None,
                 emergency_system: Optional[MultiChannelEmergencyStop] = None,
                 security_logger: Optional[EnhancedSecurityLogging] = None):
        self.server_type = server_type
        self.db_path = db_path
        self.security_system = security_system
        self.emergency_system = emergency_system
        self.security_logger = security_logger
        self.logger = logging.getLogger(f"tool_server.{server_type.value}")

        # Rate limiting
        self.rate_limits: Dict[str, Dict[str, Any]] = {}
        self.default_rate_limit = 100  # requests per hour

        # Authentication cache
        self.auth_cache: Dict[str, Dict[str, Any]] = {}
        self.auth_cache_ttl = 3600  # 1 hour

        # Operation tracking
        self.active_operations: Dict[str, ToolOperation] = {}
        self.operation_history: List[ToolOperationResult] = []

    async def initialize(self) -> bool:
        """Initialize the tool server"""
        try:
            await self._setup_database()
            await self._initialize_security()
            await self._load_configuration()

            self.logger.info(f"Tool server {self.server_type.value} initialized successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize tool server: {e}")
            return False

    async def _setup_database(self):
        """Setup SQLite database for tool server"""
        async with aiosqlite.connect(self.db_path) as db:
            # Operations table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS tool_operations (
                    operation_id TEXT PRIMARY KEY,
                    tool_type TEXT,
                    operation_name TEXT,
                    parameters TEXT,
                    user_id TEXT,
                    security_level TEXT,
                    timestamp TEXT,
                    session_id TEXT,
                    rollback_data TEXT,
                    audit_metadata TEXT
                )
            """)

            # Results table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS operation_results (
                    operation_id TEXT PRIMARY KEY,
                    success BOOLEAN,
                    result TEXT,
                    error_message TEXT,
                    execution_time REAL,
                    security_validated BOOLEAN,
                    rollback_id TEXT,
                    audit_trail TEXT,
                    FOREIGN KEY (operation_id) REFERENCES tool_operations (operation_id)
                )
            """)

            # Rate limiting table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS rate_limits (
                    user_id TEXT,
                    tool_type TEXT,
                    window_start TEXT,
                    request_count INTEGER,
                    PRIMARY KEY (user_id, tool_type, window_start)
                )
            """)

            # Authentication cache table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS auth_cache (
                    user_id TEXT PRIMARY KEY,
                    auth_token TEXT,
                    expires_at TEXT,
                    permissions TEXT
                )
            """)

            # Rollback data table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS rollback_data (
                    rollback_id TEXT PRIMARY KEY,
                    operation_id TEXT,
                    rollback_type TEXT,
                    rollback_data TEXT,
                    created_at TEXT,
                    expires_at TEXT,
                    FOREIGN KEY (operation_id) REFERENCES tool_operations (operation_id)
                )
            """)

            await db.commit()

    async def _initialize_security(self):
        """Initialize security systems"""
        if self.security_system:
            await self.security_system.initialize()

        if self.emergency_system:
            await self.emergency_system.initialize()

        if self.security_logger:
            await self.security_logger.initialize()

    async def _load_configuration(self):
        """Load tool server configuration"""
        # Override in subclasses for specific configuration
        pass

    async def execute_operation(self,
                              operation_name: str,
                              parameters: Dict[str, Any],
                              user_id: Optional[str] = None,
                              session_id: Optional[str] = None) -> ToolOperationResult:
        """Execute a tool operation with full security validation"""
        operation_id = str(uuid.uuid4())
        start_time = time.time()

        try:
            # Create operation record
            operation = ToolOperation(
                operation_id=operation_id,
                tool_type=self.server_type,
                operation_name=operation_name,
                parameters=parameters,
                user_id=user_id,
                security_level=await self._determine_security_level(operation_name, parameters),
                timestamp=datetime.now(),
                session_id=session_id
            )

            # Security validation
            security_context = await self._validate_security(operation)
            if not security_context.whitelist_validated:
                raise ToolServerSecurityError("Operation not whitelisted")

            if security_context.emergency_stop_active:
                raise ToolServerSecurityError("Emergency stop active")

            if not security_context.authentication_valid:
                raise ToolServerAuthenticationError("Authentication failed")

            if security_context.rate_limit_remaining <= 0:
                raise ToolServerRateLimitError("Rate limit exceeded")

            # Store operation
            await self._store_operation(operation)
            self.active_operations[operation_id] = operation

            # Execute the operation
            result_data = await self._execute_specific_operation(operation_name, parameters, security_context)

            # Create rollback data if needed
            rollback_id = None
            if await self._requires_rollback(operation_name):
                rollback_id = await self._create_rollback_data(operation, result_data)

            # Create result
            execution_time = time.time() - start_time
            result = ToolOperationResult(
                operation_id=operation_id,
                success=True,
                result=result_data,
                error_message=None,
                execution_time=execution_time,
                security_validated=True,
                rollback_id=rollback_id,
                audit_trail=await self._create_audit_trail(operation, result_data)
            )

            # Store result
            await self._store_result(result)

            # Update rate limiting
            await self._update_rate_limit(user_id)

            # Security logging
            if self.security_logger:
                await self.security_logger.log_tool_operation(
                    tool_type=self.server_type.value,
                    operation=operation_name,
                    user_id=user_id,
                    success=True,
                    execution_time=execution_time
                )

            return result

        except Exception as e:
            execution_time = time.time() - start_time
            error_result = ToolOperationResult(
                operation_id=operation_id,
                success=False,
                result=None,
                error_message=str(e),
                execution_time=execution_time,
                security_validated=False
            )

            await self._store_result(error_result)

            # Security logging for errors
            if self.security_logger:
                await self.security_logger.log_security_event(
                    event_type="tool_operation_error",
                    details={
                        "tool_type": self.server_type.value,
                        "operation": operation_name,
                        "error": str(e),
                        "user_id": user_id
                    }
                )

            raise

        finally:
            # Cleanup
            if operation_id in self.active_operations:
                del self.active_operations[operation_id]

    async def _validate_security(self, operation: ToolOperation) -> SecurityContext:
        """Validate security for operation"""
        # Check emergency stop
        emergency_active = False
        if self.emergency_system:
            emergency_active = self.emergency_system.is_emergency_active()

        # Check whitelist
        whitelist_validated = True
        if self.security_system:
            whitelist_validated = await self.security_system.is_command_allowed(
                f"{self.server_type.value}:{operation.operation_name}"
            )

        # Check authentication
        auth_valid = await self._validate_authentication(operation.user_id)

        # Check rate limiting
        rate_limit_remaining = await self._check_rate_limit(operation.user_id)

        return SecurityContext(
            user_id=operation.user_id,
            session_id=operation.session_id,
            permission_level="standard",
            rate_limit_remaining=rate_limit_remaining,
            authentication_valid=auth_valid,
            emergency_stop_active=emergency_active,
            whitelist_validated=whitelist_validated,
            audit_required=operation.security_level in [SecurityLevel.HIGH, SecurityLevel.CRITICAL]
        )

    async def _validate_authentication(self, user_id: Optional[str]) -> bool:
        """Validate user authentication"""
        if not user_id:
            return False

        # Check cache first
        if user_id in self.auth_cache:
            cache_entry = self.auth_cache[user_id]
            if datetime.fromisoformat(cache_entry["expires_at"]) > datetime.now():
                return cache_entry["valid"]

        # Check database
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT auth_token, expires_at FROM auth_cache WHERE user_id = ?",
                (user_id,)
            ) as cursor:
                row = await cursor.fetchone()
                if row and datetime.fromisoformat(row[1]) > datetime.now():
                    return True

        return False

    async def _check_rate_limit(self, user_id: Optional[str]) -> int:
        """Check rate limiting for user"""
        if not user_id:
            return 0

        current_hour = datetime.now().replace(minute=0, second=0, microsecond=0)

        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT request_count FROM rate_limits WHERE user_id = ? AND tool_type = ? AND window_start = ?",
                (user_id, self.server_type.value, current_hour.isoformat())
            ) as cursor:
                row = await cursor.fetchone()
                current_count = row[0] if row else 0

                return max(0, self.default_rate_limit - current_count)

    async def _update_rate_limit(self, user_id: Optional[str]):
        """Update rate limiting counter"""
        if not user_id:
            return

        current_hour = datetime.now().replace(minute=0, second=0, microsecond=0)

        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT OR REPLACE INTO rate_limits (user_id, tool_type, window_start, request_count)
                VALUES (?, ?, ?, COALESCE((SELECT request_count FROM rate_limits
                         WHERE user_id = ? AND tool_type = ? AND window_start = ?), 0) + 1)
            """, (user_id, self.server_type.value, current_hour.isoformat(),
                  user_id, self.server_type.value, current_hour.isoformat()))
            await db.commit()

    async def rollback_operation(self, rollback_id: str) -> bool:
        """Rollback a previous operation"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                async with db.execute(
                    "SELECT operation_id, rollback_type, rollback_data FROM rollback_data WHERE rollback_id = ?",
                    (rollback_id,)
                ) as cursor:
                    row = await cursor.fetchone()
                    if not row:
                        return False

                    operation_id, rollback_type, rollback_data_json = row
                    rollback_data = json.loads(rollback_data_json)

                    # Execute rollback
                    success = await self._execute_rollback(rollback_type, rollback_data)

                    if success and self.security_logger:
                        await self.security_logger.log_security_event(
                            event_type="operation_rollback",
                            details={
                                "rollback_id": rollback_id,
                                "operation_id": operation_id,
                                "rollback_type": rollback_type
                            }
                        )

                    return success

        except Exception as e:
            self.logger.error(f"Rollback failed: {e}")
            return False

    @abstractmethod
    async def _execute_specific_operation(self,
                                        operation_name: str,
                                        parameters: Dict[str, Any],
                                        security_context: SecurityContext) -> Dict[str, Any]:
        """Execute tool-specific operation - must be implemented by subclasses"""
        pass

    @abstractmethod
    async def _determine_security_level(self, operation_name: str, parameters: Dict[str, Any]) -> SecurityLevel:
        """Determine security level for operation - must be implemented by subclasses"""
        pass

    @abstractmethod
    async def _requires_rollback(self, operation_name: str) -> bool:
        """Check if operation requires rollback capability - must be implemented by subclasses"""
        pass

    @abstractmethod
    async def _create_rollback_data(self, operation: ToolOperation, result_data: Dict[str, Any]) -> str:
        """Create rollback data for operation - must be implemented by subclasses"""
        pass

    @abstractmethod
    async def _execute_rollback(self, rollback_type: str, rollback_data: Dict[str, Any]) -> bool:
        """Execute rollback operation - must be implemented by subclasses"""
        pass

    async def _store_operation(self, operation: ToolOperation):
        """Store operation in database"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO tool_operations
                (operation_id, tool_type, operation_name, parameters, user_id, security_level,
                 timestamp, session_id, rollback_data, audit_metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                operation.operation_id,
                operation.tool_type.value,
                operation.operation_name,
                json.dumps(operation.parameters),
                operation.user_id,
                operation.security_level.value,
                operation.timestamp.isoformat(),
                operation.session_id,
                json.dumps(operation.rollback_data) if operation.rollback_data else None,
                json.dumps(operation.audit_metadata) if operation.audit_metadata else None
            ))
            await db.commit()

    async def _store_result(self, result: ToolOperationResult):
        """Store operation result in database"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO operation_results
                (operation_id, success, result, error_message, execution_time,
                 security_validated, rollback_id, audit_trail)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                result.operation_id,
                result.success,
                json.dumps(result.result) if result.result else None,
                result.error_message,
                result.execution_time,
                result.security_validated,
                result.rollback_id,
                json.dumps(result.audit_trail) if result.audit_trail else None
            ))
            await db.commit()

    async def _create_audit_trail(self, operation: ToolOperation, result_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create audit trail for operation"""
        return [{
            "timestamp": datetime.now().isoformat(),
            "event": "operation_executed",
            "operation_id": operation.operation_id,
            "tool_type": operation.tool_type.value,
            "operation_name": operation.operation_name,
            "user_id": operation.user_id,
            "security_level": operation.security_level.value,
            "result_size": len(str(result_data)) if result_data else 0
        }]

    async def get_operation_history(self,
                                  user_id: Optional[str] = None,
                                  limit: int = 100) -> List[Dict[str, Any]]:
        """Get operation history"""
        async with aiosqlite.connect(self.db_path) as db:
            query = """
                SELECT o.operation_id, o.tool_type, o.operation_name, o.timestamp,
                       r.success, r.execution_time, r.error_message
                FROM tool_operations o
                LEFT JOIN operation_results r ON o.operation_id = r.operation_id
                WHERE 1=1
            """
            params = []

            if user_id:
                query += " AND o.user_id = ?"
                params.append(user_id)

            query += " ORDER BY o.timestamp DESC LIMIT ?"
            params.append(limit)

            async with db.execute(query, params) as cursor:
                rows = await cursor.fetchall()
                return [{
                    "operation_id": row[0],
                    "tool_type": row[1],
                    "operation_name": row[2],
                    "timestamp": row[3],
                    "success": row[4],
                    "execution_time": row[5],
                    "error_message": row[6]
                } for row in rows]

    async def cleanup_expired_data(self):
        """Cleanup expired data from database"""
        current_time = datetime.now()

        async with aiosqlite.connect(self.db_path) as db:
            # Clean expired auth cache
            await db.execute(
                "DELETE FROM auth_cache WHERE expires_at < ?",
                (current_time.isoformat(),)
            )

            # Clean expired rollback data
            await db.execute(
                "DELETE FROM rollback_data WHERE expires_at < ?",
                (current_time.isoformat(),)
            )

            # Clean old rate limit data (older than 24 hours)
            cutoff_time = current_time - timedelta(hours=24)
            await db.execute(
                "DELETE FROM rate_limits WHERE window_start < ?",
                (cutoff_time.isoformat(),)
            )

            await db.commit()


class ToolServerManager:
    """Manager for all essential tool servers"""

    def __init__(self):
        self.servers: Dict[ToolServerType, BaseToolServer] = {}
        self.logger = logging.getLogger("tool_server_manager")

    async def register_server(self, server: BaseToolServer):
        """Register a tool server"""
        await server.initialize()
        self.servers[server.server_type] = server
        self.logger.info(f"Registered tool server: {server.server_type.value}")

    async def execute_operation(self,
                              tool_type: ToolServerType,
                              operation_name: str,
                              parameters: Dict[str, Any],
                              user_id: Optional[str] = None,
                              session_id: Optional[str] = None) -> ToolOperationResult:
        """Execute operation on specific tool server"""
        if tool_type not in self.servers:
            raise ValueError(f"Tool server not found: {tool_type.value}")

        server = self.servers[tool_type]
        return await server.execute_operation(operation_name, parameters, user_id, session_id)

    async def rollback_operation(self, rollback_id: str) -> bool:
        """Rollback operation across all servers"""
        for server in self.servers.values():
            if await server.rollback_operation(rollback_id):
                return True
        return False

    async def cleanup_all_servers(self):
        """Cleanup expired data from all servers"""
        for server in self.servers.values():
            await server.cleanup_expired_data()

    async def get_server_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all tool servers"""
        status = {}
        for tool_type, server in self.servers.items():
            status[tool_type.value] = {
                "active_operations": len(server.active_operations),
                "total_operations": len(server.operation_history),
                "rate_limits": len(server.rate_limits)
            }
        return status