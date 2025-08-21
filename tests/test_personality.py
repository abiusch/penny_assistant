"""Tests for personality functionality."""

import pytest
from core.personality import apply, _load_config


def test_apply_basic():
    """Test basic personality application."""
    result = apply("Hello world")
    assert isinstance(result, str)
    assert "Hello world" in result


def test_apply_with_settings():
    """Test personality with custom settings."""
    settings = {"sarcasm": "high", "cursing_level": 0}
    result = apply("Hello", settings)
    assert isinstance(result, str)
    assert "Oh, really?" in result


def test_apply_sarcasm_levels():
    """Test different sarcasm levels."""
    # High sarcasm
    result_high = apply("Test", {"sarcasm": "high"})
    assert "Oh, really?" in result_high

    # Medium sarcasm
    result_medium = apply("Test", {"sarcasm": "medium"})
    assert "Sure..." in result_medium

    # Low/no sarcasm
    result_low = apply("Test", {"sarcasm": "low"})
    assert "Test" in result_low


def test_apply_cursing_level():
    """Test cursing level functionality."""
    # High cursing level
    result = apply("Test", {"cursing_level": 5})
    assert "🤬" in result

    # Low cursing level
    result = apply("Test", {"cursing_level": 1})
    assert "🤬" not in result


def test_config_loading():
    """Test configuration loading."""
    config = _load_config()
    assert isinstance(config, dict)
    assert "personality" in config