"""
複素平面座標変換ユーティリティの単体テスト

このテストファイルは、ComplexCoordinateTransformクラスの
すべての機能について包括的なテストを実行します。
"""

import pytest
import math
from PyQt6.QtCore import QPoint, QSize

from fractal_editor.models.data_models import ComplexNumber, ComplexRegion
from fractal_editor.services.coordinate_transform import (
    ComplexCoordinateTransform,
    CoordinateTransformError,
    InvalidCoordinateError,
    InvalidRegionError
)


class TestComplexCoordinateTransform:
    """ComplexCoordinateTransformクラスのテスト"""
    
    def setup_method(self):
        """各テストメソッドの前に実行される初期化"""
        # 標準的なテスト用データを準備
        self.widget_size = QSize(800, 600)
        self.complex_region = ComplexRegion(
            ComplexNumber(-2.0, 1.5),  # top_left
            ComplexNumber(2.0, -1.5)   # bottom_right
        )
        
    def test_screen_to_complex_center_point(self):
        """スクリーン中央点の複素平面座標変換テスト"""
        # スクリーン中央点
        center_point = QPoint(400, 300)
        
        result = ComplexCoordinateTransform.screen_to_complex(
            center_point, self.widget_size, self.complex_region
        )
        
        # 複素平面の中央は(0, 0)になるはず
        assert abs(result.real - 0.0) < 1e-10
        assert abs(result.imaginary - 0.0) < 1e-10
    
    def test_screen_to_complex_corner_points(self):
        """スクリーン四隅の複素平面座標変換テスト"""
        # 左上角 (0, 0)
        top_left_screen = QPoint(0, 0)
        result = ComplexCoordinateTransform.screen_to_complex(
            top_left_screen, self.widget_size, self.complex_region
        )
        assert abs(result.real - (-2.0)) < 1e-10
        assert abs(result.imaginary - 1.5) < 1e-10
        
        # 右下角 (800, 600)
        bottom_right_screen = QPoint(800, 600)
        result = ComplexCoordinateTransform.screen_to_complex(
            bottom_right_screen, self.widget_size, self.complex_region
        )
        assert abs(result.real - 2.0) < 1e-10
        assert abs(result.imaginary - (-1.5)) < 1e-10
    
    def test_complex_to_screen_center_point(self):
        """複素平面中央点のスクリーン座標変換テスト"""
        center_complex = ComplexNumber(0.0, 0.0)
        
        result = ComplexCoordinateTransform.complex_to_screen(
            center_complex, self.widget_size, self.complex_region
        )
        
        # スクリーンの中央は(400, 300)になるはず
        assert result.x() == 400
        assert result.y() == 300
    
    def test_complex_to_screen_corner_points(self):
        """複素平面四隅のスクリーン座標変換テスト"""
        # 左上角
        top_left_complex = ComplexNumber(-2.0, 1.5)
        result = ComplexCoordinateTransform.complex_to_screen(
            top_left_complex, self.widget_size, self.complex_region
        )
        assert result.x() == 0
        assert result.y() == 0
        
        # 右下角
        bottom_right_complex = ComplexNumber(2.0, -1.5)
        result = ComplexCoordinateTransform.complex_to_screen(
            bottom_right_complex, self.widget_size, self.complex_region
        )
        assert result.x() == 800
        assert result.y() == 600
    
    def test_coordinate_conversion_roundtrip(self):
        """座標変換の往復テスト（精度確認）"""
        # 複数のテストポイントで往復変換をテスト
        test_points = [
            QPoint(100, 150),
            QPoint(400, 300),
            QPoint(700, 450),
            QPoint(0, 0),
            QPoint(800, 600)
        ]
        
        for original_point in test_points:
            # スクリーン → 複素平面 → スクリーン
            complex_point = ComplexCoordinateTransform.screen_to_complex(
                original_point, self.widget_size, self.complex_region
            )
            converted_point = ComplexCoordinateTransform.complex_to_screen(
                complex_point, self.widget_size, self.complex_region
            )
            
            # 元の座標と変換後の座標が一致することを確認
            assert abs(converted_point.x() - original_point.x()) <= 1
            assert abs(converted_point.y() - original_point.y()) <= 1
    
    def test_calculate_zoom_region_zoom_in(self):
        """ズームイン時の領域計算テスト"""
        zoom_center = ComplexNumber(0.0, 0.0)
        zoom_factor = 2.0  # 2倍ズームイン
        
        result = ComplexCoordinateTransform.calculate_zoom_region(
            self.complex_region, zoom_center, zoom_factor
        )
        
        # 領域サイズが半分になることを確認
        expected_width = self.complex_region.width / 2.0
        expected_height = self.complex_region.height / 2.0
        
        assert abs(result.width - expected_width) < 1e-10
        assert abs(result.height - expected_height) < 1e-10
        
        # 中心が保持されることを確認
        assert abs(result.center.real - zoom_center.real) < 1e-10
        assert abs(result.center.imaginary - zoom_center.imaginary) < 1e-10
    
    def test_calculate_zoom_region_zoom_out(self):
        """ズームアウト時の領域計算テスト"""
        zoom_center = ComplexNumber(0.0, 0.0)
        zoom_factor = 0.5  # 2倍ズームアウト
        
        result = ComplexCoordinateTransform.calculate_zoom_region(
            self.complex_region, zoom_center, zoom_factor
        )
        
        # 領域サイズが2倍になることを確認
        expected_width = self.complex_region.width / 0.5
        expected_height = self.complex_region.height / 0.5
        
        assert abs(result.width - expected_width) < 1e-10
        assert abs(result.height - expected_height) < 1e-10
    
    def test_calculate_zoom_region_off_center(self):
        """中心以外でのズーム領域計算テスト"""
        zoom_center = ComplexNumber(1.0, 0.5)
        zoom_factor = 4.0
        
        result = ComplexCoordinateTransform.calculate_zoom_region(
            self.complex_region, zoom_center, zoom_factor
        )
        
        # 指定した中心が新しい領域の中心になることを確認
        assert abs(result.center.real - zoom_center.real) < 1e-10
        assert abs(result.center.imaginary - zoom_center.imaginary) < 1e-10
    
    def test_calculate_pan_region(self):
        """パン操作の領域計算テスト"""
        # 右に100ピクセル、下に50ピクセル移動
        screen_delta = QPoint(100, 50)
        
        result = ComplexCoordinateTransform.calculate_pan_region(
            self.complex_region, screen_delta, self.widget_size
        )
        
        # 複素平面での移動量を計算
        expected_real_delta = (100 / 800) * self.complex_region.width
        expected_imag_delta = -(50 / 600) * self.complex_region.height
        
        # 新しい領域の境界を確認
        expected_top_left_real = self.complex_region.top_left.real - expected_real_delta
        expected_top_left_imag = self.complex_region.top_left.imaginary - expected_imag_delta
        
        assert abs(result.top_left.real - expected_top_left_real) < 1e-10
        assert abs(result.top_left.imaginary - expected_top_left_imag) < 1e-10
    
    def test_invalid_screen_point_type(self):
        """無効なスクリーン座標タイプのエラーテスト"""
        with pytest.raises(InvalidCoordinateError):
            ComplexCoordinateTransform.screen_to_complex(
                "invalid", self.widget_size, self.complex_region
            )
    
    def test_invalid_widget_size(self):
        """無効なウィジェットサイズのエラーテスト"""
        with pytest.raises(InvalidCoordinateError):
            ComplexCoordinateTransform.screen_to_complex(
                QPoint(100, 100), QSize(0, 600), self.complex_region
            )
        
        with pytest.raises(InvalidCoordinateError):
            ComplexCoordinateTransform.screen_to_complex(
                QPoint(100, 100), QSize(800, -600), self.complex_region
            )
    
    def test_invalid_complex_region_type(self):
        """無効な複素領域タイプのエラーテスト"""
        with pytest.raises(InvalidRegionError):
            ComplexCoordinateTransform.screen_to_complex(
                QPoint(100, 100), self.widget_size, "invalid"
            )
    
    def test_invalid_zoom_factor(self):
        """無効なズーム倍率のエラーテスト"""
        zoom_center = ComplexNumber(0.0, 0.0)
        
        # ゼロのズーム倍率
        with pytest.raises(InvalidCoordinateError):
            ComplexCoordinateTransform.calculate_zoom_region(
                self.complex_region, zoom_center, 0.0
            )
        
        # 負のズーム倍率
        with pytest.raises(InvalidCoordinateError):
            ComplexCoordinateTransform.calculate_zoom_region(
                self.complex_region, zoom_center, -1.0
            )
        
        # 極端に大きなズーム倍率
        with pytest.raises(InvalidCoordinateError):
            ComplexCoordinateTransform.calculate_zoom_region(
                self.complex_region, zoom_center, 1e15
            )
    
    def test_extreme_zoom_region_size_limits(self):
        """極端なズーム時の領域サイズ制限テスト"""
        zoom_center = ComplexNumber(0.0, 0.0)
        
        # 極端に大きなズーム倍率（入力検証でエラーになる）
        with pytest.raises(InvalidCoordinateError):
            ComplexCoordinateTransform.calculate_zoom_region(
                self.complex_region, zoom_center, 1e12
            )
        
        # MAX_ZOOM_FACTOR以下での正常動作確認
        max_allowed_zoom = ComplexCoordinateTransform.MAX_ZOOM_FACTOR
        result = ComplexCoordinateTransform.calculate_zoom_region(
            self.complex_region, zoom_center, max_allowed_zoom
        )
        
        # 結果が有効な領域であることを確認
        assert result.width > 0
        assert result.height > 0
        assert math.isfinite(result.width)
        assert math.isfinite(result.height)
    
    def test_numerical_precision_limits(self):
        """数値精度限界のテスト"""
        # 極端に大きな座標値
        large_region = ComplexRegion(
            ComplexNumber(-1e14, 1e14),
            ComplexNumber(1e14, -1e14)
        )
        
        # 正常な変換ができることを確認
        center_point = QPoint(400, 300)
        result = ComplexCoordinateTransform.screen_to_complex(
            center_point, self.widget_size, large_region
        )
        
        assert math.isfinite(result.real)
        assert math.isfinite(result.imaginary)
    
    def test_aspect_ratio_preservation(self):
        """アスペクト比保持のテスト"""
        # 正方形でないウィジェットサイズ
        non_square_size = QSize(1200, 600)  # 2:1のアスペクト比
        
        # 正方形の複素領域
        square_region = ComplexRegion(
            ComplexNumber(-1.0, 1.0),
            ComplexNumber(1.0, -1.0)
        )
        
        # 中央点の変換
        center_screen = QPoint(600, 300)
        result = ComplexCoordinateTransform.screen_to_complex(
            center_screen, non_square_size, square_region
        )
        
        # 中央が(0, 0)になることを確認
        assert abs(result.real - 0.0) < 1e-10
        assert abs(result.imaginary - 0.0) < 1e-10
    
    def test_edge_case_single_pixel_region(self):
        """1ピクセル領域のエッジケーステスト"""
        single_pixel_size = QSize(1, 1)
        
        # 単一ピクセルでの変換
        result = ComplexCoordinateTransform.screen_to_complex(
            QPoint(0, 0), single_pixel_size, self.complex_region
        )
        
        # 左上角の座標になることを確認
        assert abs(result.real - self.complex_region.top_left.real) < 1e-10
        assert abs(result.imaginary - self.complex_region.top_left.imaginary) < 1e-10
    
    def test_floating_point_screen_coordinates(self):
        """浮動小数点スクリーン座標の処理テスト"""
        # QPointは整数座標のみなので、境界値での動作を確認
        boundary_points = [
            QPoint(799, 599),  # 右下境界近く
            QPoint(1, 1),      # 左上境界近く
        ]
        
        for point in boundary_points:
            result = ComplexCoordinateTransform.screen_to_complex(
                point, self.widget_size, self.complex_region
            )
            
            # 有効な複素数が返されることを確認
            assert math.isfinite(result.real)
            assert math.isfinite(result.imaginary)
            
            # 往復変換で精度を確認
            converted_back = ComplexCoordinateTransform.complex_to_screen(
                result, self.widget_size, self.complex_region
            )
            assert abs(converted_back.x() - point.x()) <= 1
            assert abs(converted_back.y() - point.y()) <= 1


if __name__ == "__main__":
    # テストの実行
    pytest.main([__file__, "-v"])