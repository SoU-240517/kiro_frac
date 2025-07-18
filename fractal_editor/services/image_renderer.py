"""
Image rendering engine for fractal visualization.

This module provides functionality to convert NumPy arrays to Pillow images,
apply anti-aliasing, and adjust brightness/contrast for fractal rendering.
"""

import numpy as np
from PIL import Image, ImageEnhance, ImageFilter
from typing import Tuple, Optional
from dataclasses import dataclass

from .color_system import ColorMapper, GradientColorMapper, PresetPalettes


@dataclass
class RenderSettings:
    """Settings for image rendering."""
    anti_aliasing: bool = True
    brightness: float = 1.0  # 0.0 to 2.0, 1.0 is normal
    contrast: float = 1.0    # 0.0 to 2.0, 1.0 is normal
    gamma: float = 1.0       # 0.1 to 3.0, 1.0 is normal
    
    def __post_init__(self):
        """Validate render settings."""
        if not 0.0 <= self.brightness <= 2.0:
            raise ValueError(f"Brightness must be between 0.0 and 2.0, got {self.brightness}")
        if not 0.0 <= self.contrast <= 2.0:
            raise ValueError(f"Contrast must be between 0.0 and 2.0, got {self.contrast}")
        if not 0.1 <= self.gamma <= 3.0:
            raise ValueError(f"Gamma must be between 0.1 and 3.0, got {self.gamma}")


class ImageRenderer:
    """Renders fractal iteration data to PIL Images."""
    
    def __init__(self, color_mapper: ColorMapper = None):
        """Initialize the image renderer.
        
        Args:
            color_mapper: Color mapper to use for coloring. If None, uses default rainbow palette.
        """
        if color_mapper is None:
            default_mapper = GradientColorMapper()
            default_mapper.set_palette(PresetPalettes.get_rainbow())
            self._color_mapper = default_mapper
        else:
            self._color_mapper = color_mapper
    
    def set_color_mapper(self, color_mapper: ColorMapper) -> None:
        """Set the color mapper to use for rendering."""
        self._color_mapper = color_mapper
    
    def render_to_image(self, iteration_data: np.ndarray, max_iterations: int, 
                       settings: RenderSettings = None) -> Image.Image:
        """Render iteration data to a PIL Image.
        
        Args:
            iteration_data: 2D NumPy array of iteration counts
            max_iterations: Maximum iteration count used in calculation
            settings: Render settings to apply
            
        Returns:
            PIL Image object
        """
        if settings is None:
            settings = RenderSettings()
        
        # Convert iteration data to RGB image
        rgb_array = self._iteration_to_rgb(iteration_data, max_iterations)
        
        # Create PIL Image from RGB array
        image = Image.fromarray(rgb_array, 'RGB')
        
        # Apply post-processing effects
        if settings.anti_aliasing:
            image = self._apply_anti_aliasing(image)
        
        if settings.brightness != 1.0:
            image = self._adjust_brightness(image, settings.brightness)
        
        if settings.contrast != 1.0:
            image = self._adjust_contrast(image, settings.contrast)
        
        if settings.gamma != 1.0:
            image = self._apply_gamma_correction(image, settings.gamma)
        
        return image
    
    def render_to_array(self, iteration_data: np.ndarray, max_iterations: int) -> np.ndarray:
        """Render iteration data to RGB array without post-processing.
        
        Args:
            iteration_data: 2D NumPy array of iteration counts
            max_iterations: Maximum iteration count used in calculation
            
        Returns:
            3D NumPy array with shape (height, width, 3) containing RGB values
        """
        return self._iteration_to_rgb(iteration_data, max_iterations)
    
    def _iteration_to_rgb(self, iteration_data: np.ndarray, max_iterations: int) -> np.ndarray:
        """Convert iteration data to RGB array using the color mapper.
        
        Args:
            iteration_data: 2D NumPy array of iteration counts
            max_iterations: Maximum iteration count
            
        Returns:
            3D NumPy array with RGB values
        """
        height, width = iteration_data.shape
        rgb_array = np.zeros((height, width, 3), dtype=np.uint8)
        
        # Vectorized color mapping for better performance
        for i in range(height):
            for j in range(width):
                iteration = iteration_data[i, j]
                color = self._color_mapper.map_iteration_to_color(iteration, max_iterations)
                rgb_array[i, j] = color
        
        return rgb_array
    
    def _apply_anti_aliasing(self, image: Image.Image) -> Image.Image:
        """Apply anti-aliasing to smooth the image.
        
        Args:
            image: PIL Image to process
            
        Returns:
            Anti-aliased PIL Image
        """
        # Use a slight Gaussian blur for anti-aliasing
        return image.filter(ImageFilter.GaussianBlur(radius=0.5))
    
    def _adjust_brightness(self, image: Image.Image, brightness: float) -> Image.Image:
        """Adjust image brightness.
        
        Args:
            image: PIL Image to process
            brightness: Brightness factor (1.0 = normal, 0.0 = black, 2.0 = very bright)
            
        Returns:
            Brightness-adjusted PIL Image
        """
        enhancer = ImageEnhance.Brightness(image)
        return enhancer.enhance(brightness)
    
    def _adjust_contrast(self, image: Image.Image, contrast: float) -> Image.Image:
        """Adjust image contrast.
        
        Args:
            image: PIL Image to process
            contrast: Contrast factor (1.0 = normal, 0.0 = gray, 2.0 = high contrast)
            
        Returns:
            Contrast-adjusted PIL Image
        """
        enhancer = ImageEnhance.Contrast(image)
        return enhancer.enhance(contrast)
    
    def _apply_gamma_correction(self, image: Image.Image, gamma: float) -> Image.Image:
        """Apply gamma correction to the image.
        
        Args:
            image: PIL Image to process
            gamma: Gamma value (1.0 = normal, <1.0 = brighter, >1.0 = darker)
            
        Returns:
            Gamma-corrected PIL Image
        """
        # Convert to numpy array for gamma correction
        img_array = np.array(image, dtype=np.float32)
        
        # Apply gamma correction: output = input^(1/gamma)
        img_array = img_array / 255.0  # Normalize to 0-1
        img_array = np.power(img_array, 1.0 / gamma)
        img_array = img_array * 255.0  # Scale back to 0-255
        
        # Clip values and convert back to uint8
        img_array = np.clip(img_array, 0, 255).astype(np.uint8)
        
        return Image.fromarray(img_array, 'RGB')


