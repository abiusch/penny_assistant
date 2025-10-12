"""Compatibility wrapper for the legacy unpredictable personality module."""

from __future__ import annotations

from importlib import import_module

_legacy = import_module("src.personality.unpredictable_response")

UnpredictablePenny = getattr(_legacy, "UnpredictablePenny")

__all__ = ["UnpredictablePenny"]
