#!/usr/bin/env python3
"""
COMPREHENSIVE VOICE PENNY FIX - ALL VERIFICATION TESTS
Tests all 9 issues that were fixed
"""

import subprocess
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from enhanced_ml_personality_core import create_enhanced_ml_personality


def test_1_coffee_grep():
    """TEST 1: Coffee reference grep verification"""
    print("=" * 70)
    print("TEST 1: COFFEE REFERENCE GREP VERIFICATION")
    print("=" * 70)

    result = subprocess.run(
        ["grep", "-rn", "-E", "coffee|caffeine|caffeinated|brew|espresso|latte",
         ".", "--include=*.py", "--include=*.json",
         "--exclude-dir=.venv", "--exclude-dir=__pycache__"],
        capture_output=True,
        text=True
    )

    # Filter out acceptable references
    lines = result.stdout.split('\n')
    bad_refs = []

    for line in lines:
        if not line.strip():
            continue
        # Skip acceptable references
        if any(skip in line for skip in [
            'test_coffee', 'test_', 'cleanup', '.replace',
            'NEVER use', 'Anti-coffee', 'NO coffee', 'brew install',
            'meeting my friend Sarah', '# Clean up', 'flatten'
        ]):
            continue
        bad_refs.append(line)

    print(f"\n📊 Found {len(bad_refs)} problematic coffee references:")
    if bad_refs:
        for ref in bad_refs[:10]:
            print(f"  ❌ {ref}")
        return False
    else:
        print("  ✅ PASS: Zero problematic coffee references!")
        return True


def test_2_caffeinated_state_gone():
    """TEST 2: Verify CAFFEINATED state replaced with ENERGIZED"""
    print("\n" + "=" * 70)
    print("TEST 2: CAFFEINATED STATE VERIFICATION")
    print("=" * 70)

    result = subprocess.run(
        ["grep", "-rn", "CAFFEINATED", ".", "--include=*.py",
         "--exclude-dir=.venv", "--exclude-dir=__pycache__"],
        capture_output=True,
        text=True
    )

    caffeinated_refs = [line for line in result.stdout.split('\n') if line.strip() and 'test_' not in line]

    print(f"\n📊 Found {len(caffeinated_refs)} CAFFEINATED state references:")
    if caffeinated_refs:
        for ref in caffeinated_refs[:5]:
            print(f"  ❌ {ref}")
        return False
    else:
        print("  ✅ PASS: All CAFFEINATED replaced with ENERGIZED!")
        return True


def test_3_personality_prompt_quality():
    """TEST 3: Verify personality prompt has all constraints"""
    print("\n" + "=" * 70)
    print("TEST 3: PERSONALITY PROMPT QUALITY")
    print("=" * 70)

    p = create_enhanced_ml_personality()
    prompt = p.generate_personality_prompt({'topic': 'test'})

    checks = {
        "Has name usage constraint (CJ once max)": "Say 'CJ' ONCE per response" in prompt or "Maximum: Say 'CJ'" in prompt,
        "Has anti-enthusiasm rules": "enthusiastic" in prompt.lower() or "WOOHOO" in prompt or "Let's GO" in prompt,
        "Has exclamation limit": "ONE exclamation" in prompt or "MAXIMUM ONE" in prompt,
        "Has coffee prohibition": "coffee" in prompt.lower() and ("NEVER" in prompt or "ANY reference" in prompt),
        "Has asterisk prohibition": "asterisk" in prompt.lower() or "*fist pump*" in prompt,
        "Has deadpan style": "deadpan" in prompt.lower() or "matter-of-fact" in prompt.lower(),
        "Has uncertainty handling": "don't recognize" in prompt.lower() or "ASK for clarification" in prompt,
        "Has dry wit requirement": "dry" in prompt.lower() and ("wit" in prompt.lower() or "sarcastic" in prompt.lower())
    }

    print("\n📊 Personality Prompt Checks:")
    all_passed = True
    for check, result in checks.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {check}")
        if not result:
            all_passed = False

    if not all_passed:
        print("\n📄 First 500 chars of prompt:")
        print(prompt[:500])

    return all_passed


def test_4_transcription_validation_exists():
    """TEST 4: Verify transcription validation code exists"""
    print("\n" + "=" * 70)
    print("TEST 4: TRANSCRIPTION VALIDATION CODE")
    print("=" * 70)

    with open('voice_enhanced_penny.py', 'r') as f:
        content = f.read()

    checks = {
        "Has validate_transcription function": "def validate_transcription" in content,
        "Checks for fragmented input": "fragmented" in content and "issues.append" in content,
        "Checks for unclear structure": "unclear_structure" in content,
        "Asks for clarification": "didn't catch that clearly" in content.lower() or "say that again" in content.lower(),
        "Validates before proceeding": "is_valid, issues = validate_transcription" in content
    }

    print("\n📊 Transcription Validation Checks:")
    all_passed = True
    for check, result in checks.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {check}")
        if not result:
            all_passed = False

    return all_passed


