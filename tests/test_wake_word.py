"""Tests for wake word detection functionality."""

import pytest
from src.core.wake_word import detect_wake_word, extract_command


class TestWakeWordDetection:
    """Test wake word detection functionality."""

    def test_detect_wake_word_variations(self):
        """Test detection of various wake word formats."""
        # Positive cases
        assert detect_wake_word("hey penny") is True
        assert detect_wake_word("Hey Penny") is True
        assert detect_wake_word("HEY PENNY") is True
        assert detect_wake_word("penny") is True
        assert detect_wake_word("Penny") is True
        assert detect_wake_word("ok penny") is True
        assert detect_wake_word("okay penny") is True
        assert detect_wake_word("hello penny") is True
        
        # Wake word in middle/end of sentence
        assert detect_wake_word("I said hey penny") is True
        assert detect_wake_word("Call penny please") is True
        
        # Negative cases
        assert detect_wake_word("") is False
        assert detect_wake_word(None) is False
        assert detect_wake_word("hello there") is False
        assert detect_wake_word("pen") is False
        assert detect_wake_word("penny stock") is True  # Contains "penny"
        assert detect_wake_word("spend penny") is True  # Contains "penny"

    def test_extract_command_basic(self):
        """Test basic command extraction."""
        # Commands after wake words
        assert extract_command("hey penny what time is it") == "what time is it"
        assert extract_command("penny tell me a joke") == "tell me a joke"
        assert extract_command("ok penny turn on the lights") == "turn on the lights"
        assert extract_command("okay penny, how are you") == "how are you"
        assert extract_command("hello penny good morning") == "good morning"
        
        # Wake word only
        assert extract_command("penny") == ""
        assert extract_command("hey penny") == ""
        assert extract_command("okay penny") == ""

    def test_extract_command_edge_cases(self):
        """Test edge cases for command extraction."""
        # Empty/None input
        assert extract_command("") == ""
        assert extract_command(None) == ""
        
        # No wake word - should return original
        assert extract_command("what time is it") == "what time is it"
        assert extract_command("turn on the lights") == "turn on the lights"
        
        # Wake word not at start
        assert extract_command("I said penny hello") == "I said penny hello"
        
        # Multiple wake words
        assert extract_command("hey penny penny tell me") == "penny tell me"
        
        # Punctuation handling
        assert extract_command("penny, what's the weather") == "what's the weather"
        assert extract_command("hey penny, can you help") == "can you help"

    def test_case_insensitive_processing(self):
        """Test that processing is case insensitive."""
        # Mixed case wake words
        assert detect_wake_word("Hey PENNY") is True
        assert detect_wake_word("OK Penny") is True
        assert detect_wake_word("OKAY penny") is True
        
        # Mixed case extraction
        assert extract_command("HEY PENNY what time") == "what time"
        assert extract_command("Penny Tell Me") == "Tell Me"  # Preserves original case in command
        assert extract_command("OK PENNY, HELLO") == "HELLO"

    def test_whitespace_handling(self):
        """Test proper whitespace handling."""
        # Extra whitespace
        assert detect_wake_word("  hey penny  ") is True
        assert detect_wake_word("\tpenny\n") is True
        
        # Whitespace in extraction
        assert extract_command("  hey penny  what time  ") == "what time"
        assert extract_command("penny   tell me") == "tell me"
        assert extract_command("okay penny,   hello") == "hello"

    def test_wake_word_priority(self):
        """Test that longer wake words are matched before shorter ones."""
        # "hey penny" should be matched before just "penny"
        assert extract_command("hey penny please") == "please"
        assert extract_command("okay penny thanks") == "thanks"
        
        # Ensure "penny" at start is still handled correctly
        assert extract_command("penny hey there") == "hey there"

    def test_integration_scenario(self):
        """Test realistic usage scenarios."""
        # Typical voice commands
        test_cases = [
            ("Hey Penny, what's the weather like today?", "what's the weather like today?"),
            ("Penny, set a timer for 5 minutes", "set a timer for 5 minutes"),
            ("OK Penny, remind me to call mom", "remind me to call mom"),
            ("Hello Penny, good morning!", "good morning!"),
            ("Penny", ""),  # Just wake word
            ("Hey Penny", ""),  # Just wake word with greeting
            ("what time is it", "what time is it"),  # No wake word
        ]
        
        for input_text, expected_command in test_cases:
            actual_command = extract_command(input_text)
            assert actual_command == expected_command, f"Failed for input: '{input_text}'"

    def test_wake_word_boundary_detection(self):
        """Test that wake words are detected properly at word boundaries."""
        # These should detect wake word
        assert detect_wake_word("penny hello") is True
        assert detect_wake_word("hey penny there") is True
        
        # These contain "penny" but as part of other words - still should detect
        # because current implementation uses substring matching
        assert detect_wake_word("spenny") is True  # Contains "penny"
        assert detect_wake_word("pennywhistle") is True  # Contains "penny"
        
        # This is current behavior - could be enhanced with word boundary detection
        # if false positives become an issue


class TestWakeWordConfiguration:
    """Test wake word configuration and customization."""

    def test_all_configured_wake_words(self):
        """Test all wake words defined in the configuration."""
        wake_words = [
            "hey penny",
            "penny", 
            "ok penny",
            "okay penny",
            "hello penny"
        ]
        
        for wake_word in wake_words:
            assert detect_wake_word(wake_word) is True, f"Failed to detect: {wake_word}"
            assert detect_wake_word(wake_word.upper()) is True, f"Failed to detect uppercase: {wake_word}"
            assert detect_wake_word(wake_word.title()) is True, f"Failed to detect title case: {wake_word}"


if __name__ == "__main__":
    pytest.main([__file__])
