#!/usr/bin/env python3
"""
Social Intelligence Integration for Penny
Integrates advanced social awareness with voice interface
"""

import sys
import os
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime
import json
import asyncio
import threading

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from advanced_social_intelligence import AdvancedSocialIntelligence, SocialSituation
from relationship_dynamics_engine import RelationshipDynamicsEngine, RelationshipInsight
from prosody_emotion_detector import ProsodyEmotionDetector, VoiceContext, EmotionPrediction
from enhanced_context_detector import EnhancedContextDetector, ContextAnalysis
from calibrated_adaptive_sass_enhanced_penny import CalibratedAdaptiveSassEnhancedPenny

@dataclass
class SocialIntelligenceAnalysis:
    """Complete social intelligence analysis"""
    social_situation: SocialSituation
    relationship_dynamics: Dict[str, Any]
    voice_emotion: Optional[EmotionPrediction]
    enhanced_context: ContextAnalysis
    recommended_response_style: str
    confidence_score: float
    social_insights: List[str]

@dataclass
class VoiceInteractionContext:
    """Context for voice-based social interaction"""
    audio_data: Optional[bytes]
    transcribed_text: str
    speaker: str
    timestamp: datetime
    conversation_history: List[Dict[str, str]]
    background_context: str

class SocialIntelligenceIntegration:
    """Integrated social intelligence system for voice interactions"""

    def __init__(self, memory_db_path: str = "penny_memory.db"):
        print("🧠 Initializing Social Intelligence Integration...")

        # Initialize core components
        self.social_ai = AdvancedSocialIntelligence("social_intelligence.db")
        self.relationship_engine = RelationshipDynamicsEngine("relationship_dynamics.db")
        self.prosody_detector = ProsodyEmotionDetector("prosody_emotions.db")
        self.context_detector = EnhancedContextDetector()
        self.penny = CalibratedAdaptiveSassEnhancedPenny(memory_db_path)

        # Initialize known relationships (Josh and Reneille from requirements)
        self._initialize_known_relationships()

        print("✅ Social Intelligence Integration initialized!")

    def _initialize_known_relationships(self):
        """Initialize known relationships from requirements"""

        # Add Josh profile
        self.social_ai.add_person_profile(
            "Josh", "friend", "analytical",
            stress_indicators=["quiet", "short responses", "works late", "avoids meetings"],
            support_preferences=["practical solutions", "space to think", "minimal pressure"]
        )

        # Add Reneille profile
        self.social_ai.add_person_profile(
            "Reneille", "friend", "emotional",
            stress_indicators=["talks fast", "lots of questions", "seeks validation", "overthinking"],
            support_preferences=["empathetic listening", "validation", "brainstorming", "emotional support"]
        )

        # Add Josh-Reneille relationship dynamic
        self.social_ai.add_relationship_dynamic(
            "Josh", "Reneille", "colleagues", "equal", "complementary"
        )

        print("📋 Initialized known relationships: Josh, Reneille")

    async def analyze_voice_interaction(self, interaction_context: VoiceInteractionContext) -> SocialIntelligenceAnalysis:
        """Perform comprehensive social intelligence analysis of voice interaction"""

        print(f"🔍 Analyzing social context for: {interaction_context.transcribed_text[:50]}...")

        # 1. Enhanced context detection
        enhanced_context = self.context_detector.analyze_comprehensive_context(
            interaction_context.transcribed_text
        )

        # 2. Social situation analysis
        social_situation = self.social_ai.analyze_social_situation(
            interaction_context.transcribed_text,
            {
                "speaker": interaction_context.speaker,
                "timestamp": interaction_context.timestamp.isoformat(),
                "background": interaction_context.background_context
            }
        )

        # 3. Relationship dynamics analysis
        relationship_dynamics = self.relationship_engine.analyze_relationship_dynamics(
            interaction_context.transcribed_text,
            {
                "speaker": interaction_context.speaker,
                "conversation_history": interaction_context.conversation_history
            }
        )

        # 4. Voice emotion analysis (if audio available)
        voice_emotion = None
        if interaction_context.audio_data:
            voice_context = VoiceContext(
                speaker=interaction_context.speaker,
                timestamp=interaction_context.timestamp,
                conversation_context=interaction_context.transcribed_text[:100],
                background_noise_level=0.1,  # Would be detected from audio
                audio_quality_score=0.8      # Would be assessed from audio
            )

            try:
                _, voice_emotion = self.prosody_detector.analyze_voice_emotion(
                    interaction_context.audio_data, voice_context
                )
            except Exception as e:
                print(f"⚠️ Voice emotion analysis failed: {e}")

        # 5. Generate comprehensive response recommendation
        recommended_style, confidence, insights = self._generate_response_recommendation(
            enhanced_context, social_situation, relationship_dynamics, voice_emotion
        )

        return SocialIntelligenceAnalysis(
            social_situation=social_situation,
            relationship_dynamics=relationship_dynamics,
            voice_emotion=voice_emotion,
            enhanced_context=enhanced_context,
            recommended_response_style=recommended_style,
            confidence_score=confidence,
            social_insights=insights
        )

    def _generate_response_recommendation(self, enhanced_context: ContextAnalysis,
                                        social_situation: SocialSituation,
                                        relationship_dynamics: Dict[str, Any],
                                        voice_emotion: Optional[EmotionPrediction]) -> Tuple[str, float, List[str]]:
        """Generate comprehensive response recommendation"""

        recommendations = []
        insights = []
        confidence_factors = []

        # Base recommendation on enhanced context
        base_style = enhanced_context.communication_preference
        recommendations.append(f"Context-based: {base_style}")
        confidence_factors.append(enhanced_context.inference_confidence)

        # Layer in social situation analysis
        if social_situation.confidence_level > 0.6:
            recommendations.append(f"Social situation: {social_situation.suggested_approach}")
            insights.append(f"Social context: {social_situation.primary_context.value}")
            confidence_factors.append(social_situation.confidence_level)

        # Factor in relationship dynamics
        if relationship_dynamics.get("people_involved"):
            people = relationship_dynamics["people_involved"]
            insights.append(f"People involved: {', '.join(people)}")

            # Check for relationship-specific adjustments
            if "relationship_insights" in relationship_dynamics:
                rel_insights = relationship_dynamics["relationship_insights"]

                # If someone needs attention
                if rel_insights.get("relationship_status") == "needs_attention":
                    recommendations.append("Extra supportive approach needed")
                    insights.append("Relationship needs attention")

                # If there are tensions
                if "relationships" in rel_insights:
                    tense_relationships = [
                        pair for pair, data in rel_insights["relationships"].items()
                        if data["status"] == "tense"
                    ]
                    if tense_relationships:
                        recommendations.append("Address interpersonal tensions carefully")
                        insights.append(f"Tension detected: {', '.join(tense_relationships)}")

            confidence_factors.append(0.7)  # Moderate confidence for relationship analysis

        # Factor in voice emotion if available
        if voice_emotion and voice_emotion.confidence > 0.5:
            emotion = voice_emotion.primary_emotion
            intensity = voice_emotion.intensity.value

            if emotion in ["frustrated", "angry"] and intensity in ["high", "extreme"]:
                recommendations.append("Use calm, de-escalating tone")
                insights.append(f"Voice emotion: {emotion} ({intensity})")
            elif emotion in ["sad", "tired"] and intensity in ["medium", "high"]:
                recommendations.append("Use gentle, supportive tone")
                insights.append(f"Voice emotion: {emotion} ({intensity})")
            elif emotion in ["excited", "happy"]:
                recommendations.append("Match positive energy appropriately")
                insights.append(f"Voice emotion: {emotion} ({intensity})")
            elif emotion == "anxious":
                recommendations.append("Provide reassurance and structure")
                insights.append(f"Voice emotion: {emotion} ({intensity})")

            confidence_factors.append(voice_emotion.confidence)

        # Synthesize final recommendation
        if "calm, de-escalating" in str(recommendations):
            final_style = "calm_supportive"
        elif "gentle, supportive" in str(recommendations):
            final_style = "gentle_empathetic"
        elif "extra supportive" in str(recommendations).lower():
            final_style = "extra_supportive"
        elif "address tensions" in str(recommendations).lower():
            final_style = "diplomatic_careful"
        elif enhanced_context.emotion_profile.primary_emotion in ["frustrated", "overwhelmed"]:
            final_style = "patient_helpful"
        elif enhanced_context.emotion_profile.primary_emotion == "excited":
            final_style = "enthusiastic_matching"
        else:
            final_style = base_style

        # Calculate overall confidence
        overall_confidence = sum(confidence_factors) / len(confidence_factors) if confidence_factors else 0.5

        return final_style, overall_confidence, insights

    def generate_socially_intelligent_response(self, interaction_context: VoiceInteractionContext) -> Dict[str, Any]:
        """Generate a socially intelligent response using all available information"""

        # Perform social intelligence analysis
        analysis = asyncio.run(self.analyze_voice_interaction(interaction_context))

        # Prepare context for Penny
        penny_context = {
            "topic": analysis.enhanced_context.topic,
            "emotion": analysis.enhanced_context.emotion_profile.primary_emotion,
            "social_context": analysis.social_situation.primary_context.value,
            "participants": analysis.social_situation.participants,
            "communication_preference": analysis.recommended_response_style,
            "relationship_factors": analysis.relationship_dynamics.get("recommendations", []),
            "voice_emotion": analysis.voice_emotion.primary_emotion if analysis.voice_emotion else None,
            "social_insights": analysis.social_insights,
            "confidence": analysis.confidence_score
        }

        # Generate response using calibrated Penny
        response = self.penny.generate_adaptive_sass_response(
            interaction_context.transcribed_text,
            penny_context
        )

        # Learn from the interaction
        self._learn_from_interaction(interaction_context, analysis, response)

        return {
            "response": response,
            "social_analysis": analysis,
            "confidence": analysis.confidence_score,
            "insights": analysis.social_insights,
            "response_style": analysis.recommended_response_style
        }

    def _learn_from_interaction(self, interaction_context: VoiceInteractionContext,
                              analysis: SocialIntelligenceAnalysis, response: str):
        """Learn from the interaction to improve future responses"""

        # Update social AI learning
        self.social_ai.learn_from_interaction(
            interaction_context.transcribed_text, response
        )

        # Store interaction for analysis
        try:
            # This would ideally include feedback mechanisms
            print(f"📚 Learning from interaction with {len(analysis.social_situation.participants)} participants")
        except Exception as e:
            print(f"⚠️ Learning update failed: {e}")

    def get_social_intelligence_status(self) -> Dict[str, Any]:
        """Get status of social intelligence systems"""

        return {
            "social_ai": {
                "people_known": len(self.social_ai.person_profiles),
                "relationships_tracked": len(self.social_ai.relationship_dynamics)
            },
            "relationship_engine": {
                "network_summary": self.relationship_engine.get_network_summary()
            },
            "prosody_detector": {
                "recent_emotions": len(self.prosody_detector.get_emotion_history(days=1))
            },
            "penny_integration": {
                "self_awareness_calibration": True,
                "adaptive_sass": True,
                "voice_ready": True
            }
        }

    def simulate_voice_interaction(self, text_input: str, speaker: str = "CJ",
                                 background_context: str = "casual conversation") -> Dict[str, Any]:
        """Simulate a voice interaction for testing"""

        interaction_context = VoiceInteractionContext(
            audio_data=None,  # No actual audio for simulation
            transcribed_text=text_input,
            speaker=speaker,
            timestamp=datetime.now(),
            conversation_history=[],
            background_context=background_context
        )

        return self.generate_socially_intelligent_response(interaction_context)

