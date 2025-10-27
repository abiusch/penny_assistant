# 🧠 Hebbian Learning Layer - Implementation Skeletons

**Date:** October 27, 2025
**Status:** Design Specification
**Purpose:** Python class skeletons with method signatures, docstrings, and type hints

---

## 📋 File Structure

```
src/personality/
├── hebbian_vocabulary_associator.py       # Component 1
├── hebbian_dimension_associator.py        # Component 2
├── hebbian_sequence_learner.py            # Component 3
├── hebbian_learning_manager.py            # Component 4 (orchestrator)
├── hebbian_config.py                      # Configuration
└── hebbian_types.py                       # Shared data types
```

---

## File 1: `hebbian_types.py`

**Purpose:** Shared data types and constants across all Hebbian components

```python
#!/usr/bin/env python3
"""
Hebbian Learning Types and Constants
Shared data structures for all Hebbian learning components
"""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum

# ============================================================================
# ENUMS
# ============================================================================

class ContextType(Enum):
    """Conversation context types for vocabulary association"""
    CASUAL_CHAT = "casual_chat"
    FORMAL_TECHNICAL = "formal_technical"
    PROBLEM_SOLVING = "problem_solving"
    CREATIVE_DISCUSSION = "creative_discussion"
    EMOTIONAL_SUPPORT = "emotional_support"
    QUICK_QUERY = "quick_query"


class ConversationState(Enum):
    """Conversation states for sequence learning"""
    PROBLEM_STATEMENT = "problem_statement"
    CLARIFICATION_QUESTION = "clarification_question"
    TECHNICAL_EXPLANATION = "technical_explanation"
    SIMPLIFIED_EXPLANATION = "simplified_explanation"
    CODE_REVIEW = "code_review"
    DEBUGGING_HELP = "debugging_help"
    OPINION_REQUEST = "opinion_request"
    CASUAL_CHAT = "casual_chat"
    FOLLOW_UP_QUESTION = "follow_up_question"
    POSITIVE_FEEDBACK = "positive_feedback"
    CORRECTION_REQUEST = "correction_request"
    FRUSTRATION_EXPRESSION = "frustration_expression"


# ============================================================================
# DATA CLASSES: Vocabulary
# ============================================================================

@dataclass
class VocabularyAssociation:
    """Represents a term-context association"""
    term: str
    context_type: str
    strength: float  # 0.0 to 1.0
    observation_count: int
    last_updated: datetime
    first_observed: datetime

    def __post_init__(self):
        """Validate strength bounds"""
        if not 0.0 <= self.strength <= 1.0:
            raise ValueError(f"Strength must be 0.0-1.0, got {self.strength}")


@dataclass
class VocabularyObservation:
    """Represents a single observation of a term in context"""
    term: str
    context_type: str
    timestamp: datetime
    user_message: str
    session_id: Optional[str] = None


# ============================================================================
# DATA CLASSES: Dimensions
# ============================================================================

@dataclass
class DimensionCoactivation:
    """Represents co-activation between two personality dimensions"""
    dim1: str
    dim2: str
    strength: float  # 0.0 to 1.0
    observation_count: int
    last_updated: datetime
    first_observed: datetime

    def __post_init__(self):
        """Ensure dim1 < dim2 to avoid duplicates"""
        if self.dim1 > self.dim2:
            self.dim1, self.dim2 = self.dim2, self.dim1


@dataclass
class MultiDimensionalPattern:
    """Represents a pattern of 3+ dimensions activating together"""
    pattern_id: str
    dimensions: Dict[str, float]  # {dim_name: typical_value}
    frequency: int
    avg_satisfaction: float
    last_observed: datetime
    first_observed: datetime


@dataclass
class NegativeCorrelation:
    """Represents dimensions that anti-correlate"""
    dim_high: str
    dim_low: str
    correlation_strength: float
    observation_count: int


@dataclass
class DimensionPrediction:
    """Prediction of dimension value based on co-activations"""
    dimension: str
    predicted_value: float
    confidence: float
    sources: List[str]  # Which dimensions contributed to prediction


# ============================================================================
# DATA CLASSES: Sequences
# ============================================================================

@dataclass
class StateTransition:
    """Represents a transition between conversation states"""
    state_from: str
    state_to: str
    transition_count: int
    transition_probability: float
    last_observed: datetime
    first_observed: datetime


@dataclass
class StateSequence:
    """Represents a sequence of conversation states"""
    sequence: List[str]
    frequency: int
    avg_satisfaction: float
    last_observed: datetime
    first_observed: datetime


@dataclass
class SkipOpportunity:
    """Represents a state that can potentially be skipped"""
    from_state: str
    skip_state: str
    to_state: str
    confidence: float


@dataclass
class PatternTemplate:
    """Represents a recurring pattern with actionable insights"""
    pattern_id: str
    sequence: List[str]
    frequency: int
    avg_satisfaction: float
    skip_opportunities: List[SkipOpportunity]
    last_applied: Optional[datetime] = None


@dataclass
class AnticipatedResponse:
    """Represents an anticipated user need"""
    current_state: str
    likely_next_states: List[Tuple[str, float]]  # (state, probability)
    suggested_action: Optional[str]
    confidence: float


# ============================================================================
# CONSTANTS
# ============================================================================

# Default configuration values
DEFAULT_LEARNING_RATE = 0.05
DEFAULT_COMPETITIVE_RATE = 0.01
DEFAULT_DECAY_RATE_PER_DAY = 0.001
DEFAULT_CONFIDENCE_THRESHOLD = 0.65
DEFAULT_ACTIVATION_THRESHOLD = 0.6
DEFAULT_PATTERN_THRESHOLD = 5

# Context type definitions
CONTEXT_DEFINITIONS = {
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

# Personality dimensions (from existing personality_tracker.py)
PERSONALITY_DIMENSIONS = [
    'communication_formality',
    'technical_depth_preference',
    'humor_style_preference',
    'response_length_preference',
    'conversation_pace_preference',
    'proactive_suggestions',
    'emotional_support_style'
]
```

