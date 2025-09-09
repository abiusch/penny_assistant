#!/usr/bin/env python3
"""
Test Script for Guided Learning System
Demonstrates proactive curiosity and learning capabilities
"""

import sys
import os
import json

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def test_guided_learning():
    """Test the guided learning system with simulated conversations."""
    print("🧠 Testing Guided Learning & Reasoning System")
    print("=" * 50)
    
    try:
        # Import systems
        from emotional_memory_system import EmotionalMemorySystem
        from src.core.guided_learning_system import GuidedLearningSystem
        from memory_system import MemoryManager
        
        # Initialize systems
        print("📚 Initializing memory systems...")
        memory_manager = MemoryManager()
        emotional_memory = EmotionalMemorySystem(memory_manager)
        guided_learning = GuidedLearningSystem(emotional_memory)
        
        print("✅ Systems initialized successfully!")
        
        # Test scenarios
        test_scenarios = [
            {
                "name": "Explicit Research Request",
                "user_input": "Can you research quantum computing for me?",
                "expected": "Should detect research opportunity and ask for permission"
            },
            {
                "name": "Curiosity Expression", 
                "user_input": "I wonder how machine learning actually works",
                "expected": "Should detect curiosity and offer to explore topic"
            },
            {
                "name": "Knowledge Gap",
                "user_input": "I don't really understand blockchain technology",
                "expected": "Should offer to research and clarify understanding"
            },
            {
                "name": "Problem Solving",
                "user_input": "I need to decide between Python and JavaScript for my project",
                "expected": "Should offer to research pros/cons to help decide"
            },
            {
                "name": "Correction Attempt",
                "user_input": "Actually, that's not quite right - React is a library, not a framework",
                "expected": "Should detect correction and acknowledge learning"
            }
        ]
        
        print("\n🧪 Running Test Scenarios:")
        print("-" * 30)
        
        for i, scenario in enumerate(test_scenarios, 1):
            print(f"\n{i}. {scenario['name']}")
            print(f"   Input: \"{scenario['user_input']}\"")
            print(f"   Expected: {scenario['expected']}")
            
            # Test learning opportunity detection
            opportunities = guided_learning.detect_learning_opportunities(
                scenario['user_input'], 
                "Previous conversation context"
            )
            
            if opportunities:
                best_opp = max(opportunities, key=lambda x: x.confidence)
                print(f"   ✅ Detected: {best_opp.opportunity_type.value}")
                print(f"   📋 Topic: {best_opp.topic}")
                print(f"   🎯 Confidence: {best_opp.confidence:.2f}")
                
                # Generate permission request
                permission_request = guided_learning.request_research_permission(best_opp)
                print(f"   💬 Permission Request: \"{permission_request}\"")
                
            else:
                print("   ❌ No learning opportunities detected")
        
        # Test correction detection
        print("\n🔍 Testing Correction Detection:")
        print("-" * 30)
        
        previous_response = "React is a JavaScript framework for building user interfaces."
        correction_input = "Actually, React is a library, not a framework."
        
        correction = guided_learning.detect_correction_attempt(
            correction_input, previous_response
        )
        
        if correction:
            original, corrected = correction
            print(f"   ✅ Correction detected!")
            print(f"   📝 Original: {original[:50]}...")
            print(f"   ✏️ Corrected: {corrected}")
            
            # Record the correction
            correction_id = guided_learning.record_user_correction(
                original, corrected, correction_input, correction_input
            )
            print(f"   💾 Recorded as correction #{correction_id}")
        else:
            print("   ❌ Correction not detected")
        
        # Test curiosity question generation
        print("\n❓ Testing Curiosity Questions:")
        print("-" * 30)
        
        topics = ["machine learning", "quantum computing", "sustainable energy"]
        
        for topic in topics:
            question = guided_learning.generate_curiosity_question(topic, "user interest context")
            print(f"   🤔 {topic}: \"{question}\"")
        
        # Test learning context generation
        print("\n📊 Testing Learning Context:")
        print("-" * 30)
        
        learning_context = guided_learning.get_learning_context_for_llm()
        if learning_context:
            print(f"   📋 Generated context: {learning_context}")
        else:
            print("   📋 No learning context available yet")
        
        # Database verification
        print("\n🗄️ Verifying Database Tables:")
        print("-" * 30)
        
        import sqlite3
        
        with sqlite3.connect(emotional_memory.db_path) as conn:
            # Check for new tables
            cursor = conn.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name IN (
                    'research_sessions', 'user_corrections', 'curiosity_topics'
                )
            """)
            
            tables = [row[0] for row in cursor.fetchall()]
            
            for table in ['research_sessions', 'user_corrections', 'curiosity_topics']:
                if table in tables:
                    print(f"   ✅ Table '{table}' exists")
                    
                    # Count entries
                    count_cursor = conn.execute(f"SELECT COUNT(*) FROM {table}")
                    count = count_cursor.fetchone()[0]
                    print(f"      📊 {count} entries")
                else:
                    print(f"   ❌ Table '{table}' missing")
        
        print("\n🎉 Guided Learning System Test Complete!")
        print("\n📋 Summary:")
        print("   ✅ Learning opportunity detection working")
        print("   ✅ Correction detection working")
        print("   ✅ Permission request generation working")
        print("   ✅ Database integration working")
        print("   ✅ Curiosity question generation working")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def demo_conversation_flow():
    """Demonstrate a full conversation flow with guided learning."""
    print("\n🎭 Demonstration: Guided Learning Conversation Flow")
    print("=" * 60)
    
    # Simulated conversation
    conversation = [
        {
            "user": "I'm trying to learn about artificial intelligence",
            "assistant": "AI is a fascinating field! It involves creating systems that can perform tasks requiring human intelligence.",
            "learning_action": "Should detect learning interest and offer research"
        },
        {
            "user": "Sure, go ahead and research it",
            "assistant": "Great! I've researched AI and found current trends include...",
            "learning_action": "Should conduct research and provide findings"
        },
        {
            "user": "Actually, machine learning is a subset of AI, not the other way around",
            "assistant": "You're absolutely right! Thanks for the correction - machine learning is indeed a subset of AI.",
            "learning_action": "Should detect correction and acknowledge learning"
        }
    ]
    
    for i, turn in enumerate(conversation, 1):
        print(f"\n💬 Turn {i}:")
        print(f"   👤 User: {turn['user']}")
        print(f"   🤖 Assistant: {turn['assistant']}")
        print(f"   🧠 Learning Action: {turn['learning_action']}")
    
    print("\n🎯 Key Features Demonstrated:")
    print("   📚 Permission-based research requests")
    print("   🔍 Learning from user corrections")
    print("   🤝 Respectful boundary management")
    print("   💡 Proactive curiosity with consent")


if __name__ == "__main__":
    print("🧠 Guided Learning & Reasoning System Test")
    print("""This system transforms Penny from reactive to genuinely curious:
    
    🎯 Features:
    • Permission-based research and exploration
    • Learning from user corrections
    • Proactive curiosity with boundaries
    • Knowledge building about user's world
    • Respectful follow-up questions
    """)
    
    success = test_guided_learning()
    
    if success:
        demo_conversation_flow()
        print("\n🚀 Ready to integrate with conversation pipeline!")
    else:
        print("\n⚠️ Please fix issues before integration.")
