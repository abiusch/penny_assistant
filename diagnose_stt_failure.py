#!/usr/bin/env python3
"""
CRITICAL: Diagnose why STT is producing garbage transcriptions
"""

import sounddevice as sd
import numpy as np
import soundfile as sf
import whisper
import sys

print("=" * 70)
print("STT FAILURE ROOT CAUSE DIAGNOSTIC")
print("=" * 70)

# Test 1: Check if Whisper works with proper audio
print("\n📋 TEST 1: Whisper with known good audio")
print("=" * 70)

print("Recording 3 seconds with SIMPLE method (no chunking)...")
print("Say clearly: 'Hello Penny'")

import time
time.sleep(1)
print("🔴 Recording...")

simple_audio = sd.rec(int(3 * 16000), samplerate=16000, channels=1, dtype='float32', blocking=True)

print(f"Audio shape: {simple_audio.shape}")
print(f"Audio dtype: {simple_audio.dtype}")
print(f"Audio range: [{simple_audio.min():.4f}, {simple_audio.max():.4f}]")

sf.write('test_simple.wav', simple_audio, 16000)

model = whisper.load_model("base")
result = model.transcribe('test_simple.wav')

print(f"\nTranscription: '{result['text']}'")
if 'hello' in result['text'].lower() or 'penny' in result['text'].lower():
    print("✅ Simple method works correctly")
else:
    print("❌ Even simple method is broken - Whisper or mic issue")
    sys.exit(1)

# Test 2: Chunked recording (like voice_enhanced_penny.py)
print("\n" + "=" * 70)
print("📋 TEST 2: Chunked recording (current voice_enhanced_penny.py method)")
print("=" * 70)

print("\nRecording with chunking for 3 seconds...")
print("Say clearly: 'This is a test'")

time.sleep(1)
print("🔴 Recording...")

chunks = []
for i in range(6):  # 6 chunks of 0.5s
    chunk = sd.rec(int(0.5 * 16000), samplerate=16000, channels=1, dtype='float32', blocking=True)
    chunks.append(chunk)

# Concatenate EXACTLY as voice_enhanced_penny.py does
chunked_audio = np.concatenate(chunks, axis=0)

print(f"\nChunked audio properties:")
print(f"  Number of chunks: {len(chunks)}")
print(f"  Each chunk shape: {chunks[0].shape}")
print(f"  Combined shape: {chunked_audio.shape}")
print(f"  Combined dtype: {chunked_audio.dtype}")
print(f"  Expected shape: ({int(3 * 16000)}, 1)")

# Check if shape is wrong
if chunked_audio.shape != (int(3 * 16000), 1):
    print(f"  ⚠️  WARNING: Shape mismatch!")

sf.write('test_chunked.wav', chunked_audio, 16000)

result_chunked = model.transcribe('test_chunked.wav')

print(f"\nChunked transcription: '{result_chunked['text']}'")

if 'test' in result_chunked['text'].lower():
    print("✅ Chunked method works")
else:
    print("❌ Chunked method produces garbage")

    # Try fix: flatten before concatenate
    print("\n🔧 Trying fix: flatten before concatenate...")
    flattened_chunks = [chunk.flatten() for chunk in chunks]
    fixed_audio = np.concatenate(flattened_chunks, axis=0)
    print(f"  Fixed shape: {fixed_audio.shape}")

    sf.write('test_fixed.wav', fixed_audio, 16000)
    result_fixed = model.transcribe('test_fixed.wav')
    print(f"  Fixed transcription: '{result_fixed['text']}'")

    if 'test' in result_fixed['text'].lower():
        print("  ✅ FLATTENING FIXES IT!")
        print("\n" + "=" * 70)
        print("ROOT CAUSE IDENTIFIED:")
        print("Chunked audio needs to be flattened before concatenation")
        print("\nFIX for voice_enhanced_penny.py:")
        print("  Change: audio_data = np.concatenate(audio_chunks, axis=0)")
        print("  To:     audio_data = np.concatenate([c.flatten() for c in audio_chunks])")
        print("=" * 70)

# Test 3: Check current stt_engine.py
print("\n" + "=" * 70)
print("📋 TEST 3: Test actual stt_engine.py function")
print("=" * 70)

sys.path.insert(0, '/Users/CJ/Desktop/penny_assistant')
from stt_engine import transcribe_audio

print("\nTesting stt_engine.transcribe_audio() with chunked audio...")
transcription = transcribe_audio(chunked_audio)

print(f"stt_engine result: '{transcription}'")

if transcription and 'test' in transcription.lower():
    print("✅ stt_engine works with chunked audio")
else:
    print("❌ stt_engine fails with chunked audio")
    print("   Checking if shape is the issue...")

    # Try with flattened
    transcription_flat = transcribe_audio(fixed_audio.reshape(-1, 1) if len(fixed_audio.shape) == 1 else fixed_audio)
    print(f"   With reshape: '{transcription_flat}'")
