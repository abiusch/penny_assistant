#!/usr/bin/env python3
"""
Prosody-Based Emotion Detection for Penny
Voice-based emotion enhancement using tone, pace, and pauses
"""

try:
    import numpy as np
    import librosa
    import scipy.signal
    AUDIO_AVAILABLE = True
except ImportError:
    AUDIO_AVAILABLE = False
    print("⚠️ Audio processing libraries not available. Using simulated prosody analysis.")
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import json
import sqlite3
from datetime import datetime
import io
import wave

class ProsodyFeature(Enum):
    PITCH = "pitch"
    PITCH_VARIANCE = "pitch_variance"
    SPEAKING_RATE = "speaking_rate"
    PAUSE_DURATION = "pause_duration"
    PAUSE_FREQUENCY = "pause_frequency"
    VOLUME = "volume"
    VOLUME_VARIANCE = "volume_variance"
    VOICE_QUALITY = "voice_quality"

class EmotionIntensity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    EXTREME = "extreme"

@dataclass
class ProsodyProfile:
    """Prosodic features extracted from audio"""
    pitch_mean: float
    pitch_std: float
    speaking_rate: float  # words per minute or syllables per second
    pause_duration_mean: float
    pause_frequency: float  # pauses per minute
    volume_mean: float
    volume_std: float
    voice_quality_score: float  # 0-1, higher = clearer/more stable
    audio_duration: float

@dataclass
class EmotionPrediction:
    """Emotion prediction from prosody"""
    primary_emotion: str
    confidence: float
    intensity: EmotionIntensity
    alternative_emotions: List[Tuple[str, float]]  # (emotion, confidence)
    prosody_indicators: Dict[str, str]  # feature -> interpretation

@dataclass
class VoiceContext:
    """Contextual information about voice sample"""
    speaker: str
    timestamp: datetime
    conversation_context: str
    background_noise_level: float
    audio_quality_score: float

