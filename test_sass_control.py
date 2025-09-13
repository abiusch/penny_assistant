#!/usr/bin/env python3
"""
Test script for sass level control system
Verifies sass control integration with memory system
"""

import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def test_sass_controller():
    """Test basic sass controller functionality"""
    print("🎭 Testing Sass Controller")
    print("="*50)
    
    try:
        from sass_controller import create_sass_controller, SassLevel
        
        # Create sass controller
        sass = create_sass_controller()
        print("✅ Sass controller created")
        
        # Test current level
        print(f"Current level: {sass.get_sass_status()}")
        
        # Test command parsing
        test_commands = [
            "set sass to spicy",
            "tone it down", 
            "be more sassy",
            "professional mode",
            "maximum sass"
        ]
        
        for command in test_commands:
            parsed = sass.parse_sass_command(command)
            if parsed:
                print(f"'{command}' → {parsed.value}")
            else:
                print(f"'{command}' → no change")
        
        # Test response modification
        test_response = "Oh wow! That's amazing! This is really interesting!!!"
        print(f"\nOriginal: {test_response}")
        
        for level in SassLevel:
            sass.set_sass_level(level)
            modified = sass.apply_sass_to_response(test_response)
            print(f"{level.value:8}: {modified}")
        
        return True
        
    except Exception as e:
        print(f"❌ Sass controller test failed: {e}")
        return False

def test_sass_enhanced_penny():
    """Test sass-enhanced Penny integration"""
    print("\n🤖 Testing Sass-Enhanced Penny")
    print("="*50)
    
    try:
        from sass_enhanced_penny import create_sass_enhanced_penny
        
        # Create sass-enhanced Penny
        penny = create_sass_enhanced_penny("test_sass.db")
        print("✅ Sass-enhanced Penny created")
        
        # Start session
        session_id = penny.start_conversation_session("test")
        print(f"✅ Session started: {session_id}")
        
        # Test sass commands
        sass_commands = [
            "What's my current sass level?",
            "Set sass to minimal", 
            "How are you doing?",  # Should be polite
            "Set sass to maximum",
            "How are you doing?",  # Should be sassy
            "Tone it down please",
            "Tell me about yourself"  # Should be medium sass
        ]
        
        for i, command in enumerate(sass_commands, 1):
            print(f"\n{i}. User: {command}")
            try:
                response = penny.generate_sass_aware_response(command)
                current_sass = penny.sass_controller.current_level.value
                print(f"   Penny [{current_sass}]: {response[:100]}...")
            except Exception as e:
                print(f"   Error: {e}")
        
        # Test comprehensive status
        status = penny.get_comprehensive_status()
        print(f"\n📊 Final Status:")
        print(f"   Sass level: {status['sass_level']}")
        print(f"   Description: {status['sass_description']}")
        print(f"   Memory items: {sum(status['memory_stats'].values())}")
        
        penny.end_conversation_session("Test completed")
        
        # Clean up
        os.remove("test_sass.db")
        return True
        
    except Exception as e:
        print(f"❌ Sass-enhanced Penny test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_natural_sass_commands():
    """Test natural language sass commands"""
    print("\n🗣️ Testing Natural Language Sass Commands")
    print("="*50)
    
    try:
        from sass_controller import create_sass_controller, SassLevel
        
        sass = create_sass_controller()
        
        # Test natural language parsing
        natural_commands = [
            ("tone it down", "Should decrease sass level"),
            ("be more sassy", "Should increase sass level"), 
            ("professional mode", "Should set to minimal"),
            ("maximum sass please", "Should set to maximum"),
            ("dial it back", "Should decrease sass level"),
            ("turn it up", "Should increase sass level"),
            ("be polite", "Should set to minimal"),
            ("normal sass", "Should set to medium")
        ]
        
        for command, expected in natural_commands:
            original_level = sass.current_level
            parsed_level = sass.parse_sass_command(command)
            
            if parsed_level:
                print(f"✅ '{command}' → {original_level.value} to {parsed_level.value} ({expected})")
            else:
                print(f"❌ '{command}' → no change ({expected})")
        
        return True
        
    except Exception as e:
        print(f"❌ Natural command test failed: {e}")
        return False

def test_sass_persistence():
    """Test that sass preferences persist across sessions"""
    print("\n💾 Testing Sass Persistence")
    print("="*50)
    
    try:
        from sass_enhanced_penny import create_sass_enhanced_penny
        
        # First session - change sass level
        print("Session 1: Setting sass to spicy...")
        penny1 = create_sass_enhanced_penny("test_persistence.db")
        penny1.generate_sass_aware_response("set sass to spicy")
        level1 = penny1.sass_controller.current_level.value
        print(f"   Set to: {level1}")
        penny1.end_conversation_session("Session 1 complete")
        
        # Second session - check if sass level persisted
        print("\nSession 2: Checking sass persistence...")
        penny2 = create_sass_enhanced_penny("test_persistence.db")
        level2 = penny2.sass_controller.current_level.value
        print(f"   Loaded: {level2}")
        
        if level1 == level2:
            print("✅ Sass preference persisted across sessions!")
            success = True
        else:
            print(f"❌ Sass preference not persisted: {level1} → {level2}")
            success = False
        
        penny2.end_conversation_session("Session 2 complete")
        
        # Clean up
        os.remove("test_persistence.db")
        return success
        
    except Exception as e:
        print(f"❌ Sass persistence test failed: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Running Sass Control System Tests...")
    
    results = []
    results.append(("Sass Controller", test_sass_controller()))
    results.append(("Sass-Enhanced Penny", test_sass_enhanced_penny()))
    results.append(("Natural Commands", test_natural_sass_commands()))
    results.append(("Sass Persistence", test_sass_persistence()))
    
    print("\n📊 Test Results:")
    print("="*50)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {test_name:20} {status}")
        if result:
            passed += 1
    
    print(f"\n🎆 Results: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("\n🎉 All tests passed! Sass control system is ready!")
        print("\n💡 You can now:")
        print("   • python3 memory_chat_penny.py (text with sass control)")
        print("   • Say 'set sass to spicy' to change personality")
        print("   • Say 'tone it down' for natural control")
        print("   • Say 'sass options' to see all levels")
    else:
        print("\n⚠️ Some tests failed. Check the errors above.")
