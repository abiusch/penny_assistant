#!/usr/bin/env python3
"""
Sass Level Configuration System - User-Controllable Personality Intensity
Integrates with existing personality coordination to provide user control
"""

import json
import os
from enum import Enum
from typing import Dict, Any, Optional
from dataclasses import dataclass

class SassLevel(Enum):
    MINIMAL = "minimal"      # Very polite, almost formal
    LITE = "lite"           # Friendly with light humor
    MEDIUM = "medium"       # Balanced sass and helpfulness (default)
    SPICY = "spicy"         # More sarcastic and direct
    MAXIMUM = "maximum"     # Full personality, very sassy

@dataclass
class SassConfig:
    level: SassLevel
    energy_multiplier: float    # How much energy to apply
    humor_frequency: float      # How often to use humor
    sarcasm_intensity: float    # How sarcastic to be
    directness: float          # How direct/blunt to be
    enthusiasm_cap: float      # Maximum enthusiasm level
    description: str           # User-friendly description

class SassController:
    """Manages user-controllable sass levels for Penny's personality"""
    
    def __init__(self, config_path: str = "sass_config.json"):
        self.config_path = config_path
        self.sass_configs = self._load_sass_configs()
        self.current_level = SassLevel.MEDIUM  # Default
        self.load_user_preference()
    
    def _load_sass_configs(self) -> Dict[SassLevel, SassConfig]:
        """Load or create sass level configurations"""
        default_configs = {
            SassLevel.MINIMAL: SassConfig(
                level=SassLevel.MINIMAL,
                energy_multiplier=0.3,
                humor_frequency=0.1,
                sarcasm_intensity=0.0,
                directness=0.2,
                enthusiasm_cap=0.4,
                description="Very polite and professional, minimal personality"
            ),
            SassLevel.LITE: SassConfig(
                level=SassLevel.LITE,
                energy_multiplier=0.6,
                humor_frequency=0.3,
                sarcasm_intensity=0.2,
                directness=0.4,
                enthusiasm_cap=0.6,
                description="Friendly with light humor and gentle teasing"
            ),
            SassLevel.MEDIUM: SassConfig(
                level=SassLevel.MEDIUM,
                energy_multiplier=0.8,
                humor_frequency=0.5,
                sarcasm_intensity=0.4,
                directness=0.6,
                enthusiasm_cap=0.8,
                description="Balanced sass and helpfulness, naturally engaging"
            ),
            SassLevel.SPICY: SassConfig(
                level=SassLevel.SPICY,
                energy_multiplier=1.0,
                humor_frequency=0.7,
                sarcasm_intensity=0.7,
                directness=0.8,
                enthusiasm_cap=0.9,
                description="More sarcastic and direct, witty comebacks"
            ),
            SassLevel.MAXIMUM: SassConfig(
                level=SassLevel.MAXIMUM,
                energy_multiplier=1.2,
                humor_frequency=0.9,
                sarcasm_intensity=0.9,
                directness=0.9,
                enthusiasm_cap=1.0,
                description="Full personality unleashed, maximum sass and energy"
            )
        }
        
        # Save default configs if file doesn't exist
        if not os.path.exists(self.config_path):
            self.save_configs_to_file(default_configs)
        
        return default_configs
    
    def save_configs_to_file(self, configs: Dict[SassLevel, SassConfig]):
        """Save sass configurations to file"""
        try:
            config_data = {}
            for level, config in configs.items():
                config_data[level.value] = {
                    "energy_multiplier": config.energy_multiplier,
                    "humor_frequency": config.humor_frequency,
                    "sarcasm_intensity": config.sarcasm_intensity,
                    "directness": config.directness,
                    "enthusiasm_cap": config.enthusiasm_cap,
                    "description": config.description
                }
            
            with open(self.config_path, 'w') as f:
                json.dump(config_data, f, indent=2)
                
        except Exception as e:
            print(f"⚠️ Could not save sass config: {e}")
    
    def load_user_preference(self):
        """Load user's saved sass preference"""
        try:
            if os.path.exists("user_sass_preference.json"):
                with open("user_sass_preference.json", 'r') as f:
                    data = json.load(f)
                    self.current_level = SassLevel(data.get("sass_level", "medium"))
        except Exception:
            self.current_level = SassLevel.MEDIUM
    
    def save_user_preference(self):
        """Save user's current sass preference"""
        try:
            with open("user_sass_preference.json", 'w') as f:
                json.dump({"sass_level": self.current_level.value}, f)
        except Exception as e:
            print(f"⚠️ Could not save sass preference: {e}")
    
    def set_sass_level(self, level: SassLevel) -> bool:
        """Set the current sass level"""
        if level in self.sass_configs:
            self.current_level = level
            self.save_user_preference()
            return True
        return False
    
    def get_current_config(self) -> SassConfig:
        """Get current sass configuration"""
        return self.sass_configs[self.current_level]
    
    def parse_sass_command(self, user_input: str) -> Optional[SassLevel]:
        """Parse user commands to change sass level"""
        input_lower = user_input.lower()
        
        # Direct level setting
        if "set sass to" in input_lower:
            for level in SassLevel:
                if level.value in input_lower:
                    return level
        
        # Natural language commands
        if any(phrase in input_lower for phrase in ["tone it down", "be less sassy", "dial it back"]):
            # Move down one level
            levels = list(SassLevel)
            current_index = levels.index(self.current_level)
            if current_index > 0:
                return levels[current_index - 1]
        
        elif any(phrase in input_lower for phrase in ["be more sassy", "turn it up", "more attitude"]):
            # Move up one level  
            levels = list(SassLevel)
            current_index = levels.index(self.current_level)
            if current_index < len(levels) - 1:
                return levels[current_index + 1]
        
        elif any(phrase in input_lower for phrase in ["be polite", "professional mode", "formal"]):
            return SassLevel.MINIMAL
        
        elif any(phrase in input_lower for phrase in ["normal", "default", "medium sass"]):
            return SassLevel.MEDIUM
        
        elif any(phrase in input_lower for phrase in ["maximum sass", "full attitude", "unleash"]):
            return SassLevel.MAXIMUM
        
        return None
    
    def get_sass_status(self) -> str:
        """Get current sass level status for user"""
        config = self.get_current_config()
        return f"Sass level: {self.current_level.value.upper()} - {config.description}"
    
    def list_available_levels(self) -> str:
        """List all available sass levels"""
        levels = []
        for level, config in self.sass_configs.items():
            marker = "👉" if level == self.current_level else "  "
            levels.append(f"{marker} {level.value.upper()}: {config.description}")
        
        return "Available sass levels:\n" + "\n".join(levels)
    
    def apply_sass_to_response(self, response: str, context: Dict[str, Any] = None) -> str:
        """Apply current sass level to response"""
        config = self.get_current_config()
        context = context or {}
        
        # Apply sass-specific modifications based on level
        if config.level == SassLevel.MINIMAL:
            # Very polite and formal
            response = response.replace("What's on your mind?", "How may I assist you with this matter?")
            response = response.replace("can be quite the journey", "requires careful consideration")
            response = response.replace("!", ".")
            
        elif config.level == SassLevel.LITE:
            # Friendly with light humor
            response = response.replace("What's on your mind?", "What's cooking in your code today?")
            response = response.replace("can be quite the journey", "can be quite the adventure")
            
        elif config.level == SassLevel.MEDIUM:
            # Balanced - keep as is but add slight personality
            response = response.replace("What's on your mind?", "What's on your mind? I'm here to help!")
            
        elif config.level == SassLevel.SPICY:
            # More sarcastic and direct
            response = response.replace("Development can be quite the journey", "Ah, development... the endless cycle of breaking things that used to work")
            response = response.replace("What's on your mind?", "What delightful coding chaos are we dealing with today?")
            
        elif config.level == SassLevel.MAXIMUM:
            # Full sass unleashed
            response = response.replace("Development can be quite the journey", "Oh boy, another programming adventure! Let me guess - something that worked yesterday is mysteriously broken today?")
            response = response.replace("What's on your mind?", "Spill the tea - what's driving you crazy in your code right now?")
        if config.energy_multiplier < 0.5:
            # Low energy - tone down exclamations
            response = response.replace("!", ".")
            response = response.replace("Oh wow", "That's interesting")
            response = response.replace("Amazing", "Good")
        
        elif config.energy_multiplier > 1.0:
            # High energy - boost enthusiasm
            response = response.replace("That's good", "That's amazing!")
            response = response.replace("Interesting", "Oh wow, that's fascinating")
        
        # Apply enthusiasm cap
        if config.enthusiasm_cap < 0.7:
            # Cap excessive enthusiasm
            response = response.replace("!!!", "!")
            response = response.replace("OH BOY", "Oh")
            response = response.replace("AMAZING", "good")
        
        # Apply sarcasm intensity
        if config.sarcasm_intensity < 0.3:
            # Reduce sarcasm
            response = response.replace("Well, well, well", "Well")
            response = response.replace("Oh really?", "I see")
        
        elif config.sarcasm_intensity > 0.7:
            # Increase sarcasm (but don't add if not already there)
            if "that's" in response.lower() and "interesting" in response.lower():
                response = response.replace("That's interesting", "That's... interesting")
        
        return response

def create_sass_controller() -> SassController:
    """Factory function to create sass controller"""
    return SassController()

# Example usage and testing
if __name__ == "__main__":
    print("🎭 Testing Sass Level Control System...")
    
    # Create sass controller
    sass = create_sass_controller()
    
    # Test current level
    print(f"Current: {sass.get_sass_status()}")
    
    # Test level listing
    print(f"\n{sass.list_available_levels()}")
    
    # Test command parsing
    test_commands = [
        "set sass to spicy",
        "tone it down",
        "be more sassy", 
        "professional mode",
        "maximum sass please"
    ]
    
    print(f"\nTesting command parsing:")
    for command in test_commands:
        parsed_level = sass.parse_sass_command(command)
        if parsed_level:
            print(f"'{command}' → {parsed_level.value}")
        else:
            print(f"'{command}' → no change")
    
    # Test response modification
    print(f"\nTesting response modification:")
    test_response = "Oh wow! That's amazing! This is really interesting!!!"
    
    for level in SassLevel:
        sass.set_sass_level(level)
        modified = sass.apply_sass_to_response(test_response)
        print(f"{level.value}: {modified}")
    
    print("✅ Sass control system test completed!")
