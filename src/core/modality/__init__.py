"""
Modality Package - Unified interfaces for chat, voice, and future modalities.
"""

from .edge_modal_interface import (
    EdgeModalInterface,
    ChatModalInterface,
    VoiceModalInterface,
    create_modal_interface
)

__all__ = [
    'EdgeModalInterface',
    'ChatModalInterface',
    'VoiceModalInterface',
    'create_modal_interface'
]
