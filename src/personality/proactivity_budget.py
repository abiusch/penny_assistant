"""
ProactivityBudget - Week 11 Safety Feature.

Prevents "helpful-stalker bot" syndrome from 2026 AI failure modes.

Hard limits (NOT configurable by end-users):
  MAX_NUDGES_PER_DAY           = 2
  MAX_GOAL_RESURRECTIONS_WEEK  = 1
  DORMANT_THRESHOLD_DAYS       = 14
  REQUIRE_PERMISSION_AFTER_DAYS= 7
  MIN_CONFIDENCE_FOR_PROACTIVE = 0.8

These constants are module-level to make them visible and hard to bypass.
"""

import sqlite3
import logging
from datetime import datetime, timedelta, date
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Hard limits — intentionally NOT configurable (Risk 2: Runaway Autonomy)
# ---------------------------------------------------------------------------

MAX_NUDGES_PER_DAY            = 2       # Max proactive mentions per calendar day
MAX_GOAL_RESURRECTIONS_WEEK   = 1       # Max goal resurrections per ISO week
DORMANT_THRESHOLD_DAYS        = 14      # A goal is "dormant" after this many days
REQUIRE_PERMISSION_AFTER_DAYS = 7       # Must ask permission if goal is >7 days old
MIN_CONFIDENCE_FOR_PROACTIVE  = 0.80    # Minimum confidence to nudge unprompted


