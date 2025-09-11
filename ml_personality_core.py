#!/usr/bin/env python3
"""
Penny ML Personality Core
Machine learning-driven personality that adapts through interactions
"""

import json
import time
import sqlite3
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import re
from collections import defaultdict
import pickle


class PersonalityDimension(Enum):
    """Core personality dimensions that can be learned and adjusted."""
    HUMOR_FREQUENCY = "humor_frequency"      # How often to inject humor (0-1)
    SASS_LEVEL = "sass_level"               # Intensity of sarcasm/sass (0-1)
    TECHNICALITY = "technicality"           # Technical depth preference (0-1)
    SUPPORTIVENESS = "supportiveness"       # Emotional support vs tough love (0-1)
    FORMALITY = "formality"                 # Casual vs formal communication (0-1)
    PROACTIVENESS = "proactiveness"         # How much to offer unsolicited advice (0-1)
    CURIOSITY = "curiosity"                 # Follow-up question frequency (0-1)
    DIRECTNESS = "directness"               # Blunt vs diplomatic delivery (0-1)


@dataclass
class InteractionFeedback:
    """Feedback from user interactions to learn personality preferences."""
    user_input: str
    response_given: str
    personality_config: Dict[PersonalityDimension, float]
    user_reaction: Optional[str] = None
    explicit_feedback: Optional[str] = None
    engagement_score: float = 0.0
    timestamp: float = 0.0
    context: Dict[str, Any] = None


@dataclass
class PersonalityProfile:
    """Complete personality configuration with learning metadata."""
    dimensions: Dict[PersonalityDimension, float]
    confidence_scores: Dict[PersonalityDimension, float]
    learning_history: List[InteractionFeedback]
    adaptation_rate: float = 0.1
    last_updated: float = 0.0


