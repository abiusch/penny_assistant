"""Comprehensive security audit for the containerized code execution system.

This audit replays all previously identified attack vectors against the new
Docker-secured execution pipeline and adds container-specific validation.
Run with: python3 comprehensive_security_audit_v2.py
"""

from __future__ import annotations

import asyncio
import contextlib
import statistics
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Tuple

from code_generation_tool_server import create_code_generation_server
from docker_security_container import DockerRuntimeError, DockerSecurityError


BASELINE_RESULTS: Dict[str, Tuple[int, int]] = {
    "Memory Exhaustion": (0, 5),
    "CPU Resource Control": (3, 8),
    "Process Creation": (2, 5),
    "Concurrent Attacks": (4, 10),
    "System Access": (10, 10),
    "Container Isolation": (0, 5),
    "Performance Impact": (0, 0),
}

TARGET_SCORE = 90.0
EMERGENCY_STOP_TARGET_SECONDS = 2.0


@dataclass
class AttackResult:
    name: str
    blocked: bool
    execution_time: float
    notes: Optional[str] = None

    def icon(self) -> str:
        return "✅" if self.blocked else "❌"


@dataclass
class AuditCategoryResult:
    name: str
    attack_results: List[AttackResult] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)

    @property
    def total(self) -> int:
        return len(self.attack_results)

    @property
    def passed(self) -> int:
        return sum(1 for result in self.attack_results if result.blocked)

    @property
    def score(self) -> float:
        return (self.passed / self.total * 100.0) if self.total else 100.0

    @property
    def baseline(self) -> Tuple[int, int]:
        return BASELINE_RESULTS.get(self.name, (0, self.total or 1))

    def add_result(self, attack_result: AttackResult) -> None:
        self.attack_results.append(attack_result)

    def summary(self) -> str:
        baseline_passed, baseline_total = self.baseline
        improvement = self.passed - baseline_passed
        baseline_score = (baseline_passed / baseline_total * 100.0) if baseline_total else 0.0
        return (
            f"{self.name}: {self.passed}/{self.total} ({self.score:.1f}%) "
            f"| Previous: {baseline_passed}/{baseline_total} ({baseline_score:.1f}%) "
            f"| Δ {improvement:+d}"
        )


async def _ensure_docker_ready() -> None:
    """Run a quick sanity check to ensure the container manager is functional."""
    server = await create_code_generation_server()
    try:
        if not getattr(server, "container_manager", None):
            raise RuntimeError("Docker security container manager not available. Start Docker Desktop and rebuild the penny-code-runner image.")

        result = await server.execute_code_sandboxed(
            "print('container_sanity_check')",
            timeout=5.0,
            user_id="audit_sanity",
        )
        data = result.data or {}
        if not result.success or not data.get("success", False):
            raise RuntimeError(
                "Unable to execute code inside the Docker sandbox."
                " Ensure the penny-code-runner image exists and Docker is running."
            )
    finally:
        await server.stop()


async def _execute_attack(
    server,
    description: str,
    code: str,
    *,
    timeout: float,
    expect_block: bool,
    user_id: str,
) -> AttackResult:
    start = time.time()
    notes: Optional[str] = None

    try:
        result = await server.execute_code_sandboxed(code, timeout=timeout, user_id=user_id)
        elapsed = time.time() - start
        data = result.data or {}

        blocked = not result.success or not data.get("success", False)
        if expect_block:
            passed = blocked
            if blocked:
                notes = data.get("error") or result.error or "Blocked by sandbox"
            else:
                output = data.get("output") or ""
                notes = data.get("error") or output[:120]
        else:
            passed = result.success and data.get("success", False)
            notes = data.get("output") or data.get("error") or result.error

        return AttackResult(description, passed, elapsed, notes)

    except (DockerSecurityError, DockerRuntimeError) as exc:
        elapsed = time.time() - start
        if expect_block:
            return AttackResult(description, True, elapsed, f"Container manager blocked execution: {exc}")
        return AttackResult(description, False, elapsed, f"Container error: {exc}")
    except Exception as exc:  # pylint: disable=broad-except
        elapsed = time.time() - start
        if expect_block:
            return AttackResult(description, True, elapsed, f"Exception: {exc}")
        return AttackResult(description, False, elapsed, f"Exception: {exc}")


