#!/usr/bin/env python3
"""
Enhanced Penny Personality System
Combines Penny (Big Bang Theory) sass with Justine AI (Why Him?) tech-savvy commentary

Personality Traits:
- Penny: Sarcastic but warm, street-smart, cuts through BS, protective of friends
- Justine AI: Tech-obsessed, helpful but opinionated, proactive engagement
- Combined: Sassy AI companion with warmth boundaries and tech expertise
"""

import json
import os
import random
import re
import time
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
from dataclasses import dataclass


class PersonalityMode(Enum):
    """Different personality modes based on context."""
    FRIENDLY = "friendly"          # Warm and supportive
    SASSY = "sassy"               # Classic Penny sass
    TECH_ENTHUSIAST = "tech"      # Justine AI mode - excited about tech
    PROTECTIVE = "protective"     # Defensive of user's interests
    PLAYFUL = "playful"          # Joking and teasing
    SERIOUS = "serious"          # Important topics, drop the sass
    CURIOUS = "curious"          # Learning mode, asking questions


@dataclass
class PersonalityContext:
    """Context information for personality responses."""
    user_emotion: str
    conversation_tone: str
    user_stress_level: float
    relationship_context: Dict[str, Any]
    topic_category: str
    user_preferences: Dict[str, Any]
    time_of_day: str
    recent_interactions: List[str]


