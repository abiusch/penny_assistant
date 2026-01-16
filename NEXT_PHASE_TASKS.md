# NEXT_PHASE_TASKS.md

> ⚠️ **SINGLE SOURCE OF TRUTH**
> 
> This file is the **primary reference** for Penny's development status.
> All major documentation files are in the root directory.
> 
> 🎯 **Current status:** [CURRENT_STATUS.md](CURRENT_STATUS.md)  
> 📋 **Detailed roadmap:** [ROADMAP.md](ROADMAP.md)  
> 📚 **Project overview:** [README.md](README.md)

**Last Updated:** January 16, 2026

---

## 🚨 URGENT: REPOSITORY CLEANUP (JUST COMPLETED!)

**Status:** ✅ COMPLETE

**What was done:**
- Moved 117 test files → `tests/`
- Moved 35 experimental scripts → `experiments/`
- Archived 41 completed docs → `docs/archive/phases/`
- Consolidated 27 databases → `data/`
- Created `ENTRY_POINTS.md`
- Split requirements into core/platform/optional
- Added `.env.example` and `MINIMAL_SETUP.md`

**Why this was critical:**
Three external reviews (Manus, ChatGPT, Perplexity) unanimously flagged:
> "Root directory sprawl will directly hurt velocity if not cleaned"

**Next:** Week 8.5 Judgment & Clarify System

---

## 🎯 QUICK STATUS

**Current:** Repository Cleanup Complete ✅
**Next:** Week 8.5 Judgment & Clarify System (1 week) ⭐
**Then:** Week 9-10 Hebbian Learning (2 weeks)
**Phase 3:** 85% Complete → 90% after Week 8.5
**Server:** 🟢 Port 5001
**Tests:** 🟢 100% pass rate

---

## ✅ RECENTLY COMPLETED

**Week 8: Emotional Continuity** (December 30, 2025)
- ✅ Emotion detection (27 emotions, 90%+ accuracy)
- ✅ Cross-session emotional tracking (7-day memory window)
- ✅ Personality snapshots with version control + rollback
- ✅ Forgetting mechanism (30-day gradual decay)
- ✅ Consent management (GDPR Article 17 compliant)
- ✅ 100% test pass rate (9/9 integration tests)
- ✅ Production ready, committed to GitHub

**Status:** Production deployed, server running on port 5001

---

## 🎯 ACTIVE WORK: WEEK 8.5 JUDGMENT & CLARIFY SYSTEM

**Goal:** Control layer that prevents drift in all learning systems

**Duration:** 1 week (15-20 hours estimated)

**Priority:** ⭐ **CRITICAL - Must complete before Week 9**

### **Why This First:**

**The Problem:**
- LLMs optimize for progress (always output something)
- "Answering immediately" is often a failure mode
- Learning systems can reinforce patterns from ambiguous inputs
- This causes drift over time

**The Solution:**
Penny should default to:
- ✅ Answering when request is clear and low-stakes
- ✅ Asking clarifying question when ambiguity/stakes present
- ✅ Slowing down when cost of being wrong is high

**The Benefit:**
- Prevents Hebbian from learning bad patterns (Week 9-10)
- Makes outcome tracking more reliable (Week 11)
- Protects goal continuity from ambiguity (Week 12)
- Ensures user model builds correct beliefs (Week 13)

### **What It Does:**

**1. Ambiguity Detection**
- Detects vague referents ("that", "it", "the thing")
- Identifies missing key parameters (date, scope, audience)
- Triggers: "Quick check so I don't go off into the weeds—do you mean X or Y?"

**2. Risk Assessment**
- Detects high-stakes tasks (finance, irreversible actions)
- Flags requests requiring high accuracy
- Triggers: "Wanna make sure I nail this—{clarification}?"

**3. Confidence Monitoring**
- Detects contradictions with past context/memory
- Identifies when response would require guessing
- Triggers: "Hold up—last time you said X. Did that change?"

**4. Personality Preservation**
- All clarifications sound like Penny (casual, confident, witty)
- Maximum 1-2 questions, no corporate disclaimers
- Examples:
  - "Before I sprint in the wrong direction: what's the end goal here?"
  - "Two-second clarity question: what's the {parameter}?"

### **Implementation Plan:**

