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
import hashlib
from functools import wraps
from contextlib import ExitStack
from src.memory.storage_io import atomic_write
from src.memory.storage_lock import get_store_lock
from src.memory.errors import MemoryStorageError
from src.memory.consent_manager import consent_guarded, without_emotion

logger = logging.getLogger(__name__)


def _store_guarded(method):
    """Always acquire after the consent guard, including on standalone stores."""
    @wraps(method)
    def call(self, *args, **kwargs):
        with ExitStack() as stack:
            try:
                stack.enter_context(self._store_lock.hold(self.index_path))
            except OSError as error:
                self._storage_failed = True
                raise MemoryStorageError('Cannot coordinate the memory store; restart before continuing') from error
            return method(self, *args, **kwargs)
    return call


def _write_guarded(method):
    @wraps(method)
    @_store_guarded
    def call(self, *args, **kwargs):
        if self._write_depth == 0:
            self._require_current()
        self._write_depth += 1
        try:
            return method(self, *args, **kwargs)
        finally:
            self._write_depth -= 1
    return call


class VectorStore:
    """FAISS-based vector store for fast similarity search with persistent storage"""

    def __init__(
        self,
        embedding_dim: int = 384,
        storage_path: str = "data/embeddings/vector_store",
        consent_manager=None,
    ):
        """
        Initialize vector store with persistent storage.

        Args:
            embedding_dim: Dimension of embedding vectors (default: 384)
            storage_path: Base path for storing index and metadata (without extension)
        """
        self.embedding_dim = int(embedding_dim)
        self.consent_manager = consent_manager
        self.storage_path = Path(storage_path).resolve()
        self.index_path = self.storage_path.with_suffix('.index')
        self.metadata_path = self.storage_path.with_suffix('.pkl')
        self._storage_failed = False
        self._generation = (None, None)
        self._write_depth = 0
        self._store_lock = get_store_lock(self.index_path)

        # Ensure directory exists
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)

        self._initialize()
        logger.info(f"VectorStore initialized: {self.index.ntotal} vectors, dim={self.embedding_dim}")

    @consent_guarded
    @_store_guarded
    def _initialize(self):
        # Check and load under the same lock so another writer cannot create or
        # replace one half between startup's existence check and load.
        if self.index_path.exists() or self.metadata_path.exists():
            logger.info(f"Loading existing vector store from {self.storage_path}")
            self.load()
        else:
            logger.info(f"Creating new vector store at {self.storage_path}")
            self.index = faiss.IndexFlatIP(self.embedding_dim)
            self.id_to_metadata: Dict[int, Dict[str, Any]] = {}
            self.next_id = 0

    def _require_healthy(self):
        if self._storage_failed:
            raise MemoryStorageError('The memory store is unavailable; repair and reload it before continuing')

    def _disk_generation(self):
        """Fingerprint bytes, not counts or mtimes (same-shape edits matter)."""
        result = []
        for path in (self.index_path, self.metadata_path):
            try:
                with path.open('rb') as source:
                    result.append(hashlib.file_digest(source, 'sha256').digest())
            except FileNotFoundError:
                result.append(None)
        return tuple(result)

    def _require_current(self):
        self._require_healthy()
        try:
            current = self._disk_generation()
        except OSError as error:
            self._storage_failed = True
            raise MemoryStorageError('Cannot check the memory store; restart before continuing') from error
        if current != self._generation:
            self._storage_failed = True
            raise MemoryStorageError('The memory store changed on disk; restart before saving more conversations')

    @consent_guarded
    @_write_guarded
    def add(self, embeddings: np.ndarray, metadata: Optional[List[Dict[str, Any]]] = None) -> List[int]:
        """
        Add embeddings to the index with metadata.

        Args:
            embeddings: Embeddings to add (shape: [n, embedding_dim] or [embedding_dim])
            metadata: Optional metadata for each embedding

        Returns:
            List of assigned IDs
        """
        self._require_healthy()
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
        self._require_healthy()
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

    @consent_guarded
    @_write_guarded
    def save(self):
        """Replace each file atomically; failure invalidates this instance.

        These two replacements are not an atomic pair. A failed second write
        leaves an unconfirmed store requiring validation/recovery before reuse.
        """
        self._require_healthy()
        try:
            if self.consent_manager is not None:
                self.id_to_metadata = {key: self.consent_manager.filter_record(record)
                                       for key, record in self.id_to_metadata.items()}
            # Serialize both before changing either existing file.
            index_bytes = faiss.serialize_index(self.index).tobytes()
            metadata_bytes = pickle.dumps({
                'id_to_metadata': self.id_to_metadata,
                'next_id': self.next_id,
                'embedding_dim': self.embedding_dim
            })
            atomic_write(self.index_path, index_bytes)
            atomic_write(self.metadata_path, metadata_bytes)
            self._generation = (hashlib.sha256(index_bytes).digest(),
                                hashlib.sha256(metadata_bytes).digest())

            logger.debug(f"Saved vector store: {self.index.ntotal} vectors")
        except Exception as e:
            self._storage_failed = True
            logger.error('Memory store save failed (%s)', type(e).__name__)
            raise MemoryStorageError('The memory store save is not confirmed; repair and reload before continuing') from e

    @consent_guarded
    @_store_guarded
    def delete_emotional_metadata(self):
        """Atomically redact metadata without rewriting vectors or conversations.

        Read disk directly, including records not in this instance's cache. Unlike
        ordinary save(), this edits only metadata. Errors leave deletion pending.
        """
        def redact(record):
            result = without_emotion(record)
            result['context'] = without_emotion(record.get('context'))
            return result
        before = self._disk_generation()
        was_current = before == self._generation and not self._storage_failed
        self.id_to_metadata = {key: redact(record) for key, record in self.id_to_metadata.items()}
        if not self.metadata_path.exists():
            if self.index_path.exists():
                raise FileNotFoundError('Memory metadata missing; deletion cannot be verified')
            if not was_current:
                self._storage_failed = True
            return
        with self.metadata_path.open('rb') as source:
            payload = pickle.load(source)
        payload['id_to_metadata'] = {key: redact(record)
                                     for key, record in payload['id_to_metadata'].items()}
        metadata_bytes = pickle.dumps(payload)
        atomic_write(self.metadata_path, metadata_bytes)
        if was_current:
            self._generation = (before[0], hashlib.sha256(metadata_bytes).digest())
        else:
            # Deletion uses latest disk metadata, but must never bless an old
            # vector/cache snapshot as current merely because redaction worked.
            self._storage_failed = True

    @consent_guarded
    @_store_guarded
    def load(self):
        """Validate a complete pair before installing it; never reset bad data."""
        try:
            index = faiss.read_index(str(self.index_path))
            with open(self.metadata_path, 'rb') as f:
                data = pickle.load(f)
            metadata = data['id_to_metadata']
            next_id = data['next_id']
            dimension = data.get('embedding_dim', 384)
            if (not isinstance(index, faiss.IndexFlatIP)
                    or index.d != self.embedding_dim or dimension != index.d
                    or type(next_id) is not int or next_id != index.ntotal
                    or not isinstance(metadata, dict)
                    or any(type(key) is not int or not 0 <= key < next_id
                           or not isinstance(record, dict)
                           for key, record in metadata.items())):
                raise ValueError('Inconsistent vector index and metadata')

            generation = self._disk_generation()
            self.index = index
            self.id_to_metadata = metadata
            self.next_id = next_id
            self._generation = generation
            self._storage_failed = False
            logger.info(f"Loaded vector store: {self.index.ntotal} vectors")
        except Exception as e:
            self._storage_failed = True
            logger.error('Memory store load failed (%s)', type(e).__name__)
            raise MemoryStorageError('Cannot load the memory store; restore a complete matching pair before continuing') from e

    @consent_guarded
    @_write_guarded
    def clear(self):
        """Clear all vectors and metadata"""
        self._require_healthy()
        self.index = faiss.IndexFlatIP(int(self.embedding_dim))
        self.id_to_metadata = {}
        self.next_id = 0
        self.save()
        logger.info("Vector store cleared")

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the vector store"""
        self._require_healthy()
        return {
            'total_vectors': self.index.ntotal,
            'embedding_dim': self.embedding_dim,
            'metadata_count': len(self.id_to_metadata),
            'storage_path': str(self.storage_path)
        }

    # Legacy compatibility methods
    def size(self) -> int:
        """Get the number of vectors in the store"""
        self._require_healthy()
        return self.index.ntotal

    def get_by_id(self, id: int) -> Optional[Dict[str, Any]]:
        """Get metadata for a specific ID"""
        self._require_healthy()
        return self.id_to_metadata.get(id)

    @consent_guarded
    @_write_guarded
    def delete(self, ids: List[int]):
        """Delete entries by ID (removes metadata only)"""
        self._require_healthy()
        for id in ids:
            if id in self.id_to_metadata:
                del self.id_to_metadata[id]
                logger.debug(f"Deleted metadata for ID {id}")
        self.save()
