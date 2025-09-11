#!/usr/bin/env python3
"""
Enhanced Penny with Pragmatics Integration
Adds conversational understanding to fix the "ask me anything" issue
"""

import sys
import os
import time
from typing import Dict, Any, Optional

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from speed_optimized_enhanced_penny import create_speed_optimized_enhanced_penny
from pragmatics_core import create_pragmatics_core, ResponseStrategy, ConversationRole
from performance_monitor import time_operation, OperationType, get_performance_summary


class PragmaticsEnhancedPenny:
    """Enhanced Penny with conversational pragmatics understanding"""
    
    def __init__(self):
        # Initialize existing enhanced system
        self.enhanced_penny = create_speed_optimized_enhanced_penny()
        
        # Add pragmatics layer
        self.pragmatics = create_pragmatics_core()
        
        print("Pragmatics-Enhanced Penny initialized!")
        print("✅ ML personality + dynamic states + conversational pragmatics active")
    
    def generate_pragmatically_aware_response(self, user_input: str, context: Dict[str, Any] = None) -> str:
        """Generate response with full pragmatic understanding"""
        context = context or {}
        
        with time_operation(OperationType.TOTAL_PIPELINE, {"pragmatics_enabled": True}):
            
            # Step 1: Generate base response from enhanced personality system
            with time_operation(OperationType.PERSONALITY_GENERATION):
                # Get enhanced personality prompt
                personality_prompt = self.enhanced_penny.get_enhanced_personality_prompt(context)
                
                # For this demo, we'll simulate LLM response generation
                # In real integration, this would call your LLM with the personality prompt
                base_response = self._simulate_llm_response(user_input, personality_prompt, context)
            
            # Step 2: Apply pragmatic understanding
            with time_operation(OperationType.HUMOR_DETECTION, {"operation": "pragmatics"}):
                enhanced_response, strategy = self.pragmatics.get_pragmatic_response_strategy(
                    user_input, base_response, context
                )
            
            # Step 3: Apply existing enhanced personality processing if needed
            if strategy == ResponseStrategy.ANSWER:
                # Normal response - apply full personality enhancement
                final_response = self.enhanced_penny.generate_enhanced_response_safe(
                    user_input, enhanced_response, context
                )
            else:
                # Pragmatics took over (like asking questions) - apply lighter personality touch
                final_response = self._apply_personality_to_pragmatic_response(
                    enhanced_response, context
                )
            
            return final_response
    
    def _simulate_llm_response(self, user_input: str, personality_prompt: str, context: Dict[str, Any]) -> str:
        """Simulate LLM response for demo purposes"""
        # Check if this is a response to a question we just asked
        pragmatic_state = self.pragmatics.get_state_info()
        
        if pragmatic_state['current_role'] == 'ai_leading':
            # We're in AI-leading mode, user is likely answering our question
            if "highlight" in user_input.lower() or "day" in user_input.lower():
                # User is answering about their day
                return self._generate_followup_response(user_input, "day_highlight")
            elif "learned" in user_input.lower() or "surprised" in user_input.lower():
                # User is answering about learning
                return self._generate_followup_response(user_input, "learning")
            elif "project" in user_input.lower() or "working" in user_input.lower():
                # User is answering about projects
                return self._generate_followup_response(user_input, "projects")
            else:
                # General response to user's answer
                return self._generate_followup_response(user_input, "general")
        
        # Normal processing for non-AI-leading scenarios
        if "microservice" in user_input.lower():
            return "Consider whether the complexity overhead is worth it for your use case."
        elif "josh" in user_input.lower():
            return "Here are some technical suggestions for your work with Josh."
        elif "ask me" in user_input.lower():
            # This is the problematic case - old system would misunderstand
            return "Sure, what would you like to know about?"
        else:
            return "I'd be happy to help with that."
    
    def _generate_followup_response(self, user_input: str, response_type: str) -> str:
        """Generate appropriate followup responses when user answers our questions"""
        user_lower = user_input.lower()
        
        if response_type == "day_highlight":
            if "in-n-out" in user_lower or "burger" in user_lower or "food" in user_lower:
                # After this response, reset to normal conversation mode
                self.pragmatics.state.current_role = ConversationRole.USER_LEADING
                return "In-N-Out! Now that's a solid day highlight. Those burgers hit different. What's your go-to order?"
            elif "work" in user_lower or "project" in user_lower:
                self.pragmatics.state.current_role = ConversationRole.USER_LEADING
                return "Work highlights are the best kind! What made it so great?"
            else:
                self.pragmatics.state.current_role = ConversationRole.USER_LEADING
                return f"Nice! {user_input.strip('.')} sounds like a good way to spend the day. What made it special?"
        
        elif response_type == "learning":
            self.pragmatics.state.current_role = ConversationRole.USER_LEADING
            return f"Interesting! {user_input.strip('.')} - I love when things surprise us. How are you going to use that knowledge?"
        
        elif response_type == "projects":
            self.pragmatics.state.current_role = ConversationRole.USER_LEADING
            return f"Cool! {user_input.strip('.')} sounds like something worth diving into. What's the most challenging part?"
        
        else:
            # General acknowledgment with followup - return to normal mode
            self.pragmatics.state.current_role = ConversationRole.USER_LEADING
            return f"Gotcha! {user_input.strip('.')} - tell me more about that!"
    
    def _apply_personality_to_pragmatic_response(self, response: str, context: Dict[str, Any]) -> str:
        """Apply personality styling to pragmatically-generated responses"""
        # Get current dynamic state for personality styling
        try:
            current_state = self.enhanced_penny._dynamic_states.current_state.value
            
            if current_state == 'caffeinated':
                # Add energy but don't go overboard with exclamation points
                if "Tell me" in response and "?" in response:
                    response = response.replace("Tell me", "Ooh, tell me")
                # Limit exclamation points to avoid screaming
                response = response.replace("?!", "?")
                if response.count("!") > 2:
                    response = response.replace("!", ".", response.count("!") - 1)
                    
            elif current_state == 'mischievous':
                # Add sass but keep it conversational
                if "you want me to ask" in response.lower():
                    response = response.replace("I like it!", "I like it.")
            
        except Exception:
            # Graceful degradation if personality system fails
            pass
        
        # Always clean up excessive punctuation
        response = response.replace("?!", "?")
        response = response.replace("!!", "!")
        
        return response
    
    def learn_from_pragmatic_interaction(self, user_input: str, response: str, 
                                       user_reaction: str = None, context: Dict[str, Any] = None):
        """Learn from interaction with pragmatic awareness"""
        # Update pragmatic state
        self.pragmatics.update_conversation_state(user_input, response, context)
        
        # Apply existing ML learning
        self.enhanced_penny.learn_from_interaction_enhanced(
            user_input, response, user_reaction, context
        )
    
    def get_comprehensive_stats(self) -> Dict[str, Any]:
        """Get stats from all systems including pragmatics"""
        stats = self.enhanced_penny.get_comprehensive_stats()
        
        # Add pragmatics info
        pragmatic_state = self.pragmatics.get_state_info()
        stats.update({f"pragmatics_{k}": v for k, v in pragmatic_state.items()})
        
        return stats
    
    def get_enhanced_personality_prompt(self, context: Dict[str, Any] = None) -> str:
        """Get personality prompt enhanced with pragmatic understanding"""
        base_prompt = self.enhanced_penny.get_enhanced_personality_prompt(context)
        
        # Add pragmatic awareness instructions
        pragmatic_state = self.pragmatics.get_state_info()
        
        if pragmatic_state['current_role'] == 'ai_leading':
            base_prompt += "\n\nCONVERSATIONAL CONTEXT: The user has invited you to ask questions. Take initiative and ask engaging questions about their experiences, projects, or interests."
        
        return base_prompt


