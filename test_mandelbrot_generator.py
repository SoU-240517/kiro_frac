"""
Unit tests for the MandelbrotGenerator class.

These tests verify the mathematical accuracy and correctness of the
Mandelbrot set calculation implementation.
"""

import unittest
import numpy as np
from fractal_editor.generators.mandelbrot import MandelbrotGenerator
from fractal_editor.models.data_models import (
    FractalParameters, ComplexRegion, ComplexNumber
)


class TestMandelbrotGenerator(unittest.TestCase):
    """Test cases for MandelbrotGenerator class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.generator = MandelbrotGenerator()
        
        # Standard test parameters
        self.standard_region = ComplexRegion(
            top_left=ComplexNumber(-2.0, 1.0),
            bottom_right=ComplexNumber(1.0, -1.0)
        )
        
        self.standard_parameters = FractalParameters(
            region=self.standard_region,
            max_iterations=100,
            image_size=(100, 100),
            custom_parameters={}
        )
    
    def test_generator_properties(self):
        """Test basic generator properties."""
        self.assertEqual(self.generator.name, "Mandelbrot Set")
        self.assertIn("Mandelbrot", self.generator.description)
        self.assertIn("z_{n+1} = z_n^2 + c", self.generator.description)
    
    def test_parameter_definitions(self):
        """Test parameter definitions."""
        param_defs = self.generator.get_parameter_definitions()
        self.assertEqual(len(param_defs), 1)
        
        escape_radius_def = param_defs[0]
        self.assertEqual(escape_radius_def.name, "escape_radius")
        self.assertEqual(escape_radius_def.parameter_type, "float")
        self.assertEqual(escape_radius_def.default_value, 2.0)
        self.assertEqual(escape_radius_def.min_value, 1.0)
        self.assertEqual(escape_radius_def.max_value, 10.0)
    
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
        self.assertEqual(result.metadata['generator'], "Mandelbrot Set")
        self.assertEqual(result.metadata['escape_radius'], 2.0)
        self.assertEqual(result.metadata['algorithm'], 'standard_mandelbrot')
    
    def test_known_mandelbrot_points(self):
        """Test calculation for known points in the Mandelbrot set."""
        # Test point c = 0 (should be in the set)
        region_zero = ComplexRegion(
            top_left=ComplexNumber(-0.1, 0.1),
            bottom_right=ComplexNumber(0.1, -0.1)
        )
        
        params_zero = FractalParameters(
            region=region_zero,
            max_iterations=100,
            image_size=(3, 3),  # Small image for precise testing
            custom_parameters={}
        )
        
        result = self.generator.calculate(params_zero)
        
        # Center pixel should reach max iterations (point is in the set)
        center_iterations = result.iteration_data[1, 1]  # Center of 3x3 grid
        self.assertEqual(center_iterations, 100)
    
    def test_known_escape_points(self):
        """Test calculation for known points that escape quickly."""
        # Test point c = 2 (should escape immediately)
        region_escape = ComplexRegion(
            top_left=ComplexNumber(1.9, 0.1),
            bottom_right=ComplexNumber(2.1, -0.1)
        )
        
        params_escape = FractalParameters(
            region=region_escape,
            max_iterations=100,
            image_size=(3, 3),
            custom_parameters={}
        )
        
        result = self.generator.calculate(params_escape)
        
        # Center pixel should escape very quickly
        center_iterations = result.iteration_data[1, 1]
        self.assertLess(center_iterations, 5)  # Should escape in first few iterations
    
    def test_boundary_behavior(self):
        """Test behavior at the boundary of the Mandelbrot set."""
        # Test a region that includes both inside and outside points
        region_boundary = ComplexRegion(
            top_left=ComplexNumber(-0.8, 0.2),
            bottom_right=ComplexNumber(-0.6, -0.2)
        )
        
        params_boundary = FractalParameters(
            region=region_boundary,
            max_iterations=100,  # Reasonable iterations for testing
            image_size=(10, 10),
            custom_parameters={}
        )
        
        result = self.generator.calculate(params_boundary)
        
        # Should have a mix of high and low iteration counts
        iterations = result.iteration_data.flatten()
        unique_values = np.unique(iterations)
        
        # Should have variety in iteration counts (not all same value)
        self.assertGreater(len(unique_values), 2)
        
        # Should have some variety in the iteration counts
        min_iter = np.min(iterations)
        max_iter = np.max(iterations)
        self.assertLess(min_iter, max_iter)  # Should have different values
    
    def test_custom_escape_radius(self):
        """Test calculation with custom escape radius."""
        params_custom = FractalParameters(
            region=self.standard_region,
            max_iterations=50,
            image_size=(50, 50),
            custom_parameters={'escape_radius': 4.0}
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
            custom_parameters={'escape_radius': 2.0}
        )
        
        result_standard = self.generator.calculate(params_standard)
        
        # Results should be different (higher escape radius should affect calculation)
        self.assertFalse(np.array_equal(result.iteration_data, result_standard.iteration_data))
    
    def test_parameter_validation(self):
        """Test parameter validation."""
        # Valid parameters should pass
        self.assertTrue(self.generator.validate_parameters(self.standard_parameters))
        
        # Invalid escape radius should fail
        invalid_params = FractalParameters(
            region=self.standard_region,
            max_iterations=100,
            image_size=(100, 100),
            custom_parameters={'escape_radius': -1.0}  # Invalid negative radius
        )
        
        self.assertFalse(self.generator.validate_parameters(invalid_params))
        
        # Non-numeric escape radius should fail
        invalid_params2 = FractalParameters(
            region=self.standard_region,
            max_iterations=100,
            image_size=(100, 100),
            custom_parameters={'escape_radius': "invalid"}
        )
        
        self.assertFalse(self.generator.validate_parameters(invalid_params2))
    
    def test_mathematical_accuracy_simple_case(self):
        """Test mathematical accuracy for a simple, manually verifiable case."""
        # Test c = -1 (should be in the set)
        # For c = -1: z_0 = 0, z_1 = -1, z_2 = 0, z_3 = -1, ... (period 2)
        region_minus_one = ComplexRegion(
            top_left=ComplexNumber(-1.01, 0.01),
            bottom_right=ComplexNumber(-0.99, -0.01)
        )
        
        params_minus_one = FractalParameters(
            region=region_minus_one,
            max_iterations=100,
            image_size=(3, 3),
            custom_parameters={}
        )
        
        result = self.generator.calculate(params_minus_one)
        
        # Center pixel (c ≈ -1) should reach max iterations
        center_iterations = result.iteration_data[1, 1]
        self.assertEqual(center_iterations, 100)
    
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
                    custom_parameters={}
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


if __name__ == '__main__':
    unittest.main()