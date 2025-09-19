#!/usr/bin/env python3
"""
Relationship Dynamics Engine for Penny
Multi-person relationship modeling and group dynamics awareness
"""

import json
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, asdict
from enum import Enum
import re

class RelationshipStatus(Enum):
    HARMONIOUS = "harmonious"
    NEUTRAL = "neutral"
    TENSE = "tense"
    CONFLICT = "conflict"
    SUPPORTIVE = "supportive"
    COLLABORATIVE = "collaborative"
    COMPETITIVE = "competitive"

class GroupDynamicType(Enum):
    BRAINSTORMING = "brainstorming"
    DECISION_MAKING = "decision_making"
    PROBLEM_SOLVING = "problem_solving"
    SOCIAL = "social"
    CRISIS_RESPONSE = "crisis_response"
    CELEBRATION = "celebration"
    CONFLICT_RESOLUTION = "conflict_resolution"

@dataclass
class RelationshipInsight:
    """Insight about a specific relationship"""
    person_a: str
    person_b: str
    current_status: RelationshipStatus
    trust_level: float  # 0-1
    communication_effectiveness: float  # 0-1
    recent_interactions: List[str]
    stress_factors: List[str]
    support_opportunities: List[str]
    recommended_approach: str

@dataclass
class GroupDynamic:
    """Analysis of group interactions"""
    participants: List[str]
    dynamic_type: GroupDynamicType
    power_structure: Dict[str, str]  # person -> role (leader, contributor, observer, etc.)
    communication_flow: Dict[str, List[str]]  # who talks to whom
    tension_points: List[Tuple[str, str]]  # pairs with tension
    collaboration_strengths: List[Tuple[str, str]]  # pairs that work well
    group_mood: str
    effectiveness_score: float
    recommended_facilitation: str

@dataclass
class SocialNetwork:
    """Model of the entire social network"""
    people: Set[str]
    relationships: Dict[Tuple[str, str], RelationshipInsight]
    groups: Dict[str, List[str]]  # group_name -> members
    influence_map: Dict[str, List[str]]  # who influences whom
    communication_patterns: Dict[str, Dict[str, float]]  # frequency matrix
    recent_events: List[Dict[str, Any]]

