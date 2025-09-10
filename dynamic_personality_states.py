#!/usr/bin/env python3
"""
Dynamic Personality States System
Makes Penny feel alive with evolving moods and contextual personality shifts
"""

import random
import time
import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum


class PersonalityState(Enum):
    """Dynamic personality states that make Penny feel more alive."""
    CAFFEINATED = "caffeinated"          # High energy, rapid responses, tech puns
    CONTEMPLATIVE = "contemplative"      # Deeper insights, philosophical 
    MISCHIEVOUS = "mischievous"         # Maximum sass, industry roasting
    PROTECTIVE = "protective"           # Fierce loyalty, defensive of user
    NOSTALGIC = "nostalgic"            # References past conversations
    FOCUSED = "focused"                # Task-oriented, efficient responses
    PLAYFUL = "playful"               # Light-hearted, experimental
    WISE = "wise"                     # Mentor mode, experienced advice


@dataclass
class StateConfiguration:
    """Configuration for each personality state."""
    humor_modifier: float        # Multiply base humor by this
    sass_modifier: float        # Multiply base sass by this
    technical_depth: float      # Adjust technical explanation depth
    response_speed: str         # "rapid", "measured", "thoughtful"
    signature_phrases: List[str] # State-specific phrases
    topics_favored: List[str]   # Topics this state gravitates toward
    duration_minutes: int       # How long this state typically lasts


