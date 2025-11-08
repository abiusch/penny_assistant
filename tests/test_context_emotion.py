#!/usr/bin/env python3
"""
Comprehensive Test Suite for Context Manager & Emotion Detector
Week 6 Implementation Validation
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
from src.memory.context_manager import ContextManager, ConversationContext
from src.memory.emotion_detector import EmotionDetector, EmotionResult


def print_header(title):
    """Print a formatted test header"""
    print("\n" + "=" * 70)
    print(f"🧪 {title}")
    print("=" * 70)


def print_test(title):
    """Print a test section header"""
    print(f"\n✅ {title}")
    print("-" * 70)


def test_context_manager():
    """Test 1: ContextManager Functionality"""
    print_test("TEST 1: ContextManager Functionality")

    manager = ContextManager(max_window_size=5)

    # Test 1.1: Add turns
    print("  Step 1: Adding conversation turns...")
    manager.add_turn(
        "What is Python?",
        "Python is a high-level programming language.",
        {'emotion': 'neutral'}
    )
    manager.add_turn(
        "How do I learn it?",
        "Start with the basics and practice regularly.",
        {'emotion': 'curious'}
    )
    manager.add_turn(
        "This is great!",
        "I'm glad you're excited about learning!",
        {'emotion': 'joy'}
    )

    window = manager.get_context_window()
    assert len(window) == 3, f"Expected 3 turns, got {len(window)}"
    print(f"  ✅ Added 3 turns successfully")

    # Test 1.2: Window size limit
    print("\n  Step 2: Testing window size limits...")
    for i in range(5):
        manager.add_turn(f"Question {i}", f"Answer {i}")

    window = manager.get_context_window()
    assert len(window) == 5, f"Expected max 5 turns, got {len(window)}"
    print(f"  ✅ Window size limited to 5 turns")

    # Test 1.3: Topic extraction
    print("\n  Step 3: Testing topic extraction...")
    manager_topic = ContextManager()
    manager_topic.add_turn(
        "Tell me about Python programming",
        "Python is great for beginners"
    )
    topic = manager_topic.get_current_topic()
    assert topic == 'programming', f"Expected 'programming', got '{topic}'"
    print(f"  ✅ Topic extracted: {topic}")

    # Test 1.4: Context summarization
    print("\n  Step 4: Testing context summarization...")
    summary = manager.summarize_context()
    assert "5 turn(s)" in summary, "Summary should mention turn count"
    print(f"  ✅ Summary generated: {summary[:60]}...")

    # Test 1.5: Context for prompt
    print("\n  Step 5: Testing prompt formatting...")
    prompt_context = manager.get_context_for_prompt(max_turns=2)
    assert "Previous conversation:" in prompt_context
    assert "Turn 1:" in prompt_context
    print(f"  ✅ Prompt context formatted ({len(prompt_context)} chars)")

    # Test 1.6: Clear context
    print("\n  Step 6: Testing context clearing...")
    manager.clear_context()
    window = manager.get_context_window()
    assert len(window) == 0, "Window should be empty after clear"
    print(f"  ✅ Context cleared successfully")

    return True


def test_emotion_detector():
    """Test 2: EmotionDetector Functionality"""
    print_test("TEST 2: EmotionDetector Functionality")

    detector = EmotionDetector()

    # Test 2.1: Detect joy
    print("  Step 1: Testing joy detection...")
    result = detector.detect_emotion("I'm so happy and excited about this!")
    assert result.primary_emotion == 'joy', f"Expected 'joy', got '{result.primary_emotion}'"
    assert result.confidence > 0.5, "Confidence should be high for clear emotion"
    assert result.sentiment == 'positive'
    print(f"  ✅ Joy detected (confidence: {result.confidence:.2f})")

    # Test 2.2: Detect sadness
    print("\n  Step 2: Testing sadness detection...")
    result = detector.detect_emotion("I'm feeling really sad and down today")
    assert result.primary_emotion == 'sadness', f"Expected 'sadness', got '{result.primary_emotion}'"
    assert result.sentiment == 'negative'
    print(f"  ✅ Sadness detected (confidence: {result.confidence:.2f})")

    # Test 2.3: Detect anger
    print("\n  Step 3: Testing anger detection...")
    result = detector.detect_emotion("This is so frustrating and annoying!")
    assert result.primary_emotion == 'anger', f"Expected 'anger', got '{result.primary_emotion}'"
    assert result.sentiment == 'negative'
    print(f"  ✅ Anger detected (confidence: {result.confidence:.2f})")

    # Test 2.4: Detect fear
    print("\n  Step 4: Testing fear detection...")
    result = detector.detect_emotion("I'm really worried and scared about this")
    assert result.primary_emotion == 'fear', f"Expected 'fear', got '{result.primary_emotion}'"
    print(f"  ✅ Fear detected (confidence: {result.confidence:.2f})")

    # Test 2.5: Detect surprise
    print("\n  Step 5: Testing surprise detection...")
    result = detector.detect_emotion("Wow! That's so amazing and unexpected!")
    assert result.primary_emotion in ['surprise', 'joy'], "Should detect surprise or joy"
    print(f"  ✅ Surprise/Joy detected: {result.primary_emotion}")

    # Test 2.6: Neutral text
    print("\n  Step 6: Testing neutral text...")
    result = detector.detect_emotion("The meeting is at 3pm tomorrow")
    assert result.primary_emotion == 'neutral', f"Expected 'neutral', got '{result.primary_emotion}'"
    print(f"  ✅ Neutral detected")

    return True


def test_sentiment_analysis():
    """Test 3: Sentiment Analysis"""
    print_test("TEST 3: Sentiment Analysis")

    detector = EmotionDetector()

    # Test 3.1: Positive sentiment
    print("  Step 1: Testing positive sentiment...")
    sentiment, score = detector.get_sentiment("This is great and wonderful!")
    assert sentiment == 'positive', f"Expected 'positive', got '{sentiment}'"
    assert score > 0, f"Expected positive score, got {score}"
    print(f"  ✅ Positive sentiment: {score:.2f}")

    # Test 3.2: Negative sentiment
    print("\n  Step 2: Testing negative sentiment...")
    sentiment, score = detector.get_sentiment("This is terrible and awful")
    assert sentiment == 'negative', f"Expected 'negative', got '{sentiment}'"
    assert score < 0, f"Expected negative score, got {score}"
    print(f"  ✅ Negative sentiment: {score:.2f}")

    # Test 3.3: Neutral sentiment
    print("\n  Step 3: Testing neutral sentiment...")
    sentiment, score = detector.get_sentiment("The book is on the table")
    assert sentiment == 'neutral', f"Expected 'neutral', got '{sentiment}'"
    assert abs(score) < 0.3, "Neutral score should be close to 0"
    print(f"  ✅ Neutral sentiment: {score:.2f}")

    # Test 3.4: Negation handling
    print("\n  Step 4: Testing negation...")
    sentiment1, score1 = detector.get_sentiment("This is good")
    sentiment2, score2 = detector.get_sentiment("This is not good")
    assert score2 < score1, "Negation should reduce positive sentiment"
    print(f"  ✅ Negation handled: 'good'={score1:.2f}, 'not good'={score2:.2f}")

    return True


def test_emotional_trajectory():
    """Test 4: Emotional Trajectory Analysis"""
    print_test("TEST 4: Emotional Trajectory Analysis")

    detector = EmotionDetector()

    # Create conversation with changing emotions
    turns = [
        {'user_input': "I'm excited to start!", 'assistant_response': "Great!"},
        {'user_input': "This is getting difficult", 'assistant_response': "Keep going"},
        {'user_input': "I'm frustrated now", 'assistant_response': "That's normal"},
        {'user_input': "Finally got it working!", 'assistant_response': "Excellent!"},
    ]

    print("  Step 1: Analyzing emotional trajectory...")
    trajectory = detector.analyze_emotional_trajectory(turns)

    emotions = trajectory['emotions']
    assert len(emotions) == 4, f"Expected 4 emotions, got {len(emotions)}"
    print(f"  ✅ Emotions: {' → '.join(emotions)}")

    print("\n  Step 2: Checking overall trend...")
    trend = trajectory['overall_trend']
    print(f"  ✅ Overall trend: {trend}")

    print("\n  Step 3: Checking emotional variance...")
    variance = trajectory['emotional_variance']
    assert variance >= 0, "Variance should be non-negative"
    print(f"  ✅ Emotional variance: {variance:.3f}")

    return True


def test_context_emotion_integration():
    """Test 5: Context + Emotion Integration"""
    print_test("TEST 5: Context + Emotion Integration")

    manager = ContextManager(max_window_size=10)
    detector = EmotionDetector()

    print("  Step 1: Adding turns with emotion detection...")

    conversations = [
        ("I love Python!", "It's a great language!"),
        ("How do I handle errors?", "Use try-except blocks."),
        ("This is confusing", "Let me explain better."),
        ("Ah, I get it now!", "Excellent!"),
    ]

    for user_msg, assistant_msg in conversations:
        # Detect emotion
        emotion_result = detector.detect_emotion(user_msg)

        # Add to context with emotion metadata
        manager.add_turn(
            user_msg,
            assistant_msg,
            {
                'emotion': emotion_result.primary_emotion,
                'sentiment': emotion_result.sentiment,
                'confidence': emotion_result.confidence
            }
        )

    print(f"  ✅ Added {len(conversations)} turns with emotion tracking")

    # Test context retrieval
    print("\n  Step 2: Retrieving context with emotions...")
    context = manager.get_context_for_prompt(include_metadata=True)
    assert "Emotion:" in context, "Should include emotion metadata"
    print(f"  ✅ Context includes emotions ({len(context)} chars)")

    # Test emotional trajectory
    print("\n  Step 3: Analyzing emotional trajectory...")
    window = manager.get_context_window()
    trajectory = detector.analyze_emotional_trajectory(window)
    print(f"  ✅ Emotions: {' → '.join(trajectory['emotions'])}")

    # Test stats
    print("\n  Step 4: Getting context stats...")
    stats = manager.get_stats()
    assert stats['window_size'] == 4, f"Expected 4 turns, got {stats['window_size']}"
    assert stats['current_topic'] is not None, "Should have a topic"
    print(f"  ✅ Stats: {stats['window_size']} turns, topic='{stats['current_topic']}'")

    return True


def test_performance():
    """Test 6: Performance Benchmarks"""
    print_test("TEST 6: Performance Benchmarks")

    manager = ContextManager()
    detector = EmotionDetector()

    # Test context manager performance
    print("  Step 1: Benchmarking context manager...")
    start = time.time()
    for i in range(100):
        manager.add_turn(f"Question {i}", f"Answer {i}")
    context_time = time.time() - start
    print(f"  ✅ 100 context adds: {context_time:.3f}s ({100/context_time:.1f} ops/s)")

    # Test emotion detection performance
    print("\n  Step 2: Benchmarking emotion detection...")
    test_texts = [
        "I'm happy",
        "This is sad",
        "So angry",
        "Feeling scared",
        "What a surprise!",
    ] * 20  # 100 texts

    start = time.time()
    for text in test_texts:
        detector.detect_emotion(text)
    emotion_time = time.time() - start
    print(f"  ✅ 100 emotion detections: {emotion_time:.3f}s ({100/emotion_time:.1f} ops/s)")

    # Check performance targets
    assert context_time < 1.0, "Context operations should be <1s for 100 ops"
    assert emotion_time < 1.0, "Emotion detection should be <1s for 100 ops"
    print("\n  ✅ Performance meets targets (<1s for 100 operations)")

    return True


def main():
    """Run all tests"""
    print_header("🧪 CONTEXT & EMOTION TEST SUITE")

    print("\nThis will test context management and emotion detection.")
    print("Expected time: <30 seconds\n")

    # Track results
    tests = [
        ("ContextManager", test_context_manager),
        ("EmotionDetector", test_emotion_detector),
        ("Sentiment Analysis", test_sentiment_analysis),
        ("Emotional Trajectory", test_emotional_trajectory),
        ("Context + Emotion Integration", test_context_emotion_integration),
        ("Performance", test_performance),
    ]

    results = {}
    for test_name, test_func in tests:
        try:
            success = test_func()
            results[test_name] = "PASSING" if success else "FAILED"
        except AssertionError as e:
            print(f"\n  ❌ Assertion Error: {e}")
            results[test_name] = "FAILED"
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
        symbol = "✅" if status == "PASSING" else "❌"
        print(f"{symbol} {test_name}: {status}")
        if status != "PASSING":
            all_passed = False

    # Final message
    if all_passed:
        print("\n" + "=" * 70)
        print("🎉 WEEK 6: CONTEXT & EMOTION TRACKING COMPLETE! ✅")
        print("=" * 70)
        print("\nAll systems operational:")
        print("  ✅ Context manager tracks conversation windows")
        print("  ✅ Topic extraction working")
        print("  ✅ Emotion detection (6 emotions)")
        print("  ✅ Sentiment analysis (-1 to 1)")
        print("  ✅ Emotional trajectory tracking")
        print("  ✅ Performance <10ms per operation")
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
