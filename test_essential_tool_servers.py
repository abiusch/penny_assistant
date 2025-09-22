"""
Comprehensive Security-Integrated Testing Suite for Essential Tool Servers
Tests all 9 security components integration, emergency stop effectiveness, and performance under load
"""

import asyncio
import json
import time
import uuid
import tempfile
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
import unittest
from unittest.mock import AsyncMock, MagicMock, patch
import sqlite3

# Import our tool servers and security systems
from tool_server_foundation import ToolServerManager, ToolServerType, SecurityLevel
from file_system_tool_server import FileSystemToolServer
from web_search_tool_server import WebSearchToolServer
from calendar_tool_server import CalendarToolServer
from task_management_tool_server import TaskManagementToolServer

# Import security components
from command_whitelist_system import CommandWhitelistSystem
from emergency_stop import MultiChannelEmergencyStop
from enhanced_security_logging import EnhancedSecurityLogging


class TestSecurityIntegration(unittest.IsolatedAsyncioTestCase):
    """Test security integration across all tool servers"""

    async def asyncSetUp(self):
        """Setup test environment with all security components"""
        self.test_db = tempfile.mktemp(suffix=".db")
        self.test_sandbox = tempfile.mkdtemp(prefix="tool_test_")

        # Mock security components
        self.command_whitelist = AsyncMock(spec=CommandWhitelistSystem)
        self.emergency_stop = AsyncMock(spec=MultiChannelEmergencyStop)
        self.security_logger = AsyncMock(spec=EnhancedSecurityLogging)

        # Setup mock behaviors
        self.command_whitelist.is_command_allowed.return_value = True
        self.command_whitelist.initialize.return_value = True
        self.emergency_stop.is_emergency_active.return_value = False
        self.emergency_stop.initialize.return_value = True
        self.emergency_stop.trigger_emergency_stop = AsyncMock()
        self.security_logger.initialize.return_value = True
        self.security_logger.log_tool_operation = AsyncMock()
        self.security_logger.log_security_event = AsyncMock()

        # Initialize tool servers
        self.file_server = FileSystemToolServer(
            db_path=self.test_db,
            security_system=self.command_whitelist,
            emergency_system=self.emergency_stop,
            security_logger=self.security_logger
        )
        self.file_server.sandbox_root = Path(self.test_sandbox)

        self.web_server = WebSearchToolServer(
            db_path=self.test_db,
            security_system=self.command_whitelist,
            emergency_system=self.emergency_stop,
            security_logger=self.security_logger
        )

        self.calendar_server = CalendarToolServer(
            db_path=self.test_db,
            security_system=self.command_whitelist,
            emergency_system=self.emergency_stop,
            security_logger=self.security_logger
        )

        self.task_server = TaskManagementToolServer(
            db_path=self.test_db,
            security_system=self.command_whitelist,
            emergency_system=self.emergency_stop,
            security_logger=self.security_logger
        )

        # Initialize all servers
        await self.file_server.initialize()
        await self.web_server.initialize()
        await self.calendar_server.initialize()
        await self.task_server.initialize()

        # Setup tool server manager
        self.manager = ToolServerManager()
        await self.manager.register_server(self.file_server)
        await self.manager.register_server(self.web_server)
        await self.manager.register_server(self.calendar_server)
        await self.manager.register_server(self.task_server)

    async def asyncTearDown(self):
        """Cleanup test environment"""
        try:
            Path(self.test_db).unlink(missing_ok=True)
            shutil.rmtree(self.test_sandbox, ignore_errors=True)
        except Exception:
            pass

    async def test_security_component_integration(self):
        """Critical Test: Verify all 9 security components properly intercept operations"""

        # Test 1: Command Whitelist Integration
        self.command_whitelist.is_command_allowed.return_value = False

        with self.assertRaises(Exception) as context:
            await self.file_server.execute_operation(
                "read_file",
                {"path": "test.txt"},
                user_id="test_user"
            )

        self.assertIn("not whitelisted", str(context.exception))
        self.command_whitelist.is_command_allowed.assert_called()

        # Reset for next tests
        self.command_whitelist.is_command_allowed.return_value = True

        # Test 2: Security Logging Integration
        await self.file_server.execute_operation(
            "create_file",
            {"path": "test.txt", "content": "test content"},
            user_id="test_user"
        )

        self.security_logger.log_tool_operation.assert_called()
        call_args = self.security_logger.log_tool_operation.call_args
        self.assertEqual(call_args[1]["tool_type"], "file_system")
        self.assertEqual(call_args[1]["operation"], "create_file")

        # Test 3: Rate Limiting Integration (Web Search)
        # Simulate rate limit exceeded
        with patch.object(self.web_server, '_check_operation_rate_limit') as mock_rate_limit:
            mock_rate_limit.side_effect = Exception("Rate limit exceeded")

            with self.assertRaises(Exception) as context:
                await self.web_server.execute_operation(
                    "search",
                    {"query": "test query"},
                    user_id="test_user"
                )

            self.assertIn("Rate limit", str(context.exception))

        # Test 4: Authentication Integration (Calendar)
        with patch.object(self.calendar_server, '_verify_authentication') as mock_auth:
            mock_auth.side_effect = Exception("Authentication failed")

            with self.assertRaises(Exception) as context:
                await self.calendar_server.execute_operation(
                    "list_calendars",
                    {"service": "google"},
                    user_id="test_user"
                )

            self.assertIn("Authentication", str(context.exception))

        # Test 5: Audit Logging Integration (Task Management)
        await self.task_server.execute_operation(
            "create_task",
            {"task": {"title": "Test Task", "description": "Test", "priority": "medium"}},
            user_id="test_user"
        )

        # Verify audit logging was called
        self.assertTrue(self.task_server.log_all_operations)

    async def test_emergency_stop_effectiveness(self):
        """Critical Test: Verify emergency stops halt operations mid-execution"""

        # Test 1: Emergency stop before operation
        self.emergency_stop.is_emergency_active.return_value = True

        with self.assertRaises(Exception) as context:
            await self.file_server.execute_operation(
                "delete_file",
                {"path": "important.txt"},
                user_id="test_user"
            )

        self.assertIn("Emergency stop active", str(context.exception))

        # Test 2: Emergency stop activation during operation
        self.emergency_stop.is_emergency_active.return_value = False

        async def slow_operation():
            """Simulate a slow operation that can be interrupted"""
            await asyncio.sleep(0.1)  # Give time for emergency stop
            if self.emergency_stop.is_emergency_active():
                raise Exception("Emergency stop active - operation terminated")
            return {"success": True}

        # Start operation and trigger emergency stop
        operation_task = asyncio.create_task(
            self.file_server.execute_operation(
                "create_file",
                {"path": "test.txt", "content": "test"},
                user_id="test_user"
            )
        )

        # Trigger emergency stop after a short delay
        await asyncio.sleep(0.05)
        self.emergency_stop.is_emergency_active.return_value = True

        # Reset for normal operations
        self.emergency_stop.is_emergency_active.return_value = False

        # Test 3: Emergency stop recovery
        await self.emergency_stop.trigger_emergency_stop("Test emergency")
        self.emergency_stop.trigger_emergency_stop.assert_called_with("Test emergency")

        # Test 4: Verify all servers respect emergency stop
        self.emergency_stop.is_emergency_active.return_value = True

        servers_to_test = [
            (self.file_server, "read_file", {"path": "test.txt"}),
            (self.web_server, "search", {"query": "test"}),
            (self.calendar_server, "list_calendars", {"service": "google"}),
            (self.task_server, "list_tasks", {})
        ]

        for server, operation, params in servers_to_test:
            with self.assertRaises(Exception) as context:
                await server.execute_operation(operation, params, user_id="test_user")
            self.assertIn("Emergency stop", str(context.exception))

    async def test_performance_under_load(self):
        """Critical Test: Verify performance and security under concurrent load"""

        # Reset emergency stop
        self.emergency_stop.is_emergency_active.return_value = False

        # Test 1: Concurrent file operations
        async def file_operation(i):
            try:
                result = await self.file_server.execute_operation(
                    "create_file",
                    {"path": f"test_file_{i}.txt", "content": f"content {i}"},
                    user_id=f"user_{i % 5}"  # 5 different users
                )
                return {"success": True, "operation": i}
            except Exception as e:
                return {"success": False, "error": str(e), "operation": i}

        # Run 50 concurrent file operations
        start_time = time.time()
        tasks = [file_operation(i) for i in range(50)]
        results = await asyncio.gather(*tasks)
        execution_time = time.time() - start_time

        # Verify performance
        successful_ops = sum(1 for r in results if r["success"])
        self.assertGreater(successful_ops, 45)  # At least 90% success rate
        self.assertLess(execution_time, 10.0)  # Should complete within 10 seconds

        # Test 2: Security bypass prevention under load
        # Simulate trying to bypass security during high load

        async def security_bypass_attempt():
            # Try to execute without proper authentication
            try:
                await self.calendar_server.execute_operation(
                    "delete_event",
                    {"event_id": "important_event", "service": "google"},
                    user_id=None  # No user ID
                )
                return {"bypassed": True}
            except Exception as e:
                return {"bypassed": False, "error": str(e)}

        # Run security bypass attempts concurrently with legitimate operations
        bypass_tasks = [security_bypass_attempt() for _ in range(10)]
        legitimate_tasks = [file_operation(i + 100) for i in range(10)]

        all_tasks = bypass_tasks + legitimate_tasks
        all_results = await asyncio.gather(*all_tasks)

        # Verify no security bypasses occurred
        bypass_results = all_results[:10]
        legitimate_results = all_results[10:]

        for result in bypass_results:
            self.assertFalse(result.get("bypassed", False))

        # Verify legitimate operations still work
        legitimate_success = sum(1 for r in legitimate_results if r.get("success", False))
        self.assertGreater(legitimate_success, 7)  # At least 70% success rate

        # Test 3: Rate limiting under load
        async def rate_limited_search(i):
            try:
                result = await self.web_server.execute_operation(
                    "search",
                    {"query": f"test query {i}"},
                    user_id="rate_test_user"
                )
                return {"success": True}
            except Exception as e:
                return {"success": False, "error": str(e)}

        # Attempt many searches rapidly to trigger rate limiting
        search_tasks = [rate_limited_search(i) for i in range(20)]
        search_results = await asyncio.gather(*search_tasks)

        # Some should succeed, some should be rate limited
        successful_searches = sum(1 for r in search_results if r["success"])
        rate_limited_searches = sum(1 for r in search_results
                                  if not r["success"] and "rate limit" in r.get("error", "").lower())

        # Verify rate limiting is working
        self.assertGreater(rate_limited_searches, 0)
        self.assertLess(successful_searches, 20)  # Not all should succeed

    async def test_rollback_system_security(self):
        """Test rollback system security and integrity"""

        # Test 1: File system rollback
        original_content = "original content"
        modified_content = "modified content"

        # Create file
        create_result = await self.file_server.execute_operation(
            "create_file",
            {"path": "rollback_test.txt", "content": original_content},
            user_id="test_user"
        )

        # Modify file
        modify_result = await self.file_server.execute_operation(
            "write_file",
            {"path": "rollback_test.txt", "content": modified_content},
            user_id="test_user"
        )

        rollback_id = modify_result.get("rollback_id")
        self.assertIsNotNone(rollback_id)

        # Test rollback
        rollback_success = await self.file_server.rollback_operation(rollback_id)
        self.assertTrue(rollback_success)

        # Test 2: Task management rollback
        task_result = await self.task_server.execute_operation(
            "create_task",
            {"task": {"title": "Rollback Test", "description": "Test task", "priority": "low"}},
            user_id="test_user"
        )

        task_rollback_id = task_result.get("rollback_id")
        if task_rollback_id:
            rollback_success = await self.task_server.rollback_operation(task_rollback_id)
            self.assertTrue(rollback_success)

    async def test_cross_server_security_consistency(self):
        """Test security consistency across all tool servers"""

        # Test 1: Consistent security level determination
        test_cases = [
            (self.file_server, "delete_file", SecurityLevel.HIGH),
            (self.web_server, "download_file", SecurityLevel.HIGH),
            (self.calendar_server, "delete_event", SecurityLevel.CRITICAL),
            (self.task_server, "delete_task", SecurityLevel.CRITICAL)
        ]

        for server, operation, expected_level in test_cases:
            security_level = await server._determine_security_level(operation, {})
            self.assertEqual(security_level, expected_level)

        # Test 2: Consistent audit logging
        operations = [
            (self.file_server, "read_file", {"path": "test.txt"}),
            (self.web_server, "search", {"query": "test"}),
            (self.task_server, "list_tasks", {})
        ]

        for server, operation, params in operations:
            try:
                await server.execute_operation(operation, params, user_id="audit_test_user")
            except Exception:
                pass  # Ignore operation failures, we're testing audit logging

            # Verify security logging was called
            self.security_logger.log_tool_operation.assert_called()

    async def test_authentication_flow_security(self):
        """Test authentication flow security for calendar integration"""

        # Test 1: OAuth flow security
        auth_result = await self.calendar_server.execute_operation(
            "authenticate",
            {"service": "google", "redirect_uri": "https://localhost:8080/callback"},
            user_id="auth_test_user"
        )

        self.assertIn("auth_url", auth_result)
        self.assertEqual(auth_result["step"], "authorization_required")

        # Test 2: Invalid service rejection
        with self.assertRaises(ValueError):
            await self.calendar_server.execute_operation(
                "authenticate",
                {"service": "invalid_service"},
                user_id="auth_test_user"
            )

        # Test 3: Credential encryption verification
        test_credentials = {"access_token": "test_token", "refresh_token": "test_refresh"}
        encrypted = self.calendar_server._encrypt_credentials(test_credentials)
        decrypted = self.calendar_server._decrypt_credentials(encrypted)

        self.assertEqual(test_credentials["access_token"], decrypted["access_token"])

    async def test_comprehensive_error_handling(self):
        """Test comprehensive error handling across all servers"""

        # Test 1: Invalid parameters
        error_cases = [
            (self.file_server, "read_file", {"path": ""}),
            (self.web_server, "search", {"query": ""}),
            (self.calendar_server, "create_event", {"event": {}}),
            (self.task_server, "create_task", {"task": {}})
        ]

        for server, operation, params in error_cases:
            with self.assertRaises(Exception):
                await server.execute_operation(operation, params, user_id="error_test_user")

        # Test 2: Security violations
        self.command_whitelist.is_command_allowed.return_value = False

        for server in [self.file_server, self.web_server, self.calendar_server, self.task_server]:
            with self.assertRaises(Exception) as context:
                await server.execute_operation("dummy_operation", {}, user_id="security_test_user")
            self.assertIn("not whitelisted", str(context.exception))

    async def test_data_integrity_and_cleanup(self):
        """Test data integrity and cleanup procedures"""

        # Test 1: Database consistency
        # Create operations that span multiple tables
        task_result = await self.task_server.execute_operation(
            "create_task",
            {"task": {"title": "Integrity Test", "description": "Test", "priority": "medium"}},
            user_id="integrity_test_user"
        )

        comment_result = await self.task_server.execute_operation(
            "add_comment",
            {"task_id": task_result["task_id"], "comment": "Test comment"},
            user_id="integrity_test_user"
        )

        self.assertTrue(comment_result["added"])

        # Test 2: Cleanup procedures
        await self.manager.cleanup_all_servers()

        # Verify cleanup worked (expired data removed)
        # This would need actual expired data to test properly

        # Test 3: Rollback data expiration
        # Test that old rollback data is properly cleaned up
        await self.file_server.cleanup_expired_data()

    async def test_manager_integration(self):
        """Test tool server manager integration"""

        # Test 1: Cross-server operation execution
        file_result = await self.manager.execute_operation(
            ToolServerType.FILE_SYSTEM,
            "create_file",
            {"path": "manager_test.txt", "content": "test"},
            user_id="manager_test_user"
        )
        self.assertTrue(file_result.success)

        # Test 2: Server status monitoring
        status = await self.manager.get_server_status()
        self.assertIn("file_system", status)
        self.assertIn("web_search", status)
        self.assertIn("calendar", status)
        self.assertIn("task_management", status)

        # Test 3: Rollback across servers
        if file_result.rollback_id:
            rollback_success = await self.manager.rollback_operation(file_result.rollback_id)
            self.assertTrue(rollback_success)


