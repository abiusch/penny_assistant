#!/usr/bin/env python3
"""
Adaptive Sass Learning System
Combines user control with personality learning - sass controls become training data
"""

import json
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from collections import defaultdict

from sass_controller import SassLevel, SassConfig

@dataclass
class SassLearningEvent:
    """Records when user adjusts sass level and context"""
    timestamp: float
    context: Dict[str, Any]
    user_command: str
    from_sass: SassLevel
    to_sass: SassLevel
    topic: str
    emotion: str
    participants: List[str]

@dataclass
class LearnedSassPattern:
    """A learned pattern about when user prefers certain sass levels"""
    context_pattern: Dict[str, Any]  # What contexts this applies to
    preferred_sass: SassLevel
    confidence: float
    usage_count: int
    last_used: float
    examples: List[str]  # Example situations where this pattern applied

class AdaptiveSassLearning:
    """Learns user's sass preferences from their control usage"""
    
    def __init__(self, learning_data_path: str = "sass_learning.json"):
        self.learning_data_path = learning_data_path
        self.learning_events: List[SassLearningEvent] = []
        self.learned_patterns: List[LearnedSassPattern] = []
        self.context_sass_history: Dict[str, List[Tuple[SassLevel, float]]] = defaultdict(list)
        
        # Learning parameters
        self.min_pattern_confidence = 0.6
        self.pattern_decay_days = 30
        self.min_examples_for_pattern = 3
        
        self.load_learning_data()
    
    def record_sass_adjustment(self, user_command: str, from_sass: SassLevel, 
                             to_sass: SassLevel, context: Dict[str, Any]):
        """Record when user adjusts sass level for learning"""
        
        event = SassLearningEvent(
            timestamp=time.time(),
            context=context.copy(),
            user_command=user_command,
            from_sass=from_sass,
            to_sass=to_sass,
            topic=context.get('topic', 'general'),
            emotion=context.get('emotion', 'neutral'),
            participants=context.get('participants', [])
        )
        
        self.learning_events.append(event)
        
        # Update context history
        context_key = self._get_context_key(context)
        self.context_sass_history[context_key].append((to_sass, time.time()))
        
        # Trigger pattern learning
        self._update_learned_patterns()
        
        # Save learning data
        self.save_learning_data()
        
        print(f"🧠 Learned: User prefers {to_sass.value} sass for {context_key}")
    
    def get_learned_sass_for_context(self, context: Dict[str, Any]) -> Optional[SassLevel]:
        """Get the learned sass preference for this context"""
        
        context_key = self._get_context_key(context)
        
        # Check for exact context match first
        if context_key in self.context_sass_history:
            recent_adjustments = self._get_recent_adjustments(context_key)
            if recent_adjustments:
                # Return most recent preference with high confidence
                return recent_adjustments[0][0]
        
        # Check learned patterns
        best_pattern = self._find_best_matching_pattern(context)
        if best_pattern and best_pattern.confidence > self.min_pattern_confidence:
            return best_pattern.preferred_sass
        
        return None  # No learned preference
    
    def get_learning_insights(self) -> Dict[str, Any]:
        """Get insights about learned sass patterns"""
        
        insights = {
            "total_adjustments": len(self.learning_events),
            "learned_patterns": len(self.learned_patterns),
            "context_preferences": {},
            "recent_trends": [],
            "strongest_patterns": []
        }
        
        # Context preferences
        for pattern in self.learned_patterns:
            if pattern.confidence > self.min_pattern_confidence:
                context_desc = self._describe_context_pattern(pattern.context_pattern)
                insights["context_preferences"][context_desc] = {
                    "preferred_sass": pattern.preferred_sass.value,
                    "confidence": pattern.confidence,
                    "usage_count": pattern.usage_count
                }
        
        # Recent trends (last 7 days)
        recent_events = [e for e in self.learning_events 
                        if time.time() - e.timestamp < 7 * 24 * 3600]
        
        if recent_events:
            sass_counts = defaultdict(int)
            for event in recent_events:
                sass_counts[event.to_sass.value] += 1
            
            insights["recent_trends"] = [
                f"Used {sass} sass {count} times this week"
                for sass, count in sorted(sass_counts.items(), key=lambda x: x[1], reverse=True)
            ]
        
        # Strongest patterns
        strong_patterns = sorted(
            [p for p in self.learned_patterns if p.confidence > 0.8],
            key=lambda p: p.confidence,
            reverse=True
        )[:3]
        
        for pattern in strong_patterns:
            context_desc = self._describe_context_pattern(pattern.context_pattern)
            insights["strongest_patterns"].append({
                "context": context_desc,
                "preferred_sass": pattern.preferred_sass.value,
                "confidence": pattern.confidence
            })
        
        return insights
    
    def _get_context_key(self, context: Dict[str, Any]) -> str:
        """Generate a key representing the context"""
        topic = context.get('topic', 'general')
        emotion = context.get('emotion', 'neutral')
        participants = sorted(context.get('participants', []))
        
        key_parts = [topic, emotion]
        if participants:
            key_parts.extend(participants)
        
        return ":".join(key_parts)
    
    def _get_recent_adjustments(self, context_key: str, days: int = 7) -> List[Tuple[SassLevel, float]]:
        """Get recent sass adjustments for this context"""
        if context_key not in self.context_sass_history:
            return []
        
        cutoff_time = time.time() - (days * 24 * 3600)
        recent = [(sass, ts) for sass, ts in self.context_sass_history[context_key] 
                 if ts > cutoff_time]
        
        # Sort by timestamp, most recent first
        return sorted(recent, key=lambda x: x[1], reverse=True)
    
    def _find_best_matching_pattern(self, context: Dict[str, Any]) -> Optional[LearnedSassPattern]:
        """Find the best matching learned pattern for this context"""
        
        best_pattern = None
        best_score = 0.0
        
        for pattern in self.learned_patterns:
            score = self._calculate_pattern_match_score(pattern.context_pattern, context)
            if score > best_score and score > 0.5:  # Minimum match threshold
                best_score = score
                best_pattern = pattern
        
        return best_pattern
    
    def _calculate_pattern_match_score(self, pattern_context: Dict[str, Any], 
                                     current_context: Dict[str, Any]) -> float:
        """Calculate how well a pattern matches the current context"""
        
        score = 0.0
        total_factors = 0
        
        # Topic match
        if 'topic' in pattern_context:
            total_factors += 1
            if pattern_context['topic'] == current_context.get('topic'):
                score += 1.0
            elif pattern_context['topic'] in current_context.get('topic', ''):
                score += 0.5
        
        # Emotion match
        if 'emotion' in pattern_context:
            total_factors += 1
            if pattern_context['emotion'] == current_context.get('emotion'):
                score += 1.0
        
        # Participants match
        if 'participants' in pattern_context:
            total_factors += 1
            pattern_participants = set(pattern_context['participants'])
            current_participants = set(current_context.get('participants', []))
            
            if pattern_participants & current_participants:  # Any overlap
                overlap_ratio = len(pattern_participants & current_participants) / len(pattern_participants | current_participants)
                score += overlap_ratio
        
        return score / total_factors if total_factors > 0 else 0.0
    
    def _update_learned_patterns(self):
        """Update learned patterns based on recent events"""
        
        # Group events by context similarity
        context_groups = defaultdict(list)
        
        for event in self.learning_events:
            context_key = self._get_context_key(event.context)
            context_groups[context_key].append(event)
        
        # Update or create patterns for each context group
        for context_key, events in context_groups.items():
            if len(events) >= self.min_examples_for_pattern:
                self._update_pattern_for_context_group(events)
    
    def _update_pattern_for_context_group(self, events: List[SassLearningEvent]):
        """Update or create a pattern for a group of similar events"""
        
        if not events:
            return
        
        # Calculate preferred sass level for this context
        sass_counts = defaultdict(int)
        for event in events:
            sass_counts[event.to_sass] += 1
        
        # Find most common sass level
        preferred_sass = max(sass_counts.keys(), key=lambda k: sass_counts[k])
        
        # Calculate confidence based on consistency
        total_events = len(events)
        preferred_count = sass_counts[preferred_sass]
        confidence = preferred_count / total_events
        
        # Create context pattern from most recent event
        latest_event = max(events, key=lambda e: e.timestamp)
        context_pattern = {
            'topic': latest_event.topic,
            'emotion': latest_event.emotion,
            'participants': latest_event.participants
        }
        
        # Check if pattern already exists
        existing_pattern = None
        for pattern in self.learned_patterns:
            if self._calculate_pattern_match_score(pattern.context_pattern, context_pattern) > 0.9:
                existing_pattern = pattern
                break
        
        if existing_pattern:
            # Update existing pattern
            existing_pattern.preferred_sass = preferred_sass
            existing_pattern.confidence = confidence
            existing_pattern.usage_count = total_events
            existing_pattern.last_used = latest_event.timestamp
            existing_pattern.examples = [e.user_command for e in events[-3:]]  # Last 3 examples
        else:
            # Create new pattern
            new_pattern = LearnedSassPattern(
                context_pattern=context_pattern,
                preferred_sass=preferred_sass,
                confidence=confidence,
                usage_count=total_events,
                last_used=latest_event.timestamp,
                examples=[e.user_command for e in events[-3:]]
            )
            self.learned_patterns.append(new_pattern)
    
    def _describe_context_pattern(self, context_pattern: Dict[str, Any]) -> str:
        """Generate human-readable description of a context pattern"""
        
        parts = []
        
        if context_pattern.get('topic'):
            parts.append(f"topic: {context_pattern['topic']}")
        
        if context_pattern.get('emotion'):
            parts.append(f"mood: {context_pattern['emotion']}")
        
        if context_pattern.get('participants'):
            participants = ", ".join(context_pattern['participants'])
            parts.append(f"with: {participants}")
        
        return " | ".join(parts) if parts else "general"
    
    def save_learning_data(self):
        """Save learning data to file"""
        try:
            data = {
                "learning_events": [
                    {
                        "timestamp": e.timestamp,
                        "context": e.context,
                        "user_command": e.user_command,
                        "from_sass": e.from_sass.value,
                        "to_sass": e.to_sass.value,
                        "topic": e.topic,
                        "emotion": e.emotion,
                        "participants": e.participants
                    }
                    for e in self.learning_events
                ],
                "learned_patterns": [
                    {
                        "context_pattern": p.context_pattern,
                        "preferred_sass": p.preferred_sass.value,
                        "confidence": p.confidence,
                        "usage_count": p.usage_count,
                        "last_used": p.last_used,
                        "examples": p.examples
                    }
                    for p in self.learned_patterns
                ]
            }
            
            with open(self.learning_data_path, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            print(f"⚠️ Could not save sass learning data: {e}")
    
    def load_learning_data(self):
        """Load learning data from file"""
        try:
            if not hasattr(self, 'learning_data_path') or not self.learning_data_path:
                return
                
            import os
            if not os.path.exists(self.learning_data_path):
                return
            
            with open(self.learning_data_path, 'r') as f:
                data = json.load(f)
            
            # Load learning events
            self.learning_events = []
            for event_data in data.get("learning_events", []):
                event = SassLearningEvent(
                    timestamp=event_data["timestamp"],
                    context=event_data["context"],
                    user_command=event_data["user_command"],
                    from_sass=SassLevel(event_data["from_sass"]),
                    to_sass=SassLevel(event_data["to_sass"]),
                    topic=event_data["topic"],
                    emotion=event_data["emotion"],
                    participants=event_data["participants"]
                )
                self.learning_events.append(event)
            
            # Load learned patterns
            self.learned_patterns = []
            for pattern_data in data.get("learned_patterns", []):
                pattern = LearnedSassPattern(
                    context_pattern=pattern_data["context_pattern"],
                    preferred_sass=SassLevel(pattern_data["preferred_sass"]),
                    confidence=pattern_data["confidence"],
                    usage_count=pattern_data["usage_count"],
                    last_used=pattern_data["last_used"],
                    examples=pattern_data["examples"]
                )
                self.learned_patterns.append(pattern)
            
            # Rebuild context history
            self.context_sass_history = defaultdict(list)
            for event in self.learning_events:
                context_key = self._get_context_key(event.context)
                self.context_sass_history[context_key].append((event.to_sass, event.timestamp))
                
        except Exception as e:
            print(f"⚠️ Could not load sass learning data: {e}")

def create_adaptive_sass_learning() -> AdaptiveSassLearning:
    """Factory function to create adaptive sass learning system"""
    return AdaptiveSassLearning()

# Example usage and testing
if __name__ == "__main__":
    print("🧠 Testing Adaptive Sass Learning System...")
    
    learning = create_adaptive_sass_learning()
    
    # Simulate some learning events
    test_scenarios = [
        # User prefers minimal sass during programming frustration
        ("tone it down", SassLevel.MEDIUM, SassLevel.MINIMAL, 
         {'topic': 'programming', 'emotion': 'frustrated', 'participants': []}),
        ("professional mode", SassLevel.SPICY, SassLevel.MINIMAL,
         {'topic': 'programming', 'emotion': 'frustrated', 'participants': []}),
        
        # User likes spicy sass when talking about Josh
        ("be more sassy", SassLevel.MEDIUM, SassLevel.SPICY,
         {'topic': 'conversation', 'emotion': 'neutral', 'participants': ['josh']}),
        ("turn it up", SassLevel.LITE, SassLevel.SPICY,
         {'topic': 'conversation', 'emotion': 'neutral', 'participants': ['josh']}),
        
        # User prefers medium sass for general conversation
        ("normal sass", SassLevel.MINIMAL, SassLevel.MEDIUM,
         {'topic': 'conversation', 'emotion': 'neutral', 'participants': []}),
    ]
    
    # Record learning events
    for command, from_sass, to_sass, context in test_scenarios:
        learning.record_sass_adjustment(command, from_sass, to_sass, context)
    
    # Test learned preferences
    test_contexts = [
        {'topic': 'programming', 'emotion': 'frustrated', 'participants': []},
        {'topic': 'conversation', 'emotion': 'neutral', 'participants': ['josh']},
        {'topic': 'conversation', 'emotion': 'neutral', 'participants': []},
        {'topic': 'programming', 'emotion': 'neutral', 'participants': []},  # New context
    ]
    
    print("\n🎯 Testing Learned Preferences:")
    for i, context in enumerate(test_contexts, 1):
        learned_sass = learning.get_learned_sass_for_context(context)
        context_key = learning._get_context_key(context)
        
        if learned_sass:
            print(f"{i}. {context_key} → Learned preference: {learned_sass.value}")
        else:
            print(f"{i}. {context_key} → No learned preference (use default)")
    
    # Show learning insights
    insights = learning.get_learning_insights()
    print(f"\n📊 Learning Insights:")
    print(f"   Total adjustments: {insights['total_adjustments']}")
    print(f"   Learned patterns: {insights['learned_patterns']}")
    
    if insights['context_preferences']:
        print(f"   Context preferences:")
        for context, pref in insights['context_preferences'].items():
            print(f"     {context}: {pref['preferred_sass']} (confidence: {pref['confidence']:.2f})")
    
    print("✅ Adaptive sass learning system test completed!")
