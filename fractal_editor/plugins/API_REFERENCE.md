# プラグイン開発者向けAPIリファレンス

このドキュメントは、フラクタルエディタのプラグイン開発で使用できるすべてのクラス、メソッド、関数の詳細なリファレンスです。

## 基底クラス

### FractalPlugin

プラグインの基底クラス。すべてのプラグインはこのクラスを継承する必要があります。

```python
class FractalPlugin(ABC):
    @property
    @abstractmethod
    def metadata(self) -> PluginMetadata:
        """プラグインのメタデータを返す"""
        pass
    
    @abstractmethod
    def create_generator(self) -> FractalGenerator:
        """フラクタル生成器のインスタンスを作成"""
        pass
    
    def initialize(self) -> bool:
        """プラグインの初期化（オプション）"""
        return True
    
    def cleanup(self) -> None:
        """プラグインのクリーンアップ（オプション）"""
        pass
    
    def get_configuration_schema(self) -> Optional[Dict[str, Any]]:
        """設定スキーマを返す（オプション）"""
        return None
```

### FractalGenerator

フラクタル生成器の基底クラス。

```python
class FractalGenerator(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        """生成器の名前"""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """生成器の説明"""
        pass
    
    @abstractmethod
    def calculate(self, parameters: FractalParameters) -> FractalResult:
        """フラクタルを計算"""
        pass
    
    @abstractmethod
    def get_parameter_definitions(self) -> List[ParameterDefinition]:
        """パラメータ定義のリストを返す"""
        pass
```

## 開発者向けヘルパークラス

### SimpleFractalGenerator

シンプルなフラクタル生成器の基底クラス。点単位の計算を実装するだけで済みます。

```python
class SimpleFractalGenerator(FractalGenerator):
    def __init__(self, name: str, description: str):
        """
        Args:
            name: 生成器の名前
            description: 生成器の説明
        """
    
    def add_parameter(self, param_def: ParameterDefinition) -> None:
        """パラメータ定義を追加"""
    
    @abstractmethod
    def calculate_point(self, c: complex, max_iterations: int, **kwargs) -> int:
        """
        単一の複素数点でのフラクタル計算
        
        Args:
            c: 複素数点
            max_iterations: 最大反復回数
            **kwargs: カスタムパラメータ
            
        Returns:
            その点での反復回数
        """
        pass
```

### SimplePlugin

シンプルなプラグインの基底クラス。

```python
class SimplePlugin(FractalPlugin):
    def __init__(self, name: str, version: str, author: str, description: str,
                 generator_factory: Callable[[], FractalGenerator]):
        """
        Args:
            name: プラグイン名
            version: バージョン
            author: 作者
            description: 説明
            generator_factory: 生成器を作成する関数
        """
```

## データクラス

### PluginMetadata

プラグインのメタデータを格納するデータクラス。

```python
@dataclass
class PluginMetadata:
    name: str                           # プラグイン名
    version: str                        # バージョン
    author: str                         # 作者
    description: str                    # 説明
    min_app_version: str = "1.0.0"     # 最小アプリケーションバージョン
    dependencies: List[str] = None      # 依存関係
```

### ParameterDefinition

パラメータ定義を格納するデータクラス。

```python
@dataclass
class ParameterDefinition:
    name: str                    # パラメータ名
    display_name: str           # 表示名
    parameter_type: str         # タイプ ('float', 'int', 'complex', 'bool', 'string')
    default_value: Any          # デフォルト値
    min_value: Any = None       # 最小値
    max_value: Any = None       # 最大値
    description: str = ""       # 説明
```

### FractalParameters

フラクタル計算のパラメータを格納するデータクラス。

```python
@dataclass
class FractalParameters:
    region: ComplexRegion              # 複素平面の領域
    max_iterations: int                # 最大反復回数
    image_size: Tuple[int, int]        # 画像サイズ (width, height)
    custom_parameters: Dict[str, Any]  # カスタムパラメータ
```

### FractalResult

フラクタル計算の結果を格納するデータクラス。

```python
@dataclass
class FractalResult:
    iteration_data: np.ndarray    # 反復回数データ (2D配列)
    region: ComplexRegion         # 計算された領域
    calculation_time: float       # 計算時間（秒）
```

### ComplexRegion

複素平面の領域を表すデータクラス。

```python
@dataclass
class ComplexRegion:
    top_left: ComplexNumber      # 左上の複素数
    bottom_right: ComplexNumber  # 右下の複素数
    
    @property
    def width(self) -> float:    # 幅
    
    @property
    def height(self) -> float:   # 高さ
```

### ComplexNumber

複素数を表すデータクラス。

```python
@dataclass
class ComplexNumber:
    real: float        # 実部
    imaginary: float   # 虚部
    
    @property
    def magnitude(self) -> float:  # 絶対値
    
    def square(self) -> 'ComplexNumber':  # 二乗
    
    def __add__(self, other: 'ComplexNumber') -> 'ComplexNumber':  # 加算
```

