#!/usr/bin/env python3
"""
Direct Tool Safety Test - Bypassing __init__.py
"""

import sys
sys.path.insert(0, '/Users/CJ/Desktop/penny_assistant')

# Import directly from the module file
import importlib.util
spec = importlib.util.spec_from_file_location(
    "tool_safety", 
    "/Users/CJ/Desktop/penny_assistant/src/tools/tool_safety.py"
)
tool_safety = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tool_safety)

InputValidator = tool_safety.InputValidator
RateLimiter = tool_safety.RateLimiter
ToolValidationError = tool_safety.ToolValidationError

print("=" * 70)
print("🧪 TOOL SAFETY VALIDATION TEST")
print("=" * 70)

# Test 1: Input Validation
print("\n✅ TEST 1: Input Validation")
validator = InputValidator()

# Valid inputs
tests_passed = 0
tests_total = 0

# Web search - valid
tests_total += 1
try:
    validator.validate_web_search({"query": "Python programming"})
    print("  ✅ Valid web search query accepted")
    tests_passed += 1
except:
    print("  ❌ Valid query rejected")

# Web search - XSS
tests_total += 1
try:
    validator.validate_web_search({"query": "<script>alert('xss')</script>"})
    print("  ❌ XSS not blocked")
except ToolValidationError:
    print("  ✅ XSS attack blocked")
    tests_passed += 1

# Math - valid
tests_total += 1
try:
    validator.validate_math_calc({"expression": "2 + 2"})
    print("  ✅ Valid math expression accepted")
    tests_passed += 1
except:
    print("  ❌ Valid math rejected")

# Math - import
tests_total += 1
try:
    validator.validate_math_calc({"expression": "import os"})
    print("  ❌ Import not blocked")
except ToolValidationError:
    print("  ✅ Import attempt blocked")
    tests_passed += 1

# Math - exec
tests_total += 1
try:
    validator.validate_math_calc({"expression": "exec('code')"})
    print("  ❌ Exec not blocked")
except ToolValidationError:
    print("  ✅ Exec attempt blocked")
    tests_passed += 1

# Test 2: Rate Limiting
print("\n✅ TEST 2: Rate Limiting")
limiter = RateLimiter(max_calls=3, window_seconds=60)

# First 3 calls should succeed
for i in range(3):
    tests_total += 1
    if limiter.check_rate_limit("test_tool"):
        print(f"  ✅ Call {i+1}: Allowed")
        tests_passed += 1
    else:
        print(f"  ❌ Call {i+1}: Incorrectly blocked")

# 4th call should fail
tests_total += 1
if not limiter.check_rate_limit("test_tool"):
    print("  ✅ Call 4: Correctly rate limited")
    tests_passed += 1
else:
    print("  ❌ Call 4: Should have been blocked")

# Summary
print("\n" + "=" * 70)
print("📊 TEST SUMMARY")
print("=" * 70)
print(f"\nTotal tests:  {tests_total}")
print(f"Passed:       {tests_passed} ✅")
print(f"Failed:       {tests_total - tests_passed} {'❌' if tests_passed < tests_total else '✅'}")
print(f"Success rate: {(tests_passed/tests_total)*100:.1f}%")

if tests_passed == tests_total:
    print("\n🎉 ALL TOOL SAFETY TESTS PASSED!")
    print("   - Input validation: ✅")
    print("   - XSS prevention: ✅")
    print("   - Injection prevention: ✅")
    print("   - Rate limiting: ✅")
    print("\n   Week 4 Fix #4: VERIFIED ✅")

print("=" * 70)
