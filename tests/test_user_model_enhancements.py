"""
Week 13 Enhancement tests (2026 memory-architecture alignment).

Covers:
  Fix 2 — belief staging / quarantine
  Fix 3 — temporal decay + archiving
  Fix 5 — contradiction detection
  Fix 4 — outcome-driven reinforce/weaken (store-level)
"""

import os
import json
import tempfile
from datetime import datetime, timedelta

import pytest

from src.personality.user_belief_store import UserBeliefStore, Predicate
from src.personality.belief_extractor import BeliefExtractor


@pytest.fixture
def store():
    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    s = UserBeliefStore(db_path=db_path, subject="CJ")
    yield s
    os.unlink(db_path)


def _backdate_staging_first_seen(store, predicate, object_value, days):
    """Push a staging row's first_seen into the past to simulate elapsed time."""
    past = (datetime.now() - timedelta(days=days)).isoformat()
    with store._get_conn() as conn:
        conn.execute(
            "UPDATE belief_staging SET first_seen = ? "
            "WHERE subject = ? AND predicate = ? AND object_value = ?",
            (past, store.subject, predicate, object_value),
        )


def _backdate_last_updated(store, predicate, object_value, days):
    past = (datetime.now() - timedelta(days=days)).isoformat()
    with store._get_conn() as conn:
        conn.execute(
            "UPDATE user_beliefs SET last_updated = ? "
            "WHERE subject = ? AND predicate = ? AND object_value = ?",
            (past, store.subject, predicate, object_value),
        )


# ---------------------------------------------------------------------------
# Fix 2: Staging / quarantine
# ---------------------------------------------------------------------------

class TestBeliefStaging:
    def test_single_observation_stays_in_staging(self, store):
        res = store.observe_belief(Predicate.PREFERS, "dark_mode", "I prefer dark mode")
        assert res["status"] == "staged"
        # Not yet a permanent belief
        assert store.get_beliefs(predicate=Predicate.PREFERS) == []
        assert len(store.get_staging()) == 1

    def test_promotion_requires_min_observations_and_days(self, store):
        # Three observations same day → still staged (days span = 0)
        for _ in range(3):
            res = store.observe_belief(Predicate.WORKS_WITH, "python")
        assert res["status"] == "staged"
        assert store.get_beliefs(predicate=Predicate.WORKS_WITH) == []

        # Simulate the staging entry being 4 days old, observe once more → promote
        _backdate_staging_first_seen(store, Predicate.WORKS_WITH, "python", days=4)
        res = store.observe_belief(Predicate.WORKS_WITH, "python")
        assert res["status"] == "promoted"
        beliefs = store.get_beliefs(predicate=Predicate.WORKS_WITH)
        assert len(beliefs) == 1
        assert beliefs[0]["object_value"] == "python"
        assert beliefs[0]["confidence"] == 0.6  # promotions start at 0.6
        assert beliefs[0]["source"] == "promoted_from_staging"
        # Staging entry cleared after promotion
        assert store.get_staging() == []

    def test_reinforce_existing_permanent_belief(self, store):
        store.add_or_update_belief(Predicate.EXPERT_IN, "python")  # permanent at 0.5
        res = store.observe_belief(Predicate.EXPERT_IN, "python")
        assert res["status"] == "reinforced"
        beliefs = store.get_beliefs(predicate=Predicate.EXPERT_IN)
        assert beliefs[0]["confidence"] > 0.5  # boosted

    def test_expired_staging_cleaned_up(self, store):
        store.observe_belief(Predicate.LIKES, "tabs")
        _backdate_staging_first_seen(store, Predicate.LIKES, "tabs", days=40)
        removed = store.cleanup_expired_staging()
        assert removed == 1
        assert store.get_staging() == []

    def test_user_correction_bypasses_staging(self, store):
        # Seed a permanent belief, then correct it → instant permanent write
        store.add_or_update_belief(Predicate.LEARNING, "javascript")
        ok = store.correct_belief(Predicate.LEARNING, "javascript", "typescript")
        assert ok
        beliefs = store.get_beliefs(predicate=Predicate.LEARNING)
        assert beliefs[0]["object_value"] == "typescript"
        assert beliefs[0]["source"] == "user_corrected"

    def test_extractor_staging_mode_does_not_write_permanent(self, store):
        ext = BeliefExtractor(store, use_staging=True)
        ext.extract_from_turn("I'm an expert in Python")
        # Beliefs are staged, not permanent
        assert store.get_belief_report()["total"] == 0
        assert len(store.get_staging()) >= 1

    def test_extractor_default_mode_writes_permanent(self, store):
        ext = BeliefExtractor(store)  # use_staging defaults False
        ext.extract_from_turn("I'm an expert in Python")
        assert store.get_belief_report()["total"] >= 1


