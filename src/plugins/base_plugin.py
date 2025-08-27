"""
Abstract base class for all PennyGPT plugins
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional


class BasePlugin(ABC):
    """Base class that all plugins must inherit from"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.name = self.__class__.__name__.lower().replace('plugin', '')
    
    @abstractmethod
    def can_handle(self, intent: str, query: str) -> bool:
        """
        Determine if this plugin can handle the given intent/query
        
        Args:
            intent: The classified intent (e.g., 'weather', 'calendar', etc.)
            query: The original user query
            
        Returns:
            bool: True if this plugin can handle the request
        """
        pass
    
    @abstractmethod
    async def execute(self, query: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Execute the plugin's functionality
        
        Args:
            query: The user's query
            context: Optional context from the conversation
            
        Returns:
            Dict containing:
                - success: bool
                - response: str (text response for user)
                - data: Optional[Dict] (structured data)
                - error: Optional[str] (error message if failed)
        """
        pass
    
    def get_help_text(self) -> str:
        """Return help text describing what this plugin does"""
        return f"Plugin: {self.name}"
    
    def get_supported_intents(self) -> List[str]:
        """Return list of intents this plugin supports"""
        return []
