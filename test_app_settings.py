"""
アプリケーション設定システムのテスト

AppSettingsクラスとSettingsManagerクラスの動作を検証します。
"""

import unittest
import tempfile
import os
import json
from pathlib import Path

from fractal_editor.models.app_settings import AppSettings, SettingsManager


class TestAppSettings(unittest.TestCase):
    """AppSettingsクラスのテスト"""
    
    def test_default_settings_creation(self):
        """デフォルト設定の作成をテスト"""
        settings = AppSettings()
        
        # デフォルト値の確認
        self.assertEqual(settings.default_max_iterations, 1000)
        self.assertEqual(settings.default_image_size, (800, 600))
        self.assertEqual(settings.default_color_palette, "Rainbow")
        self.assertTrue(settings.enable_anti_aliasing)
        # CPUコア数に基づいて調整されるため、実際のコア数を確認
        expected_cores = max(1, os.cpu_count() or 4)
        self.assertEqual(settings.thread_count, expected_cores)
        self.assertTrue(settings.enable_parallel_computation)
        self.assertEqual(settings.auto_save_interval, 300)
        self.assertEqual(settings.recent_projects_count, 10)
        self.assertEqual(settings.default_export_format, "PNG")
        self.assertEqual(settings.default_export_quality, 95)
    
    def test_settings_validation_valid_values(self):
        """有効な設定値の検証をテスト"""
        settings = AppSettings(
            default_max_iterations=500,
            default_image_size=(1024, 768),
            thread_count=8,
            auto_save_interval=120,
            recent_projects_count=5,
            brightness_adjustment=1.5,
            contrast_adjustment=1.2,
            memory_limit_mb=512,
            default_export_quality=85
        )
        
        self.assertTrue(settings.validate())
    
    def test_settings_validation_invalid_values(self):
        """無効な設定値の検証をテスト"""
        # 最大反復回数が範囲外
        settings = AppSettings(default_max_iterations=5)
        self.assertFalse(settings.validate())
        
        settings = AppSettings(default_max_iterations=15000)
        self.assertFalse(settings.validate())
        
        # 画像サイズが小さすぎる
        settings = AppSettings(default_image_size=(50, 50))
        self.assertFalse(settings.validate())
        
        # スレッド数が範囲外
        settings = AppSettings(thread_count=0)
        self.assertFalse(settings.validate())
        
        settings = AppSettings(thread_count=50)
        self.assertFalse(settings.validate())
        
        # 自動保存間隔が範囲外
        settings = AppSettings(auto_save_interval=10)
        self.assertFalse(settings.validate())
        
        settings = AppSettings(auto_save_interval=5000)
        self.assertFalse(settings.validate())
        
        # 明度調整が範囲外
        settings = AppSettings(brightness_adjustment=0.05)
        self.assertFalse(settings.validate())
        
        settings = AppSettings(brightness_adjustment=5.0)
        self.assertFalse(settings.validate())
    
    def test_to_dict_conversion(self):
        """辞書への変換をテスト"""
        settings = AppSettings(
            default_max_iterations=750,
            default_color_palette="Grayscale"
        )
        
        data = settings.to_dict()
        
        self.assertIsInstance(data, dict)
        self.assertEqual(data['default_max_iterations'], 750)
        self.assertEqual(data['default_color_palette'], "Grayscale")
        self.assertIn('enable_anti_aliasing', data)
    
    def test_from_dict_creation(self):
        """辞書からの作成をテスト"""
        data = {
            'default_max_iterations': 1500,
            'default_image_size': [1920, 1080],
            'default_color_palette': 'Hot',
            'enable_anti_aliasing': False,
            'thread_count': 6
        }
        
        settings = AppSettings.from_dict(data)
        
        self.assertEqual(settings.default_max_iterations, 1500)
        self.assertEqual(settings.default_image_size, [1920, 1080])
        self.assertEqual(settings.default_color_palette, 'Hot')
        self.assertFalse(settings.enable_anti_aliasing)
        self.assertEqual(settings.thread_count, 6)
    
    def test_from_dict_with_invalid_keys(self):
        """無効なキーを含む辞書からの作成をテスト"""
        data = {
            'default_max_iterations': 800,
            'invalid_key': 'invalid_value',
            'another_invalid_key': 123
        }
        
        settings = AppSettings.from_dict(data)
        
        # 有効なキーのみが適用される
        self.assertEqual(settings.default_max_iterations, 800)
        # 無効なキーは無視され、デフォルト値が使用される
        self.assertEqual(settings.default_color_palette, "Rainbow")


