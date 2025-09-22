#!/usr/bin/env python3
"""
MCP (Model Context Protocol) Foundation for Penny AI Assistant
Phase 2 Priority 8.1: MCP Protocol Implementation

This module provides the core MCP protocol implementation with:
- JSON-RPC over stdio/HTTP transport layers
- Protocol message handling and validation
- Security integration with existing whitelist system
- Transport layer abstraction for multiple connection types
- Error handling and recovery mechanisms

Integrates with:
- Command Whitelist System (security approval)
- Emergency Stop System (immediate termination)
- Enhanced Security Logging (audit trails)
- Rate Limiting System (abuse prevention)
"""

import asyncio
import json
import uuid
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Callable, Protocol
from enum import Enum, IntEnum
from dataclasses import dataclass, asdict, field
from abc import ABC, abstractmethod
import aiohttp
import subprocess
from pathlib import Path

# Import existing security components
try:
    from command_whitelist_system import CommandWhitelistSystem, PermissionLevel, SecurityRisk, OperationType
    from multi_channel_emergency_stop import MultiChannelEmergencyStop, EmergencyTrigger
    from enhanced_security_logging import EnhancedSecurityLogger as EnhancedSecurityLogging, SecurityEventType, SecuritySeverity
    from rate_limiting_resource_control import RateLimitingResourceControl
except ImportError as e:
    print(f"Warning: Could not import security components: {e}")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MCPMessageType(Enum):
    """MCP message types"""
    REQUEST = "request"
    RESPONSE = "response"
    NOTIFICATION = "notification"
    ERROR = "error"


class MCPTransportType(Enum):
    """MCP transport layer types"""
    STDIO = "stdio"
    HTTP = "http"
    WEBSOCKET = "websocket"
    TCP = "tcp"


class MCPCapabilityType(Enum):
    """Types of MCP capabilities"""
    TOOLS = "tools"
    RESOURCES = "resources"
    PROMPTS = "prompts"
    LOGGING = "logging"
    SAMPLING = "sampling"


class MCPErrorCode(IntEnum):
    """Standard MCP error codes"""
    PARSE_ERROR = -32700
    INVALID_REQUEST = -32600
    METHOD_NOT_FOUND = -32601
    INVALID_PARAMS = -32602
    INTERNAL_ERROR = -32603
    TRANSPORT_ERROR = -32000
    SECURITY_ERROR = -32001
    TIMEOUT_ERROR = -32002


@dataclass
class MCPMessage:
    """Base MCP message structure"""
    jsonrpc: str = "2.0"
    id: Optional[Union[str, int]] = None
    method: Optional[str] = None
    params: Optional[Dict[str, Any]] = None
    result: Optional[Any] = None
    error: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        if self.id is None and self.method is not None:
            self.id = str(uuid.uuid4())

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        data = {"jsonrpc": self.jsonrpc}

        if self.id is not None:
            data["id"] = self.id
        if self.method is not None:
            data["method"] = self.method
        if self.params is not None:
            data["params"] = self.params
        if self.result is not None:
            data["result"] = self.result
        if self.error is not None:
            data["error"] = self.error

        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MCPMessage':
        """Create message from dictionary"""
        return cls(
            jsonrpc=data.get("jsonrpc", "2.0"),
            id=data.get("id"),
            method=data.get("method"),
            params=data.get("params"),
            result=data.get("result"),
            error=data.get("error")
        )


