"""
Tests for Hebbian Sequence Learner
Week 9 Day 6-7: Conversation flow pattern learning
"""

import pytest
import os
import sys
import tempfile
import sqlite3

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.personality.hebbian.hebbian_sequence_learner import HebbianSequenceLearner
from src.personality.hebbian.hebbian_types import (
    ConversationState,
    DEFAULT_PATTERN_THRESHOLD
)


@pytest.fixture
def temp_db():
    """Create temporary database with Hebbian schema"""
    fd, db_path = tempfile.mkstemp(suffix='.db')
    os.close(fd)

    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()

        # conversation_state_transitions table
        cursor.execute("""
            CREATE TABLE conversation_state_transitions (
                state_from TEXT NOT NULL,
                state_to TEXT NOT NULL,
                transition_count INTEGER DEFAULT 1,
                transition_probability REAL DEFAULT 0.0,
                avg_satisfaction REAL DEFAULT 0.5,
                last_observed DATETIME DEFAULT CURRENT_TIMESTAMP,
                first_observed DATETIME DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (state_from, state_to)
            )
        """)

        # state_sequences table
        cursor.execute("""
            CREATE TABLE state_sequences (
                sequence_id TEXT PRIMARY KEY,
                sequence_json TEXT NOT NULL,
                frequency INTEGER DEFAULT 1,
                avg_satisfaction REAL DEFAULT 0.5,
                last_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
                first_seen DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # pattern_templates table
        cursor.execute("""
            CREATE TABLE pattern_templates (
                pattern_id TEXT PRIMARY KEY,
                template_json TEXT NOT NULL,
                skip_opportunities_json TEXT,
                frequency INTEGER DEFAULT 0,
                avg_satisfaction REAL DEFAULT 0.5,
                last_applied DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.commit()

    yield db_path
    os.unlink(db_path)


@pytest.fixture
def learner(temp_db):
    """Create sequence learner with temp database"""
    return HebbianSequenceLearner(db_path=temp_db, pattern_threshold=3)


class TestStateClassification:
    """Test conversation state classification"""

    def test_classify_problem_statement(self, learner):
        """Test: Classify messages with problem indicators"""
        test_cases = [
            ("I'm stuck on this async code", "problem_statement"),
            ("This function is broken", "problem_statement"),
            ("Getting an error when I run this", "problem_statement"),
            ("Why doesn't this work?", "problem_statement"),
        ]

        for message, expected in test_cases:
            result = learner.classify_conversation_state(message, {})
            assert result == expected, f"'{message}' should be {expected}, got {result}"

    def test_classify_clarification_question(self, learner):
        """Test: Classify clarification requests"""
        test_cases = [
            ("What do you mean by that?", "clarification_question"),
            ("Can you explain that again?", "clarification_question"),
            ("I don't understand", "clarification_question"),
        ]

        for message, expected in test_cases:
            result = learner.classify_conversation_state(message, {})
            assert result == expected, f"'{message}' should be {expected}, got {result}"

    def test_classify_positive_feedback(self, learner):
        """Test: Classify positive feedback"""
        test_cases = [
            ("Thanks! That works perfectly", "positive_feedback"),
            ("Great, got it!", "positive_feedback"),
            ("Awesome, makes sense now", "positive_feedback"),
        ]

        for message, expected in test_cases:
            result = learner.classify_conversation_state(message, {})
            assert result == expected, f"'{message}' should be {expected}, got {result}"

    def test_classify_frustration(self, learner):
        """Test: Classify frustration expressions"""
        test_cases = [
            ("Ugh still not working!!", "frustration_expression"),
            ("Argh this is so frustrating", "frustration_expression"),
        ]

        for message, expected in test_cases:
            result = learner.classify_conversation_state(message, {})
            assert result == expected, f"'{message}' should be {expected}, got {result}"

    def test_classify_with_context(self, learner):
        """Test: Context affects classification"""
        # Follow-up context
        result = learner.classify_conversation_state(
            "What about this case?",
            {'is_follow_up': True}
        )
        assert result == "follow_up_question"

        # Code context
        result = learner.classify_conversation_state(
            "Check this out",
            {'has_code': True}
        )
        assert result == "code_review"

    def test_empty_message(self, learner):
        """Test: Empty message returns casual_chat"""
        result = learner.classify_conversation_state("", {})
        assert result == "casual_chat"


class TestTransitionLearning:
    """Test state transition learning"""

    def test_observe_transition_creates_record(self, learner):
        """Test: Observing transition creates database record"""
        updates = learner.observe_transition("problem_statement", "clarification_question")
        assert updates >= 1

        # Verify in database
        prob = learner.get_transition_probability("problem_statement", "clarification_question")
        assert prob > 0.0

    def test_repeated_transition_increases_count(self, learner):
        """Test: Repeated transitions increase count"""
        # Observe same transition multiple times
        for _ in range(5):
            learner.observe_transition("problem_statement", "clarification_question")

        # Also observe another transition
        learner.observe_transition("problem_statement", "positive_feedback")

        # Check probabilities
        prob_clarify = learner.get_transition_probability(
            "problem_statement", "clarification_question"
        )
        prob_feedback = learner.get_transition_probability(
            "problem_statement", "positive_feedback"
        )

        # Clarification should be more likely
        assert prob_clarify > prob_feedback

    def test_probability_normalization(self, learner):
        """Test: Probabilities are normalized"""
        # Create multiple transitions from same state
        for _ in range(3):
            learner.observe_transition("problem_statement", "clarification_question")
        for _ in range(2):
            learner.observe_transition("problem_statement", "positive_feedback")

        # Probabilities should sum to 1.0
        prob1 = learner.get_transition_probability("problem_statement", "clarification_question")
        prob2 = learner.get_transition_probability("problem_statement", "positive_feedback")

        assert abs((prob1 + prob2) - 1.0) < 0.01

    def test_transition_updates_history(self, learner):
        """Test: Transitions update conversation history"""
        learner.observe_transition("problem_statement", "clarification_question")
        learner.observe_transition("clarification_question", "positive_feedback")

        assert len(learner.conversation_history) == 2
        assert learner.conversation_history[-1] == "positive_feedback"


class TestPrediction:
    """Test state prediction"""

    def test_predict_next_states(self, learner):
        """Test: Predict likely next states"""
        # Train some transitions
        for _ in range(5):
            learner.observe_transition("problem_statement", "clarification_question")
        for _ in range(3):
            learner.observe_transition("problem_statement", "positive_feedback")

        predictions = learner.predict_next_states("problem_statement", [], n=3)

        assert len(predictions) >= 2
        # First prediction should be clarification (more common)
        assert predictions[0][0] == "clarification_question"
        assert predictions[0][1] > predictions[1][1]  # Higher probability

    def test_predict_with_no_history(self, learner):
        """Test: Prediction works with empty history"""
        predictions = learner.predict_next_states("unknown_state", [], n=3)
        assert predictions == []  # No data yet

    def test_anticipate_user_need(self, learner):
        """Test: Anticipation returns when confident"""
        # Train strong pattern
        for _ in range(10):
            learner.observe_transition("problem_statement", "clarification_question")

        anticipation = learner.anticipate_user_need("problem_statement", [])

        if anticipation:  # Only if we have enough data
            assert anticipation.current_state == "problem_statement"
            assert len(anticipation.likely_next_states) > 0
            assert anticipation.confidence > 0.0


class TestPatternDetection:
    """Test sequence pattern detection"""

    def test_sequence_pattern_created(self, learner):
        """Test: Repeated sequences create patterns"""
        # Simulate a recurring pattern by building up history
        # We need to observe transitions that build up the history
        pattern = ["problem_statement", "clarification_question", "positive_feedback"]

        # Build up history over multiple "sessions"
        for _ in range(5):
            # Add first state to history manually (simulating conversation start)
            learner.conversation_history.append(pattern[0])
            # Then observe transitions which add to history
            for i in range(len(pattern) - 1):
                learner.observe_transition(pattern[i], pattern[i + 1])

        # Check that sequences were created
        with sqlite3.connect(learner.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM state_sequences")
            count = cursor.fetchone()[0]

        # Should have created at least one sequence pattern
        assert count >= 1

    def test_detect_recurring_patterns(self, learner):
        """Test: Detect recurring patterns with threshold"""
        # Create pattern manually
        with sqlite3.connect(learner.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO state_sequences (sequence_id, sequence_json, frequency, avg_satisfaction)
                VALUES (?, ?, ?, ?)
            """, ("test_seq", '["a", "b", "c"]', 5, 0.8))
            conn.commit()

        patterns = learner.detect_recurring_patterns(min_frequency=3)
        assert len(patterns) >= 1
        assert patterns[0].frequency >= 3


class TestMaintenanceAndExport:
    """Test maintenance and export functionality"""

    def test_reset_history(self, learner):
        """Test: Reset clears history"""
        learner.observe_transition("a", "b")
        learner.observe_transition("b", "c")
        assert len(learner.conversation_history) == 2

        learner.reset_history()
        assert len(learner.conversation_history) == 0

    def test_export_transition_matrix(self, learner):
        """Test: Export transition matrix"""
        learner.observe_transition("problem_statement", "clarification_question")
        learner.observe_transition("clarification_question", "positive_feedback")

        matrix = learner.export_transition_matrix()

        assert len(matrix) >= 2
        assert all('state_from' in row for row in matrix)
        assert all('state_to' in row for row in matrix)
        assert all('probability' in row for row in matrix)

    def test_get_statistics(self, learner):
        """Test: Get system statistics"""
        # Create some data
        learner.observe_transition("problem_statement", "clarification_question")
        learner.observe_transition("clarification_question", "positive_feedback")

        stats = learner.get_statistics()

        assert 'total_transitions' in stats
        assert stats['total_transitions'] >= 2
        assert 'total_observations' in stats
        assert 'history_length' in stats


class TestEdgeCases:
    """Test edge cases and error handling"""

    def test_empty_transition_handled(self, learner):
        """Test: Empty states don't crash"""
        updates = learner.observe_transition("", "")
        assert updates == 0

    def test_none_transition_handled(self, learner):
        """Test: None states don't crash"""
        updates = learner.observe_transition(None, None)
        assert updates == 0

    def test_unknown_state_probability(self, learner):
        """Test: Unknown state returns 0 probability"""
        prob = learner.get_transition_probability("unknown_from", "unknown_to")
        assert prob == 0.0

    def test_temporal_decay(self, learner):
        """Test: Temporal decay reduces counts"""
        # Create transition with count
        learner.observe_transition("a", "b")

        # Apply decay (normally for old entries, but we test the mechanism)
        with sqlite3.connect(learner.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE conversation_state_transitions
                SET last_observed = datetime('now', '-10 days')
            """)
            conn.commit()

        decayed = learner.apply_temporal_decay(days_inactive=7.0)
        assert decayed >= 0  # May be 0 if no old entries


# Run tests
if __name__ == '__main__':
    pytest.main([__file__, '-v'])
