"""Tests for PennyGPT Health Monitor."""

import pytest
import asyncio
from unittest.mock import patch, MagicMock
import requests

from health_monitor import PennyGPTHealthMonitor, ComponentHealth, HealthStatus


class TestHealthMonitor:
    """Test health monitoring functionality."""

    @pytest.fixture
    def health_monitor(self):
        """Create health monitor instance."""
        with patch('health_monitor.load_config') as mock_config:
            mock_config.return_value = {
                'llm': {
                    'base_url': 'http://localhost:1234/v1',
                    'model': 'test-model'
                }
            }
            return PennyGPTHealthMonitor()

    @pytest.mark.asyncio
    async def test_lm_studio_healthy(self, health_monitor):
        """Test healthy LM Studio check."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'data': [{'id': 'test-model'}, {'id': 'other-model'}]
        }
        
        with patch('requests.get', return_value=mock_response):
            result = await health_monitor.check_lm_studio_health()
            
            assert result.status == HealthStatus.HEALTHY
            assert result.name == "LM Studio"
            assert result.response_time_ms is not None
            assert result.details['model_available'] is True

    @pytest.mark.asyncio
    async def test_lm_studio_connection_refused(self, health_monitor):
        """Test LM Studio connection refused."""
        with patch('requests.get', side_effect=requests.exceptions.ConnectionError):
            result = await health_monitor.check_lm_studio_health()
            
            assert result.status == HealthStatus.UNHEALTHY
            assert "Connection refused" in result.error
            assert result.response_time_ms is None

    @pytest.mark.asyncio
    async def test_lm_studio_model_not_available(self, health_monitor):
        """Test when configured model is not available."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'data': [{'id': 'other-model'}]  # Missing 'test-model'
        }
        
        with patch('requests.get', return_value=mock_response):
            result = await health_monitor.check_lm_studio_health()
            
            assert result.status == HealthStatus.DEGRADED
            assert "not available" in result.error
            assert result.details['model_available'] is False

    @pytest.mark.asyncio
    async def test_lm_studio_timeout(self, health_monitor):
        """Test LM Studio timeout."""
        with patch('requests.get', side_effect=requests.exceptions.Timeout):
            result = await health_monitor.check_lm_studio_health()
            
            assert result.status == HealthStatus.DEGRADED
            assert "timed out" in result.error
            assert result.response_time_ms == 2000

    @pytest.mark.asyncio
    async def test_llm_completion_healthy(self, health_monitor):
        """Test healthy LLM completion."""
        with patch('health_monitor.OpenAICompatLLM') as mock_llm_class:
            mock_llm = MagicMock()
            mock_llm.complete.return_value = "OK, I can hear you!"
            mock_llm_class.return_value = mock_llm
            
            result = await health_monitor.check_llm_completion()
            
            assert result.status == HealthStatus.HEALTHY
            assert result.name == "LLM Completion"
            assert result.response_time_ms is not None

    @pytest.mark.asyncio
    async def test_llm_completion_error_response(self, health_monitor):
        """Test LLM completion with error response."""
        with patch('health_monitor.OpenAICompatLLM') as mock_llm_class:
            mock_llm = MagicMock()
            mock_llm.complete.return_value = "[llm error] Connection failed"
            mock_llm_class.return_value = mock_llm
            
            result = await health_monitor.check_llm_completion()
            
            assert result.status == HealthStatus.UNHEALTHY
            assert "Invalid response" in result.error

    @pytest.mark.asyncio
    async def test_tts_healthy(self, health_monitor):
        """Test healthy TTS check."""
        with patch('health_monitor.GoogleTTS') as mock_tts_class:
            mock_tts = MagicMock()
            mock_tts.speak.return_value = True
            mock_tts.cache_enabled = True
            mock_tts.memory_cache = {'test': 'value'}
            mock_tts_class.return_value = mock_tts
            
            result = await health_monitor.check_tts_health()
            
            assert result.status == HealthStatus.HEALTHY
            assert result.name == "TTS"
            assert result.details['cache_enabled'] is True
            assert result.details['cache_size'] == 1

    @pytest.mark.asyncio
    async def test_tts_synthesis_failed(self, health_monitor):
        """Test TTS synthesis failure."""
        with patch('health_monitor.GoogleTTS') as mock_tts_class:
            mock_tts = MagicMock()
            mock_tts.speak.return_value = False
            mock_tts_class.return_value = mock_tts
            
            result = await health_monitor.check_tts_health()
            
            assert result.status == HealthStatus.DEGRADED
            assert "synthesis failed" in result.error

    @pytest.mark.asyncio
    async def test_stt_healthy(self, health_monitor):
        """Test healthy STT check."""
        with patch('health_monitor.WhisperSTT') as mock_stt_class:
            mock_stt = MagicMock()
            mock_stt._model = MagicMock()  # Model loaded
            mock_stt.model_name = "base"
            mock_stt_class.return_value = mock_stt
            
            result = await health_monitor.check_stt_health()
            
            assert result.status == HealthStatus.HEALTHY
            assert result.name == "STT"
            assert result.details['model_loaded'] is True
            assert result.details['model_name'] == "base"

    @pytest.mark.asyncio
    async def test_stt_model_not_loaded(self, health_monitor):
        """Test STT with model not loaded."""
        with patch('health_monitor.WhisperSTT') as mock_stt_class:
            mock_stt = MagicMock()
            mock_stt._model = None  # Model not loaded
            mock_stt_class.return_value = mock_stt
            
            result = await health_monitor.check_stt_health()
            
            assert result.status == HealthStatus.UNHEALTHY
            assert "failed to load" in result.error

    @pytest.mark.asyncio
    async def test_audio_devices_healthy(self, health_monitor):
        """Test healthy audio devices check."""
        mock_devices = [
            {'max_input_channels': 2, 'name': 'Microphone'},
            {'max_output_channels': 2, 'name': 'Speakers'},
            {'max_input_channels': 0, 'max_output_channels': 0, 'name': 'Other'}
        ]
        
        with patch('sounddevice.query_devices') as mock_query:
            mock_query.return_value = mock_devices
            # Mock specific device queries
            mock_query.side_effect = [
                mock_devices,  # All devices
                {'name': 'Default Input'},  # Default input
                {'name': 'Default Output'}  # Default output
            ]
            
            result = await health_monitor.check_audio_devices()
            
            assert result.status == HealthStatus.HEALTHY
            assert result.name == "Audio Devices"
            assert result.details['input_devices'] == 1
            assert result.details['output_devices'] == 1

    @pytest.mark.asyncio
    async def test_audio_devices_not_available(self, health_monitor):
        """Test when sounddevice is not available."""
        with patch('health_monitor.__import__', side_effect=ImportError):
            result = await health_monitor.check_audio_devices()
            
            assert result.status == HealthStatus.UNHEALTHY
            assert "not available" in result.error

    @pytest.mark.asyncio
    async def test_check_all_components(self, health_monitor):
        """Test checking all components together."""
        # Mock all checks to return healthy
        with patch.object(health_monitor, 'check_lm_studio_health') as mock_lm, \
             patch.object(health_monitor, 'check_tts_health') as mock_tts, \
             patch.object(health_monitor, 'check_stt_health') as mock_stt, \
             patch.object(health_monitor, 'check_audio_devices') as mock_audio, \
             patch.object(health_monitor, 'check_llm_completion') as mock_completion:
            
            mock_lm.return_value = ComponentHealth("LM Studio", HealthStatus.HEALTHY, 100)
            mock_tts.return_value = ComponentHealth("TTS", HealthStatus.HEALTHY, 200)
            mock_stt.return_value = ComponentHealth("STT", HealthStatus.HEALTHY, 300)
            mock_audio.return_value = ComponentHealth("Audio Devices", HealthStatus.HEALTHY, 50)
            mock_completion.return_value = ComponentHealth("LLM Completion", HealthStatus.HEALTHY, 1000)
            
            results = await health_monitor.check_all_components()
            
            assert len(results) == 5
            assert all(h.status == HealthStatus.HEALTHY for h in results.values())
            assert "LM Studio" in results
            assert "LLM Completion" in results

    @pytest.mark.asyncio
    async def test_check_all_components_lm_studio_unhealthy(self, health_monitor):
        """Test when LM Studio is unhealthy - should skip completion test."""
        with patch.object(health_monitor, 'check_lm_studio_health') as mock_lm, \
             patch.object(health_monitor, 'check_tts_health') as mock_tts, \
             patch.object(health_monitor, 'check_stt_health') as mock_stt, \
             patch.object(health_monitor, 'check_audio_devices') as mock_audio:
            
            mock_lm.return_value = ComponentHealth("LM Studio", HealthStatus.UNHEALTHY, None, "Connection failed")
            mock_tts.return_value = ComponentHealth("TTS", HealthStatus.HEALTHY, 200)
            mock_stt.return_value = ComponentHealth("STT", HealthStatus.HEALTHY, 300)
            mock_audio.return_value = ComponentHealth("Audio Devices", HealthStatus.HEALTHY, 50)
            
            results = await health_monitor.check_all_components()
            
            assert len(results) == 4  # Should not include LLM Completion
            assert "LM Studio" in results
            assert "LLM Completion" not in results

    def test_format_health_report(self, health_monitor):
        """Test health report formatting."""
        health_status = {
            "Component 1": ComponentHealth("Component 1", HealthStatus.HEALTHY, 100),
            "Component 2": ComponentHealth("Component 2", HealthStatus.DEGRADED, 200, "Warning message"),
            "Component 3": ComponentHealth("Component 3", HealthStatus.UNHEALTHY, None, "Error message")
        }
        
        report = health_monitor.format_health_report(health_status)
        
        assert "🏥 PennyGPT Health Report" in report
        assert "🟡 DEGRADED" in report  # 1/3 healthy = degraded overall
        assert "✅ Component 1" in report
        assert "⚠️ Component 2" in report
        assert "❌ Component 3" in report
        assert "Warning message" in report
        assert "Error message" in report

    @pytest.mark.asyncio
    async def test_run_health_check_healthy(self, health_monitor):
        """Test running health check when system is healthy."""
        mock_health_status = {
            "Component 1": ComponentHealth("Component 1", HealthStatus.HEALTHY, 100),
            "Component 2": ComponentHealth("Component 2", HealthStatus.HEALTHY, 200)
        }
        
        with patch.object(health_monitor, 'check_all_components', return_value=mock_health_status):
            is_healthy = await health_monitor.run_health_check()
            
            assert is_healthy is True

    @pytest.mark.asyncio
    async def test_run_health_check_unhealthy(self, health_monitor):
        """Test running health check when system is unhealthy."""
        mock_health_status = {
            "Component 1": ComponentHealth("Component 1", HealthStatus.UNHEALTHY, None, "Error"),
            "Component 2": ComponentHealth("Component 2", HealthStatus.UNHEALTHY, None, "Error")
        }
        
        with patch.object(health_monitor, 'check_all_components', return_value=mock_health_status):
            is_healthy = await health_monitor.run_health_check()
            
            assert is_healthy is False


if __name__ == "__main__":
    pytest.main([__file__, '-v'])
