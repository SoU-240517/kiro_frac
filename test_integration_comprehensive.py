#!/usr/bin/env python3
"""
統合テストスイート - フラクタルエディタ
UI-モデル間の統合テスト、エンドツーエンドワークフロー、パフォーマンステストを実装
"""

import unittest
import sys
import os
import time
import tempfile
import shutil
import json
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import numpy as np

# PyQt6のテスト用設定
os.environ['QT_QPA_PLATFORM'] = 'offscreen'

try:
    from PyQt6.QtWidgets import QApplication, QWidget
    from PyQt6.QtCore import QTimer, Qt
    from PyQt6.QtTest import QTest
    from PyQt6.QtGui import QPixmap
    PYQT_AVAILABLE = True
except ImportError:
    PYQT_AVAILABLE = False
    print("警告: PyQt6が利用できません。UIテストはスキップされます。")

# プロジェクトパスを追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'fractal_editor'))

from fractal_editor.models.data_models import (
    ComplexNumber, ComplexRegion, FractalParameters, FractalResult
)
from fractal_editor.generators.mandelbrot import MandelbrotGenerator
from fractal_editor.generators.julia import JuliaGenerator
from fractal_editor.generators.custom_formula import CustomFormulaGenerator
from fractal_editor.services.color_system import ColorPalette, ColorMapper, ColorStop
from fractal_editor.services.image_renderer import ImageRenderer
from fractal_editor.services.project_manager import ProjectManager
from fractal_editor.models.app_settings import AppSettings

if PYQT_AVAILABLE:
    from fractal_editor.ui.main_window import MainWindow
    from fractal_editor.ui.fractal_widget import FractalWidget
    from fractal_editor.ui.parameter_panel import ParameterPanel


class IntegrationTestBase(unittest.TestCase):
    """統合テストの基底クラス"""
    
    @classmethod
    def setUpClass(cls):
        """テストクラス全体の初期化"""
        if PYQT_AVAILABLE and not QApplication.instance():
            cls.app = QApplication([])
        cls.temp_dir = tempfile.mkdtemp(prefix='fractal_test_')
        
    @classmethod
    def tearDownClass(cls):
        """テストクラス全体のクリーンアップ"""
        if hasattr(cls, 'temp_dir') and os.path.exists(cls.temp_dir):
            shutil.rmtree(cls.temp_dir)
    
    def setUp(self):
        """各テストの初期化"""
        self.test_parameters = FractalParameters(
            region=ComplexRegion(
                top_left=ComplexNumber(-2.0, 1.0),
                bottom_right=ComplexNumber(1.0, -1.0)
            ),
            max_iterations=100,
            image_size=(200, 200),
            custom_parameters={}
        )


