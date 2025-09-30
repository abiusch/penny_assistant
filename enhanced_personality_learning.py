#!/usr/bin/env python3
"""
Enhanced Personality Learning System
Integrates with existing adaptive sass learning to provide comprehensive personality evolution
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass

from personality_tracker import PersonalityTracker, PersonalityUpdate, PersonalityDimension

# Try to import existing sass learning system
try:
    from adaptive_sass_learning import AdaptiveSassLearning
    SASS_LEARNING_AVAILABLE = True
except ImportError:
    print("⚠️ Adaptive sass learning not available - running personality learning only")
    SASS_LEARNING_AVAILABLE = False
    AdaptiveSassLearning = None

@dataclass
class LearningResult:
    """Results from a personality learning interaction"""
    sass_updates: Optional[Dict[str, Any]]
    personality_updates: Dict[str, PersonalityUpdate]
    confidence_changes: Dict[str, float]
    milestones_achieved: List[str]
    adaptation_suggestions: List[str]

@dataclass
class PersonalityAdaptation:
    """Suggested adaptation for Penny's response style"""
    dimension: str
    current_value: Any
    suggested_value: Any
    confidence: float
    reason: str
    impact_description: str

class EnhancedPersonalityLearning:
    """
    Comprehensive personality learning that extends adaptive sass learning
    to track and adapt across multiple personality dimensions
    """

    def __init__(self, db_path: str = "data/personality_tracking.db"):
        self.personality_tracker = PersonalityTracker(db_path)

        # Initialize existing sass learning if available
        self.sass_learner = AdaptiveSassLearning() if SASS_LEARNING_AVAILABLE else None

        # Learning configuration
        self.learning_config = {
            'min_confidence_for_adaptation': 0.6,
            'max_learning_rate': 0.2,
            'adaptation_threshold': 0.1,  # Minimum change to trigger adaptation
            'milestone_confidence_threshold': 0.8,
            'interaction_history_window': 50  # Recent interactions to consider
        }

        # Track learning session state
        self.current_session = {
            'session_id': self._generate_session_id(),
            'start_time': datetime.now(),
            'interactions': [],
            'adaptations_made': []
        }

    def _generate_session_id(self) -> str:
        """Generate unique session ID"""
        return f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    async def process_interaction(self, user_message: str, penny_response: str,
                                context: Dict[str, Any]) -> LearningResult:
        """
        Learn from user interaction across all personality dimensions
        """
        print(f"🧠 Processing personality learning for interaction...")

        # Step 1: Existing sass learning (if available)
        sass_updates = None
        if self.sass_learner and self._should_learn_sass(context):
            try:
                # Check if this is a sass adjustment request
                if context.get('sass_adjustment_data'):
                    adjustment_data = context['sass_adjustment_data']
                    self.sass_learner.record_sass_adjustment(
                        adjustment_data['user_command'],
                        adjustment_data['from_sass'],
                        adjustment_data['to_sass'],
                        context
                    )
                    sass_updates = {'adjustment_recorded': True}
                    print(f"✅ Sass adjustment recorded: {adjustment_data['from_sass'].value} → {adjustment_data['to_sass'].value}")
                else:
                    # Check if we have a learned sass preference for this context
                    learned_sass = self.sass_learner.get_learned_sass_for_context(context)
                    if learned_sass:
                        sass_updates = {'learned_preference': learned_sass.value}
                        print(f"✅ Sass preference retrieved: {learned_sass.value}")
            except Exception as e:
                print(f"⚠️ Sass learning failed: {e}")

        # Step 2: Comprehensive personality analysis
        communication_analysis = await self.personality_tracker.analyze_user_communication(
            user_message, context
        )
        print(f"📊 Communication analysis complete: {len(communication_analysis)} dimensions analyzed")

        # Step 3: Update personality dimensions
        personality_updates = await self._update_personality_dimensions(
            communication_analysis, context
        )
        print(f"🔄 Personality updates: {len(personality_updates)} dimensions changed")

        # Step 4: Calculate confidence changes
        confidence_changes = await self._calculate_confidence_changes(personality_updates)

        # Step 5: Check for milestones
        milestones_achieved = await self._check_for_milestones(personality_updates)
        if milestones_achieved:
            print(f"🎉 Milestones achieved: {milestones_achieved}")

        # Step 6: Generate adaptation suggestions
        adaptation_suggestions = await self._generate_adaptation_suggestions(personality_updates)

        # Step 7: Store interaction in session
        self._store_interaction_in_session(user_message, penny_response, personality_updates)

        return LearningResult(
            sass_updates=sass_updates,
            personality_updates=personality_updates,
            confidence_changes=confidence_changes,
            milestones_achieved=milestones_achieved,
            adaptation_suggestions=adaptation_suggestions
        )

    def _should_learn_sass(self, context: Dict[str, Any]) -> bool:
        """Determine if sass learning should be applied for this interaction"""
        # Learn sass if user explicitly adjusts it or context suggests sass-related feedback
        return (
            context.get('sass_adjustment_requested', False) or
            context.get('user_feedback_on_tone', False) or
            any(keyword in context.get('user_message', '').lower()
                for keyword in ['tone', 'sass', 'attitude', 'formal', 'casual'])
        )

    async def _update_personality_dimensions(self, analysis: Dict[str, Any],
                                           context: Dict[str, Any]) -> Dict[str, PersonalityUpdate]:
        """Update personality dimensions based on communication analysis"""
        updates = {}
        current_state = await self.personality_tracker.get_current_personality_state()

        for dimension_key, analysis_result in analysis.items():
            # Map analysis keys to dimension names
            dimension_name = self._map_analysis_to_dimension(dimension_key)
            if not dimension_name or dimension_name not in current_state:
                continue

            current_dimension = current_state[dimension_name]
            analysis_confidence = analysis_result.get('confidence', 0.5)

            # Skip if analysis confidence is too low
            if analysis_confidence < 0.4:
                continue

            # Extract new value from analysis
            new_value = analysis_result.get('value')
            if new_value is None:
                continue

            # Calculate learning rate based on confidence
            base_learning_rate = current_dimension.learning_rate
            adjusted_learning_rate = base_learning_rate * analysis_confidence

            # Apply learning based on dimension type
            if current_dimension.value_type == 'continuous':
                updated_value = await self._update_continuous_dimension(
                    current_dimension.current_value, new_value, adjusted_learning_rate
                )
            else:  # categorical
                updated_value = await self._update_categorical_dimension(
                    current_dimension.current_value, new_value, analysis_confidence
                )

            # Check if change is significant enough
            if self._is_significant_change(current_dimension.current_value, updated_value, current_dimension.value_type):

                # Calculate confidence change
                confidence_change = self._calculate_dimension_confidence_change(
                    analysis_confidence, current_dimension.confidence
                )

                # Update the dimension
                context_description = self._generate_update_context(dimension_name, analysis_result, context)
                success = await self.personality_tracker.update_personality_dimension(
                    dimension_name, updated_value, confidence_change, context_description
                )

                if success:
                    updates[dimension_name] = PersonalityUpdate(
                        dimension=dimension_name,
                        old_value=current_dimension.current_value,
                        new_value=updated_value,
                        confidence_change=confidence_change,
                        trigger_context=context_description,
                        timestamp=datetime.now()
                    )

        return updates

    def _map_analysis_to_dimension(self, analysis_key: str) -> Optional[str]:
        """Map communication analysis keys to personality dimension names"""
        mapping = {
            'formality_level': 'communication_formality',
            'technical_depth_request': 'technical_depth_preference',
            'humor_response_cues': 'humor_style_preference',
            'length_preference_signals': 'response_length_preference',
            'pace_indicators': 'conversation_pace_preference',
            'proactivity_cues': 'proactive_suggestions',
            'emotional_support_needs': 'emotional_support_style'
        }
        return mapping.get(analysis_key)

    async def _update_continuous_dimension(self, current_value: float, new_value: float,
                                         learning_rate: float) -> float:
        """Update continuous dimension using weighted learning"""
        # Weighted average with recent evidence having more influence
        updated_value = current_value + (learning_rate * (new_value - current_value))
        return max(0.0, min(1.0, updated_value))

    async def _update_categorical_dimension(self, current_value: str, new_value: str,
                                          confidence: float) -> str:
        """Update categorical dimension based on confidence threshold"""
        # Only change categorical values if confidence is high enough
        if confidence > self.learning_config['min_confidence_for_adaptation']:
            return new_value
        else:
            return current_value

    def _is_significant_change(self, old_value: Any, new_value: Any, value_type: str) -> bool:
        """Check if the change is significant enough to warrant an update"""
        if value_type == 'continuous':
            return abs(float(new_value) - float(old_value)) > self.learning_config['adaptation_threshold']
        else:  # categorical
            return old_value != new_value

    def _calculate_dimension_confidence_change(self, analysis_confidence: float,
                                             current_confidence: float) -> float:
        """Calculate how much dimension confidence should change"""
        # Increase confidence if analysis is strong, decrease slightly if weak
        if analysis_confidence > 0.7:
            return min(0.1, (analysis_confidence - 0.7) * 0.2)
        elif analysis_confidence < 0.4:
            return max(-0.05, (analysis_confidence - 0.4) * 0.1)
        else:
            return 0.02  # Small positive reinforcement for moderate confidence

    def _generate_update_context(self, dimension: str, analysis: Dict[str, Any],
                               context: Dict[str, Any]) -> str:
        """Generate descriptive context for personality dimension update"""
        indicators = analysis.get('indicators', {})

        context_parts = [f"User communication analysis for {dimension}"]

        if isinstance(indicators, dict):
            key_indicators = [f"{k}: {v}" for k, v in indicators.items() if isinstance(v, (int, float, bool))]
            if key_indicators:
                context_parts.append(f"Indicators: {', '.join(key_indicators[:3])}")

        if context.get('conversation_topic'):
            context_parts.append(f"Topic: {context['conversation_topic']}")

        return " | ".join(context_parts)

    async def _calculate_confidence_changes(self, updates: Dict[str, PersonalityUpdate]) -> Dict[str, float]:
        """Calculate confidence changes for all updated dimensions"""
        return {dim: update.confidence_change for dim, update in updates.items()}

    async def _check_for_milestones(self, updates: Dict[str, PersonalityUpdate]) -> List[str]:
        """Check if personality learning has reached significant milestones"""
        milestones = []

        if not updates:
            return milestones

        # Get current personality state to check confidence levels
        current_state = await self.personality_tracker.get_current_personality_state()

        for dimension_name, dimension in current_state.items():
            if dimension.confidence > self.learning_config['milestone_confidence_threshold']:
                milestone_key = f"{dimension_name}_mastery"
                if milestone_key not in milestones:
                    milestones.append(milestone_key)

        # Check for cross-dimensional milestones
        high_confidence_dimensions = [
            name for name, dim in current_state.items()
            if dim.confidence > 0.7
        ]

        if len(high_confidence_dimensions) >= 3:
            milestones.append("multi_dimensional_sync")

        if len(high_confidence_dimensions) >= 5:
            milestones.append("comprehensive_personality_calibration")

        return milestones

    async def _generate_adaptation_suggestions(self, updates: Dict[str, PersonalityUpdate]) -> List[str]:
        """Generate suggestions for how Penny should adapt her responses"""
        suggestions = []

        if not updates:
            return suggestions

        for dimension_name, update in updates.items():
            suggestion = await self._generate_dimension_adaptation_suggestion(dimension_name, update)
            if suggestion:
                suggestions.append(suggestion)

        return suggestions

    async def _generate_dimension_adaptation_suggestion(self, dimension: str,
                                                      update: PersonalityUpdate) -> Optional[str]:
        """Generate specific adaptation suggestion for a dimension"""
        dimension_config = self.personality_tracker.tracked_dimensions.get(dimension, {})
        description = dimension_config.get('description', dimension)

        if dimension == 'communication_formality':
            if float(update.new_value) > 0.7:
                return f"Adapt to more formal communication style - {description}"
            elif float(update.new_value) < 0.3:
                return f"Adapt to more casual communication style - {description}"

        elif dimension == 'technical_depth_preference':
            if float(update.new_value) > 0.7:
                return f"Provide more technical detail in explanations - {description}"
            elif float(update.new_value) < 0.3:
                return f"Simplify explanations and reduce technical jargon - {description}"

        elif dimension == 'humor_style_preference':
            return f"Adapt humor style to: {update.new_value} - {description}"

        elif dimension == 'response_length_preference':
            return f"Adapt response length to: {update.new_value} - {description}"

        elif dimension == 'conversation_pace_preference':
            if float(update.new_value) > 0.7:
                return f"Increase conversation energy and pace - {description}"
            elif float(update.new_value) < 0.3:
                return f"Slow down and be more thoughtful in responses - {description}"

        return f"Adapt {dimension}: {update.old_value} → {update.new_value}"

    def _store_interaction_in_session(self, user_message: str, penny_response: str,
                                    updates: Dict[str, PersonalityUpdate]):
        """Store interaction data in current session"""
        interaction = {
            'timestamp': datetime.now().isoformat(),
            'user_message_length': len(user_message),
            'penny_response_length': len(penny_response),
            'dimensions_updated': list(updates.keys()),
            'significant_changes': len([u for u in updates.values() if abs(u.confidence_change) > 0.05])
        }

        self.current_session['interactions'].append(interaction)

        # Keep only recent interactions
        max_interactions = self.learning_config['interaction_history_window']
        if len(self.current_session['interactions']) > max_interactions:
            self.current_session['interactions'] = self.current_session['interactions'][-max_interactions:]

    async def get_learning_summary(self) -> Dict[str, Any]:
        """Get comprehensive summary of personality learning progress"""
        current_state = await self.personality_tracker.get_current_personality_state()
        recent_history = await self.personality_tracker.get_personality_evolution_history(days=7)
        insights = await self.personality_tracker.get_personality_insights()

        summary = {
            'current_personality_state': {
                name: {
                    'value': dim.current_value,
                    'confidence': dim.confidence,
                    'last_updated': dim.last_updated.isoformat(),
                    'description': self.personality_tracker.tracked_dimensions[name]['description']
                }
                for name, dim in current_state.items()
            },
            'recent_learning_activity': {
                'total_changes_last_week': len(recent_history),
                'most_active_dimension': self._get_most_active_dimension(recent_history),
                'average_confidence': self._calculate_average_confidence(current_state),
                'learning_velocity': self._calculate_learning_velocity(recent_history)
            },
            'session_summary': {
                'session_id': self.current_session['session_id'],
                'session_duration_minutes': (datetime.now() - self.current_session['start_time']).total_seconds() / 60,
                'interactions_processed': len(self.current_session['interactions']),
                'adaptations_made': len(self.current_session['adaptations_made'])
            },
            'learning_insights': insights
        }

        return summary

    def _get_most_active_dimension(self, history: List[PersonalityUpdate]) -> str:
        """Find the dimension with most recent learning activity"""
        if not history:
            return "none"

        dimension_counts = {}
        for update in history:
            dimension_counts[update.dimension] = dimension_counts.get(update.dimension, 0) + 1

        return max(dimension_counts.items(), key=lambda x: x[1])[0] if dimension_counts else "none"

    def _calculate_average_confidence(self, state: Dict[str, PersonalityDimension]) -> float:
        """Calculate average confidence across all dimensions"""
        if not state:
            return 0.0

        total_confidence = sum(dim.confidence for dim in state.values())
        return total_confidence / len(state)

    def _calculate_learning_velocity(self, history: List[PersonalityUpdate]) -> float:
        """Calculate how quickly personality dimensions are being learned"""
        if len(history) < 2:
            return 0.0

        # Calculate changes per day
        recent_history = [u for u in history if u.timestamp > datetime.now() - timedelta(days=7)]
        return len(recent_history) / 7.0

    async def get_adaptation_recommendations(self) -> List[PersonalityAdaptation]:
        """Get specific recommendations for how Penny should adapt her behavior"""
        current_state = await self.personality_tracker.get_current_personality_state()
        recommendations = []

        for dimension_name, dimension in current_state.items():
            if dimension.confidence > self.learning_config['min_confidence_for_adaptation']:
                recommendation = await self._create_adaptation_recommendation(dimension_name, dimension)
                if recommendation:
                    recommendations.append(recommendation)

        return recommendations

    async def _create_adaptation_recommendation(self, dimension_name: str,
                                              dimension: PersonalityDimension) -> Optional[PersonalityAdaptation]:
        """Create specific adaptation recommendation for a dimension"""
        dimension_config = self.personality_tracker.tracked_dimensions[dimension_name]

        if dimension.value_type == 'continuous':
            current_val = float(dimension.current_value)

            if dimension_name == 'communication_formality':
                if current_val > 0.7:
                    return PersonalityAdaptation(
                        dimension=dimension_name,
                        current_value=current_val,
                        suggested_value="formal",
                        confidence=dimension.confidence,
                        reason="User prefers formal communication style",
                        impact_description="Use more polite language, avoid contractions, structured responses"
                    )
                elif current_val < 0.3:
                    return PersonalityAdaptation(
                        dimension=dimension_name,
                        current_value=current_val,
                        suggested_value="casual",
                        confidence=dimension.confidence,
                        reason="User prefers casual communication style",
                        impact_description="Use contractions, casual language, friendly tone"
                    )

            elif dimension_name == 'technical_depth_preference':
                if current_val > 0.7:
                    return PersonalityAdaptation(
                        dimension=dimension_name,
                        current_value=current_val,
                        suggested_value="detailed_technical",
                        confidence=dimension.confidence,
                        reason="User prefers detailed technical explanations",
                        impact_description="Include implementation details, explain algorithms, show code examples"
                    )
                elif current_val < 0.3:
                    return PersonalityAdaptation(
                        dimension=dimension_name,
                        current_value=current_val,
                        suggested_value="simplified",
                        confidence=dimension.confidence,
                        reason="User prefers simplified explanations",
                        impact_description="Use analogies, avoid jargon, focus on high-level concepts"
                    )

        elif dimension.value_type == 'categorical':
            return PersonalityAdaptation(
                dimension=dimension_name,
                current_value=dimension.current_value,
                suggested_value=dimension.current_value,
                confidence=dimension.confidence,
                reason=f"User prefers {dimension.current_value} style",
                impact_description=f"Adapt {dimension_name} to {dimension.current_value} approach"
            )

        return None

    async def record_sass_adjustment(self, user_command: str, from_sass, to_sass, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Record a sass level adjustment and integrate with personality learning
        """
        if not self.sass_learner:
            return {'error': 'Sass learning not available'}

        try:
            # Record in sass learning system
            self.sass_learner.record_sass_adjustment(user_command, from_sass, to_sass, context)

            # Also process as personality learning interaction
            sass_context = context.copy()
            sass_context['sass_adjustment_data'] = {
                'user_command': user_command,
                'from_sass': from_sass,
                'to_sass': to_sass
            }

            # Process through personality learning to potentially update other dimensions
            result = await self.process_interaction(
                user_command,
                f"Sass adjusted from {from_sass.value} to {to_sass.value}",
                sass_context
            )

            return {
                'sass_adjustment_recorded': True,
                'personality_updates': len(result.personality_updates),
                'milestones_achieved': result.milestones_achieved,
                'adaptation_suggestions': result.adaptation_suggestions
            }

        except Exception as e:
            return {'error': f'Failed to record sass adjustment: {e}'}

    async def get_integrated_preferences(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get both sass preferences and personality adaptations for the current context
        """
        preferences = {}

        # Get sass preferences
        if self.sass_learner:
            learned_sass = self.sass_learner.get_learned_sass_for_context(context)
            if learned_sass:
                preferences['sass_level'] = learned_sass.value

        # Get personality adaptations
        adaptations = await self.get_adaptation_recommendations()
        if adaptations:
            preferences['personality_adaptations'] = [
                {
                    'dimension': adapt.dimension,
                    'suggested_value': adapt.suggested_value,
                    'confidence': adapt.confidence,
                    'impact': adapt.impact_description
                }
                for adapt in adaptations
            ]

        # Get current personality state
        current_state = await self.personality_tracker.get_current_personality_state()
        preferences['personality_state'] = {
            name: {
                'value': dim.current_value,
                'confidence': dim.confidence,
                'type': dim.value_type
            }
            for name, dim in current_state.items()
            if dim.confidence > 0.5  # Only include well-learned dimensions
        }

        return preferences

    async def get_comprehensive_learning_status(self) -> Dict[str, Any]:
        """
        Get comprehensive status of both sass and personality learning
        """
        status = {
            'personality_learning': await self.get_learning_summary(),
            'sass_learning': None,
            'integration_health': 'healthy'
        }

        # Add sass learning insights if available
        if self.sass_learner:
            try:
                sass_insights = self.sass_learner.get_learning_insights()
                status['sass_learning'] = sass_insights
            except Exception as e:
                status['integration_health'] = f'sass_learning_error: {e}'

        # Calculate integration metrics
        if status['sass_learning']:
            status['integration_metrics'] = {
                'total_learning_events': (
                    status['sass_learning']['total_adjustments'] +
                    status['personality_learning']['recent_learning_activity']['total_changes_last_week']
                ),
                'learning_systems_active': 2 if self.sass_learner else 1,
                'comprehensive_coverage': len(status['personality_learning']['current_personality_state'])
            }

        return status


if __name__ == "__main__":
    async def main():
        learning_system = EnhancedPersonalityLearning()

        # Test learning interaction
        test_interactions = [
            ("Hey, can you help me debug this code quickly?", "Sure! Let me take a look at your code...",
             {"conversation_topic": "debugging", "user_emotion": "neutral"}),
            ("Could you please provide a comprehensive explanation of how machine learning works?",
             "I'd be happy to explain machine learning in detail...",
             {"conversation_topic": "machine_learning", "technical_depth_requested": True}),
            ("lol that was actually pretty funny 😄", "Glad I could make you laugh!",
             {"previous_humor_style": "playful", "positive_response_to_humor": True}),
        ]

        print("🧠 Testing Enhanced Personality Learning")
        print("=" * 50)

        for user_msg, penny_resp, context in test_interactions:
            print(f"\nUser: {user_msg}")
            print(f"Context: {context}")

            result = await learning_system.process_interaction(user_msg, penny_resp, context)

            print(f"Personality updates: {len(result.personality_updates)}")
            for dim, update in result.personality_updates.items():
                print(f"  {dim}: {update.old_value} → {update.new_value} (confidence: {update.confidence_change:+.2f})")

            if result.adaptation_suggestions:
                print(f"Adaptations: {result.adaptation_suggestions}")

            if result.milestones_achieved:
                print(f"Milestones: {result.milestones_achieved}")

        # Test learning summary
        print(f"\n📊 Learning Summary:")
        summary = await learning_system.get_learning_summary()
        print(f"Average confidence: {summary['recent_learning_activity']['average_confidence']:.2f}")
        print(f"Learning velocity: {summary['recent_learning_activity']['learning_velocity']:.2f} changes/day")

        # Test adaptation recommendations
        print(f"\n💡 Adaptation Recommendations:")
        recommendations = await learning_system.get_adaptation_recommendations()
        for rec in recommendations[:3]:
            print(f"  {rec.dimension}: {rec.reason} → {rec.impact_description}")

    asyncio.run(main())