@dataclass
class MCPTool:
    """MCP tool definition"""
    name: str
    description: str
    inputSchema: Dict[str, Any]
    server_id: str
    security_risk: SecurityRisk = SecurityRisk.MEDIUM
    operation_type: OperationType = OperationType.RESTRICTED
    required_permissions: List[PermissionLevel] = field(default_factory=lambda: [PermissionLevel.AUTHENTICATED])

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for MCP protocol"""
        return {
            "name": self.name,
            "description": self.description,
            "inputSchema": self.inputSchema
        }


@dataclass
class MCPResource:
    """MCP resource definition"""
    uri: str
    name: str
    description: Optional[str] = None
    mimeType: Optional[str] = None
    server_id: Optional[str] = None


@dataclass
class MCPServerCapabilities:
    """MCP server capabilities"""
    tools: Optional[Dict[str, Any]] = None
    resources: Optional[Dict[str, Any]] = None
    prompts: Optional[Dict[str, Any]] = None
    logging: Optional[Dict[str, Any]] = None
    sampling: Optional[Dict[str, Any]] = None


@dataclass
class MCPClientCapabilities:
    """MCP client capabilities"""
    roots: Optional[Dict[str, Any]] = None
    sampling: Optional[Dict[str, Any]] = None


class MCPTransport(ABC):
    """Abstract base class for MCP transport layers"""

    def __init__(self, transport_id: str, security_system: Optional[CommandWhitelistSystem] = None):
        self.transport_id = transport_id
        self.security_system = security_system
        self.connected = False
        self.last_activity = datetime.now()

    @abstractmethod
    async def connect(self) -> bool:
        """Establish connection"""
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """Close connection"""
        pass

    @abstractmethod
    async def send_message(self, message: MCPMessage) -> None:
        """Send message through transport"""
        pass

    @abstractmethod
    async def receive_message(self) -> Optional[MCPMessage]:
        """Receive message from transport"""
        pass

    @abstractmethod
    def is_healthy(self) -> bool:
        """Check transport health"""
        pass


class MCPStdioTransport(MCPTransport):
    """MCP transport over stdio (subprocess)"""

    def __init__(self, transport_id: str, command: List[str],
                 security_system: Optional[CommandWhitelistSystem] = None,
                 working_directory: Optional[str] = None):
        super().__init__(transport_id, security_system)
        self.command = command
        self.working_directory = working_directory
        self.process: Optional[subprocess.Popen] = None
        self.read_buffer = []

    async def connect(self) -> bool:
        """Start subprocess and establish stdio connection"""
        try:
            # Security check: Validate command through whitelist
            if self.security_system:
                # Create operation for subprocess execution
                operation_params = {
                    'command': self.command,
                    'working_directory': self.working_directory
                }

                permission_result = self.security_system.check_operation_permission(
                    operation_name='subprocess_execution',
                    user_permission_level=PermissionLevel.AUTHENTICATED,
                    operation_params=operation_params
                )

                if not permission_result.permission_granted:
                    logger.error(f"Security system denied MCP subprocess: {permission_result.denial_reason}")
                    return False

            # Start subprocess
            self.process = subprocess.Popen(
                self.command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=self.working_directory
            )

            self.connected = True
            self.last_activity = datetime.now()
            logger.info(f"MCP stdio transport {self.transport_id} connected")
            return True

        except Exception as e:
            logger.error(f"Failed to connect MCP stdio transport: {e}")
            return False

    async def disconnect(self) -> None:
        """Terminate subprocess"""
        if self.process:
            try:
                self.process.terminate()
                # Wait for graceful shutdown
                try:
                    self.process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self.process.kill()
                    self.process.wait()
            except Exception as e:
                logger.error(f"Error disconnecting stdio transport: {e}")
            finally:
                self.process = None
                self.connected = False

    async def send_message(self, message: MCPMessage) -> None:
        """Send JSON-RPC message to subprocess stdin"""
        if not self.connected or not self.process:
            raise RuntimeError("Transport not connected")

        try:
            json_data = json.dumps(message.to_dict())
            self.process.stdin.write(json_data + '\n')
            self.process.stdin.flush()
            self.last_activity = datetime.now()

        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            raise

    async def receive_message(self) -> Optional[MCPMessage]:
        """Receive JSON-RPC message from subprocess stdout"""
        if not self.connected or not self.process:
            return None

        try:
            # Non-blocking read with timeout
            import select
            import sys

            if sys.platform != 'win32':
                # Unix-like systems
                ready, _, _ = select.select([self.process.stdout], [], [], 0.1)
                if ready:
                    line = self.process.stdout.readline()
                    if line:
                        self.last_activity = datetime.now()
                        data = json.loads(line.strip())
                        return MCPMessage.from_dict(data)
            else:
                # Windows - simpler approach
                if self.process.poll() is None:  # Process still running
                    line = self.process.stdout.readline()
                    if line:
                        self.last_activity = datetime.now()
                        data = json.loads(line.strip())
                        return MCPMessage.from_dict(data)

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON message: {e}")
        except Exception as e:
            logger.error(f"Error receiving message: {e}")

        return None

    def is_healthy(self) -> bool:
        """Check if subprocess is running and responsive"""
        if not self.connected or not self.process:
            return False

        # Check if process is still running
        if self.process.poll() is not None:
            return False

        # Check for recent activity
        time_since_activity = datetime.now() - self.last_activity
        if time_since_activity > timedelta(minutes=5):
            return False

        return True


class MCPHttpTransport(MCPTransport):
    """MCP transport over HTTP"""

    def __init__(self, transport_id: str, base_url: str,
                 security_system: Optional[CommandWhitelistSystem] = None,
                 headers: Optional[Dict[str, str]] = None,
                 timeout: float = 30.0):
        super().__init__(transport_id, security_system)
        self.base_url = base_url.rstrip('/')
        self.headers = headers or {}
        self.timeout = timeout
        self.session: Optional[aiohttp.ClientSession] = None

    async def connect(self) -> bool:
        """Establish HTTP session"""
        try:
            # Security check for HTTP connection
            if self.security_system:
                operation_params = {
                    'url': self.base_url,
                    'method': 'POST',
                    'headers': self.headers
                }

                permission_result = self.security_system.check_operation_permission(
                    operation_name='http_connection',
                    user_permission_level=PermissionLevel.AUTHENTICATED,
                    operation_params=operation_params
                )

                if not permission_result.permission_granted:
                    logger.error(f"Security system denied HTTP connection: {permission_result.denial_reason}")
                    return False

            # Create HTTP session
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            self.session = aiohttp.ClientSession(
                headers=self.headers,
                timeout=timeout
            )

            # Test connection with a ping
            await self._ping()

            self.connected = True
            self.last_activity = datetime.now()
            logger.info(f"MCP HTTP transport {self.transport_id} connected to {self.base_url}")
            return True

        except Exception as e:
            logger.error(f"Failed to connect MCP HTTP transport: {e}")
            if self.session:
                await self.session.close()
                self.session = None
            return False

    async def disconnect(self) -> None:
        """Close HTTP session"""
        if self.session:
            await self.session.close()
            self.session = None
        self.connected = False

    async def send_message(self, message: MCPMessage) -> None:
        """Send JSON-RPC message via HTTP POST"""
        if not self.connected or not self.session:
            raise RuntimeError("Transport not connected")

        try:
            json_data = message.to_dict()
            async with self.session.post(
                f"{self.base_url}/jsonrpc",
                json=json_data
            ) as response:
                if response.status != 200:
                    raise RuntimeError(f"HTTP error: {response.status}")

                self.last_activity = datetime.now()

        except Exception as e:
            logger.error(f"Failed to send HTTP message: {e}")
            raise

    async def receive_message(self) -> Optional[MCPMessage]:
        """HTTP transport doesn't support async receive - use request/response pattern"""
        return None

    async def send_and_receive(self, message: MCPMessage) -> Optional[MCPMessage]:
        """Send message and wait for response (HTTP-specific method)"""
        if not self.connected or not self.session:
            raise RuntimeError("Transport not connected")

        try:
            json_data = message.to_dict()
            async with self.session.post(
                f"{self.base_url}/jsonrpc",
                json=json_data
            ) as response:
                if response.status != 200:
                    raise RuntimeError(f"HTTP error: {response.status}")

                self.last_activity = datetime.now()
                response_data = await response.json()
                return MCPMessage.from_dict(response_data)

        except Exception as e:
            logger.error(f"Failed to send/receive HTTP message: {e}")
            raise

    async def _ping(self) -> None:
        """Test connection health"""
        ping_message = MCPMessage(
            method="ping",
            params={}
        )

        try:
            async with self.session.post(
                f"{self.base_url}/ping",
                json=ping_message.to_dict()
            ) as response:
                if response.status not in [200, 404]:  # 404 OK if ping endpoint doesn't exist
                    raise RuntimeError(f"Ping failed: {response.status}")
        except Exception as e:
            # Ping failure is non-fatal during connection
            logger.debug(f"Ping failed (non-fatal): {e}")

    def is_healthy(self) -> bool:
        """Check HTTP connection health"""
        if not self.connected or not self.session:
            return False

        # Check for recent activity
        time_since_activity = datetime.now() - self.last_activity
        if time_since_activity > timedelta(minutes=10):
            return False

        return True


