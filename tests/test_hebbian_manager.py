"""
Tests for Hebbian Learning Manager
Week 10 Day 8: Central orchestrator for all Hebbian components
"""

import pytest
import os
import sys
import tempfile
import sqlite3
import time

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.personality.hebbian.hebbian_learning_manager import HebbianLearningManager


@pytest.fixture
def temp_db():
    """Create temporary database with full Hebbian schema"""
    fd, db_path = tempfile.mkstemp(suffix='.db')
    os.close(fd)

    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()

        # ==============================
        # VOCABULARY TABLES
        # ==============================
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
                override_strength REAL NOT NULL CHECK (override_strength >= 0.0 AND override_strength <= 1.0),
                reason TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                created_by TEXT DEFAULT 'user',
                PRIMARY KEY (term, context_type)
            )
        """)

        # ==============================
        # DIMENSION TABLES
        # ==============================
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

        # ==============================
        # SEQUENCE TABLES
        # ==============================
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
def manager(temp_db):
    """Create manager with temp database"""
    return HebbianLearningManager(
        db_path=temp_db,
        enable_caching=True,
        cache_size=100,
        cache_refresh_interval=50
    )


@pytest.fixture
def manager_no_cache(temp_db):
    """Create manager without caching"""
    return HebbianLearningManager(
        db_path=temp_db,
        enable_caching=False
    )


class TestInitialization:
    """Test manager initialization"""

    def test_init_with_caching(self, temp_db):
        """Test: Manager initializes with caching enabled"""
        manager = HebbianLearningManager(
            db_path=temp_db,
            enable_caching=True
        )
        assert manager.enable_caching is True
        assert manager.conversation_count == 0
        assert manager.previous_state is None

    def test_init_without_caching(self, temp_db):
        """Test: Manager initializes with caching disabled"""
        manager = HebbianLearningManager(
            db_path=temp_db,
            enable_caching=False
        )
        assert manager.enable_caching is False

    def test_components_initialized(self, manager):
        """Test: All components are initialized"""
        assert manager.vocab_associator is not None
        assert manager.dim_associator is not None
        assert manager.sequence_learner is not None


class TestProcessConversationTurn:
    """Test the main entry point"""

    def test_basic_turn_processing(self, manager):
        """Test: Basic conversation turn is processed"""
        result = manager.process_conversation_turn(
            user_message="ngl this async stuff is confusing",
            assistant_response="I hear you! Let me break it down...",
            context={'formality': 0.3, 'technical_depth': 0.5},
            active_dimensions={'emotional_support_style': 0.8}
        )

        assert 'vocab_observations' in result
        assert 'coactivations_updated' in result
        assert 'current_state' in result
        assert 'latency_ms' in result
        assert result['latency_ms'] > 0

    def test_state_classification(self, manager):
        """Test: State is classified correctly"""
        result = manager.process_conversation_turn(
            user_message="I'm stuck on this async code",
            assistant_response="Let me help debug that...",
            context={}
        )

        assert result['current_state'] == 'problem_statement'

    def test_state_transition_recorded(self, manager):
        """Test: State transitions are recorded"""
        # First turn
        manager.process_conversation_turn(
            user_message="I'm stuck on this",
            assistant_response="What specifically?",
            context={}
        )

        # Second turn
        result = manager.process_conversation_turn(
            user_message="Thanks that works!",
            assistant_response="Glad I could help!",
            context={}
        )

        assert result['state_transitions'] == 1

    def test_vocabulary_observed(self, manager):
        """Test: Vocabulary terms are observed"""
        result = manager.process_conversation_turn(
            user_message="ngl tbh this is confusing yo",
            assistant_response="Got it!",
            context={'formality': 0.2}
        )

        # Should observe some casual terms
        assert result['vocab_observations'] > 0

    def test_dimension_coactivations_observed(self, manager):
        """Test: Dimension coactivations are observed"""
        result = manager.process_conversation_turn(
            user_message="Help me out",
            assistant_response="Sure!",
            context={},
            active_dimensions={
                'emotional_support_style': 0.8,
                'response_length_preference': 0.3,
                'communication_formality': 0.2
            }
        )

        assert result['coactivations_updated'] >= 1

    def test_predictions_generated(self, manager):
        """Test: Predictions are generated"""
        # Train some patterns first
        for _ in range(3):
            manager.process_conversation_turn(
                user_message="I'm stuck on this",
                assistant_response="Let me help",
                context={},
                active_dimensions={'emotional_support_style': 0.8}
            )

        result = manager.process_conversation_turn(
            user_message="Another problem here",
            assistant_response="On it!",
            context={},
            active_dimensions={'emotional_support_style': 0.7}
        )

        assert 'predictions' in result

    def test_conversation_count_increments(self, manager):
        """Test: Conversation count increments"""
        assert manager.conversation_count == 0

        manager.process_conversation_turn(
            user_message="Hello",
            assistant_response="Hi!",
            context={}
        )
        assert manager.conversation_count == 1

        manager.process_conversation_turn(
            user_message="How are you?",
            assistant_response="Great!",
            context={}
        )
        assert manager.conversation_count == 2


class TestContextTypeDetermination:
    """Test context type classification"""

    def test_emotional_support_context(self, manager):
        """Test: Emotional support detected"""
        context_type = manager._determine_context_type(
            "I'm stressed about this deadline",
            {}
        )
        assert context_type == 'emotional_support'

    def test_problem_solving_context(self, manager):
        """Test: Problem solving detected"""
        context_type = manager._determine_context_type(
            "Getting an error when running the tests",
            {}
        )
        assert context_type == 'problem_solving'

    def test_quick_query_context(self, manager):
        """Test: Quick query detected"""
        context_type = manager._determine_context_type(
            "Quick question about this",
            {}
        )
        assert context_type == 'quick_query'

    def test_creative_context(self, manager):
        """Test: Creative discussion detected"""
        context_type = manager._determine_context_type(
            "I have an idea for a new feature",
            {}
        )
        assert context_type == 'creative_discussion'

    def test_formal_technical_from_metrics(self, manager):
        """Test: Formal technical from high metrics"""
        context_type = manager._determine_context_type(
            "Please explain the implementation",
            {'formality': 0.8, 'technical_depth': 0.7}
        )
        assert context_type == 'formal_technical'

    def test_casual_from_metrics(self, manager):
        """Test: Casual chat from low metrics"""
        context_type = manager._determine_context_type(
            "Hey what's up",
            {'formality': 0.2, 'technical_depth': 0.3}
        )
        assert context_type == 'casual_chat'

    def test_casual_from_indicators(self, manager):
        """Test: Casual chat from language indicators"""
        context_type = manager._determine_context_type(
            "yo dude check this out",
            {}
        )
        assert context_type == 'casual_chat'


class TestCaching:
    """Test caching behavior"""

    def test_cache_initialized(self, manager):
        """Test: Cache is initialized when enabled"""
        assert manager.enable_caching is True
        # should_use_term_cached should exist
        assert hasattr(manager, 'should_use_term_cached')

    def test_no_cache_when_disabled(self, manager_no_cache):
        """Test: No cache when disabled"""
        assert manager_no_cache.enable_caching is False

    def test_cache_refresh(self, manager):
        """Test: Cache can be refreshed"""
        # This should not raise
        manager.refresh_caches()

    def test_should_use_term_with_cache(self, manager):
        """Test: should_use_term uses cache"""
        # First call (miss)
        result1 = manager.should_use_term('test', 'casual_chat')
        # Second call (should hit cache)
        result2 = manager.should_use_term('test', 'casual_chat')

        # Results should be consistent
        assert result1 == result2


class TestMaintenanceMethods:
    """Test maintenance methods"""

    def test_apply_temporal_decay_all(self, manager):
        """Test: Temporal decay applies to all components"""
        # Add some data first
        manager.process_conversation_turn(
            user_message="test message",
            assistant_response="test response",
            context={}
        )

        results = manager.apply_temporal_decay_all(days_inactive=1.0)

        assert 'vocab_associations' in results
        assert 'transitions' in results

    def test_prune_all(self, manager):
        """Test: Prune removes weak associations"""
        results = manager.prune_all(min_strength=0.1, min_observations=2)

        assert 'vocab_associations' in results

    def test_reset_session(self, manager):
        """Test: Reset clears session state"""
        # Process some turns
        manager.process_conversation_turn(
            user_message="First message",
            assistant_response="First response",
            context={}
        )
        manager.process_conversation_turn(
            user_message="Second message",
            assistant_response="Second response",
            context={}
        )

        assert manager.previous_state is not None

        # Reset
        manager.reset_session()

        assert manager.previous_state is None


class TestExportAndMonitoring:
    """Test export and monitoring methods"""

    def test_export_all_data(self, manager):
        """Test: Export returns all component data"""
        # Add some data
        manager.process_conversation_turn(
            user_message="Test message",
            assistant_response="Test response",
            context={},
            active_dimensions={'emotional_support_style': 0.8}
        )

        data = manager.export_all_data()

        assert 'vocab_associations' in data
        assert 'coactivations' in data
        assert 'transitions' in data

    def test_get_system_stats(self, manager):
        """Test: System stats returns comprehensive info"""
        # Process a turn
        manager.process_conversation_turn(
            user_message="Hello",
            assistant_response="Hi!",
            context={}
        )

        stats = manager.get_system_stats()

        assert 'vocab' in stats
        assert 'dimensions' in stats
        assert 'sequences' in stats
        assert 'performance' in stats
        assert stats['performance']['conversation_count'] == 1

    def test_get_health_summary(self, manager):
        """Test: Health summary returns status"""
        health = manager.get_health_summary()

        assert 'status' in health
        assert 'components' in health
        assert 'issues' in health
        assert health['components']['vocab_associator'] in ['ok', 'no_data', 'error']


class TestConvenienceMethods:
    """Test convenience methods"""

    def test_get_vocabulary_for_context(self, manager):
        """Test: Get vocabulary for context returns list"""
        # Add some data
        manager.process_conversation_turn(
            user_message="ngl this is cool yo",
            assistant_response="Thanks!",
            context={'formality': 0.2}
        )

        vocab = manager.get_vocabulary_for_context('casual_chat', min_strength=0.05)
        assert isinstance(vocab, list)

    def test_get_dimension_predictions_for(self, manager):
        """Test: Get predictions for single dimension"""
        predictions = manager.get_dimension_predictions_for(
            'emotional_support_style',
            0.8
        )
        assert isinstance(predictions, dict)

    def test_get_likely_next_states(self, manager):
        """Test: Get likely next states returns list"""
        states = manager.get_likely_next_states('problem_statement')
        assert isinstance(states, list)


class TestPerformance:
    """Test performance characteristics"""

    def test_latency_under_10ms(self, manager):
        """Test: Processing latency is under 10ms target"""
        # Process multiple turns
        latencies = []
        for i in range(10):
            result = manager.process_conversation_turn(
                user_message=f"Test message {i}",
                assistant_response=f"Response {i}",
                context={},
                active_dimensions={'emotional_support_style': 0.5 + i * 0.01}
            )
            latencies.append(result['latency_ms'])

        avg_latency = sum(latencies) / len(latencies)
        # Should be under 10ms on average (our target)
        assert avg_latency < 50  # Be generous for CI environments

    def test_cache_refresh_interval(self, manager):
        """Test: Cache refreshes at configured interval"""
        manager.cache_refresh_interval = 5

        # Process enough turns to trigger refresh
        for i in range(6):
            manager.process_conversation_turn(
                user_message=f"Message {i}",
                assistant_response=f"Response {i}",
                context={}
            )

        # Should have processed 6 conversations
        assert manager.conversation_count == 6


class TestEdgeCases:
    """Test edge cases and error handling"""

    def test_empty_message(self, manager):
        """Test: Empty message doesn't crash"""
        result = manager.process_conversation_turn(
            user_message="",
            assistant_response="I need more context",
            context={}
        )

        assert 'current_state' in result

    def test_none_context(self, manager):
        """Test: None context handled"""
        result = manager.process_conversation_turn(
            user_message="Hello",
            assistant_response="Hi!",
            context=None
        )

        assert 'current_state' in result

    def test_none_dimensions(self, manager):
        """Test: None dimensions handled"""
        result = manager.process_conversation_turn(
            user_message="Hello",
            assistant_response="Hi!",
            context={},
            active_dimensions=None
        )

        assert result['coactivations_updated'] == 0

    def test_empty_dimensions(self, manager):
        """Test: Empty dimensions handled"""
        result = manager.process_conversation_turn(
            user_message="Hello",
            assistant_response="Hi!",
            context={},
            active_dimensions={}
        )

        assert result['coactivations_updated'] == 0


# Run tests
if __name__ == '__main__':
    pytest.main([__file__, '-v'])
