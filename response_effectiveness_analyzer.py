#!/usr/bin/env python3
"""
Response Effectiveness Analyzer
Measures which personality approaches work best and learns from feedback
"""

import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
from dataclasses import dataclass
from enum import Enum
import json
import hashlib

class FeedbackType(Enum):
    """Types of user feedback on responses"""
    POSITIVE = "positive"  # User engaged positively
    NEUTRAL = "neutral"  # Standard interaction
    NEGATIVE = "negative"  # User expressed dissatisfaction
    IGNORED = "ignored"  # User didn't engage with response
    FOLLOW_UP = "follow_up"  # User asked follow-up questions
    CORRECTED = "corrected"  # User corrected Penny's response
    PRAISED = "praised"  # User explicitly praised the response

@dataclass
class ResponseMetrics:
    """Metrics for evaluating response effectiveness"""
    engagement_score: float  # 0-1, how engaged user was
    satisfaction_indicators: List[str]  # Positive signals
    dissatisfaction_indicators: List[str]  # Negative signals
    follow_up_depth: int  # How many follow-ups
    time_to_next_message: float  # Seconds
    message_length_ratio: float  # User response length / Penny response length

class ResponseEffectivenessAnalyzer:
    """
    Tracks response effectiveness and learns which personality styles work best
    Enables continuous improvement through feedback analysis
    """
    
    def __init__(self, db_path: str = "data/personality_tracking.db"):
        self.db_path = db_path
        self._init_database()
        
        # Positive engagement indicators
        self.positive_indicators = [
            'thanks', 'thank you', 'perfect', 'exactly', 'great', 'awesome', 
            'helpful', 'appreciate', 'love it', 'nice', 'excellent', 'brilliant',
            'yes!', 'yeah!', 'got it', 'makes sense', 'i see', 'ah', 'interesting'
        ]
        
        # Negative engagement indicators
        self.negative_indicators = [
            'no', 'wrong', 'incorrect', 'not what i asked', 'thats not right',
            'confused', 'doesnt make sense', 'what?', 'huh?', 'unclear',
            'too long', 'too short', 'too technical', 'too simple'
        ]
        
        # Follow-up indicators
        self.follow_up_indicators = [
            'what about', 'how about', 'can you also', 'and', 'but', 'however',
            'follow up', 'additionally', 'also', 'tell me more', 'elaborate'
        ]
    
    def _init_database(self):
        """Initialize response effectiveness database"""
        Path("data").mkdir(exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            # Response effectiveness tracking
            conn.execute('''
                CREATE TABLE IF NOT EXISTS response_effectiveness (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    response_id TEXT UNIQUE NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    personality_snapshot TEXT NOT NULL,
                    context_snapshot TEXT NOT NULL,
                    response_length INTEGER,
                    user_feedback_type TEXT,
                    engagement_score REAL,
                    satisfaction_score REAL,
                    follow_up_count INTEGER DEFAULT 0,
                    time_to_next_message REAL,
                    effectiveness_score REAL
                )
            ''')
            
            # Personality effectiveness patterns
            conn.execute('''
                CREATE TABLE IF NOT EXISTS personality_effectiveness_patterns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    personality_profile TEXT NOT NULL,
                    context_pattern TEXT NOT NULL,
                    avg_effectiveness REAL,
                    sample_count INTEGER,
                    confidence REAL DEFAULT 0.5,
                    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(personality_profile, context_pattern)
                )
            ''')
            
            # A/B test results (when trying personality variations)
            conn.execute('''
                CREATE TABLE IF NOT EXISTS personality_ab_tests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    test_id TEXT NOT NULL,
                    variant_a TEXT NOT NULL,
                    variant_b TEXT NOT NULL,
                    context TEXT NOT NULL,
                    variant_a_score REAL,
                    variant_b_score REAL,
                    winner TEXT,
                    confidence REAL,
                    sample_size INTEGER,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
    
    def _generate_response_id(self, penny_response: str, timestamp: float) -> str:
        """Generate unique ID for a response"""
        content = f"{penny_response[:100]}_{timestamp}"
        return hashlib.md5(content.encode()).hexdigest()
    
    async def analyze_user_response(self, user_message: str, 
                                   previous_penny_response: str,
                                   time_since_response: float) -> ResponseMetrics:
        """Analyze user's response to determine effectiveness"""
        message_lower = user_message.lower()
        
        # Detect satisfaction indicators
        satisfaction_indicators = [ind for ind in self.positive_indicators 
                                  if ind in message_lower]
        dissatisfaction_indicators = [ind for ind in self.negative_indicators 
                                     if ind in message_lower]
        
        # Check for follow-up questions
        follow_up_depth = sum(1 for ind in self.follow_up_indicators 
                             if ind in message_lower)
        if '?' in user_message:
            follow_up_depth += 1
        
        # Calculate engagement score
        engagement_score = 0.5  # Baseline
        
        # Positive indicators increase score
        engagement_score += min(0.4, len(satisfaction_indicators) * 0.1)
        
        # Negative indicators decrease score
        engagement_score -= min(0.4, len(dissatisfaction_indicators) * 0.15)
        
        # Follow-ups indicate engagement
        engagement_score += min(0.2, follow_up_depth * 0.05)
        
        # Quick responses indicate engagement
        if time_since_response < 30:  # Less than 30 seconds
            engagement_score += 0.1
        elif time_since_response > 300:  # More than 5 minutes
            engagement_score -= 0.1
        
        engagement_score = max(0.0, min(1.0, engagement_score))
        
        # Calculate message length ratio
        user_length = len(user_message)
        penny_length = len(previous_penny_response)
        length_ratio = user_length / max(1, penny_length)
        
        return ResponseMetrics(
            engagement_score=engagement_score,
            satisfaction_indicators=satisfaction_indicators,
            dissatisfaction_indicators=dissatisfaction_indicators,
            follow_up_depth=follow_up_depth,
            time_to_next_message=time_since_response,
            message_length_ratio=length_ratio
        )
    
    async def record_response_effectiveness(self, 
                                          response_text: str,
                                          personality_state: Dict[str, Any],
                                          context: Dict[str, Any],
                                          metrics: ResponseMetrics):
        """Record effectiveness of a response"""
        response_id = self._generate_response_id(response_text, datetime.now().timestamp())
        
        # Determine feedback type
        if metrics.satisfaction_indicators and not metrics.dissatisfaction_indicators:
            if len(metrics.satisfaction_indicators) > 2 or 'perfect' in metrics.satisfaction_indicators:
                feedback_type = FeedbackType.PRAISED.value
            else:
                feedback_type = FeedbackType.POSITIVE.value
        elif metrics.dissatisfaction_indicators:
            if 'wrong' in metrics.dissatisfaction_indicators or 'incorrect' in metrics.dissatisfaction_indicators:
                feedback_type = FeedbackType.CORRECTED.value
            else:
                feedback_type = FeedbackType.NEGATIVE.value
        elif metrics.follow_up_depth > 0:
            feedback_type = FeedbackType.FOLLOW_UP.value
        elif metrics.time_to_next_message > 600:  # 10 minutes
            feedback_type = FeedbackType.IGNORED.value
        else:
            feedback_type = FeedbackType.NEUTRAL.value
        
        # Calculate satisfaction score
        satisfaction_score = metrics.engagement_score
        if feedback_type == FeedbackType.PRAISED.value:
            satisfaction_score = min(1.0, satisfaction_score + 0.2)
        elif feedback_type == FeedbackType.NEGATIVE.value:
            satisfaction_score = max(0.0, satisfaction_score - 0.3)
        
        # Calculate overall effectiveness score
        effectiveness_score = (
            metrics.engagement_score * 0.4 +
            satisfaction_score * 0.4 +
            min(1.0, metrics.follow_up_depth * 0.2) * 0.2
        )
        
        # Store in database
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT OR REPLACE INTO response_effectiveness
                (response_id, personality_snapshot, context_snapshot, response_length,
                 user_feedback_type, engagement_score, satisfaction_score, 
                 follow_up_count, time_to_next_message, effectiveness_score)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                response_id,
                json.dumps(personality_state),
                json.dumps(context),
                len(response_text),
                feedback_type,
                metrics.engagement_score,
                satisfaction_score,
                metrics.follow_up_depth,
                metrics.time_to_next_message,
                effectiveness_score
            ))
            
            conn.commit()
        
        # Update personality effectiveness patterns
        await self._update_effectiveness_patterns(personality_state, context, effectiveness_score)
        
        return effectiveness_score
    
    async def _update_effectiveness_patterns(self, personality_state: Dict[str, Any],
                                           context: Dict[str, Any],
                                           effectiveness_score: float):
        """Update learned patterns about personality effectiveness"""
        
        # Create simplified personality profile (key dimensions only)
        personality_profile = {
            'formality': personality_state.get('communication_formality', 0.5),
            'technical': personality_state.get('technical_depth_preference', 0.5),
            'sass': personality_state.get('sass_level', 'medium'),
            'pace': personality_state.get('conversation_pace_preference', 0.5)
        }
        
        # Create context pattern
        context_pattern = {
            'time': context.get('time_of_day', 'unknown'),
            'topic': context.get('topic_category', 'general'),
            'mood': context.get('mood_state', 'neutral')
        }
        
        profile_str = json.dumps(personality_profile, sort_keys=True)
        context_str = json.dumps(context_pattern, sort_keys=True)
        
        with sqlite3.connect(self.db_path) as conn:
            # Check if pattern exists
            cursor = conn.execute('''
                SELECT id, avg_effectiveness, sample_count, confidence
                FROM personality_effectiveness_patterns
                WHERE personality_profile = ? AND context_pattern = ?
            ''', (profile_str, context_str))
            
            row = cursor.fetchone()
            
            if row:
                # Update existing pattern
                pattern_id, avg_eff, sample_count, confidence = row
                new_avg = (avg_eff * sample_count + effectiveness_score) / (sample_count + 1)
                new_confidence = min(1.0, confidence + 0.05)
                
                conn.execute('''
                    UPDATE personality_effectiveness_patterns
                    SET avg_effectiveness = ?, sample_count = ?, confidence = ?,
                        last_updated = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (new_avg, sample_count + 1, new_confidence, pattern_id))
            else:
                # Insert new pattern
                conn.execute('''
                    INSERT INTO personality_effectiveness_patterns
                    (personality_profile, context_pattern, avg_effectiveness, 
                     sample_count, confidence)
                    VALUES (?, ?, ?, 1, 0.3)
                ''', (profile_str, context_str, effectiveness_score))
            
            conn.commit()
    
    async def get_optimal_personality_for_context(self, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Get the personality configuration that works best for this context"""
        
        context_pattern = {
            'time': context.get('time_of_day', 'unknown'),
            'topic': context.get('topic_category', 'general'),
            'mood': context.get('mood_state', 'neutral')
        }
        context_str = json.dumps(context_pattern, sort_keys=True)
        
        with sqlite3.connect(self.db_path) as conn:
            # Find patterns matching this context
            cursor = conn.execute('''
                SELECT personality_profile, avg_effectiveness, confidence, sample_count
                FROM personality_effectiveness_patterns
                WHERE context_pattern = ? AND confidence > 0.5 AND sample_count >= 3
                ORDER BY avg_effectiveness DESC
                LIMIT 1
            ''', (context_str,))
            
            row = cursor.fetchone()
            
            if row:
                profile_str, avg_eff, confidence, sample_count = row
                personality_profile = json.loads(profile_str)
                
                return {
                    'personality': personality_profile,
                    'expected_effectiveness': avg_eff,
                    'confidence': confidence,
                    'based_on_samples': sample_count
                }
        
        return None
    
    async def get_effectiveness_insights(self) -> Dict[str, Any]:
        """Get insights about response effectiveness patterns"""
        insights = {
            'total_responses_tracked': 0,
            'avg_effectiveness': 0.0,
            'best_performing_personalities': [],
            'worst_performing_personalities': [],
            'effectiveness_by_context': {},
            'feedback_distribution': {},
            'recent_trend': 'stable'
        }
        
        with sqlite3.connect(self.db_path) as conn:
            # Total responses
            cursor = conn.execute('SELECT COUNT(*) FROM response_effectiveness')
            insights['total_responses_tracked'] = cursor.fetchone()[0]
            
            if insights['total_responses_tracked'] == 0:
                return insights
            
            # Average effectiveness
            cursor = conn.execute('SELECT AVG(effectiveness_score) FROM response_effectiveness')
            insights['avg_effectiveness'] = cursor.fetchone()[0] or 0.0
            
            # Feedback distribution
            cursor = conn.execute('''
                SELECT user_feedback_type, COUNT(*) 
                FROM response_effectiveness 
                GROUP BY user_feedback_type
            ''')
            insights['feedback_distribution'] = {
                row[0]: row[1] for row in cursor.fetchall()
            }
            
            # Best performing personalities
            cursor = conn.execute('''
                SELECT personality_profile, context_pattern, avg_effectiveness, sample_count
                FROM personality_effectiveness_patterns
                WHERE confidence > 0.6
                ORDER BY avg_effectiveness DESC
                LIMIT 5
            ''')
            
            for row in cursor.fetchall():
                profile_str, context_str, avg_eff, samples = row
                insights['best_performing_personalities'].append({
                    'personality': json.loads(profile_str),
                    'context': json.loads(context_str),
                    'effectiveness': avg_eff,
                    'samples': samples
                })
            
            # Worst performing (for improvement)
            cursor = conn.execute('''
                SELECT personality_profile, context_pattern, avg_effectiveness, sample_count
                FROM personality_effectiveness_patterns
                WHERE confidence > 0.6
                ORDER BY avg_effectiveness ASC
                LIMIT 3
            ''')
            
            for row in cursor.fetchall():
                profile_str, context_str, avg_eff, samples = row
                insights['worst_performing_personalities'].append({
                    'personality': json.loads(profile_str),
                    'context': json.loads(context_str),
                    'effectiveness': avg_eff,
                    'samples': samples
                })
            
            # Recent trend (last 10 vs previous 10)
            cursor = conn.execute('''
                SELECT effectiveness_score FROM response_effectiveness
                ORDER BY timestamp DESC LIMIT 20
            ''')
            
            recent_scores = [row[0] for row in cursor.fetchall()]
            if len(recent_scores) >= 20:
                recent_10 = sum(recent_scores[:10]) / 10
                previous_10 = sum(recent_scores[10:20]) / 10
                
                if recent_10 > previous_10 + 0.05:
                    insights['recent_trend'] = 'improving'
                elif recent_10 < previous_10 - 0.05:
                    insights['recent_trend'] = 'declining'
                else:
                    insights['recent_trend'] = 'stable'
        
        return insights
    
    async def suggest_personality_improvements(self) -> List[Dict[str, Any]]:
        """Suggest personality adjustments based on effectiveness data"""
        suggestions = []
        
        insights = await self.get_effectiveness_insights()
        
        # If overall effectiveness is low, suggest adjustments
        if insights['avg_effectiveness'] < 0.6:
            suggestions.append({
                'type': 'overall_improvement_needed',
                'priority': 'high',
                'suggestion': 'Overall response effectiveness is below target. Consider adjusting personality dimensions.',
                'current_avg': insights['avg_effectiveness'],
                'target': 0.7
            })
        
        # Check for declining trend
        if insights['recent_trend'] == 'declining':
            suggestions.append({
                'type': 'declining_trend',
                'priority': 'medium',
                'suggestion': 'Response effectiveness is declining. May need to refresh personality approach.',
                'action': 'Review recent personality changes and consider reverting'
            })
        
        # Learn from best performers
        if insights['best_performing_personalities']:
            best = insights['best_performing_personalities'][0]
            suggestions.append({
                'type': 'learn_from_success',
                'priority': 'low',
                'suggestion': f"High effectiveness ({best['effectiveness']:.2f}) with this personality configuration",
                'successful_personality': best['personality'],
                'context': best['context'],
                'action': 'Consider applying similar configuration to related contexts'
            })
        
        # Address worst performers
        if insights['worst_performing_personalities']:
            worst = insights['worst_performing_personalities'][0]
            if worst['effectiveness'] < 0.4:
                suggestions.append({
                    'type': 'fix_underperformer',
                    'priority': 'high',
                    'suggestion': f"Low effectiveness ({worst['effectiveness']:.2f}) in this configuration",
                    'problematic_personality': worst['personality'],
                    'context': worst['context'],
                    'action': 'Adjust personality dimensions for this context'
                })
        
        return suggestions


if __name__ == "__main__":
    import asyncio
    
    async def test_effectiveness_analyzer():
        print("📊 Testing Response Effectiveness Analyzer")
        print("=" * 60)
        
        analyzer = ResponseEffectivenessAnalyzer()
        
        # Simulate some responses and feedback
        test_scenarios = [
            {
                'penny_response': "Here's a detailed explanation of how async/await works in Python...",
                'user_response': "Thanks! That makes perfect sense now.",
                'time_delay': 25.0,
                'personality': {
                    'communication_formality': 0.6,
                    'technical_depth_preference': 0.8,
                    'sass_level': 'lite'
                },
                'context': {
                    'time_of_day': 'morning',
                    'topic_category': 'technical',
                    'mood_state': 'neutral'
                }
            },
            {
                'penny_response': "Yo, just debug that function lol",
                'user_response': "That's not helpful at all. I need actual guidance.",
                'time_delay': 15.0,
                'personality': {
                    'communication_formality': 0.2,
                    'technical_depth_preference': 0.3,
                    'sass_level': 'spicy'
                },
                'context': {
                    'time_of_day': 'afternoon',
                    'topic_category': 'technical',
                    'mood_state': 'frustrated'
                }
            },
            {
                'penny_response': "Let me walk you through this step by step...",
                'user_response': "Awesome! Can you also explain how to handle errors?",
                'time_delay': 20.0,
                'personality': {
                    'communication_formality': 0.5,
                    'technical_depth_preference': 0.7,
                    'sass_level': 'medium'
                },
                'context': {
                    'time_of_day': 'evening',
                    'topic_category': 'learning',
                    'mood_state': 'excited'
                }
            }
        ]
        
        print("\n📈 Analyzing Response Effectiveness:")
        for i, scenario in enumerate(test_scenarios, 1):
            print(f"\n--- Scenario {i} ---")
            print(f"Penny: {scenario['penny_response'][:50]}...")
            print(f"User: {scenario['user_response']}")
            
            # Analyze user response
            metrics = await analyzer.analyze_user_response(
                scenario['user_response'],
                scenario['penny_response'],
                scenario['time_delay']
            )
            
            print(f"\nMetrics:")
            print(f"  Engagement score: {metrics.engagement_score:.2f}")
            print(f"  Positive indicators: {metrics.satisfaction_indicators}")
            print(f"  Negative indicators: {metrics.dissatisfaction_indicators}")
            print(f"  Follow-up depth: {metrics.follow_up_depth}")
            
            # Record effectiveness
            effectiveness = await analyzer.record_response_effectiveness(
                scenario['penny_response'],
                scenario['personality'],
                scenario['context'],
                metrics
            )
            
            print(f"  Overall effectiveness: {effectiveness:.2f}")
        
        # Get insights
        print("\n\n💡 Effectiveness Insights:")
        insights = await analyzer.get_effectiveness_insights()
        
        print(f"  Total responses tracked: {insights['total_responses_tracked']}")
        print(f"  Average effectiveness: {insights['avg_effectiveness']:.2f}")
        print(f"  Recent trend: {insights['recent_trend']}")
        
        if insights['feedback_distribution']:
            print(f"\n  Feedback distribution:")
            for feedback_type, count in insights['feedback_distribution'].items():
                print(f"    {feedback_type}: {count}")
        
        if insights['best_performing_personalities']:
            print(f"\n  Best performing personality:")
            best = insights['best_performing_personalities'][0]
            print(f"    Effectiveness: {best['effectiveness']:.2f}")
            print(f"    Personality: {best['personality']}")
            print(f"    Context: {best['context']}")
        
        # Get improvement suggestions
        print("\n\n🔧 Improvement Suggestions:")
        suggestions = await analyzer.suggest_personality_improvements()
        
        for i, suggestion in enumerate(suggestions, 1):
            print(f"\n  {i}. [{suggestion['priority']}] {suggestion['type']}")
            print(f"     {suggestion['suggestion']}")
            if 'action' in suggestion:
                print(f"     Action: {suggestion['action']}")
        
        print("\n✅ Response effectiveness analyzer test completed!")
    
    asyncio.run(test_effectiveness_analyzer())
