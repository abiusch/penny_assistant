#!/usr/bin/env python3
"""
Adaptive Sass Memory Chat Interface
Chat interface with adaptive sass learning - Penny learns your preferences!
"""

import sys
import os

# Add src to path and handle imports
try:
    sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
    print("✅ Path setup complete")
    
    # Import the adaptive sass-enhanced system
    print("🔄 Importing adaptive sass-enhanced Penny...")
    from adaptive_sass_enhanced_penny import create_adaptive_sass_enhanced_penny
    from performance_monitor import time_operation, OperationType
    print("✅ Adaptive sass-enhanced system imported")

except Exception as e:
    print(f"❌ Import error: {e}")
    import traceback
    traceback.print_exc()
    print("Press Enter to exit...")
    input()
    sys.exit(1)

def detect_context(user_input: str) -> dict:
    """Detect conversation context for enhanced responses"""
    context = {'topic': 'conversation', 'emotion': 'neutral', 'participants': []}
    
    input_lower = user_input.lower()
    
    # Detect topics
    if any(word in input_lower for word in ['code', 'programming', 'debug', 'bug', 'api', 'function', 'error']):
        context['topic'] = 'programming'
    elif any(word in input_lower for word in ['feel', 'emotion', 'mood', 'happy', 'sad', 'frustrated']):
        context['topic'] = 'personal'
    elif any(word in input_lower for word in ['remember', 'recall', 'memory', 'know about']):
        context['topic'] = 'memory'
    elif any(word in input_lower for word in ['sass', 'attitude', 'personality']):
        context['topic'] = 'sass'
    
    # Detect emotions
    if any(word in input_lower for word in ['frustrated', 'angry', 'annoyed', 'broken']):
        context['emotion'] = 'frustrated'
    elif any(word in input_lower for word in ['excited', 'amazing', 'awesome', 'great']):
        context['emotion'] = 'excited'
    elif any(word in input_lower for word in ['curious', 'wonder', 'what', 'how', 'why']):
        context['emotion'] = 'curious'
    elif any(word in input_lower for word in ['worried', 'concerned', 'problem']):
        context['emotion'] = 'concerned'
    
    # Detect participants
    if any(name in input_lower for name in ['josh', 'brochacho']):
        context['participants'].append('josh')
    if 'reneille' in input_lower:
        context['participants'].append('reneille')
    
    return context

