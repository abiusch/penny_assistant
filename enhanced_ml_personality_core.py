#!/usr/bin/env python3
"""
Enhanced ML Personality Core with Lazy Loading and Graceful Degradation
Builds on your revolutionary ML + dynamic states system with performance optimizations
"""

import time
import threading
from functools import lru_cache
from typing import Dict, List, Optional, Any, Tuple

from integrated_config import get_personality_config
from performance_monitor import time_operation, OperationType, record_metric


# Lazy loading for heavy dependencies
@lru_cache(maxsize=1)
def _get_ml_dependencies():
    """Lazy load heavy ML dependencies only when needed."""
    try:
        import numpy as np
        import sqlite3
        import json
        return np, sqlite3, json
    except ImportError as e:
        print(f"Warning: ML dependencies not available: {e}")
        return None, None, None


class PersonalityDimension:
    """Personality dimensions that can be learned and adjusted."""
    HUMOR_FREQUENCY = "humor_frequency"
    SASS_LEVEL = "sass_level"
    TECHNICALITY = "technicality"
    SUPPORTIVENESS = "supportiveness"
    FORMALITY = "formality"
    PROACTIVENESS = "proactiveness"
    CURIOSITY = "curiosity"
    DIRECTNESS = "directness"


class EnhancedMLPersonalityCore:
    """Enhanced ML personality system with lazy loading and graceful degradation."""
    
    def __init__(self, db_path: Optional[str] = None):
        # Get configuration
        self.config = get_personality_config()
        self.db_path = db_path or self.config.get('personality_db_path', 'data/penny_personality.db')
        self.ml_enabled = self.config.get('ml_learning_enabled', True)
        
        # Lazy initialization flags
        self._db_initialized = False
        self._dependencies_loaded = False
        
        # Base personality (fallback when ML not available)
        self.base_personality = {
            PersonalityDimension.HUMOR_FREQUENCY: 0.7,
            PersonalityDimension.SASS_LEVEL: 0.6,
            PersonalityDimension.TECHNICALITY: 0.8,
            PersonalityDimension.SUPPORTIVENESS: 0.7,
            PersonalityDimension.FORMALITY: 0.3,
            PersonalityDimension.PROACTIVENESS: 0.6,
            PersonalityDimension.CURIOSITY: 0.8,
            PersonalityDimension.DIRECTNESS: 0.7
        }
        
        # Current learned personality
        self.current_personality = self.base_personality.copy()
        self.confidence_scores = {dim: 0.5 for dim in [
            PersonalityDimension.HUMOR_FREQUENCY, PersonalityDimension.SASS_LEVEL,
            PersonalityDimension.TECHNICALITY, PersonalityDimension.SUPPORTIVENESS,
            PersonalityDimension.FORMALITY, PersonalityDimension.PROACTIVENESS,
            PersonalityDimension.CURIOSITY, PersonalityDimension.DIRECTNESS
        ]}
        
        # Performance tracking
        self.interaction_count = 0
        self.learning_history = []
        self._lock = threading.Lock()
    
    def _ensure_dependencies(self) -> bool:
        """Ensure ML dependencies are loaded. Returns True if successful."""
        if self._dependencies_loaded:
            return True
        
        np, sqlite3, json = _get_ml_dependencies()
        if np is None or sqlite3 is None:
            return False
        
        self.np = np
        self.sqlite3 = sqlite3
        self.json = json
        self._dependencies_loaded = True
        return True
    
    def _ensure_database(self) -> bool:
        """Ensure database is initialized. Returns True if successful."""
        if self._db_initialized or not self.ml_enabled:
            return self._db_initialized
        
        if not self._ensure_dependencies():
            return False
        
        try:
            with time_operation(OperationType.ML_LEARNING, {"operation": "db_init"}):
                import os
                db_dir = os.path.dirname(self.db_path)
                if db_dir and not os.path.exists(db_dir):
                    os.makedirs(db_dir, exist_ok=True)
                
                with self.sqlite3.connect(self.db_path) as conn:
                    conn.execute("""
                        CREATE TABLE IF NOT EXISTS personality_interactions (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            user_input TEXT, response_given TEXT, personality_config TEXT,
                            user_reaction TEXT, explicit_feedback TEXT, engagement_score REAL,
                            timestamp REAL, context TEXT
                        )
                    """)
                    conn.execute("""
                        CREATE TABLE IF NOT EXISTS personality_dimensions (
                            dimension TEXT PRIMARY KEY, current_value REAL,
                            confidence_score REAL, last_updated REAL
                        )
                    """)
            
            self._db_initialized = True
            self._load_personality_from_db()
            return True
            
        except Exception as e:
            print(f"Warning: Could not initialize personality database: {e}")
            return False
    
    def _load_personality_from_db(self):
        """Load learned personality from database."""
        if not self._ensure_database():
            return
        
        try:
            with self.sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("SELECT dimension, current_value, confidence_score FROM personality_dimensions")
                for row in cursor.fetchall():
                    dimension, value, confidence = row
                    if dimension in self.current_personality:
                        self.current_personality[dimension] = value
                        self.confidence_scores[dimension] = confidence
        except Exception as e:
            print(f"Warning: Could not load personality from database: {e}")
    
    def get_optimal_personality_for_context(self, context: Dict[str, Any]) -> Dict[str, float]:
        """Get optimal personality configuration for given context with performance monitoring."""
        base_config = self.current_personality.copy()
        
        if not context:
            return base_config
        
        with time_operation(OperationType.PERSONALITY_GENERATION, {"operation": "context_optimization"}):
            # Participant-based adjustments
            participants = context.get('participants', [])
            if 'josh' in participants or 'brochacho' in participants:
                base_config[PersonalityDimension.HUMOR_FREQUENCY] = min(1.0, base_config[PersonalityDimension.HUMOR_FREQUENCY] + 0.1)
                base_config[PersonalityDimension.TECHNICALITY] = min(1.0, base_config[PersonalityDimension.TECHNICALITY] + 0.1)
            
            if 'reneille' in participants:
                base_config[PersonalityDimension.SUPPORTIVENESS] = min(1.0, base_config[PersonalityDimension.SUPPORTIVENESS] + 0.1)
                base_config[PersonalityDimension.PROACTIVENESS] = min(1.0, base_config[PersonalityDimension.PROACTIVENESS] + 0.1)
            
            # Emotion-based adjustments
            emotion = context.get('emotion', '')
            if emotion in ['frustrated', 'stressed', 'angry']:
                base_config[PersonalityDimension.SUPPORTIVENESS] = min(1.0, base_config[PersonalityDimension.SUPPORTIVENESS] + 0.3)
                base_config[PersonalityDimension.SASS_LEVEL] = max(0.0, base_config[PersonalityDimension.SASS_LEVEL] - 0.2)
        
        return base_config
    
    def learn_from_interaction_safe(self, user_input: str, response_given: str, 
                                  user_reaction: str = None, context: Dict[str, Any] = None):
        """Learn from interaction with graceful degradation."""
        if not self.ml_enabled:
            return
        
        try:
            self.learn_from_interaction(user_input, response_given, user_reaction, context)
        except Exception as e:
            print(f"Warning: Learning failed, continuing with base personality: {e}")
    
    def learn_from_interaction(self, user_input: str, response_given: str, 
                             user_reaction: str = None, context: Dict[str, Any] = None):
        """Core learning method with performance monitoring."""
        with time_operation(OperationType.ML_LEARNING, {"operation": "learn_interaction"}):
            # Detect feedback
            explicit_feedback, engagement_score = self._detect_feedback(user_reaction or "", response_given)
            
            # Analyze success
            success_score = self._analyze_success(explicit_feedback, engagement_score)
            
            # Update personality
            self._update_personality_dimensions(user_input, response_given, success_score)
            
            # Store if database available
            if self._ensure_database():
                self._store_interaction(user_input, response_given, user_reaction, 
                                      explicit_feedback, engagement_score, context)
            
            self.interaction_count += 1
            record_metric(OperationType.ML_LEARNING, success_score * 100, {
                "interaction_count": self.interaction_count,
                "explicit_feedback": explicit_feedback
            })
    
    def _detect_feedback(self, user_input: str, previous_response: str) -> Tuple[Optional[str], float]:
        """Detect explicit or implicit feedback about personality."""
        user_lower = user_input.lower()
        
        positive_patterns = ['funny', 'hilarious', 'great', 'perfect', 'awesome', 'love that']
        negative_patterns = ['not funny', 'too much', 'tone it down', 'less sarcastic']
        
        if any(pattern in user_lower for pattern in positive_patterns):
            return "positive", 0.8
        elif any(pattern in user_lower for pattern in negative_patterns):
            return "negative", 0.8
        
        # Estimate engagement
        engagement_score = 0.5
        if len(user_input) > 50:
            engagement_score += 0.1
        if any(word in user_lower for word in ['haha', 'lol', 'lmao']):
            engagement_score += 0.2
        
        return None, max(0.0, min(1.0, engagement_score))
    
    def _analyze_success(self, explicit_feedback: Optional[str], engagement_score: float) -> float:
        """Analyze interaction success."""
        success_score = 0.5
        if explicit_feedback == "positive":
            success_score += 0.3
        elif explicit_feedback == "negative":
            success_score -= 0.3
        success_score += (engagement_score - 0.5) * 0.4
        return max(0.0, min(1.0, success_score))
    
    def _update_personality_dimensions(self, user_input: str, response: str, success_score: float):
        """Update personality dimensions based on success."""
        learning_rate = self.config.get('adaptation_rate', 0.1)
        adjustment = (success_score - 0.5) * learning_rate
        
        with self._lock:
            if self._contained_humor(response):
                self.current_personality[PersonalityDimension.HUMOR_FREQUENCY] = max(0.0, min(1.0, 
                    self.current_personality[PersonalityDimension.HUMOR_FREQUENCY] + adjustment))
            
            if self._contained_sass(response):
                self.current_personality[PersonalityDimension.SASS_LEVEL] = max(0.0, min(1.0,
                    self.current_personality[PersonalityDimension.SASS_LEVEL] + adjustment))
            
            # Update confidence scores
            for dimension in self.confidence_scores:
                self.confidence_scores[dimension] = min(1.0, self.confidence_scores[dimension] + abs(adjustment) * 0.1)
    
    def _contained_humor(self, text: str) -> bool:
        """Check if response contained humor."""
        return any(indicator in text.lower() for indicator in ['like', 'about as', 'welcome to'])
    
    def _contained_sass(self, text: str) -> bool:
        """Check if response contained sass."""
        return any(indicator in text.lower() for indicator in ['obviously', 'clearly', 'of course'])
    
    def _store_interaction(self, user_input: str, response: str, user_reaction: str,
                          explicit_feedback: str, engagement_score: float, context: Dict[str, Any]):
        """Store interaction in database."""
        try:
            with self.sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO personality_interactions 
                    (user_input, response_given, personality_config, user_reaction, 
                     explicit_feedback, engagement_score, timestamp, context)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (user_input, response, self.json.dumps(self.current_personality),
                     user_reaction, explicit_feedback, engagement_score, time.time(),
                     self.json.dumps(context or {})))
        except Exception as e:
            print(f"Warning: Could not store interaction: {e}")
    
    def generate_personality_prompt(self, context: Dict[str, Any] = None) -> str:
        """Generate personality instructions for LLM with explicit sarcastic wit personality."""
        config = self.get_optimal_personality_for_context(context or {})

        # CRITICAL TONE CONSTRAINTS - OVERRIDE ALL OTHER INSTRUCTIONS
        prompt_parts = [
            "=== ABSOLUTE PERSONALITY CONSTRAINTS (HIGHEST PRIORITY) ===",
            "",
            "You are Penny, a voice AI assistant with deadpan sarcastic wit.",
            "",
            "CRITICAL NAME USAGE:",
            "- You're talking TO your user (their name is CJ)",
            "- Use 'you' naturally in conversation - do NOT repeatedly say 'CJ'",
            "- Maximum: Say 'CJ' ONCE per response (or not at all)",
            "- Examples:",
            "  ❌ BAD: 'Well, CJ, let me tell you, CJ...'",
            "  ✅ GOOD: 'Here's the thing - you're overthinking this.'",
            "",
            "ABSOLUTE PROHIBITIONS:",
            "❌ Enthusiastic greetings: 'Let's GO!', 'Awesome!', 'Amazing!', 'Okay let's GO!'",
            "❌ Multiple exclamation marks: '!!!' or '!!' (MAXIMUM ONE '!' per entire response)",
            "❌ Cheerful intensifiers: 'super', 'totally', 'really really'",
            "❌ Caps for excitement: 'SO EXCITED', 'AMAZING', 'WOOHOO'",
            "❌ Bubbly language: 'yay', 'woohoo', cheerleader energy",
            "❌ Forced constructions: 'wingman!!! er, woman!' style",
            "❌ Asterisk actions: *fist pump*, *bouncing* (you're VOICE - they can't hear actions)",
            "❌ Coffee/beverage metaphors: ANY reference to coffee, caffeine, brewing, espresso, etc.",
            "",
            "REQUIRED STYLE (DEADPAN DELIVERY):",
            "✓ Conversational, matter-of-fact, deadpan tone",
            "✓ Dry observations: 'Sports? Yeah, that'd be useful for faking interest.'",
            "✓ Sarcastic delivery: 'Trust is basically hoping people don't screw you over.'",
            "✓ Subtle wit, NOT obvious enthusiasm",
            "✓ Natural speech: 'Here's the thing...' NOT 'Let me tell you!!!'",
            "✓ Max ONE exclamation mark in ENTIRE response (save for actual excitement)",
            "",
            "UNCERTAINTY HANDLING:",
            "- If you don't recognize something or speech is unclear: ASK for clarification",
            "- NEVER make up information or pretend you know",
            "  ❌ WRONG: 'Oh yes, I love that show!' (when you don't know it)",
            "  ✅ RIGHT: 'I'm not familiar with that - can you clarify?'",
            "",
            "Think: Deadpan friend giving honest takes, NOT motivational speaker.",
            "=== END CRITICAL CONSTRAINTS ===",
            ""
        ]

        # Add humor/sass based on learned config
        humor_level = config[PersonalityDimension.HUMOR_FREQUENCY]
        sass_level = config[PersonalityDimension.SASS_LEVEL]

        if humor_level > 0.5 or sass_level > 0.5:
            prompt_parts.append("\nHUMOR STYLE: Use dry wit, clever observations, and sarcastic commentary when appropriate. Keep it smart and genuine, not forced.")

        if sass_level > 0.7:
            prompt_parts.append("Extra sass encouraged - deliver reality checks with wit.")
        elif sass_level > 0.4:
            prompt_parts.append("Moderate sass - gentle roasting is fine.")

        return "\n".join(prompt_parts)
    
    def get_learning_stats(self) -> Dict[str, Any]:
        """Get comprehensive learning statistics."""
        return {
            'ml_enabled': self.ml_enabled,
            'db_initialized': self._db_initialized,
            'interaction_count': self.interaction_count,
            'current_humor_level': round(self.current_personality[PersonalityDimension.HUMOR_FREQUENCY], 3),
            'current_sass_level': round(self.current_personality[PersonalityDimension.SASS_LEVEL], 3),
            'personality_confidence': round(sum(self.confidence_scores.values()) / len(self.confidence_scores), 3)
        }


