# NEXT_PHASE_TASKS.md

> ⚠️ **SINGLE SOURCE OF TRUTH**
> 
> This file is the **primary reference** for Penny's development status.
> All major documentation files are in the root directory.
> 
> 🎯 **Current status:** [CURRENT_STATUS.md](CURRENT_STATUS.md)  
> 📋 **Detailed roadmap:** [ROADMAP.md](ROADMAP.md)  
> 📚 **Project overview:** [README.md](README.md)

**Last Updated:** May 29, 2026

---

## 🎯 QUICK STATUS

**Current:** Week 13 COMPLETE! 🎉 (Phase 4 done)
**Next:** Streaming TTS + Barge-In (🔴 HIGH PRIORITY voice UX — see AI Landscape Review)
**Phase 3:** 100% complete (Weeks 8.5–11 done)
**Phase 4:** 100% complete (Weeks 12–13 done)
**Server:** 🟢 Port 5001
**Tests:** 🟢 397/397 passing (100% pass rate!)
**Diagnostics:** 🟢 18/18 (week6 suite) — restored 2 modules lost in cleanup, rebuilt corrupt tracking DB

---

## 🎉 MAJOR MILESTONE: WEEK 8.5 COMPLETE!

### **Judgment & Clarify System - PRODUCTION READY**

**Completed:** January 18, 2026

**Final Stats:**
- ✅ **73/73 tests passing (100%)**
- ✅ **2,400+ lines of production code**
- ✅ **All 3 phases complete**
- ✅ **Committed and pushed to GitHub**

**What We Built:**

**Phase 1: Detection Layer (43 tests)**
- 5 detection methods: vague referents, stakes, missing params, contradictions, confidence
- 893 lines of code in `judgment_engine.py`
- ~4 hours implementation time

**Phase 2: Personality Layer (18 tests)**
- PennyStyleClarifier with 30+ templates
- Frustration detection
- All questions in Penny's authentic voice
- 368 lines of code
- ~2 hours implementation time

**Phase 3: Pipeline Integration (12 tests)**
- Integrated into `research_first_pipeline.py`
- Judgment logging system
- Configuration options
- Demo script with 9 scenarios
- ~4 hours implementation time

**Total Effort:** ~10 hours (under the 15-20 hour estimate!)

**Why This Matters:**
> "Once judgment exists, not every subsystem has to be perfect. Week 8.5 fundamentally changes the risk profile." - ChatGPT External Review

**All future learning is now PROTECTED:**
- ✅ Hebbian Learning won't learn from vague inputs
- ✅ Outcome Tracking gets clear, unambiguous data
- ✅ Goal Continuity has well-defined tasks
- ✅ User Model builds correct beliefs

---

## ✅ RECENTLY COMPLETED (January 16-28, 2026)

### **Week 9: Hebbian Learning - Core Components** (January 28, 2026)
**Status:** ✅ COMPLETE (75/75 Hebbian tests + 63 Week 8.5 tests = 138 total)

**What Was Built:**

**Component 1: Vocabulary Associator (24 tests)**
- Learns word-context associations via Hebbian strengthening
- Example: "ngl" → casual contexts (0.85), not formal (0.12)
- Temporal decay for old patterns
- 400 lines of code

**Component 2: Dimension Associator (15 tests)**
- Learns personality dimension co-activation patterns
- Example: emotional_support → brief_responses (0.72)
- Multi-dimensional pattern detection
- 380 lines of code

**Component 3: Sequence Learner (22 tests)**
- Learns conversation flow patterns (12 states)
- Example: problem → clarification → solution
- Predicts next conversation states
- 500 lines of code

**Integration (14 tests)**
- All 3 components working together
- Data persistence validated
- Performance: 5ms overhead (<10ms target)
- Statistics and export functions

**Total:** ~1,280 lines of production code, 75 tests, 138 total with Week 8.5

**Final Commit:** 526d61e - "Week 9 Hebbian Learning - Core Components Complete"

**Protected by:** Week 8.5 Judgment System (no learning from vague inputs)

**What Penny Learned:**
- Vocabulary patterns (word-context associations)
- Personality patterns (dimension co-activations)
- Conversation patterns (state transitions)

---

