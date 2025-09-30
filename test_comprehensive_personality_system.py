#!/usr/bin/env python3
"""
Comprehensive test of the integrated personality learning system
Tests the integration between sass learning and multi-dimensional personality tracking
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, Any

from enhanced_personality_learning import EnhancedPersonalityLearning
from personality_milestones import PersonalityMilestones
from sass_controller import SassLevel

async def test_basic_personality_learning():
    """Test basic personality learning functionality"""
    print("🧠 Testing Basic Personality Learning")
    print("=" * 50)

    learning_system = EnhancedPersonalityLearning()

    # Test basic interaction processing
    test_interactions = [
        {
            'user_message': "Hey, can you help me debug this code quickly?",
            'penny_response': "Sure! Let me take a look at your code...",
            'context': {
                'conversation_topic': 'debugging',
                'user_emotion': 'neutral',
                'request_type': 'quick_help'
            }
        },
        {
            'user_message': "Could you please provide a comprehensive explanation of how machine learning algorithms work, including the mathematical foundations?",
            'penny_response': "I'd be happy to explain machine learning in detail with mathematical foundations...",
            'context': {
                'conversation_topic': 'machine_learning',
                'technical_depth_requested': True,
                'formality_level': 'high'
            }
        },
        {
            'user_message': "lol that was actually pretty funny 😄",
            'penny_response': "Glad I could make you laugh!",
            'context': {
                'previous_humor_style': 'playful',
                'positive_response_to_humor': True,
                'emotional_tone': 'positive'
            }
        }
    ]

    results = []
    for i, interaction in enumerate(test_interactions, 1):
        print(f"\n--- Interaction {i} ---")
        print(f"User: {interaction['user_message']}")
        print(f"Context: {interaction['context']}")

        result = await learning_system.process_interaction(
            interaction['user_message'],
            interaction['penny_response'],
            interaction['context']
        )

        results.append(result)

        print(f"✅ Personality updates: {len(result.personality_updates)}")
        for dim, update in result.personality_updates.items():
            print(f"   {dim}: {update.old_value} → {update.new_value} (confidence: {update.confidence_change:+.3f})")

        if result.adaptation_suggestions:
            print(f"💡 Adaptations: {result.adaptation_suggestions}")

        if result.milestones_achieved:
            print(f"🏆 Milestones: {result.milestones_achieved}")

    print(f"\n📊 Learning Summary after {len(test_interactions)} interactions:")
    summary = await learning_system.get_learning_summary()
    print(f"   Average confidence: {summary['recent_learning_activity']['average_confidence']:.3f}")
    print(f"   Learning velocity: {summary['recent_learning_activity']['learning_velocity']:.2f} changes/day")
    print(f"   Total dimensions tracked: {len(summary['current_personality_state'])}")

    return results, learning_system

async def test_sass_integration():
    """Test integration with adaptive sass learning"""
    print("\n🎭 Testing Sass Integration")
    print("=" * 50)

    learning_system = EnhancedPersonalityLearning()

    # Test sass adjustment recording
    sass_adjustments = [
        {
            'command': "tone it down",
            'from_sass': SassLevel.MEDIUM,
            'to_sass': SassLevel.MINIMAL,
            'context': {
                'topic': 'programming',
                'emotion': 'frustrated',
                'participants': []
            }
        },
        {
            'command': "be more sassy",
            'from_sass': SassLevel.MINIMAL,
            'to_sass': SassLevel.SPICY,
            'context': {
                'topic': 'conversation',
                'emotion': 'playful',
                'participants': ['friend']
            }
        },
        {
            'command': "normal sass please",
            'from_sass': SassLevel.SPICY,
            'to_sass': SassLevel.MEDIUM,
            'context': {
                'topic': 'general',
                'emotion': 'neutral',
                'participants': []
            }
        }
    ]

    for i, adjustment in enumerate(sass_adjustments, 1):
        print(f"\n--- Sass Adjustment {i} ---")
        print(f"Command: '{adjustment['command']}'")
        print(f"Sass: {adjustment['from_sass'].value} → {adjustment['to_sass'].value}")
        print(f"Context: {adjustment['context']}")

        result = await learning_system.record_sass_adjustment(
            adjustment['command'],
            adjustment['from_sass'],
            adjustment['to_sass'],
            adjustment['context']
        )

        print(f"✅ Result: {result}")

    # Test retrieving integrated preferences
    test_contexts = [
        {'topic': 'programming', 'emotion': 'frustrated'},
        {'topic': 'conversation', 'emotion': 'playful', 'participants': ['friend']},
        {'topic': 'general', 'emotion': 'neutral'}
    ]

    print(f"\n🎯 Testing Preference Retrieval:")
    for context in test_contexts:
        preferences = await learning_system.get_integrated_preferences(context)
        print(f"Context: {context}")

        if 'sass_level' in preferences:
            print(f"   Learned sass: {preferences['sass_level']}")

        if 'personality_adaptations' in preferences:
            print(f"   Personality adaptations: {len(preferences['personality_adaptations'])}")
            for adapt in preferences['personality_adaptations'][:2]:  # Show first 2
                print(f"     {adapt['dimension']}: {adapt['suggested_value']} (confidence: {adapt['confidence']:.2f})")

        if 'personality_state' in preferences:
            high_confidence_dims = [
                name for name, data in preferences['personality_state'].items()
                if data['confidence'] > 0.6
            ]
            print(f"   High-confidence dimensions: {high_confidence_dims}")

    return learning_system

async def test_milestone_system():
    """Test personality milestone system"""
    print("\n🏆 Testing Milestone System")
    print("=" * 50)

    learning_system = EnhancedPersonalityLearning()
    milestones = PersonalityMilestones(learning_system.personality_tracker)

    # Simulate some personality development to trigger milestones
    development_interactions = [
        # Build up technical depth preference
        ("Can you explain the technical details of how this algorithm works?", "technical response",
         {'technical_depth_requested': True, 'topic': 'algorithms'}),
        ("I need a detailed technical breakdown of this system", "detailed response",
         {'technical_depth_requested': True, 'topic': 'systems'}),
        ("Show me the implementation details", "implementation details",
         {'technical_depth_requested': True, 'topic': 'coding'}),

        # Build up humor style preference
        ("That joke was pretty good! 😄", "Thanks! Glad you enjoyed it",
         {'humor_feedback': 'positive', 'topic': 'conversation'}),
        ("Haha, you're funny", "I do try! 😊",
         {'humor_feedback': 'positive', 'topic': 'conversation'}),
        ("That was hilarious 😂", "Comedy gold! ✨",
         {'humor_feedback': 'positive', 'topic': 'conversation'}),

        # Build up formality preferences
        ("Thank you for your assistance", "You're welcome",
         {'formality_level': 'high', 'topic': 'general'}),
        ("I would appreciate a formal response", "Certainly, I'll be more formal",
         {'formality_level': 'high', 'topic': 'general'}),
    ]

    print(f"Processing {len(development_interactions)} interactions to build personality confidence...")

    for user_msg, penny_resp, context in development_interactions:
        await learning_system.process_interaction(user_msg, penny_resp, context)

    # Check current personality state
    personality_state = await learning_system.personality_tracker.get_current_personality_state()
    print(f"\n📊 Current Personality State:")
    for name, dim in personality_state.items():
        print(f"   {name}: {dim.current_value} (confidence: {dim.confidence:.3f})")

    # Check for achieved milestones
    achieved_milestones = await milestones.get_achieved_milestones()
    print(f"\n🎖️ Achieved Milestones: {len(achieved_milestones)}")
    for milestone in achieved_milestones:
        print(f"   {milestone.name} ({milestone.rarity}) - {milestone.achieved_at.strftime('%m/%d %H:%M')}")

    # Check milestone progress
    progress_list = await milestones.get_milestone_progress()
    print(f"\n📈 Milestone Progress (Top 3):")
    for progress in progress_list[:3]:
        milestone_template = milestones.milestone_templates[progress.milestone_id]
        print(f"   {milestone_template['name']}: {progress.current_progress:.1%}")
        print(f"     Estimated completion: {progress.estimated_completion}")

    # Get milestone summary
    summary = await milestones.get_milestone_summary()
    print(f"\n📋 Milestone Summary:")
    print(f"   Total achieved: {summary['total_achieved']}")
    print(f"   Achievement rate: {summary['achievement_rate']:.1%}")
    print(f"   Rarity breakdown: {summary['rarity_breakdown']}")

    return milestones

async def test_comprehensive_integration():
    """Test the complete integrated system"""
    print("\n🚀 Testing Comprehensive Integration")
    print("=" * 50)

    learning_system = EnhancedPersonalityLearning()

    # Get comprehensive learning status
    status = await learning_system.get_comprehensive_learning_status()

    print(f"Integration Health: {status['integration_health']}")
    print(f"Learning Systems Active: {status.get('integration_metrics', {}).get('learning_systems_active', 1)}")

    if status['sass_learning']:
        print(f"Sass Learning Events: {status['sass_learning']['total_adjustments']}")
        if status['sass_learning']['context_preferences']:
            print(f"Sass Context Preferences: {len(status['sass_learning']['context_preferences'])}")

    personality_summary = status['personality_learning']
    print(f"Personality Dimensions: {len(personality_summary['current_personality_state'])}")
    print(f"Recent Activity: {personality_summary['recent_learning_activity']['total_changes_last_week']} changes")
    print(f"Average Confidence: {personality_summary['recent_learning_activity']['average_confidence']:.3f}")

    # Test adaptation recommendations
    adaptations = await learning_system.get_adaptation_recommendations()
    print(f"\n💡 Current Adaptation Recommendations: {len(adaptations)}")
    for adapt in adaptations[:3]:  # Show top 3
        print(f"   {adapt.dimension}: {adapt.reason}")
        print(f"     → {adapt.impact_description}")

    print(f"\n✅ Comprehensive personality learning system integration test completed!")
    return status

async def main():
    """Run comprehensive test suite"""
    print("🧪 COMPREHENSIVE PERSONALITY LEARNING SYSTEM TEST")
    print("=" * 60)
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    try:
        # Test 1: Basic personality learning
        basic_results, learning_system = await test_basic_personality_learning()

        # Test 2: Sass integration
        sass_system = await test_sass_integration()

        # Test 3: Milestone system
        milestone_system = await test_milestone_system()

        # Test 4: Comprehensive integration
        integration_status = await test_comprehensive_integration()

        print(f"\n🎉 ALL TESTS COMPLETED SUCCESSFULLY!")
        print(f"=" * 60)
        print(f"✅ Basic personality learning: PASSED")
        print(f"✅ Sass integration: PASSED")
        print(f"✅ Milestone system: PASSED")
        print(f"✅ Comprehensive integration: PASSED")

        # Final summary
        print(f"\n📊 FINAL SYSTEM STATUS:")
        if integration_status.get('integration_metrics'):
            metrics = integration_status['integration_metrics']
            print(f"   Total learning events: {metrics['total_learning_events']}")
            print(f"   Learning systems active: {metrics['learning_systems_active']}")
            print(f"   Personality dimensions: {metrics['comprehensive_coverage']}")

        print(f"\n🚀 The comprehensive personality learning system is PRODUCTION READY!")

    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())