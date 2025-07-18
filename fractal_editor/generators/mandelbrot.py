"""
Mandelbrot set fractal generator.

This module implements the classic Mandelbrot set fractal generator with
mathematically accurate calculations.
"""

import numpy as np
import time
from typing import List
from .base import FractalGenerator
from ..models.data_models import (
    FractalParameters, FractalResult, ParameterDefinition, ComplexNumber
)
from ..services.memory_manager import MemoryManager, MemoryPriority


class MandelbrotGenerator(FractalGenerator):
    """
    Generator for the classic Mandelbrot set fractal.
    
    The Mandelbrot set is defined as the set of complex numbers c for which
    the sequence z_{n+1} = z_n^2 + c (starting with z_0 = 0) remains bounded.
    """
    
    @property
    def name(self) -> str:
        """Get the name of this fractal generator."""
        return "Mandelbrot Set"
    
    @property
    def description(self) -> str:
        """Get a description of this fractal generator."""
        return "Classic Mandelbrot set fractal: z_{n+1} = z_n^2 + c, starting with z_0 = 0"
    
    def calculate(self, parameters: FractalParameters) -> FractalResult:
        """
        Calculate the Mandelbrot set with the given parameters.
        
        Args:
            parameters: The parameters for fractal generation
            
        Returns:
            FractalResult containing the calculated iteration data
        """
        if not self.validate_parameters(parameters):
            raise ValueError("Invalid parameters for Mandelbrot generator")
        
        # メモリマネージャーを取得
        memory_manager = MemoryManager()
        
        # メモリ使用量を事前チェック
        width, height = parameters.image_size
        estimated_memory = memory_manager.estimate_fractal_memory_usage(
            width, height, parameters.max_iterations
        )
        
        if not memory_manager.check_memory_availability(estimated_memory):
            # メモリ不足時の最適化提案を取得
            optimization = memory_manager.optimize_for_large_computation(
                width, height, parameters.max_iterations
            )
            raise MemoryError(
                f"メモリ不足でマンデルブロ集合計算を実行できません。"
                f"推定メモリ使用量: {optimization['estimated_memory_mb']:.1f}MB, "
                f"利用可能メモリ: {optimization['available_memory_mb']:.1f}MB。"
                f"推奨事項: {optimization['recommendations']}"
            )
        
        # メモリ管理コンテキストで計算を実行
        with memory_manager.memory_context("Mandelbrot calculation"):
            start_time = time.time()
            
            # Extract parameters
            max_iterations = parameters.max_iterations
            region = parameters.region
            
            # Get escape radius (default 2.0 for Mandelbrot set)
            escape_radius = parameters.get_custom_parameter('escape_radius', 2.0)
            escape_radius_squared = escape_radius * escape_radius
            
            # Create coordinate arrays
            x_min, x_max = region.top_left.real, region.bottom_right.real
            y_min, y_max = region.bottom_right.imaginary, region.top_left.imaginary
            
            x_coords = np.linspace(x_min, x_max, width)
            y_coords = np.linspace(y_min, y_max, height)
            
            # メモリ管理された配列を割り当て
            iteration_data = memory_manager.allocate_array(
                (height, width), 
                dtype=np.int32,
                priority=MemoryPriority.HIGH,
                description=f"Mandelbrot result {width}x{height}"
            )
            
            if iteration_data is None:
                raise MemoryError("結果配列の割り当てに失敗しました")
            
            # Calculate Mandelbrot set
            for i, y in enumerate(y_coords):
                for j, x in enumerate(x_coords):
                    # c is the complex parameter for this pixel
                    c = complex(x, y)
                    z = complex(0, 0)  # Starting point z_0 = 0
                    
                    # Iterate the Mandelbrot formula: z = z^2 + c
                    for n in range(max_iterations):
                        # Check for escape condition
                        if z.real * z.real + z.imag * z.imag > escape_radius_squared:
                            iteration_data[i, j] = n
                            break
                        
                        # Mandelbrot iteration: z = z^2 + c
                        z = z * z + c
                    else:
                        # Point didn't escape within max_iterations
                        iteration_data[i, j] = max_iterations
            
            calculation_time = time.time() - start_time
            
            # メモリ統計を取得
            memory_stats = memory_manager.get_memory_statistics()
            
            # Create result with metadata
            result = FractalResult(
                iteration_data=iteration_data,
                region=region,
                calculation_time=calculation_time,
                parameters=parameters,
                metadata={
                    'generator': self.name,
                    'escape_radius': escape_radius,
                    'algorithm': 'memory_managed_mandelbrot',
                    'memory_usage_mb': memory_stats['allocation_statistics']['total_allocated_mb'],
                    'peak_memory_mb': memory_stats['allocation_statistics']['peak_memory_mb']
                }
            )
            
            return result
    
    def get_parameter_definitions(self) -> List[ParameterDefinition]:
        """
        Get the parameter definitions for the Mandelbrot generator.
        
        Returns:
            List of parameter definitions that this generator accepts
        """
        return [
            ParameterDefinition(
                name="escape_radius",
                display_name="Escape Radius",
                parameter_type="float",
                default_value=2.0,
                min_value=1.0,
                max_value=10.0,
                description="Radius at which points are considered to have escaped to infinity"
            )
        ]
    
    def validate_parameters(self, parameters: FractalParameters) -> bool:
        """
        Validate that the given parameters are suitable for Mandelbrot generation.
        
        Args:
            parameters: The parameters to validate
            
        Returns:
            True if parameters are valid, False otherwise
        """
        # Call parent validation first
        if not super().validate_parameters(parameters):
            return False
        
        # Mandelbrot-specific validation
        escape_radius = parameters.get_custom_parameter('escape_radius', 2.0)
        if not isinstance(escape_radius, (int, float)) or escape_radius <= 0:
            return False
        
        return True