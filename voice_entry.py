"""Voice entrypoint that applies the shared Penny persona."""

from __future__ import annotations

from typing import Callable, Optional

from personality.filter import sanitize_output
from personality.prompt_templates import DRY_SARCASTIC_SYSTEM

SYSTEM_PROMPT = DRY_SARCASTIC_SYSTEM

Generator = Callable[[str, str], str]


def respond(user_text: str, *, generator: Optional[Generator] = None) -> str:
    """Generate a voice response using the shared system prompt."""
    if generator is None:
        raise ValueError("A generator callable must be supplied to respond().")

    raw_response = generator(SYSTEM_PROMPT, user_text)
    return sanitize_output(raw_response)


__all__ = ["respond", "SYSTEM_PROMPT"]
