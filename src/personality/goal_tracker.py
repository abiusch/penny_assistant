"""
GoalTracker - Week 12: Goal Continuity.

Tracks in-progress and suspended goals across sessions so Penny
never forgets what the user was working on.

Goal lifecycle:
    detected → active → suspended → completed
                                  → abandoned

Safety: All proactive follow-ups are gated by ProactivityBudget
(MAX_NUDGES_PER_DAY=2, REQUIRE_PERMISSION_AFTER_DAYS=7).
"""

import re
import sqlite3
import uuid
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any, Tuple

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Goal states
# ---------------------------------------------------------------------------

class GoalState:
    ACTIVE    = "active"       # Being worked on this session
    SUSPENDED = "suspended"    # Mentioned but not resolved; may resurface
    COMPLETED = "completed"    # User confirmed done
    ABANDONED = "abandoned"    # Expired or user moved on


# ---------------------------------------------------------------------------
# Goal detection patterns
# ---------------------------------------------------------------------------

# Phrases that signal a new goal / intent
GOAL_START_PATTERNS = [
    r"\b(i('m| am) trying to|i want to|i need to|i('d| would) like to)\b",
    r"\b(help me|can you help|i have to|i must|i should)\b",
    r"\b(working on|building|writing|fixing|setting up|figuring out)\b",
    r"\b(my goal is|my task is|i('m| am) working on)\b",
]

# Phrases that suggest the goal was resolved
COMPLETION_PATTERNS = [
    r"\b(done|finished|complete|completed|solved|fixed|worked|works)\b",
    r"\b(got it working|all good|sorted|sorted it|nailed it)\b",
    r"\b(thanks.{0,20}(that worked|perfect|great)|perfect)\b",
]

# Phrases that suggest the user is abandoning / moving on
ABANDON_PATTERNS = [
    r"\b(forget (it|that)|never mind|nevermind|moving on|let('s| us) drop)\b",
    r"\b(scrap (it|that)|cancel(l?ed)?|don't bother|not worth it)\b",
]

_GOAL_RE    = [re.compile(p, re.IGNORECASE) for p in GOAL_START_PATTERNS]
_DONE_RE    = [re.compile(p, re.IGNORECASE) for p in COMPLETION_PATTERNS]
_ABANDON_RE = [re.compile(p, re.IGNORECASE) for p in ABANDON_PATTERNS]


def _extract_goal_text(user_message: str) -> Optional[str]:
    """
    Try to extract a short goal description from a user message.
    Returns None if no clear goal phrase is found.
    """
    for pattern in _GOAL_RE:
        m = pattern.search(user_message)
        if m:
            # Take the sentence containing the match, cap at 120 chars
            start = max(0, m.start() - 10)
            snippet = user_message[start:start + 120].strip()
            # Remove leading conjunctions
            snippet = re.sub(r'^(and|but|so|ok|okay)[,\s]+', '', snippet, flags=re.IGNORECASE)
            return snippet[:100]
    return None


def _is_completion(text: str) -> bool:
    return any(p.search(text) for p in _DONE_RE)


def _is_abandon(text: str) -> bool:
    return any(p.search(text) for p in _ABANDON_RE)


# ---------------------------------------------------------------------------
# Main class
# ---------------------------------------------------------------------------

