"""
Verification test for Task 1: Project structure and core interfaces setup.
This test verifies that all core interfaces and data models are properly implemented.
"""
import sys
import os
import numpy as np
from datetime import datetime

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fractal_editor.models.interfaces import ColorMapper, FractalPlugin, PluginMetadata
from fractal_editor.generators.base import FractalGenerator
from fractal_editor.models.data_models import (
    ComplexNumber, ComplexRegion, FractalParameters, FractalResult, 
    ParameterDefinition, ColorStop, ColorPalette, InterpolationMode,
    AppSettings, FractalProject
)
from fractal_editor.generators.base import FractalGeneratorRegistry, fractal_registry
from fractal_editor.controllers.base import MainController, FractalController, UIController
from fractal_editor.services.error_handling import (
    ErrorHandlingService, FractalCalculationException, 
    FormulaValidationError, FormulaEvaluationError
)


def test_complex_number():
    """Test ComplexNumber data model."""
    print("Testing ComplexNumber...")
    
    # Test creation
    c1 = ComplexNumber(3.0, 4.0)
    assert c1.real == 3.0
    assert c1.imaginary == 4.0
    
    # Test magnitude
    assert c1.magnitude == 5.0  # 3-4-5 triangle
    
    # Test square
    c2 = c1.square()  # (3+4i)^2 = 9 + 24i - 16 = -7 + 24i
    assert c2.real == -7.0
    assert c2.imaginary == 24.0
    
    # Test addition
    c3 = ComplexNumber(1.0, 2.0)
    c4 = c1 + c3
    assert c4.real == 4.0
    assert c4.imaginary == 6.0
    
    # Test conversion to complex
    complex_val = c1.to_complex()
    assert complex_val == complex(3.0, 4.0)
    
    print("✓ ComplexNumber tests passed")


def test_complex_region():
    """Test ComplexRegion data model."""
    print("Testing ComplexRegion...")
    
    top_left = ComplexNumber(-2.0, 1.0)
    bottom_right = ComplexNumber(1.0, -1.0)
    region = ComplexRegion(top_left, bottom_right)
    
    assert region.width == 3.0  # 1.0 - (-2.0)
    assert region.height == 2.0  # 1.0 - (-1.0)
    
    print("✓ ComplexRegion tests passed")


def test_fractal_parameters():
    """Test FractalParameters data model."""
    print("Testing FractalParameters...")
    
    region = ComplexRegion(
        ComplexNumber(-2.0, 1.0),
        ComplexNumber(1.0, -1.0)
    )
    
    params = FractalParameters(
        region=region,
        max_iterations=1000,
        image_size=(800, 600),
        custom_parameters={'c': complex(0.3, 0.5)}
    )
    
    assert params.validate() == True
    
    # Test invalid parameters
    invalid_params = FractalParameters(
        region=region,
        max_iterations=0,  # Invalid
        image_size=(800, 600)
    )
    assert invalid_params.validate() == False
    
    print("✓ FractalParameters tests passed")


def test_parameter_definition():
    """Test ParameterDefinition data model."""
    print("Testing ParameterDefinition...")
    
    # Test integer parameter
    int_param = ParameterDefinition(
        name="max_iter",
        display_name="Maximum Iterations",
        parameter_type="int",
        default_value=1000,
        min_value=1,
        max_value=10000
    )
    
    assert int_param.validate_value(500) == True
    assert int_param.validate_value(0) == False  # Below minimum
    assert int_param.validate_value(20000) == False  # Above maximum
    assert int_param.validate_value("invalid") == False  # Wrong type
    
    # Test float parameter
    float_param = ParameterDefinition(
        name="zoom",
        display_name="Zoom Level",
        parameter_type="float",
        default_value=1.0,
        min_value=0.1,
        max_value=100.0
    )
    
    assert float_param.validate_value(2.5) == True
    assert float_param.validate_value(0.05) == False  # Below minimum
    
    print("✓ ParameterDefinition tests passed")


def test_color_palette():
    """Test ColorPalette and related models."""
    print("Testing ColorPalette...")
    
    stops = [
        ColorStop(0.0, (0, 0, 0)),      # Black
        ColorStop(0.5, (255, 0, 0)),    # Red
        ColorStop(1.0, (255, 255, 255)) # White
    ]
    
    palette = ColorPalette(
        name="Test Palette",
        color_stops=stops,
        interpolation_mode=InterpolationMode.LINEAR
    )
    
    assert palette.name == "Test Palette"
    assert len(palette.color_stops) == 3
    assert palette.interpolation_mode == InterpolationMode.LINEAR
    
    print("✓ ColorPalette tests passed")


def test_app_settings():
    """Test AppSettings data model."""
    print("Testing AppSettings...")
    
    settings = AppSettings()
    
    assert settings.default_max_iterations == 1000
    assert settings.default_image_size == (800, 600)
    assert settings.thread_count > 0
    assert settings.enable_anti_aliasing == True
    
    print("✓ AppSettings tests passed")


