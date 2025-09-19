#!/usr/bin/env python3
"""
Reasoning Transparency System for Penny
Makes Penny's decision-making process visible and explainable
"""

import json
import time
from enum import Enum
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime


class ReasoningType(Enum):
    CONTEXT_DETECTION = "context_detection"
    RESPONSE_STYLE = "response_style"
    MEMORY_RETRIEVAL = "memory_retrieval"
    SOCIAL_BOUNDARY = "social_boundary"
    CONFIDENCE_ASSESSMENT = "confidence_assessment"


@dataclass
class ReasoningStep:
    """A single step in the reasoning process."""
    step_id: str
    reasoning_type: ReasoningType
    input_data: Dict[str, Any]
    logic_applied: str
    output_result: Any
    confidence: float
    timestamp: float


@dataclass
class ReasoningChain:
    """Complete reasoning chain for a decision."""
    chain_id: str
    user_input: str
    final_decision: str
    reasoning_steps: List[ReasoningStep]
    overall_confidence: float
    debug_mode: bool
    timestamp: float


class ReasoningTransparencySystem:
    """System for making Penny's reasoning transparent and explainable."""

    def __init__(self, debug_mode: bool = False):
        self.debug_mode = debug_mode
        self.reasoning_chains: List[ReasoningChain] = []
        self.reasoning_patterns = self._load_reasoning_patterns()

    def _load_reasoning_patterns(self) -> Dict[str, Any]:
        """Load common reasoning patterns and templates."""
        return {
            "sass_level_decision": {
                "pattern": "detected {emotion} + {intensity} + past pattern {past_pattern} → chose {sass_level}",
                "factors": ["emotion", "intensity", "past_pattern", "social_context"]
            },
            "memory_relevance": {
                "pattern": "current {topic} matches past {past_topic} from {timeframe} → retrieved {memory_count} memories",
                "factors": ["topic", "past_topic", "timeframe", "memory_count"]
            },
            "social_boundary": {
                "pattern": "topic {topic} with context {social_context} → boundary level {boundary_level}",
                "factors": ["topic", "social_context", "boundary_level"]
            },
            "confidence_expression": {
                "pattern": "uncertainty level {uncertainty} + past accuracy {accuracy} → express as {expression}",
                "factors": ["uncertainty", "accuracy", "expression"]
            }
        }

    def start_reasoning_chain(self, user_input: str) -> str:
        """Start a new reasoning chain."""
        chain_id = f"chain_{int(time.time() * 1000)}_{hash(user_input) % 10000}"

        reasoning_chain = ReasoningChain(
            chain_id=chain_id,
            user_input=user_input,
            final_decision="",
            reasoning_steps=[],
            overall_confidence=0.0,
            debug_mode=self.debug_mode,
            timestamp=time.time()
        )

        self.reasoning_chains.append(reasoning_chain)
        return chain_id

    def add_reasoning_step(self, chain_id: str, reasoning_type: ReasoningType,
                          input_data: Dict[str, Any], logic_applied: str,
                          output_result: Any, confidence: float) -> None:
        """Add a reasoning step to the current chain."""

        reasoning_step = ReasoningStep(
            step_id=f"step_{len(self._get_chain(chain_id).reasoning_steps) + 1}",
            reasoning_type=reasoning_type,
            input_data=input_data,
            logic_applied=logic_applied,
            output_result=output_result,
            confidence=confidence,
            timestamp=time.time()
        )

        chain = self._get_chain(chain_id)
        chain.reasoning_steps.append(reasoning_step)

    def finalize_reasoning_chain(self, chain_id: str, final_decision: str) -> ReasoningChain:
        """Finalize the reasoning chain with the final decision."""
        chain = self._get_chain(chain_id)
        chain.final_decision = final_decision

        # Calculate overall confidence as weighted average
        if chain.reasoning_steps:
            confidences = [step.confidence for step in chain.reasoning_steps]
            chain.overall_confidence = sum(confidences) / len(confidences)
        else:
            chain.overall_confidence = 0.5  # Default uncertain

        return chain

    def generate_debug_explanation(self, chain_id: str) -> str:
        """Generate human-readable explanation of the reasoning process."""
        chain = self._get_chain(chain_id)

        if not self.debug_mode:
            return ""

        explanation_parts = []
        explanation_parts.append(f"🧠 Reasoning for: '{chain.user_input}'")
        explanation_parts.append("=" * 50)

        for i, step in enumerate(chain.reasoning_steps, 1):
            explanation_parts.append(f"\n{i}. {step.reasoning_type.value.upper()}:")
            explanation_parts.append(f"   Input: {self._format_input_data(step.input_data)}")
            explanation_parts.append(f"   Logic: {step.logic_applied}")
            explanation_parts.append(f"   Result: {self._format_output_result(step.output_result)}")
            explanation_parts.append(f"   Confidence: {step.confidence:.2f}")

        explanation_parts.append(f"\n🎯 Final Decision: {chain.final_decision}")
        explanation_parts.append(f"📊 Overall Confidence: {chain.overall_confidence:.2f}")

        return "\n".join(explanation_parts)

    def generate_pattern_explanation(self, chain_id: str, pattern_type: str) -> str:
        """Generate explanation using predefined patterns."""
        chain = self._get_chain(chain_id)

        if pattern_type not in self.reasoning_patterns:
            return f"Unknown pattern type: {pattern_type}"

        pattern = self.reasoning_patterns[pattern_type]

        # Extract factors from reasoning steps
        factors = {}
        for step in chain.reasoning_steps:
            if step.reasoning_type == ReasoningType.CONTEXT_DETECTION:
                factors.update(step.input_data)
                factors["emotion"] = step.output_result.get("primary_emotion", "unknown")
                factors["intensity"] = step.output_result.get("intensity", "unknown")
            elif step.reasoning_type == ReasoningType.MEMORY_RETRIEVAL:
                factors["past_pattern"] = step.output_result.get("pattern", "none")
                factors["memory_count"] = len(step.output_result.get("memories", []))
            elif step.reasoning_type == ReasoningType.RESPONSE_STYLE:
                factors["sass_level"] = step.output_result

        # Format pattern string
        try:
            formatted_pattern = pattern["pattern"].format(**factors)
            return formatted_pattern
        except KeyError as e:
            return f"Missing factor for pattern: {e}"

    def get_confidence_reasoning(self, chain_id: str) -> Dict[str, Any]:
        """Get detailed confidence reasoning."""
        chain = self._get_chain(chain_id)

        confidence_factors = []
        for step in chain.reasoning_steps:
            confidence_factors.append({
                "step": step.reasoning_type.value,
                "confidence": step.confidence,
                "reasoning": self._explain_confidence_level(step.confidence)
            })

        return {
            "overall_confidence": chain.overall_confidence,
            "confidence_explanation": self._explain_confidence_level(chain.overall_confidence),
            "step_confidences": confidence_factors,
            "recommendation": self._get_confidence_recommendation(chain.overall_confidence)
        }

    def analyze_reasoning_patterns(self) -> Dict[str, Any]:
        """Analyze patterns in reasoning over time."""
        if not self.reasoning_chains:
            return {"message": "No reasoning chains to analyze"}

        # Analyze confidence trends
        confidence_trends = []
        reasoning_type_usage = {}

        for chain in self.reasoning_chains[-10:]:  # Last 10 chains
            confidence_trends.append(chain.overall_confidence)

            for step in chain.reasoning_steps:
                step_type = step.reasoning_type.value
                reasoning_type_usage[step_type] = reasoning_type_usage.get(step_type, 0) + 1

        avg_confidence = sum(confidence_trends) / len(confidence_trends) if confidence_trends else 0

        return {
            "average_confidence": avg_confidence,
            "confidence_trend": "improving" if len(confidence_trends) > 1 and confidence_trends[-1] > confidence_trends[0] else "stable",
            "most_used_reasoning": max(reasoning_type_usage, key=reasoning_type_usage.get) if reasoning_type_usage else "none",
            "reasoning_type_usage": reasoning_type_usage,
            "total_chains": len(self.reasoning_chains)
        }

    def _get_chain(self, chain_id: str) -> ReasoningChain:
        """Get reasoning chain by ID."""
        for chain in self.reasoning_chains:
            if chain.chain_id == chain_id:
                return chain
        raise ValueError(f"Reasoning chain {chain_id} not found")

    def _format_input_data(self, input_data: Dict[str, Any]) -> str:
        """Format input data for display."""
        if not input_data:
            return "None"

        # Limit display length
        formatted_items = []
        for key, value in input_data.items():
            str_value = str(value)
            if len(str_value) > 50:
                str_value = str_value[:47] + "..."
            formatted_items.append(f"{key}={str_value}")

        return ", ".join(formatted_items)

    def _format_output_result(self, output_result: Any) -> str:
        """Format output result for display."""
        if isinstance(output_result, dict):
            return json.dumps(output_result, indent=None)[:100] + ("..." if len(str(output_result)) > 100 else "")
        else:
            str_result = str(output_result)
            return str_result[:100] + ("..." if len(str_result) > 100 else "")

    def _explain_confidence_level(self, confidence: float) -> str:
        """Explain what a confidence level means."""
        if confidence >= 0.9:
            return "Very confident - strong evidence supports this decision"
        elif confidence >= 0.7:
            return "Confident - good evidence, minor uncertainty"
        elif confidence >= 0.5:
            return "Moderately confident - some uncertainty remains"
        elif confidence >= 0.3:
            return "Low confidence - significant uncertainty"
        else:
            return "Very uncertain - limited evidence available"

    def _get_confidence_recommendation(self, confidence: float) -> str:
        """Get recommendation based on confidence level."""
        if confidence >= 0.8:
            return "Proceed with current approach"
        elif confidence >= 0.6:
            return "Consider expressing mild uncertainty"
        elif confidence >= 0.4:
            return "Express uncertainty and ask for clarification"
        else:
            return "Acknowledge uncertainty and suggest alternatives"

    def export_reasoning_data(self, filename: str = None) -> str:
        """Export reasoning data for analysis."""
        if filename is None:
            filename = f"reasoning_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        export_data = {
            "export_timestamp": time.time(),
            "debug_mode": self.debug_mode,
            "reasoning_chains": [asdict(chain) for chain in self.reasoning_chains],
            "patterns_analysis": self.analyze_reasoning_patterns()
        }

        with open(filename, 'w') as f:
            json.dump(export_data, f, indent=2, default=str)

        return filename


