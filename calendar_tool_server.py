"""
Calendar Integration Tool Server
Provides secure calendar operations with comprehensive authentication
"""

import asyncio
import json
import base64
import hashlib
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any, Union
import aiohttp
import aiosqlite
from dataclasses import dataclass

from tool_server_foundation import (
    BaseToolServer, ToolServerType, SecurityLevel, SecurityContext,
    ToolOperation, ToolOperationResult, ToolServerSecurityError,
    ToolServerAuthenticationError
)


@dataclass
class CalendarEvent:
    """Calendar event data structure"""
    id: Optional[str] = None
    title: str = ""
    description: str = ""
    start_time: datetime = None
    end_time: datetime = None
    location: str = ""
    attendees: List[str] = None
    calendar_id: str = ""
    created_by: str = ""
    last_modified: Optional[datetime] = None
    recurrence_rule: Optional[str] = None
    reminder_minutes: Optional[int] = None
    visibility: str = "private"
    status: str = "confirmed"

    def __post_init__(self):
        if self.attendees is None:
            self.attendees = []


@dataclass
class CalendarCredentials:
    """Calendar service credentials"""
    service: str
    user_id: str
    access_token: str
    refresh_token: Optional[str]
    expires_at: datetime
    scopes: List[str]
    calendar_list: List[Dict[str, Any]]


