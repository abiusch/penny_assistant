"""
Tests for TTS Caching System
Ensures caching improves latency while preserving all existing behavior.
"""

import pytest
import tempfile
import os
import time
from unittest.mock import Mock, patch, MagicMock
import threading

from adapters.tts.cache import TTSCache, CachedPhrase
from adapters.tts.cached_google_tts import CachedGoogleTTS

class TestTTSCache:
    
    def setup_method(self):
        """Setup test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.cache = TTSCache(
            cache_dir=self.temp_dir,
            max_phrase_duration=2.0,
            max_cache_size_mb=1,  # Small for testing
            enable_pregeneration=False  # Disable for testing
        )
    
    def teardown_method(self):
        """Cleanup test environment"""
        self.cache.shutdown()
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_cache_key_generation(self):
        """Test cache key generation consistency"""
        key1 = self.cache._generate_cache_key("Hello", "default")
        key2 = self.cache._generate_cache_key("hello", "default")
        key3 = self.cache._generate_cache_key("Hello", "female")
        
        assert key1 == key2  # Case insensitive
        assert key1 != key3  # Different voice
        assert len(key1) == 32  # MD5 length
    
    def test_duration_estimation(self):
        """Test speech duration estimation"""
        short_text = "Hello"
        long_text = "This is a much longer sentence with many words"
        
        short_duration = self.cache._estimate_duration(short_text)
        long_duration = self.cache._estimate_duration(long_text)
        
        assert short_duration < long_duration
        assert short_duration > 0
    
    def test_should_cache_logic(self):
        """Test caching decision logic"""
        assert self.cache._should_cache("Hello")  # Short phrase
        assert self.cache._should_cache("I'm sorry")  # Common phrase
        assert not self.cache._should_cache("")  # Empty string
        assert not self.cache._should_cache("A" * 200)  # Very long text
    
    def test_cache_miss(self):
        """Test cache miss behavior"""
        result = self.cache.get_cached_audio("Nonexistent phrase")
        assert result is None
        assert self.cache.stats['misses'] == 1
        assert self.cache.stats['hits'] == 0
    
    def test_cache_storage_and_retrieval(self):
        """Test storing and retrieving cached audio"""
        # Create a test audio file
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
            temp_file.write(b"fake audio data")
            test_audio_path = temp_file.name
        
        try:
            # Cache the audio
            text = "Hello world"
            success = self.cache.cache_generated_audio(text, test_audio_path, 1.0)
            assert success
            
            # Retrieve from cache
            cached_path = self.cache.get_cached_audio(text)
            assert cached_path is not None
            assert os.path.exists(cached_path)
            assert self.cache.stats['hits'] == 1
            
            # Verify file content
            with open(cached_path, 'rb') as f:
                assert f.read() == b"fake audio data"
        
        finally:
            os.unlink(test_audio_path)
    
    def test_cache_eviction(self):
        """Test LRU cache eviction"""
        # Fill cache beyond size limit
        audio_files = []
        
        try:
            for i in range(10):
                with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                    # Write some data to make file size meaningful
                    temp_file.write(b"x" * 1024 * 100)  # 100KB per file
                    audio_files.append(temp_file.name)
                
                text = f"Test phrase {i}"
                self.cache.cache_generated_audio(text, temp_file.name, 0.5)
            
            # Check that eviction occurred
            assert self.cache.stats['evictions'] > 0
            assert len(self.cache.cache) < 10
        
        finally:
            for path in audio_files:
                try:
                    os.unlink(path)
                except FileNotFoundError:
                    pass
    
    def test_pregeneration_queue(self):
        """Test background pregeneration queuing"""
        cache_with_bg = TTSCache(
            cache_dir=self.temp_dir + "_bg",
            enable_pregeneration=True
        )
        
        try:
            # Request pregeneration
            cache_with_bg.request_pregeneration("Hello")
            cache_with_bg.request_pregeneration("Thank you", priority=True)
            
            # Check queue is not empty
            assert not cache_with_bg.pregeneration_queue.empty()
            
        finally:
            cache_with_bg.shutdown()
    
    def test_statistics_tracking(self):
        """Test cache statistics"""
        stats = self.cache.get_stats()
        
        # Initial stats
        assert stats['hits'] == 0
        assert stats['misses'] == 0
        assert stats['cached_phrases'] == 0
        assert stats['hit_rate'] == 0.0
        
        # Test a miss
        self.cache.get_cached_audio("Missing")
        stats = self.cache.get_stats()
        assert stats['misses'] == 1
        assert stats['hit_rate'] == 0.0

class TestCachedGoogleTTS:
    
    def setup_method(self):
        """Setup test environment"""
        self.temp_dir = tempfile.mkdtemp()
        
        # Mock the base GoogleTTS adapter
        self.mock_base_tts = Mock()
        self.mock_base_tts.speak.return_value = True
        
        # Create cached TTS with mocked base
        with patch('adapters.tts.cached_google_tts.GoogleTTS', return_value=self.mock_base_tts):
            with patch('adapters.tts.cached_google_tts.get_tts_cache') as mock_get_cache:
                self.mock_cache = Mock(spec=TTSCache)
                mock_get_cache.return_value = self.mock_cache
                
                self.cached_tts = CachedGoogleTTS({})
    
    def test_cache_hit_path(self):
        """Test that cache hits bypass TTS generation"""
        # Setup cache to return a file path
        self.mock_cache.get_cached_audio.return_value = "/fake/cached/file.wav"
        
        with patch('os.path.exists', return_value=True):
            with patch.object(self.cached_tts, '_play_cached_audio', return_value=True) as mock_play:
                result = self.cached_tts.speak("Hello")
                
                assert result is True
                mock_play.assert_called_once()
                self.mock_base_tts.speak.assert_not_called()  # Should bypass generation
    
    def test_cache_miss_path(self):
        """Test that cache misses fall back to generation"""
        # Setup cache to return None (cache miss)
        self.mock_cache.get_cached_audio.return_value = None
        
        with patch.object(self.cached_tts, '_speak_and_cache', return_value=True) as mock_speak_cache:
            result = self.cached_tts.speak("New phrase")
            
            assert result is True
            mock_speak_cache.assert_called_once()
    
    def test_ssml_bypass_cache(self):
        """Test that SSML bypasses cache"""
        with patch.object(self.cached_tts, '_speak_direct', return_value=True) as mock_direct:
            result = self.cached_tts.speak("<speak>Hello</speak>", ssml=True)
            
            assert result is True
            mock_direct.assert_called_once()
            self.mock_cache.get_cached_audio.assert_not_called()
    
    def test_long_text_bypass_cache(self):
        """Test that long text bypasses cache"""
        long_text = "A" * 200  # Very long text
        
        with patch.object(self.cached_tts, '_speak_direct', return_value=True) as mock_direct:
            result = self.cached_tts.speak(long_text)
            
            assert result is True
            mock_direct.assert_called_once()
    
    def test_pregeneration_request(self):
        """Test requesting pregeneration"""
        self.cached_tts.request_pregeneration("Thank you")
        
        self.mock_cache.request_pregeneration.assert_called_once_with("Thank you", "default")
    
    def test_cache_warming(self):
        """Test warming cache with conversation phrases"""
        phrases = ["Hello", "How are you?", "Goodbye"]
        
        self.cached_tts.warm_cache_for_conversation(phrases)
        
        assert self.mock_cache.request_pregeneration.call_count == 3

class TestTTSCacheIntegration:
    """Integration tests with real file operations"""
    
    def setup_method(self):
        """Setup integration test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.cache = TTSCache(
            cache_dir=self.temp_dir,
            enable_pregeneration=False
        )
    
    def teardown_method(self):
        """Cleanup"""
        self.cache.shutdown()
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_end_to_end_caching(self):
        """Test complete cache workflow"""
        # Create a mock audio file
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
            temp_file.write(b"mock audio data for testing")
            test_audio = temp_file.name
        
        try:
            text = "Hello from cache test"
            
            # First call - cache miss, should generate and cache
            cached_result = self.cache.cache_generated_audio(text, test_audio, 1.0)
            assert cached_result is True
            
            # Second call - cache hit, should return cached file
            cached_file = self.cache.get_cached_audio(text)
            assert cached_file is not None
            assert os.path.exists(cached_file)
            
            # Verify cached content
            with open(cached_file, 'rb') as f:
                content = f.read()
                assert content == b"mock audio data for testing"
            
            # Check statistics
            stats = self.cache.get_stats()
            assert stats['hits'] == 1
            assert stats['cached_phrases'] == 1
            assert stats['hit_rate'] > 0
        
        finally:
            os.unlink(test_audio)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
