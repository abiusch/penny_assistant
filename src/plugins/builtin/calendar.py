"""
Calendar plugin for PennyGPT
"""

import subprocess
import json
import re
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from ..base_plugin import BasePlugin


class CalendarPlugin(BasePlugin):
    """Plugin to handle calendar queries"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.calendar_app = self.config.get('calendar_app', 'macos')  # macos, google, outlook
        
    def can_handle(self, intent: str, query: str) -> bool:
        """Check if this plugin can handle calendar requests"""
        if intent == 'calendar':
            return True
            
        # Calendar query patterns
        query_lower = query.lower().strip()
        
        calendar_patterns = [
            r"what'?s? (on )?my (calendar|schedule)",
            r"what'?s? my next (meeting|appointment|event)",
            r"when is my next",
            r"do i have (any |anything )?today",
            r"do i have (any |anything )?tomorrow", 
            r"what'?s? (on )?my agenda",
            r"any meetings today",
            r"any events today",
            r"schedule for today",
            r"schedule for tomorrow"
        ]
        
        return any(re.search(pattern, query_lower) for pattern in calendar_patterns)
    
    async def execute(self, query: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """Execute calendar lookup"""
        try:
            query_lower = query.lower().strip()
            
            # Determine time scope
            if any(word in query_lower for word in ['today', 'now']):
                events = await self._get_today_events()
                time_scope = "today"
            elif 'tomorrow' in query_lower:
                events = await self._get_tomorrow_events()
                time_scope = "tomorrow"
            elif 'next' in query_lower:
                events = await self._get_next_events(limit=3)
                time_scope = "upcoming"
            else:
                events = await self._get_today_events()
                time_scope = "today"
            
            if events:
                response = self._format_calendar_response(events, time_scope)
                return {
                    'success': True,
                    'response': response,
                    'data': {'events': events, 'time_scope': time_scope}
                }
            else:
                response = f"You don't have any events {time_scope}."
                return {
                    'success': True,
                    'response': response,
                    'data': {'events': [], 'time_scope': time_scope}
                }
                
        except Exception as e:
            return {
                'success': False,
                'response': f"Sorry, I couldn't access your calendar: {str(e)}",
                'error': str(e)
            }
    
    async def _get_today_events(self) -> List[Dict[str, Any]]:
        """Get today's calendar events"""
        if self.calendar_app == 'macos':
            return await self._get_macos_events_for_date(datetime.now().date())
        else:
            return []  # Placeholder for other calendar systems
    
    async def _get_tomorrow_events(self) -> List[Dict[str, Any]]:
        """Get tomorrow's calendar events"""
        if self.calendar_app == 'macos':
            tomorrow = datetime.now().date() + timedelta(days=1)
            return await self._get_macos_events_for_date(tomorrow)
        else:
            return []
    
    async def _get_next_events(self, limit: int = 3) -> List[Dict[str, Any]]:
        """Get next few upcoming events"""
        if self.calendar_app == 'macos':
            return await self._get_macos_upcoming_events(limit)
        else:
            return []
    
    async def _get_macos_events_for_date(self, date) -> List[Dict[str, Any]]:
        """Get macOS Calendar events for a specific date using AppleScript"""
        try:
            # Simpler AppleScript that's less likely to timeout
            applescript = f'''
            tell application "Calendar"
                set todaysEvents to {{}}
                set today to current date
                set startOfDay to today - (time of today)
                set endOfDay to startOfDay + (24 * 60 * 60)
                
                repeat with cal in calendars
                    try
                        set dayEvents to (every event of cal whose start date ≥ startOfDay and start date < endOfDay)
                        repeat with evt in dayEvents
                            set end of todaysEvents to (summary of evt as string)
                        end repeat
                    end try
                end repeat
                
                return todaysEvents
            end tell
            '''
            
            # Execute AppleScript with shorter timeout
            result = subprocess.run(
                ['osascript', '-e', applescript],
                capture_output=True,
                text=True,
                timeout=5  # Reduced timeout
            )
            
            if result.returncode == 0:
                return self._parse_simple_events(result.stdout)
            else:
                print(f"AppleScript error: {result.stderr}")
                return []
                
        except subprocess.TimeoutExpired:
            print("Calendar access timed out")
            return []
        except Exception as e:
            print(f"Calendar access error: {e}")
            return []
    
    async def _get_macos_upcoming_events(self, limit: int) -> List[Dict[str, Any]]:
        """Get upcoming macOS Calendar events"""
        try:
            applescript = f'''
            tell application "Calendar"
                set eventList to {{}}
                set currentDate to current date
                set endDate to currentDate + (7 * 24 * 60 * 60) -- Next 7 days
                
                repeat with cal in calendars
                    set calEvents to (every event of cal whose start date >= currentDate and start date < endDate)
                    repeat with evt in calEvents
                        set eventRecord to {{title:(summary of evt), startDate:(start date of evt), endDate:(end date of evt), calendar:(name of cal)}}
                        set end of eventList to eventRecord
                    end repeat
                end repeat
                
                return eventList
            end tell
            '''
            
            result = subprocess.run(
                ['osascript', '-e', applescript],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                events = self._parse_applescript_events(result.stdout)
                # Sort by start time and limit results
                events.sort(key=lambda x: x.get('start_time', ''))
                return events[:limit]
            else:
                print(f"AppleScript error: {result.stderr}")
                return []
                
        except Exception as e:
            print(f"Calendar access error: {e}")
            return []
    
    def _parse_simple_events(self, output: str) -> List[Dict[str, Any]]:
        """Parse simple AppleScript output into event objects"""
        events = []
        
        try:
            # Clean up the output and split by commas
            clean_output = output.strip()
            if not clean_output or clean_output == "{}":
                return events
                
            # Remove curly braces and split on commas
            clean_output = clean_output.strip('{}').strip()
            if not clean_output:
                return events
                
            event_titles = [title.strip().strip('"') for title in clean_output.split(',')]
            
            for title in event_titles:
                if title:
                    event = {
                        'title': title,
                        'start_time': 'today',  # Simplified for now
                        'calendar': 'Calendar'
                    }
                    events.append(event)
        except Exception as e:
            print(f"Error parsing calendar events: {e}")
        
        return events
    
    def _format_calendar_response(self, events: List[Dict[str, Any]], time_scope: str) -> str:
        """Format calendar events into a natural response"""
        if not events:
            return f"You don't have any events {time_scope}."
        
        if len(events) == 1:
            event = events[0]
            return f"You have one event {time_scope}: {event['title']} at {event.get('start_time', 'unknown time')}."
        
        response = f"You have {len(events)} events {time_scope}: "
        event_descriptions = []
        
        for event in events:
            time_str = event.get('start_time', 'unknown time')
            event_descriptions.append(f"{event['title']} at {time_str}")
        
        if len(event_descriptions) <= 3:
            response += ", ".join(event_descriptions) + "."
        else:
            response += ", ".join(event_descriptions[:3]) + f", and {len(event_descriptions) - 3} more."
        
        return response
    
    def get_help_text(self) -> str:
        return "Ask about your calendar! Try: 'What's on my calendar today?' or 'What's my next meeting?'"
    
    def get_supported_intents(self) -> List[str]:
        return ['calendar']


# Test function
if __name__ == "__main__":
    import asyncio
    
    async def test_calendar():
        plugin = CalendarPlugin()
        result = await plugin.execute("What's on my calendar today?")
        print(result)
    
    asyncio.run(test_calendar())
