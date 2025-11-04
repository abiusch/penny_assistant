#!/usr/bin/env python3
"""
Tool Call Orchestrator - Phase 3B Week 3
Intercepts and manages tool calling from LLM output.
"""

import re
import json
import asyncio
from typing import Optional, Dict, Any, Callable, List, Union
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class ToolCall:
    """Represents a parsed tool call from LLM."""
    tool_name: str
    arguments: Dict[str, Any]
    raw_output: str

    def to_dict(self) -> Dict:
        return {
            "type": "tool",
            "tool": self.tool_name,
            "args": self.arguments
        }


@dataclass
class FinalAnswer:
    """Represents a final answer (no tool call)."""
    content: str

    def to_dict(self) -> Dict:
        return {
            "type": "final",
            "content": self.content
        }


class ToolCallParser:
    """
    Parses LLM output to detect and extract tool calls.

    Handles the <|channel|>...<|message|>{...} syntax from gpt-oss-20b.
    """

    def __init__(self):
        # Pattern to match: <|channel|>anything<|message|>{json}
        self.tool_pattern = re.compile(
            r'<\|channel\|>(.*?)<\|message\|>(\{.*?\})',
            re.DOTALL
        )

    def parse(self, model_output: str) -> Union[ToolCall, FinalAnswer]:
        """
        Parse model output for tool calls.

        Returns:
            ToolCall if tool syntax detected
            FinalAnswer if normal response
        """
        # Check for tool call syntax
        match = self.tool_pattern.search(model_output)

        if match:
            return self._parse_tool_call(match, model_output)
        else:
            return self._parse_final_answer(model_output)

    def _parse_tool_call(self, match, raw_output: str) -> ToolCall:
        """Extract tool name and arguments from matched pattern."""
        try:
            tool_descriptor = match.group(1).strip()  # e.g., "commentary to=browser.run code"
            args_json = match.group(2)  # e.g., '{"query": "..."}'

            # Parse arguments
            arguments = json.loads(args_json)

            # Map tool descriptor to standard tool name
            tool_name = self._map_tool_name(tool_descriptor, arguments)

            logger.info(f"🔧 Tool call detected: {tool_name} with args: {arguments}")

            return ToolCall(
                tool_name=tool_name,
                arguments=arguments,
                raw_output=raw_output
            )

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse tool arguments: {e}")
            # Treat as final answer if parsing fails
            return FinalAnswer(content=raw_output)
        except Exception as e:
            logger.error(f"Error parsing tool call: {e}")
            return FinalAnswer(content=raw_output)

    def _map_tool_name(self, descriptor: str, arguments: Dict) -> str:
        """
        Map tool descriptor to standard tool name.

        Examples:
            "commentary to=browser.run code" → "web.search"
            "calculator" → "math.calc"
        """
        descriptor_lower = descriptor.lower()

        # Web search indicators
        if any(keyword in descriptor_lower for keyword in ['browser', 'search', 'web', 'query']):
            return "web.search"

        # Math/calculator indicators
        if any(keyword in descriptor_lower for keyword in ['calc', 'math', 'compute']):
            return "math.calc"

        # Code execution indicators
        if any(keyword in descriptor_lower for keyword in ['code', 'execute', 'run', 'python']):
            return "code.execute"

        # Check arguments for hints
        if 'query' in arguments:
            return "web.search"
        if 'expression' in arguments or 'equation' in arguments:
            return "math.calc"
        if 'code' in arguments:
            return "code.execute"

        # Default to web search (most common)
        logger.warning(f"Unknown tool descriptor: {descriptor}, defaulting to web.search")
        return "web.search"

    def _parse_final_answer(self, model_output: str) -> FinalAnswer:
        """Parse output as final answer (no tool call)."""
        # Clean up any remaining artifacts
        cleaned = self._clean_output(model_output)

        return FinalAnswer(content=cleaned)

    def _clean_output(self, text: str) -> str:
        """Remove any residual tool syntax from output."""
        # Remove incomplete tool calls
        text = self.tool_pattern.sub('', text)

        # Remove other artifacts
        text = re.sub(r'<\|[^|]+\|>', '', text)

        # Clean up whitespace
        text = re.sub(r'\s+', ' ', text).strip()

        return text


