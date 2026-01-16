#!/usr/bin/env python3
"""
Enhanced Adaptive Voice Interface
Fixes: Enter to stop recording, automatic CJ recognition, reduced TTS chunking
"""

import sounddevice as sd
import json
import sys
import os
import time
import numpy as np
import threading
import queue

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

def record_until_enter():
    """Record audio until user presses Enter"""
    print("🎤 Recording... Press ENTER to stop")
    
    # Audio parameters
    sample_rate = 16000
    channels = 1
    
    # Storage for audio chunks
    audio_chunks = []
    
    # Audio recording callback
    def audio_callback(indata, frames, time, status):
        audio_chunks.append(indata.copy())
    
    # Start recording
    stream = sd.InputStream(
        samplerate=sample_rate,
        channels=channels,
        callback=audio_callback,
        device=1  # MacBook Pro Microphone
    )
    
    stream.start()
    
    # Wait for Enter key
    input()  # This blocks until Enter is pressed
    
    # Stop recording
    stream.stop()
    stream.close()
    
    # Combine all audio chunks
    if audio_chunks:
        audio_data = np.concatenate(audio_chunks, axis=0)
        print(f"⏹️ Recording complete ({len(audio_data)/sample_rate:.1f}s)")
        return audio_data
    else:
        print("⏹️ No audio recorded")
        return np.array([])

