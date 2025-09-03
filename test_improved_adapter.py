#!/usr/bin/env python3
"""
Test the improved OpenAI-compatible adapter with real LM Studio
"""

import sys
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from adapters.llm.openai_compat import OpenAICompatLLM

def test_improved_adapter():
    """Test the improved adapter with ChatGPT suggestions"""
    
    print("Testing Improved OpenAI-Compatible Adapter")
    print("=" * 45)
    
    # Load actual config
    with open("penny_config.json", "r") as f:
        config = json.load(f)
    
    print(f"Config base_url: {config['llm']['base_url']}")
    
    # Create adapter
    adapter = OpenAICompatLLM(config)
    print(f"Normalized base_url: {adapter.base_url}")
    
    # Test health check
    print("\n🔍 Testing Health Check...")
    health = adapter.health()
    print(f"Status: {health['status']}")
    print(f"Response time: {health.get('response_time_ms', 'N/A')}ms")
    print(f"Available models: {health['available_models']}")
    print(f"Configured model available: {health['model_available']}")
    
    if health['error']:
        print(f"Error: {health['error']}")
    
    # Test completion if healthy
    if health['status'] in ['healthy', 'warning']:
        print("\n💬 Testing Completion...")
        try:
            response = adapter.complete("Say hello in exactly 5 words.", tone="friendly")
            print(f"Response: '{response}'")
            
            if response.startswith("[llm error]"):
                print("❌ Completion failed with error")
            else:
                print("✅ Completion successful")
                
        except Exception as e:
            print(f"❌ Completion exception: {e}")
    else:
        print("⏭️  Skipping completion test - server not healthy")
    
    # Test URL normalization examples
    print("\n🔧 Testing URL Normalization...")
    test_urls = [
        "http://localhost:1234",
        "http://localhost:1234/",
        "http://localhost:1234/v1",
        "http://localhost:1234/v1/",
    ]
    
    for test_url in test_urls:
        test_config = {"llm": {"base_url": test_url}}
        test_adapter = OpenAICompatLLM(test_config)
        print(f"  {test_url:30} → {test_adapter.base_url}")

if __name__ == "__main__":
    test_improved_adapter()
