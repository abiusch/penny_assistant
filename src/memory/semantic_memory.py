"""
Semantic Memory System
Combines embeddings and vector store for intelligent conversation memory
"""

import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

from src.memory.embedding_generator import get_embedding_generator
from src.memory.vector_store import VectorStore

logger = logging.getLogger(__name__)


class SemanticMemory:
    """Semantic memory with vector search capabilities"""

    def __init__(self, base_memory=None, embedding_dim: int = 384):
        """
        Initialize semantic memory.

        Args:
            base_memory: Optional MemoryManager instance for integration
            embedding_dim: Dimension of embeddings (default: 384)
        """
        self.base_memory = base_memory
        self.embedding_generator = get_embedding_generator()
        self.vector_store = VectorStore(embedding_dim=embedding_dim)
        self.turn_id_to_vector_id: Dict[str, int] = {}
        logger.info("Initialized SemanticMemory")

    def add_conversation_turn(
        self,
        user_input: str,
        assistant_response: str,
        turn_id: Optional[str] = None,
        timestamp: Optional[datetime] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Add a conversation turn to semantic memory.

        Args:
            user_input: User's message
            assistant_response: Assistant's response
            turn_id: Optional unique ID for this turn
            timestamp: Optional timestamp
            context: Optional additional context metadata

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

        # Create metadata
        metadata = {
            'turn_id': turn_id,
            'user_input': user_input,
            'assistant_response': assistant_response,
            'timestamp': timestamp.isoformat(),
            'combined_text': combined_text
        }

        # Add optional context to metadata
        if context:
            metadata['context'] = context

        # Add to vector store
        vector_ids = self.vector_store.add(embedding, metadata=[metadata])
        self.turn_id_to_vector_id[turn_id] = vector_ids[0]

        logger.debug(f"Added conversation turn {turn_id} to semantic memory")
        return turn_id

    def semantic_search(
        self,
        query: str,
        k: int = 5,
        min_similarity: float = 0.0
    ) -> List[Dict[str, Any]]:
        """
        Search for semantically similar conversations.

        Args:
            query: Search query
            k: Number of results to return
            min_similarity: Minimum similarity threshold (0-1)

        Returns:
            List of matching conversations with similarity scores
        """
        # Generate query embedding
        query_embedding = self.embedding_generator.encode(query)

        # Search vector store
        results = self.vector_store.search(query_embedding, k=k)

        # Filter by minimum similarity and format results
        filtered_results = []
        for result in results:
            if result['similarity'] >= min_similarity:
                metadata = result['metadata']
                filtered_results.append({
                    'turn_id': metadata.get('turn_id'),
                    'user_input': metadata.get('user_input'),
                    'assistant_response': metadata.get('assistant_response'),
                    'timestamp': metadata.get('timestamp'),
                    'similarity': result['similarity']
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
            'total_conversations': len(self.turn_id_to_vector_id),
            'vector_store_size': vector_stats['total_vectors'],
            'embedding_dim': vector_stats['embedding_dim'],
            'model_name': self.embedding_generator.get_model_name()
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
