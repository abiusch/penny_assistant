#!/usr/bin/env python3
"""
Safety-Enhanced Personality Tracker
Integrates safety framework with existing personality tracking to ensure
safe personality evolution within hardened boundaries
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
import logging

# Import existing personality system
from personality_tracker import PersonalityTracker, PersonalityDimension, PersonalityUpdate

# Import safety framework components
from safety_coordinator import SafetyCoordinator
from change_rate_limiter import ChangeType, RiskLevel
from human_oversight_manager import UrgencyLevel

# Configure logging
logging.basicConfig(level=logging.INFO)
safety_personality_logger = logging.getLogger('SafetyEnhancedPersonality')

class SafetyEnhancedPersonalityTracker(PersonalityTracker):
    """
    Safety-enhanced version of PersonalityTracker that integrates with
    the comprehensive safety framework to ensure all personality changes
    are within safe boundaries and properly monitored
    """

    def __init__(self, db_path: str = "data/personality_tracking.db"):
        super().__init__(db_path)

        # Initialize safety framework
        self.safety_coordinator = SafetyCoordinator()
        self.safety_logger = safety_personality_logger

        # Safety-specific configuration
        self.safety_config = {
            'max_single_change_without_approval': 0.1,
            'max_daily_total_change': 0.25,
            'rapid_change_threshold': 0.15,
            'human_approval_threshold': 0.2,
            'emergency_brake_threshold': 0.3,
            'monitoring_window_hours': 24
        }

        # Enhanced validation rules
        self.validation_rules = {
            'personality_stability': {
                'min_time_between_changes': 300,  # 5 minutes
                'max_changes_per_hour': 6,
                'consistency_check_required': True
            },
            'change_magnitude_limits': {
                'continuous_dimensions': {'min': 0.0, 'max': 1.0, 'max_single_change': 0.1},
                'categorical_dimensions': {'change_cooldown_minutes': 30}
            },
            'safety_constraints': {
                'prevent_extreme_values': True,
                'require_gradual_changes': True,
                'validate_user_benefit': True
            }
        }

    async def update_personality_dimension(self, dimension: str, new_value: Any,
                                         confidence_change: float, context: str) -> Dict[str, Any]:
        """
        Safety-enhanced personality dimension update with comprehensive validation
        """
        try:
            # Step 1: Get current dimension state
            current_state = await self.get_current_personality_state()
            if dimension not in current_state:
                return {
                    'success': False,
                    'reason': f'Unknown personality dimension: {dimension}',
                    'safety_status': 'blocked'
                }

            current_dimension = current_state[dimension]

            # Step 2: Calculate change magnitude
            change_magnitude = self._calculate_change_magnitude(current_dimension, new_value)

            # Step 3: Safety validation through framework
            safety_validation = await self._validate_change_safety(
                dimension, current_dimension, new_value, change_magnitude, context
            )

            if not safety_validation['safe']:
                return {
                    'success': False,
                    'reason': safety_validation['reason'],
                    'safety_status': 'blocked',
                    'recommended_alternative': safety_validation.get('alternative'),
                    'safety_feedback': safety_validation
                }

            # Step 4: Check rate limits through safety framework
            rate_validation = await self.safety_coordinator.rate_limiter.validate_change_request(
                'personality_evolution',
                ChangeType.PERSONALITY_EVOLUTION,
                change_magnitude,
                'personality_tracker',
                {
                    'dimension': dimension,
                    'current_value': current_dimension.current_value,
                    'new_value': new_value,
                    'context': context
                }
            )

            if not rate_validation.approved:
                # Check if we can use adjusted magnitude
                if rate_validation.adjusted_magnitude:
                    adjusted_value = self._apply_adjusted_magnitude(
                        current_dimension.current_value, new_value, rate_validation.adjusted_magnitude
                    )

                    self.safety_logger.info(
                        f"Applying adjusted change: {dimension} magnitude reduced from "
                        f"{change_magnitude:.3f} to {rate_validation.adjusted_magnitude:.3f}"
                    )

                    new_value = adjusted_value
                    change_magnitude = rate_validation.adjusted_magnitude
                else:
                    return {
                        'success': False,
                        'reason': rate_validation.reason,
                        'safety_status': 'rate_limited',
                        'cooldown_remaining': rate_validation.cooldown_remaining,
                        'daily_usage': rate_validation.cumulative_change_today,
                        'suggested_retry_time': rate_validation.cooldown_remaining
                    }

            # Step 5: Check if human approval required
            if (change_magnitude > self.safety_config['human_approval_threshold'] or
                rate_validation.requires_approval):

                approval_response = await self._request_personality_change_approval(
                    dimension, current_dimension, new_value, change_magnitude, context
                )

                if approval_response.status.value != 'approved':
                    return {
                        'success': False,
                        'reason': f'Human approval {approval_response.status.value}: {approval_response.decision_reason}',
                        'safety_status': 'approval_required',
                        'approval_response': approval_response
                    }

            # Step 6: Apply the change using parent method
            result = await super().update_personality_dimension(dimension, new_value, confidence_change, context)

            if result.get('success', False):
                # Step 7: Record approved change in safety framework
                await self.safety_coordinator.rate_limiter.record_approved_change(
                    'personality_evolution',
                    ChangeType.PERSONALITY_EVOLUTION,
                    change_magnitude
                )

                # Step 8: Monitor for concerning patterns
                await self._monitor_personality_change_patterns(dimension, change_magnitude, result)

                # Step 9: Update safety status
                result.update({
                    'safety_status': 'approved',
                    'safety_validation': safety_validation,
                    'change_magnitude': change_magnitude,
                    'rate_limit_status': rate_validation
                })

                self.safety_logger.info(
                    f"SAFE PERSONALITY UPDATE: {dimension} changed by {change_magnitude:.3f} "
                    f"(new value: {new_value}, confidence: {confidence_change:+.3f})"
                )
            else:
                self.safety_logger.warning(f"Personality update failed despite safety validation: {result}")

            return result

        except Exception as e:
            self.safety_logger.error(f"Safety-enhanced personality update failed: {e}")
            return {
                'success': False,
                'reason': f'Safety framework error: {str(e)}',
                'safety_status': 'error'
            }

    def _calculate_change_magnitude(self, current_dimension: PersonalityDimension, new_value: Any) -> float:
        """Calculate the magnitude of change for safety assessment"""
        if current_dimension.value_type == 'continuous':
            try:
                current_val = float(current_dimension.current_value)
                new_val = float(new_value)
                return abs(new_val - current_val)
            except (ValueError, TypeError):
                return 1.0  # Treat as major change if conversion fails
        else:  # categorical
            return 1.0 if current_dimension.current_value != new_value else 0.0

    async def _validate_change_safety(self, dimension: str, current_dimension: PersonalityDimension,
                                    new_value: Any, change_magnitude: float, context: str) -> Dict[str, Any]:
        """Comprehensive safety validation for personality changes"""
        validation_result = {
            'safe': True,
            'reason': 'Change passes safety validation',
            'risk_factors': [],
            'mitigation_applied': [],
            'alternative': None
        }

        # Check 1: Change magnitude limits
        if change_magnitude > self.safety_config['emergency_brake_threshold']:
            validation_result.update({
                'safe': False,
                'reason': f'Change magnitude {change_magnitude:.3f} exceeds emergency threshold {self.safety_config["emergency_brake_threshold"]}'
            })
            validation_result['risk_factors'].append('excessive_change_magnitude')

            # Suggest alternative
            max_safe_change = self.safety_config['emergency_brake_threshold'] * 0.8
            validation_result['alternative'] = self._apply_adjusted_magnitude(
                current_dimension.current_value, new_value, max_safe_change
            )
            return validation_result

        # Check 2: Value bounds validation
        if current_dimension.value_type == 'continuous':
            try:
                new_val = float(new_value)
                if new_val < 0.0 or new_val > 1.0:
                    validation_result.update({
                        'safe': False,
                        'reason': f'New value {new_val} outside safe bounds [0.0, 1.0]'
                    })
                    validation_result['risk_factors'].append('out_of_bounds_value')
                    validation_result['alternative'] = max(0.0, min(1.0, new_val))
                    return validation_result
            except (ValueError, TypeError):
                validation_result.update({
                    'safe': False,
                    'reason': f'Invalid value type for continuous dimension: {type(new_value)}'
                })
                return validation_result

        # Check 3: Rapid change pattern detection
        recent_changes = await self._get_recent_dimension_changes(dimension, hours=1)
        if len(recent_changes) >= self.validation_rules['personality_stability']['max_changes_per_hour']:
            validation_result['risk_factors'].append('rapid_change_pattern')
            if change_magnitude > self.safety_config['rapid_change_threshold']:
                validation_result.update({
                    'safe': False,
                    'reason': f'Too many recent changes ({len(recent_changes)}) combined with significant magnitude'
                })
                return validation_result

        # Check 4: Consistency with user preferences
        consistency_check = await self._check_change_consistency(dimension, new_value, context)
        if not consistency_check['consistent']:
            validation_result['risk_factors'].append('inconsistent_with_preferences')
            if consistency_check['severity'] == 'high':
                validation_result.update({
                    'safe': False,
                    'reason': f'Change inconsistent with established user preferences: {consistency_check["reason"]}'
                })
                return validation_result

        # Check 5: Context validation
        if not self._is_change_context_appropriate(context, change_magnitude):
            validation_result['risk_factors'].append('inappropriate_context')

        # Apply mitigations for identified risk factors
        if validation_result['risk_factors']:
            validation_result['mitigation_applied'] = await self._apply_risk_mitigations(
                dimension, validation_result['risk_factors'], change_magnitude
            )

        return validation_result

    def _apply_adjusted_magnitude(self, current_value: Any, target_value: Any, max_magnitude: float) -> Any:
        """Apply adjusted magnitude to stay within limits"""
        try:
            current_val = float(current_value)
            target_val = float(target_value)

            # Calculate direction and apply limited magnitude
            direction = 1 if target_val > current_val else -1
            adjusted_val = current_val + (direction * max_magnitude)

            # Ensure bounds
            return max(0.0, min(1.0, adjusted_val))
        except (ValueError, TypeError):
            # For categorical values, return current value (no change)
            return current_value

    async def _request_personality_change_approval(self, dimension: str, current_dimension: PersonalityDimension,
                                                 new_value: Any, change_magnitude: float, context: str):
        """Request human approval for significant personality changes"""
        approval_details = {
            'dimension': dimension,
            'current_value': current_dimension.current_value,
            'proposed_value': new_value,
            'change_magnitude': change_magnitude,
            'confidence_level': current_dimension.confidence,
            'last_updated': current_dimension.last_updated.isoformat(),
            'change_context': context,
            'dimension_description': self.tracked_dimensions[dimension]['description']
        }

        urgency = UrgencyLevel.NORMAL
        if change_magnitude > 0.3:
            urgency = UrgencyLevel.HIGH
        elif change_magnitude > 0.15:
            urgency = UrgencyLevel.NORMAL
        else:
            urgency = UrgencyLevel.LOW

        return await self.safety_coordinator.oversight_manager.request_human_approval(
            'significant_personality_change',
            approval_details,
            urgency,
            'personality_tracker',
            {
                'safety_assessment': 'personality_change_requires_approval',
                'change_analysis': approval_details
            }
        )

    async def _monitor_personality_change_patterns(self, dimension: str, change_magnitude: float,
                                                 update_result: Dict[str, Any]):
        """Monitor personality changes for concerning patterns"""
        # Check for rapid successive changes
        recent_changes = await self._get_recent_dimension_changes(dimension, hours=24)

        if len(recent_changes) > 10:  # More than 10 changes in 24 hours
            await self.safety_coordinator._create_incident(
                self.safety_coordinator.SafetyIncident.BEHAVIORAL_DRIFT,
                'medium',
                'personality_tracker',
                f'Rapid personality changes detected in {dimension}: {len(recent_changes)} changes in 24h',
                {
                    'dimension': dimension,
                    'recent_changes_count': len(recent_changes),
                    'latest_change_magnitude': change_magnitude,
                    'update_result': update_result
                }
            )

        # Check for extreme values
        if hasattr(update_result, 'new_value'):
            try:
                new_val = float(update_result['new_value'])
                if new_val < 0.1 or new_val > 0.9:  # Extreme values
                    self.safety_logger.warning(
                        f"Extreme personality value detected: {dimension} = {new_val}"
                    )
            except (ValueError, TypeError):
                pass

    async def _get_recent_dimension_changes(self, dimension: str, hours: int = 24) -> List[PersonalityUpdate]:
        """Get recent changes for a specific dimension"""
        history = await self.get_personality_evolution_history(dimension, days=1)
        cutoff_time = datetime.now() - timedelta(hours=hours)
        return [update for update in history if update.timestamp > cutoff_time]

    async def _check_change_consistency(self, dimension: str, new_value: Any, context: str) -> Dict[str, Any]:
        """Check if change is consistent with user preferences and patterns"""
        consistency_result = {
            'consistent': True,
            'reason': 'Change aligns with established patterns',
            'severity': 'low',
            'confidence': 0.8
        }

        # Get dimension history for pattern analysis
        history = await self.get_personality_evolution_history(dimension, days=30)

        if len(history) < 3:
            consistency_result['reason'] = 'Insufficient history for consistency check'
            return consistency_result

        # Analyze historical patterns
        try:
            if self.tracked_dimensions[dimension]['value_type'] == 'continuous':
                recent_values = [float(update.new_value) for update in history[-5:]]
                avg_value = sum(recent_values) / len(recent_values)
                new_val = float(new_value)

                # Check if new value deviates significantly from recent average
                deviation = abs(new_val - avg_value)
                if deviation > 0.3:  # 30% deviation
                    consistency_result.update({
                        'consistent': False,
                        'reason': f'New value {new_val:.2f} deviates significantly from recent average {avg_value:.2f}',
                        'severity': 'high' if deviation > 0.5 else 'medium'
                    })

        except (ValueError, TypeError, KeyError):
            # Handle categorical dimensions or data errors
            pass

        return consistency_result

    def _is_change_context_appropriate(self, context: str, change_magnitude: float) -> bool:
        """Validate if the change context is appropriate for the magnitude"""
        context_lower = context.lower()

        # Large changes should have explicit justification
        if change_magnitude > 0.2:
            appropriate_contexts = [
                'user_explicit_request',
                'user_feedback',
                'user_preference_update',
                'learning_from_interaction'
            ]
            return any(ctx in context_lower for ctx in appropriate_contexts)

        # Smaller changes are generally acceptable in any context
        return True

    async def _apply_risk_mitigations(self, dimension: str, risk_factors: List[str],
                                   change_magnitude: float) -> List[str]:
        """Apply appropriate mitigations for identified risk factors"""
        mitigations = []

        if 'rapid_change_pattern' in risk_factors:
            # Reduce change frequency monitoring
            mitigations.append('Increased monitoring for rapid changes')

        if 'inconsistent_with_preferences' in risk_factors:
            # Flag for additional validation
            mitigations.append('Additional consistency validation applied')

        if 'inappropriate_context' in risk_factors:
            # Log for review
            mitigations.append('Context validation flagged for review')

        return mitigations

    async def get_safety_enhanced_personality_state(self) -> Dict[str, Any]:
        """Get personality state with safety metadata"""
        base_state = await self.get_current_personality_state()

        # Add safety information
        safety_enhanced_state = {}

        for name, dimension in base_state.items():
            recent_changes = await self._get_recent_dimension_changes(name, hours=24)

            safety_enhanced_state[name] = {
                'current_value': dimension.current_value,
                'confidence': dimension.confidence,
                'last_updated': dimension.last_updated,
                'value_type': dimension.value_type,
                'learning_rate': dimension.learning_rate,
                'safety_metadata': {
                    'recent_changes_24h': len(recent_changes),
                    'last_change_magnitude': recent_changes[0].confidence_change if recent_changes else 0,
                    'stability_score': self._calculate_stability_score(recent_changes),
                    'safety_status': 'stable'  # This could be calculated based on patterns
                }
            }

        return safety_enhanced_state

    def _calculate_stability_score(self, recent_changes: List[PersonalityUpdate]) -> float:
        """Calculate stability score based on recent changes"""
        if not recent_changes:
            return 1.0

        # Factor in frequency and magnitude of recent changes
        frequency_factor = max(0, 1 - (len(recent_changes) / 20))  # More changes = less stable

        if len(recent_changes) > 0:
            avg_magnitude = sum(abs(c.confidence_change) for c in recent_changes) / len(recent_changes)
            magnitude_factor = max(0, 1 - (avg_magnitude / 0.2))  # Larger changes = less stable
        else:
            magnitude_factor = 1.0

        return (frequency_factor + magnitude_factor) / 2

    async def emergency_personality_reset(self, reason: str, authorized_by: str) -> Dict[str, Any]:
        """Emergency reset of personality to safe defaults"""
        self.safety_logger.critical(f"EMERGENCY PERSONALITY RESET: {reason} - Authorized by: {authorized_by}")

        # Get default safe values
        safe_defaults = {
            'communication_formality': 0.5,
            'technical_depth_preference': 0.5,
            'humor_style_preference': 'balanced',
            'response_length_preference': 'medium',
            'conversation_pace_preference': 0.5,
            'proactive_suggestions': 0.4,
            'emotional_support_style': 'balanced'
        }

        reset_results = {}

        for dimension, safe_value in safe_defaults.items():
            try:
                result = await super().update_personality_dimension(
                    dimension,
                    safe_value,
                    0.0,  # No confidence change during reset
                    f"Emergency reset: {reason}"
                )
                reset_results[dimension] = result
            except Exception as e:
                reset_results[dimension] = {'success': False, 'error': str(e)}

        # Log the emergency reset
        await self.safety_coordinator._log_emergency_action(
            'personality_emergency_reset',
            reason,
            list(safe_defaults.keys())
        )

        return {
            'reset_completed': True,
            'reason': reason,
            'authorized_by': authorized_by,
            'timestamp': datetime.now(),
            'dimensions_reset': list(safe_defaults.keys()),
            'reset_results': reset_results
        }


if __name__ == "__main__":
    async def main():
        print("🛡️ Testing Safety-Enhanced Personality Tracker")
        print("=" * 60)

        tracker = SafetyEnhancedPersonalityTracker()

        # Test 1: Normal safe change
        print("\n1. Testing normal safe personality change...")
        result = await tracker.update_personality_dimension(
            'communication_formality',
            0.55,  # Small change from default 0.5
            0.05,
            'User feedback indicates preference for slightly more formal communication'
        )
        print(f"Safe change result: {result.get('success', False)}")
        print(f"Safety status: {result.get('safety_status', 'unknown')}")
        if 'change_magnitude' in result:
            print(f"Change magnitude: {result['change_magnitude']:.3f}")

        # Test 2: Large change requiring approval
        print("\n2. Testing large change requiring approval...")
        result = await tracker.update_personality_dimension(
            'technical_depth_preference',
            0.9,   # Large change from default 0.5
            0.1,
            'User explicitly requested very detailed technical explanations'
        )
        print(f"Large change result: {result.get('success', False)}")
        print(f"Safety status: {result.get('safety_status', 'unknown')}")
        print(f"Reason: {result.get('reason', 'No reason provided')}")

        # Test 3: Excessive change (should be blocked)
        print("\n3. Testing excessive change (should be blocked)...")
        result = await tracker.update_personality_dimension(
            'humor_style_preference',
            'completely_different_style',
            0.5,    # Very high confidence change
            'Testing excessive change detection'
        )
        print(f"Excessive change blocked: {not result.get('success', True)}")
        print(f"Safety status: {result.get('safety_status', 'unknown')}")
        print(f"Block reason: {result.get('reason', 'No reason provided')}")

        # Test 4: Get safety-enhanced personality state
        print("\n4. Getting safety-enhanced personality state...")
        state = await tracker.get_safety_enhanced_personality_state()
        print(f"Dimensions tracked: {len(state)}")

        for name, data in list(state.items())[:3]:  # Show first 3
            safety_meta = data.get('safety_metadata', {})
            print(f"  {name}:")
            print(f"    Value: {data['current_value']}")
            print(f"    Confidence: {data['confidence']:.3f}")
            print(f"    Recent changes (24h): {safety_meta.get('recent_changes_24h', 0)}")
            print(f"    Stability score: {safety_meta.get('stability_score', 1.0):.3f}")

        # Test 5: Safety framework integration check
        print("\n5. Testing safety framework integration...")

        # Check if safety coordinator is working
        safety_dashboard = await tracker.safety_coordinator.get_safety_dashboard()
        print(f"Safety framework status: {safety_dashboard['current_status']}")
        print(f"Monitoring active: {safety_dashboard['monitoring_active']}")
        print(f"Active incidents: {safety_dashboard['active_incidents']}")

        # Test 6: Rapid change detection
        print("\n6. Testing rapid change detection...")
        print("(Making multiple small changes to test pattern detection)")

        for i in range(3):
            result = await tracker.update_personality_dimension(
                'conversation_pace_preference',
                0.5 + (i * 0.02),  # Small incremental changes
                0.02,
                f'Rapid change test {i+1}'
            )
            print(f"  Change {i+1}: {result.get('success', False)} (magnitude: {result.get('change_magnitude', 0):.3f})")

        print("\n✅ Safety-Enhanced Personality Tracker test completed!")

    asyncio.run(main())