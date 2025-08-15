#!/usr/bin/env python3
"""Test script to verify imports work as shown in the image."""

def test_imports():
    """Test all imports as shown in the image."""
    try:
        from core.stt.factory import STTFactory
        print("STT OK")
    except Exception as e:
        print(f"STT ERROR: {e}")
        return False

    try:
        from core.tts.factory import TTSFactory
        print("TTS OK")
    except Exception as e:
        print(f"TTS ERROR: {e}")
        return False

    try:
        from core.vad.webrtc_vad import SimpleVAD
        print("VAD OK")
    except Exception as e:
        print(f"VAD ERROR: {e}")
        return False

    try:
        from core.telemetry import Telemetry
        print("TELEMETRY OK")
    except Exception as e:
        print(f"TELEMETRY ERROR: {e}")
        return False

    try:
        from core.pipeline import run_once
        print("PIPELINE OK")
    except Exception as e:
        print(f"PIPELINE ERROR: {e}")
        return False

    return True

def test_vad_methods():
    """Test that SimpleVAD has the required methods."""
    try:
        from core.vad.webrtc_vad import SimpleVAD
        vad = SimpleVAD()
        
        # Test .start() method
        vad.start()
        print("VAD .start() method OK")
        
        # Test .feed_is_voice() method  
        result = vad.feed_is_voice(True)
        print(f"VAD .feed_is_voice() method OK: {result}")
        
        return True
    except Exception as e:
        print(f"VAD METHOD ERROR: {e}")
        return False

if __name__ == "__main__":
    print("Testing imports...")
    if test_imports():
        print("All imports work!")
        
        print("\nTesting VAD methods...")
        if test_vad_methods():
            print("VAD methods work!")
        else:
            print("VAD methods failed!")
    else:
        print("Some imports failed!")
