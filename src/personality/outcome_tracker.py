"""
OutcomeTracker - Week 11: Track response effectiveness over time.

Learns which response strategies work well in which contexts
by detecting user reactions and recording outcome data.
"""

import sqlite3
import logging
import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Tuple, Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Reaction detection patterns
# ---------------------------------------------------------------------------

POSITIVE_SIGNALS = [
    "thanks", "thank you", "thx", "ty", "perfect", "great", "awesome",
    "exactly", "worked", "works", "fixed", "solved", "yes", "yep", "yup",
    "nice", "love it", "good", "correct", "right", "helpful", "brilliant",
    "makes sense", "got it", "that's it", "👍", "🙌", "✅", "💯",
]

NEGATIVE_SIGNALS = [
    "didn't work", "doesn't work", "not working", "wrong", "incorrect",
    "that's wrong", "no", "nope", "not helpful", "unhelpful", "confusing",
    "too much", "too long", "not what i", "that's not", "nevermind",
    "forget it", "never mind", "that doesn't", "still broken", "still not",
    "still wrong", "👎", "❌",
]

# ---------------------------------------------------------------------------
# Response type classification
# ---------------------------------------------------------------------------

def classify_response_type(response: str) -> str:
    """Classify response into a type string based on content."""
    if "```" in response:
        return "code_example"
    length = len(response.strip())
    if length > 500:
        return "detailed_explanation"
    if length < 100:
        return "brief_answer"
    return "conversational"


# ---------------------------------------------------------------------------
# Main class
# ---------------------------------------------------------------------------

