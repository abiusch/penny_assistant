"""Wake word detection for Penny Assistant."""

def detect_wake_word(text: str) -> bool:
    """
    Check if text contains the wake word.
    
    Args:
        text: Transcribed text from speech recognition
        
    Returns:
        True if wake word detected, False otherwise
    """
    if not text:
        return False
    
    text_lower = text.lower().strip()
    
    # List of wake word variations
    wake_words = [
        "hey penny",
        "penny",
        "ok penny",
        "okay penny",
        "hello penny"
    ]
    
    # Check if any wake word is in the text
    for wake_word in wake_words:
        if wake_word in text_lower:
            return True
    
    return False


def extract_command(text: str) -> str:
    """
    Extract the command after the wake word.
    
    Args:
        text: Full transcribed text
        
    Returns:
        Command text after wake word, or full text if no wake word
    """
    if not text:
        return ""
    
    text_lower = text.lower().strip()
    
    # Wake words to remove
    wake_words = [
        "hey penny",
        "okay penny", 
        "ok penny",
        "hello penny",
        "penny"  # Check this last since it's shortest
    ]
    
    # Find and remove wake word
    for wake_word in wake_words:
        if text_lower.startswith(wake_word):
            # Return the text after wake word
            command = text[len(wake_word):].strip()
            # Remove leading comma or other punctuation
            command = command.lstrip(',').strip()
            return command if command else ""
    
    # No wake word found at start, return original
    return text
