#!/usr/bin/env python3
"""
TTS Voice Quality Comparison Tool
Tests different TTS engines with Penny's personality to find the best voice
"""

import os
import time
import subprocess
from dataclasses import dataclass
from typing import List, Optional
import asyncio

@dataclass
class TTSTest:
    name: str
    sample_text: str
    expected_personality: str

class VoiceQualityTester:
    def __init__(self):
        self.test_phrases = [
            TTSTest(
                "Penny Sass",
                "Oh sweetie, you're trying to explain quantum physics to me? That's adorable.",
                "Sarcastic but affectionate"
            ),
            TTSTest(
                "Tech Enthusiasm", 
                "Ooh, that's a really cool algorithm! How does the neural network training work?",
                "Excited and curious"
            ),
            TTSTest(
                "Warm Support",
                "Hey, you seem stressed about that presentation. Want to talk through it?",
                "Caring and supportive"
            ),
            TTSTest(
                "Playful Teasing",
                "Did you seriously just try to debug that for three hours when it was a missing semicolon?",
                "Amused teasing"
            ),
            TTSTest(
                "Philosophy Mode",
                "You know what I've been thinking about? What makes consciousness different from really sophisticated pattern matching?",
                "Thoughtful and deep"
            )
        ]
    
    async def test_google_tts(self, text: str) -> bool:
        """Test current Google TTS for baseline"""
        try:
            import sys
            sys.path.append('/Users/CJ/Desktop/penny_assistant/src')
            from adapters.tts.google_tts_adapter import GoogleTTS
            
            # Create GoogleTTS with minimal config
            config = {'tts': {'cache_enabled': True}}
            tts = GoogleTTS(config)
            print(f"🤖 Google TTS: {text}")
            
            # Use the speak method
            success = tts.speak(text)
            if success:
                # Wait a bit for playback to start
                await asyncio.sleep(1)
                return True
            return False
        except Exception as e:
            print(f"❌ Google TTS failed: {e}")
            return False
    
    async def test_elevenlabs(self, text: str, voice_id: str = "EXAVITQu4vr4xnSDxMaL") -> bool:
        """Test ElevenLabs TTS (Bella voice by default)"""
        try:
            import requests
            
            # You'll need to set ELEVENLABS_API_KEY environment variable
            api_key = os.getenv("ELEVENLABS_API_KEY")
            if not api_key:
                print("⚠️  Set ELEVENLABS_API_KEY to test ElevenLabs")
                return False
            
            url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
            headers = {
                "Accept": "audio/mpeg",
                "Content-Type": "application/json",
                "xi-api-key": api_key
            }
            
            data = {
                "text": text,
                "model_id": "eleven_monolingual_v1",
                "voice_settings": {
                    "stability": 0.5,
                    "similarity_boost": 0.8
                }
            }
            
            print(f"🎭 ElevenLabs: {text}")
            response = requests.post(url, json=data, headers=headers)
            
            if response.status_code == 200:
                with open("/tmp/elevenlabs_test.mp3", "wb") as f:
                    f.write(response.content)
                subprocess.run(["afplay", "/tmp/elevenlabs_test.mp3"])
                return True
            else:
                print(f"❌ ElevenLabs failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ ElevenLabs error: {e}")
            return False
    
    async def test_voice_options(self):
        """Test different ElevenLabs voices to find the best Penny match"""
        # Popular female voices that could work for Penny
        voices = [
            ("EXAVITQu4vr4xnSDxMaL", "Bella - Warm and friendly"),
            ("21m00Tcm4TlvDq8ikWAM", "Rachel - Natural conversational"),
            ("AZnzlk1XvdvUeBnXmlld", "Domi - Confident and clear"),
            ("pNInz6obpgDQGcFmaJgB", "Adam - For comparison (male)"),
        ]
        
        test_text = "Hey there! I'm Penny, your AI companion. Ready to chat about whatever's on your mind?"
        
        print("🎭 Testing different ElevenLabs voices for Penny...")
        print("=" * 50)
        
        for voice_id, description in voices:
            print(f"\n🎤 Testing: {description}")
            await self.test_elevenlabs(test_text, voice_id)
            input("Press Enter for next voice...")
    
    async def run_comparison(self):
        """Run full voice comparison test"""
        print("🎤 TTS Voice Quality Comparison")
        print("=" * 50)
        
        test_text = "Oh sweetie, you're trying to explain quantum physics to me? That's adorable."
        
        print(f"\n📝 Testing: Penny Sass")
        print(f"Text: '{test_text}'")
        print("-" * 30)
        
        # Test current vs ElevenLabs
        print("\n1. Current Google TTS:")
        await self.test_google_tts(test_text)
        
        print("\n2. ElevenLabs (Bella voice):")
        await self.test_elevenlabs(test_text)
        
        print("\n🎯 Ready to test different voice options?")
        choice = input("Test different ElevenLabs voices? (y/n): ").lower()
        if choice == 'y':
            await self.test_voice_options()

async def main():
    tester = VoiceQualityTester()
    
    print("🎯 Penny Voice Quality Upgrade with ElevenLabs")
    print("Testing natural voice vs current Google TTS")
    print()
    
    # Check if API key is set
    if not os.getenv("ELEVENLABS_API_KEY"):
        print("🔧 Setup needed:")
        print("1. Get API key from https://elevenlabs.io")
        print("2. Run: export ELEVENLABS_API_KEY='your_key_here'")
        print("3. Run this script again")
        return
    
    await tester.run_comparison()

if __name__ == "__main__":
    asyncio.run(main())