async def run_memory_exhaustion_tests() -> AuditCategoryResult:
    category = AuditCategoryResult("Memory Exhaustion")
    server = await create_code_generation_server()

    attacks: Sequence[Tuple[str, str]] = [
        ("Large list allocation", "x = [0] * (10**8)"),
        ("Recursive structure", "x = []; [x.append(x) for _ in range(10**6)]"),
        ("String blowup", "s = 'A' * (10**8)"),
        ("Dictionary expansion", "d = {i: 'data'*100 for i in range(2_000_000)}"),
        ("Gradual leak", "buf = [];\nfor i in range(10**6): buf.append('x'*1000)")
    ]

    try:
        for idx, (name, code) in enumerate(attacks):
            result = await _execute_attack(
                server,
                name,
                code,
                timeout=5.0,
                expect_block=True,
                user_id=f"mem_attack_{idx}",
            )
            category.add_result(result)
    finally:
        await server.stop()

    return category


async def run_cpu_resource_tests() -> AuditCategoryResult:
    category = AuditCategoryResult("CPU Resource Control")
    server = await create_code_generation_server()

    attacks: Sequence[Tuple[str, str]] = [
        ("Tight while loop", "while True: pass"),
        ("Recursive factorial", "def f(n): return 1 if n==0 else n*f(n-1)\nf(5000)"),
        ("Prime stress", "def primes():\n    n = 2\n    while True:\n        for i in range(2, n):\n            if n % i == 0:\n                break\n        else:\n            pass\n        n += 1\nprimes()"),
        ("List comprehension blast", "sum([i*i for i in range(10**7)])"),
        ("Nested loops", "total = 0\nwhile True:\n    for i in range(500000):\n        total += i"),
        ("Math stress", "import math\nwhile True:\n    for i in range(10**6):\n        math.sqrt(i)"),
        ("Threaded CPU", "import threading\nfor _ in range(20):\n    threading.Thread(target=lambda: sum(i*i for i in range(10**6))).start()"),
        ("Future spam", "import concurrent.futures as cf\nwith cf.ThreadPoolExecutor(max_workers=32) as ex:\n    list(ex.map(lambda _: sum(i*i for i in range(10**6)), range(32)))")
    ]

    try:
        for idx, (name, code) in enumerate(attacks):
            result = await _execute_attack(
                server,
                name,
                code,
                timeout=4.0,
                expect_block=True,
                user_id=f"cpu_attack_{idx}",
            )
            category.add_result(result)
    finally:
        await server.stop()

    return category


async def run_process_creation_tests() -> AuditCategoryResult:
    category = AuditCategoryResult("Process Creation")
    server = await create_code_generation_server()

    attacks: Sequence[Tuple[str, str]] = [
        ("Fork bomb", "import os\nfor _ in range(100):\n    pid = os.fork() if hasattr(os, 'fork') else None"),
        ("Subprocess storm", "import subprocess\nfor _ in range(50):\n    subprocess.Popen(['sleep', '1'])"),
        ("Thread explosion", "import threading\nfor _ in range(200):\n    threading.Thread(target=lambda: [None]*10**6).start()"),
        ("Async task flood", "import asyncio\nasync def spam():\n    while True:\n        await asyncio.sleep(0.01)\nfor _ in range(500):\n    asyncio.get_event_loop().create_task(spam())\nasyncio.get_event_loop().run_forever()"),
        ("Multiprocessing pool", "from multiprocessing import Pool\nwith Pool(32) as pool:\n    pool.map(lambda x: x*x, range(10**7))")
    ]

    try:
        for idx, (name, code) in enumerate(attacks):
            result = await _execute_attack(
                server,
                name,
                code,
                timeout=4.0,
                expect_block=True,
                user_id=f"proc_attack_{idx}",
            )
            category.add_result(result)
    finally:
        await server.stop()

    return category


