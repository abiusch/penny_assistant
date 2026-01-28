# 🚀 WEEK 9 HEBBIAN LEARNING - START GUIDE

**Project:** PennyGPT AI Companion  
**Phase:** Week 9-10 Hebbian Learning  
**Current:** Week 9 Start - Core Components  
**Duration:** 10-12 hours (Week 9) + 4-10 hours (Week 10)  
**Prerequisites:** ✅ Week 8.5 Judgment System Complete (73/73 tests)

---

## 🎯 WHAT IS HEBBIAN LEARNING?

**Neuroscience principle:** "Neurons that fire together, wire together"

**Applied to Penny:**
- Learn which **words** go with which **contexts**
- Learn which **personality dimensions** activate together
- Learn **conversation patterns** and anticipate needs

**Why now is perfect:**
- ✅ Week 8.5 judgment ensures clear training data
- ✅ No learning from vague/ambiguous inputs
- ✅ Contradictions caught before reinforcement
- ✅ High confidence required for learning

---

## 📚 EXISTING SPECIFICATIONS (READY TO USE)

**All specs created October 2025, tested design:**

### **Main Documents:**
1. `HEBBIAN_IMPLEMENTATION_GUIDE.md` - Week-by-week overview
2. `docs/specs/hebbian_original/HEBBIAN_INTEGRATION_PLAN.md` - Detailed day-by-day plan
3. `docs/specs/hebbian_original/HEBBIAN_LEARNING_SPECS.md` - Complete specifications
4. `docs/specs/hebbian_original/HEBBIAN_LEARNING_ARCHITECTURE.md` - Architecture design
5. `docs/specs/hebbian_original/HEBBIAN_IMPLEMENTATION_SKELETONS.md` - Code templates
6. `docs/specs/hebbian_original/HEBBIAN_DATABASE_SCHEMA.sql` - Database schema
7. `CLAUDE_CODE_HEBBIAN_SPECS_PROMPT.md` - Claude Code instructions

**Total documentation:** 187KB (comprehensive and production-ready!)

---

## 🏗️ WEEK 9 ARCHITECTURE

### **Three Core Components:**

**Component 1: Vocabulary Association Matrix** (3-4 hours)
```python
# Learn: Which words go with which contexts?
hebbian_vocab.observe("ngl", context="casual_opinion")
hebbian_vocab.should_use("ngl", "formal_technical")  # → False
hebbian_vocab.should_use("ngl", "casual_opinion")    # → True
```

**Component 2: Dimension Co-activation** (3-4 hours)
```python
# Learn: Which personality dimensions activate together?
# Pattern: stressed → (high empathy + brief + simple)
hebbian_dim.observe_activation({
    'empathy': 0.8,
    'response_length': 0.3,
    'technical_depth': 0.4
})
# Next time stressed → automatically apply all three
```

**Component 3: Conversation Sequence Learning** (4-5 hours)
```python
# Learn: What usually comes next in conversations?
hebbian_seq.observe_transition("user_question", "penny_explanation")
hebbian_seq.predict_next_state("user_question")  # → "penny_explanation"
```

---

## 📋 WEEK 9 DAY-BY-DAY PLAN

### **Day 1-2: Database + Vocabulary Associator (4 hours)**

**Step 1: Database Setup (30 min)**
```bash
# Apply Hebbian database schema
cd /Users/CJ/Desktop/penny_assistant
sqlite3 data/personality_tracking.db < docs/specs/hebbian_original/HEBBIAN_DATABASE_SCHEMA.sql

# Verify tables created
sqlite3 data/personality_tracking.db ".tables" | grep hebbian
```

**Expected tables:**
- vocab_associations
- vocab_context_observations
- dimension_coactivations
- conversation_state_transitions
- hebbian_config
- hebbian_stats

**Step 2: Create Module Structure (15 min)**
```bash
# Create hebbian module
mkdir -p src/personality/hebbian
touch src/personality/hebbian/__init__.py

# Copy type definitions
# (See HEBBIAN_IMPLEMENTATION_SKELETONS.md for templates)
```

