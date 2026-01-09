# 🧠 Hebbian Learning Layer - Architecture Overview

**Date:** October 27, 2025
**Status:** Design Specification
**Phase:** Phase 3E (Weeks 9-10)
**Estimated Implementation Time:** 8-12 hours

---

## 📋 Executive Summary

The Hebbian Learning Layer enhances Penny's personality system with neuroscience-inspired associative learning capabilities. Inspired by the principle "neurons that fire together, wire together," this layer learns implicit associations between:

1. **Vocabulary & Context** - Which words belong in which contexts
2. **Personality Dimensions** - Which dimensions naturally co-activate together
3. **Conversation Flow** - Sequential patterns in conversation states

**Key Design Principles:**
- ✅ Modular (can be disabled without breaking existing system)
- ✅ Performant (<10ms latency per component)
- ✅ Persistent (all associations survive restart)
- ✅ Debuggable (all associations viewable/exportable)
- ✅ Safe (decay mechanisms prevent runaway learning)

---

## 🎯 System Overview

### **Current Penny Architecture**

```
User Input
    ↓
┌─────────────────────────────────────────────────────┐
│ research_first_pipeline.py                          │
├─────────────────────────────────────────────────────┤
│ 1. Context Detection (time, mood indicators)        │
│ 2. Personality State Retrieval (from DB)            │
│ 3. Dynamic Prompt Building (confidence > 0.65)      │
│ 4. LLM Generation (GPT-4)                          │
│ 5. Response Post-Processing (formality, vocab)      │
│ 6. Personality Observation & Update                 │
└─────────────────────────────────────────────────────┘
    ↓
Response to User
```

### **Enhanced Architecture with Hebbian Layer**

```
User Input
    ↓
┌─────────────────────────────────────────────────────┐
│ research_first_pipeline.py                          │
├─────────────────────────────────────────────────────┤
│ 1. Context Detection                                │
│    └─> [NEW] Conversation State Classification      │
│                                                      │
│ 2. Personality State Retrieval                      │
│    └─> [NEW] Co-activation Prediction              │
│         (If empathy↑, also activate brief+simple)    │
│                                                      │
│ 3. Dynamic Prompt Building                          │
│    └─> [ENHANCED] Uses predicted co-activations     │
│                                                      │
│ 4. LLM Generation                                   │
│                                                      │
│ 5. Response Post-Processing                         │
│    └─> [NEW] Vocabulary Association Filtering       │
│         (Should "ngl" be used in this context?)      │
│                                                      │
│ 6. Personality Observation & Update                 │
│    └─> [NEW] Hebbian Learning Updates              │
│         • Strengthen co-occurring associations       │
│         • Weaken competing associations             │
│         • Record state transitions                  │
└─────────────────────────────────────────────────────┘
    ↓
Response to User
```

---

## 🧩 Component Architecture

### **Component 1: Vocabulary Association Matrix**

**Purpose:** Learn which vocabulary terms belong in which contexts

**Architecture:**
```
┌─────────────────────────────────────────────────────┐
│ HebbianVocabularyAssociator                         │
├─────────────────────────────────────────────────────┤
│ Data Structure:                                     │
│   Association Matrix: term × context → strength     │
│                                                      │
│ Key Methods:                                        │
│   • observe_term_in_context(term, context)          │
│   • get_association_strength(term, context)         │
│   • should_use_term(term, context) → bool           │
│   • decay_unused_associations()                     │
│   • export_matrix() → Dict                          │
│                                                      │
│ Database Tables:                                    │
│   • vocab_associations                              │
│   • vocab_context_observations                      │
└─────────────────────────────────────────────────────┘
```

**Context Types:**
- `casual_chat` - Informal conversation, opinions, hot takes
- `formal_technical` - Professional explanations, documentation
- `problem_solving` - Debugging, troubleshooting, analysis
- `creative_discussion` - Brainstorming, design, exploration
- `emotional_support` - Empathy, encouragement, validation
- `quick_query` - Brief questions, rapid-fire Q&A

**Learning Rule:**
```python
# Hebbian strengthening
if term appears in context:
    strength[term][context] += learning_rate * (1.0 - strength[term][context])

# Competitive weakening (other contexts)
for other_context in contexts:
    if other_context != context:
        strength[term][other_context] *= (1.0 - competitive_rate)
```

---

