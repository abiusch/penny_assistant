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

# Stopwords to filter from vocabulary observation
STOPWORDS = {
    'a', 'an', 'the', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
    'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
    'should', 'may', 'might', 'must', 'shall', 'can', 'need', 'dare',
    'ought', 'used', 'to', 'of', 'in', 'for', 'on', 'with', 'at', 'by',
    'from', 'as', 'into', 'through', 'during', 'before', 'after', 'above',
    'below', 'between', 'under', 'again', 'further', 'then', 'once',
    'here', 'there', 'when', 'where', 'why', 'how', 'all', 'each', 'few',
    'more', 'most', 'other', 'some', 'such', 'no', 'nor', 'not', 'only',
    'own', 'same', 'so', 'than', 'too', 'very', 's', 't', 'just', 'don',
    'now', 'and', 'but', 'or', 'if', 'because', 'until', 'while', 'about',
    'against', 'both', 'this', 'that', 'these', 'those', 'am', 'i', 'you',
    'he', 'she', 'it', 'we', 'they', 'what', 'which', 'who', 'whom',
    'my', 'your', 'his', 'her', 'its', 'our', 'their', 'me', 'him', 'us',
    'them', 'myself', 'yourself', 'himself', 'herself', 'itself', 'ourselves',
    'themselves', 'any', 'up', 'down', 'out', 'off', 'over', 'also'
}
