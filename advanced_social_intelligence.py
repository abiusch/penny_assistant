#!/usr/bin/env python3
"""
Advanced Social Intelligence System for Penny
Phase 1.5 Days 4-14: Social awareness and relationship modeling
"""

import json
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import re

class SocialContext(Enum):
    PROBLEM_SOLVING = "problem_solving"
    BRAINSTORMING = "brainstorming"
    DECISION_MAKING = "decision_making"
    VENTING = "venting"
    CELEBRATION = "celebration"
    CRISIS = "crisis"
    CASUAL_CHAT = "casual_chat"
    PROFESSIONAL = "professional"
    PERSONAL = "personal"

class CommunicationTiming(Enum):
    ADVICE_MOMENT = "advice_moment"
    VALIDATION_MOMENT = "validation_moment"
    SPACE_GIVING = "space_giving"
    ACTIVE_LISTENING = "active_listening"
    PROBLEM_SOLVING = "problem_solving"

@dataclass
class PersonProfile:
    """Enhanced person profile with social intelligence"""
    name: str
    relationship_type: str  # friend, colleague, family, mentor, etc.
    communication_style: str  # direct, gentle, analytical, emotional, etc.
    stress_indicators: List[str]  # verbal/behavioral patterns when stressed
    support_preferences: List[str]  # how they prefer to receive help
    interaction_patterns: Dict[str, Any]  # historical interaction patterns
    emotional_patterns: Dict[str, Any]  # emotional response patterns
    last_interaction: Optional[datetime] = None
    relationship_dynamic_score: float = 0.5  # 0-1 closeness/trust level

@dataclass
class RelationshipDynamic:
    """Models relationship between multiple people"""
    person_a: str
    person_b: str
    relationship_type: str  # professional, personal, mentor-mentee, etc.
    power_dynamic: str  # equal, hierarchical, supportive, etc.
    communication_pattern: str  # collaborative, competitive, supportive, etc.
    conflict_resolution_style: str
    shared_context: List[str]  # shared projects, interests, history
    tension_indicators: List[str]  # signs of relationship stress
    last_observed: datetime = datetime.now()

@dataclass
class SocialSituation:
    """Current social situation analysis"""
    primary_context: SocialContext
    participants: List[str]
    emotional_atmosphere: str
    communication_needs: List[CommunicationTiming]
    relationship_factors: List[str]
    suggested_approach: str
    confidence_level: float

