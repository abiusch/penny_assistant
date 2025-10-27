# 🧠 Claude Code Task: Design Hebbian Learning Layer for Penny

## 📋 **Context**

Penny is an adaptive AI assistant with a personality system that learns user communication styles. We want to add a **Hebbian Learning Layer** inspired by neuroscience principles: "neurons that fire together, wire together."

**Current System:**
- Tracks user vocabulary, formality, response length preferences
- Stores personality dimensions with confidence scores
- Adapts prompts and responses based on learned preferences
- Uses confidence threshold (0.65) to activate adaptations

**Read These First:**
- `NEXT_PHASE_TASKS.md` - Complete roadmap and context
- `THREE_PERSPECTIVE_STRATEGIC_REVIEW.md` - Strategic direction
- `src/personality/personality_tracker.py` - Current personality system
- `src/personality/dynamic_personality_prompt_builder.py` - Prompt building
- `src/personality/personality_response_post_processor.py` - Response adaptation

---

## 🎯 **Your Task**

Design and spec out a **Hebbian Learning Layer** that enhances Penny's personality system with three core capabilities:

1. **Vocabulary Association Learning**
2. **Personality Dimension Co-activation Learning**
3. **Conversation Flow Pattern Learning**

---

## 📐 **Design Requirements**

### **1. Vocabulary Association Matrix**

**Goal:** Learn which words/phrases co-occur with which contexts

**Example Pattern:**
```
"ngl" appears frequently in: casual context, opinion-giving, hot takes
"ngl" rarely appears in: formal context, technical explanations, reports
→ Strong association: ("ngl", "casual_opinion") = 0.89
→ Weak association: ("ngl", "formal_technical") = 0.12
```

**Requirements:**
- Track term → context associations
- Strengthen connections when terms and contexts co-occur (Hebbian rule)
- Weaken competing associations (competitive learning)
- Support context types: casual, formal, technical, creative, work, personal
- Provide `should_use_term(term, context) → bool` method
- Store associations in database (persist across sessions)

**Questions to Answer:**
- What data structure for the association matrix?
- How to handle new terms vs established terms?
- What learning rate for strengthening/weakening?
- How to prevent overfit to recent conversations?
- Integration point with response post-processor?

---

### **2. Personality Dimension Co-activation Learning**

**Goal:** Learn which personality dimensions activate together naturally

**Example Pattern:**
```
When user is stressed:
- Empathy dimension: 0.8 (high)
- Response length: 0.3 (brief)
- Technical depth: 0.4 (simplified)

These three "fire together" repeatedly
→ Learn association: stressed context → (high empathy + brief + simple)
→ Next time: Automatically apply all three together
```

**Requirements:**
- Track which personality dimensions co-activate
- Build co-activation matrix: (dim1, dim2) → strength
- Support predictive activation: "If empathy is high, what else should be?"
- Handle multi-dimensional patterns (3+ dimensions together)
- Integrate with prompt builder for automatic dimension selection

**Current Personality Dimensions:**
```python
# From personality_tracker.py
- formality (0.0 = casual, 1.0 = formal)
- technical_depth (0.0 = simple, 1.0 = detailed)
- response_length (0.0 = brief, 1.0 = verbose)
- empathy (0.0 = neutral, 1.0 = highly empathetic)
- humor (0.0 = serious, 1.0 = playful)
- directness (0.0 = diplomatic, 1.0 = blunt)
```

**Questions to Answer:**
- How to detect "active" vs "inactive" dimensions?
- What threshold for co-activation (both > 0.6)?
- How to handle negative correlations (one high → other low)?
- Database schema for co-activation matrix?
- Integration with `dynamic_personality_prompt_builder.py`?

---

### **3. Conversation Flow Pattern Learning**

**Goal:** Learn sequential patterns in conversation states

