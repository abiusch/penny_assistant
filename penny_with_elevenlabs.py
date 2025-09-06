#!/usr/bin/env python3
"""Penny Assistant with ElevenLabs Natural Voice."""

import sounddevice as sd
import json
import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

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
    except Exception as e:
        print(f"❌ Config load failed: {e}")
        return

    # Set the correct microphone
    sd.default.device = 1  # MacBook Pro Microphone

    # Initialize TTS with factory
    print("🎭 Initializing Penny's Voice...")
    try:
        tts_info = get_tts_info(config)
        print(f"   Voice type: {tts_info['will_use']}")
        print(f"   Personality aware: {tts_info['personality_aware']}")

        tts = create_tts_adapter(config)
        print("   ✅ Voice system ready!")
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
        
        # Get LLM response with instruction for brevity
        try:
            llm = get_llm()
            # Add instruction for shorter, conversational responses
            prompt = f"Please give a brief, conversational response (2-3 sentences max) to: {text}"
            response = llm.generate(prompt) if hasattr(llm, 'generate') else llm.complete(prompt)
            print(f"🤖 Penny: {response}")
        except Exception as e:
            print(f"❌ LLM failed: {e}")
            response = "Sorry, I'm having trouble thinking right now."
        
        # Speak the response with personality-aware voice
        print("🔊 Speaking with natural voice...")
        try:
            success = tts.speak(response)
            if not success:
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
