"""
Tests for the image rendering engine.
"""

import unittest
import numpy as np
import tempfile
import os
from PIL import Image

from fractal_editor.services.image_renderer import (
    RenderSettings, ImageRenderer, HighResolutionRenderer,
    ImageExporter, RenderingEngine
)
from fractal_editor.services.color_system import (
    GradientColorMapper, PresetPalettes
)


class TestRenderSettings(unittest.TestCase):
    """Tests for RenderSettings class."""
    
    def test_valid_render_settings(self):
        """Test creating valid render settings."""
        settings = RenderSettings(
            anti_aliasing=True,
            brightness=1.5,
            contrast=1.2,
            gamma=0.8
        )
        
        self.assertTrue(settings.anti_aliasing)
        self.assertEqual(settings.brightness, 1.5)
        self.assertEqual(settings.contrast, 1.2)
        self.assertEqual(settings.gamma, 0.8)
    
    def test_default_render_settings(self):
        """Test default render settings."""
        settings = RenderSettings()
        
        self.assertTrue(settings.anti_aliasing)
        self.assertEqual(settings.brightness, 1.0)
        self.assertEqual(settings.contrast, 1.0)
        self.assertEqual(settings.gamma, 1.0)
    
    def test_invalid_brightness_raises_error(self):
        """Test that invalid brightness values raise errors."""
        with self.assertRaises(ValueError):
            RenderSettings(brightness=-0.1)
        
        with self.assertRaises(ValueError):
            RenderSettings(brightness=2.1)
    
    def test_invalid_contrast_raises_error(self):
        """Test that invalid contrast values raise errors."""
        with self.assertRaises(ValueError):
            RenderSettings(contrast=-0.1)
        
        with self.assertRaises(ValueError):
            RenderSettings(contrast=2.1)
    
    def test_invalid_gamma_raises_error(self):
        """Test that invalid gamma values raise errors."""
        with self.assertRaises(ValueError):
            RenderSettings(gamma=0.05)
        
        with self.assertRaises(ValueError):
            RenderSettings(gamma=3.1)


class TestImageRenderer(unittest.TestCase):
    """Tests for ImageRenderer class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a simple test iteration data
        self.iteration_data = np.array([
            [0, 10, 20, 30],
            [40, 50, 60, 70],
            [80, 90, 100, 100]
        ])
        self.max_iterations = 100
        
        # Create a color mapper
        color_mapper = GradientColorMapper()
        color_mapper.set_palette(PresetPalettes.get_grayscale())
        self.renderer = ImageRenderer(color_mapper)
    
    def test_render_to_array(self):
        """Test rendering iteration data to RGB array."""
        rgb_array = self.renderer.render_to_array(self.iteration_data, self.max_iterations)
        
        # Check array shape
        expected_shape = (3, 4, 3)  # height, width, channels
        self.assertEqual(rgb_array.shape, expected_shape)
        
        # Check data type
        self.assertEqual(rgb_array.dtype, np.uint8)
        
        # Check that values are in valid RGB range
        self.assertTrue(np.all(rgb_array >= 0))
        self.assertTrue(np.all(rgb_array <= 255))
    
    def test_render_to_image(self):
        """Test rendering iteration data to PIL Image."""
        image = self.renderer.render_to_image(self.iteration_data, self.max_iterations)
        
        # Check that we get a PIL Image
        self.assertIsInstance(image, Image.Image)
        
        # Check image size
        self.assertEqual(image.size, (4, 3))  # width, height
        
        # Check image mode
        self.assertEqual(image.mode, 'RGB')
    
    def test_render_with_settings(self):
        """Test rendering with custom settings."""
        settings = RenderSettings(
            anti_aliasing=False,
            brightness=1.5,
            contrast=1.2,
            gamma=0.8
        )
        
        image = self.renderer.render_to_image(
            self.iteration_data, self.max_iterations, settings
        )
        
        self.assertIsInstance(image, Image.Image)
        self.assertEqual(image.size, (4, 3))
    
    def test_default_color_mapper(self):
        """Test renderer with default color mapper."""
        renderer = ImageRenderer()  # No color mapper provided
        image = renderer.render_to_image(self.iteration_data, self.max_iterations)
        
        self.assertIsInstance(image, Image.Image)


class TestHighResolutionRenderer(unittest.TestCase):
    """Tests for HighResolutionRenderer class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.iteration_data = np.array([
            [0, 50, 100],
            [25, 75, 100]
        ])
        self.max_iterations = 100
        self.hr_renderer = HighResolutionRenderer()
    
    def test_high_resolution_rendering(self):
        """Test high-resolution rendering."""
        scale_factor = 2
        image = self.hr_renderer.render_high_resolution(
            self.iteration_data, self.max_iterations, scale_factor
        )
        
        # Check that image is scaled up
        original_size = (3, 2)  # width, height
        expected_size = (6, 4)  # 2x scale
        
        self.assertEqual(image.size, expected_size)
        self.assertIsInstance(image, Image.Image)


