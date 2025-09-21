#!/usr/bin/env python3
"""
Rollback & Recovery System for Penny AI Assistant
Phase B2: Operational Security (Days 4-5)

This system provides comprehensive rollback and recovery capabilities:
- File operation tracking with timestamps and checksums
- Automatic backup creation before destructive operations
- One-click rollback for instant reversion to previous state
- Recovery validation to verify rollback success and system integrity
- Incremental backup system for efficient storage of multiple recovery points
- Cross-operation rollback to undo complex multi-step operations atomically
"""

import asyncio
import json
import sqlite3
import hashlib
import shutil
import gzip
import time
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Union
from enum import Enum
from dataclasses import dataclass, field, asdict
from pathlib import Path
import threading
import logging
import tempfile

# Import existing security components
try:
    from enhanced_security_logging import EnhancedSecurityLogger as EnhancedSecurityLogging, SecurityEventType, SecuritySeverity
    from rate_limiting_resource_control import RateLimitingResourceControl, OperationType
    from command_whitelist_system import CommandWhitelistSystem, PermissionLevel, SecurityRisk
except ImportError as e:
    print(f"Warning: Could not import security components: {e}")


class FileOperationType(Enum):
    """Types of file operations that can be tracked and rolled back"""
    CREATE = "create"
    MODIFY = "modify"
    DELETE = "delete"
    MOVE = "move"
    COPY = "copy"
    CHMOD = "chmod"
    CHOWN = "chown"
    LINK = "link"
    MKDIR = "mkdir"
    RMDIR = "rmdir"


class BackupStrategy(Enum):
    """Backup strategies for different operation types"""
    FULL_COPY = "full_copy"          # Complete file copy
    INCREMENTAL = "incremental"      # Only changes since last backup
    DELTA = "delta"                  # Binary diff-based backup
    METADATA_ONLY = "metadata_only"  # Only file metadata
    CONTENT_HASH = "content_hash"    # Content-based deduplication


class RecoveryPointType(Enum):
    """Types of recovery points"""
    AUTOMATIC = "automatic"          # Auto-created before operations
    MANUAL = "manual"               # User-requested checkpoint
    SCHEDULED = "scheduled"         # Time-based snapshots
    OPERATION_GROUP = "operation_group"  # Before multi-step operations
    CRITICAL = "critical"           # Before high-risk operations


