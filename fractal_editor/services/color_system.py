"""
Color system for fractal rendering.

This module provides color palette management, color mapping, and interpolation
functionality for rendering fractal images with various color schemes.
"""

import math
import colorsys
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import List, Tuple, Dict, Any
import numpy as np


class InterpolationMode(Enum):
    """Color interpolation modes."""
    LINEAR = "linear"
    CUBIC = "cubic"
    HSV = "hsv"


@dataclass
class ColorStop:
    """Represents a color stop in a gradient."""
    position: float  # 0.0 - 1.0
    color: Tuple[int, int, int]  # RGB values (0-255)
    
    def __post_init__(self):
        """Validate color stop values."""
        if not 0.0 <= self.position <= 1.0:
            raise ValueError(f"Position must be between 0.0 and 1.0, got {self.position}")
        
        r, g, b = self.color
        if not all(0 <= c <= 255 for c in [r, g, b]):
            raise ValueError(f"RGB values must be between 0 and 255, got {self.color}")


@dataclass
class ColorPalette:
    """Represents a color palette with gradient stops."""
    name: str
    color_stops: List[ColorStop]
    interpolation_mode: InterpolationMode = InterpolationMode.LINEAR
    
    def __post_init__(self):
        """Validate and sort color stops."""
        if len(self.color_stops) < 2:
            raise ValueError("Color palette must have at least 2 color stops")
        
        # Sort color stops by position
        self.color_stops.sort(key=lambda stop: stop.position)
        
        # Ensure first stop is at 0.0 and last stop is at 1.0
        if self.color_stops[0].position != 0.0:
            raise ValueError("First color stop must be at position 0.0")
        if self.color_stops[-1].position != 1.0:
            raise ValueError("Last color stop must be at position 1.0")


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


