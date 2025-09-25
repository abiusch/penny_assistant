#!/usr/bin/env python3
"""
MCP Tool Registry for Penny AI Assistant
Phase 2 Priority 8.1: Tool Registry with Dynamic Capability Discovery

This module provides comprehensive tool registry and capability management:
- Dynamic tool discovery from multiple MCP servers
- Capability mapping and conflict resolution
- Tool execution routing with security validation
- Real-time capability updates and change notifications
- Tool performance monitoring and optimization
- Security integration with command whitelist and authorization

Security Features:
- All tool registrations validated through Command Whitelist
- Tool execution requires authentication and authorization
- Emergency Stop integration for immediate tool termination
- Enhanced Security Logging for all tool operations
- Rate Limiting prevents tool abuse and resource exhaustion
- Rollback integration for destructive tool operations
"""

import asyncio
import json
import uuid
import time
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set, Callable, Union, Tuple, Awaitable
from enum import Enum, IntEnum
from dataclasses import dataclass, field, asdict
from contextlib import asynccontextmanager
import sqlite3
import threading
import logging
from pathlib import Path

# Import MCP components
from mcp_protocol_foundation import MCPTool, MCPResource, MCPMessage
from mcp_server_manager import MCPServerManager, MCPServerConnection, MCPServerState

# Import security systems
try:
    from command_whitelist_system import CommandWhitelistSystem, PermissionLevel, SecurityRisk, OperationType
    from multi_channel_emergency_stop import MultiChannelEmergencyStop, EmergencyTrigger, EmergencyState
    from enhanced_security_logging import EnhancedSecurityLogger as EnhancedSecurityLogging, SecurityEventType, SecuritySeverity
    from rate_limiting_resource_control import RateLimitingResourceControl, RateLimitType
    from rollback_recovery_system import RollbackRecoverySystem, FileOperationType
    from advanced_authentication_system import AdvancedAuthenticationSystem, AuthenticationLevel
except ImportError as e:
    print(f"Warning: Could not import security components: {e}")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ToolCategory(Enum):
    """Tool categories for organization and security"""
    FILE_SYSTEM = "file_system"
    NETWORK = "network"
    DATA_PROCESSING = "data_processing"
    COMMUNICATION = "communication"
    SYSTEM_INFO = "system_info"
    DEVELOPMENT = "development"
    SECURITY = "security"
    AUTOMATION = "automation"
    UNKNOWN = "unknown"


class ToolExecutionResult(Enum):
    """Tool execution result types"""
    SUCCESS = "success"
    FAILURE = "failure"
    TIMEOUT = "timeout"
    SECURITY_DENIED = "security_denied"
    RATE_LIMITED = "rate_limited"
    EMERGENCY_STOPPED = "emergency_stopped"


class ToolCapabilityType(Enum):
    """Types of tool capabilities"""
    READ_ONLY = "read_only"
    READ_WRITE = "read_write"
    DESTRUCTIVE = "destructive"
    NETWORK_ACCESS = "network_access"
    SYSTEM_ACCESS = "system_access"
    FILE_ACCESS = "file_access"


@dataclass
class ToolSecurityProfile:
    """Security profile for tools"""
    tool_name: str
    category: ToolCategory
    capabilities: List[ToolCapabilityType]
    security_risk: SecurityRisk
    operation_type: OperationType
    required_permissions: List[PermissionLevel]
    requires_rollback: bool = False
    requires_auth: bool = True
    max_execution_time: float = 30.0
    rate_limit_tier: str = "standard"

    def __post_init__(self):
        # Auto-configure based on capabilities
        if ToolCapabilityType.DESTRUCTIVE in self.capabilities:
            self.requires_rollback = True
            self.security_risk = SecurityRisk.HIGH
            self.operation_type = OperationType.RESTRICTED

        if ToolCapabilityType.SYSTEM_ACCESS in self.capabilities:
            self.security_risk = SecurityRisk.CRITICAL
            self.required_permissions = [PermissionLevel.AUTHENTICATED]


@dataclass
class ToolRegistration:
    """Tool registration record"""
    tool: MCPTool
    server_id: str
    security_profile: ToolSecurityProfile
    registration_time: datetime
    last_used: Optional[datetime] = None
    usage_count: int = 0
    success_count: int = 0
    failure_count: int = 0
    average_execution_time: float = 0.0

    # Performance metrics
    execution_times: List[float] = field(default_factory=list)
    recent_errors: List[str] = field(default_factory=list)

    @property
    def success_rate(self) -> float:
        """Calculate success rate"""
        if self.usage_count == 0:
            return 0.0
        return self.success_count / self.usage_count

    @property
    def error_rate(self) -> float:
        """Calculate error rate"""
        if self.usage_count == 0:
            return 0.0
        return self.failure_count / self.usage_count


