"""STT Factory for creating speech-to-text instances."""

from adapters.stt.whisper_adapter import WhisperSTT

def create_stt_engine(config):
    """Create STT engine based on configuration."""
    stt_config = config.get('stt', {})
    stt_type = stt_config.get('type', 'whisper')
    stt_provider = stt_config.get('provider', 'whisper_local')
    
    if stt_type == 'whisper' or stt_provider == 'whisper_local':
        return WhisperSTT(config)
    else:
        raise ValueError(f"Unknown STT type: {stt_type} or provider: {stt_provider}")

class STTFactory:
    """Factory for STT engines."""
    
    @staticmethod
    def create(config):
        return create_stt_engine(config)
    
    @staticmethod
    def from_config(config):
        return create_stt_engine(config)