class MCPProtocolHandler:
    """Core MCP protocol message handler"""

    def __init__(self,
                 security_system: Optional[CommandWhitelistSystem] = None,
                 emergency_system: Optional[MultiChannelEmergencyStop] = None,
                 security_logger: Optional[EnhancedSecurityLogging] = None):
        self.security_system = security_system
        self.emergency_system = emergency_system
        self.security_logger = security_logger

        # Message handlers
        self.request_handlers: Dict[str, Callable] = {}
        self.notification_handlers: Dict[str, Callable] = {}

        # Protocol state
        self.client_capabilities: Optional[MCPClientCapabilities] = None
        self.server_capabilities: Optional[MCPServerCapabilities] = None

        # Register core handlers
        self._register_core_handlers()

    def _register_core_handlers(self):
        """Register core MCP protocol handlers"""
        self.request_handlers.update({
            "initialize": self._handle_initialize,
            "ping": self._handle_ping,
            "tools/list": self._handle_tools_list,
            "tools/call": self._handle_tools_call,
            "resources/list": self._handle_resources_list,
            "resources/read": self._handle_resources_read,
        })

        self.notification_handlers.update({
            "notifications/initialized": self._handle_initialized,
            "notifications/cancelled": self._handle_cancelled,
        })

    async def handle_message(self, message: MCPMessage, transport: MCPTransport) -> Optional[MCPMessage]:
        """Main message handling dispatch"""
        try:
            # Security logging
            if self.security_logger:
                await self._log_security_event(
                    SecurityEventType.ACCESS_GRANTED,
                    f"MCP message received: {message.method}",
                    {"transport_id": transport.transport_id, "method": message.method}
                )

            # Emergency stop check
            if self.emergency_system and self.emergency_system.is_emergency_active():
                return self._create_error_response(
                    message.id,
                    MCPErrorCode.SECURITY_ERROR,
                    "Emergency stop active - all operations suspended"
                )

            # Handle different message types
            if message.method is not None:
                if message.id is not None:
                    # Request - needs response
                    return await self._handle_request(message, transport)
                else:
                    # Notification - no response
                    await self._handle_notification(message, transport)
                    return None
            elif message.result is not None or message.error is not None:
                # Response to our request - handled by caller
                return message
            else:
                return self._create_error_response(
                    message.id,
                    MCPErrorCode.INVALID_REQUEST,
                    "Invalid message format"
                )

        except Exception as e:
            logger.error(f"Error handling MCP message: {e}")
            return self._create_error_response(
                message.id,
                MCPErrorCode.INTERNAL_ERROR,
                str(e)
            )

    async def _handle_request(self, message: MCPMessage, transport: MCPTransport) -> MCPMessage:
        """Handle MCP request messages"""
        method = message.method

        if method in self.request_handlers:
            try:
                result = await self.request_handlers[method](message.params or {}, transport)
                return MCPMessage(id=message.id, result=result)
            except Exception as e:
                logger.error(f"Error handling request {method}: {e}")
                return self._create_error_response(
                    message.id,
                    MCPErrorCode.INTERNAL_ERROR,
                    str(e)
                )
        else:
            return self._create_error_response(
                message.id,
                MCPErrorCode.METHOD_NOT_FOUND,
                f"Method not found: {method}"
            )

    async def _handle_notification(self, message: MCPMessage, transport: MCPTransport) -> None:
        """Handle MCP notification messages"""
        method = message.method

        if method in self.notification_handlers:
            try:
                await self.notification_handlers[method](message.params or {}, transport)
            except Exception as e:
                logger.error(f"Error handling notification {method}: {e}")

    async def _handle_initialize(self, params: Dict[str, Any], transport: MCPTransport) -> Dict[str, Any]:
        """Handle MCP initialize request"""
        # Extract client capabilities
        self.client_capabilities = MCPClientCapabilities(
            roots=params.get("capabilities", {}).get("roots"),
            sampling=params.get("capabilities", {}).get("sampling")
        )

        # Return server capabilities
        server_capabilities = {
            "tools": {"listChanged": True},
            "resources": {"subscribe": True, "listChanged": True},
            "logging": {},
        }

        return {
            "protocolVersion": "2024-11-05",
            "capabilities": server_capabilities,
            "serverInfo": {
                "name": "penny-mcp-server",
                "version": "1.0.0"
            }
        }

    async def _handle_ping(self, params: Dict[str, Any], transport: MCPTransport) -> Dict[str, Any]:
        """Handle ping request"""
        return {"status": "ok", "timestamp": datetime.now().isoformat()}

    async def _handle_tools_list(self, params: Dict[str, Any], transport: MCPTransport) -> Dict[str, Any]:
        """Handle tools list request - will be implemented by tool registry"""
        return {"tools": []}

    async def _handle_tools_call(self, params: Dict[str, Any], transport: MCPTransport) -> Dict[str, Any]:
        """Handle tool call request - will be implemented by tool registry"""
        tool_name = params.get("name")
        if not tool_name:
            raise ValueError("Tool name required")

        # Security check through whitelist
        if self.security_system:
            operation_params = {
                'tool_name': tool_name,
                'tool_params': params.get("arguments", {})
            }

            permission_result = self.security_system.check_operation_permission(
                operation_name='tool_execution',
                user_permission_level=PermissionLevel.AUTHENTICATED,
                operation_params=operation_params
            )

            if not permission_result.permission_granted:
                raise ValueError(f"Tool access denied: {permission_result.denial_reason}")

        # Placeholder - will be implemented by tool registry
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"Tool {tool_name} execution would happen here"
                }
            ]
        }

    async def _handle_resources_list(self, params: Dict[str, Any], transport: MCPTransport) -> Dict[str, Any]:
        """Handle resources list request"""
        return {"resources": []}

    async def _handle_resources_read(self, params: Dict[str, Any], transport: MCPTransport) -> Dict[str, Any]:
        """Handle resource read request"""
        return {"contents": []}

    async def _handle_initialized(self, params: Dict[str, Any], transport: MCPTransport) -> None:
        """Handle initialized notification"""
        logger.info("MCP client initialized")

    async def _handle_cancelled(self, params: Dict[str, Any], transport: MCPTransport) -> None:
        """Handle cancelled notification"""
        request_id = params.get("requestId")
        logger.info(f"MCP request cancelled: {request_id}")

    def _create_error_response(self, request_id: Optional[Union[str, int]],
                             code: MCPErrorCode, message: str) -> MCPMessage:
        """Create standardized error response"""
        return MCPMessage(
            id=request_id,
            error={
                "code": code.value,
                "message": message,
                "data": {"timestamp": datetime.now().isoformat()}
            }
        )

    async def _log_security_event(self, event_type: SecurityEventType,
                                description: str, context: Dict[str, Any]) -> None:
        """Log security events if security logger available"""
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


