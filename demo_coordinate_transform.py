"""
複素平面座標変換ユーティリティのデモンストレーション

このスクリプトは、ComplexCoordinateTransformクラスの
主要機能を実際に使用して動作を確認します。
"""

from PyQt6.QtCore import QPoint, QSize
from fractal_editor.models.data_models import ComplexNumber, ComplexRegion
from fractal_editor.services.coordinate_transform import ComplexCoordinateTransform


def main():
    print("=== 複素平面座標変換ユーティリティ デモ ===\n")
    
    # テスト用のデータを準備
    widget_size = QSize(800, 600)
    complex_region = ComplexRegion(
        ComplexNumber(-2.0, 1.5),  # 左上
        ComplexNumber(2.0, -1.5)   # 右下
    )
    
    print(f"ウィジェットサイズ: {widget_size.width()} x {widget_size.height()}")
    print(f"複素平面領域: {complex_region.top_left} から {complex_region.bottom_right}")
    print(f"領域サイズ: 幅={complex_region.width:.2f}, 高さ={complex_region.height:.2f}\n")
    
    # 1. スクリーン座標から複素平面座標への変換
    print("1. スクリーン座標 → 複素平面座標")
    test_points = [
        QPoint(0, 0),      # 左上
        QPoint(400, 300),  # 中央
        QPoint(800, 600),  # 右下
        QPoint(200, 150),  # 任意の点
    ]
    
    for screen_point in test_points:
        complex_point = ComplexCoordinateTransform.screen_to_complex(
            screen_point, widget_size, complex_region
        )
        print(f"  スクリーン({screen_point.x()}, {screen_point.y()}) → 複素平面({complex_point.real:.3f}, {complex_point.imaginary:.3f})")
    
    print()
    
    # 2. 複素平面座標からスクリーン座標への変換
    print("2. 複素平面座標 → スクリーン座標")
    test_complex_points = [
        ComplexNumber(-2.0, 1.5),   # 左上
        ComplexNumber(0.0, 0.0),    # 中央
        ComplexNumber(2.0, -1.5),   # 右下
        ComplexNumber(-1.0, 0.5),   # 任意の点
    ]
    
    for complex_point in test_complex_points:
        screen_point = ComplexCoordinateTransform.complex_to_screen(
            complex_point, widget_size, complex_region
        )
        print(f"  複素平面({complex_point.real:.3f}, {complex_point.imaginary:.3f}) → スクリーン({screen_point.x()}, {screen_point.y()})")
    
    print()
    
    # 3. ズーム領域の計算
    print("3. ズーム領域の計算")
    zoom_center = ComplexNumber(0.0, 0.0)
    zoom_factors = [2.0, 4.0, 0.5]  # 2倍ズームイン、4倍ズームイン、2倍ズームアウト
    
    for zoom_factor in zoom_factors:
        new_region = ComplexCoordinateTransform.calculate_zoom_region(
            complex_region, zoom_center, zoom_factor
        )
        zoom_type = "ズームイン" if zoom_factor > 1.0 else "ズームアウト"
        print(f"  {zoom_factor}倍{zoom_type}: 新しい領域サイズ 幅={new_region.width:.3f}, 高さ={new_region.height:.3f}")
        print(f"    中心: ({new_region.center.real:.3f}, {new_region.center.imaginary:.3f})")
    
    print()
    
    # 4. パン操作の計算
    print("4. パン操作の計算")
    pan_deltas = [
        QPoint(100, 0),    # 右に100ピクセル
        QPoint(0, 50),     # 下に50ピクセル
        QPoint(-50, -25),  # 左上に移動
    ]
    
    for pan_delta in pan_deltas:
        new_region = ComplexCoordinateTransform.calculate_pan_region(
            complex_region, pan_delta, widget_size
        )
        direction = f"({pan_delta.x():+d}, {pan_delta.y():+d})ピクセル移動"
        print(f"  {direction}: 新しい中心 ({new_region.center.real:.3f}, {new_region.center.imaginary:.3f})")
    
    print()
    
    # 5. 往復変換の精度確認
    print("5. 往復変換の精度確認")
    original_screen = QPoint(350, 250)
    
    # スクリーン → 複素平面 → スクリーン
    complex_converted = ComplexCoordinateTransform.screen_to_complex(
        original_screen, widget_size, complex_region
    )
    screen_converted = ComplexCoordinateTransform.complex_to_screen(
        complex_converted, widget_size, complex_region
    )
    
    error_x = abs(screen_converted.x() - original_screen.x())
    error_y = abs(screen_converted.y() - original_screen.y())
    
    print(f"  元のスクリーン座標: ({original_screen.x()}, {original_screen.y()})")
    print(f"  変換後のスクリーン座標: ({screen_converted.x()}, {screen_converted.y()})")
    print(f"  誤差: X={error_x}ピクセル, Y={error_y}ピクセル")
    
    if error_x <= 1 and error_y <= 1:
        print("  ✓ 往復変換の精度は良好です")
    else:
        print("  ⚠ 往復変換に誤差があります")
    
    print("\n=== デモ完了 ===")


if __name__ == "__main__":
    main()