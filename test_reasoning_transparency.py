#!/usr/bin/env python3
"""
Testing Framework for Reasoning Transparency System
Comprehensive tests for reasoning explanations, confidence indicators, and integration
"""

import pytest
import json
import time
from typing import Dict, List, Any
from unittest.mock import Mock, patch

# Import systems to test
from reasoning_transparency_system import (
    ReasoningTransparencySystem, ReasoningType, ReasoningChain, ReasoningStep
)
from confidence_indicator_engine import (
    ConfidenceIndicatorEngine, ConfidenceLevel, UncertaintyType, ConfidenceContext
)
from integrated_reasoning_system import IntegratedReasoningSystem


class TestReasoningTransparencySystem:
    """Test suite for the reasoning transparency system."""

    def setup_method(self):
        """Set up test fixtures."""
        self.reasoning_system = ReasoningTransparencySystem(debug_mode=True)

    def test_start_reasoning_chain(self):
        """Test starting a new reasoning chain."""
        user_input = "I'm frustrated with this bug"
        chain_id = self.reasoning_system.start_reasoning_chain(user_input)

        assert chain_id is not None
        assert chain_id.startswith("chain_")
        assert len(self.reasoning_system.reasoning_chains) == 1

        chain = self.reasoning_system.reasoning_chains[0]
        assert chain.user_input == user_input
        assert chain.debug_mode is True
        assert len(chain.reasoning_steps) == 0

    def test_add_reasoning_step(self):
        """Test adding reasoning steps."""
        chain_id = self.reasoning_system.start_reasoning_chain("test input")

        self.reasoning_system.add_reasoning_step(
            chain_id=chain_id,
            reasoning_type=ReasoningType.CONTEXT_DETECTION,
            input_data={"emotion": "frustrated", "intensity": "high"},
            logic_applied="Detected frustration from language patterns",
            output_result={"primary_emotion": "frustrated"},
            confidence=0.8
        )

        chain = self.reasoning_system._get_chain(chain_id)
        assert len(chain.reasoning_steps) == 1

        step = chain.reasoning_steps[0]
        assert step.reasoning_type == ReasoningType.CONTEXT_DETECTION
        assert step.confidence == 0.8
        assert step.output_result["primary_emotion"] == "frustrated"

    def test_finalize_reasoning_chain(self):
        """Test finalizing a reasoning chain."""
        chain_id = self.reasoning_system.start_reasoning_chain("test input")

        # Add some steps
        self.reasoning_system.add_reasoning_step(
            chain_id, ReasoningType.CONTEXT_DETECTION, {}, "logic", {}, 0.8
        )
        self.reasoning_system.add_reasoning_step(
            chain_id, ReasoningType.MEMORY_RETRIEVAL, {}, "logic", {}, 0.6
        )

        final_decision = "Use supportive tone"
        chain = self.reasoning_system.finalize_reasoning_chain(chain_id, final_decision)

        assert chain.final_decision == final_decision
        assert chain.overall_confidence == 0.7  # Average of 0.8 and 0.6

    def test_generate_debug_explanation(self):
        """Test generating debug explanations."""
        chain_id = self.reasoning_system.start_reasoning_chain("I'm frustrated")

        self.reasoning_system.add_reasoning_step(
            chain_id, ReasoningType.CONTEXT_DETECTION,
            {"text": "I'm frustrated"}, "Analyzed emotion words",
            {"emotion": "frustrated"}, 0.9
        )

        self.reasoning_system.finalize_reasoning_chain(chain_id, "Use calm tone")

        explanation = self.reasoning_system.generate_debug_explanation(chain_id)

        assert "🧠 Reasoning for: 'I'm frustrated'" in explanation
        assert "CONTEXT_DETECTION" in explanation
        assert "emotion" in explanation
        assert "Overall Confidence: 0.90" in explanation

    def test_pattern_explanation(self):
        """Test pattern-based explanations."""
        chain_id = self.reasoning_system.start_reasoning_chain("test")

        # Add steps that match sass_level_decision pattern
        self.reasoning_system.add_reasoning_step(
            chain_id, ReasoningType.CONTEXT_DETECTION, {},
            "logic", {"primary_emotion": "frustrated", "intensity": "high"}, 0.8
        )
        self.reasoning_system.add_reasoning_step(
            chain_id, ReasoningType.MEMORY_RETRIEVAL, {},
            "logic", {"pattern": "minimal sass"}, 0.7
        )
        self.reasoning_system.add_reasoning_step(
            chain_id, ReasoningType.RESPONSE_STYLE, {},
            "logic", "minimal_sass", 0.8
        )

        explanation = self.reasoning_system.generate_pattern_explanation(
            chain_id, "sass_level_decision"
        )

        # Should contain pattern elements
        assert "frustrated" in explanation
        assert "high" in explanation
        assert "minimal sass" in explanation or "minimal_sass" in explanation

    def test_confidence_reasoning(self):
        """Test confidence reasoning analysis."""
        chain_id = self.reasoning_system.start_reasoning_chain("test")

        self.reasoning_system.add_reasoning_step(
            chain_id, ReasoningType.CONTEXT_DETECTION, {}, "logic", {}, 0.9
        )
        self.reasoning_system.add_reasoning_step(
            chain_id, ReasoningType.MEMORY_RETRIEVAL, {}, "logic", {}, 0.6
        )

        self.reasoning_system.finalize_reasoning_chain(chain_id, "test decision")

        confidence_analysis = self.reasoning_system.get_confidence_reasoning(chain_id)

        assert "overall_confidence" in confidence_analysis
        assert "confidence_explanation" in confidence_analysis
        assert "step_confidences" in confidence_analysis
        assert len(confidence_analysis["step_confidences"]) == 2


