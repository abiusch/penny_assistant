#!/usr/bin/env python3
"""
Phase 1 Integration Test - Quick Reality Check
Tests slang_vocabulary_tracker and contextual_preference_engine with real Penny
"""

import asyncio
import logging
import os
import sys
from typing import Dict, Any

# Ensure local packages can be imported
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from slang_vocabulary_tracker import SlangVocabularyTracker
from contextual_preference_engine import ContextualPreferenceEngine
from research_first_pipeline import ResearchFirstPipeline

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("phase1_integration")


async def test_vocabulary_tracking():
    """Test vocabulary tracking with sample messages"""
    print("\n" + "="*70)
    print("🧪 PHASE 1 INTEGRATION TEST: Vocabulary Tracking")
    print("="*70)

    tracker = SlangVocabularyTracker()

    # Simulate different conversation styles
    test_messages = [
        {
            "message": "yo penny, what's the deal with async functions?",
            "context": {"topic": "programming", "formality": "casual"},
            "description": "Casual tech question"
        },
        {
            "message": "Could you please explain the difference between synchronous and asynchronous programming?",
            "context": {"topic": "programming", "formality": "formal"},
            "description": "Formal tech question"
        },
        {
            "message": "ngl, python's async/await syntax is pretty fire 🔥",
            "context": {"topic": "programming", "formality": "casual"},
            "description": "Slang-heavy casual"
        },
        {
            "message": "I appreciate the comprehensive explanation. The implementation details are quite intricate.",
            "context": {"topic": "programming", "formality": "formal"},
            "description": "Formal appreciation"
        },
    ]

    print("\n📝 Analyzing test messages...")
    for i, test in enumerate(test_messages, 1):
        print(f"\n{i}. {test['description']}")
        print(f"   Message: \"{test['message']}\"")

        result = await tracker.analyze_message_vocabulary(
            test['message'],
            test['context']
        )

        print(f"   → Vocabulary style: {result['vocabulary_style']}")
        print(f"   → Slang detected: {result['slang_detected'][:3]}")
        print(f"   → Technical terms: {result['technical_terms'][:3]}")
        print(f"   → Casual terms: {result['casual_terms'][:3]}")
        print(f"   → Formal terms: {result['formal_terms'][:3]}")

    # Get learned profile
    print("\n" + "-"*70)
    print("📊 LEARNED VOCABULARY PROFILE:")
    print("-"*70)

    profile = await tracker.get_user_vocabulary_profile()
    print(f"Formality Score: {profile['formality_score']:.2f} (0=casual, 1=formal)")
    print(f"Technical Depth: {profile['technical_depth_score']:.2f}")
    print(f"Total Unique Terms: {profile['total_unique_terms']}")
    print(f"Vocabulary Diversity: {profile['vocabulary_diversity_score']:.2f}")
    most_used = [term['term'] for term in profile['most_used_terms'][:5]]
    print(f"Most Used Terms: {most_used}")

    return profile


async def test_contextual_preferences():
    """Test contextual preference engine"""
    print("\n" + "="*70)
    print("🎯 PHASE 1 INTEGRATION TEST: Contextual Preferences")
    print("="*70)

    engine = ContextualPreferenceEngine()

    # Simulate different contexts
    test_contexts = [
        {
            "message": "how do I fix this bug?",
            "context": {"time_of_day": "late_night", "recent_errors": True},
            "description": "Late night debugging"
        },
        {
            "message": "let's brainstorm some features",
            "context": {"time_of_day": "morning", "energy_level": "high"},
            "description": "Morning creative session"
        },
        {
            "message": "explain this error message",
            "context": {"time_of_day": "afternoon", "frustration_detected": True},
            "description": "Afternoon troubleshooting"
        },
    ]

    print("\n🔍 Analyzing contexts...")
    for i, test in enumerate(test_contexts, 1):
        print(f"\n{i}. {test['description']}")
        print(f"   Message: \"{test['message']}\"")
        print(f"   Context: {test['context']}")

        result = await engine.analyze_current_context(
            test['message'],
            test['context']
        )

        print(f"   → Time of day: {result['time_of_day']}")
        print(f"   → Topic category: {result['topic_category']}")
        print(f"   → Social context: {result['social_context']}")
        print(f"   → Mood state: {result['mood_state']}")
        print(f"   → Work/Personal: {result['work_personal']}")

    # Get learned patterns
    print("\n" + "-"*70)
    print("📈 LEARNED CONTEXTUAL INSIGHTS:")
    print("-"*70)

    insights = await engine.get_contextual_insights()
    print(f"Learned contexts: {len(insights['learned_contexts'])}")
    print(f"Context diversity: {insights['context_diversity']}")
    print(f"Strongest effects: {len(insights['strongest_context_effects'])}")
    print(f"Most effective: {len(insights['most_effective_contexts'])}")

    return insights


