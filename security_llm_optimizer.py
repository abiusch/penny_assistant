#!/usr/bin/env python3
"""
Security LLM Optimization System
Advanced token usage optimization with quality maintenance for security analysis
"""

import asyncio
import hashlib
import json
import logging
import sqlite3
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Union, Callable
from dataclasses import dataclass, asdict
from enum import Enum
from collections import defaultdict, deque
import re

try:
    from security_event_templates import SecurityEventClassifier, ContextCompressor, EventCategory
    from security_context_optimizer import ContextCompressor as AdvancedCompressor, OptimizationTarget, CompressionLevel
    from security_batch_processor import SecurityBatchProcessor, BatchStrategy
except ImportError as e:
    print(f"Warning: Could not import security components: {e}")

class PromptStrategy(Enum):
    """LLM prompt optimization strategies"""
    TEMPLATE_BASED = "template_based"      # Use predefined templates
    DYNAMIC_PROMPT = "dynamic_prompt"      # Generate prompts dynamically
    PROGRESSIVE = "progressive"            # Progressive detail addition
    HIERARCHICAL = "hierarchical"          # Hierarchical analysis
    CACHED_REASONING = "cached_reasoning"  # Use cached reasoning patterns

class QualityMetric(Enum):
    """Quality measurement metrics"""
    ACCURACY = "accuracy"           # Decision accuracy
    COMPLETENESS = "completeness"   # Analysis completeness
    CONSISTENCY = "consistency"     # Consistency across similar events
    RELEVANCE = "relevance"         # Relevance of analysis
    CONFIDENCE = "confidence"       # Confidence in decisions

class TokenBudget(Enum):
    """Token budget levels"""
    MINIMAL = 100      # Emergency/fast processing
    COMPACT = 300      # Standard processing
    STANDARD = 800     # Normal analysis
    DETAILED = 2000    # Comprehensive analysis
    UNLIMITED = -1     # No limit (debugging/training)

@dataclass
class PromptTemplate:
    """Optimized prompt template for security analysis"""
    template_id: str
    name: str
    category: EventCategory
    base_prompt: str
    variable_sections: Dict[str, str]
    token_estimate: int
    quality_threshold: float
    usage_contexts: List[str]
    performance_metrics: Dict[str, float]

@dataclass
class QualityAssessment:
    """Quality assessment for LLM output"""
    assessment_id: str
    decision_accuracy: float
    reasoning_completeness: float
    confidence_calibration: float
    consistency_score: float
    overall_quality: float
    quality_factors: Dict[str, float]
    improvement_suggestions: List[str]

@dataclass
class TokenOptimizationResult:
    """Result of token optimization"""
    original_tokens: int
    optimized_tokens: int
    token_savings: int
    compression_ratio: float
    quality_impact: float
    processing_time_ms: float
    optimization_strategy: str

@dataclass
class CachedReasoning:
    """Cached reasoning pattern for reuse"""
    pattern_id: str
    event_signature: str
    reasoning_template: str
    decision_pattern: str
    confidence_level: float
    usage_count: int
    last_updated: datetime
    quality_score: float

