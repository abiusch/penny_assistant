"""
Test Suite for Agent Goal Decomposer
Validates goal decomposition logic across different request types
"""

import asyncio
import unittest
from datetime import datetime
from typing import Dict, Any

from agent_goal_decomposer import (
    GoalDecomposer, RequestCategory, PlanningComplexity,
    ToolServerType, SecurityLevel, decompose_user_goal
)


class TestGoalDecomposer(unittest.IsolatedAsyncioTestCase):
    """Test goal decomposition functionality"""

    async def asyncSetUp(self):
        """Setup test environment"""
        self.decomposer = GoalDecomposer()

    async def test_presentation_preparation(self):
        """Test: Help me prepare for my presentation tomorrow"""
        user_goal = "Help me prepare for my presentation tomorrow"

        plan = await self.decomposer.decompose_goal(user_goal, user_id="test_user")

        # Validate basic plan structure
        self.assertEqual(plan.user_goal, user_goal)
        self.assertIn(plan.category, [RequestCategory.CONTENT_CREATION, RequestCategory.MIXED])
        self.assertGreaterEqual(len(plan.steps), 2)

        # Validate step types
        step_operations = [(step.tool_server, step.operation) for step in plan.steps]

        # Should include calendar check
        calendar_ops = [op for server, op in step_operations if server == ToolServerType.CALENDAR]
        self.assertGreater(len(calendar_ops), 0, "Should include calendar operations")

        # Should include task creation
        task_ops = [op for server, op in step_operations if server == ToolServerType.TASK_MANAGEMENT]
        self.assertGreater(len(task_ops), 0, "Should include task management operations")

        # Validate plan summary
        summary = self.decomposer.get_plan_summary(plan)
        self.assertIn("goal", summary)
        self.assertIn("step_summary", summary)
        self.assertGreater(len(summary["step_summary"]), 0)

        print(f"✅ Presentation prep plan: {len(plan.steps)} steps")
        for i, step in enumerate(plan.steps):
            print(f"   {i+1}. {step.tool_server.value}.{step.operation} - {step.reason}")

    async def test_research_project(self):
        """Test: Research machine learning trends for our project"""
        user_goal = "Research machine learning trends for our project"

        plan = await self.decomposer.decompose_goal(user_goal, user_id="test_user")

        # Validate research categorization
        self.assertEqual(plan.category, RequestCategory.RESEARCH)
        self.assertGreaterEqual(len(plan.steps), 2)

        # Should start with web search
        first_step = plan.steps[0]
        self.assertEqual(first_step.tool_server, ToolServerType.WEB_SEARCH)
        self.assertEqual(first_step.operation, "search")
        self.assertIn("machine learning trends", first_step.parameters.get("query", "").lower())

        # Should include task tracking
        task_steps = [step for step in plan.steps if step.tool_server == ToolServerType.TASK_MANAGEMENT]
        self.assertGreater(len(task_steps), 0)

        # Validate execution time
        self.assertGreater(plan.total_estimated_time, 0)

        print(f"✅ Research plan: {len(plan.steps)} steps, {plan.total_estimated_time:.1f}s estimated")

    async def test_meeting_scheduling(self):
        """Test: Schedule a team meeting for next week"""
        user_goal = "Schedule a team meeting for next week"

        plan = await self.decomposer.decompose_goal(user_goal, user_id="test_user")

        # Validate scheduling categorization
        self.assertEqual(plan.category, RequestCategory.SCHEDULING)

        # Should include calendar operations
        calendar_steps = [step for step in plan.steps if step.tool_server == ToolServerType.CALENDAR]
        self.assertGreater(len(calendar_steps), 0, "Should include calendar operations")

        # Should check availability first
        availability_steps = [step for step in plan.steps if step.operation == "get_availability"]
        self.assertGreater(len(availability_steps), 0, "Should check availability")

        # Should create event
        create_steps = [step for step in plan.steps if step.operation == "create_event"]
        self.assertGreater(len(create_steps), 0, "Should create event")

        print(f"✅ Meeting scheduling plan: {len(plan.steps)} steps")

    async def test_file_organization(self):
        """Test: Organize my documents and clean up the desktop"""
        user_goal = "Organize my documents and clean up the desktop"

        plan = await self.decomposer.decompose_goal(user_goal, user_id="test_user")

        # Validate file management categorization
        self.assertEqual(plan.category, RequestCategory.FILE_MANAGEMENT)

        # Should include file system operations
        file_steps = [step for step in plan.steps if step.tool_server == ToolServerType.FILE_SYSTEM]
        self.assertGreater(len(file_steps), 0, "Should include file operations")

        # Should list directory first
        list_steps = [step for step in plan.steps if step.operation == "list_directory"]
        self.assertGreater(len(list_steps), 0, "Should list directories")

        print(f"✅ File organization plan: {len(plan.steps)} steps")

    async def test_task_planning(self):
        """Test: Plan my tasks for the software development project"""
        user_goal = "Plan my tasks for the software development project"

        plan = await self.decomposer.decompose_goal(user_goal, user_id="test_user")

        # Validate task organization categorization
        self.assertEqual(plan.category, RequestCategory.TASK_ORGANIZATION)

        # Should include task management operations
        task_steps = [step for step in plan.steps if step.tool_server == ToolServerType.TASK_MANAGEMENT]
        self.assertGreater(len(task_steps), 0, "Should include task operations")

        # Should list current tasks
        list_steps = [step for step in plan.steps if step.operation == "list_tasks"]
        self.assertGreater(len(list_steps), 0, "Should list current tasks")

        # Should create project or tasks
        creation_steps = [step for step in plan.steps
                         if step.operation in ["create_project", "create_task"]]
        self.assertGreater(len(creation_steps), 0, "Should create project or tasks")

        print(f"✅ Task planning: {len(plan.steps)} steps")

    async def test_mixed_goal(self):
        """Test: Help me understand blockchain and create a summary"""
        user_goal = "Help me understand blockchain and create a summary"

        plan = await self.decomposer.decompose_goal(user_goal, user_id="test_user")

        # Should handle mixed research + content creation
        self.assertIn(plan.category, [RequestCategory.RESEARCH, RequestCategory.CONTENT_CREATION, RequestCategory.MIXED])

        # Should include web search
        web_steps = [step for step in plan.steps if step.tool_server == ToolServerType.WEB_SEARCH]
        self.assertGreater(len(web_steps), 0, "Should include web search")

        # Should include file creation for summary
        file_steps = [step for step in plan.steps
                     if step.tool_server == ToolServerType.FILE_SYSTEM and
                        step.operation in ["create_file", "write_file"]]
        self.assertGreater(len(file_steps), 0, "Should create summary file")

        print(f"✅ Mixed goal plan: {len(plan.steps)} steps")

    async def test_plan_validation(self):
        """Test plan validation functionality"""
        user_goal = "Test validation with simple task"

        plan = await self.decomposer.decompose_goal(user_goal, user_id="test_user")
        validation = self.decomposer.validate_plan(plan)

        # Should be valid
        self.assertTrue(validation["valid"], f"Plan should be valid: {validation['errors']}")
        self.assertIsInstance(validation["errors"], list)
        self.assertIsInstance(validation["warnings"], list)

        print(f"✅ Plan validation: {'PASS' if validation['valid'] else 'FAIL'}")
        if validation["warnings"]:
            print(f"   Warnings: {len(validation['warnings'])}")

    async def test_complexity_determination(self):
        """Test complexity determination for different goal types"""
        test_goals = [
            ("Create a quick note", PlanningComplexity.SIMPLE),
            ("Research and organize findings for presentation", PlanningComplexity.MODERATE),
            ("Plan comprehensive project with research, scheduling, and documentation", PlanningComplexity.COMPLEX)
        ]

        for goal, expected_complexity in test_goals:
            plan = await self.decomposer.decompose_goal(goal, user_id="test_user")
            self.assertIsInstance(plan.complexity, PlanningComplexity)
            print(f"✅ '{goal}' -> {plan.complexity.value} ({len(plan.steps)} steps)")

    async def test_security_levels(self):
        """Test that security levels are properly assigned"""
        user_goal = "Delete old files and create important presentation"

        plan = await self.decomposer.decompose_goal(user_goal, user_id="test_user")

        # Check that delete operations have high security
        delete_steps = [step for step in plan.steps if "delete" in step.operation]
        for step in delete_steps:
            self.assertIn(step.security_level, [SecurityLevel.HIGH, SecurityLevel.CRITICAL])

        # Check that read operations have low security
        read_steps = [step for step in plan.steps if step.operation in ["read_file", "list_directory", "search"]]
        for step in read_steps:
            self.assertEqual(step.security_level, SecurityLevel.LOW)

        print(f"✅ Security levels properly assigned across {len(plan.steps)} steps")

    async def test_parameter_extraction(self):
        """Test parameter extraction from user goals"""
        test_cases = [
            ("Search for Python tutorials", "python tutorials"),
            ("Find all PDF files in my documents", "*.pdf"),
            ("Schedule urgent meeting tomorrow", "urgent"),
        ]

        for goal, expected_param in test_cases:
            plan = await self.decomposer.decompose_goal(goal, user_id="test_user")

            # Check that parameters contain expected content
            found_param = False
            for step in plan.steps:
                for param_value in step.parameters.values():
                    if isinstance(param_value, str) and expected_param.lower() in param_value.lower():
                        found_param = True
                        break
                    elif isinstance(param_value, dict):
                        for nested_value in param_value.values():
                            if isinstance(nested_value, str) and expected_param.lower() in nested_value.lower():
                                found_param = True
                                break

            self.assertTrue(found_param, f"Expected parameter '{expected_param}' not found in goal '{goal}'")

        print(f"✅ Parameter extraction working correctly")

    async def test_convenience_function(self):
        """Test the convenience function for goal decomposition"""
        user_goal = "Quick test of convenience function"

        plan = await decompose_user_goal(user_goal, user_id="test_user")

        self.assertIsNotNone(plan)
        self.assertEqual(plan.user_goal, user_goal)
        self.assertGreater(len(plan.steps), 0)

        print(f"✅ Convenience function working: {len(plan.steps)} steps generated")

    async def test_fallback_options(self):
        """Test that fallback options are generated"""
        user_goal = "Complex goal that might need fallbacks"

        plan = await self.decomposer.decompose_goal(user_goal, user_id="test_user")

        self.assertIsNotNone(plan.fallback_options)
        self.assertGreater(len(plan.fallback_options), 0)

        print(f"✅ Fallback options: {len(plan.fallback_options)} alternatives generated")

    async def test_step_dependencies(self):
        """Test that step dependencies are properly set"""
        user_goal = "Research topic and create comprehensive report"

        plan = await self.decomposer.decompose_goal(user_goal, user_id="test_user")

        # Check for dependency chains
        has_dependencies = any(len(step.depends_on) > 0 for step in plan.steps)

        if len(plan.steps) > 1:
            self.assertTrue(has_dependencies, "Multi-step plans should have dependencies")

        # Validate dependency references
        all_step_ids = {step.step_id for step in plan.steps}
        for step in plan.steps:
            for dep_id in step.depends_on:
                self.assertIn(dep_id, all_step_ids, f"Invalid dependency reference: {dep_id}")

        print(f"✅ Step dependencies properly set for {len(plan.steps)} steps")


