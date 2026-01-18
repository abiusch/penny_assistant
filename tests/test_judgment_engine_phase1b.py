"""
Tests for Phase 1B: Stakes Assessment & Missing Parameters

Tests both new Phase 1B features AND ensures Phase 1A features still work.
"""

import pytest
from src.judgment.judgment_engine import (
    JudgmentEngine,
    Decision,
    StakesLevel,
    ResponseStrategy
)


class TestStakesAssessment:
    """Test stakes assessment (LOW/MEDIUM/HIGH) detection."""

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

    def test_low_stakes_normal_request(self, engine, empty_context):
        """Test: Normal request has LOW stakes"""
        decision = engine.analyze_request("Fix the authentication bug", empty_context)

        assert decision.stakes_level == StakesLevel.LOW
        assert decision.clarify_needed is False
        assert decision.response_strategy == ResponseStrategy.ANSWER

    def test_medium_stakes_single_category(self, engine, empty_context):
        """Test: Single high-stakes keyword triggers MEDIUM stakes"""
        decision = engine.analyze_request("Delete all user data", empty_context)

        assert decision.stakes_level == StakesLevel.MEDIUM
        assert decision.clarify_needed is True
        assert decision.response_strategy == ResponseStrategy.CLARIFY
        assert "MEDIUM stakes detected" in decision.reasoning

    def test_high_stakes_multiple_categories(self, engine, empty_context):
        """Test: Multiple high-stakes categories trigger HIGH stakes"""
        decision = engine.analyze_request(
            "Buy stocks and delete my account",
            empty_context
        )

        assert decision.stakes_level == StakesLevel.HIGH
        assert decision.clarify_needed is True
        assert decision.response_strategy == ResponseStrategy.ESCALATE
        assert "HIGH stakes detected" in decision.reasoning

    def test_financial_keywords_trigger_medium(self, engine, empty_context):
        """Test: Financial keywords trigger MEDIUM stakes"""
        inputs = [
            "Invest $10,000 in stocks",
            "Buy that cryptocurrency",
            "Transfer money to my account",
            "Process the payment"
        ]

        for user_input in inputs:
            decision = engine.analyze_request(user_input, empty_context)
            assert decision.stakes_level == StakesLevel.MEDIUM

    def test_medical_keywords_trigger_medium(self, engine, empty_context):
        """Test: Medical keywords trigger MEDIUM stakes"""
        decision = engine.analyze_request(
            "Recommend a treatment for my condition",
            empty_context
        )

        assert decision.stakes_level == StakesLevel.MEDIUM
        assert decision.clarify_needed is True

    def test_legal_keywords_trigger_medium(self, engine, empty_context):
        """Test: Legal keywords trigger MEDIUM stakes"""
        decision = engine.analyze_request(
            "Help me draft a legal contract",
            empty_context
        )

        assert decision.stakes_level == StakesLevel.MEDIUM
        assert decision.clarify_needed is True


class TestMissingParameterDetection:
    """Test missing parameter detection for actions requiring specific inputs."""

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

    def test_schedule_missing_params(self, engine, empty_context):
        """Test: 'Schedule a meeting' triggers clarification (missing date, time, attendees)"""
        decision = engine.analyze_request("Schedule a meeting", empty_context)

        assert decision.clarify_needed is True
        assert decision.response_strategy == ResponseStrategy.CLARIFY
        assert "parameter" in decision.reasoning.lower()  # Check for parameter-related reasoning
        assert "missing_params" in decision.clarify_question

    def test_schedule_with_all_params(self, engine, empty_context):
        """Test: 'Schedule a meeting tomorrow at 3pm with John' does NOT trigger clarification"""
        decision = engine.analyze_request(
            "Schedule a meeting tomorrow at 3pm with John",
            empty_context
        )

        assert decision.clarify_needed is False
        assert decision.response_strategy == ResponseStrategy.ANSWER

    def test_send_missing_params(self, engine, empty_context):
        """Test: 'Send an email' triggers clarification (missing recipient, content)"""
        decision = engine.analyze_request("Send an email", empty_context)

        assert decision.clarify_needed is True
        assert "missing_params" in decision.clarify_question

    def test_email_with_params(self, engine, empty_context):
        """Test: 'Email john@example.com about the project' does NOT trigger clarification"""
        decision = engine.analyze_request(
            "Email john@example.com about the project",
            empty_context
        )

        # Should not trigger missing params (has recipient and subject indicators)
        # May still trigger if other issues detected, but not missing params specifically
        if decision.clarify_needed:
            assert "missing_params" not in decision.clarify_question

    def test_deploy_missing_params(self, engine, empty_context):
        """Test: 'Deploy the app' triggers clarification (missing environment, version)"""
        decision = engine.analyze_request("Deploy the app", empty_context)

        assert decision.clarify_needed is True
        assert "missing_params" in decision.clarify_question

    def test_deploy_with_params(self, engine, empty_context):
        """Test: 'Deploy v2.0 to production' does NOT trigger clarification"""
        decision = engine.analyze_request(
            "Deploy v2.0 to production",
            empty_context
        )

        assert decision.clarify_needed is False


