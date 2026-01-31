#!/usr/bin/env python3
"""
Research-First Conversation Pipeline
A clean implementation that ensures factual queries trigger research before generating responses.
"""

import sys
import os
import time
import logging
import json
from typing import Optional, Dict, Any
from datetime import datetime

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
from src.personality.personality_milestone_tracker import PersonalityMilestoneTracker
from src.personality.adaptation_ab_test import get_ab_test, ABTestMetrics

# Phase 3B Week 3: Tool Calling Infrastructure
from src.tools.tool_orchestrator import ToolOrchestrator
from src.tools.tool_registry import get_tool_registry

# Week 6: Context Manager, Emotion Detector, Semantic Memory Integration
from src.memory import ContextManager, EmotionDetector, SemanticMemory

# Week 7.5: Nemotron-3 Nano Local LLM
from src.llm.nemotron_client import create_nemotron_client

# Week 8: Emotional Continuity System
from src.memory.emotion_detector_v2 import EmotionDetectorV2
from src.memory.emotional_continuity import EmotionalContinuity
from src.personality.personality_snapshots import PersonalitySnapshotManager
from src.memory.forgetting_mechanism import ForgettingMechanism
from src.memory.consent_manager import ConsentManager

# Week 8.5: Judgment & Clarify System
from src.judgment import JudgmentEngine, PennyStyleClarifier

# Week 10: Hebbian Learning System (with safety features)
try:
    from src.personality.hebbian import HebbianLearningManager
    HEBBIAN_AVAILABLE = True
except ImportError:
    HEBBIAN_AVAILABLE = False

logger = logging.getLogger(__name__)


