#!/usr/bin/env python3
"""
Tests for Personality State Cache (Phase 3A)
"""

import time
import pytest
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "personality"))

from personality_state_cache import PersonalityStateCache


def test_cache_hit():
    """Test cache returns stored value."""
    cache = PersonalityStateCache(ttl_seconds=300)

    test_state = {
        "formality": {"value": 0.8, "confidence": 0.7}
    }

    cache.set("test_user", test_state)

    # Should hit cache
    retrieved = cache.get("test_user")
    assert retrieved == test_state
    assert cache.stats["hits"] == 1
    assert cache.stats["misses"] == 0


def test_cache_miss():
    """Test cache returns None for non-existent key."""
    cache = PersonalityStateCache(ttl_seconds=300)

    retrieved = cache.get("nonexistent_user")
    assert retrieved is None
    assert cache.stats["misses"] == 1


def test_cache_expiration():
    """Test cache entries expire after TTL."""
    cache = PersonalityStateCache(ttl_seconds=1)  # 1 second TTL

    test_state = {"formality": {"value": 0.8, "confidence": 0.7}}
    cache.set("test_user", test_state)

    # Should hit immediately
    assert cache.get("test_user") == test_state

    # Wait for expiration
    time.sleep(1.5)

    # Should miss (expired)
    assert cache.get("test_user") is None
    assert cache.stats["misses"] == 1


def test_cache_invalidation():
    """Test manual cache invalidation."""
    cache = PersonalityStateCache(ttl_seconds=300)

    test_state = {"formality": {"value": 0.8, "confidence": 0.7}}
    cache.set("test_user", test_state)

    # Should hit
    assert cache.get("test_user") == test_state

    # Invalidate
    cache.invalidate("test_user")

    # Should miss
    assert cache.get("test_user") is None
    assert cache.stats["invalidations"] == 1


def test_cache_stats():
    """Test cache statistics."""
    cache = PersonalityStateCache(ttl_seconds=300)

    test_state = {"formality": {"value": 0.8, "confidence": 0.7}}

    # 2 hits, 1 miss
    cache.set("user1", test_state)
    cache.get("user1")  # hit
    cache.get("user1")  # hit
    cache.get("user2")  # miss

    stats = cache.get_stats()
    assert stats["hits"] == 2
    assert stats["misses"] == 1
    assert stats["hit_rate"] == 2/3  # 66.7%
    assert stats["cache_size"] == 1


def test_cache_clear():
    """Test clearing entire cache."""
    cache = PersonalityStateCache(ttl_seconds=300)

    cache.set("user1", {"test": "data1"})
    cache.set("user2", {"test": "data2"})

    assert cache.get_stats()["cache_size"] == 2

    cache.clear()

    assert cache.get_stats()["cache_size"] == 0
    assert cache.get("user1") is None
    assert cache.get("user2") is None


def test_multiple_users():
    """Test cache handles multiple users independently."""
    cache = PersonalityStateCache(ttl_seconds=300)

    state1 = {"formality": {"value": 0.8, "confidence": 0.7}}
    state2 = {"formality": {"value": 0.3, "confidence": 0.6}}

    cache.set("user1", state1)
    cache.set("user2", state2)

    assert cache.get("user1") == state1
    assert cache.get("user2") == state2

    # Invalidate one shouldn't affect the other
    cache.invalidate("user1")
    assert cache.get("user1") is None
    assert cache.get("user2") == state2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
