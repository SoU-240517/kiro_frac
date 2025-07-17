"""
Services for the Fractal Editor application.
"""

from .error_handling import (
    ErrorHandlingService,
    FractalCalculationException,
    FormulaValidationError,
    FormulaEvaluationError,
    PluginLoadError
)
from .parallel_calculator import ParallelCalculator

__all__ = [
    'ErrorHandlingService',
    'FractalCalculationException',
    'FormulaValidationError', 
    'FormulaEvaluationError',
    'PluginLoadError',
    'ParallelCalculator'
]