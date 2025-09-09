#!/usr/bin/env python3
"""
Penny Humor Integration
Connects the enhanced humor system to existing Penny personality
"""

import sys
import os
import time
import random
from typing import Dict, List, Optional, Any

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from enhanced_humor_system import EnhancedHumorSystem, HumorOpportunity, HumorType


class PennyWithEnhancedHumor:
    """Penny's personality enhanced with contextual humor system."""
    
    def __init__(self, cj_learning_system=None):
        self.humor_system = EnhancedHumorSystem()
        self.cj_learning = cj_learning_system
        self.conversation_history = []
        
        # Penny-specific humor additions
        self.penny_specific_humor = {
            'josh_jokes': [
                "Brochacho! That nickname never gets old. Did you come up with that in a Verizon break room?",
                "Josh going from Verizon to Google - that's like upgrading from a flip phone to an iPhone.",
                "I bet Google's cafeteria is slightly better than Verizon's vending machines.",
                "From telecom to tech giant - someone's moving up in the world!"
            ],
            'reneille_jokes': [
                "I bet Reneille has her wedding planned with the precision of a Google algorithm.",
                "Wedding planning and working at Google? That's some serious multitasking skills.",
                "I'm impressed anyone can stay organized while planning a wedding AND working in tech.",
                "Let me guess - the wedding planning spreadsheet has more tabs than Chrome?"
            ],
            'cj_roasts': [
                "CJ, you're asking an AI for life advice. I mean, I'm flattered, but maybe call your mom?",
                "Another day, another FastAPI question. I should start charging consulting fees.",
                "You've built an AI with attitude problems. I'm not sure if that's brilliant or concerning.",
                "Here you are, debugging code by talking to a computer program with sass. Peak 2025 energy."
            ],
            'coding_reality': [
                "The code works perfectly... until you show it to someone else. Then it dies of stage fright.",
                "Programming: the art of convincing yourself that copy-pasting from Stack Overflow is 'research.'",
                "That moment when you fix a bug and three new ones appear. It's like coding whack-a-mole.",
                "Git commit messages: where 'fix stuff' is considered detailed documentation."
            ]
        }
        
        # Context-aware response modifiers
        self.context_modifiers = {
            'stress_detected': [
                "before we dive into solutions",
                "but first, take a breath",
                "after you've had some coffee"
            ],
            'excitement_detected': [
                "I love the enthusiasm, but",
                "easy there, tiger",
                "slow down, speed racer"
            ],
            'confusion_detected': [
                "let me break this down",
                "in simple terms",
                "without the tech jargon"
            ]
        }
    
    def generate_enhanced_response(self, user_input: str, base_response: str, 
                                 context: Dict[str, Any] = None) -> str:
        """Generate response with enhanced humor integration."""
        context = context or {}
        
        # Detect humor opportunities
        humor_opportunities = self.humor_system.detect_humor_opportunities(
            user_input, 
            str(context), 
            self.conversation_history
        )
        
        # Add Penny-specific humor opportunities
        penny_opportunities = self._detect_penny_specific_humor(user_input, context)
        humor_opportunities.extend(penny_opportunities)
        
        # Apply humor to base response
        if humor_opportunities:
            enhanced_response = self.humor_system.generate_humorous_response(
                base_response, humor_opportunities
            )
        else:
            enhanced_response = base_response
        
        # Add contextual personality modifications
        enhanced_response = self._apply_context_modifications(
            enhanced_response, user_input, context
        )
        
        # Store for conversation history
        self.conversation_history.append(user_input)
        if len(self.conversation_history) > 20:
            self.conversation_history = self.conversation_history[-20:]
        
        # Update humor system timing
        self.humor_system.update_timing()
        
        return enhanced_response
    
    def _detect_penny_specific_humor(self, user_input: str, context: Dict[str, Any]) -> List[HumorOpportunity]:
        """Detect Penny-specific humor opportunities."""
        opportunities = []
        user_lower = user_input.lower()
        
        # Josh/Brochacho detection
        if any(name in user_lower for name in ['josh', 'brochacho']):
            joke = random.choice(self.penny_specific_humor['josh_jokes'])
            opportunities.append(HumorOpportunity(
                humor_type=HumorType.CALLBACK,
                context="Josh interaction",
                setup=user_input,
                punchline=joke,
                confidence=0.8
            ))
        
        # Reneille detection
        if 'reneille' in user_lower:
            joke = random.choice(self.penny_specific_humor['reneille_jokes'])
            opportunities.append(HumorOpportunity(
                humor_type=HumorType.CALLBACK,
                context="Reneille interaction",
                setup=user_input,
                punchline=joke,
                confidence=0.8
            ))
        
        # CJ self-roasting opportunities
        cj_triggers = ['help me', 'what should i', 'advice', 'opinion']
        if any(trigger in user_lower for trigger in cj_triggers):
            if random.random() < 0.3:  # 30% chance for self-roast
                joke = random.choice(self.penny_specific_humor['cj_roasts'])
                opportunities.append(HumorOpportunity(
                    humor_type=HumorType.SELF_AWARE,
                    context="CJ roasting",
                    setup=user_input,
                    punchline=joke,
                    confidence=0.6
                ))
        
        # Coding reality checks
        coding_words = ['code', 'bug', 'debug', 'programming', 'development']
        if any(word in user_lower for word in coding_words):
            if random.random() < 0.4:  # 40% chance for coding humor
                joke = random.choice(self.penny_specific_humor['coding_reality'])
                opportunities.append(HumorOpportunity(
                    humor_type=HumorType.OBSERVATIONAL,
                    context="coding reality",
                    setup=user_input,
                    punchline=joke,
                    confidence=0.7
                ))
        
        return opportunities
    
    def _apply_context_modifications(self, response: str, user_input: str, 
                                   context: Dict[str, Any]) -> str:
        """Apply contextual modifications to response."""
        user_lower = user_input.lower()
        
        # Detect emotional context and modify accordingly
        if any(word in user_lower for word in ['stressed', 'frustrated', 'annoyed', 'angry']):
            modifier = random.choice(self.context_modifiers['stress_detected'])
            response = f"Okay, {modifier} - {response.lower()}"
        
        elif any(word in user_lower for word in ['excited', 'amazing', 'awesome', 'love']):
            modifier = random.choice(self.context_modifiers['excitement_detected'])
            response = f"{modifier.capitalize()}, {response.lower()}"
        
        elif any(word in user_lower for word in ['confused', 'lost', 'understand', 'explain']):
            modifier = random.choice(self.context_modifiers['confusion_detected'])
            response = f"Alright, {modifier}: {response.lower()}"
        
        return response
    
    def get_humor_stats(self) -> Dict[str, Any]:
        """Get humor system statistics."""
        return {
            'conversation_turns': len(self.conversation_history),
            'total_responses': self.humor_system.response_count,
            'callbacks_stored': len(self.humor_system.conversation_callbacks),
            'inside_jokes': len(self.humor_system.inside_jokes)
        }


