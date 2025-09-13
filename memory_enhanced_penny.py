#!/usr/bin/env python3
"""
Memory-Enhanced Penny - Integrates persistent memory with existing personality systems
Builds on pragmatics_enhanced_penny.py to add cross-session memory capabilities
"""

import sys
import os
from typing import Dict, Any, Optional
from datetime import datetime

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from performance_monitor import time_operation, OperationType
from pragmatics_enhanced_penny import PragmaticsEnhancedPenny
from persistent_memory import PersistentMemory, MemoryEnhancedPersonality, MemoryType

class MemoryEnhancedPenny(PragmaticsEnhancedPenny):
    """Penny with persistent memory capabilities for cross-session relationship building"""
    
    def __init__(self, memory_db_path: str = "penny_memory.db"):
        # Initialize parent personality system
        super().__init__()
        
        # Add memory capabilities
        print("🧠 Initializing persistent memory system...")
        self.memory = PersistentMemory(memory_db_path)
        self.memory_personality = MemoryEnhancedPersonality(self.memory)
        self.current_session_id = 0
        
        print("✅ Memory-enhanced Penny initialized!")
    
    def start_conversation_session(self, interface_type: str = "text"):
        """Start a new conversation session with memory tracking"""
        self.current_session_id = self.memory.start_conversation_session(interface_type)
        return self.current_session_id
    
    def end_conversation_session(self, summary: str = ""):
        """End the current conversation session"""
        if self.current_session_id > 0:
            self.memory.end_conversation_session(self.current_session_id, summary)
            self.current_session_id = 0
    
    def generate_memory_aware_response(self, user_input: str, context: Dict[str, Any] = None) -> str:
        """Generate response with memory-enhanced context"""
        context = context or {}
        
        with time_operation(OperationType.TOTAL_PIPELINE, {"memory_enabled": True}):
            
            # Step 1: Enhance context with relevant memories
            with time_operation(OperationType.PERSONALITY_GENERATION, {"operation": "memory_recall"}):
                enhanced_context = self.memory_personality.enhance_context_with_memory(context)
                
                # Add memory insights to context for LLM
                if enhanced_context.get('remembered_facts'):
                    enhanced_context['memory_context'] = "What I remember about you: " + \
                        "; ".join(enhanced_context['remembered_facts'][:3])
                
                if enhanced_context.get('inside_jokes'):
                    enhanced_context['shared_jokes'] = "; ".join(enhanced_context['inside_jokes'])
            
            # Step 2: Generate response using enhanced context
            with time_operation(OperationType.LLM):
                response = self.generate_pragmatically_aware_response(user_input, enhanced_context)
            
            # Step 3: Learn from this interaction
            with time_operation(OperationType.HUMOR_DETECTION, {"operation": "memory_learning"}):
                self.memory_personality.learn_from_conversation(user_input, response, enhanced_context)
                
                # Log reaction if indicators present
                if self.current_session_id > 0:
                    reaction_indicators = self._extract_reaction_indicators(user_input)
                    if reaction_indicators:
                        self.memory.log_user_reaction(
                            self.current_session_id, user_input, response, reaction_indicators
                        )
            
            return response
    
    def _extract_reaction_indicators(self, user_input: str) -> list:
        """Extract user reaction indicators from input"""
        indicators = []
        user_lower = user_input.lower()
        
        # Positive reactions
        positive_markers = ['lol', 'haha', 'funny', 'love it', 'perfect', 'great', 
                           'awesome', 'brilliant', 'exactly', 'yes!']
        # Negative reactions  
        negative_markers = ['confused', 'what?', 'huh?', 'wrong', 'no', 'stop',
                           'don\'t understand', 'makes no sense']
        
        for marker in positive_markers + negative_markers:
            if marker in user_lower:
                indicators.append(marker)
        
        return indicators
    
    def get_relationship_summary(self) -> str:
        """Get a natural language summary of relationship memories"""
        summary = self.memory.get_relationship_summary()
        
        summary_parts = []
        
        if summary['user_facts']:
            facts = [f.value for f in summary['user_facts'][:3]]
            summary_parts.append(f"I know that {', '.join(facts)}")
        
        if summary['preferences']:
            prefs = [p.value for p in summary['preferences'][:2]]
            summary_parts.append(f"You prefer {', '.join(prefs)}")
            
        if summary['inside_jokes']:
            jokes = [j.value for j in summary['inside_jokes'][:2]]
            summary_parts.append(f"We have some inside jokes: {', '.join(jokes)}")
            
        if summary['technical_interests']:
            interests = [t.key.replace('interest_', '') for t in summary['technical_interests'][:3]]
            summary_parts.append(f"You're interested in {', '.join(interests)}")
        
        if summary_parts:
            return ". ".join(summary_parts) + "."
        else:
            return "We're still getting to know each other!"
    
    def manually_store_memory(self, memory_type: str, key: str, value: str, confidence: float = 1.0):
        """Manually store a memory (for testing/setup)"""
        try:
            # Handle common variations
            if memory_type == "technical_interest":
                memory_type = "tech_interest"
            
            mem_type = MemoryType(memory_type)
            success = self.memory.store_memory(mem_type, key, value, confidence)
            if success:
                print(f"✅ Stored memory: {key} = {value}")
            else:
                print(f"❌ Failed to store memory: {key}")
            return success
        except ValueError:
            print(f"❌ Invalid memory type: {memory_type}")
            print(f"Valid types: {[mt.value for mt in MemoryType]}")
            return False
    
    def show_memory_stats(self):
        """Display current memory statistics"""
        stats = self.memory.get_memory_stats()
        print("\n📊 Memory Statistics:")
        for memory_type, count in stats.items():
            print(f"   {memory_type}: {count} items")
        
        print(f"\n🤝 Relationship Summary:")
        print(f"   {self.get_relationship_summary()}")
    
    def search_memories(self, search_term: str, limit: int = 5) -> str:
        """Search memories and return formatted results"""
        memories = self.memory.search_memories(search_term=search_term, limit=limit)
        
        if not memories:
            return f"I don't have any memories matching '{search_term}'"
        
        results = []
        for mem in memories:
            age_days = (datetime.now() - mem.last_accessed).days
            results.append(f"• {mem.key}: {mem.value} (remembered {age_days} days ago)")
        
        return f"Here's what I remember about '{search_term}':\n" + "\n".join(results)
    
    def cleanup_old_memories(self, days_old: int = 90):
        """Clean up old, low-confidence memories"""
        self.memory.cleanup_old_memories(days_old)
    
    # Override parent methods to use memory-aware versions
    def generate_pragmatically_aware_response(self, user_input: str, context: Dict[str, Any] = None) -> str:
        """Override to use memory-aware response generation"""
        # If no session active, this is a standalone call - use memory awareness
        if self.current_session_id == 0:
            return self.generate_memory_aware_response(user_input, context)
        else:
            # Session active, use parent method but still learn
            response = super().generate_pragmatically_aware_response(user_input, context)
            # Still learn from interaction
            self.memory_personality.learn_from_conversation(user_input, response, context or {})
            return response

