"""
データモデルの単体テスト

フラクタルエディタのコアデータモデルの動作を検証します。
"""

import unittest
import numpy as np
import math
from fractal_editor.models.data_models import (
    ComplexNumber, ComplexRegion, FractalParameters, FractalResult
)


class TestComplexNumber(unittest.TestCase):
    """ComplexNumberクラスのテスト"""
    
    def test_creation_with_valid_values(self):
        """有効な値での複素数作成"""
        c = ComplexNumber(3.0, 4.0)
        self.assertEqual(c.real, 3.0)
        self.assertEqual(c.imaginary, 4.0)
    
    def test_magnitude_calculation(self):
        """絶対値の計算"""
        c = ComplexNumber(3.0, 4.0)
        self.assertAlmostEqual(c.magnitude, 5.0)
        
        c_zero = ComplexNumber(0.0, 0.0)
        self.assertEqual(c_zero.magnitude, 0.0)
    
    def test_phase_calculation(self):
        """偏角の計算"""
        c = ComplexNumber(1.0, 1.0)
        self.assertAlmostEqual(c.phase, math.pi / 4)
        
        c_real = ComplexNumber(1.0, 0.0)
        self.assertAlmostEqual(c_real.phase, 0.0)
    
    def test_square_operation(self):
        """二乗演算"""
        c = ComplexNumber(2.0, 3.0)
        squared = c.square()
        # (2 + 3i)^2 = 4 + 12i - 9 = -5 + 12i
        self.assertAlmostEqual(squared.real, -5.0)
        self.assertAlmostEqual(squared.imaginary, 12.0)
    
    def test_conjugate(self):
        """複素共役"""
        c = ComplexNumber(2.0, 3.0)
        conj = c.conjugate()
        self.assertEqual(conj.real, 2.0)
        self.assertEqual(conj.imaginary, -3.0)
    
    def test_arithmetic_operations(self):
        """算術演算"""
        c1 = ComplexNumber(1.0, 2.0)
        c2 = ComplexNumber(3.0, 4.0)
        
        # 加算
        add_result = c1 + c2
        self.assertEqual(add_result.real, 4.0)
        self.assertEqual(add_result.imaginary, 6.0)
        
        # 減算
        sub_result = c1 - c2
        self.assertEqual(sub_result.real, -2.0)
        self.assertEqual(sub_result.imaginary, -2.0)
        
        # 乗算
        mul_result = c1 * c2
        # (1 + 2i)(3 + 4i) = 3 + 4i + 6i - 8 = -5 + 10i
        self.assertEqual(mul_result.real, -5.0)
        self.assertEqual(mul_result.imaginary, 10.0)
    
    def test_conversion_to_complex(self):
        """Python標準complex型への変換"""
        c = ComplexNumber(2.0, 3.0)
        py_complex = c.to_complex()
        self.assertEqual(py_complex, complex(2.0, 3.0))
    
    def test_creation_from_complex(self):
        """Python標準complex型からの作成"""
        py_complex = complex(2.0, 3.0)
        c = ComplexNumber.from_complex(py_complex)
        self.assertEqual(c.real, 2.0)
        self.assertEqual(c.imaginary, 3.0)
    
    def test_validation_with_invalid_types(self):
        """無効な型での検証"""
        with self.assertRaises(ValueError):
            ComplexNumber("invalid", 2.0)
        
        with self.assertRaises(ValueError):
            ComplexNumber(2.0, "invalid")
    
    def test_validation_with_infinite_values(self):
        """無限大値での検証"""
        with self.assertRaises(ValueError):
            ComplexNumber(float('inf'), 2.0)
        
        with self.assertRaises(ValueError):
            ComplexNumber(2.0, float('nan'))


