#!/usr/bin/env python3
"""Test audio recording and transcription quality"""

import sounddevice as sd
import soundfile as sf
import whisper
import numpy as np
import sys

print("=" * 70)
print("AUDIO QUALITY DIAGNOSTIC TEST")
print("=" * 70)

print("\n🎤 Recording 5 seconds of audio...")
print("📢 Say clearly: 'This is a test of the recording system'")
print("   (Recording starts in 2 seconds...)\n")

import time
time.sleep(2)

# Record with same settings as voice_enhanced_penny.py
sample_rate = 16000
duration = 5

print("🔴 RECORDING NOW...")
audio = sd.rec(
    int(duration * sample_rate),
    samplerate=sample_rate,
    channels=1,
    dtype='float32',
    blocking=True
)
print("⏹️  Recording complete\n")

# Save for inspection
sf.write('diagnostic_test.wav', audio, sample_rate)
print("💾 Audio saved to diagnostic_test.wav")

# Check audio properties
print(f"\n📊 Audio Properties:")
print(f"   Shape: {audio.shape}")
print(f"   Sample rate: {sample_rate} Hz")
print(f"   Duration: {duration} seconds")
print(f"   Data type: {audio.dtype}")
print(f"   Min value: {audio.min():.4f}")
print(f"   Max value: {audio.max():.4f}")
print(f"   Mean: {audio.mean():.4f}")
print(f"   RMS: {np.sqrt(np.mean(audio**2)):.4f}")

# Analyze audio quality
print(f"\n🔍 Quality Analysis:")
if audio.max() < 0.01:
    print("   ❌ WARNING: Audio appears SILENT or extremely quiet!")
    print("      → Microphone may not be working")
    print("      → Check System Preferences > Sound > Input")
elif audio.max() < 0.05:
    print("   ⚠️  WARNING: Audio is very quiet")
    print("      → Speak louder or move closer to microphone")
elif audio.max() > 0.95:
    print("   ⚠️  WARNING: Audio may be CLIPPING (too loud)")
    print("      → Lower input volume or speak quieter")
else:
    print(f"   ✅ Audio level good ({audio.max():.3f})")

# Check if audio is mostly silence
silence_ratio = np.sum(np.abs(audio) < 0.01) / len(audio)
print(f"   Silence ratio: {silence_ratio:.1%}")
if silence_ratio > 0.9:
    print("   ❌ WARNING: Audio is >90% silence!")

# Transcribe
print(f"\n🎙️  Transcribing with Whisper...")
try:
    model = whisper.load_model("base")
    result = model.transcribe('diagnostic_test.wav')

    print(f"\n📝 Transcription Result:")
    print(f"   Text: '{result['text']}'")
    print(f"   Language: {result.get('language', 'unknown')}")

    # Compare with expected
    expected_phrases = [
        "test",
        "recording",
        "system"
    ]

    actual = result['text'].lower().strip()

    matches = sum(1 for phrase in expected_phrases if phrase in actual)

    print(f"\n🎯 Accuracy Check:")
    print(f"   Expected words found: {matches}/{len(expected_phrases)}")

    if matches >= 2:
        print("   ✅ Transcription appears ACCURATE")
    elif matches == 1:
        print("   ⚠️  Transcription PARTIALLY accurate")
    else:
        print("   ❌ Transcription WRONG!")
        print(f"      Expected keywords: {expected_phrases}")
        print(f"      Got: '{actual}'")

except Exception as e:
    print(f"   ❌ Transcription ERROR: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 70)
print("DIAGNOSTIC COMPLETE")
print("=" * 70)
