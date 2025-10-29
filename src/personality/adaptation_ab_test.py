#!/usr/bin/env python3
"""
Adaptation A/B Testing Framework - Phase 3A Week 2
Tests effectiveness of personality adaptation vs baseline.
"""

import random
import sqlite3
import json
from typing import Dict, Optional, Literal
from datetime import datetime
from dataclasses import dataclass, asdict


@dataclass
class ABTestMetrics:
    """Metrics collected for A/B test analysis."""
    conversation_id: str
    user_id: str
    group: Literal["control", "treatment"]
    timestamp: str

    # Engagement metrics
    conversation_length_seconds: float
    message_count: int
    user_message_length_avg: int

    # Quality metrics
    user_corrections: int
    follow_up_questions: int
    positive_indicators: int  # thanks, great, helpful, etc.
    negative_indicators: int  # confused, wrong, not helpful, etc.

    # Satisfaction (optional, explicit feedback)
    satisfaction_rating: Optional[int] = None  # 1-10 if provided

    def to_dict(self) -> dict:
        return asdict(self)


class AdaptationABTest:
    """
    A/B testing framework for personality adaptation.

    Randomly assigns conversations to control or treatment groups
    and tracks metrics to measure adaptation effectiveness.
    """

    def __init__(
        self,
        db_path: str = "data/personality.db",
        treatment_probability: float = 0.5
    ):
        """
        Initialize A/B test framework.

        Args:
            db_path: Path to database
            treatment_probability: Probability of treatment assignment (0.5 = 50/50)
        """
        self.db_path = db_path
        self.treatment_probability = treatment_probability
        self._init_database()

    def _init_database(self):
        """Initialize A/B testing tables."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # A/B test assignments
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ab_test_assignments (
                conversation_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                group_assignment TEXT NOT NULL,
                assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # A/B test metrics
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ab_test_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                group_assignment TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                -- Engagement metrics
                conversation_length_seconds REAL,
                message_count INTEGER,
                user_message_length_avg INTEGER,

                -- Quality metrics
                user_corrections INTEGER,
                follow_up_questions INTEGER,
                positive_indicators INTEGER,
                negative_indicators INTEGER,

                -- Satisfaction
                satisfaction_rating INTEGER,

                FOREIGN KEY (conversation_id) REFERENCES ab_test_assignments(conversation_id)
            )
        ''')

        # Create indexes
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_ab_metrics_group
            ON ab_test_metrics(group_assignment)
        ''')

        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_ab_metrics_user
            ON ab_test_metrics(user_id)
        ''')

        conn.commit()
        conn.close()

    def assign_group(
        self,
        conversation_id: str,
        user_id: str = "default"
    ) -> Literal["control", "treatment"]:
        """
        Assign conversation to control or treatment group.

        Returns:
            "control" or "treatment"
        """
        # Check if already assigned
        existing = self._get_assignment(conversation_id)
        if existing:
            return existing

        # Random assignment
        group = "treatment" if random.random() < self.treatment_probability else "control"

        # Store assignment
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO ab_test_assignments
            (conversation_id, user_id, group_assignment)
            VALUES (?, ?, ?)
        ''', (conversation_id, user_id, group))

        conn.commit()
        conn.close()

        return group

    def _get_assignment(self, conversation_id: str) -> Optional[str]:
        """Get existing group assignment."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT group_assignment
            FROM ab_test_assignments
            WHERE conversation_id = ?
        ''', (conversation_id,))

        result = cursor.fetchone()
        conn.close()

        return result[0] if result else None

    def is_control_group(self, conversation_id: str) -> bool:
        """Check if conversation is in control group."""
        assignment = self._get_assignment(conversation_id)
        return assignment == "control"

    def is_treatment_group(self, conversation_id: str) -> bool:
        """Check if conversation is in treatment group."""
        assignment = self._get_assignment(conversation_id)
        return assignment == "treatment"

    def record_metrics(self, metrics: ABTestMetrics):
        """Record metrics for a conversation."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO ab_test_metrics
            (conversation_id, user_id, group_assignment, timestamp,
             conversation_length_seconds, message_count, user_message_length_avg,
             user_corrections, follow_up_questions, positive_indicators,
             negative_indicators, satisfaction_rating)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            metrics.conversation_id,
            metrics.user_id,
            metrics.group,
            metrics.timestamp,
            metrics.conversation_length_seconds,
            metrics.message_count,
            metrics.user_message_length_avg,
            metrics.user_corrections,
            metrics.follow_up_questions,
            metrics.positive_indicators,
            metrics.negative_indicators,
            metrics.satisfaction_rating
        ))

        conn.commit()
        conn.close()

    def get_results(self) -> Dict:
        """
        Calculate A/B test results.

        Returns:
            {
                "control": {...metrics...},
                "treatment": {...metrics...},
                "deltas": {...improvements...}
            }
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        results = {
            "control": self._calculate_group_metrics(cursor, "control"),
            "treatment": self._calculate_group_metrics(cursor, "treatment"),
        }

        conn.close()

        # Calculate deltas
        if results["control"]["count"] > 0 and results["treatment"]["count"] > 0:
            results["deltas"] = self._calculate_deltas(
                results["control"],
                results["treatment"]
            )
        else:
            results["deltas"] = {}

        return results

    def _calculate_group_metrics(self, cursor, group: str) -> Dict:
        """Calculate average metrics for a group."""
        cursor.execute('''
            SELECT
                COUNT(*) as count,
                AVG(conversation_length_seconds) as avg_length,
                AVG(message_count) as avg_messages,
                AVG(user_message_length_avg) as avg_msg_length,
                AVG(user_corrections) as avg_corrections,
                AVG(follow_up_questions) as avg_followups,
                AVG(positive_indicators) as avg_positive,
                AVG(negative_indicators) as avg_negative,
                AVG(satisfaction_rating) as avg_satisfaction
            FROM ab_test_metrics
            WHERE group_assignment = ?
        ''', (group,))

        row = cursor.fetchone()

        return {
            "count": row[0] or 0,
            "avg_conversation_length": row[1] or 0,
            "avg_messages": row[2] or 0,
            "avg_message_length": row[3] or 0,
            "avg_corrections": row[4] or 0,
            "avg_followups": row[5] or 0,
            "avg_positive": row[6] or 0,
            "avg_negative": row[7] or 0,
            "avg_satisfaction": row[8] or 0,
        }

    def _calculate_deltas(
        self,
        control: Dict,
        treatment: Dict
    ) -> Dict:
        """Calculate percentage improvements."""
        deltas = {}

        for key in control:
            if key == "count":
                continue

            control_val = control[key]
            treatment_val = treatment[key]

            if control_val > 0:
                delta_pct = ((treatment_val - control_val) / control_val) * 100
                deltas[key] = {
                    "control": control_val,
                    "treatment": treatment_val,
                    "delta_pct": delta_pct
                }

        return deltas

    def print_results(self):
        """Print formatted A/B test results."""
        results = self.get_results()

        print("\n" + "="*60)
        print("📊 A/B TEST RESULTS")
        print("="*60)

        print(f"\nControl Group (n={results['control']['count']}):")
        self._print_group_metrics(results['control'])

        print(f"\nTreatment Group (n={results['treatment']['count']}):")
        self._print_group_metrics(results['treatment'])

        if results.get('deltas'):
            print("\n🎯 DELTAS (Treatment vs Control):")
            for key, data in results['deltas'].items():
                delta = data['delta_pct']
                emoji = "📈" if delta > 0 else "📉"
                print(f"  {emoji} {key}: {delta:+.1f}%")

        print("="*60 + "\n")

    def _print_group_metrics(self, metrics: Dict):
        """Print metrics for a group."""
        print(f"  Avg conversation length: {metrics['avg_conversation_length']:.1f}s")
        print(f"  Avg messages: {metrics['avg_messages']:.1f}")
        print(f"  Avg message length: {metrics['avg_message_length']:.0f} chars")
        print(f"  Avg corrections: {metrics['avg_corrections']:.2f}")
        print(f"  Avg follow-ups: {metrics['avg_followups']:.2f}")
        print(f"  Avg positive indicators: {metrics['avg_positive']:.2f}")
        print(f"  Avg negative indicators: {metrics['avg_negative']:.2f}")
        if metrics['avg_satisfaction'] > 0:
            print(f"  Avg satisfaction: {metrics['avg_satisfaction']:.1f}/10")


# Singleton instance
_ab_test = None


def get_ab_test() -> AdaptationABTest:
    """Get global A/B test instance."""
    global _ab_test
    if _ab_test is None:
        _ab_test = AdaptationABTest()
    return _ab_test
