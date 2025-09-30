#!/usr/bin/env python3
"""
Personality-Aware Response Generator
Adapts Penny's responses based on learned personality dimensions
"""

import re
import asyncio
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass

from personality_tracker import PersonalityTracker, PersonalityDimension
from enhanced_personality_learning import EnhancedPersonalityLearning, PersonalityAdaptation

@dataclass
class ResponseAdaptation:
    """Represents an adaptation applied to a response"""
    dimension: str
    adaptation_type: str
    original_text: str
    adapted_text: str
    confidence: float
    reason: str

@dataclass
class AdaptedResponse:
    """Complete adapted response with metadata"""
    original_response: str
    adapted_response: str
    adaptations_applied: List[ResponseAdaptation]
    personality_state_used: Dict[str, Any]
    adaptation_confidence: float

class PersonalityAwareResponseGenerator:
    """
    Modifies Penny's responses based on learned personality preferences
    Applies adaptations for formality, technical depth, humor style, length, etc.
    """

    def __init__(self, personality_tracker: PersonalityTracker):
        self.tracker = personality_tracker

        # Response adaptation rules
        self.adaptation_rules = {
            'communication_formality': {
                'high_threshold': 0.7,
                'low_threshold': 0.3,
                'adaptations': ['formality_language', 'sentence_structure', 'politeness_level']
            },
            'technical_depth_preference': {
                'high_threshold': 0.7,
                'low_threshold': 0.3,
                'adaptations': ['technical_detail', 'jargon_level', 'example_complexity']
            },
            'humor_style_preference': {
                'adaptations': ['humor_injection', 'wit_style', 'playfulness_level']
            },
            'response_length_preference': {
                'adaptations': ['content_expansion', 'detail_level', 'conciseness']
            },
            'conversation_pace_preference': {
                'high_threshold': 0.7,
                'low_threshold': 0.3,
                'adaptations': ['energy_level', 'response_speed', 'enthusiasm']
            },
            'proactive_suggestions': {
                'high_threshold': 0.6,
                'low_threshold': 0.4,
                'adaptations': ['suggestion_injection', 'follow_up_questions']
            },
            'emotional_support_style': {
                'adaptations': ['empathy_level', 'solution_focus', 'encouragement_style']
            }
        }

        # Language patterns for different styles
        self.language_patterns = {
            'formal': {
                'contractions': {
                    "can't": "cannot", "won't": "will not", "it's": "it is", "you're": "you are",
                    "we're": "we are", "I'm": "I am", "that's": "that is", "there's": "there is",
                    "here's": "here is", "what's": "what is", "who's": "who is", "where's": "where is"
                },
                'politeness_additions': [
                    "I'd be happy to help with that.",
                    "Please let me know if you need any clarification.",
                    "I hope this information proves useful.",
                    "Thank you for your question."
                ],
                'formal_transitions': ["Furthermore", "Additionally", "Moreover", "However", "Nevertheless"]
            },
            'casual': {
                'formal_to_casual': {
                    "however": "but", "furthermore": "also", "nevertheless": "still",
                    "additionally": "plus", "therefore": "so"
                },
                'casual_additions': ["by the way", "oh", "actually", "you know", "honestly"],
                'casual_endings': ["Hope that helps!", "Let me know if you need more!", "Does that make sense?"]
            }
        }

        # Technical depth patterns
        self.technical_patterns = {
            'simplify': {
                'replacements': {
                    'algorithm': 'method',
                    'implementation': 'way to build it',
                    'optimization': 'making it faster',
                    'instantiate': 'create',
                    'parameters': 'settings',
                    'configuration': 'setup'
                },
                'explanation_style': 'analogies'
            },
            'enhance': {
                'additions': [
                    'implementation details',
                    'code examples',
                    'architectural considerations',
                    'performance implications'
                ]
            }
        }

        # Humor style patterns
        self.humor_styles = {
            'dry': {
                'patterns': ['understated', 'deadpan', 'subtle'],
                'markers': ['apparently', 'clearly', 'obviously', 'naturally']
            },
            'playful': {
                'patterns': ['emoji', 'exclamation', 'wordplay'],
                'markers': ['😊', '✨', '🎉', 'fun fact', 'plot twist']
            },
            'roasting': {
                'patterns': ['gentle_teasing', 'challenge', 'competitive'],
                'markers': ['sure you can handle', 'if you think you\'re ready', 'brave enough']
            },
            'tech_humor': {
                'patterns': ['programming_jokes', 'tech_references', 'nerd_humor'],
                'markers': ['bug feature', 'works on my machine', 'rubber duck']
            },
            'dad_jokes': {
                'patterns': ['puns', 'obvious_jokes', 'groan_worthy'],
                'markers': ['speaking of', 'you could say', 'get it?']
            }
        }

    async def generate_response(self, user_message: str, base_response: str,
                              context: Dict[str, Any]) -> AdaptedResponse:
        """
        Modify response based on learned personality preferences
        """
        # Get current personality state
        personality_state = await self.tracker.get_current_personality_state()

        # Determine which adaptations to apply
        adaptations_to_apply = await self._determine_adaptations(personality_state, context)

        # Apply adaptations sequentially
        adapted_response = base_response
        adaptations_applied = []

        for adaptation in adaptations_to_apply:
            adaptation_result = await self._apply_adaptation(
                adapted_response, adaptation, personality_state, context
            )

            if adaptation_result:
                adapted_response = adaptation_result.adapted_text
                adaptations_applied.append(adaptation_result)

        # Calculate overall adaptation confidence
        adaptation_confidence = self._calculate_adaptation_confidence(adaptations_applied, personality_state)

        return AdaptedResponse(
            original_response=base_response,
            adapted_response=adapted_response,
            adaptations_applied=adaptations_applied,
            personality_state_used={name: dim.current_value for name, dim in personality_state.items()},
            adaptation_confidence=adaptation_confidence
        )

    async def _determine_adaptations(self, personality_state: Dict[str, PersonalityDimension],
                                   context: Dict[str, Any]) -> List[str]:
        """Determine which adaptations should be applied based on personality state"""
        adaptations = []

        for dimension_name, dimension in personality_state.items():
            if dimension.confidence < 0.5:
                continue  # Skip low-confidence dimensions

            rules = self.adaptation_rules.get(dimension_name, {})

            if dimension.value_type == 'continuous':
                value = float(dimension.current_value)
                high_threshold = rules.get('high_threshold', 0.7)
                low_threshold = rules.get('low_threshold', 0.3)

                if value > high_threshold:
                    adaptations.extend([f"{dimension_name}_high_{a}" for a in rules.get('adaptations', [])])
                elif value < low_threshold:
                    adaptations.extend([f"{dimension_name}_low_{a}" for a in rules.get('adaptations', [])])

            elif dimension.value_type == 'categorical':
                adaptations.extend([f"{dimension_name}_{dimension.current_value}_{a}"
                                 for a in rules.get('adaptations', [])])

        return adaptations

    async def _apply_adaptation(self, response: str, adaptation: str,
                              personality_state: Dict[str, PersonalityDimension],
                              context: Dict[str, Any]) -> Optional[ResponseAdaptation]:
        """Apply a specific adaptation to the response"""
        original_response = response

        # Parse adaptation string (e.g., "communication_formality_high_formality_language")
        parts = adaptation.split('_')
        if len(parts) < 3:
            return None

        dimension = '_'.join(parts[:2])  # e.g., "communication_formality"
        level = parts[2]  # e.g., "high", "low", or specific value
        adaptation_type = '_'.join(parts[3:])  # e.g., "formality_language"

        # Apply specific adaptation based on type
        adapted_text = response

        if 'formality_language' in adaptation_type:
            adapted_text = await self._adapt_formality_language(response, level)
        elif 'technical_detail' in adaptation_type:
            adapted_text = await self._adapt_technical_detail(response, level, context)
        elif 'humor_injection' in adaptation_type:
            adapted_text = await self._adapt_humor_style(response, level, context)
        elif 'content_expansion' in adaptation_type:
            adapted_text = await self._adapt_response_length(response, level, context)
        elif 'energy_level' in adaptation_type:
            adapted_text = await self._adapt_conversation_pace(response, level)
        elif 'suggestion_injection' in adaptation_type:
            adapted_text = await self._adapt_proactive_suggestions(response, level, context)
        elif 'empathy_level' in adaptation_type:
            adapted_text = await self._adapt_emotional_support(response, level, context)

        # Return adaptation result if text was changed
        if adapted_text != original_response:
            dimension_obj = personality_state.get(dimension)
            confidence = dimension_obj.confidence if dimension_obj else 0.5

            return ResponseAdaptation(
                dimension=dimension,
                adaptation_type=adaptation_type,
                original_text=original_response,
                adapted_text=adapted_text,
                confidence=confidence,
                reason=f"Applied {adaptation_type} based on {dimension} preference"
            )

        return None

    async def _adapt_formality_language(self, response: str, level: str) -> str:
        """Adapt formality level of the response language"""
        if level == "high":
            # Make more formal
            adapted = response

            # Replace contractions
            for contraction, expansion in self.language_patterns['formal']['contractions'].items():
                adapted = adapted.replace(contraction, expansion)

            # Add polite language if not present
            if not any(polite in adapted.lower() for polite in ['please', 'thank you', 'appreciate']):
                polite_addition = self.language_patterns['formal']['politeness_additions'][0]
                adapted = f"{polite_addition} {adapted}"

            # Replace casual connectors with formal ones
            adapted = re.sub(r'\bbut\b', 'however', adapted)
            adapted = re.sub(r'\bso\b', 'therefore', adapted)

            return adapted

        elif level == "low":
            # Make more casual
            adapted = response

            # Replace formal words with casual equivalents
            for formal, casual in self.language_patterns['casual']['formal_to_casual'].items():
                adapted = re.sub(rf'\b{formal}\b', casual, adapted, flags=re.IGNORECASE)

            # Add casual markers
            if not any(casual in adapted.lower() for casual in ['hey', 'oh', 'by the way']):
                casual_addition = self.language_patterns['casual']['casual_additions'][0]
                adapted = f"{casual_addition}, {adapted.lower()}"

            # Add casual ending if formal ending detected
            if any(formal_end in adapted for formal_end in ['sincerely', 'regards', 'thank you']):
                casual_ending = self.language_patterns['casual']['casual_endings'][0]
                adapted = f"{adapted} {casual_ending}"

            return adapted

        return response

    async def _adapt_technical_detail(self, response: str, level: str, context: Dict[str, Any]) -> str:
        """Adapt technical depth of the response"""
        if level == "low":
            # Simplify technical language
            adapted = response

            for technical, simple in self.technical_patterns['simplify']['replacements'].items():
                adapted = re.sub(rf'\b{technical}\b', simple, adapted, flags=re.IGNORECASE)

            # Add analogies if explaining complex concepts
            if any(complex_word in adapted.lower() for complex_word in ['system', 'process', 'method']):
                adapted += " (Think of it like organizing your files on your computer - same idea!)"

            return adapted

        elif level == "high":
            # Add technical detail
            adapted = response

            # Look for opportunities to add technical detail
            if 'algorithm' in adapted.lower():
                adapted += " For implementation details, you'd typically use a recursive approach with memoization to optimize performance."

            if 'database' in adapted.lower():
                adapted += " Consider indexing strategies and query optimization for production use."

            if 'function' in adapted.lower():
                adapted += " Remember to handle edge cases and consider time/space complexity."

            return adapted

        return response

    async def _adapt_humor_style(self, response: str, style: str, context: Dict[str, Any]) -> str:
        """Adapt humor style in the response"""
        if style not in self.humor_styles:
            return response

        humor_config = self.humor_styles[style]
        adapted = response

        if style == "playful":
            # Add playful elements
            if not any(emoji in adapted for emoji in ['😊', '✨', '🎉']):
                adapted += " ✨"

            # Add playful language
            if "here's" in adapted.lower():
                adapted = adapted.replace("here's", "here's the fun part:")

        elif style == "dry":
            # Add subtle dry humor
            if "obviously" not in adapted.lower() and "clearly" not in adapted.lower():
                adapted = f"Clearly, {adapted.lower()}"

        elif style == "tech_humor":
            # Add programming humor
            if "error" in adapted.lower():
                adapted += " (It's not a bug, it's a feature! 😏)"

            if "works" in adapted.lower():
                adapted = adapted.replace("works", "works (on my machine)")

        elif style == "roasting":
            # Add gentle teasing
            if "can" in adapted and "you" in adapted:
                adapted = adapted.replace("you can", "if you think you can handle it, you can")

        return adapted

    async def _adapt_response_length(self, response: str, preference: str, context: Dict[str, Any]) -> str:
        """Adapt response length based on preference"""
        if preference == "brief":
            # Shorten response
            sentences = response.split('. ')
            if len(sentences) > 2:
                # Keep first 2 sentences and add summary
                adapted = '. '.join(sentences[:2]) + '. '
                adapted += "Want more details on any part?"
                return adapted

        elif preference == "comprehensive":
            # Expand response with more detail
            adapted = response

            # Add examples if explaining concepts
            if any(concept in adapted.lower() for concept in ['how', 'what', 'why']):
                adapted += "\n\nFor example, if you're working with user data, you'd want to validate inputs, hash passwords, and use HTTPS for transmission."

            # Add follow-up questions
            adapted += "\n\nWould you like me to dive deeper into any specific aspect?"

            return adapted

        elif preference == "detailed":
            # Add moderate detail
            adapted = response

            if "here's how" in adapted.lower():
                adapted += " I'll break this down step by step:"

            return adapted

        return response

    async def _adapt_conversation_pace(self, response: str, level: str) -> str:
        """Adapt conversation energy and pace"""
        if level == "high":
            # Increase energy
            adapted = response

            # Add exclamation marks sparingly
            if not any(punct in adapted for punct in ['!', '?']):
                adapted = adapted.rstrip('.') + '!'

            # Add energetic language
            if "let's" not in adapted.lower():
                adapted = f"Let's dive in! {adapted}"

            # Add momentum
            adapted += " Ready to keep going?"

            return adapted

        elif level == "low":
            # Slow down, be more thoughtful
            adapted = response

            # Add thoughtful pauses
            adapted = adapted.replace('. ', '... ')

            # Add contemplative language
            if not any(thoughtful in adapted.lower() for thoughtful in ['consider', 'think about', 'reflect']):
                adapted = f"Let's think about this carefully. {adapted}"

            return adapted

        return response

    async def _adapt_proactive_suggestions(self, response: str, level: str, context: Dict[str, Any]) -> str:
        """Adapt level of proactive suggestions"""
        if level == "high":
            # Add proactive suggestions
            adapted = response

            # Add related suggestions
            topic = context.get('conversation_topic', 'this')
            adapted += f"\n\nWhile we're on {topic}, you might also want to consider exploring related areas like testing strategies or performance optimization."

            # Add follow-up questions
            adapted += " What would you like to tackle next?"

            return adapted

        elif level == "low":
            # Remove or minimize suggestions, stick to answering what was asked
            adapted = response

            # Remove proactive elements
            adapted = re.sub(r'\n\n(You might also|Consider also|Another option).*', '', adapted)
            adapted = re.sub(r'\s*(What do you think|Want to explore|Should we)\?', '', adapted)

            return adapted

        return response

    async def _adapt_emotional_support(self, response: str, style: str, context: Dict[str, Any]) -> str:
        """Adapt emotional support style"""
        if style == "empathetic":
            # Add empathetic language
            adapted = response

            if any(frustration in context.get('user_message', '').lower()
                   for frustration in ['stuck', 'frustrated', 'confused']):
                adapted = f"I can understand how that might be frustrating. {adapted}"

        elif style == "solution_focused":
            # Focus on practical solutions
            adapted = response

            if "problem" in response.lower() or "issue" in response.lower():
                adapted += " Let's break this down into actionable steps to get you moving forward."

        elif style == "cheerleading":
            # Add encouragement and positivity
            adapted = response

            adapted += " You've got this! 💪"

        elif style == "analytical":
            # Keep it logical and structured
            adapted = response

            if not any(structure in adapted.lower() for structure in ['first', 'step', 'approach']):
                adapted = f"Here's a systematic approach: {adapted}"

        return adapted

    def _calculate_adaptation_confidence(self, adaptations: List[ResponseAdaptation],
                                       personality_state: Dict[str, PersonalityDimension]) -> float:
        """Calculate overall confidence in the adaptations applied"""
        if not adaptations:
            return 0.0

        total_confidence = sum(adaptation.confidence for adaptation in adaptations)
        return min(1.0, total_confidence / len(adaptations))

    async def get_adaptation_preview(self, base_response: str, user_message: str,
                                   context: Dict[str, Any]) -> Dict[str, str]:
        """Preview how response would be adapted for different personality settings"""
        preview = {"original": base_response}

        # Test different personality configurations
        test_configs = {
            "formal_technical": {"communication_formality": 0.9, "technical_depth_preference": 0.8},
            "casual_simple": {"communication_formality": 0.2, "technical_depth_preference": 0.2},
            "playful_medium": {"communication_formality": 0.5, "humor_style_preference": "playful"},
            "brief_energetic": {"response_length_preference": "brief", "conversation_pace_preference": 0.8}
        }

        for config_name, config in test_configs.items():
            # Temporarily simulate personality state
            adapted = base_response

            if "formality" in config:
                level = "high" if config["communication_formality"] > 0.7 else "low"
                adapted = await self._adapt_formality_language(adapted, level)

            if "technical_depth_preference" in config:
                level = "high" if config["technical_depth_preference"] > 0.7 else "low"
                adapted = await self._adapt_technical_detail(adapted, level, context)

            if "humor_style_preference" in config:
                adapted = await self._adapt_humor_style(adapted, config["humor_style_preference"], context)

            if "response_length_preference" in config:
                adapted = await self._adapt_response_length(adapted, config["response_length_preference"], context)

            if "conversation_pace_preference" in config:
                level = "high" if config["conversation_pace_preference"] > 0.7 else "low"
                adapted = await self._adapt_conversation_pace(adapted, level)

            preview[config_name] = adapted

        return preview


