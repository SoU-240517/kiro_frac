"""
設定とプロジェクト管理機能のデモンストレーション

このスクリプトは、フラクタルエディタの設定管理とプロジェクト管理機能の
基本的な使用方法を示します。
"""

import os
import tempfile
from datetime import datetime

from fractal_editor.models.app_settings import AppSettings, SettingsManager
from fractal_editor.services.project_manager import ProjectManager, create_default_project
from fractal_editor.models.data_models import (
    ComplexNumber, ComplexRegion, FractalParameters, ColorPalette, 
    ColorStop, InterpolationMode
)


def demo_settings_management():
    """設定管理機能のデモ"""
    print("=== 設定管理機能のデモ ===")
    
    # 一時ディレクトリで設定マネージャーを作成
    temp_dir = tempfile.mkdtemp()
    settings_file = os.path.join(temp_dir, "demo_settings.json")
    settings_manager = SettingsManager(settings_file)
    
    # 1. デフォルト設定の読み込み
    print("1. デフォルト設定を読み込み...")
    default_settings = settings_manager.load_settings()
    print(f"   デフォルト最大反復回数: {default_settings.default_max_iterations}")
    print(f"   デフォルト画像サイズ: {default_settings.default_image_size}")
    print(f"   スレッド数: {default_settings.thread_count}")
    
    # 2. カスタム設定の作成と保存
    print("\n2. カスタム設定を作成・保存...")
    custom_settings = AppSettings(
        default_max_iterations=1500,
        default_image_size=(1920, 1080),
        default_color_palette="Plasma",
        enable_anti_aliasing=True,
        thread_count=8,
        brightness_adjustment=1.2,
        contrast_adjustment=1.1
    )
    
    success = settings_manager.save_settings(custom_settings)
    print(f"   設定保存結果: {'成功' if success else '失敗'}")
    
    # 3. 設定の読み込み確認
    print("\n3. 保存した設定を読み込み確認...")
    loaded_settings = settings_manager.load_settings()
    print(f"   最大反復回数: {loaded_settings.default_max_iterations}")
    print(f"   画像サイズ: {loaded_settings.default_image_size}")
    print(f"   カラーパレット: {loaded_settings.default_color_palette}")
    print(f"   明度調整: {loaded_settings.brightness_adjustment}")
    
    # 4. 設定のバックアップ
    print("\n4. 設定をバックアップ...")
    backup_file = os.path.join(temp_dir, "settings_backup.json")
    backup_success = settings_manager.backup_settings(backup_file)
    print(f"   バックアップ結果: {'成功' if backup_success else '失敗'}")
    
    # 5. 設定の変更
    print("\n5. 設定を変更...")
    modified_settings = AppSettings(
        default_max_iterations=800,
        default_color_palette="Cool"
    )
    settings_manager.save_settings(modified_settings)
    current = settings_manager.get_settings()
    print(f"   変更後の最大反復回数: {current.default_max_iterations}")
    print(f"   変更後のカラーパレット: {current.default_color_palette}")
    
    # 6. バックアップからの復元
    print("\n6. バックアップから復元...")
    restore_success = settings_manager.restore_from_backup(backup_file)
    print(f"   復元結果: {'成功' if restore_success else '失敗'}")
    
    restored = settings_manager.get_settings()
    print(f"   復元後の最大反復回数: {restored.default_max_iterations}")
    print(f"   復元後のカラーパレット: {restored.default_color_palette}")
    
    # クリーンアップ
    import shutil
    shutil.rmtree(temp_dir, ignore_errors=True)
    print("\n設定管理デモ完了！")