class QualityMonitor:
    """Monitors and maintains analysis quality"""

    def __init__(self):
        self.quality_history: deque = deque(maxlen=1000)
        self.quality_thresholds = {
            QualityMetric.ACCURACY: 0.85,
            QualityMetric.COMPLETENESS: 0.80,
            QualityMetric.CONSISTENCY: 0.88,
            QualityMetric.RELEVANCE: 0.82,
            QualityMetric.CONFIDENCE: 0.75
        }
        self.logger = logging.getLogger("quality_monitor")

    def assess_quality(self, llm_output: Dict[str, Any], expected_output: Optional[Dict[str, Any]] = None) -> QualityAssessment:
        """Assess quality of LLM output"""

        assessment_id = f"qa_{int(time.time() * 1000)}"

        # Assess different quality dimensions
        accuracy = self._assess_accuracy(llm_output, expected_output)
        completeness = self._assess_completeness(llm_output)
        consistency = self._assess_consistency(llm_output)
        relevance = self._assess_relevance(llm_output)
        confidence = self._assess_confidence(llm_output)

        # Calculate overall quality
        weights = {
            "accuracy": 0.3,
            "completeness": 0.25,
            "consistency": 0.2,
            "relevance": 0.15,
            "confidence": 0.1
        }

        overall_quality = (
            accuracy * weights["accuracy"] +
            completeness * weights["completeness"] +
            consistency * weights["consistency"] +
            relevance * weights["relevance"] +
            confidence * weights["confidence"]
        )

        # Generate improvement suggestions
        suggestions = self._generate_improvement_suggestions(
            accuracy, completeness, consistency, relevance, confidence
        )

        assessment = QualityAssessment(
            assessment_id=assessment_id,
            decision_accuracy=accuracy,
            reasoning_completeness=completeness,
            confidence_calibration=confidence,
            consistency_score=consistency,
            overall_quality=overall_quality,
            quality_factors={
                "accuracy": accuracy,
                "completeness": completeness,
                "consistency": consistency,
                "relevance": relevance,
                "confidence": confidence
            },
            improvement_suggestions=suggestions
        )

        self.quality_history.append(assessment)
        return assessment

    def _assess_accuracy(self, output: Dict[str, Any], expected: Optional[Dict[str, Any]]) -> float:
        """Assess decision accuracy"""
        if not expected:
            # Use heuristic assessment based on reasoning quality
            decision = output.get("decision", "").lower()
            reasoning = output.get("reasoning", "")

            # Check for clear decision
            if decision in ["allow", "block", "deny"]:
                score = 0.7
            else:
                score = 0.4

            # Check reasoning quality
            if len(reasoning) > 50 and any(word in reasoning.lower() for word in ["because", "due to", "since"]):
                score += 0.2

            return min(score, 1.0)

        # Compare with expected output
        decision_match = output.get("decision", "").lower() == expected.get("decision", "").lower()
        reasoning_similarity = self._calculate_text_similarity(
            output.get("reasoning", ""), expected.get("reasoning", "")
        )

        return decision_match * 0.7 + reasoning_similarity * 0.3

    def _assess_completeness(self, output: Dict[str, Any]) -> float:
        """Assess completeness of analysis"""
        required_fields = ["decision", "reasoning", "confidence"]
        optional_fields = ["alternatives", "risks", "recommendations"]

        score = 0.0

        # Check required fields
        for field in required_fields:
            if field in output and output[field]:
                score += 1.0 / len(required_fields)

        # Bonus for optional fields
        for field in optional_fields:
            if field in output and output[field]:
                score += 0.1

        # Check reasoning depth
        reasoning = output.get("reasoning", "")
        if len(reasoning) > 100:
            score += 0.1
        if len(reasoning) > 200:
            score += 0.1

        return min(score, 1.0)

    def _assess_consistency(self, output: Dict[str, Any]) -> float:
        """Assess consistency with historical decisions"""
        if len(self.quality_history) < 5:
            return 0.8  # Default score with insufficient history

        current_decision = output.get("decision", "").lower()
        recent_decisions = [qa.decision_accuracy for qa in list(self.quality_history)[-10:]]

        # Check if decision pattern is consistent
        if recent_decisions:
            avg_quality = sum(recent_decisions) / len(recent_decisions)
            return min(avg_quality + 0.1, 1.0)

        return 0.8

    def _assess_relevance(self, output: Dict[str, Any]) -> float:
        """Assess relevance of analysis to security context"""
        reasoning = output.get("reasoning", "").lower()
        decision = output.get("decision", "").lower()

        score = 0.5  # Base score

        # Check for security-relevant terms
        security_terms = ["security", "risk", "threat", "permission", "access", "authorization", "violation"]
        relevant_terms = sum(1 for term in security_terms if term in reasoning)
        score += min(relevant_terms * 0.05, 0.3)

        # Check decision relevance
        if decision in ["allow", "block", "deny"] and len(reasoning) > 30:
            score += 0.2

        return min(score, 1.0)

    def _assess_confidence(self, output: Dict[str, Any]) -> float:
        """Assess confidence calibration"""
        stated_confidence = output.get("confidence", "medium").lower()
        reasoning_length = len(output.get("reasoning", ""))

        confidence_scores = {
            "high": 0.9,
            "medium": 0.7,
            "low": 0.5,
            "very_high": 0.95,
            "very_low": 0.3
        }

        base_score = confidence_scores.get(stated_confidence, 0.6)

        # Adjust based on reasoning depth
        if reasoning_length > 150 and stated_confidence == "high":
            return min(base_score + 0.1, 1.0)
        elif reasoning_length < 50 and stated_confidence == "high":
            return max(base_score - 0.2, 0.0)

        return base_score

    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two texts"""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())

        if not words1 or not words2:
            return 0.0

        intersection = words1.intersection(words2)
        union = words1.union(words2)

        return len(intersection) / len(union) if union else 0.0

    def _generate_improvement_suggestions(self, accuracy: float, completeness: float,
                                        consistency: float, relevance: float, confidence: float) -> List[str]:
        """Generate suggestions for quality improvement"""
        suggestions = []

        if accuracy < self.quality_thresholds[QualityMetric.ACCURACY]:
            suggestions.append("Improve decision accuracy by providing more context")

        if completeness < self.quality_thresholds[QualityMetric.COMPLETENESS]:
            suggestions.append("Include more comprehensive analysis with alternatives and risks")

        if consistency < self.quality_thresholds[QualityMetric.CONSISTENCY]:
            suggestions.append("Review decision patterns for consistency with similar cases")

        if relevance < self.quality_thresholds[QualityMetric.RELEVANCE]:
            suggestions.append("Focus analysis more specifically on security implications")

        if confidence < self.quality_thresholds[QualityMetric.CONFIDENCE]:
            suggestions.append("Improve confidence calibration by aligning stated confidence with reasoning depth")

        return suggestions

    def get_quality_trend(self, window_size: int = 20) -> Dict[str, float]:
        """Get recent quality trend"""
        if len(self.quality_history) < window_size:
            window_size = len(self.quality_history)

        if window_size == 0:
            return {"overall_quality": 0.0}

        recent_assessments = list(self.quality_history)[-window_size:]

        return {
            "overall_quality": sum(qa.overall_quality for qa in recent_assessments) / len(recent_assessments),
            "accuracy_trend": sum(qa.decision_accuracy for qa in recent_assessments) / len(recent_assessments),
            "completeness_trend": sum(qa.reasoning_completeness for qa in recent_assessments) / len(recent_assessments),
            "consistency_trend": sum(qa.consistency_score for qa in recent_assessments) / len(recent_assessments)
        }

class PromptOptimizer:
    """Optimizes prompts for different security scenarios"""

    def __init__(self):
        self.templates: Dict[str, PromptTemplate] = {}
        self.cached_reasoning: Dict[str, CachedReasoning] = {}
        self.logger = logging.getLogger("prompt_optimizer")

        self._load_prompt_templates()

    def _load_prompt_templates(self):
        """Load optimized prompt templates"""

        # File Access Template
        file_access_template = PromptTemplate(
            template_id="file_access_001",
            name="File Access Analysis",
            category=EventCategory.ACCESS_CONTROL,
            base_prompt="""Analyze this file access request for security implications:

