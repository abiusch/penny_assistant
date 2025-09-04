"""
Tests for Penny Doctor system health checker
"""

import pytest
import sys
import os
from unittest.mock import patch, MagicMock
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from penny_doctor import PennyDoctor

class TestPennyDoctor:
    
    def setup_method(self):
        """Setup test environment"""
        self.doctor = PennyDoctor()
        
    def test_initialization(self):
        """Test PennyDoctor initializes correctly"""
        assert self.doctor.project_root is not None
        assert self.doctor.results == []
        assert self.doctor.error_count == 0
        
    def test_print_result_success(self, capsys):
        """Test printing successful results"""
        self.doctor.print_result("Test Check", True, "All good", "")
        
        captured = capsys.readouterr()
        assert "✅ Test Check" in captured.out
        assert "All good" in captured.out
        assert self.doctor.error_count == 0
        
    def test_print_result_failure(self, capsys):
        """Test printing failed results with fix suggestion"""
        self.doctor.print_result("Test Check", False, "Problem found", "Fix it like this")
        
        captured = capsys.readouterr()
        assert "❌ Test Check" in captured.out
        assert "Problem found" in captured.out
        assert "🔧 Fix: Fix it like this" in captured.out
        assert self.doctor.error_count == 1
        
    def test_check_python_environment_success(self):
        """Test Python environment check with good conditions"""
        with patch('sys.version_info', (3, 11, 0)):
            with patch.object(sys, 'prefix', '/venv/path'):
                with patch.object(sys, 'base_prefix', '/system/path'):
                    with patch.dict(os.environ, {'PYTHONPATH': 'src'}):
                        result = self.doctor.check_python_environment()
                        
        # Should pass all checks
        assert result == True
        
    def test_check_python_environment_old_version(self):
        """Test Python environment check with old Python version"""
        with patch('sys.version_info', (3, 8, 0)):
            result = self.doctor.check_python_environment()
            
        # Should fail due to old Python version
        assert self.doctor.error_count > 0
        
    @patch('requests.get')
    def test_check_daemon_health_success(self, mock_get):
        """Test daemon health check with healthy daemon"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "ok": True,
            "uptime_s": 45.2,
            "ptt_active": False
        }
        mock_get.return_value = mock_response
        
        # Mock POST requests for endpoints
        with patch('requests.post') as mock_post:
            mock_post.return_value.status_code = 200
            result = self.doctor.check_daemon_health()
            
        assert result == True
        
    @patch('requests.get')
    def test_check_daemon_health_failure(self, mock_get):
        """Test daemon health check with offline daemon"""
        mock_get.side_effect = Exception("Connection refused")
        
        result = self.doctor.check_daemon_health()
        
        assert result == False
        assert self.doctor.error_count > 0
        
    def test_check_dependencies_missing(self):
        """Test dependency check with missing packages"""
        # This will likely find some missing packages in test environment
        result = self.doctor.check_dependencies()
        
        # Should complete without crashing
        assert isinstance(result, bool)
        
    @patch('pyaudio.PyAudio')
    def test_check_audio_system_success(self, mock_pyaudio):
        """Test audio system check with working audio"""
        mock_pa_instance = MagicMock()
        mock_pa_instance.get_default_input_device_info.return_value = {
            'name': 'Test Microphone'
        }
        mock_pa_instance.get_default_output_device_info.return_value = {
            'name': 'Test Speaker'
        }
        mock_pyaudio.return_value = mock_pa_instance
        
        with patch('subprocess.run') as mock_subprocess:
            mock_subprocess.return_value = None
            result = self.doctor.check_audio_system()
            
        assert isinstance(result, bool)
        
    @patch('pyaudio.PyAudio')
    def test_check_audio_system_failure(self, mock_pyaudio):
        """Test audio system check with audio issues"""
        mock_pyaudio.side_effect = Exception("Audio system not available")
        
        result = self.doctor.check_audio_system()
        
        assert result == False
        
    def test_check_penny_components(self):
        """Test PennyGPT component check"""
        result = self.doctor.check_penny_components()
        
        # Should complete and check for files
        assert isinstance(result, bool)
        
    def test_check_permissions_non_macos(self):
        """Test permission check on non-macOS"""
        with patch('sys.platform', 'linux'):
            result = self.doctor.check_permissions()
            
        assert result == True  # Should skip checks on non-macOS
        
    def test_run_all_checks_completes(self, capsys):
        """Test that running all checks completes without crashing"""
        # This is an integration test - should not crash
        try:
            self.doctor.run_all_checks()
            success = True
        except Exception as e:
            print(f"Error: {e}")
            success = False
            
        assert success == True
        
        # Check that output was produced
        captured = capsys.readouterr()
        assert "Penny Doctor" in captured.out
        assert "Health Check Summary" in captured.out

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
