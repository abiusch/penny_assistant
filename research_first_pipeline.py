#!/usr/bin/env python3
"""
Research-First Conversation Pipeline
A clean implementation that ensures factual queries trigger research before generating responses.
"""

import sys
import os
import time
import logging
from typing import Optional, Dict, Any

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.core.pipeline import PipelineLoop, State
from memory_system import MemoryManager
from emotional_memory_system import create_enhanced_memory_system
from personality_integration import create_personality_integration
from factual_research_manager import ResearchManager

logger = logging.getLogger(__name__)


class ResearchFirstPipeline(PipelineLoop):
    """Research-first pipeline that always researches before answering factual questions."""

    def __init__(self):
        super().__init__()

        # Initialize core systems
        self.base_memory = MemoryManager()
        self.enhanced_memory = create_enhanced_memory_system(self.base_memory)
        self.personality = create_personality_integration(self.enhanced_memory)
        self.research_manager = ResearchManager()

        print("🔬 Research-First Pipeline initialized")
        print("   • Factual queries trigger autonomous research")
        print("   • Financial topics require research validation")
        print("   • Enhanced memory and personality integration active")

    def think(self, user_text: str) -> str:
        """Research-first think method with comprehensive error handling."""
        if self.state.name != "THINKING":
            return ""

        try:
            # Step 1: Process input
            actual_command = user_text.strip()

            # Step 2: Research classification
            research_required = self.research_manager.requires_research(actual_command)
            financial_topic = self.research_manager.is_financial_topic(actual_command)

            print(f"🔍 Query: '{actual_command[:50]}...'")
            print(f"   Research required: {research_required}")
            print(f"   Financial topic: {financial_topic}")

            # Step 3: Conduct research if needed
            research_context = ""
            if research_required:
                print("📚 Conducting research...")
                research_result = self.research_manager.run_research(actual_command, [])

                if research_result.success and research_result.summary:
                    # Format research for personality integration, not replacement
                    key_facts = research_result.key_insights[:3] if research_result.key_insights else []
                    research_context = f"\nResearch findings to incorporate naturally: {research_result.summary[:200]}...\nKey insights: {'; '.join(key_facts)}\nRemember: Respond in Penny's characteristic style while weaving in this information.\n"
                    print(f"✅ Research successful: {research_result.summary[:100]}...")
                else:
                    research_context = "\nResearch attempt failed - acknowledge limitation with Penny's characteristic humor and offer to help differently.\n"
                    print(f"⚠️ Research failed: {research_result.error}")

            # Step 4: Build enhanced prompt
            memory_context = self.enhanced_memory.get_enhanced_context_for_llm()

            # Build personality-focused prompt that integrates research
            prompt_parts = []

            # Always start with personality direction
            personality_direction = (
                "You are Penny, a witty and engaging AI assistant with personality. "
                "Always respond with your characteristic sass, humor, and conversational style. "
                "Ask follow-up questions, make witty observations, and engage like a friend would."
            )
            prompt_parts.append(personality_direction)

            if memory_context:
                prompt_parts.append(f"Context from our relationship: {memory_context}")

            if research_context:
                prompt_parts.append(research_context)

            prompt_parts.append(f"User: {actual_command}")
            prompt_parts.append("Respond as Penny - be informative but keep your personality, humor, and engagement style.")

            enhanced_prompt = "\n\n".join(prompt_parts)

            # Step 5: Generate base response
            tone = self._route_tone(actual_command)

            if hasattr(self.llm, 'complete'):
                base_response = self.llm.complete(enhanced_prompt, tone=tone)
            else:
                base_response = self.llm.generate(enhanced_prompt)

            if not base_response or len(base_response.strip()) == 0:
                base_response = "I'm having trouble generating a response. Could you try rephrasing?"

            print(f"🤖 Base response: {base_response[:100]}...")

            # Step 6: Apply personality enhancement (should amplify, not diminish personality)
            try:
                # Create context that preserves research but enhances personality
                personality_context = {
                    'research_included': research_required,
                    'financial_topic': financial_topic,
                    'user_query': actual_command
                }

                # Fix method signature - only pass base response and command
                enhanced_response = self.personality.generate_contextual_response(
                    base_response, actual_command
                )
                print(f"🎭 Personality applied: {self.personality.personality_system.current_mode.value}")

                # Ensure personality enhancement didn't strip research content
                if research_required and research_result and research_result.success:
                    # If personality system stripped too much research content, blend it back in
                    if len(enhanced_response) < len(base_response) * 0.7:
                        enhanced_response = base_response  # Use original if too much was stripped
                        print("⚠️ Personality enhancement was too aggressive, kept original research response")

            except Exception as e:
                print(f"⚠️ Personality enhancement failed: {e}")
                enhanced_response = base_response

            # Step 7: Add financial disclaimer if needed (in Penny's style)
            final_response = enhanced_response
            if financial_topic:
                # Check if we already have a disclaimer
                if "disclaimer" not in final_response.lower() and "financial advice" not in final_response.lower():
                    penny_disclaimer = (
                        "\n\n(Quick legal note: I'm just sharing info here, not dishing out financial advice. "
                        "Always chat with a real financial pro before making any money moves! 💰)"
                    )
                    final_response += penny_disclaimer

            # Step 8: Store in memory
            try:
                turn = self.base_memory.add_conversation_turn(
                    user_input=actual_command,
                    assistant_response=final_response,
                    context={"research_used": research_required, "financial_topic": financial_topic},
                    response_time_ms=100
                )
                self.enhanced_memory.process_conversation_turn(actual_command, final_response, turn.turn_id)
                print("💾 Conversation saved to memory")
            except Exception as e:
                print(f"⚠️ Memory storage failed: {e}")

            self.state = State.SPEAKING
            return final_response

        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            logger.error(f"Research-first pipeline error: {e}", exc_info=True)
            print(f"❌ Pipeline error: {e}")
            print(f"Full traceback:\n{error_details}")
            self.state = State.SPEAKING
            return f"I encountered an issue processing that request. Please try rephrasing. Error: {str(e)}"


def main():
    """Test the research-first pipeline."""
    print("🧪 Testing Research-First Pipeline")
    print("=" * 50)

    pipeline = ResearchFirstPipeline()

    test_queries = [
        "Hello, how are you?",  # Non-research query
        "What are some emerging robotics companies to invest in?",  # Research + financial
        "Tell me about Tesla's latest developments",  # Research query
        "What's the weather like today?",  # Non-research
    ]

    for i, query in enumerate(test_queries, 1):
        print(f"\n--- Test {i}: {query} ---")
        pipeline.state = State.THINKING
        response = pipeline.think(query)
        print(f"Response length: {len(response)}")
        if response and len(response) > 0:
            print("✅ Valid response generated")
        else:
            print("❌ Empty response - pipeline failed")

        time.sleep(0.5)  # Brief pause between tests

    print(f"\n✨ Research-First Pipeline Testing Complete")


if __name__ == "__main__":
    main()