class ToolOrchestrator:
    """
    Orchestrates tool calling workflow.

    Manages the loop: LLM → Tool Call → Execute → LLM → Final Answer
    """

    def __init__(self, max_iterations: int = 3):
        """
        Initialize orchestrator.

        Args:
            max_iterations: Maximum tool call iterations before forcing exit
        """
        self.parser = ToolCallParser()
        self.max_iterations = max_iterations
        self.tool_registry = {}  # Will be populated by ToolRegistry

        logger.info(f"🎭 Tool Orchestrator initialized (max_iterations: {max_iterations})")

    def register_tool(self, tool_name: str, tool_func: Callable):
        """Register a tool function."""
        self.tool_registry[tool_name] = tool_func
        logger.info(f"🔧 Registered tool: {tool_name}")

    async def orchestrate(
        self,
        initial_prompt: str,
        llm_generator: Callable,
        conversation_context: List[Dict] = None
    ) -> str:
        """
        Orchestrate the tool calling loop.

        Args:
            initial_prompt: The user's query
            llm_generator: Function to call LLM (takes context, returns output)
            conversation_context: Existing conversation history

        Returns:
            Final answer string for user
        """
        if conversation_context is None:
            conversation_context = []

        # Add user query
        conversation_context.append({
            "role": "user",
            "content": initial_prompt
        })

        iteration = 0

        while iteration < self.max_iterations:
            iteration += 1
            logger.info(f"🔄 Orchestration iteration {iteration}/{self.max_iterations}")

            # Generate LLM response
            try:
                model_output = llm_generator(conversation_context)
            except Exception as e:
                logger.error(f"LLM generation failed: {e}")
                return "I encountered an error processing your request."

            # Parse output
            parsed = self.parser.parse(model_output)

            if isinstance(parsed, FinalAnswer):
                # Done! Return to user
                logger.info(f"✅ Final answer received (iteration {iteration})")
                return parsed.content

            elif isinstance(parsed, ToolCall):
                # Execute tool
                logger.info(f"🔧 Executing tool: {parsed.tool_name}")

                tool_result = await self._execute_tool(parsed)

                # Add tool call and result to context
                conversation_context.append({
                    "role": "assistant",
                    "content": f"[TOOL_CALL: {parsed.tool_name}({json.dumps(parsed.arguments)})]"
                })

                conversation_context.append({
                    "role": "system",
                    "content": f"TOOL_RESULT:\n{tool_result}\n\nNow provide a natural conversational answer using these results."
                })

                # Loop continues - LLM will generate again with tool results
                logger.info(f"✅ Tool executed, looping back to LLM")

        # Max iterations reached
        logger.warning(f"⚠️ Max iterations ({self.max_iterations}) reached")
        return "I had trouble finding the right information. Could you rephrase your question?"

    async def _execute_tool(self, tool_call: ToolCall) -> str:
        """
        Execute a tool and return results.

        Returns:
            Tool results as formatted string
        """
        tool_func = self.tool_registry.get(tool_call.tool_name)

        if not tool_func:
            error_msg = f"Tool '{tool_call.tool_name}' not found in registry"
            logger.error(f"❌ {error_msg}")
            return f"ERROR: {error_msg}"

        try:
            # Execute tool (handle both sync and async)
            if asyncio.iscoroutinefunction(tool_func):
                result = await tool_func(tool_call.arguments)
            else:
                result = tool_func(tool_call.arguments)

            return str(result)

        except Exception as e:
            error_msg = f"Tool execution failed: {e}"
            logger.error(f"❌ {error_msg}")
            return f"ERROR: {error_msg}"


# Global orchestrator instance
_orchestrator = None


def get_orchestrator() -> ToolOrchestrator:
    """Get global orchestrator instance."""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = ToolOrchestrator(max_iterations=3)
    return _orchestrator
