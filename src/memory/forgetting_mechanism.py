"""
Gradual forgetting mechanism for emotional threads.

Implements time-based decay to make Penny's memory feel natural - she remembers
recent things clearly, but older memories fade over time. Just like a real person.

Week 8 Implementation
"""

from datetime import datetime, timedelta
from typing import List
import logging

logger = logging.getLogger(__name__)


class ForgettingMechanism:
    """
    Implements gradual forgetting of emotional threads.
    
    Real relationships don't have perfect memory - things fade over time.
    This makes Penny's memory feel more natural and prevents her from
    bringing up ancient history inappropriately.
    
    Features:
    - 30-day auto-decay (emotional threads fade completely after 30 days)
    - Intensity-based decay (stronger emotions remembered longer)
    - Linear decay over time (gradually weakens)
    - Manual forget option (user can ask to forget specific things)
    - Forget-all option (user can reset emotional memory)
    
    Example:
        forgetter = ForgettingMechanism(decay_days=30)
        
        # Day 1: Strong emotion (intensity=0.9)
        # Day 7: Still remembered (intensity=0.77)
        # Day 15: Half-strength (intensity=0.45)
        # Day 30: Gone (intensity=0.0)
    """
    
    def __init__(self, decay_days: int = 30):
        """
        Initialize forgetting mechanism.
        
        Args:
            decay_days: Number of days until complete forgetting
        """
        self.decay_days = decay_days
        logger.info(f"ForgettingMechanism initialized (decay={decay_days} days)")
    
    def apply_decay(self, threads: List) -> List:
        """
        Apply time-based decay to emotional threads.
        
        Threads older than decay_days are removed.
        Threads within the window have their intensity reduced linearly.
        
        Formula: 
            new_intensity = original_intensity * (1 - age_days/decay_days)
        
        Args:
            threads: List of EmotionalThread objects
            
        Returns:
            List of threads with decay applied (some may be removed)
            
        Example:
            >>> # Thread from 15 days ago with intensity 0.9
            >>> decayed = forgetter.apply_decay([thread])
            >>> decayed[0].intensity
            0.45  # 0.9 * (1 - 15/30) = 0.9 * 0.5
        """
        now = datetime.now()
        decayed_threads = []
        
        for thread in threads:
            age_days = (now - thread.timestamp).days
            
            # Remove if too old
            if age_days > self.decay_days:
                logger.debug(
                    f"Forgetting thread {thread.turn_id} "
                    f"(age={age_days}d > {self.decay_days}d)"
                )
                continue
            
            # Apply linear decay to intensity
            decay_factor = 1.0 - (age_days / self.decay_days)
            original_intensity = thread.intensity
            thread.intensity *= decay_factor
            
            logger.debug(
                f"Applied decay to thread {thread.turn_id}: "
                f"{original_intensity:.2f} → {thread.intensity:.2f} "
                f"(age={age_days}d, factor={decay_factor:.2f})"
            )
            
            decayed_threads.append(thread)
        
        removed_count = len(threads) - len(decayed_threads)
        if removed_count > 0:
            logger.info(f"Forgot {removed_count} old threads (>{self.decay_days}d)")
        
        return decayed_threads
    
    def forget_thread(self, threads: List, turn_id: str) -> List:
        """
        Manually forget a specific thread.
        
        Use when user says: "Forget about when I was stressed about work"
        
        Args:
            threads: List of EmotionalThread objects
            turn_id: ID of thread to forget
            
        Returns:
            List of threads with specified thread removed
            
        Example:
            >>> threads = forgetter.forget_thread(threads, "turn_12345")
            >>> # Thread with ID "turn_12345" is now removed
        """
        logger.info(f"Manually forgetting thread {turn_id}")
        return [t for t in threads if t.turn_id != turn_id]
    
    def forget_emotion_type(self, threads: List, emotion: str) -> List:
        """
        Forget all threads of a specific emotion type.
        
        Use when user says: "Forget about all the times I was sad"
        
        Args:
            threads: List of EmotionalThread objects
            emotion: Emotion type to forget (e.g., 'sadness', 'anger')
            
        Returns:
            List of threads with specified emotion type removed
            
        Example:
            >>> # Forget all sadness
            >>> threads = forgetter.forget_emotion_type(threads, 'sadness')
        """
        before_count = len(threads)
        filtered = [t for t in threads if t.emotion != emotion]
        after_count = len(filtered)
        
        removed_count = before_count - after_count
        logger.info(f"Forgot {removed_count} threads of type '{emotion}'")
        
        return filtered
    
    def forget_time_range(
        self,
        threads: List,
        start: datetime,
        end: datetime
    ) -> List:
        """
        Forget all threads within a time range.
        
        Use when user says: "Forget about last week"
        
        Args:
            threads: List of EmotionalThread objects
            start: Start of time range
            end: End of time range
            
        Returns:
            List of threads with threads in range removed
            
        Example:
            >>> # Forget last week
            >>> last_week_start = datetime.now() - timedelta(days=7)
            >>> threads = forgetter.forget_time_range(
            ...     threads, last_week_start, datetime.now()
            ... )
        """
        before_count = len(threads)
        filtered = [
            t for t in threads
            if not (start <= t.timestamp <= end)
        ]
        after_count = len(filtered)
        
        removed_count = before_count - after_count
        logger.info(
            f"Forgot {removed_count} threads from "
            f"{start.isoformat()} to {end.isoformat()}"
        )
        
        return filtered
    
    def forget_all(self, threads: List) -> List:
        """
        Forget all emotional threads.
        
        Use when user explicitly requests full emotional memory reset:
        "Forget everything about my emotional state"
        
        This is a nuclear option - use carefully and confirm with user first.
        
        Args:
            threads: List of EmotionalThread objects
            
        Returns:
            Empty list
            
        Example:
            >>> # User requested memory reset
            >>> threads = forgetter.forget_all(threads)
            >>> len(threads)
            0
        """
        count = len(threads)
        logger.warning(f"Forgetting ALL emotional threads ({count} total) - user request")
        return []
    
    def get_decay_stats(self, threads: List) -> dict:
        """
        Get statistics about decay status.
        
        Useful for understanding memory health and showing user
        what will be forgotten soon.
        
        Args:
            threads: List of EmotionalThread objects
            
        Returns:
            Dictionary with decay statistics
            
        Example:
            >>> stats = forgetter.get_decay_stats(threads)
            >>> print(f"{stats['will_decay_soon']} threads will fade in 3 days")
        """
        now = datetime.now()
        
        # Categorize by age
        fresh = []      # < 7 days
        aging = []      # 7-14 days
        fading = []     # 14-30 days
        
        for thread in threads:
            age_days = (now - thread.timestamp).days
            
            if age_days < 7:
                fresh.append(thread)
            elif age_days < 14:
                aging.append(thread)
            elif age_days < self.decay_days:
                fading.append(thread)
        
        return {
            'total_threads': len(threads),
            'fresh': len(fresh),           # Recently created
            'aging': len(aging),           # Starting to fade
            'fading': len(fading),         # Will be gone soon
            'decay_days': self.decay_days,
            'oldest_age_days': max(
                ((now - t.timestamp).days for t in threads),
                default=0
            )
        }