Operation: {operation}
Resource: {resource}
User: {user_id}
Risk Level: {risk_score}

Decision required: allow/block
Provide reasoning focusing on security risks.""",
            variable_sections={
                "context": "Additional context: {context}",
                "parameters": "Parameters: {parameters}",
                "alternatives": "Suggest alternatives if blocking."
            },
            token_estimate=120,
            quality_threshold=0.85,
            usage_contexts=["file_read", "file_write", "file_access"],
            performance_metrics={"avg_accuracy": 0.91, "avg_processing_time": 45}
        )

        # Network Security Template
        network_template = PromptTemplate(
            template_id="network_001",
            name="Network Request Analysis",
            category=EventCategory.NETWORK_SECURITY,
            base_prompt="""Evaluate this network request for security risks:

URL/Target: {resource}
Method: {operation}
User: {user_id}
Risk Indicators: {risk_indicators}

Assess security implications and recommend action.""",
            variable_sections={
                "reputation": "URL reputation: {url_reputation}",
                "content_type": "Expected content: {content_type}",
                "business_context": "Business justification: {business_context}"
            },
            token_estimate=150,
            quality_threshold=0.80,
            usage_contexts=["network_request", "http_access", "download"],
            performance_metrics={"avg_accuracy": 0.87, "avg_processing_time": 60}
        )

        # Privilege Escalation Template
        privilege_template = PromptTemplate(
            template_id="privilege_001",
            name="Privilege Escalation Review",
            category=EventCategory.AUTHORIZATION,
            base_prompt="""Review this privilege escalation request:

