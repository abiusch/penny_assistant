import os, tempfile, subprocess, threading, time
import hashlib
from pathlib import Path
from typing import Optional, Dict

try:
    from gtts import gTTS  # type: ignore
    GTTS_AVAILABLE = True
except Exception:
    gTTS = None
    GTTS_AVAILABLE = False

class GoogleTTS:
    def __init__(self, config):
        self.config = config or {}
        self.tts_config = self.config.get('tts', {})
        self._last_file = None
        self._error_logged = False
        
        # Initialize cache
        self.cache_enabled = self.tts_config.get('cache_enabled', True)
        self.cache_dir = Path(tempfile.gettempdir()) / 'pennygpt_tts_cache'
        if self.cache_enabled:
            self.cache_dir.mkdir(exist_ok=True)
        
        # Cache for phrases under 60 characters
        self.memory_cache: Dict[str, str] = {}
        self.max_cache_phrase_length = 60
        
        # Background playback thread
        self._playback_thread = None
        self._stop_playback = threading.Event()

    def _get_cache_key(self, text: str) -> str:
        """Generate cache key for text."""
        return hashlib.md5(text.encode('utf-8')).hexdigest()

    def _get_cached_file(self, text: str) -> Optional[str]:
        """Get cached audio file path if exists."""
        if not self.cache_enabled:
            return None
            
        cache_key = self._get_cache_key(text)
        
        # Check memory cache for short phrases
        if len(text) <= self.max_cache_phrase_length:
            return self.memory_cache.get(cache_key)
        
        # Check disk cache
        cache_file = self.cache_dir / f"{cache_key}.mp3"
        if cache_file.exists():
            return str(cache_file)
        
        return None

    def _cache_file(self, text: str, file_path: str):
        """Cache the audio file."""
        if not self.cache_enabled:
            return
            
        cache_key = self._get_cache_key(text)
        
        # Cache short phrases in memory
        if len(text) <= self.max_cache_phrase_length:
            self.memory_cache[cache_key] = file_path
        
        # Also cache to disk for persistence
        try:
            cache_file = self.cache_dir / f"{cache_key}.mp3"
            if not cache_file.exists():
                import shutil
                shutil.copy2(file_path, cache_file)
        except Exception as e:
            if not self._error_logged:
                print(f"[TTS] Cache write failed: {e}")

    def _synthesize_audio(self, text: str) -> Optional[str]:
        """Synthesize text to audio file."""
        if not GTTS_AVAILABLE:
            if not self._error_logged:
                print("[TTS] gTTS not installed; skipping audio synthesis.")
                self._error_logged = True
            return None
        
        try:
            # Check cache first
            cached_file = self._get_cached_file(text)
            if cached_file and os.path.exists(cached_file):
                return cached_file
            
            # Synthesize new audio
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
                gTTS(text=text, lang="en").save(f.name)
                self._last_file = f.name
                
                # Cache the result
                self._cache_file(text, f.name)
                
                return f.name
                
        except Exception as e:
            if not self._error_logged:
                print(f"[TTS] Synthesis failed: {e}")
                self._error_logged = True
            return None

    def _play_audio_file(self, file_path: str) -> bool:
        """Play audio file using system player."""
        try:
            # Use afplay on macOS
            process = subprocess.Popen(
                ["afplay", file_path],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            
            # Wait for playback to complete or stop signal
            while process.poll() is None:
                if self._stop_playback.wait(0.1):  # Check every 100ms
                    process.terminate()
                    try:
                        process.wait(timeout=1.0)
                    except subprocess.TimeoutExpired:
                        process.kill()
                    return False
            
            return process.returncode == 0
            
        except Exception as e:
            if not self._error_logged:
                print(f"[TTS] Playback failed: {e}")
                self._error_logged = True
            return False

    def _background_play(self, file_path: str):
        """Background thread function for audio playback."""
        try:
            self._play_audio_file(file_path)
        except Exception as e:
            if not self._error_logged:
                print(f"[TTS] Background playback error: {e}")
        finally:
            self._stop_playback.clear()

    def speak(self, text: str, voice_id=None, ssml=None, allow_barge_in=True) -> bool:
        """
        Speak the given text.
        
        Returns:
            bool: True if synthesis and playback initiation succeeded, False otherwise
        """
        if not text or not text.strip():
            return True  # Nothing to speak
        
        text = text.strip()
        
        # Stop any current playback
        self.stop()
        
        # Synthesize audio
        audio_file = self._synthesize_audio(text)
        if not audio_file:
            return False
        
        # Start background playback
        self._playback_thread = threading.Thread(
            target=self._background_play,
            args=(audio_file,),
            daemon=True
        )
        self._playback_thread.start()
        
        return True

    def stop(self):
        """Stop current audio playback."""
        # Signal stop to background thread
        self._stop_playback.set()
        
        # Wait for thread to finish (with timeout)
        if self._playback_thread and self._playback_thread.is_alive():
            self._playback_thread.join(timeout=1.0)
        
        # Fallback: kill all afplay processes
        try:
            subprocess.run(
                ["killall", "afplay"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
                timeout=2.0
            )
        except Exception:
            pass  # Ignore errors

    def is_speaking(self) -> bool:
        """Check if currently speaking."""
        return (self._playback_thread and 
                self._playback_thread.is_alive() and 
                not self._stop_playback.is_set())

    def clear_cache(self):
        """Clear TTS cache."""
        self.memory_cache.clear()
        
        if self.cache_enabled and self.cache_dir.exists():
            try:
                import shutil
                shutil.rmtree(self.cache_dir)
                self.cache_dir.mkdir(exist_ok=True)
                print("[TTS] Cache cleared successfully")
            except Exception as e:
                print(f"[TTS] Failed to clear cache: {e}")

    def preload_common_phrases(self):
        """Preload common phrases to reduce latency."""
        if not self.tts_config.get('preload_common_phrases', False):
            return
            
        common_phrases = [
            "Hello!",
            "I'm listening.",
            "Sorry, I didn't catch that.",
            "Let me think about that.",
            "I'm having trouble with that request.",
            "Is there anything else I can help you with?",
            "Goodbye!"
        ]
        
        print("[TTS] Preloading common phrases...")
        for phrase in common_phrases:
            self._synthesize_audio(phrase)
        print("[TTS] Preload complete")

    def __del__(self):
        """Cleanup on destruction."""
        try:
            self.stop()
        except Exception:
            pass
