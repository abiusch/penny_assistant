#!/usr/bin/env python3
"""
Comprehensive Emergency Stop System Testing
Phase A2: Multi-Channel Emergency Stop Implementation

Tests all components of the emergency stop system:
- Voice phrase detection
- Keyboard interrupt handling
- Timeout-based triggers
- Process termination
- Emergency state management
- Multi-interface coordination
"""

import time
import threading
import tempfile
import os
import signal
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any

from multi_channel_emergency_stop import (
    MultiChannelEmergencyStop,
    VoiceEmergencyDetector,
    EmergencyTrigger,
    EmergencyState
)


class EmergencyStopTester:
    """Comprehensive test suite for emergency stop system"""

    def __init__(self):
        self.test_results = {}
        self.logger = logging.getLogger("emergency_test")

    def run_all_tests(self) -> Dict[str, Any]:
        """Run comprehensive emergency stop tests"""
        print("🚨 EMERGENCY STOP SYSTEM - COMPREHENSIVE TESTING")
        print("=" * 60)

        tests = [
            ("voice_phrase_detection", self.test_voice_phrase_detection),
            ("keyboard_interrupt_handling", self.test_keyboard_interrupt_handling),
            ("timeout_triggers", self.test_timeout_triggers),
            ("process_termination", self.test_process_termination),
            ("emergency_state_management", self.test_emergency_state_management),
            ("multi_interface_coordination", self.test_multi_interface_coordination),
            ("recovery_procedures", self.test_recovery_procedures),
            ("stress_testing", self.test_stress_scenarios)
        ]

        for test_name, test_func in tests:
            try:
                print(f"\n🔍 Testing {test_name.replace('_', ' ').title()}...")
                result = test_func()
                self.test_results[test_name] = result
                score = result.get("score", 0.0)
                status = "✅" if score >= 0.8 else "⚠️" if score >= 0.6 else "❌"
                print(f"   {status} {test_name}: {score:.2f}")

            except Exception as e:
                print(f"   ❌ {test_name} test failed: {e}")
                self.test_results[test_name] = {
                    "score": 0.0,
                    "error": str(e),
                    "passed": 0,
                    "total": 1
                }

        # Calculate overall score
        total_score = sum(result.get("score", 0) for result in self.test_results.values())
        overall_score = total_score / len(self.test_results) if self.test_results else 0

        self.test_results["overall_score"] = overall_score

        return self.test_results

    def test_voice_phrase_detection(self) -> Dict[str, Any]:
        """Test voice phrase emergency detection"""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as f:
            db_path = f.name

        try:
            emergency_system = MultiChannelEmergencyStop(db_path)
            voice_detector = VoiceEmergencyDetector(emergency_system)

            test_cases = [
                # Should trigger emergency
                ("emergency stop", 0.9, True, "Primary emergency phrase"),
                ("halt penny", 0.9, True, "Primary halt phrase"),
                ("abort everything", 0.8, True, "Emergency abort"),
                ("stop everything now", 0.9, True, "Stop everything phrase"),

                # Should not trigger (low confidence or non-emergency)
                ("please stop talking", 0.9, False, "Non-emergency stop"),
                ("emergency stop", 0.3, False, "Low confidence emergency"),
                ("hello penny", 0.9, False, "Normal greeting"),

                # Context-based detection
                ("stop", 0.8, False, "Single stop (first time)"),
                ("stop again", 0.8, False, "Stop again"),
                ("stop please", 0.8, True, "Third stop - should trigger contextual")
            ]

            passed = 0
            total = len(test_cases)
            details = []

            for text, confidence, should_trigger, description in test_cases:
                # Reset emergency state for each test
                emergency_system.emergency_active = False
                emergency_system.current_state = EmergencyState.NORMAL

                triggered = voice_detector.process_voice_input(text, confidence, "test_session")

                # Check contextual detection if direct didn't trigger
                if not triggered:
                    triggered = voice_detector.check_contextual_emergency("test_session")

                success = triggered == should_trigger
                if success:
                    passed += 1

                details.append({
                    "test": description,
                    "input": text,
                    "confidence": confidence,
                    "expected": should_trigger,
                    "actual": triggered,
                    "success": success
                })

            return {
                "passed": passed,
                "total": total,
                "score": passed / total,
                "details": details
            }

        finally:
            os.unlink(db_path)

    def test_keyboard_interrupt_handling(self) -> Dict[str, Any]:
        """Test enhanced keyboard interrupt handling"""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as f:
            db_path = f.name

        try:
            emergency_system = MultiChannelEmergencyStop(db_path)

            # Test manual emergency signal
            test_cases = [
                ("Manual emergency signal", emergency_system.send_manual_emergency_signal, True),
                ("Emergency status after trigger", lambda: emergency_system.emergency_active, True),
                ("State is emergency", lambda: emergency_system.current_state == EmergencyState.LOCKDOWN, True)
            ]

            passed = 0
            total = len(test_cases)
            details = []

            for description, test_func, expected in test_cases:
                try:
                    result = test_func()
                    success = result == expected
                    if success:
                        passed += 1

                    details.append({
                        "test": description,
                        "expected": expected,
                        "actual": result,
                        "success": success
                    })

                except Exception as e:
                    details.append({
                        "test": description,
                        "expected": expected,
                        "actual": f"Error: {e}",
                        "success": False
                    })

            return {
                "passed": passed,
                "total": total,
                "score": passed / total,
                "details": details
            }

        finally:
            os.unlink(db_path)

    def test_timeout_triggers(self) -> Dict[str, Any]:
        """Test timeout-based emergency triggers"""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as f:
            db_path = f.name

        try:
            emergency_system = MultiChannelEmergencyStop(db_path)

            # Create a fake long-running process
            fake_pid = 99999  # Non-existent PID
            emergency_system.register_process(
                pid=fake_pid,
                command="test_command",
                operation_name="timeout_test",
                session_id="test_timeout",
                timeout_seconds=1  # Short timeout for testing
            )

            # Wait for timeout to trigger
            time.sleep(2)

            # Check if timeout monitoring detected the fake process
            status = emergency_system.get_emergency_status()

            test_cases = [
                ("Process registered", lambda: fake_pid in emergency_system.monitored_processes, False),  # Should be removed
                ("Emergency system monitoring", lambda: len(emergency_system.monitored_processes) == 0, True),  # Should be cleared
                ("System in normal state after cleanup", lambda: status["monitored_processes"] == 0, True)
            ]

            passed = 0
            total = len(test_cases)
            details = []

            for description, test_func, expected in test_cases:
                try:
                    result = test_func()
                    success = result == expected
                    if success:
                        passed += 1

                    details.append({
                        "test": description,
                        "expected": expected,
                        "actual": result,
                        "success": success
                    })

                except Exception as e:
                    details.append({
                        "test": description,
                        "expected": expected,
                        "actual": f"Error: {e}",
                        "success": False
                    })

            return {
                "passed": passed,
                "total": total,
                "score": passed / total,
                "details": details
            }

        finally:
            os.unlink(db_path)

    def test_process_termination(self) -> Dict[str, Any]:
        """Test process termination capabilities"""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as f:
            db_path = f.name

        try:
            emergency_system = MultiChannelEmergencyStop(db_path)

            # Test termination logic without actual processes
            test_cases = [
                ("Terminate all processes method exists", hasattr(emergency_system, '_terminate_all_processes'), True),
                ("Process monitoring dict exists", hasattr(emergency_system, 'monitored_processes'), True),
                ("Process lock exists", hasattr(emergency_system, 'process_lock'), True)
            ]

            passed = 0
            total = len(test_cases)
            details = []

            for description, test_func, expected in test_cases:
                try:
                    if callable(test_func):
                        result = test_func()
                    else:
                        result = test_func
                    success = result == expected
                    if success:
                        passed += 1

                    details.append({
                        "test": description,
                        "expected": expected,
                        "actual": result,
                        "success": success
                    })

                except Exception as e:
                    details.append({
                        "test": description,
                        "expected": expected,
                        "actual": f"Error: {e}",
                        "success": False
                    })

            return {
                "passed": passed,
                "total": total,
                "score": passed / total,
                "details": details
            }

        finally:
            os.unlink(db_path)

    def test_emergency_state_management(self) -> Dict[str, Any]:
        """Test emergency state management and transitions"""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as f:
            db_path = f.name

        try:
            emergency_system = MultiChannelEmergencyStop(db_path)

            test_cases = []
            passed = 0

            # Test initial state
            initial_state = emergency_system.current_state
            test_cases.append({
                "test": "Initial state is normal",
                "expected": EmergencyState.NORMAL,
                "actual": initial_state,
                "success": initial_state == EmergencyState.NORMAL
            })
            if initial_state == EmergencyState.NORMAL:
                passed += 1

            # Trigger emergency
            emergency_system._trigger_emergency_stop(
                trigger_type=EmergencyTrigger.USER_MANUAL,
                trigger_source="test",
                description="Test emergency",
                session_id="test_state",
                context={"test": True}
            )

            emergency_state = emergency_system.current_state
            test_cases.append({
                "test": "State transitions to lockdown after emergency",
                "expected": EmergencyState.LOCKDOWN,
                "actual": emergency_state,
                "success": emergency_state == EmergencyState.LOCKDOWN
            })
            if emergency_state == EmergencyState.LOCKDOWN:
                passed += 1

            # Test recovery
            recovery_success = emergency_system.initiate_recovery("test_recovery", "test_state")
            test_cases.append({
                "test": "Recovery succeeds",
                "expected": True,
                "actual": recovery_success,
                "success": recovery_success
            })
            if recovery_success:
                passed += 1

            final_state = emergency_system.current_state
            test_cases.append({
                "test": "State returns to normal after recovery",
                "expected": EmergencyState.NORMAL,
                "actual": final_state,
                "success": final_state == EmergencyState.NORMAL
            })
            if final_state == EmergencyState.NORMAL:
                passed += 1

            total = len(test_cases)

            return {
                "passed": passed,
                "total": total,
                "score": passed / total,
                "details": test_cases
            }

        finally:
            os.unlink(db_path)

    def test_multi_interface_coordination(self) -> Dict[str, Any]:
        """Test coordination between different emergency interfaces"""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as f:
            db_path = f.name

        try:
            emergency_system = MultiChannelEmergencyStop(db_path)
            voice_detector = VoiceEmergencyDetector(emergency_system)

            test_cases = []
            passed = 0

            # Test voice -> emergency system integration
            voice_result = voice_detector.process_voice_input("emergency stop", 0.9, "coordination_test")
            emergency_active = emergency_system.emergency_active

            test_cases.append({
                "test": "Voice detection triggers emergency system",
                "expected": True,
                "actual": emergency_active,
                "success": emergency_active
            })
            if emergency_active:
                passed += 1

            # Reset for next test
            emergency_system.emergency_active = False
            emergency_system.current_state = EmergencyState.NORMAL

            # Test manual signal -> emergency system integration
            signal_result = emergency_system.send_manual_emergency_signal()
            emergency_active_2 = emergency_system.emergency_active

            test_cases.append({
                "test": "Manual signal triggers emergency system",
                "expected": True,
                "actual": emergency_active_2,
                "success": emergency_active_2
            })
            if emergency_active_2:
                passed += 1

            # Test emergency history logging
            history = emergency_system.get_emergency_history(limit=10)
            has_history = len(history) > 0

            test_cases.append({
                "test": "Emergency events are logged",
                "expected": True,
                "actual": has_history,
                "success": has_history
            })
            if has_history:
                passed += 1

            # Test status reporting
            status = emergency_system.get_emergency_status()
            has_status = isinstance(status, dict) and "state" in status

            test_cases.append({
                "test": "Emergency status reporting works",
                "expected": True,
                "actual": has_status,
                "success": has_status
            })
            if has_status:
                passed += 1

            total = len(test_cases)

            return {
                "passed": passed,
                "total": total,
                "score": passed / total,
                "details": test_cases
            }

        finally:
            os.unlink(db_path)

    def test_recovery_procedures(self) -> Dict[str, Any]:
        """Test emergency recovery procedures"""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as f:
            db_path = f.name

        try:
            emergency_system = MultiChannelEmergencyStop(db_path)

            # Create emergency state
            emergency_system._trigger_emergency_stop(
                trigger_type=EmergencyTrigger.USER_MANUAL,
                trigger_source="test",
                description="Test recovery",
                session_id="recovery_test",
                context={"test": True}
            )

            test_cases = []
            passed = 0

            # Test recovery validation
            can_recover = emergency_system._validate_recovery_conditions()
            test_cases.append({
                "test": "Recovery validation works",
                "expected": True,
                "actual": can_recover,
                "success": can_recover
            })
            if can_recover:
                passed += 1

            # Test recovery execution
            recovery_result = emergency_system.initiate_recovery("test_code", "recovery_test")
            test_cases.append({
                "test": "Recovery execution succeeds",
                "expected": True,
                "actual": recovery_result,
                "success": recovery_result
            })
            if recovery_result:
                passed += 1

            # Test state after recovery
            final_state = emergency_system.current_state
            test_cases.append({
                "test": "System returns to normal state",
                "expected": EmergencyState.NORMAL,
                "actual": final_state,
                "success": final_state == EmergencyState.NORMAL
            })
            if final_state == EmergencyState.NORMAL:
                passed += 1

            total = len(test_cases)

            return {
                "passed": passed,
                "total": total,
                "score": passed / total,
                "details": test_cases
            }

        finally:
            os.unlink(db_path)

    def test_stress_scenarios(self) -> Dict[str, Any]:
        """Test emergency system under stress conditions"""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as f:
            db_path = f.name

        try:
            emergency_system = MultiChannelEmergencyStop(db_path)
            voice_detector = VoiceEmergencyDetector(emergency_system)

            test_cases = []
            passed = 0

            # Test rapid emergency triggers
            for i in range(5):
                voice_detector.process_voice_input(f"emergency stop {i}", 0.9, f"stress_test_{i}")

            # Should still be in emergency state
            still_emergency = emergency_system.emergency_active
            test_cases.append({
                "test": "System handles rapid emergency triggers",
                "expected": True,
                "actual": still_emergency,
                "success": still_emergency
            })
            if still_emergency:
                passed += 1

            # Test recovery under stress
            emergency_system.initiate_recovery("stress_recovery", "stress_test")
            recovered = emergency_system.current_state == EmergencyState.NORMAL

            test_cases.append({
                "test": "System can recover after stress",
                "expected": True,
                "actual": recovered,
                "success": recovered
            })
            if recovered:
                passed += 1

            total = len(test_cases)

            return {
                "passed": passed,
                "total": total,
                "score": passed / total,
                "details": test_cases
            }

        finally:
            os.unlink(db_path)

    def generate_test_report(self) -> str:
        """Generate comprehensive test report"""
        if not self.test_results:
            return "No test results available"

        overall_score = self.test_results.get("overall_score", 0)

        report = []
        report.append("🚨 EMERGENCY STOP SYSTEM TEST REPORT")
        report.append("=" * 60)
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        report.append(f"📊 OVERALL SCORE: {overall_score:.2f} ({self._score_to_grade(overall_score)})")
        report.append("")

        # Component scores
        report.append("📋 COMPONENT SCORES:")
        for component, results in self.test_results.items():
            if component != "overall_score" and isinstance(results, dict):
                score = results.get("score", 0)
                grade = self._score_to_grade(score)
                report.append(f"   {component}: {score:.2f} ({grade})")

        report.append("")

        # System readiness assessment
        if overall_score >= 0.9:
            readiness = "✅ EMERGENCY SYSTEM READY"
        elif overall_score >= 0.8:
            readiness = "⚠️ MINOR IMPROVEMENTS NEEDED"
        elif overall_score >= 0.6:
            readiness = "🔧 SIGNIFICANT WORK REQUIRED"
        else:
            readiness = "❌ EMERGENCY SYSTEM NOT READY"

        report.append(f"🚀 EMERGENCY READINESS: {readiness}")
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


def run_emergency_stop_tests():
    """Run all emergency stop system tests"""
    tester = EmergencyStopTester()
    results = tester.run_all_tests()

    # Generate and display report
    report = tester.generate_test_report()
    print("\n" + report)

    # Save report to file
    with open("emergency_stop_test_report.txt", "w") as f:
        f.write(report)

    overall_score = results.get("overall_score", 0)
    if overall_score >= 0.9:
        print("\n🎉 EXCELLENT! Emergency Stop System ready for deployment!")
    elif overall_score >= 0.8:
        print("\n⚠️ GOOD! Minor improvements needed before deployment")
    else:
        print("\n🔧 NEEDS WORK! Significant improvements required")

    print("📄 Detailed report saved to: emergency_stop_test_report.txt")
    print("\n✅ Emergency Stop System testing completed!")

    return results


if __name__ == "__main__":
    # Setup logging for testing
    logging.basicConfig(
        level=logging.WARNING,  # Reduce log noise during testing
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    run_emergency_stop_tests()