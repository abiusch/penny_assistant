"""Tests for OpenAI Compatible LLM adapter."""

import pytest
import requests
from unittest.mock import patch, MagicMock

from src.adapters.llm.openai_compat import OpenAICompatLLM


class TestOpenAICompatLLM:
    """Test OpenAI Compatible LLM adapter."""

    @pytest.fixture
    def config(self):
        """Sample configuration for testing."""
        return {
            "llm": {
                "provider": "openai_compatible",
                "base_url": "http://localhost:1234/v1",
                "api_key": "lm-studio",
                "model": "test-model",
                "temperature": 0.7,
                "max_tokens": 256
            }
        }

    @pytest.fixture
    def llm_adapter(self, config):
        """Create LLM adapter instance."""
        return OpenAICompatLLM(config)

    def test_initialization(self, llm_adapter):
        """Test adapter initialization."""
        assert llm_adapter.base_url == "http://localhost:1234/v1"
        assert llm_adapter.api_key == "lm-studio"
        assert llm_adapter.model == "test-model"
        assert llm_adapter.temperature == 0.7
        assert llm_adapter.max_tokens == 256

    def test_url_construction(self, llm_adapter):
        """Test that URL is constructed correctly without double /v1."""
        with patch('requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "choices": [{"message": {"content": "test response"}}]
            }
            mock_post.return_value = mock_response
            
            llm_adapter.complete("test prompt")
            
            # Check that the URL doesn't have double /v1
            expected_url = "http://localhost:1234/v1/chat/completions"
            mock_post.assert_called_once()
            actual_url = mock_post.call_args[0][0]
            assert actual_url == expected_url
            assert "/v1/v1/" not in actual_url

    def test_timeout_setting(self, llm_adapter):
        """Test that timeout is set to 15 seconds."""
        with patch('requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "choices": [{"message": {"content": "test response"}}]
            }
            mock_post.return_value = mock_response
            
            llm_adapter.complete("test prompt")
            
            # Check timeout parameter
            call_kwargs = mock_post.call_args[1]
            assert call_kwargs['timeout'] == 15

    @patch('requests.post')
    def test_complete_success(self, mock_post, llm_adapter):
        """Test successful completion."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Hello, world!"}}]
        }
        mock_post.return_value = mock_response
        
        result = llm_adapter.complete("Say hello")
        
        assert result == "Hello, world!"
        mock_post.assert_called_once()

    @patch('requests.post')
    def test_complete_error_handling(self, mock_post, llm_adapter):
        """Test error handling in completion."""
        mock_post.side_effect = requests.exceptions.RequestException("Connection error")
        
        result = llm_adapter.complete("test prompt")
        
        assert result.startswith("[llm error]")
        assert "Connection error" in result
        assert "test prompt" in result

    def _check_lm_studio_running(self):
        """Check if LM Studio is running and accessible."""
        try:
            response = requests.get("http://localhost:1234/v1/models", timeout=2)
            return response.status_code == 200
        except Exception:
            return False

    @pytest.mark.skipif(
        not pytest.importorskip("requests", reason="requests not available"),
        reason="Skipping integration test"
    )
    def test_integration_with_lm_studio(self, llm_adapter):
        """Integration test with actual LM Studio (skips if not running)."""
        if not self._check_lm_studio_running():
            pytest.skip("LM Studio not running on localhost:1234")
        
        # Test that we can ping the models endpoint
        try:
            response = requests.get("http://localhost:1234/v1/models", timeout=5)
            assert response.status_code == 200
            
            # Test a simple completion
            result = llm_adapter.complete("Say 'test' if you can hear me", tone="friendly")
            assert isinstance(result, str)
            assert len(result) > 0
            assert not result.startswith("[llm error]")
            
        except Exception as e:
            pytest.fail(f"Integration test failed: {e}")

    def test_request_format(self, llm_adapter):
        """Test that request format matches OpenAI API."""
        with patch('requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "choices": [{"message": {"content": "response"}}]
            }
            mock_post.return_value = mock_response
            
            llm_adapter.complete("test prompt", tone="helpful")
            
            # Check request format
            call_args = mock_post.call_args
            headers = call_args[1]['headers']
            assert headers['Authorization'] == 'Bearer lm-studio'
            assert headers['Content-Type'] == 'application/json'
            
            # Check body structure
            import json
            body = json.loads(call_args[1]['data'])
            assert body['model'] == 'test-model'
            assert body['temperature'] == 0.7
            assert body['max_tokens'] == 256
            assert len(body['messages']) == 2
            assert body['messages'][0]['role'] == 'system'
            assert 'helpful' in body['messages'][0]['content']
            assert body['messages'][1]['role'] == 'user'
            assert body['messages'][1]['content'] == 'test prompt'
