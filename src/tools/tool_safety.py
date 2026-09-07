#!/usr/bin/env python3
"""
Tool Safety Module - Week 4 Fix #4
Provides timeout, rate limiting, and input validation for tools.
"""

import time
import asyncio
from functools import wraps
from typing import Dict, Any, Callable
import re
from collections import defaultdict
from datetime import datetime, timedelta
import logging
import builtins
import json
from pathlib import Path
import subprocess
import sys
from threading import Lock

logger = logging.getLogger(__name__)


class ToolSafetyError(Exception):
    """Base exception for tool safety violations."""
    pass


class ToolTimeoutError(ToolSafetyError):
    """Tool execution exceeded timeout."""
    pass


class ToolRateLimitError(ToolSafetyError):
    """Tool rate limit exceeded."""
    pass


class ToolValidationError(ToolSafetyError):
    """Tool input validation failed."""
    pass


class RateLimiter:
    """Rate limiter for tool calls."""
    
    def __init__(self, max_calls: int = 5, window_seconds: int = 60):
        """
        Initialize rate limiter.
        
        Args:
            max_calls: Maximum calls allowed in window
            window_seconds: Time window in seconds
        """
        self.max_calls = max_calls
        self.window_seconds = window_seconds
        self.calls: Dict[str, list] = defaultdict(list)
        self._lock = Lock()
    
    def check_rate_limit(self, tool_name: str) -> bool:
        """
        Check if tool can be called without exceeding rate limit.
        
        Args:
            tool_name: Name of the tool
            
        Returns:
            True if call is allowed, False otherwise
        """
        with self._lock:
            now = time.monotonic()
            self._expire(tool_name, now)
            if len(self.calls[tool_name]) >= self.max_calls:
                logger.warning(f"Rate limit exceeded for {tool_name}")
                return False
            self.calls[tool_name].append(now)
            return True
    
    def get_remaining_calls(self, tool_name: str) -> int:
        """Get number of remaining calls in current window."""
        with self._lock:
            self._expire(tool_name, time.monotonic())
            return max(0, self.max_calls - len(self.calls[tool_name]))

    def _expire(self, tool_name, now):
        self.calls[tool_name] = [stamp for stamp in self.calls[tool_name]
                                 if stamp > now - self.window_seconds]
    
    def reset(self, tool_name: str = None):
        """Reset rate limiter for specific tool or all tools."""
        with self._lock:
            if tool_name:
                self.calls[tool_name] = []
            else:
                self.calls.clear()


class InputValidator:
    """Validates tool inputs for safety."""
    
    @staticmethod
    def validate_web_search(args: Dict[str, Any]) -> bool:
        """
        Validate web search arguments.
        
        Args:
            args: Tool arguments
            
        Returns:
            True if valid
            
        Raises:
            ToolValidationError: If validation fails
        """
        query = args.get("query", "")
        
        # Check query exists
        if not query or not isinstance(query, str):
            raise ToolValidationError("Query must be a non-empty string")
        
        # Check query length
        if len(query) > 500:
            raise ToolValidationError("Query too long (max 500 chars)")
        
        # Check for suspicious patterns
        suspicious_patterns = [
            r'<script',
            r'javascript:',
            r'onerror=',
            r'eval\(',
        ]
        
        query_lower = query.lower()
        for pattern in suspicious_patterns:
            if re.search(pattern, query_lower):
                raise ToolValidationError(f"Suspicious pattern detected: {pattern}")
        
        # Check max_results if present
        max_results = args.get("max_results", 3)
        if not isinstance(max_results, int) or max_results < 1 or max_results > 10:
            raise ToolValidationError("max_results must be integer between 1-10")
        
        return True
    
    @staticmethod
    def validate_math_calc(args: Dict[str, Any]) -> bool:
        """
        Validate math calculation arguments.
        
        Args:
            args: Tool arguments
            
        Returns:
            True if valid
            
        Raises:
            ToolValidationError: If validation fails
        """
        expression = args.get("expression") or args.get("equation", "")
        
        # Check expression exists
        if not expression or not isinstance(expression, str):
            raise ToolValidationError("Expression must be a non-empty string")
        
        # Check length
        if len(expression) > 200:
            raise ToolValidationError("Expression too long (max 200 chars)")
        
        # Check for dangerous patterns
        dangerous_patterns = [
            r'import\s',
            r'exec\(',
            r'eval\(',
            r'__\w+__',
            r'open\(',
            r'file\(',
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, expression, re.IGNORECASE):
                raise ToolValidationError(f"Dangerous pattern detected: {pattern}")
        
        # Only allow safe characters
        allowed_chars = set('0123456789+-*/().%^, abcdefghijklmnopqrstuvwxyz')
        if not all(c.lower() in allowed_chars for c in expression):
            raise ToolValidationError("Expression contains invalid characters")
        
        return True
    
    @staticmethod
    def validate_code_execute(args: Dict[str, Any]) -> bool:
        """
        Validate code execution arguments.
        
        Args:
            args: Tool arguments
            
        Returns:
            True if valid
            
        Raises:
            ToolValidationError: If validation fails
        """
        # For now, code execution is disabled for safety
        raise ToolValidationError("Code execution is disabled for security")


