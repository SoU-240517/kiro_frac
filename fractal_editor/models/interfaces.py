"""
Abstract interfaces for fractal generation and plugin system.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Tuple, Dict, Any
from .data_models import FractalParameters, FractalResult, ParameterDefinition, ColorPalette


class FractalGenerator(ABC):
    """Abstract base class for fractal generators."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Get the name of this fractal generator."""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Get the description of this fractal generator."""
        pass
    
    @abstractmethod
    def calculate(self, parameters: FractalParameters) -> FractalResult:
        """Calculate fractal with given parameters."""
        pass
    
    @abstractmethod
    def get_parameter_definitions(self) -> List[ParameterDefinition]:
        """Get the parameter definitions for this fractal type."""
        pass


class ColorMapper(ABC):
    """Abstract base class for color mapping."""
    
    @abstractmethod
    def map_iteration_to_color(self, iteration: int, max_iteration: int) -> Tuple[int, int, int]:
        """Map iteration count to RGB color."""
        pass
    
    @abstractmethod
    def set_palette(self, palette: ColorPalette) -> None:
        """Set the color palette to use for mapping."""
        pass


@dataclass
class PluginMetadata:
    """Metadata for a plugin."""
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
        """Get plugin metadata."""
        pass
    
    @abstractmethod
    def create_generator(self) -> FractalGenerator:
        """Create a fractal generator instance."""
        pass