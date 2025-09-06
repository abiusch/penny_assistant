#!/usr/bin/env python3
"""
Streaming ElevenLabs TTS - Generates and plays chunks in parallel for faster speech
"""

import os
import tempfile
import subprocess
import threading
import time
import hashlib
import requests
import re
import queue
from pathlib import Path
from typing import Optional, Dict, Any, List
from concurrent.futures import ThreadPoolExecutor, as_completed

class StreamingElevenLabsTTS:
    """Streaming ElevenLabs TTS adapter - generates chunks in parallel"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config or {}
        self.tts_config = self.config.get('tts', {})
        self._error_logged = False
        
        # ElevenLabs configuration
        self.api_key = os.getenv("ELEVENLABS_API_KEY")
        if not self.api_key:
            raise ValueError("ELEVENLABS_API_KEY environment variable required")
        
        # Rachel voice ID
        self.voice_id = "21m00Tcm4TlvDq8ikWAM"
        self.base_url = "https://api.elevenlabs.io/v1"
        
        # Cache system
        self.cache_enabled = self.tts_config.get('cache_enabled', True)
        self.cache_dir = Path(tempfile.gettempdir()) / 'pennygpt_elevenlabs_cache'
        if self.cache_enabled:
            self.cache_dir.mkdir(exist_ok=True)
        
        self.memory_cache: Dict[str, str] = {}
        self.max_cache_phrase_length = 60
        
        # Streaming controls
        self._stop_speaking = threading.Event()
        self._audio_queue = queue.Queue()
        self._is_speaking = False
        
        # Personality settings (simplified for speed)
        self.personality_settings = {
            'sassy': {'stability': 0.25, 'similarity_boost': 0.7, 'style': 0.4},
            'tech_enthusiast': {'stability': 0.2, 'similarity_boost': 0.8, 'style': 0.5},
            'supportive': {'stability': 0.4, 'similarity_boost': 0.75, 'style': 0.3},
            'playful': {'stability': 0.3, 'similarity_boost': 0.7, 'style': 0.45},
            'default': {'stability': 0.3, 'similarity_boost': 0.7, 'style': 0.2}
        }
    
    def _detect_personality_mode(self, text: str) -> str:
        """Quick personality detection with proper priority order"""
        text_lower = text.lower()
        
        # Sassy indicators FIRST - override everything else
        if any(pattern in text_lower for pattern in ['obviously', 'of course', 'sure thing', 'yeah right', 'really?', 'seriously?']):
            return 'sassy'
        # Supportive indicators - before tech (anxiety about tech)
        elif any(pattern in text_lower for pattern in ['stressed', 'worried', 'help me', 'struggling', 'difficult', 'overwhelmed']):
            return 'supportive'
        # Tech enthusiasm indicators - only if no sassy/support
        elif any(pattern in text_lower for pattern in ['algorithm', 'neural', 'quantum', 'programming', 'ai', 'machine learning']):
            return 'tech_enthusiast'
        # Playful indicators
        elif any(pattern in text_lower for pattern in ['haha', 'funny', 'silly', 'ridiculous', 'crazy']):
            return 'playful'
        
        return 'default'
    
    def _clean_text_for_speech(self, text: str) -> str:
        """Clean text quickly"""
        text = text.replace('**', '').replace('*', '').replace('#', '').replace('`', '')
        text = re.sub(r'^\d+\.\s*', '', text, flags=re.MULTILINE)
        text = re.sub(r'\s+', ' ', text).strip()
        return text
    
    def _split_into_chunks(self, text: str) -> List[str]:
        """Split text into optimal chunks for streaming"""
        text = self._clean_text_for_speech(text)
        
        # Very short chunks for streaming (150-200 chars)
        max_length = 180
        
        if len(text) <= max_length:
            return [text]
        
        # Split at sentence boundaries
        sentences = text.replace('. ', '.\n').replace('? ', '?\n').replace('! ', '!\n').split('\n')
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            if len(current_chunk + sentence) < max_length:
                current_chunk += sentence + " "
            else:
                if current_chunk.strip():
                    chunks.append(current_chunk.strip())
                current_chunk = sentence + " "
        
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def _synthesize_chunk(self, text: str, chunk_index: int) -> tuple:
        """Synthesize a single chunk - returns (index, audio_file_path)"""
        try:
            personality = self._detect_personality_mode(text)
            voice_settings = self.personality_settings.get(personality, self.personality_settings['default'])
            
            # API request
            url = f"{self.base_url}/text-to-speech/{self.voice_id}"
            headers = {
                "Accept": "audio/mpeg",
                "Content-Type": "application/json",
                "xi-api-key": self.api_key
            }
            
            data = {
                "text": text,
                "model_id": "eleven_monolingual_v1",
                "voice_settings": voice_settings
            }
            
            response = requests.post(url, json=data, headers=headers, timeout=10)
            
            if response.status_code == 200:
                # Save to temporary file
                with tempfile.NamedTemporaryFile(suffix=f"_chunk_{chunk_index}.mp3", delete=False) as f:
                    f.write(response.content)
                    return (chunk_index, f.name)
            else:
                print(f"[ElevenLabs] Chunk {chunk_index} API error: {response.status_code}")
                return (chunk_index, None)
                
        except Exception as e:
            print(f"[ElevenLabs] Chunk {chunk_index} synthesis failed: {e}")
            return (chunk_index, None)
    
    def _play_audio_file(self, file_path: str) -> bool:
        """Play audio file"""
        if not file_path:
            return False
            
        try:
            result = subprocess.run(
                ["afplay", file_path],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=15,
                check=True
            )
            return True
        except Exception as e:
            print(f"[ElevenLabs] Playback failed: {e}")
            return False
    
    def speak(self, text: str, voice_id=None, ssml=None, allow_barge_in=True) -> bool:
        """Speak with streaming synthesis and playback"""
        if not text or not text.strip():
            return True
        
        text = text.strip()
        self.stop()  # Stop any current speech
        
        # Split into chunks
        chunks = self._split_into_chunks(text)
        
        if len(chunks) == 1:
            # Single chunk - just synthesize and play
            print(f"[ElevenLabs] Single chunk")
            chunk_index, audio_file = self._synthesize_chunk(chunks[0], 0)
            return self._play_audio_file(audio_file)
        
        print(f"[ElevenLabs] Streaming {len(chunks)} chunks")
        self._is_speaking = True
        
        # Start parallel synthesis of all chunks
        with ThreadPoolExecutor(max_workers=3) as executor:
            # Submit all synthesis tasks
            future_to_chunk = {
                executor.submit(self._synthesize_chunk, chunk, i): i 
                for i, chunk in enumerate(chunks)
            }
            
            # Collect results as they complete
            audio_files = {}
            
            for future in as_completed(future_to_chunk):
                if self._stop_speaking.is_set():
                    break
                    
                chunk_index, audio_file = future.result()
                if audio_file:
                    audio_files[chunk_index] = audio_file
                    
                    # If this is the next chunk to play, start playing
                    if chunk_index == 0 or (chunk_index > 0 and (chunk_index - 1) in audio_files):
                        self._play_queued_chunks(audio_files, chunks)
        
        self._is_speaking = False
        return True
    
    def _play_queued_chunks(self, audio_files: dict, chunks: list):
        """Play chunks in order as they become available"""
        for i in range(len(chunks)):
            if self._stop_speaking.is_set():
                break
                
            if i in audio_files:
                print(f"[ElevenLabs] Playing chunk {i+1}/{len(chunks)}")
                self._play_audio_file(audio_files[i])
                # Small pause between chunks
                time.sleep(0.1)
            else:
                # Wait for chunk to be ready
                max_wait = 5  # seconds
                waited = 0
                while i not in audio_files and waited < max_wait and not self._stop_speaking.is_set():
                    time.sleep(0.1)
                    waited += 0.1
                
                if i in audio_files:
                    print(f"[ElevenLabs] Playing chunk {i+1}/{len(chunks)}")
                    self._play_audio_file(audio_files[i])
                else:
                    print(f"[ElevenLabs] Chunk {i+1} timeout")
                    break
    
    def stop(self):
        """Stop current speech"""
        self._stop_speaking.set()
        self._is_speaking = False
        
        # Kill any afplay processes
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
        
        # Reset stop signal
        self._stop_speaking.clear()
    
    def is_speaking(self) -> bool:
        """Check if currently speaking"""
        return self._is_speaking
    
    def clear_cache(self):
        """Clear TTS cache"""
        self.memory_cache.clear()
        print("[ElevenLabs] Cache cleared")
