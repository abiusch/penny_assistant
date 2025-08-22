#!/usr/bin/env python3
"""Penny Assistant with improved wake word detection."""

import sounddevice as sd
import time
import threading
from stt_engine import transcribe_audio
from core.llm_router import get_llm
from core.wake_word import detect_wake_word, extract_command
from adapters.tts.google_tts_adapter import GoogleTTS

# Set the correct microphone
sd.default.device = 1  # MacBook Pro Microphone

# Initialize TTS
tts = GoogleTTS({})

# State management
is_speaking = False
is_processing = False

def set_speaking(state):
    global is_speaking
    is_speaking = state

def listen_once(duration=3):
    """Record and transcribe audio once."""
    audio_data = sd.rec(int(duration * 16000), samplerate=16000, channels=1)
    sd.wait()
    return transcribe_audio(audio_data)

def listen_for_wake_word():
    """Listen for wake word with better handling."""
    global is_processing, is_speaking
    
    print("💤 Listening for 'Hey Penny'...")
    
    # Record audio
    text = listen_once(3)
    
    # Skip if we're currently speaking (avoid self-triggering)
    if is_speaking:
        return None
    
    if text and detect_wake_word(text):
        # Stop any ongoing speech immediately
        tts.stop()
        is_speaking = False
        
        print(f"👂 Wake word detected!")
        
        # Extract command if it's in the same utterance
        command = extract_command(text)
        
        if command and len(command) > 2:  # Ignore single punctuation
            print(f"📝 Command: {command}")
            return command
        else:
            # Give visual feedback and wait for command
            print("🎤 Yes? Listening...")
            
            # Wait a moment for user to start speaking
            time.sleep(0.5)
            
            # Listen for longer for the actual command
            command = listen_once(5)
            
            if command and len(command.strip()) > 2:
                print(f"📝 Command: {command}")
                return command
            else:
                print("🤷 Didn't catch that")
                return None
    
    return None

def speak_response(text):
    """Speak response with state management."""
    global is_speaking
    is_speaking = True
    tts.speak(text)
    # Add delay for speech to finish (rough estimate)
    time.sleep(len(text) * 0.05)  # Adjust timing as needed
    is_speaking = False

def process_command(command: str):
    """Process a command and speak response."""
    global is_processing
    
    if not command or is_processing:
        return
    
    is_processing = True
    print(f"🤔 Processing: {command}")
    
    try:
        # Get LLM response with shorter prompt
        llm = get_llm()
        
        # Add instruction for brevity
        prompt = f"{command}\n(Respond in 1-2 sentences for voice output)"
        response = llm.generate(prompt) if hasattr(llm, 'generate') else llm.complete(prompt)
        
        # Truncate if too long
        sentences = response.split('. ')
        if len(sentences) > 2:
            response = '. '.join(sentences[:2]) + '.'
        
        print(f"🤖 Response: {response}")
        print("🔊 Speaking...")
        
        speak_response(response)
        
    finally:
        is_processing = False

def main():
    print("💬 Penny Assistant - Wake Word Mode")
    print("Say 'Hey Penny' followed by your command")
    print("Or say 'Hey Penny', wait for the chime, then speak")
    print("Press Ctrl+C to exit\n")
    
    try:
        while True:
            # Skip listening while speaking
            if is_speaking:
                time.sleep(0.5)
                continue
            
            # Listen for wake word
            command = listen_for_wake_word()
            
            # Process if we got a command
            if command:
                process_command(command)
            
            # Brief pause before listening again
            time.sleep(0.2)
            
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
        tts.stop()

if __name__ == '__main__':
    main()
