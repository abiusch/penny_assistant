#!/usr/bin/env python3
"""
Interactive Debugging Assistant
Claude's step-by-step debugging methodology implemented for Penny
"""

import os
import ast
import re
import sys
import json
import asyncio
import traceback
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

@dataclass
class DebugStep:
    """Represents a single debugging step"""
    step_number: int
    description: str
    action: str
    expected_result: str
    actual_result: Optional[str] = None
    issues_found: List[str] = None
    suggestions: List[str] = None

@dataclass
class ExecutionPath:
    """Represents a traced execution path"""
    entry_point: str
    steps: List[str]
    variables_at_step: Dict[str, Any]
    potential_failures: List[str]
    suggested_breakpoints: List[str]

@dataclass
class DebugPlan:
    """Complete debugging plan and analysis"""
    problem_understanding: Dict[str, Any]
    reproduction_steps: List[str]
    isolation_strategy: Dict[str, Any]
    execution_trace: ExecutionPath
    root_cause_analysis: Dict[str, Any]
    proposed_solutions: List[Dict[str, Any]]
    verification_steps: List[str]
    prevention_measures: List[str]

class InteractiveDebugger:
    """
    Claude's debugging methodology:
    1. Problem Reproduction - Understand exactly what's happening
    2. Issue Isolation - Narrow to specific components/functions
    3. Execution Tracing - Step through code path systematically
    4. Assumption Verification - Check inputs, outputs, state at each step
    5. Side Effect Analysis - Look for unintended interactions
    """

    def __init__(self, code_analyzer=None):
        self.code_analyzer = code_analyzer
        self.debugging_strategies = [
            "reproduce_issue",
            "isolate_problem",
            "trace_execution",
            "verify_assumptions",
            "check_side_effects"
        ]

        # Common error patterns and their solutions
        self.error_patterns = {
            "AttributeError": {
                "common_causes": ["None value", "wrong object type", "missing attribute"],
                "investigation_steps": ["Check object initialization", "Verify object type", "Trace variable assignment"],
                "typical_solutions": ["Add null checks", "Initialize objects properly", "Use hasattr() checks"]
            },
            "KeyError": {
                "common_causes": ["Missing dictionary key", "typo in key name", "dynamic key generation"],
                "investigation_steps": ["Print dictionary contents", "Check key generation logic", "Verify data source"],
                "typical_solutions": ["Use dict.get() with defaults", "Add key existence checks", "Validate input data"]
            },
            "ImportError": {
                "common_causes": ["Missing dependency", "wrong import path", "circular imports"],
                "investigation_steps": ["Check installed packages", "Verify file paths", "Look for circular dependencies"],
                "typical_solutions": ["Install missing packages", "Fix import paths", "Restructure to avoid circular imports"]
            },
            "TypeError": {
                "common_causes": ["Wrong argument types", "calling non-callable", "incompatible operations"],
                "investigation_steps": ["Check function signatures", "Verify argument types", "Trace variable types"],
                "typical_solutions": ["Add type checking", "Convert types properly", "Use type hints"]
            },
            "IndexError": {
                "common_causes": ["Empty list/array", "off-by-one error", "dynamic index calculation"],
                "investigation_steps": ["Check list length", "Verify index calculations", "Trace loop boundaries"],
                "typical_solutions": ["Add bounds checking", "Use enumerate()", "Handle empty collections"]
            },
            "FileNotFoundError": {
                "common_causes": ["Wrong file path", "file doesn't exist", "permission issues"],
                "investigation_steps": ["Check file existence", "Verify path construction", "Check permissions"],
                "typical_solutions": ["Use absolute paths", "Add file existence checks", "Handle missing files gracefully"]
            }
        }

        # Performance issue patterns
        self.performance_patterns = {
            "slow_response": {
                "likely_causes": ["Database N+1 queries", "blocking I/O", "inefficient algorithms", "memory leaks"],
                "investigation_areas": ["Database queries", "API calls", "loop complexity", "memory usage"]
            },
            "memory_leak": {
                "likely_causes": ["Circular references", "unclosed resources", "growing caches", "event listeners"],
                "investigation_areas": ["Object lifecycle", "Resource cleanup", "Cache management", "Event handling"]
            },
            "high_cpu": {
                "likely_causes": ["Infinite loops", "inefficient algorithms", "excessive recursion", "CPU-bound operations"],
                "investigation_areas": ["Loop conditions", "Algorithm complexity", "Recursion depth", "Processing logic"]
            }
        }

    async def debug_issue(self, error_description: str, relevant_files: List[str],
                         error_traceback: Optional[str] = None) -> DebugPlan:
        """
        Step-by-step debugging like Claude's approach
        """
        print(f"🔍 Starting debugging analysis for: {error_description}")

        # Step 1: Understand the problem
        understanding = await self.understand_problem(error_description, error_traceback)
        print(f"📋 Problem categorized as: {understanding['error_type']}")

        # Step 2: Create reproduction strategy
        reproduction_steps = await self.create_reproduction_steps(error_description, understanding)
        print(f"🔬 Generated {len(reproduction_steps)} reproduction steps")

        # Step 3: Isolation strategy
        isolation = await self.create_isolation_strategy(relevant_files, understanding)
        print(f"🎯 Isolation strategy targets {len(isolation['focus_areas'])} areas")

        # Step 4: Trace execution path
        execution_trace = await self.trace_execution_path(relevant_files, understanding)
        print(f"📊 Traced execution through {len(execution_trace.steps)} steps")

        # Step 5: Root cause analysis
        root_cause = await self.analyze_root_cause(understanding, isolation, execution_trace)
        print(f"🎯 Root cause analysis: {root_cause['primary_cause']}")

        # Step 6: Propose solutions
        solutions = await self.propose_solutions(understanding, root_cause, relevant_files)
        print(f"💡 Generated {len(solutions)} solution approaches")

        # Step 7: Verification steps
        verification_steps = await self.create_verification_steps(solutions)

        # Step 8: Prevention measures
        prevention_measures = await self.suggest_prevention_measures(understanding, root_cause)

        return DebugPlan(
            problem_understanding=understanding,
            reproduction_steps=reproduction_steps,
            isolation_strategy=isolation,
            execution_trace=execution_trace,
            root_cause_analysis=root_cause,
            proposed_solutions=solutions,
            verification_steps=verification_steps,
            prevention_measures=prevention_measures
        )

    async def understand_problem(self, description: str, traceback_text: Optional[str] = None) -> Dict[str, Any]:
        """
        First step: Really understand what's happening
        """
        understanding = {
            "description": description,
            "error_type": "unknown",
            "severity": "medium",
            "likely_causes": [],
            "investigation_focus": [],
            "similar_issues": [],
            "context_clues": []
        }

        # Analyze error description for clues
        desc_lower = description.lower()

        # Categorize error type
        if any(keyword in desc_lower for keyword in ['crash', 'exception', 'error', 'fail']):
            understanding["error_type"] = "runtime_error"
            understanding["severity"] = "high"
        elif any(keyword in desc_lower for keyword in ['slow', 'hang', 'timeout', 'performance']):
            understanding["error_type"] = "performance_issue"
            understanding["severity"] = "medium"
        elif any(keyword in desc_lower for keyword in ['wrong', 'incorrect', 'unexpected', 'logic']):
            understanding["error_type"] = "logic_error"
            understanding["severity"] = "medium"
        elif any(keyword in desc_lower for keyword in ['ui', 'display', 'render', 'visual']):
            understanding["error_type"] = "ui_issue"
            understanding["severity"] = "low"

        # Extract context clues from description
        if 'when' in desc_lower:
            understanding["context_clues"].append("Conditional occurrence - look for specific triggers")
        if 'sometimes' in desc_lower or 'occasionally' in desc_lower:
            understanding["context_clues"].append("Intermittent issue - race condition or state-dependent")
        if 'after' in desc_lower:
            understanding["context_clues"].append("Sequential dependency - check operation ordering")

        # Analyze traceback if provided
        if traceback_text:
            traceback_analysis = self._analyze_traceback(traceback_text)
            understanding["error_type"] = traceback_analysis["error_type"]
            understanding["likely_causes"] = traceback_analysis["likely_causes"]
            understanding["investigation_focus"] = traceback_analysis["focus_areas"]

        # Add general investigation areas based on error type
        error_investigations = {
            "runtime_error": ["Exception handling", "Input validation", "Object initialization", "Resource availability"],
            "performance_issue": ["Algorithm efficiency", "Database queries", "I/O operations", "Memory usage"],
            "logic_error": ["Business logic", "Conditional statements", "Data transformations", "State management"],
            "ui_issue": ["Template rendering", "CSS styling", "JavaScript execution", "Data binding"]
        }

        understanding["investigation_focus"].extend(
            error_investigations.get(understanding["error_type"], ["General code review"])
        )

        return understanding

    def _analyze_traceback(self, traceback_text: str) -> Dict[str, Any]:
        """Analyze Python traceback for specific error patterns"""
        analysis = {
            "error_type": "runtime_error",
            "likely_causes": [],
            "focus_areas": [],
            "exception_type": None,
            "error_location": None
        }

        # Extract exception type
        lines = traceback_text.strip().split('\n')
        if lines:
            last_line = lines[-1]
            if ':' in last_line:
                exception_type = last_line.split(':')[0].strip()
                analysis["exception_type"] = exception_type

                # Use our error pattern knowledge
                if exception_type in self.error_patterns:
                    pattern_info = self.error_patterns[exception_type]
                    analysis["likely_causes"] = pattern_info["common_causes"]
                    analysis["focus_areas"] = pattern_info["investigation_steps"]

        # Extract error location
        for line in lines:
            if 'File "' in line and 'line' in line:
                analysis["error_location"] = line.strip()
                break

        return analysis

    async def create_reproduction_steps(self, description: str, understanding: Dict) -> List[str]:
        """Create steps to reproduce the issue reliably"""
        steps = []

        # Basic reproduction framework
        steps.append("1. Document exact environment (Python version, dependencies, OS)")
        steps.append("2. Create minimal test case that triggers the issue")

        # Add specific steps based on error type
        error_type = understanding["error_type"]

        if error_type == "runtime_error":
            steps.extend([
                "3. Identify exact input that causes the error",
                "4. Check if error occurs consistently or intermittently",
                "5. Test with different input variations to find patterns"
            ])
        elif error_type == "performance_issue":
            steps.extend([
                "3. Measure baseline performance with profiling tools",
                "4. Test with different data sizes to identify scaling issues",
                "5. Monitor resource usage (CPU, memory, I/O) during execution"
            ])
        elif error_type == "logic_error":
            steps.extend([
                "3. Create test cases with known expected outputs",
                "4. Test edge cases and boundary conditions",
                "5. Trace variable values at key decision points"
            ])

        # Add context-specific steps
        if "sometimes" in description.lower():
            steps.append("6. Run multiple iterations to identify conditions that trigger the issue")

        if "after" in description.lower():
            steps.append("6. Document the exact sequence of operations leading to the issue")

        return steps

    async def create_isolation_strategy(self, relevant_files: List[str], understanding: Dict) -> Dict[str, Any]:
        """Develop strategy to isolate the problem to specific components"""
        strategy = {
            "focus_areas": [],
            "elimination_order": [],
            "testing_approach": [],
            "monitoring_points": []
        }

        # Prioritize files based on likely relevance
        prioritized_files = await self._prioritize_files_for_debugging(relevant_files, understanding)
        strategy["focus_areas"] = prioritized_files[:5]  # Top 5 most relevant

        # Create elimination strategy
        strategy["elimination_order"] = [
            "Test individual components in isolation",
            "Remove external dependencies (mock/stub)",
            "Simplify data inputs to minimal test cases",
            "Disable non-essential features temporarily",
            "Test with different configurations"
        ]

        # Determine testing approach based on error type
        error_type = understanding["error_type"]
        if error_type == "runtime_error":
            strategy["testing_approach"] = [
                "Unit tests for individual functions",
                "Integration tests for component interactions",
                "Error boundary testing with invalid inputs"
            ]
        elif error_type == "performance_issue":
            strategy["testing_approach"] = [
                "Performance profiling with different workloads",
                "Memory usage monitoring",
                "Database query analysis",
                "I/O operation timing"
            ]

        # Set up monitoring points
        strategy["monitoring_points"] = [
            "Function entry and exit points",
            "Variable state at critical junctions",
            "External API call results",
            "Database query execution times",
            "Error handling paths"
        ]

        return strategy

    async def trace_execution_path(self, relevant_files: List[str], understanding: Dict) -> ExecutionPath:
        """Trace the execution path to understand program flow"""
        execution_path = ExecutionPath(
            entry_point="",
            steps=[],
            variables_at_step={},
            potential_failures=[],
            suggested_breakpoints=[]
        )

        # Identify likely entry point
        entry_points = [f for f in relevant_files if any(name in f.lower() for name in ['main', 'app', 'run'])]
        if entry_points:
            execution_path.entry_point = entry_points[0]
        elif relevant_files:
            execution_path.entry_point = relevant_files[0]

        # Analyze execution flow
        if execution_path.entry_point and os.path.exists(execution_path.entry_point):
            try:
                flow_analysis = await self._analyze_execution_flow(execution_path.entry_point)
                execution_path.steps = flow_analysis["steps"]
                execution_path.potential_failures = flow_analysis["failure_points"]
                execution_path.suggested_breakpoints = flow_analysis["breakpoints"]
            except Exception as e:
                print(f"⚠️ Error analyzing execution flow: {e}")
                execution_path.steps = ["Manual code review required"]

        return execution_path

    async def _analyze_execution_flow(self, file_path: str) -> Dict:
        """Analyze execution flow through a Python file"""
        flow_info = {
            "steps": [],
            "failure_points": [],
            "breakpoints": []
        }

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Parse AST for function calls and control flow
            tree = ast.parse(content)

            # Track function definitions and calls
            functions_defined = []
            function_calls = []
            conditional_blocks = []
            exception_handlers = []

            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    functions_defined.append(node.name)
                    flow_info["breakpoints"].append(f"Function entry: {node.name} (line {node.lineno})")

                elif isinstance(node, ast.Call) and hasattr(node.func, 'id'):
                    function_calls.append(node.func.id)

                elif isinstance(node, ast.If):
                    conditional_blocks.append(f"Conditional at line {node.lineno}")
                    flow_info["failure_points"].append(f"Conditional logic at line {node.lineno}")

                elif isinstance(node, ast.Try):
                    exception_handlers.append(f"Exception handler at line {node.lineno}")
                    flow_info["breakpoints"].append(f"Exception handler: line {node.lineno}")

                elif isinstance(node, ast.For) or isinstance(node, ast.While):
                    flow_info["failure_points"].append(f"Loop at line {node.lineno} - check termination conditions")
                    flow_info["breakpoints"].append(f"Loop entry: line {node.lineno}")

            # Build execution steps
            flow_info["steps"] = [
                f"File initialization: {os.path.basename(file_path)}",
                f"Functions defined: {', '.join(functions_defined) if functions_defined else 'None'}",
                f"External function calls: {len(set(function_calls))} unique calls",
                f"Conditional branches: {len(conditional_blocks)}",
                f"Exception handlers: {len(exception_handlers)}"
            ]

        except Exception as e:
            flow_info["steps"] = [f"Error parsing file: {e}"]

        return flow_info

    async def _prioritize_files_for_debugging(self, files: List[str], understanding: Dict) -> List[str]:
        """Prioritize files based on debugging relevance"""
        scored_files = []

        for file_path in files:
            score = 0
            file_name = os.path.basename(file_path).lower()

            # Score based on file type and name
            if any(keyword in file_name for keyword in ['main', 'app', 'core', 'engine']):
                score += 5

            if understanding["error_type"] == "runtime_error":
                if any(keyword in file_name for keyword in ['error', 'exception', 'handler']):
                    score += 3
            elif understanding["error_type"] == "performance_issue":
                if any(keyword in file_name for keyword in ['process', 'query', 'cache', 'optimize']):
                    score += 3

            # Check if file contains likely error-related code
            try:
                if file_path.endswith('.py') and os.path.exists(file_path):
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read().lower()

                    # Look for error handling
                    if 'try:' in content and 'except' in content:
                        score += 2

                    # Look for logging
                    if any(keyword in content for keyword in ['log', 'print', 'debug']):
                        score += 1

                    # Look for the specific error mentioned
                    for cause in understanding.get("likely_causes", []):
                        if cause.lower() in content:
                            score += 2

            except Exception:
                pass  # Skip files we can't read

            scored_files.append((file_path, score))

        # Sort by score and return file paths
        scored_files.sort(key=lambda x: x[1], reverse=True)
        return [file_path for file_path, score in scored_files]

    async def analyze_root_cause(self, understanding: Dict, isolation: Dict, execution_trace: ExecutionPath) -> Dict[str, Any]:
        """Analyze the root cause like Claude's systematic approach"""
        analysis = {
            "primary_cause": "unknown",
            "contributing_factors": [],
            "evidence": [],
            "confidence": 0.0,
            "alternative_theories": []
        }

        error_type = understanding["error_type"]
        likely_causes = understanding.get("likely_causes", [])

        # Synthesize information from all sources
        if likely_causes:
            analysis["primary_cause"] = likely_causes[0]
            analysis["contributing_factors"] = likely_causes[1:]
            analysis["confidence"] = 0.7

        # Look for evidence in execution trace
        if execution_trace.potential_failures:
            analysis["evidence"].extend([f"Execution trace: {failure}" for failure in execution_trace.potential_failures])

        # Add evidence from focus areas
        for area in isolation["focus_areas"]:
            analysis["evidence"].append(f"Focus area identified: {os.path.basename(area)}")

        # Generate alternative theories based on error type
        if error_type == "runtime_error":
            analysis["alternative_theories"] = [
                "Input validation failure",
                "Race condition in concurrent code",
                "Resource exhaustion (memory/file handles)",
                "Configuration or environment issue"
            ]
        elif error_type == "performance_issue":
            analysis["alternative_theories"] = [
                "Database query inefficiency",
                "Algorithmic complexity issue",
                "Memory leak or excessive allocation",
                "I/O bottleneck or blocking operations"
            ]

        # Adjust confidence based on available evidence
        evidence_count = len(analysis["evidence"])
        if evidence_count >= 3:
            analysis["confidence"] = min(0.9, analysis["confidence"] + 0.2)
        elif evidence_count == 0:
            analysis["confidence"] = max(0.3, analysis["confidence"] - 0.2)

        return analysis

    async def propose_solutions(self, understanding: Dict, root_cause: Dict, relevant_files: List[str]) -> List[Dict[str, Any]]:
        """Propose solutions based on root cause analysis"""
        solutions = []

        primary_cause = root_cause["primary_cause"]
        error_type = understanding["error_type"]

        # Get solution templates based on error type and cause
        if primary_cause in self.error_patterns:
            pattern_solutions = self.error_patterns[primary_cause]["typical_solutions"]
            for solution in pattern_solutions:
                solutions.append({
                    "approach": solution,
                    "complexity": "medium",
                    "implementation_steps": await self._generate_implementation_steps(solution, relevant_files),
                    "testing_strategy": await self._generate_testing_strategy(solution),
                    "risks": await self._identify_solution_risks(solution),
                    "estimated_effort": "2-4 hours"
                })

        # Add error-type specific solutions
        if error_type == "performance_issue":
            solutions.append({
                "approach": "Profile and optimize critical paths",
                "complexity": "high",
                "implementation_steps": [
                    "Add performance profiling to identify bottlenecks",
                    "Implement caching for expensive operations",
                    "Optimize database queries and indexes",
                    "Consider asynchronous processing for I/O operations"
                ],
                "testing_strategy": ["Performance benchmarks", "Load testing", "Memory profiling"],
                "risks": ["May introduce complexity", "Could affect code readability"],
                "estimated_effort": "1-2 days"
            })

        # Add preventive solutions
        solutions.append({
            "approach": "Implement comprehensive error handling and monitoring",
            "complexity": "medium",
            "implementation_steps": [
                "Add structured logging at key points",
                "Implement error boundaries and graceful degradation",
                "Add health checks and monitoring",
                "Create automated tests for error scenarios"
            ],
            "testing_strategy": ["Error injection testing", "Monitoring validation", "Alert testing"],
            "risks": ["Increased code complexity", "Performance overhead from logging"],
            "estimated_effort": "4-6 hours"
        })

        return solutions

    async def _generate_implementation_steps(self, solution: str, files: List[str]) -> List[str]:
        """Generate specific implementation steps for a solution"""
        steps = []

        if "null checks" in solution.lower():
            steps = [
                "Identify variables that could be None",
                "Add 'if variable is not None:' checks before usage",
                "Use 'variable or default_value' patterns where appropriate",
                "Consider using Optional type hints"
            ]
        elif "type checking" in solution.lower():
            steps = [
                "Add isinstance() checks for critical parameters",
                "Implement type validation at function entry points",
                "Add type hints to function signatures",
                "Use mypy or similar tools for static type checking"
            ]
        elif "error handling" in solution.lower():
            steps = [
                "Wrap risky operations in try-catch blocks",
                "Define specific exception types for different error cases",
                "Implement proper error logging with context",
                "Add user-friendly error messages"
            ]

        if not steps:
            steps = [f"Implement {solution}", "Add tests for the implementation", "Update documentation"]

        return steps

    async def _generate_testing_strategy(self, solution: str) -> List[str]:
        """Generate testing strategy for a solution"""
        strategies = [
            "Unit tests for the specific fix",
            "Integration tests for component interaction",
            "Regression tests to ensure fix doesn't break existing functionality"
        ]

        if "performance" in solution.lower():
            strategies.append("Performance benchmarks before and after")

        if "error" in solution.lower():
            strategies.append("Error injection tests to verify error handling")

        return strategies

    async def _identify_solution_risks(self, solution: str) -> List[str]:
        """Identify potential risks of implementing a solution"""
        risks = []

        if "type checking" in solution.lower():
            risks = ["May reject previously valid inputs", "Could impact performance"]
        elif "error handling" in solution.lower():
            risks = ["May mask underlying issues", "Could change application behavior"]
        elif "optimization" in solution.lower():
            risks = ["May introduce bugs", "Could affect code maintainability"]

        if not risks:
            risks = ["May have unintended side effects", "Requires thorough testing"]

        return risks

    async def create_verification_steps(self, solutions: List[Dict]) -> List[str]:
        """Create steps to verify that solutions work"""
        steps = [
            "1. Implement the chosen solution in a feature branch",
            "2. Run the original reproduction steps to confirm fix",
            "3. Execute the full test suite to check for regressions",
            "4. Perform manual testing of related functionality",
            "5. Monitor logs and metrics after deployment"
        ]

        # Add solution-specific verification
        if any("performance" in sol["approach"].lower() for sol in solutions):
            steps.append("6. Compare performance metrics before and after fix")

        if any("error" in sol["approach"].lower() for sol in solutions):
            steps.append("6. Test error scenarios to verify graceful handling")

        return steps

    async def suggest_prevention_measures(self, understanding: Dict, root_cause: Dict) -> List[str]:
        """Suggest measures to prevent similar issues in the future"""
        measures = []

        error_type = understanding["error_type"]

        if error_type == "runtime_error":
            measures = [
                "Implement comprehensive input validation",
                "Add more unit tests, especially for edge cases",
                "Use static analysis tools (mypy, pylint)",
                "Implement code review checklist for common errors",
                "Add automated testing for error scenarios"
            ]
        elif error_type == "performance_issue":
            measures = [
                "Set up continuous performance monitoring",
                "Implement performance budgets and alerts",
                "Add regular performance testing to CI/CD",
                "Document performance expectations",
                "Regular code profiling and optimization reviews"
            ]
        elif error_type == "logic_error":
            measures = [
                "Increase test coverage, especially for business logic",
                "Implement property-based testing for complex logic",
                "Add code review focus on logic correctness",
                "Document expected behavior clearly",
                "Use pair programming for complex features"
            ]

        # General prevention measures
        measures.extend([
            "Implement structured logging for better observability",
            "Set up automated monitoring and alerting",
            "Regular code quality reviews and refactoring",
            "Maintain up-to-date documentation",
            "Establish incident post-mortem process"
        ])

        return measures

    async def interactive_debug_session(self, issue_description: str, files: List[str]) -> str:
        """Run an interactive debugging session with step-by-step guidance"""
        print(f"\n🔍 INTERACTIVE DEBUGGING SESSION")
        print(f"Issue: {issue_description}")
        print("=" * 50)

        # Generate debug plan
        debug_plan = await self.debug_issue(issue_description, files)

        # Format response for interactive use
        response = f"**🔍 Debugging Analysis Complete!**\n\n"

        response += f"**Problem Type:** {debug_plan.problem_understanding['error_type']}\n"
        response += f"**Severity:** {debug_plan.problem_understanding['severity']}\n\n"

        response += f"**🎯 Most Likely Cause:** {debug_plan.root_cause_analysis['primary_cause']}\n\n"

        response += f"**📋 Step-by-Step Investigation:**\n"
        for i, step in enumerate(debug_plan.reproduction_steps[:5], 1):
            response += f"{i}. {step}\n"

        response += f"\n**🔧 Recommended Solution:**\n"
        if debug_plan.proposed_solutions:
            best_solution = debug_plan.proposed_solutions[0]
            response += f"**Approach:** {best_solution['approach']}\n"
            response += f"**Complexity:** {best_solution['complexity']}\n"
            response += f"**Estimated Effort:** {best_solution['estimated_effort']}\n\n"

            response += f"**Implementation Steps:**\n"
            for i, step in enumerate(best_solution['implementation_steps'], 1):
                response += f"{i}. {step}\n"

        response += f"\n**✅ Verification:**\n"
        for i, step in enumerate(debug_plan.verification_steps[:3], 1):
            response += f"{i}. {step}\n"

        return response


