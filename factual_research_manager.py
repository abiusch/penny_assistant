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

try:
    from src.core.query_classifier import needs_research as shared_needs_research
except ImportError:  # pragma: no cover - fallback for isolated tooling
    shared_needs_research = None


class FactualQueryClassifier:
    """Heuristic classifier to decide when research or disclaimers are needed."""

    FINANCIAL_PHRASES = {
        "stock market", "stock price", "share price", "price target",
        "earnings report", "quarterly results", "market cap", "market capitalization",
        "financial statement", "investment strategy", "mutual fund", "401k",
        "roth ira", "retirement account", "cryptocurrency", "crypto price",
        "bitcoin price", "ethereum price", "mortgage rate", "interest rate",
        "federal reserve", "fed rate", "option contract", "options trading",
        "initial public offering", "mergers and acquisitions", "valuation model"
    }

    STRONG_FINANCIAL_KEYWORDS = {
        "invest", "investment", "investing", "stock", "stocks", "portfolio",
        "equity", "dividend", "ipo", "earnings", "revenue", "etf",
        "crypto", "cryptocurrency", "bitcoin", "ethereum", "financial",
        "finance", "trading", "brokerage", "hedge fund", "mutual fund",
        "bond", "options", "merger", "acquisition", "valuation"
    }

    WEAK_FINANCIAL_KEYWORDS = {
        "price", "prices", "buy", "sell", "market", "budget"
    }

    FINANCIAL_CONTEXT_WORDS = {
        "stock", "stocks", "share", "shares", "portfolio", "invest", "investment",
        "investing", "crypto", "cryptocurrency", "bitcoin", "ethereum",
        "fund", "funds", "etf", "bond", "bonds", "option", "options",
        "retirement", "mortgage", "valuation", "revenue", "earnings"
    }

    FINANCIAL_CONTEXT_PHRASES = {
        "mutual fund", "mutual funds", "401k", "ira", "roth ira"
    }

    PROGRAMMING_KEYWORDS = {
        "python", "javascript", "java", "c++", "c#", "go", "golang",
        "rust", "typescript", "sql", "html", "css", "bash", "shell",
        "code", "coding", "program", "programming", "script", "function",
        "method", "class", "module", "package", "library", "api", "endpoint",
        "debug", "bug", "error", "exception", "stack trace", "traceback",
        "variable", "loop", "list", "array", "dictionary", "tuple",
        "algorithm", "compile", "runtime", "test", "unit test",
        "recursion", "recursive", "iterate", "iteration", "callback",
        "async", "await", "promise", "lambda", "closure", "decorator",
        "regex", "regular expression", "parse", "parser", "serialize"
    }

    PROGRAMMING_PHRASES = {
        "how do i", "how to", "what is the difference", "explain the",
        "example of", "sample code", "fix this", "solve this", "debug",
        "error message", "stack trace", "traceback", "why does",
        "write a", "write an", "write code", "write function",
        "create a", "create an", "create function", "create code",
        "implement", "implement a", "implement an", "implement function",
        "can you write", "can you create", "can you make",
        "build a", "build an", "make a", "make an",
        "best way to", "difference between",
        "what does this", "review this", "review my", "check this",
        "fix my code", "debug this", "what's wrong with"
    }

    PERSONAL_KEYWORDS = {
        "how are you", "how's your", "how do you feel", "what's up",
        "good morning", "good afternoon", "good evening", "hello", "hi",
        # User preferences/instructions - NOT factual queries
        "you don't need", "no need to", "don't bother", "skip", "ignore",
        "don't add", "no thanks", "that's fine", "nevermind", "forget it"
    }

    # Self-reference keywords - when user is talking about Penny herself
    # Note: Must be specific to avoid false matches (e.g., "do you" catches "do some research")
    SELF_REFERENCE_KEYWORDS = {
        "your name", "who are you", "what are you",
        "you are an", "you are a", "you're an", "you're a",
        "are you an", "are you a",
        "what can you do", "what do you do", "how do you work",
        "about you", "about yourself", "tell me about penny",
        "penny's", "your system", "your code", "your personality"
    }

    # Explicit research request patterns - when user directly asks for research
    EXPLICIT_RESEARCH_REQUESTS = {
        "do some research", "do research", "look it up", "look that up",
        "search for", "find out", "check the latest", "check for updates",
        "what's the current", "what's the latest", "get the latest",
        "update yourself", "come back with updated", "go research",
        "find the latest", "check what's new", "see what's new",
        "look up the", "research this", "research that"
    }

    QUESTION_WORDS = {"who", "what", "when", "where", "why", "how"}

    TIME_SENSITIVE_PATTERNS = [
        r'\b(?:latest|recent|current|today|this week|this month|this year|new|updated?|202[0-9])\b',
        r'\b(?:breaking|news|announced|released|launched|just)\b',
        r'\b(?:now|currently|recently|lately)\b',
        r'\b(?:happened|occurred|took place|what.*result|election.*result)\b',
        r'\b(?:who won|winner of|champion|championship).*(?:this year|202[0-9]|today|latest)\b'
    ]

    HIGH_RISK_PATTERNS = [
        r'\b(?:stock|market|valuation|earnings|revenue)\b',
        r'\b(?:price|prices|pricing|update|upgrade|version|release|patch)\b'
    ]

    def requires_research(self, text: str) -> bool:
        """Smart research triggering - only for high-risk categories that require current data"""
        if not text:
            return False
        lowered = text.lower()

        # FIRST: Check for EXPLICIT research requests (user directly asking for research)
        # This should be checked early, but after opt-outs
        has_explicit_request = any(pattern in lowered for pattern in self.EXPLICIT_RESEARCH_REQUESTS)

        # SECOND: Check opt-outs (user declining research)
        # Use word boundaries to avoid false matches like "hi" in "this"
        has_opt_out = any(
            re.search(r'\b' + re.escape(pattern) + r'\b', lowered)
            for pattern in self.PERSONAL_KEYWORDS
        )
        if has_opt_out:
            return False

        # Skip research when user is talking about Penny herself
        if any(pattern in lowered for pattern in self.SELF_REFERENCE_KEYWORDS):
            return False

        # If we have explicit research request, trigger research
        if has_explicit_request:
            return True

        if self._is_financial_query(lowered):
            return True

        if any(re.search(pattern, lowered) for pattern in self.TIME_SENSITIVE_PATTERNS):
            return True

        if self._is_basic_programming_question(lowered):
            return False

        if any(re.search(pattern, lowered) for pattern in self.HIGH_RISK_PATTERNS):
            return True

        # Questions about specific company developments or tech specs
        if any(pattern in lowered for pattern in ["what are the", "tell me about", "details about"]):
            # Only if it seems like it could be about recent developments
            if any(word in lowered for word in ["company", "robot", "technology", "product", "service"]):
                return True

        if shared_needs_research is not None:
            return shared_needs_research(text)

        # Everything else can use training knowledge
        return False

    def is_financial_topic(self, text: str) -> bool:
        if not text:
            return False
        lowered = text.lower()
        return self._is_financial_query(lowered)

    def _contains_any_word(self, lowered: str, words: set[str]) -> bool:
        """Return True if any whole-word match from words is found in lowered."""
        return any(re.search(r'\b' + re.escape(word) + r'\b', lowered) for word in words)

    def _is_financial_query(self, lowered: str) -> bool:
        """Detect if text is asking about financial topics that need current info."""
        if any(phrase in lowered for phrase in self.FINANCIAL_PHRASES):
            return True

        if self._contains_any_word(lowered, self.STRONG_FINANCIAL_KEYWORDS):
            return True

        if self._contains_any_word(lowered, self.WEAK_FINANCIAL_KEYWORDS):
            if (self._contains_any_word(lowered, self.FINANCIAL_CONTEXT_WORDS)
                    or any(phrase in lowered for phrase in self.FINANCIAL_CONTEXT_PHRASES)):
                return True

        return False

    def _is_basic_programming_question(self, lowered: str) -> bool:
        """Detect coding/programming help that should use training knowledge."""
        # Check for explicit programming phrases first (even without keywords)
        if any(phrase in lowered for phrase in self.PROGRAMMING_PHRASES):
            # But skip if it's time-sensitive
            if re.search(r'\b(?:latest|current|recent|202[0-9])\b', lowered):
                return False
            if any(pattern in lowered for pattern in self.EXPLICIT_RESEARCH_REQUESTS):
                return False
            return True

        # Check for programming keywords
        if not self._contains_any_word(lowered, self.PROGRAMMING_KEYWORDS):
            return False

        if re.search(r'\b(?:latest|current|recent|202[0-9])\b', lowered):
            return False

        if any(pattern in lowered for pattern in self.EXPLICIT_RESEARCH_REQUESTS):
            return False

        code_markers = ['def ', 'class ', 'try:', 'except', 'import ', 'console.log', '=>', 'error:', 'traceback', 'stack trace']
        if any(marker in lowered for marker in code_markers):
            return True

        return True  # If has programming keywords, assume it's a programming question

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
