#!/usr/bin/env python3
"""
Penny Chat Interface - Text-based conversation with full personality system
Uses all the same systems as voice interface but with keyboard input/output
"""

print("🚀 Starting Penny Chat Interface...")

try:
    import sys
    import os
    import time
    from typing import Dict, Any
    print("✅ Basic imports successful")
    
    # Add src to path
    sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
    print("✅ Path setup complete")
    
    # Import all the same systems used in voice interface
    print("🔄 Importing performance monitor...")
    from performance_monitor import time_operation, OperationType
    print("✅ Performance monitor imported")
    
    print("🔄 Importing pragmatics system...")
    from pragmatics_enhanced_penny import PragmaticsEnhancedPenny
    print("✅ Pragmatics system imported")

except Exception as e:
    print(f"❌ Import error: {e}")
    import traceback
    traceback.print_exc()
    print("Press Enter to exit...")
    input()
    exit(1)

def create_enhanced_penny():
    """Initialize the same enhanced personality system used in voice interface"""
    try:
        print("🧠 Initializing PragmaticsEnhancedPenny...")
        # Initialize the full pragmatics-enhanced system
        enhanced_penny = PragmaticsEnhancedPenny()
        print("🧠 Enhanced personality system initialized successfully")
        return enhanced_penny
    except Exception as e:
        print(f"⚠️ Error initializing enhanced personality: {e}")
        import traceback
        traceback.print_exc()
        return None

def detect_context(text: str) -> Dict[str, Any]:
    """Same context detection logic as voice interface"""
    context = {'topic': 'conversation', 'emotion': 'neutral', 'participants': []}
    text_lower = text.lower()
    
    # Detect personal topics
    if 'feeling' in text_lower or 'how are' in text_lower:
        context['topic'] = 'personal'
        context['emotion'] = 'curious'
    
    # Detect development/programming topics
    elif any(word in text_lower for word in ['code', 'programming', 'development', 'debugging', 'fix', 'break', 'improvements']):
        context['topic'] = 'programming'
        if any(word in text_lower for word in ['break', 'broken', 'frustrat', 'backward']):
            context['emotion'] = 'frustrated'
        elif any(word in text_lower for word in ['ability', 'can you', 'write']):
            context['emotion'] = 'curious'
    
    # Detect participants
    if any(name in text_lower for name in ['josh', 'brochacho']):
        context['participants'].append('josh')
    if 'reneille' in text_lower:
        context['participants'].append('reneille')
    
    return context

def main():
    """Main chat loop"""
    print("🎭 Penny Chat Interface - Enhanced Personality System")
    print("="*60)
    
    # Initialize enhanced personality system
    enhanced_penny = create_enhanced_penny()
    if not enhanced_penny:
        print("❌ Could not initialize enhanced personality system.")
        print("Press Enter to exit...")
        input()
        return
    
    print("\n🎯 Features Active:")
    print("   • Dynamic personality states with contextual transitions")
    print("   • Machine learning adaptation from interactions")
    print("   • Context-aware response generation")
    print("   • Relationship awareness (Josh, Reneille)")
    print("   • Conversational pragmatics (ask me anything detection)")
    print("   • Development-focused pattern matching")
    print("   • Balanced personality coordination")
    
    # Test greeting
    print("\n🔊 Testing enhanced personality system...")
    try:
        test_context = {'topic': 'conversation', 'emotion': 'neutral', 'participants': []}
        greeting = enhanced_penny.generate_pragmatically_aware_response(
            "Hello Penny!", test_context
        )
        print(f"🤖 Penny: {greeting}")
        print("✅ Enhanced personality system test successful!")
    except Exception as e:
        print(f"❌ Greeting test failed: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n💬 Chat Interface Ready! (Type 'quit', 'exit', or Ctrl+C to end)")
    print("-" * 60)
    
    conversation_count = 0
    
    try:
        while True:
            # Get user input
            print("\n📝 You: ", end="")
            user_input = input().strip()
            
            # Handle exit commands
            if user_input.lower() in ['quit', 'exit', 'bye', 'goodbye']:
                print("\n👋 Penny: Thanks for chatting! See you next time!")
                break
            
            if not user_input:
                print("💭 (Type something to chat, or 'quit' to exit)")
                continue
            
            conversation_count += 1
            
            # Generate response using same pipeline as voice interface
            try:
                with time_operation(OperationType.LLM):
                    # Context detection (same as voice interface)
                    context = detect_context(user_input)
                    
                    # Generate enhanced response using full personality system
                    enhanced_response = enhanced_penny.generate_pragmatically_aware_response(
                        user_input, context
                    )
                
                print(f"🤖 Penny: {enhanced_response}")
                
                # Show performance metrics occasionally
                if conversation_count % 5 == 0:
                    print(f"\n📊 Performance: {conversation_count} responses generated")
                
            except KeyboardInterrupt:
                raise  # Let this bubble up to outer handler
            except Exception as e:
                print(f"❌ Error generating response: {e}")
                import traceback
                traceback.print_exc()
                print("🔄 Trying again...")
                
    except KeyboardInterrupt:
        print("\n\n👋 Chat ended by user. Goodbye!")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n📊 Final Stats:")
    print(f"   💬 Total conversations: {conversation_count}")
    print("   🎭 Enhanced personality system: Active")
    print("   🧠 All advanced features: Enabled")
    print("\n✨ Thanks for chatting with Penny!")

if __name__ == "__main__":
    main()
