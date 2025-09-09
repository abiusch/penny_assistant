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
                        suggested_research=f\"Research {topic} comprehensively\",
                        permission_strategy=ResearchPermissionStrategy.DIRECT_ASK,
                        expected_user_interest=0.8
                    ))\n        \n        # 2. Implicit curiosity indicators\n        for pattern in self.research_patterns['implicit_curiosity']:\n            if re.search(pattern, user_lower):\n                topic = self._extract_main_topic(user_input)\n                if topic:\n                    opportunities.append(LearningOpportunity(\n                        opportunity_type=LearningOpportunityType.FOLLOW_UP_CURIOSITY,\n                        topic=topic,\n                        context=user_input,\n                        user_input=user_input,\n                        confidence=0.7,\n                        suggested_research=f\"Explore {topic} to satisfy curiosity\",\n                        permission_strategy=ResearchPermissionStrategy.CURIOUS_SUGGESTION,\n                        expected_user_interest=0.6\n                    ))\n        \n        # 3. Knowledge gaps\n        for pattern in self.research_patterns['knowledge_gaps']:\n            if re.search(pattern, user_lower):\n                topic = self._extract_confusion_topic(user_input)\n                if topic:\n                    opportunities.append(LearningOpportunity(\n                        opportunity_type=LearningOpportunityType.KNOWLEDGE_GAP,\n                        topic=topic,\n                        context=user_input,\n                        user_input=user_input,\n                        confidence=0.8,\n                        suggested_research=f\"Clarify understanding of {topic}\",\n                        permission_strategy=ResearchPermissionStrategy.PROBLEM_SOLVING,\n                        expected_user_interest=0.7\n                    ))\n        \n        # 4. Problem-solving opportunities\n        for pattern in self.research_patterns['problem_solving']:\n            if re.search(pattern, user_lower):\n                topic = self._extract_decision_topic(user_input)\n                if topic:\n                    opportunities.append(LearningOpportunity(\n                        opportunity_type=LearningOpportunityType.PROBLEM_SOLVING,\n                        topic=topic,\n                        context=user_input,\n                        user_input=user_input,\n                        confidence=0.8,\n                        suggested_research=f\"Research options for {topic}\",\n                        permission_strategy=ResearchPermissionStrategy.PROBLEM_SOLVING,\n                        expected_user_interest=0.8\n                    ))\n        \n        # 5. Interest deepening based on learning goals\n        current_interests = self._get_current_learning_interests()\n        for interest_topic in current_interests:\n            if interest_topic.lower() in user_lower:\n                opportunities.append(LearningOpportunity(\n                    opportunity_type=LearningOpportunityType.INTEREST_DEEPENING,\n                    topic=interest_topic,\n                    context=user_input,\n                    user_input=user_input,\n                    confidence=0.6,\n                    suggested_research=f\"Deepen knowledge of {interest_topic}\",\n                    permission_strategy=ResearchPermissionStrategy.INTEREST_BUILDING,\n                    expected_user_interest=0.9\n                ))\n        \n        return opportunities\n    \n    def detect_correction_attempt(self, user_input: str, previous_assistant_response: str) -> Optional[Tuple[str, str]]:\n        \"\"\"Detect if user is correcting previous information.\"\"\"\n        user_lower = user_input.lower()\n        \n        # Check for correction patterns\n        for pattern in self.correction_patterns:\n            if re.search(pattern, user_lower):\n                # Extract what they're correcting\n                original_info = self._extract_corrected_info(previous_assistant_response)\n                corrected_info = self._extract_new_info(user_input)\n                \n                if original_info and corrected_info:\n                    return (original_info, corrected_info)\n        \n        return None\n    \n    def request_research_permission(self, opportunity: LearningOpportunity) -> str:\n        \"\"\"Generate a permission request based on the opportunity.\"\"\"\n        strategy = opportunity.permission_strategy\n        templates = self.permission_templates[strategy]\n        \n        # Choose template based on user's emotional state and personality\n        emotional_context = self.memory.current_emotional_context\n        \n        if emotional_context and emotional_context.detected_emotion.value in ['playful', 'curious']:\n            # Use more enthusiastic templates\n            template = random.choice(templates)\n        else:\n            # Use more measured templates\n            template = templates[0]  # Use first (usually most direct)\n        \n        # Fill in template variables\n        filled_template = self._fill_permission_template(template, opportunity)\n        \n        return filled_template\n    \n    def generate_curiosity_question(self, topic: str, context: str) -> str:\n        \"\"\"Generate a curious follow-up question about a topic.\"\"\"\n        # Consider user's learning style and emotional state\n        emotional_context = self.memory.current_emotional_context\n        \n        # Get related topics from user's interests\n        related_topics = self._find_related_learning_topics(topic)\n        \n        # Choose appropriate curiosity template\n        template = random.choice(self.curiosity_templates)\n        \n        # Fill in the template\n        question = template.format(\n            topic=topic,\n            related_topic=related_topics[0] if related_topics else \"other interests\"\n        )\n        \n        return question\n    \n    def record_research_session(self, opportunity: LearningOpportunity, permission_granted: bool) -> int:\n        \"\"\"Record a research session in the database.\"\"\"\n        current_time = time.time()\n        \n        with sqlite3.connect(self.db_path) as conn:\n            cursor = conn.execute(\"\"\"\n                INSERT INTO research_sessions \n                (topic, user_input, permission_requested, permission_granted, \n                 research_conducted, timestamp)\n                VALUES (?, ?, ?, ?, ?, ?)\n            \"\"\", (\n                opportunity.topic,\n                opportunity.user_input,\n                current_time,\n                int(permission_granted),\n                0,  # Not conducted yet\n                current_time\n            ))\n            \n            session_id = cursor.lastrowid\n            \n        return session_id\n    \n    def record_user_correction(self, original_info: str, corrected_info: str, \n                             context: str, user_input: str) -> int:\n        \"\"\"Record when user corrects Penny's information.\"\"\"\n        current_time = time.time()\n        \n        with sqlite3.connect(self.db_path) as conn:\n            cursor = conn.execute(\"\"\"\n                INSERT INTO user_corrections \n                (original_statement, corrected_statement, context, user_input,\n                 confidence_before, confidence_after, learned_from, timestamp)\n                VALUES (?, ?, ?, ?, ?, ?, ?, ?)\n            \"\"\", (\n                original_info,\n                corrected_info,\n                context,\n                user_input,\n                0.5,  # Assumed confidence before\n                0.8,  # Higher confidence after correction\n                1,    # Learned from this\n                current_time\n            ))\n            \n            correction_id = cursor.lastrowid\n            \n        # Add to recent corrections to avoid repetition\n        self.memory.recent_corrections.append(corrected_info)\n        if len(self.memory.recent_corrections) > 10:\n            self.memory.recent_corrections.pop(0)\n            \n        return correction_id\n    \n    def update_research_session(self, session_id: int, research_results: str, \n                              user_feedback: Optional[str] = None, \n                              feedback_rating: Optional[int] = None):\n        \"\"\"Update research session with results and feedback.\"\"\"\n        with sqlite3.connect(self.db_path) as conn:\n            conn.execute(\"\"\"\n                UPDATE research_sessions \n                SET research_conducted = 1, research_results = ?, \n                    user_feedback = ?, feedback_rating = ?\n                WHERE id = ?\n            \"\"\", (research_results, user_feedback, feedback_rating, session_id))\n    \n    def get_learning_context_for_llm(self) -> str:\n        \"\"\"Get learning context to include in LLM prompts.\"\"\"\n        context_parts = []\n        \n        # Recent corrections to incorporate\n        if self.memory.recent_corrections:\n            corrections_context = \"Recent learnings: \" + \", \".join(self.memory.recent_corrections[-3:])\n            context_parts.append(corrections_context)\n        \n        # Current learning goals with permission\n        permitted_topics = [\n            goal.topic for goal in self.memory.learning_goals.values()\n            if goal.exploration_permission and goal.user_interest_level > 0.5\n        ]\n        if permitted_topics:\n            learning_context = f\"User interested in learning about: {', '.join(permitted_topics[:3])}\"\n            context_parts.append(learning_context)\n        \n        # Pending research topics\n        if self.memory.pending_research_topics:\n            pending_context = f\"Pending research: {', '.join(self.memory.pending_research_topics[:2])}\"\n            context_parts.append(pending_context)\n        \n        return \"\\n\".join(context_parts)\n    \n    # Helper methods\n    def _extract_topic_from_text(self, text: str) -> Optional[str]:\n        \"\"\"Extract topic from text after research indicators.\"\"\"\n        # Simple extraction - take first few meaningful words\n        words = text.split()[:4]\n        topic_words = [w for w in words if len(w) > 2 and w.isalpha()]\n        return \" \".join(topic_words) if topic_words else None\n    \n    def _extract_main_topic(self, text: str) -> Optional[str]:\n        \"\"\"Extract main topic from general text.\"\"\"\n        # Look for nouns and important terms\n        words = re.findall(r'\\b[a-zA-Z]{3,}\\b', text)\n        # Filter out common words\n        common_words = {'the', 'and', 'but', 'how', 'why', 'what', 'when', 'where', 'about', 'with', 'that', 'this'}\n        meaningful_words = [w for w in words if w.lower() not in common_words][:3]\n        return \" \".join(meaningful_words) if meaningful_words else None\n    \n    def _extract_confusion_topic(self, text: str) -> Optional[str]:\n        \"\"\"Extract what the user is confused about.\"\"\"\n        # Look for topics after confusion indicators\n        patterns = [r'understand (.+)', r'confused about (.+)', r'difference between (.+)']\n        for pattern in patterns:\n            match = re.search(pattern, text.lower())\n            if match:\n                return match.group(1).strip()[:50]\n        return self._extract_main_topic(text)\n    \n    def _extract_decision_topic(self, text: str) -> Optional[str]:\n        \"\"\"Extract decision/problem topic.\"\"\"\n        # Look for topics after decision indicators\n        patterns = [r'figure out (.+)', r'decide (.+)', r'choose (.+)', r'best way to (.+)']\n        for pattern in patterns:\n            match = re.search(pattern, text.lower())\n            if match:\n                return match.group(1).strip()[:50]\n        return self._extract_main_topic(text)\n    \n    def _get_current_learning_interests(self) -> List[str]:\n        \"\"\"Get current learning interests from memory.\"\"\"\n        return [goal.topic for goal in self.memory.learning_goals.values() \n                if goal.user_interest_level > 0.4]\n    \n    def _extract_corrected_info(self, previous_response: str) -> Optional[str]:\n        \"\"\"Extract information that was corrected from previous response.\"\"\"\n        # Simple extraction of factual statements\n        sentences = previous_response.split('.')[:2]  # First two sentences\n        return '. '.join(sentences).strip() if sentences else None\n    \n    def _extract_new_info(self, user_input: str) -> Optional[str]:\n        \"\"\"Extract the corrected information from user input.\"\"\"\n        # Look for corrective statements\n        user_input = user_input.strip()\n        # Remove correction indicators\n        for pattern in self.correction_patterns:\n            user_input = re.sub(pattern, '', user_input, flags=re.IGNORECASE)\n        return user_input.strip() if user_input.strip() else None\n    \n    def _fill_permission_template(self, template: str, opportunity: LearningOpportunity) -> str:\n        \"\"\"Fill in permission template with opportunity details.\"\"\"\n        # Get related context\n        related_interests = self._find_related_learning_topics(opportunity.topic)\n        \n        # Basic template filling\n        filled = template.format(\n            topic=opportunity.topic,\n            specific_aspect=f\"the practical applications of {opportunity.topic}\",\n            speculation=f\"this connects to {related_interests[0] if related_interests else 'your other interests'}\",\n            hook=f\"It seems really relevant to what you're thinking about\",\n            aspect=\"the real-world applications\",\n            specific_help=\"current options and best practices\",\n            problem=\"your decision\",\n            related_interest=related_interests[0] if related_interests else \"technology\",\n            connection=related_interests[0] if related_interests else \"your interests\"\n        )\n        \n        return filled\n    \n    def _find_related_learning_topics(self, topic: str) -> List[str]:\n        \"\"\"Find related topics from user's learning history.\"\"\"\n        # Simple keyword matching for now\n        related = []\n        topic_lower = topic.lower()\n        \n        for goal in self.memory.learning_goals.values():\n            if (goal.topic.lower() != topic_lower and \n                any(word in goal.topic.lower() for word in topic_lower.split())):\n                related.append(goal.topic)\n        \n        return related[:2]  # Return top 2 related topics\n\n\ndef create_guided_learning_system(emotional_memory_system):\n    \"\"\"Factory function to create guided learning system.\"\"\"\n    return GuidedLearningSystem(emotional_memory_system)\n