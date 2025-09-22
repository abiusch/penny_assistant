"""
Agent Goal Decomposer
Core planning engine that breaks down complex user requests into executable steps using available tool operations
"""

import asyncio
import json
import re
import uuid
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict

# Import existing security components with fallbacks
try:
    from tool_server_foundation import ToolServerType, SecurityLevel
except ImportError:
    # Fallback definitions for standalone testing
    from enum import Enum

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
    """Categories of user requests for planning"""
    RESEARCH = "research"
    FILE_MANAGEMENT = "file_management"
    SCHEDULING = "scheduling"
    TASK_ORGANIZATION = "task_organization"
    CONTENT_CREATION = "content_creation"
    COMMUNICATION = "communication"
    ANALYSIS = "analysis"
    MIXED = "mixed"


class PlanningComplexity(Enum):
    """Complexity levels for goal decomposition"""
    SIMPLE = "simple"        # 1-2 steps
    MODERATE = "moderate"    # 3-5 steps
    COMPLEX = "complex"      # 6-10 steps
    ADVANCED = "advanced"    # 10+ steps


@dataclass
class PlanStep:
    """Individual step in an execution plan"""
    step_id: str
    tool_server: ToolServerType
    operation: str
    parameters: Dict[str, Any]
    reason: str
    depends_on: List[str] = None  # Previous step IDs this depends on
    security_level: SecurityLevel = SecurityLevel.MEDIUM
    estimated_time: float = 30.0  # seconds
    timeout: float = 60.0  # seconds
    retry_count: int = 2

    def __post_init__(self):
        if self.depends_on is None:
            self.depends_on = []


@dataclass
class ExecutionPlan:
    """Complete execution plan for a user goal"""
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