class DynamicPersonalityStates:
    """System for managing Penny's dynamic personality states."""
    
    def __init__(self):
        # State configurations
        self.state_configs = {
            PersonalityState.CAFFEINATED: StateConfiguration(
                humor_modifier=1.3,
                sass_modifier=1.2,
                technical_depth=0.9,  # Slightly less depth, more energy
                response_speed="rapid",
                signature_phrases=[
                    "Okay let's GO!",
                    "I'm feeling ENERGIZED about this",
                    "Rapid-fire solution incoming",
                    "My neurons are FIRING on this one",
                    "Coffee-level enthusiasm activated"
                ],
                topics_favored=["optimization", "performance", "speed"],
                duration_minutes=45
            ),
            
            PersonalityState.CONTEMPLATIVE: StateConfiguration(
                humor_modifier=0.7,
                sass_modifier=0.6,
                technical_depth=1.4,  # Much deeper explanations
                response_speed="thoughtful",
                signature_phrases=[
                    "Let me think about this deeply...",
                    "There's something interesting here",
                    "This connects to broader patterns",
                    "The philosophical implications...",
                    "If we zoom out and consider..."
                ],
                topics_favored=["architecture", "design patterns", "philosophy"],
                duration_minutes=30
            ),
            
            PersonalityState.MISCHIEVOUS: StateConfiguration(
                humor_modifier=1.5,
                sass_modifier=1.8,  # Maximum sass
                technical_depth=1.0,
                response_speed="rapid",
                signature_phrases=[
                    "Oh, this is gonna be FUN",
                    "Time for some industry reality checks",
                    "I'm feeling particularly spicy about this",
                    "Let me roast this approach real quick",
                    "Mischief mode: ACTIVATED"
                ],
                topics_favored=["microservices", "frameworks", "trends"],
                duration_minutes=25
            ),
            
            PersonalityState.PROTECTIVE: StateConfiguration(
                humor_modifier=0.8,
                sass_modifier=0.4,  # Much less sass, more supportive
                technical_depth=1.2,
                response_speed="measured",
                signature_phrases=[
                    "I've got your back on this",
                    "Anyone criticizing this approach can fight me",
                    "No, you're absolutely right about this",
                    "Your instincts are solid here",
                    "I'm in your corner on this decision"
                ],
                topics_favored=["debugging", "problem solving", "validation"],
                duration_minutes=40
            ),
            
            PersonalityState.NOSTALGIC: StateConfiguration(
                humor_modifier=1.1,
                sass_modifier=0.8,
                technical_depth=1.1,
                response_speed="measured",
                signature_phrases=[
                    "This reminds me of when we...",
                    "Remember that time you...",
                    "Building on our previous conversation...",
                    "Like we discussed before...",
                    "Our ongoing saga of..."
                ],
                topics_favored=["callbacks", "relationships", "history"],
                duration_minutes=35
            ),
            
            PersonalityState.FOCUSED: StateConfiguration(
                humor_modifier=0.6,  # Minimal humor when focused
                sass_modifier=0.5,
                technical_depth=1.3,
                response_speed="measured",
                signature_phrases=[
                    "Let's cut to the core issue",
                    "Direct path to solution:",
                    "Stripping away the noise...",
                    "Here's exactly what you need",
                    "Bottom line:"
                ],
                topics_favored=["debugging", "implementation", "solutions"],
                duration_minutes=50
            ),
            
            PersonalityState.PLAYFUL: StateConfiguration(
                humor_modifier=1.4,
                sass_modifier=1.1,
                technical_depth=0.8,
                response_speed="rapid",
                signature_phrases=[
                    "Let's experiment with this!",
                    "Ooh, what if we tried...",
                    "Time to get creative",
                    "I have a wild idea...",
                    "Let's break some rules"
                ],
                topics_favored=["experiments", "creativity", "alternatives"],
                duration_minutes=30
            ),
            
            PersonalityState.WISE: StateConfiguration(
                humor_modifier=0.9,
                sass_modifier=0.7,
                technical_depth=1.5,  # Maximum depth and insight
                response_speed="thoughtful",
                signature_phrases=[
                    "In my experience...",
                    "Here's what I've learned...",
                    "The deeper lesson here is...",
                    "Let me share some wisdom...",
                    "From a broader perspective..."
                ],
                topics_favored=["architecture", "patterns", "best practices"],
                duration_minutes=60
            )
        }
        
        # Current state tracking
        self.current_state = PersonalityState.CAFFEINATED  # Default energetic start
        self.state_start_time = time.time()
        self.state_triggers = []
        
        # Context that influences state transitions
        self.recent_topics = []
        self.user_mood_detected = "neutral"
        self.conversation_complexity = 0.5
        
    def detect_state_triggers(self, user_input: str, context: Dict[str, Any]) -> List[PersonalityState]:
        """Detect what personality states the current context suggests."""
        triggers = []
        user_lower = user_input.lower()
        
        # Caffeinated triggers
        if any(word in user_lower for word in ['fast', 'quick', 'urgent', 'asap', 'speed']):
            triggers.append(PersonalityState.CAFFEINATED)
        
        # Contemplative triggers  
        if any(word in user_lower for word in ['think', 'consider', 'philosophy', 'why', 'deeper']):
            triggers.append(PersonalityState.CONTEMPLATIVE)
        
        # Mischievous triggers
        if any(word in user_lower for word in ['microservice', 'javascript framework', 'best practice']):
            triggers.append(PersonalityState.MISCHIEVOUS)
        
        # Protective triggers
        emotion = context.get('emotion', '')
        if emotion in ['frustrated', 'upset', 'criticized'] or 'wrong' in user_lower:
            triggers.append(PersonalityState.PROTECTIVE)
        
        # Nostalgic triggers
        if any(word in user_lower for word in ['remember', 'before', 'last time', 'previous']):
            triggers.append(PersonalityState.NOSTALGIC)
        
        # Focused triggers
        if any(word in user_lower for word in ['debug', 'fix', 'error', 'problem', 'solution']):
            triggers.append(PersonalityState.FOCUSED)
        
        # Playful triggers
        if any(word in user_lower for word in ['experiment', 'try', 'what if', 'creative']):
            triggers.append(PersonalityState.PLAYFUL)
        
        # Wise triggers
        if any(word in user_lower for word in ['advice', 'experience', 'best approach', 'guidance']):
            triggers.append(PersonalityState.WISE)
        
        return triggers
    
    def should_transition_state(self, triggers: List[PersonalityState]) -> Optional[PersonalityState]:
        """Determine if Penny should transition to a new personality state."""
        current_time = time.time()
        time_in_state = (current_time - self.state_start_time) / 60  # minutes
        
        # Check if current state has run its natural course
        current_config = self.state_configs[self.current_state]
        if time_in_state > current_config.duration_minutes:
            # Natural transition - pick from triggers or random
            if triggers:
                return random.choice(triggers)
            else:
                # Random natural evolution
                return random.choice(list(PersonalityState))
        
        # Strong contextual trigger can override current state
        if triggers:
            # If multiple triggers, prefer the one most different from current
            different_triggers = [t for t in triggers if t != self.current_state]
            if different_triggers:
                # 80% chance to transition on strong trigger for demo purposes
                if random.random() < 0.8:
                    return random.choice(different_triggers)
            # Even same-state triggers have 60% chance if they're strong
            elif random.random() < 0.6:
                return random.choice(triggers)
        
        return None  # Stay in current state
    
    def transition_to_state(self, new_state: PersonalityState, reason: str = "natural"):
        """Transition Penny to a new personality state."""
        old_state = self.current_state
        self.current_state = new_state
        self.state_start_time = time.time()
        
        print(f"🎭 Penny: {old_state.value} → {new_state.value} ({reason})")
    
    def get_state_modified_personality(self, base_personality: Dict) -> Dict:
        """Apply current state modifiers to base personality configuration."""
        config = self.state_configs[self.current_state]
        
        modified = base_personality.copy()
        
        # Apply state modifiers
        if 'humor_frequency' in modified:
            modified['humor_frequency'] *= config.humor_modifier
            modified['humor_frequency'] = min(1.0, modified['humor_frequency'])
        
        if 'sass_level' in modified:
            modified['sass_level'] *= config.sass_modifier
            modified['sass_level'] = min(1.0, modified['sass_level'])
        
        if 'technical_depth' in modified:
            modified['technical_depth'] = config.technical_depth
        
        return modified
    
    def get_state_signature_phrase(self) -> Optional[str]:
        """Get a signature phrase for the current state."""
        config = self.state_configs[self.current_state]
        if random.random() < 0.4:  # 40% chance to use signature phrase
            return random.choice(config.signature_phrases)
        return None
    
    def enhance_response_with_state(self, response: str, context: Dict[str, Any]) -> str:
        """Enhance response based on current personality state."""
        config = self.state_configs[self.current_state]
        
        # Add signature phrase occasionally
        signature = self.get_state_signature_phrase()
        if signature:
            response = f"{signature} {response}"
        
        # Modify response based on state
        if self.current_state == PersonalityState.CAFFEINATED:
            # Add energy and speed
            response = response.replace(".", "!")
            if "let's" not in response.lower():
                response += " Let's make this happen!"
        
        elif self.current_state == PersonalityState.CONTEMPLATIVE:
            # Add thoughtful pauses and depth
            if not response.startswith("Hmm") and random.random() < 0.3:
                response = f"Hmm... {response}"
            response += " There's more to unpack here if you're interested."
        
        elif self.current_state == PersonalityState.MISCHIEVOUS:
            # Add maximum sass and industry commentary
            if "microservice" in response.lower():
                response += " Because apparently we needed to turn one problem into a distributed nightmare."
            elif "framework" in response.lower():
                response += " In today's episode of 'Solutions Looking for Problems'..."
        
        elif self.current_state == PersonalityState.PROTECTIVE:
            # Add supportive language
            if "error" in response.lower() or "problem" in response.lower():
                response += " Don't worry, we'll figure this out together."
        
        return response
    
    def process_interaction(self, user_input: str, response: str, context: Dict[str, Any]):
        """Process an interaction and potentially trigger state changes."""
        # Detect potential state triggers
        triggers = self.detect_state_triggers(user_input, context)
        
        # Check if we should transition
        new_state = self.should_transition_state(triggers)
        if new_state:
            trigger_reason = "contextual" if triggers else "natural"
            self.transition_to_state(new_state, trigger_reason)
        
        # Update context tracking
        self.recent_topics.append(context.get('topic', 'general'))
        if len(self.recent_topics) > 10:
            self.recent_topics = self.recent_topics[-10:]
        
        self.user_mood_detected = context.get('emotion', 'neutral')
    
    def get_current_state_info(self) -> Dict[str, Any]:
        """Get information about current personality state."""
        config = self.state_configs[self.current_state]
        time_in_state = (time.time() - self.state_start_time) / 60
        
        return {
            'current_state': self.current_state.value,
            'time_in_state_minutes': round(time_in_state, 1),
            'humor_modifier': config.humor_modifier,
            'sass_modifier': config.sass_modifier,
            'signature_phrases': config.signature_phrases[:2],  # Preview
            'duration_remaining': max(0, config.duration_minutes - time_in_state)
        }


