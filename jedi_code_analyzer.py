#!/usr/bin/env python3
"""
Jedi-Level Code Analysis System
Based on Claude's actual coding methodology for deep codebase understanding
"""

import os
import ast
import sys
import json
import asyncio
import re
import hashlib
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
from collections import defaultdict, Counter

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

@dataclass
class ArchitectureComponent:
    """Represents a component in the system architecture"""
    name: str
    file_path: str
    component_type: str  # controller, model, service, utility, etc.
    dependencies: List[str]
    responsibilities: List[str]
    complexity_score: float
    patterns_used: List[str]

@dataclass
class DesignPattern:
    """Represents a detected design pattern"""
    pattern_name: str
    confidence: float
    evidence: List[str]
    files_involved: List[str]
    implications: List[str]
    educational_notes: List[str]

@dataclass
class DataFlowPath:
    """Represents data flow through the system"""
    start_point: str
    end_point: str
    path: List[str]
    data_transformations: List[str]
    potential_issues: List[str]

@dataclass
class CodebaseAnalysis:
    """Complete codebase analysis results"""
    architecture_overview: Dict[str, Any]
    design_patterns: List[DesignPattern]
    components: List[ArchitectureComponent]
    data_flows: List[DataFlowPath]
    dependencies: Dict[str, List[str]]
    complexity_metrics: Dict[str, float]
    security_analysis: Dict[str, Any]
    performance_insights: Dict[str, Any]
    recommendations: List[str]

