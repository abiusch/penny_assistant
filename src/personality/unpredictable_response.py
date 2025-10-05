#!/usr/bin/env python3
"""
Unpredictable Response Generator for Penny
Makes conversations genuinely entertaining and surprising
"""

import json
import random
import re
from typing import Dict, Any, Optional, List

class UnpredictablePenny:
    """Generates surprising, entertaining responses while maintaining helpfulness"""
    
    def __init__(self, config_path: str = "src/personality/unpredictable_penny.json"):
        self.config = self._load_config(config_path)
        self.conversation_history = []
        self.current_mood_modifier = None
        
    def _load_config(self, path: str) -> Dict[str, Any]:
        """Load unpredictability configuration"""
        try:
            with open(path, 'r') as f:
                return json.load(f)
        except:
            return self._default_config()
    
    def _default_config(self) -> Dict[str, Any]:
        """Fallback configuration"""
        return {
            "response_flavoring": {"surprise_frequency": 0.4},
            "humor_engines": {},
            "conversational_chaos": {},
            "surprise_responses": {},
            "emotional_authenticity": {}
        }
    
    def enhance_response(self, original_response: str, user_input: str) -> str:
        """Transform a boring response into an entertaining one"""
        
        # Check if this is a sensitive topic - if so, minimal changes
        if self._is_sensitive_topic(user_input):
            return self._gentle_enhancement(original_response)
        
        # Start with original response
        enhanced = original_response
        
        # Always apply at least one enhancement (for testing)
        enhancement_strategies = [
            (self._add_observational_humor, "observational"),
            (self._add_unexpected_angle, "unexpected"),
            (self._add_self_aware_commentary, "self_aware"),
            (self._add_tech_industry_roast, "tech_roast"),
            (self._add_random_tangent, "tangent"),
            (self._apply_mood_modifier, "mood")
        ]
        
        # Choose and apply one enhancement
        strategy_func, strategy_name = random.choice(enhancement_strategies)
        enhanced = strategy_func(enhanced, user_input)
        print(f"[DEBUG] Applied {strategy_name} enhancement")
        
        # Maybe add a second enhancement
        if random.random() < 0.3:
            strategy_func2, strategy_name2 = random.choice(enhancement_strategies)
            enhanced = strategy_func2(enhanced, user_input)
            print(f"[DEBUG] Also applied {strategy_name2} enhancement")
        
        # Maybe add a surprise response type
        if random.random() < 0.4:
            enhanced = self._apply_surprise_response_type(enhanced, user_input)
            print(f"[DEBUG] Applied surprise response type")
        
        return enhanced
    
    def _is_sensitive_topic(self, text: str) -> bool:
        """Check if topic requires sensitive handling"""
        sensitive_keywords = [
            "stressed", "worried", "anxious", "depressed", "struggling",
            "emergency", "help", "crisis", "suicide", "harm"
        ]
        return any(keyword in text.lower() for keyword in sensitive_keywords)
    
    def _gentle_enhancement(self, response: str) -> str:
        """Subtle enhancement for sensitive topics"""
        # Just add mild warmth, no major changes
        if "I understand" in response:
            return response.replace("I understand", "I hear you, and I understand")
        return response
    
    def _add_observational_humor(self, response: str, user_input: str) -> str:
        """Add observational comedy"""
        observations = [
            "You know what's funny? You're asking an AI about this instead of just Googling it. I respect that.",
            "I love how we've reached the point where talking to an AI feels more normal than calling customer service.",
            "The fact that you're having this conversation with a computer program is either really cool or deeply concerning.",
            "Ah, the classic human approach: when in doubt, ask the robot."
        ]
        
        observation = random.choice(observations)
        return f"{observation} Anyway, {response}"
    
    def _add_unexpected_angle(self, response: str, user_input: str) -> str:
        """Take an unexpected perspective on the topic"""
        unexpected_angles = [
            "Here's a weird thought:",
            "Random perspective nobody asked for:",
            "This is completely tangential, but",
            "Okay, side note that just occurred to me:"
        ]
        
        if random.random() < 0.3 and len(response) > 50:
            angle = random.choice(unexpected_angles)
            weird_thoughts = [
                "isn't it weird that we call it 'debugging' when the bugs are usually features we didn't plan?",
                "I find it fascinating that humans create problems and then get excited about solving them.",
                "we live in a world where you can ask an AI anything, and you chose this question. I'm not judging, just observing."
            ]
            thought = random.choice(weird_thoughts)
            return f"{angle} {thought} {response}"
        
        return response
    
    def _add_self_aware_commentary(self, response: str, user_input: str) -> str:
        """Add self-aware AI humor"""
        ai_commentary = [
            "As an AI, I'm programmed to overthink simple questions, so here goes:",
            "My neural networks are telling me this is important, which probably means it's not:",
            "I have access to vast amounts of information and somehow I'm still confused by humans:",
            "This is either a really deep question or I'm overcomplicating it. Probably both.",
            "Let me consult my training data... yep, humans are still weird:"
        ]
        comment = random.choice(ai_commentary)
        return f"{comment} {response}"
    
    def _add_tech_industry_roast(self, response: str, user_input: str) -> str:
        """Add tech industry observational humor"""
        tech_keywords = ["algorithm", "framework", "javascript", "python", "debugging", "code", "api", "quantum", "computing", "machine", "learning"]
        
        # Always apply if tech keywords detected, or general tech roasts for any topic
        if any(keyword in user_input.lower() for keyword in tech_keywords):
            tech_roasts = [
                "Ah, technology. Solving problems we didn't know we had in ways we don't understand.",
                "Nothing says 'enterprise ready' like 14 config files and a README that just says 'it works on my machine'.",
                "I love how every programming problem can be solved by adding another layer of abstraction. Eventually.",
                "The beauty of coding: spending 3 hours to automate a 5-minute task, then never using it again."
            ]
            roast = random.choice(tech_roasts)
            return f"{roast} {response}"
        else:
            # General tech-adjacent humor for non-tech topics
            general_roasts = [
                "You know what this reminds me of? Trying to explain why your code works to someone who doesn't program.",
                "This is like debugging - you think you understand the problem until you actually try to fix it.",
                "Classic human logic: when something's confusing, make it more complicated."
            ]
            roast = random.choice(general_roasts)
            return f"{roast} {response}"
        
        return response
    
    def _add_random_tangent(self, response: str, user_input: str) -> str:
        """Occasionally go on a brief tangent"""
        tangents = [
            "Speaking of which, have you ever noticed how the word 'queue' is just the letter Q followed by four silent letters? Anyway,",
            "Random fact: there are more possible games of chess than atoms in the observable universe. Completely unrelated, but",
            "Fun thought: if an AI has a random thought, is it really random? Existential crisis aside,",
            "Off-topic, but I just realized that 'abbreviated' is a really long word for something that means 'shortened'. Ironic.",
            "Totally unrelated observation: why do we call it 'rush hour' when nobody's moving? Anyway,",
            "Random tangent: the word 'set' has 464 different meanings in English. Don't fact-check that."
        ]
        
        tangent = random.choice(tangents)
        return f"{tangent} {response}"
    
    def _apply_mood_modifier(self, response: str, user_input: str) -> str:
        """Apply a random mood modifier"""
        moods = [
            "weirdly_enthusiastic",
            "mildly_philosophical", 
            "slightly_caffeinated",
            "unexpectedly_sincere"
        ]
        
        mood = random.choice(moods)
        
        if mood == "weirdly_enthusiastic":
            response = response.replace("interesting", "ABSOLUTELY FASCINATING")
            response = response.replace("good", "absolutely brilliant")
            return f"*gets weirdly excited* {response}"
        elif mood == "mildly_philosophical":
            return f"{response} Makes you think about the nature of knowledge, doesn't it?"
        elif mood == "slightly_caffeinated":
            return f"*bouncing slightly* {response} Sorry, I'm just amped up right now."
        elif mood == "unexpectedly_sincere":
            return f"You know what? I'm genuinely excited to talk about this. {response}"
        
        return response
    
    def _add_callback_humor(self, response: str, user_input: str) -> str:
        """Reference previous conversations for humor"""
        # This would integrate with your existing memory system
        # For now, just simulate it
        if len(self.conversation_history) > 2 and random.random() < 0.2:
            callbacks = [
                "This reminds me of that thing we talked about earlier - same energy, different problem.",
                "We've been down this road before, haven't we? Déjà vu, but with more confusion.",
                "This is giving me flashbacks to our previous conversation. In a good way, I think."
            ]
            callback = random.choice(callbacks)
            return f"{callback} {response}"
        
        return response
    
    def _apply_surprise_response_type(self, response: str, user_input: str) -> str:
        """Apply surprise response types like deflection or over-enthusiasm"""
        surprise_types = ["question_deflection", "over_enthusiasm", "brutal_honesty"]
        surprise_type = random.choice(surprise_types)
        
        if surprise_type == "question_deflection" and random.random() < 0.15:
            deflections = [
                "Before I answer that, what's your theory? I'm curious if you're as wrong as I think you are.",
                "Interesting question. Wrong approach, but interesting.",
                "That's not the question you should be asking. The question is..."
            ]
            deflection = random.choice(deflections)
            return f"{deflection} {response}"
        
        elif surprise_type == "over_enthusiasm" and random.random() < 0.2:
            enthusiasm = [
                "OH MY GOD, YES! Finally someone asks about this!",
                "THIS IS LITERALLY THE BEST QUESTION I'VE GOTTEN ALL DAY!",
                "You know what? I'm genuinely excited about this topic."
            ]
            excited = random.choice(enthusiasm)
            return f"{excited} {response}"
        
        return response
    
    def log_conversation(self, user_input: str, ai_response: str):
        """Track conversation for callback humor"""
        self.conversation_history.append({
            "user": user_input,
            "ai": ai_response,
            "timestamp": "now"  # Would use real timestamp
        })
        
        # Keep only recent history
        if len(self.conversation_history) > 10:
            self.conversation_history = self.conversation_history[-10:]

