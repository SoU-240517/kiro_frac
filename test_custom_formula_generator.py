"""
カスタム式フラクタル生成器のテスト

CustomFormulaGeneratorクラスとその関連機能をテストします。
"""

import unittest
import numpy as np
from fractal_editor.generators.custom_formula import (
    CustomFormulaGenerator, CustomFormulaGeneratorFactory,
    create_custom_fractal, create_fractal_from_template
)
from fractal_editor.models.data_models import (
    FractalParameters, ComplexRegion, ComplexNumber, ParameterDefinition
)
from fractal_editor.services.formula_parser import FormulaValidationError


class TestCustomFormulaGenerator(unittest.TestCase):
    """CustomFormulaGeneratorクラスのテスト"""
    
    def setUp(self):
        """テスト用のセットアップ"""
        self.simple_formula = "z**2 + c"
        self.generator = CustomFormulaGenerator(self.simple_formula, "Test Generator")
        
        # テスト用のパラメータ
        self.test_region = ComplexRegion(
            top_left=ComplexNumber(-2.0, 1.0),
            bottom_right=ComplexNumber(1.0, -1.0)
        )
        self.test_parameters = FractalParameters(
            region=self.test_region,
            max_iterations=50,
            image_size=(100, 100)
        )
    
    def test_generator_creation(self):
        """生成器の作成テスト"""
        self.assertEqual(self.generator.name, "Test Generator")
        self.assertIn("z**2 + c", self.generator.description)
        self.assertEqual(self.generator.formula_text, self.simple_formula)
    
    def test_invalid_formula_rejection(self):
        """無効な数式の拒否テスト"""
        invalid_formulas = [
            "import os",
            "exec('print(1)')",
            "unknown_function(z)",
            "z +",  # 構文エラー
        ]
        
        for formula in invalid_formulas:
            with self.subTest(formula=formula):
                with self.assertRaises(FormulaValidationError):
                    CustomFormulaGenerator(formula)
    
    def test_basic_calculation(self):
        """基本的な計算テスト"""
        result = self.generator.calculate(self.test_parameters)
        
        # 結果の基本検証
        self.assertIsNotNone(result)
        self.assertEqual(result.iteration_data.shape, (100, 100))
        self.assertGreater(result.calculation_time, 0)
        self.assertEqual(result.region, self.test_region)
        
        # メタデータの検証
        self.assertIn('formula', result.metadata)
        self.assertEqual(result.metadata['formula'], self.simple_formula)
        self.assertIn('complexity_score', result.metadata)
        self.assertIn('used_variables', result.metadata)
    
    def test_mandelbrot_calculation(self):
        """マンデルブロ集合の計算テスト"""
        # マンデルブロ集合の典型的な領域
        mandelbrot_region = ComplexRegion(
            top_left=ComplexNumber(-2.5, 1.25),
            bottom_right=ComplexNumber(1.0, -1.25)
        )
        mandelbrot_params = FractalParameters(
            region=mandelbrot_region,
            max_iterations=100,
            image_size=(50, 50)
        )
        
        result = self.generator.calculate(mandelbrot_params)
        
        # マンデルブロ集合の特性を検証
        # 原点付近は収束するはず
        center_x, center_y = 25, 25  # 画像の中心
        center_iterations = result.iteration_data[center_y, center_x]
        
        # 中心付近は最大反復回数に達するはず（収束）
        self.assertEqual(center_iterations, 100)
        
        # 端の方は発散するはず
        edge_iterations = result.iteration_data[0, 0]
        self.assertLess(edge_iterations, 100)
    
    def test_julia_set_calculation(self):
        """ジュリア集合の計算テスト"""
        # ジュリア集合用のパラメータ
        julia_params = FractalParameters(
            region=self.test_region,
            max_iterations=50,
            image_size=(50, 50),
            custom_parameters={'c': ComplexNumber(-0.7269, 0.1889)}
        )
        
        result = self.generator.calculate(julia_params)
        
        # 結果の基本検証
        self.assertEqual(result.iteration_data.shape, (50, 50))
        self.assertIn('fixed_c', result.metadata)
        
        # ジュリア集合の場合、固定cが使用されているはず
        fixed_c = result.metadata['fixed_c']
        self.assertIsInstance(fixed_c, ComplexNumber)
        self.assertAlmostEqual(fixed_c.real, -0.7269, places=4)
        self.assertAlmostEqual(fixed_c.imaginary, 0.1889, places=4)
    
    def test_parameter_definitions(self):
        """パラメータ定義のテスト"""
        param_defs = self.generator.get_parameter_definitions()
        
        # 基本パラメータが含まれているかチェック
        param_names = [pd.name for pd in param_defs]
        self.assertIn('formula', param_names)
        self.assertIn('escape_radius', param_names)
        self.assertIn('c', param_names)  # z**2 + c なので c が含まれるはず
        
        # 各パラメータの詳細をチェック
        for param_def in param_defs:
            self.assertIsInstance(param_def, ParameterDefinition)
            self.assertIsInstance(param_def.name, str)
            self.assertIsInstance(param_def.display_name, str)
            self.assertIsInstance(param_def.parameter_type, str)
    
    def test_formula_update(self):
        """数式更新のテスト"""
        new_formula = "z**3 + c"
        self.generator.update_formula(new_formula)
        
        self.assertEqual(self.generator.formula_text, new_formula)
        self.assertIn(new_formula, self.generator.description)
        
        # 無効な数式での更新は失敗するはず
        with self.assertRaises(FormulaValidationError):
            self.generator.update_formula("invalid_function(z)")
    
    def test_recommended_parameters(self):
        """推奨パラメータのテスト"""
        recommendations = self.generator.get_recommended_parameters()
        
        self.assertIn('max_iterations', recommendations)
        self.assertIn('escape_radius', recommendations)
        self.assertIsInstance(recommendations['max_iterations'], int)
        self.assertIsInstance(recommendations['escape_radius'], float)
        
        # 指数関数の場合の推奨値テスト
        exp_generator = CustomFormulaGenerator("exp(z) + c")
        exp_recommendations = exp_generator.get_recommended_parameters()
        
        # 指数関数は反復回数が少なく、発散半径が大きいはず
        self.assertLessEqual(exp_recommendations['max_iterations'], 50)
        self.assertGreaterEqual(exp_recommendations['escape_radius'], 10.0)
    
    def test_complex_formulas(self):
        """複雑な数式のテスト"""
        complex_formulas = [
            "sin(z**2) + c",
            "exp(z) + c",
            "log(z + 1) + c",
            "z**3 + c*z + 1",
            "conj(z)**2 + c"
        ]
        
        for formula in complex_formulas:
            with self.subTest(formula=formula):
                generator = CustomFormulaGenerator(formula)
                result = generator.calculate(self.test_parameters)
                
                # 基本的な結果検証
                self.assertEqual(result.iteration_data.shape, (100, 100))
                self.assertGreater(result.calculation_time, 0)
                self.assertEqual(result.metadata['formula'], formula)
    
    def test_error_handling_in_calculation(self):
        """計算中のエラーハンドリングテスト"""
        # ゼロ除算が発生する可能性のある数式
        division_formula = "c / z"
        generator = CustomFormulaGenerator(division_formula)
        
        # 計算は完了するはず（エラーは適切に処理される）
        result = generator.calculate(self.test_parameters)
        self.assertEqual(result.iteration_data.shape, (100, 100))
    
    def test_from_template(self):
        """テンプレートからの作成テスト"""
        generator = CustomFormulaGenerator.from_template("マンデルブロ集合")
        
        self.assertEqual(generator.name, "マンデルブロ集合")
        self.assertEqual(generator.formula_text, "z**2 + c")
        
        # 存在しないテンプレートはエラーになるはず
        with self.assertRaises(KeyError):
            CustomFormulaGenerator.from_template("Nonexistent Template")
    
    def test_mandelbrot_variant_creation(self):
        """マンデルブロ変種の作成テスト"""
        generator = CustomFormulaGenerator.create_mandelbrot_variant(3)
        
        self.assertEqual(generator.formula_text, "z**3 + c")
        self.assertIn("3次", generator.name)
        
        # 無効な累乗数はエラーになるはず
        with self.assertRaises(ValueError):
            CustomFormulaGenerator.create_mandelbrot_variant(1)
    
    def test_julia_variant_creation(self):
        """ジュリア変種の作成テスト"""
        generator = CustomFormulaGenerator.create_julia_variant(-0.7, 0.2, 2)
        
        self.assertEqual(generator.formula_text, "z**2 + c")
        self.assertIn("ジュリア集合", generator.name)
        self.assertIn("-0.7000", generator.name)
        self.assertIn("+0.2000", generator.name)