class TestImageExporter(unittest.TestCase):
    """Tests for ImageExporter class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.iteration_data = np.array([
            [0, 25, 50],
            [75, 100, 100]
        ])
        self.max_iterations = 100
        self.exporter = ImageExporter()
        
        # Create temporary directory for test files
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up test files."""
        # Remove all files in temp directory
        for filename in os.listdir(self.temp_dir):
            os.remove(os.path.join(self.temp_dir, filename))
        os.rmdir(self.temp_dir)
    
    def test_export_png(self):
        """Test PNG export."""
        filepath = os.path.join(self.temp_dir, "test.png")
        
        self.exporter.export_png(self.iteration_data, self.max_iterations, filepath)
        
        # Check that file was created
        self.assertTrue(os.path.exists(filepath))
        
        # Check that it's a valid PNG
        with Image.open(filepath) as img:
            self.assertEqual(img.format, 'PNG')
            self.assertEqual(img.size, (3, 2))
    
    def test_export_jpeg(self):
        """Test JPEG export."""
        filepath = os.path.join(self.temp_dir, "test.jpg")
        
        self.exporter.export_jpeg(
            self.iteration_data, self.max_iterations, filepath, quality=80
        )
        
        # Check that file was created
        self.assertTrue(os.path.exists(filepath))
        
        # Check that it's a valid JPEG
        with Image.open(filepath) as img:
            self.assertEqual(img.format, 'JPEG')
            self.assertEqual(img.size, (3, 2))
    
    def test_invalid_jpeg_quality_raises_error(self):
        """Test that invalid JPEG quality raises error."""
        filepath = os.path.join(self.temp_dir, "test.jpg")
        
        with self.assertRaises(ValueError):
            self.exporter.export_jpeg(
                self.iteration_data, self.max_iterations, filepath, quality=0
            )
        
        with self.assertRaises(ValueError):
            self.exporter.export_jpeg(
                self.iteration_data, self.max_iterations, filepath, quality=101
            )
    
    def test_export_high_resolution(self):
        """Test high-resolution export."""
        filepath = os.path.join(self.temp_dir, "test_hr.png")
        
        self.exporter.export_high_resolution(
            self.iteration_data, self.max_iterations, filepath, scale_factor=2
        )
        
        # Check that file was created
        self.assertTrue(os.path.exists(filepath))
        
        # Check that image is high resolution
        with Image.open(filepath) as img:
            self.assertEqual(img.size, (6, 4))  # 2x scale


