"""
Julia set fractal generator.

This module implements the Julia set fractal generator with
mathematically accurate calculations and configurable complex parameter c.
"""

import numpy as np
import time
from typing import List
from .base import FractalGenerator
from ..models.data_models import (
    FractalParameters, FractalResult, ParameterDefinition, ComplexNumber
)
from ..services.memory_manager import MemoryManager, MemoryPriority


class JuliaGenerator(FractalGenerator):
    """
    Generator for Julia set fractals.
    
    The Julia set is defined as the set of complex numbers z for which
    the sequence z_{n+1} = z_n^2 + c (where c is a fixed complex parameter)
    remains bounded when starting with z_0 = z.
    """
    
    @property
    def name(self) -> str:
        """Get the name of this fractal generator."""
        return "Julia Set"
    
    @property
    def description(self) -> str:
        """Get a description of this fractal generator."""
        return "Julia set fractal: z_{n+1} = z_n^2 + c, where c is a fixed complex parameter"
    
    def calculate(self, parameters: FractalParameters) -> FractalResult:
        """
        Calculate the Julia set with the given parameters.
        
        Args:
            parameters: The parameters for fractal generation
            
        Returns:
            FractalResult containing the calculated iteration data
        """
        if not self.validate_parameters(parameters):
            raise ValueError("Invalid parameters for Julia generator")
        
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
                f"メモリ不足でジュリア集合計算を実行できません。"
                f"推定メモリ使用量: {optimization['estimated_memory_mb']:.1f}MB, "
                f"利用可能メモリ: {optimization['available_memory_mb']:.1f}MB。"
                f"推奨事項: {optimization['recommendations']}"
            )
        
        # メモリ管理コンテキストで計算を実行
        with memory_manager.memory_context("Julia calculation"):
            start_time = time.time()
            
            # Extract parameters
            max_iterations = parameters.max_iterations
            region = parameters.region
            
            # Get Julia set parameters
            c_real = parameters.get_custom_parameter('c_real', -0.7)
            c_imag = parameters.get_custom_parameter('c_imag', 0.27015)
            c = complex(c_real, c_imag)
            
            # Get escape radius (default 2.0 for Julia set)
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
                description=f"Julia result {width}x{height}"
            )
            
            if iteration_data is None:
                raise MemoryError("結果配列の割り当てに失敗しました")
            
            # Calculate Julia set
            for i, y in enumerate(y_coords):
                for j, x in enumerate(x_coords):
                    # z is the starting point for this pixel
                    z = complex(x, y)
                    
                    # Iterate the Julia formula: z = z^2 + c
                    for n in range(max_iterations):
                        # Check for escape condition
                        if z.real * z.real + z.imag * z.imag > escape_radius_squared:
                            iteration_data[i, j] = n
                            break
                        
                        # Julia iteration: z = z^2 + c
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
                    'c_parameter': c,
                    'c_real': c_real,
                    'c_imag': c_imag,
                    'escape_radius': escape_radius,
                    'algorithm': 'memory_managed_julia',
                    'memory_usage_mb': memory_stats['allocation_statistics']['total_allocated_mb'],
                    'peak_memory_mb': memory_stats['allocation_statistics']['peak_memory_mb']
                }
            )
            
            return result
    
    def get_parameter_definitions(self) -> List[ParameterDefinition]:
        """
        Get the parameter definitions for the Julia generator.
        
        Returns:
            List of parameter definitions that this generator accepts
        """
        return [
            ParameterDefinition(
                name="c_real",
                display_name="C Real Part",
                parameter_type="float",
                default_value=-0.7,
                min_value=-2.0,
                max_value=2.0,
                description="Real part of the complex parameter c"
            ),
            ParameterDefinition(
                name="c_imag",
                display_name="C Imaginary Part",
                parameter_type="float",
                default_value=0.27015,
                min_value=-2.0,
                max_value=2.0,
                description="Imaginary part of the complex parameter c"
            ),
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
        Validate that the given parameters are suitable for Julia generation.
        
        Args:
            parameters: The parameters to validate
            
        Returns:
            True if parameters are valid, False otherwise
        """
        # Call parent validation first
        if not super().validate_parameters(parameters):
            return False
        
        # Julia-specific validation
        c_real = parameters.get_custom_parameter('c_real', -0.7)
        c_imag = parameters.get_custom_parameter('c_imag', 0.27015)
        escape_radius = parameters.get_custom_parameter('escape_radius', 2.0)
        
        # Validate c parameters
        if not isinstance(c_real, (int, float)):
            return False
        if not isinstance(c_imag, (int, float)):
            return False
        
        # Validate escape radius
        if not isinstance(escape_radius, (int, float)) or escape_radius <= 0:
            return False
        
        return True
    
    def set_c_parameter(self, c_real: float, c_imag: float) -> None:
        """
        Convenience method to set the complex parameter c.
        
        Args:
            c_real: Real part of c
            c_imag: Imaginary part of c
        """
        # This method would be used by UI components to set the c parameter
        # The actual parameter setting would be done through FractalParameters
        pass
    
    def get_interesting_c_values(self) -> List[tuple[float, float, str]]:
        """
        Get a list of interesting c values that produce beautiful Julia sets.
        
        Returns:
            List of tuples (c_real, c_imag, description)
        """
        return [
            (-0.7, 0.27015, "Classic Julia set"),
            (-0.8, 0.156, "Spiral Julia set"),
            (-0.75, 0.0, "Real axis Julia set"),
            (0.285, 0.01, "Dendrite Julia set"),
            (-0.4, 0.6, "Rabbit Julia set"),
            (-0.123, 0.745, "Douady rabbit"),
            (-0.235, 0.827, "Fractal dust"),
            (0.3, 0.5, "Connected Julia set"),
            (-1.25, 0.0, "Basilica Julia set"),
            (-0.1, 0.651, "Airplane Julia set")
        ]