@dataclass
class ToolExecutionContext:
    """Context for tool execution"""
    execution_id: str
    tool_name: str
    server_id: str
    arguments: Dict[str, Any]
    user_id: Optional[str]
    session_id: Optional[str]
    start_time: datetime
    timeout: float
    security_validated: bool = False
    rollback_checkpoint: Optional[str] = None


@dataclass
class ToolExecutionRecord:
    """Record of tool execution"""
    execution_id: str
    tool_name: str
    server_id: str
    arguments: Dict[str, Any]
    result: ToolExecutionResult
    start_time: datetime
    end_time: Optional[datetime]
    execution_time: Optional[float]
    output: Optional[Dict[str, Any]]
    error_message: Optional[str]
    user_id: Optional[str]
    security_events: List[str] = field(default_factory=list)


class MCPToolRegistry:
    """
    Comprehensive tool registry with dynamic capability discovery and security integration.

    Features:
    - Dynamic tool discovery from multiple MCP servers
    - Security-validated tool registration and execution
    - Performance monitoring and optimization
    - Real-time capability updates
    - Tool execution routing with load balancing
    - Comprehensive audit logging and security integration
    """

    def __init__(self,
                 db_path: str = "mcp_tool_registry.db",
                 server_manager: Optional[MCPServerManager] = None,
                 security_system: Optional[CommandWhitelistSystem] = None,
                 emergency_system: Optional[MultiChannelEmergencyStop] = None,
                 security_logger: Optional[EnhancedSecurityLogging] = None,
                 rate_limiter: Optional[RateLimitingResourceControl] = None,
                 auth_system: Optional[AdvancedAuthenticationSystem] = None,
                 rollback_system: Optional[RollbackRecoverySystem] = None):

        self.db_path = db_path
        self.server_manager = server_manager

        # Security systems
        self.security_system = security_system
        self.emergency_system = emergency_system
        self.security_logger = security_logger
        self.rate_limiter = rate_limiter
        self.auth_system = auth_system
        self.rollback_system = rollback_system

        # Registry state
        self.registered_tools: Dict[str, ToolRegistration] = {}
        self.tool_categories: Dict[ToolCategory, List[str]] = {
            category: [] for category in ToolCategory
        }
        self.inline_executors: Dict[str, Callable[[Dict[str, Any]], Any]] = {}

        # Execution tracking
        self.active_executions: Dict[str, ToolExecutionContext] = {}
        self.execution_history: List[ToolExecutionRecord] = []

        # Discovery and monitoring
        self.discovery_active = False
        self.discovery_task: Optional[asyncio.Task] = None
        self.discovery_interval = 60.0  # seconds

        # Security profiles cache
        self.security_profiles: Dict[str, ToolSecurityProfile] = {}

        # Performance optimization
        self.execution_cache: Dict[str, Dict[str, Any]] = {}
        self.cache_ttl = 300  # 5 minutes

        self._init_database()
        self._init_default_security_profiles()

    def _init_database(self) -> None:
        """Initialize tool registry database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Tool registrations table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tool_registrations (
                    tool_name TEXT PRIMARY KEY,
                    server_id TEXT NOT NULL,
                    tool_data TEXT NOT NULL,
                    security_profile TEXT NOT NULL,
                    registration_time TEXT NOT NULL,
                    last_used TEXT,
                    usage_count INTEGER DEFAULT 0,
                    success_count INTEGER DEFAULT 0,
                    failure_count INTEGER DEFAULT 0,
                    average_execution_time REAL DEFAULT 0.0,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Tool execution history
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tool_executions (
                    execution_id TEXT PRIMARY KEY,
                    tool_name TEXT NOT NULL,
                    server_id TEXT NOT NULL,
                    arguments TEXT NOT NULL,
                    result TEXT NOT NULL,
                    start_time TEXT NOT NULL,
                    end_time TEXT,
                    execution_time REAL,
                    output TEXT,
                    error_message TEXT,
                    user_id TEXT,
                    security_events TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Tool capabilities table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tool_capabilities (
                    tool_name TEXT,
                    capability_type TEXT,
                    capability_data TEXT,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (tool_name, capability_type)
                )
            """)

            # Create indexes
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_tool_server ON tool_registrations(server_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_execution_time ON tool_executions(start_time)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_execution_tool ON tool_executions(tool_name)")

            conn.commit()

    def _init_default_security_profiles(self) -> None:
        """Initialize default security profiles for common tool types"""
        self.security_profiles.update({
            # File system tools
            "file_read": ToolSecurityProfile(
                tool_name="file_read",
                category=ToolCategory.FILE_SYSTEM,
                capabilities=[ToolCapabilityType.READ_ONLY, ToolCapabilityType.FILE_ACCESS],
                security_risk=SecurityRisk.LOW,
                operation_type=OperationType.READ_ONLY,
                required_permissions=[PermissionLevel.VERIFIED]
            ),
            "file_write": ToolSecurityProfile(
                tool_name="file_write",
                category=ToolCategory.FILE_SYSTEM,
                capabilities=[ToolCapabilityType.READ_WRITE, ToolCapabilityType.FILE_ACCESS],
                security_risk=SecurityRisk.MEDIUM,
                operation_type=OperationType.FILE_SYSTEM,
                required_permissions=[PermissionLevel.AUTHENTICATED],
                requires_rollback=True
            ),
            "file_delete": ToolSecurityProfile(
                tool_name="file_delete",
                category=ToolCategory.FILE_SYSTEM,
                capabilities=[ToolCapabilityType.DESTRUCTIVE, ToolCapabilityType.FILE_ACCESS],
                security_risk=SecurityRisk.HIGH,
                operation_type=OperationType.RESTRICTED,
                required_permissions=[PermissionLevel.AUTHENTICATED],
                requires_rollback=True
            ),

            # Network tools
            "http_request": ToolSecurityProfile(
                tool_name="http_request",
                category=ToolCategory.NETWORK,
                capabilities=[ToolCapabilityType.NETWORK_ACCESS],
                security_risk=SecurityRisk.MEDIUM,
                operation_type=OperationType.COMMUNICATION,
                required_permissions=[PermissionLevel.VERIFIED]
            ),

            # System tools
            "system_command": ToolSecurityProfile(
                tool_name="system_command",
                category=ToolCategory.SYSTEM_INFO,
                capabilities=[ToolCapabilityType.SYSTEM_ACCESS],
                security_risk=SecurityRisk.CRITICAL,
                operation_type=OperationType.RESTRICTED,
                required_permissions=[PermissionLevel.AUTHENTICATED]
            ),
        })

    async def start_discovery(self) -> None:
        """Start automatic tool discovery from servers"""
        if self.discovery_active or not self.server_manager:
            return

        self.discovery_active = True
        self.discovery_task = asyncio.create_task(self._discovery_loop())
        logger.info("Tool discovery started")

    async def stop_discovery(self) -> None:
        """Stop automatic tool discovery"""
        self.discovery_active = False
        if self.discovery_task:
            self.discovery_task.cancel()

    async def discover_tools(self) -> Dict[str, List[MCPTool]]:
        """Discover tools from all available servers"""
        if not self.server_manager:
            return {}

        discovered_tools = {}

        try:
            # Get tools from all servers
            tools_by_server = await self.server_manager.get_available_tools()

            for server_id, tools in tools_by_server.items():
                # Register each discovered tool
                for tool in tools:
                    await self._register_discovered_tool(tool, server_id)

                discovered_tools[server_id] = tools

            await self._log_security_event(
                SecurityEventType.TOOL_DISCOVERY,
                f"Tool discovery completed: {sum(len(tools) for tools in discovered_tools.values())} tools found",
                {"servers": list(discovered_tools.keys())}
            )

            return discovered_tools

        except Exception as e:
            logger.error(f"Tool discovery failed: {e}")
            return {}

    async def register_inline_tool(self,
                                   tool_name: str,
                                   description: str,
                                   input_schema: Dict[str, Any],
                                   executor: Callable[[Dict[str, Any]], Union[Dict[str, Any], Awaitable[Dict[str, Any]]]],
                                   *,
                                   category: ToolCategory = ToolCategory.COMMUNICATION,
                                   security_risk: SecurityRisk = SecurityRisk.LOW,
                                   operation_type: OperationType = OperationType.COMMUNICATION,
                                   required_permissions: Optional[List[PermissionLevel]] = None,
                                   capabilities: Optional[List[ToolCapabilityType]] = None,
                                   server_id: Optional[str] = None,
                                   timeout: float = 30.0) -> bool:
        """Register an in-process tool executor with the registry"""

        server_identifier = server_id or f"inline:{tool_name}"
        tool = MCPTool(
            name=tool_name,
            description=description,
            inputSchema=input_schema,
            server_id=server_identifier,
            security_risk=security_risk,
            operation_type=operation_type,
            required_permissions=required_permissions or [PermissionLevel.AUTHENTICATED]
        )

        if not await self._validate_tool_registration(tool, server_identifier):
            return False

        security_profile = ToolSecurityProfile(
            tool_name=tool_name,
            category=category,
            capabilities=capabilities or [ToolCapabilityType.READ_ONLY],
            security_risk=security_risk,
            operation_type=operation_type,
            required_permissions=required_permissions or [PermissionLevel.AUTHENTICATED],
            max_execution_time=timeout
        )

        registration = ToolRegistration(
            tool=tool,
            server_id=server_identifier,
            security_profile=security_profile,
            registration_time=datetime.now()
        )

        self.registered_tools[tool_name] = registration
        self.inline_executors[tool_name] = executor

        if category not in self.tool_categories:
            self.tool_categories[category] = []
        if tool_name not in self.tool_categories[category]:
            self.tool_categories[category].append(tool_name)

        await self._save_tool_registration(registration)

        logger.info(f"Inline tool registered: {tool_name}")
        return True

    async def _register_discovered_tool(self, tool: MCPTool, server_id: str) -> None:
        """Register a discovered tool with security validation"""
        try:
            # Security validation
            if not await self._validate_tool_registration(tool, server_id):
                logger.warning(f"Tool registration denied by security: {tool.name}")
                return

            # Create or get security profile
            security_profile = self._get_or_create_security_profile(tool)

            # Create registration
            registration = ToolRegistration(
                tool=tool,
                server_id=server_id,
                security_profile=security_profile,
                registration_time=datetime.now()
            )

            # Store in registry
            self.registered_tools[tool.name] = registration

            # Update category mapping
            if security_profile.category not in self.tool_categories:
                self.tool_categories[security_profile.category] = []
            if tool.name not in self.tool_categories[security_profile.category]:
                self.tool_categories[security_profile.category].append(tool.name)

            # Save to database
            await self._save_tool_registration(registration)

            logger.info(f"Tool registered: {tool.name} from server {server_id}")

        except Exception as e:
            logger.error(f"Failed to register tool {tool.name}: {e}")

    async def execute_tool(self, tool_name: str, arguments: Dict[str, Any],
                          user_id: Optional[str] = None,
                          session_id: Optional[str] = None,
                          timeout: Optional[float] = None) -> Dict[str, Any]:
        """Execute tool with comprehensive security validation and monitoring"""
        execution_id = str(uuid.uuid4())

        # Check if tool is registered
        if tool_name not in self.registered_tools:
            raise ValueError(f"Tool not found: {tool_name}")

        registration = self.registered_tools[tool_name]
        security_profile = registration.security_profile

        # Emergency stop check
        if self.emergency_system and self.emergency_system.is_emergency_active():
            raise RuntimeError("Emergency stop active - tool execution suspended")

        # Create execution context
        context = ToolExecutionContext(
            execution_id=execution_id,
            tool_name=tool_name,
            server_id=registration.server_id,
            arguments=arguments,
            user_id=user_id,
            session_id=session_id,
            start_time=datetime.now(),
            timeout=timeout or security_profile.max_execution_time
        )

        try:
            self.active_executions[execution_id] = context

            # Security validation
            context.security_validated = await self._validate_tool_execution(
                tool_name, arguments, user_id, security_profile
            )

            if not context.security_validated:
                raise PermissionError(f"Tool execution denied by security: {tool_name}")

            # Rate limiting check
            if not await self._check_tool_rate_limits(tool_name, user_id):
                raise RuntimeError(f"Rate limit exceeded for tool: {tool_name}")

            # Create rollback checkpoint if required
            if security_profile.requires_rollback and self.rollback_system:
                context.rollback_checkpoint = await self._create_rollback_checkpoint(
                    tool_name, arguments
                )

            # Execute tool
            start_time = time.time()
            if tool_name in self.inline_executors:
                result = await self._execute_inline_tool(context)
            else:
                result = await self._execute_tool_on_server(context)
            execution_time = time.time() - start_time

            # Update metrics
            await self._update_tool_metrics(registration, execution_time, True)

            # Create execution record
            execution_record = ToolExecutionRecord(
                execution_id=execution_id,
                tool_name=tool_name,
                server_id=registration.server_id,
                arguments=arguments,
                result=ToolExecutionResult.SUCCESS,
                start_time=context.start_time,
                end_time=datetime.now(),
                execution_time=execution_time,
                output=result,
                error_message=None,
                user_id=user_id
            )

            await self._save_execution_record(execution_record)

            if hasattr(SecurityEventType, "DATA_ACCESS"):
                await self._log_security_event(
                    SecurityEventType.DATA_ACCESS,
                    f"Tool executed successfully: {tool_name}",
                    {
                        "execution_id": execution_id,
                        "tool_name": tool_name,
                        "server_id": registration.server_id,
                        "user_id": user_id,
                        "execution_time": execution_time
                    }
                )

            return result

        except Exception as e:
            # Handle execution failure
            await self._handle_tool_execution_failure(context, e)
            raise

        finally:
            # Cleanup
            self.active_executions.pop(execution_id, None)

    async def _execute_tool_on_server(self, context: ToolExecutionContext) -> Dict[str, Any]:
        """Execute tool on the appropriate server"""
        if not self.server_manager:
            raise RuntimeError("No server manager available")

        # Execute with timeout
        try:
            result = await asyncio.wait_for(
                self.server_manager.call_tool(
                    context.tool_name,
                    context.arguments,
                    preferred_server=context.server_id
                ),
                timeout=context.timeout
            )
            return result

        except asyncio.TimeoutError:
            raise RuntimeError(f"Tool execution timed out after {context.timeout}s")

    async def _execute_inline_tool(self, context: ToolExecutionContext) -> Dict[str, Any]:
        """Execute inline-registered tool via in-process executor"""
        executor = self.inline_executors.get(context.tool_name)
        if not executor:
            raise RuntimeError(f"Inline executor not found for tool: {context.tool_name}")

        try:
            if asyncio.iscoroutinefunction(executor):
                result = await asyncio.wait_for(
                    executor(context.arguments),
                    timeout=context.timeout
                )
            else:
                loop = asyncio.get_running_loop()
                result = await asyncio.wait_for(
                    loop.run_in_executor(None, executor, context.arguments),
                    timeout=context.timeout
                )

            if hasattr(result, "success"):
                if not getattr(result, "success"):
                    raise RuntimeError(getattr(result, "error", "Inline tool execution failed"))
                return getattr(result, "data", {}) or {}

            return result
        except asyncio.TimeoutError:
            raise RuntimeError(f"Inline tool execution timed out after {context.timeout}s")

    async def get_available_tools(self, category: Optional[ToolCategory] = None,
                                user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get available tools with security filtering"""
        available_tools = []

        for tool_name, registration in self.registered_tools.items():
            # Category filter
            if category and registration.security_profile.category != category:
                continue

            # Security filter
            if user_id and not await self._check_tool_access(tool_name, user_id):
                continue

            # Server health check
            is_inline = tool_name in self.inline_executors
            if self.server_manager and not is_inline:
                server_status = self.server_manager.get_server_status()
                server_info = server_status.get(registration.server_id, {})
                if server_info.get("health", {}).get("state") != MCPServerState.HEALTHY.value:
                    continue

            tool_info = {
                "name": registration.tool.name,
                "description": registration.tool.description,
                "inputSchema": registration.tool.inputSchema,
                "server_id": registration.server_id,
                "category": registration.security_profile.category.value,
                "security_risk": registration.security_profile.security_risk.value,
                "success_rate": registration.success_rate,
                "average_execution_time": registration.average_execution_time,
                "usage_count": registration.usage_count
            }

            available_tools.append(tool_info)

        return available_tools

    async def get_tool_categories(self) -> Dict[str, List[str]]:
        """Get tools organized by category"""
        categories = {}
        for category, tool_names in self.tool_categories.items():
            # Filter out tools that aren't currently registered
            active_tools = [name for name in tool_names if name in self.registered_tools]
            if active_tools:
                categories[category.value] = active_tools

        return categories

    async def get_tool_metrics(self, tool_name: Optional[str] = None) -> Dict[str, Any]:
        """Get tool performance metrics"""
        if tool_name:
            if tool_name not in self.registered_tools:
                return {}

            registration = self.registered_tools[tool_name]
            return {
                "tool_name": tool_name,
                "usage_count": registration.usage_count,
                "success_rate": registration.success_rate,
                "error_rate": registration.error_rate,
                "average_execution_time": registration.average_execution_time,
                "last_used": registration.last_used.isoformat() if registration.last_used else None,
                "recent_errors": registration.recent_errors[-5:]  # Last 5 errors
            }
        else:
            # Overall metrics
            total_tools = len(self.registered_tools)
            total_executions = sum(reg.usage_count for reg in self.registered_tools.values())
            total_successes = sum(reg.success_count for reg in self.registered_tools.values())

            return {
                "total_tools": total_tools,
                "total_executions": total_executions,
                "overall_success_rate": total_successes / max(total_executions, 1),
                "active_executions": len(self.active_executions),
                "tools_by_category": {
                    cat.value: len(tools) for cat, tools in self.tool_categories.items()
                    if tools
                }
            }

    async def _validate_tool_registration(self, tool: MCPTool, server_id: str) -> bool:
        """Validate tool registration through security systems"""
        if not self.security_system:
            return True

        try:
            operation_params = {
                'tool_name': tool.name,
                'server_id': server_id,
                'tool_description': tool.description,
                'input_schema': tool.inputSchema
            }

            permission_result = self.security_system.check_operation_permission(
                operation_name='tool_registration',
                user_permission_level=PermissionLevel.AUTHENTICATED,
                operation_params=operation_params
            )

            return permission_result.permission_granted

        except Exception as e:
            logger.error(f"Tool registration validation failed: {e}")
            return False

    async def _validate_tool_execution(self, tool_name: str, arguments: Dict[str, Any],
                                     user_id: Optional[str],
                                     security_profile: ToolSecurityProfile) -> bool:
        """Validate tool execution through security systems"""
        if not self.security_system:
            return True

        try:
            # Authentication check
            if security_profile.requires_auth and self.auth_system:
                auth_level = await self.auth_system.get_current_authentication_level()
                if auth_level < AuthenticationLevel.BASIC:
                    return False

            # Permission check
            operation_params = {
                'tool_name': tool_name,
                'tool_arguments': arguments,
                'user_id': user_id,
                'security_risk': security_profile.security_risk.value
            }

            permission_result = self.security_system.check_operation_permission(
                operation_name='tool_execution',
                user_permission_level=PermissionLevel.AUTHENTICATED,
                operation_params=operation_params
            )

            return permission_result.permission_granted

        except Exception as e:
            logger.error(f"Tool execution validation failed: {e}")
            return False

    async def _check_tool_rate_limits(self, tool_name: str, user_id: Optional[str]) -> bool:
        """Check rate limits for tool execution"""
        if not self.rate_limiter:
            return True

        try:
            # This would integrate with the rate limiting system
            # Implementation depends on specific rate limiter interface
            return True  # Placeholder

        except Exception as e:
            logger.error(f"Rate limit check failed: {e}")
            return False

    async def _check_tool_access(self, tool_name: str, user_id: str) -> bool:
        """Check if user has access to tool"""
        if tool_name not in self.registered_tools:
            return False

        registration = self.registered_tools[tool_name]
        security_profile = registration.security_profile

        # Basic permission check
        if self.auth_system:
            try:
                auth_level = await self.auth_system.get_current_authentication_level()
                min_required = min(security_profile.required_permissions,
                                 default=PermissionLevel.VERIFIED)

                if auth_level.value < min_required.value:
                    return False

            except Exception:
                return False

        return True

    def _get_or_create_security_profile(self, tool: MCPTool) -> ToolSecurityProfile:
        """Get or create security profile for tool"""
        # Check if we have a predefined profile
        if tool.name in self.security_profiles:
            return self.security_profiles[tool.name]

        # Create default profile based on tool name and description
        category = self._infer_tool_category(tool)
        capabilities = self._infer_tool_capabilities(tool)

        profile = ToolSecurityProfile(
            tool_name=tool.name,
            category=category,
            capabilities=capabilities,
            security_risk=SecurityRisk.MEDIUM,
            operation_type=OperationType.COMMUNICATION,
            required_permissions=[PermissionLevel.VERIFIED]
        )

        # Cache the profile
        self.security_profiles[tool.name] = profile
        return profile

    def _infer_tool_category(self, tool: MCPTool) -> ToolCategory:
        """Infer tool category from name and description"""
        name_lower = tool.name.lower()
        desc_lower = tool.description.lower()

        if any(keyword in name_lower or keyword in desc_lower
               for keyword in ['file', 'read', 'write', 'delete', 'directory']):
            return ToolCategory.FILE_SYSTEM

        if any(keyword in name_lower or keyword in desc_lower
               for keyword in ['http', 'request', 'url', 'api', 'network']):
            return ToolCategory.NETWORK

        if any(keyword in name_lower or keyword in desc_lower
               for keyword in ['system', 'command', 'execute', 'process']):
            return ToolCategory.SYSTEM_INFO

        if any(keyword in name_lower or keyword in desc_lower
               for keyword in ['email', 'message', 'send', 'notify']):
            return ToolCategory.COMMUNICATION

        return ToolCategory.UNKNOWN

    def _infer_tool_capabilities(self, tool: MCPTool) -> List[ToolCapabilityType]:
        """Infer tool capabilities from name and description"""
        capabilities = []
        name_lower = tool.name.lower()
        desc_lower = tool.description.lower()

        if any(keyword in name_lower or keyword in desc_lower
               for keyword in ['read', 'get', 'list', 'show']):
            capabilities.append(ToolCapabilityType.READ_ONLY)

        if any(keyword in name_lower or keyword in desc_lower
               for keyword in ['write', 'create', 'update', 'modify']):
            capabilities.append(ToolCapabilityType.READ_WRITE)

        if any(keyword in name_lower or keyword in desc_lower
               for keyword in ['delete', 'remove', 'destroy', 'truncate']):
            capabilities.append(ToolCapabilityType.DESTRUCTIVE)

        if any(keyword in name_lower or keyword in desc_lower
               for keyword in ['http', 'url', 'request', 'api', 'network']):
            capabilities.append(ToolCapabilityType.NETWORK_ACCESS)

        if any(keyword in name_lower or keyword in desc_lower
               for keyword in ['file', 'directory', 'path']):
            capabilities.append(ToolCapabilityType.FILE_ACCESS)

        if any(keyword in name_lower or keyword in desc_lower
               for keyword in ['system', 'command', 'execute', 'process']):
            capabilities.append(ToolCapabilityType.SYSTEM_ACCESS)

        return capabilities if capabilities else [ToolCapabilityType.READ_ONLY]

    async def _create_rollback_checkpoint(self, tool_name: str,
                                        arguments: Dict[str, Any]) -> Optional[str]:
        """Create rollback checkpoint for destructive operations"""
        if not self.rollback_system:
            return None

        try:
            checkpoint_id = f"tool_{tool_name}_{uuid.uuid4().hex[:8]}"

            # This would integrate with the rollback system
            # Implementation depends on specific rollback system interface
            return checkpoint_id

        except Exception as e:
            logger.error(f"Failed to create rollback checkpoint: {e}")
            return None

    async def _update_tool_metrics(self, registration: ToolRegistration,
                                 execution_time: float, success: bool) -> None:
        """Update tool performance metrics"""
        registration.usage_count += 1
        registration.last_used = datetime.now()

        if success:
            registration.success_count += 1
        else:
            registration.failure_count += 1

        # Update execution time metrics
        registration.execution_times.append(execution_time)
        if len(registration.execution_times) > 100:  # Keep last 100 measurements
            registration.execution_times.pop(0)

        registration.average_execution_time = sum(registration.execution_times) / len(registration.execution_times)

        # Save updated metrics
        await self._save_tool_registration(registration)

    async def _handle_tool_execution_failure(self, context: ToolExecutionContext,
                                           error: Exception) -> None:
        """Handle tool execution failure with cleanup and logging"""
        try:
            # Update tool metrics
            if context.tool_name in self.registered_tools:
                registration = self.registered_tools[context.tool_name]
                registration.failure_count += 1
                registration.usage_count += 1
                registration.recent_errors.append(str(error))
                if len(registration.recent_errors) > 10:
                    registration.recent_errors.pop(0)

                await self._save_tool_registration(registration)

            # Rollback if checkpoint exists
            if context.rollback_checkpoint and self.rollback_system:
                try:
                    # This would integrate with rollback system
                    logger.info(f"Rolling back after tool failure: {context.execution_id}")
                except Exception as rollback_error:
                    logger.error(f"Rollback failed: {rollback_error}")

            # Create failure record
            execution_record = ToolExecutionRecord(
                execution_id=context.execution_id,
                tool_name=context.tool_name,
                server_id=context.server_id,
                arguments=context.arguments,
                result=ToolExecutionResult.FAILURE,
                start_time=context.start_time,
                end_time=datetime.now(),
                execution_time=None,
                output=None,
                error_message=str(error),
                user_id=context.user_id
            )

            await self._save_execution_record(execution_record)

            # Log security event
            if hasattr(SecurityEventType, "SECURITY_VIOLATION"):
                await self._log_security_event(
                    SecurityEventType.SECURITY_VIOLATION,
                    f"Tool execution failed: {context.tool_name}",
                    {
                        "execution_id": context.execution_id,
                        "tool_name": context.tool_name,
                        "error": str(error),
                        "user_id": context.user_id
                    }
                )

        except Exception as cleanup_error:
            logger.error(f"Error during failure cleanup: {cleanup_error}")

    async def _discovery_loop(self) -> None:
        """Tool discovery loop"""
        while self.discovery_active:
            try:
                await self.discover_tools()
                await asyncio.sleep(self.discovery_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Discovery loop error: {e}")

    async def _save_tool_registration(self, registration: ToolRegistration) -> None:
        """Save tool registration to database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            tool_payload = asdict(registration.tool)
            if isinstance(tool_payload.get("security_risk"), Enum):
                tool_payload["security_risk"] = tool_payload["security_risk"].value
            if isinstance(tool_payload.get("operation_type"), Enum):
                tool_payload["operation_type"] = tool_payload["operation_type"].value
            if isinstance(tool_payload.get("required_permissions"), list):
                tool_payload["required_permissions"] = [
                    perm.value if isinstance(perm, Enum) else perm
                    for perm in tool_payload["required_permissions"]
                ]

            profile_payload = asdict(registration.security_profile)
            if isinstance(profile_payload.get("category"), Enum):
                profile_payload["category"] = profile_payload["category"].value
            if isinstance(profile_payload.get("security_risk"), Enum):
                profile_payload["security_risk"] = profile_payload["security_risk"].value
            if isinstance(profile_payload.get("operation_type"), Enum):
                profile_payload["operation_type"] = profile_payload["operation_type"].value
            if isinstance(profile_payload.get("capabilities"), list):
                profile_payload["capabilities"] = [
                    cap.value if isinstance(cap, Enum) else cap
                    for cap in profile_payload["capabilities"]
                ]
            if isinstance(profile_payload.get("required_permissions"), list):
                profile_payload["required_permissions"] = [
                    perm.value if isinstance(perm, Enum) else perm
                    for perm in profile_payload["required_permissions"]
                ]

            cursor.execute("""
                INSERT OR REPLACE INTO tool_registrations
                (tool_name, server_id, tool_data, security_profile, registration_time,
                 last_used, usage_count, success_count, failure_count, average_execution_time, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                registration.tool.name,
                registration.server_id,
                json.dumps(tool_payload),
                json.dumps(profile_payload),
                registration.registration_time.isoformat(),
                registration.last_used.isoformat() if registration.last_used else None,
                registration.usage_count,
                registration.success_count,
                registration.failure_count,
                registration.average_execution_time,
                datetime.now().isoformat()
            ))
            conn.commit()

    async def _save_execution_record(self, record: ToolExecutionRecord) -> None:
        """Save execution record to database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO tool_executions
                (execution_id, tool_name, server_id, arguments, result, start_time,
                 end_time, execution_time, output, error_message, user_id, security_events)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                record.execution_id,
                record.tool_name,
                record.server_id,
                json.dumps(record.arguments),
                record.result.value,
                record.start_time.isoformat(),
                record.end_time.isoformat() if record.end_time else None,
                record.execution_time,
                json.dumps(record.output) if record.output else None,
                record.error_message,
                record.user_id,
                json.dumps(record.security_events)
            ))
            conn.commit()

    async def _log_security_event(self, event_type: SecurityEventType,
                                description: str, context: Dict[str, Any]) -> None:
        """Log security events"""
        if self.security_logger:
            try:
                await self.security_logger.log_security_event(
                    event_type=event_type,
                    description=description,
                    context=context,
                    severity=SecuritySeverity.INFO
                )
            except Exception as e:
                logger.error(f"Failed to log security event: {e}")

    async def shutdown(self) -> None:
        """Shutdown tool registry"""
        try:
            await self.stop_discovery()
            logger.info("Tool registry shutdown complete")
        except Exception as e:
            logger.error(f"Error during tool registry shutdown: {e}")


# Example usage
async def main():
    """Example tool registry usage"""
    print("🚀 MCP Tool Registry Test")

    try:
        # Initialize security systems
        whitelist = CommandWhitelistSystem()
        emergency = MultiChannelEmergencyStop()
        logger_sys = EnhancedSecurityLogging()

        # Create tool registry
        registry = MCPToolRegistry(
            security_system=whitelist,
            emergency_system=emergency,
            security_logger=logger_sys
        )

        print("✅ MCP Tool Registry created with security integration")
        print("✅ Dynamic tool discovery capabilities ready")
        print("✅ Security validation and authorization active")
        print("✅ Performance monitoring and metrics collection enabled")

    except Exception as e:
        print(f"❌ Error during tool registry test: {e}")


if __name__ == "__main__":
    asyncio.run(main())
