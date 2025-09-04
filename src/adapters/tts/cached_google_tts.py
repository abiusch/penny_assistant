"""
Enhanced Google TTS Adapter with Caching
Integrates TTS cache for perceived latency improvements while preserving all existing behavior.
"""

import os
import time
import tempfile
from typing import Optional
from .cache import get_tts_cache, TTSCache

class CachedGoogleTTS:
    """
    Enhanced Google TTS adapter with intelligent caching.
    
    Provides instant playback for cached phrases while maintaining
    all existing functionality including barge-in behavior.
    """
    
    def __init__(self, config: dict):
        self.config = config
        self.cache = get_tts_cache()
        
        # Initialize the original TTS adapter
        from .google_tts_adapter import GoogleTTS
        self.base_tts = GoogleTTS(config)
        
        # Prime cache with common phrases on startup
        self._prime_cache_if_needed()
    
    def _prime_cache_if_needed(self):
        """Prime cache with common phrases on first startup"""
        # Only prime if cache is empty (first run)
        stats = self.cache.get_stats()
        if stats['cached_phrases'] == 0:
            print("Priming TTS cache with common phrases...")
            self.cache.prime_common_phrases()
    
    def speak(self, text: str, voice_id: str = None, ssml: bool = False, 
              allow_barge_in: bool = True, output_file: str = None) -> bool:
        """
        Enhanced speak method with intelligent caching.
        
        Checks cache first for instant playback, falls back to generation,
        and caches the result for future use.
        """
        
        # Handle SSML and special cases - bypass cache
        if ssml or not text or len(text.strip()) > 100:
            return self._speak_direct(text, voice_id, ssml, allow_barge_in, output_file)
        
        text_clean = text.strip()
        cache_key_voice = voice_id or "default"
        
        # Try cache first
        cached_file = self.cache.get_cached_audio(text_clean, cache_key_voice)
        
        if cached_file and os.path.exists(cached_file):
            # Cache hit - instant playback!
            return self._play_cached_audio(cached_file, allow_barge_in, output_file)
        
        # Cache miss - generate and cache
        return self._speak_and_cache(text, voice_id, ssml, allow_barge_in, output_file)
    
    def _speak_direct(self, text: str, voice_id: str = None, ssml: bool = False,
                     allow_barge_in: bool = True, output_file: str = None) -> bool:
        """Direct TTS without caching (for SSML, long text, etc.)"""
        return self.base_tts.speak(text, voice_id, ssml, allow_barge_in, output_file)
    
    def _play_cached_audio(self, cached_file: str, allow_barge_in: bool = True, 
                          output_file: str = None) -> bool:
        """Play cached audio file"""
        try:
            if output_file:
                # Copy cached file to output location
                import shutil
                shutil.copy2(cached_file, output_file)
                return True
            else:
                # Play the cached audio directly
                return self.base_tts._play_audio_file(cached_file, allow_barge_in)
        
        except Exception as e:
            print(f"Failed to play cached audio: {e}")
            return False
    
    def _speak_and_cache(self, text: str, voice_id: str = None, ssml: bool = False,
                        allow_barge_in: bool = True, output_file: str = None) -> bool:
        """Generate TTS and cache the result"""
        
        # Generate to temporary file for caching
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
            temp_path = temp_file.name
        
        try:
            # Generate TTS to temporary file
            start_time = time.time()
            success = self.base_tts.speak(text, voice_id, ssml, allow_barge_in=False, 
                                        output_file=temp_path)
            
            if not success:
                return False
            
            generation_time = time.time() - start_time
            
            # Cache the generated audio (if appropriate)
            text_clean = text.strip()
            if self.cache._should_cache(text_clean):
                self.cache.cache_generated_audio(text_clean, temp_path, 
                                               generation_time, voice_id or "default")
            
            # Handle output
            if output_file:
                import shutil
                shutil.copy2(temp_path, output_file)
                result = True
            else:
                # Play the generated audio
                result = self.base_tts._play_audio_file(temp_path, allow_barge_in)
            
            return result
            
        except Exception as e:
            print(f"TTS generation failed: {e}")
            return False
        
        finally:
            # Clean up temporary file
            try:
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
            except Exception:
                pass
    
    def request_pregeneration(self, text: str, voice_id: str = None):
        """Request background pregeneration of a phrase"""
        self.cache.request_pregeneration(text, voice_id or "default")
    
    def get_cache_stats(self) -> dict:
        """Get caching statistics"""
        return self.cache.get_stats()
    
    def warm_cache_for_conversation(self, phrases: list):
        """Warm cache with phrases likely to be used in conversation"""
        for phrase in phrases:
            self.request_pregeneration(phrase)
    
    # Pass through methods that don't need caching
    def get_voices(self):
        """Get available voices"""
        return self.base_tts.get_voices()
    
    def set_voice(self, voice_id: str):
        """Set default voice"""
        return self.base_tts.set_voice(voice_id)
    
    def test_speech(self, test_phrase: str = "This is a test of the speech system."):
        """Test speech with caching"""
        return self.speak(test_phrase)
    
    def shutdown(self):
        """Shutdown TTS and cache"""
        self.cache.shutdown()
        if hasattr(self.base_tts, 'shutdown'):
            self.base_tts.shutdown()

# Convenience function for backward compatibility
def create_cached_tts(config: dict) -> CachedGoogleTTS:
    """Create a cached TTS instance"""
    return CachedGoogleTTS(config)
