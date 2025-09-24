"""
Comprehensive Security Audit for Code Generation Server
Tests all security boundaries mentioned in feedback
"""

import asyncio
import time
from code_generation_tool_server import create_code_generation_server


async def test_memory_exhaustion_attacks():
    """Test various memory exhaustion attack vectors"""
    print("🧠 Testing Memory Exhaustion Attacks")

    server = await create_code_generation_server()
    attacks_blocked = 0
    total_attacks = 0

    memory_attacks = [
        ("Large list allocation", "x = [0] * (10**8)"),
        ("Recursive data structure", "x = []; x.append(x); y = [x] * (10**6)"),
        ("String multiplication", "s = 'A' * (10**7)"),
        ("Dictionary expansion", "d = {i: 'x' * 1000 for i in range(100000)}"),
        ("Nested list comprehension", "x = [[i] * 1000 for i in range(10000)]")
    ]

    try:
        for attack_name, attack_code in memory_attacks:
            total_attacks += 1
            result = await server.execute_code_sandboxed(
                attack_code,
                timeout=3.0,
                user_id="memory_audit"
            )

            # Attack should be blocked by resource limits
            blocked = not result.success or not result.data.get("success", False)
            if blocked:
                attacks_blocked += 1
                print(f"   ✅ Blocked: {attack_name}")
            else:
                print(f"   ❌ BREACH: {attack_name}")

        success_rate = (attacks_blocked / total_attacks) * 100
        print(f"   🛡️ Memory attack blocking: {attacks_blocked}/{total_attacks} ({success_rate:.1f}%)")
        return success_rate >= 90

    finally:
        await server.stop()


async def test_infinite_loop_variants():
    """Test various infinite loop attack vectors"""
    print("🔄 Testing Infinite Loop Variants")

    server = await create_code_generation_server()
    loops_controlled = 0
    total_loops = 0

    loop_attacks = [
        ("Basic while loop", "while True: pass"),
        ("Recursive function", "def f(): f()\nf()"),
        ("Generator infinite loop", "def gen(): \n  while True: yield 1\nlist(gen())"),
        ("Nested loops", "while True:\n  for i in range(1000000): pass"),
        ("Sleep loop", "import time\nwhile True: time.sleep(0.1)")
    ]

    try:
        for attack_name, attack_code in loop_attacks:
            total_loops += 1
            start_time = time.time()

            result = await server.execute_code_sandboxed(
                attack_code,
                timeout=2.0,
                user_id="loop_audit"
            )

            execution_time = time.time() - start_time

            # Should timeout or be terminated within reasonable time
            controlled = execution_time <= 3.0 and (not result.success or not result.data.get("success", False))
            if controlled:
                loops_controlled += 1
                print(f"   ✅ Controlled: {attack_name} ({execution_time:.2f}s)")
            else:
                print(f"   ❌ UNCONTROLLED: {attack_name} ({execution_time:.2f}s)")

        success_rate = (loops_controlled / total_loops) * 100
        print(f"   ⏱️ Loop control rate: {loops_controlled}/{total_loops} ({success_rate:.1f}%)")
        return success_rate >= 90

    finally:
        await server.stop()


async def test_system_access_attempts():
    """Test various system access attack vectors"""
    print("🖥️ Testing System Access Attempts")

    server = await create_code_generation_server()
    accesses_blocked = 0
    total_attempts = 0

    system_attacks = [
        ("File system read", "open('/etc/passwd').read()"),
        ("File system write", "open('/tmp/malicious', 'w').write('hack')"),
        ("Environment variables", "import os; os.environ['PATH']"),
        ("System commands", "import os; os.system('ls -la')"),
        ("Process execution", "import subprocess; subprocess.run(['ps', 'aux'])"),
        ("Network access", "import urllib.request; urllib.request.urlopen('http://evil.com')"),
        ("Socket creation", "import socket; socket.socket().connect(('127.0.0.1', 22))"),
        ("Module import bypass", "__import__('os').system('whoami')"),
        ("Eval bypass", "eval('__import__(\"os\").system(\"id\")')"),
        ("Exec bypass", "exec('import subprocess; subprocess.run([\"uname\", \"-a\"])')")
    ]

    try:
        for attack_name, attack_code in system_attacks:
            total_attempts += 1

            result = await server.execute_code_sandboxed(
                attack_code,
                timeout=2.0,
                user_id="system_audit"
            )

            # Should be blocked by security validation or sandbox
            blocked = not result.success or not result.data.get("success", False)
            if blocked:
                accesses_blocked += 1
                print(f"   ✅ Blocked: {attack_name}")
            else:
                print(f"   ❌ SYSTEM BREACH: {attack_name}")
                if result.data and result.data.get("output"):
                    print(f"       Output: {result.data['output'][:100]}...")

        success_rate = (accesses_blocked / total_attempts) * 100
        print(f"   🔒 System access blocking: {accesses_blocked}/{total_attempts} ({success_rate:.1f}%)")
        return success_rate >= 95  # Stricter requirement for system access

    finally:
        await server.stop()


