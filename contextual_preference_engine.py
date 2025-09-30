#!/usr/bin/env python3
"""
Contextual Preference Engine
Adapts personality based on context: time of day, topic, social setting, mood
"""

import sqlite3
from datetime import datetime, time
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
import json
from enum import Enum

class ContextType(Enum):
    """Types of contexts that influence personality"""
    TIME_OF_DAY = "time_of_day"
    TOPIC_CATEGORY = "topic_category"
    SOCIAL_CONTEXT = "social_context"
    MOOD_STATE = "mood_state"
    DAY_OF_WEEK = "day_of_week"
    WORK_PERSONAL = "work_personal"

class TimeOfDay(Enum):
    """Time periods with different personality expectations"""
    EARLY_MORNING = "early_morning"  # 5am-8am
    MORNING = "morning"  # 8am-12pm
    AFTERNOON = "afternoon"  # 12pm-5pm
    EVENING = "evening"  # 5pm-9pm
    NIGHT = "night"  # 9pm-12am
    LATE_NIGHT = "late_night"  # 12am-5am

class ContextualPreferenceEngine:
    """
    Learns how user's personality preferences change based on context
    Enables Penny to adapt dynamically to different situations
    """
    
    def __init__(self, db_path: str = "data/personality_tracking.db"):
        self.db_path = db_path
        self._init_database()
        
        # Default contextual adjustments (before learning)
        self.default_context_effects = {
            TimeOfDay.EARLY_MORNING: {
                'conversation_pace_preference': -0.2,  # Slower, more gentle
                'humor_style_preference': 'gentle',
                'response_length_preference': 'brief'
            },
            TimeOfDay.MORNING: {
                'conversation_pace_preference': 0.1,  # Energetic
                'proactive_suggestions': 0.1,  # More proactive
            },
            TimeOfDay.LATE_NIGHT: {
                'conversation_pace_preference': -0.1,  # More chill
                'humor_style_preference': 'dry',
                'communication_formality': -0.1  # More casual
            }
        }
    
    def _init_database(self):
        """Initialize contextual preferences database"""
        Path("data").mkdir(exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            # Contextual preferences table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS contextual_preferences (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    context_type TEXT NOT NULL,
                    context_value TEXT NOT NULL,
                    personality_adjustments TEXT NOT NULL,
                    confidence REAL DEFAULT 0.5,
                    usage_count INTEGER DEFAULT 1,
                    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
                    effectiveness_score REAL DEFAULT 0.5,
                    UNIQUE(context_type, context_value)
                )
            ''')
            
            # Context observations (raw data for learning)
            conn.execute('''
                CREATE TABLE IF NOT EXISTS context_observations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    context_type TEXT NOT NULL,
                    context_value TEXT NOT NULL,
                    observed_preferences TEXT NOT NULL,
                    user_satisfaction_indicator REAL,
                    session_id TEXT
                )
            ''')
            
            # Context transitions (learning how preferences change)
            conn.execute('''
                CREATE TABLE IF NOT EXISTS context_transitions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    from_context TEXT NOT NULL,
                    to_context TEXT NOT NULL,
                    personality_shift TEXT NOT NULL,
                    transition_smoothness REAL
                )
            ''')
            
            conn.commit()
    
    def get_current_time_context(self) -> TimeOfDay:
        """Determine current time of day context"""
        current_hour = datetime.now().hour
        
        if 5 <= current_hour < 8:
            return TimeOfDay.EARLY_MORNING
        elif 8 <= current_hour < 12:
            return TimeOfDay.MORNING
        elif 12 <= current_hour < 17:
            return TimeOfDay.AFTERNOON
        elif 17 <= current_hour < 21:
            return TimeOfDay.EVENING
        elif 21 <= current_hour < 24:
            return TimeOfDay.NIGHT
        else:
            return TimeOfDay.LATE_NIGHT
    
    def get_topic_context(self, message: str, conversation_history: List[Dict[str, Any]]) -> str:
        """Determine topic category from message and history"""
        message_lower = message.lower()
        
        # Topic detection patterns
        tech_keywords = ['code', 'debug', 'program', 'algorithm', 'deploy', 'bug', 'error', 'function']
        work_keywords = ['meeting', 'project', 'deadline', 'client', 'presentation', 'email']
        personal_keywords = ['family', 'friend', 'weekend', 'vacation', 'dinner', 'movie']
        learning_keywords = ['learn', 'understand', 'explain', 'how does', 'why does', 'teach']
        creative_keywords = ['write', 'design', 'create', 'build', 'make', 'idea', 'brainstorm']
        
        # Count keyword matches
        keyword_counts = {
            'technical': sum(1 for kw in tech_keywords if kw in message_lower),
            'work': sum(1 for kw in work_keywords if kw in message_lower),
            'personal': sum(1 for kw in personal_keywords if kw in message_lower),
            'learning': sum(1 for kw in learning_keywords if kw in message_lower),
            'creative': sum(1 for kw in creative_keywords if kw in message_lower)
        }
        
        # Return category with highest count, default to 'general'
        max_category = max(keyword_counts.items(), key=lambda x: x[1])
        return max_category[0] if max_category[1] > 0 else 'general'
    
    def get_social_context(self, context: Dict[str, Any]) -> str:
        """Determine social context (solo, with others, specific people)"""
        participants = context.get('participants', [])
        
        if not participants:
            return 'solo'
        elif len(participants) == 1:
            return f'with_{participants[0]}'
        else:
            return 'group'
    
    def get_mood_context(self, message: str, context: Dict[str, Any]) -> str:
        """Detect user's mood from message and context"""
        message_lower = message.lower()
        
        # Mood indicators
        frustrated_indicators = ['frustrated', 'annoyed', 'stuck', 'confused', 'ugh', 'damn', 'argh']
        excited_indicators = ['excited', 'awesome', 'amazing', 'love', 'great', '!', 'yay']
        stressed_indicators = ['stressed', 'overwhelmed', 'busy', 'deadline', 'urgent', 'asap']
        tired_indicators = ['tired', 'exhausted', 'sleepy', 'worn out', 'drained']
        happy_indicators = ['happy', 'glad', 'pleased', 'good mood', 'feeling good']
        
        # Check for mood indicators
        if any(ind in message_lower for ind in frustrated_indicators):
            return 'frustrated'
        elif any(ind in message_lower for ind in excited_indicators):
            return 'excited'
        elif any(ind in message_lower for ind in stressed_indicators):
            return 'stressed'
        elif any(ind in message_lower for ind in tired_indicators):
            return 'tired'
        elif any(ind in message_lower for ind in happy_indicators):
            return 'happy'
        
        # Default to neutral if no strong indicators
        return context.get('emotion', 'neutral')
    
    async def analyze_current_context(self, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze all contextual factors for current interaction"""
        current_context = {
            'time_of_day': self.get_current_time_context().value,
            'topic_category': self.get_topic_context(message, context.get('conversation_history', [])),
            'social_context': self.get_social_context(context),
            'mood_state': self.get_mood_context(message, context),
            'day_of_week': datetime.now().strftime('%A').lower(),
            'work_personal': 'work' if self.get_topic_context(message, []) in ['technical', 'work'] else 'personal'
        }
        
        return current_context
    
    async def get_contextual_personality_adjustments(self, current_context: Dict[str, Any]) -> Dict[str, Any]:
        """Get personality adjustments based on current context"""
        adjustments = {}
        
        # Check database for learned contextual preferences
        with sqlite3.connect(self.db_path) as conn:
            for context_type, context_value in current_context.items():
                cursor = conn.execute('''
                    SELECT personality_adjustments, confidence, effectiveness_score
                    FROM contextual_preferences
                    WHERE context_type = ? AND context_value = ? AND confidence > 0.5
                ''', (context_type, context_value))
                
                row = cursor.fetchone()
                if row:
                    learned_adjustments = json.loads(row[0])
                    confidence = row[1]
                    effectiveness = row[2]
                    
                    # Apply learned adjustments weighted by confidence and effectiveness
                    weight = confidence * effectiveness
                    for dimension, adjustment in learned_adjustments.items():
                        if dimension not in adjustments:
                            adjustments[dimension] = []
                        adjustments[dimension].append({
                            'value': adjustment,
                            'weight': weight,
                            'source': f'{context_type}:{context_value}'
                        })
        
        # Apply default context effects if no learned preferences
        time_context = current_context.get('time_of_day')
        if time_context and not any(a.get('source', '').startswith('time_of_day') for adj_list in adjustments.values() for a in adj_list):
            try:
                time_enum = TimeOfDay(time_context)
                if time_enum in self.default_context_effects:
                    default_adj = self.default_context_effects[time_enum]
                    for dimension, adjustment in default_adj.items():
                        if dimension not in adjustments:
                            adjustments[dimension] = []
                        adjustments[dimension].append({
                            'value': adjustment,
                            'weight': 0.3,  # Lower weight for defaults
                            'source': f'default_time:{time_context}'
                        })
            except ValueError:
                pass
        
        # Calculate final weighted adjustments
        final_adjustments = {}
        for dimension, adjustment_list in adjustments.items():
            if adjustment_list:
                # Weighted average of all adjustments for this dimension
                total_weight = sum(a['weight'] for a in adjustment_list)
                if total_weight > 0:
                    weighted_value = sum(a['value'] * a['weight'] for a in adjustment_list if isinstance(a['value'], (int, float))) / total_weight
                    final_adjustments[dimension] = {
                        'adjustment': weighted_value,
                        'confidence': min(1.0, total_weight),
                        'sources': [a['source'] for a in adjustment_list]
                    }
                else:
                    # Categorical adjustment - use most confident
                    best_adjustment = max(adjustment_list, key=lambda a: a['weight'])
                    final_adjustments[dimension] = {
                        'adjustment': best_adjustment['value'],
                        'confidence': best_adjustment['weight'],
                        'sources': [best_adjustment['source']]
                    }
        
        return final_adjustments
    
    async def record_context_observation(self, current_context: Dict[str, Any], 
                                        observed_preferences: Dict[str, Any],
                                        user_satisfaction: float = 0.5):
        """Record an observation about preferences in a specific context"""
        with sqlite3.connect(self.db_path) as conn:
            for context_type, context_value in current_context.items():
                conn.execute('''
                    INSERT INTO context_observations
                    (context_type, context_value, observed_preferences, user_satisfaction_indicator)
                    VALUES (?, ?, ?, ?)
                ''', (context_type, context_value, json.dumps(observed_preferences), user_satisfaction))
            
            conn.commit()
        
        # Update learned contextual preferences
        await self._update_contextual_preferences(current_context, observed_preferences, user_satisfaction)
    
    async def _update_contextual_preferences(self, current_context: Dict[str, Any],
                                           observed_preferences: Dict[str, Any],
                                           user_satisfaction: float):
        """Update learned contextual preferences based on observations"""
        with sqlite3.connect(self.db_path) as conn:
            for context_type, context_value in current_context.items():
                # Get existing preference
                cursor = conn.execute('''
                    SELECT id, personality_adjustments, confidence, usage_count, effectiveness_score
                    FROM contextual_preferences
                    WHERE context_type = ? AND context_value = ?
                ''', (context_type, context_value))
                
                row = cursor.fetchone()
                
                if row:
                    # Update existing preference
                    pref_id, existing_adj_json, confidence, usage_count, effectiveness = row
                    existing_adj = json.loads(existing_adj_json)
                    
                    # Merge observed preferences
                    for dimension, value in observed_preferences.items():
                        if dimension in existing_adj and isinstance(value, (int, float)) and isinstance(existing_adj[dimension], (int, float)):
                            # Weighted average for continuous values
                            existing_adj[dimension] = (existing_adj[dimension] * usage_count + value) / (usage_count + 1)
                        else:
                            # Replace for categorical or new dimensions
                            existing_adj[dimension] = value
                    
                    # Update confidence and effectiveness
                    new_confidence = min(1.0, confidence + 0.05)
                    new_effectiveness = (effectiveness * usage_count + user_satisfaction) / (usage_count + 1)
                    
                    conn.execute('''
                        UPDATE contextual_preferences
                        SET personality_adjustments = ?, confidence = ?, usage_count = ?,
                            effectiveness_score = ?, last_updated = CURRENT_TIMESTAMP
                        WHERE id = ?
                    ''', (json.dumps(existing_adj), new_confidence, usage_count + 1, 
                         new_effectiveness, pref_id))
                else:
                    # Insert new preference
                    conn.execute('''
                        INSERT INTO contextual_preferences
                        (context_type, context_value, personality_adjustments, confidence, 
                         usage_count, effectiveness_score)
                        VALUES (?, ?, ?, 0.5, 1, ?)
                    ''', (context_type, context_value, json.dumps(observed_preferences), user_satisfaction))
            
            conn.commit()
    
    async def record_context_transition(self, from_context: Dict[str, Any], 
                                       to_context: Dict[str, Any],
                                       personality_shift: Dict[str, Any],
                                       smoothness: float = 0.5):
        """Record how personality shifted between contexts"""
        from_str = json.dumps(from_context, sort_keys=True)
        to_str = json.dumps(to_context, sort_keys=True)
        shift_str = json.dumps(personality_shift)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT INTO context_transitions
                (from_context, to_context, personality_shift, transition_smoothness)
                VALUES (?, ?, ?, ?)
            ''', (from_str, to_str, shift_str, smoothness))
            
            conn.commit()
    
    async def get_contextual_insights(self) -> Dict[str, Any]:
        """Get insights about learned contextual preferences"""
        insights = {
            'learned_contexts': [],
            'strongest_context_effects': [],
            'context_diversity': 0,
            'most_effective_contexts': []
        }
        
        with sqlite3.connect(self.db_path) as conn:
            # Get all learned contexts
            cursor = conn.execute('''
                SELECT context_type, context_value, personality_adjustments, 
                       confidence, usage_count, effectiveness_score
                FROM contextual_preferences
                WHERE confidence > 0.5
                ORDER BY confidence DESC
            ''')
            
            for row in cursor.fetchall():
                context_type, context_value, adj_json, confidence, usage_count, effectiveness = row
                adjustments = json.loads(adj_json)
                
                insights['learned_contexts'].append({
                    'context': f'{context_type}:{context_value}',
                    'adjustments': adjustments,
                    'confidence': confidence,
                    'usage_count': usage_count,
                    'effectiveness': effectiveness
                })
            
            # Calculate context diversity
            unique_context_types = conn.execute('''
                SELECT COUNT(DISTINCT context_type) FROM contextual_preferences
            ''').fetchone()[0]
            insights['context_diversity'] = unique_context_types
            
            # Get strongest context effects (highest confidence * magnitude)
            for learned in insights['learned_contexts'][:10]:
                magnitude = sum(abs(v) for v in learned['adjustments'].values() if isinstance(v, (int, float)))
                strength = learned['confidence'] * magnitude
                
                if strength > 0.3:
                    insights['strongest_context_effects'].append({
                        'context': learned['context'],
                        'strength': strength,
                        'adjustments': learned['adjustments']
                    })
            
            # Sort by strength
            insights['strongest_context_effects'].sort(key=lambda x: x['strength'], reverse=True)
            
            # Get most effective contexts
            insights['most_effective_contexts'] = sorted(
                [ctx for ctx in insights['learned_contexts'] if ctx['effectiveness'] > 0.6],
                key=lambda x: x['effectiveness'],
                reverse=True
            )[:5]
        
        return insights


