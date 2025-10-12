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
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from speed_optimized_enhanced_penny import create_speed_optimized_enhanced_penny
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

    # Set microphone
    sd.default.device = [1, 2]  # Input device 1, output device 2

    # Initialize enhanced personality system
    print("🧠 Initializing Enhanced Revolutionary Personality System...")
    try:
        enhanced_penny = create_speed_optimized_enhanced_penny()
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
        import threading
        import numpy as np
        import queue

        print("\n🎤 Recording... (press Enter to stop)")

        # Queue for continuous audio capture (no fragmentation)
        audio_queue = queue.Queue()
        recording = True

        def audio_callback(indata, frames, time_info, status):
            """Called automatically by sounddevice for each audio block"""
            if recording:
                if status.input_overflow:
                    print("⚠️  Audio buffer overflow - may cause gaps")
                audio_queue.put(indata.copy())

        def wait_for_enter():
            """Wait for Enter key in separate thread"""
            nonlocal recording
            input()
            recording = False

        # Start Enter-waiting thread
        enter_thread = threading.Thread(target=wait_for_enter, daemon=True)
        enter_thread.start()

        # Start continuous background recording (no chunking = no gaps)
        try:
            with time_operation(OperationType.STT):
                with sd.InputStream(
                    samplerate=16000,
                    channels=1,
                    dtype='float32',
                    callback=audio_callback,
                    blocksize=8192
                ):
                    # Recording happens in background via callback
                    enter_thread.join()  # Wait until Enter pressed
        except Exception as e:
            print(f"❌ Recording error: {e}")
            return

        print("⏹️  Stopping recording...")

        # Collect all captured audio chunks (captured continuously, no gaps)
        audio_chunks = []
        while not audio_queue.empty():
            audio_chunks.append(audio_queue.get())

        if not audio_chunks:
            print("🤷 No audio captured")
            return

        # Concatenate chunks (these were captured continuously by callback)
        audio_data = np.concatenate(audio_chunks, axis=0)

        # Validate audio quality
        audio_max = np.abs(audio_data).max()
        audio_mean = np.abs(audio_data).mean()
        print(f"[STT Debug] Audio volume: {audio_mean:.6f}, max: {audio_max:.4f}")

        if audio_max < 0.0005:
            print("🤷 Audio too quiet - speak louder or closer to mic")
            return

        # Transcribe
        text = transcribe_audio(audio_data)

        if not text or not isinstance(text, str) or not text.strip():
            print("🤷 Heard nothing. Try again.")
            return

        # Validate transcription quality
        def validate_transcription(text):
            """Check if transcription seems coherent"""
            issues = []
            words = text.split()

            # Too short and fragmented
            if len(words) < 5 and text.count(',') > 2:
                issues.append("fragmented")

            # No clear question or statement structure
            if len(words) > 3:
                has_question_word = any(w in text.lower() for w in
                    ['what', 'how', 'why', 'when', 'where', 'who', 'can', 'could', 'would', 'should', 'do', 'does', 'is', 'are'])
                has_statement = any(w in text.lower() for w in
                    ['i', 'you', 'we', 'they', 'this', 'that', 'have', 'has', 'want', 'need', 'think'])

                if not has_question_word and not has_statement and len(words) < 10:
                    issues.append("unclear_structure")

            # Lots of sentence fragments
            sentences = [s.strip() for s in text.split('.') if s.strip()]
            short_fragments = [s for s in sentences if len(s.split()) < 3]
            if len(sentences) > 1 and len(short_fragments) > len(sentences) / 2:
                issues.append("too_many_fragments")

            return len(issues) == 0, issues

        is_valid, issues = validate_transcription(text)
        if not is_valid:
            print(f"⚠️ Transcription unclear (issues: {', '.join(issues)})")
            tts.speak("Sorry, I didn't catch that clearly. Could you say that again?")
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
                
                # Generate base response from LLM
                base_response = llm.generate(full_prompt)
                
                # Apply enhanced personality processing
                enhanced_response = enhanced_penny.generate_enhanced_response_safe(
                    text, base_response, context
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
            enhanced_penny.learn_from_interaction_enhanced(
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
    print("\nPress Enter to speak, Ctrl+C to exit")
    
    # Test with enhanced greeting
    print("\n🔊 Testing enhanced personality system...")
    try:
        greeting_context = {'topic': 'greeting', 'emotion': 'excited'}
        greeting_prompt = enhanced_penny.get_enhanced_personality_prompt(greeting_context)
        
        # Generate enhanced greeting
        test_greeting = enhanced_penny.generate_enhanced_response_safe(
            "Hello Penny!",
            "Hey! I'm ready with my enhanced revolutionary personality system!",
            greeting_context
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
            input("\nPress Enter to start recording: ")
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
