#!/usr/bin/env python3
"""
Phase 0: Pragmatics Core - Skeleton Implementation
Adds conversational context awareness and basic AMA detection to Penny
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
import time
import re


class ConversationRole(Enum):
    """Who is expected to drive the conversation"""
    USER_LEADING = "user_leading"  # User asks, AI answers
    AI_LEADING = "ai_leading"      # AI asks, user answers
    MIXED = "mixed"                # Both participants asking/answering


class ConversationGoal(Enum):
    """Primary purpose of current conversation"""
    TASK_COMPLETION = "task"       # Getting specific help/info
    SOCIAL_BONDING = "bonding"     # Building relationship
    INFORMATION_SHARING = "sharing" # User wants to tell AI about themselves
    EXPLORATION = "exploration"    # Open-ended discussion


class ResponseStrategy(Enum):
    """How AI should respond"""
    ANSWER = "answer"              # Provide information/help
    ASK = "ask"                    # Ask questions to learn about user
    CLARIFY = "clarify"            # Ask for clarification
    REFLECT = "reflect"            # Acknowledge and reflect back
    DEFER = "defer"                # "I don't know, tell me more"


@dataclass
class PragmaticsState:
    """Maintains conversational context and pragmatic understanding"""
    # Role tracking
    current_role: ConversationRole = ConversationRole.USER_LEADING
    role_confidence: float = 0.5
    
    # Goal tracking
    current_goal: ConversationGoal = ConversationGoal.TASK_COMPLETION
    goal_confidence: float = 0.5
    
    # Turn tracking
    turn_count: int = 0
    questions_asked_by_ai: int = 0
    questions_asked_by_user: int = 0
    
    # Memory pointers
    last_user_question: Optional[str] = None
    last_ai_question: Optional[str] = None
    unanswered_questions: List[str] = None
    
    # Timestamps
    last_update: float = 0.0
    conversation_start: float = 0.0
    
    def __post_init__(self):
        if self.unanswered_questions is None:
            self.unanswered_questions = []
        if self.conversation_start == 0.0:
            self.conversation_start = time.time()


class PragmaticsCore:
    """Core pragmatics processing for conversational understanding"""
    
    def __init__(self):
        self.state = PragmaticsState()
        self.enabled = True
        
        # Configuration
        self.role_detection_threshold = 0.65
        self.max_consecutive_ai_questions = 3
        
        # Patterns for role detection
        self.invite_questions_patterns = [
            r'\bask me (anything|something|questions?)\b',
            r'\byou ask\b',
            r'\binterview me\b',
            r'\bquestion me\b',
            r'\bwhat (do|would) you (like to|want to|wanna) know\b',
            r'\bwhat would you ask\b',
            r'\btell me what you.*want to know\b'
        ]
        
        self.request_to_ask_patterns = [
            r'\b(can|may|could) I ask (you|something)\b',
            r'\bmind if I ask\b',
            r'\blet me ask you\b',
            r'\bI (want to|wanna|would like to) ask\b',
            r'\bI have a question\b'
        ]
    
    def detect_role_reversal(self, user_input: str) -> Tuple[bool, float, str]:
        """
        Detect if user is inviting AI to ask questions vs requesting to ask questions
        Returns: (role_reversal_detected, confidence, detected_pattern)
        """
        user_lower = user_input.lower().strip()
        
        # Check for invite patterns (user wants AI to ask)
        for pattern in self.invite_questions_patterns:
            if re.search(pattern, user_lower):
                return True, 0.9, f"invite_pattern: {pattern}"
        
        # Check for request patterns (user wants to ask AI)
        for pattern in self.request_to_ask_patterns:
            if re.search(pattern, user_lower):
                return False, 0.9, f"request_pattern: {pattern}"
        
        # Additional heuristics
        if "ask me" in user_lower and "can I" not in user_lower:
            return True, 0.7, "ask_me_heuristic"
        
        if user_lower.endswith("?") and len(user_lower.split()) < 6:
            # Short questions typically mean user is asking AI
            return False, 0.6, "short_question"
        
        return False, 0.3, "no_clear_pattern"
    
    def update_conversation_state(self, user_input: str, ai_response: str, 
                                context: Dict[str, Any] = None) -> ResponseStrategy:
        """
        Update pragmatic state and determine response strategy
        """
        if not self.enabled:
            return ResponseStrategy.ANSWER
        
        context = context or {}
        
        # Update turn tracking
        self.state.turn_count += 1
        self.state.last_update = time.time()
        
        # Detect role reversal
        role_reversal, confidence, pattern = self.detect_role_reversal(user_input)
        
        if role_reversal and confidence > self.role_detection_threshold:
            # User wants AI to ask questions
            self.state.current_role = ConversationRole.AI_LEADING
            self.state.role_confidence = confidence
            self.state.current_goal = ConversationGoal.INFORMATION_SHARING
            
            return ResponseStrategy.ASK
        
        # Check if user asked a question
        if user_input.strip().endswith('?'):
            self.state.questions_asked_by_user += 1
            self.state.last_user_question = user_input
            self.state.current_role = ConversationRole.USER_LEADING
            
            return ResponseStrategy.ANSWER
        
        # Default behavior
        self.state.current_role = ConversationRole.USER_LEADING
        return ResponseStrategy.ANSWER
    
    def generate_questions_for_user(self, context: Dict[str, Any] = None) -> List[str]:
        """
        Generate appropriate questions when AI should take initiative
        """
        context = context or {}
        
        # Get topic-specific questions
        topic = context.get('topic', 'general')
        participants = context.get('participants', [])
        
        questions = []
        
        if topic == 'programming' or 'code' in context.get('user_input', '').lower():
            questions = [
                "What's the most interesting project you're working on right now?",
                "What programming language or framework are you most excited about lately?",
                "Have you run into any particularly tricky bugs recently?"
            ]
        elif 'josh' in participants or 'brochacho' in participants:
            questions = [
                "How's the latest project with Josh going?",
                "What's Josh been working on that's got you excited?",
                "Any new tech adventures you and Josh are planning?"
            ]
        elif 'reneille' in participants:
            questions = [
                "How are things going with Reneille's projects?",
                "What's Reneille organizing that you're involved in?",
                "Any interesting collaborations with Reneille lately?"
            ]
        else:
            # General questions
            questions = [
                "What's been the highlight of your day so far?",
                "What's something you've learned recently that surprised you?",
                "Is there a project or idea you're excited about right now?"
            ]
        
        # Limit to avoid overwhelming
        return questions[:2]
    
    def get_pragmatic_response_strategy(self, user_input: str, base_response: str,
                                      context: Dict[str, Any] = None) -> Tuple[str, ResponseStrategy]:
        """
        Apply pragmatic understanding to modify response
        """
        if not self.enabled:
            return base_response, ResponseStrategy.ANSWER
        
        # Update state and get strategy
        strategy = self.update_conversation_state(user_input, base_response, context)
        
        if strategy == ResponseStrategy.ASK:
            # User invited questions - generate appropriate questions
            questions = self.generate_questions_for_user(context)
            
            if questions:
                # Acknowledge the invitation and ask questions
                response = f"You want me to ask YOU something? I like it! "
                response += questions[0]
                
                if len(questions) > 1:
                    response += f" And {questions[1].lower()}"
                
                return response, strategy
            else:
                # Fallback if no questions generated
                return "You want me to ask you something? Tell me about what you're working on!", strategy
        
        elif strategy == ResponseStrategy.ANSWER:
            # Normal response - just return the base response
            return base_response, strategy
        
        return base_response, strategy
    
    def get_state_info(self) -> Dict[str, Any]:
        """Get current pragmatic state for debugging/monitoring"""
        return {
            'enabled': self.enabled,
            'current_role': self.state.current_role.value,
            'current_goal': self.state.current_goal.value,
            'role_confidence': self.state.role_confidence,
            'turn_count': self.state.turn_count,
            'questions_by_ai': self.state.questions_asked_by_ai,
            'questions_by_user': self.state.questions_asked_by_user
        }
    
    def reset_state(self):
        """Reset pragmatic state for new conversation"""
        self.state = PragmaticsState()


def create_pragmatics_core():
    """Factory function for creating pragmatics core"""
    return PragmaticsCore()


if __name__ == "__main__":
    print("Testing Pragmatics Core - Phase 0")
    print("=" * 40)
    
    pragmatics = create_pragmatics_core()
    
    # Test cases for the specific "ask me anything" problem
    test_cases = [
        {
            'input': "Ask me anything.",
            'context': {'topic': 'conversation'},
            'expected': 'AI should ask questions'
        },
        {
            'input': "Ask me something about my projects.",
            'context': {'topic': 'programming'},
            'expected': 'AI should ask about projects'
        },
        {
            'input': "Can I ask you something?",
            'context': {'topic': 'conversation'},
            'expected': 'User wants to ask AI'
        },
        {
            'input': "What do you think about microservices?",
            'context': {'topic': 'architecture'},
            'expected': 'Answer the question'
        },
        {
            'input': "You ask me about Josh's project.",
            'context': {'participants': ['josh'], 'topic': 'programming'},
            'expected': 'AI should ask about Josh'
        }
    ]
    
    for i, case in enumerate(test_cases, 1):
        print(f"\nTest {i}: {case['input']}")
        print(f"Expected: {case['expected']}")
        
        # Test role detection
        role_reversal, confidence, pattern = pragmatics.detect_role_reversal(case['input'])
        print(f"Role reversal detected: {role_reversal} (confidence: {confidence:.2f}, pattern: {pattern})")
        
        # Test full response strategy
        base_response = "I'd be happy to help with that."
        enhanced_response, strategy = pragmatics.get_pragmatic_response_strategy(
            case['input'], base_response, case['context']
        )
        
        print(f"Strategy: {strategy.value}")
        print(f"Enhanced response: {enhanced_response}")
        
        # Show state
        state_info = pragmatics.get_state_info()
        print(f"Current role: {state_info['current_role']}")
    
    print(f"\nPragmatics Core Phase 0 ready!")
    print("Key features implemented:")
    print("- Role reversal detection for 'ask me anything' scenarios")
    print("- Context-aware question generation")
    print("- Conversational state tracking")
    print("- Integration-ready response strategy system")