class TestComplexRegion(unittest.TestCase):
    """ComplexRegionクラスのテスト"""
    
    def test_creation_with_valid_region(self):
        """有効な領域での作成"""
        top_left = ComplexNumber(-2.0, 1.0)
        bottom_right = ComplexNumber(1.0, -1.0)
        region = ComplexRegion(top_left, bottom_right)
        
        self.assertEqual(region.top_left, top_left)
        self.assertEqual(region.bottom_right, bottom_right)
    
    def test_width_and_height_calculation(self):
        """幅と高さの計算"""
        top_left = ComplexNumber(-2.0, 1.0)
        bottom_right = ComplexNumber(1.0, -1.0)
        region = ComplexRegion(top_left, bottom_right)
        
        self.assertEqual(region.width, 3.0)  # 1.0 - (-2.0)
        self.assertEqual(region.height, 2.0)  # 1.0 - (-1.0)
    
    def test_center_calculation(self):
        """中心点の計算"""
        top_left = ComplexNumber(-2.0, 1.0)
        bottom_right = ComplexNumber(2.0, -1.0)
        region = ComplexRegion(top_left, bottom_right)
        
        center = region.center
        self.assertEqual(center.real, 0.0)
        self.assertEqual(center.imaginary, 0.0)
    
    def test_area_calculation(self):
        """面積の計算"""
        top_left = ComplexNumber(-1.0, 1.0)
        bottom_right = ComplexNumber(1.0, -1.0)
        region = ComplexRegion(top_left, bottom_right)
        
        self.assertEqual(region.area, 4.0)  # 2.0 * 2.0
    
    def test_contains_point(self):
        """点の包含判定"""
        top_left = ComplexNumber(-2.0, 1.0)
        bottom_right = ComplexNumber(2.0, -1.0)
        region = ComplexRegion(top_left, bottom_right)
        
        # 領域内の点
        self.assertTrue(region.contains(ComplexNumber(0.0, 0.0)))
        self.assertTrue(region.contains(ComplexNumber(-1.0, 0.5)))
        
        # 領域外の点
        self.assertFalse(region.contains(ComplexNumber(-3.0, 0.0)))
        self.assertFalse(region.contains(ComplexNumber(0.0, 2.0)))
    
    def test_zoom_operation(self):
        """ズーム操作"""
        top_left = ComplexNumber(-2.0, 2.0)
        bottom_right = ComplexNumber(2.0, -2.0)
        region = ComplexRegion(top_left, bottom_right)
        
        # 2倍ズーム（領域が半分になる）
        zoomed = region.zoom(2.0)
        self.assertAlmostEqual(zoomed.width, 2.0)
        self.assertAlmostEqual(zoomed.height, 2.0)
        
        # 中心は変わらない
        self.assertAlmostEqual(zoomed.center.real, 0.0)
        self.assertAlmostEqual(zoomed.center.imaginary, 0.0)
    
    def test_validation_with_invalid_region(self):
        """無効な領域での検証"""
        # 左右が逆
        with self.assertRaises(ValueError):
            ComplexRegion(
                ComplexNumber(1.0, 1.0),
                ComplexNumber(-1.0, -1.0)
            )
        
        # 上下が逆
        with self.assertRaises(ValueError):
            ComplexRegion(
                ComplexNumber(-1.0, -1.0),
                ComplexNumber(1.0, 1.0)
            )


class TestFractalParameters(unittest.TestCase):
    """FractalParametersクラスのテスト"""
    
    def setUp(self):
        """テスト用の基本設定"""
        self.region = ComplexRegion(
            ComplexNumber(-2.0, 1.0),
            ComplexNumber(1.0, -1.0)
        )
    
    def test_creation_with_valid_parameters(self):
        """有効なパラメータでの作成"""
        params = FractalParameters(
            region=self.region,
            max_iterations=100,
            image_size=(800, 600)
        )
        
        self.assertEqual(params.region, self.region)
        self.assertEqual(params.max_iterations, 100)
        self.assertEqual(params.image_size, (800, 600))
        self.assertEqual(params.custom_parameters, {})
    
    def test_aspect_ratio_calculation(self):
        """アスペクト比の計算"""
        params = FractalParameters(
            region=self.region,
            max_iterations=100,
            image_size=(800, 600)
        )
        
        self.assertAlmostEqual(params.aspect_ratio, 800/600)
    
    def test_pixel_density_calculation(self):
        """ピクセル密度の計算"""
        params = FractalParameters(
            region=self.region,
            max_iterations=100,
            image_size=(100, 100)
        )
        
        expected_density = (100 * 100) / self.region.area
        self.assertAlmostEqual(params.pixel_density, expected_density)
    
    def test_custom_parameters_management(self):
        """カスタムパラメータの管理"""
        params = FractalParameters(
            region=self.region,
            max_iterations=100,
            image_size=(800, 600)
        )
        
        # パラメータ設定
        params.set_custom_parameter("julia_c", ComplexNumber(0.3, 0.5))
        self.assertIsInstance(params.get_custom_parameter("julia_c"), ComplexNumber)
        
        # デフォルト値の取得
        self.assertEqual(params.get_custom_parameter("nonexistent", "default"), "default")
    
    def test_validation_with_invalid_parameters(self):
        """無効なパラメータでの検証"""
        # 無効な反復回数
        with self.assertRaises(ValueError):
            FractalParameters(
                region=self.region,
                max_iterations=0,
                image_size=(800, 600)
            )
        
        # 反復回数が大きすぎる
        with self.assertRaises(ValueError):
            FractalParameters(
                region=self.region,
                max_iterations=20000,
                image_size=(800, 600)
            )
        
        # 無効な画像サイズ
        with self.assertRaises(ValueError):
            FractalParameters(
                region=self.region,
                max_iterations=100,
                image_size=(0, 600)
            )
        
        # 画像サイズが大きすぎる
        with self.assertRaises(ValueError):
            FractalParameters(
                region=self.region,
                max_iterations=100,
                image_size=(10000, 10000)
            )