# ---------------------------------------------------------------------------
# Fix 3: Temporal decay + archiving
# ---------------------------------------------------------------------------

class TestTemporalDecay:
    def test_recently_observed_does_not_decay(self, store):
        store.add_or_update_belief(Predicate.USES, "macos")
        before = store.get_beliefs(predicate=Predicate.USES)[0]["confidence"]
        store.apply_temporal_decay()
        after = store.get_beliefs(predicate=Predicate.USES)[0]["confidence"]
        assert after == before

    def test_decay_reduces_confidence_over_time(self, store):
        store.add_or_update_belief(Predicate.USES, "ubuntu")
        for _ in range(4):  # raise confidence well above archive threshold
            store.add_or_update_belief(Predicate.USES, "ubuntu")
        _backdate_last_updated(store, Predicate.USES, "ubuntu", days=10)
        before = 0.5 + 4 * 0.08  # not exact, just > archive threshold
        store.apply_temporal_decay(decay_rate=0.005)
        after = store.get_beliefs(predicate=Predicate.USES)[0]["confidence"]
        # 10 days * 0.005 = 0.05 lost
        assert after < before
        assert after > store.MIN_CONFIDENCE_BEFORE_ARCHIVE

    def test_low_confidence_belief_gets_archived(self, store):
        store.add_or_update_belief(Predicate.HAS, "mac")  # 0.5
        _backdate_last_updated(store, Predicate.HAS, "mac", days=60)
        result = store.apply_temporal_decay(decay_rate=0.005)  # 60*0.005=0.30 -> 0.20
        assert result["archived"] == 1
        assert store.get_beliefs(predicate=Predicate.HAS) == []
        archived = store.get_archived_beliefs()
        assert len(archived) == 1
        assert archived[0]["object_value"] == "mac"

    def test_archived_belief_can_be_restored(self, store):
        store.add_or_update_belief(Predicate.HAS, "raspberry_pi")
        _backdate_last_updated(store, Predicate.HAS, "raspberry_pi", days=60)
        store.apply_temporal_decay(decay_rate=0.005)
        assert store.get_archived_beliefs()  # archived
        ok = store.restore_belief(Predicate.HAS, "raspberry_pi")
        assert ok
        restored = store.get_beliefs(predicate=Predicate.HAS)
        assert len(restored) == 1
        assert store.get_archived_beliefs() == []


# ---------------------------------------------------------------------------
# Fix 5: Contradiction detection
# ---------------------------------------------------------------------------

class TestContradictionDetection:
    def test_detect_predicate_contradiction(self, store):
        store.add_or_update_belief(Predicate.PREFERS, "brief_answers")
        store.add_or_update_belief(Predicate.DISLIKES, "brief_answers")
        conflicts = store.detect_contradictions()
        assert len(conflicts) >= 1
        assert conflicts[0]["type"] == "predicate_conflict"

    def test_detect_object_contradiction_same_predicate(self, store):
        store.add_or_update_belief(Predicate.PREFERS, "brief_responses")
        store.add_or_update_belief(Predicate.PREFERS, "detailed_responses")
        conflicts = store.detect_contradictions()
        assert len(conflicts) >= 1

    def test_observe_blocks_contradictory_write(self, store):
        store.add_or_update_belief(Predicate.PREFERS, "dark")  # permanent
        res = store.observe_belief(Predicate.DISLIKES, "dark")
        assert res["status"] == "contradiction"
        # Not staged, not written
        assert store.get_staging() == []
        assert store.get_beliefs(predicate=Predicate.DISLIKES) == []

    def test_check_before_write_returns_none_when_safe(self, store):
        store.add_or_update_belief(Predicate.PREFERS, "python")
        assert store.check_before_write(Predicate.EXPERT_IN, "rust") is None


