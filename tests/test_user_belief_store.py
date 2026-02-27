"""
Tests for UserBeliefStore - Week 13.

Tests cover:
  - Adding and updating beliefs
  - Confidence boosting on repeated evidence
  - Belief retrieval and filtering
  - User corrections
  - Belief removal
  - Summary generation
  - Report statistics
"""

import os
import tempfile
import pytest

from src.personality.user_belief_store import (
    UserBeliefStore,
    Predicate,
    BASE_CONFIDENCE,
    MAX_CONFIDENCE,
    EVIDENCE_BOOST,
    CORRECTION_CONFIDENCE,
)


@pytest.fixture
def store():
    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    s = UserBeliefStore(db_path=db_path, subject="test_user")
    yield s
    os.unlink(db_path)


# ---------------------------------------------------------------------------
# Adding beliefs
# ---------------------------------------------------------------------------

class TestAddBelief:
    def test_add_new_belief(self, store):
        b = store.add_or_update_belief(Predicate.EXPERT_IN, "python")
        assert b is not None
        assert b["predicate"] == Predicate.EXPERT_IN
        assert b["object_value"] == "python"
        assert b["confidence"] == BASE_CONFIDENCE

    def test_belief_stored_in_db(self, store):
        store.add_or_update_belief(Predicate.PREFERS, "brief_answers")
        beliefs = store.get_beliefs(predicate=Predicate.PREFERS)
        assert len(beliefs) == 1
        assert beliefs[0]["object_value"] == "brief_answers"

    def test_evidence_count_starts_at_one(self, store):
        b = store.add_or_update_belief(Predicate.WORKS_ON, "penny_assistant")
        assert b["evidence_count"] == 1

    def test_add_with_evidence_text(self, store):
        b = store.add_or_update_belief(
            Predicate.EXPERT_IN, "python",
            evidence_text="I've been writing Python for 10 years"
        )
        assert b is not None

    def test_add_with_context(self, store):
        b = store.add_or_update_belief(
            Predicate.PREFERS, "code_examples",
            context="user asked for code when explanation was given"
        )
        assert b["context"] is not None


# ---------------------------------------------------------------------------
# Confidence boosting
# ---------------------------------------------------------------------------

class TestConfidenceBoosting:
    def test_second_evidence_boosts_confidence(self, store):
        store.add_or_update_belief(Predicate.EXPERT_IN, "python")
        b2 = store.add_or_update_belief(Predicate.EXPERT_IN, "python")
        assert b2["confidence"] > BASE_CONFIDENCE

    def test_confidence_increases_with_each_evidence(self, store):
        confidences = []
        for _ in range(5):
            b = store.add_or_update_belief(Predicate.USES, "macos")
            confidences.append(b["confidence"])
        assert confidences == sorted(confidences)  # strictly increasing

    def test_confidence_never_exceeds_max(self, store):
        for _ in range(50):
            b = store.add_or_update_belief(Predicate.EXPERT_IN, "python")
        assert b["confidence"] <= MAX_CONFIDENCE

    def test_evidence_count_increments(self, store):
        store.add_or_update_belief(Predicate.WORKS_WITH, "fastapi")
        store.add_or_update_belief(Predicate.WORKS_WITH, "fastapi")
        store.add_or_update_belief(Predicate.WORKS_WITH, "fastapi")
        beliefs = store.get_beliefs(predicate=Predicate.WORKS_WITH)
        assert beliefs[0]["evidence_count"] == 3

    def test_different_objects_dont_share_confidence(self, store):
        store.add_or_update_belief(Predicate.EXPERT_IN, "python")
        store.add_or_update_belief(Predicate.EXPERT_IN, "python")
        store.add_or_update_belief(Predicate.EXPERT_IN, "rust")
        python_b = store.get_beliefs(predicate=Predicate.EXPERT_IN)
        python_b = next(b for b in python_b if b["object_value"] == "python")
        rust_b   = next(b for b in store.get_beliefs() if b["object_value"] == "rust")
        assert python_b["confidence"] > rust_b["confidence"]


# ---------------------------------------------------------------------------
# Retrieval and filtering
# ---------------------------------------------------------------------------

