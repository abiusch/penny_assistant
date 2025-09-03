#!/usr/bin/env python3
"""
Memory-Enhanced Pipeline Integration
Connects the memory system to PennyGPT's main pipeline
"""

import sys
import os
import time
from typing import Optional, Dict, Any

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
sys.path.insert(0, os.path.dirname(__file__))

from src.core.pipeline import PipelineLoop, State
from memory_system import MemoryManager
from emotional_memory_system import create_enhanced_memory_system

# Health monitor with safe fallback
class NullHealthMonitor:
    """Null object pattern for health monitor when unavailable."""
    async def check_all_components(self):
        return {
            "status": "health_monitor_disabled",
            "message": "Health monitoring temporarily disabled"
        }


class MemoryEnhancedPipeline(PipelineLoop):
    """Enhanced pipeline with conversation memory and context awareness."""
    
    def __init__(self):
        super().__init__()
        
        # Initialize base memory manager
        base_memory = MemoryManager()
        
        # Enhance with emotional intelligence
        self.memory = create_enhanced_memory_system(base_memory)
        
        # Initialize health monitor with safe fallback
        try:
            from health_monitor import PennyGPTHealthMonitor
            self.health_monitor = PennyGPTHealthMonitor()
            print("🏥 Health monitor initialized")
        except Exception as e:
            self.health_monitor = NullHealthMonitor()
            print(f"⚠️ Health monitor disabled: {e}")
        
        print("🧠 Memory-enhanced pipeline with emotional intelligence initialized")
    
    def think(self, user_text: str) -> str:
        """Enhanced think method with memory integration."""
        if self.state != State.THINKING:
            return ""
        
        # Get enhanced memory context (includes emotional intelligence)
        memory_context = self.memory.get_enhanced_context_for_llm()
        
        # Enhanced prompt with memory context
        if memory_context:
            enhanced_prompt = f"{memory_context}\n\nUser: {user_text}"
        else:
            enhanced_prompt = user_text
        
        tone = self._route_tone(user_text)
        self.telemetry.log_event("thinking_start", {
            "tone": tone,
            "has_memory_context": bool(memory_context),
            "context_length": len(memory_context) if memory_context else 0
        })
        
        # Personality layer
        try:
            from core.personality import apply as apply_personality
        except Exception:
            def apply_personality(txt, cfg): 
                return f"[{tone}] {txt}" if txt else "Say that again?"
        
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
        
        # Apply personality
        reply = apply_personality(reply_raw, self.cfg.get("personality", {}))
        
        # Store in memory with emotional processing
        try:
            # Add conversation turn to base memory
            turn = self.memory.base_memory.add_conversation_turn(
                user_input=user_text,
                assistant_response=reply,
                context={
                    "tone": tone,
                    "response_time_ms": response_time_ms,
                    "timestamp": time.time()
                },
                response_time_ms=response_time_ms
            )
            
            # Process through emotional intelligence system
            self.memory.process_conversation_turn(user_text, reply, turn.turn_id)
            
        except Exception as e:
            print(f"Warning: Failed to save to memory: {e}")
        
        self.telemetry.log_event("thinking_complete", {
            "reply_length": len(reply),
            "response_time_ms": response_time_ms,
            "saved_to_memory": True
        })
        
        self.state = State.SPEAKING
        return reply
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """Get comprehensive memory statistics including emotional data."""
        base_stats = self.memory.base_memory.get_memory_stats()
        emotional_insights = self.get_emotional_insights()
        
        # Combine stats
        enhanced_stats = {
            **base_stats,
            'family_members_known': len(self.memory.family_members),
            'value_alignments': len(self.memory.value_alignments),
            'learning_goals': len(self.memory.learning_goals),
            'recent_emotions': list(emotional_insights.get('emotional_patterns', {}).keys())[:3],
            'primary_relationships': len([
                m for m in self.memory.family_members.values() 
                if m.mention_count > 2
            ])
        }
        
        return enhanced_stats
    
    def search_memory(self, query: str, limit: int = 5):
        """Search conversation history."""
        return self.memory.base_memory.search_conversations(query, limit)
    
    def start_new_session(self) -> str:
        """Start a new conversation session."""
        return self.memory.base_memory.start_new_session()
    
    def get_user_preferences(self) -> Dict[str, Any]:
        """Get learned user preferences."""
        preferences = {}
        for key, pref in self.memory.base_memory.user_preferences.items():
            if pref.confidence > 0.3:  # Only confident preferences
                preferences[key] = {
                    'value': pref.value,
                    'confidence': pref.confidence,
                    'frequency': pref.frequency
                }
        return preferences
    
    def get_emotional_insights(self) -> Dict[str, Any]:
        """Get emotional intelligence insights about the user."""
        return self.memory.get_emotional_insights()
    
    def get_family_context(self) -> Dict[str, Any]:
        """Get family and relationship context for personality responses."""
        context = {
            'known_people': {},
            'recent_mentions': [],
            'emotional_associations': {}
        }
        
        # Get recently mentioned people
        recent_cutoff = time.time() - (7 * 24 * 60 * 60)  # Last week
        for name, member in self.memory.family_members.items():
            if member.last_mentioned > recent_cutoff:
                context['recent_mentions'].append({
                    'name': name,
                    'relationship': member.relationship_type.value,
                    'primary_emotion': max(member.emotional_associations.items(), 
                                         key=lambda x: x[1])[0] if member.emotional_associations else 'neutral'
                })
            
            context['known_people'][name] = {
                'type': member.relationship_type.value,
                'mentions': member.mention_count
            }
        
        return context


def main():
    """Test the memory-enhanced pipeline."""
    print("🧠 Testing Memory-Enhanced Pipeline")
    print("=" * 40)
    
    # Create enhanced pipeline
    pipeline = MemoryEnhancedPipeline()
    
    # Simulate some interactions
    test_conversations = [
        "Hello! My name is Alex and I love technology",
        "Can you help me understand artificial intelligence?", 
        "That's really helpful, thanks! I'm particularly interested in machine learning",
        "What's the weather like today?",
        "Thanks! You're very helpful. I prefer brief responses by the way"
    ]
    
    for i, user_input in enumerate(test_conversations, 1):
        print(f"\n--- Turn {i} ---")
        print(f"User: {user_input}")
        
        # Simulate pipeline flow
        if pipeline.start_listening():
            # Simulate STT
            pipeline.state = State.THINKING
            
            # Generate response with memory
            response = pipeline.think(user_input)
            print(f"Assistant: {response}")
            
            # Return to idle
            pipeline.state = State.IDLE
    
    # Show memory stats
    print("\n📊 Memory Statistics:")
    stats = pipeline.get_memory_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    # Show learned preferences
    print("\n👤 Learned User Preferences:")
    preferences = pipeline.get_user_preferences()
    for key, pref in preferences.items():
        print(f"  {key}: {pref['value']} (confidence: {pref['confidence']:.2f})")
    
    # Test memory search
    print("\n🔍 Memory Search for 'technology':")
    results = pipeline.search_memory("technology")
    for result in results:
        print(f"  User: {result.user_input[:50]}...")
        print(f"  Assistant: {result.assistant_response[:50]}...")


if __name__ == "__main__":
    import time
    main()
