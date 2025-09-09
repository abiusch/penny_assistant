#!/usr/bin/env python3
"""
Complete ML Penny Demo
Shows the full machine learning personality system in action
"""

import sys
import os
import time
import json

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from ml_enhanced_penny import create_ml_enhanced_penny

def main():
    print("🧠 Complete ML Penny Demo")
    print("Machine Learning Personality System")
    print("=" * 50)
    
    # Initialize ML-enhanced Penny
    ml_penny = create_ml_enhanced_penny()
    
    print("🎯 Demonstrating machine learning personality adaptation...")
    print()
    
    # Simulation of learning over time
    learning_scenarios = [
        # Initial interactions - testing baseline
        {
            'phase': 'Initial Testing',
            'interactions': [
                {
                    'user': "Hey Penny, help me debug this code",
                    'response': "Let's look at the error and trace through the logic.",
                    'context': {'topic': 'debugging'},
                    'user_feedback': "That was really helpful!"
                },
                {
                    'user': "Should I use microservices?",
                    'response': "Consider whether the complexity overhead is worth it.",
                    'context': {'topic': 'architecture'},
                    'user_feedback': "Too boring, can you be more entertaining?"
                }
            ]
        },
        # After learning - more humor
        {
            'phase': 'After Learning Humor Preference',
            'interactions': [
                {
                    'user': "More debugging issues...",
                    'response': "Another debugging adventure! Let's solve this mystery.",
                    'context': {'topic': 'debugging'},
                    'user_feedback': "Much better! I love the humor."
                },
                {
                    'user': "Framework choice again?",
                    'response': "Ah, the eternal framework question!",
                    'context': {'topic': 'frameworks'},
                    'user_feedback': "Perfect! That's exactly what I wanted."
                }
            ]
        },
        # Testing with Josh
        {
            'phase': 'Josh Interaction Learning',
            'interactions': [
                {
                    'user': "Josh thinks this architecture is overcomplicated",
                    'response': "Josh has a point - sometimes simple is better.",
                    'context': {'participants': ['josh'], 'topic': 'architecture'},
                    'user_feedback': "Josh laughed at that!"
                }
            ]
        },
        # Testing with Reneille
        {
            'phase': 'Reneille Interaction Learning',
            'interactions': [
                {
                    'user': "Reneille needs help organizing this project",
                    'response': "Let's create a systematic approach to project organization.",
                    'context': {'participants': ['reneille'], 'topic': 'organization'},
                    'user_feedback': "She really appreciated the structured approach."
                }
            ]
        },
        # Testing emotional adaptation
        {
            'phase': 'Emotional Context Learning',
            'interactions': [
                {
                    'user': "I'm really frustrated with this bug",
                    'response': "I understand debugging can be frustrating. Let's tackle this together.",
                    'context': {'topic': 'debugging', 'emotion': 'frustrated'},
                    'user_feedback': "Thank you for being so supportive."
                }
            ]
        }
    ]
    
    # Run learning simulation
    for phase_data in learning_scenarios:
        print(f"📚 {phase_data['phase']}")
        print("-" * len(phase_data['phase']) + "---")
        
        for interaction in phase_data['interactions']:
            print(f"👤 User: {interaction['user']}")
            
            # Generate adaptive response
            adaptive_response = ml_penny.generate_adaptive_response(
                interaction['user'],
                interaction['response'],
                interaction['context']
            )
            
            print(f"🤖 Penny: {adaptive_response}")
            
            # Process feedback for learning
            ml_penny.process_user_feedback(
                interaction['user_feedback'],
                interaction['context']
            )
            
            print(f"💬 Feedback: {interaction['user_feedback']}")
            
            # Show current personality state
            stats = ml_penny.get_learning_statistics()
            print(f"📊 Humor Level: {stats['current_humor_level']:.3f} | " +
                  f"Sass Level: {stats['current_sass_level']:.3f} | " +
                  f"Interactions: {stats['total_interactions']}")
            print()
        
        print()
    
    # Show final learned personality
    print("🎭 Final Learned Personality Configuration")
    print("=" * 45)
    
    final_stats = ml_penny.get_learning_statistics()
    print(f"Total Interactions: {final_stats['total_interactions']}")
    print(f"Average Engagement: {final_stats['avg_engagement_score']:.3f}")
    print(f"Humor Success Rate: {final_stats['humor_success_rate']:.3f}")
    print(f"Personality Confidence: {final_stats['personality_confidence']:.3f}")
    print(f"Current Humor Level: {final_stats['current_humor_level']:.3f}")
    print(f"Current Sass Level: {final_stats['current_sass_level']:.3f}")
    print()
    
    # Demonstrate context-aware prompts
    print("🎯 Context-Aware Personality Prompts")
    print("=" * 38)
    
    contexts = [
        {'topic': 'debugging', 'emotion': 'frustrated'},
        {'participants': ['josh'], 'topic': 'architecture'},
        {'participants': ['reneille'], 'topic': 'organization'},
        {'topic': 'frameworks', 'emotion': 'excited'}
    ]
    
    for context in contexts:
        prompt = ml_penny.get_personality_prompt_for_llm(context)
        print(f"Context: {context}")
        print(f"Prompt: {prompt}")
        print()
    
    print("✨ ML Learning Capabilities Demonstrated:")
    print("🔬 Adapts humor frequency based on user feedback")
    print("🎭 Adjusts sass level based on interaction success")
    print("👥 Personalizes responses for specific people (Josh/Reneille)")
    print("😊 Modifies supportiveness based on emotional context")
    print("🧠 Learns technical depth preferences from user reactions")
    print("⚡ Stores interaction history for continuous improvement")
    print("📊 Tracks humor success rates and engagement metrics")
    print("🎯 Generates context-aware personality prompts")
    print()
    print("🚀 Ready for Integration with Existing Penny Systems!")
    print("This ML personality core can replace or enhance existing personality systems.")

if __name__ == "__main__":
    main()
