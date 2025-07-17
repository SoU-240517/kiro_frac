"""
Unit tests for the JuliaGenerator class.

These tests verify the mathematical accuracy and correctness of the
Julia set calculation implementation.
"""

import unittest
import numpy as np
from fractal_editor.generators.julia import JuliaGenerator
from fractal_editor.models.data_models import (
    FractalParameters, ComplexRegion, ComplexNumber
)


class TestJuliaGenerator(unittest.TestCase):
    """Test cases for JuliaGenerator class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.generator = JuliaGenerator()
        
        # Standard test parameters
        self.standard_region = ComplexRegion(
            top_left=ComplexNumber(-2.0, 2.0),
            bottom_right=ComplexNumber(2.0, -2.0)
        )
        
        self.standard_parameters = FractalParameters(
            region=self.standard_region,
            max_iterations=100,
            image_size=(100, 100),
            custom_parameters={
                'c_real': -0.7,
                'c_imag': 0.27015
            }
        )
    
    def test_generator_properties(self):
        """Test basic generator properties."""
        self.assertEqual(self.generator.name, "Julia Set")
        self.assertIn("Julia", self.generator.description)
        self.assertIn("z_{n+1} = z_n^2 + c", self.generator.description)
    
    def test_parameter_definitions(self):
        """Test parameter definitions."""
        param_defs = self.generator.get_parameter_definitions()
        self.assertEqual(len(param_defs), 3)
        
        # Check parameter names
        param_names = [pd.name for pd in param_defs]
        self.assertIn("c_real", param_names)
        self.assertIn("c_imag", param_names)
        self.assertIn("escape_radius", param_names)
        
        # Check c_real parameter
        c_real_def = next(pd for pd in param_defs if pd.name == "c_real")
        self.assertEqual(c_real_def.parameter_type, "float")
        self.assertEqual(c_real_def.default_value, -0.7)
        self.assertEqual(c_real_def.min_value, -2.0)
        self.assertEqual(c_real_def.max_value, 2.0)
        
        # Check c_imag parameter
        c_imag_def = next(pd for pd in param_defs if pd.name == "c_imag")
        self.assertEqual(c_imag_def.parameter_type, "float")
        self.assertEqual(c_imag_def.default_value, 0.27015)
        self.assertEqual(c_imag_def.min_value, -2.0)
        self.assertEqual(c_imag_def.max_value, 2.0)
    
    def test_calculate_returns_valid_result(self):
        """Test that calculate returns a valid FractalResult."""
        result = self.generator.calculate(self.standard_parameters)
        
        # Check result structure
        self.assertIsNotNone(result)
        self.assertEqual(result.iteration_data.shape, (100, 100))
        self.assertEqual(result.region, self.standard_region)
        self.assertGreater(result.calculation_time, 0)
        self.assertEqual(result.parameters, self.standard_parameters)
        
        # Check metadata
        self.assertEqual(result.metadata['generator'], "Julia Set")
        self.assertEqual(result.metadata['c_real'], -0.7)
        self.assertEqual(result.metadata['c_imag'], 0.27015)
        self.assertEqual(result.metadata['escape_radius'], 2.0)
        self.assertEqual(result.metadata['algorithm'], 'standard_julia')
    
    def test_different_c_parameters(self):
        """Test calculation with different c parameters."""
        # Test with c = 0 (should produce a filled circle-like shape)
        params_zero = FractalParameters(
            region=self.standard_region,
            max_iterations=100,
            image_size=(50, 50),
            custom_parameters={
                'c_real': 0.0,
                'c_imag': 0.0
            }
        )
        
        result_zero = self.generator.calculate(params_zero)
        self.assertIsNotNone(result_zero)
        self.assertEqual(result_zero.metadata['c_real'], 0.0)
        self.assertEqual(result_zero.metadata['c_imag'], 0.0)
        
        # Test with different c value
        params_different = FractalParameters(
            region=self.standard_region,
            max_iterations=100,
            image_size=(50, 50),
            custom_parameters={
                'c_real': -0.8,
                'c_imag': 0.156
            }
        )
        
        result_different = self.generator.calculate(params_different)
        
        # Results should be different
        self.assertFalse(np.array_equal(result_zero.iteration_data, result_different.iteration_data))
    
    def test_julia_set_with_c_zero(self):
        """Test Julia set with c = 0 (should behave like z^2)."""
        # For c = 0, the Julia set is just the unit circle
        # Points inside |z| < 1 should not escape, points outside should escape quickly
        
        params_c_zero = FractalParameters(
            region=ComplexRegion(
                top_left=ComplexNumber(-1.5, 1.5),
                bottom_right=ComplexNumber(1.5, -1.5)
            ),
            max_iterations=50,
            image_size=(10, 10),
            custom_parameters={
                'c_real': 0.0,
                'c_imag': 0.0
            }
        )
        
        result = self.generator.calculate(params_c_zero)
        
        # Center point (0,0) should reach max iterations
        center_iterations = result.iteration_data[5, 5]  # Center of 10x10 grid
        self.assertEqual(center_iterations, 50)
        
        # Corner points (far from origin) should escape quickly
        corner_iterations = result.iteration_data[0, 0]  # Top-left corner
        self.assertLess(corner_iterations, 10)
    
    def test_parameter_validation(self):
        """Test parameter validation."""
        # Valid parameters should pass
        self.assertTrue(self.generator.validate_parameters(self.standard_parameters))
        
        # Invalid c_real should fail
        invalid_params = FractalParameters(
            region=self.standard_region,
            max_iterations=100,
            image_size=(100, 100),
            custom_parameters={
                'c_real': "invalid",
                'c_imag': 0.27015
            }
        )
        
        self.assertFalse(self.generator.validate_parameters(invalid_params))
        
        # Invalid c_imag should fail
        invalid_params2 = FractalParameters(
            region=self.standard_region,
            max_iterations=100,
            image_size=(100, 100),
            custom_parameters={
                'c_real': -0.7,
                'c_imag': "invalid"
            }
        )
        
        self.assertFalse(self.generator.validate_parameters(invalid_params2))
        
        # Invalid escape radius should fail
        invalid_params3 = FractalParameters(
            region=self.standard_region,
            max_iterations=100,
            image_size=(100, 100),
            custom_parameters={
                'c_real': -0.7,
                'c_imag': 0.27015,
                'escape_radius': -1.0
            }
        )
        
        self.assertFalse(self.generator.validate_parameters(invalid_params3))
    
    def test_custom_escape_radius(self):
        """Test calculation with custom escape radius."""
        params_custom = FractalParameters(
            region=self.standard_region,
            max_iterations=50,
            image_size=(50, 50),
            custom_parameters={
                'c_real': -0.7,
                'c_imag': 0.27015,
                'escape_radius': 4.0
            }
        )
        
        result = self.generator.calculate(params_custom)
        
        # Should complete without error
        self.assertIsNotNone(result)
        self.assertEqual(result.metadata['escape_radius'], 4.0)
        
        # Compare with standard escape radius
        params_standard = FractalParameters(
            region=self.standard_region,
            max_iterations=50,
            image_size=(50, 50),
            custom_parameters={
                'c_real': -0.7,
                'c_imag': 0.27015,
                'escape_radius': 2.0
            }
        )
        
        result_standard = self.generator.calculate(params_standard)
        
        # Results should be different (higher escape radius should affect calculation)
        self.assertFalse(np.array_equal(result.iteration_data, result_standard.iteration_data))
    
    def test_iteration_data_bounds(self):
        """Test that iteration data is within expected bounds."""
        result = self.generator.calculate(self.standard_parameters)
        
        # All iteration counts should be between 0 and max_iterations
        self.assertTrue(np.all(result.iteration_data >= 0))
        self.assertTrue(np.all(result.iteration_data <= self.standard_parameters.max_iterations))
        
        # Should have some variety in iteration counts
        unique_counts = np.unique(result.iteration_data)
        self.assertGreater(len(unique_counts), 5)  # Should have at least some variety
    
    def test_different_image_sizes(self):
        """Test calculation with different image sizes."""
        sizes_to_test = [(10, 10), (50, 25), (100, 100)]
        
        for width, height in sizes_to_test:
            with self.subTest(size=(width, height)):
                params = FractalParameters(
                    region=self.standard_region,
                    max_iterations=50,
                    image_size=(width, height),
                    custom_parameters={
                        'c_real': -0.7,
                        'c_imag': 0.27015
                    }
                )
                
                result = self.generator.calculate(params)
                
                # Check that result has correct dimensions
                self.assertEqual(result.iteration_data.shape, (height, width))
                self.assertEqual(result.image_size, (width, height))
    
    def test_calculation_time_recorded(self):
        """Test that calculation time is properly recorded."""
        result = self.generator.calculate(self.standard_parameters)
        
        # Calculation time should be positive and reasonable
        self.assertGreater(result.calculation_time, 0)
        self.assertLess(result.calculation_time, 60)  # Should complete within 60 seconds
    
    def test_reproducibility(self):
        """Test that calculations are reproducible."""
        result1 = self.generator.calculate(self.standard_parameters)
        result2 = self.generator.calculate(self.standard_parameters)
        
        # Results should be identical
        np.testing.assert_array_equal(result1.iteration_data, result2.iteration_data)
        self.assertEqual(result1.region, result2.region)
    
    def test_interesting_c_values(self):
        """Test the list of interesting c values."""
        interesting_values = self.generator.get_interesting_c_values()
        
        # Should have multiple interesting values
        self.assertGreater(len(interesting_values), 5)
        
        # Each value should be a tuple with 3 elements
        for c_real, c_imag, description in interesting_values:
            self.assertIsInstance(c_real, (int, float))
            self.assertIsInstance(c_imag, (int, float))
            self.assertIsInstance(description, str)
            self.assertGreater(len(description), 0)
    
    def test_mathematical_accuracy_simple_case(self):
        """Test mathematical accuracy for a simple case."""
        # Test with c = -1 (real axis)
        params_real = FractalParameters(
            region=ComplexRegion(
                top_left=ComplexNumber(-2.0, 0.1),
                bottom_right=ComplexNumber(2.0, -0.1)
            ),
            max_iterations=100,
            image_size=(20, 5),
            custom_parameters={
                'c_real': -1.0,
                'c_imag': 0.0
            }
        )
        
        result = self.generator.calculate(params_real)
        
        # Should complete without error
        self.assertIsNotNone(result)
        self.assertEqual(result.metadata['c_real'], -1.0)
        self.assertEqual(result.metadata['c_imag'], 0.0)
        
        # Should have variety in iteration counts
        unique_counts = np.unique(result.iteration_data)
        self.assertGreater(len(unique_counts), 3)
    
    def test_default_parameters_when_missing(self):
        """Test that default parameters are used when custom parameters are missing."""
        params_minimal = FractalParameters(
            region=self.standard_region,
            max_iterations=50,
            image_size=(50, 50),
            custom_parameters={}  # No custom parameters
        )
        
        result = self.generator.calculate(params_minimal)
        
        # Should use default values
        self.assertEqual(result.metadata['c_real'], -0.7)
        self.assertEqual(result.metadata['c_imag'], 0.27015)
        self.assertEqual(result.metadata['escape_radius'], 2.0)
    
    def test_julia_vs_mandelbrot_difference(self):
        """Test that Julia set produces different results from Mandelbrot set."""
        from fractal_editor.generators.mandelbrot import MandelbrotGenerator
        
        mandelbrot_gen = MandelbrotGenerator()
        
        # Use same region and iterations for both
        params_julia = FractalParameters(
            region=self.standard_region,
            max_iterations=50,
            image_size=(50, 50),
            custom_parameters={
                'c_real': -0.7,
                'c_imag': 0.27015
            }
        )
        
        params_mandelbrot = FractalParameters(
            region=self.standard_region,
            max_iterations=50,
            image_size=(50, 50),
            custom_parameters={}
        )
        
        julia_result = self.generator.calculate(params_julia)
        mandelbrot_result = mandelbrot_gen.calculate(params_mandelbrot)
        
        # Results should be different (different fractal types)
        self.assertFalse(np.array_equal(julia_result.iteration_data, mandelbrot_result.iteration_data))


if __name__ == '__main__':
    unittest.main()