#!/usr/bin/env python3
"""
Quick Profile Inspection Script
Run this to see what Penny has learned about your communication style
"""

import asyncio
from slang_vocabulary_tracker import SlangVocabularyTracker
from contextual_preference_engine import ContextualPreferenceEngine


async def inspect():
    print("👤 USER PROFILE INSPECTION")
    print("="*50)

    tracker = SlangVocabularyTracker()
    engine = ContextualPreferenceEngine()

    # Vocabulary Profile
    profile = await tracker.get_user_vocabulary_profile()
    print(f"\n📊 Vocabulary Profile:")
    print(f"   Formality: {profile['formality_score']:.2f}")
    print(f"   Technical: {profile['technical_depth_score']:.2f}")
    print(f"   Most used: {profile['most_used_terms'][:5]}")

    # Contextual Patterns
    patterns = await engine.get_learned_patterns()
    print(f"\n🎯 Contextual Patterns:")
    print(f"   Contexts analyzed: {patterns['total_contexts_analyzed']}")
    print(f"   Common contexts: {patterns['most_common_contexts'][:3]}")

    print("\n" + "="*50)


if __name__ == "__main__":
    asyncio.run(inspect())
