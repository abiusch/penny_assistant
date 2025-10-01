#!/usr/bin/env python3
"""
Test conversation understanding fixes
Validates that Penny correctly classifies different types of user input
"""

from factual_research_manager import FactualQueryClassifier

def test_conversation_understanding():
    classifier = FactualQueryClassifier()

    test_cases = [
        # User preferences - should NOT trigger research
        ("you don't need to add GPT", False, "User preference/instruction"),
        ("no need to research that", False, "User declining research"),
        ("don't bother looking that up", False, "User declining research"),
        ("skip the research", False, "User instruction"),

        # Self-reference - should NOT trigger research
        ("who are you", False, "Asking about Penny"),
        ("what are you", False, "Asking about Penny"),
        ("what can you do", False, "Asking about Penny's capabilities"),
        ("how do you work", False, "Asking about Penny's system"),
        ("tell me about yourself", False, "Asking about Penny"),
        ("are you an AI", False, "Asking about Penny"),

        # Greetings - should NOT trigger research
        ("hello", False, "Greeting"),
        ("good morning", False, "Greeting"),
        ("how are you", False, "Greeting"),

        # Factual queries - SHOULD trigger research
        ("what is the latest price of Bitcoin", True, "Current price query"),
        ("tell me about Boston Dynamics robots", True, "Company/product query"),
        ("what are the 2025 iPhone features", True, "Current product query"),

        # Financial - SHOULD trigger research
        ("should I invest in Tesla stock", True, "Investment query"),
        ("what's the market valuation of OpenAI", True, "Financial query"),
    ]

    print("🧪 TESTING CONVERSATION UNDERSTANDING")
    print("=" * 70)

    passed = 0
    failed = 0

    for query, expected_research, description in test_cases:
        result = classifier.requires_research(query)
        status = "✅" if result == expected_research else "❌"

        if result == expected_research:
            passed += 1
        else:
            failed += 1

        print(f"{status} {description}")
        print(f"   Query: \"{query}\"")
        print(f"   Expected research: {expected_research}, Got: {result}")
        print()

    print("=" * 70)
    print(f"Results: {passed}/{len(test_cases)} passed, {failed} failed")

    if failed == 0:
        print("✅ All tests passed! Conversation understanding is fixed.")
    else:
        print(f"❌ {failed} tests failed. Need more fixes.")

    return failed == 0


if __name__ == "__main__":
    success = test_conversation_understanding()
    exit(0 if success else 1)
