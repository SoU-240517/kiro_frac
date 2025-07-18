"""
パフォーマンス最適化機能のテスト

メモリ管理とUI応答性の最適化機能をテストします。
"""

import unittest
import numpy as np
import time
import threading
from unittest.mock import Mock, patch
import sys
import os

# テスト対象のモジュールをインポート
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'fractal_editor'))

from fractal_editor.services.memory_manager import (
    MemoryManager, MemoryPriority, MemoryUsageInfo, 
    MemoryEfficientArrayOps
)
from fractal_editor.models.data_models import (
    FractalParameters, ComplexRegion, ComplexNumber
)


class TestMemoryManager(unittest.TestCase):
    """メモリマネージャーのテスト"""
    
    def setUp(self):
        """テスト前の準備"""
        # 新しいインスタンスを強制作成（シングルトンをリセット）
        MemoryManager._instance = None
        self.memory_manager = MemoryManager()
    
    def tearDown(self):
        """テスト後のクリーンアップ"""
        if hasattr(self, 'memory_manager'):
            self.memory_manager.stop_memory_monitoring()
            self.memory_manager.force_garbage_collection()
    
    def test_memory_info_retrieval(self):
        """メモリ情報取得のテスト"""
        memory_info = self.memory_manager.get_memory_info()
        
        self.assertIsInstance(memory_info, MemoryUsageInfo)
        self.assertGreater(memory_info.total_memory, 0)
        self.assertGreater(memory_info.available_memory, 0)
        self.assertGreaterEqual(memory_info.memory_percent, 0)
        self.assertLessEqual(memory_info.memory_percent, 100)
    
    def test_memory_availability_check(self):
        """メモリ可用性チェックのテスト"""
        # 小さなサイズ（利用可能であるべき）
        small_size = 1024 * 1024  # 1MB
        self.assertTrue(self.memory_manager.check_memory_availability(small_size))
        
        # 非常に大きなサイズ（利用不可能であるべき）
        huge_size = 1024 * 1024 * 1024 * 1024  # 1TB
        self.assertFalse(self.memory_manager.check_memory_availability(huge_size))
    
    def test_fractal_memory_estimation(self):
        """フラクタルメモリ使用量推定のテスト"""
        width, height = 800, 600
        max_iterations = 1000
        
        estimated_memory = self.memory_manager.estimate_fractal_memory_usage(
            width, height, max_iterations
        )
        
        self.assertGreater(estimated_memory, 0)
        
        # 基本的な配列サイズより大きいはず（オーバーヘッドを含む）
        base_size = width * height * 4  # int32のサイズ
        self.assertGreater(estimated_memory, base_size)
    
    def test_array_allocation(self):
        """配列割り当てのテスト"""
        shape = (100, 100)
        
        # 正常な割り当て
        array = self.memory_manager.allocate_array(
            shape, np.int32, MemoryPriority.NORMAL, "Test array"
        )
        
        self.assertIsNotNone(array)
        self.assertEqual(array.shape, shape)
        self.assertEqual(array.dtype, np.int32)
        
        # 統計情報の確認
        stats = self.memory_manager.get_memory_statistics()
        self.assertGreater(stats['allocation_statistics']['active_allocations'], 0)
        self.assertGreater(stats['allocation_statistics']['total_allocated_mb'], 0)
    
    def test_memory_optimization_recommendations(self):
        """メモリ最適化推奨事項のテスト"""
        # 大きなサイズでテスト
        width, height = 4000, 3000
        max_iterations = 2000
        
        recommendations = self.memory_manager.optimize_for_large_computation(
            width, height, max_iterations
        )
        
        self.assertIn('estimated_memory_mb', recommendations)
        self.assertIn('available_memory_mb', recommendations)
        self.assertIn('memory_sufficient', recommendations)
        self.assertIn('recommendations', recommendations)
        
        # メモリ不足の場合、推奨事項があるはず
        if not recommendations['memory_sufficient']:
            self.assertGreater(len(recommendations['recommendations']), 0)
    
    def test_garbage_collection(self):
        """ガベージコレクションのテスト"""
        # いくつかの配列を作成
        arrays = []
        for i in range(5):
            array = self.memory_manager.allocate_array(
                (50, 50), np.int32, MemoryPriority.LOW, f"Test array {i}"
            )
            if array is not None:
                arrays.append(array)
        
        initial_allocations = len(self.memory_manager.allocations)
        
        # 配列への参照を削除
        arrays.clear()
        
        # ガベージコレクションを実行
        collected = self.memory_manager.force_garbage_collection()
        
        self.assertIsInstance(collected, dict)
        self.assertIn('generation_0', collected)
        self.assertIn('generation_1', collected)
        self.assertIn('generation_2', collected)
    
    def test_memory_context_manager(self):
        """メモリコンテキストマネージャーのテスト"""
        with self.memory_manager.memory_context("Test context"):
            # コンテキスト内で配列を作成
            array = self.memory_manager.allocate_array(
                (100, 100), np.int32, MemoryPriority.NORMAL, "Context test"
            )
            self.assertIsNotNone(array)
        
        # コンテキスト終了後、ガベージコレクションが実行されているはず
        # （実際の検証は困難だが、エラーが発生しないことを確認）


