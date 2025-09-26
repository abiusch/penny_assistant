#!/usr/bin/env python3
"""
Educational Code Review System
Claude's educational code review methodology for learning-focused feedback
"""

import os
import ast
import re
import sys
import json
import asyncio
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
from collections import defaultdict

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

@dataclass
class CodeIssue:
    """Represents a code issue found during review"""
    severity: str  # critical, major, minor, suggestion
    category: str  # security, performance, maintainability, style, etc.
    description: str
    file_path: str
    line_number: Optional[int]
    code_snippet: str
    explanation: str
    suggested_fix: str
    learning_note: str
    examples: List[str] = None

@dataclass
class DesignPatternUsage:
    """Represents usage of a design pattern"""
    pattern_name: str
    implementation_quality: str  # excellent, good, needs_improvement, incorrect
    file_path: str
    explanation: str
    educational_notes: List[str]
    improvement_suggestions: List[str]
    examples_of_better_usage: List[str]

@dataclass
class CodeReview:
    """Complete code review results"""
    overall_assessment: Dict[str, Any]
    code_quality_score: float
    issues_found: List[CodeIssue]
    pattern_analysis: List[DesignPatternUsage]
    best_practices_review: Dict[str, Any]
    security_review: Dict[str, Any]
    performance_review: Dict[str, Any]
    maintainability_assessment: Dict[str, Any]
    educational_highlights: List[str]
    learning_recommendations: List[str]
    positive_aspects: List[str]
    areas_for_improvement: List[str]

