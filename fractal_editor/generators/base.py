"""
Abstract base classes and interfaces for fractal generators.
Defines the core interface that all fractal generators must implement.
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any
from ..models.data_models import FractalParameters, FractalResult, ParameterDefinition


class FractalGenerator(ABC):
    """Abstract base class for all fractal generators."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Get the name of this fractal generator."""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Get a description of this fractal generator."""
        pass
    
    @abstractmethod
    def calculate(self, parameters: FractalParameters) -> FractalResult:
        """
        Calculate the fractal with the given parameters.
        
        Args:
            parameters: The parameters for fractal generation
            
        Returns:
            FractalResult containing the calculated iteration data
            
        Raises:
            FractalCalculationException: If calculation fails
        """
        pass
    
    @abstractmethod
    def get_parameter_definitions(self) -> List[ParameterDefinition]:
        """
        Get the parameter definitions for this fractal generator.
        
        Returns:
            List of parameter definitions that this generator accepts
        """
        pass
    
    def validate_parameters(self, parameters: FractalParameters) -> bool:
        """
        Validate that the given parameters are suitable for this generator.
        
        Args:
            parameters: The parameters to validate
            
        Returns:
            True if parameters are valid, False otherwise
        """
        # Basic validation
        try:
            parameters.validate()
        except Exception:
            return False
        
        # Check custom parameters against parameter definitions
        param_defs = {pd.name: pd for pd in self.get_parameter_definitions()}
        
        for param_name, param_value in parameters.custom_parameters.items():
            if param_name in param_defs:
                if not param_defs[param_name].validate_value(param_value):
                    return False
        
        return True
    
    def get_default_parameters(self) -> Dict[str, Any]:
        """
        Get default values for this generator's custom parameters.
        
        Returns:
            Dictionary of parameter names to default values
        """
        return {pd.name: pd.default_value for pd in self.get_parameter_definitions()}


class ColorMapper(ABC):
    """Abstract base class for color mapping strategies."""
    
    @abstractmethod
    def map_iteration_to_color(self, iteration: int, max_iteration: int) -> tuple[int, int, int]:
        """
        Map an iteration count to an RGB color.
        
        Args:
            iteration: The iteration count (0 to max_iteration)
            max_iteration: The maximum iteration count
            
        Returns:
            RGB color tuple (r, g, b) with values 0-255
        """
        pass
    
    @abstractmethod
    def set_palette(self, palette: 'ColorPalette') -> None:
        """
        Set the color palette for this mapper.
        
        Args:
            palette: The color palette to use
        """
        pass


class FractalGeneratorRegistry:
    """Registry for managing available fractal generators."""
    
    def __init__(self):
        self._generators: Dict[str, type[FractalGenerator]] = {}
    
    def register(self, generator_class: type[FractalGenerator]) -> None:
        """
        Register a fractal generator class.
        
        Args:
            generator_class: The generator class to register
        """
        # Create a temporary instance to get the name
        temp_instance = generator_class()
        self._generators[temp_instance.name] = generator_class
    
    def unregister(self, generator_class: type[FractalGenerator]) -> bool:
        """
        Unregister a fractal generator class.
        
        Args:
            generator_class: The generator class to unregister
            
        Returns:
            True if the generator was unregistered, False if it wasn't registered
        """
        try:
            # Create a temporary instance to get the name
            temp_instance = generator_class()
            name = temp_instance.name
            
            if name in self._generators:
                del self._generators[name]
                return True
            return False
        except Exception:
            return False
    
    def get_generator(self, name: str) -> FractalGenerator:
        """
        Get a fractal generator instance by name.
        
        Args:
            name: The name of the generator
            
        Returns:
            An instance of the requested generator
            
        Raises:
            KeyError: If the generator is not registered
        """
        if name not in self._generators:
            raise KeyError(f"Fractal generator '{name}' is not registered")
        
        return self._generators[name]()
    
    def list_generators(self) -> List[str]:
        """
        Get a list of all registered generator names.
        
        Returns:
            List of generator names
        """
        return list(self._generators.keys())
    
    def get_generator_info(self, name: str) -> Dict[str, Any]:
        """
        Get information about a registered generator.
        
        Args:
            name: The name of the generator
            
        Returns:
            Dictionary with generator information
        """
        if name not in self._generators:
            raise KeyError(f"Fractal generator '{name}' is not registered")
        
        generator = self._generators[name]()
        return {
            'name': generator.name,
            'description': generator.description,
            'parameters': generator.get_parameter_definitions(),
            'default_values': generator.get_default_parameters()
        }


# Global registry instance
fractal_registry = FractalGeneratorRegistry()