class GoalTracker:
    """
    Persist and manage user goals across conversation sessions.

    Key methods:
        process_turn()          — main entry point; call each turn
        get_active_goals()      — list goals needing attention
        get_suspended_goals()   — list goals dormant > N days
        mark_completed()        — mark a goal done
        mark_abandoned()        — mark a goal as dropped
        get_goals_report()      — summary statistics
    """

    # A goal with no activity after this many days becomes suspended
    AUTO_SUSPEND_DAYS = 1

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
                CREATE TABLE IF NOT EXISTS goals (
                    goal_id         TEXT PRIMARY KEY,
                    description     TEXT NOT NULL,
                    state           TEXT NOT NULL DEFAULT 'active',
                    created_at      TIMESTAMP NOT NULL,
                    last_mentioned  TIMESTAMP NOT NULL,
                    completed_at    TIMESTAMP,
                    session_id      TEXT,
                    context_snippet TEXT,
                    mention_count   INTEGER NOT NULL DEFAULT 1
                );

                CREATE TABLE IF NOT EXISTS goal_events (
                    id              INTEGER PRIMARY KEY AUTOINCREMENT,
                    goal_id         TEXT NOT NULL,
                    event_type      TEXT NOT NULL,
                    timestamp       TIMESTAMP NOT NULL,
                    session_id      TEXT,
                    note            TEXT
                );

                CREATE INDEX IF NOT EXISTS idx_goals_state
                    ON goals(state);
                CREATE INDEX IF NOT EXISTS idx_goals_last_mentioned
                    ON goals(last_mentioned);
                CREATE INDEX IF NOT EXISTS idx_goal_events_goal
                    ON goal_events(goal_id);
            """)

    # ------------------------------------------------------------------
    # Core API
    # ------------------------------------------------------------------

    def process_turn(
        self,
        user_message: str,
        session_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Main entry point. Call once per user turn.

        Detects new goals, updates existing ones, auto-suspends stale goals.

        Returns:
            {
              "new_goal": goal dict or None,
              "updated_goals": list of updated goal dicts,
              "suspended_now": list of newly suspended goal dicts,
            }
        """
        result: Dict[str, Any] = {
            "new_goal": None,
            "updated_goals": [],
            "suspended_now": [],
        }

        # 1. Check for completion / abandon signals first
        if _is_completion(user_message):
            updated = self._mark_active_goals_completed(session_id)
            result["updated_goals"].extend(updated)

        elif _is_abandon(user_message):
            updated = self._mark_active_goals_abandoned(session_id)
            result["updated_goals"].extend(updated)

        else:
            # 2. Try to detect a new goal
            goal_text = _extract_goal_text(user_message)
            if goal_text:
                new_goal = self._create_goal(
                    description=goal_text,
                    context_snippet=user_message[:200],
                    session_id=session_id,
                )
                result["new_goal"] = new_goal
            # Note: unrelated messages don't refresh goal timestamps;
            # stale goals should be suspended, not kept alive artificially.

        # 4. Auto-suspend stale active goals
        result["suspended_now"] = self._auto_suspend_stale()

        return result

    def get_active_goals(self) -> List[Dict]:
        """Return all goals currently in 'active' state."""
        with self._get_conn() as conn:
            rows = conn.execute(
                "SELECT * FROM goals WHERE state = ? ORDER BY last_mentioned DESC",
                (GoalState.ACTIVE,),
            ).fetchall()
        return [dict(r) for r in rows]

    def get_suspended_goals(self, min_days_dormant: int = 0) -> List[Dict]:
        """Return suspended goals, optionally filtering by dormancy."""
        cutoff = (datetime.now() - timedelta(days=min_days_dormant)).isoformat()
        with self._get_conn() as conn:
            rows = conn.execute(
                """
                SELECT * FROM goals
                 WHERE state = ?
                   AND last_mentioned <= ?
                 ORDER BY last_mentioned ASC
                """,
                (GoalState.SUSPENDED, cutoff),
            ).fetchall()
        return [dict(r) for r in rows]

    def get_goal(self, goal_id: str) -> Optional[Dict]:
        """Fetch a single goal by ID."""
        with self._get_conn() as conn:
            row = conn.execute(
                "SELECT * FROM goals WHERE goal_id = ?", (goal_id,)
            ).fetchone()
        return dict(row) if row else None

    def mark_completed(
        self,
        goal_id: str,
        session_id: Optional[str] = None,
        note: str = "",
    ) -> bool:
        """Mark a goal as completed. Returns True if found and updated."""
        return self._set_state(
            goal_id, GoalState.COMPLETED,
            completed_at=datetime.now().isoformat(),
            session_id=session_id,
            event_note=note or "marked completed",
        )

    def mark_abandoned(
        self,
        goal_id: str,
        session_id: Optional[str] = None,
        note: str = "",
    ) -> bool:
        """Mark a goal as abandoned. Returns True if found and updated."""
        return self._set_state(
            goal_id, GoalState.ABANDONED,
            session_id=session_id,
            event_note=note or "marked abandoned",
        )

    def mark_suspended(
        self,
        goal_id: str,
        session_id: Optional[str] = None,
        note: str = "",
    ) -> bool:
        """Manually suspend a goal."""
        return self._set_state(
            goal_id, GoalState.SUSPENDED,
            session_id=session_id,
            event_note=note or "manually suspended",
        )

    def update_last_mentioned(self, goal_id: str) -> None:
        """Refresh last_mentioned timestamp and increment mention_count."""
        with self._get_conn() as conn:
            conn.execute(
                """
                UPDATE goals
                   SET last_mentioned = ?,
                       mention_count  = mention_count + 1
                 WHERE goal_id = ?
                """,
                (datetime.now().isoformat(), goal_id),
            )

    def days_since_last_mentioned(self, goal_id: str) -> Optional[float]:
        """Return how many days since a goal was last mentioned, or None."""
        goal = self.get_goal(goal_id)
        if goal is None:
            return None
        last = datetime.fromisoformat(goal["last_mentioned"])
        return (datetime.now() - last).total_seconds() / 86400

    def get_goals_report(self) -> Dict[str, Any]:
        """Return summary statistics."""
        with self._get_conn() as conn:
            totals = conn.execute(
                """
                SELECT
                    COUNT(*)                         AS total,
                    SUM(state = 'active')            AS active,
                    SUM(state = 'suspended')         AS suspended,
                    SUM(state = 'completed')         AS completed,
                    SUM(state = 'abandoned')         AS abandoned
                  FROM goals
                """
            ).fetchone()

            recent = conn.execute(
                """
                SELECT goal_id, description, state, last_mentioned
                  FROM goals
                 ORDER BY last_mentioned DESC
                 LIMIT 5
                """
            ).fetchall()

        return {
            "total":     totals["total"]     or 0,
            "active":    totals["active"]    or 0,
            "suspended": totals["suspended"] or 0,
            "completed": totals["completed"] or 0,
            "abandoned": totals["abandoned"] or 0,
            "recent":    [dict(r) for r in recent],
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _create_goal(
        self,
        description: str,
        context_snippet: str = "",
        session_id: Optional[str] = None,
    ) -> Dict:
        goal_id = f"goal_{uuid.uuid4().hex[:10]}"
        now = datetime.now().isoformat()
        goal = {
            "goal_id": goal_id,
            "description": description,
            "state": GoalState.ACTIVE,
            "created_at": now,
            "last_mentioned": now,
            "completed_at": None,
            "session_id": session_id,
            "context_snippet": context_snippet,
            "mention_count": 1,
        }
        with self._get_conn() as conn:
            conn.execute(
                """
                INSERT INTO goals
                    (goal_id, description, state, created_at, last_mentioned,
                     session_id, context_snippet, mention_count)
                VALUES (?, ?, ?, ?, ?, ?, ?, 1)
                """,
                (
                    goal_id, description, GoalState.ACTIVE, now, now,
                    session_id, context_snippet,
                ),
            )
            self._log_event(conn, goal_id, "created", session_id, "goal detected")
        logger.info(f"📌 New goal tracked: {description[:60]}")
        return goal

    def _set_state(
        self,
        goal_id: str,
        state: str,
        completed_at: Optional[str] = None,
        session_id: Optional[str] = None,
        event_note: str = "",
    ) -> bool:
        with self._get_conn() as conn:
            existing = conn.execute(
                "SELECT goal_id FROM goals WHERE goal_id = ?", (goal_id,)
            ).fetchone()
            if not existing:
                return False
            if completed_at:
                conn.execute(
                    "UPDATE goals SET state = ?, completed_at = ? WHERE goal_id = ?",
                    (state, completed_at, goal_id),
                )
            else:
                conn.execute(
                    "UPDATE goals SET state = ? WHERE goal_id = ?",
                    (state, goal_id),
                )
            self._log_event(conn, goal_id, f"state→{state}", session_id, event_note)
        return True

    def _mark_active_goals_completed(self, session_id: Optional[str]) -> List[Dict]:
        active = self.get_active_goals()
        updated = []
        for g in active:
            self.mark_completed(g["goal_id"], session_id, "completion signal detected")
            g["state"] = GoalState.COMPLETED
            updated.append(g)
        return updated

    def _mark_active_goals_abandoned(self, session_id: Optional[str]) -> List[Dict]:
        active = self.get_active_goals()
        updated = []
        for g in active:
            self.mark_abandoned(g["goal_id"], session_id, "abandon signal detected")
            g["state"] = GoalState.ABANDONED
            updated.append(g)
        return updated

    def _touch_active_goals(self, session_id: Optional[str]) -> None:
        """Update last_mentioned for all active goals (user still in context)."""
        now = datetime.now().isoformat()
        with self._get_conn() as conn:
            conn.execute(
                "UPDATE goals SET last_mentioned = ? WHERE state = ?",
                (now, GoalState.ACTIVE),
            )

    def _auto_suspend_stale(self) -> List[Dict]:
        """
        Move active goals that haven't been mentioned in AUTO_SUSPEND_DAYS
        to 'suspended'. Called at the end of each process_turn().
        """
        cutoff = (
            datetime.now() - timedelta(days=self.AUTO_SUSPEND_DAYS)
        ).isoformat()
        with self._get_conn() as conn:
            stale = conn.execute(
                """
                SELECT * FROM goals
                 WHERE state = ? AND last_mentioned < ?
                """,
                (GoalState.ACTIVE, cutoff),
            ).fetchall()
            stale_list = [dict(r) for r in stale]
            for g in stale_list:
                conn.execute(
                    "UPDATE goals SET state = ? WHERE goal_id = ?",
                    (GoalState.SUSPENDED, g["goal_id"]),
                )
                self._log_event(conn, g["goal_id"], "state→suspended",
                                None, "auto-suspended: stale")
        return stale_list

    def _log_event(
        self,
        conn: sqlite3.Connection,
        goal_id: str,
        event_type: str,
        session_id: Optional[str],
        note: str,
    ) -> None:
        conn.execute(
            """
            INSERT INTO goal_events (goal_id, event_type, timestamp, session_id, note)
            VALUES (?, ?, ?, ?, ?)
            """,
            (goal_id, event_type, datetime.now().isoformat(), session_id, note),
        )
