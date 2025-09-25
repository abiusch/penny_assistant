#!/usr/bin/env python3
"""
Test that research integration preserves Penny's personality.
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_personality_preservation():
    """Test that Penny's personality comes through in research responses."""

    print("🎭 TESTING PERSONALITY PRESERVATION WITH RESEARCH")
    print("=" * 60)

    try:
        from research_first_pipeline import ResearchFirstPipeline
        from core.pipeline import State

        pipeline = ResearchFirstPipeline()

        test_cases = [
            {
                "query": "Hello, how are you?",
                "expectation": "Should be casual, friendly, maybe ask about weather or day"
            },
            {
                "query": "What do you think about emerging robotics companies for investment?",
                "expectation": "Should blend research with personality, ask follow-ups, show engagement"
            },
            {
                "query": "Tell me about Tesla",
                "expectation": "Should be informative but maintain conversational tone and curiosity"
            }
        ]

        for i, case in enumerate(test_cases, 1):
            print(f"\n--- Test {i}: {case['query'][:40]}... ---")
            print(f"Expected: {case['expectation']}")

            pipeline.state = State.THINKING
            response = pipeline.think(case['query'])

            print(f"\n📝 Response ({len(response)} chars):")
            print(f"{response}")

            # Analyze personality indicators
            personality_indicators = {
                'questions': '?' in response,
                'emoji_or_humor': any(char in response for char in '😄😊🤖💰☀️🎉') or any(word in response.lower() for word in ['lol', 'haha', 'hehe', 'witty', 'sassy']),
                'conversational': any(phrase in response.lower() for phrase in ['how about', 'what do you think', 'speaking of', 'by the way', 'you know']),
                'personal_touch': any(word in response.lower() for word in ['i think', 'i feel', 'personally', 'honestly', 'frankly']),
                'casual_language': any(word in response.lower() for word in ["you're", "it's", "don't", "can't", "won't", "i'm"])
            }

            print(f"\n🔍 Personality Analysis:")
            for indicator, present in personality_indicators.items():
                status = "✅" if present else "❌"
                print(f"   {status} {indicator.replace('_', ' ').title()}: {present}")

            personality_score = sum(personality_indicators.values()) / len(personality_indicators) * 100
            print(f"   🎯 Personality Score: {personality_score:.0f}%")

            if personality_score >= 40:
                print("✅ Personality preserved!")
            else:
                print("❌ Response too generic/formal")

            print("-" * 60)

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_personality_preservation()