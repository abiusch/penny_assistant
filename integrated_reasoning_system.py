#!/usr/bin/env python3
"""
Integrated Reasoning System for Penny
Connects reasoning transparency with enhanced context detection and memory systems
"""

import json
import time
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass

# Import existing systems
from enhanced_context_detector import EnhancedContextDetector, ContextAnalysis
from memory_system import MemoryManager, ConversationTurn, UserPreference
from reasoning_transparency_system import (
    ReasoningTransparencySystem, ReasoningType, create_reasoning_transparency_system
)
from confidence_indicator_engine import (
    ConfidenceIndicatorEngine, ConfidenceContext, UncertaintyType, create_confidence_indicator_engine
)


@dataclass
class IntegratedReasoningResult:
    """Complete reasoning result with transparency and confidence."""
    user_input: str
    context_analysis: ContextAnalysis
    retrieved_memories: List[Any]
    reasoning_explanation: str
    confidence_expression: str
    final_response_style: str
    reasoning_chain_id: str
    overall_confidence: float
    debug_info: Optional[str] = None


class IntegratedReasoningSystem:
    """Integrates all reasoning components for transparent decision-making."""

    def __init__(self, debug_mode: bool = False):
        self.debug_mode = debug_mode

        # Initialize component systems
        self.context_detector = EnhancedContextDetector()
        self.memory_system = MemoryManager()
        self.reasoning_system = create_reasoning_transparency_system(debug_mode)
        self.confidence_engine = create_confidence_indicator_engine()

        # Response style mappings
        self.response_style_mappings = self._load_response_style_mappings()

    def _load_response_style_mappings(self) -> Dict[str, Dict[str, Any]]:
        """Load mappings from context to response styles."""
        return {
            "calm_supportive": {
                "sass_level": "minimal",
                "tone": "supportive",
                "approach": "problem_solving",
                "confidence_expression": "moderate_hedging"
            },
            "enthusiastic_matching": {
                "sass_level": "moderate",
                "tone": "enthusiastic",
                "approach": "energy_matching",
                "confidence_expression": "mild_hedging"
            },
            "professional_structured": {
                "sass_level": "minimal",
                "tone": "professional",
                "approach": "structured",
                "confidence_expression": "factual"
            },
            "empathetic_listening": {
                "sass_level": "none",
                "tone": "empathetic",
                "approach": "listening",
                "confidence_expression": "gentle_hedging"
            },
            "enthusiastic_celebratory": {
                "sass_level": "moderate",
                "tone": "celebratory",
                "approach": "enthusiasm",
                "confidence_expression": "confident"
            },
            "casual_humor": {
                "sass_level": "high",
                "tone": "casual",
                "approach": "humor",
                "confidence_expression": "casual_hedging"
            },
            "balanced_responsive": {
                "sass_level": "moderate",
                "tone": "balanced",
                "approach": "adaptive",
                "confidence_expression": "moderate_hedging"
            }
        }

    def process_user_input(self, user_input: str, session_id: str = None) -> IntegratedReasoningResult:
        """Process user input with full reasoning transparency."""

        # Start reasoning chain
        chain_id = self.reasoning_system.start_reasoning_chain(user_input)

        # Step 1: Enhanced context detection
        context_analysis = self._analyze_context_with_reasoning(user_input, chain_id)

        # Step 2: Memory retrieval based on context
        retrieved_memories = self._retrieve_memories_with_reasoning(
            user_input, context_analysis, chain_id, session_id
        )

        # Step 3: Response style determination
        response_style = self._determine_response_style_with_reasoning(
            context_analysis, retrieved_memories, chain_id
        )

        # Step 4: Confidence assessment
        overall_confidence, confidence_expression = self._assess_confidence_with_reasoning(
            context_analysis, retrieved_memories, response_style, chain_id
        )

        # Finalize reasoning chain
        final_decision = f"Use {response_style} response style with confidence level {overall_confidence:.2f}"
        reasoning_chain = self.reasoning_system.finalize_reasoning_chain(chain_id, final_decision)

        # Generate explanations
        reasoning_explanation = self._generate_reasoning_explanation(chain_id, context_analysis)

        debug_info = None
        if self.debug_mode:
            debug_info = self.reasoning_system.generate_debug_explanation(chain_id)

        return IntegratedReasoningResult(
            user_input=user_input,
            context_analysis=context_analysis,
            retrieved_memories=retrieved_memories,
            reasoning_explanation=reasoning_explanation,
            confidence_expression=confidence_expression,
            final_response_style=response_style,
            reasoning_chain_id=chain_id,
            overall_confidence=overall_confidence,
            debug_info=debug_info
        )

    def _analyze_context_with_reasoning(self, user_input: str, chain_id: str) -> ContextAnalysis:
        """Analyze context with reasoning transparency."""

        # Perform context analysis
        context_analysis = self.context_detector.analyze_comprehensive_context(user_input)

        # Add reasoning step
        self.reasoning_system.add_reasoning_step(
            chain_id=chain_id,
            reasoning_type=ReasoningType.CONTEXT_DETECTION,
            input_data={
                "user_input": user_input,
                "text_length": len(user_input),
                "word_count": len(user_input.split())
            },
            logic_applied=f"Analyzed emotional indicators, topic patterns, and social context cues",
            output_result={
                "primary_emotion": context_analysis.emotion_profile.primary_emotion,
                "intensity": context_analysis.emotion_profile.intensity.value,
                "topic": context_analysis.topic,
                "social_context": context_analysis.social_context,
                "communication_preference": context_analysis.communication_preference
            },
            confidence=context_analysis.inference_confidence
        )

        return context_analysis

    def _retrieve_memories_with_reasoning(self, user_input: str, context_analysis: ContextAnalysis,
                                        chain_id: str, session_id: str = None) -> List[Any]:
        """Retrieve relevant memories with reasoning transparency."""

        # Search for relevant memories based on context
        search_terms = [
            context_analysis.topic,
            context_analysis.emotion_profile.primary_emotion,
            context_analysis.social_context
        ]

        # This would integrate with the actual memory system
        # For now, simulate memory retrieval
        retrieved_memories = self._simulate_memory_retrieval(search_terms, context_analysis)

        # Add reasoning step
        self.reasoning_system.add_reasoning_step(
            chain_id=chain_id,
            reasoning_type=ReasoningType.MEMORY_RETRIEVAL,
            input_data={
                "search_terms": search_terms,
                "emotion": context_analysis.emotion_profile.primary_emotion,
                "topic": context_analysis.topic,
                "social_context": context_analysis.social_context
            },
            logic_applied=f"Searched memories for similar emotional states and topics",
            output_result={
                "memory_count": len(retrieved_memories),
                "patterns_found": [mem.get("pattern", "none") for mem in retrieved_memories],
                "relevance_scores": [mem.get("relevance", 0.5) for mem in retrieved_memories]
            },
            confidence=0.7 if retrieved_memories else 0.3
        )

        return retrieved_memories

    def _determine_response_style_with_reasoning(self, context_analysis: ContextAnalysis,
                                               retrieved_memories: List[Any], chain_id: str) -> str:
        """Determine response style with reasoning transparency."""

        # Start with context-based preference
        base_style = context_analysis.communication_preference

        # Adjust based on memory patterns
        memory_preferences = []
        for memory in retrieved_memories:
            if "preferred_style" in memory:
                memory_preferences.append(memory["preferred_style"])

        # Determine final style
        if memory_preferences:
            # Use most common memory preference if confident enough
            most_common_memory_style = max(set(memory_preferences), key=memory_preferences.count)
            frequency = memory_preferences.count(most_common_memory_style)

            if frequency >= 2:  # Strong pattern
                final_style = most_common_memory_style
                reasoning_logic = f"Memory pattern shows strong preference for {most_common_memory_style} (frequency: {frequency})"
                confidence = 0.8
            else:
                final_style = base_style
                reasoning_logic = f"Insufficient memory pattern, using context-based preference: {base_style}"
                confidence = 0.6
        else:
            final_style = base_style
            reasoning_logic = f"No relevant memory patterns, using context-based preference: {base_style}"
            confidence = 0.5

        # Add reasoning step
        self.reasoning_system.add_reasoning_step(
            chain_id=chain_id,
            reasoning_type=ReasoningType.RESPONSE_STYLE,
            input_data={
                "context_preference": base_style,
                "memory_preferences": memory_preferences,
                "memory_count": len(retrieved_memories)
            },
            logic_applied=reasoning_logic,
            output_result=final_style,
            confidence=confidence
        )

        return final_style

    def _assess_confidence_with_reasoning(self, context_analysis: ContextAnalysis,
                                        retrieved_memories: List[Any], response_style: str,
                                        chain_id: str) -> Tuple[float, str]:
        """Assess overall confidence with reasoning transparency."""

        # Calculate confidence factors
        context_confidence = context_analysis.inference_confidence
        memory_confidence = min(len(retrieved_memories) * 0.2, 0.8) if retrieved_memories else 0.2
        style_confidence = 0.8 if response_style in self.response_style_mappings else 0.4

        # Overall confidence calculation
        overall_confidence = (context_confidence * 0.4 + memory_confidence * 0.3 + style_confidence * 0.3)

        # Create confidence context
        confidence_context = ConfidenceContext(
            topic=context_analysis.topic,
            social_setting=context_analysis.social_context,
            relationship_familiarity=min(len(retrieved_memories) * 0.1, 1.0),
            conversation_stakes="medium",  # Would be determined dynamically
            past_accuracy=0.75  # Would be calculated from history
        )

        # Generate confidence expression
        confidence_expression_obj = self.confidence_engine.generate_confidence_expression(
            overall_confidence,
            f"this approach ({response_style}) will work well",
            confidence_context,
            UncertaintyType.PREFERENCE
        )

        confidence_expression = confidence_expression_obj.expression

        # Add reasoning step
        self.reasoning_system.add_reasoning_step(
            chain_id=chain_id,
            reasoning_type=ReasoningType.CONFIDENCE_ASSESSMENT,
            input_data={
                "context_confidence": context_confidence,
                "memory_confidence": memory_confidence,
                "style_confidence": style_confidence
            },
            logic_applied=f"Weighted combination: context({context_confidence:.2f}) * 0.4 + memory({memory_confidence:.2f}) * 0.3 + style({style_confidence:.2f}) * 0.3",
            output_result={
                "overall_confidence": overall_confidence,
                "confidence_expression": confidence_expression,
                "expression_type": confidence_expression_obj.confidence_level.value
            },
            confidence=overall_confidence
        )

        return overall_confidence, confidence_expression

    def _simulate_memory_retrieval(self, search_terms: List[str], context_analysis: ContextAnalysis) -> List[Dict[str, Any]]:
        """Simulate memory retrieval for demonstration."""
        # This would integrate with the actual memory system

        simulated_memories = []

        # Simulate based on emotion and topic
        if context_analysis.emotion_profile.primary_emotion == "frustrated" and context_analysis.topic == "programming":
            simulated_memories.append({
                "pattern": "prefers minimal sass when debugging",
                "preferred_style": "calm_supportive",
                "relevance": 0.9,
                "timestamp": time.time() - 3600,  # 1 hour ago
                "context": "debugging session"
            })
            simulated_memories.append({
                "pattern": "responds well to structured help",
                "preferred_style": "professional_structured",
                "relevance": 0.7,
                "timestamp": time.time() - 7200,  # 2 hours ago
                "context": "coding problem"
            })

        elif context_analysis.emotion_profile.primary_emotion == "excited":
            simulated_memories.append({
                "pattern": "enjoys matching enthusiasm",
                "preferred_style": "enthusiastic_matching",
                "relevance": 0.8,
                "timestamp": time.time() - 1800,  # 30 minutes ago
                "context": "celebration"
            })

        return simulated_memories

    def _generate_reasoning_explanation(self, chain_id: str, context_analysis: ContextAnalysis) -> str:
        """Generate human-readable reasoning explanation."""

        # Use pattern-based explanation
        pattern_explanation = self.reasoning_system.generate_pattern_explanation(
            chain_id, "sass_level_decision"
        )

        if pattern_explanation and not pattern_explanation.startswith("Missing"):
            return pattern_explanation

        # Fallback to general explanation
        return f"Detected {context_analysis.emotion_profile.primary_emotion} emotion with {context_analysis.emotion_profile.intensity.value} intensity in {context_analysis.social_context} context → chose {context_analysis.communication_preference} approach"

    def explain_decision(self, result: IntegratedReasoningResult) -> str:
        """Generate comprehensive explanation of the decision-making process."""

        explanation_parts = []

        explanation_parts.append("💭 **How I made this decision:**")
        explanation_parts.append(f"   {result.reasoning_explanation}")

        if result.retrieved_memories:
            explanation_parts.append(f"\n🧠 **Memory insights:** Found {len(result.retrieved_memories)} relevant past interactions")

        explanation_parts.append(f"\n🎯 **Confidence:** {result.confidence_expression}")

        if result.overall_confidence < 0.6:
            explanation_parts.append("\n❓ **Note:** I'm not entirely sure about this - let me know if I'm misreading the situation!")

        return "\n".join(explanation_parts)

    def get_reasoning_stats(self) -> Dict[str, Any]:
        """Get statistics about reasoning patterns."""
        return {
            "reasoning_patterns": self.reasoning_system.analyze_reasoning_patterns(),
            "confidence_stats": self.confidence_engine.get_confidence_stats(),
            "memory_retrieval_success_rate": 0.75,  # Would be calculated dynamically
            "average_reasoning_steps": 4.2  # Would be calculated dynamically
        }