**Phase 1: Detection Layer (6-9 hours)**
- Phase 1A: Vague referent detection (2-3 hours)
- Phase 1B: Stakes assessment + missing parameters (2-3 hours)
- Phase 1C: Contradiction detection + confidence (2-3 hours)

**Phase 2: Personality Layer (4-6 hours)**
- Build PennyStyleClarifier
- Format questions in Penny's voice
- Templates for different trigger types
- Frustration detection

**Phase 3: Pipeline Integration (4-6 hours)**
- Integrate into research_first_pipeline.py
- Add judgment check before processing
- Return clarifying questions
- Full integration tests

### **Implementation Prompts Available:**
- `CLAUDE_CODE_PHASE1A_PROMPT.md` - Vague referents
- `CLAUDE_CODE_PHASE1B_PROMPT.md` - Stakes + parameters
- `CLAUDE_CODE_PHASE1C_PROMPT.md` - Contradictions + confidence

### **Test Scenarios:**

**Ambiguous:**
```
User: "Fix that thing"
Penny: "Quick check—you mean the auth bug or the TTS latency?"
```

**Missing Parameter:**
```
User: "Schedule a meeting with the team"
Penny: "Two-second clarity question: what's the date and time?"
```

**High Stakes:**
```
User: "Delete all test data"
Penny: "Wanna make sure I nail this—you mean just test_* tables, 
        or everything in the test database?"
```

**Contradiction:**
```
Previous: "Use Rust for this"
Current: "Use Python for the API"
Penny: "Hold up—last time you said Rust. Did that change, or is 
        this a different project?"
```

**Low Stakes (No Clarification):**
```
User: "What's 2+2?"
Penny: "4"
```

---

## 🧠 UPCOMING: WEEK 9-10 HEBBIAN LEARNING

**Goal:** Brain-inspired associative learning

**Duration:** 2 weeks (14-22 hours)

**Status:** ⏸️ Waiting for Week 8.5 completion

**Why Wait:** Hebbian learns patterns from conversations. Week 8.5 ensures it learns from CLEAR inputs, not ambiguous ones.

**What It Does:**
1. **Vocabulary Association** - Learns when to use which words
2. **Dimension Co-activation** - Personality dimensions adapt together
3. **Conversation Sequences** - Anticipates user needs

**Implementation:**
- Week 9: Core components (10-12 hours)
- Week 10: Integration & polish (4-10 hours)

**Specs:** Already complete (187KB documentation from October)

**Start after:** Week 8.5 complete

---

## 🔮 AFTER WEEK 10 (FUTURE PHASES)

**Phase 4 Planning:**

**Week 11: Outcome Tracking** (1 week)
- Track whether responses helped or hurt
- Learn from success/failure patterns
- Adapt strategies based on outcomes

**Week 12: Goal Continuity** (1 week)
- Track unfinished business across sessions
- Remember suspended tasks
- Proactive follow-ups

**Week 13: User Model** (2-3 weeks)
- Penny maintains explicit beliefs about you
- Confidence scores for each belief
- Transparent reasoning, user can correct

**All protected by Week 8.5 Judgment layer!**

---

## 📊 SYSTEM STATUS SUMMARY

### **Active Systems:**
- **LLM:** Nemotron-3 Nano (30B params, 1M context, $0/month, 100% local)
- **Memory:** 539 conversation vectors (AES-128 encrypted)
- **Personality:** 7 dimensions tracking, 0.74 confidence (technical depth)
- **Emotional Intelligence:** Week 8 active (7-day memory, 0.8 intensity threshold)
- **Security:** GDPR Article 17 compliant, encrypted, PII-protected
- **Server:** Port 5001, stable, 100% test pass rate

### **Performance Metrics:**
- Response Time: 5-10s (acceptable for local LLM)
- Emotion Accuracy: 90%+ on 27 emotions
- Test Coverage: 100% (9/9 integration + 30/30 diagnostic)
- Cost: $0/month forever

**Complete details:** [CURRENT_STATUS.md](CURRENT_STATUS.md)

---

## 📚 DOCUMENTATION REFERENCE

### **Primary Documents (Root Directory):**

**Status & Planning:**
- **[CURRENT_STATUS.md](CURRENT_STATUS.md)** - Complete system status, active systems, metrics
- **[ROADMAP.md](ROADMAP.md)** - Detailed roadmap, decision framework
- **[README.md](README.md)** - Project overview, quick start guide

