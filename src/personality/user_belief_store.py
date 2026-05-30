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
import json
import logging
from datetime import datetime, timedelta
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

    # --- Temporal decay (Fix 3) ---
    DEFAULT_DECAY_RATE = 0.005            # confidence lost per idle day
    MIN_CONFIDENCE_BEFORE_ARCHIVE = 0.3   # below this, archive instead of keep

    # --- Contradiction detection (Fix 5) ---
    # Predicate pairs that conflict when they share the same object.
    CONTRADICTORY_PREDICATES = {
        "prefers": "dislikes",
        "likes": "dislikes",
        "expert_in": "unfamiliar_with",
        "responds_well_to": "frustrated_by",
    }
    # Object words that conflict under the same predicate.
    CONTRADICTORY_OBJECTS = [
        ("brief", "detailed"),
        ("brief", "verbose"),
        ("short", "long"),
        ("formal", "casual"),
        ("morning", "night"),
        ("simple", "complex"),
        ("dark", "light"),
    ]

    def __init__(
        self,
        db_path: str = "data/personality_tracking.db",
        subject: str = "user",
        staging_min_observations: int = 3,
        staging_min_days: int = 3,
        staging_max_age_days: int = 30,
    ):
        self.db_path = db_path
        self.subject = subject   # The user's identifier (e.g. "CJ")
        # --- Staging / quarantine config (Fix 2) ---
        self.STAGING_MIN_OBSERVATIONS = staging_min_observations
        self.STAGING_MIN_DAYS = staging_min_days
        self.STAGING_MAX_AGE_DAYS = staging_max_age_days
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

                -- Fix 2: provisional beliefs awaiting promotion to permanent
                CREATE TABLE IF NOT EXISTS belief_staging (
                    id                INTEGER PRIMARY KEY AUTOINCREMENT,
                    subject           TEXT NOT NULL,
                    predicate         TEXT NOT NULL,
                    object_value      TEXT NOT NULL,
                    observations      TEXT NOT NULL,   -- JSON array of {ts, evidence}
                    first_seen        TIMESTAMP NOT NULL,
                    last_seen         TIMESTAMP NOT NULL,
                    observation_count INTEGER NOT NULL DEFAULT 1,
                    UNIQUE(subject, predicate, object_value)
                );

                -- Fix 3: beliefs that decayed below the archive threshold
                CREATE TABLE IF NOT EXISTS belief_archive (
                    id               INTEGER PRIMARY KEY AUTOINCREMENT,
                    subject          TEXT NOT NULL,
                    predicate        TEXT NOT NULL,
                    object_value     TEXT NOT NULL,
                    final_confidence REAL NOT NULL,
                    context          TEXT,
                    source           TEXT,
                    archived_at      TIMESTAMP NOT NULL,
                    UNIQUE(subject, predicate, object_value)
                );

                CREATE UNIQUE INDEX IF NOT EXISTS idx_belief_triple
                    ON user_beliefs(subject, predicate, object_value);
                CREATE INDEX IF NOT EXISTS idx_belief_predicate
                    ON user_beliefs(predicate, subject);
                CREATE INDEX IF NOT EXISTS idx_evidence_belief
                    ON belief_evidence(belief_id);
                CREATE INDEX IF NOT EXISTS idx_staging_triple
                    ON belief_staging(subject, predicate, object_value);
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
        initial_confidence: float = BASE_CONFIDENCE,
    ) -> Dict[str, Any]:
        """
        Add a new belief or strengthen an existing one.

        ``initial_confidence`` sets the starting confidence for a *brand new*
        belief (defaults to BASE_CONFIDENCE; staging promotions pass 0.6).

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
                        initial_confidence, context, now, now, source,
                    ),
                )
                new_confidence = initial_confidence
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

    # ------------------------------------------------------------------
    # Fix 2: Staging / quarantine
    # ------------------------------------------------------------------

    def observe_belief(
        self,
        predicate: str,
        object_value: str,
        evidence_text: str = "",
        session_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Observe a *candidate* belief from conversation.

        New beliefs go to STAGING first and only become permanent after
        STAGING_MIN_OBSERVATIONS spanning STAGING_MIN_DAYS. Already-permanent
        beliefs are reinforced immediately. Contradictions are blocked.

        Returns {"status": "reinforced"|"staged"|"promoted"|"contradiction",
                 "belief": <dict or None>, "observation_count": int}.

        NOTE: user corrections bypass staging entirely (use correct_belief()).
        """
        now = datetime.now()
        now_iso = now.isoformat()
        subject = self.subject

        # Already permanent → reinforce immediately.
        if self._get_permanent_belief(predicate, object_value) is not None:
            belief = self.add_or_update_belief(
                predicate, object_value, evidence_text, session_id=session_id
            )
            return {"status": "reinforced", "belief": belief,
                    "observation_count": belief["evidence_count"]}

        # Block observations that contradict an existing permanent belief.
        conflict = self.check_before_write(predicate, object_value)
        if conflict:
            self._log_contradiction(conflict, predicate, object_value)
            return {"status": "contradiction", "belief": None,
                    "observation_count": 0, "conflict": conflict}

        with self._get_conn() as conn:
            row = conn.execute(
                """
                SELECT * FROM belief_staging
                 WHERE subject = ? AND predicate = ? AND object_value = ?
                """,
                (subject, predicate, object_value),
            ).fetchone()

            if row is None:
                observations = [{"ts": now_iso, "evidence": evidence_text[:200]}]
                conn.execute(
                    """
                    INSERT INTO belief_staging
                        (subject, predicate, object_value, observations,
                         first_seen, last_seen, observation_count)
                    VALUES (?, ?, ?, ?, ?, ?, 1)
                    """,
                    (subject, predicate, object_value,
                     json.dumps(observations), now_iso, now_iso),
                )
                return {"status": "staged", "belief": None, "observation_count": 1}

            # Existing staging entry → add observation
            observations = json.loads(row["observations"])
            observations.append({"ts": now_iso, "evidence": evidence_text[:200]})
            new_count = row["observation_count"] + 1
            conn.execute(
                """
                UPDATE belief_staging
                   SET observations = ?, last_seen = ?, observation_count = ?
                 WHERE id = ?
                """,
                (json.dumps(observations), now_iso, new_count, row["id"]),
            )
            staging = {
                "first_seen": row["first_seen"],
                "last_seen": now_iso,
                "observation_count": new_count,
            }

        if self._should_promote(staging):
            belief = self._promote_to_permanent(
                predicate, object_value, evidence_text, session_id
            )
            return {"status": "promoted", "belief": belief,
                    "observation_count": new_count}

        return {"status": "staged", "belief": None, "observation_count": new_count}

    def _get_permanent_belief(self, predicate: str, object_value: str) -> Optional[Dict]:
        with self._get_conn() as conn:
            row = conn.execute(
                """
                SELECT * FROM user_beliefs
                 WHERE subject = ? AND predicate = ? AND object_value = ?
                """,
                (self.subject, predicate, object_value),
            ).fetchone()
        return dict(row) if row else None

    def _should_promote(self, staging: Dict[str, Any]) -> bool:
        if staging["observation_count"] < self.STAGING_MIN_OBSERVATIONS:
            return False
        first = datetime.fromisoformat(staging["first_seen"])
        last = datetime.fromisoformat(staging["last_seen"])
        return (last - first).days >= self.STAGING_MIN_DAYS

    def _promote_to_permanent(
        self, predicate: str, object_value: str,
        evidence_text: str = "", session_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        belief = self.add_or_update_belief(
            predicate, object_value, evidence_text,
            session_id=session_id, source="promoted_from_staging",
            initial_confidence=0.6,
        )
        with self._get_conn() as conn:
            conn.execute(
                """
                DELETE FROM belief_staging
                 WHERE subject = ? AND predicate = ? AND object_value = ?
                """,
                (self.subject, predicate, object_value),
            )
        logger.info(f"Promoted belief from staging: {predicate}→{object_value}")
        return belief

    def get_staging(self) -> List[Dict]:
        """Return all staged (not-yet-permanent) candidate beliefs."""
        with self._get_conn() as conn:
            rows = conn.execute(
                "SELECT * FROM belief_staging WHERE subject = ? ORDER BY observation_count DESC",
                (self.subject,),
            ).fetchall()
        return [dict(r) for r in rows]

    def cleanup_expired_staging(self) -> int:
        """Drop staging entries older than STAGING_MAX_AGE_DAYS. Returns count removed."""
        cutoff = (datetime.now() - timedelta(days=self.STAGING_MAX_AGE_DAYS)).isoformat()
        with self._get_conn() as conn:
            cur = conn.execute(
                "DELETE FROM belief_staging WHERE subject = ? AND first_seen < ?",
                (self.subject, cutoff),
            )
        return cur.rowcount

    # ------------------------------------------------------------------
    # Fix 3: Temporal decay + archiving
    # ------------------------------------------------------------------

    def _get_all_beliefs(self) -> List[Dict]:
        with self._get_conn() as conn:
            rows = conn.execute(
                "SELECT * FROM user_beliefs WHERE subject = ?", (self.subject,)
            ).fetchall()
        return [dict(r) for r in rows]

    def apply_temporal_decay(self, decay_rate: Optional[float] = None) -> Dict[str, int]:
        """
        Reduce confidence of beliefs by their idle time. Beliefs that fall below
        MIN_CONFIDENCE_BEFORE_ARCHIVE are moved to belief_archive.

        Intended to run during an IDLE phase (end of session / manual trigger),
        NOT per-turn. Returns {"decayed": n, "archived": n}.
        """
        rate = self.DEFAULT_DECAY_RATE if decay_rate is None else decay_rate
        now = datetime.now()
        decayed = archived = 0

        for belief in self._get_all_beliefs():
            last = datetime.fromisoformat(belief["last_updated"])
            days_idle = (now - last).days
            if days_idle <= 0:
                continue  # observed today → no decay

            new_conf = max(0.0, belief["confidence"] - rate * days_idle)
            if new_conf < self.MIN_CONFIDENCE_BEFORE_ARCHIVE:
                self._archive_belief(belief, new_conf)
                archived += 1
            else:
                with self._get_conn() as conn:
                    conn.execute(
                        "UPDATE user_beliefs SET confidence = ? WHERE belief_id = ?",
                        (new_conf, belief["belief_id"]),
                    )
                decayed += 1

        if decayed or archived:
            logger.info(f"Temporal decay: {decayed} decayed, {archived} archived")
        return {"decayed": decayed, "archived": archived}

    def _archive_belief(self, belief: Dict[str, Any], final_confidence: float) -> None:
        now_iso = datetime.now().isoformat()
        with self._get_conn() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO belief_archive
                    (subject, predicate, object_value, final_confidence,
                     context, source, archived_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (belief["subject"], belief["predicate"], belief["object_value"],
                 final_confidence, belief.get("context"), belief.get("source"), now_iso),
            )
            conn.execute(
                "DELETE FROM user_beliefs WHERE belief_id = ?", (belief["belief_id"],)
            )
        logger.info(f"Archived belief: {belief['predicate']}→{belief['object_value']}")

    def get_archived_beliefs(self) -> List[Dict]:
        with self._get_conn() as conn:
            rows = conn.execute(
                "SELECT * FROM belief_archive WHERE subject = ? ORDER BY archived_at DESC",
                (self.subject,),
            ).fetchall()
        return [dict(r) for r in rows]

    def restore_belief(self, predicate: str, object_value: str) -> bool:
        """Restore an archived belief back to the active store at MIN+0.1 confidence."""
        with self._get_conn() as conn:
            row = conn.execute(
                """
                SELECT * FROM belief_archive
                 WHERE subject = ? AND predicate = ? AND object_value = ?
                """,
                (self.subject, predicate, object_value),
            ).fetchone()
            if row is None:
                return False
            conn.execute(
                """
                DELETE FROM belief_archive
                 WHERE subject = ? AND predicate = ? AND object_value = ?
                """,
                (self.subject, predicate, object_value),
            )
        restore_conf = round(self.MIN_CONFIDENCE_BEFORE_ARCHIVE + 0.1, 3)
        self.add_or_update_belief(
            predicate, object_value, source="restored_from_archive",
            initial_confidence=restore_conf,
        )
        logger.info(f"Restored belief from archive: {predicate}→{object_value}")
        return True

    # ------------------------------------------------------------------
    # Fix 5: Contradiction detection
    # ------------------------------------------------------------------

    def _objects_contradict(self, obj_a: str, obj_b: str) -> bool:
        a, b = obj_a.lower(), obj_b.lower()
        if a == b:
            return False
        for x, y in self.CONTRADICTORY_OBJECTS:
            if (x in a and y in b) or (y in a and x in b):
                return True
        return False

    def _are_contradictory(self, a: Dict, b: Dict) -> bool:
        # Same object, opposing predicates (either direction)
        if a["object_value"] == b["object_value"]:
            pa, pb = a["predicate"], b["predicate"]
            if self.CONTRADICTORY_PREDICATES.get(pa) == pb:
                return True
            if self.CONTRADICTORY_PREDICATES.get(pb) == pa:
                return True
        # Same predicate, opposing objects
        if a["predicate"] == b["predicate"]:
            if self._objects_contradict(a["object_value"], b["object_value"]):
                return True
        return False

    def detect_contradictions(self) -> List[Dict[str, Any]]:
        """Find contradictory pairs among existing permanent beliefs."""
        beliefs = self._get_all_beliefs()
        out: List[Dict[str, Any]] = []
        for i, a in enumerate(beliefs):
            for b in beliefs[i + 1:]:
                if self._are_contradictory(a, b):
                    out.append({"belief_a": a, "belief_b": b,
                                "type": "predicate_conflict"})
        return out

    def check_before_write(self, predicate: str, object_value: str) -> Optional[Dict]:
        """Return conflict info if (predicate, object_value) contradicts an
        existing permanent belief, else None."""
        candidate = {"predicate": predicate, "object_value": object_value}
        for existing in self._get_all_beliefs():
            if self._are_contradictory(existing, candidate):
                return {"conflict": True, "existing": existing,
                        "new_predicate": predicate, "new_object": object_value}
        return None

    def _log_contradiction(self, conflict: Dict, predicate: str, object_value: str) -> None:
        ex = conflict["existing"]
        logger.warning(
            "Contradiction blocked: existing "
            f"'{ex['predicate']}→{ex['object_value']}' vs new "
            f"'{predicate}→{object_value}'"
        )

    # ------------------------------------------------------------------
    # Fix 4: outcome-driven reinforcement / weakening
    # ------------------------------------------------------------------

    def _adjust_confidence(self, predicate: str, object_value: str, delta: float) -> Optional[Dict]:
        now = datetime.now().isoformat()
        with self._get_conn() as conn:
            row = conn.execute(
                """
                SELECT belief_id, confidence FROM user_beliefs
                 WHERE subject = ? AND predicate = ? AND object_value = ?
                """,
                (self.subject, predicate, object_value),
            ).fetchone()
            if row is None:
                return None
            new_conf = min(MAX_CONFIDENCE, max(0.0, row["confidence"] + delta))
            conn.execute(
                "UPDATE user_beliefs SET confidence = ?, last_updated = ? WHERE belief_id = ?",
                (new_conf, now, row["belief_id"]),
            )
            belief_id = row["belief_id"]
        return self.get_belief(belief_id)

    def reinforce_belief(self, predicate: str, object_value: str,
                         boost: float = 0.02) -> Optional[Dict]:
        """Nudge a belief's confidence up (e.g. after a positive outcome)."""
        return self._adjust_confidence(predicate, object_value, abs(boost))

    def weaken_belief(self, predicate: str, object_value: str,
                      penalty: float = 0.05) -> Optional[Dict]:
        """Nudge a belief's confidence down (e.g. after a negative outcome)."""
        return self._adjust_confidence(predicate, object_value, -abs(penalty))
