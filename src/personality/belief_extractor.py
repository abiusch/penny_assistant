"""
BeliefExtractor - Week 13: User Model.

Extracts explicit beliefs from conversation turns using pattern matching,
then stores them in UserBeliefStore.

Design principles:
  - Only infer what's stated — no guessing from tone/emotion
  - High-precision > high-recall (better to miss a belief than create a wrong one)
  - Judgment system already filters ambiguous inputs (Week 8.5)
"""

import re
import logging
from typing import List, Tuple, Optional, Dict, Any

from src.personality.user_belief_store import UserBeliefStore, Predicate

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Extraction patterns
# Each entry: (predicate, compiled_regex, object_group_index)
#   The regex must have at least one capture group for the object value.
# ---------------------------------------------------------------------------

# Helper: compile with IGNORECASE
def _r(pattern: str) -> re.Pattern:
    return re.compile(pattern, re.IGNORECASE)


EXTRACTION_PATTERNS: List[Tuple[str, re.Pattern, int]] = [

    # --- Expertise ---
    # "I'm a Python developer", "I'm a senior engineer"
    (Predicate.IS, _r(r"\bi(?:'m| am) an? ([\w\s]{3,30}?)(?:\s+at\b|$|[,.]|\s+and\b)"), 1),

    # "I work in / with Python", "I use FastAPI"
    (Predicate.WORKS_WITH, _r(r"\bi (?:work (?:in|with)|use|work using) ([\w\s\+\#\.]{2,25})(?:\s+a lot|\s+for\b|\s+to\b|\s+every|\s+all\b|$|[,.])"), 1),

    # "I'm an expert in / at Python"
    (Predicate.EXPERT_IN, _r(r"\bi(?:'m| am) (?:an? )?expert (?:in|at|with) ([\w\s\+\#\.]{2,30})"), 1),

    # "I know Python well", "I know a lot about databases"
    (Predicate.EXPERT_IN, _r(r"\bi (?:know|understand) ([\w\s\+\#\.]{2,30}) well\b"), 1),

    # "I'm learning Rust", "I'm trying to learn TypeScript"
    (Predicate.LEARNING, _r(r"\bi(?:'m| am) (?:trying to )?learn(?:ing)? ([\w\s\+\#\.]{2,25})"), 1),

    # "I've never used Docker", "I'm not familiar with Kubernetes"
    (Predicate.UNFAMILIAR_WITH, _r(r"\bi(?:'ve| have)? never (?:used|tried|worked with) ([\w\s\+\#\.]{2,25})"), 1),
    (Predicate.UNFAMILIAR_WITH, _r(r"\bi(?:'m| am) not familiar with ([\w\s\+\#\.]{2,25})"), 1),

    # --- Preferences ---
    # "I prefer brief answers", "I like short responses"
    (Predicate.PREFERS, _r(r"\bi (?:prefer|like|want|love) ([\w\s]{3,40}?)(?:\s+over\b|$|[,.]|\s+when\b|\s+rather\b)"), 1),

    # "I don't like long explanations", "I hate verbose responses"
    (Predicate.DISLIKES, _r(r"\bi (?:don't|do not|hate|dislike|can't stand) (?:like )?(\b[\w\s]{3,40}?)(?:\s+in\b|$|[,.]|\s+when\b)"), 1),

    # --- Work context ---
    # "I'm working on penny_assistant", "I work at Anthropic"
    (Predicate.WORKS_ON, _r(r"\bi(?:'m| am) working on ([\w\s_\-]{3,40})"), 1),
    (Predicate.WORKS_AT,  _r(r"\bi (?:work at|work for) ([\w\s]{3,30})"), 1),

    # --- Platform / tools ---
    # "I'm on macOS", "I use Ubuntu"
    (Predicate.USES, _r(r"\bi(?:'m| am) (?:using|on|running) (macOS|Ubuntu|Windows|Linux|[\w\s]{3,20}?)(?:\s+\d|\s+version|\s+and\b|$|[,.])"), 1),

    # "I have a Mac", "I have 16GB RAM"
    (Predicate.HAS, _r(r"\bi(?:'ve| have) (?:a |an )?(Mac(?:Book)?|Linux box|Windows PC|Raspberry Pi)"), 1),

    # --- Communication style ---
    # "I respond well to examples", "I understand better with code examples"
    (Predicate.RESPONDS_WELL_TO, _r(r"\bi (?:respond|understand|learn) (?:well |best )?(?:to |with |from )?(code examples?|examples?|analogies|visuals?|step.by.step)"), 1),

    # "it's frustrating when responses are too long"
    (Predicate.FRUSTRATED_BY, _r(r"\bit(?:'s| is) frustrating when ([\w\s]{5,50}?)(?:$|[,.])"), 1),
]

