"""
Integration tests for Week 11 Outcome Tracking.

Tests cover:
  - OutcomeTracker + ProactivityBudget working together
  - End-to-end reaction → outcome → strategy suggestion flow
  - Feature-flag behaviour (disabled by default)
  - Safety: proactivity limits enforced even when outcome tracking on
  - Multi-turn tracking simulation
"""

import os
import tempfile
import pytest
from datetime import datetime, timedelta

from src.personality.outcome_tracker import OutcomeTracker, classify_response_type
from src.personality.proactivity_budget import (
    ProactivityBudget,
    MAX_NUDGES_PER_DAY,
    MAX_GOAL_RESURRECTIONS_WEEK,
    DORMANT_THRESHOLD_DAYS,
    REQUIRE_PERMISSION_AFTER_DAYS,
    MIN_CONFIDENCE_FOR_PROACTIVE,
)


@pytest.fixture
def shared_db():
    """Single temp DB shared between tracker and budget (mirrors production)."""
    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    tracker = OutcomeTracker(db_path=db_path)
    budget  = ProactivityBudget(db_path=db_path)
    yield tracker, budget
    os.unlink(db_path)


# ---------------------------------------------------------------------------
# End-to-end: react → observe → suggest
# ---------------------------------------------------------------------------

class TestEndToEndFlow:
    def test_positive_reaction_improves_success_rate(self, shared_db):
        tracker, _ = shared_db
        strategy = "brief_code_first"
        for i in range(3):
            rid = OutcomeTracker.generate_response_id()
            reaction, conf = tracker.detect_user_reaction("thanks, that worked!")
            tracker.observe_outcome(rid, "code_example", reaction,
                                    context_type="technical", strategy=strategy,
                                    confidence=conf)

        rate = tracker.get_strategy_success_rate(strategy, "technical")
        assert rate == 1.0

    def test_negative_reaction_lowers_success_rate(self, shared_db):
        tracker, _ = shared_db
        strategy = "verbose_explain"
        for i in range(3):
            rid = OutcomeTracker.generate_response_id()
            reaction, conf = tracker.detect_user_reaction("that didn't work at all")
            tracker.observe_outcome(rid, "detailed_explanation", reaction,
                                    context_type="technical", strategy=strategy,
                                    confidence=conf)

        rate = tracker.get_strategy_success_rate(strategy, "technical")
        assert rate == 0.0

    def test_suggest_best_strategy_from_history(self, shared_db):
        tracker, _ = shared_db
        # Build history: code_first wins in technical context
        for i in range(4):
            rid = OutcomeTracker.generate_response_id()
            tracker.observe_outcome(rid, "code_example", "positive",
                                    context_type="technical", strategy="code_first")
        for i in range(4):
            rid = OutcomeTracker.generate_response_id()
            tracker.observe_outcome(rid, "detailed_explanation", "negative",
                                    context_type="technical", strategy="explanation_heavy")

        best = tracker.suggest_best_strategy("technical")
        assert best == "code_first"

    def test_multi_turn_tracking(self, shared_db):
        """Simulate 5 turns: response then reaction each turn."""
        tracker, _ = shared_db
        turns = [
            ("here's the fix:\n```python\nresult = x + 1\n```", "awesome, works!"),
            ("The reason is that Python uses dynamic typing.", "thanks"),
            ("Try using asyncio instead.", "didn't work unfortunately"),
            ("You can also use subprocess.run()", "perfect, that solved it"),
            ("Here is a longer explanation of the concept. " * 10, "makes sense"),
        ]

        last_response_id   = None
        last_response_type = None
        reactions_recorded = 0

        for assistant_resp, user_followup in turns:
            # Record reaction to previous response
            if last_response_id:
                reaction, conf = tracker.detect_user_reaction(user_followup)
                if reaction != "neutral":
                    tracker.observe_outcome(
                        last_response_id, last_response_type, reaction,
                        confidence=conf
                    )
                    reactions_recorded += 1

            # Tag this response
            last_response_id   = OutcomeTracker.generate_response_id()
            last_response_type = classify_response_type(assistant_resp)

        report = tracker.get_outcome_report()
        assert report["total_observations"] == reactions_recorded
        assert reactions_recorded >= 3  # At least 3 clear reactions in the data


# ---------------------------------------------------------------------------
# classify_response_type correctness
# ---------------------------------------------------------------------------

class TestResponseTypeClassification:
    def test_code_block_classified(self):
        resp = "Here's how:\n```python\nprint('hello')\n```"
        assert classify_response_type(resp) == "code_example"

    def test_short_classified_as_brief(self):
        assert classify_response_type("Yes.") == "brief_answer"

    def test_long_classified_as_detailed(self):
        long = "This is an explanation. " * 25  # >500 chars
        assert classify_response_type(long) == "detailed_explanation"

    def test_medium_classified_as_conversational(self):
        medium = "Sure, let me check that. " * 5  # ~125 chars, no code
        assert classify_response_type(medium) == "conversational"


# ---------------------------------------------------------------------------
# Proactivity + Outcome integration
# ---------------------------------------------------------------------------

class TestProactivitySafety:
    def test_nudge_blocked_after_daily_limit(self, shared_db):
        _, budget = shared_db
        budget.record_nudge("g1")
        budget.record_nudge("g2")
        allowed, reason = budget.can_nudge_about_goal("g3", confidence=0.9)
        assert allowed is False
        assert "Daily nudge limit" in reason

    def test_confidence_gating_integrated(self, shared_db):
        tracker, budget = shared_db
        # Even with good outcome history, proactivity is gated by confidence
        for i in range(5):
            tracker.observe_outcome(f"r{i}", "brief_answer", "positive", strategy="proactive")

        # Check that the budget still gates on confidence independently
        allowed, _ = budget.can_nudge_about_goal("goal", confidence=0.5)
        assert allowed is False

    def test_resurrection_and_budget_summary(self, shared_db):
        _, budget = shared_db
        budget.record_resurrection("old_goal", "finish docs")
        summary = budget.get_budget_summary()
        assert summary["resurrections_this_week"] == 1
        assert summary["resurrections_remaining_week"] == 0

    def test_permission_message_contains_goal(self, shared_db):
        _, budget = shared_db
        msg = budget.request_permission_for_goal("g1", "refactor the auth module", days_dormant=10)
        assert "refactor the auth module" in msg


# ---------------------------------------------------------------------------
# Outcome report integration
# ---------------------------------------------------------------------------

class TestOutcomeReportIntegration:
    def test_report_after_mixed_reactions(self, shared_db):
        tracker, _ = shared_db
        for label, reaction in [("great!", "positive"), ("wrong", "negative"),
                                 ("ok", "neutral"), ("thanks", "positive")]:
            rid = OutcomeTracker.generate_response_id()
            tracker.observe_outcome(rid, "brief_answer", reaction, strategy="mixed")

        report = tracker.get_outcome_report()
        assert report["total_observations"] == 4
        assert report["positive_count"] == 2
        assert report["negative_count"] == 1
        assert report["neutral_count"] == 1
        # success rate = 2 / (2+1) ≈ 0.667
        assert abs(report["overall_success_rate"] - 2/3) < 0.01

    def test_strategy_appears_in_report(self, shared_db):
        tracker, _ = shared_db
        tracker.observe_outcome("x1", "code_example", "positive", strategy="my_strategy")
        tracker.observe_outcome("x2", "brief_answer",  "negative", strategy="my_strategy")
        report = tracker.get_outcome_report()
        strat_names = [s["strategy"] for s in report["strategies"]]
        assert "my_strategy" in strat_names