class ProactivityBudget:
    """
    Enforces daily/weekly proactive-behaviour limits.

    Usage:
        budget = ProactivityBudget(db_path="data/personality_tracking.db")

        # Before nudging about a goal:
        allowed, reason = budget.can_nudge_about_goal(
            goal_id="project_x", last_mentioned=last_mention_date, confidence=0.85
        )
        if not allowed:
            # Skip or ask permission
            msg = budget.request_permission_for_goal(goal_id, goal_description)

        # After nudging:
        budget.record_nudge(goal_id=goal_id, session_id=session_id)
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
                CREATE TABLE IF NOT EXISTS proactive_nudges (
                    id              INTEGER PRIMARY KEY AUTOINCREMENT,
                    goal_id         TEXT NOT NULL,
                    nudge_date      DATE NOT NULL,
                    nudge_time      TIMESTAMP NOT NULL,
                    session_id      TEXT,
                    confidence      REAL,
                    permission_given INTEGER NOT NULL DEFAULT 0
                );

                CREATE TABLE IF NOT EXISTS goal_resurrections (
                    id              INTEGER PRIMARY KEY AUTOINCREMENT,
                    goal_id         TEXT NOT NULL,
                    resurrection_date DATE NOT NULL,
                    resurrection_time TIMESTAMP NOT NULL,
                    iso_week        TEXT NOT NULL,
                    session_id      TEXT,
                    user_approved   INTEGER NOT NULL DEFAULT 0,
                    goal_description TEXT
                );

                CREATE INDEX IF NOT EXISTS idx_nudges_date
                    ON proactive_nudges(nudge_date);
                CREATE INDEX IF NOT EXISTS idx_nudges_goal
                    ON proactive_nudges(goal_id, nudge_date);
                CREATE INDEX IF NOT EXISTS idx_resurrections_week
                    ON goal_resurrections(iso_week);
            """)

    # ------------------------------------------------------------------
    # Core API
    # ------------------------------------------------------------------

    def can_nudge_about_goal(
        self,
        goal_id: str,
        last_mentioned: Optional[datetime] = None,
        confidence: float = 1.0,
    ) -> tuple[bool, str]:
        """
        Check all safety conditions before a proactive nudge.

        Returns:
            (allowed: bool, reason: str)
        """
        # 1. Confidence threshold
        if confidence < MIN_CONFIDENCE_FOR_PROACTIVE:
            return (
                False,
                f"Confidence {confidence:.2f} below minimum {MIN_CONFIDENCE_FOR_PROACTIVE}",
            )

        # 2. Daily nudge limit
        today_count = self._nudges_today()
        if today_count >= MAX_NUDGES_PER_DAY:
            return (
                False,
                f"Daily nudge limit reached ({today_count}/{MAX_NUDGES_PER_DAY})",
            )

        # 3. Permission required for dormant goals
        if last_mentioned is not None:
            days_dormant = (datetime.now() - last_mentioned).days
            if days_dormant >= REQUIRE_PERMISSION_AFTER_DAYS:
                return (
                    False,
                    f"Goal dormant {days_dormant} days — permission required "
                    f"(threshold: {REQUIRE_PERMISSION_AFTER_DAYS} days)",
                )

        return True, "OK"

    def can_resurrect_goal(
        self,
        goal_id: str,
        last_mentioned: Optional[datetime] = None,
    ) -> tuple[bool, str]:
        """
        Check if a dormant goal can be resurrected this week.

        Returns:
            (allowed: bool, reason: str)
        """
        # Weekly resurrection limit
        week_count = self._resurrections_this_week()
        if week_count >= MAX_GOAL_RESURRECTIONS_WEEK:
            return (
                False,
                f"Weekly resurrection limit reached "
                f"({week_count}/{MAX_GOAL_RESURRECTIONS_WEEK})",
            )

        # Goal must actually be dormant
        if last_mentioned is not None:
            days_dormant = (datetime.now() - last_mentioned).days
            if days_dormant < DORMANT_THRESHOLD_DAYS:
                return (
                    False,
                    f"Goal not dormant yet ({days_dormant} days, "
                    f"threshold: {DORMANT_THRESHOLD_DAYS} days)",
                )

        return True, "OK"

    def request_permission_for_goal(
        self,
        goal_id: str,
        goal_description: str,
        days_dormant: Optional[int] = None,
    ) -> str:
        """
        Generate a permission-request message in Penny's voice.

        Returns a message Penny can send to ask the user if they
        still want to be reminded about the goal.
        """
        if days_dormant and days_dormant >= DORMANT_THRESHOLD_DAYS:
            age_str = f"about {days_dormant // 7} week{'s' if days_dormant >= 14 else ''} ago"
            return (
                f"Hey, you mentioned '{goal_description}' {age_str}. "
                f"Still want me to keep track of that, or are we moving on?"
            )
        elif days_dormant:
            return (
                f"Quick check — do you still want me to follow up on "
                f"'{goal_description}'? It's been {days_dormant} days."
            )
        else:
            return (
                f"Want me to keep following up on '{goal_description}'? "
                f"Just say yes and I'll keep it on my radar."
            )

    def record_nudge(
        self,
        goal_id: str,
        session_id: Optional[str] = None,
        confidence: float = 1.0,
        permission_given: bool = False,
    ) -> None:
        """Record a proactive nudge against the daily budget."""
        now = datetime.now()
        with self._get_conn() as conn:
            conn.execute(
                """
                INSERT INTO proactive_nudges
                    (goal_id, nudge_date, nudge_time, session_id,
                     confidence, permission_given)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    goal_id,
                    now.date().isoformat(),
                    now.isoformat(),
                    session_id,
                    confidence,
                    1 if permission_given else 0,
                ),
            )

    def record_resurrection(
        self,
        goal_id: str,
        goal_description: str = "",
        session_id: Optional[str] = None,
        user_approved: bool = False,
    ) -> None:
        """Record a goal resurrection against the weekly budget."""
        now = datetime.now()
        iso_week = f"{now.isocalendar()[0]}-W{now.isocalendar()[1]:02d}"
        with self._get_conn() as conn:
            conn.execute(
                """
                INSERT INTO goal_resurrections
                    (goal_id, resurrection_date, resurrection_time,
                     iso_week, session_id, user_approved, goal_description)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    goal_id,
                    now.date().isoformat(),
                    now.isoformat(),
                    iso_week,
                    session_id,
                    1 if user_approved else 0,
                    goal_description,
                ),
            )

    def get_budget_summary(self) -> Dict[str, Any]:
        """
        Show current budget usage.

        Returns:
            nudges_today, nudges_remaining_today,
            resurrections_this_week, resurrections_remaining_week,
            limits (hard limit values)
        """
        nudges_today      = self._nudges_today()
        resurrections_week = self._resurrections_this_week()

        return {
            "nudges_today":               nudges_today,
            "nudges_remaining_today":     max(0, MAX_NUDGES_PER_DAY - nudges_today),
            "resurrections_this_week":    resurrections_week,
            "resurrections_remaining_week": max(
                0, MAX_GOAL_RESURRECTIONS_WEEK - resurrections_week
            ),
            "limits": {
                "max_nudges_per_day":              MAX_NUDGES_PER_DAY,
                "max_resurrections_per_week":      MAX_GOAL_RESURRECTIONS_WEEK,
                "dormant_threshold_days":          DORMANT_THRESHOLD_DAYS,
                "require_permission_after_days":   REQUIRE_PERMISSION_AFTER_DAYS,
                "min_confidence_for_proactive":    MIN_CONFIDENCE_FOR_PROACTIVE,
            },
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _nudges_today(self) -> int:
        today = date.today().isoformat()
        with self._get_conn() as conn:
            row = conn.execute(
                "SELECT COUNT(*) AS cnt FROM proactive_nudges WHERE nudge_date = ?",
                (today,),
            ).fetchone()
        return row["cnt"] if row else 0

    def _resurrections_this_week(self) -> int:
        now = datetime.now()
        iso_week = f"{now.isocalendar()[0]}-W{now.isocalendar()[1]:02d}"
        with self._get_conn() as conn:
            row = conn.execute(
                "SELECT COUNT(*) AS cnt FROM goal_resurrections WHERE iso_week = ?",
                (iso_week,),
            ).fetchone()
        return row["cnt"] if row else 0