class HighResolutionRenderer:
    """Specialized renderer for high-resolution fractal images."""
    
    def __init__(self, color_mapper: ColorMapper = None):
        """Initialize the high-resolution renderer."""
        self._base_renderer = ImageRenderer(color_mapper)
    
    def render_high_resolution(self, iteration_data: np.ndarray, max_iterations: int,
                             scale_factor: int = 2, settings: RenderSettings = None) -> Image.Image:
        """Render a high-resolution version of the fractal.
        
        Args:
            iteration_data: 2D NumPy array of iteration counts
            max_iterations: Maximum iteration count
            scale_factor: Factor by which to increase resolution (2 = 4x pixels)
            settings: Render settings to apply
            
        Returns:
            High-resolution PIL Image
        """
        if settings is None:
            settings = RenderSettings()
        
        # Upscale the iteration data using interpolation
        upscaled_data = self._upscale_iteration_data(iteration_data, scale_factor)
        
        # Render the upscaled data
        return self._base_renderer.render_to_image(upscaled_data, max_iterations, settings)
    
    def _upscale_iteration_data(self, iteration_data: np.ndarray, scale_factor: int) -> np.ndarray:
        """Upscale iteration data using bilinear interpolation.
        
        Args:
            iteration_data: Original iteration data
            scale_factor: Scaling factor
            
        Returns:
            Upscaled iteration data
        """
        from scipy.ndimage import zoom
        
        try:
            # Use scipy for high-quality upscaling if available
            return zoom(iteration_data, scale_factor, order=1)  # Bilinear interpolation
        except ImportError:
            # Fallback to simple nearest-neighbor upscaling
            return np.repeat(np.repeat(iteration_data, scale_factor, axis=0), scale_factor, axis=1)


