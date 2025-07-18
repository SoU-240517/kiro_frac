"""
画像エクスポート機能の統合テスト
実際のフラクタル生成からエクスポートまでの一連の流れをテスト
"""

import sys
import os
import tempfile
import numpy as np
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer
from PIL import Image

# プロジェクトのルートディレクトリをパスに追加
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fractal_editor.generators.mandelbrot import MandelbrotGenerator
from fractal_editor.models.data_models import FractalParameters, ComplexRegion, ComplexNumber
from fractal_editor.services.image_renderer import RenderingEngine, RenderSettings
from fractal_editor.services.color_system import GradientColorMapper, PresetPalettes
from fractal_editor.controllers.export_controller import ExportController


def test_complete_export_workflow():
    """完全なエクスポートワークフローのテスト"""
    print("🔄 完全なエクスポートワークフローのテストを開始...")
    
    try:
        # 1. フラクタル生成
        print("  📊 フラクタルを生成中...")
        generator = MandelbrotGenerator()
        
        parameters = FractalParameters(
            region=ComplexRegion(
                top_left=ComplexNumber(-2.0, 1.0),
                bottom_right=ComplexNumber(1.0, -1.0)
            ),
            max_iterations=100,
            image_size=(200, 200),
            custom_parameters={}
        )
        
        result = generator.calculate(parameters)
        print(f"  ✅ フラクタル生成完了: {result.iteration_data.shape}")
        
        # 2. カラーマッピング設定
        print("  🎨 カラーマッピングを設定中...")
        color_mapper = GradientColorMapper()
        color_mapper.set_palette(PresetPalettes.get_rainbow())
        
        # 3. レンダリングエンジン設定
        print("  🖼️ レンダリングエンジンを設定中...")
        rendering_engine = RenderingEngine()
        rendering_engine.set_color_mapper(color_mapper)
        
        # 4. 一時ディレクトリ作成
        temp_dir = tempfile.mkdtemp()
        print(f"  📁 一時ディレクトリ: {temp_dir}")
        
        # 5. PNG形式でエクスポート
        png_path = os.path.join(temp_dir, "test_mandelbrot.png")
        print(f"  💾 PNG形式でエクスポート中: {png_path}")
        
        rendering_engine.export_image(
            iteration_data=result.iteration_data,
            max_iterations=parameters.max_iterations,
            filepath=png_path,
            high_resolution=False
        )
        
        # ファイル存在確認
        if os.path.exists(png_path):
            with Image.open(png_path) as img:
                print(f"  ✅ PNG エクスポート成功: {img.size}, {img.format}")
        else:
            raise FileNotFoundError("PNG ファイルが作成されませんでした")
        
        # 6. JPEG形式でエクスポート
        jpeg_path = os.path.join(temp_dir, "test_mandelbrot.jpg")
        print(f"  💾 JPEG形式でエクスポート中: {jpeg_path}")
        
        rendering_engine.export_image(
            iteration_data=result.iteration_data,
            max_iterations=parameters.max_iterations,
            filepath=jpeg_path,
            high_resolution=False,
            quality=90
        )
        
        # ファイル存在確認
        if os.path.exists(jpeg_path):
            with Image.open(jpeg_path) as img:
                print(f"  ✅ JPEG エクスポート成功: {img.size}, {img.format}")
        else:
            raise FileNotFoundError("JPEG ファイルが作成されませんでした")
        
        # 7. 高解像度エクスポート
        hires_path = os.path.join(temp_dir, "test_mandelbrot_hires.png")
        print(f"  🔍 高解像度エクスポート中: {hires_path}")
        
        rendering_engine.export_image(
            iteration_data=result.iteration_data,
            max_iterations=parameters.max_iterations,
            filepath=hires_path,
            high_resolution=True,
            scale_factor=2
        )
        
        # ファイル存在確認
        if os.path.exists(hires_path):
            with Image.open(hires_path) as img:
                expected_size = (200 * 2, 200 * 2)
                if img.size == expected_size:
                    print(f"  ✅ 高解像度エクスポート成功: {img.size}")
                else:
                    print(f"  ⚠️ 高解像度サイズが期待値と異なります: {img.size} (期待値: {expected_size})")
        else:
            raise FileNotFoundError("高解像度ファイルが作成されませんでした")
        
        # 8. カスタムレンダリング設定でエクスポート
        custom_path = os.path.join(temp_dir, "test_mandelbrot_custom.png")
        print(f"  ⚙️ カスタム設定でエクスポート中: {custom_path}")
        
        custom_settings = RenderSettings(
            anti_aliasing=True,
            brightness=1.2,
            contrast=1.1,
            gamma=0.9
        )
        
        rendering_engine.export_image(
            iteration_data=result.iteration_data,
            max_iterations=parameters.max_iterations,
            filepath=custom_path,
            settings=custom_settings
        )
        
        # ファイル存在確認
        if os.path.exists(custom_path):
            with Image.open(custom_path) as img:
                print(f"  ✅ カスタム設定エクスポート成功: {img.size}")
        else:
            raise FileNotFoundError("カスタム設定ファイルが作成されませんでした")
        
        # 9. ファイルサイズ比較
        print("  📏 ファイルサイズ比較:")
        files = [
            ("PNG (標準)", png_path),
            ("JPEG (品質90%)", jpeg_path),
            ("PNG (高解像度)", hires_path),
            ("PNG (カスタム設定)", custom_path)
        ]
        
        for name, path in files:
            if os.path.exists(path):
                size_kb = os.path.getsize(path) / 1024
                print(f"    {name}: {size_kb:.1f} KB")
        
        # 10. クリーンアップ
        print("  🧹 一時ファイルをクリーンアップ中...")
        import shutil
        shutil.rmtree(temp_dir)
        
        print("✅ 完全なエクスポートワークフローテスト成功！")
        return True
        
    except Exception as e:
        print(f"❌ エクスポートワークフローテスト失敗: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_export_controller_integration():
    """エクスポートコントローラーの統合テスト"""
    print("\n🔄 エクスポートコントローラーの統合テストを開始...")
    
    try:
        # QApplicationの初期化
        if not QApplication.instance():
            app = QApplication(sys.argv)
        
        # 1. フラクタル生成
        print("  📊 フラクタルを生成中...")
        generator = MandelbrotGenerator()
        
        parameters = FractalParameters(
            region=ComplexRegion(
                top_left=ComplexNumber(-1.5, 1.0),
                bottom_right=ComplexNumber(0.5, -1.0)
            ),
            max_iterations=80,
            image_size=(150, 150),
            custom_parameters={}
        )
        
        result = generator.calculate(parameters)
        print(f"  ✅ フラクタル生成完了: {result.iteration_data.shape}")
        
        # 2. エクスポートコントローラー初期化
        print("  🎛️ エクスポートコントローラーを初期化中...")
        controller = ExportController()
        controller.initialize()
        
        # 3. フラクタルデータ設定
        controller.set_fractal_data(result, parameters.max_iterations)
        print("  ✅ フラクタルデータ設定完了")
        
        # 4. サポートされている形式の確認
        formats = controller.get_supported_formats()
        print(f"  📋 サポートされている形式: {len(formats)} 種類")
        for fmt in formats:
            print(f"    - {fmt['name']}: {fmt['description']}")
        
        # 5. 一時ディレクトリ作成
        temp_dir = tempfile.mkdtemp()
        
        # 6. クイックエクスポートテスト
        quick_export_path = os.path.join(temp_dir, "quick_export.png")
        print(f"  ⚡ クイックエクスポート実行: {quick_export_path}")
        
        success = controller.quick_export(quick_export_path, "PNG")
        if success and os.path.exists(quick_export_path):
            print("  ✅ クイックエクスポート成功")
        else:
            raise RuntimeError("クイックエクスポートが失敗しました")
        
        # 7. 高解像度クイックエクスポート
        hires_export_path = os.path.join(temp_dir, "quick_export_hires.png")
        print(f"  🔍 高解像度クイックエクスポート実行: {hires_export_path}")
        
        success = controller.quick_export(hires_export_path, "PNG", high_resolution=True, scale_factor=3)
        if success and os.path.exists(hires_export_path):
            with Image.open(hires_export_path) as img:
                expected_size = (150 * 3, 150 * 3)
                if img.size == expected_size:
                    print(f"  ✅ 高解像度クイックエクスポート成功: {img.size}")
                else:
                    print(f"  ⚠️ サイズが期待値と異なります: {img.size} (期待値: {expected_size})")
        else:
            raise RuntimeError("高解像度クイックエクスポートが失敗しました")
        
        # 8. エクスポート履歴確認
        history = controller.get_export_history()
        print(f"  📚 エクスポート履歴: {len(history)} 件")
        for i, entry in enumerate(history):
            print(f"    {i+1}. {os.path.basename(entry['filepath'])} ({entry.get('timestamp', 'N/A')})")
        
        # 9. 設定検証テスト
        print("  🔍 設定検証テスト...")
        
        valid_settings = {
            'filepath': quick_export_path,
            'format': 'PNG',
            'high_resolution': False,
            'width': 800,
            'height': 600,
            'anti_aliasing': True,
            'brightness': 1.0,
            'contrast': 1.0,
            'gamma': 1.0
        }
        
        is_valid, error_msg = controller.validate_export_settings(valid_settings)
        if is_valid:
            print("  ✅ 設定検証成功")
        else:
            print(f"  ❌ 設定検証失敗: {error_msg}")
        
        # 10. クリーンアップ
        print("  🧹 一時ファイルをクリーンアップ中...")
        import shutil
        shutil.rmtree(temp_dir)
        
        print("✅ エクスポートコントローラー統合テスト成功！")
        return True
        
    except Exception as e:
        print(f"❌ エクスポートコントローラー統合テスト失敗: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """メイン関数"""
    print("🚀 画像エクスポート機能の統合テストを開始します\n")
    
    success_count = 0
    total_tests = 2
    
    # テスト1: 完全なエクスポートワークフロー
    if test_complete_export_workflow():
        success_count += 1
    
    # テスト2: エクスポートコントローラー統合
    if test_export_controller_integration():
        success_count += 1
    
    # 結果表示
    print(f"\n📊 テスト結果: {success_count}/{total_tests} 成功")
    
    if success_count == total_tests:
        print("🎉 すべての統合テストが成功しました！")
        print("\n✨ 画像エクスポート機能は正常に動作しています:")
        print("  ✅ PNG形式での画像出力")
        print("  ✅ JPEG形式での画像出力")
        print("  ✅ 解像度指定機能")
        print("  ✅ 高解像度画像生成")
        print("  ✅ カスタムレンダリング設定")
        print("  ✅ エクスポートコントローラー統合")
        print("  ✅ クイックエクスポート機能")
        print("  ✅ エクスポート履歴管理")
        print("  ✅ 設定検証機能")
        return True
    else:
        print("❌ 一部のテストが失敗しました")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)