class CodeReviewMentor:
    """
    Claude's educational code review approach:
    1. Educational Explanations - Explain WHY, not just WHAT
    2. Pattern Teaching - Point out design patterns and architectural decisions
    3. Best Practice Guidance - Suggest improvements from real experience
    4. Context Consideration - Tailor advice to project needs
    """

    def __init__(self):
        self.review_aspects = [
            "code_quality",
            "design_patterns",
            "performance",
            "security",
            "maintainability",
            "testing",
            "documentation"
        ]

        # Best practices database
        self.best_practices = {
            "python": {
                "naming": {
                    "functions": "snake_case for functions and variables",
                    "classes": "PascalCase for classes",
                    "constants": "UPPER_CASE for constants",
                    "private": "Leading underscore for private members"
                },
                "structure": {
                    "imports": "Group imports: standard library, third-party, local",
                    "functions": "Keep functions small and focused (under 20 lines)",
                    "classes": "Single responsibility principle",
                    "modules": "One main concept per module"
                },
                "error_handling": {
                    "exceptions": "Use specific exception types",
                    "logging": "Log errors with context",
                    "recovery": "Implement graceful degradation",
                    "validation": "Validate inputs early"
                },
                "performance": {
                    "loops": "Avoid nested loops when possible",
                    "data_structures": "Choose appropriate data structures",
                    "io": "Use async for I/O operations",
                    "memory": "Be mindful of memory usage in loops"
                }
            }
        }

        # Security review patterns
        self.security_checklist = {
            "input_validation": {
                "check_for": ["user input", "api parameters", "file uploads", "database queries"],
                "look_for": ["sanitize", "validate", "escape", "filter"],
                "red_flags": ["eval(", "exec(", "shell=True", "raw SQL"]
            },
            "authentication": {
                "check_for": ["login", "session", "token", "password"],
                "look_for": ["hash", "encrypt", "secure", "verify"],
                "red_flags": ["hardcoded password", "plain text", "weak encryption"]
            },
            "data_exposure": {
                "check_for": ["api keys", "secrets", "credentials", "personal data"],
                "look_for": ["environment variables", "config files", "encrypted storage"],
                "red_flags": ["print password", "log secret", "hardcoded key"]
            }
        }

        # Performance patterns
        self.performance_patterns = {
            "database": {
                "good": ["bulk operations", "indexed queries", "connection pooling", "query optimization"],
                "bad": ["N+1 queries", "missing indexes", "large result sets", "no connection pooling"]
            },
            "algorithms": {
                "good": ["O(log n) or O(n) complexity", "appropriate data structures", "caching"],
                "bad": ["O(n²) or worse", "inappropriate data structures", "repeated calculations"]
            },
            "io": {
                "good": ["async operations", "streaming", "batching", "compression"],
                "bad": ["blocking operations", "large memory loads", "frequent small requests"]
            }
        }

        # Educational content database
        self.educational_content = {
            "design_patterns": {
                "singleton": {
                    "when_to_use": "When you need exactly one instance of a class",
                    "implementation_notes": "Use __new__ method or module-level variables",
                    "alternatives": "Dependency injection often better for testability",
                    "common_mistakes": "Thread safety issues, testing difficulties"
                },
                "factory": {
                    "when_to_use": "When object creation logic is complex or configurable",
                    "implementation_notes": "Separate creation logic from business logic",
                    "alternatives": "Dependency injection, builder pattern",
                    "common_mistakes": "Over-engineering simple object creation"
                },
                "observer": {
                    "when_to_use": "When objects need to react to events",
                    "implementation_notes": "Decouple event producers from consumers",
                    "alternatives": "Message queues, event buses",
                    "common_mistakes": "Memory leaks from not unsubscribing"
                }
            },
            "architectural_concepts": {
                "separation_of_concerns": "Each module should have a single, well-defined responsibility",
                "dependency_injection": "Pass dependencies rather than creating them internally",
                "single_responsibility": "A class should have only one reason to change",
                "open_closed": "Open for extension, closed for modification",
                "composition_over_inheritance": "Favor object composition over class inheritance"
            }
        }

    async def review_code(self, file_content: str, file_path: str, project_context: Dict = None) -> CodeReview:
        """
        Educational code review like Claude's style
        """
        print(f"📝 Reviewing code: {os.path.basename(file_path)}")

        # Step 1: Overall assessment
        overall_assessment = await self.assess_overall_quality(file_content, file_path)
        print(f"📊 Overall quality: {overall_assessment['quality_score']:.1f}/10")

        # Step 2: Pattern analysis
        pattern_analysis = await self.analyze_patterns(file_content, file_path)
        print(f"🎨 Patterns analyzed: {len(pattern_analysis)} patterns found")

        # Step 3: Issue detection
        issues_found = await self.find_issues(file_content, file_path)
        print(f"🔍 Issues found: {len(issues_found)} total")

        # Step 4: Best practices review
        best_practices_review = await self.check_best_practices(file_content, file_path)

        # Step 5: Security review
        security_review = await self.security_analysis(file_content, file_path)
        print(f"🛡️ Security score: {security_review['security_score']:.1f}/10")

        # Step 6: Performance review
        performance_review = await self.analyze_performance(file_content, file_path)

        # Step 7: Maintainability assessment
        maintainability = await self.assess_maintainability(file_content, file_path)

        # Step 8: Generate educational content
        educational_highlights = await self.generate_educational_content(
            file_content, pattern_analysis, issues_found
        )

        # Step 9: Learning recommendations
        learning_recommendations = await self.generate_learning_recommendations(
            overall_assessment, issues_found, pattern_analysis
        )

        # Step 10: Positive feedback and improvements
        positive_aspects = await self.identify_positive_aspects(file_content, pattern_analysis)
        areas_for_improvement = await self.identify_improvement_areas(issues_found, best_practices_review)

        return CodeReview(
            overall_assessment=overall_assessment,
            code_quality_score=overall_assessment['quality_score'],
            issues_found=issues_found,
            pattern_analysis=pattern_analysis,
            best_practices_review=best_practices_review,
            security_review=security_review,
            performance_review=performance_review,
            maintainability_assessment=maintainability,
            educational_highlights=educational_highlights,
            learning_recommendations=learning_recommendations,
            positive_aspects=positive_aspects,
            areas_for_improvement=areas_for_improvement
        )

    async def assess_overall_quality(self, code: str, file_path: str) -> Dict[str, Any]:
        """Assess overall code quality with educational context"""
        assessment = {
            "quality_score": 5.0,
            "complexity": "medium",
            "readability": "good",
            "structure": "organized",
            "documentation": "needs_improvement",
            "summary": "",
            "key_strengths": [],
            "key_weaknesses": []
        }

        lines = code.split('\n')
        non_empty_lines = [line for line in lines if line.strip()]

        # Analyze structure
        try:
            tree = ast.parse(code)

            # Count different elements
            functions = len([node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)])
            classes = len([node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)])
            imports = len([node for node in ast.walk(tree) if isinstance(node, (ast.Import, ast.ImportFrom))])

            # Assess complexity
            if len(non_empty_lines) > 200:
                assessment["complexity"] = "high"
                assessment["quality_score"] -= 1
            elif len(non_empty_lines) < 50:
                assessment["complexity"] = "low"
                assessment["quality_score"] += 0.5

            # Assess structure
            if classes > 0 and functions > 0:
                assessment["structure"] = "well_organized"
                assessment["quality_score"] += 1
                assessment["key_strengths"].append("Good separation of classes and functions")

            # Check for documentation
            docstring_count = len(re.findall(r'""".*?"""', code, re.DOTALL))
            if docstring_count >= functions // 2:
                assessment["documentation"] = "good"
                assessment["quality_score"] += 1
                assessment["key_strengths"].append("Well-documented functions")
            elif docstring_count == 0:
                assessment["documentation"] = "missing"
                assessment["quality_score"] -= 1
                assessment["key_weaknesses"].append("Missing function documentation")

            # Check readability
            avg_line_length = sum(len(line) for line in non_empty_lines) / len(non_empty_lines) if non_empty_lines else 0
            if avg_line_length > 100:
                assessment["readability"] = "poor"
                assessment["quality_score"] -= 0.5
                assessment["key_weaknesses"].append("Lines are too long (>100 chars)")
            elif avg_line_length < 80:
                assessment["readability"] = "excellent"
                assessment["quality_score"] += 0.5

        except SyntaxError:
            assessment["quality_score"] = 2.0
            assessment["complexity"] = "unknown"
            assessment["key_weaknesses"].append("Syntax errors prevent analysis")

        # Generate summary
        assessment["summary"] = self._generate_quality_summary(assessment)

        # Normalize score
        assessment["quality_score"] = max(1.0, min(10.0, assessment["quality_score"]))

        return assessment

    def _generate_quality_summary(self, assessment: Dict) -> str:
        """Generate a human-readable quality summary"""
        score = assessment["quality_score"]

        if score >= 8:
            return "Excellent code quality with strong structure and documentation"
        elif score >= 6:
            return "Good code quality with room for minor improvements"
        elif score >= 4:
            return "Acceptable code quality but needs attention in several areas"
        else:
            return "Code quality needs significant improvement"

    async def analyze_patterns(self, code: str, file_path: str) -> List[DesignPatternUsage]:
        """Analyze design patterns with educational context"""
        patterns_found = []

        try:
            tree = ast.parse(code)

            # Look for singleton pattern
            singleton_usage = self._analyze_singleton_pattern(tree, code, file_path)
            if singleton_usage:
                patterns_found.append(singleton_usage)

            # Look for factory pattern
            factory_usage = self._analyze_factory_pattern(tree, code, file_path)
            if factory_usage:
                patterns_found.append(factory_usage)

            # Look for observer pattern
            observer_usage = self._analyze_observer_pattern(tree, code, file_path)
            if observer_usage:
                patterns_found.append(observer_usage)

            # Look for strategy pattern
            strategy_usage = self._analyze_strategy_pattern(tree, code, file_path)
            if strategy_usage:
                patterns_found.append(strategy_usage)

        except SyntaxError:
            pass  # Skip analysis for files with syntax errors

        return patterns_found

    def _analyze_singleton_pattern(self, tree: ast.AST, code: str, file_path: str) -> Optional[DesignPatternUsage]:
        """Analyze singleton pattern implementation"""
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                # Look for __new__ method (common singleton implementation)
                has_new_method = any(isinstance(method, ast.FunctionDef) and method.name == '__new__'
                                   for method in node.body)

                # Look for instance variables
                has_instance_var = '_instance' in code.lower()

                if has_new_method or has_instance_var:
                    # Assess implementation quality
                    quality = "needs_improvement"
                    educational_notes = []
                    improvement_suggestions = []

                    if has_new_method and has_instance_var:
                        quality = "good"
                        educational_notes.append("Proper singleton implementation using __new__ method")
                    else:
                        improvement_suggestions.append("Consider using __new__ method for proper singleton implementation")

                    # Check for thread safety
                    if "threading" in code.lower() or "lock" in code.lower():
                        quality = "excellent"
                        educational_notes.append("Thread-safe singleton implementation")
                    else:
                        improvement_suggestions.append("Consider thread safety for multi-threaded applications")

                    return DesignPatternUsage(
                        pattern_name="Singleton",
                        implementation_quality=quality,
                        file_path=file_path,
                        explanation="Singleton pattern ensures only one instance of a class exists",
                        educational_notes=educational_notes,
                        improvement_suggestions=improvement_suggestions,
                        examples_of_better_usage=[
                            "Use dependency injection instead for better testability",
                            "Consider module-level variables for simple singletons"
                        ]
                    )

        return None

    def _analyze_factory_pattern(self, tree: ast.AST, code: str, file_path: str) -> Optional[DesignPatternUsage]:
        """Analyze factory pattern implementation"""
        factory_indicators = ["create_", "make_", "build_", "Factory", "Builder"]

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if any(indicator in node.name for indicator in factory_indicators):
                    quality = "good"
                    educational_notes = [
                        "Factory pattern centralizes object creation logic",
                        "Useful when object creation is complex or configurable"
                    ]
                    improvement_suggestions = []

                    # Check if it's a proper factory (returns different types)
                    if "return" in ast.dump(node):
                        educational_notes.append("Factory method properly returns created objects")
                    else:
                        improvement_suggestions.append("Factory methods should return created objects")

                    return DesignPatternUsage(
                        pattern_name="Factory",
                        implementation_quality=quality,
                        file_path=file_path,
                        explanation="Factory pattern encapsulates object creation logic",
                        educational_notes=educational_notes,
                        improvement_suggestions=improvement_suggestions,
                        examples_of_better_usage=[
                            "Abstract Factory for creating families of related objects",
                            "Builder pattern for complex object construction"
                        ]
                    )

        return None

    def _analyze_observer_pattern(self, tree: ast.AST, code: str, file_path: str) -> Optional[DesignPatternUsage]:
        """Analyze observer pattern implementation"""
        observer_indicators = ["subscribe", "notify", "observer", "listener", "callback", "event"]

        has_observer_methods = False
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if any(indicator in node.name.lower() for indicator in observer_indicators):
                    has_observer_methods = True
                    break

        if has_observer_methods:
            quality = "good"
            educational_notes = [
                "Observer pattern enables loose coupling between components",
                "Subjects notify observers of state changes automatically"
            ]
            improvement_suggestions = []

            # Check for proper implementation
            if "list" in code.lower() and "append" in code.lower():
                educational_notes.append("Proper observer list management")
            else:
                improvement_suggestions.append("Maintain a list of observers for notification")

            return DesignPatternUsage(
                pattern_name="Observer",
                implementation_quality=quality,
                file_path=file_path,
                explanation="Observer pattern implements publisher-subscriber relationship",
                educational_notes=educational_notes,
                improvement_suggestions=improvement_suggestions,
                examples_of_better_usage=[
                    "Use weak references to prevent memory leaks",
                    "Consider using event libraries for complex scenarios"
                ]
            )

        return None

    def _analyze_strategy_pattern(self, tree: ast.AST, code: str, file_path: str) -> Optional[DesignPatternUsage]:
        """Analyze strategy pattern implementation"""
        strategy_indicators = ["strategy", "algorithm", "policy", "execute", "apply"]

        has_strategy_methods = False
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                if any(indicator in node.name.lower() for indicator in strategy_indicators):
                    has_strategy_methods = True
                    break

        if has_strategy_methods:
            return DesignPatternUsage(
                pattern_name="Strategy",
                implementation_quality="good",
                file_path=file_path,
                explanation="Strategy pattern encapsulates algorithms and makes them interchangeable",
                educational_notes=[
                    "Strategy pattern enables algorithm selection at runtime",
                    "Promotes open-closed principle (open for extension, closed for modification)"
                ],
                improvement_suggestions=[
                    "Consider using abstract base classes for type safety",
                    "Document when to use each strategy"
                ],
                examples_of_better_usage=[
                    "Use enum or registry for strategy selection",
                    "Combine with factory pattern for strategy creation"
                ]
            )

        return None

    async def find_issues(self, code: str, file_path: str) -> List[CodeIssue]:
        """Find code issues with educational explanations"""
        issues = []

        lines = code.split('\n')

        # Check for common issues
        for i, line in enumerate(lines, 1):
            line_stripped = line.strip()

            # Security issues
            if 'eval(' in line or 'exec(' in line:
                issues.append(CodeIssue(
                    severity="critical",
                    category="security",
                    description="Use of eval() or exec() detected",
                    file_path=file_path,
                    line_number=i,
                    code_snippet=line_stripped,
                    explanation="eval() and exec() can execute arbitrary code and are major security risks",
                    suggested_fix="Use safer alternatives like json.loads() or ast.literal_eval()",
                    learning_note="Code injection attacks often exploit eval() and exec() functions",
                    examples=["json.loads() for JSON data", "ast.literal_eval() for Python literals"]
                ))

            # Hardcoded credentials
            if re.search(r'password\s*=\s*["\'][^"\']+["\']', line, re.IGNORECASE):
                issues.append(CodeIssue(
                    severity="critical",
                    category="security",
                    description="Hardcoded password detected",
                    file_path=file_path,
                    line_number=i,
                    code_snippet=line_stripped,
                    explanation="Hardcoded passwords are visible in source code and version control",
                    suggested_fix="Use environment variables or secure configuration files",
                    learning_note="Credentials should never be stored in source code",
                    examples=["os.getenv('PASSWORD')", "config.get('password')"]
                ))

            # Long lines
            if len(line) > 120:
                issues.append(CodeIssue(
                    severity="minor",
                    category="style",
                    description="Line too long",
                    file_path=file_path,
                    line_number=i,
                    code_snippet=line_stripped[:50] + "...",
                    explanation="Long lines reduce readability and make code harder to review",
                    suggested_fix="Break line into multiple lines or extract to variables",
                    learning_note="PEP 8 recommends maximum line length of 79-88 characters",
                    examples=["Use parentheses for implicit line continuation", "Extract complex expressions to variables"]
                ))

            # Missing error handling in risky operations
            if re.search(r'open\s*\(|requests\.|urllib\.|socket\.', line):
                # Check if this line or nearby lines have try/except
                context_lines = lines[max(0, i-3):min(len(lines), i+3)]
                has_error_handling = any('try:' in l or 'except' in l for l in context_lines)

                if not has_error_handling:
                    issues.append(CodeIssue(
                        severity="major",
                        category="reliability",
                        description="I/O operation without error handling",
                        file_path=file_path,
                        line_number=i,
                        code_snippet=line_stripped,
                        explanation="File operations and network requests can fail and should be handled gracefully",
                        suggested_fix="Wrap in try-except block with appropriate error handling",
                        learning_note="Always handle exceptions for operations that can fail",
                        examples=["try/except blocks", "context managers (with statement)"]
                    ))

        # Check for missing docstrings
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and node.name != '__init__':
                    # Check if function has docstring
                    has_docstring = (node.body and
                                   isinstance(node.body[0], ast.Expr) and
                                   isinstance(node.body[0].value, ast.Constant) and
                                   isinstance(node.body[0].value.value, str))

                    if not has_docstring:
                        issues.append(CodeIssue(
                            severity="minor",
                            category="documentation",
                            description=f"Function '{node.name}' missing docstring",
                            file_path=file_path,
                            line_number=node.lineno,
                            code_snippet=f"def {node.name}(...)",
                            explanation="Docstrings help other developers understand function purpose and usage",
                            suggested_fix="Add docstring describing function purpose, parameters, and return value",
                            learning_note="Good documentation is essential for maintainable code",
                            examples=['"""Function description."""', "Google-style or Sphinx-style docstrings"]
                        ))

        except SyntaxError:
            issues.append(CodeIssue(
                severity="critical",
                category="syntax",
                description="Syntax error in file",
                file_path=file_path,
                line_number=None,
                code_snippet="",
                explanation="File contains syntax errors that prevent parsing",
                suggested_fix="Fix syntax errors before proceeding with review",
                learning_note="Use an IDE or linter to catch syntax errors early",
                examples=["Check for missing colons", "Verify proper indentation"]
            ))

        return issues

    async def check_best_practices(self, code: str, file_path: str) -> Dict[str, Any]:
        """Check adherence to Python best practices"""
        practices = {
            "naming_conventions": {"score": 5.0, "issues": [], "good_examples": []},
            "function_design": {"score": 5.0, "issues": [], "good_examples": []},
            "error_handling": {"score": 5.0, "issues": [], "good_examples": []},
            "imports": {"score": 5.0, "issues": [], "good_examples": []},
            "overall_score": 5.0
        }

        lines = code.split('\n')

        # Check naming conventions
        snake_case_pattern = re.compile(r'^[a-z_][a-z0-9_]*$')
        pascal_case_pattern = re.compile(r'^[A-Z][a-zA-Z0-9]*$')

        try:
            tree = ast.parse(code)

            # Check function names
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    if not snake_case_pattern.match(node.name) and not node.name.startswith('__'):
                        practices["naming_conventions"]["issues"].append(
                            f"Function '{node.name}' should use snake_case naming"
                        )
                        practices["naming_conventions"]["score"] -= 0.5
                    else:
                        practices["naming_conventions"]["good_examples"].append(
                            f"Good function naming: {node.name}"
                        )

                # Check class names
                elif isinstance(node, ast.ClassDef):
                    if not pascal_case_pattern.match(node.name):
                        practices["naming_conventions"]["issues"].append(
                            f"Class '{node.name}' should use PascalCase naming"
                        )
                        practices["naming_conventions"]["score"] -= 0.5
                    else:
                        practices["naming_conventions"]["good_examples"].append(
                            f"Good class naming: {node.name}"
                        )

            # Check function length
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    func_lines = node.end_lineno - node.lineno if hasattr(node, 'end_lineno') else 0
                    if func_lines > 30:
                        practices["function_design"]["issues"].append(
                            f"Function '{node.name}' is too long ({func_lines} lines)"
                        )
                        practices["function_design"]["score"] -= 1
                    elif func_lines < 20:
                        practices["function_design"]["good_examples"].append(
                            f"Good function length: {node.name} ({func_lines} lines)"
                        )

        except SyntaxError:
            practices["naming_conventions"]["score"] = 0
            practices["function_design"]["score"] = 0

        # Check imports organization
        import_sections = {"stdlib": [], "third_party": [], "local": []}
        in_imports = True

        for line in lines:
            if line.strip().startswith(('import ', 'from ')):
                if not in_imports:
                    practices["imports"]["issues"].append("Imports not grouped at top of file")
                    practices["imports"]["score"] -= 1
                    break
            elif line.strip() and not line.strip().startswith('#'):
                in_imports = False

        # Check error handling
        has_try_except = any('try:' in line and 'except' in ''.join(lines[i:i+10])
                           for i, line in enumerate(lines))
        if has_try_except:
            practices["error_handling"]["good_examples"].append("Error handling present in code")
        else:
            practices["error_handling"]["issues"].append("No error handling found")
            practices["error_handling"]["score"] -= 2

        # Calculate overall score
        scores = [practices[key]["score"] for key in practices if key != "overall_score"]
        practices["overall_score"] = sum(scores) / len(scores) if scores else 0

        return practices

    async def security_analysis(self, code: str, file_path: str) -> Dict[str, Any]:
        """Perform security analysis with educational context"""
        security = {
            "security_score": 7.0,
            "vulnerabilities": [],
            "good_practices": [],
            "recommendations": [],
            "educational_notes": []
        }

        code_lower = code.lower()

        # Check for common vulnerabilities
        if 'eval(' in code or 'exec(' in code:
            security["vulnerabilities"].append({
                "type": "Code Injection",
                "severity": "Critical",
                "description": "Use of eval() or exec() allows arbitrary code execution",
                "education": "These functions can execute any Python code, making them major security risks"
            })
            security["security_score"] -= 3

        if re.search(r'password\s*=\s*["\'][^"\']+["\']', code, re.IGNORECASE):
            security["vulnerabilities"].append({
                "type": "Hardcoded Credentials",
                "severity": "Critical",
                "description": "Passwords or keys hardcoded in source code",
                "education": "Credentials in source code can be accessed by anyone with code access"
            })
            security["security_score"] -= 3

        if 'shell=True' in code:
            security["vulnerabilities"].append({
                "type": "Command Injection",
                "severity": "High",
                "description": "shell=True in subprocess calls can allow command injection",
                "education": "Avoid shell=True or sanitize inputs carefully to prevent command injection"
            })
            security["security_score"] -= 2

        # Check for good practices
        if any(keyword in code_lower for keyword in ['validate', 'sanitize', 'escape']):
            security["good_practices"].append("Input validation/sanitization found")
            security["security_score"] += 0.5

        if any(keyword in code_lower for keyword in ['hash', 'encrypt', 'bcrypt']):
            security["good_practices"].append("Cryptographic functions used")
            security["security_score"] += 0.5

        if 'try:' in code and 'except' in code:
            security["good_practices"].append("Error handling present")
            security["security_score"] += 0.5

        # Generate recommendations
        security["recommendations"] = [
            "Use environment variables for sensitive configuration",
            "Implement input validation for all user inputs",
            "Use parameterized queries for database operations",
            "Add logging for security-relevant events",
            "Regular security dependency updates"
        ]

        # Educational notes
        security["educational_notes"] = [
            "Security should be considered at every layer of the application",
            "Input validation is the first line of defense against many attacks",
            "Never trust user input - validate, sanitize, and escape appropriately",
            "Use established libraries for cryptographic operations",
            "Security through obscurity is not sufficient - use proper security measures"
        ]

        security["security_score"] = max(0, min(10, security["security_score"]))

        return security

    async def analyze_performance(self, code: str, file_path: str) -> Dict[str, Any]:
        """Analyze performance aspects with educational insights"""
        performance = {
            "performance_score": 7.0,
            "bottlenecks": [],
            "optimizations": [],
            "educational_insights": []
        }

        code_lower = code.lower()

        # Check for potential bottlenecks
        if re.search(r'for.*in.*:', code) and any(keyword in code_lower for keyword in ['request', 'query', 'api']):
            performance["bottlenecks"].append({
                "type": "N+1 Query Problem",
                "description": "Potential database queries or API calls in loops",
                "impact": "High - can cause exponential performance degradation",
                "education": "Batch operations or use bulk queries instead of individual requests"
            })
            performance["performance_score"] -= 2

        if 'time.sleep' in code_lower:
            performance["bottlenecks"].append({
                "type": "Blocking Sleep",
                "description": "Synchronous sleep calls block execution",
                "impact": "Medium - prevents concurrent operations",
                "education": "Use asyncio.sleep() for asynchronous operations"
            })
            performance["performance_score"] -= 1

        # Check for good patterns
        if 'async def' in code or 'await' in code:
            performance["optimizations"].append({
                "type": "Asynchronous Programming",
                "description": "Async/await patterns for non-blocking operations",
                "benefit": "Improved concurrency and resource utilization"
            })
            performance["performance_score"] += 1

        if any(keyword in code_lower for keyword in ['cache', 'memoize', '@lru_cache']):
            performance["optimizations"].append({
                "type": "Caching",
                "description": "Caching mechanisms to avoid repeated calculations",
                "benefit": "Reduced computational overhead for repeated operations"
            })
            performance["performance_score"] += 1

        # Educational insights
        performance["educational_insights"] = [
            "Profile first, optimize second - measure before making changes",
            "Algorithmic improvements often provide better gains than micro-optimizations",
            "Consider the trade-offs between memory usage and CPU performance",
            "Caching can dramatically improve performance but increases memory usage",
            "Asynchronous programming helps with I/O-bound operations, not CPU-bound ones"
        ]

        performance["performance_score"] = max(0, min(10, performance["performance_score"]))

        return performance

    async def assess_maintainability(self, code: str, file_path: str) -> Dict[str, Any]:
        """Assess code maintainability with improvement suggestions"""
        maintainability = {
            "maintainability_score": 6.0,
            "factors": {},
            "suggestions": [],
            "positive_aspects": []
        }

        lines = code.split('\n')
        non_empty_lines = [line for line in lines if line.strip()]

        # Function length analysis
        try:
            tree = ast.parse(code)
            function_lengths = []
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    func_length = (node.end_lineno - node.lineno) if hasattr(node, 'end_lineno') else 10
                    function_lengths.append(func_length)

            if function_lengths:
                avg_function_length = sum(function_lengths) / len(function_lengths)
                if avg_function_length < 15:
                    maintainability["positive_aspects"].append("Functions are appropriately sized")
                    maintainability["maintainability_score"] += 1
                elif avg_function_length > 30:
                    maintainability["suggestions"].append("Break down large functions into smaller ones")
                    maintainability["maintainability_score"] -= 1

        except SyntaxError:
            maintainability["maintainability_score"] -= 2

        # Documentation assessment
        comment_lines = len([line for line in lines if line.strip().startswith('#')])
        docstring_count = len(re.findall(r'""".*?"""', code, re.DOTALL))

        doc_ratio = (comment_lines + docstring_count) / len(non_empty_lines) if non_empty_lines else 0

        if doc_ratio > 0.2:
            maintainability["positive_aspects"].append("Well-documented code")
            maintainability["maintainability_score"] += 1
        elif doc_ratio < 0.05:
            maintainability["suggestions"].append("Add more comments and docstrings")
            maintainability["maintainability_score"] -= 1

        # Complexity indicators
        complexity_keywords = ['if', 'elif', 'else', 'for', 'while', 'try', 'except']
        complexity_count = sum(code.lower().count(keyword) for keyword in complexity_keywords)
        complexity_ratio = complexity_count / len(non_empty_lines) if non_empty_lines else 0

        if complexity_ratio > 0.3:
            maintainability["suggestions"].append("Reduce complexity by extracting helper functions")
            maintainability["maintainability_score"] -= 1

        maintainability["factors"] = {
            "documentation_ratio": doc_ratio,
            "complexity_ratio": complexity_ratio,
            "average_function_length": sum(function_lengths) / len(function_lengths) if function_lengths else 0
        }

        maintainability["maintainability_score"] = max(0, min(10, maintainability["maintainability_score"]))

        return maintainability

    async def generate_educational_content(self, code: str, patterns: List[DesignPatternUsage],
                                         issues: List[CodeIssue]) -> List[str]:
        """Generate educational highlights and teaching moments"""
        highlights = []

        # Pattern-based education
        for pattern in patterns:
            if pattern.implementation_quality in ["excellent", "good"]:
                highlights.append(
                    f"✨ Great use of {pattern.pattern_name} pattern! {pattern.explanation}"
                )
                highlights.extend(pattern.educational_notes)

        # Issue-based education
        critical_issues = [issue for issue in issues if issue.severity == "critical"]
        if critical_issues:
            highlights.append(
                "🚨 Critical security issues found - these should be addressed immediately"
            )

        # Code structure education
        if 'class' in code and 'def' in code:
            highlights.append(
                "📚 Good separation of concerns with classes and functions - this follows object-oriented principles"
            )

        if 'async def' in code:
            highlights.append(
                "⚡ Async programming detected - great for I/O-bound operations and concurrent processing"
            )

        if re.search(r'""".*?"""', code, re.DOTALL):
            highlights.append(
                "📖 Docstrings found - excellent for code documentation and IDE support"
            )

        return highlights

    async def generate_learning_recommendations(self, assessment: Dict, issues: List[CodeIssue],
                                              patterns: List[DesignPatternUsage]) -> List[str]:
        """Generate personalized learning recommendations"""
        recommendations = []

        # Based on quality score
        quality_score = assessment.get("quality_score", 5)

        if quality_score < 5:
            recommendations.append(
                "📚 Focus on code fundamentals: PEP 8 style guide, function design, and error handling"
            )

        # Based on issues found
        security_issues = [issue for issue in issues if issue.category == "security"]
        if security_issues:
            recommendations.append(
                "🛡️ Study secure coding practices: OWASP guidelines, input validation, and authentication"
            )

        performance_issues = [issue for issue in issues if "performance" in issue.category.lower()]
        if performance_issues:
            recommendations.append(
                "⚡ Learn performance optimization: profiling tools, algorithmic complexity, and caching strategies"
            )

        # Based on patterns
        if len(patterns) < 2:
            recommendations.append(
                "🎨 Study design patterns: Gang of Four patterns, SOLID principles, and architectural patterns"
            )

        # General recommendations
        recommendations.extend([
            "🧪 Practice test-driven development (TDD) for better code quality",
            "📖 Read 'Clean Code' by Robert Martin for best practices",
            "🔧 Use static analysis tools like pylint, mypy, and black for code quality",
            "👥 Participate in code reviews to learn from experienced developers"
        ])

        return recommendations[:5]  # Limit to top 5

    async def identify_positive_aspects(self, code: str, patterns: List[DesignPatternUsage]) -> List[str]:
        """Identify positive aspects of the code for encouragement"""
        positives = []

        # Pattern usage
        excellent_patterns = [p for p in patterns if p.implementation_quality == "excellent"]
        if excellent_patterns:
            positives.append(f"Excellent implementation of {excellent_patterns[0].pattern_name} pattern")

        # Code structure
        if 'class' in code and 'def' in code:
            positives.append("Good separation of concerns with classes and functions")

        # Error handling
        if 'try:' in code and 'except' in code:
            positives.append("Proactive error handling implemented")

        # Documentation
        if '"""' in code:
            positives.append("Good documentation with docstrings")

        # Modern Python features
        if 'async def' in code:
            positives.append("Modern asynchronous programming patterns")

        if '@' in code:  # Decorators
            positives.append("Good use of Python decorators")

        if 'with ' in code:  # Context managers
            positives.append("Proper resource management with context managers")

        return positives

    async def identify_improvement_areas(self, issues: List[CodeIssue],
                                       best_practices: Dict) -> List[str]:
        """Identify key areas for improvement"""
        improvements = []

        # Critical issues first
        critical_issues = [issue for issue in issues if issue.severity == "critical"]
        if critical_issues:
            improvements.append("Address critical security and reliability issues immediately")

        # Best practices
        for practice, data in best_practices.items():
            if practice != "overall_score" and data["score"] < 5:
                improvements.append(f"Improve {practice.replace('_', ' ')}")

        # Common patterns
        issue_categories = {}
        for issue in issues:
            issue_categories[issue.category] = issue_categories.get(issue.category, 0) + 1

        for category, count in sorted(issue_categories.items(), key=lambda x: x[1], reverse=True):
            if count > 2:
                improvements.append(f"Focus on {category} improvements ({count} issues)")

        return improvements[:5]  # Top 5 areas