class AdvancedSocialIntelligence:
    """Advanced social awareness and relationship modeling system"""

    def __init__(self, db_path: str = "social_intelligence.db"):
        self.db_path = db_path
        self.person_profiles: Dict[str, PersonProfile] = {}
        self.relationship_dynamics: Dict[str, RelationshipDynamic] = {}

        # Initialize database
        self._init_database()
        self._load_profiles()

        # Social intelligence patterns
        self.stress_indicators = {
            "verbal": [
                "ugh", "argh", "whatever", "fine", "tired", "exhausted",
                "overwhelming", "can't deal", "done with", "fed up"
            ],
            "behavioral": [
                "short responses", "delayed replies", "work late",
                "skipping meetings", "avoiding calls", "being quiet"
            ]
        }

        self.support_preferences = {
            "problem_solving": ["help debug", "brainstorm solutions", "practical advice"],
            "emotional": ["listen", "validate feelings", "empathy", "understanding"],
            "space": ["time alone", "work independently", "minimal check-ins"],
            "distraction": ["chat about other things", "humor", "lighten mood"]
        }

        self.communication_timing_patterns = {
            "advice_moment": [
                "what should I do", "any ideas", "how would you approach",
                "need suggestions", "stuck on", "not sure how to"
            ],
            "validation_moment": [
                "feeling", "frustrated", "proud", "excited", "worried",
                "think I", "seems like", "just wanted to say"
            ],
            "space_giving": [
                "need to think", "processing", "overwhelmed", "lot on my mind",
                "dealing with", "working through"
            ]
        }

    def _init_database(self):
        """Initialize SQLite database for social intelligence"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Person profiles table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS person_profiles (
                name TEXT PRIMARY KEY,
                relationship_type TEXT,
                communication_style TEXT,
                stress_indicators TEXT,
                support_preferences TEXT,
                interaction_patterns TEXT,
                emotional_patterns TEXT,
                last_interaction TEXT,
                relationship_dynamic_score REAL
            )
        """)

        # Relationship dynamics table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS relationship_dynamics (
                id TEXT PRIMARY KEY,
                person_a TEXT,
                person_b TEXT,
                relationship_type TEXT,
                power_dynamic TEXT,
                communication_pattern TEXT,
                conflict_resolution_style TEXT,
                shared_context TEXT,
                tension_indicators TEXT,
                last_observed TEXT
            )
        """)

        # Social interaction history
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS social_interactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                participants TEXT,
                context_type TEXT,
                user_input TEXT,
                detected_emotions TEXT,
                social_response TEXT,
                effectiveness_score REAL
            )
        """)

        conn.commit()
        conn.close()

    def _load_profiles(self):
        """Load existing profiles from database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Load person profiles
        cursor.execute("SELECT * FROM person_profiles")
        for row in cursor.fetchall():
            name, rel_type, comm_style, stress_ind, support_pref, int_patterns, emo_patterns, last_int, rel_score = row

            self.person_profiles[name] = PersonProfile(
                name=name,
                relationship_type=rel_type,
                communication_style=comm_style,
                stress_indicators=json.loads(stress_ind) if stress_ind else [],
                support_preferences=json.loads(support_pref) if support_pref else [],
                interaction_patterns=json.loads(int_patterns) if int_patterns else {},
                emotional_patterns=json.loads(emo_patterns) if emo_patterns else {},
                last_interaction=datetime.fromisoformat(last_int) if last_int else None,
                relationship_dynamic_score=rel_score or 0.5
            )

        # Load relationship dynamics
        cursor.execute("SELECT * FROM relationship_dynamics")
        for row in cursor.fetchall():
            id_str, person_a, person_b, rel_type, power_dyn, comm_pattern, conflict_style, shared_ctx, tension_ind, last_obs = row

            self.relationship_dynamics[id_str] = RelationshipDynamic(
                person_a=person_a,
                person_b=person_b,
                relationship_type=rel_type,
                power_dynamic=power_dyn,
                communication_pattern=comm_pattern,
                conflict_resolution_style=conflict_style,
                shared_context=json.loads(shared_ctx) if shared_ctx else [],
                tension_indicators=json.loads(tension_ind) if tension_ind else [],
                last_observed=datetime.fromisoformat(last_obs) if last_obs else datetime.now()
            )

        conn.close()

    def analyze_social_situation(self, user_input: str, context: Dict[str, Any] = None) -> SocialSituation:
        """Analyze the current social situation comprehensively"""
        context = context or {}

        # Detect participants mentioned
        participants = self._detect_participants(user_input)

        # Analyze social context
        social_context = self._detect_social_context(user_input)

        # Detect emotional atmosphere
        emotional_atmosphere = self._analyze_emotional_atmosphere(user_input, participants)

        # Determine communication needs
        communication_needs = self._determine_communication_needs(user_input, social_context)

        # Analyze relationship factors
        relationship_factors = self._analyze_relationship_factors(participants, user_input)

        # Generate suggested approach
        suggested_approach = self._generate_social_approach(
            social_context, emotional_atmosphere, communication_needs, relationship_factors
        )

        # Calculate confidence
        confidence = self._calculate_social_confidence(participants, social_context)

        return SocialSituation(
            primary_context=social_context,
            participants=participants,
            emotional_atmosphere=emotional_atmosphere,
            communication_needs=communication_needs,
            relationship_factors=relationship_factors,
            suggested_approach=suggested_approach,
            confidence_level=confidence
        )

    def _detect_participants(self, user_input: str) -> List[str]:
        """Detect people mentioned in the input"""
        participants = []

        # Known names from profiles
        for name in self.person_profiles.keys():
            if name.lower() in user_input.lower():
                participants.append(name)

        # Common name patterns
        name_patterns = [
            r'\b([A-Z][a-z]+)\b',  # Capitalized words
            r'\bmy (boss|manager|colleague|friend|partner)\b',
            r'\bthe (team|group|client)\b'
        ]

        for pattern in name_patterns:
            matches = re.findall(pattern, user_input, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    match = match[0] if match[0] else match[1]
                if match not in participants and len(match) > 2:
                    participants.append(match)

        return participants[:3]  # Limit to 3 participants

    def _detect_social_context(self, user_input: str) -> SocialContext:
        """Detect the type of social situation"""
        text_lower = user_input.lower()

        context_patterns = {
            SocialContext.PROBLEM_SOLVING: [
                "how to", "stuck on", "can't figure", "problem with", "issue with", "bug", "error"
            ],
            SocialContext.BRAINSTORMING: [
                "ideas for", "thinking about", "what if", "brainstorm", "explore", "possibilities"
            ],
            SocialContext.DECISION_MAKING: [
                "should I", "decide", "choice", "option", "which", "better to", "pick"
            ],
            SocialContext.VENTING: [
                "ugh", "frustrated", "annoying", "can't believe", "ridiculous", "driving me crazy"
            ],
            SocialContext.CELEBRATION: [
                "awesome", "amazing", "success", "great news", "accomplished", "finished", "won"
            ],
            SocialContext.CRISIS: [
                "urgent", "emergency", "critical", "broken", "disaster", "panic", "help"
            ],
            SocialContext.PROFESSIONAL: [
                "meeting", "project", "deadline", "client", "presentation", "report", "team"
            ],
            SocialContext.PERSONAL: [
                "feeling", "relationship", "family", "friend", "personal", "life", "home"
            ]
        }

        # Count matches for each context
        context_scores = {}
        for context, patterns in context_patterns.items():
            score = sum(1 for pattern in patterns if pattern in text_lower)
            if score > 0:
                context_scores[context] = score

        if context_scores:
            return max(context_scores, key=context_scores.get)

        return SocialContext.CASUAL_CHAT

    def _analyze_emotional_atmosphere(self, user_input: str, participants: List[str]) -> str:
        """Analyze the emotional atmosphere of the situation"""
        text_lower = user_input.lower()

        # Positive indicators
        positive_indicators = [
            "excited", "happy", "great", "awesome", "love", "amazing", "perfect",
            "thrilled", "proud", "accomplished", "successful"
        ]

        # Negative indicators
        negative_indicators = [
            "frustrated", "annoying", "tired", "stressed", "worried", "anxious",
            "upset", "angry", "disappointed", "overwhelmed", "difficult"
        ]

        # Neutral indicators
        neutral_indicators = [
            "thinking", "wondering", "curious", "interesting", "considering", "discussing"
        ]

        positive_count = sum(1 for indicator in positive_indicators if indicator in text_lower)
        negative_count = sum(1 for indicator in negative_indicators if indicator in text_lower)
        neutral_count = sum(1 for indicator in neutral_indicators if indicator in text_lower)

        # Analyze participant-specific emotional context
        participant_stress = 0
        for participant in participants:
            if participant in self.person_profiles:
                profile = self.person_profiles[participant]
                stress_indicators = profile.stress_indicators
                if any(indicator in text_lower for indicator in stress_indicators):
                    participant_stress += 1

        # Determine overall atmosphere
        if negative_count + participant_stress > positive_count + neutral_count:
            return "tense" if participant_stress > 0 else "negative"
        elif positive_count > negative_count + neutral_count:
            return "positive"
        elif neutral_count > 0:
            return "neutral"
        else:
            return "unclear"

    def _determine_communication_needs(self, user_input: str, social_context: SocialContext) -> List[CommunicationTiming]:
        """Determine what type of communication response is needed"""
        text_lower = user_input.lower()
        needs = []

        # Check for explicit timing patterns
        for timing, patterns in self.communication_timing_patterns.items():
            if any(pattern in text_lower for pattern in patterns):
                needs.append(CommunicationTiming(timing))

        # Context-based needs
        if social_context == SocialContext.PROBLEM_SOLVING:
            needs.append(CommunicationTiming.PROBLEM_SOLVING)
        elif social_context == SocialContext.VENTING:
            needs.extend([CommunicationTiming.VALIDATION_MOMENT, CommunicationTiming.ACTIVE_LISTENING])
        elif social_context == SocialContext.CELEBRATION:
            needs.append(CommunicationTiming.VALIDATION_MOMENT)
        elif social_context == SocialContext.CRISIS:
            needs.extend([CommunicationTiming.PROBLEM_SOLVING, CommunicationTiming.ADVICE_MOMENT])

        # If no specific needs detected, default to active listening
        if not needs:
            needs.append(CommunicationTiming.ACTIVE_LISTENING)

        return list(set(needs))  # Remove duplicates

    def _analyze_relationship_factors(self, participants: List[str], user_input: str) -> List[str]:
        """Analyze relationship factors affecting the situation"""
        factors = []

        for participant in participants:
            if participant in self.person_profiles:
                profile = self.person_profiles[participant]

                # Check for stress indicators
                if any(indicator in user_input.lower() for indicator in profile.stress_indicators):
                    factors.append(f"{participant}_showing_stress")

                # Check communication style compatibility
                factors.append(f"{participant}_prefers_{profile.communication_style}")

                # Check relationship closeness
                if profile.relationship_dynamic_score > 0.7:
                    factors.append(f"close_relationship_with_{participant}")
                elif profile.relationship_dynamic_score < 0.3:
                    factors.append(f"distant_relationship_with_{participant}")

        # Check for multi-person dynamics
        if len(participants) > 1:
            for i, person_a in enumerate(participants):
                for person_b in participants[i+1:]:
                    dynamic_key = f"{person_a}_{person_b}"
                    reverse_key = f"{person_b}_{person_a}"

                    if dynamic_key in self.relationship_dynamics:
                        dynamic = self.relationship_dynamics[dynamic_key]
                        factors.append(f"dynamic_{dynamic.communication_pattern}_{person_a}_{person_b}")
                    elif reverse_key in self.relationship_dynamics:
                        dynamic = self.relationship_dynamics[reverse_key]
                        factors.append(f"dynamic_{dynamic.communication_pattern}_{person_b}_{person_a}")

        return factors

    def _generate_social_approach(self, social_context: SocialContext, emotional_atmosphere: str,
                                 communication_needs: List[CommunicationTiming],
                                 relationship_factors: List[str]) -> str:
        """Generate suggested approach based on social analysis"""

        approach_components = []

        # Base approach on context
        if social_context == SocialContext.PROBLEM_SOLVING:
            approach_components.append("Focus on practical solutions")
        elif social_context == SocialContext.VENTING:
            approach_components.append("Provide empathetic listening")
        elif social_context == SocialContext.CELEBRATION:
            approach_components.append("Share in the excitement")
        elif social_context == SocialContext.CRISIS:
            approach_components.append("Offer immediate support")

        # Adjust for emotional atmosphere
        if emotional_atmosphere == "tense":
            approach_components.append("Use calm, reassuring tone")
        elif emotional_atmosphere == "positive":
            approach_components.append("Match positive energy")
        elif emotional_atmosphere == "negative":
            approach_components.append("Validate feelings, offer support")

        # Adjust for communication needs
        if CommunicationTiming.SPACE_GIVING in communication_needs:
            approach_components.append("Give space, minimal pressure")
        elif CommunicationTiming.ADVICE_MOMENT in communication_needs:
            approach_components.append("Offer specific, actionable advice")
        elif CommunicationTiming.VALIDATION_MOMENT in communication_needs:
            approach_components.append("Acknowledge and validate feelings")

        # Factor in relationship dynamics
        stress_factors = [f for f in relationship_factors if "stress" in f]
        if stress_factors:
            approach_components.append("Be extra supportive, check stress levels")

        close_relationships = [f for f in relationship_factors if "close_relationship" in f]
        if close_relationships:
            approach_components.append("Use familiar, warm communication style")

        return "; ".join(approach_components) if approach_components else "Respond naturally and supportively"

    def _calculate_social_confidence(self, participants: List[str], social_context: SocialContext) -> float:
        """Calculate confidence level in social analysis"""
        confidence = 0.5  # Base confidence

        # Higher confidence for known participants
        known_participants = sum(1 for p in participants if p in self.person_profiles)
        if participants:
            confidence += 0.2 * (known_participants / len(participants))

        # Higher confidence for clear contexts
        clear_contexts = [SocialContext.PROBLEM_SOLVING, SocialContext.CELEBRATION, SocialContext.CRISIS]
        if social_context in clear_contexts:
            confidence += 0.2

        # Lower confidence for complex multi-person situations
        if len(participants) > 2:
            confidence -= 0.1

        return min(max(confidence, 0.0), 1.0)

    def learn_from_interaction(self, user_input: str, response: str, feedback: str = None):
        """Learn from social interactions to improve future responses"""
        # This would implement learning mechanisms
        # For now, we'll store the interaction for future analysis

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        situation = self.analyze_social_situation(user_input)

        cursor.execute("""
            INSERT INTO social_interactions
            (timestamp, participants, context_type, user_input, detected_emotions, social_response, effectiveness_score)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            datetime.now().isoformat(),
            json.dumps(situation.participants),
            situation.primary_context.value,
            user_input,
            situation.emotional_atmosphere,
            response,
            0.5  # Default effectiveness, could be improved with feedback
        ))

        conn.commit()
        conn.close()

    def add_person_profile(self, name: str, relationship_type: str,
                          communication_style: str = "balanced",
                          stress_indicators: List[str] = None,
                          support_preferences: List[str] = None):
        """Add or update a person profile"""

        profile = PersonProfile(
            name=name,
            relationship_type=relationship_type,
            communication_style=communication_style,
            stress_indicators=stress_indicators or [],
            support_preferences=support_preferences or [],
            interaction_patterns={},
            emotional_patterns={},
            relationship_dynamic_score=0.5
        )

        self.person_profiles[name] = profile

        # Save to database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT OR REPLACE INTO person_profiles
            (name, relationship_type, communication_style, stress_indicators,
             support_preferences, interaction_patterns, emotional_patterns,
             last_interaction, relationship_dynamic_score)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            name, relationship_type, communication_style,
            json.dumps(stress_indicators or []),
            json.dumps(support_preferences or []),
            json.dumps({}),
            json.dumps({}),
            None,
            0.5
        ))

        conn.commit()
        conn.close()

    def add_relationship_dynamic(self, person_a: str, person_b: str,
                               relationship_type: str, power_dynamic: str = "equal",
                               communication_pattern: str = "collaborative"):
        """Add relationship dynamic between two people"""

        dynamic_id = f"{person_a}_{person_b}"

        dynamic = RelationshipDynamic(
            person_a=person_a,
            person_b=person_b,
            relationship_type=relationship_type,
            power_dynamic=power_dynamic,
            communication_pattern=communication_pattern,
            conflict_resolution_style="collaborative",
            shared_context=[],
            tension_indicators=[]
        )

        self.relationship_dynamics[dynamic_id] = dynamic

        # Save to database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT OR REPLACE INTO relationship_dynamics
            (id, person_a, person_b, relationship_type, power_dynamic,
             communication_pattern, conflict_resolution_style, shared_context,
             tension_indicators, last_observed)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            dynamic_id, person_a, person_b, relationship_type, power_dynamic,
            communication_pattern, "collaborative", json.dumps([]),
            json.dumps([]), datetime.now().isoformat()
        ))

        conn.commit()
        conn.close()

