#!/usr/bin/env python3
"""
Guided Learning & Reasoning System for PennyGPT
Transforms Penny from reactive to proactive and genuinely curious
"""

import json
import time
import re
import sqlite3
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import random


class LearningOpportunityType(Enum):
    """Types of learning opportunities Penny can detect."""
    RESEARCH_REQUEST = "research_request"
    KNOWLEDGE_GAP = "knowledge_gap"
    FOLLOW_UP_CURIOSITY = "follow_up_curiosity"
    CORRECTION_OPPORTUNITY = "correction_opportunity"
    INTEREST_DEEPENING = "interest_deepening"
    PROBLEM_SOLVING = "problem_solving"


class ResearchPermissionStrategy(Enum):
    """Strategies for requesting research permission."""
    DIRECT_ASK = "direct_ask"
    CURIOUS_SUGGESTION = "curious_suggestion"
    PROBLEM_SOLVING = "problem_solving"
    INTEREST_BUILDING = "interest_building"


@dataclass
class LearningOpportunity:
    """Represents a detected opportunity for learning/research."""
    opportunity_type: LearningOpportunityType
    topic: str
    context: str
    user_input: str
    confidence: float
    suggested_research: str
    permission_strategy: ResearchPermissionStrategy
    expected_user_interest: float


class GuidedLearningSystem:
    """Core system for guided learning and proactive curiosity."""
    
    def __init__(self, emotional_memory_system):
        self.memory = emotional_memory_system
        self.db_path = emotional_memory_system.db_path
        
        # Load personal profile for enhanced context
        try:
            from src.core.personal_profile_system import PersonalProfileLoader
            self.personal_profile = PersonalProfileLoader()
            print("✅ Personal profile loaded for guided learning")
        except Exception as e:
            print(f"⚠️ Personal profile not available: {e}")
            self.personal_profile = None
        
        # Learning opportunity patterns
        self.research_patterns = {
            'explicit_request': [
                r'can you (research|look up|find out|investigate)',
                r'i want to (learn|know|understand) (more )?about',
                r'tell me (more )?about',
                r'what (do you know|can you tell me) about',
                r'help me (understand|learn|figure out)'
            ],
            'implicit_curiosity': [
                r'i wonder (if|why|how|what)',
                r'(why|how) (does|do|is|are)',
                r'what would happen if',
                r'i\'ve been thinking about',
                r'i\'m curious about'
            ],
            'knowledge_gaps': [
                r'i don\'t (really )?understand',
                r'i\'m (not sure|confused) about',
                r'what\'s the difference between',
                r'how is .* different from',
                r'i\'ve never (heard of|understood)'
            ],
            'problem_solving': [
                r'i need to (figure out|solve|decide)',
                r'i\'m trying to (understand|choose|pick)',
                r'should i .* or .*',
                r'what\'s the best way to',
                r'how do i (choose|decide|determine)'
            ]
        }
        
        # Correction detection patterns
        self.correction_patterns = [
            r'(no|nope|actually|well actually)',
            r'that\'s (not|incorrect|wrong)',
            r'(i think|i believe) (it\'s|that\'s) (actually)',
            r'(let me correct|to clarify)',
            r'(it\'s more like|it\'s actually)'
        ]
        
        # Permission request templates
        self.permission_templates = {
            ResearchPermissionStrategy.DIRECT_ASK: [
                "Want me to look into {topic} for you? I'm curious about {specific_aspect}.",
                "I'd love to research {topic} if you're interested. Should I dig into it?",
                "I could explore {topic} and see what I find. Worth investigating?"
            ],
            ResearchPermissionStrategy.CURIOUS_SUGGESTION: [
                "This makes me curious about {topic}. I wonder if {speculation}? Want me to explore that?",
                "You know what's interesting about {topic}? {hook}. Should we dive deeper?",
                "I'm genuinely curious about {aspect} of {topic}. Mind if I research it?"
            ],
            ResearchPermissionStrategy.PROBLEM_SOLVING: [
                "I could help you figure out {topic} by researching {specific_help}. Useful?",
                "Want me to look up {topic} to help with {problem}? Might find some good options.",
                "I could investigate {topic} and find some practical insights for you. Worth doing?"
            ],
            ResearchPermissionStrategy.INTEREST_BUILDING: [
                "Since you're into {related_interest}, you might find {topic} fascinating. Should I explore it?",
                "Given your interest in {connection}, {topic} could be right up your alley. Want me to dig in?",
                "I think you'd really enjoy learning about {topic}, especially {hook}. Shall I research it?"
            ]
        }
        
        # Curiosity follow-up templates
        self.curiosity_templates = [
            "What got you interested in {topic}?",
            "Have you experimented with {topic} before?",
            "What aspects of {topic} intrigue you most?",
            "How does {topic} connect to {related_topic}?",
            "What would you want to do with {topic} knowledge?",
            "Any particular angle on {topic} you'd like to explore?"
        ]
    
    def detect_learning_opportunities(self, user_input: str, conversation_context: str) -> List[LearningOpportunity]:
        """Detect opportunities for research, learning, or curiosity."""
        opportunities = []
        user_lower = user_input.lower()
        
        # 1. Explicit research requests
        for pattern in self.research_patterns['explicit_request']:
            matches = re.finditer(pattern, user_lower)
            for match in matches:
                # Extract topic after the pattern
                after_match = user_lower[match.end():].strip()
                topic = self._extract_topic_from_text(after_match)
                
                if topic:
                    opportunities.append(LearningOpportunity(
                        opportunity_type=LearningOpportunityType.RESEARCH_REQUEST,
                        topic=topic,
                        context=user_input,
                        user_input=user_input,
                        confidence=0.9,
                        suggested_research=f"Research {topic} comprehensively",
                        permission_strategy=ResearchPermissionStrategy.DIRECT_ASK,
                        expected_user_interest=0.8
                    ))
        
        # 2. Implicit curiosity indicators
        for pattern in self.research_patterns['implicit_curiosity']:
            if re.search(pattern, user_lower):
                topic = self._extract_main_topic(user_input)
                if topic:
                    opportunities.append(LearningOpportunity(
                        opportunity_type=LearningOpportunityType.FOLLOW_UP_CURIOSITY,
                        topic=topic,
                        context=user_input,
                        user_input=user_input,
                        confidence=0.7,
                        suggested_research=f"Explore {topic} to satisfy curiosity",
                        permission_strategy=ResearchPermissionStrategy.CURIOUS_SUGGESTION,
                        expected_user_interest=0.6
                    ))
        
        # 3. Knowledge gaps
        for pattern in self.research_patterns['knowledge_gaps']:
            if re.search(pattern, user_lower):
                topic = self._extract_confusion_topic(user_input)
                if topic:
                    opportunities.append(LearningOpportunity(
                        opportunity_type=LearningOpportunityType.KNOWLEDGE_GAP,
                        topic=topic,
                        context=user_input,
                        user_input=user_input,
                        confidence=0.8,
                        suggested_research=f"Clarify understanding of {topic}",
                        permission_strategy=ResearchPermissionStrategy.PROBLEM_SOLVING,
                        expected_user_interest=0.7
                    ))
        
        # 4. Problem-solving opportunities
        for pattern in self.research_patterns['problem_solving']:
            if re.search(pattern, user_lower):
                topic = self._extract_decision_topic(user_input)
                if topic:
                    opportunities.append(LearningOpportunity(
                        opportunity_type=LearningOpportunityType.PROBLEM_SOLVING,
                        topic=topic,
                        context=user_input,
                        user_input=user_input,
                        confidence=0.8,
                        suggested_research=f"Research options for {topic}",
                        permission_strategy=ResearchPermissionStrategy.PROBLEM_SOLVING,
                        expected_user_interest=0.8
                    ))
        
        # 5. Interest deepening based on learning goals
        current_interests = self._get_current_learning_interests()
        for interest_topic in current_interests:
            if interest_topic.lower() in user_lower:
                opportunities.append(LearningOpportunity(
                    opportunity_type=LearningOpportunityType.INTEREST_DEEPENING,
                    topic=interest_topic,
                    context=user_input,
                    user_input=user_input,
                    confidence=0.6,
                    suggested_research=f"Deepen knowledge of {interest_topic}",
                    permission_strategy=ResearchPermissionStrategy.INTEREST_BUILDING,
                    expected_user_interest=0.9
                ))
        
        return opportunities
    
    def detect_correction_attempt(self, user_input: str, previous_assistant_response: str) -> Optional[Tuple[str, str]]:
        """Detect if user is correcting previous information."""
        user_lower = user_input.lower()
        
        # Check for correction patterns
        for pattern in self.correction_patterns:
            if re.search(pattern, user_lower):
                # Extract what they're correcting
                original_info = self._extract_corrected_info(previous_assistant_response)
                corrected_info = self._extract_new_info(user_input)
                
                if original_info and corrected_info:
                    return (original_info, corrected_info)
        
        return None
    
    def request_research_permission(self, opportunity: LearningOpportunity) -> str:
        """Generate a permission request based on the opportunity."""
        strategy = opportunity.permission_strategy
        templates = self.permission_templates[strategy]
        
        # Choose template based on user's emotional state and personality
        emotional_context = self.memory.current_emotional_context
        
        if emotional_context and emotional_context.detected_emotion.value in ['playful', 'curious']:
            # Use more enthusiastic templates
            template = random.choice(templates)
        else:
            # Use more measured templates
            template = templates[0]  # Use first (usually most direct)
        
        # Fill in template variables
        filled_template = self._fill_permission_template(template, opportunity)
        
        return filled_template
    
    def generate_curiosity_question(self, topic: str, context: str) -> str:
        """Generate a curious follow-up question about a topic."""
        # Consider user's learning style and emotional state
        emotional_context = self.memory.current_emotional_context
        
        # Get related topics from user's interests
        related_topics = self._find_related_learning_topics(topic)
        
        # Choose appropriate curiosity template
        template = random.choice(self.curiosity_templates)
        
        # Fill in the template
        question = template.format(
            topic=topic,
            related_topic=related_topics[0] if related_topics else "other interests"
        )
        
        return question
    
    def record_research_session(self, opportunity: LearningOpportunity, permission_granted: bool) -> int:
        """Record a research session in the database."""
        current_time = time.time()
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                INSERT INTO research_sessions 
                (topic, user_input, permission_requested, permission_granted, 
                 research_conducted, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                opportunity.topic,
                opportunity.user_input,
                current_time,
                int(permission_granted),
                0,  # Not conducted yet
                current_time
            ))
            
            session_id = cursor.lastrowid
            
        return session_id
    
    def record_user_correction(self, original_info: str, corrected_info: str, 
                             context: str, user_input: str) -> int:
        """Record when user corrects Penny's information."""
        current_time = time.time()
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                INSERT INTO user_corrections 
                (original_statement, corrected_statement, context, user_input,
                 confidence_before, confidence_after, learned_from, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                original_info,
                corrected_info,
                context,
                user_input,
                0.5,  # Assumed confidence before
                0.8,  # Higher confidence after correction
                1,    # Learned from this
                current_time
            ))
            
            correction_id = cursor.lastrowid
            
        # Add to recent corrections to avoid repetition
        self.memory.recent_corrections.append(corrected_info)
        if len(self.memory.recent_corrections) > 10:
            self.memory.recent_corrections.pop(0)
            
        return correction_id
    
    def update_research_session(self, session_id: int, research_results: str, 
                              user_feedback: Optional[str] = None, 
                              feedback_rating: Optional[int] = None):
        """Update research session with results and feedback."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                UPDATE research_sessions 
                SET research_conducted = 1, research_results = ?, 
                    user_feedback = ?, feedback_rating = ?
                WHERE id = ?
            """, (research_results, user_feedback, feedback_rating, session_id))
    
    def get_learning_context_for_llm(self) -> str:
        """Get learning context to include in LLM prompts."""
        context_parts = []
        
        # Recent corrections to incorporate
        if hasattr(self.memory, 'recent_corrections') and self.memory.recent_corrections:
            corrections_context = "Recent learnings: " + ", ".join(self.memory.recent_corrections[-3:])
            context_parts.append(corrections_context)
        
        # Current learning goals with permission
        if hasattr(self.memory, 'learning_goals'):
            permitted_topics = [
                goal.topic for goal in self.memory.learning_goals.values()
                if goal.exploration_permission and goal.user_interest_level > 0.5
            ]
            if permitted_topics:
                learning_context = f"User interested in learning about: {', '.join(permitted_topics[:3])}"
                context_parts.append(learning_context)
        
        # Pending research topics
        if hasattr(self.memory, 'pending_research_topics') and self.memory.pending_research_topics:
            pending_context = f"Pending research: {', '.join(self.memory.pending_research_topics[:2])}"
            context_parts.append(pending_context)
        
        return "\n".join(context_parts)
    
    # Helper methods
    def _extract_topic_from_text(self, text: str) -> Optional[str]:
        """Extract topic from text after research indicators."""
        # Simple extraction - take first few meaningful words
        words = text.split()[:4]
        topic_words = [w for w in words if len(w) > 2 and w.isalpha()]
        return " ".join(topic_words) if topic_words else None
    
    def _extract_main_topic(self, text: str) -> Optional[str]:
        """Extract main topic from general text."""
        # Look for nouns and important terms
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text)
        # Filter out common words
        common_words = {'the', 'and', 'but', 'how', 'why', 'what', 'when', 'where', 'about', 'with', 'that', 'this'}
        meaningful_words = [w for w in words if w.lower() not in common_words][:3]
        return " ".join(meaningful_words) if meaningful_words else None
    
    def _extract_confusion_topic(self, text: str) -> Optional[str]:
        """Extract what the user is confused about."""
        # Look for topics after confusion indicators
        patterns = [r'understand (.+)', r'confused about (.+)', r'difference between (.+)']
        for pattern in patterns:
            match = re.search(pattern, text.lower())
            if match:
                return match.group(1).strip()[:50]
        return self._extract_main_topic(text)
    
    def _extract_decision_topic(self, text: str) -> Optional[str]:
        """Extract decision/problem topic."""
        # Look for topics after decision indicators
        patterns = [r'figure out (.+)', r'decide (.+)', r'choose (.+)', r'best way to (.+)']
        for pattern in patterns:
            match = re.search(pattern, text.lower())
            if match:
                return match.group(1).strip()[:50]
        return self._extract_main_topic(text)
    
    def _get_current_learning_interests(self) -> List[str]:
        """Get current learning interests from memory."""
        if hasattr(self.memory, 'learning_goals'):
            return [goal.topic for goal in self.memory.learning_goals.values() 
                    if goal.user_interest_level > 0.4]
        return []
    
    def _extract_corrected_info(self, previous_response: str) -> Optional[str]:
        """Extract information that was corrected from previous response."""
        # Simple extraction of factual statements
        sentences = previous_response.split('.')[:2]  # First two sentences
        return '. '.join(sentences).strip() if sentences else None
    
    def _extract_new_info(self, user_input: str) -> Optional[str]:
        """Extract the corrected information from user input."""
        # Look for corrective statements
        user_input = user_input.strip()
        # Remove correction indicators
        for pattern in self.correction_patterns:
            user_input = re.sub(pattern, '', user_input, flags=re.IGNORECASE)
        return user_input.strip() if user_input.strip() else None
    
    def _fill_permission_template(self, template: str, opportunity: LearningOpportunity) -> str:
        """Fill in permission template with opportunity details."""
        # Get related context
        related_interests = self._find_related_learning_topics(opportunity.topic)
        
        # Basic template filling
        filled = template.format(
            topic=opportunity.topic,
            specific_aspect=f"the practical applications of {opportunity.topic}",
            speculation=f"this connects to {related_interests[0] if related_interests else 'your other interests'}",
            hook=f"It seems really relevant to what you're thinking about",
            aspect="the real-world applications",
            specific_help="current options and best practices",
            problem="your decision",
            related_interest=related_interests[0] if related_interests else "technology",
            connection=related_interests[0] if related_interests else "your interests"
        )
        
        return filled
    
    def _find_related_learning_topics(self, topic: str) -> List[str]:
        """Find related topics from user's learning history."""
        # Simple keyword matching for now
        related = []
        topic_lower = topic.lower()
        
        if hasattr(self.memory, 'learning_goals'):
            for goal in self.memory.learning_goals.values():
                if (goal.topic.lower() != topic_lower and 
                    any(word in goal.topic.lower() for word in topic_lower.split())):
                    related.append(goal.topic)
        
        return related[:2]  # Return top 2 related topics


def create_guided_learning_system(emotional_memory_system):
    """Factory function to create guided learning system."""
    return GuidedLearningSystem(emotional_memory_system)
