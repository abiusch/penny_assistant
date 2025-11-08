"""
Context Manager for Conversation Tracking
Maintains conversation context windows and topic continuity
"""

from datetime import datetime
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)


@dataclass
class ConversationContext:
    """Represents current conversation state"""
    current_topic: Optional[str] = None
    context_window: List[Dict[str, Any]] = field(default_factory=list)
    emotional_state: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'current_topic': self.current_topic,
            'context_window': self.context_window,
            'emotional_state': self.emotional_state,
            'timestamp': self.timestamp.isoformat()
        }


class ContextManager:
    """Manages conversation context across turns"""

    def __init__(self, max_window_size: int = 10):
        """
        Initialize context manager.

        Args:
            max_window_size: Maximum number of turns to keep in context window
        """
        self.max_window_size = max_window_size
        self.context = ConversationContext()
        self._topic_keywords: Dict[str, List[str]] = {}
        logger.info(f"Initialized ContextManager with window size: {max_window_size}")

    def add_turn(
        self,
        user_input: str,
        assistant_response: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Add a conversation turn to context.

        Args:
            user_input: User's message
            assistant_response: Assistant's response
            metadata: Optional metadata (emotions, timestamps, etc.)
        """
        turn = {
            'user_input': user_input,
            'assistant_response': assistant_response,
            'timestamp': datetime.now().isoformat(),
            'metadata': metadata or {}
        }

        # Add to context window
        self.context.context_window.append(turn)

        # Maintain window size limit
        if len(self.context.context_window) > self.max_window_size:
            self.context.context_window.pop(0)

        # Update emotional state if provided
        if metadata and 'emotion' in metadata:
            self.context.emotional_state = metadata['emotion']

        # Extract and update topic
        self._update_topic(user_input, assistant_response)

        # Update timestamp
        self.context.timestamp = datetime.now()

        logger.debug(f"Added turn to context. Window size: {len(self.context.context_window)}")

    def get_context_window(self, max_turns: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get recent conversation turns.

        Args:
            max_turns: Maximum number of turns to return (defaults to window size)

        Returns:
            List of recent conversation turns
        """
        if max_turns is None:
            return self.context.context_window.copy()

        return self.context.context_window[-max_turns:] if max_turns > 0 else []

    def get_current_topic(self) -> Optional[str]:
        """
        Get the current conversation topic.

        Returns:
            Current topic string or None
        """
        return self.context.current_topic

    def summarize_context(self) -> str:
        """
        Create a summary of the current context.

        Returns:
            Human-readable context summary
        """
        if not self.context.context_window:
            return "No conversation history."

        num_turns = len(self.context.context_window)
        topic = self.context.current_topic or "general conversation"
        emotion = self.context.emotional_state or "neutral"

        summary = f"Conversation with {num_turns} turn(s) about {topic}. "
        summary += f"Current emotional tone: {emotion}."

        return summary

    def clear_context(self) -> None:
        """Clear all context and reset to initial state"""
        self.context = ConversationContext()
        logger.info("Cleared conversation context")

    def get_context_for_prompt(
        self,
        max_turns: Optional[int] = None,
        include_metadata: bool = False
    ) -> str:
        """
        Format context for LLM prompt injection.

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
        if self.context.current_topic:
            lines.append(f"\nCurrent topic: {self.context.current_topic}")

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
            self.context.current_topic = max(topic_scores, key=topic_scores.get)
        else:
            # Keep previous topic or set to general
            if self.context.current_topic is None:
                self.context.current_topic = "general conversation"

    def get_emotional_trajectory(self) -> List[str]:
        """
        Get the emotional trajectory over conversation.

        Returns:
            List of emotions in chronological order
        """
        emotions = []
        for turn in self.context.context_window:
            if turn.get('metadata') and 'emotion' in turn['metadata']:
                emotions.append(turn['metadata']['emotion'])
        return emotions

    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the current context.

        Returns:
            Dictionary with context statistics
        """
        return {
            'window_size': len(self.context.context_window),
            'max_window_size': self.max_window_size,
            'current_topic': self.context.current_topic,
            'emotional_state': self.context.emotional_state,
            'timestamp': self.context.timestamp.isoformat() if self.context.context_window else None
        }