class TestMemoryEfficientArrayOps(unittest.TestCase):
    """メモリ効率的配列操作のテスト"""
    
    def test_chunked_array_creation(self):
        """チャンク配列作成のテスト"""
        total_shape = (200, 100)
        chunk_size = 50
        
        try:
            chunks = MemoryEfficientArrayOps.create_chunked_array(
                total_shape, chunk_size, np.int32
            )
            
            self.assertGreater(len(chunks), 0)
            
            # チャンクサイズの確認
            total_height = 0
            for chunk in chunks:
                self.assertEqual(chunk.shape[1], total_shape[1])  # 幅は同じ
                total_height += chunk.shape[0]
            
            self.assertEqual(total_height, total_shape[0])
            
        except MemoryError:
            # メモリ不足の場合はスキップ
            self.skipTest("メモリ不足のためテストをスキップ")
    
    def test_chunk_combination(self):
        """チャンク結合のテスト"""
        # 小さなチャンクを作成
        chunk1 = np.ones((50, 100), dtype=np.int32)
        chunk2 = np.ones((30, 100), dtype=np.int32) * 2
        chunk3 = np.ones((20, 100), dtype=np.int32) * 3
        
        chunks = [chunk1, chunk2, chunk3]
        
        try:
            combined = MemoryEfficientArrayOps.combine_chunks(chunks)
            
            self.assertEqual(combined.shape, (100, 100))
            self.assertEqual(combined.dtype, np.int32)
            
            # 値の確認
            self.assertTrue(np.all(combined[:50] == 1))
            self.assertTrue(np.all(combined[50:80] == 2))
            self.assertTrue(np.all(combined[80:] == 3))
            
        except MemoryError:
            self.skipTest("メモリ不足のためテストをスキップ")


