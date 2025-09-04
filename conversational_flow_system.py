#!/usr/bin/env python3
"""
Conversational Flow & Relationship Building System
Handles natural conversation flow, follow-up questions, historical references,
and deeper relationship building for PennyGPT
"""

import json
import time
import random
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import re


class ConversationState(Enum):
    """Different conversation states for natural flow."""
    IDLE = "idle"                    # Waiting for wake word
    ENGAGED = "engaged"              # In active conversation
    FOLLOW_UP = "follow_up"          # Expecting follow-up response
    DEEP_DIVE = "deep_dive"          # In philosophical/learning discussion
    PERMISSION_PENDING = "pending"   # Waiting for permission to research/learn


@dataclass
class ConversationContext:
    """Context for managing conversation flow."""
    current_state: ConversationState
    topic_stack: List[str] = field(default_factory=list)  # Current conversation topics
    follow_up_questions: List[str] = field(default_factory=list)
    last_user_input: str = ""
    last_assistant_response: str = ""
    engagement_level: float = 0.0    # 0-1 scale of user engagement
    conversation_depth: int = 0      # How many exchanges in current topic
    pending_permissions: List[str] = field(default_factory=list)
    last_interaction_time: float = 0.0
    session_start_time: float = 0.0


@dataclass
class RelationshipInsight:
    """Insights about relationships for building deeper connections."""
    name: str
    relationship_type: str
    context: str
    emotional_patterns: Dict[str, float]
    conversation_history: List[str] = field(default_factory=list)
    shared_memories: List[str] = field(default_factory=list)
    important_dates: List[str] = field(default_factory=list)
    inside_jokes: List[str] = field(default_factory=list)


