#!/usr/bin/env python3
"""
Confidence Indicator Engine for Penny
Handles uncertainty expression and confidence communication
"""

import json
import random
from enum import Enum
from dataclasses import dataclass
from typing import Dict, List, Optional, Any, Tuple
import math


class ConfidenceLevel(Enum):
    VERY_HIGH = "very_high"      # 0.9-1.0
    HIGH = "high"                # 0.75-0.9
    MODERATE = "moderate"        # 0.5-0.75
    LOW = "low"                  # 0.25-0.5
    VERY_LOW = "very_low"        # 0.0-0.25


class UncertaintyType(Enum):
    FACTUAL = "factual"          # Not sure about facts
    EMOTIONAL = "emotional"      # Not sure about emotional state
    CONTEXTUAL = "contextual"    # Not sure about context/situation
    PREFERENCE = "preference"    # Not sure about user preferences
    PREDICTION = "prediction"    # Not sure about future outcomes


@dataclass
class ConfidenceContext:
    """Context for confidence expression."""
    topic: str
    social_setting: str
    relationship_familiarity: float  # 0-1, how well we know the user
    conversation_stakes: str         # low, medium, high
    past_accuracy: float            # 0-1, how accurate we've been on this topic


@dataclass
class ConfidenceExpression:
    """A way to express uncertainty."""
    confidence_level: ConfidenceLevel
    uncertainty_type: UncertaintyType
    expression: str
    hedging_words: List[str]
    follow_up_question: Optional[str]
    alternatives_offered: bool


