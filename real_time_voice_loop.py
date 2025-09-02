#!/usr/bin/env python3
"""
PennyGPT Real-Time Voice Assistant
Connects all infrastructure: memory, pipeline, health monitoring, and audio I/O
"""

import asyncio
import sounddevice as sd
import numpy as np
import threading
import queue
import time
import sys
import os
from typing import Optional, Dict, Any
from pathlib import Path

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
sys.path.insert(0, os.path.dirname(__file__))

from memory_enhanced_pipeline import MemoryEnhancedPipeline
from src.core.pipeline import State
from src.core.telemetry import Telemetry
from src.core.wake_word import detect_wake_word, extract_command
from stt_engine import transcribe_audio


class RealTimeVoiceAssistant:
    """Complete real-time voice assistant with memory and monitoring."""
    
    def __init__(self, config_path: str = "penny_config.json"):
        print("🤖 Initializing PennyGPT Real-Time Voice Assistant...")
        
        # Core components
        self.pipeline = MemoryEnhancedPipeline()
        self.telemetry = Telemetry()
        
        # Audio configuration
        self.sample_rate = 16000  # 16kHz for Whisper
        self.channels = 1  # Mono
        self.chunk_size = 1024  # Small chunks for responsiveness
        self.audio_queue = queue.Queue()
        
        # Voice Activity Detection
        self.vad_threshold = 0.01  # Energy threshold for voice detection
        self.silence_duration = 2.0  # Seconds of silence before processing
        self.min_speech_duration = 0.5  # Minimum speech length to process
        
        # State management
        self.running = False
        self.listening_active = False
        self.audio_stream = None
        
        # Wake word detection
        self.wake_words = ["hey penny", "penny", "ok penny", "okay penny", "hello penny"]
        
        print("✅ PennyGPT initialized successfully!")
        
    def audio_callback(self, indata, frames, time_info, status):
        """Callback for audio input stream."""
        if status:
            print(f"⚠️ Audio status: {status}")
        
        # Convert to numpy array and add to queue
        audio_chunk = indata[:, 0]  # Use first channel only
        if not self.audio_queue.full():
            self.audio_queue.put(audio_chunk.copy())
    
    def detect_voice_activity(self, audio_chunk: np.ndarray) -> bool:
        """Enhanced voice activity detection."""
        # Calculate RMS energy
        rms = np.sqrt(np.mean(audio_chunk**2))
        
        # Simple threshold-based detection
        return rms > self.vad_threshold
    
    def process_audio_buffer(self, audio_buffer: list) -> Optional[str]:
        """Process collected audio buffer through STT pipeline."""
        if not audio_buffer:
            return None
            
        try:
            # Concatenate audio chunks
            full_audio = np.concatenate(audio_buffer)
            
            print("🎙️ Processing speech through STT...")
            start_time = time.time()
            
            # FIX: Use the direct transcribe function with numpy array
            text = transcribe_audio(full_audio)
            confidence = 1.0  # Default confidence
            
            stt_time = (time.time() - start_time) * 1000
            print(f"📝 STT completed in {stt_time:.1f}ms")
            
            if text and text.strip():
                print(f"👤 Heard: '{text}' (confidence: {confidence:.2f})")
                self.telemetry.log_event("stt_success", {
                    "text": text,
                    "confidence": confidence,
                    "response_time_ms": stt_time
                })
                return text.strip()
            else:
                print("❓ No speech detected")
                self.telemetry.log_event("stt_empty")
                return None
                
        except Exception as e:
            print(f"❌ STT Error: {e}")
            self.telemetry.log_event("stt_error", {"error": str(e)})
            return None
    
    async def process_audio_stream(self):
        """Main audio processing loop."""
        audio_buffer = []
        silence_start = None
        speech_start = None
        
        print("🎧 Audio processing started - listening for wake words...")
        
        while self.running:
            try:
                # Get audio chunk with timeout
                try:
                    audio_chunk = self.audio_queue.get(timeout=0.1)
                except queue.Empty:
                    continue
                
                # Check for voice activity
                has_voice = self.detect_voice_activity(audio_chunk)
                current_time = time.time()
                
                if has_voice:
                    # Voice detected
                    if not self.listening_active:
                        # Start listening
                        self.listening_active = True
                        speech_start = current_time
                        audio_buffer = [audio_chunk]
                        silence_start = None
                        print("🎙️ Voice detected - recording...")
                        self.telemetry.log_event("voice_activity_start")
                    else:
                        # Continue recording
                        audio_buffer.append(audio_chunk)
                        silence_start = None
                
                else:
                    # Silence detected
                    if self.listening_active:
                        if silence_start is None:
                            silence_start = current_time
                        elif current_time - silence_start > self.silence_duration:
                            # End of speech - process if long enough
                            speech_duration = current_time - (speech_start or current_time)
                            
                            if speech_duration >= self.min_speech_duration:
                                print(f"🔄 Processing {speech_duration:.1f}s of speech...")
                                await self.handle_voice_input(audio_buffer)
                            else:
                                print(f"⏭️ Ignoring {speech_duration:.1f}s speech (too short)")
                            
                            # Reset
                            audio_buffer = []
                            self.listening_active = False
                            silence_start = None
                            speech_start = None
                
            except Exception as e:
                print(f"❌ Audio processing error: {e}")
                self.telemetry.log_event("audio_processing_error", {"error": str(e)})
    
    async def handle_voice_input(self, audio_buffer: list):
        """Handle voice input through the complete pipeline."""
        try:
            # Step 1: Speech-to-Text
            user_text = self.process_audio_buffer(audio_buffer)
            if not user_text:
                return
            
            # Step 2: Wake word detection
            if not detect_wake_word(user_text):
                print(f"💭 Ignoring (no wake word): '{user_text}'")
                self.telemetry.log_event("wake_word_not_detected", {"text": user_text})
                return
            
            # Step 3: Extract command
            command = extract_command(user_text)
            if not command:
                command = "Hello"  # Default greeting
            
            print(f"🧠 Processing command: '{command}'")
            self.telemetry.log_event("command_extracted", {
                "original": user_text,
                "command": command
            })
            
            # Step 4: Generate response with memory
            print("🤖 Thinking...")
            start_time = time.time()
            
            # Set pipeline state
            self.pipeline.state = State.THINKING
            response = self.pipeline.think(command)
            
            think_time = (time.time() - start_time) * 1000
            print(f"💭 Generated response in {think_time:.1f}ms")
            
            if response:
                print(f"🤖 PennyGPT: '{response}'")
                
                # Step 5: Text-to-Speech
                print("🔊 Speaking response...")
                self.pipeline.state = State.SPEAKING
                tts_success = self.pipeline.speak(response)
                
                if tts_success:
                    print("✅ Response spoken successfully")
                    self.telemetry.log_event("conversation_complete", {
                        "command_length": len(command),
                        "response_length": len(response),
                        "think_time_ms": think_time
                    })
                else:
                    print("❌ TTS failed")
                    self.telemetry.log_event("tts_failed")
            else:
                print("❌ No response generated")
                self.telemetry.log_event("no_response_generated")
            
            # Return to idle
            self.pipeline.state = State.IDLE
            print("😴 Ready for next command...")
            
        except Exception as e:
            print(f"❌ Voice input handling error: {e}")
            self.telemetry.log_event("voice_input_error", {"error": str(e)})
            self.pipeline.state = State.IDLE
    
    def start_audio_stream(self):
        """Start the audio input stream."""
        try:
            print(f"🎧 Starting audio stream (sample rate: {self.sample_rate}Hz)...")
            
            self.audio_stream = sd.InputStream(
                samplerate=self.sample_rate,
                channels=self.channels,
                dtype=np.float32,
                blocksize=self.chunk_size,
                callback=self.audio_callback
            )
            self.audio_stream.start()
            print("✅ Audio stream started successfully")
            return True
            
        except Exception as e:
            print(f"❌ Failed to start audio stream: {e}")
            return False
    
    def stop_audio_stream(self):
        """Stop the audio input stream."""
        if self.audio_stream:
            try:
                self.audio_stream.stop()
                self.audio_stream.close()
                print("🎧 Audio stream stopped")
            except Exception as e:
                print(f"⚠️ Error stopping audio stream: {e}")
    
    async def run(self):
        """Main run loop for the voice assistant."""
        print("\n" + "=" * 50)
        print("🎙️ PennyGPT Real-Time Voice Assistant")
        print("=" * 50)
        print("🎯 Wake words: hey penny, penny, ok penny")
        print("🎧 Listening for voice commands...")
        print("📊 Dashboard: http://localhost:8080")
        print("🛑 Press Ctrl+C to stop")
        print("=" * 50 + "\n")
        
        # Check system health first
        print("🏥 Running system health check...")
        try:
            health_stats = await self.pipeline.health_monitor.check_all_components()
            
            if isinstance(health_stats, dict) and health_stats.get("status") == "health_monitor_disabled":
                print("✅ Health check skipped (health monitor not configured)")
            else:
                healthy_count = sum(1 for h in health_stats.values() 
                                  if hasattr(h, 'status') and h.status.name == 'HEALTHY')
                total_count = len(health_stats)
                
                if healthy_count == total_count:
                    print(f"✅ All systems healthy ({healthy_count}/{total_count})")
                else:
                    print(f"⚠️ System status: {healthy_count}/{total_count} components healthy")
                    for name, health in health_stats.items():
                        if hasattr(health, 'status') and health.status.name != 'HEALTHY':
                            print(f"   ❌ {name}: {health.status.name}")
        except Exception as e:
            print(f"⚠️ Health check failed: {e}")
        
        # Show memory stats
        memory_stats = self.pipeline.get_memory_stats()
        print(f"🧠 Memory: {memory_stats.get('total_conversation_turns', 0)} conversations, "
              f"{memory_stats.get('user_preferences', 0)} preferences learned")
        print()
        
        # Start audio stream
        if not self.start_audio_stream():
            print("❌ Cannot start without audio input")
            return
        
        self.running = True
        
        try:
            # Start audio processing loop
            await self.process_audio_stream()
            
        except KeyboardInterrupt:
            print("\n\n🛑 Stopping PennyGPT...")
        
        except Exception as e:
            print(f"\n❌ Unexpected error: {e}")
            self.telemetry.log_event("main_loop_error", {"error": str(e)})
        
        finally:
            self.running = False
            self.stop_audio_stream()
            
            # Show final stats
            final_stats = self.pipeline.get_memory_stats()
            print(f"\n📊 Session Summary:")
            print(f"   💬 Conversations: {final_stats.get('total_conversation_turns', 0)}")
            print(f"   🧠 Memory: {final_stats.get('memory_db_size', 0)/1024:.1f}KB")
            print(f"   👤 Preferences: {final_stats.get('user_preferences', 0)}")
            
            print("\n👋 PennyGPT stopped. Thanks for chatting!")
    
    def run_sync(self):
        """Synchronous wrapper for the async run method."""
        try:
            asyncio.run(self.run())
        except KeyboardInterrupt:
            pass


def check_audio_devices():
    """Check and display available audio devices."""
    print("🎵 Audio Device Information:")
    print("-" * 30)
    
    try:
        devices = sd.query_devices()
        default_input = sd.query_devices(kind='input')
        default_output = sd.query_devices(kind='output')
        
        print(f"Default Input: {default_input['name']}")
        print(f"Default Output: {default_output['name']}")
        print(f"Total Devices: {len(devices)}")
        
        input_devices = [d for d in devices if d['max_input_channels'] > 0]
        print(f"Input Devices Available: {len(input_devices)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Audio device check failed: {e}")
        return False


def main():
    """Entry point for PennyGPT voice assistant."""
    print("🤖 PennyGPT Real-Time Voice Assistant")
    print("=" * 40)
    
    # Check audio devices
    if not check_audio_devices():
        print("\n❌ Audio setup required. Please ensure:")
        print("   • Microphone is connected")
        print("   • Audio permissions are granted")
        print("   • sounddevice library is installed")
        return 1
    
    print()
    
    # Create and run voice assistant
    assistant = RealTimeVoiceAssistant()
    assistant.run_sync()
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
