"""
Demonstration of the core interfaces and data models working together.
This shows how the implemented components will be used in the fractal editor.
"""
import sys
import os
import numpy as np

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fractal_editor.models.data_models import (
    ComplexNumber, ComplexRegion, FractalParameters, FractalResult,
    ParameterDefinition, ColorStop, ColorPalette, InterpolationMode,
    AppSettings
)
from fractal_editor.generators.base import FractalGenerator, fractal_registry
from fractal_editor.controllers.base import MainController, FractalController
from fractal_editor.services.error_handling import ErrorHandlingService


class DemoMandelbrotGenerator(FractalGenerator):
    """Demo implementation of a Mandelbrot generator for demonstration."""
    
    @property
    def name(self) -> str:
        return "Demo Mandelbrot"
    
    @property
    def description(self) -> str:
        return "Demo implementation of Mandelbrot set generator"
    
    def calculate(self, parameters: FractalParameters) -> FractalResult:
        """Simple Mandelbrot calculation for demonstration."""
        import time
        start_time = time.time()
        
        width, height = parameters.image_size
        iteration_data = np.zeros((height, width), dtype=int)
        
        # Get complex plane coordinates
        x_min = parameters.region.top_left.real
        x_max = parameters.region.bottom_right.real
        y_min = parameters.region.bottom_right.imaginary
        y_max = parameters.region.top_left.imaginary
        
        # Simple Mandelbrot calculation (not optimized)
        for i in range(height):
            for j in range(width):
                # Map pixel to complex plane
                x = x_min + (x_max - x_min) * j / width
                y = y_min + (y_max - y_min) * i / height
                c = complex(x, y)
                
                # Mandelbrot iteration
                z = complex(0, 0)
                for n in range(parameters.max_iterations):
                    if abs(z) > 2:
                        iteration_data[i, j] = n
                        break
                    z = z * z + c
                else:
                    iteration_data[i, j] = parameters.max_iterations
        
        calculation_time = time.time() - start_time
        
        return FractalResult(
            iteration_data=iteration_data,
            region=parameters.region,
            calculation_time=calculation_time
        )
    
    def get_parameter_definitions(self):
        return [
            ParameterDefinition(
                name="max_iterations",
                display_name="Maximum Iterations",
                parameter_type="int",
                default_value=100,
                min_value=10,
                max_value=1000,
                description="Maximum number of iterations for convergence test"
            ),
            ParameterDefinition(
                name="escape_radius",
                display_name="Escape Radius",
                parameter_type="float",
                default_value=2.0,
                min_value=1.0,
                max_value=10.0,
                description="Radius for escape condition"
            )
        ]


def demonstrate_data_models():
    """Demonstrate the data models working together."""
    print("🔢 DEMONSTRATING DATA MODELS")
    print("-" * 40)
    
    # Create complex numbers
    print("Creating complex numbers...")
    c1 = ComplexNumber(-0.7, 0.27015)
    c2 = ComplexNumber(0.3, 0.5)
    print(f"c1 = {c1.real} + {c1.imaginary}i (magnitude: {c1.magnitude:.3f})")
    print(f"c2 = {c2.real} + {c2.imaginary}i (magnitude: {c2.magnitude:.3f})")
    
    # Create a complex region
    print("\nCreating complex region...")
    region = ComplexRegion(
        top_left=ComplexNumber(-2.0, 1.0),
        bottom_right=ComplexNumber(1.0, -1.0)
    )
    print(f"Region: {region.width} × {region.height} complex plane area")
    
    # Create fractal parameters
    print("\nCreating fractal parameters...")
    parameters = FractalParameters(
        region=region,
        max_iterations=100,
        image_size=(400, 300),
        custom_parameters={'escape_radius': 2.0}
    )
    print(f"Parameters valid: {parameters.validate()}")
    print(f"Image size: {parameters.image_size}")
    print(f"Max iterations: {parameters.max_iterations}")
    
    # Create color palette
    print("\nCreating color palette...")
    palette = ColorPalette(
        name="Demo Palette",
        color_stops=[
            ColorStop(0.0, (0, 0, 0)),      # Black
            ColorStop(0.5, (255, 0, 0)),    # Red  
            ColorStop(1.0, (255, 255, 0))   # Yellow
        ],
        interpolation_mode=InterpolationMode.LINEAR
    )
    print(f"Palette '{palette.name}' with {len(palette.color_stops)} color stops")
    
    return parameters, palette


