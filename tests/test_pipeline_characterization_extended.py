"""
Additional characterization tests for ResearchFirstPipeline.think().

This file is additive to tests/test_pipeline_characterization.py, which
already locks in the base contract (state guard, happy path, prompt
assembly, exception fallback, data-dir isolation). Here we extend coverage
to branches that file's fixture deliberately stubs out or doesn't exercise:
  - the research-required success/failure prompt paths
  - the financial-topic disclaimer
  - the real JudgmentEngine clarify-and-short-circuit path
  - A/B test control-group gating of personality enhancement/post-processing
  - a couple of "as-is" quirks worth flagging for the R1 decomposition
    (see TestThinkKnownQuirks) -- these are NOT bugs to fix here, just
    documented current behavior.

Same isolation strategy as the base file: db_path + data_dir -> temp dir,
self.llm -> FakeLLM, tool_orchestrator -> single-pass stub, ab_test -> no-op.
Slow (full pipeline construction, ~seconds) -- gated behind --run-slow via
conftest SLOW_FILES, same as test_pipeline_characterization.py.
"""

import os
import shutil
import tempfile

import pytest

from src.core.pipeline import State
from research_first_pipeline import ResearchFirstPipeline
from factual_research_manager import ResearchResult


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


class TestThinkResearchPaths:
    """Step 2/3: research classification + research-context prompt assembly."""

    def test_research_success_flags_and_prompt(self, pipeline):
        p, _ = pipeline
        p.research_manager.requires_research = lambda x: True
        p.research_manager.run_research = lambda query, history=None: ResearchResult(
            query=query,
            success=True,
            summary="Widgets are up 12% this quarter.",
            key_insights=["insight A", "insight B"],
            recommendations=[],
            findings=[{"source": "example.com"}],
            confidence=0.9,
            execution_time=0.01,
        )
        p.state = State.THINKING
        r = p.think("Tell me about widget sales")

        assert isinstance(r, str) and r
        # Side-effect flags used by the web interface to show "research used" UI
        assert p.last_research_triggered is True
        assert p.last_research_success is True

        prompt = p.llm.calls[0][0]
        assert "RESEARCH MODE:" in prompt
        assert "RESEARCH SUCCESS" in prompt
        assert "Widgets are up 12% this quarter." in prompt
        assert "insight A" in prompt

    def test_research_failure_flags_and_prompt(self, pipeline):
        p, _ = pipeline
        p.research_manager.requires_research = lambda x: True
        p.research_manager.run_research = lambda query, history=None: ResearchResult(
            query=query,
            success=False,
            summary=None,
            key_insights=[],
            recommendations=[],
            findings=[],
            confidence=0.0,
            execution_time=0.01,
            error="no findings",
        )
        p.state = State.THINKING
        r = p.think("Tell me about widget sales")

        assert isinstance(r, str) and r
        assert p.last_research_triggered is True
        assert p.last_research_success is False

        prompt = p.llm.calls[0][0]
        assert "RESEARCH MODE (NO DATA):" in prompt
        assert "RESEARCH FAILED - CRITICAL INSTRUCTION" in prompt
        assert "do not fabricate" in prompt.lower()


class TestThinkFinancialDisclaimer:
    """Step 6: financial-topic responses get a disclaimer appended."""

    def test_disclaimer_appended_for_financial_topic(self, pipeline):
        p, _ = pipeline
        p.research_manager.is_financial_topic = lambda x: True
        p.state = State.THINKING
        r = p.think("What's a good ETF for retirement?")

        assert "not financial advice" in r.lower()
        assert "42" in r  # stub content still present alongside the disclaimer

    def test_no_disclaimer_for_non_financial_topic(self, pipeline):
        p, _ = pipeline
        p.research_manager.is_financial_topic = lambda x: False
        p.state = State.THINKING
        r = p.think("Hello Penny, how are you today?")

        assert "financial advice" not in r.lower()


class TestThinkJudgmentClarifyGate:
    """
    Step 1.3: the real JudgmentEngine can short-circuit think() before any
    LLM call. Uses the docstring's own example input ("Fix that thing" ->
    vague referent) rather than mocking Decision, so this exercises the
    real JudgmentEngine + PennyStyleClarifier wiring, not a stand-in.
    """

    def test_vague_referent_short_circuits_before_llm(self, pipeline):
        # PennyStyleClarifier picks one of 5 fixed templates via random.choice,
        # so the exact string isn't seeded/deterministic -- pin the closed set
        # of possible outputs for "action=fix" instead of one literal string.
        possible_responses = {
            "Quick check so I don't go off into the weeds—do you mean X or Y?",
            "Before I sprint in the wrong direction: which fix exactly?",
            "Two-second check: which fix exactly?",
            "Real quick—which fix exactly?",
            "Just to nail this—which fix exactly?",
        }
        p, _ = pipeline
        p.state = State.THINKING
        r = p.think("Fix that thing")

        assert r in possible_responses
        assert p.llm.calls == []  # never reached generation
        assert p.state == State.SPEAKING

    def test_clarify_logs_duplicate_line(self, pipeline, caplog):
        """
        Documents an existing quirk, not a spec: _should_clarify() (line
        ~355-356 in research_first_pipeline.py) logs the same
        "Judgment: Clarifying due to ..." message twice via two consecutive
        identical logger.info() calls. This looks like a copy-paste slip,
        but think() is left untouched here -- just locking in the doubled
        log line so it doesn't silently change during the R1 decomposition.
        """
        import logging
        caplog.set_level(logging.INFO)
        p, _ = pipeline
        p.state = State.THINKING
        p.think("Fix that thing")

        matches = [
            rec for rec in caplog.records
            if "Judgment: Clarifying due to" in rec.message
        ]
        assert len(matches) == 2
        assert matches[0].message == matches[1].message


