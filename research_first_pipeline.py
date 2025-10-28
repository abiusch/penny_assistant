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

from chat_entry import respond as chat_respond
from personality.filter import sanitize_output
from src.core.pipeline import PipelineLoop, State
from memory_system import MemoryManager
from emotional_memory_system import create_enhanced_memory_system
from personality_integration import create_personality_integration
from factual_research_manager import ResearchManager

# Phase 2: Dynamic Personality Adaptation
from src.personality.dynamic_personality_prompt_builder import DynamicPersonalityPromptBuilder
from src.personality.personality_response_post_processor import PersonalityResponsePostProcessor
from personality_tracker import PersonalityTracker
import asyncio

# Phase 3A Week 2: Milestone & Achievement System
try:
    from src.personality.personality_milestone_tracker import PersonalityMilestoneTracker
    MILESTONES_AVAILABLE = True
except ImportError:
    MILESTONES_AVAILABLE = False

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

        # Phase 2: Dynamic Personality Adaptation
        self.personality_prompt_builder = DynamicPersonalityPromptBuilder()
        self.personality_post_processor = PersonalityResponsePostProcessor()
        self.personality_tracker = PersonalityTracker()

        # Phase 3A Week 2: Milestone & Achievement System
        self.milestone_tracker = PersonalityMilestoneTracker() if MILESTONES_AVAILABLE else None

        print("🔬 Research-First Pipeline initialized")
        print("   • Factual queries trigger autonomous research")
        print("   • Financial topics require research validation")
        print("   • Enhanced memory and personality integration active")
        print("   • Dynamic personality adaptation enabled (Phase 2)")
        print("   • Active personality learning from conversations enabled")

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

            print(f"🔍 Query: '{actual_command[:50]}...'", flush=True)
            print(f"   Research required: {research_required}", flush=True)
            print(f"   Financial topic: {financial_topic}", flush=True)

            # Track research for web interface
            self.last_research_triggered = research_required
            self.last_research_success = False

            # Step 3: Conduct research if needed
            research_context = ""
            if research_required:
                print("📚 Conducting research...")
                research_result = self.research_manager.run_research(actual_command, [])

                # Debug research result details
                print(f"🔍 DEBUG Research Result:")
                print(f"  - Success: {research_result.success}")
                print(f"  - Has summary: {bool(research_result.summary)}")
                print(f"  - Summary length: {len(research_result.summary) if research_result.summary else 0}")
                print(f"  - Key insights: {len(research_result.key_insights) if research_result.key_insights else 0}")
                print(f"  - Findings count: {len(research_result.findings) if research_result.findings else 0}")

                if research_result.success and research_result.summary:
                    # Track successful research
                    self.last_research_success = True

                    # Format research for personality integration, not replacement
                    key_facts = research_result.key_insights[:3] if research_result.key_insights else []
                    research_context = (
                        f"\n🎯 RESEARCH SUCCESS - You just conducted successful research and found current information!\n"
                        f"RESEARCH FINDINGS: {research_result.summary}\n"
                        f"KEY INSIGHTS: {'; '.join(key_facts) if key_facts else 'Multiple current sources found'}\n"
                        f"SOURCES FOUND: {len(research_result.findings)} sources with current information\n"
                        f"\nINSTRUCTIONS:\n"
                        f"- Share the current information you found in your characteristic sassy Penny style\n"
                        f"- Reference that you just researched this (don't pretend you already knew it)\n"
                        f"- Be engaging and informative using the research findings\n"
                        f"- Maintain your personality while being factually accurate\n"
                        f"- Do NOT say you're not connected to the internet - you just successfully researched this!\n"
                    )
                    print(f"✅ Research successful: {research_result.summary[:100]}...")
                else:
                    research_context = (
                        "\nRESEARCH FAILED - CRITICAL INSTRUCTION: You MUST explicitly tell the user that you don't have current/recent information about this topic. "
                        "Use phrases like 'I don't have current information', 'my data isn't up to date', or 'I can't access recent updates'. "
                        "Do this with Penny's characteristic humor but be completely honest about the limitation. "
                        "ABSOLUTELY DO NOT fabricate specific statistics, dates, technical specs, or recent developments. "
                        "Instead, suggest they check the official Boston Dynamics website, recent tech news, or company announcements.\n"
                    )
                    print(f"⚠️ Research failed: {research_result.error if research_result else 'No research result'}")

            # Step 4: Build contextual prompt for shared persona responder
            memory_context = self.enhanced_memory.get_enhanced_context_for_llm()
            tone = self._route_tone(actual_command)
            render_debug: Dict[str, str] = {}

            def _build_research_instructions() -> str:
                if not research_required:
                    return (
                        "KNOWLEDGE STRATEGY:\n"
                        "- Lead with the most important finding or fix.\n"
                        "- If details might be outdated, say so and suggest checking current sources."
                    )

                if research_result and research_result.success and research_result.summary:
                    return (
                        "RESEARCH MODE:\n"
                        "- You just completed fresh research; cite the findings explicitly.\n"
                        "- State that you researched this rather than claiming prior knowledge.\n"
                        "- Prioritise factual accuracy and cite the key insights provided."
                    )

                return (
                    "RESEARCH MODE (NO DATA):\n"
                    "- Research was attempted but failed; be transparent about the gap.\n"
                    "- Never fabricate numbers or recent events.\n"
                    "- Recommend official sources or recent publications for up-to-date information."
                )

            def llm_generator(system_prompt: str, user_input: str) -> str:
                # Phase 2: Build personality-enhanced prompt
                personality_enhancement = ""
                try:
                    personality_enhancement = asyncio.run(
                        self.personality_prompt_builder.build_personality_prompt(
                            user_id="default",
                            context={'topic': 'general', 'query': user_input}
                        )
                    )
                    print("🎭 Personality-enhanced prompt applied (length: {} chars)".format(len(personality_enhancement)))
                except Exception as e:
                    logger.warning(f"Personality prompt building failed: {e}")

                prompt_sections = [system_prompt if system_prompt else "", _build_research_instructions()]

                # Add personality enhancement early (before research context)
                if personality_enhancement:
                    prompt_sections.append(personality_enhancement)

                if memory_context:
                    prompt_sections.append(f"Conversation context: {memory_context}")

                if research_context:
                    prompt_sections.append(research_context)

                prompt_sections.append(
                    "RESPONSE REQUIREMENTS:\n"
                    "- Stay dry, concise, and direct.\n"
                    "- Lead with the actionable answer before elaborating.\n"
                    "- If recommending verification or research, make it explicit."
                )

                prompt_sections.append(f"User query: {user_input}")

                final_prompt = "\n\n".join(filter(None, prompt_sections))
                render_debug['prompt'] = final_prompt

                if hasattr(self.llm, 'complete'):
                    raw = self.llm.complete(final_prompt, tone=tone)
                else:
                    raw = self.llm.generate(final_prompt)

                render_debug['raw'] = raw
                return raw

            final_response = chat_respond(actual_command, generator=llm_generator)

            if render_debug.get('raw'):
                print(f"🤖 Base response: {render_debug['raw'][:100]}...")

            # Phase 2: Post-process response with personality
            personality_adjustments = []
            try:
                result = asyncio.run(
                    self.personality_post_processor.process_response(
                        final_response,
                        context={'topic': 'general', 'query': actual_command}
                    )
                )
                final_response = result["response"]
                personality_adjustments = result.get("adjustments", [])
                if personality_adjustments:
                    print(f"🎨 Response post-processed: {', '.join(personality_adjustments)}")
                else:
                    print("🎨 Response post-processed (no adjustments needed)")
            except Exception as e:
                logger.warning(f"Personality post-processing failed: {e}")

            # Step 6: Add financial disclaimer if needed (in Penny's style)
            if financial_topic:
                # Check if we already have a disclaimer
                if "disclaimer" not in final_response.lower() and "financial advice" not in final_response.lower():
                    penny_disclaimer = (
                        "\n\nQuick note: I'm sharing general information here, not financial advice. "
                        "Talk to a licensed professional before making money moves."
                    )
                    final_response = sanitize_output(final_response + penny_disclaimer)

            # Step 8: Store in memory
            try:
                print("💾 Attempting to save conversation to memory...", flush=True)
                turn = self.base_memory.add_conversation_turn(
                    user_input=actual_command,
                    assistant_response=final_response,
                    context={"research_used": research_required, "financial_topic": financial_topic},
                    response_time_ms=100
                )
                print(f"💾 Base memory saved, turn_id: {turn.turn_id}", flush=True)

                self.enhanced_memory.process_conversation_turn(actual_command, final_response, turn.turn_id)
                print("💾 Enhanced memory processing complete", flush=True)

                # Update personality tracking from this conversation
                self._update_personality_from_conversation(actual_command, final_response, turn.turn_id)
                print("✅ Conversation saved to memory successfully", flush=True)
            except Exception as e:
                import traceback
                print(f"⚠️ Memory storage failed: {e}", flush=True)
                print(f"⚠️ Traceback: {traceback.format_exc()}", flush=True)

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

    def _update_personality_from_conversation(self, user_input: str, assistant_response: str, turn_id: str):
        """Analyze conversation and update personality dimensions (Phase 2.5: Active Learning)"""
        try:
            # Analyze user's communication style
            context = {}  # TODO: Could add more context like is_follow_up, previous_humor_style, etc.

            print("🧠 Analyzing conversation for personality signals...", flush=True)
            analysis = asyncio.run(self.personality_tracker.analyze_user_communication(user_input, context))

            updates_made = 0

            # Update communication formality if detected with confidence
            formality = analysis.get('formality_level', {})
            if formality.get('confidence', 0) > 0.5:
                asyncio.run(self._update_dimension_if_changed(
                    'communication_formality',
                    formality['value'],
                    formality['confidence'] * 0.05,  # Small confidence boost per conversation
                    f"User message: '{user_input[:50]}...' - formality indicators: {formality.get('indicators', {})}"
                ))
                updates_made += 1

            # Update technical depth preference
            tech_depth = analysis.get('technical_depth_request', {})
            if tech_depth.get('confidence', 0) > 0.5:
                asyncio.run(self._update_dimension_if_changed(
                    'technical_depth_preference',
                    tech_depth['value'],
                    tech_depth['confidence'] * 0.05,
                    f"User message: '{user_input[:50]}...' - technical indicators: {tech_depth.get('indicators', {})}"
                ))
                updates_made += 1

            # Update humor style preference
            humor = analysis.get('humor_response_cues', {})
            if humor.get('confidence', 0) > 0.5:
                asyncio.run(self._update_dimension_if_changed(
                    'humor_style_preference',
                    humor['value'],
                    humor['confidence'] * 0.05,
                    f"User message: '{user_input[:50]}...' - humor response: {humor.get('indicators', {})}"
                ))
                updates_made += 1

            # Update response length preference
            length = analysis.get('length_preference_signals', {})
            if length.get('confidence', 0) > 0.5:
                asyncio.run(self._update_dimension_if_changed(
                    'response_length_preference',
                    length['value'],
                    length['confidence'] * 0.05,
                    f"User message: '{user_input[:50]}...' - length indicators: {length.get('indicators', {})}"
                ))
                updates_made += 1

            if updates_made > 0:
                print(f"🎯 Personality tracking: {updates_made} dimensions analyzed and updated", flush=True)
            else:
                print("🎯 Personality tracking: No strong signals detected in this conversation", flush=True)

            # Phase 3A Week 2: Check for newly achieved milestones
            if self.milestone_tracker:
                try:
                    personality_state_obj = asyncio.run(self.personality_tracker.get_current_personality_state())
                    # Convert PersonalityDimension objects to dict format
                    personality_state = {}
                    for dim_name, dim_obj in personality_state_obj.items():
                        personality_state[dim_name] = {
                            "value": dim_obj.current_value,
                            "confidence": dim_obj.confidence
                        }

                    new_milestones = self.milestone_tracker.check_milestones(
                        user_id="default",
                        personality_state=personality_state
                    )

                    if new_milestones:
                        print(f"\n🎉 NEW ACHIEVEMENT{'S' if len(new_milestones) > 1 else ''}!")
                        for milestone in new_milestones:
                            print(f"   {milestone.icon} {milestone.name}")
                            print(f"      {milestone.description}")
                        print()
                except Exception as milestone_err:
                    print(f"⚠️ Milestone checking failed: {milestone_err}", flush=True)

        except Exception as e:
            print(f"⚠️ Personality tracking update failed: {e}", flush=True)
            import traceback
            print(f"⚠️ Traceback: {traceback.format_exc()}", flush=True)

    async def _update_dimension_if_changed(self, dimension: str, new_value, confidence_change: float, context: str):
        """Helper to update a dimension only if the value changed significantly"""
        try:
            # Get current state
            current_state = await self.personality_tracker.get_current_personality_state()
            current_dim = current_state.get(dimension)

            if not current_dim:
                return False

            # For continuous dimensions, only update if change is significant (> 0.1 difference)
            if current_dim.value_type == 'continuous':
                current_value = float(current_dim.current_value)
                new_value_float = float(new_value)

                # Blend old and new values (learning rate)
                learning_rate = current_dim.learning_rate
                blended_value = current_value * (1 - learning_rate) + new_value_float * learning_rate

                # Only update if blended value is different enough
                if abs(blended_value - current_value) > 0.01:
                    await self.personality_tracker.update_personality_dimension(
                        dimension, blended_value, confidence_change, context
                    )
                    print(f"  • {dimension}: {current_value:.2f} → {blended_value:.2f} (confidence +{confidence_change:.3f})", flush=True)
                    return True

            # For categorical dimensions, update if different from current
            else:
                if str(new_value) != str(current_dim.current_value):
                    await self.personality_tracker.update_personality_dimension(
                        dimension, new_value, confidence_change, context
                    )
                    print(f"  • {dimension}: {current_dim.current_value} → {new_value} (confidence +{confidence_change:.3f})", flush=True)
                    return True

            return False

        except Exception as e:
            print(f"⚠️ Failed to update dimension {dimension}: {e}", flush=True)
            return False


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
