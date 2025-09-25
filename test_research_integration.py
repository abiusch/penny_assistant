import numpy as np
import pytest

from enhanced_conversation_pipeline import EnhancedConversationPipeline
from factual_research_manager import ResearchResult
from src.core.pipeline import State


class StubTelemetry:
    def __init__(self):
        self.events = []

    def log_event(self, event_type, data=None):
        self.events.append((event_type, data or {}))

    def log_performance(self, operation, duration):  # pragma: no cover - not used in tests
        pass


class StubResearchManager:
    def __init__(self):
        self.calls = 0

    def requires_research(self, text: str) -> bool:
        return "invest" in text.lower() or "robotics" in text.lower()

    def is_financial_topic(self, text: str) -> bool:
        return "invest" in text.lower()

    def run_research(self, query: str, history):
        self.calls += 1
        return ResearchResult(
            query=query,
            success=True,
            summary="Stub synthesis of verified robotics investment data",
            key_insights=["Founded companies in 2024 show the highest growth"],
            recommendations=[],
            findings=[{"source": "stub", "evidence": "synthetic"}],
            confidence=0.8,
            execution_time=0.12,
        )


class StubLLM:
    def complete(self, prompt: str, tone=None):
        return "Stubbed response grounded in research"

    def generate(self, prompt: str):  # pragma: no cover - fallback
        return self.complete(prompt)


def test_financial_query_triggers_research_and_disclaimer():
    pipeline = EnhancedConversationPipeline()

    pipeline.telemetry = StubTelemetry()
    pipeline.telemetry_client = None
    pipeline.ab_testing = None
    pipeline.cultural_adapter = None
    pipeline.research_manager = StubResearchManager()
    pipeline.llm = StubLLM()

    pipeline.state = State.THINKING
    response = pipeline.think("I want to research emerging robotics companies to invest in")

    assert pipeline.research_manager.calls == 1
    assert any(evt[0] == "factual_research_triggered" for evt in pipeline.telemetry.events)
    assert any(evt[0] == "factual_research_result" for evt in pipeline.telemetry.events)
    assert "informational purposes only" in response.lower()


def test_legacy_adaptive_chat_routes_to_pipeline():
    import adaptive_sass_chat
    import chat_penny

    assert adaptive_sass_chat.run_enhanced_chat is chat_penny.main


def test_voice_launcher_invokes_enhanced_pipeline(monkeypatch):
    events = {}

    class StubPipeline:
        def __init__(self):
            self.state = State.IDLE

        def think(self, text):
            events['think'] = text
            self.state = State.SPEAKING
            return "stub voice reply"

        def speak(self, response):
            events['speak'] = response
            self.state = State.IDLE
            return True

        def shutdown(self):
            events['shutdown'] = True

    import voice_enhanced_penny

    user_inputs = iter(["", "exit"])
    monkeypatch.setattr("builtins.input", lambda prompt='': next(user_inputs))
    monkeypatch.setattr(voice_enhanced_penny, "EnhancedConversationPipeline", StubPipeline)
    monkeypatch.setattr(voice_enhanced_penny, "record_audio", lambda *args, **kwargs: np.zeros((voice_enhanced_penny.SAMPLE_RATE, 1), dtype='float32'))
    monkeypatch.setattr(voice_enhanced_penny, "transcribe_audio", lambda pipeline, audio: "Tell me about robotics investments")
    def speak_via_helper(pipeline, response):
        events.setdefault('spoken_via_helper', response)
        return pipeline.speak(response)

    monkeypatch.setattr(voice_enhanced_penny, "speak_response", speak_via_helper)
    monkeypatch.setattr("builtins.print", lambda *args, **kwargs: None)

    voice_enhanced_penny.main()

    assert events.get('think') == "Tell me about robotics investments"
    assert events.get('speak') == "stub voice reply"
    assert events.get('shutdown') is True