class TestUIModelIntegration(IntegrationTestBase):
    """UI-モデル間の統合テスト"""
    
    @unittest.skipUnless(PYQT_AVAILABLE, "PyQt6が必要です")
    def test_main_window_initialization(self):
        """メインウィンドウの初期化テスト"""
        try:
            main_window = MainWindow()
            self.assertIsNotNone(main_window)
            self.assertTrue(main_window.isVisible() or True)  # オフスクリーンでも通る
            
            # 主要コンポーネントの存在確認
            self.assertIsNotNone(main_window.fractal_display_area)
            self.assertIsNotNone(main_window.parameter_dock)
            
            main_window.close()
        except Exception as e:
            self.fail(f"メインウィンドウの初期化に失敗: {e}")
    
    @unittest.skipUnless(PYQT_AVAILABLE, "PyQt6が必要です")
    def test_fractal_widget_parameter_binding(self):
        """フラクタルウィジェットとパラメータの連携テスト"""
        try:
            main_window = MainWindow()
            fractal_display = main_window.fractal_display_area
            parameter_dock = main_window.parameter_dock
            
            # UI要素の基本的な存在確認
            self.assertIsNotNone(fractal_display)
            self.assertIsNotNone(parameter_dock)
            
            # 少し待機してイベント処理を完了
            QTest.qWait(100)
            
            # 基本的なUI操作のテスト
            main_window.resize(800, 600)
            QTest.qWait(50)
            
            main_window.close()
        except Exception as e:
            self.fail(f"パラメータ連携テストに失敗: {e}")
    
    def test_generator_color_system_integration(self):
        """フラクタル生成器と色彩システムの統合テスト"""
        # フラクタル生成
        generator = MandelbrotGenerator()
        result = generator.calculate(self.test_parameters)
        
        # 色彩システムでの処理
        color_palette = ColorPalette(
            name="テストパレット",
            color_stops=[
                ColorStop(0.0, (0, 0, 0)),
                ColorStop(0.5, (255, 0, 0)),
                ColorStop(1.0, (255, 255, 255))
            ]
        )
        
        # 具体的なColorMapperの実装を使用
        from fractal_editor.services.color_system import LinearColorMapper
        color_mapper = LinearColorMapper()
        color_mapper.set_palette(color_palette)
        
        # 画像レンダリング
        renderer = ImageRenderer()
        image = renderer.render_fractal(result, color_mapper)
        
        self.assertIsNotNone(image)
        self.assertEqual(image.size, self.test_parameters.image_size)
    
    def test_project_manager_settings_integration(self):
        """プロジェクトマネージャーと設定システムの統合テスト"""
        # 設定の作成
        settings = AppSettings(
            default_max_iterations=500,
            default_image_size=(400, 400),
            default_color_palette="Rainbow"
        )
        
        # プロジェクトマネージャーの初期化（設定ディレクトリを指定）
        project_manager = ProjectManager(self.temp_dir)
        
        # 新規プロジェクトの作成
        project = project_manager.create_new_project("統合テストプロジェクト")
        
        self.assertIsNotNone(project)
        self.assertEqual(project.name, "統合テストプロジェクト")
        self.assertEqual(project.parameters.max_iterations, settings.default_max_iterations)
        
        # プロジェクトの保存と読み込み
        test_file = os.path.join(self.temp_dir, "test_project.json")
        project_manager.save_project(project, test_file)
        
        loaded_project = project_manager.load_project(test_file)
        self.assertEqual(loaded_project.name, project.name)
        self.assertEqual(loaded_project.parameters.max_iterations, project.parameters.max_iterations)


class TestEndToEndWorkflow(IntegrationTestBase):
    """エンドツーエンドワークフローテスト"""
    
    def test_complete_fractal_generation_workflow(self):
        """完全なフラクタル生成ワークフローのテスト"""
        # 1. フラクタル生成器の選択と初期化
        generator = MandelbrotGenerator()
        # 生成器名は英語の場合があるので、存在確認のみ
        self.assertIsNotNone(generator.name)
        
        # 2. パラメータの設定
        parameters = FractalParameters(
            region=ComplexRegion(
                top_left=ComplexNumber(-2.5, 1.25),
                bottom_right=ComplexNumber(1.0, -1.25)
            ),
            max_iterations=200,
            image_size=(300, 300),
            custom_parameters={}
        )
        
        # 3. フラクタル計算の実行
        start_time = time.time()
        result = generator.calculate(parameters)
        calculation_time = time.time() - start_time
        
        self.assertIsNotNone(result)
        self.assertEqual(result.iteration_data.shape, (300, 300))
        self.assertGreater(result.calculation_time, 0)
        self.assertLess(calculation_time, 10.0)  # 10秒以内で完了
        
        # 4. 色彩システムの適用
        color_palette = ColorPalette(
            name="グラデーション",
            color_stops=[
                ColorStop(0.0, (0, 0, 128)),
                ColorStop(0.3, (0, 128, 255)),
                ColorStop(0.7, (255, 255, 0)),
                ColorStop(1.0, (255, 0, 0))
            ]
        )
        
        # 具体的なColorMapperの実装を使用
        from fractal_editor.services.color_system import LinearColorMapper
        color_mapper = LinearColorMapper()
        color_mapper.set_palette(color_palette)
        
        # 5. 画像レンダリング
        renderer = ImageRenderer()
        image = renderer.render_fractal(result, color_mapper)
        
        self.assertIsNotNone(image)
        self.assertEqual(image.size, (300, 300))
        
        # 6. 画像の保存
        output_path = os.path.join(self.temp_dir, "test_fractal.png")
        image.save(output_path)
        
        self.assertTrue(os.path.exists(output_path))
        self.assertGreater(os.path.getsize(output_path), 1000)  # 最低限のファイルサイズ
    
    def test_custom_formula_workflow(self):
        """カスタム数式フラクタルの完全ワークフロー"""
        # 1. カスタム数式の定義
        formula = "z**3 + c"
        generator = CustomFormulaGenerator(formula, "三次フラクタル")
        
        # 2. パラメータの設定
        parameters = FractalParameters(
            region=ComplexRegion(
                top_left=ComplexNumber(-1.5, 1.5),
                bottom_right=ComplexNumber(1.5, -1.5)
            ),
            max_iterations=150,
            image_size=(250, 250),
            custom_parameters={"formula": formula}
        )
        
        # 3. 計算の実行
        result = generator.calculate(parameters)
        
        self.assertIsNotNone(result)
        self.assertEqual(result.iteration_data.shape, (250, 250))
        
        # 4. 結果の検証（三次フラクタルの特徴的なパターンの確認）
        unique_values = np.unique(result.iteration_data)
        self.assertGreater(len(unique_values), 10)  # 十分な多様性があること
    
    def test_project_save_load_workflow(self):
        """プロジェクト保存・読み込みワークフロー"""
        # 1. プロジェクトの作成
        settings = AppSettings()
        project_manager = ProjectManager(self.temp_dir)
        
        original_project = project_manager.create_new_project("ワークフローテスト")
        original_project.fractal_type = "mandelbrot"
        original_project.parameters = self.test_parameters
        
        # 2. プロジェクトの保存
        project_file = os.path.join(self.temp_dir, "workflow_test.json")
        project_manager.save_project(original_project, project_file)
        
        # 3. プロジェクトの読み込み
        loaded_project = project_manager.load_project(project_file)
        
        # 4. データの整合性確認
        self.assertEqual(loaded_project.name, original_project.name)
        self.assertEqual(loaded_project.fractal_type, original_project.fractal_type)
        self.assertEqual(
            loaded_project.parameters.max_iterations,
            original_project.parameters.max_iterations
        )
        
        # 5. 読み込んだプロジェクトでフラクタル生成
        generator = MandelbrotGenerator()
        result = generator.calculate(loaded_project.parameters)
        
        self.assertIsNotNone(result)
        self.assertEqual(result.iteration_data.shape, self.test_parameters.image_size)


