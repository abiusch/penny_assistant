#!/usr/bin/env python3
"""
Minimal Penny Personality Layer
Simple personality system with tone presets and safety guardrails.

Features:
- 3 tone presets: friendly, dry, concise
- "Penny sass" mode with warmth guardrails  
- Safety fallbacks for sensitive topics
- Config-driven enable/disable
"""

import json
import os
import random
import re
from dataclasses import dataclass
from types import SimpleNamespace
from typing import Any, Dict, List, Optional, Union


# Tone presets
TONE_PRESETS = {
    "friendly": {
        "warmth": 0.8,
        "formality": 0.3,
        "sass": 0.2,
        "prefixes": ["Hey!", "Hi there!", "Oh, ", "Sure thing! "],
        "style": "warm and encouraging"
    },
    "dry": {
        "warmth": 0.2,
        "formality": 0.7,
        "sass": 0.1,
        "prefixes": ["", "Right. ", "Understood. ", "Noted. "],
        "style": "matter-of-fact and concise"
    },
    "concise": {
        "warmth": 0.4,
        "formality": 0.6,
        "sass": 0.0,
        "prefixes": ["", "Got it. ", ""],
        "style": "brief and to the point"
    },
    "penny": {
        "warmth": 0.7,
        "formality": 0.2,
        "sass": 0.6,
        "prefixes": ["Oh honey, ", "Sweetie, ", "Okay, ", "Well, "],
        "style": "warm but sassy"
    }
}

# Sensitive topics that should avoid sass
SENSITIVE_TOPICS = [
    "sad", "death", "grief", "depression", "depressed", "anxiety", "suicide", "crisis",
    "emergency", "medical", "health", "illness", "pain", "hurt", "worried",
    "scared", "afraid", "help", "urgent", "serious", "problem"
]

# Penny sass phrases (warm but playful)
PENNY_SASS = [
    "Oh, {text}",
    "Sweetie, {text}",
    "Well, {text}",
    "Honey, {text}",
    "Right... {text}",
    "Sure thing! {text}"
]


def _load_config() -> Dict:
    """Load personality configuration from penny_config.json"""
    # Try to find config file from various locations
    config_paths = [
        "penny_config.json",
        "../penny_config.json", 
        "../../penny_config.json",
        os.path.join(os.path.dirname(__file__), "..", "..", "penny_config.json")
    ]
    
    for path in config_paths:
        if os.path.exists(path):
            try:
                with open(path, 'r') as f:
                    return json.load(f)
            except Exception:
                continue
    
    return {}


def _detect_sensitive_content(text: str) -> bool:
    """Detect if text contains sensitive topics that should avoid sass."""
    text_lower = text.lower()
    return any(topic in text_lower for topic in SENSITIVE_TOPICS)


def _apply_tone_preset(text: str, preset_name: str) -> str:
    """Apply a tone preset to the text."""
    if preset_name not in TONE_PRESETS:
        return text
    
    preset = TONE_PRESETS[preset_name]
    
    # Don't add sass to sensitive content
    if _detect_sensitive_content(text) and preset_name == "penny":
        # Fall back to friendly for sensitive topics
        preset = TONE_PRESETS["friendly"]
    
    # Add prefix based on tone
    if preset["prefixes"] and random.random() < 0.4:  # 40% chance of prefix
        prefix = random.choice([p for p in preset["prefixes"] if p])
        if prefix and not text.startswith(prefix.strip()):
            return f"{prefix}{text}"
    
    # Apply Penny sass if appropriate
    if preset_name == "penny" and not _detect_sensitive_content(text):
        if random.random() < preset["sass"]:
            sass_template = random.choice(PENNY_SASS)
            return sass_template.format(text=text)
    
    return text


def apply(text: str, tone: Union[str, Dict, None] = None) -> str:
    """
    Apply personality to text based on tone settings.
    
    Args:
        text: The input text to personalize
        tone: Tone preset name ("friendly", "dry", "concise", "penny") 
              or config dict with personality settings
              
    Returns:
        Personalized text with applied tone
    """
    if not text or not text.strip():
        return "Say that again?"
    
    # Load config to check if personality is enabled
    config = _load_config()
    personality_config = config.get("personality", {})
    
    # Check if personality is disabled
    if not personality_config.get("enabled", True):
        return text
    
    # Handle different tone input types
    if isinstance(tone, dict):
        # Legacy support: extract tone from personality config
        if "tone" in tone:
            tone_name = tone["tone"]
        else:
            # Default to friendly if no tone specified
            tone_name = "friendly"
    elif isinstance(tone, str):
        tone_name = tone
    else:
        # Default tone
        tone_name = personality_config.get("default_tone", "friendly")
    
    # Ensure tone is valid
    if tone_name not in TONE_PRESETS:
        tone_name = "friendly"
    
    # Apply the tone preset
    result = _apply_tone_preset(text, tone_name)
    
    return result


# Legacy compatibility - keep for existing imports
class PennyPersonalitySystem:
    """Legacy compatibility class."""
    def __init__(self, config_path=None):
        self.config = _load_config()
        self.current_mode = SimpleNamespace(value="friendly", sass_level="medium")
        self.signature_expressions: List[str] = []
    
    def apply_personality(self, text: str, context=None) -> str:
        """Legacy method - delegates to apply()"""
        result = apply(text, "friendly")
        if isinstance(context, PersonalityContext):
            # Simple heuristic: shift mode based on topics for compatibility
            topic = context.topic_category
            if topic in {"technology", "learning"}:
                self.current_mode.value = "tech"
            elif topic in {"relationships", "work_stress"}:
                self.current_mode.value = "supportive"
            else:
                self.current_mode.value = "friendly"
        return result


@dataclass
class PersonalityContext:
    """Lightweight container for personality context metadata."""

    user_emotion: str
    conversation_tone: str
    user_stress_level: float
    relationship_context: Dict[str, Any]
    topic_category: str
    user_preferences: Dict[str, Any]
    recent_interactions: List[str]


def create_personality_context(
    user_emotion: str,
    conversation_tone: str,
    user_stress_level: float,
    relationship_context: Dict[str, Any],
    topic_category: str,
    user_preferences: Dict[str, Any],
    recent_interactions: List[str],
) -> PersonalityContext:
    """Factory helper used by the integration layer to construct context."""

    return PersonalityContext(
        user_emotion=user_emotion,
        conversation_tone=conversation_tone,
        user_stress_level=user_stress_level,
        relationship_context=relationship_context,
        topic_category=topic_category,
        user_preferences=user_preferences,
        recent_interactions=recent_interactions,
    )