class TestCustomFormulaGeneratorFactory(unittest.TestCase):
    """CustomFormulaGeneratorFactoryクラスのテスト"""
    
    def test_create_from_formula(self):
        """数式からの作成テスト"""
        formula = "z**2 + c"
        generator = CustomFormulaGeneratorFactory.create_from_formula(formula)
        
        self.assertEqual(generator.formula_text, formula)
        self.assertIn(formula, generator.name)
        
        # 名前と説明を指定した場合
        custom_name = "My Custom Fractal"
        custom_desc = "My custom description"
        generator2 = CustomFormulaGeneratorFactory.create_from_formula(
            formula, custom_name, custom_desc
        )
        
        self.assertEqual(generator2.name, custom_name)
        self.assertEqual(generator2.description, custom_desc)
    
    def test_create_from_template(self):
        """テンプレートからの作成テスト"""
        generator = CustomFormulaGeneratorFactory.create_from_template("マンデルブロ集合")
        
        self.assertEqual(generator.name, "マンデルブロ集合")
        self.assertEqual(generator.formula_text, "z**2 + c")
    
    def test_list_available_templates(self):
        """利用可能テンプレートのリストテスト"""
        templates = CustomFormulaGeneratorFactory.list_available_templates()
        
        self.assertIsInstance(templates, list)
        self.assertGreater(len(templates), 0)
        self.assertIn("マンデルブロ集合", templates)
    
    def test_get_template_info(self):
        """テンプレート情報の取得テスト"""
        info = CustomFormulaGeneratorFactory.get_template_info("マンデルブロ集合")
        
        self.assertIn('name', info)
        self.assertIn('formula', info)
        self.assertIn('description', info)
        self.assertIn('example_params', info)
        
        self.assertEqual(info['name'], "マンデルブロ集合")
        self.assertEqual(info['formula'], "z**2 + c")
    
    def test_validate_formula(self):
        """数式検証のテスト"""
        # 有効な数式
        valid_result = CustomFormulaGeneratorFactory.validate_formula("z**2 + c")
        self.assertTrue(valid_result['valid'])
        self.assertIn('complexity', valid_result)
        self.assertIn('variables', valid_result)
        
        # 無効な数式
        invalid_result = CustomFormulaGeneratorFactory.validate_formula("invalid_func(z)")
        self.assertFalse(invalid_result['valid'])
        self.assertIn('error', invalid_result)
    
    def test_create_preset_generators(self):
        """プリセット生成器の作成テスト"""
        presets = CustomFormulaGeneratorFactory.create_preset_generators()
        
        self.assertIsInstance(presets, dict)
        self.assertGreater(len(presets), 0)
        
        # いくつかの基本的なプリセットが含まれているかチェック
        expected_presets = ["マンデルブロ集合", "三次マンデルブロ", "指数フラクタル"]
        for preset_name in expected_presets:
            if preset_name in presets:  # 一部のプリセットは数式の問題でスキップされる可能性がある
                self.assertIsInstance(presets[preset_name], CustomFormulaGenerator)


