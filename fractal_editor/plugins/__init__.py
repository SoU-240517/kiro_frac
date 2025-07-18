"""
Plugin system package.
"""

from .base import FractalPlugin, PluginMetadata, PluginManager, plugin_manager

__all__ = [
    'FractalPlugin',
    'PluginMetadata',
    'PluginManager', 
    'plugin_manager'
]