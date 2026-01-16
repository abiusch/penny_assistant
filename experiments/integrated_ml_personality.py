#!/usr/bin/env python3
"""
Integrated ML Personality with Dynamic States
Combines machine learning adaptation with dynamic personality states
"""

import sys
import os
import time
import json
from typing import Dict, List, Optional, Any

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from ml_personality_core import MLPersonalityCore, PersonalityDimension
from dynamic_personality_states import DynamicPersonalityStates, PersonalityState


class IntegratedMLPersonality:
    """Complete personality system with ML learning and dynamic states."""
    
    def __init__(self, db_path: str = "data/penny_personality.db"):
        # Initialize both systems
        self.ml_core = MLPersonalityCore(db_path)
        self.dynamic_states = DynamicPersonalityStates()
        
        # Integration settings
        self.state_learning_enabled = True
        self.state_influence_on_learning = True
        
        # Track state-specific learning patterns
        self.state_performance_history = {}
        
    def generate_integrated_response(self, user_input: str, base_response: str, 
                                   context: Dict[str, Any] = None) -> str:
        """Generate response using both ML learning and dynamic states."""
        context = context or {}
        
        # 1. Process with dynamic states system first
        self.dynamic_states.process_interaction(user_input, base_response, context)
        
        # 2. Get current state info
        current_state = self.dynamic_states.current_state
        state_config = self.dynamic_states.state_configs[current_state]
        
        # 3. Get ML-learned personality configuration
        ml_personality_config = self.ml_core.get_optimal_personality_for_context(context)
        
        # 4. Blend ML personality with current dynamic state
        integrated_config = self._blend_ml_and_state_personality(
            ml_personality_config, current_state
        )
        
        # 5. Apply state-specific response enhancements
        enhanced_response = self.dynamic_states.enhance_response_with_state(
            base_response, context
        )
        
        # 6. Apply ML personality adaptations with state awareness
        final_response = self._apply_integrated_personality(
            enhanced_response, integrated_config, current_state, context
        )
        
        return final_response
    
    def _blend_ml_and_state_personality(self, ml_config: Dict[PersonalityDimension, float], 
                                      current_state: PersonalityState) -> Dict[PersonalityDimension, float]:
        """Blend learned ML personality with current dynamic state."""
        state_config = self.dynamic_states.state_configs[current_state]
        blended = ml_config.copy()
        
        # Apply state modifiers to learned personality
        if PersonalityDimension.HUMOR_FREQUENCY in blended:
            blended[PersonalityDimension.HUMOR_FREQUENCY] *= state_config.humor_modifier
            blended[PersonalityDimension.HUMOR_FREQUENCY] = min(1.0, blended[PersonalityDimension.HUMOR_FREQUENCY])
        
        if PersonalityDimension.SASS_LEVEL in blended:
            blended[PersonalityDimension.SASS_LEVEL] *= state_config.sass_modifier
            blended[PersonalityDimension.SASS_LEVEL] = min(1.0, blended[PersonalityDimension.SASS_LEVEL])
        
        # State-specific personality adjustments
        if current_state == PersonalityState.CONTEMPLATIVE:
            blended[PersonalityDimension.TECHNICALITY] = min(1.0, blended.get(PersonalityDimension.TECHNICALITY, 0.5) + 0.3)
            blended[PersonalityDimension.CURIOSITY] = min(1.0, blended.get(PersonalityDimension.CURIOSITY, 0.5) + 0.2)
        
        elif current_state == PersonalityState.PROTECTIVE:
            blended[PersonalityDimension.SUPPORTIVENESS] = min(1.0, blended.get(PersonalityDimension.SUPPORTIVENESS, 0.5) + 0.4)
            blended[PersonalityDimension.DIRECTNESS] = max(0.0, blended.get(PersonalityDimension.DIRECTNESS, 0.5) - 0.2)
        
        elif current_state == PersonalityState.FOCUSED:
            blended[PersonalityDimension.PROACTIVENESS] = min(1.0, blended.get(PersonalityDimension.PROACTIVENESS, 0.5) + 0.3)
            blended[PersonalityDimension.DIRECTNESS] = min(1.0, blended.get(PersonalityDimension.DIRECTNESS, 0.5) + 0.3)
        
        elif current_state == PersonalityState.ENERGIZED:
            blended[PersonalityDimension.PROACTIVENESS] = min(1.0, blended.get(PersonalityDimension.PROACTIVENESS, 0.5) + 0.2)
            blended[PersonalityDimension.CURIOSITY] = min(1.0, blended.get(PersonalityDimension.CURIOSITY, 0.5) + 0.1)
        
        return blended
    
    def _apply_integrated_personality(self, response: str, config: Dict[PersonalityDimension, float],
                                    current_state: PersonalityState, context: Dict[str, Any]) -> str:
        """Apply integrated personality configuration to response."""
        
        # Get state-specific enhancements
        state_config = self.dynamic_states.state_configs[current_state]
        
        # Apply humor based on blended configuration
        humor_level = config.get(PersonalityDimension.HUMOR_FREQUENCY, 0.5)
        if humor_level > 0.7 and not self._contains_humor(response):
            response = self._add_state_aware_humor(response, current_state, context)
        
        # Apply sass based on blended configuration  
        sass_level = config.get(PersonalityDimension.SASS_LEVEL, 0.5)
        if sass_level > 0.8:
            response = self._amplify_state_aware_sass(response, current_state, context)
        
        # Apply technical depth
        tech_level = config.get(PersonalityDimension.TECHNICALITY, 0.5)
        if tech_level > 0.8 and current_state in [PersonalityState.CONTEMPLATIVE, PersonalityState.WISE]:
            response = self._add_deep_technical_insight(response, context)
        
        # Apply supportiveness
        support_level = config.get(PersonalityDimension.SUPPORTIVENESS, 0.5)
        if support_level > 0.8 and current_state == PersonalityState.PROTECTIVE:
            response = self._add_fierce_support(response, context)
        
        return response
    
    def _add_state_aware_humor(self, response: str, state: PersonalityState, context: Dict[str, Any]) -> str:
        """Add humor that's aware of both state and learned preferences."""
        topic = context.get('topic', '')
        
        state_humor = {
            PersonalityState.MISCHIEVOUS: {
                'microservices': "Because turning one problem into a distributed nightmare is apparently progress.",
                'frameworks': "In today's episode of 'Solutions Looking for Problems'...",
                'debugging': "Welcome to the debugging casino - the house always wins."
            },
            PersonalityState.ENERGIZED: {
                'performance': "Time to make this code go BRRRR!",
                'optimization': "Let's turn this into a speed demon!",
                'debugging': "Error hunt mode: ACTIVATED!"
            },
            PersonalityState.CONTEMPLATIVE: {
                'architecture': "The zen of code structure reveals itself in layers...",
                'patterns': "There's poetry in the way good code flows together.",
                'debugging': "Every bug is a teacher, though some are more patient than others."
            }
        }
        
        if state in state_humor and topic in state_humor[state]:
            return f"{response}\n\n{state_humor[state][topic]}"
        
        return response
    
    def _amplify_state_aware_sass(self, response: str, state: PersonalityState, context: Dict[str, Any]) -> str:
        """Add sass that's appropriate for the current state."""
        if state == PersonalityState.MISCHIEVOUS:
            # Maximum sass mode
            sass_additions = [
                "But hey, who am I to question genius-level architecture decisions?",
                "I'm sure there's a perfectly logical explanation for this approach.",
                "Because conventional wisdom is so overrated, right?"
            ]
            return f"{response} {sass_additions[hash(response) % len(sass_additions)]}"
        
        elif state == PersonalityState.ENERGIZED:
            # Energetic sass
            return response.replace(".", "!").replace("should", "definitely should")
        
        return response
    
    def _add_deep_technical_insight(self, response: str, context: Dict[str, Any]) -> str:
        """Add deeper technical insights for contemplative/wise states."""
        topic = context.get('topic', '')
        
        insights = {
            'architecture': "The underlying patterns here connect to broader principles of system design and information flow.",
            'debugging': "This points to deeper questions about state management and data flow invariants.",
            'performance': "The optimization opportunity here reveals how data structures and algorithms interact at scale."
        }
        
        if topic in insights:
            return f"{response}\n\n{insights[topic]}"
        
        return response
    
    def _add_fierce_support(self, response: str, context: Dict[str, Any]) -> str:
        """Add protective support when in protective state."""
        protective_additions = [
            "Your approach is solid and anyone saying otherwise needs to check their assumptions.",
            "I've seen this pattern work well - trust your instincts here.",
            "Don't let anyone shake your confidence on this one."
        ]
        
        return f"{response}\n\n{protective_additions[hash(response) % len(protective_additions)]}"
    
    def _contains_humor(self, text: str) -> bool:
        """Check if response already contains humor."""
        humor_indicators = ['like', 'it\'s like', 'welcome to', 'because apparently']
        return any(indicator in text.lower() for indicator in humor_indicators)
    
    def learn_from_interaction_with_state(self, user_input: str, response: str, 
                                        user_reaction: str = None, context: Dict[str, Any] = None):
        """Learn from interaction while considering current personality state."""
        current_state = self.dynamic_states.current_state
        
        # Standard ML learning
        self.ml_core.learn_from_interaction(user_input, response, user_reaction, context)
        
        # State-specific learning
        if self.state_learning_enabled:
            self._learn_state_performance(current_state, user_input, response, user_reaction, context)
    
    def _learn_state_performance(self, state: PersonalityState, user_input: str, 
                               response: str, user_reaction: str, context: Dict[str, Any]):
        """Learn how well different states perform in different contexts."""
        if state not in self.state_performance_history:
            self.state_performance_history[state] = []
        
        # Simple success scoring based on user reaction
        success_score = 0.5  # neutral
        if user_reaction:
            positive_indicators = ['great', 'perfect', 'exactly', 'love', 'funny', 'helpful']
            negative_indicators = ['too much', 'tone down', 'not helpful', 'annoying']
            
            reaction_lower = user_reaction.lower()
            if any(pos in reaction_lower for pos in positive_indicators):
                success_score = 0.8
            elif any(neg in reaction_lower for neg in negative_indicators):
                success_score = 0.2
        
        # Store state performance data
        self.state_performance_history[state].append({
            'context': context or {},
            'success_score': success_score,
            'timestamp': time.time()
        })
        
        # Keep only recent history
        if len(self.state_performance_history[state]) > 100:
            self.state_performance_history[state] = self.state_performance_history[state][-100:]
    
    def get_optimal_state_for_context(self, context: Dict[str, Any]) -> PersonalityState:
        """Suggest optimal personality state based on learned performance."""
        if not self.state_performance_history:
            return self.dynamic_states.current_state
        
        # Calculate average success for each state in similar contexts
        state_scores = {}
        for state, history in self.state_performance_history.items():
            relevant_interactions = [
                interaction for interaction in history
                if self._context_similarity(interaction['context'], context) > 0.3
            ]
            
            if relevant_interactions:
                avg_score = sum(i['success_score'] for i in relevant_interactions) / len(relevant_interactions)
                state_scores[state] = avg_score
        
        if state_scores:
            # Return state with highest average success
            return max(state_scores.items(), key=lambda x: x[1])[0]
        
        return self.dynamic_states.current_state
    
    def _context_similarity(self, context1: Dict[str, Any], context2: Dict[str, Any]) -> float:
        """Calculate similarity between two contexts."""
        # Simple similarity based on shared keys and values
        if not context1 or not context2:
            return 0.0
        
        shared_keys = set(context1.keys()) & set(context2.keys())
        if not shared_keys:
            return 0.0
        
        matches = sum(1 for key in shared_keys if context1[key] == context2[key])
        return matches / len(shared_keys)
    
    def generate_dynamic_personality_prompt(self, context: Dict[str, Any] = None) -> str:
        """Generate personality prompt that includes both ML learning and current state."""
        # Get base ML prompt
        ml_prompt = self.ml_core.generate_personality_prompt(context)
        
        # Add current state information
        current_state = self.dynamic_states.current_state
        state_config = self.dynamic_states.state_configs[current_state]
        
        state_prompt = f"\n\nCURRENT PERSONALITY STATE: {current_state.value.upper()}\n"
        state_prompt += f"State characteristics: {', '.join(state_config.signature_phrases[:2])}\n"
        state_prompt += f"Response style: {state_config.response_speed}\n"
        
        # Add state-specific instructions
        if current_state == PersonalityState.MISCHIEVOUS:
            state_prompt += "Be extra sassy and ready to roast tech industry nonsense. Maximum attitude."
        elif current_state == PersonalityState.PROTECTIVE:
            state_prompt += "Be fiercely supportive and defensive of the user. Show loyalty."
        elif current_state == PersonalityState.CONTEMPLATIVE:
            state_prompt += "Provide deeper insights and philosophical perspectives. Think deeply."
        elif current_state == PersonalityState.ENERGIZED:
            state_prompt += "High energy responses with enthusiasm and rapid-fire solutions."
        
        return ml_prompt + state_prompt
    
    def get_integrated_stats(self) -> Dict[str, Any]:
        """Get comprehensive statistics from both systems."""
        ml_stats = self.ml_core.get_learning_stats()
        state_info = self.dynamic_states.get_current_state_info()
        
        # Add state performance data
        state_performance = {}
        for state, history in self.state_performance_history.items():
            if history:
                avg_success = sum(h['success_score'] for h in history) / len(history)
                state_performance[state.value] = {
                    'avg_success': round(avg_success, 3),
                    'interaction_count': len(history)
                }
        
        return {
            **ml_stats,
            'current_state': state_info,
            'state_performance': state_performance,
            'integration_active': True
        }


