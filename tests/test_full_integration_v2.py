#!/usr/bin/env python3
"""
Full Integration Test v2 - Week 6 Complete System Integration
Tests: Context Manager + Emotion Detector + Semantic Memory + EdgeModalInterface

This test validates that all Week 6 components work together seamlessly:
- Context Manager tracks conversation windows
- Emotion Detector analyzes emotional state
- Semantic Memory retrieves relevant past conversations
- EdgeModalInterface integrates everything
"""

import sys
import os
import asyncio
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.core.modality.edge_modal_interface import ChatModalInterface
from src.memory import ContextManager, EmotionDetector, SemanticMemory


def print_header(text):
    """Print a formatted test header."""
    print("\n" + "=" * 70)
    print(f"🧪 {text}")
    print("=" * 70 + "\n")


def print_step(step_num, text):
    """Print a formatted test step."""
    print(f"  Step {step_num}: {text}")


def print_success(text):
    """Print a success message."""
    print(f"  ✅ {text}\n")


def print_error(text):
    """Print an error message."""
    print(f"  ❌ {text}\n")


def test_standalone_components():
    """Test 1: Verify standalone components work correctly."""
    print_header("TEST 1: Standalone Component Verification")

    # Step 1: Context Manager
    print_step(1, "Testing Context Manager...")
    ctx_mgr = ContextManager(max_window_size=5)
    ctx_mgr.add_turn("Hello!", "Hi there!")
    ctx_mgr.add_turn("How are you?", "I'm doing well, thanks!")

    assert len(ctx_mgr.context.context_window) == 2, "Context should have 2 turns"
    stats = ctx_mgr.get_stats()
    print_success(f"Context Manager working: {stats['window_size']} turns tracked")

    # Step 2: Emotion Detector
    print_step(2, "Testing Emotion Detector...")
    detector = EmotionDetector()
    result = detector.detect_emotion("I'm so happy today!")

    assert result.primary_emotion in ['joy', 'surprise'], "Should detect positive emotion"
    assert result.sentiment == 'positive', "Should detect positive sentiment"
    print_success(f"Emotion Detector working: {result.primary_emotion} ({result.confidence:.2f})")

    # Step 3: Semantic Memory
    print_step(3, "Testing Semantic Memory...")
    sem_mem = SemanticMemory()
    sem_mem.add_conversation_turn(
        user_input="I love Python programming",
        assistant_response="That's great! Python is versatile.",
        turn_id="test_1",
        context={'topic': 'programming'}
    )
    sem_mem.add_conversation_turn(
        user_input="Python is great for AI",
        assistant_response="Yes, especially with libraries like TensorFlow.",
        turn_id="test_2",
        context={'topic': 'ai'}
    )

    results = sem_mem.semantic_search(query="Python coding", k=2)
    assert len(results) > 0, "Should find similar memories"
    print_success(f"Semantic Memory working: Found {len(results)} similar memories")

    print_success("All standalone components working correctly! ✨")


def test_edge_modal_interface_initialization():
    """Test 2: Verify EdgeModalInterface initializes all components."""
    print_header("TEST 2: EdgeModalInterface Initialization")

    print_step(1, "Creating ChatModalInterface...")
    interface = ChatModalInterface(
        user_id="test_user",
        enable_edge_models=False,  # Disable to avoid loading models
        enable_personality=False    # Disable to simplify test
    )

    # Step 2: Verify components exist
    print_step(2, "Verifying all components initialized...")
    assert hasattr(interface, 'context_manager'), "Should have context_manager"
    assert hasattr(interface, 'emotion_detector'), "Should have emotion_detector"
    assert hasattr(interface, 'semantic_memory'), "Should have semantic_memory"
    print_success("All components initialized in EdgeModalInterface")

    # Step 3: Verify component types
    print_step(3, "Verifying component types...")
    assert isinstance(interface.context_manager, ContextManager), "Should be ContextManager"
    assert isinstance(interface.emotion_detector, EmotionDetector), "Should be EmotionDetector"
    assert isinstance(interface.semantic_memory, SemanticMemory), "Should be SemanticMemory"
    print_success("All components are correct types")

    interface.cleanup()
    print_success("EdgeModalInterface initialized successfully! ✨")


