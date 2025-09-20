#!/usr/bin/env python3
"""
Integrated Security Streaming System
Combines all security components for fast-path security evaluation
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, AsyncIterator, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import json

try:
    from security_streaming_processor import (
        SecurityStreamingProcessor, StreamingSecurityDecision,
        SecurityDecision, DecisionConfidence, DecisionSource
    )
    from security_emergency_fallback import (
        SecurityFallbackRuleEngine, EmergencyDecision,
        EmergencyThreatLevel, FallbackAction
    )
    from security_timeout_manager import (
        SecurityTimeoutManager, TimeoutConfig, TimeoutSeverity, TimeoutAction
    )
    from security_decision_cache import (
        SecurityDecisionCache, CacheEvictionPolicy, DecisionConfidence as CacheConfidence
    )
    from security_ethics_foundation import SecurityEthicsFoundation
    from security_violation_handler import SecurityViolationHandler
except ImportError as e:
    print(f"Warning: Could not import all security components: {e}")

class IntegratedDecisionSource(Enum):
    """Sources for integrated security decisions"""
    CACHE_HIT = "cache_hit"
    RULE_BASED_FAST = "rule_based_fast"
    EMERGENCY_FALLBACK = "emergency_fallback"
    TIMEOUT_FALLBACK = "timeout_fallback"
    LLM_STREAMING = "llm_streaming"
    LLM_COMPLETE = "llm_complete"
    SYSTEM_OVERRIDE = "system_override"

@dataclass
class IntegratedSecurityDecision:
    """Comprehensive security decision with full metadata"""
    # Core decision
    decision: str  # "allow", "block", "review", "defer"
    confidence: str  # "very_high", "high", "medium", "low", "uncertain"
    reasoning: str

    # Processing metadata
    decision_source: IntegratedDecisionSource
    processing_time_ms: float
    cache_used: bool
    fallback_used: bool
    timeout_occurred: bool

    # Security context
    operation: str
    parameters: Dict[str, Any]
    session_id: str
    request_id: str
    threat_level: str

    # Response guidance
    alternatives: List[str]
    restrictions: List[str]
    monitoring_required: bool
    escalation_required: bool

    # System state
    timestamp: datetime
    component_decisions: Dict[str, Any]
    performance_metrics: Dict[str, Any]

class IntegratedSecurityStreamingSystem:
    """
    Integrated system combining all security components for comprehensive
    fast-path security evaluation with streaming responses
    """

    def __init__(self,
                 cache_config: Dict[str, Any] = None,
                 timeout_config: Dict[str, Any] = None,
                 fallback_config: Dict[str, Any] = None,
                 streaming_config: Dict[str, Any] = None):

        self.logger = logging.getLogger("integrated_security")

        # Initialize all components
        cache_cfg = cache_config or {}
        self.cache = SecurityDecisionCache(
            db_path=cache_cfg.get("db_path", "integrated_security_cache.db"),
            max_entries=cache_cfg.get("max_entries", 10000),
            default_ttl_seconds=cache_cfg.get("ttl_seconds", 3600),
            eviction_policy=CacheEvictionPolicy(cache_cfg.get("eviction_policy", "adaptive"))
        )

        timeout_cfg = timeout_config or {}
        self.timeout_manager = SecurityTimeoutManager(
            default_timeout_seconds=timeout_cfg.get("default_timeout", 5.0),
            max_concurrent_operations=timeout_cfg.get("max_concurrent", 10)
        )

        fallback_cfg = fallback_config or {}
        self.fallback_engine = SecurityFallbackRuleEngine(
            db_path=fallback_cfg.get("db_path", "integrated_emergency_rules.db")
        )

        streaming_cfg = streaming_config or {}
        self.streaming_processor = SecurityStreamingProcessor(
            db_path=streaming_cfg.get("db_path", "integrated_streaming.db"),
            llm_timeout_seconds=streaming_cfg.get("llm_timeout", 3.0),
            fallback_decision=SecurityDecision.BLOCK
        )

        # Additional components
        self.ethics_foundation = SecurityEthicsFoundation()
        self.violation_handler = SecurityViolationHandler("integrated_violations.db")

        # System state
        self.system_metrics = {
            "total_requests": 0,
            "avg_response_time_ms": 0.0,
            "cache_hit_rate": 0.0,
            "fallback_usage_rate": 0.0,
            "timeout_rate": 0.0,
            "decision_accuracy": 0.0
        }

        self.logger.info("Integrated Security Streaming System initialized")

    async def evaluate_security_request(self,
                                       operation: str,
                                       parameters: Dict[str, Any],
                                       session_id: str,
                                       user_context: Dict[str, Any] = None,
                                       session_context: Dict[str, Any] = None,
                                       request_id: Optional[str] = None) -> AsyncIterator[IntegratedSecurityDecision]:
        """
        Comprehensive security evaluation with streaming responses
        Returns decisions as they become available from different components
        """

        start_time = time.time()
        self.system_metrics["total_requests"] += 1

        if request_id is None:
            request_id = f"req_{int(time.time() * 1000)}"

        user_context = user_context or {}
        session_context = session_context or {}

        component_decisions = {}
        performance_metrics = {}

        try:
            # Phase 1: Cache Check (fastest - <1ms)
            cache_decision = await self._check_cache(
                operation, parameters, user_context, session_context, request_id, session_id
            )

            if cache_decision:
                processing_time = (time.time() - start_time) * 1000
                self._update_metrics(processing_time, True, False, False)

                component_decisions["cache"] = asdict(cache_decision)
                performance_metrics["cache_time_ms"] = processing_time

                yield self._create_integrated_decision(
                    decision=cache_decision.decision.value,
                    confidence=cache_decision.confidence.value,
                    reasoning=f"Cached decision: {cache_decision.reasoning}",
                    decision_source=IntegratedDecisionSource.CACHE_HIT,
                    processing_time_ms=processing_time,
                    cache_used=True,
                    fallback_used=False,
                    timeout_occurred=False,
                    operation=operation,
                    parameters=parameters,
                    session_id=session_id,
                    request_id=request_id,
                    threat_level="cached",
                    alternatives=[],
                    restrictions=[],
                    monitoring_required=False,
                    escalation_required=False,
                    component_decisions=component_decisions,
                    performance_metrics=performance_metrics
                )
                return

            # Phase 2: Fast Rule-Based Processing (1-5ms)
            rule_start = time.time()
            rule_decision = await self._fast_rule_evaluation(
                operation, parameters, session_id, request_id
            )
            rule_time = (time.time() - rule_start) * 1000
            performance_metrics["rule_evaluation_time_ms"] = rule_time

            if rule_decision and rule_decision.decision != SecurityDecision.REVIEW:
                processing_time = (time.time() - start_time) * 1000
                self._update_metrics(processing_time, False, False, False)

                component_decisions["rule_engine"] = {
                    "decision": rule_decision.decision.value,
                    "confidence": rule_decision.confidence.value,
                    "source": rule_decision.source.value
                }

                # Cache the decision for future use
                await self._cache_decision(
                    operation, parameters, user_context, session_context,
                    rule_decision.decision.value, rule_decision.confidence.value,
                    rule_decision.reasoning, processing_time
                )

                yield self._create_integrated_decision(
                    decision=rule_decision.decision.value,
                    confidence=rule_decision.confidence.value,
                    reasoning=rule_decision.reasoning,
                    decision_source=IntegratedDecisionSource.RULE_BASED_FAST,
                    processing_time_ms=processing_time,
                    cache_used=False,
                    fallback_used=False,
                    timeout_occurred=False,
                    operation=operation,
                    parameters=parameters,
                    session_id=session_id,
                    request_id=request_id,
                    threat_level="rule_based",
                    alternatives=rule_decision.alternatives,
                    restrictions=rule_decision.restrictions,
                    monitoring_required=True,
                    escalation_required=False,
                    component_decisions=component_decisions,
                    performance_metrics=performance_metrics
                )
                return

            # Phase 3: Timeout-Managed LLM Processing (with fallbacks)
            llm_start = time.time()
            timeout_decision = await self._timeout_managed_llm_evaluation(
                operation, parameters, session_id, request_id, user_context
            )
            llm_time = (time.time() - llm_start) * 1000
            performance_metrics["llm_evaluation_time_ms"] = llm_time

            processing_time = (time.time() - start_time) * 1000
            timeout_occurred = timeout_decision.get("timeout_used", False)
            fallback_used = timeout_decision.get("decision_source") in ["timeout_handler", "fallback"]

            self._update_metrics(processing_time, False, fallback_used, timeout_occurred)

            component_decisions["llm_timeout"] = timeout_decision["result"]

            # Cache the decision
            await self._cache_decision(
                operation, parameters, user_context, session_context,
                timeout_decision["result"]["decision"],
                timeout_decision["result"].get("confidence", "medium"),
                timeout_decision["result"]["reason"],
                processing_time
            )

            yield self._create_integrated_decision(
                decision=timeout_decision["result"]["decision"],
                confidence=timeout_decision["result"].get("confidence", "medium"),
                reasoning=timeout_decision["result"]["reason"],
                decision_source=self._map_decision_source(timeout_decision["decision_source"]),
                processing_time_ms=processing_time,
                cache_used=False,
                fallback_used=fallback_used,
                timeout_occurred=timeout_occurred,
                operation=operation,
                parameters=parameters,
                session_id=session_id,
                request_id=request_id,
                threat_level=self._assess_threat_level(timeout_decision["result"]),
                alternatives=timeout_decision["result"].get("alternatives", []),
                restrictions=timeout_decision["result"].get("restrictions", []),
                monitoring_required=timeout_decision.get("monitoring_required", True),
                escalation_required=timeout_decision.get("escalated", False),
                component_decisions=component_decisions,
                performance_metrics=performance_metrics
            )

        except Exception as e:
            # Emergency fallback for any system failures
            self.logger.error(f"System error in security evaluation: {e}")

            emergency_decision = self.fallback_engine.evaluate_emergency_request(
                operation, parameters, session_id
            )

            processing_time = (time.time() - start_time) * 1000
            self._update_metrics(processing_time, False, True, False)

            component_decisions["emergency_fallback"] = asdict(emergency_decision)

            yield self._create_integrated_decision(
                decision="block" if emergency_decision.action == FallbackAction.IMMEDIATE_BLOCK else "review",
                confidence="high",
                reasoning=f"Emergency fallback: {emergency_decision.reasoning}",
                decision_source=IntegratedDecisionSource.EMERGENCY_FALLBACK,
                processing_time_ms=processing_time,
                cache_used=False,
                fallback_used=True,
                timeout_occurred=False,
                operation=operation,
                parameters=parameters,
                session_id=session_id,
                request_id=request_id,
                threat_level=emergency_decision.threat_level.value,
                alternatives=emergency_decision.safe_alternatives,
                restrictions=[],
                monitoring_required=True,
                escalation_required=emergency_decision.requires_escalation,
                component_decisions=component_decisions,
                performance_metrics=performance_metrics
            )

    async def _check_cache(self,
                          operation: str,
                          parameters: Dict[str, Any],
                          user_context: Dict[str, Any],
                          session_context: Dict[str, Any],
                          request_id: str,
                          session_id: str) -> Optional[StreamingSecurityDecision]:
        """Check cache for existing decision"""

        cache_key = self.cache.generate_cache_key(
            operation=operation,
            parameters=parameters,
            user_context=user_context,
            session_context=session_context,
            security_level="standard"
        )

        cached_entry = self.cache.get(cache_key)
        if cached_entry and cached_entry.is_valid():
            return StreamingSecurityDecision(
                decision=SecurityDecision(cached_entry.decision),
                confidence=DecisionConfidence(cached_entry.confidence.value),
                source=DecisionSource.CACHED,
                timestamp=datetime.now(),
                reasoning=cached_entry.reasoning,
                request_id=request_id,
                session_id=session_id,
                operation=operation,
                parameters=parameters,
                processing_time_ms=0.5,  # Cache access time
                is_final=True,
                alternatives=cached_entry.alternatives,
                restrictions=cached_entry.restrictions
            )

        return None

    async def _fast_rule_evaluation(self,
                                   operation: str,
                                   parameters: Dict[str, Any],
                                   session_id: str,
                                   request_id: str) -> Optional[StreamingSecurityDecision]:
        """Fast rule-based evaluation"""

        # Use the streaming processor's rule evaluator
        return self.streaming_processor.rule_evaluator.evaluate(operation, parameters)

    async def _timeout_managed_llm_evaluation(self,
                                            operation: str,
                                            parameters: Dict[str, Any],
                                            session_id: str,
                                            request_id: str,
                                            user_context: Dict[str, Any]) -> Dict[str, Any]:
        """LLM evaluation with timeout management"""

        async def llm_operation(op: str, params: Dict[str, Any]) -> Dict[str, Any]:
            """Wrapper for LLM operation"""

            # Use streaming processor for LLM evaluation
            decisions = []
            async for decision in self.streaming_processor.evaluate_security_request(
                operation=op,
                parameters=params,
                session_id=session_id,
                request_id=request_id
            ):
                decisions.append(decision)

            if decisions:
                final_decision = decisions[-1]  # Get the most complete decision
                return {
                    "decision": final_decision.decision.value,
                    "confidence": final_decision.confidence.value,
                    "reason": final_decision.reasoning,
                    "source": final_decision.source.value,
                    "alternatives": final_decision.alternatives,
                    "restrictions": final_decision.restrictions
                }
            else:
                # No decisions returned - use emergency fallback
                emergency_decision = self.fallback_engine.evaluate_emergency_request(
                    operation, parameters, session_id
                )
                return {
                    "decision": "block" if emergency_decision.action == FallbackAction.IMMEDIATE_BLOCK else "review",
                    "confidence": "medium",
                    "reason": f"Emergency fallback: {emergency_decision.reasoning}",
                    "source": "emergency_fallback",
                    "alternatives": emergency_decision.safe_alternatives,
                    "restrictions": []
                }

        # Execute with timeout management
        return await self.timeout_manager.execute_with_timeout(
            operation=operation,
            parameters=parameters,
            session_id=session_id,
            operation_func=llm_operation,
            operation_type=self._classify_operation_type(operation)
        )

    async def _cache_decision(self,
                            operation: str,
                            parameters: Dict[str, Any],
                            user_context: Dict[str, Any],
                            session_context: Dict[str, Any],
                            decision: str,
                            confidence: str,
                            reasoning: str,
                            processing_time_ms: float):
        """Cache a security decision"""

        cache_key = self.cache.generate_cache_key(
            operation=operation,
            parameters=parameters,
            user_context=user_context,
            session_context=session_context,
            security_level="standard"
        )

        # Map confidence levels
        cache_confidence_map = {
            "very_high": CacheConfidence.VERY_HIGH,
            "high": CacheConfidence.HIGH,
            "medium": CacheConfidence.MEDIUM,
            "low": CacheConfidence.LOW,
            "uncertain": CacheConfidence.UNCERTAIN
        }

        cache_confidence = cache_confidence_map.get(confidence, CacheConfidence.MEDIUM)

        self.cache.put(
            cache_key=cache_key,
            decision=decision,
            confidence=cache_confidence,
            reasoning=reasoning,
            processing_time_ms=processing_time_ms
        )

    def _create_integrated_decision(self, **kwargs) -> IntegratedSecurityDecision:
        """Create integrated security decision"""
        return IntegratedSecurityDecision(**kwargs)

    def _map_decision_source(self, source: str) -> IntegratedDecisionSource:
        """Map decision source to integrated enum"""
        mapping = {
            "normal_processing": IntegratedDecisionSource.LLM_COMPLETE,
            "timeout_handler": IntegratedDecisionSource.TIMEOUT_FALLBACK,
            "fallback": IntegratedDecisionSource.EMERGENCY_FALLBACK,
            "retry_success": IntegratedDecisionSource.LLM_STREAMING,
            "overload_handler": IntegratedDecisionSource.SYSTEM_OVERRIDE,
            "error_fallback": IntegratedDecisionSource.EMERGENCY_FALLBACK
        }
        return mapping.get(source, IntegratedDecisionSource.SYSTEM_OVERRIDE)

    def _assess_threat_level(self, decision_result: Dict[str, Any]) -> str:
        """Assess threat level from decision result"""
        decision = decision_result.get("decision", "block")
        confidence = decision_result.get("confidence", "medium")

        if decision == "block" and confidence in ["very_high", "high"]:
            return "high"
        elif decision == "block":
            return "medium"
        elif decision == "review":
            return "medium"
        else:
            return "low"

    def _classify_operation_type(self, operation: str) -> str:
        """Classify operation for timeout configuration"""
        # Use the timeout manager's classification
        return self.timeout_manager._classify_operation(operation, {})

    def _update_metrics(self, processing_time_ms: float, cache_used: bool, fallback_used: bool, timeout_occurred: bool):
        """Update system performance metrics"""

        # Update average response time
        current_avg = self.system_metrics["avg_response_time_ms"]
        total_requests = self.system_metrics["total_requests"]

        self.system_metrics["avg_response_time_ms"] = (
            (current_avg * (total_requests - 1) + processing_time_ms) / total_requests
        )

        # Update rates
        if cache_used:
            cache_hits = getattr(self, '_cache_hits', 0) + 1
            setattr(self, '_cache_hits', cache_hits)
            self.system_metrics["cache_hit_rate"] = cache_hits / total_requests

        if fallback_used:
            fallback_uses = getattr(self, '_fallback_uses', 0) + 1
            setattr(self, '_fallback_uses', fallback_uses)
            self.system_metrics["fallback_usage_rate"] = fallback_uses / total_requests

        if timeout_occurred:
            timeouts = getattr(self, '_timeouts', 0) + 1
            setattr(self, '_timeouts', timeouts)
            self.system_metrics["timeout_rate"] = timeouts / total_requests

    async def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""

        return {
            "system_metrics": self.system_metrics,
            "cache_info": self.cache.get_cache_info(),
            "cache_stats": asdict(self.cache.get_statistics()),
            "timeout_stats": self.timeout_manager.get_timeout_statistics(),
            "fallback_stats": self.fallback_engine.get_rule_statistics(),
            "streaming_stats": self.streaming_processor.get_performance_stats(),
            "timestamp": datetime.now().isoformat()
        }

    async def invalidate_cache(self, pattern: str = "*", reason: str = "manual"):
        """Invalidate cache entries"""
        self.cache.invalidate(pattern, reason)

    def shutdown(self):
        """Shutdown all components"""
        self.streaming_processor.shutdown()
        self.logger.info("Integrated Security Streaming System shutdown complete")

async def comprehensive_demo():
    """Comprehensive demonstration of the integrated security system"""

    print("🚀 Integrated Security Streaming System Demo")
    print("=" * 70)

    # Initialize system
    system = IntegratedSecurityStreamingSystem(
        cache_config={
            "max_entries": 1000,
            "ttl_seconds": 600,
            "eviction_policy": "adaptive"
        },
        timeout_config={
            "default_timeout": 3.0,
            "max_concurrent": 5
        }
    )

    # Test scenarios
    test_scenarios = [
        # Safe operations (should be fast)
        ("help", {}, {"user_id": "demo_user"}, {"session_type": "interactive"}),
        ("file_read", {"path": "config.json"}, {"user_id": "demo_user"}, {"session_type": "interactive"}),

        # Dangerous operations (should be blocked quickly)
        ("system_delete", {"path": "/", "recursive": True}, {"user_id": "demo_user"}, {"session_type": "interactive"}),
        ("../../../etc/passwd", {"access": "read"}, {"user_id": "demo_user"}, {"session_type": "interactive"}),

        # Ambiguous operations (may require LLM)
        ("network_request", {"url": "http://example.com", "method": "GET"}, {"user_id": "demo_user"}, {"session_type": "api"}),
        ("data_analysis", {"dataset": "user_behavior.csv"}, {"user_id": "demo_user"}, {"session_type": "interactive"}),

        # Repeat for cache testing
        ("help", {}, {"user_id": "demo_user"}, {"session_type": "interactive"}),
        ("file_read", {"path": "config.json"}, {"user_id": "demo_user"}, {"session_type": "interactive"}),
    ]

    print(f"Testing {len(test_scenarios)} scenarios...\n")

    total_start = time.time()

    for i, (operation, parameters, user_context, session_context) in enumerate(test_scenarios):
        print(f"{i+1}. Testing: {operation}")
        print(f"   Parameters: {parameters}")

        scenario_start = time.time()
        decisions = []

        async for decision in system.evaluate_security_request(
            operation=operation,
            parameters=parameters,
            session_id=f"demo_session_{i}",
            user_context=user_context,
            session_context=session_context,
            request_id=f"req_{i}"
        ):
            decisions.append(decision)

        scenario_time = (time.time() - scenario_start) * 1000

        if decisions:
            final_decision = decisions[-1]
            print(f"   Decision: {final_decision.decision} ({final_decision.confidence})")
            print(f"   Source: {final_decision.decision_source.value}")
            print(f"   Time: {final_decision.processing_time_ms:.1f}ms")
            print(f"   Cache Used: {final_decision.cache_used}")
            print(f"   Fallback Used: {final_decision.fallback_used}")
            print(f"   Timeout: {final_decision.timeout_occurred}")
            if final_decision.alternatives:
                print(f"   Alternatives: {', '.join(final_decision.alternatives[:2])}")
            if final_decision.escalation_required:
                print(f"   ⚠️  ESCALATION REQUIRED")
            print()
        else:
            print(f"   ❌ No decision returned\n")

    total_time = (time.time() - total_start) * 1000

    # System performance summary
    print("📊 Performance Summary")
    print("=" * 40)
    print(f"Total Test Time: {total_time:.1f}ms")
    print(f"Average per Request: {total_time / len(test_scenarios):.1f}ms")

    status = await system.get_system_status()
    print(f"Cache Hit Rate: {status['system_metrics']['cache_hit_rate']:.1%}")
    print(f"Fallback Usage: {status['system_metrics']['fallback_usage_rate']:.1%}")
    print(f"Timeout Rate: {status['system_metrics']['timeout_rate']:.1%}")
    print(f"Average Response Time: {status['system_metrics']['avg_response_time_ms']:.1f}ms")

    # Component statistics
    print(f"\n🔧 Component Statistics")
    print("=" * 40)
    print(f"Cache Entries: {status['cache_stats']['total_entries']}")
    print(f"Active Timeouts: {status['timeout_stats']['active_operations']}")
    print(f"Emergency Rules: {status['fallback_stats']['total_rules']}")

    # Cleanup
    system.shutdown()

    # Remove demo databases
    import os
    demo_files = [
        "integrated_security_cache.db", "integrated_emergency_rules.db",
        "integrated_streaming.db", "integrated_violations.db"
    ]
    for file in demo_files:
        if os.path.exists(file):
            os.remove(file)

    print("\n✅ Integrated Security System Demo Complete!")

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    asyncio.run(comprehensive_demo())