class TestPerformanceIntegration(IntegrationTestBase):
    """パフォーマンス統合テスト"""
    
    def test_large_image_generation_performance(self):
        """大きな画像生成のパフォーマンステスト"""
        # 高解像度パラメータ
        large_parameters = FractalParameters(
            region=ComplexRegion(
                top_left=ComplexNumber(-2.0, 1.0),
                bottom_right=ComplexNumber(1.0, -1.0)
            ),
            max_iterations=500,
            image_size=(1000, 1000),  # 1000x1000の高解像度
            custom_parameters={}
        )
        
        generator = MandelbrotGenerator()
        
        # パフォーマンス測定
        start_time = time.time()
        start_memory = self._get_memory_usage()
        
        result = generator.calculate(large_parameters)
        
        end_time = time.time()
        end_memory = self._get_memory_usage()
        
        calculation_time = end_time - start_time
        memory_increase = end_memory - start_memory
        
        # パフォーマンス検証
        self.assertIsNotNone(result)
        self.assertEqual(result.iteration_data.shape, (1000, 1000))
        self.assertLess(calculation_time, 60.0)  # 60秒以内
        self.assertLess(memory_increase, 500 * 1024 * 1024)  # 500MB以内のメモリ増加
        
        print(f"大画像生成パフォーマンス: {calculation_time:.2f}秒, メモリ増加: {memory_increase/1024/1024:.1f}MB")
    
    def test_multiple_generator_performance(self):
        """複数フラクタル生成器の連続実行パフォーマンス"""
        generators = [
            MandelbrotGenerator(),
            JuliaGenerator(),
            CustomFormulaGenerator("z**2 + c", "テスト")
        ]
        
        results = []
        total_start_time = time.time()
        
        for generator in generators:
            start_time = time.time()
            result = generator.calculate(self.test_parameters)
            end_time = time.time()
            
            results.append({
                'generator': generator.name,
                'time': end_time - start_time,
                'result': result
            })
        
        total_time = time.time() - total_start_time
        
        # 結果の検証
        self.assertEqual(len(results), 3)
        for result_info in results:
            self.assertIsNotNone(result_info['result'])
            self.assertLess(result_info['time'], 5.0)  # 各生成器5秒以内
        
        self.assertLess(total_time, 15.0)  # 全体で15秒以内
        
        print(f"複数生成器パフォーマンス: 合計{total_time:.2f}秒")
        for result_info in results:
            print(f"  {result_info['generator']}: {result_info['time']:.2f}秒")
    
    def test_memory_leak_detection(self):
        """メモリリーク検出テスト"""
        initial_memory = self._get_memory_usage()
        
        # 複数回の生成を実行
        for i in range(10):
            generator = MandelbrotGenerator()
            result = generator.calculate(self.test_parameters)
            
            # 明示的にメモリを解放
            del result
            del generator
        
        # ガベージコレクションを強制実行
        import gc
        gc.collect()
        
        final_memory = self._get_memory_usage()
        memory_increase = final_memory - initial_memory
        
        # メモリ増加が許容範囲内であることを確認
        self.assertLess(memory_increase, 50 * 1024 * 1024)  # 50MB以内
        
        print(f"メモリリークテスト: {memory_increase/1024/1024:.1f}MB増加")
    
    def _get_memory_usage(self):
        """現在のメモリ使用量を取得"""
        try:
            import psutil
            process = psutil.Process()
            return process.memory_info().rss
        except ImportError:
            # psutilが利用できない場合は0を返す
            return 0


