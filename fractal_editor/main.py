"""
Main entry point for the Fractal Editor application.
"""
import sys
import os
from .controllers.base import MainController
from .services.error_handling import ErrorHandlingService

# 追加: PyQt6のインポート
from PyQt6.QtWidgets import QApplication
from .ui.main_window import MainWindow

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

        # --- ここからGUI起動 ---
        app = QApplication(sys.argv)
        window = MainWindow()
        window.show()
        return app.exec()
        # --- ここまでGUI起動 ---

    except Exception as e:
        print(f"Failed to initialize Fractal Editor: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
