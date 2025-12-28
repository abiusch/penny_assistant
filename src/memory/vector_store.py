"""
Vector Store using FAISS
Fast vector similarity search for semantic memory with persistent storage
"""

import numpy as np
import faiss
from typing import List, Tuple, Dict, Any, Optional
from pathlib import Path
import pickle
import logging

logger = logging.getLogger(__name__)


class VectorStore:
    """FAISS-based vector store for fast similarity search with persistent storage"""

    def __init__(
        self,
        embedding_dim: int = 384,
        storage_path: str = "data/embeddings/vector_store"
    ):
        """
        Initialize vector store with persistent storage.

        Args:
            embedding_dim: Dimension of embedding vectors (default: 384)
            storage_path: Base path for storing index and metadata (without extension)
        """
        self.embedding_dim = int(embedding_dim)
        self.storage_path = Path(storage_path)
        self.index_path = self.storage_path.with_suffix('.index')
        self.metadata_path = self.storage_path.with_suffix('.pkl')

        # Ensure directory exists
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)

        # Try to load existing index
        if self.index_path.exists() and self.metadata_path.exists():
            logger.info(f"Loading existing vector store from {self.storage_path}")
            self.load()
        else:
            logger.info(f"Creating new vector store at {self.storage_path}")
            self.index = faiss.IndexFlatIP(int(embedding_dim))
            self.id_to_metadata: Dict[int, Dict[str, Any]] = {}
            self.next_id = 0

        logger.info(f"VectorStore initialized: {self.index.ntotal} vectors, dim={self.embedding_dim}")

    def add(self, embeddings: np.ndarray, metadata: Optional[List[Dict[str, Any]]] = None) -> List[int]:
        """
        Add embeddings to the index with metadata.

        Args:
            embeddings: Embeddings to add (shape: [n, embedding_dim] or [embedding_dim])
            metadata: Optional metadata for each embedding

        Returns:
            List of assigned IDs
        """
        # Handle single embedding
        if len(embeddings.shape) == 1:
            embeddings = embeddings.reshape(1, -1)

        n = embeddings.shape[0]

        # Validate metadata
        if metadata is None:
            metadata = [{} for _ in range(n)]
        elif len(metadata) != n:
            raise ValueError(f"Metadata length {len(metadata)} doesn't match embeddings {n}")

        # Normalize embeddings for cosine similarity with IndexFlatIP
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        norms[norms == 0] = 1  # Prevent division by zero
        embeddings_normalized = embeddings / norms

        # Add to FAISS index
        self.index.add(embeddings_normalized.astype('float32'))

        # Store metadata
        ids = []
        for i, meta in enumerate(metadata):
            idx = self.next_id
            self.id_to_metadata[idx] = meta
            ids.append(idx)
            self.next_id += 1

        logger.info(f"Added {n} vectors (total: {self.index.ntotal})")

        # Auto-save after adding
        self.save()

        return ids

    def search(
        self,
        query_embedding: np.ndarray,
        k: int = 5
    ) -> List[Tuple[int, float, Dict[str, Any]]]:
        """
        Search for similar vectors.

        Args:
            query_embedding: Query embedding (shape: [embedding_dim])
            k: Number of results to return

        Returns:
            List of (id, similarity_score, metadata) tuples
        """
        if self.index.ntotal == 0:
            logger.warning("Vector store is empty")
            return []

        # Handle single embedding
        if len(query_embedding.shape) == 1:
            query_embedding = query_embedding.reshape(1, -1)

        # Normalize query for cosine similarity
        norm = np.linalg.norm(query_embedding)
        if norm > 0:
            query_embedding = query_embedding / norm

        # Search
        k = min(k, self.index.ntotal)
        distances, indices = self.index.search(query_embedding.astype('float32'), k)

        # Convert to results
        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx == -1:  # FAISS returns -1 for empty slots
                continue

            # Convert distance to similarity (IndexFlatIP returns inner product)
            similarity = float(dist)

            # Get metadata
            metadata = self.id_to_metadata.get(int(idx), {})

            results.append((int(idx), similarity, metadata))

        logger.debug(f"Search found {len(results)} results")
        return results

    def save(self):
        """Save index and metadata to disk"""
        try:
            # Save FAISS index
            faiss.write_index(self.index, str(self.index_path))

            # Save metadata
            with open(self.metadata_path, 'wb') as f:
                pickle.dump({
                    'id_to_metadata': self.id_to_metadata,
                    'next_id': self.next_id,
                    'embedding_dim': self.embedding_dim
                }, f)

            logger.debug(f"Saved vector store: {self.index.ntotal} vectors")
        except Exception as e:
            logger.error(f"Failed to save vector store: {e}")

    def load(self):
        """Load index and metadata from disk"""
        try:
            # Load FAISS index
            self.index = faiss.read_index(str(self.index_path))

            # Load metadata
            with open(self.metadata_path, 'rb') as f:
                data = pickle.load(f)
                self.id_to_metadata = data['id_to_metadata']
                self.next_id = data['next_id']
                self.embedding_dim = data.get('embedding_dim', 384)

            logger.info(f"Loaded vector store: {self.index.ntotal} vectors")
        except Exception as e:
            logger.error(f"Failed to load vector store: {e}")
            # Fall back to empty index
            self.index = faiss.IndexFlatIP(int(self.embedding_dim))
            self.id_to_metadata = {}
            self.next_id = 0

    def clear(self):
        """Clear all vectors and metadata"""
        self.index = faiss.IndexFlatIP(int(self.embedding_dim))
        self.id_to_metadata = {}
        self.next_id = 0
        self.save()
        logger.info("Vector store cleared")

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the vector store"""
        return {
            'total_vectors': self.index.ntotal,
            'embedding_dim': self.embedding_dim,
            'metadata_count': len(self.id_to_metadata),
            'storage_path': str(self.storage_path)
        }

    # Legacy compatibility methods
    def size(self) -> int:
        """Get the number of vectors in the store"""
        return self.index.ntotal

    def get_by_id(self, id: int) -> Optional[Dict[str, Any]]:
        """Get metadata for a specific ID"""
        return self.id_to_metadata.get(id)

    def delete(self, ids: List[int]):
        """Delete entries by ID (removes metadata only)"""
        for id in ids:
            if id in self.id_to_metadata:
                del self.id_to_metadata[id]
                logger.debug(f"Deleted metadata for ID {id}")
        self.save()
