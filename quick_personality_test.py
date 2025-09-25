#!/usr/bin/env python3
"""Quick test of personality integration."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def quick_test():
    from research_first_pipeline import ResearchFirstPipeline
    from core.pipeline import State

    pipeline = ResearchFirstPipeline()

    # Test a simple greeting
    pipeline.state = State.THINKING
    response = pipeline.think("How are you doing today?")

    print("Response:")
    print(response)
    print(f"\nLength: {len(response)}")

    # Check for personality indicators
    has_personality = any([
        '?' in response and 'you' in response.lower(),
        any(emoji in response for emoji in '😄😊🤖💰☀️🎉🚗💡'),
        any(word in response.lower() for word in ["i'm", "you're", "it's", "can't"]),
        any(phrase in response.lower() for phrase in ['how about', 'speaking of', 'by the way'])
    ])

    print(f"Has personality indicators: {has_personality}")

if __name__ == "__main__":
    quick_test()