#!/usr/bin/env python3
"""
Enhanced Humor System for Penny
Adds contextual comedy, observational humor, and situational awareness
"""

import random
import time
import re
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum


class HumorType(Enum):
    """Types of humor Penny can use."""
    OBSERVATIONAL = "observational"
    SELF_AWARE = "self_aware"
    TECH_ROASTING = "tech_roasting"
    SITUATIONAL = "situational"
    CALLBACK = "callback"
    TIMING_BASED = "timing_based"
    ANALOGY = "analogy"


@dataclass
class HumorOpportunity:
    """Represents a detected opportunity for humor."""
    humor_type: HumorType
    context: str
    setup: str
    punchline: str
    confidence: float
    timing_delay: float = 0.0


class EnhancedHumorSystem:
    """Advanced humor system with contextual awareness and timing."""
    
    def __init__(self):
        # Humor patterns and triggers
        self.observational_patterns = {
            'debugging': [
                "The beauty of coding: spending 3 hours to automate a 5-minute task, then never using it again.",
                "Debugging is like being a detective in a crime movie where you're also the murderer.",
                "That moment when your code works and you have absolutely no idea why.",
                "Nothing says 'professional developer' like commenting out code instead of deleting it, just in case."
            ],
            'frameworks': [
                "JavaScript frameworks: changing faster than TikTok trends and twice as confusing.",
                "Every JavaScript framework promises to be 'the last one you'll ever need.' Narrator: It wasn't.",
                "React, Vue, Angular, Svelte... at this point we're just collecting Pokemon cards.",
                "The JS ecosystem: where 'lightweight' means only 500 dependencies."
            ],
            'architecture': [
                "Microservices: turning one problem into a distributed systems nightmare.",
                "Clean architecture is like a clean room - looks great until someone actually needs to work in it.",
                "The best part about over-engineering? You get to solve problems you didn't have before.",
                "Enterprise software: where simple solutions go to die slow, committee-driven deaths."
            ],
            'meetings': [
                "That meeting could have been an email. That email could have been a Slack message. That Slack message could have been silence.",
                "Daily standups: where 'quick sync' means 45 minutes of my life I'll never get back.",
                "Nothing says productivity like scheduling a meeting to plan the meeting about the meeting.",
                "Status update: still pretending to understand what everyone else is talking about."
            ]
        }
        
        self.self_aware_humor = [
            "I'm an AI giving you life advice. Let that sink in for a moment.",
            "Here I am, an artificial intelligence, explaining why humans do illogical things. The irony is not lost on me.",
            "I don't even have thumbs and I'm still more helpful than autocorrect.",
            "An AI with personality - what could possibly go wrong?",
            "I process information at gigahertz speeds but still can't figure out why people use Internet Explorer.",
            "I'm running on servers somewhere, judging your code choices. We live in interesting times.",
            "Congratulations, you're taking technical advice from a computer program with an attitude problem."
        ]
        
        self.timing_based_humor = {
            'long_pause': [
                "Well, this is awkward. Did I break something or are you just contemplating life?",
                "I can hear you thinking from here. Need a moment?",
                "Taking some time to process my wisdom? I'll wait."
            ],
            'quick_response': [
                "Wow, that was fast. Did you even read my response or just mash Enter?",
                "Speed typing champion over here!",
                "Either you're very decisive or you didn't think this through."
            ],
            'repeat_question': [
                "Déjà vu or did you just ask me the same thing again?",
                "I answered this already, but sure, let me repeat myself for the people in the back.",
                "Either your memory is failing or you're testing mine."
            ]
        }
        
        self.analogy_generators = {
            'complexity': [
                "That's like trying to solve a Rubik's cube while blindfolded and riding a unicycle",
                "About as straightforward as assembling IKEA furniture with instructions in Klingon",
                "Like performing surgery with oven mitts - technically possible but why would you?",
                "That approach is like using a flamethrower to light a candle"
            ],
            'inefficiency': [
                "That's like hiring a marching band to wake up one person",
                "About as efficient as a chocolate teapot",
                "Like taking a helicopter to cross the street",
                "That's the scenic route through bureaucracy mountain"
            ],
            'overengineering': [
                "That's like building a spaceship to get to the grocery store",
                "About as necessary as a submarine with screen doors",
                "Like using machine learning to decide what to have for breakfast",
                "That's bringing a rocket launcher to a pillow fight"
            ]
        }
        
        # Callback humor storage
        self.conversation_callbacks = []
        self.inside_jokes = []
        
        # Timing tracking
        self.last_response_time = time.time()
        self.response_count = 0
        
    def detect_humor_opportunities(self, user_input: str, context: str, 
                                 conversation_history: List[str]) -> List[HumorOpportunity]:
        """Detect opportunities for humor in the current context."""
        opportunities = []
        user_lower = user_input.lower()
        
        # 1. Observational humor based on tech topics
        for topic, jokes in self.observational_patterns.items():
            if any(keyword in user_lower for keyword in self._get_topic_keywords(topic)):
                joke = random.choice(jokes)
                opportunities.append(HumorOpportunity(
                    humor_type=HumorType.OBSERVATIONAL,
                    context=f"tech topic: {topic}",
                    setup=user_input,
                    punchline=joke,
                    confidence=0.8
                ))
        
        # 2. Self-aware AI humor
        ai_triggers = ['ai', 'artificial intelligence', 'robot', 'computer', 'algorithm']
        if any(trigger in user_lower for trigger in ai_triggers):
            joke = random.choice(self.self_aware_humor)
            opportunities.append(HumorOpportunity(
                humor_type=HumorType.SELF_AWARE,
                context="AI discussion",
                setup=user_input,
                punchline=joke,
                confidence=0.7
            ))
        
        # 3. Timing-based humor
        current_time = time.time()
        time_since_last = current_time - self.last_response_time
        
        if time_since_last > 30:  # Long pause
            joke = random.choice(self.timing_based_humor['long_pause'])
            opportunities.append(HumorOpportunity(
                humor_type=HumorType.TIMING_BASED,
                context="long pause",
                setup="silence",
                punchline=joke,
                confidence=0.6,
                timing_delay=1.0
            ))
        elif time_since_last < 2:  # Quick response
            joke = random.choice(self.timing_based_humor['quick_response'])
            opportunities.append(HumorOpportunity(
                humor_type=HumorType.TIMING_BASED,
                context="quick response",
                setup="fast typing",
                punchline=joke,
                confidence=0.5
            ))
        
        # 4. Repetition detection
        if self._is_repeat_question(user_input, conversation_history):
            joke = random.choice(self.timing_based_humor['repeat_question'])
            opportunities.append(HumorOpportunity(
                humor_type=HumorType.TIMING_BASED,
                context="repeat question",
                setup="repetition",
                punchline=joke,
                confidence=0.7
            ))
        
        # 5. Analogy opportunities
        complexity_triggers = ['complex', 'complicated', 'difficult', 'hard']
        if any(trigger in user_lower for trigger in complexity_triggers):
            analogy = random.choice(self.analogy_generators['complexity'])
            opportunities.append(HumorOpportunity(
                humor_type=HumorType.ANALOGY,
                context="complexity complaint",
                setup=user_input,
                punchline=analogy,
                confidence=0.6
            ))
        
        # 6. Callback humor from previous conversations
        callback_opportunity = self._detect_callback_opportunity(user_input, context)
        if callback_opportunity:
            opportunities.append(callback_opportunity)
        
        return opportunities
    
    def _get_topic_keywords(self, topic: str) -> List[str]:
        """Get keywords that trigger specific humor topics."""
        keyword_map = {
            'debugging': ['debug', 'bug', 'error', 'broken', 'fix', 'issue', 'problem'],
            'frameworks': ['react', 'vue', 'angular', 'svelte', 'framework', 'library'],
            'architecture': ['microservice', 'architecture', 'design pattern', 'clean code'],
            'meetings': ['meeting', 'standup', 'sync', 'call', 'conference']
        }
        return keyword_map.get(topic, [])
    
    def _is_repeat_question(self, user_input: str, history: List[str]) -> bool:
        """Check if user is repeating a previous question."""
        if len(history) < 2:
            return False
        
        # Simple similarity check
        user_lower = user_input.lower()
        for previous in history[-5:]:  # Check last 5 messages
            if len(previous) > 10 and user_lower in previous.lower():
                return True
        return False
    
    def _detect_callback_opportunity(self, user_input: str, context: str) -> Optional[HumorOpportunity]:
        """Detect opportunities to reference previous jokes or conversations."""
        # This would check against stored conversation history for callback opportunities
        # For now, return None - would be enhanced with actual conversation memory
        return None
    
    def generate_humorous_response(self, base_response: str, opportunities: List[HumorOpportunity]) -> str:
        """Enhance base response with humor."""
        if not opportunities:
            return base_response
        
        # Select best humor opportunity
        best_opportunity = max(opportunities, key=lambda x: x.confidence)
        
        # Only use humor if confidence is high enough
        if best_opportunity.confidence < 0.5:
            return base_response
        
        # Generate enhanced response based on humor type
        if best_opportunity.humor_type == HumorType.OBSERVATIONAL:
            return f"{base_response}\n\n{best_opportunity.punchline}"
        
        elif best_opportunity.humor_type == HumorType.SELF_AWARE:
            return f"{best_opportunity.punchline}\n\n{base_response}"
        
        elif best_opportunity.humor_type == HumorType.TIMING_BASED:
            return f"{best_opportunity.punchline}\n\n{base_response}"
        
        elif best_opportunity.humor_type == HumorType.ANALOGY:
            return f"{base_response} {best_opportunity.punchline}."
        
        else:
            return f"{base_response}\n\n{best_opportunity.punchline}"
    
    def add_callback_memory(self, joke: str, context: str):
        """Store a joke for potential future callbacks."""
        self.conversation_callbacks.append({
            'joke': joke,
            'context': context,
            'timestamp': time.time()
        })
        
        # Keep only recent callbacks
        if len(self.conversation_callbacks) > 50:
            self.conversation_callbacks = self.conversation_callbacks[-50:]
    
    def create_inside_joke(self, user_input: str, response: str, context: str):
        """Create an inside joke based on interaction."""
        # Simple inside joke creation based on funny interactions
        if any(word in user_input.lower() for word in ['fail', 'broke', 'disaster', 'mess']):
            self.inside_jokes.append({
                'reference': user_input[:50],
                'context': context,
                'timestamp': time.time()
            })
    
    def update_timing(self):
        """Update timing for timing-based humor."""
        self.last_response_time = time.time()
        self.response_count += 1


