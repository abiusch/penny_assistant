# Penny reliability work — handoff to Claude

Snapshot: September 7, 2026. Repository: `abiusch/penny_assistant`.
Read `NEXT_PHASE_TASKS.md` for current status; this handoff is a dated summary.

## Direction

CJ asked Codex to review the existing project and improve reliability and
efficiency. The approach is small, tested fixes to everyday conversation behavior
before adding more subsystems. Preserve useful existing architecture and tests;
do not enable disabled learning features as a side effect. CJ reviews and merges
the PRs. Keep `NEXT_PHASE_TASKS.md` current as work and merges progress.

The audit covered repository history, primary entry points, tools, memory,
consent, personality, model selection, CI, roadmap documents, and the available
local Claude session. It did not read every historical chat or every source line.
The complete audit is `docs/reviews/2026-09-06_project_review.md` (15 findings).
Its eight isolated defect probes load the historical revision `dc416fa` through
Git; passing those probes reproduces the old defects, not current correctness.

## Merged work

- [PR #32](https://github.com/abiusch/penny_assistant/pull/32): replace fragile
  brace-regex tool parsing with complete JSON decoding; support nested arguments;
  report malformed/unknown tools explicitly; replay actual tool calls and results
  into subsequent model prompts. Previously the model repeatedly received the
  original prompt without the tool result. Add real parser/orchestrator/pipeline
  regression coverage, isolate pipeline construction/storage, run all 30 offline
  characterization checks in CI, declare pytest-timeout, and use the project
  virtualenv for `make test`.
- [PR #33](https://github.com/abiusch/penny_assistant/pull/33): accept bare JSON
  tool envelopes observed from local LM Studio in addition to channel-wrapped
  output. Synthetic live verification with `openai/gpt-oss-20b`: `347 * 29`
  executes the registered calculator once and returns **10,063** in two model
  calls. No saved conversations or private memory were used.
- [PR #34](https://github.com/abiusch/penny_assistant/pull/34): preserve the audit
  and historical reproduction evidence in the repository.
- [PR #35](https://github.com/abiusch/penny_assistant/pull/35): replace SIGALRM
  synchronous timeouts, which failed in request threads, with a short-lived Python
  worker that is killed and reaped on timeout. Keep validation and atomic shared
  rate accounting in the caller. Replace calculator `eval` with bounded arithmetic;
  add 34 focused cases and Windows tool-safety CI. Live synthetic calculator
  verification also passes from a request thread. Local validation at that point:
  **534 passed, 2 existing expected failures, plus 30 characterization checks**.

Latest confirmed merged main revision before the current work: `9725d7b` (#35).
These live checks establish the synthetic tool round trip; they do not establish
full live web/audio behavior or concurrent conversation isolation.

## Current work: PR #36, pending review/merge

[PR #36](https://github.com/abiusch/penny_assistant/pull/36), branch
`codex/model-error-handling`, implementation commit `f380afc`:

- The OpenAI-compatible adapter previously returned provider exception text and
  the entire internal prompt as an ordinary answer when a request failed. It now
  raises a shared `ModelGenerationError` for request failures or unusable responses.
- The tool loop propagates generation failure. ResearchFirstPipeline returns a
  fixed retry message, enters speaking state, and skips failed assistant-turn
  persistence, success metrics, response tagging, and personality processing of
  failed generation. Empty post-processed replies are rejected too. A subsequent
  successful request recovers and saves normally.
- Failure after a completed tool does not trigger another generation attempt or
  rerun the tool. Pre-generation bookkeeping, research, and completed tools are
  not rolled back; this is not an atomic transaction for all turn effects.
- The base voice pipeline returns the same failure reply instead of echoing the
  user's input. Remove the full-prompt debug preview; generation-error diagnostics
  omit provider details. The general pipeline error reply also omits exception
  text, while its diagnostic traceback remains available.
- Successful chat and legacy text completions remain supported. Tool-parse and
  tool-execution fallback replies retain their existing behavior.

This intentionally changes the failure contract. One characterization previously
asserted the exception leak; it now explicitly asserts a sanitized reply. Do not
describe this correction as a behavior-preserving refactor.

Local verification: **569 passed, 2 existing expected failures**, all **30**
offline pipeline characterizations, and three updated legacy adapter assertions.
There are **35 new canonical cases**, including real adapter → orchestrator →
pipeline failures from request threads in both A/B groups, failure after tool use,
recovery, and empty output. **30 of the initial 32 cases failed before the fix.**
Failures use mocked requests and synthetic data; no live service was stopped.
The whole legacy test collection was not run. GitHub CI and Claude review were
still running when this handoff was prepared; check the PR's latest commit before
recommending merge.

## Next priorities and boundaries

1. Finish review and merge of #36 after the latest checks pass.
2. Resolve configuration and data roots independently of launch directory; verify
   root, `web_interface/`, and unrelated-directory launches. Do not automatically
   combine existing stores: identify and back up distinct stores before migration.
3. Enforce emotion-tracking consent at durable storage and implement actual
   revoke/delete behavior across affected stores, including restart verification.
4. Follow up on divergent voice/web/text entry points, shared mutable web request
   state, reproducible installation, and crash-safe memory persistence.
5. Later address feature-flag wiring, dependency/path injection, A/B feedback
   attribution, and conversation/clarification/restart continuity.

The two Week 15 expected failures still represent unfinished enforcement.
Synchronous workers support trusted importable functions with JSON inputs/results;
closures, bound instances, in-process state mutation, and child-spawning tools are
outside the current contract. The worker is a timeout boundary, not a security
sandbox. Disabled learning remains disabled. Runtime performance beyond the
synthetic tool checks has not been comprehensively benchmarked.

## Validation commands

Run from the repository root with the project dependencies installed:

```bash
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 make test
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 PENNY_DISABLE_HEALTH_LOOP=1 PYTHONPATH=src .venv/bin/python -m pytest tests/test_pipeline_characterization.py tests/test_pipeline_characterization_extended.py --run-slow --tb=short
```

Keep integration tests offline and inject temporary storage and fake expensive
dependencies before constructing the pipeline. Verify real application data is
unchanged. Read the current diff and latest checks; historical test counts and
older task recaps do not prove a newer revision is ready to merge.
