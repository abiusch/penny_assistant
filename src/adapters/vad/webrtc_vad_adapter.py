import sys
import webrtcvad

# Python version compatibility check
if sys.version_info >= (3, 13):
    import warnings
    warnings.warn(
        "Python 3.13+ detected. WebRTC VAD may have compatibility issues. "
        "Consider using Python 3.11 for better stability.",
        UserWarning,
        stacklevel=2
    )

class WebRTCVAD:
    def __init__(self, cfg: dict = None):
        self.cfg = cfg or {}
        level = {"low": 0, "medium": 2, "high": 3}.get(self.cfg.get("sensitivity", "medium"), 2)
        self.vad = webrtcvad.Vad(level)

    def is_speech(self, audio_bytes: bytes) -> bool:
        if not audio_bytes or len(audio_bytes) == 0:
            return False
        # WebRTC VAD requires specific sample rates and frame sizes
        # For now, use simple heuristic - non-empty audio likely contains speech
        return len(audio_bytes) > 160  # Minimum frame size for 16kHz, 10ms
