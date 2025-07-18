# フラクタルエディタ プラグイン開発ガイド

このガイドでは、フラクタルエディタ用のカスタムプラグインを開発する方法について説明します。

## 概要

フラクタルエディタのプラグインシステムを使用すると、独自のフラクタル生成アルゴリズムを実装し、アプリケーションに統合できます。プラグインは動的に読み込まれ、メインアプリケーションと同じUIで使用できます。

## 基本的なプラグイン構造

プラグインは以下の2つの主要コンポーネントで構成されます：

1. **フラクタル生成器** (`FractalGenerator`を継承)
2. **プラグインクラス** (`FractalPlugin`を継承)

## 簡単な開始方法

### 1. SimpleFractalGeneratorを使用

最も簡単な方法は、`SimpleFractalGenerator`を継承することです：

```python
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
        """単一点でのフラクタル計算"""
        z = complex(0, 0)
        power = kwargs.get('power', 2.0)
        
        for n in range(max_iterations):
            if abs(z) > 2.0:
                return n
            z = z**power + c
        
        return max_iterations

class MyFractalPlugin(SimplePlugin):
    def __init__(self):
        super().__init__(
            name="マイフラクタルプラグイン",
            version="1.0.0",
            author="あなたの名前",
            description="カスタムフラクタルプラグイン",
            generator_factory=MyFractalGenerator
        )
```

### 2. パラメータの定義

プラグインは様々なタイプのパラメータを定義できます：

```python
# 浮動小数点パラメータ
self.add_parameter(
    PluginDeveloperAPI.create_parameter_definition(
        name="zoom_factor",
        display_name="ズーム倍率",
        param_type="float",
        default_value=1.0,
        min_value=0.1,
        max_value=100.0,
        description="表示のズーム倍率"
    )
)

# 整数パラメータ
self.add_parameter(
    PluginDeveloperAPI.create_parameter_definition(
        name="iterations",
        display_name="反復回数",
        param_type="int",
        default_value=100,
        min_value=10,
        max_value=1000,
        description="最大反復回数"
    )
)

# ブールパラメータ
self.add_parameter(
    PluginDeveloperAPI.create_parameter_definition(
        name="use_smooth_coloring",
        display_name="スムーズカラーリング",
        param_type="bool",
        default_value=True,
        description="スムーズカラーリングを使用"
    )
)

# 文字列パラメータ
self.add_parameter(
    PluginDeveloperAPI.create_parameter_definition(
        name="formula_type",
        display_name="数式タイプ",
        param_type="string",
        default_value="standard",
        description="使用する数式のタイプ"
    )
)
```

## 高度なプラグイン開発

### カスタムフラクタル生成器

より複雑なフラクタルの場合、`FractalGenerator`を直接継承できます：

```python
from fractal_editor.generators.base import FractalGenerator
from fractal_editor.models.data_models import FractalResult, ParameterDefinition
import numpy as np
import time

class AdvancedFractalGenerator(FractalGenerator):
    @property
    def name(self) -> str:
        return "高度なフラクタル"
    
    @property
    def description(self) -> str:
        return "高度なカスタムフラクタル生成器"
    
    def calculate(self, parameters) -> FractalResult:
        start_time = time.time()
        
        # カスタム計算ロジック
        width, height = parameters.image_size
        iteration_data = np.zeros((height, width), dtype=int)
        
        # 複素平面の計算
        # ... あなたのカスタムアルゴリズム ...
        
        calculation_time = time.time() - start_time
        
        return FractalResult(
            iteration_data=iteration_data,
            region=parameters.region,
            calculation_time=calculation_time
        )
    
    def get_parameter_definitions(self) -> List[ParameterDefinition]:
        return [
            # パラメータ定義のリスト
        ]
```

## プラグインのテスト

プラグインをテストするための基本的なコード：

```python
def test_my_plugin():
    # プラグインを作成
    plugin = MyFractalPlugin()
    
    # メタデータを検証
    metadata = plugin.metadata
    print(f"プラグイン名: {metadata.name}")
    print(f"バージョン: {metadata.version}")
    
    # 生成器を作成
    generator = plugin.create_generator()
    
    # テスト計算
    from fractal_editor.plugins.developer_api import PluginDeveloperAPI
    from fractal_editor.models.data_models import FractalParameters
    
    region = PluginDeveloperAPI.create_complex_region(
        center_real=0.0,
        center_imag=0.0,
        width=4.0,
        height=4.0
    )
    
    parameters = FractalParameters(
        region=region,
        max_iterations=100,
        image_size=(100, 100),
        custom_parameters={"power": 2.0}
    )
    
    result = generator.calculate(parameters)
    print(f"計算時間: {result.calculation_time:.2f}秒")

if __name__ == "__main__":
    test_my_plugin()
```

## プラグインの配布

### ファイル構造

プラグインは単一の`.py`ファイルまたはパッケージとして配布できます：

```
my_fractal_plugin.py          # 単一ファイル
# または
my_fractal_plugin/            # パッケージ
    __init__.py              # プラグインクラスを含む
    generator.py             # 生成器の実装
    utils.py                 # ユーティリティ関数
```

### インストール

ユーザーはプラグインファイルをプラグインディレクトリに配置するだけです。アプリケーションが自動的に検出して読み込みます。

## ベストプラクティス

### 1. エラーハンドリング

```python
def calculate_point(self, c: complex, max_iterations: int, **kwargs) -> int:
    try:
        z = complex(0, 0)
        for n in range(max_iterations):
            if abs(z) > 2.0:
                return n
            z = z**2 + c
        return max_iterations
    except (OverflowError, ValueError, ZeroDivisionError):
        # エラーが発生した場合は最大反復回数を返す
        return max_iterations
```

### 2. パフォーマンス最適化

- 複雑な計算は事前に計算する
- 不要な計算を避ける
- NumPyを活用する（可能な場合）

### 3. ユーザビリティ

- 分かりやすいパラメータ名と説明を使用
- 適切なデフォルト値を設定
- 妥当な範囲制限を設定

## サンプルプラグイン

以下のサンプルプラグインが参考として提供されています：

1. **バーニングシップフラクタル** (`burning_ship_plugin.py`)
   - 絶対値を使用したマンデルブロ集合の変形

2. **トリコーンフラクタル** (`tricorn_plugin.py`)
   - 複素共役を使用したフラクタル

これらのサンプルは`fractal_editor/plugins/samples/`ディレクトリにあります。

## トラブルシューティング

### よくある問題

1. **プラグインが読み込まれない**
   - ファイル名とクラス名を確認
   - 構文エラーがないか確認
   - 必要なインポートが正しいか確認

2. **計算エラー**
   - 数値オーバーフローの処理を追加
   - ゼロ除算の処理を追加
   - 無効な入力値の処理を追加

3. **パフォーマンスの問題**
   - 計算の複雑さを確認
   - 不要なループを避ける
   - 適切な発散判定を使用

### デバッグ

プラグインのデバッグには以下の方法が有効です：

```python
# ログ出力
print(f"計算中: c={c}, n={n}, z={z}")

# 例外の詳細表示
import traceback
try:
    # 計算コード
    pass
except Exception as e:
    print(f"エラー: {e}")
    traceback.print_exc()
```

## サポート

プラグイン開発に関する質問や問題がある場合は、以下のリソースを参照してください：

- サンプルプラグインのソースコード
- 開発者向けAPIドキュメント
- フラクタルエディタのメインドキュメント

プラグイン開発を楽しんでください！