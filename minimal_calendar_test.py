#!/usr/bin/env python3
"""
Ultra-minimal AppleScript for calendar access
"""

import subprocess
import time

def test_minimal_calendar():
    """Test the most basic calendar operations"""
    
    print("Ultra-Minimal Calendar Test")
    print("=" * 30)
    
    # Test 1: Just check if Calendar app is available
    print("1. Testing Calendar app availability...")
    try:
        result = subprocess.run(
            ['osascript', '-e', 'tell application "Calendar" to return "OK"'],
            capture_output=True,
            text=True,
            timeout=2
        )
        print(f"Calendar app response: {result.stdout.strip()}")
        print(f"Return code: {result.returncode}")
    except subprocess.TimeoutExpired:
        print("Calendar app test timed out")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 2: Get calendar count only
    print("\n2. Testing calendar count...")
    try:
        result = subprocess.run(
            ['osascript', '-e', 'tell application "Calendar" to return count of calendars'],
            capture_output=True,
            text=True,
            timeout=2
        )
        print(f"Calendar count: {result.stdout.strip()}")
        print(f"Return code: {result.returncode}")
    except subprocess.TimeoutExpired:
        print("Calendar count test timed out")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 3: Get just first calendar name
    print("\n3. Testing first calendar name...")
    try:
        result = subprocess.run(
            ['osascript', '-e', 'tell application "Calendar" to return name of calendar 1'],
            capture_output=True,
            text=True,
            timeout=2
        )
        print(f"First calendar: {result.stdout.strip()}")
        print(f"Return code: {result.returncode}")
    except subprocess.TimeoutExpired:
        print("First calendar test timed out")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 4: Simple event count for first calendar only
    print("\n4. Testing event count for first calendar only...")
    try:
        script = '''
        tell application "Calendar"
            set cal to calendar 1
            set today to current date
            set startOfDay to today - (time of today)
            set endOfDay to startOfDay + (24 * 60 * 60)
            
            set dayEvents to (every event of cal whose start date ≥ startOfDay and start date < endOfDay)
            return count of dayEvents
        end tell
        '''
        
        result = subprocess.run(
            ['osascript', '-e', script],
            capture_output=True,
            text=True,
            timeout=5
        )
        print(f"Event count for first calendar: {result.stdout.strip()}")
        print(f"Return code: {result.returncode}")
        if result.stderr:
            print(f"Error: {result.stderr}")
    except subprocess.TimeoutExpired:
        print("Event count test timed out")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 5: Alternative approach - use System Events
    print("\n5. Testing System Events approach...")
    try:
        script = '''
        tell application "System Events"
            if exists process "Calendar" then
                return "Calendar is running"
            else
                return "Calendar is not running"
            end if
        end tell
        '''
        
        result = subprocess.run(
            ['osascript', '-e', script],
            capture_output=True,
            text=True,
            timeout=2
        )
        print(f"System Events result: {result.stdout.strip()}")
    except Exception as e:
        print(f"System Events error: {e}")

if __name__ == "__main__":
    test_minimal_calendar()
