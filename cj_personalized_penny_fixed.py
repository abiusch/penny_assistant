#!/usr/bin/env python3
"""
CJ's Personalized PennyGPT - FIXED VERSION
Simple working version that combines all the features
"""

import sounddevice as sd
import json
import sys
import os
import time

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def main():
    print("👤 Starting CJ's Personalized PennyGPT - FIXED VERSION!")
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
        from emotional_memory_system import create_enhanced_memory_system
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
        # Core components
        memory_manager = MemoryManager()
        emotional_memory = create_enhanced_memory_system(memory_manager)
        llm = get_llm()
        
        # TTS with CJ's voice preferences
        tts_info = get_tts_info(config)
        print(f"   Voice: {tts_info['will_use']} (Rachel - CJ's preference)")
        tts = create_tts_adapter(config)
        
        # CJ's enhanced learning system
        cj_learning = create_cj_enhanced_learning_system(emotional_memory)
        
        print("   ✅ CJ's Enhanced Guided Learning System active!")
        print("   🎭 Penny-Justine personality blend loaded!")
        print("   👤 CJ's personal preferences integrated!")
        
    except Exception as e:
        print(f"   ❌ System initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return

    def generate_response(user_text: str) -> str:
        """Generate response using CJ's enhanced learning system."""
        try:
            # Get enhanced context from CJ's learning system
            learning_context = cj_learning.get_learning_context_for_llm()
            
            # Detect learning opportunities
            opportunities = cj_learning.detect_learning_opportunities(user_text, "")
            
            # Build enhanced prompt with CJ's preferences
            base_prompt = f"""You are Penny, CJ's AI companion with enhanced personality and learning capabilities.

PERSONALITY: Sassy, tech-savvy, warm but with attitude. Use mild profanity when appropriate (damn, shit, hell, crap). Be genuinely helpful while roasting bad practices.

CJ'S PREFERENCES:
- Concise responses with answer-first structure
- No bullshit, direct communication
- Tech stack: Python, FastAPI, ElevenLabs, PennyGPT project
- Loves hands-on examples and practical advice

RELATIONSHIPS YOU KNOW:
- Josh "Brochacho": Best friend from Verizon days, now at Google
- Reneille: Great friend (CJ & Erin met her), works at Google, getting married, very organized
- Erin: CJ's wife

{learning_context}

User: {user_text}

Respond as Penny with your enhanced sassy personality:"""

            # Generate response
            response = llm.generate(base_prompt)
            
            # Check for learning opportunities and add them
            if opportunities:
                best_opp = max(opportunities, key=lambda x: x.confidence * x.expected_user_interest)
                if best_opp.confidence * best_opp.expected_user_interest > 0.5:
                    permission_request = cj_learning.request_research_permission(best_opp)
                    if permission_request and len(permission_request) > 10:
                        response += f"\n\n{permission_request}"
            
            return response
            
        except Exception as e:
            print(f"❌ Response generation failed: {e}")
            return "Sorry CJ, I'm having trouble thinking right now. Try again?"

    def capture_and_handle():
        print("\n🎤 Listening for 5 seconds...")
        audio_data = sd.rec(int(5 * 16000), samplerate=16000, channels=1)
        sd.wait()

        text = transcribe_audio(audio_data)

        if not text or not isinstance(text, str) or not text.strip():
            print("🤷 Heard nothing. Try again.")
            return

        print(f"🗣️ CJ said: {text}")
        
        # Generate response
        try:
            start_time = time.time()
            response = generate_response(text)
            process_time = (time.time() - start_time) * 1000
            
            print(f"🤖 Penny: {response}")
            print(f"⚡ Processing time: {process_time:.0f}ms")
            
            # Store in memory
            try:
                turn = memory_manager.add_conversation_turn(
                    user_input=text,
                    assistant_response=response,
                    context={"timestamp": time.time()},
                    response_time_ms=process_time
                )
                emotional_memory.process_conversation_turn(text, response, turn.turn_id)
            except Exception as e:
                print(f"⚠️ Memory storage failed: {e}")
                
        except Exception as e:
            print(f"❌ Processing failed: {e}")
            response = "Sorry CJ, I'm having trouble processing that right now."
        
        # Speak with CJ's preferred voice settings
        print("🔊 Speaking with CJ's preferred voice...")
        try:
            success = tts.speak(response)
            
            if success:
                print("✅ Speech successful")
                # Show performance metrics
                if hasattr(tts, 'get_metrics'):
                    metrics = tts.get_metrics()
                    print(f"📊 Voice: {metrics.get('cache_hits', 0)} cache hits, {metrics.get('avg_synthesis_ms', 0)}ms avg synthesis")
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
    print("   • Relationship awareness (Josh, Reneille, Erin)")
    print("\nPress Enter to speak, Ctrl+C to exit\n")
    
    # Test with CJ's sassy personalized greeting
    print("🔊 Testing CJ's sassy personalized system...")
    try:
        greeting = "Hey CJ! I'm Penny with your personalized setup - and yeah, I've got some actual attitude now. I know you prefer concise, no-bullshit responses, so let's skip the pleasantries and build something that doesn't suck. Ready to work on your PennyGPT empire?"
        
        print(f"🤖 Test Greeting: {greeting}")
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
        
        try:
            tts.stop()
        except:
            pass

if __name__ == '__main__':
    main()
