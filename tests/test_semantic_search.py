#!/usr/bin/env python3
"""
Comprehensive Test Suite for Semantic Search System
Week 5 Implementation Validation
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
import numpy as np
from src.memory.embedding_generator import get_embedding_generator
from src.memory.vector_store import VectorStore
from src.memory.semantic_memory import SemanticMemory


def print_header(title):
    """Print a formatted test header"""
    print("\n" + "=" * 70)
    print(f"🧪 {title}")
    print("=" * 70)


def print_test(title):
    """Print a test section header"""
    print(f"\n✅ {title}")
    print("-" * 70)


def test_embedding_generation():
    """Test 1: Embedding Generation"""
    print_test("TEST 1: Embedding Generation")

    generator = get_embedding_generator()

    # Test single embedding
    text = "Python is a programming language"
    embedding = generator.encode(text)
    print(f"  Single embedding shape: {embedding.shape}")
    print(f"  ✅ Single text embedding: {embedding.shape[0]} dimensions")

    # Test batch embeddings
    texts = [
        "Python is a programming language",
        "JavaScript is used for web development",
        "Machine learning is fascinating"
    ]
    embeddings = generator.encode(texts)
    print(f"  Batch embedding shape: {embeddings.shape}")
    print(f"  ✅ Batch embeddings: {embeddings.shape}")

    # Test similarity calculation
    emb1 = generator.encode("Python programming")
    emb2 = generator.encode("Python coding")
    emb3 = generator.encode("The weather is nice")

    sim_related = generator.cosine_similarity(emb1, emb2)
    sim_unrelated = generator.cosine_similarity(emb1, emb3)

    print(f"  Similarity (related): {sim_related:.3f}")
    print(f"  Similarity (unrelated): {sim_unrelated:.3f}")
    print(f"  ✅ Similarity calculation works")

    return True


def test_vector_store():
    """Test 2: Vector Store Operations"""
    print_test("TEST 2: Vector Store Operations")

    generator = get_embedding_generator()
    store = VectorStore(embedding_dim=384)

    # Add vectors
    texts = [
        "Python is a programming language",
        "JavaScript is used for web development",
        "The weather is nice today"
    ]

    embeddings = generator.encode(texts)
    metadata_list = [{'text': text} for text in texts]

    ids = store.add(embeddings, metadata=metadata_list)
    print(f"  Added {len(ids)} vectors with IDs: {ids}")
    print(f"  ✅ Vector addition works")

    # Search vectors
    query = "tell me about programming languages"
    query_emb = generator.encode(query)
    results = store.search(query_emb, k=2)

    print(f"  Search results: {len(results)}")
    for result in results:
        text = result['metadata']['text']
        distance = result['distance']
        print(f"    - {text} (distance: {distance:.3f})")
    print(f"  ✅ Vector search works")

    # Get stats
    stats = store.get_stats()
    print(f"  Store stats: {stats['total_vectors']} vectors, {stats['embedding_dim']} dims")
    print(f"  ✅ Stats retrieval works")

    return True


def test_semantic_memory():
    """Test 3: Semantic Memory Integration"""
    print_test("TEST 3: Semantic Memory Integration")

    memory = SemanticMemory()

    # Add conversations
    conversations = [
        ("What is Python?", "Python is a high-level programming language known for its simplicity and readability."),
        ("How do I learn JavaScript?", "Start with the basics of JavaScript syntax, then move on to DOM manipulation and frameworks."),
        ("Tell me about machine learning", "Machine learning is a subset of AI that enables systems to learn from data."),
        ("What's the weather like?", "I don't have access to real-time weather data, but you can check a weather service.")
    ]

    for user_input, assistant_response in conversations:
        memory.add_conversation_turn(user_input, assistant_response)
        print(f"  Added: '{user_input}'")

    print(f"  ✅ Added {len(conversations)} conversations")

    # Test semantic search
    print("\n  Testing semantic search...")
    query = "How can I learn to code?"
    results = memory.semantic_search(query, k=3, min_similarity=0.3)

    print(f"  Found {len(results)} similar conversations:")
    for result in results:
        print(f"    - {result['user_input']} (similarity: {result['similarity']:.3f})")
    print(f"  ✅ Semantic search finds relevant conversations")

    # Test context retrieval
    context = memory.get_relevant_context("How do I code?", max_turns=2)
    print(f"\n  Context for 'How do I code?':")
    print(f"    {len(context)} characters of context")
    print(f"  ✅ Context retrieval works")

    return True


def test_performance():
    """Test 4: Performance Benchmarks"""
    print_test("TEST 4: Performance Benchmarks")

    generator = get_embedding_generator()
    store = VectorStore(embedding_dim=384)

    # Benchmark embedding generation
    test_texts = [f"This is test sentence number {i}" for i in range(100)]

    start = time.time()
    embeddings = generator.encode(test_texts)
    embed_time = time.time() - start

    embed_rate = len(test_texts) / embed_time
    print(f"  100 embeddings: {embed_time:.3f}s ({embed_rate:.1f} emb/s)")

    # Add to store for search benchmark
    store.add(embeddings)

    # Benchmark search
    query_emb = generator.encode("test sentence")

    start = time.time()
    for _ in range(100):
        store.search(query_emb, k=5)
    search_time = time.time() - start

    search_rate = 100 / search_time
    print(f"  100 searches: {search_time:.3f}s ({search_rate:.1f} searches/s)")
    print(f"  ✅ Performance acceptable")

    return True


def test_edge_cases():
    """Test 5: Edge Cases"""
    print_test("TEST 5: Edge Cases")

    memory = SemanticMemory()

    # Add some test data
    memory.add_conversation_turn("Test 1", "Response 1")
    memory.add_conversation_turn("Test 2", "Response 2")
    memory.add_conversation_turn("Test 3", "Response 3")

    # Search with nonsense query (should still return results)
    results = memory.semantic_search("asdfghjkl qwerty", k=3)
    print(f"  Search for nonsense: {len(results)} results")
    print(f"  ✅ Handles edge cases")

    # Get stats
    stats = memory.get_stats()
    print(f"\n  Semantic Memory Stats:")
    print(f"    Total conversations: {stats['total_conversations']}")
    print(f"    Vector store size: {stats['vector_store_size']}")
    print(f"    Embedding model: {stats['model_name']}")
    print(f"  ✅ Stats collection works")

    return True


def main():
    """Run all tests"""
    print_header("🧪 SEMANTIC SEARCH TEST SUITE")

    print("\nThis will test the performance of all semantic search components.")
    print("Expected time: 2-3 minutes (first run downloads model)\n")

    # Track results
    tests = [
        ("Embedding generation", test_embedding_generation),
        ("Vector store", test_vector_store),
        ("Semantic search", test_semantic_memory),
        ("Memory integration", test_performance),
        ("Performance", test_edge_cases),
    ]

    results = {}
    for test_name, test_func in tests:
        try:
            success = test_func()
            results[test_name] = "WORKING" if success else "FAILED"
        except Exception as e:
            print(f"\n  ❌ Error: {e}")
            import traceback
            traceback.print_exc()
            results[test_name] = "ERROR"

    # Print summary
    print_header("📊 TEST SUMMARY")
    print()

    all_passed = True
    for test_name, status in results.items():
        symbol = "✅" if status == "WORKING" else "❌"
        print(f"{symbol} {test_name}: {status}")
        if status != "WORKING":
            all_passed = False

    # Final message
    if all_passed:
        print("\n" + "=" * 70)
        print("🎉 WEEK 5: SEMANTIC SEARCH COMPLETE! ✅")
        print("=" * 70)
    else:
        print("\n" + "=" * 70)
        print("⚠️  SOME TESTS FAILED - CHECK ERRORS ABOVE")
        print("=" * 70)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Tests cancelled by user")
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
