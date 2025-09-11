#!/usr/bin/env python3
"""
Voice Activity Detection for Natural Conversation Flow
Detects speech vs silence to trigger responses naturally
"""

import sounddevice as sd
import numpy as np
import time
from typing import Tuple, Optional
import threading


class VoiceActivityDetector:
    """Detects when user is speaking vs when they've finished"""
    
    def __init__(self, 
                 silence_threshold: float = 0.01,
                 silence_duration: float = 1.5,
                 max_recording_time: float = 30.0,
                 sample_rate: int = 16000):
        
        self.silence_threshold = silence_threshold
        self.silence_duration = silence_duration
        self.max_recording_time = max_recording_time
        self.sample_rate = sample_rate
        
        # Internal state
        self.is_recording = False
        self.audio_buffer = []
        self.last_speech_time = 0.0
        self.recording_start = 0.0
        
    def record_until_silence(self, device: Optional[int] = None) -> np.ndarray:
        """
        Record audio until user stops speaking (detected by silence)
        Returns: Complete audio recording as numpy array
        """
        print("🎤 Listening... (speak naturally, I'll respond when you pause)")
        
        self.audio_buffer = []
        self.is_recording = True
        self.recording_start = time.time()
        self.last_speech_time = time.time()
        
        # Use a smaller chunk size for more responsive detection
        chunk_duration = 0.1  # 100ms chunks
        chunk_samples = int(chunk_duration * self.sample_rate)
        
        try:
            while self.is_recording:
                # Record a small chunk
                chunk = sd.rec(chunk_samples, 
                             samplerate=self.sample_rate, 
                             channels=1, 
                             device=device,
                             dtype='float32')
                sd.wait()
                
                # Add to buffer
                self.audio_buffer.append(chunk.flatten())
                
                # Check if this chunk contains speech
                chunk_volume = np.max(np.abs(chunk))
                current_time = time.time()
                
                if chunk_volume > self.silence_threshold:
                    # Speech detected
                    self.last_speech_time = current_time
                    print("🗣️", end="", flush=True)  # Visual feedback
                else:
                    # Silence detected
                    silence_duration = current_time - self.last_speech_time
                    
                    # Only stop if we've had some speech first
                    speech_duration = self.last_speech_time - self.recording_start
                    if speech_duration > 0.5 and silence_duration > self.silence_duration:
                        print(" (silence detected - processing...)")
                        break
                
                # Safety timeout
                total_duration = current_time - self.recording_start
                if total_duration > self.max_recording_time:
                    print(" (max time reached - processing...)")
                    break
        
        except KeyboardInterrupt:
            print(" (interrupted)")
            return np.array([])
        
        finally:
            self.is_recording = False
        
        # Combine all chunks
        if self.audio_buffer:
            complete_audio = np.concatenate(self.audio_buffer)
            print(f"📝 Recorded {len(complete_audio)/self.sample_rate:.1f} seconds")
            return complete_audio
        else:
            return np.array([])
    
    def get_recording_stats(self) -> dict:
        """Get statistics about the last recording"""
        if not self.audio_buffer:
            return {}
        
        complete_audio = np.concatenate(self.audio_buffer)
        return {
            'duration_seconds': len(complete_audio) / self.sample_rate,
            'max_volume': float(np.max(np.abs(complete_audio))),
            'mean_volume': float(np.mean(np.abs(complete_audio))),
            'chunks_recorded': len(self.audio_buffer)
        }


def create_voice_detector(silence_threshold: float = 0.01,
                         silence_duration: float = 1.5,
                         max_recording_time: float = 30.0) -> VoiceActivityDetector:
    """Factory function with configurable parameters"""
    return VoiceActivityDetector(
        silence_threshold=silence_threshold,
        silence_duration=silence_duration,
        max_recording_time=max_recording_time
    )


if __name__ == "__main__":
    print("Testing Voice Activity Detection")
    print("=" * 35)
    
    # Test different sensitivity levels
    configs = [
        {"name": "Sensitive", "threshold": 0.005, "duration": 1.0},
        {"name": "Normal", "threshold": 0.01, "duration": 1.5},
        {"name": "Patient", "threshold": 0.02, "duration": 2.0}
    ]
    
    print("Available configurations:")
    for i, config in enumerate(configs):
        print(f"{i+1}. {config['name']}: threshold={config['threshold']}, pause={config['duration']}s")
    
    try:
        choice = int(input("Choose config (1-3): ")) - 1
        selected = configs[choice]
    except (ValueError, IndexError):
        selected = configs[1]  # Default to normal
    
    print(f"\nUsing {selected['name']} configuration")
    
    vad = create_voice_detector(
        silence_threshold=selected['threshold'],
        silence_duration=selected['duration']
    )
    
    print("\nTest: Speak naturally and I'll detect when you finish...")
    print("Press Ctrl+C to exit")
    
    try:
        while True:
            input("\nPress Enter to start recording: ")
            
            # Test recording
            audio = vad.record_until_silence()
            
            if len(audio) > 0:
                stats = vad.get_recording_stats()
                print(f"Recording stats: {stats}")
                print("✅ Would now process this audio for transcription")
            else:
                print("❌ No audio recorded")
                
    except KeyboardInterrupt:
        print("\n👋 Voice activity detection test complete!")
