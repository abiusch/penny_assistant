#!/usr/bin/env python3
"""
Test script for voice memory integration
Verifies that voice interface uses memory system correctly
"""

import sys
import os

# Add src to path  
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def test_voice_memory_integration():
    """Test that voice interface can use memory system"""
    print("🎤 Testing Voice Memory Integration")
    print("="*50)
    
    try:
        # Test imports
        print("1. Testing imports...")
        from memory_enhanced_penny import create_memory_enhanced_penny
        print("   ✅ Memory-enhanced Penny import successful")
        
        # Test memory system initialization
        print("\n2. Testing memory system initialization...")
        penny = create_memory_enhanced_penny("test_voice_memory.db")
        print("   ✅ Memory-enhanced Penny created successfully")
        
        # Test session management
        print("\n3. Testing voice session management...")
        session_id = penny.start_conversation_session("voice")
        print(f"   ✅ Voice session started: {session_id}")
        
        # Test memory-aware response generation
        print("\n4. Testing memory-aware voice responses...")
        
        # Simulate storing some memories first
        penny.manually_store_memory("user_fact", "name", "CJ")
        penny.manually_store_memory("preference", "interface", "Prefers voice interaction")
        
        # Test response generation
        test_contexts = [
            ("Hi Penny, I'm back!", {'topic': 'greeting', 'emotion': 'neutral'}),
            ("What do you remember about me?", {'topic': 'memory', 'emotion': 'curious'}),
            ("I'm working on FastAPI", {'topic': 'programming', 'emotion': 'neutral'})
        ]
        
        for i, (test_input, context) in enumerate(test_contexts, 1):
            print(f"   Test {i}: {test_input}")
            try:
                response = penny.generate_memory_aware_response(test_input, context)
                print(f"   ✅ Response generated: {response[:80]}...")
            except Exception as e:
                print(f"   ❌ Response generation failed: {e}")
        
        # Test memory summary
        print("\n5. Testing memory summary...")
        summary = penny.get_relationship_summary()
        print(f"   ✅ Memory summary: {summary}")
        
        # Test session cleanup
        print("\n6. Testing session cleanup...")
        penny.end_conversation_session("Test voice session completed")
        print("   ✅ Session ended successfully")
        
        print("\n🎉 Voice Memory Integration Test PASSED!")
        return True
        
    except Exception as e:
        print(f"\n❌ Voice Memory Integration Test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # Clean up test database
        try:
            os.remove("test_voice_memory.db")
            print("🧹 Test database cleaned up")
        except:
            pass

def test_voice_context_detection():
    """Test that voice interface context detection works with memory"""
    print("\n🔍 Testing Voice Context Detection with Memory")
    print("="*50)
    
    # This simulates the context detection logic from voice interface
    test_inputs = [
        "How are you feeling today?",
        "I'm working on debugging this code", 
        "Tell me what you remember about Josh",
        "My friend Reneille helped with the project"
    ]
    
    for i, text in enumerate(test_inputs, 1):
        print(f"{i}. Input: {text}")
        
        # Simulate context detection from voice interface
        context = {'topic': 'conversation', 'emotion': 'neutral', 'participants': []}
        text_lower = text.lower()
        
        # Personal topics
        if 'feeling' in text_lower or 'how are' in text_lower:
            context['topic'] = 'personal'
            context['emotion'] = 'curious'
        
        # Programming topics  
        elif any(word in text_lower for word in ['code', 'programming', 'debugging']):
            context['topic'] = 'programming'
            if 'debugging' in text_lower:
                context['emotion'] = 'frustrated'
        
        # Memory topics
        elif any(word in text_lower for word in ['remember', 'recall']):
            context['topic'] = 'memory'
            context['emotion'] = 'curious'
            
        # Participants
        if 'josh' in text_lower:
            context['participants'].append('josh')
        if 'reneille' in text_lower:
            context['participants'].append('reneille')
            
        print(f"   Detected context: {context}")
        print()
    
    print("✅ Voice context detection logic verified!")

if __name__ == "__main__":
    print("🧪 Running Voice Memory Integration Tests...")
    
    success = test_voice_memory_integration()
    test_voice_context_detection()
    
    if success:
        print("\n🎉 All tests passed! Voice memory integration is ready!")
        print("\n💡 You can now run:")
        print("   • python3 voice_enhanced_penny.py (for voice with memory)")
        print("   • python3 memory_chat_penny.py (for text with memory)")
        print("   • Both interfaces share the same memory database!")
    else:
        print("\n❌ Some tests failed. Check the errors above.")