---

## File 2: `hebbian_vocabulary_associator.py`

**Purpose:** Learn vocabulary-context associations

```python
#!/usr/bin/env python3
"""
Hebbian Vocabulary Associator
Learns which vocabulary terms belong in which conversational contexts
through Hebbian learning with competitive inhibition
"""

import sqlite3
import re
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Set
from collections import defaultdict
from functools import lru_cache
import logging

from hebbian_types import (
    VocabularyAssociation,
    VocabularyObservation,
    ContextType,
    CONTEXT_DEFINITIONS,
    DEFAULT_LEARNING_RATE,
    DEFAULT_COMPETITIVE_RATE,
    DEFAULT_DECAY_RATE_PER_DAY,
    DEFAULT_CONFIDENCE_THRESHOLD
)

logger = logging.getLogger(__name__)


class HebbianVocabularyAssociator:
    """
    Learns vocabulary-context associations through Hebbian learning

    Core Algorithm:
    1. Strengthen association when term appears in context (Hebbian rule)
    2. Weaken competing associations (competitive learning)
    3. Apply temporal decay to unused associations
    4. Provide predictions for term appropriateness
    """

    def __init__(
        self,
        db_path: str = "data/personality_tracking.db",
        learning_rate: float = DEFAULT_LEARNING_RATE,
        competitive_rate: float = DEFAULT_COMPETITIVE_RATE,
        decay_rate_per_day: float = DEFAULT_DECAY_RATE_PER_DAY
    ):
        """
        Initialize vocabulary associator

        Args:
            db_path: Path to SQLite database
            learning_rate: Rate of association strengthening (0.0-1.0)
            competitive_rate: Rate of competitive weakening (0.0-1.0)
            decay_rate_per_day: Daily decay rate for unused associations
        """
        self.db_path = db_path
        self.learning_rate = learning_rate
        self.competitive_rate = competitive_rate
        self.decay_rate_per_day = decay_rate_per_day

        # TODO: Initialize database connection
        # TODO: Create tables if not exist
        # TODO: Load configuration from database

    # ========================================================================
    # CORE LEARNING METHODS
    # ========================================================================

    def observe_term_in_context(
        self,
        term: str,
        context: str,
        session_id: Optional[str] = None
    ) -> None:
        """
        Observe term in context, update associations via Hebbian learning

        Algorithm:
        1. Get current strength for term-context pair
        2. Apply Hebbian strengthening: Δw = η * (1 - w)
        3. Apply competitive weakening to other contexts
        4. Update database with new strengths
        5. Log observation

        Args:
            term: The vocabulary term (normalized to lowercase)
            context: The conversation context type
            session_id: Optional session identifier
        """
        # TODO: Normalize term (lowercase, trim)
        # TODO: Get current association strength
        # TODO: Apply Hebbian strengthening
        # TODO: Apply competitive weakening to other contexts
        # TODO: Update database
        # TODO: Log observation
        pass

    def observe_conversation(
        self,
        user_message: str,
        context: str,
        session_id: Optional[str] = None
    ) -> List[str]:
        """
        Extract terms from message and observe all associations

        Args:
            user_message: User's message text
            context: Conversation context type
            session_id: Optional session identifier

        Returns:
            List of terms observed
        """
        # TODO: Extract terms (tokenize, filter stopwords)
        # TODO: For each term, call observe_term_in_context()
        # TODO: Return list of observed terms
        pass

    # ========================================================================
    # QUERY METHODS
    # ========================================================================

    def get_association_strength(
        self,
        term: str,
        context: str
    ) -> float:
        """
        Get current association strength between term and context

        Args:
            term: The vocabulary term
            context: The conversation context type

        Returns:
            float: Association strength (0.0-1.0), default 0.5 if not observed
        """
        # TODO: Query database for association
        # TODO: Return strength or default (0.5)
        # TODO: Apply any active overrides
        pass

    def should_use_term(
        self,
        term: str,
        context: str,
        threshold: float = DEFAULT_CONFIDENCE_THRESHOLD
    ) -> bool:
        """
        Determine if term is appropriate for context

        Args:
            term: The vocabulary term
            context: The conversation context type
            threshold: Minimum strength to recommend usage

        Returns:
            bool: True if term should be used in this context
        """
        # TODO: Get association strength
        # TODO: Compare to threshold
        # TODO: Check for manual overrides (always block certain terms)
        pass

    def get_top_contexts_for_term(
        self,
        term: str,
        n: int = 3
    ) -> List[Tuple[str, float]]:
        """
        Get top N contexts where term is most appropriate

        Args:
            term: The vocabulary term
            n: Number of top contexts to return

        Returns:
            List of (context, strength) tuples, sorted by strength desc
        """
        # TODO: Query all contexts for term
        # TODO: Sort by strength descending
        # TODO: Return top N
        pass

    # ========================================================================
    # FILTERING METHODS
    # ========================================================================

    def filter_response_vocabulary(
        self,
        response: str,
        context: str,
        threshold: float = DEFAULT_CONFIDENCE_THRESHOLD
    ) -> str:
        """
        Filter out inappropriate vocabulary from response

        Args:
            response: Assistant's generated response
            context: Conversation context type
            threshold: Minimum strength to allow usage

        Returns:
            str: Filtered response with inappropriate terms removed
        """
        # TODO: Tokenize response
        # TODO: For each token, check should_use_term()
        # TODO: Replace inappropriate terms with alternatives or remove
        # TODO: Reconstruct and return filtered response
        pass

    # ========================================================================
    # MAINTENANCE METHODS
    # ========================================================================

    def apply_temporal_decay(
        self,
        days_inactive: float = 1.0
    ) -> int:
        """
        Apply time-based decay to unused associations

        Decay formula: strength *= (1 - decay_rate * days_inactive)

        Args:
            days_inactive: Number of days since last update for decay

        Returns:
            int: Number of associations decayed
        """
        # TODO: Query associations not updated in last N days
        # TODO: Apply decay formula to each
        # TODO: Update database
        # TODO: Return count of decayed associations
        pass

    def prune_weak_associations(
        self,
        min_strength: float = 0.1,
        min_observations: int = 2
    ) -> int:
        """
        Remove weak, rarely-observed associations to save space

        Args:
            min_strength: Minimum strength to keep
            min_observations: Minimum observation count to keep

        Returns:
            int: Number of associations pruned
        """
        # TODO: Query weak associations
        # TODO: Delete from database
        # TODO: Return count deleted
        pass

    # ========================================================================
    # EXPORT & DEBUG METHODS
    # ========================================================================

    def export_association_matrix(self) -> List[Dict]:
        """
        Export all associations for analysis

        Returns:
            List of dicts with keys: term, context, strength, observations
        """
        # TODO: Query all associations
        # TODO: Format as list of dicts
        # TODO: Return
        pass

    def get_statistics(self) -> Dict[str, any]:
        """
        Get system statistics

        Returns:
            Dict with counts, averages, etc.
        """
        # TODO: Count total associations
        # TODO: Count strong associations (>threshold)
        # TODO: Calculate average strength
        # TODO: Get most/least associated terms
        # TODO: Return stats dict
        pass

    # ========================================================================
    # PRIVATE HELPER METHODS
    # ========================================================================

    def _normalize_term(self, term: str) -> str:
        """Normalize term to lowercase, trimmed"""
        # TODO: Implement
        pass

    def _cap_strength(self, strength: float) -> float:
        """Cap strength to valid range [0.0, 1.0]"""
        # TODO: Implement
        pass

    def _extract_terms(self, message: str) -> List[str]:
        """Extract terms from message (tokenize, filter)"""
        # TODO: Tokenize
        # TODO: Filter stopwords
        # TODO: Return terms
        pass

    def _get_all_contexts(self) -> List[str]:
        """Get list of all context types"""
        # TODO: Return list of context type strings
        pass
```

