"""
フラクタルエディタのコアデータモデル

このモジュールは、フラクタル計算に必要な基本的なデータ構造を定義します。
複素数、フラクタルパラメータ、計算結果などの主要なデータクラスを含みます。
"""

import math
import numpy as np
from dataclasses import dataclass, field
from typing import Dict, Any, Tuple, Optional, List
import time
from datetime import datetime


@dataclass
class ComplexNumber:
    """複素数を表現するデータクラス"""
    real: float
    imaginary: float

    def __post_init__(self):
        """初期化後の検証"""
        self.validate()

    def validate(self) -> None:
        """複素数の妥当性を検証"""
        if not isinstance(self.real, (int, float)):
            raise ValueError(f"Real part must be a number, got {type(self.real)}")
        if not isinstance(self.imaginary, (int, float)):
            raise ValueError(f"Imaginary part must be a number, got {type(self.imaginary)}")

        # 無限大やNaNのチェック
        if not math.isfinite(self.real):
            raise ValueError(f"Real part must be finite, got {self.real}")
        if not math.isfinite(self.imaginary):
            raise ValueError(f"Imaginary part must be finite, got {self.imaginary}")

    @property
    def magnitude(self) -> float:
        """複素数の絶対値（大きさ）を計算"""
        return math.sqrt(self.real * self.real + self.imaginary * self.imaginary)

    @property
    def phase(self) -> float:
        """複素数の偏角を計算（ラジアン）"""
        return math.atan2(self.imaginary, self.real)

    def square(self) -> 'ComplexNumber':
        """複素数の二乗を計算"""
        return ComplexNumber(
            real=self.real * self.real - self.imaginary * self.imaginary,
            imaginary=2 * self.real * self.imaginary
        )

    def conjugate(self) -> 'ComplexNumber':
        """複素共役を返す"""
        return ComplexNumber(self.real, -self.imaginary)

    def to_complex(self) -> complex:
        """Python標準のcomplex型に変換"""
        return complex(self.real, self.imaginary)

    @classmethod
    def from_complex(cls, c: complex) -> 'ComplexNumber':
        """Python標準のcomplex型から作成"""
        return cls(c.real, c.imag)

    def __add__(self, other: 'ComplexNumber') -> 'ComplexNumber':
        """複素数の加算"""
        return ComplexNumber(self.real + other.real, self.imaginary + other.imaginary)

    def __sub__(self, other: 'ComplexNumber') -> 'ComplexNumber':
        """複素数の減算"""
        return ComplexNumber(self.real - other.real, self.imaginary - other.imaginary)

    def __mul__(self, other: 'ComplexNumber') -> 'ComplexNumber':
        """複素数の乗算"""
        return ComplexNumber(
            real=self.real * other.real - self.imaginary * other.imaginary,
            imaginary=self.real * other.imaginary + self.imaginary * other.real
        )

    def __str__(self) -> str:
        """文字列表現"""
        if self.imaginary >= 0:
            return f"{self.real} + {self.imaginary}i"
        else:
            return f"{self.real} - {abs(self.imaginary)}i"


