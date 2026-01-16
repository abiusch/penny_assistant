#!/usr/bin/env python3
"""
Adaptive Sass Chat Interface (legacy entry point)

This launcher now routes through the unified enhanced conversation pipeline so
that every conversational path benefits from the research-first architecture,
authenticity guardrails, and telemetry instrumentation.
"""

from chat_penny import main as run_enhanced_chat


def main() -> None:
    """Delegate conversation handling to the enhanced pipeline."""

    print("🔁 'adaptive_sass_chat.py' now uses the enhanced conversation pipeline")
    print("   • Factual queries trigger autonomous research by default")
    print("   • Cultural intelligence and telemetry run in lockstep")
    print("   • Existing memory and sass learning still feed the pipeline")
    run_enhanced_chat()


if __name__ == "__main__":
    main()