class TestMemoryIntegratedFractalGeneration(unittest.TestCase):
    """メモリ管理統合フラクタル生成のテスト"""
    
    def setUp(self):
        """テスト前の準備"""
        # テスト用のパラメータを作成
        self.test_region = ComplexRegion(
            ComplexNumber(-2.0, 1.0),
            ComplexNumber(1.0, -1.0)
        )
        self.test_parameters = FractalParameters(
            region=self.test_region,
            max_iterations=100,
            image_size=(200, 150),  # 小さなサイズでテスト
            custom_parameters={}
        )
    
    def test_mandelbrot_with_memory_management(self):
        """メモリ管理付きマンデルブロ生成のテスト"""
        from fractal_editor.generators.mandelbrot import MandelbrotGenerator
        
        generator = MandelbrotGenerator()
        
        try:
            result = generator.calculate(self.test_parameters)
            
            self.assertIsNotNone(result)
            self.assertEqual(result.iteration_data.shape, (150, 200))
            self.assertIn('memory_usage_mb', result.metadata)
            self.assertIn('algorithm', result.metadata)
            self.assertEqual(result.metadata['algorithm'], 'memory_managed_mandelbrot')
            
        except MemoryError as e:
            self.skipTest(f"メモリ不足のためテストをスキップ: {e}")
    
    def test_julia_with_memory_management(self):
        """メモリ管理付きジュリア生成のテスト"""
        from fractal_editor.generators.julia import JuliaGenerator
        
        generator = JuliaGenerator()
        
        try:
            result = generator.calculate(self.test_parameters)
            
            self.assertIsNotNone(result)
            self.assertEqual(result.iteration_data.shape, (150, 200))
            self.assertIn('memory_usage_mb', result.metadata)
            self.assertIn('algorithm', result.metadata)
            self.assertEqual(result.metadata['algorithm'], 'memory_managed_julia')
            
        except MemoryError as e:
            self.skipTest(f"メモリ不足のためテストをスキップ: {e}")


class TestBackgroundCalculationMock(unittest.TestCase):
    """バックグラウンド計算のモックテスト（PyQt6なしでテスト）"""
    
    def test_calculation_progress_data_structure(self):
        """計算進行状況データ構造のテスト"""
        from fractal_editor.services.background_calculator import CalculationProgress, CalculationStatus
        
        progress = CalculationProgress(
            status=CalculationStatus.CALCULATING,
            current_step=50,
            total_steps=100,
            elapsed_time=10.0,
            estimated_remaining_time=10.0,
            message="テスト中"
        )
        
        self.assertEqual(progress.progress_percentage, 50.0)
        self.assertFalse(progress.is_complete)
        
        # 完了状態のテスト
        completed_progress = CalculationProgress(
            status=CalculationStatus.COMPLETED,
            current_step=100,
            total_steps=100,
            elapsed_time=20.0,
            estimated_remaining_time=0.0
        )
        
        self.assertEqual(completed_progress.progress_percentage, 100.0)
        self.assertTrue(completed_progress.is_complete)
    
    def test_responsive_ui_manager_mock(self):
        """UI応答性管理のモックテスト"""
        from fractal_editor.services.background_calculator import ResponsiveUIManager
        
        ui_manager = ResponsiveUIManager()
        
        # 更新間隔の設定
        ui_manager.set_update_interval(100)
        self.assertEqual(ui_manager._update_interval, 100)
        
        # 最小値の制限
        ui_manager.set_update_interval(5)
        self.assertEqual(ui_manager._update_interval, 10)  # 最小10ms
        
        # 応答性ループのテスト
        iterations = list(ui_manager.create_responsive_loop(10, 3))
        self.assertEqual(len(iterations), 10)
        self.assertEqual(iterations, list(range(10)))


def run_performance_tests():
    """パフォーマンステストを実行"""
    print("パフォーマンス最適化機能のテストを開始...")
    
    # テストスイートを作成
    test_suite = unittest.TestSuite()
    
    # メモリ管理テスト
    test_suite.addTest(unittest.makeSuite(TestMemoryManager))
    test_suite.addTest(unittest.makeSuite(TestMemoryEfficientArrayOps))
    test_suite.addTest(unittest.makeSuite(TestMemoryIntegratedFractalGeneration))
    test_suite.addTest(unittest.makeSuite(TestBackgroundCalculationMock))
    
    # テストランナーを作成して実行
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # 結果の表示
    print(f"\n=== テスト結果 ===")
    print(f"実行テスト数: {result.testsRun}")
    print(f"失敗: {len(result.failures)}")
    print(f"エラー: {len(result.errors)}")
    print(f"スキップ: {len(result.skipped) if hasattr(result, 'skipped') else 0}")
    
    if result.failures:
        print("\n=== 失敗したテスト ===")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback}")
    
    if result.errors:
        print("\n=== エラーが発生したテスト ===")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback}")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_performance_tests()
    sys.exit(0 if success else 1)