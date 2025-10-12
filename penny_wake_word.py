#!/usr/bin/env python3
"""Penny Assistant with wake word detection."""

import sounddevice as sd
import time
from voice_entry import respond as voice_respond
from stt_engine import transcribe_audio
from core.llm_router import get_llm
from core.wake_word import detect_wake_word, extract_command
from adapters.tts.google_tts_adapter import GoogleTTS

# Set the correct microphone
sd.default.device = 1  # MacBook Pro Microphone

# Initialize TTS
tts = GoogleTTS({})

def listen_for_wake_word():
    """Listen for wake word in continuous mode."""
    print("💤 Listening for wake word ('Hey Penny')...")
    
    while True:
        # Record a short chunk of audio
        audio_data = sd.rec(int(3 * 16000), samplerate=16000, channels=1)
        sd.wait()
        
        # Transcribe it
        text = transcribe_audio(audio_data)
        
        if text and detect_wake_word(text):
            print(f"👂 Wake word detected! Heard: '{text}'")
            
            # Extract command if it's in the same utterance
            command = extract_command(text)
            
            if command:
                # Command was in same sentence as wake word
                print(f"📝 Command: {command}")
                return command
            else:
                # Wait for command
                print("🎤 Yes? (listening for 5 seconds)")
                audio_data = sd.rec(int(5 * 16000), samplerate=16000, channels=1)
                sd.wait()
                
                command = transcribe_audio(audio_data)
                if command:
                    print(f"📝 Command: {command}")
                    return command
                else:
                    print("🤷 Didn't catch that")
                    tts.speak("Sorry, I didn't hear anything")
                    return None

def process_command(command: str):
    """Process a command and speak response."""
    if not command:
        return
    
    print(f"🤔 Processing: {command}")
    
    # Get LLM response
    llm = get_llm()
    def generator(system_prompt: str, user_text: str) -> str:
        del system_prompt
        return llm.generate(user_text) if hasattr(llm, 'generate') else llm.complete(user_text)

    response = voice_respond(command, generator=generator)
    
    print(f"🤖 Response: {response}")
    print("🔊 Speaking...")
    tts.speak(response)

def main():
    print("💬 Starting Penny with wake word detection...")
    print("Say 'Hey Penny' or 'Penny' to activate")
    print("Press Ctrl+C to exit\n")
    
    try:
        while True:
            # Listen for wake word
            command = listen_for_wake_word()
            
            # Process if we got a command
            if command:
                process_command(command)
            
            # Brief pause before listening again
            time.sleep(0.5)
            
    except KeyboardInterrupt:
        print("\n👋 Exiting PennyGPT...")
        tts.stop()

if __name__ == '__main__':
    main()
