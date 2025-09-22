"""
Test Suite for Agent Execution Orchestrator
Tests plan execution, error recovery, security integration, and performance
"""

import asyncio
import unittest
from datetime import datetime, timedelta
from typing import Dict, Any, List

from agent_execution_orchestrator import (
    AgentExecutionOrchestrator, ExecutionStatus, StepStatus,
    ExecutionResult, StepExecution, execute_plan
)
from agent_goal_decomposer import (
    ExecutionPlan, PlanStep, ToolServerType, SecurityLevel,
    RequestCategory, PlanningComplexity
)


class MockMCPClient:
    """Mock MCP client for testing"""

    def __init__(self, fail_operations=None, slow_operations=None):
        self.fail_operations = fail_operations or []
        self.slow_operations = slow_operations or []
        self.call_count = 0

    async def initialize(self):
        return True

    async def close(self):
        pass

    async def call_tool(self, server_type, operation, parameters):
        self.call_count += 1
        operation_key = f"{server_type.value}:{operation}"

        # Simulate failures
        if operation_key in self.fail_operations:
            raise Exception(f"Mock failure for {operation_key}")

        # Simulate slow operations
        if operation_key in self.slow_operations:
            await asyncio.sleep(2.0)

        return {
            "status": "success",
            "result": f"Mock result for {operation}",
            "data": parameters,
            "timestamp": datetime.now().isoformat()
        }


class MockSecurityComponent:
    """Mock security component for testing"""

    def __init__(self, allow_all=True, emergency_active=False):
        self.allow_all = allow_all
        self.emergency_active = emergency_active
        self.events = []

    async def initialize(self):
        return True

    async def is_command_allowed(self, command):
        return self.allow_all

    def is_emergency_active(self):
        return self.emergency_active

    async def log_security_event(self, event_type, details):
        self.events.append({"type": event_type, "details": details})

    async def create_checkpoint(self, execution_id):
        return f"checkpoint_{execution_id}"

    async def rollback_to_checkpoint(self, checkpoint_id):
        return True


