"""WebRTC VAD implementation."""

from src.adapters.vad.webrtc_vad_adapter import WebRTCVAD

def create_vad_engine(config):
    """Create VAD engine based on configuration."""
    return WebRTCVAD()

class SimpleVAD:
    """Simple Voice Activity Detection interface."""
    
    def __init__(self, energy_threshold=300):
        self.energy_threshold = energy_threshold
        self.webrtc_vad = WebRTCVAD()
    
    def start(self):
        """Start VAD processing."""
        pass
    
    def feed_is_voice(self, frame_bytes: bytes) -> bool:
        """Feed audio frame and detect if it contains voice."""
        if not frame_bytes:
            return False
        return self.webrtc_vad.is_speech(frame_bytes)
