#!/usr/bin/env python3
"""
Debug pipeline calls to see what's happening.
"""

import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def debug_pipeline_calls():
    """Debug what happens when we call the pipeline from different contexts."""

    print("🔍 Debug Pipeline Calls")
    print("=" * 50)

    try:
        from research_first_pipeline import ResearchFirstPipeline
        from core.pipeline import State

        print("1️⃣ Creating pipeline...")
        pipeline = ResearchFirstPipeline()

        print("\n2️⃣ Testing direct call from main method...")
        pipeline.state = State.THINKING
        print(f"Pipeline state: {pipeline.state}")
        print("Calling think method...")

        # Call with debug output
        result = pipeline.think("Hello")
        print(f"Result: '{result}'")
        print(f"Result length: {len(result) if result else 0}")
        print(f"Result type: {type(result)}")

        if not result:
            print("❌ Empty result - checking for exceptions...")

        print("\n3️⃣ Testing research query...")
        pipeline.state = State.THINKING
        result2 = pipeline.think("What are emerging robotics companies to invest in?")
        print(f"Research result: '{result2[:100] if result2 else 'EMPTY'}...'")

    except Exception as e:
        print(f"❌ Debug test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_pipeline_calls()