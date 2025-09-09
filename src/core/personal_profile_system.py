#!/usr/bin/env python3
"""
Personal Profile System for PennyGPT
Loads user profile to provide immediate context and personality awareness
"""

import json
import os
import re
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from pathlib import Path


@dataclass
class CommunicationStyle:
    """User's communication preferences."""
    conversation_style: str  # direct, detailed, casual, professional
    response_length: str     # brief, detailed, varies
    humor_style: str        # dry, playful, sarcastic, professional, warm
    feedback_style: str     # direct, gentle, examples, questions
    sass_level: str         # low, medium, high, varies
    curiosity_level: str    # few, some, many, depends
    proactivity_level: str  # low, medium, high


@dataclass 
class InterestProfile:
    """User's interests and learning preferences."""
    active_interests: Dict[str, List[str]]  # category -> list of interests
    deep_interest_areas: List[str]
    interest_ratings: Dict[str, int]  # topic -> 1-5 rating
    learning_style: str  # visual, auditory, hands-on, reading
    research_permissions: Dict[str, str]  # topic -> auto/ask/depends


@dataclass
class ProfessionalContext:
    """User's professional background and current work."""
    current_role: str
    current_projects: List[str]
    technical_stack: List[str]
    professional_challenges: List[str]
    career_goals: List[str]
    learning_priorities: List[str]


@dataclass
class PersonalContext:
    """User's personal context and values."""
    life_situation: Dict[str, str]
    values_principles: List[str]
    current_challenges: List[str]
    major_goals: List[str]


