#!/usr/bin/env python3
"""
Final demonstration of personality-preserved research integration.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def final_demo():
    """Demonstrate that Penny maintains personality while doing research."""

    print("🎭 FINAL PERSONALITY + RESEARCH DEMO")
    print("=" * 60)

    from research_first_pipeline import ResearchFirstPipeline
    from core.pipeline import State

    pipeline = ResearchFirstPipeline()

    demos = [
        {
            "scenario": "Casual Greeting",
            "query": "Hey Penny, how are you doing?",
            "expect": "Should be chatty, friendly, no research"
        },
        {
            "scenario": "Investment Research Query",
            "query": "What robotics companies should I consider investing in?",
            "expect": "Should research BUT maintain Penny's personality, ask follow-ups, be engaging"
        }
    ]

    for demo in demos:
        print(f"\n🎬 SCENARIO: {demo['scenario']}")
        print(f"Query: \"{demo['query']}\"")
        print(f"Expected: {demo['expect']}")
        print("-" * 60)

        pipeline.state = State.THINKING
        response = pipeline.think(demo['query'])

        print("🤖 Penny's Response:")
        print(response)
        print(f"\n📊 Response Stats: {len(response)} characters")

        # Check for personality vs generic corporate speak
        personality_signs = [
            ('Emoji/Expression', any(c in response for c in '😄😊🤖💰☀️🎉🚗💡🌊🐬☕')),
            ('Questions to user', '?' in response and any(word in response.lower() for word in ['you', 'your'])),
            ('Casual contractions', any(word in response for word in ["I'm", "you're", "it's", "don't", "can't"])),
            ('Personal touch', any(phrase in response.lower() for phrase in ['i think', 'personally', 'honestly', 'in my opinion'])),
            ('Conversational hooks', any(phrase in response.lower() for phrase in ['speaking of', 'by the way', 'how about', 'what do you think']))
        ]

        print("\n🔍 Personality Check:")
        for sign, present in personality_signs:
            status = "✅" if present else "❌"
            print(f"   {status} {sign}")

        personality_count = sum(present for _, present in personality_signs)
        if personality_count >= 2:
            print(f"🎉 PERSONALITY PRESERVED! ({personality_count}/5 indicators)")
        else:
            print(f"⚠️ Personality weak ({personality_count}/5 indicators)")

        print("=" * 60)

if __name__ == "__main__":
    final_demo()