def create_reasoning_transparency_system(debug_mode: bool = False) -> ReasoningTransparencySystem:
    """Factory function to create reasoning transparency system."""
    return ReasoningTransparencySystem(debug_mode=debug_mode)


if __name__ == "__main__":
    # Test the reasoning transparency system
    reasoning_system = create_reasoning_transparency_system(debug_mode=True)

    # Simulate a reasoning chain
    user_input = "I'm really frustrated with this bug but determined to fix it"
    chain_id = reasoning_system.start_reasoning_chain(user_input)

    # Add context detection step
    reasoning_system.add_reasoning_step(
        chain_id=chain_id,
        reasoning_type=ReasoningType.CONTEXT_DETECTION,
        input_data={"text": user_input, "length": len(user_input)},
        logic_applied="Analyzed emotional indicators and intensity markers",
        output_result={"primary_emotion": "frustrated", "intensity": "high", "compound": ["determined"]},
        confidence=0.85
    )

    # Add memory retrieval step
    reasoning_system.add_reasoning_step(
        chain_id=chain_id,
        reasoning_type=ReasoningType.MEMORY_RETRIEVAL,
        input_data={"topic": "programming", "emotion": "frustrated"},
        logic_applied="Retrieved similar past interactions about programming frustration",
        output_result={"pattern": "prefers minimal sass when debugging", "memories": ["mem1", "mem2"]},
        confidence=0.75
    )

    # Add response style step
    reasoning_system.add_reasoning_step(
        chain_id=chain_id,
        reasoning_type=ReasoningType.RESPONSE_STYLE,
        input_data={"emotion": "frustrated", "past_pattern": "minimal sass", "context": "programming"},
        logic_applied="Combined emotion + past pattern + context to select response style",
        output_result="supportive_minimal_sass",
        confidence=0.80
    )

    # Finalize chain
    final_decision = "Use supportive tone with minimal sass to help with debugging"
    chain = reasoning_system.finalize_reasoning_chain(chain_id, final_decision)

    # Generate explanations
    print("=== REASONING TRANSPARENCY DEMO ===\n")

    print("1. DEBUG EXPLANATION:")
    print(reasoning_system.generate_debug_explanation(chain_id))

    print("\n\n2. PATTERN EXPLANATION:")
    print(reasoning_system.generate_pattern_explanation(chain_id, "sass_level_decision"))

    print("\n\n3. CONFIDENCE ANALYSIS:")
    confidence_analysis = reasoning_system.get_confidence_reasoning(chain_id)
    print(json.dumps(confidence_analysis, indent=2))

    print("\n\n4. REASONING PATTERNS ANALYSIS:")
    patterns_analysis = reasoning_system.analyze_reasoning_patterns()
    print(json.dumps(patterns_analysis, indent=2))