"""
Integration Tests for Week 9 Hebbian Learning Components
Tests vocabulary and dimension associators working together
"""

import pytest
import os
import sys
import tempfile
import sqlite3
import time

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.personality.hebbian.hebbian_vocabulary_associator import HebbianVocabularyAssociator
from src.personality.hebbian.hebbian_dimension_associator import HebbianDimensionAssociator
from src.personality.hebbian.hebbian_types import PERSONALITY_DIMENSIONS


@pytest.fixture
def temp_db():
    """Create temporary database with full Hebbian schema"""
    fd, db_path = tempfile.mkstemp(suffix='.db')
    os.close(fd)

    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()

        # Vocabulary tables
        cursor.execute("""
            CREATE TABLE vocab_associations (
                term TEXT NOT NULL,
                context_type TEXT NOT NULL,
                strength REAL DEFAULT 0.5,
                observation_count INTEGER DEFAULT 1,
                last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
                first_observed DATETIME DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (term, context_type)
            )
        """)
        cursor.execute("""
            CREATE TABLE vocab_context_observations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                term TEXT NOT NULL,
                context_type TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                user_message TEXT,
                session_id TEXT
            )
        """)
        cursor.execute("""
            CREATE TABLE vocab_overrides (
                term TEXT NOT NULL,
                context_type TEXT NOT NULL,
                override_strength REAL NOT NULL,
                reason TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                created_by TEXT DEFAULT 'user',
                PRIMARY KEY (term, context_type)
            )
        """)

        # Dimension tables
        cursor.execute("""
            CREATE TABLE dimension_coactivations (
                dim1 TEXT NOT NULL,
                dim2 TEXT NOT NULL,
                strength REAL DEFAULT 0.0,
                observation_count INTEGER DEFAULT 0,
                last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
                first_observed DATETIME DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (dim1, dim2),
                CHECK (dim1 < dim2)
            )
        """)
        cursor.execute("""
            CREATE TABLE coactivation_observations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                dimensions_json TEXT NOT NULL,
                context_snapshot TEXT,
                session_id TEXT
            )
        """)
        cursor.execute("""
            CREATE TABLE multi_dim_patterns (
                pattern_id TEXT PRIMARY KEY,
                dimensions_json TEXT NOT NULL,
                frequency INTEGER DEFAULT 1,
                avg_satisfaction REAL DEFAULT 0.5,
                last_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
                first_seen DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("""
            CREATE TABLE negative_correlations (
                dim_high TEXT NOT NULL,
                dim_low TEXT NOT NULL,
                correlation_strength REAL DEFAULT 0.0,
                observation_count INTEGER DEFAULT 0,
                last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (dim_high, dim_low)
            )
        """)

        conn.commit()

    yield db_path
    os.unlink(db_path)


@pytest.fixture
def vocab_associator(temp_db):
    """Create vocabulary associator"""
    return HebbianVocabularyAssociator(db_path=temp_db, learning_rate=0.1)


@pytest.fixture
def dim_associator(temp_db):
    """Create dimension associator"""
    return HebbianDimensionAssociator(db_path=temp_db, learning_rate=0.1)


class TestIntegratedLearning:
    """Test vocab and dimension learning working together"""

    def test_simulated_conversation_flow(self, vocab_associator, dim_associator):
        """Test: Simulate a complete conversation learning flow"""
        # Scenario: User sends casual message when stressed

        # Step 1: User message arrives
        user_message = "ngl I'm pretty stuck on this async stuff tbh"
        context_type = "problem_solving"

        # Step 2: Extract vocabulary associations
        terms = vocab_associator.observe_conversation(user_message, context_type)
        assert len(terms) > 0
        assert "ngl" in terms
        assert "stuck" in terms
        assert "async" in terms

        # Step 3: Observe personality dimensions (from response generation)
        dim_associator.observe_activations({
            'emotional_support_style': 0.8,      # High empathy for stressed user
            'response_length_preference': 0.3,   # Brief responses
            'technical_depth_preference': 0.6    # Medium technical depth
        })

        # Verify both systems learned
        vocab_strength = vocab_associator.get_association_strength("ngl", context_type)
        assert vocab_strength > 0.5

        dim_coact = dim_associator.get_coactivation_strength(
            'emotional_support_style',
            'response_length_preference'
        )
        assert dim_coact > 0.0

    def test_context_vocabulary_matching(self, vocab_associator):
        """Test: Vocabulary learns context-appropriate usage"""
        # Train casual vocabulary
        casual_messages = [
            "ngl this is pretty cool",
            "tbh I think this approach works better",
            "yo can you help with this real quick",
        ]
        for msg in casual_messages:
            vocab_associator.observe_conversation(msg, "casual_chat")

        # Train formal vocabulary
        formal_messages = [
            "Could you please explain the implementation details?",
            "I would appreciate a thorough analysis of this approach.",
            "Please provide documentation for this feature.",
        ]
        for msg in formal_messages:
            vocab_associator.observe_conversation(msg, "formal_technical")

        # Verify vocabulary learned context
        assert vocab_associator.should_use_term("ngl", "casual_chat", threshold=0.55)
        assert vocab_associator.should_use_term("please", "formal_technical", threshold=0.55)

        # Verify cross-context isn't recommended
        ngl_casual = vocab_associator.get_association_strength("ngl", "casual_chat")
        ngl_formal = vocab_associator.get_association_strength("ngl", "formal_technical")
        assert ngl_casual > ngl_formal

    def test_dimension_pattern_emergence(self, dim_associator):
        """Test: Dimension patterns emerge from repeated observations"""
        # Simulate stressed user pattern: empathy + brief + simple
        stressed_pattern = {
            'emotional_support_style': 0.85,
            'response_length_preference': 0.2,  # Brief
            'technical_depth_preference': 0.3   # Simple
        }

        # Observe pattern multiple times
        for _ in range(5):
            dim_associator.observe_activations(stressed_pattern)

        # Check pattern was detected
        patterns = dim_associator.get_multi_dim_patterns(min_frequency=3)
        assert len(patterns) >= 1

        # Check co-activations learned
        empathy_brief = dim_associator.get_coactivation_strength(
            'emotional_support_style',
            'response_length_preference'
        )
        assert empathy_brief > 0.1


class TestPerformance:
    """Test performance requirements"""

    def test_vocab_observation_latency(self, vocab_associator):
        """Test: Vocabulary observation < 3ms"""
        message = "ngl this is a test message for performance tbh"

        start = time.time()
        for _ in range(10):
            vocab_associator.observe_conversation(message, "casual_chat")
        elapsed = (time.time() - start) / 10 * 1000  # ms per observation

        assert elapsed < 10, f"Vocab observation too slow: {elapsed:.2f}ms"

    def test_dim_observation_latency(self, dim_associator):
        """Test: Dimension observation < 3ms"""
        dims = {
            'emotional_support_style': 0.85,
            'response_length_preference': 0.2,
            'technical_depth_preference': 0.3
        }

        start = time.time()
        for _ in range(10):
            dim_associator.observe_activations(dims)
        elapsed = (time.time() - start) / 10 * 1000  # ms per observation

        assert elapsed < 10, f"Dim observation too slow: {elapsed:.2f}ms"

    def test_vocab_query_latency(self, vocab_associator):
        """Test: Vocabulary query < 1ms"""
        # Pre-populate some data
        vocab_associator.observe_conversation("test message", "casual_chat")

        start = time.time()
        for _ in range(100):
            vocab_associator.get_association_strength("test", "casual_chat")
        elapsed = (time.time() - start) / 100 * 1000  # ms per query

        assert elapsed < 5, f"Vocab query too slow: {elapsed:.2f}ms"

    def test_dim_prediction_latency(self, dim_associator):
        """Test: Dimension prediction < 3ms"""
        # Pre-train some co-activations
        for _ in range(5):
            dim_associator.observe_activations({
                'emotional_support_style': 0.85,
                'response_length_preference': 0.2
            })

        start = time.time()
        for _ in range(10):
            dim_associator.predict_coactivations(
                {'emotional_support_style': 0.8},
                threshold=0.1
            )
        elapsed = (time.time() - start) / 10 * 1000  # ms per prediction

        assert elapsed < 10, f"Dim prediction too slow: {elapsed:.2f}ms"


class TestDataPersistence:
    """Test data persistence across sessions"""

    def test_vocab_data_persists(self, temp_db):
        """Test: Vocabulary data persists after reconnection"""
        # First session: create and train
        associator1 = HebbianVocabularyAssociator(db_path=temp_db, learning_rate=0.1)
        for _ in range(5):
            associator1.observe_term_in_context("ngl", "casual_chat")
        strength1 = associator1.get_association_strength("ngl", "casual_chat")

        # Second session: reconnect and verify
        associator2 = HebbianVocabularyAssociator(db_path=temp_db, learning_rate=0.1)
        strength2 = associator2.get_association_strength("ngl", "casual_chat")

        assert strength2 == strength1

    def test_dim_data_persists(self, temp_db):
        """Test: Dimension data persists after reconnection"""
        # First session
        associator1 = HebbianDimensionAssociator(db_path=temp_db, learning_rate=0.1)
        for _ in range(5):
            associator1.observe_activations({
                'emotional_support_style': 0.85,
                'response_length_preference': 0.2
            })
        coact1 = associator1.get_coactivation_strength(
            'emotional_support_style',
            'response_length_preference'
        )

        # Second session
        associator2 = HebbianDimensionAssociator(db_path=temp_db, learning_rate=0.1)
        coact2 = associator2.get_coactivation_strength(
            'emotional_support_style',
            'response_length_preference'
        )

        assert coact2 == coact1


class TestStatistics:
    """Test statistics and export functionality"""

    def test_combined_statistics(self, vocab_associator, dim_associator):
        """Test: Both components report statistics"""
        # Generate some data
        vocab_associator.observe_conversation("test message ngl", "casual_chat")
        dim_associator.observe_activations({
            'emotional_support_style': 0.85,
            'response_length_preference': 0.2
        })

        # Get statistics
        vocab_stats = vocab_associator.get_statistics()
        dim_stats = dim_associator.get_statistics()

        assert vocab_stats['total_associations'] > 0
        assert dim_stats['total_coactivations'] > 0

    def test_export_functions(self, vocab_associator, dim_associator):
        """Test: Both components can export data"""
        # Generate some data
        vocab_associator.observe_conversation("test message", "casual_chat")
        dim_associator.observe_activations({
            'emotional_support_style': 0.85,
            'response_length_preference': 0.2
        })

        # Export
        vocab_export = vocab_associator.export_association_matrix()
        dim_export = dim_associator.export_coactivation_matrix()

        assert len(vocab_export) > 0
        assert len(dim_export) > 0


class TestEdgeCases:
    """Test edge cases and error handling"""

    def test_empty_message_handled(self, vocab_associator):
        """Test: Empty message doesn't crash"""
        terms = vocab_associator.observe_conversation("", "casual_chat")
        assert terms == []

    def test_single_dimension_handled(self, dim_associator):
        """Test: Single dimension doesn't crash"""
        updates = dim_associator.observe_activations({
            'emotional_support_style': 0.85
        })
        assert updates == 0  # Need 2+ dimensions

    def test_invalid_context_handled(self, vocab_associator):
        """Test: Invalid context doesn't crash"""
        strength = vocab_associator.observe_term_in_context("test", "invalid_context")
        assert strength == 0.0


# Run tests
if __name__ == '__main__':
    pytest.main([__file__, '-v'])
