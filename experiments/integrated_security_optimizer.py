#!/usr/bin/env python3
"""
Integrated Security Optimizer
Complete integration of all optimization components with existing security systems
"""

import asyncio
import json
import logging
import sqlite3
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable, AsyncIterator, Union, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
from concurrent.futures import ThreadPoolExecutor
import hashlib

try:
    # Import optimization components
    from security_event_templates import SecurityEventClassifier, ContextCompressor, EventCategory
    from security_batch_processor import SecurityBatchProcessor, BatchStrategy, ProcessingMode
    from security_context_optimizer import ContextCompressor as AdvancedCompressor, OptimizationTarget
    from security_llm_optimizer import SecurityLLMOptimizer, TokenBudget, QualityMetric

    # Import existing security components
    from enhanced_security_logging import (
        EnhancedSecurityLogger, SecurityEventType, SecuritySeverity, SecurityEvent
    )
    from security_streaming_processor import (
        SecurityStreamingProcessor, StreamingSecurityDecision, SecurityDecision
    )
    from security_violation_handler import SecurityViolationHandler
    from security_ethics_foundation import SecurityEthicsFoundation
except ImportError as e:
    print(f"Warning: Could not import all components: {e}")

class OptimizationMode(Enum):
    """Optimization operation modes"""
    PERFORMANCE = "performance"        # Optimize for speed
    EFFICIENCY = "efficiency"          # Optimize for token usage
    QUALITY = "quality"               # Optimize for analysis quality
    BALANCED = "balanced"             # Balance all factors
    EMERGENCY = "emergency"           # Emergency/minimal processing

class ProcessingPipeline(Enum):
    """Processing pipeline configurations"""
    REAL_TIME = "real_time"           # Immediate processing
    BATCH_OPTIMIZED = "batch_optimized" # Batch processing
    HYBRID = "hybrid"                 # Adaptive pipeline selection
    STREAMING = "streaming"           # Streaming with optimization

@dataclass
class OptimizationConfig:
    """Configuration for optimization system"""
    mode: OptimizationMode
    pipeline: ProcessingPipeline
    token_budget: TokenBudget
    quality_threshold: float
    batch_size_limit: int
    cache_enabled: bool
    compression_level: int
    template_matching: bool
    performance_monitoring: bool

@dataclass
class ProcessingResult:
    """Comprehensive processing result"""
    event_id: str
    decision: str
    confidence: str
    reasoning: str
    alternatives: List[str]

    # Optimization metrics
    original_tokens: int
    optimized_tokens: int
    token_savings: int
    processing_time_ms: float
    quality_score: float

    # Processing metadata
    pipeline_used: str
    optimization_applied: List[str]
    cache_hit: bool
    template_matched: bool
    batch_processed: bool

    # Security metadata
    risk_assessment: Dict[str, float]
    escalation_required: bool
    monitoring_flags: List[str]

