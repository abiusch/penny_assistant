#!/usr/bin/env python3
"""
Debug calendar access issues
"""

import subprocess
import time
from datetime import datetime

def test_simple_calendar_access():
    """Test basic calendar access"""
    print("Testing basic calendar access...")
    
    try:
        # Simple test - just get calendar names
        result = subprocess.run(
            ['osascript', '-e', 'tell application "Calendar" to get name of calendars'],
            capture_output=True,
            text=True,
            timeout=5
        )
        print(f"Calendar names result: {result.returncode}")
        print(f"Output: {result.stdout}")
        if result.stderr:
            print(f"Error: {result.stderr}")
    except subprocess.TimeoutExpired:
        print("Calendar names query timed out")
    except Exception as e:
        print(f"Error: {e}")

def test_event_count():
    """Test getting event count for today"""
    print("\nTesting event count...")
    
    try:
        applescript = '''
        tell application "Calendar"
            set eventCount to 0
            set today to current date
            set startOfDay to today - (time of today)
            set endOfDay to startOfDay + (24 * 60 * 60)
            
            repeat with cal in calendars
                try
                    set dayEvents to (every event of cal whose start date ≥ startOfDay and start date < endOfDay)
                    set eventCount to eventCount + (count of dayEvents)
                end try
            end repeat
            
            return eventCount
        end tell
        '''
        
        result = subprocess.run(
            ['osascript', '-e', applescript],
            capture_output=True,
            text=True,
            timeout=5
        )
        print(f"Event count result: {result.returncode}")
        print(f"Output: {result.stdout}")
        if result.stderr:
            print(f"Error: {result.stderr}")
    except subprocess.TimeoutExpired:
        print("Event count query timed out")
    except Exception as e:
        print(f"Error: {e}")

def test_sqlite_calendar():
    """Test direct SQLite access to calendar database"""
    print("\nTesting SQLite calendar access...")
    
    import os
    import sqlite3
    
    # Common calendar database paths
    calendar_paths = [
        os.path.expanduser("~/Library/Calendars/Calendar.sqlitedb"),
        os.path.expanduser("~/Library/Application Support/CalendarAgent/Calendar.sqlitedb"),
        os.path.expanduser("~/Library/Calendars/LocalCalendar.calendar/Events.sqlite")
    ]
    
    for path in calendar_paths:
        if os.path.exists(path):
            print(f"Found calendar database: {path}")
            try:
                conn = sqlite3.connect(path)
                cursor = conn.cursor()
                
                # Try to get table names
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                tables = cursor.fetchall()
                print(f"Tables: {tables}")
                
                conn.close()
                return path
            except Exception as e:
                print(f"Error accessing {path}: {e}")
    
    print("No accessible calendar databases found")
    return None

if __name__ == "__main__":
    print("Calendar Debug Script")
    print("=" * 40)
    
    test_simple_calendar_access()
    test_event_count()
    test_sqlite_calendar()
