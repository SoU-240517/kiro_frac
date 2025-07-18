"""
Integration test to verify color system and image renderer work together.
"""

import unittest
import numpy as np
import tempfile
import os
from PIL import Image

from fractal_editor.services.color_system import (
    ColorSystemManager, PresetPalettes, GradientColorMapper
)
from fractal_editor.services.image_renderer import (
    RenderingEngine, RenderSettings
)


class TestColorSystemImageRendererIntegration(unittest.TestCase):
    """Integration tests for color system and image renderer."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create sample fractal iteration data
        self.iteration_data = np.array([
            [0, 10, 20, 30, 40],
            [50, 60, 70, 80, 90],
            [100, 100, 100, 100, 100],  # Points that didn't escape
            [5, 15, 25, 35, 45],
            [55, 65, 75, 85, 95]
        ])
        self.max_iterations = 100
        
        # Set up color system and rendering engine
        self.color_manager = ColorSystemManager()
        self.rendering_engine = RenderingEngine()
        
        # Create temporary directory for test files
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up test files."""
        for filename in os.listdir(self.temp_dir):
            os.remove(os.path.join(self.temp_dir, filename))
        os.rmdir(self.temp_dir)
    
    def test_render_with_different_palettes(self):
        """Test rendering with different color palettes."""
        palette_names = ["Rainbow", "Fire", "Ocean", "Grayscale"]
        
        for palette_name in palette_names:
            with self.subTest(palette=palette_name):
                # Set the palette
                self.color_manager.set_current_palette_by_name(palette_name)
                color_mapper = self.color_manager.get_color_mapper()
                self.rendering_engine.set_color_mapper(color_mapper)
                
                # Render the image
                image = self.rendering_engine.render_preview(
                    self.iteration_data, self.max_iterations
                )
                
                # Verify the image was created correctly
                self.assertIsInstance(image, Image.Image)
                self.assertEqual(image.size, (5, 5))  # width, height
                self.assertEqual(image.mode, 'RGB')
    
    def test_render_with_different_interpolation_modes(self):
        """Test rendering with different interpolation modes."""
        from fractal_editor.services.color_system import InterpolationMode
        
        # Test each interpolation mode
        modes = [InterpolationMode.LINEAR, InterpolationMode.CUBIC, InterpolationMode.HSV]
        
        for mode in modes:
            with self.subTest(mode=mode.value):
                # Create a palette with the specific interpolation mode
                palette = PresetPalettes.get_rainbow()
                palette.interpolation_mode = mode
                
                # Set up the color mapper and rendering engine
                color_mapper = GradientColorMapper(palette)
                self.rendering_engine.set_color_mapper(color_mapper)
                
                # Render the image
                image = self.rendering_engine.render_preview(
                    self.iteration_data, self.max_iterations
                )
                
                # Verify the image was created
                self.assertIsInstance(image, Image.Image)
                self.assertEqual(image.size, (5, 5))
    
    def test_export_with_different_settings(self):
        """Test exporting images with different render settings."""
        # Set up a colorful palette
        self.color_manager.set_current_palette_by_name("Fire")
        color_mapper = self.color_manager.get_color_mapper()
        self.rendering_engine.set_color_mapper(color_mapper)
        
        # Test different render settings
        settings_list = [
            RenderSettings(anti_aliasing=True, brightness=1.0, contrast=1.0),
            RenderSettings(anti_aliasing=False, brightness=1.5, contrast=1.2),
            RenderSettings(anti_aliasing=True, brightness=0.8, contrast=0.9, gamma=1.2)
        ]
        
        for i, settings in enumerate(settings_list):
            with self.subTest(settings_index=i):
                filepath = os.path.join(self.temp_dir, f"test_{i}.png")
                
                # Export the image
                self.rendering_engine.export_image(
                    self.iteration_data, self.max_iterations, filepath, settings=settings
                )
                
                # Verify the file was created
                self.assertTrue(os.path.exists(filepath))
                
                # Verify it's a valid image
                with Image.open(filepath) as img:
                    self.assertEqual(img.format, 'PNG')
                    self.assertEqual(img.size, (5, 5))
    
    def test_high_resolution_export_with_custom_palette(self):
        """Test high-resolution export with custom palette."""
        # Create a custom palette
        custom_palette = self.color_manager.create_custom_palette(
            "Custom Test",
            [
                (0.0, (255, 0, 0)),    # Red
                (0.5, (255, 255, 0)),  # Yellow
                (1.0, (0, 255, 0))     # Green
            ]
        )
        
        # Set up the rendering engine with the custom palette
        color_mapper = GradientColorMapper(custom_palette)
        self.rendering_engine.set_color_mapper(color_mapper)
        
        # Export high-resolution image
        filepath = os.path.join(self.temp_dir, "test_hr_custom.png")
        self.rendering_engine.export_image(
            self.iteration_data, self.max_iterations, filepath,
            high_resolution=True, scale_factor=2
        )
        
        # Verify the file was created with correct size
        self.assertTrue(os.path.exists(filepath))
        
        with Image.open(filepath) as img:
            self.assertEqual(img.format, 'PNG')
            self.assertEqual(img.size, (10, 10))  # 2x scale
    
    def test_color_mapping_consistency(self):
        """Test that color mapping is consistent between direct mapping and rendering."""
        # Set up a simple grayscale palette for predictable results
        self.color_manager.set_current_palette_by_name("Grayscale")
        color_mapper = self.color_manager.get_color_mapper()
        
        # Test direct color mapping
        test_iteration = 50
        direct_color = color_mapper.map_iteration_to_color(test_iteration, self.max_iterations)
        
        # Create a simple 1x1 iteration array with the same value
        single_iteration = np.array([[test_iteration]])
        
        # Render using the image renderer
        self.rendering_engine.set_color_mapper(color_mapper)
        image = self.rendering_engine.render_preview(single_iteration, self.max_iterations)
        
        # Get the color from the rendered image
        rendered_color = image.getpixel((0, 0))
        
        # They should be the same (or very close due to processing)
        self.assertEqual(direct_color, rendered_color)
    
    def test_max_iteration_pixels_with_no_antialiasing(self):
        """Test that pixels with max iterations are rendered as black when anti-aliasing is disabled."""
        # Create iteration data with some max iteration values
        max_iter_data = np.array([
            [0, 50, 100],
            [25, 100, 75],
            [100, 100, 100]
        ])
        
        # Set up rendering with anti-aliasing disabled to avoid color bleeding
        self.color_manager.set_current_palette_by_name("Rainbow")
        color_mapper = self.color_manager.get_color_mapper()
        self.rendering_engine.set_color_mapper(color_mapper)
        
        # Render with anti-aliasing disabled
        settings = RenderSettings(anti_aliasing=False)
        image = self.rendering_engine.render_preview(max_iter_data, 100, settings)
        
        # Check that all max iteration pixels are black
        # Pixels at (0,2), (1,1), (2,0), (2,1), (2,2) should all be black
        max_iter_pixels = [(2, 0), (1, 1), (0, 2), (1, 2), (2, 2)]
        
        for x, y in max_iter_pixels:
            pixel_color = image.getpixel((x, y))
            self.assertEqual(pixel_color, (0, 0, 0), 
                           f"Max iteration pixel at ({x}, {y}) should be black but got {pixel_color}")


if __name__ == '__main__':
    unittest.main()