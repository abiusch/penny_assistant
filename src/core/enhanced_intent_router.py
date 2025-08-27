"""
Enhanced intent router with plugin system integration
Extends the existing intent_router.py functionality
"""

import re
from typing import Dict, Any, Optional, Tuple, List
from ..plugins.loader import PluginLoader


class EnhancedIntentRouter:
    """Enhanced router that integrates plugins with existing intent logic"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.plugin_loader = PluginLoader(config)
        self.plugin_loader.load_builtin_plugins()
        
        # Load routing rules from config
        self.routing_rules = self.config.get('routing_rules', {})
    
    def is_agent_mode_trigger(self, text: str) -> bool:
        """Return True if the input text looks like a task that needs Agent Mode."""
        keywords = ["plan", "schedule", "set a reminder", "book", "make a reservation", "text", "call", "order", "find me"]
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in keywords)
    
    def classify_intent(self, text: str) -> str:
        """
        Classify user intent - enhanced version of your existing logic
        """
        text_lower = text.lower().strip()

        # Check for agent mode triggers first
        if self.is_agent_mode_trigger(text):
            return "agent_task"

        # Weather intent (enhanced patterns)
        weather_patterns = [
            r'\b(weather|temperature|temp|forecast|rain|sunny|cloudy|hot|cold)\b',
            r'\bhow.*outside\b',
            r'\bwhat.*like.*outside\b'
        ]
        if any(re.search(pattern, text_lower) for pattern in weather_patterns):
            return "weather"

        # Time intent
        if any(word in text_lower for word in ["time", "clock", "what time"]):
            return "time"

        # Entertainment
        if any(word in text_lower for word in ["joke", "funny", "laugh", "humor"]):
            return "entertainment"

        # Help
        if any(word in text_lower for word in ["help", "assist", "support"]):
            return "help"

        # Calendar/schedule (new)
        calendar_patterns = [
            r'\b(calendar|schedule|meeting|appointment|event)\b',
            r'\bwhen.*\b'
        ]
        if any(re.search(pattern, text_lower) for pattern in calendar_patterns):
            return 'calendar'

        # System/shell commands (new)
        shell_patterns = [
            r'\b(run|execute|command|terminal|shell)\b',
            r'^(ls|cd|pwd|ps|kill|grep)',
            r'\bopen\s+\w+'
        ]
        if any(re.search(pattern, text_lower) for pattern in shell_patterns):
            return 'shell'

        # Default to conversation
        return "conversation"
    
    def route_query(self, query: str, context: Optional[Dict] = None) -> Tuple[str, str, Dict[str, Any]]:
        """
        Route a query to the appropriate handler
        
        Args:
            query: User's query
            context: Optional conversation context
            
        Returns:
            Tuple of (handler_type, intent, payload)
            - handler_type: 'plugin' or 'llm' 
            - intent: The classified intent
            - payload: Dict with routing info and data
        """
        intent = self.classify_intent(query)
        
        # First, try to find a plugin that can handle this
        plugin = self.plugin_loader.find_plugin_for_intent(intent, query)
        if plugin:
            return ('plugin', intent, {
                'plugin_name': plugin.name,
                'plugin_instance': plugin,
                'query': query,
                'context': context
            })
        
        # Fall back to existing intent routing logic
        if intent == "agent_task":
            return ('llm', intent, {"text": query, "requires_planning": True})
        elif intent == "weather":
            return ('llm', intent, {"query": query})
        elif intent == "time":
            return ('llm', intent, {"query": query})
        elif intent == "entertainment":
            return ('llm', intent, {"type": "joke", "query": query})
        elif intent == "help":
            return ('llm', intent, {"query": query})
        else:
            # Default to general conversation
            return ('llm', 'conversation', {"text": query})
    
    async def handle_query(self, query: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Handle a user query by routing it to the appropriate handler
        
        Returns:
            Dict containing the response and metadata
        """
        handler_type, intent, payload = self.route_query(query, context)
        
        if handler_type == 'plugin':
            # Execute plugin
            plugin = payload['plugin_instance']
            result = await plugin.execute(query, context)
            result['handler_type'] = 'plugin'
            result['handler_name'] = payload['plugin_name']
            result['intent'] = intent
            return result
        
        else:
            # Return instruction to use LLM (compatible with existing system)
            return {
                'success': True,
                'handler_type': 'llm',
                'intent': intent,
                'payload': payload,
                'response': None,  # Will be filled by LLM
                'route_to_llm': True
            }
    
    def get_available_plugins(self) -> Dict[str, str]:
        """Get list of available plugins with their help text"""
        plugins = self.plugin_loader.get_all_plugins()
        return {name: plugin.get_help_text() for name, plugin in plugins.items()}
    
    def get_plugin_help(self, plugin_name: str) -> Optional[str]:
        """Get help text for a specific plugin"""
        plugin = self.plugin_loader.get_plugin(plugin_name)
        return plugin.get_help_text() if plugin else None


# Backward compatibility functions to match your existing interface
def route_intent(text: str):
    """
    Legacy function for backward compatibility
    """
    router = EnhancedIntentRouter()
    handler_type, intent, payload = router.route_query(text)
    
    # Return in the old format
    return intent, payload

def is_agent_mode_trigger(text: str) -> bool:
    """Legacy function for backward compatibility"""
    router = EnhancedIntentRouter()
    return router.is_agent_mode_trigger(text)
