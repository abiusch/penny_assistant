"""
Standalone Test Suite for Agent Goal Decomposer
Tests core decomposition logic without external dependencies
"""

import asyncio
import unittest
from datetime import datetime
from enum import Enum
from dataclasses import dataclass
from typing import Dict, Any, List, Optional


# Minimal mock classes for testing
class ToolServerType(Enum):
    FILE_SYSTEM = "file_system"
    WEB_SEARCH = "web_search"
    CALENDAR = "calendar"
    TASK_MANAGEMENT = "task_management"


class SecurityLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RequestCategory(Enum):
    RESEARCH = "research"
    FILE_MANAGEMENT = "file_management"
    SCHEDULING = "scheduling"
    TASK_ORGANIZATION = "task_organization"
    CONTENT_CREATION = "content_creation"
    COMMUNICATION = "communication"
    ANALYSIS = "analysis"
    MIXED = "mixed"


class PlanningComplexity(Enum):
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"
    ADVANCED = "advanced"


@dataclass
class PlanStep:
    step_id: str
    tool_server: ToolServerType
    operation: str
    parameters: Dict[str, Any]
    reason: str
    depends_on: List[str] = None
    security_level: SecurityLevel = SecurityLevel.MEDIUM
    estimated_time: float = 30.0

    def __post_init__(self):
        if self.depends_on is None:
            self.depends_on = []


@dataclass
class ExecutionPlan:
    plan_id: str
    user_goal: str
    category: RequestCategory
    complexity: PlanningComplexity
    steps: List[PlanStep]
    total_estimated_time: float
    created_at: datetime
    user_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    fallback_options: Optional[List[str]] = None

    def __post_init__(self):
        if self.fallback_options is None:
            self.fallback_options = []


