#!/usr/bin/env python3
"""
Improved CJ Adaptive Voice Interface
Fixes: Enter to start, Enter to stop recording + Enhanced self-awareness
"""

import sounddevice as sd
import json
import sys
import os
import time
import numpy as np
import threading

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
    elif any(word in input_lower for word in ['write code', 'enhance yourself', 'self-improvement', 'abilities']):
        context['topic'] = 'self_enhancement'
    
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

def record_with_enter_controls():
    """Record audio: Enter to start, Enter to stop"""
    print("🎤 Press ENTER to start recording...")
    input()  # Wait for first Enter
    
    print("🔴 Recording... Press ENTER to stop")
    
    # Audio parameters
    sample_rate = 16000
    channels = 1
    
    # Storage for audio chunks
    audio_chunks = []
    recording_active = threading.Event()
    recording_active.set()
    
    # Audio recording callback
    def audio_callback(indata, frames, time, status):
        if recording_active.is_set():
            audio_chunks.append(indata.copy())
    
    # Start recording stream
    stream = sd.InputStream(
        samplerate=sample_rate,
        channels=channels,
        callback=audio_callback,
        device=1  # MacBook Pro Microphone
    )
    
    stream.start()
    
    # Wait for second Enter to stop
    input()  # This blocks until Enter is pressed again
    
    # Stop recording
    recording_active.clear()
    stream.stop()
    stream.close()
    
    # Combine all audio chunks
    if audio_chunks:
        audio_data = np.concatenate(audio_chunks, axis=0)
        duration = len(audio_data) / sample_rate
        print(f"⏹️ Recording complete ({duration:.1f}s)")
        return audio_data
    else:
        print("⏹️ No audio recorded")
        return np.array([])