def create_social_intelligence_integration(memory_db_path: str = "penny_memory.db") -> SocialIntelligenceIntegration:
    """Factory function"""
    return SocialIntelligenceIntegration(memory_db_path)

if __name__ == "__main__":
    # Demo and testing
    print("🧠 Social Intelligence Integration Demo")
    print("=" * 60)

    # Create integrated system
    social_system = create_social_intelligence_integration("test_social_integration.db")

    # Test scenarios with varying social complexity
    test_scenarios = [
        {
            "text": "Josh is being weird about the project deadline and it's making me anxious",
            "context": "work discussion"
        },
        {
            "text": "Reneille and Josh had a disagreement in the meeting today about the feature scope",
            "context": "team conflict"
        },
        {
            "text": "I'm really excited about the new AI features we're building!",
            "context": "project enthusiasm"
        },
        {
            "text": "I'm feeling overwhelmed with the workload and Josh isn't responding to my messages",
            "context": "stress and communication issues"
        },
        {
            "text": "The team celebration went great - everyone was so happy with the launch results",
            "context": "team celebration"
        }
    ]

    print("\n🔬 Social Intelligence Analysis Tests:")

    for i, scenario in enumerate(test_scenarios, 1):
        print(f"\n{i}. SCENARIO: {scenario['text']}")
        print(f"   CONTEXT: {scenario['context']}")
        print("-" * 60)

        # Generate socially intelligent response
        result = social_system.simulate_voice_interaction(
            scenario["text"], "CJ", scenario["context"]
        )

        print(f"📝 RESPONSE: {result['response']}")
        print(f"🎯 RESPONSE STYLE: {result['response_style']}")
        print(f"📊 CONFIDENCE: {result['confidence']:.2f}")

        if result['insights']:
            print("🧠 SOCIAL INSIGHTS:")
            for insight in result['insights']:
                print(f"   • {insight}")

        print()

    # Show social intelligence status
    print("📊 Social Intelligence System Status:")
    status = social_system.get_social_intelligence_status()

    print(f"   People known: {status['social_ai']['people_known']}")
    print(f"   Relationships tracked: {status['social_ai']['relationships_tracked']}")
    print(f"   Network size: {status['relationship_engine']['network_summary']['total_people']}")
    print(f"   Self-awareness calibration: {status['penny_integration']['self_awareness_calibration']}")
    print(f"   Voice interface ready: {status['penny_integration']['voice_ready']}")

    # Clean up test databases
    import os
    test_dbs = [
        "test_social_integration.db", "social_intelligence.db",
        "relationship_dynamics.db", "prosody_emotions.db"
    ]

    for db in test_dbs:
        if os.path.exists(db):
            os.remove(db)

    print("\n✅ Social Intelligence Integration demo completed!")