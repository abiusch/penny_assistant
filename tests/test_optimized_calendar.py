#!/usr/bin/env python3
"""
Test the efficient calendar scripts in a simple way
"""

import subprocess

def test_optimized_calendar():
    """Test our optimized calendar approach"""
    
    print("Testing Optimized Calendar Access")
    print("=" * 35)
    
    # Test the exact script from our plugin
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
    
    try:
        print("Running optimized calendar script...")
        result = subprocess.run(
            ['osascript', '-e', applescript],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        print(f"Return code: {result.returncode}")
        print(f"Output: {result.stdout.strip()}")
        
        if result.stderr:
            print(f"Error: {result.stderr}")
            
        # Parse the output
        if result.returncode == 0:
            output = result.stdout.strip()
            if output == "NO_EVENTS":
                print("✅ No events found today")
            elif output.startswith("ERROR:"):
                print(f"❌ AppleScript error: {output}")
            else:
                print("✅ Found events:")
                events = output.split(',')
                for event in events:
                    if '|' in event:
                        title, time = event.split('|', 1)
                        print(f"  - {title.strip()} at {time.strip()}")
                        
    except subprocess.TimeoutExpired:
        print("❌ Script timed out")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_optimized_calendar()
