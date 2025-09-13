#!/usr/bin/env python3
"""
Quick Demo of Sass Control System
Shows how different sass levels affect Penny's responses
"""

import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def demo_sass_levels():
    """Demonstrate different sass levels with the same input"""
    print("🎭 Sass Level Demo - Same Question, Different Attitudes")
    print("="*60)
    
    try:
        from sass_enhanced_penny import create_sass_enhanced_penny, SassLevel
        
        # Create sass-enhanced Penny
        penny = create_sass_enhanced_penny("demo_sass.db")
        session_id = penny.start_conversation_session("demo")
        
        # Test question
        test_question = "How do you feel about helping me with programming?"
        
        print(f"Question: \"{test_question}\"\n")
        
        # Test each sass level
        for level in SassLevel:
            print(f"🎯 {level.value.upper()}:")
            
            # Set sass level
            penny.sass_controller.set_sass_level(level)
            config = penny.sass_controller.get_current_config()
            print(f"   ({config.description})")
            
            # Generate response
            try:
                response = penny.generate_sass_aware_response(test_question)
                # Limit response length for demo
                if len(response) > 150:
                    response = response[:150] + "..."
                print(f"   Penny: {response}")
            except Exception as e:
                print(f"   Error: {e}")
            
            print()  # Blank line
        
        penny.end_conversation_session("Demo complete")
        os.remove("demo_sass.db")
        
        print("✨ Notice how Penny's personality changes with each sass level!")
        print("   • MINIMAL: Polite and professional")
        print("   • LITE: Friendly with light humor") 
        print("   • MEDIUM: Balanced sass and helpfulness")
        print("   • SPICY: More sarcastic and direct")
        print("   • MAXIMUM: Full personality unleashed")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()

def show_sass_commands():
    """Show available sass control commands"""
    print("\n🎮 Available Sass Control Commands:")
    print("="*40)
    
    commands = [
        ("Direct Level Setting:", [
            "set sass to minimal",
            "set sass to lite", 
            "set sass to medium",
            "set sass to spicy",
            "set sass to maximum"
        ]),
        ("Natural Language:", [
            "tone it down",
            "dial it back", 
            "be more sassy",
            "turn it up",
            "professional mode",
            "maximum sass please"
        ]),
        ("Status Commands:", [
            "sass level",
            "current sass",
            "sass options",
            "list sass levels"
        ])
    ]
    
    for category, command_list in commands:
        print(f"\n{category}")
        for cmd in command_list:
            print(f"   • \"{cmd}\"")

if __name__ == "__main__":
    print("🎭 Sass Control System Demo")
    
    demo_sass_levels()
    show_sass_commands()
    
    print(f"\n🚀 Ready to try it yourself!")
    print(f"   Run: python3 memory_chat_penny.py")
    print(f"   Then try: 'set sass to spicy' or 'tone it down'")
