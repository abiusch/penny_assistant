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
from datetime import datetime, timedelta

import pytest

from src.core.pipeline import State
from research_first_pipeline import ResearchFirstPipeline, OUTCOME_TRACKING_AVAILABLE
from src.memory.emotional_continuity import EmotionalThread
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


class TestThinkPromptCaptureCoverage:
    """
    Closes coverage gaps found in the PromptBuilder pre-flight (R1 step 2 prep).
    Several variables the `llm_generator` closure captures had no assertion on
    their effect on the assembled prompt / LLM call, so a faithful extraction
    could drop them without any test noticing. These lock the CURRENT behavior.
    Nothing is extracted yet -- they exercise the closure exactly as it stands.
    """

    def test_tone_is_threaded_through_to_llm_call(self, pipeline):
        # tone comes from _route_tone() (on the parent PipelineLoop) and must
        # reach self.llm.complete(final_prompt, tone=tone). The existing tests
        # record (prompt, tone) but never assert the tone slot.
        p, _ = pipeline
        p._route_tone = lambda text: "sentinel_tone"
        p.state = State.THINKING
        p.think("Hello Penny")

        assert p.llm.calls, "LLM was never called"
        assert p.llm.calls[0][1] == "sentinel_tone"

    def test_conversation_and_semantic_sections_injected_when_present(self, pipeline):
        # The existing 17 tests run on a fresh pipeline where conversation
        # context and semantic results are both empty, so those two prompt
        # sections are never exercised. Seed both and assert they land.
        p, _ = pipeline
        p.context_manager.get_context_for_prompt = lambda **kw: "PRIOR_CONTEXT_SENTINEL"
        p.semantic_memory.semantic_search = lambda query, k=3: [
            {"user_input": "we talked about widgets before", "similarity": 0.88},
        ]
        p.state = State.THINKING
        p.think("Hello Penny")

        prompt = p.llm.calls[0][0]
        assert "PRIOR_CONTEXT_SENTINEL" in prompt                 # conversation-context section
        assert "Relevant past conversations:" in prompt           # semantic-memory section header
        assert "we talked about widgets before" in prompt         # semantic hit content

    def test_current_emotion_line_injected(self, pipeline):
        # emotion_result is always produced; its "User's current emotion:" line
        # is injected into the prompt, but no existing test asserts it.
        p, _ = pipeline
        p.state = State.THINKING
        p.think("Hello Penny, how are you today?")

        prompt = p.llm.calls[0][0]
        assert "User's current emotion:" in prompt


class TestInputProcessorPrereqCoverage:
    """Coverage gaps closed before the R1 step-5 InputProcessor extraction.

    Two think() input-processing branches were never exercised because every
    existing test starts from a fresh pipeline:
      - the emotional-continuity check-in path (Step 1.6), gated behind three
        opt-in/enabled flags plus a pre-seeded emotional thread; and
      - the enabled learning pre-hooks (Steps 1.1/1.15/1.2), which default to
        None and were only ever tested in the disabled state.
    These lock CURRENT behavior so the upcoming extraction can be proven
    byte-faithful. No production code has moved yet.
    """

    def test_emotional_checkin_injects_context(self, pipeline):
        # GAP 1: emotional-continuity check-in path (Step 1.6).
        # should_check_in() only fires when tracking + check-ins consent are on
        # AND EmotionalContinuity.enabled is True. That `enabled` flag is
        # captured once at __init__ from is_tracking_enabled() (default False),
        # so flipping the consent prefs alone is not enough -- we must also flip
        # emotional_continuity.enabled directly. Set everything in-memory;
        # grant_consent() would write to data/user_consent.json.
        p, _ = pipeline
        p.consent_manager.preferences['emotional_tracking_enabled'] = True
        p.consent_manager.preferences['proactive_checkins_enabled'] = True
        p.emotional_continuity.enabled = True
        # Seed a prior high-intensity, un-followed-up thread inside the window.
        p.emotional_continuity.threads.append(EmotionalThread(
            emotion='stress',
            intensity=0.9,
            context='worried about layoffs',
            timestamp=datetime.now(),
            turn_id='prev',
        ))
        p.state = State.THINKING
        # Neutral input on purpose: track_emotion() runs first (Step 1.6) and a
        # high-intensity input would append a newer thread that should_check_in()
        # would return instead of our seeded one.
        p.think("what time is it")

        assert p.llm.calls, "LLM was never called"
        assert "[EMOTIONAL CONTEXT]" in p.llm.calls[0][0]

    @pytest.mark.skipif(
        not OUTCOME_TRACKING_AVAILABLE,
        reason="outcome tracking symbols unavailable; post-turn tagging block "
               "would NameError on a stubbed outcome_tracker",
    )
    def test_learning_prehooks_wired_when_enabled(self, pipeline):
        # GAP 2: the learning pre-hooks (Steps 1.1/1.15/1.2) guard on attribute
        # truthiness, not on the *_enabled flags, so assigning a stub to each
        # attribute exercises the enabled branch without constructing the real
        # subsystems. We assert only that think() routes the normalized command
        # to each hook -- not the subsystems' internal logic.
        p, _ = pipeline

        class GoalStub:
            def __init__(self):
                self.calls = []

            def process_turn(self, cmd, session_id=None):
                self.calls.append((cmd, session_id))
                return {"new_goal": None, "updated_goals": []}

        class BeliefStub:
            def __init__(self):
                self.calls = []

            def extract_from_turn(self, cmd, session_id=None):
                self.calls.append((cmd, session_id))
                return []

        class OutcomeStub:
            def __init__(self):
                self.calls = []

            def detect_user_reaction(self, cmd, prior_response_id=None,
                                     session_id=None):
                self.calls.append((cmd, prior_response_id, session_id))
                return ("neutral", 0.0)

        goal_stub = GoalStub()
        belief_stub = BeliefStub()
        outcome_stub = OutcomeStub()
        p.goal_tracker = goal_stub
        p.belief_extractor = belief_stub
        p.outcome_tracker = outcome_stub
        # Prerequisite: the Step 1.1 branch also requires a prior response id.
        p._last_response_id = "resp_prev"
        # user_model_enabled stays False so the only belief call is the pre-hook,
        # not the separate belief use inside _judgment_gate.
        p.state = State.THINKING
        p.think("hello penny")

        assert goal_stub.calls, "goal_tracker.process_turn was not called"
        assert goal_stub.calls[0][0] == "hello penny"
        assert belief_stub.calls, "belief_extractor.extract_from_turn was not called"
        assert belief_stub.calls[0][0] == "hello penny"
        assert outcome_stub.calls, "outcome_tracker.detect_user_reaction was not called"
        assert outcome_stub.calls[0][0] == "hello penny"