class ResearchFirstPipeline(PipelineLoop):
    """Research-first pipeline that always researches before answering factual questions."""

    def __init__(self):
        super().__init__()

        # WEEK 7.5: Replace OpenAI with Nemotron-3 Nano (local LLM)
        try:
            self.llm = create_nemotron_client(
                reasoning_mode="auto",  # Intelligent: Fast for chat, reasoning for complex queries
                temperature=0.7
            )
            logger.info("✅ Using Nemotron-3 Nano (100% local, zero cost)")
        except Exception as e:
            logger.warning(f"⚠️ Nemotron not available: {e}")
            # Fallback to parent's LLM (OpenAI via factory)
            logger.info("Fallback to LLMFactory (from config)")

        # Initialize core systems
        # WEEK 7: Removed base_memory and enhanced_memory (redundant with semantic memory)
        # self.base_memory = MemoryManager()  # REMOVED - redundant
        # self.enhanced_memory = create_enhanced_memory_system(self.base_memory)  # REMOVED - redundant
        # self.personality = create_personality_integration(self.enhanced_memory)  # REMOVED - refactor needed
        self.research_manager = ResearchManager()

        # Phase 2: Dynamic Personality Adaptation
        self.personality_prompt_builder = DynamicPersonalityPromptBuilder()
        self.personality_post_processor = PersonalityResponsePostProcessor()
        self.personality_tracker = PersonalityTracker()

        # Phase 3A Week 2: Milestone & Achievement System
        self.milestone_tracker = PersonalityMilestoneTracker()
        logger.info("🏆 Milestone tracker initialized")

        self.ab_test = get_ab_test()
        logger.info("📊 A/B testing framework initialized")

        # Phase 3B Week 3: Tool Calling Infrastructure
        self.tool_registry = get_tool_registry()
        self.tool_orchestrator = ToolOrchestrator(max_iterations=3)
        self.tool_registry.register_with_orchestrator(self.tool_orchestrator)
        logger.info("🔧 Tool orchestrator initialized with {} tools".format(len(self.tool_registry.tools)))

        # Week 6: Context Manager, Emotion Detector, Semantic Memory
        self.context_manager = ContextManager(max_window_size=10)
        self.emotion_detector = EmotionDetector()
        self.semantic_memory = SemanticMemory()
        logger.info("🧠 Week 6 systems initialized: Context Manager, Emotion Detector, Semantic Memory")

        # Week 8: Emotional Continuity System
        self.consent_manager = ConsentManager()
        self.emotion_detector_v2 = EmotionDetectorV2()
        self.emotional_continuity = EmotionalContinuity(
            semantic_memory=self.semantic_memory,
            emotion_detector=self.emotion_detector_v2,
            window_days=self.consent_manager.get_memory_window(),
            intensity_threshold=self.consent_manager.get_intensity_threshold(),
            enabled=self.consent_manager.is_tracking_enabled()
        )
        self.personality_snapshots = PersonalitySnapshotManager(
            storage_path="data/personality_snapshots",
            snapshot_interval=50
        )
        self.forgetting_mechanism = ForgettingMechanism(decay_days=30)
        logger.info("🧠 Week 8 Emotional Continuity initialized")

        # Week 8.5: Initialize Judgment & Clarify System
        self.judgment_enabled = True  # Will be configurable via config.json
        if self.judgment_enabled:
            self.judgment_engine = JudgmentEngine()
            self.clarifier = PennyStyleClarifier()
            logger.info("🧠 Week 8.5 Judgment & Clarify System initialized")
            print("   • Week 8.5: Judgment & Clarify System active")
            print("     - Detects vague referents, missing parameters, contradictions")
            print("     - Stakes assessment (LOW/MEDIUM/HIGH)")
            print("     - Confidence scoring (0.0-1.0)")
            print("     - Penny-style clarifications (casual, confident, brief)")

        # Week 10: Initialize Hebbian Learning System (with safety features)
        self.hebbian_enabled = False  # Disabled by default until Day 10 testing
        self.hebbian = None
        self.last_judgment_result = None  # Store for safety check

        if HEBBIAN_AVAILABLE and self.hebbian_enabled:
            try:
                self.hebbian = HebbianLearningManager(
                    db_path='data/personality_tracking.db',
                    enable_caching=True,
                    # Safety configuration
                    promotion_min_observations=5,
                    promotion_min_days=7,
                    max_staging_age_days=30,
                    turn_budget_max_writes=5,
                    turn_budget_max_time_ms=15000
                )
                logger.info("🧠 Week 10 Hebbian Learning initialized (with safety)")
                print("   • Week 10: Hebbian Learning System active")
                print("     - Learning quarantine (staging → permanent)")
                print("     - Turn budgets (max 5 writes, 15s time limit)")
                print("     - Mini-observability (drift detection)")
            except Exception as e:
                logger.warning(f"⚠️ Hebbian Learning not available: {e}")
                self.hebbian = None
        else:
            if not HEBBIAN_AVAILABLE:
                logger.info("Hebbian Learning not available (import failed)")
            else:
                logger.info("Hebbian Learning disabled (set hebbian_enabled=True to enable)")

        print("🔬 Research-First Pipeline initialized (Week 7.5 Architecture)")
        print("   • Factual queries trigger autonomous research")
        print("   • Financial topics require research validation")
        print("   • Dynamic personality adaptation enabled (Phase 2)")
        print("   • Active personality learning from conversations enabled")
        print("   • Tool calling system active (Phase 3B Week 3)")
        print("   • Week 7: Single-store architecture with encryption")
        print("     - Context Manager: In-memory cache only (10 turns)")
        print("     - Semantic Memory: ONLY persistent store (encrypted emotions)")
        print("     - Data encryption: AES-128 for sensitive fields (GDPR compliant)")
        print("     - PII detection: Ready for culture learning (Week 8-9)")
        print("   • Week 7.5: Nemotron-3 Nano Local LLM")
        print("     - 100% local inference (zero API costs)")
        print("     - 1M token context window")
        print("     - Built for agentic AI workflows")
        print("   • Week 8: Emotional Continuity System")
        print("     - Advanced emotion detection (transformer-based, 27 emotions)")
        print("     - Cross-session emotional tracking (7-day window)")
        print("     - Natural check-ins about past emotional moments")
        print("     - Personality snapshots with rollback capability")
        print("     - Gradual forgetting mechanism (30-day decay)")
        print("     - User consent & privacy controls (GDPR Article 17)")

    def _should_clarify(self, user_input: str, context: dict) -> tuple[bool, Optional[str]]:
        """
        Check if we should clarify before proceeding.

        Args:
            user_input: The user's message
            context: Conversation context

        Returns:
            (should_clarify: bool, clarifying_question: str or None)

        Example:
            should_clarify, question = self._should_clarify("Fix that bug", context)
            if should_clarify:
                return question  # Ask for clarification
            # else: proceed with tools
        """
        # Check if judgment is enabled
        if not self.judgment_enabled:
            return False, None

        # Build context for judgment engine
        judgment_context = {
            'conversation_history': context.get('conversation_history', []),
            'semantic_memory': context.get('semantic_memory', []),
            'emotional_state': context.get('emotional_state'),
            'personality_state': context.get('personality_state')
        }

        # Get judgment decision
        decision = self.judgment_engine.analyze_request(user_input, judgment_context)

        # Log judgment decision
        self._log_judgment_decision(decision, user_input)

        # If clarification needed, format in Penny's voice
        if decision.clarify_needed:
            clarifying_question = self.clarifier.format_question(
                decision,
                user_input=user_input
            )

            # Log judgment decision
            logger.info(f"🤔 Judgment: Clarifying due to {decision.reasoning}")
            print(f"🤔 Judgment: Clarifying due to {decision.reasoning}")
            print(f"💬 Question: {clarifying_question}")

            return True, clarifying_question

        return False, None

    def _log_judgment_decision(self, decision, user_input: str):
        """
        Log judgment decision for analysis.

        Useful for:
        - Understanding when judgment triggers
        - Tuning detection thresholds
        - Debugging clarification logic

        Args:
            decision: Decision object from JudgmentEngine
            user_input: Original user input
        """
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'user_input': user_input,
            'clarify_needed': decision.clarify_needed,
            'reasoning': decision.reasoning,
            'stakes_level': decision.stakes_level.value,
            'confidence': decision.confidence,
            'intent': decision.intent
        }

        # Store for safety check
        self.last_judgment_result = log_entry

        # Log to file for analysis
        log_file = 'data/judgment_logs.jsonl'
        os.makedirs('data', exist_ok=True)

        with open(log_file, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')

    def _is_safe_to_learn(self, message: str, context: dict) -> bool:
        """
        Additional safety checks before Hebbian learning.

        Week 10 Day 9: Safety-first approach to learning.
        Prevents learning from ambiguous or low-confidence inputs.

        Args:
            message: User message
            context: Conversation context

        Returns:
            bool: Whether it's safe to learn from this interaction
        """
        # Check 1: Don't learn if judgment flagged issues
        if self.last_judgment_result:
            judgment = self.last_judgment_result
            if judgment.get('clarify_needed', False):
                logger.debug("Skipping Hebbian learning: judgment flagged ambiguity")
                return False

            if judgment.get('confidence', 1.0) < 0.7:
                logger.debug("Skipping Hebbian learning: low judgment confidence")
                return False

        # Check 2: Message must be substantive
        if len(message.strip()) < 5:
            logger.debug("Skipping Hebbian learning: message too short")
            return False

        # Check 3: Context must be clear (not 'unclear' type)
        if context.get('context_type') == 'unclear':
            logger.debug("Skipping Hebbian learning: unclear context")
            return False

        return True

    def _get_personality_state_for_learning(self) -> dict:
        """Get current personality state for Hebbian learning."""
        try:
            return self.personality_tracker.get_personality_state()
        except Exception as e:
            logger.warning(f"Could not get personality state: {e}")
            return {}

    def think(self, user_text: str) -> str:
        """Research-first think method with comprehensive error handling."""
        if self.state.name != "THINKING":
            return ""

        try:
            # Step 0: A/B test assignment
            start_time = time.time()
            user_id = "default"  # Could be extracted from context if multi-user
            conversation_id = f"conv_{user_id}_{datetime.now().timestamp()}"
            group = self.ab_test.assign_group(conversation_id, user_id)
            is_control = self.ab_test.is_control_group(conversation_id)

            if is_control:
                logger.info(f"🧪 A/B Test: Control group (baseline)")
            else:
                logger.info(f"🧪 A/B Test: Treatment group (adapted)")

            # Step 1: Process input
            actual_command = user_text.strip()

            # Step 1.2: Week 8.5 - Judgment check (should we clarify first?)
            # Build initial context for judgment
            initial_judgment_context = {
                'conversation_history': [],  # Will populate from context manager
                'semantic_memory': [],
                'emotional_state': None,
                'personality_state': None
            }

            # Check if we should clarify before proceeding
            should_clarify, clarifying_question = self._should_clarify(actual_command, initial_judgment_context)

            if should_clarify:
                # Return clarifying question instead of processing
                logger.info(f"✋ Judgment system returned clarification - not proceeding with tools")
                self.state = State.SPEAKING
                return clarifying_question

            # Step 1.5: Week 6 - Detect emotion from user input
            emotion_result = self.emotion_detector.detect_emotion(actual_command)
            print(f"😊 Emotion detected: {emotion_result.primary_emotion} (confidence: {emotion_result.confidence:.2f}, sentiment: {emotion_result.sentiment})")

            # Step 1.6: Week 8 - Track significant emotions and check for emotional context
            turn_id = f"turn_{int(time.time() * 1000)}"
            emotional_thread = None
            check_in_thread = None
            emotional_context = ""

            if self.consent_manager.is_tracking_enabled():
                # Track emotion if significant
                emotional_thread = self.emotional_continuity.track_emotion(
                    user_input=actual_command,
                    turn_id=turn_id
                )

                if emotional_thread:
                    logger.info(
                        f"📌 Tracked emotion: {emotional_thread.emotion} "
                        f"(intensity={emotional_thread.intensity:.2f})"
                    )

                # Check if we should reference previous emotional context
                if self.consent_manager.is_checkins_enabled():
                    check_in_thread = self.emotional_continuity.should_check_in()

                    if check_in_thread:
                        emotional_context = self.emotional_continuity.generate_check_in_prompt(
                            check_in_thread
                        )
                        logger.info(f"💭 Suggesting emotional check-in: {check_in_thread.emotion}")

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
            # WEEK 7: Removed enhanced_memory context (now using semantic memory only)
            # memory_context = self.enhanced_memory.get_enhanced_context_for_llm()  # REMOVED
            tone = self._route_tone(actual_command)
            render_debug: Dict[str, str] = {}

            # Step 4.5: Week 6 - Get conversation context and semantic memories
            conversation_context = self.context_manager.get_context_for_prompt(max_turns=5, include_metadata=True)
            print(f"💬 Conversation context: {len(conversation_context)} chars")

            # Get semantic memories (similar past conversations)
            semantic_results = []
            try:
                semantic_results = self.semantic_memory.semantic_search(query=actual_command, k=3)
                print(f"🧠 Semantic memory: Found {len(semantic_results)} relevant memories")
            except Exception as e:
                logger.warning(f"Semantic search failed: {e}")

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
                # Phase 2: Build personality-enhanced prompt (only for treatment group)
                personality_enhancement = ""
                if not is_control:
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
                else:
                    print("🧪 A/B Test: Skipping personality enhancement (control group)")

                prompt_sections = [system_prompt if system_prompt else "", _build_research_instructions()]

                # Add personality enhancement early (before research context) - only for treatment
                if personality_enhancement and not is_control:
                    prompt_sections.append(personality_enhancement)

                # Week 6: Add conversation context from context manager
                if conversation_context:
                    prompt_sections.append(f"\n{conversation_context}")

                # Week 6: Add semantic memory context
                if semantic_results:
                    semantic_context = "\n\nRelevant past conversations:"
                    for result in semantic_results:
                        semantic_context += f"\n- User: {result.get('user_input', '')[:100]}... (similarity: {result.get('similarity', 0):.2f})"
                    prompt_sections.append(semantic_context)

                # Week 8: Add emotional context if check-in suggested
                if emotional_context:
                    prompt_sections.append(emotional_context)

                # Week 6: Add current topic and emotional state
                stats = self.context_manager.get_stats()
                context_info = []
                if stats.get('current_topic'):
                    context_info.append(f"Current topic: {stats['current_topic']}")
                if stats.get('emotional_state'):
                    context_info.append(f"User's emotional state: {stats['emotional_state']}")
                if emotion_result:
                    context_info.append(f"User's current emotion: {emotion_result.primary_emotion} ({emotion_result.sentiment})")
                if context_info:
                    prompt_sections.append("\n\n" + "\n".join(context_info))

                # WEEK 7: Removed legacy memory_context (using semantic memory instead)
                # if memory_context:
                #     prompt_sections.append(f"Legacy conversation context: {memory_context}")

                if research_context:
                    prompt_sections.append(research_context)

                # Phase 3B Week 3: Add tool manifest
                tool_manifest = self.tool_registry.get_tool_manifest()
                prompt_sections.append(tool_manifest)

                prompt_sections.append(
                    "RESPONSE REQUIREMENTS:\n"
                    "- You may use tools if needed by outputting: <|channel|>commentary<|message|>{\"tool\": \"tool_name\", \"args\": {...}}\n"
                    "- OR respond directly with natural conversational text\n"
                    "- Do NOT mix tool calls with natural text\n"
                    "- If using a tool, output ONLY the tool call syntax\n"
                    "- If answering directly, use ONLY natural English\n"
                    "- Stay dry, concise, and direct.\n"
                    "- Lead with the actionable answer before elaborating.\n"
                    "- If recommending verification or research, make it explicit."
                )

                prompt_sections.append(f"User query: {user_input}")

                final_prompt = "\n\n".join(filter(None, prompt_sections))
                render_debug['prompt'] = final_prompt

                # Week 6+7: Debug logging for prompt length
                print(f"✨ Final prompt built: {len(final_prompt)} chars (Week 7 architecture)", flush=True)
                print(f"   📊 Breakdown: base={len(system_prompt if system_prompt else '')}, "
                      f"conv_ctx={len(conversation_context)}, "
                      f"semantic={len(str(semantic_results))}, "
                      f"emotion={'yes' if emotion_result else 'no'}, "
                      f"research={'yes' if research_context else 'no'}", flush=True)

                # Debug: Show actual prompt being sent to LLM
                print(f"🔍 FULL PROMPT SENT TO LLM:\n{final_prompt[:500]}...\n", flush=True)

                # Phase 3B Week 3: Use tool orchestrator
                print("🔧 Checking for tool calls...", flush=True)
                
                # Create LLM generator wrapper for orchestrator
                def orchestrator_llm_gen(context):
                    # Simple: just call LLM with the final prompt
                    if hasattr(self.llm, 'complete'):
                        return self.llm.complete(final_prompt, tone=tone)
                    else:
                        return self.llm.generate(final_prompt)
                
                # Run orchestrator (sync wrapper for async)
                orchestrated_response = asyncio.run(
                    self.tool_orchestrator.orchestrate(
                        initial_prompt=user_input,
                        llm_generator=orchestrator_llm_gen,
                        conversation_context=[]
                    )
                )

                render_debug['raw'] = orchestrated_response
                return orchestrated_response

            final_response = chat_respond(actual_command, generator=llm_generator)

            if render_debug.get('raw'):
                print(f"🤖 Base response: {render_debug['raw'][:100]}...")

            # Phase 2: Post-process response with personality (only for treatment group)
            personality_adjustments = []
            if not is_control:
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
            else:
                print("🧪 A/B Test: Skipping response post-processing (control group)")

            # Step 6: Add financial disclaimer if needed (in Penny's style)
            if financial_topic:
                # Check if we already have a disclaimer
                if "disclaimer" not in final_response.lower() and "financial advice" not in final_response.lower():
                    penny_disclaimer = (
                        "\n\nQuick note: I'm sharing general information here, not financial advice. "
                        "Talk to a licensed professional before making money moves."
                    )
                    final_response = sanitize_output(final_response + penny_disclaimer)

            # Step 8: Store in memory (WEEK 7: Dual-save architecture)
            try:
                print("💾 Attempting to save conversation to memory (Week 7 dual-save)...", flush=True)

                # Build enhanced metadata with ALL conversation data
                # WEEK 7: All metadata now stored in semantic memory (single source of truth)
                enhanced_metadata = {
                    "research_used": research_required,
                    "financial_topic": financial_topic,
                    "emotion": emotion_result.primary_emotion,
                    "emotion_confidence": emotion_result.confidence,
                    "sentiment": emotion_result.sentiment,
                    "sentiment_score": emotion_result.sentiment_score,
                    "ab_test_group": group,
                    "tools_used": [],  # TODO: Track tool usage from orchestrator
                    "response_time_ms": int((time.time() - start_time) * 1000)
                }

                # WEEK 7: Removed base_memory and enhanced_memory saves (redundant)
                # OLD: self.base_memory.add_conversation_turn(...) - REMOVED
                # OLD: self.enhanced_memory.process_conversation_turn(...) - REMOVED

                # WEEK 7: Generate turn_id for tracking
                import uuid
                turn_id = str(uuid.uuid4())

                # SAVE 1: Context Manager (in-memory cache only, NO persistence)
                self.context_manager.add_turn(
                    user_input=actual_command,
                    assistant_response=final_response,
                    metadata=enhanced_metadata
                )
                print(f"💬 Context Manager: Cached turn (in-memory only)", flush=True)

                # SAVE 2: Semantic Memory (ONLY persistent store)
                self.semantic_memory.add_conversation_turn(
                    user_input=actual_command,
                    assistant_response=final_response,
                    turn_id=turn_id,
                    context=enhanced_metadata  # Includes encrypted emotions/sentiment
                )
                print(f"🧠 Semantic Memory: Turn {turn_id[:8]}... saved with encryption", flush=True)

                # Update personality tracking from this conversation
                self._update_personality_from_conversation(actual_command, final_response, turn_id)
                print("✅ Conversation saved (Week 7 dual-save: Context cache + Semantic persistent)", flush=True)

                # Week 10: Hebbian Learning (with safety checks)
                if self.hebbian and self._is_safe_to_learn(actual_command, enhanced_metadata):
                    try:
                        hebbian_result = self.hebbian.process_conversation_turn(
                            user_message=actual_command,
                            assistant_response=final_response,
                            context={
                                'formality': enhanced_metadata.get('formality', 0.5),
                                'technical_depth': enhanced_metadata.get('technical_depth', 0.5),
                                'emotion': enhanced_metadata.get('emotion'),
                                'sentiment': enhanced_metadata.get('sentiment')
                            },
                            active_dimensions=self._get_personality_state_for_learning(),
                            session_id=turn_id
                        )
                        logger.debug(f"Hebbian learning: staging={hebbian_result['staging_count']}, "
                                   f"permanent={hebbian_result['permanent_count']}, "
                                   f"latency={hebbian_result['latency_ms']:.1f}ms")
                        print(f"🧠 Hebbian Learning: {hebbian_result['staging_count']} staging, "
                              f"{hebbian_result['permanent_count']} permanent patterns", flush=True)
                    except Exception as heb_e:
                        # Don't break response if Hebbian learning fails
                        logger.error(f"Hebbian learning error (non-fatal): {heb_e}")
                elif self.hebbian:
                    logger.debug("Hebbian learning skipped: safety check failed")

                # Week 8: Mark emotional follow-up if we referenced past emotion
                if check_in_thread and self._response_references_emotion(final_response, check_in_thread):
                    self.emotional_continuity.mark_followed_up(check_in_thread, turn_id)
                    logger.info(f"✅ Marked emotional follow-up for {check_in_thread.turn_id}")

                # Week 8: Check if snapshot needed
                stats = self.semantic_memory.get_stats()
                conversation_count = stats.get('total_conversations', 0)
                if self.personality_snapshots.should_snapshot(conversation_count):
                    try:
                        personality_state = self.personality_tracker.get_personality_state()
                        emotional_threads = [t.to_dict() for t in self.emotional_continuity.threads]

                        snapshot = self.personality_snapshots.create_snapshot(
                            personality_state=personality_state,
                            emotional_threads=emotional_threads,
                            conversation_count=conversation_count
                        )
                        logger.info(f"📸 Created personality snapshot v{snapshot.version}")
                    except Exception as snap_e:
                        logger.warning(f"Snapshot creation failed: {snap_e}")

                # Week 8: Apply forgetting mechanism (every 10 conversations)
                if conversation_count % 10 == 0:
                    self.emotional_continuity.threads = self.forgetting_mechanism.apply_decay(
                        self.emotional_continuity.threads
                    )
                    logger.info(f"🧹 Applied forgetting mechanism ({conversation_count} conversations)")

            except Exception as e:
                import traceback
                print(f"⚠️ Memory storage failed: {e}", flush=True)
                print(f"⚠️ Traceback: {traceback.format_exc()}", flush=True)

            # Step 9: Record A/B test metrics
            try:
                conversation_length = time.time() - start_time
                message_count = 2  # user + assistant
                user_message_length = len(actual_command)

                # Detect quality indicators in user message
                user_lower = actual_command.lower()
                positive_indicators = sum([
                    'thank' in user_lower,
                    'great' in user_lower,
                    'helpful' in user_lower,
                    'perfect' in user_lower,
                    'exactly' in user_lower,
                    'awesome' in user_lower,
                    'excellent' in user_lower
                ])

                negative_indicators = sum([
                    'confus' in user_lower,
                    'wrong' in user_lower,
                    'not help' in user_lower,
                    'unclear' in user_lower,
                    'incorrect' in user_lower,
                    'bad' in user_lower
                ])

                # Record metrics
                metrics = ABTestMetrics(
                    conversation_id=conversation_id,
                    user_id=user_id,
                    group="control" if is_control else "treatment",
                    timestamp=datetime.now().isoformat(),
                    conversation_length_seconds=conversation_length,
                    message_count=message_count,
                    user_message_length_avg=user_message_length,
                    user_corrections=0,  # Could be detected from follow-up messages
                    follow_up_questions=1 if '?' in actual_command else 0,
                    positive_indicators=positive_indicators,
                    negative_indicators=negative_indicators
                )

                self.ab_test.record_metrics(metrics)
                logger.info(f"📊 A/B metrics recorded: {group} group")
            except Exception as e:
                logger.error(f"Failed to record A/B test metrics: {e}")

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
            try:
                newly_achieved = self.milestone_tracker.check_milestones(user_id="default")

                if newly_achieved:
                    print("\n" + "="*60)
                    print("🎉 NEW ACHIEVEMENT UNLOCKED!")
                    print("="*60)
                    for milestone in newly_achieved:
                        print(f"   {milestone.icon} {milestone.name}")
                        print(f"      {milestone.description}")
                    print("="*60 + "\n")
            except Exception as e:
                logger.error(f"Error checking milestones: {e}")

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

    def _response_references_emotion(self, response: str, thread) -> bool:
        """
        Check if Penny's response references the emotional thread.

        Simple heuristic: Does response mention the emotion or context?
        """
        response_lower = response.lower()

        # Check for emotion mention
        if thread.emotion.lower() in response_lower:
            return True

        # Check for context keywords
        context_words = thread.context.lower().split()[:5]  # First 5 words
        for word in context_words:
            if len(word) > 4 and word in response_lower:  # Only meaningful words
                return True

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