**Example Pattern:**
```
Sequence observed 5 times:
1. User: "I'm stuck on X" (state: problem_statement)
2. Penny: Gives complex answer (state: technical_explanation)
3. User: "Can you simplify?" (state: simplification_request)
4. Penny: Gives simpler answer (state: simplified_explanation)
5. User: "Perfect thanks" (state: positive_feedback)

Pattern learned: problem_statement → technical → simplification_request
Next time: Skip directly to simplified explanation
```

**Requirements:**
- Track state transitions: state1 → state2 with frequency/strength
- Identify conversation states automatically or from context
- Build transition matrix for predicting next likely states
- Support sequence prediction: "Given current state, what's next?"
- Anticipate user needs before explicit request

**Conversation States to Consider:**
```
- problem_statement
- clarification_question
- technical_explanation
- simplified_explanation
- code_review
- debugging_help
- opinion_request
- casual_chat
- follow_up_question
- positive_feedback
- correction
- frustration_expression
```

**Questions to Answer:**
- How to classify conversation states automatically?
- What data structure for transition matrix?
- How to balance learned patterns vs flexibility?
- Database schema for sequence history?
- Integration point with `research_first_pipeline.py`?

---

## 🏗️ **Architecture Requirements**

### **General Principles:**

1. **Modular Design**
   - Each Hebbian component is independent module
   - Can be enabled/disabled individually
   - Doesn't break existing personality system if removed

2. **Database Integration**
   - All associations persist across sessions
   - Use existing `personality.db` schema
   - Add new tables as needed (specify schema)

3. **Performance**
   - Minimal latency impact (<10ms per component)
   - Efficient matrix operations
   - Consider caching frequently-accessed associations

4. **Interpretability**
   - All associations should be viewable/debuggable
   - Provide methods to export association matrices
   - Support dashboard visualization (future)

5. **Safety**
   - Prevent runaway strengthening (cap at 1.0)
   - Decay unused associations over time
   - Allow manual override/reset if needed

---

## 📂 **Expected Deliverables**

### **1. Architecture Document**
```
File: HEBBIAN_LEARNING_ARCHITECTURE.md

Contents:
- System overview diagram
- Component descriptions
- Data flow between components
- Integration points with existing system
- Database schema additions
- Performance considerations
- Testing strategy
```

### **2. Detailed Specifications**
```
File: HEBBIAN_LEARNING_SPECS.md

For each component:
- Purpose and goals
- Algorithm/approach (pseudocode)
- Data structures
- API surface (public methods)
- Configuration parameters (learning rates, thresholds)
- Edge cases and error handling
- Example usage
```

### **3. Database Schema**
```
File: HEBBIAN_DATABASE_SCHEMA.sql

Tables needed:
- vocabulary_associations (term, context_type, strength, last_updated)
- dimension_coactivations (dim1, dim2, strength, observation_count)
- conversation_transitions (state_from, state_to, strength, last_seen)
- hebbian_config (component, parameter, value)

Include:
- Indexes for performance
- Foreign key relationships
- Migration plan from current schema
```

### **4. Implementation Skeleton**
```
Files:
- src/personality/hebbian_vocabulary_associator.py (class skeleton)
- src/personality/hebbian_dimension_associator.py (class skeleton)
- src/personality/hebbian_sequence_learner.py (class skeleton)
- src/personality/hebbian_learning_manager.py (orchestrator)

Include:
- Class definitions with method signatures
- Docstrings explaining purpose
- TODO comments for implementation details
- Type hints for all methods
```

### **5. Integration Plan**
```
File: HEBBIAN_INTEGRATION_PLAN.md

Step-by-step:
1. Which files need modification?
2. What changes to each file?
3. How to maintain backward compatibility?
4. How to test each integration point?
5. Rollout strategy (feature flags?)
6. Migration plan for existing users
```

---

## 🎯 **Success Criteria**

Your design is successful if:

1. ✅ **Modular** - Can be added without breaking Phase 2
2. ✅ **Performant** - <10ms latency impact per component
3. ✅ **Persistent** - All learnings survive restart
4. ✅ **Debuggable** - Can inspect all associations
5. ✅ **Scalable** - Works with 100+ conversations
6. ✅ **Safe** - Has limits and decay mechanisms
7. ✅ **Practical** - Clear implementation path
8. ✅ **Testable** - Can validate each component

