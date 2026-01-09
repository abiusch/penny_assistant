"""
Tests for Phase 1A: Vague Referent Detection
"""

import pytest
from src.judgment.judgment_engine import (
    JudgmentEngine,
    Decision,
    StakesLevel,
    ResponseStrategy
)


class TestVagueReferentDetection:
    """Test vague referent detection specifically."""

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

    def test_detect_vague_that_thing(self, engine, empty_context):
        """Test: 'Fix that thing' triggers clarification"""
        decision = engine.analyze_request("Fix that thing", empty_context)

        assert decision.clarify_needed is True
        assert decision.response_strategy == ResponseStrategy.CLARIFY
        assert "Vague referent" in decision.reasoning
        assert decision.confidence < 0.5

    def test_detect_vague_it(self, engine, empty_context):
        """Test: 'Delete it' triggers clarification"""
        decision = engine.analyze_request("Delete it", empty_context)

        assert decision.clarify_needed is True
        assert decision.response_strategy == ResponseStrategy.CLARIFY

    def test_clear_with_specific_noun(self, engine, empty_context):
        """Test: 'Fix the authentication bug' does NOT trigger clarification"""
        decision = engine.analyze_request(
            "Fix the authentication bug",
            empty_context
        )

        assert decision.clarify_needed is False
        assert decision.response_strategy == ResponseStrategy.ANSWER
        assert decision.confidence > 0.7

    def test_clear_with_file_name(self, engine, empty_context):
        """Test: 'Delete test_file.py' does NOT trigger clarification"""
        decision = engine.analyze_request(
            "Delete test_file.py",
            empty_context
        )

        assert decision.clarify_needed is False
        assert decision.response_strategy == ResponseStrategy.ANSWER

    def test_vague_this_without_context(self, engine, empty_context):
        """Test: 'Update this' triggers clarification"""
        decision = engine.analyze_request("Update this", empty_context)

        assert decision.clarify_needed is True

    def test_intent_extraction_fix(self, engine, empty_context):
        """Test: Intent correctly identified as 'fix_issue'"""
        decision = engine.analyze_request("Fix that thing", empty_context)

        assert decision.intent == 'fix_issue'

    def test_intent_extraction_delete(self, engine, empty_context):
        """Test: Intent correctly identified as 'delete_something'"""
        decision = engine.analyze_request("Delete it", empty_context)

        assert decision.intent == 'delete_something'

    def test_clarifying_question_generated(self, engine, empty_context):
        """Test: Clarifying question is generated for vague input"""
        decision = engine.analyze_request("Fix that", empty_context)

        assert decision.clarify_question is not None
        assert "clarify_referent" in decision.clarify_question


class TestJudgmentEngineBasics:
    """Test basic Decision structure and engine initialization."""

    def test_engine_initializes(self):
        """Test: Engine initializes without errors"""
        engine = JudgmentEngine()
        assert engine is not None
        assert len(engine.vague_referents) > 0

    def test_decision_structure(self):
        """Test: Decision dataclass has all required fields"""
        decision = Decision(
            intent="test",
            stakes_level=StakesLevel.LOW,
            clarify_needed=False,
            clarify_question=None,
            response_strategy=ResponseStrategy.ANSWER,
            confidence=0.8,
            reasoning="Test"
        )

        assert decision.intent == "test"
        assert decision.stakes_level == StakesLevel.LOW
        assert decision.clarify_needed is False
        assert decision.response_strategy == ResponseStrategy.ANSWER
        assert decision.confidence == 0.8


# Run tests
if __name__ == '__main__':
    pytest.main([__file__, '-v'])
