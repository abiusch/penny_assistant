"""Lightweight heuristics for deciding when external research is required."""

from __future__ import annotations

from functools import lru_cache
from typing import Iterable

_TRIVIAL_KEYWORDS = (
    "code",
    "bug",
    "function",
    "syntax",
    "average",
    "loop",
    "python",
    "error",
)

_FRESHNESS_KEYWORDS = (
    "latest",
    "today",
    "current",
    "breaking",
    "price",
    "release notes",
    "news",
    "update",
)


def _contains_any(text: str, needles: Iterable[str]) -> bool:
    return any(needle in text for needle in needles)


def needs_research(query: str) -> bool:
    """Determine whether a query should go through the research stack."""
    q = (query or "").lower()

    if _contains_any(q, _TRIVIAL_KEYWORDS):
        return False

    if _contains_any(q, _FRESHNESS_KEYWORDS):
        return True

    return llm_intent_score(q) > 0.80 and not local_answer_confident(q)


@lru_cache(maxsize=512)
def llm_intent_score(query: str) -> float:
    """Stub scoring function: higher value implies the user wants current info."""
    score = 0.5
    if _contains_any(query, _FRESHNESS_KEYWORDS):
        score += 0.4
    if "financial" in query or "stock" in query:
        score += 0.2
    return min(score, 1.0)


@lru_cache(maxsize=512)
def local_answer_confident(query: str) -> bool:
    """Return True when Penny can likely answer from local knowledge."""
    return _contains_any(query, _TRIVIAL_KEYWORDS)


__all__ = ["needs_research", "llm_intent_score", "local_answer_confident"]
