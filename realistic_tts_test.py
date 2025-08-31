#!/usr/bin/env python3
"""
Realistic TTS latency measurement and optimization
"""

import sys
import time
import json
import threading
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def measure_realistic_tts_latency():
    """Measure actual TTS latency with proper timing"""
    
    print("Realistic TTS Latency Measurement")
    print("=" * 40)
    
    # Test different TTS backends
    backends = []
    
    # 1. Test pyttsx3 (System TTS)
    try:
        import pyttsx3
        backends.append(("System TTS (pyttsx3)", test_pyttsx3_latency))
        print("✅ System TTS available")
    except ImportError:
        print("❌ System TTS not available")
    
    # 2. Test Google TTS
    try:
        from gtts import gTTS
        backends.append(("Google TTS (gtts)", test_gtts_latency))
        print("✅ Google TTS available")
    except ImportError:
        print("❌ Google TTS not available")
    
    # 3. Test macOS say command
    try:
        result = subprocess.run(['say', '--version'], capture_output=True)
        if result.returncode == 0:
            backends.append(("macOS Say", test_say_latency))
            print("✅ macOS Say available")
        else:
            print("❌ macOS Say not available")
    except FileNotFoundError:
        print("❌ macOS Say not available")
    
    if not backends:
        print("❌ No TTS backends available for testing")
        return
    
    print(f"\n🧪 Testing {len(backends)} TTS backends...")
    
    test_phrases = [
        "Hello",
        "I'm ready to help",
        "That's interesting",
        "I didn't catch that, could you repeat it?",
        "Let me think about that for a moment while I process your request"
    ]
    
    results = {}
    
    for backend_name, test_func in backends:
        print(f"\n📊 Testing {backend_name}...")
        backend_results = []
        
        for phrase in test_phrases:
            latency = test_func(phrase)
            backend_results.append({
                'phrase': phrase,
                'length': len(phrase),
                'latency': latency
            })
            print(f"  '{phrase[:20]}...' ({len(phrase)} chars): {latency:.3f}s")
        
        # Calculate averages
        valid_results = [r for r in backend_results if r['latency'] > 0]
        if valid_results:
            avg_latency = sum(r['latency'] for r in valid_results) / len(valid_results)
            results[backend_name] = {
                'results': backend_results,
                'average_latency': avg_latency,
                'success_rate': len(valid_results) / len(backend_results)
            }
            print(f"  Average: {avg_latency:.3f}s, Success: {len(valid_results)}/{len(backend_results)}")
        else:
            print(f"  ❌ All tests failed")
    
    # Summary
    print(f"\n📈 Performance Summary:")
    print("-" * 50)
    
    sorted_backends = sorted(results.items(), key=lambda x: x[1]['average_latency'])
    
    for backend_name, data in sorted_backends:
        avg = data['average_latency']
        success = data['success_rate'] * 100
        
        speed_rating = "🚀 Excellent" if avg < 0.1 else "✅ Good" if avg < 0.5 else "⚠️ Acceptable" if avg < 1.0 else "❌ Slow"
        
        print(f"{backend_name:20} | {avg:6.3f}s avg | {success:5.1f}% success | {speed_rating}")
    
    # Recommendations
    print(f"\n💡 Recommendations:")
    if results:
        fastest = sorted_backends[0]
        print(f"• Use {fastest[0]} for lowest latency ({fastest[1]['average_latency']:.3f}s)")
        
        # Realistic expectations
        best_latency = fastest[1]['average_latency']
        if best_latency < 0.1:
            print(f"• Sub-100ms latency is achievable with {fastest[0]}")
        elif best_latency < 0.5:
            print(f"• Sub-500ms latency is realistic")
        else:
            print(f"• Expect >500ms latency - consider caching strategies")
    
    return results

