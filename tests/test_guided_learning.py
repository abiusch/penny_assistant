#!/usr/bin/env python3
"""
Comprehensive Tests for Guided Learning System
Validates proactive curiosity, learning from corrections, and research capabilities
"""

import sys
import os
import time
import json

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from emotional_memory_system import EmotionalMemorySystem
from src.core.guided_learning_system import GuidedLearningSystem, LearningOpportunityType
from memory_system import MemoryManager


class GuidedLearningTests:
    """Test suite for guided learning system."""
    
    def __init__(self):
        self.tests_passed = 0
        self.tests_failed = 0
        
        # Initialize systems
        self.memory_manager = MemoryManager()
        self.emotional_memory = EmotionalMemorySystem(self.memory_manager)
        self.guided_learning = GuidedLearningSystem(self.emotional_memory)
        
    def assert_test(self, condition: bool, test_name: str, details: str = ""):
        """Assert test condition and track results."""
        if condition:
            print(f"✅ {test_name}")
            self.tests_passed += 1
        else:
            print(f"❌ {test_name}")
            if details:
                print(f"   Details: {details}")
            self.tests_failed += 1
    
    def test_learning_opportunity_detection(self):
        """Test detection of various learning opportunities."""
        print("\n🔍 Testing Learning Opportunity Detection:")
        
        test_cases = [
            {
                "input": "Can you research machine learning for me?",
                "expected_type": LearningOpportunityType.RESEARCH_REQUEST,
                "expected_topic": "machine learning"
            },
            {
                "input": "I wonder how quantum computers actually work",
                "expected_type": LearningOpportunityType.FOLLOW_UP_CURIOSITY,
                "expected_topic": "quantum computers"
            },
            {
                "input": "I don't understand blockchain technology",
                "expected_type": LearningOpportunityType.KNOWLEDGE_GAP,
                "expected_topic": "blockchain technology"
            },
            {
                "input": "I need to decide between React and Vue for my project",
                "expected_type": LearningOpportunityType.PROBLEM_SOLVING,
                "expected_topic": "React and Vue"
            }
        ]
        
        for case in test_cases:
            opportunities = self.guided_learning.detect_learning_opportunities(
                case["input"], "context"
            )
            
            found_matching = False
            for opp in opportunities:
                if (opp.opportunity_type == case["expected_type"] and 
                    case["expected_topic"].lower() in opp.topic.lower()):
                    found_matching = True
                    break
            
            self.assert_test(
                found_matching,
                f"Detect '{case['expected_type'].value}' in: '{case['input'][:30]}...'",
                f"Expected topic: {case['expected_topic']}, Found opportunities: {[o.topic for o in opportunities]}"
            )
    
    def test_correction_detection(self):
        """Test detection of user corrections."""
        print("\n✏️ Testing Correction Detection:")
        
        test_cases = [
            {
                "previous": "Python is a compiled language",
                "correction": "Actually, Python is an interpreted language",
                "should_detect": True
            },
            {
                "previous": "React is a framework",
                "correction": "No, React is a library, not a framework",
                "should_detect": True
            },
            {
                "previous": "The sky is blue",
                "correction": "That's interesting about the sky",
                "should_detect": False
            }
        ]
        
        for case in test_cases:
            correction = self.guided_learning.detect_correction_attempt(
                case["correction"], case["previous"]
            )
            
            detected = correction is not None
            
            self.assert_test(
                detected == case["should_detect"],
                f"Correction detection: '{case['correction'][:30]}...'",
                f"Expected: {case['should_detect']}, Got: {detected}"
            )
    
    def test_permission_request_generation(self):
        """Test generation of research permission requests."""
        print("\n💬 Testing Permission Request Generation:")
        
        from src.core.guided_learning_system import LearningOpportunity, ResearchPermissionStrategy
        
        # Create test opportunity
        opportunity = LearningOpportunity(
            opportunity_type=LearningOpportunityType.RESEARCH_REQUEST,
            topic="artificial intelligence",
            context="User wants to learn about AI",
            user_input="Tell me about AI",
            confidence=0.8,
            suggested_research="Research AI comprehensively",
            permission_strategy=ResearchPermissionStrategy.CURIOUS_SUGGESTION,
            expected_user_interest=0.7
        )
        
        permission_request = self.guided_learning.request_research_permission(opportunity)
        
        # Check that request contains key elements
        contains_topic = "artificial intelligence" in permission_request.lower()
        contains_question = "?" in permission_request
        is_reasonable_length = 20 < len(permission_request) < 200
        
        self.assert_test(
            contains_topic and contains_question and is_reasonable_length,
            "Permission request generation",
            f"Generated: '{permission_request}'"
        )
    
    def test_curiosity_question_generation(self):
        """Test generation of curious follow-up questions."""
        print("\n❓ Testing Curiosity Question Generation:")
        
        topics = ["machine learning", "quantum computing", "sustainable energy", "blockchain"]
        
        for topic in topics:
            question = self.guided_learning.generate_curiosity_question(topic, "user interest context")
            
            # Check question quality
            contains_topic = topic.lower() in question.lower()
            is_question = "?" in question
            is_reasonable_length = 10 < len(question) < 150
            
            self.assert_test(
                contains_topic and is_question and is_reasonable_length,
                f"Curiosity question for '{topic}'",
                f"Generated: '{question}'"
            )
    
    def test_database_integration(self):
        """Test database storage and retrieval."""
        print("\n🗄️ Testing Database Integration:")
        
        # Test research session recording
        from src.core.guided_learning_system import LearningOpportunity, LearningOpportunityType, ResearchPermissionStrategy
        
        opportunity = LearningOpportunity(
            opportunity_type=LearningOpportunityType.RESEARCH_REQUEST,
            topic="test topic",
            context="test context",
            user_input="test user input",
            confidence=0.8,
            suggested_research="test research",
            permission_strategy=ResearchPermissionStrategy.DIRECT_ASK,
            expected_user_interest=0.7
        )
        
        # Record research session
        session_id = self.guided_learning.record_research_session(opportunity, True)
        
        self.assert_test(
            session_id > 0,
            "Research session recording",
            f"Session ID: {session_id}"
        )
        
        # Update with results
        self.guided_learning.update_research_session(
            session_id, "test research results", "positive feedback", 4
        )
        
        # Test correction recording
        correction_id = self.guided_learning.record_user_correction(
            "original info", "corrected info", "context", "user input"
        )
        
        self.assert_test(
            correction_id > 0,
            "User correction recording",
            f"Correction ID: {correction_id}"
        )
        
        # Verify database tables exist and have entries
        import sqlite3
        
        with sqlite3.connect(self.emotional_memory.db_path) as conn:
            # Check research sessions
            cursor = conn.execute("SELECT COUNT(*) FROM research_sessions")
            research_count = cursor.fetchone()[0]
            
            # Check user corrections
            cursor = conn.execute("SELECT COUNT(*) FROM user_corrections")
            corrections_count = cursor.fetchone()[0]
            
            self.assert_test(
                research_count > 0 and corrections_count > 0,
                "Database entries created",
                f"Research sessions: {research_count}, Corrections: {corrections_count}"
            )
    
    def run_all_tests(self):
        """Run the complete test suite."""
        print("🧠 Guided Learning System - Comprehensive Tests")
        print("=" * 60)
        
        self.test_learning_opportunity_detection()
        self.test_correction_detection()
        self.test_permission_request_generation()
        self.test_curiosity_question_generation()
        self.test_database_integration()
        
        print("\n" + "=" * 60)
        print(f"📊 Test Results: {self.tests_passed} passed, {self.tests_failed} failed")
        
        if self.tests_failed == 0:
            print("🎉 All tests passed! Guided Learning System is working correctly.")
            print("\n🚀 Ready for integration with conversation pipeline!")
            return True
        else:
            print("⚠️ Some tests failed. Review the guided learning system.")
            return False


def main():
    """Run guided learning tests."""
    print("🧪 Starting Guided Learning System Tests...")
    print("""This validates the new proactive curiosity and learning capabilities:
    
    🎯 Testing:
    • Learning opportunity detection (research requests, curiosity, knowledge gaps)
    • User correction detection and acknowledgment
    • Permission request generation for research
    • Curiosity question generation
    • Database integration for learning tracking
    • Integration with existing emotional memory system
    """)
    
    tester = GuidedLearningTests()
    success = tester.run_all_tests()
    
    if success:
        print("\n✨ Next Steps:")
        print("   1. Run: python penny_with_guided_learning.py")
        print("   2. Try saying: 'Can you research machine learning for me?'")
        print("   3. Express curiosity: 'I wonder how AI actually works'")
        print("   4. Correct Penny when she's wrong - she'll learn!")
        print("   5. Say: 'I don't understand blockchain' for targeted help")
    
    return 0 if success else 1


if __name__ == "__main__":
    exit(main())
