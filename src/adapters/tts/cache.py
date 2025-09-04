"""
TTS Cache System - Perceived Latency Polish
Caches short phrases for instant playback while preserving barge-in behavior.
"""

import os
import json
import hashlib
import threading
import time
from pathlib import Path
from typing import Dict, Optional, Set
import tempfile
from dataclasses import dataclass
from queue import Queue, Empty

@dataclass
class CachedPhrase:
    """Represents a cached TTS phrase"""
    text: str
    file_path: str
    duration_seconds: float
    voice_id: str
    created_at: float
    access_count: int = 0
    last_accessed: float = 0

class TTSCache:
    """
    Intelligent TTS caching system for perceived latency improvements.
    
    Features:
    - Caches phrases ≤2 seconds for instant playback
    - Background pre-generation of common phrases
    - LRU eviction with usage tracking
    - Preserves existing barge-in behavior
    - Thread-safe operations
    """
    
    def __init__(self, cache_dir: str = None, max_phrase_duration: float = 2.0, 
                 max_cache_size_mb: int = 50, enable_pregeneration: bool = True):
        self.cache_dir = Path(cache_dir or tempfile.mkdtemp(prefix="penny_tts_cache_"))
        self.cache_dir.mkdir(exist_ok=True)
        
        self.max_phrase_duration = max_phrase_duration
        self.max_cache_size_mb = max_cache_size_mb
        self.enable_pregeneration = enable_pregeneration
        
        # Cache storage
        self.cache: Dict[str, CachedPhrase] = {}
        self.cache_lock = threading.RLock()
        
        # Background processing
        self.pregeneration_queue: Queue = Queue()
        self.background_thread: Optional[threading.Thread] = None
        self.shutdown_flag = threading.Event()
        
        # Statistics
        self.stats = {
            'hits': 0,
            'misses': 0,
            'generations': 0,
            'evictions': 0,
            'background_generations': 0
        }
        
        # Common phrases for pregeneration
        self.common_phrases = [
            "Hello",
            "Hi there",
            "I'm sorry",
            "Let me check",
            "One moment",
            "Please wait",
            "I don't understand",
            "Can you repeat that?",
            "I'm here to help",
            "Thank you",
            "You're welcome",
            "Goodbye",
            "See you later",
            "I'm thinking",
            "Got it",
            "Understood",
            "No problem",
            "Sure thing",
            "Of course",
            "I see"
        ]
        
        self._load_cache_metadata()
        if self.enable_pregeneration:
            self._start_background_thread()
    
    def _generate_cache_key(self, text: str, voice_id: str = "default") -> str:
        """Generate a cache key for the given text and voice"""
        content = f"{text.lower().strip()}:{voice_id}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def _estimate_duration(self, text: str) -> float:
        """Estimate speech duration for text (rough approximation)"""
        # Rough estimate: ~150 words per minute, ~5 chars per word
        chars = len(text.strip())
        words = max(1, chars / 5)
        return (words / 150) * 60
    
    def _should_cache(self, text: str) -> bool:
        """Determine if a phrase should be cached"""
        text = text.strip()
        if not text or len(text) > 100:  # Skip very long phrases
            return False
        
        estimated_duration = self._estimate_duration(text)
        return estimated_duration <= self.max_phrase_duration
    
    def _get_cache_file_path(self, cache_key: str) -> Path:
        """Get the file path for a cache entry"""
        return self.cache_dir / f"{cache_key}.wav"
    
    def get_cached_audio(self, text: str, voice_id: str = "default") -> Optional[str]:
        """
        Retrieve cached audio file path if available.
        Returns None if not cached or cache miss.
        """
        if not self._should_cache(text):
            return None
        
        cache_key = self._generate_cache_key(text, voice_id)
        
        with self.cache_lock:
            if cache_key in self.cache:
                cached = self.cache[cache_key]
                
                # Check if file still exists
                if cached.file_path and os.path.exists(cached.file_path):
                    # Update access stats
                    cached.access_count += 1
                    cached.last_accessed = time.time()
                    self.stats['hits'] += 1
                    return cached.file_path
                else:
                    # File missing, remove from cache
                    del self.cache[cache_key]
            
            self.stats['misses'] += 1
            return None
    
    def cache_generated_audio(self, text: str, audio_file_path: str, 
                            duration: float, voice_id: str = "default") -> bool:
        """
        Cache a generated audio file.
        Returns True if cached successfully, False if skipped.
        """
        if not self._should_cache(text):
            return False
        
        if duration > self.max_phrase_duration:
            return False
        
        cache_key = self._generate_cache_key(text, voice_id)
        cache_file_path = self._get_cache_file_path(cache_key)
        
        try:
            # Copy audio file to cache
            import shutil
            shutil.copy2(audio_file_path, cache_file_path)
            
            with self.cache_lock:
                self.cache[cache_key] = CachedPhrase(
                    text=text.strip(),
                    file_path=str(cache_file_path),
                    duration_seconds=duration,
                    voice_id=voice_id,
                    created_at=time.time(),
                    access_count=0,
                    last_accessed=time.time()
                )
                
                self.stats['generations'] += 1
                
                # Check cache size and evict if necessary
                self._evict_if_necessary()
                
            return True
            
        except Exception as e:
            print(f"Failed to cache audio: {e}")
            return False
    
    def request_pregeneration(self, text: str, voice_id: str = "default", priority: bool = False):
        """Request background pregeneration of a phrase"""
        if not self.enable_pregeneration or not self._should_cache(text):
            return
        
        cache_key = self._generate_cache_key(text, voice_id)
        
        with self.cache_lock:
            # Skip if already cached
            if cache_key in self.cache:
                return
        
        try:
            if priority:
                # Add to front of queue for high-priority items
                temp_queue = Queue()
                temp_queue.put((text, voice_id))
                while not self.pregeneration_queue.empty():
                    try:
                        item = self.pregeneration_queue.get_nowait()
                        temp_queue.put(item)
                    except Empty:
                        break
                
                self.pregeneration_queue = temp_queue
            else:
                self.pregeneration_queue.put((text, voice_id))
        except Exception as e:
            print(f"Failed to queue pregeneration: {e}")
    
    def _start_background_thread(self):
        """Start the background pregeneration thread"""
        if self.background_thread is None or not self.background_thread.is_alive():
            self.background_thread = threading.Thread(
                target=self._background_worker,
                daemon=True,
                name="TTSCacheWorker"
            )
            self.background_thread.start()
    
    def _background_worker(self):
        """Background worker for pregeneration"""
        while not self.shutdown_flag.is_set():
            try:
                # Get item from queue with timeout
                text, voice_id = self.pregeneration_queue.get(timeout=1.0)
                
                cache_key = self._generate_cache_key(text, voice_id)
                
                # Skip if already cached
                with self.cache_lock:
                    if cache_key in self.cache:
                        continue
                
                # Generate TTS in background
                self._generate_and_cache_phrase(text, voice_id)
                self.stats['background_generations'] += 1
                
            except Empty:
                continue
            except Exception as e:
                print(f"Background TTS generation error: {e}")
    
    def _generate_and_cache_phrase(self, text: str, voice_id: str):
        """Generate and cache a single phrase (called from background thread)"""
        try:
            # Import TTS adapter (avoid circular imports)
            from adapters.tts.google_tts_adapter import GoogleTTS
            
            # Create temporary TTS instance
            tts = GoogleTTS({})
            
            # Generate audio to temporary file
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                temp_path = temp_file.name
            
            # Generate TTS (this should be non-blocking for background generation)
            tts.speak(text, voice_id=voice_id, output_file=temp_path)
            
            # Get duration (rough estimate for caching decision)
            duration = self._estimate_duration(text)
            
            # Cache the generated audio
            self.cache_generated_audio(text, temp_path, duration, voice_id)
            
            # Clean up temp file
            os.unlink(temp_path)
            
        except Exception as e:
            print(f"Failed to generate cached phrase '{text}': {e}")
    
    def prime_common_phrases(self, voice_id: str = "default"):
        """Queue common phrases for pregeneration"""
        for phrase in self.common_phrases:
            self.request_pregeneration(phrase, voice_id)
    
    def _evict_if_necessary(self):
        """Evict least recently used items if cache is too large"""
        # Calculate current cache size
        total_size = 0
        for cached in self.cache.values():
            if os.path.exists(cached.file_path):
                total_size += os.path.getsize(cached.file_path)
        
        max_size_bytes = self.max_cache_size_mb * 1024 * 1024
        
        if total_size <= max_size_bytes:
            return
        
        # Sort by access patterns (LRU + frequency)
        items = list(self.cache.items())
        items.sort(key=lambda x: (x[1].access_count, x[1].last_accessed))
        
        # Evict items until under size limit
        for cache_key, cached in items:
            if total_size <= max_size_bytes:
                break
            
            try:
                if os.path.exists(cached.file_path):
                    file_size = os.path.getsize(cached.file_path)
                    os.unlink(cached.file_path)
                    total_size -= file_size
                
                del self.cache[cache_key]
                self.stats['evictions'] += 1
                
            except Exception as e:
                print(f"Failed to evict cache entry: {e}")
    
    def _load_cache_metadata(self):
        """Load cache metadata from disk (for persistence across restarts)"""
        metadata_file = self.cache_dir / "cache_metadata.json"
        if not metadata_file.exists():
            return
        
        try:
            with open(metadata_file, 'r') as f:
                data = json.load(f)
            
            for cache_key, cached_data in data.items():
                file_path = cached_data['file_path']
                
                # Only load if file still exists
                if os.path.exists(file_path):
                    self.cache[cache_key] = CachedPhrase(
                        text=cached_data['text'],
                        file_path=file_path,
                        duration_seconds=cached_data['duration_seconds'],
                        voice_id=cached_data['voice_id'],
                        created_at=cached_data['created_at'],
                        access_count=cached_data.get('access_count', 0),
                        last_accessed=cached_data.get('last_accessed', time.time())
                    )
        
        except Exception as e:
            print(f"Failed to load cache metadata: {e}")
    
    def _save_cache_metadata(self):
        """Save cache metadata to disk"""
        metadata_file = self.cache_dir / "cache_metadata.json"
        
        try:
            data = {}
            for cache_key, cached in self.cache.items():
                data[cache_key] = {
                    'text': cached.text,
                    'file_path': cached.file_path,
                    'duration_seconds': cached.duration_seconds,
                    'voice_id': cached.voice_id,
                    'created_at': cached.created_at,
                    'access_count': cached.access_count,
                    'last_accessed': cached.last_accessed
                }
            
            with open(metadata_file, 'w') as f:
                json.dump(data, f, indent=2)
        
        except Exception as e:
            print(f"Failed to save cache metadata: {e}")
    
    def get_stats(self) -> Dict:
        """Get cache statistics"""
        with self.cache_lock:
            total_size = 0
            for cached in self.cache.values():
                if os.path.exists(cached.file_path):
                    total_size += os.path.getsize(cached.file_path)
            
            return {
                **self.stats,
                'cached_phrases': len(self.cache),
                'cache_size_mb': total_size / (1024 * 1024),
                'hit_rate': self.stats['hits'] / max(1, self.stats['hits'] + self.stats['misses'])
            }
    
    def clear_cache(self):
        """Clear all cached items"""
        with self.cache_lock:
            for cached in self.cache.values():
                try:
                    if os.path.exists(cached.file_path):
                        os.unlink(cached.file_path)
                except Exception as e:
                    print(f"Failed to delete cached file: {e}")
            
            self.cache.clear()
            self.stats = {key: 0 for key in self.stats}
    
    def shutdown(self):
        """Shutdown the cache system gracefully"""
        self.shutdown_flag.set()
        
        if self.background_thread and self.background_thread.is_alive():
            self.background_thread.join(timeout=2.0)
        
        self._save_cache_metadata()

# Global cache instance (singleton pattern)
_global_cache: Optional[TTSCache] = None

def get_tts_cache() -> TTSCache:
    """Get the global TTS cache instance"""
    global _global_cache
    if _global_cache is None:
        _global_cache = TTSCache()
    return _global_cache

def initialize_tts_cache(cache_dir: str = None, **kwargs) -> TTSCache:
    """Initialize the global TTS cache with custom settings"""
    global _global_cache
    _global_cache = TTSCache(cache_dir=cache_dir, **kwargs)
    return _global_cache
