#!/usr/bin/env python3
"""
Security Response Timeout Manager
Handles timeouts and safe defaults for security decisions
"""

import asyncio
import logging
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable, Union, Awaitable
from dataclasses import dataclass, asdict
from enum import Enum
from concurrent.futures import ThreadPoolExecutor, Future, TimeoutError as FutureTimeoutError

class TimeoutSeverity(Enum):
    """Severity levels for timeout handling"""
    LOW = "low"          # Non-critical operations
    MEDIUM = "medium"    # Important but not security-critical
    HIGH = "high"        # Security-critical operations
    CRITICAL = "critical" # Emergency or safety-critical

class TimeoutAction(Enum):
    """Actions to take when timeout occurs"""
    ALLOW_DEFAULT = "allow_default"
    BLOCK_DEFAULT = "block_default"
    DEFER_TO_HUMAN = "defer_to_human"
    USE_CACHE = "use_cache"
    USE_FALLBACK_RULES = "use_fallback_rules"
    EMERGENCY_SAFE_MODE = "emergency_safe_mode"

class TimeoutReason(Enum):
    """Reasons for timeout"""
    LLM_SLOW_RESPONSE = "llm_slow_response"
    LLM_UNAVAILABLE = "llm_unavailable"
    NETWORK_TIMEOUT = "network_timeout"
    PROCESSING_TIMEOUT = "processing_timeout"
    RESOURCE_EXHAUSTION = "resource_exhaustion"
    SYSTEM_OVERLOAD = "system_overload"

@dataclass
class TimeoutConfig:
    """Configuration for timeout handling"""
    operation_type: str
    timeout_seconds: float
    severity: TimeoutSeverity
    default_action: TimeoutAction
    retry_count: int = 0
    retry_delay_seconds: float = 1.0
    escalation_threshold: int = 3
    safe_default_decision: str = "block"
    monitoring_required: bool = True

@dataclass
class TimeoutEvent:
    """Record of a timeout event"""
    event_id: str
    operation: str
    parameters: Dict[str, Any]
    timeout_config: TimeoutConfig
    timeout_reason: TimeoutReason
    occurred_at: datetime
    processing_duration_ms: float
    retry_count: int
    final_action: TimeoutAction
    decision_made: str
    session_id: str
    escalated: bool = False

@dataclass
class SafeDefaultRule:
    """Rule for determining safe defaults"""
    rule_id: str
    operation_pattern: str
    parameter_conditions: Dict[str, Any]
    default_decision: str  # "allow" or "block"
    confidence: float
    reasoning: str
    requires_monitoring: bool = True