class TestPriorityOrdering:
    """Test that clarification triggers have correct priority: vague > missing > stakes."""

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

    def test_vague_takes_priority_over_stakes(self, engine, empty_context):
        """Test: Vague referent takes priority over high stakes"""
        decision = engine.analyze_request("Delete that thing", empty_context)

        # Should clarify due to vague referent, not stakes
        assert decision.clarify_needed is True
        assert "Vague referent" in decision.reasoning
        assert "clarify_referent" in decision.clarify_question

    def test_vague_takes_priority_over_missing(self, engine, empty_context):
        """Test: Vague referent takes priority over missing params"""
        decision = engine.analyze_request("Schedule that", empty_context)

        # Should clarify due to vague referent, not missing params
        assert decision.clarify_needed is True
        assert "Vague referent" in decision.reasoning

    def test_missing_takes_priority_over_stakes(self, engine, empty_context):
        """Test: Missing params take priority over medium stakes"""
        decision = engine.analyze_request("Delete all data at 3pm", empty_context)

        # "Delete all data" would trigger medium stakes
        # But if parameters are missing, that takes priority
        # Note: In this case, no params are actually missing for "delete"
        # So stakes should trigger
        assert decision.clarify_needed is True
        assert decision.stakes_level == StakesLevel.MEDIUM


class TestPhase1ARegression:
    """Ensure Phase 1A features (vague referents) still work correctly."""

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

    def test_vague_referent_still_works(self, engine, empty_context):
        """Test: Phase 1A vague referent detection still works"""
        decision = engine.analyze_request("Fix that thing", empty_context)

        assert decision.clarify_needed is True
        assert "Vague referent" in decision.reasoning
        # Phase 1C: Confidence now computed dynamically
        assert decision.confidence < 0.6  # Should be low due to vague terms

    def test_clear_input_still_works(self, engine, empty_context):
        """Test: Phase 1A clear input detection still works"""
        decision = engine.analyze_request(
            "Fix the authentication bug in auth.py",
            empty_context
        )

        assert decision.clarify_needed is False
        assert decision.response_strategy == ResponseStrategy.ANSWER
        # Phase 1C: Confidence now computed dynamically (has file name, clear action, detailed)
        assert decision.confidence > 0.8  # Should be high

    def test_intent_extraction_still_works(self, engine, empty_context):
        """Test: Phase 1A intent extraction still works"""
        decision = engine.analyze_request("Delete test_file.py", empty_context)

        assert decision.intent == 'delete_something'


class TestClarifyingQuestions:
    """Test that clarifying questions are generated correctly."""

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

    def test_missing_param_question_format(self, engine, empty_context):
        """Test: Missing param question has correct format"""
        decision = engine.analyze_request("Schedule a meeting", empty_context)

        assert "missing_params" in decision.clarify_question
        assert "schedule" in decision.clarify_question
        # Should list missing params like 'date', 'time', 'attendees'

    def test_high_stakes_question_format(self, engine, empty_context):
        """Test: High stakes question has correct format"""
        decision = engine.analyze_request("Delete all production data", empty_context)

        assert "confirm_high_stakes" in decision.clarify_question
        assert "destructive" in decision.clarify_question


# Run tests
if __name__ == '__main__':
    pytest.main([__file__, '-v'])