### **Component 2: Dimension Co-activation Matrix**

**Purpose:** Learn which personality dimensions naturally activate together

**Architecture:**
```
┌─────────────────────────────────────────────────────┐
│ HebbianDimensionAssociator                          │
├─────────────────────────────────────────────────────┤
│ Data Structure:                                     │
│   Co-activation Matrix: (dim1, dim2) → strength     │
│   Multi-dimensional Patterns: List[Pattern]         │
│                                                      │
│ Key Methods:                                        │
│   • observe_activations(dimensions: Dict[str, float])│
│   • predict_coactivations(known_dims) → Dict        │
│   • get_pattern_strength(dims: List[str]) → float   │
│   • detect_negative_correlations() → List[Tuple]    │
│   • export_coactivation_graph() → NetworkX         │
│                                                      │
│ Database Tables:                                    │
│   • dimension_coactivations                         │
│   • multi_dim_patterns                              │
│   • coactivation_observations                       │
└─────────────────────────────────────────────────────┘
```

**Personality Dimensions (from personality_tracker.py):**
1. `communication_formality` (0.0=casual, 1.0=formal)
2. `technical_depth_preference` (0.0=simple, 1.0=detailed)
3. `humor_style_preference` (categorical)
4. `response_length_preference` (categorical)
5. `conversation_pace_preference` (0.0=slow, 1.0=fast)
6. `proactive_suggestions` (0.0=reactive, 1.0=proactive)
7. `emotional_support_style` (categorical)

**Learning Rule:**
```python
# Hebbian co-activation
for dim1, val1 in active_dimensions.items():
    for dim2, val2 in active_dimensions.items():
        if dim1 != dim2 and val1 > threshold and val2 > threshold:
            coactivation[dim1][dim2] += η * val1 * val2

# Negative correlation detection
if dim1_high and dim2_low (consistently):
    negative_correlation[(dim1, dim2)] = strength
```

---

### **Component 3: Conversation Flow Pattern Learner**

**Purpose:** Learn sequential patterns in conversation states to anticipate user needs

**Architecture:**
```
┌─────────────────────────────────────────────────────┐
│ HebbianSequenceLearner                              │
├─────────────────────────────────────────────────────┤
│ Data Structure:                                     │
│   Transition Matrix: state1 × state2 → strength     │
│   Sequence History: List[StateSequence]             │
│   Pattern Templates: Dict[pattern_id, sequence]     │
│                                                      │
│ Key Methods:                                        │
│   • classify_conversation_state(message) → State    │
│   • observe_transition(from_state, to_state)        │
│   • predict_next_states(current) → List[State]      │
│   • detect_recurring_patterns() → List[Pattern]     │
│   • anticipate_user_need(history) → Optional[Action]│
│                                                      │
│ Database Tables:                                    │
│   • conversation_state_transitions                  │
│   • state_sequences                                 │
│   • recurring_patterns                              │
└─────────────────────────────────────────────────────┘
```

**Conversation States:**
```python
CONVERSATION_STATES = [
    'problem_statement',      # "I'm stuck on X"
    'clarification_question', # "Can you explain Y?"
    'technical_explanation',  # Detailed response
    'simplified_explanation', # ELI5-style response
    'code_review',           # Code analysis
    'debugging_help',        # Troubleshooting
    'opinion_request',       # "What do you think?"
    'casual_chat',           # Non-technical conversation
    'follow_up_question',    # Continuation of previous topic
    'positive_feedback',     # "Perfect, thanks!"
    'correction_request',    # "No, I meant..."
    'frustration_expression' # "This is confusing"
]
```

**Learning Rule:**
```python
# Markov chain transition strengthening
transition_count[state_from][state_to] += 1
transition_prob[state_from][state_to] = (
    transition_count[state_from][state_to] /
    sum(transition_count[state_from].values())
)

# Pattern template detection (n-gram approach)
if sequence appears N times:
    pattern_templates[sequence_id] = {
        'sequence': [state1, state2, state3, ...],
        'frequency': N,
        'avg_satisfaction': score,
        'skip_opportunity': state2  # Which state could be skipped
    }
```

---

## 🔗 Data Flow Diagrams

### **Flow 1: Vocabulary Association Learning**

