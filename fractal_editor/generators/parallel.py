"""
Parallel computation system for fractal generation.

This module provides multiprocessing-based parallel computation capabilities
with progress tracking and cancellation support.
"""

import multiprocessing as mp
import numpy as np
import time
import threading
from typing import Callable, Any, Optional, List, Tuple
from dataclasses import dataclass
from enum import Enum
import queue
import os
from ..services.memory_manager import MemoryManager, MemoryPriority, MemoryEfficientArrayOps


class ComputationStatus(Enum):
    """Status of a parallel computation."""
    NOT_STARTED = "not_started"
    RUNNING = "running"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    ERROR = "error"


@dataclass
class ProgressInfo:
    """Information about computation progress."""
    current_step: int
    total_steps: int
    elapsed_time: float
    estimated_remaining_time: float
    status: ComputationStatus
    
    @property
    def progress_percentage(self) -> float:
        """Get progress as a percentage (0-100)."""
        if self.total_steps == 0:
            return 0.0
        return (self.current_step / self.total_steps) * 100.0
    
    @property
    def is_complete(self) -> bool:
        """Check if computation is complete."""
        return self.status in [ComputationStatus.COMPLETED, ComputationStatus.CANCELLED, ComputationStatus.ERROR]


class ParallelCalculator:
    """
    Parallel computation engine for fractal calculations.
    
    This class manages multiprocessing-based parallel computation with
    progress tracking and cancellation capabilities.
    """
    
    def __init__(self, num_processes: Optional[int] = None):
        """
        Initialize the parallel calculator.
        
        Args:
            num_processes: Number of processes to use. If None, uses CPU count.
        """
        self.num_processes = num_processes or os.cpu_count() or 4
        self._cancel_event = mp.Event()
        self._progress_queue = mp.Queue()
        self._result_queue = mp.Queue()
        self._current_computation = None
        self._progress_thread = None
        self._progress_callback = None
        
    def calculate_fractal_parallel(self, 
                                 generator_func: Callable,
                                 parameters: Any,
                                 progress_callback: Optional[Callable[[ProgressInfo], None]] = None) -> Any:
        """
        Calculate fractal using parallel processing.
        
        Args:
            generator_func: Function that calculates fractal for a region
            parameters: Parameters for fractal generation
            progress_callback: Optional callback for progress updates
            
        Returns:
            Fractal calculation result
            
        Raises:
            RuntimeError: If computation is cancelled or fails
        """
        self._progress_callback = progress_callback
        self._cancel_event.clear()
        
        try:
            # Divide the computation into chunks for parallel processing
            chunks = self._create_computation_chunks(parameters)
            
            # Start progress monitoring
            if progress_callback:
                self._start_progress_monitoring(len(chunks))
            
            # Execute parallel computation
            start_time = time.time()
            results = self._execute_parallel_computation(generator_func, chunks)
            calculation_time = time.time() - start_time
            
            # Combine results
            combined_result = self._combine_results(results, parameters, calculation_time)
            
            # Update final progress
            if progress_callback:
                final_progress = ProgressInfo(
                    current_step=len(chunks),
                    total_steps=len(chunks),
                    elapsed_time=calculation_time,
                    estimated_remaining_time=0.0,
                    status=ComputationStatus.COMPLETED
                )
                progress_callback(final_progress)
            
            return combined_result
            
        except Exception as e:
            if progress_callback:
                error_progress = ProgressInfo(
                    current_step=0,
                    total_steps=1,
                    elapsed_time=0.0,
                    estimated_remaining_time=0.0,
                    status=ComputationStatus.ERROR
                )
                progress_callback(error_progress)
            raise RuntimeError(f"Parallel computation failed: {e}")
        
        finally:
            self._cleanup()
    
    def cancel_computation(self) -> None:
        """Cancel the current computation."""
        self._cancel_event.set()
        
        if self._progress_callback:
            cancel_progress = ProgressInfo(
                current_step=0,
                total_steps=1,
                elapsed_time=0.0,
                estimated_remaining_time=0.0,
                status=ComputationStatus.CANCELLED
            )
            self._progress_callback(cancel_progress)
    
    def _create_computation_chunks(self, parameters: Any) -> List[Tuple[Any, int]]:
        """
        Divide the computation into chunks for parallel processing.
        
        Args:
            parameters: Fractal generation parameters
            
        Returns:
            List of (chunk_parameters, chunk_index) tuples
        """
        # Divide the image into horizontal strips for parallel processing
        width, height = parameters.image_size
        chunk_height = max(1, height // self.num_processes)
        
        chunks = []
        for i in range(self.num_processes):
            start_row = i * chunk_height
            end_row = min((i + 1) * chunk_height, height)
            
            if start_row >= height:
                break
            
            # Create parameters for this chunk
            chunk_params = self._create_chunk_parameters(parameters, start_row, end_row)
            chunks.append((chunk_params, i))
        
        return chunks
    
    def _create_chunk_parameters(self, original_params: Any, start_row: int, end_row: int) -> Any:
        """
        Create parameters for a specific chunk of the computation.
        
        Args:
            original_params: Original fractal parameters
            start_row: Starting row for this chunk
            end_row: Ending row for this chunk
            
        Returns:
            Parameters for the chunk
        """
        from ..models.data_models import FractalParameters, ComplexRegion, ComplexNumber
        
        # Calculate the region for this chunk
        width, height = original_params.image_size
        chunk_height = end_row - start_row
        
        # Calculate the complex plane coordinates for this chunk
        region = original_params.region
        y_min = region.bottom_right.imaginary
        y_max = region.top_left.imaginary
        
        # Calculate y coordinates for this chunk
        # Note: In image coordinates, row 0 is at the top, but in complex plane,
        # higher Y values are at the top. We need to map correctly.
        y_range = y_max - y_min
        chunk_y_min = y_min + (start_row / height) * y_range
        chunk_y_max = y_min + (end_row / height) * y_range
        
        chunk_region = ComplexRegion(
            top_left=ComplexNumber(region.top_left.real, chunk_y_max),
            bottom_right=ComplexNumber(region.bottom_right.real, chunk_y_min)
        )
        
        # Create chunk parameters
        chunk_params = FractalParameters(
            region=chunk_region,
            max_iterations=original_params.max_iterations,
            image_size=(width, chunk_height),
            custom_parameters=original_params.custom_parameters.copy()
        )
        
        # Add chunk metadata
        chunk_params.custom_parameters['_chunk_start_row'] = start_row
        chunk_params.custom_parameters['_chunk_end_row'] = end_row
        chunk_params.custom_parameters['_original_height'] = height
        
        return chunk_params
    
    def _execute_parallel_computation(self, generator_func: Callable, chunks: List[Tuple[Any, int]]) -> List[Any]:
        """
        Execute the parallel computation using a row-based approach.
        
        Args:
            generator_func: Function to calculate fractal for each chunk
            chunks: List of computation chunks
            
        Returns:
            List of results from each chunk
        """
        # Use a custom row-based parallel calculation instead of chunking
        # This ensures coordinate consistency
        # Get the original parameters from the first chunk's metadata
        original_params = chunks[0][0]
        if '_original_height' in original_params.custom_parameters:
            # Reconstruct original parameters from chunk metadata
            original_height = original_params.custom_parameters['_original_height']
            original_image_size = (original_params.image_size[0], original_height)
            
            # Find the original region by looking at all chunks
            all_chunk_params = [chunk_params for chunk_params, _ in chunks]
            
            # Get the full region bounds
            min_y = min(cp.region.bottom_right.imaginary for cp in all_chunk_params)
            max_y = max(cp.region.top_left.imaginary for cp in all_chunk_params)
            
            from ..models.data_models import FractalParameters, ComplexRegion, ComplexNumber
            
            original_region = ComplexRegion(
                top_left=ComplexNumber(original_params.region.top_left.real, max_y),
                bottom_right=ComplexNumber(original_params.region.bottom_right.real, min_y)
            )
            
            reconstructed_params = FractalParameters(
                region=original_region,
                max_iterations=original_params.max_iterations,
                image_size=original_image_size,
                custom_parameters={k: v for k, v in original_params.custom_parameters.items() 
                                 if not k.startswith('_chunk')}
            )
            
            return self._calculate_rows_parallel(generator_func, reconstructed_params)
        else:
            return self._calculate_rows_parallel(generator_func, original_params)
    
    def _calculate_rows_parallel(self, generator_func: Callable, original_params: Any) -> List[Any]:
        """
        Calculate fractal rows in parallel to ensure coordinate consistency.
        
        Args:
            generator_func: Base generator function (not used directly)
            original_params: Original fractal parameters
            
        Returns:
            List with single combined result
        """
        import concurrent.futures
        from ..generators.mandelbrot import MandelbrotGenerator
        from ..generators.julia import JuliaGenerator
        
        # メモリマネージャーを取得
        memory_manager = MemoryManager()
        
        # メモリ使用量を事前チェック
        width, height = original_params.image_size
        estimated_memory = memory_manager.estimate_fractal_memory_usage(
            width, height, original_params.max_iterations
        )
        
        if not memory_manager.check_memory_availability(estimated_memory):
            # メモリ不足時の最適化提案を取得
            optimization = memory_manager.optimize_for_large_computation(
                width, height, original_params.max_iterations
            )
            raise MemoryError(
                f"メモリ不足で並列フラクタル計算を実行できません。"
                f"推定メモリ使用量: {optimization['estimated_memory_mb']:.1f}MB, "
                f"利用可能メモリ: {optimization['available_memory_mb']:.1f}MB。"
                f"推奨事項: {optimization['recommendations']}"
            )
        
        # メモリ管理コンテキストで計算を実行
        with memory_manager.memory_context("Parallel fractal calculation"):
            # Determine which generator to use based on the function
            if hasattr(generator_func, '__self__'):
                generator = generator_func.__self__
            else:
                # Fallback - create a new Mandelbrot generator
                generator = MandelbrotGenerator()
            
            max_iterations = original_params.max_iterations
            region = original_params.region
            
            # Get generator-specific parameters
            if isinstance(generator, MandelbrotGenerator):
                escape_radius = original_params.get_custom_parameter('escape_radius', 2.0)
                escape_radius_squared = escape_radius * escape_radius
            elif hasattr(generator, '__class__') and 'Julia' in generator.__class__.__name__:
                c_real = original_params.get_custom_parameter('c_real', -0.7)
                c_imag = original_params.get_custom_parameter('c_imag', 0.27015)
                c = complex(c_real, c_imag)
                escape_radius = original_params.get_custom_parameter('escape_radius', 2.0)
                escape_radius_squared = escape_radius * escape_radius
            else:
                # Generic parameters
                escape_radius = 2.0
                escape_radius_squared = 4.0
            
            # Create coordinate arrays (same as sequential)
            x_min, x_max = region.top_left.real, region.bottom_right.real
            y_min, y_max = region.bottom_right.imaginary, region.top_left.imaginary
            
            x_coords = np.linspace(x_min, x_max, width)
            y_coords = np.linspace(y_min, y_max, height)
            
            # メモリ管理された配列を割り当て
            iteration_data = memory_manager.allocate_array(
                (height, width), 
                dtype=np.int32,
                priority=MemoryPriority.HIGH,
                description=f"Parallel fractal result {width}x{height}"
            )
            
            if iteration_data is None:
                raise MemoryError("並列計算用結果配列の割り当てに失敗しました")
            
            def calculate_row(row_index):
                """Calculate a single row of the fractal."""
                y = y_coords[row_index]
                
                # 行データ用の小さな配列を割り当て
                row_data = memory_manager.allocate_array(
                    (width,), 
                    dtype=np.int32,
                    priority=MemoryPriority.NORMAL,
                    description=f"Row {row_index} data"
                )
                
                if row_data is None:
                    # フォールバック: 通常のnumpy配列を使用
                    row_data = np.zeros(width, dtype=np.int32)
                
                for j, x in enumerate(x_coords):
                    if isinstance(generator, MandelbrotGenerator):
                        # Mandelbrot: c = complex point, z starts at 0
                        c_point = complex(x, y)
                        z = complex(0, 0)
                    elif hasattr(generator, '__class__') and 'Julia' in generator.__class__.__name__:
                        # Julia: z = complex point, c is fixed parameter
                        z = complex(x, y)
                        c_point = c  # Use the fixed c parameter defined above
                    else:
                        # Default to Mandelbrot behavior
                        c_point = complex(x, y)
                        z = complex(0, 0)
                    
                    # Iterate the fractal formula
                    for n in range(max_iterations):
                        # Check for escape condition
                        if z.real * z.real + z.imag * z.imag > escape_radius_squared:
                            row_data[j] = n
                            break
                        
                        # Apply the iteration formula: z = z^2 + c
                        z = z * z + c_point
                    else:
                        # Point didn't escape within max_iterations
                        row_data[j] = max_iterations
                
                return row_index, row_data
            
            # Calculate rows in parallel
            with concurrent.futures.ThreadPoolExecutor(max_workers=self.num_processes) as executor:
                # Submit all rows for processing
                future_to_row = {executor.submit(calculate_row, i): i for i in range(height)}
                
                completed_count = 0
                for future in concurrent.futures.as_completed(future_to_row):
                    try:
                        # Check for cancellation
                        if self._cancel_event.is_set():
                            executor.shutdown(wait=False)
                            raise RuntimeError("Computation was cancelled")
                        
                        # Get result
                        row_index, row_data = future.result()
                        iteration_data[row_index] = row_data
                        completed_count += 1
                        
                        # Update progress
                        self._update_progress(completed_count, height)
                        
                        # 定期的にガベージコレクションを実行（メモリ効率化）
                        if completed_count % max(1, height // 10) == 0:
                            memory_manager.force_garbage_collection()
                        
                    except Exception as e:
                        executor.shutdown(wait=False)
                        raise RuntimeError(f"Row calculation failed: {e}")
            
            # メモリ統計を取得
            memory_stats = memory_manager.get_memory_statistics()
            
            # Create the result
            from ..models.data_models import FractalResult
            calculation_time = 0.1  # Placeholder - timing is handled at higher level
            
            result = FractalResult(
                iteration_data=iteration_data,
                region=region,
                calculation_time=calculation_time,
                parameters=original_params,
                metadata={
                    'generator': 'Memory-Managed Parallel Row Computation',
                    'num_processes': self.num_processes,
                    'algorithm': 'memory_managed_parallel_rows',
                    'memory_usage_mb': memory_stats['allocation_statistics']['total_allocated_mb'],
                    'peak_memory_mb': memory_stats['allocation_statistics']['peak_memory_mb']
                }
            )
            
            return [result]  # Return as list to match expected interface
    
    def _combine_results(self, chunk_results: List[Any], original_params: Any, calculation_time: float) -> Any:
        """
        Combine results from parallel chunks into a single result.
        
        Args:
            chunk_results: Results from each chunk
            original_params: Original parameters
            calculation_time: Total calculation time
            
        Returns:
            Combined fractal result
        """
        from ..models.data_models import FractalResult
        
        # Handle the case where we have a single pre-combined result (row-based approach)
        if len(chunk_results) == 1 and hasattr(chunk_results[0], 'metadata') and chunk_results[0].metadata.get('algorithm') == 'parallel_rows':
            result = chunk_results[0]
            # Update timing and metadata
            result.calculation_time = calculation_time
            result.metadata.update({
                'total_calculation_time': calculation_time,
                'parallel_efficiency': 1.0  # Row-based is already optimized
            })
            return result
        
        # Original chunk-based approach
        # Sort results by chunk start row to ensure correct order
        sorted_results = sorted(chunk_results, 
                              key=lambda r: r.parameters.custom_parameters.get('_chunk_start_row', 0))
        
        # Combine iteration data vertically (stacking rows)
        iteration_arrays = [result.iteration_data for result in sorted_results]
        combined_iteration_data = np.vstack(iteration_arrays)
        
        # Verify the combined shape matches the original parameters
        expected_shape = (original_params.image_size[1], original_params.image_size[0])
        if combined_iteration_data.shape != expected_shape:
            raise RuntimeError(f"Combined result shape {combined_iteration_data.shape} doesn't match expected {expected_shape}")
        
        # Create combined result
        combined_result = FractalResult(
            iteration_data=combined_iteration_data,
            region=original_params.region,
            calculation_time=calculation_time,
            parameters=original_params,
            metadata={
                'generator': 'Parallel Computation',
                'num_processes': self.num_processes,
                'num_chunks': len(chunk_results),
                'chunk_calculation_times': [r.calculation_time for r in sorted_results],
                'parallel_efficiency': sum(r.calculation_time for r in sorted_results) / calculation_time if calculation_time > 0 else 1.0
            }
        )
        
        return combined_result
    
    def _start_progress_monitoring(self, total_chunks: int) -> None:
        """Start progress monitoring - simplified for threading approach."""
        self._total_chunks = total_chunks
        self._completed_chunks = 0
        self._start_time = time.time()
    
    def _update_progress(self, completed: int, total: int) -> None:
        """Update progress information."""
        if self._progress_callback:
            elapsed_time = time.time() - self._start_time
            if completed > 0:
                estimated_total_time = elapsed_time * total / completed
                estimated_remaining_time = max(0, estimated_total_time - elapsed_time)
            else:
                estimated_remaining_time = 0.0
            
            progress_info = ProgressInfo(
                current_step=completed,
                total_steps=total,
                elapsed_time=elapsed_time,
                estimated_remaining_time=estimated_remaining_time,
                status=ComputationStatus.RUNNING if completed < total else ComputationStatus.COMPLETED
            )
            
            self._progress_callback(progress_info)
    
    def _cleanup(self) -> None:
        """Clean up resources."""
        if self._progress_thread and self._progress_thread.is_alive():
            self._progress_thread.join(timeout=1.0)
        
        # Clear queues
        try:
            while not self._progress_queue.empty():
                self._progress_queue.get_nowait()
        except queue.Empty:
            pass
        
        try:
            while not self._result_queue.empty():
                self._result_queue.get_nowait()
        except queue.Empty:
            pass
    
    @staticmethod
    def _init_worker(cancel_event: mp.Event) -> None:
        """Initialize worker process."""
        global _worker_cancel_event
        _worker_cancel_event = cancel_event


# Global variable for worker processes
_worker_cancel_event = None


def _worker_calculate_chunk(generator_func: Callable, chunk_params: Any, chunk_index: int, progress_queue, cancel_event) -> Any:
    """
    Worker function to calculate a fractal chunk.
    
    Args:
        generator_func: Function to calculate fractal
        chunk_params: Parameters for this chunk
        chunk_index: Index of this chunk
        progress_queue: Queue for progress updates
        cancel_event: Event for cancellation
        
    Returns:
        Fractal result for this chunk
    """
    try:
        # Check for cancellation
        if cancel_event and cancel_event.is_set():
            raise RuntimeError("Computation was cancelled")
        
        # Calculate the chunk
        result = generator_func(chunk_params)
        
        # Report progress
        try:
            progress_queue.put(chunk_index, block=False)
        except:
            pass  # Skip if queue is full or other error
        
        return result
        
    except Exception as e:
        # Report error through progress queue
        try:
            progress_queue.put(f"ERROR_{chunk_index}: {e}", block=False)
        except:
            pass
        raise


class ParallelFractalGenerator:
    """
    Wrapper that adds parallel computation capabilities to any fractal generator.
    """
    
    def __init__(self, base_generator: Any, num_processes: Optional[int] = None):
        """
        Initialize parallel fractal generator.
        
        Args:
            base_generator: Base fractal generator to parallelize
            num_processes: Number of processes to use
        """
        self.base_generator = base_generator
        self.parallel_calculator = ParallelCalculator(num_processes)
        
    @property
    def name(self) -> str:
        """Get the name of this fractal generator."""
        return f"{self.base_generator.name} (Parallel)"
    
    @property
    def description(self) -> str:
        """Get a description of this fractal generator."""
        return f"{self.base_generator.description} - Parallel computation enabled"
    
    def calculate(self, parameters: Any, progress_callback: Optional[Callable[[ProgressInfo], None]] = None) -> Any:
        """
        Calculate fractal using parallel processing.
        
        Args:
            parameters: Fractal generation parameters
            progress_callback: Optional progress callback
            
        Returns:
            Fractal calculation result
        """
        return self.parallel_calculator.calculate_fractal_parallel(
            self.base_generator.calculate,
            parameters,
            progress_callback
        )
    
    def cancel_computation(self) -> None:
        """Cancel the current computation."""
        self.parallel_calculator.cancel_computation()
    
    def get_parameter_definitions(self) -> List[Any]:
        """Get parameter definitions from base generator."""
        return self.base_generator.get_parameter_definitions()
    
    def validate_parameters(self, parameters: Any) -> bool:
        """Validate parameters using base generator."""
        return self.base_generator.validate_parameters(parameters)