def demo_project_management():
    """プロジェクト管理機能のデモ"""
    print("\n=== プロジェクト管理機能のデモ ===")
    
    # 一時ディレクトリでプロジェクトマネージャーを作成
    temp_dir = tempfile.mkdtemp()
    project_manager = ProjectManager(temp_dir)
    
    # 1. デフォルトプロジェクトの作成
    print("1. デフォルトプロジェクトを作成...")
    default_project = create_default_project("デモプロジェクト1")
    print(f"   プロジェクト名: {default_project.name}")
    print(f"   フラクタルタイプ: {default_project.fractal_type}")
    print(f"   最大反復回数: {default_project.parameters.max_iterations}")
    print(f"   画像サイズ: {default_project.parameters.image_size}")
    
    # 2. カスタムプロジェクトの作成
    print("\n2. カスタムプロジェクトを作成...")
    
    # カスタム複素領域（ズームイン）
    custom_region = ComplexRegion(
        top_left=ComplexNumber(-0.8, 0.2),
        bottom_right=ComplexNumber(-0.7, 0.1)
    )
    
    # カスタムパラメータ
    custom_parameters = FractalParameters(
        region=custom_region,
        max_iterations=2000,
        image_size=(1024, 768),
        custom_parameters={'zoom_level': 10, 'detail_mode': 'high'}
    )
    
    # カスタムカラーパレット
    custom_palette = ColorPalette(
        name="Custom Sunset",
        color_stops=[
            ColorStop(0.0, (0, 0, 0)),        # 黒
            ColorStop(0.3, (128, 0, 128)),    # 紫
            ColorStop(0.6, (255, 165, 0)),    # オレンジ
            ColorStop(1.0, (255, 255, 0))     # 黄色
        ],
        interpolation_mode=InterpolationMode.HSV
    )
    
    from fractal_editor.models.data_models import FractalProject
    custom_project = FractalProject(
        name="カスタムマンデルブロ探索",
        fractal_type="mandelbrot",
        parameters=custom_parameters,
        color_palette=custom_palette
    )
    
    print(f"   プロジェクト名: {custom_project.name}")
    print(f"   複素領域: {custom_project.parameters.region.top_left} to {custom_project.parameters.region.bottom_right}")
    print(f"   カラーパレット: {custom_project.color_palette.name}")
    print(f"   補間モード: {custom_project.color_palette.interpolation_mode.value}")
    
    # 3. プロジェクトの保存
    print("\n3. プロジェクトを保存...")
    project1_path = os.path.join(temp_dir, "demo_project_1")
    project2_path = os.path.join(temp_dir, "custom_mandelbrot")
    
    project_manager.save_project(default_project, project1_path)
    project_manager.save_project(custom_project, project2_path)
    
    print(f"   プロジェクト1保存先: {project1_path}.fractal")
    print(f"   プロジェクト2保存先: {project2_path}.fractal")
    
    # 4. 最近使用したプロジェクトの確認
    print("\n4. 最近使用したプロジェクトを確認...")
    recent_projects = project_manager.get_recent_projects()
    print(f"   最近使用したプロジェクト数: {len(recent_projects)}")
    
    for i, project_info in enumerate(recent_projects):
        print(f"   {i+1}. {project_info['name']} ({project_info['fractal_type']})")
        print(f"      ファイル: {os.path.basename(project_info['file_path'])}")
        print(f"      最終更新: {project_info['last_modified'][:19]}")
    
    # 5. プロジェクトの読み込み
    print("\n5. プロジェクトを読み込み...")
    loaded_project = project_manager.load_project(project2_path + ".fractal")
    
    print(f"   読み込んだプロジェクト: {loaded_project.name}")
    print(f"   フラクタルタイプ: {loaded_project.fractal_type}")
    print(f"   最大反復回数: {loaded_project.parameters.max_iterations}")
    print(f"   カスタムパラメータ: {loaded_project.parameters.custom_parameters}")
    
    # 6. プロジェクトの統計情報
    print("\n6. プロジェクト統計情報...")
    print(f"   複素領域の幅: {loaded_project.parameters.region.width:.6f}")
    print(f"   複素領域の高さ: {loaded_project.parameters.region.height:.6f}")
    print(f"   複素領域の面積: {loaded_project.parameters.region.area:.6f}")
    print(f"   アスペクト比: {loaded_project.parameters.aspect_ratio:.3f}")
    
    # 7. 別のプロジェクトを作成（ジュリア集合）
    print("\n7. ジュリア集合プロジェクトを作成...")
    julia_project = create_default_project("ジュリア集合探索")
    julia_project.fractal_type = "julia"
    julia_project.parameters.custom_parameters = {
        'c_real': -0.7269,
        'c_imaginary': 0.1889
    }
    
    julia_path = os.path.join(temp_dir, "julia_exploration")
    project_manager.save_project(julia_project, julia_path)
    
    print(f"   ジュリア集合プロジェクト保存: {julia_path}.fractal")
    
    # 8. 最終的な最近使用したプロジェクトリスト
    print("\n8. 最終的な最近使用したプロジェクトリスト...")
    final_recent = project_manager.get_recent_projects()
    
    for i, project_info in enumerate(final_recent):
        print(f"   {i+1}. {project_info['name']}")
        print(f"      タイプ: {project_info['fractal_type']}")
        print(f"      最終アクセス: {project_info['last_accessed'][:19]}")
    
    # クリーンアップ
    import shutil
    shutil.rmtree(temp_dir, ignore_errors=True)
    print("\nプロジェクト管理デモ完了！")


