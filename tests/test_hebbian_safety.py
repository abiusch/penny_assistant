"""
Tests for Hebbian Learning Safety Features
Week 10 Day 9: Quarantine, Turn Budget, and Observability

Tests cover:
- Learning quarantine (staging -> permanent)
- Turn budget enforcement
- Mini-observability and drift detection
- Pipeline integration safety
"""

import pytest
import os
import sys
import tempfile
import sqlite3
import time
from datetime import datetime, timedelta

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.personality.hebbian.hebbian_learning_manager import (
    HebbianLearningManager,
    TurnBudget
)


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

        # Sequence tables
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
    """Create manager with temp database and safety features"""
    return HebbianLearningManager(
        db_path=temp_db,
        enable_caching=True,
        promotion_min_observations=5,
        promotion_min_days=7,
        max_staging_age_days=30,
        turn_budget_max_writes=5,
        turn_budget_max_time_ms=15000
    )


# ============================================================================
# LEARNING QUARANTINE TESTS
# ============================================================================

class TestLearningQuarantine:
    """Test learning quarantine system."""

    def test_patterns_go_to_staging_first(self, manager):
        """Patterns should start in staging, not permanent."""
        # Process one conversation
        manager.process_conversation_turn(
            user_message="ngl this is cool",
            assistant_response="Thanks!",
            context={'formality': 0.3},
            active_dimensions={'emotional_support_style': 0.8, 'response_length_preference': 0.3}
        )

        # Should have staging patterns, no permanent yet
        assert len(manager.staging_patterns) > 0
        assert len(manager.permanent_patterns) == 0

    def test_promotion_requires_minimum_observations(self, manager):
        """Patterns need 5+ observations to promote."""
        # Observe pattern 4 times (below threshold)
        for i in range(4):
            manager.process_conversation_turn(
                user_message=f"test message {i}",
                assistant_response="response",
                context={'formality': 0.5},
                active_dimensions={'emotional_support_style': 0.8, 'response_length_preference': 0.3}
            )

        manager._check_promotions()

        # Should still be in staging
        assert len(manager.permanent_patterns) == 0

    def test_promotion_requires_time_span(self, manager):
        """Patterns need 7+ days span to promote."""
        # Create staging pattern with 5 observations but same day
        pattern_key = "test:pattern1"
        now = datetime.now()

        manager.staging_patterns[pattern_key] = {
            'pattern_type': 'test',
            'pattern': {'test': 'data'},
            'observations': [
                {'timestamp': now, 'context': {}}
                for _ in range(5)
            ],
            'first_seen': now,
            'last_seen': now
        }

        # Should not promote (same day)
        assert not manager._should_promote(manager.staging_patterns[pattern_key])

    def test_promotion_requires_distributed_observations(self, manager):
        """Patterns need observations on 3+ different days."""
        pattern_key = "test:pattern2"
        first_seen = datetime.now() - timedelta(days=10)

        # 5 observations but only on 2 days
        manager.staging_patterns[pattern_key] = {
            'pattern_type': 'test',
            'pattern': {'test': 'data'},
            'observations': [
                {'timestamp': first_seen, 'context': {}},
                {'timestamp': first_seen, 'context': {}},
                {'timestamp': first_seen + timedelta(days=8), 'context': {}},
                {'timestamp': first_seen + timedelta(days=8), 'context': {}},
                {'timestamp': first_seen + timedelta(days=8), 'context': {}}
            ],
            'first_seen': first_seen,
            'last_seen': first_seen + timedelta(days=8)
        }

        # Should not promote (only 2 unique days)
        assert not manager._should_promote(manager.staging_patterns[pattern_key])

    def test_promotion_after_meeting_all_criteria(self, manager):
        """Patterns promote after meeting all criteria."""
        pattern_key = "test:pattern3"
        first_seen = datetime.now() - timedelta(days=10)

        # 5 observations across 5 different days
        manager.staging_patterns[pattern_key] = {
            'pattern_type': 'test',
            'pattern': {'test': 'data'},
            'observations': [
                {'timestamp': first_seen + timedelta(days=i), 'context': {}}
                for i in range(5)
            ],
            'first_seen': first_seen,
            'last_seen': first_seen + timedelta(days=8)
        }

        # Should promote (meets all criteria)
        assert manager._should_promote(manager.staging_patterns[pattern_key])

        # Do promotion
        manager._check_promotions()
        assert len(manager.permanent_patterns) == 1
        assert pattern_key not in manager.staging_patterns

    def test_staging_expires_after_max_age(self, manager):
        """Old staging patterns should expire."""
        pattern_key = "test:old_pattern"
        old_date = datetime.now() - timedelta(days=35)

        manager.staging_patterns[pattern_key] = {
            'pattern_type': 'test',
            'pattern': {'test': 'data'},
            'observations': [],
            'first_seen': old_date,
            'last_seen': old_date
        }

        # Should expire
        assert manager._should_expire(manager.staging_patterns[pattern_key])

        # Do cleanup
        manager._check_promotions()
        assert pattern_key not in manager.staging_patterns

    def test_pattern_hash_is_deterministic(self, manager):
        """Pattern hash should be deterministic for same input."""
        pattern = {'terms': ['hello', 'world'], 'context_type': 'casual'}

        hash1 = manager._pattern_hash(pattern)
        hash2 = manager._pattern_hash(pattern)

        assert hash1 == hash2
        assert len(hash1) == 8  # 8 character hash


