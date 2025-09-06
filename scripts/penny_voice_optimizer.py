#!/usr/bin/env python3
"""
Enhanced Penny Voice Tester
Tests specific ElevenLabs voices that match Penny's personality traits
"""

import os
import asyncio
import requests
import subprocess

class PennyVoiceTester:
    def __init__(self):
        self.api_key = os.getenv("ELEVENLABS_API_KEY")
        if not self.api_key:
            raise ValueError("Set ELEVENLABS_API_KEY environment variable")
    
    async def test_voice(self, voice_id: str, voice_name: str, text: str, personality_settings: dict):
        """Test a specific voice with custom personality settings"""
        try:
            url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
            headers = {
                "Accept": "audio/mpeg",
                "Content-Type": "application/json",
                "xi-api-key": self.api_key
            }
            
            data = {
                "text": text,
                "model_id": "eleven_monolingual_v1",
                "voice_settings": personality_settings
            }
            
            print(f"🎤 {voice_name}: {text}")
            response = requests.post(url, json=data, headers=headers)
            
            if response.status_code == 200:
                filename = f"/tmp/penny_voice_{voice_id[:8]}.mp3"
                with open(filename, "wb") as f:
                    f.write(response.content)
                subprocess.run(["afplay", filename])
                return True
            else:
                print(f"❌ Failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Error: {e}")
            return False
    
    async def test_penny_candidates(self):
        """Test voices specifically for Penny's personality"""
        
        # Penny personality test phrases
        test_phrases = [
            "Oh sweetie, that's... actually pretty smart. I'm impressed!",
            "Wait, wait, wait. You're telling me this neural network thing can learn? That's so cool!",
            "Okay, I know I tease you about your geeky stuff, but this AI thing is actually fascinating."
        ]
        
        # Voice candidates with Penny-optimized settings
        penny_voices = [
            {
                "id": "21m00Tcm4TlvDq8ikWAM", 
                "name": "Rachel - Natural & Conversational",
                "settings": {"stability": 0.3, "similarity_boost": 0.7, "style": 0.2}
            },
            {
                "id": "EXAVITQu4vr4xnSDxMaL", 
                "name": "Bella - Warm & Friendly (Higher Energy)",
                "settings": {"stability": 0.2, "similarity_boost": 0.8, "style": 0.4}
            },
            {
                "id": "AZnzlk1XvdvUeBnXmlld", 
                "name": "Domi - Confident & Playful", 
                "settings": {"stability": 0.4, "similarity_boost": 0.6, "style": 0.3}
            },
            {
                "id": "ThT5KcBeYPX3keUQqHPh", 
                "name": "Dorothy - Expressive & Animated",
                "settings": {"stability": 0.3, "similarity_boost": 0.75, "style": 0.5}
            },
            {
                "id": "oWAxZDx7w5VEj9dCyTzz", 
                "name": "Grace - Young & Energetic",
                "settings": {"stability": 0.25, "similarity_boost": 0.8, "style": 0.4}
            }
        ]
        
        print("🎭 Testing Penny-Optimized Voices")
        print("=" * 60)
        
        for phrase in test_phrases:
            print(f"\n📝 Testing phrase: '{phrase}'")
            print("-" * 40)
            
            for voice in penny_voices:
                await self.test_voice(
                    voice["id"], 
                    voice["name"], 
                    phrase, 
                    voice["settings"]
                )
                
                rating = input(f"Rate {voice['name']} (1-5, or 's' to skip): ").strip()
                if rating == 's':
                    break
                    
                await asyncio.sleep(1)
            
            print("\n" + "="*40)
            continue_test = input("Continue to next phrase? (y/n): ").lower()
            if continue_test != 'y':
                break
    
    async def get_voice_library(self):
        """Get all available voices from ElevenLabs"""
        try:
            url = "https://api.elevenlabs.io/v1/voices"
            headers = {"xi-api-key": self.api_key}
            
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                voices = response.json()["voices"]
                print("🎤 Available ElevenLabs Voices:")
                print("=" * 50)
                
                for voice in voices:
                    print(f"• {voice['name']} ({voice['voice_id'][:8]}...)")
                    if 'labels' in voice:
                        labels = ', '.join(voice['labels'].values()) if voice['labels'] else 'No labels'
                        print(f"  Labels: {labels}")
                    print()
                
                return voices
            else:
                print(f"❌ Failed to get voices: {response.status_code}")
                return []
        except Exception as e:
            print(f"❌ Error getting voices: {e}")
            return []

async def main():
    try:
        tester = PennyVoiceTester()
        
        print("🎯 Penny Voice Optimization Test")
        print("Finding the perfect voice for Penny's personality")
        print()
        
        choice = input("Choose option:\n1. Test Penny-optimized voices\n2. Browse all available voices\n3. Both\nChoice (1/2/3): ").strip()
        
        if choice in ['2', '3']:
            print("\n🎤 Getting voice library...")
            await tester.get_voice_library()
            
        if choice in ['1', '3']:
            print("\n🎭 Testing optimized voices...")
            await tester.test_penny_candidates()
            
    except ValueError as e:
        print(f"❌ Setup error: {e}")
        print("Get your API key from https://elevenlabs.io")
        print("Then run: export ELEVENLABS_API_KEY='your_key_here'")

if __name__ == "__main__":
    asyncio.run(main())