```
User: "ngl I think React is better"
          ↓
┌─────────────────────────────────┐
│ Context Detection               │
│ → Detected: casual_chat         │
└─────────────────────────────────┘
          ↓
┌─────────────────────────────────┐
│ Vocabulary Extraction           │
│ → Terms: ["ngl", "React"]       │
└─────────────────────────────────┘
          ↓
┌─────────────────────────────────┐
│ Hebbian Observation             │
│ STRENGTHEN:                     │
│   assoc["ngl"]["casual_chat"]   │
│   += 0.05 * (1.0 - 0.72)        │
│   = 0.014                       │
│                                 │
│ WEAKEN COMPETITORS:             │
│   assoc["ngl"]["formal_tech"]   │
│   *= (1.0 - 0.01)               │
│   = 0.12 * 0.99 = 0.119         │
└─────────────────────────────────┘
          ↓
┌─────────────────────────────────┐
│ Database Update                 │
│ vocab_associations:             │
│   ("ngl", "casual_chat", 0.734) │
│   ("ngl", "formal_tech", 0.119) │
└─────────────────────────────────┘
          ↓
┌─────────────────────────────────┐
│ Future Usage Decision           │
│ In casual context:              │
│   should_use("ngl") → TRUE      │
│ In formal context:              │
│   should_use("ngl") → FALSE     │
└─────────────────────────────────┘
```

---

### **Flow 2: Dimension Co-activation Learning**

```
User appears stressed: "I'm so confused, help!"
          ↓
┌─────────────────────────────────┐
│ Personality Dimension Detection │
│ Active dimensions:              │
│   emotional_support → 0.85      │
│   response_length → 0.25 (brief)│
│   technical_depth → 0.30 (simple)│
└─────────────────────────────────┘
          ↓
┌─────────────────────────────────┐
│ Hebbian Co-activation Update    │
│ STRENGTHEN pairs:               │
│   coact[emotional][length_brief]│
│   += 0.05 * 0.85 * 0.25         │
│   = 0.011                       │
│                                 │
│   coact[emotional][depth_simple]│
│   += 0.05 * 0.85 * 0.30         │
│   = 0.013                       │
└─────────────────────────────────┘
          ↓
┌─────────────────────────────────┐
│ Pattern Recognition             │
│ Multi-dim pattern detected:     │
│   "stressed_user_support"       │
│   = (emotional↑, brief↑, simple↑)│
│   Frequency: 5 times            │
│   Confidence: 0.78              │
└─────────────────────────────────┘
          ↓
┌─────────────────────────────────┐
│ Future Prediction               │
│ Next time emotional_support↑:  │
│   → Also activate brief         │
│   → Also activate simple        │
│   (without explicit detection)  │
└─────────────────────────────────┘
```

---

### **Flow 3: Sequence Pattern Learning**

```
Conversation History:
  1. User: "I'm stuck on X" (problem_statement)
  2. Penny: Complex answer (technical_explanation)
  3. User: "Can you simplify?" (simplification_request)
  4. Penny: Simple answer (simplified_explanation)
  5. User: "Perfect thanks" (positive_feedback)
          ↓
┌─────────────────────────────────┐
│ Transition Observation          │
│ Recorded sequence:              │
│   problem → technical           │
│   technical → simplification    │
│   simplification → simplified   │
│   simplified → positive         │
└─────────────────────────────────┘
          ↓
┌─────────────────────────────────┐
│ Pattern Frequency Check         │
│ This sequence occurred: 5 times │
│ Average satisfaction: 0.92      │
│                                 │
│ Insight: Users who ask problems │
│ often need simplification       │
└─────────────────────────────────┘
          ↓
┌─────────────────────────────────┐
│ Pattern Template Created        │
│ Pattern: "problem_to_simple"    │
│ Skip: technical_explanation     │
│ Jump to: simplified_explanation │
│ Confidence: 0.85                │
└─────────────────────────────────┘
          ↓
┌─────────────────────────────────┐
│ Future Anticipation             │
│ Next problem_statement:         │
│   → Check if user prefers simple│
│   → If pattern matches, skip    │
│      complex answer, give simple│
└─────────────────────────────────┘
```

---

## 🔌 Integration Points with Existing System

### **Integration Point 1: Context Detection (research_first_pipeline.py:~120)**

**Current:**
```python
# No conversation state classification
```

