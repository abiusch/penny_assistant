"""
Cultural Intelligence Tool Server
Task 9.3b: Authentic cultural intelligence capabilities for Penny

Provides MCP operations that let Penny research authentic conversational
patterns, validate cultural references, adapt communication style, and
integrate new cultural knowledge without resorting to superficial slang.

Design goals:
- Leverage existing autonomous research pipeline for cultural investigations
- Store cultural knowledge in persistent memory with confidence tracking
- Enhance (not replace) existing sass-based personality system
- Provide authenticity and sensitivity validation before cultural usage
"""

from __future__ import annotations

import asyncio
import json
import logging
import statistics
import time
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

# Optional MCP + security imports (with fallbacks for standalone execution)
try:
    from mcp_client import MCPToolServer, MCPOperation, MCPResult
    from tool_server_foundation import SecurityLevel
    from command_whitelist_system import CommandWhitelistSystem
    from multi_channel_emergency_stop import MultiChannelEmergencyStop
    from enhanced_security_logging import EnhancedSecurityLogging
    from rollback_recovery_system import RollbackRecoverySystem
    from rate_limiting_resource_control import RateLimitingResourceControl
    MCP_AVAILABLE = True
except ImportError:  # pragma: no cover - fallback definitions for environments without MCP
    from enum import Enum

    class SecurityLevel(Enum):
        LOW = "low"
        MEDIUM = "medium"
        HIGH = "high"
        CRITICAL = "critical"

    @dataclass
    class MCPOperation:
        name: str
        parameters: Dict[str, Any]
        security_level: SecurityLevel = SecurityLevel.MEDIUM

    @dataclass
    class MCPResult:
        success: bool
        data: Any = None
        error: Optional[str] = None
        metadata: Optional[Dict[str, Any]] = None

    class MCPToolServer:
        def __init__(self, name: str, operations: Dict[str, MCPOperation]):
            self.name = name
            self.operations = operations

        async def start(self) -> bool:
            return True

        async def stop(self) -> bool:
            return True

    class CommandWhitelistSystem:
        async def is_command_allowed(self, command: str) -> bool:
            return True

    class MultiChannelEmergencyStop:
        def is_emergency_active(self) -> bool:
            return False

    class EnhancedSecurityLogging:
        async def log_security_event(self, event_type: str, details: Dict[str, Any]):
            return None

    class RollbackRecoverySystem:
        async def create_checkpoint(self, checkpoint_id: str) -> str:
            return checkpoint_id

    class RateLimitingResourceControl:
        async def check_rate_limit(self, user_id: str, operation: str) -> bool:
            return True

    MCP_AVAILABLE = False

# Reuse autonomous research components for cultural investigations
try:
    from autonomous_research_tool_server import (
        KnowledgeGap,
        KnowledgeGapType,
        ResearchQuestion,
        ResearchScope,
        ResearchExecutor,
        InformationSynthesizer,
        ResearchFinding,
    )
except ImportError:  # pragma: no cover - minimal fallback if research server unavailable
    KnowledgeGap = None  # type: ignore
    KnowledgeGapType = None  # type: ignore
    ResearchQuestion = None  # type: ignore
    ResearchScope = None  # type: ignore

    class ResearchFinding:  # type: ignore
        def __init__(self, finding_id: str, research_question_id: str, summary: str,
                     key_insights: List[str], supporting_sources: List[str],
                     confidence_level: float, actionable_recommendations: List[str],
                     related_topics: List[str], created_at: datetime):
            self.finding_id = finding_id
            self.research_question_id = research_question_id
            self.summary = summary
            self.key_insights = key_insights
            self.supporting_sources = supporting_sources
            self.confidence_level = confidence_level
            self.actionable_recommendations = actionable_recommendations
            self.related_topics = related_topics
            self.created_at = created_at

    class ResearchExecutor:  # type: ignore
        async def create_research_plan(self, *args, **kwargs):
            raise RuntimeError("Autonomous research components not available")

        async def execute_research_plan(self, *args, **kwargs):
            raise RuntimeError("Autonomous research components not available")

    class InformationSynthesizer:  # type: ignore
        async def synthesize_research_findings(self, findings: List[ResearchFinding],
                                               synthesis_style: str = "comprehensive") -> Dict[str, Any]:
            return {
                "summary": "Research subsystem unavailable",
                "key_insights": [],
                "recommendations": [],
                "confidence": 0.0,
                "related_topics": [],
                "next_steps": []
            }

# Personality + memory systems
try:
    from adaptive_sass_learning import AdaptiveSassLearning
    from sass_controller import SassLevel
except ImportError:  # pragma: no cover - graceful fallback
    from enum import Enum

    AdaptiveSassLearning = None  # type: ignore

    class SassLevel(Enum):  # type: ignore
        MINIMAL = "minimal"
        LITE = "lite"
        MEDIUM = "medium"
        SPICY = "spicy"
        MAXIMUM = "maximum"

try:
    from persistent_memory import PersistentMemory, MemoryType, MemoryItem
except ImportError:  # pragma: no cover
    PersistentMemory = None  # type: ignore
    MemoryType = None  # type: ignore

    @dataclass
    class MemoryItem:  # type: ignore
        id: Optional[int]
        memory_type: str
        key: str
        value: str
        confidence: float
        created_at: datetime
        last_accessed: datetime
        access_count: int
        context: str

LOGGER = logging.getLogger(__name__)

# Positive media and regional focus areas for authenticity-first research
POSITIVE_MEDIA_LIBRARY = [
    {
        "title": "Ted Lasso",
        "type": "series",
        "tone": "uplifting",
        "notes": "Heart-forward storytelling with optimistic humor",
        "regions": ["california", "global"],
        "generations": ["millennial", "gen x"],
    },
    {
        "title": "Spider-Man: Into the Spider-Verse",
        "type": "film",
        "tone": "inspiring",
        "notes": "Authentic multi-cultural storytelling with vibrant dialogue",
        "regions": ["california", "new york"],
        "generations": ["gen z", "millennial"],
    },
    {
        "title": "The Good Place",
        "type": "series",
        "tone": "thoughtful",
        "notes": "Smart philosophical humor with natural conversational beats",
        "regions": ["global"],
        "generations": ["millennial", "gen x"],
    },
    {
        "title": "Everything Everywhere All at Once",
        "type": "film",
        "tone": "empathetic",
        "notes": "Intergenerational immigrant family story balanced with absurd humor",
        "regions": ["california", "global"],
        "generations": ["millennial", "gen x"],
    },
]

