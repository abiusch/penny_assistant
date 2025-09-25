"""
Test Suite for Cultural Intelligence Tool Server (Task 9.3b)
Verifies authentic cultural research, reference validation, and memory integration.
"""

import asyncio
import json
import os
import tempfile
import unittest

from cultural_intelligence_tool_server import (
    create_cultural_intelligence_server,
)
from persistent_memory import PersistentMemory


class TestCulturalIntelligenceServer(unittest.IsolatedAsyncioTestCase):
    """Validate core cultural intelligence operations"""

    async def asyncSetUp(self):
        self.temp_memory = tempfile.NamedTemporaryFile(suffix="_cultural_memory.db", delete=False)
        self.temp_memory.close()
        self.server = await create_cultural_intelligence_server({
            "memory": PersistentMemory(self.temp_memory.name)
        })
        # Prime reference storage for consistent validation
        await self.server.generate_contextual_references(
            topic="mentoring interns",
            cultural_background={"region": "california", "generation": "millennial"},
            confidence_threshold=0.75,
            user_id="setup_user"
        )

    async def asyncTearDown(self):
        await self.server.stop()
        try:
            os.remove(self.temp_memory.name)
        except OSError:
            pass

    async def test_research_and_reference_generation(self):
        """End-to-end check for research + contextual reference generation"""
        research_result = await self.server.research_cultural_context(
            topic="mentoring interns",
            region="california",
            generation="millennial",
            tone_goal="supportive",
            user_id="test_user",
        )
        self.assertTrue(research_result.success, msg=str(research_result.error))
        data = research_result.data
        self.assertGreater(len(data["key_patterns"]), 0)

        references_result = await self.server.generate_contextual_references(
            topic="mentoring interns",
            cultural_background={"region": "california", "generation": "millennial"},
            confidence_threshold=0.75,
            user_id="test_user",
        )
        self.assertTrue(references_result.success)
        self.assertGreaterEqual(len(references_result.data["references"]), 1)

    async def test_authenticity_validation_flow(self):
        """Ensure authenticity validator flags forced items and approves natural ones"""
        natural_validation = await self.server.validate_cultural_reference(
            reference="Ted Lasso",
            context={
                "topic": "team morale",
                "relationship": "professional",
                "conversation": "We were talking about keeping morale up during crunch weeks.",
                "keywords": ["morale", "lasso"],
            },
            user_id="test_user",
        )
        self.assertTrue(natural_validation.success)
        self.assertEqual(natural_validation.data["recommendation"], "safe_to_use")

        forced_validation = await self.server.validate_cultural_reference(
            reference="bruh",
            context={
                "topic": "status report",
                "relationship": "professional",
                "sass_level": "minimal",
                "conversation": "Let's review the incident report.",
                "requires_depth": True,
            },
            user_id="test_user",
        )
        self.assertTrue(forced_validation.success)
        self.assertEqual(forced_validation.data["recommendation"], "revise_before_use")

    async def test_authenticity_risk_assessment(self):
        """Validate risk evaluation aggregates element-level risk"""
        risk_result = await self.server.assess_authenticity_risk(
            proposed_response="Let's tackle this together—no need to overcomplicate it.",
            cultural_elements=["Ted Lasso", "bruh"],
            user_profile={"relationship": "professional", "topic": "planning"},
            user_id="test_user",
        )
        self.assertTrue(risk_result.success)
        self.assertIn(risk_result.data["combined_risk"], {"medium", "high", "low"})
        self.assertEqual(len(risk_result.data["element_risks"]), 2)


if __name__ == "__main__":
    unittest.main()