class ConfidenceIndicatorEngine:
    """Engine for expressing uncertainty appropriately."""

    def __init__(self):
        self.confidence_expressions = self._load_confidence_expressions()
        self.hedging_strategies = self._load_hedging_strategies()
        self.context_adjustments = self._load_context_adjustments()

    def _load_confidence_expressions(self) -> Dict[str, List[Dict[str, Any]]]:
        """Load different ways to express confidence levels."""
        return {
            "very_high": [
                {"expression": "I'm confident that {content}", "strength": "strong"},
                {"expression": "I'm quite sure {content}", "strength": "strong"},
                {"expression": "Based on what I know, {content}", "strength": "factual"},
                {"expression": "{content}", "strength": "direct"}  # No hedging needed
            ],
            "high": [
                {"expression": "I think {content}", "strength": "mild"},
                {"expression": "It seems like {content}", "strength": "observational"},
                {"expression": "I believe {content}", "strength": "moderate"},
                {"expression": "From what I can tell, {content}", "strength": "analytical"}
            ],
            "moderate": [
                {"expression": "I think {content}, but I'm not entirely sure", "strength": "honest"},
                {"expression": "It might be that {content}", "strength": "tentative"},
                {"expression": "My sense is {content}, though I could be wrong", "strength": "humble"},
                {"expression": "I'm getting the impression that {content}", "strength": "interpretive"}
            ],
            "low": [
                {"expression": "I'm not sure, but maybe {content}", "strength": "uncertain"},
                {"expression": "I could be wrong, but {content}", "strength": "cautious"},
                {"expression": "I'm having trouble pinpointing this, but {content}", "strength": "struggling"},
                {"expression": "This is just a guess, but {content}", "strength": "speculative"}
            ],
            "very_low": [
                {"expression": "I'm really not sure about this - {content}?", "strength": "very_uncertain"},
                {"expression": "I honestly don't know, but could it be {content}?", "strength": "admitting_uncertainty"},
                {"expression": "I'm quite uncertain here - {content} maybe?", "strength": "highly_tentative"},
                {"expression": "I'm probably way off, but {content}?", "strength": "self_deprecating"}
            ]
        }

    def _load_hedging_strategies(self) -> Dict[str, List[str]]:
        """Load hedging words and phrases."""
        return {
            "mild_hedging": [
                "I think", "it seems", "appears to be", "looks like",
                "probably", "likely", "tends to be"
            ],
            "moderate_hedging": [
                "might be", "could be", "possibly", "perhaps",
                "I suspect", "my impression is", "it's possible that"
            ],
            "strong_hedging": [
                "I'm not sure but", "maybe", "I could be wrong but",
                "this is just a guess", "I'm uncertain whether"
            ],
            "follow_up_hedging": [
                "does that sound right?", "what do you think?",
                "am I on the right track?", "how does that feel to you?",
                "let me know if I'm misreading this"
            ]
        }

    def _load_context_adjustments(self) -> Dict[str, Dict[str, float]]:
        """Load adjustments based on context."""
        return {
            "relationship_familiarity": {
                # More familiar = can be more direct about uncertainty
                "very_familiar": 1.2,    # Boost confidence expression
                "familiar": 1.1,
                "somewhat_familiar": 1.0,
                "unfamiliar": 0.9,       # More cautious
                "very_unfamiliar": 0.8
            },
            "conversation_stakes": {
                # Higher stakes = more careful about uncertainty
                "low": 1.1,              # Can be more casual
                "medium": 1.0,
                "high": 0.8,             # More careful
                "critical": 0.6          # Very careful
            },
            "social_setting": {
                "casual_chat": 1.2,
                "problem_solving": 1.0,
                "professional": 0.9,
                "crisis": 0.7,
                "celebration": 1.1,
                "venting": 1.0,
                "friend_discussion": 1.1
            }
        }

    def assess_confidence_level(self, confidence_score: float) -> ConfidenceLevel:
        """Convert numerical confidence to confidence level."""
        if confidence_score >= 0.9:
            return ConfidenceLevel.VERY_HIGH
        elif confidence_score >= 0.75:
            return ConfidenceLevel.HIGH
        elif confidence_score >= 0.5:
            return ConfidenceLevel.MODERATE
        elif confidence_score >= 0.25:
            return ConfidenceLevel.LOW
        else:
            return ConfidenceLevel.VERY_LOW

    def determine_uncertainty_type(self, context: Dict[str, Any]) -> UncertaintyType:
        """Determine what type of uncertainty we're dealing with."""
        # Look for clues in the context about what we're uncertain about

        if "emotion" in context or "feeling" in context:
            return UncertaintyType.EMOTIONAL
        elif "preference" in context or "like" in context or "want" in context:
            return UncertaintyType.PREFERENCE
        elif "will" in context or "predict" in context or "future" in context:
            return UncertaintyType.PREDICTION
        elif "situation" in context or "social" in context:
            return UncertaintyType.CONTEXTUAL
        else:
            return UncertaintyType.FACTUAL

    def generate_confidence_expression(self, confidence_score: float,
                                     content: str,
                                     context: ConfidenceContext,
                                     uncertainty_type: UncertaintyType = None) -> ConfidenceExpression:
        """Generate appropriate confidence expression."""

        # Assess base confidence level
        confidence_level = self.assess_confidence_level(confidence_score)

        # Determine uncertainty type if not provided
        if uncertainty_type is None:
            uncertainty_type = self.determine_uncertainty_type({"content": content})

        # Apply context adjustments
        adjusted_confidence = self._apply_context_adjustments(confidence_score, context)
        final_confidence_level = self.assess_confidence_level(adjusted_confidence)

        # Select appropriate expression
        expression_data = self._select_expression(final_confidence_level, content, context)

        # Determine if we should offer alternatives
        alternatives_offered = adjusted_confidence < 0.6

        # Generate follow-up question if appropriate
        follow_up = self._generate_follow_up_question(final_confidence_level, uncertainty_type, context)

        return ConfidenceExpression(
            confidence_level=final_confidence_level,
            uncertainty_type=uncertainty_type,
            expression=expression_data["expression"],
            hedging_words=expression_data["hedging_words"],
            follow_up_question=follow_up,
            alternatives_offered=alternatives_offered
        )

    def express_uncertainty(self, confidence_score: float,
                          content: str,
                          context: ConfidenceContext,
                          include_alternatives: bool = False) -> str:
        """Express uncertainty in a natural way."""

        expression = self.generate_confidence_expression(confidence_score, content, context)

        result_parts = [expression.expression]

        # Add follow-up question if present
        if expression.follow_up_question:
            result_parts.append(expression.follow_up_question)

        # Add alternatives if requested and appropriate
        if include_alternatives and expression.alternatives_offered:
            alternatives = self._generate_alternatives(content, expression.uncertainty_type)
            if alternatives:
                result_parts.append(f"Or maybe {alternatives}?")

        return " ".join(result_parts)

    def calibrate_confidence_expression(self, stated_confidence: float,
                                      actual_confidence: float,
                                      context: ConfidenceContext) -> Dict[str, Any]:
        """Calibrate how we express confidence based on past accuracy."""

        # Calculate accuracy gap
        accuracy_gap = abs(stated_confidence - actual_confidence)

        # Adjust future confidence expression
        if accuracy_gap > 0.3:  # We were significantly off
            adjustment = -0.2  # Be more cautious
            recommendation = "Express more uncertainty in similar situations"
        elif accuracy_gap > 0.15:  # Somewhat off
            adjustment = -0.1
            recommendation = "Slight increase in uncertainty expression"
        elif accuracy_gap < 0.05:  # Very accurate
            adjustment = 0.1   # Can be slightly more confident
            recommendation = "Current confidence expression is well-calibrated"
        else:
            adjustment = 0
            recommendation = "Maintain current confidence expression style"

        return {
            "accuracy_gap": accuracy_gap,
            "confidence_adjustment": adjustment,
            "recommendation": recommendation,
            "calibrated_confidence": max(0, min(1, actual_confidence + adjustment))
        }

    def _apply_context_adjustments(self, confidence_score: float, context: ConfidenceContext) -> float:
        """Apply contextual adjustments to confidence score."""

        adjusted_score = confidence_score

        # Relationship familiarity adjustment
        if context.relationship_familiarity > 0.8:
            familiarity_key = "very_familiar"
        elif context.relationship_familiarity > 0.6:
            familiarity_key = "familiar"
        elif context.relationship_familiarity > 0.4:
            familiarity_key = "somewhat_familiar"
        elif context.relationship_familiarity > 0.2:
            familiarity_key = "unfamiliar"
        else:
            familiarity_key = "very_unfamiliar"

        adjusted_score *= self.context_adjustments["relationship_familiarity"][familiarity_key]

        # Stakes adjustment
        adjusted_score *= self.context_adjustments["conversation_stakes"][context.conversation_stakes]

        # Social setting adjustment
        adjusted_score *= self.context_adjustments["social_setting"][context.social_setting]

        # Past accuracy adjustment
        if context.past_accuracy < 0.5:
            adjusted_score *= 0.8  # Be more cautious if we've been wrong before
        elif context.past_accuracy > 0.8:
            adjusted_score *= 1.1  # Can be slightly more confident

        return max(0, min(1, adjusted_score))

    def _select_expression(self, confidence_level: ConfidenceLevel, content: str, context: ConfidenceContext) -> Dict[str, Any]:
        """Select appropriate expression for the confidence level."""

        level_key = confidence_level.value
        expressions = self.confidence_expressions[level_key]

        # Select expression based on context
        if context.social_setting == "casual_chat":
            # Prefer more casual expressions
            preferred_strengths = ["mild", "observational", "honest"]
        elif context.social_setting == "professional":
            # Prefer more formal expressions
            preferred_strengths = ["analytical", "factual", "moderate"]
        else:
            # Default selection
            preferred_strengths = []

        # Try to find preferred expression
        selected = None
        for expr in expressions:
            if not preferred_strengths or expr["strength"] in preferred_strengths:
                selected = expr
                break

        # Fallback to first expression
        if selected is None:
            selected = expressions[0]

        # Format the expression
        formatted_expression = selected["expression"].format(content=content)

        # Add hedging words based on confidence level
        hedging_words = []
        if confidence_level in [ConfidenceLevel.LOW, ConfidenceLevel.VERY_LOW]:
            hedging_words = random.sample(self.hedging_strategies["strong_hedging"],
                                        min(2, len(self.hedging_strategies["strong_hedging"])))
        elif confidence_level == ConfidenceLevel.MODERATE:
            hedging_words = random.sample(self.hedging_strategies["moderate_hedging"], 1)

        return {
            "expression": formatted_expression,
            "hedging_words": hedging_words,
            "strength": selected["strength"]
        }

    def _generate_follow_up_question(self, confidence_level: ConfidenceLevel,
                                   uncertainty_type: UncertaintyType,
                                   context: ConfidenceContext) -> Optional[str]:
        """Generate appropriate follow-up question."""

        # Only generate follow-up for low confidence or when appropriate
        if confidence_level not in [ConfidenceLevel.LOW, ConfidenceLevel.VERY_LOW, ConfidenceLevel.MODERATE]:
            return None

        # Don't ask follow-ups in high-stakes situations unless very uncertain
        if context.conversation_stakes == "critical" and confidence_level != ConfidenceLevel.VERY_LOW:
            return None

        follow_up_options = {
            UncertaintyType.EMOTIONAL: [
                "How does that feel to you?",
                "Am I reading your mood right?",
                "Does that match what you're experiencing?"
            ],
            UncertaintyType.PREFERENCE: [
                "Is that what you'd prefer?",
                "Does that sound good to you?",
                "What would you rather do?"
            ],
            UncertaintyType.CONTEXTUAL: [
                "Am I understanding the situation correctly?",
                "Does that match what's happening?",
                "Have I got the context right?"
            ],
            UncertaintyType.FACTUAL: [
                "Does that sound right to you?",
                "Do you have more information about this?",
                "Am I on the right track?"
            ],
            UncertaintyType.PREDICTION: [
                "What do you think will happen?",
                "Does that seem likely to you?",
                "How do you see this playing out?"
            ]
        }

        options = follow_up_options.get(uncertainty_type, follow_up_options[UncertaintyType.FACTUAL])
        return random.choice(options)

    def _generate_alternatives(self, content: str, uncertainty_type: UncertaintyType) -> Optional[str]:
        """Generate alternative possibilities."""

        # This is a simplified version - in practice, this would use more sophisticated logic
        alternative_templates = {
            UncertaintyType.EMOTIONAL: "you're feeling differently about this",
            UncertaintyType.PREFERENCE: "you'd prefer something else",
            UncertaintyType.CONTEXTUAL: "the situation is different than I think",
            UncertaintyType.FACTUAL: "there's another explanation",
            UncertaintyType.PREDICTION: "things might go differently"
        }

        return alternative_templates.get(uncertainty_type)

    def get_confidence_stats(self) -> Dict[str, Any]:
        """Get statistics about confidence expression patterns."""
        # This would be implemented to track and analyze confidence patterns over time
        return {
            "total_expressions": 0,
            "accuracy_rate": 0.0,
            "most_common_confidence_level": "moderate",
            "calibration_score": 0.0
        }


