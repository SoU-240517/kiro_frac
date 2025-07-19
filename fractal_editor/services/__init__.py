"""
Services module for fractal editor.
Contains business logic and utility services.
"""

from .color_system import (
    ColorStop, ColorPalette, InterpolationMode, ColorMapper,
    GradientColorMapper, PresetPalettes, ColorSystemManager
)

from .image_renderer import (
    RenderSettings, ImageRenderer, HighResolutionRenderer,
    ImageExporter, RenderingEngine
)

from .project_manager import (
    ProjectManager, ProjectFileError, create_default_project
)

from .coordinate_transform import (
    ComplexCoordinateTransform, CoordinateTransformError,
    InvalidCoordinateError, InvalidRegionError
)

__all__ = [
    # Color system
    'ColorStop', 'ColorPalette', 'InterpolationMode', 'ColorMapper',
    'GradientColorMapper', 'PresetPalettes', 'ColorSystemManager',
    
    # Image rendering
    'RenderSettings', 'ImageRenderer', 'HighResolutionRenderer',
    'ImageExporter', 'RenderingEngine',
    
    # Project management
    'ProjectManager', 'ProjectFileError', 'create_default_project',
    
    # Coordinate transformation
    'ComplexCoordinateTransform', 'CoordinateTransformError',
    'InvalidCoordinateError', 'InvalidRegionError'
]