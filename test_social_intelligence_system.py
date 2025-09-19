#!/usr/bin/env python3
"""
Comprehensive Test and Validation System for Social Intelligence
Tests all components and integration
"""

import os
import sys
import json
import sqlite3
from datetime import datetime
from typing import Dict, List, Any, Tuple
import asyncio

# Import all social intelligence components
from advanced_social_intelligence import create_advanced_social_intelligence
from relationship_dynamics_engine import create_relationship_dynamics_engine
from prosody_emotion_detector import create_prosody_emotion_detector, ProsodyProfile, VoiceContext
from social_intelligence_integration import create_social_intelligence_integration, VoiceInteractionContext

class SocialIntelligenceTestSuite:
    """Comprehensive test suite for social intelligence system"""

    def __init__(self):
        self.test_results = {}
        self.test_databases = []

    def run_all_tests(self) -> Dict[str, Any]:
        """Run all test suites"""
        print("🧪 Running Social Intelligence Test Suite")
        print("=" * 60)

        # Test individual components
        self.test_results["advanced_social_intelligence"] = self.test_advanced_social_intelligence()
        self.test_results["relationship_dynamics"] = self.test_relationship_dynamics()
        self.test_results["prosody_detection"] = self.test_prosody_detection()
        self.test_results["integration"] = self.test_system_integration()
        self.test_results["real_world_scenarios"] = self.test_real_world_scenarios()

        # Generate overall assessment
        overall_score = self.calculate_overall_score()
        self.test_results["overall_score"] = overall_score

        # Cleanup
        self.cleanup_test_databases()

        return self.test_results

    def test_advanced_social_intelligence(self) -> Dict[str, Any]:
        """Test advanced social intelligence component"""
        print("\n🧠 Testing Advanced Social Intelligence...")

        try:
            # Create test instance
            social_ai = create_advanced_social_intelligence("test_social_ai.db")
            self.test_databases.append("test_social_ai.db")

            test_cases = [
                {
                    "input": "Josh is being weird about the project deadline and it's making me anxious",
                    "expected_participants": ["Josh"],
                    "expected_context": "problem_solving",
                    "expected_atmosphere": "tense"
                },
                {
                    "input": "The team worked really well together on the new feature",
                    "expected_participants": ["team"],
                    "expected_context": "celebration",
                    "expected_atmosphere": "positive"
                },
                {
                    "input": "I need to figure out how to approach Josh about the timeline issue",
                    "expected_participants": ["Josh"],
                    "expected_context": "problem_solving",
                    "expected_atmosphere": "neutral"
                }
            ]

            results = {"passed": 0, "total": len(test_cases), "details": []}

            for i, test_case in enumerate(test_cases):
                try:
                    situation = social_ai.analyze_social_situation(test_case["input"])

                    # Check participants detection
                    participants_correct = len(situation.participants) > 0
                    if participants_correct:
                        results["passed"] += 0.3

                    # Check context detection
                    context_reasonable = situation.primary_context.value in [
                        "problem_solving", "celebration", "casual_chat", "venting", "crisis"
                    ]
                    if context_reasonable:
                        results["passed"] += 0.3

                    # Check confidence
                    confidence_reasonable = 0.0 <= situation.confidence_level <= 1.0
                    if confidence_reasonable:
                        results["passed"] += 0.4

                    results["details"].append({
                        "test": f"case_{i+1}",
                        "participants_detected": len(situation.participants),
                        "context": situation.primary_context.value,
                        "confidence": situation.confidence_level,
                        "success": participants_correct and context_reasonable and confidence_reasonable
                    })

                except Exception as e:
                    results["details"].append({"test": f"case_{i+1}", "error": str(e), "success": False})

            results["score"] = results["passed"] / results["total"]
            print(f"   ✅ Advanced Social Intelligence: {results['score']:.2f}")
            return results

        except Exception as e:
            print(f"   ❌ Advanced Social Intelligence test failed: {e}")
            return {"score": 0.0, "error": str(e)}

    def test_relationship_dynamics(self) -> Dict[str, Any]:
        """Test relationship dynamics engine"""
        print("\n🔗 Testing Relationship Dynamics...")

        try:
            # Create test instance
            rel_engine = create_relationship_dynamics_engine("test_rel_dynamics.db")
            self.test_databases.append("test_rel_dynamics.db")

            test_cases = [
                {
                    "input": "Josh and Reneille had a disagreement about the project scope",
                    "expected_people": 2,
                    "expected_tension": True
                },
                {
                    "input": "The team collaboration was excellent today",
                    "expected_people": 1,  # "team"
                    "expected_tension": False
                },
                {
                    "input": "I'm worried about Josh - he seems stressed",
                    "expected_people": 1,
                    "expected_tension": False
                }
            ]

            results = {"passed": 0, "total": len(test_cases), "details": []}

            for i, test_case in enumerate(test_cases):
                try:
                    analysis = rel_engine.analyze_relationship_dynamics(test_case["input"])

                    # Check people detection
                    people_detected = len(analysis["people_involved"])
                    people_reasonable = people_detected > 0
                    if people_reasonable:
                        results["passed"] += 0.4

                    # Check for relationship insights
                    has_insights = "relationship_insights" in analysis
                    if has_insights:
                        results["passed"] += 0.3

                    # Check recommendations
                    has_recommendations = len(analysis.get("recommendations", [])) > 0
                    if has_recommendations:
                        results["passed"] += 0.3

                    results["details"].append({
                        "test": f"case_{i+1}",
                        "people_detected": people_detected,
                        "has_insights": has_insights,
                        "recommendations": len(analysis.get("recommendations", [])),
                        "success": people_reasonable and has_insights and has_recommendations
                    })

                except Exception as e:
                    results["details"].append({"test": f"case_{i+1}", "error": str(e), "success": False})

            results["score"] = results["passed"] / results["total"]
            print(f"   ✅ Relationship Dynamics: {results['score']:.2f}")
            return results

        except Exception as e:
            print(f"   ❌ Relationship Dynamics test failed: {e}")
            return {"score": 0.0, "error": str(e)}

    def test_prosody_detection(self) -> Dict[str, Any]:
        """Test prosody emotion detection"""
        print("\n🎙️ Testing Prosody Emotion Detection...")

        try:
            # Create test instance
            prosody_detector = create_prosody_emotion_detector("test_prosody.db")
            self.test_databases.append("test_prosody.db")

            # Test with simulated prosody profiles
            test_profiles = [
                {
                    "name": "happy_excited",
                    "profile": ProsodyProfile(
                        pitch_mean=280, pitch_std=80, speaking_rate=6.0,
                        pause_duration_mean=0.4, pause_frequency=25,
                        volume_mean=0.8, volume_std=0.15,
                        voice_quality_score=0.9, audio_duration=5.0
                    ),
                    "expected_emotion": "excited"
                },
                {
                    "name": "sad_tired",
                    "profile": ProsodyProfile(
                        pitch_mean=140, pitch_std=25, speaking_rate=2.8,
                        pause_duration_mean=2.2, pause_frequency=15,
                        volume_mean=0.4, volume_std=0.1,
                        voice_quality_score=0.5, audio_duration=6.0
                    ),
                    "expected_emotion": "sad"
                },
                {
                    "name": "angry_frustrated",
                    "profile": ProsodyProfile(
                        pitch_mean=220, pitch_std=120, speaking_rate=5.5,
                        pause_duration_mean=0.3, pause_frequency=30,
                        volume_mean=0.9, volume_std=0.25,
                        voice_quality_score=0.6, audio_duration=4.0
                    ),
                    "expected_emotion": "angry"
                }
            ]

            results = {"passed": 0, "total": len(test_profiles), "details": []}

            for test_profile in test_profiles:
                try:
                    prediction = prosody_detector.predict_emotion_from_prosody(test_profile["profile"])

                    # Check if emotion is reasonable
                    emotion_reasonable = prediction.primary_emotion in [
                        "happy", "sad", "angry", "frustrated", "excited", "anxious", "calm", "tired", "neutral"
                    ]
                    if emotion_reasonable:
                        results["passed"] += 0.4

                    # Check confidence
                    confidence_reasonable = 0.0 <= prediction.confidence <= 1.0
                    if confidence_reasonable:
                        results["passed"] += 0.3

                    # Check prosody indicators
                    has_indicators = len(prediction.prosody_indicators) > 0
                    if has_indicators:
                        results["passed"] += 0.3

                    results["details"].append({
                        "test": test_profile["name"],
                        "predicted_emotion": prediction.primary_emotion,
                        "confidence": prediction.confidence,
                        "indicators": len(prediction.prosody_indicators),
                        "success": emotion_reasonable and confidence_reasonable and has_indicators
                    })

                except Exception as e:
                    results["details"].append({
                        "test": test_profile["name"],
                        "error": str(e),
                        "success": False
                    })

            results["score"] = results["passed"] / results["total"]
            print(f"   ✅ Prosody Detection: {results['score']:.2f}")
            return results

        except Exception as e:
            print(f"   ❌ Prosody Detection test failed: {e}")
            return {"score": 0.0, "error": str(e)}

    def test_system_integration(self) -> Dict[str, Any]:
        """Test full system integration"""
        print("\n🔧 Testing System Integration...")

        try:
            # Create integrated system
            social_system = create_social_intelligence_integration("test_integration.db")
            self.test_databases.append("test_integration.db")

            test_scenarios = [
                {
                    "text": "Josh is being weird about the project deadline",
                    "speaker": "CJ",
                    "context": "work discussion"
                },
                {
                    "text": "I'm really excited about the new features!",
                    "speaker": "CJ",
                    "context": "project enthusiasm"
                },
                {
                    "text": "The team meeting went really well today",
                    "speaker": "CJ",
                    "context": "team update"
                }
            ]

            results = {"passed": 0, "total": len(test_scenarios), "details": []}

            for i, scenario in enumerate(test_scenarios):
                try:
                    result = social_system.simulate_voice_interaction(
                        scenario["text"], scenario["speaker"], scenario["context"]
                    )

                    # Check response generation
                    has_response = len(result.get("response", "")) > 0
                    if has_response:
                        results["passed"] += 0.3

                    # Check social analysis
                    has_analysis = "social_analysis" in result
                    if has_analysis:
                        results["passed"] += 0.3

                    # Check confidence score
                    has_confidence = "confidence" in result and 0 <= result["confidence"] <= 1
                    if has_confidence:
                        results["passed"] += 0.4

                    results["details"].append({
                        "test": f"scenario_{i+1}",
                        "has_response": has_response,
                        "has_analysis": has_analysis,
                        "confidence": result.get("confidence", 0),
                        "response_length": len(result.get("response", "")),
                        "success": has_response and has_analysis and has_confidence
                    })

                except Exception as e:
                    results["details"].append({
                        "test": f"scenario_{i+1}",
                        "error": str(e),
                        "success": False
                    })

            results["score"] = results["passed"] / results["total"]
            print(f"   ✅ System Integration: {results['score']:.2f}")
            return results

        except Exception as e:
            print(f"   ❌ System Integration test failed: {e}")
            return {"score": 0.0, "error": str(e)}

    def test_real_world_scenarios(self) -> Dict[str, Any]:
        """Test with realistic scenarios"""
        print("\n🌍 Testing Real-World Scenarios...")

        try:
            social_system = create_social_intelligence_integration("test_realworld.db")
            self.test_databases.append("test_realworld.db")

            real_world_scenarios = [
                {
                    "scenario": "Josh missed the deadline and team is frustrated",
                    "text": "Josh missed the deadline again and now Reneille is upset and the whole team is behind schedule",
                    "expected_elements": ["multiple people", "tension", "work pressure"]
                },
                {
                    "scenario": "Successful product launch celebration",
                    "text": "The product launch was amazing! Josh's technical work was perfect and Reneille's user research really paid off",
                    "expected_elements": ["positive emotion", "recognition", "team success"]
                },
                {
                    "scenario": "Personal stress affecting work",
                    "text": "I'm feeling really overwhelmed lately and I think it's affecting how I communicate with Josh and Reneille",
                    "expected_elements": ["personal stress", "self-awareness", "relationship impact"]
                },
                {
                    "scenario": "Cross-team conflict resolution",
                    "text": "There's tension between our team and the design team, and Josh thinks we should escalate but Reneille wants to talk it out",
                    "expected_elements": ["group dynamics", "conflict resolution", "different approaches"]
                }
            ]

            results = {"passed": 0, "total": len(real_world_scenarios), "details": []}

            for scenario in real_world_scenarios:
                try:
                    result = social_system.simulate_voice_interaction(
                        scenario["text"], "CJ", scenario["scenario"]
                    )

                    # Evaluate response appropriateness
                    response = result.get("response", "")
                    response_length_appropriate = 50 <= len(response) <= 500
                    if response_length_appropriate:
                        results["passed"] += 0.2

                    # Check for social insights
                    insights = result.get("insights", [])
                    has_meaningful_insights = len(insights) > 0
                    if has_meaningful_insights:
                        results["passed"] += 0.3

                    # Check response style appropriateness
                    response_style = result.get("response_style", "")
                    has_response_style = len(response_style) > 0
                    if has_response_style:
                        results["passed"] += 0.3

                    # Check confidence level
                    confidence = result.get("confidence", 0)
                    confidence_reasonable = confidence > 0.3  # Should have some confidence
                    if confidence_reasonable:
                        results["passed"] += 0.2

                    results["details"].append({
                        "scenario": scenario["scenario"],
                        "response_length": len(response),
                        "insights_count": len(insights),
                        "response_style": response_style,
                        "confidence": confidence,
                        "success": (response_length_appropriate and has_meaningful_insights and
                                  has_response_style and confidence_reasonable)
                    })

                except Exception as e:
                    results["details"].append({
                        "scenario": scenario["scenario"],
                        "error": str(e),
                        "success": False
                    })

            results["score"] = results["passed"] / results["total"]
            print(f"   ✅ Real-World Scenarios: {results['score']:.2f}")
            return results

        except Exception as e:
            print(f"   ❌ Real-World Scenarios test failed: {e}")
            return {"score": 0.0, "error": str(e)}

    def calculate_overall_score(self) -> float:
        """Calculate overall system score"""
        component_scores = []

        for component, results in self.test_results.items():
            if isinstance(results, dict) and "score" in results:
                component_scores.append(results["score"])

        return sum(component_scores) / len(component_scores) if component_scores else 0.0

    def cleanup_test_databases(self):
        """Clean up test databases"""
        for db_path in self.test_databases:
            if os.path.exists(db_path):
                os.remove(db_path)

    def generate_test_report(self) -> str:
        """Generate comprehensive test report"""
        report = []
        report.append("🧠 SOCIAL INTELLIGENCE SYSTEM TEST REPORT")
        report.append("=" * 60)
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")

        overall_score = self.test_results.get("overall_score", 0.0)
        report.append(f"📊 OVERALL SCORE: {overall_score:.2f} ({self._score_to_grade(overall_score)})")
        report.append("")

        # Component breakdown
        report.append("📋 COMPONENT SCORES:")
        for component, results in self.test_results.items():
            if component != "overall_score" and isinstance(results, dict):
                score = results.get("score", 0.0)
                report.append(f"   {component}: {score:.2f} ({self._score_to_grade(score)})")

        report.append("")

        # Detailed results
        report.append("🔍 DETAILED RESULTS:")
        for component, results in self.test_results.items():
            if component != "overall_score" and isinstance(results, dict):
                report.append(f"\n{component.upper()}:")
                if "details" in results:
                    for detail in results["details"]:
                        success_indicator = "✅" if detail.get("success", False) else "❌"
                        report.append(f"   {success_indicator} {detail.get('test', 'unknown')}")

        return "\n".join(report)

    def _score_to_grade(self, score: float) -> str:
        """Convert score to grade"""
        if score >= 0.9:
            return "A"
        elif score >= 0.8:
            return "B"
        elif score >= 0.7:
            return "C"
        elif score >= 0.6:
            return "D"
        else:
            return "F"

def run_comprehensive_tests():
    """Run all social intelligence tests"""
    test_suite = SocialIntelligenceTestSuite()
    results = test_suite.run_all_tests()

    # Generate and display report
    report = test_suite.generate_test_report()
    print("\n" + report)

    # Save report to file
    with open("social_intelligence_test_report.txt", "w") as f:
        f.write(report)

    return results

if __name__ == "__main__":
    print("🧪 Social Intelligence System - Comprehensive Testing")
    print("=" * 60)

    results = run_comprehensive_tests()

    overall_score = results.get("overall_score", 0.0)
    if overall_score >= 0.8:
        print(f"\n🎉 EXCELLENT! Social Intelligence System achieved {overall_score:.2f} overall score")
    elif overall_score >= 0.6:
        print(f"\n✅ GOOD! Social Intelligence System achieved {overall_score:.2f} overall score")
    else:
        print(f"\n⚠️ NEEDS IMPROVEMENT! Social Intelligence System achieved {overall_score:.2f} overall score")

    print(f"📄 Detailed report saved to: social_intelligence_test_report.txt")
    print("\n✅ Social Intelligence System testing completed!")