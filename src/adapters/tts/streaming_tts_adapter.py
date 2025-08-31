"""
Low-latency TTS adapter with streaming, caching, and preprocessing
"""

import os
import tempfile
import subprocess
import threading
import time
import hashlib
import json
from pathlib import Path
from queue import Queue, Empty
from typing import Optional, Dict, Any, Callable
import asyncio

try:
    from gtts import gTTS
    GTTS_AVAILABLE = True
except ImportError:
    GTTS_AVAILABLE = False

try:
    import pyttsx3
    PYTTSX3_AVAILABLE = True
except ImportError:
    PYTTSX3_AVAILABLE = False


class StreamingTTS:
    """Low-latency TTS with streaming, caching, and multiple backends"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.cache_dir = Path(tempfile.gettempdir()) / "penny_tts_cache"
        self.cache_dir.mkdir(exist_ok=True)
        
        # Audio playback queue for streaming
        self.audio_queue = Queue()
        self.playback_thread = None
        self.is_playing = False
        self.stop_playback = threading.Event()
        
        # TTS backends in order of preference (fastest first)
        self.backends = self._initialize_backends()
        
        # Common phrases cache
        self.phrase_cache = self._load_phrase_cache()
        
        # Background preprocessing
        self.preprocess_queue = Queue()
        self.preprocess_thread = None
        self._start_background_processor()
        
    def _initialize_backends(self) -> list:
        """Initialize available TTS backends in order of latency preference"""
        backends = []
        
        # 1. System TTS (fastest, lowest quality)
        if PYTTSX3_AVAILABLE:
            try:
                engine = pyttsx3.init()
                # Configure for speed
                engine.setProperty('rate', self.config.get('speaking_rate', 1.2) * 200)
                engine.setProperty('volume', 0.9)
                voices = engine.getProperty('voices')
                if voices:
                    # Prefer female voices for clarity
                    for voice in voices:
                        if 'female' in voice.name.lower() or 'samantha' in voice.name.lower():
                            engine.setProperty('voice', voice.id)
                            break
                backends.append(('system', engine))
            except Exception as e:
                print(f"[TTS] System TTS unavailable: {e}")
        
        # 2. Google TTS (higher quality, moderate latency)
        if GTTS_AVAILABLE:
            backends.append(('google', None))
            
        # 3. Say command (macOS fallback)
        if os.system("which say > /dev/null 2>&1") == 0:
            backends.append(('say', None))
            
        return backends
    
    def _load_phrase_cache(self) -> Dict[str, str]:
        """Load cached audio files for common phrases"""
        cache_file = self.cache_dir / "phrase_cache.json"
        if cache_file.exists():
            try:
                with open(cache_file, 'r') as f:
                    return json.load(f)
            except Exception:
                pass
        return {}
    
    def _save_phrase_cache(self):
        """Save phrase cache to disk"""
        cache_file = self.cache_dir / "phrase_cache.json"
        try:
            with open(cache_file, 'w') as f:
                json.dump(self.phrase_cache, f)
        except Exception as e:
            print(f"[TTS] Cache save failed: {e}")
    
    def _get_cache_key(self, text: str, backend: str) -> str:
        """Generate cache key for text and backend"""
        return hashlib.md5(f"{backend}:{text}".encode()).hexdigest()
    
    def _start_background_processor(self):
        """Start background thread for preprocessing common phrases"""
        if self.preprocess_thread is None or not self.preprocess_thread.is_alive():
            self.preprocess_thread = threading.Thread(
                target=self._background_processor,
                daemon=True
            )
            self.preprocess_thread.start()
    
    def _background_processor(self):
        """Background processor for common phrases"""
        common_phrases = [
            "I didn't catch that. Could you say it again?",
            "I'm not sure about that.",
            "Let me think about that.",
            "That's interesting.",
            "I don't have information about that.",
            "Could you be more specific?",
            "I'm processing that now.",
            "Just a moment.",
            "I'm sorry, I didn't understand.",
            "That sounds good."
        ]
        
        # Preprocess common phrases during idle time
        for phrase in common_phrases:
            try:
                # Only preprocess if not already cached
                cache_key = self._get_cache_key(phrase, 'google')
                if cache_key not in self.phrase_cache:
                    self._preprocess_phrase(phrase)
                    time.sleep(0.1)  # Don't overwhelm the system
            except Exception as e:
                print(f"[TTS] Background processing failed for '{phrase}': {e}")
    
    def _preprocess_phrase(self, text: str):
        """Preprocess a phrase and cache the audio"""
        for backend_name, backend in self.backends:
            cache_key = self._get_cache_key(text, backend_name)
            if cache_key in self.phrase_cache:
                continue
                
            try:
                audio_file = self._generate_audio(text, backend_name, backend)
                if audio_file and os.path.exists(audio_file):
                    self.phrase_cache[cache_key] = audio_file
                    break  # Use first successful backend
            except Exception as e:
                print(f"[TTS] Preprocessing failed for backend {backend_name}: {e}")
                continue
        
        self._save_phrase_cache()
    
    def _generate_audio(self, text: str, backend_name: str, backend: Any) -> Optional[str]:
        """Generate audio file for given text using specified backend"""
        
        if backend_name == 'system' and backend:
            # Use pyttsx3 for immediate playback (no file needed)
            return 'SYSTEM_IMMEDIATE'
            
        elif backend_name == 'google':
            # Use Google TTS
            try:
                audio_file = self.cache_dir / f"tts_{int(time.time() * 1000)}.mp3"
                tts = gTTS(text=text, lang="en", slow=False)
                tts.save(str(audio_file))
                return str(audio_file)
            except Exception as e:
                print(f"[TTS] Google TTS failed: {e}")
                return None
                
        elif backend_name == 'say':
            # Use macOS say command
            try:
                audio_file = self.cache_dir / f"say_{int(time.time() * 1000)}.aiff"
                cmd = [
                    'say', 
                    '-o', str(audio_file),
                    '-r', str(int(self.config.get('speaking_rate', 1.0) * 200)),
                    text
                ]
                subprocess.run(cmd, check=True, capture_output=True)
                return str(audio_file)
            except Exception as e:
                print(f"[TTS] Say command failed: {e}")
                return None
        
        return None
    
    def _start_playback_thread(self):
        """Start the audio playback thread"""
        if self.playback_thread is None or not self.playback_thread.is_alive():
            self.stop_playback.clear()
            self.playback_thread = threading.Thread(
                target=self._playback_worker,
                daemon=True
            )
            self.playback_thread.start()
    
    def _playback_worker(self):
        """Worker thread for playing audio files"""
        while not self.stop_playback.is_set():
            try:
                audio_file = self.audio_queue.get(timeout=0.1)
                if audio_file == 'STOP':
                    break
                    
                if audio_file == 'SYSTEM_IMMEDIATE':
                    # System TTS handles playback directly
                    continue
                    
                if audio_file and os.path.exists(audio_file):
                    # Play audio file
                    try:
                        process = subprocess.Popen(
                            ['afplay', audio_file],
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL
                        )
                        
                        # Wait for playback to complete or stop signal
                        while process.poll() is None and not self.stop_playback.is_set():
                            time.sleep(0.01)
                        
                        if self.stop_playback.is_set():
                            process.terminate()
                            
                    except Exception as e:
                        print(f"[TTS] Playback failed: {e}")
                        
                self.audio_queue.task_done()
                
            except Empty:
                continue
            except Exception as e:
                print(f"[TTS] Playback worker error: {e}")
    
    def speak(self, text: str, voice_id: Optional[str] = None, 
             ssml: Optional[str] = None, allow_barge_in: bool = True) -> bool:
        """
        Speak text with minimal latency using best available method
        Returns True if speech started successfully
        """
        if not text or not text.strip():
            return False
        
        text = text.strip()
        
        # Check cache first for instant playback
        for backend_name, _ in self.backends:
            cache_key = self._get_cache_key(text, backend_name)
            if cache_key in self.phrase_cache:
                cached_file = self.phrase_cache[cache_key]
                
                if cached_file == 'SYSTEM_IMMEDIATE':
                    # Use system TTS for immediate playback
                    return self._speak_system_immediate(text)
                elif os.path.exists(cached_file):
                    # Queue cached audio file
                    self._start_playback_thread()
                    self.audio_queue.put(cached_file)
                    self.is_playing = True
                    return True
        
        # No cache hit - generate audio with fastest available backend
        for backend_name, backend in self.backends:
            try:
                if backend_name == 'system' and backend:
                    return self._speak_system_immediate(text)
                else:
                    # Generate and play audio file
                    audio_file = self._generate_audio(text, backend_name, backend)
                    if audio_file:
                        # Cache for future use
                        cache_key = self._get_cache_key(text, backend_name)
                        self.phrase_cache[cache_key] = audio_file
                        
                        if audio_file == 'SYSTEM_IMMEDIATE':
                            return True
                        else:
                            # Queue for playback
                            self._start_playback_thread()
                            self.audio_queue.put(audio_file)
                            self.is_playing = True
                            return True
                            
            except Exception as e:
                print(f"[TTS] Backend {backend_name} failed: {e}")
                continue
        
        print("[TTS] All backends failed")
        return False
    
    def _speak_system_immediate(self, text: str) -> bool:
        """Use system TTS for immediate speaking (lowest latency)"""
        try:
            for backend_name, backend in self.backends:
                if backend_name == 'system' and backend:
                    # Run in separate thread to avoid blocking
                    def speak_async():
                        try:
                            backend.say(text)
                            backend.runAndWait()
                        except Exception as e:
                            print(f"[TTS] System TTS error: {e}")
                    
                    thread = threading.Thread(target=speak_async, daemon=True)
                    thread.start()
                    self.is_playing = True
                    return True
        except Exception as e:
            print(f"[TTS] System immediate speech failed: {e}")
        return False
    
    def stop(self):
        """Stop current speech immediately"""
        self.is_playing = False
        self.stop_playback.set()
        
        # Stop system TTS
        try:
            for backend_name, backend in self.backends:
                if backend_name == 'system' and backend:
                    backend.stop()
        except Exception:
            pass
        
        # Stop macOS audio playback
        try:
            subprocess.run(
                ['killall', 'afplay'],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False
            )
        except Exception:
            pass
        
        # Clear audio queue
        while not self.audio_queue.empty():
            try:
                self.audio_queue.get_nowait()
                self.audio_queue.task_done()
            except Empty:
                break
    
    def is_speaking(self) -> bool:
        """Check if currently speaking"""
        return self.is_playing
    
    def preload_common_phrases(self, phrases: list):
        """Preload common phrases for instant access"""
        for phrase in phrases:
            if phrase and phrase.strip():
                self._preprocess_phrase(phrase.strip())


# Backward compatibility class
class GoogleTTS:
    """Backward compatible wrapper for GoogleTTS"""
    
    def __init__(self, config):
        self.streaming_tts = StreamingTTS(config)
    
    def speak(self, text, voice_id=None, ssml=None, allow_barge_in=True):
        return self.streaming_tts.speak(text, voice_id, ssml, allow_barge_in)
    
    def stop(self):
        self.streaming_tts.stop()
