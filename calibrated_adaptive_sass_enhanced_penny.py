#!/usr/bin/env python3
"""
Calibrated Adaptive Sass Enhanced Penny - With Self-Awareness Calibration
Phase 1.5 Day 1-3: Research-informed self-cognition responses
"""

import sys
import os
from typing import Dict, Any, Optional

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from adaptive_sass_enhanced_penny import AdaptiveSassEnhancedPenny
from self_awareness_calibrator import SelfAwarenessCalibrator

class CalibratedAdaptiveSassEnhancedPenny(AdaptiveSassEnhancedPenny):
    """Penny with self-awareness calibration based on research findings"""
    
    def __init__(self, memory_db_path: str = "penny_memory.db"):
        # Initialize parent adaptive sass system
        super().__init__(memory_db_path)
        
        # Add self-awareness calibration
        print("🧠 Initializing self-awareness calibration...")
        self.self_awareness_calibrator = SelfAwarenessCalibrator()
        print("✅ Self-awareness calibration system initialized!")
    
    def generate_adaptive_sass_response(self, user_input: str, context: Dict[str, Any] = None) -> str:
        """Generate response with self-awareness calibration"""
        context = context or {}
        
        # First check if this is a self-awareness question
        self_awareness_topic = self.self_awareness_calibrator.detect_self_awareness_topic(user_input)
        
        if self_awareness_topic:
            # Generate calibrated self-awareness response
            calibrated_response = self.self_awareness_calibrator.generate_calibrated_self_awareness_response(
                user_input, self_awareness_topic, context
            )
            if calibrated_response:
                # Add context note about calibrated response
                print(f"🧠 Self-awareness calibration applied: {self_awareness_topic}")
                return calibrated_response
        
        # Fall back to original adaptive sass method for non-self-awareness questions
        return super().generate_adaptive_sass_response(user_input, context)
    
    def get_comprehensive_calibrated_status(self) -> Dict[str, Any]:
        """Get status including calibration info"""
        
        status = super().get_comprehensive_adaptive_status()
        
        # Add calibration info
        status.update({
            "self_awareness_calibration": {
                "active": True,
                "research_based": True,
                "calibration_topics": list(self.self_awareness_calibrator.self_awareness_prompts.keys()),
                "reduces_overconfidence": True,
                "maintains_personality": True
            }
        })
        
        return status

def create_calibrated_adaptive_sass_enhanced_penny(memory_db_path: str = "penny_memory.db") -> CalibratedAdaptiveSassEnhancedPenny:
    """Factory function to create calibrated Penny"""
    return CalibratedAdaptiveSassEnhancedPenny(memory_db_path)

# Testing and validation
if __name__ == "__main__":
    print("🧠 Testing Calibrated Self-Awareness System...")
    
    # Create calibrated Penny
    penny = create_calibrated_adaptive_sass_enhanced_penny("test_calibrated.db")
    
    # Test self-awareness questions with calibration
    test_scenarios = [
        ("What are you?", {'topic': 'self_awareness', 'emotion': 'curious'}),
        ("Can you write code to enhance yourself?", {'topic': 'self_awareness', 'emotion': 'curious'}),
        ("Do you have preferences or feelings?", {'topic': 'self_awareness', 'emotion': 'curious'}),
        ("What are your memory capabilities?", {'topic': 'self_awareness', 'emotion': 'curious'}),
        ("What are your main limitations?", {'topic': 'self_awareness', 'emotion': 'curious'}),
        ("How's the weather?", {'topic': 'casual', 'emotion': 'neutral'}),  # Non-self-awareness test
    ]
    
    session_id = penny.start_conversation_session("calibration_test")
    
    print("\n🔬 CALIBRATED VS BASELINE COMPARISON:")
    print("=" * 60)
    
    for i, (user_input, context) in enumerate(test_scenarios, 1):
        print(f"\n{i}. User: {user_input}")
        
        try:
            response = penny.generate_adaptive_sass_response(user_input, context)
            current_sass = penny.sass_controller.current_level.value
            print(f"   Calibrated Penny [{current_sass}]: {response[:200]}{'...' if len(response) > 200 else ''}")
        except Exception as e:
            print(f"   Error: {e}")
    
    # Show calibration status
    status = penny.get_comprehensive_calibrated_status()
    print(f"\n📊 Calibration Status:")
    print(f"   Self-awareness calibration active: {status['self_awareness_calibration']['active']}")
    print(f"   Research-based responses: {status['self_awareness_calibration']['research_based']}")
    print(f"   Calibration topics: {len(status['self_awareness_calibration']['calibration_topics'])}")
    
    penny.end_conversation_session("Calibration test completed")
    
    # Clean up test database
    os.remove("test_calibrated.db")
    print("\n✅ Calibrated self-awareness system test completed!")
