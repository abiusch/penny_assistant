#!/usr/bin/env python3
"""
Adaptive Sass Voice Interface
Voice interface with adaptive sass learning - unified memory across voice + text
"""

import sounddevice as sd
import json
import sys
import os
import time
import numpy as np

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from adaptive_sass_enhanced_penny import create_adaptive_sass_enhanced_penny
from performance_monitor import time_operation, OperationType, get_performance_summary

def detect_context(user_input: str) -> dict:
    """Detect conversation context for adaptive sass"""
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
    
    # Detect participants
    if any(name in input_lower for name in ['josh', 'brochacho']):
        context['participants'].append('josh')
    if 'reneille' in input_lower:
        context['participants'].append('reneille')
    
    return context

def main():
    print("🎤 Adaptive Sass Voice Interface - Memory + Learning Across Voice & Text!")
    print("=" * 70)
    
    # Check speech recognition availability
    try:
        import speech_recognition as sr
        print("✅ Speech Recognition available")
    except ImportError:
        print("❌ Speech Recognition not available")
        print("💡 Install with: pip install speechrecognition")
        print("📝 For now, you can use: python3 adaptive_sass_chat.py")
        return
    
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

    # Set microphone to MacBook (based on your previous tests)
    sd.default.device = 1  # MacBook Pro Microphone

    # Initialize adaptive sass-enhanced personality system
    print("🧠 Initializing Adaptive Sass-Enhanced Voice System...")
    try:
        penny = create_adaptive_sass_enhanced_penny()
        
        # Start voice conversation session
        session_id = penny.start_conversation_session("adaptive_voice")
        print(f"   📝 Started adaptive voice session: {session_id}")
        
        # Check what we remember
        relationship_summary = penny.get_relationship_summary()
        if "still getting to know" not in relationship_summary:
            print(f"   🤝 Memory: {relationship_summary[:60]}...")
        else:
            print("   🌱 Fresh start - ready to learn about you!")
        
        # TTS setup
        tts_info = get_tts_info(config)
        print(f"   🔊 Voice: {tts_info['will_use']} (Rachel)")
        tts = create_tts_adapter(config)
        
        print("   ✅ Adaptive sass voice system ready!")
        print("   🧠 Cross-session memory + adaptive sass learning active!")
        
    except Exception as e:
        print(f"   ❌ System initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return

    def capture_and_respond():
        print("\n🎤 Listening for 4 seconds...")
        
        # Record audio
        with time_operation(OperationType.STT):
            audio_data = sd.rec(int(4 * 16000), samplerate=16000, channels=1, device=1)
            sd.wait()
            print("⏹️ Recording complete")

        # Show basic stats
        max_vol = np.max(np.abs(audio_data))
        print(f"📊 Audio captured (max vol: {max_vol:.3f})")

        # Transcribe
        text = transcribe_audio(audio_data)

        if not text or not isinstance(text, str) or not text.strip():
            print("🤷 Heard nothing. Try again.")
            return

        print(f"🗣️ You said: {text}")
        
        # Generate adaptive sass response
        try:
            with time_operation(OperationType.LLM):
                # Enhanced context detection for voice
                context = detect_context(text)
                
                # Generate adaptive sass-aware response
                enhanced_response = penny.generate_adaptive_sass_response(
                    text, context
                )
            
            # Show current sass level and any learning
            current_sass = penny.sass_controller.current_level.value
            learned_info = penny._get_learned_sass_info()
            print(f"🤖 Penny [{current_sass}]: {enhanced_response}")
            if "learned preference" in learned_info:
                print(f"💡 {learned_info}")
            
        except Exception as e:
            print(f"❌ Response generation failed: {e}")
            enhanced_response = "Sorry, I'm having trouble with my adaptive system right now. Try again?"
        
        # Speak with adaptive personality
        print("🔊 Speaking...")
        try:
            with time_operation(OperationType.TTS):
                success = tts.speak(enhanced_response)
            
            if success:
                print("✅ Speech successful")
            else:
                print("❌ Speech failed")
        except Exception as e:
            print(f"❌ Speech error: {e}")
        
        # Show performance stats
        perf_summary = get_performance_summary()
        if perf_summary.get('total_operations', 0) > 0:
            total_ms = sum(perf_summary.get('averages_ms', {}).values())
            print(f"⚡ Total response time: {total_ms:.0f}ms")

    print("\n🎯 Adaptive Voice Features Active:")
    print("   • Cross-session memory (shared with text interface)")
    print("   • Adaptive sass learning from voice commands")
    print("   • Context-aware personality (programming vs. social)")
    print("   • Voice sass commands: 'tone it down', 'be more sassy'")
    print("   • Memory integration: remembers you between voice/text sessions")
    print("   • Learning insights: ask 'what have you learned about my sass?'")
    
    # Test adaptive greeting
    print("\n🔊 Testing adaptive voice system...")
    try:
        test_context = {'topic': 'greeting', 'emotion': 'neutral'}
        greeting = penny.generate_adaptive_sass_response(
            "Hi Penny, I'm back for voice!", test_context
        )
        current_sass = penny.sass_controller.current_level.value
        print(f"🤖 Adaptive Greeting [{current_sass}]: {greeting}")
        
        success = tts.speak(greeting)
        if success:
            print("✅ Adaptive voice system test successful!")
        else:
            print("❌ TTS test failed")
            
    except Exception as e:
        print(f"❌ Adaptive system test error: {e}")
    
    print("\n🎤 Voice Commands You Can Try:")
    print("   • 'Set sass to minimal' (learns you prefer professional voice)")
    print("   • 'Tone it down' while debugging (learns context preference)")
    print("   • 'Be more sassy' in casual chat (learns social preference)")
    print("   • 'What have you learned about my sass preferences?'")
    print("   • Any normal conversation (memory shared with text interface)")
    print("\nPress Enter to speak, Ctrl+C to exit")
    
    interaction_count = 0
    
    try:
        while True:
            input("\nPress Enter to start recording: ")
            capture_and_respond()
            interaction_count += 1
            print(f"🧠 Learning from our conversation... ({interaction_count} voice interactions)")
            
    except KeyboardInterrupt:
        print("\n👋 Adaptive Voice session complete!")
        
        # End session with comprehensive summary
        try:
            penny.end_conversation_session("Adaptive voice session completed")
            print("💾 Voice conversation memories saved!")
            
            print("\n📊 Voice Session Summary:")
            status = penny.get_comprehensive_adaptive_status()
            print(f"   🎤 Voice interactions: {interaction_count}")
            print(f"   🧠 Memory items: {sum(status['memory_stats'].values())}")
            print(f"   🎭 Current sass: {status['sass_level']} - {status['sass_description']}")
            print(f"   📈 Sass adjustments learned: {status['adaptive_learning']['total_adjustments']}")
            print(f"   🎯 Learned patterns: {status['adaptive_learning']['learned_patterns']}")
            
            if status['adaptive_learning']['context_preferences']:
                print("   🔍 Your voice sass preferences:")
                for context, pref in list(status['adaptive_learning']['context_preferences'].items())[:3]:
                    print(f"     • {context}: {pref['preferred_sass']} sass")
            
            relationship_summary = penny.get_relationship_summary()
            print(f"   🤝 What I learned: {relationship_summary[:80]}...")
            
            print("\n💾 All voice memories and learning patterns saved!")
            print("🔄 Your adaptive sass preferences are now shared across voice + text!")
            
        except Exception as e:
            print(f"⚠️ Session summary error: {e}")
        
        try:
            tts.stop()
        except:
            pass

if __name__ == '__main__':
    main()