def create_advanced_social_intelligence(db_path: str = "social_intelligence.db") -> AdvancedSocialIntelligence:
    """Factory function to create social intelligence system"""
    return AdvancedSocialIntelligence(db_path)

if __name__ == "__main__":
    # Demo and testing
    print("🧠 Advanced Social Intelligence System")
    print("=" * 60)

    # Create system
    social_ai = create_advanced_social_intelligence("test_social.db")

    # Add some test profiles
    social_ai.add_person_profile(
        "Josh", "friend", "analytical",
        stress_indicators=["quiet", "short responses", "works late"],
        support_preferences=["practical solutions", "space to think"]
    )

    social_ai.add_person_profile(
        "Reneille", "friend", "emotional",
        stress_indicators=["talks fast", "lots of questions", "seeks validation"],
        support_preferences=["empathetic listening", "validation", "brainstorming"]
    )

    social_ai.add_relationship_dynamic(
        "Josh", "Reneille", "colleagues", "equal", "complementary"
    )

    # Test social situation analysis
    test_scenarios = [
        "Josh is being weird about the project deadline and it's making me anxious",
        "Reneille and Josh had a disagreement in the meeting today",
        "Super excited about the feature launch but Josh seems stressed",
        "Need to figure out how to approach Josh about the timeline issue",
        "Reneille asked for my opinion on the Josh situation"
    ]

    print("\n🔬 Social Situation Analysis Tests:")
    for i, scenario in enumerate(test_scenarios, 1):
        print(f"\n{i}. SCENARIO: {scenario}")
        print("-" * 40)

        situation = social_ai.analyze_social_situation(scenario)

        print(f"Context: {situation.primary_context.value}")
        print(f"Participants: {', '.join(situation.participants)}")
        print(f"Emotional Atmosphere: {situation.emotional_atmosphere}")
        print(f"Communication Needs: {[need.value for need in situation.communication_needs]}")
        print(f"Suggested Approach: {situation.suggested_approach}")
        print(f"Confidence: {situation.confidence_level:.2f}")

    # Clean up
    import os
    os.remove("test_social.db")
    print("\n✅ Advanced Social Intelligence System test completed!")