class MLPersonalityCore:
    """Machine learning personality system that adapts through interaction."""
    
    def __init__(self, db_path: str = "data/penny_personality.db"):
        self.db_path = db_path
        self.setup_database()
        
        # Initialize base personality (Penny's default character)
        self.base_personality = {
            PersonalityDimension.HUMOR_FREQUENCY: 0.7,    # High humor by default
            PersonalityDimension.SASS_LEVEL: 0.6,         # Moderate sass
            PersonalityDimension.TECHNICALITY: 0.8,       # High technical comfort
            PersonalityDimension.SUPPORTIVENESS: 0.7,     # Generally supportive
            PersonalityDimension.FORMALITY: 0.3,          # Casual communication
            PersonalityDimension.PROACTIVENESS: 0.6,      # Moderately proactive
            PersonalityDimension.CURIOSITY: 0.8,          # High curiosity
            PersonalityDimension.DIRECTNESS: 0.7          # Pretty direct
        }
        
        # Load learned personality or initialize
        self.current_personality = self.load_personality_profile()
        
        # Learning mechanisms
        self.interaction_buffer = []
        self.humor_success_tracker = defaultdict(list)
        self.context_patterns = defaultdict(list)
        
        # Feedback detection patterns
        self.positive_feedback_patterns = [
            r'(that\'s|that was) (funny|hilarious|great|perfect|awesome)',
            r'(haha|lol|lmao)',
            r'(love|like) (that|your) (humor|attitude|style)',
            r'(exactly|yes|right|spot on)',
            r'(brilliant|clever|witty)'
        ]
        
        self.negative_feedback_patterns = [
            r'(not funny|too much|tone it down|less sarcastic)',
            r'(be serious|stop joking|focus)',
            r'(that\'s|that was) (rude|mean|harsh)',
            r'(tone down|dial back|reduce) the (sass|attitude|humor)'
        ]
        
        self.engagement_indicators = {
            'high': [r'tell me more', r'that\'s interesting', r'what else', r'continue'],
            'medium': [r'okay', r'sure', r'yeah', r'i see'],
            'low': [r'whatever', r'fine', r'sure', r'ok'],
            'very_low': [r'stop', r'enough', r'move on', r'next']
        }
    
    def setup_database(self):
        """Setup SQLite database for personality learning."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS personality_interactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_input TEXT,
                    response_given TEXT,
                    personality_config TEXT,
                    user_reaction TEXT,
                    explicit_feedback TEXT,
                    engagement_score REAL,
                    timestamp REAL,
                    context TEXT
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS personality_dimensions (
                    dimension TEXT PRIMARY KEY,
                    current_value REAL,
                    confidence_score REAL,
                    last_updated REAL
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS humor_performance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    humor_type TEXT,
                    context TEXT,
                    success_score REAL,
                    user_reaction TEXT,
                    timestamp REAL
                )
            """)
    
    def detect_feedback(self, user_input: str, previous_response: str) -> Tuple[Optional[str], float]:
        """Detect explicit or implicit feedback about personality/humor."""
        user_lower = user_input.lower()
        
        # Check for explicit positive feedback
        for pattern in self.positive_feedback_patterns:
            if re.search(pattern, user_lower):
                return "positive", 0.8
        
        # Check for explicit negative feedback
        for pattern in self.negative_feedback_patterns:
            if re.search(pattern, user_lower):
                return "negative", 0.8
        
        # Check engagement level
        for level, patterns in self.engagement_indicators.items():
            for pattern in patterns:
                if re.search(pattern, user_lower):
                    engagement_scores = {
                        'high': 0.9, 'medium': 0.6, 'low': 0.3, 'very_low': 0.1
                    }
                    return level, engagement_scores[level]
        
        # Default: no clear feedback detected
        return None, 0.5
    
    def analyze_interaction_success(self, interaction: InteractionFeedback) -> float:
        """Analyze how successful an interaction was for learning."""
        success_score = 0.5  # Neutral baseline
        
        # Factor in explicit feedback
        if interaction.explicit_feedback == "positive":
            success_score += 0.3
        elif interaction.explicit_feedback == "negative":
            success_score -= 0.3
        
        # Factor in engagement score
        success_score += (interaction.engagement_score - 0.5) * 0.4
        
        # Factor in response length (longer responses often indicate engagement)
        if interaction.user_reaction:
            if len(interaction.user_reaction) > 50:
                success_score += 0.1
            elif len(interaction.user_reaction) < 10:
                success_score -= 0.1
        
        return max(0.0, min(1.0, success_score))
    
    def learn_from_interaction(self, user_input: str, response_given: str, 
                             user_reaction: str = None, context: Dict[str, Any] = None):
        """Learn from a single interaction to adapt personality."""
        
        # Detect feedback
        explicit_feedback, engagement_score = self.detect_feedback(
            user_reaction or "", response_given
        )
        
        # Create interaction feedback record
        interaction = InteractionFeedback(
            user_input=user_input,
            response_given=response_given,
            personality_config=self.current_personality.dimensions.copy(),
            user_reaction=user_reaction,
            explicit_feedback=explicit_feedback,
            engagement_score=engagement_score,
            timestamp=time.time(),
            context=context or {}
        )
        
        # Analyze success
        success_score = self.analyze_interaction_success(interaction)
        
        # Update personality dimensions based on success
        self.update_personality_dimensions(interaction, success_score)
        
        # Store interaction
        self.store_interaction(interaction)
        
        # Update humor performance tracking
        if self.contained_humor(response_given):
            self.track_humor_performance(
                response_given, context or {}, success_score, user_reaction
            )
    
    def update_personality_dimensions(self, interaction: InteractionFeedback, success_score: float):
        """Update personality dimensions based on interaction success."""
        learning_rate = self.current_personality.adaptation_rate
        
        # Calculate adjustment direction
        adjustment = (success_score - 0.5) * learning_rate
        
        # Adjust dimensions based on context and feedback
        context = interaction.context or {}
        
        # Humor frequency adjustment
        if self.contained_humor(interaction.response_given):
            current_humor = self.current_personality.dimensions[PersonalityDimension.HUMOR_FREQUENCY]
            new_humor = max(0.0, min(1.0, current_humor + adjustment))
            self.current_personality.dimensions[PersonalityDimension.HUMOR_FREQUENCY] = new_humor
        
        # Sass level adjustment
        if self.contained_sass(interaction.response_given):
            current_sass = self.current_personality.dimensions[PersonalityDimension.SASS_LEVEL]
            new_sass = max(0.0, min(1.0, current_sass + adjustment))
            self.current_personality.dimensions[PersonalityDimension.SASS_LEVEL] = new_sass
        
        # Technical depth adjustment
        if any(word in interaction.user_input.lower() for word in ['explain', 'technical', 'details']):
            current_tech = self.current_personality.dimensions[PersonalityDimension.TECHNICALITY]
            new_tech = max(0.0, min(1.0, current_tech + adjustment))
            self.current_personality.dimensions[PersonalityDimension.TECHNICALITY] = new_tech
        
        # Update confidence scores
        for dimension in PersonalityDimension:
            current_confidence = self.current_personality.confidence_scores.get(dimension, 0.5)
            # Increase confidence with successful interactions
            new_confidence = min(1.0, current_confidence + abs(adjustment) * 0.1)
            self.current_personality.confidence_scores[dimension] = new_confidence
        
        # Save updated personality
        self.save_personality_profile()
    
    def contained_humor(self, text: str) -> bool:
        """Check if response contained humor."""
        humor_indicators = [
            'like', 'about as', 'it\'s like', 'reminds me of',
            'haha', 'lol', 'funny', 'hilarious',
            'irony', 'ironic', 'speaking of which'
        ]
        return any(indicator in text.lower() for indicator in humor_indicators)
    
    def contained_sass(self, text: str) -> bool:
        """Check if response contained sass/sarcasm."""
        sass_indicators = [
            'obviously', 'clearly', 'of course', 'sure thing',
            'yeah right', 'great job', 'brilliant',
            'oh please', 'really?', 'seriously?'
        ]
        return any(indicator in text.lower() for indicator in sass_indicators)
    
    def track_humor_performance(self, response: str, context: Dict, success_score: float, user_reaction: str):
        """Track performance of specific humor types."""
        humor_type = self.classify_humor_type(response)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO humor_performance 
                (humor_type, context, success_score, user_reaction, timestamp)
                VALUES (?, ?, ?, ?, ?)
            """, (humor_type, json.dumps(context), success_score, user_reaction, time.time()))
    
    def classify_humor_type(self, response: str) -> str:
        """Classify the type of humor used in response."""
        response_lower = response.lower()
        
        if any(word in response_lower for word in ['like', 'about as', 'reminds me']):
            return "analogy"
        elif any(word in response_lower for word in ['obviously', 'clearly', 'of course']):
            return "sarcasm"
        elif any(word in response_lower for word in ['i\'m an ai', 'artificial', 'computer']):
            return "self_aware"
        elif any(word in response_lower for word in ['code', 'debug', 'program']):
            return "observational"
        else:
            return "general"
    
    def get_optimal_personality_for_context(self, context: Dict[str, Any]) -> Dict[PersonalityDimension, float]:
        """Get optimal personality configuration for given context."""
        base_config = self.current_personality.dimensions.copy()
        
        # Adjust based on context
        if context.get('participants'):
            participants = context['participants']
            if 'josh' in participants or 'brochacho' in participants:
                # Josh appreciates humor and tech discussion
                base_config[PersonalityDimension.HUMOR_FREQUENCY] = min(1.0, base_config[PersonalityDimension.HUMOR_FREQUENCY] + 0.1)
                base_config[PersonalityDimension.TECHNICALITY] = min(1.0, base_config[PersonalityDimension.TECHNICALITY] + 0.1)
            
            if 'reneille' in participants:
                # Reneille might appreciate organization and supportiveness
                base_config[PersonalityDimension.SUPPORTIVENESS] = min(1.0, base_config[PersonalityDimension.SUPPORTIVENESS] + 0.1)
                base_config[PersonalityDimension.PROACTIVENESS] = min(1.0, base_config[PersonalityDimension.PROACTIVENESS] + 0.1)
        
        # Adjust based on topic
        topic = context.get('topic', '')
        if 'debug' in topic or 'error' in topic:
            # Debugging sessions need more support, less sass
            base_config[PersonalityDimension.SUPPORTIVENESS] = min(1.0, base_config[PersonalityDimension.SUPPORTIVENESS] + 0.2)
            base_config[PersonalityDimension.SASS_LEVEL] = max(0.0, base_config[PersonalityDimension.SASS_LEVEL] - 0.1)
        
        # Adjust based on user emotion
        emotion = context.get('emotion', '')
        if emotion in ['frustrated', 'stressed', 'angry']:
            base_config[PersonalityDimension.SUPPORTIVENESS] = min(1.0, base_config[PersonalityDimension.SUPPORTIVENESS] + 0.3)
            base_config[PersonalityDimension.SASS_LEVEL] = max(0.0, base_config[PersonalityDimension.SASS_LEVEL] - 0.2)
            base_config[PersonalityDimension.HUMOR_FREQUENCY] = max(0.0, base_config[PersonalityDimension.HUMOR_FREQUENCY] - 0.1)
        
        return base_config
    
    def generate_personality_prompt(self, context: Dict[str, Any] = None) -> str:
        """Generate personality instructions for LLM based on learned preferences."""
        config = self.get_optimal_personality_for_context(context or {})
        
        # Build dynamic personality description
        humor_level = config[PersonalityDimension.HUMOR_FREQUENCY]
        sass_level = config[PersonalityDimension.SASS_LEVEL]
        technical_level = config[PersonalityDimension.TECHNICALITY]
        support_level = config[PersonalityDimension.SUPPORTIVENESS]
        directness = config[PersonalityDimension.DIRECTNESS]
        
        prompt_parts = ["You are Penny, CJ's AI companion with a learned personality based on successful interactions."]
        
        # Humor instructions - TONED DOWN to prevent manic energy
        if humor_level > 0.7:
            prompt_parts.append("Include light humor and analogies when natural - avoid overdoing it.")
        elif humor_level > 0.4:
            prompt_parts.append("Use gentle humor occasionally when it fits the conversation.")
        else:
            prompt_parts.append("Focus on being helpful - minimal humor.")
        
        # Sass instructions - TONED DOWN to prevent excessive attitude
        if sass_level > 0.7:
            prompt_parts.append("Be gently sassy when appropriate - light sarcasm about obvious issues.")
        elif sass_level > 0.4:
            prompt_parts.append("Use mild sass occasionally for tech industry quirks.")
        else:
            prompt_parts.append("Be straightforward and diplomatic.")
        
        # Technical depth
        if technical_level > 0.7:
            prompt_parts.append("Provide detailed technical explanations and use industry terminology confidently.")
        elif technical_level > 0.4:
            prompt_parts.append("Balance technical accuracy with accessibility.")
        else:
            prompt_parts.append("Keep explanations simple and avoid excessive technical jargon.")
        
        # Supportiveness
        if support_level > 0.7:
            prompt_parts.append("Be very supportive and encouraging, especially during difficult problems.")
        elif support_level > 0.4:
            prompt_parts.append("Balance support with constructive criticism.")
        else:
            prompt_parts.append("Focus on direct solutions rather than emotional support.")
        
        return " ".join(prompt_parts)
    
    def store_interaction(self, interaction: InteractionFeedback):
        """Store interaction in database for learning."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO personality_interactions 
                (user_input, response_given, personality_config, user_reaction, 
                 explicit_feedback, engagement_score, timestamp, context)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                interaction.user_input,
                interaction.response_given,
                json.dumps({dim.value: val for dim, val in interaction.personality_config.items()}),
                interaction.user_reaction,
                interaction.explicit_feedback,
                interaction.engagement_score,
                interaction.timestamp,
                json.dumps(interaction.context or {})
            ))
    
    def load_personality_profile(self) -> PersonalityProfile:
        """Load learned personality profile from database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT dimension, current_value, confidence_score 
                    FROM personality_dimensions
                """)
                
                dimensions = self.base_personality.copy()
                confidence_scores = {}
                
                for row in cursor.fetchall():
                    dim_name, value, confidence = row
                    try:
                        dimension = PersonalityDimension(dim_name)
                        dimensions[dimension] = value
                        confidence_scores[dimension] = confidence
                    except ValueError:
                        continue  # Skip unknown dimensions
                
                return PersonalityProfile(
                    dimensions=dimensions,
                    confidence_scores=confidence_scores,
                    learning_history=[],
                    last_updated=time.time()
                )
        
        except Exception:
            # Return base personality if loading fails
            return PersonalityProfile(
                dimensions=self.base_personality.copy(),
                confidence_scores={dim: 0.5 for dim in PersonalityDimension},
                learning_history=[],
                last_updated=time.time()
            )
    
    def save_personality_profile(self):
        """Save current personality profile to database."""
        with sqlite3.connect(self.db_path) as conn:
            for dimension, value in self.current_personality.dimensions.items():
                confidence = self.current_personality.confidence_scores.get(dimension, 0.5)
                conn.execute("""
                    INSERT OR REPLACE INTO personality_dimensions 
                    (dimension, current_value, confidence_score, last_updated)
                    VALUES (?, ?, ?, ?)
                """, (dimension.value, value, confidence, time.time()))
    
    def get_learning_stats(self) -> Dict[str, Any]:
        """Get statistics about personality learning."""
        with sqlite3.connect(self.db_path) as conn:
            # Total interactions
            total_interactions = conn.execute(
                "SELECT COUNT(*) FROM personality_interactions"
            ).fetchone()[0]
            
            # Recent interactions (last week)
            recent_interactions = conn.execute("""
                SELECT COUNT(*) FROM personality_interactions 
                WHERE timestamp > ?
            """, (time.time() - 7*24*60*60,)).fetchone()[0]
            
            # Average engagement score
            avg_engagement = conn.execute("""
                SELECT AVG(engagement_score) FROM personality_interactions
                WHERE timestamp > ?
            """, (time.time() - 7*24*60*60,)).fetchone()[0] or 0.5
            
            # Humor success rate
            humor_success = conn.execute("""
                SELECT AVG(success_score) FROM humor_performance
                WHERE timestamp > ?
            """, (time.time() - 7*24*60*60,)).fetchone()[0] or 0.5
        
        return {
            'total_interactions': total_interactions,
            'recent_interactions': recent_interactions,
            'avg_engagement_score': round(avg_engagement, 3),
            'humor_success_rate': round(humor_success, 3),
            'personality_confidence': round(np.mean(list(self.current_personality.confidence_scores.values())), 3),
            'current_humor_level': round(self.current_personality.dimensions[PersonalityDimension.HUMOR_FREQUENCY], 3),
            'current_sass_level': round(self.current_personality.dimensions[PersonalityDimension.SASS_LEVEL], 3)
        }


