#!/usr/bin/env python3
"""Penny Assistant with Text-to-Speech."""

import sounddevice as sd
from voice_entry import respond as voice_respond
from stt_engine import transcribe_audio
from core.llm_router import get_llm
from core.intent_router import is_agent_mode_trigger
from adapters.tts.google_tts_adapter import GoogleTTS

# Set the correct microphone
sd.default.device = [1, 2]  # Input device 1, output device 2

# Initialize TTS
tts = GoogleTTS({})

def capture_and_handle():
    print("🎤 Listening for 5 seconds...")
    audio_data = sd.rec(int(5 * 16000), samplerate=16000, channels=1)
    sd.wait()

    text = transcribe_audio(audio_data)

    if not text or not isinstance(text, str) or not text.strip():
        print("🤷 Heard nothing. Try again.")
        return

    print(f"🗣️ You said: {text}")
    
    # Get LLM response
    llm = get_llm()

    def generator(system_prompt: str, user_text: str) -> str:
        agent_mode = is_agent_mode_trigger(user_text)
        prompt = f"{system_prompt}\n\nUser: {user_text}".strip()
        if agent_mode:
            prompt = f"{system_prompt}\n\n[AGENT_MODE REQUEST]\nUser: {user_text}".strip()
        if hasattr(llm, 'generate'):
            return llm.generate(prompt)
        return llm.complete(prompt)

    response = voice_respond(text, generator=generator)
    print(f"🤖 Response: {response}")
    
    # Speak the response
    print("🔊 Speaking...")
    tts.speak(response)

if __name__ == '__main__':
    print("💬 Starting PennyGPT with speech...")
    print("Using MacBook Pro Microphone")
    print("Press Enter to speak, Ctrl+C to exit\n")
    
    try:
        while True:
            input("Press Enter to start recording: ")
            capture_and_handle()
    except KeyboardInterrupt:
        print("\n👋 Exiting PennyGPT...")
        tts.stop()  # Stop any ongoing speech
