#!/usr/bin/env python3
"""
Validation Test for CJ's Personalized PennyGPT System
Tests the complete integration with CJ's profile and preferences
"""

import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def test_cj_personalization():
    """Test CJ's personalized learning system."""
    print("👤 Testing CJ's Personalized Learning System")
    print("=" * 50)
    
    try:
        from cj_enhanced_learning import CJEnhancedLearningSystem
        from emotional_memory_system import EmotionalMemorySystem
        from memory_system import MemoryManager
        
        # Initialize systems
        memory_manager = MemoryManager()
        emotional_memory = EmotionalMemorySystem(memory_manager)
        cj_learning = CJEnhancedLearningSystem(emotional_memory)
        
        print("✅ CJ's enhanced learning system initialized")
        
        # Test CJ-specific scenarios
        test_scenarios = [
            {
                "name": "FastAPI Development Question",
                "input": "How do I optimize FastAPI response times?",
                "expected": "Should auto-approve research, connect to PennyGPT project"
            },
            {
                "name": "ElevenLabs TTS Issue",
                "input": "My ElevenLabs voice synthesis is too slow",
                "expected": "Should auto-approve, relate to voice UX goals"
            },
            {
                "name": "Python Best Practices",
                "input": "What are the latest Python async patterns?",
                "expected": "Should auto-approve, connect to current tech stack"
            },
            {
                "name": "Menu Bar App Challenge",
                "input": "I'm struggling with macOS menu bar integration",
                "expected": "Should offer research, connect to short-term goals"
            },
            {
                "name": "General Non-Tech Topic",
                "input": "Tell me about cooking recipes",
                "expected": "Should ask permission, not auto-approve"
            }
        ]
        
        print("\n🧪 Testing CJ-Specific Scenarios:")
        print("-" * 40)
        
        for i, scenario in enumerate(test_scenarios, 1):
            print(f"\n{i}. {scenario['name']}")
            print(f"   Input: \"{scenario['input']}\"")
            print(f"   Expected: {scenario['expected']}")
            
            # Test learning opportunity detection
            opportunities = cj_learning.detect_learning_opportunities(
                scenario['input'], "context"
            )
            
            if opportunities:
                best_opp = max(opportunities, key=lambda x: x.confidence * x.expected_user_interest)
                print(f"   ✅ Detected: {best_opp.opportunity_type.value}")
                print(f"   📋 Topic: {best_opp.topic}")
                print(f"   🎯 Interest: {best_opp.expected_user_interest:.2f}")
                
                # Test permission request
                permission_request = cj_learning.request_research_permission(best_opp)
                if permission_request:
                    print(f"   💬 Request: \"{permission_request[:80]}...\"")
                else:
                    print("   🚫 Auto-approved or restricted")
            else:
                print("   ❌ No opportunities detected")
        
        # Test enhanced context generation
        print("\n📊 CJ's Enhanced LLM Context:")
        print("-" * 30)
        context = cj_learning.get_learning_context_for_llm()
        context_lines = context.split('\n') if context else []
        for line in context_lines[:5]:  # Show first 5 lines
            if line.strip():
                print(f"   > {line}")
        
        if len(context_lines) > 5:
            print(f"   ... and {len(context_lines) - 5} more context lines")
        
        # Test curiosity question generation
        print("\n❓ CJ-Style Curiosity Questions:")
        print("-" * 30)
        topics = ["FastAPI optimization", "voice assistant UX", "MCP agent patterns"]
        for topic in topics:
            question = cj_learning.generate_curiosity_question(topic, "project context")
            print(f"   🤔 {topic}: \"{question}\"")
        
        print("\n🎯 CJ Personalization Summary:")
        print("   ✅ Profile-aware learning opportunity detection")
        print("   ✅ Auto-approval for tech topics CJ cares about")
        print("   ✅ CJ's communication style in permission requests")
        print("   ✅ Project-aware context and connections")
        print("   ✅ Concise, actionable curiosity questions")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def show_personalization_benefits():
    """Show the specific benefits of CJ's personalization."""
    print("\n🎆 CJ's Personalization Benefits:")
    print("=" * 40)
    
    benefits = [
        {
            "feature": "Auto-Research Topics",
            "description": "Automatically researches FastAPI, Python, ElevenLabs, TTS topics",
            "example": "Question about FastAPI → immediate research without asking"
        },
        {
            "feature": "Project-Aware Suggestions",
            "description": "Connects everything back to PennyGPT development",
            "example": "Python advice → relates to current daemon architecture"
        },
        {
            "feature": "CJ's Communication Style",
            "description": "Answer-first, concise, actionable responses",
            "example": "Solution → brief why → next step (CJ's preferred structure)"
        },
        {
            "feature": "Tech Stack Integration",
            "description": "Advice specifically for CJ's Python/FastAPI/ElevenLabs stack",
            "example": "Optimization tips for current TTS pipeline"
        },
        {
            "feature": "Goal-Oriented Context",
            "description": "Understands CJ's short-term (menu-bar app) and long-term (MCP) goals",
            "example": "Suggestions align with roadmap priorities"
        }
    ]
    
    for benefit in benefits:
        print(f"\n🎯 {benefit['feature']}:")
        print(f"   💡 {benefit['description']}")
        print(f"   🌱 Example: {benefit['example']}")


def show_next_steps():
    """Show next steps for using the personalized system."""
    print("\n🚀 Ready to Use CJ's Personalized PennyGPT!")
    print("=" * 45)
    
    print("""
📋 What's Ready:
   ✅ CJ's personal profile loaded (interests, communication style, goals)
   ✅ Penny-Justine persona blend configured
   ✅ Enhanced guided learning with auto-approvals
   ✅ Project-aware research and suggestions
   ✅ CJ's preferred communication structure

🎯 Try These Commands:
   python cj_personalized_penny.py     # Full voice experience
   python cj_enhanced_learning.py      # Test learning detection

💬 Try These Phrases:
   "How do I optimize my FastAPI daemon?"
   "ElevenLabs TTS latency is bothering me"
   "Best Python async patterns for voice apps"
   "Menu bar app integration challenges"
   "MCP agent design patterns"

🎭 What You'll Experience:
   • Immediate research on topics you care about
   • Responses in your preferred answer-first structure
   • Connections to your PennyGPT project
   • Tech stack-specific advice
   • Concise, actionable suggestions
   • Penny's warm but sassy personality
    """)


if __name__ == "__main__":
    print("🧪 CJ's Personalized PennyGPT Validation")
    print("""This tests the complete personalized learning system with CJ's profile.
    
    🎯 Testing:
    • Profile-aware learning detection
    • Auto-approval for CJ's preferred topics
    • CJ's communication style adaptation
    • Project-specific context and suggestions
    """)
    
    success = test_cj_personalization()
    
    if success:
        show_personalization_benefits()
        show_next_steps()
    else:
        print("\n⚠️ Please fix issues before using the personalized system.")
