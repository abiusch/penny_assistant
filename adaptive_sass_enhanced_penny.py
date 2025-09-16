#!/usr/bin/env python3
"""
Adaptive Sass Enhanced Penny - Combines user control with personality learning
Sass controls become training data for evolving personality preferences
"""

import sys
import os
from typing import Dict, Any, Optional

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from sass_enhanced_penny import SassEnhancedPenny
from adaptive_sass_learning import create_adaptive_sass_learning, AdaptiveSassLearning
from sass_controller import SassLevel
from persistent_memory import MemoryType

class AdaptiveSassEnhancedPenny(SassEnhancedPenny):
    """Sass-enhanced Penny with adaptive learning - sass controls train her personality"""
    
    def __init__(self, memory_db_path: str = "penny_memory.db"):
        # Initialize parent sass-enhanced system
        super().__init__(memory_db_path)
        
        # Add adaptive learning
        print("🧠 Initializing adaptive sass learning...")
        self.sass_learning = create_adaptive_sass_learning()
        
        # Track original sass level before user overrides
        self.original_sass_level = None
        self.has_active_override = False
        
        print("✅ Adaptive sass learning system initialized!")
    
    def generate_adaptive_sass_response(self, user_input: str, context: Dict[str, Any] = None) -> str:
        """Generate response using adaptive sass (learned preferences + user control)"""
        context = context or {}
        
        # First check if this is a sass command
        sass_response = self.handle_sass_command(user_input)
        if sass_response:
            return sass_response
        
        # Determine sass level using adaptive learning
        final_sass_level = self._determine_adaptive_sass_level(context)
        
        # Temporarily set sass level for this response
        original_level = self.sass_controller.current_level
        self.sass_controller.set_sass_level(final_sass_level)
        
        try:
            # Generate response with adaptive sass level
            response = super().generate_sass_aware_response(user_input, context)
            return response
        finally:
            # Restore original sass level
            self.sass_controller.set_sass_level(original_level)
    
    def handle_sass_command(self, user_input: str) -> Optional[str]:
        """Handle sass commands and record as learning events"""
        
        # Check for sass level commands
        new_level = self.sass_controller.parse_sass_command(user_input)
        
        if new_level:
            old_level = self.sass_controller.current_level
            success = self.sass_controller.set_sass_level(new_level)
            
            if success:
                # Record this as a learning event
                current_context = self._get_current_context()
                self.sass_learning.record_sass_adjustment(
                    user_input, old_level, new_level, current_context
                )
                
                # Store the preference change in memory
                self.memory.store_memory(
                    MemoryType.PREFERENCE,
                    "sass_level",
                    f"Prefers {new_level.value} sass level for {current_context.get('topic', 'general')} contexts",
                    confidence=1.0,
                    context=f"Changed from {old_level.value} to {new_level.value} via '{user_input}'"
                )
                
                # Set override flag
                self.has_active_override = True
                self.original_sass_level = old_level
                
                config = self.sass_controller.get_current_config()
                return f"Sass level changed to {new_level.value.upper()}! {config.description}\n\n🧠 I'm learning that you prefer {new_level.value} sass in this context."
        
        # Check for learning insights requests
        elif any(phrase in user_input.lower() for phrase in ["sass insights", "what have you learned", "sass patterns"]):
            return self._generate_learning_insights_response()
        
        # Check for sass status requests
        elif any(phrase in user_input.lower() for phrase in ["sass level", "current sass", "sass status"]):
            current_sass = self.sass_controller.get_sass_status()
            learned_info = self._get_learned_sass_info()
            return f"{current_sass}\n{learned_info}"
        
        elif any(phrase in user_input.lower() for phrase in ["sass options", "list sass", "available sass"]):
            return self.sass_controller.list_available_levels()
        
        return None
    
    def _determine_adaptive_sass_level(self, context: Dict[str, Any]) -> SassLevel:
        """Determine sass level using learned preferences + user override"""
        
        # If user has active override, use it
        if self.has_active_override:
            return self.sass_controller.current_level
        
        # Check for learned preference for this context
        learned_sass = self.sass_learning.get_learned_sass_for_context(context)
        if learned_sass:
            return learned_sass
        
        # Fall back to user's current preference or default
        return self.sass_controller.current_level
    
    def _get_current_context(self) -> Dict[str, Any]:
        """Get current conversation context for learning"""
        # This would ideally be passed from the conversation system
        # For now, return a basic context
        return {
            'topic': 'conversation',
            'emotion': 'neutral', 
            'participants': []
        }
    
    def _generate_learning_insights_response(self) -> str:
        """Generate response about what Penny has learned about sass preferences"""
        
        insights = self.sass_learning.get_learning_insights()
        
        if insights['total_adjustments'] == 0:
            return "I haven't learned much about your sass preferences yet! Try adjusting my sass level in different situations and I'll start to learn your patterns."
        
        response_parts = [
            f"🧠 Here's what I've learned about your sass preferences:"
        ]
        
        if insights['context_preferences']:
            response_parts.append("\n📋 Context-specific preferences:")
            for context, pref in insights['context_preferences'].items():
                confidence_desc = "very confident" if pref['confidence'] > 0.8 else "somewhat confident"
                response_parts.append(f"   • {context}: {pref['preferred_sass']} sass ({confidence_desc})")
        
        if insights['recent_trends']:
            response_parts.append("\n📈 Recent trends:")
            for trend in insights['recent_trends'][:3]:  # Top 3
                response_parts.append(f"   • {trend}")
        
        if insights['strongest_patterns']:
            response_parts.append("\n💪 Strongest patterns I've learned:")
            for pattern in insights['strongest_patterns']:
                response_parts.append(f"   • {pattern['context']}: prefer {pattern['preferred_sass']} sass")
        
        response_parts.append(f"\n📊 Total sass adjustments learned from: {insights['total_adjustments']}")
        response_parts.append("\nI use these patterns to choose my default sass level, but you can always override me!")
        
        return "\n".join(response_parts)
    
    def _get_learned_sass_info(self) -> str:
        """Get info about learned sass for current context"""
        
        current_context = self._get_current_context()
        learned_sass = self.sass_learning.get_learned_sass_for_context(current_context)
        
        if learned_sass:
            context_desc = self.sass_learning._get_context_key(current_context)
            return f"🧠 Learned preference for {context_desc}: {learned_sass.value} sass"
        else:
            return "🌱 No learned preference for this context yet"
    
    def clear_sass_override(self) -> str:
        """Clear active sass override and return to learned preferences"""
        
        if self.has_active_override:
            self.has_active_override = False
            current_context = self._get_current_context()
            learned_sass = self.sass_learning.get_learned_sass_for_context(current_context)
            
            if learned_sass:
                self.sass_controller.set_sass_level(learned_sass)
                return f"Sass override cleared! Returning to learned preference: {learned_sass.value} sass"
            else:
                self.sass_controller.set_sass_level(SassLevel.MEDIUM)
                return "Sass override cleared! Using default medium sass (no learned preference for this context)"
        else:
            return "No active sass override to clear."
    
    def get_comprehensive_adaptive_status(self) -> Dict[str, Any]:
        """Get comprehensive status including adaptive learning info"""
        
        status = super().get_comprehensive_status()
        
        # Add adaptive learning info
        learning_insights = self.sass_learning.get_learning_insights()
        status.update({
            "adaptive_learning": {
                "total_adjustments": learning_insights['total_adjustments'],
                "learned_patterns": learning_insights['learned_patterns'],
                "has_active_override": self.has_active_override,
                "context_preferences": learning_insights['context_preferences']
            }
        })
        
        return status

