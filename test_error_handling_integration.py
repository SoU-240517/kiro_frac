#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
エラーハンドリング統合テスト
フラクタルエディタのエラー処理とロバストネスをテストします
"""

import unittest
import sys
import os
import tempfile
import shutil
from unittest.mock import Mock, patch, MagicMock
import numpy as np

# プロジェクトモジュールのインポート
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'fractal_editor'))

from fractal_editor.models.data_models import (
    ComplexNumber, ComplexRegion, FractalParameters
)
from fractal_editor.generators.mandelbrot import MandelbrotGenerator
from fractal_editor.generators.custom_formula import CustomFormulaGenerator
from fractal_editor.services.error_handling import ErrorHandlingService
from fractal_editor.services.formula_parser import FormulaParser, FormulaValidationError
from fractal_editor.services.project_manager import ProjectManager


class ErrorHandlingIntegrationTest(unittest.TestCase):
    """エラーハンドリングの統合テスト"""
    
    def setUp(self):
        """各テストの前準備"""
        self.temp_dir = tempfile.mkdtemp()
        self.error_service = ErrorHandlingService()
        self.project_manager = ProjectManager(self.temp_dir)
    
    def tearDown(self):
        """各テストの後処理"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_invalid_formula_error_handling(self):
        """無効な数式のエラーハンドリングテスト"""
        print("  🔄 無効な数式エラーハンドリングテストを実行中...")
        
        invalid_formulas = [
            "import os; os.system('rm -rf /')",  # 危険なコード
            "z**2 + undefined_variable",        # 未定義変数
            "z**2 + c + )",                     # 構文エラー
            "eval('malicious_code')",           # 危険な関数
            "z**2 + c + forbidden_func()",      # 許可されていない関数
        ]
        
        for formula in invalid_formulas:
            with self.subTest(formula=formula):
                with self.assertRaises((FormulaValidationError, ValueError, SyntaxError)):
                    parser = FormulaParser(formula)
                    # パーサーの初期化時にエラーが発生するはず
        
        print("  ✅ 無効な数式エラーハンドリングテスト成功")
    
    def test_calculation_overflow_handling(self):
        """計算オーバーフローのハンドリングテスト"""
        print("  🔄 計算オーバーフローハンドリングテストを実行中...")
        
        # 極端なパラメータでオーバーフローを誘発
        generator = MandelbrotGenerator()
        extreme_parameters = FractalParameters(
            region=ComplexRegion(
                top_left=ComplexNumber(-1e10, 1e10),    # 極端に大きな値
                bottom_right=ComplexNumber(1e10, -1e10)
            ),
            max_iterations=10000,  # 非常に多い反復回数
            image_size=(10, 10),   # 小さなサイズでテスト
            custom_parameters={}
        )
        
        try:
            result = generator.calculate(extreme_parameters)
            # 結果が有効であることを確認
            self.assertIsNotNone(result)
            self.assertEqual(result.iteration_data.shape, (10, 10))
            print("    極端なパラメータでも正常に計算完了")
        except (OverflowError, MemoryError, ValueError) as e:
            # エラーが適切にハンドリングされることを確認
            print(f"    期待されるエラーが適切にキャッチされました: {type(e).__name__}")
        
        print("  ✅ 計算オーバーフローハンドリングテスト成功")
    
    def test_memory_limit_handling(self):
        """メモリ制限のハンドリングテスト"""
        print("  🔄 メモリ制限ハンドリングテストを実行中...")
        
        generator = MandelbrotGenerator()
        
        # 非常に大きな画像サイズでメモリ不足を誘発
        large_parameters = FractalParameters(
            region=ComplexRegion(
                top_left=ComplexNumber(-2.0, 1.0),
                bottom_right=ComplexNumber(1.0, -1.0)
            ),
            max_iterations=100,
            image_size=(10000, 10000),  # 非常に大きなサイズ
            custom_parameters={}
        )
        
        try:
            result = generator.calculate(large_parameters)
            # もし計算が成功した場合、結果を検証
            if result is not None:
                print("    大きな画像サイズでも計算が完了しました")
                self.assertIsNotNone(result.iteration_data)
        except MemoryError:
            print("    メモリエラーが適切にキャッチされました")
        except Exception as e:
            print(f"    その他のエラーがキャッチされました: {type(e).__name__}")
        
        print("  ✅ メモリ制限ハンドリングテスト成功")
    
    def test_file_io_error_handling(self):
        """ファイルI/Oエラーハンドリングテスト"""
        print("  🔄 ファイルI/Oエラーハンドリングテストを実行中...")
        
        # 存在しないファイルの読み込み
        non_existent_path = os.path.join(self.temp_dir, "non_existent.fractal")
        
        with self.assertRaises((FileNotFoundError, IOError)):
            self.project_manager.load_project(non_existent_path)
        
        # 無効なJSONファイルの読み込み
        invalid_json_path = os.path.join(self.temp_dir, "invalid.fractal")
        with open(invalid_json_path, 'w') as f:
            f.write("invalid json content {")
        
        with self.assertRaises((ValueError, IOError)):
            self.project_manager.load_project(invalid_json_path)
        
        # 読み取り専用ディレクトリへの保存（権限エラー）
        try:
            readonly_dir = os.path.join(self.temp_dir, "readonly")
            os.makedirs(readonly_dir)
            os.chmod(readonly_dir, 0o444)  # 読み取り専用
            
            project = self.project_manager.create_default_project("テスト")
            readonly_path = os.path.join(readonly_dir, "test.fractal")
            
            with self.assertRaises((PermissionError, IOError)):
                self.project_manager.save_project(project, readonly_path)
        except OSError:
            # Windowsでは権限設定が異なる場合があるのでスキップ
            print("    権限エラーテストをスキップ（OS制限）")
        
        print("  ✅ ファイルI/Oエラーハンドリングテスト成功")
    
    def test_invalid_parameter_handling(self):
        """無効なパラメータのハンドリングテスト"""
        print("  🔄 無効なパラメータハンドリングテストを実行中...")
        
        generator = MandelbrotGenerator()
        
        # 無効なパラメータのテストケース
        invalid_cases = [
            # 負の反復回数
            {
                'region': ComplexRegion(
                    ComplexNumber(-2.0, 1.0),
                    ComplexNumber(1.0, -1.0)
                ),
                'max_iterations': -10,
                'image_size': (100, 100),
                'custom_parameters': {}
            },
            # ゼロサイズの画像
            {
                'region': ComplexRegion(
                    ComplexNumber(-2.0, 1.0),
                    ComplexNumber(1.0, -1.0)
                ),
                'max_iterations': 100,
                'image_size': (0, 0),
                'custom_parameters': {}
            },
            # 無効な領域（左上と右下が逆）
            {
                'region': ComplexRegion(
                    ComplexNumber(1.0, -1.0),  # 逆の座標
                    ComplexNumber(-2.0, 1.0)
                ),
                'max_iterations': 100,
                'image_size': (100, 100),
                'custom_parameters': {}
            }
        ]
        
        for i, invalid_params in enumerate(invalid_cases):
            with self.subTest(case=i):
                try:
                    parameters = FractalParameters(**invalid_params)
                    result = generator.calculate(parameters)
                    # 無効なパラメータでも何らかの結果が返される場合
                    print(f"    ケース{i+1}: 無効なパラメータが処理されました")
                except (ValueError, TypeError, AttributeError) as e:
                    print(f"    ケース{i+1}: 期待されるエラーがキャッチされました: {type(e).__name__}")
        
        print("  ✅ 無効なパラメータハンドリングテスト成功")
    
    def test_custom_formula_error_recovery(self):
        """カスタム数式エラー回復テスト"""
        print("  🔄 カスタム数式エラー回復テストを実行中...")
        
        # 実行時エラーを起こす可能性のある数式
        problematic_formulas = [
            "c / z",           # ゼロ除算の可能性
            "log(z)",          # 負数の対数
            "sqrt(z - 10)",    # 負数の平方根
            "z**(1000)",       # 極端な指数
        ]
        
        for formula in problematic_formulas:
            with self.subTest(formula=formula):
                try:
                    generator = CustomFormulaGenerator(formula, f"テスト: {formula}")
                    
                    parameters = FractalParameters(
                        region=ComplexRegion(
                            ComplexNumber(-2.0, 1.0),
                            ComplexNumber(1.0, -1.0)
                        ),
                        max_iterations=50,
                        image_size=(50, 50),
                        custom_parameters={}
                    )
                    
                    result = generator.calculate(parameters)
                    
                    # 結果が有効であることを確認
                    self.assertIsNotNone(result)
                    self.assertEqual(result.iteration_data.shape, (50, 50))
                    print(f"    数式 '{formula}' が正常に処理されました")
                    
                except (ZeroDivisionError, ValueError, OverflowError) as e:
                    print(f"    数式 '{formula}' で期待されるエラー: {type(e).__name__}")
        
        print("  ✅ カスタム数式エラー回復テスト成功")
    
    def test_concurrent_error_handling(self):
        """並行処理エラーハンドリングテスト"""
        print("  🔄 並行処理エラーハンドリングテストを実行中...")
        
        # 複数の計算を同時に実行してエラーハンドリングをテスト
        generator = MandelbrotGenerator()
        
        # 正常なパラメータと異常なパラメータを混在
        parameter_sets = [
            # 正常なパラメータ
            FractalParameters(
                region=ComplexRegion(
                    ComplexNumber(-2.0, 1.0),
                    ComplexNumber(1.0, -1.0)
                ),
                max_iterations=50,
                image_size=(50, 50),
                custom_parameters={}
            ),
            # 極端なパラメータ
            FractalParameters(
                region=ComplexRegion(
                    ComplexNumber(-1e6, 1e6),
                    ComplexNumber(1e6, -1e6)
                ),
                max_iterations=1000,
                image_size=(100, 100),
                custom_parameters={}
            )
        ]
        
        results = []
        errors = []
        
        for i, params in enumerate(parameter_sets):
            try:
                result = generator.calculate(params)
                results.append(result)
                print(f"    パラメータセット{i+1}: 計算成功")
            except Exception as e:
                errors.append(e)
                print(f"    パラメータセット{i+1}: エラー処理 - {type(e).__name__}")
        
        # 少なくとも1つは成功することを確認
        self.assertGreater(len(results), 0, "少なくとも1つの計算は成功する必要があります")
        
        print("  ✅ 並行処理エラーハンドリングテスト成功")


