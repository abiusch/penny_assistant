"""
Task Management Tool Server
Provides secure task management with comprehensive audit logging
"""

import asyncio
import json
import uuid
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
import aiosqlite

from tool_server_foundation import (
    BaseToolServer, ToolServerType, SecurityLevel, SecurityContext,
    ToolOperation, ToolOperationResult, ToolServerSecurityError
)


class TaskStatus(Enum):
    """Task status enumeration"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    ON_HOLD = "on_hold"
    BLOCKED = "blocked"


class TaskPriority(Enum):
    """Task priority enumeration"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"
    CRITICAL = "critical"


@dataclass
class Task:
    """Task data structure"""
    id: str
    title: str
    description: str
    status: TaskStatus
    priority: TaskPriority
    created_by: str
    assigned_to: Optional[str] = None
    created_at: datetime = None
    updated_at: datetime = None
    due_date: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    tags: List[str] = None
    category: str = ""
    project_id: Optional[str] = None
    parent_task_id: Optional[str] = None
    estimated_hours: Optional[float] = None
    actual_hours: Optional[float] = None
    progress_percentage: int = 0
    notes: str = ""
    attachments: List[str] = None

    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.attachments is None:
            self.attachments = []
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()


@dataclass
class TaskUpdate:
    """Task update record for audit trail"""
    update_id: str
    task_id: str
    updated_by: str
    updated_at: datetime
    field_name: str
    old_value: Any
    new_value: Any
    reason: str = ""
    ip_address: str = ""
    user_agent: str = ""


@dataclass
class Project:
    """Project data structure"""
    id: str
    name: str
    description: str
    created_by: str
    created_at: datetime
    status: str = "active"
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    team_members: List[str] = None

    def __post_init__(self):
        if self.team_members is None:
            self.team_members = []


