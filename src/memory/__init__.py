"""
Semantic Memory Module
Provides embeddings, vector search, semantic memory, context tracking, and emotion detection
"""

from src.memory.embedding_generator import EmbeddingGenerator, get_embedding_generator
from src.memory.vector_store import VectorStore
from src.memory.semantic_memory import SemanticMemory
from src.memory.context_manager import ContextManager, ConversationContext
from src.memory.emotion_detector import EmotionDetector, EmotionResult

__all__ = [
    'EmbeddingGenerator',
    'get_embedding_generator',
    'VectorStore',
    'SemanticMemory',
    'ContextManager',
    'ConversationContext',
    'EmotionDetector',
    'EmotionResult',
]