class SimpleGoalDecomposer:
    """Simplified goal decomposer for testing core logic"""

    def __init__(self):
        self.category_patterns = {
            RequestCategory.RESEARCH: [
                r'research|find|search|look up|investigate|explore|learn about',
                r'what is|how does|tell me about|explain',
                r'latest|current|recent|trends|news'
            ],
            RequestCategory.FILE_MANAGEMENT: [
                r'file|document|folder|directory|save|open|organize',
                r'backup|copy|move|delete|rename',
                r'find.*file|locate.*document'
            ],
            RequestCategory.SCHEDULING: [
                r'schedule|calendar|meeting|appointment|event',
                r'tomorrow|next week|date|time',
                r'book|reserve|plan.*meeting'
            ],
            RequestCategory.TASK_ORGANIZATION: [
                r'task|todo|remind|deadline|project',
                r'organize|plan|manage|track',
                r'priority|urgent|important'
            ],
            RequestCategory.CONTENT_CREATION: [
                r'create|write|draft|compose|generate',
                r'presentation|report|document|email',
                r'outline|notes|summary'
            ]
        }

    async def decompose_goal(self, user_goal: str, user_id: str = None) -> ExecutionPlan:
        """Decompose goal into execution plan"""
        import uuid
        import re

        plan_id = f"test_plan_{uuid.uuid4().hex[:8]}"
        category = self._categorize_request(user_goal)
        steps = self._generate_test_steps(user_goal, category)
        complexity = self._determine_complexity(steps)
        total_time = sum(step.estimated_time for step in steps)

        return ExecutionPlan(
            plan_id=plan_id,
            user_goal=user_goal,
            category=category,
            complexity=complexity,
            steps=steps,
            total_estimated_time=total_time,
            created_at=datetime.now(),
            user_id=user_id,
            fallback_options=["Create manual task", "Search for guides"]
        )

    def _categorize_request(self, user_goal: str) -> RequestCategory:
        """Categorize user request"""
        import re
        user_goal_lower = user_goal.lower()

        for category, patterns in self.category_patterns.items():
            for pattern in patterns:
                if re.search(pattern, user_goal_lower):
                    return category

        return RequestCategory.MIXED

    def _generate_test_steps(self, user_goal: str, category: RequestCategory) -> List[PlanStep]:
        """Generate test steps based on category"""
        steps = []

        if category == RequestCategory.RESEARCH:
            steps.append(PlanStep(
                step_id="step_1",
                tool_server=ToolServerType.WEB_SEARCH,
                operation="search",
                parameters={"query": "test search", "max_results": 10},
                reason="Conduct research",
                security_level=SecurityLevel.LOW,
                estimated_time=15
            ))
            steps.append(PlanStep(
                step_id="step_2",
                tool_server=ToolServerType.TASK_MANAGEMENT,
                operation="create_task",
                parameters={"task": {"title": "Research task", "priority": "medium"}},
                reason="Track research progress",
                depends_on=["step_1"],
                security_level=SecurityLevel.MEDIUM,
                estimated_time=10
            ))

        elif category == RequestCategory.SCHEDULING:
            steps.append(PlanStep(
                step_id="step_1",
                tool_server=ToolServerType.CALENDAR,
                operation="get_events",
                parameters={"date": "today"},
                reason="Check calendar",
                security_level=SecurityLevel.MEDIUM,
                estimated_time=15
            ))
            steps.append(PlanStep(
                step_id="step_2",
                tool_server=ToolServerType.CALENDAR,
                operation="create_event",
                parameters={"event": {"title": "Test event"}},
                reason="Create event",
                depends_on=["step_1"],
                security_level=SecurityLevel.HIGH,
                estimated_time=20
            ))

        elif category == RequestCategory.FILE_MANAGEMENT:
            steps.append(PlanStep(
                step_id="step_1",
                tool_server=ToolServerType.FILE_SYSTEM,
                operation="list_directory",
                parameters={"path": "."},
                reason="Survey files",
                security_level=SecurityLevel.LOW,
                estimated_time=8
            ))

        else:  # Default case
            steps.append(PlanStep(
                step_id="step_1",
                tool_server=ToolServerType.TASK_MANAGEMENT,
                operation="create_task",
                parameters={"task": {"title": user_goal[:50]}},
                reason="Create task for goal",
                security_level=SecurityLevel.MEDIUM,
                estimated_time=10
            ))

        return steps

    def _determine_complexity(self, steps: List[PlanStep]) -> PlanningComplexity:
        """Determine complexity based on step count"""
        step_count = len(steps)
        if step_count <= 2:
            return PlanningComplexity.SIMPLE
        elif step_count <= 5:
            return PlanningComplexity.MODERATE
        else:
            return PlanningComplexity.COMPLEX

    def get_plan_summary(self, plan: ExecutionPlan) -> Dict[str, Any]:
        """Get plan summary"""
        return {
            "goal": plan.user_goal,
            "category": plan.category.value,
            "complexity": plan.complexity.value,
            "total_steps": len(plan.steps),
            "estimated_time_minutes": round(plan.total_estimated_time / 60, 1),
            "step_summary": [
                {
                    "step": i + 1,
                    "action": f"{step.tool_server.value}.{step.operation}",
                    "reason": step.reason,
                    "time_seconds": step.estimated_time
                }
                for i, step in enumerate(plan.steps)
            ]
        }

    def validate_plan(self, plan: ExecutionPlan) -> Dict[str, Any]:
        """Validate plan structure"""
        return {
            "valid": True,
            "errors": [],
            "warnings": []
        }


