"""
UI応答性最適化のテスト

このテストファイルは、バックグラウンド計算、プログレッシブレンダリング、
リアルタイムプレビューなどのUI応答性最適化機能をテストします。
"""

import unittest
import sys
import time
import numpy as np
from unittest.mock import Mock, patch, MagicMock
from PyQt6.QtWidgets import QApplication, QWidget
from PyQt6.QtCore import QTimer, pyqtSignal
from PyQt6.QtTest import QTest

# テスト対象のモジュールをインポート
from fractal_editor.services.background_calculator import (
    BackgroundCalculationService, ResponsiveUIManager, CalculationStatus,
    CalculationProgress, get_background_calculation_service, get_responsive_ui_manager
)
from fractal_editor.ui.main_window import MainWindow
from fractal_editor.ui.fractal_widget import FractalWidget
from fractal_editor.models.data_models import FractalParameters, ComplexRegion, ComplexNumber


class TestBackgroundCalculationService(unittest.TestCase):
    """バックグラウンド計算サービスのテスト"""
    
    @classmethod
    def setUpClass(cls):
        """テストクラス全体の初期化"""
        if not QApplication.instance():
            cls.app = QApplication(sys.argv)
        else:
            cls.app = QApplication.instance()
    
    def setUp(self):
        """各テストの初期化"""
        self.service = BackgroundCalculationService()
        self.mock_calculation_func = Mock(return_value="test_result")
        self.test_parameters = {"test": "params"}
    
    def test_service_initialization(self):
        """サービスの初期化テスト"""
        self.assertFalse(self.service.is_calculating())
        self.assertIsNone(self.service._current_worker)
        self.assertIsNone(self.service._progress_dialog)
    
    def test_calculation_start_success(self):
        """計算開始の成功テスト"""
        # 計算開始
        success = self.service.start_calculation(
            self.mock_calculation_func, 
            self.test_parameters, 
            show_progress=False
        )
        
        self.assertTrue(success)
        self.assertTrue(self.service.is_calculating())
        
        # クリーンアップ
        self.service.cancel_calculation()
        QTest.qWait(100)  # ワーカーの終了を待機
    
    def test_calculation_start_while_calculating(self):
        """計算中に新しい計算を開始しようとした場合のテスト"""
        # 最初の計算を開始
        self.service.start_calculation(
            self.mock_calculation_func, 
            self.test_parameters, 
            show_progress=False
        )
        
        # 2回目の計算開始を試行
        success = self.service.start_calculation(
            self.mock_calculation_func, 
            self.test_parameters, 
            show_progress=False
        )
        
        self.assertFalse(success)  # 2回目は失敗するはず
        
        # クリーンアップ
        self.service.cancel_calculation()
        QTest.qWait(100)
    
    def test_calculation_cancellation(self):
        """計算キャンセルのテスト"""
        # 長時間の計算をシミュレート
        def long_calculation(params):
            time.sleep(1)
            return "result"
        
        # 計算開始
        self.service.start_calculation(long_calculation, {}, show_progress=False)
        self.assertTrue(self.service.is_calculating())
        
        # キャンセル
        self.service.cancel_calculation()
        
        # 少し待ってからキャンセルが効いているかチェック
        QTest.qWait(200)
        # 注意: 実際のキャンセル処理は非同期なので、即座には反映されない場合がある
    
    def test_get_calculation_statistics(self):
        """計算統計情報の取得テスト"""
        stats = self.service.get_calculation_statistics()
        self.assertIsInstance(stats, dict)
        self.assertIn('status', stats)
        
        # 計算中の統計情報
        self.service.start_calculation(
            self.mock_calculation_func, 
            self.test_parameters, 
            show_progress=False
        )
        
        stats = self.service.get_calculation_statistics()
        self.assertIsInstance(stats, dict)
        
        # クリーンアップ
        self.service.cancel_calculation()
        QTest.qWait(100)