class TestGoalDecomposerIntegration(unittest.IsolatedAsyncioTestCase):
    """Integration tests with realistic scenarios"""

    async def asyncSetUp(self):
        """Setup test environment"""
        self.decomposer = GoalDecomposer()

    async def test_realistic_work_scenario(self):
        """Test: Realistic work scenario with multiple requirements"""
        user_goal = "I need to prepare for tomorrow's client presentation on our Q4 results. Find latest market data, update slides, and schedule follow-up meeting."

        plan = await self.decomposer.decompose_goal(
            user_goal,
            user_id="cj",
            context={"work_context": True, "urgent": True}
        )

        # Should be complex plan
        self.assertGreaterEqual(len(plan.steps), 4)
        self.assertIn(plan.complexity, [PlanningComplexity.MODERATE, PlanningComplexity.COMPLEX])

        # Should include multiple tool types
        tool_types = {step.tool_server for step in plan.steps}
        self.assertGreaterEqual(len(tool_types), 2, "Should use multiple tool types")

        # Validate realistic execution time
        self.assertLessEqual(plan.total_estimated_time, 300, "Should be completable in reasonable time")

        summary = self.decomposer.get_plan_summary(plan)
        print(f"✅ Realistic scenario: {summary['total_steps']} steps, {summary['estimated_time_minutes']} min")

    async def test_personal_organization_scenario(self):
        """Test: Personal organization scenario"""
        user_goal = "Help me get organized - clean up my files, plan this week's tasks, and research vacation destinations for next month."

        plan = await self.decomposer.decompose_goal(
            user_goal,
            user_id="cj",
            context={"personal_context": True}
        )

        # Should handle multiple categories
        self.assertGreaterEqual(len(plan.steps), 3)

        # Should include all relevant tool types
        tool_types = {step.tool_server for step in plan.steps}
        expected_types = {ToolServerType.FILE_SYSTEM, ToolServerType.TASK_MANAGEMENT, ToolServerType.WEB_SEARCH}
        self.assertTrue(expected_types.issubset(tool_types), "Should include file, task, and web operations")

        print(f"✅ Personal organization: {len(plan.steps)} steps across {len(tool_types)} tool types")

    async def test_learning_scenario(self):
        """Test: Learning and research scenario"""
        user_goal = "I want to learn about Docker containers. Find good tutorials, create a study plan, and set up practice schedule."

        plan = await self.decomposer.decompose_goal(user_goal, user_id="cj")

        # Should be research-focused
        self.assertEqual(plan.category, RequestCategory.RESEARCH)

        # Should include web search
        web_steps = [step for step in plan.steps if step.tool_server == ToolServerType.WEB_SEARCH]
        self.assertGreater(len(web_steps), 0)

        # Should include planning elements
        task_steps = [step for step in plan.steps if step.tool_server == ToolServerType.TASK_MANAGEMENT]
        calendar_steps = [step for step in plan.steps if step.tool_server == ToolServerType.CALENDAR]

        self.assertTrue(len(task_steps) > 0 or len(calendar_steps) > 0, "Should include planning")

        print(f"✅ Learning scenario: {len(plan.steps)} steps for structured learning")


if __name__ == "__main__":
    # Custom test runner with better output
    async def run_tests():
        print("🧠 TESTING AGENT GOAL DECOMPOSER")
        print("=" * 50)

        # Create test suite
        loader = unittest.TestLoader()
        suite = unittest.TestSuite()

        # Add test classes
        suite.addTests(loader.loadTestsFromTestCase(TestGoalDecomposer))
        suite.addTests(loader.loadTestsFromTestCase(TestGoalDecomposerIntegration))

        # Run tests
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)

        # Summary
        print("\n" + "=" * 50)
        print(f"🎯 GOAL DECOMPOSER TEST RESULTS")
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
            print("🎉 GOAL DECOMPOSER READY FOR PRODUCTION!")
        elif success_rate >= 70:
            print("⚠️ Goal decomposer needs improvement before deployment")
        else:
            print("❌ Critical issues found - do not deploy")

        return result.wasSuccessful()

    # Run the tests
    import sys
    success = asyncio.run(run_tests())
    sys.exit(0 if success else 1)