if __name__ == "__main__":
    async def main():
        # Test the personality-aware response generator
        tracker = PersonalityTracker()
        generator = PersonalityAwareResponseGenerator(tracker)

        # Test response
        base_response = "I can help you debug your code. Here's how to approach this problem systematically."
        user_message = "I'm stuck on this bug"
        context = {"conversation_topic": "debugging", "user_emotion": "frustrated"}

        print("🎭 Testing Personality-Aware Response Generator")
        print("=" * 50)

        # Test adaptation preview
        print(f"\nBase response: {base_response}")
        print(f"\nAdaptation previews:")

        preview = await generator.get_adaptation_preview(base_response, user_message, context)
        for config, adapted in preview.items():
            print(f"\n{config}: {adapted}")

        # Test actual adaptation with current personality state
        print(f"\nActual adaptation with current personality state:")
        adapted_response = await generator.generate_response(user_message, base_response, context)

        print(f"Original: {adapted_response.original_response}")
        print(f"Adapted: {adapted_response.adapted_response}")
        print(f"Adaptations applied: {len(adapted_response.adaptations_applied)}")

        for adaptation in adapted_response.adaptations_applied:
            print(f"  - {adaptation.dimension}: {adaptation.adaptation_type} (confidence: {adaptation.confidence:.2f})")

        print(f"Overall adaptation confidence: {adapted_response.adaptation_confidence:.2f}")

    asyncio.run(main())