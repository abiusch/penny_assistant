# 🧠 Hebbian Learning Layer - Integration Plan

**Date:** October 27, 2025
**Status:** Design Specification
**Timeline:** 2 weeks (Weeks 9-10 of Phase 3)

---

## 📋 Table of Contents

1. [Overview & Strategy](#overview--strategy)
2. [Pre-Implementation Checklist](#pre-implementation-checklist)
3. [Week 9: Components 1 & 2](#week-9-components-1--2)
4. [Week 10: Component 3 & Integration](#week-10-component-3--integration)
5. [Testing Strategy](#testing-strategy)
6. [Rollout Plan](#rollout-plan)
7. [Rollback Procedures](#rollback-procedures)

---

## Overview & Strategy

### **Integration Philosophy**

1. **Modular Addition** - Add Hebbian components without modifying existing personality system
2. **Feature Flag Control** - All changes gated by `HEBBIAN_LEARNING_ENABLED` flag
3. **Gradual Rollout** - Enable one component at a time for validation
4. **Performance First** - Monitor latency at each step, rollback if >10ms overhead
5. **Backward Compatible** - System works with or without Hebbian layer

### **Success Criteria**

| Metric | Target | Validation Method |
|--------|--------|-------------------|
| Latency Impact | <10ms per turn | Profiling with cProfile |
| Vocabulary Accuracy | >80% | Test set validation |
| Co-activation Accuracy | >75% | Validation against actual patterns |
| Sequence Prediction | >70% satisfaction | User feedback |
| System Stability | 100% uptime | No crashes during 100-conversation test |

---

## Pre-Implementation Checklist

### **Environment Setup**

```bash
# 1. Create feature branch
cd /Users/CJ/Desktop/penny_assistant
git checkout -b feature/hebbian-learning

# 2. Backup database
cp data/personality_tracking.db data/personality_tracking.db.backup

# 3. Install any new dependencies (if needed)
pip3 install networkx matplotlib pandas  # For visualization

# 4. Create Hebbian module directory
mkdir -p src/personality/hebbian

# 5. Set feature flag (OFF by default)
echo "HEBBIAN_LEARNING_ENABLED=false" >> .env
```

### **Verification Steps**

- [ ] Existing tests pass: `pytest tests/`
- [ ] Database backup created
- [ ] Feature branch created
- [ ] Dependencies installed
- [ ] `.env` file has `HEBBIAN_LEARNING_ENABLED=false`

---

## Week 9: Components 1 & 2

### **Day 1-2: Database Schema + Vocabulary Associator**

#### **Step 1: Apply Database Schema**

```bash
# Apply Hebbian database schema
sqlite3 data/personality_tracking.db < hebbian_specs/HEBBIAN_DATABASE_SCHEMA.sql

# Verify tables created
sqlite3 data/personality_tracking.db ".tables" | grep -E "vocab|coact|hebbian"
```

**Expected Output:**
```
vocab_associations
vocab_context_observations
vocab_overrides
dimension_coactivations
coactivation_observations
multi_dim_patterns
negative_correlations
conversation_state_transitions
state_sequences
pattern_templates
state_classification_log
hebbian_config
hebbian_stats
hebbian_performance_log
```

**Files to Modify:** None yet (schema only)

---

#### **Step 2: Implement Vocabulary Associator**

**Create Files:**
1. `src/personality/hebbian_types.py` (copy from skeletons)
2. `src/personality/hebbian_config.py` (copy from skeletons)
3. `src/personality/hebbian_vocabulary_associator.py` (implement from skeleton)

**Implementation Checklist:**

- [ ] `__init__()` - Database connection, table creation
- [ ] `observe_term_in_context()` - Hebbian strengthening algorithm
- [ ] `observe_conversation()` - Term extraction and batch observation
- [ ] `get_association_strength()` - Query with caching
- [ ] `should_use_term()` - Prediction with threshold
- [ ] `filter_response_vocabulary()` - Response filtering
- [ ] `apply_temporal_decay()` - Decay unused associations
- [ ] `export_association_matrix()` - Debug export

**Unit Tests:**

```bash
# Create test file
touch tests/test_hebbian_vocabulary.py

# Run tests
pytest tests/test_hebbian_vocabulary.py -v
```

**Test Cases:**
1. `test_observe_strengthens_association` - Verify Hebbian strengthening
2. `test_competitive_weakening` - Verify other contexts weaken
3. `test_should_use_term_threshold` - Verify prediction logic
4. `test_temporal_decay` - Verify decay formula
5. `test_filter_response` - Verify vocabulary filtering

---

#### **Step 3: Integration Point 1 - Post-Processing**

**File to Modify:** `research_first_pipeline.py`

**Location:** Lines 200-217 (post-processing section)

**Changes:**

```python
# BEFORE (existing code):
result = asyncio.run(
    self.personality_post_processor.process_response(
        final_response,
        context={'topic': 'general', 'query': actual_command}
    )
)

# AFTER (with Hebbian):
import os
HEBBIAN_ENABLED = os.getenv("HEBBIAN_LEARNING_ENABLED", "false").lower() == "true"

if HEBBIAN_ENABLED:
    from src.personality.hebbian_vocabulary_associator import HebbianVocabularyAssociator

    # Initialize vocab associator (do this in __init__ for production)
    if not hasattr(self, 'vocab_associator'):
        self.vocab_associator = HebbianVocabularyAssociator()

    # Determine context type
    context_type = self._determine_context_type(actual_command, turn_context)

    # Filter vocabulary before post-processing
    final_response = self.vocab_associator.filter_response_vocabulary(
        response=final_response,
        context=context_type,
        threshold=0.65
    )

# Existing post-processing
result = asyncio.run(
    self.personality_post_processor.process_response(
        final_response,
        context={'topic': 'general', 'query': actual_command}
    )
)
```

**New Helper Method:**

```python
def _determine_context_type(self, user_input: str, context: Dict) -> str:
    """
    Determine conversation context type for vocabulary association

    Args:
        user_input: User's message
        context: Turn context

    Returns:
        str: Context type (casual_chat, formal_technical, etc.)
    """
    # Check formality and technical depth
    formality = context.get('formality', 0.5)
    technical = context.get('technical_depth', 0.5)

    # Simple heuristic (can be improved)
    if formality > 0.7 and technical > 0.6:
        return 'formal_technical'
    elif formality < 0.4 and technical < 0.5:
        return 'casual_chat'
    elif 'error' in user_input.lower() or 'stuck' in user_input.lower():
        return 'problem_solving'
    elif 'stressed' in user_input.lower() or 'confused' in user_input.lower():
        return 'emotional_support'
    elif 'quick' in user_input.lower() or 'brief' in user_input.lower():
        return 'quick_query'
    else:
        return 'creative_discussion'
```

**Testing:**

```bash
# Enable feature flag
export HEBBIAN_LEARNING_ENABLED=true

# Run server and test
python3 -m web_interface.app

# Test conversation with casual slang
# Input: "ngl this is pretty cool"
# Expected: Vocabulary observed, associations updated

# Check database
sqlite3 data/personality_tracking.db "SELECT * FROM vocab_associations WHERE term='ngl';"
```

---

### **Day 3-4: Dimension Associator**

#### **Step 4: Implement Dimension Associator**

**Create File:**
- `src/personality/hebbian_dimension_associator.py` (implement from skeleton)

**Implementation Checklist:**

- [ ] `__init__()` - Database connection
- [ ] `observe_activations()` - Pairwise co-activation updates
- [ ] `get_coactivation_strength()` - Query with caching
- [ ] `predict_coactivations()` - Prediction algorithm
- [ ] `get_strongest_coactivations()` - Top co-activations
- [ ] `detect_negative_correlations()` - Anti-correlation detection
- [ ] `export_coactivation_matrix()` - Debug export
- [ ] `visualize_coactivation_network()` - NetworkX visualization

**Unit Tests:**

```bash
pytest tests/test_hebbian_dimensions.py -v
```

**Test Cases:**
1. `test_observe_strengthens_coactivation` - Verify Hebbian co-activation
2. `test_predict_coactivations` - Verify prediction logic
3. `test_multi_dim_patterns` - Verify pattern detection
4. `test_negative_correlations` - Verify anti-correlation detection

---

#### **Step 5: Integration Point 2 - Prompt Building**

**File to Modify:** `research_first_pipeline.py`

**Location:** Lines 150-168 (prompt building section)

**Changes:**

```python
# BEFORE (existing code):
personality_enhancement = asyncio.run(
    self.personality_prompt_builder.build_personality_prompt(
        user_id="default",
        context={'topic': 'general', 'query': user_input}
    )
)

# AFTER (with Hebbian):
if HEBBIAN_ENABLED:
    from src.personality.hebbian_dimension_associator import HebbianDimensionAssociator

    # Initialize dim associator (do this in __init__ for production)
    if not hasattr(self, 'dim_associator'):
        self.dim_associator = HebbianDimensionAssociator()

    # Get current personality dimensions
    current_dims = await self.personality_tracker.get_current_personality_state()

    # Get high-confidence dimensions
    known_dims = {
        dim: state.current_value
        for dim, state in current_dims.items()
        if state.confidence > 0.65
    }

    # Predict co-activations
    predicted_dims = self.dim_associator.predict_coactivations(
        known_dimensions=known_dims,
        threshold=0.65
    )

    # Add predictions to context
    context_enhanced = {
        'topic': 'general',
        'query': user_input,
        'predicted_coactivations': predicted_dims
    }
else:
    context_enhanced = {'topic': 'general', 'query': user_input}

# Build prompt with predictions
personality_enhancement = asyncio.run(
    self.personality_prompt_builder.build_personality_prompt(
        user_id="default",
        context=context_enhanced
    )
)
```

**Testing:**

```bash
# Simulate stressed user scenario 5 times
# Input: "I'm so confused, help!"
# Observe: emotional_support=0.85, brief=0.9, simple=0.8

# On 6th message with high empathy, check if brief+simple predicted
# Expected: Co-activation prediction appears in logs
```

---

### **Day 5: Week 9 Integration Testing**

#### **Integration Test 1: Vocabulary Learning**

```python
# Test: Observe "ngl" in casual context 10 times
for i in range(10):
    pipeline.process_turn(f"ngl option {i} seems better")

# Verify: Association strength increased
strength = vocab_associator.get_association_strength("ngl", "casual_chat")
assert strength > 0.6

# Verify: Should use in casual, not in formal
assert vocab_associator.should_use_term("ngl", "casual_chat") == True
assert vocab_associator.should_use_term("ngl", "formal_technical") == False
```

#### **Integration Test 2: Dimension Co-activation**

```python
# Test: Observe stressed pattern 5 times
for i in range(5):
    dim_associator.observe_activations({
        'emotional_support_style': 0.85,
        'response_length_preference': 0.2,  # Brief
        'technical_depth_preference': 0.3   # Simple
    })

# Verify: Co-activations strengthened
coact = dim_associator.get_coactivation_strength(
    'emotional_support_style', 'response_length_preference'
)
assert coact > 0.1

# Verify: Prediction works
predictions = dim_associator.predict_coactivations(
    {'emotional_support_style': 0.8}
)
assert 'response_length_preference' in predictions
```

---

## Week 10: Component 3 & Integration

### **Day 6-7: Sequence Learner**

#### **Step 6: Implement Sequence Learner**

**Create File:**
- `src/personality/hebbian_sequence_learner.py` (implement from skeleton)

**Implementation Checklist:**

- [ ] `__init__()` - Database connection, load classification rules
- [ ] `classify_conversation_state()` - State classification algorithm
- [ ] `observe_transition()` - Markov chain updates
- [ ] `get_transition_probability()` - Query transitions
- [ ] `predict_next_states()` - State prediction
- [ ] `detect_recurring_patterns()` - Pattern detection
- [ ] `anticipate_user_need()` - Anticipation logic
- [ ] `export_transition_matrix()` - Debug export
- [ ] `visualize_state_graph()` - Graph visualization

**Unit Tests:**

```bash
pytest tests/test_hebbian_sequences.py -v
```

**Test Cases:**
1. `test_classify_problem_statement` - Verify state classification
2. `test_transition_probability` - Verify Markov updates
3. `test_predict_next_states` - Verify prediction
4. `test_detect_recurring_pattern` - Verify pattern detection
5. `test_anticipate_simplification` - Verify anticipation

---

#### **Step 7: Integration Point 3 - Conversation Learning**

**File to Modify:** `research_first_pipeline.py`

**Location:** Lines 240-250 (after memory save)

**Changes:**

```python
# AFTER existing personality update:
self._update_personality_from_conversation(
    actual_command, final_response, turn.turn_id
)

# NEW: Hebbian learning updates
if HEBBIAN_ENABLED:
    self._update_hebbian_associations(
        user_input=actual_command,
        assistant_response=final_response,
        context=turn_context,
        active_dimensions=current_dims
    )
```

**New Method:**

```python
def _update_hebbian_associations(
    self,
    user_input: str,
    assistant_response: str,
    context: Dict,
    active_dimensions: Dict
):
    """
    Update Hebbian associations after conversation turn

    Args:
        user_input: User's message
        assistant_response: Assistant's response
        context: Turn context
        active_dimensions: Current personality dimensions
    """
    if not HEBBIAN_ENABLED:
        return

    from src.personality.hebbian_learning_manager import HebbianLearningManager

    # Initialize manager if not exists
    if not hasattr(self, 'hebbian_manager'):
        self.hebbian_manager = HebbianLearningManager()

    # Process turn through all Hebbian components
    try:
        result = self.hebbian_manager.process_conversation_turn(
            user_message=user_input,
            assistant_response=assistant_response,
            context=context,
            active_dimensions={
                dim: state.current_value
                for dim, state in active_dimensions.items()
            }
        )

        # Log results
        print(f"🧠 Hebbian learning: {result['vocab_observations']} vocab, "
              f"{result['coactivations_updated']} coactivations, "
              f"{result['state_transitions']} transitions "
              f"({result['latency_ms']:.1f}ms)", flush=True)

    except Exception as e:
        logger.error(f"Hebbian learning update failed: {e}")
        import traceback
        traceback.print_exc()
```

---

### **Day 8: Hebbian Learning Manager**

#### **Step 8: Implement Manager**

**Create File:**
- `src/personality/hebbian_learning_manager.py` (implement from skeleton)

**Implementation Checklist:**

- [ ] `__init__()` - Initialize all components
- [ ] `process_conversation_turn()` - Main entry point
- [ ] `should_use_term_cached()` - Cached vocabulary lookup
- [ ] `predict_coactivations_cached()` - Cached prediction
- [ ] `apply_temporal_decay_all()` - Decay all components
- [ ] `refresh_caches()` - Cache maintenance
- [ ] `export_all_data()` - Export for analysis
- [ ] `get_system_stats()` - Statistics
- [ ] `get_health_summary()` - Health monitoring

**Implementation:**

```python
def process_conversation_turn(
    self,
    user_message: str,
    assistant_response: str,
    context: Dict[str, Any],
    active_dimensions: Dict[str, float]
) -> Dict[str, Any]:
    """Main processing method"""

    start_time = time.time()
    result = {
        'vocab_observations': 0,
        'coactivations_updated': 0,
        'state_transitions': 0,
        'predictions': {},
        'latency_ms': 0
    }

    # 1. Classify conversation state
    conversation_state = self.sequence_learner.classify_conversation_state(
        user_message, context
    )

    # 2. Determine context type for vocabulary
    context_type = self._determine_context_type(user_message, context)

    # 3. Observe vocabulary
    observed_terms = self.vocab_associator.observe_conversation(
        user_message, context_type
    )
    result['vocab_observations'] = len(observed_terms)

    # 4. Observe dimension co-activations
    self.dim_associator.observe_activations(active_dimensions)
    result['coactivations_updated'] = len(active_dimensions)

    # 5. Observe state transition
    if hasattr(self, 'previous_state') and self.previous_state:
        self.sequence_learner.observe_transition(
            self.previous_state,
            conversation_state
        )
        result['state_transitions'] = 1

    self.previous_state = conversation_state

    # 6. Generate predictions for next turn
    result['predictions'] = {
        'next_states': self.sequence_learner.predict_next_states(
            conversation_state, self.sequence_learner.conversation_history
        ),
        'coactivations': self.dim_associator.predict_coactivations(
            {k: v for k, v in active_dimensions.items() if v > 0.6}
        )
    }

    # 7. Update statistics
    self.conversation_count += 1

    # 8. Refresh caches if needed
    if self.conversation_count % self.cache_refresh_interval == 0:
        self.refresh_caches()

    result['latency_ms'] = (time.time() - start_time) * 1000
    return result
```

---

### **Day 9: Full System Testing**

#### **End-to-End Test Suite**

```python
# tests/test_hebbian_integration.py

def test_full_pipeline_with_hebbian():
    """Test complete pipeline with Hebbian enabled"""

    # Enable Hebbian
    os.environ["HEBBIAN_LEARNING_ENABLED"] = "true"

    pipeline = ResearchFirstPipeline()

    # Process 10 conversations
    for i in range(10):
        response = pipeline.process_turn(f"Test message {i}")
        assert response is not None

    # Verify Hebbian data was created
    with sqlite3.connect("data/personality_tracking.db") as conn:
        cursor = conn.cursor()

        # Check vocab associations
        vocab_count = cursor.execute("SELECT COUNT(*) FROM vocab_associations").fetchone()[0]
        assert vocab_count > 0

        # Check coactivations
        coact_count = cursor.execute("SELECT COUNT(*) FROM dimension_coactivations").fetchone()[0]
        assert coact_count > 0

        # Check transitions
        trans_count = cursor.execute("SELECT COUNT(*) FROM conversation_state_transitions").fetchone()[0]
        assert trans_count > 0


def test_hebbian_disabled_still_works():
    """Verify system works with Hebbian disabled"""

    # Disable Hebbian
    os.environ["HEBBIAN_LEARNING_ENABLED"] = "false"

    pipeline = ResearchFirstPipeline()

    # Process conversation
    response = pipeline.process_turn("Test message")
    assert response is not None


def test_performance_within_budget():
    """Verify Hebbian adds <10ms latency"""

    import time

    # Test with Hebbian disabled
    os.environ["HEBBIAN_LEARNING_ENABLED"] = "false"
    pipeline_no_hebb = ResearchFirstPipeline()

    start = time.time()
    for i in range(10):
        pipeline_no_hebb.process_turn(f"Test {i}")
    time_no_hebb = (time.time() - start) / 10

    # Test with Hebbian enabled
    os.environ["HEBBIAN_LEARNING_ENABLED"] = "true"
    pipeline_with_hebb = ResearchFirstPipeline()

    start = time.time()
    for i in range(10):
        pipeline_with_hebb.process_turn(f"Test {i}")
    time_with_hebb = (time.time() - start) / 10

    # Verify overhead < 10ms per turn
    overhead = (time_with_hebb - time_no_hebb) * 1000
    assert overhead < 10, f"Hebbian overhead {overhead:.1f}ms exceeds 10ms budget"
```

---

### **Day 10: Documentation & Final Testing**

#### **Step 9: Create User Documentation**

**Create File:** `docs/HEBBIAN_LEARNING_GUIDE.md`

**Contents:**
- What is Hebbian learning?
- How to enable/disable
- How to monitor learning
- How to export/analyze data
- How to debug issues
- Performance tips

#### **Step 10: Performance Profiling**

```bash
# Profile Hebbian components
python3 -m cProfile -o hebbian_profile.stats \
    -c "from src.personality.hebbian_learning_manager import *; test_full_pipeline()"

# Analyze results
python3 -c "import pstats; p = pstats.Stats('hebbian_profile.stats'); p.sort_stats('cumulative').print_stats(20)"
```

**Verify:**
- `observe_term_in_context()` < 2ms
- `observe_activations()` < 3ms
- `observe_transition()` < 2ms
- `process_conversation_turn()` < 10ms total

#### **Step 11: Create Monitoring Dashboard**

**Add to Web Interface:** `web_interface/templates/hebbian_dashboard.html`

**Features:**
- Top vocabulary associations
- Strongest co-activations visualized
- Common conversation patterns
- System health indicators
- Performance metrics

---

## Testing Strategy

### **Unit Tests** (30 tests total)

```bash
# Run all Hebbian unit tests
pytest tests/test_hebbian_*.py -v --cov=src/personality/hebbian

# Expected coverage: >80%
```

**Test Categories:**
1. Vocabulary Associator: 10 tests
2. Dimension Associator: 8 tests
3. Sequence Learner: 7 tests
4. Learning Manager: 5 tests

### **Integration Tests** (10 tests)

```bash
# Run integration tests
pytest tests/test_hebbian_integration.py -v
```

**Test Scenarios:**
1. Full pipeline with Hebbian enabled
2. Full pipeline with Hebbian disabled (backward compatibility)
3. Performance within budget
4. Database consistency
5. Cache correctness
6. Decay mechanics
7. Export functionality
8. Error handling
9. Feature flag toggling
10. Multi-user isolation (future)

### **System Tests** (5 scenarios)

**Scenario 1: 100-Conversation Stress Test**

```python
for i in range(100):
    pipeline.process_turn(f"Conversation {i}")

# Verify:
# - No crashes
# - Database size < 1MB growth
# - Performance stable
# - All associations valid (0.0-1.0)
```

**Scenario 2: Real User Simulation**

```python
# Simulate realistic conversation patterns
conversations = [
    ("ngl I'm stuck on this async code", "casual_chat", "problem"),
    ("Can you simplify that?", "quick_query", "simplification"),
    ("Perfect thanks!", "casual_chat", "positive_feedback"),
    # ... 50 more realistic examples
]

for msg, context, state in conversations:
    pipeline.process_turn(msg)

# Verify learned patterns match expectations
```

**Scenario 3: Edge Cases**

- Empty messages
- Very long messages (10,000+ chars)
- Special characters / Unicode
- SQL injection attempts
- Rapid-fire messages (stress test)

**Scenario 4: Database Recovery**

- Corrupt database file
- Missing tables
- Invalid strengths (outside 0.0-1.0)
- Orphaned observations

**Scenario 5: Performance Degradation**

- 1,000 conversations
- 10,000 vocabulary associations
- Check if queries remain <1ms

---

## Rollout Plan

### **Phase 1: Internal Testing (Days 1-10)**

- ✅ All unit tests pass
- ✅ All integration tests pass
- ✅ System tests pass
- ✅ Performance within budget
- ✅ Documentation complete

### **Phase 2: Staged Rollout (Days 11-12)**

**Day 11 Morning: Vocabulary Only**

```bash
# Enable only vocabulary associator
export HEBBIAN_VOCAB_ENABLED=true
export HEBBIAN_DIM_ENABLED=false
export HEBBIAN_SEQ_ENABLED=false

# Test with 20 conversations
# Monitor for issues
```

**Day 11 Afternoon: Add Dimensions**

```bash
export HEBBIAN_DIM_ENABLED=true

# Test with 20 more conversations
# Verify co-activation predictions
```

**Day 12 Morning: Add Sequences**

```bash
export HEBBIAN_SEQ_ENABLED=true

# Test with 20 more conversations
# Verify anticipation works
```

**Day 12 Afternoon: Full Enable**

```bash
export HEBBIAN_LEARNING_ENABLED=true

# Full system active
# Monitor for 50 conversations
```

### **Phase 3: Production (Days 13-14)**

**Day 13: Deploy to Main**

```bash
# Merge feature branch
git checkout main
git merge feature/hebbian-learning

# Set feature flag in production
echo "HEBBIAN_LEARNING_ENABLED=true" >> .env

# Restart server
pkill -f "python3.*web_interface"
python3 -m web_interface.app
```

**Day 14: Monitor & Tune**

- Watch logs for errors
- Monitor database growth
- Check performance metrics
- Adjust learning rates if needed
- User feedback collection

---

## Rollback Procedures

### **Emergency Rollback: Disable Feature Flag**

```bash
# Quickest rollback - disable via environment variable
export HEBBIAN_LEARNING_ENABLED=false

# Restart server
pkill -f "python3.*web_interface"
python3 -m web_interface.app

# System continues without Hebbian, all existing functionality intact
```

**Time to Rollback:** <30 seconds

---

### **Partial Rollback: Disable Specific Component**

```bash
# Disable only problematic component
export HEBBIAN_VOCAB_ENABLED=false  # If vocabulary has issues
export HEBBIAN_DIM_ENABLED=false    # If dimensions have issues
export HEBBIAN_SEQ_ENABLED=false    # If sequences have issues

# Other components continue working
```

---

### **Full Rollback: Revert Code Changes**

```bash
# Revert to previous commit
git revert HEAD

# Or restore from backup
git checkout main~1

# Restart server
python3 -m web_interface.app
```

**Time to Rollback:** <5 minutes

---

### **Database Rollback: Restore Backup**

```bash
# If database corrupted
cp data/personality_tracking.db.backup data/personality_tracking.db

# Optionally remove Hebbian tables
sqlite3 data/personality_tracking.db <<EOF
DROP TABLE IF EXISTS vocab_associations;
DROP TABLE IF EXISTS vocab_context_observations;
DROP TABLE IF EXISTS dimension_coactivations;
-- ... (all Hebbian tables)
EOF
```

**Time to Rollback:** <2 minutes

---

## File Modification Summary

### **New Files Created** (6 Python + 1 SQL + 3 Tests)

```
src/personality/
├── hebbian_types.py                    # NEW - Data types
├── hebbian_config.py                   # NEW - Configuration
├── hebbian_vocabulary_associator.py    # NEW - Component 1
├── hebbian_dimension_associator.py     # NEW - Component 2
├── hebbian_sequence_learner.py         # NEW - Component 3
└── hebbian_learning_manager.py         # NEW - Orchestrator

tests/
├── test_hebbian_vocabulary.py          # NEW - Unit tests
├── test_hebbian_dimensions.py          # NEW - Unit tests
├── test_hebbian_sequences.py           # NEW - Unit tests
└── test_hebbian_integration.py         # NEW - Integration tests

hebbian_specs/
└── HEBBIAN_DATABASE_SCHEMA.sql         # NEW - Database schema

docs/
└── HEBBIAN_LEARNING_GUIDE.md           # NEW - User guide
```

### **Files Modified** (1 core file)

```
research_first_pipeline.py:
  - Line ~27: Add Hebbian imports
  - Line ~48: Initialize Hebbian components
  - Line ~210: Add vocabulary filtering
  - Line ~165: Add co-activation predictions
  - Line ~245: Add Hebbian learning updates
  - Lines ~250-290: New method _update_hebbian_associations()
  - Lines ~295-310: New method _determine_context_type()
```

**Total Lines Added:** ~350 lines to `research_first_pipeline.py`

### **Files Not Modified** (Backward Compatible)

```
✅ personality_tracker.py - No changes
✅ dynamic_personality_prompt_builder.py - No changes
✅ personality_response_post_processor.py - No changes
✅ emotional_memory_system.py - No changes
✅ slang_vocabulary_tracker.py - No changes
```

---

## Risk Mitigation

### **Risk 1: Performance Degradation**

**Mitigation:**
- Feature flag allows instant disable
- LRU caching for hot paths
- Batch database updates
- Profiling at each step

**Monitoring:**
- Log latency per component
- Alert if >10ms
- Auto-disable if >20ms

---

### **Risk 2: Database Corruption**

**Mitigation:**
- Backup before rollout
- Transaction wrapping
- Constraint checks
- Regular integrity checks

**Recovery:**
- Restore from backup (<2 min)
- Rebuild tables from scratch

---

### **Risk 3: Incorrect Predictions**

**Mitigation:**
- Confidence thresholds
- Manual override system
- User feedback collection
- A/B testing

**Monitoring:**
- Track prediction accuracy
- User satisfaction signals
- False positive rate

---

### **Risk 4: Memory Leak**

**Mitigation:**
- LRU cache with size limits
- Database pruning
- Temporal decay
- Regular monitoring

**Monitoring:**
- Memory usage tracking
- Database size alerts
- Cache hit rates

---

## Success Metrics & KPIs

### **Week 9 End Goals**

- [ ] Vocabulary associator passes all tests
- [ ] Dimension associator passes all tests
- [ ] Integration points 1 & 2 working
- [ ] Performance <5ms overhead
- [ ] No regressions in existing tests

### **Week 10 End Goals**

- [ ] Sequence learner passes all tests
- [ ] Full integration complete
- [ ] All 45 tests passing
- [ ] Performance <10ms overhead
- [ ] Documentation complete
- [ ] Staged rollout successful

### **Post-Launch Goals (Week 11)**

- [ ] 100 conversations processed successfully
- [ ] Vocabulary accuracy >80%
- [ ] Co-activation accuracy >75%
- [ ] Sequence prediction satisfaction >70%
- [ ] Zero crashes or data loss
- [ ] User satisfaction maintained

---

## Post-Integration Maintenance

### **Daily Tasks**

```bash
# Check system health
python3 -c "from src.personality.hebbian_learning_manager import *; print(manager.get_health_summary())"

# Apply temporal decay (if not automated)
python3 -c "from src.personality.hebbian_learning_manager import *; manager.apply_temporal_decay_all()"
```

### **Weekly Tasks**

```bash
# Export data for analysis
python3 -c "from src.personality.hebbian_learning_manager import *; manager.export_all_data().to_csv('hebbian_export.csv')"

# Prune weak associations
python3 -c "from src.personality.hebbian_learning_manager import *; manager.prune_all(min_strength=0.1)"

# Check database size
ls -lh data/personality_tracking.db
```

### **Monthly Tasks**

- Review top associations for accuracy
- Analyze co-activation network
- Check for stale patterns
- Update configuration if needed
- User feedback review

---

## Contact & Escalation

**Implementation Questions:**
- Refer to: `HEBBIAN_LEARNING_SPECS.md`
- Refer to: `HEBBIAN_IMPLEMENTATION_SKELETONS.md`

**Database Issues:**
- Refer to: `HEBBIAN_DATABASE_SCHEMA.sql`
- Backup location: `data/personality_tracking.db.backup`

**Integration Issues:**
- Check feature flag: `echo $HEBBIAN_LEARNING_ENABLED`
- Check logs: `tail -f penny.log | grep -i hebbian`
- Emergency disable: `export HEBBIAN_LEARNING_ENABLED=false`

---

## Appendix: Quick Reference Commands

### **Enable/Disable Hebbian**

```bash
# Enable
export HEBBIAN_LEARNING_ENABLED=true

# Disable
export HEBBIAN_LEARNING_ENABLED=false

# Check status
echo $HEBBIAN_LEARNING_ENABLED
```

### **Database Queries**

```bash
# Check vocabulary associations
sqlite3 data/personality_tracking.db "SELECT * FROM vocab_associations LIMIT 10;"

# Check co-activations
sqlite3 data/personality_tracking.db "SELECT * FROM dimension_coactivations LIMIT 10;"

# Check transitions
sqlite3 data/personality_tracking.db "SELECT * FROM conversation_state_transitions LIMIT 10;"

# System health
sqlite3 data/personality_tracking.db "SELECT * FROM v_hebbian_health;"
```

### **Testing Commands**

```bash
# Run all Hebbian tests
pytest tests/test_hebbian_*.py -v

# Run with coverage
pytest tests/test_hebbian_*.py --cov=src/personality/hebbian --cov-report=html

# Run integration tests only
pytest tests/test_hebbian_integration.py -v

# Profile performance
python3 -m cProfile -s cumulative -c "from tests.test_hebbian_integration import *; test_full_pipeline()"
```

---

**Status:** ✅ Integration Plan Complete
**Ready for Implementation:** Week 9-10 of Phase 3

---

*Designed for Penny's Phase 3E Enhancement - October 27, 2025*