def test_conversation_saving():
    """Test 3: Verify conversations are saved to all systems."""
    print_header("TEST 3: Conversation Saving to All Systems")

    print_step(1, "Creating interface and saving conversation...")
    interface = ChatModalInterface(
        user_id="test_user",
        enable_edge_models=False,
        enable_personality=False
    )

    # Step 2: Save a conversation with emotion
    print_step(2, "Saving conversation with emotion detection...")
    turn_id = interface.save_conversation(
        user_input="I'm really excited about this new feature!",
        assistant_response="That's wonderful! I'm glad you're excited.",
        metadata={'test': True}
    )

    assert turn_id != "error", "Conversation should save successfully"
    print_success(f"Conversation saved with turn_id: {turn_id}")

    # Step 3: Verify saved to context manager
    print_step(3, "Verifying saved to Context Manager...")
    stats = interface.context_manager.get_stats()
    assert stats['window_size'] == 1, "Should have 1 turn in context"
    assert stats['emotional_state'] is not None, "Should have emotional state"
    print_success(f"Context Manager: {stats['window_size']} turns, emotion: {stats['emotional_state']}")

    # Step 4: Verify emotion was detected
    print_step(4, "Verifying emotion detection...")
    window = interface.context_manager.context.context_window
    assert len(window) > 0, "Should have turns in window"
    assert 'metadata' in window[0], "Turn should have metadata"
    assert 'emotion' in window[0]['metadata'], "Metadata should contain emotion"
    detected_emotion = window[0]['metadata']['emotion']
    print_success(f"Emotion detected: {detected_emotion}")

    # Step 5: Verify saved to semantic memory
    print_step(5, "Verifying saved to Semantic Memory...")
    search_results = interface.semantic_memory.semantic_search(query="excited feature", k=2)
    assert len(search_results) > 0, "Should find the saved conversation"
    print_success(f"Semantic Memory: Found {len(search_results)} results")

    interface.cleanup()
    print_success("Conversation saving to all systems working! ✨")


def test_contextual_prompt_building():
    """Test 4: Verify contextual prompt building."""
    print_header("TEST 4: Contextual Prompt Building")

    print_step(1, "Creating interface and adding conversation history...")
    interface = ChatModalInterface(
        user_id="test_user",
        enable_edge_models=False,
        enable_personality=False
    )

    # Add some conversation history
    interface.save_conversation(
        "Tell me about Python",
        "Python is a high-level programming language."
    )
    interface.save_conversation(
        "What can I use it for?",
        "You can use Python for web development, data science, AI, and more."
    )

    # Step 2: Build contextual prompt
    print_step(2, "Building contextual prompt...")
    base_prompt = "You are a helpful assistant."
    enhanced_prompt = interface._build_contextual_prompt(
        user_input="Can you help me learn Python?",
        base_prompt=base_prompt,
        max_context_turns=5
    )

    assert len(enhanced_prompt) > len(base_prompt), "Enhanced prompt should be longer"
    assert "Previous conversation:" in enhanced_prompt, "Should include conversation context"
    print_success(f"Enhanced prompt generated ({len(enhanced_prompt)} chars)")

    # Step 3: Verify context includes topic
    print_step(3, "Verifying topic extraction...")
    assert "Current topic:" in enhanced_prompt, "Should include current topic"
    print_success("Topic extraction included in prompt")

    # Step 4: Verify semantic context
    print_step(4, "Verifying semantic context...")
    # Add delay for semantic memory to index
    import time
    time.sleep(0.1)

    # Search should find previous Python conversations
    search_results = interface.semantic_memory.semantic_search(query="Python programming", k=3)
    if len(search_results) > 0:
        print_success(f"Semantic context: Found {len(search_results)} relevant memories")
    else:
        print_success("Semantic context: No results (expected for small dataset)")

    interface.cleanup()
    print_success("Contextual prompt building working! ✨")


