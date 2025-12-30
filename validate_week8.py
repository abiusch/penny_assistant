#!/usr/bin/env python3
"""
Week 8 Component Validation Script

Run this to validate that all Week 8 components are working correctly
before integration into the main pipeline.

Usage:
    python validate_week8.py

Requirements:
    - All Week 8 files must be in place
    - transformers library installed: pip install transformers torch
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

def test_imports():
    """Test that all Week 8 components can be imported"""
    print("\n" + "="*60)
    print("TEST 1: Imports")
    print("="*60)
    
    try:
        from src.memory.emotion_detector_v2 import EmotionDetectorV2
        print("✅ EmotionDetectorV2 imported successfully")
    except Exception as e:
        print(f"❌ Failed to import EmotionDetectorV2: {e}")
        return False
    
    try:
        from src.memory.emotional_continuity import EmotionalContinuity, EmotionalThread
        print("✅ EmotionalContinuity imported successfully")
    except Exception as e:
        print(f"❌ Failed to import EmotionalContinuity: {e}")
        return False
    
    try:
        from src.personality.personality_snapshots import PersonalitySnapshotManager
        print("✅ PersonalitySnapshotManager imported successfully")
    except Exception as e:
        print(f"❌ Failed to import PersonalitySnapshotManager: {e}")
        return False
    
    try:
        from src.memory.forgetting_mechanism import ForgettingMechanism
        print("✅ ForgettingMechanism imported successfully")
    except Exception as e:
        print(f"❌ Failed to import ForgettingMechanism: {e}")
        return False
    
    try:
        from src.memory.consent_manager import ConsentManager
        print("✅ ConsentManager imported successfully")
    except Exception as e:
        print(f"❌ Failed to import ConsentManager: {e}")
        return False
    
    return True


def test_emotion_detector():
    """Test emotion detection with sample inputs"""
    print("\n" + "="*60)
    print("TEST 2: Emotion Detection")
    print("="*60)
    
    try:
        from src.memory.emotion_detector_v2 import EmotionDetectorV2
        
        detector = EmotionDetectorV2()
        print("✅ Detector initialized")
        
        # Test cases
        test_cases = [
            ("I'm so excited about this!", "joy"),
            ("I'm really worried about work", "fear"),
            ("This makes me so angry", "anger"),
            ("I'm feeling sad", "sadness"),
        ]
        
        passed = 0
        for text, expected_emotion in test_cases:
            result = detector.detect_emotion(text)
            detected = result['dominant_emotion']
            confidence = result['confidence']
            
            # Accept related emotions
            emotion_groups = {
                'joy': ['joy', 'surprise'],
                'fear': ['fear', 'sadness'],
                'anger': ['anger', 'disgust'],
                'sadness': ['sadness', 'fear']
            }
            
            valid_emotions = emotion_groups.get(expected_emotion, [expected_emotion])
            
            if detected in valid_emotions:
                print(f"✅ '{text}' → {detected} ({confidence:.2f})")
                passed += 1
            else:
                print(f"❌ '{text}' → {detected} (expected {expected_emotion})")
        
        print(f"\nPassed: {passed}/{len(test_cases)}")
        return passed >= len(test_cases) * 0.75  # 75% pass rate
        
    except Exception as e:
        print(f"❌ Emotion detection test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_emotional_continuity():
    """Test emotional continuity tracking"""
    print("\n" + "="*60)
    print("TEST 3: Emotional Continuity")
    print("="*60)
    
    try:
        from src.memory.emotion_detector_v2 import EmotionDetectorV2
        from src.memory.emotional_continuity import EmotionalContinuity
        from src.memory.semantic_memory import SemanticMemory
        
        detector = EmotionDetectorV2()
        memory = SemanticMemory()
        tracker = EmotionalContinuity(
            semantic_memory=memory,
            emotion_detector=detector,
            enabled=True
        )
        print("✅ Tracker initialized")
        
        # Test significant emotion tracking
        thread = tracker.track_emotion(
            "I'm absolutely devastated about this",
            "test_turn_001"
        )
        
        if thread:
            print(f"✅ Tracked significant emotion: {thread.emotion} ({thread.intensity:.2f})")
        else:
            print("❌ Failed to track significant emotion")
            return False
        
        # Test weak emotion (should not track)
        thread2 = tracker.track_emotion(
            "That's interesting",
            "test_turn_002"
        )
        
        if thread2 is None:
            print("✅ Correctly ignored weak emotion")
        else:
            print("❌ Incorrectly tracked weak emotion")
            return False
        
        # Test check-in suggestion
        check_in = tracker.should_check_in()
        if check_in:
            print("✅ Check-in suggested for unresolved thread")
            prompt = tracker.generate_check_in_prompt(check_in)
            print(f"   Prompt: {prompt[:80]}...")
        else:
            print("❌ No check-in suggested")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Emotional continuity test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_personality_snapshots():
    """Test personality snapshot system"""
    print("\n" + "="*60)
    print("TEST 4: Personality Snapshots")
    print("="*60)
    
    try:
        from src.personality.personality_snapshots import PersonalitySnapshotManager
        
        manager = PersonalitySnapshotManager(
            storage_path="data/test_validation_snapshots",
            snapshot_interval=50
        )
        print("✅ Snapshot manager initialized")
        
        # Test snapshot creation
        snapshot = manager.create_snapshot(
            personality_state={'formality': 0.3, 'sarcasm': 0.6},
            emotional_threads=[],
            conversation_count=50
        )
        print(f"✅ Created snapshot v{snapshot.version}")
        
        # Test retrieval
        latest = manager.get_latest()
        if latest and latest.version == snapshot.version:
            print("✅ Snapshot retrieval working")
        else:
            print("❌ Snapshot retrieval failed")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Personality snapshot test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_forgetting():
    """Test forgetting mechanism"""
    print("\n" + "="*60)
    print("TEST 5: Forgetting Mechanism")
    print("="*60)
    
    try:
        from src.memory.forgetting_mechanism import ForgettingMechanism
        from src.memory.emotional_continuity import EmotionalThread
        from datetime import datetime, timedelta
        
        forgetter = ForgettingMechanism(decay_days=30)
        print("✅ Forgetting mechanism initialized")
        
        # Create old thread
        old_thread = EmotionalThread(
            emotion='joy',
            intensity=0.9,
            context="Test context",
            timestamp=datetime.now() - timedelta(days=15),
            turn_id="test_old"
        )
        
        # Apply decay
        decayed = forgetter.apply_decay([old_thread])
        
        if len(decayed) == 1 and decayed[0].intensity < 0.9:
            print(f"✅ Decay applied: {0.9:.2f} → {decayed[0].intensity:.2f}")
        else:
            print("❌ Decay not applied correctly")
            return False
        
        # Test complete forgetting
        very_old = EmotionalThread(
            emotion='joy',
            intensity=0.9,
            context="Test",
            timestamp=datetime.now() - timedelta(days=35),
            turn_id="test_very_old"
        )
        
        decayed2 = forgetter.apply_decay([very_old])
        if len(decayed2) == 0:
            print("✅ Old threads completely forgotten")
        else:
            print("❌ Old threads not forgotten")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Forgetting mechanism test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_consent():
    """Test consent manager"""
    print("\n" + "="*60)
    print("TEST 6: Consent Manager")
    print("="*60)
    
    try:
        from src.memory.consent_manager import ConsentManager
        
        consent = ConsentManager(storage_path="data/test_validation_consent.json")
        print("✅ Consent manager initialized")
        
        # Default should be disabled
        if not consent.is_tracking_enabled():
            print("✅ Tracking disabled by default (privacy-first)")
        else:
            print("❌ Tracking enabled by default (should be opt-in)")
            return False
        
        # Grant consent
        consent.grant_consent(emotional_tracking=True, proactive_checkins=True)
        
        if consent.is_tracking_enabled() and consent.is_checkins_enabled():
            print("✅ Consent granted successfully")
        else:
            print("❌ Consent not granted")
            return False
        
        # Revoke consent
        consent.revoke_consent()
        
        if not consent.is_tracking_enabled():
            print("✅ Consent revoked successfully")
        else:
            print("❌ Consent not revoked")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Consent manager test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all validation tests"""
    print("\n" + "="*60)
    print("WEEK 8 COMPONENT VALIDATION")
    print("="*60)
    print("\nValidating all Week 8 emotional continuity components...")
    
    results = []
    
    # Run tests
    results.append(("Imports", test_imports()))
    results.append(("Emotion Detection", test_emotion_detector()))
    results.append(("Emotional Continuity", test_emotional_continuity()))
    results.append(("Personality Snapshots", test_personality_snapshots()))
    results.append(("Forgetting Mechanism", test_forgetting()))
    results.append(("Consent Manager", test_consent()))
    
    # Summary
    print("\n" + "="*60)
    print("VALIDATION SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nOverall: {passed}/{total} tests passed ({passed/total*100:.0f}%)")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! Week 8 is ready for integration!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Check errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