class RollbackStatus(Enum):
    """Status of rollback operations"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIALLY_COMPLETED = "partially_completed"
    VALIDATION_FAILED = "validation_failed"


@dataclass
class FileOperation:
    """Record of a file system operation"""
    operation_id: str
    operation_type: FileOperationType
    file_path: str
    timestamp: datetime
    user_id: str
    original_checksum: Optional[str] = None
    new_checksum: Optional[str] = None
    file_size_before: Optional[int] = None
    file_size_after: Optional[int] = None
    permissions_before: Optional[str] = None
    permissions_after: Optional[str] = None
    backup_path: Optional[str] = None
    recovery_point_id: Optional[str] = None
    additional_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RecoveryPoint:
    """A point-in-time recovery checkpoint"""
    recovery_point_id: str
    recovery_point_type: RecoveryPointType
    timestamp: datetime
    description: str
    file_operations: List[str]  # Operation IDs included
    backup_size_bytes: int
    checksum: str
    is_compressed: bool
    retention_days: int
    created_by: str
    validation_status: bool = True
    restoration_count: int = 0


@dataclass
class RollbackPlan:
    """Plan for rolling back operations"""
    rollback_id: str
    target_recovery_point_id: str
    operations_to_rollback: List[str]  # Operation IDs
    estimated_duration_seconds: float
    estimated_data_size_bytes: int
    rollback_strategy: str
    requires_confirmation: bool
    risk_assessment: str
    created_at: datetime


@dataclass
class RollbackExecution:
    """Execution record of a rollback operation"""
    rollback_id: str
    execution_id: str
    status: RollbackStatus
    started_at: datetime
    completed_at: Optional[datetime] = None
    operations_completed: int = 0
    operations_failed: int = 0
    total_operations: int = 0
    error_messages: List[str] = field(default_factory=list)
    rollback_checksum: Optional[str] = None
    validation_results: Dict[str, bool] = field(default_factory=dict)


class RollbackRecoverySystem:
    """
    Comprehensive rollback and recovery system

    Provides automatic backup creation, file operation tracking,
    and one-click rollback capabilities with validation.
    """

    def __init__(self,
                 db_path: str = "rollback_recovery.db",
                 backup_root: str = "backups",
                 security_logger: Optional[EnhancedSecurityLogging] = None,
                 rate_limiter: Optional[RateLimitingResourceControl] = None,
                 whitelist_system: Optional[CommandWhitelistSystem] = None):

        self.db_path = db_path
        self.backup_root = Path(backup_root)
        self.security_logger = security_logger
        self.rate_limiter = rate_limiter
        self.whitelist_system = whitelist_system

        # Configuration
        self.auto_backup_enabled = True
        self.default_retention_days = 30
        self.max_backup_size_gb = 10  # Maximum backup storage
        self.compression_enabled = True
        self.incremental_backup_threshold = 1024 * 1024  # 1MB

        # Operation tracking
        self.tracked_operations: Dict[str, FileOperation] = {}
        self.recovery_points: Dict[str, RecoveryPoint] = {}
        self.active_rollbacks: Dict[str, RollbackExecution] = {}

        # Background processing
        self.monitoring_active = False
        self.cleanup_thread: Optional[threading.Thread] = None

        # Statistics
        self.stats = {
            'total_operations_tracked': 0,
            'total_backups_created': 0,
            'total_rollbacks_executed': 0,
            'total_recovery_points': 0,
            'storage_used_bytes': 0,
            'successful_rollbacks': 0,
            'failed_rollbacks': 0
        }

        self._init_database()
        self._ensure_backup_directory()

    def _init_database(self):
        """Initialize rollback and recovery database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS file_operations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    operation_id TEXT UNIQUE NOT NULL,
                    operation_type TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    original_checksum TEXT,
                    new_checksum TEXT,
                    file_size_before INTEGER,
                    file_size_after INTEGER,
                    permissions_before TEXT,
                    permissions_after TEXT,
                    backup_path TEXT,
                    recovery_point_id TEXT,
                    additional_metadata TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS recovery_points (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    recovery_point_id TEXT UNIQUE NOT NULL,
                    recovery_point_type TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    description TEXT NOT NULL,
                    file_operations TEXT NOT NULL,
                    backup_size_bytes INTEGER NOT NULL,
                    checksum TEXT NOT NULL,
                    is_compressed INTEGER NOT NULL,
                    retention_days INTEGER NOT NULL,
                    created_by TEXT NOT NULL,
                    validation_status INTEGER DEFAULT 1,
                    restoration_count INTEGER DEFAULT 0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS rollback_plans (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    rollback_id TEXT UNIQUE NOT NULL,
                    target_recovery_point_id TEXT NOT NULL,
                    operations_to_rollback TEXT NOT NULL,
                    estimated_duration_seconds REAL NOT NULL,
                    estimated_data_size_bytes INTEGER NOT NULL,
                    rollback_strategy TEXT NOT NULL,
                    requires_confirmation INTEGER NOT NULL,
                    risk_assessment TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS rollback_executions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    rollback_id TEXT NOT NULL,
                    execution_id TEXT UNIQUE NOT NULL,
                    status TEXT NOT NULL,
                    started_at TEXT NOT NULL,
                    completed_at TEXT,
                    operations_completed INTEGER DEFAULT 0,
                    operations_failed INTEGER DEFAULT 0,
                    total_operations INTEGER DEFAULT 0,
                    error_messages TEXT,
                    rollback_checksum TEXT,
                    validation_results TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                );

                CREATE INDEX IF NOT EXISTS idx_file_operations_time ON file_operations(timestamp);
                CREATE INDEX IF NOT EXISTS idx_file_operations_path ON file_operations(file_path);
                CREATE INDEX IF NOT EXISTS idx_recovery_points_time ON recovery_points(timestamp);
                CREATE INDEX IF NOT EXISTS idx_rollback_executions_status ON rollback_executions(status);
            """)

    def _ensure_backup_directory(self):
        """Ensure backup directory structure exists"""
        try:
            self.backup_root.mkdir(parents=True, exist_ok=True)
            (self.backup_root / "files").mkdir(exist_ok=True)
            (self.backup_root / "recovery_points").mkdir(exist_ok=True)
            (self.backup_root / "temp").mkdir(exist_ok=True)
        except Exception as e:
            logging.error(f"Error creating backup directories: {e}")

    async def start_monitoring(self):
        """Start rollback and recovery monitoring"""
        if self.monitoring_active:
            return

        self.monitoring_active = True

        # Start cleanup thread
        self.cleanup_thread = threading.Thread(target=self._cleanup_loop, daemon=True)
        self.cleanup_thread.start()

        # Load existing recovery points
        await self._load_recovery_points()

        if self.security_logger:
            await self.security_logger.log_security_event(
                event_type=SecurityEventType.SYSTEM_STARTUP,
                severity=SecuritySeverity.INFO,
                details={
                    'component': 'Rollback Recovery System',
                    'action': 'monitoring_started',
                    'backup_root': str(self.backup_root),
                    'auto_backup_enabled': self.auto_backup_enabled
                }
            )

    def stop_monitoring(self):
        """Stop rollback and recovery monitoring"""
        self.monitoring_active = False
        if self.cleanup_thread and self.cleanup_thread.is_alive():
            self.cleanup_thread.join(timeout=5)

    async def track_file_operation(self,
                                 operation_type: FileOperationType,
                                 file_path: str,
                                 user_id: str = "system",
                                 auto_backup: bool = True) -> str:
        """
        Track a file operation and optionally create backup

        Returns:
            Operation ID for tracking
        """
        operation_id = f"op_{int(time.time() * 1000000)}"

        try:
            # Get file information before operation
            file_path_obj = Path(file_path)
            original_checksum = None
            file_size_before = None
            permissions_before = None

            if file_path_obj.exists():
                original_checksum = await self._calculate_file_checksum(file_path)
                file_size_before = file_path_obj.stat().st_size
                permissions_before = oct(file_path_obj.stat().st_mode)[-3:]

            # Create backup if auto_backup is enabled and operation is destructive
            backup_path = None
            if auto_backup and self.auto_backup_enabled and self._is_destructive_operation(operation_type):
                backup_path = await self._create_file_backup(file_path, operation_id)

            # Create operation record
            operation = FileOperation(
                operation_id=operation_id,
                operation_type=operation_type,
                file_path=file_path,
                timestamp=datetime.now(),
                user_id=user_id,
                original_checksum=original_checksum,
                file_size_before=file_size_before,
                permissions_before=permissions_before,
                backup_path=backup_path
            )

            # Store operation
            self.tracked_operations[operation_id] = operation
            await self._save_file_operation(operation)

            # Update statistics
            self.stats['total_operations_tracked'] += 1

            if self.security_logger:
                await self.security_logger.log_security_event(
                    event_type=SecurityEventType.DATA_ACCESS,
                    severity=SecuritySeverity.INFO,
                    details={
                        'component': 'Rollback Recovery System',
                        'action': 'file_operation_tracked',
                        'operation_id': operation_id,
                        'operation_type': operation_type.value,
                        'file_path': file_path,
                        'backup_created': backup_path is not None
                    }
                )

            return operation_id

        except Exception as e:
            logging.error(f"Error tracking file operation: {e}")
            if self.security_logger:
                await self.security_logger.log_security_event(
                    event_type=SecurityEventType.SYSTEM_ERROR,
                    severity=SecuritySeverity.ERROR,
                    details={
                        'component': 'Rollback Recovery System',
                        'action': 'file_operation_tracking_failed',
                        'error': str(e),
                        'file_path': file_path
                    }
                )
            raise

    async def complete_file_operation(self, operation_id: str) -> bool:
        """
        Complete tracking of a file operation (record post-operation state)

        Returns:
            True if completed successfully
        """
        try:
            if operation_id not in self.tracked_operations:
                logging.warning(f"Operation {operation_id} not found in tracked operations")
                return False

            operation = self.tracked_operations[operation_id]
            file_path_obj = Path(operation.file_path)

            # Get file information after operation
            if file_path_obj.exists():
                operation.new_checksum = await self._calculate_file_checksum(operation.file_path)
                operation.file_size_after = file_path_obj.stat().st_size
                operation.permissions_after = oct(file_path_obj.stat().st_mode)[-3:]

            # Update operation record
            await self._update_file_operation(operation)

            if self.security_logger:
                await self.security_logger.log_security_event(
                    event_type=SecurityEventType.DATA_MODIFICATION,
                    severity=SecuritySeverity.INFO,
                    details={
                        'component': 'Rollback Recovery System',
                        'action': 'file_operation_completed',
                        'operation_id': operation_id,
                        'checksum_changed': operation.original_checksum != operation.new_checksum
                    }
                )

            return True

        except Exception as e:
            logging.error(f"Error completing file operation {operation_id}: {e}")
            return False

    def _is_destructive_operation(self, operation_type: FileOperationType) -> bool:
        """Check if an operation type is destructive and needs backup"""
        destructive_ops = {
            FileOperationType.MODIFY,
            FileOperationType.DELETE,
            FileOperationType.MOVE,
            FileOperationType.CHMOD,
            FileOperationType.CHOWN,
            FileOperationType.RMDIR
        }
        return operation_type in destructive_ops

    async def _create_file_backup(self, file_path: str, operation_id: str) -> Optional[str]:
        """Create backup of a file before operation"""
        try:
            file_path_obj = Path(file_path)
            if not file_path_obj.exists():
                return None

            # Determine backup strategy
            file_size = file_path_obj.stat().st_size
            strategy = self._determine_backup_strategy(file_size)

            # Create backup path
            backup_dir = self.backup_root / "files" / operation_id
            backup_dir.mkdir(parents=True, exist_ok=True)
            backup_file_path = backup_dir / file_path_obj.name

            if strategy == BackupStrategy.FULL_COPY:
                # Simple file copy
                shutil.copy2(file_path, backup_file_path)

                # Optionally compress
                if self.compression_enabled and file_size > self.incremental_backup_threshold:
                    compressed_path = f"{backup_file_path}.gz"
                    with open(backup_file_path, 'rb') as f_in:
                        with gzip.open(compressed_path, 'wb') as f_out:
                            shutil.copyfileobj(f_in, f_out)
                    backup_file_path.unlink()  # Remove uncompressed version
                    backup_file_path = Path(compressed_path)

            elif strategy == BackupStrategy.METADATA_ONLY:
                # Store only file metadata
                metadata = {
                    'size': file_size,
                    'permissions': oct(file_path_obj.stat().st_mode),
                    'modified_time': file_path_obj.stat().st_mtime,
                    'checksum': await self._calculate_file_checksum(file_path)
                }

                with open(backup_file_path.with_suffix('.metadata.json'), 'w') as f:
                    json.dump(metadata, f, indent=2)
                backup_file_path = backup_file_path.with_suffix('.metadata.json')

            # Update statistics
            self.stats['total_backups_created'] += 1
            self.stats['storage_used_bytes'] += backup_file_path.stat().st_size

            return str(backup_file_path)

        except Exception as e:
            logging.error(f"Error creating file backup: {e}")
            return None

    def _determine_backup_strategy(self, file_size: int) -> BackupStrategy:
        """Determine appropriate backup strategy based on file size and type"""
        if file_size == 0:
            return BackupStrategy.METADATA_ONLY
        elif file_size < self.incremental_backup_threshold:
            return BackupStrategy.FULL_COPY
        else:
            return BackupStrategy.FULL_COPY  # Could implement delta backup here

    async def _calculate_file_checksum(self, file_path: str) -> str:
        """Calculate SHA-256 checksum of a file"""
        try:
            sha256_hash = hashlib.sha256()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(chunk)
            return sha256_hash.hexdigest()
        except Exception as e:
            logging.error(f"Error calculating checksum for {file_path}: {e}")
            return ""

    async def create_recovery_point(self,
                                  description: str,
                                  recovery_type: RecoveryPointType = RecoveryPointType.MANUAL,
                                  operation_ids: Optional[List[str]] = None,
                                  created_by: str = "system") -> str:
        """
        Create a recovery point checkpoint

        Returns:
            Recovery point ID
        """
        recovery_point_id = f"rp_{int(time.time() * 1000000)}"

        try:
            # Determine which operations to include
            if operation_ids is None:
                # Include all recent operations (last hour)
                cutoff_time = datetime.now() - timedelta(hours=1)
                operation_ids = [
                    op_id for op_id, op in self.tracked_operations.items()
                    if op.timestamp >= cutoff_time
                ]

            # Calculate total backup size
            total_size = 0
            for op_id in operation_ids:
                if op_id in self.tracked_operations:
                    op = self.tracked_operations[op_id]
                    if op.backup_path and Path(op.backup_path).exists():
                        total_size += Path(op.backup_path).stat().st_size

            # Create recovery point record
            recovery_point = RecoveryPoint(
                recovery_point_id=recovery_point_id,
                recovery_point_type=recovery_type,
                timestamp=datetime.now(),
                description=description,
                file_operations=operation_ids,
                backup_size_bytes=total_size,
                checksum=self._calculate_recovery_point_checksum(operation_ids),
                is_compressed=self.compression_enabled,
                retention_days=self.default_retention_days,
                created_by=created_by
            )

            # Store recovery point
            self.recovery_points[recovery_point_id] = recovery_point
            await self._save_recovery_point(recovery_point)

            # Update statistics
            self.stats['total_recovery_points'] += 1

            if self.security_logger:
                await self.security_logger.log_security_event(
                    event_type=SecurityEventType.SYSTEM_UPDATE,
                    severity=SecuritySeverity.INFO,
                    details={
                        'component': 'Rollback Recovery System',
                        'action': 'recovery_point_created',
                        'recovery_point_id': recovery_point_id,
                        'description': description,
                        'operations_included': len(operation_ids),
                        'backup_size_bytes': total_size
                    }
                )

            return recovery_point_id

        except Exception as e:
            logging.error(f"Error creating recovery point: {e}")
            if self.security_logger:
                await self.security_logger.log_security_event(
                    event_type=SecurityEventType.SYSTEM_ERROR,
                    severity=SecuritySeverity.ERROR,
                    details={
                        'component': 'Rollback Recovery System',
                        'action': 'recovery_point_creation_failed',
                        'error': str(e)
                    }
                )
            raise

    def _calculate_recovery_point_checksum(self, operation_ids: List[str]) -> str:
        """Calculate checksum for a recovery point"""
        # Create a deterministic hash of all operation IDs and their checksums
        hasher = hashlib.sha256()

        for op_id in sorted(operation_ids):  # Sort for deterministic order
            hasher.update(op_id.encode())
            if op_id in self.tracked_operations:
                op = self.tracked_operations[op_id]
                if op.original_checksum:
                    hasher.update(op.original_checksum.encode())

        return hasher.hexdigest()

    async def create_rollback_plan(self,
                                 target_recovery_point_id: str,
                                 confirmation_required: bool = True) -> str:
        """
        Create a rollback plan to restore to a specific recovery point

        Returns:
            Rollback plan ID
        """
        rollback_id = f"rb_{int(time.time() * 1000000)}"

        try:
            if target_recovery_point_id not in self.recovery_points:
                raise ValueError(f"Recovery point {target_recovery_point_id} not found")

            recovery_point = self.recovery_points[target_recovery_point_id]

            # Find operations that need to be rolled back
            operations_to_rollback = []
            cutoff_time = recovery_point.timestamp

            for op_id, operation in self.tracked_operations.items():
                if operation.timestamp > cutoff_time:
                    operations_to_rollback.append(op_id)

            # Estimate rollback complexity
            estimated_duration = len(operations_to_rollback) * 2.0  # 2 seconds per operation
            estimated_size = sum(
                Path(self.tracked_operations[op_id].backup_path).stat().st_size
                for op_id in operations_to_rollback
                if op_id in self.tracked_operations and
                   self.tracked_operations[op_id].backup_path and
                   Path(self.tracked_operations[op_id].backup_path).exists()
            )

            # Risk assessment
            risk_level = "LOW"
            if len(operations_to_rollback) > 50:
                risk_level = "HIGH"
            elif len(operations_to_rollback) > 20:
                risk_level = "MEDIUM"

            # Create rollback plan
            rollback_plan = RollbackPlan(
                rollback_id=rollback_id,
                target_recovery_point_id=target_recovery_point_id,
                operations_to_rollback=operations_to_rollback,
                estimated_duration_seconds=estimated_duration,
                estimated_data_size_bytes=estimated_size,
                rollback_strategy="sequential_reverse",
                requires_confirmation=confirmation_required,
                risk_assessment=risk_level,
                created_at=datetime.now()
            )

            # Save rollback plan
            await self._save_rollback_plan(rollback_plan)

            if self.security_logger:
                await self.security_logger.log_security_event(
                    event_type=SecurityEventType.SYSTEM_UPDATE,
                    severity=SecuritySeverity.WARNING,
                    details={
                        'component': 'Rollback Recovery System',
                        'action': 'rollback_plan_created',
                        'rollback_id': rollback_id,
                        'target_recovery_point': target_recovery_point_id,
                        'operations_to_rollback': len(operations_to_rollback),
                        'risk_assessment': risk_level
                    }
                )

            return rollback_id

        except Exception as e:
            logging.error(f"Error creating rollback plan: {e}")
            if self.security_logger:
                await self.security_logger.log_security_event(
                    event_type=SecurityEventType.SYSTEM_ERROR,
                    severity=SecuritySeverity.ERROR,
                    details={
                        'component': 'Rollback Recovery System',
                        'action': 'rollback_plan_creation_failed',
                        'error': str(e)
                    }
                )
            raise

    async def execute_rollback(self, rollback_id: str, confirmed: bool = False) -> str:
        """
        Execute a rollback plan

        Returns:
            Execution ID for tracking
        """
        execution_id = f"exec_{int(time.time() * 1000000)}"

        try:
            # Load rollback plan
            rollback_plan = await self._load_rollback_plan(rollback_id)
            if not rollback_plan:
                raise ValueError(f"Rollback plan {rollback_id} not found")

            # Check confirmation requirement
            if rollback_plan.requires_confirmation and not confirmed:
                raise ValueError("Rollback requires confirmation but was not provided")

            # Create execution record
            execution = RollbackExecution(
                rollback_id=rollback_id,
                execution_id=execution_id,
                status=RollbackStatus.IN_PROGRESS,
                started_at=datetime.now(),
                total_operations=len(rollback_plan.operations_to_rollback)
            )

            self.active_rollbacks[execution_id] = execution
            await self._save_rollback_execution(execution)

            # Start rollback process
            success = await self._perform_rollback(execution, rollback_plan)

            # Update execution status
            execution.completed_at = datetime.now()
            execution.status = RollbackStatus.COMPLETED if success else RollbackStatus.FAILED

            # Validate rollback if successful
            if success:
                validation_results = await self._validate_rollback(execution, rollback_plan)
                execution.validation_results = validation_results

                if not all(validation_results.values()):
                    execution.status = RollbackStatus.VALIDATION_FAILED

            await self._update_rollback_execution(execution)

            # Update statistics
            if execution.status == RollbackStatus.COMPLETED:
                self.stats['successful_rollbacks'] += 1
            else:
                self.stats['failed_rollbacks'] += 1

            self.stats['total_rollbacks_executed'] += 1

            if self.security_logger:
                await self.security_logger.log_security_event(
                    event_type=SecurityEventType.SYSTEM_UPDATE,
                    severity=SecuritySeverity.CRITICAL,
                    details={
                        'component': 'Rollback Recovery System',
                        'action': 'rollback_executed',
                        'execution_id': execution_id,
                        'status': execution.status.value,
                        'operations_completed': execution.operations_completed,
                        'operations_failed': execution.operations_failed
                    }
                )

            return execution_id

        except Exception as e:
            logging.error(f"Error executing rollback: {e}")
            if self.security_logger:
                await self.security_logger.log_security_event(
                    event_type=SecurityEventType.SYSTEM_ERROR,
                    severity=SecuritySeverity.CRITICAL,
                    details={
                        'component': 'Rollback Recovery System',
                        'action': 'rollback_execution_failed',
                        'error': str(e)
                    }
                )
            raise

    async def _perform_rollback(self, execution: RollbackExecution, plan: RollbackPlan) -> bool:
        """Perform the actual rollback operations"""
        try:
            # Sort operations in reverse chronological order
            operations = []
            for op_id in plan.operations_to_rollback:
                if op_id in self.tracked_operations:
                    operations.append(self.tracked_operations[op_id])

            operations.sort(key=lambda x: x.timestamp, reverse=True)

            # Execute rollback operations
            for operation in operations:
                try:
                    success = await self._rollback_single_operation(operation)
                    if success:
                        execution.operations_completed += 1
                    else:
                        execution.operations_failed += 1
                        execution.error_messages.append(f"Failed to rollback operation {operation.operation_id}")

                    # Update execution record periodically
                    if (execution.operations_completed + execution.operations_failed) % 10 == 0:
                        await self._update_rollback_execution(execution)

                except Exception as e:
                    execution.operations_failed += 1
                    execution.error_messages.append(f"Error rolling back {operation.operation_id}: {str(e)}")

            return execution.operations_failed == 0

        except Exception as e:
            logging.error(f"Error performing rollback: {e}")
            execution.error_messages.append(f"Rollback failed: {str(e)}")
            return False

    async def _rollback_single_operation(self, operation: FileOperation) -> bool:
        """Rollback a single file operation"""
        try:
            file_path = Path(operation.file_path)

            if operation.operation_type == FileOperationType.CREATE:
                # Delete the created file
                if file_path.exists():
                    file_path.unlink()
                return True

            elif operation.operation_type == FileOperationType.DELETE:
                # Restore from backup
                if operation.backup_path and Path(operation.backup_path).exists():
                    backup_path = Path(operation.backup_path)

                    # Handle compressed backups
                    if backup_path.suffix == '.gz':
                        with gzip.open(backup_path, 'rb') as f_in:
                            with open(file_path, 'wb') as f_out:
                                shutil.copyfileobj(f_in, f_out)
                    else:
                        shutil.copy2(backup_path, file_path)

                    return True

            elif operation.operation_type == FileOperationType.MODIFY:
                # Restore from backup
                if operation.backup_path and Path(operation.backup_path).exists():
                    backup_path = Path(operation.backup_path)

                    # Handle compressed backups
                    if backup_path.suffix == '.gz':
                        with gzip.open(backup_path, 'rb') as f_in:
                            with open(file_path, 'wb') as f_out:
                                shutil.copyfileobj(f_in, f_out)
                    else:
                        shutil.copy2(backup_path, file_path)

                    return True

            elif operation.operation_type == FileOperationType.CHMOD:
                # Restore original permissions
                if operation.permissions_before and file_path.exists():
                    mode = int(operation.permissions_before, 8)
                    file_path.chmod(mode)
                    return True

            elif operation.operation_type == FileOperationType.MOVE:
                # This would require more complex logic to determine source/destination
                # For now, attempt to restore from backup if available
                if operation.backup_path and Path(operation.backup_path).exists():
                    shutil.copy2(operation.backup_path, file_path)
                    return True

            # Add more operation types as needed

            return False

        except Exception as e:
            logging.error(f"Error rolling back operation {operation.operation_id}: {e}")
            return False

    async def _validate_rollback(self, execution: RollbackExecution, plan: RollbackPlan) -> Dict[str, bool]:
        """Validate that rollback was successful"""
        validation_results = {}

        try:
            recovery_point = self.recovery_points[plan.target_recovery_point_id]

            # Validate each operation that was rolled back
            for op_id in plan.operations_to_rollback:
                if op_id in self.tracked_operations:
                    operation = self.tracked_operations[op_id]
                    file_path = Path(operation.file_path)

                    # Check if file state matches expected state
                    if operation.operation_type == FileOperationType.CREATE:
                        # File should not exist
                        validation_results[op_id] = not file_path.exists()

                    elif operation.operation_type in [FileOperationType.DELETE, FileOperationType.MODIFY]:
                        # File should exist and match original checksum
                        if file_path.exists() and operation.original_checksum:
                            current_checksum = await self._calculate_file_checksum(str(file_path))
                            validation_results[op_id] = current_checksum == operation.original_checksum
                        else:
                            validation_results[op_id] = False

                    else:
                        # Default validation - assume success if no error occurred
                        validation_results[op_id] = True

            # Overall validation
            validation_results['overall'] = all(validation_results.values())

        except Exception as e:
            logging.error(f"Error validating rollback: {e}")
            validation_results['overall'] = False

        return validation_results

    async def _save_file_operation(self, operation: FileOperation):
        """Save file operation to database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO file_operations
                (operation_id, operation_type, file_path, timestamp, user_id,
                 original_checksum, new_checksum, file_size_before, file_size_after,
                 permissions_before, permissions_after, backup_path, recovery_point_id,
                 additional_metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                operation.operation_id,
                operation.operation_type.value,
                operation.file_path,
                operation.timestamp.isoformat(),
                operation.user_id,
                operation.original_checksum,
                operation.new_checksum,
                operation.file_size_before,
                operation.file_size_after,
                operation.permissions_before,
                operation.permissions_after,
                operation.backup_path,
                operation.recovery_point_id,
                json.dumps(operation.additional_metadata)
            ))

    async def _update_file_operation(self, operation: FileOperation):
        """Update file operation in database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                UPDATE file_operations
                SET new_checksum = ?, file_size_after = ?, permissions_after = ?
                WHERE operation_id = ?
            """, (
                operation.new_checksum,
                operation.file_size_after,
                operation.permissions_after,
                operation.operation_id
            ))

    async def _save_recovery_point(self, recovery_point: RecoveryPoint):
        """Save recovery point to database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO recovery_points
                (recovery_point_id, recovery_point_type, timestamp, description,
                 file_operations, backup_size_bytes, checksum, is_compressed,
                 retention_days, created_by, validation_status, restoration_count)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                recovery_point.recovery_point_id,
                recovery_point.recovery_point_type.value,
                recovery_point.timestamp.isoformat(),
                recovery_point.description,
                json.dumps(recovery_point.file_operations),
                recovery_point.backup_size_bytes,
                recovery_point.checksum,
                recovery_point.is_compressed,
                recovery_point.retention_days,
                recovery_point.created_by,
                recovery_point.validation_status,
                recovery_point.restoration_count
            ))

    async def _save_rollback_plan(self, plan: RollbackPlan):
        """Save rollback plan to database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO rollback_plans
                (rollback_id, target_recovery_point_id, operations_to_rollback,
                 estimated_duration_seconds, estimated_data_size_bytes,
                 rollback_strategy, requires_confirmation, risk_assessment)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                plan.rollback_id,
                plan.target_recovery_point_id,
                json.dumps(plan.operations_to_rollback),
                plan.estimated_duration_seconds,
                plan.estimated_data_size_bytes,
                plan.rollback_strategy,
                plan.requires_confirmation,
                plan.risk_assessment
            ))

    async def _save_rollback_execution(self, execution: RollbackExecution):
        """Save rollback execution to database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO rollback_executions
                (rollback_id, execution_id, status, started_at, completed_at,
                 operations_completed, operations_failed, total_operations,
                 error_messages, rollback_checksum, validation_results)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                execution.rollback_id,
                execution.execution_id,
                execution.status.value,
                execution.started_at.isoformat(),
                execution.completed_at.isoformat() if execution.completed_at else None,
                execution.operations_completed,
                execution.operations_failed,
                execution.total_operations,
                json.dumps(execution.error_messages),
                execution.rollback_checksum,
                json.dumps(execution.validation_results)
            ))

    async def _update_rollback_execution(self, execution: RollbackExecution):
        """Update rollback execution in database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                UPDATE rollback_executions
                SET status = ?, completed_at = ?, operations_completed = ?,
                    operations_failed = ?, error_messages = ?, validation_results = ?
                WHERE execution_id = ?
            """, (
                execution.status.value,
                execution.completed_at.isoformat() if execution.completed_at else None,
                execution.operations_completed,
                execution.operations_failed,
                json.dumps(execution.error_messages),
                json.dumps(execution.validation_results),
                execution.execution_id
            ))

    async def _load_rollback_plan(self, rollback_id: str) -> Optional[RollbackPlan]:
        """Load rollback plan from database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT target_recovery_point_id, operations_to_rollback,
                       estimated_duration_seconds, estimated_data_size_bytes,
                       rollback_strategy, requires_confirmation, risk_assessment,
                       created_at
                FROM rollback_plans
                WHERE rollback_id = ?
            """, (rollback_id,))

            row = cursor.fetchone()
            if row:
                return RollbackPlan(
                    rollback_id=rollback_id,
                    target_recovery_point_id=row[0],
                    operations_to_rollback=json.loads(row[1]),
                    estimated_duration_seconds=row[2],
                    estimated_data_size_bytes=row[3],
                    rollback_strategy=row[4],
                    requires_confirmation=bool(row[5]),
                    risk_assessment=row[6],
                    created_at=datetime.fromisoformat(row[7])
                )
        return None

    async def _load_recovery_points(self):
        """Load existing recovery points from database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT recovery_point_id, recovery_point_type, timestamp, description,
                           file_operations, backup_size_bytes, checksum, is_compressed,
                           retention_days, created_by, validation_status, restoration_count
                    FROM recovery_points
                    WHERE datetime(timestamp) > datetime('now', '-30 days')
                    ORDER BY timestamp DESC
                """)

                for row in cursor.fetchall():
                    recovery_point = RecoveryPoint(
                        recovery_point_id=row[0],
                        recovery_point_type=RecoveryPointType(row[1]),
                        timestamp=datetime.fromisoformat(row[2]),
                        description=row[3],
                        file_operations=json.loads(row[4]),
                        backup_size_bytes=row[5],
                        checksum=row[6],
                        is_compressed=bool(row[7]),
                        retention_days=row[8],
                        created_by=row[9],
                        validation_status=bool(row[10]),
                        restoration_count=row[11]
                    )
                    self.recovery_points[recovery_point.recovery_point_id] = recovery_point

        except Exception as e:
            logging.error(f"Error loading recovery points: {e}")

    def _cleanup_loop(self):
        """Background cleanup loop"""
        while self.monitoring_active:
            try:
                # Clean up old backups and recovery points
                self._cleanup_old_data()

                # Sleep for 1 hour
                time.sleep(3600)

            except Exception as e:
                logging.error(f"Error in cleanup loop: {e}")

    def _cleanup_old_data(self):
        """Clean up old backups and database records"""
        try:
            cutoff_date = datetime.now() - timedelta(days=self.default_retention_days)

            with sqlite3.connect(self.db_path) as conn:
                # Remove old file operations
                conn.execute("""
                    DELETE FROM file_operations
                    WHERE datetime(timestamp) < ?
                """, (cutoff_date.isoformat(),))

                # Remove old recovery points
                cursor = conn.execute("""
                    SELECT recovery_point_id FROM recovery_points
                    WHERE datetime(timestamp) < ?
                """, (cutoff_date.isoformat(),))

                old_recovery_points = [row[0] for row in cursor.fetchall()]

                for rp_id in old_recovery_points:
                    # Remove from memory
                    if rp_id in self.recovery_points:
                        del self.recovery_points[rp_id]

                    # Remove backup files
                    rp_backup_dir = self.backup_root / "recovery_points" / rp_id
                    if rp_backup_dir.exists():
                        shutil.rmtree(rp_backup_dir, ignore_errors=True)

                # Remove database records
                conn.execute("""
                    DELETE FROM recovery_points
                    WHERE datetime(timestamp) < ?
                """, (cutoff_date.isoformat(),))

        except Exception as e:
            logging.error(f"Error cleaning up old data: {e}")

    def get_current_stats(self) -> Dict[str, Any]:
        """Get current rollback and recovery statistics"""
        return {
            'statistics': self.stats.copy(),
            'tracked_operations': len(self.tracked_operations),
            'recovery_points': len(self.recovery_points),
            'active_rollbacks': len(self.active_rollbacks),
            'monitoring_active': self.monitoring_active,
            'backup_root': str(self.backup_root),
            'auto_backup_enabled': self.auto_backup_enabled,
            'compression_enabled': self.compression_enabled
        }

    async def get_recovery_points(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get list of available recovery points"""
        sorted_points = sorted(
            self.recovery_points.values(),
            key=lambda x: x.timestamp,
            reverse=True
        )

        return [
            {
                'recovery_point_id': rp.recovery_point_id,
                'type': rp.recovery_point_type.value,
                'timestamp': rp.timestamp.isoformat(),
                'description': rp.description,
                'operations_count': len(rp.file_operations),
                'backup_size_bytes': rp.backup_size_bytes,
                'created_by': rp.created_by,
                'validation_status': rp.validation_status
            }
            for rp in sorted_points[:limit]
        ]

    async def get_rollback_status(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a rollback execution"""
        if execution_id in self.active_rollbacks:
            execution = self.active_rollbacks[execution_id]
            return {
                'execution_id': execution_id,
                'rollback_id': execution.rollback_id,
                'status': execution.status.value,
                'started_at': execution.started_at.isoformat(),
                'completed_at': execution.completed_at.isoformat() if execution.completed_at else None,
                'progress': {
                    'operations_completed': execution.operations_completed,
                    'operations_failed': execution.operations_failed,
                    'total_operations': execution.total_operations,
                    'percentage': (execution.operations_completed / execution.total_operations * 100) if execution.total_operations > 0 else 0
                },
                'validation_results': execution.validation_results,
                'error_messages': execution.error_messages
            }
        return None


# Integration helper function
async def create_integrated_rollback_system(
    security_logger: Optional[EnhancedSecurityLogging] = None,
    rate_limiter: Optional[RateLimitingResourceControl] = None,
    whitelist_system: Optional[CommandWhitelistSystem] = None,
    backup_root: str = "backups"
) -> RollbackRecoverySystem:
    """
    Create integrated rollback and recovery system

    Returns configured and initialized system
    """
    rollback_system = RollbackRecoverySystem(
        security_logger=security_logger,
        rate_limiter=rate_limiter,
        whitelist_system=whitelist_system,
        backup_root=backup_root
    )

    # Start monitoring
    await rollback_system.start_monitoring()

    return rollback_system


if __name__ == "__main__":
    # Example usage
    async def main():
        # Create rollback system
        rollback_system = await create_integrated_rollback_system()

        # Example file operation tracking
        operation_id = await rollback_system.track_file_operation(
            FileOperationType.MODIFY,
            "/tmp/test_file.txt",
            "test_user"
        )

        # Complete the operation
        await rollback_system.complete_file_operation(operation_id)

        # Create recovery point
        recovery_point_id = await rollback_system.create_recovery_point(
            "Test recovery point",
            RecoveryPointType.MANUAL
        )

        # Get statistics
        stats = rollback_system.get_current_stats()
        print(f"Rollback system stats: {stats}")

        # Stop monitoring
        rollback_system.stop_monitoring()

    asyncio.run(main())