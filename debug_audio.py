#!/usr/bin/env python3
"""Debug audio recording issues."""

import sounddevice as sd
import numpy as np
from stt_engine import transcribe_audio

# Set the correct microphone
sd.default.device = [0, 2]  # iPhone Microphone input, MacBook Speakers output

print("Testing audio capture...")
print("Say something in 3 seconds...")

audio_data = sd.rec(int(3 * 16000), samplerate=16000, channels=1, dtype='float32')
sd.wait()

# Check audio levels
max_level = np.max(np.abs(audio_data))
mean_level = np.mean(np.abs(audio_data))

print(f"Audio stats:")
print(f"  Max level: {max_level:.4f}")
print(f"  Mean level: {mean_level:.4f}")
print(f"  Shape: {audio_data.shape}")

if max_level < 0.001:
    print("❌ No audio detected - microphone may be muted")
elif max_level < 0.01:
    print("⚠️ Very quiet audio - speak louder or move closer")
else:
    print("✅ Audio captured successfully")
    
# Try transcribing anyway
print("\nTrying transcription...")
text = transcribe_audio(audio_data)
if text:
    print(f"Transcribed: {text}")
else:
    print("No transcription (likely detected as silence)")
    
# Check the silence threshold
print(f"\nCurrent silence threshold in stt_engine: 0.01")
print(f"Your audio mean level: {mean_level:.4f}")
if mean_level < 0.01:
    print("→ Your audio is being rejected as silence. Speak louder!")
