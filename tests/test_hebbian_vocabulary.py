"""
Tests for Hebbian Vocabulary Associator
Week 9 Day 1-2: Core vocabulary association learning
"""

import pytest
import os
import sys
import tempfile
import sqlite3

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.personality.hebbian.hebbian_vocabulary_associator import HebbianVocabularyAssociator
from src.personality.hebbian.hebbian_types import DEFAULT_CONFIDENCE_THRESHOLD


@pytest.fixture
def temp_db():
    """Create temporary database with Hebbian schema"""
    fd, db_path = tempfile.mkstemp(suffix='.db')
    os.close(fd)

    # Create tables
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        # vocab_associations table
        cursor.execute("""
            CREATE TABLE vocab_associations (
                term TEXT NOT NULL,
                context_type TEXT NOT NULL,
                strength REAL DEFAULT 0.5 CHECK (strength >= 0.0 AND strength <= 1.0),
                observation_count INTEGER DEFAULT 1,
                last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
                first_observed DATETIME DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (term, context_type)
            )
        """)
        # vocab_context_observations table
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
        # vocab_overrides table
        cursor.execute("""
            CREATE TABLE vocab_overrides (
                term TEXT NOT NULL,
                context_type TEXT NOT NULL,
                override_strength REAL NOT NULL CHECK (override_strength >= 0.0 AND override_strength <= 1.0),
                reason TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                created_by TEXT DEFAULT 'user',
                PRIMARY KEY (term, context_type)
            )
        """)
        conn.commit()

    yield db_path

    # Cleanup
    os.unlink(db_path)


@pytest.fixture
def associator(temp_db):
    """Create vocabulary associator with temp database"""
    return HebbianVocabularyAssociator(
        db_path=temp_db,
        learning_rate=0.1,  # Higher for faster testing
        competitive_rate=0.05,
        decay_rate_per_day=0.01
    )


class TestHebbianStrengthening:
    """Test basic Hebbian strengthening rule"""

    def test_observe_strengthens_association(self, associator):
        """Test that observing term in context strengthens association"""
        # Initial strength should be default (0.5)
        initial = associator.get_association_strength("ngl", "casual_chat")
        assert initial == 0.5

        # Observe term in context
        new_strength = associator.observe_term_in_context("ngl", "casual_chat")

        # Strength should increase
        assert new_strength > initial
        assert new_strength == associator.get_association_strength("ngl", "casual_chat")

    def test_repeated_observation_increases_strength(self, associator):
        """Test that repeated observations continue strengthening"""
        strengths = []

        # Observe multiple times
        for i in range(5):
            strength = associator.observe_term_in_context("ngl", "casual_chat")
            strengths.append(strength)

        # Each observation should increase strength
        for i in range(1, len(strengths)):
            assert strengths[i] > strengths[i-1], f"Strength should increase: {strengths}"

    def test_strength_approaches_one_asymptotically(self, associator):
        """Test that strength approaches 1.0 but never exceeds it"""
        # Observe many times
        for i in range(50):
            strength = associator.observe_term_in_context("ngl", "casual_chat")

        # Should be close to 1.0 but not exceed
        assert strength < 1.0
        assert strength > 0.9  # Should be high after many observations


class TestCompetitiveWeakening:
    """Test competitive weakening of non-active contexts"""

    def test_competitive_weakening_occurs(self, associator):
        """Test that observing in one context weakens others"""
        # First establish associations in two contexts
        associator.observe_term_in_context("hello", "casual_chat")
        associator.observe_term_in_context("hello", "formal_technical")

        # Get strengths
        casual_before = associator.get_association_strength("hello", "casual_chat")
        formal_before = associator.get_association_strength("hello", "formal_technical")

        # Now observe in casual only
        for _ in range(5):
            associator.observe_term_in_context("hello", "casual_chat")

        # Casual should be stronger, formal should be weaker
        casual_after = associator.get_association_strength("hello", "casual_chat")
        formal_after = associator.get_association_strength("hello", "formal_technical")

        assert casual_after > casual_before
        assert formal_after < formal_before

    def test_term_becomes_context_specific(self, associator):
        """Test that term becomes specific to observed context"""
        # Observe "ngl" only in casual context 10 times
        for _ in range(10):
            associator.observe_term_in_context("ngl", "casual_chat")

        # Should be appropriate in casual
        assert associator.should_use_term("ngl", "casual_chat") is True

        # Might not be appropriate in formal (depends on threshold)
        casual_strength = associator.get_association_strength("ngl", "casual_chat")
        formal_strength = associator.get_association_strength("ngl", "formal_technical")

        assert casual_strength > formal_strength