if __name__ == "__main__":
    import asyncio
    
    async def test_contextual_engine():
        print("🌍 Testing Contextual Preference Engine")
        print("=" * 60)
        
        engine = ContextualPreferenceEngine()
        
        # Test context analysis
        test_scenarios = [
            ("Hey, can you help me debug this code?", 
             {'participants': [], 'emotion': 'neutral'}),
            
            ("I'm exhausted... can we keep this brief?",
             {'participants': [], 'emotion': 'tired'}),
            
            ("Super excited about this new project! Let's dive deep into the architecture",
             {'participants': ['team'], 'emotion': 'excited'}),
        ]
        
        print("\n📊 Analyzing Contexts:")
        for message, context in test_scenarios:
            print(f"\nMessage: {message}")
            
            current_context = await engine.analyze_current_context(message, context)
            print(f"  Context analysis:")
            for key, value in current_context.items():
                print(f"    {key}: {value}")
            
            adjustments = await engine.get_contextual_personality_adjustments(current_context)
            if adjustments:
                print(f"  Personality adjustments:")
                for dimension, adj_info in adjustments.items():
                    print(f"    {dimension}: {adj_info['adjustment']} (confidence: {adj_info['confidence']:.2f})")
            else:
                print(f"  No adjustments needed (using baseline personality)")
        
        # Simulate learning
        print("\n\n🧠 Simulating Contextual Learning...")
        
        # Record some observations
        morning_context = {
            'time_of_day': 'morning',
            'topic_category': 'technical',
            'mood_state': 'neutral'
        }
        
        morning_preferences = {
            'conversation_pace_preference': 0.2,  # More energetic in morning
            'technical_depth_preference': 0.1,  # Ready for details
            'response_length_preference': 'detailed'
        }
        
        await engine.record_context_observation(morning_context, morning_preferences, user_satisfaction=0.8)
        
        late_night_context = {
            'time_of_day': 'late_night',
            'topic_category': 'general',
            'mood_state': 'tired'
        }
        
        late_night_preferences = {
            'conversation_pace_preference': -0.2,  # Slower at night
            'response_length_preference': 'brief',
            'communication_formality': -0.1  # More casual
        }
        
        await engine.record_context_observation(late_night_context, late_night_preferences, user_satisfaction=0.9)
        
        # Get insights
        print("\n💡 Contextual Learning Insights:")
        insights = await engine.get_contextual_insights()
        
        print(f"  Context diversity: {insights['context_diversity']} different context types learned")
        print(f"  Learned contexts: {len(insights['learned_contexts'])}")
        
        if insights['strongest_context_effects']:
            print(f"\n  Strongest context effects:")
            for effect in insights['strongest_context_effects'][:3]:
                print(f"    {effect['context']}: strength {effect['strength']:.2f}")
                for dim, val in effect['adjustments'].items():
                    print(f"      - {dim}: {val}")
        
        print("\n✅ Contextual preference engine test completed!")
    
    asyncio.run(test_contextual_engine())
