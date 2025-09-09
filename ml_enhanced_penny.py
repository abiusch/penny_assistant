#!/usr/bin/env python3
"""
ML-Enhanced Penny Integration - Complete File
Connects machine learning personality core to existing Penny systems
"""

import sys
import os
import time
import json
from typing import Dict, List, Optional, Any

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from ml_personality_core import MLPersonalityCore, PersonalityDimension


class MLEnhancedPenny:
    """Penny with machine learning personality adaptation."""
    
    def __init__(self, cj_learning_system=None, config=None):
        # Initialize ML personality core
        self.ml_personality = MLPersonalityCore()
        
        # Existing systems
        self.cj_learning = cj_learning_system
        self.config = config or {}
        
        # Conversation tracking for learning
        self.conversation_history = []
        self.last_response = ""
        self.waiting_for_feedback = False
    
    def generate_adaptive_response(self, user_input: str, base_response: str, 
                                 context: Dict[str, Any] = None) -> str:
        """Generate response that adapts based on learned personality preferences."""
        context = context or {}
        
        # Get optimal personality configuration for this context
        personality_config = self.ml_personality.get_optimal_personality_for_context(context)
        
        # Enhance the base response using learned preferences
        enhanced_response = self._apply_personality_adaptations(
            base_response, personality_config, context
        )
        
        # Store for learning
        self.last_response = enhanced_response
        self.waiting_for_feedback = True
        
        return enhanced_response
    
    def _apply_personality_adaptations(self, response: str, config: Dict[PersonalityDimension, float], 
                                     context: Dict[str, Any]) -> str:
        """Apply personality adaptations to response based on learned preferences."""
        
        # Humor injection based on learned preferences
        humor_level = config[PersonalityDimension.HUMOR_FREQUENCY]
        if humor_level > 0.6 and not self._contains_humor(response):
            response = self._inject_contextual_humor(response, context)
        
        # Sass modification based on learned preferences
        sass_level = config[PersonalityDimension.SASS_LEVEL]
        if sass_level > 0.7:
            response = self._amplify_sass(response, context)
        elif sass_level < 0.3:
            response = self._reduce_sass(response)
        
        # Technical depth adjustment
        tech_level = config[PersonalityDimension.TECHNICALITY]
        if tech_level > 0.7 and 'technical' in context.get('topic', ''):
            response = self._increase_technical_depth(response, context)
        elif tech_level < 0.3:
            response = self._simplify_technical_language(response)
        
        # Supportiveness adjustment
        support_level = config[PersonalityDimension.SUPPORTIVENESS]
        emotion = context.get('emotion', '')
        if support_level > 0.7 and emotion in ['frustrated', 'stressed', 'confused']:
            response = self._add_emotional_support(response, emotion)
        
        # Proactiveness adjustment
        proactive_level = config[PersonalityDimension.PROACTIVENESS]
        if proactive_level > 0.6:
            response = self._add_proactive_suggestions(response, context)
        
        return response
    
    def _inject_contextual_humor(self, response: str, context: Dict[str, Any]) -> str:
        """Inject humor based on context and learned preferences."""
        topic = context.get('topic', '')
        
        humor_additions = {
            'debugging': [
                "It's like playing detective, except the criminal is past-you.",
                "Welcome to debugging: where the code worked yesterday and logic goes to die.",
                "Time to play 'find the needle in the haystack' - except the haystack is also needles."
            ],
            'frameworks': [
                "Framework choice: where every decision is simultaneously right and wrong depending on who you ask.",
                "Let's pick a framework before a new one comes out in the next 10 minutes.",
                "The eternal framework question - it's like asking 'what's the best pizza topping?'"
            ],
            'architecture': [
                "Architecture decisions: where 'it depends' is always the correct answer.",
                "Designing architecture is like urban planning, but the laws of physics change weekly.",
                "Clean architecture: beautiful in theory, chaotic in practice."
            ]
        }
        
        if topic in humor_additions:
            humor = humor_additions[topic][hash(response) % len(humor_additions[topic])]
            return f"{response}\n\n{humor}"
        
        return response
    
    def _amplify_sass(self, response: str, context: Dict[str, Any]) -> str:
        """Increase sass level based on learned preferences."""
        sass_replacements = {
            'that approach': 'that questionable approach',
            'you should': 'you really should',
            'consider': 'seriously consider',
            'might want': 'definitely want',
            'could be': 'is probably'
        }
        
        for original, sassy in sass_replacements.items():
            response = response.replace(original, sassy)
        
        # Add some direct commentary
        if 'microservice' in response.lower():
            response += " But hey, who doesn't love distributed system complexity?"
        elif 'framework' in response.lower():
            response += " Because apparently we needed another way to render a div."
        
        return response
    
    def _reduce_sass(self, response: str) -> str:
        """Reduce sass level for users who prefer more straightforward communication."""
        # Remove potentially sassy words/phrases
        sass_words = ['obviously', 'clearly', 'of course', 'really?', 'seriously?']
        for word in sass_words:
            response = response.replace(word, '')
        
        # Clean up any extra spaces
        response = ' '.join(response.split())
        
        return response
    
    def _increase_technical_depth(self, response: str, context: Dict[str, Any]) -> str:
        """Add more technical detail for users who prefer deeper explanations."""
        topic = context.get('topic', '')
        
        if 'fastapi' in topic.lower():
            response += "\n\nFor optimization, consider async context managers, connection pooling, and middleware for cross-cutting concerns like logging and metrics."
        elif 'react' in topic.lower():
            response += "\n\nConsider React.memo for component optimization, useCallback for function memoization, and React Suspense for data fetching patterns."
        elif 'python' in topic.lower():
            response += "\n\nLeverage type hints for better IDE support, consider dataclasses for structured data, and use context managers for resource management."
        
        return response
    
    def _simplify_technical_language(self, response: str) -> str:
        """Simplify technical language for users who prefer accessible explanations."""
        tech_simplifications = {
            'asynchronous': 'non-blocking',
            'middleware': 'helper functions',
            'optimization': 'making it faster',
            'memoization': 'caching results',
            'polymorphism': 'using objects in flexible ways'
        }
        
        for technical, simple in tech_simplifications.items():
            response = response.replace(technical, simple)
        
        return response
    
    def _add_emotional_support(self, response: str, emotion: str) -> str:
        """Add emotional support for frustrated/stressed users."""
        support_prefixes = {
            'frustrated': "I get it, debugging can be really frustrating. ",
            'stressed': "No worries, let's take this step by step. ",
            'confused': "That's totally understandable - this can be confusing. "
        }
        
        if emotion in support_prefixes:
            response = support_prefixes[emotion] + response
        
        return response
    
    def _add_proactive_suggestions(self, response: str, context: Dict[str, Any]) -> str:
        """Add proactive suggestions for users who appreciate them."""
        topic = context.get('topic', '')
        
        proactive_additions = {
            'debugging': "\n\nWhile we're at it, want me to suggest some debugging tools that might help prevent this in the future?",
            'frameworks': "\n\nI could also walk you through the pros and cons of the top alternatives if that would help your decision.",
            'performance': "\n\nShould I also look into performance monitoring tools that could help you catch issues early?"
        }
        
        for key, addition in proactive_additions.items():
            if key in topic.lower():
                response += addition
                break
        
        return response
    
    def _contains_humor(self, text: str) -> bool:
        """Check if text already contains humor."""
        humor_indicators = [
            'like', 'it\'s like', 'reminds me of', 'about as',
            'welcome to', 'the beauty of', 'nothing says'
        ]
        return any(indicator in text.lower() for indicator in humor_indicators)
    
    def process_user_feedback(self, user_input: str, context: Dict[str, Any] = None):
        """Process user feedback to learn personality preferences."""
        if not self.waiting_for_feedback:
            return
        
        # Learn from the interaction
        self.ml_personality.learn_from_interaction(
            user_input=self.conversation_history[-1] if self.conversation_history else "",
            response_given=self.last_response,
            user_reaction=user_input,
            context=context
        )
        
        self.waiting_for_feedback = False
    
    def get_personality_prompt_for_llm(self, context: Dict[str, Any] = None) -> str:
        """Get dynamic personality prompt based on learned preferences."""
        return self.ml_personality.generate_personality_prompt(context)
    
    def get_learning_statistics(self) -> Dict[str, Any]:
        """Get comprehensive learning statistics."""
        ml_stats = self.ml_personality.get_learning_stats()
        
        # Add additional stats
        ml_stats.update({
            'conversation_turns': len(self.conversation_history),
            'last_update': self.ml_personality.current_personality.last_updated
        })
        
        return ml_stats