def test_pyttsx3_latency(text: str) -> float:
    """Test pyttsx3 latency"""
    try:
        import pyttsx3
        
        # Measure time to start speaking (not complete)
        start_time = time.time()
        
        engine = pyttsx3.init()
        engine.setProperty('rate', 200)  # Faster speech
        
        # Use threading to measure start time, not completion time
        speaking_started = threading.Event()
        
        def on_start(name):
            speaking_started.set()
        
        engine.connect('started-utterance', on_start)
        
        # Start speaking
        engine.say(text)
        engine.startLoop(False)
        
        # Wait for speech to start (not complete)
        speaking_started.wait(timeout=2.0)
        latency = time.time() - start_time
        
        engine.stop()
        
        return latency if speaking_started.is_set() else -1
        
    except Exception as e:
        print(f"  pyttsx3 error: {e}")
        return -1

def test_gtts_latency(text: str) -> float:
    """Test Google TTS latency"""
    try:
        from gtts import gTTS
        import tempfile
        
        start_time = time.time()
        
        # Generate audio file
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
            tts = gTTS(text=text, lang="en", slow=False)
            tts.save(f.name)
            
            # Measure time until we can start playback
            generation_time = time.time() - start_time
            
            # Start playback (this is when user hears audio)
            try:
                subprocess.Popen(['afplay', f.name], 
                               stdout=subprocess.DEVNULL, 
                               stderr=subprocess.DEVNULL)
                total_latency = time.time() - start_time
                
                # Cleanup
                Path(f.name).unlink(missing_ok=True)
                
                return total_latency
            except Exception:
                Path(f.name).unlink(missing_ok=True)
                return generation_time  # At least return generation time
        
    except Exception as e:
        print(f"  gtts error: {e}")
        return -1

def test_say_latency(text: str) -> float:
    """Test macOS say command latency"""
    try:
        start_time = time.time()
        
        # Start say command (it begins speaking immediately)
        process = subprocess.Popen(
            ['say', text],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        
        # Measure time to start (say starts immediately)
        latency = time.time() - start_time
        
        # Don't wait for completion, just measure start time
        return latency
        
    except Exception as e:
        print(f"  say error: {e}")
        return -1

def test_streaming_tts_improvements():
    """Test our streaming TTS implementation"""
    print(f"\n🎯 Testing Streaming TTS Implementation...")
    
    try:
        from src.core.tts.factory import TTSFactory
        
        config = {
            "tts": {
                "type": "google",
                "streaming": True,
                "cache_enabled": True
            }
        }
        
        tts = TTSFactory.create(config)
        
        test_phrases = [
            "Hello, I'm ready to help!",
            "I didn't catch that",
            "Let me think about that"
        ]
        
        print("Testing streaming TTS with caching...")
        
        total_latency = 0
        successful_tests = 0
        
        for i, phrase in enumerate(test_phrases):
            print(f"  Test {i+1}: '{phrase}'")
            
            # First call (should cache)
            start_time = time.time()
            success = tts.speak(phrase)
            latency = time.time() - start_time
            
            if success:
                print(f"    First call: {latency:.3f}s")
                successful_tests += 1
                total_latency += latency
                
                time.sleep(0.5)  # Brief pause
                
                # Second call (should be cached)
                start_time = time.time()
                success = tts.speak(phrase)
                cached_latency = time.time() - start_time
                
                if success:
                    improvement = (latency - cached_latency) / latency * 100
                    print(f"    Cached call: {cached_latency:.3f}s ({improvement:.1f}% faster)")
            else:
                print(f"    ❌ Failed")
            
            # Stop any ongoing speech
            if hasattr(tts, 'stop'):
                tts.stop()
                time.sleep(0.2)
        
        if successful_tests > 0:
            avg_latency = total_latency / successful_tests
            print(f"\n  Streaming TTS Average: {avg_latency:.3f}s")
            
            if avg_latency < 0.01:
                print("  🚀 Sub-10ms latency achieved!")
            elif avg_latency < 0.1:
                print("  ✅ Sub-100ms latency achieved")
            elif avg_latency < 0.5:
                print("  ⚠️ Sub-500ms latency")
            else:
                print("  ❌ >500ms latency")
        
    except ImportError as e:
        print(f"  ❌ Could not test streaming TTS: {e}")
    except Exception as e:
        print(f"  ❌ Streaming TTS test failed: {e}")

if __name__ == "__main__":
    results = measure_realistic_tts_latency()
    test_streaming_tts_improvements()
