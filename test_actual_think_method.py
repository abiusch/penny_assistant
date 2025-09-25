#!/usr/bin/env python3
"""
Test the actual think() method directly to see if it returns empty.
"""

import sys
import os
import traceback

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_actual_think_method():
    """Test the actual think() method that chat interface calls."""

    print("🎯 TESTING ACTUAL think() METHOD")
    print("=" * 50)

    try:
        from enhanced_conversation_pipeline import EnhancedConversationPipeline
        from core.pipeline import State

        pipeline = EnhancedConversationPipeline()

        # Test simple query
        print("\n1️⃣ Testing: 'Hello'")
        pipeline.state = State.THINKING
        result = pipeline.think("Hello")
        print(f"Result: '{result}'")
        print(f"Result length: {len(result) if result else 0}")
        print(f"Result type: {type(result)}")

        if not result or result == "":
            print("❌ Empty result from think() method!")
        else:
            print("✅ think() method returned valid response")

        # Test research query
        print("\n2️⃣ Testing: 'Tell me about emerging robotics companies'")
        pipeline.state = State.THINKING
        result2 = pipeline.think("Tell me about emerging robotics companies")
        print(f"Result: '{result2[:100] if result2 else 'EMPTY'}...'")
        print(f"Result length: {len(result2) if result2 else 0}")

        if not result2 or result2 == "":
            print("❌ Empty result from research query!")
        else:
            print("✅ Research query returned valid response")

        # Test with wrong state
        print("\n3️⃣ Testing with IDLE state (should return empty)")
        pipeline.state = State.IDLE
        result3 = pipeline.think("Hello")
        print(f"Result with IDLE state: '{result3}'")
        if result3 == "":
            print("✅ Correctly returns empty for non-THINKING state")
        else:
            print("❌ Should return empty for non-THINKING state")

    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    test_actual_think_method()