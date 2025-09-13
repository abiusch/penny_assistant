#!/usr/bin/env python3
"""
Memory-Enhanced Chat Interface - Text-based conversation with persistent memory
Builds on chat_penny.py to add cross-session relationship building
"""

print("🚀 Starting Memory-Enhanced Penny Chat Interface...")

try:
    import sys
    import os
    import time
    from typing import Dict, Any
    print("✅ Basic imports successful")
    
    # Add src to path
    sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
    print("✅ Path setup complete")
    
    # Import the sass-enhanced system instead of basic memory system
    print("🔄 Importing sass-enhanced Penny...")
    from sass_enhanced_penny import create_sass_enhanced_penny
    from performance_monitor import time_operation, OperationType
    print("✅ Sass-enhanced system imported")

except Exception as e:
    print(f"❌ Import error: {e}")
    import traceback
    traceback.print_exc()
    print("Press Enter to exit...")
    input()
    exit(1)

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
    
    # Detect memory-related queries
    elif any(word in text_lower for word in ['remember', 'recall', 'know about me', 'what do you know']):
        context['topic'] = 'memory'
        context['emotion'] = 'curious'
    
    # Detect participants
    if any(name in text_lower for name in ['josh', 'brochacho']):
        context['participants'].append('josh')
    if 'reneille' in text_lower:
        context['participants'].append('reneille')
    
    return context

def main():
    """Main chat loop with memory and sass control capabilities"""
    print("🧠 Sass-Enhanced Memory Chat Interface")
    print("="*70)
    
    # Initialize sass-enhanced personality system
    print("🧠 Initializing sass-enhanced personality system...")
    try:
        penny = create_sass_enhanced_penny()
        print("✅ Sass-enhanced Penny initialized successfully")
    except Exception as e:
        print(f"❌ Error initializing sass-enhanced Penny: {e}")
        import traceback
        traceback.print_exc()
        print("Press Enter to exit...")
        input()
        return
    
    # Start conversation session
    session_id = penny.start_conversation_session("text")
    
    print("\n🎯 Enhanced Features Active:")
    print("   • Persistent memory across conversations")
    print("   • Cross-session relationship building")
    print("   • User-controllable sass levels (minimal to maximum)")
    print("   • Dynamic personality states with memory context")
    print("   • Machine learning adaptation from interactions")
    print("   • Context-aware response generation")
    print("   • Inside jokes and preference tracking")
    print("   • Conversational pragmatics and role detection")
    
    # Show existing memory if any
    print("\n📚 Checking what I remember about you...")
    relationship_summary = penny.get_relationship_summary()
    if "still getting to know" not in relationship_summary:
        print(f"🤝 {relationship_summary}")
    else:
        print("🌱 This is a fresh start - I'm ready to learn about you!")
    
    # Test greeting
    print("\n🔊 Testing sass-enhanced personality system...")
    try:
        test_context = {'topic': 'conversation', 'emotion': 'neutral', 'participants': []}
        # Use a simpler greeting to avoid overly energetic responses
        greeting = penny.generate_sass_aware_response(
            "Hi Penny, I'm back!", test_context
        )
        print(f"🤖 Penny ({penny.get_sass_status()}): {greeting}")
        print("✅ Sass-enhanced personality system test successful!")
    except Exception as e:
        print(f"❌ Greeting test failed: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n💬 Sass-Enhanced Memory Chat Ready! Commands:")
    print("   • 'memory stats' - Show what I remember about you")
    print("   • 'search memories [term]' - Search my memories")
    print("   • 'remember [fact]' - Manually add something to my memory")
    print("   • 'sass level' - Show current sass setting")
    print("   • 'set sass to [level]' - Change sass (minimal/lite/medium/spicy/maximum)")
    print("   • 'tone it down' or 'be more sassy' - Adjust sass naturally")
    print("   • 'sass options' - List all sass levels")
    print("   • 'quit', 'exit', or Ctrl+C to end")
    print("-" * 70)
    
    conversation_count = 0
    
    try:
        while True:
            # Get user input
            print("\n📝 You: ", end="")
            user_input = input().strip()
            
            # Handle exit commands
            if user_input.lower() in ['quit', 'exit', 'bye', 'goodbye']:
                print("\n👋 Penny: Thanks for chatting! I'll remember our conversation for next time!")
                break
            
            if not user_input:
                print("💭 (Type something to chat, or 'quit' to exit)")
                continue
            
            conversation_count += 1
            
            # Handle special memory commands
            if user_input.lower() == "memory stats":
                penny.show_memory_stats()
                continue
            elif user_input.lower().startswith("search memories "):
                search_term = user_input[15:].strip()
                result = penny.search_memories(search_term)
                print(f"🔍 {result}")
                continue
            elif user_input.lower().startswith("remember "):
                fact = user_input[9:].strip()
                success = penny.manually_store_memory("user_fact", f"manual_{conversation_count}", fact)
                if success:
                    print("✅ Got it! I'll remember that.")
                else:
                    print("❌ Sorry, couldn't store that memory.")
                continue
            
            # Generate response using memory-enhanced system
            try:
                with time_operation(OperationType.LLM):
                    # Context detection (same as voice interface)
                    context = detect_context(user_input)
                    
                    # Generate sass-aware response (includes memory integration)
                    enhanced_response = penny.generate_sass_aware_response(
                        user_input, context
                    )
                
                print(f"🤖 Penny: {enhanced_response}")
                
                # Show memory learning indicators occasionally
                if conversation_count % 3 == 0:
                    print(f"\n🧠 I'm learning from our conversation... ({conversation_count} exchanges so far)")
                
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
    
    # End conversation session with summary
    summary = f"Text chat with {conversation_count} exchanges. Topics discussed."
    penny.end_conversation_session(summary)
    
    print("\n📊 Final Session Stats:")
    print(f"   💬 Total conversations: {conversation_count}")
    print(f"   🧠 Memory system: Active")
    print(f"   🔄 Session ID: {session_id}")
    
    # Show final memory summary
    print("\n🤝 What I learned about you this session:")
    final_summary = penny.get_relationship_summary()
    print(f"   {final_summary}")
    
    print("\n✨ Thanks for chatting! I'll remember our conversation for next time.")
    print("💾 Your memories are saved in: penny_memory.db")

if __name__ == "__main__":
    main()
