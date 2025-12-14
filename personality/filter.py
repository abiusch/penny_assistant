"""Post-processing filters that enforce Penny's shared persona rules."""

from __future__ import annotations

import json
import pathlib
import re
from typing import Match

_CONFIG_PATH = pathlib.Path(__file__).with_name("config.json")
_CONFIG = json.loads(_CONFIG_PATH.read_text(encoding="utf-8"))

_FORBIDDEN_PHRASES = tuple(_CONFIG.get("forbidden_phrases", []))
_EMOJI_POLICY = _CONFIG.get("emoji_use", "allow")
_MAX_EXCLAMATIONS = int(_CONFIG.get("max_exclamations", 3))


def _replacement_for_phrase(phrase: str) -> str:
    tokens = phrase.split()
    if len(tokens) > 1:
        return tokens[-1]
    return ""


def _sanitize_phrase(text: str, phrase: str) -> str:
    replacement = _replacement_for_phrase(phrase)
    pattern = re.compile(re.escape(phrase), flags=re.IGNORECASE)

    def _sub(match: Match[str]) -> str:
        if not replacement:
            return ""
        value = match.group(0)
        if value.isupper():
            return replacement.upper()
        if value.islower():
            return replacement
        return replacement

    return pattern.sub(_sub, text)


def sanitize_output(text: str) -> str:
    """Apply shared persona filters to a model response."""
    sanitized = text or ""

    for phrase in _FORBIDDEN_PHRASES:
        sanitized = _sanitize_phrase(sanitized, phrase)

    if _EMOJI_POLICY == "none":
        # Remove emojis but preserve code formatting (backticks, equals, pipes, etc.)
        # Keep: letters, numbers, whitespace, punctuation, dashes (including em/en dash), and code symbols
        sanitized = re.sub(r"[^\w\s.,;:!?\'\"()\-\u2013\u2014\[\]`=|/*+<>{}#$%&@~\\^_]", "", sanitized)

    if _MAX_EXCLAMATIONS <= 0:
        sanitized = sanitized.replace("!", ".")
    elif sanitized.count("!") > _MAX_EXCLAMATIONS:
        allowed = _MAX_EXCLAMATIONS
        parts = []
        for char in sanitized:
            if char == "!":
                if allowed > 0:
                    parts.append(char)
                    allowed -= 1
                else:
                    parts.append(".")
            else:
                parts.append(char)
        sanitized = "".join(parts)

    sanitized = re.sub(r"\s{2,}", " ", sanitized)
    return sanitized.strip()


__all__ = ["sanitize_output"]