---

## File 3: `hebbian_dimension_associator.py`

**Purpose:** Learn personality dimension co-activations

```python
#!/usr/bin/env python3
"""
Hebbian Dimension Associator
Learns which personality dimensions naturally co-activate together
"""

import sqlite3
import json
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from collections import defaultdict
import logging

from hebbian_types import (
    DimensionCoactivation,
    MultiDimensionalPattern,
    NegativeCorrelation,
    DimensionPrediction,
    PERSONALITY_DIMENSIONS,
    DEFAULT_LEARNING_RATE,
    DEFAULT_ACTIVATION_THRESHOLD,
    DEFAULT_CONFIDENCE_THRESHOLD
)

logger = logging.getLogger(__name__)


class HebbianDimensionAssociator:
    """
    Learns personality dimension co-activations through Hebbian learning

    Core Algorithm:
    1. Observe which dimensions are active simultaneously
    2. Strengthen pairwise co-activations via Δw = η * x1 * x2
    3. Detect multi-dimensional patterns (3+ dims)
    4. Predict dimension values based on known activations
    """

    def __init__(
        self,
        db_path: str = "data/personality_tracking.db",
        learning_rate: float = DEFAULT_LEARNING_RATE,
        activation_threshold: float = DEFAULT_ACTIVATION_THRESHOLD
    ):
        """
        Initialize dimension associator

        Args:
            db_path: Path to SQLite database
            learning_rate: Rate of co-activation strengthening
            activation_threshold: Threshold for considering dimension "active"
        """
        self.db_path = db_path
        self.learning_rate = learning_rate
        self.activation_threshold = activation_threshold

        # TODO: Initialize database connection
        # TODO: Create tables if not exist
        # TODO: Load configuration

    # ========================================================================
    # CORE LEARNING METHODS
    # ========================================================================

    def observe_activations(
        self,
        dimensions: Dict[str, float],
        session_id: Optional[str] = None
    ) -> None:
        """
        Observe dimension activations, update co-activations

        Algorithm:
        1. Filter to active dimensions (value > threshold)
        2. For each pair of active dimensions:
           - Strengthen co-activation: Δw = η * x1 * x2
        3. Detect multi-dimensional patterns if 3+ active
        4. Check for negative correlations
        5. Update database

        Args:
            dimensions: Dict of dimension_name -> current_value
            session_id: Optional session identifier
        """
        # TODO: Filter to active dimensions
        # TODO: For each pair, update co-activation strength
        # TODO: Detect multi-dim patterns
        # TODO: Check negative correlations
        # TODO: Log observation
        pass

    # ========================================================================
    # QUERY METHODS
    # ========================================================================

    def get_coactivation_strength(
        self,
        dim1: str,
        dim2: str
    ) -> float:
        """
        Get co-activation strength between two dimensions

        Args:
            dim1: First dimension name
            dim2: Second dimension name

        Returns:
            float: Co-activation strength (0.0-1.0), default 0.0
        """
        # TODO: Normalize order (dim1 < dim2)
        # TODO: Query database
        # TODO: Return strength or default (0.0)
        pass

    def get_strongest_coactivations(
        self,
        dimension: str,
        n: int = 5
    ) -> List[Tuple[str, float]]:
        """
        Get dimensions that most strongly co-activate with given dimension

        Args:
            dimension: Dimension name
            n: Number of top co-activations to return

        Returns:
            List of (other_dimension, strength) tuples
        """
        # TODO: Query coactivations where dim1 or dim2 matches
        # TODO: Sort by strength descending
        # TODO: Return top N
        pass

    # ========================================================================
    # PREDICTION METHODS
    # ========================================================================

    def predict_coactivations(
        self,
        known_dimensions: Dict[str, float],
        threshold: float = DEFAULT_CONFIDENCE_THRESHOLD
    ) -> Dict[str, DimensionPrediction]:
        """
        Predict other dimension values based on known active dimensions

        Algorithm:
        1. For each known dimension that's active (> threshold)
        2. Find strongly co-activated dimensions
        3. Predict their values: predicted_val = known_val * coact_strength
        4. Average predictions if multiple sources
        5. Return high-confidence predictions only

        Args:
            known_dimensions: Dict of known dimension_name -> value
            threshold: Minimum confidence for predictions

        Returns:
            Dict of predicted dimension_name -> DimensionPrediction
        """
        # TODO: Implement prediction algorithm
        # TODO: For each known active dimension
        # TODO: Get strong co-activations
        # TODO: Predict values
        # TODO: Average multiple predictions
        # TODO: Filter by confidence threshold
        # TODO: Return predictions
        pass

    # ========================================================================
    # PATTERN DETECTION METHODS
    # ========================================================================

    def get_multi_dim_patterns(
        self,
        min_frequency: int = 3
    ) -> List[MultiDimensionalPattern]:
        """
        Get recurring patterns of 3+ dimensions activating together

        Args:
            min_frequency: Minimum observation count to include

        Returns:
            List of MultiDimensionalPattern objects
        """
        # TODO: Query multi_dim_patterns table
        # TODO: Filter by frequency
        # TODO: Sort by frequency/satisfaction
        # TODO: Return patterns
        pass

    def detect_negative_correlations(
        self,
        threshold: float = 0.6
    ) -> List[NegativeCorrelation]:
        """
        Detect dimension pairs that anti-correlate

        Args:
            threshold: Minimum correlation strength to report

        Returns:
            List of NegativeCorrelation objects
        """
        # TODO: Query negative_correlations table
        # TODO: Filter by strength
        # TODO: Return correlations
        pass

    # ========================================================================
    # EXPORT & DEBUG METHODS
    # ========================================================================

    def export_coactivation_matrix(self) -> List[Dict]:
        """
        Export co-activation matrix for analysis

        Returns:
            List of dicts with keys: dim1, dim2, strength, observations
        """
        # TODO: Query all coactivations
        # TODO: Format as list of dicts
        # TODO: Return
        pass

    def visualize_coactivation_network(
        self,
        output_path: str = "coactivation_network.png"
    ) -> None:
        """
        Generate NetworkX visualization of co-activation network

        Args:
            output_path: Path to save visualization image
        """
        # TODO: Import networkx, matplotlib
        # TODO: Create graph with dimensions as nodes
        # TODO: Add edges for strong coactivations
        # TODO: Draw and save
        pass

    def get_statistics(self) -> Dict[str, any]:
        """Get system statistics"""
        # TODO: Count coactivations
        # TODO: Average strength
        # TODO: Most/least connected dimensions
        # TODO: Return stats
        pass

    # ========================================================================
    # PRIVATE HELPER METHODS
    # ========================================================================

    def _normalize_dim_pair(
        self,
        dim1: str,
        dim2: str
    ) -> Tuple[str, str]:
        """Ensure dim1 < dim2 to avoid duplicates"""
        # TODO: Implement
        pass

    def _is_dimension_active(
        self,
        value: float
    ) -> bool:
        """Check if dimension value exceeds activation threshold"""
        # TODO: Implement
        pass

    def _generate_pattern_id(
        self,
        dimensions: Dict[str, float]
    ) -> str:
        """Generate unique ID for multi-dimensional pattern"""
        # TODO: Implement (hash of sorted dimension names)
        pass
```

