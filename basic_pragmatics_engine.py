#!/usr/bin/env python3
"""
Pragmatics State System - Phase 0
Skeleton implementation with basic conversational context tracking and AMA detection
"""

import time
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
import re


class ConversationRole(Enum):
    """Roles participants can take in conversation"""
    QUESTIONER = "questioner"  # Actively asking questions
    RESPONDER = "responder"    # Primarily answering questions
    COLLABORATOR = "collaborator"  # Mutual exchange
    LISTENER = "listener"      # Passive, encouraging responses


class Initiative(Enum):
    """Who is driving the conversation"""
    USER = "user"
    AI = "ai"
    MIXED = "mixed"


class ConversationGoal(Enum):
    """Primary purpose of current conversation"""
    TASK = "task"              # Getting something done
    BONDING = "bonding"        # Social connection
    LEARNING = "learning"      # Information exchange
    VALIDATION = "validation"  # Seeking approval/support
    EXPLORATION = "exploration" # Open-ended discovery


class RoleSignal(Enum):
    """Signals about role transitions"""
    INVITE_QUESTIONS = "invite_questions"    # "Ask me anything"
    REQUEST_TO_ASK = "request_to_ask"       # "Can I ask you something?"
    YIELD_FLOOR = "yield_floor"             # "What do you think?"
    TAKE_INITIATIVE = "take_initiative"     # "Let me tell you about..."
    NONE = "none"


@dataclass
class PragmaticsState:
    """Complete conversational context state"""
    # Role tracking
    user_role: ConversationRole = ConversationRole.COLLABORATOR
    ai_role: ConversationRole = ConversationRole.COLLABORATOR
    initiative: Initiative = Initiative.MIXED
    
    # Goal and purpose
    current_goal: ConversationGoal = ConversationGoal.LEARNING
    goal_confidence: float = 0.5
    
    # Memory pointers
    turn_count: int = 0
    last_role_switch: Optional[int] = None
    unanswered_questions: List[str] = field(default_factory=list)
    
    # Context
    timestamp: float = field(default_factory=time.time)
    
    def update_turn(self):
        """Increment turn counter and update timestamp"""
        self.turn_count += 1
        self.timestamp = time.time()
    
    def switch_roles(self, new_user_role: ConversationRole, new_ai_role: ConversationRole):
        """Record a role transition"""
        self.user_role = new_user_role
        self.ai_role = new_ai_role
        self.last_role_switch = self.turn_count
        
        # Update initiative based on roles
        if new_ai_role == ConversationRole.QUESTIONER:
            self.initiative = Initiative.AI
        elif new_user_role == ConversationRole.QUESTIONER:
            self.initiative = Initiative.USER
        else:
            self.initiative = Initiative.MIXED


class RoleSignalDetector:
    """Detects conversational role signals and transitions"""
    
    def __init__(self):
        # Patterns for "ask me anything" type invitations
        self.invite_questions_patterns = [
            r'\bask me (anything|something|about)',
            r'\byou ask\b',
            r'\binterview me\b',
            r'\bfire away\b',
            r'\bshoot\b',  # "Shoot!" 
            r'\bgo ahead and ask\b',
            r'\bwhat do you want to know\b',
            r'\bwhat would you like to know\b',
            r'\btell me what you want to know\b'
        ]
        
        # Patterns for "can I ask you" type requests
        self.request_to_ask_patterns = [
            r'\bcan I ask you\b',
            r'\bmay I ask you\b',
            r'\blet me ask you\b',
            r'\bI want to ask you\b',
            r'\bI have a question\b',
            r'\bquestion for you\b'
        ]
        
        # Patterns that yield conversational floor
        self.yield_floor_patterns = [
            r'\bwhat do you think\b',
            r'\byour thoughts\b',
            r'\bwhat about you\b',
            r'\bhow about you\b',
            r'\byour turn\b'
        ]
        
        # Compile patterns for efficiency
        self.invite_regex = re.compile('|'.join(self.invite_questions_patterns), re.IGNORECASE)
        self.request_regex = re.compile('|'.join(self.request_to_ask_patterns), re.IGNORECASE)
        self.yield_regex = re.compile('|'.join(self.yield_floor_patterns), re.IGNORECASE)
    
    def detect_role_signal(self, text: str) -> Tuple[RoleSignal, float]:
        """
        Detect role transition signals in user input
        Returns (signal_type, confidence)
        """
        text = text.strip()
        
        # Check for invitation to ask questions
        if self.invite_regex.search(text):
            # Additional context clues for higher confidence
            confidence = 0.8
            if any(word in text.lower() for word in ['anything', 'whatever', 'curious']):
                confidence = 0.9
            return RoleSignal.INVITE_QUESTIONS, confidence
        
        # Check for request to ask
        if self.request_regex.search(text):
            return RoleSignal.REQUEST_TO_ASK, 0.8
        
        # Check for yielding floor
        if self.yield_regex.search(text):
            return RoleSignal.YIELD_FLOOR, 0.7
        
        # Check for question patterns (indicates user wants to ask)
        if text.endswith('?') and len(text.split()) > 2:
            return RoleSignal.REQUEST_TO_ASK, 0.6
        
        return RoleSignal.NONE, 0.0


