#!/usr/bin/env python3
"""
Penny Usage Tracker - Phase 0 SLM Validation

Track problems during daily Penny usage to determine if SLM investment is warranted.

Usage:
    python3 penny_usage_tracker.py log research "Asked to write Python function, triggered web search"
    python3 penny_usage_tracker.py log personality "Used 'data-daddy' nickname"
    python3 penny_usage_tracker.py log latency "Response took 8 seconds"
    python3 penny_usage_tracker.py report
"""

import json
import sys
from datetime import datetime
from pathlib import Path

TRACKER_FILE = Path(__file__).parent / "data" / "phase0_tracking.json"

def load_data():
    """Load existing tracking data"""
    if TRACKER_FILE.exists():
        with open(TRACKER_FILE, 'r') as f:
            return json.load(f)
    return {
        "start_date": datetime.now().isoformat(),
        "conversations": 0,
        "problems": {
            "research_false_positives": [],
            "personality_violations": [],
            "slow_responses": [],
            "tone_mismatches": [],
            "other": []
        },
        "notes": []
    }

def save_data(data):
    """Save tracking data"""
    TRACKER_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(TRACKER_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def log_problem(category, description):
    """Log a problem occurrence"""
    data = load_data()
    
    # Map category aliases
    category_map = {
        'research': 'research_false_positives',
        'personality': 'personality_violations',
        'latency': 'slow_responses',
        'tone': 'tone_mismatches'
    }
    
    category = category_map.get(category, category)
    
    if category not in data['problems']:
        category = 'other'
    
    entry = {
        "timestamp": datetime.now().isoformat(),
        "description": description
    }
    
    data['problems'][category].append(entry)
    save_data(data)
    
    print(f"✅ Logged: {category} - {description}")

def log_conversation():
    """Increment conversation counter"""
    data = load_data()
    data['conversations'] += 1
    save_data(data)
    print(f"✅ Conversation #{data['conversations']} logged")

def add_note(note):
    """Add a general observation"""
    data = load_data()
    entry = {
        "timestamp": datetime.now().isoformat(),
        "note": note
    }
    data['notes'].append(entry)
    save_data(data)
    print(f"✅ Note added: {note}")

def generate_report():
    """Generate validation report"""
    data = load_data()
    
    print("\n" + "="*60)
    print("📊 PHASE 0 VALIDATION REPORT")
    print("="*60)
    
    print(f"\n📅 Tracking Period: {data['start_date'][:10]} to {datetime.now().date()}")
    print(f"💬 Total Conversations: {data['conversations']}")
    
    print("\n📋 PROBLEM SUMMARY:")
    print("-"*60)
    
    total_problems = 0
    for category, problems in data['problems'].items():
        count = len(problems)
        total_problems += count
        if count > 0:
            print(f"\n{category.upper().replace('_', ' ')}: {count} occurrences")
            for p in problems[-3:]:  # Show last 3
                print(f"  • {p['timestamp'][:19]}: {p['description']}")
            if count > 3:
                print(f"  ... and {count - 3} more")
    
    print(f"\n📊 TOTAL PROBLEMS: {total_problems}")
    
    if data['conversations'] > 0:
        problem_rate = (total_problems / data['conversations']) * 100
        print(f"📈 Problem Rate: {problem_rate:.1f}% of conversations")
    
    print("\n💭 NOTES:")
    print("-"*60)
    for note in data['notes'][-5:]:  # Show last 5
        print(f"  • {note['timestamp'][:19]}: {note['note']}")
    
    print("\n🎯 DECISION CRITERIA:")
    print("-"*60)
    
    research_problems = len(data['problems']['research_false_positives'])
    personality_problems = len(data['problems']['personality_violations'])
    
    print(f"\nResearch False Positives: {research_problems}")
    if research_problems >= 10:
        print("  ⚠️  HIGH - Consider Research Classifier SLM")
    elif research_problems >= 5:
        print("  ⚠️  MODERATE - Monitor closely")
    else:
        print("  ✅ LOW - Pattern matching may be sufficient")
    
    print(f"\nPersonality Violations: {personality_problems}")
    if personality_problems >= 10:
        print("  ⚠️  HIGH - Consider Personality Guard SLM")
    elif personality_problems >= 5:
        print("  ⚠️  MODERATE - Monitor closely")
    else:
        print("  ✅ LOW - Temperature fix may be sufficient")
    
    print("\n🎯 RECOMMENDATION:")
    print("-"*60)
    
    if data['conversations'] < 20:
        print("⏳ INSUFFICIENT DATA - Continue validation")
        print(f"   Need {20 - data['conversations']} more conversations")
    elif total_problems / data['conversations'] > 0.3:
        print("🚀 PROCEED TO SLM PHASE 1")
        print("   High problem rate justifies SLM investment")
        print("   Start with: Research Classifier (highest ROI)")
    elif total_problems / data['conversations'] > 0.15:
        print("🤔 BORDERLINE - Continue validation or prototype")
        print("   Consider quick Research Classifier prototype")
    else:
        print("✅ SIMPLE FIXES SUFFICIENT")
        print("   Focus on Personality Phase 2 instead of SLMs")
        print("   Revisit SLMs in 3-6 months with more data")
    
    print("\n" + "="*60)

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return
    
    command = sys.argv[1]
    
    if command == "log":
        if len(sys.argv) < 4:
            print("Usage: python3 penny_usage_tracker.py log <category> <description>")
            print("Categories: research, personality, latency, tone")
            return
        category = sys.argv[2]
        description = " ".join(sys.argv[3:])
        log_problem(category, description)
    
    elif command == "conversation":
        log_conversation()
    
    elif command == "note":
        if len(sys.argv) < 3:
            print("Usage: python3 penny_usage_tracker.py note <your observation>")
            return
        note = " ".join(sys.argv[2:])
        add_note(note)
    
    elif command == "report":
        generate_report()
    
    elif command == "reset":
        if input("⚠️  Reset all tracking data? (yes/no): ").lower() == "yes":
            TRACKER_FILE.unlink(missing_ok=True)
            print("✅ Tracking data reset")
    
    else:
        print(f"Unknown command: {command}")
        print(__doc__)

if __name__ == "__main__":
    main()
