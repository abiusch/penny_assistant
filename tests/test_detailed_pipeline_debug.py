#!/usr/bin/env python3
"""
Detailed debug test that traces through the entire think() method.
"""

import sys
import os
import traceback

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_think_method_detailed():
    """Step through the think method to find exactly where it fails."""

    print("🔍 DETAILED PIPELINE THINK() METHOD DEBUG")
    print("=" * 70)

    try:
        from enhanced_conversation_pipeline import EnhancedConversationPipeline
        from core.pipeline import State

        pipeline = EnhancedConversationPipeline()
        pipeline.state = State.THINKING

        print("✅ Pipeline initialized and state set")

        test_input = "Hello"
        print(f"📝 Testing input: '{test_input}'")

        # Step 1: Extract command
        try:
            actual_command = pipeline.extract_command_from_input(test_input)
            print(f"✅ Command extracted: '{actual_command}'")
        except Exception as e:
            print(f"❌ Command extraction failed: {e}")
            traceback.print_exc()
            return

        # Step 2: Research classification
        try:
            research_required = pipeline.research_manager.requires_research(actual_command)
            financial_topic = pipeline.research_manager.is_financial_topic(actual_command)
            print(f"✅ Research classification - Required: {research_required}, Financial: {financial_topic}")
        except Exception as e:
            print(f"❌ Research classification failed: {e}")
            traceback.print_exc()
            return

        # Step 3: Memory context
        try:
            memory_context = pipeline.memory.get_enhanced_context_for_llm()
            print(f"✅ Memory context retrieved - Length: {len(memory_context) if memory_context else 0}")
        except Exception as e:
            print(f"❌ Memory context failed: {e}")
            traceback.print_exc()
            return

        # Step 4: Build enhanced prompt
        try:
            prompt_sections = []
            if memory_context:
                prompt_sections.append(memory_context)
            prompt_sections.append(f"User: {actual_command}")
            enhanced_prompt = "\n\n".join(prompt_sections)
            print(f"✅ Enhanced prompt built - Length: {len(enhanced_prompt)}")
            print(f"📄 Prompt preview: '{enhanced_prompt[:100]}...'")
        except Exception as e:
            print(f"❌ Prompt building failed: {e}")
            traceback.print_exc()
            return

        # Step 5: Tone routing
        try:
            tone = pipeline._route_tone(actual_command)
            print(f"✅ Tone routing: '{tone}'")
        except Exception as e:
            print(f"❌ Tone routing failed: {e}")
            traceback.print_exc()
            return

        # Step 6: LLM generation
        try:
            print("🤖 Attempting LLM generation...")
            if hasattr(pipeline.llm, 'complete'):
                reply_raw = pipeline.llm.complete(enhanced_prompt, tone=tone)
                print(f"✅ LLM generation successful: '{reply_raw[:100]}...'")
            else:
                reply_raw = pipeline.llm.generate(enhanced_prompt)
                print(f"✅ LLM generation (fallback): '{reply_raw[:100]}...'")
        except Exception as e:
            print(f"❌ LLM generation failed: {e}")
            traceback.print_exc()
            reply_raw = "LLM generation failed"

        # Step 7: Personality enhancement
        try:
            personality_enhanced_reply = pipeline.personality_integration.generate_contextual_response(
                reply_raw, actual_command
            )
            print(f"✅ Personality enhancement: '{personality_enhanced_reply[:100]}...'")
        except Exception as e:
            print(f"❌ Personality enhancement failed: {e}")
            traceback.print_exc()
            personality_enhanced_reply = reply_raw

        # Step 8: Conversation flow
        try:
            topic_category = pipeline.personality_integration._categorize_topic(actual_command, {})
            final_reply = pipeline.conversation_flow.enhance_response_with_flow(
                personality_enhanced_reply,
                actual_command,
                topic_category
            )
            print(f"✅ Conversation flow enhancement: '{final_reply[:100]}...'")
        except Exception as e:
            print(f"❌ Conversation flow failed: {e}")
            traceback.print_exc()
            final_reply = personality_enhanced_reply

        print(f"\n🎯 FINAL RESULT: '{final_reply}'")

        if not final_reply or final_reply.strip() == "":
            print("❌ Empty final result - this is why pipeline returns default message")
        else:
            print("✅ Pipeline would return valid response")

    except Exception as e:
        print(f"❌ Overall test failed: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    test_think_method_detailed()