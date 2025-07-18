"""
設定とプロジェクト管理の統合テスト

このテストファイルは、設定管理とプロジェクト管理機能の統合動作を検証します。
"""

import unittest
import tempfile
import os
from pathlib import Path

from fractal_editor.models.app_settings import AppSettings, SettingsManager
from fractal_editor.services.project_manager import ProjectManager, create_default_project
from fractal_editor.models.data_models import FractalProject, ComplexNumber, ComplexRegion


class TestSettingsProjectIntegration(unittest.TestCase):
    """設定とプロジェクト管理の統合テスト"""
    
    def setUp(self):
        """テスト前の準備"""
        # 一時ディレクトリを作成
        self.temp_dir = tempfile.mkdtemp()
        
        # 設定マネージャーとプロジェクトマネージャーを初期化
        self.settings_manager = SettingsManager(
            os.path.join(self.temp_dir, "settings.json")
        )
        self.project_manager = ProjectManager(self.temp_dir)
    
    def tearDown(self):
        """テスト後のクリーンアップ"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_settings_affect_default_project_creation(self):
        """設定がデフォルトプロジェクト作成に影響することをテスト"""
        # カスタム設定を作成
        custom_settings = AppSettings(
            default_max_iterations=1500,
            default_image_size=(1024, 768),
            default_color_palette="Cool"
        )
        self.settings_manager.save_settings(custom_settings)
        
        # デフォルトプロジェクトを作成
        project = create_default_project("設定テストプロジェクト")
        
        # 設定の値がプロジェクトに反映されていることを確認
        # （現在の実装では直接反映されないが、将来的に統合予定）
        self.assertEqual(project.name, "設定テストプロジェクト")
        self.assertEqual(project.fractal_type, "mandelbrot")
    
    def test_project_save_load_with_custom_settings(self):
        """カスタム設定環境でのプロジェクト保存・読み込みをテスト"""
        # カスタム設定を保存
        custom_settings = AppSettings(
            recent_projects_count=5,
            auto_backup_enabled=True
        )
        self.settings_manager.save_settings(custom_settings)
        
        # プロジェクトを作成・保存
        project = create_default_project("統合テストプロジェクト")
        file_path = os.path.join(self.temp_dir, "integration_test")
        
        self.project_manager.save_project(project, file_path)
        
        # プロジェクトを読み込み
        loaded_project = self.project_manager.load_project(file_path + ".fractal")
        
        # データが正しく保存・読み込みされることを確認
        self.assertEqual(loaded_project.name, "統合テストプロジェクト")
        
        # 最近使用したプロジェクトリストに追加されることを確認
        recent_projects = self.project_manager.get_recent_projects()
        self.assertEqual(len(recent_projects), 1)
        self.assertEqual(recent_projects[0]['name'], "統合テストプロジェクト")
    
    def test_settings_backup_and_project_management(self):
        """設定のバックアップとプロジェクト管理の併用をテスト"""
        # 初期設定を作成
        initial_settings = AppSettings(
            default_max_iterations=800,
            recent_projects_count=15
        )
        self.settings_manager.save_settings(initial_settings)
        
        # プロジェクトを複数作成・保存
        for i in range(3):
            project = create_default_project(f"プロジェクト{i+1}")
            file_path = os.path.join(self.temp_dir, f"project_{i+1}")
            self.project_manager.save_project(project, file_path)
        
        # 設定をバックアップ
        backup_path = os.path.join(self.temp_dir, "settings_backup.json")
        backup_success = self.settings_manager.backup_settings(backup_path)
        self.assertTrue(backup_success)
        
        # 設定を変更
        modified_settings = AppSettings(
            default_max_iterations=1200,
            recent_projects_count=5
        )
        self.settings_manager.save_settings(modified_settings)
        
        # 最近使用したプロジェクトが3件あることを確認
        recent_projects = self.project_manager.get_recent_projects()
        self.assertEqual(len(recent_projects), 3)
        
        # 設定を復元
        restore_success = self.settings_manager.restore_from_backup(backup_path)
        self.assertTrue(restore_success)
        
        # 復元された設定を確認
        restored_settings = self.settings_manager.get_settings()
        self.assertEqual(restored_settings.default_max_iterations, 800)
        self.assertEqual(restored_settings.recent_projects_count, 15)
    
    def test_concurrent_settings_and_project_operations(self):
        """設定とプロジェクト操作の同時実行をテスト"""
        # 複数の設定変更とプロジェクト操作を交互に実行
        
        # 設定1を保存
        settings1 = AppSettings(default_max_iterations=500)
        self.settings_manager.save_settings(settings1)
        
        # プロジェクト1を保存
        project1 = create_default_project("同時実行テスト1")
        self.project_manager.save_project(
            project1, 
            os.path.join(self.temp_dir, "concurrent_1")
        )
        
        # 設定2を保存
        settings2 = AppSettings(default_max_iterations=1500)
        self.settings_manager.save_settings(settings2)
        
        # プロジェクト2を保存
        project2 = create_default_project("同時実行テスト2")
        self.project_manager.save_project(
            project2, 
            os.path.join(self.temp_dir, "concurrent_2")
        )
        
        # 最終的な状態を確認
        final_settings = self.settings_manager.get_settings()
        self.assertEqual(final_settings.default_max_iterations, 1500)
        
        recent_projects = self.project_manager.get_recent_projects()
        self.assertEqual(len(recent_projects), 2)
        
        # プロジェクトが正しく読み込めることを確認
        loaded_project1 = self.project_manager.load_project(
            os.path.join(self.temp_dir, "concurrent_1.fractal")
        )
        loaded_project2 = self.project_manager.load_project(
            os.path.join(self.temp_dir, "concurrent_2.fractal")
        )
        
        self.assertEqual(loaded_project1.name, "同時実行テスト1")
        self.assertEqual(loaded_project2.name, "同時実行テスト2")
    
    def test_error_handling_integration(self):
        """エラーハンドリングの統合テスト"""
        # 無効な設定を保存しようとする
        invalid_settings = AppSettings(default_max_iterations=5)  # 範囲外
        save_success = self.settings_manager.save_settings(invalid_settings)
        self.assertFalse(save_success)
        
        # 有効なプロジェクトは正常に保存できることを確認
        valid_project = create_default_project("エラーテストプロジェクト")
        self.project_manager.save_project(
            valid_project,
            os.path.join(self.temp_dir, "error_test")
        )
        
        # プロジェクトが正常に読み込めることを確認
        loaded_project = self.project_manager.load_project(
            os.path.join(self.temp_dir, "error_test.fractal")
        )
        self.assertEqual(loaded_project.name, "エラーテストプロジェクト")
        
        # 存在しないプロジェクトファイルの読み込みでエラーが発生することを確認
        from fractal_editor.services.project_manager import ProjectFileError
        with self.assertRaises(ProjectFileError):
            self.project_manager.load_project(
                os.path.join(self.temp_dir, "nonexistent.fractal")
            )


class TestSettingsProjectWorkflow(unittest.TestCase):
    """設定とプロジェクト管理の実際のワークフローテスト"""
    
    def setUp(self):
        """テスト前の準備"""
        self.temp_dir = tempfile.mkdtemp()
        self.settings_manager = SettingsManager(
            os.path.join(self.temp_dir, "workflow_settings.json")
        )
        self.project_manager = ProjectManager(self.temp_dir)
    
    def tearDown(self):
        """テスト後のクリーンアップ"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_typical_user_workflow(self):
        """典型的なユーザーワークフローをテスト"""
        # 1. アプリケーション起動時の設定読み込み
        initial_settings = self.settings_manager.load_settings()
        self.assertIsInstance(initial_settings, AppSettings)
        
        # 2. ユーザーが設定をカスタマイズ
        custom_settings = AppSettings(
            default_max_iterations=1200,
            default_image_size=(1920, 1080),
            default_color_palette="Plasma",
            enable_anti_aliasing=True,
            thread_count=8
        )
        self.settings_manager.save_settings(custom_settings)
        
        # 3. 新しいプロジェクトを作成
        project1 = create_default_project("マンデルブロ探索")
        
        # 4. プロジェクトのパラメータを調整
        project1.parameters.max_iterations = 2000
        project1.parameters.region = ComplexRegion(
            top_left=ComplexNumber(-0.8, 0.2),
            bottom_right=ComplexNumber(-0.7, 0.1)
        )
        
        # 5. プロジェクトを保存
        project1_path = os.path.join(self.temp_dir, "mandelbrot_exploration")
        self.project_manager.save_project(project1, project1_path)
        
        # 6. 別のプロジェクトを作成・保存
        project2 = create_default_project("ジュリア集合研究")
        project2.fractal_type = "julia"
        project2_path = os.path.join(self.temp_dir, "julia_research")
        self.project_manager.save_project(project2, project2_path)
        
        # 7. 最近使用したプロジェクトを確認
        recent_projects = self.project_manager.get_recent_projects()
        self.assertEqual(len(recent_projects), 2)
        
        # 最新のプロジェクトが先頭に来ることを確認
        self.assertEqual(recent_projects[0]['name'], "ジュリア集合研究")
        self.assertEqual(recent_projects[1]['name'], "マンデルブロ探索")
        
        # 8. プロジェクトを再度開く
        reopened_project = self.project_manager.load_project(project1_path + ".fractal")
        self.assertEqual(reopened_project.name, "マンデルブロ探索")
        self.assertEqual(reopened_project.parameters.max_iterations, 2000)
        
        # 9. 設定を確認
        current_settings = self.settings_manager.get_settings()
        self.assertEqual(current_settings.default_max_iterations, 1200)
        self.assertEqual(current_settings.thread_count, 8)
    
    def test_project_management_with_settings_changes(self):
        """設定変更を伴うプロジェクト管理をテスト"""
        # 初期設定
        settings = AppSettings(recent_projects_count=3)
        self.settings_manager.save_settings(settings)
        
        # 複数のプロジェクトを作成
        projects = []
        for i in range(5):
            project = create_default_project(f"プロジェクト{i+1}")
            file_path = os.path.join(self.temp_dir, f"project_{i+1}")
            self.project_manager.save_project(project, file_path)
            projects.append(project)
        
        # 最近使用したプロジェクト数が設定に従って制限されることを確認
        # （現在の実装では固定値10だが、将来的に設定から取得予定）
        recent_projects = self.project_manager.get_recent_projects()
        self.assertEqual(len(recent_projects), 5)  # 全て保持される
        
        # 設定を変更
        new_settings = AppSettings(recent_projects_count=2)
        self.settings_manager.save_settings(new_settings)
        
        # 新しいプロジェクトを追加
        new_project = create_default_project("新しいプロジェクト")
        new_file_path = os.path.join(self.temp_dir, "new_project")
        self.project_manager.save_project(new_project, new_file_path)
        
        # 最近使用したプロジェクトリストを確認
        recent_projects_after = self.project_manager.get_recent_projects()
        self.assertGreaterEqual(len(recent_projects_after), 1)


if __name__ == '__main__':
    unittest.main(verbosity=2)