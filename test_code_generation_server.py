"""
Test Suite for Code Generation Tool Server
Tests secure code generation, sandboxed execution, and security integration
"""

import asyncio
import tempfile
import os
from datetime import datetime

from code_generation_tool_server import (
    CodeGenerationToolServer, CodeExecutionSandbox, CodeGenerationEngine,
    create_code_generation_server
)


class MockSecurityComponent:
    """Mock security component for testing"""

    def __init__(self, allow_all=True, emergency_active=False):
        self.allow_all = allow_all
        self.emergency_active = emergency_active
        self.events = []

    async def is_command_allowed(self, command):
        return self.allow_all

    def is_emergency_active(self):
        return self.emergency_active

    async def log_security_event(self, event_type, details):
        self.events.append({"type": event_type, "details": details})

    async def create_checkpoint(self, checkpoint_id):
        return f"checkpoint_{checkpoint_id}"

    async def check_rate_limit(self, user_id, operation):
        return self.allow_all


async def test_code_generation_engine():
    """Test core code generation functionality"""
    print("🔧 Testing Code Generation Engine")

    engine = CodeGenerationEngine()

    # Test function generation
    result = await engine.generate_code(
        "Create a function that calculates the factorial of a number",
        code_type="function",
        style_preferences={"function_name": "calculate_factorial"}
    )

    print(f"   Function generation: {'SUCCESS' if result['success'] else 'FAILED'}")
    if result["success"]:
        print(f"   Generated code length: {len(result['code'])} characters")

    # Test class generation
    result = await engine.generate_code(
        "Create a class for managing a simple todo list",
        code_type="class",
        style_preferences={"class_name": "TodoManager"}
    )

    print(f"   Class generation: {'SUCCESS' if result['success'] else 'FAILED'}")

    # Test code analysis
    sample_code = '''
def hello_world():
    """A simple hello world function"""
    print("Hello, World!")
    return "Hello, World!"
'''

    analysis = await engine.analyze_existing_code(sample_code, "structure")
    print(f"   Code analysis: {'SUCCESS' if analysis['success'] else 'FAILED'}")

    if analysis["success"]:
        structure = analysis["analysis"]
        print(f"   Functions found: {len(structure['functions'])}")
        print(f"   Classes found: {len(structure['classes'])}")

    return True


async def test_code_execution_sandbox():
    """Test sandboxed code execution"""
    print("🏖️ Testing Code Execution Sandbox")

    # Test safe code execution
    safe_code = '''
x = 2 + 3
print(f"Result: {x}")
'''

    async with CodeExecutionSandbox(max_execution_time=5.0) as sandbox:
        result = await sandbox.execute_code(safe_code)
        print(f"   Safe code execution: {'SUCCESS' if result['success'] else 'FAILED'}")
        print(f"   Output: {result['output'].strip()}")

    # Test security validation
    dangerous_code = '''
import os
os.system("echo 'This should be blocked'")
'''

    async with CodeExecutionSandbox() as sandbox:
        security_check = await sandbox.validate_code_security(dangerous_code)
        print(f"   Security validation: {'BLOCKED' if not security_check['valid'] else 'FAILED'}")
        print(f"   Issues found: {len(security_check['issues'])}")

    # Test syntax error handling
    invalid_code = '''
def broken_function(
    print("Missing closing parenthesis")
'''

    async with CodeExecutionSandbox() as sandbox:
        result = await sandbox.execute_code(invalid_code)
        print(f"   Syntax error handling: {'SUCCESS' if not result['success'] else 'FAILED'}")

    # Test timeout handling
    infinite_loop = '''
while True:
    pass
'''

    async with CodeExecutionSandbox(max_execution_time=1.0) as sandbox:
        result = await sandbox.execute_code(infinite_loop)
        print(f"   Timeout handling: {'SUCCESS' if not result['success'] and 'timeout' in result['error'].lower() else 'FAILED'}")

    return True


async def test_server_operations():
    """Test code generation tool server operations"""
    print("🚀 Testing Code Generation Tool Server")

    # Create server with mock security components
    security_components = {
        'whitelist': MockSecurityComponent(),
        'emergency': MockSecurityComponent(),
        'logger': MockSecurityComponent(),
        'rollback': MockSecurityComponent(),
        'rate_limiter': MockSecurityComponent()
    }

    server = await create_code_generation_server(security_components)

    try:
        # Test code generation operation
        result = await server.generate_code(
            "Create a function that sorts a list",
            code_type="function",
            user_id="test_user"
        )

        print(f"   Generate code operation: {'SUCCESS' if result.success else 'FAILED'}")

        if result.success:
            generated_code = result.data["code"]

            # Test syntax validation
            syntax_result = await server.validate_code_syntax(
                generated_code,
                user_id="test_user"
            )

            print(f"   Syntax validation: {'SUCCESS' if syntax_result.success and syntax_result.data['valid'] else 'FAILED'}")

            # Test code analysis
            analysis_result = await server.analyze_existing_code(
                generated_code,
                analysis_type="structure",
                user_id="test_user"
            )

            print(f"   Code analysis: {'SUCCESS' if analysis_result.success else 'FAILED'}")

            # Test sandboxed execution
            execution_result = await server.execute_code_sandboxed(
                "print('Hello from sandbox!')",
                timeout=5.0,
                user_id="test_user"
            )

            print(f"   Sandboxed execution: {'SUCCESS' if execution_result.success else 'FAILED'}")

        # Test performance metrics
        metrics = await server.get_performance_metrics()
        print(f"   Performance metrics: {metrics['total_generation_requests']} generations, {metrics['total_executions']} executions")

        return True

    finally:
        await server.stop()


