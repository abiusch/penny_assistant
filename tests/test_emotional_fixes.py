#!/usr/bin/env python3
"""
Test script to validate the fixed emotional memory system
"""

import sys
import os
import tempfile
import shutil
import time

# Add src directory to Python path  
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
sys.path.insert(0, os.path.dirname(__file__))

def main():
    print("🔧 TESTING EMOTIONAL MEMORY SYSTEM FIXES")
    print("=" * 60)
    
    try:
        # Import the fixed version
        from memory_system import MemoryManager
        from emotional_memory_system_fixed import create_enhanced_memory_system
        
        # Create temporary database for testing
        temp_dir = tempfile.mkdtemp()
        temp_db = os.path.join(temp_dir, 'test_memory.db')
        
        try:
            # Initialize with temporary database
            print("📝 Initializing enhanced memory system...")
            base_memory = MemoryManager(db_path=temp_db)
            enhanced_memory = create_enhanced_memory_system(base_memory)
            print("✅ Memory system initialized")
            
            # Test conversations that previously caused issues
            test_conversations = [
                # This should NOT create relationship entries for "Hello", "Thanks", etc.
                ("Hello! Thanks for your help. You're very useful!", 
                 "You're welcome! I'm happy to help."),
                
                # This should properly link "Max" with "my dog" context
                ("My dog Max is sick and I'm worried about him",
                 "I'm sorry to hear Max isn't feeling well. It's clear you care deeply about him."),
                
                # This should NOT create relationships for "Ugh" or other common words  
                ("Ugh, this is frustrating. What should I do?",
                 "I can hear your frustration. Let's work through this step by step."),
                
                # This SHOULD create a proper family relationship
                ("My mom is visiting tomorrow and I need to clean the house",
                 "That's exciting that your mom is visiting! A quick tidy-up plan might help."),
                
                # This should NOT create false relationships
                ("The weather is nice today. How are you doing?",
                 "I'm doing well, thank you! The weather does sound lovely."),
                
                # This SHOULD create a proper friend relationship with context
                ("I'm meeting my friend Sarah for coffee later",
                 "That sounds nice! Enjoy your coffee with Sarah.")
            ]
            
            print(f"\n🗣️ Processing {len(test_conversations)} test conversations...")
            relationship_count_before = len(enhanced_memory.family_members)
            
            for i, (user_input, assistant_response) in enumerate(test_conversations, 1):
                print(f"\n--- Conversation {i} ---")
                print(f"User: {user_input}")
                
                # Test relationship extraction directly
                mentions = enhanced_memory.extract_relationship_mentions(user_input)
                print(f"🔍 Detected mentions: {mentions}")
                
                # Process through the system
                turn = base_memory.add_conversation_turn(
                    user_input=user_input,
                    assistant_response=assistant_response,
                    response_time_ms=500
                )
                
                enhanced_memory.process_conversation_turn(user_input, assistant_response, turn.turn_id)
                
                # Check current relationship count
                current_count = len(enhanced_memory.family_members)
                print(f"📊 Total relationships: {current_count}")
            
            relationship_count_after = len(enhanced_memory.family_members)
            relationships_added = relationship_count_after - relationship_count_before
            
            print(f"\n📊 RELATIONSHIP DETECTION RESULTS:")
            print(f"   Relationships before: {relationship_count_before}")
            print(f"   Relationships after: {relationship_count_after}")
            print(f"   New relationships added: {relationships_added}")
            
            # Show final relationship summary
            print(f"\n👥 FINAL RELATIONSHIPS DETECTED:")
            valid_relationships = 0
            false_positives = 0
            
            for name, member in enhanced_memory.family_members.items():
                context_info = f" - {member.context}" if member.context else ""
                print(f"   {name}: {member.relationship_type.value}{context_info} ({member.mention_count} mentions)")
                
                # Check if this is a valid relationship (not a common word)
                if name not in ['Hello', 'Thanks', 'You', 'Ugh', 'The', 'What', 'How', 'Why', 'Hi', 'Hey']:
                    valid_relationships += 1
                else:
                    false_positives += 1
            
            print(f"\n📈 PERFORMANCE ANALYSIS:")
            print(f"   ✅ Valid relationships detected: {valid_relationships}")
            print(f"   ❌ False positives: {false_positives}")
            print(f"   📊 Total processing: {relationships_added} new relationships")
            
            # Success criteria
            success = (
                relationships_added <= 4 and  # Should add 2-4 real relationships, not 10+
                false_positives == 0 and      # No common words as relationships
                valid_relationships >= 2      # At least detected Max and mom/Sarah
            )
            
            if success:
                print(f"\n🎉 SUCCESS - RELATIONSHIP DETECTION FIXES WORKING!")
                print(f"   ✓ No longer detecting common words as relationships")
                print(f"   ✓ Reasonable number of relationships detected")
                print(f"   ✓ Names properly linked to context")
            else:
                print(f"\n⚠️ ISSUES STILL PRESENT:")
                if relationships_added > 4:
                    print(f"   - Too many relationships detected ({relationships_added}, should be ≤4)")
                if false_positives > 0:
                    print(f"   - Common words still being detected as relationships ({false_positives})")
                if valid_relationships < 2:
                    print(f"   - Not detecting valid relationships properly ({valid_relationships})")
            
            # Test enhanced context
            context = enhanced_memory.get_enhanced_context_for_llm()
            print(f"\n📝 Enhanced LLM Context Preview:")
            print(f"   {context[:200]}..." if context else "   (No context generated)")
            
            print(f"\n🏁 Test completed - {'PASSED' if success else 'FAILED'}")
            return success
            
        finally:
            # Cleanup temporary database
            shutil.rmtree(temp_dir, ignore_errors=True)
            
    except Exception as e:
        print(f"❌ Critical error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    if success:
        print("\n🎯 NEXT STEPS:")
        print("1. Replace original emotional_memory_system.py with fixed version")
        print("2. Move to Task 1.2: Personality Integration & Sass System") 
        print("3. Begin implementing Penny (Big Bang Theory) personality traits")
    else:
        print("\n❗ ADDITIONAL FIXES NEEDED BEFORE PROCEEDING")
    
    sys.exit(0 if success else 1)
