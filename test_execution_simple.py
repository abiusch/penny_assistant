"""
Simple Execution Orchestrator Test - No Asyncio Conflicts
Tests core execution functionality without complex test frameworks
"""

import asyncio
from datetime import datetime

from agent_goal_decomposer import GoalDecomposer
from agent_execution_orchestrator import AgentExecutionOrchestrator, ExecutionStatus


async def test_basic_execution():
    """Test basic plan execution"""
    print("🚀 Testing Basic Plan Execution")

    # Create components
    decomposer = GoalDecomposer()
    orchestrator = AgentExecutionOrchestrator()
    await orchestrator.initialize()

    try:
        # Generate plan
        plan = await decomposer.decompose_goal(
            "Create a simple research note",
            user_id="test_user"
        )

        print(f"   Plan generated: {len(plan.steps)} steps")

        # Execute plan
        result = await orchestrator.execute_plan(plan, "test_user")

        print(f"   Execution status: {result.status.value}")
        print(f"   Completed steps: {result.completed_steps}/{result.total_steps}")

        # Validate success
        success = result.status == ExecutionStatus.COMPLETED
        print(f"   Result: {'SUCCESS' if success else 'FAILED'}")

        return success

    finally:
        await orchestrator.cleanup()


async def test_dependency_execution():
    """Test execution with dependencies"""
    print("🔗 Testing Dependency Resolution")

    from agent_goal_decomposer import ExecutionPlan, PlanStep, ToolServerType, SecurityLevel, RequestCategory, PlanningComplexity

    # Create plan with dependencies
    steps = [
        PlanStep(
            step_id="step_1",
            tool_server=ToolServerType.WEB_SEARCH,
            operation="search",
            parameters={"query": "test"},
            reason="Research first",
            depends_on=[],
            security_level=SecurityLevel.LOW,
            estimated_time=10.0
        ),
        PlanStep(
            step_id="step_2",
            tool_server=ToolServerType.FILE_SYSTEM,
            operation="create_file",
            parameters={"path": "summary.txt"},
            reason="Create file based on research",
            depends_on=["step_1"],
            security_level=SecurityLevel.MEDIUM,
            estimated_time=8.0
        )
    ]

    plan = ExecutionPlan(
        plan_id="dependency_test",
        user_goal="Test dependency execution",
        category=RequestCategory.MIXED,
        complexity=PlanningComplexity.SIMPLE,
        steps=steps,
        total_estimated_time=18.0,
        created_at=datetime.now(),
        user_id="test_user"
    )

    orchestrator = AgentExecutionOrchestrator()
    await orchestrator.initialize()

    try:
        result = await orchestrator.execute_plan(plan, "test_user")

        print(f"   Execution status: {result.status.value}")
        print(f"   Dependencies handled: {'YES' if result.status == ExecutionStatus.COMPLETED else 'NO'}")

        return result.status == ExecutionStatus.COMPLETED

    finally:
        await orchestrator.cleanup()


async def test_progress_tracking():
    """Test progress tracking functionality"""
    print("📈 Testing Progress Tracking")

    decomposer = GoalDecomposer()
    orchestrator = AgentExecutionOrchestrator()
    await orchestrator.initialize()

    progress_updates = []

    async def progress_callback(status_info):
        progress_updates.append(status_info['progress']['percentage'])

    try:
        plan = await decomposer.decompose_goal(
            "Research and organize data",
            user_id="test_user"
        )

        result = await orchestrator.execute_plan(
            plan,
            "test_user",
            progress_callback
        )

        print(f"   Progress updates received: {len(progress_updates)}")
        print(f"   Final progress: {max(progress_updates) if progress_updates else 0}%")

        return len(progress_updates) > 0 and result.status == ExecutionStatus.COMPLETED

    finally:
        await orchestrator.cleanup()


async def test_performance_metrics():
    """Test performance metrics collection"""
    print("📊 Testing Performance Metrics")

    orchestrator = AgentExecutionOrchestrator()
    await orchestrator.initialize()

    try:
        # Execute multiple small plans
        decomposer = GoalDecomposer()

        for i in range(3):
            plan = await decomposer.decompose_goal(
                f"Test execution {i+1}",
                user_id="test_user"
            )
            await orchestrator.execute_plan(plan, "test_user")

        # Get metrics
        metrics = await orchestrator.get_performance_metrics()

        print(f"   Total executions: {metrics['total_executions']}")
        print(f"   Successful executions: {metrics['successful_executions']}")
        print(f"   Steps executed: {metrics['total_steps_executed']}")

        return metrics['total_executions'] >= 3

    finally:
        await orchestrator.cleanup()


async def test_end_to_end_workflow():
    """Test complete end-to-end workflow"""
    print("🎯 Testing End-to-End Workflow")

    decomposer = GoalDecomposer()
    orchestrator = AgentExecutionOrchestrator()
    await orchestrator.initialize()

    try:
        # Complex goal requiring multiple operations
        goal = "Research machine learning trends, create summary document, and schedule follow-up meeting"

        # Step 1: Goal decomposition
        plan = await decomposer.decompose_goal(goal, user_id="test_user")

        print(f"   Goal decomposed: {len(plan.steps)} steps")
        print(f"   Category: {plan.category.value}")
        print(f"   Complexity: {plan.complexity.value}")

        # Step 2: Plan execution
        result = await orchestrator.execute_plan(plan, "test_user")

        print(f"   Execution completed: {result.status.value}")
        print(f"   Steps completed: {result.completed_steps}/{result.total_steps}")

        # Step 3: Validate success
        success = (
            result.status == ExecutionStatus.COMPLETED and
            result.completed_steps == result.total_steps
        )

        print(f"   End-to-end success: {'YES' if success else 'NO'}")

        return success

    finally:
        await orchestrator.cleanup()


async def run_simple_execution_tests():
    """Run all simple execution tests"""
    print("🧪 SIMPLE EXECUTION ORCHESTRATOR TESTS")
    print("=" * 60)

    tests = [
        ("Basic Execution", test_basic_execution),
        ("Dependency Resolution", test_dependency_execution),
        ("Progress Tracking", test_progress_tracking),
        ("Performance Metrics", test_performance_metrics),
        ("End-to-End Workflow", test_end_to_end_workflow)
    ]

    results = []

    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
            print(f"   ✅ {test_name}: {'PASS' if result else 'FAIL'}\n")
        except Exception as e:
            print(f"   ❌ {test_name}: ERROR - {e}\n")
            results.append((test_name, False))

    # Summary
    print("=" * 60)
    print("📊 EXECUTION ORCHESTRATOR TEST RESULTS")

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {test_name}: {status}")

    success_rate = (passed / total) * 100
    print(f"\n📈 Success Rate: {passed}/{total} ({success_rate:.1f}%)")

    if success_rate >= 90:
        print("🎉 EXECUTION ORCHESTRATOR READY FOR PRODUCTION!")
        print("   All core functionality validated")
    elif success_rate >= 70:
        print("⚠️  Some execution features need improvement")
    else:
        print("❌ Critical execution issues found")

    return success_rate >= 90


if __name__ == "__main__":
    # Run without unittest framework to avoid asyncio conflicts
    success = asyncio.run(run_simple_execution_tests())
    exit(0 if success else 1)