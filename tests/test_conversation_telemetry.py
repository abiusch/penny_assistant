"""
Telemetry and A/B testing integration tests.
"""

import asyncio
import os
import tempfile
import unittest

from conversation_telemetry_system import ConversationTelemetrySystem
from production_a_b_testing import ProductionABTesting


class TestConversationTelemetry(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.temp_db = tempfile.NamedTemporaryFile(suffix="_telemetry.db", delete=False)
        self.temp_db.close()
        self.telemetry = ConversationTelemetrySystem(self.temp_db.name)
        await self.telemetry.initialize()
        self.ab_testing = ProductionABTesting(self.telemetry, self.temp_db.name)

    async def asyncTearDown(self):
        try:
            os.remove(self.temp_db.name)
        except OSError:
            pass

    async def test_logging_and_flow_metrics(self):
        await self.telemetry.log_cultural_decision(
            "enhanced",
            {"topic": "relationships", "session_id": "s1"},
            {"improvement": 0.2}
        )
        flow_metrics = await self.telemetry.measure_conversation_flow([
            {"user": "How are the interns doing?", "assistant": "They're settling in nicely."},
            {"user": "Any ideas to keep things fun?", "assistant": "We could run a game night."}
        ], {"session_id": "s1"})
        self.assertIn("response_appropriateness", flow_metrics)

        decisions = await self.telemetry.get_recent_decisions(limit=5)
        self.assertGreaterEqual(len(decisions), 1)

    async def test_personality_and_ab_metrics(self):
        consistency = await self.telemetry.assess_personality_consistency(
            ["Let's ship it.", "We can iterate quickly."],
            {"keywords": ["ship", "iterate"]}
        )
        self.assertGreaterEqual(consistency, 0.0)

        assigned = await self.ab_testing.randomly_assign_cultural_mode("user123", "session123")
        await self.ab_testing.collect_session_metrics(
            "session123",
            assigned,
            {
                "response_appropriateness": 0.8,
                "engagement_improvement": 0.1,
            }
        )
        summary = await self.ab_testing.analyze_comparative_performance()
        self.assertIn("enabled_average", summary)
        self.assertIn("disabled_average", summary)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
