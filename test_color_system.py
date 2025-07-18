"""
Tests for the color system module.
"""

import unittest
import math
from fractal_editor.services.color_system import (
    ColorStop, ColorPalette, InterpolationMode, GradientColorMapper,
    PresetPalettes, ColorSystemManager
)


class TestColorStop(unittest.TestCase):
    """Tests for ColorStop class."""
    
    def test_valid_color_stop_creation(self):
        """Test creating a valid color stop."""
        stop = ColorStop(0.5, (128, 64, 192))
        self.assertEqual(stop.position, 0.5)
        self.assertEqual(stop.color, (128, 64, 192))
    
    def test_invalid_position_raises_error(self):
        """Test that invalid positions raise ValueError."""
        with self.assertRaises(ValueError):
            ColorStop(-0.1, (255, 0, 0))
        
        with self.assertRaises(ValueError):
            ColorStop(1.1, (255, 0, 0))
    
    def test_invalid_color_values_raise_error(self):
        """Test that invalid color values raise ValueError."""
        with self.assertRaises(ValueError):
            ColorStop(0.5, (-1, 0, 0))
        
        with self.assertRaises(ValueError):
            ColorStop(0.5, (256, 0, 0))


class TestColorPalette(unittest.TestCase):
    """Tests for ColorPalette class."""
    
    def test_valid_palette_creation(self):
        """Test creating a valid color palette."""
        stops = [
            ColorStop(0.0, (0, 0, 0)),
            ColorStop(0.5, (128, 128, 128)),
            ColorStop(1.0, (255, 255, 255))
        ]
        palette = ColorPalette("Test", stops)
        self.assertEqual(palette.name, "Test")
        self.assertEqual(len(palette.color_stops), 3)
        self.assertEqual(palette.interpolation_mode, InterpolationMode.LINEAR)
    
    def test_palette_sorts_color_stops(self):
        """Test that color stops are sorted by position."""
        stops = [
            ColorStop(1.0, (255, 255, 255)),
            ColorStop(0.0, (0, 0, 0)),
            ColorStop(0.5, (128, 128, 128))
        ]
        palette = ColorPalette("Test", stops)
        positions = [stop.position for stop in palette.color_stops]
        self.assertEqual(positions, [0.0, 0.5, 1.0])
    
    def test_palette_requires_minimum_stops(self):
        """Test that palette requires at least 2 color stops."""
        with self.assertRaises(ValueError):
            ColorPalette("Test", [ColorStop(0.0, (0, 0, 0))])
    
    def test_palette_requires_start_and_end_stops(self):
        """Test that palette requires stops at 0.0 and 1.0."""
        with self.assertRaises(ValueError):
            ColorPalette("Test", [
                ColorStop(0.1, (0, 0, 0)),
                ColorStop(1.0, (255, 255, 255))
            ])
        
        with self.assertRaises(ValueError):
            ColorPalette("Test", [
                ColorStop(0.0, (0, 0, 0)),
                ColorStop(0.9, (255, 255, 255))
            ])


