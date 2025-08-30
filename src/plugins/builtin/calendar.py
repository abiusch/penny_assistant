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
        """Get macOS Calendar events using optimized approach"""
        try:
            # Optimized AppleScript that checks only primary calendars
            applescript = '''
            tell application "Calendar"
                try
                    set today to current date
                    set startOfDay to today - (time of today)
                    set endOfDay to startOfDay + (24 * 60 * 60) - 1
                    
                    set eventList to {}
                    set maxEvents to 5
                    set currentCount to 0
                    
                    -- Get calendar count first
                    set calCount to count of calendars
                    
                    -- Only check first few calendars to avoid timeout
                    set maxCals to 3
                    if calCount < maxCals then set maxCals to calCount
                    
                    repeat with i from 1 to maxCals
                        if currentCount ≥ maxEvents then exit repeat
                        
                        try
                            set cal to calendar i
                            set dayEvents to (every event of cal whose start date ≥ startOfDay and start date ≤ endOfDay)
                            
                            repeat with evt in dayEvents
                                if currentCount ≥ maxEvents then exit repeat
                                
                                set eventTitle to summary of evt
                                set eventStart to start date of evt
                                set eventList to eventList & {eventTitle & "|" & (eventStart as string)}
                                set currentCount to currentCount + 1
                            end repeat
                        on error
                            -- Skip this calendar if error
                        end try
                    end repeat
                    
                    if (count of eventList) > 0 then
                        set AppleScript's text item delimiters to ","
                        set result to eventList as string
                        set AppleScript's text item delimiters to ""
                        return result
                    else
                        return "NO_EVENTS"
                    end if
                on error errMsg
                    return "ERROR:" & errMsg
                end try
            end tell
            '''
            
            result = subprocess.run(
                ['osascript', '-e', applescript],
                capture_output=True,
                text=True,
                timeout=5  # Slightly longer timeout
            )
            
            if result.returncode == 0:
                output = result.stdout.strip()
                return self._parse_applescript_events(output)
            else:
                print(f"AppleScript error: {result.stderr}")
                return []
                
        except subprocess.TimeoutExpired:
            print("Calendar access timed out - using fallback")
            # Return a helpful fallback message
            return [{'title': 'Calendar check timed out - please check manually', 'start_time': 'unknown', 'calendar': 'System'}]
        except Exception as e:
            print(f"Calendar access error: {e}")
            return []
    
    def _parse_applescript_events(self, output: str) -> List[Dict[str, Any]]:
        """Parse optimized AppleScript output into event objects"""
        events = []
        
        if not output or output == "NO_EVENTS":
            return events
        
        if output.startswith("ERROR:"):
            print(f"AppleScript error: {output}")
            return events
        
        try:
            # Split by commas (between events)
            event_parts = output.split(',')
            
            for part in event_parts:
                if '|' in part:
                    title, date_str = part.split('|', 1)
                    
                    # Parse the date string to create a cleaner time representation
                    time_str = self._format_date_string(date_str.strip())
                    
                    events.append({
                        'title': title.strip(),
                        'start_time': time_str,
                        'calendar': 'Calendar'
                    })
        except Exception as e:
            print(f"Error parsing AppleScript events: {e}")
        
        return events
    
    def _format_date_string(self, date_str: str) -> str:
        """Format AppleScript date string into readable time"""
        try:
            # AppleScript dates come in format like "Saturday, August 30, 2025 at 2:00:00 PM"
            if " at " in date_str:
                date_part, time_part = date_str.split(" at ", 1)
                # Extract just the time part
                return time_part.strip()
            else:
                # Fallback to just showing the date
                return date_str.strip()
        except:
            return "unknown time"
    
    async def _get_macos_upcoming_events(self, limit: int) -> List[Dict[str, Any]]:
        """Get upcoming macOS Calendar events using optimized approach"""
        try:
            # Optimized AppleScript for upcoming events
            applescript = f'''
            tell application "Calendar"
                try
                    set now to current date
                    set futureLimit to now + (7 * 24 * 60 * 60) -- 7 days ahead
                    
                    set eventList to {{}}
                    set maxEvents to {limit}
                    set currentCount to 0
                    
                    -- Get calendar count first
                    set calCount to count of calendars
                    
                    -- Only check first few calendars to avoid timeout
                    set maxCals to 3
                    if calCount < maxCals then set maxCals to calCount
                    
                    repeat with i from 1 to maxCals
                        if currentCount ≥ maxEvents then exit repeat
                        
                        try
                            set cal to calendar i
                            set futureEvents to (every event of cal whose start date > now and start date ≤ futureLimit)
                            
                            repeat with evt in futureEvents
                                if currentCount ≥ maxEvents then exit repeat
                                
                                set eventTitle to summary of evt
                                set eventStart to start date of evt
                                set eventList to eventList & {{eventTitle & "|" & (eventStart as string)}}
                                set currentCount to currentCount + 1
                            end repeat
                        on error
                            -- Skip this calendar if error
                        end try
                    end repeat
                    
                    if (count of eventList) > 0 then
                        set AppleScript's text item delimiters to ","
                        set result to eventList as string
                        set AppleScript's text item delimiters to ""
                        return result
                    else
                        return "NO_EVENTS"
                    end if
                on error errMsg
                    return "ERROR:" & errMsg
                end try
            end tell
            '''
            
            result = subprocess.run(
                ['osascript', '-e', applescript],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                output = result.stdout.strip()
                return self._parse_applescript_events(output)
            else:
                print(f"AppleScript error: {result.stderr}")
                return []
                
        except subprocess.TimeoutExpired:
            print("Upcoming events access timed out - using fallback")
            return [{'title': 'Upcoming events check timed out', 'start_time': 'unknown', 'calendar': 'System'}]
        except Exception as e:
            print(f"Upcoming events access error: {e}")
            return []
    
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