def create_penny_with_enhanced_humor(cj_learning_system=None):
    """Factory function to create Penny with enhanced humor."""
    return PennyWithEnhancedHumor(cj_learning_system)


if __name__ == "__main__":
    print("🎭 Testing Penny with Enhanced Humor")
    print("=" * 50)
    
    penny_humor = PennyWithEnhancedHumor()
    
    test_scenarios = [
        {
            'input': "Hey Josh, what do you think about this code?",
            'base_response': "I think Josh would appreciate the clean structure.",
            'context': {'participants': ['josh']}
        },
        {
            'input': "Reneille, how do you organize your projects?",
            'base_response': "Here are some project organization tips.",
            'context': {'participants': ['reneille']}
        },
        {
            'input': "I'm debugging this frustrating piece of code",
            'base_response': "Let's look at debugging strategies.",
            'context': {'emotion': 'frustrated', 'topic': 'debugging'}
        },
        {
            'input': "Which JavaScript framework should I use?",
            'base_response': "React is a solid choice for most projects.",
            'context': {'topic': 'frameworks'}
        },
        {
            'input': "Help me understand microservices",
            'base_response': "Microservices architecture breaks applications into smaller services.",
            'context': {'topic': 'architecture', 'emotion': 'confused'}
        }
    ]
    
    for i, scenario in enumerate(test_scenarios, 1):
        print(f"\n--- Test {i} ---")
        print(f"📝 Input: '{scenario['input']}'")
        print(f"🤖 Base: '{scenario['base_response']}'")
        print(f"🎯 Context: {scenario['context']}")
        
        enhanced = penny_humor.generate_enhanced_response(
            scenario['input'],
            scenario['base_response'],
            scenario['context']
        )
        
        print(f"😂 Enhanced: '{enhanced}'")
        print(f"📊 Stats: {penny_humor.get_humor_stats()}")
    
    print("\n✅ Penny Enhanced Humor test complete!")
    print("🎭 Ready to integrate with existing personality system!")