@dataclass
class ComplexRegion:
    """複素平面上の矩形領域を表現するデータクラス"""
    top_left: ComplexNumber
    bottom_right: ComplexNumber

    def __post_init__(self):
        """初期化後の検証"""
        self.validate()

    def validate(self) -> None:
        """領域の妥当性を検証"""
        if not isinstance(self.top_left, ComplexNumber):
            raise ValueError("top_left must be a ComplexNumber")
        if not isinstance(self.bottom_right, ComplexNumber):
            raise ValueError("bottom_right must be a ComplexNumber")

        # 領域の整合性チェック
        if self.top_left.real >= self.bottom_right.real:
            raise ValueError("top_left.real must be less than bottom_right.real")
        if self.top_left.imaginary <= self.bottom_right.imaginary:
            raise ValueError("top_left.imaginary must be greater than bottom_right.imaginary")

        # 領域サイズの妥当性チェック
        if self.width <= 0:
            raise ValueError(f"Region width must be positive, got {self.width}")
        if self.height <= 0:
            raise ValueError(f"Region height must be positive, got {self.height}")

    @property
    def width(self) -> float:
        """領域の幅を計算"""
        return self.bottom_right.real - self.top_left.real

    @property
    def height(self) -> float:
        """領域の高さを計算"""
        return self.top_left.imaginary - self.bottom_right.imaginary

    @property
    def center(self) -> ComplexNumber:
        """領域の中心点を計算"""
        center_real = (self.top_left.real + self.bottom_right.real) / 2
        center_imag = (self.top_left.imaginary + self.bottom_right.imaginary) / 2
        return ComplexNumber(center_real, center_imag)

    @property
    def area(self) -> float:
        """領域の面積を計算"""
        return self.width * self.height

    def contains(self, point: ComplexNumber) -> bool:
        """指定された点が領域内にあるかチェック"""
        return (self.top_left.real <= point.real <= self.bottom_right.real and
                self.bottom_right.imaginary <= point.imaginary <= self.top_left.imaginary)

    def zoom(self, factor: float, center: Optional[ComplexNumber] = None) -> 'ComplexRegion':
        """指定された倍率で領域をズーム"""
        if factor <= 0:
            raise ValueError("Zoom factor must be positive")

        if center is None:
            center = self.center

        new_width = self.width / factor
        new_height = self.height / factor

        new_top_left = ComplexNumber(
            center.real - new_width / 2,
            center.imaginary + new_height / 2
        )
        new_bottom_right = ComplexNumber(
            center.real + new_width / 2,
            center.imaginary - new_height / 2
        )

        return ComplexRegion(new_top_left, new_bottom_right)


@dataclass
class FractalParameters:
    """フラクタル計算のパラメータを表現するデータクラス"""
    region: ComplexRegion
    max_iterations: int
    image_size: Tuple[int, int]  # (width, height)
    custom_parameters: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """初期化後の検証"""
        self.validate()

    def validate(self) -> None:
        """パラメータの妥当性を検証"""
        if not isinstance(self.region, ComplexRegion):
            raise ValueError("region must be a ComplexRegion")

        if not isinstance(self.max_iterations, int) or self.max_iterations <= 0:
            raise ValueError(f"max_iterations must be a positive integer, got {self.max_iterations}")

        if self.max_iterations > 10000:
            raise ValueError(f"max_iterations too large (max 10000), got {self.max_iterations}")

        if not isinstance(self.image_size, tuple) or len(self.image_size) != 2:
            raise ValueError("image_size must be a tuple of (width, height)")

        width, height = self.image_size
        if not isinstance(width, int) or not isinstance(height, int):
            raise ValueError("image_size dimensions must be integers")

        if width <= 0 or height <= 0:
            raise ValueError(f"image_size dimensions must be positive, got {self.image_size}")

        if width > 8192 or height > 8192:
            raise ValueError(f"image_size too large (max 8192x8192), got {self.image_size}")

        if not isinstance(self.custom_parameters, dict):
            raise ValueError("custom_parameters must be a dictionary")

    @property
    def aspect_ratio(self) -> float:
        """画像のアスペクト比を計算"""
        width, height = self.image_size
        return width / height

    @property
    def pixel_density(self) -> float:
        """ピクセル密度（ピクセル/単位面積）を計算"""
        width, height = self.image_size
        return (width * height) / self.region.area

    def get_custom_parameter(self, key: str, default: Any = None) -> Any:
        """カスタムパラメータを安全に取得"""
        return self.custom_parameters.get(key, default)

    def set_custom_parameter(self, key: str, value: Any) -> None:
        """カスタムパラメータを設定"""
        if not isinstance(key, str):
            raise ValueError("Parameter key must be a string")
        self.custom_parameters[key] = value