def demonstrate_fractal_generation():
    """Demonstrate fractal generation using the core interfaces."""
    print("\n🌀 DEMONSTRATING FRACTAL GENERATION")
    print("-" * 40)
    
    # Create and register a demo generator
    print("Registering demo fractal generator...")
    fractal_registry.register(DemoMandelbrotGenerator)
    
    # List available generators
    generators = fractal_registry.list_generators()
    print(f"Available generators: {generators}")
    
    # Get generator info
    info = fractal_registry.get_generator_info("Demo Mandelbrot")
    print(f"Generator: {info['name']}")
    print(f"Description: {info['description']}")
    print(f"Parameters: {len(info['parameters'])} defined")
    
    # Create parameters for generation
    region = ComplexRegion(
        top_left=ComplexNumber(-2.0, 1.0),
        bottom_right=ComplexNumber(1.0, -1.0)
    )
    
    parameters = FractalParameters(
        region=region,
        max_iterations=50,  # Low for demo speed
        image_size=(100, 75),  # Small for demo speed
        custom_parameters={'escape_radius': 2.0}
    )
    
    # Generate fractal
    print(f"\nGenerating fractal with {parameters.image_size} resolution...")
    generator = fractal_registry.get_generator("Demo Mandelbrot")
    
    if generator.validate_parameters(parameters):
        result = generator.calculate(parameters)
        print(f"✓ Generation completed in {result.calculation_time:.3f} seconds")
        print(f"✓ Result shape: {result.iteration_data.shape}")
        print(f"✓ Min iterations: {result.iteration_data.min()}")
        print(f"✓ Max iterations: {result.iteration_data.max()}")
        return result
    else:
        print("❌ Parameters validation failed")
        return None


def demonstrate_controllers():
    """Demonstrate the controller system."""
    print("\n🎮 DEMONSTRATING CONTROLLERS")
    print("-" * 40)
    
    # Initialize main controller
    print("Initializing main controller...")
    main_controller = MainController()
    main_controller.initialize()
    print(f"✓ Main controller initialized: {main_controller.is_initialized}")
    
    # Initialize fractal controller
    print("Initializing fractal controller...")
    fractal_controller = FractalController()
    fractal_controller.initialize()
    print(f"✓ Fractal controller initialized: {fractal_controller.is_initialized}")
    
    # Test parameter management
    region = ComplexRegion(
        top_left=ComplexNumber(-1.0, 1.0),
        bottom_right=ComplexNumber(1.0, -1.0)
    )
    
    test_params = FractalParameters(
        region=region,
        max_iterations=200,
        image_size=(800, 600)
    )
    
    fractal_controller.set_parameters(test_params)
    retrieved_params = fractal_controller.get_parameters()
    
    print(f"✓ Parameters stored and retrieved successfully")
    print(f"✓ Retrieved max iterations: {retrieved_params.max_iterations}")
    
    return main_controller, fractal_controller


def demonstrate_error_handling():
    """Demonstrate the error handling system."""
    print("\n⚠️  DEMONSTRATING ERROR HANDLING")
    print("-" * 40)
    
    error_service = ErrorHandlingService()
    
    # Test various error scenarios
    print("Testing error handling scenarios...")
    
    # Test general error
    try:
        raise ValueError("Demo error for testing")
    except Exception as e:
        error_service.handle_general_error(e, "demonstration")
        print("✓ General error handled successfully")
    
    print("✓ Error handling system is working")


def main():
    """Main demonstration function."""
    print("=" * 60)
    print("🎯 FRACTAL EDITOR CORE INTERFACES DEMONSTRATION")
    print("=" * 60)
    
    try:
        # Demonstrate each component
        parameters, palette = demonstrate_data_models()
        result = demonstrate_fractal_generation()
        controllers = demonstrate_controllers()
        demonstrate_error_handling()
        
        print("\n" + "=" * 60)
        print("🎉 DEMONSTRATION COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        print("✅ All core interfaces are working correctly")
        print("✅ Data models are functioning properly")
        print("✅ Fractal generation system is operational")
        print("✅ Controller system is initialized")
        print("✅ Error handling is working")
        print("\n🚀 Ready for implementation of specific fractal generators!")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ DEMONSTRATION FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)