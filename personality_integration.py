#!/usr/bin/env python3
"""
Personality Integration Layer
Connects the enhanced Penny personality system with the emotional memory system
"""

import sys
import os
import time
from typing import Dict, Any, Optional, List

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
sys.path.insert(0, os.path.dirname(__file__))

from src.core.personality import PennyPersonalitySystem, create_personality_context, PersonalityContext


class PersonalityIntegrationLayer:
    """Integration layer between personality system and emotional memory."""
    
    def __init__(self, emotional_memory):
        self.emotional_memory = emotional_memory
        self.personality_system = PennyPersonalitySystem()
        
        # Track conversation patterns for personality adaptation
        self.conversation_history = []
        self.user_personality_profile = {
            'prefers_sass': None,  # Will be learned
            'tech_interest_level': 0.5,
            'humor_appreciation': None,
            'formality_preference': 'casual'
        }
        
        print("🎭 Penny personality integration initialized with emotional memory")
        
    def create_enhanced_personality_context(self, user_input: str) -> PersonalityContext:
        """Create personality context from emotional memory insights."""
        
        # Get emotional insights
        insights = self.emotional_memory.get_emotional_insights()
        
        # Get current emotional context
        current_emotion = "neutral"
        conversation_tone = "casual"
        stress_level = 0.0
        
        if self.emotional_memory.current_emotional_context:
            current_emotion = self.emotional_memory.current_emotional_context.detected_emotion.value
            conversation_tone = self.emotional_memory.current_emotional_context.conversation_tone
            stress_level = self.emotional_memory.current_emotional_context.user_stress_level
        
        # Build relationship context
        relationship_context = {
            'known_people': {},
            'recent_mentions': [],
            'emotional_associations': {}
        }
        
        # Get recently mentioned people (last 24 hours)
        recent_cutoff = time.time() - (24 * 60 * 60)
        for name, member in self.emotional_memory.family_members.items():
            if member.last_mentioned > recent_cutoff:
                relationship_context['recent_mentions'].append({
                    'name': name,
                    'relationship': member.relationship_type.value,
                    'context': member.context,
                    'primary_emotion': self._get_primary_emotion(member.emotional_associations)
                })
            
            relationship_context['known_people'][name] = {
                'type': member.relationship_type.value,
                'mentions': member.mention_count,
                'context': member.context
            }
        
        # Determine topic category
        topic_category = self._categorize_topic(user_input, insights)
        
        # Get user preferences from memory
        user_preferences = {}
        try:
            for key, pref in self.emotional_memory.base_memory.user_preferences.items():
                if pref.confidence > 0.3:
                    user_preferences[key] = pref.value
        except:
            pass  # Graceful fallback if user_preferences not available
        
        # Get recent interaction patterns
        recent_interactions = self._get_recent_interactions()
        
        return create_personality_context(
            user_emotion=current_emotion,
            conversation_tone=conversation_tone,
            user_stress_level=stress_level,
            relationship_context=relationship_context,
            topic_category=topic_category,
            user_preferences=user_preferences,
            recent_interactions=recent_interactions
        )
    
    def _get_primary_emotion(self, emotional_associations: Dict[str, float]) -> str:
        """Get the primary emotion from emotional associations."""
        if not emotional_associations:
            return 'neutral'
        return max(emotional_associations.items(), key=lambda x: x[1])[0]
    
    def _categorize_topic(self, user_input: str, insights: Dict[str, Any]) -> str:
        """Categorize the topic of user input."""
        user_lower = user_input.lower()
        
        # Tech-related keywords
        tech_keywords = [
            'computer', 'software', 'app', 'website', 'code', 'programming', 
            'ai', 'artificial intelligence', 'technology', 'tech', 'digital',
            'internet', 'online', 'phone', 'smartphone', 'laptop', 'tablet'
        ]
        
        # Relationship keywords
        relationship_keywords = [
            'family', 'mom', 'dad', 'sister', 'brother', 'friend', 'boyfriend',
            'girlfriend', 'husband', 'wife', 'relationship', 'dating', 'marriage'
        ]
        
        # Work/stress keywords
        work_keywords = [
            'work', 'job', 'boss', 'colleague', 'meeting', 'deadline', 'project',
            'stress', 'busy', 'overwhelmed', 'tired', 'pressure'
        ]
        
        # Learning keywords
        learning_keywords = [
            'learn', 'teach', 'explain', 'understand', 'how', 'what', 'why',
            'education', 'study', 'knowledge', 'help me'
        ]
        
        if any(keyword in user_lower for keyword in tech_keywords):
            return 'technology'
        elif any(keyword in user_lower for keyword in relationship_keywords):
            return 'relationships'
        elif any(keyword in user_lower for keyword in work_keywords):
            return 'work_stress'
        elif any(keyword in user_lower for keyword in learning_keywords):
            return 'learning'
        else:
            return 'general'
    
    def _get_recent_interactions(self, limit: int = 10) -> List[str]:
        """Get recent interaction patterns."""
        # Get recent conversations from base memory
        try:
            recent_conversations = self.emotional_memory.base_memory.get_recent_conversations(limit)
            return [conv.user_input for conv in recent_conversations]
        except:
            return []  # Graceful fallback
    
    def adapt_personality_based_on_feedback(self, user_input: str, assistant_response: str):
        """Adapt personality based on user feedback patterns."""
        user_lower = user_input.lower()
        
        # Detect feedback about personality
        positive_feedback = [
            'funny', 'hilarious', 'love it', 'perfect', 'great', 'awesome',
            'exactly', 'yes', 'right', 'good one', 'haha', 'lol'
        ]
        
        negative_feedback = [
            'too much', 'annoying', 'stop', 'not funny', 'serious', 'rude',
            'inappropriate', 'tone it down', 'be nice'
        ]
        
        # Check if user is responding to sass/humor
        if any(phrase in user_lower for phrase in positive_feedback):
            if self.personality_system.current_mode.value in ['sassy', 'playful']:
                self.user_personality_profile['prefers_sass'] = True
                self.user_personality_profile['humor_appreciation'] = True
        
        elif any(phrase in user_lower for phrase in negative_feedback):
            if self.personality_system.current_mode.value in ['sassy', 'playful']:
                self.user_personality_profile['prefers_sass'] = False
                # Temporarily reduce sass levels
                self.personality_system.personality_traits['sarcasm_level'] *= 0.7
        
        # Detect tech interest
        tech_enthusiasm_indicators = [
            'cool', 'interesting', 'tell me more', 'how does it work', 'awesome tech'
        ]
        
        if (self.personality_system.current_mode.value == 'tech' and
            any(phrase in user_lower for phrase in tech_enthusiasm_indicators)):
            self.user_personality_profile['tech_interest_level'] = min(1.0, 
                self.user_personality_profile['tech_interest_level'] + 0.1)
    
    def generate_contextual_response(self, base_response: str, user_input: str) -> str:
        """Generate a contextually appropriate response with full personality."""
        
        # Create enhanced context from emotional memory
        context = self.create_enhanced_personality_context(user_input)
        
        # Apply personality
        enhanced_response = self.personality_system.apply_personality(base_response, context)
        
        # Learn from this interaction
        self.adapt_personality_based_on_feedback(user_input, enhanced_response)
        
        # Store interaction for pattern analysis
        self.conversation_history.append({
            'user_input': user_input,
            'response': enhanced_response,
            'personality_mode': self.personality_system.current_mode.value,
            'timestamp': time.time()
        })
        
        # Keep history manageable
        if len(self.conversation_history) > 50:
            self.conversation_history = self.conversation_history[-25:]
        
        return enhanced_response
    
    def get_personality_insights(self) -> Dict[str, Any]:
        """Get insights about personality usage and adaptation."""
        recent_modes = [
            interaction['personality_mode'] 
            for interaction in self.conversation_history[-10:]
        ]
        
        return {
            'user_personality_profile': self.user_personality_profile,
            'current_mode': self.personality_system.current_mode.value,
            'recent_modes_used': recent_modes,
            'conversation_patterns': {
                'total_interactions': len(self.conversation_history),
                'sass_success_rate': self._calculate_sass_success_rate(),
                'tech_enthusiasm_engagement': self._calculate_tech_engagement()
            }
        }
    
    def _calculate_sass_success_rate(self) -> float:
        """Calculate how well sass is being received."""
        sass_interactions = [
            i for i in self.conversation_history 
            if i['personality_mode'] in ['sassy', 'playful']
        ]
        
        if not sass_interactions:
            return 0.5  # Unknown
        
        # This is simplified - in a real implementation, you'd analyze user responses
        if self.user_personality_profile['prefers_sass'] is True:
            return 0.8
        elif self.user_personality_profile['prefers_sass'] is False:
            return 0.2
        else:
            return 0.5  # Still learning
    
    def _calculate_tech_engagement(self) -> float:
        """Calculate user engagement with tech topics."""
        return self.user_personality_profile['tech_interest_level']


# Integration function for existing pipeline
def create_personality_integration(emotional_memory_system) -> PersonalityIntegrationLayer:
    """Factory function to create personality integration."""
    return PersonalityIntegrationLayer(emotional_memory_system)


# Legacy compatibility - enhanced apply function
def apply_enhanced_personality(text: str, emotional_memory, user_input: str = "") -> str:
    """Enhanced personality application with emotional memory integration."""
    integration = PersonalityIntegrationLayer(emotional_memory)
    return integration.generate_contextual_response(text, user_input)