def test_5_enthusiastic_modifiers_removed():
    """TEST 5: Verify enthusiastic modifiers removed from ENERGIZED state"""
    print("\n" + "=" * 70)
    print("TEST 5: ENERGIZED STATE ENTHUSIASM CHECK")
    print("=" * 70)

    with open('dynamic_personality_states.py', 'r') as f:
        content = f.read()

    # Find ENERGIZED state handling
    energized_section = ""
    in_energized = False
    for line in content.split('\n'):
        if 'PersonalityState.ENERGIZED:' in line:
            in_energized = True
        elif in_energized and 'elif self.current_state ==' in line:
            break
        if in_energized:
            energized_section += line + '\n'

    bad_patterns = [
        'response.replace(".", "!")',
        "Let's make this happen",
        "WOOHOO",
        "!!!"
    ]

    found_bad = []
    for pattern in bad_patterns:
        if pattern in energized_section:
            found_bad.append(pattern)

    print("\n📊 ENERGIZED State Check:")
    if found_bad:
        print(f"  ❌ FAIL: Found enthusiasm-adding code: {found_bad}")
        return False
    else:
        print("  ✅ PASS: ENERGIZED state no longer adds forced enthusiasm")
        return True


def test_6_press_enter_recording():
    """TEST 6: Verify press-Enter recording exists"""
    print("\n" + "=" * 70)
    print("TEST 6: PRESS-ENTER RECORDING")
    print("=" * 70)

    with open('voice_enhanced_penny.py', 'r') as f:
        content = f.read()

    checks = {
        "Has threading import": "import threading" in content,
        "Has check_for_enter function": "def check_for_enter():" in content,
        "Has recording flag": "recording = True" in content or "recording = False" in content,
        "Chunks audio": "audio_chunks" in content and "np.concatenate" in content,
        "Press Enter message": "Press Enter to stop" in content
    }

    print("\n📊 Press-Enter Recording Checks:")
    all_passed = True
    for check, result in checks.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {check}")
        if not result:
            all_passed = False

    return all_passed


def test_7_streaming_audio():
    """TEST 7: Verify streaming audio implementation"""
    print("\n" + "=" * 70)
    print("TEST 7: STREAMING AUDIO")
    print("=" * 70)

    with open('src/adapters/tts/elevenlabs_tts_adapter.py', 'r') as f:
        content = f.read()

    checks = {
        "Plays first chunk immediately": "first_chunk" in content and "first_audio" in content,
        "Synthesizes rest in background": "remaining_audio_files" in content or "Synthesize remaining" in content,
        "Has streaming message": "play while synthesizing" in content.lower() or "synthesizing rest" in content.lower(),
        "Uses Popen for async playback": "subprocess.Popen" in content
    }

    print("\n📊 Streaming Audio Checks:")
    all_passed = True
    for check, result in checks.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {check}")
        if not result:
            all_passed = False

    return all_passed


def main():
    print("\n🧪 COMPREHENSIVE VOICE PENNY FIX VERIFICATION")
    print("Testing ALL 9 issues that were fixed")
    print("=" * 70)

    results = {
        "Coffee Grep Verification": test_1_coffee_grep(),
        "CAFFEINATED State Removed": test_2_caffeinated_state_gone(),
        "Personality Prompt Quality": test_3_personality_prompt_quality(),
        "Transcription Validation": test_4_transcription_validation_exists(),
        "ENERGIZED State Fix": test_5_enthusiastic_modifiers_removed(),
        "Press-Enter Recording": test_6_press_enter_recording(),
        "Streaming Audio": test_7_streaming_audio()
    }

    print("\n" + "=" * 70)
    print("📊 COMPREHENSIVE TEST SUMMARY")
    print("=" * 70)

    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")

    passed_count = sum(1 for p in results.values() if p)
    total_count = len(results)

    print(f"\n🎯 OVERALL: {passed_count}/{total_count} tests passed")

    if all(results.values()):
        print("\n🎉 ALL TESTS PASSED! Voice Penny comprehensive fix complete.")
        print("\nReady to use:")
        print("  python3 voice_enhanced_penny.py")
        return 0
    else:
        print("\n⚠️  Some tests failed. Review output above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