### **Repository Cleanup** (January 16, 2026)
- ✅ Organized 118 test files → `tests/`
- ✅ Moved 35 experimental scripts → `experiments/`
- ✅ Archived 41 completed docs → `docs/archive/phases/`
- ✅ Consolidated 27 databases → `data/`
- ✅ Split requirements into core/platform/optional
- ✅ Created `.env.example` and `MINIMAL_SETUP.md`
- ✅ Created `ENTRY_POINTS.md` for canonical entry points
- ✅ Committed and pushed to GitHub (c8a0ea9)

**Why this was critical:**
> "Root directory sprawl will directly hurt velocity if not cleaned" - External reviews (unanimous)

### **Week 8.5: Judgment & Clarify System** (January 18, 2026)
**Status:** ✅ COMPLETE (73/73 tests passing)

**Phase 1: Detection Layer**
- Vague referent detection (10 tests)
- Stakes assessment (HIGH/MEDIUM/LOW)
- Missing parameter detection (20 tests)
- Contradiction detection (13 tests)
- Confidence assessment (0.0-1.0 scoring)
- **Total: 43/43 tests, 893 lines**

**Phase 2: Personality Layer**
- PennyStyleClarifier (368 lines)
- 30+ templates in Penny's voice
- Frustration detection
- Context hints
- **Total: 18/18 tests, 735 lines**

**Phase 3: Pipeline Integration**
- research_first_pipeline.py integration (+110 lines)
- Judgment logging system
- Configuration options (penny_config.json)
- Demo script with 9 scenarios
- **Total: 12/12 tests**

**Final Commit:** ddfd369 - "Week 8.5 Phase 3: Pipeline Integration - COMPLETE!"

**Examples of Judgment in Action:**
```
User: "Fix that thing"
Penny: "Quick check—which thing specifically?"

User: "Delete all test data"
Penny: "Wanna make sure I nail this—you mean ALL items?"

User: "What's 2+2?"
Penny: "4" (no clarification needed)
```

---

## ✅ COMPLETED: WEEKS 10 & 11

### **Week 10: Hebbian Integration** (January 31, 2026) - COMPLETE
- ✅ HebbianLearningManager orchestration layer (36 tests)
- ✅ Learning Quarantine system (staging → permanent promotion)
- ✅ TurnBudget safety limits (5 writes, 20 lookups, 15s)
- ✅ Mini-observability (drift detection, reports, export)
- ✅ Pipeline integration with feature flag
- ✅ **199/199 tests passing**

### **Week 11: Outcome Tracking** (February 27, 2026) - COMPLETE
- ✅ OutcomeTracker (auto-detect reactions, strategy success rates)
- ✅ ProactivityBudget (Risk 2 safety: 2 nudges/day, 1 resurrection/week)
- ✅ Pipeline integration (turn-start detection, turn-end tagging)
- ✅ **272/272 tests passing** (+73 new tests)

### **Week 12: Goal Continuity** (February 27, 2026) - COMPLETE
- ✅ GoalTracker (`src/personality/goal_tracker.py`) — 29 tests
- ✅ FollowUpEngine (`src/personality/followup_engine.py`) — 17 tests
- ✅ Integration (`test_goal_continuity_integration.py`) — 13 tests
- ✅ **331/331 tests passing** (+59 new tests)
- ✅ Commit: `04d2308` — pushed

**How it works:**
```
Turn: "I want to set up monitoring"
  → GoalTracker detects goal, stores as active

[next session, 3 days later]
FollowUpEngine: "Hey, still working on set up monitoring?"
  → ProactivityBudget confirms: 1 nudge used (1 remaining today)
```

---

## ✅ WEEK 13 USER MODEL — COMPLETE (May 2026)

**Goal:** Penny maintains explicit, inspectable beliefs about CJ — confidence scores per belief, user-correctable. ✅ DONE.

**What shipped (commit `4d82a94`, 397/397 tests):**
- `src/personality/user_belief_store.py` — SQLite triple store (subject→predicate→object_value) with typed `Predicate` vocabulary, Bayesian confidence (BASE 0.5, +0.08/evidence, MAX 0.97), correction audit trail. Tables: `user_beliefs`, `belief_evidence`, `belief_corrections`.
- `src/personality/belief_extractor.py` — high-precision regex extraction per predicate, `build_context_snippet()` for prompt injection, `detect_correction()`.
- Pipeline integration at Step 1.2 (feature flag `user_model_enabled`, default false).
- Tests: 28 + 24 + 14 = 66 new.

