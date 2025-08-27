"""
Plugin system for PennyGPT
"""

from .loader import PluginLoader
from .base_plugin import BasePlugin

__all__ = ['PluginLoader', 'BasePlugin']