**Enhancement:**
```python
from src.personality.hebbian_sequence_learner import HebbianSequenceLearner

sequence_learner = HebbianSequenceLearner()

# Classify conversation state
conversation_state = sequence_learner.classify_conversation_state(
    user_input=actual_command,
    context={'mood_indicators': mood, 'history': recent_turns}
)

# Predict next likely states
predicted_next_states = sequence_learner.predict_next_states(
    current_state=conversation_state,
    history=conversation_history
)
```

---

### **Integration Point 2: Prompt Building (research_first_pipeline.py:~150)**

**Current:**
```python
personality_enhancement = asyncio.run(
    self.personality_prompt_builder.build_personality_prompt(
        user_id="default",
        context={'topic': 'general', 'query': user_input}
    )
)
```

**Enhancement:**
```python
from src.personality.hebbian_dimension_associator import HebbianDimensionAssociator

dim_associator = HebbianDimensionAssociator()

# Get current personality state
current_dims = await personality_tracker.get_current_personality_state()

# Predict co-activations
predicted_dims = dim_associator.predict_coactivations(
    known_dimensions={
        dim: state.current_value
        for dim, state in current_dims.items()
        if state.confidence > 0.65
    }
)

# Build prompt with predicted co-activations
personality_enhancement = asyncio.run(
    self.personality_prompt_builder.build_personality_prompt(
        user_id="default",
        context={
            'topic': 'general',
            'query': user_input,
            'predicted_coactivations': predicted_dims  # NEW
        }
    )
)
```

---

### **Integration Point 3: Post-Processing (research_first_pipeline.py:~200)**

**Current:**
```python
result = asyncio.run(
    self.personality_post_processor.process_response(
        final_response,
        context={'topic': 'general', 'query': actual_command}
    )
)
```

**Enhancement:**
```python
from src.personality.hebbian_vocabulary_associator import HebbianVocabularyAssociator

vocab_associator = HebbianVocabularyAssociator()

# Check vocabulary appropriateness
context_type = conversation_state  # From earlier classification
filtered_response = vocab_associator.filter_response_vocabulary(
    response=final_response,
    context=context_type,
    threshold=0.65
)

# Then apply existing post-processing
result = asyncio.run(
    self.personality_post_processor.process_response(
        filtered_response,
        context={'topic': 'general', 'query': actual_command}
    )
)
```

---

### **Integration Point 4: Learning Update (research_first_pipeline.py:~240)**

**Current:**
```python
self._update_personality_from_conversation(
    actual_command, final_response, turn.turn_id
)
```

**Enhancement:**
```python
# Existing personality update
self._update_personality_from_conversation(
    actual_command, final_response, turn.turn_id
)

# NEW: Hebbian learning updates
self._update_hebbian_associations(
    user_input=actual_command,
    assistant_response=final_response,
    conversation_state=conversation_state,
    active_dimensions=current_dims
)
```

**New Method:**
```python
def _update_hebbian_associations(
    self,
    user_input: str,
    assistant_response: str,
    conversation_state: str,
    active_dimensions: Dict
):
    """Update Hebbian associations after conversation turn"""

    # 1. Update vocabulary associations
    self.vocab_associator.observe_conversation(
        user_message=user_input,
        context=conversation_state
    )

    # 2. Update dimension co-activations
    active_dims_dict = {
        dim: state.current_value
        for dim, state in active_dimensions.items()
        if state.confidence > 0.5
    }
    self.dim_associator.observe_activations(active_dims_dict)

    # 3. Update conversation transitions
    if hasattr(self, 'previous_conversation_state'):
        self.sequence_learner.observe_transition(
            from_state=self.previous_conversation_state,
            to_state=conversation_state
        )
    self.previous_conversation_state = conversation_state
```

---

## 💾 Database Schema Overview

### **New Tables Required**

