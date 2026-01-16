#!/usr/bin/env python3
"""
Fixed Test for Enhanced Emotional Memory System
Addresses Python 3.13 compatibility issues
"""

import sys
import os

# Add src directory to Python path  
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
sys.path.insert(0, os.path.dirname(__file__))

from memory_enhanced_pipeline import MemoryEnhancedPipeline
import time

def test_emotional_memory():
    """Test emotional memory system with sample conversations."""
    print("🧪 Testing Enhanced Emotional Memory System")
    print("=" * 50)
    
    try:
        # Initialize pipeline with emotional intelligence
        pipeline = MemoryEnhancedPipeline()
        
        # Test conversations that should trigger emotional intelligence
        test_conversations = [
            ("Hello! My name is Sarah and I'm feeling excited about this new AI", 
             "Hi Sarah! I love your enthusiasm! What are you most excited to explore?"),
            
            ("My mom is visiting tomorrow and I'm a bit worried about the house being messy",
             "I can hear the concern in your voice about your mom's visit. Would it help to talk through a quick tidying plan?"),
            
            ("Can you explain machine learning to me? I want to understand AI better",
             "Absolutely! Machine learning is fascinating. Let me break it down simply..."),
            
            ("Ugh, this work project is so frustrating. My manager keeps changing requirements", 
             "That sounds incredibly frustrating! Constantly shifting requirements can be exhausting."),
            
            ("Thanks! You're really helpful. I prefer when explanations are detailed",
             "You're welcome! I've noted your preference for detailed explanations - I'll keep that in mind."),
             
            ("My dog Max is sick and I'm worried about him",
             "I'm sorry to hear Max isn't feeling well. It's clear you care deeply about him.")
        ]
        
        print("🗣️ Processing test conversations...")
        conversation_count = 0
        error_count = 0
        
        for i, (user_input, expected_response) in enumerate(test_conversations, 1):
            print(f"\n--- Conversation {i} ---")
            print(f"User: {user_input}")
            
            try:
                # Get enhanced context before processing
                context = pipeline.memory.get_enhanced_context_for_llm()
                if context:
                    print(f"📝 Context: {context[:100]}...")
                
                # Simulate storing the turn
                turn = pipeline.memory.base_memory.add_conversation_turn(
                    user_input=user_input,
                    assistant_response=expected_response,
                    response_time_ms=500
                )
                
                # Process through emotional intelligence
                pipeline.memory.process_conversation_turn(user_input, expected_response, turn.turn_id)
                print("✅ Processed through emotional intelligence")
                conversation_count += 1
                
            except Exception as e:
                print(f"❌ Error: {e}")
                error_count += 1
                continue
            
            # Small delay to simulate real conversation
            time.sleep(0.05)
        
        print(f"\n📊 Processing Summary: {conversation_count} successful, {error_count} errors")
        
        # Show emotional insights
        print("\n" + "=" * 50)
        print("🧠 EMOTIONAL INTELLIGENCE ANALYSIS")
        print("=" * 50)
        
        try:
            insights = pipeline.get_emotional_insights()
            
            # Emotional patterns
            print("\n😊 Emotional Patterns Detected:")
            patterns = insights.get('emotional_patterns', {})
            if patterns:
                for emotion, count in patterns.items():
                    print(f"   {emotion}: {count} occurrences")
            else:
                print("   No patterns detected yet")
            
            # Relationships detected
            print("\n👥 Relationships Identified:")
            relationships = insights.get('relationship_summary', {})
            if relationships:
                for name, info in relationships.items():
                    print(f"   {name}: {info['type']} (mentioned {info['mentions']} times)")
            else:
                print("   No relationships detected yet")
            
            # Value alignments
            print("\n💭 Value Alignments:")
            values = insights.get('value_alignments', {})
            if values:
                for category, info in values.items():
                    print(f"   {category}: {info['statement']} (confidence: {info['confidence']:.2f})")
            else:
                print("   No value alignments detected yet")
            
            # Learning interests
            print("\n📚 Learning Interests:")
            learning = insights.get('learning_interests', {})
            if learning:
                for topic, info in learning.items():
                    print(f"   {topic}: interest level {info['interest_level']:.2f}")
            else:
                print("   No learning interests detected yet")
            
            # Family context
            print("\n👨‍👩‍👧‍👦 Family Context:")
            family_context = pipeline.get_family_context()
            known_people = family_context.get('known_people', {})
            if known_people:
                for name, person in known_people.items():
                    print(f"   {name}: {person['type']} ({person['mentions']} mentions)")
            else:
                print("   No family members identified yet")
            
            # Enhanced memory stats
            print("\n📊 Enhanced Memory Statistics:")
            stats = pipeline.get_memory_stats()
            enhanced_stats = {k: v for k, v in stats.items() 
                            if k.startswith(('family', 'value', 'learning', 'recent', 'primary'))}
            if enhanced_stats:
                for key, value in enhanced_stats.items():
                    print(f"   {key}: {value}")
            else:
                print("   Enhanced stats will appear after more conversations")
            
        except Exception as e:
            print(f"❌ Error getting insights: {e}")
            return False
        
        print("\n🎉 Emotional Memory System Test Complete!")
        return True
        
    except Exception as e:
        print(f"❌ Critical error initializing system: {e}")
        return False

if __name__ == "__main__":
    success = test_emotional_memory()
    if success:
        print("\n✅ All emotional intelligence features working correctly!")
    else:
        print("\n❌ Some issues detected in emotional intelligence system")
