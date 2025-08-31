"""TTS Factory for creating text-to-speech instances."""

from adapters.tts.google_tts_adapter import GoogleTTS
from adapters.tts.streaming_tts_adapter import StreamingTTS

def create_tts_engine(config):
    """Create TTS engine based on configuration."""
    tts_config = config.get('tts', {})
    tts_type = tts_config.get('type', 'google')
    
    # Check if streaming mode is enabled
    if tts_config.get('streaming', True):  # Default to streaming for better latency
        return StreamingTTS(tts_config)
    elif tts_type == 'google':
        return GoogleTTS(tts_config)
    else:
        raise ValueError(f"Unknown TTS type: {tts_type}")

class TTSFactory:
    """Factory for TTS engines."""
    
    @staticmethod
    def create(config):
        return create_tts_engine(config)
