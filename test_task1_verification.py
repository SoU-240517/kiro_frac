"""
Integration test to verify that Task 3 (フラクタル計算エンジンの実装) is complete.

This test verifies that all subtasks have been implemented correctly:
- 3.1 基本的なマンデルブロ集合生成器を実装
- 3.2 ジュリア集合生成器を実装  
- 3.3 並列計算システムの実装
"""

import unittest
import numpy as np
from fractal_editor.generators import fractal_registry, MandelbrotGenerator, JuliaGenerator
from fractal_editor.generators.parallel import ParallelFractalGenerator
from fractal_editor.models.data_models import (
    FractalParameters, ComplexRegion, ComplexNumber
)


class TestTask3Verification(unittest.TestCase):
    """Integration test for Task 3 completion verification."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Standard test region and parameters
        self.test_region = ComplexRegion(
            top_left=ComplexNumber(-2.0, 1.0),
            bottom_right=ComplexNumber(1.0, -1.0)
        )
        
        self.test_params = FractalParameters(
            region=self.test_region,
            max_iterations=100,
            image_size=(50, 50),
            custom_parameters={}
        )
    
    def test_subtask_3_1_mandelbrot_generator_implemented(self):
        """Verify subtask 3.1: Mandelbrot generator is implemented and working."""
        # Test that MandelbrotGenerator can be imported and instantiated
        generator = MandelbrotGenerator()
        
        # Test basic properties
        self.assertEqual(generator.name, "Mandelbrot Set")
        self.assertIn("Mandelbrot", generator.description)
        
        # Test parameter definitions
        param_defs = generator.get_parameter_definitions()
        self.assertGreater(len(param_defs), 0)
        
        # Test calculation
        result = generator.calculate(self.test_params)
        self.assertIsNotNone(result)
        self.assertEqual(result.iteration_data.shape, (50, 50))
        self.assertGreater(result.calculation_time, 0)
        
        # Test mathematical accuracy with known point
        # Point c = 0 should be in the Mandelbrot set
        zero_region = ComplexRegion(
            top_left=ComplexNumber(-0.1, 0.1),
            bottom_right=ComplexNumber(0.1, -0.1)
        )
        zero_params = FractalParameters(
            region=zero_region,
            max_iterations=100,
            image_size=(3, 3),
            custom_parameters={}
        )
        zero_result = generator.calculate(zero_params)
        center_iterations = zero_result.iteration_data[1, 1]
        self.assertEqual(center_iterations, 100)  # Should reach max iterations
        
        print("✓ Subtask 3.1: Mandelbrot generator implemented and mathematically accurate")
    
    def test_subtask_3_2_julia_generator_implemented(self):
        """Verify subtask 3.2: Julia generator is implemented and working."""
        # Test that JuliaGenerator can be imported and instantiated
        generator = JuliaGenerator()
        
        # Test basic properties
        self.assertEqual(generator.name, "Julia Set")
        self.assertIn("Julia", generator.description)
        
        # Test parameter definitions
        param_defs = generator.get_parameter_definitions()
        self.assertGreaterEqual(len(param_defs), 3)  # c_real, c_imag, escape_radius
        
        param_names = [pd.name for pd in param_defs]
        self.assertIn("c_real", param_names)
        self.assertIn("c_imag", param_names)
        self.assertIn("escape_radius", param_names)
        
        # Test calculation with default parameters
        julia_params = FractalParameters(
            region=self.test_region,
            max_iterations=100,
            image_size=(50, 50),
            custom_parameters={
                'c_real': -0.7,
                'c_imag': 0.27015
            }
        )
        
        result = generator.calculate(julia_params)
        self.assertIsNotNone(result)
        self.assertEqual(result.iteration_data.shape, (50, 50))
        self.assertGreater(result.calculation_time, 0)
        
        # Test that different c parameters produce different results
        julia_params2 = FractalParameters(
            region=self.test_region,
            max_iterations=100,
            image_size=(50, 50),
            custom_parameters={
                'c_real': 0.0,
                'c_imag': 0.0
            }
        )
        
        result2 = generator.calculate(julia_params2)
        self.assertFalse(np.array_equal(result.iteration_data, result2.iteration_data))
        
        # Test interesting c values
        interesting_values = generator.get_interesting_c_values()
        self.assertGreater(len(interesting_values), 5)
        
        print("✓ Subtask 3.2: Julia generator implemented with configurable c parameter")
    
    def test_subtask_3_3_parallel_computation_implemented(self):
        """Verify subtask 3.3: Parallel computation system is implemented and working."""
        # Test ParallelFractalGenerator wrapper
        base_generator = MandelbrotGenerator()
        parallel_generator = ParallelFractalGenerator(base_generator, num_processes=2)
        
        # Test wrapper properties
        self.assertIn("Parallel", parallel_generator.name)
        self.assertIn("Parallel", parallel_generator.description)
        
        # Test that parallel computation produces same results as sequential
        sequential_result = base_generator.calculate(self.test_params)
        parallel_result = parallel_generator.calculate(self.test_params)
        
        np.testing.assert_array_equal(
            sequential_result.iteration_data,
            parallel_result.iteration_data
        )
        
        # Test progress tracking
        progress_updates = []
        
        def progress_callback(progress):
            progress_updates.append(progress)
        
        parallel_result_with_progress = parallel_generator.calculate(
            self.test_params,
            progress_callback
        )
        
        # Should have received progress updates
        self.assertGreater(len(progress_updates), 0)
        
        # Final progress should be complete
        final_progress = progress_updates[-1]
        self.assertTrue(final_progress.is_complete)
        self.assertEqual(final_progress.progress_percentage, 100.0)
        
        # Test with Julia generator too
        julia_generator = JuliaGenerator()
        parallel_julia = ParallelFractalGenerator(julia_generator, num_processes=2)
        
        julia_params = FractalParameters(
            region=self.test_region,
            max_iterations=50,
            image_size=(30, 30),
            custom_parameters={
                'c_real': -0.7,
                'c_imag': 0.27015
            }
        )
        
        sequential_julia = julia_generator.calculate(julia_params)
        parallel_julia_result = parallel_julia.calculate(julia_params)
        
        np.testing.assert_array_equal(
            sequential_julia.iteration_data,
            parallel_julia_result.iteration_data
        )
        
        print("✓ Subtask 3.3: Parallel computation system implemented with progress tracking")
    
    def test_fractal_registry_integration(self):
        """Verify that generators are properly registered in the fractal registry."""
        # Test that generators are registered
        available_generators = fractal_registry.list_generators()
        self.assertIn("Mandelbrot Set", available_generators)
        self.assertIn("Julia Set", available_generators)
        
        # Test getting generators from registry
        mandelbrot = fractal_registry.get_generator("Mandelbrot Set")
        self.assertIsInstance(mandelbrot, MandelbrotGenerator)
        
        julia = fractal_registry.get_generator("Julia Set")
        self.assertIsInstance(julia, JuliaGenerator)
        
        # Test generator info
        mandelbrot_info = fractal_registry.get_generator_info("Mandelbrot Set")
        self.assertEqual(mandelbrot_info['name'], "Mandelbrot Set")
        self.assertIn('parameters', mandelbrot_info)
        self.assertIn('default_values', mandelbrot_info)
        
        julia_info = fractal_registry.get_generator_info("Julia Set")
        self.assertEqual(julia_info['name'], "Julia Set")
        self.assertIn('parameters', julia_info)
        self.assertIn('default_values', julia_info)
        
        print("✓ Fractal generators properly registered and accessible via registry")
    
    def test_mathematical_accuracy_verification(self):
        """Verify mathematical accuracy of both generators."""
        mandelbrot = MandelbrotGenerator()
        julia = JuliaGenerator()
        
        # Test Mandelbrot set boundary behavior
        # Point c = 2 should escape quickly (outside the set)
        escape_region = ComplexRegion(
            top_left=ComplexNumber(1.9, 0.1),
            bottom_right=ComplexNumber(2.1, -0.1)
        )
        escape_params = FractalParameters(
            region=escape_region,
            max_iterations=100,
            image_size=(3, 3),
            custom_parameters={}
        )
        
        escape_result = mandelbrot.calculate(escape_params)
        center_escape = escape_result.iteration_data[1, 1]
        self.assertLess(center_escape, 10)  # Should escape quickly
        
        # Test Julia set with c = 0 (should behave like z^2)
        julia_zero_params = FractalParameters(
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
        
        julia_zero_result = julia.calculate(julia_zero_params)
        
        # Center point (0,0) should reach max iterations
        center_julia = julia_zero_result.iteration_data[5, 5]
        self.assertEqual(center_julia, 50)
        
        # Corner points should escape quickly
        corner_julia = julia_zero_result.iteration_data[0, 0]
        self.assertLess(corner_julia, 10)
        
        print("✓ Mathematical accuracy verified for both Mandelbrot and Julia sets")
    
    def test_performance_and_efficiency(self):
        """Verify that parallel computation provides performance benefits."""
        mandelbrot = MandelbrotGenerator()
        parallel_mandelbrot = ParallelFractalGenerator(mandelbrot, num_processes=2)
        
        # Use larger parameters for performance testing
        perf_params = FractalParameters(
            region=self.test_region,
            max_iterations=200,
            image_size=(100, 100),
            custom_parameters={}
        )
        
        import time
        
        # Sequential timing
        start_time = time.time()
        sequential_result = mandelbrot.calculate(perf_params)
        sequential_time = time.time() - start_time
        
        # Parallel timing
        start_time = time.time()
        parallel_result = parallel_mandelbrot.calculate(perf_params)
        parallel_time = time.time() - start_time
        
        # Results should be identical
        np.testing.assert_array_equal(
            sequential_result.iteration_data,
            parallel_result.iteration_data
        )
        
        # Parallel should not be significantly slower (allowing for overhead)
        efficiency_ratio = sequential_time / parallel_time
        self.assertGreater(efficiency_ratio, 0.5)  # At least 50% efficiency
        
        print(f"✓ Performance test: Sequential={sequential_time:.3f}s, Parallel={parallel_time:.3f}s, Efficiency={efficiency_ratio:.2f}x")


if __name__ == '__main__':
    print("=" * 60)
    print("Task 3 Verification: フラクタル計算エンジンの実装")
    print("=" * 60)
    
    unittest.main(verbosity=2)