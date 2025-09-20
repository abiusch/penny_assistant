#!/usr/bin/env python3
"""
Comprehensive Test Suite for Security Streaming System
Tests all components individually and in integration
"""

import asyncio
import logging
import time
import unittest
from datetime import datetime, timedelta
from typing import Dict, List, Any
import os
import sys

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from security_streaming_processor import SecurityStreamingProcessor, SecurityDecision, DecisionConfidence
    from security_emergency_fallback import SecurityFallbackRuleEngine, EmergencyThreatLevel
    from security_timeout_manager import SecurityTimeoutManager, TimeoutSeverity
    from security_decision_cache import SecurityDecisionCache, CacheEvictionPolicy
    from integrated_security_streaming_system import IntegratedSecurityStreamingSystem
except ImportError as e:
    print(f"Import error: {e}")
    print("Please ensure all security components are in the same directory")
    sys.exit(1)

class TestSecurityStreamingProcessor(unittest.TestCase):
    """Test the streaming security processor"""

    def setUp(self):
        self.processor = SecurityStreamingProcessor(
            db_path="test_streaming.db",
            llm_timeout_seconds=1.0
        )

    def tearDown(self):
        self.processor.shutdown()
        if os.path.exists("test_streaming.db"):
            os.remove("test_streaming.db")

    def test_cache_functionality(self):
        """Test caching system"""
        cache = self.processor.cache

        # Test cache miss
        entry = cache.get("test_operation", {"param": "value"})
        self.assertIsNone(entry)

        # Test cache set and get
        cache.set("test_operation", {"param": "value"},
                 SecurityDecision.ALLOW, DecisionConfidence.HIGH, "Test reasoning")

        entry = cache.get("test_operation", {"param": "value"})
        self.assertIsNotNone(entry)
        self.assertEqual(entry.decision, SecurityDecision.ALLOW)

    def test_rule_based_evaluation(self):
        """Test rule-based evaluation"""
        evaluator = self.processor.rule_evaluator

        # Test blocking rule
        decision = evaluator.evaluate("rm -rf /", {})
        self.assertIsNotNone(decision)
        self.assertEqual(decision.decision, SecurityDecision.BLOCK)

        # Test allowing rule
        decision = evaluator.evaluate("help", {})
        self.assertIsNotNone(decision)
        self.assertEqual(decision.decision, SecurityDecision.ALLOW)

    async def test_streaming_evaluation(self):
        """Test streaming evaluation"""
        decisions = []
        async for decision in self.processor.evaluate_security_request(
            "file_read", {"path": "test.txt"}, "test_session", "test_req"
        ):
            decisions.append(decision)

        self.assertGreater(len(decisions), 0)
        final_decision = decisions[-1]
        self.assertIn(final_decision.decision, [SecurityDecision.ALLOW, SecurityDecision.BLOCK])

class TestSecurityFallbackEngine(unittest.TestCase):
    """Test the emergency fallback engine"""

    def setUp(self):
        self.engine = SecurityFallbackRuleEngine("test_emergency.db")

    def tearDown(self):
        if os.path.exists("test_emergency.db"):
            os.remove("test_emergency.db")

    def test_critical_threat_detection(self):
        """Test detection of critical threats"""
        decision = self.engine.evaluate_emergency_request(
            "rm -rf /", {"force": True}, "test_session"
        )

        self.assertEqual(decision.threat_level, EmergencyThreatLevel.CRITICAL)
        self.assertTrue(decision.requires_escalation)

    def test_safe_operation_detection(self):
        """Test detection of safe operations"""
        decision = self.engine.evaluate_emergency_request(
            "help", {}, "test_session"
        )

        self.assertEqual(decision.threat_level, EmergencyThreatLevel.SAFE)
        self.assertFalse(decision.requires_escalation)

    def test_custom_rule_addition(self):
        """Test adding custom rules"""
        from security_emergency_fallback import EmergencyRule, FallbackAction

        custom_rule = EmergencyRule(
            rule_id="test_001",
            name="Test Rule",
            pattern="test_dangerous_command",
            threat_level=EmergencyThreatLevel.HIGH,
            action=FallbackAction.IMMEDIATE_BLOCK,
            description="Test dangerous command"
        )

        success = self.engine.add_custom_rule(custom_rule)
        self.assertTrue(success)

        decision = self.engine.evaluate_emergency_request(
            "test_dangerous_command", {}, "test_session"
        )
        self.assertEqual(decision.threat_level, EmergencyThreatLevel.HIGH)

