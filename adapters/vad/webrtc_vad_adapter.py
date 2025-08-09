class WebRTCVAD:
    def __init__(self, cfg: dict):
        self.cfg = cfg
    def is_speech(self, audio_bytes: bytes) -> bool:
        return True