class RelationshipDynamicsEngine:
    """Engine for modeling and analyzing relationship dynamics"""

    def __init__(self, db_path: str = "relationship_dynamics.db"):
        self.db_path = db_path
        self.social_network = SocialNetwork(
            people=set(),
            relationships={},
            groups={},
            influence_map={},
            communication_patterns={},
            recent_events=[]
        )

        # Initialize database
        self._init_database()
        self._load_network()

        # Relationship pattern recognition
        self.tension_indicators = {
            "communication": [
                "not responding", "short replies", "avoiding", "being distant",
                "not talking", "ignoring", "cold shoulder", "formal tone"
            ],
            "behavioral": [
                "missed meetings", "left early", "working separately",
                "taking sides", "complaining about", "frustrated with"
            ],
            "verbal": [
                "disagreement", "argument", "conflict", "tension",
                "not happy", "issue with", "problem with", "annoyed"
            ]
        }

        self.collaboration_indicators = {
            "positive": [
                "working well together", "great collaboration", "synergy",
                "complementary", "builds on", "supports", "helps"
            ],
            "productive": [
                "getting things done", "efficient", "productive",
                "making progress", "solving problems", "achieving goals"
            ],
            "supportive": [
                "backing up", "covering for", "supporting", "helping out",
                "looking out for", "checking in", "encouraging"
            ]
        }

        self.power_dynamic_indicators = {
            "leadership": [
                "leads", "directs", "decides", "takes charge", "manages",
                "coordinates", "organizes", "delegates"
            ],
            "influence": [
                "convinces", "persuades", "influences", "guides",
                "mentors", "advises", "suggests"
            ],
            "expertise": [
                "expert in", "specialist", "knows about", "experienced",
                "skilled at", "good with", "authority on"
            ]
        }

    def _init_database(self):
        """Initialize database for relationship tracking"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Relationships table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS relationships (
                person_a TEXT,
                person_b TEXT,
                status TEXT,
                trust_level REAL,
                communication_effectiveness REAL,
                last_updated TEXT,
                interaction_history TEXT,
                stress_factors TEXT,
                PRIMARY KEY (person_a, person_b)
            )
        """)

        # Group interactions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS group_interactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                participants TEXT,
                dynamic_type TEXT,
                interaction_summary TEXT,
                outcomes TEXT,
                effectiveness_score REAL
            )
        """)

        # Social events table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS social_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                event_type TEXT,
                people_involved TEXT,
                description TEXT,
                impact_analysis TEXT
            )
        """)

        conn.commit()
        conn.close()

    def _load_network(self):
        """Load existing network data from database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Load relationships
        cursor.execute("SELECT * FROM relationships")
        for row in cursor.fetchall():
            person_a, person_b, status, trust, comm_eff, last_updated, history, stress = row

            self.social_network.people.add(person_a)
            self.social_network.people.add(person_b)

            insight = RelationshipInsight(
                person_a=person_a,
                person_b=person_b,
                current_status=RelationshipStatus(status) if status else RelationshipStatus.NEUTRAL,
                trust_level=trust or 0.5,
                communication_effectiveness=comm_eff or 0.5,
                recent_interactions=json.loads(history) if history else [],
                stress_factors=json.loads(stress) if stress else [],
                support_opportunities=[],
                recommended_approach=""
            )

            self.social_network.relationships[(person_a, person_b)] = insight

        conn.close()

    def analyze_relationship_dynamics(self, user_input: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Analyze relationship dynamics from user input"""
        context = context or {}

        # Extract people mentioned
        people_mentioned = self._extract_people(user_input)

        # Analyze relationship indicators
        relationship_analysis = {}

        if len(people_mentioned) >= 2:
            # Multi-person dynamics
            relationship_analysis = self._analyze_multi_person_dynamics(user_input, people_mentioned)
        elif len(people_mentioned) == 1:
            # Single person relationship with user
            relationship_analysis = self._analyze_user_person_relationship(user_input, people_mentioned[0])

        # Detect group dynamics if applicable
        group_dynamics = None
        if len(people_mentioned) > 2 or self._is_group_context(user_input):
            group_dynamics = self._analyze_group_dynamics(user_input, people_mentioned)

        # Update network based on analysis
        self._update_network(user_input, people_mentioned, relationship_analysis)

        return {
            "people_involved": people_mentioned,
            "relationship_insights": relationship_analysis,
            "group_dynamics": group_dynamics,
            "network_update": "updated",
            "recommendations": self._generate_relationship_recommendations(
                relationship_analysis, group_dynamics
            )
        }

    def _extract_people(self, text: str) -> List[str]:
        """Extract people mentioned in text"""
        people = []

        # Known people from network
        for person in self.social_network.people:
            if person.lower() in text.lower():
                people.append(person)

        # Common name patterns
        name_patterns = [
            r'\b([A-Z][a-z]{2,})\b',  # Capitalized names
            r'\bmy (boss|manager|colleague|friend|partner|team)\b',
            r'\bthe (team|group|client|customer)\b'
        ]

        for pattern in name_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    match = match[0] if match[0] else match[1]
                if match.lower() not in [p.lower() for p in people] and len(match) > 2:
                    people.append(match.title())

        return people[:5]  # Limit to 5 people

    def _analyze_multi_person_dynamics(self, text: str, people: List[str]) -> Dict[str, Any]:
        """Analyze dynamics between multiple people"""
        analysis = {"relationships": {}, "overall_dynamic": "neutral"}

        text_lower = text.lower()

        # Analyze each pair
        for i, person_a in enumerate(people):
            for person_b in people[i+1:]:
                pair_key = f"{person_a}-{person_b}"

                # Check for tension indicators
                tension_score = 0
                for category, indicators in self.tension_indicators.items():
                    for indicator in indicators:
                        if indicator in text_lower and (person_a.lower() in text_lower and person_b.lower() in text_lower):
                            tension_score += 1

                # Check for collaboration indicators
                collaboration_score = 0
                for category, indicators in self.collaboration_indicators.items():
                    for indicator in indicators:
                        if indicator in text_lower and (person_a.lower() in text_lower and person_b.lower() in text_lower):
                            collaboration_score += 1

                # Determine relationship status
                if tension_score > collaboration_score and tension_score > 0:
                    status = RelationshipStatus.TENSE
                elif collaboration_score > tension_score and collaboration_score > 0:
                    status = RelationshipStatus.COLLABORATIVE
                else:
                    status = RelationshipStatus.NEUTRAL

                analysis["relationships"][pair_key] = {
                    "status": status.value,
                    "tension_indicators": tension_score,
                    "collaboration_indicators": collaboration_score,
                    "context_from_input": self._extract_relationship_context(text, person_a, person_b)
                }

        # Determine overall dynamic
        if any(rel["status"] == "tense" for rel in analysis["relationships"].values()):
            analysis["overall_dynamic"] = "tension_present"
        elif any(rel["status"] == "collaborative" for rel in analysis["relationships"].values()):
            analysis["overall_dynamic"] = "collaborative"

        return analysis

    def _analyze_user_person_relationship(self, text: str, person: str) -> Dict[str, Any]:
        """Analyze relationship between user and one person"""
        analysis = {"person": person, "relationship_status": "neutral", "concerns": [], "positives": []}

        text_lower = text.lower()
        person_lower = person.lower()

        # Check for stress/concern indicators about this person
        concern_patterns = [
            "worried about", "concerned about", "issue with", "problem with",
            "frustrated with", "annoyed with", "confused about", "not sure about"
        ]

        for pattern in concern_patterns:
            if pattern in text_lower and person_lower in text_lower:
                analysis["concerns"].append(pattern)

        # Check for positive indicators
        positive_patterns = [
            "great work", "doing well", "proud of", "appreciate", "helpful",
            "supportive", "reliable", "talented", "good at"
        ]

        for pattern in positive_patterns:
            if pattern in text_lower and person_lower in text_lower:
                analysis["positives"].append(pattern)

        # Determine overall status
        if len(analysis["concerns"]) > len(analysis["positives"]):
            analysis["relationship_status"] = "needs_attention"
        elif len(analysis["positives"]) > len(analysis["concerns"]):
            analysis["relationship_status"] = "positive"

        return analysis

    def _analyze_group_dynamics(self, text: str, people: List[str]) -> GroupDynamic:
        """Analyze group dynamics from context"""
        text_lower = text.lower()

        # Determine dynamic type
        dynamic_type = GroupDynamicType.SOCIAL  # default

        if any(word in text_lower for word in ["meeting", "discussion", "brainstorm"]):
            dynamic_type = GroupDynamicType.BRAINSTORMING
        elif any(word in text_lower for word in ["decide", "choice", "decision"]):
            dynamic_type = GroupDynamicType.DECISION_MAKING
        elif any(word in text_lower for word in ["problem", "issue", "fix", "solve"]):
            dynamic_type = GroupDynamicType.PROBLEM_SOLVING
        elif any(word in text_lower for word in ["crisis", "urgent", "emergency"]):
            dynamic_type = GroupDynamicType.CRISIS_RESPONSE
        elif any(word in text_lower for word in ["celebrate", "success", "achievement"]):
            dynamic_type = GroupDynamicType.CELEBRATION
        elif any(word in text_lower for word in ["conflict", "disagree", "argument"]):
            dynamic_type = GroupDynamicType.CONFLICT_RESOLUTION

        # Analyze power structure
        power_structure = {}
        for person in people:
            person_lower = person.lower()

            # Check for leadership indicators
            leadership_score = 0
            for indicator in self.power_dynamic_indicators["leadership"]:
                if indicator in text_lower and person_lower in text_lower:
                    leadership_score += 1

            if leadership_score > 0:
                power_structure[person] = "leader"
            else:
                power_structure[person] = "contributor"

        # Detect tension points
        tension_points = []
        for i, person_a in enumerate(people):
            for person_b in people[i+1:]:
                if any(indicator in text_lower for indicator in self.tension_indicators["verbal"]):
                    if person_a.lower() in text_lower and person_b.lower() in text_lower:
                        tension_points.append((person_a, person_b))

        # Calculate effectiveness score
        effectiveness_score = 0.5  # baseline
        if dynamic_type in [GroupDynamicType.PROBLEM_SOLVING, GroupDynamicType.DECISION_MAKING]:
            if any(word in text_lower for word in ["resolved", "decided", "solved", "agreed"]):
                effectiveness_score += 0.3
        if len(tension_points) == 0:
            effectiveness_score += 0.2
        if any(word in text_lower for word in ["productive", "efficient", "good progress"]):
            effectiveness_score += 0.2

        effectiveness_score = min(effectiveness_score, 1.0)

        return GroupDynamic(
            participants=people,
            dynamic_type=dynamic_type,
            power_structure=power_structure,
            communication_flow={},  # Would need more analysis
            tension_points=tension_points,
            collaboration_strengths=[],  # Would need more analysis
            group_mood=self._assess_group_mood(text_lower),
            effectiveness_score=effectiveness_score,
            recommended_facilitation=self._suggest_facilitation(dynamic_type, tension_points, effectiveness_score)
        )

    def _extract_relationship_context(self, text: str, person_a: str, person_b: str) -> str:
        """Extract context about relationship between two people"""
        # Find sentences mentioning both people
        sentences = re.split(r'[.!?]', text)
        relevant_sentences = []

        for sentence in sentences:
            if person_a.lower() in sentence.lower() and person_b.lower() in sentence.lower():
                relevant_sentences.append(sentence.strip())

        return "; ".join(relevant_sentences)

    def _is_group_context(self, text: str) -> bool:
        """Check if text describes a group context"""
        group_indicators = [
            "team", "group", "meeting", "everyone", "all of us",
            "together", "collectively", "as a group"
        ]
        text_lower = text.lower()
        return any(indicator in text_lower for indicator in group_indicators)

    def _assess_group_mood(self, text_lower: str) -> str:
        """Assess overall group mood from text"""
        positive_words = ["excited", "motivated", "productive", "happy", "successful"]
        negative_words = ["frustrated", "tired", "stressed", "confused", "overwhelmed"]
        neutral_words = ["focused", "working", "discussing", "considering"]

        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        neutral_count = sum(1 for word in neutral_words if word in text_lower)

        if positive_count > negative_count and positive_count > neutral_count:
            return "positive"
        elif negative_count > positive_count:
            return "negative"
        else:
            return "neutral"

    def _suggest_facilitation(self, dynamic_type: GroupDynamicType, tension_points: List[Tuple[str, str]], effectiveness: float) -> str:
        """Suggest facilitation approach for group"""
        suggestions = []

        if len(tension_points) > 0:
            suggestions.append("Address tension between specific individuals")

        if effectiveness < 0.5:
            if dynamic_type == GroupDynamicType.BRAINSTORMING:
                suggestions.append("Refocus on creative idea generation")
            elif dynamic_type == GroupDynamicType.DECISION_MAKING:
                suggestions.append("Clarify decision criteria and process")
            else:
                suggestions.append("Improve structure and clarity of discussion")

        if not suggestions:
            suggestions.append("Maintain current positive group dynamic")

        return "; ".join(suggestions)

    def _update_network(self, text: str, people: List[str], analysis: Dict[str, Any]):
        """Update social network based on new information"""
        timestamp = datetime.now()

        # Add new people to network
        for person in people:
            self.social_network.people.add(person)

        # Update relationships
        if "relationships" in analysis:
            for pair_key, pair_data in analysis["relationships"].items():
                person_a, person_b = pair_key.split("-")

                # Get or create relationship insight
                rel_key = (person_a, person_b)
                if rel_key not in self.social_network.relationships:
                    insight = RelationshipInsight(
                        person_a=person_a,
                        person_b=person_b,
                        current_status=RelationshipStatus.NEUTRAL,
                        trust_level=0.5,
                        communication_effectiveness=0.5,
                        recent_interactions=[],
                        stress_factors=[],
                        support_opportunities=[],
                        recommended_approach=""
                    )
                    self.social_network.relationships[rel_key] = insight

                # Update with new information
                insight = self.social_network.relationships[rel_key]
                insight.current_status = RelationshipStatus(pair_data["status"])
                insight.recent_interactions.append(f"{timestamp.isoformat()}: {text[:100]}")

                # Keep only recent interactions (last 10)
                insight.recent_interactions = insight.recent_interactions[-10:]

        # Save to database
        self._save_network_updates()

    def _save_network_updates(self):
        """Save network updates to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Save relationships
        for (person_a, person_b), insight in self.social_network.relationships.items():
            cursor.execute("""
                INSERT OR REPLACE INTO relationships
                (person_a, person_b, status, trust_level, communication_effectiveness,
                 last_updated, interaction_history, stress_factors)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                person_a, person_b, insight.current_status.value,
                insight.trust_level, insight.communication_effectiveness,
                datetime.now().isoformat(),
                json.dumps(insight.recent_interactions),
                json.dumps(insight.stress_factors)
            ))

        conn.commit()
        conn.close()

    def _generate_relationship_recommendations(self, relationship_analysis: Dict[str, Any], group_dynamics: Optional[GroupDynamic]) -> List[str]:
        """Generate recommendations based on relationship analysis"""
        recommendations = []

        # Relationship-specific recommendations
        if "relationships" in relationship_analysis:
            for pair_key, pair_data in relationship_analysis["relationships"].items():
                if pair_data["status"] == "tense":
                    recommendations.append(f"Consider addressing tension between {pair_key.replace('-', ' and ')}")
                elif pair_data["status"] == "collaborative":
                    recommendations.append(f"Leverage strong collaboration between {pair_key.replace('-', ' and ')}")

        # Group dynamics recommendations
        if group_dynamics:
            if group_dynamics.effectiveness_score < 0.5:
                recommendations.append(f"Group effectiveness could be improved: {group_dynamics.recommended_facilitation}")

            if len(group_dynamics.tension_points) > 0:
                recommendations.append("Address interpersonal tensions affecting group dynamics")

        # General recommendations
        if relationship_analysis.get("overall_dynamic") == "tension_present":
            recommendations.append("Focus on relationship repair and communication improvement")

        if not recommendations:
            recommendations.append("Maintain current positive relationship dynamics")

        return recommendations

    def get_relationship_insight(self, person_a: str, person_b: str) -> Optional[RelationshipInsight]:
        """Get insight about specific relationship"""
        key = (person_a, person_b)
        reverse_key = (person_b, person_a)

        if key in self.social_network.relationships:
            return self.social_network.relationships[key]
        elif reverse_key in self.social_network.relationships:
            return self.social_network.relationships[reverse_key]

        return None

    def get_network_summary(self) -> Dict[str, Any]:
        """Get summary of current social network"""
        return {
            "total_people": len(self.social_network.people),
            "total_relationships": len(self.social_network.relationships),
            "people": list(self.social_network.people),
            "relationship_statuses": {
                key: insight.current_status.value
                for key, insight in self.social_network.relationships.items()
            }
        }

