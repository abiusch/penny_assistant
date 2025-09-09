#!/usr/bin/env python3
"""
CJ's Personalized PennyGPT with Guided Learning
Uses CJ's specific profile and persona for truly personalized AI conversations
"""

import sounddevice as sd
import json
import sys
import os
import time

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def main():
    print("👤 Starting CJ's Personalized PennyGPT!")
    print("🎯 Features: Personal profile, guided learning, CJ-specific preferences")
    
    # Check API key
    api_key = os.getenv("ELEVENLABS_API_KEY")
    if not api_key:
        print("❌ ELEVENLABS_API_KEY not set!")
        return
    else:
        print(f"🔑 API Key configured")

    try:
        from stt_engine import transcribe_audio
        from core.llm_router import get_llm
        from adapters.tts.tts_factory import create_tts_adapter, get_tts_info
        from memory_system import MemoryManager
        from cj_enhanced_learning import create_cj_enhanced_learning_system
        from src.core.learning_enhanced_pipeline import LearningEnhancedPipeline
        print("✅ All imports successful")
    except Exception as e:
        print(f"❌ Import failed: {e}")
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
    sd.default.device = 1  # MacBook Pro Microphone

    # Initialize CJ's personalized systems
    print("🧠 Initializing CJ's Personalized AI Systems...")
    try:
        # Memory system
        memory_manager = MemoryManager()
        
        # LLM
        llm = get_llm()
        
        # TTS with CJ's voice preferences
        tts_info = get_tts_info(config)
        print(f"   Voice: {tts_info['will_use']} (Rachel - CJ's preference)")
        tts = create_tts_adapter(config)
        
        # Create CJ's enhanced learning pipeline
        class CJPersonalizedPipeline(LearningEnhancedPipeline):
            def __init__(self, stt_engine, llm, tts_adapter, memory_manager):
                super().__init__(stt_engine, llm, tts_adapter, memory_manager)
                # Replace guided learning with CJ's enhanced version
                self.guided_learning = create_cj_enhanced_learning_system(self.emotional_memory)
        
        # Initialize CJ's pipeline
        pipeline = CJPersonalizedPipeline(None, llm, tts, memory_manager)
        
        print("   ✅ CJ's Enhanced Guided Learning System active!")
        print("   🎭 Penny-Justine personality blend loaded!")
        print("   👤 CJ's personal preferences integrated!")
        
    except Exception as e:
        print(f"   ❌ System initialization failed: {e}")
        return

    def capture_and_handle():
        print("\n🎤 Listening for 5 seconds...")
        audio_data = sd.rec(int(5 * 16000), samplerate=16000, channels=1)
        sd.wait()

        text = transcribe_audio(audio_data)

        if not text or not isinstance(text, str) or not text.strip():
            print("🤷 Heard nothing. Try again.")
            return

        print(f"🗣️ CJ said: {text}")
        
        # Process through CJ's personalized pipeline
        try:
            start_time = time.time()
            response = pipeline.think(text)
            process_time = (time.time() - start_time) * 1000
            
            print(f"🤖 Penny: {response}")
            print(f"⚡ Processing time: {process_time:.0f}ms")
            
            # Show CJ-specific learning stats
            try:
                learning_stats = pipeline.get_learning_stats()
                if learning_stats['research_requests_week'] > 0:
                    print(f"📊 This week: {learning_stats['research_requests_week']} research requests, {learning_stats['corrections_week']} corrections")
            except:
                pass
                
        except Exception as e:
            print(f"❌ Processing failed: {e}")
            response = "Sorry CJ, I'm having trouble processing that right now."
        
        # Speak with CJ's preferred voice settings
        print("🔊 Speaking with CJ's preferred voice...")
        try:
            success = tts.speak(response)
            
            if success:
                # Show performance metrics
                if hasattr(tts, 'get_metrics'):
                    metrics = tts.get_metrics()
                    print(f"📊 Voice: {metrics['cache_hits']} cache hits, {metrics['avg_synthesis_ms']}ms avg synthesis")
            else:
                print("❌ Speech failed")
        except Exception as e:
            print(f"❌ Speech error: {e}")

    print("🎭 Voice: Rachel (CJ's preferred ElevenLabs voice)")
    print("🎤 Audio: MacBook Pro Microphone")
    print("👤 Profile: CJ's personal preferences active")
    print("\n🎯 Personalized Capabilities:")
    print("   • Auto-research FastAPI, Python, ElevenLabs topics")
    print("   • Concise responses with answer-first structure")
    print("   • PennyGPT project-aware suggestions")
    print("   • Tech stack-specific advice (Python, FastAPI, etc.)")
    print("   • CJ's communication style (warm, confident, little sassy)")
    print("\nPress Enter to speak, Ctrl+C to exit\n")
    
    # Test with CJ's sassy personalized greeting
    print("🔊 Testing CJ's sassy personalized system...")
    try:
        greeting = "Hey CJ! I'm Penny with your personalized setup - and yeah, I've got some actual attitude now. I know you prefer concise, no-bullshit responses, so let's skip the pleasantries and build something that doesn't suck. Ready to work on your PennyGPT empire?"
        success = tts.speak(greeting)
        if success:
            print("✅ CJ's sassy personalized system ready!")
        else:
            print("❌ System test failed")
    except Exception as e:
        print(f"❌ Test error: {e}")
    
    try:
        while True:
            input("\nPress Enter to start recording: ")
            capture_and_handle()
    except KeyboardInterrupt:
        print("\n👋 Thanks CJ! Hope the personalized experience was helpful.")
        print("Your preferences and learning history are saved for next time!")
        
        # Show session summary
        try:
            learning_stats = pipeline.get_learning_stats()
            print(f"\n📊 Session Summary:")
            print(f"   🔬 Research requests: {learning_stats['research_requests_week']}")
            print(f"   ✏️ Corrections learned: {learning_stats['corrections_week']}")
            print(f"   🎯 Active learning goals: {learning_stats['active_learning_goals']}")
            if learning_stats['permission_rate'] > 0:
                print(f"   ✅ Research permission rate: {learning_stats['permission_rate']:.1%}")
        except:
            pass
            
        try:
            tts.stop()
        except:
            pass

if __name__ == '__main__':
    main()
