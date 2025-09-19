#!/usr/bin/env python3
"""
Demo script for Penny's Reasoning Transparency System
Shows how the system makes decisions visible and explainable
"""

import json
from integrated_reasoning_system import create_integrated_reasoning_system


def demo_reasoning_transparency():
    """Demonstrate the reasoning transparency system."""

    print("🤖 PENNY'S REASONING TRANSPARENCY SYSTEM DEMO")
    print("=" * 60)
    print()
    print("This demo shows how Penny's decision-making process becomes")
    print("visible and explainable through the reasoning transparency system.")
    print()

    # Create the integrated reasoning system
    reasoning_system = create_integrated_reasoning_system(debug_mode=True)

    # Demo scenarios
    scenarios = [
        {
            "input": "I'm really frustrated with this bug but determined to fix it",
            "description": "Programming frustration with determination"
        },
        {
            "input": "I think you might prefer minimal sass here, but let me know if I'm wrong",
            "description": "Uncertainty expression with preference"
        },
        {
            "input": "Josh is being weird about the project deadline",
            "description": "Social context with friend mention"
        },
        {
            "input": "Super excited about the new feature launch!",
            "description": "High positive emotion"
        }
    ]

    for i, scenario in enumerate(scenarios, 1):
        print(f"\n🎬 SCENARIO {i}: {scenario['description']}")
        print("-" * 60)
        print(f"💬 User says: \"{scenario['input']}\"")
        print()

        # Process the input
        result = reasoning_system.process_user_input(scenario['input'])

        # Show the decision
        print("🧠 PENNY'S DECISION PROCESS:")
        print(f"   └─ Detected emotion: {result.context_analysis.emotion_profile.primary_emotion}")
        print(f"      ({result.context_analysis.emotion_profile.intensity.value} intensity)")
        print(f"   └─ Topic: {result.context_analysis.topic}")
        print(f"   └─ Social context: {result.context_analysis.social_context}")
        print(f"   └─ Retrieved memories: {len(result.retrieved_memories)}")
        print(f"   └─ Chosen response style: {result.final_response_style}")
        print(f"   └─ Overall confidence: {result.overall_confidence:.2f}")
        print()

        # Show reasoning explanation
        print("💭 REASONING EXPLANATION:")
        print(f"   {result.reasoning_explanation}")
        print()

        # Show confidence expression
        print("🎯 CONFIDENCE EXPRESSION:")
        print(f"   \"{result.confidence_expression}\"")
        print()

        # Show uncertainty handling
        if result.overall_confidence < 0.6:
            print("❓ UNCERTAINTY HANDLING:")
            print("   ├─ Low confidence detected")
            print("   ├─ Expressing uncertainty appropriately")
            print("   └─ Ready to ask for clarification")
            print()

        # Show complete explanation
        explanation = reasoning_system.explain_decision(result)
        print("📋 COMPLETE EXPLANATION FOR USER:")
        print(explanation)

        print("\n" + "="*60)

    print()
    print("✨ KEY FEATURES DEMONSTRATED:")
    print()
    print("1. 🔍 REASONING CHAIN VISIBILITY:")
    print("   - Shows each step: context detection → memory retrieval → style decision")
    print("   - Displays confidence for each reasoning step")
    print("   - Explains the logic behind each decision")
    print()
    print("2. 🎯 CONFIDENCE INDICATORS:")
    print("   - Expresses uncertainty appropriately")
    print("   - Adjusts language based on confidence level")
    print("   - Offers alternatives when uncertain")
    print()
    print("3. 🧠 CONTEXTUAL MEMORY RETRIEVAL:")
    print("   - Finds relevant past interactions")
    print("   - Uses patterns to inform current decisions")
    print("   - Shows how memory influences reasoning")
    print()
    print("4. 🤝 SOCIAL BOUNDARY RECOGNITION:")
    print("   - Adjusts communication style based on context")
    print("   - Recognizes different social situations")
    print("   - Adapts formality and approach accordingly")
    print()
    print("🚀 This system makes Penny's AI reasoning transparent,")
    print("   helping users understand and trust the decision-making process!")


def demo_confidence_calibration():
    """Demonstrate confidence calibration features."""

    print("\n🎯 CONFIDENCE CALIBRATION DEMO")
    print("=" * 40)
    print()

    reasoning_system = create_integrated_reasoning_system(debug_mode=False)

    # Test different confidence scenarios
    confidence_scenarios = [
        ("I'm definitely frustrated", 0.9, "High confidence - clear emotional signal"),
        ("Maybe I'm a bit annoyed?", 0.3, "Low confidence - uncertain language"),
        ("I think you might prefer this approach", 0.6, "Moderate confidence - hedged statement"),
        ("Not sure what I'm feeling", 0.2, "Very low confidence - explicit uncertainty")
    ]

    print("Testing confidence expression for different scenarios:")
    print()

    for input_text, expected_confidence, description in confidence_scenarios:
        print(f"📝 Input: \"{input_text}\"")
        print(f"💡 Expected: {description}")

        result = reasoning_system.process_user_input(input_text)

        print(f"🎯 Actual confidence: {result.overall_confidence:.2f}")
        print(f"💬 Expression: \"{result.confidence_expression}\"")

        # Check if confidence is appropriate
        confidence_appropriate = abs(result.overall_confidence - expected_confidence) < 0.3
        print(f"✅ Confidence appropriate: {confidence_appropriate}")
        print()


if __name__ == "__main__":
    try:
        demo_reasoning_transparency()
        demo_confidence_calibration()

        print("\n🎉 Demo completed successfully!")
        print("The reasoning transparency system is ready for integration with Penny!")

    except Exception as e:
        print(f"❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()