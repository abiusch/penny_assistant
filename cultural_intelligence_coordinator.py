"""
Cultural Intelligence Coordinator
Integrates the cultural intelligence MCP server with Penny's conversation system
and MCP registry, providing authenticity-aware response enhancement utilities.
"""

import asyncio
import threading
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple, Union, Awaitable, Callable, TYPE_CHECKING

from cultural_intelligence_tool_server import create_cultural_intelligence_server, MCPResult

try:
    from persistent_memory import PersistentMemory
except ImportError:  # pragma: no cover
    PersistentMemory = None  # type: ignore

# MCP registry types (optional when registry integration is used)
try:  # pragma: no cover - optional dependency in some environments
    from mcp_tool_registry import (
        MCPToolRegistry,
        ToolCategory,
        ToolCapabilityType,
    )
    from command_whitelist_system import SecurityRisk, OperationType, PermissionLevel
except ImportError:  # pragma: no cover
    MCPToolRegistry = None  # type: ignore
    ToolCategory = None  # type: ignore
    ToolCapabilityType = None  # type: ignore
    SecurityRisk = None  # type: ignore
    OperationType = None  # type: ignore
    PermissionLevel = None  # type: ignore


if TYPE_CHECKING:
    from conversation_telemetry_system import ConversationTelemetrySystem


@dataclass
class CulturalEnhancementResult:
    """Represents the decision made by the cultural intelligence coordinator."""

    response: str
    used_cultural_enhancement: bool
    decision: str
    metrics: Dict[str, Any]
    context: Dict[str, Any]


class _AsyncLoopRunner:
    """Runs an asyncio event loop in a background thread for sync contexts."""

    def __init__(self) -> None:
        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    def _run_loop(self) -> None:  # pragma: no cover - thread loop
        asyncio.set_event_loop(self._loop)
        self._loop.run_forever()

    def run(self, coro: Awaitable[Any]) -> Any:
        future = asyncio.run_coroutine_threadsafe(coro, self._loop)
        return future.result()

    def shutdown(self) -> None:
        self._loop.call_soon_threadsafe(self._loop.stop)
        self._thread.join(timeout=1.0)


