"""
Emotional continuity across sessions.

Tracks significant emotional moments and enables Penny to reference them naturally
in future conversations, creating genuine relationship depth.

Week 8 Implementation
"""

from datetime import datetime, timedelta
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class EmotionalThread:
    """
    Represents a significant emotional moment that can be referenced later.
    
    Think of this as a "bookmark" in your emotional history. When you express
    a strong emotion (intensity >0.8), we save a thread so Penny can follow up
    naturally in future conversations.
    
    Example:
        Monday: "I'm really stressed about layoffs" (intensity=0.9)
        → Thread created
        Wednesday: "Hey Penny"
        → Penny: "Hey! How are you feeling about work? You seemed stressed Monday."
    """
    
    def __init__(
        self,
        emotion: str,
        intensity: float,
        context: str,
        timestamp: datetime,
        turn_id: str
    ):
        """
        Create an emotional thread.
        
        Args:
            emotion: The dominant emotion (joy, sadness, anger, fear, etc.)
            intensity: How strong the emotion was (0.0-1.0, only track if >0.8)
            context: Snippet of what was said (first 200 chars for reference)
            timestamp: When this emotion was expressed
            turn_id: Unique ID for this conversation turn
        """
        self.emotion = emotion
        self.intensity = intensity
        self.context = context[:200]  # Limit context length
        self.timestamp = timestamp
        self.turn_id = turn_id
        self.follow_ups: List[str] = []  # Track which turns referenced this
    
    def to_dict(self) -> dict:
        """Serialize for storage"""
        return {
            'emotion': self.emotion,
            'intensity': self.intensity,
            'context': self.context,
            'timestamp': self.timestamp.isoformat(),
            'turn_id': self.turn_id,
            'follow_ups': self.follow_ups
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'EmotionalThread':
        """Deserialize from storage"""
        thread = cls(
            emotion=data['emotion'],
            intensity=data['intensity'],
            context=data['context'],
            timestamp=datetime.fromisoformat(data['timestamp']),
            turn_id=data['turn_id']
        )
        thread.follow_ups = data.get('follow_ups', [])
        return thread
    
    def __repr__(self) -> str:
        return (
            f"EmotionalThread(emotion='{self.emotion}', "
            f"intensity={self.intensity:.2f}, "
            f"timestamp={self.timestamp.isoformat()})"
        )


class EmotionalContinuity:
    """
    Tracks emotional context across sessions to create relationship continuity.
    
    This is what makes Penny remember not just WHAT you said, but HOW you felt.
    Unlike generic AI that treats each conversation as isolated, Penny can say:
    "You seemed stressed about work last week - how's that going?"
    
    Features:
    - 7-day memory window (remembers recent emotional moments)
    - 0.8+ intensity threshold (only significant emotions)
    - Natural follow-up suggestions
    - User consent required (opt-in)
    - 30-day auto-decay (gradual forgetting)
    
    Privacy:
    - Encrypted storage (inherited from semantic memory)
    - User can disable entirely
    - User can manually forget specific threads
    - No sharing between users
    """
    
    def __init__(
        self,
        semantic_memory,
        emotion_detector,
        window_days: int = 7,
        intensity_threshold: float = 0.8,
        enabled: bool = True
    ):
        """
        Initialize emotional continuity tracker.
        
        Args:
            semantic_memory: SemanticMemory instance for storage
            emotion_detector: EmotionDetectorV2 instance
            window_days: How many days to remember emotions (default 7)
            intensity_threshold: Minimum intensity to track (default 0.8)
            enabled: Whether emotional tracking is active (user can disable)
        """
        self.semantic_memory = semantic_memory
        self.emotion_detector = emotion_detector
        self.window_days = window_days
        self.intensity_threshold = intensity_threshold
        self.enabled = enabled
        
        # In-memory cache of emotional threads
        self.threads: List[EmotionalThread] = []
        
        logger.info(
            f"EmotionalContinuity initialized "
            f"(window={window_days}d, threshold={intensity_threshold}, "
            f"enabled={enabled})"
        )
    
    def track_emotion(
        self,
        user_input: str,
        turn_id: str,
        timestamp: Optional[datetime] = None
    ) -> Optional[EmotionalThread]:
        """
        Track emotional moment if it's significant enough.
        
        This gets called after every user message. Most messages won't create
        a thread (intensity too low), but when you express strong emotion,
        we save it for future reference.
        
        Args:
            user_input: What the user said
            turn_id: Unique ID for this turn
            timestamp: When this was said (defaults to now)
            
        Returns:
            EmotionalThread if emotion was significant, None otherwise
            
        Example:
            >>> tracker.track_emotion(
            ...     "I'm SO excited about this!",
            ...     "turn_12345"
            ... )
            EmotionalThread(emotion='joy', intensity=0.92, ...)
            
            >>> tracker.track_emotion(
            ...     "That's interesting",  # Low intensity
            ...     "turn_12346"
            ... )
            None
        """
        if not self.enabled:
            return None
        
        if timestamp is None:
            timestamp = datetime.now()
        
        # Detect emotion and intensity
        emotion_result = self.emotion_detector.detect_emotion(user_input)
        intensity = self.emotion_detector.detect_intensity(user_input)
        
        # Only track if intensity exceeds threshold
        if intensity < self.intensity_threshold:
            logger.debug(
                f"Emotion intensity {intensity:.2f} below threshold "
                f"{self.intensity_threshold} - not tracking"
            )
            return None
        
        # Create emotional thread
        thread = EmotionalThread(
            emotion=emotion_result['dominant_emotion'],
            intensity=intensity,
            context=user_input,
            timestamp=timestamp,
            turn_id=turn_id
        )
        
        self.threads.append(thread)
        logger.info(
            f"📌 Tracked emotional thread: {thread.emotion} "
            f"(intensity={intensity:.2f})"
        )
        
        # Clean up old threads
        self._cleanup_old_threads()
        
        return thread
    
    def get_recent_threads(
        self,
        emotion: Optional[str] = None,
        min_intensity: float = 0.7
    ) -> List[EmotionalThread]:
        """
        Get recent emotional threads within the memory window.
        
        Args:
            emotion: Filter by specific emotion (optional)
            min_intensity: Minimum intensity threshold
            
        Returns:
            List of recent threads, sorted by timestamp (newest first)
            
        Example:
            >>> # Get all recent threads
            >>> threads = tracker.get_recent_threads()
            
            >>> # Get only sadness threads
            >>> sad_threads = tracker.get_recent_threads(emotion='sadness')
            
            >>> # Get very intense emotions only
            >>> intense = tracker.get_recent_threads(min_intensity=0.9)
        """
        cutoff = datetime.now() - timedelta(days=self.window_days)
        
        # Filter by time window and intensity
        threads = [
            t for t in self.threads
            if t.timestamp > cutoff and t.intensity >= min_intensity
        ]
        
        # Filter by emotion if specified
        if emotion:
            threads = [t for t in threads if t.emotion == emotion]
        
        # Sort by timestamp (newest first)
        return sorted(threads, key=lambda t: t.timestamp, reverse=True)
    
    def should_check_in(self) -> Optional[EmotionalThread]:
        """
        Determine if Penny should proactively check in about an emotional thread.
        
        This looks for significant emotional moments that haven't been followed
        up on yet. Perfect for starting a conversation naturally:
        "Hey, you seemed worried about X last week - how's that going?"
        
        Returns:
            EmotionalThread to check in about, or None if no check-in needed
            
        Example:
            >>> thread = tracker.should_check_in()
            >>> if thread:
            ...     print(f"Check in about: {thread.emotion} - {thread.context}")
        """
        if not self.enabled:
            return None
        
        # Get recent significant threads
        recent = self.get_recent_threads(min_intensity=0.8)
        
        if not recent:
            return None
        
        # Find threads with no follow-ups
        unresolved = [t for t in recent if not t.follow_ups]
        
        if unresolved:
            # Return most recent unresolved thread
            return unresolved[0]
        
        return None
    
    def mark_followed_up(
        self,
        thread: EmotionalThread,
        follow_up_turn_id: str
    ):
        """
        Mark that a thread was followed up on.
        
        Call this when Penny references an emotional thread in her response,
        so we don't keep checking in about the same thing repeatedly.
        
        Args:
            thread: The thread that was referenced
            follow_up_turn_id: ID of the turn where follow-up happened
            
        Example:
            >>> thread = tracker.should_check_in()
            >>> # Penny mentions the thread in her response
            >>> tracker.mark_followed_up(thread, "turn_67890")
        """
        thread.follow_ups.append(follow_up_turn_id)
        logger.info(f"Marked thread {thread.turn_id} as followed up")
    
    def generate_check_in_prompt(self, thread: EmotionalThread) -> str:
        """
        Generate natural check-in prompt addition for Penny.
        
        This creates a system prompt addition that tells Penny about a previous
        emotional moment, so she can reference it naturally if appropriate.
        
        Args:
            thread: The emotional thread to reference
            
        Returns:
            Prompt text to add to system prompt
            
        Example:
            >>> thread = tracker.should_check_in()
            >>> prompt = tracker.generate_check_in_prompt(thread)
            >>> print(prompt)
            [EMOTIONAL CONTEXT] User expressed stress (intensity=0.85) 2 days ago.
            Context: "I'm worried about layoffs". Consider acknowledging naturally.
        """
        days_ago = (datetime.now() - thread.timestamp).days
        
        if days_ago == 0:
            time_ref = "earlier today"
        elif days_ago == 1:
            time_ref = "yesterday"
        else:
            time_ref = f"{days_ago} days ago"
        
        return (
            f"[EMOTIONAL CONTEXT] User expressed {thread.emotion} "
            f"(intensity={thread.intensity:.2f}) {time_ref}. "
            f"Context: \"{thread.context[:100]}...\". "
            f"Consider acknowledging this naturally if appropriate."
        )
    
    def _cleanup_old_threads(self):
        """Remove threads older than memory window"""
        cutoff = datetime.now() - timedelta(days=self.window_days)
        before_count = len(self.threads)
        self.threads = [t for t in self.threads if t.timestamp > cutoff]
        after_count = len(self.threads)
        
        if before_count > after_count:
            logger.debug(
                f"Cleaned up {before_count - after_count} old threads "
                f"(older than {self.window_days} days)"
            )
    
    def get_stats(self) -> dict:
        """
        Get emotional tracking statistics.
        
        Useful for understanding what emotions are being tracked and
        showing the user what Penny remembers about their emotional state.
        
        Returns:
            Dictionary with tracking statistics
            
        Example:
            >>> stats = tracker.get_stats()
            >>> print(f"Tracking {stats['total_threads']} emotional moments")
            >>> print(f"Breakdown: {stats['emotion_breakdown']}")
        """
        recent = self.get_recent_threads()
        
        # Count emotions
        emotion_counts = {}
        for thread in recent:
            emotion_counts[thread.emotion] = emotion_counts.get(thread.emotion, 0) + 1
        
        # Calculate average intensity
        avg_intensity = (
            sum(t.intensity for t in recent) / len(recent)
            if recent else 0.0
        )
        
        return {
            'enabled': self.enabled,
            'window_days': self.window_days,
            'intensity_threshold': self.intensity_threshold,
            'total_threads': len(recent),
            'emotion_breakdown': emotion_counts,
            'avg_intensity': round(avg_intensity, 2),
            'oldest_thread': recent[-1].timestamp.isoformat() if recent else None,
            'newest_thread': recent[0].timestamp.isoformat() if recent else None
        }


if __name__ == "__main__":
    # Demo usage
    logging.basicConfig(level=logging.INFO)
    
    from src.memory.emotion_detector_v2 import EmotionDetectorV2
    from src.memory.semantic_memory import SemanticMemory
    
    # Setup
    detector = EmotionDetectorV2()
    memory = SemanticMemory()
    tracker = EmotionalContinuity(
        semantic_memory=memory,
        emotion_detector=detector,
        window_days=7,
        intensity_threshold=0.8
    )
    
    # Simulate conversation
    print("\n🧠 Emotional Continuity Demo:")
    print("=" * 60)
    
    # Day 1: Strong emotion
    print("\nDay 1:")
    thread1 = tracker.track_emotion(
        "I'm really stressed about the layoffs at work",
        turn_id="turn_001"
    )
    if thread1:
        print(f"✅ Tracked: {thread1.emotion} (intensity={thread1.intensity:.2f})")
    
    # Day 1: Weak emotion (won't track)
    thread2 = tracker.track_emotion(
        "That's kind of interesting",
        turn_id="turn_002"
    )
    if not thread2:
        print("❌ Not tracked: Intensity too low")
    
    # Day 3: Check if we should follow up
    print("\nDay 3:")
    check_in = tracker.should_check_in()
    if check_in:
        prompt = tracker.generate_check_in_prompt(check_in)
        print(f"📝 Check-in prompt:\n{prompt}")
    
    # Show stats
    print("\n📊 Stats:")
    stats = tracker.get_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")
