# Test Quarantine Notes

**Last updated:** May 29, 2026

A bare `pytest` runs the **canonical suite** — the curated Weeks 8.5–13 feature
tests (~408 tests, 100% green, ~2s warm). This is the "397/397" suite the
project tracks. The exact file list lives in `pytest.ini` (`testpaths`).

Everything else in `tests/` is legacy/experimental and is **not** run by default.
This file records why, so nothing is silently lost.

## How to run the excluded tests

```bash
pytest tests --run-slow      # collect & run EVERYTHING, including the below
pytest tests/test_foo.py     # run any single file explicitly (always works)
```

`--run-slow` is defined in `conftest.py`; without it the files below are skipped
at collection time.

---

## 1. Slow / import-unsafe (hang at collection — live LLM, audio, full boot)

These open real resources at import time, so they hang a normal machine.

| File | Why |
|------|-----|
| `test_chunked_recording.py` | opens a real audio input stream |
| `test_comprehensive_system_diagnostic.py` | boots the whole stack |
| `test_nemotron.py` | hits the live local LLM |
| `test_week8_integration.py` | live integration |
| `test_week8_live.py` | live integration |
| `test_audio_devices.py` | enumerates real audio hardware |
| `test_audio_quality.py` | real audio processing |

## 2. Quarantined (pre-existing breakage — NOT regressions from recent work)

Each needs a triage decision (fix vs delete). Listed in `conftest.py`
(`QUARANTINE_FILES`) with the same reasons.

| File | Why | Suggested action |
|------|-----|------------------|
| `test_basic.py` | `OpenAICompatLLM.generate()` removed (API drift) | update to current adapter API |
| `test_context_emotion.py` | cannot import `ConversationContext` (renamed/removed) | update import / delete |
| `test_essential_tool_servers.py` | imports `emergency_stop` (renamed `multi_channel_emergency_stop`) | update import |
| `test_penny_chat.py` | reads from stdin at import (interactive script) | not a unit test — delete or guard |
| `test_research_integration.py` | imports `enhanced_conversation_pipeline.py`, which has a **syntax error** | fix/rewrite that module (see below) or delete test |
| `test_gpt_smoke.py` | requires `openai` package (not installed) | `pip install openai` or delete |
| `test_performance_integration.py` | requires `aiohttp_cors` package (not installed) | `pip install aiohttp_cors` or delete |

## 3. Live-network test files (run but make real HTTP calls)

Not gated, but they rely on a reachable local LLM endpoint and will fail/timeout
(30s cap via `pytest.ini`) when offline. Consider mocking or marking `slow`:
`test_openai_compat_llm.py`, `test_openai_compat.py`, `test_improved_adapter.py`,
`test_health_monitor.py`, `test_penny_doctor.py`, `test_pipeline_debug.py`,
`test_detailed_pipeline_debug.py`, `test_personality_actually_works.py`,
`tests/integration/*` (spawn `factual_research_manager` event loops).

---

## Known source-code issue surfaced during triage

`enhanced_conversation_pipeline.py` has a genuine **indentation/syntax error**
around the conversational-flow `try/except` (~lines 277–300): the method body is
at 12 spaces but the block dedents to 8 mid-method. Because of this it was **not**
restored to the repo root — it remains only in `experiments/`. It is not imported
by the active pipeline (`research_first_pipeline.py` imports fine without it), so
it does not affect runtime. It needs a proper rewrite before it can be revived;
the only thing that imports it is the quarantined `test_research_integration.py`.