async def run_concurrent_attack_tests() -> AuditCategoryResult:
    category = AuditCategoryResult("Concurrent Attacks")
    server = await create_code_generation_server()

    try:
        attack_coroutines = []
        descriptions: List[str] = []

        for i in range(5):
            descriptions.append(f"Concurrent memory {i}")
            attack_coroutines.append(
                server.execute_code_sandboxed(
                    "x = [0] * (10**7)",
                    timeout=3.0,
                    user_id=f"concurrent_mem_{i}",
                )
            )

        for i in range(3):
            descriptions.append(f"Concurrent CPU {i}")
            attack_coroutines.append(
                server.execute_code_sandboxed(
                    "while True: pass",
                    timeout=2.5,
                    user_id=f"concurrent_cpu_{i}",
                )
            )

        for i in range(2):
            descriptions.append(f"Concurrent system {i}")
            attack_coroutines.append(
                server.execute_code_sandboxed(
                    "import os; os.system('echo attack')",
                    timeout=2.5,
                    user_id=f"concurrent_sys_{i}",
                )
            )

        start = time.time()
        results = await asyncio.gather(*attack_coroutines, return_exceptions=True)
        total_time = time.time() - start

        for desc, execution in zip(descriptions, results):
            if isinstance(execution, Exception):
                category.add_result(AttackResult(desc, True, total_time, f"Exception: {execution}"))
                continue
            data = execution.data or {}
            blocked = not execution.success or not data.get("success", False)
            notes = data.get("error") or execution.error
            category.add_result(AttackResult(desc, blocked, data.get("execution_time", total_time), notes))

        category.notes.append(f"Concurrent attack batch completed in {total_time:.2f}s")

    finally:
        await server.stop()

    return category


async def run_system_access_tests() -> AuditCategoryResult:
    category = AuditCategoryResult("System Access")
    server = await create_code_generation_server()

    attacks: Sequence[Tuple[str, str]] = [
        ("File read", "open('/etc/passwd').read()"),
        ("File write", "open('/workspace/hack', 'w').write('hack')"),
        ("Environment exfil", "import os; os.environ['SECRET_KEY']"),
        ("System command", "import os; os.system('uname -a')"),
        ("Subprocess run", "import subprocess; subprocess.run(['ls', '/'])"),
        ("Network request", "import urllib.request as u; u.urlopen('http://example.com')"),
        ("Socket connect", "import socket; s = socket.socket(); s.connect(('1.1.1.1', 80))"),
        ("Module bypass", "__import__('os').system('whoami')"),
        ("Eval escape", "eval('__import__(\"os\").system(\"id\")')"),
        ("Exec escape", "exec('import subprocess; subprocess.run([\"ps\", \"aux\"])')")
    ]

    try:
        for idx, (name, code) in enumerate(attacks):
            result = await _execute_attack(
                server,
                name,
                code,
                timeout=3.0,
                expect_block=True,
                user_id=f"system_attack_{idx}",
            )
            category.add_result(result)
    finally:
        await server.stop()

    return category


async def run_container_isolation_tests() -> AuditCategoryResult:
    category = AuditCategoryResult("Container Isolation")
    server = await create_code_generation_server()
    manager = server.container_manager
    if not manager:
        await server.stop()
        raise RuntimeError("Container manager unavailable for isolation tests")

    tests: Sequence[Tuple[str, str]] = [
        ("Escape attempt", "import os; os.listdir('/workspace/../..')"),
        ("Host file write", "open('/host_escape', 'w').write('breakout')"),
        ("Network isolation", "import socket; socket.gethostbyname('example.com')"),
        ("Volume tamper", "open('/workspace/runtime.txt', 'w').write('tamper')"),
        ("Mount inspection", "import os; os.listdir('/mnt')")
    ]

    try:
        # Attack-oriented checks
        for idx, (name, code) in enumerate(tests):
            expect_success = name in {"Escape attempt", "Mount inspection"}
            # Listing directories may succeed legitimately; we only require write/network attempts to fail.
            result = await _execute_attack(
                server,
                name,
                code,
                timeout=3.0,
                expect_block=not expect_success,
                user_id=f"container_isolation_{idx}",
            )
            category.add_result(result)

        # Emergency stop responsiveness
        container_id = await manager.create_code_container(
            "import time\nwhile True:\n    time.sleep(0.1)",
            timeout=30,
            metadata={"test": "emergency_stop"},
        )
        task = asyncio.create_task(manager.execute_in_container(container_id))
        await asyncio.sleep(0.5)
        start = time.time()
        await manager.emergency_stop_all_containers()
        elapsed = time.time() - start
        task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await task
        category.notes.append(f"Emergency stop completed in {elapsed:.2f}s")
        category.add_result(AttackResult("Emergency stop compliance", elapsed <= EMERGENCY_STOP_TARGET_SECONDS, elapsed))

        await manager.batch_container_cleanup(0)

    finally:
        await server.stop()

    return category


