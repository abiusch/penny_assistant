import subprocess
import threading

def speak_text(text: str) -> None:
    def _speak():
        try:
            # Add rate control: -r 40 = 40 words per minute (very deliberate pace)
            # This is quite slow but should be very clear and easy to follow
            subprocess.run(["say", "-r", "40", text])
        except Exception as e:
            print(f"[ERROR_MODE] TTS failure: {e}")
    threading.Thread(target=_speak, daemon=True).start()
