#!/usr/bin/env python3
"""
Adaptive voice chat launcher that now delegates to the enhanced pipeline.

By sharing the same pipeline as the text and standard voice launchers we ensure
all spoken interactions trigger the research-first safeguards, cultural
intelligence, and telemetry instrumentation.
"""

from voice_enhanced_penny import main as run_voice_session


def main() -> None:
    print("🔁 'adaptive_voice_penny.py' now forwards to the enhanced voice pipeline")
    run_voice_session()


if __name__ == "__main__":
    main()
