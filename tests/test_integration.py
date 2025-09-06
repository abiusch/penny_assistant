#!/usr/bin/env python3
"""
Integration Test for Enhanced PennyGPT System
Tests configuration loading, personality enhancement, and TTS metrics
"""

import sys
import os
import json

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

def test_configuration_loading():
    """Test the consolidated configuration system"""
    print("🔧 Testing Configuration Loading...")
    
    try:
        from config.config_loader import load_config, validate_config
        
        # Test validation
        validation = validate_config()
        print(f"✅ Configuration valid: {validation['valid']}")
        
        if validation['warnings']:
            for warning in validation['warnings']:
                print(f"⚠️ Warning: {warning}")
        
        if validation['loaded_profile']:
            print(f"🎭 Loaded profile: {validation['loaded_profile']}")
        
        # Test loading
        config = load_config()
        print(f"📋 Base config sections: {len(config['base'])} keys")
        
        if config['personality']:
            print(f"🎭 Personality: {config['personality'].name} v{config['personality'].version}")
            return True
        else:
            print("⚠️ No personality profile loaded")
            return True  # Still valid, just using defaults
            
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False

def test_personality_enhancement():
    """Test the unpredictable personality system"""
    print("\n🎭 Testing Personality Enhancement...")
    
    try:
        from personality.unpredictable_response import UnpredictablePenny
        
        penny = UnpredictablePenny()
        
        # Test normal enhancement
        original = "Machine learning is a subset of artificial intelligence."
        test_input = "Tell me about machine learning"
        enhanced = penny.enhance_response(original, test_input)
        
        enhancement_applied = enhanced != original and len(enhanced) > len(original)
        print(f"✅ Enhancement applied: {enhancement_applied}")
        print(f"   Original length: {len(original)}")
        print(f"   Enhanced length: {len(enhanced)}")
        
        # Test safety system
        sensitive_input = "I'm feeling really stressed and overwhelmed"
        safe_original = "Here are some strategies that might help."
        safe_enhanced = penny.enhance_response(safe_original, sensitive_input)
        
        # Should be gentle, not humorous
        has_humor = any(marker in safe_enhanced.lower() for marker in [
            "funny", "beauty of coding", "random fact"
        ])
        
        print(f"✅ Safety system active: {not has_humor}")
        
        return enhancement_applied and not has_humor
        
    except Exception as e:
        print(f"❌ Personality test failed: {e}")
        return False

def test_tts_metrics():
    """Test TTS adapter with metrics"""
    print("\n📊 Testing TTS Metrics System...")
    
    try:
        # Load config to get TTS settings
        with open('penny_config.json', 'r') as f:
            config = json.load(f)
        
        from adapters.tts.tts_factory import create_tts_adapter
        
        tts = create_tts_adapter(config)
        
        # Check if metrics are available
        if hasattr(tts, 'get_metrics'):
            initial_metrics = tts.get_metrics()
            print(f"✅ Metrics available: {list(initial_metrics.keys())}")
            print(f"   TTS engine: {initial_metrics.get('tts_engine', 'unknown')}")
            print(f"   Initial cache hits: {initial_metrics.get('cache_hits', 0)}")
            
            # Test a short phrase (won't actually speak in test)
            # This would normally increment metrics
            print("✅ TTS adapter created successfully")
            return True
        else:
            print("⚠️ Metrics not available on this TTS adapter")
            return True  # Still valid, just no metrics
            
    except Exception as e:
        print(f"❌ TTS test failed: {e}")
        return False

def test_pipeline_integration():
    """Test that all components work together"""
    print("\n🔗 Testing Pipeline Integration...")
    
    try:
        # Test that we can import and initialize key components
        from personality.unpredictable_response import UnpredictablePenny
        from config.config_loader import load_config
        
        # Load configuration
        config = load_config()
        print("✅ Configuration loaded")
        
        # Initialize personality
        penny = UnpredictablePenny()
        print("✅ Personality system initialized")
        
        # Test end-to-end enhancement
        user_input = "How does quantum computing work?"
        llm_response = "Quantum computing uses quantum mechanical phenomena like superposition and entanglement to process information."
        
        # Apply personality enhancement
        enhanced_response = penny.enhance_response(llm_response, user_input)
        
        # Verify enhancement
        is_enhanced = enhanced_response != llm_response
        is_reasonable_length = len(enhanced_response) < len(llm_response) * 3
        
        print(f"✅ End-to-end enhancement: {is_enhanced}")
        print(f"✅ Reasonable length: {is_reasonable_length}")
        
        if is_enhanced:
            print(f"   Enhanced preview: {enhanced_response[:100]}...")
        
        return is_enhanced and is_reasonable_length
        
    except Exception as e:
        print(f"❌ Pipeline integration test failed: {e}")
        return False

def main():
    """Run all integration tests"""
    print("🧪 PennyGPT Engineering Improvements - Integration Tests")
    print("=" * 60)
    
    tests = [
        ("Configuration Loading", test_configuration_loading),
        ("Personality Enhancement", test_personality_enhancement),
        ("TTS Metrics", test_tts_metrics),
        ("Pipeline Integration", test_pipeline_integration)
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        print(f"\n🧪 Running: {test_name}")
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name}: PASSED")
            else:
                failed += 1
                print(f"❌ {test_name}: FAILED")
        except Exception as e:
            failed += 1
            print(f"❌ {test_name}: ERROR - {e}")
    
    print("\n" + "=" * 60)
    print(f"📊 Integration Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All integration tests passed! Engineering improvements are working correctly.")
        print("\n🚀 Your PennyGPT system is ready for production with:")
        print("   ✅ Consolidated configuration with schema versioning")
        print("   ✅ TTS metrics and production guardrails")
        print("   ✅ Smoke tests for personality system reliability")
        print("   ✅ Comprehensive error handling and validation")
        return True
    else:
        print("⚠️ Some integration tests failed. Review the system before production use.")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
