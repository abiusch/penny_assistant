#!/usr/bin/env python3
"""
TTS Factory - Automatically chooses the right TTS adapter based on configuration
"""

import os
from typing import Dict, Any, Optional

def create_tts_adapter(config: Dict[str, Any]):
    """
    Create the appropriate TTS adapter based on configuration
    
    Args:
        config: Full penny configuration dictionary
        
    Returns:
        TTS adapter instance (GoogleTTS or ElevenLabsTTS)
    """
    tts_config = config.get('tts', {})
    tts_type = tts_config.get('type', 'google').lower()
    
    print(f"[TTS Factory] Creating TTS adapter: {tts_type}")
    
    if tts_type == 'elevenlabs':
        # Check if API key is available
        api_key = os.getenv("ELEVENLABS_API_KEY")
        if not api_key:
            print("[TTS Factory] ⚠️  ELEVENLABS_API_KEY not found, falling back to Google TTS")
            tts_type = 'google'
        else:
            try:
                from adapters.tts.elevenlabs_tts_adapter import ElevenLabsTTS
                print("[TTS Factory] ✅ Using ElevenLabs TTS with personality awareness")
                return ElevenLabsTTS(config)
            except ImportError as e:
                print(f"[TTS Factory] ⚠️  ElevenLabs import failed: {e}, falling back to Google TTS")
                tts_type = 'google'
            except Exception as e:
                print(f"[TTS Factory] ⚠️  ElevenLabs setup failed: {e}, falling back to Google TTS")
                tts_type = 'google'
    
    # Default to Google TTS
    if tts_type == 'google' or tts_type not in ['elevenlabs']:
        try:
            from adapters.tts.google_tts_adapter import GoogleTTS
            print("[TTS Factory] ✅ Using Google TTS")
            return GoogleTTS(config)
        except ImportError as e:
            print(f"[TTS Factory] ❌ Google TTS import failed: {e}")
            raise
        except Exception as e:
            print(f"[TTS Factory] ❌ Google TTS setup failed: {e}")
            raise
    
    raise ValueError(f"Unknown TTS type: {tts_type}")


def get_tts_info(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Get information about the TTS configuration without creating the adapter
    
    Returns:
        Dictionary with TTS configuration info
    """
    tts_config = config.get('tts', {})
    tts_type = tts_config.get('type', 'google').lower()
    
    info = {
        'configured_type': tts_type,
        'available_types': [],
        'will_use': None,
        'personality_aware': False
    }
    
    # Check ElevenLabs availability
    if os.getenv("ELEVENLABS_API_KEY"):
        try:
            import requests
            info['available_types'].append('elevenlabs')
        except ImportError:
            pass
    
    # Google TTS is usually available
    try:
        import gtts
        info['available_types'].append('google')
    except ImportError:
        pass
    
    # Determine what will actually be used
    if tts_type == 'elevenlabs' and 'elevenlabs' in info['available_types']:
        info['will_use'] = 'elevenlabs'
        info['personality_aware'] = tts_config.get('elevenlabs', {}).get('personality_aware', False)
    elif 'google' in info['available_types']:
        info['will_use'] = 'google'
    else:
        info['will_use'] = 'none'
    
    return info
