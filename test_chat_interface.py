#!/usr/bin/env python3
"""
Test the updated chat interface with research-first pipeline.
"""

import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_chat_interface():
    """Test that the chat interface imports and initializes correctly."""

    print("🧪 Testing Updated Chat Interface")
    print("=" * 50)

    try:
        print("1️⃣ Testing imports...")
        from chat_penny import main, ResearchFirstPipeline
        print("✅ Imports successful")

        print("\n2️⃣ Testing pipeline initialization...")
        pipeline = ResearchFirstPipeline()
        print("✅ Pipeline initialized successfully")

        print("\n3️⃣ Testing sample research query...")
        from core.pipeline import State
        pipeline.state = State.THINKING
        response = pipeline.think("Tell me about emerging robotics companies with investment potential")

        if response and len(response) > 0:
            print("✅ Research query generated response")
            print(f"Response length: {len(response)}")
            if "research" in response.lower() or "disclaimer" in response.lower():
                print("✅ Response contains research or disclaimer content")
            else:
                print("⚠️ Response may not contain expected research content")
        else:
            print("❌ Research query failed to generate response")

        print("\n4️⃣ Testing simple conversational query...")
        pipeline.state = State.THINKING
        response2 = pipeline.think("Hello, how are you today?")

        if response2 and len(response2) > 0:
            print("✅ Conversational query generated response")
            print(f"Response length: {len(response2)}")
        else:
            print("❌ Conversational query failed")

        print("\n🎉 Chat interface testing complete!")

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_chat_interface()