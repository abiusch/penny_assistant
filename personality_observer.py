#!/usr/bin/env python3
"""
Penny with Personality Tracking - Silent Observation Mode
Adds Phase 1 tracking to real Penny conversations without changing behavior
Just logs what Penny learns about your communication style
"""

import asyncio
import sys
from datetime import datetime
from typing import Dict, Any

# Import personality tracking components
from slang_vocabulary_tracker import SlangVocabularyTracker
from contextual_preference_engine import ContextualPreferenceEngine
from response_effectiveness_analyzer import ResponseEffectivenessAnalyzer
from personality_tracker import PersonalityTracker

class PersonalityObserver:
    """
    Silent observer that tracks personality without affecting responses
    Wraps around existing Penny to learn communication patterns
    """
    
    def __init__(self):
        print("🧠 Initializing Personality Observer (Silent Mode)...")
        self.slang_tracker = SlangVocabularyTracker()
        self.context_engine = ContextualPreferenceEngine()
        self.effectiveness_analyzer = ResponseEffectivenessAnalyzer()
        self.personality_tracker = PersonalityTracker()
        
        self.last_penny_response = None
        self.last_response_time = None
        self.conversation_count = 0
        
        print("✅ Personality Observer ready - tracking enabled, behavior unchanged")
    
    async def observe_user_message(self, user_message: str, context: Dict[str, Any] = None):
        """
        Silently observe and learn from user message
        Returns insights without affecting Penny's response
        """
        self.conversation_count += 1
        
        if context is None:
            context = {}
        
        print(f"\n{'='*60}")
        print(f"📝 Message #{self.conversation_count}: Observing...")
        print(f"{'='*60}")
        
        insights = {}
        
        # 1. Vocabulary Analysis
        try:
            vocab_analysis = await self.slang_tracker.analyze_message_vocabulary(
                user_message, context
            )
            insights['vocabulary'] = {
                'style': vocab_analysis['vocabulary_style'],
                'slang': vocab_analysis['slang_detected'][:3],  # First 3
                'technical': vocab_analysis['technical_terms'][:3],
            }
            print(f"📚 Vocabulary: {vocab_analysis['vocabulary_style']}")
            if vocab_analysis['slang_detected']:
                print(f"   Slang: {', '.join(vocab_analysis['slang_detected'][:3])}")
        except Exception as e:
            print(f"⚠️ Vocabulary tracking error: {e}")
        
        # 2. Context Analysis
        try:
            current_context = await self.context_engine.analyze_current_context(
                user_message, context
            )
            insights['context'] = current_context
            print(f"🌍 Context: {current_context['time_of_day']} | {current_context['topic_category']} | {current_context['mood_state']}")
        except Exception as e:
            print(f"⚠️ Context tracking error: {e}")
        
        # 3. Personality Communication Analysis
        try:
            comm_analysis = await self.personality_tracker.analyze_user_communication(
                user_message, context
            )
            insights['personality'] = {
                'formality': comm_analysis['formality_level']['value'],
                'technical_depth': comm_analysis['technical_depth_request']['value'],
                'humor_style': comm_analysis['humor_response_cues']['value'],
            }
            print(f"🎭 Personality: Formality {comm_analysis['formality_level']['value']:.2f} | Tech {comm_analysis['technical_depth_request']['value']:.2f}")
        except Exception as e:
            print(f"⚠️ Personality tracking error: {e}")
        
        # 4. Effectiveness Analysis (if we have previous response)
        if self.last_penny_response and self.last_response_time:
            try:
                time_since = (datetime.now().timestamp() - self.last_response_time)
                metrics = await self.effectiveness_analyzer.analyze_user_response(
                    user_message,
                    self.last_penny_response,
                    time_since
                )
                
                insights['effectiveness'] = {
                    'engagement': metrics.engagement_score,
                    'satisfaction_signals': metrics.satisfaction_indicators,
                    'dissatisfaction_signals': metrics.dissatisfaction_indicators,
                }
                
                print(f"📊 Engagement: {metrics.engagement_score:.2f}", end="")
                if metrics.satisfaction_indicators:
                    print(f" | Positive: {', '.join(metrics.satisfaction_indicators[:2])}")
                else:
                    print()
            except Exception as e:
                print(f"⚠️ Effectiveness tracking error: {e}")
        
        print(f"{'='*60}\n")
        
        return insights
    
    async def record_penny_response(self, penny_response: str):
        """Record Penny's response for future effectiveness analysis"""
        self.last_penny_response = penny_response
        self.last_response_time = datetime.now().timestamp()
    
    async def get_learning_summary(self):
        """Get summary of what Penny has learned so far"""
        print("\n" + "="*60)
        print("🧠 LEARNING SUMMARY")
        print("="*60)
        
        try:
            # Vocabulary Profile
            vocab_profile = await self.slang_tracker.get_user_vocabulary_profile()
            print(f"\n📖 Vocabulary Profile:")
            print(f"   Unique terms learned: {vocab_profile['total_unique_terms']}")
            print(f"   Formality score: {vocab_profile['formality_score']:.2f} (0=casual, 1=formal)")
            print(f"   Technical depth: {vocab_profile['technical_depth_score']:.2f} (0=simple, 1=technical)")
            
            if vocab_profile['most_used_terms']:
                print(f"   Top terms:")
                for term in vocab_profile['most_used_terms'][:5]:
                    print(f"      • {term['term']}: {term['usage_count']}x ({term['category']})")
            
            # Personality State
            personality_state = await self.personality_tracker.get_current_personality_state()
            print(f"\n🎭 Personality Dimensions:")
            for dim_name, dimension in list(personality_state.items())[:5]:
                print(f"   • {dim_name}: {dimension.current_value} (confidence: {dimension.confidence:.2f})")
            
            # Context Insights
            context_insights = await self.context_engine.get_contextual_insights()
            print(f"\n🌍 Context Learning:")
            print(f"   Context types learned: {context_insights['context_diversity']}")
            print(f"   Total contexts: {len(context_insights['learned_contexts'])}")
            
            # Effectiveness Insights
            eff_insights = await self.effectiveness_analyzer.get_effectiveness_insights()
            print(f"\n📊 Response Effectiveness:")
            print(f"   Responses tracked: {eff_insights['total_responses_tracked']}")
            if eff_insights['total_responses_tracked'] > 0:
                print(f"   Average effectiveness: {eff_insights['avg_effectiveness']:.2f}")
                print(f"   Trend: {eff_insights['recent_trend']}")
            
            # Recommendations
            vocab_recs = await self.slang_tracker.get_vocabulary_recommendations()
            if vocab_recs:
                print(f"\n💡 Recommendations for Penny:")
                for rec in vocab_recs[:3]:
                    print(f"   • {rec['dimension']}: {rec['recommendation']}")
                    print(f"     Reason: {rec['reason']}")
            
            print(f"\n{'='*60}")
            print(f"✅ {self.conversation_count} messages observed and learned from!")
            print(f"{'='*60}\n")
            
        except Exception as e:
            print(f"⚠️ Error generating summary: {e}")


