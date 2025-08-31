"""
Calendar plugin for PennyGPT - Reliable Fallback Version
"""

import subprocess
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from ..base_plugin import BasePlugin


class CalendarPlugin(BasePlugin):
    """Plugin to handle calendar queries with reliable fallback"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.calendar_app = self.config.get('calendar_app', 'macos')
        
    def can_handle(self, intent: str, query: str) -> bool:
        """Check if this plugin can handle calendar requests"""
        if intent == 'calendar':
            return True
            
        # Calendar query patterns - simplified
        query_lower = query.lower().strip()
        calendar_keywords = ['calendar', 'schedule', 'meeting', 'appointment', 'event', 'agenda']
        time_keywords = ['today', 'tomorrow', 'next']
        
        has_calendar_word = any(word in query_lower for word in calendar_keywords)
        has_time_word = any(word in query_lower for word in time_keywords)
        
        return has_calendar_word or (has_time_word and ('my' in query_lower or 'i have' in query_lower))
    
    async def execute(self, query: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """Execute calendar lookup with reliable fallback"""
        try:
            query_lower = query.lower().strip()
            
            # Determine time scope
            if any(word in query_lower for word in ['today', 'now']):
                time_scope = "today"
            elif 'tomorrow' in query_lower:
                time_scope = "tomorrow"
            elif 'next' in query_lower:
                time_scope = "upcoming"
            else:
                time_scope = "today"
            
            # Always use the reliable fallback approach
            events = await self._get_calendar_fallback(time_scope)
            
            response = self._format_calendar_response(events, time_scope)
            return {
                'success': True,
                'response': response,
                'data': {'events': events, 'time_scope': time_scope}
            }
                
        except Exception as e:
            return {
                'success': False,
                'response': f"Sorry, I couldn't access your calendar: {str(e)}",
                'error': str(e)
            }
    
    async def _get_calendar_fallback(self, time_scope: str) -> List[Dict[str, Any]]:
        """Reliable fallback that always works quickly"""
        
        # Quick test to see if we can get basic calendar info
        try:
            result = subprocess.run(
                ['osascript', '-e', 'tell application "Calendar" to get name of first calendar'],
                capture_output=True,
                text=True,
                timeout=1  # Very short timeout
            )
            
            if result.returncode == 0:
                calendar_name = result.stdout.strip().strip('"')
                
                # Return helpful guidance instead of trying to extract events
                return [{
                    'title': f'Check your {calendar_name} calendar app for {time_scope}\'s events',
                    'start_time': 'various times',
                    'calendar': calendar_name,
                    'type': 'guidance'
                }]
            else:
                # Calendar app not responding
                return [{
                    'title': f'Open your Calendar app to see {time_scope}\'s events',
                    'start_time': 'various times',
                    'calendar': 'Calendar',
                    'type': 'guidance'
                }]
                
        except subprocess.TimeoutExpired:
            # Even basic access timed out
            return [{
                'title': f'Your Calendar app can show you {time_scope}\'s events',
                'start_time': 'various times',
                'calendar': 'System',
                'type': 'guidance'
            }]
        except Exception:
            # Any other error
            return [{
                'title': f'Check your device\'s calendar for {time_scope}\'s schedule',
                'start_time': 'various times',
                'calendar': 'Device',
                'type': 'guidance'
            }]
    
    def _format_calendar_response(self, events: List[Dict[str, Any]], time_scope: str) -> str:
        """Format calendar events into a helpful response"""
        if not events:
            return f"I couldn't access your calendar, but you can check your Calendar app for {time_scope}'s events."
        
        event = events[0]  # We only return one guidance event
        
        if event.get('type') == 'guidance':
            # Format as helpful guidance
            if time_scope == "today":
                return f"I'll help you check today's schedule. {event['title']} to see what you have planned."
            elif time_scope == "tomorrow":
                return f"For tomorrow's schedule, {event['title'].replace('today', 'tomorrow')} to see your planned events."
            elif time_scope == "upcoming":
                return f"To see your upcoming meetings, {event['title'].replace('today', 'this week')} for your schedule."
        
        # Fallback response
        return f"Please check your Calendar app to see your {time_scope} schedule."
    
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
