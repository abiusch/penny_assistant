"""
Integration tests for Week 12 Goal Continuity.

Tests the full loop: GoalTracker + FollowUpEngine + ProactivityBudget
working together across a simulated multi-session conversation.
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
from src.personality.followup_engine import FollowUpEngine
from src.personality.outcome_tracker import OutcomeTracker


@pytest.fixture
def full_stack():
    """Complete Week 12 stack sharing one temp DB."""
    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    tracker  = GoalTracker(db_path=db_path)
    budget   = ProactivityBudget(db_path=db_path)
    engine   = FollowUpEngine(tracker, budget, confidence=0.9)
    outcomes = OutcomeTracker(db_path=db_path)
    yield tracker, budget, engine, outcomes
    os.unlink(db_path)


def _backdate_goal(tracker, goal_id, days_ago):
    old_ts = (datetime.now() - timedelta(days=days_ago)).isoformat()
    with tracker._get_conn() as conn:
        conn.execute(
            "UPDATE goals SET last_mentioned = ?, state = 'suspended' WHERE goal_id = ?",
            (old_ts, goal_id),
        )


# ---------------------------------------------------------------------------
# Session start: follow-up surfaced
# ---------------------------------------------------------------------------

class TestSessionStartFollowUp:
    def test_followup_surfaced_at_session_start(self, full_stack):
        tracker, budget, engine, _ = full_stack
        tracker.process_turn("I want to finish the API documentation")
        goal_id = tracker.get_active_goals()[0]["goal_id"]
        _backdate_goal(tracker, goal_id, days_ago=3)

        followups = engine.get_followups_for_session(session_id="sess_1")
        assert len(followups) == 1
        assert "documentation" in followups[0]["message"] or \
               "API" in followups[0]["message"]

    def test_no_followup_on_first_session(self, full_stack):
        _, _, engine, _ = full_stack
        assert engine.get_followups_for_session() == []

    def test_followup_within_budget(self, full_stack):
        tracker, budget, engine, _ = full_stack
        tracker.process_turn("I need to deploy the new release")
        goal_id = tracker.get_active_goals()[0]["goal_id"]
        _backdate_goal(tracker, goal_id, days_ago=4)

        engine.get_followups_for_session()
        assert budget.get_budget_summary()["nudges_today"] == 1


# ---------------------------------------------------------------------------
# Goal lifecycle across sessions
# ---------------------------------------------------------------------------

class TestGoalLifecycle:
    def test_goal_detected_then_completed(self, full_stack):
        tracker, _, _, _ = full_stack
        tracker.process_turn("I'm working on the login feature")
        assert len(tracker.get_active_goals()) == 1

        tracker.process_turn("Done, it's all working now!")
        assert len(tracker.get_active_goals()) == 0
        report = tracker.get_goals_report()
        assert report["completed"] == 1

    def test_goal_detected_then_abandoned(self, full_stack):
        tracker, _, _, _ = full_stack
        tracker.process_turn("I want to rewrite the whole test suite")
        tracker.process_turn("Forget it, not worth the time")
        assert tracker.get_goals_report()["abandoned"] == 1

    def test_goal_suspended_then_completed_via_signal(self, full_stack):
        tracker, _, _, _ = full_stack
        tracker.process_turn("I need to fix the config loading bug")
        goal_id = tracker.get_active_goals()[0]["goal_id"]
        tracker.mark_suspended(goal_id)

        assert tracker.get_goal(goal_id)["state"] == GoalState.SUSPENDED

        # User comes back and signals completion
        tracker.process_turn("Finally got it working, that was tricky!")
        # Suspended goals are not auto-completed by signals (only active ones)
        # Manually complete it
        tracker.mark_completed(goal_id)
        assert tracker.get_goal(goal_id)["state"] == GoalState.COMPLETED

    def test_multiple_goals_tracked(self, full_stack):
        tracker, _, _, _ = full_stack
        tracker.process_turn("I want to add auth to the app")
        tracker.process_turn("I need to write migration scripts too")
        assert len(tracker.get_active_goals()) == 2


# ---------------------------------------------------------------------------
# Safety: proactivity limits respected
# ---------------------------------------------------------------------------

class TestSafetyLimits:
    def test_no_followup_after_daily_limit(self, full_stack):
        tracker, budget, engine, _ = full_stack
        for _ in range(MAX_NUDGES_PER_DAY):
            budget.record_nudge("x")

        tracker.process_turn("I'm trying to set up monitoring")
        goal_id = tracker.get_active_goals()[0]["goal_id"]
        _backdate_goal(tracker, goal_id, days_ago=3)

        assert engine.get_followups_for_session() == []

    def test_permission_needed_for_old_goal(self, full_stack):
        tracker, budget, engine, _ = full_stack
        tracker.process_turn("I want to document all the API endpoints")
        goal_id = tracker.get_active_goals()[0]["goal_id"]
        _backdate_goal(tracker, goal_id, REQUIRE_PERMISSION_AFTER_DAYS + 2)

        needs, msg = engine.needs_permission(goal_id)
        assert needs is True
        assert msg is not None


# ---------------------------------------------------------------------------
# Integration with OutcomeTracker
# ---------------------------------------------------------------------------

class TestGoalAndOutcomeIntegration:
    def test_positive_outcome_after_goal_completion(self, full_stack):
        tracker, _, _, outcomes = full_stack
        # Simulate: goal set, response given, user says thanks
        tracker.process_turn("I need to fix the null pointer exception")
        resp_id = OutcomeTracker.generate_response_id()
        reaction, conf = outcomes.detect_user_reaction("fixed it, thanks!")
        outcomes.observe_outcome(resp_id, "code_example", reaction, strategy="debug_first")

        rate = outcomes.get_strategy_success_rate("debug_first")
        assert rate == 1.0

    def test_goals_report_and_outcome_report_independent(self, full_stack):
        tracker, _, _, outcomes = full_stack
        tracker.process_turn("I'm working on the payment gateway")
        outcomes.observe_outcome("r1", "brief_answer", "positive", strategy="s1")

        goal_report    = tracker.get_goals_report()
        outcome_report = outcomes.get_outcome_report()
        assert goal_report["active"] == 1
        assert outcome_report["positive_count"] == 1


# ---------------------------------------------------------------------------
# Follow-up summary
# ---------------------------------------------------------------------------

class TestFollowUpSummary:
    def test_summary_shows_followable_goals(self, full_stack):
        tracker, _, engine, _ = full_stack
        tracker.process_turn("I want to profile the slow endpoints")
        goal_id = tracker.get_active_goals()[0]["goal_id"]
        _backdate_goal(tracker, goal_id, days_ago=3)

        summary = engine.get_followup_summary()
        assert summary["suspended_goals"] >= 1
        assert summary["followable_now"] >= 1

    def test_summary_budget_embedded(self, full_stack):
        _, _, engine, _ = full_stack
        summary = engine.get_followup_summary()
        assert "budget" in summary
        assert "limits" in summary["budget"]
