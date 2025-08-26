#!/usr/bin/env python3
"""Debug and calibrate audio settings for Penny Assistant."""

import sounddevice as sd
import numpy as np
import time

# Set the correct microphone
sd.default.device = 1  # MacBook Pro Microphone

def monitor_audio_levels(duration=10):
    """Monitor audio levels in real-time."""
    print("🎤 Monitoring audio levels for 10 seconds...")
    print("Speak at different volumes to see the levels")
    print("-" * 50)
    
    sample_rate = 16000
    block_size = int(sample_rate * 0.1)  # 100ms blocks
    
    def callback(indata, frames, time, status):
        volume = np.abs(indata).mean()
        # Create a visual bar
        bar_length = int(volume * 500)  # Scale for display
        bar = "█" * min(bar_length, 50)
        
        # Color code based on detection
        if volume < 0.002:
            status = "🔴 TOO QUIET"
        elif volume < 0.005:
            status = "🟡 BORDERLINE"
        else:
            status = "🟢 GOOD"
        
        print(f"Level: {volume:.4f} {status} {bar}")
    
    with sd.InputStream(callback=callback, 
                       channels=1, 
                       samplerate=sample_rate,
                       blocksize=block_size):
        time.sleep(duration)
    
    print("-" * 50)
    print("\nCalibration complete!")
    print("Current threshold: 0.002")
    print("If mostly 🔴, lower threshold further")
    print("If mostly 🟢, current settings are good")

def test_different_durations():
    """Test recording at different durations."""
    print("\nTesting different recording durations...")
    
    for duration in [2, 3, 5]:
        print(f"\n📢 Speak something in {duration} seconds...")
        time.sleep(0.5)
        
        audio = sd.rec(int(duration * 16000), samplerate=16000, channels=1)
        sd.wait()
        
        volume = np.abs(audio).mean()
        max_vol = np.abs(audio).max()
        
        print(f"  Duration: {duration}s")
        print(f"  Mean volume: {volume:.4f}")
        print(f"  Max volume: {max_vol:.4f}")
        
        if volume < 0.002:
            print("  ❌ Would be filtered as silence")
        else:
            print("  ✅ Would be processed")

if __name__ == "__main__":
    print("Audio Calibration Tool for Penny Assistant")
    print("=" * 50)
    
    # First monitor real-time levels
    monitor_audio_levels()
    
    # Then test recording
    print("\nWant to test recording? (y/n): ", end="")
    if input().lower() == 'y':
        test_different_durations()
    
    print("\nRecommendations:")
    print("1. If audio is consistently too quiet, try:")
    print("   - Speaking louder/closer to mic")
    print("   - Reducing silence threshold below 0.002")
    print("   - Checking System Settings > Sound > Input volume")
    print("\n2. Current threshold: 0.002 (just lowered from 0.005)")
