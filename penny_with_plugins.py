#!/usr/bin/env python3
"""
Enhanced Penny Assistant with Plugin System
Integrates weather plugin with existing voice pipeline
"""

import sounddevice as sd
import asyncio
import sys
import os
import tempfile
from gtts import gTTS
from pygame import mixer
import io

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from stt_engine import transcribe_audio
from src.core.enhanced_intent_router import EnhancedIntentRouter
from src.core.llm_router import get_llm
from src.core.llm_router import load_config

# Set the correct microphone
sd.default.device = 1  # MacBook Pro Microphone


class PennyWithPlugins:
    """Enhanced Penny with plugin system and TTS"""
    
    def __init__(self):
        self.config = load_config()
        self.router = EnhancedIntentRouter(self.config)
        self.llm = get_llm()
        
        # Initialize TTS
        self.tts_enabled = True
        try:
            mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
            print("🔊 TTS system initialized")
        except Exception as e:
            print(f"⚠️ TTS initialization failed: {e}")
            self.tts_enabled = False
            
        print("🔌 Plugin system loaded")
        
        # Show available plugins
        plugins = self.router.get_available_plugins()
        if plugins:
            print("📦 Available plugins:")
            for name, help_text in plugins.items():
                print(f"  • {name}: {help_text}")
        else:
            print("📦 No plugins loaded")
    
    async def speak_response(self, text: str) -> bool:
        """Convert text to speech and play it"""
        if not self.tts_enabled or not text.strip():
            return False
            
        try:
            print("🔊 Speaking response...")
            
            # Create TTS audio
            tts = gTTS(text=text, lang='en', slow=False)
            
            # Save to temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as temp_file:
                tts.save(temp_file.name)
                temp_filename = temp_file.name
            
            # Play the audio
            mixer.music.load(temp_filename)
            mixer.music.play()
            
            # Wait for playback to complete
            while mixer.music.get_busy():
                await asyncio.sleep(0.1)
            
            # Clean up temp file
            try:
                os.unlink(temp_filename)
            except:
                pass  # File cleanup failure is non-critical
                
            return True
            
        except Exception as e:
            print(f"❌ TTS error: {e}")
            return False
    
    async def handle_query(self, text: str) -> str:
        """Handle user query through plugin system"""
        try:
            # Route through plugin system
            result = await self.router.handle_query(text)
            
            if result['handler_type'] == 'plugin':
                # Plugin handled it
                if result['success']:
                    print(f"🔌 Plugin '{result['handler_name']}' handled query")
                    return result['response']
                else:
                    print(f"❌ Plugin error: {result.get('error', 'Unknown error')}")
                    return result['response']
            
            elif result.get('route_to_llm'):
                # Route to LLM
                print(f"🤖 Routing to LLM (intent: {result['intent']})")
                
                # Use your existing LLM
                if hasattr(self.llm, 'generate'):
                    response = self.llm.generate(text)
                elif hasattr(self.llm, 'complete'):
                    response = self.llm.complete(text)
                else:
                    response = f"I heard: {text}"
                
                return response
            
            else:
                return "I'm not sure how to handle that."
                
        except Exception as e:
            print(f"❌ Error processing query: {e}")
            return f"Sorry, I encountered an error: {str(e)}"
    
    async def capture_and_handle(self):
        """Capture audio and handle with plugins, including TTS response"""
        print("🎤 Listening for 5 seconds...")
        audio_data = sd.rec(int(5 * 16000), samplerate=16000, channels=1)
        sd.wait()

        text = transcribe_audio(audio_data)

        if not text or not isinstance(text, str) or not text.strip():
            print("🤷 Heard nothing. Try again.")
            return

        print(f"🗣️ You said: {text}")
        
        # Process through plugin system
        response = await self.handle_query(text)
        print(f"💬 Response: {response}")
        
        # Speak the response
        if response:
            success = await self.speak_response(response)
            if not success and self.tts_enabled:
                print("⚠️ TTS failed, but response generated successfully")
        
        return response


async def main():
    """Main async loop for enhanced Penny with TTS"""
    print("💬 Starting Enhanced PennyGPT with Plugins and TTS...")
    print("Using MacBook Pro Microphone")
    print("Press Enter to speak, Ctrl+C to exit")
    print("Try asking: 'What's the weather?' or 'How's the weather in London?'")
    print("Responses will be spoken back to you!")
    print()
    
    penny = PennyWithPlugins()
    
    try:
        while True:
            input("Press Enter to start recording: ")
            await penny.capture_and_handle()
    except KeyboardInterrupt:
        print("\n👋 Exiting Enhanced PennyGPT...")


def sync_test():
    """Synchronous test function"""
    print("🧪 Testing plugin system...")
    
    async def run_test():
        penny = PennyWithPlugins()
        
        test_queries = [
            "What's the weather?",
            "How's the weather in London?", 
            "Tell me a joke",
            "What time is it?"
        ]
        
        for query in test_queries:
            print(f"\n📝 Testing: '{query}'")
            response = await penny.handle_query(query)
            print(f"💬 Response: {response}")
    
    asyncio.run(run_test())


if __name__ == '__main__':
    import sys
    
    # Support both test mode and normal mode
    if len(sys.argv) > 1 and sys.argv[1] == '--test':
        sync_test()
    else:
        asyncio.run(main())
