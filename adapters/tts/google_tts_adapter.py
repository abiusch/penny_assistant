from io import BytesIO
from gtts import gTTS

class GoogleTTS:
    def __init__(self, cfg: dict):
        self.cfg = cfg or {}
    def speak(self, text: str) -> bytes:
        if self.cfg.get("dry_run", False):
            return b""
        buf = BytesIO()
        gTTS(text=text, lang="en").write_to_fp(buf)
        return buf.getvalue()
