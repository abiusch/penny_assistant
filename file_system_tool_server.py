"""
File System Tool Server
Provides secure file operations with comprehensive rollback capabilities
"""

import asyncio
import json
import os
import shutil
import tempfile
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
import aiosqlite
import aiofiles

from tool_server_foundation import (
    BaseToolServer, ToolServerType, SecurityLevel, SecurityContext,
    ToolOperation, ToolOperationResult, ToolServerSecurityError
)


class FileSystemToolServer(BaseToolServer):
    """File system tool server with rollback integration"""

    def __init__(self, *args, **kwargs):
        super().__init__(ToolServerType.FILE_SYSTEM, *args, **kwargs)

        # File operation configuration
        self.allowed_extensions = {'.txt', '.json', '.py', '.md', '.yaml', '.yml', '.csv'}
        self.blocked_paths = {'/etc', '/usr', '/bin', '/sbin', '/var/log', '/proc', '/sys'}
        self.max_file_size = 100 * 1024 * 1024  # 100MB
        self.rollback_retention_days = 30

        # Sandboxed directory for operations
        self.sandbox_root = Path("./file_operations_sandbox")
        self.rollback_storage = Path("./rollback_storage")

    async def _load_configuration(self):
        """Load file system specific configuration"""
        # Ensure sandbox directories exist
        self.sandbox_root.mkdir(exist_ok=True)
        self.rollback_storage.mkdir(exist_ok=True)

        # Create subdirectories for rollback storage
        (self.rollback_storage / "files").mkdir(exist_ok=True)
        (self.rollback_storage / "metadata").mkdir(exist_ok=True)

    async def _execute_specific_operation(self,
                                        operation_name: str,
                                        parameters: Dict[str, Any],
                                        security_context: SecurityContext) -> Dict[str, Any]:
        """Execute file system specific operations"""

        operation_map = {
            "read_file": self._read_file,
            "write_file": self._write_file,
            "create_file": self._create_file,
            "delete_file": self._delete_file,
            "copy_file": self._copy_file,
            "move_file": self._move_file,
            "list_directory": self._list_directory,
            "create_directory": self._create_directory,
            "delete_directory": self._delete_directory,
            "get_file_info": self._get_file_info,
            "search_files": self._search_files,
            "calculate_checksum": self._calculate_checksum
        }

        if operation_name not in operation_map:
            raise ValueError(f"Unknown file operation: {operation_name}")

        return await operation_map[operation_name](parameters, security_context)

    async def _determine_security_level(self, operation_name: str, parameters: Dict[str, Any]) -> SecurityLevel:
        """Determine security level for file operations"""

        # High-risk operations
        if operation_name in ["delete_file", "delete_directory", "move_file"]:
            return SecurityLevel.HIGH

        # Write operations
        if operation_name in ["write_file", "create_file", "copy_file", "create_directory"]:
            return SecurityLevel.MEDIUM

        # Read operations
        if operation_name in ["read_file", "list_directory", "get_file_info", "search_files", "calculate_checksum"]:
            return SecurityLevel.LOW

        return SecurityLevel.MEDIUM

    async def _requires_rollback(self, operation_name: str) -> bool:
        """Check if operation requires rollback capability"""
        rollback_operations = {
            "write_file", "create_file", "delete_file", "copy_file",
            "move_file", "create_directory", "delete_directory"
        }
        return operation_name in rollback_operations

    async def _create_rollback_data(self, operation: ToolOperation, result_data: Dict[str, Any]) -> str:
        """Create rollback data for file operations"""
        rollback_id = f"rb_{operation.operation_id}_{int(datetime.now().timestamp())}"

        rollback_info = {
            "rollback_id": rollback_id,
            "operation_id": operation.operation_id,
            "operation_name": operation.operation_name,
            "parameters": operation.parameters,
            "timestamp": datetime.now().isoformat(),
            "expires_at": (datetime.now() + timedelta(days=self.rollback_retention_days)).isoformat()
        }

        # Store operation-specific rollback data
        if operation.operation_name in ["write_file", "create_file"]:
            # Store previous file content or note file didn't exist
            file_path = self._validate_path(operation.parameters.get("path"))
            if file_path.exists():
                rollback_file_path = self.rollback_storage / "files" / f"{rollback_id}_original"
                shutil.copy2(file_path, rollback_file_path)
                rollback_info["rollback_type"] = "restore_file"
                rollback_info["original_file"] = str(rollback_file_path)
            else:
                rollback_info["rollback_type"] = "delete_created_file"

        elif operation.operation_name == "delete_file":
            # Store deleted file
            file_path = self._validate_path(operation.parameters.get("path"))
            if file_path.exists():
                rollback_file_path = self.rollback_storage / "files" / f"{rollback_id}_deleted"
                shutil.copy2(file_path, rollback_file_path)
                rollback_info["rollback_type"] = "restore_deleted_file"
                rollback_info["deleted_file"] = str(rollback_file_path)
                rollback_info["original_path"] = str(file_path)

        elif operation.operation_name == "move_file":
            # Store original location
            rollback_info["rollback_type"] = "restore_file_location"
            rollback_info["original_path"] = operation.parameters.get("source_path")
            rollback_info["moved_path"] = operation.parameters.get("destination_path")

        elif operation.operation_name == "copy_file":
            # Store destination path for deletion
            rollback_info["rollback_type"] = "delete_copied_file"
            rollback_info["copied_path"] = operation.parameters.get("destination_path")

        elif operation.operation_name == "create_directory":
            # Store directory path for deletion
            rollback_info["rollback_type"] = "delete_created_directory"
            rollback_info["created_path"] = operation.parameters.get("path")

        elif operation.operation_name == "delete_directory":
            # Store entire directory structure
            dir_path = self._validate_path(operation.parameters.get("path"))
            if dir_path.exists():
                rollback_dir_path = self.rollback_storage / "files" / f"{rollback_id}_deleted_dir"
                shutil.copytree(dir_path, rollback_dir_path)
                rollback_info["rollback_type"] = "restore_deleted_directory"
                rollback_info["deleted_directory"] = str(rollback_dir_path)
                rollback_info["original_path"] = str(dir_path)

        # Store rollback metadata
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
        """Execute rollback operation"""
        try:
            if rollback_type == "restore_file":
                # Restore original file content
                original_file = Path(rollback_data["original_file"])
                target_path = self._validate_path(rollback_data["parameters"]["path"])
                if original_file.exists():
                    shutil.copy2(original_file, target_path)
                    return True

            elif rollback_type == "delete_created_file":
                # Delete the created file
                target_path = self._validate_path(rollback_data["parameters"]["path"])
                if target_path.exists():
                    target_path.unlink()
                    return True

            elif rollback_type == "restore_deleted_file":
                # Restore deleted file
                deleted_file = Path(rollback_data["deleted_file"])
                target_path = Path(rollback_data["original_path"])
                if deleted_file.exists():
                    shutil.copy2(deleted_file, target_path)
                    return True

            elif rollback_type == "restore_file_location":
                # Move file back to original location
                moved_path = Path(rollback_data["moved_path"])
                original_path = Path(rollback_data["original_path"])
                if moved_path.exists():
                    shutil.move(str(moved_path), str(original_path))
                    return True

            elif rollback_type == "delete_copied_file":
                # Delete the copied file
                copied_path = Path(rollback_data["copied_path"])
                if copied_path.exists():
                    copied_path.unlink()
                    return True

            elif rollback_type == "delete_created_directory":
                # Delete the created directory
                created_path = Path(rollback_data["created_path"])
                if created_path.exists():
                    shutil.rmtree(created_path)
                    return True

            elif rollback_type == "restore_deleted_directory":
                # Restore deleted directory
                deleted_dir = Path(rollback_data["deleted_directory"])
                target_path = Path(rollback_data["original_path"])
                if deleted_dir.exists():
                    shutil.copytree(deleted_dir, target_path)
                    return True

            return False

        except Exception as e:
            self.logger.error(f"Rollback execution failed: {e}")
            return False

    def _validate_path(self, path_str: str) -> Path:
        """Validate and secure file path"""
        if not path_str:
            raise ToolServerSecurityError("Path cannot be empty")

        path = Path(path_str).resolve()

        # Check for blocked paths
        for blocked in self.blocked_paths:
            if str(path).startswith(blocked):
                raise ToolServerSecurityError(f"Access to {blocked} is blocked")

        # Ensure path is within sandbox if not absolute trusted path
        if not path.is_absolute() or not any(str(path).startswith(trusted) for trusted in ["/tmp", str(self.sandbox_root)]):
            # Resolve relative to sandbox
            path = (self.sandbox_root / path_str).resolve()

        return path

    def _validate_file_extension(self, path: Path):
        """Validate file extension"""
        if path.suffix.lower() not in self.allowed_extensions:
            raise ToolServerSecurityError(f"File extension {path.suffix} not allowed")

    async def _read_file(self, parameters: Dict[str, Any], security_context: SecurityContext) -> Dict[str, Any]:
        """Read file content"""
        file_path = self._validate_path(parameters.get("path", ""))

        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        if file_path.stat().st_size > self.max_file_size:
            raise ToolServerSecurityError(f"File too large: {file_path.stat().st_size} bytes")

        self._validate_file_extension(file_path)

        async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
            content = await f.read()

        return {
            "path": str(file_path),
            "content": content,
            "size": file_path.stat().st_size,
            "modified": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
        }

    async def _write_file(self, parameters: Dict[str, Any], security_context: SecurityContext) -> Dict[str, Any]:
        """Write content to file"""
        file_path = self._validate_path(parameters.get("path", ""))
        content = parameters.get("content", "")

        if len(content.encode('utf-8')) > self.max_file_size:
            raise ToolServerSecurityError(f"Content too large: {len(content)} bytes")

        self._validate_file_extension(file_path)

        # Ensure parent directory exists
        file_path.parent.mkdir(parents=True, exist_ok=True)

        async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
            await f.write(content)

        return {
            "path": str(file_path),
            "size": file_path.stat().st_size,
            "operation": "write_complete"
        }

    async def _create_file(self, parameters: Dict[str, Any], security_context: SecurityContext) -> Dict[str, Any]:
        """Create new file"""
        file_path = self._validate_path(parameters.get("path", ""))
        content = parameters.get("content", "")

        if file_path.exists():
            raise FileExistsError(f"File already exists: {file_path}")

        return await self._write_file(parameters, security_context)

    async def _delete_file(self, parameters: Dict[str, Any], security_context: SecurityContext) -> Dict[str, Any]:
        """Delete file"""
        file_path = self._validate_path(parameters.get("path", ""))

        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        if not file_path.is_file():
            raise ToolServerSecurityError(f"Not a file: {file_path}")

        file_size = file_path.stat().st_size
        file_path.unlink()

        return {
            "path": str(file_path),
            "operation": "delete_complete",
            "size_deleted": file_size
        }

    async def _copy_file(self, parameters: Dict[str, Any], security_context: SecurityContext) -> Dict[str, Any]:
        """Copy file"""
        source_path = self._validate_path(parameters.get("source_path", ""))
        dest_path = self._validate_path(parameters.get("destination_path", ""))

        if not source_path.exists():
            raise FileNotFoundError(f"Source file not found: {source_path}")

        if dest_path.exists() and not parameters.get("overwrite", False):
            raise FileExistsError(f"Destination file exists: {dest_path}")

        self._validate_file_extension(source_path)
        self._validate_file_extension(dest_path)

        # Ensure destination directory exists
        dest_path.parent.mkdir(parents=True, exist_ok=True)

        shutil.copy2(source_path, dest_path)

        return {
            "source_path": str(source_path),
            "destination_path": str(dest_path),
            "operation": "copy_complete",
            "size": dest_path.stat().st_size
        }

    async def _move_file(self, parameters: Dict[str, Any], security_context: SecurityContext) -> Dict[str, Any]:
        """Move file"""
        source_path = self._validate_path(parameters.get("source_path", ""))
        dest_path = self._validate_path(parameters.get("destination_path", ""))

        if not source_path.exists():
            raise FileNotFoundError(f"Source file not found: {source_path}")

        if dest_path.exists() and not parameters.get("overwrite", False):
            raise FileExistsError(f"Destination file exists: {dest_path}")

        self._validate_file_extension(source_path)
        self._validate_file_extension(dest_path)

        # Ensure destination directory exists
        dest_path.parent.mkdir(parents=True, exist_ok=True)

        shutil.move(str(source_path), str(dest_path))

        return {
            "source_path": str(source_path),
            "destination_path": str(dest_path),
            "operation": "move_complete"
        }

    async def _list_directory(self, parameters: Dict[str, Any], security_context: SecurityContext) -> Dict[str, Any]:
        """List directory contents"""
        dir_path = self._validate_path(parameters.get("path", "."))

        if not dir_path.exists():
            raise FileNotFoundError(f"Directory not found: {dir_path}")

        if not dir_path.is_dir():
            raise ToolServerSecurityError(f"Not a directory: {dir_path}")

        files = []
        directories = []

        for item in dir_path.iterdir():
            item_info = {
                "name": item.name,
                "path": str(item),
                "size": item.stat().st_size if item.is_file() else 0,
                "modified": datetime.fromtimestamp(item.stat().st_mtime).isoformat(),
                "permissions": oct(item.stat().st_mode)[-3:]
            }

            if item.is_file():
                files.append(item_info)
            elif item.is_dir():
                directories.append(item_info)

        return {
            "path": str(dir_path),
            "files": sorted(files, key=lambda x: x["name"]),
            "directories": sorted(directories, key=lambda x: x["name"]),
            "total_files": len(files),
            "total_directories": len(directories)
        }

    async def _create_directory(self, parameters: Dict[str, Any], security_context: SecurityContext) -> Dict[str, Any]:
        """Create directory"""
        dir_path = self._validate_path(parameters.get("path", ""))

        if dir_path.exists():
            raise FileExistsError(f"Directory already exists: {dir_path}")

        dir_path.mkdir(parents=parameters.get("create_parents", True), exist_ok=False)

        return {
            "path": str(dir_path),
            "operation": "create_directory_complete"
        }

    async def _delete_directory(self, parameters: Dict[str, Any], security_context: SecurityContext) -> Dict[str, Any]:
        """Delete directory"""
        dir_path = self._validate_path(parameters.get("path", ""))

        if not dir_path.exists():
            raise FileNotFoundError(f"Directory not found: {dir_path}")

        if not dir_path.is_dir():
            raise ToolServerSecurityError(f"Not a directory: {dir_path}")

        # Count items before deletion
        total_files = sum(1 for item in dir_path.rglob("*") if item.is_file())
        total_dirs = sum(1 for item in dir_path.rglob("*") if item.is_dir())

        shutil.rmtree(dir_path)

        return {
            "path": str(dir_path),
            "operation": "delete_directory_complete",
            "files_deleted": total_files,
            "directories_deleted": total_dirs
        }

    async def _get_file_info(self, parameters: Dict[str, Any], security_context: SecurityContext) -> Dict[str, Any]:
        """Get file information"""
        file_path = self._validate_path(parameters.get("path", ""))

        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        stat = file_path.stat()

        return {
            "path": str(file_path),
            "name": file_path.name,
            "size": stat.st_size,
            "type": "file" if file_path.is_file() else "directory",
            "extension": file_path.suffix,
            "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            "permissions": oct(stat.st_mode)[-3:],
            "is_readable": os.access(file_path, os.R_OK),
            "is_writable": os.access(file_path, os.W_OK)
        }

    async def _search_files(self, parameters: Dict[str, Any], security_context: SecurityContext) -> Dict[str, Any]:
        """Search for files"""
        search_path = self._validate_path(parameters.get("path", "."))
        pattern = parameters.get("pattern", "*")
        recursive = parameters.get("recursive", False)
        max_results = min(parameters.get("max_results", 100), 1000)  # Cap at 1000

        if not search_path.exists():
            raise FileNotFoundError(f"Search path not found: {search_path}")

        results = []
        search_method = search_path.rglob if recursive else search_path.glob

        for item in search_method(pattern):
            if len(results) >= max_results:
                break

            if item.is_file():
                results.append({
                    "path": str(item),
                    "name": item.name,
                    "size": item.stat().st_size,
                    "modified": datetime.fromtimestamp(item.stat().st_mtime).isoformat(),
                    "extension": item.suffix
                })

        return {
            "search_path": str(search_path),
            "pattern": pattern,
            "recursive": recursive,
            "results": results,
            "total_found": len(results),
            "truncated": len(results) >= max_results
        }

    async def _calculate_checksum(self, parameters: Dict[str, Any], security_context: SecurityContext) -> Dict[str, Any]:
        """Calculate file checksum"""
        file_path = self._validate_path(parameters.get("path", ""))
        algorithm = parameters.get("algorithm", "sha256").lower()

        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        if not file_path.is_file():
            raise ToolServerSecurityError(f"Not a file: {file_path}")

        if algorithm not in ["md5", "sha1", "sha256", "sha512"]:
            raise ValueError(f"Unsupported algorithm: {algorithm}")

        hash_obj = hashlib.new(algorithm)

        async with aiofiles.open(file_path, 'rb') as f:
            while chunk := await f.read(8192):
                hash_obj.update(chunk)

        return {
            "path": str(file_path),
            "algorithm": algorithm,
            "checksum": hash_obj.hexdigest(),
            "file_size": file_path.stat().st_size
        }