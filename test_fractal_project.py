"""
フラクタルプロジェクト管理システムのテスト

FractalProjectクラスとProjectManagerクラスの動作を検証します。
"""

import unittest
import tempfile
import os
import json
import shutil
from datetime import datetime
from pathlib import Path

from fractal_editor.models.fractal_project import FractalProject, ProjectManager
from fractal_editor.models.data_models import FractalParameters, ComplexRegion, ComplexNumber
from fractal_editor.models.color_system import ColorPalette, ColorStop, InterpolationMode


class TestFractalProject(unittest.TestCase):
    """FractalProjectクラスのテスト"""
    
    def test_default_project_creation(self):
        """デフォルトプロジェクトの作成をテスト"""
        project = FractalProject(name="Test Project")
        
        # デフォルト値の確認
        self.assertEqual(project.name, "Test Project")
        self.assertEqual(project.fractal_type, "Mandelbrot")
        self.assertEqual(project.image_size, (800, 600))
        self.assertEqual(project.max_iterations, 1000)
        self.assertEqual(project.version, "1.0")
        
        # デフォルトのフラクタルパラメータが設定されているか確認
        self.assertIsNotNone(project.fractal_parameters)
        self.assertIsNotNone(project.fractal_parameters.region)
        
        # デフォルトのカラーパレットが設定されているか確認
        self.assertIsNotNone(project.color_palette)
        self.assertTrue(len(project.color_palette.color_stops) > 0)
    
    def test_custom_project_creation(self):
        """カスタムプロジェクトの作成をテスト"""
        custom_region = ComplexRegion(
            top_left=ComplexNumber(-1.0, 0.5),
            bottom_right=ComplexNumber(0.5, -0.5)
        )
        
        custom_parameters = FractalParameters(
            region=custom_region,
            max_iterations=500,
            image_size=(1024, 768),
            custom_parameters={"test_param": "test_value"}
        )
        
        custom_palette = ColorPalette(
            name="Test Palette",
            color_stops=[
                ColorStop(0.0, (255, 0, 0)),
                ColorStop(1.0, (0, 0, 255))
            ],
            interpolation_mode=InterpolationMode.LINEAR
        )
        
        project = FractalProject(
            name="Custom Project",
            description="Test description",
            fractal_type="Julia",
            fractal_parameters=custom_parameters,
            color_palette=custom_palette,
            image_size=(1024, 768),
            max_iterations=500,
            author="Test Author"
        )
        
        # カスタム値の確認
        self.assertEqual(project.name, "Custom Project")
        self.assertEqual(project.description, "Test description")
        self.assertEqual(project.fractal_type, "Julia")
        self.assertEqual(project.image_size, (1024, 768))
        self.assertEqual(project.max_iterations, 500)
        self.assertEqual(project.author, "Test Author")
        
        # カスタムパラメータの確認
        self.assertEqual(project.fractal_parameters.max_iterations, 500)
        self.assertEqual(project.fractal_parameters.image_size, (1024, 768))
        self.assertEqual(project.fractal_parameters.custom_parameters["test_param"], "test_value")
        
        # カスタムパレットの確認
        self.assertEqual(project.color_palette.name, "Test Palette")
        self.assertEqual(len(project.color_palette.color_stops), 2)
    
    def test_project_validation_valid(self):
        """有効なプロジェクトの検証をテスト"""
        project = FractalProject(
            name="Valid Project",
            fractal_type="Mandelbrot",
            image_size=(800, 600),
            max_iterations=1000
        )
        
        self.assertTrue(project.validate())
    
    def test_project_validation_invalid(self):
        """無効なプロジェクトの検証をテスト"""
        # 空の名前
        project = FractalProject(name="")
        self.assertFalse(project.validate())
        
        # 無効な画像サイズ
        project = FractalProject(name="Test", image_size=(0, 600))
        self.assertFalse(project.validate())
        
        project = FractalProject(name="Test", image_size=(800, 0))
        self.assertFalse(project.validate())
        
        # 無効な最大反復回数
        project = FractalProject(name="Test", max_iterations=0)
        self.assertFalse(project.validate())
        
        project = FractalProject(name="Test", max_iterations=-1)
        self.assertFalse(project.validate())
    
    def test_to_dict_conversion(self):
        """辞書への変換をテスト"""
        project = FractalProject(
            name="Dict Test",
            description="Test description",
            fractal_type="Julia",
            author="Test Author"
        )
        
        data = project.to_dict()
        
        self.assertIsInstance(data, dict)
        self.assertEqual(data["name"], "Dict Test")
        self.assertEqual(data["description"], "Test description")
        self.assertEqual(data["fractal_type"], "Julia")
        self.assertEqual(data["author"], "Test Author")
        self.assertIn("fractal_parameters", data)
        self.assertIn("color_palette", data)
        self.assertIn("created_date", data)
        self.assertIn("last_modified", data)
    
    def test_from_dict_creation(self):
        """辞書からの作成をテスト"""
        data = {
            "name": "From Dict Test",
            "description": "Test description",
            "fractal_type": "Mandelbrot",
            "image_size": [1024, 768],
            "max_iterations": 1500,
            "author": "Test Author",
            "version": "2.0",
            "created_date": "2024-01-01T12:00:00",
            "last_modified": "2024-01-02T12:00:00",
            "fractal_parameters": {
                "region": {
                    "top_left": {"real": -2.0, "imaginary": 1.0},
                    "bottom_right": {"real": 1.0, "imaginary": -1.0}
                },
                "max_iterations": 1500,
                "image_size": [1024, 768],
                "custom_parameters": {"test": "value"}
            },
            "color_palette": {
                "name": "Test Palette",
                "color_stops": [
                    {"position": 0.0, "color": [255, 0, 0]},
                    {"position": 1.0, "color": [0, 0, 255]}
                ],
                "interpolation_mode": "linear"
            }
        }
        
        project = FractalProject.from_dict(data)
        
        # 基本情報の確認
        self.assertEqual(project.name, "From Dict Test")
        self.assertEqual(project.description, "Test description")
        self.assertEqual(project.fractal_type, "Mandelbrot")
        self.assertEqual(project.image_size, (1024, 768))
        self.assertEqual(project.max_iterations, 1500)
        self.assertEqual(project.author, "Test Author")
        self.assertEqual(project.version, "2.0")
        
        # フラクタルパラメータの確認
        self.assertIsNotNone(project.fractal_parameters)
        self.assertEqual(project.fractal_parameters.max_iterations, 1500)
        self.assertEqual(project.fractal_parameters.image_size, (1024, 768))
        self.assertEqual(project.fractal_parameters.custom_parameters["test"], "value")
        
        # カラーパレットの確認
        self.assertIsNotNone(project.color_palette)
        self.assertEqual(project.color_palette.name, "Test Palette")
        self.assertEqual(len(project.color_palette.color_stops), 2)
    
    def test_update_modification_time(self):
        """最終更新時刻の更新をテスト"""
        project = FractalProject(name="Time Test")
        original_time = project.last_modified
        
        # 少し待ってから更新
        import time
        time.sleep(0.01)
        project.update_modification_time()
        
        # 更新時刻が変更されているか確認
        self.assertGreater(project.last_modified, original_time)


