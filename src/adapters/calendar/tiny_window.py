"""
Calendar Tiny-Window Fallback System
Implements ChatGPT Priority #6: Reliable calendar integration with timeout handling.
"""

import subprocess
import json
import time
import threading
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from datetime import datetime, timedelta

@dataclass
class CalendarEvent:
    """Represents a calendar event"""
    title: str
    start_time: datetime
    end_time: datetime
    location: Optional[str] = None
    attendees: Optional[List[str]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'title': self.title,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat(),
            'location': self.location,
            'attendees': self.attendees or []
        }

class CalendarTimeoutError(Exception):
    """Raised when calendar operations timeout"""
    pass

class CalendarTinyWindow:
    """
    Reliable calendar integration with tiny query windows and hard timeouts.
    
    Features:
    - Configurable primary calendar selection
    - 2-hour query window (next 2 hours only)
    - 3-second hard timeout with friendly fallbacks
    - AppleScript reliability improvements
    - Graceful degradation when calendar unavailable
    """
    
    def __init__(self, primary_calendar: str = None, timeout_seconds: int = 3,
                 query_window_hours: int = 2, enable_fallback: bool = True):
        self.primary_calendar = primary_calendar or "Calendar"  # Default calendar name
        self.timeout_seconds = timeout_seconds
        self.query_window_hours = query_window_hours
        self.enable_fallback = enable_fallback
        
        # Statistics
        self.stats = {
            'total_queries': 0,
            'successful_queries': 0,
            'timeout_queries': 0,
            'error_queries': 0,
            'fallback_used': 0,
            'avg_query_time_ms': 0.0
        }
        
        # Friendly fallback messages
        self.fallback_messages = [
            "I'm having trouble accessing your calendar right now. You might want to check it directly.",
            "Your calendar seems to be taking a while to respond. I'd suggest opening Calendar.app to check.",
            "Calendar access is being slow today. Want me to try something else instead?",
            "I can't quickly grab your calendar info right now. Maybe check your schedule manually?",
            "Calendar is being unresponsive. This might be a good time to take a quick break!"
        ]
    
    def _execute_applescript_with_timeout(self, script: str, timeout: int = None) -> str:
        """Execute AppleScript with hard timeout"""
        timeout = timeout or self.timeout_seconds
        
        def target():
            try:
                self.result = subprocess.run(
                    ['osascript', '-e', script],
                    capture_output=True,
                    text=True,
                    timeout=timeout
                )
            except Exception as e:
                self.result = None
                self.error = e
        
        self.result = None
        self.error = None
        
        thread = threading.Thread(target=target)
        thread.daemon = True
        thread.start()
        thread.join(timeout)
        
        if thread.is_alive():
            # Timeout occurred
            raise CalendarTimeoutError(f"Calendar query timed out after {timeout} seconds")
        
        if self.error:
            raise self.error
        
        if self.result is None:
            raise CalendarTimeoutError("Calendar query failed to complete")
        
        if self.result.returncode != 0:
            raise RuntimeError(f"AppleScript failed: {self.result.stderr}")
        
        return self.result.stdout.strip()
    
    def _get_tiny_window_script(self) -> str:
        """Generate AppleScript for tiny 2-hour window query"""
        now = datetime.now()
        start_time = now.strftime("%m/%d/%Y %H:%M:%S")
        end_time = (now + timedelta(hours=self.query_window_hours)).strftime("%m/%d/%Y %H:%M:%S")
        
        # Simplified AppleScript focusing on reliability over features
        script = f'''
        tell application "Calendar"
            set startDate to date "{start_time}"
            set endDate to date "{end_time}"
            set eventList to {{}}
            
            try
                set calendarRef to calendar "{self.primary_calendar}"
                set theEvents to (every event of calendarRef whose start date ≥ startDate and start date ≤ endDate)
                
                repeat with anEvent in theEvents
                    set eventInfo to (summary of anEvent) & "|" & ¬
                                   (start date of anEvent as string) & "|" & ¬
                                   (end date of anEvent as string)
                    set end of eventList to eventInfo
                end repeat
                
            on error
                -- If primary calendar fails, try default calendar
                set theEvents to (every event whose start date ≥ startDate and start date ≤ endDate)
                
                repeat with anEvent in theEvents
                    set eventInfo to (summary of anEvent) & "|" & ¬
                                   (start date of anEvent as string) & "|" & ¬
                                   (end date of anEvent as string)
                    set end of eventList to eventInfo
                end repeat
            end try
            
            set AppleScript's text item delimiters to "\\n"
            return eventList as string
        end tell
        '''
        
        return script
    
    def get_upcoming_events(self) -> List[CalendarEvent]:
        """
        Get upcoming events from the tiny 2-hour window.
        Returns empty list on timeout with friendly fallback.
        """
        start_time = time.time()
        self.stats['total_queries'] += 1
        
        try:
            script = self._get_tiny_window_script()
            result = self._execute_applescript_with_timeout(script)
            
            events = self._parse_applescript_result(result)
            
            # Update stats
            query_time = (time.time() - start_time) * 1000
            self.stats['successful_queries'] += 1
            self._update_avg_query_time(query_time)
            
            return events
            
        except CalendarTimeoutError:
            self.stats['timeout_queries'] += 1
            if self.enable_fallback:
                self.stats['fallback_used'] += 1
            return []  # Return empty list, let caller handle fallback message
            
        except Exception as e:
            self.stats['error_queries'] += 1
            print(f"Calendar error: {e}")
            return []
    
    def get_next_meeting_summary(self) -> str:
        """
        Get a friendly summary of upcoming meetings.
        Handles timeouts gracefully with fallback messages.
        """
        events = self.get_upcoming_events()
        
        if not events:
            # Check if this was due to timeout
            recent_fallback = self.stats['timeout_queries'] > 0 and (
                self.stats['timeout_queries'] == self.stats['total_queries'] or
                self.stats['timeout_queries'] > self.stats['successful_queries']
            )
            
            if recent_fallback:
                return self.get_friendly_fallback_message()
            else:
                return "You don't have any meetings in the next couple hours. Perfect time to focus!"
        
        # Format the response
        if len(events) == 1:
            event = events[0]
            time_str = event.start_time.strftime("%-I:%M %p")
            return f"You have '{event.title}' at {time_str}."
        
        elif len(events) == 2:
            event1, event2 = events[0], events[1]
            time1 = event1.start_time.strftime("%-I:%M %p")
            time2 = event2.start_time.strftime("%-I:%M %p")
            return f"You have '{event1.title}' at {time1} and '{event2.title}' at {time2}."
        
        else:
            # 3+ events
            first_event = events[0]
            time_str = first_event.start_time.strftime("%-I:%M %p")
            return f"You have '{first_event.title}' at {time_str} plus {len(events)-1} more meetings in the next couple hours."
    
    def get_friendly_fallback_message(self) -> str:
        """Get a random friendly fallback message"""
        import random
        return random.choice(self.fallback_messages)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get calendar system statistics"""
        total = self.stats['total_queries']
        if total == 0:
            success_rate = 0.0
            timeout_rate = 0.0
        else:
            success_rate = self.stats['successful_queries'] / total
            timeout_rate = self.stats['timeout_queries'] / total
        
        return {
            **self.stats,
            'success_rate': success_rate,
            'timeout_rate': timeout_rate,
            'primary_calendar': self.primary_calendar,
            'query_window_hours': self.query_window_hours,
            'timeout_seconds': self.timeout_seconds
        }

# Parsing and utility methods continue...
