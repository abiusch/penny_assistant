"""
Integration tests for Week 13 User Model.

Tests the full pipeline: BeliefExtractor → UserBeliefStore →
context injection → user correction flow.
"""

import os
import tempfile
import pytest

from src.personality.user_belief_store import UserBeliefStore, Predicate, CORRECTION_CONFIDENCE
from src.personality.belief_extractor import BeliefExtractor


@pytest.fixture
def stack():
    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    store     = UserBeliefStore(db_path=db_path, subject="CJ")
    extractor = BeliefExtractor(store)
    yield store, extractor
    os.unlink(db_path)


# ---------------------------------------------------------------------------
# Multi-turn belief building
# ---------------------------------------------------------------------------

class TestMultiTurnBeliefBuilding:
    def test_beliefs_accumulate_across_turns(self, stack):
        store, extractor = stack
        extractor.extract_from_turn("I'm an expert in Python")
        extractor.extract_from_turn("I prefer brief answers")
        extractor.extract_from_turn("I'm working on penny assistant")
        report = store.get_belief_report()
        assert report["total"] >= 3

    def test_repeated_turns_boost_confidence(self, stack):
        store, extractor = stack
        for _ in range(4):
            extractor.extract_from_turn("I know Python well")
        beliefs = store.get_beliefs(predicate=Predicate.EXPERT_IN)
        python = next((b for b in beliefs if "python" in b["object_value"]), None)
        assert python is not None
        assert python["confidence"] > 0.5 + 3 * 0.08 - 0.01  # 4 updates

    def test_different_predicates_stored_separately(self, stack):
        store, extractor = stack
        extractor.extract_from_turn("I'm an expert in Python")
        extractor.extract_from_turn("I prefer code examples")
        experts = store.get_beliefs(predicate=Predicate.EXPERT_IN)
        prefs   = store.get_beliefs(predicate=Predicate.PREFERS)
        assert len(experts) >= 1
        assert len(prefs) >= 1


# ---------------------------------------------------------------------------
# Correction flow
# ---------------------------------------------------------------------------

class TestCorrectionFlow:
    def test_detect_correction_signal(self, stack):
        _, extractor = stack
        assert extractor.detect_correction("Actually, I prefer Python not Ruby")
        assert extractor.detect_correction("That's not right, I use TypeScript")
        assert not extractor.detect_correction("Thanks, that worked!")

    def test_full_correction_cycle(self, stack):
        store, extractor = stack
        # User states a belief
        extractor.extract_from_turn("I'm learning JavaScript")
        # Penny feeds back wrong info, user corrects
        result = extractor.extract_explicit_correction(
            Predicate.LEARNING, "javascript", "typescript",
            reason="user clarified"
        )
        assert result is True
        beliefs = store.get_beliefs(predicate=Predicate.LEARNING)
        assert beliefs[0]["object_value"] == "typescript"
        assert beliefs[0]["confidence"] == CORRECTION_CONFIDENCE
        assert beliefs[0]["source"] == "user_corrected"

    def test_correction_marked_in_summary(self, stack):
        store, extractor = stack
        extractor.extract_from_turn("I prefer dark mode")
        store.correct_belief(Predicate.PREFERS, "dark_mode", "light_mode")
        for _ in range(4):
            store.add_or_update_belief(Predicate.PREFERS, "light_mode")
        summary = store.get_summary()
        assert "✓" in summary  # correction marker visible


# ---------------------------------------------------------------------------
# Context snippet injection
# ---------------------------------------------------------------------------

class TestContextSnippetInjection:
    def test_snippet_generated_with_beliefs(self, stack):
        store, extractor = stack
        for _ in range(4):
            extractor.extract_from_turn("I'm an expert in Python")
        snippet = extractor.build_context_snippet(["python"])
        assert snippet != ""
        assert "[User:" in snippet
        assert "python" in snippet

    def test_snippet_empty_without_beliefs(self, stack):
        _, extractor = stack
        snippet = extractor.build_context_snippet()
        assert snippet == ""

    def test_relevant_beliefs_ranked_by_keywords(self, stack):
        store, extractor = stack
        for _ in range(4):
            extractor.extract_from_turn("I know Python well")
        for _ in range(4):
            extractor.extract_from_turn("I prefer brief answers")

        # Python keyword → python belief should rank first
        beliefs = extractor.get_relevant_beliefs(["python"], min_confidence=0.4)
        assert len(beliefs) >= 1
        first = beliefs[0]
        assert "python" in first["object_value"] or "python" in first["predicate"]


# ---------------------------------------------------------------------------
# Belief summary — user-facing transparency
# ---------------------------------------------------------------------------

class TestBeliefSummary:
    def test_summary_shows_high_confidence_beliefs(self, stack):
        store, extractor = stack
        for _ in range(5):
            extractor.extract_from_turn("I'm an expert in Python")
        summary = store.get_summary()
        assert "python" in summary.lower()
        assert "Want to correct anything?" in summary

    def test_summary_empty_for_new_store(self, stack):
        store, _ = stack
        summary = store.get_summary()
        assert "still learning" in summary.lower()

    def test_summary_caps_at_max_beliefs(self, stack):
        store, _ = stack
        for i in range(15):
            for _ in range(4):
                store.add_or_update_belief(Predicate.WORKS_WITH, f"tool_{i}")
        summary = store.get_summary(max_beliefs=5)
        # Count bullet points
        bullet_count = summary.count("  •")
        assert bullet_count <= 5


# ---------------------------------------------------------------------------
# Belief report
# ---------------------------------------------------------------------------

class TestBeliefReport:
    def test_report_counts_high_confidence(self, stack):
        store, extractor = stack
        for _ in range(6):
            extractor.extract_from_turn("I know Python well")
        report = store.get_belief_report()
        assert report["high_confidence"] >= 1

    def test_report_by_predicate_groups(self, stack):
        store, extractor = stack
        extractor.extract_from_turn("I'm an expert in Python")
        extractor.extract_from_turn("I'm an expert in SQL")
        extractor.extract_from_turn("I prefer brief answers")
        report = store.get_belief_report()
        pred_map = {r["predicate"]: r["cnt"] for r in report["by_predicate"]}
        assert pred_map.get(Predicate.EXPERT_IN, 0) >= 1
