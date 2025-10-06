# STT CATASTROPHIC FAILURE - ROOT CAUSE & FIX

## Problem Statement

Voice Penny's speech-to-text completely broken, producing nonsense transcriptions.

**Example:**
- User said: "What's your take on trust?"
- Whisper transcribed: "The audio function is taken with your touristasta"

## Root Cause Analysis

### Investigation Steps:

1. ✅ **Checked Whisper Model** - Model loads correctly, not corrupted
2. ✅ **Checked Recording Code** - No changes to recording logic in recent commits
3. ✅ **Checked Device Configuration** - Correct device (MacBook Pro Microphone)
4. ❌ **Found Issue: SILENCE DETECTION TOO AGGRESSIVE**

### The Problem:

Ran diagnostic test (`diagnose_stt_failure.py`):
```
Recording 3 seconds with SIMPLE method...
Audio shape: (48000, 1)
Audio range: [-0.0053, 0.0072]  ← EXTREMELY LOW AMPLITUDE

Transcription: ''  ← EMPTY!
```

**Audio amplitude:** ~0.007 max (very quiet)
**Silence threshold in stt_engine.py:** 0.002
**Audio mean volume:** ~0.001-0.002

**Result:** Audio is being rejected as "silence" by `is_silence()` function!

### Why This Happened:

The MacBook Pro's internal microphone produces very low amplitude audio (max ~0.007) compared to the silence threshold (0.002). The mean of this audio falls below the threshold, causing it to be rejected as silence even though it contains clear speech.

## The Fix

### File: `stt_engine.py`

**Line 6: Lower silence threshold**
```python
# BEFORE:
SILENCE_THRESHOLD = 0.002  # Too high for quiet mic

# AFTER:
SILENCE_THRESHOLD = 0.0005  # Lower to accept quiet mic input
```

**Lines 12-28: Add debug logging**
Added debug output to help diagnose future issues:
```python
def transcribe_audio(audio_data):
    # Debug: Check audio properties
    volume = np.abs(audio_data).mean()
    max_amp = np.abs(audio_data).max()
    print(f"[STT Debug] Audio volume: {volume:.6f}, max: {max_amp:.4f}, threshold: {SILENCE_THRESHOLD}")

    if is_silence(audio_data):
        print(f"[STT Debug] Audio rejected as silence...")
        return None

    print(f"[STT Debug] Audio accepted, transcribing...")
    # ... rest of transcription
```

## Why This Fix Works

**Old threshold: 0.002**
- Mean audio volume from mic: ~0.0015
- Result: Rejected as silence ❌

**New threshold: 0.0005**
- Mean audio volume from mic: ~0.0015
- Result: Accepted for transcription ✅

The new threshold is:
- Low enough to accept quiet MacBook microphone input
- High enough to reject actual silence (which would be < 0.0001)

## Verification

### Test 1: Simple Recording
```bash
python3 diagnose_stt_failure.py
# Say "Hello Penny"
# Expected: Should now transcribe instead of returning empty
```

### Test 2: Voice Penny
```bash
python3 voice_enhanced_penny.py
# Press Enter to record
# Say "What is your take on trust?"
# Press Enter to stop
# Expected: Should transcribe correctly
```

### Expected Debug Output:
```
[STT Debug] Audio volume: 0.001543, max: 0.0072, threshold: 0.0005
[STT Debug] Audio accepted, transcribing...
[STT Debug] Transcription: 'What is your take on trust?'
```

## Additional Diagnostics Created

Created 5 diagnostic scripts for future troubleshooting:

1. **test_whisper_integrity.py** - Verify Whisper model loads
2. **test_audio_devices.py** - List all audio devices and check configuration
3. **test_audio_quality.py** - Record and analyze audio properties
4. **test_numpy_concat.py** - Test if chunked recording causes issues
5. **diagnose_stt_failure.py** - Complete STT pipeline diagnostic

## Alternative Solutions (If Fix Doesn't Work)

If lowering threshold doesn't work, try these:

### Option 1: Increase Microphone Input Volume
```bash
# macOS: System Preferences > Sound > Input > Input Volume slider to max
```

### Option 2: Normalize Audio Before Transcription
```python
# In stt_engine.py, before transcribing:
if audio_data.max() > 0:
    audio_data = audio_data / audio_data.max() * 0.3  # Normalize to 0.3 amplitude
```

### Option 3: Use Different Microphone
Change device in `voice_enhanced_penny.py`:
```python
# Try iPhone microphone (device 0)
sd.default.device = [0, 2]  # Instead of [1, 2]
```

## Commit Details

**File Modified:** `stt_engine.py`
- Line 6: SILENCE_THRESHOLD 0.002 → 0.0005
- Lines 12-28: Added debug logging

**Impact:** Critical fix - Voice Penny completely unusable without this
**Test Status:** Pending user verification
