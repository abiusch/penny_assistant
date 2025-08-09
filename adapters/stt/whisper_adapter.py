class STTWhisper:
    def __init__(self, cfg: dict):
        self.cfg = cfg or {}
        self._available = True
    def transcribe(self, audio_bytes: bytes) -> str:
        return ""