class CulturalIntelligenceCoordinator:
    """Core coordinator that speaks to the cultural intelligence MCP server."""

    OPERATION_REGISTRY_METADATA: Dict[str, Dict[str, Any]] = {
        "research_cultural_context": {
            "description": "Research authentic conversational patterns for a topic",
            "schema": {
                "type": "object",
                "properties": {
                    "topic": {"type": "string"},
                    "region": {"type": ["string", "null"], "default": "california"},
                    "generation": {"type": ["string", "null"], "default": "millennial"},
                    "media_focus": {"type": ["string", "null"]},
                    "tone_goal": {"type": ["string", "null"]},
                },
                "required": ["topic"],
            },
        },
        "analyze_communication_patterns": {
            "description": "Analyze transcripts for conversational authenticity cues",
            "schema": {
                "type": "object",
                "properties": {
                    "source_type": {"type": "string"},
                    "sample_transcripts": {"type": "array"},
                    "authenticity_filter": {"type": "boolean", "default": True},
                },
                "required": ["source_type"],
            },
        },
        "validate_cultural_reference": {
            "description": "Validate if a cultural reference fits the current context",
            "schema": {
                "type": "object",
                "properties": {
                    "reference": {"type": "string"},
                    "context": {"type": "object"},
                    "appropriateness_check": {"type": "boolean", "default": True},
                },
                "required": ["reference", "context"],
            },
        },
        "suggest_authentic_responses": {
            "description": "Suggest culturally aware variants of a response",
            "schema": {
                "type": "object",
                "properties": {
                    "conversation_context": {"type": "object"},
                    "personality_constraints": {"type": "object"},
                },
                "required": ["conversation_context"],
            },
        },
        "adapt_communication_style": {
            "description": "Adapt communication style for a target audience",
            "schema": {
                "type": "object",
                "properties": {
                    "target_audience": {"type": "object"},
                    "existing_personality": {"type": "object"},
                    "conversation_goal": {"type": "string"},
                },
                "required": ["target_audience", "existing_personality"],
            },
        },
        "generate_contextual_references": {
            "description": "Generate contextual cultural references",
            "schema": {
                "type": "object",
                "properties": {
                    "topic": {"type": "string"},
                    "cultural_background": {"type": "object"},
                    "confidence_threshold": {"type": "number", "default": 0.8},
                },
                "required": ["topic", "cultural_background"],
            },
        },
        "store_communication_pattern": {
            "description": "Store a cultural communication pattern",
            "schema": {
                "type": "object",
                "properties": {
                    "pattern_type": {"type": "string"},
                    "usage_context": {"type": "object"},
                    "effectiveness_score": {"type": "number"},
                    "examples": {"type": "array"},
                },
                "required": ["pattern_type", "usage_context", "effectiveness_score"],
            },
        },
        "analyze_conversation_effectiveness": {
            "description": "Analyze effectiveness of cultural elements in a conversation",
            "schema": {
                "type": "object",
                "properties": {
                    "conversation_history": {"type": "array"},
                    "cultural_elements": {"type": "array"},
                    "user_feedback": {"type": "object"},
                },
                "required": ["conversation_history", "cultural_elements"],
            },
        },
        "update_cultural_knowledge": {
            "description": "Persist newly learned cultural knowledge",
            "schema": {
                "type": "object",
                "properties": {
                    "new_information": {"type": "object"},
                    "source_credibility": {"type": "number"},
                    "integration_strategy": {"type": "string"},
                },
                "required": ["new_information", "source_credibility"],
            },
        },
        "assess_authenticity_risk": {
            "description": "Assess authenticity risk for a proposed response",
            "schema": {
                "type": "object",
                "properties": {
                    "proposed_response": {"type": "string"},
                    "cultural_elements": {"type": "array"},
                    "user_profile": {"type": "object"},
                },
                "required": ["proposed_response", "cultural_elements"],
            },
        },
        "filter_inappropriate_references": {
            "description": "Filter out inappropriate cultural references",
            "schema": {
                "type": "object",
                "properties": {
                    "content": {"type": "array"},
                    "sensitivity_guidelines": {"type": "object"},
                },
                "required": ["content", "sensitivity_guidelines"],
            },
        },
        "validate_generational_appropriateness": {
            "description": "Validate if a reference fits user demographics",
            "schema": {
                "type": "object",
                "properties": {
                    "reference": {"type": "string"},
                    "user_demographics": {"type": "object"},
                },
                "required": ["reference", "user_demographics"],
            },
        },
    }

    def __init__(self,
                 server,
                 default_region: str = "california",
                 default_generation: str = "millennial",
                 metadata: Optional[Dict[str, Any]] = None,
                 telemetry: Optional["ConversationTelemetrySystem"] = None):
        self.server = server
        self.default_region = default_region
        self.default_generation = default_generation
        self.metadata = metadata or {}
        self.metrics_history: List[Dict[str, Any]] = []
        self.telemetry = telemetry

    @classmethod
    async def create(cls,
                     default_region: str = "california",
                     default_generation: str = "millennial",
                     security_components: Optional[Dict[str, Any]] = None,
                     memory_path: Optional[str] = None,
                     telemetry: Optional["ConversationTelemetrySystem"] = None) -> "CulturalIntelligenceCoordinator":
        components = dict(security_components or {})
        if memory_path and PersistentMemory is not None:
            components['memory'] = PersistentMemory(memory_path)
        server = await create_cultural_intelligence_server(components or None)
        return cls(server, default_region, default_generation, telemetry=telemetry)

    async def shutdown(self) -> None:
        await self.server.stop()

    async def register_with_registry(self, registry: MCPToolRegistry) -> bool:
        """Register cultural intelligence operations with the MCP tool registry."""
        if MCPToolRegistry is None or registry is None:
            return False

        success = True
        for operation, meta in self.OPERATION_REGISTRY_METADATA.items():
            tool_name = f"cultural_intelligence.{operation}"

            async def executor(args: Dict[str, Any], op=operation):
                return await self._call(op, **args)

            registered = await registry.register_inline_tool(
                tool_name=tool_name,
                description=meta["description"],
                input_schema=meta["schema"],
                executor=executor,
                category=ToolCategory.COMMUNICATION if ToolCategory else None,
                capabilities=[ToolCapabilityType.READ_ONLY] if ToolCapabilityType else None,
                security_risk=SecurityRisk.LOW if SecurityRisk else None,
                operation_type=OperationType.COMMUNICATION if OperationType else None,
                required_permissions=[PermissionLevel.AUTHENTICATED] if PermissionLevel else None,
            )
            success &= registered
        return success

    async def enhance_response(self,
                               user_input: str,
                               conversation_history: List[Dict[str, str]],
                               base_response: str,
                               metadata: Optional[Dict[str, Any]] = None) -> CulturalEnhancementResult:
        """Assess and optionally enhance a response with cultural intelligence."""

        metadata = metadata or {}
        start_time = time.time()

        region = metadata.get("region", self.default_region)
        generation = metadata.get("generation", self.default_generation)
        topic = metadata.get("topic") or self._infer_topic(user_input)
        relationship = metadata.get("relationship", "professional")
        sass_level = metadata.get("sass_level", "medium")
        tone_goal = metadata.get("tone", "balanced")

        conversation_summary = self._summarize_history(conversation_history)
        keywords = self._extract_keywords(user_input)

        personality_constraints = {
            "sass_level": sass_level,
            "personality_mode": metadata.get("personality_mode", "balanced"),
        }
        conversation_context = {
            "user_message": user_input,
            "conversation_history": conversation_summary,
            "topic": topic,
            "region": region,
            "generation": generation,
            "relationship": relationship,
            "keywords": keywords,
            "sass_level": sass_level,
            "conversation": conversation_summary,
        }

        references_data = await self._call(
            "generate_contextual_references",
            topic=topic,
            cultural_background={
                "region": region,
                "generation": generation,
                "tone": tone_goal,
            },
            confidence_threshold=float(metadata.get("confidence_threshold", 0.75)),
        )

        base_risk = await self._call(
            "assess_authenticity_risk",
            proposed_response=base_response,
            cultural_elements=[],
            user_profile={
                "relationship": relationship,
                "topic": topic,
                "sass_level": sass_level,
                "keywords": keywords,
            },
        )
        base_validation = base_risk.get("response_validation", {}) if isinstance(base_risk, dict) else {}
        base_score = self._authenticity_score(base_validation)

        suggestions_payload = await self._call(
            "suggest_authentic_responses",
            conversation_context=conversation_context,
            personality_constraints=personality_constraints,
        )
        suggestions = suggestions_payload.get("suggestions", []) if isinstance(suggestions_payload, dict) else []
        guardrail_disable = topic == "technology" and relationship == "professional"
        if guardrail_disable:
            suggestions = []

        best_choice = None
        best_score = base_score
        min_gain = 0.05
        min_score = 0.6
        if topic in {"technology", "work_stress"} or relationship == "professional":
            min_gain = 0.12
            min_score = 0.72
        restricted_styles = {"supportive", "playful"} if topic == "technology" and relationship == "professional" else set()

        for suggestion in suggestions:
            validation = suggestion.get("authenticity", {})
            score = self._authenticity_score(validation)
            if validation.get("forced_usage_detected"):
                continue
            if suggestion.get("style") in restricted_styles:
                continue
            if score >= best_score + min_gain and score >= min_score:
                best_choice = {
                    "style": suggestion.get("style"),
                    "response": suggestion.get("response", base_response),
                    "authenticity": validation,
                    "score": score,
                }
                best_score = score

        if best_choice and base_score >= 0.75 and (best_score - base_score) < 0.15:
            best_choice = None
            best_score = base_score

        used_enhancement = best_choice is not None
        chosen_response = best_choice["response"] if best_choice else base_response
        decision = "enhanced" if used_enhancement else "base"

        reference_used = self._detect_reference(chosen_response, references_data.get("references", []) if isinstance(references_data, dict) else [])

        metrics = {
            "base_authenticity_score": round(base_score, 3),
            "enhanced_authenticity_score": round(best_score, 3),
            "improvement": round(best_score - base_score, 3),
            "reference_used": reference_used,
            "latency_ms": round((time.time() - start_time) * 1000, 2),
            "forced_detected": bool(best_choice and best_choice["authenticity"].get("forced_usage_detected")),
            "conversation_flow_disruption": 0 if used_enhancement else 0,
            "engagement_projection": self._estimate_engagement_delta(base_score, best_score),
        }

        context_details = {
            "topic": topic,
            "region": region,
            "generation": generation,
            "relationship": relationship,
            "references_considered": references_data.get("references", []) if isinstance(references_data, dict) else [],
            "base_validation": base_validation,
            "selected_suggestion": best_choice,
            "all_suggestions": suggestions,
        }

        if used_enhancement:
            try:
                await self._call(
                    "store_communication_pattern",
                    pattern_type=f"cultural_{best_choice['style']}",
                    usage_context={
                        "topic": topic,
                        "relationship": relationship,
                        "sass_level": sass_level,
                        "conversation": conversation_summary,
                    },
                    effectiveness_score=max(0.0, best_score - base_score),
                    examples=[chosen_response],
                )
            except Exception:
                pass  # Best-effort storage

        await self._record_telemetry(
            decision=decision,
            user_input=user_input,
            base_response=base_response,
            chosen_response=chosen_response,
            conversation_history=conversation_history,
            metadata=metadata,
            metrics=metrics,
        )

        self.metrics_history.append(metrics)

        return CulturalEnhancementResult(
            response=chosen_response,
            used_cultural_enhancement=used_enhancement,
            decision=decision,
            metrics=metrics,
            context=context_details,
        )

    async def _call(self, operation: str, **kwargs) -> Dict[str, Any]:
        """Invoke an operation on the cultural intelligence server."""
        method = getattr(self.server, operation, None)
        if not method:
            raise AttributeError(f"Cultural intelligence operation not found: {operation}")
        result = await method(**kwargs)
        if isinstance(result, MCPResult):
            if not result.success:
                return {"error": result.error, "success": False}
            return result.data or {}
        return result

    def _authenticity_score(self, validation: Dict[str, Any]) -> float:
        if not validation:
            return 0.5
        total_checks = 6  # natural_fit, personality_match, appropriate_timing, cultural_sensitivity, user_relationship, no_forced_usage
        failed = validation.get("failed_checks", [])
        score = max(0.0, (total_checks - len(failed)) / total_checks)
        return float(score)

    def _summarize_history(self, history: List[Dict[str, str]], limit: int = 5) -> str:
        turns = history[-limit:]
        summary_parts = []
        for turn in turns:
            user = turn.get("user", "")
            assistant = turn.get("assistant", "")
            summary_parts.append(f"User: {user}")
            summary_parts.append(f"Penny: {assistant}")
        return " \n".join(summary_parts)

    def _extract_keywords(self, text: str, limit: int = 6) -> List[str]:
        tokens = [token.strip(".,!?\n ") for token in text.split() if len(token) > 3]
        seen = []
        for token in tokens:
            lower = token.lower()
            if lower not in seen:
                seen.append(lower)
            if len(seen) >= limit:
                break
        return seen

    def _infer_topic(self, text: str) -> str:
        lower = text.lower()
        if any(word in lower for word in ["deploy", "bug", "code", "api", "server", "build"]):
            return "technology"
        if any(word in lower for word in ["friend", "family", "relationship", "partner", "josh", "reneille"]):
            return "relationships"
        if any(word in lower for word in ["stress", "overwhelmed", "burnout", "tired"]):
            return "wellbeing"
        return "general"

    def _detect_reference(self, response: str, references: List[Dict[str, Any]]) -> Optional[str]:
        response_lower = response.lower()
        for item in references:
            title = str(item.get("title", ""))
            if title and title.lower() in response_lower:
                return title
        return None

    def _estimate_engagement_delta(self, base_score: float, enhanced_score: float) -> float:
        return round(enhanced_score - base_score, 3)

    async def _record_telemetry(self,
                                decision: str,
                                user_input: str,
                                base_response: str,
                                chosen_response: str,
                                conversation_history: List[Dict[str, str]],
                                metadata: Dict[str, Any],
                                metrics: Dict[str, Any]) -> None:
        if not getattr(self, "telemetry", None):
            return

        try:
            session_id = metadata.get("session_id", "unknown_session")
            context_payload = {
                "topic": metadata.get("topic"),
                "relationship": metadata.get("relationship"),
                "generation": metadata.get("generation", self.default_generation),
                "region": metadata.get("region", self.default_region),
                "session_id": session_id,
            }
            await self.telemetry.log_cultural_decision(decision, context_payload, metrics)

            extended_history = conversation_history + [{
                "user": user_input,
                "assistant": chosen_response,
            }]
            flow_metadata = {"session_id": session_id, "decision": decision}
            flow_metrics = await self.telemetry.measure_conversation_flow(extended_history, flow_metadata)

            engagement_payload = {
                "turn_count": len(extended_history),
                "cultural_decision": decision,
                "latency_ms": metrics.get("latency_ms"),
                "response_appropriateness": flow_metrics.get("response_appropriateness"),
                "conversation_stability": flow_metrics.get("conversation_stability"),
            }
            await self.telemetry.track_engagement_metrics(session_id, engagement_payload)

            baseline = metadata.get("personality_baseline") or {
                "keywords": metadata.get("personality_keywords", ["balanced"])
            }
            await self.telemetry.assess_personality_consistency(
                [base_response, chosen_response],
                baseline,
            )
        except Exception:
            # Telemetry should not interfere with response generation.
            pass


