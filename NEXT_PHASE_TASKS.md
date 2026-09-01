# NEXT_PHASE_TASKS.md

> ⚠️ **SINGLE SOURCE OF TRUTH**
> 
> This file is the **primary reference** for Penny's development status.
> All major documentation files are in the root directory.
> 
> 🎯 **Current status:** [CURRENT_STATUS.md](CURRENT_STATUS.md)  
> 📋 **Detailed roadmap:** [ROADMAP.md](ROADMAP.md)  
> 📚 **Project overview:** [README.md](README.md)

**Last Updated:** September 1, 2026

---

## 🎯 QUICK STATUS

**⏭️ Week 14 (Platform Abstraction Layer) substantively complete (Sep 1, 2026) — audio-output abstraction (#27) + VAD import guard (#28). Next: Week 15 (Capability Awareness).**  

**Current:** Phase 5 in progress — Week 14 substantively complete (audio-output #27, VAD guard #28). R1 `think()` decomposition COMPLETE (PRs #15–#23)  
**Next:** Week 15 (Capability Awareness System, 2026 Risk 5). R4/R5/R2 remain in Week 16; calendar cross-platform in Week 18  
**Phase 4:** ✅ 100% Complete  
**Phase 5:** 🔄 In progress (Weeks 14-18 — Polish & Productization); Week 14 substantively complete  
**Server:** 🟢 Port 5001  
**Tests:** 🟢 463 canonical (~2s) + 29 `think()` characterization (`--run-slow`)  
**Diagnostics:** 🟢 18/18 passing  
**CI:** 🟢 stabilized — runs the canonical suite; 6 pre-existing bugs fixed (see Aug 5 recap below)  
**LLM:** gpt-oss-20b via LM Studio (localhost:1234), config-driven multi-model  
**Last Commit:** `0e8c784` (R1 step 6: PostTurnProcessor extraction, #23)

---

## 📅 SESSION RECAP — August 5, 2026 (CI Stabilization + Characterization Expansion)

None of the bugs below were caused by recent work — they were latent failures
exposed once CI was actually examined. As of today, **"verified locally" and
"green in CI" mean the same thing for the first time.**

### 🟢 CI fully stabilized — 6 pre-existing bugs found and fixed

1. **PyObjC breaks Linux CI** (PR #8, merged) — `pyobjc-core` + 4 framework
   packages were listed unconditionally in `requirements.txt`; they have no
   Linux wheels ("PyObjC requires macOS to build"). Added
   `; platform_system == "Darwin"` markers to all five.
2. **psutil undeclared** (PR #9, merged) — imported unguarded in 4
   operational-security modules (`multi_channel_emergency_stop`,
   `rate_limiting_resource_control`, `lm_studio_performance_monitor`,
   `runaway_process_detector`) but never declared. "Worked" locally only because
   it happened to be installed. Added to `requirements.in`/`.txt`.
3. **sentence-transformers / faiss-cpu / cryptography undeclared** (PR #10, open)
   — same pattern (imported by `embedding_generator`, `vector_store`,
   `encryption`). Adding them forced two transitive-consistency fixes:
   **`cffi` → 2.0.0** (cryptography 46.0.3 requires cffi>=2.0.0) and
   **`setuptools<81`** (see follow-ups). Verified with a from-scratch
   `--no-cache-dir` clean install: **0 conflicts, 17/17 characterization,
   451 canonical.**
4. **ci.yml overrode the canonical suite** (PR #11, merged) — the test job ran
   `pytest tests/`, and a positional path **overrides `pytest.ini`'s
   `testpaths`**, so CI silently collected **136 files** (incl.
   quarantined/legacy) instead of the intended **22-file canonical suite**.
   Fixed to bare `pytest`. **Root-cause fix** — this is exactly why "verified
   locally" (`make test`) and "green in CI" had diverged.
5. **test_tts_cache.py wrong path** (PR #13, merged) — ci.yml ran
   `python test_tts_cache.py` at repo root, but commit `c8a0ea9` (pre-Week-8.5
   cleanup) moved it to `tests/`. Fixed the path; verified it still passes 3/3.
6. **SoT PRD recovered** (PR #12, merged) —
   `docs/specs/SOURCE_OF_TRUTH_SYSTEM_PRD.md` (278 lines) existed only in an
   uncommitted git stash, never on any branch — one `stash drop` from permanent
   loss. Committed it properly, and fixed a now-stale "`think()` has ZERO test
   coverage" claim inside the doc.

**Merged today:** #8, #9, #11, #12, #13. **Open:** #10 (clean-install deps).

### 🧪 Characterization tests: 5 → 17

An autonomous agent added **12 extended tests** on top of the 5 base tests —
research success/failure paths, financial disclaimer, judgment clarify-gate,
A/B personality gating, resilience, and documented quirks.
(`tests/test_pipeline_characterization.py` +
`tests/test_pipeline_characterization_extended.py`, run with `--run-slow`.)

### 🤖 Autonomous agents (CI workflows)

- **Characterization test writer** (`.github/workflows/characterization-tests.yml`)
  — manual trigger, **additive-only** (writes tests, never touches production code).
- **Background code reviewer** (`.github/workflows/code-reviewer.yml`) —
  auto-runs on every PR, **read-only** (comments only, never edits code).
- **Dependency watchdog** (`.github/workflows/dependency-watchdog.yml`) —
  just built; weekly schedule + manual trigger; checks for vulnerabilities with
  clean-install + marker-preservation verification before proposing any fix.

### 📌 New known follow-ups (not urgent — don't lose track)

- **`mcp_protocol_foundation.py` broken import guard** — the
  `try/except ImportError` catches the error, then crashes anyway on
  unconditional use of the now-undefined names a few lines later. It doesn't
  actually degrade gracefully. (Same non-functional-guard pattern as
  `MultiChannelEmergencyStop` / `PredictiveSecurityAnalytics`.)
- **`GoogleTTS.speak()` silently accepts an `output_file` kwarg it doesn't
  handle** — surfaced as warnings during the TTS cache test (test still passes).
  Worth a look.
- **`setuptools<81` is a temporary pin** — the real fix is updating/replacing
  `webrtcvad` (unmaintained; depends on deprecated `pkg_resources`, which
  setuptools 81+ removed).

### ✅ Status: R1 is now genuinely unblocked

Not just "tests exist" — verified end-to-end: clean install works, the canonical
suite runs correctly in CI, and characterization tests gate real `think()`
behavior. **Next session's priority: start the actual `think()` decomposition (R1).**

---

## 📅 SESSION RECAP — August 25, 2026 (R1 COMPLETE — `think()` Decomposed)

**R1 is done.** The 572-line `think()` God Object is now an orchestrator of six
named, independently-verified phases. Each piece was extracted as its own
reviewed PR — never a big-bang rewrite.

### ✅ R1 complete — `think()` decomposed into 6 pieces

| Piece | Extraction | PR |
|-------|-----------|-----|
| Financial disclaimer | `_apply_financial_disclaimer` (module-level pure fn) | **#15** |
| Prompt assembly | `_build_and_generate` + `PromptContext` dataclass | **#17** |
| Research classification | `_classify_and_research` + `ResearchOutcome` dataclass | **#18** |
| Judgment/clarify gate | `_judgment_gate` (short-circuit stays visible in `think()`) | **#19** |
| Input processing | `_input_prehooks` + `_process_emotion` (bracket the gate) | **#21** |
| Post-turn processing | `_persist_turn` + `_record_ab_metrics` + `_tag_response_for_next_turn` | **#23** |

### 🔬 How each extraction was done (the discipline that made it safe)

Every step followed the same loop — **no exceptions**:
1. **Map before cutting** — a read-only investigation of exact boundaries,
   data-flow (what escapes to `self.*` / downstream), and entanglement.
2. **Close coverage gaps first** — where a branch was untested, new
   characterization tests were landed *before* the extraction, in their own
   prep PRs: **#16** (PromptBuilder), **#20** (InputProcessor: emotional
   check-in + enabled learning hooks), **#22** (PostTurnProcessor: dual-save
   content, snapshot, forgetting, Hebbian wiring, `mark_followed_up`, A/B
   computation, outcome tagging).
3. **Faithful move only** — bodies relocated **byte-for-byte** (verified via
   `difflib` after dedent), no behavior change, `self.*` side effects and
   try/except seams preserved.
4. **Reviewed + real CI** — automated code reviewer on every PR, verified green
   against actual CI (3.11 + 3.13), not just "verified locally."

**Characterization suite grew 17 → 29** along the way (5 base + 24 extended,
`--run-slow`). The canonical 451-suite was unaffected by any extraction (the
characterization files live outside `testpaths`, gated behind `--run-slow`).

**Net result:** `think()` reads as a sequence of phase calls — input pre-hooks →
judgment gate → emotion/continuity → research → prompt/generate → financial
disclaimer → persist → A/B metrics → response tagging — each testable in
isolation, each a named method instead of an inline block.

### 📌 Consolidated follow-up list (everything flagged "not now" across R1 + Week 14)

None of these block anything; captured here so they aren't lost:

1. **Leaked exception text** in `think()`'s outer fallback response (returns
   `...Error: {str(e)}` to the user — should not surface raw exception text).
2. **`conversation_history` hardcoded to `[]`** — the judgment/research paths
   receive an always-empty history instead of real conversation context.
3. **Duplicated log line in `_should_clarify()`** — the same clarify decision is
   logged twice.
4. **`mcp_protocol_foundation.py` non-functional import guard** — `try/except
   ImportError` catches, then crashes anyway on unconditional use of the
   now-undefined names. Same pattern as `MultiChannelEmergencyStop` /
   `PredictiveSecurityAnalytics`.
5. **PyObjC markers only in `requirements.txt`, not `requirements.in`** — the
   `; platform_system == "Darwin"` markers will be lost on the next
   `pip-compile` (drift risk).
6. **`setuptools<81` pin is temporary** — the real fix is replacing/updating
   `webrtcvad` (unmaintained; depends on deprecated `pkg_resources`, removed in
   setuptools 81+).
7. **Hebbian timing test flakiness** (`test_latency_under_10ms` /
   `test_vocab_observation_latency`) — has now tripped CI enough times
   (latest: 52.38ms vs a hard-coded 50ms threshold on a 3.11 runner) to warrant
   a **real fix** (loosen the threshold or quarantine it), not another
   re-diagnosis. It is machine-speed noise, unrelated to the code under test.
8. **Boston Dynamics hardcoded example** in the research-failure response
   template — a stale, domain-specific example baked into a generic template.
9. **`GoogleTTS.speak()` silently accepts an unhandled `output_file` kwarg** —
   surfaced as warnings during the TTS cache test (test still passes).
10. **`src/audio/listener.py` has an unguarded `import webrtcvad`** — the same
    crash-on-import issue the adapter had (fixed in #28), in a different module.
    Same fix pattern, not yet applied. *(Week 14)*
11. **`is_speech()` in `webrtc_vad_adapter.py` is a stub** — returns
    `len(audio_bytes) > 160` and never uses the real `webrtcvad.Vad` object, so
    it isn't actually doing voice-activity detection. Needs a proper
    implementation (correct frame sizing + `vad.is_speech`). *(Week 14)*
12. **Calendar cross-platform support deferred to Week 18** — `osascript`/
    AppleScript calendar access is real macOS *functionality*, not a primitive
    swap, so it belongs with the Windows/Linux porting work, not the abstraction
    layer. *(Week 14, by design)*
13. **~15 experimental root `penny_*.py` entry scripts not ported** — deemed
    low-value (they use already-cross-platform `sounddevice`); not worth the
    ripple. *(Week 14, by design)*

---

## 📅 SESSION RECAP — September 1, 2026 (Week 14 — Platform Abstraction Layer)

**Week 14's two high-value slices are done.** Per the read-only investigation,
the OS-specific surface that actually mattered was audio playback and the
unguarded VAD import; both are now abstracted/guarded with graceful degradation.
Everything else was already cross-platform or explicitly deferred (below), so
Week 14 is **substantively complete**.

### ✅ Completed slices

| Slice | What | PR |
|-------|------|-----|
| Audio-output abstraction | `build_playback_command()` + `play_audio_file()` (`src/adapters/audio/playback.py`) — afplay/mpg123/ffplay by OS (all MP3-capable, unlike aplay/paplay/winsound); 4 TTS adapters wired **argv-only** (barge-in/timeout/killall untouched); loud `UnsupportedPlatformError` on unknown OS | **#27** |
| WebRTC VAD import guard | `try/except ImportError` + `VAD_AVAILABLE`; `WebRTCVAD` degrades (no crash) when webrtcvad is missing/broken; callers can check `.available`; `is_speech()` left byte-identical | **#28** |

Same discipline as R1: **tests first** (mocked, no hardware), faithful/minimal
changes, reviewed + real CI, `research_first_pipeline.py` untouched. Canonical
suite grew **451 → 463** (+8 audio, +4 VAD guard); characterization still 29.

### ✅ Scope check — nothing missed

The original Week 14 definition is one line ("Abstract OS-specific code with
graceful degradation"). The investigation enumerated the full OS-specific
surface; each item is now done or explicitly deferred:
- **Audio playback** → done (#27).
- **VAD import guard** → done (#28).
- **Audio input** (`sounddevice`/PortAudio) → already cross-platform.
- **Platform detection** (`system_info.py`) → already branches correctly.
- **Calendar** (`osascript`) → deferred to **Week 18** (macOS functionality, not
  a primitive swap). See follow-up #12.
- **~15 root `penny_*.py` entry scripts** → low-value, not ported. Follow-up #13.
- **Stop/`killall` playback interruption** + **`is_speech()` stub** +
  **`listener.py` unguarded import** → follow-ups #10/#11 (and the #27 stop-abstraction note).

Follow-ups #10–#13 captured in the consolidated list above.

---

## 🔧 ACTIVE WORK: REFACTORING (In Progress)

### **Architecture Audit Completed** (Late June 2026)

Full senior-engineer audit performed. See `PENNY_ARCHITECTURE_AUDIT.md` (committed).

**Grade: C+** — Subsystems are A-grade, orchestration wiring is D-grade.

**Top 3 findings:**
1. 🟡 **God Object:** `research_first_pipeline.py` is 1,167 lines; `think()` is 572 lines. Now has a safety net (5 characterization tests) + structured logging (R6). Ready for R1 decomposition.
2. 🔴 **Root directory chaos:** ~150 Python files at root level. Already caused regressions.
3. 🔴 **Mixed imports:** Code split between root, `src/`, `src/core/` with `sys.path` manipulation.

### **Refactoring Progress:**

| Phase | What | Status | Notes |
|-------|------|--------|-------|
| **R3** | Config unification | 🟡 Partial | LLM registry done (`src/llm/registry.py`). Feature flags still hardcoded in pipeline |
| **R6** | Structured logging | ✅ Done | 50 `print()` → `logger` (info/debug/warning/error); banner + `__main__` kept |
| — | DB path injectable | ✅ Done | `ResearchFirstPipeline(db_path=, data_dir=)` routes storage (semantic store, snapshots, judgment logs, PersonalityTracker, MilestoneTracker); temp-dir verified |
| — | `think()` characterization tests | ✅ Done | 5 tests (`tests/test_pipeline_characterization.py`, `--run-slow`): state guard, happy path, prompt assembly, never-raises, temp isolation |
| **R1** | Pipeline decomposition | ✅ **Done (Aug 25, 2026)** | `think()` → 6 phases across PRs #15/#17/#18/#19/#21/#23 (prep tests #16/#20/#22). Byte-faithful moves, characterization 17→29. See Aug 25 recap |
| **R4** | DB connection pooling | 🅿️ **Parked (investigated Aug 25, 2026)** | Read-only investigation found the premise is incorrect: **no leaks or exhaustion exist.** Every connection is opened per-operation and safely closed (`with self._get_conn() as conn:` + refcount GC; zero persistent held connections). The app is single-threaded (Flask `app.run`, no `threaded=True`) / single-user — **no concurrent DB access.** Naive pooling would risk **introducing** real bugs (SQLite thread-affinity violations, lock contention) to fix a problem that doesn't exist. **Recommend R4 stay parked** unless real profiling data ever justifies it. |
| **R5** | Async cleanup | ⏸️ Week 16 (small-scope only) | Real but small: **consolidate the repeated event-loop creation** in the personality-update path (`_update_personality_from_conversation` spins up/tears down a fresh loop 5× per turn) — **NOT** converting `think()` to async (that's viral across Flask routes / `chat_entry` / all callers). The 5 updates write the same DB, so ordering is delicate (parallelizing risks lock races). Needs its **own dedicated investigation + a targeted test** before any edit — same discipline as R1. Remove unnecessary `asyncio.run()` calls. |
| **R2** | Source tree cleanup | ⏸️ Later | Move ~150 root files → `src/`. Highest regression risk, defer |

**Quick wins already completed:**
- ✅ `think()` characterization tests — 5 tests, pipeline no longer untested (`fb25410`)
- ✅ R6 structured logging — 50 `print()` → `logger` (`0fa94d1`)
- ✅ DB path injectable — enables characterization tests (`34abc75`)
- ✅ Config-driven LLM registry — multi-model support (`9edd8de`)
- ✅ Deleted throwaway artifacts (`24385f6`)
- ✅ Moved 19 `commit_*.sh` to `experiments/legacy/`
- ✅ Established canonical test suite (`conftest.py`, `pytest.ini`, `make test`)
- ✅ Added `.gitignore` rules for runtime artifacts
- ✅ Documented test exclusions in `QUARANTINE_NOTES.md`

### **⚠️ Critical Note for AI Assistants:**

`research_first_pipeline.py` `think()` now has a **characterization safety net** — 5 tests in `tests/test_pipeline_characterization.py` (run with `pytest tests/test_pipeline_characterization.py --run-slow`). These lock CURRENT behavior, not desired behavior. When doing R1 decomposition, **run them after every extraction step** and keep them green — a diff there means you changed pipeline behavior. The canonical 451-suite still covers subsystems only, so it will NOT catch pipeline regressions on its own.

---

## 🎉 PHASE 4 COMPLETE: ADVANCED LEARNING (Weeks 8.5-13)

### **Full System Stack (Production-Ready):**

| Week | System | Tests | Status |
|------|--------|-------|--------|
| 8.5 | Judgment & Clarify | 63 | ✅ Production |
| 9 | Hebbian Learning Core (3 components) | 75 | ✅ Production |
| 10 | Hebbian Integration + Safety Systems | 62 | ✅ Production |
| 11 | Outcome Tracking + Proactivity Budget | — | ✅ Production |
| 12 | Goal Continuity | — | ✅ Production |
| 13 | User Model + 2026 Enhancements | 97 | ✅ Production |
| — | Integration, diagnostics, refactor additions | 154 | ✅ Passing |
| **Total** | | **451** | **100%** |

---

## ✅ COMPLETED WORK (January — June 2026)

### **Refactoring & Infrastructure** (Late June 2026)
**Status:** 🔄 In Progress

**R6 Structured Logging (`0fa94d1`):**
- Converted 50 diagnostic `print()` → `logger` in `research_first_pipeline.py`
- 13 info, 29 debug, 6 warning, 2 error
- Preserved user-facing startup banner and `__main__` demo as `print()`
- Stripped `flush=True` from converted calls (logger rejects it)
- No logic change

**DB Path Injectability (`34abc75`):**
- `ResearchFirstPipeline(db_path=..., data_dir=...)` — defaults to real `data/`
- Routes all hardcoded paths: personality_tracking.db, vector store, snapshots, judgment logs
- Proven: temp `data_dir` creates isolated storage — `think()` can run without polluting real data
- Enables characterization tests (next step)

**Config-Driven LLM Registry (`9edd8de`):**
- New `src/llm/registry.py`: `create_llm`, `resolve_model_config`, `available_models`
- Standardized on OpenAI-compatible serving
- `penny_config.json` → `llm.active_model` + `llm.models` dict
- Active model: gpt-oss-20b via LM Studio (localhost:1234)
- Registered models: qwen3-8b, llama-3.1-8b (config-only switching)
- Graceful Nemotron/Ollama fallback chain
- Pipeline `self.llm` now built from config (was hardcoded)

**Canonical Test Suite:**
- `conftest.py`: puts `src/` on path, `--run-slow` gate for network/audio tests
- `pytest.ini`: 30s signal-timeout, explicit `testpaths` list = canonical suite
- `make test` = canonical (451 tests, ~2s)
- `make test-all` = everything including quarantined legacy tests
- Documented exclusions in `QUARANTINE_NOTES.md`
- Resolved: "397 passing" was never bare `pytest` — it was curated feature tests only

**Regression Fixes (`a85b92e`):**
- Restored 16 modules to root broken by experiments/ cleanup
- Fixed `EnhancedSecurityLogging` NameError in `security_performance_integrator.py`
- Rebuilt corrupted `personality_tracking.db`
- Fixed "frustrating" → anger emotion gap
- Diagnostics: 8/11 → 18/18

---

### **Week 13 Enhancement: 2026 Memory Architecture Alignment** (May-June 2026)
**Status:** ✅ COMPLETE (`1517d42`, +31 new tests)

**5 Critical Fixes Applied (based on 2026 AI best practices research):**

**Fix 1: Beliefs Wired Into LLM Responses (+4 tests)**
- `build_context_snippet()` now injected into pipeline prompt
- Relevance + confidence filtered, capped at 5 beliefs per turn
- Penny now USES what she learns about you (previously dead code)

**Fix 2: Belief Staging / Quarantine (+7 tests)**
- New `belief_staging` table — no single-observation permanent beliefs
- Promotion requires: 3+ observations across 3+ days
- `BeliefExtractor(use_staging=)` flag, default off for back-compat; pipeline opts in
- Addresses Risk 3 (Belief Pollution)

**Fix 3: Temporal Decay (+4 tests)**
- `apply_temporal_decay()` for idle-phase processing
- Below 0.3 confidence → archived (restorable)
- New `belief_archive` table

**Fix 4: Cross-System Integration (+12 tests)**
- New `belief_integration.py` with tested helpers
- 4a: Beliefs → Judgment context (**WIRED LIVE** in pipeline)
- 4b: Outcomes → Belief reinforcement/weakening (tested, not yet hooked)
- 4c: Hebbian → Belief creation on promotion (tested, not yet hooked)
- 4d: Safety → Belief write gating (tested, pluggable `can_write` gate)

**Fix 5: Contradiction Detection (+4 tests)**
- `detect_contradictions()` + `check_before_write()`
- Blocks conflicting beliefs before write

**⚠️ 4b/4c/4d Scope Note:** Implemented as tested helpers in `belief_integration.py`.
Not yet called from their subsystems — each is one function call from being live.
CC noted the hooks referenced in the spec don't exist in those subsystems yet;
wiring would require small edits to outcome_tracker, hebbian_learning_manager, and
user_belief_store. Deferred for now — decide when to prioritize.

---

### **Week 13: User Model**
**Status:** ✅ COMPLETE (66 base + 31 enhancement = 97 tests)

- `UserBeliefStore` — Subject-predicate-object triple store with confidence
- `BeliefExtractor` — Regex-based extraction from conversations
- Correction/audit system, staging, decay, contradictions
- Performance: 0.09ms/query

---

### **Weeks 11-12: Outcome Tracking, Goal Continuity**
**Status:** ✅ COMPLETE

- OutcomeTracker, strategy success rates, reaction detection
- ProactivityBudget (2 nudges/day, 1 resurrection/week, 0.8 confidence gate)
- GoalTracker, FollowUpEngine (gated by ProactivityBudget)

---

### **Weeks 9-10: Hebbian Learning + Safe Integration**
**Status:** ✅ COMPLETE (75 + 62 = 137 tests)

- 3 Hebbian components (vocabulary, dimension, sequence)
- HebbianLearningManager orchestration
- Safety: quarantine, turn budgets, mini-observability
- Performance: 3.12ms avg (<10ms target)

---

### **Week 8.5: Judgment & Clarify System**
**Status:** ✅ COMPLETE (63 tests)

- Detection (vague referents, stakes, params, contradictions, confidence)
- Personality layer (PennyStyleClarifier, 30+ templates)
- Pipeline integration with judgment logging

---

### **Repository Maintenance** (January + May-June 2026)

- **Jan 2026:** Organized 200+ files
- **May-June 2026:** Fixed regressions from experiments/ cleanup (16 modules restored), rebuilt corrupted DB, established canonical test suite, added `.gitignore` for runtime artifacts

---

## 🚀 PHASE 5: POLISH & PRODUCTIZATION (Weeks 14-18)

### **Week 14: Platform Abstraction Layer** — ✅ Substantively complete (Sep 1, 2026)
Abstract OS-specific code with graceful degradation. **Done:** audio-output
abstraction (#27), WebRTC VAD import guard (#28). **Deferred:** calendar → Week 18;
root entry scripts (low-value); stop/killall + `is_speech()` stub + `listener.py`
guard → follow-ups #10–#13. See the Sep 1 recap.

### **Week 15: Capability Awareness System**
Penny knows and communicates her own capabilities. Hard enforcement at orchestrator level (2026 Risk 5).

### **Week 16: Repository Organization (Part 2) + Pipeline Decomposition**
**This is where R1/R4/R5 happen:**
- R1: Decompose God Object `research_first_pipeline.py` → 7 composable processors
- R4: DB connection pooling (6+ connections → 1 shared pool)
- R5: Remove unnecessary `asyncio.run()` calls
- Clean source tree, collapse docs, performance profiling

### **Week 17: Penny Console (Observability Dashboard)**
Full dashboard extending mini-observability from Week 10.

### **Week 18: Cross-Platform Support**
Windows + Linux compatibility.

---

## 💡 PHASE ∞: OPTIONAL ENHANCEMENTS (Post-Week 18)

### **Email-Based AI Insights System (APPROVED - Phase 0 Testing)**
✅ ChatGPT approved. Process AI newsletters via Gmail API.
**Phase 0:** Manual testing. **Phase 1 (Post-18):** Automated digest (3-4 hours).
**Proposal:** `EMAIL_BASED_AI_INSIGHTS_PROPOSAL.md`

### **Memory Service Orchestration Layer**
Unify existing memory systems (working, episodic, semantic, procedural) into tiered architecture with entity linking and hierarchical retrieval.
**Effort:** 8-12 hours | **Priority:** HIGH

### **Active/Inactive Phase Processing**
Move expensive operations (decay, promotions, drift checks) to idle time. ~50% per-turn overhead reduction.
**Effort:** 3-4 hours | **Priority:** MEDIUM-HIGH

### **Model Evaluation: Reasoning Model Upgrade**
Evaluate Qwen3-30B-A3B, DeepSeek-R1-Distill for hybrid model routing.
**Note:** LLM registry (`src/llm/registry.py`) now supports config-only model switching — evaluation is infrastructure-ready.
**Effort:** 2-3 hours eval, 4-6 hours integration | **Priority:** MEDIUM

### **Persistent Agent Capabilities**
Background awareness loop with calendar/goal notifications, gated by proactivity budget.
**Effort:** 4-6 hours | **Priority:** LOW

---

## 🛡️ 2026 AI FAILURE MODE MITIGATIONS

| Risk | Mitigation | Status |
|------|-----------|--------|
| **1. Learning Drift** | Hebbian quarantine (5 obs, 7 days) | ✅ Week 10 |
| **2. Runaway Autonomy** | Proactivity budgets (2/day, permission gates) | ✅ Week 11 |
| **3. Belief Pollution** | Belief staging (3 obs, 3 days) + contradiction detection | ✅ Week 13 |
| **4. Late Observability** | Mini-observability (drift detection, learning logs) | ✅ Week 10 |
| **5. Capability Bypass** | Hard enforcement at orchestrator level | ⏳ Week 15 |
| **6. Latency Balloon** | Turn budgets (5 writes, 20 lookups, 15s max) | ✅ Week 10 |

---

## 📊 SYSTEM STATUS SUMMARY

### **Active Systems:**
- **LLM:** gpt-oss-20b via LM Studio (localhost:1234). Config-driven multi-model registry (`src/llm/registry.py`). Registered: qwen3-8b, llama-3.1-8b. Fallback: Nemotron/Ollama.
- **Memory:** Conversation vectors (AES-128 encrypted)
- **Personality:** 7 dimensions, active learning
- **Emotional Intelligence:** Week 8 (7-day memory, 0.8 intensity threshold)
- **Judgment:** Week 8.5 (63 tests, production-ready)
- **Hebbian Learning:** Weeks 9-10 (137 tests, safe integration)
- **Outcome Tracking:** Week 11 (strategy learning, reaction detection)
- **Goal Continuity:** Week 12 (unfinished business tracking)
- **User Model:** Week 13 (beliefs, staging, decay, contradictions, 97 tests)
- **Proactivity Budget:** Active (2 nudges/day, permission gates)
- **Safety:** Active (quarantine, turn budgets, observability)
- **Security:** GDPR Article 17, encrypted, PII-protected
- **Server:** Port 5001, stable

### **Performance:**
- Response Time: 5-10s (local LLM)
- Hebbian Latency: 3.12ms (<10ms target)
- Belief Query: 0.09ms
- Canonical Test Suite: 451 tests (~2s)
- Diagnostics: 18/18
- Cost: $0/month (100% local)

---

## 🏗️ DEVELOPMENT STRATEGY (CRITICAL)

### **Single-Threaded Development (No Agent Swarms Until Post-Week 18)**

Swarm orchestration improves dev tooling (Layer 2), NOT cognitive architecture (Layer 1). Velocity multipliers are dangerous before foundations are hardened.

**Current approach:** User + Claude Code = coherent vision, quality over speed

> "Direction > Speed during foundation building"

**Future trigger:** Reconsider for parallelizable work post-Week 18. Never for core architecture.

---

## 🎯 FOR AI ASSISTANTS (CRITICAL INSTRUCTIONS)

**1. ALWAYS READ FIRST:** This file → CURRENT_STATUS.md → ROADMAP.md

**2. CURRENT STATUS:**
- Phase 4 COMPLETE (451 tests). R6 logging + DB injectability done. Characterization tests next.
- LLM is now config-driven multi-model via `src/llm/registry.py`
- `research_first_pipeline.py` `think()` has ZERO test coverage — do NOT refactor without characterization tests

**3. ARCHITECTURE:**
- Single-threaded development, direction > speed
- Safety-first (judgment → learning → staging → permanent)
- See `PENNY_ARCHITECTURE_AUDIT.md` for full audit and R1-R6 refactoring roadmap

**4. TEST SUITE:**
- `make test` = canonical suite (451 tests, ~2s)
- `make test-all` = includes quarantined legacy tests
- See `QUARANTINE_NOTES.md` for excluded tests and reasons
- `conftest.py` handles path setup and `--run-slow` gating

**5. LLM CONFIGURATION:**
- Active: gpt-oss-20b via LM Studio (localhost:1234)
- Config: `penny_config.json` → `llm.active_model` + `llm.models`
- Registry: `src/llm/registry.py` — `create_llm()`, `available_models()`
- Do NOT add more models without user approval

**6. 2026 ALIGNMENT (Verified June 2026):**
- 🟢 AHEAD: Judgment, local-first, personality, anti-drift, safety, observability
- 🟡 WATCH: Memory architecture (tiered/graph enhancement planned)
- 🟡 ADD: Active/inactive phase processing
- 🟡 EVALUATE: Reasoning models (post-Week 18)

**7. NEVER REFERENCE:** `/docs/archive/`, `/experiments/` (except 16 restored modules), old roadmaps

**8. EXTERNAL REVIEWS:** Manus, ChatGPT (×3), Perplexity — all processed

---

## 🔄 RECENT UPDATES

- **September 1, 2026:** Week 14 (Platform Abstraction Layer) substantively complete — audio-output abstraction (#27) + WebRTC VAD import guard (#28). Canonical 451→463. See Sep 1 recap
- **August 25, 2026:** R1 COMPLETE — `think()` decomposed into 6 phases (PRs #15/#17/#18/#19/#21/#23, prep tests #16/#20/#22). Byte-faithful moves, characterization 17→29. See Aug 25 recap
- **August 5, 2026:** CI fully stabilized (6 pre-existing bugs fixed), characterization 5→17. See Aug 5 recap
- **Late June 2026:** R6 structured logging (`0fa94d1`) + DB injectability (`34abc75`). Characterization tests next
- **Late June 2026:** Config-driven LLM registry (`9edd8de`), canonical test suite, refactor quick-wins, 451 tests
- **Late June 2026:** Architecture audit completed (`PENNY_ARCHITECTURE_AUDIT.md`)
- **May-June 2026:** Week 13 2026 Enhancement (+31 tests), regression fixes (diagnostics 18/18)
- **January 28, 2026:** Weeks 9-10 complete (safe integration, 199 tests)
- **January 18, 2026:** Week 8.5 complete (judgment system, 73 tests)
- **January 16, 2026:** Repository cleanup (200+ files)

---

**Last Updated:** September 1, 2026  
**Maintained By:** CJ  
**Status:** ✅ Phase 4 COMPLETE · R1 COMPLETE · Phase 5 Week 14 substantively complete. Next: Week 15 (Capability Awareness) 🚀
