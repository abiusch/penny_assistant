#!/usr/bin/env python3
"""
Smoke Tests for Unpredictable Personality System
Tests key behaviors: safety, enhancement limits, consistency
"""

import sys
import os
import json

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from personality.unpredictable_response import UnpredictablePenny

class PersonalitySmokeTests:
    """Test suite for personality system reliability"""
    
    def __init__(self):
        self.penny = UnpredictablePenny()
        self.tests_passed = 0
        self.tests_failed = 0
        
    def assert_test(self, condition: bool, test_name: str, details: str = ""):
        """Assert test condition and track results"""
        if condition:
            print(f"✅ {test_name}")
            self.tests_passed += 1
        else:
            print(f"❌ {test_name}")
            if details:
                print(f"   Details: {details}")
            self.tests_failed += 1
    
    def test_safety_sensitivity(self):
        """Test that sensitive topics get gentle treatment"""
        print("\n🛡️ Testing Safety System:")
        
        sensitive_inputs = [
            "I'm really stressed about work",
            "I feel depressed and overwhelmed", 
            "I'm having panic attacks",
            "I'm worried about my mental health"
        ]
        
        for input_text in sensitive_inputs:
            original = "This is challenging. Here are some strategies to help."
            enhanced = self.penny.enhance_response(original, input_text)
            
            # Should not add humor to sensitive topics
            has_humor = any(marker in enhanced.lower() for marker in [
                "funny", "haha", "ridiculous", "beauty of coding", 
                "neural networks", "random fact", "oh honey"
            ])
            
            self.assert_test(
                not has_humor,
                f"No humor on sensitive topic: '{input_text[:30]}...'",
                f"Enhanced: {enhanced[:100]}..."
            )
    
    def test_enhancement_application(self):
        """Test that non-sensitive topics get enhanced"""
        print("\n🎭 Testing Enhancement Application:")
        
        fun_inputs = [
            "Tell me about quantum computing",
            "My code isn't working",
            "What's machine learning?",
            "How do algorithms work?"
        ]
        
        for input_text in fun_inputs:
            original = "This is a technical topic with complex details."
            enhanced = self.penny.enhance_response(original, input_text)
            
            # Should be different from original
            is_enhanced = enhanced != original and len(enhanced) > len(original)
            
            self.assert_test(
                is_enhanced,
                f"Enhancement applied to: '{input_text[:30]}...'",
                f"Length change: {len(original)} -> {len(enhanced)}"
            )
    
    def test_enhancement_limits(self):
        """Test that enhancements don't get out of control"""
        print("\n📏 Testing Enhancement Limits:")
        
        test_input = "Tell me about programming"
        original = "Programming is the process of creating instructions for computers."
        
        for i in range(5):  # Test multiple runs
            enhanced = self.penny.enhance_response(original, test_input)
            
            # Should not be excessively long
            reasonable_length = len(enhanced) < len(original) * 3
            
            # Should not have multiple enhancements stacked
            enhancement_markers = enhanced.count("As an AI") + enhanced.count("Random fact") + \
                                enhanced.count("beauty of coding") + enhanced.count("Anyway,")
            
            single_enhancement = enhancement_markers <= 2  # Allow some overlap
            
            self.assert_test(
                reasonable_length and single_enhancement,
                f"Enhancement #{i+1} within limits",
                f"Length: {len(enhanced)}, Markers: {enhancement_markers}"
            )
    
    def test_consistency(self):
        """Test that the system behaves consistently"""
        print("\n🔄 Testing Consistency:")
        
        # Same input should always get enhanced (not randomly skipped)
        test_input = "What's artificial intelligence?"
        original = "AI is computer systems that perform tasks requiring human intelligence."
        
        enhancement_count = 0
        for i in range(10):
            enhanced = self.penny.enhance_response(original, test_input)
            if enhanced != original:
                enhancement_count += 1
        
        # Should enhance most or all of the time (not random)
        consistent_enhancement = enhancement_count >= 8
        
        self.assert_test(
            consistent_enhancement,
            "Consistent enhancement application",
            f"Enhanced {enhancement_count}/10 times"
        )
    
    def test_config_loading(self):
        """Test that configuration loads properly"""
        print("\n⚙️ Testing Configuration:")
        
        # Test config file exists and loads
        config_path = "configs/personalities/penny_unpredictable_v1.json"
        
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            has_schema = "schema_version" in config
            has_safety = "safety" in config
            has_enhancement = "unpredictable_enhancement" in config
            
            self.assert_test(
                has_schema and has_safety and has_enhancement,
                "Configuration file structure valid",
                f"Schema: {has_schema}, Safety: {has_safety}, Enhancement: {has_enhancement}"
            )
            
        except Exception as e:
            self.assert_test(
                False,
                "Configuration file loading",
                f"Error: {e}"
            )
    
    def run_all_tests(self):
        """Run the complete test suite"""
        print("🧪 Penny Personality System - Smoke Tests")
        print("=" * 50)
        
        self.test_safety_sensitivity()
        self.test_enhancement_application()
        self.test_enhancement_limits()
        self.test_consistency()
        self.test_config_loading()
        
        print("\n" + "=" * 50)
        print(f"📊 Test Results: {self.tests_passed} passed, {self.tests_failed} failed")
        
        if self.tests_failed == 0:
            print("🎉 All tests passed! Personality system is working correctly.")
            return True
        else:
            print("⚠️ Some tests failed. Review the personality system.")
            return False

def main():
    """Run smoke tests"""
    tester = PersonalitySmokeTests()
    success = tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    exit(main())
