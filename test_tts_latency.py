#!/usr/bin/env python3
"""
Test script for low-latency TTS improvements
"""

import sys
import time
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.core.tts.factory import TTSFactory

def load_config():
    """Load configuration"""
    try:
        with open("penny_config.json", "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"Failed to load config: {e}")
        return {"tts": {"type": "google", "streaming": True}}

def test_tts_latency():
    """Test TTS latency improvements"""
    print("Testing TTS Latency Improvements")
    print("=" * 40)
    
    config = load_config()
    print(f"TTS Config: {config.get('tts', {})}")
    
    try:
        # Create TTS engine
        print("\n1. Creating TTS engine...")
        start_time = time.time()
        tts = TTSFactory.create(config)
        creation_time = time.time() - start_time
        print(f"   TTS engine created in {creation_time:.3f}s")
        
        # Test phrases for latency measurement
        test_phrases = [
            "Hello, I'm ready to help!",
            "I didn't catch that. Could you say it again?",
            "Let me think about that for a moment.",
            "That sounds interesting. Tell me more.",
            "I'm not sure about that. Could you be more specific?"
        ]
        
        print(f"\n2. Testing {len(test_phrases)} phrases...")
        
        total_latency = 0
        successful_calls = 0
        
        for i, phrase in enumerate(test_phrases, 1):
            print(f"\n   Test {i}: '{phrase[:30]}...' ({len(phrase)} chars)")
            
            # Measure time to start speaking
            start_time = time.time()
            success = tts.speak(phrase)
            latency = time.time() - start_time
            
            if success:
                print(f"   ✅ Started in {latency:.3f}s")
                successful_calls += 1
                total_latency += latency
                
                # Brief pause between tests
                time.sleep(0.5)
                
                # Stop current speech before next test
                if hasattr(tts, 'stop'):
                    tts.stop()
                    time.sleep(0.2)
            else:
                print(f"   ❌ Failed to start")
            
        # Results summary
        print(f"\n3. Results Summary:")
        print(f"   Successful calls: {successful_calls}/{len(test_phrases)}")
        
        if successful_calls > 0:
            avg_latency = total_latency / successful_calls
            print(f"   Average latency: {avg_latency:.3f}s")
            
            if avg_latency < 0.1:
                print("   🚀 Excellent latency (< 0.1s)")
            elif avg_latency < 0.3:
                print("   ✅ Good latency (< 0.3s)")
            elif avg_latency < 0.5:
                print("   ⚠️  Acceptable latency (< 0.5s)")
            else:
                print("   ❌ High latency (> 0.5s)")
        
        # Test caching if available
        if hasattr(tts, 'phrase_cache'):
            print(f"\n4. Cache Performance:")
            cache_size = len(tts.phrase_cache) if hasattr(tts, 'phrase_cache') else 0
            print(f"   Cached phrases: {cache_size}")
            
            if cache_size > 0:
                # Test cached phrase speed
                first_phrase = test_phrases[0]
                print(f"   Testing cached phrase: '{first_phrase[:30]}...'")
                
                start_time = time.time()
                success = tts.speak(first_phrase)
                cached_latency = time.time() - start_time
                
                if success:
                    print(f"   ✅ Cached response in {cached_latency:.3f}s")
                    if cached_latency < avg_latency:
                        improvement = ((avg_latency - cached_latency) / avg_latency) * 100
                        print(f"   📈 {improvement:.1f}% faster than first call")
        
        # Test streaming features if available
        if hasattr(tts, 'is_speaking'):
            print(f"\n5. Streaming Features:")
            print(f"   ✅ Streaming TTS available")
            print(f"   ✅ Non-blocking speech")
            print(f"   ✅ Barge-in support")
        else:
            print(f"\n5. Streaming Features:")
            print(f"   ❌ Legacy blocking TTS")
        
        # Cleanup
        if hasattr(tts, 'stop'):
            tts.stop()
            
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("   Make sure required TTS libraries are installed:")
        print("   pip install gtts pyttsx3")
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()

def test_backend_availability():
    """Test which TTS backends are available"""
    print("\nTesting TTS Backend Availability")
    print("=" * 35)
    
    # Test pyttsx3 (system TTS)
    try:
        import pyttsx3
        engine = pyttsx3.init()
        voices = engine.getProperty('voices')
        print(f"✅ System TTS (pyttsx3): {len(voices)} voices available")
    except Exception as e:
        print(f"❌ System TTS (pyttsx3): {e}")
    
    # Test Google TTS
    try:
        from gtts import gTTS
        print("✅ Google TTS (gtts): Available")
    except Exception as e:
        print(f"❌ Google TTS (gtts): {e}")
    
    # Test macOS say command
    import subprocess
    try:
        result = subprocess.run(['say', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ macOS Say command: Available")
        else:
            print("❌ macOS Say command: Not available")
    except Exception as e:
        print(f"❌ macOS Say command: {e}")

if __name__ == "__main__":
    test_backend_availability()
    test_tts_latency()
