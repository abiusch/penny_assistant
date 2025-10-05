#!/usr/bin/env python3
"""
Quick Check: What Has Penny Learned About You?
Run this anytime to see Penny's current understanding of your communication style
"""

import asyncio
from slang_vocabulary_tracker import SlangVocabularyTracker
from contextual_preference_engine import ContextualPreferenceEngine
from response_effectiveness_analyzer import ResponseEffectivenessAnalyzer
from personality_tracker import PersonalityTracker

async def quick_check():
    """Show current personality learning state in human-readable format"""
    
    print("\n" + "="*70)
    print("🧠 WHAT PENNY KNOWS ABOUT YOU")
    print("="*70 + "\n")
    
    try:
        # Initialize trackers
        slang_tracker = SlangVocabularyTracker()
        context_engine = ContextualPreferenceEngine()
        effectiveness_analyzer = ResponseEffectivenessAnalyzer()
        personality_tracker = PersonalityTracker()
        
        # Get vocabulary profile
        vocab_profile = await slang_tracker.get_user_vocabulary_profile()
        
        print("📖 YOUR COMMUNICATION STYLE")
        print("-" * 70)
        
        formality_desc = "very casual" if vocab_profile['formality_score'] < 0.3 else \
                        "casual" if vocab_profile['formality_score'] < 0.5 else \
                        "balanced" if vocab_profile['formality_score'] < 0.7 else \
                        "formal"
        
        tech_desc = "beginner-friendly" if vocab_profile['technical_depth_score'] < 0.3 else \
                   "somewhat technical" if vocab_profile['technical_depth_score'] < 0.6 else \
                   "highly technical"
        
        print(f"📊 Formality Level: {vocab_profile['formality_score']:.2f}/1.0 ({formality_desc})")
        print(f"🔧 Technical Depth: {vocab_profile['technical_depth_score']:.2f}/1.0 ({tech_desc})")
        print(f"📚 Unique Terms Learned: {vocab_profile['total_unique_terms']}")
        
        if vocab_profile['most_used_terms']:
            print(f"\n🔥 Your Most Used Terms:")
            for i, term in enumerate(vocab_profile['most_used_terms'][:8], 1):
                category_emoji = {
                    'slang': '😎',
                    'technical': '💻',
                    'casual': '🗣️',
                    'formal': '📝'
                }.get(term['category'], '💬')
                print(f"   {i}. {category_emoji} '{term['term']}' - used {term['usage_count']}x")
        
        # Get personality dimensions
        personality_state = await personality_tracker.get_current_personality_state()
        
        print(f"\n🎭 PERSONALITY PREFERENCES")
        print("-" * 70)
        
        # Show key dimensions
        key_dims = [
            'communication_formality',
            'technical_depth_preference',
            'response_length_preference',
            'conversation_pace_preference'
        ]
        
        for dim_name in key_dims:
            if dim_name in personality_state:
                dim = personality_state[dim_name]
                confidence_bar = "█" * int(dim.confidence * 10) + "░" * (10 - int(dim.confidence * 10))
                
                if dim.value_type == 'continuous':
                    value_str = f"{float(dim.current_value):.2f}"
                else:
                    value_str = str(dim.current_value)
                
                print(f"   {dim_name}: {value_str}")
                print(f"      Confidence: [{confidence_bar}] {dim.confidence:.0%}")
        
        # Context insights
        context_insights = await context_engine.get_contextual_insights()
        
        print(f"\n🌍 CONTEXT PATTERNS")
        print("-" * 70)
        print(f"   Contexts learned: {len(context_insights['learned_contexts'])}")
        print(f"   Context variety: {context_insights['context_diversity']} types")
        
        if context_insights['strongest_context_effects']:
            print(f"\n   Strongest patterns:")
            for effect in context_insights['strongest_context_effects'][:3]:
                print(f"      • {effect['context']}")
                print(f"        Strength: {effect['strength']:.2f}")
        
        # Effectiveness data
        eff_insights = await effectiveness_analyzer.get_effectiveness_insights()
        
        print(f"\n📊 CONVERSATION METRICS")
        print("-" * 70)
        print(f"   Total messages tracked: {eff_insights['total_responses_tracked']}")
        
        if eff_insights['total_responses_tracked'] > 0:
            avg_eff = eff_insights['avg_effectiveness']
            eff_desc = "excellent" if avg_eff > 0.8 else \
                      "good" if avg_eff > 0.6 else \
                      "okay" if avg_eff > 0.4 else \
                      "needs work"
            
            print(f"   Average engagement: {avg_eff:.2f}/1.0 ({eff_desc})")
            print(f"   Trend: {eff_insights['recent_trend']}")
            
            if eff_insights['feedback_distribution']:
                print(f"\n   Feedback breakdown:")
                for feedback_type, count in eff_insights['feedback_distribution'].items():
                    emoji = {
                        'positive': '👍',
                        'praised': '🌟',
                        'follow_up': '💬',
                        'neutral': '😐',
                        'negative': '👎',
                        'corrected': '✏️',
                        'ignored': '😶'
                    }.get(feedback_type, '•')
                    print(f"      {emoji} {feedback_type}: {count}")
        
        # Recommendations
        vocab_recs = await slang_tracker.get_vocabulary_recommendations()
        improvements = await effectiveness_analyzer.suggest_personality_improvements()
        
        if vocab_recs or improvements:
            print(f"\n💡 RECOMMENDATIONS FOR PENNY")
            print("-" * 70)
            
            if vocab_recs:
                for rec in vocab_recs[:3]:
                    action_emoji = "📈" if rec['recommendation'] == 'increase' else "📉" if rec['recommendation'] == 'decrease' else "🎯"
                    print(f"   {action_emoji} {rec['dimension']}: {rec['recommendation']}")
                    print(f"      Why: {rec['reason'][:80]}")
            
            if improvements:
                for imp in improvements[:2]:
                    priority_emoji = "🔴" if imp['priority'] == 'high' else "🟡" if imp['priority'] == 'medium' else "🟢"
                    print(f"   {priority_emoji} [{imp['priority']}] {imp['type']}")
                    print(f"      {imp['suggestion'][:80]}")
        
        print(f"\n" + "="*70)
        
        # Summary
        if vocab_profile['total_unique_terms'] < 10:
            print("📊 STATUS: Just getting started - need more conversations!")
            print("   Have 5-10 more chats to build a solid profile.")
        elif vocab_profile['total_unique_terms'] < 30:
            print("📊 STATUS: Building your profile - good progress!")
            print("   Pattern recognition is improving. Keep chatting!")
        else:
            print("📊 STATUS: Profile well-established!")
            print("   Penny has a solid understanding of your style.")
            if eff_insights['avg_effectiveness'] > 0.6:
                print("   ✨ Ready for Phase 2 - make Penny use this knowledge!")
        
        print("="*70 + "\n")
        
    except FileNotFoundError:
        print("❌ No learning data found yet!")
        print("   Start using personality_observer.py to collect data.")
        print("="*70 + "\n")
    except Exception as e:
        print(f"❌ Error reading profile: {e}")
        print("="*70 + "\n")

if __name__ == "__main__":
    asyncio.run(quick_check())
