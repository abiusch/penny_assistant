#!/usr/bin/env python3
"""
Sass-Enhanced Memory Penny - Adds user-controllable sass levels to memory system
Builds on memory_enhanced_penny.py with sass level control integration
"""

import sys
import os
from typing import Dict, Any, Optional

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from memory_enhanced_penny import MemoryEnhancedPenny
from sass_controller import create_sass_controller, SassLevel
from persistent_memory import MemoryType

class SassEnhancedPenny(MemoryEnhancedPenny):
    """Memory-enhanced Penny with user-controllable sass levels"""
    
    def __init__(self, memory_db_path: str = "penny_memory.db"):
        # Initialize parent memory system
        super().__init__(memory_db_path)
        
        # Add sass control
        print("🎭 Initializing sass control system...")
        self.sass_controller = create_sass_controller()
        
        # Store sass preference as a memory for cross-session persistence
        current_sass = self.sass_controller.get_current_config()
        self.memory.store_memory(
            MemoryType.PREFERENCE, 
            "sass_level", 
            f"Prefers {current_sass.level.value} sass level",
            confidence=1.0,
            context="User sass preference"
        )
        
        print("✅ Sass-enhanced memory system initialized!")
    
    def handle_sass_command(self, user_input: str) -> Optional[str]:
        """Handle sass level control commands"""
        # Check for sass level commands
        new_level = self.sass_controller.parse_sass_command(user_input)
        
        if new_level:
            old_level = self.sass_controller.current_level
            success = self.sass_controller.set_sass_level(new_level)
            
            if success:
                # Store the preference change in memory
                self.memory.store_memory(
                    MemoryType.PREFERENCE,
                    "sass_level",
                    f"Prefers {new_level.value} sass level",
                    confidence=1.0,
                    context=f"Changed from {old_level.value} to {new_level.value}"
                )
                
                config = self.sass_controller.get_current_config()
                return f"Sass level changed to {new_level.value.upper()}! {config.description}"
        
        # Check for sass status requests
        elif any(phrase in user_input.lower() for phrase in ["sass level", "current sass", "sass status"]):
            return self.sass_controller.get_sass_status()
        
        elif any(phrase in user_input.lower() for phrase in ["sass options", "list sass", "available sass"]):
            return self.sass_controller.list_available_levels()
        
        return None
    
    def generate_sass_aware_response(self, user_input: str, context: Dict[str, Any] = None) -> str:
        """Generate response with sass level control applied"""
        context = context or {}
        
        # First check if this is a sass command
        sass_response = self.handle_sass_command(user_input)
        if sass_response:
            return sass_response
        
        # Generate normal memory-aware response
        response = self.generate_memory_aware_response(user_input, context)
        
        # Apply current sass level
        sass_modified_response = self.sass_controller.apply_sass_to_response(response, context)
        
        return sass_modified_response
    
    def get_sass_status(self) -> str:
        """Get current sass level status"""
        return self.sass_controller.get_sass_status()
    
    def set_sass_level(self, level_name: str) -> bool:
        """Set sass level by name"""
        try:
            level = SassLevel(level_name.lower())
            return self.sass_controller.set_sass_level(level)
        except ValueError:
            return False
    
    def get_comprehensive_status(self) -> Dict[str, Any]:
        """Get comprehensive status including sass level"""
        status = {
            "memory_stats": self.memory.get_memory_stats(),
            "relationship_summary": self.get_relationship_summary(),
            "sass_level": self.sass_controller.current_level.value,
            "sass_description": self.sass_controller.get_current_config().description
        }
        return status

def create_sass_enhanced_penny(memory_db_path: str = "penny_memory.db") -> SassEnhancedPenny:
    """Factory function to create sass-enhanced Penny"""
    return SassEnhancedPenny(memory_db_path)

# Testing and example usage
if __name__ == "__main__":
    print("🎭 Testing Sass-Enhanced Memory System...")
    
    # Create sass-enhanced Penny
    penny = create_sass_enhanced_penny("test_sass_memory.db")
    
    # Test sass commands
    test_commands = [
        "What's my current sass level?",
        "Set sass to spicy",
        "What are the sass options?", 
        "Tone it down please",
        "How are you feeling today?",  # Normal conversation
        "Maximum sass please",
        "Tell me a joke"  # Should be more sassy now
    ]
    
    session_id = penny.start_conversation_session("test")
    
    for i, command in enumerate(test_commands, 1):
        print(f"\n{i}. User: {command}")
        
        try:
            response = penny.generate_sass_aware_response(command)
            print(f"   Penny: {response[:100]}...")
            print(f"   Current sass: {penny.get_sass_status()}")
        except Exception as e:
            print(f"   Error: {e}")
    
    # Show final status
    status = penny.get_comprehensive_status()
    print(f"\n📊 Final Status:")
    print(f"   Memory items: {sum(status['memory_stats'].values())}")
    print(f"   Sass level: {status['sass_level']} - {status['sass_description']}")
    
    penny.end_conversation_session("Test sass session completed")
    
    # Clean up test database
    os.remove("test_sass_memory.db")
    print("\n✅ Sass-Enhanced Memory System test completed!")