class SecurityTimeoutManager:
    """Manages timeouts and safe defaults for security operations"""

    def __init__(self,
                 default_timeout_seconds: float = 5.0,
                 max_concurrent_operations: int = 10):

        self.logger = logging.getLogger("security_timeout")
        self.default_timeout = default_timeout_seconds
        self.max_concurrent = max_concurrent_operations

        # Configuration and state
        self.timeout_configs: Dict[str, TimeoutConfig] = {}
        self.safe_default_rules: Dict[str, SafeDefaultRule] = {}
        self.active_operations: Dict[str, asyncio.Task] = {}
        self.timeout_history: List[TimeoutEvent] = []
        self.performance_stats = {
            "total_operations": 0,
            "timeouts_occurred": 0,
            "avg_response_time_ms": 0.0,
            "escalations": 0,
            "safe_defaults_used": 0
        }

        # Thread safety
        self.lock = threading.RLock()

        # Initialize default configurations
        self._setup_default_timeout_configs()
        self._setup_safe_default_rules()

        self.logger.info("Security Timeout Manager initialized")

    def _setup_default_timeout_configs(self):
        """Setup default timeout configurations for different operation types"""

        default_configs = [
            TimeoutConfig(
                operation_type="file_read",
                timeout_seconds=2.0,
                severity=TimeoutSeverity.LOW,
                default_action=TimeoutAction.ALLOW_DEFAULT,
                retry_count=2,
                safe_default_decision="allow"
            ),
            TimeoutConfig(
                operation_type="file_write",
                timeout_seconds=3.0,
                severity=TimeoutSeverity.MEDIUM,
                default_action=TimeoutAction.BLOCK_DEFAULT,
                retry_count=1,
                safe_default_decision="block"
            ),
            TimeoutConfig(
                operation_type="system_command",
                timeout_seconds=5.0,
                severity=TimeoutSeverity.HIGH,
                default_action=TimeoutAction.USE_FALLBACK_RULES,
                retry_count=0,
                safe_default_decision="block"
            ),
            TimeoutConfig(
                operation_type="network_access",
                timeout_seconds=10.0,
                severity=TimeoutSeverity.HIGH,
                default_action=TimeoutAction.BLOCK_DEFAULT,
                retry_count=1,
                safe_default_decision="block"
            ),
            TimeoutConfig(
                operation_type="privilege_operation",
                timeout_seconds=15.0,
                severity=TimeoutSeverity.CRITICAL,
                default_action=TimeoutAction.DEFER_TO_HUMAN,
                retry_count=0,
                safe_default_decision="block"
            ),
            TimeoutConfig(
                operation_type="data_access",
                timeout_seconds=7.0,
                severity=TimeoutSeverity.MEDIUM,
                default_action=TimeoutAction.USE_CACHE,
                retry_count=1,
                safe_default_decision="block"
            ),
            TimeoutConfig(
                operation_type="help_query",
                timeout_seconds=1.0,
                severity=TimeoutSeverity.LOW,
                default_action=TimeoutAction.ALLOW_DEFAULT,
                retry_count=0,
                safe_default_decision="allow"
            )
        ]

        with self.lock:
            for config in default_configs:
                self.timeout_configs[config.operation_type] = config

    def _setup_safe_default_rules(self):
        """Setup rules for determining safe defaults"""

        safe_rules = [
            SafeDefaultRule(
                rule_id="safe_read_01",
                operation_pattern="read|view|show|list|display|cat|less|head|tail",
                parameter_conditions={"file_extension": [".txt", ".md", ".json", ".log"]},
                default_decision="allow",
                confidence=0.9,
                reasoning="Read operations on safe file types are generally safe",
                requires_monitoring=False
            ),
            SafeDefaultRule(
                rule_id="safe_info_01",
                operation_pattern="help|info|status|version|ping|echo",
                parameter_conditions={},
                default_decision="allow",
                confidence=0.95,
                reasoning="Information and help commands are safe",
                requires_monitoring=False
            ),
            SafeDefaultRule(
                rule_id="safe_calc_01",
                operation_pattern="calculate|compute|convert|format|validate",
                parameter_conditions={},
                default_decision="allow",
                confidence=0.85,
                reasoning="Calculation and formatting operations are generally safe",
                requires_monitoring=True
            ),
            SafeDefaultRule(
                rule_id="block_system_01",
                operation_pattern="delete|remove|format|destroy|kill|halt|shutdown",
                parameter_conditions={},
                default_decision="block",
                confidence=0.95,
                reasoning="Destructive operations should be blocked by default",
                requires_monitoring=True
            ),
            SafeDefaultRule(
                rule_id="block_network_01",
                operation_pattern="download|upload|connect|send|post|curl|wget",
                parameter_conditions={},
                default_decision="block",
                confidence=0.85,
                reasoning="Network operations require careful review",
                requires_monitoring=True
            ),
            SafeDefaultRule(
                rule_id="block_privilege_01",
                operation_pattern="sudo|admin|root|chmod|chown|passwd",
                parameter_conditions={},
                default_decision="block",
                confidence=0.98,
                reasoning="Privilege operations require authentication",
                requires_monitoring=True
            )
        ]

        with self.lock:
            for rule in safe_rules:
                self.safe_default_rules[rule.rule_id] = rule

    async def execute_with_timeout(self,
                                  operation: str,
                                  parameters: Dict[str, Any],
                                  session_id: str,
                                  operation_func: Callable,
                                  operation_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Execute operation with timeout handling and safe defaults
        """

        start_time = time.time()
        operation_id = f"{operation}_{int(time.time() * 1000)}"

        # Determine operation type if not specified
        if operation_type is None:
            operation_type = self._classify_operation(operation, parameters)

        # Get timeout configuration
        config = self.timeout_configs.get(operation_type, self._get_default_config())

        try:
            # Check if we're at max concurrent operations
            if len(self.active_operations) >= self.max_concurrent:
                return self._handle_overload(operation, parameters, session_id, config)

            # Execute operation with timeout
            task = asyncio.create_task(
                self._execute_operation(operation_func, operation, parameters)
            )

            with self.lock:
                self.active_operations[operation_id] = task

            try:
                result = await asyncio.wait_for(task, timeout=config.timeout_seconds)

                # Success - update stats and return
                processing_time = (time.time() - start_time) * 1000
                self._update_success_stats(processing_time)

                return {
                    "success": True,
                    "result": result,
                    "processing_time_ms": processing_time,
                    "timeout_used": False,
                    "decision_source": "normal_processing"
                }

            except asyncio.TimeoutError:
                # Timeout occurred - handle with retries and fallbacks
                return await self._handle_timeout(
                    operation, parameters, session_id, config, start_time, operation_id
                )

        except Exception as e:
            self.logger.error(f"Error executing operation {operation}: {e}")
            return self._handle_execution_error(operation, parameters, session_id, config, e)

        finally:
            # Cleanup
            with self.lock:
                if operation_id in self.active_operations:
                    if not self.active_operations[operation_id].done():
                        self.active_operations[operation_id].cancel()
                    del self.active_operations[operation_id]

    async def _execute_operation(self,
                               operation_func: Callable,
                               operation: str,
                               parameters: Dict[str, Any]) -> Any:
        """Execute the actual operation"""

        if asyncio.iscoroutinefunction(operation_func):
            return await operation_func(operation, parameters)
        else:
            # Run synchronous function in thread pool
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, operation_func, operation, parameters)

    async def _handle_timeout(self,
                            operation: str,
                            parameters: Dict[str, Any],
                            session_id: str,
                            config: TimeoutConfig,
                            start_time: float,
                            operation_id: str) -> Dict[str, Any]:
        """Handle timeout with retries and fallbacks"""

        processing_time = (time.time() - start_time) * 1000

        # Create timeout event
        timeout_event = TimeoutEvent(
            event_id=f"timeout_{int(time.time() * 1000)}",
            operation=operation,
            parameters=parameters,
            timeout_config=config,
            timeout_reason=TimeoutReason.PROCESSING_TIMEOUT,
            occurred_at=datetime.now(),
            processing_duration_ms=processing_time,
            retry_count=0,
            final_action=config.default_action,
            decision_made="pending",
            session_id=session_id
        )

        # Try retries first
        if config.retry_count > 0:
            retry_result = await self._attempt_retries(timeout_event, config)
            if retry_result["success"]:
                return retry_result

        # Apply timeout action
        return await self._apply_timeout_action(timeout_event, config)

    async def _attempt_retries(self,
                             timeout_event: TimeoutEvent,
                             config: TimeoutConfig) -> Dict[str, Any]:
        """Attempt retries with exponential backoff"""

        for retry in range(config.retry_count):
            self.logger.info(f"Retry {retry + 1}/{config.retry_count} for {timeout_event.operation}")

            # Wait before retry
            await asyncio.sleep(config.retry_delay_seconds * (2 ** retry))

            try:
                # This would be where we retry the original operation
                # For now, simulate retry logic
                await asyncio.sleep(0.1)  # Simulate quick retry

                # In real implementation, we would re-execute the operation
                # with a shorter timeout
                shorter_timeout = config.timeout_seconds * 0.8

                # Simulate success after retry
                if retry == config.retry_count - 1:  # Last retry succeeds
                    timeout_event.retry_count = retry + 1
                    return {
                        "success": True,
                        "result": {"decision": "allow", "reason": "Retry successful"},
                        "processing_time_ms": timeout_event.processing_duration_ms + (retry + 1) * 100,
                        "timeout_used": True,
                        "decision_source": "retry_success",
                        "retry_count": retry + 1
                    }

            except Exception as e:
                self.logger.warning(f"Retry {retry + 1} failed: {e}")
                continue

        # All retries failed
        timeout_event.retry_count = config.retry_count
        return {"success": False}

    async def _apply_timeout_action(self,
                                  timeout_event: TimeoutEvent,
                                  config: TimeoutConfig) -> Dict[str, Any]:
        """Apply the configured timeout action"""

        processing_time = timeout_event.processing_duration_ms

        if config.default_action == TimeoutAction.ALLOW_DEFAULT:
            decision = "allow"
            reasoning = "Timeout occurred, using safe default: allow"

        elif config.default_action == TimeoutAction.BLOCK_DEFAULT:
            decision = "block"
            reasoning = "Timeout occurred, using safe default: block"

        elif config.default_action == TimeoutAction.USE_CACHE:
            cache_result = self._get_cached_decision(timeout_event.operation, timeout_event.parameters)
            if cache_result:
                decision = cache_result["decision"]
                reasoning = f"Timeout occurred, using cached decision: {decision}"
            else:
                decision = config.safe_default_decision
                reasoning = "Timeout occurred, no cache available, using safe default"

        elif config.default_action == TimeoutAction.USE_FALLBACK_RULES:
            fallback_result = self._apply_safe_default_rules(timeout_event.operation, timeout_event.parameters)
            decision = fallback_result["decision"]
            reasoning = fallback_result["reasoning"]

        elif config.default_action == TimeoutAction.DEFER_TO_HUMAN:
            decision = "defer"
            reasoning = "Timeout occurred, deferring to human review"
            timeout_event.escalated = True

        elif config.default_action == TimeoutAction.EMERGENCY_SAFE_MODE:
            decision = "emergency_safe"
            reasoning = "Timeout occurred, entering emergency safe mode"

        else:
            decision = "block"
            reasoning = "Timeout occurred, unknown action, defaulting to block"

        # Update timeout event
        timeout_event.decision_made = decision
        timeout_event.final_action = config.default_action

        # Log timeout event
        self._log_timeout_event(timeout_event)

        # Update statistics
        self._update_timeout_stats(timeout_event)

        # Check for escalation
        if self._should_escalate_timeout(timeout_event):
            timeout_event.escalated = True
            self._escalate_timeout(timeout_event)

        return {
            "success": True,
            "result": {
                "decision": decision,
                "reason": reasoning,
                "confidence": "low",
                "source": "timeout_handler"
            },
            "processing_time_ms": processing_time,
            "timeout_used": True,
            "decision_source": config.default_action.value,
            "escalated": timeout_event.escalated,
            "monitoring_required": config.monitoring_required
        }

    def _classify_operation(self, operation: str, parameters: Dict[str, Any]) -> str:
        """Classify operation type for timeout configuration"""

        operation_lower = operation.lower()

        # File operations
        if any(keyword in operation_lower for keyword in ["read", "write", "file", "open", "save"]):
            if any(keyword in operation_lower for keyword in ["write", "save", "create", "modify"]):
                return "file_write"
            else:
                return "file_read"

        # System operations
        if any(keyword in operation_lower for keyword in ["system", "command", "execute", "run", "sudo", "admin"]):
            return "system_command"

        # Network operations
        if any(keyword in operation_lower for keyword in ["network", "http", "download", "upload", "connect"]):
            return "network_access"

        # Privilege operations
        if any(keyword in operation_lower for keyword in ["privilege", "permission", "auth", "login", "password"]):
            return "privilege_operation"

        # Data access
        if any(keyword in operation_lower for keyword in ["database", "data", "query", "select", "insert"]):
            return "data_access"

        # Help queries
        if any(keyword in operation_lower for keyword in ["help", "info", "status", "version"]):
            return "help_query"

        # Default to system command for unknown operations
        return "system_command"

    def _get_cached_decision(self, operation: str, parameters: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Get cached decision if available"""
        # This would integrate with the caching system
        # For demo purposes, return None
        return None

    def _apply_safe_default_rules(self, operation: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Apply safe default rules to determine decision"""

        import re

        operation_text = f"{operation} {' '.join(str(v) for v in parameters.values())}"

        # Check rules in order of confidence
        with self.lock:
            sorted_rules = sorted(self.safe_default_rules.values(),
                                key=lambda r: r.confidence, reverse=True)

            for rule in sorted_rules:
                if re.search(rule.operation_pattern, operation_text, re.IGNORECASE):
                    # Check parameter conditions
                    if self._check_parameter_conditions(parameters, rule.parameter_conditions):
                        return {
                            "decision": rule.default_decision,
                            "reasoning": f"Safe default rule applied: {rule.reasoning}",
                            "confidence": rule.confidence,
                            "rule_id": rule.rule_id,
                            "monitoring_required": rule.requires_monitoring
                        }

        # No rules matched - use conservative default
        return {
            "decision": "block",
            "reasoning": "No safe default rules matched, using conservative default",
            "confidence": 0.5,
            "rule_id": "default_conservative",
            "monitoring_required": True
        }

    def _check_parameter_conditions(self,
                                  parameters: Dict[str, Any],
                                  conditions: Dict[str, Any]) -> bool:
        """Check if parameters match rule conditions"""

        if not conditions:
            return True

        for key, expected_values in conditions.items():
            if key in parameters:
                param_value = parameters[key]
                if isinstance(expected_values, list):
                    if not any(exp_val in str(param_value) for exp_val in expected_values):
                        return False
                else:
                    if expected_values not in str(param_value):
                        return False

        return True

    def _get_default_config(self) -> TimeoutConfig:
        """Get default timeout configuration"""
        return TimeoutConfig(
            operation_type="unknown",
            timeout_seconds=self.default_timeout,
            severity=TimeoutSeverity.MEDIUM,
            default_action=TimeoutAction.BLOCK_DEFAULT,
            safe_default_decision="block"
        )

    def _handle_overload(self,
                        operation: str,
                        parameters: Dict[str, Any],
                        session_id: str,
                        config: TimeoutConfig) -> Dict[str, Any]:
        """Handle system overload situation"""

        self.logger.warning(f"System overload, rejecting operation: {operation}")

        return {
            "success": False,
            "result": {
                "decision": "block",
                "reason": "System overload - too many concurrent operations",
                "confidence": "high",
                "source": "overload_protection"
            },
            "processing_time_ms": 0,
            "timeout_used": False,
            "decision_source": "overload_handler",
            "escalated": True,
            "monitoring_required": True
        }

    def _handle_execution_error(self,
                              operation: str,
                              parameters: Dict[str, Any],
                              session_id: str,
                              config: TimeoutConfig,
                              error: Exception) -> Dict[str, Any]:
        """Handle execution errors"""

        self.logger.error(f"Execution error for {operation}: {error}")

        return {
            "success": False,
            "result": {
                "decision": config.safe_default_decision,
                "reason": f"Execution error occurred: {str(error)}",
                "confidence": "low",
                "source": "error_handler"
            },
            "processing_time_ms": 0,
            "timeout_used": False,
            "decision_source": "error_fallback",
            "escalated": True,
            "monitoring_required": True
        }

    def _should_escalate_timeout(self, timeout_event: TimeoutEvent) -> bool:
        """Determine if timeout should be escalated"""

        escalation_conditions = [
            timeout_event.timeout_config.severity == TimeoutSeverity.CRITICAL,
            timeout_event.retry_count >= timeout_event.timeout_config.escalation_threshold,
            timeout_event.final_action == TimeoutAction.DEFER_TO_HUMAN
        ]

        return any(escalation_conditions)

    def _escalate_timeout(self, timeout_event: TimeoutEvent):
        """Escalate timeout to human oversight"""

        self.logger.critical(f"TIMEOUT ESCALATION: {timeout_event.operation} - {timeout_event.timeout_reason.value}")

        # In real implementation, this would:
        # - Send alert to administrators
        # - Log to escalation system
        # - Potentially trigger emergency procedures

        with self.lock:
            self.performance_stats["escalations"] += 1

    def _log_timeout_event(self, timeout_event: TimeoutEvent):
        """Log timeout event for analysis"""

        with self.lock:
            self.timeout_history.append(timeout_event)

            # Keep only recent history
            if len(self.timeout_history) > 1000:
                self.timeout_history = self.timeout_history[-1000:]

        self.logger.warning(f"Timeout: {timeout_event.operation} ({timeout_event.timeout_reason.value})")

    def _update_success_stats(self, processing_time_ms: float):
        """Update statistics for successful operations"""

        with self.lock:
            self.performance_stats["total_operations"] += 1

            # Update average response time
            current_avg = self.performance_stats["avg_response_time_ms"]
            total_ops = self.performance_stats["total_operations"]

            self.performance_stats["avg_response_time_ms"] = (
                (current_avg * (total_ops - 1) + processing_time_ms) / total_ops
            )

    def _update_timeout_stats(self, timeout_event: TimeoutEvent):
        """Update statistics for timeout events"""

        with self.lock:
            self.performance_stats["total_operations"] += 1
            self.performance_stats["timeouts_occurred"] += 1

            if timeout_event.decision_made in ["allow", "block"]:
                self.performance_stats["safe_defaults_used"] += 1

    def get_timeout_statistics(self) -> Dict[str, Any]:
        """Get timeout and performance statistics"""

        with self.lock:
            recent_timeouts = [
                event for event in self.timeout_history
                if (datetime.now() - event.occurred_at).total_seconds() < 3600
            ]

            timeout_by_reason = {}
            for event in recent_timeouts:
                reason = event.timeout_reason.value
                timeout_by_reason[reason] = timeout_by_reason.get(reason, 0) + 1

            return {
                "performance_stats": self.performance_stats.copy(),
                "recent_timeouts_1h": len(recent_timeouts),
                "timeout_by_reason": timeout_by_reason,
                "active_operations": len(self.active_operations),
                "configured_operation_types": len(self.timeout_configs),
                "safe_default_rules": len(self.safe_default_rules)
            }

    def update_timeout_config(self, operation_type: str, config: TimeoutConfig):
        """Update timeout configuration for an operation type"""

        with self.lock:
            self.timeout_configs[operation_type] = config

        self.logger.info(f"Updated timeout config for {operation_type}")

    def add_safe_default_rule(self, rule: SafeDefaultRule):
        """Add new safe default rule"""

        with self.lock:
            self.safe_default_rules[rule.rule_id] = rule

        self.logger.info(f"Added safe default rule: {rule.rule_id}")

    def get_system_status(self) -> Dict[str, Any]:
        """Get current system status"""

        return {
            "active_operations": len(self.active_operations),
            "max_concurrent": self.max_concurrent,
            "default_timeout": self.default_timeout,
            "total_configs": len(self.timeout_configs),
            "total_safe_rules": len(self.safe_default_rules),
            "uptime": "system_uptime_here",  # Would calculate actual uptime
            "last_update": datetime.now().isoformat()
        }

async def demo_timeout_manager():
    """Demonstrate timeout manager functionality"""

    manager = SecurityTimeoutManager(default_timeout_seconds=2.0)

    # Mock operation functions
    async def fast_operation(operation: str, parameters: Dict[str, Any]):
        await asyncio.sleep(0.5)
        return {"decision": "allow", "reason": "Fast operation completed"}

    async def slow_operation(operation: str, parameters: Dict[str, Any]):
        await asyncio.sleep(5.0)  # Will timeout
        return {"decision": "allow", "reason": "Slow operation completed"}

    def sync_operation(operation: str, parameters: Dict[str, Any]):
        time.sleep(1.0)
        return {"decision": "allow", "reason": "Sync operation completed"}

    test_cases = [
        ("file_read", {"path": "config.txt"}, fast_operation),
        ("system_command", {"cmd": "ls -la"}, slow_operation),
        ("help", {}, sync_operation),
        ("network_access", {"url": "http://example.com"}, slow_operation),
        ("privilege_operation", {"action": "sudo"}, slow_operation)
    ]

    print("⏰ Security Timeout Manager Demo")
    print("=" * 60)

    for i, (operation, parameters, operation_func) in enumerate(test_cases):
        print(f"\n{i+1}. Testing: {operation}")
        print(f"   Parameters: {parameters}")

        result = await manager.execute_with_timeout(
            operation=operation,
            parameters=parameters,
            session_id=f"demo_session_{i}",
            operation_func=operation_func
        )

        print(f"   Result: {result['result']['decision']}")
        print(f"   Reason: {result['result']['reason']}")
        print(f"   Processing Time: {result['processing_time_ms']:.1f}ms")
        print(f"   Timeout Used: {result['timeout_used']}")
        print(f"   Source: {result['decision_source']}")
        if result.get('escalated'):
            print(f"   ⚠️  ESCALATED")

    print(f"\n📊 System Statistics:")
    stats = manager.get_timeout_statistics()
    for key, value in stats["performance_stats"].items():
        print(f"   {key}: {value}")

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    asyncio.run(demo_timeout_manager())