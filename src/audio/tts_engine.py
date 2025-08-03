import subprocess
import threading

def speak_text(text: str) -> None:
    def _speak():
        try:
            subprocess.run(["say", text])
        except Exception as e:
            print(f"[ERROR_MODE] TTS failure: {e}")
    threading.Thread(target=_speak, daemon=True).start()
