"""
Tests for Calendar Tiny-Window Fallback System
Ensures reliable calendar access with timeout handling.
"""

import pytest
import time
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

from adapters.calendar.tiny_window import CalendarTinyWindow, CalendarEvent, CalendarTimeoutError

class TestCalendarTinyWindow:
    
    def setup_method(self):
        """Setup test environment"""
        self.calendar = CalendarTinyWindow(
            primary_calendar="Test Calendar",
            timeout_seconds=1,  # Short timeout for testing
            query_window_hours=2
        )
    
    def test_timeout_handling(self):
        """Test that timeouts are handled gracefully"""
        def slow_applescript(*args, **kwargs):
            time.sleep(2)  # Longer than timeout
            return Mock(returncode=0, stdout="test")
        
        with patch('subprocess.run', side_effect=slow_applescript):
            events = self.calendar.get_upcoming_events()
            
            assert events == []  # Should return empty list on timeout
            assert self.calendar.stats['timeout_queries'] == 1
            assert self.calendar.stats['total_queries'] == 1
    
    def test_friendly_fallback_messages(self):
        """Test that fallback messages are friendly and helpful"""
        message = self.calendar.get_friendly_fallback_message()
        
        assert isinstance(message, str)
        assert len(message) > 0
        assert message in self.calendar.fallback_messages
    
    def test_meeting_summary_with_timeout(self):
        """Test meeting summary handles timeouts with friendly messages"""
        # Force a timeout scenario
        self.calendar.stats['timeout_queries'] = 1
        self.calendar.stats['total_queries'] = 1
        
        with patch.object(self.calendar, 'get_upcoming_events', return_value=[]):
            summary = self.calendar.get_next_meeting_summary()
            
            # Should return a fallback message, not the "no meetings" message
            assert "trouble" in summary.lower() or "slow" in summary.lower() or "check" in summary.lower()
    
    def test_meeting_summary_formatting(self):
        """Test different meeting summary formats"""
        # Single meeting
        event1 = CalendarEvent(
            title="Team Meeting",
            start_time=datetime.now() + timedelta(hours=1),
            end_time=datetime.now() + timedelta(hours=2)
        )
        
        with patch.object(self.calendar, 'get_upcoming_events', return_value=[event1]):
            summary = self.calendar.get_next_meeting_summary()
            assert "Team Meeting" in summary
            assert "at" in summary
    
    def test_stats_tracking(self):
        """Test that statistics are tracked correctly"""
        initial_stats = self.calendar.get_stats()
        
        assert initial_stats['total_queries'] == 0
        assert initial_stats['success_rate'] == 0.0
        assert initial_stats['timeout_rate'] == 0.0
        
        # Simulate successful query
        self.calendar.stats['total_queries'] = 1
        self.calendar.stats['successful_queries'] = 1
        
        updated_stats = self.calendar.get_stats()
        assert updated_stats['success_rate'] == 1.0
        assert updated_stats['timeout_rate'] == 0.0
    
    def test_tiny_window_script_generation(self):
        """Test that AppleScript is generated correctly"""
        script = self.calendar._get_tiny_window_script()
        
        assert 'tell application "Calendar"' in script
        assert self.calendar.primary_calendar in script
        assert "startDate" in script
        assert "endDate" in script

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
