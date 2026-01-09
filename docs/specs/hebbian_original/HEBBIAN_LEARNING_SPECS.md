# 🧠 Hebbian Learning Layer - Detailed Specifications

**Date:** October 27, 2025
**Status:** Design Specification
**Related:** HEBBIAN_LEARNING_ARCHITECTURE.md

---

## 📋 Table of Contents

1. [Component 1: Vocabulary Association Matrix](#component-1-vocabulary-association-matrix)
2. [Component 2: Dimension Co-activation Matrix](#component-2-dimension-co-activation-matrix)
3. [Component 3: Conversation Sequence Learner](#component-3-conversation-sequence-learner)
4. [Component 4: Hebbian Learning Manager](#component-4-hebbian-learning-manager)
5. [Configuration Parameters](#configuration-parameters)
6. [Edge Cases & Error Handling](#edge-cases--error-handling)

---

## Component 1: Vocabulary Association Matrix

### **Purpose**

Learn which vocabulary terms (words, slang, phrases) belong in which conversational contexts through associative learning.

### **Core Algorithm: Hebbian Learning with Competitive Inhibition**

```python
# Hebbian Rule: Δw_ij = η * x_i * x_j
# Where:
#   w_ij = connection strength from neuron i (term) to neuron j (context)
#   η = learning rate
#   x_i = activation of term (1.0 if present, 0.0 if absent)
#   x_j = activation of context (1.0 if active, 0.0 if inactive)

def observe_term_in_context(term: str, context: str):
    """
    Hebbian strengthening with competitive weakening

    Algorithm:
    1. Strengthen association between term and context (Hebbian rule)
    2. Weaken competing associations (competitive learning)
    3. Apply caps to prevent runaway strengthening
    4. Update database with new strengths
    """

    # Get current strength
    current_strength = get_association_strength(term, context)

    # Hebbian strengthening: strengthen the active association
    # Use diminishing returns: strength approaches 1.0 asymptotically
    delta_strengthen = LEARNING_RATE * (1.0 - current_strength)
    new_strength = current_strength + delta_strengthen

    # Competitive weakening: weaken other contexts for this term
    for other_context in ALL_CONTEXTS:
        if other_context != context:
            other_strength = get_association_strength(term, other_context)
            delta_weaken = COMPETITIVE_RATE * other_strength
            new_other_strength = other_strength - delta_weaken

            # Apply floor (don't go below 0)
            new_other_strength = max(0.0, new_other_strength)

            # Update database
            update_association(term, other_context, new_other_strength)

    # Apply cap (don't exceed 1.0)
    new_strength = min(1.0, new_strength)

    # Update database
    update_association(term, context, new_strength)

    # Log observation
    log_observation(term, context, timestamp=now())
```

### **Data Structures**

```python
@dataclass
class VocabularyAssociation:
    """Represents a term-context association"""
    term: str
    context_type: str
    strength: float  # 0.0 to 1.0
    observation_count: int
    last_updated: datetime
    first_observed: datetime

@dataclass
class ContextType:
    """Represents a conversation context category"""
    name: str
    description: str
    keywords: List[str]
    mood_indicators: List[str]
```

### **Context Types**

```python
CONTEXT_TYPES = {
    'casual_chat': {
        'description': 'Informal conversation, opinions, hot takes',
        'keywords': ['yo', 'ngl', 'tbh', 'lol', 'dude', 'honestly'],
        'formality_range': (0.0, 0.4),
        'technical_range': (0.0, 0.5)
    },
    'formal_technical': {
        'description': 'Professional explanations, documentation',
        'keywords': ['please', 'could you', 'specifically', 'implementation'],
        'formality_range': (0.7, 1.0),
        'technical_range': (0.6, 1.0)
    },
    'problem_solving': {
        'description': 'Debugging, troubleshooting, analysis',
        'keywords': ['stuck', 'error', 'broken', 'debug', 'fix', 'help'],
        'formality_range': (0.3, 0.7),
        'technical_range': (0.5, 1.0)
    },
    'creative_discussion': {
        'description': 'Brainstorming, design, exploration',
        'keywords': ['idea', 'what if', 'thinking', 'brainstorm', 'design'],
        'formality_range': (0.2, 0.6),
        'technical_range': (0.3, 0.8)
    },
    'emotional_support': {
        'description': 'Empathy, encouragement, validation',
        'keywords': ['stressed', 'confused', 'frustrated', 'help', 'struggling'],
        'formality_range': (0.2, 0.6),
        'technical_range': (0.0, 0.4)
    },
    'quick_query': {
        'description': 'Brief questions, rapid-fire Q&A',
        'keywords': ['quick', 'briefly', 'tldr', 'short answer', 'summary'],
        'formality_range': (0.2, 0.8),
        'technical_range': (0.2, 0.8)
    }
}
```

### **API Surface**

```python
class HebbianVocabularyAssociator:
    """
    Learns vocabulary-context associations through Hebbian learning
    """

    def __init__(self, db_path: str = "data/personality_tracking.db",
                 learning_rate: float = 0.05,
                 competitive_rate: float = 0.01):
        """
        Initialize vocabulary associator

        Args:
            db_path: Path to database
            learning_rate: Rate of strengthening (default 0.05)
            competitive_rate: Rate of competitive weakening (default 0.01)
        """
        pass

    def observe_term_in_context(self, term: str, context: str) -> None:
        """
        Record observation of term in context, update associations

        Args:
            term: The vocabulary term observed
            context: The conversation context type
        """
        pass

    def observe_conversation(self, user_message: str, context: str) -> None:
        """
        Extract terms from message and observe all associations

        Args:
            user_message: The user's message text
            context: The conversation context type
        """
        pass

    def get_association_strength(self, term: str, context: str) -> float:
        """
        Get current association strength between term and context

        Args:
            term: The vocabulary term
            context: The conversation context type

        Returns:
            float: Association strength (0.0 to 1.0)
        """
        pass

    def should_use_term(self, term: str, context: str,
                        threshold: float = 0.65) -> bool:
        """
        Determine if term is appropriate for context

        Args:
            term: The vocabulary term
            context: The conversation context type
            threshold: Minimum strength to recommend usage

        Returns:
            bool: True if term should be used in this context
        """
        pass

    def filter_response_vocabulary(self, response: str, context: str,
                                   threshold: float = 0.65) -> str:
        """
        Filter out inappropriate vocabulary from response

        Args:
            response: The assistant's generated response
            context: The conversation context type
            threshold: Minimum strength to allow usage

        Returns:
            str: Filtered response with inappropriate terms removed
        """
        pass

    def get_top_contexts_for_term(self, term: str, n: int = 3) -> List[Tuple[str, float]]:
        """
        Get top N contexts where term is most appropriate

        Args:
            term: The vocabulary term
            n: Number of top contexts to return

        Returns:
            List of (context, strength) tuples, sorted by strength desc
        """
        pass

    def apply_temporal_decay(self, days_inactive: float = 1.0) -> int:
        """
        Apply time-based decay to unused associations

        Args:
            days_inactive: Number of days since last update for decay

        Returns:
            int: Number of associations decayed
        """
        pass

    def export_association_matrix(self) -> pd.DataFrame:
        """
        Export all associations as pandas DataFrame

        Returns:
            DataFrame with columns: term, context, strength, observations
        """
        pass
```

### **Example Usage**

```python
# Initialize
vocab_associator = HebbianVocabularyAssociator(
    learning_rate=0.05,
    competitive_rate=0.01
)

# Observe user using "ngl" in casual context (10 times)
for i in range(10):
    vocab_associator.observe_term_in_context("ngl", "casual_chat")

# Check association strength
strength_casual = vocab_associator.get_association_strength("ngl", "casual_chat")
strength_formal = vocab_associator.get_association_strength("ngl", "formal_technical")

print(f"'ngl' in casual: {strength_casual:.2f}")  # ~0.40 (strengthened)
print(f"'ngl' in formal: {strength_formal:.2f}")  # ~0.45 (weakened from 0.50 default)

# Should we use "ngl" in formal context?
use_in_formal = vocab_associator.should_use_term("ngl", "formal_technical", threshold=0.65)
print(f"Use 'ngl' in formal? {use_in_formal}")  # False

# Filter a response
response = "NGL, the implementation is solid. You could optimize the database queries."
filtered = vocab_associator.filter_response_vocabulary(response, "formal_technical")
print(filtered)  # "The implementation is solid. You could optimize the database queries."
```

---

## Component 2: Dimension Co-activation Matrix

### **Purpose**

Learn which personality dimensions naturally activate together so future activations can be predicted.

### **Core Algorithm: Hebbian Co-activation Learning**

```python
def observe_activations(dimensions: Dict[str, float]):
    """
    Observe which dimensions are active simultaneously

    Algorithm:
    1. Identify which dimensions are "active" (above activation threshold)
    2. For each pair of active dimensions, strengthen co-activation
    3. Detect multi-dimensional patterns (3+ dimensions)
    4. Update co-activation matrix in database
    """

    # Filter to active dimensions only
    active_dims = {
        dim: value for dim, value in dimensions.items()
        if value > ACTIVATION_THRESHOLD  # e.g., 0.6
    }

    # Pairwise co-activation strengthening
    for dim1, val1 in active_dims.items():
        for dim2, val2 in active_dims.items():
            if dim1 < dim2:  # Avoid duplicate pairs (A,B) and (B,A)

                # Get current co-activation strength
                current = get_coactivation_strength(dim1, dim2)

                # Hebbian update: Δw = η * x1 * x2
                delta = LEARNING_RATE * val1 * val2
                new_strength = current + delta

                # Apply cap
                new_strength = min(1.0, new_strength)

                # Update database
                update_coactivation(dim1, dim2, new_strength)

    # Detect negative correlations (one high, other consistently low)
    for dim1, val1 in dimensions.items():
        for dim2, val2 in dimensions.items():
            if dim1 != dim2:
                if val1 > 0.7 and val2 < 0.3:
                    # Possible negative correlation
                    update_negative_correlation(dim1, dim2)

    # Multi-dimensional pattern detection
    if len(active_dims) >= 3:
        pattern_id = generate_pattern_id(active_dims)
        update_pattern_frequency(pattern_id, active_dims)
```

### **Data Structures**

```python
@dataclass
class DimensionCoactivation:
    """Represents co-activation between two dimensions"""
    dim1: str
    dim2: str
    strength: float  # 0.0 to 1.0
    observation_count: int
    last_updated: datetime

@dataclass
class MultiDimensionalPattern:
    """Represents a pattern of 3+ dimensions activating together"""
    pattern_id: str
    dimensions: Dict[str, float]  # {dim_name: typical_value}
    frequency: int
    avg_satisfaction: float
    last_observed: datetime

@dataclass
class NegativeCorrelation:
    """Represents dimensions that anti-correlate"""
    dim_high: str
    dim_low: str
    correlation_strength: float  # Negative correlation coefficient
    observation_count: int
```

### **Prediction Algorithm**

```python
def predict_coactivations(known_dimensions: Dict[str, float],
                          threshold: float = 0.65) -> Dict[str, float]:
    """
    Predict other dimension values based on known active dimensions

    Algorithm:
    1. For each known dimension that's active (above threshold)
    2. Find strongly co-activated dimensions
    3. Predict their values based on co-activation strength
    4. Average predictions if multiple sources suggest same dimension
    5. Only return high-confidence predictions
    """

    predicted_dims = {}
    prediction_sources = defaultdict(list)  # Track multiple predictions

    # For each known active dimension
    for known_dim, known_val in known_dimensions.items():
        if known_val < threshold:
            continue  # Not strongly active

        # Get co-activations with this dimension
        coactivations = get_strong_coactivations(known_dim, min_strength=0.5)

        for other_dim, coact_strength in coactivations:
            if other_dim in known_dimensions:
                continue  # Already know this dimension

            # Predict value for other_dim
            # Assumption: If dim1 is high and often co-activates with dim2,
            # then dim2 is likely also high
            predicted_value = known_val * coact_strength
            prediction_sources[other_dim].append({
                'value': predicted_value,
                'confidence': coact_strength,
                'source': known_dim
            })

    # Average predictions with confidence weighting
    for dim, predictions in prediction_sources.items():
        if len(predictions) == 0:
            continue

        # Weighted average
        total_conf = sum(p['confidence'] for p in predictions)
        weighted_val = sum(p['value'] * p['confidence'] for p in predictions) / total_conf
        avg_conf = total_conf / len(predictions)

        # Only include if high confidence
        if avg_conf >= threshold:
            predicted_dims[dim] = {
                'value': weighted_val,
                'confidence': avg_conf,
                'sources': [p['source'] for p in predictions]
            }

    return predicted_dims
```

### **API Surface**

```python
class HebbianDimensionAssociator:
    """
    Learns personality dimension co-activations through Hebbian learning
    """

    def __init__(self, db_path: str = "data/personality_tracking.db",
                 learning_rate: float = 0.05,
                 activation_threshold: float = 0.6):
        """
        Initialize dimension associator

        Args:
            db_path: Path to database
            learning_rate: Rate of co-activation strengthening
            activation_threshold: Threshold for considering dimension "active"
        """
        pass

    def observe_activations(self, dimensions: Dict[str, float]) -> None:
        """
        Observe which dimensions are currently active, update co-activations

        Args:
            dimensions: Dict of dimension_name -> current_value
        """
        pass

    def get_coactivation_strength(self, dim1: str, dim2: str) -> float:
        """
        Get co-activation strength between two dimensions

        Args:
            dim1: First dimension name
            dim2: Second dimension name

        Returns:
            float: Co-activation strength (0.0 to 1.0)
        """
        pass

    def predict_coactivations(self, known_dimensions: Dict[str, float],
                             threshold: float = 0.65) -> Dict[str, Dict]:
        """
        Predict other dimension values based on known active dimensions

        Args:
            known_dimensions: Dict of known dimension_name -> value
            threshold: Minimum confidence for predictions

        Returns:
            Dict of predicted dimension_name -> {value, confidence, sources}
        """
        pass

    def get_strongest_coactivations(self, dimension: str, n: int = 5) -> List[Tuple[str, float]]:
        """
        Get dimensions that most strongly co-activate with given dimension

        Args:
            dimension: Dimension name
            n: Number of top co-activations to return

        Returns:
            List of (other_dimension, strength) tuples
        """
        pass

    def detect_negative_correlations(self, threshold: float = 0.6) -> List[Tuple[str, str, float]]:
        """
        Detect dimension pairs that anti-correlate

        Args:
            threshold: Minimum correlation strength to report

        Returns:
            List of (dim_high, dim_low, correlation) tuples
        """
        pass

    def get_multi_dim_patterns(self, min_frequency: int = 3) -> List[MultiDimensionalPattern]:
        """
        Get recurring patterns of 3+ dimensions activating together

        Args:
            min_frequency: Minimum observation count to include

        Returns:
            List of MultiDimensionalPattern objects
        """
        pass

    def export_coactivation_matrix(self) -> pd.DataFrame:
        """
        Export co-activation matrix as pandas DataFrame

        Returns:
            DataFrame with columns: dim1, dim2, strength, observations
        """
        pass

    def visualize_coactivation_network(self, output_path: str = "coactivation_network.png"):
        """
        Generate NetworkX visualization of co-activation network

        Args:
            output_path: Path to save visualization image
        """
        pass
```

### **Example Usage**

```python
# Initialize
dim_associator = HebbianDimensionAssociator(
    learning_rate=0.05,
    activation_threshold=0.6
)

# User is stressed - observe dimensions
observed_dims = {
    'emotional_support_style': 0.85,  # High empathy
    'response_length_preference': 0.25,  # Brief
    'technical_depth_preference': 0.30,  # Simple
    'communication_formality': 0.40  # Somewhat casual
}

# Observe this pattern 5 times
for _ in range(5):
    dim_associator.observe_activations(observed_dims)

# Check co-activation strength
coact_empathy_brief = dim_associator.get_coactivation_strength(
    'emotional_support_style', 'response_length_preference'
)
print(f"Empathy ↔ Brief: {coact_empathy_brief:.2f}")  # ~0.21 (0.85 * 0.25 * 5 * 0.05)

# Next time, predict based on high empathy alone
known = {'emotional_support_style': 0.80}
predicted = dim_associator.predict_coactivations(known, threshold=0.65)

print("Predicted co-activations:")
for dim, info in predicted.items():
    print(f"  {dim}: {info['value']:.2f} (confidence: {info['confidence']:.2f})")
# Output:
#   response_length_preference: 0.20 (confidence: 0.71)
#   technical_depth_preference: 0.24 (confidence: 0.68)
```

---

## Component 3: Conversation Sequence Learner

### **Purpose**

Learn sequential patterns in conversation states to anticipate user needs and skip predictable intermediate steps.

### **Core Algorithm: Markov Chain Transition Learning**

```python
def observe_transition(state_from: str, state_to: str):
    """
    Observe a state transition and update transition matrix

    Algorithm:
    1. Increment transition count
    2. Recalculate transition probabilities
    3. Check for recurring sequences
    4. Update pattern templates if sequence is frequent
    """

    # Increment count
    transition_count[state_from][state_to] += 1

    # Recalculate probabilities for this state
    total_transitions_from = sum(transition_count[state_from].values())
    for next_state, count in transition_count[state_from].items():
        transition_prob[state_from][next_state] = count / total_transitions_from

    # Update database
    update_transition(state_from, state_to,
                     count=transition_count[state_from][state_to],
                     probability=transition_prob[state_from][next_state])

    # Check for sequence patterns
    if len(conversation_history) >= 3:
        recent_sequence = conversation_history[-3:]
        sequence_key = "→".join(recent_sequence)

        sequence_frequency[sequence_key] += 1

        # If sequence is frequent, create pattern template
        if sequence_frequency[sequence_key] >= PATTERN_THRESHOLD:  # e.g., 5
            create_or_update_pattern_template(sequence_key, recent_sequence)
```

### **State Classification Algorithm**

```python
def classify_conversation_state(message: str, context: Dict) -> str:
    """
    Classify message into one of the predefined conversation states

    Algorithm:
    1. Check for explicit state indicators (keywords, phrases)
    2. Check for contextual clues (follow-up, error mention, sentiment)
    3. Use heuristics and regex patterns
    4. Return most confident classification
    """

    # Normalize message
    msg_lower = message.lower()

    # Priority 1: Explicit problem statement
    if any(indicator in msg_lower for indicator in ['stuck', 'error', 'issue', 'problem', 'broken']):
        return 'problem_statement'

    # Priority 2: Clarification request
    if any(indicator in msg_lower for indicator in ['what do you mean', 'can you explain', 'clarify']):
        return 'clarification_question'

    # Priority 3: Simplification request
    if any(indicator in msg_lower for indicator in ['simpler', 'eli5', 'plain english', 'simplify']):
        return 'simplification_request'

    # Priority 4: Positive feedback
    if any(indicator in msg_lower for indicator in ['perfect', 'thanks', 'great', 'exactly', 'that works']):
        return 'positive_feedback'

    # Priority 5: Frustration
    if any(indicator in msg_lower for indicator in ['confused', 'frustrating', 'doesn\'t make sense']):
        return 'frustration_expression'

    # Priority 6: Correction
    if any(indicator in msg_lower for indicator in ['no', 'actually', 'i meant', 'not what i']):
        return 'correction_request'

    # Priority 7: Opinion request
    if any(indicator in msg_lower for indicator in ['what do you think', 'your opinion', 'your take']):
        return 'opinion_request'

    # Priority 8: Code review
    if context.get('has_code_block', False):
        return 'code_review'

    # Priority 9: Follow-up
    if context.get('is_follow_up', False):
        return 'follow_up_question'

    # Default: Classify based on formality/technical depth
    if context.get('formality', 0.5) < 0.4:
        return 'casual_chat'
    else:
        return 'technical_explanation'
```

### **Pattern Template Detection**

```python
def detect_recurring_patterns(min_frequency: int = 5) -> List[PatternTemplate]:
    """
    Detect sequences that occur frequently with high user satisfaction

    Algorithm:
    1. Get all sequences with frequency >= min_frequency
    2. Calculate average user satisfaction for each
    3. Identify "skip opportunities" (predictable intermediate states)
    4. Return pattern templates sorted by usefulness
    """

    patterns = []

    query = """
        SELECT sequence, frequency, avg_satisfaction
        FROM state_sequences
        WHERE frequency >= ?
        ORDER BY frequency DESC
    """

    for sequence_json, freq, satisfaction in cursor.execute(query, (min_frequency,)):
        sequence = json.loads(sequence_json)

        # Analyze sequence for skip opportunities
        # Example: [problem, technical, simplification, simple, positive]
        # Opportunity: Skip "technical" if "simplification" commonly follows
        skip_candidates = []

        for i in range(len(sequence) - 2):
            state_a = sequence[i]
            state_b = sequence[i + 1]
            state_c = sequence[i + 2]

            # Check if state_b is commonly skipped (direct A→C transition exists)
            direct_prob = transition_prob[state_a].get(state_c, 0.0)
            via_b_prob = (transition_prob[state_a].get(state_b, 0.0) *
                         transition_prob[state_b].get(state_c, 0.0))

            if direct_prob > 0.3 and via_b_prob > direct_prob:
                # State B is sometimes skipped, could be an opportunity
                skip_candidates.append({
                    'from_state': state_a,
                    'skip_state': state_b,
                    'to_state': state_c,
                    'confidence': direct_prob
                })

        pattern = PatternTemplate(
            sequence=sequence,
            frequency=freq,
            avg_satisfaction=satisfaction,
            skip_opportunities=skip_candidates
        )
        patterns.append(pattern)

    return patterns
```

### **Data Structures**

```python
@dataclass
class StateTransition:
    """Represents a transition between conversation states"""
    state_from: str
    state_to: str
    transition_count: int
    transition_probability: float
    last_observed: datetime

@dataclass
class StateSequence:
    """Represents a sequence of conversation states"""
    sequence: List[str]
    frequency: int
    avg_satisfaction: float
    last_observed: datetime

@dataclass
class PatternTemplate:
    """Represents a recurring pattern with skip opportunities"""
    sequence: List[str]
    frequency: int
    avg_satisfaction: float
    skip_opportunities: List[Dict[str, Any]]

@dataclass
class AnticipatedResponse:
    """Represents an anticipated user need"""
    current_state: str
    likely_next_states: List[Tuple[str, float]]  # (state, probability)
    suggested_action: Optional[str]
    confidence: float
```

### **API Surface**

```python
class HebbianSequenceLearner:
    """
    Learns conversation flow patterns through sequence observation
    """

    def __init__(self, db_path: str = "data/personality_tracking.db",
                 pattern_threshold: int = 5):
        """
        Initialize sequence learner

        Args:
            db_path: Path to database
            pattern_threshold: Minimum frequency to create pattern template
        """
        pass

    def classify_conversation_state(self, message: str,
                                    context: Dict[str, Any]) -> str:
        """
        Classify message into conversation state

        Args:
            message: User's message text
            context: Contextual information (formality, mood, is_follow_up, etc.)

        Returns:
            str: Conversation state classification
        """
        pass

    def observe_transition(self, state_from: str, state_to: str,
                          satisfaction: Optional[float] = None) -> None:
        """
        Observe a state transition, update transition matrix

        Args:
            state_from: Previous conversation state
            state_to: Current conversation state
            satisfaction: Optional user satisfaction score (0.0-1.0)
        """
        pass

    def predict_next_states(self, current_state: str,
                           history: List[str],
                           n: int = 3) -> List[Tuple[str, float]]:
        """
        Predict most likely next conversation states

        Args:
            current_state: Current conversation state
            history: Recent state history
            n: Number of top predictions to return

        Returns:
            List of (next_state, probability) tuples
        """
        pass

    def detect_recurring_patterns(self, min_frequency: int = 5) -> List[PatternTemplate]:
        """
        Detect recurring conversation patterns

        Args:
            min_frequency: Minimum observation count

        Returns:
            List of PatternTemplate objects
        """
        pass

    def anticipate_user_need(self, current_state: str,
                            history: List[str]) -> Optional[AnticipatedResponse]:
        """
        Anticipate user's next need based on patterns

        Args:
            current_state: Current conversation state
            history: Recent state history

        Returns:
            AnticipatedResponse object if confident prediction, else None
        """
        pass

    def get_transition_probability(self, state_from: str,
                                   state_to: str) -> float:
        """
        Get probability of transitioning from one state to another

        Args:
            state_from: Source state
            state_to: Target state

        Returns:
            float: Transition probability (0.0-1.0)
        """
        pass

    def export_transition_matrix(self) -> pd.DataFrame:
        """
        Export transition matrix as pandas DataFrame

        Returns:
            DataFrame with columns: state_from, state_to, probability, count
        """
        pass

    def visualize_state_graph(self, output_path: str = "state_transitions.png",
                             min_probability: float = 0.1):
        """
        Generate graph visualization of state transitions

        Args:
            output_path: Path to save visualization
            min_probability: Minimum probability to show edge
        """
        pass
```

### **Example Usage**

```python
# Initialize
sequence_learner = HebbianSequenceLearner(pattern_threshold=5)

# Simulate conversation flow (observed 5 times)
for i in range(5):
    # User states problem
    state1 = sequence_learner.classify_conversation_state(
        "I'm stuck on this async code",
        context={'formality': 0.4}
    )
    # → 'problem_statement'

    # Penny gives complex answer
    sequence_learner.observe_transition('problem_statement', 'technical_explanation')

    # User requests simplification
    state2 = sequence_learner.classify_conversation_state(
        "Can you simplify that?",
        context={'is_follow_up': True}
    )
    # → 'simplification_request'

    sequence_learner.observe_transition('technical_explanation', 'simplification_request')

    # Penny gives simple answer
    sequence_learner.observe_transition('simplification_request', 'simplified_explanation')

    # User satisfied
    state3 = sequence_learner.classify_conversation_state(
        "Perfect, thanks!",
        context={}
    )
    # → 'positive_feedback'

    sequence_learner.observe_transition('simplified_explanation', 'positive_feedback', satisfaction=0.95)

# After 5 observations, predict next states
predictions = sequence_learner.predict_next_states('problem_statement', history=[])
print("After 'problem_statement', likely next states:")
for state, prob in predictions:
    print(f"  {state}: {prob:.2f}")
# Output:
#   technical_explanation: 0.80 (observed 4/5 times)
#   simplified_explanation: 0.20 (observed 1/5 times if we learned to skip)

# Detect patterns
patterns = sequence_learner.detect_recurring_patterns(min_frequency=3)
print(f"Found {len(patterns)} recurring patterns")

# Anticipate user need
anticipated = sequence_learner.anticipate_user_need(
    current_state='problem_statement',
    history=['casual_chat', 'opinion_request']
)

if anticipated and anticipated.confidence > 0.7:
    print(f"High probability user will request: {anticipated.suggested_action}")
    # "User likely to request simplification - provide concise answer first"
```

---

## Component 4: Hebbian Learning Manager

### **Purpose**

Orchestrate all three Hebbian components with performance optimization, caching, and centralized configuration.

### **API Surface**

```python
class HebbianLearningManager:
    """
    Central manager for all Hebbian learning components
    Provides unified interface and performance optimization
    """

    def __init__(self, db_path: str = "data/personality_tracking.db",
                 enable_caching: bool = True,
                 cache_size: int = 200):
        """
        Initialize Hebbian learning manager

        Args:
            db_path: Path to database
            enable_caching: Whether to use LRU caches for performance
            cache_size: Size of LRU caches
        """
        self.vocab_associator = HebbianVocabularyAssociator(db_path)
        self.dim_associator = HebbianDimensionAssociator(db_path)
        self.sequence_learner = HebbianSequenceLearner(db_path)

        self.enable_caching = enable_caching
        if enable_caching:
            self.vocab_cache = LRUCache(maxsize=cache_size)
            self.pattern_cache = LRUCache(maxsize=cache_size // 4)

        self.conversation_count = 0
        self.cache_refresh_interval = 100

    def process_conversation_turn(self,
                                  user_message: str,
                                  assistant_response: str,
                                  context: Dict[str, Any],
                                  active_dimensions: Dict[str, float]) -> Dict[str, Any]:
        """
        Process a complete conversation turn through all Hebbian components

        Args:
            user_message: User's message
            assistant_response: Assistant's response
            context: Conversation context
            active_dimensions: Current personality dimension values

        Returns:
            Dict with learning updates and predictions
        """
        pass

    def should_use_term_cached(self, term: str, context: str,
                               threshold: float = 0.65) -> bool:
        """
        Cached version of should_use_term for performance

        Args:
            term: Vocabulary term
            context: Conversation context
            threshold: Confidence threshold

        Returns:
            bool: Whether term should be used
        """
        if not self.enable_caching:
            return self.vocab_associator.should_use_term(term, context, threshold)

        cache_key = f"{term}:{context}:{threshold}"
        if cache_key in self.vocab_cache:
            return self.vocab_cache[cache_key]

        result = self.vocab_associator.should_use_term(term, context, threshold)
        self.vocab_cache[cache_key] = result
        return result

    def refresh_caches(self) -> None:
        """Refresh all caches (call periodically)"""
        if self.enable_caching:
            self.vocab_cache.clear()
            self.pattern_cache.clear()

    def apply_temporal_decay_all(self, days_inactive: float = 1.0) -> Dict[str, int]:
        """
        Apply temporal decay to all components

        Args:
            days_inactive: Days since last use for decay

        Returns:
            Dict with count of decayed items per component
        """
        return {
            'vocab_associations': self.vocab_associator.apply_temporal_decay(days_inactive),
            'coactivations': 0,  # Implement if needed
            'transitions': 0     # Implement if needed
        }

    def export_all_data(self) -> Dict[str, pd.DataFrame]:
        """
        Export all Hebbian learning data

        Returns:
            Dict with DataFrames for each component
        """
        return {
            'vocab_associations': self.vocab_associator.export_association_matrix(),
            'coactivations': self.dim_associator.export_coactivation_matrix(),
            'transitions': self.sequence_learner.export_transition_matrix()
        }

    def get_system_stats(self) -> Dict[str, Any]:
        """
        Get statistics about Hebbian learning system

        Returns:
            Dict with counts, averages, top associations, etc.
        """
        pass
```

---

## Configuration Parameters

### **Global Configuration**

```python
# hebbian_config.py

HEBBIAN_CONFIG = {
    # Vocabulary Associator
    'vocab': {
        'learning_rate': 0.05,        # Strengthening rate
        'competitive_rate': 0.01,     # Weakening rate
        'decay_rate_per_day': 0.001,  # Temporal decay
        'confidence_threshold': 0.65,  # Prediction threshold
        'max_association_strength': 1.0,
        'min_association_strength': 0.0,
        'default_strength': 0.5
    },

    # Dimension Associator
    'dimensions': {
        'learning_rate': 0.05,
        'activation_threshold': 0.6,   # Consider dimension "active"
        'prediction_threshold': 0.65,  # Confidence for predictions
        'multi_dim_min_size': 3        # Min dimensions for pattern
    },

    # Sequence Learner
    'sequences': {
        'pattern_threshold': 5,        # Min frequency for pattern
        'prediction_confidence': 0.7,  # Min confidence to anticipate
        'max_history_length': 10       # Max states to track
    },

    # Performance
    'performance': {
        'enable_caching': True,
        'cache_size': 200,
        'cache_refresh_interval': 100,
        'batch_size': 10               # Batch DB updates
    },

    # Safety
    'safety': {
        'max_decay_iterations': 100,   # Prevent infinite decay loops
        'strength_cap': 1.0,
        'strength_floor': 0.0
    }
}
```

### **Per-User Configuration** (Future)

```python
# Allow per-user overrides
USER_HEBBIAN_CONFIG = {
    'user_123': {
        'vocab': {
            'learning_rate': 0.07,  # Learn faster for this user
            'confidence_threshold': 0.70  # Higher threshold
        }
    }
}
```

---

## Edge Cases & Error Handling

### **Edge Case 1: Cold Start (No Training Data)**

**Problem:** System has no observations yet, all strengths are default (0.5)

**Solution:**
```python
def get_association_strength_with_fallback(term: str, context: str) -> float:
    """Get association with intelligent fallback for cold start"""

    # Try database lookup
    strength = get_association_strength(term, context)

    # If no observations, use heuristics
    if strength == DEFAULT_STRENGTH and observation_count == 0:
        # Use keyword-based heuristics
        if term in SLANG_TERMS and context in ['casual_chat', 'opinion_request']:
            return 0.7  # Slang likely belongs in casual
        elif term in FORMAL_TERMS and context in ['formal_technical', 'problem_solving']:
            return 0.7  # Formal terms belong in formal contexts

    return strength
```

### **Edge Case 2: Conflicting Patterns**

**Problem:** Two patterns suggest opposite actions

**Example:**
- Pattern A: `problem → simple` (skip complex explanation)
- Pattern B: `problem → technical → simple` (give complex first)

**Solution:**
```python
def resolve_conflicting_patterns(patterns: List[PatternTemplate]) -> PatternTemplate:
    """Resolve conflicts by choosing highest confidence + frequency"""

    # Score each pattern
    scored_patterns = [
        (pattern, pattern.avg_satisfaction * math.log(pattern.frequency))
        for pattern in patterns
    ]

    # Return highest scoring pattern
    return max(scored_patterns, key=lambda x: x[1])[0]
```

### **Edge Case 3: Runaway Strengthening**

**Problem:** Association strength grows unbounded

**Solution:** Already handled by cap in algorithm:
```python
new_strength = min(MAX_STRENGTH, current_strength + delta)
```

### **Edge Case 4: Database Corruption**

**Problem:** Database file corrupted or connection fails

**Solution:**
```python
def safe_database_operation(operation: Callable, *args, **kwargs):
    """Wrap database operations with error handling"""
    try:
        return operation(*args, **kwargs)
    except sqlite3.DatabaseError as e:
        logger.error(f"Database error: {e}")
        # Attempt to reconnect
        try:
            reconnect_database()
            return operation(*args, **kwargs)
        except:
            logger.critical("Database reconnection failed, using in-memory fallback")
            # Use in-memory cache for this session
            return fallback_operation(*args, **kwargs)
```

### **Edge Case 5: Memory Overflow**

**Problem:** Association matrix grows too large

**Solution:**
```python
def prune_weak_associations(min_strength: float = 0.1,
                           min_observations: int = 2) -> int:
    """Remove weak, rarely-observed associations"""

    query = """
        DELETE FROM vocab_associations
        WHERE strength < ? AND observation_count < ?
    """

    cursor.execute(query, (min_strength, min_observations))
    deleted = cursor.rowcount

    logger.info(f"Pruned {deleted} weak associations")
    return deleted
```

### **Edge Case 6: NaN or Inf Values**

**Problem:** Arithmetic errors produce invalid values

**Solution:**
```python
def safe_strength_update(current: float, delta: float) -> float:
    """Safely update strength with NaN/Inf protection"""

    new_strength = current + delta

    # Check for invalid values
    if math.isnan(new_strength) or math.isinf(new_strength):
        logger.warning(f"Invalid strength value detected: {new_strength}, using default")
        return DEFAULT_STRENGTH

    # Apply bounds
    return max(MIN_STRENGTH, min(MAX_STRENGTH, new_strength))
```

---

## Testing Requirements

### **Unit Tests**

```python
def test_hebbian_strengthening():
    """Verify basic Hebbian strengthening"""
    associator = HebbianVocabularyAssociator()
    initial = associator.get_association_strength("test", "context1")

    for _ in range(10):
        associator.observe_term_in_context("test", "context1")

    final = associator.get_association_strength("test", "context1")
    assert final > initial

def test_competitive_weakening():
    """Verify competitive weakening of non-active contexts"""
    # Test implementation...

def test_coactivation_prediction():
    """Verify dimension co-activation prediction"""
    # Test implementation...

def test_sequence_prediction():
    """Verify conversation sequence prediction"""
    # Test implementation...
```

### **Integration Tests**

```python
def test_full_pipeline():
    """Test complete Hebbian learning pipeline"""
    manager = HebbianLearningManager()

    # Simulate conversation
    result = manager.process_conversation_turn(
        user_message="ngl this is confusing",
        assistant_response="Let me simplify...",
        context={'formality': 0.3, 'mood': 'frustrated'},
        active_dimensions={'empathy': 0.8, 'brief': 0.9}
    )

    assert result['vocab_observations'] > 0
    assert result['coactivations_updated'] > 0
    assert result['state_transitions'] > 0
```

---

**Status:** ✅ Detailed Specifications Complete
**Next Step:** Design database schema in `HEBBIAN_DATABASE_SCHEMA.sql`

---

*Designed for Penny's Phase 3E Enhancement - October 27, 2025*