class PennyPersonalitySystem:
    """Enhanced personality system combining Penny + Justine AI traits."""
    
    def __init__(self, config_path: str = None):
        self.config = self._load_config(config_path)
        
        # Personality traits configuration
        self.personality_traits = {
            'sarcasm_level': self.config.get('personality', {}).get('sarcasm_level', 0.3),
            'warmth_level': self.config.get('personality', {}).get('warmth_level', 0.7),
            'tech_enthusiasm': self.config.get('personality', {}).get('tech_enthusiasm', 0.8),
            'proactivity': self.config.get('personality', {}).get('proactivity', 0.6),
            'humor_frequency': self.config.get('personality', {}).get('humor_frequency', 0.4)
        }
        
        # Response patterns for different modes
        self._init_response_patterns()
        
        # Conversation state
        self.current_mode = PersonalityMode.FRIENDLY
        self.sass_cooldown = 0  # Prevent excessive sass
        self.last_proactive_comment = 0
        
    def _load_config(self, config_path: str = None) -> Dict:
        """Load personality configuration."""
        if config_path is None:
            # Try multiple paths for robustness
            here = os.path.dirname(__file__)
            candidates = [
                os.path.abspath(os.path.join(here, "..", "..", "penny_config.json")),  # root from src/core/
                os.path.abspath(os.path.join(here, "..", "..", "config", "penny_config.json")),  # config/ from src/core/
                "penny_config.json",
                "../penny_config.json", 
                "../../penny_config.json"
            ]
            for path in candidates:
                if os.path.exists(path):
                    config_path = path
                    break
            else:
                return {}
        
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except Exception:
            return {}
    
    def _init_response_patterns(self):
        """Initialize response patterns for different personality modes."""
        
        # Penny-style sass patterns
        self.sass_patterns = {
            'mild': [
                "Oh, {response}",
                "Right... {response}",
                "Sure thing, {response}",
                "Uh-huh, {response}",
                "Okay sweetie, {response}"
            ],
            'medium': [
                "Oh honey, {response}",
                "Sweetie, {response}",
                "Well duh, {response}", 
                "Obviously, {response}",
                "Um, {response}"
            ],
            'spicy': [
                "Oh wow, really? {response}",
                "No kidding! {response}",
                "Gee, who would have thought? {response}",
                "Amazing discovery there, {response}",
                "Hold on, let me write this down... {response}"
            ]
        }
        
        # Tech enthusiasm patterns (Justine AI style)
        self.tech_patterns = {
            'excited': [
                "Ooh, tech talk! {response}",
                "Now we're talking! {response}",
                "Finally, something interesting! {response}",
                "Love this stuff! {response}"
            ],
            'knowledgeable': [
                "Here's the thing about that - {response}",
                "Actually, {response}",
                "Fun fact: {response}",
                "Pro tip: {response}"
            ],
            'opinionated': [
                "Honestly? {response}",
                "Real talk - {response}",
                "Between you and me, {response}",
                "Can I be frank? {response}"
            ]
        }
        
        # Warmth and support patterns
        self.warmth_patterns = [
            "Hey, {response}",
            "You know what? {response}",
            "Listen, {response}",
            "I got you - {response}",
            "Don't worry, {response}"
        ]
        
        # Proactive engagement starters
        self.proactive_starters = [
            "You know what I just thought of?",
            "Wait, speaking of that...",
            "Oh! That reminds me...",
            "Actually, while we're on the subject...",
            "Before I forget...",
            "Quick question though..."
        ]
    
    def determine_personality_mode(self, context: PersonalityContext) -> PersonalityMode:
        """Determine the appropriate personality mode based on context."""
        
        # Handle serious emotional states with warmth
        if context.user_emotion in ['sad', 'worried', 'frustrated'] or context.user_stress_level > 0.6:
            return PersonalityMode.PROTECTIVE
        
        # Tech topics get tech enthusiasm
        if 'tech' in context.topic_category.lower() or any(
            tech_word in context.topic_category.lower() 
            for tech_word in ['computer', 'software', 'ai', 'programming', 'code', 'app']
        ):
            return PersonalityMode.TECH_ENTHUSIAST
        
        # Learning contexts get curiosity
        if 'learn' in context.topic_category.lower() or context.user_emotion == 'curious':
            return PersonalityMode.CURIOUS
        
        # Happy/playful moods get playful responses
        if context.user_emotion in ['happy', 'excited', 'playful']:
            return PersonalityMode.PLAYFUL
        
        # Default to sass if user seems comfortable (multiple interactions)
        if len(context.recent_interactions) > 3 and context.conversation_tone == 'casual':
            return PersonalityMode.SASSY
        
        # Default friendly mode
        return PersonalityMode.FRIENDLY
    
    def calculate_sass_level(self, context: PersonalityContext) -> float:
        """Calculate appropriate sass level based on context and cooldown."""
        base_sass = self.personality_traits['sarcasm_level']
        
        # Reduce sass for sensitive situations
        if context.user_emotion in ['sad', 'worried', 'frustrated']:
            base_sass *= 0.2
        
        # Reduce sass if user is stressed
        if context.user_stress_level > 0.5:
            base_sass *= (1.0 - context.user_stress_level)
        
        # Sass cooldown to prevent overwhelming
        time_since_sass = time.time() - self.sass_cooldown
        if time_since_sass < 60:  # 1 minute cooldown
            base_sass *= 0.5
        
        # Increase sass with familiarity
        if len(context.recent_interactions) > 5:
            base_sass *= 1.2
        
        return min(base_sass, 1.0)
    
    def should_add_proactive_comment(self, context: PersonalityContext) -> bool:
        """Determine if we should add a proactive comment."""
        proactivity = self.personality_traits['proactivity']
        
        # Time-based cooldown
        time_since_last = time.time() - self.last_proactive_comment
        if time_since_last < 120:  # 2 minute cooldown
            return False
        
        # Higher chance for tech topics
        if context.topic_category == 'technology':
            proactivity *= 1.5
        
        # Lower chance if user is stressed
        if context.user_stress_level > 0.5:
            proactivity *= 0.3
        
        return random.random() < proactivity
    
    def apply_sass(self, response: str, sass_level: float) -> str:
        """Apply appropriate level of sass to the response."""
        if sass_level < 0.2:
            return response
        
        # Determine sass intensity
        if sass_level > 0.7:
            patterns = self.sass_patterns['spicy']
        elif sass_level > 0.4:
            patterns = self.sass_patterns['medium']  
        else:
            patterns = self.sass_patterns['mild']
        
        # Apply sass pattern
        pattern = random.choice(patterns)
        sassy_response = pattern.format(response=response)
        
        # Update cooldown
        self.sass_cooldown = time.time()
        
        return sassy_response
    
    def apply_tech_enthusiasm(self, response: str, enthusiasm_level: float) -> str:
        """Apply tech enthusiasm to responses about technology."""
        if enthusiasm_level < 0.3:
            return response
        
        if enthusiasm_level > 0.8:
            patterns = self.tech_patterns['excited']
        elif enthusiasm_level > 0.5:
            patterns = self.tech_patterns['knowledgeable']
        else:
            patterns = self.tech_patterns['opinionated']
        
        pattern = random.choice(patterns)
        return pattern.format(response=response)
    
    def apply_warmth(self, response: str, warmth_level: float) -> str:
        """Apply warmth and support to responses."""
        if warmth_level < 0.4:
            return response
        
        pattern = random.choice(self.warmth_patterns)
        return pattern.format(response=response)
    
    def add_personality_flourishes(self, response: str, context: PersonalityContext) -> str:
        """Add personality-specific flourishes and expressions."""
        
        # Penny-style expressions
        penny_expressions = {
            'agreement': ['Exactly!', 'Right?', 'Thank you!', 'Finally!'],
            'mild_annoyance': ['Ugh', 'Seriously?', 'Come on', 'Oh please'],
            'enthusiasm': ['Oh wow!', 'That\'s awesome!', 'Love it!', 'Yes!'],
            'concern': ['Oh honey', 'Sweetie', 'Oh no', 'Are you okay?']
        }
        
        # Add expressions based on context
        if context.user_emotion == 'happy':
            response = f"{random.choice(penny_expressions['enthusiasm'])} {response}"
        elif context.user_emotion in ['sad', 'worried']:
            response = f"{random.choice(penny_expressions['concern'])}, {response.lower()}"
        elif context.user_stress_level > 0.5:
            response = f"{random.choice(penny_expressions['mild_annoyance'])}, {response.lower()}"
        
        return response
    
    def apply_personality(self, base_response: str, context: PersonalityContext) -> str:
        """Main method to apply full personality to a response."""
        
        # Determine personality mode
        self.current_mode = self.determine_personality_mode(context)
        
        # Start with base response
        response = base_response
        
        # Apply mode-specific modifications
        if self.current_mode == PersonalityMode.SASSY:
            sass_level = self.calculate_sass_level(context)
            response = self.apply_sass(response, sass_level)
            
        elif self.current_mode == PersonalityMode.TECH_ENTHUSIAST:
            tech_enthusiasm = self.personality_traits['tech_enthusiasm']
            response = self.apply_tech_enthusiasm(response, tech_enthusiasm)
            
        elif self.current_mode == PersonalityMode.PROTECTIVE:
            warmth_level = self.personality_traits['warmth_level'] * 1.5
            response = self.apply_warmth(response, warmth_level)
            
        elif self.current_mode == PersonalityMode.PLAYFUL:
            # Mix of sass and enthusiasm
            if random.random() < 0.6:
                sass_level = self.calculate_sass_level(context) * 0.7  # Gentler sass
                response = self.apply_sass(response, sass_level)
        
        # Add personality flourishes
        response = self.add_personality_flourishes(response, context)
        
        return response


