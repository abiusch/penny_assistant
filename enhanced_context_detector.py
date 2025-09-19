#!/usr/bin/env python3
"""
Phase 1.5 Days 4-7: Enhanced Context Detection System
Expands emotion vocabulary and adds multi-layered context analysis
"""

from enum import Enum
from dataclasses import dataclass
from typing import Dict, List, Optional

class EmotionIntensity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    EXTREME = "extreme"

@dataclass 
class EmotionProfile:
    primary_emotion: str
    intensity: EmotionIntensity
    compound_emotions: List[str]
    confidence: float

@dataclass
class ContextAnalysis:
    topic: str
    emotion_profile: EmotionProfile
    social_context: str
    communication_preference: str
    inference_confidence: float

class EnhancedContextDetector:
    def __init__(self):
        self.emotion_patterns = {
            "frustrated": {
                "low": ["a bit annoying", "slightly bothered"],
                "medium": ["frustrated", "annoying", "bothered", "stuck"],
                "high": ["really frustrated", "driving me crazy", "fed up"],
                "extreme": ["absolutely livid", "furious", "can't take it anymore"],
                "compound_indicators": ["but determined", "yet hopeful", "still trying"]
            },
            "excited": {
                "low": ["interested", "curious", "looking forward"],
                "medium": ["excited", "thrilled", "pumped"],
                "high": ["super excited", "absolutely thrilled"],
                "extreme": ["ecstatic", "beside myself with excitement"],
                "compound_indicators": ["but nervous", "yet worried", "with anxiety"]
            },
            "overwhelmed": {
                "low": ["bit much", "lot to handle"],
                "medium": ["overwhelmed", "drowning", "too much"],
                "high": ["completely overwhelmed", "totally swamped"],
                "extreme": ["absolutely buried", "breaking point"],
                "compound_indicators": ["but managing", "yet determined", "still fighting"]
            },
            "determined": {
                "low": ["motivated", "focused", "ready to try"],
                "medium": ["determined", "committed", "won't give up"],
                "high": ["absolutely determined", "completely focused"],
                "extreme": ["obsessively focused", "laser determined"],
                "compound_indicators": ["but tired", "yet frustrated", "with doubt"]
            },
            "anxious": {
                "low": ["a bit worried", "slightly concerned"],
                "medium": ["anxious", "worried", "nervous", "stressed"],
                "high": ["really anxious", "very worried", "panicking"],
                "extreme": ["terrified", "paralyzed with anxiety"],
                "compound_indicators": ["but excited", "yet hopeful", "still optimistic"]
            }
        }
    
    def analyze_comprehensive_context(self, user_input: str) -> ContextAnalysis:
        """Perform enhanced context analysis"""
        
        emotion_profile = self._detect_emotion_profile(user_input)
        topic = self._detect_topic(user_input)
        social_context = self._detect_social_context(user_input)
        communication_preference = self._infer_communication_preference(emotion_profile, social_context)
        confidence = emotion_profile.confidence
        
        return ContextAnalysis(
            topic=topic,
            emotion_profile=emotion_profile,
            social_context=social_context,
            communication_preference=communication_preference,
            inference_confidence=confidence
        )
    
    def _detect_emotion_profile(self, text: str) -> EmotionProfile:
        """Detect emotions with intensity and compounds"""
        
        text_lower = text.lower()
        detected_emotions = []
        compound_emotions = []
        
        for emotion, patterns in self.emotion_patterns.items():
            emotion_detected = False
            
            # Check intensity levels (extreme to low)
            for intensity_level in ["extreme", "high", "medium", "low"]:
                if any(pattern in text_lower for pattern in patterns[intensity_level]):
                    detected_emotions.append((emotion, EmotionIntensity(intensity_level)))
                    emotion_detected = True
                    break
            
            # Check for compound emotion indicators
            if emotion_detected:
                compound_indicators = patterns.get("compound_indicators", [])
                for indicator in compound_indicators:
                    if indicator in text_lower:
                        compound_emotions.append(f"{emotion}_{indicator.replace(' ', '_')}")
        
        # Determine primary emotion
        if detected_emotions:
            # Sort by intensity (extreme > high > medium > low)
            intensity_order = {"extreme": 4, "high": 3, "medium": 2, "low": 1}
            detected_emotions.sort(key=lambda x: intensity_order[x[1].value], reverse=True)
            
            primary_emotion = detected_emotions[0][0]
            primary_intensity = detected_emotions[0][1]
        else:
            primary_emotion = "neutral"
            primary_intensity = EmotionIntensity.LOW
        
        # Calculate confidence
        confidence = min(len(detected_emotions) * 0.4, 1.0)
        
        return EmotionProfile(
            primary_emotion=primary_emotion,
            intensity=primary_intensity,
            compound_emotions=compound_emotions,
            confidence=confidence
        )
    
    def _detect_topic(self, text: str) -> str:
        """Detect conversation topic"""
        
        text_lower = text.lower()
        
        topic_patterns = {
            "programming": ["code", "bug", "debug", "function", "api", "programming"],
            "work": ["meeting", "project", "deadline", "team", "manager", "work"],
            "personal": ["feeling", "think", "friend", "relationship", "family"]
        }
        
        for topic, patterns in topic_patterns.items():
            if any(pattern in text_lower for pattern in patterns):
                return topic
        
        return "general"
    
    def _detect_social_context(self, text: str) -> str:
        """Detect social situation"""
        
        text_lower = text.lower()
        
        if any(word in text_lower for word in ["problem", "issue", "bug", "error", "fix"]):
            return "problem_solving"
        elif any(word in text_lower for word in ["awesome", "amazing", "success", "great"]):
            return "celebration"
        elif any(word in text_lower for word in ["ugh", "argh", "annoying", "hate"]):
            return "venting"
        elif any(word in text_lower for word in ["urgent", "emergency", "critical", "help"]):
            return "crisis"
        elif any(word in text_lower for word in ["josh", "reneille"]):
            return "friend_discussion"
        else:
            return "casual_chat"
    
    def _infer_communication_preference(self, emotion_profile: EmotionProfile, social_context: str) -> str:
        """Infer preferred communication style"""
        
        # High intensity negative emotions need calm support
        if emotion_profile.intensity in [EmotionIntensity.HIGH, EmotionIntensity.EXTREME]:
            if emotion_profile.primary_emotion in ["frustrated", "overwhelmed", "anxious"]:
                return "calm_supportive"
            elif emotion_profile.primary_emotion in ["excited"]:
                return "enthusiastic_matching"
        
        # Context-based preferences
        if social_context == "problem_solving":
            return "professional_structured"
        elif social_context == "venting":
            return "empathetic_listening"
        elif social_context == "celebration":
            return "enthusiastic_celebratory"
        elif social_context == "friend_discussion":
            return "casual_humor"
        
        return "balanced_responsive"

