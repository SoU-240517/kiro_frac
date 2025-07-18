"""
Fractal generators package.
"""

from .base import FractalGenerator, ColorMapper, FractalGeneratorRegistry, fractal_registry
from .mandelbrot import MandelbrotGenerator
from .julia import JuliaGenerator
from .custom_formula import (
    CustomFormulaGenerator, CustomFormulaGeneratorFactory,
    create_custom_fractal, create_fractal_from_template
)

# Register the generators
fractal_registry.register(MandelbrotGenerator)
fractal_registry.register(JuliaGenerator)

__all__ = [
    'FractalGenerator',
    'ColorMapper', 
    'FractalGeneratorRegistry',
    'fractal_registry',
    'MandelbrotGenerator',
    'JuliaGenerator',
    'CustomFormulaGenerator',
    'CustomFormulaGeneratorFactory',
    'create_custom_fractal',
    'create_fractal_from_template'
]