def demo_integration():
    """設定とプロジェクト管理の統合デモ"""
    print("\n=== 統合機能デモ ===")
    
    temp_dir = tempfile.mkdtemp()
    
    # 設定マネージャーとプロジェクトマネージャーを初期化
    settings_manager = SettingsManager(os.path.join(temp_dir, "integrated_settings.json"))
    project_manager = ProjectManager(temp_dir)
    
    print("1. 統合環境を初期化...")
    
    # カスタム設定を作成
    app_settings = AppSettings(
        default_max_iterations=1800,
        default_image_size=(1600, 1200),
        default_color_palette="Viridis",
        recent_projects_count=5,
        auto_backup_enabled=True
    )
    settings_manager.save_settings(app_settings)
    
    print("2. 設定に基づいてプロジェクトを作成...")
    
    # 設定を取得してプロジェクトに反映（将来的な機能）
    current_settings = settings_manager.get_settings()
    
    # 複数のプロジェクトを作成・保存
    project_names = [
        "高解像度マンデルブロ",
        "ジュリア集合コレクション",
        "フラクタルアート作品1",
        "数学研究プロジェクト"
    ]
    
    for name in project_names:
        project = create_default_project(name)
        # 設定の値を反映（デモ用）
        project.parameters.max_iterations = current_settings.default_max_iterations
        project.parameters.image_size = current_settings.default_image_size
        
        file_path = os.path.join(temp_dir, name.replace(" ", "_"))
        project_manager.save_project(project, file_path)
        
        print(f"   保存: {name}")
    
    print("\n3. 統合状態を確認...")
    
    # 設定情報
    settings = settings_manager.get_settings()
    print(f"   現在の設定 - 最大反復回数: {settings.default_max_iterations}")
    print(f"   現在の設定 - 画像サイズ: {settings.default_image_size}")
    print(f"   現在の設定 - 最近使用プロジェクト数制限: {settings.recent_projects_count}")
    
    # プロジェクト情報
    recent_projects = project_manager.get_recent_projects()
    print(f"   保存されたプロジェクト数: {len(recent_projects)}")
    
    print("\n4. 設定とプロジェクトの同期デモ...")
    
    # 設定を変更
    new_settings = AppSettings(
        default_max_iterations=2500,
        default_image_size=(2048, 1536),
        recent_projects_count=3
    )
    settings_manager.save_settings(new_settings)
    
    # 新しいプロジェクトを作成（新しい設定を反映）
    final_project = create_default_project("最終統合テスト")
    final_project.parameters.max_iterations = new_settings.default_max_iterations
    final_project.parameters.image_size = new_settings.default_image_size
    
    final_path = os.path.join(temp_dir, "final_integration_test")
    project_manager.save_project(final_project, final_path)
    
    print(f"   新しい設定でプロジェクト作成: {final_project.name}")
    print(f"   反復回数: {final_project.parameters.max_iterations}")
    print(f"   画像サイズ: {final_project.parameters.image_size}")
    
    # 最終状態
    final_recent = project_manager.get_recent_projects()
    print(f"\n   最終的な最近使用プロジェクト数: {len(final_recent)}")
    
    # クリーンアップ
    import shutil
    shutil.rmtree(temp_dir, ignore_errors=True)
    print("\n統合機能デモ完了！")


def main():
    """メイン関数"""
    print("フラクタルエディタ - 設定とプロジェクト管理機能デモ")
    print("=" * 60)
    
    try:
        # 各デモを実行
        demo_settings_management()
        demo_project_management()
        demo_integration()
        
        print("\n" + "=" * 60)
        print("すべてのデモが正常に完了しました！")
        print("\n主な機能:")
        print("✓ アプリケーション設定の管理（保存・読み込み・バックアップ・復元）")
        print("✓ フラクタルプロジェクトの管理（作成・保存・読み込み）")
        print("✓ 最近使用したプロジェクトの追跡")
        print("✓ 設定とプロジェクトの統合管理")
        print("✓ エラーハンドリングと妥当性検証")
        print("✓ JSON形式でのデータ永続化")
        
    except Exception as e:
        print(f"\nエラーが発生しました: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()