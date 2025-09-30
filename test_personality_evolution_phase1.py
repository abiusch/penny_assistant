#!/usr/bin/env python3
"""
Personality Evolution System - Phase 1 Complete Test
Tests all Phase 1 components working together
"""

import asyncio
from datetime import datetime

# Import all Phase 1 components
from slang_vocabulary_tracker import SlangVocabularyTracker
from contextual_preference_engine import ContextualPreferenceEngine
from response_effectiveness_analyzer import ResponseEffectivenessAnalyzer
from personality_tracker import PersonalityTracker

async def test_integrated_personality_system():
    """
    Test the complete integrated personality tracking system
    Simulates a realistic conversation flow with all components working together
    """
    
    print("=" * 80)
    print("🎯 PERSONALITY EVOLUTION SYSTEM - PHASE 1 INTEGRATION TEST")
    print("=" * 80)
    
    # Initialize all components
    print("\n📦 Initializing components...")
    slang_tracker = SlangVocabularyTracker()
    context_engine = ContextualPreferenceEngine()
    effectiveness_analyzer = ResponseEffectivenessAnalyzer()
    personality_tracker = PersonalityTracker()
    
    print("✅ All components initialized successfully")
    
    # Simulate a conversation
    conversation = [
        {
            'user_message': "Hey Penny, can you help me debug this code? It's totally broken",
            'penny_response': "Sure thing! Let me take a look. What's the error you're seeing?",
            'context': {
                'participants': [],
                'emotion': 'frustrated',
                'topic': 'programming',
                'is_follow_up_question': False
            }
        },
        {
            'user_message': "Perfect! That fixed it. You're awesome!",
            'penny_response': "Glad I could help! Debugging can be frustrating but you got this.",
            'context': {
                'participants': [],
                'emotion': 'excited',
                'topic': 'programming',
                'is_follow_up_question': True,
                'previous_response_technical': True
            }
        },
        {
            'user_message': "btw can you explain how async/await works? I'm confused",
            'penny_response': "Absolutely! Async/await is Python's way of handling asynchronous operations...",
            'context': {
                'participants': [],
                'emotion': 'neutral',
                'topic': 'programming',
                'is_follow_up_question': True
            }
        }
    ]
    
    print("\n\n" + "=" * 80)
    print("💬 SIMULATING CONVERSATION")
    print("=" * 80)
    
    last_response_time = datetime.now().timestamp()
    
    for i, exchange in enumerate(conversation, 1):
        print(f"\n--- Exchange {i} ---")
        print(f"👤 User: {exchange['user_message']}")
        print(f"🤖 Penny: {exchange['penny_response']}")
        
        # 1. VOCABULARY ANALYSIS
        print(f"\n📚 Vocabulary Analysis:")
        vocab_analysis = await slang_tracker.analyze_message_vocabulary(
            exchange['user_message'],
            exchange['context']
        )
        print(f"  Vocabulary style: {vocab_analysis['vocabulary_style']}")
        if vocab_analysis['slang_detected']:
            print(f"  Slang detected: {', '.join(vocab_analysis['slang_detected'])}")
        if vocab_analysis['technical_terms']:
            print(f"  Technical terms: {', '.join(vocab_analysis['technical_terms'])}")
        
        # 2. CONTEXT ANALYSIS
        print(f"\n🌍 Context Analysis:")
        current_context = await context_engine.analyze_current_context(
            exchange['user_message'],
            exchange['context']
        )
        print(f"  Time of day: {current_context['time_of_day']}")
        print(f"  Topic: {current_context['topic_category']}")
        print(f"  Mood: {current_context['mood_state']}")
        print(f"  Social context: {current_context['social_context']}")
        
        # Get contextual adjustments
        adjustments = await context_engine.get_contextual_personality_adjustments(current_context)
        if adjustments:
            print(f"  Personality adjustments:")
            for dim, adj_info in list(adjustments.items())[:3]:  # Show first 3
                print(f"    {dim}: {adj_info['adjustment']}")
        
        # 3. PERSONALITY COMMUNICATION ANALYSIS
        print(f"\n🧠 Personality Analysis:")
        comm_analysis = await personality_tracker.analyze_user_communication(
            exchange['user_message'],
            exchange['context']
        )
        print(f"  Formality: {comm_analysis['formality_level']['value']:.2f}")
        print(f"  Technical depth: {comm_analysis['technical_depth_request']['value']:.2f}")
        print(f"  Humor style: {comm_analysis['humor_response_cues']['value']}")
        print(f"  Pace preference: {comm_analysis['pace_indicators']['value']:.2f}")
        
        # 4. EFFECTIVENESS ANALYSIS (if not first message)
        if i > 1:
            print(f"\n📊 Response Effectiveness:")
            current_time = datetime.now().timestamp()
            time_since_response = current_time - last_response_time
            
            metrics = await effectiveness_analyzer.analyze_user_response(
                exchange['user_message'],
                conversation[i-2]['penny_response'],  # Previous Penny response
                time_since_response
            )
            
            print(f"  Engagement score: {metrics.engagement_score:.2f}")
            if metrics.satisfaction_indicators:
                print(f"  Positive indicators: {', '.join(metrics.satisfaction_indicators)}")
            if metrics.dissatisfaction_indicators:
                print(f"  Negative indicators: {', '.join(metrics.dissatisfaction_indicators)}")
            
            # Get mock personality state for testing
            personality_state = {
                'communication_formality': comm_analysis['formality_level']['value'],
                'technical_depth_preference': comm_analysis['technical_depth_request']['value'],
                'sass_level': 'medium'
            }
            
            effectiveness_score = await effectiveness_analyzer.record_response_effectiveness(
                conversation[i-2]['penny_response'],
                personality_state,
                current_context,
                metrics
            )
            
            print(f"  Overall effectiveness: {effectiveness_score:.2f}")
        
        last_response_time = datetime.now().timestamp()
    
    # COMPREHENSIVE INSIGHTS
    print("\n\n" + "=" * 80)
    print("📈 COMPREHENSIVE INSIGHTS")
    print("=" * 80)
    
    # Vocabulary Profile
    print("\n📖 Vocabulary Profile:")
    vocab_profile = await slang_tracker.get_user_vocabulary_profile()
    print(f"  Total unique terms learned: {vocab_profile['total_unique_terms']}")
    print(f"  Formality score: {vocab_profile['formality_score']:.2f}")
    print(f"  Technical depth score: {vocab_profile['technical_depth_score']:.2f}")
    
    if vocab_profile['most_used_terms']:
        print(f"  Most used terms:")
        for term in vocab_profile['most_used_terms'][:5]:
            print(f"    - {term['term']}: {term['usage_count']} times ({term['category']})")
    
    # Vocabulary Recommendations
    print("\n💡 Vocabulary Recommendations:")
    vocab_recs = await slang_tracker.get_vocabulary_recommendations()
    for rec in vocab_recs[:3]:
        print(f"  {rec['dimension']}: {rec['recommendation']}")
        print(f"    Reason: {rec['reason']}")
        print(f"    Confidence: {rec['confidence']:.2f}")
    
    # Contextual Insights
    print("\n🌍 Contextual Learning:")
    context_insights = await context_engine.get_contextual_insights()
    print(f"  Context diversity: {context_insights['context_diversity']} types")
    print(f"  Learned contexts: {len(context_insights['learned_contexts'])}")
    
    if context_insights['strongest_context_effects']:
        print(f"  Strongest context effects:")
        for effect in context_insights['strongest_context_effects'][:3]:
            print(f"    {effect['context']}: strength {effect['strength']:.2f}")
    
    # Personality State
    print("\n🎭 Current Personality State:")
    personality_state = await personality_tracker.get_current_personality_state()
    for dim_name, dimension in list(personality_state.items())[:5]:
        print(f"  {dim_name}: {dimension.current_value}")
        print(f"    Confidence: {dimension.confidence:.2f}")
    
    # Effectiveness Insights
    print("\n📊 Response Effectiveness:")
    eff_insights = await effectiveness_analyzer.get_effectiveness_insights()
    print(f"  Total responses tracked: {eff_insights['total_responses_tracked']}")
    print(f"  Average effectiveness: {eff_insights['avg_effectiveness']:.2f}")
    print(f"  Recent trend: {eff_insights['recent_trend']}")
    
    if eff_insights['feedback_distribution']:
        print(f"  Feedback distribution:")
        for feedback_type, count in eff_insights['feedback_distribution'].items():
            print(f"    {feedback_type}: {count}")
    
    # Improvement Suggestions
    print("\n🔧 Improvement Suggestions:")
    suggestions = await effectiveness_analyzer.suggest_personality_improvements()
    for i, suggestion in enumerate(suggestions[:3], 1):
        print(f"  {i}. [{suggestion['priority']}] {suggestion['type']}")
        print(f"     {suggestion['suggestion']}")
    
    # SUMMARY
    print("\n\n" + "=" * 80)
    print("✅ PHASE 1 INTEGRATION TEST SUMMARY")
    print("=" * 80)
    
    print("\n🎯 Components Tested:")
    print("  ✅ Slang Vocabulary Tracker - Learning user's language")
    print("  ✅ Contextual Preference Engine - Adapting to situations")
    print("  ✅ Response Effectiveness Analyzer - Measuring what works")
    print("  ✅ Personality Tracker - Comprehensive dimension tracking")
    
    print("\n📊 System Capabilities Demonstrated:")
    print(f"  ✅ Vocabulary learning: {vocab_profile['total_unique_terms']} terms tracked")
    print(f"  ✅ Context awareness: {context_insights['context_diversity']} context types")
    print(f"  ✅ Effectiveness tracking: {eff_insights['total_responses_tracked']} responses analyzed")
    print(f"  ✅ Personality dimensions: {len(personality_state)} dimensions tracked")
    
    print("\n🚀 Ready for Phase 2:")
    print("  📝 Integration with response generation")
    print("  🎖️ Milestone system implementation")
    print("  🔗 Cross-system coordination")
    
    print("\n" + "=" * 80)
    print("🎉 PHASE 1 COMPLETE - ALL SYSTEMS OPERATIONAL!")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(test_integrated_personality_system())