def main():
    print("🎤 Enhanced Adaptive Voice Interface - CJ's Voice Assistant!")
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
        
        # Optimize TTS settings for faster speech (less chunking)
        if 'tts' in config and 'elevenlabs' in config['tts']:
            # Increase chunk size to reduce splitting
            config['tts']['elevenlabs']['chunk_size'] = 2500  # Larger chunks
            config['tts']['elevenlabs']['optimize_streaming'] = True
        
    except Exception as e:
        print(f"❌ Config load failed: {e}")
        return

    # Set microphone to MacBook
    sd.default.device = 1  # MacBook Pro Microphone

    # Initialize adaptive sass-enhanced personality system for CJ
    print("🧠 Initializing CJ's Adaptive Voice Assistant...")
    try:
        penny = create_adaptive_sass_enhanced_penny()
        
        # Start voice conversation session for CJ
        session_id = penny.start_conversation_session("cj_adaptive_voice")
        print(f"   📝 Started CJ's voice session: {session_id}")
        
        # Store CJ's identity in memory for this session
        penny.manually_store_memory("user_fact", "name", "CJ")
        penny.manually_store_memory("user_fact", "interface", "Voice")
        print("   👤 CJ identity stored in memory")
        
        # Check what we remember about CJ
        relationship_summary = penny.get_relationship_summary()
        if "still getting to know" not in relationship_summary:
            print(f"   🤝 What I know about CJ: {relationship_summary[:60]}...")
        else:
            print("   🌱 Fresh start - ready to learn about CJ!")
        
        # TTS setup with optimized settings
        tts_info = get_tts_info(config)
        print(f"   🔊 Voice: {tts_info['will_use']} (Rachel)")
        tts = create_tts_adapter(config)
        
        print("   ✅ CJ's adaptive voice assistant ready!")
        print("   🧠 Cross-session memory + adaptive sass learning active!")
        
    except Exception as e:
        print(f"   ❌ System initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return

    def capture_and_respond():
        print("\n" + "="*50)
        
        # Record until Enter is pressed
        with time_operation(OperationType.STT):
            audio_data = record_until_enter()

        if len(audio_data) == 0:
            print("🤷 No audio recorded. Try again.")
            return

        # Show basic stats
        max_vol = np.max(np.abs(audio_data))
        duration = len(audio_data) / 16000
        print(f"📊 Audio: {duration:.1f}s (max vol: {max_vol:.3f})")

        # Transcribe
        text = transcribe_audio(audio_data)

        if not text or not isinstance(text, str) or not text.strip():
            print("🤷 Could not understand speech. Try again.")
            return

        print(f"🗣️ CJ said: {text}")
        
        # Generate adaptive sass response with CJ context
        try:
            with time_operation(OperationType.LLM):
                # Enhanced context detection for voice
                context = detect_context(text)
                
                # Add CJ-specific context
                context['user'] = 'CJ'
                context['interface'] = 'voice'
                
                # Prepend CJ context to the input for better recognition
                contextualized_input = f"CJ says: {text}"
                
                # Generate adaptive sass-aware response
                enhanced_response = penny.generate_adaptive_sass_response(
                    contextualized_input, context
                )
                
                # Clean up any redundant CJ mentions in response
                enhanced_response = enhanced_response.replace("CJ says: ", "")
                enhanced_response = enhanced_response.replace("CJ, ", "")
            
            # Show current sass level and any learning
            current_sass = penny.sass_controller.current_level.value
            learned_info = penny._get_learned_sass_info()
            
            print(f"🤖 Penny [{current_sass}]: {enhanced_response}")
            if "learned preference" in learned_info:
                print(f"💡 {learned_info}")
            
        except Exception as e:
            print(f"❌ Response generation failed: {e}")
            enhanced_response = "Sorry CJ, I'm having trouble with my adaptive system right now. Try again?"
        
        # Speak with adaptive personality (optimized for less chunking)
        print("🔊 Speaking...")
        try:
            with time_operation(OperationType.TTS):
                # Optimize response length to reduce chunking
                if len(enhanced_response) > 2000:
                    # If response is very long, summarize key points
                    parts = enhanced_response.split('. ')
                    if len(parts) > 5:
                        enhanced_response = '. '.join(parts[:5]) + '.'
                
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
            print(f"⚡ Response time: {total_ms:.0f}ms (STT: {averages.get('STT', 0):.0f}ms, LLM: {averages.get('LLM', 0):.0f}ms, TTS: {averages.get('TTS', 0):.0f}ms)")

    print("\n🎯 CJ's Voice Assistant Features:")
    print("   • Press ENTER to stop recording (no more 4-second cutoff!)")
    print("   • Automatic CJ recognition (knows you're CJ)")
    print("   • Optimized speech output (faster, fewer chunks)")
    print("   • Cross-session memory (shared with text interface)")
    print("   • Adaptive sass learning from voice commands")
    print("   • Context-aware personality (programming vs. social)")
    
    # Test adaptive greeting with CJ recognition
    print("\n🔊 Testing CJ's adaptive voice system...")
    try:
        test_context = {'topic': 'greeting', 'emotion': 'neutral', 'user': 'CJ', 'interface': 'voice'}
        greeting = penny.generate_adaptive_sass_response(
            "CJ says: Hi Penny, I'm back for voice!", test_context
        )
        greeting = greeting.replace("CJ says: ", "").replace("CJ, ", "")
        
        current_sass = penny.sass_controller.current_level.value
        print(f"🤖 Adaptive Greeting [{current_sass}]: {greeting}")
        
        # Test optimized speech
        success = tts.speak(greeting)
        if success:
            print("✅ CJ's adaptive voice system test successful!")
        else:
            print("❌ TTS test failed")
            
    except Exception as e:
        print(f"❌ Adaptive system test error: {e}")
    
    print("\n🎤 Enhanced Voice Commands for CJ:")
    print("   • 'Set sass to minimal' (learns CJ prefers professional voice)")
    print("   • 'Tone it down' while debugging (learns context preference)")
    print("   • 'Be more sassy' in casual chat (learns social preference)")
    print("   • 'What have you learned about my sass preferences?'")
    print("   • Any conversation (Penny knows you're CJ automatically)")
    print("\n💡 Press Enter to start recording, Ctrl+C to exit")
    
    interaction_count = 0
    
    try:
        while True:
            print("\n🎤 Ready for CJ's voice input...")
            capture_and_respond()
            interaction_count += 1
            print(f"🧠 Learning from CJ's voice... ({interaction_count} interactions)")
            
    except KeyboardInterrupt:
        print("\n👋 CJ's Adaptive Voice session complete!")
        
        # End session with comprehensive summary
        try:
            penny.end_conversation_session("CJ's adaptive voice session completed")
            print("💾 CJ's voice conversation memories saved!")
            
            print("\n📊 CJ's Voice Session Summary:")
            status = penny.get_comprehensive_adaptive_status()
            print(f"   🎤 CJ's voice interactions: {interaction_count}")
            print(f"   🧠 Memory items: {sum(status['memory_stats'].values())}")
            print(f"   🎭 Current sass: {status['sass_level']} - {status['sass_description']}")
            print(f"   📈 Sass adjustments learned: {status['adaptive_learning']['total_adjustments']}")
            print(f"   🎯 Learned patterns: {status['adaptive_learning']['learned_patterns']}")
            
            if status['adaptive_learning']['context_preferences']:
                print("   🔍 CJ's voice sass preferences:")
                for context, pref in list(status['adaptive_learning']['context_preferences'].items())[:3]:
                    print(f"     • {context}: {pref['preferred_sass']} sass")
            
            relationship_summary = penny.get_relationship_summary()
            print(f"   🤝 What I learned about CJ: {relationship_summary[:80]}...")
            
            print("\n💾 All CJ's voice memories and learning patterns saved!")
            print("🔄 CJ's adaptive sass preferences are now shared across voice + text!")
            
        except Exception as e:
            print(f"⚠️ Session summary error: {e}")
        
        try:
            tts.stop()
        except:
            pass

if __name__ == '__main__':
    main()
