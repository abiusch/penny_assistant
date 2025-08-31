"""
Shell commands plugin for PennyGPT
"""

import subprocess
import re
import shlex
from typing import Dict, Any, Optional, List
from ..base_plugin import BasePlugin


class ShellPlugin(BasePlugin):
    """Plugin to handle safe shell command execution"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.timeout = self.config.get('timeout', 10)
        
        # Whitelist of safe commands
        self.allowed_commands = {
            'ls': 'List directory contents',
            'pwd': 'Print working directory', 
            'whoami': 'Show current user',
            'date': 'Show current date and time',
            'uptime': 'Show system uptime',
            'df': 'Show disk usage',
            'ps': 'Show running processes',
            'top': 'Show system processes (brief)',
            'free': 'Show memory usage',
            'uname': 'Show system information',
        }
        
        # Arguments whitelist for each command
        self.allowed_args = {
            'ls': ['-l', '-la', '-a', '-h'],
            'df': ['-h'],
            'ps': ['aux', '-ef'],
            'top': ['-l', '1'],  # macOS: single snapshot
            'free': ['-h'],
            'uname': ['-a'],
        }
    
    def can_handle(self, intent: str, query: str) -> bool:
        """Check if this plugin can handle shell command requests"""
        if intent == 'shell':
            return True
            
        query_lower = query.lower().strip()
        
        # Shell command patterns
        shell_patterns = [
            r'run\s+(ls|pwd|whoami|date|uptime|df|ps|top|free|uname)',
            r'execute\s+(ls|pwd|whoami|date|uptime|df|ps|top|free|uname)',
            r'show me (the )?(files|directory|processes|memory|disk|uptime)',
            r'what\s*(files|processes|memory|disk)\s*(are|is)',
            r'list (files|processes|directory)',
            r'disk (usage|space)',
            r'memory usage',
            r'system (info|uptime)',
            r'who am i',
            r'current (user|directory|time)'
        ]
        
        return any(re.search(pattern, query_lower) for pattern in shell_patterns)
    
    async def execute(self, query: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """Execute shell command safely"""
        try:
            command_info = self._parse_shell_command(query)
            
            if not command_info:
                return {
                    'success': False,
                    'response': "I couldn't understand that command. Try asking for things like 'list files', 'show disk usage', or 'what processes are running'.",
                    'error': 'command_not_recognized'
                }
            
            result = await self._execute_command(command_info)
            
            if result['success']:
                formatted_response = self._format_shell_response(command_info, result['output'])
                return {
                    'success': True,
                    'response': formatted_response,
                    'data': result
                }
            else:
                return {
                    'success': False,
                    'response': f"Command failed: {result['error']}",
                    'error': result['error']
                }
                
        except Exception as e:
            return {
                'success': False,
                'response': f"Error executing command: {str(e)}",
                'error': str(e)
            }
    
    def _parse_shell_command(self, query: str) -> Optional[Dict[str, Any]]:
        """Parse natural language query into shell command"""
        query_lower = query.lower().strip()
        
        # Direct command patterns
        for cmd in self.allowed_commands:
            if f"run {cmd}" in query_lower or f"execute {cmd}" in query_lower:
                return {'command': cmd, 'args': []}
        
        # Natural language patterns
        if any(word in query_lower for word in ['list', 'show']) and any(word in query_lower for word in ['files', 'directory']):
            return {'command': 'ls', 'args': ['-la']}
        
        if 'disk' in query_lower and ('usage' in query_lower or 'space' in query_lower):
            return {'command': 'df', 'args': ['-h']}
        
        if 'memory' in query_lower and 'usage' in query_lower:
            if self._is_macos():
                return {'command': 'top', 'args': ['-l', '1']}
            else:
                return {'command': 'free', 'args': ['-h']}
        
        if any(word in query_lower for word in ['processes', 'running']):
            return {'command': 'ps', 'args': ['aux']}
        
        if 'uptime' in query_lower or 'how long' in query_lower:
            return {'command': 'uptime', 'args': []}
        
        if 'who am i' in query_lower or 'current user' in query_lower:
            return {'command': 'whoami', 'args': []}
        
        if 'current directory' in query_lower or 'where am i' in query_lower:
            return {'command': 'pwd', 'args': []}
        
        if 'date' in query_lower or 'time' in query_lower:
            return {'command': 'date', 'args': []}
        
        if 'system info' in query_lower:
            return {'command': 'uname', 'args': ['-a']}
        
        return None
    
    def _is_macos(self) -> bool:
        """Check if running on macOS"""
        try:
            result = subprocess.run(['uname'], capture_output=True, text=True, timeout=2)
            return result.stdout.strip() == 'Darwin'
        except:
            return False
    
    async def _execute_command(self, command_info: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the shell command safely"""
        cmd = command_info['command']
        args = command_info['args']
        
        # Verify command is allowed
        if cmd not in self.allowed_commands:
            return {
                'success': False,
                'error': f"Command '{cmd}' is not allowed"
            }
        
        # Verify arguments are allowed
        allowed_cmd_args = self.allowed_args.get(cmd, [])
        for arg in args:
            if arg not in allowed_cmd_args:
                return {
                    'success': False, 
                    'error': f"Argument '{arg}' not allowed for command '{cmd}'"
                }
        
        try:
            # Build command with arguments
            full_command = [cmd] + args
            
            # Execute with timeout and security restrictions
            result = subprocess.run(
                full_command,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                cwd='/',  # Run from root to avoid exposing current directory
                env={'PATH': '/usr/bin:/bin:/usr/sbin:/sbin'}  # Minimal PATH
            )
            
            return {
                'success': result.returncode == 0,
                'output': result.stdout,
                'error': result.stderr if result.returncode != 0 else None,
                'command': ' '.join(full_command)
            }
            
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'error': f"Command timed out after {self.timeout} seconds"
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _format_shell_response(self, command_info: Dict[str, Any], output: str) -> str:
        """Format shell command output into natural language response"""
        cmd = command_info['command']
        
        if not output.strip():
            return f"The {cmd} command completed but returned no output."
        
        # Limit output length for voice responses
        lines = output.strip().split('\n')
        if len(lines) > 10:
            truncated_output = '\n'.join(lines[:10])
            response = f"Here are the first 10 lines from {cmd}:\n{truncated_output}\n... and {len(lines) - 10} more lines."
        else:
            response = f"Here's the output from {cmd}:\n{output.strip()}"
        
        # Add context for specific commands
        if cmd == 'df':
            response = "Here's your disk usage:\n" + output.strip()
        elif cmd == 'ps':
            response = f"Here are your running processes (showing first 10):\n" + '\n'.join(lines[:10])
        elif cmd == 'whoami':
            response = f"You are logged in as: {output.strip()}"
        elif cmd == 'pwd':
            response = f"Current directory: {output.strip()}"
        elif cmd == 'date':
            response = f"Current date and time: {output.strip()}"
        elif cmd == 'uptime':
            response = f"System uptime: {output.strip()}"
        
        return response
    
    def get_help_text(self) -> str:
        return "Ask about system info! Try: 'Show disk usage', 'List files', or 'What processes are running?'"
    
    def get_supported_intents(self) -> List[str]:
        return ['shell']


# Test function
if __name__ == "__main__":
    import asyncio
    
    async def test_shell():
        plugin = ShellPlugin()
        
        test_queries = [
            "Show disk usage",
            "List files", 
            "What processes are running?",
            "Who am I?",
            "Show system uptime"
        ]
        
        for query in test_queries:
            print(f"\nTesting: {query}")
            result = await plugin.execute(query)
            print(f"Result: {result['response']}")
    
    asyncio.run(test_shell())
