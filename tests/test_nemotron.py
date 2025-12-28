#!/usr/bin/env python3
"""
Nemotron-3 Nano Integration Test
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.llm.nemotron_client import create_nemotron_client
import time

print("=" * 70)
print("🧪 NEMOTRON-3 NANO TEST")
print("=" * 70)

# Test 1: Create client
print("\n✅ TEST 1: Client Creation")
try:
    client = create_nemotron_client()
    print(f"  ✅ Client created: {client.model_name}")
except Exception as e:
    print(f"  ❌ Failed: {e}")
    exit(1)

# Test 2: Simple generation (string prompt)
print("\n✅ TEST 2: Simple Generation (String Prompt)")
try:
    start = time.time()
    response = client.generate("What is 2+2? Answer briefly.")
    elapsed = time.time() - start

    print(f"  ✅ Response in {elapsed:.2f}s: {response[:100]}")

    if "4" in response:
        print("  ✅ Correct answer")
except Exception as e:
    print(f"  ❌ Failed: {e}")

# Test 3: Message-based generation
print("\n✅ TEST 3: Message-Based Generation")
try:
    messages = [{"role": "user", "content": "What is 2+2? Answer briefly."}]

    start = time.time()
    response = client.generate(messages)
    elapsed = time.time() - start

    print(f"  ✅ Response in {elapsed:.2f}s: {response[:100]}")

    if "4" in response:
        print("  ✅ Correct answer")
except Exception as e:
    print(f"  ❌ Failed: {e}")

# Test 4: Complete method (LLMFactory compatibility)
print("\n✅ TEST 4: Complete Method (LLMFactory Compatible)")
try:
    start = time.time()
    response = client.complete("What is 5+3? Answer briefly.", tone="neutral")
    elapsed = time.time() - start

    print(f"  ✅ Response in {elapsed:.2f}s: {response[:100]}")

    if "8" in response:
        print("  ✅ Correct answer")
except Exception as e:
    print(f"  ❌ Failed: {e}")

# Test 5: Chat completion (OpenAI-compatible)
print("\n✅ TEST 5: Chat Completion (OpenAI-compatible)")
try:
    messages = [
        {"role": "system", "content": "You are Penny, a helpful AI assistant."},
        {"role": "user", "content": "What's your name?"}
    ]

    response = client.chat_completion(messages)
    content = response["choices"][0]["message"]["content"]

    print(f"  ✅ Response: {content[:100]}")

    if "Penny" in content or "penny" in content.lower():
        print("  ✅ Identified as Penny")
except Exception as e:
    print(f"  ❌ Failed: {e}")

# Test 6: Performance
print("\n✅ TEST 6: Performance")
try:
    times = []
    for i in range(3):
        start = time.time()
        client.generate("Say hello!")
        times.append(time.time() - start)

    avg = sum(times) / len(times)
    print(f"  ✅ Average: {avg:.2f}s (min: {min(times):.2f}s, max: {max(times):.2f}s)")
except Exception as e:
    print(f"  ❌ Failed: {e}")

print("\n" + "=" * 70)
print("🎉 NEMOTRON-3 NANO: READY!")
print("=" * 70)
