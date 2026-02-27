"""
Tests for GoalTracker - Week 12.

Tests cover:
  - Goal detection from user messages
  - Goal state transitions (active → suspended → completed / abandoned)
  - Auto-suspension of stale goals
  - process_turn() composite behavior
  - Goals report
  - Edge cases
"""

import os
import tempfile
import pytest
from datetime import datetime, timedelta

from src.personality.goal_tracker import (
    GoalTracker,
    GoalState,
    _extract_goal_text,
    _is_completion,
    _is_abandon,
)


@pytest.fixture
def tracker():
    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    t = GoalTracker(db_path=db_path)
    yield t
    os.unlink(db_path)


# ---------------------------------------------------------------------------
# Pattern detection helpers
# ---------------------------------------------------------------------------

class TestPatternDetection:
    def test_extract_goal_from_want_to(self):
        text = "I want to fix the login bug today"
        goal = _extract_goal_text(text)
        assert goal is not None
        assert "fix" in goal.lower() or "login" in goal.lower()

    def test_extract_goal_from_trying(self):
        goal = _extract_goal_text("I'm trying to deploy the new feature")
        assert goal is not None

    def test_extract_goal_from_working_on(self):
        goal = _extract_goal_text("I've been working on the migration script")
        assert goal is not None

    def test_no_goal_in_question(self):
        goal = _extract_goal_text("What time is it?")
        assert goal is None

    def test_completion_thanks_worked(self):
        assert _is_completion("thanks, that worked!") is True

    def test_completion_done(self):
        assert _is_completion("done") is True

    def test_completion_solved(self):
        assert _is_completion("solved it") is True

    def test_no_completion_in_neutral(self):
        assert _is_completion("what's next?") is False

    def test_abandon_nevermind(self):
        assert _is_abandon("nevermind, forget it") is True

    def test_abandon_moving_on(self):
        assert _is_abandon("moving on") is True

    def test_no_abandon_in_neutral(self):
        assert _is_abandon("let me try again") is False


# ---------------------------------------------------------------------------
# Goal creation
# ---------------------------------------------------------------------------

class TestGoalCreation:
    def test_new_goal_detected(self, tracker):
        result = tracker.process_turn("I want to set up CI/CD for this project")
        assert result["new_goal"] is not None
        assert result["new_goal"]["state"] == GoalState.ACTIVE

    def test_goal_stored_in_db(self, tracker):
        tracker.process_turn("I need to write unit tests for the API")
        goals = tracker.get_active_goals()
        assert len(goals) == 1

    def test_no_goal_from_question(self, tracker):
        result = tracker.process_turn("What is the weather today?")
        assert result["new_goal"] is None

    def test_goal_has_description(self, tracker):
        tracker.process_turn("I'm trying to optimise the database queries")
        goals = tracker.get_active_goals()
        assert len(goals[0]["description"]) > 5

    def test_goal_id_unique(self, tracker):
        tracker.process_turn("I want to refactor the auth module")
        tracker.process_turn("I need to add error handling too")
        goals = tracker.get_active_goals()
        ids = [g["goal_id"] for g in goals]
        assert len(set(ids)) == len(ids)


# ---------------------------------------------------------------------------
# State transitions
# ---------------------------------------------------------------------------

class TestStateTransitions:
    def test_mark_completed(self, tracker):
        tracker.process_turn("I'm trying to write docs")
        goal_id = tracker.get_active_goals()[0]["goal_id"]
        result = tracker.mark_completed(goal_id)
        assert result is True
        goal = tracker.get_goal(goal_id)
        assert goal["state"] == GoalState.COMPLETED
        assert goal["completed_at"] is not None

    def test_mark_abandoned(self, tracker):
        tracker.process_turn("I want to migrate the database")
        goal_id = tracker.get_active_goals()[0]["goal_id"]
        tracker.mark_abandoned(goal_id)
        assert tracker.get_goal(goal_id)["state"] == GoalState.ABANDONED

    def test_mark_suspended(self, tracker):
        tracker.process_turn("I need to fix the memory leak")
        goal_id = tracker.get_active_goals()[0]["goal_id"]
        tracker.mark_suspended(goal_id)
        assert tracker.get_goal(goal_id)["state"] == GoalState.SUSPENDED

    def test_mark_nonexistent_returns_false(self, tracker):
        assert tracker.mark_completed("fake_id_xyz") is False

    def test_completion_signal_completes_active_goals(self, tracker):
        tracker.process_turn("I'm working on the search feature")
        result = tracker.process_turn("Done, it works perfectly!")
        assert any(g["state"] == GoalState.COMPLETED
                   for g in result["updated_goals"])

    def test_abandon_signal_abandons_active_goals(self, tracker):
        tracker.process_turn("I want to rewrite the frontend")
        result = tracker.process_turn("Forget it, moving on")
        assert any(g["state"] == GoalState.ABANDONED
                   for g in result["updated_goals"])


# ---------------------------------------------------------------------------
# Auto-suspension
# ---------------------------------------------------------------------------

class TestAutoSuspension:
    def test_stale_goal_auto_suspended(self, tracker):
        # Create a goal then backdate last_mentioned
        tracker.process_turn("I'm trying to set up Docker")
        goal_id = tracker.get_active_goals()[0]["goal_id"]

        # Backdate to 2 days ago (beyond AUTO_SUSPEND_DAYS=1)
        old_ts = (datetime.now() - timedelta(days=2)).isoformat()
        with tracker._get_conn() as conn:
            conn.execute(
                "UPDATE goals SET last_mentioned = ? WHERE goal_id = ?",
                (old_ts, goal_id),
            )

        # Next turn triggers auto-suspend check
        result = tracker.process_turn("What's the weather?")
        assert any(g["goal_id"] == goal_id for g in result["suspended_now"])
        assert tracker.get_goal(goal_id)["state"] == GoalState.SUSPENDED

    def test_recent_goal_not_auto_suspended(self, tracker):
        tracker.process_turn("I need to update the config files")
        result = tracker.process_turn("ok so continuing with that")
        # Active goals touched, none suspended
        active = tracker.get_active_goals()
        assert len(active) >= 1


# ---------------------------------------------------------------------------
# Days since last mentioned
# ---------------------------------------------------------------------------

class TestDaysSinceLastMentioned:
    def test_just_created_goal_is_zero_days(self, tracker):
        tracker.process_turn("I want to clean up the test suite")
        goal_id = tracker.get_active_goals()[0]["goal_id"]
        days = tracker.days_since_last_mentioned(goal_id)
        assert days is not None
        assert days < 1

    def test_nonexistent_goal_returns_none(self, tracker):
        assert tracker.days_since_last_mentioned("ghost_id") is None


# ---------------------------------------------------------------------------
# Goals report
# ---------------------------------------------------------------------------

class TestGoalsReport:
    def test_empty_report(self, tracker):
        report = tracker.get_goals_report()
        assert report["total"] == 0
        assert report["active"] == 0

    def test_report_counts(self, tracker):
        tracker.process_turn("I want to write an API wrapper")
        tracker.process_turn("I need to add pagination support")
        report = tracker.get_goals_report()
        assert report["active"] == 2
        assert report["total"] == 2

    def test_report_after_completion(self, tracker):
        tracker.process_turn("I'm trying to add tests")
        goal_id = tracker.get_active_goals()[0]["goal_id"]
        tracker.mark_completed(goal_id)
        report = tracker.get_goals_report()
        assert report["completed"] == 1
        assert report["active"] == 0
