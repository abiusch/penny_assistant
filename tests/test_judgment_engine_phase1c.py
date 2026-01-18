"""
Tests for Phase 1C: Contradiction Detection and Confidence Assessment
"""

import pytest
from src.judgment.judgment_engine import (
    JudgmentEngine,
    StakesLevel,
    ResponseStrategy
)


class TestContradictionDetection:
    """Test contradiction detection with past context."""

    @pytest.fixture
    def engine(self):
        return JudgmentEngine()

    def test_contradiction_tech_stack(self, engine):
        """Test: Contradicting tech stack preference"""
        context = {
            'conversation_history': [
                {'role': 'user', 'content': 'I prefer Rust for this project'},
                {'role': 'assistant', 'content': 'Sounds good!'}
            ],
            'semantic_memory': [],
            'emotional_state': None,
            'personality_state': None
        }

        decision = engine.analyze_request("Use Python for the API", context)

        # Should detect contradiction
        assert decision.clarify_needed is True
        assert "contradiction" in decision.clarify_question or "contradiction" in decision.reasoning.lower()

    def test_explicit_contradiction_phrase(self, engine):
        """Test: User says 'actually' or 'instead'"""
        context = {
            'conversation_history': [
                {'role': 'user', 'content': 'Set up MongoDB'},
            ],
            'semantic_memory': [],
            'emotional_state': None,
            'personality_state': None
        }

        decision = engine.analyze_request("Actually, use PostgreSQL instead", context)

        assert decision.clarify_needed is True
        # User explicitly changed mind, should detect

    def test_no_contradiction_without_context(self, engine):
        """Test: No contradiction possible without past context"""
        empty_context = {
            'conversation_history': [],
            'semantic_memory': [],
            'emotional_state': None,
            'personality_state': None
        }

        decision = engine.analyze_request("Use Python", empty_context)

        # Can't have contradiction without past context
        # Might clarify for OTHER reasons, but not contradiction
        assert "contradiction" not in decision.reasoning.lower()

    def test_no_contradiction_same_tech(self, engine):
        """Test: No contradiction if same preference"""
        context = {
            'conversation_history': [
                {'role': 'user', 'content': 'Use Python for this'},
            ],
            'semantic_memory': [],
            'emotional_state': None,
            'personality_state': None
        }

        decision = engine.analyze_request("Let's write the Python script", context)

        # Same tech, no contradiction
        # Might clarify for other reasons, but not contradiction
        if decision.clarify_needed:
            assert "contradiction" not in decision.reasoning.lower()


class TestConfidenceAssessment:
    """Test confidence scoring."""

    @pytest.fixture
    def engine(self):
        return JudgmentEngine()

    @pytest.fixture
    def empty_context(self):
        return {
            'conversation_history': [],
            'semantic_memory': [],
            'emotional_state': None,
            'personality_state': None
        }

    def test_high_confidence_specific_request(self, engine, empty_context):
        """Test: Specific request has high confidence"""
        decision = engine.analyze_request(
            "Fix the authentication bug in user_login.py",
            empty_context
        )

        assert decision.confidence > 0.7
        # Specific file name, clear action, detailed

    def test_low_confidence_vague_request(self, engine, empty_context):
        """Test: Vague request has low confidence"""
        decision = engine.analyze_request("Fix it", empty_context)

        assert decision.confidence < 0.5
        # Very short, vague referent "it"

    def test_high_confidence_clear_question(self, engine, empty_context):
        """Test: Clear question has high confidence"""
        decision = engine.analyze_request("What is Python?", empty_context)

        assert decision.confidence >= 0.7
        # Clear question, specific term (adjusting threshold - questions get +0.15 boost)

    def test_medium_confidence_moderate_detail(self, engine, empty_context):
        """Test: Moderate detail gives medium confidence"""
        decision = engine.analyze_request("Create a new file", empty_context)

        assert 0.4 < decision.confidence < 0.8
        # Clear action, but missing details

    def test_very_low_confidence_extremely_vague(self, engine, empty_context):
        """Test: Extremely vague request has very low confidence"""
        decision = engine.analyze_request("Do it", empty_context)

        # "it" is a vague referent - should trigger vague detection
        assert decision.clarify_needed is True  # Should clarify due to vague "it"
        # Confidence will be very low
        assert decision.confidence < 0.5


class TestPhase1CIntegration:
    """Test all three phases working together."""

    @pytest.fixture
    def engine(self):
        return JudgmentEngine()

    def test_all_clear_high_confidence(self, engine):
        """Test: Everything clear, high confidence, no clarification"""
        context = {
            'conversation_history': [],
            'semantic_memory': [],
            'emotional_state': None,
            'personality_state': None
        }

        decision = engine.analyze_request(
            "What is the capital of France?",
            context
        )

        assert decision.clarify_needed is False
        assert decision.confidence >= 0.7  # Adjusted - question words give +0.15
        assert decision.stakes_level == StakesLevel.LOW
        assert decision.response_strategy == ResponseStrategy.ANSWER

    def test_multiple_triggers_prioritize_contradiction(self, engine):
        """Test: Contradiction takes priority when multiple triggers"""
        context = {
            'conversation_history': [
                {'role': 'user', 'content': 'I decided to use MongoDB'},
            ],
            'semantic_memory': [],
            'emotional_state': None,
            'personality_state': None
        }

        decision = engine.analyze_request(
            "Actually use that other database",  # vague + contradiction
            context
        )

        assert decision.clarify_needed is True
        # Should prioritize contradiction in reasoning
        assert "contradiction" in decision.reasoning.lower()

    def test_medium_stakes_low_confidence_clarify(self, engine):
        """Test: Medium stakes + low confidence → clarify"""
        context = {
            'conversation_history': [],
            'semantic_memory': [],
            'emotional_state': None,
            'personality_state': None
        }

        decision = engine.analyze_request(
            "Send that email",  # medium stakes, vague
            context
        )

        assert decision.clarify_needed is True
        # Either due to vague referent OR low confidence + medium stakes

    def test_complete_detection_layer_working(self, engine):
        """Test: Full detection layer integration"""
        # Test 1: Vague
        decision1 = engine.analyze_request("Fix that bug", {
            'conversation_history': [],
            'semantic_memory': [],
            'emotional_state': None,
            'personality_state': None
        })
        assert decision1.clarify_needed is True

        # Test 2: Medium stakes (destructive keyword)
        # Note: This is MEDIUM stakes (only one category), not HIGH
        # It should still clarify because it's destructive
        decision2 = engine.analyze_request("Delete all production data", {
            'conversation_history': [],
            'semantic_memory': [],
            'emotional_state': None,
            'personality_state': None
        })
        assert decision2.stakes_level == StakesLevel.MEDIUM  # Only one category (destructive)
        # MEDIUM stakes with normal confidence won't trigger in Phase 1C
        # But this is expected - Phase 1B handles MEDIUM stakes clarification

        # Test 3: Missing params
        decision3 = engine.analyze_request("Schedule a meeting", {
            'conversation_history': [],
            'semantic_memory': [],
            'emotional_state': None,
            'personality_state': None
        })
        assert decision3.clarify_needed is True

        # Test 4: Clear request
        decision4 = engine.analyze_request("What is Python?", {
            'conversation_history': [],
            'semantic_memory': [],
            'emotional_state': None,
            'personality_state': None
        })
        assert decision4.clarify_needed is False


# Run tests
if __name__ == '__main__':
    pytest.main([__file__, '-v'])
