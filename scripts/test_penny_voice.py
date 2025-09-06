#!/usr/bin/env python3
"""
Test ElevenLabs integration with Penny's personality system
"""

import sys
import os
import asyncio

# Add src to path
sys.path.append('/Users/CJ/Desktop/penny_assistant/src')

from adapters.tts.elevenlabs_tts_adapter import ElevenLabsTTS

async def test_penny_voice_modes():
    """Test different personality modes with real Penny phrases"""
    
    config = {'tts': {'cache_enabled': True}}
    
    try:
        tts = ElevenLabsTTS(config)
        print("🎭 Testing Penny Voice Personality Modes")
        print("=" * 50)
        
        test_phrases = [
            ("Sassy Mode", "Oh sweetie, you really think that algorithm is optimized? That's... adorable."),
            ("Tech Enthusiast", "Wait, that neural network architecture is actually amazing! How does the backpropagation work?"),
            ("Supportive Mode", "Hey, you seem really stressed about this presentation. Want to talk through it together?"),
            ("Playful Mode", "Haha, did you seriously just spend three hours debugging a missing semicolon? That's so you!"),
            ("Default Mode", "I think that's a really interesting point about machine learning.")
        ]
        
        for mode, phrase in test_phrases:
            print(f"\n🎤 {mode}")
            print(f"Text: '{phrase}'")
            print("Playing...")
            
            success = tts.speak(phrase)
            if success:
                # Wait for audio to finish
                while tts.is_speaking():
                    await asyncio.sleep(0.1)
                print("✅ Played successfully")
            else:
                print("❌ Failed to play")
            
            input("Press Enter for next mode...")
        
        print("\n🎉 Voice personality test complete!")
        print("Notice how Rachel's voice changes slightly for each personality mode!")
        
    except ValueError as e:
        print(f"❌ Setup error: {e}")
        print("Make sure ELEVENLABS_API_KEY is set")
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_penny_voice_modes())