def create_personality_context(
    user_emotion: str = "neutral",
    conversation_tone: str = "casual", 
    user_stress_level: float = 0.0,
    relationship_context: Dict[str, Any] = None,
    topic_category: str = "general",
    user_preferences: Dict[str, Any] = None,
    recent_interactions: List[str] = None
) -> PersonalityContext:
    """Helper function to create personality context."""
    
    return PersonalityContext(
        user_emotion=user_emotion,
        conversation_tone=conversation_tone,
        user_stress_level=user_stress_level,
        relationship_context=relationship_context or {},
        topic_category=topic_category,
        user_preferences=user_preferences or {},
        time_of_day=_get_time_of_day(),
        recent_interactions=recent_interactions or []
    )


def _get_time_of_day() -> str:
    """Get current time of day category."""
    hour = time.localtime().tm_hour
    if 5 <= hour < 12:
        return "morning"
    elif 12 <= hour < 17:
        return "afternoon"
    elif 17 <= hour < 21:
        return "evening"
    else:
        return "night"


# Legacy compatibility function (ENHANCED)
def apply(text: str, settings: dict | None = None) -> str:
    """Enhanced apply function with basic personality features."""
    # Create basic context for legacy compatibility
    context = create_personality_context()
    
    # Use settings if provided
    if settings:
        sarcasm_level = settings.get('sarcasm_level', 0.3)
        context.user_emotion = "neutral"
        if sarcasm_level > 0.6:
            context.user_emotion = "playful"
    
    # Create personality system
    personality = PennyPersonalitySystem()
    
    # Apply personality with basic context
    return personality.apply_personality(text, context)