class CalendarToolServer(BaseToolServer):
    """Calendar tool server with authentication and security"""

    def __init__(self, *args, **kwargs):
        super().__init__(ToolServerType.CALENDAR, *args, **kwargs)

        # Supported calendar services
        self.supported_services = {
            "google": {
                "auth_url": "https://accounts.google.com/o/oauth2/auth",
                "token_url": "https://oauth2.googleapis.com/token",
                "api_base": "https://www.googleapis.com/calendar/v3",
                "scopes": ["https://www.googleapis.com/auth/calendar"]
            },
            "outlook": {
                "auth_url": "https://login.microsoftonline.com/common/oauth2/v2.0/authorize",
                "token_url": "https://login.microsoftonline.com/common/oauth2/v2.0/token",
                "api_base": "https://graph.microsoft.com/v1.0",
                "scopes": ["https://graph.microsoft.com/Calendars.ReadWrite"]
            }
        }

        # Authentication configuration
        self.token_cache_duration = 3600  # 1 hour
        self.max_events_per_request = 1000
        self.max_calendar_range_days = 365

        # Security settings
        self.require_encryption = True
        self.audit_all_operations = True

    async def _load_configuration(self):
        """Load calendar specific configuration"""
        await self._setup_credentials_storage()
        await self._load_service_credentials()

    async def _setup_credentials_storage(self):
        """Setup secure credentials storage"""
        async with aiosqlite.connect(self.db_path) as db:
            # Calendar credentials table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS calendar_credentials (
                    user_id TEXT,
                    service TEXT,
                    encrypted_credentials TEXT,
                    expires_at TEXT,
                    created_at TEXT,
                    last_used TEXT,
                    PRIMARY KEY (user_id, service)
                )
            """)

            # Calendar access log
            await db.execute("""
                CREATE TABLE IF NOT EXISTS calendar_access_log (
                    log_id TEXT PRIMARY KEY,
                    user_id TEXT,
                    service TEXT,
                    operation TEXT,
                    calendar_id TEXT,
                    event_id TEXT,
                    timestamp TEXT,
                    success BOOLEAN,
                    ip_address TEXT,
                    user_agent TEXT
                )
            """)

            # Event cache
            await db.execute("""
                CREATE TABLE IF NOT EXISTS event_cache (
                    cache_key TEXT PRIMARY KEY,
                    user_id TEXT,
                    service TEXT,
                    calendar_id TEXT,
                    event_data TEXT,
                    cached_at TEXT,
                    expires_at TEXT
                )
            """)

            await db.commit()

    async def _load_service_credentials(self):
        """Load service-specific credentials (API keys, client secrets)"""
        # Load from secure storage or environment
        pass

    async def _execute_specific_operation(self,
                                        operation_name: str,
                                        parameters: Dict[str, Any],
                                        security_context: SecurityContext) -> Dict[str, Any]:
        """Execute calendar specific operations"""

        operation_map = {
            "authenticate": self._authenticate,
            "list_calendars": self._list_calendars,
            "get_events": self._get_events,
            "create_event": self._create_event,
            "update_event": self._update_event,
            "delete_event": self._delete_event,
            "search_events": self._search_events,
            "get_availability": self._get_availability,
            "create_meeting": self._create_meeting,
            "send_invitation": self._send_invitation,
            "get_calendar_settings": self._get_calendar_settings,
            "set_calendar_permissions": self._set_calendar_permissions
        }

        if operation_name not in operation_map:
            raise ValueError(f"Unknown calendar operation: {operation_name}")

        # Verify authentication for all operations except authenticate
        if operation_name != "authenticate":
            await self._verify_authentication(security_context.user_id, parameters.get("service", ""))

        return await operation_map[operation_name](parameters, security_context)

    async def _determine_security_level(self, operation_name: str, parameters: Dict[str, Any]) -> SecurityLevel:
        """Determine security level for calendar operations"""

        # Critical operations
        if operation_name in ["delete_event", "set_calendar_permissions"]:
            return SecurityLevel.CRITICAL

        # High-risk operations
        if operation_name in ["create_event", "update_event", "send_invitation", "create_meeting"]:
            return SecurityLevel.HIGH

        # Medium-risk operations
        if operation_name in ["get_events", "search_events", "get_availability"]:
            return SecurityLevel.MEDIUM

        # Low-risk operations
        if operation_name in ["authenticate", "list_calendars", "get_calendar_settings"]:
            return SecurityLevel.LOW

        return SecurityLevel.MEDIUM

    async def _requires_rollback(self, operation_name: str) -> bool:
        """Check if operation requires rollback capability"""
        rollback_operations = {
            "create_event", "update_event", "delete_event", "set_calendar_permissions"
        }
        return operation_name in rollback_operations

    async def _create_rollback_data(self, operation: ToolOperation, result_data: Dict[str, Any]) -> str:
        """Create rollback data for calendar operations"""
        rollback_id = f"cal_rb_{operation.operation_id}_{int(datetime.now().timestamp())}"

        rollback_info = {
            "rollback_id": rollback_id,
            "operation_id": operation.operation_id,
            "operation_name": operation.operation_name,
            "parameters": operation.parameters,
            "result_data": result_data,
            "timestamp": datetime.now().isoformat(),
            "expires_at": (datetime.now() + timedelta(days=7)).isoformat()  # 7 days retention
        }

        if operation.operation_name == "create_event":
            rollback_info["rollback_type"] = "delete_created_event"
            rollback_info["event_id"] = result_data.get("event_id")
            rollback_info["calendar_id"] = operation.parameters.get("calendar_id")

        elif operation.operation_name == "update_event":
            rollback_info["rollback_type"] = "restore_event_state"
            rollback_info["event_id"] = operation.parameters.get("event_id")
            rollback_info["calendar_id"] = operation.parameters.get("calendar_id")
            # Store original event data (would need to fetch before update)

        elif operation.operation_name == "delete_event":
            rollback_info["rollback_type"] = "restore_deleted_event"
            rollback_info["original_event_data"] = operation.parameters.get("original_event_data")

        # Store rollback data
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO rollback_data
                (rollback_id, operation_id, rollback_type, rollback_data, created_at, expires_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                rollback_id,
                operation.operation_id,
                rollback_info.get("rollback_type", "unknown"),
                json.dumps(rollback_info),
                rollback_info["timestamp"],
                rollback_info["expires_at"]
            ))
            await db.commit()

        return rollback_id

    async def _execute_rollback(self, rollback_type: str, rollback_data: Dict[str, Any]) -> bool:
        """Execute rollback operation for calendar changes"""
        try:
            if rollback_type == "delete_created_event":
                # Delete the event that was created
                # Implementation would call the actual calendar API
                return True

            elif rollback_type == "restore_event_state":
                # Restore the original event state
                # Implementation would call the actual calendar API
                return True

            elif rollback_type == "restore_deleted_event":
                # Recreate the deleted event
                # Implementation would call the actual calendar API
                return True

            return False

        except Exception as e:
            self.logger.error(f"Calendar rollback failed: {e}")
            return False

    async def _verify_authentication(self, user_id: str, service: str):
        """Verify user authentication for calendar service"""
        if not user_id or not service:
            raise ToolServerAuthenticationError("User ID and service required")

        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("""
                SELECT encrypted_credentials, expires_at FROM calendar_credentials
                WHERE user_id = ? AND service = ?
            """, (user_id, service)) as cursor:
                row = await cursor.fetchone()
                if not row:
                    raise ToolServerAuthenticationError(f"No credentials found for {service}")

                encrypted_creds, expires_at = row
                if datetime.fromisoformat(expires_at) < datetime.now():
                    raise ToolServerAuthenticationError("Credentials expired")

    def _encrypt_credentials(self, credentials: Dict[str, Any]) -> str:
        """Encrypt credentials for secure storage"""
        # In production, use proper encryption (AES, Fernet, etc.)
        # This is a simplified example
        data = json.dumps(credentials)
        encoded = base64.b64encode(data.encode()).decode()
        return encoded

    def _decrypt_credentials(self, encrypted_data: str) -> Dict[str, Any]:
        """Decrypt credentials from storage"""
        # In production, use proper decryption
        # This is a simplified example
        try:
            decoded = base64.b64decode(encrypted_data.encode()).decode()
            return json.loads(decoded)
        except Exception:
            raise ToolServerAuthenticationError("Failed to decrypt credentials")

    async def _log_calendar_access(self, user_id: str, service: str, operation: str,
                                 calendar_id: str = "", event_id: str = "",
                                 success: bool = True, ip_address: str = "",
                                 user_agent: str = ""):
        """Log calendar access for audit trail"""
        log_id = f"cal_log_{int(datetime.now().timestamp())}_{user_id}"

        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO calendar_access_log
                (log_id, user_id, service, operation, calendar_id, event_id,
                 timestamp, success, ip_address, user_agent)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                log_id, user_id, service, operation, calendar_id, event_id,
                datetime.now().isoformat(), success, ip_address, user_agent
            ))
            await db.commit()

    async def _authenticate(self, parameters: Dict[str, Any], security_context: SecurityContext) -> Dict[str, Any]:
        """Authenticate with calendar service"""
        service = parameters.get("service", "")
        auth_code = parameters.get("auth_code", "")
        redirect_uri = parameters.get("redirect_uri", "")

        if service not in self.supported_services:
            raise ValueError(f"Unsupported calendar service: {service}")

        if not auth_code:
            # Return authorization URL for user to visit
            service_config = self.supported_services[service]
            auth_params = {
                "client_id": "your_client_id",  # Load from config
                "response_type": "code",
                "scope": " ".join(service_config["scopes"]),
                "redirect_uri": redirect_uri,
                "access_type": "offline"  # For refresh tokens
            }

            auth_url = f"{service_config['auth_url']}?" + "&".join(
                f"{k}={v}" for k, v in auth_params.items()
            )

            return {
                "auth_url": auth_url,
                "service": service,
                "step": "authorization_required"
            }

        # Exchange auth code for tokens
        try:
            tokens = await self._exchange_auth_code(service, auth_code, redirect_uri)

            # Store encrypted credentials
            credentials = {
                "access_token": tokens["access_token"],
                "refresh_token": tokens.get("refresh_token"),
                "expires_at": (datetime.now() + timedelta(seconds=tokens["expires_in"])).isoformat(),
                "scopes": self.supported_services[service]["scopes"]
            }

            encrypted_creds = self._encrypt_credentials(credentials)

            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    INSERT OR REPLACE INTO calendar_credentials
                    (user_id, service, encrypted_credentials, expires_at, created_at, last_used)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    security_context.user_id,
                    service,
                    encrypted_creds,
                    credentials["expires_at"],
                    datetime.now().isoformat(),
                    datetime.now().isoformat()
                ))
                await db.commit()

            await self._log_calendar_access(
                security_context.user_id, service, "authenticate", success=True
            )

            return {
                "service": service,
                "authenticated": True,
                "expires_at": credentials["expires_at"],
                "step": "authentication_complete"
            }

        except Exception as e:
            await self._log_calendar_access(
                security_context.user_id, service, "authenticate", success=False
            )
            raise ToolServerAuthenticationError(f"Authentication failed: {e}")

    async def _exchange_auth_code(self, service: str, auth_code: str, redirect_uri: str) -> Dict[str, Any]:
        """Exchange authorization code for access tokens"""
        service_config = self.supported_services[service]

        token_data = {
            "grant_type": "authorization_code",
            "code": auth_code,
            "redirect_uri": redirect_uri,
            "client_id": "your_client_id",  # Load from config
            "client_secret": "your_client_secret"  # Load from config
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(service_config["token_url"], data=token_data) as response:
                if response.status != 200:
                    raise ToolServerAuthenticationError(f"Token exchange failed: {response.status}")

                return await response.json()

    async def _list_calendars(self, parameters: Dict[str, Any], security_context: SecurityContext) -> Dict[str, Any]:
        """List available calendars"""
        service = parameters.get("service", "")

        # Mock implementation - in production, call actual calendar API
        calendars = [
            {
                "id": "primary",
                "name": "Primary Calendar",
                "description": "Main calendar",
                "timezone": "UTC",
                "access_role": "owner"
            },
            {
                "id": "work",
                "name": "Work Calendar",
                "description": "Work-related events",
                "timezone": "UTC",
                "access_role": "writer"
            }
        ]

        await self._log_calendar_access(
            security_context.user_id, service, "list_calendars", success=True
        )

        return {
            "service": service,
            "calendars": calendars,
            "total_count": len(calendars),
            "timestamp": datetime.now().isoformat()
        }

    async def _get_events(self, parameters: Dict[str, Any], security_context: SecurityContext) -> Dict[str, Any]:
        """Get events from calendar"""
        service = parameters.get("service", "")
        calendar_id = parameters.get("calendar_id", "primary")
        start_date = parameters.get("start_date")
        end_date = parameters.get("end_date")
        max_results = min(parameters.get("max_results", 100), self.max_events_per_request)

        # Validate date range
        if start_date and end_date:
            start = datetime.fromisoformat(start_date)
            end = datetime.fromisoformat(end_date)
            if (end - start).days > self.max_calendar_range_days:
                raise ToolServerSecurityError("Date range too large")

        # Mock implementation - in production, call actual calendar API
        events = [
            {
                "id": "event1",
                "title": "Team Meeting",
                "description": "Weekly team sync",
                "start_time": "2024-01-15T10:00:00Z",
                "end_time": "2024-01-15T11:00:00Z",
                "location": "Conference Room A",
                "attendees": ["user1@example.com", "user2@example.com"],
                "status": "confirmed"
            }
        ]

        await self._log_calendar_access(
            security_context.user_id, service, "get_events", calendar_id, success=True
        )

        return {
            "service": service,
            "calendar_id": calendar_id,
            "events": events,
            "total_count": len(events),
            "start_date": start_date,
            "end_date": end_date,
            "timestamp": datetime.now().isoformat()
        }

    async def _create_event(self, parameters: Dict[str, Any], security_context: SecurityContext) -> Dict[str, Any]:
        """Create new calendar event"""
        service = parameters.get("service", "")
        calendar_id = parameters.get("calendar_id", "primary")
        event_data = parameters.get("event", {})

        # Validate event data
        required_fields = ["title", "start_time", "end_time"]
        for field in required_fields:
            if field not in event_data:
                raise ValueError(f"Missing required field: {field}")

        # Create event (mock implementation)
        event_id = f"event_{int(datetime.now().timestamp())}"

        await self._log_calendar_access(
            security_context.user_id, service, "create_event", calendar_id, event_id, success=True
        )

        return {
            "service": service,
            "calendar_id": calendar_id,
            "event_id": event_id,
            "event": {**event_data, "id": event_id},
            "created": True,
            "timestamp": datetime.now().isoformat()
        }

    async def _update_event(self, parameters: Dict[str, Any], security_context: SecurityContext) -> Dict[str, Any]:
        """Update existing calendar event"""
        service = parameters.get("service", "")
        calendar_id = parameters.get("calendar_id", "primary")
        event_id = parameters.get("event_id", "")
        event_updates = parameters.get("updates", {})

        if not event_id:
            raise ValueError("Event ID required for update")

        # Update event (mock implementation)
        await self._log_calendar_access(
            security_context.user_id, service, "update_event", calendar_id, event_id, success=True
        )

        return {
            "service": service,
            "calendar_id": calendar_id,
            "event_id": event_id,
            "updates": event_updates,
            "updated": True,
            "timestamp": datetime.now().isoformat()
        }

    async def _delete_event(self, parameters: Dict[str, Any], security_context: SecurityContext) -> Dict[str, Any]:
        """Delete calendar event"""
        service = parameters.get("service", "")
        calendar_id = parameters.get("calendar_id", "primary")
        event_id = parameters.get("event_id", "")

        if not event_id:
            raise ValueError("Event ID required for deletion")

        # Delete event (mock implementation)
        await self._log_calendar_access(
            security_context.user_id, service, "delete_event", calendar_id, event_id, success=True
        )

        return {
            "service": service,
            "calendar_id": calendar_id,
            "event_id": event_id,
            "deleted": True,
            "timestamp": datetime.now().isoformat()
        }

    async def _search_events(self, parameters: Dict[str, Any], security_context: SecurityContext) -> Dict[str, Any]:
        """Search events in calendar"""
        service = parameters.get("service", "")
        calendar_id = parameters.get("calendar_id", "primary")
        query = parameters.get("query", "")
        max_results = min(parameters.get("max_results", 50), 200)

        if not query:
            raise ValueError("Search query required")

        # Search events (mock implementation)
        events = []

        await self._log_calendar_access(
            security_context.user_id, service, "search_events", calendar_id, success=True
        )

        return {
            "service": service,
            "calendar_id": calendar_id,
            "query": query,
            "events": events,
            "total_count": len(events),
            "timestamp": datetime.now().isoformat()
        }

    async def _get_availability(self, parameters: Dict[str, Any], security_context: SecurityContext) -> Dict[str, Any]:
        """Get availability information"""
        service = parameters.get("service", "")
        start_date = parameters.get("start_date")
        end_date = parameters.get("end_date")
        attendees = parameters.get("attendees", [])

        # Mock availability data
        availability = {
            "busy_times": [],
            "free_times": [
                {
                    "start": start_date,
                    "end": end_date
                }
            ]
        }

        return {
            "service": service,
            "start_date": start_date,
            "end_date": end_date,
            "attendees": attendees,
            "availability": availability,
            "timestamp": datetime.now().isoformat()
        }

    async def _create_meeting(self, parameters: Dict[str, Any], security_context: SecurityContext) -> Dict[str, Any]:
        """Create meeting with invitations"""
        # Combine event creation with invitation sending
        event_result = await self._create_event(parameters, security_context)

        # Send invitations (mock implementation)
        attendees = parameters.get("event", {}).get("attendees", [])
        invitations_sent = len(attendees)

        return {
            **event_result,
            "meeting_created": True,
            "invitations_sent": invitations_sent,
            "attendees": attendees
        }

    async def _send_invitation(self, parameters: Dict[str, Any], security_context: SecurityContext) -> Dict[str, Any]:
        """Send calendar invitation"""
        service = parameters.get("service", "")
        event_id = parameters.get("event_id", "")
        attendees = parameters.get("attendees", [])

        # Send invitations (mock implementation)
        return {
            "service": service,
            "event_id": event_id,
            "attendees": attendees,
            "invitations_sent": len(attendees),
            "timestamp": datetime.now().isoformat()
        }

    async def _get_calendar_settings(self, parameters: Dict[str, Any], security_context: SecurityContext) -> Dict[str, Any]:
        """Get calendar settings"""
        service = parameters.get("service", "")
        calendar_id = parameters.get("calendar_id", "primary")

        # Mock settings
        settings = {
            "timezone": "UTC",
            "default_event_length": 60,
            "working_hours": {
                "start": "09:00",
                "end": "17:00"
            },
            "notifications": {
                "email": True,
                "popup": True
            }
        }

        return {
            "service": service,
            "calendar_id": calendar_id,
            "settings": settings,
            "timestamp": datetime.now().isoformat()
        }

    async def _set_calendar_permissions(self, parameters: Dict[str, Any], security_context: SecurityContext) -> Dict[str, Any]:
        """Set calendar permissions"""
        service = parameters.get("service", "")
        calendar_id = parameters.get("calendar_id", "")
        permissions = parameters.get("permissions", {})

        # Set permissions (mock implementation)
        return {
            "service": service,
            "calendar_id": calendar_id,
            "permissions": permissions,
            "updated": True,
            "timestamp": datetime.now().isoformat()
        }