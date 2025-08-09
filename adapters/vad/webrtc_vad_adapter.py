import webrtcvad

class WebRTCVAD:
    def __init__(self, cfg: dict):
        self.cfg = cfg or {}
        level = {"low": 0, "medium": 2, "high": 3}.get(self.cfg.get("sensitivity", "medium"), 2)
        self.vad = webrtcvad.Vad(level)
    def is_speech(self, audio_bytes: bytes) -> bool:
        return bool(audio_bytes)
