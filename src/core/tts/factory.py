"""TTS Factory for creating text-to-speech instances."""

from adapters.tts.google_tts_adapter import GoogleTTS

def create_tts_engine(config):
    """Create TTS engine based on configuration."""
    tts_type = config.get('tts', {}).get('type', 'google')
    
    if tts_type == 'google':
        return GoogleTTS(config.get('tts', {}))
    else:
        raise ValueError(f"Unknown TTS type: {tts_type}")

class TTSFactory:
    """Factory for TTS engines."""
    
    @staticmethod
    def create(config):
        return create_tts_engine(config)