# Example usage - integrate this into your existing Penny
async def demo_with_observer():
    """
    Demo showing how to integrate observer with existing Penny
    """
    print("🎯 PENNY WITH PERSONALITY OBSERVER - DEMO")
    print("="*60)
    print("This shows personality tracking running alongside normal Penny")
    print("Penny's responses are unchanged - we're just learning silently")
    print("="*60 + "\n")
    
    observer = PersonalityObserver()
    
    # Simulate a conversation
    conversation = [
        "Hey Penny, can you help me debug this async function?",
        "Perfect! That totally worked. You're awesome!",
        "btw, can you explain how asyncio event loops work?",
        "Thanks! That makes sense now.",
    ]
    
    for i, user_message in enumerate(conversation, 1):
        print(f"\n👤 YOU: {user_message}")
        
        # Observe user message
        insights = await observer.observe_user_message(user_message, {
            'participants': [],
            'emotion': 'neutral'
        })
        
        # Simulate Penny's response (in real integration, this is actual Penny)
        if "debug" in user_message.lower():
            penny_response = "I'll help you debug that. What error are you seeing?"
        elif "awesome" in user_message.lower() or "perfect" in user_message.lower():
            penny_response = "Glad I could help! Let me know if you need anything else."
        elif "explain" in user_message.lower():
            penny_response = "The asyncio event loop is Python's way of managing asynchronous tasks. It schedules and executes coroutines, allowing concurrent operations without threads..."
        else:
            penny_response = "You're welcome! Feel free to ask if you have more questions."
        
        print(f"🤖 PENNY: {penny_response[:100]}{'...' if len(penny_response) > 100 else ''}")
        
        # Record Penny's response for effectiveness tracking
        await observer.record_penny_response(penny_response)
        
        # Small delay to simulate conversation timing
        await asyncio.sleep(0.5)
    
    # Show what was learned
    await observer.get_learning_summary()


# Integration instructions
def print_integration_instructions():
    """
    Show how to integrate with existing Penny code
    """
    print("\n" + "="*60)
    print("📋 INTEGRATION INSTRUCTIONS")
    print("="*60)
    
    print("""
To add personality tracking to your existing Penny:

1. Import at the top of your main Penny file:
   
   from personality_observer import PersonalityObserver
   
2. Initialize in Penny's __init__:
   
   self.personality_observer = PersonalityObserver()
   
3. In your message handling loop, add:
   
   # Before generating response
   insights = await self.personality_observer.observe_user_message(
       user_message, 
       context={'emotion': detected_emotion, 'participants': []}
   )
   
   # After Penny responds
   await self.personality_observer.record_penny_response(penny_response)
   
4. Periodically check learning (e.g., every 10 messages or on exit):
   
   await self.personality_observer.get_learning_summary()

That's it! Penny will learn silently without changing her behavior.
After collecting data, review insights to decide on Phase 2.
""")
    print("="*60 + "\n")


if __name__ == "__main__":
    print("\n🧠 PERSONALITY OBSERVER - SILENT LEARNING MODE\n")
    
    if len(sys.argv) > 1 and sys.argv[1] == "--instructions":
        print_integration_instructions()
    else:
        print("Running demo conversation...")
        print("(Use --instructions flag to see integration guide)\n")
        asyncio.run(demo_with_observer())
        print("\n" + "="*60)
        print("✅ Demo complete!")
        print("="*60)
        print("\nNext steps:")
        print("1. Integrate observer into your real Penny (see --instructions)")
        print("2. Have 5-10 real conversations")
        print("3. Run: python inspect_phase1_profile.py")
        print("4. Review insights and decide on Phase 2")
        print("="*60 + "\n")
