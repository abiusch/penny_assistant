#!/usr/bin/env python3
"""
Fixed Penny Voice Test - Synchronous version that waits for audio
"""

import sys
import os
import subprocess
import time

# Add src to path
sys.path.append('/Users/CJ/Desktop/penny_assistant/src')

from adapters.tts.elevenlabs_tts_adapter import ElevenLabsTTS

def test_penny_voice_sync():
    """Test different personality modes with proper audio waiting"""
    
    config = {'tts': {'cache_enabled': True}}
    
    try:
        tts = ElevenLabsTTS(config)
        print("🎭 Testing Penny Voice Personality Modes (FIXED)")
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
            
            # Stop any previous audio
            tts.stop()
            time.sleep(0.5)
            
            print("🔄 Synthesizing...")
            
            # Get the audio file directly instead of using background threading
            personality = tts._detect_personality_mode(phrase)
            audio_file = tts._synthesize_audio(phrase, personality)
            
            if audio_file:
                print(f"📁 Audio file: {audio_file}")
                print("🔊 Playing audio...")
                
                # Play synchronously and wait for completion
                result = subprocess.run(
                    ["afplay", audio_file], 
                    capture_output=True, 
                    text=True,
                    timeout=30
                )
                
                if result.returncode == 0:
                    print("✅ Played successfully")
                else:
                    print(f"❌ Playback failed: {result.stderr}")
            else:
                print("❌ Failed to synthesize audio")
            
            # Wait for user
            input("Press Enter for next mode...")
        
        print("\n🎉 Voice personality test complete!")
        print("You should have heard Rachel's voice change for each personality mode!")
        
    except ValueError as e:
        print(f"❌ Setup error: {e}")
        print("Make sure ELEVENLABS_API_KEY is set")
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_penny_voice_sync()
