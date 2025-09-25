#!/usr/bin/env python3
"""
Enhanced Penny Chat Interface (Text)
Routes every conversation through the EnhancedConversationPipeline so factual
queries trigger autonomous research, cultural intelligence, and telemetry.
"""

import logging
import os
import sys
from typing import Dict

# Ensure local packages can be imported when launched via VS Code task
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from core.pipeline import State
from research_first_pipeline import ResearchFirstPipeline

logger = logging.getLogger("chat_penny")
logging.basicConfig(level=logging.INFO)

HELP_TEXT = """\
Commands:
  memory stats            Show a snapshot of Penny's memory and conversation state
  search memories <term>  Search stored memories for a keyword
  quit/exit               Leave the conversation
"""


def print_intro(pipeline: ResearchFirstPipeline) -> None:
    print("🧠 Enhanced Penny Chat Interface")
    print("=" * 70)
    print("This interface uses the full research-first pipeline. Factual queries trigger")
    print("autonomous research, cultural intelligence, and telemetry instrumentation.")

    try:
        stats = pipeline.base_memory.get_memory_stats()
        print("\n📊 System snapshot:")
        print(f"   Memory items: {sum(stats.values())}")
        print(f"   Research-first mode: enabled")
        print(f"   Enhanced personality: active")
    except Exception as exc:  # pragma: no cover - informational only
        logger.debug("Unable to display initial stats: %s", exc)

    print("\n" + HELP_TEXT)
    print("-" * 70)


def handle_memory_stats(pipeline: ResearchFirstPipeline) -> None:
    try:
        stats = pipeline.base_memory.get_memory_stats()
        summary = pipeline.enhanced_memory.get_relationship_summary()
        print("\n🧠 Memory statistics:")
        for key, value in stats.items():
            print(f"   {key}: {value}")
        print(f"🤝 Relationship summary: {summary}")
    except Exception as exc:
        print(f"❌ Unable to retrieve memory stats: {exc}")


def handle_memory_search(pipeline: ResearchFirstPipeline, term: str) -> None:
    try:
        results = pipeline.base_memory.search_memories(search_term=term, limit=5)
        if not results:
            print(f"🤷 No memories found for '{term}'.")
            return
        print(f"🔍 Top memories for '{term}':")
        for item in results:
            print(f"   • {item.key}: {item.value}")
    except Exception as exc:
        print(f"❌ Memory search failed: {exc}")


def run_chat_loop(pipeline: ResearchFirstPipeline) -> None:
    conversation_turns = 0
    try:
        while True:
            try:
                user_input = input("📝 You: ").strip()
            except EOFError:
                print()
                break

            if not user_input:
                continue

            lowered = user_input.lower()
            if lowered in {"quit", "exit", "bye"}:
                break

            if lowered == "memory stats":
                handle_memory_stats(pipeline)
                continue

            if lowered.startswith("search memories "):
                term = user_input[len("search memories "):].strip()
                if term:
                    handle_memory_search(pipeline, term)
                else:
                    print("⚠️ Provide a search term after 'search memories'.")
                continue

            pipeline.state = State.THINKING
            response = pipeline.think(user_input)
            pipeline.state = State.IDLE

            if not response:
                response = "I didn't catch that. Could you rephrase?"

            print(f"🤖 Penny: {response}")
            conversation_turns += 1
    finally:
        try:
            pipeline.shutdown()
        except Exception as exc:  # pragma: no cover - best effort cleanup
            logger.debug("Pipeline shutdown error: %s", exc)
        print("\n👋 Ending Penny session. Take care!")


def main():
    pipeline = ResearchFirstPipeline()
    print_intro(pipeline)
    run_chat_loop(pipeline)


if __name__ == "__main__":
    main()
