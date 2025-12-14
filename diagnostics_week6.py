#!/usr/bin/env python3
"""
Week 6 Integration Diagnostics - Comprehensive Bug Check
Runs multiple diagnostic tests to find potential issues.
"""

import sys
import traceback
from typing import List, Tuple

# Test results
results = []

def test_result(name: str, passed: bool, details: str = ""):
    """Record test result"""
    status = "✅ PASS" if passed else "❌ FAIL"
    results.append((name, passed, details))
    print(f"{status}: {name}")
    if details:
        print(f"   {details}")

def diagnostic_1_imports():
    """Test 1: Verify all Week 6 imports work"""
    try:
        from src.memory import ContextManager, EmotionDetector, SemanticMemory
        test_result("Week 6 imports", True, "All imports successful")
        return True
    except Exception as e:
        test_result("Week 6 imports", False, f"Import error: {e}")
        return False

def diagnostic_2_initialization():
    """Test 2: Verify Week 6 systems initialize correctly"""
    try:
        from src.memory import ContextManager, EmotionDetector, SemanticMemory

        ctx = ContextManager(max_window_size=10)
        emo = EmotionDetector()
        sem = SemanticMemory()

        test_result("Week 6 initialization", True, "All systems initialized")
        return True
    except Exception as e:
        test_result("Week 6 initialization", False, f"Init error: {e}")
        return False

def diagnostic_3_emotion_detection():
    """Test 3: Verify emotion detection works correctly"""
    try:
        from src.memory import EmotionDetector

        detector = EmotionDetector()

        # Test cases
        test_cases = [
            ("I'm thrilled to see the new features working!", "joy"),
            ("I'm so excited!", "joy"),
            ("This is frustrating", "anger"),
            ("Hello there", "neutral"),
        ]

        all_passed = True
        for text, expected_emotion in test_cases:
            result = detector.detect_emotion(text)
            if result.primary_emotion != expected_emotion:
                all_passed = False
                test_result(f"Emotion: '{text[:30]}...'", False,
                           f"Expected {expected_emotion}, got {result.primary_emotion}")
            else:
                test_result(f"Emotion: '{text[:30]}...'", True)

        return all_passed
    except Exception as e:
        test_result("Emotion detection", False, f"Error: {e}")
        return False

def diagnostic_4_research_classification():
    """Test 4: Verify research classification doesn't trigger on conversational messages"""
    try:
        from factual_research_manager import FactualQueryClassifier

        classifier = FactualQueryClassifier()

        # Test cases: (text, should_research)
        test_cases = [
            ("I'm thrilled to see the new features working!", False),
            ("I'm so excited to test this!", False),
            ("Thanks for the help!", False),
            ("This is awesome!", False),
            ("What's the current stock price of Apple?", True),
            ("Tell me the latest news about Tesla", True),
            ("Hello Penny!", False),
            ("How are you doing?", False),
        ]

        all_passed = True
        for text, should_research in test_cases:
            result = classifier.requires_research(text)
            if result != should_research:
                all_passed = False
                test_result(f"Research: '{text[:40]}...'", False,
                           f"Expected research={should_research}, got {result}")
            else:
                test_result(f"Research: '{text[:40]}...'", True)

        return all_passed
    except Exception as e:
        test_result("Research classification", False, f"Error: {e}\n{traceback.format_exc()}")
        return False

def diagnostic_5_context_manager():
    """Test 5: Verify context manager stores and retrieves correctly"""
    try:
        from src.memory import ContextManager

        ctx = ContextManager(max_window_size=5)

        # Add some turns
        ctx.add_turn("Hello", "Hi there!", {"emotion": "joy"})
        ctx.add_turn("How are you?", "I'm doing great!", {"emotion": "joy"})
        ctx.add_turn("Tell me a joke", "Why did the chicken cross the road?", {"emotion": "neutral"})

        # Get stats
        stats = ctx.get_stats()

        if stats['window_size'] != 3:
            test_result("Context Manager: window size", False, f"Expected 3, got {stats['window_size']}")
            return False

        # Get context for prompt
        context = ctx.get_context_for_prompt(max_turns=2)

        if len(context) == 0:
            test_result("Context Manager: context retrieval", False, "No context retrieved")
            return False

        test_result("Context Manager", True, f"Stored {stats['window_size']} turns successfully")
        return True
    except Exception as e:
        test_result("Context Manager", False, f"Error: {e}")
        return False

