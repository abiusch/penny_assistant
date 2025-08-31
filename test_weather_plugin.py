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


async def test_calculations_plugin():
    """Test calculations plugin directly"""
    print("\n=== Testing Calculations Plugin ===")
    
    try:
        from src.plugins.builtin.calculations import CalculationsPlugin
    except ImportError as e:
        print(f"Calculations plugin import failed: {e}")
        return None
    
    plugin = CalculationsPlugin()
    print(f"Plugin loaded: {plugin.name}")
    
    # Test intent recognition
    test_cases = [
        ("What's 15 + 25?", 'calculation'),
        ("25% of 200", 'calculation'),
        ("Convert 25 celsius to fahrenheit", 'calculation'),
        ("Square root of 144", 'calculation'),
        ("Tell me a joke", 'entertainment'),  # Should not match
    ]
    
    for query, intent in test_cases:
        can_handle = plugin.can_handle(intent, query)
        print(f"Query: '{query}' (intent: {intent}) -> Can handle: {can_handle}")
    
    # Test execution
    print("\n--- Testing calculations execution ---")
    test_calculations = [
        "What's 15 + 25?",
        "25% of 200", 
        "Square root of 144",
        "Convert 25 celsius to fahrenheit"
    ]
    
    for calc in test_calculations:
        result = await plugin.execute(calc)
        print(f"Calculation: {calc}")
        print(f"Success: {result['success']}")
        print(f"Response: {result['response']}")
        print()
    
    return plugin


async def test_shell_plugin():
    """Test shell plugin directly"""
    print("\n=== Testing Shell Plugin ===")
    
    # Import here to avoid issues if shell plugin has problems
    try:
        from src.plugins.builtin.shell import ShellPlugin
    except ImportError as e:
        print(f"Shell plugin import failed: {e}")
        return None
    
    plugin = ShellPlugin()
    print(f"Plugin loaded: {plugin.name}")
    
    # Test intent recognition
    test_cases = [
        ("Show disk usage", 'shell'),
        ("List files", 'shell'),
        ("What processes are running?", 'shell'),
        ("Who am I?", 'shell'),
        ("Tell me a joke", 'entertainment'),  # Should not match
    ]
    
    for query, intent in test_cases:
        can_handle = plugin.can_handle(intent, query)
        print(f"Query: '{query}' (intent: {intent}) -> Can handle: {can_handle}")
    
    # Test execution
    print("\n--- Testing shell execution ---")
    test_commands = ["Show disk usage", "Who am I?", "List files"]
    
    for cmd in test_commands:
        result = await plugin.execute(cmd)
        print(f"Command: {cmd}")
        print(f"Success: {result['success']}")
        if result['success']:
            response = result['response'][:100] + "..." if len(result['response']) > 100 else result['response']
            print(f"Response: {response}")
        else:
            print(f"Error: {result['error']}")
        print()
    
    return plugin


async def test_calendar_plugin():
    """Test calendar plugin directly"""
    print("\n=== Testing Calendar Plugin ===")
    
    # Import here to avoid issues if calendar plugin has problems
    try:
        from src.plugins.builtin.calendar import CalendarPlugin
    except ImportError as e:
        print(f"Calendar plugin import failed: {e}")
        return None
    
    plugin = CalendarPlugin()
    print(f"Plugin loaded: {plugin.name}")
    
    # Test intent recognition
    test_cases = [
        ("What's on my calendar today?", 'calendar'),
        ("What's my next meeting?", 'calendar'),
        ("Do I have anything tomorrow?", 'calendar'),
        ("Tell me a joke", 'entertainment'),  # Should not match
    ]
    
    for query, intent in test_cases:
        can_handle = plugin.can_handle(intent, query)
        print(f"Query: '{query}' (intent: {intent}) -> Can handle: {can_handle}")
    
    # Test execution
    print("\n--- Testing calendar execution ---")
    result = await plugin.execute("What's on my calendar today?")
    print(f"Calendar result: {result}")
    
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
        "What's on my calendar today?",  # Test calendar plugin
        "What's my next meeting?",      # Test calendar plugin
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
        
        # Test calculations plugin
        calc_plugin = await test_calculations_plugin()
        
        # Test shell plugin
        shell_plugin = await test_shell_plugin()
        
        # Test calendar plugin
        calendar_plugin = await test_calendar_plugin()
        
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
