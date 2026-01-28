"""
Hebbian Learning Layer for Penny
Week 9-10 of Phase 3E

Components:
- HebbianVocabularyAssociator: Learns vocabulary-context associations
- HebbianDimensionAssociator: Learns personality dimension co-activations
- HebbianSequenceLearner: Learns conversation flow patterns
- HebbianLearningManager: Orchestrates all components
"""

from .hebbian_types import (
    ContextType,
    ConversationState,
    VocabularyAssociation,
    VocabularyObservation,
    DimensionCoactivation,
    MultiDimensionalPattern,
    NegativeCorrelation,
    DimensionPrediction,
    StateTransition,
    StateSequence,
    PatternTemplate,
    SkipOpportunity,
    AnticipatedResponse,
    CONTEXT_DEFINITIONS,
    PERSONALITY_DIMENSIONS,
    DEFAULT_LEARNING_RATE,
    DEFAULT_COMPETITIVE_RATE,
    DEFAULT_DECAY_RATE_PER_DAY,
    DEFAULT_CONFIDENCE_THRESHOLD,
    DEFAULT_ACTIVATION_THRESHOLD,
    DEFAULT_PATTERN_THRESHOLD
)

from .hebbian_config import HebbianConfig, HEBBIAN_DEFAULT_CONFIG

from .hebbian_vocabulary_associator import HebbianVocabularyAssociator
from .hebbian_dimension_associator import HebbianDimensionAssociator
from .hebbian_sequence_learner import HebbianSequenceLearner

__all__ = [
    # Types
    'ContextType',
    'ConversationState',
    'VocabularyAssociation',
    'VocabularyObservation',
    'DimensionCoactivation',
    'MultiDimensionalPattern',
    'NegativeCorrelation',
    'DimensionPrediction',
    'StateTransition',
    'StateSequence',
    'PatternTemplate',
    'SkipOpportunity',
    'AnticipatedResponse',
    # Constants
    'CONTEXT_DEFINITIONS',
    'PERSONALITY_DIMENSIONS',
    'DEFAULT_LEARNING_RATE',
    'DEFAULT_COMPETITIVE_RATE',
    'DEFAULT_DECAY_RATE_PER_DAY',
    'DEFAULT_CONFIDENCE_THRESHOLD',
    'DEFAULT_ACTIVATION_THRESHOLD',
    'DEFAULT_PATTERN_THRESHOLD',
    # Config
    'HebbianConfig',
    'HEBBIAN_DEFAULT_CONFIG',
    # Components
    'HebbianVocabularyAssociator',
    'HebbianDimensionAssociator',
    'HebbianSequenceLearner',
]