class OutcomeTracker:
    """
    Tracks response effectiveness for adaptive strategy selection.

    Architecture:
        - observe_outcome()       → Record one outcome observation
        - detect_user_reaction()  → Auto-detect +/-/neutral from user text
        - get_strategy_success_rate()  → Rolling success % per strategy
        - suggest_best_strategy()      → Recommend based on history
        - get_outcome_report()         → Statistics overview
    """

    def __init__(self, db_path: str = "data/personality_tracking.db"):
        self.db_path = db_path
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
                CREATE TABLE IF NOT EXISTS outcome_observations (
                    response_id     TEXT PRIMARY KEY,
                    timestamp       TIMESTAMP NOT NULL,
                    response_type   TEXT NOT NULL,
                    context_type    TEXT NOT NULL DEFAULT 'general',
                    strategy        TEXT NOT NULL DEFAULT 'default',
                    reaction        TEXT NOT NULL DEFAULT 'neutral',
                    confidence      REAL NOT NULL DEFAULT 1.0,
                    user_message    TEXT,
                    assistant_response TEXT,
                    session_id      TEXT
                );

                CREATE TABLE IF NOT EXISTS strategy_success_rates (
                    strategy        TEXT NOT NULL,
                    context_type    TEXT NOT NULL DEFAULT 'general',
                    positive_count  INTEGER NOT NULL DEFAULT 0,
                    negative_count  INTEGER NOT NULL DEFAULT 0,
                    neutral_count   INTEGER NOT NULL DEFAULT 0,
                    last_updated    TIMESTAMP NOT NULL,
                    PRIMARY KEY (strategy, context_type)
                );

                CREATE TABLE IF NOT EXISTS user_reaction_patterns (
                    id              INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp       TIMESTAMP NOT NULL,
                    user_text       TEXT NOT NULL,
                    reaction        TEXT NOT NULL,
                    prior_response_id TEXT,
                    session_id      TEXT
                );

                CREATE INDEX IF NOT EXISTS idx_outcome_strategy
                    ON outcome_observations(strategy, context_type);
                CREATE INDEX IF NOT EXISTS idx_outcome_timestamp
                    ON outcome_observations(timestamp);
                CREATE INDEX IF NOT EXISTS idx_outcome_reaction
                    ON outcome_observations(reaction);
            """)

    # ------------------------------------------------------------------
    # Core API
    # ------------------------------------------------------------------

    def observe_outcome(
        self,
        response_id: str,
        response_type: str,
        reaction: str,
        context_type: str = "general",
        strategy: str = "default",
        confidence: float = 1.0,
        user_message: Optional[str] = None,
        assistant_response: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> None:
        """
        Record a single outcome observation.

        Args:
            response_id:        Unique ID for the response being assessed
            response_type:      'brief_answer' | 'detailed_explanation' |
                                'code_example' | 'conversational'
            reaction:           'positive' | 'negative' | 'neutral'
            context_type:       e.g. 'technical', 'casual_chat', 'general'
            strategy:           Strategy name used to generate the response
            confidence:         How confident the reaction detection is (0-1)
            user_message:       Original user message (optional, for logging)
            assistant_response: Response text (optional, for logging)
            session_id:         Session identifier (optional)
        """
        if reaction not in ("positive", "negative", "neutral"):
            raise ValueError(f"reaction must be positive/negative/neutral, got: {reaction}")

        with self._get_conn() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO outcome_observations
                    (response_id, timestamp, response_type, context_type,
                     strategy, reaction, confidence, user_message,
                     assistant_response, session_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    response_id,
                    datetime.now().isoformat(),
                    response_type,
                    context_type,
                    strategy,
                    reaction,
                    confidence,
                    user_message,
                    assistant_response,
                    session_id,
                ),
            )

            # Update aggregated rates
            self._update_success_rate(conn, strategy, context_type, reaction)

    def detect_user_reaction(
        self,
        user_text: str,
        prior_response_id: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> Tuple[str, float]:
        """
        Detect reaction from user follow-up text.

        Returns:
            (reaction, confidence) — reaction is 'positive' | 'negative' | 'neutral'
        """
        text_lower = user_text.lower()

        pos_hits = sum(1 for s in POSITIVE_SIGNALS if s in text_lower)
        neg_hits = sum(1 for s in NEGATIVE_SIGNALS if s in text_lower)

        if pos_hits > 0 and neg_hits == 0:
            reaction, confidence = "positive", min(0.6 + pos_hits * 0.1, 1.0)
        elif neg_hits > 0 and pos_hits == 0:
            reaction, confidence = "negative", min(0.6 + neg_hits * 0.1, 1.0)
        elif neg_hits > pos_hits:
            reaction, confidence = "negative", 0.55
        elif pos_hits > neg_hits:
            reaction, confidence = "positive", 0.55
        else:
            reaction, confidence = "neutral", 1.0

        # Log the detection
        with self._get_conn() as conn:
            conn.execute(
                """
                INSERT INTO user_reaction_patterns
                    (timestamp, user_text, reaction, prior_response_id, session_id)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    datetime.now().isoformat(),
                    user_text[:500],
                    reaction,
                    prior_response_id,
                    session_id,
                ),
            )

        return reaction, confidence

    def get_strategy_success_rate(
        self,
        strategy: str,
        context_type: str = "general",
    ) -> float:
        """
        Return success rate (0.0–1.0) for a strategy in a context.

        Calculated as: positive / (positive + negative)
        Neutral reactions are excluded.
        Returns 0.5 (neutral prior) when no data.
        """
        with self._get_conn() as conn:
            row = conn.execute(
                """
                SELECT positive_count, negative_count
                  FROM strategy_success_rates
                 WHERE strategy = ? AND context_type = ?
                """,
                (strategy, context_type),
            ).fetchone()

        if row is None:
            return 0.5  # No data → neutral prior

        pos = row["positive_count"]
        neg = row["negative_count"]
        total = pos + neg
        if total == 0:
            return 0.5

        return pos / total

    def suggest_best_strategy(
        self,
        context_type: str = "general",
        candidates: Optional[List[str]] = None,
    ) -> Optional[str]:
        """
        Suggest the best strategy for a context based on outcome history.

        Args:
            context_type: Context to optimise for
            candidates:   List of strategy names to consider.
                         If None, uses all known strategies for context.

        Returns:
            Best strategy name, or None if no data.
        """
        with self._get_conn() as conn:
            if candidates:
                placeholders = ",".join("?" * len(candidates))
                rows = conn.execute(
                    f"""
                    SELECT strategy, positive_count, negative_count
                      FROM strategy_success_rates
                     WHERE context_type = ?
                       AND strategy IN ({placeholders})
                     ORDER BY
                         CAST(positive_count AS FLOAT) /
                         (positive_count + negative_count + 1) DESC
                    """,
                    [context_type] + list(candidates),
                ).fetchall()
            else:
                rows = conn.execute(
                    """
                    SELECT strategy, positive_count, negative_count
                      FROM strategy_success_rates
                     WHERE context_type = ?
                     ORDER BY
                         CAST(positive_count AS FLOAT) /
                         (positive_count + negative_count + 1) DESC
                    """,
                    (context_type,),
                ).fetchall()

        if not rows:
            return None

        best = rows[0]
        pos = best["positive_count"]
        neg = best["negative_count"]
        # Only suggest if there's actual positive evidence
        if pos + neg < 2:
            return None

        return best["strategy"]

    def get_outcome_report(self) -> Dict[str, Any]:
        """
        Generate a summary statistics report.

        Returns dict with:
            total_observations, positive_count, negative_count,
            neutral_count, overall_success_rate, strategies (list),
            recent_trend (last 10 reactions)
        """
        with self._get_conn() as conn:
            totals = conn.execute(
                """
                SELECT
                    COUNT(*)                                       AS total,
                    SUM(reaction = 'positive')                     AS positive,
                    SUM(reaction = 'negative')                     AS negative,
                    SUM(reaction = 'neutral')                      AS neutral
                  FROM outcome_observations
                """
            ).fetchone()

            strategies = conn.execute(
                """
                SELECT
                    strategy,
                    context_type,
                    positive_count,
                    negative_count,
                    neutral_count,
                    last_updated
                  FROM strategy_success_rates
                 ORDER BY last_updated DESC
                 LIMIT 20
                """
            ).fetchall()

            recent = conn.execute(
                """
                SELECT reaction
                  FROM outcome_observations
                 ORDER BY timestamp DESC
                 LIMIT 10
                """
            ).fetchall()

        total = totals["total"] or 0
        pos   = totals["positive"] or 0
        neg   = totals["negative"] or 0
        neu   = totals["neutral"] or 0
        denominator = pos + neg
        success_rate = (pos / denominator) if denominator > 0 else 0.5

        return {
            "total_observations": total,
            "positive_count": pos,
            "negative_count": neg,
            "neutral_count": neu,
            "overall_success_rate": round(success_rate, 3),
            "strategies": [
                {
                    "strategy": r["strategy"],
                    "context_type": r["context_type"],
                    "positive": r["positive_count"],
                    "negative": r["negative_count"],
                    "neutral": r["neutral_count"],
                    "success_rate": round(
                        r["positive_count"]
                        / max(r["positive_count"] + r["negative_count"], 1),
                        3,
                    ),
                    "last_updated": r["last_updated"],
                }
                for r in strategies
            ],
            "recent_trend": [r["reaction"] for r in recent],
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _update_success_rate(
        self,
        conn: sqlite3.Connection,
        strategy: str,
        context_type: str,
        reaction: str,
    ) -> None:
        """Upsert the aggregated success-rate row for strategy+context."""
        now = datetime.now().isoformat()

        existing = conn.execute(
            "SELECT * FROM strategy_success_rates WHERE strategy=? AND context_type=?",
            (strategy, context_type),
        ).fetchone()

        if existing is None:
            pos = 1 if reaction == "positive" else 0
            neg = 1 if reaction == "negative" else 0
            neu = 1 if reaction == "neutral" else 0
            conn.execute(
                """
                INSERT INTO strategy_success_rates
                    (strategy, context_type, positive_count, negative_count,
                     neutral_count, last_updated)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (strategy, context_type, pos, neg, neu, now),
            )
        else:
            col = {"positive": "positive_count",
                   "negative": "negative_count",
                   "neutral":  "neutral_count"}[reaction]
            conn.execute(
                f"""
                UPDATE strategy_success_rates
                   SET {col} = {col} + 1,
                       last_updated = ?
                 WHERE strategy = ? AND context_type = ?
                """,
                (now, strategy, context_type),
            )

    @staticmethod
    def generate_response_id() -> str:
        """Generate a unique response ID."""
        return f"resp_{uuid.uuid4().hex[:12]}"
