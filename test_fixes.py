#!/usr/bin/env python3
"""Test script to verify our fixes work correctly."""

def test_imports():
    """Test that all critical imports work."""
    print("Testing imports...")
    
    try:
        from src.core.llm_router import load_config, get_llm
        print("✅ LLM router imports OK")
    except Exception as e:
        print(f"❌ LLM router import failed: {e}")
        return False

    try:
        from src.core.personality import apply
        print("✅ Personality imports OK")
    except Exception as e:
        print(f"❌ Personality import failed: {e}")
        return False

    try:
        from src.core.stt.factory import STTFactory
        print("✅ STT factory imports OK")
    except Exception as e:
        print(f"❌ STT factory import failed: {e}")
        return False

    try:
        from src.core.tts.factory import TTSFactory
        print("✅ TTS factory imports OK")
    except Exception as e:
        print(f"❌ TTS factory import failed: {e}")
        return False

    try:
        from src.core.vad.webrtc_vad import SimpleVAD
        print("✅ VAD imports OK")
    except Exception as e:
        print(f"❌ VAD import failed: {e}")
        return False

    try:
        from src.adapters.llm.factory import LLMFactory
        print("✅ LLM factory imports OK")
    except Exception as e:
        print(f"❌ LLM factory import failed: {e}")
        return False
    
    return True

def test_config_loading():
    """Test configuration loading."""
    print("\nTesting config loading...")
    
    try:
        from src.core.llm_router import load_config
        config = load_config()
        print(f"✅ Config loaded successfully: {type(config)}")
        print(f"   Config keys: {list(config.keys())}")
        return True
    except Exception as e:
        print(f"❌ Config loading failed: {e}")
        return False

def test_personality():
    """Test personality functionality."""
    print("\nTesting personality...")
    
    try:
        from src.core.personality import apply
        result = apply("Hello world")
        print(f"✅ Personality apply works: '{result}'")
        
        # Test with settings
        result2 = apply("Test", {"sarcasm": "high"})
        print(f"✅ Personality with settings: '{result2}'")
        return True
    except Exception as e:
        print(f"❌ Personality test failed: {e}")
        return False

def test_vad():
    """Test VAD functionality."""
    print("\nTesting VAD...")
    
    try:
        from src.core.vad.webrtc_vad import SimpleVAD
        vad = SimpleVAD()
        
        # Test the fixed method signature
        result = vad.feed_is_voice(b"test audio data")
        print(f"✅ VAD feed_is_voice works: {result}")
        return True
    except Exception as e:
        print(f"❌ VAD test failed: {e}")
        return False

def test_llm_creation():
    """Test LLM creation."""
    print("\nTesting LLM creation...")
    
    try:
        from src.core.llm_router import get_llm
        llm = get_llm()
        print(f"✅ LLM created: {type(llm)}")
        
        # Test generation
        result = llm.generate("Hello")
        print(f"✅ LLM generate works: '{result}'")
        return True
    except Exception as e:
        print(f"❌ LLM creation failed: {e}")
        return False

def main():
    """Run all tests."""
    print("🧪 Testing Penny Assistant fixes...\n")
    
    tests = [
        test_imports,
        test_config_loading,
        test_personality,
        test_vad,
        test_llm_creation,
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                print("   Test failed!")
        except Exception as e:
            print(f"   Test crashed: {e}")
    
    print(f"\n📊 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Fixes are working correctly.")
        return True
    else:
        print("⚠️  Some tests failed. There may still be issues.")
        return False

if __name__ == "__main__":
    main()
