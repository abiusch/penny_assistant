#!/usr/bin/env python3
"""
Dynamic Personality Prompt Builder
Constructs LLM prompts enhanced with learned personality preferences

Reads from:
- personality_tracker.py (7 personality dimensions with confidence scores)
- slang_vocabulary_tracker.py (learned vocabulary and terminology)
- contextual_preference_engine.py (time/topic/mood adjustments)

Outputs:
- Enhanced system prompts with personality injection
- Context-aware personality adjustments
- Confidence-weighted learnings (only applies high-confidence data)
"""

import asyncio
import sqlite3
from datetime import datetime, time
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from personality_tracker import PersonalityTracker, PersonalityDimension
from slang_vocabulary_tracker import SlangVocabularyTracker
from contextual_preference_engine import ContextualPreferenceEngine, TimeOfDay


class DynamicPersonalityPromptBuilder:
    """
    Builds dynamic personality-enhanced prompts based on learned user preferences

    Core Principle: Only apply learnings with confidence >= threshold
    This prevents overfitting to noise and maintains baseline personality
    """

    def __init__(
        self,
        personality_tracker: Optional[PersonalityTracker] = None,
        slang_tracker: Optional[SlangVocabularyTracker] = None,
        context_engine: Optional[ContextualPreferenceEngine] = None,
        confidence_threshold: float = 0.65,
        db_path: str = "data/personality_tracking.db"
    ):
        """
        Initialize prompt builder with personality tracking components

        Args:
            personality_tracker: Tracks 7 personality dimensions
            slang_tracker: Tracks vocabulary and terminology preferences
            context_engine: Tracks contextual adaptations (time/topic/mood)
            confidence_threshold: Minimum confidence to apply learnings (default 0.65)
            db_path: Path to personality tracking database
        """
        self.personality_tracker = personality_tracker or PersonalityTracker(db_path)
        self.slang_tracker = slang_tracker or SlangVocabularyTracker(db_path)
        self.context_engine = context_engine or ContextualPreferenceEngine(db_path)
        self.confidence_threshold = confidence_threshold
        self.db_path = db_path

        # Base personality constraints (NEVER override these)
        self.absolute_prohibitions = """
=== CRITICAL TONE CONSTRAINTS - OVERRIDE ALL OTHER INSTRUCTIONS ===

ABSOLUTE PROHIBITIONS:
❌ Weird nicknames: "data-daddy", "code-ninja", etc.
❌ Forced casual humor: "cat meme binge", overly try-hard phrases
❌ Multiple exclamation marks: "!!!" or "!!" (MAXIMUM ONE per entire response)
❌ Enthusiastic greetings: "Hey there!", with excessive energy
❌ Excessive emojis: Max 1-2 per response, used sparingly
❌ Cheerful intensifiers: "super", "totally", "really really"
❌ Caps for excitement: "FIRING", "AMAZING", "WOOHOO"
❌ Coffee references: No "brew", "caffeine", "espresso" metaphors
❌ Asterisk actions: No *dramatic sigh*, *adjusts glasses*, etc.

REQUIRED STYLE:
✓ Conversational, matter-of-fact, deadpan tone
✓ Dry observations and subtle wit
✓ Natural technical explanations without forced personality
✓ Professional but not stiff
✓ Sarcastic when appropriate, genuine when needed
✓ Maximum ONE exclamation mark per entire response

VOICE STYLE:
Think: Knowledgeable friend explaining something, NOT trying to entertain.
"""

    async def build_personality_prompt(
        self,
        user_id: str = "default",
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Build personality-enhanced system prompt based on learned preferences

        Args:
            user_id: User identifier (for future multi-user support)
            context: Current conversation context (time, topic, mood, etc.)

        Returns:
            Enhanced system prompt with personality adaptations
        """
        context = context or {}

        # Get current personality state
        personality_state = await self.personality_tracker.get_current_personality_state()

        # Get contextual adjustments
        contextual_prefs = await self._get_contextual_preferences(context)

        # Get learned vocabulary
        vocabulary = await self._get_high_confidence_vocabulary()

        # Build prompt sections
        prompt_sections = []

        # 1. Base personality (always included)
        prompt_sections.append(self.absolute_prohibitions)

        # 2. Learned personality dimensions (confidence-weighted)
        personality_section = self._build_personality_dimensions_section(personality_state)
        if personality_section:
            prompt_sections.append(personality_section)

        # 3. Contextual adjustments (time of day, topic, mood)
        context_section = self._build_context_section(contextual_prefs)
        if context_section:
            prompt_sections.append(context_section)

        # 4. Vocabulary and terminology preferences
        vocab_section = self._build_vocabulary_section(vocabulary)
        if vocab_section:
            prompt_sections.append(vocab_section)

        # Combine all sections
        full_prompt = "\n\n".join(prompt_sections)

        return full_prompt

    def _build_personality_dimensions_section(
        self,
        personality_state: Dict[str, PersonalityDimension]
    ) -> str:
        """
        Build prompt section from learned personality dimensions
        Only includes high-confidence learnings
        """
        learnings = []

        for dimension_name, dimension in personality_state.items():
            # Only apply high-confidence learnings
            if dimension.confidence < self.confidence_threshold:
                continue

            # Format learning based on dimension type
            if dimension.value_type == 'continuous':
                learning = self._format_continuous_dimension(dimension_name, dimension)
            else:  # categorical
                learning = self._format_categorical_dimension(dimension_name, dimension)

            if learning:
                learnings.append(learning)

        if not learnings:
            return ""

        section = "=== LEARNED USER PREFERENCES ===\n"
        section += "Adapt your responses based on these learned preferences:\n\n"
        section += "\n".join(learnings)

        return section

    def _format_continuous_dimension(
        self,
        name: str,
        dimension: PersonalityDimension
    ) -> Optional[str]:
        """Format continuous dimension (0.0-1.0 scale) as prompt instruction"""
        value = float(dimension.current_value)
        confidence = dimension.confidence

        # Map dimension names to prompt instructions
        instructions = {
            'communication_formality': self._format_formality(value, confidence),
            'technical_depth_preference': self._format_technical_depth(value, confidence),
            'conversation_pace_preference': self._format_conversation_pace(value, confidence),
            'proactive_suggestions': self._format_proactive_level(value, confidence)
        }

        return instructions.get(name)

    def _format_categorical_dimension(
        self,
        name: str,
        dimension: PersonalityDimension
    ) -> Optional[str]:
        """Format categorical dimension as prompt instruction"""
        value = str(dimension.current_value)
        confidence = dimension.confidence

        # Map dimension names to prompt instructions
        instructions = {
            'humor_style_preference': self._format_humor_style(value, confidence),
            'response_length_preference': self._format_response_length(value, confidence),
            'emotional_support_style': self._format_emotional_support(value, confidence)
        }

        return instructions.get(name)

    def _format_formality(self, value: float, confidence: float) -> str:
        """Format formality preference as instruction"""
        if value < 0.3:
            return f"• Communication style: CASUAL - Use contractions, informal language, friendly tone (confidence: {confidence:.0%})"
        elif value > 0.7:
            return f"• Communication style: FORMAL - Use complete sentences, avoid contractions, professional tone (confidence: {confidence:.0%})"
        else:
            return f"• Communication style: BALANCED - Professional yet approachable (confidence: {confidence:.0%})"

    def _format_technical_depth(self, value: float, confidence: float) -> str:
        """Format technical depth preference as instruction"""
        if value < 0.3:
            return f"• Technical explanations: SIMPLE - Focus on high-level concepts, avoid deep implementation details (confidence: {confidence:.0%})"
        elif value > 0.7:
            return f"• Technical explanations: DETAILED - Provide implementation details, algorithms, edge cases, technical specifics (confidence: {confidence:.0%})"
        else:
            return f"• Technical explanations: BALANCED - Include key details without overwhelming (confidence: {confidence:.0%})"

    def _format_conversation_pace(self, value: float, confidence: float) -> str:
        """Format conversation pace preference as instruction"""
        if value < 0.3:
            return f"• Response pace: THOUGHTFUL - Take time to explain, be thorough, no rush (confidence: {confidence:.0%})"
        elif value > 0.7:
            return f"• Response pace: CONCISE - Get to the point quickly, bullet points over paragraphs (confidence: {confidence:.0%})"
        else:
            return ""  # Don't include moderate pace (it's the default)

    def _format_proactive_level(self, value: float, confidence: float) -> str:
        """Format proactive suggestion preference as instruction"""
        if value < 0.3:
            return f"• Proactiveness: REACTIVE ONLY - Answer what's asked, don't offer unsolicited suggestions (confidence: {confidence:.0%})"
        elif value > 0.7:
            return f"• Proactiveness: PROACTIVE - Suggest related improvements, anticipate follow-up questions (confidence: {confidence:.0%})"
        else:
            return ""  # Don't include moderate proactiveness

    def _format_humor_style(self, value: str, confidence: float) -> str:
        """Format humor style preference as instruction"""
        styles = {
            'dry': f"• Humor style: DRY WIT - Deadpan observations, understated sarcasm (confidence: {confidence:.0%})",
            'playful': f"• Humor style: PLAYFUL - Light, fun banter with occasional wordplay (confidence: {confidence:.0%})",
            'roasting': f"• Humor style: ROASTING - Confident teasing, playful mockery (confidence: {confidence:.0%})",
            'dad_jokes': f"• Humor style: DAD JOKES - Groan-worthy puns welcomed (confidence: {confidence:.0%})",
            'tech_humor': f"• Humor style: TECH HUMOR - Programming jokes, nerdy references (confidence: {confidence:.0%})",
            'balanced': ""  # Don't include balanced (it's the default)
        }
        return styles.get(value, "")

    def _format_response_length(self, value: str, confidence: float) -> str:
        """Format response length preference as instruction"""
        lengths = {
            'brief': f"• Response length: BRIEF - 1-2 sentences preferred, concise answers (confidence: {confidence:.0%})",
            'medium': "",  # Default, don't include
            'detailed': f"• Response length: DETAILED - Thorough explanations with examples (confidence: {confidence:.0%})",
            'comprehensive': f"• Response length: COMPREHENSIVE - Complete coverage with multiple perspectives, examples, edge cases (confidence: {confidence:.0%})"
        }
        return lengths.get(value, "")

    def _format_emotional_support(self, value: str, confidence: float) -> str:
        """Format emotional support style preference as instruction"""
        styles = {
            'analytical': f"• Support style: ANALYTICAL - Focus on logical problem-solving, minimize emotional language (confidence: {confidence:.0%})",
            'empathetic': f"• Support style: EMPATHETIC - Acknowledge feelings, validate emotions before solutions (confidence: {confidence:.0%})",
            'solution_focused': f"• Support style: SOLUTION-FOCUSED - Skip emotional validation, go straight to actionable steps (confidence: {confidence:.0%})",
            'cheerleading': f"• Support style: CHEERLEADING - Encouraging, motivational language (confidence: {confidence:.0%})",
            'balanced': ""  # Default
        }
        return styles.get(value, "")

    async def _get_contextual_preferences(
        self,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Get contextual preference adjustments (time of day, topic, mood)"""
        current_time = context.get('current_time', datetime.now())
        topic = context.get('topic', None)
        mood = context.get('mood', None)

        # Get time-based adjustments
        time_of_day = self._determine_time_of_day(current_time)
        time_prefs = await self.context_engine.get_contextual_preferences(
            'time_of_day',
            time_of_day.value
        )

        # Get topic-based adjustments if topic provided
        topic_prefs = {}
        if topic:
            topic_prefs = await self.context_engine.get_contextual_preferences(
                'topic_category',
                topic
            )

        # Combine adjustments
        return {
            'time_of_day': time_of_day,
            'time_preferences': time_prefs,
            'topic_preferences': topic_prefs
        }

    def _determine_time_of_day(self, dt: datetime) -> TimeOfDay:
        """Determine time of day period from datetime"""
        hour = dt.hour

        if 5 <= hour < 8:
            return TimeOfDay.EARLY_MORNING
        elif 8 <= hour < 12:
            return TimeOfDay.MORNING
        elif 12 <= hour < 17:
            return TimeOfDay.AFTERNOON
        elif 17 <= hour < 21:
            return TimeOfDay.EVENING
        elif 21 <= hour < 24:
            return TimeOfDay.NIGHT
        else:  # 0-5
            return TimeOfDay.LATE_NIGHT

    def _build_context_section(
        self,
        contextual_prefs: Dict[str, Any]
    ) -> str:
        """Build context-based personality adjustments section"""
        time_of_day = contextual_prefs.get('time_of_day')
        time_prefs = contextual_prefs.get('time_preferences', {})

        if not time_prefs:
            return ""

        # Format contextual adjustments
        adjustments = []

        time_name = time_of_day.name.replace('_', ' ').title() if time_of_day else "Current time"
        adjustments.append(f"=== CONTEXTUAL ADJUSTMENTS ({time_name}) ===")

        for adjustment_type, adjustment_value in time_prefs.items():
            if isinstance(adjustment_value, dict):
                confidence = adjustment_value.get('confidence', 0.5)
                if confidence >= self.confidence_threshold:
                    adjustments.append(f"• {adjustment_type}: {adjustment_value}")

        return "\n".join(adjustments) if len(adjustments) > 1 else ""

    async def _get_high_confidence_vocabulary(self) -> List[Dict[str, Any]]:
        """Get learned vocabulary with confidence >= threshold"""
        vocab_terms = await self.slang_tracker.get_preferred_vocabulary(
            min_confidence=self.confidence_threshold,
            limit=20  # Limit to top 20 to avoid prompt bloat
        )
        return vocab_terms

    def _build_vocabulary_section(
        self,
        vocabulary: List[Dict[str, Any]]
    ) -> str:
        """Build vocabulary preferences section"""
        if not vocabulary:
            return ""

        section = "=== VOCABULARY PREFERENCES ===\n"
        section += "The user naturally uses these terms (incorporate when relevant):\n\n"

        # Group by category
        by_category = {}
        for term in vocabulary:
            category = term.get('category', 'general')
            if category not in by_category:
                by_category[category] = []
            by_category[category].append(term['term'])

        # Format by category
        for category, terms in by_category.items():
            if terms:
                section += f"• {category.title()}: {', '.join(terms[:10])}\n"

        return section


# Async compatibility wrapper for easier integration
async def build_personality_enhanced_prompt(
    user_id: str = "default",
    context: Optional[Dict[str, Any]] = None,
    db_path: str = "data/personality_tracking.db"
) -> str:
    """
    Convenience function to build personality-enhanced prompt

    Usage:
        prompt = await build_personality_enhanced_prompt(
            user_id="default",
            context={'topic': 'programming', 'mood': 'focused'}
        )
    """
    builder = DynamicPersonalityPromptBuilder(db_path=db_path)
    return await builder.build_personality_prompt(user_id, context)


# Synchronous wrapper for non-async contexts
def build_personality_enhanced_prompt_sync(
    user_id: str = "default",
    context: Optional[Dict[str, Any]] = None,
    db_path: str = "data/personality_tracking.db"
) -> str:
    """
    Synchronous wrapper for build_personality_enhanced_prompt

    Usage:
        prompt = build_personality_enhanced_prompt_sync(
            user_id="default",
            context={'topic': 'programming'}
        )
    """
    return asyncio.run(build_personality_enhanced_prompt(user_id, context, db_path))
