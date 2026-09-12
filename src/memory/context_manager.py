"""
Context Manager for Conversation Tracking
Maintains in-memory conversation context with LRU eviction - NO database persistence

WEEK 7 REFACTOR:
- In-memory only (no database writes)
- Uses deque for O(1) append/popleft operations
- Automatic LRU eviction when window is full
- Semantic Memory handles ALL persistence
"""

from datetime import datetime
from typing import List, Dict, Optional, Any
from collections import deque
from copy import deepcopy
import logging
from src.memory.consent_manager import consent_guarded, without_emotion

logger = logging.getLogger(__name__)


class ContextManager:
    """
    In-memory conversation context manager with LRU eviction.

    This is a CACHE ONLY - no persistence. All long-term storage
    happens in SemanticMemory. This manager provides fast access
    to recent conversation turns for prompt building.

    Performance:
    - O(1) add_turn (deque append)
    - O(1) get recent turns (deque slicing)
    - O(n) topic extraction (n = window size, typically 10)
    """

    def __init__(self, max_window_size: int = 10, *, consent_manager=None):
        """
        Initialize in-memory context manager.

        Args:
            max_window_size: Maximum number of turns to keep in memory (LRU)
        """
        self.max_window_size = max_window_size
        self.consent_manager = consent_manager

        # Use deque with maxlen for automatic LRU eviction
        self._turns: deque = deque(maxlen=max_window_size)

        # Track current topic and emotional state
        self._current_topic: Optional[str] = None
        self._current_emotion: Optional[str] = None

        logger.info(f"✅ ContextManager initialized (in-memory only, window={max_window_size})")

    @consent_guarded
    def add_turn(
        self,
        user_input: str,
        assistant_response: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Add a conversation turn to in-memory cache.

        NO DATABASE WRITES - this is cache only. Semantic Memory handles persistence.

        Args:
            user_input: User's message
            assistant_response: Assistant's response
            metadata: Optional metadata (emotions, timestamps, etc.)
        """
        if self.consent_manager is not None:
            metadata = self.consent_manager.filter_context(metadata)
        turn = {
            'user_input': user_input,
            'assistant_response': assistant_response,
            'timestamp': datetime.now().isoformat(),
            'metadata': metadata or {}
        }

        # Add to deque (automatically evicts oldest if at maxlen)
        self._turns.append(turn)

        # Update emotional state if provided
        if metadata and 'emotion' in metadata:
            self._current_emotion = metadata['emotion']

        # Extract and update topic
        self._update_topic(user_input, assistant_response)

        logger.debug(f"✅ Turn added to cache (window size: {len(self._turns)}/{self.max_window_size})")

    @consent_guarded
    def delete_emotional_metadata(self):
        for turn in self._turns:
            turn['metadata'] = without_emotion(turn.get('metadata'))
        self._current_emotion = None

    def _apply_consent(self):
        if self.consent_manager is None:
            return list(self._turns)
        for turn in self._turns:
            if self.consent_manager.was_deleted(turn.get('timestamp')):
                turn['metadata'] = without_emotion(turn.get('metadata'))
        # Opt-out hides retained history; only a deletion cutoff purges the cache.
        turns = deepcopy(list(self._turns))
        if not self.consent_manager.is_tracking_enabled():
            for turn in turns:
                turn['metadata'] = without_emotion(turn.get('metadata'))
        self._current_emotion = next((turn['metadata']['emotion'] for turn in reversed(turns)
                                     if 'emotion' in turn['metadata']), None)
        return turns

    @consent_guarded
    def get_context_window(self, max_turns: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get recent conversation turns from in-memory cache.

        Args:
            max_turns: Maximum number of turns to return (defaults to all in cache)

        Returns:
            List of recent conversation turns (most recent last)
        """
        turns = self._apply_consent()
        if max_turns is None:
            return turns

        # Get last N turns (deque slicing)
        n = min(max_turns, len(turns))
        return turns[-n:] if n > 0 else []

    def get_current_topic(self) -> Optional[str]:
        """
        Get the current conversation topic.

        Returns:
            Current topic string or None
        """
        return self._current_topic

    @consent_guarded
    def summarize_context(self) -> str:
        """
        Create a summary of the current in-memory context.

        Returns:
            Human-readable context summary
        """
        self._apply_consent()
        if not self._turns:
            return "No conversation history in cache."

        num_turns = len(self._turns)
        topic = self._current_topic or "general conversation"
        emotion = self._current_emotion or "neutral"

        summary = f"Conversation with {num_turns} turn(s) about {topic}. "
        summary += f"Current emotional tone: {emotion}."

        return summary

    def clear_context(self) -> None:
        """Clear in-memory cache (no database operations)"""
        self._turns.clear()
        self._current_topic = None
        self._current_emotion = None
        logger.info("✅ Context cache cleared")

    def get_context_for_prompt(
        self,
        max_turns: Optional[int] = None,
        include_metadata: bool = False
    ) -> str:
        """
        Format in-memory context for LLM prompt injection.

        Args:
            max_turns: Maximum turns to include
            include_metadata: Whether to include metadata in output

        Returns:
            Formatted context string for prompt
        """
        turns = self.get_context_window(max_turns)

        if not turns:
            return ""

        lines = ["Previous conversation:"]

        for i, turn in enumerate(turns, 1):
            user_msg = turn['user_input']
            assistant_msg = turn['assistant_response']

            lines.append(f"\nTurn {i}:")
            lines.append(f"User: {user_msg}")
            lines.append(f"Assistant: {assistant_msg}")

            if include_metadata and turn.get('metadata'):
                metadata = turn['metadata']
                if 'emotion' in metadata:
                    lines.append(f"(Emotion: {metadata['emotion']})")

        # Add current context summary
        if self._current_topic:
            lines.append(f"\nCurrent topic: {self._current_topic}")

        return "\n".join(lines)

    def _update_topic(self, user_input: str, assistant_response: str) -> None:
        """
        Extract and update current topic from conversation.

        Args:
            user_input: User's message
            assistant_response: Assistant's response
        """
        # Simple topic extraction using common question patterns
        combined_text = (user_input + " " + assistant_response).lower()

        # Topic keywords to look for
        topics = {
            'programming': ['python', 'javascript', 'code', 'programming', 'software', 'function', 'class'],
            'ai': ['ai', 'machine learning', 'neural network', 'deep learning', 'artificial intelligence'],
            'weather': ['weather', 'temperature', 'rain', 'sunny', 'forecast'],
            'food': ['food', 'recipe', 'cooking', 'eat', 'meal', 'dinner'],
            'health': ['health', 'exercise', 'fitness', 'medical', 'doctor'],
            'technology': ['technology', 'tech', 'computer', 'internet', 'device'],
            'science': ['science', 'research', 'study', 'experiment', 'theory'],
            'education': ['learn', 'study', 'education', 'school', 'teach'],
        }

        # Count topic keyword matches
        topic_scores = {}
        for topic, keywords in topics.items():
            score = sum(1 for keyword in keywords if keyword in combined_text)
            if score > 0:
                topic_scores[topic] = score

        # Update to highest scoring topic
        if topic_scores:
            self._current_topic = max(topic_scores, key=topic_scores.get)
        else:
            # Keep previous topic or set to general
            if self._current_topic is None:
                self._current_topic = "general conversation"

    @consent_guarded
    def get_emotional_trajectory(self) -> List[str]:
        """
        Get the emotional trajectory over cached conversation.

        Returns:
            List of emotions in chronological order
        """
        turns = self._apply_consent()
        emotions = []
        for turn in turns:
            if turn.get('metadata') and 'emotion' in turn['metadata']:
                emotions.append(turn['metadata']['emotion'])
        return emotions

    @consent_guarded
    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the in-memory context cache.

        Returns:
            Dictionary with context statistics
        """
        self._apply_consent()
        return {
            'window_size': len(self._turns),
            'max_window_size': self.max_window_size,
            'current_topic': self._current_topic,
            'emotional_state': self._current_emotion,
            'cache_type': 'in-memory (no persistence)',
            'timestamp': self._turns[-1]['timestamp'] if self._turns else None
        }