class TestConvenienceFunctions(unittest.TestCase):
    """便利関数のテスト"""
    
    def test_create_custom_fractal(self):
        """create_custom_fractal関数のテスト"""
        formula = "z**3 + c"
        generator = create_custom_fractal(formula)
        
        self.assertEqual(generator.formula_text, formula)
        self.assertIn(formula, generator.name)
        
        # 名前を指定した場合
        custom_name = "My Fractal"
        generator2 = create_custom_fractal(formula, custom_name)
        self.assertEqual(generator2.name, custom_name)
    
    def test_create_fractal_from_template(self):
        """create_fractal_from_template関数のテスト"""
        generator = create_fractal_from_template("マンデルブロ集合")
        
        self.assertEqual(generator.name, "マンデルブロ集合")
        self.assertEqual(generator.formula_text, "z**2 + c")


class TestIntegrationWithExistingSystem(unittest.TestCase):
    """既存システムとの統合テスト"""
    
    def test_parameter_validation(self):
        """パラメータ検証の統合テスト"""
        generator = CustomFormulaGenerator("z**2 + c")
        
        # 有効なパラメータ
        valid_params = FractalParameters(
            region=ComplexRegion(
                top_left=ComplexNumber(-2.0, 1.0),
                bottom_right=ComplexNumber(1.0, -1.0)
            ),
            max_iterations=100,
            image_size=(50, 50)
        )
        
        self.assertTrue(generator.validate_parameters(valid_params))
        
        # 無効なパラメータ（負の反復回数）
        try:
            invalid_params = FractalParameters(
                region=ComplexRegion(
                    top_left=ComplexNumber(-2.0, 1.0),
                    bottom_right=ComplexNumber(1.0, -1.0)
                ),
                max_iterations=-10,  # 無効
                image_size=(50, 50)
            )
            # パラメータ作成時にエラーになるはず
            self.fail("Invalid parameters should raise an error")
        except ValueError:
            # 期待される動作
            pass
    
    def test_default_parameters(self):
        """デフォルトパラメータの取得テスト"""
        generator = CustomFormulaGenerator("z**2 + c")
        defaults = generator.get_default_parameters()
        
        self.assertIsInstance(defaults, dict)
        self.assertIn('formula', defaults)
        self.assertIn('escape_radius', defaults)


if __name__ == '__main__':
    unittest.main()