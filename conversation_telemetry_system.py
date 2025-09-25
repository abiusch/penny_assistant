"""
Conversation Telemetry System
Collects production metrics to evaluate cultural intelligence effectiveness.
"""

from __future__ import annotations

import asyncio
import json
import time
import uuid
import threading
from pathlib import Path
from typing import Any, Awaitable, Dict, List, Optional

import aiosqlite

from conversation_flow_analyzer import ConversationFlowAnalyzer


class ConversationTelemetrySystem:
    """Stores cultural intelligence telemetry in SQLite for later analysis."""

    def __init__(self, db_path: str = "conversation_telemetry.db") -> None:
        self.db_path = Path(db_path)
        self._flow_analyzer = ConversationFlowAnalyzer()
        self._tables_initialized = False

    async def initialize(self) -> None:
        async with aiosqlite.connect(self.db_path) as db:
            await self._ensure_tables(db)

    async def log_cultural_decision(self,
                                    decision_type: str,
                                    context: Dict[str, Any],
                                    outcome: Dict[str, Any]) -> None:
        async with aiosqlite.connect(self.db_path) as db:
            await self._ensure_tables(db)
            await db.execute(
                """
                INSERT INTO cultural_decisions
                (decision_id, timestamp, decision_type, context_json, outcome_json)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    str(uuid.uuid4()),
                    int(time.time()),
                    decision_type,
                    json.dumps(context, ensure_ascii=True),
                    json.dumps(outcome, ensure_ascii=True),
                ),
            )
            await db.commit()

    async def measure_conversation_flow(self,
                                        conversation_turns: List[Dict[str, str]],
                                        metadata: Optional[Dict[str, Any]] = None) -> Dict[str, float]:
        """Compute flow metrics for a conversation transcript and persist them."""
        metadata = metadata or {}
        latest_turn = conversation_turns[-1] if conversation_turns else {"user": "", "assistant": ""}
        appropriateness = self._flow_analyzer.analyze_response_appropriateness(
            latest_turn.get("user", ""), latest_turn.get("assistant", "")
        )
        disruption = self._flow_analyzer.detect_conversation_disruption(conversation_turns)

        metrics = {
            "response_appropriateness": round(appropriateness, 4),
            "conversation_stability": round(disruption, 4),
            "turn_count": len(conversation_turns),
        }

        async with aiosqlite.connect(self.db_path) as db:
            await self._ensure_tables(db)
            await db.execute(
                """
                INSERT INTO conversation_metrics
                (metric_id, timestamp, metrics_json, metadata_json)
                VALUES (?, ?, ?, ?)
                """,
                (
                    str(uuid.uuid4()),
                    int(time.time()),
                    json.dumps(metrics, ensure_ascii=True),
                    json.dumps(metadata, ensure_ascii=True),
                ),
            )
            await db.commit()

        return metrics

    async def track_engagement_metrics(self,
                                       session_id: str,
                                       metrics: Dict[str, Any]) -> None:
        async with aiosqlite.connect(self.db_path) as db:
            await self._ensure_tables(db)
            await db.execute(
                """
                INSERT INTO engagement_metrics
                (session_id, timestamp, metrics_json)
                VALUES (?, ?, ?)
                """,
                (
                    session_id,
                    int(time.time()),
                    json.dumps(metrics, ensure_ascii=True),
                ),
            )
            await db.commit()

    async def assess_personality_consistency(self,
                                             responses: List[str],
                                             baseline_personality: Dict[str, List[str]]) -> float:
        if not responses:
            return 0.0

        scores = [
            self._flow_analyzer.score_authenticity(response, baseline_personality)
            for response in responses
        ]
        average = sum(scores) / len(scores)

        async with aiosqlite.connect(self.db_path) as db:
            await self._ensure_tables(db)
            await db.execute(
                """
                INSERT INTO personality_consistency
                (consistency_id, timestamp, average_score, sample_count)
                VALUES (?, ?, ?, ?)
                """,
                (
                    str(uuid.uuid4()),
                    int(time.time()),
                    float(round(average, 4)),
                    len(scores),
                ),
            )
            await db.commit()

        return average

    async def get_recent_decisions(self, limit: int = 50) -> List[Dict[str, Any]]:
        async with aiosqlite.connect(self.db_path) as db:
            await self._ensure_tables(db)
            cursor = await db.execute(
                "SELECT decision_type, context_json, outcome_json, timestamp\n                 FROM cultural_decisions ORDER BY timestamp DESC LIMIT ?",
                (limit,),
            )
            rows = await cursor.fetchall()
        decisions = []
        for dtype, context_json, outcome_json, timestamp in rows:
            decisions.append({
                "decision_type": dtype,
                "context": json.loads(context_json),
                "outcome": json.loads(outcome_json),
                "timestamp": timestamp,
            })
        return decisions

    async def _ensure_tables(self, db: aiosqlite.Connection) -> None:
        if self._tables_initialized:
            return

        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS cultural_decisions (
                decision_id TEXT PRIMARY KEY,
                timestamp INTEGER,
                decision_type TEXT,
                context_json TEXT,
                outcome_json TEXT
            )
            """,
        )
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS conversation_metrics (
                metric_id TEXT PRIMARY KEY,
                timestamp INTEGER,
                metrics_json TEXT,
                metadata_json TEXT
            )
            """,
        )
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS engagement_metrics (
                metric_id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                timestamp INTEGER,
                metrics_json TEXT
            )
            """,
        )
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS personality_consistency (
                consistency_id TEXT PRIMARY KEY,
                timestamp INTEGER,
                average_score REAL,
                sample_count INTEGER
            )
            """,
        )
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS ab_testing_sessions (
                session_id TEXT PRIMARY KEY,
                user_id TEXT,
                cultural_enabled INTEGER,
                assigned_at INTEGER
            )
            """,
        )
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS ab_session_metrics (
                record_id TEXT PRIMARY KEY,
                session_id TEXT,
                cultural_enabled INTEGER,
                metrics_json TEXT,
                recorded_at INTEGER
            )
            """,
        )
        await db.commit()
        self._tables_initialized = True


class _AsyncLoopRunner:
    """Utility to run coroutines on a persistent background loop."""

    def __init__(self) -> None:
        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    def _run_loop(self) -> None:  # pragma: no cover
        asyncio.set_event_loop(self._loop)
        self._loop.run_forever()

    def run(self, coro: Awaitable[Any]) -> Any:
        future = asyncio.run_coroutine_threadsafe(coro, self._loop)
        return future.result()

    def shutdown(self) -> None:
        self._loop.call_soon_threadsafe(self._loop.stop)
        self._thread.join(timeout=1.0)


class TelemetryClient:
    """Synchronous facade over ConversationTelemetrySystem."""

    def __init__(self, db_path: str = "conversation_telemetry.db") -> None:
        self._runner = _AsyncLoopRunner()
        self.telemetry = ConversationTelemetrySystem(db_path)
        self._runner.run(self.telemetry.initialize())

    def run(self, coro):
        return self._runner.run(coro)

    def log_cultural_decision(self,
                              decision_type: str,
                              context: Dict[str, Any],
                              outcome: Dict[str, Any]) -> None:
        self.run(self.telemetry.log_cultural_decision(decision_type, context, outcome))

    def measure_conversation_flow(self,
                                  conversation_turns: List[Dict[str, str]],
                                  metadata: Optional[Dict[str, Any]] = None) -> Dict[str, float]:
        return self.run(self.telemetry.measure_conversation_flow(conversation_turns, metadata))

    def track_engagement_metrics(self, session_id: str, metrics: Dict[str, Any]) -> None:
        self.run(self.telemetry.track_engagement_metrics(session_id, metrics))

    def assess_personality_consistency(self,
                                       responses: List[str],
                                       baseline_personality: Dict[str, List[str]]) -> float:
        return self.run(self.telemetry.assess_personality_consistency(responses, baseline_personality))

    def get_recent_decisions(self, limit: int = 50) -> List[Dict[str, Any]]:
        return self.run(self.telemetry.get_recent_decisions(limit))

    def shutdown(self) -> None:
        self._runner.shutdown()