def create_integrated_reasoning_system(debug_mode: bool = False) -> IntegratedReasoningSystem:
    """Factory function to create integrated reasoning system."""
    return IntegratedReasoningSystem(debug_mode=debug_mode)


if __name__ == "__main__":
    # Test the integrated reasoning system
    reasoning_system = create_integrated_reasoning_system(debug_mode=True)

    test_inputs = [
        "I'm really frustrated with this bug but determined to fix it",
        "Josh is being weird about the project deadline and it's making me anxious",
        "Super excited about the new feature launch!",
        "I need help with this API integration"
    ]

    print("=== INTEGRATED REASONING SYSTEM DEMO ===\n")

    for i, user_input in enumerate(test_inputs, 1):
        print(f"{i}. Processing: '{user_input}'")
        print("=" * 60)

        # Process input
        result = reasoning_system.process_user_input(user_input, f"session_{i}")

        # Show results
        print(f"Response Style: {result.final_response_style}")
        print(f"Overall Confidence: {result.overall_confidence:.2f}")
        print(f"Reasoning: {result.reasoning_explanation}")
        print(f"Confidence Expression: {result.confidence_expression}")

        # Show explanation
        print("\n" + reasoning_system.explain_decision(result))

        if result.debug_info:
            print(f"\n📊 DEBUG INFO:\n{result.debug_info}")

        print("\n" + "="*60 + "\n")