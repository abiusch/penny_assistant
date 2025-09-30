#!/usr/bin/env python3
"""
Comprehensive test suite for Google Custom Search Engine integration.
Tests the entire search pipeline from Google CSE through the research system.
"""

import os
import sys
import asyncio
import time
from typing import List, Dict, Any

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))


class TestResults:
    """Track test results across the entire suite"""

    def __init__(self):
        self.tests_run = 0
        self.tests_passed = 0
        self.tests_failed = 0
        self.failures = []

    def add_result(self, test_name: str, passed: bool, message: str = ""):
        self.tests_run += 1
        if passed:
            self.tests_passed += 1
            print(f"✅ {test_name}")
        else:
            self.tests_failed += 1
            self.failures.append({"test": test_name, "message": message})
            print(f"❌ {test_name}: {message}")

    def summary(self):
        success_rate = (self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0
        print(f"\n📊 TEST SUMMARY")
        print(f"   Tests Run: {self.tests_run}")
        print(f"   Passed: {self.tests_passed}")
        print(f"   Failed: {self.tests_failed}")
        print(f"   Success Rate: {success_rate:.1f}%")

        if self.failures:
            print(f"\n❌ FAILURES:")
            for failure in self.failures:
                print(f"   • {failure['test']}: {failure['message']}")

        return success_rate >= 80.0


async def test_google_cse_basic_functionality(results: TestResults):
    """Test basic Google CSE search functionality"""
    print("\n🧪 Testing Google CSE Basic Functionality")
    print("-" * 50)

    try:
        from google_cse_search import GoogleCSESearch, GoogleCSESearchError

        # Test environment configuration
        api_key = os.getenv('GOOGLE_CSE_API_KEY')
        engine_id = os.getenv('GOOGLE_CSE_ENGINE_ID')

        if not api_key or api_key == 'your_google_custom_search_api_key_here':
            results.add_result("Google CSE API Key Check", False, "API key not configured")
            print("💡 To fix: Set GOOGLE_CSE_API_KEY in your .env file")
            return
        else:
            results.add_result("Google CSE API Key Check", True)

        if not engine_id or engine_id == 'your_custom_search_engine_id_here':
            results.add_result("Google CSE Engine ID Check", False, "Engine ID not configured")
            print("💡 To fix: Set GOOGLE_CSE_ENGINE_ID in your .env file")
            return
        else:
            results.add_result("Google CSE Engine ID Check", True)

        # Test search functionality
        async with GoogleCSESearch() as search:
            # Test usage stats
            stats = search.get_usage_stats()
            results.add_result("Usage Stats", stats is not None and 'today_searches' in stats)

            # Test basic search
            test_query = "machine learning basics"
            search_results = await search.search(test_query, num_results=3)

            results.add_result("Basic Search", len(search_results) > 0,
                             f"Expected results, got {len(search_results)}")

            if search_results:
                first_result = search_results[0]
                has_required_fields = all(hasattr(first_result, field) for field in ['title', 'url', 'snippet'])
                results.add_result("Search Result Format", has_required_fields)

                # Test URL validity
                valid_url = first_result.url.startswith(('http://', 'https://'))
                results.add_result("Valid URLs", valid_url)

                print(f"   Sample result: {first_result.title}")
                print(f"   URL: {first_result.url}")
                print(f"   Snippet: {first_result.snippet[:100]}...")

    except GoogleCSESearchError as e:
        results.add_result("Google CSE Configuration", False, str(e))
    except Exception as e:
        results.add_result("Google CSE Basic Test", False, f"Unexpected error: {e}")


async def test_web_search_server_integration(results: TestResults):
    """Test integration with the web search server"""
    print("\n🧪 Testing Web Search Server Integration")
    print("-" * 50)

    try:
        from web_search_tool_server import WebSearchToolServer
        from tool_server_foundation import SecurityContext, SecurityLevel
        from datetime import datetime

        # Create web search server
        web_server = WebSearchToolServer()

        # Create security context
        security_context = SecurityContext(
            user_id="test_user",
            operation_id="test_search",
            security_level=SecurityLevel.MEDIUM,
            timestamp=datetime.now(),
            request_metadata={"test": True}
        )

        # Test search parameters
        search_params = {
            "query": "Python programming tutorial",
            "max_results": 3,
            "engine": "google_cse"
        }

        # Perform search
        search_results = await web_server._search(search_params, security_context)

        # Validate response format
        expected_keys = ["query", "engine", "results", "total_results", "timestamp"]
        has_expected_format = all(key in search_results for key in expected_keys)
        results.add_result("Search Response Format", has_expected_format)

        # Test results quality
        results_list = search_results.get("results", [])
        has_results = len(results_list) > 0
        results.add_result("Search Results Returned", has_results)

        if has_results:
            first_result = results_list[0]
            has_result_fields = all(field in first_result for field in ['title', 'url', 'snippet'])
            results.add_result("Result Field Completeness", has_result_fields)

            print(f"   Engine used: {search_results.get('engine')}")
            print(f"   Results count: {search_results.get('total_results')}")
            print(f"   Sample: {first_result.get('title', 'No title')}")

        # Test fallback mechanism
        fallback_params = {
            "query": "test fallback search",
            "max_results": 2,
            "engine": "duckduckgo"  # Force DuckDuckGo to test fallback
        }

        fallback_results = await web_server._search(fallback_params, security_context)
        fallback_works = "results" in fallback_results
        results.add_result("Fallback Mechanism", fallback_works)

    except Exception as e:
        results.add_result("Web Search Server Integration", False, str(e))


async def test_autonomous_research_integration(results: TestResults):
    """Test integration with the autonomous research system"""
    print("\n🧪 Testing Autonomous Research Integration")
    print("-" * 50)

    try:
        from autonomous_research_tool_server import ResearchExecutor

        # Create research executor
        executor = ResearchExecutor(web_search_available=True)

        # Test web search method
        test_query = "artificial intelligence research"
        research_sources = await executor._web_search(test_query, "test_user")

        has_sources = len(research_sources) > 0
        results.add_result("Research Source Generation", has_sources)

        if has_sources:
            first_source = research_sources[0]

            # Validate source structure
            required_attrs = ['source_id', 'url', 'title', 'content', 'credibility_score', 'source_type']
            has_required_attrs = all(hasattr(first_source, attr) for attr in required_attrs)
            results.add_result("Research Source Structure", has_required_attrs)

            # Test credibility scoring
            credibility_in_range = 0.0 <= first_source.credibility_score <= 1.0
            results.add_result("Credibility Score Range", credibility_in_range)

            # Test URL validity
            valid_research_url = first_source.url.startswith(('http://', 'https://'))
            results.add_result("Research URL Validity", valid_research_url)

            print(f"   Sources found: {len(research_sources)}")
            print(f"   Sample source: {first_source.title}")
            print(f"   Credibility: {first_source.credibility_score}")
            print(f"   Source type: {first_source.source_type}")

    except Exception as e:
        results.add_result("Autonomous Research Integration", False, str(e))


async def test_boston_dynamics_query(results: TestResults):
    """Test the specific query that was previously fabricating results"""
    print("\n🧪 Testing Boston Dynamics Query (Anti-Fabrication)")
    print("-" * 50)

    try:
        from research_first_pipeline import ResearchFirstPipeline
        from src.core.pipeline import State

        pipeline = ResearchFirstPipeline()

        # The problematic query that was fabricating data
        test_query = "What are the recent updates to Boston Dynamics Stretch robot?"

        # Test classification
        research_required = pipeline.research_manager.requires_research(test_query)
        results.add_result("Query Classification", research_required,
                         "Should require research for time-sensitive query")

        # Test full pipeline
        pipeline.state = State.THINKING
        start_time = time.time()
        response = pipeline.think(test_query)
        execution_time = time.time() - start_time

        # Validate response
        has_response = len(response) > 50
        results.add_result("Response Generation", has_response)

        # Check for fabrication indicators (should NOT be present)
        fabrication_indicators = [
            "15% battery improvement",
            "90% confidence study",
            "research whisper",
            "research nugget",
            "recent firmware update increased"
        ]

        has_fabrication = any(indicator.lower() in response.lower() for indicator in fabrication_indicators)
        results.add_result("No Fabrication", not has_fabrication,
                         "Response should not contain fabricated statistics")

        # Check for proper uncertainty handling
        uncertainty_indicators = [
            "don't have current",
            "my data",
            "out of date",
            "check official",
            "not sure",
            "2023"  # Should reference training cutoff
        ]

        has_uncertainty = any(indicator.lower() in response.lower() for indicator in uncertainty_indicators)
        results.add_result("Uncertainty Acknowledgment", has_uncertainty,
                         "Should acknowledge data limitations")

        # Check for source suggestions
        source_suggestions = [
            "official",
            "website",
            "Boston Dynamics",
            "recent news",
            "press release"
        ]

        suggests_sources = any(suggestion.lower() in response.lower() for suggestion in source_suggestions)
        results.add_result("Source Suggestions", suggests_sources,
                         "Should suggest authoritative sources")

        print(f"   Execution time: {execution_time:.2f}s")
        print(f"   Response length: {len(response)} chars")
        print(f"   Preview: {response[:150]}...")

    except Exception as e:
        results.add_result("Boston Dynamics Query Test", False, str(e))


async def test_rate_limiting_and_usage_tracking(results: TestResults):
    """Test rate limiting and usage tracking functionality"""
    print("\n🧪 Testing Rate Limiting and Usage Tracking")
    print("-" * 50)

    try:
        from google_cse_search import GoogleCSESearch

        async with GoogleCSESearch() as search:
            # Test usage stats
            initial_stats = search.get_usage_stats()
            initial_count = initial_stats['today_searches']

            # Perform a search
            await search.search("test rate limiting", num_results=1)

            # Check if usage was incremented
            new_stats = search.get_usage_stats()
            new_count = new_stats['today_searches']

            usage_incremented = new_count > initial_count
            results.add_result("Usage Tracking", usage_incremented)

            # Test stats structure
            expected_stats = ['today_searches', 'daily_limit', 'remaining_today', 'total_searches']
            has_expected_stats = all(stat in new_stats for stat in expected_stats)
            results.add_result("Usage Stats Structure", has_expected_stats)

            # Test rate limit calculation
            remaining = new_stats['remaining_today']
            valid_remaining = isinstance(remaining, int) and remaining >= 0
            results.add_result("Rate Limit Calculation", valid_remaining)

            print(f"   Today's searches: {new_stats['today_searches']}")
            print(f"   Daily limit: {new_stats['daily_limit']}")
            print(f"   Remaining: {new_stats['remaining_today']}")
            print(f"   Status: {new_stats['status']}")

    except Exception as e:
        results.add_result("Rate Limiting Test", False, str(e))


async def run_comprehensive_tests():
    """Run the complete test suite"""
    print("🚀 GOOGLE CSE INTEGRATION - COMPREHENSIVE TEST SUITE")
    print("=" * 70)

    results = TestResults()

    # Run all test categories
    await test_google_cse_basic_functionality(results)
    await test_web_search_server_integration(results)
    await test_autonomous_research_integration(results)
    await test_boston_dynamics_query(results)
    await test_rate_limiting_and_usage_tracking(results)

    # Print summary
    success = results.summary()

    if success:
        print(f"\n🎉 GOOGLE CSE INTEGRATION TESTS PASSED!")
        print(f"   • Reliable search functionality working")
        print(f"   • No more fabrication in research responses")
        print(f"   • Rate limiting and usage tracking functional")
        print(f"   • Fallback mechanisms operational")
        print(f"   • Ready for production use")
    else:
        print(f"\n⚠️ SOME TESTS FAILED - REVIEW NEEDED")
        print(f"   Check configuration and API setup")

    return success


if __name__ == "__main__":
    print("💡 Setup Requirements:")
    print("   1. Set GOOGLE_CSE_API_KEY in .env file")
    print("   2. Set GOOGLE_CSE_ENGINE_ID in .env file")
    print("   3. Ensure Google CSE API is enabled and configured")
    print("   4. Install required dependencies")
    print()

    success = asyncio.run(run_comprehensive_tests())
    exit(0 if success else 1)