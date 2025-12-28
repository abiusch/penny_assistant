"""
Semantic Memory System - WEEK 7 REFACTOR
NOW the ONLY persistent store (no base_memory redundancy)

CHANGES:
- Integrated encryption for sensitive fields (emotions, sentiment)
- Stores ALL conversation metadata (was split across 3 systems)
- NO dependency on base_memory (removed)
- Automatic persistence via FAISS save/load
"""

import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

from src.memory.embedding_generator import get_embedding_generator
from src.memory.vector_store import VectorStore
from src.security.encryption import get_encryption

logger = logging.getLogger(__name__)


class SemanticMemory:
    """
    Semantic memory with vector search and encryption.

    WEEK 7: This is now the ONLY persistent store.
    - Context Manager = in-memory cache only
    - Base Memory = REMOVED (redundant)
    - Semantic Memory = single source of truth for all conversations

    Features:
    - Vector similarity search (FAISS)
    - Encrypted sensitive fields (emotions, sentiment)
    - Stores ALL metadata (research_used, financial_topic, tools_used, etc.)
    - Automatic persistence to disk
    """

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
            storage_path=storage_path  # CROSS-MODAL FIX: Pass storage path
        )
        self.turn_id_to_vector_id: Dict[str, int] = {}

        # WEEK 7: Encryption for sensitive data (GDPR Article 9)
        self.encrypt_sensitive = encrypt_sensitive
        if encrypt_sensitive:
            self.encryption = get_encryption()
            logger.info("🔐 Semantic Memory initialized with encryption enabled")
        else:
            self.encryption = None
            logger.info("⚠️  Semantic Memory initialized WITHOUT encryption")

        logger.info(f"✅ SemanticMemory initialized (SOLE persistent store) at {storage_path}")

    def add_conversation_turn(
        self,
        user_input: str,
        assistant_response: str,
        turn_id: Optional[str] = None,
        timestamp: Optional[datetime] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Add a conversation turn to semantic memory (ONLY persistent store).

        WEEK 7: Now stores ALL metadata (not split with base_memory)
        - Encrypts sensitive fields (emotion, sentiment) before storage
        - Stores research_used, financial_topic, tools_used, ab_test_group, etc.

        Args:
            user_input: User's message
            assistant_response: Assistant's response
            turn_id: Optional unique ID for this turn
            timestamp: Optional timestamp
            context: Full metadata dict including:
                - emotion: str (encrypted)
                - emotion_confidence: float
                - sentiment: str (encrypted)
                - sentiment_score: float (encrypted)
                - research_used: bool
                - financial_topic: bool
                - tools_used: List[str]
                - ab_test_group: str
                - user_id: str (future multi-user)

        Returns:
            turn_id for this conversation turn
        """
        if turn_id is None:
            turn_id = str(uuid.uuid4())

        if timestamp is None:
            timestamp = datetime.now()

        # Create combined text for embedding (user + assistant for better context)
        combined_text = f"User: {user_input}\nAssistant: {assistant_response}"

        # Generate embedding
        embedding = self.embedding_generator.encode(combined_text)

        # Create base metadata
        metadata = {
            'turn_id': turn_id,
            'user_input': user_input,
            'assistant_response': assistant_response,
            'timestamp': timestamp.isoformat(),
            'combined_text': combined_text
        }

        # Add context with encryption for sensitive fields
        if context:
            # Encrypt sensitive fields (GDPR Article 9 compliance)
            encrypted_context = context.copy()

            if self.encrypt_sensitive and self.encryption:
                # Fields to encrypt: emotion, sentiment, sentiment_score
                sensitive_fields = ['emotion', 'sentiment', 'sentiment_score']

                for field in sensitive_fields:
                    if field in encrypted_context and encrypted_context[field] is not None:
                        # Convert to string and encrypt
                        encrypted_context[field] = self.encryption.encrypt(
                            str(encrypted_context[field])
                        )

            metadata['context'] = encrypted_context

        # Add to vector store
        vector_ids = self.vector_store.add(embedding, metadata=[metadata])
        self.turn_id_to_vector_id[turn_id] = vector_ids[0]

        logger.debug(f"✅ Turn {turn_id} added (encrypted={'yes' if self.encrypt_sensitive else 'no'})")
        return turn_id

    def semantic_search(
        self,
        query: str,
        k: int = 5,
        min_similarity: float = 0.0
    ) -> List[Dict[str, Any]]:
        """
        Search for semantically similar conversations.

        WEEK 7: Automatically decrypts sensitive fields before returning results.

        Args:
            query: Search query
            k: Number of results to return
            min_similarity: Minimum similarity threshold (0-1)

        Returns:
            List of matching conversations with similarity scores and decrypted metadata
        """
        # Generate query embedding
        query_embedding = self.embedding_generator.encode(query)

        # Search vector store
        results = self.vector_store.search(query_embedding, k=k)

        # Filter by minimum similarity and format results
        filtered_results = []
        for result in results:
            # CROSS-MODAL FIX: VectorStore now returns tuples (id, similarity, metadata)
            if isinstance(result, tuple):
                vector_id, similarity, metadata = result
            else:
                # Legacy dict format compatibility
                vector_id = result['id']
                similarity = result['similarity']
                metadata = result['metadata']

            if similarity >= min_similarity:

                # Decrypt sensitive fields if encryption is enabled
                context = metadata.get('context', {})
                if self.encrypt_sensitive and self.encryption and context:
                    decrypted_context = context.copy()

                    # Decrypt sensitive fields
                    sensitive_fields = ['emotion', 'sentiment', 'sentiment_score']
                    for field in sensitive_fields:
                        if field in decrypted_context and decrypted_context[field]:
                            try:
                                decrypted_context[field] = self.encryption.decrypt(
                                    decrypted_context[field]
                                )
                                # Convert back to proper type
                                if field == 'sentiment_score':
                                    decrypted_context[field] = float(decrypted_context[field])
                            except Exception as e:
                                logger.warning(f"Failed to decrypt {field}: {e}")

                    context = decrypted_context

                # Build result with decrypted data
                filtered_results.append({
                    'turn_id': metadata.get('turn_id'),
                    'user_input': metadata.get('user_input'),
                    'assistant_response': metadata.get('assistant_response'),
                    'timestamp': metadata.get('timestamp'),
                    'similarity': similarity,  # Use unpacked similarity
                    'context': context  # Now includes decrypted sensitive fields
                })

        return filtered_results

    def get_relevant_context(
        self,
        query: str,
        max_turns: int = 3,
        min_similarity: float = 0.5
    ) -> str:
        """
        Get relevant conversation context for a query.

        Args:
            query: Current query/question
            max_turns: Maximum number of past turns to include
            min_similarity: Minimum similarity threshold

        Returns:
            Formatted context string
        """
        # Search for relevant conversations
        results = self.semantic_search(
            query,
            k=max_turns,
            min_similarity=min_similarity
        )

        if not results:
            return ""

        # Format as context
        context_parts = []
        for i, result in enumerate(results, 1):
            context_parts.append(
                f"[Relevant Context {i}]\n"
                f"User: {result['user_input']}\n"
                f"Assistant: {result['assistant_response']}\n"
            )

        return "\n".join(context_parts)

    def find_similar_conversations(
        self,
        turn_id: str,
        k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Find conversations similar to a specific turn.

        Args:
            turn_id: ID of the turn to find similar conversations for
            k: Number of similar conversations to return

        Returns:
            List of similar conversations
        """
        # Get the vector ID for this turn
        vector_id = self.turn_id_to_vector_id.get(turn_id)
        if vector_id is None:
            logger.warning(f"Turn ID {turn_id} not found in semantic memory")
            return []

        # Get the metadata (includes the embedding text)
        metadata = self.vector_store.get_by_id(vector_id)
        if not metadata:
            return []

        # Use the combined text to search
        combined_text = metadata.get('combined_text', '')
        return self.semantic_search(combined_text, k=k + 1)[1:]  # Exclude the query itself

    def get_conversation_by_id(self, turn_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific conversation turn by ID.

        Args:
            turn_id: The turn ID to retrieve

        Returns:
            Conversation dict or None if not found
        """
        vector_id = self.turn_id_to_vector_id.get(turn_id)
        if vector_id is None:
            return None

        metadata = self.vector_store.get_by_id(vector_id)
        if not metadata:
            return None

        return {
            'turn_id': metadata.get('turn_id'),
            'user_input': metadata.get('user_input'),
            'assistant_response': metadata.get('assistant_response'),
            'timestamp': metadata.get('timestamp')
        }

    def delete_conversation(self, turn_id: str):
        """
        Delete a conversation turn from semantic memory.

        Args:
            turn_id: The turn ID to delete
        """
        vector_id = self.turn_id_to_vector_id.get(turn_id)
        if vector_id is not None:
            self.vector_store.delete([vector_id])
            del self.turn_id_to_vector_id[turn_id]
            logger.debug(f"Deleted conversation turn {turn_id}")

    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about semantic memory.

        Returns:
            Dict with stats about the memory system
        """
        vector_stats = self.vector_store.get_stats()
        return {
            'total_conversations': len(self.turn_id_to_vector_id),  # Use actual count
            'vector_store': vector_stats,
            'embedding_dim': self.embedding_generator.embedding_dim,
            'encryption_enabled': self.encrypt_sensitive
        }

    def clear(self):
        """Clear all semantic memory"""
        self.vector_store.clear()
        self.turn_id_to_vector_id.clear()
        logger.info("Cleared semantic memory")

    def save(self, filepath: str):
        """
        Save semantic memory to disk.

        Args:
            filepath: Path to save the vector store
        """
        self.vector_store.save(filepath)
        logger.info(f"Saved semantic memory to {filepath}")

    def load(self, filepath: str):
        """
        Load semantic memory from disk.

        Args:
            filepath: Path to load the vector store from
        """
        self.vector_store.load(filepath)
        # Rebuild turn_id mapping from metadata
        self.turn_id_to_vector_id.clear()
        for vector_id, metadata in self.vector_store.id_to_metadata.items():
            turn_id = metadata.get('turn_id')
            if turn_id:
                self.turn_id_to_vector_id[turn_id] = vector_id
        logger.info(f"Loaded semantic memory from {filepath}")