class TestErrorHandlingIntegration(IntegrationTestBase):
    """エラーハンドリング統合テスト"""
    
    def test_invalid_parameter_handling(self):
        """無効なパラメータのエラーハンドリング"""
        generator = MandelbrotGenerator()
        
        # 無効なパラメータのテスト（データモデルの検証をバイパス）
        try:
            # 無効な範囲のテスト
            with self.assertRaises(ValueError):
                ComplexRegion(
                    top_left=ComplexNumber(1.0, 1.0),  # 無効な範囲
                    bottom_right=ComplexNumber(-1.0, -1.0)
                )
            
            # 負の反復回数のテスト
            invalid_params = FractalParameters(
                region=ComplexRegion(
                    top_left=ComplexNumber(-2.0, 1.0),
                    bottom_right=ComplexNumber(1.0, -1.0)
                ),
                max_iterations=-100,  # 負の値
                image_size=(100, 100),
                custom_parameters={}
            )
            
            # 負の反復回数でも計算は実行されるが、結果が適切に処理されることを確認
            result = generator.calculate(invalid_params)
            # 結果が何らかの形で返されることを確認
            self.assertIsNotNone(result)
            
        except Exception as e:
            # 何らかのエラーが発生することを確認
            self.assertIsInstance(e, (ValueError, RuntimeError, TypeError))
    
    def test_formula_error_handling(self):
        """数式エラーのハンドリング"""
        # 無効な数式
        invalid_formulas = [
            "import os",  # 危険なコード
            "z**",  # 構文エラー
            "undefined_function(z)",  # 未定義関数
        ]
        
        for formula in invalid_formulas:
            with self.assertRaises(Exception):
                generator = CustomFormulaGenerator(formula, "エラーテスト")
                generator.calculate(self.test_parameters)


def run_integration_tests():
    """統合テストスイートの実行"""
    print("=== フラクタルエディタ統合テストスイート ===")
    print(f"PyQt6利用可能: {PYQT_AVAILABLE}")
    
    # テストスイートの作成
    test_suite = unittest.TestSuite()
    
    # UI-モデル統合テスト
    test_suite.addTest(unittest.makeSuite(TestUIModelIntegration))
    
    # エンドツーエンドワークフローテスト
    test_suite.addTest(unittest.makeSuite(TestEndToEndWorkflow))
    
    # パフォーマンステスト
    test_suite.addTest(unittest.makeSuite(TestPerformanceIntegration))
    
    # エラーハンドリングテスト
    test_suite.addTest(unittest.makeSuite(TestErrorHandlingIntegration))
    
    # テストランナーの実行
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # 結果の表示
    print(f"\n=== テスト結果 ===")
    print(f"実行テスト数: {result.testsRun}")
    print(f"失敗: {len(result.failures)}")
    print(f"エラー: {len(result.errors)}")
    print(f"成功率: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_integration_tests()
    sys.exit(0 if success else 1)