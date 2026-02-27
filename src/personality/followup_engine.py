"""
FollowUpEngine - Week 12: Goal Continuity.

Decides WHEN and HOW to follow up on suspended goals.
Always uses ProactivityBudget before sending a follow-up —
never nudges without checking the safety limits first.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any, Tuple

from src.personality.goal_tracker import GoalTracker, GoalState
from src.personality.proactivity_budget import (
    ProactivityBudget,
    DORMANT_THRESHOLD_DAYS,
    REQUIRE_PERMISSION_AFTER_DAYS,
    MIN_CONFIDENCE_FOR_PROACTIVE,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Follow-up message templates (in Penny's voice)
# ---------------------------------------------------------------------------

# Goal is suspended, user mentioned it < REQUIRE_PERMISSION_AFTER_DAYS ago
SOFT_NUDGE_TEMPLATES = [
    "Hey, still working on {description}?",
    "Any progress on {description}?",
    "Just checking—{description}—still on the radar?",
    "Quick one: {description}—where'd that land?",
]

# Goal needs permission (dormant > REQUIRE_PERMISSION_AFTER_DAYS)
# These are generated via ProactivityBudget.request_permission_for_goal()

# Goal is close to being auto-abandoned (very old)
LAST_CHANCE_TEMPLATES = [
    "Last chance to revive this one: {description}. Still relevant?",
    "Been a while on {description}—want me to keep tracking it or drop it?",
    "I'm about to mark '{description}' as done-for. Say the word if you want to keep it.",
]


def _pick_template(templates: List[str], index: int, description: str) -> str:
    tmpl = templates[index % len(templates)]
    return tmpl.format(description=description)


# ---------------------------------------------------------------------------
# Main class
# ---------------------------------------------------------------------------

class FollowUpEngine:
    """
    Generates timely, safe follow-up prompts for suspended goals.

    Safety contract:
        Every follow-up goes through ProactivityBudget.can_nudge_about_goal().
        If the budget says no, no follow-up is generated — period.
    """

    # Goals older than this get a "last chance" message
    LAST_CHANCE_DAYS = DORMANT_THRESHOLD_DAYS - 2  # 12 days by default

    def __init__(
        self,
        goal_tracker: GoalTracker,
        proactivity_budget: ProactivityBudget,
        confidence: float = MIN_CONFIDENCE_FOR_PROACTIVE,
    ):
        self.goals = goal_tracker
        self.budget = proactivity_budget
        self.confidence = confidence

    # ------------------------------------------------------------------
    # Core API
    # ------------------------------------------------------------------

    def get_followups_for_session(
        self,
        session_id: Optional[str] = None,
        max_followups: int = 1,
    ) -> List[Dict[str, Any]]:
        """
        Generate follow-up prompts for suspended goals at session start.

        Respects ProactivityBudget. Returns at most `max_followups` items
        (default 1 to avoid overwhelming the user).

        Returns list of dicts:
            {
              "goal_id": str,
              "message": str,          # follow-up prompt in Penny's voice
              "type": str,             # "soft_nudge" | "permission_request" | "last_chance"
              "days_dormant": float,
            }
        """
        suspended = self.goals.get_suspended_goals()
        followups: List[Dict[str, Any]] = []

        for goal in suspended:
            if len(followups) >= max_followups:
                break

            last_mentioned = datetime.fromisoformat(goal["last_mentioned"])
            days_dormant = (datetime.now() - last_mentioned).days

            # Budget check
            allowed, reason = self.budget.can_nudge_about_goal(
                goal_id=goal["goal_id"],
                last_mentioned=last_mentioned,
                confidence=self.confidence,
            )

            if not allowed:
                logger.debug(f"Follow-up blocked for {goal['goal_id']}: {reason}")
                continue

            # Choose message type
            if days_dormant >= self.LAST_CHANCE_DAYS:
                msg_type = "last_chance"
                idx = len(followups)
                message = _pick_template(LAST_CHANCE_TEMPLATES, idx, goal["description"])
            elif days_dormant >= REQUIRE_PERMISSION_AFTER_DAYS:
                # This path won't usually be reached because ProactivityBudget
                # blocks nudges after REQUIRE_PERMISSION_AFTER_DAYS without
                # permission — but included for completeness
                msg_type = "permission_request"
                message = self.budget.request_permission_for_goal(
                    goal["goal_id"],
                    goal["description"],
                    days_dormant=days_dormant,
                )
            else:
                msg_type = "soft_nudge"
                idx = len(followups)
                message = _pick_template(SOFT_NUDGE_TEMPLATES, idx, goal["description"])

            followups.append({
                "goal_id":     goal["goal_id"],
                "message":     message,
                "type":        msg_type,
                "days_dormant": days_dormant,
                "description": goal["description"],
            })

            # Record nudge against budget
            self.budget.record_nudge(
                goal_id=goal["goal_id"],
                session_id=session_id,
                confidence=self.confidence,
            )
            logger.info(
                f"📬 Follow-up generated ({msg_type}): {goal['description'][:50]}"
            )

        return followups

    def needs_permission(self, goal_id: str) -> Tuple[bool, Optional[str]]:
        """
        Check if Penny needs to ask permission before mentioning goal_id.

        Returns:
            (needs_permission: bool, message: str or None)
        """
        goal = self.goals.get_goal(goal_id)
        if goal is None:
            return False, None

        last_mentioned = datetime.fromisoformat(goal["last_mentioned"])
        days_dormant = (datetime.now() - last_mentioned).days

        if days_dormant >= REQUIRE_PERMISSION_AFTER_DAYS:
            msg = self.budget.request_permission_for_goal(
                goal_id,
                goal["description"],
                days_dormant=days_dormant,
            )
            return True, msg

        return False, None

    def can_follow_up(self, goal_id: str) -> Tuple[bool, str]:
        """
        Quick check: can we follow up on this specific goal right now?

        Returns (allowed, reason).
        """
        goal = self.goals.get_goal(goal_id)
        if goal is None:
            return False, "Goal not found"

        last_mentioned = datetime.fromisoformat(goal["last_mentioned"])
        return self.budget.can_nudge_about_goal(
            goal_id=goal_id,
            last_mentioned=last_mentioned,
            confidence=self.confidence,
        )

    def generate_soft_nudge(self, goal_id: str) -> Optional[str]:
        """
        Generate a single soft nudge for a specific goal (no budget check —
        caller must call can_follow_up() first).
        """
        goal = self.goals.get_goal(goal_id)
        if goal is None:
            return None
        return _pick_template(SOFT_NUDGE_TEMPLATES, 0, goal["description"])

    def get_followup_summary(self) -> Dict[str, Any]:
        """
        Overview of follow-up status: pending suspended goals + budget state.
        """
        suspended = self.goals.get_suspended_goals()
        budget_summary = self.budget.get_budget_summary()

        followable = []
        blocked = []

        for g in suspended:
            last = datetime.fromisoformat(g["last_mentioned"])
            allowed, reason = self.budget.can_nudge_about_goal(
                goal_id=g["goal_id"],
                last_mentioned=last,
                confidence=self.confidence,
            )
            entry = {
                "goal_id": g["goal_id"],
                "description": g["description"],
                "days_dormant": (datetime.now() - last).days,
            }
            if allowed:
                followable.append(entry)
            else:
                entry["blocked_reason"] = reason
                blocked.append(entry)

        return {
            "suspended_goals":   len(suspended),
            "followable_now":    len(followable),
            "blocked":           len(blocked),
            "followable_goals":  followable,
            "blocked_goals":     blocked,
            "budget":            budget_summary,
        }
