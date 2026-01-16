#!/usr/bin/env python3
"""Test if chunked recording causes transcription issues"""

import sounddevice as sd
import whisper
import numpy as np
import soundfile as sf
import time

print("=" * 70)
print("CHUNKED RECORDING TEST")
print("=" * 70)

print("\n🎤 Testing chunked recording (like voice_enhanced_penny.py)")
print("📢 Say: 'What is your take on trust'")
print("   Press Enter when done speaking...\n")

import threading

recording = True
audio_chunks = []

def check_for_enter():
    global recording
    input("   (Press Enter to stop) ")
    recording = False
    print("⏹️  Stopping recording...")

# Start Enter detection
enter_thread = threading.Thread(target=check_for_enter, daemon=True)
enter_thread.start()

print("🔴 RECORDING NOW...")

# Record in chunks (EXACT SAME as voice_enhanced_penny.py)
while recording:
    chunk = sd.rec(int(0.5 * 16000), samplerate=16000, channels=1, blocking=True)
    if recording:
        audio_chunks.append(chunk)

# Combine chunks (EXACT SAME as voice_enhanced_penny.py)
if audio_chunks:
    audio_data = np.concatenate(audio_chunks, axis=0)
else:
    audio_data = np.array([[]])

print(f"\n📊 Chunked Audio Properties:")
print(f"   Total chunks: {len(audio_chunks)}")
print(f"   Combined shape: {audio_data.shape}")
print(f"   Data type: {audio_data.dtype}")
print(f"   Max amplitude: {audio_data.max():.4f}")
print(f"   Duration: {len(audio_data)/16000:.2f} seconds")

# Save
sf.write('chunked_test.wav', audio_data, 16000)
print(f"   Saved to: chunked_test.wav")

# Transcribe with same method as stt_engine.py
print(f"\n🎙️  Transcribing chunked audio...")
model = whisper.load_model("base")
result = model.transcribe('chunked_test.wav')

print(f"\n📝 Chunked Recording Transcription:")
print(f"   '{result['text']}'")

# Now test NON-chunked for comparison
print(f"\n" + "=" * 70)
print("COMPARISON: Non-chunked recording")
print("=" * 70)

print("\n🎤 Recording 5 seconds (non-chunked)...")
print("📢 Say SAME phrase: 'What is your take on trust'")
print("   (Starting in 2 seconds...)\n")

time.sleep(2)
print("🔴 RECORDING NOW...")

# Record as single chunk
audio_single = sd.rec(int(5 * 16000), samplerate=16000, channels=1, dtype='float32', blocking=True)

print(f"\n📊 Single-Chunk Audio Properties:")
print(f"   Shape: {audio_single.shape}")
print(f"   Data type: {audio_single.dtype}")
print(f"   Max amplitude: {audio_single.max():.4f}")

# Save
sf.write('single_test.wav', audio_single, 16000)
print(f"   Saved to: single_test.wav")

# Transcribe
print(f"\n🎙️  Transcribing single-chunk audio...")
result_single = model.transcribe('single_test.wav')

print(f"\n📝 Single-Chunk Recording Transcription:")
print(f"   '{result_single['text']}'")

# Compare
print(f"\n" + "=" * 70)
print("COMPARISON RESULTS")
print("=" * 70)
print(f"\nChunked:  '{result['text']}'")
print(f"Single:   '{result_single['text']}'")

chunked_words = set(result['text'].lower().split())
single_words = set(result_single['text'].lower().split())

overlap = chunked_words & single_words
print(f"\nWord overlap: {len(overlap)} words")

if 'trust' in result['text'].lower():
    print("✅ Chunked method captured 'trust'")
else:
    print("❌ Chunked method MISSED 'trust'")

if 'trust' in result_single['text'].lower():
    print("✅ Single method captured 'trust'")
else:
    print("❌ Single method MISSED 'trust'")