---

## File 4: `hebbian_sequence_learner.py`

**Purpose:** Learn conversation flow patterns

```python
#!/usr/bin/env python3
"""
Hebbian Sequence Learner
Learns sequential patterns in conversation states to anticipate user needs
"""

import sqlite3
import json
import hashlib
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from collections import defaultdict
import re
import logging

from hebbian_types import (
    StateTransition,
    StateSequence,
    PatternTemplate,
    SkipOpportunity,
    AnticipatedResponse,
    ConversationState,
    DEFAULT_PATTERN_THRESHOLD
)

logger = logging.getLogger(__name__)


class HebbianSequenceLearner:
    """
    Learns conversation flow patterns through Markov chain transition learning

    Core Algorithm:
    1. Classify conversation states from messages
    2. Observe state transitions, update transition matrix
    3. Detect recurring sequences (n-grams)
    4. Identify skip opportunities (predictable intermediate states)
    5. Anticipate user needs based on patterns
    """

    def __init__(
        self,
        db_path: str = "data/personality_tracking.db",
        pattern_threshold: int = DEFAULT_PATTERN_THRESHOLD
    ):
        """
        Initialize sequence learner

        Args:
            db_path: Path to SQLite database
            pattern_threshold: Minimum frequency to create pattern template
        """
        self.db_path = db_path
        self.pattern_threshold = pattern_threshold

        # Conversation state history (in-memory)
        self.conversation_history: List[str] = []

        # TODO: Initialize database connection
        # TODO: Create tables if not exist
        # TODO: Load configuration
        # TODO: Load state classification rules

    # ========================================================================
    # STATE CLASSIFICATION METHODS
    # ========================================================================

    def classify_conversation_state(
        self,
        message: str,
        context: Dict[str, any]
    ) -> str:
        """
        Classify message into conversation state

        Algorithm:
        1. Normalize message (lowercase)
        2. Check for explicit indicators (keywords, phrases)
        3. Check contextual clues (follow-up, sentiment)
        4. Use heuristics and regex patterns
        5. Return most confident classification

        Args:
            message: User's message text
            context: Contextual information (formality, mood, is_follow_up, etc.)

        Returns:
            str: Conversation state classification
        """
        # TODO: Normalize message
        # TODO: Check priority 1 indicators (problem statement)
        # TODO: Check priority 2 indicators (clarification)
        # TODO: Check priority 3 indicators (simplification)
        # TODO: Check priority 4 indicators (feedback)
        # TODO: Check priority 5 indicators (frustration)
        # TODO: Default classification based on context
        # TODO: Return state
        pass

    # ========================================================================
    # TRANSITION LEARNING METHODS
    # ========================================================================

    def observe_transition(
        self,
        state_from: str,
        state_to: str,
        satisfaction: Optional[float] = None
    ) -> None:
        """
        Observe state transition, update transition matrix

        Algorithm:
        1. Increment transition count
        2. Recalculate transition probabilities for state_from
        3. Check if recent sequence forms a recurring pattern
        4. Update database

        Args:
            state_from: Previous conversation state
            state_to: Current conversation state
            satisfaction: Optional user satisfaction score (0.0-1.0)
        """
        # TODO: Increment transition count
        # TODO: Recalculate probabilities
        # TODO: Update conversation_history
        # TODO: Check for sequence patterns
        # TODO: Update database
        pass

    # ========================================================================
    # QUERY METHODS
    # ========================================================================

    def get_transition_probability(
        self,
        state_from: str,
        state_to: str
    ) -> float:
        """
        Get probability of transitioning from one state to another

        Args:
            state_from: Source state
            state_to: Target state

        Returns:
            float: Transition probability (0.0-1.0)
        """
        # TODO: Query database
        # TODO: Return probability or 0.0 if not observed
        pass

    def predict_next_states(
        self,
        current_state: str,
        history: List[str],
        n: int = 3
    ) -> List[Tuple[str, float]]:
        """
        Predict most likely next conversation states

        Args:
            current_state: Current conversation state
            history: Recent state history
            n: Number of top predictions to return

        Returns:
            List of (next_state, probability) tuples
        """
        # TODO: Query transitions from current_state
        # TODO: Sort by probability descending
        # TODO: Consider recent history for context
        # TODO: Return top N
        pass

    # ========================================================================
    # PATTERN DETECTION METHODS
    # ========================================================================

    def detect_recurring_patterns(
        self,
        min_frequency: int = None
    ) -> List[PatternTemplate]:
        """
        Detect recurring conversation patterns

        Algorithm:
        1. Get sequences with frequency >= threshold
        2. Calculate average user satisfaction
        3. Identify skip opportunities (predictable intermediate states)
        4. Return pattern templates

        Args:
            min_frequency: Minimum observation count (default: pattern_threshold)

        Returns:
            List of PatternTemplate objects
        """
        # TODO: Query state_sequences table
        # TODO: Filter by frequency
        # TODO: For each sequence, detect skip opportunities
        # TODO: Create PatternTemplate objects
        # TODO: Return patterns
        pass

    def anticipate_user_need(
        self,
        current_state: str,
        history: List[str]
    ) -> Optional[AnticipatedResponse]:
        """
        Anticipate user's next need based on patterns

        Args:
            current_state: Current conversation state
            history: Recent state history

        Returns:
            AnticipatedResponse object if confident prediction, else None
        """
        # TODO: Get likely next states
        # TODO: Check for matching pattern templates
        # TODO: If high-confidence match, create AnticipatedResponse
        # TODO: Suggest action (e.g., "User likely to request simplification")
        # TODO: Return anticipation or None
        pass

    # ========================================================================
    # EXPORT & DEBUG METHODS
    # ========================================================================

    def export_transition_matrix(self) -> List[Dict]:
        """
        Export transition matrix for analysis

        Returns:
            List of dicts with keys: state_from, state_to, probability, count
        """
        # TODO: Query all transitions
        # TODO: Format as list of dicts
        # TODO: Return
        pass

    def visualize_state_graph(
        self,
        output_path: str = "state_transitions.png",
        min_probability: float = 0.1
    ) -> None:
        """
        Generate graph visualization of state transitions

        Args:
            output_path: Path to save visualization
            min_probability: Minimum probability to show edge
        """
        # TODO: Import networkx, matplotlib
        # TODO: Create directed graph
        # TODO: Add nodes (states)
        # TODO: Add edges (transitions with prob > min_probability)
        # TODO: Draw and save
        pass

    def get_statistics(self) -> Dict[str, any]:
        """Get system statistics"""
        # TODO: Count total transitions
        # TODO: Count recurring sequences
        # TODO: Count pattern templates
        # TODO: Most/least common transitions
        # TODO: Return stats
        pass

    # ========================================================================
    # PRIVATE HELPER METHODS
    # ========================================================================

    def _check_for_sequence_pattern(self) -> None:
        """Check if recent history forms a recurring pattern"""
        # TODO: Get last 3-5 states from history
        # TODO: Generate sequence hash
        # TODO: Check if sequence exists in database
        # TODO: If yes, increment frequency
        # TODO: If no and meets threshold, create new sequence
        pass

    def _generate_sequence_hash(
        self,
        sequence: List[str]
    ) -> str:
        """Generate hash for sequence"""
        # TODO: Implement (hash of concatenated states)
        pass

    def _detect_skip_opportunities(
        self,
        sequence: List[str]
    ) -> List[SkipOpportunity]:
        """Detect states that can be skipped in sequence"""
        # TODO: For each triplet (A, B, C) in sequence
        # TODO: Check if direct A→C transition exists with decent probability
        # TODO: If yes, B is a skip candidate
        # TODO: Return list of SkipOpportunity objects
        pass
```