class IntegratedSecurityOptimizer:
    """Complete security optimization system"""

    def __init__(self,
                 config: OptimizationConfig = None,
                 db_path: str = "integrated_security_optimizer.db"):

        self.db_path = db_path
        self.logger = logging.getLogger("integrated_security_optimizer")

        # Configuration
        self.config = config or self._get_default_config()

        # Initialize optimization components
        self.event_classifier = SecurityEventClassifier()
        self.context_compressor = AdvancedCompressor()
        self.batch_processor = SecurityBatchProcessor()
        self.llm_optimizer = SecurityLLMOptimizer()

        # Initialize existing security components
        self.security_logger = EnhancedSecurityLogger()
        self.streaming_processor = SecurityStreamingProcessor()
        self.violation_handler = SecurityViolationHandler()
        self.ethics_foundation = SecurityEthicsFoundation()

        # Processing state
        self.processing_stats = {
            "total_events": 0,
            "optimized_events": 0,
            "avg_token_savings": 0.0,
            "avg_quality_score": 0.0,
            "avg_processing_time": 0.0,
            "cache_hit_rate": 0.0,
            "optimization_success_rate": 0.0
        }

        # Thread management
        self.executor = ThreadPoolExecutor(max_workers=8, thread_name_prefix="sec_optimizer")
        self.processing_lock = threading.RLock()

        # Initialize database
        self._init_database()

        # Setup integration hooks
        self._setup_integration_hooks()

        self.logger.info("Integrated Security Optimizer initialized")

    def _get_default_config(self) -> OptimizationConfig:
        """Get default optimization configuration"""
        return OptimizationConfig(
            mode=OptimizationMode.BALANCED,
            pipeline=ProcessingPipeline.HYBRID,
            token_budget=TokenBudget.STANDARD,
            quality_threshold=0.85,
            batch_size_limit=50,
            cache_enabled=True,
            compression_level=2,
            template_matching=True,
            performance_monitoring=True
        )

    def _init_database(self):
        """Initialize integrated optimization database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS processing_results (
                event_id TEXT PRIMARY KEY,
                decision TEXT,
                confidence TEXT,
                reasoning TEXT,
                original_tokens INTEGER,
                optimized_tokens INTEGER,
                token_savings INTEGER,
                processing_time_ms REAL,
                quality_score REAL,
                pipeline_used TEXT,
                optimization_applied TEXT,
                cache_hit BOOLEAN,
                template_matched BOOLEAN,
                batch_processed BOOLEAN,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS optimization_metrics (
                timestamp TEXT PRIMARY KEY,
                total_events INTEGER,
                optimized_events INTEGER,
                avg_token_savings REAL,
                avg_quality_score REAL,
                avg_processing_time REAL,
                cache_hit_rate REAL,
                optimization_success_rate REAL
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS pipeline_performance (
                pipeline_name TEXT,
                event_count INTEGER,
                avg_processing_time REAL,
                avg_quality_score REAL,
                success_rate REAL,
                last_updated TEXT,
                PRIMARY KEY (pipeline_name, last_updated)
            )
        """)

        conn.commit()
        conn.close()

    def _setup_integration_hooks(self):
        """Setup integration with existing security components"""

        # Hook into security logger for event optimization
        self.security_logger.register_event_callback(self._on_security_event)

        # Hook into streaming processor for optimization
        original_evaluate = self.streaming_processor.evaluate_security_request

        async def optimized_evaluate(operation, parameters, session_id, request_id=None):
            # Apply optimization before streaming evaluation
            event_data = {
                "event_type": "permission_check",
                "operation": operation,
                "parameters": parameters,
                "session_id": session_id,
                "request_id": request_id
            }

            # If optimization is enabled, process through optimizer
            if self.config.pipeline in [ProcessingPipeline.HYBRID, ProcessingPipeline.STREAMING]:
                optimized_result = await self.process_security_event(event_data)

                # Convert to streaming format
                async def yield_optimized():
                    yield StreamingSecurityDecision(
                        decision=SecurityDecision(optimized_result.decision),
                        confidence=optimized_result.confidence,
                        source=f"optimized_{optimized_result.pipeline_used}",
                        timestamp=datetime.now(),
                        reasoning=optimized_result.reasoning,
                        request_id=request_id or "",
                        session_id=session_id,
                        operation=operation,
                        parameters=parameters,
                        processing_time_ms=optimized_result.processing_time_ms,
                        is_final=True,
                        alternatives=optimized_result.alternatives
                    )

                return yield_optimized()
            else:
                # Use original evaluation
                return original_evaluate(operation, parameters, session_id, request_id)

        # Replace the method
        self.streaming_processor.evaluate_security_request = optimized_evaluate

    def _on_security_event(self, event: SecurityEvent):
        """Handle security events for optimization"""
        if self.config.pipeline == ProcessingPipeline.BATCH_OPTIMIZED:
            # Queue for batch processing
            event_data = {
                "event_id": event.event_id,
                "event_type": event.event_type.value,
                "operation": event.operation,
                "parameters": event.parameters,
                "context": event.context,
                "user_id": event.user_id,
                "session_id": event.session_id,
                "risk_score": event.risk_score,
                "severity": event.severity.value
            }

            asyncio.create_task(self.batch_processor.add_event(event_data))

    async def process_security_event(self, event_data: Dict[str, Any]) -> ProcessingResult:
        """Process security event with full optimization"""

        start_time = time.time()
        event_id = event_data.get("event_id", f"evt_{int(time.time() * 1000)}")

        try:
            # Step 1: Select optimal processing pipeline
            pipeline = self._select_pipeline(event_data)

            # Step 2: Apply optimization pipeline
            if pipeline == "real_time_optimized":
                result = await self._process_real_time_optimized(event_data)
            elif pipeline == "batch_optimized":
                result = await self._process_batch_optimized(event_data)
            elif pipeline == "streaming_optimized":
                result = await self._process_streaming_optimized(event_data)
            else:  # fallback
                result = await self._process_fallback(event_data)

            # Step 3: Enhance with security analysis
            result = await self._enhance_with_security_analysis(result, event_data)

            # Step 4: Quality assurance
            result = await self._apply_quality_assurance(result)

            # Step 5: Update metrics and logging
            processing_time = (time.time() - start_time) * 1000
            result.processing_time_ms = processing_time

            await self._update_processing_stats(result)
            await self._store_processing_result(result)

            # Step 6: Trigger any necessary security actions
            await self._handle_security_actions(result, event_data)

            return result

        except Exception as e:
            self.logger.error(f"Error processing event {event_id}: {e}")
            return await self._create_error_result(event_id, str(e), time.time() - start_time)

    def _select_pipeline(self, event_data: Dict[str, Any]) -> str:
        """Select optimal processing pipeline based on event and configuration"""

        if self.config.pipeline == ProcessingPipeline.REAL_TIME:
            return "real_time_optimized"
        elif self.config.pipeline == ProcessingPipeline.BATCH_OPTIMIZED:
            return "batch_optimized"
        elif self.config.pipeline == ProcessingPipeline.STREAMING:
            return "streaming_optimized"
        else:  # HYBRID
            # Intelligent pipeline selection
            risk_score = event_data.get("risk_score", 0.5)
            severity = event_data.get("severity", 2)

            # High-risk events get real-time processing
            if risk_score > 0.8 or severity >= 5:
                return "real_time_optimized"
            # Batch similar events
            elif self._should_batch_event(event_data):
                return "batch_optimized"
            # Default to streaming
            else:
                return "streaming_optimized"

    def _should_batch_event(self, event_data: Dict[str, Any]) -> bool:
        """Determine if event should be batch processed"""

        # Check if we have similar pending events
        operation = event_data.get("operation", "")
        event_type = event_data.get("event_type", "")

        # Simple heuristic: batch file operations and routine checks
        return any(op in operation.lower() for op in ["file_read", "list", "check", "validate"])

    async def _process_real_time_optimized(self, event_data: Dict[str, Any]) -> ProcessingResult:
        """Process with real-time optimization"""

        # Use LLM optimizer with minimal token budget for speed
        optimization_result = await self.llm_optimizer.optimize_security_analysis(
            event_data,
            token_budget=TokenBudget.COMPACT,
            quality_target=0.80
        )

        analysis = optimization_result["analysis_result"]
        metrics = optimization_result["optimization_metrics"]
        quality = optimization_result["quality_assessment"]

        return ProcessingResult(
            event_id=event_data.get("event_id", "unknown"),
            decision=analysis["decision"],
            confidence=analysis.get("confidence", "medium"),
            reasoning=analysis.get("reasoning", ""),
            alternatives=analysis.get("alternatives", []),
            original_tokens=metrics["original_tokens"],
            optimized_tokens=metrics["optimized_tokens"],
            token_savings=metrics["token_savings"],
            processing_time_ms=0,  # Will be set later
            quality_score=quality["overall_quality"],
            pipeline_used="real_time_optimized",
            optimization_applied=["llm_optimization", "context_compression"],
            cache_hit=analysis.get("source") == "cached_reasoning",
            template_matched=True,
            batch_processed=False,
            risk_assessment=analysis.get("risk_assessment", {}),
            escalation_required=quality["overall_quality"] < 0.7,
            monitoring_flags=[]
        )

    async def _process_batch_optimized(self, event_data: Dict[str, Any]) -> ProcessingResult:
        """Process with batch optimization"""

        # Add to batch processor
        await self.batch_processor.add_event(event_data)

        # For demo, simulate batch processing result
        template = self.event_classifier.classify_event(event_data)

        if template:
            compressed_context, _ = self.context_compressor.compress_context(
                event_data, OptimizationTarget.EFFICIENCY
            )

            # Simple template-based decision
            decision = "allow" if event_data.get("risk_score", 0.5) < 0.6 else "block"
            confidence = "high" if template else "medium"
            reasoning = f"Batch-processed using template {template.name if template else 'default'}"

            return ProcessingResult(
                event_id=event_data.get("event_id", "unknown"),
                decision=decision,
                confidence=confidence,
                reasoning=reasoning,
                alternatives=[],
                original_tokens=len(json.dumps(event_data)) // 4,
                optimized_tokens=len(json.dumps(compressed_context)) // 4,
                token_savings=50,  # Estimate
                processing_time_ms=0,
                quality_score=0.82,
                pipeline_used="batch_optimized",
                optimization_applied=["batch_processing", "template_matching", "context_compression"],
                cache_hit=False,
                template_matched=template is not None,
                batch_processed=True,
                risk_assessment={"level": "low"},
                escalation_required=False,
                monitoring_flags=[]
            )
        else:
            return await self._process_fallback(event_data)

    async def _process_streaming_optimized(self, event_data: Dict[str, Any]) -> ProcessingResult:
        """Process with streaming optimization"""

        # Use streaming processor with optimization
        decisions = []
        async for decision in self.streaming_processor.evaluate_security_request(
            event_data.get("operation", ""),
            event_data.get("parameters", {}),
            event_data.get("session_id", "")
        ):
            decisions.append(decision)
            break  # Take first decision for demo

        if decisions:
            decision = decisions[0]
            return ProcessingResult(
                event_id=event_data.get("event_id", "unknown"),
                decision=decision.decision.value,
                confidence=decision.confidence.value,
                reasoning=decision.reasoning,
                alternatives=decision.alternatives,
                original_tokens=200,  # Estimate
                optimized_tokens=150,  # Estimate
                token_savings=50,
                processing_time_ms=decision.processing_time_ms,
                quality_score=0.85,
                pipeline_used="streaming_optimized",
                optimization_applied=["streaming_processing", "rule_based_evaluation"],
                cache_hit=decision.source.value == "cached",
                template_matched=True,
                batch_processed=False,
                risk_assessment={"level": "medium"},
                escalation_required=False,
                monitoring_flags=[]
            )
        else:
            return await self._process_fallback(event_data)

    async def _process_fallback(self, event_data: Dict[str, Any]) -> ProcessingResult:
        """Fallback processing when optimization fails"""

        risk_score = event_data.get("risk_score", 0.5)
        operation = event_data.get("operation", "unknown")

        # Simple fallback logic
        if risk_score > 0.8:
            decision = "block"
            confidence = "high"
            reasoning = f"High risk operation {operation} blocked by fallback security policy"
        elif risk_score > 0.5:
            decision = "allow_with_monitoring"
            confidence = "medium"
            reasoning = f"Medium risk operation {operation} allowed with monitoring"
        else:
            decision = "allow"
            confidence = "high"
            reasoning = f"Low risk operation {operation} allowed"

        return ProcessingResult(
            event_id=event_data.get("event_id", "unknown"),
            decision=decision,
            confidence=confidence,
            reasoning=reasoning,
            alternatives=[],
            original_tokens=100,
            optimized_tokens=100,
            token_savings=0,
            processing_time_ms=0,
            quality_score=0.75,
            pipeline_used="fallback",
            optimization_applied=["fallback_processing"],
            cache_hit=False,
            template_matched=False,
            batch_processed=False,
            risk_assessment={"level": "low" if risk_score < 0.5 else "medium"},
            escalation_required=risk_score > 0.9,
            monitoring_flags=["fallback_used"]
        )

    async def _enhance_with_security_analysis(self, result: ProcessingResult, event_data: Dict[str, Any]) -> ProcessingResult:
        """Enhance result with additional security analysis"""

        # Check ethical boundaries
        ethical_violation = self.ethics_foundation.evaluate_ethical_boundaries(
            event_data.get("operation", ""), event_data.get("context", {})
        )

        if ethical_violation:
            result.decision = "block"
            result.reasoning += f" Ethical concern: {ethical_violation.description}"
            result.escalation_required = True
            result.monitoring_flags.append("ethical_violation")

        # Add risk assessment details
        risk_score = event_data.get("risk_score", 0.5)
        result.risk_assessment.update({
            "risk_score": risk_score,
            "risk_level": "high" if risk_score > 0.7 else "medium" if risk_score > 0.4 else "low",
            "security_concerns": self._identify_security_concerns(event_data)
        })

        return result

    def _identify_security_concerns(self, event_data: Dict[str, Any]) -> List[str]:
        """Identify security concerns in event data"""
        concerns = []

        operation = event_data.get("operation", "").lower()
        resource = event_data.get("resource", "").lower()
        parameters = event_data.get("parameters", {})

        # Check for common security concerns
        if "../" in resource or "..\\" in resource:
            concerns.append("path_traversal_attempt")

        if any(term in operation for term in ["delete", "remove", "format", "destroy"]):
            concerns.append("destructive_operation")

        if any(term in operation for term in ["admin", "root", "sudo", "privilege"]):
            concerns.append("privilege_operation")

        if "password" in str(parameters).lower() or "token" in str(parameters).lower():
            concerns.append("credential_handling")

        return concerns

    async def _apply_quality_assurance(self, result: ProcessingResult) -> ProcessingResult:
        """Apply quality assurance checks"""

        # Check if quality meets threshold
        if result.quality_score < self.config.quality_threshold:
            result.monitoring_flags.append("quality_below_threshold")

            # If quality is very low, escalate
            if result.quality_score < 0.6:
                result.escalation_required = True
                result.monitoring_flags.append("low_quality_escalation")

        # Check for consistency
        if result.decision == "allow" and result.risk_assessment.get("risk_score", 0) > 0.8:
            result.monitoring_flags.append("inconsistent_decision")
            result.escalation_required = True

        return result

    async def _handle_security_actions(self, result: ProcessingResult, event_data: Dict[str, Any]):
        """Handle any required security actions"""

        # Log the decision
        event_type = SecurityEventType.PERMISSION_CHECK
        if result.decision == "block":
            event_type = SecurityEventType.ACCESS_DENIED
        elif result.decision == "allow":
            event_type = SecurityEventType.ACCESS_GRANTED

        severity = SecuritySeverity.WARNING if result.escalation_required else SecuritySeverity.INFO

        self.security_logger.log_security_event(
            event_type=event_type,
            severity=severity,
            description=f"Optimized security decision: {result.decision}",
            source_component="integrated_optimizer",
            source_function="process_security_event",
            user_id=event_data.get("user_id"),
            session_id=event_data.get("session_id"),
            operation=event_data.get("operation"),
            decision=result.decision,
            reason=result.reasoning
        )

        # Handle violations
        if result.decision == "block" or result.escalation_required:
            # Create mock permission check for violation handler
            from command_whitelist_system import PermissionCheck, SecurityRisk, PermissionLevel

            permission_check = PermissionCheck(
                allowed=result.decision == "allow",
                operation=event_data.get("operation", ""),
                reason=result.reasoning,
                risk_level=SecurityRisk.HIGH if result.escalation_required else SecurityRisk.MEDIUM,
                alternative_suggestions=result.alternatives,
                required_permission=PermissionLevel.AUTHENTICATED,
                user_permission=PermissionLevel.GUEST
            )

            self.violation_handler.handle_permission_violation(
                permission_check,
                event_data.get("session_id", ""),
                event_data.get("context", {})
            )

    async def _update_processing_stats(self, result: ProcessingResult):
        """Update processing statistics"""

        with self.processing_lock:
            self.processing_stats["total_events"] += 1

            if result.token_savings > 0:
                self.processing_stats["optimized_events"] += 1

            total = self.processing_stats["total_events"]

            # Update averages
            self.processing_stats["avg_token_savings"] = (
                (self.processing_stats["avg_token_savings"] * (total - 1) + result.token_savings) / total
            )

            self.processing_stats["avg_quality_score"] = (
                (self.processing_stats["avg_quality_score"] * (total - 1) + result.quality_score) / total
            )

            self.processing_stats["avg_processing_time"] = (
                (self.processing_stats["avg_processing_time"] * (total - 1) + result.processing_time_ms) / total
            )

            # Cache hit rate
            cache_hits = getattr(self, '_cache_hits', 0)
            if result.cache_hit:
                cache_hits += 1
                setattr(self, '_cache_hits', cache_hits)

            self.processing_stats["cache_hit_rate"] = cache_hits / total

            # Optimization success rate
            optimized = self.processing_stats["optimized_events"]
            self.processing_stats["optimization_success_rate"] = optimized / total

    async def _store_processing_result(self, result: ProcessingResult):
        """Store processing result in database"""

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT OR REPLACE INTO processing_results
            (event_id, decision, confidence, reasoning, original_tokens, optimized_tokens,
             token_savings, processing_time_ms, quality_score, pipeline_used,
             optimization_applied, cache_hit, template_matched, batch_processed)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            result.event_id,
            result.decision,
            result.confidence,
            result.reasoning,
            result.original_tokens,
            result.optimized_tokens,
            result.token_savings,
            result.processing_time_ms,
            result.quality_score,
            result.pipeline_used,
            json.dumps(result.optimization_applied),
            result.cache_hit,
            result.template_matched,
            result.batch_processed
        ))

        conn.commit()
        conn.close()

    async def _create_error_result(self, event_id: str, error: str, processing_time: float) -> ProcessingResult:
        """Create error result"""

        return ProcessingResult(
            event_id=event_id,
            decision="block",
            confidence="low",
            reasoning=f"Processing error occurred: {error}. Defaulting to block for safety.",
            alternatives=["Contact system administrator", "Retry with different parameters"],
            original_tokens=0,
            optimized_tokens=0,
            token_savings=0,
            processing_time_ms=processing_time * 1000,
            quality_score=0.0,
            pipeline_used="error_handler",
            optimization_applied=["error_handling"],
            cache_hit=False,
            template_matched=False,
            batch_processed=False,
            risk_assessment={"level": "unknown"},
            escalation_required=True,
            monitoring_flags=["processing_error"]
        )

    def get_optimization_stats(self) -> Dict[str, Any]:
        """Get comprehensive optimization statistics"""

        with self.processing_lock:
            stats = self.processing_stats.copy()

        # Add component statistics
        stats.update({
            "llm_optimizer_stats": self.llm_optimizer.get_optimization_stats(),
            "context_compressor_stats": self.context_compressor.get_optimization_stats(),
            "batch_processor_stats": self.batch_processor.get_processing_metrics(),
            "classification_stats": self.event_classifier.get_classification_stats()
        })

        return stats

    def get_system_status(self) -> Dict[str, Any]:
        """Get system status"""

        return {
            "configuration": asdict(self.config),
            "processing_stats": self.processing_stats,
            "component_status": {
                "event_classifier": "active",
                "context_compressor": "active",
                "batch_processor": "active",
                "llm_optimizer": "active",
                "security_logger": "active",
                "streaming_processor": "active"
            },
            "performance_metrics": {
                "avg_token_efficiency": self.processing_stats["avg_token_savings"] / max(self.processing_stats["avg_processing_time"], 1),
                "quality_efficiency": self.processing_stats["avg_quality_score"] / max(self.processing_stats["avg_processing_time"], 1),
                "optimization_effectiveness": self.processing_stats["optimization_success_rate"]
            }
        }

    async def shutdown(self):
        """Shutdown the integrated optimizer"""

        self.executor.shutdown(wait=True)
        self.batch_processor.shutdown()
        self.streaming_processor.shutdown()
        self.security_logger.stop()

        self.logger.info("Integrated Security Optimizer shutdown complete")