---

## 📚 **Reference Materials**

### **Hebbian Learning Principles:**
```
Core rule: Δw_ij = η * x_i * x_j
- w_ij: connection strength from neuron i to j
- η: learning rate (how fast to update)
- x_i, x_j: activation levels of neurons

Competitive learning:
- Strengthen winner
- Weaken competitors
- Maintains sparse representations
```

### **Penny's Current Architecture:**
```
User Input
    ↓
Context Detection (time, mood indicators)
    ↓
Personality State Retrieval (from DB)
    ↓
Dynamic Prompt Building (if confidence > 0.65)
    ↓
LLM Generation (GPT-4)
    ↓
Response Post-Processing (vocabulary substitution, formality adjustment)
    ↓
Personality Observation & Update (track patterns, update confidence)
    ↓
Response to User

Hebbian layer integrates at:
- Context Detection (vocabulary associations)
- Prompt Building (dimension co-activation)
- Response Post-Processing (sequence learning)
```

---

## 💡 **Design Considerations**

### **Think About:**

1. **Learning Rate**
   - Too high: Overfits to recent conversations
   - Too low: Never learns new patterns
   - Consider: 0.05 for strengthening, 0.01 for weakening?

2. **Decay Strategy**
   - Unused associations should weaken over time
   - Prevent stale patterns from persisting
   - Consider: -0.001 per day for unused?

3. **Competitive Learning**
   - When one association strengthens, competitors weaken
   - Maintains sparse, interpretable representations
   - Example: "ngl" in casual (strengthen) → "ngl" in formal (weaken)

4. **Bootstrapping**
   - How to initialize with no data?
   - Should we seed with common patterns?
   - How to prevent cold-start problems?

5. **Multi-User**
   - Each user gets separate association matrices
   - How to share patterns across users (optional, privacy-preserving)?
   - Consider: federated learning in Phase 4?

---

## 🚀 **Deliverable Format**

**Create 5 markdown files in `/Users/CJ/Desktop/penny_assistant/hebbian_specs/`:**

1. `HEBBIAN_LEARNING_ARCHITECTURE.md`
2. `HEBBIAN_LEARNING_SPECS.md`
3. `HEBBIAN_DATABASE_SCHEMA.sql`
4. `HEBBIAN_IMPLEMENTATION_SKELETONS.md` (code skeletons)
5. `HEBBIAN_INTEGRATION_PLAN.md`

**Use clear headings, code examples, diagrams (ASCII art is fine), and be specific.**

---

## 🎯 **Timeline**

This is a design task, not implementation. Focus on:
- ✅ Clear specifications
- ✅ Practical algorithms
- ✅ Integration strategy
- ✅ Testing approach

**Estimated design time:** 3-4 hours
**Implementation time (later):** 8-12 hours

---

## 🤔 **Questions to Address**

In your design, explicitly answer:

1. How do associations decay over time?
2. How to prevent overfitting to recent conversations?
3. How to handle conflicting patterns?
4. How to initialize with zero training data?
5. How to debug when associations are wrong?
6. How to visualize association matrices?
7. How to test Hebbian learning is working?
8. How to rollback if it breaks something?

---

## 💜 **Design Philosophy**

**Keep in mind:**
- Penny's uniqueness is personal adaptation
- Hebbian learning should enhance, not replace, existing system
- User trust requires interpretability
- Performance matters (can't be slow)
- Privacy matters (local learning only)

**Goal:** Make Penny feel more naturally intuitive, like she "gets" the user's patterns without being told explicitly.

---

## 🎊 **Ready to Design!**

Use your architectural expertise to create practical, implementable specifications for Penny's Hebbian Learning Layer.

**Focus on:** Clarity, practicality, and integration with existing system.

**When complete:** Notify user that specs are ready in `hebbian_specs/` directory.

---

**Good luck! 🧠✨**