# ============================================================================
# TURN BUDGET TESTS
# ============================================================================

class TestTurnBudget:
    """Test turn budget enforcement."""

    def test_write_budget_enforced(self):
        """Write budget should prevent excessive writes."""
        budget = TurnBudget(max_learning_writes=5)
        budget.start_turn()

        # Try to write 10 times
        writes_allowed = 0
        for _ in range(10):
            if budget.can_write():
                budget.record_write()
                writes_allowed += 1

        # Should be limited to MAX_LEARNING_WRITES
        assert writes_allowed == 5
        assert not budget.can_write()

    def test_lookup_budget_enforced(self):
        """Lookup budget should prevent excessive lookups."""
        budget = TurnBudget(max_cache_lookups=20)
        budget.start_turn()

        # Try to lookup 30 times
        lookups_allowed = 0
        for _ in range(30):
            if budget.can_lookup():
                budget.record_lookup()
                lookups_allowed += 1

        # Should be limited to MAX_CACHE_LOOKUPS
        assert lookups_allowed == 20
        assert not budget.can_lookup()

    def test_query_budget_enforced(self):
        """Query budget should prevent excessive queries."""
        budget = TurnBudget(max_db_queries=10)
        budget.start_turn()

        queries_allowed = 0
        for _ in range(15):
            if budget.can_query():
                budget.record_query()
                queries_allowed += 1

        assert queries_allowed == 10
        assert not budget.can_query()

    def test_time_budget_tracking(self):
        """Time budget should track elapsed time."""
        budget = TurnBudget(max_turn_time_ms=15000)
        budget.start_turn()

        time.sleep(0.05)  # Sleep 50ms

        time_remaining = budget.time_remaining_ms()
        assert time_remaining < budget.MAX_TURN_TIME_MS
        assert time_remaining > 0

    def test_budget_summary(self):
        """Budget summary should show current usage."""
        budget = TurnBudget()
        budget.start_turn()

        budget.record_write()
        budget.record_write()
        budget.record_lookup()

        summary = budget.get_summary()
        assert '2/5' in summary['writes']
        assert '1/20' in summary['lookups']
        assert 'time_remaining_ms' in summary

    def test_budget_resets_on_new_turn(self):
        """Budget should reset when starting new turn."""
        budget = TurnBudget(max_learning_writes=5)
        budget.start_turn()

        # Use up writes
        for _ in range(5):
            budget.record_write()
        assert not budget.can_write()

        # Start new turn
        budget.start_turn()
        assert budget.can_write()
        assert budget.operations['writes'] == 0


# ============================================================================
# MINI-OBSERVABILITY TESTS
# ============================================================================