# ---------------------------------------------------------------------------
# Fix 4: outcome-driven reinforce / weaken (store level)
# ---------------------------------------------------------------------------

class TestReinforceWeaken:
    def test_reinforce_raises_confidence(self, store):
        store.add_or_update_belief(Predicate.PREFERS, "examples")
        b = store.reinforce_belief(Predicate.PREFERS, "examples", boost=0.02)
        assert b is not None
        assert b["confidence"] == pytest.approx(0.52, abs=1e-6)

    def test_weaken_lowers_confidence(self, store):
        store.add_or_update_belief(Predicate.PREFERS, "examples")
        b = store.weaken_belief(Predicate.PREFERS, "examples", penalty=0.05)
        assert b is not None
        assert b["confidence"] == pytest.approx(0.45, abs=1e-6)

    def test_adjust_missing_belief_returns_none(self, store):
        assert store.reinforce_belief(Predicate.PREFERS, "nonexistent") is None


# ---------------------------------------------------------------------------
# Fix 4: cross-system integration helpers (belief_integration)
# ---------------------------------------------------------------------------

from src.personality import belief_integration as bi


class _FakePattern:
    def __init__(self, pattern_type, term=None):
        self.pattern_type = pattern_type
        self.term = term


class TestCrossSystemIntegration:
    def test_positive_outcome_reinforces_beliefs(self, store):
        store.add_or_update_belief(Predicate.PREFERS, "examples")
        beliefs = store.get_beliefs(predicate=Predicate.PREFERS)
        updated = bi.apply_outcome_to_beliefs(store, "positive", beliefs)
        assert updated and updated[0]["confidence"] > 0.5

    def test_negative_outcome_weakens_beliefs(self, store):
        store.add_or_update_belief(Predicate.PREFERS, "examples")
        beliefs = store.get_beliefs(predicate=Predicate.PREFERS)
        updated = bi.apply_outcome_to_beliefs(store, "negative", beliefs)
        assert updated and updated[0]["confidence"] < 0.5

    def test_neutral_outcome_is_noop(self, store):
        store.add_or_update_belief(Predicate.PREFERS, "examples")
        beliefs = store.get_beliefs(predicate=Predicate.PREFERS)
        assert bi.apply_outcome_to_beliefs(store, "neutral", beliefs) == []

    def test_hebbian_vocabulary_pattern_creates_observation(self, store):
        res = bi.belief_from_hebbian_pattern(store, _FakePattern("vocabulary", "lol"))
        assert res is not None
        assert res["status"] in ("staged", "promoted", "reinforced")
        assert len(store.get_staging()) == 1

    def test_hebbian_nonvocabulary_pattern_ignored(self, store):
        assert bi.belief_from_hebbian_pattern(store, _FakePattern("temporal", "x")) is None

    def test_gated_observe_blocks_when_budget_denies(self, store):
        res = bi.gated_observe(store, Predicate.LIKES, "tabs", can_write=lambda: False)
        assert res["status"] == "skipped_budget"
        assert store.get_staging() == []

    def test_gated_observe_writes_when_allowed(self, store):
        res = bi.gated_observe(store, Predicate.LIKES, "tabs", can_write=lambda: True)
        assert res["status"] == "staged"
        assert len(store.get_staging()) == 1

    def test_beliefs_for_judgment_returns_relevant(self, store):
        from src.personality.belief_extractor import BeliefExtractor
        ext = BeliefExtractor(store)
        for _ in range(4):
            ext.extract_from_turn("I know Python well")
        result = bi.beliefs_for_judgment(ext, ["python"])
        assert any("python" in b["object_value"] for b in result)

    def test_helpers_null_safe_when_disabled(self, store):
        assert bi.beliefs_for_judgment(None, ["x"]) == []
        assert bi.apply_outcome_to_beliefs(None, "positive", []) == []
        assert bi.belief_from_hebbian_pattern(None, None) is None
        assert bi.gated_observe(None, "p", "o") is None