class ImageExporter:
    """Handles exporting fractal images to various formats."""
    
    def __init__(self, renderer: ImageRenderer = None):
        """Initialize the image exporter."""
        self._renderer = renderer or ImageRenderer()
    
    def export_png(self, iteration_data: np.ndarray, max_iterations: int, 
                   filepath: str, settings: RenderSettings = None) -> None:
        """Export fractal as PNG image.
        
        Args:
            iteration_data: 2D NumPy array of iteration counts
            max_iterations: Maximum iteration count
            filepath: Path to save the PNG file
            settings: Render settings to apply
        """
        image = self._renderer.render_to_image(iteration_data, max_iterations, settings)
        image.save(filepath, 'PNG', optimize=True)
    
    def export_jpeg(self, iteration_data: np.ndarray, max_iterations: int,
                    filepath: str, quality: int = 95, settings: RenderSettings = None) -> None:
        """Export fractal as JPEG image.
        
        Args:
            iteration_data: 2D NumPy array of iteration counts
            max_iterations: Maximum iteration count
            filepath: Path to save the JPEG file
            quality: JPEG quality (1-100)
            settings: Render settings to apply
        """
        if not 1 <= quality <= 100:
            raise ValueError(f"JPEG quality must be between 1 and 100, got {quality}")
        
        image = self._renderer.render_to_image(iteration_data, max_iterations, settings)
        image.save(filepath, 'JPEG', quality=quality, optimize=True)
    
    def export_high_resolution(self, iteration_data: np.ndarray, max_iterations: int,
                             filepath: str, scale_factor: int = 2, 
                             settings: RenderSettings = None) -> None:
        """Export high-resolution fractal image.
        
        Args:
            iteration_data: 2D NumPy array of iteration counts
            max_iterations: Maximum iteration count
            filepath: Path to save the image file
            scale_factor: Resolution scaling factor
            settings: Render settings to apply
        """
        hr_renderer = HighResolutionRenderer(self._renderer._color_mapper)
        image = hr_renderer.render_high_resolution(
            iteration_data, max_iterations, scale_factor, settings
        )
        
        # Determine format from file extension
        if filepath.lower().endswith('.png'):
            image.save(filepath, 'PNG', optimize=True)
        elif filepath.lower().endswith(('.jpg', '.jpeg')):
            image.save(filepath, 'JPEG', quality=95, optimize=True)
        else:
            # Default to PNG
            image.save(filepath, 'PNG', optimize=True)


class RenderingEngine:
    """Main rendering engine that coordinates all rendering operations."""
    
    def __init__(self):
        """Initialize the rendering engine."""
        self._renderer = ImageRenderer()
        self._exporter = ImageExporter(self._renderer)
        self._hr_renderer = HighResolutionRenderer()
    
    def set_color_mapper(self, color_mapper: ColorMapper) -> None:
        """Set the color mapper for all renderers."""
        self._renderer.set_color_mapper(color_mapper)
        self._hr_renderer = HighResolutionRenderer(color_mapper)
        self._exporter = ImageExporter(self._renderer)
    
    def render_preview(self, iteration_data: np.ndarray, max_iterations: int,
                      settings: RenderSettings = None) -> Image.Image:
        """Render a preview image for display."""
        return self._renderer.render_to_image(iteration_data, max_iterations, settings)
    
    def export_image(self, iteration_data: np.ndarray, max_iterations: int,
                    filepath: str, high_resolution: bool = False,
                    scale_factor: int = 2, quality: int = 95,
                    settings: RenderSettings = None) -> None:
        """Export fractal image to file.
        
        Args:
            iteration_data: 2D NumPy array of iteration counts
            max_iterations: Maximum iteration count
            filepath: Path to save the image
            high_resolution: Whether to render at high resolution
            scale_factor: Resolution scaling factor (if high_resolution=True)
            quality: JPEG quality (if saving as JPEG)
            settings: Render settings to apply
        """
        if high_resolution:
            self._exporter.export_high_resolution(
                iteration_data, max_iterations, filepath, scale_factor, settings
            )
        elif filepath.lower().endswith(('.jpg', '.jpeg')):
            self._exporter.export_jpeg(
                iteration_data, max_iterations, filepath, quality, settings
            )
        else:
            self._exporter.export_png(
                iteration_data, max_iterations, filepath, settings
            )
    
    def get_render_settings(self) -> RenderSettings:
        """Get default render settings."""
        return RenderSettings()
    
    def create_render_settings(self, anti_aliasing: bool = True, brightness: float = 1.0,
                             contrast: float = 1.0, gamma: float = 1.0) -> RenderSettings:
        """Create custom render settings."""
        return RenderSettings(
            anti_aliasing=anti_aliasing,
            brightness=brightness,
            contrast=contrast,
            gamma=gamma
        )