"""
Tests for BeliefExtractor - Week 13.

Tests cover:
  - Pattern extraction from natural language
  - Expertise detection
  - Preference detection
  - Work context detection
  - Correction signal detection
  - Context snippet generation
  - Relevant belief retrieval
"""

import os
import tempfile
import pytest

from src.personality.user_belief_store import UserBeliefStore, Predicate
from src.personality.belief_extractor import BeliefExtractor, _clean_object


@pytest.fixture
def extractor():
    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    store = UserBeliefStore(db_path=db_path, subject="test_user")
    ext = BeliefExtractor(store)
    yield ext
    os.unlink(db_path)


# ---------------------------------------------------------------------------
# Helper cleaning
# ---------------------------------------------------------------------------

class TestCleanObject:
    def test_strips_punctuation(self):
        assert _clean_object("Python.") == "python"
        assert _clean_object("FastAPI!") == "fastapi"

    def test_lowercases(self):
        assert _clean_object("Python") == "python"

    def test_replaces_spaces_with_underscores(self):
        assert _clean_object("brief answers") == "brief_answers"

    def test_truncates_long_values(self):
        long = "a" * 100
        assert len(_clean_object(long)) <= 60


# ---------------------------------------------------------------------------
# Expertise extraction
# ---------------------------------------------------------------------------

class TestExpertiseExtraction:
    def test_expert_in_python(self, extractor):
        beliefs = extractor.extract_from_turn("I'm an expert in Python")
        preds = [b["predicate"] for b in beliefs]
        assert Predicate.EXPERT_IN in preds

    def test_works_with_fastapi(self, extractor):
        beliefs = extractor.extract_from_turn("I use FastAPI for all my projects")
        preds = [b["predicate"] for b in beliefs]
        assert Predicate.WORKS_WITH in preds

    def test_learning_rust(self, extractor):
        beliefs = extractor.extract_from_turn("I'm learning Rust these days")
        preds = [b["predicate"] for b in beliefs]
        assert Predicate.LEARNING in preds

    def test_unfamiliar_with_kubernetes(self, extractor):
        beliefs = extractor.extract_from_turn("I've never used Kubernetes before")
        preds = [b["predicate"] for b in beliefs]
        assert Predicate.UNFAMILIAR_WITH in preds

    def test_know_python_well(self, extractor):
        beliefs = extractor.extract_from_turn("I know Python well")
        preds = [b["predicate"] for b in beliefs]
        assert Predicate.EXPERT_IN in preds


# ---------------------------------------------------------------------------
# Preference extraction
# ---------------------------------------------------------------------------

class TestPreferenceExtraction:
    def test_prefers_brief_answers(self, extractor):
        beliefs = extractor.extract_from_turn("I prefer brief answers")
        preds = [b["predicate"] for b in beliefs]
        assert Predicate.PREFERS in preds

    def test_likes_code_examples(self, extractor):
        beliefs = extractor.extract_from_turn("I like code examples")
        preds = [b["predicate"] for b in beliefs]
        assert Predicate.PREFERS in preds

    def test_dislikes_verbose(self, extractor):
        beliefs = extractor.extract_from_turn("I don't like verbose explanations")
        preds = [b["predicate"] for b in beliefs]
        assert Predicate.DISLIKES in preds


# ---------------------------------------------------------------------------
# Work context extraction
# ---------------------------------------------------------------------------

class TestWorkContextExtraction:
    def test_working_on_project(self, extractor):
        beliefs = extractor.extract_from_turn("I'm working on the penny assistant")
        preds = [b["predicate"] for b in beliefs]
        assert Predicate.WORKS_ON in preds

    def test_uses_macos(self, extractor):
        beliefs = extractor.extract_from_turn("I'm on macOS")
        preds = [b["predicate"] for b in beliefs]
        assert Predicate.USES in preds


# ---------------------------------------------------------------------------
# No false positives
# ---------------------------------------------------------------------------

class TestNoFalsePositives:
    def test_no_extraction_from_question(self, extractor):
        beliefs = extractor.extract_from_turn("What time is it?")
        assert len(beliefs) == 0

    def test_no_extraction_from_generic(self, extractor):
        beliefs = extractor.extract_from_turn("Ok sounds good")
        assert len(beliefs) == 0

    def test_skips_trivial_objects(self, extractor):
        # "it" / "that" should be filtered
        beliefs = extractor.extract_from_turn("I never used it before")
        objects = [b["object_value"] for b in beliefs]
        assert "it" not in objects


# ---------------------------------------------------------------------------
# Correction signal
# ---------------------------------------------------------------------------

class TestCorrectionDetection:
    def test_actually_signals_correction(self, extractor):
        assert extractor.detect_correction("Actually, I prefer Python not Ruby")

    def test_wrong_signals_correction(self, extractor):
        assert extractor.detect_correction("That's not right")

    def test_neutral_no_correction(self, extractor):
        assert not extractor.detect_correction("I want to refactor this module")

    def test_apply_explicit_correction(self, extractor):
        extractor.extract_from_turn("I'm learning JavaScript")
        result = extractor.extract_explicit_correction(
            Predicate.LEARNING, "javascript", "typescript"
        )
        assert result is True
        beliefs = extractor.store.get_beliefs(predicate=Predicate.LEARNING)
        assert beliefs[0]["object_value"] == "typescript"


# ---------------------------------------------------------------------------
# Context snippet
# ---------------------------------------------------------------------------

class TestContextSnippet:
    def test_empty_snippet_when_no_beliefs(self, extractor):
        snippet = extractor.build_context_snippet()
        assert snippet == ""

    def test_snippet_format(self, extractor):
        for _ in range(4):
            extractor.extract_from_turn("I'm an expert in Python")
        snippet = extractor.build_context_snippet()
        assert snippet.startswith("[User:")
        assert "python" in snippet

    def test_relevant_beliefs_filtered_by_keyword(self, extractor):
        for _ in range(4):
            extractor.extract_from_turn("I know Python well")
        for _ in range(4):
            extractor.extract_from_turn("I prefer brief answers")

        python_relevant = extractor.get_relevant_beliefs(["python"], min_confidence=0.5)
        preds_objs = [(b["predicate"], b["object_value"]) for b in python_relevant]
        # python-related belief should rank higher
        assert any("python" in obj for _, obj in preds_objs)
