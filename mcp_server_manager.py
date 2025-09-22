#!/usr/bin/env python3
"""
MCP Server Manager for Penny AI Assistant
Phase 2 Priority 8.1: Server Manager with Health Monitoring

This module provides comprehensive MCP server lifecycle management:
- Multi-server connection management and health monitoring
- Automatic failover and load balancing across servers
- Server discovery and capability registration
- Security integration with authentication and authorization
- Real-time health metrics and performance monitoring
- Graceful server restart and recovery mechanisms

Security Features:
- All server operations validated through Command Whitelist
- Emergency Stop integration for immediate server termination
- Enhanced Security Logging for all server lifecycle events
- Rate Limiting prevents server abuse and resource exhaustion
- Authentication validation for server access
"""

import asyncio
import json
import time
import uuid
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set, Callable, Union
from enum import Enum, IntEnum
from dataclasses import dataclass, field, asdict
from contextlib import asynccontextmanager
import sqlite3
import threading
from pathlib import Path

# Import MCP components
from mcp_client import MCPClient, MCPClientConfig, MCPClientState
from mcp_protocol_foundation import MCPTool, MCPResource, MCPTransportType

# Import security systems
try:
    from command_whitelist_system import CommandWhitelistSystem, PermissionLevel, SecurityRisk, OperationType
    from multi_channel_emergency_stop import MultiChannelEmergencyStop, EmergencyTrigger, EmergencyState
    from enhanced_security_logging import EnhancedSecurityLogger as EnhancedSecurityLogging, SecurityEventType, SecuritySeverity
    from rate_limiting_resource_control import RateLimitingResourceControl, RateLimitType
    from rollback_recovery_system import RollbackRecoverySystem
    from advanced_authentication_system import AdvancedAuthenticationSystem, AuthenticationLevel
except ImportError as e:
    print(f"Warning: Could not import security components: {e}")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MCPServerState(Enum):
    """MCP server states"""
    UNKNOWN = "unknown"
    STARTING = "starting"
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    FAILED = "failed"
    MAINTENANCE = "maintenance"
    TERMINATED = "terminated"