class GradientColorMapper(ColorMapper):
    """Color mapper that uses gradient interpolation between color stops."""
    
    def __init__(self, palette: ColorPalette = None):
        self._palette = palette
    
    def set_palette(self, palette: ColorPalette) -> None:
        """Set the color palette to use for mapping."""
        self._palette = palette
    
    def map_iteration_to_color(self, iteration: int, max_iteration: int) -> Tuple[int, int, int]:
        """Map iteration count to RGB color using gradient interpolation."""
        if not self._palette:
            raise ValueError("No palette set")
        
        if iteration >= max_iteration:
            # Points that didn't escape - use black
            return (0, 0, 0)
        
        # Normalize iteration to 0.0-1.0 range
        position = iteration / max_iteration
        
        return self._interpolate_color(position)
    
    def _interpolate_color(self, position: float) -> Tuple[int, int, int]:
        """Interpolate color at given position using the current palette."""
        # Clamp position to valid range
        position = max(0.0, min(1.0, position))
        
        # Find the two color stops to interpolate between
        stops = self._palette.color_stops
        
        # Handle edge cases
        if position <= stops[0].position:
            return stops[0].color
        if position >= stops[-1].position:
            return stops[-1].color
        
        # Find the two stops to interpolate between
        for i in range(len(stops) - 1):
            if stops[i].position <= position <= stops[i + 1].position:
                return self._interpolate_between_stops(
                    stops[i], stops[i + 1], position
                )
        
        # Fallback (should not reach here)
        return stops[-1].color
    
    def _interpolate_between_stops(self, stop1: ColorStop, stop2: ColorStop, position: float) -> Tuple[int, int, int]:
        """Interpolate color between two color stops."""
        # Calculate interpolation factor
        if stop2.position == stop1.position:
            t = 0.0
        else:
            t = (position - stop1.position) / (stop2.position - stop1.position)
        
        if self._palette.interpolation_mode == InterpolationMode.LINEAR:
            return self._linear_interpolation(stop1.color, stop2.color, t)
        elif self._palette.interpolation_mode == InterpolationMode.CUBIC:
            return self._cubic_interpolation(stop1.color, stop2.color, t)
        elif self._palette.interpolation_mode == InterpolationMode.HSV:
            return self._hsv_interpolation(stop1.color, stop2.color, t)
        else:
            return self._linear_interpolation(stop1.color, stop2.color, t)
    
    def _linear_interpolation(self, color1: Tuple[int, int, int], color2: Tuple[int, int, int], t: float) -> Tuple[int, int, int]:
        """Linear interpolation between two RGB colors."""
        r1, g1, b1 = color1
        r2, g2, b2 = color2
        
        r = int(r1 + (r2 - r1) * t)
        g = int(g1 + (g2 - g1) * t)
        b = int(b1 + (b2 - b1) * t)
        
        return (r, g, b)
    
    def _cubic_interpolation(self, color1: Tuple[int, int, int], color2: Tuple[int, int, int], t: float) -> Tuple[int, int, int]:
        """Cubic (smooth) interpolation between two RGB colors."""
        # Use smoothstep function for cubic interpolation
        smooth_t = t * t * (3.0 - 2.0 * t)
        return self._linear_interpolation(color1, color2, smooth_t)
    
    def _hsv_interpolation(self, color1: Tuple[int, int, int], color2: Tuple[int, int, int], t: float) -> Tuple[int, int, int]:
        """HSV interpolation between two RGB colors."""
        # Convert RGB to HSV
        r1, g1, b1 = [c / 255.0 for c in color1]
        r2, g2, b2 = [c / 255.0 for c in color2]
        
        h1, s1, v1 = colorsys.rgb_to_hsv(r1, g1, b1)
        h2, s2, v2 = colorsys.rgb_to_hsv(r2, g2, b2)
        
        # Interpolate in HSV space
        # Handle hue wraparound
        if abs(h2 - h1) > 0.5:
            if h1 > h2:
                h2 += 1.0
            else:
                h1 += 1.0
        
        h = (h1 + (h2 - h1) * t) % 1.0
        s = s1 + (s2 - s1) * t
        v = v1 + (v2 - v1) * t
        
        # Convert back to RGB
        r, g, b = colorsys.hsv_to_rgb(h, s, v)
        return (int(r * 255), int(g * 255), int(b * 255))


