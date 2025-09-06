#!/usr/bin/env python3
"""
Enhanced Personality Loader for Penny
Loads detailed personality configuration from JSON schema
"""

import json
import os
from typing import Dict, Any, Optional

class PersonalityLoader:
    """Loads and applies enhanced personality configurations"""
    
    def __init__(self, config_path: str = None):
        self.config_path = config_path or "src/personality/penny_enhanced.json"
        self.personality_config = None
        
    def load_personality(self) -> Dict[str, Any]:
        """Load personality configuration from JSON file"""
        try:
            with open(self.config_path, 'r') as f:
                self.personality_config = json.load(f)
            return self.personality_config
        except FileNotFoundError:
            print(f"Personality config not found: {self.config_path}")
            return self._default_config()
        except json.JSONDecodeError as e:
            print(f"Invalid personality config JSON: {e}")
            return self._default_config()
    
    def _default_config(self) -> Dict[str, Any]:
        """Fallback configuration if file loading fails"""
        return {
            "style": {
                "sass_level": {"default": 0.4},
                "cursing": {"enabled": True, "level": "mild"}
            },
            "safety": {
                "keywords": ["stressed", "worried", "anxious"]
            }
        }
    
    def get_sass_level(self, context: str = "default") -> float:
        """Get appropriate sass level for context"""
        if not self.personality_config:
            return 0.4
            
        sass_config = self.personality_config.get("style", {}).get("sass_level", {})
        
        # Check for sensitive topics
        safety_keywords = self.personality_config.get("safety", {}).get("keywords", [])
        if any(keyword in context.lower() for keyword in safety_keywords):
            return sass_config.get("on_sensitive", 0.0)
        
        return sass_config.get("default", 0.4)
    
    def can_curse(self, context: str = "", user_cursed: bool = False) -> bool:
        """Determine if cursing is appropriate for this context"""
        if not self.personality_config:
            return False
            
        cursing_config = self.personality_config.get("style", {}).get("cursing", {})
        
        if not cursing_config.get("enabled", False):
            return False
            
        # Never curse on sensitive topics
        safety_keywords = self.personality_config.get("safety", {}).get("keywords", [])
        if any(keyword in context.lower() for keyword in safety_keywords):
            return False
            
        # Check triggers
        triggers = cursing_config.get("triggers", [])
        if user_cursed and "user_curses_first" in triggers:
            return True
            
        if "emphasis" in triggers or "frustration" in triggers:
            return True
            
        return False
    
    def get_lexicon(self, category: str) -> list:
        """Get vocabulary for specific category"""
        if not self.personality_config:
            return []
            
        return self.personality_config.get("lexicon", {}).get(category, [])
    
    def should_avoid_humor_type(self, humor_type: str) -> bool:
        """Check if specific humor type should be avoided"""
        if not self.personality_config:
            return False
            
        avoid_list = self.personality_config.get("humor", {}).get("avoid", [])
        return humor_type in avoid_list

# Usage example:
def apply_personality_to_response(response: str, user_input: str = "") -> str:
    """Apply personality configuration to modify response"""
    loader = PersonalityLoader()
    config = loader.load_personality()
    
    # Check if we should modify response based on personality
    sass_level = loader.get_sass_level(user_input)
    can_curse = loader.can_curse(user_input, "fuck" in user_input.lower())
    
    # Simple personality application (this could be much more sophisticated)
    if sass_level > 0.5 and can_curse:
        # Add some sass and mild profanity
        if "interesting" in response.lower():
            response = response.replace("interesting", "pretty damn cool")
    
    return response

if __name__ == "__main__":
    # Test the personality loader
    loader = PersonalityLoader()
    config = loader.load_personality()
    
    print("Personality loaded:")
    print(f"Default sass level: {loader.get_sass_level()}")
    print(f"Can curse (normal): {loader.can_curse()}")
    print(f"Can curse (sensitive): {loader.can_curse('I am really stressed')}")
    print(f"Sassy phrases: {loader.get_lexicon('sassy')}")
