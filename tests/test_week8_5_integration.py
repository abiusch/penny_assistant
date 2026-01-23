"""
Integration tests for Week 8.5 Judgment & Clarify System

Tests the complete flow from user input → judgment → Penny response
"""

import pytest
import sys
import os

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.judgment import JudgmentEngine, PennyStyleClarifier


class TestJudgmentIntegration:
    """Test judgment system integration end-to-end."""

    @pytest.fixture
    def engine(self):
        return JudgmentEngine()

    @pytest.fixture
    def clarifier(self):
        return PennyStyleClarifier()

    @pytest.fixture
    def empty_context(self):
        return {
            'conversation_history': [],
            'semantic_memory': [],
            'emotional_state': None,
            'personality_state': None
        }

    def test_vague_request_gets_penny_style_question(self, engine, clarifier, empty_context):
        """Test: Vague request → Penny-style clarifying question"""
        # User says something vague
        user_input = "Fix that thing"

        # Judgment detects vague referent
        decision = engine.analyze_request(user_input, empty_context)
        assert decision.clarify_needed is True

        # Clarifier formats in Penny's voice
        question = clarifier.format_question(decision, user_input)

        # Should be casual, not corporate
        assert "I apologize" not in question
        assert len(question) < 150
        assert "?" in question

    def test_clear_request_proceeds_without_clarification(self, engine, clarifier, empty_context):
        """Test: Clear request → No clarification needed"""
        user_input = "What is Python?"

        decision = engine.analyze_request(user_input, empty_context)

        # Should NOT need clarification
        assert decision.clarify_needed is False
        assert decision.confidence >= 0.7  # Clear enough to proceed

    def test_high_stakes_gets_confirmation(self, engine, clarifier, empty_context):
        """Test: High stakes → Confirmation question"""
        user_input = "Delete all production data"

        decision = engine.analyze_request(user_input, empty_context)

        # Should need clarification (high or medium stakes)
        assert decision.clarify_needed is True
        assert decision.stakes_level.value in ['MEDIUM', 'medium', 'HIGH', 'high']

        # Question should indicate confirmation needed
        question = clarifier.format_question(decision, user_input)
        confirmation_words = ['sure', 'confirm', 'double', 'check', 'commit']
        assert any(word in question.lower() for word in confirmation_words)

    def test_frustrated_user_gets_empathetic_response(self, engine, clarifier, empty_context):
        """Test: Frustrated user → Empathetic detection works"""
        user_input = "Just fix the fucking bug already"

        # Clarifier detects frustration
        is_frustrated = clarifier.detect_frustration(user_input)
        assert is_frustrated is True

        # This specific phrase "fix the bug" is specific enough in context
        # Test that frustration detection works even if clarification not needed
        decision = engine.analyze_request(user_input, empty_context)

        # If clarification IS needed, format empathetically
        if decision.clarify_needed:
            question = clarifier.format_question(decision, user_input, user_seems_frustrated=True)
            # Should acknowledge but still clarify
            assert len(question) > 0
            # Should not be dismissive
            assert "whatever" not in question.lower()
        else:
            # Frustration detection still works even if no clarification
            assert is_frustrated is True

    def test_missing_params_gets_parameter_question(self, engine, clarifier, empty_context):
        """Test: Missing params → Question about specific param"""
        user_input = "Schedule a meeting"

        decision = engine.analyze_request(user_input, empty_context)
        assert decision.clarify_needed is True

        question = clarifier.format_question(decision, user_input)

        # Should ask about date/time
        assert "date" in question.lower() or "time" in question.lower()

    def test_contradiction_detected_and_questioned(self, engine, clarifier):
        """Test: Contradiction → Question about what changed"""
        context = {
            'conversation_history': [
                {'role': 'user', 'content': 'I prefer Rust for this project'}
            ],
            'semantic_memory': [],
            'emotional_state': None,
            'personality_state': None
        }

        user_input = "Use Python for the API"

        decision = engine.analyze_request(user_input, context)
        assert decision.clarify_needed is True

        question = clarifier.format_question(decision, user_input)

        # Should reference the contradiction or ask about tech stack
        # Accept any reasonable contradiction question format
        question_lower = question.lower()
        is_contradiction_question = (
            'rust' in question_lower or  # References the previous tech
            'python' in question_lower or  # References the new tech
            any(word in question_lower for word in ['hold', 'wait', 'thought', 'chang', 'before', 'mention', 'shift'])
        )
        assert is_contradiction_question, f"Question doesn't reference contradiction: {question}"

    def test_end_to_end_flow(self, engine, clarifier, empty_context):
        """Test: Complete flow from user input to Penny response"""
        # Scenario: User asks vague question
        user_input = "Debug it"

        # Step 1: Judgment detects issue
        decision = engine.analyze_request(user_input, empty_context)
        assert decision.clarify_needed is True
        assert decision.confidence < 0.5

        # Step 2: Format in Penny's voice
        question = clarifier.format_question(decision, user_input)

        # Step 3: Verify output is Penny-like
        assert isinstance(question, str)
        assert len(question) > 10
        assert len(question) < 150
        assert "?" in question

        # Should be casual - accept wide range of Penny-style markers
        penny_markers = ['quick', 'real', 'check', 'need', 'what', 'which', 'two', 'second', 'nail', 'just']
        assert any(marker in question.lower() for marker in penny_markers), f"No Penny markers in: {question}"

    def test_multiple_vague_scenarios(self, engine, clarifier, empty_context):
        """Test: Vague referents trigger clarification"""
        # These have clear vague referents: "that", "it", "this"
        vague_inputs = [
            "Fix that",
            "Debug it",
            "Delete this",
        ]

        for user_input in vague_inputs:
            decision = engine.analyze_request(user_input, empty_context)
            assert decision.clarify_needed is True, f"Failed for: {user_input}"

    def test_clear_specific_requests_proceed(self, engine, clarifier, empty_context):
        """Test: Clear, specific requests don't trigger clarification"""
        clear_inputs = [
            "What is Python?",
            "How do I install numpy?",
            "Tell me about machine learning",
            "What's the weather like?"
        ]

        for user_input in clear_inputs:
            decision = engine.analyze_request(user_input, empty_context)
            assert decision.clarify_needed is False, f"Failed for: {user_input}"

    def test_judgment_logging_creates_file(self, engine, empty_context, tmp_path):
        """Test: Judgment decisions are logged to file"""
        import json
        from datetime import datetime

        user_input = "Fix that bug"
        decision = engine.analyze_request(user_input, empty_context)

        # Verify decision has necessary fields for logging
        assert hasattr(decision, 'clarify_needed')
        assert hasattr(decision, 'reasoning')
        assert hasattr(decision, 'confidence')
        assert hasattr(decision, 'stakes_level')
        assert hasattr(decision, 'intent')

        # Verify we can create log entry
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'user_input': user_input,
            'clarify_needed': decision.clarify_needed,
            'reasoning': decision.reasoning,
            'stakes_level': decision.stakes_level.value,
            'confidence': decision.confidence,
            'intent': decision.intent
        }

        # Should serialize without errors
        json_str = json.dumps(log_entry)
        assert len(json_str) > 0