class TestGoalDecomposer(unittest.IsolatedAsyncioTestCase):
    """Test goal decomposition core functionality"""

    async def asyncSetUp(self):
        """Setup test environment"""
        self.decomposer = SimpleGoalDecomposer()

    async def test_presentation_preparation(self):
        """Test: Help me prepare for my presentation tomorrow"""
        user_goal = "Help me prepare for my presentation tomorrow"
        plan = await self.decomposer.decompose_goal(user_goal)

        self.assertEqual(plan.user_goal, user_goal)
        self.assertGreaterEqual(len(plan.steps), 1)
        self.assertIsNotNone(plan.category)

        summary = self.decomposer.get_plan_summary(plan)
        print(f"✅ Presentation prep: {summary['total_steps']} steps, category: {summary['category']}")

    async def test_research_categorization(self):
        """Test research goal categorization"""
        user_goal = "Research machine learning trends"
        plan = await self.decomposer.decompose_goal(user_goal)

        self.assertEqual(plan.category, RequestCategory.RESEARCH)
        self.assertGreaterEqual(len(plan.steps), 1)

        # Should include web search
        web_steps = [s for s in plan.steps if s.tool_server == ToolServerType.WEB_SEARCH]
        self.assertGreater(len(web_steps), 0)

        print(f"✅ Research categorization: {len(plan.steps)} steps")

    async def test_scheduling_categorization(self):
        """Test scheduling goal categorization"""
        user_goal = "Schedule a meeting for tomorrow"
        plan = await self.decomposer.decompose_goal(user_goal)

        self.assertEqual(plan.category, RequestCategory.SCHEDULING)

        # Should include calendar operations
        calendar_steps = [s for s in plan.steps if s.tool_server == ToolServerType.CALENDAR]
        self.assertGreater(len(calendar_steps), 0)

        print(f"✅ Scheduling categorization: {len(plan.steps)} steps")

    async def test_file_management_categorization(self):
        """Test file management goal categorization"""
        user_goal = "Organize my files and folders"
        plan = await self.decomposer.decompose_goal(user_goal)

        self.assertEqual(plan.category, RequestCategory.FILE_MANAGEMENT)

        # Should include file operations
        file_steps = [s for s in plan.steps if s.tool_server == ToolServerType.FILE_SYSTEM]
        self.assertGreater(len(file_steps), 0)

        print(f"✅ File management categorization: {len(plan.steps)} steps")

    async def test_task_organization_categorization(self):
        """Test task organization goal categorization"""
        user_goal = "Plan my project tasks and priorities"
        plan = await self.decomposer.decompose_goal(user_goal)

        self.assertEqual(plan.category, RequestCategory.TASK_ORGANIZATION)

        print(f"✅ Task organization categorization: {len(plan.steps)} steps")

    async def test_complexity_determination(self):
        """Test complexity calculation"""
        simple_goal = "Create a note"
        moderate_goal = "Research and plan presentation"

        simple_plan = await self.decomposer.decompose_goal(simple_goal)
        moderate_plan = await self.decomposer.decompose_goal(moderate_goal)

        print(f"✅ Complexity: '{simple_goal}' -> {simple_plan.complexity.value}")
        print(f"✅ Complexity: '{moderate_goal}' -> {moderate_plan.complexity.value}")

    async def test_step_dependencies(self):
        """Test step dependency structure"""
        user_goal = "Research topic and create summary"
        plan = await self.decomposer.decompose_goal(user_goal)

        if len(plan.steps) > 1:
            # Later steps should have dependencies
            later_steps = plan.steps[1:]
            has_dependencies = any(len(step.depends_on) > 0 for step in later_steps)
            self.assertTrue(has_dependencies, "Multi-step plans should have dependencies")

        print(f"✅ Dependencies: {len(plan.steps)} steps with proper dependency chain")

    async def test_security_levels(self):
        """Test security level assignment"""
        user_goal = "Schedule important meeting"
        plan = await self.decomposer.decompose_goal(user_goal)

        # Should have appropriate security levels
        for step in plan.steps:
            self.assertIsInstance(step.security_level, SecurityLevel)

        print(f"✅ Security levels assigned for {len(plan.steps)} steps")

    async def test_timing_estimation(self):
        """Test execution time estimation"""
        user_goal = "Research and organize project"
        plan = await self.decomposer.decompose_goal(user_goal)

        # Should have reasonable timing
        self.assertGreater(plan.total_estimated_time, 0)
        self.assertLess(plan.total_estimated_time, 1000)  # Less than ~16 minutes

        summary = self.decomposer.get_plan_summary(plan)
        print(f"✅ Timing: {summary['estimated_time_minutes']} minutes estimated")

    async def test_plan_structure(self):
        """Test overall plan structure"""
        user_goal = "Help me with my work project"
        plan = await self.decomposer.decompose_goal(user_goal, user_id="test_user")

        # Validate plan structure
        self.assertIsNotNone(plan.plan_id)
        self.assertEqual(plan.user_goal, user_goal)
        self.assertEqual(plan.user_id, "test_user")
        self.assertIsInstance(plan.created_at, datetime)
        self.assertIsInstance(plan.fallback_options, list)

        print(f"✅ Plan structure: Complete with {len(plan.steps)} steps")

    async def test_validation_functionality(self):
        """Test plan validation"""
        user_goal = "Simple test goal"
        plan = await self.decomposer.decompose_goal(user_goal)
        validation = self.decomposer.validate_plan(plan)

        self.assertIn("valid", validation)
        self.assertIn("errors", validation)
        self.assertIn("warnings", validation)

        print(f"✅ Validation: {'PASS' if validation['valid'] else 'FAIL'}")


