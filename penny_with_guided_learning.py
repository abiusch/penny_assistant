#!/usr/bin/env python3
"""
Enhanced Penny Assistant with Guided Learning & Reasoning
Demonstrates proactive curiosity and learning capabilities
"""

import sounddevice as sd
import json
import sys
import os
import time

from voice_entry import respond as voice_respond

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def main():
    print("🧠 Starting PennyGPT with Guided Learning & Reasoning!")
    print("🎯 New Features: Proactive curiosity, learning from corrections, research requests")
    
    # Debug: Check API key first
    api_key = os.getenv("ELEVENLABS_API_KEY")
    if not api_key:
        print("❌ ELEVENLABS_API_KEY not set!")
        print("   Run: export ELEVENLABS_API_KEY='your_actual_key'")
        print("   Get your key from: https://elevenlabs.io")
        return
    else:
        print(f"🔑 API Key: {api_key[:8]}...{api_key[-4:]}")

    try:
        from stt_engine import transcribe_audio
        from core.llm_router import get_llm
        from adapters.tts.tts_factory import create_tts_adapter, get_tts_info
        from memory_system import MemoryManager
        from src.core.learning_enhanced_pipeline import create_learning_enhanced_pipeline
        print("✅ Imports successful")
    except Exception as e:
        print(f"❌ Import failed: {e}")
        import traceback
        traceback.print_exc()
        return

    # Load configuration
    try:
        with open('penny_config.json', 'r') as f:
            config = json.load(f)
        print("✅ Config loaded")
        
        # Load personality profile if specified
        if 'personality' in config and 'profile_path' in config['personality']:
            personality_path = config['personality']['profile_path']
            try:
                with open(personality_path, 'r') as f:
                    personality_config = json.load(f)
                print(f"✅ Personality profile loaded: {personality_config.get('name', 'Unknown')} v{personality_config.get('version', '1.0')}")
                
                # Validate schema version
                schema_version = personality_config.get('schema_version', '0.0.0')
                if schema_version.startswith('1.'):
                    print(f"✅ Compatible schema version: {schema_version}")
                else:
                    print(f"⚠️ Warning: Personality schema version {schema_version} may not be compatible")
                    
            except Exception as e:
                print(f"⚠️ Warning: Could not load personality profile: {e}")
                print("   Continuing with default personality settings")
                
    except Exception as e:
        print(f"❌ Config load failed: {e}")
        return

    # Set the correct microphone
    sd.default.device = 1  # MacBook Pro Microphone

    # Initialize systems
    print("🧠 Initializing Enhanced AI Systems...")
    try:
        # Initialize memory manager
        memory_manager = MemoryManager()
        
        # Initialize LLM
        llm = get_llm()
        
        # Initialize TTS with factory
        tts_info = get_tts_info(config)
        print(f"   Voice type: {tts_info['will_use']}")
        print(f"   Personality aware: {tts_info['personality_aware']}")
        tts = create_tts_adapter(config)
        
        # Create learning-enhanced pipeline
        pipeline = create_learning_enhanced_pipeline(
            None,  # STT engine (direct input for this demo)
            llm,
            tts,
            memory_manager
        )
        
        print("   ✅ Guided Learning System initialized!")
        print("   🧠 Emotional Memory System active!")
        print("   🎭 Unpredictable Personality System active!")
        print("   🔍 Research & Curiosity System active!")
        
    except Exception as e:
        print(f"   ❌ System initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return

    def capture_and_handle():
        print("\n🎤 Listening for 5 seconds...")
        audio_data = sd.rec(int(5 * 16000), samplerate=16000, channels=1)
        sd.wait()

        text = transcribe_audio(audio_data)

        if not text or not isinstance(text, str) or not text.strip():
            print("🤷 Heard nothing. Try again.")
            return

        print(f"🗣️ You said: {text}")
        
        # Process through enhanced pipeline with guided learning
        try:
            start_time = time.time()
            def generator(system_prompt: str, user_text: str) -> str:
                del system_prompt
                return pipeline.think(user_text)

            enhanced_response = voice_respond(text, generator=generator)
            process_time = (time.time() - start_time) * 1000
            
            print(f"🤖 Penny: {enhanced_response}")
            print(f"⚡ Processing time: {process_time:.0f}ms")
            
            # Show learning stats
            try:
                learning_stats = pipeline.get_learning_stats()
                if learning_stats['research_requests_week'] > 0 or learning_stats['corrections_week'] > 0:
                    print(f"📊 Learning: {learning_stats['research_requests_week']} research requests, {learning_stats['corrections_week']} corrections this week")
            except:
                pass  # Stats not available yet
                
        except Exception as e:
            print(f"❌ Processing failed: {e}")
            enhanced_response = "Sorry, I'm having trouble processing that right now."
        
        # Speak the response with personality-aware voice
        print("🔊 Speaking with natural voice...")
        try:
            # Detect personality from user input for voice adaptation
            user_personality = 'default'
            if hasattr(tts, '_detect_personality_mode'):
                user_personality = tts._detect_personality_mode(text)
                if user_personality != 'default':
                    print(f"[Penny Voice] Detected {user_personality} mode from user input")
            
            # Override TTS personality detection to use user input
            if hasattr(tts, '_detect_personality_mode'):
                original_detect = tts._detect_personality_mode
                tts._detect_personality_mode = lambda _: user_personality
            
            success = tts.speak(enhanced_response)
            
            # Restore original function
            if hasattr(tts, '_detect_personality_mode'):
                tts._detect_personality_mode = original_detect
            
            if success:
                # Show performance metrics after successful speech
                if hasattr(tts, 'get_metrics'):
                    metrics = tts.get_metrics()
                    print(f"📊 Performance: {metrics['cache_hits']} cache hits, {metrics['avg_synthesis_ms']}ms avg synthesis")
            else:
                print("❌ Speech failed")
        except Exception as e:
            print(f"❌ Speech error: {e}")

    print("🎭 Voice: Rachel (ElevenLabs) with Personality Awareness")
    print("🎤 Audio: MacBook Pro Microphone")
    print("🧠 New: Guided Learning & Reasoning System")
    print("\n🎯 New Capabilities:")
    print("   • Ask 'Can you research X for me?' to trigger research requests")
    print("   • Express curiosity like 'I wonder how X works' for exploration")
    print("   • Correct Penny when she's wrong - she'll learn from it!")
    print("   • Say 'I don't understand X' for targeted help")
    print("\nPress Enter to speak, Ctrl+C to exit\n")
    
    # Test the voice and learning system on startup
    print("🔊 Testing enhanced systems...")
    try:
        test_response = "Hey there! I'm Penny with my new guided learning system. I'm not just reactive anymore - I'm genuinely curious and I learn from our conversations. Want to explore something together?"
        success = tts.speak(test_response)
        if success:
            print("✅ Enhanced system test successful!")
            # Show initial metrics
            if hasattr(tts, 'get_metrics'):
                metrics = tts.get_metrics()
                print(f"📊 TTS Metrics: {metrics['cache_hits']} cache hits, {metrics['avg_synthesis_ms']}ms avg synthesis")
        else:
            print("❌ Enhanced system test failed")
    except Exception as e:
        print(f"❌ Enhanced system test error: {e}")
    
    try:
        while True:
            input("\nPress Enter to start recording: ")
            capture_and_handle()
    except KeyboardInterrupt:
        print("\n👋 Exiting Enhanced PennyGPT...")
        print("Thanks for testing the guided learning system!")
        
        # Show final learning stats
        try:
            learning_stats = pipeline.get_learning_stats()
            print(f"\n📊 Session Learning Summary:")
            print(f"   🔬 Research requests: {learning_stats['research_requests_week']}")
            print(f"   ✏️ Corrections learned: {learning_stats['corrections_week']}")
            print(f"   🎯 Active learning goals: {learning_stats['active_learning_goals']}")
            if learning_stats['permission_rate'] > 0:
                print(f"   ✅ Research permission rate: {learning_stats['permission_rate']:.1%}")
        except:
            pass
            
        try:
            tts.stop()  # Stop any ongoing speech
        except:
            pass

if __name__ == '__main__':
    main()