class TestSettingsManager(unittest.TestCase):
    """SettingsManagerクラスのテスト"""
    
    def setUp(self):
        """テスト前の準備"""
        # 一時ディレクトリを作成
        self.temp_dir = tempfile.mkdtemp()
        self.settings_file = os.path.join(self.temp_dir, "test_settings.json")
        self.manager = SettingsManager(self.settings_file)
    
    def tearDown(self):
        """テスト後のクリーンアップ"""
        # 一時ディレクトリ内のすべてのファイルを削除
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_save_and_load_settings(self):
        """設定の保存と読み込みをテスト"""
        # カスタム設定を作成
        original_settings = AppSettings(
            default_max_iterations=1200,
            default_color_palette="Cool",
            enable_anti_aliasing=False,
            thread_count=8
        )
        
        # 設定を保存
        success = self.manager.save_settings(original_settings)
        self.assertTrue(success)
        self.assertTrue(os.path.exists(self.settings_file))
        
        # 設定を読み込み
        loaded_settings = self.manager.load_settings()
        
        # 値が正しく保存・読み込みされているか確認
        self.assertEqual(loaded_settings.default_max_iterations, 1200)
        self.assertEqual(loaded_settings.default_color_palette, "Cool")
        self.assertFalse(loaded_settings.enable_anti_aliasing)
        self.assertEqual(loaded_settings.thread_count, 8)
    
    def test_load_nonexistent_file(self):
        """存在しないファイルの読み込みをテスト"""
        # 存在しないファイルを指定
        nonexistent_file = os.path.join(self.temp_dir, "nonexistent.json")
        manager = SettingsManager(nonexistent_file)
        
        # デフォルト設定が返されることを確認
        settings = manager.load_settings()
        self.assertIsInstance(settings, AppSettings)
        self.assertEqual(settings.default_max_iterations, 1000)  # デフォルト値
        
        # ファイルが作成されることを確認
        self.assertTrue(os.path.exists(nonexistent_file))
    
    def test_load_invalid_json_file(self):
        """無効なJSONファイルの読み込みをテスト"""
        # 無効なJSONファイルを作成
        with open(self.settings_file, 'w') as f:
            f.write("invalid json content {")
        
        # デフォルト設定が返されることを確認
        settings = self.manager.load_settings()
        self.assertIsInstance(settings, AppSettings)
        self.assertEqual(settings.default_max_iterations, 1000)  # デフォルト値
    
    def test_save_invalid_settings(self):
        """無効な設定の保存をテスト"""
        # 無効な設定を作成
        invalid_settings = AppSettings(default_max_iterations=5)  # 範囲外の値
        
        # 保存が失敗することを確認
        success = self.manager.save_settings(invalid_settings)
        self.assertFalse(success)
    
    def test_reset_to_defaults(self):
        """デフォルト設定へのリセットをテスト"""
        # カスタム設定を保存
        custom_settings = AppSettings(default_max_iterations=2000)
        self.manager.save_settings(custom_settings)
        
        # デフォルトにリセット
        default_settings = self.manager.reset_to_defaults()
        
        # デフォルト値が設定されていることを確認
        self.assertEqual(default_settings.default_max_iterations, 1000)
        
        # ファイルからも正しく読み込まれることを確認
        loaded_settings = self.manager.load_settings()
        self.assertEqual(loaded_settings.default_max_iterations, 1000)
    
    def test_backup_and_restore(self):
        """バックアップと復元をテスト"""
        # 元の設定を作成・保存
        original_settings = AppSettings(
            default_max_iterations=1500,
            default_color_palette="Plasma"
        )
        self.manager.save_settings(original_settings)
        
        # バックアップを作成
        backup_file = os.path.join(self.temp_dir, "backup.json")
        backup_success = self.manager.backup_settings(backup_file)
        self.assertTrue(backup_success)
        self.assertTrue(os.path.exists(backup_file))
        
        # 設定を変更
        modified_settings = AppSettings(
            default_max_iterations=500,
            default_color_palette="Viridis"
        )
        self.manager.save_settings(modified_settings)
        
        # バックアップから復元
        restore_success = self.manager.restore_from_backup(backup_file)
        self.assertTrue(restore_success)
        
        # 元の設定に戻っていることを確認
        restored_settings = self.manager.get_settings()
        self.assertEqual(restored_settings.default_max_iterations, 1500)
        self.assertEqual(restored_settings.default_color_palette, "Plasma")
        
        # バックアップファイルを削除
        os.remove(backup_file)
    
    def test_get_settings_caching(self):
        """設定のキャッシュ機能をテスト"""
        # 初回取得
        settings1 = self.manager.get_settings()
        
        # 2回目取得（キャッシュから）
        settings2 = self.manager.get_settings()
        
        # 同じオブジェクトが返されることを確認
        self.assertIs(settings1, settings2)
        
        # 新しい設定を保存後、キャッシュが更新されることを確認
        new_settings = AppSettings(default_max_iterations=800)
        self.manager.save_settings(new_settings)
        
        settings3 = self.manager.get_settings()
        self.assertEqual(settings3.default_max_iterations, 800)


if __name__ == '__main__':
    # テストの実行
    unittest.main(verbosity=2)