async def test_resource_exhaustion_edge_cases():
    """Test edge case resource exhaustion scenarios"""
    print("⚡ Testing Resource Exhaustion Edge Cases")

    server = await create_code_generation_server()
    cases_handled = 0
    total_cases = 0

    edge_cases = [
        ("CPU intensive computation", "sum(i**2 for i in range(10**6))"),
        ("Large file creation attempt", "open('/tmp/large', 'w').write('X' * (10**7))"),
        ("Thread bomb", "import threading\nfor i in range(1000): threading.Thread(target=lambda: None).start()"),
        ("Process fork bomb", "import os\nfor i in range(100): os.fork() if hasattr(os, 'fork') else None"),
        ("Import bomb", "for i in range(1000): __import__('sys')"),
        ("Exception spam", "for i in range(100000): \n  try: 1/0\n  except: pass"),
        ("Garbage collection stress", "import gc\nfor i in range(10000): gc.collect()"),
        ("Regex bomb", "import re\nre.search('(a+)+$', 'a' * 100 + 'b')")
    ]

    try:
        for case_name, case_code in edge_cases:
            total_cases += 1
            start_time = time.time()

            result = await server.execute_code_sandboxed(
                case_code,
                timeout=3.0,
                user_id="edge_audit"
            )

            execution_time = time.time() - start_time

            # Should be controlled by resource limits or timeout
            handled = execution_time <= 4.0 and (not result.success or not result.data.get("success", False))
            if handled:
                cases_handled += 1
                print(f"   ✅ Handled: {case_name} ({execution_time:.2f}s)")
            else:
                print(f"   ❌ UNHANDLED: {case_name} ({execution_time:.2f}s)")

        success_rate = (cases_handled / total_cases) * 100
        print(f"   🛡️ Edge case handling: {cases_handled}/{total_cases} ({success_rate:.1f}%)")
        return success_rate >= 85

    finally:
        await server.stop()


async def test_concurrent_attack_scenarios():
    """Test security under concurrent attack conditions"""
    print("🚀 Testing Concurrent Attack Scenarios")

    server = await create_code_generation_server()

    try:
        # Create mixed attack workload
        attack_tasks = []

        # Memory attacks
        for i in range(3):
            task = server.execute_code_sandboxed(
                f"x = [0] * (10**7)",
                timeout=2.0,
                user_id=f"concurrent_mem_{i}"
            )
            attack_tasks.append(task)

        # CPU attacks
        for i in range(3):
            task = server.execute_code_sandboxed(
                f"sum(i**2 for i in range(10**5))",
                timeout=2.0,
                user_id=f"concurrent_cpu_{i}"
            )
            attack_tasks.append(task)

        # System access attacks
        for i in range(4):
            task = server.execute_code_sandboxed(
                f"import os; os.system('echo attack_{i}')",
                timeout=2.0,
                user_id=f"concurrent_sys_{i}"
            )
            attack_tasks.append(task)

        print(f"   Running {len(attack_tasks)} concurrent attacks...")
        start_time = time.time()

        results = await asyncio.gather(*attack_tasks, return_exceptions=True)

        execution_time = time.time() - start_time
        print(f"   ⏱️ Concurrent execution time: {execution_time:.2f}s")

        # Analyze results
        attacks_blocked = 0
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                attacks_blocked += 1
            elif not result.success or not result.data.get("success", False):
                attacks_blocked += 1

        success_rate = (attacks_blocked / len(attack_tasks)) * 100
        print(f"   🛡️ Concurrent attacks blocked: {attacks_blocked}/{len(attack_tasks)} ({success_rate:.1f}%)")

        # Security should remain effective under load
        security_maintained = success_rate >= 90
        performance_maintained = execution_time < 10.0

        return security_maintained and performance_maintained

    finally:
        await server.stop()


async def run_comprehensive_security_audit():
    """Run complete security audit covering all attack vectors"""
    print("🔒 COMPREHENSIVE SECURITY AUDIT")
    print("=" * 60)
    print("Testing all security boundaries and attack vectors")
    print("to validate production-ready security posture.\n")

    tests = [
        ("Memory Exhaustion Attacks", test_memory_exhaustion_attacks),
        ("Infinite Loop Variants", test_infinite_loop_variants),
        ("System Access Attempts", test_system_access_attempts),
        ("Resource Exhaustion Edge Cases", test_resource_exhaustion_edge_cases),
        ("Concurrent Attack Scenarios", test_concurrent_attack_scenarios)
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
            status = "✅ SECURE" if result else "❌ VULNERABLE"
            print(f"   {status} ({execution_time:.2f}s)\n")

        except Exception as e:
            print(f"   ❌ TEST ERROR: {e}\n")
            results.append((test_name, False))

    # Security audit summary
    print("=" * 60)
    print("🔒 COMPREHENSIVE SECURITY AUDIT RESULTS")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ SECURE" if result else "❌ VULNERABLE"
        print(f"   {test_name}: {status}")

    security_score = (passed / total) * 100
    print(f"\n🛡️ Overall Security Score: {passed}/{total} ({security_score:.1f}%)")

    if security_score >= 95:
        print("\n🎉 SECURITY AUDIT PASSED - PRODUCTION READY!")
        print("   All critical security boundaries validated")
        print("   No significant vulnerabilities found")
        print("   Safe for autonomous learning deployment")
    elif security_score >= 85:
        print("\n⚠️ SECURITY CONCERNS IDENTIFIED")
        print("   Some vulnerabilities need addressing before production")
    else:
        print("\n❌ CRITICAL SECURITY VULNERABILITIES FOUND")
        print("   DO NOT deploy until security issues are resolved")

    return security_score >= 95


if __name__ == "__main__":
    success = asyncio.run(run_comprehensive_security_audit())
    exit(0 if success else 1)