def create_ml_enhanced_penny(cj_learning_system=None, config=None):
    """Factory function to create ML-enhanced Penny."""
    return MLEnhancedPenny(cj_learning_system, config)


if __name__ == "__main__":
    print("🤖 Testing ML-Enhanced Penny Integration")
    print("=" * 50)
    
    # Create ML-enhanced Penny
    ml_penny = create_ml_enhanced_penny()
    
    test_scenarios = [
        {
            'user_input': "I'm debugging this frustrating code issue",
            'base_response': "Let's look at the error and trace through the logic.",
            'context': {'topic': 'debugging', 'emotion': 'frustrated'}
        },
        {
            'user_input': "Which React framework should I use?",
            'base_response': "React is a solid choice for most projects.",
            'context': {'topic': 'frameworks', 'participants': ['josh']}
        },
        {
            'user_input': "Can you explain FastAPI optimization?",
            'base_response': "FastAPI optimization focuses on async patterns and middleware.",
            'context': {'topic': 'fastapi', 'technical': True}
        }
    ]
    
    print("🎭 Testing adaptive responses...")
    for i, scenario in enumerate(test_scenarios, 1):
        print(f"\n--- Test {i} ---")
        print(f"📝 Input: '{scenario['user_input']}'")
        print(f"🤖 Base: '{scenario['base_response']}'")
        
        # Generate adaptive response
        adaptive_response = ml_penny.generate_adaptive_response(
            scenario['user_input'],
            scenario['base_response'],
            scenario['context']
        )
        
        print(f"🎯 Adaptive: '{adaptive_response}'")
        print(f"📊 Learning Stats: {ml_penny.get_learning_statistics()}")
        
        # Simulate user feedback
        feedback = "That was perfect!" if i % 2 == 0 else "A bit too technical"
        ml_penny.process_user_feedback(feedback, scenario['context'])
        print(f"💬 Feedback: '{feedback}'")
    
    print(f"\n🧠 Final Personality Prompt:")
    print(ml_penny.get_personality_prompt_for_llm({'topic': 'debugging', 'emotion': 'stressed'}))
    
    print("\n✅ ML-Enhanced Penny integration test complete!")
