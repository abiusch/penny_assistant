# NEXT_PHASE_TASKS.md

> ⚠️ **SINGLE SOURCE OF TRUTH**
> 
> This file is the **primary reference** for Penny's development status.
> All major documentation files are in the root directory.
> 
> 🎯 **Current status:** [CURRENT_STATUS.md](CURRENT_STATUS.md)  
> 📋 **Detailed roadmap:** [ROADMAP.md](ROADMAP.md)  
> 📚 **Project overview:** [README.md](README.md)

**Last Updated:** January 18, 2026

---

## 🎯 QUICK STATUS

**Current:** Week 8.5 COMPLETE! 🎉  
**Next:** Week 9-10 Hebbian Learning (2 weeks)  
**Phase 3:** 85% → 95% (Week 8.5 complete!) → 100% after Week 13  
**Server:** 🟢 Port 5001  
**Tests:** 🟢 73/73 passing (100% pass rate!)

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

## ✅ RECENTLY COMPLETED (January 16-18, 2026)

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

## 🧠 NEXT UP: WEEK 9-10 HEBBIAN LEARNING

**Goal:** Brain-inspired associative learning

**Duration:** 2 weeks (14-22 hours estimated)

**Status:** 🎯 READY TO START

**Why Now is Perfect:**
- ✅ Week 8.5 judgment layer protects against learning from vague inputs
- ✅ Detection system ensures clear training data
- ✅ Contradictions caught before reinforcement
- ✅ Confidence scoring prevents guessing

**What Hebbian Learning Does:**
1. **Vocabulary Association** - Learns when to use which words
2. **Dimension Co-activation** - Personality dimensions adapt together
3. **Conversation Sequences** - Anticipates user needs

**Implementation Plan:**
- Week 9: Core components (10-12 hours)
  - Hebbian weight matrix
  - Association tracking
  - Decay mechanisms
  
- Week 10: Integration & polish (4-10 hours)
  - Connect to personality system
  - Memory integration
  - Testing and validation

**Specs:** Already complete (187KB documentation from October)

**Protected by:** Week 8.5 Judgment System ✅

---

## 🔮 PHASE 4: ADVANCED LEARNING (Weeks 11-13)

**After Hebbian Learning completes:**

**Week 11: Outcome Tracking** (1 week)
- Track whether responses helped or hurt
- Learn from success/failure patterns
- Adapt strategies based on outcomes
- **Protected by judgment system**

**Week 12: Goal Continuity** (1 week)
- Track unfinished business across sessions
- Remember suspended tasks
- Proactive follow-ups
- **Judgment ensures clear goals**

**Week 13: User Model** (2-3 weeks)
- Penny maintains explicit beliefs about you
- Confidence scores for each belief
- Transparent reasoning, user can correct
- **Judgment prevents incorrect assumptions**

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
- **Judgment System:** Week 8.5 active (73/73 tests, production-ready) ⭐ NEW!
- **Security:** GDPR Article 17 compliant, encrypted, PII-protected
- **Server:** Port 5001, stable

### **Performance Metrics:**
- Response Time: 5-10s (acceptable for local LLM)
- Emotion Accuracy: 90%+ on 27 emotions
- Judgment Tests: 73/73 passing (100%)
- Total Tests: 100+ passing
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
   - ⭐ Week 9-10: Hebbian Learning (NEXT UP!)
   - Use existing Hebbian specs from October
   - Judgment system now protects learning

**3. WEEK 8.5 STATUS:**
   - ✅ COMPLETE - 73/73 tests passing
   - ✅ Committed: ddfd369
   - ✅ Production ready
   - ✅ Protects all future learning

**4. FOR HEBBIAN LEARNING:**
   - ✅ Judgment system ensures clear training data
   - ✅ Specs are ready (187KB documentation)
   - ✅ Start with Week 9 core components
   - ✅ Week 10 for integration and polish

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
- **January 18, 2026 (Evening):** Week 8.5 marked COMPLETE! 73/73 tests passing 🎉
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
- **START:** Week 9 Hebbian Learning (core components)
- **Specs:** Check `/hebbian_specs/` folder
- **Duration:** 10-12 hours for Week 9
- **Protected:** Judgment system ensures quality training data

---

## ✨ SUMMARY

**Where we are:** Week 8.5 COMPLETE! 🎉

**What we accomplished:**
- ✅ Repository cleanup (200+ files organized)
- ✅ Judgment & Clarify System (73/73 tests)
- ✅ Detection layer (5 methods)
- ✅ Personality layer (Penny's voice)
- ✅ Pipeline integration (production ready)

**What's next:** Week 9-10 Hebbian Learning (brain-inspired associative learning)

**Questions?**
- Status: [CURRENT_STATUS.md](CURRENT_STATUS.md)
- Setup: [MINIMAL_SETUP.md](MINIMAL_SETUP.md)
- Demo: `python demo_week8_5.py`
- Ask CJ if unclear

---

**Last Updated:** January 18, 2026  
**Maintained By:** CJ  
**Status:** ✅ Week 8.5 COMPLETE - Ready for Week 9-10 Hebbian Learning! 🚀
