"""
Characterization tests for ResearchFirstPipeline.think().

These LOCK the pipeline's current observable behavior so the God-Object
decomposition (R1) can proceed safely. They are NOT specifications of desired
behavior — they capture what think() does today.

Strategy (the pipeline is heavy and has many hardcoded deps, so we inject/stub
the external and expensive seams and assert orchestration behavior):
  - db_path + data_dir  -> temp (persistent writes never touch real data/)
  - self.llm            -> FakeLLM (deterministic, offline, records calls)
  - tool_orchestrator   -> stub that runs the real prompt-assembly generator once
  - ab_test             -> no-op (avoids A/B db access)
  - research_manager    -> requires_research False (no live web search)

Slow (each build ~4.5s) — gated behind --run-slow via conftest SLOW_FILES.
"""

import glob
import os
import shutil
import tempfile

import pytest

from src.core.pipeline import State
from research_first_pipeline import ResearchFirstPipeline


class FakeLLM:
    """Offline stand-in that records prompts and returns a fixed completion."""

    STUB = "STUBRESP the answer is 42"

    def __init__(self):
        self.calls = []

    def complete(self, prompt, tone=None, **kw):
        self.calls.append((prompt, tone))
        return self.STUB

    def generate(self, prompt, **kw):
        self.calls.append((prompt, None))
        return self.STUB


async def _fake_orchestrate(initial_prompt=None, llm_generator=None,
                            conversation_context=None, **kw):
    """Mimic 'no tool call, just answer': run the real generator once."""
    return llm_generator({}) if llm_generator else ""


@pytest.fixture
def pipeline():
    d = tempfile.mkdtemp()
    p = ResearchFirstPipeline(db_path=os.path.join(d, "tracking.db"), data_dir=d)
    p.llm = FakeLLM()
    p.tool_orchestrator.orchestrate = _fake_orchestrate
    p.ab_test.assign_group = lambda *a, **k: "treatment"
    p.ab_test.is_control_group = lambda *a, **k: False
    p.ab_test.record_metrics = lambda *a, **k: None
    p.research_manager.requires_research = lambda x: False  # keep tests offline
    yield p, d
    shutil.rmtree(d, ignore_errors=True)


class TestThinkContract:
    def test_returns_empty_when_not_thinking(self, pipeline):
        """State guard: think() no-ops unless state == THINKING."""
        p, _ = pipeline
        p.state = State.IDLE
        assert p.think("hello") == ""

    def test_happy_path_returns_sanitized_stub(self, pipeline):
        p, _ = pipeline
        p.state = State.THINKING
        r = p.think("Hello Penny, how are you today?")
        assert isinstance(r, str) and r
        assert "42" in r                       # stub content survives generation + post-processing
        assert len(p.llm.calls) == 1           # LLM invoked exactly once
        assert p.state == State.SPEAKING       # transitions THINKING -> SPEAKING

    def test_llm_receives_assembled_prompt(self, pipeline):
        p, _ = pipeline
        p.state = State.THINKING
        p.think("Hello Penny")
        prompt = p.llm.calls[0][0]
        # prompt assembly includes the user query and response-requirements block
        assert "User query" in prompt
        assert "Hello Penny" in prompt
        assert "RESPONSE REQUIREMENTS" in prompt

    def test_never_raises_returns_graceful_fallback(self, pipeline):
        """Any generation error is caught; think() always returns a str."""
        p, _ = pipeline

        async def boom(**kw):
            raise RuntimeError("boom")

        p.tool_orchestrator.orchestrate = boom
        p.state = State.THINKING
        r = p.think("Hello Penny")
        assert isinstance(r, str)
        assert "issue processing" in r.lower()  # graceful fallback message


class TestThinkIsolation:
    def _real_data_files(self):
        # Ignore transient WAL/SHM artifacts (created even by read-only WAL access).
        return {
            f for f in glob.glob("data/**/*", recursive=True)
            if not f.endswith(("-shm", "-wal"))
        }

    def test_persistent_writes_stay_in_temp(self, pipeline):
        p, d = pipeline
        before = self._real_data_files()
        p.state = State.THINKING
        p.think("Hello Penny, I like tabs over spaces")
        after = self._real_data_files()
        # think() must not create new files under the real data/ dir
        assert after == before, f"think() polluted real data/: {sorted(after - before)}"
        # and the semantic memory vector store must live under the injected temp dir
        assert glob.glob(os.path.join(d, "embeddings", "*")), "vector store not in temp dir"
