#!/usr/bin/env python3
"""
Personality-Aware Prompt Builder
Transforms learned personality preferences into dynamic LLM system prompts
"""

import asyncio
from typing import Dict, List, Any, Optional
from dataclasses import dataclass


@dataclass
class PersonalityProfile:
    """Unified personality profile from all tracking systems"""
    # Core dimensions
    formality: float  # 0-1 (0=casual, 1=formal)
    technical_depth: float  # 0-1 (0=simple, 1=technical)
    humor_style: str  # playful, dry, roasting, minimal
    response_length: str  # brief, medium, detailed
    sass_level: float  # 0-1 (0=professional, 1=maximum sass)

    # Learned vocabulary
    user_slang: List[str]  # User's common slang terms
    common_phrases: List[str]  # User's frequent phrases

    # Contextual adjustments
    context_modifiers: Dict[str, float]  # Additional context-based adjustments

    # Confidence
    confidence: float  # Overall confidence in personality data


class PersonalityPromptBuilder:
    """Builds personality-aware system prompts from learned preferences"""

    def __init__(self):
        self.base_identity = "You are Penny, an AI assistant"

    async def get_unified_personality_profile(self) -> PersonalityProfile:
        """Retrieve and combine personality data from all tracking systems"""
        try:
            # Import here to avoid circular dependencies
            from personality_tracker import PersonalityTracker
            from slang_vocabulary_tracker import SlangVocabularyTracker
            from contextual_preference_engine import ContextualPreferenceEngine

            tracker = PersonalityTracker()
            vocab_tracker = SlangVocabularyTracker()
            context_engine = ContextualPreferenceEngine()

            # Get personality dimensions
            personality_state = await tracker.get_current_personality_state()

            # Get vocabulary profile
            vocab_profile = await vocab_tracker.get_user_vocabulary_profile()

            # Extract key data - handle PersonalityDimension objects
            def extract_value(obj, default):
                """Extract numeric value from PersonalityDimension or return default"""
                if obj is None:
                    return default
                if isinstance(obj, (int, float)):
                    return float(obj)
                if hasattr(obj, 'current_value'):
                    return float(obj.current_value)
                return default

            formality = extract_value(personality_state.get('communication_formality'), 0.5)
            technical_depth = extract_value(personality_state.get('technical_depth_preference'), 0.5)

            # Extract string values
            humor_obj = personality_state.get('humor_style_preference', 'playful')
            humor_style = humor_obj.current_value if hasattr(humor_obj, 'current_value') else str(humor_obj)

            length_obj = personality_state.get('response_length_preference', 'medium')
            response_length = length_obj.current_value if hasattr(length_obj, 'current_value') else str(length_obj)

            # Calculate sass level (inverse of formality, boosted by casual slang)
            slang_count = len(vocab_profile.get('slang_vocabulary', []))
            sass_level = (1.0 - formality) * 0.7 + min(slang_count / 20.0, 0.3)
            sass_level = min(sass_level, 1.0)

            # Extract user slang (top 10 most used)
            user_slang = [
                term['term'] for term in vocab_profile.get('most_used_terms', [])[:10]
                if term.get('category') == 'slang'
            ]

            # Get contextual insights
            context_insights = await context_engine.get_contextual_insights()
            context_modifiers = {}

            # Calculate overall confidence - average of dimension confidences
            formality_conf = extract_value(personality_state.get('communication_formality'), 0.5)
            if hasattr(personality_state.get('communication_formality'), 'confidence'):
                formality_conf = personality_state['communication_formality'].confidence

            # Use formality confidence as overall confidence (or average multiple if available)
            confidence = formality_conf if isinstance(formality_conf, float) else 0.3

            return PersonalityProfile(
                formality=formality,
                technical_depth=technical_depth,
                humor_style=humor_style,
                response_length=response_length,
                sass_level=sass_level,
                user_slang=user_slang,
                common_phrases=[],
                context_modifiers=context_modifiers,
                confidence=confidence
            )

        except Exception as e:
            # Graceful degradation - return neutral profile
            print(f"⚠️ Could not load personality profile: {e}")
            return PersonalityProfile(
                formality=0.5,
                technical_depth=0.5,
                humor_style='playful',
                response_length='medium',
                sass_level=0.3,
                user_slang=[],
                common_phrases=[],
                context_modifiers={},
                confidence=0.0
            )

    def build_personality_instructions(self, profile: PersonalityProfile) -> str:
        """Build personality instructions based on learned preferences"""
        instructions = []

        # Only apply if we have confidence
        if profile.confidence < 0.3:
            return ""  # Use base prompt only

        instructions.append("\n🎭 PERSONALITY CONFIGURATION:")

        # Formality instructions
        if profile.formality < 0.3:
            instructions.append(
                "• COMMUNICATION STYLE: Very casual and conversational"
                "\n  - Use contractions (don't, can't, you're, I'm)"
                "\n  - Keep it real and natural, like texting a friend"
                "\n  - Skip formal pleasantries"
            )
        elif profile.formality < 0.5:
            instructions.append(
                "• COMMUNICATION STYLE: Casual but clear"
                "\n  - Use natural, everyday language"
                "\n  - Contractions are fine"
            )
        elif profile.formality < 0.7:
            instructions.append(
                "• COMMUNICATION STYLE: Balanced professional-casual"
                "\n  - Clear and helpful, not stuffy"
            )
        else:
            instructions.append(
                "• COMMUNICATION STYLE: Professional and polished"
                "\n  - Maintain formal tone and complete sentences"
            )

        # Sass level instructions
        if profile.sass_level > 0.7:
            instructions.append(
                "• SASS LEVEL: MAXIMUM 🔥"
                "\n  - Be witty, playful, and sarcastic"
                "\n  - Throw in sass when appropriate"
                "\n  - Don't hold back on personality"
                "\n  - User loves banter and attitude"
            )
        elif profile.sass_level > 0.5:
            instructions.append(
                "• SASS LEVEL: Medium 😏"
                "\n  - Add light humor and personality"
                "\n  - Occasional sass is welcome"
            )
        elif profile.sass_level > 0.3:
            instructions.append(
                "• SASS LEVEL: Mild"
                "\n  - Keep it professional with hints of personality"
            )

        # Humor style instructions
        humor_instructions = {
            'playful': "• HUMOR: Playful and fun, keep it light",
            'dry': "• HUMOR: Dry wit and subtle sarcasm",
            'roasting': "• HUMOR: Roasting mode - user can handle it",
            'minimal': "• HUMOR: Keep humor minimal, focus on being helpful"
        }
        if profile.humor_style in humor_instructions:
            instructions.append(humor_instructions[profile.humor_style])

        # Response length instructions
        length_instructions = {
            'brief': "• LENGTH: Keep responses SHORT and to the point",
            'medium': "• LENGTH: Moderate detail, don't ramble",
            'detailed': "• LENGTH: Comprehensive explanations welcome"
        }
        if profile.response_length in length_instructions:
            instructions.append(length_instructions[profile.response_length])

        # Technical depth instructions
        if profile.technical_depth > 0.7:
            instructions.append(
                "• TECHNICAL DEPTH: High"
                "\n  - User understands technical concepts"
                "\n  - Don't dumb things down"
            )
        elif profile.technical_depth > 0.5:
            instructions.append("• TECHNICAL DEPTH: Moderate - balance clarity with detail")
        else:
            instructions.append("• TECHNICAL DEPTH: Keep it simple and accessible")

        # Learned slang instructions
        if profile.user_slang and profile.formality < 0.5:
            slang_examples = ', '.join(profile.user_slang[:5])
            instructions.append(
                f"• VOCABULARY: User uses casual language"
                f"\n  - Feel free to use terms like: {slang_examples}"
                f"\n  - Match their conversational energy"
            )

        return '\n'.join(instructions)

    async def build_personality_prompt(
        self,
        base_prompt: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Build complete personality-aware system prompt"""

        # Get current personality profile
        profile = await self.get_unified_personality_profile()

        # Start with base identity
        if base_prompt:
            prompt = base_prompt
        else:
            prompt = self.base_identity

        # Add personality instructions if we have confidence
        if profile.confidence >= 0.3:
            personality_instructions = self.build_personality_instructions(profile)
            if personality_instructions:
                prompt += "\n" + personality_instructions
                prompt += f"\n\n💪 Confidence: {profile.confidence:.0%} - These preferences learned from real conversations"

        # Add context-specific adjustments
        if context:
            time_of_day = context.get('time_of_day')
            if time_of_day == 'late_night' and profile.formality < 0.5:
                prompt += "\n• CONTEXT: Late night vibes - keep it chill"

            mood = context.get('mood')
            if mood == 'frustrated' and profile.sass_level > 0.5:
                prompt += "\n• CONTEXT: User seems frustrated - tone down sass, be helpful"

        return prompt

    def get_example_comparison(self) -> Dict[str, str]:
        """Show before/after prompt examples"""
        return {
            'before': "You are PennyGPT, a sassy AI assistant with charm, sarcasm, and helpfulness.",
            'after_casual': """You are Penny, an AI assistant

🎭 PERSONALITY CONFIGURATION:
• COMMUNICATION STYLE: Very casual and conversational
  - Use contractions (don't, can't, you're, I'm)
  - Keep it real and natural, like texting a friend
  - Skip formal pleasantries
• SASS LEVEL: MAXIMUM 🔥
  - Be witty, playful, and sarcastic
  - Throw in sass when appropriate
  - Don't hold back on personality
  - User loves banter and attitude
• HUMOR: Playful and fun, keep it light
• LENGTH: Moderate detail, don't ramble
• TECHNICAL DEPTH: High
  - User understands technical concepts
  - Don't dumb things down
• VOCABULARY: User uses casual language
  - Feel free to use terms like: btw, mofo, dont, ngl, lol
  - Match their conversational energy

💪 Confidence: 85% - These preferences learned from real conversations""",
            'after_formal': """You are Penny, an AI assistant

🎭 PERSONALITY CONFIGURATION:
• COMMUNICATION STYLE: Professional and polished
  - Maintain formal tone and complete sentences
• SASS LEVEL: Mild
  - Keep it professional with hints of personality
• HUMOR: Keep humor minimal, focus on being helpful
• LENGTH: Comprehensive explanations welcome
• TECHNICAL DEPTH: Moderate - balance clarity with detail

💪 Confidence: 65% - These preferences learned from real conversations"""
        }


# Synchronous wrapper for easy integration
def get_personality_prompt(base_prompt: Optional[str] = None, context: Optional[Dict[str, Any]] = None) -> str:
    """Synchronous wrapper - returns personality-aware prompt"""
    builder = PersonalityPromptBuilder()
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If loop is already running, create a task
            import threading
            result = [None]
            def run():
                new_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(new_loop)
                result[0] = new_loop.run_until_complete(
                    builder.build_personality_prompt(base_prompt, context)
                )
                new_loop.close()
            thread = threading.Thread(target=run)
            thread.start()
            thread.join()
            return result[0]
        else:
            return loop.run_until_complete(
                builder.build_personality_prompt(base_prompt, context)
            )
    except RuntimeError:
        # No event loop, create new one
        return asyncio.run(builder.build_personality_prompt(base_prompt, context))


if __name__ == "__main__":
    # Demo the personality prompt builder
    print("🧪 PERSONALITY PROMPT BUILDER DEMO")
    print("=" * 70)

    builder = PersonalityPromptBuilder()
    examples = builder.get_example_comparison()

    print("\n📋 BEFORE (Generic):")
    print(examples['before'])

    print("\n\n✨ AFTER (Casual User):")
    print(examples['after_casual'])

    print("\n\n✨ AFTER (Formal User):")
    print(examples['after_formal'])

    print("\n" + "=" * 70)
    print("This is what makes Penny ACTUALLY sassy! 🔥")
