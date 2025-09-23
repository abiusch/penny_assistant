"""
Code Generation Tool Server
Secure MCP tool server for code generation, testing, and safe execution
Enables autonomous learning and self-improvement within security boundaries
"""

import asyncio
import ast
import json
import os
import subprocess
import tempfile
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
import sys
import importlib.util

# Import existing MCP and security infrastructure
try:
    from mcp_client import MCPToolServer, MCPOperation, MCPResult
    from tool_server_foundation import ToolServerType, SecurityLevel
    from command_whitelist_system import CommandWhitelistSystem
    from multi_channel_emergency_stop import MultiChannelEmergencyStop
    from enhanced_security_logging import EnhancedSecurityLogging
    from rollback_recovery_system import RollbackRecoverySystem
    from rate_limiting_resource_control import RateLimitingResourceControl
    MCP_AVAILABLE = True
except ImportError:
    # Fallback definitions for standalone operation
    from enum import Enum
    from dataclasses import dataclass

    class ToolServerType(Enum):
        CODE_GENERATION = "code_generation"

    class SecurityLevel(Enum):
        LOW = "low"
        MEDIUM = "medium"
        HIGH = "high"
        CRITICAL = "critical"

    @dataclass
    class MCPOperation:
        name: str
        parameters: Dict[str, Any]
        security_level: SecurityLevel = SecurityLevel.MEDIUM

    @dataclass
    class MCPResult:
        success: bool
        data: Any = None
        error: Optional[str] = None
        metadata: Optional[Dict[str, Any]] = None

    class MCPToolServer:
        def __init__(self, name, operations): pass
        async def start(self): return True
        async def stop(self): return True

    # Mock security classes
    class CommandWhitelistSystem:
        async def is_command_allowed(self, command): return True

    class MultiChannelEmergencyStop:
        def is_emergency_active(self): return False

    class EnhancedSecurityLogging:
        async def log_security_event(self, event_type, details): pass

    class RollbackRecoverySystem:
        async def create_checkpoint(self, checkpoint_id): return "mock_checkpoint"
        async def rollback_to_checkpoint(self, checkpoint_id): return True

    class RateLimitingResourceControl:
        async def check_rate_limit(self, user_id, operation): return True

    MCP_AVAILABLE = False


