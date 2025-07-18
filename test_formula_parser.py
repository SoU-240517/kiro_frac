"""
数式パーサーのテスト

FormulaParserクラスとFormulaTemplateManagerクラスの機能をテストします。
"""

import unittest
import math
import cmath
from fractal_editor.services.formula_parser import (
    FormulaParser, FormulaValidationError, FormulaEvaluationError,
    FormulaTemplate, FormulaTemplateManager, template_manager
)


class TestFormulaParser(unittest.TestCase):
    """FormulaParserクラスのテスト"""
    
    def test_basic_formula_parsing(self):
        """基本的な数式の解析テスト"""
        # 有効な数式
        valid_formulas = [
            "z**2 + c",
            "z * z + c",
            "sin(z) + c",
            "exp(z) + c",
            "z**3 + c",
            "abs(z) + c",
            "conj(z) + c",
            "sqrt(z) + c",
            "log(z) + c"
        ]
        
        for formula in valid_formulas:
            with self.subTest(formula=formula):
                parser = FormulaParser(formula)
                self.assertIsNotNone(parser.compiled_formula)
    
    def test_invalid_formula_rejection(self):
        """無効な数式の拒否テスト"""
        invalid_formulas = [
            "import os",  # インポート文
            "os.system('ls')",  # 危険な関数呼び出し
            "exec('print(1)')",  # exec関数
            "eval('1+1')",  # eval関数
            "__import__('os')",  # __import__関数
            "open('file.txt')",  # ファイル操作
            "x + y",  # 許可されていない変数
            "z.real",  # 属性アクセス（直接的）
            "z[0]",  # インデックスアクセス
            "[1, 2, 3]",  # リスト
            "{'a': 1}",  # 辞書
            "z if True else c",  # 条件式
            "z and c",  # ブール演算子
            "z == c",  # 比較演算子
        ]
        
        for formula in invalid_formulas:
            with self.subTest(formula=formula):
                with self.assertRaises(FormulaValidationError):
                    FormulaParser(formula)
    
    def test_allowed_variables(self):
        """許可された変数のテスト"""
        allowed_vars = ['z', 'c', 'n', 'pi', 'e', 'i', 'j']
        
        for var in allowed_vars:
            with self.subTest(variable=var):
                parser = FormulaParser(var)
                self.assertIsNotNone(parser.compiled_formula)
    
    def test_allowed_functions(self):
        """許可された関数のテスト"""
        # 1つの引数を取る関数
        single_arg_functions = [
            'sin', 'cos', 'tan', 'sinh', 'cosh', 'tanh',
            'asin', 'acos', 'atan', 'asinh', 'acosh', 'atanh',
            'exp', 'log', 'log10', 'sqrt',
            'abs', 'conj', 'real', 'imag', 'phase',
            'floor', 'ceil', 'round'
        ]
        
        # 複数の引数を取る関数
        multi_arg_functions = {
            'min': 'min(z, c)',
            'max': 'max(z, c)',
            'rect': 'rect(1, 2)'
        }
        
        for func in single_arg_functions:
            with self.subTest(function=func):
                formula = f"{func}(z)"
                parser = FormulaParser(formula)
                self.assertIsNotNone(parser.compiled_formula)
        
        for func, formula in multi_arg_functions.items():
            with self.subTest(function=func):
                parser = FormulaParser(formula)
                self.assertIsNotNone(parser.compiled_formula)
    
    def test_formula_evaluation(self):
        """数式評価のテスト"""
        test_cases = [
            # (formula, z, c, n, expected_result)
            ("z**2 + c", 1+1j, 0+0j, 0, 2j),
            ("z + c", 1+0j, 2+0j, 0, 3+0j),
            ("z * c", 2+0j, 3+0j, 0, 6+0j),
            ("abs(z)", 3+4j, 0+0j, 0, 5+0j),
            ("conj(z)", 1+2j, 0+0j, 0, 1-2j),
            ("real(z)", 3+4j, 0+0j, 0, 3+0j),
            ("imag(z)", 3+4j, 0+0j, 0, 4+0j),
            ("pi", 0+0j, 0+0j, 0, math.pi+0j),
            ("e", 0+0j, 0+0j, 0, math.e+0j),
            ("i", 0+0j, 0+0j, 0, 1j),
            ("n", 0+0j, 0+0j, 5, 5+0j),
        ]
        
        for formula, z, c, n, expected in test_cases:
            with self.subTest(formula=formula):
                parser = FormulaParser(formula)
                result = parser.evaluate(z, c, n)
                self.assertAlmostEqual(result, expected, places=10)
    
    def test_complex_formula_evaluation(self):
        """複雑な数式の評価テスト"""
        parser = FormulaParser("z**2 + c")
        
        # マンデルブロ集合の典型的な計算
        z = 0+0j
        c = -0.5+0.5j
        
        # 数回反復
        for i in range(5):
            z = parser.evaluate(z, c, i)
            self.assertIsInstance(z, complex)
    
    def test_evaluation_errors(self):
        """評価エラーのテスト"""
        # ゼロ除算
        parser = FormulaParser("1 / z")
        with self.assertRaises(FormulaEvaluationError):
            parser.evaluate(0+0j, 0+0j, 0)
        
        # 対数の定義域エラー（実装によっては複素数で処理される場合もある）
        parser = FormulaParser("log(z)")
        try:
            result = parser.evaluate(0+0j, 0+0j, 0)
            # 複素数の対数は定義されているので、エラーにならない場合もある
            self.assertTrue(math.isinf(result.real) or math.isnan(result.real))
        except FormulaEvaluationError:
            # エラーになる場合もある
            pass
    
    def test_get_used_variables(self):
        """使用変数の取得テスト"""
        test_cases = [
            ("z**2 + c", {'z', 'c'}),
            ("sin(z)", {'z'}),
            ("c", {'c'}),
            ("pi + e", {'pi', 'e'}),
            ("z + c + n", {'z', 'c', 'n'}),
            ("1 + 2", set()),  # 定数のみ
        ]
        
        for formula, expected_vars in test_cases:
            with self.subTest(formula=formula):
                parser = FormulaParser(formula)
                used_vars = parser.get_used_variables()
                self.assertEqual(used_vars, expected_vars)
    
    def test_complexity_score(self):
        """複雑度スコアのテスト"""
        test_cases = [
            ("z", 0.5),  # 変数参照のみ
            ("z + c", 1.5),  # 加算 + 2つの変数
            ("z**2 + c", 2.5),  # 累乗 + 加算 + 2つの変数
            ("sin(z**2) + c", 4.5),  # 関数 + 累乗 + 加算 + 2つの変数
        ]
        
        for formula, expected_min_score in test_cases:
            with self.subTest(formula=formula):
                parser = FormulaParser(formula)
                score = parser.get_complexity_score()
                self.assertGreaterEqual(score, expected_min_score)
    
    def test_syntax_validation(self):
        """構文検証のテスト"""
        valid_formulas = ["z**2 + c", "sin(z)", "abs(z) + conj(c)"]
        invalid_formulas = ["z +", "sin()", "unknown_func(z)"]
        
        for formula in valid_formulas:
            with self.subTest(formula=formula, valid=True):
                self.assertTrue(FormulaParser.validate_syntax_only(formula))
        
        for formula in invalid_formulas:
            with self.subTest(formula=formula, valid=False):
                self.assertFalse(FormulaParser.validate_syntax_only(formula))
    
    def test_formula_testing(self):
        """数式テスト機能のテスト"""
        result = FormulaParser.test_formula("z**2 + c")
        
        self.assertTrue(result['valid'])
        self.assertEqual(result['formula'], "z**2 + c")
        self.assertGreater(result['complexity'], 0)
        self.assertIn('z', result['variables'])
        self.assertIn('c', result['variables'])
        self.assertIsInstance(result['test_results'], list)
        self.assertGreater(len(result['test_results']), 0)
    
    def test_empty_formula(self):
        """空の数式のテスト"""
        with self.assertRaises(FormulaValidationError):
            FormulaParser("")
        
        with self.assertRaises(FormulaValidationError):
            FormulaParser("   ")


