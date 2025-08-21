import threading
import sounddevice as sd
import time
from stt_engine import transcribe_audio
from core.llm_router import get_llm
from src.audio.tts_engine import speak_text
from src.core.intent_router import is_agent_mode_trigger
from pynput import keyboard  # ✅ REPLACED `keyboard` WITH `pynput`

def capture_and_handle():
    print("🎤 Listening...")
    audio_data = sd.rec(int(5 * 16000), samplerate=16000, channels=1)
    sd.wait()

    text = transcribe_audio(audio_data)

    if not text or not isinstance(text, str) or not text.strip():
        print("🤷🏻 Heard nothing. Try again when you're actually saying something.")
        return

    print(f"🗣️ You said: {text}")
    agent_mode = is_agent_mode_trigger(text)
    llm = get_llm()
    response = llm.generate(text) if hasattr(llm, 'generate') else llm.complete(text)
    speak_text(response)

# ✅ NEW HOTKEY HANDLER USING `pynput`
def on_press(key):
    try:
        if key.char == ' ':
            capture_and_handle()
    except AttributeError:
        pass  # Ignore shift, ctrl, etc.

def hotkey_listener():
    with keyboard.Listener(on_press=on_press) as listener:
        listener.join()

if __name__ == '__main__':
    print("💬 Starting PennyGPT voice assistant...")

    listener_thread = threading.Thread(target=hotkey_listener, daemon=True)
    listener_thread.start()

    # Test: interruptible speech
    speak_text("Testing speech. Try hitting spacebar while I’m talking.")
    speak_text("Okay rude, you cut me off. I’ll remember that.")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("👋 Exiting PennyGPT...")
