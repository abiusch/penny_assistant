"""
Tests for Hebbian Dimension Associator
Week 9 Day 3-4: Personality dimension co-activation learning
"""

import pytest
import os
import sys
import tempfile
import sqlite3

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.personality.hebbian.hebbian_dimension_associator import HebbianDimensionAssociator
from src.personality.hebbian.hebbian_types import (
    DEFAULT_CONFIDENCE_THRESHOLD,
    DEFAULT_ACTIVATION_THRESHOLD,
    PERSONALITY_DIMENSIONS
)


@pytest.fixture
def temp_db():
    """Create temporary database with Hebbian schema"""
    fd, db_path = tempfile.mkstemp(suffix='.db')
    os.close(fd)

    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()

        # dimension_coactivations table
        cursor.execute("""
            CREATE TABLE dimension_coactivations (
                dim1 TEXT NOT NULL,
                dim2 TEXT NOT NULL,
                strength REAL DEFAULT 0.0 CHECK (strength >= 0.0 AND strength <= 1.0),
                observation_count INTEGER DEFAULT 0,
                last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
                first_observed DATETIME DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (dim1, dim2),
                CHECK (dim1 < dim2)
            )
        """)

        # coactivation_observations table
        cursor.execute("""
            CREATE TABLE coactivation_observations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                dimensions_json TEXT NOT NULL,
                context_snapshot TEXT,
                session_id TEXT
            )
        """)

        # multi_dim_patterns table
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

        # negative_correlations table
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
def associator(temp_db):
    """Create dimension associator with temp database"""
    return HebbianDimensionAssociator(
        db_path=temp_db,
        learning_rate=0.1,  # Higher for faster testing
        activation_threshold=0.6
    )


class TestCoactivationLearning:
    """Test basic co-activation learning"""

    def test_observe_creates_coactivations(self, associator):
        """Test that observing active dimensions creates co-activations"""
        # Observe two active dimensions
        updates = associator.observe_activations({
            'emotional_support_style': 0.85,
            'response_length_preference': 0.2  # Low = brief
        })

        # Should have created at least one co-activation
        assert updates >= 1

        # Check co-activation exists
        strength = associator.get_coactivation_strength(
            'emotional_support_style',
            'response_length_preference'
        )
        assert strength > 0.0

    def test_repeated_observation_strengthens(self, associator):
        """Test that repeated observations strengthen co-activation"""
        dims = {
            'emotional_support_style': 0.85,
            'response_length_preference': 0.2
        }

        # Observe multiple times
        strengths = []
        for _ in range(5):
            associator.observe_activations(dims)
            strength = associator.get_coactivation_strength(
                'emotional_support_style',
                'response_length_preference'
            )
            strengths.append(strength)

        # Should be monotonically increasing
        for i in range(1, len(strengths)):
            assert strengths[i] >= strengths[i-1]

    def test_neutral_dimensions_ignored(self, associator):
        """Test that neutral (0.5) dimensions don't create co-activations"""
        # Observe with neutral values
        updates = associator.observe_activations({
            'emotional_support_style': 0.5,
            'response_length_preference': 0.5
        })

        # Should not update anything (values too close to neutral)
        assert updates == 0

    def test_minimum_two_dimensions_required(self, associator):
        """Test that at least 2 active dimensions are needed"""
        # Single active dimension
        updates = associator.observe_activations({
            'emotional_support_style': 0.85
        })

        assert updates == 0


class TestPrediction:
    """Test co-activation prediction"""

    def test_predict_from_known_dimension(self, associator):
        """Test predicting unknown dimensions from known ones"""
        # Train co-activation with more observations for stronger signal
        for _ in range(20):
            associator.observe_activations({
                'emotional_support_style': 0.9,  # More extreme value
                'response_length_preference': 0.1  # More extreme value
            })

        # Predict from empathy alone with lower threshold
        predictions = associator.predict_coactivations(
            {'emotional_support_style': 0.9},
            threshold=0.15  # Lower threshold to account for confidence scaling
        )

        # Should predict response_length_preference
        assert 'response_length_preference' in predictions
        pred = predictions['response_length_preference']
        assert pred.confidence > 0

    def test_prediction_confidence(self, associator):
        """Test that prediction confidence reflects co-activation strength"""
        # Train weak co-activation (few observations)
        associator.observe_activations({
            'emotional_support_style': 0.85,
            'humor_style_preference': 0.8
        })

        # Train strong co-activation (many observations)
        for _ in range(10):
            associator.observe_activations({
                'emotional_support_style': 0.85,
                'response_length_preference': 0.2
            })

        predictions = associator.predict_coactivations(
            {'emotional_support_style': 0.85},
            threshold=0.1
        )

        # response_length should have higher confidence than humor
        if 'response_length_preference' in predictions and 'humor_style_preference' in predictions:
            assert (predictions['response_length_preference'].confidence >=
                    predictions['humor_style_preference'].confidence)

    def test_no_prediction_for_known_dimensions(self, associator):
        """Test that we don't predict dimensions we already know"""
        # Train
        for _ in range(5):
            associator.observe_activations({
                'emotional_support_style': 0.85,
                'response_length_preference': 0.2
            })

        # Predict with both dimensions known
        predictions = associator.predict_coactivations({
            'emotional_support_style': 0.85,
            'response_length_preference': 0.2
        })

        # Should not predict either (both already known)
        assert 'emotional_support_style' not in predictions
        assert 'response_length_preference' not in predictions


