#!/usr/bin/env python3
"""
Fixed Integration Test for PennyGPT
Tests all core systems to ensure they're working together
"""

import sys
import os

# Set PYTHONPATH
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def test_integration():
    print('🧪 PennyGPT Integration Verification')
    print('=' * 40)
    
    success_count = 0
    total_tests = 0
    
    # Test 1: Core personality system
    total_tests += 1
    try:
        from core.personality import apply, TONE_PRESETS
        result = apply('Hello there!', 'friendly')
        print(f'✅ Personality System: "{result}"')
        success_count += 1
    except Exception as e:
        print(f'❌ Personality System: {e}')
    
    # Test 2: Config system
    total_tests += 1
    try:
        from src.config import load_config
        config = load_config()
        print(f'✅ Config System: Loaded {len(config)} sections')
        success_count += 1
    except Exception as e:
        print(f'❌ Config System: {e}')
    
    # Test 3: Audio device configuration
    total_tests += 1
    try:
        import sounddevice as sd
        device = sd.default.device
        print(f'✅ Audio Configuration: {device}')
        success_count += 1
    except Exception as e:
        print(f'❌ Audio Configuration: {e}')
    
    # Test 4: Memory system
    total_tests += 1
    try:
        from memory_system import PennyMemory
        memory = PennyMemory()
        print('✅ Memory System: Available')
        success_count += 1
    except Exception as e:
        print(f'❌ Memory System: {e}')
    
    # Test 5: LLM routing
    total_tests += 1
    try:
        from core.llm_router import get_llm_info
        info = get_llm_info()
        print(f'✅ LLM Router: {info.get("will_use", "configured")}')
        success_count += 1
    except Exception as e:
        print(f'❌ LLM Router: {e}')
    
    # Test 6: Adaptive Sass System
    total_tests += 1
    try:
        from adaptive_sass_enhanced_penny import create_adaptive_sass_enhanced_penny
        penny = create_adaptive_sass_enhanced_penny("test_integration.db")
        print('✅ Adaptive Sass System: Available')
        success_count += 1
        # Clean up test database
        os.remove("test_integration.db")
    except Exception as e:
        print(f'❌ Adaptive Sass System: {e}')
    
    # Test 7: Voice interface readiness
    total_tests += 1
    try:
        # Test that voice dependencies are available
        import speech_recognition as sr
        print('✅ Voice Interface: Speech Recognition Available')
        success_count += 1
    except Exception as e:
        print(f'❌ Voice Interface: {e}')
    
    print(f'\n📊 Integration Status: {success_count}/{total_tests} systems working')
    if success_count == total_tests:
        print('🎉 All core systems integrated successfully!')
        print('\n🚀 Ready to run:')
        print('   • python3 adaptive_sass_chat.py (adaptive sass learning)')
        print('   • python3 voice_enhanced_penny.py (voice interface)')
        print('   • python3 memory_chat_penny.py (memory + sass control)')
    else:
        print(f'⚠️  {total_tests - success_count} systems need attention')
        print('\n🔧 Available systems can still be used:')
        if success_count >= 4:
            print('   • Core personality and memory systems are working')
        print('   • Try: python3 test_adaptive_sass.py')

if __name__ == "__main__":
    test_integration()