class TestPostTurnProcessorPrereqCoverage:
    """Coverage gaps closed before the R1 step-6 PostTurnProcessor extraction.

    PostTurnProcessor is the final, most entangled piece of think(): the Step 8
    dual-save block (7-8 subsystems under one try/except), Step 9 A/B metrics,
    and the Week 11 outcome-tagging step. The original mapping tested only
    isolation ("does it write to a temp dir without erroring"), not the content
    of what gets saved or most of the sub-branches. These lock CURRENT behavior
    so the upcoming extraction can be proven byte-faithful. No code has moved.
    """

    def test_dual_save_content(self, pipeline):
        # Step 8: capture the args handed to both save targets and assert the
        # enhanced_metadata payload is correct (not merely "no exception").
        p, _ = pipeline
        ctx_calls = []
        sem_calls = []
        p.context_manager.add_turn = lambda **kw: ctx_calls.append(kw)
        p.semantic_memory.add_conversation_turn = lambda **kw: sem_calls.append(kw)

        craft = "Tell me about the history of computers"
        expected_emotion = p.emotion_detector.detect_emotion(craft)
        p.state = State.THINKING
        final = p.think(craft)

        assert ctx_calls, "context_manager.add_turn was not called"
        assert sem_calls, "semantic_memory.add_conversation_turn was not called"
        # Both saves see the same user input + assistant response.
        assert ctx_calls[0]["user_input"] == craft
        assert ctx_calls[0]["assistant_response"] == final
        assert sem_calls[0]["user_input"] == craft
        assert sem_calls[0]["assistant_response"] == final
        # semantic_memory persists the metadata under `context`; context_manager
        # under `metadata`. Both carry the same enhanced_metadata dict.
        meta = sem_calls[0]["context"]
        assert meta is ctx_calls[0]["metadata"]
        assert meta["research_used"] is False           # fixture: requires_research=False
        assert meta["financial_topic"] is False         # non-financial input
        assert meta["ab_test_group"] == "treatment"     # fixture assign_group stub
        assert meta["emotion"] == expected_emotion.primary_emotion
        assert meta["sentiment"] == expected_emotion.sentiment
        assert isinstance(meta["response_time_ms"], int) and meta["response_time_ms"] >= 0

    def test_personality_snapshot_fires_on_first_turn(self, pipeline):
        # should_snapshot() returns True whenever no snapshots exist yet, so the
        # very first turn on a fresh pipeline creates one (interval is 50, but
        # the empty-list short-circuit fires first).
        p, _ = pipeline
        assert p.personality_snapshots.snapshots == []
        p.state = State.THINKING
        p.think("Hello Penny")

        assert len(p.personality_snapshots.snapshots) == 1

    def test_forgetting_mechanism_applies_decay(self, pipeline):
        # apply_decay fires when conversation_count % 10 == 0. The count comes
        # from semantic_memory.get_stats(), which is >=1 after the save and so
        # never naturally lands on a multiple of 10 -- stub it to 10.
        p, _ = pipeline
        p.semantic_memory.get_stats = lambda: {"total_conversations": 10}
        # Two seeded threads: one inside the 30-day window (should decay), one
        # older than the window (should be pruned). Tracking consent stays off,
        # so _process_emotion leaves these untouched before the save.
        recent = EmotionalThread(
            emotion="joy", intensity=0.9, context="great news",
            timestamp=datetime.now() - timedelta(days=15), turn_id="recent",
        )
        stale = EmotionalThread(
            emotion="sadness", intensity=0.8, context="old worry",
            timestamp=datetime.now() - timedelta(days=40), turn_id="stale",
        )
        p.emotional_continuity.threads = [recent, stale]
        p.state = State.THINKING
        p.think("Hello Penny")

        remaining = p.emotional_continuity.threads
        turn_ids = {t.turn_id for t in remaining}
        assert "stale" not in turn_ids                  # pruned (age 40 > 30)
        assert "recent" in turn_ids                     # kept but decayed
        kept = next(t for t in remaining if t.turn_id == "recent")
        assert kept.intensity < 0.9                      # 0.9 * (1 - 15/30) = 0.45

    def test_hebbian_integration_wired(self, pipeline):
        # Hebbian is None by default; assign a stub and use a benign, substantive
        # message so _is_safe_to_learn() passes. Assert think() routes the turn
        # into process_conversation_turn with the expected keys.
        p, _ = pipeline

        class HebbianStub:
            def __init__(self):
                self.calls = []

            def process_conversation_turn(self, **kw):
                self.calls.append(kw)
                return {"staging_count": 1, "permanent_count": 0, "latency_ms": 1.0}

        heb = HebbianStub()
        p.hebbian = heb
        craft = "Please tell me about the history of computers"
        p.state = State.THINKING
        final = p.think(craft)

        assert heb.calls, "hebbian.process_conversation_turn was not called"
        call = heb.calls[0]
        assert call["user_message"] == craft
        assert call["assistant_response"] == final
        assert isinstance(call["session_id"], str) and call["session_id"]  # turn_id (uuid)

    def test_mark_followed_up(self, pipeline):
        # Reuse the GAP-1 check-in seeding so _process_emotion returns a non-None
        # check_in_thread, then make the LLM echo the emotion word so
        # _response_references_emotion matches and mark_followed_up fires.
        p, _ = pipeline

        class EmotionEchoLLM(FakeLLM):
            STUB = "I remember you mentioned stress about the layoffs. How are you doing?"

        p.llm = EmotionEchoLLM()
        # Force control group so the personality post-processor doesn't rewrite
        # the response (which could strip the emotion word before the follow-up
        # check). sanitize_output preserves plain words.
        p.ab_test.is_control_group = lambda *a, **k: True
        p.consent_manager.preferences["emotional_tracking_enabled"] = True
        p.consent_manager.preferences["proactive_checkins_enabled"] = True
        p.emotional_continuity.enabled = True
        seeded = EmotionalThread(
            emotion="stress", intensity=0.9, context="worried about layoffs",
            timestamp=datetime.now(), turn_id="prev",
        )
        p.emotional_continuity.threads.append(seeded)
        assert seeded.follow_ups == []
        p.state = State.THINKING
        # Neutral input: track_emotion() won't create a higher-priority thread.
        p.think("what time is it")

        assert seeded.follow_ups, "mark_followed_up did not append a follow-up turn"

    def test_ab_metrics_computation(self, pipeline):
        # Step 9: capture the ABTestMetrics object and assert the quality-signal
        # counts computed from the user message (not just "record_metrics ran").
        p, _ = pipeline
        captured = []
        p.ab_test.record_metrics = lambda metrics: captured.append(metrics)

        p.state = State.THINKING
        p.think("thanks, that was perfect and helpful?")

        assert captured, "record_metrics was not called"
        m = captured[0]
        assert m.positive_indicators == 3      # thank, perfect, helpful
        assert m.negative_indicators == 0
        assert m.follow_up_questions == 1       # contains '?'

    @pytest.mark.skipif(
        not OUTCOME_TRACKING_AVAILABLE,
        reason="outcome tracking symbols unavailable; the tagging block would "
               "NameError on classify_response_type/generate_response_id",
    )
    def test_outcome_tagging_enabled(self, pipeline):
        # Week 11: a truthy outcome_tracker activates the post-turn tagging step,
        # which stamps _last_response_id/_last_response_type for next-turn
        # reaction detection. The Step 1.1 pre-hook stays inert because
        # _last_response_id starts as None.
        p, _ = pipeline

        class OutcomeStub:
            pass

        p.outcome_tracker = OutcomeStub()
        assert p._last_response_id is None
        p.state = State.THINKING
        p.think("Hello Penny")

        assert p._last_response_id is not None
        assert p._last_response_type is not None