def diagnostic_6_semantic_memory():
    """Test 6: Verify semantic memory saves and searches (may have cache permission issues)"""
    try:
        from src.memory import SemanticMemory

        sem = SemanticMemory()

        # Try to add a turn
        sem.add_conversation_turn(
            user_input="What's the weather?",
            assistant_response="I don't have real-time weather data.",
            turn_id="test-001",
            context={"emotion": "neutral"}
        )

        # Try to search
        results = sem.semantic_search("weather forecast", k=1)

        test_result("Semantic Memory", True, f"Found {len(results)} results")
        return True
    except PermissionError as e:
        test_result("Semantic Memory", False, f"⚠️ Cache permission issue (known): {e}")
        return False
    except Exception as e:
        test_result("Semantic Memory", False, f"Error: {e}")
        return False

def diagnostic_7_integration_pipeline():
    """Test 7: Verify ResearchFirstPipeline has Week 6 integration"""
    try:
        from research_first_pipeline import ResearchFirstPipeline

        # Check if Week 6 attributes exist
        pipeline = ResearchFirstPipeline(
            llm=None,  # We won't call it
            base_memory=None,
            enhanced_memory=None
        )

        if not hasattr(pipeline, 'context_manager'):
            test_result("Pipeline integration: context_manager", False, "Attribute missing")
            return False

        if not hasattr(pipeline, 'emotion_detector'):
            test_result("Pipeline integration: emotion_detector", False, "Attribute missing")
            return False

        if not hasattr(pipeline, 'semantic_memory'):
            test_result("Pipeline integration: semantic_memory", False, "Attribute missing")
            return False

        test_result("Pipeline integration", True, "All Week 6 attributes present")
        return True
    except Exception as e:
        test_result("Pipeline integration", False, f"Error: {e}")
        return False

def diagnostic_8_prompt_building():
    """Test 8: Verify prompt includes Week 6 context"""
    try:
        # This is checked via the debug output in actual runs
        # For now, just verify the debug line exists in the code
        with open('research_first_pipeline.py', 'r') as f:
            content = f.read()

        if "🔍 FULL PROMPT SENT TO LLM" not in content:
            test_result("Prompt debug logging", False, "Debug line missing")
            return False

        test_result("Prompt debug logging", True, "Debug line present")
        return True
    except Exception as e:
        test_result("Prompt debug logging", False, f"Error: {e}")
        return False

def main():
    """Run all diagnostics"""
    print("=" * 60)
    print("WEEK 6 INTEGRATION - COMPREHENSIVE DIAGNOSTICS")
    print("=" * 60)
    print()

    diagnostics = [
        diagnostic_1_imports,
        diagnostic_2_initialization,
        diagnostic_3_emotion_detection,
        diagnostic_4_research_classification,
        diagnostic_5_context_manager,
        diagnostic_6_semantic_memory,
        diagnostic_7_integration_pipeline,
        diagnostic_8_prompt_building,
    ]

    for diagnostic in diagnostics:
        print(f"\n{'─' * 60}")
        print(f"Running: {diagnostic.__doc__.split(':')[1].strip()}")
        print('─' * 60)
        try:
            diagnostic()
        except Exception as e:
            print(f"❌ CRASH: {e}")
            traceback.print_exc()

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    passed = sum(1 for _, p, _ in results if p)
    total = len(results)

    print(f"\nTests passed: {passed}/{total}")

    if passed == total:
        print("\n✅ ALL DIAGNOSTICS PASSED!")
    else:
        print(f"\n⚠️ {total - passed} ISSUES FOUND:")
        for name, passed, details in results:
            if not passed:
                print(f"   • {name}")
                if details:
                    print(f"     {details}")

    return 0 if passed == total else 1

if __name__ == "__main__":
    sys.exit(main())
