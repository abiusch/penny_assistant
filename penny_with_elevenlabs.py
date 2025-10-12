#!/usr/bin/env python3
"""Penny Assistant with ElevenLabs Natural Voice."""

import sounddevice as sd
import json
import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Import the unpredictable personality system
from personality.unpredictable_response import UnpredictablePenny
from voice_entry import respond as voice_respond

def main():
    print("💬 Starting PennyGPT with Natural Voice!")
    
    # Debug: Check API key first
    api_key = os.getenv("ELEVENLABS_API_KEY")
    if not api_key:
        print("❌ ELEVENLABS_API_KEY not set!")
        print("   Run: export ELEVENLABS_API_KEY='your_actual_key'")
        print("   Get your key from: https://elevenlabs.io")
        return
    else:
        print(f"🔑 API Key: {api_key[:8]}...{api_key[-4:]}")

    try:
        from stt_engine import transcribe_audio
        from core.llm_router import get_llm
        from adapters.tts.tts_factory import create_tts_adapter, get_tts_info
        print("✅ Imports successful")
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return

    # Load configuration
    try:
        with open('penny_config.json', 'r') as f:
            config = json.load(f)
        print("✅ Config loaded")
        
        # Load personality profile if specified
        if 'personality' in config and 'profile_path' in config['personality']:
            personality_path = config['personality']['profile_path']
            try:
                with open(personality_path, 'r') as f:
                    personality_config = json.load(f)
                print(f"✅ Personality profile loaded: {personality_config.get('name', 'Unknown')} v{personality_config.get('version', '1.0')}")
                
                # Validate schema version
                schema_version = personality_config.get('schema_version', '0.0.0')
                if schema_version.startswith('1.'):
                    print(f"✅ Compatible schema version: {schema_version}")
                else:
                    print(f"⚠️ Warning: Personality schema version {schema_version} may not be compatible")
                    
            except Exception as e:
                print(f"⚠️ Warning: Could not load personality profile: {e}")
                print("   Continuing with default personality settings")
                
    except Exception as e:
        print(f"❌ Config load failed: {e}")
        return

    # Set the correct microphone
    sd.default.device = [1, 2]  # Input device 1, output device 2

    # Initialize TTS with factory
    print("🎭 Initializing Penny's Voice...")
    try:
        tts_info = get_tts_info(config)
        print(f"   Voice type: {tts_info['will_use']}")
        print(f"   Personality aware: {tts_info['personality_aware']}")

        tts = create_tts_adapter(config)
        print("   ✅ Voice system ready!")
        
        # Initialize unpredictable personality system
        unpredictable_penny = UnpredictablePenny()
        print("   🎭 Personality enhancement system ready!")
        
    except Exception as e:
        print(f"   ❌ Voice system failed: {e}")
        import traceback
        traceback.print_exc()
        return

    def capture_and_handle():
        print("\n🎤 Listening for 5 seconds...")
        audio_data = sd.rec(int(5 * 16000), samplerate=16000, channels=1)
        sd.wait()

        text = transcribe_audio(audio_data)

        if not text or not isinstance(text, str) or not text.strip():
            print("🤷 Heard nothing. Try again.")
            return

        print(f"🗣️ You said: {text}")
        
        try:
            llm = get_llm()

            def generator(system_prompt: str, user_text: str) -> str:
                instruction = "Keep this brief and conversational (2-3 sentences)."
                prompt = f"{system_prompt}\n\n{instruction}\nUser: {user_text}".strip()
                original = llm.generate(prompt) if hasattr(llm, 'generate') else llm.complete(prompt)
                enhanced = unpredictable_penny.enhance_response(original, user_text)
                unpredictable_penny.log_conversation(user_text, enhanced)
                return enhanced

            enhanced_response = voice_respond(text, generator=generator)
            print(f"🤖 Penny: {enhanced_response}")
        except Exception as e:
            print(f"❌ LLM failed: {e}")
            enhanced_response = "Sorry, I'm having trouble thinking right now."
        
        # Speak the response with personality-aware voice
        # IMPORTANT: Use the USER INPUT for personality detection, not Penny's response
        print("🔊 Speaking with natural voice...")
        try:
            # Detect personality from user input, not Penny's response
            user_personality = tts._detect_personality_mode(text)
            if user_personality != 'default':
                print(f"[Penny Voice] Detected {user_personality} mode from user input")
            
            # Override TTS personality detection to use user input
            original_detect = tts._detect_personality_mode
            tts._detect_personality_mode = lambda _: user_personality
            
            success = tts.speak(enhanced_response)
            
            # Restore original function
            tts._detect_personality_mode = original_detect
            
            if success:
                # Show performance metrics after successful speech
                if hasattr(tts, 'get_metrics'):
                    metrics = tts.get_metrics()
                    print(f"📊 Performance: {metrics['cache_hits']} cache hits, {metrics['avg_synthesis_ms']}ms avg synthesis")
            else:
                print("❌ Speech failed")
        except Exception as e:
            print(f"❌ Speech error: {e}")

    print("🎭 Voice: Rachel (ElevenLabs) with Personality Awareness")
    print("🎤 Audio: MacBook Pro Microphone")
    print("Press Enter to speak, Ctrl+C to exit\n")
    
    # Test the voice on startup
    print("🔊 Testing voice...")
    try:
        success = tts.speak("Hey there! I'm Penny, and I'm excited to chat with you using my new natural voice!")
        if success:
            print("✅ Voice test successful!")
            # Show initial metrics
            if hasattr(tts, 'get_metrics'):
                metrics = tts.get_metrics()
                print(f"📊 TTS Metrics: {metrics['cache_hits']} cache hits, {metrics['avg_synthesis_ms']}ms avg synthesis")
        else:
            print("❌ Voice test failed")
    except Exception as e:
        print(f"❌ Voice test error: {e}")
    
    try:
        while True:
            input("\nPress Enter to start recording: ")
            capture_and_handle()
    except KeyboardInterrupt:
        print("\n👋 Exiting PennyGPT...")
        print("Thanks for chatting!")
        try:
            tts.stop()  # Stop any ongoing speech
        except:
            pass

if __name__ == '__main__':
    main()
