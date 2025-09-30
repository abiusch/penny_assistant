#!/usr/bin/env python3
"""
Personality Milestones Tracking System
Celebrates and tracks significant achievements in personality learning
"""

import sqlite3
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path

from personality_tracker import PersonalityTracker, PersonalityDimension, PersonalityUpdate

@dataclass
class Milestone:
    """Represents a personality learning milestone"""
    milestone_id: str
    name: str
    description: str
    dimension: Optional[str]
    achievement_criteria: Dict[str, Any]
    celebration_message: str
    rarity: str  # common, uncommon, rare, legendary
    achieved_at: Optional[datetime] = None
    confidence_at_achievement: Optional[float] = None

@dataclass
class MilestoneProgress:
    """Progress toward achieving a milestone"""
    milestone_id: str
    current_progress: float  # 0.0 to 1.0
    requirements_met: List[str]
    requirements_pending: List[str]
    estimated_completion: Optional[str]

class PersonalityMilestones:
    """
    Tracks and celebrates personality learning achievements
    Provides motivation and feedback on learning progress
    """

    def __init__(self, personality_tracker: PersonalityTracker, db_path: str = "data/personality_tracking.db"):
        self.tracker = personality_tracker
        self.db_path = db_path

        # Initialize milestones database
        self._init_milestones_database()

        # Define milestone templates
        self.milestone_templates = {
            # Individual dimension mastery
            'communication_sync': {
                'name': 'Communication Sync',
                'description': 'Penny has learned your communication style preferences',
                'dimension': 'communication_formality',
                'criteria': {'confidence': 0.8, 'consistency': 5},
                'message': "I think I've got your communication style down! We're really clicking now 😊",
                'rarity': 'common'
            },
            'technical_calibration': {
                'name': 'Technical Sweet Spot',
                'description': 'Penny has calibrated to your preferred technical depth',
                'dimension': 'technical_depth_preference',
                'criteria': {'confidence': 0.8, 'consistency': 4},
                'message': "I've dialed in your technical sweet spot - detailed when you want to learn, concise when you just need answers! 🎯",
                'rarity': 'common'
            },
            'humor_mastery': {
                'name': 'Humor Harmony',
                'description': 'Penny has figured out your sense of humor',
                'dimension': 'humor_style_preference',
                'criteria': {'confidence': 0.75, 'positive_responses': 3},
                'message': "I think I've cracked your humor code! 😏 My jokes are landing better now, right?",
                'rarity': 'uncommon'
            },
            'pace_alignment': {
                'name': 'Conversation Rhythm',
                'description': 'Penny has matched your conversation pace preferences',
                'dimension': 'conversation_pace_preference',
                'criteria': {'confidence': 0.8, 'adaptation_success': 4},
                'message': "We've found our conversational rhythm! 🎵 I can tell when you want quick answers vs. deeper discussions",
                'rarity': 'common'
            },
            'proactivity_balance': {
                'name': 'Suggestion Balance',
                'description': 'Penny has learned when to be proactive vs. reactive',
                'dimension': 'proactive_suggestions',
                'criteria': {'confidence': 0.7, 'engagement_rate': 0.6},
                'message': "I've figured out when you want suggestions and when you just want me to answer what you asked! Balance achieved ⚖️",
                'rarity': 'uncommon'
            },
            'support_style_mastery': {
                'name': 'Emotional Intelligence',
                'description': 'Penny has learned your preferred emotional support style',
                'dimension': 'emotional_support_style',
                'criteria': {'confidence': 0.75, 'effectiveness': 3},
                'message': "I'm getting better at reading what kind of support you need - solutions, empathy, or just cheerleading! 💪",
                'rarity': 'rare'
            },

            # Multi-dimensional achievements
            'personality_foundation': {
                'name': 'Personality Foundation',
                'description': 'Multiple personality dimensions learned',
                'criteria': {'dimensions_above_threshold': 3, 'threshold': 0.6},
                'message': "We're building a solid personality foundation together! I'm learning your preferences across multiple areas 🏗️",
                'rarity': 'uncommon'
            },
            'comprehensive_sync': {
                'name': 'Comprehensive Sync',
                'description': 'High confidence across most personality dimensions',
                'criteria': {'dimensions_above_threshold': 5, 'threshold': 0.7},
                'message': "Wow! We're really in sync now. I feel like I understand your communication style across the board! 🤝",
                'rarity': 'rare'
            },
            'personality_mastery': {
                'name': 'Personality Mastery',
                'description': 'Exceptional understanding of user personality',
                'criteria': {'dimensions_above_threshold': 6, 'threshold': 0.8, 'average_confidence': 0.75},
                'message': "This is amazing! I feel like I really *get* you now. Our conversations feel so natural! ✨",
                'rarity': 'legendary'
            },

            # Learning velocity achievements
            'quick_learner': {
                'name': 'Quick Study',
                'description': 'Rapid personality learning in short time',
                'criteria': {'learning_velocity': 2.0, 'time_window_days': 7},
                'message': "I'm a quick study! Already picking up on your preferences after just a few conversations 🚀",
                'rarity': 'uncommon'
            },
            'persistent_learner': {
                'name': 'Persistent Growth',
                'description': 'Consistent learning over extended period',
                'criteria': {'consistent_learning_days': 14, 'min_daily_progress': 0.1},
                'message': "Look at us! Consistently growing and learning together over time. That's relationship building! 📈",
                'rarity': 'rare'
            },

            # Special interaction achievements
            'first_adaptation': {
                'name': 'First Adaptation',
                'description': 'First successful personality adaptation',
                'criteria': {'first_adaptation': True},
                'message': "Just made my first personality adaptation based on what I learned about you! This is exciting! 🎉",
                'rarity': 'common'
            },
            'feedback_responsive': {
                'name': 'Feedback Champion',
                'description': 'Successfully learned from user feedback',
                'criteria': {'feedback_incorporation': 5},
                'message': "I'm getting good at learning from your feedback! Thanks for helping me understand your preferences 🙏",
                'rarity': 'uncommon'
            },
            'natural_conversation': {
                'name': 'Natural Flow',
                'description': 'Conversations feel natural and effortless',
                'criteria': {'conversation_quality_score': 0.8, 'consistency': 5},
                'message': "Our conversations are starting to feel really natural! Like we've been chatting for ages 💬",
                'rarity': 'rare'
            },

            # Advanced achievements
            'personality_evolution': {
                'name': 'Personality Evolution',
                'description': 'Significant personality growth over time',
                'criteria': {'evolution_magnitude': 0.5, 'dimensions_evolved': 4, 'time_period_days': 30},
                'message': "I've evolved so much in understanding you! Looking back at our early conversations vs now - what a journey! 🦋",
                'rarity': 'legendary'
            },
            'context_master': {
                'name': 'Context Master',
                'description': 'Adapts personality based on conversation context',
                'criteria': {'context_adaptations': 10, 'context_accuracy': 0.8},
                'message': "I'm getting really good at adapting my personality based on what we're talking about! Context matters! 🎭",
                'rarity': 'rare'
            }
        }

    def _init_milestones_database(self):
        """Initialize the milestones tracking database"""
        with sqlite3.connect(self.db_path) as conn:
            # Achieved milestones table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS achieved_milestones (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    milestone_id TEXT NOT NULL,
                    achieved_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    confidence_at_achievement REAL,
                    trigger_context TEXT,
                    celebration_shown BOOLEAN DEFAULT FALSE
                )
            ''')

            # Milestone progress table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS milestone_progress (
                    milestone_id TEXT PRIMARY KEY,
                    current_progress REAL DEFAULT 0.0,
                    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
                    progress_data TEXT  -- JSON data about progress
                )
            ''')

            conn.commit()

    async def check_for_milestones(self, personality_updates: Dict[str, PersonalityUpdate],
                                 context: Dict[str, Any]) -> List[Milestone]:
        """Check if any milestones have been achieved"""
        achieved_milestones = []
        personality_state = await self.tracker.get_current_personality_state()

        for milestone_id, template in self.milestone_templates.items():
            # Skip if already achieved
            if await self._is_milestone_achieved(milestone_id):
                continue

            # Check if milestone criteria are met
            is_achieved = await self._check_milestone_criteria(
                milestone_id, template, personality_state, personality_updates, context
            )

            if is_achieved:
                milestone = await self._create_milestone_from_template(milestone_id, template, personality_state)
                await self._record_milestone_achievement(milestone, context)
                achieved_milestones.append(milestone)

        return achieved_milestones

    async def _is_milestone_achieved(self, milestone_id: str) -> bool:
        """Check if a milestone has already been achieved"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                'SELECT id FROM achieved_milestones WHERE milestone_id = ?',
                (milestone_id,)
            )
            return cursor.fetchone() is not None

    async def _check_milestone_criteria(self, milestone_id: str, template: Dict[str, Any],
                                      personality_state: Dict[str, PersonalityDimension],
                                      recent_updates: Dict[str, PersonalityUpdate],
                                      context: Dict[str, Any]) -> bool:
        """Check if milestone criteria are satisfied"""
        criteria = template['criteria']

        # Single dimension criteria
        if 'dimension' in template:
            dimension_name = template['dimension']
            if dimension_name not in personality_state:
                return False

            dimension = personality_state[dimension_name]

            # Check confidence threshold
            if 'confidence' in criteria:
                if dimension.confidence < criteria['confidence']:
                    return False

            # Check consistency (number of recent consistent updates)
            if 'consistency' in criteria:
                consistency_met = await self._check_consistency(
                    dimension_name, criteria['consistency']
                )
                if not consistency_met:
                    return False

            # Check positive responses for humor
            if 'positive_responses' in criteria:
                positive_count = await self._count_positive_humor_responses()
                if positive_count < criteria['positive_responses']:
                    return False

        # Multi-dimensional criteria
        if 'dimensions_above_threshold' in criteria:
            threshold = criteria['threshold']
            dimensions_above = sum(
                1 for dim in personality_state.values()
                if dim.confidence >= threshold
            )
            if dimensions_above < criteria['dimensions_above_threshold']:
                return False

        # Average confidence criteria
        if 'average_confidence' in criteria:
            avg_confidence = sum(dim.confidence for dim in personality_state.values()) / len(personality_state)
            if avg_confidence < criteria['average_confidence']:
                return False

        # Learning velocity criteria
        if 'learning_velocity' in criteria:
            velocity = await self._calculate_learning_velocity(criteria.get('time_window_days', 7))
            if velocity < criteria['learning_velocity']:
                return False

        # Consistent learning criteria
        if 'consistent_learning_days' in criteria:
            consistent_days = await self._count_consistent_learning_days(criteria['consistent_learning_days'])
            if consistent_days < criteria['consistent_learning_days']:
                return False

        # First adaptation check
        if 'first_adaptation' in criteria:
            if not recent_updates:  # No adaptations in this interaction
                return False

        # Special criteria checks
        if 'feedback_incorporation' in criteria:
            feedback_count = await self._count_feedback_incorporation()
            if feedback_count < criteria['feedback_incorporation']:
                return False

        return True

    async def _check_consistency(self, dimension_name: str, required_consistency: int) -> bool:
        """Check if dimension has consistent updates over recent interactions"""
        history = await self.tracker.get_personality_evolution_history(dimension_name, days=14)

        # Count recent updates that show consistency (same direction of change)
        recent_updates = [u for u in history if u.timestamp > datetime.now() - timedelta(days=7)]

        if len(recent_updates) < required_consistency:
            return False

        # Check if updates are moving in consistent direction
        consistent_updates = 0
        for update in recent_updates:
            try:
                old_val = float(update.old_value)
                new_val = float(update.new_value)
                if abs(new_val - old_val) > 0.05:  # Significant change
                    consistent_updates += 1
            except (ValueError, TypeError):
                # Categorical values - count any change as consistent
                if update.old_value != update.new_value:
                    consistent_updates += 1

        return consistent_updates >= required_consistency

    async def _count_positive_humor_responses(self) -> int:
        """Count positive responses to humor in recent interactions"""
        # This would need integration with conversation tracking
        # For now, return a simulated count based on humor style confidence
        personality_state = await self.tracker.get_current_personality_state()
        humor_dim = personality_state.get('humor_style_preference')

        if humor_dim and humor_dim.confidence > 0.6:
            return max(0, int((humor_dim.confidence - 0.5) * 10))

        return 0

    async def _calculate_learning_velocity(self, days: int) -> float:
        """Calculate learning velocity (changes per day) over specified period"""
        history = await self.tracker.get_personality_evolution_history(days=days)
        return len(history) / days

    async def _count_consistent_learning_days(self, required_days: int) -> int:
        """Count consecutive days with learning activity"""
        history = await self.tracker.get_personality_evolution_history(days=required_days + 5)

        if not history:
            return 0

        # Group updates by day
        daily_updates = {}
        for update in history:
            day = update.timestamp.date()
            daily_updates[day] = daily_updates.get(day, 0) + 1

        # Count consecutive days with updates
        consecutive_days = 0
        current_date = datetime.now().date()

        for i in range(required_days):
            check_date = current_date - timedelta(days=i)
            if check_date in daily_updates:
                consecutive_days += 1
            else:
                break

        return consecutive_days

    async def _count_feedback_incorporation(self) -> int:
        """Count instances of successful feedback incorporation"""
        # This would track when user provides feedback and Penny adapts
        # For now, estimate based on overall learning activity
        history = await self.tracker.get_personality_evolution_history(days=30)
        return len([u for u in history if 'feedback' in u.trigger_context.lower()])

    async def _create_milestone_from_template(self, milestone_id: str, template: Dict[str, Any],
                                            personality_state: Dict[str, PersonalityDimension]) -> Milestone:
        """Create milestone instance from template"""
        # Calculate confidence at achievement
        if 'dimension' in template:
            dimension_name = template['dimension']
            confidence = personality_state[dimension_name].confidence if dimension_name in personality_state else 0.0
        else:
            # Average confidence for multi-dimensional milestones
            confidence = sum(dim.confidence for dim in personality_state.values()) / len(personality_state)

        return Milestone(
            milestone_id=milestone_id,
            name=template['name'],
            description=template['description'],
            dimension=template.get('dimension'),
            achievement_criteria=template['criteria'],
            celebration_message=template['message'],
            rarity=template['rarity'],
            achieved_at=datetime.now(),
            confidence_at_achievement=confidence
        )

    async def _record_milestone_achievement(self, milestone: Milestone, context: Dict[str, Any]):
        """Record milestone achievement in database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT INTO achieved_milestones
                (milestone_id, achieved_at, confidence_at_achievement, trigger_context)
                VALUES (?, ?, ?, ?)
            ''', (
                milestone.milestone_id,
                milestone.achieved_at.isoformat(),
                milestone.confidence_at_achievement,
                str(context)
            ))
            conn.commit()

    async def get_milestone_progress(self) -> List[MilestoneProgress]:
        """Get progress toward unachieved milestones"""
        personality_state = await self.tracker.get_current_personality_state()
        progress_list = []

        for milestone_id, template in self.milestone_templates.items():
            # Skip achieved milestones
            if await self._is_milestone_achieved(milestone_id):
                continue

            progress = await self._calculate_milestone_progress(milestone_id, template, personality_state)
            if progress.current_progress > 0:  # Only show milestones with some progress
                progress_list.append(progress)

        # Sort by progress (closest to completion first)
        progress_list.sort(key=lambda x: x.current_progress, reverse=True)
        return progress_list

    async def _calculate_milestone_progress(self, milestone_id: str, template: Dict[str, Any],
                                         personality_state: Dict[str, PersonalityDimension]) -> MilestoneProgress:
        """Calculate progress toward a specific milestone"""
        criteria = template['criteria']
        requirements_met = []
        requirements_pending = []
        progress_scores = []

        # Check each criterion
        if 'dimension' in template:
            dimension_name = template['dimension']
            if dimension_name in personality_state:
                dimension = personality_state[dimension_name]

                if 'confidence' in criteria:
                    target_confidence = criteria['confidence']
                    current_confidence = dimension.confidence
                    confidence_progress = current_confidence / target_confidence

                    if confidence_progress >= 1.0:
                        requirements_met.append(f"Confidence threshold ({target_confidence:.1f})")
                    else:
                        requirements_pending.append(f"Confidence: {current_confidence:.2f}/{target_confidence:.1f}")

                    progress_scores.append(min(1.0, confidence_progress))

        if 'dimensions_above_threshold' in criteria:
            target_count = criteria['dimensions_above_threshold']
            threshold = criteria['threshold']
            current_count = sum(1 for dim in personality_state.values() if dim.confidence >= threshold)
            dimension_progress = current_count / target_count

            if dimension_progress >= 1.0:
                requirements_met.append(f"Dimensions above {threshold} threshold")
            else:
                requirements_pending.append(f"High-confidence dimensions: {current_count}/{target_count}")

            progress_scores.append(min(1.0, dimension_progress))

        # Calculate overall progress
        overall_progress = sum(progress_scores) / len(progress_scores) if progress_scores else 0.0

        # Estimate completion time
        if overall_progress > 0.8:
            estimated_completion = "Very soon!"
        elif overall_progress > 0.5:
            estimated_completion = "A few more conversations"
        elif overall_progress > 0.2:
            estimated_completion = "With some more interaction"
        else:
            estimated_completion = "Still early in the learning process"

        return MilestoneProgress(
            milestone_id=milestone_id,
            current_progress=overall_progress,
            requirements_met=requirements_met,
            requirements_pending=requirements_pending,
            estimated_completion=estimated_completion
        )

    async def get_achieved_milestones(self, days: Optional[int] = None) -> List[Milestone]:
        """Get list of achieved milestones"""
        achieved = []

        with sqlite3.connect(self.db_path) as conn:
            if days:
                cursor = conn.execute('''
                    SELECT milestone_id, achieved_at, confidence_at_achievement
                    FROM achieved_milestones
                    WHERE achieved_at > datetime('now', '-{} days')
                    ORDER BY achieved_at DESC
                '''.format(days))
            else:
                cursor = conn.execute('''
                    SELECT milestone_id, achieved_at, confidence_at_achievement
                    FROM achieved_milestones
                    ORDER BY achieved_at DESC
                ''')

            for row in cursor.fetchall():
                milestone_id, achieved_at, confidence = row
                template = self.milestone_templates.get(milestone_id)

                if template:
                    milestone = Milestone(
                        milestone_id=milestone_id,
                        name=template['name'],
                        description=template['description'],
                        dimension=template.get('dimension'),
                        achievement_criteria=template['criteria'],
                        celebration_message=template['message'],
                        rarity=template['rarity'],
                        achieved_at=datetime.fromisoformat(achieved_at),
                        confidence_at_achievement=confidence
                    )
                    achieved.append(milestone)

        return achieved

    async def get_milestone_summary(self) -> Dict[str, Any]:
        """Get comprehensive milestone summary"""
        achieved_milestones = await self.get_achieved_milestones()
        progress_milestones = await self.get_milestone_progress()

        # Group by rarity
        rarity_counts = {'common': 0, 'uncommon': 0, 'rare': 0, 'legendary': 0}
        for milestone in achieved_milestones:
            rarity_counts[milestone.rarity] += 1

        return {
            'total_achieved': len(achieved_milestones),
            'recent_achievements': len(await self.get_achieved_milestones(days=7)),
            'rarity_breakdown': rarity_counts,
            'in_progress': len(progress_milestones),
            'closest_to_completion': progress_milestones[0] if progress_milestones else None,
            'achievement_rate': len(achieved_milestones) / len(self.milestone_templates),
            'recent_milestones': achieved_milestones[:3]  # Last 3 achieved
        }

    def generate_celebration_message(self, milestone: Milestone) -> str:
        """Generate personalized celebration message for milestone achievement"""
        base_message = milestone.celebration_message

        # Add rarity-specific flourishes
        if milestone.rarity == 'legendary':
            return f"🏆 LEGENDARY ACHIEVEMENT! 🏆\n\n{base_message}\n\nThis is a really special milestone - we've built something amazing together!"
        elif milestone.rarity == 'rare':
            return f"🌟 RARE ACHIEVEMENT! 🌟\n\n{base_message}\n\nThis doesn't happen often - you should be proud of this!"
        elif milestone.rarity == 'uncommon':
            return f"✨ MILESTONE ACHIEVED! ✨\n\n{base_message}\n\nNice work! This shows real progress in our communication."
        else:  # common
            return f"🎉 Milestone unlocked! 🎉\n\n{base_message}"


if __name__ == "__main__":
    async def main():
        # Test personality milestones system
        tracker = PersonalityTracker()
        milestones = PersonalityMilestones(tracker)

        print("🏆 Testing Personality Milestones System")
        print("=" * 50)

        # Test milestone progress
        print("📊 Current milestone progress:")
        progress_list = await milestones.get_milestone_progress()
        for progress in progress_list[:5]:
            milestone_template = milestones.milestone_templates[progress.milestone_id]
            print(f"\n{milestone_template['name']}: {progress.current_progress:.1%}")
            print(f"  Requirements met: {progress.requirements_met}")
            print(f"  Still needed: {progress.requirements_pending}")
            print(f"  Estimated completion: {progress.estimated_completion}")

        # Test milestone summary
        print(f"\n📈 Milestone Summary:")
        summary = await milestones.get_milestone_summary()
        print(f"  Total achieved: {summary['total_achieved']}")
        print(f"  Recent achievements: {summary['recent_achievements']}")
        print(f"  Achievement rate: {summary['achievement_rate']:.1%}")
        print(f"  Rarity breakdown: {summary['rarity_breakdown']}")

        # Test achieved milestones
        achieved = await milestones.get_achieved_milestones()
        if achieved:
            print(f"\n🎖️ Recent achievements:")
            for milestone in achieved[:3]:
                print(f"  {milestone.name} ({milestone.rarity}) - {milestone.achieved_at.strftime('%m/%d')}")

        # Test celebration message
        if achieved:
            print(f"\n🎉 Sample celebration:")
            celebration = milestones.generate_celebration_message(achieved[0])
            print(celebration)

    asyncio.run(main())