def create_confidence_indicator_engine() -> ConfidenceIndicatorEngine:
    """Factory function to create confidence indicator engine."""
    return ConfidenceIndicatorEngine()


if __name__ == "__main__":
    # Test the confidence indicator engine
    engine = create_confidence_indicator_engine()

    # Test contexts
    contexts = [
        ConfidenceContext(
            topic="programming",
            social_setting="problem_solving",
            relationship_familiarity=0.8,
            conversation_stakes="medium",
            past_accuracy=0.7
        ),
        ConfidenceContext(
            topic="emotions",
            social_setting="casual_chat",
            relationship_familiarity=0.9,
            conversation_stakes="low",
            past_accuracy=0.6
        ),
        ConfidenceContext(
            topic="technical_advice",
            social_setting="professional",
            relationship_familiarity=0.3,
            conversation_stakes="high",
            past_accuracy=0.8
        )
    ]

    test_cases = [
        (0.95, "you're frustrated with debugging", UncertaintyType.EMOTIONAL),
        (0.7, "the bug is in the authentication module", UncertaintyType.FACTUAL),
        (0.4, "you might prefer minimal sass here", UncertaintyType.PREFERENCE),
        (0.2, "this approach will work", UncertaintyType.PREDICTION),
        (0.1, "the team dynamics are causing issues", UncertaintyType.CONTEXTUAL)
    ]

    print("=== CONFIDENCE INDICATOR ENGINE DEMO ===\n")

    for i, (confidence, content, uncertainty_type) in enumerate(test_cases):
        for j, context in enumerate(contexts):
            print(f"Test {i+1}.{j+1}: Confidence={confidence:.2f}, Context={context.social_setting}")
            print(f"Content: '{content}'")

            # Generate expression
            expression = engine.generate_confidence_expression(
                confidence, content, context, uncertainty_type
            )

            # Express uncertainty
            result = engine.express_uncertainty(
                confidence, content, context, include_alternatives=True
            )

            print(f"Expression: {result}")
            print(f"Confidence Level: {expression.confidence_level.value}")
            print(f"Uncertainty Type: {expression.uncertainty_type.value}")
            print("-" * 50)