class TestFormulaTemplate(unittest.TestCase):
    """FormulaTemplateクラスのテスト"""
    
    def test_template_creation(self):
        """テンプレート作成のテスト"""
        template = FormulaTemplate(
            name="Test Template",
            formula="z**2 + c",
            description="Test description"
        )
        
        self.assertEqual(template.name, "Test Template")
        self.assertEqual(template.formula, "z**2 + c")
        self.assertEqual(template.description, "Test description")
        self.assertEqual(template.example_params, {})
    
    def test_template_with_params(self):
        """パラメータ付きテンプレートのテスト"""
        params = {'max_iterations': 100, 'c': 0.5+0.5j}
        template = FormulaTemplate(
            name="Test Template",
            formula="z**2 + c",
            description="Test description",
            example_params=params
        )
        
        self.assertEqual(template.example_params, params)


class TestFormulaTemplateManager(unittest.TestCase):
    """FormulaTemplateManagerクラスのテスト"""
    
    def setUp(self):
        """テスト用のテンプレートマネージャーを作成"""
        self.manager = FormulaTemplateManager()
    
    def test_get_template(self):
        """テンプレート取得のテスト"""
        template = self.manager.get_template("マンデルブロ集合")
        self.assertEqual(template.name, "マンデルブロ集合")
        self.assertEqual(template.formula, "z**2 + c")
    
    def test_get_nonexistent_template(self):
        """存在しないテンプレートの取得テスト"""
        with self.assertRaises(KeyError):
            self.manager.get_template("Nonexistent Template")
    
    def test_list_templates(self):
        """テンプレートリスト取得のテスト"""
        templates = self.manager.list_templates()
        self.assertIsInstance(templates, list)
        self.assertGreater(len(templates), 0)
        self.assertIn("マンデルブロ集合", templates)
    
    def test_get_all_templates(self):
        """全テンプレート取得のテスト"""
        all_templates = self.manager.get_all_templates()
        self.assertIsInstance(all_templates, dict)
        self.assertGreater(len(all_templates), 0)
        self.assertIn("マンデルブロ集合", all_templates)
    
    def test_add_custom_template(self):
        """カスタムテンプレート追加のテスト"""
        custom_template = FormulaTemplate(
            name="Custom Test",
            formula="z**3 + c",
            description="Custom test template"
        )
        
        self.manager.add_custom_template(custom_template)
        
        # 追加されたテンプレートを取得できることを確認
        retrieved = self.manager.get_template("Custom Test")
        self.assertEqual(retrieved.name, "Custom Test")
        self.assertEqual(retrieved.formula, "z**3 + c")
    
    def test_add_invalid_custom_template(self):
        """無効なカスタムテンプレート追加のテスト"""
        invalid_template = FormulaTemplate(
            name="Invalid Test",
            formula="invalid_function(z)",
            description="Invalid test template"
        )
        
        with self.assertRaises(ValueError):
            self.manager.add_custom_template(invalid_template)
    
    def test_remove_custom_template(self):
        """カスタムテンプレート削除のテスト"""
        # まずカスタムテンプレートを追加
        custom_template = FormulaTemplate(
            name="To Be Removed",
            formula="z**2 + c",
            description="Template to be removed"
        )
        self.manager.add_custom_template(custom_template)
        
        # 削除
        result = self.manager.remove_custom_template("To Be Removed")
        self.assertTrue(result)
        
        # 削除されたことを確認
        with self.assertRaises(KeyError):
            self.manager.get_template("To Be Removed")
        
        # 存在しないテンプレートの削除
        result = self.manager.remove_custom_template("Nonexistent")
        self.assertFalse(result)
    
    def test_search_templates(self):
        """テンプレート検索のテスト"""
        # 名前で検索
        results = self.manager.search_templates("マンデルブロ")
        self.assertGreater(len(results), 0)
        self.assertTrue(any("マンデルブロ" in t.name for t in results))
        
        # 説明で検索
        results = self.manager.search_templates("指数")
        self.assertGreater(len(results), 0)
        
        # 数式で検索
        results = self.manager.search_templates("sin")
        self.assertGreater(len(results), 0)
        
        # 見つからない検索
        results = self.manager.search_templates("nonexistent_query_12345")
        self.assertEqual(len(results), 0)


class TestGlobalTemplateManager(unittest.TestCase):
    """グローバルテンプレートマネージャーのテスト"""
    
    def test_global_manager_exists(self):
        """グローバルマネージャーが存在することを確認"""
        self.assertIsInstance(template_manager, FormulaTemplateManager)
    
    def test_global_manager_has_templates(self):
        """グローバルマネージャーにテンプレートが含まれることを確認"""
        templates = template_manager.list_templates()
        self.assertGreater(len(templates), 0)


if __name__ == '__main__':
    unittest.main()