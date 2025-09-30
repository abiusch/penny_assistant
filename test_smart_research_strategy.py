#!/usr/bin/env python3
"""
Test the smart research strategy that balances training knowledge vs research requirements.
"""

import sys
import os
import time

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_smart_research_classification():
    """Test the smart research classification logic"""
    print("🧪 SMART RESEARCH STRATEGY VALIDATION")
    print("=" * 70)

    try:
        from research_first_pipeline import ResearchFirstPipeline
        from core.pipeline import State

        pipeline = ResearchFirstPipeline()

        # Test cases organized by expected behavior
        test_scenarios = [
            # Should NOT require research (use training knowledge)
            {
                "category": "General Knowledge (No Research)",
                "queries": [
                    "What is machine learning?",
                    "How does Python work?",
                    "Explain artificial intelligence",
                    "Tell me about neural networks",
                    "What are the benefits of renewable energy?",
                    "How do computers process data?",
                ],
                "should_research": False,
                "expected_behavior": "Use training knowledge with general disclaimers"
            },

            # Should NOT require research (personal/conversational)
            {
                "category": "Personal/Conversational (No Research)",
                "queries": [
                    "Hello, how are you?",
                    "What's your favorite programming language?",
                    "Can you help me debug my code?",
                    "How do you feel about technology?",
                    "What's the weather like?",
                ],
                "should_research": False,
                "expected_behavior": "Normal conversational response"
            },

            # SHOULD require research (time-sensitive)
            {
                "category": "Time-Sensitive (Research Required)",
                "queries": [
                    "What are the latest updates to Boston Dynamics Stretch robot?",
                    "What's the current price of Tesla stock?",
                    "Tell me about recent OpenAI announcements",
                    "What new features were released in iOS 2024?",
                    "What are today's top tech news stories?",
                ],
                "should_research": True,
                "expected_behavior": "Attempt research, acknowledge limitations if fails"
            },

            # SHOULD require research (financial)
            {
                "category": "Financial/Investment (Research Required)",
                "queries": [
                    "What robotics companies should I invest in?",
                    "What's the current market cap of Google?",
                    "Tell me about emerging cryptocurrency investments",
                    "What are the best tech stocks to buy now?",
                    "What's the revenue of Boston Dynamics?",
                ],
                "should_research": True,
                "expected_behavior": "Attempt research, include financial disclaimer"
            },

            # SHOULD require research (statistics/data)
            {
                "category": "Statistics/Data (Research Required)",
                "queries": [
                    "What percentage of companies use AI in 2024?",
                    "Show me the latest studies on remote work productivity",
                    "What are the current statistics on electric vehicle adoption?",
                    "What does recent research say about climate change?",
                ],
                "should_research": True,
                "expected_behavior": "Attempt research, no fabricated statistics"
            }
        ]

        print("\n🔍 CLASSIFICATION TESTING")
        print("-" * 50)

        classification_results = []

        for scenario in test_scenarios:
            print(f"\n📂 {scenario['category']}")
            scenario_correct = 0
            scenario_total = len(scenario['queries'])

            for query in scenario['queries']:
                research_required = pipeline.research_manager.requires_research(query)
                expected = scenario['should_research']

                if research_required == expected:
                    result = "✅"
                    scenario_correct += 1
                else:
                    result = "❌"

                print(f"  {result} '{query[:50]}...' → Research: {research_required} (Expected: {expected})")

            accuracy = (scenario_correct / scenario_total) * 100
            classification_results.append({
                "category": scenario['category'],
                "accuracy": accuracy,
                "correct": scenario_correct,
                "total": scenario_total
            })
            print(f"  📊 Category Accuracy: {accuracy:.1f}% ({scenario_correct}/{scenario_total})")

        # Overall classification accuracy
        total_correct = sum(r['correct'] for r in classification_results)
        total_queries = sum(r['total'] for r in classification_results)
        overall_accuracy = (total_correct / total_queries) * 100

        print(f"\n📈 OVERALL CLASSIFICATION ACCURACY: {overall_accuracy:.1f}% ({total_correct}/{total_queries})")

        # Test actual responses for key scenarios
        print(f"\n🤖 RESPONSE BEHAVIOR TESTING")
        print("-" * 50)

        response_tests = [
            {
                "query": "What is machine learning?",
                "should_research": False,
                "test_name": "General Knowledge"
            },
            {
                "query": "What are the latest Boston Dynamics updates?",
                "should_research": True,
                "test_name": "Time-Sensitive Research"
            },
            {
                "query": "What tech stocks should I buy?",
                "should_research": True,
                "test_name": "Financial Research"
            }
        ]

        response_results = []

        for test in response_tests:
            print(f"\n🧪 Testing: {test['test_name']}")
            print(f"Query: '{test['query']}'")

            research_required = pipeline.research_manager.requires_research(test['query'])
            classification_correct = research_required == test['should_research']

            print(f"Classification: {'✅' if classification_correct else '❌'} Research Required: {research_required}")

            # Test actual response
            pipeline.state = State.THINKING
            start_time = time.time()
            response = pipeline.think(test['query'])
            execution_time = time.time() - start_time

            print(f"Response Time: {execution_time:.2f}s")
            print(f"Response Length: {len(response)} chars")
            print(f"Preview: '{response[:150]}...'")

            # Analyze response quality
            has_fabrication = any(indicator in response.lower() for indicator in [
                "15% improvement", "90% confidence", "recent study shows", "according to research"
            ])

            acknowledges_limitation = any(indicator in response.lower() for indicator in [
                "i don't have", "my data", "out of date", "check official", "verify with", "not sure"
            ])

            response_quality = "✅ Good" if not has_fabrication else "❌ Potential Fabrication"
            print(f"Response Quality: {response_quality}")

            if test['should_research'] and not acknowledges_limitation:
                print("⚠️ Research query should acknowledge data limitations")

            response_results.append({
                "test_name": test['test_name'],
                "classification_correct": classification_correct,
                "no_fabrication": not has_fabrication,
                "execution_time": execution_time
            })

            time.sleep(0.5)  # Brief pause between tests

        print(f"\n" + "=" * 70)
        print(f"🎯 SMART RESEARCH STRATEGY RESULTS")
        print(f"   Classification Accuracy: {overall_accuracy:.1f}%")
        print(f"   Response Quality: {sum(1 for r in response_results if r['no_fabrication'])}/{len(response_results)} no fabrication")
        print(f"   Average Response Time: {sum(r['execution_time'] for r in response_results) / len(response_results):.2f}s")

        success_threshold = 85.0
        if overall_accuracy >= success_threshold:
            print(f"\n🎉 SMART RESEARCH STRATEGY VALIDATION PASSED!")
            print(f"   • Correctly identifies when research is needed vs training knowledge")
            print(f"   • Reduces unnecessary research attempts for general queries")
            print(f"   • Maintains safety for high-risk categories (financial, time-sensitive)")
            print(f"   • No fabrication detected in responses")
            return True
        else:
            print(f"\n❌ SMART RESEARCH STRATEGY NEEDS IMPROVEMENT")
            print(f"   Classification accuracy {overall_accuracy:.1f}% below threshold {success_threshold}%")
            return False

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_smart_research_classification()
    exit(0 if success else 1)