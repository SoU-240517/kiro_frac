"""
画像エクスポート機能のテスト
"""

import unittest
import numpy as np
import os
import tempfile
from PIL import Image
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer
import sys

from fractal_editor.ui.export_dialog import ImageExportDialog
from fractal_editor.controllers.export_controller import ExportController
from fractal_editor.services.image_renderer import RenderingEngine, RenderSettings
from fractal_editor.models.data_models import FractalResult, ComplexRegion, ComplexNumber


class TestImageExport(unittest.TestCase):
    """画像エクスポート機能のテストクラス"""
    
    @classmethod
    def setUpClass(cls):
        """テストクラスの初期化"""
        # QApplicationが存在しない場合は作成
        if not QApplication.instance():
            cls.app = QApplication(sys.argv)
        else:
            cls.app = QApplication.instance()
    
    def setUp(self):
        """各テストの前処理"""
        # テスト用のフラクタルデータを作成
        self.test_iteration_data = self._create_test_fractal_data()
        self.max_iterations = 100
        
        # テスト用の一時ディレクトリ
        self.temp_dir = tempfile.mkdtemp()
        
        # FractalResultオブジェクトを作成
        self.fractal_result = FractalResult(
            iteration_data=self.test_iteration_data,
            region=ComplexRegion(
                top_left=ComplexNumber(-2.0, 1.0),
                bottom_right=ComplexNumber(1.0, -1.0)
            ),
            calculation_time=1.5
        )
    
    def tearDown(self):
        """各テストの後処理"""
        # 一時ファイルを削除
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def _create_test_fractal_data(self) -> np.ndarray:
        """テスト用のフラクタルデータを作成"""
        # 簡単なテストパターンを作成
        width, height = 100, 100
        data = np.zeros((height, width), dtype=int)
        
        # 中心から外側に向かって値が増加するパターン
        center_x, center_y = width // 2, height // 2
        for y in range(height):
            for x in range(width):
                distance = ((x - center_x) ** 2 + (y - center_y) ** 2) ** 0.5
                data[y, x] = min(int(distance), 99)
        
        return data
    
    def test_rendering_engine_initialization(self):
        """レンダリングエンジンの初期化テスト"""
        engine = RenderingEngine()
        self.assertIsNotNone(engine)
        
        # デフォルト設定の取得
        settings = engine.get_render_settings()
        self.assertIsInstance(settings, RenderSettings)
        self.assertTrue(settings.anti_aliasing)
        self.assertEqual(settings.brightness, 1.0)
        self.assertEqual(settings.contrast, 1.0)
        self.assertEqual(settings.gamma, 1.0)
    
    def test_png_export(self):
        """PNG形式でのエクスポートテスト"""
        engine = RenderingEngine()
        filepath = os.path.join(self.temp_dir, "test_fractal.png")
        
        # PNG形式でエクスポート
        engine.export_image(
            iteration_data=self.test_iteration_data,
            max_iterations=self.max_iterations,
            filepath=filepath,
            high_resolution=False
        )
        
        # ファイルが作成されたことを確認
        self.assertTrue(os.path.exists(filepath))
        
        # 画像ファイルとして読み込めることを確認
        with Image.open(filepath) as img:
            self.assertEqual(img.format, 'PNG')
            self.assertEqual(img.size, (100, 100))  # テストデータのサイズ
    
    def test_jpeg_export(self):
        """JPEG形式でのエクスポートテスト"""
        engine = RenderingEngine()
        filepath = os.path.join(self.temp_dir, "test_fractal.jpg")
        
        # JPEG形式でエクスポート
        engine.export_image(
            iteration_data=self.test_iteration_data,
            max_iterations=self.max_iterations,
            filepath=filepath,
            high_resolution=False,
            quality=85
        )
        
        # ファイルが作成されたことを確認
        self.assertTrue(os.path.exists(filepath))
        
        # 画像ファイルとして読み込めることを確認
        with Image.open(filepath) as img:
            self.assertEqual(img.format, 'JPEG')
            self.assertEqual(img.size, (100, 100))
    
    def test_high_resolution_export(self):
        """高解像度エクスポートテスト"""
        engine = RenderingEngine()
        filepath = os.path.join(self.temp_dir, "test_fractal_hires.png")
        scale_factor = 2
        
        # 高解像度でエクスポート
        engine.export_image(
            iteration_data=self.test_iteration_data,
            max_iterations=self.max_iterations,
            filepath=filepath,
            high_resolution=True,
            scale_factor=scale_factor
        )
        
        # ファイルが作成されたことを確認
        self.assertTrue(os.path.exists(filepath))
        
        # 画像サイズが拡大されていることを確認
        with Image.open(filepath) as img:
            expected_size = (100 * scale_factor, 100 * scale_factor)
            self.assertEqual(img.size, expected_size)
    
    def test_render_settings(self):
        """レンダリング設定のテスト"""
        engine = RenderingEngine()
        filepath = os.path.join(self.temp_dir, "test_fractal_settings.png")
        
        # カスタム設定を作成
        settings = RenderSettings(
            anti_aliasing=True,
            brightness=1.2,
            contrast=1.1,
            gamma=0.9
        )
        
        # カスタム設定でエクスポート
        engine.export_image(
            iteration_data=self.test_iteration_data,
            max_iterations=self.max_iterations,
            filepath=filepath,
            settings=settings
        )
        
        # ファイルが作成されたことを確認
        self.assertTrue(os.path.exists(filepath))
    
    def test_export_controller_initialization(self):
        """エクスポートコントローラーの初期化テスト"""
        controller = ExportController()
        controller.initialize()
        
        self.assertTrue(controller.is_initialized)
        self.assertIsNotNone(controller.rendering_engine)
        self.assertEqual(len(controller.get_export_history()), 0)
    
    def test_export_controller_fractal_data_setting(self):
        """エクスポートコントローラーのフラクタルデータ設定テスト"""
        controller = ExportController()
        controller.initialize()
        
        # フラクタルデータを設定
        controller.set_fractal_data(self.fractal_result, self.max_iterations)
        
        self.assertIsNotNone(controller.current_fractal_result)
        self.assertEqual(controller.current_max_iterations, self.max_iterations)
        self.assertTrue(np.array_equal(
            controller.current_fractal_result.iteration_data,
            self.test_iteration_data
        ))
    
    def test_quick_export(self):
        """クイックエクスポート機能のテスト"""
        controller = ExportController()
        controller.initialize()
        controller.set_fractal_data(self.fractal_result, self.max_iterations)
        
        filepath = os.path.join(self.temp_dir, "quick_export.png")
        
        # クイックエクスポート実行
        success = controller.quick_export(filepath, "PNG")
        
        self.assertTrue(success)
        self.assertTrue(os.path.exists(filepath))
        
        # エクスポート履歴に追加されていることを確認
        history = controller.get_export_history()
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]['filepath'], filepath)
    
    def test_export_settings_validation(self):
        """エクスポート設定の検証テスト"""
        controller = ExportController()
        controller.initialize()
        
        # 有効な設定
        valid_settings = {
            'filepath': '/path/to/file.png',
            'format': 'PNG',
            'high_resolution': False,
            'width': 1920,
            'height': 1080,
            'quality': 95,
            'anti_aliasing': True,
            'brightness': 1.0,
            'contrast': 1.0,
            'gamma': 1.0
        }
        
        is_valid, error_msg = controller.validate_export_settings(valid_settings)
        self.assertTrue(is_valid)
        self.assertEqual(error_msg, "")
        
        # 無効な設定（ファイルパスなし）
        invalid_settings = valid_settings.copy()
        invalid_settings['filepath'] = ''
        
        is_valid, error_msg = controller.validate_export_settings(invalid_settings)
        self.assertFalse(is_valid)
        self.assertIn("ファイルパス", error_msg)
        
        # 無効な設定（解像度範囲外）
        invalid_settings = valid_settings.copy()
        invalid_settings['width'] = 50  # 最小値100未満
        
        is_valid, error_msg = controller.validate_export_settings(invalid_settings)
        self.assertFalse(is_valid)
        self.assertIn("解像度", error_msg)
    
    def test_supported_formats(self):
        """サポートされているファイル形式のテスト"""
        controller = ExportController()
        controller.initialize()
        
        formats = controller.get_supported_formats()
        
        self.assertIsInstance(formats, list)
        self.assertGreater(len(formats), 0)
        
        # PNG形式が含まれていることを確認
        png_found = any(fmt['name'] == 'PNG' for fmt in formats)
        self.assertTrue(png_found)
        
        # JPEG形式が含まれていることを確認
        jpeg_found = any(fmt['name'] == 'JPEG' for fmt in formats)
        self.assertTrue(jpeg_found)
    
    def test_export_history_management(self):
        """エクスポート履歴管理のテスト"""
        controller = ExportController()
        controller.initialize()
        controller.set_fractal_data(self.fractal_result, self.max_iterations)
        
        # 複数回エクスポート
        for i in range(3):
            filepath = os.path.join(self.temp_dir, f"export_{i}.png")
            controller.quick_export(filepath, "PNG")
        
        # 履歴の確認
        history = controller.get_export_history()
        self.assertEqual(len(history), 3)
        
        # 履歴のクリア
        controller.clear_export_history()
        history = controller.get_export_history()
        self.assertEqual(len(history), 0)


