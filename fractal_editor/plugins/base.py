"""
Plugin system base classes and interfaces.
Defines the plugin architecture for extending fractal generators.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Any, List, Optional
from ..generators.base import FractalGenerator


@dataclass
class PluginMetadata:
    """Metadata for a fractal plugin."""
    name: str
    version: str
    author: str
    description: str
    min_app_version: str = "1.0.0"
    dependencies: List[str] = None
    
    def __post_init__(self):
        """Initialize default values."""
        if self.dependencies is None:
            self.dependencies = []


class FractalPlugin(ABC):
    """Abstract base class for fractal plugins."""
    
    @property
    @abstractmethod
    def metadata(self) -> PluginMetadata:
        """Get the metadata for this plugin."""
        pass
    
    @abstractmethod
    def create_generator(self) -> FractalGenerator:
        """
        Create an instance of the fractal generator provided by this plugin.
        
        Returns:
            A new instance of the fractal generator
        """
        pass
    
    def initialize(self) -> bool:
        """
        Initialize the plugin. Called when the plugin is loaded.
        
        Returns:
            True if initialization was successful, False otherwise
        """
        return True
    
    def cleanup(self) -> None:
        """Clean up resources when the plugin is unloaded."""
        pass
    
    def get_configuration_schema(self) -> Optional[Dict[str, Any]]:
        """
        Get the configuration schema for this plugin.
        
        Returns:
            Dictionary describing the configuration options, or None if no configuration
        """
        return None


class PluginManager:
    """Manages loading, unloading, and execution of plugins."""
    
    def __init__(self):
        self._loaded_plugins: Dict[str, FractalPlugin] = {}
        self._plugin_paths: List[str] = []
        self._disabled_plugins: set[str] = set()
    
    def add_plugin_path(self, path: str) -> None:
        """
        Add a directory path to search for plugins.
        
        Args:
            path: Directory path to search for plugins
        """
        if path not in self._plugin_paths:
            self._plugin_paths.append(path)
    
    def load_plugin(self, plugin_class: type[FractalPlugin]) -> bool:
        """
        Load a plugin from a plugin class.
        
        Args:
            plugin_class: The plugin class to load
            
        Returns:
            True if the plugin was loaded successfully, False otherwise
        """
        try:
            plugin_instance = plugin_class()
            metadata = plugin_instance.metadata
            
            # Check if plugin is disabled
            if metadata.name in self._disabled_plugins:
                return False
            
            # Check if plugin is already loaded
            if metadata.name in self._loaded_plugins:
                return False
            
            # Initialize the plugin
            if not plugin_instance.initialize():
                return False
            
            # Register the plugin
            self._loaded_plugins[metadata.name] = plugin_instance
            
            # Register the generator with the global registry
            from ..generators.base import fractal_registry
            fractal_registry.register(type(plugin_instance.create_generator()))
            
            return True
            
        except Exception as e:
            # Log the error (logging will be implemented in later tasks)
            print(f"Failed to load plugin: {e}")
            return False
    
    def unload_plugin(self, plugin_name: str) -> bool:
        """
        Unload a plugin by name.
        
        Args:
            plugin_name: The name of the plugin to unload
            
        Returns:
            True if the plugin was unloaded successfully, False otherwise
        """
        if plugin_name not in self._loaded_plugins:
            return False
        
        try:
            plugin = self._loaded_plugins[plugin_name]
            plugin.cleanup()
            del self._loaded_plugins[plugin_name]
            return True
        except Exception as e:
            # Log the error (logging will be implemented in later tasks)
            print(f"Failed to unload plugin {plugin_name}: {e}")
            return False
    
    def get_loaded_plugins(self) -> List[str]:
        """
        Get a list of loaded plugin names.
        
        Returns:
            List of loaded plugin names
        """
        return list(self._loaded_plugins.keys())
    
    def get_plugin_info(self, plugin_name: str) -> Optional[PluginMetadata]:
        """
        Get information about a loaded plugin.
        
        Args:
            plugin_name: The name of the plugin
            
        Returns:
            Plugin metadata, or None if plugin is not loaded
        """
        if plugin_name not in self._loaded_plugins:
            return None
        
        return self._loaded_plugins[plugin_name].metadata
    
    def disable_plugin(self, plugin_name: str) -> None:
        """
        Disable a plugin (prevent it from loading).
        
        Args:
            plugin_name: The name of the plugin to disable
        """
        self._disabled_plugins.add(plugin_name)
        
        # Unload if currently loaded
        if plugin_name in self._loaded_plugins:
            self.unload_plugin(plugin_name)
    
    def enable_plugin(self, plugin_name: str) -> None:
        """
        Enable a previously disabled plugin.
        
        Args:
            plugin_name: The name of the plugin to enable
        """
        self._disabled_plugins.discard(plugin_name)
    
    def is_plugin_disabled(self, plugin_name: str) -> bool:
        """
        Check if a plugin is disabled.
        
        Args:
            plugin_name: The name of the plugin to check
            
        Returns:
            True if the plugin is disabled, False otherwise
        """
        return plugin_name in self._disabled_plugins


# Global plugin manager instance
plugin_manager = PluginManager()