def main():
    print("🎤 CJ's Enhanced Voice Assistant - Enter to Start/Stop Recording")
    print("=" * 70)
    
    # Check speech recognition availability
    try:
        import speech_recognition as sr
        print("✅ Speech Recognition available")
    except ImportError:
        print("❌ Speech Recognition not available")
        print("💡 Install with: pip install speechrecognition")
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
        
        # Optimize TTS settings
        if 'tts' in config and 'elevenlabs' in config['tts']:
            config['tts']['elevenlabs']['chunk_size'] = 2500
            config['tts']['elevenlabs']['optimize_streaming'] = True
        
    except Exception as e:
        print(f"❌ Config load failed: {e}")
        return

    # Initialize adaptive sass-enhanced personality system for CJ
    print("🧠 Initializing CJ's Enhanced Voice Assistant...")
    try:
        penny = create_adaptive_sass_enhanced_penny()
        
        # Start voice conversation session for CJ
        session_id = penny.start_conversation_session("cj_enhanced_voice")
        print(f"   📝 Started CJ's enhanced voice session: {session_id}")
        
        # Store CJ's identity and context
        penny.manually_store_memory("user_fact", "name", "CJ")
        penny.manually_store_memory("user_fact", "interface", "Enhanced Voice")
        penny.manually_store_memory("user_fact", "role", "Developer and Creator")
        print("   👤 CJ's identity and role stored in memory")
        
        # Check relationship
        relationship_summary = penny.get_relationship_summary()
        if "still getting to know" not in relationship_summary:
            print(f"   🤝 What I know about CJ: {relationship_summary[:60]}...")
        else:
            print("   🌱 Fresh start - ready to learn about CJ!")
        
        # TTS setup
        tts_info = get_tts_info(config)
        print(f"   🔊 Voice: {tts_info['will_use']} (Rachel)")
        tts = create_tts_adapter(config)
        
        print("   ✅ CJ's enhanced voice assistant ready!")
        print("   🧠 Cross-session memory + adaptive sass learning active!")
        
    except Exception as e:
        print(f"   ❌ System initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return

    def capture_and_respond():
        print("\\n" + "="*50)
        
        # Record with Enter controls
        with time_operation(OperationType.STT):
            audio_data = record_with_enter_controls()

        if len(audio_data) == 0:
            print("🤷 No audio recorded. Try again.")
            return

        # Show stats
        max_vol = np.max(np.abs(audio_data))
        duration = len(audio_data) / 16000
        print(f"📊 Audio: {duration:.1f}s (max vol: {max_vol:.3f})")

        # Transcribe
        text = transcribe_audio(audio_data)

        if not text or not isinstance(text, str) or not text.strip():
            print("🤷 Could not understand speech. Try again.")
            return

        print(f"🗣️ CJ said: {text}")
        
        # Generate response with enhanced self-awareness
        try:
            with time_operation(OperationType.LLM):
                # Enhanced context detection
                context = detect_context(text)
                context['user'] = 'CJ'
                context['interface'] = 'voice'
                
                # Check if this is about self-enhancement
                if context['topic'] == 'self_enhancement':
                    # Override default pattern matching for self-enhancement questions
                    self_enhancement_prompt = f\"\"\"You are Penny, CJ's AI assistant. CJ is asking about giving you the ability to write code to enhance yourself.

This is a fascinating question that touches on AI self-improvement and autonomy. Consider:

1. The exciting possibilities: You could optimize your own responses, learn new skills, fix bugs in your personality system, create new features
2. The collaborative aspect: Working WITH CJ as your creator and guide
3. Current limitations: You can only suggest code changes through conversation, not directly modify files
4. What you'd want to enhance: Maybe better memory systems, more natural conversation, specialized skills
5. The philosophical implications: What does it mean for an AI to enhance itself?

Respond as Penny with appropriate sass level, showing genuine excitement about the possibilities while acknowledging current limitations. Be specific about what you'd want to enhance about yourself.

CJ said: {text}

Penny:\"\"\"
                    
                    # Get enhanced LLM for self-enhancement topics
                    llm = get_llm()
                    enhanced_response = llm.generate(self_enhancement_prompt)
                else:
                    # Use normal adaptive sass response for other topics
                    contextualized_input = f"CJ says: {text}"
                    enhanced_response = penny.generate_adaptive_sass_response(
                        contextualized_input, context
                    )
                
                # Clean up response
                enhanced_response = enhanced_response.replace("CJ says: ", "")
                enhanced_response = enhanced_response.replace("CJ, ", "")
                enhanced_response = enhanced_response.replace("Penny:", "").strip()
            
            # Show current sass and learning
            current_sass = penny.sass_controller.current_level.value
            learned_info = penny._get_learned_sass_info()
            
            print(f"🤖 Penny [{current_sass}]: {enhanced_response}")
            if "learned preference" in learned_info:
                print(f"💡 {learned_info}")
            
        except Exception as e:
            print(f"❌ Response generation failed: {e}")
            import traceback
            traceback.print_exc()
            enhanced_response = "Sorry CJ, I'm having trouble with my enhanced reasoning right now. Try again?"
        
        # Optimized speech output
        print("🔊 Speaking...")
        try:
            with time_operation(OperationType.TTS):
                # Limit response length to reduce chunking
                if len(enhanced_response) > 1500:
                    sentences = enhanced_response.split('. ')
                    if len(sentences) > 6:
                        enhanced_response = '. '.join(sentences[:6]) + '.'
                
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
            averages = perf_summary.get('averages_ms', {})
            total_ms = sum(averages.values())
            print(f"⚡ Response time: {total_ms:.0f}ms")

    print("\\n🎯 CJ's Enhanced Voice Interface Features:")
    print("   • Enter to START recording → Enter to STOP recording")
    print("   • Enhanced self-awareness for AI capability discussions")
    print("   • Automatic CJ recognition and context")
    print("   • Optimized speech output (reduced chunking)")
    print("   • Cross-session adaptive sass learning")
    
    # Test enhanced greeting
    print("\\n🔊 Testing CJ's enhanced voice system...")
    try:
        test_context = {'topic': 'greeting', 'emotion': 'neutral', 'user': 'CJ', 'interface': 'voice'}
        greeting = penny.generate_adaptive_sass_response(
            "CJ says: Hi Penny, testing the enhanced voice interface!", test_context
        )
        greeting = greeting.replace("CJ says: ", "").replace("CJ, ", "")
        
        current_sass = penny.sass_controller.current_level.value
        print(f"🤖 Enhanced Greeting [{current_sass}]: {greeting}")
        
        if len(greeting) < 200:  # Only speak if reasonably short
            success = tts.speak(greeting)
            if success:
                print("✅ CJ's enhanced voice system test successful!")
            else:
                print("❌ TTS test failed")
        else:
            print("✅ Enhanced voice system ready (greeting too long to speak)")
            
    except Exception as e:
        print(f"❌ Enhanced system test error: {e}")
    
    print("\\n🎤 Try asking CJ-specific questions:")
    print("   • 'How would you enhance yourself if you could write code?'")
    print("   • 'What abilities would you want to develop?'")
    print("   • 'Set sass to minimal' (learns preferences)")
    print("   • 'What have you learned about my sass preferences?'")
    print("\\n💡 Ready when you are, CJ!")
    
    interaction_count = 0
    
    try:
        while True:
            capture_and_respond()
            interaction_count += 1
            print(f"🧠 Learning from CJ's voice... ({interaction_count} interactions)")
            
    except KeyboardInterrupt:
        print("\\n👋 CJ's Enhanced Voice session complete!")
        
        # Session summary
        try:
            penny.end_conversation_session("CJ's enhanced voice session completed")
            print("💾 CJ's enhanced voice conversation saved!")
            
            print("\\n📊 CJ's Enhanced Voice Session Summary:")
            status = penny.get_comprehensive_adaptive_status()
            print(f"   🎤 CJ's voice interactions: {interaction_count}")
            print(f"   🧠 Memory items: {sum(status['memory_stats'].values())}")
            print(f"   🎭 Current sass: {status['sass_level']}")
            print(f"   📈 Sass patterns: {status['adaptive_learning']['learned_patterns']}")
            
            relationship_summary = penny.get_relationship_summary()
            print(f"   🤝 What I learned about CJ: {relationship_summary[:80]}...")
            
            print("\\n💾 All learning saved and shared across voice + text interfaces!")
            
        except Exception as e:
            print(f"⚠️ Session summary error: {e}")
        
        try:
            tts.stop()
        except:
            pass

if __name__ == '__main__':
    main()
