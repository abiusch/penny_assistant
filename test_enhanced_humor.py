#!/usr/bin/env python3
"""
Test Enhanced Humor System Integration
Quick demo to see Penny's enhanced comedy in action
"""

import sys
import os
import time

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from penny_humor_integration import create_penny_with_enhanced_humor

def main():
    print("🎭 Penny's Enhanced Humor System Demo")
    print("=" * 45)
    print("Testing contextual comedy, observational humor, and timing-based jokes")
    print()
    
    # Create enhanced humor Penny
    penny_humor = create_penny_with_enhanced_humor()
    
    demo_scenarios = [
        {
            'title': "Josh Recognition + Callback Humor",
            'input': "Hey Josh! What do you think about this React code?",
            'base_response': "React looks solid. The component structure is clean.",
            'context': {'participants': ['josh'], 'topic': 'react'}
        },
        {
            'title': "Reneille + Wedding Planning Humor",
            'input': "Reneille, any tips for organizing a large project?",
            'base_response': "Here are some project organization strategies.",
            'context': {'participants': ['reneille'], 'topic': 'organization'}
        },
        {
            'title': "Debugging Observational Comedy",
            'input': "This code was working yesterday and now it's completely broken",
            'base_response': "Let's trace through the recent changes to identify the issue.",
            'context': {'topic': 'debugging', 'emotion': 'frustrated'}
        },
        {
            'title': "Framework Choice Tech Roasting",
            'input': "Should I learn Vue, React, or Angular for my new project?",
            'base_response': "React has the largest ecosystem and job market.",
            'context': {'topic': 'frameworks', 'emotion': 'confused'}
        },
        {
            'title': "Microservices Architecture Roasting",
            'input': "I'm thinking about using microservices for my todo app",
            'base_response': "Consider whether the complexity overhead is worth it for your use case.",
            'context': {'topic': 'architecture', 'complexity': 'overengineering'}
        },
        {
            'title': "AI Self-Aware Humor",
            'input': "Can AI really understand human emotions?",
            'base_response': "AI can analyze patterns in text that correlate with emotional states.",
            'context': {'topic': 'ai', 'philosophical': True}
        },
        {
            'title': "CJ Self-Roasting",
            'input': "What's your opinion on my coding style?",
            'base_response': "Your code shows good understanding of clean architecture principles.",
            'context': {'self_directed': True, 'topic': 'coding'}
        },
        {
            'title': "Excited Response Modification",
            'input': "This is amazing! FastAPI is so much better than Flask!",
            'base_response': "FastAPI does have excellent performance and automatic documentation.",
            'context': {'emotion': 'excited', 'topic': 'fastapi'}
        }
    ]
    
    for i, scenario in enumerate(demo_scenarios, 1):
        print(f"🎪 Demo {i}: {scenario['title']}")
        print(f"📝 Input: \"{scenario['input']}\"")
        print(f"🤖 Base Response: \"{scenario['base_response']}\"")
        
        # Generate enhanced response
        start_time = time.time()
        enhanced_response = penny_humor.generate_enhanced_response(
            scenario['input'],
            scenario['base_response'],
            scenario['context']
        )
        processing_time = (time.time() - start_time) * 1000
        
        print(f"😂 Enhanced Response: \"{enhanced_response}\"")
        print(f"⚡ Processing: {processing_time:.1f}ms")
        print(f"📊 Humor Stats: {penny_humor.get_humor_stats()}")
        print("-" * 45)
        print()
    
    print("🎭 Enhanced Humor Features Demonstrated:")
    print("✅ Relationship-specific callback humor (Josh/Reneille)")
    print("✅ Observational comedy about coding/debugging")
    print("✅ Tech industry roasting with constructive feedback")
    print("✅ Self-aware AI humor and meta-commentary")
    print("✅ Contextual response modifications based on emotion")
    print("✅ Timing-based humor and conversation awareness")
    print("✅ Analogy generation for complex concepts")
    print()
    print("🚀 Ready to integrate with main personality system!")

if __name__ == "__main__":
    main()
