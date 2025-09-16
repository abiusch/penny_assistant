#!/usr/bin/env python3
"""
Test coffee cleanup in sass controller
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def test_coffee_cleanup():
    print("☕ Testing Coffee/Caffeine Cleanup")
    print("="*50)
    
    try:
        from sass_controller import create_sass_controller, SassLevel
        
        sass = create_sass_controller()
        
        # Test responses with coffee/caffeine content
        test_responses = [
            "*buzzing with caffeine* OH BOY, I'M READY TO LEARN ALL ABOUT YOU, HUMAN!",
            "As a caffeinated AI companion, I'm feeling extra sassy and ready!",
            "Let's make this happen! Oh, and don't worry if you're not caffeinated enough to keep up with my rapid-fire questions – I've got your back (and a whole lot of coffee)!",
            "OH BOY, IT'S YOUR BOI CJ! *buzzing with caffeine*",
            "I'm ENERGIZED about this OH BOY!!!"
        ]
        
        for i, response in enumerate(test_responses, 1):
            print(f"\n{i}. BEFORE: {response}")
            
            # Test with different sass levels
            for level in [SassLevel.MINIMAL, SassLevel.MEDIUM, SassLevel.MAXIMUM]:
                sass.set_sass_level(level)
                cleaned = sass.apply_sass_to_response(response)
                print(f"   {level.value:8}: {cleaned}")
        
        print("\n✅ Coffee cleanup system tested!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_coffee_cleanup()