class ProsodyEmotionDetector:
    """Detects emotions from voice prosody patterns"""

    def __init__(self, db_path: str = "prosody_emotions.db"):
        self.db_path = db_path

        # Initialize emotion-prosody mappings based on research
        self.emotion_prosody_patterns = {
            "happy": {
                "pitch_mean": (200, 350),  # Hz, higher than neutral
                "pitch_variance": (50, 150),  # Higher variance
                "speaking_rate": (4.5, 6.5),  # syllables/second, faster
                "pause_duration": (0.2, 0.8),  # seconds, shorter pauses
                "volume_mean": (0.6, 0.9),  # normalized, louder
                "voice_quality": (0.7, 1.0)  # clearer, more resonant
            },
            "sad": {
                "pitch_mean": (120, 200),  # Lower pitch
                "pitch_variance": (20, 60),  # Less variance
                "speaking_rate": (2.5, 4.0),  # Slower
                "pause_duration": (0.8, 2.5),  # Longer pauses
                "volume_mean": (0.3, 0.6),  # Quieter
                "voice_quality": (0.3, 0.7)  # Less clear, breathier
            },
            "angry": {
                "pitch_mean": (180, 280),  # Variable, can be high or low
                "pitch_variance": (80, 200),  # High variance
                "speaking_rate": (4.0, 7.0),  # Can be fast or choppy
                "pause_duration": (0.1, 0.6),  # Short, sharp pauses
                "volume_mean": (0.7, 1.0),  # Loud
                "voice_quality": (0.4, 0.8)  # Tense, strained
            },
            "frustrated": {
                "pitch_mean": (160, 250),  # Slightly elevated
                "pitch_variance": (60, 120),  # Moderate variance
                "speaking_rate": (3.5, 5.5),  # Moderately fast
                "pause_duration": (0.3, 1.2),  # Moderate pauses
                "volume_mean": (0.5, 0.8),  # Moderate to loud
                "voice_quality": (0.5, 0.8)  # Slightly tense
            },
            "excited": {
                "pitch_mean": (220, 380),  # High pitch
                "pitch_variance": (80, 180),  # High variance
                "speaking_rate": (5.0, 7.5),  # Fast
                "pause_duration": (0.1, 0.5),  # Short pauses
                "volume_mean": (0.7, 1.0),  # Loud
                "voice_quality": (0.8, 1.0)  # Clear, energetic
            },
            "anxious": {
                "pitch_mean": (180, 280),  # Elevated pitch
                "pitch_variance": (40, 100),  # Moderate variance
                "speaking_rate": (3.0, 5.5),  # Variable, often fast
                "pause_duration": (0.2, 1.5),  # Frequent short pauses
                "volume_mean": (0.4, 0.7),  # Moderate
                "voice_quality": (0.4, 0.7)  # Breathy, less stable
            },
            "calm": {
                "pitch_mean": (150, 220),  # Neutral to low
                "pitch_variance": (20, 50),  # Low variance
                "speaking_rate": (3.5, 4.5),  # Steady, moderate
                "pause_duration": (0.5, 1.5),  # Natural pauses
                "volume_mean": (0.5, 0.7),  # Moderate
                "voice_quality": (0.7, 1.0)  # Clear, stable
            },
            "tired": {
                "pitch_mean": (120, 180),  # Lower pitch
                "pitch_variance": (15, 40),  # Low variance
                "speaking_rate": (2.0, 3.5),  # Slow
                "pause_duration": (1.0, 3.0),  # Long pauses
                "volume_mean": (0.3, 0.5),  # Quiet
                "voice_quality": (0.3, 0.6)  # Breathy, less energy
            }
        }

        # Baseline/neutral ranges for comparison
        self.neutral_ranges = {
            "pitch_mean": (160, 220),
            "pitch_variance": (30, 70),
            "speaking_rate": (3.5, 4.5),
            "pause_duration": (0.5, 1.5),
            "volume_mean": (0.5, 0.7),
            "voice_quality": (0.6, 0.8)
        }

        # Initialize database
        self._init_database()

    def _init_database(self):
        """Initialize database for prosody tracking"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Prosody features table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS prosody_features (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                speaker TEXT,
                pitch_mean REAL,
                pitch_std REAL,
                speaking_rate REAL,
                pause_duration_mean REAL,
                pause_frequency REAL,
                volume_mean REAL,
                volume_std REAL,
                voice_quality_score REAL,
                audio_duration REAL
            )
        """)

        # Emotion predictions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS emotion_predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                speaker TEXT,
                primary_emotion TEXT,
                confidence REAL,
                intensity TEXT,
                alternative_emotions TEXT,
                prosody_indicators TEXT,
                conversation_context TEXT
            )
        """)

        conn.commit()
        conn.close()

    def extract_prosody_features(self, audio_data: bytes, sample_rate: int = 16000) -> ProsodyProfile:
        """Extract prosodic features from audio data"""

        if not AUDIO_AVAILABLE:
            # Return simulated prosody for testing
            return ProsodyProfile(
                pitch_mean=190, pitch_std=40, speaking_rate=4.0,
                pause_duration_mean=1.0, pause_frequency=20,
                volume_mean=0.6, volume_std=0.2,
                voice_quality_score=0.7, audio_duration=5.0
            )

        try:
            # Convert bytes to numpy array
            audio_array = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0

            # Basic audio properties
            duration = len(audio_array) / sample_rate

            # Extract pitch using librosa
            pitch, _ = librosa.core.piptrack(y=audio_array, sr=sample_rate, fmin=75, fmax=400)
            pitch_values = []

            for t in range(pitch.shape[1]):
                index = pitch[:, t].argmax()
                pitch_val = pitch[index, t]
                if pitch_val > 0:
                    pitch_values.append(pitch_val)

            if len(pitch_values) == 0:
                pitch_mean, pitch_std = 0, 0
            else:
                pitch_mean = np.mean(pitch_values)
                pitch_std = np.std(pitch_values)

            # Extract volume (RMS energy)
            frame_length = int(0.025 * sample_rate)  # 25ms frames
            hop_length = int(0.010 * sample_rate)    # 10ms hop

            rms = librosa.feature.rms(y=audio_array, frame_length=frame_length, hop_length=hop_length)[0]
            volume_mean = np.mean(rms)
            volume_std = np.std(rms)

            # Estimate speaking rate (simplified)
            # This would ideally use speech recognition or syllable detection
            # For now, we'll estimate based on energy changes
            energy_changes = np.diff(rms)
            speech_segments = np.where(np.abs(energy_changes) > np.std(energy_changes) * 0.5)[0]
            estimated_syllables = len(speech_segments) / 2  # rough estimate
            speaking_rate = estimated_syllables / duration if duration > 0 else 0

            # Detect pauses (segments with low energy)
            silence_threshold = np.mean(rms) * 0.1
            silent_frames = rms < silence_threshold

            # Find continuous silent segments
            pause_starts = []
            pause_ends = []
            in_pause = False

            for i, is_silent in enumerate(silent_frames):
                if is_silent and not in_pause:
                    pause_starts.append(i)
                    in_pause = True
                elif not is_silent and in_pause:
                    pause_ends.append(i)
                    in_pause = False

            # Calculate pause statistics
            if len(pause_starts) > 0 and len(pause_ends) > 0:
                pause_durations = []
                for start, end in zip(pause_starts, pause_ends[:len(pause_starts)]):
                    pause_duration = (end - start) * hop_length / sample_rate
                    if pause_duration > 0.1:  # Only count pauses > 100ms
                        pause_durations.append(pause_duration)

                pause_duration_mean = np.mean(pause_durations) if pause_durations else 0
                pause_frequency = len(pause_durations) / (duration / 60) if duration > 0 else 0  # per minute
            else:
                pause_duration_mean = 0
                pause_frequency = 0

            # Voice quality estimation (simplified)
            # Based on spectral characteristics and stability
            spectral_centroids = librosa.feature.spectral_centroid(y=audio_array, sr=sample_rate)[0]
            spectral_rolloff = librosa.feature.spectral_rolloff(y=audio_array, sr=sample_rate)[0]

            # Higher quality voice typically has:
            # - Stable spectral characteristics
            # - Good harmonic structure
            # - Consistent energy
            centroid_stability = 1.0 - min(np.std(spectral_centroids) / np.mean(spectral_centroids), 1.0)
            energy_stability = 1.0 - min(np.std(rms) / np.mean(rms), 1.0)
            voice_quality_score = (centroid_stability + energy_stability) / 2

            return ProsodyProfile(
                pitch_mean=pitch_mean,
                pitch_std=pitch_std,
                speaking_rate=speaking_rate,
                pause_duration_mean=pause_duration_mean,
                pause_frequency=pause_frequency,
                volume_mean=volume_mean,
                volume_std=volume_std,
                voice_quality_score=voice_quality_score,
                audio_duration=duration
            )

        except Exception as e:
            print(f"Error extracting prosody features: {e}")
            # Return default/neutral profile
            return ProsodyProfile(
                pitch_mean=190, pitch_std=40, speaking_rate=4.0,
                pause_duration_mean=1.0, pause_frequency=20,
                volume_mean=0.6, volume_std=0.2,
                voice_quality_score=0.7, audio_duration=0
            )

    def predict_emotion_from_prosody(self, prosody_profile: ProsodyProfile,
                                   context: VoiceContext = None) -> EmotionPrediction:
        """Predict emotion from prosodic features"""

        emotion_scores = {}

        # Calculate how well prosody matches each emotion pattern
        for emotion, patterns in self.emotion_prosody_patterns.items():
            score = 0
            matches = 0

            # Check each prosodic feature
            features_to_check = [
                ("pitch_mean", prosody_profile.pitch_mean),
                ("pitch_variance", prosody_profile.pitch_std),
                ("speaking_rate", prosody_profile.speaking_rate),
                ("pause_duration", prosody_profile.pause_duration_mean),
                ("volume_mean", prosody_profile.volume_mean),
                ("voice_quality", prosody_profile.voice_quality_score)
            ]

            for feature_name, feature_value in features_to_check:
                if feature_name in patterns:
                    min_val, max_val = patterns[feature_name]
                    if min_val <= feature_value <= max_val:
                        score += 1.0
                        matches += 1
                    else:
                        # Partial score based on distance from range
                        if feature_value < min_val:
                            distance = min_val - feature_value
                            range_size = max_val - min_val
                            partial_score = max(0, 1.0 - (distance / range_size))
                        else:  # feature_value > max_val
                            distance = feature_value - max_val
                            range_size = max_val - min_val
                            partial_score = max(0, 1.0 - (distance / range_size))
                        score += partial_score

            # Normalize score
            total_features = len(features_to_check)
            emotion_scores[emotion] = score / total_features if total_features > 0 else 0

        # Find primary emotion
        if emotion_scores:
            primary_emotion = max(emotion_scores, key=emotion_scores.get)
            confidence = emotion_scores[primary_emotion]

            # Get alternative emotions (top 3)
            sorted_emotions = sorted(emotion_scores.items(), key=lambda x: x[1], reverse=True)
            alternative_emotions = sorted_emotions[1:4]

            # Determine intensity based on how extreme the prosodic features are
            intensity = self._determine_intensity(prosody_profile, primary_emotion)

            # Generate prosody indicators
            prosody_indicators = self._generate_prosody_indicators(prosody_profile, primary_emotion)

        else:
            primary_emotion = "neutral"
            confidence = 0.5
            alternative_emotions = []
            intensity = EmotionIntensity.MEDIUM
            prosody_indicators = {}

        return EmotionPrediction(
            primary_emotion=primary_emotion,
            confidence=confidence,
            intensity=intensity,
            alternative_emotions=alternative_emotions,
            prosody_indicators=prosody_indicators
        )

    def _determine_intensity(self, prosody_profile: ProsodyProfile, emotion: str) -> EmotionIntensity:
        """Determine emotion intensity based on prosodic extremes"""

        if emotion not in self.emotion_prosody_patterns:
            return EmotionIntensity.MEDIUM

        pattern = self.emotion_prosody_patterns[emotion]
        neutral = self.neutral_ranges

        # Calculate how far features deviate from neutral
        deviations = []

        # Pitch deviation
        if "pitch_mean" in pattern:
            neutral_pitch = (neutral["pitch_mean"][0] + neutral["pitch_mean"][1]) / 2
            deviation = abs(prosody_profile.pitch_mean - neutral_pitch) / neutral_pitch
            deviations.append(deviation)

        # Volume deviation
        if "volume_mean" in pattern:
            neutral_volume = (neutral["volume_mean"][0] + neutral["volume_mean"][1]) / 2
            deviation = abs(prosody_profile.volume_mean - neutral_volume) / neutral_volume
            deviations.append(deviation)

        # Speaking rate deviation
        if "speaking_rate" in pattern:
            neutral_rate = (neutral["speaking_rate"][0] + neutral["speaking_rate"][1]) / 2
            deviation = abs(prosody_profile.speaking_rate - neutral_rate) / neutral_rate
            deviations.append(deviation)

        # Average deviation
        if AUDIO_AVAILABLE:
            avg_deviation = np.mean(deviations) if deviations else 0
        else:
            avg_deviation = sum(deviations) / len(deviations) if deviations else 0

        if avg_deviation > 0.5:
            return EmotionIntensity.EXTREME
        elif avg_deviation > 0.3:
            return EmotionIntensity.HIGH
        elif avg_deviation > 0.15:
            return EmotionIntensity.MEDIUM
        else:
            return EmotionIntensity.LOW

    def _generate_prosody_indicators(self, prosody_profile: ProsodyProfile, emotion: str) -> Dict[str, str]:
        """Generate human-readable prosody indicators"""

        indicators = {}

        # Pitch indicators
        if prosody_profile.pitch_mean > 250:
            indicators["pitch"] = "high pitch (excited/stressed)"
        elif prosody_profile.pitch_mean < 150:
            indicators["pitch"] = "low pitch (sad/tired)"
        else:
            indicators["pitch"] = "normal pitch range"

        # Speaking rate indicators
        if prosody_profile.speaking_rate > 5.5:
            indicators["speaking_rate"] = "fast speech (excited/anxious)"
        elif prosody_profile.speaking_rate < 3.0:
            indicators["speaking_rate"] = "slow speech (sad/tired)"
        else:
            indicators["speaking_rate"] = "normal speaking pace"

        # Volume indicators
        if prosody_profile.volume_mean > 0.8:
            indicators["volume"] = "loud voice (excited/angry)"
        elif prosody_profile.volume_mean < 0.4:
            indicators["volume"] = "quiet voice (sad/tired)"
        else:
            indicators["volume"] = "normal volume"

        # Pause indicators
        if prosody_profile.pause_duration_mean > 2.0:
            indicators["pauses"] = "long pauses (thinking/tired)"
        elif prosody_profile.pause_duration_mean < 0.3:
            indicators["pauses"] = "short pauses (excited/rushed)"
        else:
            indicators["pauses"] = "natural pause patterns"

        # Voice quality indicators
        if prosody_profile.voice_quality_score > 0.8:
            indicators["voice_quality"] = "clear, stable voice"
        elif prosody_profile.voice_quality_score < 0.5:
            indicators["voice_quality"] = "breathy or strained voice"
        else:
            indicators["voice_quality"] = "normal voice quality"

        return indicators

    def analyze_voice_emotion(self, audio_data: bytes, context: VoiceContext = None,
                            sample_rate: int = 16000) -> Tuple[ProsodyProfile, EmotionPrediction]:
        """Complete voice emotion analysis"""

        # Extract prosodic features
        prosody_profile = self.extract_prosody_features(audio_data, sample_rate)

        # Predict emotion
        emotion_prediction = self.predict_emotion_from_prosody(prosody_profile, context)

        # Store results in database
        self._store_analysis_results(prosody_profile, emotion_prediction, context)

        return prosody_profile, emotion_prediction

    def _store_analysis_results(self, prosody_profile: ProsodyProfile,
                              emotion_prediction: EmotionPrediction,
                              context: VoiceContext = None):
        """Store analysis results in database"""

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        timestamp = datetime.now().isoformat()
        speaker = context.speaker if context else "unknown"

        # Store prosody features
        cursor.execute("""
            INSERT INTO prosody_features
            (timestamp, speaker, pitch_mean, pitch_std, speaking_rate, pause_duration_mean,
             pause_frequency, volume_mean, volume_std, voice_quality_score, audio_duration)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            timestamp, speaker, prosody_profile.pitch_mean, prosody_profile.pitch_std,
            prosody_profile.speaking_rate, prosody_profile.pause_duration_mean,
            prosody_profile.pause_frequency, prosody_profile.volume_mean,
            prosody_profile.volume_std, prosody_profile.voice_quality_score,
            prosody_profile.audio_duration
        ))

        # Store emotion prediction
        cursor.execute("""
            INSERT INTO emotion_predictions
            (timestamp, speaker, primary_emotion, confidence, intensity,
             alternative_emotions, prosody_indicators, conversation_context)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            timestamp, speaker, emotion_prediction.primary_emotion,
            emotion_prediction.confidence, emotion_prediction.intensity.value,
            json.dumps(emotion_prediction.alternative_emotions),
            json.dumps(emotion_prediction.prosody_indicators),
            context.conversation_context if context else ""
        ))

        conn.commit()
        conn.close()

    def get_emotion_history(self, speaker: str = None, days: int = 7) -> List[Dict[str, Any]]:
        """Get emotion history for analysis"""

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        where_clause = "WHERE timestamp > datetime('now', '-{} days')".format(days)
        if speaker:
            where_clause += f" AND speaker = '{speaker}'"

        cursor.execute(f"""
            SELECT * FROM emotion_predictions {where_clause}
            ORDER BY timestamp DESC
        """)

        results = []
        for row in cursor.fetchall():
            results.append({
                "timestamp": row[1],
                "speaker": row[2],
                "primary_emotion": row[3],
                "confidence": row[4],
                "intensity": row[5],
                "alternative_emotions": json.loads(row[6]) if row[6] else [],
                "prosody_indicators": json.loads(row[7]) if row[7] else {},
                "conversation_context": row[8]
            })

        conn.close()
        return results

def create_prosody_emotion_detector(db_path: str = "prosody_emotions.db") -> ProsodyEmotionDetector:
    """Factory function"""
    return ProsodyEmotionDetector(db_path)

def simulate_audio_analysis():
    """Simulate audio analysis for testing (since we don't have real audio)"""

    # Create detector
    detector = create_prosody_emotion_detector("test_prosody.db")

    # Simulate different emotional prosody profiles
    test_profiles = [
        # Happy/Excited
        ProsodyProfile(
            pitch_mean=280, pitch_std=80, speaking_rate=6.0,
            pause_duration_mean=0.4, pause_frequency=25,
            volume_mean=0.8, volume_std=0.15,
            voice_quality_score=0.9, audio_duration=5.0
        ),
        # Sad/Tired
        ProsodyProfile(
            pitch_mean=140, pitch_std=25, speaking_rate=2.8,
            pause_duration_mean=2.2, pause_frequency=15,
            volume_mean=0.4, volume_std=0.1,
            voice_quality_score=0.5, audio_duration=6.0
        ),
        # Angry/Frustrated
        ProsodyProfile(
            pitch_mean=220, pitch_std=120, speaking_rate=5.5,
            pause_duration_mean=0.3, pause_frequency=30,
            volume_mean=0.9, volume_std=0.25,
            voice_quality_score=0.6, audio_duration=4.0
        ),
        # Anxious
        ProsodyProfile(
            pitch_mean=250, pitch_std=60, speaking_rate=5.2,
            pause_duration_mean=0.8, pause_frequency=35,
            volume_mean=0.6, volume_std=0.2,
            voice_quality_score=0.5, audio_duration=7.0
        )
    ]

    test_contexts = [
        VoiceContext("CJ", datetime.now(), "discussing project success", 0.1, 0.9),
        VoiceContext("CJ", datetime.now(), "talking about personal issues", 0.05, 0.95),
        VoiceContext("CJ", datetime.now(), "complaining about work problem", 0.15, 0.8),
        VoiceContext("CJ", datetime.now(), "worried about deadline", 0.1, 0.85)
    ]

    print("🎙️ Prosody-Based Emotion Detection")
    print("=" * 60)

    print("\n🔬 Emotion Analysis from Simulated Voice Prosody:")

    for i, (profile, context) in enumerate(zip(test_profiles, test_contexts), 1):
        print(f"\n{i}. CONTEXT: {context.conversation_context}")
        print("-" * 40)

        # Predict emotion
        emotion_prediction = detector.predict_emotion_from_prosody(profile, context)

        print(f"Primary Emotion: {emotion_prediction.primary_emotion} ({emotion_prediction.intensity.value})")
        print(f"Confidence: {emotion_prediction.confidence:.2f}")

        if emotion_prediction.alternative_emotions:
            print("Alternative emotions:")
            for emotion, conf in emotion_prediction.alternative_emotions[:2]:
                print(f"  • {emotion}: {conf:.2f}")

        print("Prosody indicators:")
        for feature, indicator in emotion_prediction.prosody_indicators.items():
            print(f"  • {feature}: {indicator}")

        # Store in database (simulate)
        detector._store_analysis_results(profile, emotion_prediction, context)

    # Show emotion history
    print(f"\n📊 Emotion History:")
    history = detector.get_emotion_history("CJ")
    for entry in history[:3]:  # Show last 3
        print(f"  {entry['timestamp'][:19]}: {entry['primary_emotion']} ({entry['intensity']}) - {entry['confidence']:.2f}")

if __name__ == "__main__":
    simulate_audio_analysis()

    # Clean up
    import os
    if os.path.exists("test_prosody.db"):
        os.remove("test_prosody.db")
    print("\n✅ Prosody emotion detection test completed!")