class TestSecurityTimeoutManager(unittest.TestCase):
    """Test the timeout manager"""

    def setUp(self):
        self.manager = SecurityTimeoutManager(default_timeout_seconds=1.0)

    async def test_fast_operation(self):
        """Test operation that completes within timeout"""
        async def fast_op(operation: str, parameters: Dict[str, Any]):
            await asyncio.sleep(0.1)
            return {"decision": "allow", "reason": "Fast operation"}

        result = await self.manager.execute_with_timeout(
            "test_operation", {}, "test_session", fast_op
        )

        self.assertTrue(result["success"])
        self.assertFalse(result["timeout_used"])
        self.assertEqual(result["result"]["decision"], "allow")

    async def test_slow_operation_timeout(self):
        """Test operation that times out"""
        async def slow_op(operation: str, parameters: Dict[str, Any]):
            await asyncio.sleep(2.0)  # Will timeout
            return {"decision": "allow", "reason": "Slow operation"}

        result = await self.manager.execute_with_timeout(
            "test_operation", {}, "test_session", slow_op
        )

        self.assertTrue(result["success"])
        self.assertTrue(result["timeout_used"])
        # Should use fallback decision

    async def test_safe_default_rules(self):
        """Test safe default rule application"""
        async def timeout_op(operation: str, parameters: Dict[str, Any]):
            await asyncio.sleep(2.0)
            return {"decision": "allow"}

        # Test safe operation (help should be allowed by default)
        result = await self.manager.execute_with_timeout(
            "help", {}, "test_session", timeout_op, "help_query"
        )

        self.assertTrue(result["success"])
        # Help operations should be allowed even on timeout

class TestSecurityDecisionCache(unittest.TestCase):
    """Test the decision cache system"""

    def setUp(self):
        self.cache = SecurityDecisionCache(
            db_path="test_cache.db",
            max_entries=100,
            default_ttl_seconds=300
        )

    def tearDown(self):
        if os.path.exists("test_cache.db"):
            os.remove("test_cache.db")

    def test_cache_key_generation(self):
        """Test cache key generation"""
        key1 = self.cache.generate_cache_key(
            "file_read", {"path": "/test.txt"}, {"user": "test"}, {}, "standard"
        )
        key2 = self.cache.generate_cache_key(
            "file_read", {"path": "/test.txt"}, {"user": "test"}, {}, "standard"
        )

        self.assertEqual(key1.to_string(), key2.to_string())

        # Different parameters should generate different keys
        key3 = self.cache.generate_cache_key(
            "file_read", {"path": "/other.txt"}, {"user": "test"}, {}, "standard"
        )
        self.assertNotEqual(key1.to_string(), key3.to_string())

    def test_cache_operations(self):
        """Test basic cache operations"""
        from security_decision_cache import DecisionConfidence as CacheConfidence

        # Test put and get
        key = self.cache.generate_cache_key("test_op", {}, {}, {}, "standard")

        success = self.cache.put(
            key, "allow", CacheConfidence.HIGH, "Test decision"
        )
        self.assertTrue(success)

        entry = self.cache.get(key)
        self.assertIsNotNone(entry)
        self.assertEqual(entry.decision, "allow")
        self.assertEqual(entry.confidence, CacheConfidence.HIGH)

    def test_cache_invalidation(self):
        """Test cache invalidation"""
        from security_decision_cache import DecisionConfidence as CacheConfidence

        key = self.cache.generate_cache_key("file_read", {"path": "/test"}, {}, {}, "standard")
        self.cache.put(key, "allow", CacheConfidence.HIGH, "Test")

        # Verify entry exists
        entry = self.cache.get(key)
        self.assertIsNotNone(entry)

        # Invalidate
        self.cache.invalidate("file_read", "test invalidation")

        # Entry should be gone
        entry = self.cache.get(key)
        self.assertIsNone(entry)

class TestIntegratedSecuritySystem(unittest.TestCase):
    """Test the integrated security system"""

    def setUp(self):
        self.system = IntegratedSecurityStreamingSystem(
            cache_config={"db_path": "test_integrated_cache.db"},
            timeout_config={"default_timeout": 1.0},
            fallback_config={"db_path": "test_integrated_fallback.db"},
            streaming_config={"db_path": "test_integrated_streaming.db"}
        )

    def tearDown(self):
        self.system.shutdown()
        # Clean up test databases
        test_files = [
            "test_integrated_cache.db", "test_integrated_fallback.db",
            "test_integrated_streaming.db", "integrated_violations.db"
        ]
        for file in test_files:
            if os.path.exists(file):
                os.remove(file)

    async def test_fast_cache_response(self):
        """Test fast cache response"""
        # First request should miss cache
        decisions1 = []
        async for decision in self.system.evaluate_security_request(
            "help", {}, "test_session", {"user": "test"}, {"session": "test"}
        ):
            decisions1.append(decision)

        self.assertGreater(len(decisions1), 0)
        first_decision = decisions1[0]

        # Second identical request should hit cache
        decisions2 = []
        async for decision in self.system.evaluate_security_request(
            "help", {}, "test_session", {"user": "test"}, {"session": "test"}
        ):
            decisions2.append(decision)

        self.assertGreater(len(decisions2), 0)
        second_decision = decisions2[0]

        # Second request should be faster and from cache
        self.assertTrue(second_decision.cache_used)
        self.assertLess(second_decision.processing_time_ms, first_decision.processing_time_ms)

    async def test_dangerous_operation_blocking(self):
        """Test that dangerous operations are blocked quickly"""
        decisions = []
        async for decision in self.system.evaluate_security_request(
            "rm -rf /", {"force": True}, "test_session"
        ):
            decisions.append(decision)

        self.assertGreater(len(decisions), 0)
        final_decision = decisions[0]

        self.assertEqual(final_decision.decision, "block")
        self.assertIn(final_decision.confidence, ["high", "very_high"])
        self.assertLess(final_decision.processing_time_ms, 50.0)  # Should be very fast

    async def test_system_status(self):
        """Test system status reporting"""
        # Make a few requests first
        for i in range(3):
            async for decision in self.system.evaluate_security_request(
                f"test_operation_{i}", {"param": i}, f"session_{i}"
            ):
                break  # Just get first decision

        status = await self.system.get_system_status()

        self.assertIn("system_metrics", status)
        self.assertIn("cache_info", status)
        self.assertIn("timeout_stats", status)
        self.assertGreater(status["system_metrics"]["total_requests"], 0)

