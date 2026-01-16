#!/usr/bin/env python3
"""
CJ-Enhanced Guided Learning System
Integrates CJ's personal and persona profiles for truly personalized learning
"""

import sys
import os
import json
import time
from typing import Dict, List, Optional, Any, Tuple

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.core.guided_learning_system import GuidedLearningSystem, LearningOpportunity, LearningOpportunityType, ResearchPermissionStrategy


class CJEnhancedLearningSystem(GuidedLearningSystem):
    """Guided learning system enhanced with CJ's specific profile and preferences."""
    
    def __init__(self, emotional_memory_system):
        super().__init__(emotional_memory_system)
        
        # Load CJ's specific profiles
        self.cj_profile = self._load_cj_profile()
        self.cj_persona = self._load_cj_persona()
        
        if self.cj_profile:
            print("✅ CJ's personal profile loaded")
            print(f"   Role: {self.cj_profile.get('professional_context', {}).get('role', 'Unknown')}")
            print(f"   Communication: {self.cj_profile.get('communication_style', {}).get('verbosity', 'Unknown')}")
        
        if self.cj_persona:
            print("✅ CJ's persona profile loaded")
            print(f"   Style: {self.cj_persona.get('meta', {}).get('name', 'Unknown')}")
    
    def _load_cj_profile(self) -> Optional[Dict]:
        """Load CJ's personal profile."""
        try:
            with open('cj_personal_profile.json', 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️ Could not load CJ's personal profile: {e}")
            return None
    
    def _load_cj_persona(self) -> Optional[Dict]:
        """Load CJ's persona profile."""
        try:
            with open('cj_persona_profile.json', 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️ Could not load CJ's persona profile: {e}")
            return None
    
    def detect_learning_opportunities(self, user_input: str, conversation_context: str) -> List[LearningOpportunity]:
        """Enhanced learning opportunity detection using CJ's profile."""
        opportunities = super().detect_learning_opportunities(user_input, conversation_context)
        
        if not self.cj_profile:
            return opportunities
        
        user_lower = user_input.lower()
        
        # Enhanced detection based on CJ's active interests
        active_interests = self.cj_profile.get('interests', {}).get('active', [])
        evergreen_interests = self.cj_profile.get('interests', {}).get('evergreen', [])
        all_interests = active_interests + evergreen_interests
        
        for interest in all_interests:
            # Check if any words from the interest appear in user input
            interest_words = interest.lower().split()
            if any(word in user_lower for word in interest_words):
                # Check auto-approval settings
                auto_approve = self._should_auto_approve(interest)
                expected_interest = 0.9 if interest in active_interests else 0.7
                
                opportunities.append(LearningOpportunity(
                    opportunity_type=LearningOpportunityType.INTEREST_DEEPENING,
                    topic=interest,
                    context=user_input,
                    user_input=user_input,
                    confidence=0.8,
                    suggested_research=f"Explore {interest} in context of current projects",
                    permission_strategy=ResearchPermissionStrategy.DIRECT_ASK if not auto_approve else ResearchPermissionStrategy.INTEREST_BUILDING,
                    expected_user_interest=expected_interest
                ))
        
        # Enhanced detection for CJ's current projects
        current_projects = self.cj_profile.get('professional_context', {}).get('current_projects', [])
        for project in current_projects:
            project_keywords = project.lower().split()
            if any(keyword in user_lower for keyword in project_keywords):
                opportunities.append(LearningOpportunity(
                    opportunity_type=LearningOpportunityType.PROBLEM_SOLVING,
                    topic=f"{project} optimization",
                    context=user_input,
                    user_input=user_input,
                    confidence=0.9,
                    suggested_research=f"Research solutions for {project}",
                    permission_strategy=ResearchPermissionStrategy.PROBLEM_SOLVING,
                    expected_user_interest=0.95
                ))
        
        # Enhanced detection for CJ's tech stack
        tech_stack = self.cj_profile.get('professional_context', {}).get('stack', [])
        for tech in tech_stack:
            if tech.lower() in user_lower:
                opportunities.append(LearningOpportunity(
                    opportunity_type=LearningOpportunityType.RESEARCH_REQUEST,
                    topic=f"{tech} best practices",
                    context=user_input,
                    user_input=user_input,
                    confidence=0.8,
                    suggested_research=f"Research latest {tech} patterns and optimizations",
                    permission_strategy=ResearchPermissionStrategy.DIRECT_ASK,
                    expected_user_interest=0.8
                ))
        
        return opportunities
    
    def _should_auto_approve(self, topic: str) -> bool:
        """Check if topic should be auto-approved based on CJ's preferences."""
        if not self.cj_profile:
            return False
        
        auto_approve_topics = self.cj_profile.get('research_permissions', {}).get('auto_approve', [])
        
        topic_lower = topic.lower()
        for auto_topic in auto_approve_topics:
            if any(word in topic_lower for word in auto_topic.lower().split()):
                return True
        
        return False
    
    def request_research_permission(self, opportunity: LearningOpportunity) -> str:
        """Generate permission request using CJ's sassy communication style."""
        if not self.cj_profile:
            return super().request_research_permission(opportunity)
        
        # Check auto-approval first
        if self._should_auto_approve(opportunity.topic):
            sassy_auto_responses = [
                f"Already researching {opportunity.topic} because I know you're obsessed with this stuff.",
                f"On it - {opportunity.topic} is totally your jam and you know it.",
                f"Researching {opportunity.topic} automatically since you clearly live for this."
            ]
            import random
            return random.choice(sassy_auto_responses)
        
        # Check if it's a restricted topic
        never_topics = self.cj_profile.get('research_permissions', {}).get('never', [])
        for never_topic in never_topics:
            if any(word in opportunity.topic.lower() for word in never_topic.lower().split()):
                return ""  # Don't offer research for restricted topics
        
        # Generate sassy permission requests based on opportunity type
        if opportunity.opportunity_type == LearningOpportunityType.RESEARCH_REQUEST:
            sassy_requests = [
                f"I can research {opportunity.topic} for you. Why: because apparently Google is too mainstream. Want me to dig into the good stuff?",
                f"Research {opportunity.topic}? Sure, I'll do the heavy lifting while you sit there looking pretty. Interested?",
                f"Want me to research {opportunity.topic}? I promise to skip the bullshit marketing fluff. Sound good?"
            ]
        
        elif opportunity.opportunity_type == LearningOpportunityType.PROBLEM_SOLVING:
            sassy_requests = [
                f"I can research solutions for {opportunity.topic}. Why: because trial-and-error is for masochists. Want actual working approaches?",
                f"Research {opportunity.topic} solutions? Yeah, let's skip the 'throw shit at the wall' approach. Shall I find what actually works?",
                f"Want me to dig into {opportunity.topic}? I'll find solutions that don't suck. Worth doing?"
            ]
        
        elif opportunity.opportunity_type == LearningOpportunityType.INTEREST_DEEPENING:
            sassy_requests = [
                f"Since you're clearly into {opportunity.topic}, want me to find the latest developments? I'll skip the obvious stuff.",
                f"More {opportunity.topic} info? Fine, I'll feed your obsession with quality research. Interested?",
                f"I could explore {opportunity.topic} deeper. Warning: might actually be useful. Want me to proceed?"
            ]
        
        else:
            sassy_requests = [
                f"I could research {opportunity.topic} and give you the no-bullshit breakdown you prefer. Interested?",
                f"Want me to dig into {opportunity.topic}? I promise to skip the corporate buzzword bingo. Sound good?"
            ]
        
        import random
        return random.choice(sassy_requests)
    
    def _get_project_connection(self, topic: str) -> str:
        """Find connection between topic and CJ's current projects."""
        if not self.cj_profile:
            return "current"
        
        current_projects = self.cj_profile.get('professional_context', {}).get('current_projects', [])
        
        topic_lower = topic.lower()
        for project in current_projects:
            project_words = project.lower().split()
            if any(word in topic_lower for word in project_words):
                return "PennyGPT"
        
        # Check against tech stack
        tech_stack = self.cj_profile.get('professional_context', {}).get('stack', [])
        for tech in tech_stack:
            if tech.lower() in topic_lower:
                return "current"
        
        return "broader"
    
    def generate_curiosity_question(self, topic: str, context: str) -> str:
        """Generate sassy curiosity questions in CJ's preferred style."""
        if not self.cj_profile:
            return super().generate_curiosity_question(topic, context)
        
        # CJ prefers concise, direct questions with edge
        sassy_questions = [
            f"What's your actual plan with {topic}, or are we just winging it?",
            f"How's {topic} fitting into your grand PennyGPT empire?",
            f"Any specific {topic} disasters you're trying to avoid?",
            f"What's the {topic} situation - smooth sailing or dumpster fire?",
            f"Real talk: is {topic} working for you or just looking pretty?",
            f"What's your hot take on {topic} for your setup?",
            f"How badly is {topic} breaking things right now?",
            f"What's the {topic} reality check looking like?"
        ]
        
        import random
        return random.choice(sassy_questions)
    
    def get_learning_context_for_llm(self) -> str:
        """Get learning context enhanced with CJ's profile."""
        base_context = super().get_learning_context_for_llm()
        
        if not self.cj_profile:
            return base_context
        
        cj_context_parts = []
        
        # Add CJ's communication preferences
        comm_style = self.cj_profile.get('communication_style', {})
        if comm_style.get('verbosity') == 'concise-by-default':
            cj_context_parts.append("User prefers concise responses with answer-first structure")
        
        if comm_style.get('structure'):
            structure = comm_style['structure']
            if isinstance(structure, list):
                cj_context_parts.append(f"Response structure: {' → '.join(structure)}")
        
        # Add current project context
        current_projects = self.cj_profile.get('professional_context', {}).get('current_projects', [])
        if current_projects:
            cj_context_parts.append(f"Current project: {current_projects[0]}")
        
        # Add tech stack context
        tech_stack = self.cj_profile.get('professional_context', {}).get('stack', [])
        if tech_stack:
            main_stack = tech_stack[:3]  # Top 3 technologies
            cj_context_parts.append(f"Tech stack: {', '.join(main_stack)}")
        
        # Add learning preferences
        learning_style = self.cj_profile.get('learning_style', {})
        if learning_style.get('preference') == 'hands-on':
            cj_context_parts.append("Learning style: hands-on with runnable examples")
        
        # Add short-term goals
        short_term_goals = self.cj_profile.get('professional_context', {}).get('goals_short_term', [])
        if short_term_goals:
            cj_context_parts.append(f"Current focus: {short_term_goals[0]}")
        
        # Combine with base context
        all_context = [base_context] + cj_context_parts
        return "\\n".join(filter(None, all_context))
    
    def adapt_for_sensitivity(self, user_input: str) -> bool:
        """Check if we should switch to sensitive mode based on CJ's profile."""
        if not self.cj_profile:
            return False
        
        # Check CJ's sensitive triggers
        sensitive_triggers = self.cj_profile.get('communication_style', {}).get('sensitive_mode', {}).get('when_triggered_by', [])
        
        user_lower = user_input.lower()
        for trigger in sensitive_triggers:
            if trigger in user_lower:
                return True
        
        return False


def create_cj_enhanced_learning_system(emotional_memory_system):
    """Factory function to create CJ's enhanced learning system."""
    return CJEnhancedLearningSystem(emotional_memory_system)


if __name__ == "__main__":
    print("👤 CJ-Enhanced Guided Learning System Test")
    print("=" * 50)
    
    # Test the enhanced system
    try:
        from emotional_memory_system import EmotionalMemorySystem
        from memory_system import MemoryManager
        
        memory_manager = MemoryManager()
        emotional_memory = EmotionalMemorySystem(memory_manager)
        cj_learning = CJEnhancedLearningSystem(emotional_memory)
        
        print("\\n🧪 Testing CJ-Specific Detection:")
        print("-" * 30)
        
        test_inputs = [
            "I'm working on the FastAPI daemon for PennyGPT",
            "How do I improve ElevenLabs TTS latency?",
            "Python async patterns for voice assistants",
            "Menu-bar app integration challenges",
            "MCP agent design patterns",
        ]
        
        for user_input in test_inputs:
            print(f"\\n📝 Input: '{user_input}'")
            opportunities = cj_learning.detect_learning_opportunities(user_input, "context")
            
            if opportunities:
                best_opp = max(opportunities, key=lambda x: x.confidence * x.expected_user_interest)
                print(f"   🎯 Detected: {best_opp.opportunity_type.value}")
                print(f"   📋 Topic: {best_opp.topic}")
                print(f"   🎭 Interest: {best_opp.expected_user_interest:.2f}")
                
                permission_request = cj_learning.request_research_permission(best_opp)
                if permission_request:
                    print(f"   💬 Permission: '{permission_request}'")
                else:
                    print("   🚫 Auto-approved or restricted")
            else:
                print("   ❌ No opportunities detected")
        
        print("\\n📊 Enhanced Context:")
        context = cj_learning.get_learning_context_for_llm()
        print(context)
        
        print("\\n✅ CJ-Enhanced Learning System working correctly!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