if __name__ == "__main__":
    # Demo usage
    logging.basicConfig(level=logging.INFO)
    
    from src.memory.emotional_continuity import EmotionalThread
    
    print("\n🕰️ Forgetting Mechanism Demo:")
    print("=" * 60)
    
    forgetter = ForgettingMechanism(decay_days=30)
    
    # Create test threads of different ages
    now = datetime.now()
    threads = [
        EmotionalThread(
            emotion='joy',
            intensity=0.9,
            context="Really excited!",
            timestamp=now - timedelta(days=5),
            turn_id="turn_001"
        ),
        EmotionalThread(
            emotion='sadness',
            intensity=0.8,
            context="Feeling down",
            timestamp=now - timedelta(days=15),
            turn_id="turn_002"
        ),
        EmotionalThread(
            emotion='anger',
            intensity=0.85,
            context="So frustrated",
            timestamp=now - timedelta(days=35),
            turn_id="turn_003"
        )
    ]
    
    print(f"\n📋 Before decay ({len(threads)} threads):")
    for t in threads:
        age = (now - t.timestamp).days
        print(f"  {t.emotion}: {t.intensity:.2f} (age={age}d)")
    
    # Apply decay
    decayed = forgetter.apply_decay(threads)
    
    print(f"\n⏰ After decay ({len(decayed)} threads):")
    for t in decayed:
        age = (now - t.timestamp).days
        print(f"  {t.emotion}: {t.intensity:.2f} (age={age}d)")
    
    # Show stats
    print("\n📊 Decay Stats:")
    stats = forgetter.get_decay_stats(decayed)
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    # Test manual forgetting
    print("\n🗑️ Manually forgetting sadness thread...")
    filtered = forgetter.forget_thread(decayed, "turn_002")
    print(f"  Remaining: {len(filtered)} threads")
