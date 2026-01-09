"""
Judgment Engine - Detects when to clarify vs answer immediately.

Prevents learning systems from reinforcing patterns based on ambiguous inputs.
"""

from dataclasses import dataclass
from typing import Optional
from enum import Enum

class StakesLevel(Enum):
    """Risk level of the request"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class ResponseStrategy(Enum):
    """How Penny should respond"""
    ANSWER = "answer"      # Proceed with normal answer
    CLARIFY = "clarify"    # Ask clarifying question first
    TOOL = "tool"          # Use tool first
    ESCALATE = "escalate"  # Defer to user

@dataclass
class Decision:
    """
    Structured decision about how to respond to user input.

    Attributes:
        intent: What the user wants (extracted from input)
        stakes_level: Risk level of the request
        clarify_needed: Whether clarification is needed
        clarify_question: The raw question to ask (if needed)
        response_strategy: How Penny should respond
        confidence: Confidence in understanding (0.0-1.0)
        reasoning: Why this decision was made
    """
    intent: str
    stakes_level: StakesLevel
    clarify_needed: bool
    clarify_question: Optional[str]
    response_strategy: ResponseStrategy
    confidence: float  # 0.0-1.0
    reasoning: str


class JudgmentEngine:
    """
    Detects when Penny should clarify vs answer immediately.

    Purpose:
        Prevents drift by ensuring learning systems only learn from
        clear, unambiguous inputs.

    Detection Methods (Phase 1A - implement vague referent detection):
        - Vague referents: "that", "it", "the thing" without clear antecedent
        - Missing parameters: TBD in Phase 1B
        - High stakes: TBD in Phase 1B
        - Contradictions: TBD in Phase 1C
        - Low confidence: TBD in Phase 1C
    """

    def __init__(self):
        """Initialize judgment engine with detection patterns."""
        # Patterns that indicate vague/ambiguous references
        self.vague_referents = [
            "that", "it", "this", "these",
            "those", "them", "one", "stuff", "issue"
        ]

        # Vague nouns that don't clarify anything
        self.vague_nouns = [
            "thing", "things", "stuff", "one", "ones"
        ]

        # Common action verbs that aren't nouns
        self.action_verbs = [
            'fix', 'delete', 'create', 'update', 'build',
            'remove', 'add', 'change', 'modify', 'debug',
            'make', 'do', 'get', 'set', 'run', 'start',
            'stop', 'restart', 'install', 'uninstall'
        ]

        # Context window size for checking antecedents
        self.context_window = 50  # characters to look back

    def analyze_request(
        self,
        user_input: str,
        context: dict
    ) -> Decision:
        """
        Analyze user request and decide whether to clarify or answer.

        Args:
            user_input: Current user message
            context: Dictionary with:
                - 'conversation_history': List of recent message dicts
                    Each dict has: {'role': 'user'/'assistant', 'content': str}
                - 'semantic_memory': List of relevant past conversations
                - 'emotional_state': Current emotion detection result
                - 'personality_state': Current personality dimensions

        Returns:
            Decision object with structured response strategy

        Example:
            >>> engine = JudgmentEngine()
            >>> decision = engine.analyze_request(
            ...     "Fix that thing",
            ...     {'conversation_history': []}
            ... )
            >>> decision.clarify_needed
            True
        """
        # For Phase 1A: Only check vague referents
        has_vague_referent = self._detect_vague_referents(user_input, context)

        # Extract basic intent
        intent = self._extract_intent(user_input)

        # For Phase 1A: All requests are LOW stakes (will implement in 1B)
        stakes = StakesLevel.LOW

        # Decide whether to clarify
        if has_vague_referent:
            question = self._generate_clarifying_question_for_vague_referent(
                user_input,
                context
            )

            return Decision(
                intent=intent,
                stakes_level=stakes,
                clarify_needed=True,
                clarify_question=question,
                response_strategy=ResponseStrategy.CLARIFY,
                confidence=0.3,  # Low confidence due to ambiguity
                reasoning="Vague referent detected without clear antecedent"
            )
        else:
            return Decision(
                intent=intent,
                stakes_level=stakes,
                clarify_needed=False,
                clarify_question=None,
                response_strategy=ResponseStrategy.ANSWER,
                confidence=0.8,  # High confidence, request is clear
                reasoning="No ambiguity detected, proceed with answer"
            )

    def _detect_vague_referents(self, user_input: str, context: dict) -> bool:
        """
        Detect vague referents like "that", "it", "the thing".

        Algorithm:
        1. Check if input contains vague referent words
        2. Look for clear noun nearby (within context_window)
        3. If no clear noun, return True (vague)

        Examples:
            "Fix that thing" → True (vague)
            "Fix that authentication bug" → False (clear: "authentication bug")
            "Delete it" → True (vague)
            "Delete the test file" → False (clear: "test file")

        Args:
            user_input: The user's message
            context: Context dictionary (may contain recent messages)

        Returns:
            True if vague referent detected without clear antecedent
        """
        input_lower = user_input.lower()
        words = input_lower.split()

        # Check each word to see if it's a vague referent
        for i, word in enumerate(words):
            # Remove punctuation for matching
            clean_word = word.strip('.,!?;:')

            if clean_word in self.vague_referents:
                # Found a vague referent - now check for clear noun nearby
                # Look at words around this vague referent (2 before, 2 after)
                window_start = max(0, i - 2)
                window_end = min(len(words), i + 3)
                window = words[window_start:window_end]

                # Check if there's a specific noun (longer than 3 chars, not vague)
                # Exclude:
                # - Vague referents
                # - Vague nouns (thing, stuff)
                # - Action verbs (fix, delete, etc.)
                # - Common articles
                # - The vague word itself
                has_clear_noun = any(
                    len(w.strip('.,!?;:')) > 3 and
                    w.strip('.,!?;:') not in self.vague_referents and
                    w.strip('.,!?;:') not in self.vague_nouns and
                    w.strip('.,!?;:') not in self.action_verbs and
                    w.strip('.,!?;:') not in ['the', 'a', 'an', 'with', 'from', 'into']
                    for w in window if w.strip('.,!?;:') != clean_word
                )

                if not has_clear_noun:
                    return True  # Vague referent without clear noun nearby

        return False  # No vague referents found or all have clear context

    def _generate_clarifying_question_for_vague_referent(
        self,
        user_input: str,
        context: dict
    ) -> str:
        """
        Generate a clarifying question for vague referent.

        This returns a RAW question. The personality layer (Phase 2) will
        format it in Penny's voice.

        Args:
            user_input: The user's message
            context: Context dictionary

        Returns:
            Raw clarifying question (will be styled later)

        Example:
            "Fix that thing" → "which_thing: auth_bug OR tts_latency"
        """
        # For Phase 1A: Simple generic question
        # In Phase 2, this will be formatted as:
        # "Quick check—you mean the auth bug or the TTS latency?"

        # Try to extract action verb
        action = self._extract_action_verb(user_input)

        # Return structured question data
        return f"clarify_referent: action={action}"

    def _extract_intent(self, user_input: str) -> str:
        """
        Extract user's likely intent from input.

        Simple keyword-based extraction for Phase 1A.

        Args:
            user_input: The user's message

        Returns:
            Intent string (e.g., "fix_bug", "create_file", "explain_concept")
        """
        input_lower = user_input.lower()

        # Simple intent keywords
        if any(word in input_lower for word in ['fix', 'debug', 'repair']):
            return 'fix_issue'
        elif any(word in input_lower for word in ['create', 'make', 'build']):
            return 'create_something'
        elif any(word in input_lower for word in ['delete', 'remove', 'erase']):
            return 'delete_something'
        elif any(word in input_lower for word in ['explain', 'what', 'how', 'why']):
            return 'get_explanation'
        else:
            return 'general_request'

    def _extract_action_verb(self, user_input: str) -> str:
        """
        Extract the main action verb from input.

        Args:
            user_input: The user's message

        Returns:
            Action verb (e.g., "fix", "delete", "create")
        """
        input_lower = user_input.lower()

        # Common action verbs
        action_verbs = ['fix', 'delete', 'create', 'update', 'build',
                       'remove', 'add', 'change', 'modify', 'debug']

        for verb in action_verbs:
            if verb in input_lower:
                return verb

        return 'do'  # Default