## ユーティリティクラス

### PluginDeveloperAPI

プラグイン開発を支援するユーティリティクラス。

```python
class PluginDeveloperAPI:
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
        """パラメータ定義を作成"""
    
    @staticmethod
    def create_complex_region(
        center_real: float = 0.0,
        center_imag: float = 0.0,
        width: float = 4.0,
        height: float = 4.0
    ) -> ComplexRegion:
        """複素平面領域を作成"""
    
    @staticmethod
    def validate_plugin_metadata(metadata: PluginMetadata) -> List[str]:
        """プラグインメタデータを検証"""
    
    @staticmethod
    def get_plugin_templates() -> List[PluginTemplate]:
        """利用可能なプラグインテンプレートを取得"""
```

## ヘルパー関数

### create_simple_fractal_plugin

シンプルなフラクタルプラグインを作成するヘルパー関数。

```python
def create_simple_fractal_plugin(
    name: str,
    version: str,
    author: str,
    description: str,
    calculation_function: Callable[[complex, int], int]
) -> FractalPlugin:
    """
    シンプルなフラクタルプラグインを作成
    
    Args:
        name: プラグイン名
        version: バージョン
        author: 作者
        description: 説明
        calculation_function: フラクタル計算関数
        
    Returns:
        FractalPlugin インスタンス
    """
```

### validate_calculation_function

計算関数を検証するヘルパー関数。

```python
def validate_calculation_function(func: Callable[[complex, int], int]) -> List[str]:
    """
    計算関数を検証
    
    Args:
        func: 検証する関数
        
    Returns:
        エラーメッセージのリスト
    """
```

## パラメータタイプ

プラグインで使用できるパラメータタイプ：

### 'float'
浮動小数点数パラメータ
- `min_value`, `max_value`で範囲を指定可能
- UIではスライダーまたは数値入力フィールドとして表示

### 'int'
整数パラメータ
- `min_value`, `max_value`で範囲を指定可能
- UIではスピンボックスまたは数値入力フィールドとして表示

### 'bool'
ブール値パラメータ
- UIではチェックボックスとして表示

### 'string'
文字列パラメータ
- UIではテキスト入力フィールドとして表示

### 'complex'
複素数パラメータ
- UIでは実部と虚部の入力フィールドとして表示

## エラーハンドリング

### 例外クラス

```python
class PluginError(Exception):
    """プラグイン関連の基底例外"""

class PluginLoadError(PluginError):
    """プラグイン読み込みエラー"""

class PluginValidationError(PluginError):
    """プラグイン検証エラー"""
```

### 推奨されるエラーハンドリング

```python
def calculate_point(self, c: complex, max_iterations: int, **kwargs) -> int:
    try:
        # フラクタル計算
        z = complex(0, 0)
        for n in range(max_iterations):
            if abs(z) > 2.0:
                return n
            z = z**2 + c
        return max_iterations
    except (OverflowError, ValueError, ZeroDivisionError):
        # 数値エラーの場合は最大反復回数を返す
        return max_iterations
    except Exception:
        # その他のエラーの場合も最大反復回数を返す
        return max_iterations
```

## パフォーマンスのベストプラクティス

### 1. 効率的な発散判定

```python
# 良い例：早期終了
if abs(z) > 2.0:
    return n

# 避けるべき：不要な計算
if z.real*z.real + z.imag*z.imag > 4.0:  # abs(z)**2 > 4.0と同じだが遅い
    return n
```

### 2. 数値オーバーフローの回避

```python
# 大きな値をチェック
if abs(z) > 1e10:  # 非常に大きな値
    return n
```

### 3. 複雑な計算の事前計算

```python
def __init__(self):
    super().__init__(name, description)
    # 事前計算された値をキャッシュ
    self._precomputed_values = self._precompute_values()

def _precompute_values(self):
    # 複雑な計算を事前に実行
    return {...}
```

## デバッグとテスト

### 基本的なテストパターン

```python
def test_plugin():
    plugin = MyPlugin()
    
    # メタデータのテスト
    assert plugin.metadata.name
    assert plugin.metadata.version
    
    # 生成器のテスト
    generator = plugin.create_generator()
    assert generator.name
    
    # 計算のテスト
    result = generator.calculate_point(complex(0, 0), 100)
    assert isinstance(result, int)
    assert 0 <= result <= 100
```

### デバッグ出力

```python
def calculate_point(self, c: complex, max_iterations: int, **kwargs) -> int:
    if kwargs.get('debug', False):
        print(f"計算開始: c={c}, max_iterations={max_iterations}")
    
    # 計算ロジック
    
    if kwargs.get('debug', False):
        print(f"計算完了: result={result}")
    
    return result
```

このAPIリファレンスを参考に、効率的で安定したプラグインを開発してください。