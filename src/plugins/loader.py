"""
Plugin loader and manager
"""

import os
import importlib
import inspect
from typing import Dict, List, Type, Optional
from .base_plugin import BasePlugin


class PluginLoader:
    """Loads and manages plugins for PennyGPT"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.plugins: Dict[str, BasePlugin] = {}
        self.plugin_classes: Dict[str, Type[BasePlugin]] = {}
        
    def load_builtin_plugins(self) -> None:
        """Load all built-in plugins from src/plugins/builtin/"""
        builtin_dir = os.path.join(os.path.dirname(__file__), 'builtin')
        
        if not os.path.exists(builtin_dir):
            print(f"Warning: Builtin plugins directory not found: {builtin_dir}")
            return
            
        for filename in os.listdir(builtin_dir):
            if filename.endswith('.py') and not filename.startswith('_'):
                module_name = filename[:-3]  # Remove .py
                self._load_plugin_module(f"plugins.builtin.{module_name}", module_name)
    
    def _load_plugin_module(self, module_path: str, module_name: str) -> None:
        """Load a single plugin module"""
        try:
            # Use src prefix for absolute import
            full_module_path = f"src.{module_path}"
            module = importlib.import_module(full_module_path)
            
            # Find all BasePlugin subclasses in the module
            for name, obj in inspect.getmembers(module):
                if (inspect.isclass(obj) and 
                    issubclass(obj, BasePlugin) and 
                    obj != BasePlugin):
                    
                    plugin_config = self.config.get('plugins', {}).get(module_name, {})
                    plugin_instance = obj(plugin_config)
                    
                    self.plugins[plugin_instance.name] = plugin_instance
                    self.plugin_classes[plugin_instance.name] = obj
                    
                    print(f"Loaded plugin: {plugin_instance.name}")
                    
        except ImportError as e:
            print(f"Failed to load plugin {module_name}: {e}")
        except Exception as e:
            print(f"Error initializing plugin {module_name}: {e}")
    
    def find_plugin_for_intent(self, intent: str, query: str) -> Optional[BasePlugin]:
        """Find the best plugin to handle a given intent/query"""
        for plugin in self.plugins.values():
            if plugin.can_handle(intent, query):
                return plugin
        return None
    
    def get_all_plugins(self) -> Dict[str, BasePlugin]:
        """Get all loaded plugins"""
        return self.plugins.copy()
    
    def get_plugin(self, name: str) -> Optional[BasePlugin]:
        """Get a specific plugin by name"""
        return self.plugins.get(name)
