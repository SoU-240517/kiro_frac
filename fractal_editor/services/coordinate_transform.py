"""
複素平面座標変換ユーティリティ

このモジュールは、スクリーン座標と複素平面座標間の正確な変換機能を提供します。
ズーム機能で使用される座標変換の核となる機能を実装しています。
"""

import math
from typing import Tuple
from PyQt6.QtCore import QPoint, QSize
from ..models.data_models import ComplexNumber, ComplexRegion


class CoordinateTransformError(Exception):
    """座標変換エラーの基底クラス"""
    pass


class InvalidCoordinateError(CoordinateTransformError):
    """無効な座標エラー"""
    pass


class InvalidRegionError(CoordinateTransformError):
    """無効な領域エラー"""
    pass


class ComplexCoordinateTransform:
    """
    複素平面とスクリーン座標間の変換を行うユーティリティクラス
    
    このクラスは静的メソッドのみを提供し、座標変換に関する
    数学的計算を正確に実行します。数値精度とオーバーフロー対策を含みます。
    """
    
    # 数値精度の制限値
    MIN_REGION_SIZE = 1e-15  # 最小領域サイズ（数値精度限界）
    MAX_REGION_SIZE = 1e15   # 最大領域サイズ（オーバーフロー防止）
    MAX_ZOOM_FACTOR = 1e10   # 最大ズーム倍率
    MIN_ZOOM_FACTOR = 1e-10  # 最小ズーム倍率
    
    @staticmethod
    def screen_to_complex(screen_point: QPoint, widget_size: QSize, complex_region: ComplexRegion) -> ComplexNumber:
        """
        スクリーン座標を複素平面座標に変換
        
        Args:
            screen_point: スクリーン座標のポイント
            widget_size: ウィジェットのサイズ
            complex_region: 複素平面の表示領域
            
        Returns:
            変換された複素数座標
            
        Raises:
            InvalidCoordinateError: 無効な座標が指定された場合
            InvalidRegionError: 無効な領域が指定された場合
        """
        # 入力検証
        ComplexCoordinateTransform._validate_inputs(screen_point, widget_size, complex_region)
        
        try:
            # スクリーン座標を正規化（0.0-1.0の範囲）
            normalized_x = screen_point.x() / widget_size.width()
            normalized_y = screen_point.y() / widget_size.height()
            
            # 境界チェック（スクリーン外の座標も許可するが、警告的な処理）
            # 実際の変換では境界外も計算可能
            
            # 複素平面座標に変換
            # X軸: 左端がtop_left.real、右端がbottom_right.real
            # Y軸: 上端がtop_left.imaginary、下端がbottom_right.imaginary
            real_part = (complex_region.top_left.real + 
                        normalized_x * complex_region.width)
            
            imaginary_part = (complex_region.top_left.imaginary - 
                             normalized_y * complex_region.height)
            
            # 数値精度チェック
            ComplexCoordinateTransform._check_numerical_precision(real_part, imaginary_part)
            
            return ComplexNumber(real_part, imaginary_part)
            
        except (OverflowError, ValueError) as e:
            raise InvalidCoordinateError(f"座標変換中に数値エラーが発生しました: {e}")
    
    @staticmethod
    def complex_to_screen(complex_point: ComplexNumber, widget_size: QSize, complex_region: ComplexRegion) -> QPoint:
        """
        複素平面座標をスクリーン座標に変換
        
        Args:
            complex_point: 複素平面上の点
            widget_size: ウィジェットのサイズ
            complex_region: 複素平面の表示領域
            
        Returns:
            変換されたスクリーン座標
            
        Raises:
            InvalidCoordinateError: 無効な座標が指定された場合
            InvalidRegionError: 無効な領域が指定された場合
        """
        # 入力検証
        ComplexCoordinateTransform._validate_complex_inputs(complex_point, widget_size, complex_region)
        
        try:
            # 複素平面座標を正規化（0.0-1.0の範囲）
            normalized_x = ((complex_point.real - complex_region.top_left.real) / 
                           complex_region.width)
            
            normalized_y = ((complex_region.top_left.imaginary - complex_point.imaginary) / 
                           complex_region.height)
            
            # スクリーン座標に変換
            screen_x = int(round(normalized_x * widget_size.width()))
            screen_y = int(round(normalized_y * widget_size.height()))
            
            return QPoint(screen_x, screen_y)
            
        except (OverflowError, ValueError) as e:
            raise InvalidCoordinateError(f"座標変換中に数値エラーが発生しました: {e}")
    
    @staticmethod
    def calculate_zoom_region(current_region: ComplexRegion, zoom_center: ComplexNumber, 
                             zoom_factor: float) -> ComplexRegion:
        """
        ズーム操作による新しい複素平面領域を計算
        
        Args:
            current_region: 現在の複素平面領域
            zoom_center: ズームの中心点
            zoom_factor: ズーム倍率（1.0より大きい値でズームイン）
            
        Returns:
            新しい複素平面領域
            
        Raises:
            InvalidRegionError: 無効な領域が指定された場合
            InvalidCoordinateError: 無効なズーム設定の場合
        """
        # 入力検証
        ComplexCoordinateTransform._validate_zoom_inputs(current_region, zoom_center, zoom_factor)
        
        try:
            # 新しい領域のサイズを計算
            new_width = current_region.width / zoom_factor
            new_height = current_region.height / zoom_factor
            
            # 領域サイズの制限チェック
            ComplexCoordinateTransform._check_region_size_limits(new_width, new_height)
            
            # 新しい領域の境界を計算
            half_width = new_width / 2.0
            half_height = new_height / 2.0
            
            new_top_left = ComplexNumber(
                zoom_center.real - half_width,
                zoom_center.imaginary + half_height
            )
            
            new_bottom_right = ComplexNumber(
                zoom_center.real + half_width,
                zoom_center.imaginary - half_height
            )
            
            return ComplexRegion(new_top_left, new_bottom_right)
            
        except (OverflowError, ValueError) as e:
            raise InvalidRegionError(f"ズーム領域計算中に数値エラーが発生しました: {e}")
    
    @staticmethod
    def calculate_pan_region(current_region: ComplexRegion, screen_delta: QPoint, 
                            widget_size: QSize) -> ComplexRegion:
        """
        パン操作による新しい複素平面領域を計算
        
        Args:
            current_region: 現在の複素平面領域
            screen_delta: スクリーン座標での移動量
            widget_size: ウィジェットのサイズ
            
        Returns:
            新しい複素平面領域
            
        Raises:
            InvalidRegionError: 無効な領域が指定された場合
        """
        try:
            # スクリーン座標の移動量を複素平面座標の移動量に変換
            complex_delta_real = (screen_delta.x() / widget_size.width()) * current_region.width
            complex_delta_imag = -(screen_delta.y() / widget_size.height()) * current_region.height
            
            # 新しい領域の境界を計算
            new_top_left = ComplexNumber(
                current_region.top_left.real - complex_delta_real,
                current_region.top_left.imaginary - complex_delta_imag
            )
            
            new_bottom_right = ComplexNumber(
                current_region.bottom_right.real - complex_delta_real,
                current_region.bottom_right.imaginary - complex_delta_imag
            )
            
            return ComplexRegion(new_top_left, new_bottom_right)
            
        except (OverflowError, ValueError) as e:
            raise InvalidRegionError(f"パン領域計算中に数値エラーが発生しました: {e}")
    
    @staticmethod
    def _validate_inputs(screen_point: QPoint, widget_size: QSize, complex_region: ComplexRegion) -> None:
        """スクリーン座標変換の入力検証"""
        if not isinstance(screen_point, QPoint):
            raise InvalidCoordinateError("screen_pointはQPointである必要があります")
        
        if not isinstance(widget_size, QSize):
            raise InvalidCoordinateError("widget_sizeはQSizeである必要があります")
        
        if widget_size.width() <= 0 or widget_size.height() <= 0:
            raise InvalidCoordinateError("ウィジェットサイズは正の値である必要があります")
        
        if not isinstance(complex_region, ComplexRegion):
            raise InvalidRegionError("complex_regionはComplexRegionである必要があります")
    
    @staticmethod
    def _validate_complex_inputs(complex_point: ComplexNumber, widget_size: QSize, 
                                complex_region: ComplexRegion) -> None:
        """複素座標変換の入力検証"""
        if not isinstance(complex_point, ComplexNumber):
            raise InvalidCoordinateError("complex_pointはComplexNumberである必要があります")
        
        if not isinstance(widget_size, QSize):
            raise InvalidCoordinateError("widget_sizeはQSizeである必要があります")
        
        if widget_size.width() <= 0 or widget_size.height() <= 0:
            raise InvalidCoordinateError("ウィジェットサイズは正の値である必要があります")
        
        if not isinstance(complex_region, ComplexRegion):
            raise InvalidRegionError("complex_regionはComplexRegionである必要があります")
    
    @staticmethod
    def _validate_zoom_inputs(current_region: ComplexRegion, zoom_center: ComplexNumber, 
                             zoom_factor: float) -> None:
        """ズーム計算の入力検証"""
        if not isinstance(current_region, ComplexRegion):
            raise InvalidRegionError("current_regionはComplexRegionである必要があります")
        
        if not isinstance(zoom_center, ComplexNumber):
            raise InvalidCoordinateError("zoom_centerはComplexNumberである必要があります")
        
        if not isinstance(zoom_factor, (int, float)):
            raise InvalidCoordinateError("zoom_factorは数値である必要があります")
        
        if zoom_factor <= 0:
            raise InvalidCoordinateError("ズーム倍率は正の値である必要があります")
        
        if zoom_factor > ComplexCoordinateTransform.MAX_ZOOM_FACTOR:
            raise InvalidCoordinateError(f"ズーム倍率が大きすぎます（最大: {ComplexCoordinateTransform.MAX_ZOOM_FACTOR}）")
        
        if zoom_factor < ComplexCoordinateTransform.MIN_ZOOM_FACTOR:
            raise InvalidCoordinateError(f"ズーム倍率が小さすぎます（最小: {ComplexCoordinateTransform.MIN_ZOOM_FACTOR}）")
    
    @staticmethod
    def _check_numerical_precision(real_part: float, imaginary_part: float) -> None:
        """数値精度のチェック"""
        if not math.isfinite(real_part) or not math.isfinite(imaginary_part):
            raise InvalidCoordinateError("座標値が無限大またはNaNです")
        
        # 極端に大きな値のチェック
        if abs(real_part) > ComplexCoordinateTransform.MAX_REGION_SIZE:
            raise InvalidCoordinateError("実部の値が大きすぎます")
        
        if abs(imaginary_part) > ComplexCoordinateTransform.MAX_REGION_SIZE:
            raise InvalidCoordinateError("虚部の値が大きすぎます")
    
    @staticmethod
    def _check_region_size_limits(width: float, height: float) -> None:
        """領域サイズの制限チェック"""
        if width < ComplexCoordinateTransform.MIN_REGION_SIZE:
            raise InvalidRegionError("領域の幅が小さすぎます（数値精度の限界）")
        
        if height < ComplexCoordinateTransform.MIN_REGION_SIZE:
            raise InvalidRegionError("領域の高さが小さすぎます（数値精度の限界）")
        
        if width > ComplexCoordinateTransform.MAX_REGION_SIZE:
            raise InvalidRegionError("領域の幅が大きすぎます")
        
        if height > ComplexCoordinateTransform.MAX_REGION_SIZE:
            raise InvalidRegionError("領域の高さが大きすぎます")