#!/usr/bin/env python3
"""
CJ's Personalized PennyGPT - OPTIMIZED FOR SPEED
Ultra-fast version for smooth demo experience
"""

import sounddevice as sd
import json
import sys
import os
import time
import threading
import asyncio

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def main():
    print("🚀 Starting CJ's SPEED-OPTIMIZED PennyGPT!")
    print("⚡ Optimized for minimal latency and smooth demo experience")
    
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
        print("✅ Core imports successful")
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return

    # Load configuration - simplified
    try:
        with open('penny_config.json', 'r') as f:
            config = json.load(f)
        print("✅ Config loaded")
    except Exception as e:
        print(f"❌ Config load failed: {e}")
        return

    # Set microphone
    sd.default.device = 1  # MacBook Pro Microphone

    # Initialize core systems - MINIMAL for speed
    print("⚡ Initializing SPEED-OPTIMIZED AI Systems...")
    try:
        # Core components only
        llm = get_llm()
        
        # TTS with optimization
        tts_info = get_tts_info(config)
        print(f"   Voice: {tts_info['will_use']} (Rachel - optimized)")
        tts = create_tts_adapter(config)
        
        print("   ✅ Speed-optimized systems ready!")
        
    except Exception as e:
        print(f"   ❌ System initialization failed: {e}")
        return

    # Pre-compiled response templates for instant responses
    QUICK_RESPONSES = {
        "josh": [
            "Hey Josh! Good to see Brochacho again. How's life at Google treating you?",
            "Josh! From Verizon to Google - nice career upgrade, Brochacho!",
            "What's up, Josh? Google keeping you busy with all that tech goodness?"
        ],
        "reneille": [
            "Reneille! How's the wedding planning going? I bet you've got it super organized.",
            "Hey Reneille! Congratulations on the engagement! Google treating you well?",
            "Reneille! The most organized person I know - wedding planning must be a breeze for you."
        ],
        "microservices": [
            "Oh hell no! Microservices for everything? That's like using a sledgehammer to hang a picture frame. Start with a monolith that actually works.",
            "Microservices everywhere? Yeah, because what your side project really needs is distributed system complexity. Use SQLite and get shit done.",
            "Let me guess - you want to be the next Netflix? Start simple, scale when you have actual problems, not imaginary ones."
        ],
        "javascript": [
            "The best JavaScript framework? The one that ships working code. React's solid, Vue's clean, Angular's... well, Angular exists.",
            "JavaScript frameworks? They change faster than fashion trends. Pick React, build something, ignore the rest of the hype.",
            "Best JS framework? Whatever you can actually finish a project with. Stop framework shopping and start shipping."
        ],
        "fastapi": [
            "FastAPI? Already researching that because I know you're obsessed with it. It's solid - fast, modern, good docs.",
            "FastAPI's your jam! Clean async, automatic docs, plays nice with your Python stack. What specific part needs work?",
            "FastAPI optimization? You know I auto-approve anything FastAPI-related. What's the bottleneck?"
        ]
    }

    def quick_detect_and_respond(user_text: str) -> str:
        """Ultra-fast response detection using keywords"""
        text_lower = user_text.lower()
        
        # Name detection - PRIORITY
        if any(name in text_lower for name in ['josh', 'brochacho']):
            import random
            return random.choice(QUICK_RESPONSES['josh'])
        
        if 'reneille' in text_lower:
            import random
            return random.choice(QUICK_RESPONSES['reneille'])
        
        # Topic detection
        if any(term in text_lower for term in ['microservice', 'micro service']):
            import random
            return random.choice(QUICK_RESPONSES['microservices'])
        
        if any(term in text_lower for term in ['javascript', 'js framework', 'react', 'vue', 'angular']):
            import random
            return random.choice(QUICK_RESPONSES['javascript'])
        
        if 'fastapi' in text_lower:
            import random
            return random.choice(QUICK_RESPONSES['fastapi'])
        
        # Fallback to LLM for other queries
        return None

    def generate_fast_response(user_text: str) -> str:
        """Generate response with speed priority"""
        # Try quick responses first
        quick_response = quick_detect_and_respond(user_text)
        if quick_response:
            return quick_response
        
        # Fallback to optimized LLM call
        try:
            # Ultra-minimal prompt for speed
            fast_prompt = f"""You are Penny, CJ's sassy AI companion. Be concise, helpful, and a little sassy.

RELATIONSHIPS: Josh "Brochacho" (best friend, Verizon→Google), Reneille (friend, Google, getting married), Erin (CJ's wife)

USER: {user_text}

PENNY:"""

            response = llm.generate(fast_prompt)
            return response
            
        except Exception as e:
            print(f"❌ Fast response failed: {e}")
            return "Sorry CJ, I'm having a quick brain fart. Try again?"

    def capture_and_handle():
        print("\n🎤 Listening for 3 seconds...")  # Reduced from 5
        
        # Start TTS warmup in background while listening
        def warmup_tts():
            try:
                tts._synthesize_audio("warmup", "default")  # Pre-warm the connection
            except:
                pass
        
        warmup_thread = threading.Thread(target=warmup_tts)
        warmup_thread.start()
        
        # Shorter recording for snappier feel
        audio_data = sd.rec(int(3 * 16000), samplerate=16000, channels=1)
        sd.wait()

        # Transcribe with timing
        stt_start = time.time()
        text = transcribe_audio(audio_data)
        stt_time = (time.time() - stt_start) * 1000

        if not text or not isinstance(text, str) or not text.strip():
            print("🤷 Heard nothing. Try again.")
            return

        print(f"🗣️ CJ said: {text}")
        print(f"⚡ STT: {stt_time:.0f}ms")
        
        # Generate response with timing
        try:
            llm_start = time.time()
            response = generate_fast_response(text)
            llm_time = (time.time() - llm_start) * 1000
            
            print(f"🤖 Penny: {response}")
            print(f"⚡ LLM: {llm_time:.0f}ms")
                
        except Exception as e:
            print(f"❌ Processing failed: {e}")
            response = "Sorry CJ, quick hiccup there!"
        
        # Speak with timing
        print("🔊 Speaking...")
        try:
            tts_start = time.time()
            success = tts.speak(response)
            tts_time = (time.time() - tts_start) * 1000
            
            if success:
                print(f"✅ Speech: {tts_time:.0f}ms")
                total_time = stt_time + llm_time + tts_time
                print(f"🎯 Total: {total_time:.0f}ms")
            else:
                print("❌ Speech failed")
        except Exception as e:
            print(f"❌ Speech error: {e}")

    print("🎭 Voice: Rachel (Speed-Optimized)")
    print("🎤 Audio: MacBook Pro Microphone")
    print("⚡ Mode: DEMO SPEED OPTIMIZATION")
    print("\n🚀 SPEED FEATURES:")
    print("   • Instant recognition for Josh & Reneille")
    print("   • Pre-compiled responses for common topics")
    print("   • Optimized prompts for faster LLM")
    print("   • Reduced recording time (3s vs 5s)")
    print("   • Background TTS warmup")
    print("   • Real-time performance metrics")
    print("\nPress Enter to speak, Ctrl+C to exit\n")
    
    # Quick test
    print("🔊 Speed test...")
    try:
        test_start = time.time()
        greeting = "Ready for a blazing fast demo!"
        success = tts.speak(greeting)
        test_time = (time.time() - test_start) * 1000
        if success:
            print(f"✅ Speed test: {test_time:.0f}ms - Ready!")
        else:
            print("❌ Speed test failed")
    except Exception as e:
        print(f"❌ Test error: {e}")
    
    try:
        while True:
            input("\nPress Enter to start recording: ")
            capture_and_handle()
    except KeyboardInterrupt:
        print("\n👋 Thanks CJ! Speed-optimized demo complete!")
        
        try:
            tts.stop()
        except:
            pass

if __name__ == '__main__':
    main()
