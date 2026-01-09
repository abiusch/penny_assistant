# NEXT_PHASE_TASKS.md

> ⚠️ **SINGLE SOURCE OF TRUTH**
> 
> This file is the **primary reference** for Penny's development status.
> All major documentation files are in the root directory.
> 
> 🎯 **Current status:** [CURRENT_STATUS.md](CURRENT_STATUS.md)  
> 📋 **Detailed roadmap:** [ROADMAP.md](ROADMAP.md)  
> 📚 **Project overview:** [README.md](README.md)

**Last Updated:** December 31, 2025

---

## 🎯 QUICK STATUS

**Current:** Week 8 Complete ✅  
**Next:** Week 9-10 Hebbian Learning (2 weeks)  
**Phase 3:** 85% Complete  
**Server:** 🟢 Port 5001  
**Tests:** 🟢 100% pass rate (9/9 integration tests)

---

## ✅ RECENTLY COMPLETED

**Week 8: Emotional Continuity** (December 30, 2025)
- ✅ Transformer-based emotion detection (27 emotions, 90%+ accuracy)
- ✅ Cross-session emotional tracking (7-day memory window)
- ✅ Personality snapshots with version control + rollback
- ✅ Forgetting mechanism (30-day gradual decay)
- ✅ Consent management (GDPR Article 17 compliant)
- ✅ 100% test pass rate (9/9 integration tests)
- ✅ Production ready, committed to GitHub (commit 1691de4)

**Status:** Production deployed, server running on port 5001

**Complete details:** See [CURRENT_STATUS.md](CURRENT_STATUS.md)

---

## 🧠 ACTIVE WORK: WEEK 9-10 HEBBIAN LEARNING

**Goal:** Brain-inspired associative learning ("neurons that fire together, wire together")

**Duration:** 2 weeks (14-22 hours estimated)

**Status:** ⏳ Specs complete (187KB documentation), ready for implementation

### **What It Does:**

**1. Vocabulary Association Matrix**
- Learns: "ngl" + casual_context → strength 0.85
- Learns: "ngl" + formal_context → strength 0.12
- **Result:** Penny knows when to use which vocabulary contextually

**2. Dimension Co-activation Matrix**
- Learns: stress + empathy + brevity → co-activate together
- Learns: casual + sarcasm + emojis → co-activate together
- **Result:** Personality dimensions adapt in coherent patterns

**3. Conversation Sequence Learner**
- Learns: problem → technical answer → "simplify?" → simplified answer
- Predicts: Next time, skip directly to simple explanation
- **Result:** Anticipates user needs based on conversation patterns

### **Implementation Timeline:**

**Week 9 (10-12 hours):**
- Day 1-2: Vocabulary Association Matrix (3-4 hours)
- Day 3-4: Dimension Co-activation Learning (3-4 hours)
- Day 5-6: Conversation Sequence Learner (3-4 hours)
- Day 7: Testing & validation (1 hour)

**Week 10 (4-10 hours):**
- Day 1-2: Database migration (1-2 hours)
- Day 3-4: Orchestration layer (2-3 hours)
- Day 5-6: Full integration (2-3 hours)
- Day 7: End-to-end testing (1-2 hours)

### **Documentation:**

**Hebbian specs location:** Check `/hebbian_specs/` or `/docs/specs/hebbian/`

**Start here:**
1. Find and read `HEBBIAN_LEARNING_ARCHITECTURE.md` (system overview)
2. Follow `HEBBIAN_INTEGRATION_PLAN.md` (day-by-day implementation)
3. Use `HEBBIAN_IMPLEMENTATION_SKELETONS.md` (code templates)

**Complete roadmap:** See [ROADMAP.md](ROADMAP.md)

---

## 🔮 AFTER WEEK 10 (FUTURE PHASES)

**Phase 4 Planning (Not Yet Scheduled):**

Potential features being evaluated:
- **Week 11:** Outcome Tracking (causal feedback loops)
- **Week 12:** Goal Continuity (persistent intent across sessions)
- **Week 13:** User Model (explicit beliefs about user)
- **Week 14+:** Voice Optimization & Prosody matching

**Decision Point:** After Week 10, evaluate Hebbian results and decide:
- Continue Phase 4 (build more features)
- Polish & Ship (production deployment focus)
- Optimize existing features

**Complete future roadmap:** See [ROADMAP.md](ROADMAP.md)

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
- Cost: $0/month (was $5-20/month with GPT-4o-mini)