**⚠️ Carry-over from the KG recommendation (see Idea #1 below):** The store is a *triple store* (graph-shaped: subject→predicate→object), which satisfies the typed-belief goal, but it does **not yet expose graph traversal** (multi-hop queries). Two-path RAG was deferred — it needs a query layer on top of these triples. Logged as a Phase 5 medium-priority item.

---

## 🚀 NEXT UP: STREAMING TTS + BARGE-IN  (🔴 HIGH PRIORITY)

**Goal:** Cut perceived voice latency 50–70% by speaking the first sentence while the rest of the response is still generating, and let CJ interrupt mid-utterance.

**Status:** 🎯 READY TO START

**Why Now:**
- ✅ Phase 4 learning systems complete (Weeks 12–13) — voice UX is now the highest-leverage gap.
- ✅ Substantial scaffolding already exists (see audit below) — this is wiring + a sentence pump, not a rebuild.
- 2026 gold standard: sub-300ms first-audio latency + real-time interruption.

**📋 Audit of what already exists (May 2026):**
- `src/adapters/tts/streaming_tts_adapter.py` — `StreamingTTS` with a playback queue, `stop_playback` Event, and `stop()`. NOTE: today it streams *playback of pre-generated phrase files*, not LLM-token-driven sentences.
- `allow_barge_in` param is already threaded through every TTS adapter (Google, ElevenLabs, cached).
- `src/core/pipeline.py` already has `handle_barge_in()` + `barge_in_enabled` + a SPEAKING state.
- `voice_activity_detector.py` exists (silence-based VAD) — reusable for barge-in detection.
- GAP: the real voice loop (`real_time_voice_loop.py`) calls `self.pipeline.speak(response)` with the **full** response — TTS only starts after the LLM finishes. No sentence-level streaming, and VAD is not monitored *during* playback for barge-in.

**Component 1: Sentence-streaming bridge**
- Split LLM output into sentences as they arrive (the pipeline already produces text; need a streaming/generator path or a sentence buffer that flushes on `.!?`).
- Feed each completed sentence to TTS immediately so audio of sentence 1 plays while sentence 2 generates.

**Component 2: Barge-in during playback**
- Run VAD on the mic *while* TTS is playing; on detected speech above threshold, call `tts.stop()`, flush the queue, transition SPEAKING → LISTENING.
- Debounce so Penny's own audio bleed doesn't trigger self-interruption (echo gate / brief cooldown).

**Component 3: Pipeline integration**
- Feature flag: `streaming_tts_enabled` (default false), `barge_in_enabled` (already present).
- Wire into `real_time_voice_loop.py` replacing the single blocking `speak(full_response)`.

**Component 4: Latency measurement**
- Track time-to-first-audio (TTFA) vs current time-to-full-response. Target: TTFA < 1s, ideally < 300ms with cached lead-ins.

**Target:** 30+ new tests (sentence splitter, barge-in state machine, queue flush) → 425+ total.

---

## 🔬 AI LANDSCAPE REVIEW: RECOMMENDATIONS (February 27, 2026)

> Researched by Claude (Cowork) — full report: [PENNY_AI_LANDSCAPE_REVIEW_FEB2026.md](PENNY_AI_LANDSCAPE_REVIEW_FEB2026.md)
>
> **Bottom line:** Penny is architecturally ahead of most personal AI projects. Gaps are refinements, not rebuilds. Two areas deserve near-term action; the rest are Phase 5+.

### 🔴 HIGH PRIORITY (Act in Weeks 12–13)

**Voice UX: Streaming TTS + Barge-In**
- Add **streaming TTS** — begin audio playback as first sentence generates, not after full response. Cuts perceived latency 50–70%. ElevenLabs and Piper both support streaming.
- Add **barge-in support** — detect voice activity during TTS playback, interrupt pipeline, re-listen. Eliminates the "walkie-talkie" feel.
- Estimated effort: 1–2 days each. Transformative UX impact.
- 2026 gold standard: sub-300ms latency + real-time interruption (NVIDIA PersonaPlex pattern)

**Week 13 User Model: Build as Knowledge Graph, not flat store**
- The field has converged on **dual memory**: implicit statistical patterns (Hebbian ✅) + explicit, human-readable facts in a knowledge graph
- Implement User Model as a lightweight KG (NetworkX or SQLite + JSON relationships) so Penny holds queryable, typed beliefs: `CJ → prefers → short answers → context: quick questions`
- Reference: **Mem0** open-source library and **Memoria framework** (arXiv Dec 2025)
- Bonus: exposes **two-path RAG** for free — simple queries use vectors, complex multi-hop queries use KG
- Penny should be able to surface her beliefs on demand: *"Here's what I think I know about you — want to correct anything?"* (no commercial assistant does this)

### 🟡 MEDIUM PRIORITY (Phase 5, Weeks 14–15)

**LLM Benchmark: Nemotron vs. Qwen3-8B / Llama 3.1 8B**
- The 2026 trend has shifted toward smaller, well-quantized models for personal agents
- A 4-bit quantized 8B model runs at 2–4x the tokens/second of a 30B model with surprisingly similar quality on focused tasks
- **Action:** Run Qwen3-8B alongside Nemotron on 20–30 real Penny conversations. Measure response quality, judgment accuracy, and Hebbian signal quality. Only switch if quality holds — latency win would be 5–10s → 1–3s, which is massive for voice.
- Do NOT switch without benchmarking. Penny's personality/judgment is tuned to Nemotron.

**Two-Path RAG (Vector + Knowledge Graph)**
- Once KG memory exists (Week 13), route complex multi-hop queries through graph retrieval
- Simple queries keep the fast vector path; complex queries use KG path
- Microsoft GraphRAG shows +6.4 points multi-hop recall and 18–30% hallucination reduction
- No framework needed — a simple graph query layer on top of existing pipeline

### 🟢 LONGER TERM (Phase 5+, Post-Week 18)

**Full-Duplex Voice** — Simultaneous listen + speak. High impact, high complexity. Research NVIDIA PersonaPlex implementation post-Week 18.

**Multi-Agent Research Tasks** — Penny as orchestrator, spawning specialist sub-agents for deep research or code review. LangGraph or CrewAI patterns. Phase 5+ only.

### ❌ WHAT NOT TO DO

- **Don't rewrite the pipeline in LangGraph** — Penny's custom pipeline already implements what these frameworks offer. Migration cost isn't worth it.
- **Don't switch LLMs without benchmarking first** — personality + judgment are tuned to Nemotron.
- **Don't build the continuous learning scraper** — external review consensus was correct. Defer post-Week 18.

---

## ✅ PHASE 4: ADVANCED LEARNING (Weeks 11-13) — COMPLETE

**Week 11: Outcome Tracking** ✅ COMPLETE
- Tracks whether responses helped or hurt; strategy success rates
- ProactivityBudget hard limits (anti-runaway-autonomy)
- 272/272 tests passing

**Week 12: Goal Continuity** ✅ COMPLETE
- GoalTracker + FollowUpEngine built
- 331/331 tests passing

**Week 13: User Model** ✅ COMPLETE
- Explicit, confidence-scored, user-correctable beliefs (triple store)
- BeliefExtractor + context-snippet injection
- 397/397 tests passing

---

## 🚀 PHASE 5: POLISH & PRODUCTIZATION (Weeks 14-18)

**After core learning systems complete:**

### **Week 14: Platform Abstraction Layer**
**Goal:** Abstract OS-specific code with graceful degradation

**Components:**
- Platform capability registry
- OS-specific plugin architecture
- Graceful degradation patterns

### **Week 15: Capability Awareness System**
**Goal:** Penny knows and communicates her own capabilities

**Inspired by:** ChatGPT external review

**Features:**
- Self-inspection of available features
- Transparent messaging about limitations
- UI showing active/disabled capabilities

### **Week 16: Repository Organization (Part 2)**
**Goal:** Production-ready codebase structure

**Tasks:**
- Collapse documentation into canonical docs
- Remove archived experimental code
- Platform-specific test suites
- Performance profiling

### **Week 17: Penny Console (Observability Dashboard)**
**Goal:** Observability dashboard for Penny's internals

**Inspired by:** Perplexity external review

**Features:**
- Active plugins and disabled reasons
- Recent judgment decisions (from Week 8.5!)
- Memory/Hebbian training events
- Performance metrics

### **Week 18: Cross-Platform Support**
**Goal:** Windows + Linux compatibility

**Inspired by:** Manus external review

**Tasks:**
- Windows calendar alternative
- Linux audio stack testing
- Platform-specific documentation
- Cross-platform CI/CD

---

## 💡 PHASE ∞: OPTIONAL ENHANCEMENTS (Post-Week 18)

### **Continuous Learning System (DEFERRED)**

**Status:** Reviewed by external experts, consensus reached

**External Review Consensus:**
- ✅ Strategic direction is correct (2026 trends validated)
- ⏸️ Defer full system to post-Week 18
- 🔄 Start with minimal approach if needed

**Current Approach:**
- **Phase 0 (NOW):** Use Penny as research assistant
  - You find papers/repos manually
  - Penny summarizes and compares
  - 0 new code, works today

**Future Options (post-Week 18):**
- **If needed:** Build minimal AI digest tool (2-3 hours)
  - Weekly script, manual trigger
  - 2-3 curated sources
  - Penny summarizes
  - No scoring, no auto-roadmap

**Decision Point:** After Week 13
- Evaluate if manual scanning + Penny works
- Build minimal version if gaps identified
- Full system only if minimal proves valuable

**Reviews:**
- Perplexity: "Defer to post-Week 18, start minimal"
- ChatGPT: "Minimal PoC first, full pipeline later"
- Both: "Strategic fit is good, timing is early"

---

## 📊 SYSTEM STATUS SUMMARY

### **Active Systems:**
- **LLM:** Nemotron-3 Nano (30B params, 1M context, $0/month, 100% local)
- **Memory:** 539 conversation vectors (AES-128 encrypted)
- **Personality:** 7 dimensions tracking, 0.74 confidence (technical depth)
- **Emotional Intelligence:** Week 8 active (7-day memory, 0.8 intensity threshold)
- **Judgment System:** Week 8.5 active (73/73 tests, production-ready)
- **Hebbian Learning:** Week 9 active (75/75 tests, core components complete) ⭐ NEW!
- **Security:** GDPR Article 17 compliant, encrypted, PII-protected
- **Server:** Port 5001, stable

### **Performance Metrics:**
- Response Time: 5-10s (acceptable for local LLM)
- Emotion Accuracy: 90%+ on 27 emotions
- Judgment Tests: 73/73 passing (100%)
- Hebbian Tests: 75/75 passing (100%)
- Total Tests: 138 passing
- Cost: $0/month forever

**Complete details:** [CURRENT_STATUS.md](CURRENT_STATUS.md)

---

## 📚 DOCUMENTATION REFERENCE

### **Primary Documents (Root Directory):**

**Status & Planning:**
- **[NEXT_PHASE_TASKS.md](NEXT_PHASE_TASKS.md)** - This file (single source of truth)
- **[CURRENT_STATUS.md](CURRENT_STATUS.md)** - Complete system status
- **[ROADMAP.md](ROADMAP.md)** - Detailed roadmap
- **[README.md](README.md)** - Project overview
- **[MINIMAL_SETUP.md](MINIMAL_SETUP.md)** - New user setup guide
- **[ENTRY_POINTS.md](ENTRY_POINTS.md)** - Canonical entry points

**Week 8.5 Specifications:**
- `CLAUDE_CODE_PHASE1A_PROMPT.md` - Vague referent detection
- `CLAUDE_CODE_PHASE1B_PROMPT.md` - Stakes + missing parameters
- `CLAUDE_CODE_PHASE1C_PROMPT.md` - Contradictions + confidence
- `CLAUDE_CODE_PHASE2_PROMPT.md` - Personality layer
- `CLAUDE_CODE_PHASE3_PROMPT.md` - Pipeline integration
- `WEEK8_5_PHASE3_COMPLETE.md` - Final completion report
- `demo_week8_5.py` - Live demonstration script

**Other Specifications:**
- Hebbian: Check `/hebbian_specs/` or `/docs/specs/hebbian/`
- Week 8: Check root or `/docs/specs/emotional_continuity/`

**Additional Documentation:**
- Guides: `/docs/guides/`
- History: `/docs/progress/2025/`
- Archive: `/docs/archive/`

---

## 🎯 FOR AI ASSISTANTS (CRITICAL INSTRUCTIONS)

### **When helping with Penny development:**

**1. ALWAYS READ FIRST:**
   - ✅ This file (NEXT_PHASE_TASKS.md) - Single source of truth
   - ✅ [CURRENT_STATUS.md](CURRENT_STATUS.md) - Complete current state
   - ✅ [ROADMAP.md](ROADMAP.md) - What's happening next

**2. CURRENT PRIORITY:**
   - ⭐ Week 10: Hebbian Integration (NEXT UP!)
   - Week 9 core components complete
   - Judgment system protects learning

**3. WEEK 9 STATUS:**
   - ✅ COMPLETE - 75/75 Hebbian tests passing
   - ✅ Committed: 526d61e
   - ✅ 3 core components working
   - ✅ 138 total tests passing

**4. FOR WEEK 10 INTEGRATION:**
   - ✅ Create HebbianLearningManager
   - ✅ Connect to research_first_pipeline.py
   - ✅ Feature flag: HEBBIAN_LEARNING_ENABLED
   - ✅ Documentation and polish

**5. NEVER REFERENCE:**
   - ❌ Files in `/docs/archive/` - Outdated/superseded
   - ❌ Files in `/experiments/` - Not production code
   - ❌ Old roadmaps - Use this file only

**6. EXTERNAL REVIEWS COMPLETED:**
   - ✅ Manus (Windows compatibility analysis)
   - ✅ ChatGPT (architecture & risk assessment)
   - ✅ Perplexity (UX & observability insights)
   - ✅ Continuous learning proposal reviewed & deferred

---

## 🔄 MAINTENANCE POLICY

### **This File is Updated:**
- After each completed phase/week
- When priorities change
- When new phases are added
- When external feedback received

### **Recent Updates:**
- **February 27, 2026:** Week 12 Goal Continuity COMPLETE — 331/331 tests, commit 04d2308
- **February 27, 2026:** Added AI Landscape Review section with recommendations (voice UX, KG User Model, LLM benchmark, two-path RAG)
- **January 28, 2026:** Week 9 Hebbian Learning marked COMPLETE! 138/138 tests passing 🎉
- **January 18, 2026 (Evening):** Week 8.5 marked COMPLETE! 73/73 tests passing
- **January 18, 2026 (Afternoon):** Updated with Phase 3 in progress
- **January 18, 2026 (Morning):** Added Phase 1 & 2 completion
- **January 16, 2026:** Added repository cleanup and Week 8.5 start
- **January 16, 2026:** Added Phase 5 (Weeks 14-18) for productization

---

## 📝 QUICK REFERENCE

### **Most Important Files:**
- 🎯 **This file** (NEXT_PHASE_TASKS.md) - Single source of truth
- 📊 [CURRENT_STATUS.md](CURRENT_STATUS.md) - Complete system state
- 📋 [ROADMAP.md](ROADMAP.md) - Detailed plans
- 🚀 [MINIMAL_SETUP.md](MINIMAL_SETUP.md) - New user guide

### **Try the Judgment System:**
```bash
# Run demo to see judgment in action
python demo_week8_5.py

# Test scenarios:
# - Vague: "Fix that thing"
# - High stakes: "Delete all data"
# - Missing params: "Schedule meeting"
# - Clear: "What is Python?"
```

### **Next Work:**
- **START:** Week 10 Hebbian Integration
- **Files:** `src/personality/hebbian/` (Week 9 complete)
- **Duration:** 4-10 hours for Week 10
- **Create:** HebbianLearningManager orchestration layer

---

## ✨ SUMMARY

**Where we are:** Week 12 COMPLETE! 🎉

**What we accomplished (Phase 3 + 4 so far):**
- ✅ Repository cleanup (200+ files organized)
- ✅ Judgment & Clarify System (73/73 tests)
- ✅ Hebbian Learning — all 3 core components (75 tests)
- ✅ Hebbian Integration — manager + pipeline (Week 10)
- ✅ Outcome Tracking + ProactivityBudget (Week 11)
- ✅ Goal Continuity — GoalTracker + FollowUpEngine (Week 12, +59 tests)
- ✅ **331 total tests passing!**

**What's next:** Week 13 User Model (knowledge graph — NOT flat store)

**Questions?**
- Status: [CURRENT_STATUS.md](CURRENT_STATUS.md)
- Setup: [MINIMAL_SETUP.md](MINIMAL_SETUP.md)
- Demo: `python demo_week8_5.py`
- Week 9 Report: [WEEK9_COMPLETE.md](WEEK9_COMPLETE.md)
- Ask CJ if unclear

---

**Last Updated:** February 27, 2026
**Maintained By:** CJ
**Status:** ✅ Week 12 COMPLETE (331 tests) - Ready for Week 13 User Model! 🚀