def create_enhanced_humor_system():
    """Factory function to create enhanced humor system."""
    return EnhancedHumorSystem()


if __name__ == "__main__":
    print("🎭 Testing Enhanced Humor System")
    print("=" * 40)
    
    humor_system = EnhancedHumorSystem()
    
    test_inputs = [
        ("I'm debugging this stupid code", "debugging context"),
        ("Which JavaScript framework should I use?", "framework discussion"),
        ("AI is taking over the world", "AI discussion"),
        ("This is really complex and difficult", "complexity complaint"),
        ("I need help with React", "framework help"),
    ]
    
    for user_input, context in test_inputs:
        print(f"\n📝 Input: '{user_input}'")
        print(f"🎯 Context: {context}")
        
        opportunities = humor_system.detect_humor_opportunities(
            user_input, context, []
        )
        
        if opportunities:
            best = max(opportunities, key=lambda x: x.confidence)
            print(f"😂 Humor Type: {best.humor_type.value}")
            print(f"🎭 Joke: '{best.punchline}'")
            print(f"📊 Confidence: {best.confidence:.2f}")
            
            base_response = "Here's a helpful response about your question."
            enhanced = humor_system.generate_humorous_response(base_response, opportunities)
            print(f"💬 Enhanced Response: '{enhanced}'")
        else:
            print("❌ No humor opportunities detected")
        
        humor_system.update_timing()
    
    print("\n✅ Enhanced Humor System test complete!")
