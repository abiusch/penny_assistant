#!/usr/bin/env python3
"""
Debug ElevenLabs audio playback issues
"""

import os
import requests
import subprocess
import tempfile

def test_elevenlabs_audio():
    """Test ElevenLabs API and audio playback step by step"""
    
    api_key = os.getenv("ELEVENLABS_API_KEY")
    if not api_key:
        print("❌ ELEVENLABS_API_KEY not set")
        return False
    
    print("🔧 Debug: Testing ElevenLabs Audio Pipeline")
    print("=" * 50)
    
    # Step 1: Test API
    print("1. Testing ElevenLabs API...")
    url = "https://api.elevenlabs.io/v1/text-to-speech/21m00Tcm4TlvDq8ikWAM"
    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": api_key
    }
    
    data = {
        "text": "Testing audio playback",
        "model_id": "eleven_monolingual_v1",
        "voice_settings": {
            "stability": 0.3,
            "similarity_boost": 0.7,
            "style": 0.2
        }
    }
    
    try:
        response = requests.post(url, json=data, headers=headers)
        print(f"   API Response: {response.status_code}")
        
        if response.status_code != 200:
            print(f"   ❌ API Error: {response.text}")
            return False
        
        print(f"   ✅ API Success - {len(response.content)} bytes received")
        
    except Exception as e:
        print(f"   ❌ API Exception: {e}")
        return False
    
    # Step 2: Save file
    print("\n2. Saving audio file...")
    try:
        audio_file = "/tmp/elevenlabs_debug.mp3"
        with open(audio_file, "wb") as f:
            f.write(response.content)
        
        file_size = os.path.getsize(audio_file)
        print(f"   ✅ File saved: {audio_file} ({file_size} bytes)")
        
    except Exception as e:
        print(f"   ❌ File save error: {e}")
        return False
    
    # Step 3: Check file format
    print("\n3. Checking file format...")
    try:
        # Use file command to check format
        result = subprocess.run(["file", audio_file], capture_output=True, text=True)
        print(f"   File type: {result.stdout.strip()}")
        
        # Try ffprobe if available
        try:
            result = subprocess.run(["ffprobe", "-v", "quiet", "-show_format", audio_file], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                print(f"   Format details: {result.stdout}")
        except:
            print("   (ffprobe not available)")
            
    except Exception as e:
        print(f"   ❌ File check error: {e}")
    
    # Step 4: Test different players
    print("\n4. Testing audio players...")
    
    players = [
        (["afplay", audio_file], "afplay (macOS default)"),
        (["open", audio_file], "open (macOS system)"),
        (["say", "Testing system speech"], "say (macOS TTS)")
    ]
    
    for cmd, name in players:
        try:
            print(f"   Testing {name}...")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                print(f"   ✅ {name} - Success")
            else:
                print(f"   ❌ {name} - Failed: {result.stderr}")
        except subprocess.TimeoutExpired:
            print(f"   ⏱️ {name} - Timeout (may have played)")
        except Exception as e:
            print(f"   ❌ {name} - Error: {e}")
    
    # Step 5: Check audio settings
    print("\n5. Checking macOS audio settings...")
    try:
        # Check default output device
        result = subprocess.run(["system_profiler", "SPAudioDataType"], 
                              capture_output=True, text=True)
        
        lines = result.stdout.split('\n')
        for i, line in enumerate(lines):
            if "Default Output Device" in line:
                print(f"   Default Output: {line.strip()}")
                # Print next few lines for context
                for j in range(1, 4):
                    if i+j < len(lines):
                        print(f"   {lines[i+j].strip()}")
                break
        else:
            print("   ⚠️ Could not find default output device info")
            
    except Exception as e:
        print(f"   ❌ Audio settings check failed: {e}")
    
    print(f"\n📁 Audio file saved to: {audio_file}")
    print("Try manually playing it with: afplay /tmp/elevenlabs_debug.mp3")
    
    return True

if __name__ == "__main__":
    test_elevenlabs_audio()