```sql
-- Vocabulary Associations
CREATE TABLE vocab_associations (
    term TEXT NOT NULL,
    context_type TEXT NOT NULL,
    strength REAL DEFAULT 0.5,
    observation_count INTEGER DEFAULT 1,
    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (term, context_type)
);

-- Dimension Co-activations
CREATE TABLE dimension_coactivations (
    dim1 TEXT NOT NULL,
    dim2 TEXT NOT NULL,
    strength REAL DEFAULT 0.0,
    observation_count INTEGER DEFAULT 0,
    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (dim1, dim2)
);

-- Multi-dimensional Patterns
CREATE TABLE multi_dim_patterns (
    pattern_id TEXT PRIMARY KEY,
    dimensions TEXT NOT NULL, -- JSON: {"empathy": 0.8, "brief": 0.9}
    frequency INTEGER DEFAULT 1,
    avg_satisfaction REAL DEFAULT 0.5,
    last_seen DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Conversation State Transitions
CREATE TABLE conversation_state_transitions (
    state_from TEXT NOT NULL,
    state_to TEXT NOT NULL,
    transition_count INTEGER DEFAULT 1,
    last_observed DATETIME DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (state_from, state_to)
);

-- State Sequences
CREATE TABLE state_sequences (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sequence TEXT NOT NULL, -- JSON: ["problem", "technical", "simple"]
    frequency INTEGER DEFAULT 1,
    avg_satisfaction REAL,
    last_observed DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Hebbian Configuration
CREATE TABLE hebbian_config (
    component TEXT NOT NULL,
    parameter TEXT NOT NULL,
    value REAL NOT NULL,
    description TEXT,
    PRIMARY KEY (component, parameter)
);
```

**See:** `HEBBIAN_DATABASE_SCHEMA.sql` for full schema with indexes and migration plan

---

## ⚡ Performance Considerations

### **Latency Budget**

| Component | Operation | Target Latency | Strategy |
|-----------|-----------|----------------|----------|
| Vocabulary Associator | should_use_term() | <2ms | In-memory cache of top 100 terms |
| Dimension Associator | predict_coactivations() | <5ms | Precompute common patterns |
| Sequence Learner | classify_state() | <3ms | Fast regex + keyword matching |
| Database Writes | All learning updates | <10ms | Batch updates, async writes |

### **Caching Strategy**

```python
class HebbianLearningManager:
    """Orchestrates all Hebbian components with performance optimization"""

    def __init__(self):
        self.vocab_cache = LRUCache(maxsize=200)  # Most frequent terms
        self.pattern_cache = LRUCache(maxsize=50)  # Common patterns
        self.transition_cache = dict()  # All transitions (small enough)

        # Refresh caches every 100 conversations
        self.cache_refresh_interval = 100
        self.conversation_count = 0

    def get_term_association(self, term: str, context: str) -> float:
        """O(1) cache lookup, O(n) database fallback"""
        cache_key = f"{term}:{context}"

        if cache_key in self.vocab_cache:
            return self.vocab_cache[cache_key]

        # Cache miss - query database
        strength = self.vocab_associator.get_association_strength(term, context)
        self.vocab_cache[cache_key] = strength
        return strength
```

### **Database Indexing**

```sql
-- Critical indexes for performance
CREATE INDEX idx_vocab_term ON vocab_associations(term);
CREATE INDEX idx_vocab_context ON vocab_associations(context_type);
CREATE INDEX idx_vocab_strength ON vocab_associations(strength DESC);

CREATE INDEX idx_coact_dim1 ON dimension_coactivations(dim1);
CREATE INDEX idx_coact_strength ON dimension_coactivations(strength DESC);

CREATE INDEX idx_transitions_from ON conversation_state_transitions(state_from);
CREATE INDEX idx_transitions_count ON conversation_state_transitions(transition_count DESC);
```

---

## 🛡️ Safety Mechanisms

### **1. Association Strength Caps**

```python
MAX_ASSOCIATION_STRENGTH = 1.0
MIN_ASSOCIATION_STRENGTH = 0.0

def cap_strength(strength: float) -> float:
    """Prevent runaway strengthening"""
    return max(MIN_ASSOCIATION_STRENGTH, min(MAX_ASSOCIATION_STRENGTH, strength))
```

### **2. Temporal Decay**

```python
DECAY_RATE_PER_DAY = 0.001

def apply_temporal_decay(strength: float, days_since_last_use: float) -> float:
    """Unused associations gradually weaken"""
    decay_factor = DECAY_RATE_PER_DAY * days_since_last_use
    return strength * (1.0 - decay_factor)
```

### **3. Confidence Gating**

```python
PREDICTION_CONFIDENCE_THRESHOLD = 0.65

def should_apply_prediction(pattern_confidence: float) -> bool:
    """Only apply high-confidence predictions"""
    return pattern_confidence >= PREDICTION_CONFIDENCE_THRESHOLD
```

### **4. Override Mechanism**