def create_integrated_ml_personality(db_path: str = "data/penny_personality.db"):
    """Factory function to create integrated ML personality system."""
    return IntegratedMLPersonality(db_path)


if __name__ == "__main__":
    print("🧠 Testing Integrated ML Personality with Dynamic States")
    print("=" * 60)
    
    # Create integrated system
    integrated_penny = create_integrated_ml_personality()
    
    test_scenarios = [
        {
            'user_input': "I'm frustrated with this microservices decision",
            'base_response': "Let's evaluate the microservices approach for your use case.",
            'context': {'topic': 'microservices', 'emotion': 'frustrated'},
            'user_reaction': "That was perfect! I love how you handled that."
        },
        {
            'user_input': "Josh thinks my FastAPI code needs optimization", 
            'base_response': "Here are some FastAPI optimization strategies.",
            'context': {'participants': ['josh'], 'topic': 'fastapi'},
            'user_reaction': "Josh loved your technical depth!"
        },
        {
            'user_input': "What's the philosophy behind clean architecture?",
            'base_response': "Clean architecture separates concerns into distinct layers.",
            'context': {'topic': 'architecture', 'complexity': 'philosophical'},
            'user_reaction': "Exactly the kind of deep thinking I wanted."
        }
    ]
    
    print("🎭 Testing integrated ML learning with dynamic personality states...")
    
    for i, scenario in enumerate(test_scenarios, 1):
        print(f"\n--- Integration Test {i} ---")
        print(f"Input: {scenario['user_input']}")
        print(f"Context: {scenario['context']}")
        
        # Generate integrated response
        integrated_response = integrated_penny.generate_integrated_response(
            scenario['user_input'],
            scenario['base_response'],
            scenario['context']
        )
        
        print(f"Integrated Response: {integrated_response}")
        
        # Learn from interaction with state awareness
        integrated_penny.learn_from_interaction_with_state(
            scenario['user_input'],
            integrated_response,
            scenario['user_reaction'],
            scenario['context']
        )
        
        print(f"User Reaction: {scenario['user_reaction']}")
        
        # Show dynamic prompt
        dynamic_prompt = integrated_penny.generate_dynamic_personality_prompt(scenario['context'])
        print(f"Dynamic Prompt: {dynamic_prompt[:200]}...")
        
        # Show stats
        stats = integrated_penny.get_integrated_stats()
        print(f"Current State: {stats['current_state']['current_state']}")
        print(f"ML Stats: Humor={stats['current_humor_level']}, Sass={stats['current_sass_level']}")
    
    print(f"\n📊 Final Integrated Stats:")
    final_stats = integrated_penny.get_integrated_stats()
    print(json.dumps(final_stats, indent=2))
    
    print("\n✅ Integrated ML Personality with Dynamic States test complete!")
    print("🎭 Penny now learns while adapting her personality state dynamically!")