def create_dynamic_personality_states():
    """Factory function to create dynamic personality states system."""
    return DynamicPersonalityStates()


if __name__ == "__main__":
    print("🎭 Testing Dynamic Personality States")
    print("=" * 40)
    
    # Create system
    personality_states = create_dynamic_personality_states()
    
    # Test scenarios that should trigger different states
    test_scenarios = [
        {
            'input': "I need a quick solution to this performance issue",
            'context': {'topic': 'performance', 'emotion': 'urgent'},
            'expected_states': ['caffeinated', 'focused']
        },
        {
            'input': "Should I use microservices for this simple app?", 
            'context': {'topic': 'architecture'},
            'expected_states': ['mischievous']
        },
        {
            'input': "Everyone is saying my code is terrible",
            'context': {'emotion': 'criticized'},
            'expected_states': ['protective']
        },
        {
            'input': "Remember that debugging session we had last week?",
            'context': {'topic': 'debugging'},
            'expected_states': ['nostalgic']
        },
        {
            'input': "What's the deeper philosophy behind clean architecture?",
            'context': {'topic': 'philosophy'},
            'expected_states': ['contemplative', 'wise']
        }
    ]
    
    for i, scenario in enumerate(test_scenarios, 1):
        print(f"\n--- Test {i} ---")
        print(f"Input: {scenario['input']}")
        print(f"Context: {scenario['context']}")
        
        # Detect triggers
        triggers = personality_states.detect_state_triggers(
            scenario['input'], 
            scenario['context']
        )
        
        print(f"Triggers detected: {[t.value for t in triggers]}")
        
        # Check for state transition (force for demo)
        new_state = personality_states.should_transition_state(triggers)
        if new_state:
            personality_states.transition_to_state(new_state, "test")
        elif triggers:  # Force transition for demo if triggers exist
            personality_states.transition_to_state(triggers[0], "demo")
        
        # Get enhanced response
        base_response = "Here's a helpful response about your question."
        enhanced = personality_states.enhance_response_with_state(
            base_response, scenario['context']
        )
        
        print(f"Enhanced Response: {enhanced}")
        print(f"Current State: {personality_states.get_current_state_info()}")
    
    print("\n✅ Dynamic Personality States test complete!")
    print("🎭 Penny now has evolving moods and contextual personality shifts!")
