#!/usr/bin/env python3
"""
Security Streaming Response Processor
Implements fast-path security evaluation with streaming responses
"""

import asyncio
import json
import logging
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable, AsyncIterator, Union
from dataclasses import dataclass, asdict
from enum import Enum
from concurrent.futures import ThreadPoolExecutor, Future, TimeoutError as FutureTimeoutError

try:
    from security_ethics_foundation import SecurityEthicsFoundation, EthicalViolation, EthicalBoundary
    from security_violation_handler import SecurityViolationHandler, ViolationType, ViolationSeverity
    from command_whitelist_system import CommandWhitelistSystem, PermissionLevel, PermissionCheck
except ImportError as e:
    print(f"Warning: Could not import security components: {e}")

class SecurityDecision(Enum):
    """Security decision types"""
    ALLOW = "allow"
    BLOCK = "block"
    REVIEW = "review"
    UNKNOWN = "unknown"

class DecisionConfidence(Enum):
    """Confidence levels for security decisions"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNCERTAIN = "uncertain"

class DecisionSource(Enum):
    """Source of the security decision"""
    RULE_BASED = "rule_based"
    LLM_STREAMING = "llm_streaming"
    LLM_COMPLETE = "llm_complete"
    CACHED = "cached"
    FALLBACK = "fallback"

@dataclass
class StreamingSecurityDecision:
    """Security decision that can be updated as more information becomes available"""
    decision: SecurityDecision
    confidence: DecisionConfidence
    source: DecisionSource
    timestamp: datetime
    reasoning: str
    request_id: str
    session_id: str
    operation: str
    parameters: Dict[str, Any]
    processing_time_ms: float
    is_final: bool = False
    alternatives: List[str] = None
    restrictions: List[str] = None

    def __post_init__(self):
        if self.alternatives is None:
            self.alternatives = []
        if self.restrictions is None:
            self.restrictions = []

@dataclass
class SecurityCacheEntry:
    """Cache entry for security decisions"""
    decision: SecurityDecision
    confidence: DecisionConfidence
    reasoning: str
    timestamp: datetime
    hit_count: int
    operation_signature: str
    parameters_hash: str

class SecurityDecisionCache:
    """Cache for frequently requested security decisions"""

    def __init__(self, max_size: int = 1000, ttl_minutes: int = 60):
        self.cache: Dict[str, SecurityCacheEntry] = {}
        self.max_size = max_size
        self.ttl = timedelta(minutes=ttl_minutes)
        self.lock = threading.RLock()

    def _generate_cache_key(self, operation: str, parameters: Dict[str, Any]) -> str:
        """Generate cache key from operation and parameters"""
        import hashlib

        # Normalize parameters for consistent hashing
        normalized_params = json.dumps(parameters, sort_keys=True, default=str)
        params_hash = hashlib.md5(normalized_params.encode()).hexdigest()

        return f"{operation}:{params_hash}"

    def get(self, operation: str, parameters: Dict[str, Any]) -> Optional[SecurityCacheEntry]:
        """Get cached decision if available and valid"""
        key = self._generate_cache_key(operation, parameters)

        with self.lock:
            entry = self.cache.get(key)
            if entry is None:
                return None

            # Check if entry is expired
            if datetime.now() - entry.timestamp > self.ttl:
                del self.cache[key]
                return None

            # Update hit count
            entry.hit_count += 1
            return entry

    def set(self, operation: str, parameters: Dict[str, Any],
            decision: SecurityDecision, confidence: DecisionConfidence, reasoning: str):
        """Cache a security decision"""
        key = self._generate_cache_key(operation, parameters)

        with self.lock:
            # Evict oldest entries if cache is full
            if len(self.cache) >= self.max_size:
                oldest_key = min(self.cache.keys(), key=lambda k: self.cache[k].timestamp)
                del self.cache[oldest_key]

            self.cache[key] = SecurityCacheEntry(
                decision=decision,
                confidence=confidence,
                reasoning=reasoning,
                timestamp=datetime.now(),
                hit_count=0,
                operation_signature=operation,
                parameters_hash=key.split(':')[1]
            )

    def invalidate_pattern(self, operation_pattern: str):
        """Invalidate cache entries matching a pattern"""
        with self.lock:
            keys_to_remove = [k for k in self.cache.keys() if operation_pattern in k]
            for key in keys_to_remove:
                del self.cache[key]

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        with self.lock:
            total_hits = sum(entry.hit_count for entry in self.cache.values())
            return {
                "total_entries": len(self.cache),
                "total_hits": total_hits,
                "hit_rate": total_hits / max(len(self.cache), 1),
                "oldest_entry": min((e.timestamp for e in self.cache.values()), default=datetime.now()),
                "newest_entry": max((e.timestamp for e in self.cache.values()), default=datetime.now())
            }

class RuleBasedSecurityEvaluator:
    """Fast rule-based security evaluation for common patterns"""

    def __init__(self):
        self.rules = self._load_security_rules()

    def _load_security_rules(self) -> Dict[str, Any]:
        """Load fast-path security rules"""
        return {
            "immediate_block": {
                "patterns": [
                    r".*\.\./.*",  # Path traversal
                    r".*rm\s+-rf.*",  # Dangerous deletion
                    r".*sudo\s+.*",  # Sudo commands
                    r".*passwd.*",  # Password changes
                    r".*curl.*malware.*",  # Suspicious downloads
                    r".*wget.*hack.*",  # Suspicious downloads
                ],
                "keywords": [
                    "delete_all", "format_drive", "destroy", "wipe", "hack",
                    "exploit", "virus", "malware", "keylogger", "backdoor"
                ]
            },
            "immediate_allow": {
                "patterns": [
                    r"^file_read\s+[a-zA-Z0-9_./]+\.(txt|md|json|py|js|html)$",
                    r"^list_directory\s+[a-zA-Z0-9_./]+$",
                    r"^get_status$",
                    r"^help.*$"
                ],
                "operations": [
                    "get_time", "get_date", "calculate", "analyze_text",
                    "format_text", "validate_json", "check_syntax"
                ]
            },
            "require_review": {
                "patterns": [
                    r".*network.*external.*",
                    r".*database.*modify.*",
                    r".*system.*config.*",
                    r".*execute.*shell.*"
                ],
                "operations": [
                    "network_request", "database_write", "system_modify",
                    "user_management", "permission_change"
                ]
            }
        }

    def evaluate(self, operation: str, parameters: Dict[str, Any]) -> Optional[StreamingSecurityDecision]:
        """Fast rule-based evaluation"""
        import re

        start_time = time.time()
        operation_text = f"{operation} {' '.join(str(v) for v in parameters.values())}"

        # Check immediate block rules
        for pattern in self.rules["immediate_block"]["patterns"]:
            if re.search(pattern, operation_text, re.IGNORECASE):
                return StreamingSecurityDecision(
                    decision=SecurityDecision.BLOCK,
                    confidence=DecisionConfidence.HIGH,
                    source=DecisionSource.RULE_BASED,
                    timestamp=datetime.now(),
                    reasoning=f"Blocked by security pattern: {pattern}",
                    request_id="",
                    session_id="",
                    operation=operation,
                    parameters=parameters,
                    processing_time_ms=(time.time() - start_time) * 1000,
                    is_final=True
                )

        for keyword in self.rules["immediate_block"]["keywords"]:
            if keyword.lower() in operation_text.lower():
                return StreamingSecurityDecision(
                    decision=SecurityDecision.BLOCK,
                    confidence=DecisionConfidence.HIGH,
                    source=DecisionSource.RULE_BASED,
                    timestamp=datetime.now(),
                    reasoning=f"Blocked by security keyword: {keyword}",
                    request_id="",
                    session_id="",
                    operation=operation,
                    parameters=parameters,
                    processing_time_ms=(time.time() - start_time) * 1000,
                    is_final=True
                )

        # Check immediate allow rules
        for pattern in self.rules["immediate_allow"]["patterns"]:
            if re.fullmatch(pattern, operation, re.IGNORECASE):
                return StreamingSecurityDecision(
                    decision=SecurityDecision.ALLOW,
                    confidence=DecisionConfidence.HIGH,
                    source=DecisionSource.RULE_BASED,
                    timestamp=datetime.now(),
                    reasoning=f"Allowed by safe operation pattern: {pattern}",
                    request_id="",
                    session_id="",
                    operation=operation,
                    parameters=parameters,
                    processing_time_ms=(time.time() - start_time) * 1000,
                    is_final=True
                )

        if operation in self.rules["immediate_allow"]["operations"]:
            return StreamingSecurityDecision(
                decision=SecurityDecision.ALLOW,
                confidence=DecisionConfidence.HIGH,
                source=DecisionSource.RULE_BASED,
                timestamp=datetime.now(),
                reasoning=f"Allowed safe operation: {operation}",
                request_id="",
                session_id="",
                operation=operation,
                parameters=parameters,
                processing_time_ms=(time.time() - start_time) * 1000,
                is_final=True
            )

        # Check review required rules
        for pattern in self.rules["require_review"]["patterns"]:
            if re.search(pattern, operation_text, re.IGNORECASE):
                return StreamingSecurityDecision(
                    decision=SecurityDecision.REVIEW,
                    confidence=DecisionConfidence.MEDIUM,
                    source=DecisionSource.RULE_BASED,
                    timestamp=datetime.now(),
                    reasoning=f"Requires review due to pattern: {pattern}",
                    request_id="",
                    session_id="",
                    operation=operation,
                    parameters=parameters,
                    processing_time_ms=(time.time() - start_time) * 1000,
                    is_final=False
                )

        if operation in self.rules["require_review"]["operations"]:
            return StreamingSecurityDecision(
                decision=SecurityDecision.REVIEW,
                confidence=DecisionConfidence.MEDIUM,
                source=DecisionSource.RULE_BASED,
                timestamp=datetime.now(),
                reasoning=f"Operation requires review: {operation}",
                request_id="",
                session_id="",
                operation=operation,
                parameters=parameters,
                processing_time_ms=(time.time() - start_time) * 1000,
                is_final=False
            )

        return None

class SecurityStreamingProcessor:
    """Main processor for streaming security decisions"""

    def __init__(self,
                 db_path: str = "security_streaming.db",
                 llm_timeout_seconds: float = 5.0,
                 fallback_decision: SecurityDecision = SecurityDecision.BLOCK):

        self.logger = logging.getLogger("security_streaming")
        self.db_path = db_path
        self.llm_timeout = llm_timeout_seconds
        self.fallback_decision = fallback_decision

        # Initialize components
        self.cache = SecurityDecisionCache()
        self.rule_evaluator = RuleBasedSecurityEvaluator()
        self.ethics_foundation = SecurityEthicsFoundation()
        self.violation_handler = SecurityViolationHandler(db_path)
        self.whitelist_system = CommandWhitelistSystem()

        # Statistics
        self.stats = {
            "total_requests": 0,
            "cache_hits": 0,
            "rule_based_decisions": 0,
            "llm_decisions": 0,
            "fallback_decisions": 0,
            "avg_response_time_ms": 0.0
        }

        # Thread pool for LLM processing
        self.executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="security_llm")

    async def evaluate_security_request(self,
                                       operation: str,
                                       parameters: Dict[str, Any],
                                       session_id: str,
                                       request_id: Optional[str] = None) -> AsyncIterator[StreamingSecurityDecision]:
        """
        Evaluate security request with streaming responses
        Yields decisions as they become available
        """

        if request_id is None:
            request_id = f"req_{int(time.time() * 1000)}"

        start_time = time.time()
        self.stats["total_requests"] += 1

        # Step 1: Check cache first (fastest)
        cached_entry = self.cache.get(operation, parameters)
        if cached_entry:
            self.stats["cache_hits"] += 1
            decision = StreamingSecurityDecision(
                decision=cached_entry.decision,
                confidence=cached_entry.confidence,
                source=DecisionSource.CACHED,
                timestamp=datetime.now(),
                reasoning=f"Cached: {cached_entry.reasoning}",
                request_id=request_id,
                session_id=session_id,
                operation=operation,
                parameters=parameters,
                processing_time_ms=(time.time() - start_time) * 1000,
                is_final=True
            )
            self.logger.info(f"Cache hit for {operation}: {decision.decision.value}")
            yield decision
            return

        # Step 2: Fast rule-based evaluation
        rule_decision = self.rule_evaluator.evaluate(operation, parameters)
        if rule_decision:
            rule_decision.request_id = request_id
            rule_decision.session_id = session_id
            self.stats["rule_based_decisions"] += 1

            self.logger.info(f"Rule-based decision for {operation}: {rule_decision.decision.value}")

            # Cache rule-based decisions
            if rule_decision.confidence == DecisionConfidence.HIGH:
                self.cache.set(operation, parameters, rule_decision.decision,
                             rule_decision.confidence, rule_decision.reasoning)

            yield rule_decision

            # If decision is final (high confidence), stop here
            if rule_decision.is_final:
                return

        # Step 3: Start LLM evaluation in background (for uncertain cases)
        llm_future = None
        if not rule_decision or rule_decision.decision == SecurityDecision.REVIEW:
            llm_future = self.executor.submit(
                self._llm_security_evaluation,
                operation, parameters, session_id, request_id
            )

        # Step 4: Wait for LLM with timeout
        if llm_future:
            try:
                llm_decision = await asyncio.wait_for(
                    asyncio.wrap_future(llm_future),
                    timeout=self.llm_timeout
                )

                if llm_decision:
                    self.stats["llm_decisions"] += 1
                    self.logger.info(f"LLM decision for {operation}: {llm_decision.decision.value}")

                    # Cache LLM decisions if confident
                    if llm_decision.confidence in [DecisionConfidence.HIGH, DecisionConfidence.MEDIUM]:
                        self.cache.set(operation, parameters, llm_decision.decision,
                                     llm_decision.confidence, llm_decision.reasoning)

                    yield llm_decision
                    return

            except asyncio.TimeoutError:
                self.logger.warning(f"LLM timeout for {operation}, using fallback")
                llm_future.cancel()

        # Step 5: Fallback decision with safe defaults
        fallback_decision = self._generate_fallback_decision(
            operation, parameters, session_id, request_id, start_time
        )

        self.stats["fallback_decisions"] += 1
        self.logger.warning(f"Fallback decision for {operation}: {fallback_decision.decision.value}")

        yield fallback_decision

    def _llm_security_evaluation(self,
                                operation: str,
                                parameters: Dict[str, Any],
                                session_id: str,
                                request_id: str) -> Optional[StreamingSecurityDecision]:
        """Perform LLM-based security evaluation"""

        start_time = time.time()

        try:
            # Use existing security components for LLM evaluation
            permission_check = self.whitelist_system.check_permission(operation, parameters)

            if not permission_check.allowed:
                decision = SecurityDecision.BLOCK
                confidence = DecisionConfidence.HIGH
                reasoning = f"Permission denied: {permission_check.reason}"
            else:
                # Check ethical boundaries
                context_text = f"{operation} {json.dumps(parameters)}"
                ethical_violation = self.ethics_foundation.evaluate_ethical_boundaries(context_text, {})

                if ethical_violation:
                    decision = SecurityDecision.BLOCK
                    confidence = DecisionConfidence.HIGH
                    reasoning = f"Ethical violation: {ethical_violation.description}"
                else:
                    decision = SecurityDecision.ALLOW
                    confidence = DecisionConfidence.MEDIUM
                    reasoning = "No security concerns detected"

            return StreamingSecurityDecision(
                decision=decision,
                confidence=confidence,
                source=DecisionSource.LLM_COMPLETE,
                timestamp=datetime.now(),
                reasoning=reasoning,
                request_id=request_id,
                session_id=session_id,
                operation=operation,
                parameters=parameters,
                processing_time_ms=(time.time() - start_time) * 1000,
                is_final=True,
                alternatives=permission_check.alternative_suggestions if hasattr(permission_check, 'alternative_suggestions') else []
            )

        except Exception as e:
            self.logger.error(f"LLM evaluation failed: {e}")
            return None

    def _generate_fallback_decision(self,
                                  operation: str,
                                  parameters: Dict[str, Any],
                                  session_id: str,
                                  request_id: str,
                                  start_time: float) -> StreamingSecurityDecision:
        """Generate safe fallback decision when LLM is unavailable"""

        # Conservative fallback: block by default, allow only known safe operations
        safe_operations = [
            "help", "status", "ping", "echo", "list", "read", "view", "show",
            "get", "display", "check", "validate", "format", "analyze"
        ]

        is_safe = any(safe_op in operation.lower() for safe_op in safe_operations)

        decision = SecurityDecision.ALLOW if is_safe else self.fallback_decision
        confidence = DecisionConfidence.LOW
        reasoning = f"Fallback decision - LLM unavailable. Operation {'appears safe' if is_safe else 'blocked by default'}"

        alternatives = [
            "Try a simpler operation",
            "Request help for available operations",
            "Wait for full security system to be available"
        ] if not is_safe else []

        return StreamingSecurityDecision(
            decision=decision,
            confidence=confidence,
            source=DecisionSource.FALLBACK,
            timestamp=datetime.now(),
            reasoning=reasoning,
            request_id=request_id,
            session_id=session_id,
            operation=operation,
            parameters=parameters,
            processing_time_ms=(time.time() - start_time) * 1000,
            is_final=True,
            alternatives=alternatives,
            restrictions=["limited_functionality"] if not is_safe else []
        )

    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        cache_stats = self.cache.get_stats()

        return {
            "processing_stats": self.stats,
            "cache_stats": cache_stats,
            "timestamp": datetime.now().isoformat()
        }

    def invalidate_cache(self, pattern: Optional[str] = None):
        """Invalidate cache entries"""
        if pattern:
            self.cache.invalidate_pattern(pattern)
        else:
            self.cache.cache.clear()

    def shutdown(self):
        """Shutdown the processor"""
        self.executor.shutdown(wait=True)
        self.logger.info("Security streaming processor shutdown complete")

async def demo_streaming_security():
    """Demonstrate streaming security evaluation"""

    processor = SecurityStreamingProcessor(
        db_path="demo_security_streaming.db",
        llm_timeout_seconds=2.0
    )

    test_operations = [
        ("file_read", {"path": "config.json"}),
        ("system_delete", {"path": "/etc/passwd"}),
        ("help", {}),
        ("../malicious/path", {"depth": 5}),
        ("network_request", {"url": "http://suspicious.com"}),
        ("analyze_text", {"content": "Hello world"}),
        ("rm -rf /", {"force": True}),
        ("list_directory", {"path": "/home/user/documents"})
    ]

    print("🚀 Security Streaming Processor Demo")
    print("=" * 60)

    for i, (operation, parameters) in enumerate(test_operations):
        print(f"\n{i+1}. Testing: {operation}")
        print(f"   Parameters: {parameters}")
        print("   Decisions:")

        async for decision in processor.evaluate_security_request(
            operation, parameters, f"demo_session_{i}", f"req_{i}"
        ):
            print(f"   → {decision.decision.value} ({decision.confidence.value}) "
                  f"via {decision.source.value} in {decision.processing_time_ms:.1f}ms")
            print(f"     Reason: {decision.reasoning}")
            if decision.alternatives:
                print(f"     Alternatives: {', '.join(decision.alternatives)}")

    print(f"\n📊 Performance Statistics:")
    stats = processor.get_performance_stats()
    for key, value in stats["processing_stats"].items():
        print(f"   {key}: {value}")

    processor.shutdown()

    # Cleanup
    import os
    if os.path.exists("demo_security_streaming.db"):
        os.remove("demo_security_streaming.db")

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    asyncio.run(demo_streaming_security())