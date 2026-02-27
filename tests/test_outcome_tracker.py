"""
Tests for OutcomeTracker - Week 11.

Tests cover:
  - Outcome recording (observe_outcome)
  - Reaction detection (detect_user_reaction)
  - Success rate calculation (get_strategy_success_rate)
  - Strategy suggestion (suggest_best_strategy)
  - Outcome reporting (get_outcome_report)
  - Edge cases and error handling
"""

import os
import tempfile
import pytest
from datetime import datetime

from src.personality.outcome_tracker import (
    OutcomeTracker,
    classify_response_type,
    POSITIVE_SIGNALS,
    NEGATIVE_SIGNALS,
)


@pytest.fixture
def tracker():
    """Fresh OutcomeTracker backed by a temp DB for each test."""
    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    t = OutcomeTracker(db_path=db_path)
    yield t
    os.unlink(db_path)


# ---------------------------------------------------------------------------
# Response classification
# ---------------------------------------------------------------------------

class TestResponseClassification:
    def test_code_example_detected(self):
        assert classify_response_type("Here is the code:\n```python\nprint('hi')\n```") == "code_example"

    def test_brief_answer_detected(self):
        assert classify_response_type("Yes.") == "brief_answer"

    def test_detailed_explanation_detected(self):
        long_text = "This is a very detailed explanation. " * 20
        assert classify_response_type(long_text) == "detailed_explanation"

    def test_conversational_default(self):
        # 100–500 chars, no code block → conversational
        mid_length = "Sure, let me check that for you! " * 4  # ~132 chars
        assert classify_response_type(mid_length) == "conversational"


# ---------------------------------------------------------------------------
# Outcome recording
# ---------------------------------------------------------------------------

class TestObserveOutcome:
    def test_record_positive_outcome(self, tracker):
        tracker.observe_outcome(
            response_id="r001",
            response_type="brief_answer",
            reaction="positive",
            strategy="concise",
        )
        report = tracker.get_outcome_report()
        assert report["positive_count"] == 1
        assert report["total_observations"] == 1

    def test_record_negative_outcome(self, tracker):
        tracker.observe_outcome(
            response_id="r002",
            response_type="detailed_explanation",
            reaction="negative",
            strategy="verbose",
        )
        report = tracker.get_outcome_report()
        assert report["negative_count"] == 1

    def test_record_neutral_outcome(self, tracker):
        tracker.observe_outcome(
            response_id="r003",
            response_type="conversational",
            reaction="neutral",
        )
        report = tracker.get_outcome_report()
        assert report["neutral_count"] == 1

    def test_invalid_reaction_raises(self, tracker):
        with pytest.raises(ValueError):
            tracker.observe_outcome(
                response_id="r999",
                response_type="brief_answer",
                reaction="confused",
            )

    def test_upsert_same_response_id(self, tracker):
        tracker.observe_outcome("r_dup", "brief_answer", "positive")
        tracker.observe_outcome("r_dup", "brief_answer", "positive")  # same ID
        report = tracker.get_outcome_report()
        assert report["total_observations"] == 1  # INSERT OR REPLACE

    def test_records_all_fields(self, tracker):
        tracker.observe_outcome(
            response_id="r_full",
            response_type="code_example",
            reaction="positive",
            context_type="technical",
            strategy="code_first",
            confidence=0.9,
            user_message="fix my loop",
            assistant_response="Here's the fix:\n```python\nfor i in range(10): pass\n```",
            session_id="sess_abc",
        )
        report = tracker.get_outcome_report()
        assert report["total_observations"] == 1
        assert report["positive_count"] == 1


# ---------------------------------------------------------------------------
# Reaction detection
# ---------------------------------------------------------------------------

class TestDetectUserReaction:
    def test_positive_thanks(self, tracker):
        reaction, conf = tracker.detect_user_reaction("thanks!")
        assert reaction == "positive"
        assert conf > 0.5

    def test_positive_perfect(self, tracker):
        reaction, conf = tracker.detect_user_reaction("perfect, that worked")
        assert reaction == "positive"

    def test_negative_didnt_work(self, tracker):
        reaction, conf = tracker.detect_user_reaction("that didn't work for me")
        assert reaction == "negative"
        assert conf > 0.5

    def test_negative_wrong(self, tracker):
        reaction, conf = tracker.detect_user_reaction("wrong, that's not what I meant")
        assert reaction == "negative"

    def test_neutral_unrelated(self, tracker):
        reaction, conf = tracker.detect_user_reaction("what's the weather today?")
        assert reaction == "neutral"
        assert conf == 1.0

    def test_logs_reaction(self, tracker):
        tracker.detect_user_reaction("works great!")
        report = tracker.get_outcome_report()
        # At minimum doesn't crash; reaction patterns stored in separate table
        assert report is not None

    def test_emoji_positive(self, tracker):
        reaction, _ = tracker.detect_user_reaction("👍")
        assert reaction == "positive"

    def test_emoji_negative(self, tracker):
        reaction, _ = tracker.detect_user_reaction("👎")
        assert reaction == "negative"


# ---------------------------------------------------------------------------
# Success rate calculation
# ---------------------------------------------------------------------------

