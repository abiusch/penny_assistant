"""
Embedding Generator for Semantic Search
Generates 384-dimensional embeddings using sentence-transformers
"""

import numpy as np
from sentence_transformers import SentenceTransformer
from typing import List, Union
import logging

logger = logging.getLogger(__name__)


class EmbeddingGenerator:
    """Generate embeddings for text using sentence-transformers"""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize embedding generator.

        Args:
            model_name: Name of the sentence-transformers model to use
                       Default: all-MiniLM-L6-v2 (384 dimensions, fast)
        """
        self.model_name = model_name
        self.model = None
        self.embedding_dim = 384  # Dimension for all-MiniLM-L6-v2
        logger.info(f"Initializing EmbeddingGenerator with model: {model_name}")

    def _load_model(self):
        """Lazy-load the model on first use"""
        if self.model is None:
            logger.info(f"Loading sentence-transformer model: {self.model_name}")
            self.model = SentenceTransformer(self.model_name)
            logger.info("Model loaded successfully")

    def encode(self, text: Union[str, List[str]], normalize: bool = True) -> np.ndarray:
        """
        Generate embeddings for text.

        Args:
            text: Single string or list of strings to encode
            normalize: Whether to normalize embeddings to unit length

        Returns:
            numpy array of shape (embedding_dim,) for single text
            or (n, embedding_dim) for list of texts
        """
        self._load_model()

        # Convert single string to list for consistent processing
        is_single = isinstance(text, str)
        if is_single:
            text = [text]

        # Generate embeddings
        embeddings = self.model.encode(
            text,
            normalize_embeddings=normalize,
            show_progress_bar=False
        )

        # Return single embedding if input was single string
        if is_single:
            return embeddings[0]

        return embeddings

    def cosine_similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """
        Calculate cosine similarity between two embeddings.

        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector

        Returns:
            Cosine similarity score (0-1, higher is more similar)
        """
        # Normalize embeddings
        norm1 = np.linalg.norm(embedding1)
        norm2 = np.linalg.norm(embedding2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        # Calculate cosine similarity
        similarity = np.dot(embedding1, embedding2) / (norm1 * norm2)

        return float(similarity)

    def get_embedding_dim(self) -> int:
        """Get the dimension of embeddings"""
        return self.embedding_dim

    def get_model_name(self) -> str:
        """Get the name of the current model"""
        return self.model_name


# Singleton instance for efficient reuse
_embedding_generator = None


def get_embedding_generator(model_name: str = "all-MiniLM-L6-v2") -> EmbeddingGenerator:
    """
    Get the singleton embedding generator instance.

    Args:
        model_name: Name of the model to use

    Returns:
        EmbeddingGenerator instance
    """
    global _embedding_generator

    if _embedding_generator is None or _embedding_generator.model_name != model_name:
        _embedding_generator = EmbeddingGenerator(model_name)

    return _embedding_generator