class TestMiniObservability:
    """Test observability features."""

    def test_learning_report_generation(self, manager):
        """Learning report should contain key metrics."""
        # Add some test data
        manager.staging_patterns['test1'] = {
            'pattern_type': 'test',
            'pattern': {},
            'observations': [{'timestamp': datetime.now(), 'context': {}}],
            'first_seen': datetime.now(),
            'last_seen': datetime.now()
        }

        report = manager.get_learning_report()

        assert 'summary' in report
        assert 'recent_events' in report
        assert 'drift_warnings' in report
        assert report['summary']['staging_patterns'] == 1

    def test_drift_detection_high_staging(self, manager):
        """Drift detection should warn on high staging count."""
        # Create 101 staging patterns
        for i in range(101):
            manager.staging_patterns[f'test:{i}'] = {
                'pattern_type': 'test',
                'pattern': {},
                'observations': [],
                'first_seen': datetime.now(),
                'last_seen': datetime.now()
            }

        warnings = manager._check_drift()
        assert len(warnings) > 0
        assert 'High staging count' in warnings[0]

    def test_export_learning_log(self, manager, tmp_path):
        """Learning log should export to JSON."""
        # Add test data
        manager.staging_patterns['test1'] = {
            'pattern_type': 'test',
            'pattern': {},
            'observations': [],
            'first_seen': datetime.now(),
            'last_seen': datetime.now()
        }

        # Export
        log_path = tmp_path / "learning_log.json"
        manager.export_learning_log(str(log_path))

        # Verify file exists and is valid JSON
        assert log_path.exists()
        import json
        with open(log_path) as f:
            log = json.load(f)

        assert 'export_metadata' in log
        assert 'staging_patterns' in log

    def test_event_logging(self, manager):
        """Events should be logged for observability."""
        initial_events = len(manager._recent_events)

        # Process a turn which logs an event
        manager.process_conversation_turn(
            user_message="Test message",
            assistant_response="Test response",
            context={}
        )

        assert len(manager._recent_events) > initial_events

    def test_promotion_progress_tracking(self, manager):
        """Should track how close patterns are to promotion."""
        pattern = {
            'pattern_type': 'test',
            'pattern': {},
            'observations': [{'timestamp': datetime.now(), 'context': {}} for _ in range(3)],
            'first_seen': datetime.now() - timedelta(days=4),
            'last_seen': datetime.now()
        }

        progress = manager._promotion_progress(pattern)

        assert 'obs:3/5' in progress
        assert 'days:4/7' in progress


# ============================================================================
# INTEGRATION SAFETY TESTS
# ============================================================================

class TestIntegrationSafety:
    """Test safe integration behaviors."""

    def test_result_includes_safety_stats(self, manager):
        """Process result should include safety statistics."""
        result = manager.process_conversation_turn(
            user_message="Hello world",
            assistant_response="Hi!",
            context={}
        )

        assert 'staging_count' in result
        assert 'permanent_count' in result
        assert 'promotions_this_turn' in result
        assert 'budget_summary' in result

    def test_health_summary_includes_safety_components(self, manager):
        """Health summary should check safety components."""
        health = manager.get_health_summary()

        assert 'quarantine_system' in health['components']
        assert 'turn_budget' in health['components']
        assert 'drift_warnings' in health

    def test_system_stats_includes_safety_config(self, manager):
        """System stats should include safety configuration."""
        stats = manager.get_system_stats()

        assert 'safety' in stats
        assert stats['safety']['promotion_min_observations'] == 5
        assert stats['safety']['promotion_min_days'] == 7


# ============================================================================
# PERSISTENCE TESTS
# ============================================================================

class TestPersistence:
    """Test database persistence of safety data."""

    def test_staging_patterns_persist_to_db(self, manager):
        """Staging patterns should be saved to database."""
        manager.process_conversation_turn(
            user_message="Test message for persistence",
            assistant_response="Response",
            context={'formality': 0.5},
            active_dimensions={'emotional_support_style': 0.8, 'response_length_preference': 0.3}
        )

        # Check database
        with sqlite3.connect(manager.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM hebbian_staging_patterns")
            count = cursor.fetchone()[0]

        assert count > 0

    def test_promotion_log_persists(self, manager):
        """Promotions should be logged to database."""
        # Create a pattern that meets promotion criteria
        pattern_key = "test:promotable"
        first_seen = datetime.now() - timedelta(days=10)

        manager.staging_patterns[pattern_key] = {
            'pattern_type': 'test',
            'pattern': {'test': 'data'},
            'observations': [
                {'timestamp': first_seen + timedelta(days=i), 'context': {}}
                for i in range(5)
            ],
            'first_seen': first_seen,
            'last_seen': datetime.now()
        }

        # Promote it
        manager._check_promotions()

        # Check promotion log in database
        with sqlite3.connect(manager.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM hebbian_promotion_log")
            count = cursor.fetchone()[0]

        assert count > 0


# ============================================================================
# EDGE CASES
# ============================================================================

class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_staging_patterns_handled(self, manager):
        """Should handle empty staging patterns gracefully."""
        report = manager.get_learning_report()
        assert report['summary']['staging_patterns'] == 0

    def test_none_context_handled(self, manager):
        """Should handle None context gracefully."""
        result = manager.process_conversation_turn(
            user_message="Test",
            assistant_response="Response",
            context=None
        )

        assert 'current_state' in result

    def test_very_long_message_handled(self, manager):
        """Should handle very long messages."""
        long_message = "word " * 1000

        result = manager.process_conversation_turn(
            user_message=long_message,
            assistant_response="OK",
            context={}
        )

        assert 'current_state' in result
        assert 'error' not in result


# Run tests
if __name__ == '__main__':
    pytest.main([__file__, '-v'])