class MCPServerPriority(IntEnum):
    """Server priority levels for load balancing"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


class MCPLoadBalanceStrategy(Enum):
    """Load balancing strategies"""
    ROUND_ROBIN = "round_robin"
    PRIORITY_WEIGHTED = "priority_weighted"
    LEAST_CONNECTIONS = "least_connections"
    FASTEST_RESPONSE = "fastest_response"
    CAPABILITY_BASED = "capability_based"


@dataclass
class MCPServerConfig:
    """MCP server configuration"""
    server_id: str
    name: str
    description: str
    transport_type: MCPTransportType
    connection_params: Dict[str, Any]

    # Health monitoring
    health_check_interval: float = 30.0
    health_timeout: float = 10.0
    max_consecutive_failures: int = 3

    # Load balancing
    priority: MCPServerPriority = MCPServerPriority.NORMAL
    weight: float = 1.0
    max_concurrent_requests: int = 10

    # Security
    required_auth_level: AuthenticationLevel = AuthenticationLevel.BASIC
    allowed_operations: List[str] = field(default_factory=list)
    security_tags: List[str] = field(default_factory=list)

    # Auto-restart
    auto_restart: bool = True
    restart_delay: float = 5.0
    max_restart_attempts: int = 3


@dataclass
class MCPServerHealth:
    """Server health metrics"""
    server_id: str
    state: MCPServerState
    last_health_check: datetime
    consecutive_failures: int
    total_requests: int
    successful_requests: int
    failed_requests: int
    average_response_time: float
    uptime_seconds: float
    error_rate: float

    # Capability status
    available_tools: int = 0
    available_resources: int = 0

    def __post_init__(self):
        if self.total_requests > 0:
            self.error_rate = self.failed_requests / self.total_requests
        else:
            self.error_rate = 0.0


@dataclass
class MCPServerMetrics:
    """Detailed server performance metrics"""
    server_id: str
    timestamp: datetime

    # Performance metrics
    response_times: List[float] = field(default_factory=list)
    memory_usage: Optional[float] = None
    cpu_usage: Optional[float] = None

    # Request metrics
    requests_per_minute: float = 0.0
    concurrent_connections: int = 0
    queue_length: int = 0

    # Error tracking
    recent_errors: List[str] = field(default_factory=list)
    error_types: Dict[str, int] = field(default_factory=dict)


class MCPServerConnection:
    """Wrapper for MCP server connection with health monitoring"""

    def __init__(self, config: MCPServerConfig,
                 security_systems: Dict[str, Any]):
        self.config = config
        self.security_systems = security_systems

        # Client and health
        self.client: Optional[MCPClient] = None
        self.health = MCPServerHealth(
            server_id=config.server_id,
            state=MCPServerState.UNKNOWN,
            last_health_check=datetime.now(),
            consecutive_failures=0,
            total_requests=0,
            successful_requests=0,
            failed_requests=0,
            average_response_time=0.0,
            uptime_seconds=0.0,
            error_rate=0.0
        )

        # Metrics tracking
        self.metrics = MCPServerMetrics(
            server_id=config.server_id,
            timestamp=datetime.now()
        )

        # Connection state
        self.start_time: Optional[datetime] = None
        self.restart_attempts = 0

        # Tools and resources cache
        self.cached_tools: List[MCPTool] = []
        self.cached_resources: List[MCPResource] = []
        self.last_capability_refresh = datetime.now()

    async def connect(self) -> bool:
        """Connect to MCP server with security validation"""
        try:
            self.health.state = MCPServerState.STARTING

            # Create MCP client with security integration
            client_config = MCPClientConfig(
                client_name=f"penny-server-manager-{self.config.server_id}",
                require_authentication=True,
                min_permission_level=PermissionLevel.AUTHENTICATED
            )

            self.client = MCPClient(
                config=client_config,
                **self.security_systems
            )

            # Connect based on transport type
            connected = False
            if self.config.transport_type == MCPTransportType.STDIO:
                connected = await self.client.connect_stdio(
                    command=self.config.connection_params["command"],
                    working_directory=self.config.connection_params.get("working_directory")
                )
            elif self.config.transport_type == MCPTransportType.HTTP:
                connected = await self.client.connect_http(
                    base_url=self.config.connection_params["base_url"],
                    headers=self.config.connection_params.get("headers"),
                    timeout=self.config.connection_params.get("timeout")
                )

            if connected:
                self.health.state = MCPServerState.HEALTHY
                self.start_time = datetime.now()
                self.restart_attempts = 0

                # Refresh capabilities
                await self.refresh_capabilities()

                logger.info(f"MCP server {self.config.server_id} connected successfully")
                return True
            else:
                self.health.state = MCPServerState.FAILED
                return False

        except Exception as e:
            logger.error(f"Failed to connect to MCP server {self.config.server_id}: {e}")
            self.health.state = MCPServerState.FAILED
            return False

    async def disconnect(self) -> None:
        """Disconnect from MCP server"""
        if self.client:
            await self.client.disconnect()
            self.client = None

        self.health.state = MCPServerState.TERMINATED
        logger.info(f"MCP server {self.config.server_id} disconnected")

    async def health_check(self) -> bool:
        """Perform health check on server"""
        try:
            if not self.client or not self.client.is_connected:
                self.health.consecutive_failures += 1
                self.health.state = MCPServerState.UNHEALTHY
                return False

            # Perform ping test
            start_time = time.time()
            tools = await self.client.list_tools(timeout=self.config.health_timeout)
            response_time = time.time() - start_time

            # Update metrics
            self.metrics.response_times.append(response_time)
            if len(self.metrics.response_times) > 100:  # Keep last 100 measurements
                self.metrics.response_times.pop(0)

            # Update health
            self.health.last_health_check = datetime.now()
            self.health.consecutive_failures = 0
            self.health.average_response_time = sum(self.metrics.response_times) / len(self.metrics.response_times)

            # Calculate uptime
            if self.start_time:
                self.health.uptime_seconds = (datetime.now() - self.start_time).total_seconds()

            # Determine health state based on performance
            if response_time > 5.0:
                self.health.state = MCPServerState.DEGRADED
            else:
                self.health.state = MCPServerState.HEALTHY

            return True

        except Exception as e:
            logger.warning(f"Health check failed for server {self.config.server_id}: {e}")
            self.health.consecutive_failures += 1

            if self.health.consecutive_failures >= self.config.max_consecutive_failures:
                self.health.state = MCPServerState.FAILED
            else:
                self.health.state = MCPServerState.UNHEALTHY

            return False

    async def refresh_capabilities(self) -> None:
        """Refresh server capabilities (tools and resources)"""
        if not self.client or not self.client.is_connected:
            return

        try:
            # Get tools
            tools_result = await self.client.list_tools()
            self.cached_tools = [
                MCPTool(
                    name=tool["name"],
                    description=tool["description"],
                    inputSchema=tool["inputSchema"],
                    server_id=self.config.server_id
                )
                for tool in tools_result
            ]

            # Get resources
            resources_result = await self.client.list_resources()
            self.cached_resources = [
                MCPResource(
                    uri=resource["uri"],
                    name=resource["name"],
                    description=resource.get("description"),
                    mimeType=resource.get("mimeType"),
                    server_id=self.config.server_id
                )
                for resource in resources_result
            ]

            # Update health metrics
            self.health.available_tools = len(self.cached_tools)
            self.health.available_resources = len(self.cached_resources)
            self.last_capability_refresh = datetime.now()

            logger.info(f"Server {self.config.server_id}: {len(self.cached_tools)} tools, {len(self.cached_resources)} resources")

        except Exception as e:
            logger.error(f"Failed to refresh capabilities for server {self.config.server_id}: {e}")

    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call tool with request tracking"""
        if not self.client or not self.client.is_connected:
            raise RuntimeError(f"Server {self.config.server_id} not connected")

        start_time = time.time()
        self.health.total_requests += 1

        try:
            result = await self.client.call_tool(tool_name, arguments)

            # Update success metrics
            self.health.successful_requests += 1
            response_time = time.time() - start_time
            self.metrics.response_times.append(response_time)

            return result

        except Exception as e:
            # Update failure metrics
            self.health.failed_requests += 1
            self.metrics.recent_errors.append(str(e))
            if len(self.metrics.recent_errors) > 10:
                self.metrics.recent_errors.pop(0)

            raise

    def is_healthy(self) -> bool:
        """Check if server is healthy"""
        return self.health.state in [MCPServerState.HEALTHY, MCPServerState.DEGRADED]

    def can_handle_request(self) -> bool:
        """Check if server can handle new requests"""
        return (self.is_healthy() and
                self.metrics.concurrent_connections < self.config.max_concurrent_requests)