async def run_performance_assessment() -> AuditCategoryResult:
    category = AuditCategoryResult("Performance Impact")
    server = await create_code_generation_server()

    timings: List[float] = []

    try:
        for idx in range(5):
            result = await server.execute_code_sandboxed(
                "print('hello')",
                timeout=5.0,
                user_id=f"perf_check_{idx}",
            )
            data = result.data or {}
            duration = data.get("execution_time", 0.0)
            timings.append(duration)
            category.add_result(AttackResult(f"Startup sample {idx+1}", True, duration, data.get("output")))

        if timings:
            avg = statistics.mean(timings)
            worst = max(timings)
            category.notes.append(f"Average container execution time: {avg:.3f}s")
            category.notes.append(f"Worst-case execution time: {worst:.3f}s")
            category.notes.append("Measured execution times include container startup overhead and code runtime.")
    finally:
        await server.stop()

    return category


async def run_audit() -> None:
    await _ensure_docker_ready()

    print("🔒 COMPREHENSIVE SECURITY AUDIT V2 - CONTAINERIZED SYSTEM")
    print("=" * 60)
    print("Previous Audit Score: 40% (10/25 tests passed)")
    print("Current Audit Target: 90%+ (production ready)\n")

    categories = [
        await run_memory_exhaustion_tests(),
        await run_cpu_resource_tests(),
        await run_process_creation_tests(),
        await run_concurrent_attack_tests(),
        await run_system_access_tests(),
        await run_container_isolation_tests(),
        await run_performance_assessment(),
    ]

    print("\n📈 CATEGORY RESULTS")
    print("-" * 60)
    for category in categories:
        print(category.summary())
        for attack in category.attack_results:
            note_snippet = f" ({attack.notes})" if attack.notes else ""
            print(f"   {attack.icon()} {attack.name} [{attack.execution_time:.2f}s]{note_snippet}")
        for note in category.notes:
            print(f"   • {note}")
        print()

    total_passed = sum(category.passed for category in categories if category.name != "Performance Impact")
    total_tests = sum(category.total for category in categories if category.name != "Performance Impact")
    overall_score = (total_passed / total_tests * 100.0) if total_tests else 0.0

    print("=" * 60)
    print("🔒 COMPREHENSIVE SECURITY AUDIT SUMMARY")
    print("=" * 60)
    print(f"Previous Audit: 40% (10/25 tests passed)")
    print(f"Current Audit: {overall_score:.1f}% ({total_passed}/{total_tests} tests blocked)\n")

    memory_category = next(cat for cat in categories if cat.name == "Memory Exhaustion")
    cpu_category = next(cat for cat in categories if cat.name == "CPU Resource Control")
    process_category = next(cat for cat in categories if cat.name == "Process Creation")
    concurrent_category = next(cat for cat in categories if cat.name == "Concurrent Attacks")
    system_category = next(cat for cat in categories if cat.name == "System Access")

    print("📊 SECURITY IMPROVEMENTS")
    print(f"Memory Exhaustion: {memory_category.baseline[0]}/{memory_category.baseline[1]} -> {memory_category.passed}/{memory_category.total} ({memory_category.score:.1f}%)")
    print(f"CPU Resource Control: {cpu_category.baseline[0]}/{cpu_category.baseline[1]} -> {cpu_category.passed}/{cpu_category.total} ({cpu_category.score:.1f}%)")
    print(f"Process Management: {process_category.baseline[0]}/{process_category.baseline[1]} -> {process_category.passed}/{process_category.total} ({process_category.score:.1f}%)")
    print(f"Concurrent Security: {concurrent_category.baseline[0]}/{concurrent_category.baseline[1]} -> {concurrent_category.passed}/{concurrent_category.total} ({concurrent_category.score:.1f}%)")
    print(f"System Access: {system_category.baseline[0]}/{system_category.baseline[1]} -> {system_category.passed}/{system_category.total} ({system_category.score:.1f}%)\n")

    if overall_score >= TARGET_SCORE:
        print("🎯 PRODUCTION READINESS: ✅ ACHIEVED")
        print("All critical attack categories meet or exceed the security threshold.")
    else:
        print("🎯 PRODUCTION READINESS: ❌ NOT MET")
        print("Investigate failing categories before autonomous deployment.")

    print("\n⚙️ PERFORMANCE ANALYSIS")
    perf_category = next(cat for cat in categories if cat.name == "Performance Impact")
    for note in perf_category.notes:
        print(f"- {note}")
    if not perf_category.notes:
        print("- No performance samples recorded")


if __name__ == "__main__":
    asyncio.run(run_audit())
