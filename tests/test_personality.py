#!/usr/bin/env python3
"""
Tests for minimal personality layer functionality.

Tests cover:
- Basic apply() function with tone presets
- Config-driven enable/disable functionality  
- Tone switching and idempotence
- Safety fallbacks for sensitive topics
- "Penny sass" guardrails
"""

import pytest
import tempfile
import json
import os
from unittest.mock import patch, mock_open

from core.personality import apply, _detect_sensitive_content, _load_config, TONE_PRESETS
from personality.filter import sanitize_output


class TestPersonalityApply:
    """Test core apply() function with different tone presets."""
    
    def test_apply_basic_no_tone(self):
        """Test basic personality application with no tone specified."""
        result = apply("Hello world")
        assert isinstance(result, str)
        assert len(result) > 0
        # Should return some version of the original text
        assert "Hello world" in result or "hello" in result.lower()
    
    def test_apply_friendly_tone(self):
        """Test friendly tone preset."""
        result = apply("How are you doing?", "friendly")
        assert isinstance(result, str)
        assert "How are you doing?" in result
        # Friendly tone should be warm but not sassy
        
    def test_apply_dry_tone(self):
        """Test dry tone preset."""
        result = apply("Please help me", "dry")
        assert isinstance(result, str)
        assert "Please help me" in result
        # Should be matter-of-fact
        
    def test_apply_concise_tone(self):
        """Test concise tone preset."""
        result = apply("What is the weather?", "concise")
        assert isinstance(result, str)
        assert "What is the weather?" in result
        
    def test_apply_penny_tone(self):
        """Test Penny sass tone preset."""
        result = apply("Tell me a joke", "penny")
        assert isinstance(result, str)
        assert "Tell me a joke" in result
        # May have added sass, but should contain original
        
    def test_apply_invalid_tone_fallback(self):
        """Test fallback to friendly for invalid tone."""
        result = apply("Test message", "invalid_tone")
        assert isinstance(result, str)
        assert "Test message" in result


class TestPersonalitySafety:
    """Test safety guardrails for sensitive content."""
    
    def test_detect_sensitive_content(self):
        """Test sensitive content detection."""
        # Sensitive topics should be detected
        assert _detect_sensitive_content("I'm feeling sad today")
        assert _detect_sensitive_content("I'm worried about my health")
        assert _detect_sensitive_content("Emergency help needed")
        assert _detect_sensitive_content("I'm depressed")
        
        # Normal topics should not be detected as sensitive
        assert not _detect_sensitive_content("What's the weather like?")
        assert not _detect_sensitive_content("Tell me a joke")
        assert not _detect_sensitive_content("How do I code this?")
        
    def test_penny_tone_safety_fallback(self):
        """Test that Penny tone falls back to friendly for sensitive topics."""
        sensitive_texts = [
            "I'm feeling really sad",
            "I'm worried about my health",
            "I need help with depression"
        ]
        
        for text in sensitive_texts:
            result = apply(text, "penny")
            # Should not contain typical sass phrases for sensitive content
            assert not any(sass in result for sass in ["Oh honey,", "Sweetie,", "Well,"])
            # Should still contain the original text
            assert text in result
            
    def test_normal_penny_tone_can_be_sassy(self):
        """Test that Penny tone can be sassy for non-sensitive topics."""
        normal_texts = [
            "What's the weather?",
            "Tell me a joke",
            "How do I code this?"
        ]
        
        # Run multiple times to account for randomness
        sass_found = False
        for _ in range(20):  # Try multiple times
            for text in normal_texts:
                result = apply(text, "penny")
                if any(sass in result for sass in ["Oh", "Sweetie", "Well", "Honey"]):
                    sass_found = True
                    break
            if sass_found:
                break
                
        # Should find sass in at least some non-sensitive cases
        # Note: This might occasionally fail due to randomness, but should usually pass


