#!/usr/bin/env python3
"""
TTS Cache Demo and Validation Script
Tests the perceived latency improvements from caching.
"""

import os
import sys
import time
import tempfile
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / 'src'))

def create_mock_audio_file(text: str, duration: float = 1.0) -> str:
    """Create a mock audio file for testing"""
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
        # Write some fake audio data
        temp_file.write(f"MOCK_AUDIO_DATA_FOR:{text}:{duration}".encode())
        return temp_file.name

def test_cache_performance():
    """Test cache performance improvements"""
    print("🧪 Testing TTS Cache Performance...")
    print("=" * 50)
    
    try:
        from adapters.tts.cache import TTSCache
        
        # Create cache instance
        cache_dir = tempfile.mkdtemp(prefix="penny_tts_demo_")
        cache = TTSCache(cache_dir=cache_dir, enable_pregeneration=False)
        
        test_phrases = [
            "Hello",
            "Thank you",
            "I'm sorry",
            "Let me check",
            "One moment please"
        ]
        
        print("📊 Testing cache miss (first generation):")
        generation_times = []
        
        for phrase in test_phrases:
            # Simulate generation time
            start_time = time.time()
            
            # Check cache (should be miss)
            cached_file = cache.get_cached_audio(phrase)
            assert cached_file is None, f"Unexpected cache hit for {phrase}"
            
            # Simulate TTS generation
            mock_audio = create_mock_audio_file(phrase, 1.0)
            time.sleep(0.1)  # Simulate generation delay
            
            # Cache the result
            cache.cache_generated_audio(phrase, mock_audio, 1.0)
            
            generation_time = time.time() - start_time
            generation_times.append(generation_time)
            
            print(f"  {phrase}: {generation_time:.3f}s (generated + cached)")
            
            # Cleanup
            os.unlink(mock_audio)
        
        print(f"\n⏱️  Average generation time: {sum(generation_times)/len(generation_times):.3f}s")
        
        print("\n⚡ Testing cache hit (instant retrieval):")
        retrieval_times = []
        
        for phrase in test_phrases:
            start_time = time.time()
            
            # Should hit cache now
            cached_file = cache.get_cached_audio(phrase)
            assert cached_file is not None, f"Cache miss for {phrase}"
            assert os.path.exists(cached_file), f"Cached file missing for {phrase}"
            
            retrieval_time = time.time() - start_time
            retrieval_times.append(retrieval_time)
            
            print(f"  {phrase}: {retrieval_time:.6f}s (cached)")
        
        print(f"\n⚡ Average retrieval time: {sum(retrieval_times)/len(retrieval_times):.6f}s")
        
        # Performance improvement
        avg_generation = sum(generation_times) / len(generation_times)
        avg_retrieval = sum(retrieval_times) / len(retrieval_times)
        improvement = (avg_generation - avg_retrieval) / avg_generation * 100
        
        print(f"\n🚀 Performance improvement: {improvement:.1f}% faster!")
        
        # Cache statistics
        stats = cache.get_stats()
        print(f"\n📈 Cache Statistics:")
        print(f"  Cached phrases: {stats['cached_phrases']}")
        print(f"  Cache hits: {stats['hits']}")
        print(f"  Cache misses: {stats['misses']}")
        print(f"  Hit rate: {stats['hit_rate']:.1%}")
        print(f"  Cache size: {stats['cache_size_mb']:.2f} MB")
        
        cache.shutdown()
        
        # Cleanup cache directory
        import shutil
        shutil.rmtree(cache_dir)
        
        return True
        
    except Exception as e:
        print(f"❌ Cache test failed: {e}")
        return False

def test_cache_integration():
    """Test cache integration with existing TTS"""
    print("\n🔗 Testing TTS Cache Integration...")
    print("=" * 40)
    
    try:
        # This would test integration with actual TTS
        # For now, just test imports and basic functionality
        
        from adapters.tts.cached_google_tts import CachedGoogleTTS
        print("✅ CachedGoogleTTS import successful")
        
        from adapters.tts.cache import get_tts_cache, initialize_tts_cache
        print("✅ Cache utilities import successful")
        
        # Test cache initialization
        cache = initialize_tts_cache()
        print("✅ Cache initialization successful")
        
        stats = cache.get_stats()
        print(f"✅ Cache stats available: {len(stats)} metrics")
        
        cache.shutdown()
        
        return True
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        return False

def test_background_pregeneration():
    """Test background pregeneration functionality"""
    print("\n🔄 Testing Background Pregeneration...")
    print("=" * 38)
    
    try:
        from adapters.tts.cache import TTSCache
        
        # Create cache with background processing enabled
        cache_dir = tempfile.mkdtemp(prefix="penny_bg_demo_")
        cache = TTSCache(cache_dir=cache_dir, enable_pregeneration=True)
        
        # Request pregeneration
        test_phrases = ["Hello background", "Thank you background"]
        
        for phrase in test_phrases:
            cache.request_pregeneration(phrase)
            print(f"✅ Requested pregeneration: {phrase}")
        
        # Give background thread a moment
        time.sleep(0.5)
        
        print(f"✅ Background thread active: {cache.background_thread.is_alive()}")
        print(f"✅ Queue not empty: {not cache.pregeneration_queue.empty()}")
        
        cache.shutdown()
        
        # Cleanup
        import shutil
        shutil.rmtree(cache_dir)
        
        return True
        
    except Exception as e:
        print(f"❌ Background test failed: {e}")
        return False

def main():
    """Run all TTS cache tests"""
    print("🏥 TTS Cache System Validation")
    print("=" * 50)
    
    tests = [
        ("Cache Performance", test_cache_performance),
        ("Cache Integration", test_cache_integration),
        ("Background Pregeneration", test_background_pregeneration)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n🧪 Running {test_name}...")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Test {test_name} crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("📋 Test Summary")
    print("=" * 50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\n📊 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All TTS cache tests passed!")
        print("💡 Your system is ready for perceived latency improvements!")
        print("\nNext steps:")
        print("1. Integrate CachedGoogleTTS into your pipeline")
        print("2. Test with real TTS generation")
        print("3. Monitor cache hit rates in production")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
