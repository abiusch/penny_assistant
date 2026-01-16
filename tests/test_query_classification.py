#!/usr/bin/env python3
"""
Direct test of query classification system to verify research triggering.
"""

from factual_research_manager import FactualQueryClassifier

def test_query_classification():
    """Test specific investment/financial queries that should trigger research."""
    classifier = FactualQueryClassifier()

    test_queries = [
        "emerging robotics companies with investment potential",
        "I want to research emerging robotics companies",
        "What are some promising robotics startups to invest in?",
        "Tell me about specific company stock potential",
        "Should I invest in AI companies?",
        "What's the current market outlook for robotics?",
        "Hello how are you?",  # Should NOT trigger research
        "What's the weather like?",  # Should NOT trigger research
        "Tell me about Tesla stock",  # SHOULD trigger research
        "Latest updates on Apple",  # SHOULD trigger research
        "company revenue 2024",  # SHOULD trigger research
    ]

    print("🔍 QUERY CLASSIFICATION TESTING")
    print("=" * 50)

    for query in test_queries:
        requires_research = classifier.requires_research(query)
        is_financial = classifier.is_financial_topic(query)
        entities = classifier.extract_entities(query)

        status = "✅ RESEARCH" if requires_research else "❌ NO RESEARCH"
        financial_status = "💰 FINANCIAL" if is_financial else "   NON-FINANCIAL"

        print(f"\nQuery: '{query}'")
        print(f"  {status}")
        print(f"  {financial_status}")
        if entities:
            print(f"  📝 Entities: {entities}")

    print("\n" + "=" * 50)
    print("🎯 EXPECTED BEHAVIOR:")
    print("- Investment/financial queries should show '✅ RESEARCH'")
    print("- Casual queries should show '❌ NO RESEARCH'")
    print("- All investment queries should show '💰 FINANCIAL'")

if __name__ == "__main__":
    test_query_classification()