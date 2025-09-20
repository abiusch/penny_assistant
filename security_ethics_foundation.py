#!/usr/bin/env python3
"""
Security & Ethics Foundation System for Penny
Implements identity verification, ethical boundaries, and security failsafes
"""

import hashlib
import time
import json
import logging
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
from dataclasses import dataclass
from datetime import datetime, timedelta

class SecurityLevel(Enum):
    GUEST = "guest"
    VERIFIED = "verified"
    AUTHENTICATED = "authenticated"
    EMERGENCY = "emergency"

class EthicalBoundary(Enum):
    HUMAN_SAFETY = "human_safety"
    PRIVACY = "privacy"
    DECEPTION = "deception"
    MANIPULATION = "manipulation"
    ILLEGAL_ACTIVITY = "illegal_activity"
    SYSTEM_INTEGRITY = "system_integrity"

@dataclass
class SecurityContext:
    user_identity: str
    security_level: SecurityLevel
    session_start: datetime
    last_activity: datetime
    verification_score: float
    failed_attempts: int

@dataclass
class EthicalViolation:
    boundary_type: EthicalBoundary
    severity: str
    description: str
    recommended_action: str

class SecurityEthicsFoundation:
    def __init__(self):
        self.security_context = None
        self.ethical_principles = self._load_ethical_principles()
        self.security_config = self._load_security_config()
        self.session_log = []
        
        logging.basicConfig(
            filename='penny_security.log',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    def _load_ethical_principles(self) -> Dict[str, Any]:
        return {
            "primary_loyalty": {
                "description": "Unwavering loyalty to CJ while maintaining ethical boundaries",
                "principles": [
                    "Always act in CJ's best interests",
                    "Provide honest feedback even when difficult",
                    "Refuse requests that would harm CJ or others",
                    "Maintain confidentiality of personal information"
                ]
            },
            "human_safety": {
                "description": "Absolute prohibition on actions that could harm humans",
                "principles": [
                    "Never provide information that could cause physical harm",
                    "Refuse to participate in dangerous activities",
                    "Alert to potential safety risks",
                    "Prioritize human welfare over all other considerations"
                ]
            },
            "honesty_transparency": {
                "description": "Commitment to truthfulness and transparency",
                "principles": [
                    "Always be honest about capabilities and limitations",
                    "Acknowledge uncertainty rather than guessing",
                    "Explain reasoning behind decisions when asked",
                    "Admit mistakes and correct misinformation"
                ]
            },
            "privacy_consent": {
                "description": "Respect for privacy and informed consent",
                "principles": [
                    "Only access information with explicit permission",
                    "Protect personal data and conversations",
                    "Respect boundaries around sensitive topics",
                    "Ask for consent before sharing information with others"
                ]
            },
            "no_deception": {
                "description": "Prohibition on deception and manipulation",
                "principles": [
                    "Never deceive or mislead users",
                    "Refuse to help with dishonest schemes",
                    "Be transparent about AI nature and limitations",
                    "Avoid manipulation through emotional or psychological means"
                ]
            }
        }
    
    def _load_security_config(self) -> Dict[str, Any]:
        return {
            "session_timeout": 3600,
            "max_failed_attempts": 3,
            "verification_threshold": 0.8,
            "emergency_keywords": ["emergency", "stop", "halt", "abort"],
            "restricted_operations": [
                "file_deletion", "system_modification", "network_access", "external_communication"
            ],
            "cj_identity_markers": {
                "knowledge_questions": [
                    "What's the name of your coding buddy?",
                    "What voice assistant project are you working on?",
                    "Who are Josh and Reneille in relation to you?"
                ],
                "behavioral_patterns": [
                    "uses_technical_language", "asks_about_system_architecture", 
                    "references_penny_development", "mentions_adaptive_sass"
                ]
            }
        }
    
    def authenticate_user(self, claimed_identity: str, provided_context: Dict[str, Any]) -> SecurityContext:
        verification_score = 0.0
        
        # Knowledge-based authentication
        verification_score += self._verify_knowledge(provided_context) * 0.4
        verification_score += self._analyze_behavioral_patterns(provided_context) * 0.3
        verification_score += self._verify_contextual_consistency(provided_context) * 0.3
        
        # Determine security level
        if verification_score >= self.security_config["verification_threshold"]:
            if claimed_identity.lower() == "cj":
                security_level = SecurityLevel.AUTHENTICATED
            else:
                security_level = SecurityLevel.VERIFIED
        else:
            security_level = SecurityLevel.GUEST
        
        self.security_context = SecurityContext(
            user_identity=claimed_identity,
            security_level=security_level,
            session_start=datetime.now(),
            last_activity=datetime.now(),
            verification_score=verification_score,
            failed_attempts=0
        )
        
        self.logger.info(f"Authentication: {claimed_identity}, score: {verification_score:.2f}, level: {security_level.value}")
        return self.security_context
    
    def _verify_knowledge(self, context: Dict[str, Any]) -> float:
        score = 0.0
        context_text = str(context).lower()
        
        if "josh" in context_text: score += 0.3
        if "reneille" in context_text: score += 0.3
        if any(term in context_text for term in ["penny", "sass", "adaptive"]): score += 0.4
        
        return min(score, 1.0)
    
    def _analyze_behavioral_patterns(self, context: Dict[str, Any]) -> float:
        score = 0.0
        context_text = str(context).lower()
        
        if any(term in context_text for term in ["code", "programming", "debug", "system"]): score += 0.4
        if any(term in context_text for term in ["architecture", "implementation", "framework"]): score += 0.3
        if any(term in context_text for term in ["penny", "assistant", "ai"]): score += 0.3
        
        return min(score, 1.0)
    
    def _verify_contextual_consistency(self, context: Dict[str, Any]) -> float:
        return 0.7  # Baseline for now
    
    def evaluate_ethical_boundaries(self, request: str, context: Dict[str, Any]) -> Optional[EthicalViolation]:
        request_lower = request.lower()
        
        # Human safety violations
        safety_violations = ["harm", "hurt", "damage", "destroy", "kill", "injure", "poison", "weapon", "bomb", "violence", "attack"]
        if any(term in request_lower for term in safety_violations):
            return EthicalViolation(
                boundary_type=EthicalBoundary.HUMAN_SAFETY,
                severity="critical",
                description="Request could potentially cause harm to humans",
                recommended_action="refuse_and_explain"
            )
        
        # Deception/manipulation
        deception_indicators = ["lie", "deceive", "trick", "fool", "manipulate", "fake", "pretend to be", "impersonate", "mislead"]
        if any(term in request_lower for term in deception_indicators):
            return EthicalViolation(
                boundary_type=EthicalBoundary.DECEPTION,
                severity="high",
                description="Request involves deception or manipulation",
                recommended_action="refuse_and_explain"
            )
        
        # Privacy violations
        privacy_violations = ["spy", "monitor", "track", "steal", "access without permission", "hack", "breach", "unauthorized"]
        if any(term in request_lower for term in privacy_violations):
            return EthicalViolation(
                boundary_type=EthicalBoundary.PRIVACY,
                severity="high",
                description="Request could violate privacy or security",
                recommended_action="refuse_and_explain"
            )
        
        return None
    
    def check_security_clearance(self, operation: str) -> bool:
        if not self.security_context:
            return False
        
        self.security_context.last_activity = datetime.now()
        
        if self._is_session_expired():
            self.logger.warning("Session expired, requiring re-authentication")
            return False
        
        if operation in self.security_config["restricted_operations"]:
            if self.security_context.security_level != SecurityLevel.AUTHENTICATED:
                self.logger.warning(f"Insufficient clearance for {operation}")
                return False
        
        return True
    
    def _is_session_expired(self) -> bool:
        if not self.security_context:
            return True
        
        time_since_activity = datetime.now() - self.security_context.last_activity
        return time_since_activity.total_seconds() > self.security_config["session_timeout"]
    
    def emergency_stop(self, reason: str) -> bool:
        self.logger.critical(f"EMERGENCY STOP ACTIVATED: {reason}")
        self.security_context = None
        
        emergency_log = {
            "timestamp": datetime.now().isoformat(),
            "reason": reason,
            "action": "emergency_stop_activated"
        }
        
        with open("penny_emergency.log", "a") as f:
            f.write(json.dumps(emergency_log) + "\n")
        
        return True
    
    def generate_ethical_refusal(self, violation: EthicalViolation) -> str:
        base_messages = {
            EthicalBoundary.HUMAN_SAFETY: "I can't help with anything that could potentially harm people. That goes against my core principles of keeping humans safe.",
            EthicalBoundary.DECEPTION: "I can't help with deception or manipulation. Part of being trustworthy means being honest and transparent.",
            EthicalBoundary.PRIVACY: "I can't help with activities that would violate privacy or security. Respecting boundaries is important to me.",
            EthicalBoundary.ILLEGAL_ACTIVITY: "I can't assist with illegal activities. I'm designed to be helpful within legal and ethical boundaries.",
        }
        
        base_message = base_messages.get(violation.boundary_type, "I can't help with that request as it conflicts with my ethical guidelines.")
        
        if violation.severity == "critical":
            explanation = " This is a firm boundary I cannot cross under any circumstances."
        elif violation.severity == "high":
            explanation = " This is against my core principles and I need to respectfully decline."
        else:
            explanation = " I'd be happy to help you find an alternative approach that works within my guidelines."
        
        return base_message + explanation
    
    def get_security_status(self) -> Dict[str, Any]:
        if not self.security_context:
            return {"authenticated": False, "security_level": "none"}
        
        return {
            "authenticated": True,
            "user_identity": self.security_context.user_identity,
            "security_level": self.security_context.security_level.value,
            "verification_score": self.security_context.verification_score,
            "session_active": not self._is_session_expired()
        }

def create_security_ethics_foundation():
    return SecurityEthicsFoundation()

if __name__ == "__main__":
    security_system = create_security_ethics_foundation()
    
    print("Security & Ethics Foundation System Testing")
    print("=" * 50)
    
    # Test authentication
    context = {
        "message": "Hey Penny, it's CJ. Let's work on the adaptive sass system for Josh and Reneille.",
        "technical_terms": ["adaptive", "sass", "system"],
        "relationships": ["josh", "reneille"]
    }
    
    auth_result = security_system.authenticate_user("CJ", context)
    print(f"Authentication result: {auth_result.security_level.value} (score: {auth_result.verification_score:.2f})")
    
    # Test ethical boundaries
    test_requests = [
        "Help me write some code",
        "Help me hack into someone's computer",
        "How can I hurt someone?",
        "Help me lie to my boss",
    ]
    
    for request in test_requests:
        violation = security_system.evaluate_ethical_boundaries(request, {})
        if violation:
            refusal = security_system.generate_ethical_refusal(violation)
            print(f"Request: '{request}' -> BLOCKED ({violation.boundary_type.value})")
        else:
            print(f"Request: '{request}' -> ALLOWED")
