"""Chat entrypoint that applies the shared Penny persona."""

from __future__ import annotations

import sys
import os
from typing import Callable, Optional

# Ensure personality module can be found
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from personality.filter import sanitize_output
from personality.prompt_templates import DRY_SARCASTIC_SYSTEM

SYSTEM_PROMPT = DRY_SARCASTIC_SYSTEM

Generator = Callable[[str, str], str]


def respond(user_text: str, *, generator: Optional[Generator] = None) -> str:
    """Generate a chat response using the shared system prompt.

    Parameters
    ----------
    user_text:
        The user's latest utterance.
    generator:
        Callable that accepts ``(system_prompt, user_text)`` and returns the
        model's raw response. A generator must be provided by the caller to
        avoid hard dependencies on a specific LLM backend.
    """
    if generator is None:
        raise ValueError("A generator callable must be supplied to respond().")

    raw_response = generator(SYSTEM_PROMPT, user_text)
    return sanitize_output(raw_response)


__all__ = ["respond", "SYSTEM_PROMPT"]