class TestConfidenceIndicatorEngine:
    """Test suite for the confidence indicator engine."""

    def setup_method(self):
        """Set up test fixtures."""
        self.confidence_engine = ConfidenceIndicatorEngine()

    def test_assess_confidence_level(self):
        """Test confidence level assessment."""
        assert self.confidence_engine.assess_confidence_level(0.95) == ConfidenceLevel.VERY_HIGH
        assert self.confidence_engine.assess_confidence_level(0.8) == ConfidenceLevel.HIGH
        assert self.confidence_engine.assess_confidence_level(0.6) == ConfidenceLevel.MODERATE
        assert self.confidence_engine.assess_confidence_level(0.3) == ConfidenceLevel.LOW
        assert self.confidence_engine.assess_confidence_level(0.1) == ConfidenceLevel.VERY_LOW

    def test_determine_uncertainty_type(self):
        """Test uncertainty type determination."""
        assert self.confidence_engine.determine_uncertainty_type(
            {"content": "you're feeling sad"}
        ) == UncertaintyType.EMOTIONAL

        assert self.confidence_engine.determine_uncertainty_type(
            {"content": "you might prefer this"}
        ) == UncertaintyType.PREFERENCE

        assert self.confidence_engine.determine_uncertainty_type(
            {"content": "this will happen"}
        ) == UncertaintyType.PREDICTION

    def test_generate_confidence_expression(self):
        """Test confidence expression generation."""
        context = ConfidenceContext(
            topic="programming",
            social_setting="casual_chat",
            relationship_familiarity=0.8,
            conversation_stakes="low",
            past_accuracy=0.7
        )

        expression = self.confidence_engine.generate_confidence_expression(
            confidence_score=0.6,
            content="you're frustrated with debugging",
            context=context,
            uncertainty_type=UncertaintyType.EMOTIONAL
        )

        assert expression.confidence_level == ConfidenceLevel.MODERATE
        assert expression.uncertainty_type == UncertaintyType.EMOTIONAL
        assert "you're frustrated with debugging" in expression.expression

    def test_express_uncertainty(self):
        """Test uncertainty expression."""
        context = ConfidenceContext(
            topic="programming",
            social_setting="problem_solving",
            relationship_familiarity=0.5,
            conversation_stakes="medium",
            past_accuracy=0.6
        )

        result = self.confidence_engine.express_uncertainty(
            confidence_score=0.4,
            content="the bug is in the authentication module",
            context=context,
            include_alternatives=True
        )

        assert isinstance(result, str)
        assert len(result) > 0
        # Should contain some uncertainty indicators for low confidence
        uncertainty_indicators = ["not sure", "maybe", "could be", "might", "think"]
        assert any(indicator in result.lower() for indicator in uncertainty_indicators)

    def test_calibrate_confidence_expression(self):
        """Test confidence calibration."""
        context = ConfidenceContext(
            topic="test", social_setting="casual_chat",
            relationship_familiarity=0.5, conversation_stakes="low",
            past_accuracy=0.7
        )

        # Test when stated confidence was too high
        calibration = self.confidence_engine.calibrate_confidence_expression(
            stated_confidence=0.9,
            actual_confidence=0.5,
            context=context
        )

        assert calibration["accuracy_gap"] == 0.4
        assert calibration["confidence_adjustment"] < 0  # Should reduce confidence
        assert "more uncertainty" in calibration["recommendation"].lower()


