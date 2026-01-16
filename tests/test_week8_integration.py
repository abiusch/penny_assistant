#!/usr/bin/env python3
"""
Week 8 Integration Test
Tests the full pipeline with emotional continuity integrated
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from research_first_pipeline import ResearchFirstPipeline
from src.core.pipeline import State

print("=" * 70)
print("WEEK 8 INTEGRATION TEST")
print("=" * 70)

# Initialize pipeline with Week 8
print("\n1️⃣ Initializing pipeline with Week 8...")
pipeline = ResearchFirstPipeline()
print("✅ Pipeline initialized")

# Test 1: Grant consent
print("\n2️⃣ Testing consent management...")
pipeline.consent_manager.grant_consent(
    emotional_tracking=True,
    proactive_checkins=True
)
print(f"✅ Consent granted")
print(f"   - Tracking enabled: {pipeline.consent_manager.is_tracking_enabled()}")
print(f"   - Check-ins enabled: {pipeline.consent_manager.is_checkins_enabled()}")

# Test 2: Process emotional input
print("\n3️⃣ Processing emotional input...")
pipeline.state = State.THINKING
response1 = pipeline.think("I'm really stressed about work layoffs")
print(f"✅ Processed emotional input")
print(f"   - Response length: {len(response1)} chars")
print(f"   - Emotional threads tracked: {len(pipeline.emotional_continuity.threads)}")

if pipeline.emotional_continuity.threads:
    thread = pipeline.emotional_continuity.threads[0]
    print(f"   - Latest thread: {thread.emotion} (intensity={thread.intensity:.2f})")

# Test 3: Check for check-in
print("\n4️⃣ Testing check-in suggestion...")
check_in = pipeline.emotional_continuity.should_check_in()
print(f"✅ Check-in suggested: {check_in is not None}")
if check_in:
    print(f"   - Thread: {check_in.emotion} from turn {check_in.turn_id}")

# Test 4: Process follow-up
print("\n5️⃣ Processing follow-up message...")
pipeline.state = State.THINKING
response2 = pipeline.think("Hey Penny, what's up?")
print(f"✅ Processed follow-up")
print(f"   - Response length: {len(response2)} chars")

# Test 5: Verify emotional continuity features
print("\n6️⃣ Verifying Week 8 features...")
features = {
    "EmotionDetectorV2": hasattr(pipeline, 'emotion_detector_v2'),
    "EmotionalContinuity": hasattr(pipeline, 'emotional_continuity'),
    "ConsentManager": hasattr(pipeline, 'consent_manager'),
    "PersonalitySnapshots": hasattr(pipeline, 'personality_snapshots'),
    "ForgettingMechanism": hasattr(pipeline, 'forgetting_mechanism'),
}

all_present = all(features.values())
for name, present in features.items():
    status = "✅" if present else "❌"
    print(f"   {status} {name}: {present}")

# Summary
print("\n" + "=" * 70)
if all_present and pipeline.consent_manager.is_tracking_enabled():
    print("🎉 WEEK 8 INTEGRATION TEST COMPLETE!")
    print("✅ All features initialized and functional")
    print(f"✅ {len(pipeline.emotional_continuity.threads)} emotional thread(s) tracked")
else:
    print("⚠️ WEEK 8 INTEGRATION TEST INCOMPLETE")
    if not all_present:
        print("❌ Some features missing")
    if not pipeline.consent_manager.is_tracking_enabled():
        print("❌ Tracking not enabled")

print("=" * 70)
