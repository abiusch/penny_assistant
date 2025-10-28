#!/usr/bin/env python3
"""
Tests for Personality Milestone Tracker (Phase 3A Week 2)
"""

import pytest
import sqlite3
import os
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.personality.personality_milestone_tracker import PersonalityMilestoneTracker, Milestone


@pytest.fixture
def test_db_path(tmp_path):
    """Create a temporary test database."""
    db_path = tmp_path / "test_personality.db"

    # Create necessary tables
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    # Conversations table
    cursor.execute('''
        CREATE TABLE conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Personality evolution table
    cursor.execute('''
        CREATE TABLE personality_evolution (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            dimension TEXT NOT NULL,
            value REAL,
            confidence REAL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    conn.commit()
    conn.close()

    return str(db_path)


@pytest.fixture
def tracker(test_db_path):
    """Create a milestone tracker with test database."""
    return PersonalityMilestoneTracker(db_path=test_db_path)


def test_milestone_initialization(tracker):
    """Test that milestones are properly initialized."""
    assert len(tracker.milestones) > 0

    # Check that all milestone categories are present
    categories = {m.category for m in tracker.milestones}
    assert 'threshold' in categories
    assert 'confidence' in categories
    assert 'vocabulary' in categories
    assert 'conversation' in categories
    assert 'streak' in categories


def test_milestone_to_dict():
    """Test milestone to_dict conversion."""
    milestone = Milestone(
        id="test_milestone",
        name="Test Milestone",
        description="A test milestone",
        category="test",
        icon="🎯"
    )

    result = milestone.to_dict()
    assert result['id'] == "test_milestone"
    assert result['name'] == "Test Milestone"
    assert result['description'] == "A test milestone"
    assert result['category'] == "test"
    assert result['icon'] == "🎯"


def test_threshold_first_milestone(tracker, test_db_path):
    """Test first threshold crossing detection."""
    # Create personality state with one dimension above threshold
    personality_state = {
        'technical_depth_preference': {
            'value': 0.7,
            'confidence': 0.70  # Above 0.65 threshold
        },
        'communication_formality': {
            'value': 0.5,
            'confidence': 0.50  # Below threshold
        }
    }

    milestones = tracker.check_milestones(
        user_id="test_user",
        personality_state=personality_state
    )

    # Should achieve "threshold_first"
    achieved_ids = [m.id for m in milestones]
    assert 'threshold_first' in achieved_ids


def test_threshold_all_milestone(tracker, test_db_path):
    """Test all thresholds crossed detection."""
    # Create personality state with all main dimensions above threshold
    personality_state = {
        'technical_depth_preference': {
            'value': 0.7,
            'confidence': 0.70
        },
        'communication_formality': {
            'value': 0.7,
            'confidence': 0.70
        },
        'response_length_preference': {
            'value': 0.7,
            'confidence': 0.70
        }
    }

    milestones = tracker.check_milestones(
        user_id="test_user",
        personality_state=personality_state
    )

    # Should achieve both "threshold_first" and "threshold_all"
    achieved_ids = [m.id for m in milestones]
    assert 'threshold_first' in achieved_ids
    assert 'threshold_all' in achieved_ids


def test_confidence_milestone(tracker, test_db_path):
    """Test confidence milestone detection."""
    # Create personality state with high confidence
    personality_state = {
        'technical_depth_preference': {
            'value': 0.8,
            'confidence': 0.78  # Above 0.75 threshold
        }
    }

    milestones = tracker.check_milestones(
        user_id="test_user",
        personality_state=personality_state
    )

    # Should achieve "confidence_75"
    achieved_ids = [m.id for m in milestones]
    assert 'confidence_75' in achieved_ids


def test_conversation_count_milestone(tracker, test_db_path):
    """Test conversation count milestone detection."""
    conn = sqlite3.connect(test_db_path)
    cursor = conn.cursor()

    # Add 10 conversations
    for i in range(10):
        cursor.execute('''
            INSERT INTO conversations (user_id, timestamp)
            VALUES (?, ?)
        ''', ("test_user", datetime.now()))

    conn.commit()
    conn.close()

    milestones = tracker.check_milestones(user_id="test_user")

    # Should achieve "conversations_10"
    achieved_ids = [m.id for m in milestones]
    assert 'conversations_10' in achieved_ids


def test_streak_milestone(tracker, test_db_path):
    """Test streak milestone detection."""
    conn = sqlite3.connect(test_db_path)
    cursor = conn.cursor()

    # Add conversations for 3 consecutive days (including today)
    today = datetime.now().date()
    for i in range(3):
        conv_date = today - timedelta(days=i)
        cursor.execute('''
            INSERT INTO conversations (user_id, timestamp)
            VALUES (?, ?)
        ''', ("test_user", conv_date.isoformat()))

    conn.commit()
    conn.close()

    milestones = tracker.check_milestones(user_id="test_user")

    # Should achieve "streak_3"
    achieved_ids = [m.id for m in milestones]
    assert 'streak_3' in achieved_ids


def test_no_duplicate_achievements(tracker, test_db_path):
    """Test that milestones are only achieved once."""
    personality_state = {
        'technical_depth_preference': {
            'value': 0.7,
            'confidence': 0.70
        }
    }

    # Check milestones first time
    milestones_first = tracker.check_milestones(
        user_id="test_user",
        personality_state=personality_state
    )
    assert len(milestones_first) > 0

    # Check milestones second time
    milestones_second = tracker.check_milestones(
        user_id="test_user",
        personality_state=personality_state
    )

    # Should not re-achieve same milestones
    assert len(milestones_second) == 0


def test_get_achievements(tracker, test_db_path):
    """Test retrieving achievements."""
    # Achieve a milestone first
    personality_state = {
        'technical_depth_preference': {
            'value': 0.7,
            'confidence': 0.70
        }
    }

    tracker.check_milestones(
        user_id="test_user",
        personality_state=personality_state
    )

    # Get achievements
    achievements = tracker.get_achievements(user_id="test_user")

    assert len(achievements) > 0
    assert 'id' in achievements[0]
    assert 'name' in achievements[0]
    assert 'achieved_at' in achievements[0]


def test_vocabulary_count_estimation(tracker, test_db_path):
    """Test vocabulary count estimation."""
    conn = sqlite3.connect(test_db_path)
    cursor = conn.cursor()

    # Add personality evolution entries for different dimensions
    for i in range(5):
        cursor.execute('''
            INSERT INTO personality_evolution (user_id, dimension, value, confidence)
            VALUES (?, ?, ?, ?)
        ''', ("test_user", f"dimension_{i}", 0.5, 0.6))

    conn.commit()
    conn.close()

    # Get vocabulary count
    vocab_count = tracker._get_vocabulary_count("test_user")

    # Should be ~10 (5 dimensions * 2)
    assert vocab_count == 10


def test_multi_user_isolation(tracker, test_db_path):
    """Test that achievements are isolated per user."""
    personality_state = {
        'technical_depth_preference': {
            'value': 0.7,
            'confidence': 0.70
        }
    }

    # User 1 achieves milestone
    tracker.check_milestones(
        user_id="user1",
        personality_state=personality_state
    )

    # User 2 should still be able to achieve same milestone
    milestones_user2 = tracker.check_milestones(
        user_id="user2",
        personality_state=personality_state
    )

    assert len(milestones_user2) > 0


def test_milestone_persistence(tracker, test_db_path):
    """Test that achievements persist across tracker instances."""
    personality_state = {
        'technical_depth_preference': {
            'value': 0.7,
            'confidence': 0.70
        }
    }

    # Achieve milestone
    tracker.check_milestones(
        user_id="test_user",
        personality_state=personality_state
    )

    # Create new tracker instance
    new_tracker = PersonalityMilestoneTracker(db_path=test_db_path)

    # Check achievements persist
    achievements = new_tracker.get_achievements(user_id="test_user")
    assert len(achievements) > 0


def test_confidence_90_milestone(tracker, test_db_path):
    """Test high confidence milestone (0.90)."""
    personality_state = {
        'technical_depth_preference': {
            'value': 0.9,
            'confidence': 0.92  # Above 0.90
        }
    }

    milestones = tracker.check_milestones(
        user_id="test_user",
        personality_state=personality_state
    )

    achieved_ids = [m.id for m in milestones]
    # Should achieve both 75 and 90
    assert 'confidence_75' in achieved_ids
    assert 'confidence_90' in achieved_ids


def test_conversation_count_100(tracker, test_db_path):
    """Test century club milestone."""
    conn = sqlite3.connect(test_db_path)
    cursor = conn.cursor()

    # Add 100 conversations
    for i in range(100):
        cursor.execute('''
            INSERT INTO conversations (user_id, timestamp)
            VALUES (?, ?)
        ''', ("test_user", datetime.now()))

    conn.commit()
    conn.close()

    milestones = tracker.check_milestones(user_id="test_user")

    achieved_ids = [m.id for m in milestones]
    # Should achieve 10, 50, and 100
    assert 'conversations_10' in achieved_ids
    assert 'conversations_50' in achieved_ids
    assert 'conversations_100' in achieved_ids


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