class ConversationalFlowSystem:
    """System for managing natural conversation flow and relationship building."""
    
    def __init__(self, emotional_memory, personality_integration):
        self.emotional_memory = emotional_memory
        self.personality_integration = personality_integration
        
        # Conversation state management
        self.conversation_context = ConversationContext(
            current_state=ConversationState.IDLE,
            session_start_time=time.time()
        )
        
        # Relationship building
        self.relationship_insights = {}  # name -> RelationshipInsight
        
        # Conversation patterns
        self.follow_up_patterns = self._init_follow_up_patterns()
        self.historical_reference_patterns = self._init_historical_patterns()
        self.philosophical_starters = self._init_philosophical_starters()
        self.permission_requests = self._init_permission_requests()
        
        # Flow management
        self.engagement_threshold = 0.6  # When to stay engaged vs. require wake word
        self.conversation_timeout = 300  # 5 minutes of silence returns to idle
        self.deep_dive_threshold = 0.8   # Engagement level for philosophical discussions
        
        print("🗣️ Conversational flow system initialized")
    
    def _init_follow_up_patterns(self) -> Dict[str, List[str]]:
        """Initialize follow-up question patterns."""
        return {
            'curiosity': [
                "What made you interested in that?",
                "How did you first get into that?",
                "What's the most interesting part about it?",
                "Have you always felt that way?",
                "What got you thinking about that?"
            ],
            'support': [
                "How are you feeling about that now?",
                "Is there anything I can help you figure out?",
                "Want to talk through what's on your mind?",
                "What would make this easier for you?",
                "How can I support you with this?"
            ],
            'exploration': [
                "Want to dig deeper into that?",
                "That reminds me of something... want to explore it?",
                "Should we think about this together?",
                "I'm curious about your perspective on this",
                "There's more to unpack here, isn't there?"
            ],
            'tech_enthusiasm': [
                "Ooh, want to geek out about this more?",
                "Have you tried any cool tools for that?",
                "What's your setup like?",
                "Any interesting projects you're working on?",
                "Want to hear about some cool related tech?"
            ],
            'relationship_check': [
                "How's {name} doing, by the way?",
                "Speaking of {name}, how are things going there?",
                "Last time you mentioned {name} - any updates?",
                "How's your {relationship} situation?",
                "Everything good with the family?"
            ]
        }
    
    def _init_historical_patterns(self) -> List[str]:
        """Initialize patterns for referencing previous conversations."""
        return [
            "Like we talked about {timeframe}...",
            "Remember when you mentioned {topic}?",
            "You were saying {timeframe} about {topic}...",
            "That reminds me of what you said about {topic}",
            "Going back to our conversation about {topic}...",
            "You know, {timeframe} you brought up {topic}...",
            "This connects to that thing about {topic} we discussed",
            "Wasn't it {timeframe} when you told me about {topic}?"
        ]
    
    def _init_philosophical_starters(self) -> List[str]:
        """Initialize philosophical discussion starters."""
        return [
            "You know what I've been thinking about lately?",
            "Here's something interesting to consider...",
            "I wonder if you've ever thought about this...",
            "Can I share something that's been on my mind?",
            "Want to explore a philosophical question together?",
            "This might sound deep, but...",
            "I've been pondering something...",
            "Here's a thought experiment for you..."
        ]
    
    def _init_permission_requests(self) -> Dict[str, List[str]]:
        """Initialize permission request patterns."""
        return {
            'research': [
                "Want me to look into {topic} for you?",
                "I could research {topic} if you'd like?",
                "Should I dig up some info on {topic}?",
                "Mind if I explore {topic} and get back to you?",
                "Can I investigate {topic} and share what I find?"
            ],
            'learning': [
                "Want to learn about {topic} together?",
                "Should we explore {topic} as a team?",
                "Mind if I help you dive deeper into {topic}?",
                "Can we make {topic} a learning project?",
                "Want me to help you understand {topic} better?"
            ],
            'advice': [
                "Want my thoughts on {topic}?",
                "Mind if I share some perspective on {topic}?",
                "Can I offer some insights about {topic}?",
                "Should I weigh in on {topic}?",
                "Want to brainstorm {topic} together?"
            ]
        }
    
    def should_stay_engaged(self, user_input: str) -> bool:
        """Determine if we should stay in conversation mode or require wake word."""
        # Always stay engaged if in active conversation states
        if self.conversation_context.current_state in [
            ConversationState.FOLLOW_UP, 
            ConversationState.DEEP_DIVE,
            ConversationState.PERMISSION_PENDING
        ]:
            return True
        
        # Check engagement level
        if self.conversation_context.engagement_level > self.engagement_threshold:
            return True
        
        # Check time since last interaction
        time_since_last = time.time() - self.conversation_context.last_interaction_time
        if time_since_last < 30:  # Stay engaged for 30 seconds
            return True
        
        # Check for follow-up indicators in user input
        follow_up_indicators = [
            'also', 'and', 'plus', 'additionally', 'furthermore', 'moreover',
            'by the way', 'oh', 'actually', 'wait', 'another thing',
            'speaking of', 'that reminds me'
        ]
        
        if any(indicator in user_input.lower() for indicator in follow_up_indicators):
            return True
        
        return False
    
    def calculate_engagement_level(self, user_input: str, emotional_context: Any) -> float:
        """Calculate user engagement level based on input and context."""
        engagement = 0.5  # Base level
        
        # Length and complexity boost engagement
        if len(user_input) > 50:
            engagement += 0.1
        if len(user_input) > 100:
            engagement += 0.1
        
        # Questions show engagement
        if '?' in user_input:
            engagement += 0.2
        
        # Emotional indicators
        if emotional_context and hasattr(emotional_context, 'detected_emotion'):
            emotion = emotional_context.detected_emotion.value
            if emotion in ['curious', 'excited', 'happy']:
                engagement += 0.3
            elif emotion in ['frustrated', 'worried']:
                engagement += 0.2  # Engaged but needs support
        
        # Personal sharing increases engagement
        personal_indicators = ['i feel', 'i think', 'i believe', 'my', 'i\'m', 'personally']
        if any(indicator in user_input.lower() for indicator in personal_indicators):
            engagement += 0.2
        
        # Technical topics
        tech_words = ['computer', 'software', 'ai', 'technology', 'code', 'programming']
        if any(word in user_input.lower() for word in tech_words):
            engagement += 0.1
        
        return min(1.0, engagement)
    
    def generate_follow_up_question(self, user_input: str, response: str, topic_category: str) -> Optional[str]:
        """Generate appropriate follow-up questions."""
        
        # Don't generate follow-ups too frequently
        if random.random() > 0.4:  # 40% chance
            return None
        
        # Choose pattern based on topic and context
        if topic_category == 'technology':
            pattern_type = 'tech_enthusiasm'
        elif topic_category in ['relationships', 'family']:
            pattern_type = 'relationship_check'
        elif topic_category == 'work_stress':
            pattern_type = 'support'
        elif topic_category == 'learning':
            pattern_type = 'exploration'
        else:
            pattern_type = 'curiosity'
        
        patterns = self.follow_up_patterns.get(pattern_type, self.follow_up_patterns['curiosity'])
        follow_up = random.choice(patterns)
        
        # Handle relationship-specific follow-ups
        if pattern_type == 'relationship_check':
            recent_relationships = self._get_recent_relationships()
            if recent_relationships:
                relationship = random.choice(recent_relationships)
                follow_up = follow_up.format(
                    name=relationship['name'],
                    relationship=relationship['type']
                )
            else:
                # Fallback to general question
                follow_up = random.choice(self.follow_up_patterns['curiosity'])
        
        return follow_up
    
    def enhance_response_with_flow(self, base_response: str, user_input: str, topic_category: str) -> str:
        """Enhance response with conversational flow elements."""
        enhanced_response = base_response
        
        # Add historical reference if appropriate
        if random.random() < 0.2:  # 20% chance
            historical_ref = self.generate_historical_reference(topic_category)
            if historical_ref:
                enhanced_response = f"{historical_ref} {enhanced_response}"
        
        # Add follow-up question
        follow_up = self.generate_follow_up_question(user_input, enhanced_response, topic_category)
        if follow_up:
            enhanced_response = f"{enhanced_response} {follow_up}"
            self.conversation_context.current_state = ConversationState.FOLLOW_UP
        
        # Offer philosophical discussion if conditions are met
        if self.should_offer_philosophical_discussion(
            self.conversation_context.conversation_depth,
            self.conversation_context.engagement_level
        ):
            philosophical_starter = self.generate_philosophical_starter(topic_category)
            enhanced_response = f"{enhanced_response} {philosophical_starter}"
            self.conversation_context.current_state = ConversationState.DEEP_DIVE
        
        # Add permission request for learning if appropriate
        if (topic_category == 'learning' and 
            random.random() < 0.3 and
            'learn' in user_input.lower()):
            permission_req = self.generate_permission_request(
                self._extract_topic_phrase(user_input), 
                'learning'
            )
            enhanced_response = f"{enhanced_response} {permission_req}"
            self.conversation_context.current_state = ConversationState.PERMISSION_PENDING
        
        return enhanced_response
    
    def update_conversation_state(self, user_input: str, response: str, topic_category: str):
        """Update conversation state based on interaction."""
        current_time = time.time()
        
        # Update basic context
        self.conversation_context.last_user_input = user_input
        self.conversation_context.last_assistant_response = response
        self.conversation_context.last_interaction_time = current_time
        
        # Calculate engagement
        emotional_context = self.emotional_memory.current_emotional_context
        engagement = self.calculate_engagement_level(user_input, emotional_context)
        self.conversation_context.engagement_level = engagement
        
        # Update topic stack
        if topic_category not in self.conversation_context.topic_stack:
            self.conversation_context.topic_stack.append(topic_category)
        
        # Keep topic stack manageable
        if len(self.conversation_context.topic_stack) > 3:
            self.conversation_context.topic_stack.pop(0)
        
        # Update conversation depth
        if (self.conversation_context.topic_stack and 
            topic_category == self.conversation_context.topic_stack[-1]):
            self.conversation_context.conversation_depth += 1
        else:
            self.conversation_context.conversation_depth = 1
        
        # Determine new state
        if self.should_stay_engaged(user_input):
            if self.conversation_context.current_state == ConversationState.IDLE:
                self.conversation_context.current_state = ConversationState.ENGAGED
        else:
            # Check timeout
            if current_time - self.conversation_context.last_interaction_time > self.conversation_timeout:
                self.conversation_context.current_state = ConversationState.IDLE
                self.conversation_context.topic_stack.clear()
                self.conversation_context.conversation_depth = 0
    
    def build_relationship_insights(self, user_input: str, response: str):
        """Build deeper relationship insights over time."""
        
        # Get current relationships from emotional memory
        for name, member in self.emotional_memory.family_members.items():
            if name not in self.relationship_insights:
                self.relationship_insights[name] = RelationshipInsight(
                    name=name,
                    relationship_type=member.relationship_type.value,
                    context=member.context,
                    emotional_patterns=member.emotional_associations.copy()
                )
            
            insight = self.relationship_insights[name]
            
            # Update conversation history if mentioned
            if name.lower() in user_input.lower():
                insight.conversation_history.append({
                    'user_said': user_input,
                    'context': response,
                    'timestamp': time.time()
                })
                
                # Keep history manageable
                if len(insight.conversation_history) > 20:
                    insight.conversation_history = insight.conversation_history[-15:]
                
                # Look for shared memories or important information
                self._extract_shared_memories(user_input, insight)
                self._extract_important_dates(user_input, insight)
                self._detect_inside_jokes(user_input, response, insight)
    
    def generate_historical_reference(self, current_topic: str) -> Optional[str]:
        """Generate references to previous conversations."""
        try:
            recent_conversations = self.emotional_memory.base_memory.get_recent_conversations(20)
        except:
            return None
        
        if not recent_conversations or len(recent_conversations) < 3:
            return None
        
        # Find related previous conversations
        related_conversations = []
        for conv in recent_conversations[1:]:  # Skip the most recent one
            if self._topics_related(current_topic, conv.user_input):
                related_conversations.append(conv)
        
        if not related_conversations:
            return None
        
        # Generate historical reference
        past_conv = random.choice(related_conversations)
        timeframe = self._get_relative_timeframe(past_conv.timestamp)
        
        pattern = random.choice(self.historical_reference_patterns)
        reference = pattern.format(
            timeframe=timeframe,
            topic=self._extract_topic_phrase(past_conv.user_input)
        )
        
        return reference
    
    def should_offer_philosophical_discussion(self, conversation_depth: int, engagement_level: float) -> bool:
        """Determine if we should offer deeper philosophical discussion."""
        return (
            conversation_depth >= 3 and 
            engagement_level > self.deep_dive_threshold and
            random.random() < 0.3  # 30% chance when conditions are met
        )
    
    def generate_philosophical_starter(self, topic: str) -> str:
        """Generate philosophical discussion starter."""
        starter = random.choice(self.philosophical_starters)
        
        # Add topic-specific philosophical questions
        philosophical_questions = {
            'technology': [
                "What do you think AI will mean for humanity in 50 years?",
                "Do you think we're becoming too dependent on technology?",
                "Is there a line between helpful AI and AI that's too intrusive?"
            ],
            'relationships': [
                "What do you think makes relationships really last?",
                "How do you balance being there for others vs. taking care of yourself?",
                "What's the most important thing you've learned about people?"
            ],
            'learning': [
                "What drives us to keep learning and growing?",
                "Do you think wisdom comes from experience or reflection?",
                "What's the difference between knowledge and understanding?"
            ],
            'general': [
                "What's something you believe that most people don't?",
                "If you could change one thing about how people interact, what would it be?",
                "What's a question you wish more people would ask themselves?"
            ]
        }
        
        questions = philosophical_questions.get(topic, philosophical_questions['general'])
        question = random.choice(questions)
        
        return f"{starter} {question}"
    
    def generate_permission_request(self, topic: str, request_type: str = 'research') -> str:
        """Generate permission requests for proactive learning."""
        patterns = self.permission_requests.get(request_type, self.permission_requests['research'])
        request = random.choice(patterns).format(topic=topic)
        return request
    
    def _get_recent_relationships(self) -> List[Dict[str, str]]:
        """Get recently mentioned relationships."""
        recent_cutoff = time.time() - (7 * 24 * 60 * 60)  # Last week
        recent = []
        
        for name, member in self.emotional_memory.family_members.items():
            if member.last_mentioned > recent_cutoff:
                recent.append({
                    'name': name,
                    'type': member.relationship_type.value,
                    'context': member.context
                })
        
        return recent
    
    def _topics_related(self, topic1: str, text: str) -> bool:
        """Check if topics are related."""
        topic1_words = set(topic1.lower().split())
        text_words = set(text.lower().split())
        
        # Simple overlap check - could be more sophisticated
        overlap = len(topic1_words.intersection(text_words))
        return overlap > 0 or any(word in text.lower() for word in topic1_words)
    
    def _get_relative_timeframe(self, timestamp: float) -> str:
        """Get relative timeframe description."""
        time_diff = time.time() - timestamp
        
        if time_diff < 3600:  # Less than 1 hour
            return "earlier"
        elif time_diff < 86400:  # Less than 1 day
            return "today"
        elif time_diff < 172800:  # Less than 2 days
            return "yesterday"
        elif time_diff < 604800:  # Less than 1 week
            return "this week"
        elif time_diff < 2592000:  # Less than 1 month
            return "recently"
        else:
            return "a while back"
    
    def _extract_topic_phrase(self, text: str) -> str:
        """Extract a concise topic phrase from text."""
        # Simple extraction - get first few meaningful words
        words = text.lower().split()
        
        # Remove common start words
        skip_words = {'i', 'my', 'the', 'a', 'an', 'can', 'could', 'would', 'should', 'how', 'what', 'why'}
        meaningful_words = [word for word in words if word not in skip_words and len(word) > 2]
        
        # Return first 2-3 meaningful words
        if meaningful_words:
            return ' '.join(meaningful_words[:3])
        else:
            return 'that topic'
    
    def _extract_shared_memories(self, user_input: str, insight: RelationshipInsight):
        """Extract shared memories from conversation."""
        memory_indicators = [
            'remember when', 'we used to', 'that time when', 'back when',
            'i remember', 'do you remember', 'the day', 'last time'
        ]
        
        user_lower = user_input.lower()
        for indicator in memory_indicators:
            if indicator in user_lower:
                # Extract the memory
                parts = user_lower.split(indicator, 1)
                if len(parts) > 1:
                    memory = indicator + parts[1].strip()
                    if memory not in insight.shared_memories:
                        insight.shared_memories.append(memory)
                        
                        # Keep manageable
                        if len(insight.shared_memories) > 10:
                            insight.shared_memories = insight.shared_memories[-7:]
    
    def _extract_important_dates(self, user_input: str, insight: RelationshipInsight):
        """Extract important dates mentioned."""
        date_patterns = [
            r'birthday.*?(\w+ \d+)',
            r'anniversary.*?(\w+ \d+)',
            r'wedding.*?(\w+ \d+)',
            r'graduation.*?(\w+ \d+)'
        ]
        
        for pattern in date_patterns:
            matches = re.finditer(pattern, user_input.lower())
            for match in matches:
                date_info = match.group(0)
                if date_info not in insight.important_dates:
                    insight.important_dates.append(date_info)
    
    def _detect_inside_jokes(self, user_input: str, response: str, insight: RelationshipInsight):
        """Detect potential inside jokes or recurring themes."""
        humor_indicators = ['haha', 'lol', 'funny', 'hilarious', 'joke', 'always says', 'typical']
        
        if any(indicator in user_input.lower() for indicator in humor_indicators):
            # This might be an inside joke or funny memory
            if len(user_input) < 200:  # Keep it concise
                potential_joke = user_input.strip()
                if potential_joke not in insight.inside_jokes:
                    insight.inside_jokes.append(potential_joke)
                    
                    # Keep manageable
                    if len(insight.inside_jokes) > 5:
                        insight.inside_jokes = insight.inside_jokes[-3:]
    
    def get_conversation_insights(self) -> Dict[str, Any]:
        """Get insights about conversation patterns and relationships."""
        return {
            'conversation_state': self.conversation_context.current_state.value,
            'engagement_level': self.conversation_context.engagement_level,
            'conversation_depth': self.conversation_context.conversation_depth,
            'current_topics': self.conversation_context.topic_stack,
            'session_duration': time.time() - self.conversation_context.session_start_time,
            'relationship_insights_count': len(self.relationship_insights),
            'deep_relationships': [
                name for name, insight in self.relationship_insights.items()
                if len(insight.shared_memories) > 2 or len(insight.inside_jokes) > 0
            ]
        }


# Integration function
def create_conversational_flow(emotional_memory, personality_integration):
    """Factory function to create conversational flow system."""
    return ConversationalFlowSystem(emotional_memory, personality_integration)