Current Level: {current_permission}
Requested Level: {requested_permission}
User: {user_id}
Justification: {justification}
Risk Assessment: {risk_score}

Analyze legitimacy and security implications.""",
            variable_sections={
                "history": "User history: {user_history}",
                "business_need": "Business need: {business_justification}",
                "impact": "System impact: {impact_assessment}"
            },
            token_estimate=200,
            quality_threshold=0.88,
            usage_contexts=["privilege_escalation", "permission_request", "role_change"],
            performance_metrics={"avg_accuracy": 0.89, "avg_processing_time": 85}
        )

        # Quick Decision Template (for fast processing)
        quick_template = PromptTemplate(
            template_id="quick_001",
            name="Quick Security Decision",
            category=EventCategory.ANOMALY_DETECTION,
            base_prompt="""Quick security analysis:
Event: {event_type}
Action: {operation}
Risk: {risk_score}
Decision: allow/block with brief reason.""",
            variable_sections={},
            token_estimate=50,
            quality_threshold=0.70,
            usage_contexts=["emergency", "real_time", "batch_processing"],
            performance_metrics={"avg_accuracy": 0.82, "avg_processing_time": 20}
        )

        self.templates = {
            "file_access_001": file_access_template,
            "network_001": network_template,
            "privilege_001": privilege_template,
            "quick_001": quick_template
        }

    def optimize_prompt(self, event_data: Dict[str, Any], token_budget: TokenBudget,
                       quality_target: float = 0.85) -> Tuple[str, Dict[str, Any]]:
        """Optimize prompt for given constraints"""

        # Select appropriate template
        template = self._select_template(event_data, token_budget, quality_target)

        if not template:
            return self._generate_fallback_prompt(event_data, token_budget), {}

        # Build optimized prompt
        optimized_prompt = self._build_optimized_prompt(event_data, template, token_budget)

        # Generate metadata
        metadata = {
            "template_id": template.template_id,
            "estimated_tokens": self._estimate_prompt_tokens(optimized_prompt),
            "quality_target": quality_target,
            "optimization_strategy": self._get_optimization_strategy(token_budget)
        }

        return optimized_prompt, metadata

    def _select_template(self, event_data: Dict[str, Any], token_budget: TokenBudget,
                        quality_target: float) -> Optional[PromptTemplate]:
        """Select best template for the event"""

        operation = event_data.get("operation", "").lower()
        event_type = event_data.get("event_type", "").lower()

        # Quick template for minimal budgets
        if token_budget == TokenBudget.MINIMAL:
            return self.templates["quick_001"]

        # Match by operation patterns
        if any(op in operation for op in ["file", "read", "write", "access"]):
            template = self.templates["file_access_001"]
        elif any(op in operation for op in ["network", "http", "download", "url"]):
            template = self.templates["network_001"]
        elif any(op in operation for op in ["privilege", "escalation", "sudo", "admin"]):
            template = self.templates["privilege_001"]
        else:
            template = self.templates["quick_001"]

        # Check if template meets quality and budget constraints
        if (template.token_estimate <= token_budget.value and
            template.quality_threshold >= quality_target - 0.05):
            return template

        # Fallback to quick template
        return self.templates["quick_001"]

    def _build_optimized_prompt(self, event_data: Dict[str, Any], template: PromptTemplate,
                              token_budget: TokenBudget) -> str:
        """Build optimized prompt from template"""

        # Start with base prompt
        prompt = template.base_prompt.format(**event_data)

        remaining_tokens = token_budget.value - template.token_estimate

        # Add variable sections based on remaining budget
        if remaining_tokens > 0:
            for section_name, section_template in template.variable_sections.items():
                section_tokens = self._estimate_prompt_tokens(section_template)

                if section_tokens <= remaining_tokens:
                    try:
                        section_content = section_template.format(**event_data)
                        prompt += "\n" + section_content
                        remaining_tokens -= section_tokens
                    except KeyError:
                        # Skip sections with missing data
                        continue

        return prompt

    def _generate_fallback_prompt(self, event_data: Dict[str, Any], token_budget: TokenBudget) -> str:
        """Generate minimal fallback prompt"""
        event_type = event_data.get("event_type", "unknown")
        operation = event_data.get("operation", "unknown")
        risk = event_data.get("risk_score", 0.5)

        if token_budget == TokenBudget.MINIMAL:
            return f"Security check: {event_type} {operation} (risk: {risk:.1f}) - allow/block?"
        else:
            return f"Analyze security event: {event_type} operation '{operation}' with risk {risk:.2f}. Decision and brief reasoning required."

    def _estimate_prompt_tokens(self, prompt: str) -> int:
        """Estimate token count for prompt"""
        # Rough estimation: 4 characters per token
        return len(prompt) // 4

    def _get_optimization_strategy(self, token_budget: TokenBudget) -> str:
        """Get optimization strategy name"""
        if token_budget == TokenBudget.MINIMAL:
            return "emergency_minimal"
        elif token_budget == TokenBudget.COMPACT:
            return "template_optimized"
        elif token_budget == TokenBudget.STANDARD:
            return "balanced_analysis"
        else:
            return "comprehensive_analysis"

    def cache_reasoning_pattern(self, event_signature: str, reasoning: str, decision: str,
                              confidence: float, quality_score: float):
        """Cache reasoning pattern for reuse"""
        pattern_id = hashlib.md5(f"{event_signature}_{decision}".encode()).hexdigest()[:12]

        cached = CachedReasoning(
            pattern_id=pattern_id,
            event_signature=event_signature,
            reasoning_template=reasoning,
            decision_pattern=decision,
            confidence_level=confidence,
            usage_count=1,
            last_updated=datetime.now(),
            quality_score=quality_score
        )

        self.cached_reasoning[pattern_id] = cached
        self.logger.debug(f"Cached reasoning pattern: {pattern_id}")

    def get_cached_reasoning(self, event_signature: str) -> Optional[CachedReasoning]:
        """Get cached reasoning for similar events"""
        for cached in self.cached_reasoning.values():
            if cached.event_signature == event_signature:
                cached.usage_count += 1
                cached.last_updated = datetime.now()
                return cached
        return None

class SecurityLLMOptimizer:
    """Main LLM optimization system for security analysis"""

    def __init__(self, db_path: str = "security_llm_optimization.db"):
        self.db_path = db_path
        self.logger = logging.getLogger("security_llm_optimizer")

        # Initialize components
        self.classifier = SecurityEventClassifier()
        self.context_compressor = AdvancedCompressor()
        self.prompt_optimizer = PromptOptimizer()
        self.quality_monitor = QualityMonitor()

        # Optimization state
        self.optimization_history: List[TokenOptimizationResult] = []
        self.performance_metrics = {
            "total_optimizations": 0,
            "avg_token_savings": 0.0,
            "avg_quality_score": 0.0,
            "avg_processing_time": 0.0
        }

        # Thread safety
        self.lock = threading.RLock()

        # Initialize database
        self._init_database()

    def _init_database(self):
        """Initialize optimization tracking database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS optimization_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_signature TEXT,
                original_tokens INTEGER,
                optimized_tokens INTEGER,
                token_savings INTEGER,
                compression_ratio REAL,
                quality_impact REAL,
                processing_time_ms REAL,
                optimization_strategy TEXT,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS quality_assessments (
                assessment_id TEXT PRIMARY KEY,
                event_signature TEXT,
                decision_accuracy REAL,
                reasoning_completeness REAL,
                confidence_calibration REAL,
                consistency_score REAL,
                overall_quality REAL,
                improvement_suggestions TEXT,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.commit()
        conn.close()

    async def optimize_security_analysis(self, event_data: Dict[str, Any],
                                       token_budget: TokenBudget = TokenBudget.STANDARD,
                                       quality_target: float = 0.85) -> Dict[str, Any]:
        """Optimize security analysis with token and quality constraints"""

        start_time = time.time()

        # Step 1: Classify and compress context
        template = self.classifier.classify_event(event_data)
        if template:
            compressed_context, compression_metadata = self.context_compressor.compress_context(
                event_data, OptimizationTarget.BALANCED, CompressionLevel.MODERATE
            )
        else:
            compressed_context = event_data
            compression_metadata = {"strategy": "no_compression"}

        # Step 2: Optimize prompt
        optimized_prompt, prompt_metadata = self.prompt_optimizer.optimize_prompt(
            compressed_context, token_budget, quality_target
        )

        # Step 3: Check for cached reasoning
        event_signature = self._create_event_signature(compressed_context)
        cached_reasoning = self.prompt_optimizer.get_cached_reasoning(event_signature)

        if cached_reasoning and cached_reasoning.quality_score >= quality_target:
            # Use cached reasoning
            result = {
                "decision": cached_reasoning.decision_pattern,
                "reasoning": cached_reasoning.reasoning_template,
                "confidence": cached_reasoning.confidence_level,
                "source": "cached_reasoning",
                "quality_score": cached_reasoning.quality_score
            }
        else:
            # Simulate LLM analysis (in real implementation, this would call the LLM)
            result = await self._simulate_llm_analysis(compressed_context, optimized_prompt)

        # Step 4: Assess quality
        quality_assessment = self.quality_monitor.assess_quality(result)

        # Step 5: Cache high-quality reasoning
        if quality_assessment.overall_quality >= 0.8:
            self.prompt_optimizer.cache_reasoning_pattern(
                event_signature,
                result.get("reasoning", ""),
                result.get("decision", ""),
                result.get("confidence", 0.5),
                quality_assessment.overall_quality
            )

        # Step 6: Calculate optimization metrics
        processing_time = (time.time() - start_time) * 1000
        original_tokens = self._estimate_tokens(json.dumps(event_data))
        optimized_tokens = prompt_metadata.get("estimated_tokens", 0)

        optimization_result = TokenOptimizationResult(
            original_tokens=original_tokens,
            optimized_tokens=optimized_tokens,
            token_savings=max(0, original_tokens - optimized_tokens),
            compression_ratio=optimized_tokens / original_tokens if original_tokens > 0 else 1.0,
            quality_impact=quality_assessment.overall_quality,
            processing_time_ms=processing_time,
            optimization_strategy=prompt_metadata.get("optimization_strategy", "unknown")
        )

        # Step 7: Update metrics and store results
        self._update_metrics(optimization_result, quality_assessment)
        await self._store_optimization_result(optimization_result, quality_assessment, event_signature)

        # Return comprehensive result
        return {
            "analysis_result": result,
            "optimization_metrics": asdict(optimization_result),
            "quality_assessment": asdict(quality_assessment),
            "compression_info": compression_metadata,
            "prompt_info": prompt_metadata,
            "processing_time_ms": processing_time
        }

    async def _simulate_llm_analysis(self, context: Dict[str, Any], prompt: str) -> Dict[str, Any]:
        """Simulate LLM analysis (replace with actual LLM call in production)"""

        # Simulate processing delay
        await asyncio.sleep(0.1)

        operation = context.get("operation", "unknown")
        risk_score = context.get("risk_score", 0.5)
        event_type = context.get("event_type", "unknown")

        # Simple rule-based simulation
        if risk_score > 0.8:
            decision = "block"
            confidence = "high"
            reasoning = f"High risk score ({risk_score:.2f}) detected for {operation}. Security policy requires blocking high-risk operations to prevent potential security breaches."
        elif risk_score > 0.6:
            decision = "allow_with_monitoring"
            confidence = "medium"
            reasoning = f"Medium risk score ({risk_score:.2f}) for {operation}. Allowing with enhanced monitoring to track for suspicious patterns."
        else:
            decision = "allow"
            confidence = "high"
            reasoning = f"Low risk score ({risk_score:.2f}) for {operation}. Standard security checks passed, operation is safe to proceed."

        return {
            "decision": decision,
            "reasoning": reasoning,
            "confidence": confidence,
            "alternatives": self._generate_alternatives(decision),
            "risk_assessment": {"level": "high" if risk_score > 0.7 else "medium" if risk_score > 0.4 else "low"},
            "source": "llm_analysis"
        }

    def _generate_alternatives(self, decision: str) -> List[str]:
        """Generate alternatives based on decision"""
        if decision == "block":
            return [
                "Request proper authorization",
                "Use alternative approved methods",
                "Contact security team for guidance"
            ]
        elif decision == "allow_with_monitoring":
            return [
                "Proceed with standard monitoring",
                "Request additional verification",
                "Use read-only access if possible"
            ]
        else:
            return []

    def _create_event_signature(self, event_data: Dict[str, Any]) -> str:
        """Create signature for event similarity matching"""
        key_fields = ["event_type", "operation", "resource"]
        signature_data = {k: event_data.get(k, "") for k in key_fields}
        signature_str = json.dumps(signature_data, sort_keys=True)
        return hashlib.md5(signature_str.encode()).hexdigest()[:16]

    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count for text"""
        return len(text) // 4

    def _update_metrics(self, optimization_result: TokenOptimizationResult, quality_assessment: QualityAssessment):
        """Update performance metrics"""
        with self.lock:
            self.performance_metrics["total_optimizations"] += 1
            total = self.performance_metrics["total_optimizations"]

            # Update averages
            self.performance_metrics["avg_token_savings"] = (
                (self.performance_metrics["avg_token_savings"] * (total - 1) + optimization_result.token_savings) / total
            )

            self.performance_metrics["avg_quality_score"] = (
                (self.performance_metrics["avg_quality_score"] * (total - 1) + quality_assessment.overall_quality) / total
            )

            self.performance_metrics["avg_processing_time"] = (
                (self.performance_metrics["avg_processing_time"] * (total - 1) + optimization_result.processing_time_ms) / total
            )

            self.optimization_history.append(optimization_result)

    async def _store_optimization_result(self, optimization_result: TokenOptimizationResult,
                                       quality_assessment: QualityAssessment, event_signature: str):
        """Store optimization result in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Store optimization history
        cursor.execute("""
            INSERT INTO optimization_history
            (event_signature, original_tokens, optimized_tokens, token_savings,
             compression_ratio, quality_impact, processing_time_ms, optimization_strategy)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            event_signature,
            optimization_result.original_tokens,
            optimization_result.optimized_tokens,
            optimization_result.token_savings,
            optimization_result.compression_ratio,
            optimization_result.quality_impact,
            optimization_result.processing_time_ms,
            optimization_result.optimization_strategy
        ))

        # Store quality assessment
        cursor.execute("""
            INSERT INTO quality_assessments
            (assessment_id, event_signature, decision_accuracy, reasoning_completeness,
             confidence_calibration, consistency_score, overall_quality, improvement_suggestions)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            quality_assessment.assessment_id,
            event_signature,
            quality_assessment.decision_accuracy,
            quality_assessment.reasoning_completeness,
            quality_assessment.confidence_calibration,
            quality_assessment.consistency_score,
            quality_assessment.overall_quality,
            json.dumps(quality_assessment.improvement_suggestions)
        ))

        conn.commit()
        conn.close()

    def get_optimization_stats(self) -> Dict[str, Any]:
        """Get optimization statistics"""
        with self.lock:
            stats = self.performance_metrics.copy()

            # Add additional metrics
            if self.optimization_history:
                recent_results = self.optimization_history[-20:]  # Last 20 optimizations

                stats.update({
                    "recent_token_efficiency": sum(r.token_savings for r in recent_results) / len(recent_results),
                    "recent_quality_trend": sum(r.quality_impact for r in recent_results) / len(recent_results),
                    "optimization_success_rate": len([r for r in recent_results if r.quality_impact >= 0.8]) / len(recent_results),
                    "cached_reasoning_count": len(self.prompt_optimizer.cached_reasoning)
                })

            quality_trend = self.quality_monitor.get_quality_trend()
            stats.update({"quality_trend": quality_trend})

            return stats

    def get_system_status(self) -> Dict[str, Any]:
        """Get system status"""
        return {
            "total_optimizations": self.performance_metrics["total_optimizations"],
            "avg_token_savings": self.performance_metrics["avg_token_savings"],
            "avg_quality_score": self.performance_metrics["avg_quality_score"],
            "cached_patterns": len(self.prompt_optimizer.cached_reasoning),
            "available_templates": len(self.prompt_optimizer.templates),
            "optimization_history_size": len(self.optimization_history)
        }

