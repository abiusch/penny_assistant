#!/usr/bin/env python3
"""Test if numpy concatenation is corrupting audio shape"""

import numpy as np
import sounddevice as sd
import soundfile as sf
import whisper

print("=" * 70)
print("NUMPY CONCATENATION TEST")
print("=" * 70)

print("\n🎤 Recording with chunked method...")
print("📢 Say: 'Testing numpy concatenation'")
print("   (Recording for 3 seconds)\n")

# Simulate chunked recording
chunks = []
for i in range(6):  # 6 chunks of 0.5 seconds = 3 seconds
    chunk = sd.rec(int(0.5 * 16000), samplerate=16000, channels=1, dtype='float32', blocking=True)
    chunks.append(chunk)
    print(f"   Chunk {i+1}/6: shape={chunk.shape}, dtype={chunk.dtype}")

print("\n📊 Analyzing chunks before concatenation:")
for i, chunk in enumerate(chunks):
    print(f"   Chunk {i}: shape={chunk.shape}, ndim={chunk.ndim}, dtype={chunk.dtype}")

# Method 1: Current concatenation (axis=0)
print("\n🔧 Method 1: np.concatenate(chunks, axis=0)")
audio_axis0 = np.concatenate(chunks, axis=0)
print(f"   Result shape: {audio_axis0.shape}")
print(f"   Result ndim: {audio_axis0.ndim}")
print(f"   Result dtype: {audio_axis0.dtype}")

# Save and test
sf.write('concat_axis0.wav', audio_axis0, 16000)

# Method 2: Squeeze chunks first
print("\n🔧 Method 2: Squeeze chunks then concatenate")
chunks_squeezed = [chunk.squeeze() for chunk in chunks]
for i, chunk in enumerate(chunks_squeezed[:3]):
    print(f"   Squeezed chunk {i}: shape={chunk.shape}, ndim={chunk.ndim}")

audio_squeezed = np.concatenate(chunks_squeezed, axis=0)
print(f"   Result shape: {audio_squeezed.shape}")
print(f"   Result ndim: {audio_squeezed.ndim}")

sf.write('concat_squeezed.wav', audio_squeezed, 16000)

# Method 3: Flatten each chunk
print("\n🔧 Method 3: Flatten chunks then concatenate")
audio_flattened = np.concatenate([chunk.flatten() for chunk in chunks], axis=0)
print(f"   Result shape: {audio_flattened.shape}")
print(f"   Result ndim: {audio_flattened.ndim}")

sf.write('concat_flattened.wav', audio_flattened, 16000)

# Transcribe all three
print("\n🎙️  Transcribing all methods...")
model = whisper.load_model("base")

result1 = model.transcribe('concat_axis0.wav')
result2 = model.transcribe('concat_squeezed.wav')
result3 = model.transcribe('concat_flattened.wav')

print("\n📝 Transcription Results:")
print(f"\n   Method 1 (axis=0):    '{result1['text']}'")
print(f"   Method 2 (squeezed):  '{result2['text']}'")
print(f"   Method 3 (flattened): '{result3['text']}'")

# Check which is best
target = "concatenation"
print(f"\n🎯 Accuracy check (looking for '{target}'):")
print(f"   Method 1: {'✅' if target in result1['text'].lower() else '❌'}")
print(f"   Method 2: {'✅' if target in result2['text'].lower() else '❌'}")
print(f"   Method 3: {'✅' if target in result3['text'].lower() else '❌'}")
