#!/usr/bin/env python3
"""
Test streaming vs regular TTS for speed comparison
"""

import sys
import os
import time

sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def test_streaming_vs_regular():
    """Compare streaming vs regular TTS speed"""
    
    test_text = "Quantum physics is a fascinating field that studies the behavior of matter and energy at atomic and subatomic scales. At these incredibly small scales, the familiar rules of classical physics break down, and particles exhibit strange behaviors like superposition and entanglement."
    
    print("🚀 Testing TTS Speed Comparison")
    print("=" * 50)
    print(f"Test text length: {len(test_text)} characters")
    print()
    
    # Test 1: Regular ElevenLabs
    print("1. Testing Regular ElevenLabs TTS...")
    try:
        from adapters.tts.elevenlabs_tts_adapter import ElevenLabsTTS
        config = {'tts': {'cache_enabled': False}}  # Disable cache for fair test
        
        tts_regular = ElevenLabsTTS(config)
        
        start_time = time.time()
        success = tts_regular.speak(test_text)
        end_time = time.time()
        
        if success:
            print(f"   ✅ Regular TTS: {end_time - start_time:.2f} seconds")
        else:
            print(f"   ❌ Regular TTS failed")
            
    except Exception as e:
        print(f"   ❌ Regular TTS error: {e}")
    
    # Wait between tests
    time.sleep(2)
    
    # Test 2: Streaming ElevenLabs
    print("\n2. Testing Streaming ElevenLabs TTS...")
    try:
        from adapters.tts.streaming_elevenlabs_tts import StreamingElevenLabsTTS
        
        tts_streaming = StreamingElevenLabsTTS({'tts': {}})
        
        start_time = time.time()
        success = tts_streaming.speak(test_text)
        end_time = time.time()
        
        if success:
            print(f"   ✅ Streaming TTS: {end_time - start_time:.2f} seconds")
        else:
            print(f"   ❌ Streaming TTS failed")
            
    except Exception as e:
        print(f"   ❌ Streaming TTS error: {e}")
    
    print("\n🎯 Speed Test Complete!")
    print("The streaming version should start speaking much faster!")

if __name__ == "__main__":
    test_streaming_vs_regular()