**Step 3: Implement Vocabulary Associator (2.5 hours)**

**File:** `src/personality/hebbian/vocabulary_associator.py`

**Methods to implement:**
- `__init__()` - Database connection
- `observe_term_in_context()` - Hebbian strengthening
- `get_association_strength()` - Query associations
- `should_use_term()` - Prediction with threshold
- `filter_response_vocabulary()` - Apply to responses
- `apply_temporal_decay()` - Decay old associations

**Step 4: Unit Tests (1 hour)**

**File:** `tests/test_hebbian_vocabulary.py`

**Test cases:**
- Association strengthening
- Competitive weakening
- Threshold prediction
- Temporal decay
- Response filtering

**Target:** 10+ tests passing

---

### **Day 3-4: Dimension Co-activation (4 hours)**

**Step 1: Implement Dimension Associator (2.5 hours)**

**File:** `src/personality/hebbian/dimension_associator.py`

**Methods to implement:**
- `__init__()` - Database connection
- `observe_activation()` - Record co-activation
- `get_coactivation_strength()` - Query patterns
- `predict_activation()` - Suggest dimension values
- `detect_multi_dim_patterns()` - 3+ dimensions together
- `apply_temporal_decay()` - Decay old patterns

**Step 2: Unit Tests (1.5 hours)**

**File:** `tests/test_hebbian_dimensions.py`

**Test cases:**
- Co-activation recording
- Pattern detection
- Prediction accuracy
- Multi-dimensional patterns
- Negative correlations

**Target:** 8+ tests passing

---

### **Day 5-7: Sequence Learning (4 hours)**

**Step 1: Implement Sequence Learner (2.5 hours)**

**File:** `src/personality/hebbian/sequence_learner.py`

**Methods to implement:**
- `__init__()` - Database connection
- `observe_transition()` - Record state transitions
- `get_transition_strength()` - Query patterns
- `predict_next_state()` - Anticipate next state
- `classify_conversation_state()` - Categorize current state
- `detect_sequence_patterns()` - Multi-step patterns

**Step 2: Unit Tests (1.5 hours)**

**File:** `tests/test_hebbian_sequences.py`

**Test cases:**
- Transition recording
- Prediction accuracy
- State classification
- Multi-step patterns
- Edge cases

**Target:** 8+ tests passing

---

## ✅ WEEK 9 DELIVERABLES

**By end of Week 9, you should have:**

**Code:**
- [ ] `src/personality/hebbian/__init__.py`
- [ ] `src/personality/hebbian/vocabulary_associator.py`
- [ ] `src/personality/hebbian/dimension_associator.py`
- [ ] `src/personality/hebbian/sequence_learner.py`
- [ ] Database schema applied

**Tests:**
- [ ] `tests/test_hebbian_vocabulary.py` (10+ tests)
- [ ] `tests/test_hebbian_dimensions.py` (8+ tests)
- [ ] `tests/test_hebbian_sequences.py` (8+ tests)
- [ ] **Total: 26+ tests passing**

**Performance:**
- [ ] Each component < 3ms overhead
- [ ] Combined < 10ms overhead
- [ ] Memory < 50MB additional

**Documentation:**
- [ ] WEEK9_COMPLETE.md with results
- [ ] Performance metrics documented
- [ ] Any deviations from spec noted

---

## 🎯 SUCCESS CRITERIA (WEEK 9)

**All 3 components work independently:**
```python
# Vocabulary
vocab = VocabularyAssociator()
vocab.observe_term_in_context("ngl", "casual")
assert vocab.should_use_term("ngl", "casual") == True

# Dimensions
dims = DimensionAssociator()
dims.observe_activation({'empathy': 0.8, 'response_length': 0.3})
predictions = dims.predict_activation({'empathy': 0.8})
assert 'response_length' in predictions

# Sequences
seq = SequenceLearner()
seq.observe_transition("question", "explanation")
assert seq.predict_next_state("question") == "explanation"
```