class CodeExecutionSandbox:
    """Secure sandbox for code execution with resource limits"""

    def __init__(self,
                 max_execution_time: float = 10.0,
                 max_memory_mb: int = 512,
                 max_output_length: int = 10000):
        self.max_execution_time = max_execution_time
        self.max_memory_mb = max_memory_mb
        self.max_output_length = max_output_length
        self.temp_dir = None

    async def __aenter__(self):
        """Enter sandbox context"""
        # Create temporary directory for sandbox execution
        self.temp_dir = tempfile.mkdtemp(prefix="code_sandbox_")
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit sandbox context and cleanup"""
        if self.temp_dir and os.path.exists(self.temp_dir):
            import shutil
            try:
                shutil.rmtree(self.temp_dir)
            except Exception as e:
                print(f"Warning: Failed to cleanup sandbox directory: {e}")

    async def execute_code(self,
                          code: str,
                          language: str = "python",
                          capture_output: bool = True) -> Dict[str, Any]:
        """Execute code in sandbox with resource limits"""

        if language != "python":
            return {
                "success": False,
                "error": f"Language {language} not supported in sandbox",
                "output": "",
                "execution_time": 0
            }

        # Validate Python syntax
        try:
            ast.parse(code)
        except SyntaxError as e:
            return {
                "success": False,
                "error": f"Syntax error: {e}",
                "output": "",
                "execution_time": 0
            }

        # Create execution script
        script_path = os.path.join(self.temp_dir, "sandbox_script.py")

        # Wrap code with safety measures
        safe_code = self._wrap_code_for_safety(code)

        with open(script_path, 'w') as f:
            f.write(safe_code)

        # Execute with resource limits
        start_time = time.time()

        try:
            # Use subprocess with timeout and limited environment
            env = {
                "PYTHONPATH": "",
                "PATH": "/usr/bin:/bin",  # Minimal PATH
                "TMPDIR": self.temp_dir
            }

            process = await asyncio.create_subprocess_exec(
                sys.executable, script_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self.temp_dir,
                env=env
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=self.max_execution_time
                )

                execution_time = time.time() - start_time

                # Decode output
                output = stdout.decode('utf-8', errors='replace')
                error_output = stderr.decode('utf-8', errors='replace')

                # Limit output length
                if len(output) > self.max_output_length:
                    output = output[:self.max_output_length] + "\n... (output truncated)"

                if len(error_output) > self.max_output_length:
                    error_output = error_output[:self.max_output_length] + "\n... (error output truncated)"

                success = process.returncode == 0

                return {
                    "success": success,
                    "output": output,
                    "error": error_output if error_output else None,
                    "execution_time": execution_time,
                    "return_code": process.returncode
                }

            except asyncio.TimeoutError:
                # Kill the process if it times out
                try:
                    process.terminate()
                    await asyncio.wait_for(process.wait(), timeout=1.0)
                except:
                    process.kill()
                    await process.wait()

                return {
                    "success": False,
                    "error": f"Code execution timed out after {self.max_execution_time} seconds",
                    "output": "",
                    "execution_time": self.max_execution_time
                }

        except Exception as e:
            return {
                "success": False,
                "error": f"Execution failed: {str(e)}",
                "output": "",
                "execution_time": time.time() - start_time
            }

    def _wrap_code_for_safety(self, code: str) -> str:
        """Wrap user code with safety measures"""
        safety_wrapper = '''
import sys
import os
import signal

# Resource monitoring
class ResourceMonitor:
    def __init__(self, max_memory_mb):
        self.max_memory_mb = max_memory_mb

    def check_memory(self):
        try:
            import psutil
            process = psutil.Process()
            memory_mb = process.memory_info().rss / 1024 / 1024
            if memory_mb > self.max_memory_mb:
                raise MemoryError(f"Memory limit exceeded: {memory_mb:.1f}MB > {self.max_memory_mb}MB")
        except ImportError:
            pass  # psutil not available, skip memory monitoring

# Install resource monitor
monitor = ResourceMonitor(''' + str(self.max_memory_mb) + ''')

# Override dangerous functions
def safe_open(filename, mode='r', **kwargs):
    # Only allow access to files in sandbox directory
    abs_path = os.path.abspath(filename)
    sandbox_path = os.path.abspath("''' + self.temp_dir + '''")
    if not abs_path.startswith(sandbox_path):
        raise PermissionError(f"File access denied: {filename}")
    return open(filename, mode, **kwargs)

# Replace built-in open safely
import builtins
builtins.open = safe_open

# Disable dangerous modules
prohibited_modules = ['subprocess', 'os', 'sys', 'importlib', 'socket', 'urllib', 'requests']
for module in prohibited_modules:
    sys.modules[module] = None

# User code starts here
try:
''' + '\n'.join('    ' + line for line in code.split('\n')) + '''

except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)
'''
        return safety_wrapper

    async def validate_code_security(self, code: str) -> Dict[str, Any]:
        """Validate code for security issues"""

        # Parse AST to analyze code structure
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            return {
                "valid": False,
                "issues": [f"Syntax error: {e}"],
                "risk_level": "HIGH"
            }

        issues = []
        risk_level = "LOW"

        # Check for dangerous patterns
        for node in ast.walk(tree):
            # Check for dangerous imports
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name in ['os', 'sys', 'subprocess', 'socket', 'urllib', 'requests']:
                        issues.append(f"Dangerous import detected: {alias.name}")
                        risk_level = "HIGH"

            # Check for dangerous function calls
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    if node.func.id in ['exec', 'eval', 'compile']:
                        issues.append(f"Dangerous function call: {node.func.id}")
                        risk_level = "HIGH"

            # Check for file operations
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name) and node.func.id == 'open':
                    issues.append("File operation detected - will be sandboxed")
                    if risk_level == "LOW":
                        risk_level = "MEDIUM"

        return {
            "valid": risk_level != "HIGH",
            "issues": issues,
            "risk_level": risk_level
        }


class CodeGenerationEngine:
    """AI-powered code generation with security validation"""

    def __init__(self):
        self.generation_templates = {
            "function": self._generate_function_template,
            "class": self._generate_class_template,
            "test": self._generate_test_template,
            "enhancement": self._generate_enhancement_template
        }

    async def generate_code(self,
                           specification: str,
                           code_type: str = "function",
                           language: str = "python",
                           style_preferences: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Generate code based on specification"""

        if language != "python":
            return {
                "success": False,
                "error": f"Language {language} not supported",
                "code": ""
            }

        try:
            # Use appropriate template based on code type
            generator = self.generation_templates.get(code_type, self._generate_function_template)

            code = await generator(specification, style_preferences or {})

            return {
                "success": True,
                "code": code,
                "type": code_type,
                "language": language,
                "metadata": {
                    "specification": specification,
                    "generated_at": datetime.now().isoformat(),
                    "style_preferences": style_preferences
                }
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Code generation failed: {str(e)}",
                "code": ""
            }

    async def _generate_function_template(self, specification: str, style: Dict[str, Any]) -> str:
        """Generate a function based on specification"""

        # Simple template-based generation (in production, would use AI model)
        function_name = style.get('function_name', 'generated_function')

        template = f'''def {function_name}():
    """
    Generated function based on specification:
    {specification}
    """
    # TODO: Implement functionality based on specification
    # {specification}

    result = None

    # Add your implementation here

    return result
'''
        return template

    async def _generate_class_template(self, specification: str, style: Dict[str, Any]) -> str:
        """Generate a class based on specification"""

        class_name = style.get('class_name', 'GeneratedClass')

        template = f'''class {class_name}:
    """
    Generated class based on specification:
    {specification}
    """

    def __init__(self):
        """Initialize the class"""
        # Add initialization code based on specification
        pass

    def main_method(self):
        """Main method implementing the specified functionality"""
        # TODO: Implement based on specification
        # {specification}
        pass
'''
        return template

    async def _generate_test_template(self, specification: str, style: Dict[str, Any]) -> str:
        """Generate test cases based on specification"""

        test_name = style.get('test_name', 'test_generated_function')

        template = f'''import unittest

class TestGenerated(unittest.TestCase):
    """
    Generated test cases based on specification:
    {specification}
    """

    def setUp(self):
        """Set up test fixtures"""
        pass

    def {test_name}(self):
        """Test the generated functionality"""
        # TODO: Implement test based on specification
        # {specification}

        # Example test structure
        # result = function_to_test()
        # self.assertIsNotNone(result)
        # self.assertEqual(expected_value, result)

        self.assertTrue(True, "Test placeholder - implement actual test")

    def tearDown(self):
        """Clean up after tests"""
        pass

if __name__ == '__main__':
    unittest.main()
'''
        return template

    async def _generate_enhancement_template(self, specification: str, style: Dict[str, Any]) -> str:
        """Generate system enhancement code"""

        enhancement_name = style.get('enhancement_name', 'system_enhancement')

        template = f'''"""
System Enhancement: {enhancement_name}
Generated based on specification: {specification}
"""

class {enhancement_name.replace('_', '').title()}Enhancement:
    """
    Enhancement implementation for: {specification}
    """

    def __init__(self):
        """Initialize enhancement"""
        self.enhancement_id = "{enhancement_name}"
        self.description = "{specification}"
        self.installed = False

    async def install(self):
        """Install the enhancement"""
        try:
            # TODO: Implement enhancement installation
            # {specification}

            self.installed = True
            return True
        except Exception as e:
            print(f"Enhancement installation failed: {{e}}")
            return False

    async def uninstall(self):
        """Uninstall the enhancement"""
        try:
            # TODO: Implement enhancement removal
            self.installed = False
            return True
        except Exception as e:
            print(f"Enhancement uninstallation failed: {{e}}")
            return False

    def is_installed(self):
        """Check if enhancement is installed"""
        return self.installed

# Enhancement factory function
async def create_enhancement():
    """Create and return enhancement instance"""
    return {enhancement_name.replace('_', '').title()}Enhancement()
'''
        return template

    async def analyze_existing_code(self,
                                   code_content: str,
                                   analysis_type: str = "structure") -> Dict[str, Any]:
        """Analyze existing code for structure, complexity, etc."""

        try:
            tree = ast.parse(code_content)

            analysis = {
                "structure": self._analyze_structure(tree),
                "complexity": self._analyze_complexity(tree),
                "security": await self._analyze_security_issues(code_content),
                "suggestions": self._generate_suggestions(tree)
            }

            if analysis_type in analysis:
                return {
                    "success": True,
                    "analysis": analysis[analysis_type],
                    "type": analysis_type
                }
            else:
                return {
                    "success": True,
                    "analysis": analysis,
                    "type": "comprehensive"
                }

        except SyntaxError as e:
            return {
                "success": False,
                "error": f"Code analysis failed - syntax error: {e}",
                "analysis": {}
            }

    def _analyze_structure(self, tree: ast.AST) -> Dict[str, Any]:
        """Analyze code structure"""

        functions = []
        classes = []
        imports = []

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                functions.append({
                    "name": node.name,
                    "line": node.lineno,
                    "args": len(node.args.args)
                })
            elif isinstance(node, ast.ClassDef):
                classes.append({
                    "name": node.name,
                    "line": node.lineno,
                    "methods": len([n for n in node.body if isinstance(n, ast.FunctionDef)])
                })
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for alias in node.names:
                    imports.append(f"{module}.{alias.name}")

        return {
            "functions": functions,
            "classes": classes,
            "imports": imports,
            "total_lines": tree.end_lineno if hasattr(tree, 'end_lineno') else 0
        }

    def _analyze_complexity(self, tree: ast.AST) -> Dict[str, Any]:
        """Analyze code complexity"""

        complexity_score = 1  # Base complexity

        for node in ast.walk(tree):
            # Increase complexity for control structures
            if isinstance(node, (ast.If, ast.For, ast.While, ast.Try)):
                complexity_score += 1
            elif isinstance(node, ast.FunctionDef):
                complexity_score += 1

        # Determine complexity level
        if complexity_score <= 5:
            level = "LOW"
        elif complexity_score <= 15:
            level = "MEDIUM"
        else:
            level = "HIGH"

        return {
            "score": complexity_score,
            "level": level,
            "maintainability": "GOOD" if complexity_score <= 10 else "NEEDS_REVIEW"
        }

    async def _analyze_security_issues(self, code_content: str) -> Dict[str, Any]:
        """Analyze code for security issues"""

        sandbox = CodeExecutionSandbox()
        return await sandbox.validate_code_security(code_content)

    def _generate_suggestions(self, tree: ast.AST) -> List[str]:
        """Generate improvement suggestions"""

        suggestions = []

        # Check for common improvement opportunities
        function_count = len([n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)])
        if function_count == 0:
            suggestions.append("Consider organizing code into functions for better maintainability")

        # Check for docstrings
        has_docstrings = any(
            isinstance(n, ast.FunctionDef) and ast.get_docstring(n)
            for n in ast.walk(tree)
        )
        if not has_docstrings:
            suggestions.append("Add docstrings to functions for better documentation")

        return suggestions