class TestRenderingEngine(unittest.TestCase):
    """Tests for RenderingEngine class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.iteration_data = np.array([
            [0, 33, 66, 100],
            [25, 50, 75, 100]
        ])
        self.max_iterations = 100
        self.engine = RenderingEngine()
        
        # Create temporary directory for test files
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up test files."""
        # Remove all files in temp directory
        for filename in os.listdir(self.temp_dir):
            os.remove(os.path.join(self.temp_dir, filename))
        os.rmdir(self.temp_dir)
    
    def test_render_preview(self):
        """Test preview rendering."""
        image = self.engine.render_preview(self.iteration_data, self.max_iterations)
        
        self.assertIsInstance(image, Image.Image)
        self.assertEqual(image.size, (4, 2))
    
    def test_export_image_png(self):
        """Test image export as PNG."""
        filepath = os.path.join(self.temp_dir, "test.png")
        
        self.engine.export_image(self.iteration_data, self.max_iterations, filepath)
        
        self.assertTrue(os.path.exists(filepath))
        
        with Image.open(filepath) as img:
            self.assertEqual(img.format, 'PNG')
    
    def test_export_image_jpeg(self):
        """Test image export as JPEG."""
        filepath = os.path.join(self.temp_dir, "test.jpg")
        
        self.engine.export_image(
            self.iteration_data, self.max_iterations, filepath, quality=90
        )
        
        self.assertTrue(os.path.exists(filepath))
        
        with Image.open(filepath) as img:
            self.assertEqual(img.format, 'JPEG')
    
    def test_export_high_resolution_image(self):
        """Test high-resolution image export."""
        filepath = os.path.join(self.temp_dir, "test_hr.png")
        
        self.engine.export_image(
            self.iteration_data, self.max_iterations, filepath,
            high_resolution=True, scale_factor=3
        )
        
        self.assertTrue(os.path.exists(filepath))
        
        with Image.open(filepath) as img:
            self.assertEqual(img.size, (12, 6))  # 3x scale
    
    def test_set_color_mapper(self):
        """Test setting color mapper."""
        color_mapper = GradientColorMapper()
        color_mapper.set_palette(PresetPalettes.get_fire())
        
        self.engine.set_color_mapper(color_mapper)
        
        # Test that the color mapper is used
        image = self.engine.render_preview(self.iteration_data, self.max_iterations)
        self.assertIsInstance(image, Image.Image)
    
    def test_create_render_settings(self):
        """Test creating custom render settings."""
        settings = self.engine.create_render_settings(
            anti_aliasing=False,
            brightness=1.3,
            contrast=1.1,
            gamma=0.9
        )
        
        self.assertFalse(settings.anti_aliasing)
        self.assertEqual(settings.brightness, 1.3)
        self.assertEqual(settings.contrast, 1.1)
        self.assertEqual(settings.gamma, 0.9)


class TestImageProcessing(unittest.TestCase):
    """Tests for image processing functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a simple gradient for testing
        self.iteration_data = np.array([
            [0, 25, 50, 75, 100],
            [20, 40, 60, 80, 100],
            [10, 30, 50, 70, 90]
        ])
        self.max_iterations = 100
        self.renderer = ImageRenderer()
    
    def test_brightness_adjustment(self):
        """Test brightness adjustment."""
        # Render with different brightness settings
        normal_image = self.renderer.render_to_image(
            self.iteration_data, self.max_iterations,
            RenderSettings(brightness=1.0, anti_aliasing=False)
        )
        
        bright_image = self.renderer.render_to_image(
            self.iteration_data, self.max_iterations,
            RenderSettings(brightness=1.5, anti_aliasing=False)
        )
        
        # Convert to arrays for comparison
        normal_array = np.array(normal_image)
        bright_array = np.array(bright_image)
        
        # Bright image should generally have higher values
        # (except for pixels that are already at maximum)
        self.assertGreater(np.mean(bright_array), np.mean(normal_array))
    
    def test_contrast_adjustment(self):
        """Test contrast adjustment."""
        # Render with different contrast settings
        normal_image = self.renderer.render_to_image(
            self.iteration_data, self.max_iterations,
            RenderSettings(contrast=1.0, anti_aliasing=False)
        )
        
        high_contrast_image = self.renderer.render_to_image(
            self.iteration_data, self.max_iterations,
            RenderSettings(contrast=1.5, anti_aliasing=False)
        )
        
        # Both should be valid images
        self.assertIsInstance(normal_image, Image.Image)
        self.assertIsInstance(high_contrast_image, Image.Image)
    
    def test_gamma_correction(self):
        """Test gamma correction."""
        # Render with different gamma settings
        normal_image = self.renderer.render_to_image(
            self.iteration_data, self.max_iterations,
            RenderSettings(gamma=1.0, anti_aliasing=False)
        )
        
        gamma_image = self.renderer.render_to_image(
            self.iteration_data, self.max_iterations,
            RenderSettings(gamma=0.5, anti_aliasing=False)
        )
        
        # Both should be valid images
        self.assertIsInstance(normal_image, Image.Image)
        self.assertIsInstance(gamma_image, Image.Image)
        
        # Images should be different (gamma correction applied)
        normal_array = np.array(normal_image)
        gamma_array = np.array(gamma_image)
        
        # They should not be identical
        self.assertFalse(np.array_equal(normal_array, gamma_array))


if __name__ == '__main__':
    unittest.main()