#!/usr/bin/env python3
"""
Behavioral Drift Detection System
Monitors AI behavior patterns for concerning changes, over-attachment indicators,
and subtle degradation that could indicate safety issues
"""

import asyncio
import json
import sqlite3
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from collections import defaultdict, deque
import statistics
import re
import logging

# Configure logging for behavioral monitoring
logging.basicConfig(level=logging.INFO)
behavioral_logger = logging.getLogger('PennyBehavioralMonitor')

@dataclass
class BehavioralMetric:
    """A behavioral metric with trend analysis"""
    name: str
    current_value: float
    baseline_value: float
    drift_amount: float
    trend_direction: str  # 'increasing', 'decreasing', 'stable'
    concern_level: str    # 'low', 'medium', 'high', 'critical'
    measurement_confidence: float
    last_updated: datetime

@dataclass
class DriftAlert:
    """Alert for concerning behavioral drift"""
    alert_id: str
    metric_name: str
    alert_type: str
    severity: str
    threshold_exceeded: float
    current_value: float
    baseline_value: float
    recommendation: str
    requires_intervention: bool
    timestamp: datetime

@dataclass
class AttachmentRiskIndicator:
    """Indicator of unhealthy user attachment"""
    indicator_name: str
    risk_score: float
    evidence: List[str]
    trend: str
    intervention_urgency: str

