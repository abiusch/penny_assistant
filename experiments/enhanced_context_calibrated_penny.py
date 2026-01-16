#!/usr/bin/env python3
"""
Enhanced Context Calibrated Penny - Days 4-7 Integration
"""

import sys
import os
from typing import Dict, Any

sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from calibrated_adaptive_sass_enhanced_penny import CalibratedAdaptiveSassEnhancedPenny
from enhanced_context_detector import create_enhanced_context_detector

class EnhancedContextCalibratedPenny(CalibratedAdaptiveSassEnhancedPenny):
    def __init__(self, memory_db_path: str = "penny_memory.db"):
        super().__init__(memory_db_path)
        print("Enhanced context detection initialized")
        self.enhanced_context_detector = create_enhanced_context_detector()
    
    def generate_adaptive_sass_response(self, user_input: str, context: Dict[str, Any] = None) -> str:
        context = context or {}
        
        # Perform enhanced context analysis
        enhanced_analysis = self.enhanced_context_detector.analyze_comprehensive_context(user_input)
        
        # Log enhanced context
        print(f"Enhanced context: {enhanced_analysis.emotion_profile.primary_emotion} ({enhanced_analysis.emotion_profile.intensity.value}) | {enhanced_analysis.social_context}")
        
        # Check for self-awareness topics first
        self_awareness_topic = self.self_awareness_calibrator.detect_self_awareness_topic(user_input)
        
        if self_awareness_topic:
            calibrated_response = self.self_awareness_calibrator.generate_calibrated_self_awareness_response(
                user_input, self_awareness_topic, context
            )
            if calibrated_response:
                print(f"Self-awareness calibration applied: {self_awareness_topic}")
                return calibrated_response
        
        # Use enhanced context for sass adjustment
        adjusted_sass_level = self._determine_enhanced_sass_level(enhanced_analysis)
        
        # Temporarily set sass level
        original_level = self.sass_controller.current_level
        self.sass_controller.set_sass_level(adjusted_sass_level)
        
        try:
            response = super().generate_sass_aware_response(user_input, context)
            
            # Add compound emotion acknowledgment if present
            if enhanced_analysis.emotion_profile.compound_emotions:
                compound_note = self._generate_compound_emotion_acknowledgment(enhanced_analysis.emotion_profile.compound_emotions)
                if compound_note:
                    response = f"{response} {compound_note}"
            
            return response
        finally:
            self.sass_controller.set_sass_level(original_level)
    
    def _determine_enhanced_sass_level(self, enhanced_analysis):
        if self.has_active_override:
            return self.sass_controller.current_level
        
        communication_pref = enhanced_analysis.communication_preference
        
        from sass_controller import SassLevel
        
        if communication_pref == "calm_supportive":
            return SassLevel.MINIMAL
        elif communication_pref == "enthusiastic_matching":
            return SassLevel.SPICY
        elif communication_pref == "professional_structured":
            return SassLevel.PROFESSIONAL
        elif communication_pref == "empathetic_listening":
            return SassLevel.MINIMAL
        elif communication_pref == "casual_humor":
            return SassLevel.SPICY
        else:
            return SassLevel.MEDIUM
    
    def _generate_compound_emotion_acknowledgment(self, compound_emotions: list) -> str:
        if not compound_emotions:
            return ""
        
        compound_responses = {
            "frustrated_but_determined": "I can sense you're frustrated but also determined to push through.",
            "excited_but_nervous": "You seem excited about this, though I detect some nervousness too.",
            "overwhelmed_yet_determined": "You're feeling overwhelmed but I can tell you're not giving up."
        }
        
        for compound in compound_emotions:
            if compound in compound_responses:
                return compound_responses[compound]
        
        return ""

def create_enhanced_context_calibrated_penny(memory_db_path: str = "penny_memory.db"):
    return EnhancedContextCalibratedPenny(memory_db_path)

if __name__ == "__main__":
    print("Testing Enhanced Context + Calibrated System...")
    
    penny = create_enhanced_context_calibrated_penny("test_enhanced.db")
    
    test_scenarios = [
        "I'm really frustrated with this bug but determined to fix it",
        "What are you and how do you detect my emotions?",
        "Josh is being weird about the project deadline and it's making me anxious",
        "This is urgent - the server crashed and we need help immediately!"
    ]
    
    session_id = penny.start_conversation_session("enhanced_test")
    
    print("\nTesting enhanced context detection:")
    print("=" * 50)
    
    for i, user_input in enumerate(test_scenarios, 1):
        print(f"\n{i}. User: {user_input}")
        
        try:
            response = penny.generate_adaptive_sass_response(user_input, {})
            sass_level = penny.sass_controller.current_level.value
            print(f"   Penny [{sass_level}]: {response[:150]}...")
        except Exception as e:
            print(f"   Error: {e}")
    
    penny.end_conversation_session("Test completed")
    
    try:
        os.remove("test_enhanced.db")
    except:
        pass
    
    print("\nEnhanced context system test completed!")