---

## File 5: `hebbian_learning_manager.py`

**Purpose:** Orchestrate all Hebbian components

```python
#!/usr/bin/env python3
"""
Hebbian Learning Manager
Central orchestrator for all Hebbian learning components
Provides unified interface and performance optimization
"""

import time
from functools import lru_cache
from typing import Dict, List, Optional, Any
import logging

from hebbian_vocabulary_associator import HebbianVocabularyAssociator
from hebbian_dimension_associator import HebbianDimensionAssociator
from hebbian_sequence_learner import HebbianSequenceLearner
from hebbian_config import HebbianConfig

logger = logging.getLogger(__name__)


class HebbianLearningManager:
    """
    Central manager for all Hebbian learning components

    Features:
    - Unified interface for all components
    - Performance optimization via caching
    - Batch updates for efficiency
    - Health monitoring and statistics
    """

    def __init__(
        self,
        db_path: str = "data/personality_tracking.db",
        enable_caching: bool = True,
        cache_size: int = 200
    ):
        """
        Initialize Hebbian learning manager

        Args:
            db_path: Path to database
            enable_caching: Whether to use LRU caches for performance
            cache_size: Size of LRU caches
        """
        self.db_path = db_path
        self.enable_caching = enable_caching

        # Initialize components
        self.vocab_associator = HebbianVocabularyAssociator(db_path)
        self.dim_associator = HebbianDimensionAssociator(db_path)
        self.sequence_learner = HebbianSequenceLearner(db_path)

        # Performance tracking
        self.conversation_count = 0
        self.cache_refresh_interval = 100

        # TODO: Initialize caches if enabled
        # TODO: Load configuration from database

    # ========================================================================
    # MAIN PROCESSING METHOD
    # ========================================================================

    def process_conversation_turn(
        self,
        user_message: str,
        assistant_response: str,
        context: Dict[str, Any],
        active_dimensions: Dict[str, float]
    ) -> Dict[str, Any]:
        """
        Process a complete conversation turn through all Hebbian components

        This is the main entry point for Hebbian learning updates.

        Args:
            user_message: User's message
            assistant_response: Assistant's response
            context: Conversation context
            active_dimensions: Current personality dimension values

        Returns:
            Dict with learning updates and predictions
        """
        start_time = time.time()

        result = {
            'vocab_observations': 0,
            'coactivations_updated': 0,
            'state_transitions': 0,
            'predictions': {},
            'latency_ms': 0
        }

        # TODO: 1. Classify conversation state
        # TODO: 2. Observe vocabulary associations
        # TODO: 3. Observe dimension co-activations
        # TODO: 4. Observe state transitions
        # TODO: 5. Generate predictions for next turn
        # TODO: 6. Update statistics
        # TODO: 7. Refresh caches if needed

        result['latency_ms'] = (time.time() - start_time) * 1000
        self.conversation_count += 1

        return result

    # ========================================================================
    # CACHED QUERY METHODS
    # ========================================================================

    @lru_cache(maxsize=200)
    def should_use_term_cached(
        self,
        term: str,
        context: str,
        threshold: float = 0.65
    ) -> bool:
        """
        Cached version of should_use_term for performance

        Args:
            term: Vocabulary term
            context: Conversation context
            threshold: Confidence threshold

        Returns:
            bool: Whether term should be used
        """
        # TODO: Call vocab_associator.should_use_term() with caching
        pass

    @lru_cache(maxsize=50)
    def predict_coactivations_cached(
        self,
        known_dims_tuple: Tuple[Tuple[str, float], ...],
        threshold: float = 0.65
    ) -> Dict[str, Any]:
        """
        Cached version of predict_coactivations

        Note: Uses tuple of tuples for hashability (LRU cache requirement)

        Args:
            known_dims_tuple: Tuple of (dim_name, value) tuples
            threshold: Confidence threshold

        Returns:
            Dict of predictions
        """
        # TODO: Convert tuple to dict
        # TODO: Call dim_associator.predict_coactivations() with caching
        pass

    # ========================================================================
    # MAINTENANCE METHODS
    # ========================================================================

    def apply_temporal_decay_all(
        self,
        days_inactive: float = 1.0
    ) -> Dict[str, int]:
        """
        Apply temporal decay to all components

        Args:
            days_inactive: Days since last use for decay

        Returns:
            Dict with count of decayed items per component
        """
        return {
            'vocab_associations': self.vocab_associator.apply_temporal_decay(days_inactive),
            'coactivations': 0,  # TODO: Implement decay for coactivations if needed
            'transitions': 0     # TODO: Implement decay for transitions if needed
        }

    def refresh_caches(self) -> None:
        """Refresh all caches (call periodically)"""
        if self.enable_caching:
            self.should_use_term_cached.cache_clear()
            self.predict_coactivations_cached.cache_clear()
            logger.info("Hebbian caches refreshed")

    def prune_all(
        self,
        min_strength: float = 0.1,
        min_observations: int = 2
    ) -> Dict[str, int]:
        """
        Prune weak data from all components

        Args:
            min_strength: Minimum strength to keep
            min_observations: Minimum observation count to keep

        Returns:
            Dict with count of pruned items per component
        """
        return {
            'vocab_associations': self.vocab_associator.prune_weak_associations(
                min_strength, min_observations
            ),
            # TODO: Add pruning for other components if needed
        }

    # ========================================================================
    # EXPORT & MONITORING METHODS
    # ========================================================================

    def export_all_data(self) -> Dict[str, List[Dict]]:
        """
        Export all Hebbian learning data

        Returns:
            Dict with data from each component
        """
        return {
            'vocab_associations': self.vocab_associator.export_association_matrix(),
            'coactivations': self.dim_associator.export_coactivation_matrix(),
            'transitions': self.sequence_learner.export_transition_matrix()
        }

    def get_system_stats(self) -> Dict[str, Any]:
        """
        Get comprehensive statistics about Hebbian learning system

        Returns:
            Dict with counts, averages, top associations, performance metrics
        """
        return {
            'vocab': self.vocab_associator.get_statistics(),
            'dimensions': self.dim_associator.get_statistics(),
            'sequences': self.sequence_learner.get_statistics(),
            'performance': {
                'conversation_count': self.conversation_count,
                'caching_enabled': self.enable_caching,
                # TODO: Add cache hit rates
                # TODO: Add average latencies
            }
        }

    def get_health_summary(self) -> Dict[str, Any]:
        """
        Get system health summary (for dashboard/monitoring)

        Returns:
            Dict with health indicators
        """
        # TODO: Check if components are initialized
        # TODO: Check database connectivity
        # TODO: Check for any error rates
        # TODO: Return health status
        pass
```

