#!/usr/bin/env python3
"""
Personality Milestone Tracker - Phase 3A Week 2
Tracks and celebrates personality learning achievements.
"""

from typing import List, Dict, Optional
from datetime import datetime
import sqlite3


class Milestone:
    """Represents a personality achievement milestone."""

    def __init__(
        self,
        id: str,
        name: str,
        description: str,
        category: str,
        icon: str = "🎯"
    ):
        self.id = id
        self.name = name
        self.description = description
        self.category = category
        self.icon = icon

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "icon": self.icon
        }


class PersonalityMilestoneTracker:
    """
    Tracks personality learning milestones and achievements.

    Celebrates progress to build user trust and engagement.
    """

    def __init__(self, db_path: str = "data/personality.db"):
        self.db_path = db_path
        self._init_database()
        self.milestones = self._define_milestones()

    def _init_database(self):
        """Initialize milestone tracking tables."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Create achievements table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS achievements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                milestone_id TEXT NOT NULL,
                achieved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                metadata TEXT,
                UNIQUE(user_id, milestone_id)
            )
        ''')

        conn.commit()
        conn.close()

    def _define_milestones(self) -> List[Milestone]:
        """Define all available milestones."""
        return [
            # Threshold milestones
            Milestone(
                "threshold_first",
                "First Threshold Crossed!",
                "Your first personality dimension reached 0.65 confidence",
                "threshold",
                "🎯"
            ),
            Milestone(
                "threshold_all",
                "All Systems Go!",
                "All personality dimensions crossed the threshold",
                "threshold",
                "🚀"
            ),

            # Confidence milestones
            Milestone(
                "confidence_75",
                "Confidence Champion",
                "Reached 0.75 confidence on any dimension",
                "confidence",
                "💪"
            ),
            Milestone(
                "confidence_90",
                "Confidence Master",
                "Reached 0.90 confidence - truly personalized!",
                "confidence",
                "👑"
            ),

            # Vocabulary milestones
            Milestone(
                "vocabulary_10",
                "Word Learner",
                "Penny learned 10 of your favorite terms",
                "vocabulary",
                "📚"
            ),
            Milestone(
                "vocabulary_25",
                "Vocabulary Master",
                "Penny learned 25 of your favorite terms",
                "vocabulary",
                "🗣️"
            ),
            Milestone(
                "vocabulary_50",
                "Linguistic Genius",
                "Penny learned 50+ terms - she really gets you!",
                "vocabulary",
                "🧠"
            ),

            # Conversation milestones
            Milestone(
                "conversations_10",
                "Getting Started",
                "Completed 10 conversations",
                "conversation",
                "💬"
            ),
            Milestone(
                "conversations_50",
                "Conversation Master",
                "Completed 50 conversations",
                "conversation",
                "🎤"
            ),
            Milestone(
                "conversations_100",
                "Century Club",
                "Completed 100 conversations - dedication!",
                "conversation",
                "💯"
            ),
            Milestone(
                "conversations_500",
                "Legendary Conversationalist",
                "500 conversations! Penny knows you inside out.",
                "conversation",
                "⭐"
            ),

            # Streak milestones
            Milestone(
                "streak_3",
                "Building Momentum",
                "Used Penny 3 days in a row",
                "streak",
                "🔥"
            ),
            Milestone(
                "streak_7",
                "Week Warrior",
                "7-day streak! Consistent growth.",
                "streak",
                "⚡"
            ),
            Milestone(
                "streak_30",
                "Monthly Master",
                "30-day streak! Penny is part of your routine.",
                "streak",
                "🌟"
            ),
        ]

    def check_milestones(
        self,
        user_id: str = "default",
        personality_state: dict = None
    ) -> List[Milestone]:
        """
        Check which milestones were just achieved.

        Returns list of newly achieved milestones.
        """
        if personality_state is None:
            personality_state = self._get_personality_state(user_id)

        newly_achieved = []

        for milestone in self.milestones:
            # Skip if already achieved
            if self._is_achieved(user_id, milestone.id):
                continue

            # Check if milestone condition is met
            if self._check_milestone_condition(
                user_id,
                milestone,
                personality_state
            ):
                self._record_achievement(user_id, milestone.id)
                newly_achieved.append(milestone)

        return newly_achieved

    def _check_milestone_condition(
        self,
        user_id: str,
        milestone: Milestone,
        personality_state: dict
    ) -> bool:
        """Check if a specific milestone condition is met."""

        # Threshold milestones
        if milestone.id == "threshold_first":
            return self._has_any_threshold_crossed(personality_state)

        if milestone.id == "threshold_all":
            return self._have_all_thresholds_crossed(personality_state)

        # Confidence milestones
        if milestone.id == "confidence_75":
            return self._has_confidence_above(personality_state, 0.75)

        if milestone.id == "confidence_90":
            return self._has_confidence_above(personality_state, 0.90)

        # Vocabulary milestones
        if milestone.id == "vocabulary_10":
            return self._get_vocabulary_count(user_id) >= 10

        if milestone.id == "vocabulary_25":
            return self._get_vocabulary_count(user_id) >= 25

        if milestone.id == "vocabulary_50":
            return self._get_vocabulary_count(user_id) >= 50

        # Conversation milestones
        if milestone.id == "conversations_10":
            return self._get_conversation_count(user_id) >= 10

        if milestone.id == "conversations_50":
            return self._get_conversation_count(user_id) >= 50

        if milestone.id == "conversations_100":
            return self._get_conversation_count(user_id) >= 100

        if milestone.id == "conversations_500":
            return self._get_conversation_count(user_id) >= 500

        # Streak milestones
        if milestone.id == "streak_3":
            return self._get_current_streak(user_id) >= 3

        if milestone.id == "streak_7":
            return self._get_current_streak(user_id) >= 7

        if milestone.id == "streak_30":
            return self._get_current_streak(user_id) >= 30

        return False

    def _has_any_threshold_crossed(self, personality_state: dict) -> bool:
        """Check if any dimension crossed 0.65."""
        for dimension, state in personality_state.items():
            if isinstance(state, dict):
                confidence = state.get("confidence", 0.0)
            else:
                confidence = 0.0

            if confidence >= 0.65:
                return True
        return False

    def _have_all_thresholds_crossed(self, personality_state: dict) -> bool:
        """Check if all main dimensions crossed 0.65."""
        required_dims = [
            "technical_depth_preference",
            "communication_formality",
            "response_length_preference"
        ]

        for dim in required_dims:
            if dim not in personality_state:
                return False

            state = personality_state[dim]
            if isinstance(state, dict):
                confidence = state.get("confidence", 0.0)
            else:
                confidence = 0.0

            if confidence < 0.65:
                return False

        return True

    def _has_confidence_above(
        self,
        personality_state: dict,
        threshold: float
    ) -> bool:
        """Check if any dimension has confidence above threshold."""
        for dimension, state in personality_state.items():
            if isinstance(state, dict):
                confidence = state.get("confidence", 0.0)
            else:
                confidence = 0.0

            if confidence >= threshold:
                return True
        return False

    def _get_vocabulary_count(self, user_id: str) -> int:
        """Get count of learned vocabulary terms."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # This assumes vocabulary tracking exists
        # For now, return estimate based on conversations
        cursor.execute('''
            SELECT COUNT(DISTINCT dimension)
            FROM personality_evolution
            WHERE user_id = ?
        ''', (user_id,))

        result = cursor.fetchone()
        conn.close()

        # Rough estimate: 2-3 terms per dimension
        return (result[0] * 2) if result else 0

    def _get_conversation_count(self, user_id: str) -> int:
        """Get total conversation count."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT COUNT(*)
            FROM conversations
            WHERE user_id = ?
        ''', (user_id,))

        result = cursor.fetchone()
        conn.close()

        return result[0] if result else 0

    def _get_current_streak(self, user_id: str) -> int:
        """Get current consecutive day streak."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Get distinct days with conversations
        cursor.execute('''
            SELECT DISTINCT DATE(timestamp) as conv_date
            FROM conversations
            WHERE user_id = ?
            ORDER BY conv_date DESC
        ''', (user_id,))

        dates = [row[0] for row in cursor.fetchall()]
        conn.close()

        if not dates:
            return 0

        # Count consecutive days from today
        from datetime import date, timedelta

        streak = 0
        check_date = date.today()

        for conv_date_str in dates:
            conv_date = date.fromisoformat(conv_date_str)

            if conv_date == check_date:
                streak += 1
                check_date -= timedelta(days=1)
            elif conv_date < check_date:
                # Gap in streak
                break

        return streak

    def _get_personality_state(self, user_id: str) -> dict:
        """Get current personality state."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT dimension, value, confidence
            FROM personality_evolution
            WHERE user_id = ?
            ORDER BY timestamp DESC
        ''', (user_id,))

        personality_state = {}
        seen_dimensions = set()

        for row in cursor.fetchall():
            dimension, value, confidence = row
            if dimension not in seen_dimensions:
                personality_state[dimension] = {
                    "value": value,
                    "confidence": confidence
                }
                seen_dimensions.add(dimension)

        conn.close()
        return personality_state

    def _is_achieved(self, user_id: str, milestone_id: str) -> bool:
        """Check if milestone already achieved."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT 1 FROM achievements
            WHERE user_id = ? AND milestone_id = ?
        ''', (user_id, milestone_id))

        result = cursor.fetchone()
        conn.close()

        return result is not None

    def _record_achievement(self, user_id: str, milestone_id: str):
        """Record that a milestone was achieved."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT OR IGNORE INTO achievements
            (user_id, milestone_id)
            VALUES (?, ?)
        ''', (user_id, milestone_id))

        conn.commit()
        conn.close()

    def get_achievements(self, user_id: str = "default") -> List[Dict]:
        """Get all achievements for a user."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT milestone_id, achieved_at
            FROM achievements
            WHERE user_id = ?
            ORDER BY achieved_at DESC
        ''', (user_id,))

        achievements = []
        for row in cursor.fetchall():
            milestone_id, achieved_at = row

            # Find milestone details
            milestone = next(
                (m for m in self.milestones if m.id == milestone_id),
                None
            )

            if milestone:
                achievement = milestone.to_dict()
                achievement["achieved_at"] = achieved_at
                achievements.append(achievement)

        conn.close()
        return achievements