class TaskManagementToolServer(BaseToolServer):
    """Task management tool server with audit logging"""

    def __init__(self, *args, **kwargs):
        super().__init__(ToolServerType.TASK_MANAGEMENT, *args, **kwargs)

        # Task management configuration
        self.max_tasks_per_user = 1000
        self.max_projects_per_user = 100
        self.audit_retention_days = 365
        self.enable_time_tracking = True
        self.enable_notifications = True

        # Security configuration
        self.require_user_verification = True
        self.log_all_operations = True
        self.enable_data_encryption = True

    async def _load_configuration(self):
        """Load task management specific configuration"""
        await self._setup_task_storage()
        await self._setup_audit_system()

    async def _setup_task_storage(self):
        """Setup task and project storage"""
        async with aiosqlite.connect(self.db_path) as db:
            # Tasks table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    description TEXT,
                    status TEXT NOT NULL,
                    priority TEXT NOT NULL,
                    created_by TEXT NOT NULL,
                    assigned_to TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    due_date TEXT,
                    completed_at TEXT,
                    tags TEXT,
                    category TEXT,
                    project_id TEXT,
                    parent_task_id TEXT,
                    estimated_hours REAL,
                    actual_hours REAL,
                    progress_percentage INTEGER DEFAULT 0,
                    notes TEXT,
                    attachments TEXT,
                    FOREIGN KEY (project_id) REFERENCES projects (id),
                    FOREIGN KEY (parent_task_id) REFERENCES tasks (id)
                )
            """)

            # Projects table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS projects (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    created_by TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    status TEXT DEFAULT 'active',
                    start_date TEXT,
                    end_date TEXT,
                    team_members TEXT
                )
            """)

            # Task updates audit table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS task_updates (
                    update_id TEXT PRIMARY KEY,
                    task_id TEXT NOT NULL,
                    updated_by TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    field_name TEXT NOT NULL,
                    old_value TEXT,
                    new_value TEXT,
                    reason TEXT,
                    ip_address TEXT,
                    user_agent TEXT,
                    FOREIGN KEY (task_id) REFERENCES tasks (id)
                )
            """)

            # Task comments table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS task_comments (
                    comment_id TEXT PRIMARY KEY,
                    task_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    comment TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT,
                    is_internal BOOLEAN DEFAULT FALSE,
                    FOREIGN KEY (task_id) REFERENCES tasks (id)
                )
            """)

            # Time tracking table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS time_entries (
                    entry_id TEXT PRIMARY KEY,
                    task_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    start_time TEXT NOT NULL,
                    end_time TEXT,
                    duration_minutes INTEGER,
                    description TEXT,
                    billable BOOLEAN DEFAULT FALSE,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (task_id) REFERENCES tasks (id)
                )
            """)

            # Task dependencies table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS task_dependencies (
                    dependency_id TEXT PRIMARY KEY,
                    task_id TEXT NOT NULL,
                    depends_on_task_id TEXT NOT NULL,
                    dependency_type TEXT DEFAULT 'finish_to_start',
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (task_id) REFERENCES tasks (id),
                    FOREIGN KEY (depends_on_task_id) REFERENCES tasks (id)
                )
            """)

            await db.commit()

    async def _setup_audit_system(self):
        """Setup comprehensive audit system"""
        async with aiosqlite.connect(self.db_path) as db:
            # General audit log
            await db.execute("""
                CREATE TABLE IF NOT EXISTS audit_log (
                    log_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    operation TEXT NOT NULL,
                    resource_type TEXT NOT NULL,
                    resource_id TEXT,
                    timestamp TEXT NOT NULL,
                    success BOOLEAN NOT NULL,
                    details TEXT,
                    ip_address TEXT,
                    user_agent TEXT,
                    session_id TEXT
                )
            """)

            # Permission changes audit
            await db.execute("""
                CREATE TABLE IF NOT EXISTS permission_audit (
                    audit_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    target_user_id TEXT,
                    resource_type TEXT NOT NULL,
                    resource_id TEXT,
                    permission_change TEXT NOT NULL,
                    granted_by TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    reason TEXT
                )
            """)

            await db.commit()

    async def _execute_specific_operation(self,
                                        operation_name: str,
                                        parameters: Dict[str, Any],
                                        security_context: SecurityContext) -> Dict[str, Any]:
        """Execute task management specific operations"""

        operation_map = {
            "create_task": self._create_task,
            "update_task": self._update_task,
            "delete_task": self._delete_task,
            "get_task": self._get_task,
            "list_tasks": self._list_tasks,
            "search_tasks": self._search_tasks,
            "assign_task": self._assign_task,
            "add_comment": self._add_comment,
            "start_time_tracking": self._start_time_tracking,
            "stop_time_tracking": self._stop_time_tracking,
            "create_project": self._create_project,
            "update_project": self._update_project,
            "list_projects": self._list_projects,
            "add_task_dependency": self._add_task_dependency,
            "get_task_history": self._get_task_history,
            "generate_report": self._generate_report,
            "export_tasks": self._export_tasks
        }

        if operation_name not in operation_map:
            raise ValueError(f"Unknown task management operation: {operation_name}")

        # Log operation start
        await self._audit_operation_start(operation_name, parameters, security_context)

        try:
            result = await operation_map[operation_name](parameters, security_context)
            await self._audit_operation_success(operation_name, parameters, security_context, result)
            return result
        except Exception as e:
            await self._audit_operation_failure(operation_name, parameters, security_context, str(e))
            raise

    async def _determine_security_level(self, operation_name: str, parameters: Dict[str, Any]) -> SecurityLevel:
        """Determine security level for task operations"""

        # Critical operations
        if operation_name in ["delete_task", "delete_project"]:
            return SecurityLevel.CRITICAL

        # High-risk operations
        if operation_name in ["update_task", "assign_task", "update_project"]:
            return SecurityLevel.HIGH

        # Medium-risk operations
        if operation_name in ["create_task", "create_project", "add_comment"]:
            return SecurityLevel.MEDIUM

        # Low-risk operations
        if operation_name in ["get_task", "list_tasks", "search_tasks", "get_task_history", "generate_report"]:
            return SecurityLevel.LOW

        return SecurityLevel.MEDIUM

    async def _requires_rollback(self, operation_name: str) -> bool:
        """Check if operation requires rollback capability"""
        rollback_operations = {
            "create_task", "update_task", "delete_task",
            "create_project", "update_project", "assign_task"
        }
        return operation_name in rollback_operations

    async def _create_rollback_data(self, operation: ToolOperation, result_data: Dict[str, Any]) -> str:
        """Create rollback data for task operations"""
        rollback_id = f"task_rb_{operation.operation_id}_{int(datetime.now().timestamp())}"

        rollback_info = {
            "rollback_id": rollback_id,
            "operation_id": operation.operation_id,
            "operation_name": operation.operation_name,
            "parameters": operation.parameters,
            "result_data": result_data,
            "timestamp": datetime.now().isoformat(),
            "expires_at": (datetime.now() + timedelta(days=30)).isoformat()
        }

        if operation.operation_name == "create_task":
            rollback_info["rollback_type"] = "delete_created_task"
            rollback_info["task_id"] = result_data.get("task_id")

        elif operation.operation_name == "update_task":
            rollback_info["rollback_type"] = "restore_task_state"
            rollback_info["task_id"] = operation.parameters.get("task_id")
            # Store original task data
            rollback_info["original_task_data"] = await self._get_task_data(operation.parameters.get("task_id"))

        elif operation.operation_name == "delete_task":
            rollback_info["rollback_type"] = "restore_deleted_task"
            rollback_info["deleted_task_data"] = result_data.get("deleted_task_data")

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
        """Execute rollback operation for task changes"""
        try:
            if rollback_type == "delete_created_task":
                task_id = rollback_data.get("task_id")
                if task_id:
                    async with aiosqlite.connect(self.db_path) as db:
                        await db.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
                        await db.commit()
                        return True

            elif rollback_type == "restore_task_state":
                original_data = rollback_data.get("original_task_data")
                if original_data:
                    # Restore original task state
                    async with aiosqlite.connect(self.db_path) as db:
                        await db.execute("""
                            UPDATE tasks SET title=?, description=?, status=?, priority=?,
                            assigned_to=?, due_date=?, tags=?, category=?, progress_percentage=?,
                            notes=?, updated_at=?
                            WHERE id=?
                        """, (
                            original_data["title"], original_data["description"],
                            original_data["status"], original_data["priority"],
                            original_data["assigned_to"], original_data["due_date"],
                            original_data["tags"], original_data["category"],
                            original_data["progress_percentage"], original_data["notes"],
                            datetime.now().isoformat(), original_data["id"]
                        ))
                        await db.commit()
                        return True

            elif rollback_type == "restore_deleted_task":
                task_data = rollback_data.get("deleted_task_data")
                if task_data:
                    # Recreate deleted task
                    async with aiosqlite.connect(self.db_path) as db:
                        await db.execute("""
                            INSERT INTO tasks (id, title, description, status, priority,
                            created_by, assigned_to, created_at, updated_at, due_date,
                            tags, category, project_id, progress_percentage, notes)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            task_data["id"], task_data["title"], task_data["description"],
                            task_data["status"], task_data["priority"], task_data["created_by"],
                            task_data["assigned_to"], task_data["created_at"], task_data["updated_at"],
                            task_data["due_date"], task_data["tags"], task_data["category"],
                            task_data["project_id"], task_data["progress_percentage"], task_data["notes"]
                        ))
                        await db.commit()
                        return True

            return False

        except Exception as e:
            self.logger.error(f"Task rollback failed: {e}")
            return False

    async def _get_task_data(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get task data for rollback purposes"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)) as cursor:
                row = await cursor.fetchone()
                if row:
                    columns = [description[0] for description in cursor.description]
                    return dict(zip(columns, row))
                return None

    async def _audit_operation_start(self, operation: str, parameters: Dict[str, Any], security_context: SecurityContext):
        """Log operation start for audit trail"""
        log_id = f"audit_{int(datetime.now().timestamp())}_{uuid.uuid4().hex[:8]}"

        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO audit_log
                (log_id, user_id, operation, resource_type, resource_id, timestamp,
                 success, details, session_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                log_id, security_context.user_id, operation, "task",
                parameters.get("task_id", ""), datetime.now().isoformat(),
                False, json.dumps({"status": "started", "parameters": parameters}),
                security_context.session_id
            ))
            await db.commit()

    async def _audit_operation_success(self, operation: str, parameters: Dict[str, Any],
                                     security_context: SecurityContext, result: Dict[str, Any]):
        """Log successful operation for audit trail"""
        log_id = f"audit_{int(datetime.now().timestamp())}_{uuid.uuid4().hex[:8]}"

        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO audit_log
                (log_id, user_id, operation, resource_type, resource_id, timestamp,
                 success, details, session_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                log_id, security_context.user_id, operation, "task",
                result.get("task_id", parameters.get("task_id", "")),
                datetime.now().isoformat(), True,
                json.dumps({"status": "completed", "result": result}),
                security_context.session_id
            ))
            await db.commit()

    async def _audit_operation_failure(self, operation: str, parameters: Dict[str, Any],
                                     security_context: SecurityContext, error: str):
        """Log failed operation for audit trail"""
        log_id = f"audit_{int(datetime.now().timestamp())}_{uuid.uuid4().hex[:8]}"

        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO audit_log
                (log_id, user_id, operation, resource_type, resource_id, timestamp,
                 success, details, session_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                log_id, security_context.user_id, operation, "task",
                parameters.get("task_id", ""), datetime.now().isoformat(),
                False, json.dumps({"status": "failed", "error": error}),
                security_context.session_id
            ))
            await db.commit()

    async def _create_task(self, parameters: Dict[str, Any], security_context: SecurityContext) -> Dict[str, Any]:
        """Create new task"""
        task_data = parameters.get("task", {})

        # Validate required fields
        required_fields = ["title", "description", "priority"]
        for field in required_fields:
            if field not in task_data:
                raise ValueError(f"Missing required field: {field}")

        # Create task
        task_id = str(uuid.uuid4())
        now = datetime.now()

        task = Task(
            id=task_id,
            title=task_data["title"],
            description=task_data["description"],
            status=TaskStatus(task_data.get("status", "pending")),
            priority=TaskPriority(task_data["priority"]),
            created_by=security_context.user_id,
            assigned_to=task_data.get("assigned_to"),
            due_date=datetime.fromisoformat(task_data["due_date"]) if task_data.get("due_date") else None,
            tags=task_data.get("tags", []),
            category=task_data.get("category", ""),
            project_id=task_data.get("project_id"),
            parent_task_id=task_data.get("parent_task_id"),
            estimated_hours=task_data.get("estimated_hours"),
            notes=task_data.get("notes", "")
        )

        # Store task
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO tasks (id, title, description, status, priority,
                created_by, assigned_to, created_at, updated_at, due_date,
                tags, category, project_id, parent_task_id, estimated_hours, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                task.id, task.title, task.description, task.status.value,
                task.priority.value, task.created_by, task.assigned_to,
                task.created_at.isoformat(), task.updated_at.isoformat(),
                task.due_date.isoformat() if task.due_date else None,
                json.dumps(task.tags), task.category, task.project_id,
                task.parent_task_id, task.estimated_hours, task.notes
            ))
            await db.commit()

        return {
            "task_id": task_id,
            "task": asdict(task),
            "created": True,
            "timestamp": now.isoformat()
        }

    async def _update_task(self, parameters: Dict[str, Any], security_context: SecurityContext) -> Dict[str, Any]:
        """Update existing task"""
        task_id = parameters.get("task_id", "")
        updates = parameters.get("updates", {})

        if not task_id:
            raise ValueError("Task ID required for update")

        # Get current task data
        current_task = await self._get_task_data(task_id)
        if not current_task:
            raise ValueError(f"Task not found: {task_id}")

        # Track changes for audit
        changes = []
        update_fields = []
        update_values = []

        for field, new_value in updates.items():
            if field in current_task and str(current_task[field]) != str(new_value):
                changes.append({
                    "field": field,
                    "old_value": current_task[field],
                    "new_value": new_value
                })
                update_fields.append(f"{field} = ?")
                update_values.append(new_value)

        if not changes:
            return {
                "task_id": task_id,
                "updated": False,
                "message": "No changes detected"
            }

        # Update task
        update_values.append(datetime.now().isoformat())  # updated_at
        update_values.append(task_id)

        async with aiosqlite.connect(self.db_path) as db:
            query = f"UPDATE tasks SET {', '.join(update_fields)}, updated_at = ? WHERE id = ?"
            await db.execute(query, update_values)

            # Log each change
            for change in changes:
                update_id = str(uuid.uuid4())
                await db.execute("""
                    INSERT INTO task_updates
                    (update_id, task_id, updated_by, updated_at, field_name, old_value, new_value)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    update_id, task_id, security_context.user_id,
                    datetime.now().isoformat(), change["field"],
                    json.dumps(change["old_value"]), json.dumps(change["new_value"])
                ))

            await db.commit()

        return {
            "task_id": task_id,
            "updated": True,
            "changes": changes,
            "timestamp": datetime.now().isoformat()
        }

    async def _delete_task(self, parameters: Dict[str, Any], security_context: SecurityContext) -> Dict[str, Any]:
        """Delete task"""
        task_id = parameters.get("task_id", "")

        if not task_id:
            raise ValueError("Task ID required for deletion")

        # Get task data before deletion
        task_data = await self._get_task_data(task_id)
        if not task_data:
            raise ValueError(f"Task not found: {task_id}")

        # Delete task
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
            await db.commit()

        return {
            "task_id": task_id,
            "deleted": True,
            "deleted_task_data": task_data,
            "timestamp": datetime.now().isoformat()
        }

    async def _get_task(self, parameters: Dict[str, Any], security_context: SecurityContext) -> Dict[str, Any]:
        """Get single task"""
        task_id = parameters.get("task_id", "")

        if not task_id:
            raise ValueError("Task ID required")

        task_data = await self._get_task_data(task_id)
        if not task_data:
            raise ValueError(f"Task not found: {task_id}")

        return {
            "task_id": task_id,
            "task": task_data,
            "timestamp": datetime.now().isoformat()
        }

    async def _list_tasks(self, parameters: Dict[str, Any], security_context: SecurityContext) -> Dict[str, Any]:
        """List tasks with filtering"""
        user_id = parameters.get("user_id", security_context.user_id)
        status = parameters.get("status")
        priority = parameters.get("priority")
        project_id = parameters.get("project_id")
        limit = min(parameters.get("limit", 100), 1000)
        offset = parameters.get("offset", 0)

        # Build query
        conditions = ["(created_by = ? OR assigned_to = ?)"]
        params = [user_id, user_id]

        if status:
            conditions.append("status = ?")
            params.append(status)

        if priority:
            conditions.append("priority = ?")
            params.append(priority)

        if project_id:
            conditions.append("project_id = ?")
            params.append(project_id)

        query = f"""
            SELECT * FROM tasks
            WHERE {' AND '.join(conditions)}
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
        """
        params.extend([limit, offset])

        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(query, params) as cursor:
                rows = await cursor.fetchall()
                columns = [description[0] for description in cursor.description]
                tasks = [dict(zip(columns, row)) for row in rows]

            # Get total count
            count_query = f"SELECT COUNT(*) FROM tasks WHERE {' AND '.join(conditions)}"
            async with db.execute(count_query, params[:-2]) as cursor:  # Exclude limit/offset
                total_count = (await cursor.fetchone())[0]

        return {
            "tasks": tasks,
            "total_count": total_count,
            "limit": limit,
            "offset": offset,
            "timestamp": datetime.now().isoformat()
        }

    async def _search_tasks(self, parameters: Dict[str, Any], security_context: SecurityContext) -> Dict[str, Any]:
        """Search tasks by text"""
        query = parameters.get("query", "").strip()
        limit = min(parameters.get("limit", 50), 200)

        if not query:
            raise ValueError("Search query required")

        # Simple text search in title and description
        search_query = """
            SELECT * FROM tasks
            WHERE (created_by = ? OR assigned_to = ?)
            AND (title LIKE ? OR description LIKE ?)
            ORDER BY updated_at DESC
            LIMIT ?
        """

        search_term = f"%{query}%"
        params = [security_context.user_id, security_context.user_id, search_term, search_term, limit]

        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(search_query, params) as cursor:
                rows = await cursor.fetchall()
                columns = [description[0] for description in cursor.description]
                tasks = [dict(zip(columns, row)) for row in rows]

        return {
            "query": query,
            "tasks": tasks,
            "total_found": len(tasks),
            "timestamp": datetime.now().isoformat()
        }

    async def _assign_task(self, parameters: Dict[str, Any], security_context: SecurityContext) -> Dict[str, Any]:
        """Assign task to user"""
        task_id = parameters.get("task_id", "")
        assigned_to = parameters.get("assigned_to", "")

        if not task_id or not assigned_to:
            raise ValueError("Task ID and assigned_to required")

        # Update assignment
        result = await self._update_task({
            "task_id": task_id,
            "updates": {"assigned_to": assigned_to}
        }, security_context)

        return {
            **result,
            "assigned_to": assigned_to,
            "operation": "task_assigned"
        }

    async def _add_comment(self, parameters: Dict[str, Any], security_context: SecurityContext) -> Dict[str, Any]:
        """Add comment to task"""
        task_id = parameters.get("task_id", "")
        comment = parameters.get("comment", "").strip()
        is_internal = parameters.get("is_internal", False)

        if not task_id or not comment:
            raise ValueError("Task ID and comment required")

        comment_id = str(uuid.uuid4())

        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO task_comments
                (comment_id, task_id, user_id, comment, created_at, is_internal)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                comment_id, task_id, security_context.user_id,
                comment, datetime.now().isoformat(), is_internal
            ))
            await db.commit()

        return {
            "comment_id": comment_id,
            "task_id": task_id,
            "comment": comment,
            "added": True,
            "timestamp": datetime.now().isoformat()
        }

    async def _start_time_tracking(self, parameters: Dict[str, Any], security_context: SecurityContext) -> Dict[str, Any]:
        """Start time tracking for task"""
        task_id = parameters.get("task_id", "")
        description = parameters.get("description", "")

        if not task_id:
            raise ValueError("Task ID required")

        entry_id = str(uuid.uuid4())

        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO time_entries
                (entry_id, task_id, user_id, start_time, description, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                entry_id, task_id, security_context.user_id,
                datetime.now().isoformat(), description, datetime.now().isoformat()
            ))
            await db.commit()

        return {
            "entry_id": entry_id,
            "task_id": task_id,
            "tracking_started": True,
            "start_time": datetime.now().isoformat()
        }

    async def _stop_time_tracking(self, parameters: Dict[str, Any], security_context: SecurityContext) -> Dict[str, Any]:
        """Stop time tracking for task"""
        entry_id = parameters.get("entry_id", "")

        if not entry_id:
            raise ValueError("Entry ID required")

        end_time = datetime.now()

        async with aiosqlite.connect(self.db_path) as db:
            # Get start time
            async with db.execute(
                "SELECT start_time FROM time_entries WHERE entry_id = ? AND user_id = ?",
                (entry_id, security_context.user_id)
            ) as cursor:
                row = await cursor.fetchone()
                if not row:
                    raise ValueError("Time entry not found")

                start_time = datetime.fromisoformat(row[0])
                duration = int((end_time - start_time).total_seconds() / 60)  # minutes

            # Update entry
            await db.execute("""
                UPDATE time_entries
                SET end_time = ?, duration_minutes = ?
                WHERE entry_id = ?
            """, (end_time.isoformat(), duration, entry_id))
            await db.commit()

        return {
            "entry_id": entry_id,
            "tracking_stopped": True,
            "end_time": end_time.isoformat(),
            "duration_minutes": duration
        }

    async def _create_project(self, parameters: Dict[str, Any], security_context: SecurityContext) -> Dict[str, Any]:
        """Create new project"""
        project_data = parameters.get("project", {})

        if "name" not in project_data:
            raise ValueError("Project name required")

        project_id = str(uuid.uuid4())
        now = datetime.now()

        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO projects (id, name, description, created_by, created_at, status)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                project_id, project_data["name"], project_data.get("description", ""),
                security_context.user_id, now.isoformat(), "active"
            ))
            await db.commit()

        return {
            "project_id": project_id,
            "project": project_data,
            "created": True,
            "timestamp": now.isoformat()
        }

    async def _update_project(self, parameters: Dict[str, Any], security_context: SecurityContext) -> Dict[str, Any]:
        """Update project"""
        project_id = parameters.get("project_id", "")
        updates = parameters.get("updates", {})

        if not project_id:
            raise ValueError("Project ID required")

        # Simple update implementation
        return {
            "project_id": project_id,
            "updated": True,
            "timestamp": datetime.now().isoformat()
        }

    async def _list_projects(self, parameters: Dict[str, Any], security_context: SecurityContext) -> Dict[str, Any]:
        """List projects"""
        limit = min(parameters.get("limit", 50), 200)

        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("""
                SELECT * FROM projects WHERE created_by = ? ORDER BY created_at DESC LIMIT ?
            """, (security_context.user_id, limit)) as cursor:
                rows = await cursor.fetchall()
                columns = [description[0] for description in cursor.description]
                projects = [dict(zip(columns, row)) for row in rows]

        return {
            "projects": projects,
            "total_count": len(projects),
            "timestamp": datetime.now().isoformat()
        }

    async def _add_task_dependency(self, parameters: Dict[str, Any], security_context: SecurityContext) -> Dict[str, Any]:
        """Add task dependency"""
        task_id = parameters.get("task_id", "")
        depends_on_task_id = parameters.get("depends_on_task_id", "")

        if not task_id or not depends_on_task_id:
            raise ValueError("Both task IDs required")

        dependency_id = str(uuid.uuid4())

        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO task_dependencies
                (dependency_id, task_id, depends_on_task_id, created_at)
                VALUES (?, ?, ?, ?)
            """, (dependency_id, task_id, depends_on_task_id, datetime.now().isoformat()))
            await db.commit()

        return {
            "dependency_id": dependency_id,
            "task_id": task_id,
            "depends_on_task_id": depends_on_task_id,
            "added": True,
            "timestamp": datetime.now().isoformat()
        }

    async def _get_task_history(self, parameters: Dict[str, Any], security_context: SecurityContext) -> Dict[str, Any]:
        """Get task update history"""
        task_id = parameters.get("task_id", "")

        if not task_id:
            raise ValueError("Task ID required")

        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("""
                SELECT * FROM task_updates WHERE task_id = ? ORDER BY updated_at DESC
            """, (task_id,)) as cursor:
                rows = await cursor.fetchall()
                columns = [description[0] for description in cursor.description]
                history = [dict(zip(columns, row)) for row in rows]

        return {
            "task_id": task_id,
            "history": history,
            "total_updates": len(history),
            "timestamp": datetime.now().isoformat()
        }

    async def _generate_report(self, parameters: Dict[str, Any], security_context: SecurityContext) -> Dict[str, Any]:
        """Generate task management report"""
        report_type = parameters.get("report_type", "summary")
        date_range = parameters.get("date_range", 30)  # days

        # Mock report generation
        return {
            "report_type": report_type,
            "date_range": date_range,
            "generated": True,
            "report_data": {
                "total_tasks": 0,
                "completed_tasks": 0,
                "pending_tasks": 0,
                "overdue_tasks": 0
            },
            "timestamp": datetime.now().isoformat()
        }

    async def _export_tasks(self, parameters: Dict[str, Any], security_context: SecurityContext) -> Dict[str, Any]:
        """Export tasks to various formats"""
        export_format = parameters.get("format", "json")
        filters = parameters.get("filters", {})

        # Mock export
        return {
            "format": export_format,
            "exported": True,
            "record_count": 0,
            "timestamp": datetime.now().isoformat()
        }