class TestIntegratedReasoningSystem:
    """Test suite for the integrated reasoning system."""

    def setup_method(self):
        """Set up test fixtures."""
        self.integrated_system = IntegratedReasoningSystem(debug_mode=True)

    def test_process_user_input_basic(self):
        """Test basic user input processing."""
        user_input = "I'm frustrated with this bug"
        result = self.integrated_system.process_user_input(user_input)

        assert result.user_input == user_input
        assert result.context_analysis is not None
        assert result.final_response_style is not None
        assert 0 <= result.overall_confidence <= 1
        assert result.reasoning_explanation is not None
        assert result.confidence_expression is not None

    def test_context_analysis_integration(self):
        """Test that context analysis is properly integrated."""
        user_input = "I'm really excited about this new feature!"
        result = self.integrated_system.process_user_input(user_input)

        # Should detect positive emotion
        assert result.context_analysis.emotion_profile.primary_emotion == "excited"
        # Response style should match the positive emotion
        assert "enthusiastic" in result.final_response_style or "celebratory" in result.final_response_style

    def test_memory_integration(self):
        """Test memory retrieval integration."""
        user_input = "I'm frustrated with debugging this code"
        result = self.integrated_system.process_user_input(user_input)

        # Should retrieve some memories (simulated)
        assert isinstance(result.retrieved_memories, list)
        # For programming + frustrated, should get supportive style
        assert "supportive" in result.final_response_style or "calm" in result.final_response_style

    def test_confidence_expression_integration(self):
        """Test confidence expression integration."""
        user_input = "I need help with something"
        result = self.integrated_system.process_user_input(user_input)

        # Should have a confidence expression
        assert result.confidence_expression is not None
        assert len(result.confidence_expression) > 0

        # Low confidence should include uncertainty language
        if result.overall_confidence < 0.5:
            uncertainty_words = ["not sure", "maybe", "think", "might", "could"]
            assert any(word in result.confidence_expression.lower() for word in uncertainty_words)

    def test_debug_mode(self):
        """Test debug mode functionality."""
        user_input = "Test debug mode"
        result = self.integrated_system.process_user_input(user_input)

        # Debug mode should provide debug info
        assert result.debug_info is not None
        assert "🧠 Reasoning for:" in result.debug_info

    def test_explain_decision(self):
        """Test decision explanation generation."""
        user_input = "I'm confused about this error"
        result = self.integrated_system.process_user_input(user_input)

        explanation = self.integrated_system.explain_decision(result)

        assert "💭 **How I made this decision:**" in explanation
        assert result.reasoning_explanation in explanation
        assert "🎯 **Confidence:**" in explanation


