#!/usr/bin/env python3
"""
Tool Registry - Phase 3B Week 3
Registers and implements executable tools for the orchestrator.
"""

import asyncio
import sys
import os
from typing import Dict, Any
import logging

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from enhanced_web_search import EnhancedWebSearch

logger = logging.getLogger(__name__)


class ToolImplementations:
    """Implementations of all available tools."""

    @staticmethod
    async def web_search(args: Dict[str, Any]) -> str:
        """
        Execute web search using enhanced_web_search.py

        Args:
            args: {"query": "search terms", "max_results": 3}

        Returns:
            Formatted search results
        """
        query = args.get("query", "")
        max_results = args.get("max_results", 3)

        if not query:
            return "ERROR: No search query provided"

        logger.info(f"🔍 Searching web for: '{query}'")

        try:
            async with EnhancedWebSearch() as search:
                results = await search.search(query, max_results=max_results)

            if not results:
                return f"No search results found for '{query}'. The information may not be available or search providers are unavailable."

            # Format results for LLM
            formatted = f"SEARCH RESULTS FOR '{query}':\n\n"

            for i, result in enumerate(results, 1):
                formatted += f"{i}. {result.title}\n"
                formatted += f"   {result.snippet}\n"
                formatted += f"   Source: {result.url}\n"
                formatted += f"   (via {result.provider}, confidence: {result.confidence})\n\n"

            formatted += f"\nFound {len(results)} result(s). Use this information to answer the user's question."

            logger.info(f"✅ Web search completed: {len(results)} results")
            return formatted

        except Exception as e:
            error_msg = f"Web search failed: {e}"
            logger.error(f"❌ {error_msg}")
            return f"ERROR: {error_msg}"

    @staticmethod
    def math_calc(args: Dict[str, Any]) -> str:
        """
        Execute mathematical calculation.

        Args:
            args: {"expression": "2 + 2"} or {"equation": "..."}

        Returns:
            Calculation result
        """
        expression = args.get("expression") or args.get("equation", "")

        if not expression:
            return "ERROR: No expression provided"

        logger.info(f"🧮 Calculating: '{expression}'")

        try:
            # Safe eval with limited scope
            # Only allow basic math operations
            allowed_names = {
                'abs': abs,
                'round': round,
                'pow': pow,
                'sum': sum,
                'min': min,
                'max': max,
            }

            # Use eval with restricted namespace
            result = eval(expression, {"__builtins__": {}}, allowed_names)

            logger.info(f"✅ Calculation result: {result}")
            return f"CALCULATION RESULT:\n{expression} = {result}"

        except Exception as e:
            error_msg = f"Calculation failed: {e}"
            logger.error(f"❌ {error_msg}")
            return f"ERROR: {error_msg}"

    @staticmethod
    def code_execute(args: Dict[str, Any]) -> str:
        """
        Execute code (placeholder for future implementation).

        Args:
            args: {"code": "print('hello')", "language": "python"}

        Returns:
            Execution result
        """
        logger.warning("⚠️ Code execution not yet implemented")
        return "ERROR: Code execution is not yet implemented. This feature is coming soon."


class ToolRegistry:
    """
    Central registry of all available tools.

    Maps tool names to their implementations and provides metadata.
    """

    def __init__(self):
        self.tools = {
            "web.search": ToolImplementations.web_search,
            "math.calc": ToolImplementations.math_calc,
            "code.execute": ToolImplementations.code_execute,
        }

        logger.info(f"🔧 Tool Registry initialized with {len(self.tools)} tools")

    def get_tool(self, tool_name: str):
        """Get tool implementation by name."""
        return self.tools.get(tool_name)

    def list_tools(self) -> list:
        """List all available tool names."""
        return list(self.tools.keys())

    def get_tool_manifest(self) -> str:
        """
        Get tool manifest for LLM system prompt.

        This tells the LLM what tools are available and how to use them.
        """
        manifest = """
AVAILABLE TOOLS:
You have access to the following tools. When you need to use a tool, output the tool call syntax.

1. web.search - Search the web for current information
   Use when: User asks about recent events, current prices, new products, latest news
   Syntax: <|channel|>browser.run<|message|>{"query": "search terms"}
   Example: <|channel|>browser.run<|message|>{"query": "1x.tech NEO robot review"}

2. math.calc - Perform mathematical calculations
   Use when: User asks for calculations, math problems
   Syntax: <|channel|>calculator<|message|>{"expression": "2 + 2"}
   Example: <|channel|>calculator<|message|>{"expression": "15% of 847293"}

3. code.execute - Execute code (coming soon)
   Status: Not yet implemented

IMPORTANT INSTRUCTIONS:
- If you can answer from your training data, do so directly (no tool needed)
- If you need current/recent information not in your training, use web.search
- If you need to calculate something complex, use math.calc
- Output ONLY the tool call syntax when you need a tool
- After receiving tool results, provide a natural conversational answer using that information
- Do NOT make up or hallucinate information - use tools to get facts
"""
        return manifest

    def register_with_orchestrator(self, orchestrator):
        """Register all tools with the orchestrator."""
        for tool_name, tool_func in self.tools.items():
            orchestrator.register_tool(tool_name, tool_func)

        logger.info(f"✅ Registered {len(self.tools)} tools with orchestrator")


# Global registry instance
_registry = None


def get_tool_registry() -> ToolRegistry:
    """Get global tool registry instance."""
    global _registry
    if _registry is None:
        _registry = ToolRegistry()
    return _registry
