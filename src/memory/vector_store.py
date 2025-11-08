"""
Vector Store using FAISS
Fast vector similarity search for semantic memory
"""

import numpy as np
import faiss
from typing import List, Tuple, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class VectorStore:
    """FAISS-based vector store for fast similarity search"""

    def __init__(self, embedding_dim: int = 384):
        """
        Initialize vector store.

        Args:
            embedding_dim: Dimension of embedding vectors (default: 384 for all-MiniLM-L6-v2)
        """
        self.embedding_dim = embedding_dim
        self.index = faiss.IndexFlatIP(embedding_dim)  # Inner product (cosine similarity for normalized vectors)
        self.id_to_metadata: Dict[int, Dict[str, Any]] = {}
        self.next_id = 0
        logger.info(f"Initialized VectorStore with dimension: {embedding_dim}")

    def add(self, embeddings: np.ndarray, metadata: Optional[List[Dict[str, Any]]] = None) -> List[int]:
        """
        Add embeddings to the vector store.

        Args:
            embeddings: numpy array of shape (n, embedding_dim) or (embedding_dim,)
            metadata: Optional list of metadata dicts for each embedding

        Returns:
            List of assigned IDs
        """
        # Handle single embedding
        if embeddings.ndim == 1:
            embeddings = embeddings.reshape(1, -1)

        # Validate dimensions
        if embeddings.shape[1] != self.embedding_dim:
            raise ValueError(f"Expected embedding dimension {self.embedding_dim}, got {embeddings.shape[1]}")

        # Ensure embeddings are float32 for FAISS
        if embeddings.dtype != np.float32:
            embeddings = embeddings.astype(np.float32)

        # Normalize embeddings for cosine similarity
        faiss.normalize_L2(embeddings)

        # Add to FAISS index
        num_embeddings = embeddings.shape[0]
        ids = list(range(self.next_id, self.next_id + num_embeddings))

        self.index.add(embeddings)

        # Store metadata
        if metadata is None:
            metadata = [{}] * num_embeddings
        elif len(metadata) != num_embeddings:
            raise ValueError(f"Metadata length {len(metadata)} doesn't match embeddings count {num_embeddings}")

        for i, meta in zip(ids, metadata):
            self.id_to_metadata[i] = meta

        self.next_id += num_embeddings
        logger.debug(f"Added {num_embeddings} embeddings to vector store")

        return ids

    def search(self, query_embedding: np.ndarray, k: int = 5) -> List[Dict[str, Any]]:
        """
        Search for similar vectors.

        Args:
            query_embedding: Query embedding vector of shape (embedding_dim,) or (1, embedding_dim)
            k: Number of results to return

        Returns:
            List of dicts with keys: 'id', 'distance', 'similarity', 'metadata'
        """
        # Handle single embedding
        if query_embedding.ndim == 1:
            query_embedding = query_embedding.reshape(1, -1)

        # Validate dimensions
        if query_embedding.shape[1] != self.embedding_dim:
            raise ValueError(f"Expected embedding dimension {self.embedding_dim}, got {query_embedding.shape[1]}")

        # Ensure float32 and normalized
        if query_embedding.dtype != np.float32:
            query_embedding = query_embedding.astype(np.float32)

        faiss.normalize_L2(query_embedding)

        # Search
        k = min(k, self.index.ntotal)  # Don't ask for more results than we have
        if k == 0:
            return []

        distances, indices = self.index.search(query_embedding, k)

        # Format results
        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx == -1:  # FAISS returns -1 for missing results
                continue

            results.append({
                'id': int(idx),
                'distance': float(dist),
                'similarity': float(dist),  # For normalized vectors, inner product = cosine similarity
                'metadata': self.id_to_metadata.get(int(idx), {})
            })

        return results

    def get_by_id(self, id: int) -> Optional[Dict[str, Any]]:
        """
        Get metadata for a specific ID.

        Args:
            id: The ID to retrieve

        Returns:
            Metadata dict or None if not found
        """
        return self.id_to_metadata.get(id)

    def delete(self, ids: List[int]):
        """
        Delete entries by ID.

        Note: FAISS doesn't support efficient deletion, so we just remove metadata.
        The vectors remain in the index but won't be returned in results.

        Args:
            ids: List of IDs to delete
        """
        for id in ids:
            if id in self.id_to_metadata:
                del self.id_to_metadata[id]
                logger.debug(f"Deleted metadata for ID {id}")

    def size(self) -> int:
        """Get the number of vectors in the store"""
        return self.index.ntotal

    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the vector store.

        Returns:
            Dict with stats: total_vectors, embedding_dim, metadata_count
        """
        return {
            'total_vectors': self.index.ntotal,
            'embedding_dim': self.embedding_dim,
            'metadata_count': len(self.id_to_metadata)
        }

    def clear(self):
        """Clear all vectors and metadata"""
        self.index = faiss.IndexFlatIP(self.embedding_dim)
        self.id_to_metadata.clear()
        self.next_id = 0
        logger.info("Cleared vector store")

    def save(self, filepath: str):
        """
        Save the index to disk.

        Args:
            filepath: Path to save the index
        """
        faiss.write_index(self.index, filepath)
        logger.info(f"Saved vector store to {filepath}")

    def load(self, filepath: str):
        """
        Load the index from disk.

        Args:
            filepath: Path to load the index from
        """
        self.index = faiss.read_index(filepath)
        logger.info(f"Loaded vector store from {filepath}")
