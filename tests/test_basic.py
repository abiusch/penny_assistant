#!/usr/bin/env python3
"""Simple test of the pipeline without keyboard monitoring."""

from core.llm_router import get_llm
from core.pipeline import run_once

print("Testing Penny Assistant pipeline...")

# Test 1: LLM
llm = get_llm()
response = llm.generate("Hello") if hasattr(llm, 'generate') else llm.complete("Hello")
print(f"LLM Response: {response}")

# Test 2: Full pipeline
result = run_once()
print(f"Pipeline Result: {result}")

print("\n✅ Basic pipeline working! Next: fix macOS accessibility for keyboard input.")