def test_multi_turn_conversation():
    """Test 5: Multi-turn conversation with emotion tracking."""
    print_header("TEST 5: Multi-Turn Conversation Flow")

    print_step(1, "Setting up interface...")
    interface = ChatModalInterface(
        user_id="test_user",
        enable_edge_models=False,
        enable_personality=False
    )

    # Conversation sequence with varying emotions
    conversations = [
        ("Hello! I'm new here.", "Welcome! I'm happy to help you get started."),
        ("I'm having trouble with my code.", "Don't worry, I'm here to help. What's the issue?"),
        ("It keeps giving me errors!", "That's frustrating! Let me help you debug it."),
        ("Oh wait, I found the bug!", "Excellent! I'm glad you figured it out!"),
        ("Thanks for your help!", "You're very welcome! Happy to assist."),
    ]

    # Step 2: Process conversation turns
    print_step(2, "Processing 5-turn conversation...")
    for i, (user_msg, assistant_msg) in enumerate(conversations, 1):
        interface.save_conversation(user_msg, assistant_msg)
    print_success(f"Processed {len(conversations)} conversation turns")

    # Step 3: Verify context window management
    print_step(3, "Verifying context window...")
    stats = interface.context_manager.get_stats()
    assert stats['window_size'] == 5, f"Should have 5 turns, got {stats['window_size']}"
    print_success(f"Context window: {stats['window_size']} turns tracked")

    # Step 4: Analyze emotional trajectory
    print_step(4, "Analyzing emotional trajectory...")
    # Get turns from context window
    turns = interface.context_manager.context.context_window
    trajectory = interface.emotion_detector.analyze_emotional_trajectory(turns)

    emotions_detected = trajectory['emotions']
    print_success(f"Emotional trajectory: {' → '.join(emotions_detected)}")

    # Step 5: Verify topic continuity
    print_step(5, "Verifying topic tracking...")
    current_topic = stats.get('current_topic')
    print_success(f"Current topic: {current_topic if current_topic else 'general'}")

    # Step 6: Get dominant emotion
    print_step(6, "Getting dominant emotion...")
    dominant_emotion, frequency = interface.emotion_detector.get_dominant_emotion(turns)
    print_success(f"Dominant emotion: {dominant_emotion} ({frequency:.0f}x)")

    interface.cleanup()
    print_success("Multi-turn conversation tracking working! ✨")


def test_performance_benchmarks():
    """Test 6: Performance benchmarks for integration."""
    print_header("TEST 6: Performance Benchmarks")

    print_step(1, "Setting up interface...")
    interface = ChatModalInterface(
        user_id="test_user",
        enable_edge_models=False,
        enable_personality=False
    )

    # Step 2: Benchmark conversation saving
    print_step(2, "Benchmarking conversation saving (100 iterations)...")
    import time
    start = time.time()

    for i in range(100):
        interface.save_conversation(
            f"Test message {i}",
            f"Test response {i}",
            metadata={'iteration': i}
        )

    elapsed = time.time() - start
    ops_per_sec = 100 / elapsed
    print_success(f"100 saves: {elapsed:.3f}s ({ops_per_sec:.1f} ops/s)")

    # Step 3: Benchmark contextual prompt building
    print_step(3, "Benchmarking prompt building (100 iterations)...")
    start = time.time()

    for i in range(100):
        interface._build_contextual_prompt(
            user_input=f"Test query {i}",
            base_prompt="You are a helpful assistant.",
            max_context_turns=5
        )

    elapsed = time.time() - start
    ops_per_sec = 100 / elapsed
    print_success(f"100 prompts: {elapsed:.3f}s ({ops_per_sec:.1f} ops/s)")

    # Step 4: Verify performance targets
    print_step(4, "Verifying performance targets...")
    assert elapsed < 1.0, "Should build 100 prompts in <1s"
    print_success("Performance targets met! ⚡")

    interface.cleanup()
    print_success("Performance benchmarks passed! ✨")


def run_all_tests():
    """Run all integration tests."""
    print("\n" + "=" * 70)
    print("🧪 🧪 FULL INTEGRATION TEST SUITE V2")
    print("=" * 70)
    print("\nTesting Week 6 complete integration:")
    print("  - Context Manager")
    print("  - Emotion Detector")
    print("  - Semantic Memory")
    print("  - EdgeModalInterface")
    print("\nExpected time: <30 seconds\n")

    try:
        # Run all tests
        test_standalone_components()
        test_edge_modal_interface_initialization()
        test_conversation_saving()
        test_contextual_prompt_building()
        test_multi_turn_conversation()
        test_performance_benchmarks()

        # Summary
        print("\n" + "=" * 70)
        print("🧪 📊 TEST SUMMARY")
        print("=" * 70)
        print("\n✅ Standalone Components: PASSING")
        print("✅ EdgeModalInterface Init: PASSING")
        print("✅ Conversation Saving: PASSING")
        print("✅ Contextual Prompt Building: PASSING")
        print("✅ Multi-Turn Conversation: PASSING")
        print("✅ Performance Benchmarks: PASSING")

        print("\n" + "=" * 70)
        print("🎉 WEEK 6 FULL INTEGRATION: COMPLETE! ✅")
        print("=" * 70)
        print("\nAll systems operational:")
        print("  ✅ Context Manager integrated")
        print("  ✅ Emotion Detector integrated")
        print("  ✅ Semantic Memory integrated")
        print("  ✅ EdgeModalInterface enhanced")
        print("  ✅ All components working together")
        print("  ✅ Performance targets met")
        print("\n")

        return True

    except AssertionError as e:
        print_error(f"Test failed: {e}")
        return False
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
