"""
プラグイン開発者向けAPI。
プラグイン開発を簡素化するためのヘルパークラスとユーティリティを提供します。
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Tuple, Callable
import numpy as np
from ..models.data_models import ComplexNumber, ComplexRegion, FractalParameters, FractalResult, ParameterDefinition
from ..generators.base import FractalGenerator
from .base import FractalPlugin, PluginMetadata


class SimpleFractalGenerator(FractalGenerator):
    """
    シンプルなフラクタル生成器の基底クラス。
    プラグイン開発者が簡単にカスタムフラクタルを実装できるように設計されています。
    """
    
    def __init__(self, name: str, description: str):
        self._name = name
        self._description = description
        self._parameter_definitions = []
    
    @property
    def name(self) -> str:
        return self._name
    
    @property
    def description(self) -> str:
        return self._description
    
    def add_parameter(self, param_def: ParameterDefinition) -> None:
        """パラメータ定義を追加。"""
        self._parameter_definitions.append(param_def)
    
    def get_parameter_definitions(self) -> List[ParameterDefinition]:
        return self._parameter_definitions.copy()
    
    @abstractmethod
    def calculate_point(self, c: complex, max_iterations: int, **kwargs) -> int:
        """
        単一の複素数点でのフラクタル計算を実行。
        
        Args:
            c: 複素数点
            max_iterations: 最大反復回数
            **kwargs: 追加のカスタムパラメータ
            
        Returns:
            その点での反復回数
        """
        pass
    
    def calculate(self, parameters: FractalParameters) -> FractalResult:
        """フラクタル全体を計算。"""
        import time
        start_time = time.time()
        
        width, height = parameters.image_size
        iteration_data = np.zeros((height, width), dtype=int)
        
        # 複素平面の座標を計算
        x_min = parameters.region.top_left.real
        x_max = parameters.region.bottom_right.real
        y_min = parameters.region.bottom_right.imaginary
        y_max = parameters.region.top_left.imaginary
        
        x_coords = np.linspace(x_min, x_max, width)
        y_coords = np.linspace(y_min, y_max, height)
        
        # 各点を計算
        for i, y in enumerate(y_coords):
            for j, x in enumerate(x_coords):
                c = complex(x, y)
                iteration_data[i, j] = self.calculate_point(
                    c, parameters.max_iterations, **parameters.custom_parameters
                )
        
        calculation_time = time.time() - start_time
        
        return FractalResult(
            iteration_data=iteration_data,
            region=parameters.region,
            calculation_time=calculation_time
        )


class SimplePlugin(FractalPlugin):
    """
    シンプルなプラグインの基底クラス。
    プラグイン開発者が最小限のコードでプラグインを作成できるように設計されています。
    """
    
    def __init__(self, name: str, version: str, author: str, description: str,
                 generator_factory: Callable[[], FractalGenerator]):
        self._metadata = PluginMetadata(
            name=name,
            version=version,
            author=author,
            description=description
        )
        self._generator_factory = generator_factory
    
    @property
    def metadata(self) -> PluginMetadata:
        return self._metadata
    
    def create_generator(self) -> FractalGenerator:
        return self._generator_factory()


@dataclass
class PluginTemplate:
    """プラグインテンプレートの定義。"""
    name: str
    description: str
    template_code: str
    example_parameters: Dict[str, Any] = field(default_factory=dict)


class PluginDeveloperAPI:
    """プラグイン開発者向けのAPIクラス。"""
    
    @staticmethod
    def create_parameter_definition(
        name: str,
        display_name: str,
        param_type: str,
        default_value: Any,
        min_value: Any = None,
        max_value: Any = None,
        description: str = ""
    ) -> ParameterDefinition:
        """
        パラメータ定義を作成するヘルパーメソッド。
        
        Args:
            name: パラメータ名
            display_name: 表示名
            param_type: パラメータタイプ ('float', 'int', 'complex', 'bool', 'string')
            default_value: デフォルト値
            min_value: 最小値（数値型の場合）
            max_value: 最大値（数値型の場合）
            description: 説明
            
        Returns:
            ParameterDefinition インスタンス
        """
        return ParameterDefinition(
            name=name,
            display_name=display_name,
            parameter_type=param_type,
            default_value=default_value,
            min_value=min_value,
            max_value=max_value,
            description=description
        )
    
    @staticmethod
    def create_complex_region(
        center_real: float = 0.0,
        center_imag: float = 0.0,
        width: float = 4.0,
        height: float = 4.0
    ) -> ComplexRegion:
        """
        複素平面領域を作成するヘルパーメソッド。
        
        Args:
            center_real: 中心の実部
            center_imag: 中心の虚部
            width: 幅
            height: 高さ
            
        Returns:
            ComplexRegion インスタンス
        """
        half_width = width / 2
        half_height = height / 2
        
        return ComplexRegion(
            top_left=ComplexNumber(
                real=center_real - half_width,
                imaginary=center_imag + half_height
            ),
            bottom_right=ComplexNumber(
                real=center_real + half_width,
                imaginary=center_imag - half_height
            )
        )
    
    @staticmethod
    def validate_plugin_metadata(metadata: PluginMetadata) -> List[str]:
        """
        プラグインメタデータを検証。
        
        Args:
            metadata: 検証するメタデータ
            
        Returns:
            エラーメッセージのリスト（空の場合は検証成功）
        """
        errors = []
        
        if not metadata.name or not metadata.name.strip():
            errors.append("プラグイン名が空です")
        
        if not metadata.version or not metadata.version.strip():
            errors.append("バージョンが空です")
        
        if not metadata.author or not metadata.author.strip():
            errors.append("作者が空です")
        
        if not metadata.description or not metadata.description.strip():
            errors.append("説明が空です")
        
        # バージョン形式の簡単な検証
        if metadata.version and not any(c.isdigit() for c in metadata.version):
            errors.append("バージョンに数字が含まれていません")
        
        return errors
    
    @staticmethod
    def get_plugin_templates() -> List[PluginTemplate]:
        """利用可能なプラグインテンプレートを取得。"""
        return [
            PluginTemplate(
                name="基本フラクタル",
                description="シンプルなフラクタル生成器のテンプレート",
                template_code="""
