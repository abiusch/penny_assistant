#!/usr/bin/env python3
"""
Quick test to debug the audio issue
"""

import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from adapters.tts.elevenlabs_tts_adapter import ElevenLabsTTS

def debug_audio():
    config = {'tts': {'cache_enabled': True}}
    
    try:
        tts = ElevenLabsTTS(config)
        
        print("🔧 Debugging audio issue...")
        
        # Test 1: Simple text
        print("\n1. Testing simple text...")
        success = tts.speak("Hello, this is a test.")
        print(f"   Result: {success}")
        
        # Test 2: Long text (like quantum physics response)
        print("\n2. Testing long text...")
        long_text = "Quantum physics is a fascinating field that studies matter and energy at atomic scales."
        success = tts.speak(long_text)
        print(f"   Result: {success}")
        
        # Test 3: Check if audio files are being created
        print("\n3. Checking temp files...")
        import subprocess
        result = subprocess.run(["ls", "-la", "/tmp/"], capture_output=True, text=True)
        temp_files = [line for line in result.stdout.split('\n') if 'eleven' in line or '.mp3' in line]
        for file_line in temp_files[-5:]:  # Show last 5 files
            print(f"   {file_line}")
        
        # Test 4: Manual file playback
        print("\n4. Testing manual playback of last file...")
        if temp_files:
            # Extract filename from last temp file
            last_file = temp_files[-1].split()[-1] if temp_files else None
            if last_file and last_file.endswith('.mp3'):
                file_path = f"/tmp/{last_file}"
                print(f"   Playing: {file_path}")
                result = subprocess.run(["afplay", file_path], capture_output=True, text=True)
                print(f"   afplay result: {result.returncode}")
                if result.stderr:
                    print(f"   Error: {result.stderr}")
        
    except Exception as e:
        print(f"❌ Debug failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_audio()
