"""
Main entry point for the Fractal Editor application.
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fractal_editor.controllers.base import MainController
from fractal_editor.services.error_handling import ErrorHandlingService

# 追加: PyQt6のインポート
from PyQt6.QtWidgets import QApplication
from fractal_editor.ui.main_window import MainWindow

def main():
    """Main application entry point."""
    try:
        # Initialize error handling service
        error_service = ErrorHandlingService()

        # Initialize main controller
        main_controller = MainController()
        main_controller.initialize()

        print("フラクタル エディターが正常に初期化されました。")
        print("コアインターフェースとプロジェクト構造が準備完了です。")
        print("フラクタル生成の準備が整いました。")

        # --- ここからGUI起動 ---
        app = QApplication(sys.argv)
        window = MainWindow()
        window.show()
        return app.exec()
        # --- ここまでGUI起動 ---

    except Exception as e:
        print(f"フラクタル エディターの初期化に失敗しました: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