def create_enhanced_context_detector():
    """Factory function"""
    return EnhancedContextDetector()

if __name__ == "__main__":
    # Test the enhanced context detection
    detector = create_enhanced_context_detector()
    
    test_inputs = [
        "I'm really frustrated with this bug but determined to fix it",
        "Josh is being weird about the project deadline and it's making me anxious", 
        "Super excited about the new feature launch but nervous about user reception",
        "Completely overwhelmed with this workload yet still trying to push through",
        "Had an amazing meeting with the team today - everything went perfectly!"
    ]
    
    print("Enhanced Context Detection Testing")
    print("=" * 60)
    
    for i, test_input in enumerate(test_inputs, 1):
        print(f"\n{i}. INPUT: {test_input}")
        print("-" * 40)
        
        analysis = detector.analyze_comprehensive_context(test_input)
        
        print(f"Topic: {analysis.topic}")
        print(f"Primary Emotion: {analysis.emotion_profile.primary_emotion} ({analysis.emotion_profile.intensity.value})")
        if analysis.emotion_profile.compound_emotions:
            print(f"Compound Emotions: {', '.join(analysis.emotion_profile.compound_emotions)}")
        print(f"Social Context: {analysis.social_context}")
        print(f"Communication Preference: {analysis.communication_preference}")
        print(f"Confidence: {analysis.inference_confidence:.2f}")