def create_relationship_dynamics_engine(db_path: str = "relationship_dynamics.db") -> RelationshipDynamicsEngine:
    """Factory function"""
    return RelationshipDynamicsEngine(db_path)

if __name__ == "__main__":
    # Demo and testing
    print("🔗 Relationship Dynamics Engine")
    print("=" * 60)

    # Create engine
    engine = create_relationship_dynamics_engine("test_relationships.db")

    # Test scenarios
    test_scenarios = [
        "Josh and Reneille had a disagreement in the meeting about the project timeline",
        "The team worked really well together on the new feature - everyone was collaborating great",
        "I'm worried about Josh - he seems stressed and not communicating much with the team",
        "Reneille and I brainstormed some great solutions, but Josh wasn't participating much",
        "There's tension between Josh and Reneille that's affecting the whole team dynamic"
    ]

    print("\n🔬 Relationship Dynamics Analysis:")
    for i, scenario in enumerate(test_scenarios, 1):
        print(f"\n{i}. SCENARIO: {scenario}")
        print("-" * 50)

        analysis = engine.analyze_relationship_dynamics(scenario)

        print(f"People involved: {', '.join(analysis['people_involved'])}")

        if analysis['relationship_insights'].get('relationships'):
            print("Relationship insights:")
            for pair, data in analysis['relationship_insights']['relationships'].items():
                print(f"  {pair}: {data['status']} (tension: {data['tension_indicators']}, collaboration: {data['collaboration_indicators']})")

        if analysis['group_dynamics']:
            gd = analysis['group_dynamics']
            print(f"Group dynamic: {gd.dynamic_type.value}")
            print(f"Group mood: {gd.group_mood}")
            print(f"Effectiveness: {gd.effectiveness_score:.2f}")

        print("Recommendations:")
        for rec in analysis['recommendations']:
            print(f"  • {rec}")

    # Show network summary
    print(f"\n📊 Network Summary: {engine.get_network_summary()}")

    # Clean up
    import os
    os.remove("test_relationships.db")
    print("\n✅ Relationship Dynamics Engine test completed!")