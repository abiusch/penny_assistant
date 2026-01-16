#!/usr/bin/env python3
"""
Test CJ's Enhanced Sassy Penny System
Shows off the improved attitude and edge
"""

import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def test_sassy_responses():
    """Test the enhanced sassy responses."""
    print("😈 Testing CJ's Enhanced Sassy Penny System")
    print("=" * 50)
    
    try:
        from cj_enhanced_learning import CJEnhancedLearningSystem
        from emotional_memory_system import EmotionalMemorySystem
        from memory_system import MemoryManager
        
        # Initialize systems
        memory_manager = MemoryManager()
        emotional_memory = EmotionalMemorySystem(memory_manager)
        sassy_penny = CJEnhancedLearningSystem(emotional_memory)
        
        print("✅ Sassy Penny system initialized")
        
        # Test scenarios with expected sass
        test_scenarios = [
            {
                "name": "Auto-Approved Tech Topic",
                "input": "How do I optimize FastAPI performance?",
                "expected_sass": "Should auto-research with attitude"
            },
            {
                "name": "Problem-Solving Request",
                "input": "I'm struggling with ElevenLabs TTS latency issues",
                "expected_sass": "Should offer help with edge"
            },
            {
                "name": "Basic Programming Question",
                "input": "What's the best way to handle async in Python?",
                "expected_sass": "Should provide solution with snark"
            },
            {
                "name": "Menu Bar App Challenge",
                "input": "Menu bar integration is being a pain",
                "expected_sass": "Should acknowledge frustration with wit"
            },
            {
                "name": "General Tech Question",
                "input": "Should I use microservices for my project?",
                "expected_sass": "Should roast overengineering tendencies"
            }
        ]
        
        print("\n😈 Testing Enhanced Sass Responses:")
        print("-" * 40)
        
        for i, scenario in enumerate(test_scenarios, 1):
            print(f"\n{i}. {scenario['name']}")
            print(f"   Input: \"{scenario['input']}\"")
            print(f"   Expected: {scenario['expected_sass']}")
            
            # Test learning opportunity detection
            opportunities = sassy_penny.detect_learning_opportunities(
                scenario['input'], "context"
            )
            
            if opportunities:
                best_opp = max(opportunities, key=lambda x: x.confidence * x.expected_user_interest)
                print(f"   🎯 Detected: {best_opp.opportunity_type.value}")
                print(f"   📋 Topic: {best_opp.topic}")
                
                # Test sassy permission request
                permission_request = sassy_penny.request_research_permission(best_opp)
                if permission_request:
                    print(f"   😈 Sassy Response: \"{permission_request}\"")
                else:
                    print("   🚫 Auto-approved or restricted")
                
                # Test sassy curiosity question
                question = sassy_penny.generate_curiosity_question(best_opp.topic, "context")
                print(f"   🤔 Sassy Question: \"{question}\"")
            else:
                print("   ❌ No opportunities detected")
        
        print("\n😈 Enhanced Sass Features:")
        print("-" * 30)
        print("   ✅ Mild profanity (damn, shit, hell, crap)")
        print("   ✅ Tech industry roasting")
        print("   ✅ Constructive criticism with edge")
        print("   ✅ Reality check commentary")
        print("   ✅ Anti-bullshit attitude")
        print("   ✅ Genuine enthusiasm when deserved")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def show_sass_examples():
    """Show examples of the enhanced sass levels."""
    print("\n💬 Sass Level Examples:")
    print("=" * 30)
    
    examples = [
        {
            "situation": "Good Question",
            "old_response": "I can research FastAPI optimization for you. It connects to your current work. Want me to dig into best practices?",
            "sassy_response": "Already researching FastAPI optimization because I know you're obsessed with this stuff."
        },
        {
            "situation": "Bad Practice",
            "old_response": "You should use async/await instead of blocking calls.",
            "sassy_response": "Stop using blocking calls like it's 1995. Why: because debugging that shit is a nightmare. Next: refactor into proper async/await."
        },
        {
            "situation": "Overengineering",
            "old_response": "You might want to consider a simpler approach.",
            "sassy_response": "Just use SQLite for now. You don't need a distributed database cluster for your side project. Next: get it working, then optimize if you actually have users."
        },
        {
            "situation": "Curiosity Question",
            "old_response": "What's your take on FastAPI for your current setup?",
            "sassy_response": "What's your actual plan with FastAPI, or are we just winging it?"
        }
    ]
    
    for example in examples:
        print(f"\n🎭 {example['situation']}:")
        print(f"   Before: \"{example['old_response']}\"")
        print(f"   😈 Sassy: \"{example['sassy_response']}\"")


def show_personality_balance():
    """Show how the sass is balanced with helpfulness."""
    print("\n⚖️ Sass vs Helpfulness Balance:")
    print("=" * 35)
    
    print("""
✅ What the Enhanced Sass DOES:
   • Roasts bad practices, not people
   • Calls out industry nonsense
   • Uses mild profanity for emphasis
   • Provides reality checks with humor
   • Shows genuine enthusiasm for good work
   • Gives constructive criticism with edge

❌ What the Enhanced Sass DOESN'T:
   • Mock CJ personally
   • Be unhelpful or destructive
   • Use excessive profanity
   • Discourage learning
   • Be mean-spirited
   • Ignore actual problems

🎯 The Result:
   A more authentic, entertaining AI companion that:
   • Feels like talking to a competent friend with attitude
   • Provides honest feedback without sugarcoating
   • Makes technical conversations more engaging
   • Maintains warmth underneath the sass
   • Keeps CJ entertained while being genuinely helpful
    """)


if __name__ == "__main__":
    print("😈 CJ's Enhanced Sassy Penny System Test")
    print("""This tests the upgraded personality with more edge and attitude.
    
    🎯 Enhanced Features:
    • Actual sass and mild profanity
    • Tech industry roasting
    • Reality check commentary
    • Constructive criticism with bite
    • Authentic personality with edge
    """)
    
    success = test_sassy_responses()
    
    if success:
        show_sass_examples()
        show_personality_balance()
        
        print("\n🚀 Ready for Enhanced Sassy Conversations!")
        print("\n🔥 Try These Commands:")
        print("   python cj_personalized_penny.py     # Full sassy experience")
        print("   python test_cj_personalization.py   # Test enhanced system")
        
        print("\n💬 Try These for Maximum Sass:")
        print("   \"Should I use microservices for everything?\"")
        print("   \"My code isn't working and I don't know why\"")
        print("   \"What's the best JavaScript framework?\"")
        print("   \"How do I make my app scale to billions?\"")
        
        print("\n😈 Warning: Penny now has opinions and isn't afraid to share them!")
    else:
        print("\n⚠️ Please fix issues before unleashing the sass.")
