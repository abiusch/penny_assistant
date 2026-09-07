# Penny project review — September 6, 2026

**Recommendation:** prioritize reliable, consistent everyday conversations before adding another major subsystem. The recent refactoring is useful, but several connections between otherwise tested components remain broken. Fixing those connections should improve both behavior and efficiency more than another model, framework, or broad rewrite.

## Implementation update after the audit

[PR #32](https://github.com/abiusch/penny_assistant/pull/32) merged fixes for
findings 1–2 and the tool/pipeline test coverage gap in finding 8.
[PR #33](https://github.com/abiusch/penny_assistant/pull/33) adds the live-model
compatibility fix described below. Local validation for that follow-up is
**499 passed, 2 existing expected failures**, plus all **30** offline pipeline
characterization checks. The project virtualenv now has its declared dependencies
installed and `pip check` passes; pytest-timeout is declared.

A synthetic live check against LM Studio's `openai/gpt-oss-20b` revealed that it
returns bare JSON tool envelopes. The parser now accepts those as well as the
documented channel-wrapped format. For `347 * 29`, the registered calculator ran
once and the model answered **10,063** on its second call, using the returned
result. This did not access saved conversations or personal memory. Audio and
other model output variants were not verified. The worker-thread timeout defect
remains open, so this does not yet establish working calculator calls from the
web interface.

The findings and baseline below preserve the **pre-fix audit snapshot**. They
are not a statement that every original defect remains on the PR branch. PRs
#30 and #31 were subsequently confirmed merged, and #32 was based on the updated
`main`. Findings not explicitly covered above remain recommendations for follow-up.

## Original audit: scope and evidence

Reviewed the repository inventory, development history, primary entry points, conversation orchestration, tools, memory, consent, personality, model selection, test configuration, CI, and recent architecture/roadmap documents. Also inspected the available local Claude project session: user requests spanning May–September 2026, recent assistant conclusions, and saved project memory. Older work is represented by repository history and documents; this is not a claim to have read every historical chat or every line of 501 Python files.

The repository has 855 tracked files, including 501 Python files, 176 Markdown files, and 173 Python files at the root. Syntax parsing of all tracked Python files found two errors, both under `experiments/`; no syntax errors were found elsewhere.

The reviewed checkout was **`fix/hebbian-timing-thresholds` at `dc416fa`**, not `main`. Local `main` was `aadaca9`. I additionally reviewed the local **`test/week15-capability-baseline`** branch diff. Claude's session identified these as PRs #31 and #30 respectively; live GitHub status was not queried during the initial audit. No branches were switched or merged during that audit.

Validation:

| Check | Observed result |
|---|---|
| `.venv/bin/python -m pytest --tb=short` | **463 passed in 3.56 seconds**, eight warnings |
| Full-pipeline characterization collection, both files, `--run-slow` | **Fails with two collection errors**: missing `psutil` leads to undefined `MultiChannelEmergencyStop` in the import guard |
| Current environment | Flask, Flask-CORS, FAISS, and pytest-timeout absent; the traceback also establishes that psutil is absent |
| Eight isolated defect probes | **All eight defects reproduced**, without constructing the pipeline or accessing user databases, audio, a model, or the network |
| Tracked Python syntax scan | Two errors in archived experiments |

The probes are in [2026-09-06_review_probes.py](2026-09-06_review_probes.py). Run them from the project root with `.venv/bin/python docs/reviews/2026-09-06_review_probes.py`. They deliberately confirm defects at the audited revision `dc416fa`, loaded read-only with `git show` so subsequent fixes do not invalidate the historical evidence. The local Git object database must contain `dc416fa`; a shallow clone or a checkout without that historical branch may not. Their passing result is **not** a clean bill of health for the current code. Some execute unchanged methods extracted from the source with fake dependencies, so they verify the specific behavior rather than a complete application launch.

The initial audit changed only these review artifacts. It did not install dependencies, run live inference, inspect conversation databases, or benchmark actual response latency. Subsequent implementation and validation are described in the update above.

## What is worth keeping

- **The recent small refactors.** R1 split a large method into understandable phases while preserving behavior. That was a sensible way to reduce regression risk. It is a useful intermediate step; dependencies and mutable state still live on one large pipeline class.
- **The configuration-driven model registry.** Adding another compatible model can remain a configuration change. Consolidate the remaining launch paths around it.
- **The focused learning components.** Belief staging, correction handling, proactivity budgets, and outcome tracking have substantial targeted tests. Preserve these interfaces while fixing runtime wiring.
- **The fast default suite.** A 3.56-second feedback loop is valuable. Keep it and add a separate deterministic integration gate, instead of indiscriminately re-enabling every old test.
- **The decision to separate experimental code.** The previous import regressions show why further moves should follow dependency mapping and launch tests.

## Findings, ordered by practical importance

### 1. Tool results never reach the model on the next iteration — high priority

In [research_first_pipeline.py:642](../../research_first_pipeline.py#L642), `orchestrator_llm_gen(context)` ignores `context` and always calls the model with the same `final_prompt`. The orchestrator correctly appends tool results to its history, but this adapter discards them.

**Reproduced:** an offline calculator request caused three identical prompts, three tool executions, and the “rephrase” fallback. The tool's result appeared in none of the model prompts. With a nondeterministic model, the precise outcome can vary, but it still cannot answer from the omitted result.

**Improve:** pass the evolving conversation to the model, including the tool call and result. Keep application instructions distinct from user and external content. Add a test where the fake model returns a final answer only after it sees the actual result. This directly reduces wasted model calls, repeated searches, and rate-limit consumption.

### 2. The advertised tool format cannot be parsed — high priority

The pipeline tells the model to output `{"tool":"tool_name","args":{...}}`. [tool_orchestrator.py:53](../../src/tools/tool_orchestrator.py#L53) uses a non-greedy brace regex that stops at the first closing brace. Nested arguments therefore produce incomplete JSON. Even fixing brace matching would leave `_map_tool_name` and execution arguments inconsistent with the explicit `tool`/`args` envelope.

**Reproduced:** the exact nested format is classified as a final answer, not a tool call. The registry separately advertises a different flat format, so the model receives conflicting instructions.

**Improve:** define one structured tool-call contract, decode complete JSON, validate name and arguments, and reject unknown names explicitly instead of guessing `web.search`. Test nested arguments, braces inside strings, malformed JSON, unknown tools, and one complete tool round trip.

### 3. Calculator timeouts fail in web request threads — high priority

[tool_safety.py:241](../../src/tools/tool_safety.py#L241) uses `signal.signal(SIGALRM, ...)` for synchronous tools. **Reproduced:** a valid wrapped calculator call from a worker thread raises `ValueError: signal only works in main thread of the main interpreter` before executing.

This matters because [server.py:217](../../web_interface/server.py#L217) calls `app.run()` without disabling threads. Flask enables threaded mode by default; the roadmap's assertion that absence of `threaded=True` makes the server single-threaded is incorrect. [Flask API documentation](https://flask.palletsprojects.com/en/stable/api/#flask.Flask.run).

The wrapper also cancels its alarm only on normal completion and never restores the previous signal handler. A validation error or rate-limit exception can leave an alarm armed. On platforms without SIGALRM, it runs without a timeout.

**Improve:** use bounded expression evaluation and an execution mechanism that can actually stop expensive work across supported platforms. Do not treat a timeout on a waiting thread as termination of the underlying calculation. Add worker-thread and exception-cleanup tests.

### 4. Emotional tracking opt-out does not govern stored emotion data — high priority

[research_first_pipeline.py:883](../../research_first_pipeline.py#L883) always includes emotion, confidence, sentiment, and sentiment score in persistent metadata. Consent currently gates emotional continuity/check-ins, not this write. [consent_manager.py:128](../../src/memory/consent_manager.py#L128) accepts `delete_data=True`, but only updates preferences and an audit event; it invokes no deletion mechanism.

**Reproduced:** `_persist_turn` passes emotion metadata to storage while tracking is disabled. Revoking with deletion requested only changes consent records. These are application-behavior findings, not a legal compliance assessment.

**Improve:** enforce consent at the storage boundary and wire deletion to actual stores. Define whether the setting controls derived emotion metadata, raw conversation retention, or both. Test revoke/delete followed by application restart. If emotional context is retained elsewhere, deletion needs to cover those copies too.

### 5. A model outage returns the entire internal prompt as the answer — high priority

[openai_compat.py:86](../../src/adapters/llm/openai_compat.py#L86) catches request failures and returns `[llm error] ...` followed by the entire prompt. That prompt can contain retrieved conversations, beliefs, and internal instructions. It is returned as a normal string, so downstream code can also persist it as an assistant response.

**Reproduced:** a simulated request failure returned a synthetic private-memory marker from the prompt.

**Improve:** return a typed failure or raise a controlled exception; show a short user-facing error without prompt contents. Prevent failed generations from being counted as successful answers or used as learning material. The pipeline's outer exception response should also stop exposing raw exception text.

### 6. Launch location changes the configuration and memory Penny uses — high priority

[web_interface/start.sh](../../web_interface/start.sh) and the canonical web instructions change into `web_interface/`. [registry.py:36](../../src/llm/registry.py#L36) loads `penny_config.json` relative to the current directory. Pipeline storage and many subsystem defaults similarly use relative `data/...` paths.

**Reproduced:** loading configuration from the root finds the LLM settings; loading from `web_interface/` returns the fallback empty LLM configuration. The same relative storage paths resolve to a separate web data directory. Adding the parent to `sys.path` does not fix either issue.

**Improve:** resolve config and application-data roots once, independently of the working directory, then pass those paths to every subsystem. Verify launch from root, web directory, and an unrelated directory. Do not automatically combine existing data directories; identify and back up distinct stores before any migration.

### 7. The canonical voice entry bypasses the companion pipeline — high priority

[penny.py:19](../../penny.py#L19) transcribes audio and calls `get_llm()` directly. Text chat and web use `ResearchFirstPipeline`. The voice path shares a persona filter but does not pass through the newer research, memory, judgment, or learning orchestration. Text chat's `memory stats` and `search memories` commands still call `base_memory`/`enhanced_memory`, which were removed from the research pipeline.

**Improve:** expose one conversation service shared by voice, web, and text. Keep microphone/playback in the voice adapter. Replace obsolete memory commands with the current memory API. Verify the same conversation facts and model selection across each entry point, including restart.

### 8. The green CI suite does not gate the full pipeline — high priority

[pytest.ini:17](../../pytest.ini#L17) lists selected feature tests; the two characterization files are outside that list and gated behind `--run-slow`. [ci.yml](../../.github/workflows/ci.yml) runs the default suite, a narrow import smoke check, and a TTS script, but never explicitly runs those characterization files. Coverage is scoped to `src`, excluding the root-level research pipeline.

The characterization fixtures also replace the real orchestrator with a single-call stub, which explains why findings 1–2 survive those tests. Their isolation check compares filenames only **after construction**, so it cannot detect modifications to existing files or writes during construction.

**Improve:** retain the curated unit suite and add a named offline integration suite to CI. Inject expensive dependencies before construction; retain the real prompt builder, parser, orchestrator, and storage boundaries in contract tests. Include successful tool use, model failure, consent, restart, and each entry point. Test desired behavior alongside characterization; preserving old behavior alone cannot establish correctness.

### 9. Installation and test commands do not describe one reproducible environment — high priority

Flask and Flask-CORS are absent from the repository's requirements lists despite the canonical web server importing both. `pytest.ini` promises timeouts, but pytest-timeout is undeclared and absent here; pytest reports the timeout settings as unknown. FAISS and psutil **are declared**, but missing from this particular `.venv`; distinguish environment drift from missing declarations. The web start script may install Flask separately, but that does not make the standard dependency install sufficient.

`make test` invokes ambient `pytest` even though Makefile defines a virtualenv Python. Multiple requirements sets overlap, and packaging discovers only `core*` and `adapters*`, leaving newer packages and root modules outside the distribution.

**Improve:** choose one supported installation path, declare web/test dependencies, run tests through that environment's Python, and verify clean install plus actual entry-point import/startup in CI. Later, define core/web/voice/development extras and finish package discovery incrementally. This is a better investment than another round of one-off dependency fixes.

### 10. Memory persistence can silently lose data and becomes more expensive as it grows — high priority

[vector_store.py:146](../../src/memory/vector_store.py#L146) overwrites the entire FAISS index and metadata file after each add, in two separate writes. Save failures are logged and swallowed. Load failures reset the in-memory store to empty, allowing a later add to overwrite remaining recoverable files. Separate running applications load independent snapshots and can overwrite each other's additions.

**Reproduced:** the actual save method returns no failure indication after a simulated disk error. The crash-consistency and multiple-writer concerns follow from source inspection; no production store was damaged or modified to test them.

**Improve:** use a transactional durable record of conversations and treat the vector index as rebuildable derived data. Alternatively, introduce an explicit generation/checkpoint protocol and a single writer. Merely renaming each of the two files atomically does not make their pair atomic. Surface durability failures and test restart, interrupted writes, corruption recovery, and simultaneous writers.

Each turn currently writes a growing history. With similar-sized turns, this implies approximately quadratic cumulative write volume over the lifetime of the store; actual latency was not benchmarked. Keep durable conversation appends synchronous, and checkpoint/rebuild the search index separately with explicit recovery.

### 11. Web requests share mutable turn state — medium/high priority

[server.py:47](../../web_interface/server.py#L47) constructs one global pipeline. Requests share conversation context, research status, state-machine state, and outcome identifiers. Two tabs or a retry can overlap even for one person. Serializing only database writes would not protect that state. Research also owns a background event-loop thread.

**Improve:** as a small first step, serialize complete turns with a bounded queue and clear busy behavior. Longer term, return turn-local results and metadata, and assign context to a conversation/session. Keep durable memory updates under a single owner. Do not introduce SQLite pooling based on either the older “six connections must be bad” claim or the newer “no concurrency exists” claim.

Also, a SQLite connection context manager handles transactions; it does not itself close the connection. Use explicit lifetime management where needed and profile before selecting pooling. [Python sqlite3 documentation](https://docs.python.org/3.13/library/sqlite3.html#how-to-use-the-connection-context-manager).

### 12. Several completed learning features cannot be enabled through configuration — medium priority

[research_first_pipeline.py:236](../../research_first_pipeline.py#L236) hardcodes Hebbian learning, outcome tracking, goal continuity, and user modeling off. Judgment is hardcoded on. Changing a flag after construction does not construct its required objects. The README's broad “all implemented” wording therefore does not describe enabled runtime behavior.

**Improve:** resolve validated feature configuration before construction. Keep defaults conservative; enabling learning is a product choice, not an incidental audit fix. Show configured, available, and active states separately. Add config-to-object wiring tests for each feature and dependency combination.

### 13. Isolation and storage injection remain incomplete — medium priority

The pipeline injects a path into its primary tracker, but constructs prompt/post-process builders, consent manager, and global A/B machinery with their own defaults. [DynamicPersonalityPromptBuilder](../../src/personality/dynamic_personality_prompt_builder.py#L43) constructs additional trackers if none are supplied. [personality_tracker.py:539](../../personality_tracker.py#L539) uses a global cache keyed only by `"default"`, so distinct tracker databases can return the same cached state.

**Improve:** create one dependency bundle with explicit paths and lifecycle, share the intended tracker, and scope caches by store and user. Isolated tests should prove both that existing production files are untouched and that two independent data roots do not share state. Avoid constructing the full real pipeline before replacing its dependencies.

### 14. Current A/B results cannot establish that adaptation improves answers — medium priority

[think()](../../research_first_pipeline.py#L1058) creates a new conversation ID each turn. [adaptation_ab_test.py:53](../../src/personality/adaptation_ab_test.py#L53) assigns treatment with probability 0.5, so adaptation can switch on and off from one reply to the next. [_record_ab_metrics](../../research_first_pipeline.py#L997) counts praise/complaints in the **input preceding the answer being evaluated**. “That was wrong” therefore gets attached to the newly assigned group, not necessarily the group that produced the previous answer. The LLM adapter also adds a personality prompt independently, so “control” is not a complete absence of personalization.

**Improve:** make experimentation explicit and optional. Use stable session assignments, tie feedback to the response it evaluates, and use held-out conversations or blinded paired comparisons. Keep ordinary use consistent. Do not infer improvement from positive-word counts or the number of passing tests.

### 15. Conversation continuity is weaker than the feature descriptions imply — medium priority

Judgment receives an empty history at [research_first_pipeline.py:743](../../research_first_pipeline.py#L743); research receives `[]` too. Clarification returns before persisting the exchange, so the next turn lacks that interaction in the conversation cache. Research status also is not reset before the clarification early return, allowing the web response to inherit stale research metadata.

[EmotionalContinuity](../../src/memory/emotional_continuity.py#L136) begins with an empty thread list; tracking and follow-up marking mutate it in memory. The reviewed pipeline does not restore that list at startup. Snapshots alone do not implement automatic cross-session continuity.

**Improve:** use one bounded conversation history for judgment, research, and generation; persist clarification turns without implying an answer was produced; initialize metadata per turn. Store/restore emotional thread state only when consent allows it, using the same stable turn ID as conversation storage. Test “clarify → answer,” “follow-up pronoun,” and “restart → remember/follow up.”

## Efficiency improvements worth measuring

| Improvement | Evidence and expected benefit | Measurement |
|---|---|---|
| Fix the tool round trip first | Confirmed repeated model calls and tool execution | Model calls and tool calls per successfully completed request |
| Lazy-load optional models and audio | `ResearchFirstPipeline` constructs the audio base pipeline; transformer emotion detection initializes even with tracking off | Cold/warm startup time and resident memory for text, web, and voice |
| Compute emotion once per turn | `track_emotion()` calls detection, then `detect_intensity()` runs detection again | Emotion inference count and milliseconds per consented turn |
| Incremental durable writes; separate index checkpoint | Whole-history index and metadata rewritten after each addition | Write volume and p50/p95 save latency at 100/1,000/10,000 synthetic turns |
| Build one bounded prompt | Personality instructions are assembled in both pipeline and adapter; history/research have no shared token budget | Input tokens, time to first output, answer quality on the same scenarios |
| Reuse a turn's personality snapshot | Several components read the same state; the update path creates multiple event loops | Database operations and orchestration time excluding model/research latency |
| Add streaming after correctness | Current web request waits for generation and post-turn work before responding | Time to first visible text vs total turn time; cancellation behavior |

Do not move persistence into an untracked background task merely to make responses appear fast. Durability, ordering, and shutdown must remain defined. Similarly, avoid model switching or connection pooling until a repeatable benchmark identifies a real bottleneck.

## Review of the pending Week 15 work

The local `test/week15-capability-baseline` branch adds five passing-baseline tests, two strict expected-failure tests, and a slow manifest-in-prompt test. Recording an explicit unfinished invariant is useful; `xfail` is not completed enforcement.

Improve the next implementation in these ways:

- Generate advertised capabilities and executable dispatch from the same structured tool specifications, including availability and denial reason. Distinguish registered, disabled, and executable tools; `code.execute` is registered but blocked by validation.
- Replace the test's 200-character prose scan with structured metadata checks. Iterating only registered candidate names cannot discover extra unregistered tools advertised in the manifest.
- Prove validation and timeout behavior at the actual dispatch boundary, including a request thread. Wrapper identity alone does not prove an action is safely executable.
- Cover the real parser and model/tool/result loop. Capability-list equality does not fix findings 1–3.
- Remove expected-failure markers when implementation lands, and run the pipeline test in an actual CI job.

These changes fit the intent of Week 15 better than building a separate large capability framework.

## A more efficient development sequence

1. **Establish the runnable baseline.** One environment, absolute config/data roots, complete dependency injection, and an offline integration CI job. Completion: the canonical launch paths resolve the same settings, isolated data stays isolated, and a synthetic conversation completes without real services.
2. **Repair tools and failure handling.** One parser contract, evolving model history, request-safe execution limits, and typed model errors. Completion: “calculate 2+2” executes once and answers from the returned result; unavailable/invalid tools and model outages degrade cleanly.
3. **Make memory and consent dependable.** Consent-aware writes/deletion, explicit durability, one writer, and restart tests. Completion: saved conversations survive restart and simulated save failures; opt-out/delete behaves as described.
4. **Unify voice/web/text and activate features intentionally.** Reuse the conversation service, replace stale memory commands, wire configuration, and finish the narrow Week 15 capability contract. Completion: the same scenario works across interfaces with explainable feature state.
5. **Measure and optimize.** Lazy initialization, duplicate emotion work, prompt size, incremental index checkpoints, then streaming. Use a fixed scenario set and track p50/p95 instead of promising unmeasured speedups.

Keep changes small, but let each change deliver a verified behavior. Your Claude history repeatedly spends separate sessions rediscovering test scope, confirming counts, and investigating CI timing. A single repeatable verification command that records commit, interpreter, selected tests, results, and feature state would reduce that coordination cost.

The existing Source-of-Truth PRD points in a useful direction, but start smaller: an offline inventory of resolved paths, effective flags, available tools, and test commands. Avoid building its full monitoring/dashboard system before the application contracts work. Any optional endpoint health checks should be explicit and bounded.

## Documentation and smaller follow-ups

- Rewrite the README around the verified launch path and actual enabled features. Several quick-start files have moved, and the status page links to missing `CURRENT_STATUS.md` and `ROADMAP.md`.
- Keep a short current-status block and append-only historical log. Older roadmap sections still schedule completed R1 work and pooling that later sections parked. Claude's saved test-count memory is also stale.
- Treat “implemented,” “unit-tested,” “integrated,” “enabled,” and “verified in an actual session” as separate statuses. Many current claims collapse them together.
- Preserve the timing-threshold fix as a loose shared-CI guard, but create a separate performance benchmark if sub-10ms behavior matters. A 250–300ms threshold is not evidence of meeting a single-digit-millisecond target.
- Use relative web API URLs (`/chat`, `/personality`): hardcoded `localhost:5001` points to the visitor's own computer when network access is enabled. Restrict CORS to the intended UI origin, and define authentication before broadening access.
- Surface unavailable audio-player binaries as a capability state. The new playback abstraction is useful; platform command selection alone does not prove audio is installed and working.
- Keep archived syntax errors and obsolete scripts out of production imports; retire/move them only after checking dependents. Do not undertake another bulk reorganization as the first improvement.

The best next milestone is an ordinary conversation that uses a tool correctly, retains permitted memory, survives restart, and behaves consistently across interfaces—with those behaviors enforced automatically. That would turn much more of the work already completed into reliable value.
