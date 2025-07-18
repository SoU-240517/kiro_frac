"""
プラグインシステムのテスト。
実装されたプラグインシステムの動作を検証します。
"""
import sys
import os
sys.path.append('.')

from fractal_editor.plugins.base import plugin_manager, PluginMetadata
from fractal_editor.plugins.developer_api import PluginDeveloperAPI
from fractal_editor.plugins.samples.burning_ship_plugin import BurningShipPlugin
from fractal_editor.plugins.samples.tricorn_plugin import TricornPlugin
from fractal_editor.models.data_models import FractalParameters
from fractal_editor.plugins.template_generator import PluginTemplateGenerator


def test_plugin_manager():
    """プラグインマネージャーのテスト。"""
    print("=== プラグインマネージャーテスト ===")
    
    # 初期状態の確認
    print(f"読み込み済みプラグイン数: {len(plugin_manager.get_loaded_plugins())}")
    
    # サンプルプラグインを読み込み
    burning_ship = BurningShipPlugin()
    tricorn = TricornPlugin()
    
    # プラグインを読み込み
    success1 = plugin_manager.load_plugin(BurningShipPlugin)
    success2 = plugin_manager.load_plugin(TricornPlugin)
    
    print(f"バーニングシップ読み込み: {success1}")
    print(f"トリコーン読み込み: {success2}")
    
    # 読み込み済みプラグインを確認
    loaded_plugins = plugin_manager.get_loaded_plugins()
    print(f"読み込み済みプラグイン: {loaded_plugins}")
    
    # プラグイン情報を表示
    for plugin_name in loaded_plugins:
        info = plugin_manager.get_plugin_info(plugin_name)
        if info:
            print(f"  - {info.name} v{info.version} by {info.author}")
    
    # 統計情報を表示
    stats = plugin_manager.get_plugin_statistics()
    print(f"統計情報: {stats}")
    
    return loaded_plugins


def test_plugin_functionality():
    """プラグイン機能のテスト。"""
    print("\n=== プラグイン機能テスト ===")
    
    # バーニングシッププラグインをテスト
    burning_ship = BurningShipPlugin()
    generator = burning_ship.create_generator()
    
    print(f"生成器名: {generator.name}")
    print(f"説明: {generator.description}")
    
    # パラメータ定義を確認
    param_defs = generator.get_parameter_definitions()
    print(f"パラメータ数: {len(param_defs)}")
    for param in param_defs:
        print(f"  - {param.display_name} ({param.parameter_type}): {param.default_value}")
    
    # 単一点の計算をテスト
    result = generator.calculate_point(complex(0, 0), 100, power=2.0, escape_radius=2.0)
    print(f"計算結果 (0+0i): {result}")
    
    result = generator.calculate_point(complex(-1, 0), 100, power=2.0, escape_radius=2.0)
    print(f"計算結果 (-1+0i): {result}")


def test_developer_api():
    """開発者向けAPIのテスト。"""
    print("\n=== 開発者向けAPIテスト ===")
    
    # パラメータ定義の作成
    param_def = PluginDeveloperAPI.create_parameter_definition(
        name="test_param",
        display_name="テストパラメータ",
        param_type="float",
        default_value=1.0,
        min_value=0.0,
        max_value=10.0,
        description="テスト用のパラメータ"
    )
    
    print(f"パラメータ定義: {param_def.display_name} ({param_def.parameter_type})")
    
    # 複素平面領域の作成
    region = PluginDeveloperAPI.create_complex_region(
        center_real=0.0,
        center_imag=0.0,
        width=4.0,
        height=4.0
    )
    
    print(f"複素平面領域: {region.top_left} to {region.bottom_right}")
    
    # メタデータの検証
    metadata = PluginMetadata(
        name="テストプラグイン",
        version="1.0.0",
        author="テスト作者",
        description="テスト用プラグイン"
    )
    
    errors = PluginDeveloperAPI.validate_plugin_metadata(metadata)
    print(f"メタデータ検証エラー: {errors}")
    
    # プラグインテンプレートの取得
    templates = PluginDeveloperAPI.get_plugin_templates()
    print(f"利用可能なテンプレート数: {len(templates)}")
    for template in templates:
        print(f"  - {template.name}: {template.description}")


def test_template_generator():
    """テンプレート生成器のテスト。"""
    print("\n=== テンプレート生成器テスト ===")
    
    # 基本テンプレートを生成
    basic_template = PluginTemplateGenerator.generate_basic_plugin_template(
        plugin_name="テストフラクタル",
        author="テスト開発者",
        description="テスト用のフラクタルプラグイン"
    )
    
    print(f"基本テンプレート生成完了 (長さ: {len(basic_template)} 文字)")
    
    # 高度なテンプレートを生成
    advanced_template = PluginTemplateGenerator.generate_advanced_plugin_template(
        plugin_name="高度なテストフラクタル",
        author="テスト開発者",
        description="高度なテスト用フラクタルプラグイン"
    )
    
    print(f"高度なテンプレート生成完了 (長さ: {len(advanced_template)} 文字)")
    
    # 数式ベーステンプレートを生成
    formula_template = PluginTemplateGenerator.generate_formula_based_template(
        plugin_name="数式テストフラクタル",
        author="テスト開発者",
        description="数式ベースのテスト用フラクタルプラグイン",
        formula="z**3 + c"
    )
    
    print(f"数式ベーステンプレート生成完了 (長さ: {len(formula_template)} 文字)")


def test_error_handling():
    """エラーハンドリングのテスト。"""
    print("\n=== エラーハンドリングテスト ===")
    
    # 存在しないプラグインのアンロードを試行
    result = plugin_manager.unload_plugin("存在しないプラグイン")
    print(f"存在しないプラグインのアンロード: {result}")
    
    # 無効なメタデータの検証
    invalid_metadata = PluginMetadata(
        name="",  # 空の名前
        version="",  # 空のバージョン
        author="",  # 空の作者
        description=""  # 空の説明
    )
    
    errors = PluginDeveloperAPI.validate_plugin_metadata(invalid_metadata)
    print(f"無効なメタデータのエラー数: {len(errors)}")
    for error in errors:
        print(f"  - {error}")


def main():
    """メインテスト関数。"""
    print("プラグインシステムテスト開始")
    
    try:
        # 各テストを実行
        loaded_plugins = test_plugin_manager()
        test_plugin_functionality()
        test_developer_api()
        test_template_generator()
        test_error_handling()
        
        print("\n=== テスト完了 ===")
        print("すべてのテストが正常に完了しました。")
        
        # クリーンアップ
        for plugin_name in loaded_plugins:
            plugin_manager.unload_plugin(plugin_name)
        
        print("プラグインをアンロードしました。")
        
    except Exception as e:
        print(f"テスト中にエラーが発生しました: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()