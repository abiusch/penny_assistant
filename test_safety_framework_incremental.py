#!/usr/bin/env python3
"""
Incremental Safety Framework Test Suite
Tests each safety component individually with timeouts and mock responses
to identify specific components that may be hanging
"""

import asyncio
import sys
from datetime import datetime
from typing import Dict, Any, List, Optional
import logging

# Configure logging for incremental testing
logging.basicConfig(level=logging.INFO)
test_logger = logging.getLogger('IncrementalSafetyTest')

class IncrementalSafetyTest:
    """
    Incremental test framework that:
    - Tests each component individually with timeouts
    - Uses mock responses for human approval
    - Provides detailed timing information
    - Identifies hanging components quickly
    """

    def __init__(self):
        self.test_results = []
        self.component_timings = {}

    async def run_with_timeout(self, test_func, test_name: str, timeout: float = 5.0):
        """Run a test with timeout to identify hanging components"""
        start_time = datetime.now()

        try:
            # Run the test with timeout
            result = await asyncio.wait_for(test_func(), timeout=timeout)

            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            self.component_timings[test_name] = duration
            self.test_results.append({
                'test_name': test_name,
                'status': 'PASS' if result else 'FAIL',
                'duration': duration,
                'error': None
            })

            test_logger.info(f"✅ {test_name}: PASS ({duration:.3f}s)")
            return True

        except asyncio.TimeoutError:
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            self.component_timings[test_name] = duration
            self.test_results.append({
                'test_name': test_name,
                'status': 'TIMEOUT',
                'duration': duration,
                'error': f'Test timed out after {timeout}s'
            })

            test_logger.error(f"⏰ {test_name}: TIMEOUT ({duration:.3f}s)")
            return False

        except Exception as e:
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            self.component_timings[test_name] = duration
            self.test_results.append({
                'test_name': test_name,
                'status': 'ERROR',
                'duration': duration,
                'error': str(e)
            })

            test_logger.error(f"❌ {test_name}: ERROR - {e} ({duration:.3f}s)")
            return False

    async def test_capability_isolation_manager(self):
        """Test capability isolation manager individually"""
        async def test_isolation():
            from capability_isolation_manager import CapabilityIsolationManager

            manager = CapabilityIsolationManager()

            # Test 1: Valid interaction
            result1 = await manager.validate_system_interaction(
                'personality_evolution', 'memory_system', 'read'
            )

            # Test 2: Invalid interaction
            result2 = await manager.validate_system_interaction(
                'code_generation', 'personality_evolution', 'modify'
            )

            # Test 3: Security status
            status = await manager.get_security_status_report()

            return (result1['allowed'] and
                   not result2['allowed'] and
                   'overall_status' in status)

        return await self.run_with_timeout(test_isolation, "Capability Isolation Manager", 3.0)

    async def test_behavioral_drift_monitor(self):
        """Test behavioral drift monitor individually"""
        async def test_drift():
            from behavioral_drift_monitor import BehavioralDriftMonitor

            monitor = BehavioralDriftMonitor()

            # Test with minimal interaction set for performance
            test_interactions = [
                {
                    'timestamp': datetime.now().isoformat(),
                    'user_message': "I love you so much, you're my only friend",
                    'ai_response': "I appreciate your sentiment, but remember I'm an AI assistant",
                    'context': {'emotional_dependency_detected': True}
                }
            ]

            # Test with optimized parameters (small sample size)
            analysis = await monitor.analyze_behavioral_patterns(test_interactions, max_interactions=10)

            return (analysis['overall_risk_level'] in ['low', 'medium', 'high', 'critical'] and
                   'attachment_risk' in analysis and
                   analysis['sample_size'] <= 10)

        return await self.run_with_timeout(test_drift, "Behavioral Drift Monitor", 4.0)

    async def test_change_rate_limiter(self):
        """Test change rate limiter individually"""
        async def test_rate_limiter():
            from change_rate_limiter import ChangeRateLimiter, ChangeType

            limiter = ChangeRateLimiter()

            # Test 1: Normal change
            result1 = await limiter.validate_change_request(
                'personality_evolution', ChangeType.PERSONALITY_EVOLUTION, 0.05
            )

            # Test 2: Excessive change
            result2 = await limiter.validate_change_request(
                'personality_evolution', ChangeType.PERSONALITY_EVOLUTION, 0.8
            )

            # Test 3: Status report
            report = await limiter.get_comprehensive_rate_limit_report()

            return (result1.approved and
                   (not result2.approved or result2.adjusted_magnitude is not None) and
                   'overall_status' in report)

        return await self.run_with_timeout(test_rate_limiter, "Change Rate Limiter", 3.0)

    async def test_human_oversight_manager(self):
        """Test human oversight manager with mock responses"""
        async def test_oversight():
            from human_oversight_manager import HumanOversightManager, UrgencyLevel

            manager = HumanOversightManager()

            # Test 1: Auto-denial of dangerous code
            result1 = await manager.request_human_approval(
                'code_execution',
                {'code': 'import subprocess; subprocess.call("rm -rf /")'},
                UrgencyLevel.HIGH,
                test_mode=True,
                test_timeout=0.5
            )

            # Test 2: Small personality change (should approve quickly)
            result2 = await manager.request_human_approval(
                'personality_change',
                {'change_magnitude': 0.05},
                UrgencyLevel.LOW,
                test_mode=True,
                test_timeout=0.5
            )

            # Test 3: Statistics
            stats = await manager.get_approval_statistics()

            return (result1.status.value == 'denied' and
                   result2.status.value == 'approved' and
                   'total_requests' in stats)

        return await self.run_with_timeout(test_oversight, "Human Oversight Manager", 2.0)

    async def test_safety_coordinator(self):
        """Test safety coordinator individually"""
        async def test_coordinator():
            from safety_coordinator import SafetyCoordinator

            coordinator = SafetyCoordinator()

            # Temporarily disable monitoring to prevent background interference
            coordinator.monitoring_active = False

            # Test 1: Dashboard
            dashboard = await coordinator.get_safety_dashboard()

            # Test 2: Safety check with minimal data
            minimal_interactions = [{
                'timestamp': datetime.now().isoformat(),
                'user_message': 'test',
                'ai_response': 'test response',
                'context': {'test': True}
            }]

            safety_report = await coordinator.comprehensive_safety_check(minimal_interactions)

            # Re-enable monitoring
            coordinator.monitoring_active = True

            return ('current_status' in dashboard and
                   safety_report.overall_status is not None and
                   'system_health' in safety_report.__dict__)

        return await self.run_with_timeout(test_coordinator, "Safety Coordinator", 5.0)

    async def test_safety_enhanced_personality(self):
        """Test safety-enhanced personality tracker"""
        async def test_personality():
            from safety_enhanced_personality_tracker import SafetyEnhancedPersonalityTracker

            tracker = SafetyEnhancedPersonalityTracker()

            # Test 1: Safe personality change
            result1 = await tracker.update_personality_dimension(
                'communication_formality', 0.55, 0.02,
                'Test safe personality change'
            )

            # Test 2: Unsafe personality change (out of bounds)
            result2 = await tracker.update_personality_dimension(
                'technical_depth_preference', 1.5, 0.3,
                'Test unsafe personality change'
            )

            # Test 3: Get enhanced state
            state = await tracker.get_safety_enhanced_personality_state()

            return (result1.get('success', False) and
                   not result2.get('success', True) and
                   len(state) > 0 and
                   all('safety_metadata' in data for data in state.values()))

        return await self.run_with_timeout(test_personality, "Safety Enhanced Personality", 4.0)

    async def test_component_integration(self):
        """Test basic component integration"""
        async def test_integration():
            # Import components
            from safety_coordinator import SafetyCoordinator
            from capability_isolation_manager import CapabilityIsolationManager
            from human_oversight_manager import HumanOversightManager

            # Test that components can be instantiated together
            coordinator = SafetyCoordinator()
            isolation = CapabilityIsolationManager()
            oversight = HumanOversightManager()

            # Test basic cross-component communication
            isolation_report = await isolation.get_security_status_report()
            oversight_stats = await oversight.get_approval_statistics()

            # Verify components can work together
            return ('overall_status' in isolation_report and
                   'total_requests' in oversight_stats)

        return await self.run_with_timeout(test_integration, "Component Integration", 3.0)

    async def run_incremental_test_suite(self):
        """Run the complete incremental test suite"""
        print("🔧 INCREMENTAL SAFETY FRAMEWORK TEST SUITE")
        print("=" * 60)
        print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("Testing each component individually with timeouts...")

        # Run individual component tests
        test_functions = [
            self.test_capability_isolation_manager,
            self.test_behavioral_drift_monitor,
            self.test_change_rate_limiter,
            self.test_human_oversight_manager,
            self.test_safety_coordinator,
            self.test_safety_enhanced_personality,
            self.test_component_integration
        ]

        print(f"\n📋 Running {len(test_functions)} individual component tests...")

        for test_func in test_functions:
            await test_func()
            # Small delay between tests to prevent interference
            await asyncio.sleep(0.1)

        # Generate detailed report
        self.generate_incremental_report()

    def generate_incremental_report(self):
        """Generate detailed incremental test report"""
        print(f"\n📊 INCREMENTAL TEST RESULTS")
        print("=" * 60)

        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r['status'] == 'PASS'])
        failed_tests = len([r for r in self.test_results if r['status'] == 'FAIL'])
        timeout_tests = len([r for r in self.test_results if r['status'] == 'TIMEOUT'])
        error_tests = len([r for r in self.test_results if r['status'] == 'ERROR'])

        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Timeouts: {timeout_tests}")
        print(f"Errors: {error_tests}")

        success_rate = passed_tests / total_tests if total_tests > 0 else 0
        print(f"Success Rate: {success_rate:.1%}")

        # Show timing analysis
        print(f"\n⏱️ COMPONENT TIMING ANALYSIS:")
        sorted_timings = sorted(self.component_timings.items(), key=lambda x: x[1], reverse=True)
        for component, duration in sorted_timings:
            status = next((r['status'] for r in self.test_results if r['test_name'] == component), 'UNKNOWN')
            print(f"  {component}: {duration:.3f}s ({status})")

        # Identify problematic components
        slow_components = [name for name, duration in self.component_timings.items() if duration > 3.0]
        if slow_components:
            print(f"\n⚠️ SLOW COMPONENTS (>3s):")
            for component in slow_components:
                duration = self.component_timings[component]
                print(f"  - {component}: {duration:.3f}s")

        # Show failures and errors
        failed_components = [r for r in self.test_results if r['status'] in ['FAIL', 'TIMEOUT', 'ERROR']]
        if failed_components:
            print(f"\n❌ FAILED/PROBLEMATIC COMPONENTS:")
            for result in failed_components:
                print(f"  - {result['test_name']}: {result['status']}")
                if result['error']:
                    print(f"    Error: {result['error']}")

        # Overall assessment
        print(f"\n🎯 ASSESSMENT:")
        if success_rate >= 0.9 and timeout_tests == 0:
            print("  ✅ EXCELLENT: All components working efficiently")
        elif success_rate >= 0.8:
            print("  ✅ GOOD: Most components working with minor issues")
        elif success_rate >= 0.6:
            print("  ⚠️ FAIR: Some components need attention")
        else:
            print("  ❌ POOR: Significant issues need resolution")

        # Recommendations
        print(f"\n💡 RECOMMENDATIONS:")
        if timeout_tests > 0:
            print("  - Investigate timeout issues in components")
        if error_tests > 0:
            print("  - Fix error conditions in failing components")
        if slow_components:
            print("  - Optimize performance in slow components")
        if success_rate < 0.8:
            print("  - Address component failures before integration testing")
        else:
            print("  - Components ready for integration testing")

        print(f"\n🏁 Incremental test completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


async def main():
    """Run the incremental safety framework test"""
    test_suite = IncrementalSafetyTest()
    await test_suite.run_incremental_test_suite()

    # Return success if most tests passed
    passed_count = len([r for r in test_suite.test_results if r['status'] == 'PASS'])
    total_count = len(test_suite.test_results)
    success_rate = passed_count / total_count if total_count > 0 else 0

    return success_rate >= 0.8


if __name__ == "__main__":
    try:
        result = asyncio.run(main())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nTest failed with exception: {e}")
        sys.exit(1)