class TestThinkABTestGating:
    """Personality prompt-building and response post-processing are only
    applied for the treatment group; control group gets the raw stub."""

    def test_control_group_skips_personality_steps(self, pipeline):
        p, _ = pipeline
        p.ab_test.is_control_group = lambda *a, **k: True

        prompt_builder_calls = []
        post_processor_calls = []

        async def spy_build_prompt(*a, **kw):
            prompt_builder_calls.append((a, kw))
            return "SHOULD NOT BE CALLED"

        async def spy_process_response(*a, **kw):
            post_processor_calls.append((a, kw))
            return {"response": "SHOULD NOT BE CALLED", "adjustments": []}

        p.personality_prompt_builder.build_personality_prompt = spy_build_prompt
        p.personality_post_processor.process_response = spy_process_response

        p.state = State.THINKING
        r = p.think("Hello Penny, how are you today?")

        assert prompt_builder_calls == []
        assert post_processor_calls == []
        # No post-processing -> response is exactly the sanitized stub
        assert r == FakeLLM.STUB

    def test_treatment_group_runs_personality_steps(self, pipeline):
        p, _ = pipeline
        p.ab_test.is_control_group = lambda *a, **k: False

        post_processor_calls = []
        real_process_response = p.personality_post_processor.process_response

        async def spy_process_response(*a, **kw):
            post_processor_calls.append((a, kw))
            return await real_process_response(*a, **kw)

        p.personality_post_processor.process_response = spy_process_response

        p.state = State.THINKING
        p.think("Hello Penny, how are you today?")

        assert len(post_processor_calls) == 1


class TestThinkResilience:
    """Non-fatal failures in optional subsystems are swallowed."""

    def test_semantic_search_failure_is_swallowed(self, pipeline):
        p, _ = pipeline

        def boom(*a, **kw):
            raise RuntimeError("vector store unavailable")

        p.semantic_memory.semantic_search = boom
        p.state = State.THINKING
        r = p.think("Hello Penny, how are you today?")

        assert isinstance(r, str)
        assert "42" in r
        assert p.state == State.SPEAKING

    def test_uncaught_error_message_leaks_exception_text(self, pipeline):
        """
        Documents current (not necessarily desirable) behavior: the
        top-level except block in think() interpolates str(e) directly into
        the user-facing fallback response, so internal exception text is
        exposed to the end user rather than being logged-only. Not fixed
        here -- just characterized so a refactor doesn't change it silently.
        """
        async def boom(**kw):
            raise RuntimeError("boom-specific-detail")

        p, _ = pipeline
        p.tool_orchestrator.orchestrate = boom
        p.state = State.THINKING
        r = p.think("Hello Penny")

        assert "boom-specific-detail" in r


class TestThinkKnownQuirks:
    """
    Behaviors that look like bugs/stale-TODOs but are left exactly as-is
    per the characterization brief -- documented, not fixed.
    """

    def test_judgment_context_never_reflects_conversation_history(self, pipeline):
        """
        Step 1.3 builds initial_judgment_context with
        'conversation_history': [] as a hardcoded literal (comment says
        "Will populate from context manager", but nothing ever does). This
        stays empty even after prior turns have been cached in
        self.context_manager, across repeated think() calls.
        """
        p, _ = pipeline
        captured = []
        real_analyze = p.judgment_engine.analyze_request

        def spy_analyze(user_input, context):
            captured.append(context)
            return real_analyze(user_input, context)

        p.judgment_engine.analyze_request = spy_analyze

        p.state = State.THINKING
        p.think("Hello Penny, how are you today?")
        assert p.context_manager.get_stats()["window_size"] >= 1

        p.state = State.THINKING
        p.think("Following up on that last message")

        assert len(captured) == 2
        for ctx in captured:
            assert ctx["conversation_history"] == []

    def test_optional_learning_subsystems_disabled_by_default(self, pipeline):
        """
        goal_tracker / belief_extractor / outcome_tracker / hebbian are all
        None out of the box (feature-flagged off in __init__), so their
        corresponding think() branches (Step 1.1/1.15/1.2, Week 10 Hebbian)
        are dead code on a stock pipeline. A default think() call must not
        touch _last_response_id/_last_response_type, since that only
        happens when outcome_tracker is present.
        """
        p, _ = pipeline
        assert p.goal_tracker is None
        assert p.belief_extractor is None
        assert p.outcome_tracker is None
        assert p.hebbian is None

        p.state = State.THINKING
        p.think("Hello Penny, how are you today?")

        assert p._last_response_id is None
        assert p._last_response_type is None
