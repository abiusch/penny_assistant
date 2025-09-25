#!/usr/bin/env python3
"""
Direct test of the enhanced conversation pipeline to identify failures.
"""

import sys
import os
import traceback

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_pipeline_stages():
    """Test each stage of the enhanced pipeline to identify failure points."""

    print("🔧 ENHANCED CONVERSATION PIPELINE DEBUG")
    print("=" * 60)

    # Test 1: Basic imports
    print("\n1️⃣ Testing imports...")
    try:
        from enhanced_conversation_pipeline import EnhancedConversationPipeline
        from core.pipeline import State
        print("✅ Enhanced pipeline imports successful")
    except Exception as e:
        print(f"❌ Import failed: {e}")
        traceback.print_exc()
        return

    # Test 2: Pipeline initialization
    print("\n2️⃣ Testing pipeline initialization...")
    try:
        pipeline = EnhancedConversationPipeline()
        print("✅ Pipeline initialized")
    except Exception as e:
        print(f"❌ Pipeline initialization failed: {e}")
        traceback.print_exc()
        return

    # Test 3: Basic conversation setup
    print("\n3️⃣ Testing basic conversation setup...")
    try:
        pipeline.state = State.THINKING
        print(f"✅ Pipeline state set to: {pipeline.state}")
    except Exception as e:
        print(f"❌ State setting failed: {e}")
        traceback.print_exc()
        return

    # Test 4: Simple non-research query
    print("\n4️⃣ Testing simple query (Hello)...")
    try:
        response = pipeline.think("Hello")
        print(f"✅ Simple query response: '{response[:100]}...'")
        if response == "I didn't catch that. Could you rephrase?" or not response:
            print("⚠️ Got default failure response - pipeline is failing internally")
        else:
            print("✅ Simple query working correctly")
    except Exception as e:
        print(f"❌ Simple query failed: {e}")
        traceback.print_exc()

    # Test 5: Research query
    print("\n5️⃣ Testing research query (emerging robotics companies)...")
    try:
        pipeline.state = State.THINKING  # Reset state
        response = pipeline.think("Tell me about emerging robotics companies")
        print(f"✅ Research query response: '{response[:100]}...'")
        if response == "I didn't catch that. Could you rephrase?" or not response:
            print("⚠️ Research query also getting default failure response")
        else:
            print("✅ Research query working correctly")
    except Exception as e:
        print(f"❌ Research query failed: {e}")
        traceback.print_exc()

    # Test 6: Check research manager directly
    print("\n6️⃣ Testing research manager directly...")
    try:
        research_required = pipeline.research_manager.requires_research("Tell me about emerging robotics companies")
        financial_topic = pipeline.research_manager.is_financial_topic("Tell me about emerging robotics companies")
        print(f"✅ Research required: {research_required}")
        print(f"✅ Financial topic: {financial_topic}")
    except Exception as e:
        print(f"❌ Research manager test failed: {e}")
        traceback.print_exc()

    # Test 7: Check LLM integration
    print("\n7️⃣ Testing LLM integration...")
    try:
        if hasattr(pipeline, 'llm'):
            print(f"✅ LLM available: {type(pipeline.llm)}")
            if hasattr(pipeline.llm, 'complete'):
                print("✅ LLM has complete method")
                test_response = pipeline.llm.complete("Say hello", tone="friendly")
                print(f"✅ Direct LLM test: '{test_response[:50]}...'")
            else:
                print("⚠️ LLM missing complete method")
        else:
            print("❌ No LLM found on pipeline")
    except Exception as e:
        print(f"❌ LLM test failed: {e}")
        traceback.print_exc()

    # Test 8: Memory system
    print("\n8️⃣ Testing memory system...")
    try:
        memory_context = pipeline.memory.get_enhanced_context_for_llm()
        print(f"✅ Memory context length: {len(memory_context) if memory_context else 0}")
    except Exception as e:
        print(f"❌ Memory system test failed: {e}")
        traceback.print_exc()

    # Test 9: Personality system
    print("\n9️⃣ Testing personality system...")
    try:
        test_response = pipeline.personality_integration.generate_contextual_response(
            "Hello", "Hello"
        )
        print(f"✅ Personality system: '{test_response[:50]}...'")
    except Exception as e:
        print(f"❌ Personality system test failed: {e}")
        traceback.print_exc()

    print("\n" + "=" * 60)
    print("🎯 DEBUG SUMMARY:")
    print("- Check which tests failed to identify the root cause")
    print("- If LLM integration fails, the pipeline will return empty responses")
    print("- If research manager fails, research queries won't work")
    print("- If personality fails, all responses will be generic")

if __name__ == "__main__":
    test_pipeline_stages()