class TestBeliefRetrieval:
    def test_get_all_beliefs(self, store):
        store.add_or_update_belief(Predicate.EXPERT_IN, "python")
        store.add_or_update_belief(Predicate.PREFERS, "brief_answers")
        store.add_or_update_belief(Predicate.USES, "macos")
        assert len(store.get_beliefs()) == 3

    def test_filter_by_predicate(self, store):
        store.add_or_update_belief(Predicate.EXPERT_IN, "python")
        store.add_or_update_belief(Predicate.EXPERT_IN, "sql")
        store.add_or_update_belief(Predicate.PREFERS, "code_examples")
        experts = store.get_beliefs(predicate=Predicate.EXPERT_IN)
        assert len(experts) == 2
        assert all(b["predicate"] == Predicate.EXPERT_IN for b in experts)

    def test_filter_by_min_confidence(self, store):
        store.add_or_update_belief(Predicate.EXPERT_IN, "python")
        for _ in range(5):
            store.add_or_update_belief(Predicate.EXPERT_IN, "python")
        store.add_or_update_belief(Predicate.LEARNING, "rust")
        high = store.get_beliefs(min_confidence=0.7)
        # Only python belief has high confidence after 6 updates
        assert all(b["confidence"] >= 0.7 for b in high)

    def test_sorted_by_confidence_desc(self, store):
        store.add_or_update_belief(Predicate.EXPERT_IN, "python")
        for _ in range(4):
            store.add_or_update_belief(Predicate.EXPERT_IN, "python")
        store.add_or_update_belief(Predicate.LEARNING, "rust")
        beliefs = store.get_beliefs()
        confs = [b["confidence"] for b in beliefs]
        assert confs == sorted(confs, reverse=True)

    def test_get_belief_by_id(self, store):
        b = store.add_or_update_belief(Predicate.WORKS_ON, "penny")
        fetched = store.get_belief(b["belief_id"])
        assert fetched is not None
        assert fetched["object_value"] == "penny"

    def test_empty_store_returns_empty_list(self, store):
        assert store.get_beliefs() == []


# ---------------------------------------------------------------------------
# Corrections
# ---------------------------------------------------------------------------

class TestCorrections:
    def test_correct_belief(self, store):
        store.add_or_update_belief(Predicate.EXPERT_IN, "javascript")
        result = store.correct_belief(
            Predicate.EXPERT_IN,
            old_object_value="javascript",
            new_object_value="typescript",
        )
        assert result is True
        beliefs = store.get_beliefs(predicate=Predicate.EXPERT_IN)
        assert beliefs[0]["object_value"] == "typescript"

    def test_correction_sets_high_confidence(self, store):
        store.add_or_update_belief(Predicate.PREFERS, "long_explanations")
        store.correct_belief(Predicate.PREFERS, "long_explanations", "brief_answers")
        beliefs = store.get_beliefs(predicate=Predicate.PREFERS)
        assert beliefs[0]["confidence"] == CORRECTION_CONFIDENCE

    def test_correction_marks_source(self, store):
        store.add_or_update_belief(Predicate.USES, "linux")
        store.correct_belief(Predicate.USES, "linux", "macos")
        beliefs = store.get_beliefs(predicate=Predicate.USES)
        assert beliefs[0]["source"] == "user_corrected"

    def test_correct_nonexistent_returns_false(self, store):
        assert store.correct_belief(Predicate.EXPERT_IN, "cobol", "python") is False


# ---------------------------------------------------------------------------
# Removal
# ---------------------------------------------------------------------------

class TestRemoval:
    def test_remove_belief(self, store):
        store.add_or_update_belief(Predicate.DISLIKES, "dark_mode")
        removed = store.remove_belief(Predicate.DISLIKES, "dark_mode")
        assert removed is True
        assert store.get_beliefs(predicate=Predicate.DISLIKES) == []

    def test_remove_nonexistent_returns_false(self, store):
        assert store.remove_belief(Predicate.EXPERT_IN, "cobol") is False


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------

class TestSummary:
    def test_empty_summary_message(self, store):
        summary = store.get_summary()
        assert "don't have any strong beliefs" in summary.lower()

    def test_summary_contains_belief(self, store):
        for _ in range(5):
            store.add_or_update_belief(Predicate.EXPERT_IN, "python")
        summary = store.get_summary()
        assert "python" in summary.lower()
        assert "expert" in summary.lower()

    def test_summary_has_correction_marker(self, store):
        store.add_or_update_belief(Predicate.PREFERS, "dark_mode")
        store.correct_belief(Predicate.PREFERS, "dark_mode", "light_mode")
        summary = store.get_summary()
        assert "✓" in summary


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------

class TestBeliefReport:
    def test_empty_report(self, store):
        report = store.get_belief_report()
        assert report["total"] == 0

    def test_report_totals(self, store):
        store.add_or_update_belief(Predicate.EXPERT_IN, "python")
        store.add_or_update_belief(Predicate.PREFERS, "brief_answers")
        report = store.get_belief_report()
        assert report["total"] == 2

    def test_report_by_predicate(self, store):
        store.add_or_update_belief(Predicate.EXPERT_IN, "python")
        store.add_or_update_belief(Predicate.EXPERT_IN, "sql")
        store.add_or_update_belief(Predicate.PREFERS, "code_examples")
        report = store.get_belief_report()
        pred_map = {r["predicate"]: r["cnt"] for r in report["by_predicate"]}
        assert pred_map[Predicate.EXPERT_IN] == 2
        assert pred_map[Predicate.PREFERS] == 1