def with_timeout(seconds: int = 30):
    """
    Cancel async tools or kill/reap a synchronous tool's worker on timeout.

    Sync tools must be importable functions with JSON inputs/results; closures,
    bound instances, and in-process state mutations are not supported. Validation
    and shared rate limits belong outside this boundary, in the caller process.
    
    Args:
        seconds: Timeout in seconds (default: 30)
    """
    def decorator(func: Callable):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                return await asyncio.wait_for(
                    func(*args, **kwargs),
                    timeout=seconds
                )
            except asyncio.TimeoutError:
                logger.error(f"{func.__name__} timed out after {seconds}s")
                raise ToolTimeoutError(f"Tool execution timed out after {seconds} seconds")
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            module, name = func.__module__, func.__qualname__
            if module == '__main__' or '<locals>' in name or getattr(func, '__self__', None) is not None:
                raise ToolSafetyError('Synchronous tools must be importable functions')
            worker = Path(__file__).with_name('sync_worker.py').resolve()
            try:
                # subprocess.run kills and waits for the child on timeout.
                # No shell, process-global alarms, or abandoned worker threads.
                completed = subprocess.run(
                    [sys.executable, str(worker), module, name],
                    input=json.dumps([args, kwargs], allow_nan=False),
                    text=True, encoding='utf-8', stdout=subprocess.PIPE,
                    stderr=subprocess.DEVNULL, timeout=seconds,
                )
            except subprocess.TimeoutExpired as error:
                raise ToolTimeoutError(f'Tool execution timed out after {seconds} seconds') from error
            if completed.returncode != 0:
                raise ToolSafetyError('Tool worker exited without a result')
            try:
                response = json.loads(completed.stdout)
            except json.JSONDecodeError as error:
                raise ToolSafetyError('Tool worker returned an invalid result') from error
            if response['ok']:
                return response['result']
            error_type = getattr(builtins, response['error'], ToolSafetyError)
            if not isinstance(error_type, type) or not issubclass(error_type, Exception):
                error_type = ToolSafetyError
            raise error_type(response['message'])

        sync_wrapper._penny_timeout_target = func
        
        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def with_rate_limit(rate_limiter: RateLimiter, tool_name: str):
    """
    Decorator to add rate limiting to tool functions.
    
    Args:
        rate_limiter: RateLimiter instance
        tool_name: Name of the tool for tracking
    """
    def decorator(func: Callable):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            if not rate_limiter.check_rate_limit(tool_name):
                remaining = rate_limiter.get_remaining_calls(tool_name)
                raise ToolRateLimitError(
                    f"Rate limit exceeded for {tool_name}. "
                    f"Try again later. (Remaining: {remaining})"
                )
            return await func(*args, **kwargs)
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            if not rate_limiter.check_rate_limit(tool_name):
                remaining = rate_limiter.get_remaining_calls(tool_name)
                raise ToolRateLimitError(
                    f"Rate limit exceeded for {tool_name}. "
                    f"Try again later. (Remaining: {remaining})"
                )
            return func(*args, **kwargs)
        
        # Return appropriate wrapper
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def with_validation(validator_func: Callable):
    """
    Decorator to add input validation to tool functions.
    
    Args:
        validator_func: Validation function that takes args dict
    """
    def decorator(func: Callable):
        @wraps(func)
        async def async_wrapper(args: Dict[str, Any], *extra_args, **kwargs):
            # Validate inputs
            validator_func(args)
            return await func(args, *extra_args, **kwargs)
        
        @wraps(func)
        def sync_wrapper(args: Dict[str, Any], *extra_args, **kwargs):
            # Validate inputs
            validator_func(args)
            return func(args, *extra_args, **kwargs)
        
        # Return appropriate wrapper
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


class SafeToolWrapper:
    """Wraps tools with safety mechanisms."""
    
    def __init__(
        self,
        timeout_seconds: int = 30,
        max_calls_per_minute: int = 5
    ):
        """
        Initialize safe tool wrapper.
        
        Args:
            timeout_seconds: Timeout for tool execution
            max_calls_per_minute: Rate limit per tool
        """
        self.timeout_seconds = timeout_seconds
        self.rate_limiter = RateLimiter(
            max_calls=max_calls_per_minute,
            window_seconds=60
        )
        self.validator = InputValidator()
    
    def wrap_tool(self, tool_name: str, tool_func: Callable) -> Callable:
        """
        Wrap a tool with safety mechanisms.
        
        Args:
            tool_name: Name of the tool
            tool_func: Tool function to wrap
            
        Returns:
            Wrapped tool function with safety
        """
        # Get appropriate validator
        validator_map = {
            'web.search': self.validator.validate_web_search,
            'math.calc': self.validator.validate_math_calc,
            'code.execute': self.validator.validate_code_execute,
        }
        
        validator = validator_map.get(tool_name, lambda args: True)
        
        # Apply decorators
        safe_func = with_timeout(self.timeout_seconds)(tool_func)
        safe_func = with_validation(validator)(safe_func)
        safe_func = with_rate_limit(self.rate_limiter, tool_name)(safe_func)
        
        logger.info(f"✅ Tool {tool_name} wrapped with safety mechanisms")
        
        return safe_func
    
    def reset_rate_limits(self, tool_name: str = None):
        """Reset rate limits for debugging/testing."""
        self.rate_limiter.reset(tool_name)


# Global instance
_safe_wrapper = None


def get_safe_tool_wrapper(
    timeout_seconds: int = 30,
    max_calls_per_minute: int = 5
) -> SafeToolWrapper:
    """Get global safe tool wrapper instance."""
    global _safe_wrapper
    if _safe_wrapper is None:
        _safe_wrapper = SafeToolWrapper(timeout_seconds, max_calls_per_minute)
    return _safe_wrapper


__all__ = [
    'ToolSafetyError',
    'ToolTimeoutError',
    'ToolRateLimitError',
    'ToolValidationError',
    'RateLimiter',
    'InputValidator',
    'SafeToolWrapper',
    'get_safe_tool_wrapper',
    'with_timeout',
    'with_rate_limit',
    'with_validation',
]
