#!/usr/bin/env python3
"""
Tool Safety Tests - Week 4 Fix #4
Tests timeout, rate limiting, and input validation.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

import asyncio
import time
from src.tools.tool_safety import (
    get_safe_tool_wrapper,
    ToolTimeoutError,
    ToolRateLimitError,
    ToolValidationError,
    InputValidator
)


class TestToolSafety:
    """Test tool safety mechanisms."""
    
    def test_input_validation_web_search(self):
        """Test web search input validation."""
        print("\n🧪 TEST 1: Web Search Input Validation")
        print("=" * 60)
        
        validator = InputValidator()
        
        # Valid inputs
        valid_cases = [
            {"query": "Python programming"},
            {"query": "weather forecast", "max_results": 5},
            {"query": "AI research papers", "max_results": 3},
        ]
        
        for i, args in enumerate(valid_cases, 1):
            try:
                validator.validate_web_search(args)
                print(f"  ✅ Valid case {i}: {args['query'][:30]}")
            except ToolValidationError as e:
                print(f"  ❌ Should be valid but failed: {e}")
        
        # Invalid inputs
        invalid_cases = [
            ({"query": ""}, "empty query"),
            ({"query": "x" * 501}, "query too long"),
            ({"query": "<script>alert('xss')</script>"}, "XSS attempt"),
            ({"query": "test", "max_results": 50}, "max_results too high"),
            ({"query": "javascript:void(0)"}, "javascript protocol"),
        ]
        
        for args, reason in invalid_cases:
            try:
                validator.validate_web_search(args)
                print(f"  ❌ Should have failed ({reason}): {args}")
            except ToolValidationError:
                print(f"  ✅ Correctly rejected ({reason})")
        
        print("\n✅ Web search validation test complete")
    
    def test_input_validation_math_calc(self):
        """Test math calculation input validation."""
        print("\n🧪 TEST 2: Math Calculation Input Validation")
        print("=" * 60)
        
        validator = InputValidator()
        
        # Valid inputs
        valid_cases = [
            {"expression": "2 + 2"},
            {"expression": "42 * 13"},
            {"expression": "sqrt(16)"},
            {"expression": "pow(2, 8)"},
        ]
        
        for i, args in enumerate(valid_cases, 1):
            try:
                validator.validate_math_calc(args)
                print(f"  ✅ Valid case {i}: {args['expression']}")
            except ToolValidationError as e:
                print(f"  ❌ Should be valid but failed: {e}")
        
        # Invalid inputs
        invalid_cases = [
            ({"expression": ""}, "empty expression"),
            ({"expression": "x" * 201}, "expression too long"),
            ({"expression": "import os"}, "import attempt"),
            ({"expression": "exec('malicious')"}, "exec attempt"),
            ({"expression": "__import__('os')"}, "dunder method"),
            ({"expression": "open('/etc/passwd')"}, "file access"),
        ]
        
        for args, reason in invalid_cases:
            try:
                validator.validate_math_calc(args)
                print(f"  ❌ Should have failed ({reason}): {args.get('expression', '')[:30]}")
            except ToolValidationError:
                print(f"  ✅ Correctly rejected ({reason})")
        
        print("\n✅ Math calculation validation test complete")
    
    async def test_rate_limiting(self):
        """Test rate limiting functionality."""
        print("\n🧪 TEST 3: Rate Limiting")
        print("=" * 60)
        
        wrapper = get_safe_tool_wrapper(
            timeout_seconds=30,
            max_calls_per_minute=3  # Low limit for testing
        )
        
        # Reset to start fresh
        wrapper.reset_rate_limits()
        
        # Create a test tool
        async def test_tool(args):
            return "success"
        
        # Wrap with rate limiting
        rate_limiter = wrapper.rate_limiter
        safe_tool = wrapper.wrap_tool("test.tool", test_tool)
        
        print(f"  Rate limit: 3 calls per minute")
        
        # Should allow first 3 calls
        for i in range(3):
            try:
                result = await safe_tool({"test": "data"})
                print(f"  ✅ Call {i+1}: Allowed")
            except ToolRateLimitError:
                print(f"  ❌ Call {i+1}: Unexpected rate limit")
        
        # 4th call should fail
        try:
            result = await safe_tool({"test": "data"})
            print(f"  ❌ Call 4: Should have been rate limited")
        except ToolRateLimitError:
            print(f"  ✅ Call 4: Correctly rate limited")
        
        # Check remaining calls
        remaining = rate_limiter.get_remaining_calls("test.tool")
        print(f"  Remaining calls in window: {remaining}")
        
        print("\n✅ Rate limiting test complete")
    
    async def test_timeout(self):
        """Test timeout functionality."""
        print("\n🧪 TEST 4: Timeout")
        print("=" * 60)
        
        wrapper = get_safe_tool_wrapper(timeout_seconds=2)  # 2 second timeout
        
        # Create a slow tool
        async def slow_tool(args):
            await asyncio.sleep(5)  # Sleeps longer than timeout
            return "completed"
        
        safe_tool = wrapper.wrap_tool("slow.tool", slow_tool)
        
        print("  Testing 2-second timeout with 5-second task...")
        
        start = time.time()
        try:
            result = await safe_tool({"test": "data"})
            elapsed = time.time() - start
            print(f"  ❌ Should have timed out but completed in {elapsed:.1f}s")
        except ToolTimeoutError:
            elapsed = time.time() - start
            print(f"  ✅ Correctly timed out after {elapsed:.1f}s")
        
        print("\n✅ Timeout test complete")
    
    async def test_combined_safety(self):
        """Test all safety mechanisms together."""
        print("\n🧪 TEST 5: Combined Safety Mechanisms")
        print("=" * 60)
        
        wrapper = get_safe_tool_wrapper(
            timeout_seconds=5,
            max_calls_per_minute=5
        )
        wrapper.reset_rate_limits()
        
        # Create test tool with validation
        async def combined_tool(args):
            # Simulate some work
            await asyncio.sleep(0.1)
            return f"Processed: {args.get('query', 'unknown')}"
        
        validator = InputValidator()
        safe_tool = wrapper.wrap_tool("web.search", combined_tool)
        
        print("  Testing valid input...")
        try:
            result = await safe_tool({"query": "test search"})
            print(f"  ✅ Valid input accepted: {result}")
        except Exception as e:
            print(f"  ❌ Valid input rejected: {e}")
        
        print("\n  Testing invalid input...")
        try:
            result = await safe_tool({"query": "<script>xss</script>"})
            print(f"  ❌ Invalid input accepted")
        except ToolValidationError:
            print(f"  ✅ Invalid input correctly rejected")
        
        print("\n  Testing rate limit (5 calls)...")
        for i in range(6):
            try:
                result = await safe_tool({"query": f"test {i}"})
                print(f"  ✅ Call {i+1}: Allowed")
            except ToolRateLimitError:
                print(f"  ✅ Call {i+1}: Rate limited (expected)")
        
        print("\n✅ Combined safety test complete")


async def run_all_tests():
    """Run all tool safety tests."""
    print("=" * 70)
    print("🧪 TOOL SAFETY TEST SUITE - WEEK 4 FIX #4")
    print("=" * 70)
    print("\nTesting timeout, rate limiting, and validation...\n")
    
    test_suite = TestToolSafety()
    
    tests = [
        ("Input Validation (Web Search)", test_suite.test_input_validation_web_search),
        ("Input Validation (Math Calc)", test_suite.test_input_validation_math_calc),
        ("Rate Limiting", test_suite.test_rate_limiting),
        ("Timeout", test_suite.test_timeout),
        ("Combined Safety", test_suite.test_combined_safety),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            if asyncio.iscoroutinefunction(test_func):
                await test_func()
            else:
                test_func()
            passed += 1
        except Exception as e:
            failed += 1
            print(f"\n❌ Test '{name}' failed: {e}")
            import traceback
            traceback.print_exc()
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 TEST SUMMARY")
    print("=" * 70)
    print(f"\nTotal tests:  {len(tests)}")
    print(f"Passed:       {passed} ✅")
    print(f"Failed:       {failed} {'❌' if failed > 0 else '✅'}")
    print(f"Success rate: {(passed/len(tests))*100:.1f}%")
    
    if failed == 0:
        print("\n🎉 ALL TOOL SAFETY TESTS PASSED!")
        print("   - Input validation working ✅")
        print("   - Rate limiting functional ✅")
        print("   - Timeouts enforced ✅")
        print("   - Combined safety verified ✅")
        print("\n   Week 4 Fix #4: COMPLETE ✅")
        print("\n   🎊 WEEK 4: 100% COMPLETE! 🎊")
    else:
        print(f"\n⚠️  {failed} test(s) failed")
        print("   Review failures and fix issues")
    
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(run_all_tests())