class TestReasoningQuality:
    """Test suite for reasoning quality and consistency."""

    def setup_method(self):
        """Set up test fixtures."""
        self.integrated_system = IntegratedReasoningSystem(debug_mode=True)

    def test_reasoning_consistency(self):
        """Test that similar inputs produce consistent reasoning."""
        similar_inputs = [
            "I'm frustrated with this bug",
            "This bug is really frustrating me",
            "I'm getting frustrated trying to fix this"
        ]

        results = []
        for input_text in similar_inputs:
            result = self.integrated_system.process_user_input(input_text)
            results.append(result)

        # Should all detect frustration
        for result in results:
            assert result.context_analysis.emotion_profile.primary_emotion == "frustrated"

        # Should all use similar response styles
        response_styles = [result.final_response_style for result in results]
        # Most should be the same or similar (allowing some variation)
        unique_styles = set(response_styles)
        assert len(unique_styles) <= 2  # At most 2 different styles

    def test_confidence_appropriateness(self):
        """Test that confidence levels are appropriate."""
        test_cases = [
            ("I'm frustrated", 0.6),  # Clear emotion, should be confident
            ("Maybe I'm feeling something", 0.4),  # Uncertain, should be less confident
            ("Not sure what's happening", 0.3),  # Very uncertain
            ("I'm definitely excited!", 0.8),  # Very clear, should be confident
        ]

        for user_input, expected_min_confidence in test_cases:
            result = self.integrated_system.process_user_input(user_input)

            if expected_min_confidence > 0.6:
                assert result.overall_confidence >= expected_min_confidence
            else:
                # For uncertain inputs, confidence should be appropriately low
                assert result.overall_confidence <= expected_min_confidence + 0.2

    def test_reasoning_transparency_completeness(self):
        """Test that reasoning transparency provides complete information."""
        user_input = "I need help with this project"
        result = self.integrated_system.process_user_input(user_input)

        # Should have all required components
        assert result.context_analysis is not None
        assert result.reasoning_explanation is not None
        assert result.confidence_expression is not None
        assert result.final_response_style is not None

        # Debug info should show reasoning steps
        assert result.debug_info is not None
        assert "CONTEXT_DETECTION" in result.debug_info
        assert "MEMORY_RETRIEVAL" in result.debug_info
        assert "RESPONSE_STYLE" in result.debug_info
        assert "CONFIDENCE_ASSESSMENT" in result.debug_info


def run_reasoning_transparency_tests():
    """Run all reasoning transparency tests."""
    print("🧪 Running Reasoning Transparency Tests...\n")

    # Test basic functionality
    test_reasoning = TestReasoningTransparencySystem()
    test_reasoning.setup_method()

    try:
        test_reasoning.test_start_reasoning_chain()
        print("✅ Reasoning chain creation - PASSED")

        test_reasoning.test_add_reasoning_step()
        print("✅ Adding reasoning steps - PASSED")

        test_reasoning.test_generate_debug_explanation()
        print("✅ Debug explanation generation - PASSED")

    except Exception as e:
        print(f"❌ Reasoning transparency test failed: {e}")

    # Test confidence engine
    test_confidence = TestConfidenceIndicatorEngine()
    test_confidence.setup_method()

    try:
        test_confidence.test_assess_confidence_level()
        print("✅ Confidence level assessment - PASSED")

        test_confidence.test_express_uncertainty()
        print("✅ Uncertainty expression - PASSED")

    except Exception as e:
        print(f"❌ Confidence engine test failed: {e}")

    # Test integration
    test_integration = TestIntegratedReasoningSystem()
    test_integration.setup_method()

    try:
        test_integration.test_process_user_input_basic()
        print("✅ Basic integration processing - PASSED")

        test_integration.test_explain_decision()
        print("✅ Decision explanation - PASSED")

    except Exception as e:
        print(f"❌ Integration test failed: {e}")

    # Test quality
    test_quality = TestReasoningQuality()
    test_quality.setup_method()

    try:
        test_quality.test_reasoning_consistency()
        print("✅ Reasoning consistency - PASSED")

        test_quality.test_reasoning_transparency_completeness()
        print("✅ Transparency completeness - PASSED")

    except Exception as e:
        print(f"❌ Quality test failed: {e}")

    print("\n🎉 All tests completed!")


if __name__ == "__main__":
    run_reasoning_transparency_tests()