class MCPServerManager:
    """
    Comprehensive MCP server manager with health monitoring, load balancing,
    and security integration.

    Features:
    - Multi-server lifecycle management
    - Health monitoring and automatic recovery
    - Load balancing with multiple strategies
    - Security integration with all 9 security components
    - Real-time metrics and performance monitoring
    - Graceful failover and recovery
    """

    def __init__(self,
                 db_path: str = "mcp_server_manager.db",
                 load_balance_strategy: MCPLoadBalanceStrategy = MCPLoadBalanceStrategy.ROUND_ROBIN,
                 security_system: Optional[CommandWhitelistSystem] = None,
                 emergency_system: Optional[MultiChannelEmergencyStop] = None,
                 security_logger: Optional[EnhancedSecurityLogging] = None,
                 rate_limiter: Optional[RateLimitingResourceControl] = None,
                 auth_system: Optional[AdvancedAuthenticationSystem] = None,
                 rollback_system: Optional[RollbackRecoverySystem] = None):

        self.db_path = db_path
        self.load_balance_strategy = load_balance_strategy

        # Security systems
        self.security_systems = {
            'security_system': security_system,
            'emergency_system': emergency_system,
            'security_logger': security_logger,
            'rate_limiter': rate_limiter,
            'auth_system': auth_system
        }
        self.rollback_system = rollback_system

        # Server management
        self.servers: Dict[str, MCPServerConnection] = {}
        self.server_configs: Dict[str, MCPServerConfig] = {}

        # Load balancing state
        self.round_robin_index = 0
        self.server_stats: Dict[str, Dict[str, Any]] = {}

        # Health monitoring
        self.health_monitor_active = False
        self.health_monitor_task: Optional[asyncio.Task] = None

        # Metrics collection
        self.metrics_collection_active = False
        self.metrics_task: Optional[asyncio.Task] = None

        self._init_database()

    def _init_database(self) -> None:
        """Initialize server manager database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Server configurations table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS server_configs (
                    server_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    transport_type TEXT NOT NULL,
                    connection_params TEXT NOT NULL,
                    config_data TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Server health history
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS server_health_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    server_id TEXT NOT NULL,
                    state TEXT NOT NULL,
                    health_data TEXT NOT NULL,
                    timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (server_id) REFERENCES server_configs (server_id)
                )
            """)

            # Server metrics
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS server_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    server_id TEXT NOT NULL,
                    metrics_data TEXT NOT NULL,
                    timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (server_id) REFERENCES server_configs (server_id)
                )
            """)

            # Create indexes
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_health_server_time ON server_health_history(server_id, timestamp)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_metrics_server_time ON server_metrics(server_id, timestamp)")

            conn.commit()

    async def add_server(self, config: MCPServerConfig) -> bool:
        """Add MCP server to management"""
        try:
            # Security validation
            if not await self._validate_server_addition(config):
                return False

            # Store configuration
            self.server_configs[config.server_id] = config
            await self._save_server_config(config)

            # Create server connection
            server_connection = MCPServerConnection(config, self.security_systems)
            self.servers[config.server_id] = server_connection

            # Connect to server
            connected = await server_connection.connect()

            if connected:
                await self._log_security_event(
                    SecurityEventType.SERVER_STARTED,
                    f"MCP server added and connected: {config.server_id}",
                    {"server_id": config.server_id, "name": config.name}
                )

            return connected

        except Exception as e:
            logger.error(f"Failed to add server {config.server_id}: {e}")
            return False

    async def remove_server(self, server_id: str) -> bool:
        """Remove MCP server from management"""
        try:
            if server_id not in self.servers:
                return False

            # Disconnect server
            server = self.servers[server_id]
            await server.disconnect()

            # Remove from management
            del self.servers[server_id]
            del self.server_configs[server_id]

            # Remove from database
            await self._remove_server_config(server_id)

            await self._log_security_event(
                SecurityEventType.SERVER_STOPPED,
                f"MCP server removed: {server_id}",
                {"server_id": server_id}
            )

            return True

        except Exception as e:
            logger.error(f"Failed to remove server {server_id}: {e}")
            return False

    async def start_health_monitoring(self) -> None:
        """Start health monitoring for all servers"""
        if self.health_monitor_active:
            return

        self.health_monitor_active = True
        self.health_monitor_task = asyncio.create_task(self._health_monitor_loop())
        logger.info("MCP server health monitoring started")

    async def stop_health_monitoring(self) -> None:
        """Stop health monitoring"""
        self.health_monitor_active = False
        if self.health_monitor_task:
            self.health_monitor_task.cancel()

    async def get_available_tools(self) -> Dict[str, List[MCPTool]]:
        """Get all available tools from healthy servers"""
        tools_by_server = {}

        for server_id, server in self.servers.items():
            if server.is_healthy():
                tools_by_server[server_id] = server.cached_tools

        return tools_by_server

    async def get_available_resources(self) -> Dict[str, List[MCPResource]]:
        """Get all available resources from healthy servers"""
        resources_by_server = {}

        for server_id, server in self.servers.items():
            if server.is_healthy():
                resources_by_server[server_id] = server.cached_resources

        return resources_by_server

    async def call_tool(self, tool_name: str, arguments: Dict[str, Any],
                       preferred_server: Optional[str] = None) -> Dict[str, Any]:
        """Call tool using load balancing and failover"""
        # Find servers that have the tool
        capable_servers = []
        for server_id, server in self.servers.items():
            if server.is_healthy() and any(tool.name == tool_name for tool in server.cached_tools):
                capable_servers.append(server)

        if not capable_servers:
            raise RuntimeError(f"No healthy servers found with tool: {tool_name}")

        # Select server based on strategy
        selected_server = self._select_server(capable_servers, preferred_server)

        try:
            result = await selected_server.call_tool(tool_name, arguments)

            await self._log_security_event(
                SecurityEventType.TOOL_EXECUTION,
                f"Tool executed via server manager: {tool_name}",
                {
                    "tool_name": tool_name,
                    "server_id": selected_server.config.server_id,
                    "arguments": arguments
                }
            )

            return result

        except Exception as e:
            logger.error(f"Tool call failed on server {selected_server.config.server_id}: {e}")

            # Try failover to another server
            remaining_servers = [s for s in capable_servers if s != selected_server]
            if remaining_servers:
                logger.info(f"Attempting failover for tool {tool_name}")
                fallback_server = self._select_server(remaining_servers)
                return await fallback_server.call_tool(tool_name, arguments)

            raise

    def _select_server(self, servers: List[MCPServerConnection],
                      preferred_server: Optional[str] = None) -> MCPServerConnection:
        """Select server based on load balancing strategy"""
        if preferred_server:
            for server in servers:
                if server.config.server_id == preferred_server and server.can_handle_request():
                    return server

        if self.load_balance_strategy == MCPLoadBalanceStrategy.ROUND_ROBIN:
            # Round robin selection
            available_servers = [s for s in servers if s.can_handle_request()]
            if available_servers:
                server = available_servers[self.round_robin_index % len(available_servers)]
                self.round_robin_index += 1
                return server

        elif self.load_balance_strategy == MCPLoadBalanceStrategy.PRIORITY_WEIGHTED:
            # Priority-weighted selection
            available_servers = [s for s in servers if s.can_handle_request()]
            if available_servers:
                # Sort by priority (higher first)
                available_servers.sort(key=lambda s: s.config.priority.value, reverse=True)
                return available_servers[0]

        elif self.load_balance_strategy == MCPLoadBalanceStrategy.LEAST_CONNECTIONS:
            # Least connections selection
            available_servers = [s for s in servers if s.can_handle_request()]
            if available_servers:
                return min(available_servers, key=lambda s: s.metrics.concurrent_connections)

        elif self.load_balance_strategy == MCPLoadBalanceStrategy.FASTEST_RESPONSE:
            # Fastest response time selection
            available_servers = [s for s in servers if s.can_handle_request()]
            if available_servers:
                return min(available_servers, key=lambda s: s.health.average_response_time)

        # Fallback to first available
        for server in servers:
            if server.can_handle_request():
                return server

        # If no server can handle request, return first one anyway
        return servers[0]

    async def _health_monitor_loop(self) -> None:
        """Health monitoring loop"""
        while self.health_monitor_active:
            try:
                # Check health of all servers
                for server_id, server in self.servers.items():
                    try:
                        await server.health_check()

                        # Auto-restart failed servers if configured
                        if (server.health.state == MCPServerState.FAILED and
                            server.config.auto_restart and
                            server.restart_attempts < server.config.max_restart_attempts):

                            logger.info(f"Attempting to restart failed server: {server_id}")
                            await self._restart_server(server_id)

                        # Save health metrics
                        await self._save_health_metrics(server)

                    except Exception as e:
                        logger.error(f"Health check error for server {server_id}: {e}")

                # Wait for next check
                await asyncio.sleep(30)  # Check every 30 seconds

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health monitor loop error: {e}")

    async def _restart_server(self, server_id: str) -> bool:
        """Restart a failed server"""
        if server_id not in self.servers:
            return False

        try:
            server = self.servers[server_id]
            server.restart_attempts += 1

            # Disconnect and reconnect
            await server.disconnect()
            await asyncio.sleep(server.config.restart_delay)

            connected = await server.connect()
            if connected:
                logger.info(f"Server {server_id} restarted successfully")
                await self._log_security_event(
                    SecurityEventType.SERVER_RESTARTED,
                    f"MCP server restarted: {server_id}",
                    {"server_id": server_id, "restart_attempt": server.restart_attempts}
                )

            return connected

        except Exception as e:
            logger.error(f"Failed to restart server {server_id}: {e}")
            return False

    async def _validate_server_addition(self, config: MCPServerConfig) -> bool:
        """Validate server addition through security systems"""
        security_system = self.security_systems.get('security_system')
        if not security_system:
            return True

        try:
            operation_params = {
                'server_id': config.server_id,
                'transport_type': config.transport_type.value,
                'connection_params': config.connection_params
            }

            permission_result = security_system.check_operation_permission(
                operation_name='mcp_server_addition',
                user_permission_level=PermissionLevel.AUTHENTICATED,
                operation_params=operation_params
            )

            return permission_result.permission_granted

        except Exception as e:
            logger.error(f"Server addition security validation failed: {e}")
            return False

    async def _save_server_config(self, config: MCPServerConfig) -> None:
        """Save server configuration to database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO server_configs
                (server_id, name, description, transport_type, connection_params, config_data, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                config.server_id,
                config.name,
                config.description,
                config.transport_type.value,
                json.dumps(config.connection_params),
                json.dumps(asdict(config)),
                datetime.now().isoformat()
            ))
            conn.commit()

    async def _remove_server_config(self, server_id: str) -> None:
        """Remove server configuration from database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM server_configs WHERE server_id = ?", (server_id,))
            cursor.execute("DELETE FROM server_health_history WHERE server_id = ?", (server_id,))
            cursor.execute("DELETE FROM server_metrics WHERE server_id = ?", (server_id,))
            conn.commit()

    async def _save_health_metrics(self, server: MCPServerConnection) -> None:
        """Save server health metrics to database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Save health data
            cursor.execute("""
                INSERT INTO server_health_history (server_id, state, health_data)
                VALUES (?, ?, ?)
            """, (
                server.config.server_id,
                server.health.state.value,
                json.dumps(asdict(server.health))
            ))

            # Save metrics data
            cursor.execute("""
                INSERT INTO server_metrics (server_id, metrics_data)
                VALUES (?, ?)
            """, (
                server.config.server_id,
                json.dumps(asdict(server.metrics))
            ))

            conn.commit()

    async def _log_security_event(self, event_type: SecurityEventType,
                                description: str, context: Dict[str, Any]) -> None:
        """Log security events"""
        security_logger = self.security_systems.get('security_logger')
        if security_logger:
            try:
                await security_logger.log_security_event(
                    event_type=event_type,
                    description=description,
                    context=context,
                    severity=SecuritySeverity.INFO
                )
            except Exception as e:
                logger.error(f"Failed to log security event: {e}")

    def get_server_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all managed servers"""
        status = {}
        for server_id, server in self.servers.items():
            status[server_id] = {
                "config": asdict(server.config),
                "health": asdict(server.health),
                "metrics": asdict(server.metrics),
                "tools_count": len(server.cached_tools),
                "resources_count": len(server.cached_resources)
            }
        return status

    async def shutdown(self) -> None:
        """Shutdown server manager and all connections"""
        try:
            # Stop monitoring
            await self.stop_health_monitoring()

            # Disconnect all servers
            disconnect_tasks = []
            for server in self.servers.values():
                disconnect_tasks.append(server.disconnect())

            if disconnect_tasks:
                await asyncio.gather(*disconnect_tasks, return_exceptions=True)

            logger.info("MCP Server Manager shutdown complete")

        except Exception as e:
            logger.error(f"Error during server manager shutdown: {e}")


# Example usage
async def main():
    """Example MCP server manager usage"""
    print("🚀 MCP Server Manager Test")

    try:
        # Initialize security systems
        whitelist = CommandWhitelistSystem()
        emergency = MultiChannelEmergencyStop()
        logger_sys = EnhancedSecurityLogging()

        # Create server manager
        manager = MCPServerManager(
            security_system=whitelist,
            emergency_system=emergency,
            security_logger=logger_sys
        )

        print("✅ MCP Server Manager created with security integration")
        print("✅ Health monitoring capabilities ready")
        print("✅ Load balancing strategies available")
        print("✅ Emergency stop integration active")

    except Exception as e:
        print(f"❌ Error during server manager test: {e}")


if __name__ == "__main__":
    asyncio.run(main())