class GoalDecomposer:
    """Core goal decomposition engine"""

    def __init__(self):
        self.logger = None  # Will be set during initialization

        # Available tool operations mapped by server type
        self.available_operations = {
            ToolServerType.FILE_SYSTEM: {
                "read_file": {"security": SecurityLevel.LOW, "time": 5},
                "write_file": {"security": SecurityLevel.MEDIUM, "time": 10},
                "create_file": {"security": SecurityLevel.MEDIUM, "time": 8},
                "delete_file": {"security": SecurityLevel.HIGH, "time": 5},
                "copy_file": {"security": SecurityLevel.MEDIUM, "time": 10},
                "move_file": {"security": SecurityLevel.HIGH, "time": 10},
                "list_directory": {"security": SecurityLevel.LOW, "time": 8},
                "create_directory": {"security": SecurityLevel.MEDIUM, "time": 5},
                "delete_directory": {"security": SecurityLevel.HIGH, "time": 15},
                "get_file_info": {"security": SecurityLevel.LOW, "time": 3},
                "search_files": {"security": SecurityLevel.LOW, "time": 20},
                "calculate_checksum": {"security": SecurityLevel.LOW, "time": 10}
            },
            ToolServerType.WEB_SEARCH: {
                "search": {"security": SecurityLevel.LOW, "time": 15},
                "browse_page": {"security": SecurityLevel.MEDIUM, "time": 20},
                "extract_links": {"security": SecurityLevel.MEDIUM, "time": 10},
                "download_file": {"security": SecurityLevel.HIGH, "time": 30},
                "get_page_metadata": {"security": SecurityLevel.LOW, "time": 8},
                "check_url_safety": {"security": SecurityLevel.LOW, "time": 5},
                "search_images": {"security": SecurityLevel.LOW, "time": 12},
                "get_search_suggestions": {"security": SecurityLevel.LOW, "time": 5}
            },
            ToolServerType.CALENDAR: {
                "authenticate": {"security": SecurityLevel.LOW, "time": 30},
                "list_calendars": {"security": SecurityLevel.MEDIUM, "time": 10},
                "get_events": {"security": SecurityLevel.MEDIUM, "time": 15},
                "create_event": {"security": SecurityLevel.HIGH, "time": 20},
                "update_event": {"security": SecurityLevel.HIGH, "time": 15},
                "delete_event": {"security": SecurityLevel.CRITICAL, "time": 10},
                "search_events": {"security": SecurityLevel.MEDIUM, "time": 20},
                "get_availability": {"security": SecurityLevel.MEDIUM, "time": 25},
                "create_meeting": {"security": SecurityLevel.HIGH, "time": 30},
                "send_invitation": {"security": SecurityLevel.HIGH, "time": 15},
                "get_calendar_settings": {"security": SecurityLevel.LOW, "time": 5},
                "set_calendar_permissions": {"security": SecurityLevel.CRITICAL, "time": 20}
            },
            ToolServerType.TASK_MANAGEMENT: {
                "create_task": {"security": SecurityLevel.MEDIUM, "time": 10},
                "update_task": {"security": SecurityLevel.HIGH, "time": 8},
                "delete_task": {"security": SecurityLevel.CRITICAL, "time": 5},
                "get_task": {"security": SecurityLevel.LOW, "time": 5},
                "list_tasks": {"security": SecurityLevel.LOW, "time": 12},
                "search_tasks": {"security": SecurityLevel.LOW, "time": 15},
                "assign_task": {"security": SecurityLevel.HIGH, "time": 8},
                "add_comment": {"security": SecurityLevel.MEDIUM, "time": 5},
                "start_time_tracking": {"security": SecurityLevel.MEDIUM, "time": 5},
                "stop_time_tracking": {"security": SecurityLevel.MEDIUM, "time": 3},
                "create_project": {"security": SecurityLevel.MEDIUM, "time": 15},
                "update_project": {"security": SecurityLevel.HIGH, "time": 10},
                "list_projects": {"security": SecurityLevel.LOW, "time": 8},
                "add_task_dependency": {"security": SecurityLevel.MEDIUM, "time": 10},
                "get_task_history": {"security": SecurityLevel.LOW, "time": 10}
            }
        }

        # Pattern matching for goal categorization
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
            ],
            RequestCategory.COMMUNICATION: [
                r'email|message|send|contact|reach out',
                r'invite|notification|alert',
                r'share|collaborate'
            ],
            RequestCategory.ANALYSIS: [
                r'analyze|compare|review|evaluate',
                r'metrics|data|statistics|performance',
                r'summary|report|insights'
            ]
        }

        # Common goal templates
        self.goal_templates = {
            "presentation_prep": {
                "pattern": r'(prepare|prep).*presentation|presentation.*tomorrow',
                "steps": [
                    ("calendar", "get_events", "Check for presentation details"),
                    ("file", "search_files", "Find presentation files"),
                    ("web", "search", "Research latest information"),
                    ("task", "create_task", "Create preparation checklist")
                ]
            },
            "project_research": {
                "pattern": r'research.*project|project.*research',
                "steps": [
                    ("web", "search", "Initial research"),
                    ("file", "create_directory", "Create research folder"),
                    ("web", "browse_page", "Deep dive into sources"),
                    ("file", "create_file", "Save research notes"),
                    ("task", "create_task", "Track research progress")
                ]
            },
            "meeting_setup": {
                "pattern": r'schedule.*meeting|set up.*meeting|plan.*meeting',
                "steps": [
                    ("calendar", "get_availability", "Check availability"),
                    ("calendar", "create_event", "Create meeting event"),
                    ("calendar", "send_invitation", "Send invitations"),
                    ("task", "create_task", "Add meeting preparation tasks")
                ]
            },
            "file_organization": {
                "pattern": r'organize.*files|clean up.*documents',
                "steps": [
                    ("file", "list_directory", "Survey current files"),
                    ("file", "create_directory", "Create organization structure"),
                    ("file", "move_file", "Move files to appropriate folders"),
                    ("task", "create_task", "Schedule regular cleanup")
                ]
            },
            "task_planning": {
                "pattern": r'plan.*tasks|organize.*work|manage.*project',
                "steps": [
                    ("task", "list_tasks", "Review current tasks"),
                    ("task", "create_project", "Create new project"),
                    ("task", "create_task", "Break down into subtasks"),
                    ("calendar", "create_event", "Schedule work blocks")
                ]
            }
        }

    async def decompose_goal(self,
                           user_goal: str,
                           user_id: Optional[str] = None,
                           context: Optional[Dict[str, Any]] = None) -> ExecutionPlan:
        """
        Main entry point: decompose a user goal into executable steps
        """
        plan_id = f"plan_{int(datetime.now().timestamp())}_{uuid.uuid4().hex[:8]}"

        # Step 1: Categorize the request
        category = self._categorize_request(user_goal)

        # Step 2: Check for template matches
        template_steps = self._match_goal_templates(user_goal)

        # Step 3: Generate steps (template or custom)
        if template_steps:
            steps = await self._generate_steps_from_template(template_steps, user_goal, context)
        else:
            steps = await self._generate_custom_steps(user_goal, category, context)

        # Step 4: Determine complexity
        complexity = self._determine_complexity(steps)

        # Step 5: Calculate timing
        total_time = sum(step.estimated_time for step in steps)

        # Step 6: Add fallback options
        fallback_options = self._generate_fallback_options(user_goal, category)

        return ExecutionPlan(
            plan_id=plan_id,
            user_goal=user_goal,
            category=category,
            complexity=complexity,
            steps=steps,
            total_estimated_time=total_time,
            created_at=datetime.now(),
            user_id=user_id,
            context=context,
            fallback_options=fallback_options
        )

    def _categorize_request(self, user_goal: str) -> RequestCategory:
        """Categorize user request based on pattern matching"""
        user_goal_lower = user_goal.lower()

        category_scores = {}

        for category, patterns in self.category_patterns.items():
            score = 0
            for pattern in patterns:
                if re.search(pattern, user_goal_lower):
                    score += 1
            category_scores[category] = score

        # Find category with highest score
        if category_scores:
            best_category = max(category_scores, key=category_scores.get)
            if category_scores[best_category] > 0:
                return best_category

        return RequestCategory.MIXED

    def _match_goal_templates(self, user_goal: str) -> Optional[List[Tuple[str, str, str]]]:
        """Check if goal matches any predefined templates"""
        user_goal_lower = user_goal.lower()

        for template_name, template_data in self.goal_templates.items():
            if re.search(template_data["pattern"], user_goal_lower):
                return template_data["steps"]

        return None

    async def _generate_steps_from_template(self,
                                          template_steps: List[Tuple[str, str, str]],
                                          user_goal: str,
                                          context: Optional[Dict[str, Any]]) -> List[PlanStep]:
        """Generate plan steps from a template"""
        steps = []

        for i, (server_name, operation, reason) in enumerate(template_steps):
            step_id = f"step_{i+1}"

            # Map server name to ToolServerType
            server_map = {
                "file": ToolServerType.FILE_SYSTEM,
                "web": ToolServerType.WEB_SEARCH,
                "calendar": ToolServerType.CALENDAR,
                "task": ToolServerType.TASK_MANAGEMENT
            }

            tool_server = server_map.get(server_name, ToolServerType.FILE_SYSTEM)

            # Get operation metadata
            op_info = self.available_operations[tool_server].get(operation, {})
            security_level = op_info.get("security", SecurityLevel.MEDIUM)
            estimated_time = op_info.get("time", 30)

            # Generate parameters based on operation and context
            parameters = self._generate_operation_parameters(
                tool_server, operation, user_goal, context
            )

            step = PlanStep(
                step_id=step_id,
                tool_server=tool_server,
                operation=operation,
                parameters=parameters,
                reason=reason,
                depends_on=[f"step_{i}"] if i > 0 else [],
                security_level=security_level,
                estimated_time=estimated_time
            )

            steps.append(step)

        return steps

    async def _generate_custom_steps(self,
                                   user_goal: str,
                                   category: RequestCategory,
                                   context: Optional[Dict[str, Any]]) -> List[PlanStep]:
        """Generate custom steps based on goal analysis"""
        steps = []
        user_goal_lower = user_goal.lower()

        # Analyze goal for key operations needed
        if category == RequestCategory.RESEARCH:
            steps.extend(self._create_research_steps(user_goal, context))

        elif category == RequestCategory.FILE_MANAGEMENT:
            steps.extend(self._create_file_management_steps(user_goal, context))

        elif category == RequestCategory.SCHEDULING:
            steps.extend(self._create_scheduling_steps(user_goal, context))

        elif category == RequestCategory.TASK_ORGANIZATION:
            steps.extend(self._create_task_organization_steps(user_goal, context))

        elif category == RequestCategory.CONTENT_CREATION:
            steps.extend(self._create_content_creation_steps(user_goal, context))

        else:  # MIXED or other categories
            steps.extend(self._create_general_steps(user_goal, context))

        # Ensure we have at least one step
        if not steps:
            steps = [self._create_fallback_step(user_goal)]

        return steps

    def _create_research_steps(self, user_goal: str, context: Optional[Dict[str, Any]]) -> List[PlanStep]:
        """Create steps for research-focused goals"""
        steps = []

        # Extract search terms from goal
        search_terms = self._extract_search_terms(user_goal)

        # Step 1: Web search
        steps.append(PlanStep(
            step_id="step_1",
            tool_server=ToolServerType.WEB_SEARCH,
            operation="search",
            parameters={"query": search_terms, "max_results": 10},
            reason="Conduct initial research",
            security_level=SecurityLevel.LOW,
            estimated_time=15
        ))

        # Step 2: Create research folder if needed
        if "save" in user_goal.lower() or "organize" in user_goal.lower():
            steps.append(PlanStep(
                step_id="step_2",
                tool_server=ToolServerType.FILE_SYSTEM,
                operation="create_directory",
                parameters={"path": f"research_{int(datetime.now().timestamp())}"},
                reason="Create folder for research materials",
                depends_on=["step_1"],
                security_level=SecurityLevel.MEDIUM,
                estimated_time=5
            ))

        # Step 3: Create task to track research
        steps.append(PlanStep(
            step_id=f"step_{len(steps)+1}",
            tool_server=ToolServerType.TASK_MANAGEMENT,
            operation="create_task",
            parameters={
                "task": {
                    "title": f"Research: {search_terms}",
                    "description": f"Research task for: {user_goal}",
                    "priority": "medium"
                }
            },
            reason="Track research progress",
            depends_on=["step_1"],
            security_level=SecurityLevel.MEDIUM,
            estimated_time=10
        ))

        return steps

    def _create_file_management_steps(self, user_goal: str, context: Optional[Dict[str, Any]]) -> List[PlanStep]:
        """Create steps for file management goals"""
        steps = []

        # Determine what kind of file operation is needed
        if "organize" in user_goal.lower() or "clean" in user_goal.lower():
            # Step 1: List current files
            steps.append(PlanStep(
                step_id="step_1",
                tool_server=ToolServerType.FILE_SYSTEM,
                operation="list_directory",
                parameters={"path": "."},
                reason="Survey current files",
                security_level=SecurityLevel.LOW,
                estimated_time=8
            ))

            # Step 2: Create organization structure
            steps.append(PlanStep(
                step_id="step_2",
                tool_server=ToolServerType.FILE_SYSTEM,
                operation="create_directory",
                parameters={"path": "organized_files"},
                reason="Create organization structure",
                depends_on=["step_1"],
                security_level=SecurityLevel.MEDIUM,
                estimated_time=5
            ))

        elif "find" in user_goal.lower() or "search" in user_goal.lower():
            # Extract search pattern
            search_pattern = self._extract_file_pattern(user_goal)

            steps.append(PlanStep(
                step_id="step_1",
                tool_server=ToolServerType.FILE_SYSTEM,
                operation="search_files",
                parameters={"pattern": search_pattern, "recursive": True},
                reason="Search for specified files",
                security_level=SecurityLevel.LOW,
                estimated_time=20
            ))

        return steps

    def _create_scheduling_steps(self, user_goal: str, context: Optional[Dict[str, Any]]) -> List[PlanStep]:
        """Create steps for scheduling goals"""
        steps = []

        # Check if it's about viewing or creating events
        if any(word in user_goal.lower() for word in ["schedule", "create", "book", "plan"]):
            # Creating new event
            steps.append(PlanStep(
                step_id="step_1",
                tool_server=ToolServerType.CALENDAR,
                operation="get_availability",
                parameters=self._extract_time_parameters(user_goal),
                reason="Check availability",
                security_level=SecurityLevel.MEDIUM,
                estimated_time=25
            ))

            steps.append(PlanStep(
                step_id="step_2",
                tool_server=ToolServerType.CALENDAR,
                operation="create_event",
                parameters=self._extract_event_parameters(user_goal),
                reason="Create calendar event",
                depends_on=["step_1"],
                security_level=SecurityLevel.HIGH,
                estimated_time=20
            ))

        else:
            # Viewing existing events
            steps.append(PlanStep(
                step_id="step_1",
                tool_server=ToolServerType.CALENDAR,
                operation="get_events",
                parameters=self._extract_time_parameters(user_goal),
                reason="Check calendar events",
                security_level=SecurityLevel.MEDIUM,
                estimated_time=15
            ))

        return steps

    def _create_task_organization_steps(self, user_goal: str, context: Optional[Dict[str, Any]]) -> List[PlanStep]:
        """Create steps for task organization goals"""
        steps = []

        # Step 1: Review current tasks
        steps.append(PlanStep(
            step_id="step_1",
            tool_server=ToolServerType.TASK_MANAGEMENT,
            operation="list_tasks",
            parameters={"limit": 50},
            reason="Review current tasks",
            security_level=SecurityLevel.LOW,
            estimated_time=12
        ))

        # Step 2: Create new tasks or projects based on goal
        if "project" in user_goal.lower():
            project_name = self._extract_project_name(user_goal)
            steps.append(PlanStep(
                step_id="step_2",
                tool_server=ToolServerType.TASK_MANAGEMENT,
                operation="create_project",
                parameters={"project": {"name": project_name, "description": user_goal}},
                reason="Create new project",
                depends_on=["step_1"],
                security_level=SecurityLevel.MEDIUM,
                estimated_time=15
            ))
        else:
            task_title = self._extract_task_title(user_goal)
            steps.append(PlanStep(
                step_id="step_2",
                tool_server=ToolServerType.TASK_MANAGEMENT,
                operation="create_task",
                parameters={
                    "task": {
                        "title": task_title,
                        "description": user_goal,
                        "priority": self._extract_priority(user_goal)
                    }
                },
                reason="Create new task",
                depends_on=["step_1"],
                security_level=SecurityLevel.MEDIUM,
                estimated_time=10
            ))

        return steps

    def _create_content_creation_steps(self, user_goal: str, context: Optional[Dict[str, Any]]) -> List[PlanStep]:
        """Create steps for content creation goals"""
        steps = []

        content_type = self._extract_content_type(user_goal)

        # Step 1: Research if needed
        if any(word in user_goal.lower() for word in ["research", "latest", "current"]):
            steps.append(PlanStep(
                step_id="step_1",
                tool_server=ToolServerType.WEB_SEARCH,
                operation="search",
                parameters={"query": self._extract_search_terms(user_goal)},
                reason="Research content topics",
                security_level=SecurityLevel.LOW,
                estimated_time=15
            ))

        # Step 2: Create the content file
        file_name = f"{content_type}_{int(datetime.now().timestamp())}.txt"
        step_id = f"step_{len(steps)+1}"

        steps.append(PlanStep(
            step_id=step_id,
            tool_server=ToolServerType.FILE_SYSTEM,
            operation="create_file",
            parameters={
                "path": file_name,
                "content": f"# {content_type.title()}\n\nGoal: {user_goal}\n\n[Content to be added]"
            },
            reason=f"Create {content_type} file",
            depends_on=[steps[-1].step_id] if steps else [],
            security_level=SecurityLevel.MEDIUM,
            estimated_time=8
        ))

        # Step 3: Create task to track content creation
        steps.append(PlanStep(
            step_id=f"step_{len(steps)+1}",
            tool_server=ToolServerType.TASK_MANAGEMENT,
            operation="create_task",
            parameters={
                "task": {
                    "title": f"Complete {content_type}",
                    "description": user_goal,
                    "priority": "medium"
                }
            },
            reason="Track content creation progress",
            depends_on=[step_id],
            security_level=SecurityLevel.MEDIUM,
            estimated_time=10
        ))

        return steps

    def _create_general_steps(self, user_goal: str, context: Optional[Dict[str, Any]]) -> List[PlanStep]:
        """Create general steps for mixed or unclear goals"""
        steps = []

        # Try to find the most relevant operation
        if any(word in user_goal.lower() for word in ["search", "find", "look"]):
            steps.append(PlanStep(
                step_id="step_1",
                tool_server=ToolServerType.WEB_SEARCH,
                operation="search",
                parameters={"query": self._extract_search_terms(user_goal)},
                reason="Search for relevant information",
                security_level=SecurityLevel.LOW,
                estimated_time=15
            ))

        # Always create a task to track the goal
        steps.append(PlanStep(
            step_id=f"step_{len(steps)+1}",
            tool_server=ToolServerType.TASK_MANAGEMENT,
            operation="create_task",
            parameters={
                "task": {
                    "title": user_goal[:50],
                    "description": user_goal,
                    "priority": "medium"
                }
            },
            reason="Track goal progress",
            depends_on=[steps[-1].step_id] if steps else [],
            security_level=SecurityLevel.MEDIUM,
            estimated_time=10
        ))

        return steps

    def _create_fallback_step(self, user_goal: str) -> PlanStep:
        """Create a fallback step when no specific pattern is matched"""
        return PlanStep(
            step_id="step_1",
            tool_server=ToolServerType.TASK_MANAGEMENT,
            operation="create_task",
            parameters={
                "task": {
                    "title": "Review Goal",
                    "description": f"Review and plan: {user_goal}",
                    "priority": "medium"
                }
            },
            reason="Create task to review and plan goal",
            security_level=SecurityLevel.MEDIUM,
            estimated_time=10
        )

    def _generate_operation_parameters(self,
                                     tool_server: ToolServerType,
                                     operation: str,
                                     user_goal: str,
                                     context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate appropriate parameters for an operation"""
        params = {}

        if tool_server == ToolServerType.WEB_SEARCH and operation == "search":
            params["query"] = self._extract_search_terms(user_goal)
            params["max_results"] = 10

        elif tool_server == ToolServerType.FILE_SYSTEM:
            if operation in ["create_file", "write_file"]:
                params["path"] = f"generated_{int(datetime.now().timestamp())}.txt"
                params["content"] = f"Generated for: {user_goal}"
            elif operation in ["search_files"]:
                params["pattern"] = self._extract_file_pattern(user_goal)
                params["recursive"] = True
            elif operation in ["create_directory"]:
                params["path"] = f"folder_{int(datetime.now().timestamp())}"

        elif tool_server == ToolServerType.CALENDAR:
            if operation == "get_events":
                params.update(self._extract_time_parameters(user_goal))
            elif operation == "create_event":
                params.update(self._extract_event_parameters(user_goal))

        elif tool_server == ToolServerType.TASK_MANAGEMENT:
            if operation == "create_task":
                params["task"] = {
                    "title": self._extract_task_title(user_goal),
                    "description": user_goal,
                    "priority": self._extract_priority(user_goal)
                }

        return params

    def _determine_complexity(self, steps: List[PlanStep]) -> PlanningComplexity:
        """Determine the complexity level of the plan"""
        step_count = len(steps)

        if step_count <= 2:
            return PlanningComplexity.SIMPLE
        elif step_count <= 5:
            return PlanningComplexity.MODERATE
        elif step_count <= 10:
            return PlanningComplexity.COMPLEX
        else:
            return PlanningComplexity.ADVANCED

    def _generate_fallback_options(self, user_goal: str, category: RequestCategory) -> List[str]:
        """Generate fallback options if the main plan fails"""
        fallbacks = []

        fallbacks.append("Create a task to manually handle this request")
        fallbacks.append("Search for tutorials or guides on this topic")

        if category == RequestCategory.RESEARCH:
            fallbacks.append("Try alternative search terms or engines")
            fallbacks.append("Look for academic or official sources")

        elif category == RequestCategory.FILE_MANAGEMENT:
            fallbacks.append("Use system file manager for manual organization")
            fallbacks.append("Create a backup before making changes")

        elif category == RequestCategory.SCHEDULING:
            fallbacks.append("Check calendar manually and suggest times")
            fallbacks.append("Send calendar invites directly via email")

        return fallbacks

    # Helper methods for parameter extraction
    def _extract_search_terms(self, user_goal: str) -> str:
        """Extract search terms from user goal"""
        # Remove common action words and extract key terms
        stop_words = {"help", "me", "can", "you", "please", "find", "search", "look", "for"}
        words = user_goal.lower().split()
        key_words = [w for w in words if w not in stop_words and len(w) > 2]
        return " ".join(key_words) if key_words else user_goal

    def _extract_file_pattern(self, user_goal: str) -> str:
        """Extract file search pattern from user goal"""
        # Look for specific file extensions or patterns
        if ".*" in user_goal or "*." in user_goal:
            return user_goal.split()[-1]  # Assume last word is pattern
        elif any(ext in user_goal.lower() for ext in [".txt", ".pdf", ".doc", ".py"]):
            for word in user_goal.split():
                if "." in word:
                    return f"*{word}"
        return "*.txt"  # Default pattern

    def _extract_time_parameters(self, user_goal: str) -> Dict[str, Any]:
        """Extract time-related parameters from user goal"""
        params = {}

        if "tomorrow" in user_goal.lower():
            tomorrow = datetime.now() + timedelta(days=1)
            params["start_date"] = tomorrow.strftime("%Y-%m-%d")
            params["end_date"] = tomorrow.strftime("%Y-%m-%d")
        elif "next week" in user_goal.lower():
            next_week = datetime.now() + timedelta(weeks=1)
            params["start_date"] = next_week.strftime("%Y-%m-%d")
            params["end_date"] = (next_week + timedelta(days=7)).strftime("%Y-%m-%d")
        else:
            # Default to today
            today = datetime.now()
            params["start_date"] = today.strftime("%Y-%m-%d")
            params["end_date"] = today.strftime("%Y-%m-%d")

        return params

    def _extract_event_parameters(self, user_goal: str) -> Dict[str, Any]:
        """Extract event parameters from user goal"""
        return {
            "service": "google",  # Default service
            "calendar_id": "primary",
            "event": {
                "title": self._extract_event_title(user_goal),
                "description": user_goal,
                "start_time": (datetime.now() + timedelta(days=1)).isoformat(),
                "end_time": (datetime.now() + timedelta(days=1, hours=1)).isoformat()
            }
        }

    def _extract_event_title(self, user_goal: str) -> str:
        """Extract event title from user goal"""
        # Simple extraction - take first few meaningful words
        words = user_goal.split()
        if len(words) > 3:
            return " ".join(words[:4])
        return user_goal

    def _extract_task_title(self, user_goal: str) -> str:
        """Extract task title from user goal"""
        # Similar to event title but shorter
        words = user_goal.split()
        if len(words) > 5:
            return " ".join(words[:5])
        return user_goal

    def _extract_priority(self, user_goal: str) -> str:
        """Extract priority level from user goal"""
        user_goal_lower = user_goal.lower()

        if any(word in user_goal_lower for word in ["urgent", "asap", "immediately", "critical"]):
            return "urgent"
        elif any(word in user_goal_lower for word in ["important", "high", "priority"]):
            return "high"
        elif any(word in user_goal_lower for word in ["low", "later", "sometime"]):
            return "low"
        else:
            return "medium"

    def _extract_project_name(self, user_goal: str) -> str:
        """Extract project name from user goal"""
        # Look for project-related keywords and extract name
        words = user_goal.split()
        for i, word in enumerate(words):
            if word.lower() in ["project", "plan", "organize"]:
                if i + 1 < len(words):
                    return " ".join(words[i+1:i+3])  # Take next 1-2 words
        return "New Project"

    def _extract_content_type(self, user_goal: str) -> str:
        """Extract type of content to create"""
        user_goal_lower = user_goal.lower()

        content_types = {
            "presentation": ["presentation", "slides", "deck"],
            "report": ["report", "document", "analysis"],
            "email": ["email", "message", "letter"],
            "notes": ["notes", "summary", "outline"],
            "proposal": ["proposal", "plan", "suggestion"]
        }

        for content_type, keywords in content_types.items():
            if any(keyword in user_goal_lower for keyword in keywords):
                return content_type

        return "document"

    def get_plan_summary(self, plan: ExecutionPlan) -> Dict[str, Any]:
        """Generate a human-readable summary of the execution plan"""
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
            ],
            "fallback_options": plan.fallback_options
        }

    def validate_plan(self, plan: ExecutionPlan) -> Dict[str, Any]:
        """Validate that a plan is executable with available operations"""
        validation_results = {
            "valid": True,
            "errors": [],
            "warnings": []
        }

        for step in plan.steps:
            # Check if operation exists
            if step.tool_server not in self.available_operations:
                validation_results["valid"] = False
                validation_results["errors"].append(
                    f"Unknown tool server: {step.tool_server.value}"
                )
                continue

            if step.operation not in self.available_operations[step.tool_server]:
                validation_results["valid"] = False
                validation_results["errors"].append(
                    f"Unknown operation: {step.operation} for {step.tool_server.value}"
                )
                continue

            # Check dependencies
            for dep_id in step.depends_on:
                if not any(s.step_id == dep_id for s in plan.steps):
                    validation_results["valid"] = False
                    validation_results["errors"].append(
                        f"Step {step.step_id} depends on non-existent step {dep_id}"
                    )

            # Warnings for high-risk operations
            if step.security_level in [SecurityLevel.HIGH, SecurityLevel.CRITICAL]:
                validation_results["warnings"].append(
                    f"Step {step.step_id} ({step.operation}) requires {step.security_level.value} security level"
                )

        return validation_results


# Convenience function for easy usage
async def decompose_user_goal(user_goal: str,
                            user_id: Optional[str] = None,
                            context: Optional[Dict[str, Any]] = None) -> ExecutionPlan:
    """
    Convenience function to decompose a user goal into an execution plan
    """
    decomposer = GoalDecomposer()
    return await decomposer.decompose_goal(user_goal, user_id, context)