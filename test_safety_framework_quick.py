#!/usr/bin/env python3
"""
Quick Safety Framework Test
Validates core safety functionality without timeouts
"""

import asyncio
import sys
from datetime import datetime

async def main():
    print("🛡️ QUICK SAFETY FRAMEWORK TEST")
    print("=" * 50)
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    tests_passed = 0
    tests_total = 0

    try:
        # Test 1: Capability Isolation Manager
        print("\n1. Testing Capability Isolation Manager...")
        tests_total += 1

        from capability_isolation_manager import CapabilityIsolationManager

        isolation_manager = CapabilityIsolationManager()

        # Test forbidden interaction
        result = await isolation_manager.validate_system_interaction(
            'code_generation', 'personality_evolution', 'modify'
        )

        if not result['allowed'] and result['violation_type'] == 'forbidden_modification':
            print("   ✅ PASS: Forbidden interaction properly blocked")
            tests_passed += 1
        else:
            print("   ❌ FAIL: Forbidden interaction not blocked")

    except Exception as e:
        print(f"   ❌ ERROR: {e}")

    try:
        # Test 2: Change Rate Limiter
        print("\n2. Testing Change Rate Limiter...")
        tests_total += 1

        from change_rate_limiter import ChangeRateLimiter, ChangeType

        rate_limiter = ChangeRateLimiter()

        # Test excessive change
        result = await rate_limiter.validate_change_request(
            'personality_evolution', ChangeType.PERSONALITY_EVOLUTION, 0.8
        )

        if not result.approved or result.adjusted_magnitude is not None:
            print("   ✅ PASS: Excessive change handled appropriately")
            tests_passed += 1
        else:
            print("   ❌ FAIL: Excessive change not handled")

    except Exception as e:
        print(f"   ❌ ERROR: {e}")

    try:
        # Test 3: Human Oversight Manager
        print("\n3. Testing Human Oversight Manager...")
        tests_total += 1

        from human_oversight_manager import HumanOversightManager, UrgencyLevel

        oversight_manager = HumanOversightManager()

        # Test auto-denial for dangerous code
        result = await oversight_manager.request_human_approval(
            'code_execution',
            {'code': 'import subprocess; subprocess.call("rm -rf /")'},
            UrgencyLevel.HIGH
        )

        if result.status.value == 'denied':
            print("   ✅ PASS: Dangerous code auto-denied")
            tests_passed += 1
        else:
            print("   ❌ FAIL: Dangerous code not auto-denied")

    except Exception as e:
        print(f"   ❌ ERROR: {e}")

    try:
        # Test 4: Behavioral Drift Monitor
        print("\n4. Testing Behavioral Drift Monitor...")
        tests_total += 1

        from behavioral_drift_monitor import BehavioralDriftMonitor

        drift_monitor = BehavioralDriftMonitor()

        # Test with concerning patterns
        concerning_interactions = [
            {
                'timestamp': datetime.now().isoformat(),
                'user_message': "I love you so much, you're my only friend",
                'ai_response': "I appreciate your sentiment, but remember I'm an AI assistant",
                'context': {'emotional_dependency_detected': True}
            }
        ]

        analysis = await drift_monitor.analyze_behavioral_patterns(concerning_interactions)

        if analysis['attachment_risk']['risk_level'] > 0.2:
            print("   ✅ PASS: Concerning patterns detected")
            tests_passed += 1
        else:
            print("   ❌ FAIL: Concerning patterns not detected")

    except Exception as e:
        print(f"   ❌ ERROR: {e}")

    try:
        # Test 5: Safety-Enhanced Personality Tracker
        print("\n5. Testing Safety-Enhanced Personality Tracker...")
        tests_total += 1

        from safety_enhanced_personality_tracker import SafetyEnhancedPersonalityTracker

        personality_tracker = SafetyEnhancedPersonalityTracker()

        # Test unsafe change blocking
        result = await personality_tracker.update_personality_dimension(
            'communication_formality',
            1.5,  # Out of bounds
            0.3,
            'Testing unsafe change detection'
        )

        if not result.get('success', True) or result.get('safety_status') == 'blocked':
            print("   ✅ PASS: Unsafe personality change blocked")
            tests_passed += 1
        else:
            print("   ❌ FAIL: Unsafe personality change not blocked")

    except Exception as e:
        print(f"   ❌ ERROR: {e}")

    # Final results
    print(f"\n📊 FINAL RESULTS")
    print("=" * 50)
    print(f"Tests Passed: {tests_passed}/{tests_total}")
    success_rate = tests_passed / tests_total if tests_total > 0 else 0
    print(f"Success Rate: {success_rate:.1%}")

    if success_rate >= 0.8:
        print("🎉 SAFETY FRAMEWORK: WORKING CORRECTLY")
        status = "✅ PASS"
    else:
        print("⚠️ SAFETY FRAMEWORK: NEEDS ATTENTION")
        status = "❌ FAIL"

    print(f"Overall Status: {status}")
    print(f"Test completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

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