REGIONAL_COMMUNICATION_TRAITS = {
    "california": {
        "pace": "laid_back",
        "tone": "optimistic",
        "vocabulary": ["hey there", "totally", "let's dig in"],
        "humor": "warm",
        "directness": 0.5,
    },
    "tech_industry": {
        "pace": "efficient",
        "tone": "pragmatic",
        "vocabulary": ["shipping", "iteration", "playbook"],
        "humor": "dry",
        "directness": 0.7,
    },
}

GENERATIONAL_REFERENCE_GUARDRAILS = {
    "gen z": {
        "avoid": ["outdated slang", "forced meme references"],
        "embrace": ["collaborative language", "internet culture context"],
        "tone": "playful",
    },
    "millennial": {
        "avoid": ["overly formal jargon", "try-hard youthful phrases"],
        "embrace": ["shared pop culture", "self-aware humor"],
        "tone": "balanced",
    },
    "gen x": {
        "avoid": ["dismissive of experience", "too much slang"],
        "embrace": ["competence", "respectful wit"],
        "tone": "confident",
    },
}


@dataclass
class CulturalPatternRecord:
    """Represents a learned communication pattern"""

    pattern_type: str
    usage_context: Dict[str, Any]
    effectiveness_score: float
    authenticity_score: float
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    examples: List[str] = field(default_factory=list)


@dataclass
class CulturalReferenceRecord:
    """Represents a validated cultural reference"""

    reference: str
    region: str
    generation: str
    tone: str
    media_type: str
    positivity_score: float
    context_notes: str
    confidence: float
    last_validated: datetime = field(default_factory=datetime.now)
    usage_examples: List[str] = field(default_factory=list)


class CulturalKnowledgeStore:
    """Adapter around persistent memory for cultural knowledge storage"""

    def __init__(self, memory_system: Optional[PersistentMemory] = None):
        self.memory_system = memory_system
        self.patterns: Dict[str, CulturalPatternRecord] = {}
        self.references: Dict[str, CulturalReferenceRecord] = {}

        if self.memory_system and MemoryType:
            self._load_existing_memories()

    def _load_existing_memories(self) -> None:
        """Populate caches with previously stored cultural knowledge"""
        try:
            stored_items = self.memory_system.search_memories(
                memory_type=MemoryType.PREFERENCE,
                search_term="cultural::",
                limit=200
            )
        except Exception as exc:  # pragma: no cover - defensive
            LOGGER.warning("Failed to load cultural memories: %s", exc)
            return

        for item in stored_items:
            try:
                payload = json.loads(item.value)
            except (json.JSONDecodeError, TypeError):
                continue

            if payload.get("record_type") == "pattern":
                record = CulturalPatternRecord(
                    pattern_type=payload["pattern_type"],
                    usage_context=payload.get("usage_context", {}),
                    effectiveness_score=payload.get("effectiveness_score", 0.0),
                    authenticity_score=payload.get("authenticity_score", 0.0),
                    created_at=datetime.fromisoformat(payload.get("created_at", item.created_at.isoformat())),
                    updated_at=datetime.fromisoformat(payload.get("updated_at", item.last_accessed.isoformat())),
                    examples=payload.get("examples", []),
                )
                self.patterns[payload["pattern_type"]] = record
            elif payload.get("record_type") == "reference":
                record = CulturalReferenceRecord(
                    reference=payload["reference"],
                    region=payload.get("region", "global"),
                    generation=payload.get("generation", "millennial"),
                    tone=payload.get("tone", "balanced"),
                    media_type=payload.get("media_type", "reference"),
                    positivity_score=payload.get("positivity_score", 0.7),
                    context_notes=payload.get("context_notes", ""),
                    confidence=payload.get("confidence", 0.6),
                    last_validated=datetime.fromisoformat(payload.get("last_validated", item.last_accessed.isoformat())),
                    usage_examples=payload.get("usage_examples", []),
                )
                self.references[record.reference.lower()] = record

    def store_pattern(self, record: CulturalPatternRecord) -> None:
        """Persist a communication pattern"""
        key = f"cultural::pattern::{record.pattern_type}"
        self.patterns[record.pattern_type] = record

        if not self.memory_system or not MemoryType:
            return

        payload = {
            "record_type": "pattern",
            "pattern_type": record.pattern_type,
            "usage_context": record.usage_context,
            "effectiveness_score": record.effectiveness_score,
            "authenticity_score": record.authenticity_score,
            "created_at": record.created_at.isoformat(),
            "updated_at": record.updated_at.isoformat(),
            "examples": record.examples,
        }

        self.memory_system.store_memory(
            memory_type=MemoryType.PREFERENCE,
            key=key,
            value=json.dumps(payload, ensure_ascii=True),
            confidence=min(1.0, record.authenticity_score),
            context="cultural_intelligence"
        )

    def store_reference(self, record: CulturalReferenceRecord) -> None:
        """Persist a cultural reference record"""
        key = f"cultural::reference::{record.reference.lower()}"
        self.references[record.reference.lower()] = record

        if not self.memory_system or not MemoryType:
            return

        payload = {
            "record_type": "reference",
            "reference": record.reference,
            "region": record.region,
            "generation": record.generation,
            "tone": record.tone,
            "media_type": record.media_type,
            "positivity_score": record.positivity_score,
            "context_notes": record.context_notes,
            "confidence": record.confidence,
            "last_validated": record.last_validated.isoformat(),
            "usage_examples": record.usage_examples,
        }

        self.memory_system.store_memory(
            memory_type=MemoryType.PREFERENCE,
            key=key,
            value=json.dumps(payload, ensure_ascii=True),
            confidence=min(1.0, record.confidence),
            context="cultural_intelligence"
        )

    def get_reference(self, reference: str) -> Optional[CulturalReferenceRecord]:
        return self.references.get(reference.lower())

    def update_reference_confidence(self, reference: str, delta: float) -> None:
        record = self.get_reference(reference)
        if not record:
            return
        record.confidence = max(0.0, min(1.0, record.confidence + delta))
        record.last_validated = datetime.now()
        self.store_reference(record)


