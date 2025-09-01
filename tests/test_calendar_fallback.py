"""Tests for calendar plugin fallback behavior."""

import pytest
import asyncio
from unittest.mock import patch, MagicMock
import subprocess

from src.plugins.builtin.calendar import CalendarPlugin


class TestCalendarPluginFallback:
    """Test calendar plugin with various failure scenarios."""

    @pytest.fixture
    def calendar_plugin(self):
        """Create calendar plugin instance."""
        config = {
            'calendar_app': 'macos',
            'default_scope': 'today'
        }
        return CalendarPlugin(config)

    def test_can_handle_calendar_queries(self, calendar_plugin):
        """Test calendar query detection."""
        # Direct calendar queries
        assert calendar_plugin.can_handle('calendar', 'show my calendar') is True
        
        # Keyword-based detection
        assert calendar_plugin.can_handle('', 'what meetings do I have today') is True
        assert calendar_plugin.can_handle('', 'my calendar for tomorrow') is True
        assert calendar_plugin.can_handle('', 'schedule for next week') is True
        assert calendar_plugin.can_handle('', 'any appointments today') is True
        
        # Should not handle non-calendar queries
        assert calendar_plugin.can_handle('', 'what is the weather') is False
        assert calendar_plugin.can_handle('', 'tell me a joke') is False

    @pytest.mark.asyncio
    async def test_successful_calendar_access(self, calendar_plugin):
        """Test when calendar access works."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = '"My Calendar"'
        
        with patch('subprocess.run', return_value=mock_result):
            result = await calendar_plugin.execute("What's on my calendar today?")
            
            assert result['success'] is True
            assert 'My Calendar' in result['response']
            assert 'guidance' in str(result['data']['events'][0].get('type', ''))

    @pytest.mark.asyncio
    async def test_calendar_access_failure(self, calendar_plugin):
        """Test when calendar access fails."""
        mock_result = MagicMock()
        mock_result.returncode = 1
        
        with patch('subprocess.run', return_value=mock_result):
            result = await calendar_plugin.execute("What's on my calendar today?")
            
            assert result['success'] is True  # Should still succeed with fallback
            assert 'Calendar app' in result['response']

    @pytest.mark.asyncio
    async def test_calendar_timeout_handling(self, calendar_plugin):
        """Test handling of calendar access timeout."""
        with patch('subprocess.run', side_effect=subprocess.TimeoutExpired('osascript', 1)):
            result = await calendar_plugin.execute("What's on my calendar today?")
            
            assert result['success'] is True  # Should gracefully handle timeout
            assert 'Calendar app' in result['response'] or 'calendar' in result['response'].lower()

    @pytest.mark.asyncio
    async def test_general_exception_handling(self, calendar_plugin):
        """Test handling of general exceptions."""
        with patch('subprocess.run', side_effect=Exception("General error")):
            result = await calendar_plugin.execute("What's on my calendar today?")
            
            assert result['success'] is True  # Should handle gracefully with guidance
            assert 'calendar' in result['response'].lower()

    @pytest.mark.asyncio
    async def test_time_scope_detection(self, calendar_plugin):
        """Test detection of different time scopes."""
        test_cases = [
            ("What's on my calendar today?", "today"),
            ("Show me tomorrow's schedule", "tomorrow"),
            ("What meetings do I have next week?", "upcoming"),
            ("Any appointments now?", "today"),
            ("My calendar please", "today"),  # Default
        ]
        
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = '"Work Calendar"'
        
        with patch('subprocess.run', return_value=mock_result):
            for query, expected_scope in test_cases:
                result = await calendar_plugin.execute(query)
                assert result['data']['time_scope'] == expected_scope

    @pytest.mark.asyncio
    async def test_response_formatting(self, calendar_plugin):
        """Test response formatting for different scenarios."""
        # Test guidance response formatting
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = '"Personal Calendar"'
        
        with patch('subprocess.run', return_value=mock_result):
            # Test today query
            result = await calendar_plugin.execute("What's my schedule today?")
            assert 'today' in result['response'].lower()
            assert 'Personal Calendar' in result['response']
            
            # Test tomorrow query
            result = await calendar_plugin.execute("What about tomorrow?")
            assert 'tomorrow' in result['response'].lower()

    def test_get_help_text(self, calendar_plugin):
        """Test help text generation."""
        help_text = calendar_plugin.get_help_text()
        assert 'calendar' in help_text.lower()
        assert 'meeting' in help_text.lower()

    def test_get_supported_intents(self, calendar_plugin):
        """Test supported intents."""
        intents = calendar_plugin.get_supported_intents()
        assert 'calendar' in intents

    @pytest.mark.asyncio
    async def test_context_handling(self, calendar_plugin):
        """Test handling of context parameter."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = '"Context Calendar"'
        
        context = {'user_preference': 'detailed'}
        
        with patch('subprocess.run', return_value=mock_result):
            result = await calendar_plugin.execute("My calendar today", context=context)
            assert result['success'] is True
            # Context should not break the execution

    @pytest.mark.asyncio
    async def test_hard_timeout_protection(self, calendar_plugin):
        """Test that hard timeout prevents hanging."""
        import time
        
        def slow_subprocess_run(*args, **kwargs):
            # Simulate hanging process, but timeout should prevent it
            if kwargs.get('timeout', 0) < 2:  # Our timeout is 1 second
                raise subprocess.TimeoutExpired('osascript', kwargs['timeout'])
            time.sleep(5)  # This should never be reached
            return MagicMock(returncode=0, stdout='"Should not reach"')
        
        with patch('subprocess.run', side_effect=slow_subprocess_run):
            start_time = time.time()
            result = await calendar_plugin.execute("What's my calendar today?")
            end_time = time.time()
            
            # Should complete quickly due to timeout
            assert (end_time - start_time) < 3  # Should be much faster than 5 seconds
            assert result['success'] is True


class TestCalendarIntegration:
    """Integration tests for calendar plugin."""

    @pytest.mark.asyncio
    async def test_real_macos_calendar_check(self):
        """Test real macOS calendar check (integration test)."""
        # This test actually tries to access the system calendar
        # Skip if not on macOS or if calendar access is restricted
        
        try:
            result = subprocess.run(
                ['osascript', '-e', 'tell application "Calendar" to get name of first calendar'],
                capture_output=True,
                text=True,
                timeout=2
            )
            
            calendar_available = result.returncode == 0
            
        except (subprocess.TimeoutExpired, FileNotFoundError):
            calendar_available = False
        
        plugin = CalendarPlugin({'calendar_app': 'macos'})
        
        if calendar_available:
            # Should get a reasonable response
            result = await plugin.execute("What's on my calendar today?")
            assert result['success'] is True
            assert len(result['response']) > 0
        else:
            # Should gracefully handle unavailable calendar
            result = await plugin.execute("What's on my calendar today?")
            assert result['success'] is True
            assert 'calendar' in result['response'].lower()


if __name__ == "__main__":
    pytest.main([__file__, '-v'])