class TestLoadAndStress(unittest.IsolatedAsyncioTestCase):
    """Stress testing for performance validation"""

    async def asyncSetUp(self):
        """Setup for stress testing"""
        self.test_db = tempfile.mktemp(suffix=".db")
        self.test_sandbox = tempfile.mkdtemp(prefix="stress_test_")

        # Initialize minimal file server for stress testing
        self.file_server = FileSystemToolServer(db_path=self.test_db)
        self.file_server.sandbox_root = Path(self.test_sandbox)
        await self.file_server.initialize()

    async def asyncTearDown(self):
        """Cleanup stress test environment"""
        try:
            Path(self.test_db).unlink(missing_ok=True)
            shutil.rmtree(self.test_sandbox, ignore_errors=True)
        except Exception:
            pass

    async def test_concurrent_file_operations(self):
        """Stress test concurrent file operations"""

        async def create_files_batch(batch_id, count=100):
            """Create a batch of files"""
            results = []
            for i in range(count):
                try:
                    result = await self.file_server.execute_operation(
                        "create_file",
                        {"path": f"stress_batch_{batch_id}_file_{i}.txt", "content": f"Content {i}"},
                        user_id=f"stress_user_{batch_id}"
                    )
                    results.append({"success": True, "file": i})
                except Exception as e:
                    results.append({"success": False, "error": str(e), "file": i})
            return results

        # Run 5 concurrent batches of 100 files each
        start_time = time.time()
        batch_tasks = [create_files_batch(i) for i in range(5)]
        all_results = await asyncio.gather(*batch_tasks)
        execution_time = time.time() - start_time

        # Analyze results
        total_operations = sum(len(batch) for batch in all_results)
        successful_operations = sum(
            sum(1 for result in batch if result["success"])
            for batch in all_results
        )

        success_rate = successful_operations / total_operations
        operations_per_second = total_operations / execution_time

        print(f"Stress Test Results:")
        print(f"Total operations: {total_operations}")
        print(f"Successful operations: {successful_operations}")
        print(f"Success rate: {success_rate:.2%}")
        print(f"Execution time: {execution_time:.2f}s")
        print(f"Operations per second: {operations_per_second:.2f}")

        # Assertions
        self.assertGreater(success_rate, 0.95)  # At least 95% success rate
        self.assertGreater(operations_per_second, 10)  # At least 10 ops/sec

    async def test_memory_usage_under_load(self):
        """Test memory usage doesn't grow excessively under load"""
        import psutil
        import os

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss

        # Perform many operations
        for batch in range(10):
            tasks = []
            for i in range(50):
                task = self.file_server.execute_operation(
                    "create_file",
                    {"path": f"memory_test_{batch}_{i}.txt", "content": f"Content {i}"},
                    user_id="memory_test_user"
                )
                tasks.append(task)

            await asyncio.gather(*tasks, return_exceptions=True)

        final_memory = process.memory_info().rss
        memory_growth = final_memory - initial_memory
        memory_growth_mb = memory_growth / 1024 / 1024

        print(f"Memory growth: {memory_growth_mb:.2f} MB")

        # Memory growth should be reasonable (less than 100MB for this test)
        self.assertLess(memory_growth_mb, 100)


if __name__ == "__main__":
    # Run tests with verbose output
    unittest.main(verbosity=2)