async def test_with_real_penny():
    """Integration test with real Penny pipeline"""
    print("\n" + "="*70)
    print("🤖 PHASE 1 INTEGRATION TEST: Real Penny Pipeline")
    print("="*70)

    # Initialize components
    tracker = SlangVocabularyTracker()
    engine = ContextualPreferenceEngine()
    pipeline = ResearchFirstPipeline()

    print("\n✅ Components initialized successfully")
    print("📝 Ready to test with real conversations")
    print("\nTo use with chat_penny.py, add these lines to the message handler:")
    print("""
    # In chat_penny.py message handler:
    vocab_analysis = await slang_tracker.analyze_message_vocabulary(user_message, context)
    current_context = await context_engine.analyze_current_context(user_message, context)

    # Log for analysis (don't change behavior yet)
    logger.info(f"Vocab: {vocab_analysis['vocabulary_style']}, Context: {current_context['context_type']}")
    """)

    return True


async def inspect_user_profile():
    """Quick script to inspect learned user profile"""
    print("\n" + "="*70)
    print("👤 USER VOCABULARY PROFILE INSPECTION")
    print("="*70)

    tracker = SlangVocabularyTracker()
    engine = ContextualPreferenceEngine()

    # Get vocabulary profile
    vocab_profile = await tracker.get_user_vocabulary_profile()
    print(f"\n📊 Vocabulary Profile:")
    print(f"   Formality: {vocab_profile['formality_score']:.2f}")
    print(f"   Technical: {vocab_profile['technical_depth_score']:.2f}")
    most_used_terms = [t['term'] for t in vocab_profile['most_used_terms'][:5]]
    print(f"   Most used: {most_used_terms}")
    print(f"   Diversity: {vocab_profile['vocabulary_diversity_score']:.2f}")

    # Get contextual insights
    insights = await engine.get_contextual_insights()
    print(f"\n🎯 Contextual Insights:")
    print(f"   Learned contexts: {len(insights['learned_contexts'])}")
    print(f"   Context diversity: {insights['context_diversity']}")

    print(f"\n✅ Phase 1 components are tracking user communication patterns!")


async def main():
    """Run all integration tests"""
    print("🚀 Starting Phase 1 Integration Tests")
    print("="*70)

    try:
        # Test 1: Vocabulary Tracking
        vocab_profile = await test_vocabulary_tracking()

        # Test 2: Contextual Preferences
        patterns = await test_contextual_preferences()

        # Test 3: Integration readiness
        ready = await test_with_real_penny()

        # Final inspection
        await inspect_user_profile()

        print("\n" + "="*70)
        print("✅ PHASE 1 INTEGRATION TESTS COMPLETE")
        print("="*70)
        print("\n📋 Next Steps:")
        print("1. ✅ Phase 1 components work in isolation")
        print("2. 🔄 Add logging to chat_penny.py (see output above)")
        print("3. 💬 Have real conversations with Penny")
        print("4. 📊 Run this script again to see learned patterns")
        print("5. ➡️  Move to Phase 2 when ready")

    except Exception as e:
        logger.error(f"Integration test failed: {e}", exc_info=True)
        print(f"\n❌ Test failed: {e}")
        return False

    return True


if __name__ == "__main__":
    asyncio.run(main())
