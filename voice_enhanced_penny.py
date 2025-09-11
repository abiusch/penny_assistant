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
    
    # Initialize voice activity detection
    voice_detector = create_voice_detector(
        silence_threshold=0.015,  # Slightly higher threshold for better detection
        silence_duration=1.8,     # Wait 1.8 seconds of silence before processing
        max_recording_time=30.0   # Max 30 seconds per turn
    )

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
        print("\n🎤 Ready to listen... (speak naturally, I'll respond when you pause)")
        
        # Record audio using voice activity detection
        with time_operation(OperationType.STT):
            audio_data = voice_detector.record_until_silence(device=1)
        
        if len(audio_data) == 0:
            print("🤷 No audio detected. Try speaking a bit louder.")
            return
        
        # Show recording stats
        stats = voice_detector.get_recording_stats()
        print(f"📊 Recorded {stats.get('duration_seconds', 0):.1f}s (max vol: {stats.get('max_volume', 0):.3f})")
        
        # Transcribe
        text = transcribe_audio(audio_data)

        if not text or not isinstance(text, str) or not text.strip():
            print("🤷 Heard nothing. Try again.")
            return

        print(f"🗣️ You said: {text}")
        
        # Generate enhanced response
        try:
            with time_operation(OperationType.LLM):
                # Get enhanced personality prompt with current state
                context = {
                    'topic': 'conversation',
                    'emotion': 'neutral',
                    'participants': []
                }
                
                # Detect context from user input
                text_lower = text.lower()
                if any(name in text_lower for name in ['josh', 'brochacho']):
                    context['participants'].append('josh')
                if 'reneille' in text_lower:
                    context['participants'].append('reneille')
                
                # Detect emotion
                if any(word in text_lower for word in ['frustrated', 'annoyed', 'angry']):
                    context['emotion'] = 'frustrated'
                elif any(word in text_lower for word in ['excited', 'awesome', 'amazing']):
                    context['emotion'] = 'excited'
                
                # Detect topics
                if any(word in text_lower for word in ['microservice', 'architecture']):
                    context['topic'] = 'architecture'
                elif any(word in text_lower for word in ['debug', 'error', 'broken']):
                    context['topic'] = 'debugging'
                elif any(word in text_lower for word in ['fastapi', 'python', 'code']):
                    context['topic'] = 'programming'
                
                # Get enhanced personality prompt
                personality_prompt = enhanced_penny.get_enhanced_personality_prompt(context)
                
                # Build complete prompt
                full_prompt = f"""{personality_prompt}

User: {text}

Respond as Penny with your enhanced revolutionary personality:"""
                
                # Apply enhanced pragmatic personality processing
                enhanced_response = enhanced_penny.generate_pragmatically_aware_response(
                    text, context
                )
            
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
    print("   • Voice activity detection (responds when you pause)")
    print("\nPress Enter to start conversation, Ctrl+C to exit")
    print("Tip: Speak naturally - Penny will respond when you finish talking")
    
    # Test with enhanced greeting
    print("\n🔊 Testing enhanced personality system...")
    try:
        greeting_context = {'topic': 'greeting', 'emotion': 'excited'}
        greeting_prompt = enhanced_penny.get_enhanced_personality_prompt(greeting_context)
        
        # Generate enhanced greeting
        test_greeting = enhanced_penny.generate_pragmatically_aware_response(
            "Hello Penny!",
            {'topic': 'greeting', 'emotion': 'excited'}
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
