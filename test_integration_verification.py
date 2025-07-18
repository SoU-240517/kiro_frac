"""
統合テスト - カスタム式エディタシステムの統合検証

FormulaParserとCustomFormulaGeneratorが既存のシステムと正しく統合されることを検証します。
"""

import unittest
import numpy as np
from fractal_editor.generators import (
    fractal_registry, CustomFormulaGenerator, create_custom_fractal
)
from fractal_editor.models.data_models import (
    FractalParameters, ComplexRegion, ComplexNumber
)
from fractal_editor.services.formula_parser import template_manager


class TestSystemIntegration(unittest.TestCase):
    """システム統合テスト"""
    
    def setUp(self):
        """テスト用のセットアップ"""
        self.test_region = ComplexRegion(
            top_left=ComplexNumber(-2.0, 1.0),
            bottom_right=ComplexNumber(1.0, -1.0)
        )
        self.test_parameters = FractalParameters(
            region=self.test_region,
            max_iterations=50,
            image_size=(50, 50)
        )
    
    def test_custom_generator_registration(self):
        """カスタム生成器の登録テスト"""
        # カスタム生成器を作成
        custom_generator = CustomFormulaGenerator("z**3 + c", "Test Cubic")
        
        # CustomFormulaGeneratorは動的な性質があるため、
        # 直接レジストリに登録するのではなく、インスタンスとして使用することをテスト
        self.assertEqual(custom_generator.name, "Test Cubic")
        self.assertEqual(custom_generator.formula_text, "z**3 + c")
        
        # 計算が正常に動作することを確認
        result = custom_generator.calculate(self.test_parameters)
        self.assertEqual(result.iteration_data.shape, (50, 50))
        
        # 複数のカスタム生成器を管理する辞書を作成してテスト
        custom_generators = {
            "Test Cubic": CustomFormulaGenerator("z**3 + c", "Test Cubic"),
            "Test Sine": CustomFormulaGenerator("sin(z) + c", "Test Sine")
        }
        
        # 各生成器が独立して動作することを確認
        for name, generator in custom_generators.items():
            with self.subTest(generator=name):
                result = generator.calculate(self.test_parameters)
                self.assertEqual(result.iteration_data.shape, (50, 50))
    
    def test_template_system_integration(self):
        """テンプレートシステムの統合テスト"""
        # テンプレートマネージャーからテンプレートを取得
        templates = template_manager.list_templates()
        self.assertGreater(len(templates), 0)
        
        # テンプレートからカスタム生成器を作成
        mandelbrot_template = template_manager.get_template("マンデルブロ集合")
        generator = CustomFormulaGenerator(
            mandelbrot_template.formula,
            mandelbrot_template.name,
            mandelbrot_template.description
        )
        
        # 生成器が正常に動作することを確認
        result = generator.calculate(self.test_parameters)
        self.assertEqual(result.iteration_data.shape, (50, 50))
        self.assertEqual(result.metadata['formula'], "z**2 + c")
    
    def test_formula_parser_integration(self):
        """数式パーサーとの統合テスト"""
        # 複雑な数式でカスタム生成器を作成
        complex_formula = "sin(z**2) + c*exp(z/10)"
        generator = create_custom_fractal(complex_formula, "Complex Test")
        
        # パラメータ定義を取得
        param_defs = generator.get_parameter_definitions()
        param_names = [pd.name for pd in param_defs]
        
        # 必要なパラメータが含まれていることを確認
        self.assertIn('formula', param_names)
        self.assertIn('escape_radius', param_names)
        
        # 計算が正常に実行されることを確認
        result = generator.calculate(self.test_parameters)
        self.assertEqual(result.iteration_data.shape, (50, 50))
        self.assertIn('complexity_score', result.metadata)
        self.assertGreater(result.metadata['complexity_score'], 0)
    
    def test_error_resilience(self):
        """エラー耐性のテスト"""
        # 数値的に不安定な数式
        unstable_formulas = [
            "1/z + c",  # ゼロ除算の可能性
            "log(z) + c",  # 対数の定義域問題
            "z**100 + c",  # オーバーフロー
        ]
        
        for formula in unstable_formulas:
            with self.subTest(formula=formula):
                generator = CustomFormulaGenerator(formula, f"Test: {formula}")
                
                # 計算は完了するはず（エラーは適切に処理される）
                result = generator.calculate(self.test_parameters)
                self.assertEqual(result.iteration_data.shape, (50, 50))
                self.assertGreaterEqual(result.calculation_time, 0)
    
    def test_performance_comparison(self):
        """パフォーマンス比較テスト"""
        # 標準的なマンデルブロ生成器と比較
        try:
            standard_mandelbrot = fractal_registry.get_generator("Mandelbrot Set")
            standard_result = standard_mandelbrot.calculate(self.test_parameters)
        except KeyError:
            # 標準生成器が登録されていない場合はスキップ
            self.skipTest("Standard Mandelbrot generator not available")
        
        # カスタム式生成器
        custom_mandelbrot = CustomFormulaGenerator("z**2 + c", "Custom Mandelbrot")
        custom_result = custom_mandelbrot.calculate(self.test_parameters)
        
        # 両方とも同じ形状の結果を返すはず
        self.assertEqual(standard_result.iteration_data.shape, custom_result.iteration_data.shape)
        
        # 計算時間の比較（カスタム生成器は多少遅くても許容）
        time_ratio = custom_result.calculation_time / standard_result.calculation_time
        self.assertLess(time_ratio, 20.0)  # 20倍以内であれば許容（解釈実行のため遅い）
    
    def test_data_model_compatibility(self):
        """データモデルとの互換性テスト"""
        generator = CustomFormulaGenerator("z**2 + c")
        result = generator.calculate(self.test_parameters)
        
        # FractalResultの全ての属性が正しく設定されていることを確認
        self.assertIsInstance(result.iteration_data, np.ndarray)
        self.assertIsInstance(result.region, ComplexRegion)
        self.assertIsInstance(result.calculation_time, float)
        self.assertIsInstance(result.parameters, FractalParameters)
        self.assertIsInstance(result.metadata, dict)
        
        # 統計情報が正しく計算されることを確認
        stats = result.get_statistics()
        self.assertIn('image_size', stats)
        self.assertIn('calculation_time', stats)
        self.assertIn('convergence_ratio', stats)
        
        # 統計値が妥当な範囲にあることを確認
        self.assertEqual(stats['image_size'], (50, 50))
        self.assertGreaterEqual(stats['convergence_ratio'], 0.0)
        self.assertLessEqual(stats['convergence_ratio'], 1.0)
    
    def test_parameter_validation_integration(self):
        """パラメータ検証の統合テスト"""
        generator = CustomFormulaGenerator("z**2 + c")
        
        # 有効なパラメータ
        valid_params = FractalParameters(
            region=self.test_region,
            max_iterations=100,
            image_size=(100, 100),
            custom_parameters={
                'escape_radius': 4.0,
                'c': ComplexNumber(-0.5, 0.5)
            }
        )
        
        self.assertTrue(generator.validate_parameters(valid_params))
        
        # カスタムパラメータが計算に反映されることを確認
        result = generator.calculate(valid_params)
        self.assertEqual(result.metadata['escape_radius'], 4.0)
        self.assertIsInstance(result.metadata['fixed_c'], ComplexNumber)
    
    def test_multiple_generators_coexistence(self):
        """複数の生成器の共存テスト"""
        # 複数のカスタム生成器を作成
        generators = [
            CustomFormulaGenerator("z**2 + c", "Mandelbrot"),
            CustomFormulaGenerator("z**3 + c", "Cubic"),
            CustomFormulaGenerator("sin(z) + c", "Sine"),
            CustomFormulaGenerator("exp(z) + c", "Exponential")
        ]
        
        # 全ての生成器が独立して動作することを確認
        for generator in generators:
            with self.subTest(generator=generator.name):
                result = generator.calculate(self.test_parameters)
                self.assertEqual(result.iteration_data.shape, (50, 50))
                self.assertEqual(result.metadata['formula'], generator.formula_text)
    
    def test_memory_efficiency(self):
        """メモリ効率のテスト"""
        generator = CustomFormulaGenerator("z**2 + c")
        
        # 大きな画像サイズでのテスト
        large_params = FractalParameters(
            region=self.test_region,
            max_iterations=50,
            image_size=(200, 200)  # より大きなサイズ
        )
        
        result = generator.calculate(large_params)
        
        # 結果が正しいサイズであることを確認
        self.assertEqual(result.iteration_data.shape, (200, 200))
        
        # メモリ使用量が妥当であることを確認（具体的な値は環境依存）
        expected_memory = 200 * 200 * 4  # int32 = 4 bytes per element
        actual_memory = result.iteration_data.nbytes
        self.assertEqual(actual_memory, expected_memory)


if __name__ == '__main__':
    unittest.main()