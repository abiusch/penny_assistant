"""Tests for the updated research gating heuristics."""

from core.query_classifier import needs_research


def test_coding_prompt_stays_local() -> None:
    assert needs_research("Review this Python function for a bug") is False


def test_time_sensitive_goes_research() -> None:
    assert needs_research("What is the latest NVIDIA driver release notes?") is True