**Complete system details:** See [CURRENT_STATUS.md](CURRENT_STATUS.md)

---

## 📚 DOCUMENTATION REFERENCE

### **Primary Documents (Root Directory):**

**Status & Planning:**
- **[CURRENT_STATUS.md](CURRENT_STATUS.md)** - Complete system status, active systems, metrics
- **[ROADMAP.md](ROADMAP.md)** - Detailed roadmap (Week 9-13+), decision framework
- **[README.md](README.md)** - Project overview, quick start guide

**Specifications:**
- Check `/hebbian_specs/` - Week 9-10 Hebbian Learning specs (187KB)
- Check `/docs/specs/emotional_continuity/` - Week 8 Emotional Continuity specs

### **Additional Documentation:**

**Guides & How-Tos:**
- Look for guides in `/docs/guides/` or root directory
- Setup guides, troubleshooting, implementation guides

**Historical Record:**
- Weekly progress reports may be in `/docs/progress/2025/`
- Archived/completed work may be in `/docs/archive/`

---

## 🎯 FOR AI ASSISTANTS (CRITICAL INSTRUCTIONS)

### **When helping with Penny development:**

**1. ALWAYS READ FIRST:**
   - ✅ This file (NEXT_PHASE_TASKS.md) - Quick orientation
   - ✅ [CURRENT_STATUS.md](CURRENT_STATUS.md) - Complete current state
   - ✅ [ROADMAP.md](ROADMAP.md) - What's happening next

**2. FOR IMPLEMENTATION:**
   - ✅ Find Hebbian specs (check `/hebbian_specs/` or `/docs/specs/hebbian/`)
   - ✅ Start with README or ARCHITECTURE doc
   - ✅ Follow INTEGRATION_PLAN day-by-day

**3. NEVER REFERENCE:**
   - ❌ Files in `/docs/archive/` - Outdated/superseded
   - ❌ Old roadmaps or plans - Use current docs only
   - ❌ Completed feature announcements (*_COMPLETE.md files)

**4. IF CONFUSED:**
   - ❓ Ask user: "Which document should I reference?"
   - ❓ Check file modification dates (newer = more current)
   - ❓ Default to CURRENT_STATUS.md for facts

**5. VERIFY BEFORE SUGGESTING:**
   - ✅ Check CURRENT_STATUS.md for what's already implemented
   - ✅ Check ROADMAP.md for planned features
   - ✅ Don't suggest features already marked "What NOT to Build"

---

## 🔄 MAINTENANCE POLICY

### **This File is Updated:**
- After each completed week
- When starting new phases  
- When major milestones are reached
- When system status changes significantly

### **How to Update:**

**After completing a week:**
1. Move "ACTIVE WORK" section to "RECENTLY COMPLETED"
2. Update "QUICK STATUS" (current week, percentage)
3. Add new "ACTIVE WORK" section for next week
4. Update "Last Updated" date

**Keep this file under 300 lines for quick scanning by AI assistants.**

---

## 📝 QUICK REFERENCE

### **Most Important Files:**
- 🎯 **This file** (NEXT_PHASE_TASKS.md) - Quick status + next steps
- 📊 [CURRENT_STATUS.md](CURRENT_STATUS.md) - Complete system state
- 📋 [ROADMAP.md](ROADMAP.md) - Detailed implementation plans

### **Getting Started with Week 9:**
1. Find Hebbian specs (check `/hebbian_specs/` folder)
2. Read HEBBIAN_LEARNING_ARCHITECTURE.md (overview)
3. Follow HEBBIAN_INTEGRATION_PLAN.md (step-by-step)
4. Use HEBBIAN_IMPLEMENTATION_SKELETONS.md (code templates)

### **Questions About Current State:**
- Check [CURRENT_STATUS.md](CURRENT_STATUS.md) first
- Ask user if information is missing or unclear

---

## ✨ SUMMARY

**Where we are:** Week 8 (Emotional Continuity) complete and production-ready

**What's next:** Week 9-10 Hebbian Learning (brain-inspired associative learning)

**How to start:** Find Hebbian specs, read ARCHITECTURE doc, follow INTEGRATION_PLAN

**Questions?** 
- Status: Check [CURRENT_STATUS.md](CURRENT_STATUS.md)
- Plans: Check [ROADMAP.md](ROADMAP.md)
- Ask CJ if something's unclear

---

**Last Updated:** December 31, 2025  
**Maintained By:** CJ  
**Status:** ✅ Active - Single source of truth for Penny development
