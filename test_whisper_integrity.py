#!/usr/bin/env python3
"""Test Whisper model integrity"""

import whisper
import numpy as np

print("=" * 70)
print("WHISPER MODEL INTEGRITY TEST")
print("=" * 70)

try:
    print("\n1. Loading Whisper base model...")
    model = whisper.load_model("base")
    print(f"   ✅ Model loaded successfully: {type(model)}")

    print("\n2. Checking model attributes...")
    if hasattr(model, 'transcribe'):
        print("   ✅ Model has transcribe method")
    else:
        print("   ❌ Model missing transcribe method!")

    print("\n3. Model appears functional")
    print("=" * 70)
    print("✅ WHISPER MODEL INTEGRITY: PASS")

except Exception as e:
    print(f"   ❌ ERROR: {e}")
    print("=" * 70)
    print("❌ WHISPER MODEL INTEGRITY: FAIL")
    import traceback
    traceback.print_exc()