@dataclass
class FractalResult:
    """フラクタル計算結果を表現するデータクラス"""
    iteration_data: np.ndarray  # 2D array of iteration counts
    region: ComplexRegion
    calculation_time: float
    parameters: Optional[FractalParameters] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """初期化後の検証"""
        self.validate()

    def validate(self) -> None:
        """計算結果の妥当性を検証"""
        if not isinstance(self.iteration_data, np.ndarray):
            raise ValueError("iteration_data must be a numpy array")

        if self.iteration_data.ndim != 2:
            raise ValueError(f"iteration_data must be 2D array, got {self.iteration_data.ndim}D")

        if not isinstance(self.region, ComplexRegion):
            raise ValueError("region must be a ComplexRegion")

        if not isinstance(self.calculation_time, (int, float)) or self.calculation_time < 0:
            raise ValueError(f"calculation_time must be non-negative number, got {self.calculation_time}")

        if self.parameters is not None and not isinstance(self.parameters, FractalParameters):
            raise ValueError("parameters must be FractalParameters or None")

        if not isinstance(self.metadata, dict):
            raise ValueError("metadata must be a dictionary")

        # データの整合性チェック
        if self.parameters is not None:
            expected_shape = (self.parameters.image_size[1], self.parameters.image_size[0])
            if self.iteration_data.shape != expected_shape:
                raise ValueError(f"iteration_data shape {self.iteration_data.shape} doesn't match expected {expected_shape}")

    @property
    def image_size(self) -> Tuple[int, int]:
        """画像サイズを取得 (width, height)"""
        height, width = self.iteration_data.shape
        return (width, height)

    @property
    def max_iterations_reached(self) -> int:
        """最大反復回数に達したピクセル数"""
        if self.parameters is None:
            return 0
        return np.sum(self.iteration_data == self.parameters.max_iterations)

    @property
    def convergence_ratio(self) -> float:
        """収束率（最大反復回数に達しなかったピクセルの割合）"""
        if self.parameters is None:
            return 0.0
        total_pixels = self.iteration_data.size
        converged_pixels = total_pixels - self.max_iterations_reached
        return converged_pixels / total_pixels if total_pixels > 0 else 0.0

    def get_statistics(self) -> Dict[str, Any]:
        """計算結果の統計情報を取得"""
        return {
            'image_size': self.image_size,
            'calculation_time': self.calculation_time,
            'min_iterations': int(np.min(self.iteration_data)),
            'max_iterations': int(np.max(self.iteration_data)),
            'mean_iterations': float(np.mean(self.iteration_data)),
            'std_iterations': float(np.std(self.iteration_data)),
            'convergence_ratio': self.convergence_ratio,
            'total_pixels': self.iteration_data.size
        }


@dataclass
class ParameterDefinition:
    """パラメータ定義を表現するデータクラス"""
    name: str
    display_name: str
    parameter_type: str  # 'float', 'int', 'complex', 'bool', 'formula'
    default_value: Any
    min_value: Any = None
    max_value: Any = None
    description: str = ""

    def __post_init__(self):
        """初期化後の検証"""
        self.validate()

    def validate(self) -> None:
        """パラメータ定義の妥当性を検証"""
        if not isinstance(self.name, str) or not self.name.strip():
            raise ValueError("name must be a non-empty string")

        if not isinstance(self.display_name, str) or not self.display_name.strip():
            raise ValueError("display_name must be a non-empty string")

        valid_types = ['float', 'int', 'complex', 'bool', 'formula', 'string']
        if self.parameter_type not in valid_types:
            raise ValueError(f"parameter_type must be one of {valid_types}, got {self.parameter_type}")

        if not isinstance(self.description, str):
            raise ValueError("description must be a string")

        # 型固有の検証
        self._validate_type_specific()

    def _validate_type_specific(self) -> None:
        """型固有の検証"""
        if self.parameter_type == 'int':
            if not isinstance(self.default_value, int):
                raise ValueError(f"default_value must be int for type 'int', got {type(self.default_value)}")
            if self.min_value is not None and not isinstance(self.min_value, int):
                raise ValueError("min_value must be int or None for type 'int'")
            if self.max_value is not None and not isinstance(self.max_value, int):
                raise ValueError("max_value must be int or None for type 'int'")

        elif self.parameter_type == 'float':
            if not isinstance(self.default_value, (int, float)):
                raise ValueError(f"default_value must be number for type 'float', got {type(self.default_value)}")
            if self.min_value is not None and not isinstance(self.min_value, (int, float)):
                raise ValueError("min_value must be number or None for type 'float'")
            if self.max_value is not None and not isinstance(self.max_value, (int, float)):
                raise ValueError("max_value must be number or None for type 'float'")

        elif self.parameter_type == 'bool':
            if not isinstance(self.default_value, bool):
                raise ValueError(f"default_value must be bool for type 'bool', got {type(self.default_value)}")

        elif self.parameter_type == 'complex':
            if not isinstance(self.default_value, (ComplexNumber, complex)):
                raise ValueError(f"default_value must be ComplexNumber or complex for type 'complex'")

        elif self.parameter_type == 'string':
            if not isinstance(self.default_value, str):
                raise ValueError(f"default_value must be string for type 'string', got {type(self.default_value)}")

    def validate_value(self, value: Any) -> bool:
        """指定された値がこのパラメータ定義に適合するかチェック"""
        try:
            if self.parameter_type == 'int':
                if not isinstance(value, int):
                    return False
                if self.min_value is not None and value < self.min_value:
                    return False
                if self.max_value is not None and value > self.max_value:
                    return False

            elif self.parameter_type == 'float':
                if not isinstance(value, (int, float)):
                    return False
                if self.min_value is not None and value < self.min_value:
                    return False
                if self.max_value is not None and value > self.max_value:
                    return False

            elif self.parameter_type == 'bool':
                if not isinstance(value, bool):
                    return False

            elif self.parameter_type == 'complex':
                if not isinstance(value, (ComplexNumber, complex)):
                    return False

            elif self.parameter_type == 'string':
                if not isinstance(value, str):
                    return False

            elif self.parameter_type == 'formula':
                if not isinstance(value, str):
                    return False
                # 数式の構文チェックは別途実装

            return True
        except Exception:
            return False


