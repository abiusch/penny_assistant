"""
Week 13 Fix 4: cross-system integration helpers for the User Model.

These are small, dependency-injected functions so they can be unit-tested
without booting the full ResearchFirstPipeline, then called from the pipeline
with its real objects. Each is null-safe: if a subsystem is disabled (None),
the helper degrades quietly.

Wiring:
  - beliefs_for_judgment   → Judgment (8.5): attach belief context to clarify checks
  - apply_outcome_to_beliefs → Outcome (11): +/- confidence from user reactions
  - belief_from_hebbian_pattern → Hebbian (9/10): promoted patterns seed beliefs
  - gated_observe          → Safety (10): a pluggable write gate (budget hook)
"""

from typing import Any, Callable, Dict, List, Optional

POSITIVE_BELIEF_BOOST = 0.02
NEGATIVE_BELIEF_PENALTY = 0.05


def beliefs_for_judgment(
    extractor: Any,
    context_keywords: Optional[List[str]],
    min_confidence: float = 0.6,
    max_results: int = 5,
) -> List[Dict[str, Any]]:
    """Relevant beliefs to attach to the judgment/clarify context (4a)."""
    if extractor is None:
        return []
    try:
        return extractor.get_relevant_beliefs(
            context_keywords or [],
            min_confidence=min_confidence,
            max_results=max_results,
        )
    except Exception:
        return []


def apply_outcome_to_beliefs(
    store: Any,
    reaction: str,
    beliefs: List[Dict[str, Any]],
    boost: float = POSITIVE_BELIEF_BOOST,
    penalty: float = NEGATIVE_BELIEF_PENALTY,
) -> List[Dict[str, Any]]:
    """
    Reinforce beliefs on a positive outcome, weaken them on a negative one (4b).
    Neutral reactions are a no-op. Returns the updated belief dicts.
    """
    if store is None or not beliefs:
        return []
    updated: List[Dict[str, Any]] = []
    for b in beliefs:
        if reaction == "positive":
            r = store.reinforce_belief(b["predicate"], b["object_value"], boost=boost)
        elif reaction == "negative":
            r = store.weaken_belief(b["predicate"], b["object_value"], penalty=penalty)
        else:
            r = None
        if r:
            updated.append(r)
    return updated


def belief_from_hebbian_pattern(store: Any, pattern: Any) -> Optional[Dict[str, Any]]:
    """
    When Hebbian promotes a *vocabulary* pattern, record a corresponding
    communication-style belief via staging (4c). Other pattern types are ignored.
    `pattern` may be an object with attributes or a dict.
    """
    if store is None or pattern is None:
        return None

    def _get(key):
        if isinstance(pattern, dict):
            return pattern.get(key)
        return getattr(pattern, key, None)

    if _get("pattern_type") != "vocabulary":
        return None
    term = _get("term")
    if not term:
        return None

    object_value = str(term).strip().lower().replace(" ", "_")[:60]
    if not object_value:
        return None
    return store.observe_belief(
        predicate="responds_well_to",
        object_value=object_value,
        evidence_text="hebbian_vocabulary_promotion",
    )


def gated_observe(
    store: Any,
    predicate: str,
    object_value: str,
    evidence_text: str = "",
    session_id: Optional[str] = None,
    can_write: Optional[Callable[[], bool]] = None,
) -> Optional[Dict[str, Any]]:
    """
    Observe a belief only if the write gate permits it (4d).

    `can_write` is a pluggable predicate (e.g. tied to a per-turn/per-day budget).
    When None, writes are always allowed. Returns the observe_belief result, or a
    skip marker when gated.
    """
    if store is None:
        return None
    if can_write is not None and not can_write():
        return {"status": "skipped_budget", "belief": None, "observation_count": 0}
    return store.observe_belief(predicate, object_value, evidence_text, session_id)