class BasicPragmaticsEngine:
    """Phase 0 implementation of conversational pragmatics"""
    
    def __init__(self):
        self.state = PragmaticsState()
        self.detector = RoleSignalDetector()
        self.enabled = True
        self.role_threshold = 0.65  # Confidence threshold for role switching
    
    def process_user_input(self, user_input: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Process user input and update pragmatic state
        Returns pragmatic analysis and strategy recommendations
        """
        if not self.enabled:
            return {'strategy': 'answer', 'confidence': 1.0, 'pragmatics_active': False}
        
        context = context or {}
        self.state.update_turn()
        
        # Detect role signals
        signal, confidence = self.detector.detect_role_signal(user_input)
        
        # Determine strategy based on signal
        strategy = self._select_strategy(signal, confidence, user_input, context)
        
        # Update state based on detected signals
        if signal == RoleSignal.INVITE_QUESTIONS and confidence >= self.role_threshold:
            self.state.switch_roles(
                ConversationRole.RESPONDER,  # User wants to respond
                ConversationRole.QUESTIONER  # AI should ask questions
            )
        elif signal == RoleSignal.REQUEST_TO_ASK:
            self.state.switch_roles(
                ConversationRole.QUESTIONER,  # User wants to ask
                ConversationRole.RESPONDER    # AI should respond
            )
        
        return {
            'strategy': strategy,
            'confidence': confidence,
            'role_signal': signal.value,
            'ai_role': self.state.ai_role.value,
            'user_role': self.state.user_role.value,
            'initiative': self.state.initiative.value,
            'turn_count': self.state.turn_count,
            'pragmatics_active': True
        }
    
    def _select_strategy(self, signal: RoleSignal, confidence: float, 
                        user_input: str, context: Dict[str, Any]) -> str:
        """Select response strategy based on pragmatic analysis"""
        
        # High confidence role signals
        if confidence >= self.role_threshold:
            if signal == RoleSignal.INVITE_QUESTIONS:
                return 'ask_questions'  # AI should ask user questions
            elif signal == RoleSignal.REQUEST_TO_ASK:
                return 'answer'  # AI should answer user's question
            elif signal == RoleSignal.YIELD_FLOOR:
                return 'reflect_and_ask'  # Share thoughts then ask
        
        # Default behavior based on current state
        if self.state.ai_role == ConversationRole.QUESTIONER:
            return 'ask_questions'
        elif user_input.strip().endswith('?'):
            return 'answer'
        else:
            return 'respond'  # General conversational response
    
    def generate_questions_for_context(self, context: Dict[str, Any]) -> List[str]:
        """Generate appropriate questions based on context"""
        questions = []
        
        # Context-aware question generation
        topic = context.get('topic', '')
        participants = context.get('participants', [])
        
        if 'programming' in topic or 'code' in topic:
            questions.extend([
                "What's the most challenging project you're working on right now?",
                "What programming concept or technology has excited you lately?",
                "Have you run into any particularly tricky bugs recently?"
            ])
        
        if 'josh' in participants or 'brochacho' in participants:
            questions.extend([
                "What's Josh been saying about your latest code?",
                "Any new tech discoveries you want to share?"
            ])
        
        if 'reneille' in participants:
            questions.extend([
                "How are things going with Reneille?",
                "Any new organizational challenges to tackle?"
            ])
        
        # General fallback questions
        if not questions:
            questions.extend([
                "What's been on your mind lately?",
                "What's the most interesting thing you've learned recently?",
                "What are you excited about working on?"
            ])
        
        return questions[:2]  # Return at most 2 questions
    
    def get_state_info(self) -> Dict[str, Any]:
        """Get current pragmatic state information"""
        return {
            'user_role': self.state.user_role.value,
            'ai_role': self.state.ai_role.value,
            'initiative': self.state.initiative.value,
            'current_goal': self.state.current_goal.value,
            'turn_count': self.state.turn_count,
            'last_role_switch': self.state.last_role_switch,
            'enabled': self.enabled
        }
    
    def reset_state(self):
        """Reset pragmatic state to defaults"""
        self.state = PragmaticsState()
    
    def configure(self, **kwargs):
        """Configure pragmatics engine parameters"""
        if 'enabled' in kwargs:
            self.enabled = kwargs['enabled']
        if 'role_threshold' in kwargs:
            self.role_threshold = kwargs['role_threshold']


def create_basic_pragmatics_engine():
    """Factory function to create basic pragmatics engine"""
    return BasicPragmaticsEngine()


if __name__ == "__main__":
    print("Testing Basic Pragmatics Engine - Phase 0")
    print("=" * 45)
    
    engine = create_basic_pragmatics_engine()
    
    # Test cases for AMA detection
    test_cases = [
        "Ask me anything!",
        "Go ahead, ask me something.",
        "Can I ask you about your code?",
        "What do you think about this approach?",
        "Fire away with your questions.",
        "Let me ask you something.",
        "What's the weather like?",
        "That's interesting.",
        "You ask me something for once."
    ]
    
    print("Testing role signal detection:")
    for i, test_input in enumerate(test_cases, 1):
        result = engine.process_user_input(test_input)
        print(f"\n{i}. Input: \"{test_input}\"")
        print(f"   Strategy: {result['strategy']}")
        print(f"   Role Signal: {result['role_signal']}")
        print(f"   AI Role: {result['ai_role']}")
        print(f"   Confidence: {result['confidence']:.2f}")
    
    print(f"\nFinal state: {engine.get_state_info()}")
    print("\nPhase 0 Pragmatics Engine ready!")
    print("Features implemented:")
    print("- PragmaticsState tracking conversation roles and initiative")
    print("- RoleSignalDetector with regex patterns for AMA disambiguation")  
    print("- BasicPragmaticsEngine with strategy selection")
    print("- Context-aware question generation")
    print("- Configuration and fallback mechanisms")