from enum import Enum

class InterpolationMode(Enum):
    """色補間モード"""
    LINEAR = "linear"
    CUBIC = "cubic"
    HSV = "hsv"


@dataclass
class ColorStop:
    """カラーストップを表現するデータクラス"""
    position: float  # 0.0 - 1.0
    color: Tuple[int, int, int]  # RGB

    def __post_init__(self):
        """初期化後の検証"""
        self.validate()

    def validate(self) -> None:
        """カラーストップの妥当性を検証"""
        if not isinstance(self.position, (int, float)):
            raise ValueError("position must be a number")

        if not (0.0 <= self.position <= 1.0):
            raise ValueError(f"position must be between 0.0 and 1.0, got {self.position}")

        if not isinstance(self.color, tuple) or len(self.color) != 3:
            raise ValueError("color must be a tuple of (R, G, B)")

        for i, component in enumerate(self.color):
            if not isinstance(component, int):
                raise ValueError(f"color component {i} must be an integer")
            if not (0 <= component <= 255):
                raise ValueError(f"color component {i} must be between 0 and 255, got {component}")


@dataclass
class ColorPalette:
    """カラーパレットを表現するデータクラス"""
    name: str
    color_stops: List[ColorStop]
    interpolation_mode: InterpolationMode = InterpolationMode.LINEAR

    def __post_init__(self):
        """初期化後の検証"""
        self.validate()

    def validate(self) -> None:
        """カラーパレットの妥当性を検証"""
        if not isinstance(self.name, str) or not self.name.strip():
            raise ValueError("name must be a non-empty string")

        if not isinstance(self.color_stops, list) or len(self.color_stops) < 2:
            raise ValueError("color_stops must be a list with at least 2 ColorStop objects")

        for i, stop in enumerate(self.color_stops):
            if not isinstance(stop, ColorStop):
                raise ValueError(f"color_stops[{i}] must be a ColorStop object")

        if not isinstance(self.interpolation_mode, InterpolationMode):
            raise ValueError("interpolation_mode must be an InterpolationMode")

        # ポジションの順序チェック
        positions = [stop.position for stop in self.color_stops]
        if positions != sorted(positions):
            raise ValueError("color_stops must be sorted by position")

        # 最初と最後のポジションチェック
        if positions[0] != 0.0:
            raise ValueError("first color_stop position must be 0.0")
        if positions[-1] != 1.0:
            raise ValueError("last color_stop position must be 1.0")