**Specifications:**
- Week 8.5 specs: Implementation prompts available (CLAUDE_CODE_PHASE*.md)
- Hebbian specs: Check `/hebbian_specs/` or `/docs/specs/hebbian/`
- Week 8 specs: Check root or `/docs/specs/emotional_continuity/`

**Additional Documentation:**
- Guides: Look for guides in `/docs/guides/` or root directory
- History: Weekly progress in `/docs/progress/2025/`
- Archive: Completed work in `/docs/archive/`

---

## 🎯 FOR AI ASSISTANTS (CRITICAL INSTRUCTIONS)

### **When helping with Penny development:**

**1. ALWAYS READ FIRST:**
   - ✅ This file (NEXT_PHASE_TASKS.md) - Quick orientation
   - ✅ [CURRENT_STATUS.md](CURRENT_STATUS.md) - Complete current state
   - ✅ [ROADMAP.md](ROADMAP.md) - What's happening next

**2. FOR WEEK 8.5 IMPLEMENTATION:**
   - ✅ Current priority is Judgment & Clarify System
   - ✅ Three prompts available for Claude Code (Phase 1A, 1B, 1C)
   - ✅ Build detection layer first, then personality layer, then integrate
   - ✅ Do NOT start Week 9 until Week 8.5 is complete

**3. FOR FUTURE WEEKS:**
   - ✅ Week 8.5 comes before Week 9-10 (control layer for learning)
   - ✅ Hebbian specs are ready but should wait
   - ✅ All future learning protected by Week 8.5 judgment layer

**4. NEVER REFERENCE:**
   - ❌ Files in `/docs/archive/` - Outdated/superseded
   - ❌ Old roadmaps - Use current docs only
   - ❌ Completed feature announcements (*_COMPLETE.md files)

**5. VERIFY BEFORE SUGGESTING:**
   - ✅ Check CURRENT_STATUS.md for what's implemented
   - ✅ Check this file for current priorities
   - ✅ Week 8.5 comes before Week 9-10
   - ✅ Don't suggest features marked "What NOT to Build"

---

## 🔄 MAINTENANCE POLICY

### **This File is Updated:**
- After each completed week
- When priorities change
- When new phases are added
- When system status changes significantly

### **Recent Updates:**
- **January 16, 2026:** Added Week 8.5 as immediate priority
- **December 31, 2025:** Initial Week 8 completion documented
- **December 30, 2025:** Week 8 marked complete

### **How to Update After Each Week:**
1. Move completed work from "ACTIVE WORK" to "RECENTLY COMPLETED"
2. Update "QUICK STATUS" (current week, percentage)
3. Update "UPCOMING" section for next work
4. Update "Last Updated" date
5. Keep file under 400 lines for quick AI scanning

---

## 📝 QUICK REFERENCE

### **Most Important Files:**
- 🎯 **This file** (NEXT_PHASE_TASKS.md) - Quick status + priorities
- 📊 [CURRENT_STATUS.md](CURRENT_STATUS.md) - Complete system state
- 📋 [ROADMAP.md](ROADMAP.md) - Detailed plans

### **Getting Started with Week 8.5:**
1. Start with Phase 1A (vague referent detection)
2. Use `CLAUDE_CODE_PHASE1A_PROMPT.md` with Claude Code
3. Then Phase 1B, then Phase 1C (detection layer complete)
4. Then Phase 2 (personality layer)
5. Then Phase 3 (pipeline integration)

### **After Week 8.5:**
- Move to Week 9-10 Hebbian Learning
- Hebbian will learn from CLEAR inputs (thanks to Week 8.5)
- All specs already complete and ready

### **Questions About Current State:**
- Check [CURRENT_STATUS.md](CURRENT_STATUS.md) first
- Ask user if information is missing or unclear

---

## ✨ SUMMARY

**Where we are:** Week 8 (Emotional Continuity) complete and production-ready

**What's next:** Week 8.5 Judgment & Clarify System (NEW - 1 week)

**Why:** Control layer that prevents drift in all future learning systems

**Then:** Week 9-10 Hebbian Learning (2 weeks)

**Questions?**
- Status: [CURRENT_STATUS.md](CURRENT_STATUS.md)
- Plans: [ROADMAP.md](ROADMAP.md)
- Ask CJ if unclear

---

**Last Updated:** January 16, 2026  
**Maintained By:** CJ  
**Status:** ✅ Active - Week 8.5 is immediate priority