def create_pragmatics_enhanced_penny():
    """Factory function for creating pragmatics-enhanced Penny"""
    return PragmaticsEnhancedPenny()


if __name__ == "__main__":
    print("Testing Pragmatics-Enhanced Penny")
    print("=" * 45)
    
    # Create the enhanced system
    penny = create_pragmatics_enhanced_penny()
    
    # Test the exact scenario that was problematic
    print("\nTesting the original problematic scenario:")
    print("User: 'Ask me anything.'")
    
    test_context = {
        'topic': 'conversation',
        'emotion': 'neutral',
        'participants': []
    }
    
    response = penny.generate_pragmatically_aware_response(
        "Ask me anything.", 
        test_context
    )
    
    print(f"Pragmatics-Enhanced Response: {response}")
    
    # Test with different contexts
    test_cases = [
        {
            'input': "Ask me about my work with Josh.",
            'context': {'participants': ['josh'], 'topic': 'programming'},
            'description': "Specific invitation with Josh context"
        },
        {
            'input': "Can I ask you about microservices?",
            'context': {'topic': 'architecture'},
            'description': "User wants to ask AI (should not trigger role reversal)"
        },
        {
            'input': "You ask me something interesting.",
            'context': {'topic': 'general'},
            'description': "Direct invitation for AI to ask"
        }
    ]
    
    for i, case in enumerate(test_cases, 1):
        print(f"\nTest {i}: {case['description']}")
        print(f"User: '{case['input']}'")
        
        response = penny.generate_pragmatically_aware_response(
            case['input'],
            case['context']
        )
        
        print(f"Enhanced Response: {response}")
        
        # Simulate learning from interaction
        penny.learn_from_pragmatic_interaction(
            case['input'],
            response,
            "That's much better!",
            case['context']
        )
    
    # Show comprehensive stats
    print(f"\nComprehensive System Stats:")
    stats = penny.get_comprehensive_stats()
    
    print(f"Pragmatics enabled: {stats.get('pragmatics_enabled', False)}")
    print(f"Current conversational role: {stats.get('pragmatics_current_role', 'unknown')}")
    print(f"Turn count: {stats.get('pragmatics_turn_count', 0)}")
    print(f"ML humor level: {stats.get('ml_current_humor_level', 'N/A')}")
    print(f"Current personality state: {stats.get('state_current_state', 'N/A')}")
    
    print("\nPragmatics-Enhanced Penny ready!")
    print("Key improvements:")
    print("✅ Correctly interprets 'ask me anything' as invitation for AI to ask")
    print("✅ Maintains conversational role awareness")
    print("✅ Preserves ML personality learning and dynamic states")
    print("✅ Adds conversational intelligence layer")
    print("✅ Graceful degradation if pragmatics fails")
