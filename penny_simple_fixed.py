#!/usr/bin/env python3
"""Penny Assistant - Simple version with correct microphone."""

import sounddevice as sd
from voice_entry import respond as voice_respond
from stt_engine import transcribe_audio
from core.llm_router import get_llm

# Set the correct microphone
sd.default.device = 1  # MacBook Pro Microphone

def capture_and_handle():
    print("🎤 Listening for 5 seconds...")
    audio_data = sd.rec(int(5 * 16000), samplerate=16000, channels=1)
    sd.wait()

    text = transcribe_audio(audio_data)

    if not text or not isinstance(text, str) or not text.strip():
        print("🤷 Heard nothing. Try again.")
        return

    print(f"🗣️ You said: {text}")
    
    # Use configured LLM
    llm = get_llm()

    def generator(system_prompt: str, user_text: str) -> str:
        prompt = f"{system_prompt}\n\nUser: {user_text}".strip()
        if hasattr(llm, 'generate'):
            return llm.generate(prompt)
        return llm.complete(prompt)

    response = voice_respond(text, generator=generator)
    print(f"🤖 Response: {response}")

if __name__ == '__main__':
    print("💬 Starting PennyGPT (simple mode)...")
    print("Using MacBook Pro Microphone")
    print("Press Enter to speak, Ctrl+C to exit\n")
    
    try:
        while True:
            input("Press Enter to start recording: ")
            capture_and_handle()
    except KeyboardInterrupt:
        print("\n👋 Exiting PennyGPT...")
