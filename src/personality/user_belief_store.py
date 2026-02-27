"""
UserBeliefStore - Week 13: User Model.

Stores explicit, human-readable beliefs about the user as a lightweight
knowledge graph (subject → predicate → object_value triples with metadata).

Architecture inspired by 2026 AI Landscape Review recommendation:
  "Dual memory: implicit statistical patterns (Hebbian) +
   explicit, human-readable facts in a knowledge graph"

Example beliefs:
    CJ → prefers → brief_answers          (confidence=0.85)
    CJ → expert_in → Python               (confidence=0.92)
    CJ → works_on → penny_assistant       (confidence=0.99)
    CJ → dislikes → verbose_explanations  (confidence=0.71)

The user can inspect and correct beliefs at any time:
    "Here's what I think I know about you — want to correct anything?"
"""

import sqlite3
import uuid
import logging
from datetime import datetime
from typing import Optional, Dict, List, Any, Tuple

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Belief predicates (typed vocabulary)
# ---------------------------------------------------------------------------

class Predicate:
    # Preferences
    PREFERS      = "prefers"
    DISLIKES     = "dislikes"
    LIKES        = "likes"

    # Expertise
    EXPERT_IN    = "expert_in"
    LEARNING     = "learning"
    UNFAMILIAR_WITH = "unfamiliar_with"

    # Work / projects
    WORKS_ON     = "works_on"
    WORKS_WITH   = "works_with"   # tools / languages
    WORKS_AT     = "works_at"

    # Personal facts
    IS           = "is"           # CJ → is → developer
    HAS          = "has"          # CJ → has → macOS
    USES         = "uses"         # CJ → uses → Python 3.13

    # Communication style
    RESPONDS_WELL_TO = "responds_well_to"
    FRUSTRATED_BY    = "frustrated_by"

    ALL = {
        PREFERS, DISLIKES, LIKES,
        EXPERT_IN, LEARNING, UNFAMILIAR_WITH,
        WORKS_ON, WORKS_WITH, WORKS_AT,
        IS, HAS, USES,
        RESPONDS_WELL_TO, FRUSTRATED_BY,
    }


# ---------------------------------------------------------------------------
# Confidence helpers
# ---------------------------------------------------------------------------

# Base confidence for a first-time belief
BASE_CONFIDENCE = 0.5
# Max confidence we'll assign (never fully certain)
MAX_CONFIDENCE  = 0.97
# Each new piece of evidence moves confidence toward MAX
EVIDENCE_BOOST  = 0.08
# A user correction resets to high confidence (they said so explicitly)
CORRECTION_CONFIDENCE = 0.95


def _updated_confidence(current: float, evidence_count: int) -> float:
    """Bayesian-ish update: each new evidence boosts confidence."""
    return min(current + EVIDENCE_BOOST, MAX_CONFIDENCE)


# ---------------------------------------------------------------------------
# Main class
# ---------------------------------------------------------------------------

