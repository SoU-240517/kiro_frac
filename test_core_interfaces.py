#!/usr/bin/env python3
"""
Test script to verify core interfaces and project structure.
"""
import sys
import traceback
from fractal_editor import (
    ComplexNumber, ComplexRegion, FractalParameters, FractalResult,
    ColorPalette, ColorStop, InterpolationMode, AppSettings,
    ParameterDefinition, PluginMetadata,
    FractalGenerator, ColorMapper, FractalPlugin,
    MainController, FractalController, UIController,
    ErrorHandlingService, ParallelCalculator,
    FractalCalculationException
)
from fractal_editor.generators.base import fractal_registry
from fractal_editor.plugins.base import plugin_manager
import numpy as np


def test_data_models():
    """Test core data models."""
    print("Testing data models...")
    
    # Test ComplexNumber
    c1 = ComplexNumber(3.0, 4.0)
    assert c1.magnitude == 5.0, f"Expected magnitude 5.0, got {c1.magnitude}"
    
    c2 = ComplexNumber(1.0, 2.0)
    c3 = c1 + c2
    assert c3.real == 4.0 and c3.imaginary == 6.0, "Complex addition failed"
    
    # Test ComplexRegion
    region = ComplexRegion(
        top_left=ComplexNumber(-2.0, 1.0),
        bottom_right=ComplexNumber(1.0, -1.0)
    )
    assert region.width == 3.0, f"Expected width 3.0, got {region.width}"
    assert region.height == 2.0, f"Expected height 2.0, got {region.height}"
    
    # Test FractalParameters
    params = FractalParameters(
        region=region,
        max_iterations=100,
        image_size=(800, 600)
    )
    assert params.validate(), "FractalParameters validation failed"
    
    # Test ColorPalette
    palette = ColorPalette(
        name="Test",
        color_stops=[
            ColorStop(0.0, (0, 0, 0)),
            ColorStop(1.0, (255, 255, 255))
        ]
    )
    assert len(palette.color_stops) == 2, "ColorPalette creation failed"
    
    # Test ParameterDefinition
    param_def = ParameterDefinition(
        name="test_param",
        display_name="Test Parameter",
        parameter_type="float",
        default_value=1.0,
        min_value=0.0,
        max_value=10.0
    )
    assert param_def.validate_value(5.0), "Parameter validation failed"
    assert not param_def.validate_value(-1.0), "Parameter validation should have failed"
    
    print("✓ Data models test passed")


def test_generator_interface():
    """Test fractal generator interface."""
    print("Testing generator interface...")
    
    class TestGenerator(FractalGenerator):
        @property
        def name(self) -> str:
            return "Test Generator"
        
        @property
        def description(self) -> str:
            return "A test fractal generator"
        
        def calculate(self, parameters: FractalParameters) -> FractalResult:
            # Create dummy result
            width, height = parameters.image_size
            iteration_data = np.zeros((height, width), dtype=int)
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
    
    # Test generator
    generator = TestGenerator()
    assert generator.name == "Test Generator"
    
    # Test registry
    fractal_registry.register(TestGenerator)
    assert "Test Generator" in fractal_registry.list_generators()
    
    retrieved_generator = fractal_registry.get_generator("Test Generator")
    assert retrieved_generator.name == "Test Generator"
    
    print("✓ Generator interface test passed")


def test_plugin_system():
    """Test plugin system."""
    print("Testing plugin system...")
    
    class TestPlugin(FractalPlugin):
        @property
        def metadata(self) -> PluginMetadata:
            return PluginMetadata(
                name="Test Plugin",
                version="1.0.0",
                author="Test Author",
                description="A test plugin"
            )
        
        def create_generator(self) -> FractalGenerator:
            class PluginGenerator(FractalGenerator):
                @property
                def name(self) -> str:
                    return "Plugin Generator"
                
                @property
                def description(self) -> str:
                    return "Generator from plugin"
                
                def calculate(self, parameters: FractalParameters) -> FractalResult:
                    width, height = parameters.image_size
                    iteration_data = np.ones((height, width), dtype=int)
                    return FractalResult(
                        iteration_data=iteration_data,
                        region=parameters.region,
                        calculation_time=0.1
                    )
                
                def get_parameter_definitions(self):
                    return []
            
            return PluginGenerator()
    
    # Test plugin loading
    success = plugin_manager.load_plugin(TestPlugin)
    assert success, "Plugin loading failed"
    
    loaded_plugins = plugin_manager.get_loaded_plugins()
    assert "Test Plugin" in loaded_plugins, "Plugin not in loaded list"
    
    plugin_info = plugin_manager.get_plugin_info("Test Plugin")
    assert plugin_info.name == "Test Plugin", "Plugin info incorrect"
    
    print("✓ Plugin system test passed")


def test_controllers():
    """Test controller classes."""
    print("Testing controllers...")
    
    # Test MainController
    main_controller = MainController()
    main_controller.initialize()
    
    # Test FractalController
    fractal_controller = main_controller.fractal_controller
    assert fractal_controller is not None, "FractalController not initialized"
    
    # Test UIController
    ui_controller = main_controller.ui_controller
    assert ui_controller is not None, "UIController not initialized"
    
    # Test event handling
    test_event_handled = False
    
    def test_handler(event_data):
        nonlocal test_event_handled
        test_event_handled = True
    
    ui_controller.register_event_handler("test_event", test_handler)
    ui_controller.handle_event("test_event", {})
    
    assert test_event_handled, "Event handler not called"
    
    print("✓ Controllers test passed")


def test_services():
    """Test service classes."""
    print("Testing services...")
    
    # Test ErrorHandlingService
    error_service = ErrorHandlingService()
    
    # Test error handling (should not raise exceptions)
    try:
        error_service.handle_generic_error(Exception("Test error"), "test context")
        error_service.handle_formula_error(Exception("Test formula error"))
    except Exception as e:
        assert False, f"Error service should handle exceptions gracefully: {e}"
    
    # Test ParallelCalculator
    calc = ParallelCalculator(max_workers=2)
    calc.start()
    assert calc.max_workers == 2, "ParallelCalculator max_workers not set correctly"
    calc.stop()
    
    print("✓ Services test passed")


def main():
    """Run all tests."""
    print("Running core interface tests...\n")
    
    try:
        test_data_models()
        test_generator_interface()
        test_plugin_system()
        test_controllers()
        test_services()
        
        print("\n🎉 All tests passed! Core interfaces and project structure are working correctly.")
        return 0
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())