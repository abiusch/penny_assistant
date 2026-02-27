"""
Tests for ProactivityBudget - Week 11 Safety Feature.

Tests cover:
  - Daily nudge limits (MAX_NUDGES_PER_DAY = 2)
  - Weekly resurrection limits (MAX_GOAL_RESURRECTIONS_WEEK = 1)
  - Confidence threshold enforcement (MIN_CONFIDENCE_FOR_PROACTIVE = 0.8)
  - Permission requirements for dormant goals
  - Budget summary accuracy
  - Permission message generation
"""

import os
import tempfile
import pytest
from datetime import datetime, timedelta
from unittest.mock import patch

from src.personality.proactivity_budget import (
    ProactivityBudget,
    MAX_NUDGES_PER_DAY,
    MAX_GOAL_RESURRECTIONS_WEEK,
    DORMANT_THRESHOLD_DAYS,
    REQUIRE_PERMISSION_AFTER_DAYS,
    MIN_CONFIDENCE_FOR_PROACTIVE,
)


@pytest.fixture
def budget():
    """Fresh ProactivityBudget backed by a temp DB for each test."""
    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    b = ProactivityBudget(db_path=db_path)
    yield b
    os.unlink(db_path)


# ---------------------------------------------------------------------------
# Hard limit constants sanity
# ---------------------------------------------------------------------------

class TestHardLimits:
    def test_max_nudges_per_day(self):
        assert MAX_NUDGES_PER_DAY == 2

    def test_max_resurrections_per_week(self):
        assert MAX_GOAL_RESURRECTIONS_WEEK == 1

    def test_dormant_threshold(self):
        assert DORMANT_THRESHOLD_DAYS == 14

    def test_permission_threshold(self):
        assert REQUIRE_PERMISSION_AFTER_DAYS == 7

    def test_min_confidence(self):
        assert MIN_CONFIDENCE_FOR_PROACTIVE == 0.8


# ---------------------------------------------------------------------------
# Daily nudge limits
# ---------------------------------------------------------------------------

class TestDailyNudgeLimits:
    def test_first_nudge_allowed(self, budget):
        allowed, reason = budget.can_nudge_about_goal("goal_a", confidence=0.9)
        assert allowed is True
        assert reason == "OK"

    def test_second_nudge_allowed(self, budget):
        budget.record_nudge("goal_a")
        allowed, _ = budget.can_nudge_about_goal("goal_b", confidence=0.9)
        assert allowed is True

    def test_third_nudge_blocked(self, budget):
        budget.record_nudge("goal_a")
        budget.record_nudge("goal_b")
        allowed, reason = budget.can_nudge_about_goal("goal_c", confidence=0.9)
        assert allowed is False
        assert "Daily nudge limit" in reason

    def test_budget_summary_reflects_nudges(self, budget):
        budget.record_nudge("goal_a")
        summary = budget.get_budget_summary()
        assert summary["nudges_today"] == 1
        assert summary["nudges_remaining_today"] == MAX_NUDGES_PER_DAY - 1

    def test_nudge_budget_zero_remaining(self, budget):
        for _ in range(MAX_NUDGES_PER_DAY):
            budget.record_nudge("goal_x")
        summary = budget.get_budget_summary()
        assert summary["nudges_remaining_today"] == 0


# ---------------------------------------------------------------------------
# Confidence threshold
# ---------------------------------------------------------------------------

class TestConfidenceThreshold:
    def test_high_confidence_allowed(self, budget):
        allowed, _ = budget.can_nudge_about_goal("goal_a", confidence=0.9)
        assert allowed is True

    def test_exact_threshold_allowed(self, budget):
        allowed, _ = budget.can_nudge_about_goal("goal_a", confidence=MIN_CONFIDENCE_FOR_PROACTIVE)
        assert allowed is True

    def test_below_threshold_blocked(self, budget):
        allowed, reason = budget.can_nudge_about_goal("goal_a", confidence=0.7)
        assert allowed is False
        assert "Confidence" in reason

    def test_very_low_confidence_blocked(self, budget):
        allowed, _ = budget.can_nudge_about_goal("goal_a", confidence=0.0)
        assert allowed is False