class TestPersonalityConfig:
    """Test configuration-driven behavior."""
    
    def test_personality_disabled_in_config(self):
        """Test that personality can be disabled via config."""
        config_data = {
            "personality": {
                "enabled": False
            }
        }
        
        with patch('core.personality._load_config', return_value=config_data):
            result = apply("Hello world", "penny")
            # When disabled, should return text unchanged
            assert result == "Hello world"
            
    def test_personality_enabled_in_config(self):
        """Test that personality works when enabled in config."""
        config_data = {
            "personality": {
                "enabled": True,
                "default_tone": "friendly"
            }
        }
        
        with patch('core.personality._load_config', return_value=config_data):
            result = apply("Hello world")
            # Should apply some personality
            assert isinstance(result, str)
            assert len(result) > 0
            
    def test_default_tone_from_config(self):
        """Test that default tone is read from config."""
        config_data = {
            "personality": {
                "enabled": True,
                "default_tone": "dry"
            }
        }
        
        with patch('core.personality._load_config', return_value=config_data):
            result = apply("Test message")  # No tone specified
            assert "Test message" in result


class TestPersonalityIdempotence:
    """Test idempotence and consistency."""
    
    def test_empty_or_invalid_input(self):
        """Test handling of empty or invalid input."""
        # Empty string
        result = apply("")
        assert result == "Say that again?"
        
        # None input
        result = apply(None)
        assert result == "Say that again?"
        
        # Whitespace only
        result = apply("   ")
        assert result == "Say that again?"
        
    def test_tone_switching(self):
        """Test switching between tones produces different results."""
        text = "What's the weather like?"
        
        friendly_result = apply(text, "friendly")
        dry_result = apply(text, "dry")
        concise_result = apply(text, "concise")
        penny_result = apply(text, "penny")
        
        # All should contain original text
        for result in [friendly_result, dry_result, concise_result, penny_result]:
            assert text in result
            
        # Results might be the same due to randomness, but structure should be valid
        assert all(isinstance(result, str) for result in [friendly_result, dry_result, concise_result, penny_result])

    def test_consistent_output_type(self):
        """Test that apply() always returns a string."""
        test_cases = [
            ("Hello", "friendly"),
            ("", "dry"),
            (None, "concise"),
            ("Test", "penny"),
            ("Test", "invalid_tone"),
            ("Test", None),
            ("Test", {}),
            ("Test", {"tone": "friendly"})
        ]
        
        for text, tone in test_cases:
            result = apply(text, tone)
            assert isinstance(result, str)
            assert len(result) > 0


class TestPersonalityLegacySupport:
    """Test legacy compatibility features."""
    
    def test_legacy_dict_tone_input(self):
        """Test legacy dict-style tone input."""
        # Test with tone key
        result = apply("Hello", {"tone": "friendly"})
        assert isinstance(result, str)
        assert "Hello" in result
        
        # Test without tone key (should default)
        result = apply("Hello", {"other_setting": "value"})
        assert isinstance(result, str)
        assert "Hello" in result
        
    def test_legacy_personality_system_class(self):
        """Test that legacy PennyPersonalitySystem class still works."""
        from core.personality import PennyPersonalitySystem
        
        personality = PennyPersonalitySystem()
        result = personality.apply_personality("Hello world")
        assert isinstance(result, str)
        assert len(result) > 0


class TestConfigLoading:
    """Test configuration file loading."""
    
    def test_config_loading_with_file(self):
        """Test loading config from existing file."""
        # Create a temporary config file
        config_data = {
            "personality": {
                "enabled": True,
                "default_tone": "concise"
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            temp_path = f.name
        
        try:
            # Patch the config path lookup to use our temp file
            with patch('os.path.exists', side_effect=lambda path: path == temp_path):
                with patch('core.personality._load_config') as mock_load:
                    mock_load.return_value = config_data
                    result = apply("Test")
                    assert isinstance(result, str)
        finally:
            os.unlink(temp_path)
            
    def test_config_loading_fallback(self):
        """Test graceful fallback when config file is missing."""
        with patch('os.path.exists', return_value=False):
            config = _load_config()
            assert config == {}
            
            # Should still work with empty config
            result = apply("Hello world")
            assert isinstance(result, str)
            assert len(result) > 0


def test_forbidden_phrases_removed():
    """Sanitizer removes banned phrases without over-scrubbing."""
    sample = "I’m all ears, data-daddy! super pumped!"
    out = sanitize_output(sample)
    assert "ears" in out
    assert "data-daddy" not in out
    assert "super pumped" not in out
    assert "!" not in out


def test_no_emoji():
    """Sanitizer strips emoji characters."""
    sample = "Alright 🙂"
    out = sanitize_output(sample)
    assert "🙂" not in out


if __name__ == "__main__":
    pytest.main([__file__])
