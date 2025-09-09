#!/usr/bin/env python3
"""
Demonstration: Personal Profile Integration with Guided Learning
Shows how a personal profile transforms the learning experience
"""

import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def demo_profile_benefits():
    """Demonstrate the benefits of having a personal profile."""
    print("👤 Personal Profile Integration Demo")
    print("=" * 50)
    
    try:
        from src.core.personal_profile_system import create_sample_profile, PersonalProfileLoader
        
        # Create sample profile
        print("📝 Creating sample personal profile...")
        create_sample_profile()
        
        # Load profile
        print("\n👤 Loading personal profile...")
        profile_loader = PersonalProfileLoader()
        
        if not profile_loader.communication_style:
            print("❌ No profile loaded - showing default behavior")
            return
        
        print("\n🎯 Profile-Enhanced Features:")
        print("-" * 30)
        
        # 1. Communication Style Adaptation
        print(f"📢 Communication Style: {profile_loader.communication_style.conversation_style}")
        print(f"💬 Response Length: {profile_loader.communication_style.response_length}")
        print(f"😄 Humor Style: {profile_loader.communication_style.humor_style}")
        print(f"🎭 Sass Level: {profile_loader.communication_style.sass_level}")
        
        # 2. Interest-Based Research
        print(f"\n🔍 Research Permissions:")
        if profile_loader.interest_profile.research_permissions:
            for topic, permission in profile_loader.interest_profile.research_permissions.items():
                print(f"   {topic}: {permission}")
        
        # 3. Interest Level Detection
        print(f"\n📊 Interest Level Detection:")
        test_topics = ["machine learning", "cooking", "politics", "AI project management"]
        for topic in test_topics:
            interest_level = profile_loader.get_interest_level(topic)
            related = profile_loader.get_related_interests(topic)
            print(f"   {topic}: {interest_level:.1f}/1.0 interest")
            if related:
                print(f"      Related: {', '.join(related)}")
        
        # 4. LLM Context Generation
        print(f"\n🧠 Enhanced LLM Context:")
        llm_context = profile_loader.get_context_for_llm()
        print("   Context that gets added to every conversation:")
        for line in llm_context.split('\n'):
            print(f"   > {line}")
        
        # 5. Demonstrate conversation differences
        print(f"\n💬 Conversation Impact Examples:")
        print("-" * 40)
        
        examples = [
            {
                "user_input": "Tell me about machine learning",
                "without_profile": "Generic explanation of ML concepts",
                "with_profile": "ML explanation connecting to your AI project, current tech stack, and career goals as a Product Manager"
            },
            {
                "user_input": "Can you research quantum computing?",
                "without_profile": "Ask permission, then provide general research",
                "with_profile": "Auto-approve research (if in profile), connect to your technology interests, focus on practical applications"
            },
            {
                "user_input": "I don't understand blockchain",
                "without_profile": "Generic blockchain explanation",
                "with_profile": "Explanation tailored to your learning style, connected to your interest ratings, using examples from your professional context"
            }
        ]
        
        for i, example in enumerate(examples, 1):
            print(f"\n{i}. User: '{example['user_input']}'")
            print(f"   Without Profile: {example['without_profile']}")
            print(f"   With Profile: {example['with_profile']}")
        
        print(f"\n🎆 Profile Benefits Summary:")
        print("   ✅ Immediate personality matching from day one")
        print("   ✅ Research permissions streamline exploration")
        print("   ✅ Interest levels guide conversation depth")
        print("   ✅ Professional context makes advice relevant")
        print("   ✅ Learning style adaptation improves understanding")
        print("   ✅ Related interests create natural connections")
        
        return True
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def show_profile_creation_guide():
    """Show guide for creating your personal profile."""
    print("\n📝 How to Create Your Personal Profile:")
    print("=" * 45)
    
    print("""
📝 Step 1: Copy the template
   cp personal_profile_template.md my_profile_guide.md

📝 Step 2: Fill out your information
   Edit the template with your actual preferences, interests, and context

📝 Step 3: Convert to JSON format
   Use the sample JSON structure in personal_profile.json as a guide
   
📝 Step 4: Save as personal_profile.json
   This file will be automatically loaded by the learning system

🎯 Key Sections to Focus On:
   • Communication Style: How you like to interact
   • Active Interests: What you're currently into
   • Research Permissions: Topics you want auto-research vs ask-first
   • Professional Context: Your work and current projects
   • Learning Style: How you prefer to receive information

💡 Pro Tips:
   • Be specific about your interests (not just "technology" but "AI/ML", "React development")
   • Set research permissions based on your curiosity vs privacy preferences
   • Include current projects/challenges for relevant advice
   • Update the "current_context" section regularly
   • Rate your interest levels honestly (1-5 scale)
    """)


def show_integration_benefits():
    """Show specific benefits of profile integration."""
    print("\n🚀 Integration Benefits:")
    print("=" * 30)
    
    benefits = [
        {
            "feature": "Research Permission Automation",
            "benefit": "Topics you love get auto-researched, sensitive topics always ask first",
            "example": "Auto-research AI/ML topics, always ask about personal topics"
        },
        {
            "feature": "Interest-Aware Curiosity",
            "benefit": "Follow-up questions connect to your existing passions",
            "example": "Connecting new tech trends to your current React projects"
        },
        {
            "feature": "Communication Style Matching",
            "benefit": "Penny adapts sass, humor, and detail level to your preferences",
            "example": "High sass + detailed explanations + playful humor"
        },
        {
            "feature": "Professional Context Awareness",
            "benefit": "Advice and research tailored to your role and current projects",
            "example": "ML explanations focused on product management applications"
        },
        {
            "feature": "Learning Style Adaptation",
            "benefit": "Information presented in your preferred format",
            "example": "Hands-on examples vs theoretical explanations"
        }
    ]
    
    for benefit in benefits:
        print(f"\n🎯 {benefit['feature']}:")
        print(f"   💡 {benefit['benefit']}")
        print(f"   🌱 Example: {benefit['example']}")


if __name__ == "__main__":
    print("👤 Personal Profile System Demo")
    print("""This demonstrates how a personal profile transforms your AI companion:
    
    🎯 Without Profile: Generic responses, asks permission for everything
    🎆 With Profile: Personalized responses, smart permissions, relevant context
    """)
    
    success = demo_profile_benefits()
    
    if success:
        show_profile_creation_guide()
        show_integration_benefits()
        
        print("\n🎉 Ready to Create Your Profile!")
        print("\n🔄 Next Steps:")
        print("   1. Edit personal_profile.json with your actual information")
        print("   2. Run: python penny_with_guided_learning.py")
        print("   3. Experience personalized AI conversations!")
        print("\n💡 The difference will be immediately noticeable - Penny will know you from day one!")
    else:
        print("\n⚠️ Please fix issues before creating your profile.")