class TestMultiDimensionalPatterns:
    """Test multi-dimensional pattern detection"""

    def test_three_plus_dims_creates_pattern(self, associator):
        """Test that 3+ active dimensions create a multi-dim pattern"""
        # Observe 3 active dimensions
        associator.observe_activations({
            'emotional_support_style': 0.85,
            'response_length_preference': 0.2,
            'technical_depth_preference': 0.3
        })

        # Check pattern was created
        patterns = associator.get_multi_dim_patterns(min_frequency=1)
        assert len(patterns) >= 1

    def test_pattern_frequency_increases(self, associator):
        """Test that repeated patterns increase frequency"""
        dims = {
            'emotional_support_style': 0.85,
            'response_length_preference': 0.2,
            'technical_depth_preference': 0.3
        }

        # Observe same pattern multiple times
        for _ in range(5):
            associator.observe_activations(dims)

        # Check frequency
        patterns = associator.get_multi_dim_patterns(min_frequency=1)
        assert len(patterns) >= 1
        assert patterns[0].frequency >= 5


class TestQueryMethods:
    """Test query and export methods"""

    def test_get_strongest_coactivations(self, associator):
        """Test getting strongest co-activations for a dimension"""
        # Create several co-activations with different strengths
        for _ in range(10):
            associator.observe_activations({
                'emotional_support_style': 0.85,
                'response_length_preference': 0.2
            })
        for _ in range(3):
            associator.observe_activations({
                'emotional_support_style': 0.85,
                'humor_style_preference': 0.8
            })

        # Get strongest for empathy
        strongest = associator.get_strongest_coactivations('emotional_support_style', n=5)

        assert len(strongest) >= 2
        # First should be stronger than second
        assert strongest[0][1] >= strongest[1][1]

    def test_export_coactivation_matrix(self, associator):
        """Test exporting co-activation matrix"""
        # Create some co-activations
        associator.observe_activations({
            'emotional_support_style': 0.85,
            'response_length_preference': 0.2
        })
        associator.observe_activations({
            'humor_style_preference': 0.8,
            'technical_depth_preference': 0.3
        })

        matrix = associator.export_coactivation_matrix()

        assert len(matrix) >= 2
        assert all('dim1' in row for row in matrix)
        assert all('dim2' in row for row in matrix)
        assert all('strength' in row for row in matrix)

    def test_get_statistics(self, associator):
        """Test statistics gathering"""
        # Create some co-activations
        for _ in range(5):
            associator.observe_activations({
                'emotional_support_style': 0.85,
                'response_length_preference': 0.2,
                'technical_depth_preference': 0.3
            })

        stats = associator.get_statistics()

        assert 'total_coactivations' in stats
        assert stats['total_coactivations'] >= 3  # 3 pairs from 3 dims
        assert 'average_strength' in stats
        assert 'multi_dim_patterns' in stats


class TestEdgeCases:
    """Test edge cases and normalization"""

    def test_dimension_pair_normalization(self, associator):
        """Test that dim1, dim2 order is normalized"""
        # Observe in one order
        associator.observe_activations({
            'response_length_preference': 0.2,
            'emotional_support_style': 0.85
        })

        # Query in both orders - should get same result
        strength1 = associator.get_coactivation_strength(
            'emotional_support_style',
            'response_length_preference'
        )
        strength2 = associator.get_coactivation_strength(
            'response_length_preference',
            'emotional_support_style'
        )

        assert strength1 == strength2

    def test_strength_capped_at_one(self, associator):
        """Test that strength never exceeds 1.0"""
        # Observe many times
        for _ in range(100):
            associator.observe_activations({
                'emotional_support_style': 0.95,
                'response_length_preference': 0.1
            })

        strength = associator.get_coactivation_strength(
            'emotional_support_style',
            'response_length_preference'
        )

        assert strength <= 1.0

    def test_low_activation_also_triggers(self, associator):
        """Test that low values (< 1-threshold) also count as active"""
        # Both dimensions have extreme values (one high, one low)
        updates = associator.observe_activations({
            'emotional_support_style': 0.85,  # High
            'response_length_preference': 0.15  # Low (brief)
        })

        assert updates >= 1

        strength = associator.get_coactivation_strength(
            'emotional_support_style',
            'response_length_preference'
        )
        assert strength > 0


# Run tests
if __name__ == '__main__':
    pytest.main([__file__, '-v'])