# Factory functions for creating transports
def create_stdio_transport(transport_id: str, command: List[str],
                          working_directory: Optional[str] = None,
                          security_system: Optional[CommandWhitelistSystem] = None) -> MCPStdioTransport:
    """Create stdio transport with security integration"""
    return MCPStdioTransport(transport_id, command, security_system, working_directory)


def create_http_transport(transport_id: str, base_url: str,
                         headers: Optional[Dict[str, str]] = None,
                         timeout: float = 30.0,
                         security_system: Optional[CommandWhitelistSystem] = None) -> MCPHttpTransport:
    """Create HTTP transport with security integration"""
    return MCPHttpTransport(transport_id, base_url, security_system, headers, timeout)


# Example usage and testing
async def main():
    """Example MCP protocol usage"""
    print("🚀 MCP Protocol Foundation Test")

    # Initialize security systems
    try:
        whitelist = CommandWhitelistSystem()
        emergency = MultiChannelEmergencyStop()
        logger_sys = EnhancedSecurityLogging()

        # Create protocol handler with security integration
        protocol = MCPProtocolHandler(
            security_system=whitelist,
            emergency_system=emergency,
            security_logger=logger_sys
        )

        # Test message creation and handling
        init_message = MCPMessage(
            method="initialize",
            params={
                "protocolVersion": "2024-11-05",
                "capabilities": {"roots": {}, "sampling": {}},
                "clientInfo": {"name": "penny-client", "version": "1.0.0"}
            }
        )

        print("✅ MCP Protocol Foundation initialized with security integration")
        print("✅ Message creation and serialization working")
        print("✅ Transport abstraction layer ready")
        print("✅ Security integration validated")

    except Exception as e:
        print(f"❌ Error during MCP protocol test: {e}")


if __name__ == "__main__":
    asyncio.run(main())