def test_fractal_result():
    """Test FractalResult data model."""
    print("Testing FractalResult...")
    
    # Create test data
    iteration_data = np.zeros((100, 100), dtype=int)
    region = ComplexRegion(
        ComplexNumber(-2.0, 1.0),
        ComplexNumber(1.0, -1.0)
    )
    
    result = FractalResult(
        iteration_data=iteration_data,
        region=region,
        calculation_time=1.5
    )
    
    assert result.iteration_data.shape == (100, 100)
    assert result.calculation_time == 1.5
    assert result.region.width == 3.0
    
    print("✓ FractalResult tests passed")


def test_plugin_metadata():
    """Test PluginMetadata data model."""
    print("Testing PluginMetadata...")
    
    metadata = PluginMetadata(
        name="Test Plugin",
        version="1.0.0",
        author="Test Author",
        description="A test plugin"
    )
    
    assert metadata.name == "Test Plugin"
    assert metadata.dependencies == []  # Default empty list
    
    print("✓ PluginMetadata tests passed")


def test_fractal_generator_registry():
    """Test FractalGeneratorRegistry."""
    print("Testing FractalGeneratorRegistry...")
    
    # Create a test generator
    class TestGenerator(FractalGenerator):
        @property
        def name(self) -> str:
            return "Test Generator"
        
        @property
        def description(self) -> str:
            return "A test fractal generator"
        
        def calculate(self, parameters: FractalParameters) -> FractalResult:
            # Simple test implementation
            iteration_data = np.ones(parameters.image_size[::-1], dtype=int)
            return FractalResult(
                iteration_data=iteration_data,
                region=parameters.region,
                calculation_time=0.1
            )
        
        def get_parameter_definitions(self):
            return [
                ParameterDefinition(
                    name="test_param",
                    display_name="Test Parameter",
                    parameter_type="float",
                    default_value=1.0
                )
            ]
    
    # Test registry
    registry = FractalGeneratorRegistry()
    registry.register(TestGenerator)
    
    assert "Test Generator" in registry.list_generators()
    
    generator = registry.get_generator("Test Generator")
    assert generator.name == "Test Generator"
    
    info = registry.get_generator_info("Test Generator")
    assert info['name'] == "Test Generator"
    assert len(info['parameters']) == 1
    
    print("✓ FractalGeneratorRegistry tests passed")


def test_controllers():
    """Test controller classes."""
    print("Testing Controllers...")
    
    # Test MainController
    main_controller = MainController()
    assert not main_controller.is_initialized
    
    main_controller.initialize()
    assert main_controller.is_initialized
    
    # Test FractalController
    fractal_controller = FractalController()
    fractal_controller.initialize()
    assert fractal_controller.is_initialized
    
    # Test UIController
    ui_controller = UIController()
    ui_controller.initialize()
    assert ui_controller.is_initialized
    
    # Test UI state management
    ui_controller.set_ui_state('test_key', 'test_value')
    assert ui_controller.get_ui_state('test_key') == 'test_value'
    
    print("✓ Controllers tests passed")


def test_error_handling():
    """Test error handling service."""
    print("Testing ErrorHandlingService...")
    
    error_service = ErrorHandlingService()
    
    # Test that it doesn't crash when handling errors
    try:
        region = ComplexRegion(
            ComplexNumber(-2.0, 1.0),
            ComplexNumber(1.0, -1.0)
        )
        params = FractalParameters(region, 1000, (800, 600))
        
        calc_error = FractalCalculationException("Test error", params, "test_stage")
        error_service.handle_calculation_error(calc_error)
        
        formula_error = FormulaValidationError("Test formula error")
        error_service.handle_formula_error(formula_error)
        
        general_error = Exception("Test general error")
        error_service.handle_general_error(general_error, "test_context")
        
    except Exception as e:
        assert False, f"Error handling should not raise exceptions: {e}"
    
    print("✓ ErrorHandlingService tests passed")


def test_interfaces_are_abstract():
    """Test that abstract interfaces cannot be instantiated."""
    print("Testing abstract interfaces...")
    
    # These should all raise TypeError when trying to instantiate
    try:
        FractalGenerator()
        assert False, "FractalGenerator should be abstract"
    except TypeError:
        pass
    
    try:
        ColorMapper()
        assert False, "ColorMapper should be abstract"
    except TypeError:
        pass
    
    try:
        FractalPlugin()
        assert False, "FractalPlugin should be abstract"
    except TypeError:
        pass
    
    print("✓ Abstract interfaces tests passed")


def run_all_tests():
    """Run all verification tests."""
    print("=" * 60)
    print("TASK 1 VERIFICATION: Project Structure and Core Interfaces")
    print("=" * 60)
    
    try:
        test_complex_number()
        test_complex_region()
        test_fractal_parameters()
        test_parameter_definition()
        test_color_palette()
        test_app_settings()
        test_fractal_result()
        test_plugin_metadata()
        test_fractal_generator_registry()
        test_controllers()
        test_error_handling()
        test_interfaces_are_abstract()
        
        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED!")
        print("Task 1 implementation is complete and verified.")
        print("Core interfaces and project structure are ready.")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)