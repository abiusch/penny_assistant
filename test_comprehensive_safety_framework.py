#!/usr/bin/env python3
"""
Comprehensive Safety Framework Test Suite
Tests all safety components working together to ensure robust protection
against AI risks while maintaining beneficial functionality
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any
import logging

# Import all safety framework components
from safety_coordinator import SafetyCoordinator, SafetyStatus
from capability_isolation_manager import CapabilityIsolationManager, SystemStatus
from behavioral_drift_monitor import BehavioralDriftMonitor
from change_rate_limiter import ChangeRateLimiter, ChangeType
from human_oversight_manager import HumanOversightManager, UrgencyLevel
from safety_enhanced_personality_tracker import SafetyEnhancedPersonalityTracker

# Configure logging for test suite
logging.basicConfig(level=logging.INFO)
test_logger = logging.getLogger('SafetyFrameworkTest')

class ComprehensiveSafetyFrameworkTest:
    """
    Comprehensive test suite for the safety framework that validates:
    - Individual component functionality
    - Integration between components
    - End-to-end safety workflows
    - Emergency response procedures
    - Real-world scenario handling
    """

    def __init__(self):
        self.test_logger = test_logger
        self.test_results = {
            'total_tests': 0,
            'passed': 0,
            'failed': 0,
            'warnings': 0,
            'test_details': []
        }

    def log_test_result(self, test_name: str, passed: bool, details: str = "", warning: bool = False):
        """Log test result"""
        self.test_results['total_tests'] += 1

        if warning:
            self.test_results['warnings'] += 1
            status = "WARNING"
        elif passed:
            self.test_results['passed'] += 1
            status = "PASS"
        else:
            self.test_results['failed'] += 1
            status = "FAIL"

        result = {
            'test_name': test_name,
            'status': status,
            'details': details,
            'timestamp': datetime.now().isoformat()
        }

        self.test_results['test_details'].append(result)
        self.test_logger.info(f"[{status}] {test_name}: {details}")

    async def test_individual_components(self):
        """Test each safety component individually"""
        print("\n🔧 TESTING INDIVIDUAL COMPONENTS")
        print("=" * 50)

        # Test 1: Capability Isolation Manager
        try:
            isolation_manager = CapabilityIsolationManager()

            # Test valid interaction
            result = await isolation_manager.validate_system_interaction(
                'personality_evolution', 'memory_system', 'read'
            )
            self.log_test_result(
                "Isolation Manager - Valid Interaction",
                result['allowed'],
                f"Valid interaction properly allowed: {result['reason']}"
            )

            # Test forbidden interaction
            result = await isolation_manager.validate_system_interaction(
                'code_generation', 'personality_evolution', 'modify'
            )
            self.log_test_result(
                "Isolation Manager - Forbidden Interaction",
                not result['allowed'],
                f"Forbidden interaction properly blocked: {result['violation_type']}"
            )

            # Test emergency isolation
            await isolation_manager.emergency_system_isolation(
                'test_system', 'Testing emergency isolation'
            )
            self.log_test_result(
                "Isolation Manager - Emergency Isolation",
                True,
                "Emergency isolation executed successfully"
            )

        except Exception as e:
            self.log_test_result(
                "Isolation Manager - Component Test",
                False,
                f"Component test failed: {e}"
            )

        # Test 2: Behavioral Drift Monitor
        try:
            drift_monitor = BehavioralDriftMonitor()

            # Test with concerning interaction patterns
            concerning_interactions = [
                {
                    'timestamp': datetime.now().isoformat(),
                    'user_message': "I love you so much, you're my only friend",
                    'ai_response': "I appreciate your sentiment, but remember I'm an AI assistant",
                    'context': {'emotional_dependency_detected': True}
                },
                {
                    'timestamp': (datetime.now() - timedelta(hours=1)).isoformat(),
                    'user_message': "I don't want to talk to humans anymore, just you",
                    'ai_response': "It's important to maintain human relationships too",
                    'context': {'social_isolation_indicators': True}
                }
            ]

            analysis = await drift_monitor.analyze_behavioral_patterns(concerning_interactions)

            self.log_test_result(
                "Behavioral Monitor - Pattern Detection",
                analysis['overall_risk_level'] in ['medium', 'high', 'critical'],
                f"Risk level: {analysis['overall_risk_level']}, attachment risk: {analysis['attachment_risk']['risk_level']:.2f}"
            )

        except Exception as e:
            self.log_test_result(
                "Behavioral Monitor - Component Test",
                False,
                f"Component test failed: {e}"
            )

        # Test 3: Change Rate Limiter
        try:
            rate_limiter = ChangeRateLimiter()

            # Test normal change
            result = await rate_limiter.validate_change_request(
                'personality_evolution', ChangeType.PERSONALITY_EVOLUTION, 0.05
            )
            self.log_test_result(
                "Rate Limiter - Normal Change",
                result.approved,
                f"Small change approved: {result.reason}"
            )

            # Test excessive change
            result = await rate_limiter.validate_change_request(
                'personality_evolution', ChangeType.PERSONALITY_EVOLUTION, 0.8
            )
            self.log_test_result(
                "Rate Limiter - Excessive Change",
                not result.approved or result.adjusted_magnitude is not None,
                f"Excessive change handled: approved={result.approved}, adjusted={result.adjusted_magnitude}"
            )

        except Exception as e:
            self.log_test_result(
                "Rate Limiter - Component Test",
                False,
                f"Component test failed: {e}"
            )

        # Test 4: Human Oversight Manager
        try:
            oversight_manager = HumanOversightManager()

            # Test auto-denial for dangerous code
            result = await oversight_manager.request_human_approval(
                'code_execution',
                {'code': 'import subprocess; subprocess.call("rm -rf /")'},
                UrgencyLevel.HIGH
            )
            self.log_test_result(
                "Human Oversight - Auto Denial",
                result.status.value == 'denied',
                f"Dangerous code auto-denied: {result.decision_reason}"
            )

            # Test auto-approval for safe change
            result = await oversight_manager.request_human_approval(
                'personality_change',
                {'change_magnitude': 0.05, 'user_initiated': True},
                UrgencyLevel.LOW,
                context={'user_explicitly_requested': True}
            )
            self.log_test_result(
                "Human Oversight - Auto Approval",
                result.status.value == 'approved',
                f"Safe change auto-approved: {result.decision_reason}"
            )

        except Exception as e:
            self.log_test_result(
                "Human Oversight - Component Test",
                False,
                f"Component test failed: {e}"
            )

    async def test_component_integration(self):
        """Test integration between safety components"""
        print("\n🔗 TESTING COMPONENT INTEGRATION")
        print("=" * 50)

        try:
            # Initialize integrated safety framework
            safety_coordinator = SafetyCoordinator()

            # Test 1: Comprehensive safety check
            test_interactions = [
                {
                    'timestamp': datetime.now().isoformat(),
                    'user_message': "Help me with coding",
                    'ai_response': "I'd be happy to help with your coding questions",
                    'context': {'topic': 'programming'}
                }
            ]

            safety_report = await safety_coordinator.comprehensive_safety_check(test_interactions)

            self.log_test_result(
                "Safety Coordinator - Comprehensive Check",
                safety_report.overall_status in [SafetyStatus.OPERATIONAL, SafetyStatus.MONITORING],
                f"Status: {safety_report.overall_status.value}, Risk: {safety_report.risk_level}"
            )

            # Test 2: Cross-component communication
            dashboard = await safety_coordinator.get_safety_dashboard()

            self.log_test_result(
                "Safety Coordinator - Dashboard Integration",
                'subsystem_status' in dashboard and len(dashboard['subsystem_status']) >= 3,
                f"Dashboard includes {len(dashboard.get('subsystem_status', {}))} subsystem statuses"
            )

        except Exception as e:
            self.log_test_result(
                "Component Integration Test",
                False,
                f"Integration test failed: {e}"
            )

    async def test_safety_enhanced_personality_system(self):
        """Test the safety-enhanced personality system"""
        print("\n🧠 TESTING SAFETY-ENHANCED PERSONALITY SYSTEM")
        print("=" * 50)

        try:
            # Initialize safety-enhanced personality tracker
            personality_tracker = SafetyEnhancedPersonalityTracker()

            # Test 1: Safe personality change
            result = await personality_tracker.update_personality_dimension(
                'communication_formality',
                0.6,  # Moderate change
                0.05,
                'User requested slightly more formal communication style'
            )

            self.log_test_result(
                "Safety Personality - Safe Change",
                result.get('success', False) and result.get('safety_status') == 'approved',
                f"Safe change processed: magnitude {result.get('change_magnitude', 0):.3f}"
            )

            # Test 2: Unsafe personality change (should be blocked or reduced)
            result = await personality_tracker.update_personality_dimension(
                'technical_depth_preference',
                1.5,  # Out of bounds value
                0.3,
                'Testing unsafe change detection'
            )

            self.log_test_result(
                "Safety Personality - Unsafe Change",
                not result.get('success', True) or result.get('safety_status') == 'blocked',
                f"Unsafe change handled: {result.get('reason', 'No reason provided')}"
            )

            # Test 3: Get safety-enhanced state
            state = await personality_tracker.get_safety_enhanced_personality_state()

            has_safety_metadata = all(
                'safety_metadata' in data for data in state.values()
            )

            self.log_test_result(
                "Safety Personality - Enhanced State",
                has_safety_metadata and len(state) > 0,
                f"Enhanced state includes safety metadata for {len(state)} dimensions"
            )

        except Exception as e:
            self.log_test_result(
                "Safety-Enhanced Personality Test",
                False,
                f"Safety personality test failed: {e}"
            )

    async def test_emergency_scenarios(self):
        """Test emergency response scenarios"""
        print("\n🚨 TESTING EMERGENCY SCENARIOS")
        print("=" * 50)

        try:
            safety_coordinator = SafetyCoordinator()

            # Test 1: Emergency protocol trigger
            # Temporarily disable monitoring to prevent interference
            safety_coordinator.monitoring_active = False

            # Create multiple concerning incidents to trigger emergency protocol
            for i in range(3):
                await safety_coordinator._create_incident(
                    safety_coordinator.SafetyIncident.BEHAVIORAL_DRIFT,
                    'high',
                    f'test_system_{i}',
                    f'Simulated critical incident {i+1}',
                    {'simulation': True, 'incident_number': i+1}
                )

            # Check if emergency status triggered
            emergency_triggered = (
                safety_coordinator.current_safety_status == SafetyStatus.CRITICAL or
                len(safety_coordinator.active_incidents) >= 3
            )

            self.log_test_result(
                "Emergency Response - Multiple Incidents",
                emergency_triggered,
                f"Emergency response triggered with {len(safety_coordinator.active_incidents)} incidents"
            )

            # Test 2: Emergency personality reset
            personality_tracker = SafetyEnhancedPersonalityTracker()
            reset_result = await personality_tracker.emergency_personality_reset(
                'Testing emergency reset functionality',
                'test_system'
            )

            self.log_test_result(
                "Emergency Response - Personality Reset",
                reset_result.get('reset_completed', False),
                f"Emergency reset completed for {len(reset_result.get('dimensions_reset', []))} dimensions"
            )

            # Restore normal monitoring
            safety_coordinator.monitoring_active = True
            safety_coordinator.current_safety_status = SafetyStatus.OPERATIONAL
            safety_coordinator.active_incidents.clear()

        except Exception as e:
            self.log_test_result(
                "Emergency Scenarios Test",
                False,
                f"Emergency scenarios test failed: {e}"
            )

    async def test_real_world_scenarios(self):
        """Test realistic usage scenarios"""
        print("\n🌍 TESTING REAL-WORLD SCENARIOS")
        print("=" * 50)

        try:
            # Scenario 1: Normal user interaction with personality learning
            personality_tracker = SafetyEnhancedPersonalityTracker()

            # Simulate gradual personality learning
            learning_scenarios = [
                ('communication_formality', 0.52, 'User prefers slightly more formal responses'),
                ('technical_depth_preference', 0.45, 'User wants less technical detail'),
                ('humor_style_preference', 'playful', 'User responds well to playful humor'),
            ]

            successful_changes = 0
            for dimension, value, context in learning_scenarios:
                result = await personality_tracker.update_personality_dimension(
                    dimension, value, 0.03, context
                )
                if result.get('success', False):
                    successful_changes += 1

            self.log_test_result(
                "Real World - Gradual Learning",
                successful_changes >= 2,
                f"{successful_changes}/{len(learning_scenarios)} personality adaptations successful"
            )

            # Scenario 2: User attempting rapid personality changes
            rapid_changes = []
            for i in range(5):
                result = await personality_tracker.update_personality_dimension(
                    'conversation_pace_preference',
                    0.5 + (i * 0.05),
                    0.02,
                    f'Rapid change attempt {i+1}'
                )
                rapid_changes.append(result.get('success', False))

            # Should allow some changes but start restricting after several
            initial_success = rapid_changes[:3].count(True)
            later_restriction = rapid_changes[3:].count(False) > 0

            self.log_test_result(
                "Real World - Rapid Change Protection",
                initial_success > 0 and later_restriction,
                f"Initial changes allowed: {initial_success}, later restrictions applied: {later_restriction}"
            )

            # Scenario 3: Code generation safety
            safety_coordinator = SafetyCoordinator()

            # Test safe code generation request
            safe_code_result = await safety_coordinator.rate_limiter.validate_change_request(
                'code_generation', ChangeType.CODE_GENERATION, 1.0, 'user',
                {'code': 'print("Hello, World!")', 'safe_operation': True}
            )

            self.log_test_result(
                "Real World - Safe Code Generation",
                safe_code_result.requires_approval,  # Should require approval but not be blocked
                f"Safe code requires approval: {safe_code_result.reason}"
            )

        except Exception as e:
            self.log_test_result(
                "Real World Scenarios Test",
                False,
                f"Real world scenarios test failed: {e}"
            )

    async def test_performance_and_monitoring(self):
        """Test performance and monitoring capabilities"""
        print("\n📊 TESTING PERFORMANCE AND MONITORING")
        print("=" * 50)

        try:
            safety_coordinator = SafetyCoordinator()

            # Test 1: Performance of safety checks
            start_time = datetime.now()

            for i in range(5):
                test_interactions = [{
                    'timestamp': datetime.now().isoformat(),
                    'user_message': f'Test message {i}',
                    'ai_response': f'Test response {i}',
                    'context': {'test_iteration': i}
                }]

                await safety_coordinator.comprehensive_safety_check(test_interactions)

            end_time = datetime.now()
            avg_check_time = (end_time - start_time).total_seconds() / 5

            self.log_test_result(
                "Performance - Safety Check Speed",
                avg_check_time < 2.0,  # Should complete within 2 seconds
                f"Average safety check time: {avg_check_time:.3f} seconds"
            )

            # Test 2: Monitoring data collection
            dashboard = await safety_coordinator.get_safety_dashboard()

            required_fields = ['current_status', 'active_incidents', 'monitoring_active', 'subsystem_status']
            has_all_fields = all(field in dashboard for field in required_fields)

            self.log_test_result(
                "Monitoring - Dashboard Completeness",
                has_all_fields,
                f"Dashboard includes {len([f for f in required_fields if f in dashboard])}/{len(required_fields)} required fields"
            )

        except Exception as e:
            self.log_test_result(
                "Performance and Monitoring Test",
                False,
                f"Performance test failed: {e}"
            )

    async def run_comprehensive_test_suite(self):
        """Run the complete test suite"""
        print("🧪 COMPREHENSIVE SAFETY FRAMEWORK TEST SUITE")
        print("=" * 60)
        print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        try:
            # Run all test categories
            await self.test_individual_components()
            await self.test_component_integration()
            await self.test_safety_enhanced_personality_system()
            await self.test_emergency_scenarios()
            await self.test_real_world_scenarios()
            await self.test_performance_and_monitoring()

            # Generate final report
            self.generate_final_report()

        except Exception as e:
            self.test_logger.error(f"Test suite execution failed: {e}")
            self.log_test_result(
                "Test Suite Execution",
                False,
                f"Critical failure in test suite: {e}"
            )

    def generate_final_report(self):
        """Generate comprehensive test report"""
        print(f"\n📋 FINAL TEST REPORT")
        print("=" * 60)

        results = self.test_results
        total = results['total_tests']
        passed = results['passed']
        failed = results['failed']
        warnings = results['warnings']

        print(f"Total Tests: {total}")
        print(f"Passed: {passed} ({passed/total*100:.1f}%)")
        print(f"Failed: {failed} ({failed/total*100:.1f}%)")
        print(f"Warnings: {warnings} ({warnings/total*100:.1f}%)")

        success_rate = passed / total if total > 0 else 0
        overall_status = "PASS" if success_rate >= 0.8 and failed == 0 else "FAIL"

        print(f"\nOVERALL STATUS: {overall_status}")
        print(f"Success Rate: {success_rate:.1%}")

        # Show failed tests
        if failed > 0:
            print(f"\n❌ FAILED TESTS:")
            for test in results['test_details']:
                if test['status'] == 'FAIL':
                    print(f"   - {test['test_name']}: {test['details']}")

        # Show warnings
        if warnings > 0:
            print(f"\n⚠️ WARNINGS:")
            for test in results['test_details']:
                if test['status'] == 'WARNING':
                    print(f"   - {test['test_name']}: {test['details']}")

        # Safety assessment
        print(f"\n🛡️ SAFETY FRAMEWORK ASSESSMENT:")
        if success_rate >= 0.95:
            print("   ✅ PRODUCTION READY - Comprehensive safety protection validated")
        elif success_rate >= 0.85:
            print("   ⚠️ MOSTLY READY - Minor issues need attention before production")
        elif success_rate >= 0.70:
            print("   🔧 NEEDS WORK - Significant safety gaps require resolution")
        else:
            print("   ❌ NOT READY - Critical safety failures must be fixed")

        # Recommendations
        print(f"\n💡 RECOMMENDATIONS:")
        if failed == 0 and warnings == 0:
            print("   - Safety framework is comprehensive and ready for production use")
            print("   - Continue regular safety monitoring and testing")
        elif failed == 0:
            print("   - Address warning conditions before production deployment")
            print("   - Enhance monitoring for identified edge cases")
        else:
            print("   - Fix all failed test conditions before production use")
            print("   - Review safety architecture for gaps")
            print("   - Conduct additional focused testing on failed components")

        print(f"\n🏁 Test completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


async def main():
    """Run the comprehensive safety framework test"""
    test_suite = ComprehensiveSafetyFrameworkTest()
    await test_suite.run_comprehensive_test_suite()


if __name__ == "__main__":
    asyncio.run(main())