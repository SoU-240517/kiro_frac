"""
Base controller classes for the Fractal Editor application.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from ..services.error_handling import ErrorHandlingService
from ..models.data_models import AppSettings, FractalParameters, FractalResult


class BaseController(ABC):
    """Abstract base class for all controllers."""

    def __init__(self):
        """Initialize the base controller."""
        self.error_service = ErrorHandlingService()
        self._initialized = False

    @abstractmethod
    def initialize(self) -> None:
        """Initialize the controller."""
        pass

    @property
    def is_initialized(self) -> bool:
        """Check if the controller is initialized."""
        return self._initialized


class FractalController(BaseController):
    """Controller for fractal-specific operations."""

    def __init__(self):
        """Initialize the fractal controller."""
        super().__init__()
        self.current_parameters: Optional[FractalParameters] = None
        self.last_result: Optional[FractalResult] = None

    def initialize(self) -> None:
        """Initialize the fractal controller."""
        try:
            self.error_service.logger.info(
                "Initializing Fractal Controller...")
            self._initialized = True
            self.error_service.logger.info(
                "Fractal Controller initialized successfully")
        except Exception as e:
            self.error_service.handle_general_error(
                e, "fractal controller initialization")
            raise

    def set_parameters(self, parameters: FractalParameters) -> None:
        """Set the current fractal parameters."""
        self.current_parameters = parameters

    def get_parameters(self) -> Optional[FractalParameters]:
        """Get the current fractal parameters."""
        return self.current_parameters

    def set_result(self, result: FractalResult) -> None:
        """Set the last calculation result."""
        self.last_result = result

    def get_result(self) -> Optional[FractalResult]:
        """Get the last calculation result."""
        return self.last_result


class UIController(BaseController):
    """Controller for UI-related operations."""

    def __init__(self):
        """Initialize the UI controller."""
        super().__init__()
        self.ui_state: Dict[str, Any] = {}

    def initialize(self) -> None:
        """Initialize the UI controller."""
        try:
            self.error_service.logger.info("Initializing UI Controller...")
            self._setup_default_ui_state()
            self._initialized = True
            self.error_service.logger.info(
                "UI Controller initialized successfully")
        except Exception as e:
            self.error_service.handle_general_error(
                e, "UI controller initialization")
            raise

    def _setup_default_ui_state(self) -> None:
        """Set up default UI state."""
        self.ui_state = {
            'window_size': (1024, 768),
            'current_fractal_type': 'mandelbrot',
            'zoom_level': 1.0,
            'pan_offset': (0.0, 0.0),
            'color_palette': 'rainbow',
            'show_parameters_panel': True,
            'show_color_panel': True
        }

    def get_ui_state(self, key: str) -> Any:
        """Get a UI state value."""
        return self.ui_state.get(key)

    def set_ui_state(self, key: str, value: Any) -> None:
        """Set a UI state value."""
        self.ui_state[key] = value

    def update_ui_state(self, updates: Dict[str, Any]) -> None:
        """Update multiple UI state values."""
        self.ui_state.update(updates)


class MainController(BaseController):
    """Main controller for the application."""

    def __init__(self):
        """Initialize the main controller."""
        self.error_service = ErrorHandlingService()
        self.settings = AppSettings()
        self._initialized = False

    def initialize(self) -> None:
        """Initialize the application."""
        try:
            self.error_service.logger.info("Initializing Fractal Editor...")

            # Validate core interfaces are available
            self._validate_core_interfaces()

            # Set up default settings
            self._setup_default_settings()

            self._initialized = True
            self.error_service.logger.info(
                "Fractal Editor initialized successfully")

        except Exception as e:
            self.error_service.handle_general_error(e, "initialization")
            raise

    def _validate_core_interfaces(self) -> None:
        """Validate that core interfaces are properly defined."""
        from ..models.interfaces import FractalGenerator, ColorMapper, FractalPlugin
        from ..models.data_models import (
            ComplexNumber, ComplexRegion, FractalParameters,
            FractalResult, ParameterDefinition
        )

        # Verify interfaces are importable (basic validation)
        assert FractalGenerator is not None
        assert ColorMapper is not None
        assert FractalPlugin is not None

        # Verify data models are importable
        assert ComplexNumber is not None
        assert ComplexRegion is not None
        assert FractalParameters is not None
        assert FractalResult is not None
        assert ParameterDefinition is not None

        self.error_service.logger.info(
            "Core interfaces validated successfully")

    def _setup_default_settings(self) -> None:
        """Set up default application settings."""
        self.error_service.logger.info(f"Default settings configured:")
        self.error_service.logger.info(
            f"  Max iterations: {self.settings.default_max_iterations}")
        self.error_service.logger.info(
            f"  Image size: {self.settings.default_image_size}")
        self.error_service.logger.info(
            f"  Thread count: {self.settings.thread_count}")

    @property
    def is_initialized(self) -> bool:
        """Check if the controller is initialized."""
        return self._initialized
