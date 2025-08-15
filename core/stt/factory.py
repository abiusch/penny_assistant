"""STT Factory for creating speech-to-text instances."""

from adapters.stt.whisper_adapter import STTWhisper

def create_stt_engine(config):
    """Create STT engine based on configuration."""
    stt_type = config.get('stt', {}).get('type', 'whisper')
    
    if stt_type == 'whisper':
        return STTWhisper()
    else:
        raise ValueError(f"Unknown STT type: {stt_type}")

class STTFactory:
    """Factory for STT engines."""
    
    @staticmethod
    def create(config):
        return create_stt_engine(config)