---

## File 6: `hebbian_config.py`

**Purpose:** Configuration management

```python
#!/usr/bin/env python3
"""
Hebbian Learning Configuration
Centralized configuration for all Hebbian components
"""

from typing import Dict, Any
import os

# ============================================================================
# DEFAULT CONFIGURATION
# ============================================================================

HEBBIAN_DEFAULT_CONFIG: Dict[str, Dict[str, Any]] = {
    # Vocabulary Associator
    'vocab': {
        'learning_rate': 0.05,
        'competitive_rate': 0.01,
        'decay_rate_per_day': 0.001,
        'confidence_threshold': 0.65,
        'max_association_strength': 1.0,
        'min_association_strength': 0.0,
        'default_strength': 0.5
    },

    # Dimension Associator
    'dimensions': {
        'learning_rate': 0.05,
        'activation_threshold': 0.6,
        'prediction_threshold': 0.65,
        'multi_dim_min_size': 3
    },

    # Sequence Learner
    'sequences': {
        'pattern_threshold': 5,
        'prediction_confidence': 0.7,
        'max_history_length': 10
    },

    # Performance
    'performance': {
        'enable_caching': True,
        'cache_size': 200,
        'cache_refresh_interval': 100,
        'batch_size': 10
    },

    # Safety
    'safety': {
        'max_decay_iterations': 100,
        'strength_cap': 1.0,
        'strength_floor': 0.0
    }
}


class HebbianConfig:
    """Configuration manager for Hebbian learning"""

    def __init__(self, db_path: str = "data/personality_tracking.db"):
        """
        Initialize configuration manager

        Args:
            db_path: Path to database (for loading config)
        """
        self.db_path = db_path
        self.config = HEBBIAN_DEFAULT_CONFIG.copy()

        # TODO: Load configuration from database
        # TODO: Apply environment variable overrides

    def get(self, component: str, parameter: str) -> Any:
        """
        Get configuration value

        Args:
            component: Component name (vocab, dimensions, sequences, etc.)
            parameter: Parameter name

        Returns:
            Configuration value
        """
        # TODO: Implement
        pass

    def set(self, component: str, parameter: str, value: Any) -> None:
        """
        Set configuration value

        Args:
            component: Component name
            parameter: Parameter name
            value: New value
        """
        # TODO: Update in-memory config
        # TODO: Update database
        pass

    def load_from_db(self) -> None:
        """Load configuration from database"""
        # TODO: Implement
        pass

    def save_to_db(self) -> None:
        """Save configuration to database"""
        # TODO: Implement
        pass


# ============================================================================
# ENVIRONMENT VARIABLE OVERRIDES
# ============================================================================

def apply_env_overrides(config: Dict) -> Dict:
    """
    Apply environment variable overrides to configuration

    Environment variables:
    - HEBBIAN_VOCAB_LEARNING_RATE
    - HEBBIAN_DIM_ACTIVATION_THRESHOLD
    - etc.
    """
    # TODO: Implement
    pass
```

---

## Testing Skeletons

```python
#!/usr/bin/env python3
"""
tests/test_hebbian_vocabulary_associator.py
"""

import pytest
from src.personality.hebbian_vocabulary_associator import HebbianVocabularyAssociator


def test_hebbian_strengthening():
    """Test basic Hebbian strengthening rule"""
    # TODO: Create associator
    # TODO: Get initial strength
    # TODO: Observe term in context 5 times
    # TODO: Get final strength
    # TODO: Assert final > initial
    pass


def test_competitive_weakening():
    """Test competitive weakening of non-active contexts"""
    # TODO: Create associator
    # TODO: Strengthen casual context
    # TODO: Check formal context weakened
    pass


def test_should_use_term():
    """Test term appropriateness prediction"""
    # TODO: Create associator
    # TODO: Train with observations
    # TODO: Test predictions
    pass
```

---

**Status:** ✅ Implementation Skeletons Complete
**Next Step:** Create integration plan in `HEBBIAN_INTEGRATION_PLAN.md`

---

*Designed for Penny's Phase 3E Enhancement - October 27, 2025*
