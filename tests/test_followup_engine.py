"""
Tests for FollowUpEngine - Week 12.

Tests cover:
  - Follow-up generation for suspended goals
  - Budget gating (no follow-up when limit hit)
  - Permission requirement detection
  - Message type selection (soft_nudge / last_chance)
  - can_follow_up() checks
  - Summary report
"""

import os
import tempfile
import pytest
from datetime import datetime, timedelta

from src.personality.goal_tracker import GoalTracker, GoalState
from src.personality.proactivity_budget import (
    ProactivityBudget,
    MAX_NUDGES_PER_DAY,
    REQUIRE_PERMISSION_AFTER_DAYS,
    DORMANT_THRESHOLD_DAYS,
)
from src.personality.followup_engine import (
    FollowUpEngine,
    SOFT_NUDGE_TEMPLATES,
    LAST_CHANCE_TEMPLATES,
)


@pytest.fixture
def components():
    """Shared temp DB for tracker, budget, and engine."""
    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    tracker = GoalTracker(db_path=db_path)
    budget  = ProactivityBudget(db_path=db_path)
    engine  = FollowUpEngine(tracker, budget, confidence=0.9)
    yield tracker, budget, engine
    os.unlink(db_path)


def _add_suspended_goal(tracker, description="finish the report", days_ago=2):
    """Helper: insert a suspended goal backdated by `days_ago` days."""
    tracker.process_turn(f"I want to {description}")
    goal_id = tracker.get_active_goals()[0]["goal_id"]
    old_ts = (datetime.now() - timedelta(days=days_ago)).isoformat()
    with tracker._get_conn() as conn:
        conn.execute(
            "UPDATE goals SET last_mentioned = ?, state = 'suspended' WHERE goal_id = ?",
            (old_ts, goal_id),
        )
    return goal_id


# ---------------------------------------------------------------------------
# Basic follow-up generation
# ---------------------------------------------------------------------------

class TestFollowUpGeneration:
    def test_generates_followup_for_suspended_goal(self, components):
        tracker, budget, engine = components
        _add_suspended_goal(tracker, days_ago=2)
        followups = engine.get_followups_for_session()
        assert len(followups) == 1
        assert followups[0]["message"]
        assert followups[0]["type"] == "soft_nudge"

    def test_followup_contains_goal_description(self, components):
        tracker, budget, engine = components
        _add_suspended_goal(tracker, "deploy the staging server", days_ago=3)
        followups = engine.get_followups_for_session()
        assert len(followups) == 1
        assert "staging server" in followups[0]["message"] or \
               "deploy" in followups[0]["message"]

    def test_no_followup_when_no_suspended_goals(self, components):
        _, _, engine = components
        assert engine.get_followups_for_session() == []

    def test_max_followups_respected(self, components):
        tracker, budget, engine = components
        for i in range(3):
            _add_suspended_goal(tracker, f"goal number {i}", days_ago=2)
            # reset budget between calls
        followups = engine.get_followups_for_session(max_followups=1)
        assert len(followups) <= 1

    def test_records_nudge_against_budget(self, components):
        tracker, budget, engine = components
        _add_suspended_goal(tracker, days_ago=2)
        engine.get_followups_for_session()
        summary = budget.get_budget_summary()
        assert summary["nudges_today"] == 1


# ---------------------------------------------------------------------------
# Budget gating
# ---------------------------------------------------------------------------

class TestBudgetGating:
    def test_blocked_when_daily_limit_exhausted(self, components):
        tracker, budget, engine = components
        # Fill the budget
        for _ in range(MAX_NUDGES_PER_DAY):
            budget.record_nudge("some_goal")

        _add_suspended_goal(tracker, days_ago=2)
        followups = engine.get_followups_for_session()
        assert followups == []

    def test_blocked_by_low_confidence(self, components):
        tracker, budget, _ = components
        low_conf_engine = FollowUpEngine(tracker, budget, confidence=0.5)
        _add_suspended_goal(tracker, days_ago=2)
        assert low_conf_engine.get_followups_for_session() == []

    def test_blocked_when_goal_needs_permission(self, components):
        tracker, budget, engine = components
        # Days dormant >= REQUIRE_PERMISSION_AFTER_DAYS
        _add_suspended_goal(tracker, days_ago=REQUIRE_PERMISSION_AFTER_DAYS + 1)
        # Budget blocks: permission required
        followups = engine.get_followups_for_session()
        assert followups == []


# ---------------------------------------------------------------------------
# Permission detection
# ---------------------------------------------------------------------------

class TestPermissionDetection:
    def test_needs_permission_for_old_goal(self, components):
        tracker, budget, engine = components
        goal_id = _add_suspended_goal(
            tracker, "refactor the auth system",
            days_ago=REQUIRE_PERMISSION_AFTER_DAYS + 2
        )
        needs, msg = engine.needs_permission(goal_id)
        assert needs is True
        assert msg is not None
        assert "refactor the auth system" in msg

    def test_no_permission_needed_for_fresh_goal(self, components):
        tracker, budget, engine = components
        goal_id = _add_suspended_goal(tracker, days_ago=1)
        needs, msg = engine.needs_permission(goal_id)
        assert needs is False

    def test_nonexistent_goal_no_permission(self, components):
        _, _, engine = components
        needs, msg = engine.needs_permission("ghost_id")
        assert needs is False
        assert msg is None


# ---------------------------------------------------------------------------
# can_follow_up
# ---------------------------------------------------------------------------

class TestCanFollowUp:
    def test_can_follow_up_fresh_suspended_goal(self, components):
        tracker, budget, engine = components
        goal_id = _add_suspended_goal(tracker, days_ago=2)
        allowed, reason = engine.can_follow_up(goal_id)
        assert allowed is True

    def test_cannot_follow_up_nonexistent(self, components):
        _, _, engine = components
        allowed, _ = engine.can_follow_up("fake_id")
        assert allowed is False

    def test_cannot_follow_up_budget_exhausted(self, components):
        tracker, budget, engine = components
        for _ in range(MAX_NUDGES_PER_DAY):
            budget.record_nudge("x")
        goal_id = _add_suspended_goal(tracker, days_ago=2)
        allowed, _ = engine.can_follow_up(goal_id)
        assert allowed is False


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------

class TestFollowUpSummary:
    def test_empty_summary(self, components):
        _, _, engine = components
        summary = engine.get_followup_summary()
        assert summary["suspended_goals"] == 0
        assert summary["followable_now"] == 0

    def test_summary_after_suspended_goal(self, components):
        tracker, budget, engine = components
        _add_suspended_goal(tracker, days_ago=2)
        summary = engine.get_followup_summary()
        assert summary["suspended_goals"] == 1
        assert summary["followable_now"] == 1

    def test_summary_blocked_when_budget_full(self, components):
        tracker, budget, engine = components
        for _ in range(MAX_NUDGES_PER_DAY):
            budget.record_nudge("x")
        _add_suspended_goal(tracker, days_ago=2)
        summary = engine.get_followup_summary()
        assert summary["followable_now"] == 0
        assert summary["blocked"] == 1
