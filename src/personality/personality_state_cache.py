#!/usr/bin/env python3
"""
Personality State Cache - Phase 3A
Caches personality state in memory to reduce DB reads.
"""

import time
from typing import Optional, Dict, Any
from datetime import datetime, timedelta


class PersonalityStateCache:
    """
    In-memory cache for personality state.

    Reduces database reads by caching personality state
    with a configurable TTL (Time To Live).
    """

    def __init__(self, ttl_seconds: int = 300):
        """
        Initialize cache.

        Args:
            ttl_seconds: Time to live for cached entries (default: 5 minutes)
        """
        self.ttl_seconds = ttl_seconds
        self.cache = {}  # {user_id: (personality_state, timestamp)}
        self.stats = {
            "hits": 0,
            "misses": 0,
            "invalidations": 0
        }

    def get(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get personality state from cache.

        Returns None if not cached or expired.
        """
        if user_id not in self.cache:
            self.stats["misses"] += 1
            return None

        personality_state, cached_time = self.cache[user_id]

        # Check if expired
        age = time.time() - cached_time
        if age > self.ttl_seconds:
            # Expired - remove from cache
            del self.cache[user_id]
            self.stats["misses"] += 1
            return None

        # Cache hit!
        self.stats["hits"] += 1
        return personality_state

    def set(self, user_id: str, personality_state: Dict[str, Any]):
        """
        Store personality state in cache.
        """
        self.cache[user_id] = (personality_state, time.time())

    def invalidate(self, user_id: str):
        """
        Invalidate cache for user.

        Call this when personality state is updated.
        """
        if user_id in self.cache:
            del self.cache[user_id]
            self.stats["invalidations"] += 1

    def clear(self):
        """Clear entire cache."""
        self.cache.clear()

    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            {
                "hits": int,
                "misses": int,
                "invalidations": int,
                "hit_rate": float (0.0-1.0),
                "cache_size": int,
                "ttl_seconds": int
            }
        """
        total_requests = self.stats["hits"] + self.stats["misses"]
        hit_rate = self.stats["hits"] / total_requests if total_requests > 0 else 0.0

        return {
            "hits": self.stats["hits"],
            "misses": self.stats["misses"],
            "invalidations": self.stats["invalidations"],
            "hit_rate": hit_rate,
            "cache_size": len(self.cache),
            "ttl_seconds": self.ttl_seconds
        }


# Global cache instance
_cache = PersonalityStateCache(ttl_seconds=300)  # 5 minutes


def get_cache() -> PersonalityStateCache:
    """Get the global cache instance."""
    return _cache