class PresetPalettes:
    """Collection of preset color palettes."""
    
    @staticmethod
    def get_rainbow() -> ColorPalette:
        """Classic rainbow palette."""
        return ColorPalette(
            name="Rainbow",
            color_stops=[
                ColorStop(0.0, (255, 0, 0)),    # Red
                ColorStop(0.17, (255, 165, 0)),  # Orange
                ColorStop(0.33, (255, 255, 0)),  # Yellow
                ColorStop(0.5, (0, 255, 0)),     # Green
                ColorStop(0.67, (0, 0, 255)),    # Blue
                ColorStop(0.83, (75, 0, 130)),   # Indigo
                ColorStop(1.0, (148, 0, 211))    # Violet
            ],
            interpolation_mode=InterpolationMode.HSV
        )
    
    @staticmethod
    def get_fire() -> ColorPalette:
        """Fire-themed palette."""
        return ColorPalette(
            name="Fire",
            color_stops=[
                ColorStop(0.0, (0, 0, 0)),       # Black
                ColorStop(0.25, (128, 0, 0)),    # Dark red
                ColorStop(0.5, (255, 0, 0)),     # Red
                ColorStop(0.75, (255, 165, 0)),  # Orange
                ColorStop(1.0, (255, 255, 0))    # Yellow
            ],
            interpolation_mode=InterpolationMode.LINEAR
        )
    
    @staticmethod
    def get_ocean() -> ColorPalette:
        """Ocean-themed palette."""
        return ColorPalette(
            name="Ocean",
            color_stops=[
                ColorStop(0.0, (0, 0, 64)),      # Dark blue
                ColorStop(0.33, (0, 64, 128)),   # Medium blue
                ColorStop(0.67, (0, 128, 255)),  # Light blue
                ColorStop(1.0, (255, 255, 255))  # White
            ],
            interpolation_mode=InterpolationMode.LINEAR
        )
    
    @staticmethod
    def get_grayscale() -> ColorPalette:
        """Grayscale palette."""
        return ColorPalette(
            name="Grayscale",
            color_stops=[
                ColorStop(0.0, (0, 0, 0)),       # Black
                ColorStop(1.0, (255, 255, 255))  # White
            ],
            interpolation_mode=InterpolationMode.LINEAR
        )
    
    @staticmethod
    def get_sunset() -> ColorPalette:
        """Sunset-themed palette."""
        return ColorPalette(
            name="Sunset",
            color_stops=[
                ColorStop(0.0, (25, 25, 112)),   # Midnight blue
                ColorStop(0.2, (138, 43, 226)),  # Blue violet
                ColorStop(0.4, (255, 20, 147)),  # Deep pink
                ColorStop(0.6, (255, 69, 0)),    # Red orange
                ColorStop(0.8, (255, 215, 0)),   # Gold
                ColorStop(1.0, (255, 255, 224))  # Light yellow
            ],
            interpolation_mode=InterpolationMode.HSV
        )
    
    @staticmethod
    def get_electric() -> ColorPalette:
        """Electric-themed palette."""
        return ColorPalette(
            name="Electric",
            color_stops=[
                ColorStop(0.0, (0, 0, 0)),       # Black
                ColorStop(0.25, (0, 0, 255)),    # Blue
                ColorStop(0.5, (0, 255, 255)),   # Cyan
                ColorStop(0.75, (255, 255, 0)),  # Yellow
                ColorStop(1.0, (255, 255, 255))  # White
            ],
            interpolation_mode=InterpolationMode.LINEAR
        )
    
    @staticmethod
    def get_all_presets() -> Dict[str, ColorPalette]:
        """Get all preset palettes as a dictionary."""
        return {
            "Rainbow": PresetPalettes.get_rainbow(),
            "Fire": PresetPalettes.get_fire(),
            "Ocean": PresetPalettes.get_ocean(),
            "Grayscale": PresetPalettes.get_grayscale(),
            "Sunset": PresetPalettes.get_sunset(),
            "Electric": PresetPalettes.get_electric()
        }


class ColorSystemManager:
    """Manager class for the color system."""
    
    def __init__(self):
        self._presets = PresetPalettes.get_all_presets()
        self._current_mapper = GradientColorMapper()
        self._current_palette = self._presets["Rainbow"]
        self._current_mapper.set_palette(self._current_palette)
    
    def get_preset_names(self) -> List[str]:
        """Get list of available preset palette names."""
        return list(self._presets.keys())
    
    def get_preset_palette(self, name: str) -> ColorPalette:
        """Get a preset palette by name."""
        if name not in self._presets:
            raise ValueError(f"Unknown preset palette: {name}")
        return self._presets[name]
    
    def set_current_palette(self, palette: ColorPalette) -> None:
        """Set the current active palette."""
        self._current_palette = palette
        self._current_mapper.set_palette(palette)
    
    def set_current_palette_by_name(self, name: str) -> None:
        """Set the current palette by preset name."""
        palette = self.get_preset_palette(name)
        self.set_current_palette(palette)
    
    def get_current_palette(self) -> ColorPalette:
        """Get the current active palette."""
        return self._current_palette
    
    def get_color_mapper(self) -> ColorMapper:
        """Get the current color mapper."""
        return self._current_mapper
    
    def create_custom_palette(self, name: str, color_stops: List[Tuple[float, Tuple[int, int, int]]], 
                            interpolation_mode: InterpolationMode = InterpolationMode.LINEAR) -> ColorPalette:
        """Create a custom color palette."""
        stops = [ColorStop(pos, color) for pos, color in color_stops]
        return ColorPalette(name, stops, interpolation_mode)