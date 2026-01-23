"""
Demo script for Week 8.5 Judgment & Clarify System

Shows how the judgment system works end-to-end.
"""

from src.judgment import JudgmentEngine, PennyStyleClarifier


def demo_judgment_system():
    """Demonstrate the judgment system with various scenarios."""

    print("=" * 60)
    print("🧠 WEEK 8.5 JUDGMENT & CLARIFY SYSTEM DEMO")
    print("=" * 60)
    print()

    # Initialize
    engine = JudgmentEngine()
    clarifier = PennyStyleClarifier()

    # Empty context for demos
    empty_context = {
        'conversation_history': [],
        'semantic_memory': [],
        'emotional_state': None,
        'personality_state': None
    }

    # Test scenarios
    scenarios = [
        ("Fix that thing", "Vague referent"),
        ("Delete all production data", "High stakes"),
        ("Schedule a meeting", "Missing parameters"),
        ("What is Python?", "Clear question - no clarification"),
        ("Just fix the fucking bug already", "Frustrated user"),
        ("Debug it", "Vague referent (pronoun)"),
        ("Send an email", "Missing parameters"),
        ("What's 2 + 2?", "Clear question - no clarification"),
    ]

    for user_input, description in scenarios:
        print(f"📝 Scenario: {description}")
        print(f"👤 User: \"{user_input}\"")
        print()

        # Get judgment decision
        decision = engine.analyze_request(user_input, empty_context)

        print(f"   🤔 Judgment Analysis:")
        print(f"      - Clarify needed: {decision.clarify_needed}")
        print(f"      - Confidence: {decision.confidence:.2f}")
        print(f"      - Stakes: {decision.stakes_level.value}")
        print(f"      - Reasoning: {decision.reasoning}")
        print()

        if decision.clarify_needed:
            # Format in Penny's voice
            question = clarifier.format_question(decision, user_input)
            print(f"   💬 Penny: \"{question}\"")
        else:
            print(f"   ✅ Penny: Proceeding with request (no clarification needed)")

        print()
        print("-" * 60)
        print()

    # Test with contradiction context
    print("📝 Scenario: Contradiction detection")
    print("👤 User: \"I prefer Rust for this project\"")
    print("👤 User: \"Use Python for the API\"")
    print()

    context_with_history = {
        'conversation_history': [
            {'role': 'user', 'content': 'I prefer Rust for this project'}
        ],
        'semantic_memory': [],
        'emotional_state': None,
        'personality_state': None
    }

    decision = engine.analyze_request("Use Python for the API", context_with_history)

    print(f"   🤔 Judgment Analysis:")
    print(f"      - Clarify needed: {decision.clarify_needed}")
    print(f"      - Confidence: {decision.confidence:.2f}")
    print(f"      - Stakes: {decision.stakes_level.value}")
    print(f"      - Reasoning: {decision.reasoning}")
    print()

    if decision.clarify_needed:
        question = clarifier.format_question(decision, "Use Python for the API")
        print(f"   💬 Penny: \"{question}\"")

    print()
    print("-" * 60)
    print()

    print("✅ Demo complete!")
    print()
    print("Summary:")
    print("  - Vague requests → Get clarification")
    print("  - High stakes → Get confirmation")
    print("  - Missing params → Ask for details")
    print("  - Clear requests → Proceed directly")
    print("  - Frustrated users → Empathetic clarification")
    print("  - Contradictions → Question what changed")
    print()
    print("🎉 Week 8.5 Judgment & Clarify System is complete!")
    print()
    print("Next Steps:")
    print("  - Run integration tests: pytest tests/test_week8_5_integration.py -v")
    print("  - Run all tests: pytest tests/ -v")
    print("  - Expected: 71+ tests passing (61 from Phase 1+2, 10+ from Phase 3)")


if __name__ == '__main__':
    demo_judgment_system()
