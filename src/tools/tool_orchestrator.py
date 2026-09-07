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
from src.llm.errors import ModelGenerationError, require_response_text

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


class ToolParseError(ValueError):
    """The model attempted a tool call that does not satisfy the protocol."""


class ToolCallParser:
    """
    Parses LLM output to detect and extract tool calls.

    Handles channel-wrapped requests and bare JSON tool envelopes returned
    by servers that strip the model's channel tokens.
    """

    def __init__(self):
        # Match only the header; a JSON decoder handles nested objects and
        # braces inside strings. A brace regex cannot parse JSON correctly.
        self.tool_pattern = re.compile(
            r'<\|channel\|>(.*?)<\|message\|>\s*',
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
        model_output = model_output.strip()
        match = self.tool_pattern.match(model_output)

        if match:
            return self._parse_tool_call(match, model_output)
        # Only an explicit top-level tool envelope is executable. Do not
        # search prose, code examples, or nested JSON for possible actions.
        if model_output.startswith('{'):
            try:
                decoded, end = json.JSONDecoder().raw_decode(model_output)
            except json.JSONDecodeError as e:
                if re.match(r'\{\s*"tool"\s*:', model_output):
                    raise ToolParseError("Invalid tool JSON") from e
            else:
                if isinstance(decoded, dict) and 'tool' in decoded:
                    return self._validated_tool_call(
                        decoded, model_output[end:].strip(), model_output,
                    )
        if '<|channel|>' in model_output or '<|message|>' in model_output:
            raise ToolParseError("Incomplete or mixed tool request")
        return self._parse_final_answer(model_output)

    def _parse_tool_call(self, match, raw_output: str) -> ToolCall:
        """Extract tool name and arguments from matched pattern."""
        try:
            tool_descriptor = match.group(1).strip()
            payload = raw_output[match.end():]
            decoded, end = json.JSONDecoder().raw_decode(payload)
            suffix = payload[end:].strip()
            return self._validated_tool_call(decoded, suffix, raw_output, tool_descriptor)

        except json.JSONDecodeError as e:
            raise ToolParseError("Invalid tool JSON") from e

    def _validated_tool_call(self, decoded, suffix: str, raw_output: str,
                             tool_descriptor: Optional[str] = None) -> ToolCall:
        if suffix not in ('', '<|im_end|>', '<|end|>', '<|fim_suffix|>'):
            raise ToolParseError("Expected one tool request without trailing content")
        if not isinstance(decoded, dict):
            raise ToolParseError("Tool payload must be an object")

        if 'tool' in decoded or 'args' in decoded:
            if set(decoded) != {'tool', 'args'}:
                raise ToolParseError("Tool request requires only tool and args")
            tool_name, arguments = decoded['tool'], decoded['args']
        elif tool_descriptor is not None:
            # Compatibility with the previously documented flat payloads.
            tool_name = self._map_tool_name(tool_descriptor, decoded)
            arguments = decoded
        else:
            raise ToolParseError("Missing tool envelope")

        if not isinstance(tool_name, str) or not re.fullmatch(r'[A-Za-z][\w.-]*', tool_name):
            raise ToolParseError("Invalid tool name")
        if not isinstance(arguments, dict):
            raise ToolParseError("Tool arguments must be an object")

        logger.info("Tool call detected: %s", tool_name)
        return ToolCall(tool_name=tool_name, arguments=arguments, raw_output=raw_output)

    def _map_tool_name(self, descriptor: str, arguments: Dict) -> str:
        """
        Map tool descriptor to standard tool name.

        Examples:
            "commentary to=browser.run code" → "web.search"
            "calculator" → "math.calc"
        """
        match = re.fullmatch(
            r'(?:commentary\s+to=)?([\w.-]+)(?:\s+(?:code|json))?',
            descriptor.lower(),
        )
        if not match:
            raise ToolParseError("Unrecognized legacy tool descriptor")
        name = match.group(1)
        if name in ('commentary', 'analysis', 'final'):
            raise ToolParseError("Missing tool name")
        # Unknown explicit names reach the registry and are refused there.
        # Never infer a different action from argument keys or substrings.
        return {'browser.run': 'web.search', 'calculator': 'math.calc'}.get(name, name)

    def _parse_final_answer(self, model_output: str) -> FinalAnswer:
        """Parse output as final answer (no tool call)."""
        # Clean up any remaining artifacts
        cleaned = self._clean_output(model_output)

        return FinalAnswer(content=cleaned)

    def _clean_output(self, text: str) -> str:
        """Remove any residual tool syntax from output."""
        # Remove other artifacts
        text = re.sub(r'<\|[^|]+\|>', '', text)

        # Preserve paragraph breaks, lists, and indentation in code blocks.
        return text.strip()


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

        Raises:
            ModelGenerationError: No usable model answer; the caller must handle
                the failed turn without recording a successful conversation.
        """
        conversation_context = [dict(message) for message in (conversation_context or [])]

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
                model_output = require_response_text(llm_generator(conversation_context))
            except ModelGenerationError:
                raise
            except Exception as e:
                logger.error('LLM generation failed (%s)', type(e).__name__)
                raise ModelGenerationError() from None

            # Parse output
            try:
                parsed = self.parser.parse(model_output)
            except ToolParseError as e:
                logger.warning("Invalid tool request: %s", e)
                return "I couldn't read that tool request. Please try again."

            if isinstance(parsed, FinalAnswer):
                # Done! Return to user
                answer = require_response_text(parsed.content)
                logger.info(f"✅ Final answer received (iteration {iteration})")
                return answer

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
                    "role": "tool",
                    "name": parsed.tool_name,
                    "content": tool_result,
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