```python
# Manual override for problematic associations
override_associations = {
    ("ngl", "formal_technical"): 0.0,  # Force zero
    ("literally", "any_context"): 0.0  # Disable entirely
}

def get_association_with_override(term: str, context: str) -> float:
    """Check overrides before returning association"""
    if (term, context) in override_associations:
        return override_associations[(term, context)]
    return get_association_strength(term, context)
```

---

## 🔍 Debuggability & Interpretability

### **Export Association Matrices**

```python
def export_vocabulary_associations() -> pd.DataFrame:
    """Export vocab associations as pandas DataFrame for analysis"""
    query = """
        SELECT term, context_type, strength, observation_count
        FROM vocab_associations
        WHERE strength > 0.1
        ORDER BY strength DESC
    """
    return pd.read_sql_query(query, conn)

def visualize_coactivation_network():
    """Generate NetworkX graph of dimension co-activations"""
    import networkx as nx
    import matplotlib.pyplot as plt

    G = nx.Graph()

    # Add nodes (dimensions)
    for dim in PERSONALITY_DIMENSIONS:
        G.add_node(dim)

    # Add edges (co-activations > threshold)
    query = "SELECT dim1, dim2, strength FROM dimension_coactivations WHERE strength > 0.5"
    for dim1, dim2, strength in cursor.execute(query):
        G.add_edge(dim1, dim2, weight=strength)

    nx.draw(G, with_labels=True, node_size=1000)
    plt.savefig("coactivation_network.png")
```

### **Debug Dashboard Methods**

```python
def get_top_associations(term: str, n: int = 5) -> List[Tuple[str, float]]:
    """Get top N contexts for a term"""
    query = """
        SELECT context_type, strength
        FROM vocab_associations
        WHERE term = ?
        ORDER BY strength DESC
        LIMIT ?
    """
    return cursor.execute(query, (term, n)).fetchall()

def get_strongest_coactivations(n: int = 10) -> List[Tuple[str, str, float]]:
    """Get top N dimension co-activations"""
    query = """
        SELECT dim1, dim2, strength
        FROM dimension_coactivations
        ORDER BY strength DESC
        LIMIT ?
    """
    return cursor.execute(query, (n,)).fetchall()

def get_common_sequences(n: int = 5) -> List[Tuple[str, int]]:
    """Get most frequent conversation sequences"""
    query = """
        SELECT sequence, frequency
        FROM state_sequences
        ORDER BY frequency DESC
        LIMIT ?
    """
    return cursor.execute(query, (n,)).fetchall()
```

---

## 🧪 Testing Strategy

### **Unit Tests**

```python
def test_hebbian_strengthening():
    """Test basic Hebbian strengthening rule"""
    associator = HebbianVocabularyAssociator()

    # Initial state
    initial = associator.get_association_strength("ngl", "casual_chat")

    # Observe term in context 5 times
    for _ in range(5):
        associator.observe_term_in_context("ngl", "casual_chat")

    # Strength should increase
    final = associator.get_association_strength("ngl", "casual_chat")
    assert final > initial

def test_competitive_weakening():
    """Test competitive learning (other contexts weaken)"""
    associator = HebbianVocabularyAssociator()

    # Strengthen casual, should weaken formal
    initial_formal = associator.get_association_strength("ngl", "formal_technical")

    for _ in range(10):
        associator.observe_term_in_context("ngl", "casual_chat")

    final_formal = associator.get_association_strength("ngl", "formal_technical")
    assert final_formal < initial_formal
```

### **Integration Tests**

```python
def test_end_to_end_vocab_learning():
    """Test full pipeline: observation → learning → prediction"""
    manager = HebbianLearningManager()

    # Simulate 10 conversations with "ngl" in casual context
    for i in range(10):
        manager.observe_conversation(
            user_message=f"ngl I think option {i} is better",
            context="casual_chat"
        )

    # Should recommend using "ngl" in casual context
    assert manager.should_use_term("ngl", "casual_chat") == True

    # Should NOT recommend in formal context
    assert manager.should_use_term("ngl", "formal_technical") == False
```

### **System Tests**

```python
def test_personality_system_integration():
    """Test Hebbian layer doesn't break existing personality system"""
    pipeline = ResearchFirstPipeline()

    # Process conversation with Hebbian enabled
    response1 = pipeline.process_turn("yo what's up")

    # Disable Hebbian
    pipeline.hebbian_enabled = False
    response2 = pipeline.process_turn("yo what's up")

    # Should still get valid responses in both cases
    assert response1 is not None
    assert response2 is not None
```