from fractal_editor.plugins.developer_api import SimpleFractalGenerator, SimplePlugin
from fractal_editor.plugins.developer_api import PluginDeveloperAPI

class MyFractalGenerator(SimpleFractalGenerator):
    def __init__(self):
        super().__init__("マイフラクタル", "カスタムフラクタルの説明")
        
        # パラメータを追加
        self.add_parameter(
            PluginDeveloperAPI.create_parameter_definition(
                name="power",
                display_name="べき乗",
                param_type="float",
                default_value=2.0,
                min_value=1.0,
                max_value=10.0,
                description="フラクタルのべき乗値"
            )
        )
    
    def calculate_point(self, c: complex, max_iterations: int, **kwargs) -> int:
        z = complex(0, 0)
        power = kwargs.get('power', 2.0)
        
        for n in range(max_iterations):
            if abs(z) > 2.0:
                return n
            z = z**power + c
        
        return max_iterations

# プラグインクラス
class MyFractalPlugin(SimplePlugin):
    def __init__(self):
        super().__init__(
            name="マイフラクタルプラグイン",
            version="1.0.0",
            author="あなたの名前",
            description="カスタムフラクタルプラグイン",
            generator_factory=MyFractalGenerator
        )
"""
            ),
            PluginTemplate(
                name="数式ベースフラクタル",
                description="数式を使用するフラクタル生成器のテンプレート",
                template_code="""
from fractal_editor.plugins.developer_api import SimpleFractalGenerator, SimplePlugin
from fractal_editor.plugins.developer_api import PluginDeveloperAPI
import cmath

class FormulaBased FractalGenerator(SimpleFractalGenerator):
    def __init__(self):
        super().__init__("数式フラクタル", "数式ベースのフラクタル")
        
        self.add_parameter(
            PluginDeveloperAPI.create_parameter_definition(
                name="formula_type",
                display_name="数式タイプ",
                param_type="string",
                default_value="sin",
                description="使用する数式（sin, cos, exp, log）"
            )
        )
    
    def calculate_point(self, c: complex, max_iterations: int, **kwargs) -> int:
        z = complex(0, 0)
        formula_type = kwargs.get('formula_type', 'sin')
        
        for n in range(max_iterations):
            if abs(z) > 2.0:
                return n
            
            try:
                if formula_type == 'sin':
                    z = cmath.sin(z) + c
                elif formula_type == 'cos':
                    z = cmath.cos(z) + c
                elif formula_type == 'exp':
                    z = cmath.exp(z) + c
                elif formula_type == 'log':
                    z = cmath.log(z + 1) + c
                else:
                    z = z**2 + c
            except (OverflowError, ValueError):
                return n
        
        return max_iterations

class FormulaFractalPlugin(SimplePlugin):
    def __init__(self):
        super().__init__(
            name="数式フラクタルプラグイン",
            version="1.0.0", 
            author="あなたの名前",
            description="数式ベースのフラクタルプラグイン",
            generator_factory=FormulaBasedFractalGenerator
        )
"""
            )
        ]


# 開発者向けユーティリティ関数
def create_simple_fractal_plugin(
    name: str,
    version: str,
    author: str,
    description: str,
    calculation_function: Callable[[complex, int], int]
) -> FractalPlugin:
    """
    シンプルなフラクタルプラグインを作成するヘルパー関数。
    
    Args:
        name: プラグイン名
        version: バージョン
        author: 作者
        description: 説明
        calculation_function: フラクタル計算関数
        
    Returns:
        FractalPlugin インスタンス
    """
    class CustomGenerator(SimpleFractalGenerator):
        def __init__(self):
            super().__init__(name, description)
        
        def calculate_point(self, c: complex, max_iterations: int, **kwargs) -> int:
            return calculation_function(c, max_iterations)
    
    return SimplePlugin(name, version, author, description, CustomGenerator)


def validate_calculation_function(func: Callable[[complex, int], int]) -> List[str]:
    """
    計算関数を検証。
    
    Args:
        func: 検証する関数
        
    Returns:
        エラーメッセージのリスト
    """
    errors = []
    
    try:
        # テスト計算
        result = func(complex(0, 0), 100)
        if not isinstance(result, int):
            errors.append("計算関数は整数を返す必要があります")
        if result < 0:
            errors.append("計算関数は非負の整数を返す必要があります")
    except Exception as e:
        errors.append(f"計算関数のテストに失敗: {e}")
    
    return errors