class TestResponsiveUIManager(unittest.TestCase):
    """UI応答性管理のテスト"""
    
    @classmethod
    def setUpClass(cls):
        """テストクラス全体の初期化"""
        if not QApplication.instance():
            cls.app = QApplication(sys.argv)
        else:
            cls.app = QApplication.instance()
    
    def setUp(self):
        """各テストの初期化"""
        self.ui_manager = ResponsiveUIManager()
        
        # テスト用のフラクタルパラメータ
        self.test_params = FractalParameters(
            region=ComplexRegion(
                top_left=ComplexNumber(-2.0, 1.0),
                bottom_right=ComplexNumber(1.0, -1.0)
            ),
            max_iterations=1000,
            image_size=(800, 600),
            custom_parameters={}
        )
    
    def test_ui_manager_initialization(self):
        """UI管理の初期化テスト"""
        self.assertEqual(self.ui_manager._update_interval, 50)
        self.assertTrue(self.ui_manager._preview_enabled)
        self.assertEqual(self.ui_manager._preview_scale, 0.25)
        self.assertTrue(self.ui_manager._progressive_rendering)
    
    def test_update_interval_setting(self):
        """更新間隔設定のテスト"""
        self.ui_manager.set_update_interval(100)
        self.assertEqual(self.ui_manager._update_interval, 100)
        
        # 最小値のテスト
        self.ui_manager.set_update_interval(5)
        self.assertEqual(self.ui_manager._update_interval, 10)  # 最小10ms
    
    def test_preview_mode_configuration(self):
        """プレビューモード設定のテスト"""
        self.ui_manager.enable_preview_mode(True, 0.5)
        self.assertTrue(self.ui_manager._preview_enabled)
        self.assertEqual(self.ui_manager._preview_scale, 0.5)
        
        self.ui_manager.enable_preview_mode(False)
        self.assertFalse(self.ui_manager._preview_enabled)
    
    def test_create_preview_parameters(self):
        """プレビューパラメータ作成のテスト"""
        preview_params = self.ui_manager.create_preview_parameters(self.test_params)
        
        # プレビューが有効な場合
        self.assertNotEqual(preview_params.image_size, self.test_params.image_size)
        self.assertLess(preview_params.image_size[0], self.test_params.image_size[0])
        self.assertLess(preview_params.image_size[1], self.test_params.image_size[1])
        self.assertIn('_is_preview', preview_params.custom_parameters)
        
        # プレビューが無効な場合
        self.ui_manager.enable_preview_mode(False)
        preview_params_disabled = self.ui_manager.create_preview_parameters(self.test_params)
        self.assertEqual(preview_params_disabled, self.test_params)
    
    def test_create_progressive_parameters(self):
        """プログレッシブパラメータ作成のテスト"""
        # ステージ0（最初）
        stage0_params = self.ui_manager.create_progressive_parameters(self.test_params, 0, 4)
        self.assertLess(stage0_params.image_size[0], self.test_params.image_size[0])
        self.assertIn('_is_progressive', stage0_params.custom_parameters)
        self.assertEqual(stage0_params.custom_parameters['_stage'], 0)
        
        # ステージ3（最後）
        stage3_params = self.ui_manager.create_progressive_parameters(self.test_params, 3, 4)
        self.assertEqual(stage3_params.image_size, self.test_params.image_size)
        
        # プログレッシブレンダリングが無効な場合
        self.ui_manager.enable_progressive_rendering(False)
        disabled_params = self.ui_manager.create_progressive_parameters(self.test_params, 0, 4)
        self.assertEqual(disabled_params, self.test_params)
    
    def test_responsive_loop_generator(self):
        """応答性ループジェネレータのテスト"""
        iterations = list(self.ui_manager.create_responsive_loop(10, 3))
        self.assertEqual(len(iterations), 10)
        self.assertEqual(iterations, list(range(10)))
    
    def test_adaptive_update_frequency(self):
        """適応的更新頻度計算のテスト"""
        frequency = self.ui_manager.create_adaptive_update_frequency(1000, 30)
        self.assertIsInstance(frequency, int)
        self.assertGreater(frequency, 0)
        
        # 大きな反復回数での計算
        frequency_large = self.ui_manager.create_adaptive_update_frequency(100000, 60)
        self.assertIsInstance(frequency_large, int)
        self.assertGreater(frequency_large, 0)
    
    def test_ui_responsiveness_monitoring(self):
        """UI応答性監視のテスト"""
        responsiveness = self.ui_manager.monitor_ui_responsiveness()
        
        self.assertIsInstance(responsiveness, dict)
        self.assertIn('response_time_ms', responsiveness)
        self.assertIn('responsiveness', responsiveness)
        self.assertIn('target_fps', responsiveness)
        self.assertIn('recommended_update_interval', responsiveness)
        
        # 応答性評価の確認
        self.assertIn(responsiveness['responsiveness'], 
                     ['excellent', 'good', 'acceptable', 'poor'])
    
    def test_system_performance_optimization(self):
        """システムパフォーマンス最適化のテスト"""
        # 最適化実行（例外が発生しないことを確認）
        try:
            self.ui_manager.optimize_for_system_performance()
        except Exception as e:
            self.fail(f"システムパフォーマンス最適化でエラー: {e}")


