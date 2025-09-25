"""
Conversation Flow Analyzer
Provides heuristics for measuring conversational smoothness, authenticity, and
cultural element integration in Penny's production telemetry system.
"""

from __future__ import annotations

import math
import statistics
from typing import Dict, List, Sequence


class ConversationFlowAnalyzer:
    """Heuristic analyzer for conversational flow and authenticity."""

    def __init__(self) -> None:
        self._neutral_keywords = {
            "hi", "hello", "thanks", "appreciate", "sure", "sounds", "good"
        }

    def analyze_response_appropriateness(self, user_input: str, penny_response: str) -> float:
        """Score how well Penny's response aligns with the user input.

        Returns a score between 0.0 and 1.0. Measures keyword overlap,
        sentiment alignment, and response length proportionality.
        """
        if not user_input or not penny_response:
            return 0.0

        user_tokens = self._tokenize(user_input)
        response_tokens = self._tokenize(penny_response)

        if not user_tokens or not response_tokens:
            return 0.0

        overlap = len(user_tokens & response_tokens)
        coverage = overlap / max(len(user_tokens), 1)

        length_ratio = min(len(penny_response) / max(len(user_input), 1), 3.0)
        length_score = 1.0 - abs(math.log(length_ratio + 1e-6) / math.log(3.0))
        length_score = max(0.0, min(1.0, length_score))

        neutral_bonus = 0.1 if self._neutral_keywords & response_tokens else 0.0

        score = (coverage * 0.6) + (length_score * 0.3) + neutral_bonus
        return max(0.0, min(1.0, score))

    def measure_cultural_element_integration(self,
                                             response: str,
                                             cultural_elements: Sequence[str]) -> float:
        """Evaluate how naturally cultural elements appear within a response."""
        if not response:
            return 0.0
        if not cultural_elements:
            return 1.0  # No cultural elements means no forced insertion

        response_lower = response.lower()
        matches = 0
        for element in cultural_elements:
            if element and element.lower() in response_lower:
                matches += 1

        # Penalize excessive references
        density = matches / max(len(response.split()), 1)
        if matches == 0:
            return 0.5  # cultural opportunity missed but not harmful
        if density > 0.15:
            return max(0.0, 1.0 - density * 2)
        return min(1.0, 0.8 + (0.2 * matches))

    def detect_conversation_disruption(self,
                                       conversation_history: Sequence[Dict[str, str]]) -> float:
        """Score 0-1 where 1 indicates smooth flow and 0 indicates disruption."""
        if len(conversation_history) < 2:
            return 1.0

        transitions: List[float] = []
        for prev, current in zip(conversation_history[:-1], conversation_history[1:]):
            user_tokens = self._tokenize(prev.get("user", ""))
            next_tokens = self._tokenize(current.get("user", ""))
            if not user_tokens or not next_tokens:
                continue
            overlap = len(user_tokens & next_tokens)
            transitions.append(overlap / max(len(next_tokens), 1))

        if not transitions:
            return 0.7

        std_dev = statistics.pstdev(transitions)
        mean_val = statistics.mean(transitions)
        disruption = std_dev * 0.6 + (1 - mean_val) * 0.4
        return max(0.0, min(1.0, 1.0 - disruption))

    def score_authenticity(self,
                           response: str,
                           personality_baseline: Dict[str, List[str]]) -> float:
        """Compare response against personality baseline keywords."""
        if not response:
            return 0.0

        baseline_tokens = set()
        for values in personality_baseline.values():
            baseline_tokens.update(token.lower() for token in values)

        if not baseline_tokens:
            return 0.7  # neutral default when baseline missing

        response_tokens = self._tokenize(response)
        overlap = len(response_tokens & baseline_tokens)
        alignment = overlap / max(len(baseline_tokens), 1)
        tone_penalty = 0.0
        if any(word in response_tokens for word in {"uh", "umm", "like"}):
            tone_penalty = 0.1

        score = max(0.0, min(1.0, alignment * 0.8 + 0.2 - tone_penalty))
        return score

    def _tokenize(self, text: str) -> set:
        return {token.strip(".,!?" ).lower() for token in text.split() if token}
