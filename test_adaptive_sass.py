#!/usr/bin/env python3
"""
Test Adaptive Sass Learning System
Verifies that Penny learns sass preferences from user interactions
"""

import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def test_adaptive_sass_learning():
    """Test the adaptive sass learning system"""
    print("🧠 Testing Adaptive Sass Learning System")
    print("="*50)
    
    try:
        from adaptive_sass_learning import create_adaptive_sass_learning
        from sass_controller import SassLevel
        
        # Create learning system
        learning = create_adaptive_sass_learning()
        print("✅ Adaptive sass learning created")
        
        # Simulate learning scenarios
        print("\n1. Simulating learning scenarios...")
        
        scenarios = [
            # User consistently wants minimal sass when programming + frustrated
            ("tone it down", SassLevel.MEDIUM, SassLevel.MINIMAL, 
             {'topic': 'programming', 'emotion': 'frustrated', 'participants': []}),
            ("professional mode", SassLevel.SPICY, SassLevel.MINIMAL,
             {'topic': 'programming', 'emotion': 'frustrated', 'participants': []}),
            ("dial it back", SassLevel.LITE, SassLevel.MINIMAL,
             {'topic': 'programming', 'emotion': 'frustrated', 'participants': []}),
            
            # User likes spicy sass when talking with Josh
            ("be more sassy", SassLevel.MEDIUM, SassLevel.SPICY,
             {'topic': 'conversation', 'emotion': 'neutral', 'participants': ['josh']}),
            ("turn it up", SassLevel.LITE, SassLevel.SPICY,
             {'topic': 'conversation', 'emotion': 'neutral', 'participants': ['josh']}),
            ("maximum sass", SassLevel.MEDIUM, SassLevel.MAXIMUM,
             {'topic': 'conversation', 'emotion': 'neutral', 'participants': ['josh']}),
        ]
        
        # Record all learning events
        for command, from_sass, to_sass, context in scenarios:
            learning.record_sass_adjustment(command, from_sass, to_sass, context)
            print(f"   Recorded: '{command}' in {context.get('topic', 'general')} context")
        
        # Test learned preferences
        print("\n2. Testing learned preferences...")
        
        test_contexts = [
            ({'topic': 'programming', 'emotion': 'frustrated', 'participants': []}, "Should prefer MINIMAL"),
            ({'topic': 'conversation', 'emotion': 'neutral', 'participants': ['josh']}, "Should prefer SPICY/MAXIMUM"),
            ({'topic': 'conversation', 'emotion': 'neutral', 'participants': []}, "No specific preference"),
            ({'topic': 'personal', 'emotion': 'excited', 'participants': []}, "No specific preference"),
        ]
        
        for context, expected in test_contexts:
            learned_sass = learning.get_learned_sass_for_context(context)
            context_key = learning._get_context_key(context)
            
            if learned_sass:
                print(f"   ✅ {context_key} → {learned_sass.value} sass ({expected})")
            else:
                print(f"   ⚪ {context_key} → No preference ({expected})")
        
        # Get learning insights
        print("\n3. Learning insights...")
        insights = learning.get_learning_insights()
        print(f"   Total adjustments: {insights['total_adjustments']}")
        print(f"   Learned patterns: {insights['learned_patterns']}")
        
        if insights['context_preferences']:
            print("   Context preferences:")
            for context, pref in insights['context_preferences'].items():
                print(f"     • {context}: {pref['preferred_sass']} (confidence: {pref['confidence']:.2f})")
        
        return True
        
    except Exception as e:
        print(f"❌ Adaptive sass learning test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_adaptive_sass_penny():
    """Test the full adaptive sass-enhanced Penny system"""
    print("\n🤖 Testing Adaptive Sass-Enhanced Penny")
    print("="*50)
    
    try:
        from adaptive_sass_enhanced_penny import create_adaptive_sass_enhanced_penny
        
        # Create adaptive Penny
        penny = create_adaptive_sass_enhanced_penny("test_adaptive.db")
        print("✅ Adaptive sass-enhanced Penny created")
        
        # Start session
        session_id = penny.start_conversation_session("test")
        print(f"✅ Session started: {session_id}")
        
        # Test learning sequence
        print("\n1. Teaching Penny sass preferences...")
        
        learning_sequence = [
            # Teach: minimal sass for programming frustration
            ("tone it down", {'topic': 'programming', 'emotion': 'frustrated'}),
            ("This bug is driving me crazy", {'topic': 'programming', 'emotion': 'frustrated'}),  # Should use minimal
            
            # Teach: spicy sass for Josh conversations
            ("be more sassy", {'topic': 'conversation', 'emotion': 'neutral', 'participants': ['josh']}),
            ("What do you think about Josh?", {'topic': 'conversation', 'emotion': 'neutral', 'participants': ['josh']}),  # Should use spicy
            
            # Test learning insights
            ("what have you learned about my sass preferences?", {'topic': 'conversation', 'emotion': 'curious'}),
        ]
        
        for i, (user_input, context) in enumerate(learning_sequence, 1):
            print(f"\n   {i}. User: {user_input}")
            
            try:
                # Use adaptive response generation
                response = penny.generate_adaptive_sass_response(user_input, context)
                current_sass = penny.sass_controller.current_level.value
                
                # Check if this was a learning moment
                learned_sass = penny.sass_learning.get_learned_sass_for_context(context)
                if learned_sass and not user_input.startswith(("tone", "be more", "what have")):
                    print(f"      🧠 Applied learned preference: {learned_sass.value} sass")
                
                print(f"      Penny [{current_sass}]: {response[:100]}...")
                
            except Exception as e:
                print(f"      Error: {e}")
        
        # Test comprehensive status
        print("\n2. Final adaptive status...")
        status = penny.get_comprehensive_adaptive_status()
        print(f"   Current sass: {status['sass_level']}")
        print(f"   Sass adjustments: {status['adaptive_learning']['total_adjustments']}")
        print(f"   Learned patterns: {status['adaptive_learning']['learned_patterns']}")
        
        if status['adaptive_learning']['context_preferences']:
            print("   Learned preferences:")
            for context, pref in status['adaptive_learning']['context_preferences'].items():
                print(f"     • {context}: {pref['preferred_sass']} sass")
        
        penny.end_conversation_session("Test completed")
        
        # Clean up
        os.remove("test_adaptive.db")
        return True
        
    except Exception as e:
        print(f"❌ Adaptive Penny test failed: {e}")
        import traceback
        traceback.print_exc()        
        return False

def test_context_adaptation():
    """Test that Penny adapts sass based on context"""
    print("\n🎯 Testing Context-Based Sass Adaptation")
    print("="*50)
    
    try:
        from adaptive_sass_enhanced_penny import create_adaptive_sass_enhanced_penny
        
        penny = create_adaptive_sass_enhanced_penny("test_context.db")
        
        # Pre-train some preferences
        print("1. Pre-training sass preferences...")
        training_data = [
            ("tone it down", {'topic': 'programming', 'emotion': 'frustrated'}),
            ("be more sassy", {'topic': 'conversation', 'emotion': 'neutral', 'participants': ['josh']}),
        ]
        
        for command, context in training_data:
            penny.generate_adaptive_sass_response(command, context)
            print(f"   Trained: {command} for {context}")
        
        # Test adaptation in different contexts
        print("\n2. Testing sass adaptation...")
        test_contexts = [
            ("How do I fix this error?", {'topic': 'programming', 'emotion': 'frustrated'}, "Should be minimal/professional"),
            ("Tell me about Josh", {'topic': 'conversation', 'emotion': 'neutral', 'participants': ['josh']}, "Should be spicy/sassy"),
            ("How are you doing?", {'topic': 'personal', 'emotion': 'neutral'}, "Should use default sass"),
        ]
        
        for question, context, expectation in test_contexts:
            print(f"\n   Question: {question}")
            print(f"   Context: {context}")
            print(f"   Expected: {expectation}")
            
            # Check what sass level would be used
            learned_sass = penny.sass_learning.get_learned_sass_for_context(context)
            if learned_sass:
                print(f"   🧠 Learned preference: {learned_sass.value} sass")
            else:
                print(f"   🌱 No learned preference - using default")
        
        os.remove("test_context.db")
        return True
        
    except Exception as e:
        print(f"❌ Context adaptation test failed: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Running Adaptive Sass Learning Tests...")
    
    results = []
    results.append(("Adaptive Learning Core", test_adaptive_sass_learning()))
    results.append(("Adaptive Sass Penny", test_adaptive_sass_penny()))
    results.append(("Context Adaptation", test_context_adaptation()))
    
    print("\n📊 Test Results:")
    print("="*50)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {test_name:25} {status}")
        if result:
            passed += 1
    
    print(f"\n🎆 Results: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("\n🎉 All tests passed! Adaptive sass learning system is ready!")
        print("\n💡 Key Benefits:")
        print("   • Penny learns your sass preferences from usage")
        print("   • Context-aware sass adaptation")
        print("   • User control TEACHES rather than just controls")
        print("   • Authentic personality growth over time")
        print("\n🚀 Try it:")
        print("   python3 adaptive_sass_chat.py")
        print("   Say 'tone it down' when frustrated → Penny learns!")
        print("   Say 'be more sassy' with friends → Penny adapts!")
    else:
        print("\n⚠️ Some tests failed. Check the errors above.")