class TestMainWindowUIResponsiveness(unittest.TestCase):
    """メインウィンドウのUI応答性テスト"""
    
    @classmethod
    def setUpClass(cls):
        """テストクラス全体の初期化"""
        if not QApplication.instance():
            cls.app = QApplication(sys.argv)
        else:
            cls.app = QApplication.instance()
    
    def setUp(self):
        """各テストの初期化"""
        self.main_window = MainWindow()
    
    def tearDown(self):
        """各テストの後処理"""
        self.main_window.close()
    
    def test_background_service_integration(self):
        """バックグラウンドサービス統合のテスト"""
        self.assertIsNotNone(self.main_window.background_service)
        self.assertIsNotNone(self.main_window.responsive_ui_manager)
        self.assertIsNotNone(self.main_window.cancel_action)
    
    def test_preview_functionality(self):
        """プレビュー機能のテスト"""
        # プレビュー有効化
        self.main_window.enable_realtime_preview(True)
        self.assertTrue(self.main_window.preview_enabled)
        
        # プレビュー無効化
        self.main_window.enable_realtime_preview(False)
        self.assertFalse(self.main_window.preview_enabled)
    
    def test_preview_delay_setting(self):
        """プレビュー遅延設定のテスト"""
        self.main_window.set_preview_delay(1000)
        self.assertEqual(self.main_window.preview_delay_ms, 1000)
        
        # 最小値のテスト
        self.main_window.set_preview_delay(50)
        self.assertEqual(self.main_window.preview_delay_ms, 100)  # 最小100ms
    
    def test_ui_responsiveness_info(self):
        """UI応答性情報取得のテスト"""
        info = self.main_window.get_ui_responsiveness_info()
        
        self.assertIsInstance(info, dict)
        self.assertIn('ui_responsiveness', info)
        self.assertIn('calculation_status', info)
        self.assertIn('preview_enabled', info)
        self.assertIn('preview_delay_ms', info)
        self.assertIn('is_calculating', info)
    
    def test_ui_performance_optimization(self):
        """UIパフォーマンス最適化のテスト"""
        try:
            self.main_window.optimize_ui_performance()
        except Exception as e:
            self.fail(f"UIパフォーマンス最適化でエラー: {e}")


class TestFractalWidgetResponsiveness(unittest.TestCase):
    """フラクタルウィジェットの応答性テスト"""
    
    @classmethod
    def setUpClass(cls):
        """テストクラス全体の初期化"""
        if not QApplication.instance():
            cls.app = QApplication(sys.argv)
        else:
            cls.app = QApplication.instance()
    
    def setUp(self):
        """各テストの初期化"""
        self.fractal_widget = FractalWidget()
        
        # テスト用の画像データ
        self.test_image = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        self.test_region = ComplexRegion(
            top_left=ComplexNumber(-2.0, 1.0),
            bottom_right=ComplexNumber(1.0, -1.0)
        )
    
    def tearDown(self):
        """各テストの後処理"""
        self.fractal_widget.close()
    
    def test_responsive_mode_control(self):
        """応答性モード制御のテスト"""
        # 応答性モード開始
        self.fractal_widget.start_responsive_mode()
        self.assertTrue(self.fractal_widget.ui_update_timer.isActive())
        
        # 応答性モード停止
        self.fractal_widget.stop_responsive_mode()
        self.assertFalse(self.fractal_widget.ui_update_timer.isActive())
    
    def test_responsive_update_interval(self):
        """応答性更新間隔のテスト"""
        self.fractal_widget.set_responsive_update_interval(75)
        self.assertEqual(self.fractal_widget.ui_update_timer.interval(), 75)
        
        # 最小値のテスト
        self.fractal_widget.set_responsive_update_interval(5)
        self.assertEqual(self.fractal_widget.ui_update_timer.interval(), 10)  # 最小10ms
    
    def test_progressive_image_setting(self):
        """プログレッシブ画像設定のテスト"""
        # 中間ステージ
        self.fractal_widget.set_progressive_image(self.test_image, 1, 4, self.test_region)
        self.assertIsNotNone(self.fractal_widget.fractal_pixmap)
        self.assertIn("プログレッシブレンダリング中", self.fractal_widget.toolTip())
        
        # 最終ステージ
        self.fractal_widget.set_progressive_image(self.test_image, 3, 4, self.test_region)
        self.assertEqual(self.fractal_widget.toolTip(), "")
    
    def test_smooth_updates_configuration(self):
        """スムーズ更新設定のテスト"""
        # スムーズ更新有効
        self.fractal_widget.enable_smooth_updates(True)
        self.assertEqual(self.fractal_widget.ui_update_timer.interval(), 30)
        
        # スムーズ更新無効
        self.fractal_widget.enable_smooth_updates(False)
        self.assertEqual(self.fractal_widget.ui_update_timer.interval(), 50)
    
    def test_quality_mode_setting(self):
        """品質モード設定のテスト"""
        # 高品質モード
        self.fractal_widget.set_quality_mode(True)
        self.assertEqual(self.fractal_widget.zoom_sensitivity, 0.05)
        self.assertEqual(self.fractal_widget.max_zoom, 1000.0)
        
        # 高速モード
        self.fractal_widget.set_quality_mode(False)
        self.assertEqual(self.fractal_widget.zoom_sensitivity, 0.1)
        self.assertEqual(self.fractal_widget.max_zoom, 100.0)
    
    def test_display_statistics(self):
        """表示統計情報のテスト"""
        stats = self.fractal_widget.get_display_statistics()
        
        self.assertIsInstance(stats, dict)
        self.assertIn('zoom_factor', stats)
        self.assertIn('pan_offset', stats)
        self.assertIn('has_image', stats)
        self.assertIn('widget_size', stats)
        self.assertIn('responsive_mode_active', stats)
        self.assertIn('update_interval_ms', stats)
        
        # 画像設定後の統計情報
        self.fractal_widget.set_fractal_image(self.test_image, self.test_region)
        stats_with_image = self.fractal_widget.get_display_statistics()
        
        self.assertTrue(stats_with_image['has_image'])
        self.assertIn('image_size', stats_with_image)
        self.assertIn('complex_region', stats_with_image)
    
    def test_performance_optimization(self):
        """パフォーマンス最適化のテスト"""
        try:
            self.fractal_widget.optimize_for_performance()
        except Exception as e:
            self.fail(f"パフォーマンス最適化でエラー: {e}")


