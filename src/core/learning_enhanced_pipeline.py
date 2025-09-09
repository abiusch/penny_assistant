#!/usr/bin/env python3
"""
Enhanced Memory Pipeline with Guided Learning Integration
Integrates guided learning and reasoning into the existing conversation flow
"""

import sys
import os
import time
from typing import Dict, List, Optional, Any, Tuple

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from memory_enhanced_pipeline import MemoryEnhancedPipeline
from emotional_memory_system import EmotionalMemorySystem
from src.core.guided_learning_system import GuidedLearningSystem, LearningOpportunity


class LearningEnhancedPipeline(MemoryEnhancedPipeline):
    """Enhanced pipeline with guided learning and proactive curiosity."""
    
    def __init__(self, stt_engine, llm, tts_adapter, memory_manager):
        super().__init__(stt_engine, llm, tts_adapter, memory_manager)
        
        # Initialize guided learning system
        self.guided_learning = GuidedLearningSystem(self.emotional_memory)
        
        # Track conversation state for learning
        self.last_assistant_response = ""
        self.pending_research_requests = []
        self.waiting_for_permission = False
        self.current_research_topic = None
    
    def think(self, user_input: str, audio_duration: float = None) -> str:
        """Enhanced think method with guided learning integration."""
        
        # 1. Check for user corrections first
        correction = self.guided_learning.detect_correction_attempt(
            user_input, self.last_assistant_response
        )
        
        if correction:
            original_info, corrected_info = correction
            correction_id = self.guided_learning.record_user_correction(
                original_info,
                corrected_info,
                user_input,
                user_input
            )
            
            # Generate acknowledgment response
            response = self._generate_correction_acknowledgment(corrected_info)
            self._finalize_response(user_input, response)
            return response
        
        # 2. Check if user is responding to research permission request
        if self.waiting_for_permission and self.current_research_topic:
            permission_granted = self._parse_permission_response(user_input)
            
            if permission_granted is not None:
                self.waiting_for_permission = False
                
                if permission_granted:
                    # Conduct research and respond
                    response = self._conduct_research_and_respond(self.current_research_topic, user_input)
                else:
                    # Acknowledge and continue normally
                    response = self._acknowledge_permission_denied()
                    # Fall through to normal processing
                
                self.current_research_topic = None
                
                if permission_granted:
                    self._finalize_response(user_input, response)
                    return response
        
        # 3. Detect learning opportunities
        conversation_context = self.memory_manager.get_context_for_llm()
        learning_opportunities = self.guided_learning.detect_learning_opportunities(
            user_input, conversation_context
        )
        
        # 4. Get base response using existing pipeline
        base_response = super().think(user_input, audio_duration)
        
        # 5. Enhance response with learning elements
        enhanced_response = self._enhance_with_learning(
            base_response, user_input, learning_opportunities
        )
        
        # 6. Store for next iteration
        self.last_assistant_response = enhanced_response
        
        return enhanced_response
    
    def _parse_permission_response(self, user_input: str) -> Optional[bool]:
        """Parse user response to research permission request."""
        user_lower = user_input.lower().strip()
        
        # Positive responses
        positive = ['yes', 'yeah', 'sure', 'okay', 'ok', 'go ahead', 'please do', 
                   'that would be great', 'sounds good', 'please', 'do it']
        
        # Negative responses
        negative = ['no', 'nope', 'not now', 'maybe later', 'not really', 
                   'not necessary', 'skip it', 'no thanks']
        
        if any(pos in user_lower for pos in positive):
            return True
        elif any(neg in user_lower for neg in negative):
            return False
        
        return None  # Ambiguous response
    
    def _conduct_research_and_respond(self, topic: str, user_input: str) -> str:
        """Conduct research and generate response with findings."""
        # For now, simulate research with enhanced context
        # In the future, this would integrate with actual web search
        
        research_results = self._simulate_research(topic)
        
        # Store research session
        session_id = self.guided_learning.record_research_session(
            LearningOpportunity(
                opportunity_type="research_request",
                topic=topic,
                context=user_input,
                user_input=user_input,
                confidence=0.9,
                suggested_research=f"Research {topic}",
                permission_strategy="direct_ask",
                expected_user_interest=0.8
            ),
            permission_granted=True
        )
        
        # Generate response with research findings
        research_prompt = f"""
User asked about: {topic}
I've researched this topic and found: {research_results}

Provide a helpful response that:
1. Presents the key findings naturally
2. Maintains Penny's personality
3. Asks a follow-up question to deepen understanding
4. Shows genuine interest in the topic

Original user input: {user_input}
"""
        
        # Get enhanced context
        context = self._get_enhanced_context_with_learning()
        full_prompt = f"{context}\n\n{research_prompt}"
        
        research_response = self.llm.generate(full_prompt)
        
        # Update research session with results
        self.guided_learning.update_research_session(
            session_id, research_results
        )
        
        return research_response
    
    def _simulate_research(self, topic: str) -> str:
        """Simulate research results for topic (placeholder for actual research)."""
        # This would be replaced with actual web search integration
        return f"Current information about {topic} including recent developments, practical applications, and expert insights."
    
    def _acknowledge_permission_denied(self) -> str:
        """Generate acknowledgment when research permission is denied."""
        responses = [
            "No problem! Happy to just chat about it instead.",
            "Sure thing! What would you like to know?",
            "That's totally fine. What's on your mind about it?"
        ]
        
        import random
        return random.choice(responses)
    
    def _generate_correction_acknowledgment(self, corrected_info: str) -> str:
        """Generate acknowledgment of user correction."""
        responses = [
            f"Ah, you're absolutely right - {corrected_info}. Thanks for the correction!",
            f"Oh good catch! {corrected_info}. I'll remember that.",
            f"Thanks for clarifying - {corrected_info}. I appreciate you setting me straight."
        ]
        
        import random
        return random.choice(responses)
    
    def _enhance_with_learning(self, base_response: str, user_input: str, 
                             opportunities: List[LearningOpportunity]) -> str:
        """Enhance base response with learning opportunities."""
        
        if not opportunities:
            return base_response
        
        # Find the best opportunity to act on
        best_opportunity = max(opportunities, key=lambda op: op.confidence * op.expected_user_interest)
        
        # Only proceed if opportunity is strong enough
        if best_opportunity.confidence * best_opportunity.expected_user_interest < 0.4:
            return base_response
        
        # Generate permission request
        permission_request = self.guided_learning.request_research_permission(best_opportunity)
        
        # Set state for next interaction
        self.waiting_for_permission = True
        self.current_research_topic = best_opportunity.topic
        
        # Add permission request to response
        enhanced_response = f"{base_response}\n\n{permission_request}"
        
        # Record the opportunity
        session_id = self.guided_learning.record_research_session(
            best_opportunity, permission_granted=False  # Waiting for response
        )
        
        return enhanced_response
    
    def _get_enhanced_context_with_learning(self) -> str:
        """Get enhanced context including learning information."""
        base_context = self.emotional_memory.get_enhanced_context_for_llm()
        learning_context = self.guided_learning.get_learning_context_for_llm()
        
        context_parts = [base_context]
        if learning_context:
            context_parts.append(learning_context)
        
        return "\n".join(context_parts)
    
    def _finalize_response(self, user_input: str, response: str):
        """Finalize response by processing through memory systems."""
        # Process through emotional memory
        turn_id = f"{time.time():.3f}"
        self.emotional_memory.process_conversation_turn(
            user_input, response, turn_id
        )
        
        # Store conversation in base memory
        self.memory_manager.store_conversation(
            user_input, response, {
                'guided_learning': True,
                'timestamp': time.time()
            }
        )
    
    def get_learning_stats(self) -> Dict[str, Any]:
        """Get statistics about learning system performance."""
        stats = {}
        
        # Get research session stats
        with self.guided_learning.memory.base_memory.get_connection() as conn:
            cursor = conn.execute("""
                SELECT 
                    COUNT(*) as total_requests,
                    SUM(permission_granted) as granted,
                    SUM(research_conducted) as conducted,
                    AVG(feedback_rating) as avg_rating
                FROM research_sessions
                WHERE timestamp > ?
            """, (time.time() - 7*24*60*60,))  # Last week
            
            row = cursor.fetchone()
            if row:
                total, granted, conducted, avg_rating = row
                stats.update({
                    'research_requests_week': total or 0,
                    'permission_rate': (granted / total) if total else 0,
                    'completion_rate': (conducted / granted) if granted else 0,
                    'avg_feedback_rating': avg_rating or 0
                })
        
        # Get correction stats
        with self.guided_learning.memory.base_memory.get_connection() as conn:
            cursor = conn.execute("""
                SELECT COUNT(*) as corrections
                FROM user_corrections
                WHERE timestamp > ?
            """, (time.time() - 7*24*60*60,))
            
            corrections = cursor.fetchone()[0]
            stats['corrections_week'] = corrections or 0
        
        # Current learning goals
        stats['active_learning_goals'] = len([
            goal for goal in self.guided_learning.memory.learning_goals.values()
            if goal.user_interest_level > 0.4
        ])
        
        return stats


def create_learning_enhanced_pipeline(stt_engine, llm, tts_adapter, memory_manager):
    """Factory function to create learning-enhanced pipeline."""
    return LearningEnhancedPipeline(stt_engine, llm, tts_adapter, memory_manager)


# Integration function for easy replacement
def upgrade_to_learning_pipeline(existing_pipeline):
    """Upgrade existing pipeline to learning-enhanced version."""
    return LearningEnhancedPipeline(
        existing_pipeline.stt_engine,
        existing_pipeline.llm, 
        existing_pipeline.tts_adapter,
        existing_pipeline.memory_manager
    )
