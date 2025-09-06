#!/usr/bin/env python3
"""
ElevenLabs TTS Adapter with Penny Personality Integration (FIXED)
Replaces Google TTS with natural-sounding voice that adapts to Penny's personality modes
"""

import os
import tempfile
import subprocess
import threading
import time
import hashlib
import requests
import re
from pathlib import Path
from typing import Optional, Dict, Any

class ElevenLabsTTS:
    """ElevenLabs TTS adapter with Penny personality integration"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config or {}
        self.tts_config = self.config.get('tts', {})
        self._last_file = None
        self._error_logged = False
        
        # ElevenLabs configuration
        self.api_key = os.getenv("ELEVENLABS_API_KEY")
        if not self.api_key:
            raise ValueError("ELEVENLABS_API_KEY environment variable required")
        
        # Rachel voice ID (our winner)
        self.voice_id = "21m00Tcm4TlvDq8ikWAM"
        self.base_url = "https://api.elevenlabs.io/v1"
        
        # Initialize cache system (same as Google TTS)
        self.cache_enabled = self.tts_config.get('cache_enabled', True)
        self.cache_dir = Path(tempfile.gettempdir()) / 'pennygpt_elevenlabs_cache'
        if self.cache_enabled:
            self.cache_dir.mkdir(exist_ok=True)
        
        self.memory_cache: Dict[str, str] = {}
        self.max_cache_phrase_length = 60
        
        # Background playback thread
        self._playback_thread = None
        self._stop_playback = threading.Event()
        
        # Simplified voice settings - focus on quality over personality variations
        self.voice_settings = {
            'stability': 0.4,       # Good balance of consistency and variation
            'similarity_boost': 0.8, # Maintain Rachel's character
            'style': 0.3,           # Natural expressiveness
            'use_speaker_boost': True
        }
    
    def _detect_personality_mode(self, text: str) -> str:
        """Detect Penny's personality mode from text content"""
        text_lower = text.lower()
        
        # Check sassy indicators FIRST - these override everything else
        sassy_patterns = [
            'obviously', 'of course', 'sure thing', 'yeah right', 
            'really?', 'seriously?', 'great job', 'nice work',
            'brilliant', 'genius', 'perfect', 'wonderful',
            'clearly', 'apparently', 'supposedly'
        ]
        if any(pattern in text_lower for pattern in sassy_patterns):
            return 'sassy'
        
        # Supportive indicators - check before tech (anxiety about tech topics)
        support_patterns = [
            'stressed', 'worried', 'anxious', 'help me',
            'struggling', 'difficult', 'hard time', 'overwhelmed',
            'support', 'advice', 'guidance'
        ]
        if any(pattern in text_lower for pattern in support_patterns):
            return 'supportive'
        
        # Tech enthusiasm indicators - only if no sassy/support detected
        tech_patterns = [
            'algorithm', 'neural', 'quantum', 'machine learning',
            'ai', 'artificial intelligence', 'deep learning',
            'programming', 'code', 'software', 'technology',
            'computer', 'data science', 'blockchain'
        ]
        if any(pattern in text_lower for pattern in tech_patterns):
            return 'tech_enthusiast'
        
        # Playful indicators
        playful_patterns = [
            'haha', 'funny', 'silly', 'ridiculous', 'crazy',
            'weird', 'strange', 'amusing', 'hilarious'
        ]
        if any(pattern in text_lower for pattern in playful_patterns):
            return 'playful'
        
        return 'default'
    
    def _clean_text_for_speech(self, text: str) -> str:
        """Clean text to make it more natural for speech"""
        # Remove markdown formatting
        text = text.replace('**', '')  # Remove bold markers
        text = text.replace('*', '')   # Remove bullet points and italics
        text = text.replace('#', '')   # Remove headers
        text = text.replace('`', '')   # Remove code backticks
        
        # Replace numbered lists with natural speech
        text = re.sub(r'^\d+\.\s*', '', text, flags=re.MULTILINE)
        
        # Clean up extra whitespace
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        return text
    
    def _get_cache_key(self, text: str, personality: str) -> str:
        """Generate cache key including personality mode"""
        combined = f"{text}|{personality}"
        return hashlib.md5(combined.encode('utf-8')).hexdigest()
    
    def _get_cached_file(self, text: str, personality: str) -> Optional[str]:
        """Get cached audio file if exists"""
        if not self.cache_enabled:
            return None
        
        cache_key = self._get_cache_key(text, personality)
        
        # Check memory cache for short phrases
        if len(text) <= self.max_cache_phrase_length:
            return self.memory_cache.get(cache_key)
        
        # Check disk cache
        cache_file = self.cache_dir / f"{cache_key}.mp3"
        if cache_file.exists():
            return str(cache_file)
        
        return None
    
    def _cache_file(self, text: str, personality: str, file_path: str):
        """Cache the audio file with personality"""
        if not self.cache_enabled:
            return
        
        cache_key = self._get_cache_key(text, personality)
        
        # Cache short phrases in memory
        if len(text) <= self.max_cache_phrase_length:
            self.memory_cache[cache_key] = file_path
        
        # Cache to disk
        try:
            cache_file = self.cache_dir / f"{cache_key}.mp3"
            if not cache_file.exists():
                import shutil
                shutil.copy2(file_path, cache_file)
        except Exception as e:
            if not self._error_logged:
                print(f"[ElevenLabs] Cache write failed: {e}")
    
    def _synthesize_audio(self, text: str, personality: str = 'default') -> Optional[str]:
        """Synthesize text using ElevenLabs API with consistent quality settings"""
        try:
            # Check cache first
            cache_key = hashlib.md5(text.encode('utf-8')).hexdigest()
            cached_file = self._get_cached_file(text, 'default')  # Use single cache key
            if cached_file and os.path.exists(cached_file):
                return cached_file
            
            # API request with simplified settings
            url = f"{self.base_url}/text-to-speech/{self.voice_id}"
            headers = {
                "Accept": "audio/mpeg",
                "Content-Type": "application/json",
                "xi-api-key": self.api_key
            }
            
            data = {
                "text": text,
                "model_id": "eleven_monolingual_v1",
                "voice_settings": self.voice_settings  # Use single optimized settings
            }
            
            response = requests.post(url, json=data, headers=headers)
            
            if response.status_code == 200:
                # Save to temporary file
                with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
                    f.write(response.content)
                    self._last_file = f.name
                    
                    # Cache the result
                    self._cache_file(text, 'default', f.name)
                    
                    return f.name
            else:
                if not self._error_logged:
                    print(f"[ElevenLabs] API error: {response.status_code}")
                    if response.status_code == 401:
                        print("[ElevenLabs] Check your API key")
                    elif response.status_code == 429:
                        print("[ElevenLabs] Rate limit exceeded")
                return None
                
        except Exception as e:
            if not self._error_logged:
                print(f"[ElevenLabs] Synthesis failed: {e}")
                self._error_logged = True
            return None
    
    def speak(self, text: str, voice_id=None, ssml=None, allow_barge_in=True) -> bool:
        """Speak text with automatic personality detection and chunking for long text"""
        if not text or not text.strip():
            return True
        
        text = text.strip()
        
        # Clean text for natural speech (remove markdown, symbols, etc.)
        text = self._clean_text_for_speech(text)
        
        # Stop current playback
        self.stop()
        
        # For very long text, split into chunks
        max_length = 300  # Shorter chunks for faster synthesis
        if len(text) > max_length:
            # Split at sentence boundaries
            sentences = text.replace('. ', '.\n').replace('? ', '?\n').replace('! ', '!\n').split('\n')
            chunks = []
            current_chunk = ""
            
            for sentence in sentences:
                if len(current_chunk + sentence) < max_length:
                    current_chunk += sentence + " "
                else:
                    if current_chunk:
                        chunks.append(current_chunk.strip())
                    current_chunk = sentence + " "
            
            if current_chunk:
                chunks.append(current_chunk.strip())
            
            print(f"[ElevenLabs] Splitting long text into {len(chunks)} chunks")
            
            # Speak each chunk
            for i, chunk in enumerate(chunks):
                if chunk.strip():
                    print(f"[ElevenLabs] Speaking chunk {i+1}/{len(chunks)}")
                    success = self._speak_chunk(chunk)
                    if not success:
                        print(f"[ElevenLabs] Chunk {i+1} failed")
                        return False
            return True
        else:
            # Short text - speak normally
            return self._speak_chunk(text)
    
    def _speak_chunk(self, text: str) -> bool:
        """Speak a single chunk of text"""
        # Detect personality mode from text
        personality = self._detect_personality_mode(text)
        
        # Debug output
        if personality != 'default':
            print(f"[Penny Voice] Using {personality} mode")
        
        # Synthesize with personality
        audio_file = self._synthesize_audio(text, personality)
        if not audio_file:
            return False
        
        # Play synchronously
        try:
            result = subprocess.run(
                ["afplay", audio_file],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=30
            )
            return result.returncode == 0
        except subprocess.TimeoutExpired:
            print("[ElevenLabs] Chunk playback timeout")
            return False
        except Exception as e:
            if not self._error_logged:
                print(f"[ElevenLabs] Chunk playback error: {e}")
            return False
    
    def stop(self):
        """Stop current playback"""
        self._stop_playback.set()
        
        if self._playback_thread and self._playback_thread.is_alive():
            self._playback_thread.join(timeout=1.0)
        
        # Fallback: kill afplay processes
        try:
            subprocess.run(
                ["killall", "afplay"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
                timeout=2.0
            )
        except Exception:
            pass
    
    def is_speaking(self) -> bool:
        """Check if currently speaking"""
        return (self._playback_thread and 
                self._playback_thread.is_alive() and 
                not self._stop_playback.is_set())
    
    def clear_cache(self):
        """Clear TTS cache"""
        self.memory_cache.clear()
        
        if self.cache_enabled and self.cache_dir.exists():
            try:
                import shutil
                shutil.rmtree(self.cache_dir)
                self.cache_dir.mkdir(exist_ok=True)
                print("[ElevenLabs] Cache cleared")
            except Exception as e:
                print(f"[ElevenLabs] Cache clear failed: {e}")
    
    def __del__(self):
        """Cleanup"""
        try:
            self.stop()
        except Exception:
            pass
