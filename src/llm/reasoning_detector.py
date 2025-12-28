"""
Intelligent Reasoning Mode Detector
Automatically determines when to enable reasoning traces based on query complexity
"""

import re
from typing import List


class ReasoningDetector:
    """Detects when queries need deep reasoning vs fast responses"""
    
    # Queries that benefit from showing reasoning
    REASONING_TRIGGERS = [
        # Math & calculations
        r'\b(calculate|compute|solve|equation|formula)\b',
        r'\b(multiply|divide|subtract|add|sum)\b.*\d+',
        r'\d+\s*[\+\-\*\/×÷]\s*\d+',
        
        # Complex analysis
        r'\b(analyze|compare|contrast|evaluate|assess)\b',
        r'\b(pros and cons|advantages.*disadvantages)\b',
        r'\bwhy (is|are|does|do|did|would|should)\b',
        r'\bhow (does|do|can|would|should).*work\b',
        
        # Multi-step reasoning
        r'\b(step by step|explain|breakdown|walk me through)\b',
        r'\b(if.*then|assuming|given that)\b',
        r'\b(optimize|improve|better way)\b',
        
        # Logic problems
        r'\b(logic|reasoning|deduce|infer|conclude)\b',
        r'\b(proof|prove|demonstrate)\b',
        
        # Code & debugging
        r'\b(debug|fix|error|bug|issue)\b.*code',
        r'\b(refactor|optimize).*code\b',
        
        # Planning & strategy
        r'\b(plan|strategy|approach|method)\b.*complex',
        r'\b(design|architect|structure)\b',
    ]
    
    # Queries that should be FAST (no reasoning shown)
    FAST_RESPONSE_TRIGGERS = [
        # Simple greetings
        r'^\s*(hi|hey|hello|yo|sup|what\'?s up)\b',
        
        # Simple questions about Penny
        r'\b(who are you|what are you|tell me about yourself)\b',
        r'\b(what can you do|your (name|capabilities))\b',
        
        # Simple factual lookups
        r'^\s*what is\s+\w+\s*\??\s*$',
        r'^\s*who is\s+\w+\s*\??\s*$',
        
        # Quick commands
        r'^\s*(thanks|thank you|ok|okay|cool|nice|good)\b',
    ]
    
    # Minimum query length for reasoning (very short = probably simple)
    MIN_LENGTH_FOR_REASONING = 15
    
    # Keywords that suggest complexity
    COMPLEXITY_INDICATORS = [
        'multiple', 'several', 'various', 'different',
        'complex', 'complicated', 'detailed', 'comprehensive',
        'thorough', 'in-depth', 'advanced'
    ]
    
    @classmethod
    def should_use_reasoning(cls, query: str) -> bool:
        """
        Determine if a query needs reasoning mode.
        
        Args:
            query: User's query text
            
        Returns:
            True if reasoning mode should be enabled, False otherwise
        """
        query_lower = query.lower().strip()
        
        # Very short queries = simple = no reasoning
        if len(query_lower) < cls.MIN_LENGTH_FOR_REASONING:
            return False
        
        # Check for fast response triggers (override)
        for pattern in cls.FAST_RESPONSE_TRIGGERS:
            if re.search(pattern, query_lower):
                return False
        
        # Check for reasoning triggers
        for pattern in cls.REASONING_TRIGGERS:
            if re.search(pattern, query_lower):
                return True
        
        # Check for complexity indicators
        complexity_count = sum(
            1 for indicator in cls.COMPLEXITY_INDICATORS
            if indicator in query_lower
        )
        
        # Multiple complexity indicators = needs reasoning
        if complexity_count >= 2:
            return True
        
        # Check for question marks and length (complex question)
        if '?' in query and len(query_lower) > 50:
            # Long question might need reasoning
            return True
        
        # Default: no reasoning (faster)
        return False
    
    @classmethod
    def get_reasoning_confidence(cls, query: str) -> float:
        """
        Get confidence score (0-1) for whether reasoning is needed.
        
        Returns:
            0.0 = definitely no reasoning
            1.0 = definitely needs reasoning
        """
        score = 0.0
        query_lower = query.lower().strip()
        
        # Fast response check
        for pattern in cls.FAST_RESPONSE_TRIGGERS:
            if re.search(pattern, query_lower):
                return 0.0
        
        # Reasoning trigger check
        for pattern in cls.REASONING_TRIGGERS:
            if re.search(pattern, query_lower):
                score += 0.3
        
        # Complexity indicators
        complexity_count = sum(
            1 for indicator in cls.COMPLEXITY_INDICATORS
            if indicator in query_lower
        )
        score += complexity_count * 0.15
        
        # Length factor (longer = more likely complex)
        if len(query_lower) > 100:
            score += 0.2
        elif len(query_lower) > 50:
            score += 0.1
        
        return min(score, 1.0)


# Convenience function
def should_use_reasoning(query: str) -> bool:
    """Quick check if query needs reasoning mode"""
    return ReasoningDetector.should_use_reasoning(query)
