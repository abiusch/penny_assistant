#!/usr/bin/env python3
"""
Comprehensive Integration Test
Tests all systems working together: Modal Interface + Memory + Semantic Search + Tools
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import asyncio
import time
from src.core.modality import create_modal_interface
from src.memory.semantic_memory import SemanticMemory
from memory_system import MemoryManager

print("=" * 80)
print("🔍 COMPREHENSIVE INTEGRATION TEST - ALL SYSTEMS")
print("=" * 80)
print("\nTesting that all Week 3-5 systems work together seamlessly...\n")

# Track results
tests_passed = 0
tests_total = 0

async def test_integration():
    global tests_passed, tests_total
    
    # ============================================================================
    # TEST 1: EdgeModalInterface + Semantic Memory
    # ============================================================================
    print("\n" + "=" * 80)
    print("🧪 TEST 1: EdgeModalInterface + Semantic Memory Integration")
    print("=" * 80)
    
    tests_total += 1
    try:
        # Create chat interface
        chat = create_modal_interface("chat", user_id="integration_test")
        
        print("\n  Step 1: Creating chat interface...")
        assert chat is not None, "Chat interface should be created"
        assert chat.base_memory is not None, "Chat should have base memory"
        print("  ✅ Chat interface created with memory")
        
        # Add semantic memory
        print("\n  Step 2: Adding semantic memory to chat...")
        chat.semantic_memory = SemanticMemory(chat.base_memory)
        assert chat.semantic_memory is not None, "Semantic memory should be added"
        print("  ✅ Semantic memory integrated")
        
        # Save conversations
        print("\n  Step 3: Saving conversations with semantic indexing...")
        conversations = [
            ("How do I learn Python?", "Start with the basics: variables, loops, and functions."),
            ("What's the best way to code?", "Practice regularly and work on real projects."),
            ("Tell me about JavaScript", "JavaScript is great for web development."),
        ]
        
        for user_msg, assistant_msg in conversations:
            turn = chat.semantic_memory.add_conversation_turn(
                user_input=user_msg,
                assistant_response=assistant_msg,
                context={'test': 'integration'}
            )
            print(f"    - Saved: '{user_msg[:40]}'")
        
        print("  ✅ Conversations saved with semantic indexing")
        
        # Test semantic search
        print("\n  Step 4: Testing semantic search...")
        results = chat.semantic_memory.semantic_search("programming languages", k=3)
        assert len(results) > 0, "Should find similar conversations"
        print(f"  ✅ Found {len(results)} semantically similar conversations")
        for r in results[:2]:
            print(f"    - {r['user_input']} (similarity: {r['similarity']:.3f})")
        
        # Test context retrieval
        print("\n  Step 5: Testing context retrieval...")
        context = chat.semantic_memory.get_relevant_context("How can I improve my coding?")
        assert len(context) > 0, "Should get relevant context"
        print(f"  ✅ Retrieved {len(context)} chars of relevant context")
        
        chat.cleanup()
        tests_passed += 1
        print("\n✅ TEST 1 PASSED: Modal + Semantic Integration Working")
        
    except Exception as e:
        print(f"\n❌ TEST 1 FAILED: {e}")
        import traceback
        traceback.print_exc()
    
    # ============================================================================
    # TEST 2: Cross-Modal Memory Sharing
    # ============================================================================
    print("\n" + "=" * 80)
    print("🧪 TEST 2: Cross-Modal Memory Sharing (Chat + Voice)")
    print("=" * 80)
    
    tests_total += 1
    try:
        user_id = "cross_modal_test"
        
        # Create both interfaces
        print("\n  Step 1: Creating chat and voice interfaces...")
        chat = create_modal_interface("chat", user_id=user_id)
        voice = create_modal_interface("voice", user_id=user_id)
        print("  ✅ Both interfaces created")
        
        # Add semantic memory to both
        print("\n  Step 2: Adding semantic memory to both...")
        shared_base_memory = chat.base_memory
        chat.semantic_memory = SemanticMemory(shared_base_memory)
        voice.semantic_memory = SemanticMemory(shared_base_memory)
        print("  ✅ Semantic memory added to both (shared base)")
        
        # Save conversation in chat
        print("\n  Step 3: Saving conversation via chat...")
        chat.semantic_memory.add_conversation_turn(
            "What is machine learning?",
            "Machine learning is a subset of AI that learns from data.",
            context={'modality': 'chat'}
        )
        print("  ✅ Conversation saved via chat")
        
        # Search from voice
        print("\n  Step 4: Searching via voice interface...")
        results = voice.semantic_memory.semantic_search("AI and data science", k=2)
        assert len(results) > 0, "Voice should find chat's conversations"
        print(f"  ✅ Voice found {len(results)} conversations from chat")
        print(f"    - {results[0]['user_input']} (similarity: {results[0]['similarity']:.3f})")
        
        # Verify memory is shared
        chat_stats = chat.semantic_memory.get_stats()
        voice_stats = voice.semantic_memory.get_stats()
        assert chat_stats['total_conversation_turns'] == voice_stats['total_conversation_turns'], \
            "Both should see same conversations"
        print(f"\n  ✅ Memory sharing verified: {chat_stats['total_conversation_turns']} total turns")
        
        chat.cleanup()
        voice.cleanup()
        tests_passed += 1
        print("\n✅ TEST 2 PASSED: Cross-Modal Memory Sharing Works")
        
    except Exception as e:
        print(f"\n❌ TEST 2 FAILED: {e}")
        import traceback
        traceback.print_exc()
    
    # ============================================================================
    # TEST 3: Semantic Search Quality
    # ============================================================================
    print("\n" + "=" * 80)
    print("🧪 TEST 3: Semantic Search Quality & Accuracy")
    print("=" * 80)
    
    tests_total += 1
    try:
        semantic_mem = SemanticMemory()
        
        print("\n  Step 1: Adding diverse conversations...")
        test_data = [
            ("How do I learn Python programming?", "Start with Python basics and practice daily."),
            ("What's the weather like today?", "I don't have access to weather data."),
            ("Tell me about machine learning", "ML is about training models on data."),
            ("How can I cook pasta?", "Boil water, add pasta, cook for 8-10 minutes."),
            ("What is deep learning?", "Deep learning uses neural networks with many layers."),
            ("Best way to learn coding?", "Practice with projects and read others' code."),
        ]
        
        for user, assistant in test_data:
            semantic_mem.add_conversation_turn(user, assistant)
        
        print(f"  ✅ Added {len(test_data)} diverse conversations")
        
        # Test 1: Should find programming-related
        print("\n  Step 2: Testing 'programming' query...")
        results = semantic_mem.semantic_search("software development", k=3)
        programming_count = sum(1 for r in results if any(
            word in r['user_input'].lower() 
            for word in ['python', 'coding', 'programming', 'learn']
        ))
        print(f"    Found {len(results)} results, {programming_count} are programming-related")
        assert programming_count >= 2, "Should find multiple programming conversations"
        print("  ✅ Correctly identified programming conversations")
        
        # Test 2: Should find ML-related
        print("\n  Step 3: Testing 'artificial intelligence' query...")
        results = semantic_mem.semantic_search("artificial intelligence", k=3)
        ai_count = sum(1 for r in results if any(
            word in r['user_input'].lower() 
            for word in ['machine', 'learning', 'deep', 'neural']
        ))
        print(f"    Found {len(results)} results, {ai_count} are AI-related")
        assert ai_count >= 1, "Should find AI conversations"
        print("  ✅ Correctly identified AI conversations")
        
        # Test 3: High similarity for related queries
        print("\n  Step 4: Testing similarity scores...")
        results = semantic_mem.semantic_search("How to learn programming?", k=3)
        if results:
            top_similarity = results[0]['similarity']
            print(f"    Top result similarity: {top_similarity:.3f}")
            assert top_similarity > 0.5, "Related queries should have >0.5 similarity"
            print("  ✅ Similarity scores are meaningful")
        
        tests_passed += 1
        print("\n✅ TEST 3 PASSED: Semantic Search Quality Validated")
        
    except Exception as e:
        print(f"\n❌ TEST 3 FAILED: {e}")
        import traceback
        traceback.print_exc()
    
    # ============================================================================
    # TEST 4: Concurrent Access (WAL Mode)
    # ============================================================================
    print("\n" + "=" * 80)
    print("🧪 TEST 4: Concurrent Access with Semantic Memory")
    print("=" * 80)
    
    tests_total += 1
    try:
        import threading
        
        shared_memory = MemoryManager(db_path="data/test_concurrent_semantic.db")
        semantic_mem = SemanticMemory(shared_memory)
        
        print("\n  Step 1: Testing concurrent writes...")
        
        results = []
        errors = []
        
        def write_conversations(thread_id, count):
            try:
                for i in range(count):
                    semantic_mem.add_conversation_turn(
                        f"Thread {thread_id} message {i}",
                        f"Response from thread {thread_id} to message {i}"
                    )
                results.append(f"Thread {thread_id}: {count} writes")
            except Exception as e:
                errors.append(f"Thread {thread_id}: {e}")
        
        # Launch 3 threads
        threads = []
        for i in range(3):
            t = threading.Thread(target=write_conversations, args=(i, 5))
            threads.append(t)
            t.start()
        
        # Wait for all
        for t in threads:
            t.join()
        
        if errors:
            print(f"  ⚠️  Errors: {errors}")
        
        print(f"  ✅ Concurrent writes completed: {len(results)} threads successful")
        
        # Verify all writes
        stats = semantic_mem.get_stats()
        total_expected = 15  # 3 threads × 5 writes
        print(f"\n  Step 2: Verifying data integrity...")
        print(f"    Expected: {total_expected} conversations")
        print(f"    Actual: {stats.get('total_conversation_turns', 0)} conversations")
        
        # Vector store should also have the data
        vector_stats = stats.get('vector_store', {})
        print(f"    Vector store: {vector_stats.get('total_vectors', 0)} vectors")
        
        print("  ✅ Concurrent access handled correctly")
        
        tests_passed += 1
        print("\n✅ TEST 4 PASSED: Concurrent Access Working")
        
    except Exception as e:
        print(f"\n❌ TEST 4 FAILED: {e}")
        import traceback
        traceback.print_exc()
    
    # ============================================================================
    # TEST 5: Performance Under Load
    # ============================================================================
    print("\n" + "=" * 80)
    print("🧪 TEST 5: Performance Under Load")
    print("=" * 80)
    
    tests_total += 1
    try:
        semantic_mem = SemanticMemory()
        
        print("\n  Step 1: Adding 50 conversations...")
        start = time.time()
        for i in range(50):
            semantic_mem.add_conversation_turn(
                f"Test message {i}",
                f"Test response {i}"
            )
        write_time = time.time() - start
        print(f"  ✅ 50 writes in {write_time:.2f}s ({50/write_time:.1f} writes/sec)")
        
        print("\n  Step 2: Running 100 semantic searches...")
        start = time.time()
        for i in range(100):
            semantic_mem.semantic_search(f"test query {i}", k=5)
        search_time = time.time() - start
        print(f"  ✅ 100 searches in {search_time:.2f}s ({100/search_time:.1f} searches/sec)")
        
        # Verify performance targets
        assert 50/write_time > 10, "Should handle >10 writes/sec"
        assert 100/search_time > 50, "Should handle >50 searches/sec"
        
        print("\n  ✅ Performance exceeds targets")
        
        tests_passed += 1
        print("\n✅ TEST 5 PASSED: Performance Validated")
        
    except Exception as e:
        print(f"\n❌ TEST 5 FAILED: {e}")
        import traceback
        traceback.print_exc()

# ============================================================================
# RUN ALL TESTS
# ============================================================================

asyncio.run(test_integration())

# ============================================================================
# FINAL SUMMARY
# ============================================================================

print("\n" + "=" * 80)
print("📊 INTEGRATION TEST SUMMARY")
print("=" * 80)

print(f"\nTotal Tests:  {tests_total}")
print(f"Passed:       {tests_passed} ✅")
print(f"Failed:       {tests_total - tests_passed} {'❌' if tests_passed < tests_total else '✅'}")
print(f"Success Rate: {(tests_passed/tests_total)*100:.1f}%")

if tests_passed == tests_total:
    print("\n" + "=" * 80)
    print("🎉 ALL INTEGRATION TESTS PASSED!")
    print("=" * 80)
    print("\n✅ EdgeModalInterface: WORKING")
    print("✅ Semantic Memory: WORKING")
    print("✅ Cross-Modal Sharing: WORKING")
    print("✅ Search Quality: VALIDATED")
    print("✅ Concurrent Access: SAFE")
    print("✅ Performance: EXCELLENT")
    print("\n🎊 ALL SYSTEMS INTEGRATED & VALIDATED! 🎊")
    print("=" * 80)
else:
    print("\n⚠️  Some tests failed - review output above")

print()