class PersonalProfileLoader:
    """Loads and manages user personal profile."""
    
    def __init__(self, profile_path: str = "personal_profile.json"):
        self.profile_path = profile_path
        self.communication_style = None
        self.interest_profile = None
        self.professional_context = None
        self.personal_context = None
        self.current_context = {}
        
        self.load_profile()
    
    def load_profile(self):
        """Load profile from JSON file."""
        if not os.path.exists(self.profile_path):
            print(f"⚠️ No personal profile found at {self.profile_path}")
            print("   Create one using personal_profile_template.md as a guide")
            return
        
        try:
            with open(self.profile_path, 'r') as f:
                profile_data = json.load(f)
            
            # Load communication style
            comm_data = profile_data.get('communication_style', {})
            self.communication_style = CommunicationStyle(
                conversation_style=comm_data.get('conversation_style', 'casual'),
                response_length=comm_data.get('response_length', 'varies'),
                humor_style=comm_data.get('humor_style', 'playful'),
                feedback_style=comm_data.get('feedback_style', 'direct'),
                sass_level=comm_data.get('sass_level', 'medium'),
                curiosity_level=comm_data.get('curiosity_level', 'some'),
                proactivity_level=comm_data.get('proactivity_level', 'medium')
            )
            
            # Load interest profile
            interest_data = profile_data.get('interests', {})
            self.interest_profile = InterestProfile(
                active_interests=interest_data.get('active_interests', {}),
                deep_interest_areas=interest_data.get('deep_interest_areas', []),
                interest_ratings=interest_data.get('interest_ratings', {}),
                learning_style=interest_data.get('learning_style', 'mixed'),
                research_permissions=interest_data.get('research_permissions', {})
            )
            
            # Load professional context
            prof_data = profile_data.get('professional_context', {})
            self.professional_context = ProfessionalContext(
                current_role=prof_data.get('current_role', ''),
                current_projects=prof_data.get('current_projects', []),
                technical_stack=prof_data.get('technical_stack', []),
                professional_challenges=prof_data.get('professional_challenges', []),
                career_goals=prof_data.get('career_goals', []),
                learning_priorities=prof_data.get('learning_priorities', [])
            )
            
            # Load personal context
            personal_data = profile_data.get('personal_context', {})
            self.personal_context = PersonalContext(
                life_situation=personal_data.get('life_situation', {}),
                values_principles=personal_data.get('values_principles', []),
                current_challenges=personal_data.get('current_challenges', []),
                major_goals=personal_data.get('major_goals', [])
            )
            
            # Load current context
            self.current_context = profile_data.get('current_context', {})
            
            print(f"✅ Personal profile loaded successfully")
            print(f"   Communication style: {self.communication_style.conversation_style}")
            print(f"   Active interests: {len(self.interest_profile.active_interests)} categories")
            print(f"   Professional role: {self.professional_context.current_role}")
            
        except Exception as e:
            print(f"❌ Failed to load personal profile: {e}")
    
    def get_context_for_llm(self) -> str:
        """Get formatted context for LLM integration."""
        if not self.communication_style:
            return ""
        
        context_parts = []
        
        # Communication preferences
        context_parts.append(f"User communication style: {self.communication_style.conversation_style}")
        context_parts.append(f"Preferred response length: {self.communication_style.response_length}")
        context_parts.append(f"Humor style: {self.communication_style.humor_style}")
        context_parts.append(f"Sass level preference: {self.communication_style.sass_level}")
        
        # Current interests
        if self.interest_profile.active_interests:
            current_interests = []
            for category, interests in self.interest_profile.active_interests.items():
                current_interests.extend(interests[:2])  # Top 2 per category
            if current_interests:
                context_parts.append(f"Current interests: {', '.join(current_interests[:5])}")
        
        # Professional context
        if self.professional_context.current_role:
            context_parts.append(f"Professional role: {self.professional_context.current_role}")
        
        if self.professional_context.current_projects:
            context_parts.append(f"Current projects: {', '.join(self.professional_context.current_projects[:2])}")
        
        # Learning preferences
        if self.interest_profile.learning_style:
            context_parts.append(f"Learning style: {self.interest_profile.learning_style}")
        
        # Current context
        if self.current_context.get('focus_areas'):
            context_parts.append(f"Current focus: {', '.join(self.current_context['focus_areas'][:2])}")
        
        return "\n".join(context_parts)
    
    def should_auto_research(self, topic: str) -> Optional[bool]:
        """Check if topic should be auto-researched based on permissions."""
        if not self.interest_profile:
            return None
        
        topic_lower = topic.lower()
        
        # Check explicit permissions
        for topic_pattern, permission in self.interest_profile.research_permissions.items():
            if topic_pattern.lower() in topic_lower or topic_lower in topic_pattern.lower():
                if permission == "auto":
                    return True
                elif permission == "never":
                    return False
                # "ask" or "depends" returns None (ask permission)
        
        return None
    
    def get_interest_level(self, topic: str) -> float:
        """Get user's interest level in a topic (0.0-1.0)."""
        if not self.interest_profile:
            return 0.5
        
        topic_lower = topic.lower()
        
        # Check explicit ratings
        for rated_topic, rating in self.interest_profile.interest_ratings.items():
            if rated_topic.lower() in topic_lower or topic_lower in rated_topic.lower():
                return rating / 5.0  # Convert 1-5 to 0.0-1.0
        
        # Check if it's in active interests
        for category, interests in self.interest_profile.active_interests.items():
            for interest in interests:
                if interest.lower() in topic_lower or topic_lower in interest.lower():
                    return 0.8  # High interest for active topics
        
        # Check deep interest areas
        for deep_interest in self.interest_profile.deep_interest_areas:
            if deep_interest.lower() in topic_lower or topic_lower in deep_interest.lower():
                return 0.9  # Very high interest for deep areas
        
        return 0.5  # Default neutral interest
    
    def get_related_interests(self, topic: str) -> List[str]:
        """Find user's interests related to a topic."""
        if not self.interest_profile:
            return []
        
        related = []
        topic_lower = topic.lower()
        
        # Check all active interests
        for category, interests in self.interest_profile.active_interests.items():
            for interest in interests:
                # Simple keyword matching
                if any(word in interest.lower() for word in topic_lower.split()):
                    related.append(interest)
        
        # Check technical stack if it's a tech topic
        if self.professional_context:
            for tech in self.professional_context.technical_stack:
                if any(word in tech.lower() for word in topic_lower.split()):
                    related.append(tech)
        
        return related[:3]  # Return top 3 related interests
    
    def adapt_personality_for_user(self, base_personality_config: Dict) -> Dict:
        """Adapt personality configuration based on user preferences."""
        if not self.communication_style:
            return base_personality_config
        
        adapted_config = base_personality_config.copy()
        
        # Adjust sass level
        sass_mapping = {"low": 0.2, "medium": 0.6, "high": 0.9}
        if self.communication_style.sass_level in sass_mapping:
            adapted_config["personality"]["core_traits"]["sass"] = sass_mapping[self.communication_style.sass_level]
        
        # Adjust humor frequency based on humor style
        humor_mapping = {"professional": 0.3, "dry": 0.5, "playful": 0.8, "warm": 0.7}
        if self.communication_style.humor_style in humor_mapping:
            adapted_config["personality"]["core_traits"]["humor_frequency"] = humor_mapping[self.communication_style.humor_style]
        
        return adapted_config


