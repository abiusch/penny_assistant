#!/usr/bin/env python3
"""Penny Assistant with wake word and conversation memory."""

import sounddevice as sd
import time
from voice_entry import respond as voice_respond
from stt_engine import transcribe_audio
from core.llm_router import get_llm
from core.wake_word import detect_wake_word, extract_command
from core.memory import ConversationMemory
from adapters.tts.google_tts_adapter import GoogleTTS

# Set the correct microphone
sd.default.device = 1  # MacBook Pro Microphone

# Initialize components
tts = GoogleTTS({})
memory = ConversationMemory(max_exchanges=5)
llm = get_llm()

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
    
    # Check for memory commands without wake word
    if text and "clear memory" in text.lower():
        memory.clear()
        print("🧹 Memory cleared")
        speak_response("Memory cleared")
        return None
    
    return None

def speak_response(text):
    """Speak response with state management."""
    global is_speaking
    is_speaking = True
    tts.speak(text)
    # Wait longer for speech to finish (adjust multiplier as needed)
    time.sleep(len(text) * 0.08)  # Increased from 0.05
    is_speaking = False

def process_command(command: str):
    """Process a command with memory context."""
    global is_processing
    
    if not command or is_processing:
        return
    
    is_processing = True
    print(f"🤔 Processing: {command}")
    
    try:
        # Get conversation context
        context = memory.get_context()
        
        # Add instruction for brevity
        prompt = f"{command}\n(Respond in 1-2 sentences for voice output)"
        
        # Get response with context
        def generator(system_prompt: str, user_text: str) -> str:
            del system_prompt
            if hasattr(llm, 'generate'):
                result = llm.generate(prompt, context=context)
            else:
                if context:
                    full_prompt = f"Previous conversation:\n{context}\n\nUser: {prompt}"
                    result = llm.complete(full_prompt)
                else:
                    result = llm.complete(prompt)
            return result

        response = voice_respond(command, generator=generator)

        # Truncate if too long
        sentences = response.split('. ')
        if len(sentences) > 2:
            response = '. '.join(sentences[:2]) + '.'
        
        # Add to memory
        memory.add_exchange(command, response)
        
        print(f"🤖 Response: {response}")
        print(f"💭 Memory: {len(memory.history)} exchanges stored")
        print("🔊 Speaking...")
        
        speak_response(response)
        
    finally:
        is_processing = False

def main():
    print("💬 Penny Assistant - With Memory")
    print("Say 'Hey Penny' followed by your command")
    print("Say 'clear memory' to reset conversation history")
    print("Press Ctrl+C to exit\n")
    
    # Show initial state
    print(f"💭 Memory: {len(memory.history)} exchanges")
    print("")
    
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
        print(f"\n💭 Final memory: {len(memory.history)} exchanges")
        print("👋 Goodbye!")
        tts.stop()

if __name__ == '__main__':
    main()