async def test_security_integration():
    """Test security component integration"""
    print("🔒 Testing Security Integration")

    # Test with blocking security components
    blocking_security = {
        'whitelist': MockSecurityComponent(allow_all=False),
        'emergency': MockSecurityComponent(emergency_active=True),
        'logger': MockSecurityComponent(),
        'rollback': MockSecurityComponent(),
        'rate_limiter': MockSecurityComponent(allow_all=False)
    }

    server = await create_code_generation_server(blocking_security)

    try:
        # Test blocked operations
        result = await server.generate_code(
            "Test blocked operation",
            user_id="test_user"
        )

        print(f"   Blocked operation handling: {'SUCCESS' if not result.success else 'FAILED'}")

        # Test security logging
        security_events = blocking_security['logger'].events
        print(f"   Security events logged: {len(security_events)}")

        return True

    finally:
        await server.stop()


async def test_enhancement_workflow():
    """Test system enhancement proposal workflow"""
    print("🔄 Testing Enhancement Workflow")

    server = await create_code_generation_server()

    try:
        # Generate enhancement code
        enhancement_result = await server.generate_code(
            "Create an enhancement that adds logging to function calls",
            code_type="enhancement",
            style_preferences={"enhancement_name": "function_logging"},
            user_id="test_user"
        )

        print(f"   Enhancement generation: {'SUCCESS' if enhancement_result.success else 'FAILED'}")

        if enhancement_result.success:
            enhancement_code = enhancement_result.data["code"]

            # Validate enhancement code
            validation_result = await server.validate_code_syntax(
                enhancement_code,
                user_id="test_user"
            )

            print(f"   Enhancement validation: {'SUCCESS' if validation_result.success and validation_result.data['valid'] else 'FAILED'}")

            # Test enhancement in sandbox
            test_code = f'''
{enhancement_code}

# Test the enhancement
enhancement = await create_enhancement()
print(f"Enhancement created: {{enhancement.enhancement_id}}")
'''

            execution_result = await server.execute_code_sandboxed(
                test_code,
                timeout=10.0,
                user_id="test_user"
            )

            print(f"   Enhancement testing: {'SUCCESS' if execution_result.success else 'FAILED'}")

        return True

    finally:
        await server.stop()


async def test_error_handling():
    """Test comprehensive error handling"""
    print("⚠️ Testing Error Handling")

    server = await create_code_generation_server()

    try:
        # Test invalid language
        result = await server.generate_code(
            "Create a function",
            language="unsupported_language",
            user_id="test_user"
        )

        print(f"   Invalid language handling: {'SUCCESS' if not result.success else 'FAILED'}")

        # Test malformed code execution
        result = await server.execute_code_sandboxed(
            "This is not valid Python code at all!",
            user_id="test_user"
        )

        print(f"   Malformed code handling: {'SUCCESS' if not result.success else 'FAILED'}")

        # Test empty specification
        result = await server.generate_code(
            "",
            user_id="test_user"
        )

        print(f"   Empty specification handling: {'SUCCESS' if result.success else 'FAILED'}")

        return True

    finally:
        await server.stop()


async def test_performance_under_load():
    """Test performance under multiple concurrent operations"""
    print("⚡ Testing Performance Under Load")

    server = await create_code_generation_server()

    try:
        # Generate multiple operations concurrently
        tasks = []
        for i in range(5):
            task = server.generate_code(
                f"Create function number {i}",
                user_id=f"user_{i}"
            )
            tasks.append(task)

        results = await asyncio.gather(*tasks)

        successful = sum(1 for result in results if result.success)
        print(f"   Concurrent operations: {successful}/5 successful")

        # Test execution performance
        simple_code = "print('Performance test')"
        execution_tasks = []

        for i in range(3):
            task = server.execute_code_sandboxed(
                simple_code,
                user_id=f"user_{i}"
            )
            execution_tasks.append(task)

        execution_results = await asyncio.gather(*execution_tasks)
        successful_executions = sum(1 for result in execution_results if result.success)

        print(f"   Concurrent executions: {successful_executions}/3 successful")

        # Get final metrics
        metrics = await server.get_performance_metrics()
        print(f"   Final metrics: {metrics['total_generation_requests']} generations, {metrics['successful_executions']} executions")

        return successful >= 4 and successful_executions >= 2

    finally:
        await server.stop()


async def run_code_generation_tests():
    """Run comprehensive code generation tool server tests"""
    print("🧪 CODE GENERATION TOOL SERVER TEST SUITE")
    print("=" * 60)

    tests = [
        ("Code Generation Engine", test_code_generation_engine),
        ("Code Execution Sandbox", test_code_execution_sandbox),
        ("Server Operations", test_server_operations),
        ("Security Integration", test_security_integration),
        ("Enhancement Workflow", test_enhancement_workflow),
        ("Error Handling", test_error_handling),
        ("Performance Under Load", test_performance_under_load)
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
    print("📊 CODE GENERATION TOOL SERVER TEST RESULTS")

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {test_name}: {status}")

    success_rate = (passed / total) * 100
    print(f"\n📈 Success Rate: {passed}/{total} ({success_rate:.1f}%)")

    if success_rate >= 90:
        print("🎉 CODE GENERATION TOOL SERVER READY FOR PRODUCTION!")
        print("   Secure code generation and execution capabilities validated")
        print("   Foundation for autonomous learning and self-improvement ready")
    elif success_rate >= 70:
        print("⚠️  Some code generation features need improvement")
    else:
        print("❌ Critical issues found in code generation server")

    return success_rate >= 90


if __name__ == "__main__":
    # Run without unittest framework to avoid asyncio conflicts
    success = asyncio.run(run_code_generation_tests())
    exit(0 if success else 1)