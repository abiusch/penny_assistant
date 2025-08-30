#!/usr/bin/env python3
"""
Test simplified calendar approaches
"""

import subprocess
import asyncio
from datetime import datetime, timedelta

async def test_minimal_calendar():
    """Test the most minimal calendar query possible"""
    print("Testing minimal calendar query...")
    
    # Try to get just one event from one calendar
    applescript = '''
    tell application "Calendar"
        try
            set homeCalendar to calendar "Home"
            set todaysEvents to (every event of homeCalendar whose start date > (current date) - (1 * days) and start date < (current date) + (1 * days))
            if (count of todaysEvents) > 0 then
                set firstEvent to item 1 of todaysEvents
                return summary of firstEvent
            else
                return "No events"
            end if
        on error
            return "Calendar access error"
        end try
    end tell
    '''
    
    try:
        result = subprocess.run(
            ['osascript', '-e', applescript],
            capture_output=True,
            text=True,
            timeout=3
        )
        print(f"Result: {result.stdout}")
        return result.stdout.strip()
    except subprocess.TimeoutExpired:
        print("Minimal query timed out")
        return None

async def test_calendar_app_status():
    """Check if Calendar app is running and responsive"""
    print("Testing Calendar app status...")
    
    applescript = '''
    tell application "System Events"
        if (name of processes) contains "Calendar" then
            return "Calendar is running"
        else
            return "Calendar is not running"
        end if
    end tell
    '''
    
    try:
        result = subprocess.run(
            ['osascript', '-e', applescript],
            capture_output=True,
            text=True,
            timeout=2
        )
        print(f"Calendar status: {result.stdout}")
    except Exception as e:
        print(f"Error checking Calendar status: {e}")

async def test_eventkit_alternative():
    """Test using EventKit through Python (if available)"""
    print("Testing EventKit alternative...")
    
    try:
        import EventKit
        store = EventKit.EKEventStore()
        
        # Request access
        def access_granted(granted, error):
            print(f"EventKit access: {granted}")
            if error:
                print(f"EventKit error: {error}")
        
        store.requestAccessToEntityType_completion_(
            EventKit.EKEntityTypeEvent, 
            access_granted
        )
        
        return True
    except ImportError:
        print("EventKit not available (need pyobjc-framework-EventKit)")
        return False
    except Exception as e:
        print(f"EventKit error: {e}")
        return False

async def main():
    print("Calendar Alternative Testing")
    print("=" * 40)
    
    await test_calendar_app_status()
    await test_minimal_calendar()
    await test_eventkit_alternative()
    
    print("\nRecommendation:")
    print("Consider implementing a fallback that asks user to manually check their calendar")
    print("or use a simplified 'no calendar integration' mode")

if __name__ == "__main__":
    asyncio.run(main())