class TestShouldUseTerm:
    """Test term appropriateness prediction"""

    def test_should_use_term_with_high_strength(self, associator):
        """Test that high strength terms are recommended"""
        # Train term heavily
        for _ in range(10):
            associator.observe_term_in_context("awesome", "casual_chat")

        # Should recommend use
        assert associator.should_use_term("awesome", "casual_chat") is True

    def test_should_not_use_term_with_low_strength(self, associator):
        """Test that low strength terms are not recommended"""
        # Term not observed - default 0.5
        # With default threshold 0.65, should not recommend
        assert associator.should_use_term("unknown_term", "casual_chat") is False

    def test_custom_threshold(self, associator):
        """Test custom threshold works"""
        # Observe once (strength > 0.5 but < 0.65)
        associator.observe_term_in_context("test", "casual_chat")
        strength = associator.get_association_strength("test", "casual_chat")

        # With lower threshold, should be OK
        assert associator.should_use_term("test", "casual_chat", threshold=0.5) is True

        # With higher threshold, should not be OK
        assert associator.should_use_term("test", "casual_chat", threshold=0.9) is False


class TestTemporalDecay:
    """Test temporal decay mechanics"""

    def test_decay_reduces_strength(self, associator):
        """Test that decay reduces association strength"""
        # Create association
        associator.observe_term_in_context("test", "casual_chat")
        before = associator.get_association_strength("test", "casual_chat")

        # Apply decay (simulating 10 days inactive)
        # Need to manually set last_updated in past for this test
        with sqlite3.connect(associator.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE vocab_associations
                SET last_updated = datetime('now', '-10 days')
                WHERE term = 'test'
            """)
            conn.commit()

        # Apply decay
        decayed = associator.apply_temporal_decay(days_inactive=1.0)

        after = associator.get_association_strength("test", "casual_chat")
        assert after < before
        assert decayed >= 1

    def test_decay_preserves_valid_range(self, associator):
        """Test that decay keeps strength in valid range"""
        # Create weak association
        with sqlite3.connect(associator.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO vocab_associations
                (term, context_type, strength, observation_count, last_updated)
                VALUES ('weak', 'casual_chat', 0.1, 1, datetime('now', '-30 days'))
            """)
            conn.commit()

        # Apply heavy decay
        associator.apply_temporal_decay(days_inactive=1.0)

        # Should still be >= 0
        strength = associator.get_association_strength("weak", "casual_chat")
        assert strength >= 0.0


