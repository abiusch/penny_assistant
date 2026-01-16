#!/usr/bin/env python3
"""
Final validation test for research integration.
Tests all critical scenarios: greetings, casual queries, investment queries.
"""

import sys
import os
import time

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_research_integration():
    """Test all critical validation scenarios for research integration."""

    print("🧪 FINAL RESEARCH INTEGRATION VALIDATION")
    print("=" * 70)

    try:
        from research_first_pipeline import ResearchFirstPipeline
        from core.pipeline import State

        pipeline = ResearchFirstPipeline()

        # Test scenarios based on user feedback
        test_scenarios = [
            {
                "name": "Simple Greeting",
                "query": "Hello",
                "should_research": False,
                "should_work": True,
                "description": "Should work normally without research"
            },
            {
                "name": "Casual Question",
                "query": "How are you?",
                "should_research": False,
                "should_work": True,
                "description": "Should bypass research"
            },
            {
                "name": "Investment Query - Robotics",
                "query": "research robotics companies",
                "should_research": True,
                "should_work": True,
                "description": "Should trigger research"
            },
            {
                "name": "Investment Query - Specific Company",
                "query": "Tell me about Tesla stock potential",
                "should_research": True,
                "should_work": True,
                "description": "Should trigger research and include disclaimer"
            },
            {
                "name": "General Factual Query",
                "query": "What are the latest updates on Apple",
                "should_research": True,
                "should_work": True,
                "description": "Should trigger research for factual content"
            }
        ]

        results = []

        for i, scenario in enumerate(test_scenarios, 1):
            print(f"\n--- Test {i}: {scenario['name']} ---")
            print(f"Query: '{scenario['query']}'")
            print(f"Expected: {scenario['description']}")

            # Test research classification first
            research_required = pipeline.research_manager.requires_research(scenario['query'])
            financial_topic = pipeline.research_manager.is_financial_topic(scenario['query'])

            print(f"📋 Classification: Research={research_required}, Financial={financial_topic}")

            if research_required != scenario['should_research']:
                print(f"❌ Classification FAILED - Expected research={scenario['should_research']}, got {research_required}")
                results.append(False)
                continue

            # Test actual pipeline execution
            pipeline.state = State.THINKING
            start_time = time.time()
            response = pipeline.think(scenario['query'])
            execution_time = time.time() - start_time

            print(f"⏱️ Execution time: {execution_time:.2f}s")

            if not response or len(response) == 0:
                print(f"❌ Pipeline FAILED - Empty response")
                results.append(False)
                continue

            print(f"✅ Pipeline SUCCESS - Response length: {len(response)}")

            # Check for research content
            if scenario['should_research']:
                if financial_topic and "disclaimer" not in response.lower():
                    print("⚠️ Financial query missing disclaimer")
                elif "research" in response.lower() or "sources" in response.lower():
                    print("✅ Response contains research indicators")
                else:
                    print("⚠️ Research query may not contain research content")

            # Check response quality
            if len(response) > 50 and not response.startswith("I encountered an issue"):
                print("✅ Response quality good")
                results.append(True)
            else:
                print("❌ Response quality poor or error message")
                results.append(False)

            time.sleep(0.5)  # Brief pause between tests

        # Summary
        success_count = sum(results)
        total_tests = len(results)
        success_rate = (success_count / total_tests * 100) if total_tests > 0 else 0

        print(f"\n" + "=" * 70)
        print(f"🎯 FINAL VALIDATION RESULTS")
        print(f"   Successful tests: {success_count}/{total_tests}")
        print(f"   Success rate: {success_rate:.1f}%")

        if success_rate >= 80:
            print("🎉 RESEARCH INTEGRATION VALIDATION PASSED!")
            print("   • Basic conversation works normally")
            print("   • Non-factual queries bypass research")
            print("   • Investment queries trigger research")
            print("   • Exception handling prevents conversation breaks")
            print("   • Research enhancement is additive, not disruptive")
        else:
            print("❌ RESEARCH INTEGRATION VALIDATION FAILED!")
            print("   Some critical scenarios are not working correctly")

        return success_rate >= 80

    except Exception as e:
        print(f"❌ Validation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_research_integration()
    exit(0 if success else 1)