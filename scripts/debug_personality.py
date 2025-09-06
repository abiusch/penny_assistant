#!/usr/bin/env python3
"""
Debug personality detection to see what's triggering
"""

def debug_personality_detection(text: str):
    """Debug version of personality detection with detailed logging"""
    text_lower = text.lower()
    print(f"Input text: '{text}'")
    print(f"Lowercase: '{text_lower}'")
    print()
    
    # Check sassy indicators FIRST
    sassy_patterns = [
        'obviously', 'of course', 'sure thing', 'yeah right', 
        'really?', 'seriously?', 'great job', 'nice work',
        'brilliant', 'genius', 'perfect', 'wonderful',
        'clearly', 'apparently', 'supposedly'
    ]
    
    print("🎭 Checking sassy patterns:")
    sassy_matches = []
    for pattern in sassy_patterns:
        if pattern in text_lower:
            sassy_matches.append(pattern)
            print(f"   ✅ Found: '{pattern}'")
    
    if sassy_matches:
        print(f"   🎯 RESULT: sassy (matched: {sassy_matches})")
        return 'sassy'
    else:
        print("   ❌ No sassy patterns found")
    
    # Check support patterns
    support_patterns = [
        'stressed', 'worried', 'anxious', 'help me',
        'struggling', 'difficult', 'hard time', 'overwhelmed',
        'support', 'advice', 'guidance'
    ]
    
    print("\n🤗 Checking supportive patterns:")
    support_matches = []
    for pattern in support_patterns:
        if pattern in text_lower:
            support_matches.append(pattern)
            print(f"   ✅ Found: '{pattern}'")
    
    if support_matches:
        print(f"   🎯 RESULT: supportive (matched: {support_matches})")
        return 'supportive'
    else:
        print("   ❌ No supportive patterns found")
    
    # Check tech patterns
    tech_patterns = [
        'algorithm', 'neural', 'quantum', 'machine learning',
        'ai', 'artificial intelligence', 'deep learning',
        'programming', 'code', 'software', 'technology',
        'computer', 'data science', 'blockchain'
    ]
    
    print("\n🤓 Checking tech patterns:")
    tech_matches = []
    for pattern in tech_patterns:
        if pattern in text_lower:
            tech_matches.append(pattern)
            print(f"   ✅ Found: '{pattern}'")
    
    if tech_matches:
        print(f"   🎯 RESULT: tech_enthusiast (matched: {tech_matches})")
        return 'tech_enthusiast'
    else:
        print("   ❌ No tech patterns found")
    
    # Check playful patterns
    playful_patterns = [
        'haha', 'funny', 'silly', 'ridiculous', 'crazy',
        'weird', 'strange', 'amusing', 'hilarious'
    ]
    
    print("\n😄 Checking playful patterns:")
    playful_matches = []
    for pattern in playful_patterns:
        if pattern in text_lower:
            playful_matches.append(pattern)
            print(f"   ✅ Found: '{pattern}'")
    
    if playful_matches:
        print(f"   🎯 RESULT: playful (matched: {playful_matches})")
        return 'playful'
    else:
        print("   ❌ No playful patterns found")
    
    print("\n🤷 RESULT: default (no patterns matched)")
    return 'default'

if __name__ == "__main__":
    test_phrases = [
        "Obviously, quantum computing is just hype, right?",
        "Tell me about quantum algorithms",
        "I'm stressed about programming",
        "That's hilarious!"
    ]
    
    for phrase in test_phrases:
        print("=" * 60)
        result = debug_personality_detection(phrase)
        print(f"Final result: {result}")
        print()
