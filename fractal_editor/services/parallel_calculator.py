"""
Parallel calculation service for fractal generation.
"""
import multiprocessing
import os
from typing import Callable, Any, List, Tuple
from concurrent.futures import ProcessPoolExecutor, as_completed
import numpy as np


class ParallelCalculator:
    """Service for parallel fractal calculations using multiprocessing."""
    
    def __init__(self, max_workers: int = None):
        """
        Initialize parallel calculator.
        
        Args:
            max_workers: Maximum number of worker processes. If None, uses CPU count.
        """
        self.max_workers = max_workers or os.cpu_count() or 4
        self._executor = None
        self._is_cancelled = False
    
    def start(self) -> None:
        """Start the parallel calculation service."""
        if self._executor is None:
            self._executor = ProcessPoolExecutor(max_workers=self.max_workers)
    
    def stop(self) -> None:
        """Stop the parallel calculation service."""
        if self._executor:
            self._executor.shutdown(wait=True)
            self._executor = None
    
    def cancel_calculation(self) -> None:
        """Cancel ongoing calculations."""
        self._is_cancelled = True
    
    def reset_cancellation(self) -> None:
        """Reset cancellation flag."""
        self._is_cancelled = False
    
    @property
    def is_cancelled(self) -> bool:
        """Check if calculation is cancelled."""
        return self._is_cancelled
    
    def calculate_parallel_chunks(self, 
                                calculation_func: Callable,
                                chunks: List[Tuple[Any, ...]], 
                                progress_callback: Callable[[float], None] = None) -> List[Any]:
        """
        Execute calculation function on multiple chunks in parallel.
        
        Args:
            calculation_func: Function to execute on each chunk
            chunks: List of chunk data tuples
            progress_callback: Optional callback for progress updates
            
        Returns:
            List of calculation results
        """
        if not self._executor:
            self.start()
        
        self.reset_cancellation()
        results = []
        completed_count = 0
        total_chunks = len(chunks)
        
        # Submit all tasks
        future_to_chunk = {
            self._executor.submit(calculation_func, chunk): chunk 
            for chunk in chunks
        }
        
        # Collect results as they complete
        for future in as_completed(future_to_chunk):
            if self._is_cancelled:
                # Cancel remaining futures
                for f in future_to_chunk:
                    f.cancel()
                break
            
            try:
                result = future.result()
                results.append(result)
                completed_count += 1
                
                # Update progress
                if progress_callback:
                    progress = completed_count / total_chunks
                    progress_callback(progress)
                    
            except Exception as ex:
                # Handle individual chunk calculation errors
                from .error_handling import ErrorHandlingService
                error_service = ErrorHandlingService()
                error_service.handle_general_error(ex, "parallel calculation")
                results.append(None)  # Placeholder for failed calculation
        
        return results
    
    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()


def calculate_fractal_chunk(chunk_data: Tuple) -> np.ndarray:
    """
    Calculate fractal for a specific chunk of the image.
    This is a standalone function that can be pickled for multiprocessing.
    
    Args:
        chunk_data: Tuple containing (generator, parameters, y_start, y_end, x_coords, y_coords)
        
    Returns:
        numpy array with iteration data for the chunk
    """
    generator, parameters, y_start, y_end, x_coords, y_coords = chunk_data
    
    height = y_end - y_start
    width = len(x_coords)
    chunk_result = np.zeros((height, width), dtype=int)
    
    for i, y in enumerate(y_coords[y_start:y_end]):
        for j, x in enumerate(x_coords):
            # This would be implemented by specific generators
            # For now, this is a placeholder structure
            pass
    
    return chunk_result