def create_memory_enhanced_penny(memory_db_path: str = "penny_memory.db") -> MemoryEnhancedPenny:
    """Factory function to create memory-enhanced Penny"""
    return MemoryEnhancedPenny(memory_db_path)

# Testing and example usage
if __name__ == "__main__":
    print("🧠 Testing Memory-Enhanced Penny...")
    
    # Create memory-enhanced Penny
    penny = create_memory_enhanced_penny("test_memory.db")
    
    # Start a test session
    session_id = penny.start_conversation_session("test")
    print(f"Started session: {session_id}")
    
    # Test storing some memories manually
    penny.manually_store_memory("user_fact", "name", "CJ")
    penny.manually_store_memory("preference", "coding_style", "Likes clean, fast code")
    penny.manually_store_memory("inside_joke", "josh_nickname", "Calls Josh 'brochacho'")
    penny.manually_store_memory("technical_interest", "voice_ai", "Building voice AI assistant")
    
    # Test memory-aware response
    context = {'topic': 'programming', 'emotion': 'curious'}
    response = penny.generate_memory_aware_response(
        "What do you think about my FastAPI project?", 
        context
    )
    print(f"\n🤖 Penny: {response}")
    
    # Show relationship summary
    print(f"\n🤝 Relationship: {penny.get_relationship_summary()}")
    
    # Show memory stats
    penny.show_memory_stats()
    
    # Test memory search
    search_result = penny.search_memories("josh")
    print(f"\n🔍 Search result: {search_result}")
    
    # End session
    penny.end_conversation_session("Test session completed")
    
    # Clean up test database
    os.remove("test_memory.db")
    print("\n✅ Memory-Enhanced Penny test completed!")
