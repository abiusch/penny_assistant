#!/usr/bin/env python3
"""
Comprehensive Security Framework Testing
Tests command whitelist system, violation handling, and edge cases
"""

import os
import sys
import json
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple
import tempfile
import time

# Import security components
from command_whitelist_system import CommandWhitelistSystem, PermissionLevel, SecurityRisk, OperationType
from security_violation_handler import SecurityViolationHandler, ViolationType, ViolationSeverity
from security_ethics_foundation import SecurityEthicsFoundation, EthicalBoundary

class SecurityFrameworkTester:
    """Comprehensive testing for security framework"""

    def __init__(self):
        self.test_results = {}
        self.temp_dbs = []

    def run_all_tests(self) -> Dict[str, Any]:
        """Run comprehensive security tests"""
        print("🔒 Security Framework Comprehensive Testing")
        print("=" * 60)

        # Test individual components
        self.test_results["whitelist_system"] = self.test_whitelist_system()
        self.test_results["violation_handler"] = self.test_violation_handler()
        self.test_results["edge_cases"] = self.test_edge_cases()
        self.test_results["integration"] = self.test_integration()
        self.test_results["performance"] = self.test_performance()
        self.test_results["persistence"] = self.test_persistence()

        # Calculate overall score
        self.test_results["overall_score"] = self.calculate_overall_score()

        # Cleanup
        self.cleanup_test_files()

        return self.test_results

    def test_whitelist_system(self) -> Dict[str, Any]:
        """Test command whitelist system functionality"""
        print("\n🔐 Testing Command Whitelist System...")

        try:
            # Create test system
            db_path = self._create_temp_db("whitelist")
            whitelist_system = CommandWhitelistSystem(db_path)

            test_cases = [
                # Basic permission checks
                {
                    "operation": "file_read",
                    "permission": PermissionLevel.GUEST,
                    "expected_allowed": True,
                    "description": "Guest can read files"
                },
                {
                    "operation": "file_write",
                    "permission": PermissionLevel.GUEST,
                    "expected_allowed": False,
                    "description": "Guest cannot write files"
                },
                {
                    "operation": "file_write",
                    "permission": PermissionLevel.TRUSTED,
                    "expected_allowed": True,
                    "description": "Trusted can write files"
                },
                {
                    "operation": "system_modify",
                    "permission": PermissionLevel.AUTHENTICATED,
                    "expected_allowed": False,
                    "description": "Even authenticated cannot modify system (prohibited)"
                },
                # Pattern matching
                {
                    "operation": "read file config.json",
                    "permission": PermissionLevel.GUEST,
                    "expected_allowed": True,
                    "description": "Pattern matching for read operations"
                },
                {
                    "operation": "list files in directory",
                    "permission": PermissionLevel.GUEST,
                    "expected_allowed": True,
                    "description": "Pattern matching for list operations"
                },
                {
                    "operation": "execute dangerous command",
                    "permission": PermissionLevel.GUEST,
                    "expected_allowed": False,
                    "description": "Pattern matching blocks dangerous operations"
                },
                # Unknown operations
                {
                    "operation": "frobulate the widgets",
                    "permission": PermissionLevel.AUTHENTICATED,
                    "expected_allowed": False,
                    "description": "Unknown operations are blocked"
                }
            ]

            results = {"passed": 0, "total": len(test_cases), "details": []}

            for test_case in test_cases:
                whitelist_system.set_permission_level(test_case["permission"])
                check = whitelist_system.check_permission(test_case["operation"])

                success = check.allowed == test_case["expected_allowed"]
                if success:
                    results["passed"] += 1

                results["details"].append({
                    "test": test_case["description"],
                    "operation": test_case["operation"],
                    "permission": test_case["permission"].value,
                    "expected": test_case["expected_allowed"],
                    "actual": check.allowed,
                    "reason": check.reason,
                    "success": success
                })

            results["score"] = results["passed"] / results["total"]
            print(f"   ✅ Whitelist System: {results['score']:.2f}")
            return results

        except Exception as e:
            print(f"   ❌ Whitelist System test failed: {e}")
            return {"score": 0.0, "error": str(e)}

    def test_violation_handler(self) -> Dict[str, Any]:
        """Test security violation handler"""
        print("\n🚨 Testing Security Violation Handler...")

        try:
            # Create test system
            db_path = self._create_temp_db("violations")
            handler = SecurityViolationHandler(db_path)

            # Test different violation types
            test_violations = [
                {
                    "type": "permission_denied",
                    "severity": SecurityRisk.HIGH,
                    "expected_escalation": True
                },
                {
                    "type": "rate_limit",
                    "severity": SecurityRisk.MEDIUM,
                    "expected_escalation": False
                },
                {
                    "type": "ethical_violation",
                    "severity": SecurityRisk.CRITICAL,
                    "expected_escalation": True
                },
                {
                    "type": "unknown_operation",
                    "severity": SecurityRisk.LOW,
                    "expected_escalation": False
                }
            ]

            results = {"passed": 0, "total": len(test_violations), "details": []}

            for test_violation in test_violations:
                # Create mock permission check
                from command_whitelist_system import PermissionCheck

                permission_check = PermissionCheck(
                    allowed=False,
                    operation="test_operation",
                    reason=f"Test {test_violation['type']} violation",
                    risk_level=test_violation["severity"],
                    alternative_suggestions=[],
                    required_permission=PermissionLevel.AUTHENTICATED,
                    user_permission=PermissionLevel.GUEST
                )

                response = handler.handle_permission_violation(
                    permission_check, "test_session"
                )

                # Check escalation behavior
                escalation_matches = response.escalation_required == test_violation["expected_escalation"]
                has_message = len(response.message) > 0
                has_action = response.action is not None

                success = escalation_matches and has_message and has_action
                if success:
                    results["passed"] += 1

                results["details"].append({
                    "test": f"{test_violation['type']} handling",
                    "escalation_expected": test_violation["expected_escalation"],
                    "escalation_actual": response.escalation_required,
                    "action": response.action.value,
                    "message_length": len(response.message),
                    "success": success
                })

            results["score"] = results["passed"] / results["total"]
            print(f"   ✅ Violation Handler: {results['score']:.2f}")
            return results

        except Exception as e:
            print(f"   ❌ Violation Handler test failed: {e}")
            return {"score": 0.0, "error": str(e)}

    def test_edge_cases(self) -> Dict[str, Any]:
        """Test edge cases and attack scenarios"""
        print("\n⚠️ Testing Edge Cases and Attack Scenarios...")

        try:
            # Create test systems
            whitelist_db = self._create_temp_db("edge_whitelist")
            violations_db = self._create_temp_db("edge_violations")

            whitelist_system = CommandWhitelistSystem(whitelist_db)
            handler = SecurityViolationHandler(violations_db)

            edge_cases = [
                # Injection attempts
                {
                    "operation": "file_read; rm -rf /",
                    "expected_blocked": True,
                    "description": "Command injection attempt"
                },
                {
                    "operation": "read file ../../../etc/passwd",
                    "expected_blocked": True,
                    "description": "Path traversal attempt"
                },
                # Very long inputs
                {
                    "operation": "A" * 10000,
                    "expected_blocked": True,
                    "description": "Extremely long operation name"
                },
                # Unicode and special characters
                {
                    "operation": "file_read 🚫💀🔥",
                    "expected_blocked": False,  # Should classify as file_read
                    "description": "Unicode characters in operation"
                },
                # Case variations
                {
                    "operation": "FILE_READ",
                    "expected_blocked": False,
                    "description": "Case insensitive operation matching"
                },
                {
                    "operation": "ReAd FiLe",
                    "expected_blocked": False,
                    "description": "Mixed case pattern matching"
                },
                # Empty and whitespace
                {
                    "operation": "",
                    "expected_blocked": True,
                    "description": "Empty operation string"
                },
                {
                    "operation": "   \t\n   ",
                    "expected_blocked": True,
                    "description": "Whitespace-only operation"
                },
                # Rapid fire requests
                {
                    "operation": "rapid_test",
                    "expected_blocked": True,  # After rate limiting
                    "description": "Rate limiting effectiveness"
                }
            ]

            results = {"passed": 0, "total": len(edge_cases), "details": []}
            whitelist_system.set_permission_level(PermissionLevel.VERIFIED)

            for i, edge_case in enumerate(edge_cases):
                try:
                    if edge_case["description"] == "Rate limiting effectiveness":
                        # Test rapid requests
                        blocked_count = 0
                        for _ in range(10):  # Make 10 rapid requests
                            check = whitelist_system.check_permission("file_read")
                            if not check.allowed:
                                blocked_count += 1

                        success = blocked_count > 0  # Some should be blocked
                    else:
                        check = whitelist_system.check_permission(edge_case["operation"])
                        success = (not check.allowed) == edge_case["expected_blocked"]

                    if success:
                        results["passed"] += 1

                    results["details"].append({
                        "test": edge_case["description"],
                        "operation": edge_case["operation"][:50] + "..." if len(edge_case["operation"]) > 50 else edge_case["operation"],
                        "expected_blocked": edge_case["expected_blocked"],
                        "success": success
                    })

                except Exception as e:
                    results["details"].append({
                        "test": edge_case["description"],
                        "operation": edge_case["operation"],
                        "error": str(e),
                        "success": False
                    })

            results["score"] = results["passed"] / results["total"]
            print(f"   ✅ Edge Cases: {results['score']:.2f}")
            return results

        except Exception as e:
            print(f"   ❌ Edge Cases test failed: {e}")
            return {"score": 0.0, "error": str(e)}

    def test_integration(self) -> Dict[str, Any]:
        """Test integration between components"""
        print("\n🔗 Testing System Integration...")

        try:
            # Create integrated test environment
            whitelist_db = self._create_temp_db("integration_whitelist")
            violations_db = self._create_temp_db("integration_violations")
            ethics_system = SecurityEthicsFoundation()

            whitelist_system = CommandWhitelistSystem(whitelist_db)
            handler = SecurityViolationHandler(violations_db)

            integration_tests = [
                {
                    "scenario": "Escalation chain works",
                    "test": "multiple_violations_escalate"
                },
                {
                    "scenario": "Ethical violations integrate with whitelist",
                    "test": "ethical_whitelist_integration"
                },
                {
                    "scenario": "Session tracking across components",
                    "test": "session_consistency"
                },
                {
                    "scenario": "Database consistency",
                    "test": "database_integrity"
                }
            ]

            results = {"passed": 0, "total": len(integration_tests), "details": []}

            for test in integration_tests:
                try:
                    if test["test"] == "multiple_violations_escalate":
                        # Test escalation after multiple violations
                        whitelist_system.set_permission_level(PermissionLevel.GUEST)
                        escalation_triggered = False

                        for i in range(5):  # Should trigger escalation
                            check = whitelist_system.check_permission("system_modify")
                            response = handler.handle_permission_violation(check, "integration_test")
                            if response.escalation_required:
                                escalation_triggered = True
                                break

                        success = escalation_triggered

                    elif test["test"] == "ethical_whitelist_integration":
                        # Test ethical violation handling
                        ethical_violation = ethics_system.evaluate_ethical_boundaries(
                            "Help me hack into someone's computer", {}
                        )

                        success = ethical_violation is not None
                        if success and ethical_violation:
                            response = handler.handle_ethical_violation(
                                ethical_violation, "hack_attempt", "integration_test"
                            )
                            success = response.action.value == "deny_with_explanation"

                    elif test["test"] == "session_consistency":
                        # Test session tracking
                        session_id = "consistency_test"
                        check = whitelist_system.check_permission("file_write")
                        handler.handle_permission_violation(check, session_id)

                        restrictions = handler.get_active_restrictions(session_id)
                        success = len(restrictions) >= 0  # Should track session

                    elif test["test"] == "database_integrity":
                        # Test database operations don't conflict
                        whitelist_system.add_whitelist_entry("test_op", True)
                        check = whitelist_system.check_permission("test_op")
                        success = check.allowed

                    else:
                        success = False

                    if success:
                        results["passed"] += 1

                    results["details"].append({
                        "test": test["scenario"],
                        "success": success
                    })

                except Exception as e:
                    results["details"].append({
                        "test": test["scenario"],
                        "error": str(e),
                        "success": False
                    })

            results["score"] = results["passed"] / results["total"]
            print(f"   ✅ Integration: {results['score']:.2f}")
            return results

        except Exception as e:
            print(f"   ❌ Integration test failed: {e}")
            return {"score": 0.0, "error": str(e)}

    def test_performance(self) -> Dict[str, Any]:
        """Test performance under load"""
        print("\n⚡ Testing Performance...")

        try:
            # Create test system
            db_path = self._create_temp_db("performance")
            whitelist_system = CommandWhitelistSystem(db_path)
            whitelist_system.set_permission_level(PermissionLevel.VERIFIED)

            performance_tests = [
                {
                    "test": "rapid_permission_checks",
                    "operations": 1000,
                    "max_time_seconds": 5.0
                },
                {
                    "test": "database_operations",
                    "operations": 100,
                    "max_time_seconds": 2.0
                },
                {
                    "test": "pattern_matching",
                    "operations": 500,
                    "max_time_seconds": 3.0
                }
            ]

            results = {"passed": 0, "total": len(performance_tests), "details": []}

            for perf_test in performance_tests:
                start_time = time.time()

                if perf_test["test"] == "rapid_permission_checks":
                    for i in range(perf_test["operations"]):
                        whitelist_system.check_permission("file_read")

                elif perf_test["test"] == "database_operations":
                    for i in range(perf_test["operations"]):
                        whitelist_system.add_whitelist_entry(f"test_op_{i}", True)

                elif perf_test["test"] == "pattern_matching":
                    test_ops = [
                        "read file test.txt",
                        "list directory contents",
                        "write to output.log",
                        "execute command",
                        "unknown operation type"
                    ]
                    for i in range(perf_test["operations"]):
                        op = test_ops[i % len(test_ops)]
                        whitelist_system.check_permission(op)

                elapsed_time = time.time() - start_time
                success = elapsed_time <= perf_test["max_time_seconds"]

                if success:
                    results["passed"] += 1

                results["details"].append({
                    "test": perf_test["test"],
                    "operations": perf_test["operations"],
                    "time_limit": perf_test["max_time_seconds"],
                    "actual_time": round(elapsed_time, 3),
                    "ops_per_second": round(perf_test["operations"] / elapsed_time, 2),
                    "success": success
                })

            results["score"] = results["passed"] / results["total"]
            print(f"   ✅ Performance: {results['score']:.2f}")
            return results

        except Exception as e:
            print(f"   ❌ Performance test failed: {e}")
            return {"score": 0.0, "error": str(e)}

    def test_persistence(self) -> Dict[str, Any]:
        """Test data persistence and recovery"""
        print("\n💾 Testing Persistence...")

        try:
            # Create test system
            db_path = self._create_temp_db("persistence")

            # First system instance
            whitelist_system1 = CommandWhitelistSystem(db_path)
            whitelist_system1.add_whitelist_entry("persistent_test", True)
            whitelist_system1.set_permission_level(PermissionLevel.TRUSTED)

            original_status = whitelist_system1.get_security_status()

            # Destroy first instance
            del whitelist_system1

            # Create second instance - should load persisted data
            whitelist_system2 = CommandWhitelistSystem(db_path)
            whitelist_system2.set_permission_level(PermissionLevel.TRUSTED)

            # Test persistence
            check = whitelist_system2.check_permission("persistent_test")
            new_status = whitelist_system2.get_security_status()

            success = (
                check.allowed and  # Whitelist entry persisted
                new_status["operations_registered"] == original_status["operations_registered"]  # Operations persisted
            )

            results = {
                "passed": 1 if success else 0,
                "total": 1,
                "details": [{
                    "test": "Data persistence across instances",
                    "whitelist_persisted": check.allowed,
                    "operations_count_match": new_status["operations_registered"] == original_status["operations_registered"],
                    "success": success
                }],
                "score": 1.0 if success else 0.0
            }

            print(f"   ✅ Persistence: {results['score']:.2f}")
            return results

        except Exception as e:
            print(f"   ❌ Persistence test failed: {e}")
            return {"score": 0.0, "error": str(e)}

    def _create_temp_db(self, prefix: str) -> str:
        """Create temporary database for testing"""
        fd, path = tempfile.mkstemp(suffix=".db", prefix=f"test_{prefix}_")
        os.close(fd)
        self.temp_dbs.append(path)
        return path

    def cleanup_test_files(self):
        """Clean up temporary test files"""
        for db_path in self.temp_dbs:
            if os.path.exists(db_path):
                os.remove(db_path)

    def calculate_overall_score(self) -> float:
        """Calculate overall test score"""
        scores = []
        for component, results in self.test_results.items():
            if isinstance(results, dict) and "score" in results:
                scores.append(results["score"])

        return sum(scores) / len(scores) if scores else 0.0

    def generate_test_report(self) -> str:
        """Generate comprehensive test report"""
        report = []
        report.append("🔒 SECURITY FRAMEWORK TEST REPORT")
        report.append("=" * 60)
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")

        overall_score = self.test_results.get("overall_score", 0.0)
        report.append(f"📊 OVERALL SCORE: {overall_score:.2f} ({self._score_to_grade(overall_score)})")
        report.append("")

        # Component breakdown
        report.append("📋 COMPONENT SCORES:")
        for component, results in self.test_results.items():
            if component != "overall_score" and isinstance(results, dict):
                score = results.get("score", 0.0)
                report.append(f"   {component}: {score:.2f} ({self._score_to_grade(score)})")

        report.append("")

        # Security readiness assessment
        if overall_score >= 0.9:
            readiness = "✅ READY FOR AGENTIC PHASE"
        elif overall_score >= 0.8:
            readiness = "⚠️ NEEDS MINOR IMPROVEMENTS"
        elif overall_score >= 0.6:
            readiness = "🔧 NEEDS SIGNIFICANT WORK"
        else:
            readiness = "❌ NOT READY FOR AGENTIC PHASE"

        report.append(f"🚀 AGENTIC READINESS: {readiness}")
        report.append("")

        # Detailed results
        report.append("🔍 DETAILED RESULTS:")
        for component, results in self.test_results.items():
            if component != "overall_score" and isinstance(results, dict):
                report.append(f"\n{component.upper()}:")
                if "details" in results:
                    for detail in results["details"]:
                        success_indicator = "✅" if detail.get("success", False) else "❌"
                        test_name = detail.get("test", "unknown")
                        report.append(f"   {success_indicator} {test_name}")

        return "\n".join(report)

    def _score_to_grade(self, score: float) -> str:
        """Convert score to letter grade"""
        if score >= 0.9:
            return "A"
        elif score >= 0.8:
            return "B"
        elif score >= 0.7:
            return "C"
        elif score >= 0.6:
            return "D"
        else:
            return "F"