def create_adaptive_sass_enhanced_penny(memory_db_path: str = "penny_memory.db") -> AdaptiveSassEnhancedPenny:
    """Factory function to create adaptive sass-enhanced Penny"""
    return AdaptiveSassEnhancedPenny(memory_db_path)

# Testing and example usage
if __name__ == "__main__":
    print("🧠 Testing Adaptive Sass-Enhanced System...")
    
    # Create adaptive sass-enhanced Penny
    penny = create_adaptive_sass_enhanced_penny("test_adaptive_sass.db")
    
    # Test adaptive sass learning
    test_scenarios = [
        # Programming context - user wants minimal sass when frustrated
        ("tone it down", {'topic': 'programming', 'emotion': 'frustrated'}),
        ("How do I fix this bug?", {'topic': 'programming', 'emotion': 'frustrated'}),  # Should use minimal
        
        # Social context - user wants spicy sass with friends
        ("be more sassy", {'topic': 'conversation', 'emotion': 'neutral', 'participants': ['josh']}),
        ("What do you think about Josh?", {'topic': 'conversation', 'emotion': 'neutral', 'participants': ['josh']}),  # Should use spicy
        
        # Learning insights
        ("what have you learned about my sass preferences?", {'topic': 'conversation', 'emotion': 'curious'}),
    ]
    
    session_id = penny.start_conversation_session("adaptive_test")
    
    for i, (user_input, context) in enumerate(test_scenarios, 1):
        print(f"\n{i}. User: {user_input}")
        print(f"   Context: {context}")
        
        try:
            response = penny.generate_adaptive_sass_response(user_input, context)
            current_sass = penny.sass_controller.current_level.value
            print(f"   Penny [{current_sass}]: {response[:150]}...")
        except Exception as e:
            print(f"   Error: {e}")
    
    # Show comprehensive status
    status = penny.get_comprehensive_adaptive_status()
    print(f"\n📊 Final Adaptive Status:")
    print(f"   Current sass: {status['sass_level']}")
    print(f"   Total adjustments: {status['adaptive_learning']['total_adjustments']}")
    print(f"   Learned patterns: {status['adaptive_learning']['learned_patterns']}")
    
    penny.end_conversation_session("Adaptive test completed")
    
    # Clean up test database
    os.remove("test_adaptive_sass.db")
    print("\n✅ Adaptive sass-enhanced system test completed!")
