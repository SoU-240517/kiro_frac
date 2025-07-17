"""
ParameterDefinitionクラスの単体テスト

パラメータ定義システムの動作を検証します。
"""

import unittest
from fractal_editor.models.data_models import ParameterDefinition, ComplexNumber


class TestParameterDefinition(unittest.TestCase):
    """ParameterDefinitionクラスのテスト"""
    
    def test_creation_with_valid_int_parameter(self):
        """有効なint型パラメータでの作成"""
        param_def = ParameterDefinition(
            name="max_iterations",
            display_name="最大反復回数",
            parameter_type="int",
            default_value=100,
            min_value=1,
            max_value=10000,
            description="フラクタル計算の最大反復回数"
        )
        
        self.assertEqual(param_def.name, "max_iterations")
        self.assertEqual(param_def.display_name, "最大反復回数")
        self.assertEqual(param_def.parameter_type, "int")
        self.assertEqual(param_def.default_value, 100)
        self.assertEqual(param_def.min_value, 1)
        self.assertEqual(param_def.max_value, 10000)
    
    def test_creation_with_valid_float_parameter(self):
        """有効なfloat型パラメータでの作成"""
        param_def = ParameterDefinition(
            name="zoom_factor",
            display_name="ズーム倍率",
            parameter_type="float",
            default_value=1.0,
            min_value=0.1,
            max_value=100.0
        )
        
        self.assertEqual(param_def.parameter_type, "float")
        self.assertEqual(param_def.default_value, 1.0)
    
    def test_creation_with_valid_complex_parameter(self):
        """有効なcomplex型パラメータでの作成"""
        default_c = ComplexNumber(0.3, 0.5)
        param_def = ParameterDefinition(
            name="julia_c",
            display_name="ジュリア定数",
            parameter_type="complex",
            default_value=default_c
        )
        
        self.assertEqual(param_def.parameter_type, "complex")
        self.assertEqual(param_def.default_value, default_c)
    
    def test_creation_with_valid_bool_parameter(self):
        """有効なbool型パラメータでの作成"""
        param_def = ParameterDefinition(
            name="enable_anti_aliasing",
            display_name="アンチエイリアシング",
            parameter_type="bool",
            default_value=True
        )
        
        self.assertEqual(param_def.parameter_type, "bool")
        self.assertEqual(param_def.default_value, True)
    
    def test_creation_with_valid_formula_parameter(self):
        """有効なformula型パラメータでの作成"""
        param_def = ParameterDefinition(
            name="custom_formula",
            display_name="カスタム数式",
            parameter_type="formula",
            default_value="z**2 + c"
        )
        
        self.assertEqual(param_def.parameter_type, "formula")
        self.assertEqual(param_def.default_value, "z**2 + c")
    
    def test_validate_int_values(self):
        """int型値の検証"""
        param_def = ParameterDefinition(
            name="iterations",
            display_name="反復回数",
            parameter_type="int",
            default_value=100,
            min_value=1,
            max_value=1000
        )
        
        # 有効な値
        self.assertTrue(param_def.validate_value(50))
        self.assertTrue(param_def.validate_value(1))
        self.assertTrue(param_def.validate_value(1000))
        
        # 無効な値
        self.assertFalse(param_def.validate_value(0))  # 最小値未満
        self.assertFalse(param_def.validate_value(1001))  # 最大値超過
        self.assertFalse(param_def.validate_value(50.5))  # float型
        self.assertFalse(param_def.validate_value("50"))  # 文字列
    
    def test_validate_float_values(self):
        """float型値の検証"""
        param_def = ParameterDefinition(
            name="zoom",
            display_name="ズーム",
            parameter_type="float",
            default_value=1.0,
            min_value=0.1,
            max_value=10.0
        )
        
        # 有効な値
        self.assertTrue(param_def.validate_value(1.0))
        self.assertTrue(param_def.validate_value(5))  # intもOK
        self.assertTrue(param_def.validate_value(0.1))
        self.assertTrue(param_def.validate_value(10.0))
        
        # 無効な値
        self.assertFalse(param_def.validate_value(0.05))  # 最小値未満
        self.assertFalse(param_def.validate_value(15.0))  # 最大値超過
        self.assertFalse(param_def.validate_value("1.0"))  # 文字列
    
    def test_validate_bool_values(self):
        """bool型値の検証"""
        param_def = ParameterDefinition(
            name="enable_feature",
            display_name="機能有効化",
            parameter_type="bool",
            default_value=True
        )
        
        # 有効な値
        self.assertTrue(param_def.validate_value(True))
        self.assertTrue(param_def.validate_value(False))
        
        # 無効な値
        self.assertFalse(param_def.validate_value(1))  # int
        self.assertFalse(param_def.validate_value("true"))  # 文字列
        self.assertFalse(param_def.validate_value(None))
    
    def test_validate_complex_values(self):
        """complex型値の検証"""
        param_def = ParameterDefinition(
            name="complex_param",
            display_name="複素数パラメータ",
            parameter_type="complex",
            default_value=ComplexNumber(0.0, 0.0)
        )
        
        # 有効な値
        self.assertTrue(param_def.validate_value(ComplexNumber(1.0, 2.0)))
        self.assertTrue(param_def.validate_value(complex(1.0, 2.0)))
        
        # 無効な値
        self.assertFalse(param_def.validate_value(1.0))  # float
        self.assertFalse(param_def.validate_value("1+2j"))  # 文字列
    
    def test_validate_string_values(self):
        """string型値の検証"""
        param_def = ParameterDefinition(
            name="name",
            display_name="名前",
            parameter_type="string",
            default_value="default"
        )
        
        # 有効な値
        self.assertTrue(param_def.validate_value("test"))
        self.assertTrue(param_def.validate_value(""))
        
        # 無効な値
        self.assertFalse(param_def.validate_value(123))
        self.assertFalse(param_def.validate_value(None))
    
    def test_validation_with_invalid_parameter_type(self):
        """無効なパラメータタイプでの検証"""
        with self.assertRaises(ValueError):
            ParameterDefinition(
                name="test",
                display_name="テスト",
                parameter_type="invalid_type",
                default_value="test"
            )
    
    def test_validation_with_empty_name(self):
        """空の名前での検証"""
        with self.assertRaises(ValueError):
            ParameterDefinition(
                name="",
                display_name="テスト",
                parameter_type="string",
                default_value="test"
            )
        
        with self.assertRaises(ValueError):
            ParameterDefinition(
                name="   ",  # 空白のみ
                display_name="テスト",
                parameter_type="string",
                default_value="test"
            )
    
    def test_validation_with_type_mismatch(self):
        """型不整合での検証"""
        # int型なのにfloatのデフォルト値
        with self.assertRaises(ValueError):
            ParameterDefinition(
                name="test",
                display_name="テスト",
                parameter_type="int",
                default_value=1.5
            )
        
        # bool型なのに文字列のデフォルト値
        with self.assertRaises(ValueError):
            ParameterDefinition(
                name="test",
                display_name="テスト",
                parameter_type="bool",
                default_value="true"
            )
    
    def test_validation_with_invalid_range(self):
        """無効な範囲での検証"""
        # int型で無効な最小値型
        with self.assertRaises(ValueError):
            ParameterDefinition(
                name="test",
                display_name="テスト",
                parameter_type="int",
                default_value=100,
                min_value=1.5  # floatは無効
            )
        
        # float型で無効な最大値型
        with self.assertRaises(ValueError):
            ParameterDefinition(
                name="test",
                display_name="テスト",
                parameter_type="float",
                default_value=1.0,
                max_value="10"  # 文字列は無効
            )


if __name__ == '__main__':
    unittest.main()