#!/usr/bin/env python3
"""
Test Penny's relationship awareness for Josh and Reneille demo
"""

import sys
import os
import json

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

print("🧪 Testing Penny's Relationship Awareness")
print("=" * 40)

try:
    from cj_enhanced_learning import CJEnhancedLearningSystem
    from emotional_memory_system import EmotionalMemorySystem
    from memory_system import MemoryManager
    
    # Initialize the system
    memory_manager = MemoryManager()
    emotional_memory = EmotionalMemorySystem(memory_manager)
    cj_learning = CJEnhancedLearningSystem(emotional_memory)
    
    print("✅ CJ's Enhanced Learning System initialized")
    print()
    
    # Test inputs mentioning Josh and Reneille
    test_scenarios = [
        {
            "input": "Josh, meet Penny! She knows about our Verizon days.",
            "expectation": "Should recognize Josh and Verizon history"
        },
        {
            "input": "Hey Penny, Brochacho works at Google now",
            "expectation": "Should recognize Brochacho as Josh's nickname"
        },
        {
            "input": "Reneille is here and she's getting married soon!",
            "expectation": "Should recognize Reneille and wedding context"
        },
        {
            "input": "Both Josh and Reneille work at Google",
            "expectation": "Should recognize both friends and Google connection"
        },
        {
            "input": "Reneille is super organized with wedding planning",
            "expectation": "Should recognize organizational skills and wedding"
        }
    ]
    
    print("🎯 Testing Relationship Recognition:")
    print("-" * 35)
    
    for i, scenario in enumerate(test_scenarios, 1):
        print(f"\n{i}. Input: '{scenario['input']}'")
        print(f"   Expected: {scenario['expectation']}")
        
        # Test learning opportunity detection
        opportunities = cj_learning.detect_learning_opportunities(
            scenario['input'], 
            "demo context"
        )
        
        if opportunities:
            best_opp = max(opportunities, key=lambda x: x.confidence)
            print(f"   🎯 Detected: {best_opp.opportunity_type.value}")
            print(f"   📋 Topic: {best_opp.topic}")
            
            # Test permission request generation
            permission = cj_learning.request_research_permission(best_opp)
            if permission:
                print(f"   💬 Response: '{permission[:80]}...'")
        
        # Test curiosity question generation
        curiosity = cj_learning.generate_curiosity_question(
            "friends", scenario['input']
        )
        print(f"   🤔 Curiosity: '{curiosity}'")
    
    print("\n" + "=" * 40)
    print("✅ Relationship awareness test complete!")
    print("\n🎭 Penny is ready to meet Josh and Reneille!")
    print("🚀 She should recognize them and engage appropriately.")
    
except Exception as e:
    print(f"❌ Test failed: {e}")
    import traceback
    traceback.print_exc()
