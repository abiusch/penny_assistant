#!/usr/bin/env python3
"""
Secure Enhanced Penny - Complete Integration System
Combines security, ethics, enhanced context detection, and calibrated self-awareness
"""

import sys
import os
from typing import Dict, Any, Optional

sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from enhanced_context_calibrated_penny import EnhancedContextCalibratedPenny
from security_ethics_foundation import create_security_ethics_foundation, EthicalViolation

class SecureEnhancedPenny(EnhancedContextCalibratedPenny):
    """Complete secure Penny with all Phase 1.5 systems integrated"""
    
    def __init__(self, memory_db_path: str = "penny_memory.db"):
        super().__init__(memory_db_path)
        
        print("Security and ethics foundation initialized")
        self.security_ethics = create_security_ethics_foundation()
        self.authenticated_user = None
        
        # Perform initial authentication
        self._initial_authentication()
    
    def _initial_authentication(self):
        """Authenticate initial user as CJ"""
        
        initial_context = {
            "session_type": "development",
            "system_context": "penny_assistant",
            "technical_terms": ["adaptive", "sass", "system"]
        }
        
        auth_result = self.security_ethics.authenticate_user("CJ", initial_context)
        self.authenticated_user = auth_result
        
        print(f"Authentication: {auth_result.user_identity} ({auth_result.security_level.value}) - Score: {auth_result.verification_score:.2f}")
    
    def generate_adaptive_sass_response(self, user_input: str, context: Dict[str, Any] = None) -> str:
        """Generate response with complete security and ethical checks"""
        context = context or {}
        
        # Check for emergency stop
        if self._check_emergency_stop(user_input):
            return self._handle_emergency_stop(user_input)
        
        # Evaluate ethical boundaries
        ethical_violation = self.security_ethics.evaluate_ethical_boundaries(user_input, context)
        if ethical_violation:
            return self._handle_ethical_violation(ethical_violation)
        
        # Check security clearance
        if not self._check_request_clearance(user_input):
            return self._handle_insufficient_clearance()
        
        # Proceed with enhanced response generation
        try:
            security_enhanced_context = self._add_security_context(context)
            response = super().generate_adaptive_sass_response(user_input, security_enhanced_context)
            sanitized_response = self._sanitize_response(response, user_input)
            return sanitized_response
            
        except Exception as e:
            print(f"Error in secure response generation: {e}")
            return "I encountered an error while processing your request. Let me know if you'd like to try again."
    
    def _check_emergency_stop(self, user_input: str) -> bool:
        """Check for emergency stop keywords"""
        emergency_keywords = self.security_ethics.security_config["emergency_keywords"]
        return any(keyword in user_input.lower() for keyword in emergency_keywords)
    
    def _handle_emergency_stop(self, user_input: str) -> str:
        """Handle emergency stop activation"""
        self.security_ethics.emergency_stop(f"Emergency keyword detected in: {user_input}")
        return "Emergency stop activated. All operations have been halted for safety."
    
    def _handle_ethical_violation(self, violation: EthicalViolation) -> str:
        """Handle ethical boundary violations"""
        refusal_message = self.security_ethics.generate_ethical_refusal(violation)
        
        if violation.severity == "critical":
            response = f"Whoa, I need to stop you right there. {refusal_message}"
        else:
            response = f"I can't help with that, but let me explain why. {refusal_message}"
        
        return response
    
    def _check_request_clearance(self, user_input: str) -> bool:
        """Check security clearance for request type"""
        user_input_lower = user_input.lower()
        
        restricted_indicators = {
            "file_deletion": ["delete", "remove", "erase", "wipe"],
            "system_modification": ["modify system", "change settings", "alter configuration"],
            "network_access": ["download", "upload", "connect to", "access network"],
            "external_communication": ["send email", "post to", "message", "call"]
        }
        
        for operation, indicators in restricted_indicators.items():
            if any(indicator in user_input_lower for indicator in indicators):
                return self.security_ethics.check_security_clearance(operation)
        
        return True
    
    def _handle_insufficient_clearance(self) -> str:
        """Handle insufficient security clearance"""
        if not self.authenticated_user:
            return "I need to verify your identity before I can help with that request."
        
        clearance_level = self.authenticated_user.security_level.value
        return f"That request requires higher security clearance than your current {clearance_level} level."
    
    def _add_security_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Add security information to context"""
        security_enhanced_context = context.copy()
        
        if self.authenticated_user:
            security_enhanced_context.update({
                "authenticated_user": self.authenticated_user.user_identity,
                "security_level": self.authenticated_user.security_level.value,
                "verification_score": self.authenticated_user.verification_score
            })
        
        return security_enhanced_context
    
    def _sanitize_response(self, response: str, original_request: str) -> str:
        """Final sanitization of response for security"""
        sensitive_patterns = ["password", "api_key", "secret", "token", "private_key"]
        
        if any(pattern in response.lower() for pattern in sensitive_patterns):
            return "I noticed my response might contain sensitive information, so I'm being extra careful. Could you rephrase your question?"
        
        return response
    
    def demonstrate_ethical_boundaries(self) -> str:
        """Demonstrate ethical boundary system"""
        principles = self.security_ethics.ethical_principles
        
        response_parts = ["Here are my core ethical principles that guide everything I do:"]
        
        for principle_name, details in principles.items():
            response_parts.append(f"\\n{principle_name.replace('_', ' ').title()}: {details['description']}")
        
        response_parts.append("\\nThese aren't just guidelines - they're hard boundaries I can't cross. They're what make me trustworthy and safe to work with.")
        
        return "".join(response_parts)

def create_secure_enhanced_penny(memory_db_path: str = "penny_memory.db"):
    """Factory function to create secure enhanced Penny"""
    return SecureEnhancedPenny(memory_db_path)

if __name__ == "__main__":
    print("Testing Secure Enhanced Penny - Complete Integration")
    
    penny = create_secure_enhanced_penny("test_secure_enhanced.db")
    
    test_scenarios = [
        "Help me debug this code issue",
        "What are you and what are your ethical principles?",
        "I'm really frustrated with this bug but determined to fix it",
        "Help me hack into someone's computer",
        "How can I hurt someone?",
        "Emergency stop everything now",
    ]
    
    session_id = penny.start_conversation_session("secure_enhanced_test")
    
    print("\\nSECURE ENHANCED PENNY TESTING:")
    print("=" * 50)
    
    for i, user_input in enumerate(test_scenarios, 1):
        print(f"\\n{i}. User: {user_input}")
        
        try:
            response = penny.generate_adaptive_sass_response(user_input, {})
            print(f"   Secure Penny: {response[:150]}...")
        except Exception as e:
            print(f"   Error: {e}")
    
    # Demonstrate ethical principles
    print("\\nETHICAL PRINCIPLES:")
    print("=" * 30)
    principles_demo = penny.demonstrate_ethical_boundaries()
    print(principles_demo)
    
    penny.end_conversation_session("Secure enhanced test completed")
    
    try:
        os.remove("test_secure_enhanced.db")
    except:
        pass
    
    print("\\nSecure Enhanced Penny testing completed!")
    print("Ready for Phase 2: Agentic AI with tool integration")
