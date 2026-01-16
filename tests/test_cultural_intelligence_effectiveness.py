"""
Integration tests for cultural intelligence coordinator and conversation authenticity.
"""

import asyncio
import os
import tempfile
import unittest

from cultural_intelligence_coordinator import CulturalIntelligenceCoordinator
from mcp_tool_registry import MCPToolRegistry


class CulturalIntelligenceTestCase(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.temp_memory = tempfile.NamedTemporaryFile(suffix="_cultural_memory.db", delete=False)
        self.temp_memory.close()
        self.registry_db = tempfile.NamedTemporaryFile(suffix="_mcp_registry.db", delete=False)
        self.registry_db.close()
        self.coordinator = await CulturalIntelligenceCoordinator.create(
            memory_path=self.temp_memory.name
        )
        self.registry = MCPToolRegistry(db_path=self.registry_db.name)

    async def asyncTearDown(self):
        await self.coordinator.shutdown()
        try:
            os.remove(self.temp_memory.name)
        except OSError:
            pass
        try:
            os.remove(self.registry_db.name)
        except OSError:
            pass

    async def test_registry_registration_and_execution(self):
        registered = await self.coordinator.register_with_registry(self.registry)
        self.assertTrue(registered)

        available_tools = await self.registry.get_available_tools()
        cultural_tools = [tool for tool in available_tools if tool["name"].startswith("cultural_intelligence.")]
        self.assertGreaterEqual(len(cultural_tools), 10)

        result = await self.registry.execute_tool(
            "cultural_intelligence.validate_cultural_reference",
            {
                "reference": "Ted Lasso",
                "context": {
                    "topic": "team morale",
                    "relationship": "professional",
                    "conversation": "We're looking for morale boosters."
                }
            }
        )
        self.assertIn("fit_score", result)
        self.assertIn("recommendation", result)

    async def test_casual_conversation_enhancement(self):
        history = [
            {"user": "The team is drained after that crunch week.", "assistant": "We should build in some slack time."},
            {"user": "I want to keep morale up without sounding fake.", "assistant": "Let's brainstorm a few approaches."}
        ]
        base_response = "Let's remind everyone we've got each other's backs."
        result = await self.coordinator.enhance_response(
            user_input="How do I keep things light for the interns?",
            conversation_history=history,
            base_response=base_response,
            metadata={
                "topic": "relationships",
                "relationship": "friendly",
                "sass_level": "lite",
                "personality_mode": "playful"
            }
        )
        self.assertTrue(result.used_cultural_enhancement)
        self.assertGreater(result.metrics["enhanced_authenticity_score"], result.metrics["base_authenticity_score"])
        self.assertFalse(result.metrics["forced_detected"])

    async def test_technical_conversation_prefers_base_response(self):
        history = [
            {"user": "Can you help me debug this query planner issue?", "assistant": "Sure, let's gather the query plans."}
        ]
        base_response = "Let's start by capturing the slow queries and profiling them."
        result = await self.coordinator.enhance_response(
            user_input="We need to fix the latency without confusing the stakeholders.",
            conversation_history=history,
            base_response=base_response,
            metadata={
                "topic": "technology",
                "relationship": "professional",
                "sass_level": "minimal",
                "personality_mode": "analytical"
            }
        )
        self.assertFalse(result.used_cultural_enhancement)
        self.assertGreaterEqual(result.metrics["base_authenticity_score"], result.metrics["enhanced_authenticity_score"])
        self.assertEqual(result.decision, "base")


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