class UserBeliefStore:
    """
    Lightweight knowledge graph of beliefs about the user.

    Key methods:
        add_or_update_belief()   — upsert a belief triple
        get_beliefs()            — retrieve beliefs (optionally filtered)
        correct_belief()         — user explicitly corrects a belief
        get_summary()            — human-readable summary of top beliefs
        remove_belief()          — delete a belief
        get_belief_report()      — statistics overview
    """

    # Minimum confidence to include in summary
    SUMMARY_MIN_CONFIDENCE = 0.6

    def __init__(
        self,
        db_path: str = "data/personality_tracking.db",
        subject: str = "user",
    ):
        self.db_path = db_path
        self.subject = subject   # The user's identifier (e.g. "CJ")
        self._init_db()

    # ------------------------------------------------------------------
    # DB setup
    # ------------------------------------------------------------------

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._get_conn() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS user_beliefs (
                    belief_id      TEXT PRIMARY KEY,
                    subject        TEXT NOT NULL,
                    predicate      TEXT NOT NULL,
                    object_value   TEXT NOT NULL,
                    confidence     REAL NOT NULL DEFAULT 0.5,
                    evidence_count INTEGER NOT NULL DEFAULT 1,
                    context        TEXT,
                    created_at     TIMESTAMP NOT NULL,
                    last_updated   TIMESTAMP NOT NULL,
                    source         TEXT DEFAULT 'inferred'
                );

                CREATE TABLE IF NOT EXISTS belief_evidence (
                    id             INTEGER PRIMARY KEY AUTOINCREMENT,
                    belief_id      TEXT NOT NULL,
                    evidence_text  TEXT NOT NULL,
                    timestamp      TIMESTAMP NOT NULL,
                    session_id     TEXT
                );

                CREATE TABLE IF NOT EXISTS belief_corrections (
                    id             INTEGER PRIMARY KEY AUTOINCREMENT,
                    belief_id      TEXT NOT NULL,
                    old_value      TEXT,
                    new_value      TEXT NOT NULL,
                    corrected_at   TIMESTAMP NOT NULL,
                    reason         TEXT
                );

                CREATE UNIQUE INDEX IF NOT EXISTS idx_belief_triple
                    ON user_beliefs(subject, predicate, object_value);
                CREATE INDEX IF NOT EXISTS idx_belief_predicate
                    ON user_beliefs(predicate, subject);
                CREATE INDEX IF NOT EXISTS idx_evidence_belief
                    ON belief_evidence(belief_id);
            """)

    # ------------------------------------------------------------------
    # Core API
    # ------------------------------------------------------------------

    def add_or_update_belief(
        self,
        predicate: str,
        object_value: str,
        evidence_text: str = "",
        context: str = "",
        session_id: Optional[str] = None,
        source: str = "inferred",
    ) -> Dict[str, Any]:
        """
        Add a new belief or strengthen an existing one.

        Returns the belief dict (with updated confidence).
        """
        now = datetime.now().isoformat()
        subject = self.subject

        with self._get_conn() as conn:
            existing = conn.execute(
                """
                SELECT * FROM user_beliefs
                 WHERE subject = ? AND predicate = ? AND object_value = ?
                """,
                (subject, predicate, object_value),
            ).fetchone()

            if existing is None:
                belief_id = f"bel_{uuid.uuid4().hex[:10]}"
                conn.execute(
                    """
                    INSERT INTO user_beliefs
                        (belief_id, subject, predicate, object_value,
                         confidence, evidence_count, context,
                         created_at, last_updated, source)
                    VALUES (?, ?, ?, ?, ?, 1, ?, ?, ?, ?)
                    """,
                    (
                        belief_id, subject, predicate, object_value,
                        BASE_CONFIDENCE, context, now, now, source,
                    ),
                )
                new_confidence = BASE_CONFIDENCE
            else:
                belief_id = existing["belief_id"]
                new_count      = existing["evidence_count"] + 1
                new_confidence = _updated_confidence(
                    existing["confidence"], new_count
                )
                conn.execute(
                    """
                    UPDATE user_beliefs
                       SET confidence     = ?,
                           evidence_count = ?,
                           last_updated   = ?,
                           context        = COALESCE(NULLIF(?, ''), context)
                     WHERE belief_id = ?
                    """,
                    (new_confidence, new_count, now, context, belief_id),
                )

            # Log evidence
            if evidence_text:
                conn.execute(
                    """
                    INSERT INTO belief_evidence
                        (belief_id, evidence_text, timestamp, session_id)
                    VALUES (?, ?, ?, ?)
                    """,
                    (belief_id, evidence_text[:300], now, session_id),
                )

        logger.debug(
            f"Belief updated: {subject}→{predicate}→{object_value} "
            f"(conf={new_confidence:.2f})"
        )
        return self.get_belief(belief_id)

    def get_belief(self, belief_id: str) -> Optional[Dict]:
        with self._get_conn() as conn:
            row = conn.execute(
                "SELECT * FROM user_beliefs WHERE belief_id = ?", (belief_id,)
            ).fetchone()
        return dict(row) if row else None

    def get_beliefs(
        self,
        predicate: Optional[str] = None,
        min_confidence: float = 0.0,
        limit: int = 50,
    ) -> List[Dict]:
        """
        Retrieve beliefs, optionally filtered by predicate or confidence.

        Returns list sorted by confidence descending.
        """
        with self._get_conn() as conn:
            if predicate:
                rows = conn.execute(
                    """
                    SELECT * FROM user_beliefs
                     WHERE subject = ? AND predicate = ?
                       AND confidence >= ?
                     ORDER BY confidence DESC
                     LIMIT ?
                    """,
                    (self.subject, predicate, min_confidence, limit),
                ).fetchall()
            else:
                rows = conn.execute(
                    """
                    SELECT * FROM user_beliefs
                     WHERE subject = ?
                       AND confidence >= ?
                     ORDER BY confidence DESC
                     LIMIT ?
                    """,
                    (self.subject, min_confidence, limit),
                ).fetchall()
        return [dict(r) for r in rows]

    def correct_belief(
        self,
        predicate: str,
        old_object_value: str,
        new_object_value: str,
        reason: str = "",
    ) -> bool:
        """
        User explicitly corrects a belief.

        Updates the object_value and sets confidence to CORRECTION_CONFIDENCE.
        Logs the correction in belief_corrections.
        Returns True if belief found and corrected.
        """
        now = datetime.now().isoformat()
        with self._get_conn() as conn:
            row = conn.execute(
                """
                SELECT belief_id FROM user_beliefs
                 WHERE subject = ? AND predicate = ? AND object_value = ?
                """,
                (self.subject, predicate, old_object_value),
            ).fetchone()

            if row is None:
                return False

            belief_id = row["belief_id"]
            conn.execute(
                """
                UPDATE user_beliefs
                   SET object_value  = ?,
                       confidence    = ?,
                       last_updated  = ?,
                       source        = 'user_corrected'
                 WHERE belief_id = ?
                """,
                (new_object_value, CORRECTION_CONFIDENCE, now, belief_id),
            )
            conn.execute(
                """
                INSERT INTO belief_corrections
                    (belief_id, old_value, new_value, corrected_at, reason)
                VALUES (?, ?, ?, ?, ?)
                """,
                (belief_id, old_object_value, new_object_value, now, reason),
            )
        logger.info(
            f"Belief corrected: {predicate}: "
            f"{old_object_value!r} → {new_object_value!r}"
        )
        return True

    def remove_belief(self, predicate: str, object_value: str) -> bool:
        """Delete a belief. Returns True if found and removed."""
        with self._get_conn() as conn:
            cur = conn.execute(
                """
                DELETE FROM user_beliefs
                 WHERE subject = ? AND predicate = ? AND object_value = ?
                """,
                (self.subject, predicate, object_value),
            )
        return cur.rowcount > 0

    def get_summary(self, max_beliefs: int = 10) -> str:
        """
        Generate a human-readable summary Penny can show the user.

        Example output:
            Here's what I think I know about you:
            • You prefer brief_answers (85% confident)
            • You're an expert in Python (92% confident)
            • You work on penny_assistant (99% confident)
        """
        beliefs = self.get_beliefs(min_confidence=self.SUMMARY_MIN_CONFIDENCE)
        if not beliefs:
            return "I don't have any strong beliefs about you yet — still learning!"

        lines = ["Here's what I think I know about you:"]
        for b in beliefs[:max_beliefs]:
            pred  = b["predicate"].replace("_", " ")
            obj   = b["object_value"].replace("_", " ")
            conf  = int(b["confidence"] * 100)
            source_tag = " ✓" if b["source"] == "user_corrected" else ""
            lines.append(f"  • {pred}: {obj} ({conf}% confident){source_tag}")

        lines.append("\nWant to correct anything?")
        return "\n".join(lines)

    def get_belief_report(self) -> Dict[str, Any]:
        """Return statistics overview."""
        with self._get_conn() as conn:
            totals = conn.execute(
                """
                SELECT
                    COUNT(*)                                        AS total,
                    AVG(confidence)                                 AS avg_confidence,
                    SUM(source = 'user_corrected')                  AS corrected,
                    SUM(confidence >= 0.8)                          AS high_confidence,
                    SUM(confidence < 0.6)                           AS low_confidence
                  FROM user_beliefs
                 WHERE subject = ?
                """,
                (self.subject,),
            ).fetchone()

            by_predicate = conn.execute(
                """
                SELECT predicate, COUNT(*) AS cnt
                  FROM user_beliefs
                 WHERE subject = ?
                 GROUP BY predicate
                 ORDER BY cnt DESC
                """,
                (self.subject,),
            ).fetchall()

        return {
            "total":           totals["total"]          or 0,
            "avg_confidence":  round(totals["avg_confidence"] or 0, 3),
            "corrected":       totals["corrected"]       or 0,
            "high_confidence": totals["high_confidence"] or 0,
            "low_confidence":  totals["low_confidence"]  or 0,
            "by_predicate":    [dict(r) for r in by_predicate],
        }