class TestStrategySuccessRate:
    def test_default_prior_when_no_data(self, tracker):
        rate = tracker.get_strategy_success_rate("unknown_strategy")
        assert rate == 0.5

    def test_all_positive(self, tracker):
        for i in range(5):
            tracker.observe_outcome(f"r{i}", "brief_answer", "positive", strategy="s1")
        rate = tracker.get_strategy_success_rate("s1")
        assert rate == 1.0

    def test_all_negative(self, tracker):
        for i in range(3):
            tracker.observe_outcome(f"r{i}", "detailed_explanation", "negative", strategy="s2")
        rate = tracker.get_strategy_success_rate("s2")
        assert rate == 0.0

    def test_mixed_rate(self, tracker):
        tracker.observe_outcome("a1", "conversational", "positive", strategy="mix")
        tracker.observe_outcome("a2", "conversational", "negative", strategy="mix")
        tracker.observe_outcome("a3", "conversational", "neutral",  strategy="mix")
        # neutral excluded: 1 pos / 1+1 = 0.5
        rate = tracker.get_strategy_success_rate("mix")
        assert rate == 0.5

    def test_context_specific_rate(self, tracker):
        tracker.observe_outcome("t1", "brief_answer", "positive",
                                strategy="code_first", context_type="technical")
        tracker.observe_outcome("t2", "brief_answer", "negative",
                                strategy="code_first", context_type="casual_chat")
        assert tracker.get_strategy_success_rate("code_first", "technical")   == 1.0
        assert tracker.get_strategy_success_rate("code_first", "casual_chat") == 0.0


# ---------------------------------------------------------------------------
# Strategy suggestion
# ---------------------------------------------------------------------------

class TestSuggestBestStrategy:
    def test_returns_none_when_no_data(self, tracker):
        assert tracker.suggest_best_strategy("technical") is None

    def test_suggests_best_strategy(self, tracker):
        # s_good: 4 positive, s_bad: 0 positive
        for i in range(4):
            tracker.observe_outcome(f"g{i}", "brief_answer", "positive",
                                    strategy="s_good", context_type="technical")
        for i in range(4):
            tracker.observe_outcome(f"b{i}", "detailed_explanation", "negative",
                                    strategy="s_bad", context_type="technical")

        best = tracker.suggest_best_strategy("technical")
        assert best == "s_good"

    def test_candidates_filter(self, tracker):
        for i in range(3):
            tracker.observe_outcome(f"c{i}", "code_example", "positive",
                                    strategy="excellent", context_type="gen")
        for i in range(3):
            tracker.observe_outcome(f"d{i}", "brief_answer", "positive",
                                    strategy="decent", context_type="gen")

        # Only consider 'decent'
        best = tracker.suggest_best_strategy("gen", candidates=["decent"])
        assert best == "decent"

    def test_insufficient_data_returns_none(self, tracker):
        tracker.observe_outcome("only1", "brief_answer", "positive", strategy="rare")
        # Need at least 2 data points
        assert tracker.suggest_best_strategy("general", candidates=["rare"]) is None


# ---------------------------------------------------------------------------
# Outcome report
# ---------------------------------------------------------------------------

class TestOutcomeReport:
    def test_empty_report_defaults(self, tracker):
        report = tracker.get_outcome_report()
        assert report["total_observations"] == 0
        assert report["overall_success_rate"] == 0.5
        assert report["strategies"] == []
        assert report["recent_trend"] == []

    def test_report_totals(self, tracker):
        tracker.observe_outcome("x1", "brief_answer", "positive")
        tracker.observe_outcome("x2", "brief_answer", "negative")
        tracker.observe_outcome("x3", "brief_answer", "neutral")
        report = tracker.get_outcome_report()
        assert report["total_observations"] == 3
        assert report["positive_count"] == 1
        assert report["negative_count"] == 1
        assert report["neutral_count"] == 1
        assert report["overall_success_rate"] == 0.5

    def test_report_recent_trend(self, tracker):
        for i in range(5):
            tracker.observe_outcome(f"t{i}", "conversational", "positive")
        report = tracker.get_outcome_report()
        assert len(report["recent_trend"]) == 5
        assert all(r == "positive" for r in report["recent_trend"])

    def test_report_strategy_list(self, tracker):
        tracker.observe_outcome("s1", "brief_answer", "positive", strategy="alpha")
        tracker.observe_outcome("s2", "detailed_explanation", "negative", strategy="beta")
        report = tracker.get_outcome_report()
        strategy_names = {s["strategy"] for s in report["strategies"]}
        assert "alpha" in strategy_names
        assert "beta" in strategy_names


# ---------------------------------------------------------------------------
# ID generation
# ---------------------------------------------------------------------------

class TestResponseIdGeneration:
    def test_generate_unique_ids(self, tracker):
        ids = {OutcomeTracker.generate_response_id() for _ in range(100)}
        assert len(ids) == 100

    def test_id_format(self, tracker):
        rid = OutcomeTracker.generate_response_id()
        assert rid.startswith("resp_")
        assert len(rid) == 17  # "resp_" + 12 hex chars