---

## 📊 Success Metrics

### **Quantitative Metrics**

| Metric | Target | Measurement Method |
|--------|--------|-------------------|
| Vocabulary Prediction Accuracy | >80% | Test set of term-context pairs |
| Co-activation Prediction Accuracy | >75% | Validation against actual activations |
| Sequence Anticipation Success | >70% | User satisfaction after anticipated responses |
| Latency Impact | <10ms per component | Profiling with cProfile |
| Database Size Growth | <1MB per 100 convos | Monitor db file size |

### **Qualitative Metrics**

| Metric | Evaluation Method |
|--------|-------------------|
| Naturalness | User feedback: "Does Penny feel more intuitive?" |
| Appropriate Vocabulary Usage | Manual review of responses |
| Anticipation Helpfulness | Track preemptive responses that were correct |
| False Positive Rate | Track predictions that were wrong/unhelpful |

---

## 🚀 Rollout Plan

### **Phase 1: Vocabulary Associator (Week 9, Days 1-3)**
- Implement basic association matrix
- Add database tables
- Integrate with post-processor
- Test with 50 conversations

### **Phase 2: Dimension Associator (Week 9, Days 4-5)**
- Implement co-activation matrix
- Add prediction logic
- Integrate with prompt builder
- Test with stress/empathy patterns

### **Phase 3: Sequence Learner (Week 10, Days 1-3)**
- Implement state classification
- Add transition tracking
- Test pattern detection
- Integrate anticipation logic

### **Phase 4: Integration & Testing (Week 10, Days 4-5)**
- Full system integration
- Performance profiling
- User acceptance testing
- Documentation

---

## 🔄 Migration & Backward Compatibility

### **Feature Flag**

```python
# .env
HEBBIAN_LEARNING_ENABLED=false  # Default off for safety

# research_first_pipeline.py
HEBBIAN_ENABLED = os.getenv("HEBBIAN_LEARNING_ENABLED", "false").lower() == "true"

if HEBBIAN_ENABLED:
    # Use Hebbian predictions
    predicted_dims = self.dim_associator.predict_coactivations(...)
else:
    # Use existing logic
    predicted_dims = {}
```

### **Gradual Rollout**

1. **Week 9:** Deploy with feature flag OFF, database tables created
2. **Week 10 Day 1:** Enable vocabulary associator only
3. **Week 10 Day 3:** Enable dimension associator
4. **Week 10 Day 5:** Enable full sequence learning

### **Rollback Strategy**

```python
def disable_hebbian_learning():
    """Emergency rollback if issues arise"""
    # Set feature flag
    os.environ["HEBBIAN_LEARNING_ENABLED"] = "false"

    # Clear caches
    hebbian_manager.clear_all_caches()

    # Log rollback
    logger.warning("Hebbian learning disabled via emergency rollback")
```

---

## 📚 References

### **Hebbian Learning Theory**
- Hebb, D.O. (1949). The Organization of Behavior
- Gerstner & Kistler (2002). Spiking Neuron Models
- Competitive Learning: Rumelhart & Zipser (1985)

### **Implementation Guides**
- See: `HEBBIAN_LEARNING_SPECS.md` - Detailed algorithms
- See: `HEBBIAN_DATABASE_SCHEMA.sql` - Complete schema
- See: `HEBBIAN_IMPLEMENTATION_SKELETONS.md` - Code templates
- See: `HEBBIAN_INTEGRATION_PLAN.md` - Step-by-step integration

---

## ✅ Architecture Review Checklist

- [x] **Modular Design** - Can be disabled without breaking existing system
- [x] **Performance** - <10ms latency budget per component
- [x] **Persistence** - All associations stored in database
- [x] **Debuggability** - Export/visualization methods provided
- [x] **Safety** - Decay, caps, confidence gating implemented
- [x] **Testing** - Unit, integration, system test strategy defined
- [x] **Migration** - Feature flags and rollback strategy included
- [x] **Documentation** - Clear integration points and examples

---

**Status:** ✅ Architecture Design Complete
**Next Step:** Implement detailed specifications in `HEBBIAN_LEARNING_SPECS.md`

---

*Designed for Penny's Phase 3E Enhancement - October 27, 2025*
