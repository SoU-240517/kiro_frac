"""
Data models for the Fractal Editor application.
"""

from .data_models import (
    ComplexNumber,
    ComplexRegion,
    FractalParameters,
    FractalResult,
    ParameterDefinition,
    ColorStop,
    ColorPalette,
    InterpolationMode,
    AppSettings,
    FractalProject
)

from .interfaces import (
    FractalGenerator,
    ColorMapper,
    FractalPlugin,
    PluginMetadata
)

__all__ = [
    'ComplexNumber',
    'ComplexRegion', 
    'FractalParameters',
    'FractalResult',
    'ParameterDefinition',
    'ColorStop',
    'ColorPalette',
    'InterpolationMode',
    'AppSettings',
    'FractalProject',
    'FractalGenerator',
    'ColorMapper',
    'FractalPlugin',
    'PluginMetadata'
]