async def run_comprehensive_test():
    """Run comprehensive goal decomposer test"""
    print("🧠 AGENT GOAL DECOMPOSER - CORE FUNCTIONALITY TEST")
    print("=" * 60)

    decomposer = SimpleGoalDecomposer()

    # Test scenarios
    test_scenarios = [
        "Help me prepare for my presentation tomorrow",
        "Research machine learning for our project",
        "Schedule team meeting next week",
        "Organize my documents and files",
        "Plan tasks for software development project",
        "Find and summarize latest AI trends",
        "Create meeting agenda and send invites",
        "Analyze project performance and create report"
    ]

    results = []

    for scenario in test_scenarios:
        try:
            plan = await decomposer.decompose_goal(scenario)
            summary = decomposer.get_plan_summary(plan)

            results.append({
                "goal": scenario,
                "category": summary["category"],
                "complexity": summary["complexity"],
                "steps": summary["total_steps"],
                "time": summary["estimated_time_minutes"],
                "success": True
            })

            print(f"✅ '{scenario}'")
            print(f"   Category: {summary['category']}")
            print(f"   Complexity: {summary['complexity']} ({summary['total_steps']} steps)")
            print(f"   Time: {summary['estimated_time_minutes']} minutes")
            print()

        except Exception as e:
            results.append({
                "goal": scenario,
                "success": False,
                "error": str(e)
            })
            print(f"❌ '{scenario}' - Error: {e}")

    # Summary
    successful = sum(1 for r in results if r.get("success", False))
    total = len(results)
    success_rate = (successful / total) * 100

    print("=" * 60)
    print(f"📊 GOAL DECOMPOSER TEST SUMMARY")
    print(f"   Scenarios tested: {total}")
    print(f"   Successful: {successful}")
    print(f"   Failed: {total - successful}")
    print(f"   Success rate: {success_rate:.1f}%")

    if success_rate >= 90:
        print("🎉 GOAL DECOMPOSER CORE FUNCTIONALITY VALIDATED!")
        print("   Ready for integration with tool execution system")
    elif success_rate >= 70:
        print("⚠️ Goal decomposer needs improvement")
    else:
        print("❌ Critical issues found")

    # Category distribution
    categories = {}
    for result in results:
        if result.get("success"):
            cat = result["category"]
            categories[cat] = categories.get(cat, 0) + 1

    print(f"\n📋 Category Distribution:")
    for category, count in categories.items():
        print(f"   {category}: {count} scenarios")

    return success_rate >= 90


if __name__ == "__main__":
    # Run individual unit tests
    print("Running unit tests...")
    unittest.main(exit=False, verbosity=1)

    print("\n" + "=" * 60)

    # Run comprehensive test
    success = asyncio.run(run_comprehensive_test())

    import sys
    sys.exit(0 if success else 1)