def create_personal_profile_loader(profile_path: str = "personal_profile.json"):
    """Factory function to create profile loader."""
    return PersonalProfileLoader(profile_path)


def create_sample_profile():
    """Create a sample profile JSON file."""
    sample_profile = {
        "communication_style": {
            "conversation_style": "casual",
            "response_length": "detailed",
            "humor_style": "playful",
            "feedback_style": "direct",
            "sass_level": "medium",
            "curiosity_level": "many",
            "proactivity_level": "high"
        },
        "interests": {
            "active_interests": {
                "technology": ["AI/ML", "web development", "automation"],
                "professional": ["product management", "user experience", "data analysis"],
                "hobbies": ["photography", "cooking", "hiking"]
            },
            "deep_interest_areas": [
                "How AI will change work",
                "Building great user experiences",
                "Sustainable technology"
            ],
            "interest_ratings": {
                "technology": 5,
                "business": 4,
                "science": 3,
                "politics": 2,
                "sports": 2
            },
            "learning_style": "hands-on with examples",
            "research_permissions": {
                "AI/ML": "auto",
                "technology trends": "auto", 
                "politics": "ask",
                "personal topics": "ask"
            }
        },
        "professional_context": {
            "current_role": "Senior Product Manager",
            "current_projects": ["AI integration project", "User analytics dashboard"],
            "technical_stack": ["Python", "React", "SQL", "Figma"],
            "professional_challenges": ["Scaling team processes", "AI adoption strategy"],
            "career_goals": ["Director level", "AI product expertise"],
            "learning_priorities": ["Machine learning applications", "Advanced analytics"]
        },
        "personal_context": {
            "life_situation": {
                "work_life_balance": "Important",
                "family": "Single, focus on career growth"
            },
            "values_principles": [
                "Continuous learning",
                "Building useful products",
                "Helping others grow",
                "Work-life balance"
            ],
            "current_challenges": [
                "Managing complex projects",
                "Staying current with AI trends"
            ],
            "major_goals": [
                "Lead AI product initiatives",
                "Mentor junior team members",
                "Build expertise in ML applications"
            ]
        },
        "current_context": {
            "focus_areas": ["AI project launch", "Team hiring"],
            "stress_level": "moderate",
            "learning_goals": ["Advanced ML concepts", "AI product strategy"],
            "mood": "focused and curious"
        }
    }
    
    with open("personal_profile.json", 'w') as f:
        json.dump(sample_profile, f, indent=2)
    
    print("✅ Sample profile created at personal_profile.json")
    print("   Edit this file to match your preferences and context")


if __name__ == "__main__":
    print("👤 Personal Profile System for PennyGPT")
    print("Creating sample profile...")
    create_sample_profile()
    
    print("\nTesting profile loader...")
    loader = PersonalProfileLoader()
    
    if loader.communication_style:
        print(f"\n📋 LLM Context Preview:")
        print(loader.get_context_for_llm())
        
        print(f"\n🔍 Interest Level Tests:")
        test_topics = ["machine learning", "cooking", "politics", "photography"]
        for topic in test_topics:
            interest = loader.get_interest_level(topic)
            print(f"   {topic}: {interest:.1f}")