class JediCodeAnalyzer:
    """
    Claude's methodology for deep code analysis:
    1. Architecture-First Reading
    2. Pattern Recognition
    3. Data Flow Tracing
    4. Dependency Mapping
    5. Context-Aware Analysis
    """

    def __init__(self):
        self.analysis_capabilities = [
            "architecture_analysis",
            "pattern_recognition",
            "dependency_mapping",
            "data_flow_tracing",
            "performance_analysis",
            "security_review",
            "best_practices_check"
        ]

        # Pattern recognition database
        self.known_patterns = {
            "mvc": {
                "indicators": ["models", "views", "controllers", "routes", "app.py", "main.py"],
                "file_patterns": [r".*model.*\.py", r".*view.*\.py", r".*controller.*\.py"],
                "code_patterns": ["class.*Model", "class.*View", "class.*Controller", "render_template", "redirect"],
                "characteristics": ["separation_of_concerns", "web_framework", "layered_architecture"]
            },
            "factory": {
                "indicators": ["create_", "Factory", "Builder", "make_"],
                "code_patterns": ["def create_", "class.*Factory", "class.*Builder", "def make_"],
                "characteristics": ["object_creation", "abstraction", "creational_pattern"]
            },
            "observer": {
                "indicators": ["subscribe", "notify", "event", "listener", "callback"],
                "code_patterns": ["def subscribe", "def notify", "class.*Observer", "addEventListener", "on_"],
                "characteristics": ["event_driven", "loose_coupling", "behavioral_pattern"]
            },
            "singleton": {
                "indicators": ["__new__", "_instance", "getInstance"],
                "code_patterns": ["def __new__", "_instance.*=.*None", "if not.*_instance"],
                "characteristics": ["single_instance", "global_access", "creational_pattern"]
            },
            "strategy": {
                "indicators": ["Strategy", "algorithm", "choose_", "select_"],
                "code_patterns": ["class.*Strategy", "def execute", "def apply"],
                "characteristics": ["algorithm_selection", "behavioral_pattern", "polymorphism"]
            },
            "pipeline": {
                "indicators": ["pipeline", "process", "stage", "step", "chain"],
                "code_patterns": ["def process", "class.*Pipeline", "stages", "pipeline"],
                "characteristics": ["sequential_processing", "data_transformation", "architectural_pattern"]
            },
            "microservices": {
                "indicators": ["api", "service", "server", "client", "endpoint"],
                "file_patterns": [r".*_server\.py", r".*_service\.py", r".*api.*\.py"],
                "characteristics": ["distributed", "scalable", "independent", "service_oriented"]
            },
            "repository": {
                "indicators": ["repository", "repo", "dao", "data_access"],
                "code_patterns": ["class.*Repository", "class.*DAO", "def save", "def find", "def get"],
                "characteristics": ["data_access", "abstraction", "persistence"]
            }
        }

        # Security patterns to recognize
        self.security_patterns = {
            "input_validation": ["validate", "sanitize", "escape", "filter"],
            "authentication": ["auth", "login", "token", "session", "verify"],
            "authorization": ["permission", "role", "access", "authorize", "check"],
            "encryption": ["encrypt", "decrypt", "hash", "salt", "cipher"],
            "rate_limiting": ["rate_limit", "throttle", "quota", "limit"],
            "logging": ["log", "audit", "track", "monitor"]
        }

    async def analyze_codebase(self, project_path: str) -> CodebaseAnalysis:
        """
        Multi-layered code analysis following Claude's methodology
        """
        print(f"🔍 Starting Jedi-Level analysis of: {project_path}")

        # Step 1: Read project structure
        project_structure = await self._read_project_structure(project_path)
        print(f"📁 Found {len(project_structure['files'])} files to analyze")

        # Step 2: Architecture-First Reading
        architecture = await self.analyze_architecture(project_structure)
        print(f"🏗️ Architecture analysis complete: {architecture['pattern']}")

        # Step 3: Pattern Recognition
        patterns = await self.identify_patterns(project_structure)
        print(f"🎨 Identified {len(patterns)} design patterns")

        # Step 4: Dependency Mapping
        dependencies = await self.map_dependencies(project_structure)
        print(f"🕸️ Mapped dependencies for {len(dependencies)} components")

        # Step 5: Data Flow Tracing
        data_flows = await self.trace_data_flow(project_structure)
        print(f"📊 Traced {len(data_flows)} data flow paths")

        # Step 6: Security Review
        security_analysis = await self.analyze_security(project_structure)
        print(f"🛡️ Security analysis: {security_analysis['overall_score']}/10")

        # Step 7: Performance Analysis
        performance_insights = await self.analyze_performance(project_structure)
        print(f"⚡ Performance insights: {len(performance_insights['bottlenecks'])} potential issues")

        # Step 8: Generate Components
        components = await self._generate_components(project_structure, patterns, dependencies)

        # Step 9: Calculate Complexity Metrics
        complexity_metrics = await self._calculate_complexity_metrics(project_structure)

        # Step 10: Generate Recommendations
        recommendations = await self._generate_recommendations(
            architecture, patterns, security_analysis, performance_insights
        )

        return CodebaseAnalysis(
            architecture_overview=architecture,
            design_patterns=patterns,
            components=components,
            data_flows=data_flows,
            dependencies=dependencies,
            complexity_metrics=complexity_metrics,
            security_analysis=security_analysis,
            performance_insights=performance_insights,
            recommendations=recommendations
        )

    async def analyze_architecture(self, project_structure: Dict) -> Dict[str, Any]:
        """
        Understand overall system architecture like Claude does
        """
        files = project_structure['files']
        directories = project_structure['directories']

        # Analyze directory structure for architectural patterns
        arch_indicators = {
            'mvc': self._detect_mvc_structure(directories),
            'layered': self._detect_layered_architecture(directories),
            'microservices': self._detect_microservices_pattern(files),
            'pipeline': self._detect_pipeline_architecture(files),
            'modular': self._detect_modular_structure(directories)
        }

        # Determine primary architecture pattern
        primary_pattern = max(arch_indicators.items(), key=lambda x: x[1]['confidence'])

        # Analyze main entry points
        entry_points = self._identify_entry_points(files)

        # Identify core components
        core_components = self._identify_core_components(files, directories)

        # Calculate architecture complexity
        complexity_score = self._calculate_architecture_complexity(
            len(files), len(directories), len(core_components)
        )

        return {
            "pattern": primary_pattern[0],
            "confidence": primary_pattern[1]['confidence'],
            "indicators": primary_pattern[1]['indicators'],
            "entry_points": entry_points,
            "core_components": core_components,
            "complexity_score": complexity_score,
            "scalability_assessment": self._assess_scalability(primary_pattern[0], files),
            "maintainability_score": self._assess_maintainability(files, directories)
        }

    async def identify_patterns(self, project_structure: Dict) -> List[DesignPattern]:
        """
        Identify design patterns like Claude recognizes them
        """
        patterns = []
        files = project_structure['files']

        for pattern_name, pattern_info in self.known_patterns.items():
            confidence = await self._calculate_pattern_confidence(files, pattern_info)

            if confidence > 0.3:  # Only include patterns with reasonable confidence
                evidence = await self._gather_pattern_evidence(files, pattern_info)
                implications = self._explain_pattern_implications(pattern_name)
                educational_notes = self._generate_pattern_education(pattern_name)
                files_involved = [f for f in files if self._file_matches_pattern(f, pattern_info)]

                patterns.append(DesignPattern(
                    pattern_name=pattern_name,
                    confidence=confidence,
                    evidence=evidence,
                    files_involved=files_involved[:5],  # Limit to top 5 for readability
                    implications=implications,
                    educational_notes=educational_notes
                ))

        # Sort by confidence
        patterns.sort(key=lambda p: p.confidence, reverse=True)
        return patterns

    async def map_dependencies(self, project_structure: Dict) -> Dict[str, List[str]]:
        """
        Map relationships and understand coupling like Claude does
        """
        dependencies = {}
        files = project_structure['files']

        for file_path in files:
            if file_path.endswith('.py'):
                try:
                    deps = await self._extract_file_dependencies(file_path)
                    dependencies[file_path] = deps
                except Exception as e:
                    print(f"⚠️ Error analyzing {file_path}: {e}")
                    dependencies[file_path] = []

        return dependencies

    async def trace_data_flow(self, project_structure: Dict) -> List[DataFlowPath]:
        """
        Follow how information moves through the system like Claude traces execution
        """
        flows = []
        files = project_structure['files']

        # Identify data sources (entry points, databases, APIs)
        data_sources = self._identify_data_sources(files)

        # Identify data sinks (outputs, responses, storage)
        data_sinks = self._identify_data_sinks(files)

        # Trace paths between sources and sinks
        for source in data_sources:
            for sink in data_sinks:
                path = await self._trace_path(source, sink, files)
                if path:
                    flows.append(DataFlowPath(
                        start_point=source,
                        end_point=sink,
                        path=path['steps'],
                        data_transformations=path['transformations'],
                        potential_issues=path['issues']
                    ))

        return flows

    async def analyze_security(self, project_structure: Dict) -> Dict[str, Any]:
        """
        Security analysis like Claude's security-conscious approach
        """
        files = project_structure['files']
        security_score = 0
        issues = []
        good_practices = []

        for file_path in files:
            if file_path.endswith('.py'):
                file_security = await self._analyze_file_security(file_path)
                security_score += file_security['score']
                issues.extend(file_security['issues'])
                good_practices.extend(file_security['good_practices'])

        # Normalize score
        if files:
            security_score = min(10, security_score / len([f for f in files if f.endswith('.py')]))

        return {
            "overall_score": round(security_score, 1),
            "issues": issues[:10],  # Top 10 issues
            "good_practices": good_practices[:10],  # Top 10 good practices
            "security_patterns": self._detect_security_patterns(files),
            "recommendations": self._generate_security_recommendations(security_score, issues)
        }

    async def analyze_performance(self, project_structure: Dict) -> Dict[str, Any]:
        """
        Performance analysis like Claude identifies bottlenecks
        """
        files = project_structure['files']
        bottlenecks = []
        optimizations = []

        for file_path in files:
            if file_path.endswith('.py'):
                perf_analysis = await self._analyze_file_performance(file_path)
                bottlenecks.extend(perf_analysis['bottlenecks'])
                optimizations.extend(perf_analysis['optimizations'])

        return {
            "bottlenecks": bottlenecks[:10],  # Top 10 issues
            "optimization_opportunities": optimizations[:10],
            "async_usage": self._analyze_async_patterns(files),
            "database_patterns": self._analyze_database_patterns(files),
            "caching_opportunities": self._identify_caching_opportunities(files)
        }

    # Helper methods for detailed analysis

    async def _read_project_structure(self, project_path: str) -> Dict:
        """Read and categorize project files"""
        structure = {
            'files': [],
            'directories': [],
            'python_files': [],
            'config_files': [],
            'test_files': []
        }

        for root, dirs, files in os.walk(project_path):
            # Skip hidden directories and common ignore patterns
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['__pycache__', 'node_modules']]

            structure['directories'].extend([os.path.join(root, d) for d in dirs])

            for file in files:
                if file.startswith('.'):
                    continue

                file_path = os.path.join(root, file)
                structure['files'].append(file_path)

                if file.endswith('.py'):
                    structure['python_files'].append(file_path)
                    if 'test' in file.lower():
                        structure['test_files'].append(file_path)
                elif file.endswith(('.json', '.yaml', '.yml', '.toml', '.ini', '.env')):
                    structure['config_files'].append(file_path)

        return structure

    def _detect_mvc_structure(self, directories: List[str]) -> Dict:
        """Detect MVC architectural pattern"""
        mvc_indicators = ['models', 'views', 'controllers', 'templates', 'static']
        found_indicators = []

        for directory in directories:
            dir_name = os.path.basename(directory).lower()
            if any(indicator in dir_name for indicator in mvc_indicators):
                found_indicators.append(dir_name)

        confidence = len(found_indicators) / len(mvc_indicators)

        return {
            'confidence': confidence,
            'indicators': found_indicators
        }

    def _detect_layered_architecture(self, directories: List[str]) -> Dict:
        """Detect layered architecture pattern"""
        layer_indicators = ['core', 'domain', 'application', 'infrastructure', 'presentation', 'data', 'service']
        found_indicators = []

        for directory in directories:
            dir_name = os.path.basename(directory).lower()
            if any(indicator in dir_name for indicator in layer_indicators):
                found_indicators.append(dir_name)

        confidence = len(found_indicators) / len(layer_indicators)

        return {
            'confidence': confidence,
            'indicators': found_indicators
        }

    def _detect_microservices_pattern(self, files: List[str]) -> Dict:
        """Detect microservices pattern"""
        microservice_indicators = ['_server.py', '_service.py', 'api', 'client', 'endpoint']
        found_indicators = []

        for file_path in files:
            file_name = os.path.basename(file_path).lower()
            if any(indicator in file_name for indicator in microservice_indicators):
                found_indicators.append(file_name)

        confidence = min(1.0, len(found_indicators) / 3)  # Need at least 3 indicators

        return {
            'confidence': confidence,
            'indicators': found_indicators
        }

    def _detect_pipeline_architecture(self, files: List[str]) -> Dict:
        """Detect pipeline architecture pattern"""
        pipeline_indicators = ['pipeline', 'process', 'stage', 'step', 'workflow']
        found_indicators = []

        for file_path in files:
            file_name = os.path.basename(file_path).lower()
            if any(indicator in file_name for indicator in pipeline_indicators):
                found_indicators.append(file_name)

        confidence = min(1.0, len(found_indicators) / 2)  # Need at least 2 indicators

        return {
            'confidence': confidence,
            'indicators': found_indicators
        }

    def _detect_modular_structure(self, directories: List[str]) -> Dict:
        """Detect modular architecture"""
        # Count depth and organization
        max_depth = 0
        module_count = 0

        for directory in directories:
            depth = len(Path(directory).parts)
            max_depth = max(max_depth, depth)
            if 'src' in directory or any(Path(directory).name in ['core', 'modules', 'components'] for part in Path(directory).parts):
                module_count += 1

        confidence = min(1.0, (module_count / max(1, len(directories))) * 2)

        return {
            'confidence': confidence,
            'indicators': [f"max_depth_{max_depth}", f"modules_{module_count}"]
        }

    def _identify_entry_points(self, files: List[str]) -> List[str]:
        """Identify main entry points of the application"""
        entry_points = []

        for file_path in files:
            file_name = os.path.basename(file_path)
            if file_name in ['main.py', 'app.py', 'run.py', '__main__.py'] or file_name.endswith('_main.py'):
                entry_points.append(file_path)

        return entry_points

    def _identify_core_components(self, files: List[str], directories: List[str]) -> List[str]:
        """Identify core system components"""
        components = []

        # Look for important files
        important_keywords = ['core', 'base', 'main', 'engine', 'manager', 'controller', 'service']

        for file_path in files:
            if file_path.endswith('.py'):
                file_name = os.path.basename(file_path).lower()
                if any(keyword in file_name for keyword in important_keywords):
                    components.append(file_path)

        # Look for important directories
        for directory in directories:
            dir_name = os.path.basename(directory).lower()
            if any(keyword in dir_name for keyword in important_keywords):
                components.append(directory)

        return components[:10]  # Limit to top 10

    def _calculate_architecture_complexity(self, file_count: int, dir_count: int, component_count: int) -> float:
        """Calculate overall architecture complexity score"""
        # Simple heuristic for complexity
        base_complexity = (file_count / 10) + (dir_count / 5) + (component_count / 3)
        return min(10.0, base_complexity / 3)

    def _assess_scalability(self, pattern: str, files: List[str]) -> Dict:
        """Assess how scalable the current architecture is"""
        scalability_factors = {
            'mvc': 7,
            'microservices': 9,
            'pipeline': 6,
            'layered': 8,
            'modular': 8
        }

        base_score = scalability_factors.get(pattern, 5)

        # Adjust based on file count
        if len(files) > 100:
            base_score -= 1
        elif len(files) < 20:
            base_score += 1

        return {
            'score': max(1, min(10, base_score)),
            'factors': ['architecture_pattern', 'file_organization', 'component_separation']
        }

    def _assess_maintainability(self, files: List[str], directories: List[str]) -> float:
        """Assess how maintainable the codebase is"""
        # Consider organization, naming, structure
        python_files = [f for f in files if f.endswith('.py')]

        if not python_files:
            return 5.0

        # Check for good organization
        has_tests = any('test' in f.lower() for f in python_files)
        has_docs = any(f.endswith(('.md', '.rst', '.txt')) for f in files)
        has_config = any(f.endswith(('.json', '.yaml', '.yml', '.toml')) for f in files)

        score = 5.0
        if has_tests:
            score += 1.5
        if has_docs:
            score += 1.0
        if has_config:
            score += 0.5

        # Penalize if too many files in root
        root_python_files = [f for f in python_files if '/' not in f.replace('\\', '/')]
        if len(root_python_files) > 10:
            score -= 1.0

        return max(1.0, min(10.0, score))

    async def _calculate_pattern_confidence(self, files: List[str], pattern_info: Dict) -> float:
        """Calculate confidence score for pattern detection"""
        total_score = 0
        max_score = 0

        # Check file structure indicators
        if 'indicators' in pattern_info:
            for indicator in pattern_info['indicators']:
                max_score += 1
                if any(indicator.lower() in f.lower() for f in files):
                    total_score += 1

        # Check file patterns
        if 'file_patterns' in pattern_info:
            for pattern in pattern_info['file_patterns']:
                max_score += 1
                if any(re.search(pattern, f, re.IGNORECASE) for f in files):
                    total_score += 1

        # Check code patterns (simplified - would need actual file content)
        if 'code_patterns' in pattern_info:
            max_score += len(pattern_info['code_patterns']) * 0.5  # Weight code patterns less without content

        return total_score / max_score if max_score > 0 else 0.0

    async def _gather_pattern_evidence(self, files: List[str], pattern_info: Dict) -> List[str]:
        """Gather evidence for pattern detection"""
        evidence = []

        # File-based evidence
        if 'indicators' in pattern_info:
            for indicator in pattern_info['indicators']:
                matching_files = [f for f in files if indicator.lower() in f.lower()]
                if matching_files:
                    evidence.append(f"Found {indicator} pattern in {len(matching_files)} files")

        # Pattern-based evidence
        if 'file_patterns' in pattern_info:
            for pattern in pattern_info['file_patterns']:
                matching_files = [f for f in files if re.search(pattern, f, re.IGNORECASE)]
                if matching_files:
                    evidence.append(f"File pattern {pattern} matched {len(matching_files)} files")

        return evidence

    def _explain_pattern_implications(self, pattern_name: str) -> List[str]:
        """Explain what this pattern means for the codebase"""
        implications = {
            'mvc': [
                "Clear separation between data, presentation, and logic",
                "Easy to test individual components",
                "Multiple developers can work on different layers simultaneously",
                "Changes to UI don't affect business logic"
            ],
            'factory': [
                "Object creation is centralized and configurable",
                "Easy to add new object types without changing client code",
                "Reduces coupling between components",
                "Makes testing easier with mock objects"
            ],
            'observer': [
                "Components can react to events without tight coupling",
                "Easy to add new event handlers",
                "Supports asynchronous communication",
                "Can lead to complex event chains if not managed well"
            ],
            'pipeline': [
                "Data processing is broken into clear stages",
                "Easy to add, remove, or reorder processing steps",
                "Each stage can be tested independently",
                "Good for ETL and data transformation workflows"
            ],
            'microservices': [
                "Services can be developed and deployed independently",
                "Different technologies can be used for different services",
                "Scalability can be targeted to specific components",
                "Increases operational complexity"
            ]
        }

        return implications.get(pattern_name, ["Pattern provides structural benefits to code organization"])

    def _generate_pattern_education(self, pattern_name: str) -> List[str]:
        """Generate educational content about the pattern"""
        education = {
            'mvc': [
                "MVC separates concerns: Model (data), View (presentation), Controller (logic)",
                "Originally designed for desktop GUIs, now widely used in web frameworks",
                "Promotes reusability and parallel development",
                "Consider MVVM or MVP variants for different use cases"
            ],
            'factory': [
                "Factory pattern encapsulates object creation logic",
                "Useful when object creation is complex or needs to be configurable",
                "Abstract Factory can create families of related objects",
                "Consider using dependency injection for more flexibility"
            ],
            'observer': [
                "Observer implements the publish-subscribe pattern",
                "Subjects maintain a list of observers and notify them of changes",
                "Common in GUI programming and event-driven architectures",
                "Can be implemented with callbacks, events, or message queues"
            ]
        }

        return education.get(pattern_name, ["This pattern helps organize code structure"])

    def _file_matches_pattern(self, file_path: str, pattern_info: Dict) -> bool:
        """Check if a file matches the pattern indicators"""
        file_name = os.path.basename(file_path).lower()

        # Check indicators
        if 'indicators' in pattern_info:
            for indicator in pattern_info['indicators']:
                if indicator.lower() in file_name:
                    return True

        # Check file patterns
        if 'file_patterns' in pattern_info:
            for pattern in pattern_info['file_patterns']:
                if re.search(pattern, file_path, re.IGNORECASE):
                    return True

        return False

    async def _extract_file_dependencies(self, file_path: str) -> List[str]:
        """Extract dependencies from a Python file"""
        dependencies = []

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Parse imports
            tree = ast.parse(content)

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        dependencies.append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        dependencies.append(node.module)

        except Exception:
            # If parsing fails, fall back to regex
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                import_pattern = r'^\s*(?:from\s+(\S+)\s+)?import\s+(\S+)'
                matches = re.findall(import_pattern, content, re.MULTILINE)

                for from_module, import_name in matches:
                    if from_module:
                        dependencies.append(from_module)
                    else:
                        dependencies.append(import_name)

            except Exception:
                pass  # Skip files we can't read

        return dependencies

    def _identify_data_sources(self, files: List[str]) -> List[str]:
        """Identify where data enters the system"""
        sources = []

        for file_path in files:
            file_name = os.path.basename(file_path).lower()

            # Look for common data source patterns
            if any(pattern in file_name for pattern in ['api', 'client', 'input', 'reader', 'parser']):
                sources.append(file_path)

            # Look for main entry points
            if file_name in ['main.py', 'app.py', 'server.py']:
                sources.append(file_path)

        return sources

    def _identify_data_sinks(self, files: List[str]) -> List[str]:
        """Identify where data exits the system"""
        sinks = []

        for file_path in files:
            file_name = os.path.basename(file_path).lower()

            # Look for common data sink patterns
            if any(pattern in file_name for pattern in ['output', 'writer', 'exporter', 'renderer', 'response']):
                sinks.append(file_path)

        return sinks

    async def _trace_path(self, source: str, sink: str, files: List[str]) -> Optional[Dict]:
        """Trace execution path between source and sink"""
        # Simplified path tracing - in reality this would be much more complex
        # This is a placeholder for demonstration

        if source == sink:
            return None

        # Simple heuristic: if both files exist, assume they might be connected
        return {
            'steps': [source, '...', sink],
            'transformations': ['input_processing', 'business_logic', 'output_formatting'],
            'issues': ['potential_bottleneck', 'error_handling_needed']
        }

    async def _analyze_file_security(self, file_path: str) -> Dict:
        """Analyze security aspects of a single file"""
        score = 5.0  # Base score
        issues = []
        good_practices = []

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read().lower()

            # Check for security issues
            if 'password' in content and 'hardcoded' not in content:
                issues.append(f"Potential hardcoded password in {file_path}")
                score -= 2

            if 'api_key' in content or 'secret' in content:
                issues.append(f"Potential exposed API key/secret in {file_path}")
                score -= 2

            if 'exec(' in content or 'eval(' in content:
                issues.append(f"Dangerous exec/eval usage in {file_path}")
                score -= 3

            # Check for good practices
            if 'validate' in content or 'sanitize' in content:
                good_practices.append(f"Input validation found in {file_path}")
                score += 1

            if 'encrypt' in content or 'hash' in content:
                good_practices.append(f"Encryption/hashing found in {file_path}")
                score += 1

            if 'try:' in content and 'except' in content:
                good_practices.append(f"Error handling found in {file_path}")
                score += 0.5

        except Exception:
            pass  # Skip files we can't read

        return {
            'score': max(0, min(10, score)),
            'issues': issues,
            'good_practices': good_practices
        }

    def _detect_security_patterns(self, files: List[str]) -> Dict:
        """Detect security patterns across the codebase"""
        patterns_found = {}

        for pattern_name, keywords in self.security_patterns.items():
            matching_files = []
            for file_path in files:
                file_name = os.path.basename(file_path).lower()
                if any(keyword in file_name for keyword in keywords):
                    matching_files.append(file_path)

            if matching_files:
                patterns_found[pattern_name] = {
                    'files': matching_files[:3],  # Limit to first 3
                    'confidence': min(1.0, len(matching_files) / 2)
                }

        return patterns_found

    def _generate_security_recommendations(self, score: float, issues: List[str]) -> List[str]:
        """Generate security recommendations based on analysis"""
        recommendations = []

        if score < 5:
            recommendations.append("Critical security issues found - immediate attention required")
        elif score < 7:
            recommendations.append("Some security concerns - review and improve where possible")

        if any('password' in issue.lower() for issue in issues):
            recommendations.append("Use environment variables or secure vaults for credentials")

        if any('exec' in issue.lower() or 'eval' in issue.lower() for issue in issues):
            recommendations.append("Avoid exec/eval - use safer alternatives like json.loads() or ast.literal_eval()")

        recommendations.append("Implement input validation for all user inputs")
        recommendations.append("Add comprehensive error handling and logging")
        recommendations.append("Consider adding rate limiting for API endpoints")

        return recommendations

    async def _analyze_file_performance(self, file_path: str) -> Dict:
        """Analyze performance aspects of a single file"""
        bottlenecks = []
        optimizations = []

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read().lower()

            # Look for potential bottlenecks
            if 'for' in content and 'in' in content and ('request' in content or 'query' in content):
                bottlenecks.append(f"Potential N+1 query problem in {file_path}")

            if 'time.sleep' in content:
                bottlenecks.append(f"Blocking sleep call in {file_path}")

            if 'json.loads' in content or 'json.dumps' in content:
                optimizations.append(f"Consider using faster JSON libraries like orjson in {file_path}")

            # Look for good patterns
            if 'async def' in content or 'await' in content:
                optimizations.append(f"Good: async/await patterns used in {file_path}")

            if 'cache' in content or 'memoize' in content:
                optimizations.append(f"Good: caching patterns found in {file_path}")

        except Exception:
            pass

        return {
            'bottlenecks': bottlenecks,
            'optimizations': optimizations
        }

    def _analyze_async_patterns(self, files: List[str]) -> Dict:
        """Analyze async/await usage patterns"""
        async_files = []

        for file_path in files:
            if file_path.endswith('.py'):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()

                    if 'async def' in content or 'await' in content:
                        async_files.append(file_path)

                except Exception:
                    pass

        return {
            'async_files': async_files,
            'adoption_percentage': len(async_files) / len([f for f in files if f.endswith('.py')]) * 100
        }

    def _analyze_database_patterns(self, files: List[str]) -> Dict:
        """Analyze database access patterns"""
        db_files = []
        patterns = []

        db_keywords = ['sql', 'query', 'database', 'db', 'orm', 'model']

        for file_path in files:
            file_name = os.path.basename(file_path).lower()
            if any(keyword in file_name for keyword in db_keywords):
                db_files.append(file_path)

        if db_files:
            patterns.append("Database access layer identified")

        return {
            'database_files': db_files,
            'patterns': patterns
        }

    def _identify_caching_opportunities(self, files: List[str]) -> List[str]:
        """Identify where caching could improve performance"""
        opportunities = []

        for file_path in files:
            file_name = os.path.basename(file_path).lower()

            # Look for expensive operations
            if any(keyword in file_name for keyword in ['api', 'client', 'fetch', 'download']):
                opportunities.append(f"Cache API responses in {file_path}")

            if 'process' in file_name or 'transform' in file_name:
                opportunities.append(f"Cache processed results in {file_path}")

        return opportunities

    async def _generate_components(self, project_structure: Dict, patterns: List[DesignPattern], dependencies: Dict) -> List[ArchitectureComponent]:
        """Generate component analysis"""
        components = []

        for file_path in project_structure['python_files']:
            file_name = os.path.basename(file_path)

            # Determine component type
            component_type = self._classify_component_type(file_name, file_path)

            # Get dependencies
            file_deps = dependencies.get(file_path, [])

            # Determine responsibilities
            responsibilities = self._infer_responsibilities(file_name, component_type)

            # Calculate complexity (simplified)
            complexity = min(10.0, len(file_deps) + len(responsibilities))

            # Find patterns used
            patterns_used = [p.pattern_name for p in patterns if file_path in p.files_involved]

            components.append(ArchitectureComponent(
                name=file_name,
                file_path=file_path,
                component_type=component_type,
                dependencies=file_deps,
                responsibilities=responsibilities,
                complexity_score=complexity,
                patterns_used=patterns_used
            ))

        return components

    def _classify_component_type(self, file_name: str, file_path: str) -> str:
        """Classify what type of component this file represents"""
        name_lower = file_name.lower()
        path_lower = file_path.lower()

        if 'test' in name_lower:
            return 'test'
        elif any(keyword in name_lower for keyword in ['model', 'entity', 'data']):
            return 'model'
        elif any(keyword in name_lower for keyword in ['view', 'template', 'render']):
            return 'view'
        elif any(keyword in name_lower for keyword in ['controller', 'handler', 'endpoint']):
            return 'controller'
        elif any(keyword in name_lower for keyword in ['service', 'manager', 'engine']):
            return 'service'
        elif any(keyword in name_lower for keyword in ['util', 'helper', 'tool']):
            return 'utility'
        elif any(keyword in name_lower for keyword in ['config', 'setting']):
            return 'configuration'
        elif 'main' in name_lower or 'app' in name_lower:
            return 'entry_point'
        else:
            return 'module'

    def _infer_responsibilities(self, file_name: str, component_type: str) -> List[str]:
        """Infer what responsibilities this component has"""
        responsibilities = []

        type_responsibilities = {
            'model': ['data_representation', 'business_logic', 'validation'],
            'view': ['user_interface', 'presentation', 'templating'],
            'controller': ['request_handling', 'routing', 'coordination'],
            'service': ['business_logic', 'data_processing', 'external_integration'],
            'utility': ['helper_functions', 'common_operations', 'tools'],
            'configuration': ['settings_management', 'environment_config'],
            'entry_point': ['application_startup', 'main_execution'],
            'test': ['quality_assurance', 'verification', 'validation']
        }

        return type_responsibilities.get(component_type, ['general_functionality'])

    async def _calculate_complexity_metrics(self, project_structure: Dict) -> Dict[str, float]:
        """Calculate various complexity metrics"""
        files = project_structure['python_files']

        if not files:
            return {}

        # Simple metrics
        total_files = len(files)
        avg_file_size = 0

        # Calculate average file size
        total_size = 0
        readable_files = 0

        for file_path in files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = len(f.readlines())
                    total_size += lines
                    readable_files += 1
            except Exception:
                pass

        if readable_files > 0:
            avg_file_size = total_size / readable_files

        return {
            'total_files': total_files,
            'average_file_size': avg_file_size,
            'codebase_size': total_size,
            'complexity_score': min(10.0, (total_files / 10) + (avg_file_size / 50))
        }

    async def _generate_recommendations(self, architecture: Dict, patterns: List[DesignPattern],
                                      security: Dict, performance: Dict) -> List[str]:
        """Generate actionable recommendations for the codebase"""
        recommendations = []

        # Architecture recommendations
        if architecture['complexity_score'] > 7:
            recommendations.append("Consider breaking down complex components into smaller, focused modules")

        if architecture['maintainability_score'] < 6:
            recommendations.append("Improve code organization - add documentation and standardize naming conventions")

        # Pattern recommendations
        high_confidence_patterns = [p for p in patterns if p.confidence > 0.7]
        if len(high_confidence_patterns) > 3:
            recommendations.append("Great pattern usage! Your code shows strong architectural design")
        elif len(high_confidence_patterns) < 2:
            recommendations.append("Consider implementing more design patterns for better code organization")

        # Security recommendations
        if security['overall_score'] < 6:
            recommendations.append("Security needs attention - review the identified issues and implement fixes")

        # Performance recommendations
        if len(performance['bottlenecks']) > 3:
            recommendations.append("Multiple performance bottlenecks detected - prioritize the most critical ones")

        if performance['async_usage']['adoption_percentage'] < 30:
            recommendations.append("Consider adopting async/await for I/O-bound operations to improve performance")

        # General recommendations
        recommendations.append("Add comprehensive unit tests for better code reliability")
        recommendations.append("Implement continuous integration for automated testing and quality checks")
        recommendations.append("Consider adding type hints for better code documentation and IDE support")

        return recommendations[:10]  # Limit to top 10 recommendations


if __name__ == "__main__":
    async def main():
        analyzer = JediCodeAnalyzer()

        # Test with current project
        project_path = "/Users/CJ/Desktop/penny_assistant"
        analysis = await analyzer.analyze_codebase(project_path)

        print("\n🎯 JEDI-LEVEL CODE ANALYSIS RESULTS")
        print("=" * 50)

        print(f"\n🏗️ Architecture: {analysis.architecture_overview['pattern']}")
        print(f"   Confidence: {analysis.architecture_overview['confidence']:.1%}")
        print(f"   Complexity: {analysis.architecture_overview['complexity_score']:.1f}/10")

        print(f"\n🎨 Design Patterns Found: {len(analysis.design_patterns)}")
        for pattern in analysis.design_patterns[:3]:
            print(f"   • {pattern.pattern_name} ({pattern.confidence:.1%} confidence)")

        print(f"\n🛡️ Security Score: {analysis.security_analysis['overall_score']}/10")
        print(f"⚡ Performance Issues: {len(analysis.performance_insights['bottlenecks'])}")

        print(f"\n💡 Top Recommendations:")
        for i, rec in enumerate(analysis.recommendations[:5], 1):
            print(f"   {i}. {rec}")

    asyncio.run(main())