def main():
    """Main adaptive sass chat loop"""
    print("🧠 Adaptive Sass Memory Chat Interface")
    print("="*70)
    
    # Initialize adaptive sass-enhanced personality system
    print("🧠 Initializing adaptive sass-enhanced personality system...")
    try:
        penny = create_adaptive_sass_enhanced_penny()
        print("✅ Adaptive sass-enhanced Penny initialized successfully")
    except Exception as e:
        print(f"❌ Error initializing adaptive sass-enhanced Penny: {e}")
        import traceback
        traceback.print_exc()
        print("Press Enter to exit...")
        input()
        return
    
    # Start conversation session
    session_id = penny.start_conversation_session("adaptive_text")
    
    print("\n🎯 Adaptive Features Active:")
    print("   • Persistent memory across conversations")
    print("   • Cross-session relationship building")
    print("   • Adaptive sass learning (Penny learns your preferences!)")
    print("   • User-controllable sass levels with learning integration")
    print("   • Dynamic personality states with memory context")
    print("   • Machine learning adaptation from interactions")
    print("   • Context-aware response generation")
    print("   • Inside jokes and preference tracking")
    print("   • Conversational pragmatics and role detection")
    
    # Show what Penny remembers
    relationship_summary = penny.get_relationship_summary()
    if "still getting to know" not in relationship_summary:
        print(f"\n🤝 What I remember: {relationship_summary}")
    else:
        print("\n🌱 This is a fresh start - I'm ready to learn about you!")
    
    # Test greeting with adaptive sass
    print("\n🔊 Testing adaptive sass-enhanced personality system...")
    try:
        test_context = {'topic': 'conversation', 'emotion': 'neutral', 'participants': []}
        greeting = penny.generate_adaptive_sass_response(
            "Hi Penny, I'm back!", test_context
        )
        current_sass = penny.sass_controller.current_level.value
        learned_info = penny._get_learned_sass_info()
        print(f"🤖 Penny [{current_sass}]: {greeting}")
        print(f"💡 {learned_info}")
        print("✅ Adaptive sass-enhanced personality system test successful!")
    except Exception as e:
        print(f"❌ Greeting test failed: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n💬 Adaptive Sass Memory Chat Ready! Commands:")
    print("   • 'memory stats' - Show what I remember about you")
    print("   • 'search memories [term]' - Search my memories")
    print("   • 'remember [fact]' - Manually add something to my memory")
    print("   • 'sass level' - Show current sass setting & learned preferences")
    print("   • 'set sass to [level]' - Change sass (I'll learn from this!)")
    print("   • 'tone it down' or 'be more sassy' - Natural sass control")
    print("   • 'sass insights' - See what I've learned about your preferences")
    print("   • 'sass options' - List all sass levels")
    print("   • 'quit', 'exit', or Ctrl+C to end")
    print("-" * 70)
    
    conversation_count = 0
    
    try:
        while True:
            user_input = input("📝 You: ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() in ['quit', 'exit', 'bye']:
                break
            
            conversation_count += 1
            
            # Special memory commands
            if user_input.lower() == 'memory stats':
                try:
                    stats = penny.memory.get_memory_stats()
                    summary = penny.get_relationship_summary()
                    print(f"🧠 Memory Stats: {dict(stats)}")
                    print(f"🤝 Relationship: {summary}")
                    continue
                except Exception as e:
                    print(f"❌ Memory stats error: {e}")
                    continue
            
            elif user_input.lower().startswith('search memories '):
                try:
                    search_term = user_input[15:].strip()
                    results = penny.memory.search_memories(search_term)
                    if results:
                        print(f"🔍 Found {len(results)} memories about '{search_term}':")
                        for memory in results[:5]:  # Show top 5
                            print(f"   • {memory.key}: {memory.value}")
                    else:
                        print(f"🤷 No memories found about '{search_term}'")
                    continue
                except Exception as e:
                    print(f"❌ Memory search error: {e}")
                    continue
            
            elif user_input.lower().startswith('remember '):
                try:
                    fact = user_input[9:].strip()
                    penny.manually_store_memory("user_fact", "manual_memory", fact)
                    print(f"💾 Stored: {fact}")
                    continue
                except Exception as e:
                    print(f"❌ Memory storage error: {e}")
                    continue
            
            # Generate response with adaptive sass
            try:
                with time_operation(OperationType.LLM):
                    # Enhanced context detection
                    context = detect_context(user_input)
                    
                    # Generate adaptive sass-aware response (learns from usage!)
                    enhanced_response = penny.generate_adaptive_sass_response(
                        user_input, context
                    )
                
                print(f"🤖 Penny: {enhanced_response}")
                
                # Show adaptive learning indicator
                print(f"🧠 I'm learning from our conversation... ({conversation_count} exchanges so far)")
                
            except Exception as e:
                print(f"❌ Response generation failed: {e}")
                print("😅 Sorry, I had a technical hiccup. Try again?")
                import traceback
                traceback.print_exc()

    except KeyboardInterrupt:
        print("\n👋 Adaptive Sass Memory Chat session complete!")
    
    # End session with comprehensive summary
    try:
        penny.end_conversation_session("Adaptive sass chat session completed")
        
        print("\n📊 Session Summary:")
        status = penny.get_comprehensive_adaptive_status()
        print(f"   💬 Exchanges: {conversation_count}")
        print(f"   🧠 Memory items: {sum(status['memory_stats'].values())}")
        print(f"   🎭 Current sass: {status['sass_level']} - {status['sass_description']}")
        print(f"   📈 Sass adjustments learned: {status['adaptive_learning']['total_adjustments']}")
        print(f"   🎯 Learned patterns: {status['adaptive_learning']['learned_patterns']}")
        
        if status['adaptive_learning']['context_preferences']:
            print("   🔍 Your sass preferences:")
            for context, pref in list(status['adaptive_learning']['context_preferences'].items())[:3]:
                print(f"     • {context}: {pref['preferred_sass']} sass")
        
        relationship_summary = penny.get_relationship_summary()
        print(f"   🤝 What I learned: {relationship_summary[:100]}...")
        
        print("\n💾 All memories and learning patterns saved for next time!")
        
    except Exception as e:
        print(f"⚠️ Session summary error: {e}")

if __name__ == "__main__":
    main()
