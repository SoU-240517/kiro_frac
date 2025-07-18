"""
画像エクスポート機能のデモンストレーション
実際のUIを使用してエクスポート機能をテスト
"""

import sys
import os
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QLabel
from PyQt6.QtCore import QTimer

# プロジェクトのルートディレクトリをパスに追加
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fractal_editor.ui.main_window import MainWindow
from fractal_editor.generators.mandelbrot import MandelbrotGenerator
from fractal_editor.models.data_models import FractalParameters, ComplexRegion, ComplexNumber


class ExportDemoWindow(QMainWindow):
    """エクスポート機能のデモウィンドウ"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("フラクタルエディタ - エクスポート機能デモ")
        self.setGeometry(100, 100, 800, 600)
        
        # メインウィンドウを作成
        self.main_window = MainWindow()
        
        # 中央ウィジェット設定
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # 説明ラベル
        info_label = QLabel("""
🎨 フラクタルエディタ - 画像エクスポート機能デモ

このデモでは以下の機能をテストできます:
• フラクタル生成とエクスポートデータの設定
• エクスポートダイアログの表示
• PNG/JPEG形式での画像出力
• 高解像度画像生成
• カスタムレンダリング設定

下のボタンをクリックして各機能をテストしてください。
        """)
        info_label.setStyleSheet("padding: 10px; background-color: #f0f0f0; border: 1px solid #ccc;")
        layout.addWidget(info_label)
        
        # テストボタン群
        self.create_test_buttons(layout)
        
        # ステータスラベル
        self.status_label = QLabel("準備完了")
        self.status_label.setStyleSheet("padding: 5px; background-color: #e8f5e8; border: 1px solid #4caf50;")
        layout.addWidget(self.status_label)
        
        # フラクタルデータ
        self.fractal_result = None
        self.max_iterations = 100
    
    def create_test_buttons(self, layout):
        """テストボタンを作成"""
        
        # フラクタル生成ボタン
        generate_btn = QPushButton("1. フラクタルを生成")
        generate_btn.clicked.connect(self.generate_fractal)
        generate_btn.setStyleSheet("QPushButton { padding: 10px; font-size: 12px; }")
        layout.addWidget(generate_btn)
        
        # エクスポートダイアログ表示ボタン
        export_dialog_btn = QPushButton("2. エクスポートダイアログを表示")
        export_dialog_btn.clicked.connect(self.show_export_dialog)
        export_dialog_btn.setStyleSheet("QPushButton { padding: 10px; font-size: 12px; }")
        layout.addWidget(export_dialog_btn)
        
        # クイックエクスポートボタン
        quick_export_btn = QPushButton("3. クイックエクスポート (PNG)")
        quick_export_btn.clicked.connect(self.quick_export_png)
        quick_export_btn.setStyleSheet("QPushButton { padding: 10px; font-size: 12px; }")
        layout.addWidget(quick_export_btn)
        
        # 高解像度エクスポートボタン
        hires_export_btn = QPushButton("4. 高解像度エクスポート")
        hires_export_btn.clicked.connect(self.high_resolution_export)
        hires_export_btn.setStyleSheet("QPushButton { padding: 10px; font-size: 12px; }")
        layout.addWidget(hires_export_btn)
        
        # メインウィンドウ表示ボタン
        main_window_btn = QPushButton("5. メインウィンドウを表示")
        main_window_btn.clicked.connect(self.show_main_window)
        main_window_btn.setStyleSheet("QPushButton { padding: 10px; font-size: 12px; background-color: #2196f3; color: white; }")
        layout.addWidget(main_window_btn)
    
    def update_status(self, message: str):
        """ステータスを更新"""
        self.status_label.setText(f"ステータス: {message}")
        print(f"📢 {message}")
    
    def generate_fractal(self):
        """フラクタルを生成"""
        try:
            self.update_status("フラクタルを生成中...")
            
            # マンデルブロ集合を生成
            generator = MandelbrotGenerator()
            
            parameters = FractalParameters(
                region=ComplexRegion(
                    top_left=ComplexNumber(-2.0, 1.0),
                    bottom_right=ComplexNumber(1.0, -1.0)
                ),
                max_iterations=self.max_iterations,
                image_size=(300, 300),
                custom_parameters={}
            )
            
            self.fractal_result = generator.calculate(parameters)
            
            # メインウィンドウにフラクタルデータを設定
            self.main_window.set_fractal_data_for_export(self.fractal_result, self.max_iterations)
            
            self.update_status(f"フラクタル生成完了 ({self.fractal_result.iteration_data.shape})")
            
        except Exception as e:
            self.update_status(f"フラクタル生成エラー: {str(e)}")
    
    def show_export_dialog(self):
        """エクスポートダイアログを表示"""
        try:
            if self.fractal_result is None:
                self.update_status("先にフラクタルを生成してください")
                return
            
            self.update_status("エクスポートダイアログを表示中...")
            
            # エクスポートコントローラーを取得してダイアログを表示
            export_controller = self.main_window.get_export_controller()
            success = export_controller.show_export_dialog()
            
            if success:
                self.update_status("エクスポートが完了しました")
            else:
                self.update_status("エクスポートがキャンセルされました")
                
        except Exception as e:
            self.update_status(f"エクスポートダイアログエラー: {str(e)}")
    
    def quick_export_png(self):
        """クイックエクスポート（PNG）"""
        try:
            if self.fractal_result is None:
                self.update_status("先にフラクタルを生成してください")
                return
            
            self.update_status("クイックエクスポート実行中...")
            
            # デスクトップにエクスポート
            desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
            export_path = os.path.join(desktop_path, "fractal_demo_export.png")
            
            export_controller = self.main_window.get_export_controller()
            success = export_controller.quick_export(export_path, "PNG")
            
            if success:
                self.update_status(f"PNG エクスポート完了: {export_path}")
            else:
                self.update_status("PNG エクスポート失敗")
                
        except Exception as e:
            self.update_status(f"クイックエクスポートエラー: {str(e)}")
    
    def high_resolution_export(self):
        """高解像度エクスポート"""
        try:
            if self.fractal_result is None:
                self.update_status("先にフラクタルを生成してください")
                return
            
            self.update_status("高解像度エクスポート実行中...")
            
            # デスクトップにエクスポート
            desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
            export_path = os.path.join(desktop_path, "fractal_demo_hires.png")
            
            export_controller = self.main_window.get_export_controller()
            success = export_controller.quick_export(
                export_path, "PNG", high_resolution=True, scale_factor=2
            )
            
            if success:
                self.update_status(f"高解像度エクスポート完了: {export_path}")
            else:
                self.update_status("高解像度エクスポート失敗")
                
        except Exception as e:
            self.update_status(f"高解像度エクスポートエラー: {str(e)}")
    
    def show_main_window(self):
        """メインウィンドウを表示"""
        try:
            self.update_status("メインウィンドウを表示中...")
            
            # フラクタルデータが生成されている場合は設定
            if self.fractal_result is not None:
                self.main_window.set_fractal_data_for_export(self.fractal_result, self.max_iterations)
            
            self.main_window.show()
            self.main_window.raise_()
            self.main_window.activateWindow()
            
            self.update_status("メインウィンドウを表示しました（エクスポートメニューをお試しください）")
            
        except Exception as e:
            self.update_status(f"メインウィンドウ表示エラー: {str(e)}")


def main():
    """メイン関数"""
    print("🚀 フラクタルエディタ - 画像エクスポート機能デモを開始します")
    
    # QApplicationを作成
    app = QApplication(sys.argv)
    
    # デモウィンドウを作成・表示
    demo_window = ExportDemoWindow()
    demo_window.show()
    
    print("✨ デモウィンドウが表示されました")
    print("📋 以下の手順でエクスポート機能をテストしてください:")
    print("   1. 「フラクタルを生成」ボタンをクリック")
    print("   2. 「エクスポートダイアログを表示」ボタンをクリック")
    print("   3. ダイアログで設定を調整してエクスポート実行")
    print("   4. または「クイックエクスポート」ボタンで簡単エクスポート")
    print("   5. 「メインウィンドウを表示」でフル機能をテスト")
    
    # アプリケーション実行
    try:
        sys.exit(app.exec())
    except KeyboardInterrupt:
        print("\n👋 デモを終了します")
        sys.exit(0)


if __name__ == "__main__":
    main()