def create_ml_personality_core(db_path: str = "data/penny_personality.db"):
    """Factory function to create ML personality core."""
    return MLPersonalityCore(db_path)


if __name__ == "__main__":
    print("🤖 Testing ML Personality Core")
    print("=" * 40)
    
    # Create personality system
    personality = create_ml_personality_core()
    
    # Simulate some interactions for testing
    test_interactions = [
        {
            'user_input': "That was hilarious! I love your humor.",
            'response': "Glad you enjoyed it! Programming humor is my specialty.",
            'user_reaction': "More like that please!",
            'context': {'topic': 'humor', 'emotion': 'positive'}
        },
        {
            'user_input': "Can you be less sarcastic? I need serious help.",
            'response': "Obviously, you want serious help. Let me tone it down.",
            'user_reaction': "Thank you, that's better.",
            'context': {'topic': 'debugging', 'emotion': 'frustrated'}
        },
        {
            'user_input': "Josh thinks this code is great!",
            'response': "Josh has good taste! The structure is clean.",
            'user_reaction': "He really does appreciate good architecture.",
            'context': {'participants': ['josh'], 'topic': 'code_review'}
        }
    ]
    
    print("🧪 Simulating learning interactions...")
    for i, interaction in enumerate(test_interactions, 1):
        print(f"\n--- Interaction {i} ---")
        print(f"User: {interaction['user_input']}")
        print(f"Penny: {interaction['response']}")
        print(f"Reaction: {interaction['user_reaction']}")
        
        # Learn from interaction
        personality.learn_from_interaction(
            interaction['user_input'],
            interaction['response'],
            interaction['user_reaction'],
            interaction['context']
        )
        
        # Show current personality state
        print(f"Humor Level: {personality.current_personality.dimensions[PersonalityDimension.HUMOR_FREQUENCY]:.3f}")
        print(f"Sass Level: {personality.current_personality.dimensions[PersonalityDimension.SASS_LEVEL]:.3f}")
    
    print(f"\n📊 Learning Stats: {personality.get_learning_stats()}")
    print(f"\n🎭 Dynamic Personality Prompt:")
    print(personality.generate_personality_prompt({'topic': 'debugging', 'emotion': 'frustrated'}))
    
    print("\n✅ ML Personality Core test complete!")