if __name__ == "__main__":
    async def main():
        debugger = InteractiveDebugger()

        # Test debugging scenarios
        test_scenarios = [
            {
                "description": "Research pipeline sometimes returns empty results even when Brave Search succeeds",
                "files": ["research_first_pipeline.py", "factual_research_manager.py", "brave_search_api.py"],
                "traceback": None
            },
            {
                "description": "Memory system crashes with AttributeError when accessing conversation history",
                "files": ["memory_system.py", "emotional_memory_system.py"],
                "traceback": "AttributeError: 'NoneType' object has no attribute 'get'"
            }
        ]

        for scenario in test_scenarios:
            print(f"\n{'='*60}")
            print(f"DEBUGGING SCENARIO: {scenario['description']}")
            print(f"{'='*60}")

            debug_plan = await debugger.debug_issue(
                scenario["description"],
                scenario["files"],
                scenario["traceback"]
            )

            print(f"\n🎯 Root Cause: {debug_plan.root_cause_analysis['primary_cause']}")
            print(f"🔧 Best Solution: {debug_plan.proposed_solutions[0]['approach'] if debug_plan.proposed_solutions else 'Manual investigation needed'}")
            print(f"⏱️ Estimated Effort: {debug_plan.proposed_solutions[0]['estimated_effort'] if debug_plan.proposed_solutions else 'Unknown'}")

    asyncio.run(main())