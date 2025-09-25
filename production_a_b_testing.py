"""
Production A/B Testing Utilities for Cultural Intelligence
"""

from __future__ import annotations

import json
import secrets
import statistics
import time
from typing import Any, Dict, Optional

import aiosqlite

from conversation_telemetry_system import ConversationTelemetrySystem


class ProductionABTesting:
    """Manage live A/B tests for cultural intelligence enablement."""

    def __init__(self,
                 telemetry_system: ConversationTelemetrySystem,
                 db_path: Optional[str] = None) -> None:
        self.telemetry_system = telemetry_system
        self.db_path = db_path or str(telemetry_system.db_path)

    async def randomly_assign_cultural_mode(self,
                                            user_id: str,
                                            conversation_id: str) -> bool:
        async with aiosqlite.connect(self.db_path) as db:
            await self.telemetry_system._ensure_tables(db)
            cursor = await db.execute(
                "SELECT cultural_enabled FROM ab_testing_sessions WHERE session_id = ?",
                (conversation_id,),
            )
            row = await cursor.fetchone()
            if row is not None:
                return bool(row[0])

            assignment = secrets.choice([True, False])
            await db.execute(
                """
                INSERT INTO ab_testing_sessions (session_id, user_id, cultural_enabled, assigned_at)
                VALUES (?, ?, ?, ?)
                """,
                (
                    conversation_id,
                    user_id,
                    1 if assignment else 0,
                    int(time.time()),
                ),
            )
            await db.commit()
            return assignment

    async def collect_session_metrics(self,
                                      session_id: str,
                                      cultural_enabled: bool,
                                      metrics: Dict[str, Any]) -> None:
        async with aiosqlite.connect(self.db_path) as db:
            await self.telemetry_system._ensure_tables(db)
            await db.execute(
                """
                INSERT INTO ab_session_metrics
                (record_id, session_id, cultural_enabled, metrics_json, recorded_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    f"metric_{session_id}_{int(time.time()*1000)}",
                    session_id,
                    1 if cultural_enabled else 0,
                    json.dumps(metrics, ensure_ascii=True),
                    int(time.time()),
                ),
            )
            await db.commit()

    async def analyze_comparative_performance(self) -> Dict[str, Any]:
        async with aiosqlite.connect(self.db_path) as db:
            await self.telemetry_system._ensure_tables(db)
            cursor = await db.execute(
                "SELECT cultural_enabled, metrics_json FROM ab_session_metrics"
            )
            rows = await cursor.fetchall()

        enabled_scores = []
        disabled_scores = []
        for enabled_flag, metrics_json in rows:
            try:
                metrics = json.loads(metrics_json)
            except Exception:
                metrics = {}
            score = self._composite_score(metrics)
            if enabled_flag:
                enabled_scores.append(score)
            else:
                disabled_scores.append(score)

        comparison = {
            "enabled_average": statistics.mean(enabled_scores) if enabled_scores else 0.0,
            "disabled_average": statistics.mean(disabled_scores) if disabled_scores else 0.0,
            "enabled_sessions": len(enabled_scores),
            "disabled_sessions": len(disabled_scores),
        }
        comparison["delta"] = comparison["enabled_average"] - comparison["disabled_average"]
        return comparison

    def _composite_score(self, metrics: Dict[str, Any]) -> float:
        components = [
            float(metrics.get("response_appropriateness", 0.0)),
            float(metrics.get("conversation_stability", 0.0)),
            float(metrics.get("engagement_delta", metrics.get("engagement_improvement", 0.0))),
        ]
        valid_components = [value for value in components if value or value == 0.0]
        if not valid_components:
            return 0.0
        return sum(valid_components) / len(valid_components)


__all__ = ["ProductionABTesting"]