# Phrases that mean the user is correcting Penny
CORRECTION_SIGNALS = [
    r"\bthat(?:'s| is) (?:not |wrong|incorrect)",
    r"\bactually[,\s]",
    r"\bno[,\s]+i (?:don't|do not|am not|haven't)",
    r"\bcorrect(?:ion|ing)?[:\s]",
    r"\byou(?:'re| are) wrong",
    r"\bnot quite[,\s]",
]
_CORRECTION_RE = [re.compile(p, re.IGNORECASE) for p in CORRECTION_SIGNALS]


def _clean_object(value: str) -> str:
    """Normalise extracted object values."""
    value = value.strip(" .,;:!?")
    # Replace spaces with underscores for storage (easier to query)
    value = "_".join(value.lower().split())
    return value[:60]


def _is_correction_signal(text: str) -> bool:
    return any(p.search(text) for p in _CORRECTION_RE)


# ---------------------------------------------------------------------------
# Main class
# ---------------------------------------------------------------------------

class BeliefExtractor:
    """
    Extracts beliefs from user messages and updates UserBeliefStore.

    Usage:
        extractor = BeliefExtractor(belief_store)
        new_beliefs = extractor.extract_from_turn(user_message, session_id)
    """

    def __init__(self, belief_store: UserBeliefStore):
        self.store = belief_store

    def extract_from_turn(
        self,
        user_message: str,
        session_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Extract beliefs from a single user message.

        Returns list of belief dicts that were added or updated.
        """
        extracted: List[Dict[str, Any]] = []

        for predicate, pattern, group_idx in EXTRACTION_PATTERNS:
            for match in pattern.finditer(user_message):
                try:
                    raw_object = match.group(group_idx)
                    if not raw_object or len(raw_object.strip()) < 2:
                        continue

                    object_value = _clean_object(raw_object)
                    if not object_value or len(object_value) < 2:
                        continue

                    # Skip very generic matches
                    if object_value in {"it", "that", "this", "them", "a", "an", "the"}:
                        continue

                    belief = self.store.add_or_update_belief(
                        predicate=predicate,
                        object_value=object_value,
                        evidence_text=user_message[:200],
                        session_id=session_id,
                        source="inferred",
                    )
                    extracted.append(belief)
                    logger.debug(
                        f"Extracted belief: {predicate}→{object_value}"
                    )
                except (IndexError, AttributeError):
                    continue

        if extracted:
            logger.info(
                f"🧠 UserModel: extracted {len(extracted)} belief(s) from turn"
            )

        return extracted

    def detect_correction(self, user_message: str) -> bool:
        """
        Check if the user is correcting something Penny said.
        Caller should ask the user to specify what to correct.
        """
        return _is_correction_signal(user_message)

    def extract_explicit_correction(
        self,
        predicate: str,
        old_value: str,
        new_value: str,
        reason: str = "",
    ) -> bool:
        """
        Apply a user-specified correction to the belief store.
        Returns True if belief was found and corrected.
        """
        result = self.store.correct_belief(
            predicate=predicate,
            old_object_value=old_value,
            new_object_value=new_value,
            reason=reason,
        )
        if result:
            logger.info(f"✅ Belief corrected by user: {predicate}: {old_value!r}→{new_value!r}")
        return result

    def get_relevant_beliefs(
        self,
        context_keywords: List[str],
        min_confidence: float = 0.6,
        max_results: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve beliefs relevant to the current context for prompt injection.

        Args:
            context_keywords: Words from the current topic (e.g. ["Python", "async"])
            min_confidence:   Minimum confidence threshold
            max_results:      Max beliefs to return

        Returns sorted by confidence, filtered by keyword relevance.
        """
        all_beliefs = self.store.get_beliefs(min_confidence=min_confidence)

        if not context_keywords:
            return all_beliefs[:max_results]

        # Score by keyword matches
        keywords_lower = [k.lower() for k in context_keywords]

        def score(b: Dict) -> int:
            text = f"{b['predicate']} {b['object_value']}".lower()
            return sum(1 for kw in keywords_lower if kw in text)

        scored = sorted(all_beliefs, key=score, reverse=True)
        return scored[:max_results]

    def build_context_snippet(
        self,
        context_keywords: Optional[List[str]] = None,
        min_confidence: float = 0.65,
    ) -> str:
        """
        Build a compact belief context string to inject into the LLM prompt.

        Example output:
            [User: expert_in→python, prefers→brief_answers, works_on→penny_assistant]
        """
        beliefs = self.get_relevant_beliefs(
            context_keywords=context_keywords or [],
            min_confidence=min_confidence,
            max_results=5,
        )
        if not beliefs:
            return ""

        parts = [
            f"{b['predicate']}→{b['object_value']}"
            for b in beliefs
        ]
        return f"[User: {', '.join(parts)}]"
