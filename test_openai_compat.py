#!/usr/bin/env python3
"""
Unit tests for OpenAI-compatible LLM adapter
Tests URL joining, error handling, and adapter resilience
"""

import sys
import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from adapters.llm.openai_compat import OpenAICompatLLM

class TestOpenAICompatLLM(unittest.TestCase):
    """Test cases for OpenAICompatLLM adapter"""

    def setUp(self):
        """Set up test configuration"""
        self.config = {
            "llm": {
                "base_url": "http://localhost:1234/v1",
                "api_key": "test-key",
                "model": "test-model",
                "temperature": 0.7,
                "max_tokens": 256
            }
        }

    def test_url_normalization_with_v1(self):
        """Test URL normalization when base_url already has /v1"""
        adapter = OpenAICompatLLM(self.config)
        self.assertEqual(adapter.base_url, "http://localhost:1234/v1")

    def test_url_normalization_without_v1(self):
        """Test URL normalization when base_url lacks /v1"""
        config = self.config.copy()
        config["llm"]["base_url"] = "http://localhost:1234"
        adapter = OpenAICompatLLM(config)
        self.assertEqual(adapter.base_url, "http://localhost:1234/v1")

    def test_url_normalization_with_trailing_slash(self):
        """Test URL normalization with trailing slash"""
        config = self.config.copy()
        config["llm"]["base_url"] = "http://localhost:1234/"
        adapter = OpenAICompatLLM(config)
        self.assertEqual(adapter.base_url, "http://localhost:1234/v1")

    def test_url_normalization_with_trailing_slash_and_v1(self):
        """Test URL normalization with trailing slash and /v1"""
        config = self.config.copy()
        config["llm"]["base_url"] = "http://localhost:1234/v1/"
        adapter = OpenAICompatLLM(config)
        self.assertEqual(adapter.base_url, "http://localhost:1234/v1")

    @patch('requests.Session')
    def test_health_check_success(self, mock_session_class):
        """Test successful health check"""
        # Setup mock
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "data": [
                {"id": "test-model"},
                {"id": "other-model"}
            ]
        }
        mock_session.get.return_value = mock_response
        
        adapter = OpenAICompatLLM(self.config)
        health = adapter.health()
        
        self.assertEqual(health["status"], "healthy")
        self.assertTrue(health["model_available"])
        self.assertIn("test-model", health["available_models"])
        self.assertIsNone(health["error"])

    @patch('requests.Session')
    def test_health_check_model_not_available(self, mock_session_class):
        """Test health check when configured model is not available"""
        # Setup mock
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "data": [{"id": "other-model"}]
        }
        mock_session.get.return_value = mock_response
        
        adapter = OpenAICompatLLM(self.config)
        health = adapter.health()
        
        self.assertEqual(health["status"], "warning")
        self.assertFalse(health["model_available"])
        self.assertIsNotNone(health["error"])

    @patch('requests.Session')
    def test_health_check_server_down(self, mock_session_class):
        """Test health check when server is down"""
        # Setup mock
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        mock_session.get.side_effect = ConnectionError("Connection refused")
        
        adapter = OpenAICompatLLM(self.config)
        health = adapter.health()
        
        self.assertEqual(health["status"], "unhealthy")
        self.assertFalse(health["model_available"])
        self.assertIn("Connection refused", health["error"])

    @patch('requests.Session')
    def test_complete_success(self, mock_session_class):
        """Test successful completion"""
        # Setup mock
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [
                {"message": {"content": "Hello, this is a test response!"}}
            ]
        }
        mock_session.post.return_value = mock_response
        
        adapter = OpenAICompatLLM(self.config)
        result = adapter.complete("Say hello")
        
        self.assertEqual(result, "Hello, this is a test response!")
        
        # Verify correct URL was called
        call_args = mock_session.post.call_args
        self.assertIn("chat/completions", call_args[0][0])

    @patch('requests.Session')
    def test_complete_network_error(self, mock_session_class):
        """Test completion with network error"""
        # Setup mock
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        import requests
        mock_session.post.side_effect = requests.exceptions.ConnectionError("Network unreachable")
        
        adapter = OpenAICompatLLM(self.config)
        result = adapter.complete("Say hello")
        
        self.assertIn("[llm error]", result)
        self.assertIn("Network/HTTP error", result)
        self.assertIn("Network unreachable", result)

    @patch('requests.Session')
    def test_complete_malformed_response(self, mock_session_class):
        """Test completion with malformed response"""
        # Setup mock
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        mock_response = MagicMock()
        mock_response.json.return_value = {"invalid": "response"}  # Missing choices
        mock_session.post.return_value = mock_response
        
        adapter = OpenAICompatLLM(self.config)
        result = adapter.complete("Say hello")
        
        # Should handle gracefully and return empty string, not crash
        self.assertEqual(result, "")

    def test_default_configuration(self):
        """Test adapter with empty/default configuration"""
        adapter = OpenAICompatLLM({})
        
        self.assertEqual(adapter.base_url, "http://localhost:1234/v1")
        self.assertEqual(adapter.api_key, "lm-studio")
        self.assertEqual(adapter.model, "openai/gpt-oss-20b")
        self.assertEqual(adapter.temperature, 0.6)
        self.assertEqual(adapter.max_tokens, 512)

    def test_session_cleanup(self):
        """Test that session is properly cleaned up"""
        adapter = OpenAICompatLLM(self.config)
        session = adapter.session
        
        # Simulate garbage collection
        del adapter
        
        # Session should be closed (we can't easily test this automatically,
        # but the __del__ method should handle it)

if __name__ == "__main__":
    # Run tests
    unittest.main(verbosity=2)
