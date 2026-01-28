# Week 9 Complete: Hebbian Learning Layer

**Date:** January 28, 2026
**Status:** COMPLETE
**Tests:** 138/138 passing (75 Hebbian + 63 Week 8.5)

---

## Summary

Week 9 implemented the Hebbian Learning Layer for Penny - a neural-inspired system that learns from conversation patterns to improve personality adaptation over time.

### "Neurons that fire together, wire together"

The Hebbian learning principle enables Penny to:
1. Learn which vocabulary fits which contexts
2. Discover personality dimensions that work well together
3. Predict conversation flow patterns

---

## Components Implemented

### 1. HebbianVocabularyAssociator (~400 lines)
**Purpose:** Learn vocabulary-context associations

**Key Methods:**
- `observe_term_in_context()` - Hebbian strengthening: `Δw = η * (1 - w)`
- `observe_conversation()` - Extract and learn from user messages
- `should_use_term()` - Predict term appropriateness
- `apply_temporal_decay()` - Forget unused associations

**Example:**
```python
# After observing "ngl" in casual contexts 10 times:
associator.should_use_term("ngl", "casual_chat")     # True
associator.should_use_term("ngl", "formal_technical") # False
```

### 2. HebbianDimensionAssociator (~380 lines)
**Purpose:** Learn personality dimension co-activations

**Key Methods:**
- `observe_activations()` - Hebbian co-activation: `Δw = η * x1 * x2`
- `predict_coactivations()` - Predict unknown dimensions
- `get_multi_dim_patterns()` - Detect recurring patterns

**Example:**
```python
# When empathy is high, Penny learns to also use brief responses:
predictions = dim_associator.predict_coactivations({
    'emotional_support_style': 0.85
})
# Returns: {'response_length_preference': 0.2 (brief)}
```

### 3. HebbianSequenceLearner (~500 lines)
**Purpose:** Learn conversation flow patterns

**Key Methods:**
- `classify_conversation_state()` - 12 conversation states
- `observe_transition()` - Markov chain learning
- `predict_next_states()` - Anticipate user needs
- `detect_recurring_patterns()` - Find common sequences

**Conversation States:**
- problem_statement, clarification_question
- technical_explanation, simplified_explanation
- positive_feedback, frustration_expression
- follow_up_question, code_review
- debugging_help, opinion_request
- casual_chat, correction_request

---

## Database Schema

15 new tables added to `personality_tracking.db`:

**Vocabulary Tables:**
- `vocab_associations` - Term-context strengths
- `vocab_context_observations` - Observation log
- `vocab_overrides` - Manual term blocks

**Dimension Tables:**
- `dimension_coactivations` - Pairwise strengths
- `coactivation_observations` - Observation log
- `multi_dim_patterns` - 3+ dimension patterns
- `negative_correlations` - Anti-correlated dims

**Sequence Tables:**
- `conversation_state_transitions` - Markov chain
- `state_sequences` - N-gram patterns
- `pattern_templates` - Actionable patterns

**System Tables:**
- `hebbian_config` - Configuration storage
- `hebbian_stats` - Learning statistics
- `hebbian_performance_log` - Latency tracking

---

## Test Results

```
tests/test_hebbian_vocabulary.py     24 tests ✓
tests/test_hebbian_dimensions.py     15 tests ✓
tests/test_hebbian_integration.py    14 tests ✓
tests/test_hebbian_sequences.py      22 tests ✓
────────────────────────────────────────────────
Total Hebbian Tests:                 75 tests ✓

Combined with Week 8.5:             138 tests ✓
```

### Test Categories:
- **Learning Mechanics:** Hebbian strengthening, competitive weakening
- **Prediction:** Term recommendations, co-activation predictions
- **Patterns:** Multi-dim detection, sequence patterns
- **Performance:** <10ms overhead verified
- **Persistence:** Data survives reconnection
- **Edge Cases:** Empty inputs, invalid contexts

---

## Performance Metrics

| Operation | Target | Actual |
|-----------|--------|--------|
| Vocabulary observation | <3ms | ~1ms |
| Dimension observation | <3ms | ~1ms |
| Vocabulary query | <1ms | <0.5ms |
| Dimension prediction | <3ms | ~1ms |
| State classification | <2ms | ~1ms |
| **Total overhead** | **<10ms** | **~5ms** |

---

## What Penny Learned (Conceptually)

### Vocabulary Associations
```
"ngl"  → casual_chat (0.85), problem_solving (0.60)
"tbh"  → casual_chat (0.82), emotional_support (0.55)
"please" → formal_technical (0.78), quick_query (0.60)
```

### Dimension Co-activations
```
emotional_support ↔ brief_responses (0.72)
high_empathy ↔ simple_explanations (0.68)
technical_depth ↔ longer_responses (0.65)
```

### Conversation Patterns
```
problem_statement → clarification_question (0.45)
clarification_question → positive_feedback (0.38)
technical_explanation → simplified_explanation (0.32)
```

---

## Files Created

```
src/personality/hebbian/
├── __init__.py                      # Module exports
├── hebbian_types.py                 # Data classes, enums, constants
├── hebbian_config.py                # Configuration management
├── hebbian_vocabulary_associator.py # Vocabulary learning
├── hebbian_dimension_associator.py  # Dimension co-activation
└── hebbian_sequence_learner.py      # Sequence learning

tests/
├── test_hebbian_vocabulary.py       # 24 tests
├── test_hebbian_dimensions.py       # 15 tests
├── test_hebbian_integration.py      # 14 tests
└── test_hebbian_sequences.py        # 22 tests
```

**Total Lines Added:** ~3,995

---

## Week 10 Preview

### Day 8: Hebbian Learning Manager
- `HebbianLearningManager` - Orchestrates all components
- Unified `process_conversation_turn()` method
- LRU caching for performance
- Batch updates for efficiency

### Day 9: Pipeline Integration
- Connect to `research_first_pipeline.py`
- Feature flag: `HEBBIAN_LEARNING_ENABLED`
- Integration with personality post-processor

### Day 10: Documentation & Tuning
- User documentation
- Performance profiling
- Learning rate tuning
- Visualization tools

---

## Commit

```
526d61e 🧠 Week 9 Hebbian Learning - Core Components Complete (138 tests)
```

---

*Week 9 of Phase 3E Enhancement - Penny's Neural Learning Layer*
