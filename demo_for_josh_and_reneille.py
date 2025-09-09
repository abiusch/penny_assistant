#!/usr/bin/env python3
"""
PennyGPT Demo Script for Josh and Reneille
Shows off personalized AI companion features with relationship awareness
"""

import sys
import os
import json
import time

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

print("🎭 PennyGPT Demo for Josh and Reneille")
print("=" * 50)
print("👋 Welcome to CJ's Enhanced AI Companion!")
print()

# Load CJ's profile to show relationship awareness
try:
    with open('cj_personal_profile.json', 'r') as f:
        profile = json.load(f)
    
    print("📝 Penny knows about CJ's relationships:")
    relationships = profile.get('relationships', {})
    
    # Show Josh info
    josh = relationships.get('friends', {}).get('josh', {})
    if josh:
        print(f"   👨 Josh '{josh['nickname']}' - {josh['context']}")
        print(f"      🏢 Current: {josh['current_job']}")
        print(f"      📋 Notes: {josh['notes']}")
    
    # Show Reneille info  
    reneille = relationships.get('friends', {}).get('reneille', {})
    if reneille:
        print(f"   👩 Reneille - {reneille['context']}")
        print(f"      🏢 Current: {reneille['current_job']}")
        print(f"      🎉 Life: {reneille['life_events']}")
        print(f"      ⭐ Personality: {reneille['personality']}")
    
    print()
    
    # Show demo highlights
    demo_notes = profile.get('demo_notes', {})
    if demo_notes:
        print("🎯 Demo Features to Showcase:")
        for highlight in demo_notes.get('demo_highlights', []):
            print(f"   • {highlight}")
        print()
    
except Exception as e:
    print(f"⚠️ Could not load profile: {e}")

print("🚀 Demo Conversation Starters:")
print("-" * 30)
print()

print("1. 📱 For Josh (Brochacho):")
print("   'Josh, meet Penny! She knows about our Verizon days.'")
print("   'Hey Penny, Josh works at Google now - any thoughts on tech transitions?'")
print("   'Penny, what do you think about Josh's nickname Brochacho?'")
print()

print("2. 💍 For Reneille:")
print("   'Reneille, this is Penny - she knows you're getting married!'")
print("   'Hey Penny, Reneille is super organized - any wedding tech tips?'")
print("   'Penny, what do you think about having two Google employees here?'")
print()

print("3. 🔥 Show Off Sass & Learning:")
print("   'Should I use microservices for everything?'")
print("   'What's the best JavaScript framework?'")
print("   'Hey Penny, research FastAPI performance optimization'")
print("   'My code isn't working and I don't know why'")
print()

print("4. 🤔 Demonstrate Curiosity & Corrections:")
print("   'I think React is better than Angular'")
print("   'Actually Penny, it's Vue, not React'")
print("   'What's your take on Python async patterns?'")
print()

print("5. 🎭 Personality & Relationship Awareness:")
print("   'Penny, tell Josh about the PennyGPT project'")
print("   'Reneille loves organization - any project management tips?'")
print("   'What do you think about having friends over to demo you?'")
print()

print("💬 Expected Penny Responses:")
print("=" * 30)
print("• Should recognize Josh as 'Brochacho' and reference Verizon history")
print("• Should acknowledge Reneille's wedding planning and organizational skills")
print("• Should show tech industry sass with constructive feedback")
print("• Should auto-approve FastAPI research without asking permission")
print("• Should ask sassy curiosity questions like 'What's your actual plan?'")
print("• Should learn from corrections gracefully")
print("• Should maintain warm but sassy tone throughout")
print()

print("🎯 Demo Success Indicators:")
print("• Josh and Reneille see genuine personality (not robotic)")
print("• Penny shows relationship awareness and context")
print("• Tech conversations feel natural and engaging")
print("• Sass comes through without being mean")
print("• Learning and curiosity features demonstrate intelligence")
print("• Overall: feels like talking to a competent friend with attitude")
print()

print("🚀 Ready to start the demo!")
print("Run: PYTHONPATH=src python3 cj_personalized_penny.py")
print()
print("😈 Let's show off what an AI companion with real personality looks like!")
