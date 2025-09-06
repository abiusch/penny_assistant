#!/usr/bin/env python3
"""
Test ElevenLabs integration with actual Penny pipeline
"""

import sys
import json
import os

# Add src to path
sys.path.append('/Users/CJ/Desktop/penny_assistant/src')

from adapters.tts.tts_factory import create_tts_adapter, get_tts_info

def test_penny_with_elevenlabs():
    """Test ElevenLabs with real Penny configuration"""
    
    # Load real Penny config
    config_path = '/Users/CJ/Desktop/penny_assistant/penny_config.json'
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    print("🎭 Testing Penny with ElevenLabs Integration")
    print("=" * 50)
    
    # Show TTS info
    tts_info = get_tts_info(config)
    print(f"📋 TTS Configuration:")
    print(f"   Configured type: {tts_info['configured_type']}")
    print(f"   Available types: {', '.join(tts_info['available_types'])}")
    print(f"   Will use: {tts_info['will_use']}")
    print(f"   Personality aware: {tts_info['personality_aware']}")
    print()
    
    if tts_info['will_use'] != 'elevenlabs':
        print("❌ ElevenLabs not available. Check API key and config.")
        return
    
    # Create TTS adapter
    try:
        tts = create_tts_adapter(config)
        print("✅ TTS adapter created successfully")
    except Exception as e:
        print(f"❌ Failed to create TTS adapter: {e}")
        return
    
    # Test with realistic Penny responses
    print("\n🎤 Testing Realistic Penny Responses")
    print("-" * 40)
    
    penny_responses = [
        # Sassy response
        "Oh sweetie, you're asking me about quantum mechanics? That's actually... kind of impressive!",
        
        # Tech enthusiast response  
        "Wait, that machine learning algorithm you mentioned sounds fascinating! How does the gradient descent work?",
        
        # Supportive response
        "You seem really stressed about that work project. Want to talk through what's bothering you?",
        
        # Playful response
        "Haha, did you seriously just ask me to explain recursion using recursion? That's so meta!",
        
        # Default response
        "I think that's a really interesting perspective on artificial intelligence."
    ]
    
    for i, response in enumerate(penny_responses, 1):
        print(f"\n{i}. Testing response...")
        print(f"   Penny: \"{response}\"")
        
        success = tts.speak(response)
        if success:
            print("   ✅ Spoken successfully")
        else:
            print("   ❌ Failed to speak")
        
        input("   Press Enter for next response...")
    
    print("\n🎉 Penny + ElevenLabs test complete!")
    print("Notice how Penny's voice adapts to different personality modes!")

if __name__ == "__main__":
    test_penny_with_elevenlabs()
