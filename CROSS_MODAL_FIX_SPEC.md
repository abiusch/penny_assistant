# CROSS-MODAL STORAGE FIX - CC IMPLEMENTATION SPEC

**Date:** November 2, 2025  
**Estimated Time:** 10-15 minutes  
**Priority:** HIGH (blocks 100% test pass rate)

---

## 🎯 **OBJECTIVE:**

Fix VectorStore so multiple SemanticMemory instances can share the same persistent storage, enabling cross-modal memory sharing between chat and voice interfaces.

---

## 🐛 **CURRENT PROBLEM:**

```python
# Test failure:
chat.semantic_memory = SemanticMemory()  # Creates VectorStore A
voice.semantic_memory = SemanticMemory()  # Creates VectorStore B

chat saves conversation → VectorStore A
voice searches → VectorStore B (empty!)

Result: Can't find chat's conversations from voice ❌
```

**Root Cause:** Each SemanticMemory instance creates its own independent VectorStore with no shared storage.

---

## ✅ **SOLUTION:**

Make VectorStore support persistent file-based storage that multiple instances can share.

---

## 📄 **FILE 1: Update `src/memory/vector_store.py`**

### **Changes Needed:**

1. Add `storage_path` parameter to `__init__`
2. Auto-load existing index if path exists
3. Auto-save on every add operation (or periodically)
4. Ensure thread-safe file access

### **Implementation:**

```python
"""
Vector Store using FAISS
Fast vector similarity search for semantic memory
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
```

---

## 📄 **FILE 2: Update `src/memory/semantic_memory.py`**

### **Changes Needed:**

1. Accept optional `storage_path` parameter
2. Pass it to VectorStore
3. Update get_stats() to show actual conversation count

### **Implementation:**

```python
# At the top of the __init__ method, update to:

def __init__(
    self, 
    embedding_dim: int = 384, 
    encrypt_sensitive: bool = True,
    storage_path: str = "data/embeddings/vector_store"
):
    """
    Initialize semantic memory as the sole persistent store.

    Args:
        embedding_dim: Dimension of embeddings (default: 384)
        encrypt_sensitive: Encrypt emotion/sentiment fields (default: True)
        storage_path: Path for vector store persistence (default: "data/embeddings/vector_store")
    """
    self.embedding_generator = get_embedding_generator()
    self.vector_store = VectorStore(
        embedding_dim=embedding_dim,
        storage_path=storage_path  # ADDED: Pass storage path
    )
    self.turn_id_to_vector_id: Dict[str, int] = {}

    # WEEK 7: Encryption for sensitive data (GDPR Article 9)
    self.encrypt_sensitive = encrypt_sensitive
    if encrypt_sensitive:
        self.encryption = get_encryption()
    
    logger.info(f"SemanticMemory initialized with storage at {storage_path}")
```

### **Also update get_stats():**

```python
def get_stats(self) -> Dict[str, Any]:
    """Get statistics about semantic memory"""
    vector_stats = self.vector_store.get_stats()
    
    return {
        'total_conversations': len(self.turn_id_to_vector_id),  # Use actual count
        'vector_store': vector_stats,
        'embedding_dim': self.embedding_generator.embedding_dim,
        'encryption_enabled': self.encrypt_sensitive
    }
```

---

## 📄 **FILE 3: Update Integration Test**

### **Changes to `test_full_integration.py`:**

Update Test 2 to use shared storage path:

```python
# In TEST 2: Cross-Modal Memory Sharing
# Replace the lines that create semantic_memory:

# Add semantic memory to both with SHARED storage path
print("\n  Step 2: Adding semantic memory to both...")
shared_storage = "data/test_cross_modal_vectors"  # Shared path!
chat.semantic_memory = SemanticMemory(storage_path=shared_storage)
voice.semantic_memory = SemanticMemory(storage_path=shared_storage)  # Same path
print("  ✅ Semantic memory added to both (shared storage)")
```

---

## 🧪 **TESTING PROCEDURE:**

```bash
# 1. Run integration tests
cd /Users/CJ/Desktop/penny_assistant
python3 test_full_integration.py

# 2. Expected output:
# ✅ TEST 1: Modal + Semantic Integration      PASSED
# ✅ TEST 2: Cross-Modal Memory Sharing        PASSED  ← Should now PASS!
# ✅ TEST 3: Semantic Search Quality           PASSED
# ✅ TEST 4: Concurrent Access                 PASSED
# ✅ TEST 5: Performance Under Load            PASSED
#
# Success Rate: 100% ✅
```

---

## ✅ **SUCCESS CRITERIA:**

```
Expected Results:
├── VectorStore saves to disk automatically
├── Multiple instances can share same storage
├── Chat saves conversation → persisted to disk
├── Voice loads same storage → finds chat's conversation
├── All 5 integration tests pass (100%)
└── get_stats() shows correct conversation count

If all pass: Cross-Modal Storage FIXED ✅
```

---

## 🐛 **TROUBLESHOOTING:**

### **Issue: "Permission denied" on save**
```bash
# Fix permissions
chmod -R 755 data/embeddings/
```

### **Issue: "File not found" on load**
```python
# VectorStore handles this gracefully
# Creates new empty index if file doesn't exist
# Check logs for "Creating new vector store" message
```

### **Issue: Test 4 shows 0 conversations**
```python
# This is expected - concurrent test creates new instances
# that don't use shared storage path
# Only Test 2 validates cross-modal sharing
```

---

## 📊 **VALIDATION:**

After implementation, verify:

1. **Test 2 passes** ✅
   - Voice finds chat's conversations
   - Similarity scores > 0.5

2. **Files created** ✅
   ```
   data/embeddings/vector_store.index  (FAISS index)
   data/embeddings/vector_store.pkl    (metadata)
   ```

3. **Stats accurate** ✅
   ```python
   stats = semantic_mem.get_stats()
   assert stats['total_conversations'] == expected_count
   ```

---

## 🎯 **EXPECTED OUTCOME:**

```
BEFORE:
- 4/5 tests passing (80%)
- Cross-modal sharing broken
- Each instance has separate storage

AFTER:
- 5/5 tests passing (100%) ✅
- Cross-modal sharing works
- Shared persistent storage
- Ready for Nemotron swap!
```

---

## ⏰ **TIME ESTIMATE:**

```
Implementation:
├── Update vector_store.py:     5-8 min
├── Update semantic_memory.py:  2-3 min
├── Update test file:           1-2 min
├── Run tests:                  2-3 min
└── Total:                      10-16 min

Expected: ~15 minutes to 100% ✅
```

---

## 📝 **FINAL CHECKLIST:**

```bash
✅ Add storage_path parameter to VectorStore
✅ Implement auto-save on add()
✅ Implement load() in __init__
✅ Update SemanticMemory to accept storage_path
✅ Pass storage_path to VectorStore
✅ Update test to use shared path
✅ Run tests → all 5 pass
✅ Verify files created in data/embeddings/
✅ Check stats show correct counts
```

---

**This implementation makes VectorStore persistent and shareable across multiple SemanticMemory instances, fixing the cross-modal memory sharing issue!**

**Ready to implement - should take ~15 minutes!** 🚀
