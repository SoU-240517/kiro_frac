"""
カスタム式フラクタル生成器

ユーザー定義の数式を使用してフラクタルを生成するクラスを提供します。
FormulaParserを使用して安全に数式を評価し、フラクタル計算を行います。
"""

import time
import numpy as np
from typing import List, Dict, Any, Optional
from ..models.data_models import (
    FractalParameters, FractalResult, ParameterDefinition, ComplexNumber
)
from ..services.formula_parser import (
    FormulaParser, FormulaValidationError, FormulaEvaluationError,
    FormulaTemplate, template_manager
)
from .base import FractalGenerator


class CustomFormulaGenerator(FractalGenerator):
    """ユーザー定義式によるフラクタル生成器"""
    
    def __init__(self, formula: str, name: str = "Custom Formula", description: str = ""):
        """
        カスタム式フラクタル生成器を初期化
        
        Args:
            formula: フラクタル生成に使用する数式
            name: 生成器の名前
            description: 生成器の説明
            
        Raises:
            FormulaValidationError: 数式が無効な場合
        """
        self._name = name
        self._description = description or f"Custom fractal with formula: {formula}"
        self.formula_text = formula
        
        try:
            self.formula_parser = FormulaParser(formula)
        except FormulaValidationError as e:
            raise FormulaValidationError(f"Invalid formula for CustomFormulaGenerator: {e}")
        
        # 数式の複雑度に基づいてデフォルトの最大反復回数を調整
        complexity = self.formula_parser.get_complexity_score()
        if complexity > 5:
            self._default_max_iterations = 50  # 複雑な式は反復回数を少なく
        elif complexity > 3:
            self._default_max_iterations = 100
        else:
            self._default_max_iterations = 200  # シンプルな式は多めに
    
    @property
    def name(self) -> str:
        """生成器の名前を取得"""
        return self._name
    
    @property
    def description(self) -> str:
        """生成器の説明を取得"""
        return self._description
    
    def calculate(self, parameters: FractalParameters) -> FractalResult:
        """
        カスタム式でフラクタルを計算
        
        Args:
            parameters: フラクタル計算パラメータ
            
        Returns:
            計算結果
            
        Raises:
            ValueError: パラメータが無効な場合
            FormulaEvaluationError: 数式評価中にエラーが発生した場合
        """
        start_time = time.time()
        
        width, height = parameters.image_size
        iteration_data = np.zeros((height, width), dtype=np.int32)
        
        # 複素平面の座標を計算
        x_min = parameters.region.top_left.real
        x_max = parameters.region.bottom_right.real
        y_min = parameters.region.bottom_right.imaginary
        y_max = parameters.region.top_left.imaginary
        
        # 座標配列を生成
        x_coords = np.linspace(x_min, x_max, width)
        y_coords = np.linspace(y_min, y_max, height)
        
        # カスタムパラメータから固定値cを取得（ジュリア集合用）
        fixed_c = parameters.get_custom_parameter('c', None)
        
        # 発散判定の閾値
        escape_radius = parameters.get_custom_parameter('escape_radius', 2.0)
        escape_radius_squared = escape_radius * escape_radius
        
        # 各ピクセルについて計算
        for i, y in enumerate(y_coords):
            for j, x in enumerate(x_coords):
                # 初期値の設定
                if fixed_c is not None:
                    # ジュリア集合の場合：zが変数、cが固定
                    z = complex(x, y)
                    if isinstance(fixed_c, ComplexNumber):
                        c = fixed_c.to_complex()
                    else:
                        c = complex(fixed_c)
                else:
                    # マンデルブロ集合の場合：z=0、cが変数
                    z = complex(0, 0)
                    c = complex(x, y)
                
                # 反復計算
                for n in range(parameters.max_iterations):
                    try:
                        # 数式を評価
                        z = self.formula_parser.evaluate(z, c, n)
                        
                        # 発散判定
                        if z.real * z.real + z.imag * z.imag > escape_radius_squared:
                            iteration_data[i, j] = n
                            break
                            
                    except (OverflowError, ZeroDivisionError, FormulaEvaluationError):
                        # 数値エラーが発生した場合は発散とみなす
                        iteration_data[i, j] = n
                        break
                    except Exception:
                        # その他のエラーも発散とみなす
                        iteration_data[i, j] = n
                        break
                else:
                    # 最大反復回数に達した場合（収束）
                    iteration_data[i, j] = parameters.max_iterations
        
        calculation_time = time.time() - start_time
        
        # メタデータを作成
        metadata = {
            'formula': self.formula_text,
            'complexity_score': self.formula_parser.get_complexity_score(),
            'used_variables': list(self.formula_parser.get_used_variables()),
            'escape_radius': escape_radius,
            'fixed_c': fixed_c
        }
        
        return FractalResult(
            iteration_data=iteration_data,
            region=parameters.region,
            calculation_time=calculation_time,
            parameters=parameters,
            metadata=metadata
        )
    
    def get_parameter_definitions(self) -> List[ParameterDefinition]:
        """
        このフラクタル生成器のパラメータ定義を取得
        
        Returns:
            パラメータ定義のリスト
        """
        definitions = [
            ParameterDefinition(
                name="formula",
                display_name="数式",
                parameter_type="formula",
                default_value=self.formula_text,
                description="フラクタル生成式 (例: z**2 + c)"
            ),
            ParameterDefinition(
                name="escape_radius",
                display_name="発散半径",
                parameter_type="float",
                default_value=2.0,
                min_value=1.0,
                max_value=100.0,
                description="発散判定に使用する半径"
            )
        ]
        
        # 数式で使用されている変数に応じて追加パラメータを定義
        used_vars = self.formula_parser.get_used_variables()
        
        if 'c' in used_vars:
            # cが使用されている場合、固定値として設定できるオプションを追加
            definitions.append(
                ParameterDefinition(
                    name="c",
                    display_name="複素数パラメータ c",
                    parameter_type="complex",
                    default_value=ComplexNumber(-0.7269, 0.1889),  # 美しいジュリア集合の例
                    description="ジュリア集合用の固定複素数パラメータ（Noneの場合はマンデルブロ集合）"
                )
            )
        
        return definitions
    
    def update_formula(self, new_formula: str) -> None:
        """
        数式を更新
        
        Args:
            new_formula: 新しい数式
            
        Raises:
            FormulaValidationError: 新しい数式が無効な場合
        """
        try:
            new_parser = FormulaParser(new_formula)
            self.formula_parser = new_parser
            self.formula_text = new_formula
            self._description = f"Custom fractal with formula: {new_formula}"
            
            # 複雑度に基づいてデフォルト反復回数を再調整
            complexity = self.formula_parser.get_complexity_score()
            if complexity > 5:
                self._default_max_iterations = 50
            elif complexity > 3:
                self._default_max_iterations = 100
            else:
                self._default_max_iterations = 200
                
        except FormulaValidationError as e:
            raise FormulaValidationError(f"Cannot update formula: {e}")
    
    def get_recommended_parameters(self) -> Dict[str, Any]:
        """
        この数式に推奨されるパラメータを取得
        
        Returns:
            推奨パラメータの辞書
        """
        complexity = self.formula_parser.get_complexity_score()
        used_vars = self.formula_parser.get_used_variables()
        
        recommendations = {
            'max_iterations': self._default_max_iterations,
            'escape_radius': 2.0
        }
        
        # 数式の特性に基づいた推奨値
        if 'exp' in self.formula_text or 'sinh' in self.formula_text or 'cosh' in self.formula_text:
            # 指数関数系は発散が早い
            recommendations['max_iterations'] = min(50, self._default_max_iterations)
            recommendations['escape_radius'] = 10.0
        
        if 'log' in self.formula_text:
            # 対数関数系は特別な処理が必要
            recommendations['escape_radius'] = 100.0
        
        if 'sin' in self.formula_text or 'cos' in self.formula_text:
            # 三角関数系は周期的
            recommendations['escape_radius'] = 10.0
        
        if 'c' in used_vars:
            # ジュリア集合の場合の推奨c値
            recommendations['c'] = ComplexNumber(-0.7269, 0.1889)
        
        return recommendations
    
    @classmethod
    def from_template(cls, template_name: str) -> 'CustomFormulaGenerator':
        """
        テンプレートからカスタム式生成器を作成
        
        Args:
            template_name: テンプレート名
            
        Returns:
            CustomFormulaGenerator インスタンス
            
        Raises:
            KeyError: テンプレートが見つからない場合
            FormulaValidationError: テンプレートの数式が無効な場合
        """
        template = template_manager.get_template(template_name)
        
        return cls(
            formula=template.formula,
            name=template.name,
            description=template.description
        )
    
    @classmethod
    def create_mandelbrot_variant(cls, power: int = 2) -> 'CustomFormulaGenerator':
        """
        マンデルブロ集合の変種を作成
        
        Args:
            power: 累乗数
            
        Returns:
            CustomFormulaGenerator インスタンス
        """
        if power < 2:
            raise ValueError("Power must be at least 2")
        
        formula = f"z**{power} + c"
        name = f"{power}次マンデルブロ集合"
        description = f"{power}次のマンデルブロ集合"
        
        return cls(formula=formula, name=name, description=description)
    
    @classmethod
    def create_julia_variant(cls, c_real: float, c_imag: float, power: int = 2) -> 'CustomFormulaGenerator':
        """
        ジュリア集合の変種を作成
        
        Args:
            c_real: 複素数パラメータの実部
            c_imag: 複素数パラメータの虚部
            power: 累乗数
            
        Returns:
            CustomFormulaGenerator インスタンス
        """
        if power < 2:
            raise ValueError("Power must be at least 2")
        
        formula = f"z**{power} + c"
        name = f"ジュリア集合 (c={c_real:+.4f}{c_imag:+.4f}i)"
        description = f"{power}次のジュリア集合、c={c_real:+.4f}{c_imag:+.4f}i"
        
        generator = cls(formula=formula, name=name, description=description)
        return generator


