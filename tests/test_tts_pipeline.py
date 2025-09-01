"""Tests for TTS pipeline resilience and caching."""

import pytest
import tempfile
import os
import threading
import time
from unittest.mock import patch, MagicMock, call
from pathlib import Path

from src.adapters.tts.google_tts_adapter import GoogleTTS


class TestGoogleTTSResilience:
    """Test TTS adapter resilience and error handling."""

    @pytest.fixture
    def config(self):
        """Sample configuration for testing."""
        return {
            "tts": {
                "cache_enabled": True,
                "preload_common_phrases": False
            }
        }

    @pytest.fixture
    def tts_adapter(self, config):
        """Create TTS adapter instance."""
        return GoogleTTS(config)

    def test_initialization(self, tts_adapter):
        """Test adapter initialization."""
        assert tts_adapter.cache_enabled is True
        assert tts_adapter.cache_dir.name == 'pennygpt_tts_cache'
        assert isinstance(tts_adapter.memory_cache, dict)
        assert tts_adapter.max_cache_phrase_length == 60

    def test_cache_key_generation(self, tts_adapter):
        """Test cache key generation consistency."""
        text = "Hello, world!"
        key1 = tts_adapter._get_cache_key(text)
        key2 = tts_adapter._get_cache_key(text)
        assert key1 == key2
        assert len(key1) == 32  # MD5 hash length
        
        # Different text should generate different keys
        key3 = tts_adapter._get_cache_key("Different text")
        assert key1 != key3

    @patch('src.adapters.tts.google_tts_adapter.GTTS_AVAILABLE', False)
    def test_no_gtts_graceful_degradation(self, config):
        """Test graceful handling when gTTS is not available."""
        tts = GoogleTTS(config)
        result = tts.speak("Hello, world!")
        assert result is False

    @patch('src.adapters.tts.google_tts_adapter.gTTS')
    def test_synthesis_success(self, mock_gtts, tts_adapter):
        """Test successful synthesis."""
        mock_gtts_instance = MagicMock()
        mock_gtts.return_value = mock_gtts_instance
        
        with patch('tempfile.NamedTemporaryFile') as mock_temp, \
             patch('threading.Thread') as mock_thread:
            
            mock_file = MagicMock()
            mock_file.name = '/tmp/test.mp3'
            mock_temp.return_value.__enter__.return_value = mock_file
            
            result = tts_adapter.speak("Test message")
            
            assert result is True
            mock_gtts.assert_called_once_with(text="Test message", lang="en")
            mock_gtts_instance.save.assert_called_once_with('/tmp/test.mp3')

    @patch('src.adapters.tts.google_tts_adapter.gTTS')
    def test_synthesis_error_handling(self, mock_gtts, tts_adapter):
        """Test error handling during synthesis."""
        mock_gtts.side_effect = Exception("Network error")
        
        result = tts_adapter.speak("Test message")
        
        assert result is False
        # Error should be logged only once
        assert tts_adapter._error_logged is True

    def test_cache_functionality(self, tts_adapter):
        """Test memory cache functionality."""
        short_text = "Hello!"  # Under 60 chars
        cache_key = tts_adapter._get_cache_key(short_text)
        test_file = "/tmp/test.mp3"
        
        # Cache the file
        tts_adapter._cache_file(short_text, test_file)
        
        # Should be in memory cache
        assert cache_key in tts_adapter.memory_cache
        assert tts_adapter.memory_cache[cache_key] == test_file
        
        # Should retrieve from cache
        cached_file = tts_adapter._get_cached_file(short_text)
        assert cached_file == test_file

    def test_cache_disabled(self):
        """Test behavior when cache is disabled."""
        config = {"tts": {"cache_enabled": False}}
        tts = GoogleTTS(config)
        
        assert tts.cache_enabled is False
        
        # Should not cache
        tts._cache_file("Test", "/tmp/test.mp3")
        assert len(tts.memory_cache) == 0
        
        # Should not retrieve from cache
        cached_file = tts._get_cached_file("Test")
        assert cached_file is None

    @patch('subprocess.Popen')
    def test_background_playback(self, mock_popen, tts_adapter):
        """Test background audio playback."""
        mock_process = MagicMock()
        mock_process.poll.return_value = None  # Still running
        mock_process.returncode = 0  # Success
        mock_popen.return_value = mock_process
        
        # Simulate process completing after a short time
        def poll_side_effect():
            time.sleep(0.1)  # Simulate playback time
            return 0  # Process completed
        mock_process.poll.side_effect = [None, None, 0]  # Running, then complete
        
        result = tts_adapter._play_audio_file("/tmp/test.mp3")
        
        assert result is True
        mock_popen.assert_called_once_with(
            ["afplay", "/tmp/test.mp3"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

    @patch('subprocess.Popen')
    def test_playback_error_handling(self, mock_popen, tts_adapter):
        """Test error handling during playback."""
        mock_popen.side_effect = Exception("afplay not found")
        
        result = tts_adapter._play_audio_file("/tmp/test.mp3")
        
        assert result is False
        assert tts_adapter._error_logged is True

    def test_stop_functionality(self, tts_adapter):
        """Test stop functionality."""
        # Start a mock playback thread
        mock_thread = MagicMock()
        mock_thread.is_alive.return_value = True
        tts_adapter._playback_thread = mock_thread
        
        with patch('subprocess.run') as mock_run:
            tts_adapter.stop()
            
            # Should signal stop
            assert tts_adapter._stop_playback.is_set()
            
            # Should try to join thread
            mock_thread.join.assert_called_once_with(timeout=1.0)
            
            # Should killall afplay as fallback
            mock_run.assert_called_once()

    def test_is_speaking(self, tts_adapter):
        """Test is_speaking status check."""
        # No thread - not speaking
        assert tts_adapter.is_speaking() is False
        
        # Mock active thread
        mock_thread = MagicMock()
        mock_thread.is_alive.return_value = True
        tts_adapter._playback_thread = mock_thread
        tts_adapter._stop_playback.clear()
        
        assert tts_adapter.is_speaking() is True
        
        # Stopped thread
        tts_adapter._stop_playback.set()
        assert tts_adapter.is_speaking() is False

    def test_empty_text_handling(self, tts_adapter):
        """Test handling of empty or whitespace-only text."""
        assert tts_adapter.speak("") is True
        assert tts_adapter.speak("   ") is True
        assert tts_adapter.speak(None) is True

    @patch('src.adapters.tts.google_tts_adapter.gTTS')
    def test_preload_common_phrases(self, mock_gtts, config):
        """Test preloading common phrases."""
        config["tts"]["preload_common_phrases"] = True
        tts = GoogleTTS(config)
        
        mock_gtts_instance = MagicMock()
        mock_gtts.return_value = mock_gtts_instance
        
        with patch('tempfile.NamedTemporaryFile') as mock_temp:
            mock_file = MagicMock()
            mock_file.name = '/tmp/test.mp3'
            mock_temp.return_value.__enter__.return_value = mock_file
            
            tts.preload_common_phrases()
            
            # Should have called gTTS multiple times for common phrases
            assert mock_gtts.call_count >= 5  # At least 5 common phrases

    def test_clear_cache(self, tts_adapter):
        """Test cache clearing functionality."""
        # Add something to memory cache
        tts_adapter.memory_cache["test"] = "/tmp/test.mp3"
        
        with patch('shutil.rmtree') as mock_rmtree:
            tts_adapter.clear_cache()
            
            # Memory cache should be cleared
            assert len(tts_adapter.memory_cache) == 0
            
            # Should attempt to clear disk cache
            mock_rmtree.assert_called_once_with(tts_adapter.cache_dir)

    @patch('src.adapters.tts.google_tts_adapter.gTTS')
    def test_integration_flow(self, mock_gtts, tts_adapter):
        """Test complete integration flow."""
        mock_gtts_instance = MagicMock()
        mock_gtts.return_value = mock_gtts_instance
        
        with patch('tempfile.NamedTemporaryFile') as mock_temp, \
             patch('threading.Thread') as mock_thread, \
             patch.object(tts_adapter, '_background_play') as mock_bg_play:
            
            mock_file = MagicMock()
            mock_file.name = '/tmp/test.mp3'
            mock_temp.return_value.__enter__.return_value = mock_file
            
            # First call should synthesize
            result1 = tts_adapter.speak("Hello, world!")
            assert result1 is True
            mock_gtts.assert_called_once()
            
            # Mock the cache hit for second call
            with patch.object(tts_adapter, '_get_cached_file', return_value='/tmp/test.mp3'):
                result2 = tts_adapter.speak("Hello, world!")
                assert result2 is True
                # Should not call gTTS again due to cache hit
                assert mock_gtts.call_count == 1


class TestTTSPipelineNoCrash:
    """Test that TTS pipeline never crashes the application."""

    def test_no_crash_on_any_error(self):
        """Test that any TTS error doesn't crash the pipeline."""
        config = {"tts": {"cache_enabled": True}}
        tts = GoogleTTS(config)
        
        # All of these should return False but not raise exceptions
        assert tts.speak("") is True  # Empty text
        
        # Test with mocked errors at various points
        with patch('src.adapters.tts.google_tts_adapter.gTTS', side_effect=Exception("gTTS error")):
            assert tts.speak("Test") is False
        
        with patch('tempfile.NamedTemporaryFile', side_effect=Exception("File error")):
            assert tts.speak("Test") is False
        
        with patch('subprocess.Popen', side_effect=Exception("Process error")):
            # This will fail at playback, but synthesis might succeed
            result = tts._play_audio_file("/fake/path.mp3")
            assert result is False
        
        # Stop should never crash
        tts.stop()
        
        # Cleanup should never crash
        del tts


if __name__ == "__main__":
    pytest.main([__file__])
