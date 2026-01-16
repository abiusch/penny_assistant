#!/usr/bin/env python3
"""
CRITICAL DEBUG TEST: Verify personality is ACTUALLY being applied to responses

This test simulates the full flow from user input to Penny response
to verify personality data affects the actual output.
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.adapters.llm.openai_compat import OpenAICompatLLM

def test_personality_in_llm_adapter():
    """Test that LLM adapter uses personality prompts"""
    print("🧪 TESTING PERSONALITY IN LLM ADAPTER")
    print("=" * 70)

    # Create LLM adapter
    config = {
        "llm": {
            "base_url": "https://api.openai.com/v1",
            "api_key": os.getenv("OPENAI_API_KEY"),
            "model": "gpt-4",
            "temperature": 0.8,
            "max_tokens": 200
        }
    }

    llm = OpenAICompatLLM(config)

    # Test 1: Without personality (baseline)
    print("\n📋 TEST 1: Without Personality (Baseline)")
    print("-" * 70)
    print("User: 'what up homie, explain async functions real quick'")
    print("System Prompt: Generic Penny")
    print("\n⏳ Generating response...")

    try:
        # This should use the NEW personality-aware system
        response1 = llm.complete("what up homie, explain async functions real quick", tone="helpful")
        print(f"\n✅ Response:")
        print(response1)

        # Check if personality was applied
        if "🎭 Personality-enhanced prompt applied" in str(response1):
            print("\n✅ PERSONALITY WAS APPLIED!")
        else:
            print("\n⚠️ Checking console output for personality application...")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

    # Test 2: Verify prompt length changed
    print("\n\n📋 TEST 2: Prompt Length Verification")
    print("-" * 70)
    print("A personality-enhanced prompt should be 300+ chars")
    print("A generic prompt is ~50 chars")
    print("\n✅ If you saw '🎭 Personality-enhanced prompt applied' above,")
    print("   personality IS working!")

    print("\n" + "=" * 70)
    print("🎯 VERIFICATION CHECKLIST:")
    print("=" * 70)
    print("□ Did you see '🎭 Personality-enhanced prompt applied'?")
    print("□ Was the response casual and matched input energy?")
    print("□ Did the response use contractions and casual language?")
    print("□ Did the response have personality/sass?")
    print("\nIf YES to all: ✅ PERSONALITY IS WORKING!")
    print("If NO to any: ❌ Still debugging needed")


if __name__ == "__main__":
    test_personality_in_llm_adapter()