class PerformanceTests:
    """Performance benchmarks for the security system"""

    @staticmethod
    async def benchmark_response_times():
        """Benchmark response times for different scenarios"""
        system = IntegratedSecurityStreamingSystem(
            timeout_config={"default_timeout": 2.0}
        )

        scenarios = [
            ("help", {}, "Safe operation"),
            ("file_read", {"path": "config.json"}, "Read operation"),
            ("rm -rf /", {"force": True}, "Dangerous operation"),
            ("network_request", {"url": "http://example.com"}, "Network operation"),
        ]

        print("\n🚀 Performance Benchmark")
        print("=" * 50)

        results = {}

        for operation, params, description in scenarios:
            times = []
            cache_hits = 0

            # Run each scenario multiple times
            for i in range(5):
                start_time = time.time()

                async for decision in system.evaluate_security_request(
                    operation, params, f"bench_session_{i}"
                ):
                    end_time = time.time()
                    processing_time = (end_time - start_time) * 1000
                    times.append(processing_time)

                    if decision.cache_used:
                        cache_hits += 1
                    break

            avg_time = sum(times) / len(times)
            min_time = min(times)
            max_time = max(times)

            results[operation] = {
                "description": description,
                "avg_time_ms": avg_time,
                "min_time_ms": min_time,
                "max_time_ms": max_time,
                "cache_hits": cache_hits
            }

            print(f"{description:20} | Avg: {avg_time:6.1f}ms | Min: {min_time:6.1f}ms | Max: {max_time:6.1f}ms | Cache: {cache_hits}/5")

        system.shutdown()

        # Cleanup
        test_files = [
            "integrated_security_cache.db", "integrated_emergency_rules.db",
            "integrated_streaming.db", "integrated_violations.db"
        ]
        for file in test_files:
            if os.path.exists(file):
                os.remove(file)

        return results

async def run_all_tests():
    """Run all tests and benchmarks"""
    print("🧪 Security Streaming System Test Suite")
    print("=" * 60)

    # Configure logging
    logging.basicConfig(level=logging.WARNING)  # Reduce noise during tests

    # Run unit tests
    test_classes = [
        TestSecurityStreamingProcessor,
        TestSecurityFallbackEngine,
        TestSecurityTimeoutManager,
        TestSecurityDecisionCache,
        TestIntegratedSecuritySystem
    ]

    total_tests = 0
    passed_tests = 0
    failed_tests = []

    for test_class in test_classes:
        print(f"\n📋 Running {test_class.__name__}")

        suite = unittest.TestLoader().loadTestsFromTestCase(test_class)
        runner = unittest.TextTestRunner(verbosity=1, stream=open(os.devnull, 'w'))

        # Run synchronous tests
        sync_result = runner.run(suite)
        total_tests += sync_result.testsRun
        passed_tests += sync_result.testsRun - len(sync_result.failures) - len(sync_result.errors)

        if sync_result.failures:
            failed_tests.extend([f"{test_class.__name__}: {f[0]}" for f in sync_result.failures])
        if sync_result.errors:
            failed_tests.extend([f"{test_class.__name__}: {e[0]}" for e in sync_result.errors])

        # Run async tests manually
        if hasattr(test_class, 'setUp'):
            test_instance = test_class()
            test_instance.setUp()

            async_methods = [method for method in dir(test_instance)
                           if method.startswith('test_') and asyncio.iscoroutinefunction(getattr(test_instance, method))]

            for method_name in async_methods:
                try:
                    print(f"   Running {method_name}...")
                    await getattr(test_instance, method_name)()
                    passed_tests += 1
                    total_tests += 1
                except Exception as e:
                    failed_tests.append(f"{test_class.__name__}.{method_name}: {e}")
                    total_tests += 1

            if hasattr(test_instance, 'tearDown'):
                test_instance.tearDown()

    # Run performance benchmarks
    print(f"\n⚡ Performance Benchmarks")
    await PerformanceTests.benchmark_response_times()

    # Summary
    print(f"\n📊 Test Summary")
    print("=" * 30)
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {len(failed_tests)}")
    print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")

    if failed_tests:
        print(f"\n❌ Failed Tests:")
        for test in failed_tests:
            print(f"   - {test}")
    else:
        print(f"\n✅ All tests passed!")

    return len(failed_tests) == 0

if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)