if __name__ == "__main__":
    async def main():
        mentor = CodeReviewMentor()

        # Test with a sample file
        test_file = "/Users/CJ/Desktop/penny_assistant/jedi_code_analyzer.py"

        if os.path.exists(test_file):
            with open(test_file, 'r', encoding='utf-8') as f:
                code_content = f.read()

            print(f"📝 Reviewing: {os.path.basename(test_file)}")
            print("=" * 50)

            review = await mentor.review_code(code_content, test_file)

            print(f"\n📊 Overall Quality Score: {review.code_quality_score:.1f}/10")
            print(f"🛡️ Security Score: {review.security_review['security_score']:.1f}/10")

            print(f"\n✨ Positive Aspects:")
            for positive in review.positive_aspects[:3]:
                print(f"  • {positive}")

            print(f"\n🔍 Issues Found: {len(review.issues_found)}")
            for issue in review.issues_found[:3]:
                print(f"  • {issue.severity.upper()}: {issue.description}")

            print(f"\n🎨 Design Patterns: {len(review.pattern_analysis)}")
            for pattern in review.pattern_analysis:
                print(f"  • {pattern.pattern_name} ({pattern.implementation_quality})")

            print(f"\n💡 Learning Recommendations:")
            for rec in review.learning_recommendations[:3]:
                print(f"  • {rec}")

        else:
            print(f"Test file not found: {test_file}")

    asyncio.run(main())