class TestExportDialogComponents(unittest.TestCase):
    """エクスポートダイアログのコンポーネントテスト"""
    
    @classmethod
    def setUpClass(cls):
        """テストクラスの初期化"""
        if not QApplication.instance():
            cls.app = QApplication(sys.argv)
        else:
            cls.app = QApplication.instance()
    
    def setUp(self):
        """各テストの前処理"""
        self.test_iteration_data = self._create_test_fractal_data()
        self.max_iterations = 100
    
    def _create_test_fractal_data(self) -> np.ndarray:
        """テスト用のフラクタルデータを作成"""
        return np.random.randint(0, 100, size=(50, 50))
    
    def test_export_dialog_creation(self):
        """エクスポートダイアログの作成テスト"""
        dialog = ImageExportDialog()
        
        self.assertIsNotNone(dialog)
        self.assertEqual(dialog.windowTitle(), "画像エクスポート")
        self.assertTrue(dialog.isModal())
    
    def test_export_dialog_fractal_data_setting(self):
        """エクスポートダイアログのフラクタルデータ設定テスト"""
        dialog = ImageExportDialog()
        
        # フラクタルデータを設定
        dialog.set_fractal_data(self.test_iteration_data, self.max_iterations)
        
        self.assertIsNotNone(dialog.iteration_data)
        self.assertEqual(dialog.max_iterations, self.max_iterations)
        self.assertTrue(np.array_equal(dialog.iteration_data, self.test_iteration_data))
    
    def test_export_settings_retrieval(self):
        """エクスポート設定の取得テスト"""
        dialog = ImageExportDialog()
        
        # デフォルト設定を取得
        settings = dialog.get_export_settings()
        
        self.assertIsInstance(settings, dict)
        self.assertIn('filepath', settings)
        self.assertIn('format', settings)
        self.assertIn('high_resolution', settings)
        self.assertIn('anti_aliasing', settings)


def run_export_tests():
    """エクスポート機能のテストを実行"""
    print("画像エクスポート機能のテストを開始...")
    
    # テストスイートを作成
    test_suite = unittest.TestSuite()
    
    # テストケースを追加
    test_suite.addTest(unittest.makeSuite(TestImageExport))
    test_suite.addTest(unittest.makeSuite(TestExportDialogComponents))
    
    # テストランナーを作成して実行
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # 結果を表示
    if result.wasSuccessful():
        print("\n✅ すべてのテストが成功しました！")
        print(f"実行されたテスト数: {result.testsRun}")
    else:
        print(f"\n❌ {len(result.failures)} 個のテストが失敗しました")
        print(f"❌ {len(result.errors)} 個のエラーが発生しました")
        
        if result.failures:
            print("\n失敗したテスト:")
            for test, traceback in result.failures:
                print(f"- {test}: {traceback}")
        
        if result.errors:
            print("\nエラーが発生したテスト:")
            for test, traceback in result.errors:
                print(f"- {test}: {traceback}")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_export_tests()
    sys.exit(0 if success else 1)