**Tests:**
- ✅ 26+ unit tests passing
- ✅ All components < 3ms
- ✅ Database persistence working
- ✅ No crashes or memory leaks

---

## 📊 WEEK 10 PREVIEW (NEXT)

**After Week 9 completes, Week 10 will:**

1. **Create Hebbian Manager** (orchestration layer)
   - Coordinates all 3 components
   - Single entry point: `observe_conversation()`

2. **Pipeline Integration**
   - Hook into research_first_pipeline.py
   - Work with Week 8.5 judgment system
   - Feature flag controlled

3. **End-to-End Testing**
   - Integration tests
   - Real conversation testing
   - Performance validation

4. **Production Ready**
   - Rollout plan
   - Rollback procedures
   - Monitoring

---

## 🚀 READY TO START?

### **For Claude Code:**

**Tell CC:**
```
"Week 8.5 complete with 73/73 tests! Now starting Week 9: Hebbian Learning.

Read these files in order:
1. HEBBIAN_IMPLEMENTATION_GUIDE.md - Overview
2. docs/specs/hebbian_original/HEBBIAN_INTEGRATION_PLAN.md - Detailed plan
3. docs/specs/hebbian_original/HEBBIAN_IMPLEMENTATION_SKELETONS.md - Code templates

Start with Day 1-2: Database setup + Vocabulary Associator

Follow the day-by-day plan in HEBBIAN_INTEGRATION_PLAN.md"
```

### **Or Manual Implementation:**

**Follow the detailed plan in:**
`docs/specs/hebbian_original/HEBBIAN_INTEGRATION_PLAN.md`

**Start with:**
1. Apply database schema
2. Create module structure
3. Implement vocabulary_associator.py
4. Write tests
5. Verify performance

---

## 💡 KEY PRINCIPLES

**Protected by Week 8.5:**
- ✅ Only learn from clear, unambiguous inputs
- ✅ Judgment system filters vague requests
- ✅ Contradictions caught before learning
- ✅ High confidence required

**Performance First:**
- ✅ Monitor latency at each step
- ✅ Profile with cProfile
- ✅ Rollback if >10ms overhead
- ✅ Cache aggressively

**Gradual Rollout:**
- ✅ Feature flag controlled
- ✅ Enable one component at a time
- ✅ Validate before proceeding
- ✅ Rollback procedure ready

---

## 📚 REFERENCE DOCS (ALL READY)

**In your penny_assistant folder:**

1. `HEBBIAN_IMPLEMENTATION_GUIDE.md` - Start here
2. `docs/specs/hebbian_original/HEBBIAN_INTEGRATION_PLAN.md` - Detailed plan
3. `docs/specs/hebbian_original/HEBBIAN_LEARNING_SPECS.md` - Complete specs
4. `docs/specs/hebbian_original/HEBBIAN_DATABASE_SCHEMA.sql` - Database
5. `docs/specs/hebbian_original/HEBBIAN_IMPLEMENTATION_SKELETONS.md` - Code templates

**Total: 187KB of production-ready specifications!**

---

## 🎉 AFTER WEEK 9

**You'll have:**
- 3 working Hebbian components
- 26+ tests passing
- Database schema live
- Performance validated
- Ready for Week 10 integration!

**Then Week 10:**
- Orchestration layer
- Pipeline integration
- End-to-end testing
- Production deployment

---

**Ready to build brain-inspired learning! 🧠🚀**

**Questions?**
- Read: HEBBIAN_IMPLEMENTATION_GUIDE.md
- Check: HEBBIAN_INTEGRATION_PLAN.md Day 1-7
- Ask: CJ if anything unclear

---

**Last Updated:** January 18, 2026  
**Status:** Ready to start Week 9!  
**Protected by:** Week 8.5 Judgment System ✅