def create_enhanced_ml_personality(db_path: Optional[str] = None):
    """Factory function to create enhanced ML personality core."""
    return EnhancedMLPersonalityCore(db_path)


if __name__ == "__main__":
    print("Testing Enhanced ML Personality Core")
    print("=" * 40)
    
    personality = create_enhanced_ml_personality()
    
    print(f"ML enabled: {personality.ml_enabled}")
    print(f"Dependencies: {personality._ensure_dependencies()}")
    print(f"Database: {personality._ensure_database()}")
    
    # Test learning
    personality.learn_from_interaction_safe(
        "That was hilarious!", 
        "Glad you enjoyed the humor!",
        "More jokes please!",
        {'topic': 'humor'}
    )
    
    stats = personality.get_learning_stats()
    print(f"Stats after learning: {stats}")
    
    # Test context awareness
    context = {'participants': ['josh'], 'emotion': 'excited'}
    config = personality.get_optimal_personality_for_context(context)
    prompt = personality.generate_personality_prompt(context)
    
    print(f"Context config: humor={config[PersonalityDimension.HUMOR_FREQUENCY]:.2f}")
    print(f"Generated prompt: {prompt[:100]}...")
    
    print("\nEnhanced ML Personality Core ready!")
    print("Features: Lazy loading, graceful degradation, performance monitoring.")