class TestFractalResult(unittest.TestCase):
    """FractalResultクラスのテスト"""
    
    def setUp(self):
        """テスト用の基本設定"""
        self.region = ComplexRegion(
            ComplexNumber(-2.0, 1.0),
            ComplexNumber(1.0, -1.0)
        )
        self.parameters = FractalParameters(
            region=self.region,
            max_iterations=100,
            image_size=(10, 8)
        )
        self.iteration_data = np.random.randint(0, 101, size=(8, 10))
    
    def test_creation_with_valid_data(self):
        """有効なデータでの作成"""
        result = FractalResult(
            iteration_data=self.iteration_data,
            region=self.region,
            calculation_time=1.5,
            parameters=self.parameters
        )
        
        self.assertTrue(np.array_equal(result.iteration_data, self.iteration_data))
        self.assertEqual(result.region, self.region)
        self.assertEqual(result.calculation_time, 1.5)
        self.assertEqual(result.parameters, self.parameters)
    
    def test_image_size_property(self):
        """画像サイズプロパティ"""
        result = FractalResult(
            iteration_data=self.iteration_data,
            region=self.region,
            calculation_time=1.0
        )
        
        self.assertEqual(result.image_size, (10, 8))  # (width, height)
    
    def test_convergence_statistics(self):
        """収束統計の計算"""
        # 特定のデータでテスト
        test_data = np.array([
            [50, 100, 75],
            [100, 100, 25],
            [30, 60, 100]
        ])
        
        params = FractalParameters(
            region=self.region,
            max_iterations=100,
            image_size=(3, 3)
        )
        
        result = FractalResult(
            iteration_data=test_data,
            region=self.region,
            calculation_time=1.0,
            parameters=params
        )
        
        # 最大反復回数に達したピクセル数（値が100のもの）
        self.assertEqual(result.max_iterations_reached, 4)
        
        # 収束率（最大反復回数に達しなかったピクセルの割合）
        expected_convergence = 5 / 9  # 9ピクセル中5つが収束
        self.assertAlmostEqual(result.convergence_ratio, expected_convergence)
    
    def test_statistics_calculation(self):
        """統計情報の計算"""
        result = FractalResult(
            iteration_data=self.iteration_data,
            region=self.region,
            calculation_time=2.5,
            parameters=self.parameters
        )
        
        stats = result.get_statistics()
        
        self.assertEqual(stats['image_size'], (10, 8))
        self.assertEqual(stats['calculation_time'], 2.5)
        self.assertEqual(stats['total_pixels'], 80)
        self.assertIn('min_iterations', stats)
        self.assertIn('max_iterations', stats)
        self.assertIn('mean_iterations', stats)
        self.assertIn('std_iterations', stats)
        self.assertIn('convergence_ratio', stats)
    
    def test_validation_with_invalid_data(self):
        """無効なデータでの検証"""
        # 無効な配列次元
        with self.assertRaises(ValueError):
            FractalResult(
                iteration_data=np.array([1, 2, 3]),  # 1D array
                region=self.region,
                calculation_time=1.0
            )
        
        # 負の計算時間
        with self.assertRaises(ValueError):
            FractalResult(
                iteration_data=self.iteration_data,
                region=self.region,
                calculation_time=-1.0
            )
        
        # パラメータとデータサイズの不整合
        wrong_params = FractalParameters(
            region=self.region,
            max_iterations=100,
            image_size=(5, 5)  # データは(10, 8)
        )
        
        with self.assertRaises(ValueError):
            FractalResult(
                iteration_data=self.iteration_data,
                region=self.region,
                calculation_time=1.0,
                parameters=wrong_params
            )


if __name__ == '__main__':
    unittest.main()