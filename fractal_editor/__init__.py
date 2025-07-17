"""
Fractal Editor - A Windows desktop application for generating and editing fractals.

This package provides:
- Mathematical fractal generation algorithms
- Interactive user interface for fractal exploration
- Plugin system for custom fractal types
- High-quality image export capabilities
"""

__version__ = "1.0.0"
__author__ = "Fractal Editor Team"

# Core imports for easy access
from .models.data_models import (
    ComplexNumber,
    ComplexRegion,
    FractalParameters,
    FractalResult,
    ColorPalette,
    ColorStop,
    InterpolationMode,
    AppSettings,
    FractalProject,
    ParameterDefinition
)

from .generators.base import FractalGenerator, ColorMapper
from .plugins.base import FractalPlugin, PluginMetadata

from .controllers.base import (
    BaseController,
    FractalController,
    UIController,
    MainController
)

from .services.error_handling import (
    FractalCalculationException,
    FormulaValidationError,
    FormulaEvaluationError,
    PluginLoadError,
    ErrorHandlingService
)

from .services.parallel_calculator import ParallelCalculator

__all__ = [
    # Data models
    'ComplexNumber',
    'ComplexRegion', 
    'FractalParameters',
    'FractalResult',
    'ColorPalette',
    'ColorStop',
    'InterpolationMode',
    'AppSettings',
    'FractalProject',
    'ParameterDefinition',
    'PluginMetadata',
    
    # Base classes
    'FractalGenerator',
    'ColorMapper',
    'FractalPlugin',
    
    # Controllers
    'BaseController',
    'FractalController',
    'UIController',
    'MainController',
    
    # Services
    'ErrorHandlingService',
    'ParallelCalculator',
    
    # Exceptions
    'FractalCalculationException',
    'FormulaValidationError',
    'FormulaEvaluationError',
    'PluginLoadError'
]