class TestProjectManager(unittest.TestCase):
    """ProjectManagerクラスのテスト"""
    
    def setUp(self):
        """テスト前の準備"""
        # 一時ディレクトリを作成
        self.temp_dir = tempfile.mkdtemp()
        self.manager = ProjectManager(self.temp_dir)
    
    def tearDown(self):
        """テスト後のクリーンアップ"""
        # 一時ディレクトリを削除
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_create_new_project(self):
        """新しいプロジェクトの作成をテスト"""
        project = self.manager.create_new_project("New Test Project", "Julia")
        
        self.assertEqual(project.name, "New Test Project")
        self.assertEqual(project.fractal_type, "Julia")
        self.assertIn("Julia", project.description)
        self.assertIsNotNone(project.author)
    
    def test_save_and_load_project(self):
        """プロジェクトの保存と読み込みをテスト"""
        # プロジェクトを作成
        original_project = FractalProject(
            name="Save Load Test",
            description="Test project for save/load",
            fractal_type="Mandelbrot",
            author="Test Author"
        )
        
        # プロジェクトを保存
        success = self.manager.save_project(original_project)
        self.assertTrue(success)
        
        # ファイルが作成されているか確認
        project_files = list(Path(self.temp_dir).glob("*.fractal"))
        self.assertEqual(len(project_files), 1)
        
        # プロジェクトを読み込み
        loaded_project = self.manager.load_project(str(project_files[0]))
        self.assertIsNotNone(loaded_project)
        
        # 内容が正しく保存・読み込みされているか確認
        self.assertEqual(loaded_project.name, "Save Load Test")
        self.assertEqual(loaded_project.description, "Test project for save/load")
        self.assertEqual(loaded_project.fractal_type, "Mandelbrot")
        self.assertEqual(loaded_project.author, "Test Author")
    
    def test_save_project_with_custom_path(self):
        """カスタムパスでのプロジェクト保存をテスト"""
        project = FractalProject(name="Custom Path Test")
        custom_path = os.path.join(self.temp_dir, "custom_project.fractal")
        
        success = self.manager.save_project(project, custom_path)
        self.assertTrue(success)
        self.assertTrue(os.path.exists(custom_path))
        
        # ファイルパスが正しく設定されているか確認
        self.assertEqual(project.file_path, custom_path)
    
    def test_load_nonexistent_project(self):
        """存在しないプロジェクトの読み込みをテスト"""
        nonexistent_path = os.path.join(self.temp_dir, "nonexistent.fractal")
        
        project = self.manager.load_project(nonexistent_path)
        self.assertIsNone(project)
    
    def test_load_invalid_project_file(self):
        """無効なプロジェクトファイルの読み込みをテスト"""
        invalid_file = os.path.join(self.temp_dir, "invalid.fractal")
        
        # 無効なJSONファイルを作成
        with open(invalid_file, 'w') as f:
            f.write("invalid json content {")
        
        project = self.manager.load_project(invalid_file)
        self.assertIsNone(project)
    
    def test_list_projects(self):
        """プロジェクトリストの取得をテスト"""
        # 複数のプロジェクトを作成・保存
        projects = [
            FractalProject(name="Project 1", fractal_type="Mandelbrot"),
            FractalProject(name="Project 2", fractal_type="Julia"),
            FractalProject(name="Project 3", fractal_type="Custom")
        ]
        
        for project in projects:
            self.manager.save_project(project)
        
        # プロジェクトリストを取得
        project_list = self.manager.list_projects()
        
        self.assertEqual(len(project_list), 3)
        
        # プロジェクト情報が正しく含まれているか確認
        project_names = [p["name"] for p in project_list]
        self.assertIn("Project 1", project_names)
        self.assertIn("Project 2", project_names)
        self.assertIn("Project 3", project_names)
        
        # 各プロジェクト情報に必要なフィールドが含まれているか確認
        for project_info in project_list:
            self.assertIn("name", project_info)
            self.assertIn("description", project_info)
            self.assertIn("fractal_type", project_info)
            self.assertIn("last_modified", project_info)
            self.assertIn("file_path", project_info)
            self.assertIn("file_size", project_info)
    
    def test_delete_project(self):
        """プロジェクトの削除をテスト"""
        # プロジェクトを作成・保存
        project = FractalProject(name="Delete Test")
        self.manager.save_project(project)
        
        # ファイルが作成されているか確認
        project_files = list(Path(self.temp_dir).glob("*.fractal"))
        self.assertEqual(len(project_files), 1)
        file_path = str(project_files[0])
        
        # プロジェクトを削除
        success = self.manager.delete_project(file_path)
        self.assertTrue(success)
        
        # ファイルが削除されているか確認
        self.assertFalse(os.path.exists(file_path))
    
    def test_recent_projects_management(self):
        """最近使用したプロジェクトの管理をテスト"""
        # 複数のプロジェクトを作成・保存
        projects = []
        for i in range(3):
            project = FractalProject(name=f"Recent Project {i+1}")
            self.manager.save_project(project)
            projects.append(project.file_path)
        
        # 最近使用したプロジェクトリストを取得
        recent_projects = self.manager.get_recent_projects()
        
        # 保存した順序と逆順（最新が先頭）になっているか確認
        self.assertEqual(len(recent_projects), 3)
        self.assertEqual(recent_projects[0], projects[2])  # 最後に保存したものが先頭
        self.assertEqual(recent_projects[1], projects[1])
        self.assertEqual(recent_projects[2], projects[0])
    
    def test_backup_project(self):
        """プロジェクトのバックアップをテスト"""
        project = FractalProject(
            name="Backup Test",
            description="Test project for backup"
        )
        
        # バックアップを作成
        success = self.manager.backup_project(project)
        self.assertTrue(success)
        
        # バックアップディレクトリが作成されているか確認
        backup_dir = Path(self.temp_dir).parent / "backups"
        self.assertTrue(backup_dir.exists())
        
        # バックアップファイルが作成されているか確認
        backup_files = list(backup_dir.glob("*.backup"))
        self.assertGreater(len(backup_files), 0)
    
    def test_save_invalid_project(self):
        """無効なプロジェクトの保存をテスト"""
        # 無効なプロジェクト（空の名前）
        invalid_project = FractalProject(name="")
        
        success = self.manager.save_project(invalid_project)
        self.assertFalse(success)
        
        # ファイルが作成されていないか確認
        project_files = list(Path(self.temp_dir).glob("*.fractal"))
        self.assertEqual(len(project_files), 0)


if __name__ == '__main__':
    # テストの実行
    unittest.main(verbosity=2)