class CustomFormulaGeneratorFactory:
    """カスタム式フラクタル生成器のファクトリクラス"""
    
    @staticmethod
    def create_from_formula(formula: str, name: str = None, description: str = None) -> CustomFormulaGenerator:
        """
        数式からカスタム生成器を作成
        
        Args:
            formula: フラクタル生成式
            name: 生成器名（省略時は自動生成）
            description: 説明（省略時は自動生成）
            
        Returns:
            CustomFormulaGenerator インスタンス
        """
        if name is None:
            name = f"Custom: {formula}"
        
        if description is None:
            description = f"Custom fractal generator with formula: {formula}"
        
        return CustomFormulaGenerator(formula, name, description)
    
    @staticmethod
    def create_from_template(template_name: str) -> CustomFormulaGenerator:
        """
        テンプレートから生成器を作成
        
        Args:
            template_name: テンプレート名
            
        Returns:
            CustomFormulaGenerator インスタンス
        """
        return CustomFormulaGenerator.from_template(template_name)
    
    @staticmethod
    def list_available_templates() -> List[str]:
        """
        利用可能なテンプレート名のリストを取得
        
        Returns:
            テンプレート名のリスト
        """
        return template_manager.list_templates()
    
    @staticmethod
    def get_template_info(template_name: str) -> Dict[str, Any]:
        """
        テンプレートの詳細情報を取得
        
        Args:
            template_name: テンプレート名
            
        Returns:
            テンプレート情報の辞書
        """
        template = template_manager.get_template(template_name)
        
        return {
            'name': template.name,
            'formula': template.formula,
            'description': template.description,
            'example_params': template.example_params
        }
    
    @staticmethod
    def validate_formula(formula: str) -> Dict[str, Any]:
        """
        数式の妥当性を検証
        
        Args:
            formula: 検証する数式
            
        Returns:
            検証結果の辞書
        """
        return FormulaParser.test_formula(formula)
    
    @staticmethod
    def create_preset_generators() -> Dict[str, CustomFormulaGenerator]:
        """
        プリセットの生成器を作成
        
        Returns:
            生成器名をキーとする辞書
        """
        presets = {}
        
        # 基本的なプリセット
        basic_presets = [
            ("マンデルブロ集合", "z**2 + c"),
            ("三次マンデルブロ", "z**3 + c"),
            ("四次マンデルブロ", "z**4 + c"),
            ("バーニングシップ", "(abs(real(z)) + abs(imag(z))*1j)**2 + c"),
            ("指数フラクタル", "exp(z) + c"),
            ("正弦フラクタル", "sin(z) + c"),
            ("対数フラクタル", "log(z) + c"),
        ]
        
        for name, formula in basic_presets:
            try:
                presets[name] = CustomFormulaGenerator(formula, name)
            except FormulaValidationError:
                # 無効な数式はスキップ
                continue
        
        return presets


# 便利な関数
def create_custom_fractal(formula: str, name: str = None) -> CustomFormulaGenerator:
    """
    カスタムフラクタル生成器を簡単に作成する便利関数
    
    Args:
        formula: フラクタル生成式
        name: 生成器名（省略可）
        
    Returns:
        CustomFormulaGenerator インスタンス
    """
    return CustomFormulaGeneratorFactory.create_from_formula(formula, name)


def create_fractal_from_template(template_name: str) -> CustomFormulaGenerator:
    """
    テンプレートからフラクタル生成器を作成する便利関数
    
    Args:
        template_name: テンプレート名
        
    Returns:
        CustomFormulaGenerator インスタンス
    """
    return CustomFormulaGeneratorFactory.create_from_template(template_name)