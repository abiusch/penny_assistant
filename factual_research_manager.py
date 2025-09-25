"""
Factual research manager for routing Penny's factual queries through
Autonomous Research Tool Server instead of relying on base model guesses.
Provides lightweight heuristics for detecting factual/financial requests
and orchestrating research execution and synthesis.
"""

from __future__ import annotations

import asyncio
import re
import threading
import time
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

from autonomous_research_tool_server import (
    create_autonomous_research_server,
    KnowledgeGapType,
)


class FactualQueryClassifier:
    """Heuristic classifier to decide when research or disclaimers are needed."""

    FINANCIAL_KEYWORDS = {
        "invest", "investment", "stock", "stocks", "portfolio", "equity",
        "share", "shares", "dividend", "market", "valuation", "ipo",
        "earnings", "revenue", "fund", "hedge", "etf", "crypto",
        "token", "financial", "finance", "trading", "price", "buy",
        "sell", "acquire", "merger", "m&a"
    }

    FACTUAL_KEYWORDS = {
        "what is", "who is", "tell me about", "background", "history",
        "latest", "current", "update", "overview", "explain", "details",
        "company", "product", "service", "technology", "market",
        "research", "emerging", "startups", "companies"
    }

    PERSONAL_KEYWORDS = {
        "how are you", "how's your", "how do you feel", "what's up",
        "good morning", "good afternoon", "good evening", "hello", "hi"
    }

    QUESTION_WORDS = {"who", "what", "when", "where", "why", "how"}

    def requires_research(self, text: str) -> bool:
        if not text:
            return False
        lowered = text.lower()

        # Skip research for personal/greeting queries
        if any(pattern in lowered for pattern in self.PERSONAL_KEYWORDS):
            return False

        if any(keyword in lowered for keyword in self.FINANCIAL_KEYWORDS):
            return True

        if any(pattern in lowered for pattern in self.FACTUAL_KEYWORDS):
            return True

        if any(lowered.startswith(word + " ") for word in self.QUESTION_WORDS):
            # Don't research questions about the assistant itself
            if any(personal in lowered for personal in ["how are you", "how do you", "what do you think"]):
                return False
            return True

        if re.search(r"\b\d{4}\b", lowered):
            return True

        if re.search(r"\b(?:revenue|headquarters|founded|ceo|valuation)\b", lowered):
            return True

        return False

    def is_financial_topic(self, text: str) -> bool:
        if not text:
            return False
        lowered = text.lower()
        return any(keyword in lowered for keyword in self.FINANCIAL_KEYWORDS)

    def extract_entities(self, text: str, limit: int = 5) -> List[str]:
        if not text:
            return []
        entities: List[str] = []
        for token in re.findall(r"[A-Z][a-zA-Z0-9&'.-]+", text):
            if token.lower() in {"what", "who", "when", "where", "why", "how"}:
                continue
            cleaned = token.rstrip("'s").strip()
            cleaned = cleaned.rstrip("'")
            if cleaned and cleaned not in entities:
                entities.append(cleaned)
            if len(entities) >= limit:
                break
        return entities


@dataclass
class ResearchResult:
    query: str
    success: bool
    summary: Optional[str]
    key_insights: List[str]
    recommendations: List[str]
    findings: List[Dict[str, Any]]
    confidence: float
    execution_time: float
    error: Optional[str] = None


class _AsyncResearchRunner:
    """Background event loop runner so research can be called synchronously."""

    def __init__(self) -> None:
        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    def _run_loop(self) -> None:  # pragma: no cover
        asyncio.set_event_loop(self._loop)
        self._loop.run_forever()

    def run(self, coro: asyncio.Future) -> Any:
        future = asyncio.run_coroutine_threadsafe(coro, self._loop)
        return future.result()

    def shutdown(self) -> None:
        self._loop.call_soon_threadsafe(self._loop.stop)
        self._thread.join(timeout=1.0)