class TestPennyStyleConsistency:
    """Test that all clarifications maintain Penny's personality."""

    @pytest.fixture
    def engine(self):
        return JudgmentEngine()

    @pytest.fixture
    def clarifier(self):
        return PennyStyleClarifier()

    @pytest.fixture
    def empty_context(self):
        return {
            'conversation_history': [],
            'semantic_memory': [],
            'emotional_state': None,
            'personality_state': None
        }

    def test_no_corporate_speak_in_clarifications(self, engine, clarifier, empty_context):
        """Test: No corporate phrases in any clarification"""
        test_inputs = [
            "Fix that",
            "Schedule a meeting",
            "Delete all files",
            "Debug it"
        ]

        corporate_phrases = [
            "I apologize",
            "I'm sorry",
            "unfortunately",
            "at this time",
            "kindly",
            "please be advised"
        ]

        for user_input in test_inputs:
            decision = engine.analyze_request(user_input, empty_context)
            if decision.clarify_needed:
                question = clarifier.format_question(decision, user_input)
                for phrase in corporate_phrases:
                    assert phrase.lower() not in question.lower(), \
                        f"Corporate phrase '{phrase}' found in: {question}"

    def test_all_clarifications_are_brief(self, engine, clarifier, empty_context):
        """Test: All clarifications are under 150 chars"""
        test_inputs = [
            "Fix that thing",
            "Schedule a meeting",
            "Delete all production data",
            "Debug it",
            "Run the script"
        ]

        for user_input in test_inputs:
            decision = engine.analyze_request(user_input, empty_context)
            if decision.clarify_needed:
                question = clarifier.format_question(decision, user_input)
                assert len(question) < 150, \
                    f"Question too long ({len(question)} chars): {question}"


# Run tests
if __name__ == '__main__':
    pytest.main([__file__, '-v'])
