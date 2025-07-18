"""
プラグインテンプレート生成器。
開発者が簡単にプラグインを作成できるようにテンプレートを生成します。
"""
import os
from typing import Dict, Any, Optional
from pathlib import Path


class PluginTemplateGenerator:
    """プラグインテンプレートを生成するクラス。"""
    
    @staticmethod
    def generate_basic_plugin_template(
        plugin_name: str,
        author: str,
        description: str,
        output_path: Optional[str] = None
    ) -> str:
        """
        基本的なプラグインテンプレートを生成。
        
        Args:
            plugin_name: プラグイン名
            author: 作者名
            description: プラグインの説明
            output_path: 出力パス（Noneの場合は文字列として返す）
            
        Returns:
            生成されたテンプレートコード
        """
        class_name = plugin_name.replace(" ", "").replace("-", "").replace("_", "")
        generator_class = f"{class_name}Generator"
        plugin_class = f"{class_name}Plugin"
        
        template = f'''"""
{plugin_name}プラグイン。
{description}
"""
from fractal_editor.plugins.developer_api import SimpleFractalGenerator, SimplePlugin
from fractal_editor.plugins.developer_api import PluginDeveloperAPI


class {generator_class}(SimpleFractalGenerator):
    """{plugin_name}フラクタル生成器。"""
    
    def __init__(self):
        super().__init__(
            name="{plugin_name}",
            description="{description}"
        )
        
        # パラメータを追加
        self.add_parameter(
            PluginDeveloperAPI.create_parameter_definition(
                name="power",
                display_name="べき乗",
                param_type="float",
                default_value=2.0,
                min_value=1.0,
                max_value=5.0,
                description="フラクタルのべき乗値"
            )
        )
        
        self.add_parameter(
            PluginDeveloperAPI.create_parameter_definition(
                name="escape_radius",
                display_name="発散半径",
                param_type="float",
                default_value=2.0,
                min_value=1.0,
                max_value=10.0,
                description="発散判定の半径"
            )
        )
    
    def calculate_point(self, c: complex, max_iterations: int, **kwargs) -> int:
        """{plugin_name}フラクタルの計算。"""
        z = complex(0, 0)
        power = kwargs.get('power', 2.0)
        escape_radius = kwargs.get('escape_radius', 2.0)
        
        for n in range(max_iterations):
            if abs(z) > escape_radius:
                return n
            
            # TODO: ここにあなたのフラクタル計算ロジックを実装
            z = z ** power + c
        
        return max_iterations


class {plugin_class}(SimplePlugin):
    """{plugin_name}プラグイン。"""
    
    def __init__(self):
        super().__init__(
            name="{plugin_name}",
            version="1.0.0",
            author="{author}",
            description="{description}",
            generator_factory={generator_class}
        )


# プラグインのテスト関数
def test_plugin():
    """プラグインをテストする関数。"""
    plugin = {plugin_class}()
    
    print(f"プラグイン名: {{plugin.metadata.name}}")
    print(f"バージョン: {{plugin.metadata.version}}")
    print(f"作者: {{plugin.metadata.author}}")
    print(f"説明: {{plugin.metadata.description}}")
    
    generator = plugin.create_generator()
    print(f"生成器名: {{generator.name}}")
    
    # 簡単な計算テスト
    result = generator.calculate_point(complex(0, 0), 100, power=2.0)
    print(f"テスト計算結果: {{result}}")


if __name__ == "__main__":
    test_plugin()
'''
        
        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(template)
        
        return template
    
    @staticmethod
    def generate_advanced_plugin_template(
        plugin_name: str,
        author: str,
        description: str,
        output_path: Optional[str] = None
    ) -> str:
        """
        高度なプラグインテンプレートを生成。
        
        Args:
            plugin_name: プラグイン名
            author: 作者名
            description: プラグインの説明
            output_path: 出力パス（Noneの場合は文字列として返す）
            
        Returns:
            生成されたテンプレートコード
        """
        class_name = plugin_name.replace(" ", "").replace("-", "").replace("_", "")
        generator_class = f"{class_name}Generator"
        plugin_class = f"{class_name}Plugin"
        
        template = f'''"""
{plugin_name}プラグイン（高度版）。
{description}
"""
import numpy as np
import time
from typing import List, Dict, Any
from fractal_editor.generators.base import FractalGenerator
from fractal_editor.plugins.base import FractalPlugin, PluginMetadata
from fractal_editor.models.data_models import (
    FractalParameters, FractalResult, ParameterDefinition,
    ComplexNumber, ComplexRegion
)


class {generator_class}(FractalGenerator):
    """{plugin_name}フラクタル生成器（高度版）。"""
    
    def __init__(self):
        self._name = "{plugin_name}"
        self._description = "{description}"
    
    @property
    def name(self) -> str:
        return self._name
    
    @property
    def description(self) -> str:
        return self._description
    
    def calculate(self, parameters: FractalParameters) -> FractalResult:
        """フラクタル全体を計算。"""
        start_time = time.time()
        
        width, height = parameters.image_size
        iteration_data = np.zeros((height, width), dtype=int)
        
        # 複素平面の座標を計算
        x_min = parameters.region.top_left.real
        x_max = parameters.region.bottom_right.real
        y_min = parameters.region.bottom_right.imaginary
        y_max = parameters.region.top_left.imaginary
        
        # NumPyを使用した効率的な計算
        x_coords = np.linspace(x_min, x_max, width)
        y_coords = np.linspace(y_min, y_max, height)
        X, Y = np.meshgrid(x_coords, y_coords)
        C = X + 1j * Y
        
        # カスタムパラメータを取得
        power = parameters.custom_parameters.get('power', 2.0)
        escape_radius = parameters.custom_parameters.get('escape_radius', 2.0)
        
        # フラクタル計算
        Z = np.zeros_like(C)
        for n in range(parameters.max_iterations):
            # 発散していない点のマスク
            mask = np.abs(Z) <= escape_radius
            
            # TODO: ここにあなたのフラクタル計算ロジックを実装
            Z[mask] = Z[mask] ** power + C[mask]
            
            # 発散した点の反復回数を記録
            diverged = (np.abs(Z) > escape_radius) & (iteration_data == 0)
            iteration_data[diverged] = n
        
        # 発散しなかった点は最大反復回数を設定
        iteration_data[iteration_data == 0] = parameters.max_iterations
        
        calculation_time = time.time() - start_time
        
        return FractalResult(
            iteration_data=iteration_data,
            region=parameters.region,
            calculation_time=calculation_time
        )
    
    def get_parameter_definitions(self) -> List[ParameterDefinition]:
        """パラメータ定義のリストを返す。"""
        return [
            ParameterDefinition(
                name="power",
                display_name="べき乗",
                parameter_type="float",
                default_value=2.0,
                min_value=1.0,
                max_value=5.0,
                description="フラクタルのべき乗値"
            ),
            ParameterDefinition(
                name="escape_radius",
                display_name="発散半径",
                parameter_type="float",
                default_value=2.0,
                min_value=1.0,
                max_value=10.0,
                description="発散判定の半径"
            ),
            ParameterDefinition(
                name="use_smooth_coloring",
                display_name="スムーズカラーリング",
                parameter_type="bool",
                default_value=False,
                description="スムーズカラーリングを使用"
            )
        ]


class {plugin_class}(FractalPlugin):
    """{plugin_name}プラグイン（高度版）。"""
    
    def __init__(self):
        self._metadata = PluginMetadata(
            name="{plugin_name}",
            version="1.0.0",
            author="{author}",
            description="{description}",
            min_app_version="1.0.0"
        )
        self._generator = None
    
    @property
    def metadata(self) -> PluginMetadata:
        return self._metadata
    
    def create_generator(self) -> FractalGenerator:
        """フラクタル生成器のインスタンスを作成。"""
        return {generator_class}()
    
    def initialize(self) -> bool:
        """プラグインを初期化。"""
        try:
            # 初期化処理をここに追加
            self._generator = self.create_generator()
            return True
        except Exception as e:
            print(f"プラグイン初期化エラー: {{e}}")
            return False
    
    def cleanup(self) -> None:
        """プラグインをクリーンアップ。"""
        # クリーンアップ処理をここに追加
        self._generator = None
    
    def get_configuration_schema(self) -> Dict[str, Any]:
        """設定スキーマを返す。"""
        return {{
            "type": "object",
            "properties": {{
                "default_power": {{
                    "type": "number",
                    "default": 2.0,
                    "minimum": 1.0,
                    "maximum": 5.0,
                    "description": "デフォルトのべき乗値"
                }},
                "default_escape_radius": {{
                    "type": "number",
                    "default": 2.0,
                    "minimum": 1.0,
                    "maximum": 10.0,
                    "description": "デフォルトの発散半径"
                }}
            }}
        }}


# プラグインのテスト関数
def test_plugin():
    """プラグインをテストする関数。"""
    plugin = {plugin_class}()
    
    print(f"プラグイン名: {{plugin.metadata.name}}")
    print(f"バージョン: {{plugin.metadata.version}}")
    print(f"作者: {{plugin.metadata.author}}")
    print(f"説明: {{plugin.metadata.description}}")
    
    # 初期化テスト
    if plugin.initialize():
        print("プラグイン初期化成功")
        
        generator = plugin.create_generator()
        print(f"生成器名: {{generator.name}}")
        
        # パラメータ定義のテスト
        params = generator.get_parameter_definitions()
        print(f"パラメータ数: {{len(params)}}")
        for param in params:
            print(f"  - {{param.display_name}} ({{param.parameter_type}})")
        
        plugin.cleanup()
        print("プラグインクリーンアップ完了")
    else:
        print("プラグイン初期化失敗")


if __name__ == "__main__":
    test_plugin()
'''
        
        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(template)
        
        return template
    
    @staticmethod
    def generate_formula_based_template(
        plugin_name: str,
        author: str,
        description: str,
        formula: str = "z**2 + c",
        output_path: Optional[str] = None
    ) -> str:
        """
        数式ベースのプラグインテンプレートを生成。
        
        Args:
            plugin_name: プラグイン名
            author: 作者名
            description: プラグインの説明
            formula: 使用する数式
            output_path: 出力パス（Noneの場合は文字列として返す）
            
        Returns:
            生成されたテンプレートコード
        """
        class_name = plugin_name.replace(" ", "").replace("-", "").replace("_", "")
        generator_class = f"{class_name}Generator"
        plugin_class = f"{class_name}Plugin"
        
        template = f'''"""
{plugin_name}プラグイン（数式ベース）。
{description}
数式: {formula}
"""
import cmath
from fractal_editor.plugins.developer_api import SimpleFractalGenerator, SimplePlugin
from fractal_editor.plugins.developer_api import PluginDeveloperAPI


class {generator_class}(SimpleFractalGenerator):
    """{plugin_name}フラクタル生成器（数式ベース）。"""
    
    def __init__(self):
        super().__init__(
            name="{plugin_name}",
            description="{description}\\n数式: {formula}"
        )
        
        # パラメータを追加
        self.add_parameter(
            PluginDeveloperAPI.create_parameter_definition(
                name="formula_variant",
                display_name="数式バリエーション",
                param_type="string",
                default_value="standard",
                description="使用する数式のバリエーション"
            )
        )
        
        self.add_parameter(
            PluginDeveloperAPI.create_parameter_definition(
                name="coefficient",
                display_name="係数",
                param_type="float",
                default_value=1.0,
                min_value=0.1,
                max_value=5.0,
                description="数式の係数"
            )
        )
    
    def calculate_point(self, c: complex, max_iterations: int, **kwargs) -> int:
        """{plugin_name}フラクタルの計算。"""
        z = complex(0, 0)
        formula_variant = kwargs.get('formula_variant', 'standard')
        coefficient = kwargs.get('coefficient', 1.0)
        
        for n in range(max_iterations):
            if abs(z) > 2.0:
                return n
            
            try:
                # 数式バリエーションに基づく計算
                if formula_variant == 'standard':
                    # 標準: {formula}
                    z = coefficient * ({formula.replace('z', 'z').replace('c', 'c')})
                elif formula_variant == 'conjugate':
                    # 複素共役版
                    z = coefficient * ({formula.replace('z', 'z.conjugate()').replace('c', 'c')})
                elif formula_variant == 'absolute':
                    # 絶対値版
                    z = coefficient * (complex(abs(z.real), abs(z.imag))**2 + c)
                else:
                    # デフォルト
                    z = coefficient * ({formula.replace('z', 'z').replace('c', 'c')})
                    
            except (OverflowError, ValueError, ZeroDivisionError):
                return n
        
        return max_iterations


class {plugin_class}(SimplePlugin):
    """{plugin_name}プラグイン（数式ベース）。"""
    
    def __init__(self):
        super().__init__(
            name="{plugin_name}",
            version="1.0.0",
            author="{author}",
            description="{description}",
            generator_factory={generator_class}
        )


# プラグインのテスト関数
def test_plugin():
    """プラグインをテストする関数。"""
    plugin = {plugin_class}()
    
    print(f"プラグイン名: {{plugin.metadata.name}}")
    print(f"バージョン: {{plugin.metadata.version}}")
    print(f"作者: {{plugin.metadata.author}}")
    print(f"説明: {{plugin.metadata.description}}")
    
    generator = plugin.create_generator()
    print(f"生成器名: {{generator.name}}")
    
    # 各バリエーションをテスト
    variants = ['standard', 'conjugate', 'absolute']
    for variant in variants:
        result = generator.calculate_point(
            complex(0, 0), 100, 
            formula_variant=variant, 
            coefficient=1.0
        )
        print(f"{{variant}}バリエーション結果: {{result}}")


if __name__ == "__main__":
    test_plugin()
'''
        
        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(template)
        
        return template
    
    @staticmethod
    def create_plugin_directory(
        plugin_name: str,
        author: str,
        description: str,
        base_path: str = ".",
        template_type: str = "basic"
    ) -> str:
        """
        プラグインディレクトリを作成し、テンプレートファイルを生成。
        
        Args:
            plugin_name: プラグイン名
            author: 作者名
            description: プラグインの説明
            base_path: 基本パス
            template_type: テンプレートタイプ ('basic', 'advanced', 'formula')
            
        Returns:
            作成されたディレクトリのパス
        """
        # ディレクトリ名を生成
        dir_name = plugin_name.lower().replace(" ", "_").replace("-", "_")
        plugin_dir = Path(base_path) / f"{dir_name}_plugin"
        
        # ディレクトリを作成
        plugin_dir.mkdir(exist_ok=True)
        
        # テンプレートを生成
        plugin_file = plugin_dir / "__init__.py"
        
        if template_type == "basic":
            template_code = PluginTemplateGenerator.generate_basic_plugin_template(
                plugin_name, author, description
            )
        elif template_type == "advanced":
            template_code = PluginTemplateGenerator.generate_advanced_plugin_template(
                plugin_name, author, description
            )
        elif template_type == "formula":
            template_code = PluginTemplateGenerator.generate_formula_based_template(
                plugin_name, author, description
            )
        else:
            raise ValueError(f"不明なテンプレートタイプ: {template_type}")
        
        with open(plugin_file, 'w', encoding='utf-8') as f:
            f.write(template_code)
        
        # READMEファイルを作成
        readme_content = f"""# {plugin_name}プラグイン

{description}

## 作者
{author}

## インストール方法

1. このディレクトリ全体をフラクタルエディタのプラグインディレクトリにコピー
2. フラクタルエディタを再起動
3. プラグインメニューから「{plugin_name}」を選択

## 開発

このプラグインを修正する場合は、`__init__.py`ファイルを編集してください。

## テスト

```bash
python __init__.py
```

でプラグインをテストできます。
"""
        
        readme_file = plugin_dir / "README.md"
        with open(readme_file, 'w', encoding='utf-8') as f:
            f.write(readme_content)
        
        return str(plugin_dir)


# コマンドライン使用例
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 4:
        print("使用方法: python template_generator.py <プラグイン名> <作者> <説明> [テンプレートタイプ]")
        print("テンプレートタイプ: basic, advanced, formula")
        sys.exit(1)
    
    plugin_name = sys.argv[1]
    author = sys.argv[2]
    description = sys.argv[3]
    template_type = sys.argv[4] if len(sys.argv) > 4 else "basic"
    
    try:
        plugin_dir = PluginTemplateGenerator.create_plugin_directory(
            plugin_name, author, description, template_type=template_type
        )
        print(f"プラグインテンプレートを作成しました: {plugin_dir}")
    except Exception as e:
        print(f"エラー: {e}")
        sys.exit(1)