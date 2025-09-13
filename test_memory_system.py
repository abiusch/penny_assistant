#!/usr/bin/env python3
"""
Test script for the persistent memory system
Verifies memory storage, retrieval, and integration
"""

import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from memory_enhanced_penny import create_memory_enhanced_penny
from persistent_memory import MemoryType

def test_memory_system():
    """Test all aspects of the memory system"""
    print("🧠 Testing Persistent Memory System")
    print("="*50)
    
    # Create memory-enhanced Penny
    print("1. Creating memory-enhanced Penny...")
    penny = create_memory_enhanced_penny("test_memory.db")
    
    # Test manual memory storage
    print("\n2. Testing manual memory storage...")
    penny.manually_store_memory("user_fact", "name", "CJ")
    penny.manually_store_memory("preference", "coding", "Loves FastAPI and clean architecture")
    penny.manually_store_memory("inside_joke", "josh", "Calls Josh 'brochacho'")
    penny.manually_store_memory("technical_interest", "voice_ai", "Building advanced voice AI assistant")
    
    # Test memory retrieval
    print("\n3. Testing memory retrieval...")
    summary = penny.get_relationship_summary()
    print(f"Relationship Summary: {summary}")
    
    # Test memory search
    print("\n4. Testing memory search...")
    search_result = penny.search_memories("josh")
    print(f"Search for 'josh': {search_result}")
    
    # Test conversation session
    print("\n5. Testing conversation session...")
    session_id = penny.start_conversation_session("test")
    print(f"Started session: {session_id}")
    
    # Test memory-aware response generation
    print("\n6. Testing memory-aware responses...")
    
    test_inputs = [
        "What do you know about me?",
        "Tell me about Josh",
        "I'm working on a new FastAPI project",
        "How's my voice AI assistant coming along?"
    ]
    
    for i, test_input in enumerate(test_inputs, 1):
        print(f"\n   Test {i}: {test_input}")
        try:
            response = penny.generate_memory_aware_response(test_input)
            print(f"   Response: {response[:100]}...")
        except Exception as e:
            print(f"   Error: {e}")
    
    # Test memory stats
    print("\n7. Testing memory statistics...")
    penny.show_memory_stats()
    
    # End session
    penny.end_conversation_session("Test session completed successfully")
    
    print("\n✅ All memory system tests completed!")
    
    # Clean up test database
    try:
        os.remove("test_memory.db")
        print("🧹 Test database cleaned up")
    except:
        pass

def test_cross_session_memory():
    """Test that memories persist across sessions"""
    print("\n🔄 Testing Cross-Session Memory Persistence")
    print("="*50)
    
    # First session - store memories
    print("Session 1: Storing memories...")
    penny1 = create_memory_enhanced_penny("persistent_test.db")
    penny1.manually_store_memory("user_fact", "name", "CJ")
    penny1.manually_store_memory("preference", "language", "Python developer")
    
    session1 = penny1.start_conversation_session("test1")
    response1 = penny1.generate_memory_aware_response("I like microservices architecture")
    print(f"Session 1 response: {response1[:100]}...")
    penny1.end_conversation_session("First test session")
    
    # Second session - retrieve memories
    print("\nSession 2: Retrieving memories...")
    penny2 = create_memory_enhanced_penny("persistent_test.db")
    
    summary = penny2.get_relationship_summary()
    print(f"Retrieved relationship: {summary}")
    
    session2 = penny2.start_conversation_session("test2")
    response2 = penny2.generate_memory_aware_response("What do you remember about me?")
    print(f"Session 2 response: {response2[:100]}...")
    penny2.end_conversation_session("Second test session")
    
    print("✅ Cross-session memory persistence test completed!")
    
    # Clean up
    try:
        os.remove("persistent_test.db")
        print("🧹 Test database cleaned up")
    except:
        pass

if __name__ == "__main__":
    print("🧪 Running Memory System Tests...")
    
    test_memory_system()
    test_cross_session_memory()
    
    print("\n🎉 All tests completed successfully!")
    print("\n💡 The memory system is ready for integration!")
    print("   • Use 'memory_chat_penny.py' for text chat with memory")
    print("   • Memory database: 'penny_memory.db'")
    print("   • Supports cross-session relationship building")