@dataclass
class AppSettings:
    """アプリケーション設定を表現するデータクラス"""
    default_max_iterations: int = 1000
    default_image_size: Tuple[int, int] = (800, 600)
    default_color_palette: str = "Rainbow"
    enable_anti_aliasing: bool = True
    thread_count: int = field(default_factory=lambda: 4)
    auto_save_interval: int = 300  # seconds
    recent_projects_count: int = 10

    def __post_init__(self):
        """初期化後の検証"""
        self.validate()

    def validate(self) -> None:
        """設定の妥当性を検証"""
        if not isinstance(self.default_max_iterations, int) or self.default_max_iterations <= 0:
            raise ValueError("default_max_iterations must be a positive integer")

        if not isinstance(self.default_image_size, tuple) or len(self.default_image_size) != 2:
            raise ValueError("default_image_size must be a tuple of (width, height)")

        width, height = self.default_image_size
        if not isinstance(width, int) or not isinstance(height, int):
            raise ValueError("default_image_size dimensions must be integers")

        if width <= 0 or height <= 0:
            raise ValueError("default_image_size dimensions must be positive")

        if not isinstance(self.default_color_palette, str):
            raise ValueError("default_color_palette must be a string")

        if not isinstance(self.enable_anti_aliasing, bool):
            raise ValueError("enable_anti_aliasing must be a boolean")

        if not isinstance(self.thread_count, int) or self.thread_count <= 0:
            raise ValueError("thread_count must be a positive integer")

        if not isinstance(self.auto_save_interval, int) or self.auto_save_interval < 0:
            raise ValueError("auto_save_interval must be a non-negative integer")

        if not isinstance(self.recent_projects_count, int) or self.recent_projects_count < 0:
            raise ValueError("recent_projects_count must be a non-negative integer")


@dataclass
class FractalProject:
    """フラクタルプロジェクトを表現するデータクラス"""
    name: str
    fractal_type: str
    parameters: FractalParameters
    color_palette: ColorPalette
    last_modified: datetime = field(default_factory=datetime.now)
    file_path: str = ""

    def __post_init__(self):
        """初期化後の検証"""
        self.validate()

    def validate(self) -> None:
        """プロジェクトの妥当性を検証"""
        if not isinstance(self.name, str) or not self.name.strip():
            raise ValueError("name must be a non-empty string")

        if not isinstance(self.fractal_type, str) or not self.fractal_type.strip():
            raise ValueError("fractal_type must be a non-empty string")

        if not isinstance(self.parameters, FractalParameters):
            raise ValueError("parameters must be a FractalParameters object")

        if not isinstance(self.color_palette, ColorPalette):
            raise ValueError("color_palette must be a ColorPalette object")

        if not isinstance(self.last_modified, datetime):
            raise ValueError("last_modified must be a datetime object")

        if not isinstance(self.file_path, str):
            raise ValueError("file_path must be a string")

    def save_to_file(self, file_path: str) -> None:
        """
        プロジェクトをファイルに保存

        Args:
            file_path: 保存先ファイルパス

        Note:
            実際の保存処理はProjectManagerクラスで実装されています。
            このメソッドはProjectManagerを使用して保存を行います。
        """
        # 循環インポートを避けるため、関数内でインポート
        try:
            from ..services.project_manager import ProjectManager
        except ImportError:
            # 相対インポートが失敗した場合の代替手段
            import sys
            import os

            # 現在のファイルのディレクトリを取得
            current_dir = os.path.dirname(os.path.abspath(__file__))
            parent_dir = os.path.dirname(current_dir)
            services_dir = os.path.join(parent_dir, 'services')

            # services.project_managerモジュールを動的にインポート
            if services_dir not in sys.path:
                sys.path.insert(0, services_dir)

            try:
                from services.project_manager import ProjectManager
            finally:
                if services_dir in sys.path:
                    sys.path.remove(services_dir)

        manager = ProjectManager()
        manager.save_project(self, file_path)

    @classmethod
    def load_from_file(cls, file_path: str) -> 'FractalProject':
        """
        ファイルからプロジェクトを読み込み

        Args:
            file_path: 読み込むファイルパス

        Returns:
            読み込まれたプロジェクト

        Note:
            実際の読み込み処理はProjectManagerクラスで実装されています。
            このメソッドはProjectManagerを使用して読み込みを行います。
        """
        # 循環インポートを避けるため、関数内でインポート
        try:
            from ..services.project_manager import ProjectManager
        except ImportError:
            # 相対インポートが失敗した場合の代替手段
            import sys
            import os

            # 現在のファイルのディレクトリを取得
            current_dir = os.path.dirname(os.path.abspath(__file__))
            parent_dir = os.path.dirname(current_dir)
            services_dir = os.path.join(parent_dir, 'services')

            # services.project_managerモジュールを動的にインポート
            if services_dir not in sys.path:
                sys.path.insert(0, services_dir)

            try:
                from services.project_manager import ProjectManager
            finally:
                if services_dir in sys.path:
                    sys.path.remove(services_dir)

        manager = ProjectManager()
        return manager.load_project(file_path)