async def demo_llm_optimizer():
    """Demonstrate LLM optimization capabilities"""

    print("🎯 Security LLM Optimizer Demo")
    print("=" * 60)

    optimizer = SecurityLLMOptimizer("demo_llm_optimization.db")

    # Test events with different complexity levels
    test_events = [
        {
            "event_id": "evt_001",
            "event_type": "permission_check",
            "operation": "file_read",
            "resource": "/home/user/documents/report.pdf",
            "user_id": "user123",
            "risk_score": 0.3,
            "severity": 2,
            "parameters": {"file_type": "pdf", "size": "2MB"},
            "context": {"department": "finance", "clearance": "standard"}
        },
        {
            "event_id": "evt_002",
            "event_type": "security_violation",
            "operation": "path_traversal",
            "resource": "../../../etc/passwd",
            "user_id": "user456",
            "risk_score": 0.95,
            "severity": 5,
            "parameters": {"attempted_path": "../../../etc/passwd"},
            "context": {"attack_type": "path_traversal", "source_ip": "external"}
        },
        {
            "event_id": "evt_003",
            "event_type": "privilege_escalation",
            "operation": "sudo_request",
            "resource": "system_admin",
            "user_id": "user789",
            "risk_score": 0.7,
            "severity": 4,
            "parameters": {"requested_role": "admin", "justification": "maintenance"},
            "context": {"time": "after_hours", "frequency": "unusual"}
        }
    ]

    # Test different token budgets
    budgets = [TokenBudget.MINIMAL, TokenBudget.COMPACT, TokenBudget.STANDARD]

    print(f"Testing {len(test_events)} events with {len(budgets)} token budgets...\n")

    for i, event in enumerate(test_events, 1):
        print(f"{i}. Event: {event['event_type']} (Risk: {event['risk_score']:.2f})")

        for budget in budgets:
            result = await optimizer.optimize_security_analysis(
                event, budget, quality_target=0.80
            )

            analysis = result["analysis_result"]
            metrics = result["optimization_metrics"]
            quality = result["quality_assessment"]

            print(f"   {budget.name} Budget ({budget.value} tokens):")
            print(f"     Decision: {analysis['decision']}")
            print(f"     Token Savings: {metrics['token_savings']}")
            print(f"     Quality Score: {quality['overall_quality']:.2%}")
            print(f"     Processing Time: {metrics['processing_time_ms']:.1f}ms")

        print()

    # Show system statistics
    print("📊 Optimization Statistics:")
    stats = optimizer.get_optimization_stats()
    for key, value in stats.items():
        if isinstance(value, dict):
            print(f"   {key}:")
            for sub_key, sub_value in value.items():
                if isinstance(sub_value, float):
                    print(f"     {sub_key}: {sub_value:.3f}")
                else:
                    print(f"     {sub_key}: {sub_value}")
        elif isinstance(value, float):
            print(f"   {key}: {value:.3f}")
        else:
            print(f"   {key}: {value}")

    # Cleanup
    import os
    if os.path.exists("demo_llm_optimization.db"):
        os.remove("demo_llm_optimization.db")

    print("\n✅ Security LLM Optimizer Demo Complete!")

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    asyncio.run(demo_llm_optimizer())