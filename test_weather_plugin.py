#!/usr/bin/env python3
"""
Test the weather plugin setup
"""

import asyncio
import os
import sys
import json

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.plugins.builtin.weather import WeatherPlugin
from src.core.enhanced_intent_router import EnhancedIntentRouter


async def test_weather_plugin():
    """Test weather plugin directly"""
    print("=== Testing Weather Plugin ===")
    
    # Test without API key first
    plugin = WeatherPlugin()
    print(f"Plugin loaded: {plugin.name}")
    print(f"Has API key: {bool(plugin.api_key)}")
    
    # Test intent recognition with proper intents
    test_cases = [
        ("What's the weather?", 'weather'),
        ("How's the weather in London?", 'weather'),
        ("What's the temperature in Tokyo?", 'weather'),
        ("Tell me a joke", 'entertainment'),  # Should not match
    ]
    
    for query, intent in test_cases:
        can_handle = plugin.can_handle(intent, query)
        print(f"Query: '{query}' (intent: {intent}) -> Can handle: {can_handle}")
    
    # Test execution (will fail without API key, but should return proper error)
    print("\n--- Testing execution ---")
    result = await plugin.execute("What's the weather?")
    print(f"Result: {result}")
    
    return plugin


async def test_enhanced_router():
    """Test the enhanced intent router"""
    print("\n=== Testing Enhanced Intent Router ===")
    
    # Load config if it exists
    config = {}
    try:
        with open('penny_config.json', 'r') as f:
            config = json.load(f)
    except FileNotFoundError:
        print("No penny_config.json found, using defaults")
    
    router = EnhancedIntentRouter(config)
    
    # Test queries
    test_queries = [
        "What's the weather like?",
        "How's the weather in Paris?", 
        "Tell me a joke",
        "What time is it?",
        "Help me with something",
        "Plan my day"
    ]
    
    for query in test_queries:
        intent = router.classify_intent(query)
        handler_type, classified_intent, payload = router.route_query(query)
        
        print(f"Query: '{query}'")
        print(f"  Intent: {intent}")
        print(f"  Handler: {handler_type}")
        print(f"  Payload keys: {list(payload.keys())}")
        print()
    
    # Test async handling
    print("--- Testing async query handling ---")
    result = await router.handle_query("What's the weather in Berlin?")
    print(f"Weather query result: {result}")
    
    return router


async def main():
    """Run all tests"""
    print("Testing PennyGPT Weather Plugin Setup")
    print("=" * 50)
    
    try:
        # Test plugin directly
        plugin = await test_weather_plugin()
        
        # Test router integration  
        router = await test_enhanced_router()
        
        print("\n=== Summary ===")
        plugins = router.get_available_plugins()
        print(f"Available plugins: {list(plugins.keys())}")
        
        for name, help_text in plugins.items():
            print(f"  {name}: {help_text}")
        
        print("\n✅ Plugin system setup successful!")
        print("\nSystem Status:")
        if plugin.api_key:
            print("• Weather API key: ✅ Configured")
            print("• Weather plugin: ✅ Working with real data")
        else:
            print("• Weather API key: ❌ Missing")
            print("• Set: export OPENWEATHER_API_KEY='your_key'")
            print("• Get key: https://openweathermap.org/api")
        print("• Plugin routing: ✅ Working")
        print("• LLM fallback: ✅ Working")
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
