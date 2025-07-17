"""
Main entry point for the Fractal Editor application.
"""
import sys
import os
from .controllers.base import MainController
from .services.error_handling import ErrorHandlingService


def main():
    """Main application entry point."""
    try:
        # Initialize error handling service
        error_service = ErrorHandlingService()
        
        # Initialize main controller
        main_controller = MainController()
        main_controller.initialize()
        
        print("Fractal Editor initialized successfully!")
        print("Core interfaces and project structure are ready.")
        print("Ready for fractal generation implementation.")
        
        return 0
        
    except Exception as e:
        print(f"Failed to initialize Fractal Editor: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())