# ---------------------------------------------------------------------------
# Permission requirement for dormant goals
# ---------------------------------------------------------------------------

class TestPermissionRequirement:
    def test_fresh_goal_no_permission_needed(self, budget):
        last_mentioned = datetime.now() - timedelta(days=1)
        allowed, reason = budget.can_nudge_about_goal(
            "goal_a", last_mentioned=last_mentioned, confidence=0.9
        )
        assert allowed is True

    def test_permission_required_after_threshold(self, budget):
        last_mentioned = datetime.now() - timedelta(days=REQUIRE_PERMISSION_AFTER_DAYS)
        allowed, reason = budget.can_nudge_about_goal(
            "goal_a", last_mentioned=last_mentioned, confidence=0.9
        )
        assert allowed is False
        assert "permission required" in reason

    def test_very_old_goal_blocked(self, budget):
        last_mentioned = datetime.now() - timedelta(days=30)
        allowed, _ = budget.can_nudge_about_goal(
            "goal_a", last_mentioned=last_mentioned, confidence=0.9
        )
        assert allowed is False


# ---------------------------------------------------------------------------
# Weekly resurrection limits
# ---------------------------------------------------------------------------

class TestWeeklyResurrectionLimits:
    def test_first_resurrection_allowed(self, budget):
        last_mentioned = datetime.now() - timedelta(days=DORMANT_THRESHOLD_DAYS + 1)
        allowed, reason = budget.can_resurrect_goal("goal_a", last_mentioned)
        assert allowed is True
        assert reason == "OK"

    def test_second_resurrection_blocked(self, budget):
        last_mentioned = datetime.now() - timedelta(days=DORMANT_THRESHOLD_DAYS + 1)
        budget.record_resurrection("goal_a")
        allowed, reason = budget.can_resurrect_goal("goal_b", last_mentioned)
        assert allowed is False
        assert "Weekly resurrection limit" in reason

    def test_non_dormant_goal_blocked(self, budget):
        last_mentioned = datetime.now() - timedelta(days=5)  # Not dormant yet
        allowed, reason = budget.can_resurrect_goal("goal_a", last_mentioned)
        assert allowed is False
        assert "not dormant" in reason

    def test_resurrection_summary(self, budget):
        budget.record_resurrection("goal_a")
        summary = budget.get_budget_summary()
        assert summary["resurrections_this_week"] == 1
        assert summary["resurrections_remaining_week"] == 0


# ---------------------------------------------------------------------------
# Permission message generation
# ---------------------------------------------------------------------------

class TestPermissionMessages:
    def test_message_for_dormant_goal(self, budget):
        msg = budget.request_permission_for_goal(
            "project_x", "finish the API docs", days_dormant=20
        )
        assert "finish the API docs" in msg
        assert len(msg) > 10

    def test_message_for_recent_goal(self, budget):
        msg = budget.request_permission_for_goal(
            "project_y", "deploy the server", days_dormant=5
        )
        assert "deploy the server" in msg

    def test_message_no_days_provided(self, budget):
        msg = budget.request_permission_for_goal("goal_z", "read the report")
        assert "read the report" in msg


# ---------------------------------------------------------------------------
# Budget summary
# ---------------------------------------------------------------------------

class TestBudgetSummary:
    def test_fresh_summary(self, budget):
        summary = budget.get_budget_summary()
        assert summary["nudges_today"] == 0
        assert summary["nudges_remaining_today"] == MAX_NUDGES_PER_DAY
        assert summary["resurrections_this_week"] == 0
        assert summary["resurrections_remaining_week"] == MAX_GOAL_RESURRECTIONS_WEEK
        # Check hard limits are visible
        assert summary["limits"]["max_nudges_per_day"] == MAX_NUDGES_PER_DAY
        assert summary["limits"]["min_confidence_for_proactive"] == MIN_CONFIDENCE_FOR_PROACTIVE

    def test_summary_after_activity(self, budget):
        budget.record_nudge("g1")
        budget.record_resurrection("g2", "some goal")
        summary = budget.get_budget_summary()
        assert summary["nudges_today"] == 1
        assert summary["resurrections_this_week"] == 1
