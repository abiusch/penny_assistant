#!/usr/bin/env python3
"""
Comprehensive Personality Tracking System
Extends adaptive sass learning to track multiple personality dimensions
"""

import re
import sqlite3
import asyncio
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass
from pathlib import Path
import sys

# Add src/personality to path for cache import
sys.path.insert(0, str(Path(__file__).parent / "src" / "personality"))
try:
    # Try multiple import paths
    try:
        from src.personality.personality_state_cache import get_cache
    except ImportError:
        from personality_state_cache import get_cache
    CACHE_AVAILABLE = True
except ImportError:
    CACHE_AVAILABLE = False
    # Silently fall back - not an error, just less optimal

@dataclass
class PersonalityDimension:
    """Represents a trackable personality dimension"""
    name: str
    current_value: Union[float, str]
    confidence: float
    last_updated: datetime
    learning_rate: float
    value_type: str  # 'continuous', 'categorical'

    def to_dict(self) -> dict:
        """Convert PersonalityDimension to JSON-serializable dict"""
        return {
            'name': self.name,
            'current_value': self.current_value,
            'confidence': self.confidence,
            'value_type': self.value_type,
            'learning_rate': self.learning_rate,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'PersonalityDimension':
        """Create PersonalityDimension from dict"""
        return cls(
            name=data['name'],
            current_value=data['current_value'],
            confidence=data['confidence'],
            last_updated=datetime.fromisoformat(data['last_updated']) if data.get('last_updated') else datetime.now(),
            learning_rate=data.get('learning_rate', 0.1),
            value_type=data['value_type']
        )

@dataclass
class PersonalityUpdate:
    """Represents a personality dimension update"""
    dimension: str
    old_value: Union[float, str]
    new_value: Union[float, str]
    confidence_change: float
    trigger_context: str
    timestamp: datetime

@dataclass
class CommunicationPattern:
    """Represents a detected communication pattern"""
    pattern_type: str
    user_pattern: str
    suggested_adaptation: str
    confidence: float
    context: Dict[str, Any]

class PersonalityTracker:
    """
    Tracks comprehensive personality dimensions beyond just sass level
    Analyzes user communication patterns and adapts Penny's personality accordingly
    """

    def __init__(self, db_path: str = "data/personality_tracking.db"):
        self.db_path = db_path
        self.tracked_dimensions = {
            'communication_formality': {
                'range': (0.0, 1.0),  # 0=very casual, 1=very formal
                'default': 0.5,
                'learning_rate': 0.1,
                'value_type': 'continuous',
                'description': 'How formal vs casual the user prefers communication'
            },
            'technical_depth_preference': {
                'range': (0.0, 1.0),  # 0=simple explanations, 1=deep technical
                'default': 0.5,
                'learning_rate': 0.1,
                'value_type': 'continuous',
                'description': 'Preference for technical detail vs simple explanations'
            },
            'humor_style_preference': {
                'options': ['dry', 'playful', 'roasting', 'dad_jokes', 'tech_humor', 'balanced'],
                'default': 'balanced',
                'learning_rate': 0.15,
                'value_type': 'categorical',
                'description': 'Preferred style of humor and wit'
            },
            'response_length_preference': {
                'options': ['brief', 'medium', 'detailed', 'comprehensive'],
                'default': 'medium',
                'learning_rate': 0.1,
                'value_type': 'categorical',
                'description': 'Preferred length and depth of responses'
            },
            'conversation_pace_preference': {
                'range': (0.0, 1.0),  # 0=slow/thoughtful, 1=fast/energetic
                'default': 0.5,
                'learning_rate': 0.1,
                'value_type': 'continuous',
                'description': 'Preferred pace and energy level of conversation'
            },
            'proactive_suggestions': {
                'range': (0.0, 1.0),  # 0=wait for requests, 1=proactive suggestions
                'default': 0.4,
                'learning_rate': 0.08,
                'value_type': 'continuous',
                'description': 'Preference for proactive suggestions vs reactive responses'
            },
            'emotional_support_style': {
                'options': ['analytical', 'empathetic', 'solution_focused', 'cheerleading', 'balanced'],
                'default': 'balanced',
                'learning_rate': 0.12,
                'value_type': 'categorical',
                'description': 'Preferred style of emotional support and encouragement'
            }
        }

        # Initialize database
        self._init_database()

        # Communication pattern analyzers
        self.formality_indicators = {
            'formal': ['please', 'thank you', 'could you', 'would you mind', 'if you could', 'appreciate'],
            'casual': ['yo', 'hey', 'sup', 'gonna', 'wanna', 'yeah', 'cool', 'awesome', 'dude']
        }

        self.technical_indicators = {
            'deep': ['implementation', 'architecture', 'algorithm', 'optimize', 'how does it work',
                    'explain the logic', 'deep dive', 'under the hood', 'details', 'specifics'],
            'simple': ['simple explanation', 'eli5', 'in plain english', 'quick overview',
                      'just tell me', 'basic idea', 'summarize', 'brief', 'tldr']
        }

        self.humor_response_patterns = {
            'dry': ['lol', 'haha', 'clever', 'witty', 'good one'],
            'playful': ['😄', '😊', 'fun', 'cute', 'adorable', 'playful'],
            'roasting': ['savage', 'burn', 'roasted', 'brutal', 'shots fired'],
            'tech_humor': ['nerdy', 'geeky', 'programming joke', 'tech humor'],
            'dad_jokes': ['dad joke', 'punny', 'groan', 'terrible', 'so bad its good']
        }

        self.pace_indicators = {
            'fast': ['quick', 'fast', 'asap', 'immediately', 'right now', 'urgent'],
            'slow': ['take your time', 'think about it', 'carefully', 'thorough', 'detailed']
        }

    def _init_database(self):
        """Initialize the personality tracking database with WAL mode"""
        Path("data").mkdir(exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            # Enable WAL mode for concurrent access
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA busy_timeout=5000")  # 5 second timeout
            
            # Personality dimensions table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS personality_dimensions (
                    dimension TEXT PRIMARY KEY,
                    current_value TEXT NOT NULL,
                    confidence REAL DEFAULT 0.5,
                    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
                    learning_rate REAL DEFAULT 0.1,
                    value_type TEXT DEFAULT 'continuous'
                )
            ''')

            # Personality evolution history
            conn.execute('''
                CREATE TABLE IF NOT EXISTS personality_evolution (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    dimension TEXT NOT NULL,
                    old_value TEXT,
                    new_value TEXT,
                    confidence_change REAL,
                    trigger_context TEXT,
                    session_id TEXT
                )
            ''')

            # Communication patterns
            conn.execute('''
                CREATE TABLE IF NOT EXISTS communication_patterns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    pattern_type TEXT NOT NULL,
                    user_pattern TEXT,
                    penny_adaptation TEXT,
                    effectiveness_score REAL,
                    context TEXT
                )
            ''')

            # Initialize default values if not exists
            for dimension, config in self.tracked_dimensions.items():
                conn.execute('''
                    INSERT OR IGNORE INTO personality_dimensions
                    (dimension, current_value, confidence, learning_rate, value_type)
                    VALUES (?, ?, 0.3, ?, ?)
                ''', (dimension, str(config['default']), config['learning_rate'], config['value_type']))

            conn.commit()

    async def analyze_user_communication(self, user_message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze user's communication style and extract personality signals
        """
        analysis = {
            'formality_level': self._detect_formality_level(user_message),
            'technical_depth_request': self._detect_technical_depth(user_message, context),
            'humor_response_cues': self._detect_humor_preferences(user_message, context),
            'length_preference_signals': self._detect_length_preferences(user_message, context),
            'pace_indicators': self._detect_conversation_pace(user_message, context),
            'proactivity_cues': self._detect_proactivity_preferences(user_message, context),
            'emotional_support_needs': self._detect_emotional_support_style(user_message, context)
        }

        # Add confidence scores for each analysis
        for key, value in analysis.items():
            if isinstance(value, dict) and 'confidence' not in value:
                analysis[key]['confidence'] = self._calculate_analysis_confidence(key, value)

        return analysis

    def _detect_formality_level(self, message: str) -> Dict[str, Any]:
        """Detect formality level from user's language patterns"""
        message_lower = message.lower()

        formal_count = sum(1 for indicator in self.formality_indicators['formal']
                          if indicator in message_lower)
        casual_count = sum(1 for indicator in self.formality_indicators['casual']
                          if indicator in message_lower)

        # Additional formality indicators
        has_full_sentences = len([s for s in message.split('.') if len(s.strip()) > 3]) > 1
        has_contractions = len(re.findall(r"\w+'[a-z]", message)) > 0
        proper_capitalization = message[0].isupper() if message else False

        formality_score = 0.5  # Default neutral

        if formal_count > casual_count:
            formality_score = min(0.9, 0.5 + (formal_count * 0.15))
        elif casual_count > formal_count:
            formality_score = max(0.1, 0.5 - (casual_count * 0.15))

        # Adjust based on structure
        if has_full_sentences and proper_capitalization and not has_contractions:
            formality_score += 0.1
        elif has_contractions or not proper_capitalization:
            formality_score -= 0.1

        return {
            'value': max(0.0, min(1.0, formality_score)),
            'confidence': min(1.0, (formal_count + casual_count) * 0.2 + 0.3),
            'indicators': {
                'formal_words': formal_count,
                'casual_words': casual_count,
                'proper_structure': has_full_sentences and proper_capitalization
            }
        }

    def _detect_technical_depth(self, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Detect preference for technical depth based on questions and context"""
        message_lower = message.lower()

        deep_count = sum(1 for indicator in self.technical_indicators['deep']
                        if indicator in message_lower)
        simple_count = sum(1 for indicator in self.technical_indicators['simple']
                          if indicator in message_lower)

        # Context clues
        is_follow_up = context.get('is_follow_up_question', False)
        previous_was_technical = context.get('previous_response_technical', False)

        technical_score = 0.5  # Default neutral

        if deep_count > simple_count:
            technical_score = min(0.9, 0.5 + (deep_count * 0.2))
        elif simple_count > deep_count:
            technical_score = max(0.1, 0.5 - (simple_count * 0.2))

        # Adjust based on context
        if is_follow_up and previous_was_technical:
            technical_score += 0.1  # User is following up on technical content
        elif is_follow_up and not previous_was_technical:
            technical_score -= 0.05  # User didn't ask for more detail

        return {
            'value': max(0.0, min(1.0, technical_score)),
            'confidence': min(1.0, (deep_count + simple_count) * 0.25 + 0.4),
            'indicators': {
                'deep_indicators': deep_count,
                'simple_indicators': simple_count,
                'context_support': is_follow_up
            }
        }

    def _detect_humor_preferences(self, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Detect humor style preferences from user responses"""
        message_lower = message.lower()

        # Check for humor response patterns
        humor_scores = {}
        for style, indicators in self.humor_response_patterns.items():
            score = sum(1 for indicator in indicators if indicator in message_lower)
            if score > 0:
                humor_scores[style] = score

        # Check previous context for humor effectiveness
        previous_humor_style = context.get('previous_humor_style')
        user_responded_positively = context.get('positive_response_to_humor', False)

        # Determine preferred style
        if humor_scores:
            preferred_style = max(humor_scores.items(), key=lambda x: x[1])[0]
            confidence = min(1.0, max(humor_scores.values()) * 0.3 + 0.3)
        elif previous_humor_style and user_responded_positively:
            preferred_style = previous_humor_style
            confidence = 0.7
        else:
            preferred_style = 'balanced'
            confidence = 0.3

        return {
            'value': preferred_style,
            'confidence': confidence,
            'indicators': humor_scores,
            'context_support': user_responded_positively
        }

    def _detect_length_preferences(self, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Detect response length preferences"""
        message_lower = message.lower()

        brief_indicators = ['brief', 'short', 'quick', 'summary', 'tldr', 'just tell me']
        detailed_indicators = ['detailed', 'comprehensive', 'explain everything', 'full explanation', 'thorough']

        brief_count = sum(1 for indicator in brief_indicators if indicator in message_lower)
        detailed_count = sum(1 for indicator in detailed_indicators if indicator in message_lower)

        # Message length as indicator of user's communication style
        user_message_length = len(message.split())

        if brief_count > detailed_count:
            preferred_length = 'brief'
            confidence = min(1.0, brief_count * 0.4 + 0.4)
        elif detailed_count > brief_count:
            preferred_length = 'comprehensive' if detailed_count > 2 else 'detailed'
            confidence = min(1.0, detailed_count * 0.4 + 0.4)
        else:
            # Infer from user's message length
            if user_message_length < 10:
                preferred_length = 'brief'
                confidence = 0.4
            elif user_message_length > 50:
                preferred_length = 'detailed'
                confidence = 0.4
            else:
                preferred_length = 'medium'
                confidence = 0.3

        return {
            'value': preferred_length,
            'confidence': confidence,
            'indicators': {
                'brief_indicators': brief_count,
                'detailed_indicators': detailed_count,
                'user_message_length': user_message_length
            }
        }

    def _detect_conversation_pace(self, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Detect preferred conversation pace and energy level"""
        message_lower = message.lower()

        fast_count = sum(1 for indicator in self.pace_indicators['fast'] if indicator in message_lower)
        slow_count = sum(1 for indicator in self.pace_indicators['slow'] if indicator in message_lower)

        # Analyze message structure for pace indicators
        has_exclamation = '!' in message
        has_multiple_questions = message.count('?') > 1
        response_time = context.get('response_time_minutes', 5)  # Time since last message

        pace_score = 0.5  # Default neutral

        if fast_count > slow_count:
            pace_score = min(0.9, 0.5 + (fast_count * 0.2))
        elif slow_count > fast_count:
            pace_score = max(0.1, 0.5 - (slow_count * 0.2))

        # Adjust based on message characteristics
        if has_exclamation or has_multiple_questions:
            pace_score += 0.1

        # Quick responses suggest faster pace preference
        if response_time < 2:
            pace_score += 0.1
        elif response_time > 30:
            pace_score -= 0.1

        return {
            'value': max(0.0, min(1.0, pace_score)),
            'confidence': min(1.0, (fast_count + slow_count) * 0.3 + 0.3),
            'indicators': {
                'fast_indicators': fast_count,
                'slow_indicators': slow_count,
                'excitement_level': has_exclamation,
                'response_speed': response_time
            }
        }

    def _detect_proactivity_preferences(self, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Detect preference for proactive suggestions vs reactive responses"""
        message_lower = message.lower()

        proactive_positive = ['suggest', 'recommend', 'what should', 'any ideas', 'what else', 'proactive']
        proactive_negative = ['just answer', 'only what i asked', 'dont suggest', 'stop suggesting']

        positive_count = sum(1 for indicator in proactive_positive if indicator in message_lower)
        negative_count = sum(1 for indicator in proactive_negative if indicator in message_lower)

        # Check if user follows up on previous suggestions
        followed_up_on_suggestion = context.get('followed_up_on_suggestion', False)
        ignored_suggestions = context.get('ignored_suggestions_count', 0)

        proactivity_score = 0.4  # Default slightly less proactive

        if positive_count > negative_count:
            proactivity_score = min(0.9, 0.4 + (positive_count * 0.2))
        elif negative_count > positive_count:
            proactivity_score = max(0.1, 0.4 - (negative_count * 0.3))

        # Adjust based on historical behavior
        if followed_up_on_suggestion:
            proactivity_score += 0.1
        if ignored_suggestions > 2:
            proactivity_score -= 0.15

        return {
            'value': max(0.0, min(1.0, proactivity_score)),
            'confidence': min(1.0, (positive_count + negative_count) * 0.3 + 0.4),
            'indicators': {
                'positive_indicators': positive_count,
                'negative_indicators': negative_count,
                'engagement_with_suggestions': followed_up_on_suggestion
            }
        }

    def _detect_emotional_support_style(self, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Detect preferred emotional support and encouragement style"""
        message_lower = message.lower()

        # Emotional context indicators
        is_frustrated = any(word in message_lower for word in ['frustrated', 'annoyed', 'stuck', 'confused'])
        is_excited = any(word in message_lower for word in ['excited', 'awesome', 'amazing', 'love it'])
        is_seeking_help = any(word in message_lower for word in ['help', 'struggling', 'difficult', 'hard'])

        # Response to previous emotional support
        previous_support_style = context.get('previous_support_style')
        responded_well_to_support = context.get('positive_response_to_support', False)

        # Default to balanced
        preferred_style = 'balanced'
        confidence = 0.3

        if is_frustrated and is_seeking_help:
            # User is struggling - might prefer solution-focused support
            preferred_style = 'solution_focused'
            confidence = 0.6
        elif is_excited:
            # User is happy - might prefer cheerleading
            preferred_style = 'cheerleading'
            confidence = 0.5
        elif previous_support_style and responded_well_to_support:
            # Use what worked before
            preferred_style = previous_support_style
            confidence = 0.7

        return {
            'value': preferred_style,
            'confidence': confidence,
            'indicators': {
                'emotional_state': {
                    'frustrated': is_frustrated,
                    'excited': is_excited,
                    'seeking_help': is_seeking_help
                },
                'previous_effectiveness': responded_well_to_support
            }
        }

    def _calculate_analysis_confidence(self, analysis_type: str, analysis_result: Any) -> float:
        """Calculate confidence score for analysis results"""
        base_confidence = 0.3

        if isinstance(analysis_result, dict):
            # Look for indicator counts or supporting evidence
            indicators = analysis_result.get('indicators', {})
            if isinstance(indicators, dict):
                indicator_count = sum(indicators.values()) if all(isinstance(v, (int, float)) for v in indicators.values()) else 0
                base_confidence += min(0.4, indicator_count * 0.1)

            # Context support
            if analysis_result.get('context_support', False):
                base_confidence += 0.2

        return min(1.0, base_confidence)

    async def get_current_personality_state(self) -> Dict[str, PersonalityDimension]:
        """Get current personality dimension values with confidence scores - now with caching!"""

        # Phase 3A: Try cache first
        if CACHE_AVAILABLE:
            cache = get_cache()
            cached_state = cache.get("default")
            if cached_state is not None:
                return cached_state

        # Cache miss or cache disabled - read from database
        personality_state = {}

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                SELECT dimension, current_value, confidence, last_updated, learning_rate, value_type
                FROM personality_dimensions
            ''')

            for row in cursor.fetchall():
                dimension, value_str, confidence, last_updated, learning_rate, value_type = row

                # Parse value based on type
                if value_type == 'continuous':
                    current_value = float(value_str)
                else:
                    current_value = value_str

                personality_state[dimension] = PersonalityDimension(
                    name=dimension,
                    current_value=current_value,
                    confidence=confidence,
                    last_updated=datetime.fromisoformat(last_updated),
                    learning_rate=learning_rate,
                    value_type=value_type
                )

        # Store in cache
        if CACHE_AVAILABLE:
            cache.set("default", personality_state)

        return personality_state

    def get_personality_state(self) -> Dict[str, Any]:
        """
        Synchronous wrapper for get_current_personality_state().
        Used by Week 8 snapshot system which runs in sync context.
        Returns JSON-serializable dict format for snapshots.
        """
        loop = asyncio.new_event_loop()
        try:
            state = loop.run_until_complete(self.get_current_personality_state())

            # Convert PersonalityDimension objects to dicts for JSON serialization
            serializable_state = {}
            for key, dim in state.items():
                if hasattr(dim, 'to_dict'):
                    serializable_state[key] = dim.to_dict()
                else:
                    serializable_state[key] = dim

            return serializable_state
        finally:
            loop.close()

    async def update_personality_dimension(self, dimension: str, new_value: Union[float, str],
                                         confidence_change: float, context: str) -> bool:
        """Update a personality dimension with new learning"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Get current value
                cursor = conn.execute(
                    'SELECT current_value, confidence, value_type FROM personality_dimensions WHERE dimension = ?',
                    (dimension,)
                )
                row = cursor.fetchone()

                if not row:
                    return False

                old_value_str, old_confidence, value_type = row

                # Parse old value
                if value_type == 'continuous':
                    old_value = float(old_value_str)
                else:
                    old_value = old_value_str

                # Update dimension
                new_confidence = max(0.0, min(1.0, old_confidence + confidence_change))

                conn.execute('''
                    UPDATE personality_dimensions
                    SET current_value = ?, confidence = ?, last_updated = CURRENT_TIMESTAMP
                    WHERE dimension = ?
                ''', (str(new_value), new_confidence, dimension))

                # Log evolution
                conn.execute('''
                    INSERT INTO personality_evolution
                    (dimension, old_value, new_value, confidence_change, trigger_context)
                    VALUES (?, ?, ?, ?, ?)
                ''', (dimension, str(old_value), str(new_value), confidence_change, context))

                conn.commit()

                # Phase 3A: Invalidate cache after update
                if CACHE_AVAILABLE:
                    cache = get_cache()
                    cache.invalidate("default")

                return True

        except Exception as e:
            print(f"Error updating personality dimension {dimension}: {e}")
            return False

    async def get_personality_evolution_history(self, dimension: Optional[str] = None,
                                              days: int = 30) -> List[PersonalityUpdate]:
        """Get personality evolution history"""
        history = []

        with sqlite3.connect(self.db_path) as conn:
            if dimension:
                cursor = conn.execute('''
                    SELECT dimension, old_value, new_value, confidence_change, trigger_context, timestamp
                    FROM personality_evolution
                    WHERE dimension = ? AND timestamp > datetime('now', '-{} days')
                    ORDER BY timestamp DESC
                '''.format(days), (dimension,))
            else:
                cursor = conn.execute('''
                    SELECT dimension, old_value, new_value, confidence_change, trigger_context, timestamp
                    FROM personality_evolution
                    WHERE timestamp > datetime('now', '-{} days')
                    ORDER BY timestamp DESC
                '''.format(days))

            for row in cursor.fetchall():
                dim, old_val, new_val, conf_change, context, timestamp = row
                history.append(PersonalityUpdate(
                    dimension=dim,
                    old_value=old_val,
                    new_value=new_val,
                    confidence_change=conf_change,
                    trigger_context=context,
                    timestamp=datetime.fromisoformat(timestamp)
                ))

        return history

    async def store_communication_pattern(self, pattern_type: str, user_pattern: str,
                                        penny_adaptation: str, effectiveness_score: float,
                                        context: Dict[str, Any]) -> bool:
        """Store detected communication pattern for future reference"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    INSERT INTO communication_patterns
                    (pattern_type, user_pattern, penny_adaptation, effectiveness_score, context)
                    VALUES (?, ?, ?, ?, ?)
                ''', (pattern_type, user_pattern, penny_adaptation, effectiveness_score, str(context)))

                conn.commit()
                return True

        except Exception as e:
            print(f"Error storing communication pattern: {e}")
            return False

    async def get_personality_insights(self) -> Dict[str, Any]:
        """Generate insights about personality learning progress"""
        insights = {
            'dimension_confidence': {},
            'recent_changes': [],
            'learning_trends': {},
            'communication_patterns': []
        }

        # Get current confidence levels
        personality_state = await self.get_current_personality_state()
        for dim_name, dimension in personality_state.items():
            insights['dimension_confidence'][dim_name] = {
                'value': dimension.current_value,
                'confidence': dimension.confidence,
                'description': self.tracked_dimensions[dim_name]['description']
            }

        # Get recent changes
        recent_history = await self.get_personality_evolution_history(days=7)
        insights['recent_changes'] = [
            {
                'dimension': update.dimension,
                'change': f"{update.old_value} → {update.new_value}",
                'context': update.trigger_context,
                'timestamp': update.timestamp.isoformat()
            }
            for update in recent_history[:5]
        ]

        return insights

    def get_cache_stats(self) -> Optional[Dict[str, Any]]:
        """
        Get personality state cache statistics (Phase 3A)

        Returns:
            Cache stats dict with hit_rate, hits, misses, etc.
            None if cache is not available
        """
        if not CACHE_AVAILABLE:
            return None

        cache = get_cache()
        return cache.get_stats()


if __name__ == "__main__":
    async def main():
        tracker = PersonalityTracker()

        # Test communication analysis
        test_messages = [
            ("Hey, can you help me debug this code real quick?", {"previous_response_technical": False}),
            ("Could you please provide a detailed explanation of how this algorithm works?", {"is_follow_up_question": True}),
            ("lol that was actually pretty funny", {"previous_humor_style": "playful"}),
            ("I'm really frustrated with this bug, any suggestions?", {"emotional_context": True})
        ]

        print("🧠 Testing Personality Tracker")
        print("=" * 50)

        for message, context in test_messages:
            print(f"\nMessage: {message}")
            analysis = await tracker.analyze_user_communication(message, context)

            print(f"Formality: {analysis['formality_level']['value']:.2f} (confidence: {analysis['formality_level']['confidence']:.2f})")
            print(f"Technical depth: {analysis['technical_depth_request']['value']:.2f}")
            print(f"Humor style: {analysis['humor_response_cues']['value']}")
            print(f"Response length: {analysis['length_preference_signals']['value']}")

        # Test personality state
        print(f"\n📊 Current Personality State:")
        state = await tracker.get_current_personality_state()
        for dim_name, dimension in state.items():
            print(f"  {dim_name}: {dimension.current_value} (confidence: {dimension.confidence:.2f})")

        # Test insights
        print(f"\n💡 Personality Insights:")
        insights = await tracker.get_personality_insights()
        for dim_name, info in insights['dimension_confidence'].items():
            print(f"  {dim_name}: {info['value']} ({info['confidence']:.2f} confidence)")

    asyncio.run(main())