class ResearchManager:
    """Coordinates autonomous research for factual requests."""

    def __init__(self, classifier: Optional[FactualQueryClassifier] = None) -> None:
        self.classifier = classifier or FactualQueryClassifier()
        self._runner = _AsyncResearchRunner()
        self._server = None

    def requires_research(self, text: str) -> bool:
        return self.classifier.requires_research(text)

    def is_financial_topic(self, text: str) -> bool:
        return self.classifier.is_financial_topic(text)

    def extract_entities(self, text: str) -> List[str]:
        return self.classifier.extract_entities(text)

    def run_research(self,
                     query: str,
                     conversation_history: Optional[List[Dict[str, str]]] = None) -> ResearchResult:
        return self._runner.run(self._run_research_async(query, conversation_history or []))

    async def _run_research_async(self,
                                  query: str,
                                  conversation_history: List[Dict[str, str]]) -> ResearchResult:
        start_time = time.time()
        try:
            await self._ensure_server()
            context = self._build_context(conversation_history)
            gap_payload = await self._identify_or_create_gap(query, context)

            plan_result = await self._server.create_research_plan(gap_payload)
            if not plan_result.success:
                return self._failure_result(query, start_time, plan_result.error)

            research_plan = plan_result.data.get("research_plan")
            if not research_plan:
                return self._failure_result(query, start_time, "No research plan generated")

            execute_result = await self._server.execute_research_plan(research_plan)
            if not execute_result.success:
                return self._failure_result(query, start_time, execute_result.error)

            findings = execute_result.data.get("research_findings", [])
            if not findings:
                return self._failure_result(query, start_time, "Research produced no findings")

            synthesis_result = await self._server.synthesize_research_findings(findings)
            if not synthesis_result.success:
                return self._failure_result(query, start_time, synthesis_result.error)

            synthesis = synthesis_result.data or {}
            return ResearchResult(
                query=query,
                success=True,
                summary=synthesis.get("summary"),
                key_insights=synthesis.get("key_insights", []),
                recommendations=synthesis.get("recommendations", []),
                findings=findings,
                confidence=float(synthesis.get("confidence", 0.0)),
                execution_time=time.time() - start_time,
                error=None,
            )
        except Exception as exc:  # pragma: no cover - defensive
            return self._failure_result(query, start_time, str(exc))

    def _failure_result(self, query: str, start_time: float, error: Optional[str]) -> ResearchResult:
        return ResearchResult(
            query=query,
            success=False,
            summary=None,
            key_insights=[],
            recommendations=[],
            findings=[],
            confidence=0.0,
            execution_time=time.time() - start_time,
            error=error,
        )

    async def _ensure_server(self) -> None:
        if self._server is None:
            self._server = await create_autonomous_research_server()

    async def _identify_or_create_gap(self, query: str, context: str) -> Dict[str, Any]:
        gap_result = await self._server.identify_knowledge_gaps(context, query)
        if gap_result.success:
            gaps = gap_result.data.get("knowledge_gaps", [])
            if gaps:
                return gaps[0]

        # Manual fallback
        return {
            "gap_id": f"manual_gap_{uuid.uuid4().hex[:8]}",
            "gap_type": KnowledgeGapType.FACTUAL.value,
            "description": query,
            "context": context[-2000:],
            "confidence": 0.6,
            "priority": 7,
            "detected_at": datetime.utcnow().isoformat(),
            "conversation_context": {"query": query}
        }

    def _build_context(self, history: List[Dict[str, str]], limit: int = 5) -> str:
        turns = history[-limit:]
        parts: List[str] = []
        for turn in turns:
            user = turn.get("user", "")
            assistant = turn.get("assistant", "")
            if user:
                parts.append(f"User: {user}")
            if assistant:
                parts.append(f"Penny: {assistant}")
        return "\n".join(parts)

    def shutdown(self) -> None:
        self._runner.shutdown()


__all__ = [
    "FactualQueryClassifier",
    "ResearchManager",
    "ResearchResult",
]