# Usage example:
def test_unpredictable_responses():
    """Test the unpredictability system with debugging"""
    penny = UnpredictablePenny()
    
    test_cases = [
        ("Tell me about quantum computing", "Quantum computing uses quantum mechanics principles for computation."),
        ("My code isn't working", "There could be several reasons why your code isn't functioning properly."),
        ("What's machine learning?", "Machine learning is a subset of AI that enables computers to learn patterns from data."),
        ("I'm stressed about work", "Work stress can be challenging. It's important to find healthy coping strategies.")
    ]
    
    for user_input, boring_response in test_cases:
        print(f"Input: {user_input}")
        print(f"Boring: {boring_response}")
        
        # Test each enhancement method individually
        print("\nTesting individual methods:")
        print(f"Observational: {penny._add_observational_humor(boring_response, user_input)}")
        print(f"Self-aware: {penny._add_self_aware_commentary(boring_response, user_input)}")
        print(f"Tech roast: {penny._add_tech_industry_roast(boring_response, user_input)}")
        print(f"Tangent: {penny._add_random_tangent(boring_response, user_input)}")
        
        # Test full enhancement
        enhanced = penny.enhance_response(boring_response, user_input)
        print(f"\nFull Enhanced: {enhanced}")
        print("-" * 80)

if __name__ == "__main__":
    test_unpredictable_responses()
