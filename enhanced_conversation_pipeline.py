#!/usr/bin/env python3
"""
Enhanced Conversation Pipeline with Flow Management
Integrates conversational flow and relationship building with the existing pipeline
"""

import sys
import os
import time
import uuid
from typing import Optional, Dict, Any

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
sys.path.insert(0, os.path.dirname(__file__))

from src.core.pipeline import PipelineLoop, State
from memory_system import MemoryManager
from emotional_memory_system import create_enhanced_memory_system
from personality_integration import create_personality_integration
from conversational_flow_system import create_conversational_flow, ConversationState
from cultural_intelligence_coordinator import CulturalIntelligenceAdapter, CulturalEnhancementResult
from conversation_telemetry_system import TelemetryClient
from production_a_b_testing import ProductionABTesting


# Health monitor with safe fallback
class NullHealthMonitor:
    """Null object pattern for health monitor when unavailable."""
    async def check_all_components(self):
        return {
            "status": "health_monitor_disabled",
            "message": "Health monitoring temporarily disabled"
        }


class EnhancedConversationPipeline(PipelineLoop):
    """Enhanced pipeline with full conversational flow and relationship building."""
    
    def __init__(self):
        super().__init__()
        
        # Initialize layered systems
        base_memory = MemoryManager()
        self.memory = create_enhanced_memory_system(base_memory)
        self.personality_integration = create_personality_integration(self.memory)
        self.conversation_flow = create_conversational_flow(self.memory, self.personality_integration)

        # Cultural intelligence integration
        self.cultural_history = []
        self.session_id = f"session_{uuid.uuid4().hex}"
        self.telemetry_client: Optional[TelemetryClient] = None
        self.ab_testing: Optional[ProductionABTesting] = None
        self.cultural_enabled = True
        try:
            self.telemetry_client = TelemetryClient()
        except Exception as exc:
            self.telemetry_client = None
            print(f"⚠️ Telemetry client disabled: {exc}")

        try:
            self.ab_testing = ProductionABTesting(self.telemetry_client.telemetry) if self.telemetry_client else None
        except Exception as exc:
            self.ab_testing = None
            print(f"⚠️ A/B testing disabled: {exc}")

        try:
            telemetry = self.telemetry_client.telemetry if self.telemetry_client else None
            self.cultural_adapter = CulturalIntelligenceAdapter.create(
                telemetry=telemetry
            )
            if self.ab_testing and self.telemetry_client:
                self.cultural_enabled = self.telemetry_client.run(
                    self.ab_testing.randomly_assign_cultural_mode("default_user", self.session_id)
                )
                self.cultural_adapter.enabled = self.cultural_enabled
            print("🎨 Cultural intelligence adapter ready")
        except Exception as e:
            self.cultural_adapter = None
            print(f"⚠️ Cultural intelligence adapter disabled: {e}")
        
        # Initialize health monitor with safe fallback
        try:
            from health_monitor import PennyGPTHealthMonitor
            self.health_monitor = PennyGPTHealthMonitor()
            print("🏥 Health monitor initialized")
        except Exception as e:
            self.health_monitor = NullHealthMonitor()
            print(f"⚠️ Health monitor disabled: {e}")
        
        print("🚀 Enhanced conversation pipeline with full flow management initialized")
    
    def should_process_without_wake_word(self, user_text: str) -> bool:
        """Determine if we should process input without requiring wake word."""
        # Check if conversation flow system says we should stay engaged
        if self.conversation_flow.should_stay_engaged(user_text):
            print(f"🗣️ Staying engaged - conversation state: {self.conversation_flow.conversation_context.current_state.value}")
            return True
        
        # Check for wake word as fallback
        wake_words = ["penny", "hey penny", "ok penny"]
        user_lower = user_text.lower()
        return any(wake_word in user_lower for wake_word in wake_words)
    
    def extract_command_from_input(self, user_text: str) -> str:
        """Extract the actual command from user input, removing wake words if present."""
        wake_words = ["hey penny", "ok penny", "penny"]
        user_lower = user_text.lower()
        
        # If no wake word and we're in conversation, use the whole input
        if self.conversation_flow.conversation_context.current_state != ConversationState.IDLE:
            return user_text
        
        # Remove wake word if present
        for wake_word in wake_words:
            if wake_word in user_lower:
                # Find and remove the wake word
                start_pos = user_lower.find(wake_word)
                end_pos = start_pos + len(wake_word)
                command = user_text[:start_pos] + user_text[end_pos:]
                return command.strip()
        
        return user_text
    
    def think(self, user_text: str) -> str:
        """Enhanced think method with full conversational flow integration."""
        if self.state != State.THINKING:
            return ""
        
        # Extract actual command (remove wake word if present)
        actual_command = self.extract_command_from_input(user_text)
        
        # Get enhanced memory context (includes emotional intelligence)
        memory_context = self.memory.get_enhanced_context_for_llm()
        
        # Enhanced prompt with memory context
        if memory_context:
            enhanced_prompt = f"{memory_context}\n\nUser: {actual_command}"
        else:
            enhanced_prompt = actual_command
        
        tone = self._route_tone(actual_command)
        self.telemetry.log_event("thinking_start", {
            "tone": tone,
            "has_memory_context": bool(memory_context),
            "context_length": len(memory_context) if memory_context else 0,
            "conversation_state": self.conversation_flow.conversation_context.current_state.value,
            "engagement_level": self.conversation_flow.conversation_context.engagement_level
        })
        
        # Generate response with memory context
        start_time = time.time()
        try:
            if hasattr(self.llm, 'complete'):
                reply_raw = self.llm.complete(enhanced_prompt, tone=tone)
            else:
                reply_raw = self.llm.generate(enhanced_prompt)
        except Exception as e:
            self.telemetry.log_event("llm_error", {"error": str(e)})
            reply_raw = f"I had trouble processing that. Could you try rephrasing?"
        
        response_time_ms = (time.time() - start_time) * 1000
        
        # Apply personality with emotional memory integration
        try:
            personality_enhanced_reply = self.personality_integration.generate_contextual_response(
                reply_raw, actual_command
            )
            print(f"🎭 Applied Penny personality mode: {self.personality_integration.personality_system.current_mode.value}")
        except Exception as e:
            print(f"⚠️ Personality integration failed, using fallback: {e}")
            try:
                from core.personality import apply as apply_personality
                personality_enhanced_reply = apply_personality(reply_raw, self.cfg.get("personality", {}))
            except Exception:
                personality_enhanced_reply = f"[{tone}] {reply_raw}" if reply_raw else "Say that again?"

        topic_category = self.personality_integration._categorize_topic(actual_command, {})
        relationship_state = self.conversation_flow.conversation_context.current_state.value
        cultural_result: Optional[CulturalEnhancementResult] = None
        response_for_flow = personality_enhanced_reply

        personality_mode = getattr(self.personality_integration.personality_system.current_mode, "value", "balanced")
        sass_level_setting = getattr(
            getattr(self.personality_integration.personality_system, "current_mode", None),
            "sass_level",
            "medium"
        )
        personality_baseline = {
            "keywords": list(getattr(self.personality_integration.personality_system, "signature_expressions", [])) or [personality_mode]
        }

        metadata_for_culture = {
            "topic": topic_category,
            "relationship": relationship_state,
            "sass_level": sass_level_setting,
            "personality_mode": personality_mode,
            "session_id": self.session_id,
            "personality_baseline": personality_baseline,
        }

        if self.cultural_adapter:
            try:
                cultural_result = self.cultural_adapter.enhance_response(
                    user_input=actual_command,
                    conversation_history=self.cultural_history,
                    base_response=personality_enhanced_reply,
                    metadata=metadata_for_culture
                )
                response_for_flow = cultural_result.response
            except Exception as e:
                print(f"⚠️ Cultural intelligence enhancement failed: {e}")

        # Apply conversational flow enhancements
        try:
            # Enhance with conversational flow elements
            final_reply = self.conversation_flow.enhance_response_with_flow(
                response_for_flow, 
                actual_command, 
                topic_category
            )
            
            # Update conversation state
            self.conversation_flow.update_conversation_state(
                actual_command, 
                final_reply, 
                topic_category
            )
            
            # Build relationship insights
            self.conversation_flow.build_relationship_insights(actual_command, final_reply)
            
            print(f"🗣️ Conversation state: {self.conversation_flow.conversation_context.current_state.value}")
            print(f"📊 Engagement level: {self.conversation_flow.conversation_context.engagement_level:.2f}")
            
        except Exception as e:
            print(f"⚠️ Conversational flow failed, using personality response: {e}")
            final_reply = response_for_flow

        # Store in memory with emotional processing
        try:
            # Add conversation turn to base memory
            turn = self.memory.base_memory.add_conversation_turn(
                user_input=actual_command,
                assistant_response=final_reply,
                context={
                    "tone": tone,
                    "response_time_ms": response_time_ms,
                    "timestamp": time.time(),
                    "conversation_state": self.conversation_flow.conversation_context.current_state.value,
                    "engagement_level": self.conversation_flow.conversation_context.engagement_level
                },
                response_time_ms=response_time_ms
            )
            
            # Process through emotional intelligence system
            self.memory.process_conversation_turn(actual_command, final_reply, turn.turn_id)
            
        except Exception as e:
            print(f"Warning: Failed to save to memory: {e}")

        new_turn = {
            "user": actual_command,
            "assistant": final_reply
        }
        self.cultural_history.append(new_turn)
        if len(self.cultural_history) > 12:
            self.cultural_history = self.cultural_history[-12:]

        if self.telemetry_client and cultural_result and cultural_result.decision == "disabled":
            decision_context = {
                "topic": topic_category,
                "relationship": relationship_state,
                "session_id": self.session_id,
            }
            self.telemetry_client.log_cultural_decision(
                "disabled",
                decision_context,
                cultural_result.metrics,
            )
            flow_metrics = self.telemetry_client.measure_conversation_flow(
                self.cultural_history,
                {"session_id": self.session_id, "decision": "disabled"}
            )
            engagement_payload = {
                "turn_count": len(self.cultural_history),
                "cultural_decision": "disabled",
                "response_appropriateness": flow_metrics.get("response_appropriateness"),
                "conversation_stability": flow_metrics.get("conversation_stability"),
            }
            self.telemetry_client.track_engagement_metrics(self.session_id, engagement_payload)
            self.telemetry_client.assess_personality_consistency(
                [personality_enhanced_reply, final_reply],
                personality_baseline,
            )

        if self.ab_testing and self.telemetry_client and self.cultural_adapter:
            ab_metrics = {
                "response_appropriateness": cultural_result.metrics.get("enhanced_authenticity_score", 0.0) if cultural_result else 0.0,
                "engagement_improvement": cultural_result.metrics.get("improvement", 0.0) if cultural_result else 0.0,
                "used_cultural": bool(cultural_result and cultural_result.used_cultural_enhancement),
                "turn_count": len(self.cultural_history),
            }
            try:
                self.telemetry_client.run(
                    self.ab_testing.collect_session_metrics(
                        self.session_id,
                        self.cultural_enabled,
                        ab_metrics
                    )
                )
            except Exception as exc:
                print(f"⚠️ Failed to record A/B metrics: {exc}")

        self.telemetry.log_event("thinking_complete", {
            "reply_length": len(final_reply),
            "response_time_ms": response_time_ms,
            "saved_to_memory": True,
            "conversation_state": self.conversation_flow.conversation_context.current_state.value,
            "personality_mode": self.personality_integration.personality_system.current_mode.value,
            "cultural_enhancement": cultural_result.metrics if cultural_result else None
        })

        self.state = State.SPEAKING
        return final_reply
    
    def get_comprehensive_stats(self) -> Dict[str, Any]:
        """Get comprehensive statistics including all system layers."""
        base_stats = self.memory.base_memory.get_memory_stats()
        emotional_insights = self.memory.get_emotional_insights()
        personality_insights = self.personality_integration.get_personality_insights()
        conversation_insights = self.conversation_flow.get_conversation_insights()
        
        return {
            # Base memory stats
            **base_stats,
            
            # Emotional intelligence stats
            'family_members_known': len(self.memory.family_members),
            'value_alignments': len(self.memory.value_alignments),
            'learning_goals': len(self.memory.learning_goals),
            'recent_emotions': list(emotional_insights.get('emotional_patterns', {}).keys())[:3],
            
            # Personality stats
            'current_personality_mode': personality_insights.get('current_mode', 'unknown'),
            'personality_adaptations': len(personality_insights.get('recent_modes_used', [])),
            
            # Conversation flow stats
            'conversation_state': conversation_insights['conversation_state'],
            'engagement_level': conversation_insights['engagement_level'],
            'conversation_depth': conversation_insights['conversation_depth'],
            'current_topics': conversation_insights['current_topics'],
            'session_duration_minutes': conversation_insights['session_duration'] / 60,
            'deep_relationships': conversation_insights['deep_relationships'],
            
            # Integration health
            'systems_active': {
                'emotional_memory': True,
                'personality_integration': True,
                'conversational_flow': True
            }
        }