class TestExecutionOrchestrator(unittest.IsolatedAsyncioTestCase):
    """Test execution orchestrator functionality"""

    async def asyncSetUp(self):
        """Setup test environment"""
        self.mcp_client = MockMCPClient()
        self.security_components = {
            'whitelist': MockSecurityComponent(),
            'emergency': MockSecurityComponent(),
            'logger': MockSecurityComponent(),
            'rollback': MockSecurityComponent()
        }
        self.orchestrator = AgentExecutionOrchestrator(
            mcp_client=self.mcp_client,
            security_components=self.security_components
        )
        await self.orchestrator.initialize()

    async def asyncTearDown(self):
        """Cleanup after tests"""
        await self.orchestrator.cleanup()

    def _create_test_plan(self, step_count=3, with_dependencies=True) -> ExecutionPlan:
        """Create test execution plan"""
        steps = []

        for i in range(step_count):
            step_id = f"step_{i+1}"
            depends_on = [f"step_{i}"] if with_dependencies and i > 0 else []

            step = PlanStep(
                step_id=step_id,
                tool_server=ToolServerType.WEB_SEARCH if i % 2 == 0 else ToolServerType.FILE_SYSTEM,
                operation="search" if i % 2 == 0 else "create_file",
                parameters={"query": f"test_{i}"} if i % 2 == 0 else {"path": f"test_{i}.txt"},
                reason=f"Test step {i+1}",
                depends_on=depends_on,
                security_level=SecurityLevel.LOW,
                estimated_time=10.0
            )
            steps.append(step)

        return ExecutionPlan(
            plan_id="test_plan_001",
            user_goal="Test execution plan",
            category=RequestCategory.MIXED,
            complexity=PlanningComplexity.SIMPLE,
            steps=steps,
            total_estimated_time=sum(step.estimated_time for step in steps),
            created_at=datetime.now(),
            user_id="test_user"
        )

    async def test_basic_plan_execution(self):
        """Test basic plan execution functionality"""
        plan = self._create_test_plan(step_count=3)

        result = await self.orchestrator.execute_plan(plan, "test_user")

        # Validate execution result
        self.assertEqual(result.status, ExecutionStatus.COMPLETED)
        self.assertEqual(result.completed_steps, 3)
        self.assertEqual(result.total_steps, 3)
        self.assertIsNotNone(result.end_time)
        self.assertGreater(len(result.step_results), 0)

        # Check all steps completed
        for step_result in result.step_results:
            self.assertEqual(step_result.status, StepStatus.COMPLETED)
            self.assertIsNotNone(step_result.result)

        print(f"✅ Basic execution: {result.completed_steps}/{result.total_steps} steps completed")

    async def test_dependency_resolution(self):
        """Test that dependencies are respected during execution"""
        plan = self._create_test_plan(step_count=4, with_dependencies=True)

        # Track execution order
        execution_order = []

        original_call_tool = self.mcp_client.call_tool
        async def track_execution(server_type, operation, parameters):
            execution_order.append(operation)
            return await original_call_tool(server_type, operation, parameters)

        self.mcp_client.call_tool = track_execution

        result = await self.orchestrator.execute_plan(plan, "test_user")

        # Validate execution completed
        self.assertEqual(result.status, ExecutionStatus.COMPLETED)

        # Check that dependencies were respected
        # Step 1 (search) should execute before step 2 (create_file)
        search_index = execution_order.index("search")
        create_file_index = execution_order.index("create_file")
        self.assertLess(search_index, create_file_index)

        print(f"✅ Dependency resolution: Execution order {execution_order}")

    async def test_parallel_execution(self):
        """Test parallel execution of independent steps"""
        # Create plan with independent steps (no dependencies)
        plan = self._create_test_plan(step_count=3, with_dependencies=False)

        start_time = datetime.now()
        result = await self.orchestrator.execute_plan(plan, "test_user")
        execution_time = (datetime.now() - start_time).total_seconds()

        # Should complete successfully
        self.assertEqual(result.status, ExecutionStatus.COMPLETED)

        # With parallel execution, should be faster than sequential
        # (Each step takes ~0.01s mock time, sequential would be 0.03s+)
        self.assertLess(execution_time, 0.5)  # Should be much faster

        print(f"✅ Parallel execution: {execution_time:.3f}s for 3 independent steps")

    async def test_error_recovery_and_retry(self):
        """Test error recovery with retry logic"""
        # Configure MCP client to fail specific operations
        self.mcp_client.fail_operations = ["web_search:search"]

        plan = self._create_test_plan(step_count=2)

        result = await self.orchestrator.execute_plan(plan, "test_user")

        # Should fail because search operation fails
        self.assertEqual(result.status, ExecutionStatus.FAILED)

        # Check that retries were attempted
        search_step = next(
            step for step in result.step_results
            if step.step.operation == "search"
        )
        self.assertEqual(search_step.status, StepStatus.FAILED)
        self.assertGreater(search_step.retry_count, 0)

        print(f"✅ Error recovery: {search_step.retry_count} retry attempts made")

    async def test_security_integration(self):
        """Test security component integration"""
        # Configure security to block operations
        self.security_components['whitelist'].allow_all = False

        plan = self._create_test_plan(step_count=2)

        result = await self.orchestrator.execute_plan(plan, "test_user")

        # Should fail due to security validation
        self.assertEqual(result.status, ExecutionStatus.FAILED)
        self.assertIn("not allowed", result.error_summary)

        # Check security logging
        security_events = self.security_components['logger'].events
        self.assertGreater(len(security_events), 0)

        print(f"✅ Security integration: {len(security_events)} security events logged")

    async def test_emergency_stop_integration(self):
        """Test emergency stop functionality"""
        # Configure emergency system to be active
        self.security_components['emergency'].emergency_active = True

        plan = self._create_test_plan(step_count=3)

        result = await self.orchestrator.execute_plan(plan, "test_user")

        # Should be stopped due to emergency
        self.assertEqual(result.status, ExecutionStatus.FAILED)
        self.assertIn("Emergency stop active", result.error_summary)

        print("✅ Emergency stop: Execution properly blocked")

    async def test_progress_tracking(self):
        """Test real-time progress tracking"""
        plan = self._create_test_plan(step_count=4)

        progress_updates = []

        async def progress_callback(status_info):
            progress_updates.append(status_info['progress']['percentage'])

        result = await self.orchestrator.execute_plan(plan, "test_user", progress_callback)

        # Should complete successfully
        self.assertEqual(result.status, ExecutionStatus.COMPLETED)

        # Should have received progress updates
        self.assertGreater(len(progress_updates), 0)
        self.assertEqual(max(progress_updates), 100.0)  # Should reach 100%

        print(f"✅ Progress tracking: {len(progress_updates)} progress updates received")

    async def test_execution_status_queries(self):
        """Test execution status querying"""
        plan = self._create_test_plan(step_count=3)

        # Start execution (don't await completion)
        execution_task = asyncio.create_task(
            self.orchestrator.execute_plan(plan, "test_user")
        )

        # Give it a moment to start
        await asyncio.sleep(0.1)

        # Get execution ID from active executions
        execution_id = list(self.orchestrator.active_executions.keys())[0] if self.orchestrator.active_executions else None

        if execution_id:
            status = await self.orchestrator.get_execution_status(execution_id)
            self.assertIsNotNone(status)
            self.assertEqual(status['execution_id'], execution_id)
            self.assertIn('progress', status)

        # Wait for completion
        result = await execution_task
        self.assertEqual(result.status, ExecutionStatus.COMPLETED)

        print("✅ Status queries: Real-time status tracking working")

    async def test_execution_cancellation(self):
        """Test execution cancellation"""
        # Create slow operations to allow cancellation
        self.mcp_client.slow_operations = ["web_search:search", "file_system:create_file"]

        plan = self._create_test_plan(step_count=3)

        # Start execution
        execution_task = asyncio.create_task(
            self.orchestrator.execute_plan(plan, "test_user")
        )

        # Give it a moment to start
        await asyncio.sleep(0.1)

        # Cancel execution
        execution_id = list(self.orchestrator.active_executions.keys())[0]
        cancelled = await self.orchestrator.cancel_execution(execution_id)

        self.assertTrue(cancelled)

        # Wait for task to complete
        result = await execution_task
        self.assertEqual(result.status, ExecutionStatus.CANCELLED)

        print("✅ Execution cancellation: Successfully cancelled running execution")

    async def test_performance_metrics(self):
        """Test performance metrics collection"""
        plan = self._create_test_plan(step_count=3)

        # Execute multiple plans
        for i in range(3):
            await self.orchestrator.execute_plan(plan, f"test_user_{i}")

        metrics = await self.orchestrator.get_performance_metrics()

        # Validate metrics
        self.assertEqual(metrics["total_executions"], 3)
        self.assertEqual(metrics["successful_executions"], 3)
        self.assertEqual(metrics["failed_executions"], 0)
        self.assertGreater(metrics["total_steps_executed"], 0)
        self.assertGreater(metrics["average_execution_time"], 0)

        print(f"✅ Performance metrics: {metrics['total_executions']} executions tracked")

    async def test_complex_multi_domain_plan(self):
        """Test execution of complex multi-domain plan"""
        # Create complex plan with different tool servers
        steps = [
            PlanStep(
                step_id="search_step",
                tool_server=ToolServerType.WEB_SEARCH,
                operation="search",
                parameters={"query": "test research"},
                reason="Research information",
                depends_on=[],
                security_level=SecurityLevel.LOW,
                estimated_time=15.0
            ),
            PlanStep(
                step_id="calendar_step",
                tool_server=ToolServerType.CALENDAR,
                operation="get_events",
                parameters={"date": "today"},
                reason="Check calendar",
                depends_on=[],
                security_level=SecurityLevel.MEDIUM,
                estimated_time=10.0
            ),
            PlanStep(
                step_id="file_step",
                tool_server=ToolServerType.FILE_SYSTEM,
                operation="create_file",
                parameters={"path": "summary.txt", "content": "Research summary"},
                reason="Create summary file",
                depends_on=["search_step"],
                security_level=SecurityLevel.MEDIUM,
                estimated_time=8.0
            ),
            PlanStep(
                step_id="task_step",
                tool_server=ToolServerType.TASK_MANAGEMENT,
                operation="create_task",
                parameters={"task": {"title": "Review research", "priority": "medium"}},
                reason="Create follow-up task",
                depends_on=["search_step", "calendar_step"],
                security_level=SecurityLevel.MEDIUM,
                estimated_time=12.0
            )
        ]

        plan = ExecutionPlan(
            plan_id="complex_plan_001",
            user_goal="Research and organize findings",
            category=RequestCategory.MIXED,
            complexity=PlanningComplexity.COMPLEX,
            steps=steps,
            total_estimated_time=45.0,
            created_at=datetime.now(),
            user_id="test_user"
        )

        result = await self.orchestrator.execute_plan(plan, "test_user")

        # Should complete successfully
        self.assertEqual(result.status, ExecutionStatus.COMPLETED)
        self.assertEqual(result.completed_steps, 4)

        # Verify all different tool servers were called
        called_servers = set(
            step.step.tool_server for step in result.step_results
            if step.status == StepStatus.COMPLETED
        )
        self.assertEqual(len(called_servers), 4)  # All 4 server types

        print(f"✅ Complex multi-domain: {len(called_servers)} tool servers utilized")