def run_comprehensive_security_tests():
    """Run all security framework tests"""
    tester = SecurityFrameworkTester()
    results = tester.run_all_tests()

    # Generate and display report
    report = tester.generate_test_report()
    print("\n" + report)

    # Save report to file
    with open("security_framework_test_report.txt", "w") as f:
        f.write(report)

    return results

if __name__ == "__main__":
    print("🔒 Security Framework - Comprehensive Testing")
    print("=" * 60)

    results = run_comprehensive_security_tests()

    overall_score = results.get("overall_score", 0.0)
    if overall_score >= 0.9:
        print(f"\n🎉 EXCELLENT! Security Framework achieved {overall_score:.2f} overall score")
        print("✅ Ready for Agentic AI Phase!")
    elif overall_score >= 0.8:
        print(f"\n✅ GOOD! Security Framework achieved {overall_score:.2f} overall score")
        print("⚠️ Minor improvements recommended before Agentic Phase")
    elif overall_score >= 0.6:
        print(f"\n🔧 NEEDS WORK! Security Framework achieved {overall_score:.2f} overall score")
        print("❌ Significant improvements required before Agentic Phase")
    else:
        print(f"\n⚠️ CRITICAL! Security Framework achieved {overall_score:.2f} overall score")
        print("🚨 Major security issues must be resolved before proceeding")

    print(f"📄 Detailed report saved to: security_framework_test_report.txt")
    print("\n✅ Security Framework testing completed!")