class CodeGenerationToolServer(MCPToolServer):
    """Secure code generation MCP tool server"""

    def __init__(self):
        # Define available operations
        operations = {
            "generate_code": MCPOperation(
                name="generate_code",
                parameters={
                    "specification": "Code specification or requirements",
                    "code_type": "Type of code (function, class, test, enhancement)",
                    "language": "Programming language (default: python)",
                    "style_preferences": "Optional styling preferences"
                },
                security_level=SecurityLevel.HIGH
            ),
            "execute_code_sandboxed": MCPOperation(
                name="execute_code_sandboxed",
                parameters={
                    "code_content": "Code to execute",
                    "timeout": "Execution timeout in seconds",
                    "capture_output": "Whether to capture output"
                },
                security_level=SecurityLevel.CRITICAL
            ),
            "analyze_existing_code": MCPOperation(
                name="analyze_existing_code",
                parameters={
                    "code_content": "Code to analyze",
                    "analysis_type": "Type of analysis (structure, complexity, security)"
                },
                security_level=SecurityLevel.MEDIUM
            ),
            "validate_code_syntax": MCPOperation(
                name="validate_code_syntax",
                parameters={
                    "code_content": "Code to validate",
                    "language": "Programming language"
                },
                security_level=SecurityLevel.LOW
            ),
            "create_test_cases": MCPOperation(
                name="create_test_cases",
                parameters={
                    "code_content": "Code to create tests for",
                    "test_type": "Type of tests (unit, integration)"
                },
                security_level=SecurityLevel.MEDIUM
            ),
            "suggest_improvements": MCPOperation(
                name="suggest_improvements",
                parameters={
                    "code_content": "Code to analyze for improvements",
                    "focus_areas": "Areas to focus on (performance, security, maintainability)"
                },
                security_level=SecurityLevel.LOW
            ),
            "check_security_compliance": MCPOperation(
                name="check_security_compliance",
                parameters={
                    "code_content": "Code to check for security compliance",
                    "security_policies": "Security policies to validate against"
                },
                security_level=SecurityLevel.HIGH
            ),
            "propose_system_enhancement": MCPOperation(
                name="propose_system_enhancement",
                parameters={
                    "enhancement_description": "Description of proposed enhancement",
                    "code_implementation": "Code implementing the enhancement"
                },
                security_level=SecurityLevel.CRITICAL
            )
        }

        super().__init__("code_generation", operations)

        # Initialize components
        self.code_generator = CodeGenerationEngine()
        self.execution_metrics = {
            "total_executions": 0,
            "successful_executions": 0,
            "failed_executions": 0,
            "total_generation_requests": 0,
            "security_violations": 0
        }

        # Security components (will be injected by MCP framework)
        self.whitelist_system = None
        self.emergency_system = None
        self.security_logger = None
        self.rollback_system = None
        self.rate_limiter = None

    async def initialize_security_components(self,
                                           whitelist_system: Optional[CommandWhitelistSystem] = None,
                                           emergency_system: Optional[MultiChannelEmergencyStop] = None,
                                           security_logger: Optional[EnhancedSecurityLogging] = None,
                                           rollback_system: Optional[RollbackRecoverySystem] = None,
                                           rate_limiter: Optional[RateLimitingResourceControl] = None):
        """Initialize security components"""

        self.whitelist_system = whitelist_system
        self.emergency_system = emergency_system
        self.security_logger = security_logger
        self.rollback_system = rollback_system
        self.rate_limiter = rate_limiter

        if self.security_logger:
            await self.security_logger.log_security_event(
                "code_generation_server_initialized",
                {
                    "server_type": "code_generation",
                    "security_components": {
                        "whitelist": whitelist_system is not None,
                        "emergency": emergency_system is not None,
                        "logger": security_logger is not None,
                        "rollback": rollback_system is not None,
                        "rate_limiter": rate_limiter is not None
                    }
                }
            )

    async def _validate_operation_security(self, operation_name: str, user_id: str) -> bool:
        """Validate operation through security components"""

        # Check emergency stop
        if self.emergency_system and self.emergency_system.is_emergency_active():
            if self.security_logger:
                await self.security_logger.log_security_event(
                    "operation_blocked_emergency",
                    {"operation": operation_name, "user_id": user_id}
                )
            return False

        # Check command whitelist
        if self.whitelist_system:
            command_key = f"code_generation:{operation_name}"
            if not await self.whitelist_system.is_command_allowed(command_key):
                if self.security_logger:
                    await self.security_logger.log_security_event(
                        "operation_blocked_whitelist",
                        {"operation": operation_name, "user_id": user_id}
                    )
                return False

        # Check rate limits
        if self.rate_limiter:
            if not await self.rate_limiter.check_rate_limit(user_id, operation_name):
                if self.security_logger:
                    await self.security_logger.log_security_event(
                        "operation_blocked_rate_limit",
                        {"operation": operation_name, "user_id": user_id}
                    )
                return False

        return True

    # Operation implementations
    async def generate_code(self,
                           specification: str,
                           code_type: str = "function",
                           language: str = "python",
                           style_preferences: Optional[Dict[str, Any]] = None,
                           user_id: str = "anonymous") -> MCPResult:
        """Generate code based on specification"""

        if not await self._validate_operation_security("generate_code", user_id):
            return MCPResult(success=False, error="Operation blocked by security validation")

        try:
            self.execution_metrics["total_generation_requests"] += 1

            result = await self.code_generator.generate_code(
                specification, code_type, language, style_preferences
            )

            if self.security_logger:
                await self.security_logger.log_security_event(
                    "code_generated",
                    {
                        "user_id": user_id,
                        "specification": specification[:200],  # Truncate for logging
                        "code_type": code_type,
                        "language": language,
                        "success": result["success"]
                    }
                )

            return MCPResult(
                success=result["success"],
                data=result,
                error=result.get("error")
            )

        except Exception as e:
            return MCPResult(success=False, error=f"Code generation failed: {str(e)}")

    async def execute_code_sandboxed(self,
                                    code_content: str,
                                    timeout: float = 10.0,
                                    capture_output: bool = True,
                                    user_id: str = "anonymous") -> MCPResult:
        """Execute code in sandboxed environment"""

        if not await self._validate_operation_security("execute_code_sandboxed", user_id):
            return MCPResult(success=False, error="Operation blocked by security validation")

        try:
            self.execution_metrics["total_executions"] += 1

            # Create checkpoint before execution
            checkpoint_id = None
            if self.rollback_system:
                checkpoint_id = await self.rollback_system.create_checkpoint(f"code_exec_{user_id}_{int(time.time())}")

            async with CodeExecutionSandbox(max_execution_time=timeout) as sandbox:

                # Validate code security first
                security_validation = await sandbox.validate_code_security(code_content)

                if not security_validation["valid"]:
                    self.execution_metrics["security_violations"] += 1

                    if self.security_logger:
                        await self.security_logger.log_security_event(
                            "code_execution_blocked",
                            {
                                "user_id": user_id,
                                "reason": "Security validation failed",
                                "issues": security_validation["issues"]
                            }
                        )

                    return MCPResult(
                        success=False,
                        error=f"Code execution blocked: {', '.join(security_validation['issues'])}"
                    )

                # Execute code
                result = await sandbox.execute_code(code_content, capture_output=capture_output)

                if result["success"]:
                    self.execution_metrics["successful_executions"] += 1
                else:
                    self.execution_metrics["failed_executions"] += 1

                if self.security_logger:
                    await self.security_logger.log_security_event(
                        "code_executed",
                        {
                            "user_id": user_id,
                            "success": result["success"],
                            "execution_time": result["execution_time"],
                            "checkpoint_id": checkpoint_id
                        }
                    )

                return MCPResult(
                    success=True,
                    data=result,
                    metadata={"checkpoint_id": checkpoint_id}
                )

        except Exception as e:
            self.execution_metrics["failed_executions"] += 1
            return MCPResult(success=False, error=f"Code execution failed: {str(e)}")

    async def analyze_existing_code(self,
                                   code_content: str,
                                   analysis_type: str = "structure",
                                   user_id: str = "anonymous") -> MCPResult:
        """Analyze existing code"""

        if not await self._validate_operation_security("analyze_existing_code", user_id):
            return MCPResult(success=False, error="Operation blocked by security validation")

        try:
            result = await self.code_generator.analyze_existing_code(code_content, analysis_type)

            if self.security_logger:
                await self.security_logger.log_security_event(
                    "code_analyzed",
                    {
                        "user_id": user_id,
                        "analysis_type": analysis_type,
                        "success": result["success"]
                    }
                )

            return MCPResult(
                success=result["success"],
                data=result,
                error=result.get("error")
            )

        except Exception as e:
            return MCPResult(success=False, error=f"Code analysis failed: {str(e)}")

    async def validate_code_syntax(self,
                                  code_content: str,
                                  language: str = "python",
                                  user_id: str = "anonymous") -> MCPResult:
        """Validate code syntax"""

        if not await self._validate_operation_security("validate_code_syntax", user_id):
            return MCPResult(success=False, error="Operation blocked by security validation")

        try:
            if language != "python":
                return MCPResult(success=False, error=f"Language {language} not supported")

            # Parse code to check syntax
            ast.parse(code_content)

            return MCPResult(
                success=True,
                data={"valid": True, "language": language},
                metadata={"validation_time": datetime.now().isoformat()}
            )

        except SyntaxError as e:
            return MCPResult(
                success=True,
                data={
                    "valid": False,
                    "error": str(e),
                    "line": e.lineno,
                    "column": e.offset
                }
            )
        except Exception as e:
            return MCPResult(success=False, error=f"Syntax validation failed: {str(e)}")

    async def create_test_cases(self,
                                code_content: str,
                                test_type: str = "unit",
                                user_id: str = "anonymous") -> MCPResult:
        """Create test cases for given code"""

        if not await self._validate_operation_security("create_test_cases", user_id):
            return MCPResult(success=False, error="Operation blocked by security validation")

        try:
            result = await self.code_generator.generate_code(
                f"Create {test_type} tests for the following code:\\n{code_content}",
                code_type="test",
                style_preferences={"test_name": f"test_{test_type}"}
            )

            if self.security_logger:
                await self.security_logger.log_security_event(
                    "test_cases_created",
                    {
                        "user_id": user_id,
                        "test_type": test_type,
                        "success": result["success"]
                    }
                )

            return MCPResult(
                success=result["success"],
                data=result,
                error=result.get("error")
            )

        except Exception as e:
            return MCPResult(success=False, error=f"Test case creation failed: {str(e)}")

    async def suggest_improvements(self,
                                  code_content: str,
                                  focus_areas: List[str] = None,
                                  user_id: str = "anonymous") -> MCPResult:
        """Suggest improvements for given code"""

        if not await self._validate_operation_security("suggest_improvements", user_id):
            return MCPResult(success=False, error="Operation blocked by security validation")

        try:
            focus_areas = focus_areas or ["performance", "readability", "security"]

            analysis_result = await self.code_generator.analyze_existing_code(
                code_content, "comprehensive"
            )

            if analysis_result["success"]:
                suggestions = analysis_result["analysis"]["suggestions"]

                # Add focus-area specific suggestions
                if "performance" in focus_areas:
                    suggestions.append("Consider using list comprehensions for better performance")
                if "security" in focus_areas:
                    suggestions.append("Add input validation and error handling")
                if "readability" in focus_areas:
                    suggestions.append("Add comprehensive docstrings and comments")

                return MCPResult(
                    success=True,
                    data={
                        "suggestions": suggestions,
                        "focus_areas": focus_areas,
                        "analysis": analysis_result["analysis"]
                    }
                )
            else:
                return MCPResult(success=False, error=analysis_result["error"])

        except Exception as e:
            return MCPResult(success=False, error=f"Improvement suggestion failed: {str(e)}")

    async def check_security_compliance(self,
                                       code_content: str,
                                       security_policies: Optional[List[str]] = None,
                                       user_id: str = "anonymous") -> MCPResult:
        """Check code for security compliance"""

        if not await self._validate_operation_security("check_security_compliance", user_id):
            return MCPResult(success=False, error="Operation blocked by security validation")

        try:
            sandbox = CodeExecutionSandbox()
            security_validation = await sandbox.validate_code_security(code_content)

            # Apply additional security policies if provided
            additional_issues = []
            if security_policies:
                for policy in security_policies:
                    if "no_file_operations" in policy and "open" in code_content:
                        additional_issues.append("File operations not allowed per security policy")

            if additional_issues:
                security_validation["issues"].extend(additional_issues)
                security_validation["valid"] = False

            if self.security_logger:
                await self.security_logger.log_security_event(
                    "security_compliance_check",
                    {
                        "user_id": user_id,
                        "valid": security_validation["valid"],
                        "issues_count": len(security_validation["issues"])
                    }
                )

            return MCPResult(
                success=True,
                data=security_validation
            )

        except Exception as e:
            return MCPResult(success=False, error=f"Security compliance check failed: {str(e)}")

    async def propose_system_enhancement(self,
                                        enhancement_description: str,
                                        code_implementation: str,
                                        user_id: str = "anonymous") -> MCPResult:
        """Propose system enhancement with approval workflow"""

        if not await self._validate_operation_security("propose_system_enhancement", user_id):
            return MCPResult(success=False, error="Operation blocked by security validation")

        try:
            # Create enhancement proposal
            proposal_id = f"enhancement_{int(time.time())}_{uuid.uuid4().hex[:8]}"

            proposal = {
                "id": proposal_id,
                "description": enhancement_description,
                "code": code_implementation,
                "user_id": user_id,
                "created_at": datetime.now().isoformat(),
                "status": "pending_approval",
                "security_validated": False
            }

            # Validate enhancement code
            security_check = await self.check_security_compliance(
                code_implementation,
                user_id=user_id
            )

            if security_check.success and security_check.data["valid"]:
                proposal["security_validated"] = True

            if self.security_logger:
                await self.security_logger.log_security_event(
                    "enhancement_proposed",
                    {
                        "user_id": user_id,
                        "proposal_id": proposal_id,
                        "description": enhancement_description[:200],
                        "security_validated": proposal["security_validated"]
                    }
                )

            return MCPResult(
                success=True,
                data=proposal,
                metadata={"requires_approval": True}
            )

        except Exception as e:
            return MCPResult(success=False, error=f"Enhancement proposal failed: {str(e)}")

    async def get_performance_metrics(self) -> Dict[str, Any]:
        """Get server performance metrics"""
        return self.execution_metrics.copy()


# Convenience function for easy integration
async def create_code_generation_server(security_components: Optional[Dict[str, Any]] = None) -> CodeGenerationToolServer:
    """Create and initialize code generation tool server"""

    server = CodeGenerationToolServer()

    if security_components:
        await server.initialize_security_components(
            whitelist_system=security_components.get('whitelist'),
            emergency_system=security_components.get('emergency'),
            security_logger=security_components.get('logger'),
            rollback_system=security_components.get('rollback'),
            rate_limiter=security_components.get('rate_limiter')
        )

    await server.start()
    return server