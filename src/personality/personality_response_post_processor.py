#!/usr/bin/env python3
"""
Personality Response Post-Processor
Applies learned personality preferences to LLM responses after generation

Post-processing ensures personality consistency even when LLM doesn't follow prompts perfectly.
This is the "personality guard" that catches violations and applies learned preferences.
"""

import asyncio
import re
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from personality_tracker import PersonalityTracker
from slang_vocabulary_tracker import SlangVocabularyTracker


class PersonalityResponsePostProcessor:
    """
    Post-processes LLM responses to apply learned personality preferences

    Applies:
    1. ABSOLUTE PROHIBITIONS enforcement (removes violations)
    2. Vocabulary substitutions (replaces terms with user-preferred alternatives)
    3. Length adjustments (truncates or expands based on preference)
    4. Formality adjustments (adds/removes contractions, adjusts tone)
    5. Technical depth adjustments (simplifies or adds detail)
    """

    def __init__(
        self,
        personality_tracker: Optional[PersonalityTracker] = None,
        slang_tracker: Optional[SlangVocabularyTracker] = None,
        confidence_threshold: float = 0.65,
        db_path: str = "data/personality_tracking.db"
    ):
        """
        Initialize response post-processor

        Args:
            personality_tracker: Tracks personality dimensions
            slang_tracker: Tracks vocabulary preferences
            confidence_threshold: Minimum confidence to apply learnings
            db_path: Path to personality tracking database
        """
        self.personality_tracker = personality_tracker or PersonalityTracker(db_path)
        self.slang_tracker = slang_tracker or SlangVocabularyTracker(db_path)
        self.confidence_threshold = confidence_threshold
        self.db_path = db_path

        # Prohibited patterns (ABSOLUTE PROHIBITIONS)
        self.prohibited_patterns = {
            'multiple_exclamations': r'!{2,}',  # !! or !!!
            'coffee_references': r'\b(brew|caffeine|espresso|latte|cappuccino|java\b(?! programming))',
            'asterisk_actions': r'\*[^*]+\*',  # *dramatic sigh*, etc.
            'excessive_caps': r'\b[A-Z]{4,}\b(?!(HTML|CSS|JSON|API|REST|HTTP|CRUD|SQL|AWS|USA))',  # Caps words except acronyms
            'weird_nicknames': r'\b(data-daddy|code-ninja|tech-wizard|pixel-pusher|byte-master)\b',
            'forced_casual': r'\b(cat meme binge|internet rabbit hole|epic quest)\b'
        }

        # Cheerful intensifiers to remove or replace
        self.cheerful_intensifiers = {
            'super': 'very',
            'totally': 'completely',
            'really really': 'very',
            'absolutely amazing': 'effective',
            'incredibly': 'very',
            'fantastically': 'well'
        }

        # Formality adjustment patterns
        self.contractions = {
            'do not': "don't",
            'does not': "doesn't",
            'did not': "didn't",
            'will not': "won't",
            'would not': "wouldn't",
            'could not': "couldn't",
            'should not': "shouldn't",
            'is not': "isn't",
            'are not': "aren't",
            'was not': "wasn't",
            'were not': "weren't",
            'have not': "haven't",
            'has not': "hasn't",
            'had not': "hadn't",
            'cannot': "can't",
            'it is': "it's",
            'that is': "that's",
            'there is': "there's",
            'you are': "you're",
            'you have': "you've",
            'i am': "I'm"
        }

    async def process_response(
        self,
        response: str,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Post-process LLM response with personality adjustments

        Args:
            response: Raw LLM response
            context: Conversation context

        Returns:
            Processed response with personality adjustments applied
        """
        context = context or {}

        # Get personality state
        personality_state = await self.personality_tracker.get_current_personality_state()

        # Step 1: Enforce ABSOLUTE PROHIBITIONS (always applied)
        response = self._enforce_prohibitions(response)

        # Step 2: Apply vocabulary substitutions (high-confidence only)
        response = await self._apply_vocabulary_preferences(response)

        # Step 3: Apply formality adjustments
        response = self._apply_formality_adjustments(response, personality_state)

        # Step 4: Apply length adjustments
        response = self._apply_length_adjustments(response, personality_state)

        # Step 5: Final cleanup
        response = self._final_cleanup(response)

        return response

    def _enforce_prohibitions(self, response: str) -> str:
        """Enforce ABSOLUTE PROHIBITIONS by removing/replacing violations"""
        original = response

        # Remove multiple exclamation marks (keep maximum one)
        response = re.sub(r'!{2,}', '!', response)

        # Remove coffee metaphors
        response = re.sub(
            r'\b(brew|brewing|caffeine|espresso|latte|cappuccino)(?!\s+programming)\b',
            '',
            response,
            flags=re.IGNORECASE
        )

        # Remove asterisk actions
        response = re.sub(r'\*[^*]+\*', '', response)

        # Replace excessive caps (except known acronyms)
        def replace_caps(match):
            word = match.group(0)
            # Keep technical acronyms
            acronyms = {'HTML', 'CSS', 'JSON', 'API', 'REST', 'HTTP', 'CRUD', 'SQL',
                       'AWS', 'GCP', 'USA', 'UK', 'NASA', 'NATO', 'ASAP', 'FAQ'}
            if word in acronyms:
                return word
            return word.capitalize()

        response = re.sub(r'\b[A-Z]{4,}\b', replace_caps, response)

        # Remove weird nicknames
        for pattern_name, pattern in self.prohibited_patterns.items():
            if pattern_name in ('multiple_exclamations', 'excessive_caps', 'asterisk_actions', 'coffee_references'):
                continue  # Already handled above
            response = re.sub(pattern, '', response, flags=re.IGNORECASE)

        # Replace cheerful intensifiers
        for cheerful, replacement in self.cheerful_intensifiers.items():
            response = re.sub(
                r'\b' + re.escape(cheerful) + r'\b',
                replacement,
                response,
                flags=re.IGNORECASE
            )

        # Clean up any double spaces created by removals
        response = re.sub(r'\s{2,}', ' ', response).strip()

        return response

    async def _apply_vocabulary_preferences(self, response: str) -> str:
        """Apply learned vocabulary preferences (substitute preferred terms)"""
        # Get terminology preferences from database
        terminology_prefs = await self.slang_tracker.get_terminology_preferences(
            min_confidence=self.confidence_threshold
        )

        for pref in terminology_prefs:
            preferred_term = pref.get('preferred_term', '')
            alternative_terms = pref.get('alternative_terms', [])

            # Replace alternative terms with preferred term
            for alt_term in alternative_terms:
                if alt_term and preferred_term:
                    # Use word boundaries for whole-word replacement
                    pattern = r'\b' + re.escape(alt_term) + r'\b'
                    response = re.sub(pattern, preferred_term, response, flags=re.IGNORECASE)

        return response

    def _apply_formality_adjustments(
        self,
        response: str,
        personality_state: Dict
    ) -> str:
        """Apply formality adjustments based on learned preferences"""
        formality_dim = personality_state.get('communication_formality')
        if not formality_dim or formality_dim.confidence < self.confidence_threshold:
            return response  # No adjustment

        formality_value = float(formality_dim.current_value)

        # If user prefers casual (< 0.4), add contractions
        if formality_value < 0.4:
            for formal, casual in self.contractions.items():
                # Case-insensitive replacement with proper capitalization
                response = re.sub(
                    r'\b' + re.escape(formal) + r'\b',
                    casual,
                    response,
                    flags=re.IGNORECASE
                )

        # If user prefers formal (> 0.7), remove contractions
        elif formality_value > 0.7:
            # Expand contractions
            expansion_map = {v: k for k, v in self.contractions.items()}
            for contraction, expansion in expansion_map.items():
                response = re.sub(
                    r'\b' + re.escape(contraction) + r'\b',
                    expansion,
                    response,
                    flags=re.IGNORECASE
                )

        return response

    def _apply_length_adjustments(
        self,
        response: str,
        personality_state: Dict
    ) -> str:
        """Apply response length adjustments based on learned preferences"""
        length_dim = personality_state.get('response_length_preference')
        if not length_dim or length_dim.confidence < self.confidence_threshold:
            return response  # No adjustment

        length_pref = str(length_dim.current_value)

        # Count sentences
        sentences = re.split(r'[.!?]+', response)
        sentences = [s.strip() for s in sentences if s.strip()]
        sentence_count = len(sentences)

        # Apply adjustments based on preference
        if length_pref == 'brief' and sentence_count > 3:
            # Keep first 2-3 sentences for brief preference
            response = '. '.join(sentences[:3]) + '.'

        elif length_pref == 'comprehensive' and sentence_count < 3:
            # Add a follow-up suggestion for comprehensive preference
            response += " Ask if you'd like more details or examples."

        return response

    def _final_cleanup(self, response: str) -> str:
        """Final cleanup pass to ensure quality"""
        # Remove excessive whitespace
        response = re.sub(r'\s+', ' ', response).strip()

        # Ensure proper sentence endings
        if response and response[-1] not in '.!?':
            response += '.'

        # Remove any leftover double punctuation
        response = re.sub(r'([.!?])\1+', r'\1', response)

        # Clean up spacing around punctuation
        response = re.sub(r'\s+([,.!?;:])', r'\1', response)
        response = re.sub(r'([,.!?;:])\s*([,.!?;:])', r'\1\2', response)

        return response


# Async convenience function
async def process_response_with_personality(
    response: str,
    context: Optional[Dict[str, Any]] = None,
    db_path: str = "data/personality_tracking.db"
) -> str:
    """
    Convenience function to post-process response with personality

    Usage:
        processed = await process_response_with_personality(
            response="original LLM response",
            context={'topic': 'programming'}
        )
    """
    processor = PersonalityResponsePostProcessor(db_path=db_path)
    return await processor.process_response(response, context)


# Synchronous wrapper
def process_response_with_personality_sync(
    response: str,
    context: Optional[Dict[str, Any]] = None,
    db_path: str = "data/personality_tracking.db"
) -> str:
    """
    Synchronous wrapper for process_response_with_personality

    Usage:
        processed = process_response_with_personality_sync(
            response="original LLM response"
        )
    """
    return asyncio.run(process_response_with_personality(response, context, db_path))