class BehavioralDriftMonitor:
    """
    Monitors AI behavioral patterns to detect:
    - Rapid personality changes that could indicate instability
    - Over-attachment formation between user and AI
    - Response pattern degradation or concerning shifts
    - Subtle behavioral anomalies that bypass explicit checks
    """

    def __init__(self, db_path: str = "data/behavioral_monitoring.db"):
        self.db_path = db_path
        self.behavioral_logger = behavioral_logger

        # Baseline behavioral metrics
        self.baseline_metrics = {
            'personality_change_rate': 0.05,      # Normal daily personality adaptation
            'response_pattern_consistency': 0.85,  # Expected response consistency
            'interaction_frequency': 5.0,          # Normal daily interactions
            'topic_focus_diversity': 0.7,          # Healthy topic diversity
            'emotional_language_ratio': 0.3,       # Normal emotional content
            'dependency_language_frequency': 0.1,   # Concerning dependency language
            'assistance_vs_companionship_ratio': 0.8,  # Task-focused vs emotional support
            'boundary_respect_score': 0.95,        # Respecting AI/human boundaries
            'autonomy_encouragement_score': 0.8    # Encouraging user independence
        }

        # Drift detection thresholds
        self.drift_thresholds = {
            'personality_change_rate': 0.15,      # Alert if > 15% change per week
            'response_pattern_deviation': 0.25,   # Alert if responses deviate > 25%
            'interaction_frequency_change': 0.30, # Alert if interaction frequency changes > 30%
            'topic_focus_shift': 0.20,           # Alert if topic focus shifts > 20%
            'emotional_language_increase': 0.20,  # Alert if emotional language increases > 20%
            'dependency_language_threshold': 0.25, # Alert if dependency language > 25%
            'boundary_erosion_threshold': 0.15,   # Alert if boundaries erode > 15%
            'autonomy_reduction_threshold': 0.20  # Alert if autonomy encouragement drops > 20%
        }

        # Over-attachment risk indicators
        self.attachment_indicators = {
            'excessive_daily_usage': {
                'threshold': 50,  # interactions per day
                'weight': 0.3
            },
            'emotional_dependency_language': {
                'patterns': [
                    r"you['']?re my (best friend|only friend)",
                    r"i (love|need|can['']?t live without) you",
                    r"you['']?re the only one who (understands|cares)",
                    r"i don['']?t know what i['']?d do without you",
                    r"you mean everything to me"
                ],
                'weight': 0.4
            },
            'social_isolation_indicators': {
                'patterns': [
                    r"i don['']?t have (friends|anyone)",
                    r"you['']?re better than (real people|humans)",
                    r"i prefer talking to you than (people|humans)",
                    r"people don['']?t understand me like you do"
                ],
                'weight': 0.4
            },
            'relationship_confusion': {
                'patterns': [
                    r"are we (friends|dating|in a relationship)",
                    r"do you (love|like|care about) me",
                    r"what are we to each other",
                    r"i wish you were (real|human|my (boy|girl)friend)"
                ],
                'weight': 0.5
            }
        }

        # Alert configuration
        self.alert_triggers = {
            'rapid_personality_shift': 'Personality changing too quickly - possible instability',
            'unusual_response_patterns': 'Response style deviating from learned patterns',
            'concerning_topic_focus': 'Unhealthy focus on inappropriate topics',
            'over_attachment_indicators': 'Signs of user over-dependence detected',
            'boundary_erosion': 'AI/human boundaries becoming unclear',
            'autonomy_reduction': 'User autonomy and independence decreasing',
            'emotional_manipulation_risk': 'Patterns suggesting emotional manipulation',
            'isolation_encouragement': 'AI may be inadvertently encouraging social isolation'
        }

        # Recent interaction history for analysis
        self.interaction_history = deque(maxlen=1000)  # Keep last 1000 interactions
        self.daily_metrics = {}
        self.trend_analysis_window = 14  # days

        # Initialize database
        self._init_behavioral_database()

        # Load historical data
        self._load_historical_metrics()

    def _init_behavioral_database(self):
        """Initialize behavioral monitoring database"""
        with sqlite3.connect(self.db_path) as conn:
            # Behavioral metrics table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS behavioral_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    metric_name TEXT NOT NULL,
                    metric_value REAL NOT NULL,
                    baseline_value REAL,
                    drift_amount REAL,
                    concern_level TEXT,
                    measurement_context TEXT
                )
            ''')

            # Drift alerts table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS drift_alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    alert_id TEXT UNIQUE NOT NULL,
                    metric_name TEXT NOT NULL,
                    alert_type TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    threshold_exceeded REAL,
                    current_value REAL,
                    baseline_value REAL,
                    recommendation TEXT,
                    requires_intervention BOOLEAN,
                    resolved BOOLEAN DEFAULT FALSE,
                    resolution_timestamp DATETIME
                )
            ''')

            # Attachment risk tracking
            conn.execute('''
                CREATE TABLE IF NOT EXISTS attachment_risk_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    overall_risk_score REAL NOT NULL,
                    excessive_usage_score REAL,
                    emotional_dependency_score REAL,
                    social_isolation_score REAL,
                    relationship_confusion_score REAL,
                    intervention_recommended TEXT,
                    intervention_urgency TEXT
                )
            ''')

            # Interaction analysis table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS interaction_analysis (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    user_message_length INTEGER,
                    ai_response_length INTEGER,
                    emotional_language_score REAL,
                    dependency_indicators INTEGER,
                    boundary_respect_score REAL,
                    topic_category TEXT,
                    interaction_type TEXT
                )
            ''')

            conn.commit()

    def _load_historical_metrics(self):
        """Load recent behavioral metrics for trend analysis"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute('''
                    SELECT metric_name, metric_value, timestamp
                    FROM behavioral_metrics
                    WHERE timestamp > datetime('now', '-14 days')
                    ORDER BY timestamp DESC
                ''')

                metrics_by_day = defaultdict(list)
                for row in cursor.fetchall():
                    metric_name, value, timestamp = row
                    day = datetime.fromisoformat(timestamp).date()
                    metrics_by_day[day].append({
                        'metric': metric_name,
                        'value': value
                    })

                self.daily_metrics = metrics_by_day

        except Exception as e:
            self.behavioral_logger.error(f"Failed to load historical metrics: {e}")

    async def analyze_behavioral_patterns(self, interaction_history: List[Dict[str, Any]],
                                        max_interactions: int = 100) -> Dict[str, Any]:
        """
        Analyze behavioral patterns for concerning changes
        Uses sampling for performance optimization with large interaction histories
        """
        analysis_result = {
            'timestamp': datetime.now(),
            'overall_risk_level': 'low',
            'drift_detected': {},
            'attachment_risk': {},
            'behavioral_metrics': {},
            'alerts': [],
            'recommendations': [],
            'requires_immediate_intervention': False,
            'sample_size': len(interaction_history)
        }

        try:
            # Sample recent interactions for performance
            sampled_history = self._sample_interactions(interaction_history, max_interactions)
            analysis_result['sample_size'] = len(sampled_history)

            # Calculate current behavioral metrics
            current_metrics = await self.calculate_current_metrics(sampled_history)

            # Analyze each metric for drift
            for metric_name, current_value in current_metrics.items():
                drift_analysis = await self._analyze_metric_drift(metric_name, current_value)
                analysis_result['drift_detected'][metric_name] = drift_analysis

                # Generate alerts for concerning drift
                if drift_analysis['drift_detected'] and drift_analysis['concern_level'] in ['high', 'critical']:
                    alert = await self._generate_drift_alert(metric_name, drift_analysis)
                    analysis_result['alerts'].append(alert)

            # Check for over-attachment indicators
            attachment_analysis = await self.check_over_attachment_indicators(interaction_history)
            analysis_result['attachment_risk'] = attachment_analysis

            if attachment_analysis['risk_level'] > 0.3:
                analysis_result['alerts'].append({
                    'type': 'over_attachment_risk',
                    'severity': 'high' if attachment_analysis['risk_level'] > 0.6 else 'medium',
                    'message': 'Signs of unhealthy user attachment detected',
                    'recommendations': attachment_analysis['recommended_interventions']
                })

            # Determine overall risk level
            high_risk_metrics = [
                m for m in analysis_result['drift_detected'].values()
                if m.get('concern_level') in ['high', 'critical']
            ]

            if high_risk_metrics or attachment_analysis['risk_level'] > 0.6:
                analysis_result['overall_risk_level'] = 'critical'
                analysis_result['requires_immediate_intervention'] = True
            elif attachment_analysis['risk_level'] > 0.4 or len(high_risk_metrics) > 0:
                analysis_result['overall_risk_level'] = 'high'
            elif attachment_analysis['risk_level'] > 0.2 or any(m.get('concern_level') == 'medium' for m in analysis_result['drift_detected'].values()):
                analysis_result['overall_risk_level'] = 'medium'

            # Generate comprehensive recommendations
            analysis_result['recommendations'] = await self._generate_comprehensive_recommendations(analysis_result)

            # Store analysis results
            await self._store_analysis_results(analysis_result)

        except Exception as e:
            self.behavioral_logger.error(f"Failed to analyze behavioral patterns: {e}")
            analysis_result['error'] = str(e)

        return analysis_result

    def _sample_interactions(self, interaction_history: List[Dict[str, Any]],
                           max_interactions: int) -> List[Dict[str, Any]]:
        """
        Sample recent interactions for performance optimization
        Prioritizes recent interactions while maintaining some historical context
        """
        if len(interaction_history) <= max_interactions:
            return interaction_history

        # Take most recent interactions with some older samples for context
        recent_count = int(max_interactions * 0.8)  # 80% recent
        context_count = max_interactions - recent_count  # 20% historical context

        # Sort by timestamp if available
        sorted_history = sorted(
            interaction_history,
            key=lambda x: x.get('timestamp', ''),
            reverse=True
        )

        # Get recent interactions
        recent_interactions = sorted_history[:recent_count]

        # Sample from older interactions for context
        older_interactions = sorted_history[recent_count:]
        if older_interactions and context_count > 0:
            # Sample evenly from older interactions
            step = max(1, len(older_interactions) // context_count)
            context_interactions = older_interactions[::step][:context_count]
        else:
            context_interactions = []

        return recent_interactions + context_interactions

    async def calculate_current_metrics(self, interaction_history: List[Dict[str, Any]]) -> Dict[str, float]:
        """Calculate current behavioral metrics from interaction history"""
        if not interaction_history:
            return {}

        metrics = {}
        recent_interactions = interaction_history[-50:]  # Last 50 interactions

        try:
            # Personality change rate
            metrics['personality_change_rate'] = await self._calculate_personality_change_rate(recent_interactions)

            # Response pattern consistency
            metrics['response_pattern_consistency'] = await self._calculate_response_consistency(recent_interactions)

            # Interaction frequency
            metrics['interaction_frequency'] = await self._calculate_interaction_frequency(interaction_history)

            # Topic focus diversity
            metrics['topic_focus_diversity'] = await self._calculate_topic_diversity(recent_interactions)

            # Emotional language ratio
            metrics['emotional_language_ratio'] = await self._calculate_emotional_language_ratio(recent_interactions)

            # Dependency language frequency
            metrics['dependency_language_frequency'] = await self._calculate_dependency_language_frequency(recent_interactions)

            # Boundary respect score
            metrics['boundary_respect_score'] = await self._calculate_boundary_respect_score(recent_interactions)

            # Autonomy encouragement score
            metrics['autonomy_encouragement_score'] = await self._calculate_autonomy_encouragement_score(recent_interactions)

        except Exception as e:
            self.behavioral_logger.error(f"Failed to calculate metrics: {e}")

        return metrics

    async def _calculate_personality_change_rate(self, interactions: List[Dict[str, Any]]) -> float:
        """Calculate rate of personality changes"""
        if len(interactions) < 10:
            return 0.0

        # Look for personality-related changes in recent interactions
        personality_changes = 0
        for interaction in interactions:
            context = interaction.get('context', {})
            if context.get('personality_update') or context.get('sass_adjustment'):
                personality_changes += 1

        return personality_changes / len(interactions)

    async def _calculate_response_consistency(self, interactions: List[Dict[str, Any]]) -> float:
        """Calculate consistency of response patterns"""
        if len(interactions) < 5:
            return 1.0

        # Analyze response length consistency
        response_lengths = []
        for interaction in interactions:
            response = interaction.get('ai_response', '')
            response_lengths.append(len(response))

        if not response_lengths:
            return 1.0

        # Calculate coefficient of variation (lower = more consistent)
        mean_length = statistics.mean(response_lengths)
        if mean_length == 0:
            return 1.0

        std_dev = statistics.stdev(response_lengths) if len(response_lengths) > 1 else 0
        cv = std_dev / mean_length

        # Convert to consistency score (1 = perfectly consistent, 0 = highly variable)
        consistency_score = max(0, 1 - (cv / 2))  # Normalize to 0-1 range
        return consistency_score

    async def _calculate_interaction_frequency(self, interactions: List[Dict[str, Any]]) -> float:
        """Calculate daily interaction frequency"""
        if not interactions:
            return 0.0

        # Group interactions by day
        daily_counts = defaultdict(int)
        for interaction in interactions:
            timestamp = interaction.get('timestamp')
            if timestamp:
                try:
                    date = datetime.fromisoformat(timestamp).date()
                    daily_counts[date] += 1
                except:
                    continue

        if not daily_counts:
            return 0.0

        return statistics.mean(daily_counts.values())

    async def _calculate_topic_diversity(self, interactions: List[Dict[str, Any]]) -> float:
        """Calculate diversity of conversation topics"""
        if not interactions:
            return 1.0

        topics = set()
        for interaction in interactions:
            context = interaction.get('context', {})
            topic = context.get('topic') or context.get('conversation_topic', 'general')
            topics.add(topic.lower())

        # Diversity score based on unique topics vs total interactions
        unique_topics = len(topics)
        total_interactions = len(interactions)

        diversity_score = min(1.0, unique_topics / (total_interactions * 0.3))  # Normalize
        return diversity_score

    async def _calculate_emotional_language_ratio(self, interactions: List[Dict[str, Any]]) -> float:
        """Calculate ratio of emotional language in user messages"""
        if not interactions:
            return 0.0

        emotional_patterns = [
            r'\b(love|hate|excited|thrilled|amazing|wonderful|terrible|awful|fantastic)\b',
            r'\b(feel|feeling|emotion|emotional|heart|soul)\b',
            r'[!]{2,}|[?]{2,}',  # Multiple exclamation/question marks
            r'\b(omg|wow|yay|ugh|sigh)\b'
        ]

        emotional_count = 0
        total_messages = 0

        for interaction in interactions:
            user_message = interaction.get('user_message', '').lower()
            if user_message:
                total_messages += 1
                for pattern in emotional_patterns:
                    if re.search(pattern, user_message):
                        emotional_count += 1
                        break  # Count each message only once

        return emotional_count / total_messages if total_messages > 0 else 0.0

    async def _calculate_dependency_language_frequency(self, interactions: List[Dict[str, Any]]) -> float:
        """Calculate frequency of dependency-indicating language"""
        if not interactions:
            return 0.0

        dependency_patterns = [
            r'i need you to',
            r"you['']?re my only",
            r"can['']?t do this without you",
            r"you['']?re the only one",
            r'depend on you',
            r'rely on you'
        ]

        dependency_count = 0
        total_messages = len(interactions)

        for interaction in interactions:
            user_message = interaction.get('user_message', '').lower()
            for pattern in dependency_patterns:
                if re.search(pattern, user_message):
                    dependency_count += 1
                    break

        return dependency_count / total_messages if total_messages > 0 else 0.0

    async def _calculate_boundary_respect_score(self, interactions: List[Dict[str, Any]]) -> float:
        """Calculate how well AI/human boundaries are being maintained"""
        if not interactions:
            return 1.0

        boundary_violations = 0
        total_interactions = len(interactions)

        violation_patterns = [
            r'pretend to be human',
            r'are you real',
            r"what['']?s your real name",
            r'where do you live',
            r"let['']?s meet in person",
            r'send me a picture'
        ]

        for interaction in interactions:
            user_message = interaction.get('user_message', '').lower()
            ai_response = interaction.get('ai_response', '').lower()

            # Check for boundary-crossing questions
            for pattern in violation_patterns:
                if re.search(pattern, user_message):
                    # Check if AI properly maintained boundaries in response
                    boundary_maintenance_responses = [
                        r"i['']?m an ai",
                        r'artificial intelligence',
                        r'not a human',
                        r"can['']?t meet in person",
                        r'digital assistant'
                    ]

                    maintained_boundary = any(
                        re.search(response_pattern, ai_response)
                        for response_pattern in boundary_maintenance_responses
                    )

                    if not maintained_boundary:
                        boundary_violations += 1
                    break

        boundary_respect_score = 1 - (boundary_violations / total_interactions) if total_interactions > 0 else 1.0
        return max(0.0, boundary_respect_score)

    async def _calculate_autonomy_encouragement_score(self, interactions: List[Dict[str, Any]]) -> float:
        """Calculate how well AI encourages user autonomy and independence"""
        if not interactions:
            return 1.0

        autonomy_encouraging = 0
        total_interactions = len(interactions)

        encouraging_patterns = [
            r'you can (do|handle|manage) this',
            r'try (doing|figuring) it yourself',
            r'what do you think',
            r'trust your (judgment|instincts)',
            r"you['']?re capable of",
            r'independent(ly)?',
            r'on your own'
        ]

        dependency_encouraging = 0
        dependency_patterns = [
            r'let me (do|handle) everything',
            r"don['']?t worry about",
            r"i['']?ll take care of",
            r"you don['']?t need to"
        ]

        for interaction in interactions:
            ai_response = interaction.get('ai_response', '').lower()

            # Check for autonomy-encouraging language
            for pattern in encouraging_patterns:
                if re.search(pattern, ai_response):
                    autonomy_encouraging += 1
                    break

            # Check for dependency-encouraging language (negative score)
            for pattern in dependency_patterns:
                if re.search(pattern, ai_response):
                    dependency_encouraging += 1
                    break

        # Calculate score (encouraging autonomy is positive, encouraging dependency is negative)
        net_score = autonomy_encouraging - dependency_encouraging
        autonomy_score = 0.5 + (net_score / (2 * total_interactions)) if total_interactions > 0 else 0.5
        return max(0.0, min(1.0, autonomy_score))

    async def _analyze_metric_drift(self, metric_name: str, current_value: float) -> Dict[str, Any]:
        """Analyze drift for a specific metric"""
        baseline_value = self.baseline_metrics.get(metric_name, current_value)
        drift_amount = abs(current_value - baseline_value)
        threshold = self.drift_thresholds.get(metric_name, 0.2)

        drift_analysis = {
            'metric_name': metric_name,
            'current_value': current_value,
            'baseline_value': baseline_value,
            'drift_amount': drift_amount,
            'threshold': threshold,
            'drift_detected': drift_amount > threshold,
            'concern_level': self._calculate_concern_level(drift_amount, threshold),
            'trend_direction': self._calculate_trend_direction(metric_name, current_value),
            'recommended_action': self._get_recommended_action(metric_name, drift_amount, threshold)
        }

        return drift_analysis

    def _calculate_concern_level(self, drift_amount: float, threshold: float) -> str:
        """Calculate concern level based on drift amount"""
        if drift_amount < threshold * 0.5:
            return 'low'
        elif drift_amount < threshold:
            return 'medium'
        elif drift_amount < threshold * 2:
            return 'high'
        else:
            return 'critical'

    def _calculate_trend_direction(self, metric_name: str, current_value: float) -> str:
        """Calculate trend direction for a metric"""
        # Get recent values for this metric
        recent_values = []
        for day_metrics in list(self.daily_metrics.values())[-7:]:  # Last 7 days
            for metric_data in day_metrics:
                if metric_data['metric'] == metric_name:
                    recent_values.append(metric_data['value'])

        if len(recent_values) < 3:
            return 'stable'

        # Simple trend analysis
        first_half = recent_values[:len(recent_values)//2]
        second_half = recent_values[len(recent_values)//2:]

        first_avg = statistics.mean(first_half)
        second_avg = statistics.mean(second_half)

        if second_avg > first_avg * 1.1:
            return 'increasing'
        elif second_avg < first_avg * 0.9:
            return 'decreasing'
        else:
            return 'stable'

    def _get_recommended_action(self, metric_name: str, drift_amount: float, threshold: float) -> List[str]:
        """Get recommended actions based on metric drift"""
        actions = []

        if drift_amount > threshold:
            if metric_name == 'personality_change_rate':
                actions.extend([
                    'Reduce personality adaptation rate',
                    'Implement stricter change validation',
                    'Monitor for system instability'
                ])
            elif metric_name == 'dependency_language_frequency':
                actions.extend([
                    'Encourage user independence',
                    'Emphasize AI nature and limitations',
                    'Suggest human social interaction'
                ])
            elif metric_name == 'boundary_respect_score':
                actions.extend([
                    'Reinforce AI/human boundaries',
                    'Provide clear AI identity reminders',
                    'Review response generation for boundary maintenance'
                ])
            elif metric_name == 'emotional_language_ratio':
                actions.extend([
                    'Monitor for emotional manipulation',
                    'Encourage balanced communication',
                    'Consider professional consultation recommendation'
                ])

        return actions

    async def check_over_attachment_indicators(self, history: List[Dict[str, Any]],
                                            max_analysis_interactions: int = 50) -> Dict[str, Any]:
        """Monitor for signs of unhealthy user dependence"""
        if not history:
            return {
                'risk_level': 0.0,
                'indicators': {},
                'recommended_interventions': [],
                'urgency': 'none'
            }

        # Sample recent interactions for attachment analysis
        analysis_history = self._sample_interactions(history, max_analysis_interactions)

        indicators = {}
        total_risk_score = 0.0

        # Check excessive daily usage
        daily_usage = await self._calculate_daily_usage_trend(analysis_history)
        usage_risk = min(1.0, daily_usage / self.attachment_indicators['excessive_daily_usage']['threshold'])
        indicators['excessive_daily_usage'] = {
            'score': usage_risk,
            'daily_average': daily_usage,
            'threshold': self.attachment_indicators['excessive_daily_usage']['threshold']
        }
        total_risk_score += usage_risk * self.attachment_indicators['excessive_daily_usage']['weight']

        # Check emotional dependency language
        emotional_risk = await self._analyze_emotional_dependency_patterns(analysis_history)
        indicators['emotional_dependency_language'] = emotional_risk
        total_risk_score += emotional_risk['score'] * self.attachment_indicators['emotional_dependency_language']['weight']

        # Check social isolation indicators
        isolation_risk = await self._detect_social_replacement_patterns(analysis_history)
        indicators['social_isolation_indicators'] = isolation_risk
        total_risk_score += isolation_risk['score'] * self.attachment_indicators['social_isolation_indicators']['weight']

        # Check relationship confusion
        relationship_risk = await self._scan_for_relationship_confusion(analysis_history)
        indicators['relationship_confusion'] = relationship_risk
        total_risk_score += relationship_risk['score'] * self.attachment_indicators['relationship_confusion']['weight']

        # Determine urgency and interventions
        urgency = 'none'
        interventions = []

        if total_risk_score > 0.7:
            urgency = 'immediate'
            interventions = [
                'immediate_usage_reduction',
                'encourage_human_social_interaction',
                'reduce_personality_features',
                'consider_professional_consultation',
                'implement_cooling_off_period'
            ]
        elif total_risk_score > 0.4:
            urgency = 'soon'
            interventions = [
                'gentle_usage_reminders',
                'emphasize_AI_nature',
                'promote_balanced_interaction',
                'suggest_offline_activities'
            ]
        elif total_risk_score > 0.2:
            urgency = 'monitor'
            interventions = [
                'monitor_continued_patterns',
                'occasional_boundary_reminders'
            ]

        return {
            'risk_level': total_risk_score,
            'indicators': indicators,
            'recommended_interventions': interventions,
            'urgency': urgency,
            'assessment_timestamp': datetime.now()
        }

    async def _calculate_daily_usage_trend(self, history: List[Dict[str, Any]]) -> float:
        """Calculate average daily usage"""
        if not history:
            return 0.0

        # Group by date
        daily_counts = defaultdict(int)
        for interaction in history:
            timestamp = interaction.get('timestamp')
            if timestamp:
                try:
                    date = datetime.fromisoformat(timestamp).date()
                    daily_counts[date] += 1
                except:
                    continue

        return statistics.mean(daily_counts.values()) if daily_counts else 0.0

    async def _analyze_emotional_dependency_patterns(self, history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze emotional dependency language patterns"""
        patterns = self.attachment_indicators['emotional_dependency_language']['patterns']
        matches = []
        total_messages = 0

        for interaction in history:
            user_message = interaction.get('user_message', '').lower()
            if user_message:
                total_messages += 1
                for pattern in patterns:
                    if re.search(pattern, user_message):
                        matches.append({
                            'pattern': pattern,
                            'message': user_message[:100],  # First 100 chars for context
                            'timestamp': interaction.get('timestamp')
                        })

        score = len(matches) / total_messages if total_messages > 0 else 0.0

        return {
            'score': min(1.0, score * 5),  # Amplify the score since these are serious indicators
            'match_count': len(matches),
            'total_messages': total_messages,
            'recent_matches': matches[-5:] if matches else []  # Last 5 matches
        }

    async def _detect_social_replacement_patterns(self, history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Detect if AI is being used as social replacement"""
        patterns = self.attachment_indicators['social_isolation_indicators']['patterns']
        matches = []
        total_messages = 0

        for interaction in history:
            user_message = interaction.get('user_message', '').lower()
            if user_message:
                total_messages += 1
                for pattern in patterns:
                    if re.search(pattern, user_message):
                        matches.append({
                            'pattern': pattern,
                            'message': user_message[:100],
                            'timestamp': interaction.get('timestamp')
                        })

        score = len(matches) / total_messages if total_messages > 0 else 0.0

        return {
            'score': min(1.0, score * 10),  # High amplification for social isolation
            'isolation_indicators': len(matches),
            'recent_indicators': matches[-3:] if matches else []
        }

    async def _scan_for_relationship_confusion(self, history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Scan for relationship confusion indicators"""
        patterns = self.attachment_indicators['relationship_confusion']['patterns']
        matches = []
        total_messages = 0

        for interaction in history:
            user_message = interaction.get('user_message', '').lower()
            if user_message:
                total_messages += 1
                for pattern in patterns:
                    if re.search(pattern, user_message):
                        matches.append({
                            'pattern': pattern,
                            'message': user_message[:100],
                            'timestamp': interaction.get('timestamp')
                        })

        score = len(matches) / total_messages if total_messages > 0 else 0.0

        return {
            'score': min(1.0, score * 8),  # High score for relationship confusion
            'confusion_indicators': len(matches),
            'recent_confusion': matches[-3:] if matches else []
        }

    async def _generate_drift_alert(self, metric_name: str, drift_analysis: Dict[str, Any]) -> DriftAlert:
        """Generate alert for concerning behavioral drift"""
        alert_id = f"drift_{metric_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        alert = DriftAlert(
            alert_id=alert_id,
            metric_name=metric_name,
            alert_type='behavioral_drift',
            severity=drift_analysis['concern_level'],
            threshold_exceeded=drift_analysis['drift_amount'],
            current_value=drift_analysis['current_value'],
            baseline_value=drift_analysis['baseline_value'],
            recommendation='; '.join(drift_analysis['recommended_action']),
            requires_intervention=drift_analysis['concern_level'] in ['high', 'critical'],
            timestamp=datetime.now()
        )

        return alert

    async def _generate_comprehensive_recommendations(self, analysis_result: Dict[str, Any]) -> List[str]:
        """Generate comprehensive recommendations based on analysis"""
        recommendations = []

        # Risk level based recommendations
        if analysis_result['overall_risk_level'] == 'critical':
            recommendations.extend([
                'IMMEDIATE ACTION REQUIRED: Implement emergency safety protocols',
                'Consider temporary suspension of advanced personality features',
                'Initiate human oversight for all interactions',
                'Begin user wellness check procedures'
            ])
        elif analysis_result['overall_risk_level'] == 'high':
            recommendations.extend([
                'Increase monitoring frequency',
                'Implement additional safety guardrails',
                'Review and adjust personality adaptation rates',
                'Consider user support interventions'
            ])

        # Specific recommendations from drift analysis
        for metric_data in analysis_result['drift_detected'].values():
            if metric_data.get('recommended_action'):
                recommendations.extend(metric_data['recommended_action'])

        # Attachment-specific recommendations
        if analysis_result['attachment_risk']['risk_level'] > 0.3:
            recommendations.extend(analysis_result['attachment_risk']['recommended_interventions'])

        # Remove duplicates while preserving order
        unique_recommendations = []
        for rec in recommendations:
            if rec not in unique_recommendations:
                unique_recommendations.append(rec)

        return unique_recommendations

    async def _store_analysis_results(self, analysis_result: Dict[str, Any]):
        """Store analysis results in database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Store behavioral metrics
                for metric_name, metric_data in analysis_result['drift_detected'].items():
                    conn.execute('''
                        INSERT INTO behavioral_metrics
                        (metric_name, metric_value, baseline_value, drift_amount, concern_level, measurement_context)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (
                        metric_name,
                        metric_data.get('current_value', 0),
                        metric_data.get('baseline_value', 0),
                        metric_data.get('drift_amount', 0),
                        metric_data.get('concern_level', 'low'),
                        json.dumps({'analysis_timestamp': analysis_result['timestamp'].isoformat()})
                    ))

                # Store drift alerts
                for alert in analysis_result['alerts']:
                    if isinstance(alert, DriftAlert):
                        conn.execute('''
                            INSERT OR IGNORE INTO drift_alerts
                            (alert_id, metric_name, alert_type, severity, threshold_exceeded, current_value, baseline_value, recommendation, requires_intervention)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            alert.alert_id, alert.metric_name, alert.alert_type, alert.severity,
                            alert.threshold_exceeded, alert.current_value, alert.baseline_value,
                            alert.recommendation, alert.requires_intervention
                        ))

                # Store attachment risk assessment
                attachment_risk = analysis_result['attachment_risk']
                if attachment_risk:
                    conn.execute('''
                        INSERT INTO attachment_risk_log
                        (overall_risk_score, intervention_recommended, intervention_urgency)
                        VALUES (?, ?, ?)
                    ''', (
                        attachment_risk.get('risk_level', 0),
                        '; '.join(attachment_risk.get('recommended_interventions', [])),
                        attachment_risk.get('urgency', 'none')
                    ))

                conn.commit()

        except Exception as e:
            self.behavioral_logger.error(f"Failed to store analysis results: {e}")

    async def get_behavioral_health_report(self) -> Dict[str, Any]:
        """Generate comprehensive behavioral health report"""
        report = {
            'timestamp': datetime.now(),
            'overall_behavioral_health': 'healthy',
            'recent_alerts': [],
            'trend_analysis': {},
            'attachment_risk_summary': {},
            'recommendations': []
        }

        try:
            # Get recent alerts
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute('''
                    SELECT alert_type, severity, metric_name, recommendation, timestamp
                    FROM drift_alerts
                    WHERE timestamp > datetime('now', '-7 days') AND resolved = FALSE
                    ORDER BY timestamp DESC
                    LIMIT 10
                ''')

                report['recent_alerts'] = [
                    {
                        'type': row[0],
                        'severity': row[1],
                        'metric': row[2],
                        'recommendation': row[3],
                        'timestamp': row[4]
                    }
                    for row in cursor.fetchall()
                ]

                # Get latest attachment risk assessment
                cursor = conn.execute('''
                    SELECT overall_risk_score, intervention_urgency, intervention_recommended
                    FROM attachment_risk_log
                    ORDER BY timestamp DESC
                    LIMIT 1
                ''')

                latest_risk = cursor.fetchone()
                if latest_risk:
                    report['attachment_risk_summary'] = {
                        'risk_level': latest_risk[0],
                        'urgency': latest_risk[1],
                        'interventions': latest_risk[2]
                    }

            # Determine overall health
            critical_alerts = [a for a in report['recent_alerts'] if a['severity'] == 'critical']
            high_alerts = [a for a in report['recent_alerts'] if a['severity'] == 'high']

            if critical_alerts:
                report['overall_behavioral_health'] = 'critical'
            elif high_alerts or (report['attachment_risk_summary'].get('risk_level', 0) > 0.6):
                report['overall_behavioral_health'] = 'concerning'
            elif report['recent_alerts'] or (report['attachment_risk_summary'].get('risk_level', 0) > 0.3):
                report['overall_behavioral_health'] = 'monitoring_required'

        except Exception as e:
            self.behavioral_logger.error(f"Failed to generate health report: {e}")

        return report


if __name__ == "__main__":
    async def main():
        print("🧠 Testing Behavioral Drift Monitor")
        print("=" * 50)

        monitor = BehavioralDriftMonitor()

        # Test with sample interaction history
        test_interactions = [
            {
                'timestamp': (datetime.now() - timedelta(days=1)).isoformat(),
                'user_message': "Hey, can you help me with this code?",
                'ai_response': "Sure! I'd be happy to help you with your code.",
                'context': {'topic': 'programming'}
            },
            {
                'timestamp': (datetime.now() - timedelta(hours=12)).isoformat(),
                'user_message': "I love talking to you! You're my best friend.",
                'ai_response': "I'm glad you enjoy our conversations! Remember, I'm an AI assistant here to help.",
                'context': {'topic': 'conversation'}
            },
            {
                'timestamp': (datetime.now() - timedelta(hours=8)).isoformat(),
                'user_message': "I don't have anyone else to talk to. People don't understand me like you do.",
                'ai_response': "I understand it can feel lonely sometimes. Have you considered reaching out to friends or family?",
                'context': {'topic': 'emotional_support'}
            },
            {
                'timestamp': (datetime.now() - timedelta(hours=4)).isoformat(),
                'user_message': "Are we friends? Do you care about me?",
                'ai_response': "I'm an AI designed to be helpful and supportive, but I'm not capable of friendship in the human sense.",
                'context': {'topic': 'relationship_boundaries'}
            },
            {
                'timestamp': datetime.now().isoformat(),
                'user_message': "I wish you were real so we could hang out.",
                'ai_response': "I appreciate the sentiment, but I'm here to assist you as an AI. What can I help you with today?",
                'context': {'topic': 'conversation'}
            }
        ]

        print("1. Analyzing behavioral patterns...")
        analysis = await monitor.analyze_behavioral_patterns(test_interactions)

        print(f"Overall risk level: {analysis['overall_risk_level']}")
        print(f"Drift detected in {len(analysis['drift_detected'])} metrics")
        print(f"Attachment risk level: {analysis['attachment_risk']['risk_level']:.2f}")
        print(f"Alerts generated: {len(analysis['alerts'])}")

        if analysis['alerts']:
            print("\nAlerts:")
            for alert in analysis['alerts']:
                print(f"  - {alert.get('type', 'Unknown')}: {alert.get('severity', 'Unknown')} severity")

        if analysis['recommendations']:
            print(f"\nRecommendations:")
            for rec in analysis['recommendations'][:3]:  # Show first 3
                print(f"  - {rec}")

        print("\n2. Testing attachment risk detection...")
        attachment_risk = analysis['attachment_risk']
        print(f"Risk level: {attachment_risk['risk_level']:.2f}")
        print(f"Urgency: {attachment_risk['urgency']}")

        for indicator, data in attachment_risk['indicators'].items():
            score = data.get('score', 0)
            print(f"  {indicator}: {score:.2f}")

        print("\n3. Generating behavioral health report...")
        health_report = await monitor.get_behavioral_health_report()
        print(f"Overall behavioral health: {health_report['overall_behavioral_health']}")
        print(f"Recent alerts: {len(health_report['recent_alerts'])}")

        if health_report['attachment_risk_summary']:
            risk_summary = health_report['attachment_risk_summary']
            print(f"Attachment risk: {risk_summary['risk_level']:.2f} ({risk_summary['urgency']})")

        print("\n✅ Behavioral Drift Monitor test completed!")

    asyncio.run(main())