class CulturalIntelligenceAdapter:
    """Synchronous adapter for pipeline usage."""

    def __init__(self,
                 coordinator: CulturalIntelligenceCoordinator,
                 loop_runner: _AsyncLoopRunner):
        self._coordinator = coordinator
        self._loop_runner = loop_runner
        self.enabled = True

    @classmethod
    def create(cls,
               default_region: str = "california",
               default_generation: str = "millennial",
               memory_path: Optional[str] = None,
               telemetry: Optional["ConversationTelemetrySystem"] = None) -> "CulturalIntelligenceAdapter":
        runner = _AsyncLoopRunner()
        coordinator = runner.run(
            CulturalIntelligenceCoordinator.create(
                default_region=default_region,
                default_generation=default_generation,
                memory_path=memory_path,
                telemetry=telemetry
            )
        )
        return cls(coordinator, runner)

    def enhance_response(self,
                         user_input: str,
                         conversation_history: List[Dict[str, str]],
                         base_response: str,
                         metadata: Optional[Dict[str, Any]] = None) -> CulturalEnhancementResult:
        if not self.enabled:
            return CulturalEnhancementResult(
                response=base_response,
                used_cultural_enhancement=False,
                decision="disabled",
                metrics={
                    "base_authenticity_score": 0.0,
                    "enhanced_authenticity_score": 0.0,
                    "improvement": 0.0,
                    "reference_used": None,
                    "latency_ms": 0.0,
                    "forced_detected": False,
                    "conversation_flow_disruption": 0,
                    "engagement_projection": 0.0,
                },
                context={"reason": "cultural_intelligence_disabled"}
            )
        return self._loop_runner.run(
            self._coordinator.enhance_response(
                user_input=user_input,
                conversation_history=conversation_history,
                base_response=base_response,
                metadata=metadata
            )
        )

    def register_with_registry(self, registry: MCPToolRegistry) -> bool:
        if MCPToolRegistry is None or registry is None:
            return False
        return self._loop_runner.run(self._coordinator.register_with_registry(registry))

    def shutdown(self) -> None:
        try:
            self._loop_runner.run(self._coordinator.shutdown())
        finally:
            self._loop_runner.shutdown()