def main():
    """Test the enhanced conversation pipeline."""
    print("🚀 Testing Enhanced Conversation Pipeline")
    print("=" * 50)
    
    # Create enhanced pipeline
    pipeline = EnhancedConversationPipeline()
    
    # Test conversation flow scenarios
    test_scenarios = [
        # Initial engagement
        "Hey Penny, I'm working on a new AI project and need some advice",
        
        # Follow-up without wake word (should stay engaged)
        "It's about natural language processing",
        
        # Continue conversation
        "I'm having trouble with the training data",
        
        # Personal sharing (should increase engagement)
        "My mom thinks I spend too much time on computers, but I really love this stuff",
        
        # Technical follow-up
        "Do you have any suggestions for data preprocessing?",
        
        # Change topic
        "Actually, let me ask you something else - how do you handle stress?",
    ]
    
    print(f"\n🗣️ Testing {len(test_scenarios)} conversation scenarios...")
    
    for i, user_input in enumerate(test_scenarios, 1):
        print(f"\n--- Turn {i} ---")
        print(f"User: {user_input}")
        
        # Simulate processing
        should_respond = pipeline.should_process_without_wake_word(user_input)
        if should_respond:
            print("✅ Would process (engaged or wake word detected)")
            
            # Simulate conversation state updates
            actual_command = pipeline.extract_command_from_input(user_input)
            print(f"📝 Extracted command: {actual_command}")
            
            # Show conversation insights
            insights = pipeline.conversation_flow.get_conversation_insights()
            print(f"📊 State: {insights['conversation_state']}, Engagement: {insights['engagement_level']:.2f}")
        else:
            print("🔇 Would not process (wake word required)")
        
        # Update engagement for simulation
        if should_respond:
            pipeline.conversation_flow.conversation_context.engagement_level = min(1.0, 
                pipeline.conversation_flow.conversation_context.engagement_level + 0.2)
            pipeline.conversation_flow.conversation_context.last_interaction_time = time.time()
        
        time.sleep(0.1)
    
    print(f"\n🎉 Enhanced Conversation Pipeline Test Complete!")


if __name__ == "__main__":
    main()
