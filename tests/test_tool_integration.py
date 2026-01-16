#!/usr/bin/env python3
"""
Quick test for tool calling integration
Tests orchestrator without full pipeline dependencies
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.tools.tool_orchestrator import ToolOrchestrator
from src.tools.tool_registry import get_tool_registry

def mock_llm_generate(prompt):
    """Mock LLM that returns a tool call"""
    # Simulate LLM deciding to use calculator
    return '<|channel|>commentary<|message|>{"tool": "math.calc", "args": {"expression": "42 * 13"}}'

def test_tool_orchestrator():
    """Test tool orchestrator end-to-end"""
    print("🧪 Testing Tool Orchestrator")
    print("=" * 60)
    
    # Setup
    registry = get_tool_registry()
    orchestrator = ToolOrchestrator(registry)
    
    print(f"✅ Registry loaded: {len(registry.tools)} tools")
    print(f"   Available: {list(registry.tools.keys())}")
    
    # Create mock LLM
    class MockLLM:
        def __init__(self, response):
            self.response = response
            
        def generate(self, prompt):
            return self.response
        
        def complete(self, prompt, tone=None):
            return self.response
    
    # Test 1: Tool call
    print(f"\\n📝 Test 1: Calculator tool call")
    mock_llm = MockLLM('<|channel|>Let me calculate that<|message|>{"tool": "math.calc", "args": {"expression": "42 * 13"}}')
    
    response = orchestrator.orchestrate(
        user_input="What's 42 times 13?",
        system_prompt="You are a helpful assistant",
        llm=mock_llm,
        tone="helpful"
    )
    
    print(f"Response: {response[:200]}")
    if "546" in response:
        print("✅ Calculator worked!")
    else:
        print(f"❌ Expected '546' in response")
    
    # Test 2: Direct answer (no tool)
    print(f"\\n📝 Test 2: Direct answer (no tool call)")
    mock_llm_direct = MockLLM("Hello! I'm doing great, thanks for asking.")
    
    response2 = orchestrator.orchestrate(
        user_input="How are you?",
        system_prompt="You are a helpful assistant",
        llm=mock_llm_direct,
        tone="friendly"
    )
    
    print(f"Response: {response2[:200]}")
    if "great" in response2.lower():
        print("✅ Direct response worked!")
    else:
        print(f"❌ Expected direct response")
    
    # Test 3: Web search
    print(f"\\n📝 Test 3: Web search tool call")
    mock_llm_search = MockLLM('<|channel|>Let me search that<|message|>{"tool": "web.search", "args": {"query": "Python programming"}}')
    
    response3 = orchestrator.orchestrate(
        user_input="Tell me about Python",
        system_prompt="You are a helpful assistant",
        llm=mock_llm_search,
        tone="helpful"
    )
    
    print(f"Response: {response3[:200]}")
    if response3 and len(response3) > 0:
        print("✅ Web search attempt completed (may fail if no internet)")
    else:
        print(f"❌ Web search failed completely")
    
    print(f"\\n✨ Tool Orchestrator Test Complete!")
    print("=" * 60)

if __name__ == "__main__":
    test_tool_orchestrator()
