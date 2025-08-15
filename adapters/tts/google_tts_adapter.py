import os, tempfile, subprocess

try:
    from gtts import gTTS  # type: ignore
except Exception:
    gTTS = None

class GoogleTTS:
    def __init__(self, config):
        self.config = config or {}
        self._last_file = None

    def speak(self, text, voice_id=None, ssml=None, allow_barge_in=True):
        if not gTTS:
            print("[TTS] gTTS not installed; skipping audio.")
            return
        # Minimal: synth → temp mp3 → play (macOS)
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
            gTTS(text=text, lang="en").save(f.name)
            self._last_file = f.name
        try:
            subprocess.Popen(["afplay", self._last_file])
        except Exception as e:
            print(f"[TTS] playback failed: {e}")

    def stop(self):
        os.system("killall afplay >/dev/null 2>&1 || true")
