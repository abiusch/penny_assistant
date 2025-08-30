#!/usr/bin/env python3
"""
Efficient AppleScript templates for calendar queries
"""

import subprocess
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

class EfficientCalendarScripts:
    """Collection of optimized AppleScript templates for calendar access"""
    
    @staticmethod
    def get_today_events_fast() -> str:
        """Get today's events using optimized AppleScript"""
        return '''
        tell application "Calendar"
            set today to current date
            set startOfDay to today - (time of today)
            set endOfDay to startOfDay + (24 * 60 * 60) - 1
            
            set eventList to {}
            set maxEvents to 10
            set currentCount to 0
            
            try
                -- Only check first few calendars for speed
                set calList to calendars
                repeat with i from 1 to (count of calList)
                    if currentCount ≥ maxEvents then exit repeat
                    
                    set cal to item i of calList
                    try
                        set dayEvents to (every event of cal whose start date ≥ startOfDay and start date ≤ endOfDay)
                        
                        repeat with evt in dayEvents
                            if currentCount ≥ maxEvents then exit repeat
                            
                            set eventTitle to summary of evt
                            set eventStart to start date of evt
                            set eventList to eventList & {eventTitle & "|" & (eventStart as string)}
                            set currentCount to currentCount + 1
                        end repeat
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
    
    @staticmethod
    def get_next_events_fast(limit: int = 5) -> str:
        """Get next few events using optimized AppleScript"""
        return f'''
        tell application "Calendar"
            set now to current date
            set futureLimit to now + (7 * 24 * 60 * 60) -- 7 days ahead
            
            set eventList to {{}}
            set maxEvents to {limit}
            set currentCount to 0
            
            try
                repeat with cal in calendars
                    if currentCount ≥ maxEvents then exit repeat
                    
                    try
                        set futureEvents to (every event of cal whose start date > now and start date ≤ futureLimit)
                        
                        repeat with evt in futureEvents
                            if currentCount ≥ maxEvents then exit repeat
                            
                            set eventTitle to summary of evt
                            set eventStart to start date of evt
                            set eventList to eventList & {{eventTitle & "|" & (eventStart as string)}}
                            set currentCount to currentCount + 1
                        end repeat
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
    
    @staticmethod
    def get_calendar_names_fast() -> str:
        """Get calendar names quickly"""
        return '''
        tell application "Calendar"
            try
                set calNames to {}
                repeat with cal in calendars
                    set calNames to calNames & {name of cal}
                end repeat
                
                set AppleScript's text item delimiters to ","
                set result to calNames as string
                set AppleScript's text item delimiters to ""
                return result
            on error errMsg
                return "ERROR:" & errMsg
            end try
        end tell
        '''
    
    @staticmethod
    def get_event_count_fast() -> str:
        """Count today's events quickly without full details"""
        return '''
        tell application "Calendar"
            set today to current date
            set startOfDay to today - (time of today)
            set endOfDay to startOfDay + (24 * 60 * 60) - 1
            
            set totalCount to 0
            
            try
                repeat with cal in calendars
                    try
                        set dayEvents to (every event of cal whose start date ≥ startOfDay and start date ≤ endOfDay)
                        set totalCount to totalCount + (count of dayEvents)
                    end try
                end repeat
                
                return totalCount as string
            on error errMsg
                return "ERROR:" & errMsg
            end try
        end tell
        '''

def run_applescript(script: str, timeout: int = 3) -> tuple[bool, str, str]:
    """Run AppleScript with timeout and error handling"""
    try:
        result = subprocess.run(
            ['osascript', '-e', script],
            capture_output=True,
            text=True,
            timeout=timeout
        )
        return result.returncode == 0, result.stdout.strip(), result.stderr.strip()
    except subprocess.TimeoutExpired:
        return False, "", "TIMEOUT"
    except Exception as e:
        return False, "", str(e)

def parse_event_output(output: str) -> List[Dict[str, Any]]:
    """Parse event output from optimized AppleScript"""
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
                events.append({
                    'title': title.strip(),
                    'start_time': date_str.strip(),
                    'calendar': 'Calendar'
                })
    except Exception as e:
        print(f"Error parsing events: {e}")
    
    return events

def test_efficient_scripts():
    """Test the efficient AppleScript implementations"""
    scripts = EfficientCalendarScripts()
    
    print("Testing Efficient Calendar Scripts")
    print("=" * 40)
    
    # Test calendar names
    print("1. Testing calendar names...")
    success, output, error = run_applescript(scripts.get_calendar_names_fast())
    print(f"Success: {success}")
    print(f"Output: {output}")
    if error: print(f"Error: {error}")
    
    # Test event count
    print("\n2. Testing event count...")
    success, output, error = run_applescript(scripts.get_event_count_fast())
    print(f"Success: {success}")
    print(f"Output: {output}")
    if error: print(f"Error: {error}")
    
    # Test today's events
    print("\n3. Testing today's events...")
    success, output, error = run_applescript(scripts.get_today_events_fast())
    print(f"Success: {success}")
    print(f"Output: {output}")
    if error: print(f"Error: {error}")
    
    if success and output:
        events = parse_event_output(output)
        print(f"Parsed {len(events)} events:")
        for event in events:
            print(f"  - {event['title']} at {event['start_time']}")
    
    # Test next events
    print("\n4. Testing next events...")
    success, output, error = run_applescript(scripts.get_next_events_fast(3))
    print(f"Success: {success}")
    print(f"Output: {output}")
    if error: print(f"Error: {error}")
    
    if success and output:
        events = parse_event_output(output)
        print(f"Parsed {len(events)} upcoming events:")
        for event in events:
            print(f"  - {event['title']} at {event['start_time']}")

if __name__ == "__main__":
    test_efficient_scripts()
