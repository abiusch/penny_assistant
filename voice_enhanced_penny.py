#!/usr/bin/env python3
"""
Voice-Enabled Enhanced Penny
Revolutionary personality system with actual voice interactions
"""

import sounddevice as sd
import json
import sys
import os
import time
import numpy as np

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from memory_enhanced_penny import create_memory_enhanced_penny
from voice_activity_detector import create_voice_detector
from performance_monitor import time_operation, OperationType, get_performance_summary

def main():
    print("🎤 Voice-Enabled Enhanced Penny - Revolutionary Personality!")
    print("=" * 60)
    
    # Check API key
    api_key = os.getenv("ELEVENLABS_API_KEY")
    if not api_key:
        print("❌ ELEVENLABS_API_KEY not set!")
        return
    else:
        print(f"🔑 ElevenLabs API Key configured")

    try:
        from stt_engine import transcribe_audio
        from core.llm_router import get_llm
        from adapters.tts.tts_factory import create_tts_adapter, get_tts_info
        print("✅ Voice components imported successfully")
    except Exception as e:
        print(f"❌ Voice component import failed: {e}")
        return

    # Load configuration
    try:
        with open('penny_config.json', 'r') as f:
            config = json.load(f)
        print("✅ Config loaded")
    except Exception as e:
        print(f"❌ Config load failed: {e}")
        return

    # Set microphone to MacBook (now working)
    sd.default.device = 1  # MacBook Pro Microphone

    # Initialize memory-enhanced personality system
    print("🧠 Initializing Memory-Enhanced Revolutionary Personality System...")
    try:
        enhanced_penny = create_memory_enhanced_penny()
        
        # Start voice conversation session
        session_id = enhanced_penny.start_conversation_session("voice")
        print(f"   📝 Started voice session: {session_id}")
        
        # Check what we remember about the user
        relationship_summary = enhanced_penny.get_relationship_summary()
        if "still getting to know" not in relationship_summary:
            print(f"   🤝 Memory: {relationship_summary[:100]}...")
        else:
            print("   🌱 Fresh start - ready to learn about you!")
        
        llm = get_llm()
        
        # TTS with enhanced personality
        tts_info = get_tts_info(config)
        print(f"   Voice: {tts_info['will_use']} (Rachel)")
        tts = create_tts_adapter(config)
        
        print("   ✅ Memory-enhanced personality system ready!")
        print("   🧠 Cross-session memory active!")
        print("   🎭 Dynamic states + ML learning active!")
        print("   ⚡ Production-ready optimizations enabled!")
        
    except Exception as e:
        print(f"   ❌ Enhanced system initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return

    def capture_and_respond():
        print("\n🎤 Ready to speak (6-second recording)")
        
        # Simple timed recording that actually works
        with time_operation(OperationType.STT):
            print("🔴 Recording...")
            audio_data = sd.rec(int(6 * 16000), samplerate=16000, channels=1, device=1)
            sd.wait()
            print("⏹️ Recording complete")
        
        if len(audio_data) == 0:
            print("🤷 No audio recorded.")
            return
        
        # Show basic stats
        max_vol = np.max(np.abs(audio_data))
        print(f"📊 Recorded 6.0s (max vol: {max_vol:.3f})")
        
        # Transcribe
        text = transcribe_audio(audio_data)

        if not text or not isinstance(text, str) or not text.strip():
            print("🤷 Heard nothing. Try again.")
            return

        print(f"🗣️ You said: {text}")
        
        # Generate enhanced response
        try:
            with time_operation(OperationType.LLM):
                # Enhanced context detection with memory awareness
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
                
                # Generate memory-aware response instead of basic pragmatic response
                enhanced_response = enhanced_penny.generate_memory_aware_response(
                    text, context
                )
                
                print(f"DEBUG: Generated response before cleanup: '{enhanced_response[:100]}...'")
            
            print(f"🤖 Penny: {enhanced_response}")
            
        except Exception as e:
            print(f"❌ Enhanced response generation failed: {e}")
            enhanced_response = "Sorry, I'm having trouble with my enhanced personality right now. Try again?"
        
        # Speak with enhanced personality timing
        print("🔊 Speaking with enhanced personality...")
        try:
            with time_operation(OperationType.TTS):
                success = tts.speak(enhanced_response)
            
            if success:
                print("✅ Speech successful")
            else:
                print("❌ Speech failed")
        except Exception as e:
            print(f"❌ Speech error: {e}")
        
        # Enhanced learning from voice interaction
        try:
            # The memory system automatically learns from the conversation
            # No need for separate learning call - it's integrated into generate_memory_aware_response
            pass
        except Exception as e:
            print(f"⚠️ Memory learning failed: {e}")
        
        # Show performance stats
        perf_summary = get_performance_summary()
        if perf_summary.get('total_operations', 0) > 0:
            print(f"📊 Performance: {perf_summary.get('averages_ms', {})}")

    print("🎭 Memory-Enhanced Revolutionary Personality System Ready!")
    print("🎯 Features Active:")
    print("   • Persistent memory across voice conversations")
    print("   • Cross-session relationship building")
    print("   • Dynamic personality states with memory context")
    print("   • Machine learning adaptation from interactions")
    print("   • Context-aware response generation with memory")
    print("   • Relationship awareness (Josh, Reneille) with facts")
    print("   • Automatic fact extraction and storage")
    print("   • Conversational pragmatics with memory integration")
    print("   • Production-ready optimizations")
    print("\nPress Enter to start talking (6-second recordings), Ctrl+C to exit")
    
    # Test with memory-enhanced greeting
    print("\n🔊 Testing memory-enhanced personality system...")
    try:
        greeting_context = {'topic': 'greeting', 'emotion': 'neutral'}
        
        # Generate memory-aware greeting instead of basic pragmatic greeting
        test_greeting = enhanced_penny.generate_memory_aware_response(
            "Hi Penny, I'm back!",
            greeting_context
        )
        
        print(f"🤖 Memory-Enhanced Greeting: {test_greeting}")
        success = tts.speak(test_greeting)
        
        if success:
            print("✅ Memory-enhanced personality system test successful!")
        else:
            print("❌ TTS test failed")
            
    except Exception as e:
        print(f"❌ Memory-enhanced system test error: {e}")
    
    try:
        while True:
            input("\nPress Enter to start talking: ")
            capture_and_respond()
    except KeyboardInterrupt:
        print("\n👋 Memory-Enhanced Penny session complete!")
        
        # End conversation session with summary
        try:
            enhanced_penny.end_conversation_session("Voice conversation completed")
            print("💾 Conversation memories saved!")
        except Exception as e:
            print(f"⚠️ Session cleanup error: {e}")
        
        # Show final stats
        try:
            print(f"📊 Final Session Stats:")
            relationship_summary = enhanced_penny.get_relationship_summary()
            print(f"   🤝 What I learned: {relationship_summary[:100]}...")
            
            # Show memory stats
            memory_stats = enhanced_penny.memory.get_memory_stats()
            total_memories = sum(memory_stats.values())
            print(f"   🧠 Total memories stored: {total_memories}")
            
        except Exception as e:
            print(f"   ⚠️ Stats error: {e}")
        
        try:
            tts.stop()
        except:
            pass

if __name__ == '__main__':
    main()
