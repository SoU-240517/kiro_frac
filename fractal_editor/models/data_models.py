"""
Core data models for fractal generation and application settings.
"""
import math
import os
from datetime import datetime
from dataclasses import dataclass, field
from typing import Tuple, Dict, Any, List
from enum import Enum
import numpy as np


@dataclass
class ComplexNumber:
    """Represents a complex number with real and imaginary parts."""
    real: float
    imaginary: float
    
    @property
    def magnitude(self) -> float:
        """Calculate the magnitude (absolute value) of the complex number."""
        return math.sqrt(self.real * self.real + self.imaginary * self.imaginary)
    
    def square(self) -> 'ComplexNumber':
        """Calculate the square of this complex number."""
        return ComplexNumber(
            real=self.real * self.real - self.imaginary * self.imaginary,
            imaginary=2 * self.real * self.imaginary
        )
    
    def __add__(self, other: 'ComplexNumber') -> 'ComplexNumber':
        """Add two complex numbers."""
        return ComplexNumber(self.real + other.real, self.imaginary + other.imaginary)
    
    def to_complex(self) -> complex:
        """Convert to Python's built-in complex type."""
        return complex(self.real, self.imaginary)


@dataclass
class ComplexRegion:
    """Represents a rectangular region in the complex plane."""
    top_left: ComplexNumber
    bottom_right: ComplexNumber
    
    @property
    def width(self) -> float:
        """Get the width of the region."""
        return self.bottom_right.real - self.top_left.real
    
    @property
    def height(self) -> float:
        """Get the height of the region."""
        return self.top_left.imaginary - self.bottom_right.imaginary


@dataclass
class FractalParameters:
    """Parameters for fractal generation."""
    region: ComplexRegion
    max_iterations: int
    image_size: Tuple[int, int]  # (width, height)
    custom_parameters: Dict[str, Any] = field(default_factory=dict)
    
    def validate(self) -> bool:
        """Validate the fractal parameters."""
        if self.max_iterations <= 0:
            return False
        if self.image_size[0] <= 0 or self.image_size[1] <= 0:
            return False
        if self.region.width <= 0 or self.region.height <= 0:
            return False
        return True


@dataclass
class FractalResult:
    """Result of fractal calculation."""
    iteration_data: np.ndarray  # 2D array of iteration counts
    region: ComplexRegion
    calculation_time: float


@dataclass
class ParameterDefinition:
    """Definition of a parameter for fractal generation."""
    name: str
    display_name: str
    parameter_type: str  # 'float', 'int', 'complex', 'bool', 'formula'
    default_value: Any
    min_value: Any = None
    max_value: Any = None
    description: str = ""
    
    def validate_value(self, value: Any) -> bool:
        """Validate a value against this parameter definition."""
        # Type validation
        if self.parameter_type == 'int':
            if not isinstance(value, int):
                return False
            if self.min_value is not None and value < self.min_value:
                return False
            if self.max_value is not None and value > self.max_value:
                return False
        elif self.parameter_type == 'float':
            if not isinstance(value, (int, float)):
                return False
            if self.min_value is not None and value < self.min_value:
                return False
            if self.max_value is not None and value > self.max_value:
                return False
        elif self.parameter_type == 'bool':
            if not isinstance(value, bool):
                return False
        elif self.parameter_type == 'complex':
            if not isinstance(value, (complex, ComplexNumber)):
                return False
        elif self.parameter_type == 'formula':
            if not isinstance(value, str):
                return False
        
        return True


class InterpolationMode(Enum):
    """Color interpolation modes."""
    LINEAR = "linear"
    CUBIC = "cubic"
    HSV = "hsv"


@dataclass
class ColorStop:
    """A color stop in a gradient."""
    position: float  # 0.0 - 1.0
    color: Tuple[int, int, int]  # RGB


@dataclass
class ColorPalette:
    """A color palette for fractal rendering."""
    name: str
    color_stops: List[ColorStop]
    interpolation_mode: InterpolationMode = InterpolationMode.LINEAR


@dataclass
class AppSettings:
    """Application settings."""
    default_max_iterations: int = 1000
    default_image_size: Tuple[int, int] = (800, 600)
    default_color_palette: str = "Rainbow"
    enable_anti_aliasing: bool = True
    thread_count: int = field(default_factory=lambda: os.cpu_count() or 4)
    auto_save_interval: int = 300  # seconds
    recent_projects_count: int = 10


@dataclass
class FractalProject:
    """A fractal project containing all settings and parameters."""
    name: str
    fractal_type: str
    parameters: FractalParameters
    color_palette: ColorPalette
    last_modified: datetime = field(default_factory=datetime.now)
    file_path: str = ""
    
    def save_to_file(self, file_path: str) -> None:
        """Save project to file (implementation to be added later)."""
        self.file_path = file_path
        self.last_modified = datetime.now()
        # JSON serialization implementation will be added in later tasks
    
    @classmethod
    def load_from_file(cls, file_path: str) -> 'FractalProject':
        """Load project from file (implementation to be added later)."""
        # JSON deserialization implementation will be added in later tasks
        raise NotImplementedError("Project loading will be implemented in later tasks")