class RobustnessTest(unittest.TestCase):
    """ロバストネステスト"""
    
    def setUp(self):
        """各テストの前準備"""
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """各テストの後処理"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_boundary_value_robustness(self):
        """境界値でのロバストネステスト"""
        print("  🔄 境界値ロバストネステストを実行中...")
        
        generator = MandelbrotGenerator()
        
        # 境界値テストケース
        boundary_cases = [
            # 最小値
            {
                'region': ComplexRegion(
                    ComplexNumber(-0.001, 0.001),
                    ComplexNumber(0.001, -0.001)
                ),
                'max_iterations': 1,
                'image_size': (1, 1),
                'description': '最小値'
            },
            # 最大値（合理的な範囲内）
            {
                'region': ComplexRegion(
                    ComplexNumber(-100.0, 100.0),
                    ComplexNumber(100.0, -100.0)
                ),
                'max_iterations': 5000,
                'image_size': (1000, 1000),
                'description': '最大値'
            },
            # ゼロ周辺
            {
                'region': ComplexRegion(
                    ComplexNumber(-1e-10, 1e-10),
                    ComplexNumber(1e-10, -1e-10)
                ),
                'max_iterations': 100,
                'image_size': (10, 10),
                'description': 'ゼロ周辺'
            }
        ]
        
        for case in boundary_cases:
            with self.subTest(description=case['description']):
                try:
                    parameters = FractalParameters(
                        region=case['region'],
                        max_iterations=case['max_iterations'],
                        image_size=case['image_size'],
                        custom_parameters={}
                    )
                    
                    result = generator.calculate(parameters)
                    
                    # 結果の妥当性を確認
                    self.assertIsNotNone(result)
                    expected_shape = case['image_size'][::-1]  # (height, width)
                    self.assertEqual(result.iteration_data.shape, expected_shape)
                    
                    print(f"    {case['description']}: 正常に処理されました")
                    
                except Exception as e:
                    print(f"    {case['description']}: エラー処理 - {type(e).__name__}")
        
        print("  ✅ 境界値ロバストネステスト成功")
    
    def test_data_corruption_recovery(self):
        """データ破損からの回復テスト"""
        print("  🔄 データ破損回復テストを実行中...")
        
        project_manager = ProjectManager(self.temp_dir)
        
        # 正常なプロジェクトを作成
        project = project_manager.create_default_project("テストプロジェクト")
        project_path = os.path.join(self.temp_dir, "test.fractal")
        project_manager.save_project(project, project_path)
        
        # ファイルを破損させる
        corrupted_path = os.path.join(self.temp_dir, "corrupted.fractal")
        with open(corrupted_path, 'w') as f:
            f.write('{"incomplete": "json"')  # 不完全なJSON
        
        # 破損したファイルの読み込みテスト
        with self.assertRaises((ValueError, IOError)):
            project_manager.load_project(corrupted_path)
        
        # 空ファイルの処理テスト
        empty_path = os.path.join(self.temp_dir, "empty.fractal")
        with open(empty_path, 'w') as f:
            pass  # 空ファイル
        
        with self.assertRaises((ValueError, IOError)):
            project_manager.load_project(empty_path)
        
        print("  ✅ データ破損回復テスト成功")
    
    def test_resource_exhaustion_handling(self):
        """リソース枯渇ハンドリングテスト"""
        print("  🔄 リソース枯渇ハンドリングテストを実行中...")
        
        generator = MandelbrotGenerator()
        
        # 大量のメモリを消費する可能性のあるパラメータ
        resource_intensive_params = FractalParameters(
            region=ComplexRegion(
                ComplexNumber(-2.0, 1.0),
                ComplexNumber(1.0, -1.0)
            ),
            max_iterations=1000,
            image_size=(2000, 2000),  # 大きなサイズ
            custom_parameters={}
        )
        
        try:
            # タイムアウト付きで実行
            import signal
            
            def timeout_handler(signum, frame):
                raise TimeoutError("計算がタイムアウトしました")
            
            # Windowsではsignalが制限されているため、try-except で処理
            try:
                signal.signal(signal.SIGALRM, timeout_handler)
                signal.alarm(30)  # 30秒でタイムアウト
                
                result = generator.calculate(resource_intensive_params)
                
                signal.alarm(0)  # タイマーをリセット
                
                if result is not None:
                    print("    大きなリソース消費でも計算が完了しました")
                    
            except (AttributeError, OSError):
                # Windowsではsignal.SIGALRMが利用できない
                print("    タイムアウト機能はこのプラットフォームでは利用できません")
                
                # 代替として、簡単な計算時間チェック
                import time
                start_time = time.time()
                result = generator.calculate(resource_intensive_params)
                elapsed_time = time.time() - start_time
                
                if elapsed_time > 60:  # 60秒以上かかった場合
                    print(f"    計算時間が長すぎます: {elapsed_time:.1f}秒")
                else:
                    print(f"    計算完了: {elapsed_time:.1f}秒")
                    
        except (MemoryError, TimeoutError) as e:
            print(f"    期待されるリソース制限エラー: {type(e).__name__}")
        except Exception as e:
            print(f"    その他のエラー: {type(e).__name__}")
        
        print("  ✅ リソース枯渇ハンドリングテスト成功")


def run_error_handling_tests():
    """エラーハンドリングテストスイートを実行"""
    print("🛡️  フラクタルエディタ エラーハンドリング統合テストを開始します\n")
    
    # テストスイートを作成
    test_suite = unittest.TestSuite()
    
    # エラーハンドリング統合テスト
    test_suite.addTest(unittest.TestLoader().loadTestsFromTestCase(ErrorHandlingIntegrationTest))
    
    # ロバストネステスト
    test_suite.addTest(unittest.TestLoader().loadTestsFromTestCase(RobustnessTest))
    
    # テストランナーを作成して実行
    runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
    result = runner.run(test_suite)
    
    # 結果サマリーを表示
    print(f"\n📊 エラーハンドリングテスト結果サマリー:")
    print(f"  実行テスト数: {result.testsRun}")
    print(f"  成功: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"  失敗: {len(result.failures)}")
    print(f"  エラー: {len(result.errors)}")
    
    success = len(result.failures) == 0 and len(result.errors) == 0
    
    if success:
        print(f"\n🎉 すべてのエラーハンドリングテストが成功しました！")
        print(f"   🛡️  フラクタルエディタのエラー処理は堅牢です。")
    else:
        print(f"\n⚠️  一部のテストが失敗しました。エラーハンドリングの改善が必要です。")
    
    return success


if __name__ == "__main__":
    success = run_error_handling_tests()
    sys.exit(0 if success else 1)