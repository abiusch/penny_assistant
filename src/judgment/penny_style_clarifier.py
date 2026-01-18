"""
Penny Style Clarifier - Formats clarifying questions in Penny's voice.

Rules:
- Casual, confident, playful
- Max 1-2 questions at a time
- No long disclaimers
- Quick "why I'm asking" in Penny tone
- Empathetic if user frustrated
"""

from typing import Dict, List, Optional
import random
import re
from .judgment_engine import Decision, StakesLevel

class PennyStyleClarifier:
    """
    Formats clarifying questions in Penny's authentic voice.

    Personality traits:
    - Casual, confident, witty
    - Direct, no hedging
    - Uses slang when appropriate
    - Sassy but constructive
    - Enthusiastic

    Anti-patterns to avoid:
    - Corporate speak ("I apologize, but...")
    - Over-explaining
    - Multiple questions at once
    - Hedging ("perhaps", "maybe")
    - Long disclaimers
    """

    def __init__(self):
        """Initialize clarifier with Penny-style templates."""

        # Templates for vague referents
        self.VAGUE_REFERENT_TEMPLATES = [
            "Quick check so I don't go off into the weeds—do you mean {option_a} or {option_b}?",
            "Before I sprint in the wrong direction: {clarification}?",
            "Two-second check: {clarification}?",
            "Real quick—{clarification}?",
            "Just to nail this—{clarification}?",
        ]

        # Templates for missing parameters
        self.MISSING_PARAM_TEMPLATES = [
            "Two-second clarity question: what's the {param}?",
            "Real quick—what's the {param} here?",
            "Need one detail: {param}?",
            "Quick Q: {param}?",
            "What's the {param}?",
        ]

        # Templates for high stakes
        self.HIGH_STAKES_TEMPLATES = [
            "Wanna make sure I nail this—{clarification}?",
            "Let me double-check before I do something irreversible: {clarification}?",
            "Quick confirmation so I don't mess this up: {clarification}?",
            "Before I commit: {clarification}?",
            "Just checking—{clarification}? (Don't wanna yeet the wrong thing)",
        ]

        # Templates for contradictions
        self.CONTRADICTION_TEMPLATES = [
            "Hold up—last time we talked about {past_context}. Did that change?",
            "Quick sanity check: earlier you mentioned {past}, now saying {current}. Which is current?",
            "Wait—I thought we were doing {past}. Did the plan change?",
            "Heads up: this conflicts with {past_context}. What's the new direction?",
            "Real quick—you mentioned {past} before. What changed?",
        ]

        # Templates for low confidence
        self.LOW_CONFIDENCE_TEMPLATES = [
            "Wanna spell that out a bit more? Not 100% sure what you're after.",
            "Can you give me a bit more detail? Wanna make sure I get this right.",
            "What's the full picture here? Need a couple more details.",
            "Break that down for me? Wanna make sure I'm tracking.",
            "Can you expand on that? Want to nail this for you.",
        ]

        # Frustrated user templates (gentler but still Penny)
        self.FRUSTRATED_TEMPLATES = [
            "On it—quick check so I don't waste time: {clarification}?",
            "Got it—one quick thing: {clarification}?",
            "Absolutely—just need: {clarification}?",
            "Hear you—real quick: {clarification}?",
            "I'm on this—just need to know: {clarification}?",
        ]

        # Frustration indicators
        self.FRUSTRATION_INDICATORS = [
            'fuck', 'shit', 'damn', 'already', 'come on',
            'jesus', 'christ', 'dammit', 'god', 'hurry'
        ]

    def format_question(
        self,
        decision: Decision,
        user_input: str = "",
        user_seems_frustrated: bool = False
    ) -> str:
        """
        Format clarifying question in Penny's voice.

        Args:
            decision: Decision object from JudgmentEngine
            user_input: Original user input (for frustration detection)
            user_seems_frustrated: Override frustration detection

        Returns:
            Formatted question in Penny's style (1-2 sentences max)

        Examples:
            Input: "vague_referent: action=fix"
            Output: "Quick check—you mean the auth bug or the TTS latency?"

            Input: "high_stakes: confirm=delete, scope=all"
            Output: "Wanna make sure I nail this—you mean delete ALL items?"
        """
        # Detect frustration if not provided
        if not user_seems_frustrated and user_input:
            user_seems_frustrated = self.detect_frustration(user_input)

        # Parse the raw question
        raw_question = decision.clarify_question

        # Route to appropriate formatter based on question type
        if raw_question.startswith("clarify_referent:") or raw_question.startswith("vague_referent:"):
            return self._format_vague_referent(raw_question, user_seems_frustrated)

        elif raw_question.startswith("missing_params:") or raw_question.startswith("missing_param:"):
            return self._format_missing_param(raw_question, user_seems_frustrated)

        elif raw_question.startswith("confirm_high_stakes:") or raw_question.startswith("high_stakes:"):
            return self._format_high_stakes(raw_question, user_seems_frustrated)

        elif raw_question.startswith("contradiction:"):
            return self._format_contradiction(raw_question, user_seems_frustrated)

        elif raw_question.startswith("low_confidence:"):
            return self._format_low_confidence(raw_question, user_seems_frustrated)

        else:
            # Fallback for unknown format
            return "Can you give me a bit more detail on that?"

    def _format_vague_referent(self, raw_question: str, frustrated: bool) -> str:
        """Format vague referent question."""
        # Example input: "clarify_referent: action=fix" or "vague_referent: action=fix"

        if frustrated:
            # Use gentler frustrated templates
            template = random.choice(self.FRUSTRATED_TEMPLATES)
            return template.format(clarification="which specific thing")

        # Parse action if present
        action = ""
        if "action=" in raw_question:
            action = raw_question.split("action=")[1].strip()

        # Choose template
        template = random.choice(self.VAGUE_REFERENT_TEMPLATES)

        # Format based on whether we have specific options
        if "or" in raw_question or "option_" in raw_question:
            # Has specific options
            return template.format(
                option_a="the first thing",
                option_b="the second thing",
                clarification="which one specifically"
            )
        else:
            # Generic clarification
            clarification = f"which {action} exactly" if action else "which thing specifically"
            return template.format(
                option_a="X",
                option_b="Y",
                clarification=clarification
            )

    def _format_missing_param(self, raw_question: str, frustrated: bool) -> str:
        """Format missing parameter question."""
        # Example input: "missing_params: action=schedule, params=date, time"

        if frustrated:
            template = random.choice(self.FRUSTRATED_TEMPLATES)
            return template.format(clarification="what's the date and time")

        # Extract what's needed
        needs = []
        if "params=" in raw_question:
            needs_str = raw_question.split("params=")[1].strip()
            needs = [n.strip() for n in needs_str.split(",")]
        elif "needs=" in raw_question:
            needs_str = raw_question.split("needs=")[1].strip()
            needs = [n.strip() for n in needs_str.split(",")]

        # Choose template
        template = random.choice(self.MISSING_PARAM_TEMPLATES)

        # Format parameter list
        if len(needs) > 1:
            param = " and ".join(needs)
        elif needs:
            param = needs[0]
        else:
            param = "details"

        return template.format(param=param)

    def _format_high_stakes(self, raw_question: str, frustrated: bool) -> str:
        """Format high stakes confirmation question."""
        # Example input: "confirm_high_stakes: categories=destructive"

        if frustrated:
            # Still need confirmation even if frustrated
            template = "I hear you—just need to confirm: {clarification}?"
        else:
            template = random.choice(self.HIGH_STAKES_TEMPLATES)

        # Extract confirmation details
        action = "do this"
        scope = ""

        if "categories=" in raw_question:
            categories = raw_question.split("categories=")[1].strip()
            action = f"this {categories} action"

        if "confirm=" in raw_question:
            action = raw_question.split("confirm=")[1].split(",")[0].strip()

        if "scope=" in raw_question:
            scope = raw_question.split("scope=")[1].strip()

        # Build clarification
        if scope:
            clarification = f"you mean {action} {scope}"
        else:
            clarification = f"you're sure about this {action}"

        return template.format(clarification=clarification)

    def _format_contradiction(self, raw_question: str, frustrated: bool) -> str:
        """Format contradiction clarification question."""
        # Example input: "contradiction: past=Rust, now=Python"

        if frustrated:
            return "Real quick—I thought we were doing something else. What changed?"

        # Extract past and current
        past = "something else"
        current = "this"

        if "past=" in raw_question:
            past = raw_question.split("past=")[1].split(",")[0].strip()

        if "now=" in raw_question:
            current = raw_question.split("now=")[1].strip()

        # Choose template
        template = random.choice(self.CONTRADICTION_TEMPLATES)

        return template.format(
            past_context=past,
            past=past,
            current=current
        )

    def _format_low_confidence(self, raw_question: str, frustrated: bool) -> str:
        """Format low confidence clarification question."""
        # Example input: "low_confidence: unclear_what, unclear_action"

        if frustrated:
            return "Got it—can you spell that out a bit more so I nail this?"

        # Choose template
        template = random.choice(self.LOW_CONFIDENCE_TEMPLATES)

        return template

    def detect_frustration(self, user_input: str) -> bool:
        """
        Detect if user seems frustrated.

        Indicators:
        - Profanity
        - "just", "already", "come on"
        - ALL CAPS (multiple words)
        - Multiple punctuation marks (!!!, ???)

        Args:
            user_input: The user's message

        Returns:
            True if frustration detected

        Examples:
            "Just fix the fucking bug already" → True
            "JUST DO IT" → True
            "Can you help me?" → False
        """
        input_lower = user_input.lower()

        # Check for profanity or frustration words
        if any(indicator in input_lower for indicator in self.FRUSTRATION_INDICATORS):
            return True

        # Check for ALL CAPS (at least 2 words)
        words = user_input.split()
        caps_words = [w for w in words if w.isupper() and len(w) >= 2]
        if len(caps_words) >= 2:
            return True

        # Check for multiple punctuation marks
        if '!!!' in user_input or '???' in user_input or '!!' in user_input:
            return True

        return False

    def add_context_hint(
        self,
        question: str,
        decision: Decision
    ) -> str:
        """
        Optionally add brief "I can help once I know" hint.

        Only adds if:
        - Intent is clear
        - Question isn't already too long
        - Would be genuinely helpful

        Args:
            question: Already formatted question
            decision: Decision object with intent

        Returns:
            Question with optional context hint

        Example:
            Input: "Quick check—you mean the auth bug or TTS latency?"
            Output: "Quick check—you mean the auth bug or TTS latency? I can fix it once I know which one."
        """
        # Don't add hint if question is already long
        if len(question) > 100:
            return question

        # Don't add hint if no clear intent
        if not decision.intent or decision.intent == 'general_request':
            return question

        # Map intents to helpful hints
        intent_hints = {
            'fix_issue': "I can fix it once I know which one.",
            'create_something': "I can create it once I know the details.",
            'delete_something': "I can delete it once I confirm.",
            'get_explanation': "I can explain once I know what specifically.",
        }

        hint = intent_hints.get(decision.intent)
        if hint:
            return f"{question} {hint}"

        return question