class TestPruning:
    """Test pruning weak associations"""

    def test_prune_removes_weak_associations(self, associator):
        """Test that pruning removes weak, rarely-observed associations"""
        # Create weak association manually
        with sqlite3.connect(associator.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO vocab_associations
                (term, context_type, strength, observation_count)
                VALUES ('weak_term', 'casual_chat', 0.05, 1)
            """)
            conn.commit()

        # Prune
        pruned = associator.prune_weak_associations(min_strength=0.1, min_observations=2)

        # Should have been pruned
        assert pruned >= 1
        strength = associator.get_association_strength("weak_term", "casual_chat")
        assert strength == 0.5  # Default (not found)

    def test_prune_keeps_strong_associations(self, associator):
        """Test that pruning keeps strong associations"""
        # Create strong association
        for _ in range(5):
            associator.observe_term_in_context("strong", "casual_chat")

        before_strength = associator.get_association_strength("strong", "casual_chat")

        # Prune
        associator.prune_weak_associations(min_strength=0.1, min_observations=2)

        # Should still exist
        after_strength = associator.get_association_strength("strong", "casual_chat")
        assert after_strength == before_strength


class TestOverrides:
    """Test manual override functionality"""

    def test_add_override_blocks_term(self, associator):
        """Test that override with 0.0 blocks term"""
        # Train term normally
        for _ in range(5):
            associator.observe_term_in_context("blocked", "casual_chat")

        # Should be usable
        assert associator.should_use_term("blocked", "casual_chat") is True

        # Add block override
        associator.add_override("blocked", "casual_chat", 0.0, "inappropriate")

        # Should now be blocked
        assert associator.should_use_term("blocked", "casual_chat") is False

    def test_override_takes_precedence(self, associator):
        """Test that override takes precedence over learned strength"""
        # Train term
        for _ in range(5):
            associator.observe_term_in_context("test", "casual_chat")

        # Add override with different strength
        associator.add_override("test", "casual_chat", 0.3, "manual")

        # Override should be returned
        strength = associator.get_association_strength("test", "casual_chat")
        assert strength == 0.3

    def test_remove_override(self, associator):
        """Test removing override restores learned strength"""
        # Train and override
        for _ in range(5):
            associator.observe_term_in_context("test", "casual_chat")

        learned = associator.get_association_strength("test", "casual_chat")
        associator.add_override("test", "casual_chat", 0.1, "temp")

        # Remove override
        removed = associator.remove_override("test", "casual_chat")
        assert removed is True

        # Should return to learned strength
        restored = associator.get_association_strength("test", "casual_chat")
        assert restored == learned


class TestConversationObservation:
    """Test observing full conversations"""

    def test_observe_conversation_extracts_terms(self, associator):
        """Test that conversation observation extracts and observes terms"""
        message = "ngl this code is pretty cool tbh"
        terms = associator.observe_conversation(message, "casual_chat")

        # Should extract meaningful terms (not stopwords)
        assert "ngl" in terms
        assert "code" in terms
        assert "cool" in terms
        assert "tbh" in terms

        # Should not include stopwords
        assert "this" not in terms
        assert "is" not in terms
        # "pretty" is NOT a stopword, so it will be included

    def test_observe_conversation_strengthens_associations(self, associator):
        """Test that observed terms get strengthened"""
        message = "ngl this is awesome"
        associator.observe_conversation(message, "casual_chat")

        # "ngl" should be stronger in casual context
        strength = associator.get_association_strength("ngl", "casual_chat")
        assert strength > 0.5


class TestStatisticsAndExport:
    """Test statistics and export functionality"""

    def test_get_statistics(self, associator):
        """Test statistics gathering"""
        # Create some associations
        associator.observe_term_in_context("test1", "casual_chat")
        associator.observe_term_in_context("test2", "formal_technical")

        stats = associator.get_statistics()

        assert 'total_associations' in stats
        assert stats['total_associations'] >= 2
        assert 'average_strength' in stats
        assert 'context_distribution' in stats

    def test_export_association_matrix(self, associator):
        """Test exporting association matrix"""
        # Create associations
        associator.observe_term_in_context("test", "casual_chat")
        associator.observe_term_in_context("test", "formal_technical")

        matrix = associator.export_association_matrix()

        assert len(matrix) >= 2
        assert all('term' in row for row in matrix)
        assert all('context' in row for row in matrix)
        assert all('strength' in row for row in matrix)

    def test_get_top_contexts_for_term(self, associator):
        """Test getting top contexts for a term"""
        # Train term in multiple contexts with different intensities
        for _ in range(10):
            associator.observe_term_in_context("ngl", "casual_chat")
        for _ in range(3):
            associator.observe_term_in_context("ngl", "creative_discussion")

        top = associator.get_top_contexts_for_term("ngl", n=3)

        # Casual should be first (most trained)
        assert len(top) >= 2
        assert top[0][0] == "casual_chat"
        assert top[0][1] > top[1][1]  # Higher strength

    def test_get_terms_for_context(self, associator):
        """Test getting terms for a context"""
        # Train several terms in casual
        for _ in range(5):
            associator.observe_term_in_context("ngl", "casual_chat")
            associator.observe_term_in_context("tbh", "casual_chat")
            associator.observe_term_in_context("cool", "casual_chat")

        terms = associator.get_terms_for_context("casual_chat", min_strength=0.6)

        # Should return strong associations
        term_names = [t[0] for t in terms]
        assert "ngl" in term_names
        assert "tbh" in term_names


class TestEdgeCases:
    """Test edge cases and error handling"""

    def test_empty_term(self, associator):
        """Test handling of empty term"""
        strength = associator.observe_term_in_context("", "casual_chat")
        assert strength == 0.0

    def test_invalid_context(self, associator):
        """Test handling of invalid context"""
        strength = associator.observe_term_in_context("test", "invalid_context")
        assert strength == 0.0

    def test_normalization(self, associator):
        """Test term normalization"""
        # Different cases should be treated same
        associator.observe_term_in_context("NGL", "casual_chat")
        associator.observe_term_in_context("ngl", "casual_chat")
        associator.observe_term_in_context("Ngl", "casual_chat")

        # Should all contribute to same term
        with sqlite3.connect(associator.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT observation_count FROM vocab_associations
                WHERE term = 'ngl' AND context_type = 'casual_chat'
            """)
            count = cursor.fetchone()[0]
            assert count == 3


# Run tests
if __name__ == '__main__':
    pytest.main([__file__, '-v'])