class CulturalAuthenticityValidator:
    """Applies authenticity and sensitivity checks before cultural usage"""

    def __init__(self, knowledge_store: CulturalKnowledgeStore):
        self.knowledge_store = knowledge_store

    def validate_usage(self, element: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Run authenticity checks from the provided framework"""
        checks = {
            "natural_fit": self._does_element_fit_context(element, context),
            "personality_match": self._aligns_with_personality(element, context),
            "appropriate_timing": self._timing_is_natural(element, context),
            "cultural_sensitivity": self._respects_boundaries(element, context),
            "user_relationship": self._matches_relationship_context(element, context),
        }

        forced_usage = self._detect_forced_usage(element, context)
        checks["no_forced_usage"] = not forced_usage

        return {
            "all_checks_passed": all(checks.values()),
            "failed_checks": [name for name, passed in checks.items() if not passed],
            "forced_usage_detected": forced_usage,
        }

    def _does_element_fit_context(self, element: str, context: Dict[str, Any]) -> bool:
        record = self.knowledge_store.get_reference(element)
        if record:
            topic_text = context.get("topic", "")
            if not topic_text:
                return True
            topic_tokens = [token.strip().lower() for token in topic_text.split() if token]
            notes = record.context_notes.lower()
            if any(token in notes for token in topic_tokens):
                return True
            # If reference is globally applicable, treat as natural when topic is collaborative
            if record.region == "global" or "team" in topic_tokens or "mentoring" in topic_tokens:
                return True

        convo = context.get("conversation", "")
        topic = context.get("topic", "")
        if element.lower() in convo.lower():
            return True
        keywords = context.get("keywords", [])
        return any(word.lower() in element.lower() for word in keywords) or element.lower() in topic.lower()

    def _aligns_with_personality(self, element: str, context: Dict[str, Any]) -> bool:
        sass_level = context.get("sass_level", "medium")
        if sass_level == "minimal" and any(token in element.lower() for token in ["savage", "roast"]):
            return False
        return True

    def _timing_is_natural(self, element: str, context: Dict[str, Any]) -> bool:
        position = context.get("position_in_conversation", "middle")
        if position == "opening" and context.get("requires_context", False):
            return False
        return True

    def _respects_boundaries(self, element: str, context: Dict[str, Any]) -> bool:
        sensitive_topics = context.get("sensitive_topics", [])
        return not any(topic.lower() in element.lower() for topic in sensitive_topics)

    def _matches_relationship_context(self, element: str, context: Dict[str, Any]) -> bool:
        relationship = context.get("relationship", "professional")
        if relationship == "professional" and any(token in element.lower() for token in ["bro", "bestie", "dude"]):
            return False
        return True

    def _detect_forced_usage(self, element: str, context: Dict[str, Any]) -> bool:
        if context.get("authenticity_score", 1.0) < 0.5:
            return True
        if len(element.split()) <= 2 and context.get("requires_depth", False):
            return True
        return False

    def assess_risk(self, element: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Return a graded risk assessment for authenticity"""
        validation = self.validate_usage(element, context)
        risk_level = "low"
        if validation["forced_usage_detected"] or len(validation["failed_checks"]) >= 2:
            risk_level = "high"
        elif validation["failed_checks"]:
            risk_level = "medium"

        return {
            "risk_level": risk_level,
            "failed_checks": validation["failed_checks"],
            "forced_usage": validation["forced_usage_detected"],
        }


class CulturalIntelligenceToolServer(MCPToolServer):
    """Cultural intelligence MCP tool server"""

    def __init__(self, security_components: Optional[Dict[str, Any]] = None):
        operations = {
            "research_cultural_context": MCPOperation(
                name="research_cultural_context",
                parameters={
                    "topic": {"type": "string"},
                    "region": {"type": "string", "default": "california"},
                    "generation": {"type": "string", "default": "millennial"},
                    "media_focus": {"type": "string", "default": None},
                    "tone_goal": {"type": "string", "default": "balanced"},
                },
                security_level=SecurityLevel.MEDIUM,
            ),
            "analyze_communication_patterns": MCPOperation(
                name="analyze_communication_patterns",
                parameters={
                    "source_type": {"type": "string"},
                    "sample_transcripts": {"type": "array", "default": None},
                    "authenticity_filter": {"type": "boolean", "default": True},
                },
                security_level=SecurityLevel.LOW,
            ),
            "validate_cultural_reference": MCPOperation(
                name="validate_cultural_reference",
                parameters={
                    "reference": {"type": "string"},
                    "context": {"type": "object"},
                    "appropriateness_check": {"type": "boolean", "default": True},
                },
                security_level=SecurityLevel.MEDIUM,
            ),
            "suggest_authentic_responses": MCPOperation(
                name="suggest_authentic_responses",
                parameters={
                    "conversation_context": {"type": "object"},
                    "personality_constraints": {"type": "object", "default": None},
                },
                security_level=SecurityLevel.LOW,
            ),
            "adapt_communication_style": MCPOperation(
                name="adapt_communication_style",
                parameters={
                    "target_audience": {"type": "object"},
                    "existing_personality": {"type": "object"},
                    "conversation_goal": {"type": "string", "default": "maintain_relationship"},
                },
                security_level=SecurityLevel.LOW,
            ),
            "generate_contextual_references": MCPOperation(
                name="generate_contextual_references",
                parameters={
                    "topic": {"type": "string"},
                    "cultural_background": {"type": "object"},
                    "confidence_threshold": {"type": "number", "default": 0.8},
                },
                security_level=SecurityLevel.MEDIUM,
            ),
            "store_communication_pattern": MCPOperation(
                name="store_communication_pattern",
                parameters={
                    "pattern_type": {"type": "string"},
                    "usage_context": {"type": "object"},
                    "effectiveness_score": {"type": "number"},
                    "examples": {"type": "array", "default": None},
                },
                security_level=SecurityLevel.HIGH,
            ),
            "analyze_conversation_effectiveness": MCPOperation(
                name="analyze_conversation_effectiveness",
                parameters={
                    "conversation_history": {"type": "array"},
                    "cultural_elements": {"type": "array"},
                    "user_feedback": {"type": "object", "default": None},
                },
                security_level=SecurityLevel.LOW,
            ),
            "update_cultural_knowledge": MCPOperation(
                name="update_cultural_knowledge",
                parameters={
                    "new_information": {"type": "object"},
                    "source_credibility": {"type": "number"},
                    "integration_strategy": {"type": "string", "default": "append"},
                },
                security_level=SecurityLevel.HIGH,
            ),
            "assess_authenticity_risk": MCPOperation(
                name="assess_authenticity_risk",
                parameters={
                    "proposed_response": {"type": "string"},
                    "cultural_elements": {"type": "array"},
                    "user_profile": {"type": "object", "default": None},
                },
                security_level=SecurityLevel.MEDIUM,
            ),
            "filter_inappropriate_references": MCPOperation(
                name="filter_inappropriate_references",
                parameters={
                    "content": {"type": "array"},
                    "sensitivity_guidelines": {"type": "object"},
                },
                security_level=SecurityLevel.MEDIUM,
            ),
            "validate_generational_appropriateness": MCPOperation(
                name="validate_generational_appropriateness",
                parameters={
                    "reference": {"type": "string"},
                    "user_demographics": {"type": "object"},
                },
                security_level=SecurityLevel.MEDIUM,
            ),
        }

        super().__init__("cultural_intelligence", operations)

        security_components = security_components or {}
        self.whitelist_system: Optional[CommandWhitelistSystem] = security_components.get("whitelist")
        self.emergency_system: Optional[MultiChannelEmergencyStop] = security_components.get("emergency")
        self.security_logger: Optional[EnhancedSecurityLogging] = security_components.get("logger")
        self.rollback_system: Optional[RollbackRecoverySystem] = security_components.get("rollback")
        self.rate_limiter: Optional[RateLimitingResourceControl] = security_components.get("rate_limiter")

        self.memory_system: Optional[PersistentMemory] = security_components.get("memory")
        if not self.memory_system and PersistentMemory:
            try:
                self.memory_system = PersistentMemory()
            except Exception:  # pragma: no cover
                self.memory_system = None

        self.knowledge_store = CulturalKnowledgeStore(self.memory_system)
        self.auth_validator = CulturalAuthenticityValidator(self.knowledge_store)
        self.research_executor = ResearchExecutor() if ResearchExecutor else None
        self.information_synthesizer = InformationSynthesizer()
        self.sass_learning = AdaptiveSassLearning() if AdaptiveSassLearning else None

        self.metrics: Dict[str, Any] = {
            "research_requests": 0,
            "pattern_analyses": 0,
            "references_validated": 0,
            "authenticity_blocks": 0,
            "memory_updates": 0,
        }

    async def start(self) -> bool:  # type: ignore[override]
        result = await super().start()
        if self.security_logger:
            await self.security_logger.log_security_event(
                "cultural_intelligence_server_started",
                {"has_memory": self.memory_system is not None}
            )
        return result

    async def _validate_operation_security(self, operation_name: str, user_id: str) -> bool:
        if self.emergency_system and self.emergency_system.is_emergency_active():
            if self.security_logger:
                await self.security_logger.log_security_event(
                    "operation_blocked_emergency",
                    {"operation": operation_name, "user_id": user_id}
                )
            return False

        if self.whitelist_system:
            command_key = f"cultural_intelligence:{operation_name}"
            allowed = await self.whitelist_system.is_command_allowed(command_key)
            if not allowed:
                if self.security_logger:
                    await self.security_logger.log_security_event(
                        "operation_blocked_whitelist",
                        {"operation": operation_name, "user_id": user_id}
                    )
                return False

        if self.rate_limiter:
            allowed = await self.rate_limiter.check_rate_limit(user_id, operation_name)
            if not allowed:
                if self.security_logger:
                    await self.security_logger.log_security_event(
                        "operation_blocked_rate_limit",
                        {"operation": operation_name, "user_id": user_id}
                    )
                return False

        return True

    # ------------------------------------------------------------------
    # Cultural research operations
    # ------------------------------------------------------------------
    async def research_cultural_context(
        self,
        topic: str,
        region: str = "california",
        generation: str = "millennial",
        media_focus: Optional[str] = None,
        tone_goal: str = "balanced",
        user_id: str = "anonymous",
    ) -> MCPResult:
        if not await self._validate_operation_security("research_cultural_context", user_id):
            return MCPResult(success=False, error="Operation blocked by security validation")

        if not self.research_executor or not KnowledgeGap or not ResearchQuestion:
            return MCPResult(success=False, error="Autonomous research components unavailable")

        self.metrics["research_requests"] += 1

        gap = KnowledgeGap(
            gap_id=f"culture_gap_{uuid.uuid4().hex[:8]}",
            gap_type=KnowledgeGapType.CONTEXTUAL,
            description=f"Need authentic {region} {generation} communication patterns for {topic}",
            context=f"Topic: {topic}; tone goal: {tone_goal}",
            confidence=0.75,
            priority=7,
            detected_at=datetime.now(),
            conversation_context={"topic": topic, "region": region, "generation": generation},
        )

        question = ResearchQuestion(
            question_id=f"culture_q_{uuid.uuid4().hex[:8]}",
            question=f"What authentic conversational patterns resonate with {generation} audiences in {region} when discussing {topic}?",
            question_type="contextual",
            knowledge_gap_id=gap.gap_id,
            priority=8,
            expected_sources=["positive_media", "regional_interviews", "professional_dialogue"],
            time_estimate=120,
            created_at=datetime.now(),
        )

        scope = ResearchScope.COMPREHENSIVE if media_focus else ResearchScope.QUICK

        plan = await self.research_executor.create_research_plan(
            gap,
            [question],
            research_scope=scope,
            time_limit=180,
        )

        findings = await self.research_executor.execute_research_plan(plan, user_id=user_id)
        synthesis = await self.information_synthesizer.synthesize_research_findings(findings)

        authentic_patterns = self._extract_authentic_patterns(findings, region, generation)
        recommended_media = self._select_positive_media(region, generation, media_focus)

        memory_key = f"cultural::context::{topic.lower()}::{region}::{generation}"
        stored = False
        if self.memory_system and MemoryType:
            payload = {
                "topic": topic,
                "region": region,
                "generation": generation,
                "patterns": authentic_patterns,
                "media": recommended_media,
                "confidence": synthesis.get("confidence", 0.6),
                "summary": synthesis.get("summary"),
                "timestamp": datetime.now().isoformat(),
            }
            stored = self.memory_system.store_memory(
                memory_type=MemoryType.PREFERENCE,
                key=memory_key,
                value=json.dumps(payload, ensure_ascii=True),
                confidence=min(1.0, synthesis.get("confidence", 0.6)),
                context="cultural_research"
            )
            if stored:
                self.metrics["memory_updates"] += 1

        if self.security_logger:
            await self.security_logger.log_security_event(
                "cultural_research_completed",
                {
                    "topic": topic,
                    "region": region,
                    "generation": generation,
                    "confidence": synthesis.get("confidence"),
                    "stored_to_memory": stored,
                }
            )

        return MCPResult(
            success=True,
            data={
                "topic": topic,
                "region": region,
                "generation": generation,
                "research_summary": synthesis.get("summary"),
                "key_patterns": authentic_patterns,
                "recommended_media": recommended_media,
                "confidence": synthesis.get("confidence", 0.6),
                "related_topics": synthesis.get("related_topics", []),
                "stored_memory_key": memory_key if stored else None,
            }
        )

    def _extract_authentic_patterns(
        self,
        findings: List[ResearchFinding],
        region: str,
        generation: str,
    ) -> List[Dict[str, Any]]:
        patterns: List[Dict[str, Any]] = []
        for finding in findings:
            for insight in finding.key_insights:
                patterns.append({
                    "pattern": insight,
                    "region_alignment": region,
                    "generation_alignment": generation,
                    "confidence": round(finding.confidence_level, 2),
                })
        if not patterns:
            defaults = REGIONAL_COMMUNICATION_TRAITS.get(region.lower(), {})
            if defaults:
                patterns.append({
                    "pattern": f"Use {defaults.get('tone', 'warm')} tone with {defaults.get('humor', 'light')} humor cues",
                    "region_alignment": region,
                    "generation_alignment": generation,
                    "confidence": 0.55,
                })
        return patterns[:5]

    def _select_positive_media(
        self,
        region: str,
        generation: str,
        media_focus: Optional[str],
    ) -> List[Dict[str, Any]]:
        results = []
        for item in POSITIVE_MEDIA_LIBRARY:
            region_match = region.lower() in item["regions"] or "global" in item["regions"]
            generation_match = generation.lower() in item["generations"]
            media_match = media_focus is None or item["type"] == media_focus.lower()
            if region_match and generation_match and media_match:
                results.append(item)
        return results[:3]

    # ------------------------------------------------------------------
    # Communication pattern analysis
    # ------------------------------------------------------------------
    async def analyze_communication_patterns(
        self,
        source_type: str,
        sample_transcripts: Optional[List[str]] = None,
        authenticity_filter: bool = True,
        user_id: str = "anonymous",
    ) -> MCPResult:
        if not await self._validate_operation_security("analyze_communication_patterns", user_id):
            return MCPResult(success=False, error="Operation blocked by security validation")

        self.metrics["pattern_analyses"] += 1
        transcripts = sample_transcripts or self._fetch_cached_transcripts(source_type)

        if not transcripts:
            return MCPResult(success=False, error="No transcripts provided or cached for analysis")

        analysis = self._compute_pattern_analysis(transcripts, authenticity_filter)

        if self.security_logger:
            await self.security_logger.log_security_event(
                "communication_pattern_analyzed",
                {"source_type": source_type, "authenticity_filter": authenticity_filter}
            )

        return MCPResult(success=True, data=analysis)

    def _fetch_cached_transcripts(self, source_type: str) -> List[str]:
        pattern = self.knowledge_store.patterns.get(source_type)
        if pattern:
            return pattern.examples
        if source_type.lower() == "positive_media":
            return [
                "It's wild and kind of beautiful how the team refuses to give up, even when the odds are brutal.",
                "Let's break this down together—no pressure, just honest curiosity and a good plan.",
            ]
        return []

    def _compute_pattern_analysis(self, transcripts: List[str], authenticity_filter: bool) -> Dict[str, Any]:
        sentence_lengths = [len(t.split()) for t in transcripts if t]
        average_length = statistics.mean(sentence_lengths) if sentence_lengths else 0.0
        filler_tokens = ["like", "um", "you know"]
        filler_frequency = sum(t.lower().count(token) for token in transcripts for token in filler_tokens)
        emotive_markers = sum(t.count("!") for t in transcripts)

        authenticity_notes = []
        if authenticity_filter and filler_frequency > len(transcripts):
            authenticity_notes.append("Reduce filler words to maintain natural confidence")
        if authenticity_filter and emotive_markers == 0:
            authenticity_notes.append("Consider light enthusiasm markers to avoid monotone delivery")

        return {
            "sample_count": len(transcripts),
            "average_sentence_length": round(average_length, 2),
            "filler_frequency": filler_frequency,
            "emotive_markers": emotive_markers,
            "authenticity_recommendations": authenticity_notes,
            "derived_patterns": self._derive_patterns_from_samples(transcripts),
        }

    def _derive_patterns_from_samples(self, transcripts: List[str]) -> List[Dict[str, Any]]:
        patterns = []
        for text in transcripts[:5]:
            tone = "warm" if "together" in text.lower() else "balanced"
            patterns.append({
                "example": text,
                "tone": tone,
                "observed_traits": [trait for trait in ["uplifting", "collaborative", "supportive"] if trait in text.lower()],
            })
        return patterns

    # ------------------------------------------------------------------
    # Reference validation & response suggestions
    # ------------------------------------------------------------------
    async def validate_cultural_reference(
        self,
        reference: str,
        context: Dict[str, Any],
        appropriateness_check: bool = True,
        user_id: str = "anonymous",
    ) -> MCPResult:
        if not await self._validate_operation_security("validate_cultural_reference", user_id):
            return MCPResult(success=False, error="Operation blocked by security validation")

        self.metrics["references_validated"] += 1
        record = self.knowledge_store.get_reference(reference)

        default_region = (context.get("region") or "global").lower()
        default_generation = (context.get("generation") or "millennial").lower()

        fit_score = 0.6
        reasons = []

        if record:
            if record.region.lower() == default_region or record.region == "global":
                fit_score += 0.15
            if record.generation.lower() == default_generation:
                fit_score += 0.15
            reasons.append("Reference found in cultural knowledge store")
        else:
            reasons.append("Reference not yet in knowledge store; using heuristic analysis")

        validator_context = {
            "conversation": context.get("conversation", ""),
            "topic": context.get("topic", ""),
            "keywords": context.get("keywords", []),
            "sass_level": context.get("sass_level", "medium"),
            "relationship": context.get("relationship", "professional"),
            "sensitive_topics": context.get("sensitive_topics", []),
            "position_in_conversation": context.get("position", "middle"),
            "requires_context": context.get("requires_context", False),
            "requires_depth": context.get("requires_depth", False),
            "authenticity_score": context.get("authenticity_score", 0.7),
        }

        validation = self.auth_validator.validate_usage(reference, validator_context)

        if not validation["all_checks_passed"] and appropriateness_check:
            self.metrics["authenticity_blocks"] += 1

        risk = self.auth_validator.assess_risk(reference, validator_context)

        if self.security_logger:
            await self.security_logger.log_security_event(
                "cultural_reference_validated",
                {
                    "reference": reference,
                    "fit_score": fit_score,
                    "checks_passed": validation["all_checks_passed"],
                    "risk_level": risk["risk_level"],
                }
            )

        return MCPResult(
            success=True,
            data={
                "reference": reference,
                "fit_score": round(min(1.0, fit_score), 2),
                "validation": validation,
                "risk": risk,
                "recommendation": "safe_to_use" if validation["all_checks_passed"] else "revise_before_use",
                "record_found": record is not None,
            }
        )

    async def suggest_authentic_responses(
        self,
        conversation_context: Dict[str, Any],
        personality_constraints: Optional[Dict[str, Any]] = None,
        user_id: str = "anonymous",
    ) -> MCPResult:
        if not await self._validate_operation_security("suggest_authentic_responses", user_id):
            return MCPResult(success=False, error="Operation blocked by security validation")

        sass_level = self._determine_sass_level(conversation_context, personality_constraints)
        region = (conversation_context.get("region") or "california").lower()
        generation = (conversation_context.get("generation") or "millennial").lower()

        suggestions = []
        base_response = conversation_context.get("user_message", "Thanks for the context—let's tackle this together.")
        cultural_elements = conversation_context.get("cultural_elements", [])

        for style in ["supportive", "playful", "direct"]:
            authenticity = self.auth_validator.validate_usage(
                element=base_response,
                context={
                    "conversation": conversation_context.get("conversation_history", ""),
                    "topic": conversation_context.get("topic", ""),
                    "relationship": conversation_context.get("relationship", "professional"),
                    "sass_level": sass_level.value if hasattr(sass_level, "value") else str(sass_level),
                    "keywords": conversation_context.get("keywords", []),
                }
            )

            suggestions.append({
                "style": style,
                "response": self._compose_response(base_response, style, region, generation, cultural_elements),
                "sass_level": sass_level.value if hasattr(sass_level, "value") else sass_level,
                "authenticity": authenticity,
            })

        return MCPResult(success=True, data={"suggestions": suggestions})

    def _determine_sass_level(
        self,
        conversation_context: Dict[str, Any],
        personality_constraints: Optional[Dict[str, Any]],
    ):
        if personality_constraints and personality_constraints.get("sass_level"):
            level = personality_constraints["sass_level"]
            try:
                return SassLevel(level)
            except Exception:
                pass
        if self.sass_learning:
            learned = self.sass_learning.get_learned_sass_for_context({
                "topic": conversation_context.get("topic", "general"),
                "emotion": conversation_context.get("user_emotion", "neutral"),
                "participants": conversation_context.get("participants", []),
            })
            if learned:
                return learned
        return SassLevel.MEDIUM if hasattr(SassLevel, "MEDIUM") else "medium"

    def _compose_response(
        self,
        base: str,
        style: str,
        region: str,
        generation: str,
        elements: List[str],
    ) -> str:
        tone_prefix = {
            "supportive": "Hey, I got you—",
            "playful": "Alright, here's a fun take—",
            "direct": "Let's cut to it—",
        }.get(style, "Let's do this—")

        regional_trait = REGIONAL_COMMUNICATION_TRAITS.get(region, {})
        vocabulary = regional_trait.get("vocabulary", [])
        vocab_snippet = vocabulary[0] + ": " if vocabulary else ""

        reference_snippet = ""
        if elements:
            reference_snippet = f"Remember {elements[0]}? "

        return f"{tone_prefix} {vocab_snippet}{reference_snippet}{base}"

    # ------------------------------------------------------------------
    # Communication style adaptation
    # ------------------------------------------------------------------
    async def adapt_communication_style(
        self,
        target_audience: Dict[str, Any],
        existing_personality: Dict[str, Any],
        conversation_goal: str = "maintain_relationship",
        user_id: str = "anonymous",
    ) -> MCPResult:
        if not await self._validate_operation_security("adapt_communication_style", user_id):
            return MCPResult(success=False, error="Operation blocked by security validation")

        region = (target_audience.get("region") or "california").lower()
        generation = (target_audience.get("generation") or "millennial").lower()

        regional_traits = REGIONAL_COMMUNICATION_TRAITS.get(region, {})
        generational_traits = GENERATIONAL_REFERENCE_GUARDRAILS.get(generation, {})

        adaptation_plan = {
            "tone_adjustments": {
                "current": existing_personality.get("tone", "balanced"),
                "recommended": generational_traits.get("tone", regional_traits.get("tone", "balanced")),
            },
            "vocabulary": {
                "keep": existing_personality.get("signature_phrases", [])[:3],
                "add": regional_traits.get("vocabulary", [])[:2],
                "avoid": generational_traits.get("avoid", []),
            },
            "sass_level": existing_personality.get("sass_level", "medium"),
            "humor_style": regional_traits.get("humor", "warm"),
            "conversation_goal": conversation_goal,
        }

        return MCPResult(success=True, data=adaptation_plan)

    async def generate_contextual_references(
        self,
        topic: str,
        cultural_background: Dict[str, Any],
        confidence_threshold: float = 0.8,
        user_id: str = "anonymous",
    ) -> MCPResult:
        if not await self._validate_operation_security("generate_contextual_references", user_id):
            return MCPResult(success=False, error="Operation blocked by security validation")

        region = (cultural_background.get("region") or "california").lower()
        generation = (cultural_background.get("generation") or "millennial").lower()
        tone = cultural_background.get("tone", "balanced")

        references: List[CulturalReferenceRecord] = []
        for media in self._select_positive_media(region, generation, media_focus=None):
            confidence = 0.85 if media["tone"] == tone else 0.78
            if confidence >= confidence_threshold:
                record = CulturalReferenceRecord(
                    reference=media["title"],
                    region=region,
                    generation=generation,
                    tone=media["tone"],
                    media_type=media["type"],
                    positivity_score=0.9,
                    context_notes=f"Aligns with {topic} conversations",
                    confidence=confidence,
                )
                references.append(record)

        for record in references:
            self.knowledge_store.store_reference(record)
            self.metrics["memory_updates"] += 1

        payload = [asdict(record) for record in references]
        return MCPResult(success=True, data={"references": payload})

    async def store_communication_pattern(
        self,
        pattern_type: str,
        usage_context: Dict[str, Any],
        effectiveness_score: float,
        examples: Optional[List[str]] = None,
        user_id: str = "anonymous",
    ) -> MCPResult:
        if not await self._validate_operation_security("store_communication_pattern", user_id):
            return MCPResult(success=False, error="Operation blocked by security validation")

        authenticity_context = {
            "conversation": usage_context.get("conversation", ""),
            "topic": usage_context.get("topic", ""),
            "relationship": usage_context.get("relationship", "professional"),
            "sass_level": usage_context.get("sass_level", "medium"),
        }
        authenticity_check = self.auth_validator.validate_usage(pattern_type, authenticity_context)
        authenticity_score = 1.0 if authenticity_check["all_checks_passed"] else 0.6

        record = CulturalPatternRecord(
            pattern_type=pattern_type,
            usage_context=usage_context,
            effectiveness_score=effectiveness_score,
            authenticity_score=authenticity_score,
            examples=examples or [],
        )
        self.knowledge_store.store_pattern(record)
        self.metrics["memory_updates"] += 1

        return MCPResult(
            success=True,
            data={
                "stored": True,
                "authenticity": authenticity_check,
                "pattern_type": pattern_type,
            }
        )

    async def analyze_conversation_effectiveness(
        self,
        conversation_history: List[Dict[str, Any]],
        cultural_elements: List[str],
        user_feedback: Optional[Dict[str, Any]] = None,
        user_id: str = "anonymous",
    ) -> MCPResult:
        if not await self._validate_operation_security("analyze_conversation_effectiveness", user_id):
            return MCPResult(success=False, error="Operation blocked by security validation")

        authenticity_scores = []
        for element in cultural_elements:
            context = {
                "conversation": " ".join(turn.get("assistant", "") for turn in conversation_history),
                "topic": user_feedback.get("topic", "") if user_feedback else "",
                "relationship": user_feedback.get("relationship", "professional") if user_feedback else "professional",
                "sass_level": user_feedback.get("sass_level", "medium") if user_feedback else "medium",
            }
            result = self.auth_validator.validate_usage(element, context)
            authenticity_scores.append(1.0 if result["all_checks_passed"] else 0.6)

        engagement_indicators = [
            turn.get("user_reaction", "neutral") for turn in conversation_history if turn.get("user_reaction")
        ]

        effectiveness = {
            "authenticity_score": round(statistics.mean(authenticity_scores), 2) if authenticity_scores else 0.0,
            "engagement_indicators": engagement_indicators,
            "feedback_summary": user_feedback or {},
            "recommendations": self._derive_effectiveness_recommendations(authenticity_scores, engagement_indicators),
        }

        return MCPResult(success=True, data=effectiveness)

    def _derive_effectiveness_recommendations(
        self,
        authenticity_scores: List[float],
        engagement_indicators: List[str],
    ) -> List[str]:
        recommendations = []
        if authenticity_scores and statistics.mean(authenticity_scores) < 0.7:
            recommendations.append("Tone down cultural references until authenticity improves")
        if engagement_indicators.count("positive") < engagement_indicators.count("neutral"):
            recommendations.append("Invite user reflection to gauge resonance")
        if not recommendations:
            recommendations.append("Maintain current blend—users responding well")
        return recommendations

    async def update_cultural_knowledge(
        self,
        new_information: Dict[str, Any],
        source_credibility: float,
        integration_strategy: str = "append",
        user_id: str = "anonymous",
    ) -> MCPResult:
        if not await self._validate_operation_security("update_cultural_knowledge", user_id):
            return MCPResult(success=False, error="Operation blocked by security validation")

        topic = new_information.get("topic", "general")
        region = new_information.get("region", "global")
        key = f"cultural::knowledge::{topic}::{region}"

        if not self.memory_system or not MemoryType:
            return MCPResult(success=False, error="Persistent memory system unavailable")

        existing = self.memory_system.recall_memory(MemoryType.PREFERENCE, key)
        payload = {}
        if existing:
            try:
                payload = json.loads(existing.value)
            except (json.JSONDecodeError, TypeError):
                payload = {}

        if integration_strategy == "replace":
            payload = new_information
        else:
            payload.update(new_information)

        payload["source_credibility"] = source_credibility
        payload["updated_at"] = datetime.now().isoformat()

        stored = self.memory_system.store_memory(
            memory_type=MemoryType.PREFERENCE,
            key=key,
            value=json.dumps(payload, ensure_ascii=True),
            confidence=min(1.0, source_credibility),
            context="cultural_update"
        )

        if stored:
            self.metrics["memory_updates"] += 1

        return MCPResult(success=stored, data={"stored": stored, "key": key})

    async def assess_authenticity_risk(
        self,
        proposed_response: str,
        cultural_elements: List[str],
        user_profile: Optional[Dict[str, Any]] = None,
        user_id: str = "anonymous",
    ) -> MCPResult:
        if not await self._validate_operation_security("assess_authenticity_risk", user_id):
            return MCPResult(success=False, error="Operation blocked by security validation")

        profile = user_profile or {}
        context = {
            "conversation": profile.get("recent_conversation", ""),
            "topic": profile.get("topic", ""),
            "relationship": profile.get("relationship", "professional"),
            "sass_level": profile.get("sass_level", "medium"),
            "keywords": profile.get("keywords", []),
            "sensitive_topics": profile.get("sensitive_topics", []),
        }

        risks = [self.auth_validator.assess_risk(element, context) for element in cultural_elements]
        combined_risk = "low"
        if any(r["risk_level"] == "high" for r in risks):
            combined_risk = "high"
        elif any(r["risk_level"] == "medium" for r in risks):
            combined_risk = "medium"

        response_validation = self.auth_validator.validate_usage(proposed_response, context)

        return MCPResult(
            success=True,
            data={
                "combined_risk": combined_risk,
                "element_risks": risks,
                "response_validation": response_validation,
            }
        )

    async def filter_inappropriate_references(
        self,
        content: List[str],
        sensitivity_guidelines: Dict[str, Any],
        user_id: str = "anonymous",
    ) -> MCPResult:
        if not await self._validate_operation_security("filter_inappropriate_references", user_id):
            return MCPResult(success=False, error="Operation blocked by security validation")

        filtered = []
        removed = []
        banned_terms = [term.lower() for term in sensitivity_guidelines.get("banned_terms", [])]
        avoid_regions = [region.lower() for region in sensitivity_guidelines.get("avoid_regions", [])]

        for item in content:
            reference = self.knowledge_store.get_reference(item)
            if reference and reference.region.lower() in avoid_regions:
                removed.append({"reference": item, "reason": "region_sensitivity"})
                continue
            if any(term in item.lower() for term in banned_terms):
                removed.append({"reference": item, "reason": "term_match"})
                continue
            filtered.append(item)

        return MCPResult(
            success=True,
            data={
                "approved": filtered,
                "removed": removed,
            }
        )

    async def validate_generational_appropriateness(
        self,
        reference: str,
        user_demographics: Dict[str, Any],
        user_id: str = "anonymous",
    ) -> MCPResult:
        if not await self._validate_operation_security("validate_generational_appropriateness", user_id):
            return MCPResult(success=False, error="Operation blocked by security validation")

        generation = (user_demographics.get("generation") or "millennial").lower()
        record = self.knowledge_store.get_reference(reference)

        guardrails = GENERATIONAL_REFERENCE_GUARDRAILS.get(generation, {})
        appropriateness = {
            "reference": reference,
            "generation": generation,
            "safe": True,
            "notes": [],
        }

        if record and record.generation != generation and record.generation != "multigenerational":
            appropriateness["safe"] = False
            appropriateness["notes"].append("Reference aligned with different generation")

        if any(term in reference.lower() for term in guardrails.get("avoid", [])):
            appropriateness["safe"] = False
            appropriateness["notes"].append("Contains avoided terminology for this generation")

        if not guardrails:
            appropriateness["notes"].append("No guardrails found; defaulting to safe")

        return MCPResult(success=True, data=appropriateness)

    async def get_metrics(self) -> Dict[str, Any]:
        return self.metrics.copy()


async def create_cultural_intelligence_server(
    security_components: Optional[Dict[str, Any]] = None,
) -> CulturalIntelligenceToolServer:
    server = CulturalIntelligenceToolServer(security_components)
    await server.start()
    return server


if __name__ == "__main__":  # pragma: no cover - manual demonstration
    async def demo():
        server = await create_cultural_intelligence_server()
        try:
            research = await server.research_cultural_context(
                topic="mentoring junior engineers",
                region="california",
                generation="millennial",
            )
            print("Research:", json.dumps(research.data, indent=2))

            validation = await server.validate_cultural_reference(
                reference="Ted Lasso",
                context={"topic": "team morale", "relationship": "professional"},
            )
            print("Validation:", json.dumps(validation.data, indent=2))
        finally:
            await server.stop()

    asyncio.run(demo())
