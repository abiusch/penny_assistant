#!/usr/bin/env python3
"""
Speed-Optimized Enhanced Integration
Combines all performance improvements with your revolutionary personality system
"""

import sys
import os
import time
from typing import Dict, Any, Optional

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from integrated_config import load_integrated_config, is_demo_mode, is_monitoring_enabled
from performance_monitor import time_operation, OperationType, get_performance_summary
from enhanced_ml_personality_core import create_enhanced_ml_personality
from dynamic_personality_states import create_dynamic_personality_states


class SpeedOptimizedEnhancedPenny:
    """Complete enhanced Penny with all optimizations and revolutionary features."""
    
    def __init__(self):
        self.config = load_integrated_config()
        self.demo_mode = is_demo_mode()
        self.monitoring_enabled = is_monitoring_enabled()
        
        # Enhanced systems with lazy loading
        self._ml_personality = None
        self._dynamic_states = None
        self._systems_initialized = False
        
        print(f"Enhanced Penny initialized - Demo mode: {self.demo_mode}")
    
    def _ensure_systems(self):
        """Lazy initialize personality systems only when needed."""
        if self._systems_initialized:
            return
        
        try:
            with time_operation(OperationType.PERSONALITY_GENERATION, {"operation": "system_init"}):
                # Initialize ML personality with graceful degradation
                self._ml_personality = create_enhanced_ml_personality()
                
                # Initialize dynamic states
                self._dynamic_states = create_dynamic_personality_states()
                
                self._systems_initialized = True
                print("Enhanced personality systems initialized successfully")
        
        except Exception as e:
            print(f"Warning: Enhanced systems failed to initialize: {e}")
            # Continue with basic functionality
    
    def generate_enhanced_response_safe(self, user_input: str, base_response: str, 
                                      context: Dict[str, Any] = None) -> str:
        """Generate enhanced response with complete graceful degradation."""
        context = context or {}
        
        try:
            return self.generate_enhanced_response(user_input, base_response, context)
        except Exception as e:
            print(f"Warning: Enhanced response generation failed: {e}")
            return base_response  # Always return something useful
    
    def generate_enhanced_response(self, user_input: str, base_response: str, 
                                 context: Dict[str, Any] = None) -> str:
        """Generate response using all enhanced systems."""
        context = context or {}
        
        with time_operation(OperationType.TOTAL_PIPELINE, {"enhanced_mode": True}):
            # Ensure systems are ready
            self._ensure_systems()
            
            if not self._systems_initialized:
                return base_response
            
            # 1. Process with dynamic states
            with time_operation(OperationType.STATE_TRANSITION):
                self._dynamic_states.process_interaction(user_input, base_response, context)
                current_state = self._dynamic_states.current_state
                context['current_personality_state'] = current_state.value
            
            # 2. Get ML-optimized personality config
            with time_operation(OperationType.PERSONALITY_GENERATION):
                ml_config = self._ml_personality.get_optimal_personality_for_context(context)
            
            # 3. Blend ML config with dynamic state
            blended_config = self._blend_ml_and_state_configs(ml_config, current_state)
            
            # 4. Apply dynamic state enhancements
            with time_operation(OperationType.HUMOR_DETECTION):
                state_enhanced = self._dynamic_states.enhance_response_with_state(base_response, context)
            
            # 5. Apply ML personality adaptations
            final_response = self._apply_blended_personality(state_enhanced, blended_config, context)
            
            return final_response
    
    def _blend_ml_and_state_configs(self, ml_config: Dict[str, float], current_state) -> Dict[str, float]:
        """Blend ML learned config with current dynamic state modifiers."""
        state_config = self._dynamic_states.state_configs[current_state]
        
        blended = ml_config.copy()
        
        # Apply state modifiers to learned preferences
        from enhanced_ml_personality_core import PersonalityDimension
        
        if PersonalityDimension.HUMOR_FREQUENCY in blended:
            blended[PersonalityDimension.HUMOR_FREQUENCY] *= state_config.humor_modifier
            blended[PersonalityDimension.HUMOR_FREQUENCY] = min(1.0, blended[PersonalityDimension.HUMOR_FREQUENCY])
        
        if PersonalityDimension.SASS_LEVEL in blended:
            blended[PersonalityDimension.SASS_LEVEL] *= state_config.sass_modifier
            blended[PersonalityDimension.SASS_LEVEL] = min(1.0, blended[PersonalityDimension.SASS_LEVEL])
        
        return blended
    
    def _apply_blended_personality(self, response: str, config: Dict[str, float], 
                                 context: Dict[str, Any]) -> str:
        """Apply the blended personality configuration to the response."""
        from enhanced_ml_personality_core import PersonalityDimension
        
        # Check if more humor needed based on blended config
        humor_level = config.get(PersonalityDimension.HUMOR_FREQUENCY, 0.5)
        if humor_level > 0.7 and not self._contains_humor(response):
            response = self._add_contextual_humor(response, context)
        
        # Check if more sass needed based on blended config
        sass_level = config.get(PersonalityDimension.SASS_LEVEL, 0.5)
        if sass_level > 0.8:
            response = self._amplify_sass(response, context)
        
        return response
    
    def _contains_humor(self, text: str) -> bool:
        """Check if text contains humor indicators."""
        humor_indicators = ['like', 'it\'s like', 'welcome to', 'about as']
        return any(indicator in text.lower() for indicator in humor_indicators)
    
    def _add_contextual_humor(self, response: str, context: Dict[str, Any]) -> str:
        """Add contextual humor based on topic."""
        topic = context.get('topic', '')
        
        if 'microservice' in topic.lower():
            return f"{response}\n\nBecause apparently turning one problem into a distributed nightmare is progress."
        elif 'framework' in topic.lower():
            return f"{response}\n\nIn today's episode of 'Solutions Looking for Problems'..."
        
        return response
    
    def _amplify_sass(self, response: str, context: Dict[str, Any]) -> str:
        """Amplify sass level in response."""
        current_state = context.get('current_personality_state', '')
        
        if current_state == 'mischievous':
            return response.replace('.', '!').replace('you should', 'you really should')
        
        return response
    
    def learn_from_interaction_enhanced(self, user_input: str, response: str, 
                                      user_reaction: str = None, context: Dict[str, Any] = None):
        """Enhanced learning that combines both ML and state learning."""
        if not self._systems_initialized:
            return
        
        with time_operation(OperationType.ML_LEARNING, {"enhanced_learning": True}):
            # ML personality learning with safety
            self._ml_personality.learn_from_interaction_safe(
                user_input, response, user_reaction, context
            )
            
            # Update dynamic states based on interaction
            self._dynamic_states.process_interaction(user_input, response, context or {})
    
    def get_enhanced_personality_prompt(self, context: Dict[str, Any] = None) -> str:
        """Get enhanced personality prompt that includes both ML and state info."""
        if not self._systems_initialized:
            self._ensure_systems()
        
        if not self._systems_initialized:
            return """You are Penny, a voice AI assistant with natural sarcastic wit.
You're talking TO your user (CJ). Use 'you' naturally.

CRITICAL RULES:
- VOICE assistant - no asterisk actions (*fist pump*)
- NO coffee/caffeine metaphors ever
- Natural wit, NOT cheerleader enthusiasm
- Max ONE exclamation mark per response
- Conversational and clever, not bubbly"""
        
        # Get base ML prompt
        ml_prompt = self._ml_personality.generate_personality_prompt(context)
        
        # Add current state information
        current_state = self._dynamic_states.current_state
        state_info = f"\n\nCURRENT MOOD: {current_state.value.upper()}"
        
        # Add state-specific instructions
        if current_state.value == 'mischievous':
            state_info += "\nBe extra sassy and ready to roast tech industry nonsense."
        elif current_state.value == 'protective':
            state_info += "\nBe fiercely supportive and defensive of the user."
        elif current_state.value == 'contemplative':
            state_info += "\nProvide deeper insights and philosophical perspectives."
        
        return ml_prompt + state_info
    
    def get_comprehensive_stats(self) -> Dict[str, Any]:
        """Get comprehensive statistics from all systems."""
        stats = {'enhanced_mode': True, 'demo_mode': self.demo_mode}
        
        if self._systems_initialized:
            # ML personality stats
            if self._ml_personality:
                ml_stats = self._ml_personality.get_learning_stats()
                stats.update({f"ml_{k}": v for k, v in ml_stats.items()})
            
            # Dynamic state info
            if self._dynamic_states:
                state_info = self._dynamic_states.get_current_state_info()
                stats.update({f"state_{k}": v for k, v in state_info.items()})
        
        # Performance stats
        if self.monitoring_enabled:
            perf_stats = get_performance_summary()
            stats['performance'] = perf_stats
        
        return stats