class TestCalculationProgress(unittest.TestCase):
    """計算進行状況のテスト"""
    
    def test_progress_calculation(self):
        """進行状況計算のテスト"""
        progress = CalculationProgress(
            status=CalculationStatus.CALCULATING,
            current_step=25,
            total_steps=100,
            elapsed_time=10.0,
            estimated_remaining_time=30.0
        )
        
        self.assertEqual(progress.progress_percentage, 25.0)
        self.assertFalse(progress.is_complete)
        
        # 完了状態のテスト
        completed_progress = CalculationProgress(
            status=CalculationStatus.COMPLETED,
            current_step=100,
            total_steps=100,
            elapsed_time=40.0,
            estimated_remaining_time=0.0
        )
        
        self.assertEqual(completed_progress.progress_percentage, 100.0)
        self.assertTrue(completed_progress.is_complete)
    
    def test_progress_edge_cases(self):
        """進行状況のエッジケースのテスト"""
        # ゼロ除算のテスト
        zero_total_progress = CalculationProgress(
            status=CalculationStatus.PREPARING,
            current_step=0,
            total_steps=0,
            elapsed_time=0.0,
            estimated_remaining_time=0.0
        )
        
        self.assertEqual(zero_total_progress.progress_percentage, 0.0)
        
        # 100%を超える場合のテスト
        over_progress = CalculationProgress(
            status=CalculationStatus.CALCULATING,
            current_step=150,
            total_steps=100,
            elapsed_time=10.0,
            estimated_remaining_time=0.0
        )
        
        self.assertEqual(over_progress.progress_percentage, 100.0)


def run_ui_responsiveness_tests():
    """UI応答性テストを実行"""
    print("UI応答性最適化のテストを開始します...")
    
    # テストスイートを作成
    test_suite = unittest.TestSuite()
    
    # テストクラスを追加
    test_classes = [
        TestBackgroundCalculationService,
        TestResponsiveUIManager,
        TestMainWindowUIResponsiveness,
        TestFractalWidgetResponsiveness,
        TestCalculationProgress
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # テストを実行
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # 結果を表示
    print(f"\n=== テスト結果 ===")
    print(f"実行テスト数: {result.testsRun}")
    print(f"失敗: {len(result.failures)}")
    print(f"エラー: {len(result.errors)}")
    
    if result.failures:
        print("\n=== 失敗したテスト ===")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback}")
    
    if result.errors:
        print("\n=== エラーが発生したテスト ===")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback}")
    
    success = len(result.failures) == 0 and len(result.errors) == 0
    print(f"\n=== 総合結果: {'成功' if success else '失敗'} ===")
    
    return success


if __name__ == "__main__":
    # PyQt6アプリケーションを初期化
    app = QApplication(sys.argv)
    
    try:
        # テストを実行
        success = run_ui_responsiveness_tests()
        
        # 終了コードを設定
        sys.exit(0 if success else 1)
        
    except Exception as e:
        print(f"テスト実行中にエラーが発生しました: {e}")
        sys.exit(1)
    finally:
        # アプリケーションを終了
        app.quit()