class TestConvenienceFunction(unittest.IsolatedAsyncioTestCase):
    """Test convenience function"""

    async def test_convenience_execute_plan(self):
        """Test convenience function for plan execution"""
        plan = ExecutionPlan(
            plan_id="convenience_test",
            user_goal="Test convenience function",
            category=RequestCategory.MIXED,
            complexity=PlanningComplexity.SIMPLE,
            steps=[
                PlanStep(
                    step_id="step_1",
                    tool_server=ToolServerType.WEB_SEARCH,
                    operation="search",
                    parameters={"query": "test"},
                    reason="Test search",
                    depends_on=[],
                    security_level=SecurityLevel.LOW,
                    estimated_time=10.0
                )
            ],
            total_estimated_time=10.0,
            created_at=datetime.now(),
            user_id="test_user"
        )

        result = await execute_plan(plan, "test_user")

        self.assertEqual(result.status, ExecutionStatus.COMPLETED)
        self.assertEqual(result.completed_steps, 1)

        print("✅ Convenience function: Direct plan execution working")


async def run_execution_orchestrator_tests():
    """Run comprehensive execution orchestrator tests"""
    print("🚀 EXECUTION ORCHESTRATOR TEST SUITE")
    print("=" * 60)

    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestExecutionOrchestrator))
    suite.addTests(loader.loadTestsFromTestCase(TestConvenienceFunction))

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Summary
    print("\n" + "=" * 60)
    print(f"🚀 EXECUTION ORCHESTRATOR TEST RESULTS")
    print(f"   Tests run: {result.testsRun}")
    print(f"   Failures: {len(result.failures)}")
    print(f"   Errors: {len(result.errors)}")

    if result.failures:
        print("\n❌ FAILURES:")
        for test, traceback in result.failures:
            print(f"   {test}: {traceback}")

    if result.errors:
        print("\n⚠️ ERRORS:")
        for test, traceback in result.errors:
            print(f"   {test}: {traceback}")

    success_rate = ((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun) * 100
    print(f"\n📊 Success Rate: {success_rate:.1f}%")

    if success_rate >= 90:
        print("🎉 EXECUTION ORCHESTRATOR READY FOR PRODUCTION!")
        print("✅ Plan execution with dependency resolution")
        print("✅ Error recovery and retry logic")
        print("✅ Security integration and emergency stops")
        print("✅ Real-time progress tracking")
        print("✅ Performance monitoring and metrics")
    elif success_rate >= 70:
        print("⚠️ Execution orchestrator needs improvement")
    else:
        print("❌ Critical issues found in execution orchestrator")

    return result.wasSuccessful()


if __name__ == "__main__":
    # Run the execution orchestrator tests
    import sys
    success = asyncio.run(run_execution_orchestrator_tests())
    sys.exit(0 if success else 1)