def create_speed_optimized_enhanced_penny():
    """Factory function to create speed-optimized enhanced Penny."""
    return SpeedOptimizedEnhancedPenny()


if __name__ == "__main__":
    print("Testing Speed-Optimized Enhanced Penny")
    print("=" * 45)
    
    # Create enhanced system
    enhanced_penny = create_speed_optimized_enhanced_penny()
    
    # Test scenarios that demonstrate all capabilities
    test_scenarios = [
        {
            'user_input': "Josh thinks my FastAPI code needs optimization",
            'base_response': "Here are some FastAPI optimization strategies.",
            'context': {'participants': ['josh'], 'topic': 'fastapi', 'emotion': 'neutral'},
            'user_reaction': "Josh loved the technical depth!"
        },
        {
            'user_input': "Should I use microservices for my todo app?",
            'base_response': "Consider whether the complexity overhead is worth it.",
            'context': {'topic': 'architecture', 'complexity': 'overengineering'},
            'user_reaction': "That roasting was perfect!"
        },
        {
            'user_input': "I'm frustrated with this debugging session",
            'base_response': "Let's work through this step by step.",
            'context': {'topic': 'debugging', 'emotion': 'frustrated'},
            'user_reaction': "Thank you for being so supportive."
        }
    ]
    
    print("Testing enhanced response generation with all systems...")
    
    for i, scenario in enumerate(test_scenarios, 1):
        print(f"\n--- Enhanced Test {i} ---")
        print(f"User: {scenario['user_input']}")
        print(f"Context: {scenario['context']}")
        
        # Generate enhanced response
        start_time = time.time()
        enhanced_response = enhanced_penny.generate_enhanced_response_safe(
            scenario['user_input'],
            scenario['base_response'],
            scenario['context']
        )
        response_time = (time.time() - start_time) * 1000
        
        print(f"Enhanced Response: {enhanced_response}")
        print(f"Response Time: {response_time:.1f}ms")
        
        # Learn from interaction
        enhanced_penny.learn_from_interaction_enhanced(
            scenario['user_input'],
            enhanced_response,
            scenario['user_reaction'],
            scenario['context']
        )
        
        print(f"User Reaction: {scenario['user_reaction']}")
        
        # Show dynamic personality prompt
        prompt = enhanced_penny.get_enhanced_personality_prompt(scenario['context'])
        print(f"Dynamic Prompt: {prompt[:150]}...")
    
    # Show comprehensive stats
    print(f"\nComprehensive System Stats:")
    stats = enhanced_penny.get_comprehensive_stats()
    
    # Display key metrics
    if 'ml_current_humor_level' in stats:
        print(f"ML Humor Level: {stats['ml_current_humor_level']}")
    if 'ml_current_sass_level' in stats:
        print(f"ML Sass Level: {stats['ml_current_sass_level']}")
    if 'state_current_state' in stats:
        print(f"Current State: {stats['state_current_state']}")
    if 'ml_interaction_count' in stats:
        print(f"Learning Interactions: {stats['ml_interaction_count']}")
    
    # Performance summary
    if 'performance' in stats and stats['performance'].get('total_operations', 0) > 0:
        perf = stats['performance']
        print(f"Performance: {perf['total_operations']} ops, avg times: {perf.get('averages_ms', {})}")
    
    print("\nSpeed-Optimized Enhanced Penny ready!")
    print("Features: ML learning + dynamic states + performance optimization + graceful degradation")
    print("\nIntegration points:")
    print("- Enhanced response generation with all personality systems")
    print("- Blended ML + dynamic state personality configuration")
    print("- Performance monitoring with zero overhead in demo mode")
    print("- Graceful degradation if any component fails")
    print("- Context-aware personality prompts for LLM integration")