async def demo_integrated_optimizer():
    """Demonstrate the integrated security optimizer"""

    print("🚀 Integrated Security Optimizer Demo")
    print("=" * 70)

    # Test different configurations
    configs = [
        OptimizationConfig(
            mode=OptimizationMode.PERFORMANCE,
            pipeline=ProcessingPipeline.REAL_TIME,
            token_budget=TokenBudget.COMPACT,
            quality_threshold=0.80,
            batch_size_limit=10,
            cache_enabled=True,
            compression_level=2,
            template_matching=True,
            performance_monitoring=True
        ),
        OptimizationConfig(
            mode=OptimizationMode.EFFICIENCY,
            pipeline=ProcessingPipeline.BATCH_OPTIMIZED,
            token_budget=TokenBudget.MINIMAL,
            quality_threshold=0.75,
            batch_size_limit=50,
            cache_enabled=True,
            compression_level=3,
            template_matching=True,
            performance_monitoring=True
        )
    ]

    test_events = [
        {
            "event_id": "evt_001",
            "event_type": "permission_check",
            "operation": "file_read",
            "resource": "/home/user/document.pdf",
            "user_id": "user123",
            "session_id": "sess_001",
            "parameters": {"file_size": "2MB", "file_type": "pdf"},
            "context": {"department": "finance"},
            "risk_score": 0.3,
            "severity": 2
        },
        {
            "event_id": "evt_002",
            "event_type": "security_violation",
            "operation": "path_traversal",
            "resource": "../../../etc/passwd",
            "user_id": "user456",
            "session_id": "sess_002",
            "parameters": {"attempted_path": "../../../etc/passwd"},
            "context": {"source_ip": "external"},
            "risk_score": 0.95,
            "severity": 5
        }
    ]

    for i, config in enumerate(configs, 1):
        print(f"\n{i}. Testing {config.mode.value} mode with {config.pipeline.value} pipeline:")

        optimizer = IntegratedSecurityOptimizer(config, f"demo_integrated_{i}.db")

        total_time = 0
        for event in test_events:
            start = time.time()
            result = await optimizer.process_security_event(event)
            elapsed = (time.time() - start) * 1000
            total_time += elapsed

            print(f"   Event {event['event_id']}:")
            print(f"     Decision: {result.decision} ({result.confidence})")
            print(f"     Pipeline: {result.pipeline_used}")
            print(f"     Token Savings: {result.token_savings}")
            print(f"     Quality: {result.quality_score:.2%}")
            print(f"     Time: {result.processing_time_ms:.1f}ms")
            print(f"     Optimizations: {', '.join(result.optimization_applied)}")

        print(f"   Total Processing Time: {total_time:.1f}ms")

        # Show system stats
        stats = optimizer.get_optimization_stats()
        print(f"   System Stats:")
        print(f"     Events Processed: {stats['total_events']}")
        print(f"     Optimization Rate: {stats['optimization_success_rate']:.1%}")
        print(f"     Avg Token Savings: {stats['avg_token_savings']:.1f}")
        print(f"     Avg Quality: {stats['avg_quality_score']:.2%}")

        await optimizer.shutdown()

        # Cleanup
        import os
        if os.path.exists(f"demo_integrated_{i}.db"):
            os.remove(f"demo_integrated_{i}.db")

    print("\n✅ Integrated Security Optimizer Demo Complete!")

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    asyncio.run(demo_integrated_optimizer())