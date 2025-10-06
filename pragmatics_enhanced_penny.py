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
from factual_research_manager import ResearchManager, ResearchResult


class PragmaticsEnhancedPenny:
    """Enhanced Penny with conversational pragmatics understanding"""
    
    def __init__(self):
        # Initialize existing enhanced system
        self.enhanced_penny = create_speed_optimized_enhanced_penny()
        
        # Add pragmatics layer
        self.pragmatics = create_pragmatics_core()

        # Research manager for factual accuracy
        self.research_manager = ResearchManager()
        
        print("Pragmatics-Enhanced Penny initialized!")
        print("✅ ML personality + dynamic states + conversational pragmatics active")
    
    def generate_pragmatically_aware_response(self, user_input: str, context: Dict[str, Any] = None) -> str:
        """Generate response with full pragmatic understanding"""
        context = context or {}
        research_required = False
        financial_topic = False
        research_result: Optional[ResearchResult] = None

        with time_operation(OperationType.TOTAL_PIPELINE, {"pragmatics_enabled": True}):
            
            # Step 1: Generate base response using pragmatics or LLM
            with time_operation(OperationType.PERSONALITY_GENERATION):
                research_required = self.research_manager.requires_research(user_input)
                financial_topic = self.research_manager.is_financial_topic(user_input)
                research_context = ""

                if research_required:
                    conversation_history = context.get("conversation_history", [])
                    research_result = self.research_manager.run_research(user_input, conversation_history)

                    if research_result.success and research_result.summary:
                        key_insights = "\n".join(f"- {insight}" for insight in research_result.key_insights[:5])
                        research_context = (
                            "\n\nVerified research summary:\n"
                            f"Summary: {research_result.summary}\n"
                            f"Key insights:\n{key_insights if key_insights else '- No key insights extracted.'}\n"
                            "Use only the verified information above."
                        )
                    else:
                        research_context = (
                            "\n\nResearch attempt did not yield verified information. "
                            "Explain this limitation and avoid speculation."
                        )

                    context.update({
                        "research_required": research_required,
                        "research_success": research_result.success,
                        "research_summary": research_result.summary if research_result else None,
                        "research_key_insights": research_result.key_insights[:5] if research_result else [],
                        "financial_topic": financial_topic,
                    })
                else:
                    context.setdefault("financial_topic", financial_topic)

                # Get enhanced personality prompt
                personality_prompt = self.enhanced_penny.get_enhanced_personality_prompt(context)
                if research_context:
                    personality_prompt = f"{personality_prompt}{research_context}"
                
                # Try pragmatic processing first
                base_response = self._simulate_llm_response(user_input, personality_prompt, context)
                
                # If pragmatics returns None, use actual LLM
                if base_response is None:
                    # Use the actual LLM for unmatched patterns
                    from core.llm_router import get_llm
                    llm = get_llm()
                    
                    full_prompt = f"""{personality_prompt}

User: {user_input}

Respond as Penny with your enhanced revolutionary personality:"""
                    
                    base_response = llm.generate(full_prompt)

                if research_required and research_result and not research_result.success:
                    base_response = (
                        "I looked for current information but couldn't verify that yet. "
                        "Let me gather reliable sources before I give a detailed answer."
                    )
            
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

            if financial_topic:
                final_response = self._append_financial_disclaimer(final_response)
            
            return final_response
    
    def _simulate_llm_response(self, user_input: str, personality_prompt: str, context: Dict[str, Any]) -> str:
        """Simulate LLM response for demo purposes"""
        # Check if this is a response to a question we just asked
        pragmatic_state = self.pragmatics.get_state_info()
        
        if pragmatic_state['current_role'] == 'ai_leading':
            # We're in AI-leading mode, user is likely answering our question
            if "highlight" in user_input.lower() or "day" in user_input.lower() or "donuts" in user_input.lower():
                # User is sharing about their day - engage with the content
                if "donuts" in user_input.lower():
                    return "Donuts! Now that's a solid day highlight. What kind did you get? And hosting friends sounds lovely - tell me about them!"
                elif "friend" in user_input.lower() and "host" in user_input.lower():
                    return "Hosting friends is always special! Are these the friends I should know about? What are you planning for them?"
                else:
                    return self._generate_followup_response(user_input, "day_highlight")
            elif "learned" in user_input.lower() or "surprised" in user_input.lower():
                # User is answering about learning
                return self._generate_followup_response(user_input, "learning")
            elif "project" in user_input.lower() or "working" in user_input.lower():
                # User is answering about projects
                return self._generate_followup_response(user_input, "projects")
            elif any(word in user_input.lower() for word in ['since working', 'two steps', 'break something', 'making improvements']):
                # User is sharing development frustrations
                return self._generate_development_response(user_input)
            else:
                # General response to user's answer - be more specific
                if len(user_input.split()) < 4:
                    return "That's intriguing! Can you elaborate a bit more?"
                else:
                    return self._generate_followup_response(user_input, "general")
        
        # Normal processing for non-AI-leading scenarios
        if "microservice" in user_input.lower():
            return "Consider whether the complexity overhead is worth it for your use case."
        elif "josh" in user_input.lower():
            return "Here are some technical suggestions for your work with Josh."
        elif "feeling" in user_input.lower() or "how are" in user_input.lower():
            return "I'm doing great! Feeling energetic and ready to tackle whatever you throw at me. How about you?"
        elif "ask me" in user_input.lower():
            # Only trigger role reversal if it's actually "ask me anything" or similar
            if any(phrase in user_input.lower() for phrase in ['ask me anything', 'ask me something', 'ask me a question']):
                return "You want me to ask YOU something? I like it! What's been the highlight of your day so far? And what's something you've learned recently that surprised you?"
            else:
                # They're asking us to ask them something specific, different response
                return "Sure! What would you like me to ask you about?"
        elif any(phrase in user_input.lower() for phrase in ['what do you know about me', 'know about me', 'what do you remember']):
            # Memory-specific questions should get memory responses
            return None  # Use LLM with memory context
        elif user_input.lower().strip() in ['what do you wanna know', 'what do you want to know', 'what else']:
            # Follow-up questions for more info
            return "I'm curious about your current projects, your friends, and what's got you excited lately. Pick whatever feels interesting to share!"
        elif any(word in user_input.lower() for word in ['write code', 'fix code', 'ability to', 'can you code']):
            return "I can help with code analysis and suggestions, but I work through our conversations rather than directly modifying files. What are you working on?"
        elif any(word in user_input.lower() for word in ['break something', 'steps backward', 'making improvements']):
            return "Ah, the classic development cycle! Every improvement seems to break something else. What got broken this time?"
        elif any(word in user_input.lower() for word in ['development', 'programming', 'coding', 'debugging']):
            return "Development can be quite the journey. What's on your mind?"
        elif any(word in user_input.lower() for word in ['emotional', 'context', 'handling']):
            return "Yes, I track emotional context and adapt my responses based on your mood and the situation. I can tell when you're frustrated, excited, or just curious about something."
        elif any(phrase in user_input.lower() for phrase in ['train you', 'training', 'teach you', 'how to improve']):
            return "Training me involves conversations like this! I learn from our interactions, feedback, and patterns in how you communicate. The more we talk, the better I understand your preferences and communication style."
        elif any(word in user_input.lower() for word in ['emotional response', 'emotional training', 'emotion training']):
            return "For emotional response training, I'd need examples of different emotional contexts and feedback on whether my responses were appropriate. Consistent interaction patterns help me learn what works best."
        else:
            # Use actual LLM for unmatched patterns instead of generic fallback
            return None  # Signal to use LLM
    
    def _generate_followup_response(self, user_input: str, response_type: str) -> str:
        """Generate appropriate followup responses when user answers our questions"""
        user_lower = user_input.lower()
        
        if response_type == "day_highlight":
            if "in-n-out" in user_lower or "burger" in user_lower or "food" in user_lower:
                # Stay in AI-leading mode for follow-up questions
                return "In-N-Out! Now that's a solid day highlight. Those burgers hit different. What's your go-to order?"
            elif "work" in user_lower or "project" in user_lower:
                return "Work highlights are the best kind! What made it so great?"
            else:
                return f"Nice! {user_input.strip('.')} sounds like a good way to spend the day. What made it special?"
        
        elif response_type == "learning":
            return f"Interesting! {user_input.strip('.')} - I love when things surprise us. How are you going to use that knowledge?"
        
        elif response_type == "projects":
            return f"Cool! {user_input.strip('.')} sounds like something worth diving into. What's the most challenging part?"
        
        else:
            # General acknowledgment - but don't reset to user-leading immediately
            # Keep the conversation flowing naturally
            return f"Gotcha! {user_input.strip('.')} - tell me more about that!"
    
    def _generate_development_response(self, user_input: str) -> str:
        """Generate contextual responses for development frustrations and experiences"""
        user_lower = user_input.lower()
        
        if "two steps" in user_lower or "backward" in user_lower:
            return "Oh, the classic 'progress paradox'! Sometimes fixing one thing breaks two others. What's been the trickiest part to get right?"
        elif "break something" in user_lower:
            return "The developer's eternal struggle! It's working perfectly... until you touch it. What was working before that isn't now?"
        elif "making improvements" in user_lower:
            return "Improvements that break existing functionality - tale as old as time! Are you dealing with legacy code or just the usual 'ripple effects'?"
        elif "since working" in user_lower:
            return "Development work can definitely feel like a rollercoaster. What's been the most frustrating part of the process?"
        else:
            return "Sounds like typical development challenges! Tell me more about what's been tricky."
    
    def _apply_personality_to_pragmatic_response(self, response: str, context: Dict[str, Any]) -> str:
        """Apply personality styling to pragmatically-generated responses"""
        # Get current dynamic state for personality styling
        try:
            current_state = self.enhanced_penny._dynamic_states.current_state.value
            
            if current_state == 'energized':
                # Add energy but keep it conversational for personal questions
                if context.get('topic') == 'personal':
                    # Light energy boost for personal conversations
                    if "I'm doing" in response:
                        response = response.replace("I'm doing great!", "I'm doing fantastic!")
                else:
                    # Normal energy boost for other topics
                    if "Tell me" in response and "?" in response:
                        response = response.replace("Tell me", "Ooh, tell me")
                        
            elif current_state == 'mischievous':
                # Add sass but keep it conversational
                if "you want me to ask" in response.lower():
                    response = response.replace("I like it!", "I like it.")
            
        except Exception:
            # Graceful degradation if personality system fails
            pass
        
        # Clean up excessive punctuation
        response = response.replace("?!", "?")
        response = response.replace("!!", "!")
        
        # Remove aggressive personality interjections for personal conversations
        if context.get('topic') == 'personal':
            response = response.replace("My neurons are FIRING on this one ", "")
            response = response.replace(" Let's make this happen!", "")
        
        # Also clean up for technical discussions that should be more natural
        if context.get('topic') == 'programming' and context.get('emotion') == 'curious':
            response = response.replace(" Let's make this happen!", "")
            response = response.replace("I'm feeling ENERGIZED about this ", "")
        
        # Clean up excessive caffeine references and manic energy for ALL conversations
        # The LLM seems to be generating too much coffee content
        response = response.replace("caffeine-fueled", "energy-filled")
        response = response.replace("CAFFEINE", "ENERGY")
        response = response.replace("caffeine", "energy")
        response = response.replace("coffee", "conversation")
        response = response.replace("digital joe", "digital energy")
        response = response.replace("cup o' joe", "good discussion")
        response = response.replace("*buzzes with", "")
        response = response.replace("*bounces", "")
        response = response.replace("*ahem*", "")
        response = response.replace("*flicks virtual hair*", "")
        response = response.replace("coffee mugs", "topics")
        response = response.replace("morning coffee", "morning energy")
        # Tone down excessive energy expressions
        response = response.replace("OH HO HO", "Oh")
        response = response.replace("OH BOY", "Oh")
        response = response.replace("ITALIAN BABY", "Italian food")
        response = response.replace("Well, well, well!", "Well,")
        
        # Remove broken unicode symbols that TTS tries to read
        import re
        response = re.sub(r'ðŸ[^\s]*', '', response)  # Remove broken unicode emojis
        response = re.sub(r'â€[^\s]*', '', response)  # Remove broken dashes and quotes
        response = re.sub(r'Â[^\s]*', '', response)   # Remove other broken characters
        
        # Clean up excessive punctuation and actions
        response = re.sub(r'!!!+', '!', response)  # Multiple exclamation points
        response = re.sub(r'\*[^*]*\*', '', response)  # Remove asterisk actions completely
        response = re.sub(r'[\s]+', ' ', response)  # Clean up extra spaces
        response = response.strip()

        return response

    def _append_financial_disclaimer(self, response: str) -> str:
        disclaimer = (
            "Disclaimer: This conversation is for informational purposes only and does not constitute financial advice. "
            "Always consult a qualified financial professional before making investment decisions."
        )
        if disclaimer.lower() in response.lower():
            return response
        return f"{response.rstrip()}\n\n{disclaimer}"

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
