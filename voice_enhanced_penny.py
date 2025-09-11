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

from pragmatics_enhanced_penny import create_pragmatics_enhanced_penny
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

    # Initialize enhanced personality system
    print("🧠 Initializing Enhanced Revolutionary Personality System...")
    try:
        enhanced_penny = create_pragmatics_enhanced_penny()
        llm = get_llm()
        
        # TTS with enhanced personality
        tts_info = get_tts_info(config)
        print(f"   Voice: {tts_info['will_use']} (Rachel)")
        tts = create_tts_adapter(config)
        
        print("   ✅ Enhanced personality system ready!")
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
                # Context detection
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
                
                # Get enhanced personality prompt with current state
                personality_prompt = enhanced_penny.get_enhanced_personality_prompt(context)
                
                # Apply enhanced pragmatic personality processing
                enhanced_response = enhanced_penny.generate_pragmatically_aware_response(
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
        
        # Learn from this interaction (simulated feedback for now)
        try:
            # In real usage, you'd get actual user feedback
            # For now, simulate neutral feedback
            enhanced_penny.learn_from_pragmatic_interaction(
                text, enhanced_response, None, context
            )
        except Exception as e:
            print(f"⚠️ Learning failed: {e}")
        
        # Show performance stats
        perf_summary = get_performance_summary()
        if perf_summary.get('total_operations', 0) > 0:
            print(f"📊 Performance: {perf_summary.get('averages_ms', {})}")

    print("🎭 Enhanced Revolutionary Personality System Ready!")
    print("🎯 Features Active:")
    print("   • Dynamic personality states with contextual transitions")
    print("   • Machine learning adaptation from interactions")
    print("   • Blended ML + state personality configuration")
    print("   • Context-aware response generation")
    print("   • Relationship awareness (Josh, Reneille)")
    print("   • Performance monitoring and optimization")
    print("   • Complete graceful degradation")
    print("   • Conversational pragmatics (ask me anything detection)")
    print("\nPress Enter to start talking (6-second recordings), Ctrl+C to exit")
    
    # Test with enhanced greeting
    print("\n🔊 Testing enhanced personality system...")
    try:
        greeting_context = {'topic': 'greeting', 'emotion': 'neutral'}  # Changed from 'excited'
        greeting_prompt = enhanced_penny.get_enhanced_personality_prompt(greeting_context)
        
        # Generate enhanced greeting
        test_greeting = enhanced_penny.generate_pragmatically_aware_response(
            "Hello Penny!",
            {'topic': 'greeting', 'emotion': 'neutral'}  # Changed from 'excited'
        )
        
        print(f"🤖 Enhanced Greeting: {test_greeting}")
        success = tts.speak(test_greeting)
        
        if success:
            print("✅ Enhanced personality system test successful!")
        else:
            print("❌ TTS test failed")
            
    except Exception as e:
        print(f"❌ Enhanced system test error: {e}")
    
    try:
        while True:
            input("\nPress Enter to start talking: ")
            capture_and_respond()
    except KeyboardInterrupt:
        print("\n👋 Enhanced Penny session complete!")
        
        # Show final stats
        try:
            final_stats = enhanced_penny.get_comprehensive_stats()
            print(f"📊 Final System Stats:")
            if 'ml_current_humor_level' in final_stats:
                print(f"   ML Humor Level: {final_stats['ml_current_humor_level']}")
            if 'ml_current_sass_level' in final_stats:
                print(f"   ML Sass Level: {final_stats['ml_current_sass_level']}")
            if 'state_current_state' in final_stats:
                print(f"   Current State: {final_stats['state_current_state']}")
            if 'ml_interaction_count' in final_stats:
                print(f"   Learning Interactions: {final_stats['ml_interaction_count']}")
        except:
            pass
        
        try:
            tts.stop()
        except:
            pass

if __name__ == '__main__':
    main()