class TestGradientColorMapper(unittest.TestCase):
    """Tests for GradientColorMapper class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.simple_palette = ColorPalette(
            "Simple",
            [
                ColorStop(0.0, (0, 0, 0)),      # Black
                ColorStop(1.0, (255, 255, 255)) # White
            ]
        )
        self.mapper = GradientColorMapper(self.simple_palette)
    
    def test_map_iteration_to_color_basic(self):
        """Test basic iteration to color mapping."""
        # Test start color
        color = self.mapper.map_iteration_to_color(0, 100)
        self.assertEqual(color, (0, 0, 0))
        
        # Test middle color
        color = self.mapper.map_iteration_to_color(50, 100)
        self.assertEqual(color, (127, 127, 127))  # Approximately middle gray
        
        # Test max iteration (should be black for non-escaped points)
        color = self.mapper.map_iteration_to_color(100, 100)
        self.assertEqual(color, (0, 0, 0))
    
    def test_linear_interpolation(self):
        """Test linear interpolation between colors."""
        # Test with a red-to-blue gradient
        palette = ColorPalette(
            "RedBlue",
            [
                ColorStop(0.0, (255, 0, 0)),  # Red
                ColorStop(1.0, (0, 0, 255))   # Blue
            ]
        )
        mapper = GradientColorMapper(palette)
        
        # Test quarter point
        color = mapper.map_iteration_to_color(25, 100)
        expected_r = int(255 * 0.75)  # 75% red
        expected_b = int(255 * 0.25)  # 25% blue
        self.assertEqual(color, (expected_r, 0, expected_b))
    
    def test_multiple_color_stops(self):
        """Test interpolation with multiple color stops."""
        palette = ColorPalette(
            "RGB",
            [
                ColorStop(0.0, (255, 0, 0)),   # Red
                ColorStop(0.5, (0, 255, 0)),   # Green
                ColorStop(1.0, (0, 0, 255))    # Blue
            ]
        )
        mapper = GradientColorMapper(palette)
        
        # Test first half (red to green)
        color = mapper.map_iteration_to_color(25, 100)  # 25% = halfway between 0% and 50%
        self.assertEqual(color, (127, 127, 0))  # Half red, half green
        
        # Test second half (green to blue)
        color = mapper.map_iteration_to_color(75, 100)  # 75% = halfway between 50% and 100%
        self.assertEqual(color, (0, 127, 127))  # Half green, half blue
    
    def test_cubic_interpolation(self):
        """Test cubic interpolation mode."""
        palette = ColorPalette(
            "Test",
            [
                ColorStop(0.0, (0, 0, 0)),
                ColorStop(1.0, (255, 255, 255))
            ],
            InterpolationMode.CUBIC
        )
        mapper = GradientColorMapper(palette)
        
        # Cubic interpolation should produce different results than linear
        linear_color = self.mapper.map_iteration_to_color(25, 100)
        cubic_color = mapper.map_iteration_to_color(25, 100)
        
        # They should be different (cubic is smoother)
        self.assertNotEqual(linear_color, cubic_color)
    
    def test_no_palette_raises_error(self):
        """Test that mapping without a palette raises an error."""
        mapper = GradientColorMapper()
        with self.assertRaises(ValueError):
            mapper.map_iteration_to_color(50, 100)


class TestPresetPalettes(unittest.TestCase):
    """Tests for preset palettes."""
    
    def test_rainbow_palette(self):
        """Test rainbow palette creation."""
        palette = PresetPalettes.get_rainbow()
        self.assertEqual(palette.name, "Rainbow")
        self.assertEqual(len(palette.color_stops), 7)
        self.assertEqual(palette.interpolation_mode, InterpolationMode.HSV)
        
        # Check first and last colors
        self.assertEqual(palette.color_stops[0].color, (255, 0, 0))  # Red
        self.assertEqual(palette.color_stops[-1].color, (148, 0, 211))  # Violet
    
    def test_fire_palette(self):
        """Test fire palette creation."""
        palette = PresetPalettes.get_fire()
        self.assertEqual(palette.name, "Fire")
        self.assertEqual(len(palette.color_stops), 5)
        self.assertEqual(palette.interpolation_mode, InterpolationMode.LINEAR)
    
    def test_grayscale_palette(self):
        """Test grayscale palette creation."""
        palette = PresetPalettes.get_grayscale()
        self.assertEqual(palette.name, "Grayscale")
        self.assertEqual(len(palette.color_stops), 2)
        self.assertEqual(palette.color_stops[0].color, (0, 0, 0))
        self.assertEqual(palette.color_stops[1].color, (255, 255, 255))
    
    def test_all_presets_available(self):
        """Test that all presets are available."""
        presets = PresetPalettes.get_all_presets()
        expected_names = ["Rainbow", "Fire", "Ocean", "Grayscale", "Sunset", "Electric"]
        
        self.assertEqual(set(presets.keys()), set(expected_names))
        
        # Verify each preset is a valid ColorPalette
        for name, palette in presets.items():
            self.assertIsInstance(palette, ColorPalette)
            self.assertEqual(palette.name, name)


class TestColorSystemManager(unittest.TestCase):
    """Tests for ColorSystemManager class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.manager = ColorSystemManager()
    
    def test_initial_state(self):
        """Test initial state of color system manager."""
        self.assertIsNotNone(self.manager.get_current_palette())
        self.assertEqual(self.manager.get_current_palette().name, "Rainbow")
        self.assertIsNotNone(self.manager.get_color_mapper())
    
    def test_get_preset_names(self):
        """Test getting preset palette names."""
        names = self.manager.get_preset_names()
        self.assertIn("Rainbow", names)
        self.assertIn("Fire", names)
        self.assertIn("Ocean", names)
        self.assertIn("Grayscale", names)
    
    def test_set_palette_by_name(self):
        """Test setting palette by name."""
        self.manager.set_current_palette_by_name("Fire")
        self.assertEqual(self.manager.get_current_palette().name, "Fire")
    
    def test_invalid_preset_name_raises_error(self):
        """Test that invalid preset name raises error."""
        with self.assertRaises(ValueError):
            self.manager.get_preset_palette("NonExistent")
    
    def test_create_custom_palette(self):
        """Test creating a custom palette."""
        color_stops = [
            (0.0, (255, 0, 0)),
            (0.5, (0, 255, 0)),
            (1.0, (0, 0, 255))
        ]
        
        palette = self.manager.create_custom_palette(
            "Custom", color_stops, InterpolationMode.HSV
        )
        
        self.assertEqual(palette.name, "Custom")
        self.assertEqual(len(palette.color_stops), 3)
        self.assertEqual(palette.interpolation_mode, InterpolationMode.HSV)


class TestColorInterpolation(unittest.TestCase):
    """Tests for different color interpolation modes."""
    
    def test_hsv_interpolation_hue_wraparound(self):
        """Test HSV interpolation handles hue wraparound correctly."""
        # Create a palette that goes from red (hue=0) to magenta (hue=300)
        # This should wrap around through purple rather than going through yellow
        palette = ColorPalette(
            "HueWrap",
            [
                ColorStop(0.0, (255, 0, 0)),    # Red (hue=0)
                ColorStop(1.0, (255, 0, 255))   # Magenta (hue=300)
            ],
            InterpolationMode.HSV
        )
        
        mapper = GradientColorMapper(palette)
        
        # The middle color should be more purple-ish, not yellow-ish
        middle_color = mapper.map_iteration_to_color(50, 100)
        r, g, b = middle_color
        
        # In HSV interpolation with wraparound, we should get a purple-ish color
        # The green component should be relatively low
        self.assertLess(g, max(r, b), "HSV interpolation should produce purple, not yellow")


if __name__ == '__main__':
    unittest.main()