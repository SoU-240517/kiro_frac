"""
プロジェクトマネージャーのテスト

このテストファイルは、FractalProjectクラスとProjectManagerクラスの
保存・読み込み機能、最近使用したプロジェクトの管理機能をテストします。
"""

import unittest
import tempfile
import os
import json
from datetime import datetime
from pathlib import Path

from fractal_editor.models.data_models import (
    FractalProject, FractalParameters, ColorPalette, ComplexRegion,
    ComplexNumber, ColorStop, InterpolationMode
)
from fractal_editor.services.project_manager import (
    ProjectManager, ProjectFileError, create_default_project
)


class TestProjectManager(unittest.TestCase):
    """プロジェクトマネージャーのテストクラス"""
    
    def setUp(self):
        """テスト前の準備"""
        # 一時ディレクトリを作成
        self.temp_dir = tempfile.mkdtemp()
        self.project_manager = ProjectManager(self.temp_dir)
        
        # テスト用プロジェクトを作成
        self.test_project = self._create_test_project()
    
    def tearDown(self):
        """テスト後のクリーンアップ"""
        # 一時ディレクトリを削除
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def _create_test_project(self) -> FractalProject:
        """テスト用のプロジェクトを作成"""
        region = ComplexRegion(
            top_left=ComplexNumber(-2.0, 1.0),
            bottom_right=ComplexNumber(1.0, -1.0)
        )
        
        parameters = FractalParameters(
            region=region,
            max_iterations=500,
            image_size=(400, 300),
            custom_parameters={'test_param': 'test_value'}
        )
        
        color_palette = ColorPalette(
            name="Test Palette",
            color_stops=[
                ColorStop(0.0, (0, 0, 0)),
                ColorStop(0.5, (255, 0, 0)),
                ColorStop(1.0, (255, 255, 255))
            ],
            interpolation_mode=InterpolationMode.LINEAR
        )
        
        return FractalProject(
            name="テストプロジェクト",
            fractal_type="mandelbrot",
            parameters=parameters,
            color_palette=color_palette
        )
    
    def test_save_project_creates_file(self):
        """プロジェクト保存でファイルが作成されることをテスト"""
        file_path = os.path.join(self.temp_dir, "test_project")
        
        # プロジェクトを保存
        self.project_manager.save_project(self.test_project, file_path)
        
        # ファイルが作成されることを確認
        expected_path = file_path + ".fractal"
        self.assertTrue(os.path.exists(expected_path))
        
        # プロジェクトのfile_pathが更新されることを確認
        self.assertEqual(self.test_project.file_path, expected_path)
    
    def test_save_project_creates_valid_json(self):
        """保存されたファイルが有効なJSONであることをテスト"""
        file_path = os.path.join(self.temp_dir, "test_project")
        
        # プロジェクトを保存
        self.project_manager.save_project(self.test_project, file_path)
        
        # JSONファイルを読み込んで検証
        with open(file_path + ".fractal", 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 基本構造を確認
        self.assertIn('version', data)
        self.assertIn('metadata', data)
        self.assertIn('project', data)
        
        # プロジェクトデータを確認
        project_data = data['project']
        self.assertEqual(project_data['name'], "テストプロジェクト")
        self.assertEqual(project_data['fractal_type'], "mandelbrot")
        self.assertIn('parameters', project_data)
        self.assertIn('color_palette', project_data)
    
    def test_load_project_restores_data(self):
        """プロジェクト読み込みでデータが正しく復元されることをテスト"""
        file_path = os.path.join(self.temp_dir, "test_project")
        
        # プロジェクトを保存
        self.project_manager.save_project(self.test_project, file_path)
        
        # プロジェクトを読み込み
        loaded_project = self.project_manager.load_project(file_path + ".fractal")
        
        # データが正しく復元されることを確認
        self.assertEqual(loaded_project.name, self.test_project.name)
        self.assertEqual(loaded_project.fractal_type, self.test_project.fractal_type)
        
        # パラメータの確認
        self.assertEqual(loaded_project.parameters.max_iterations, 500)
        self.assertEqual(loaded_project.parameters.image_size, (400, 300))
        self.assertEqual(loaded_project.parameters.custom_parameters['test_param'], 'test_value')
        
        # 複素領域の確認
        self.assertEqual(loaded_project.parameters.region.top_left.real, -2.0)
        self.assertEqual(loaded_project.parameters.region.top_left.imaginary, 1.0)
        
        # カラーパレットの確認
        self.assertEqual(loaded_project.color_palette.name, "Test Palette")
        self.assertEqual(len(loaded_project.color_palette.color_stops), 3)
        self.assertEqual(loaded_project.color_palette.color_stops[0].color, (0, 0, 0))
    
    def test_load_nonexistent_file_raises_error(self):
        """存在しないファイルの読み込みでエラーが発生することをテスト"""
        nonexistent_path = os.path.join(self.temp_dir, "nonexistent.fractal")
        
        with self.assertRaises(ProjectFileError):
            self.project_manager.load_project(nonexistent_path)
    
    def test_load_invalid_json_raises_error(self):
        """無効なJSONファイルの読み込みでエラーが発生することをテスト"""
        invalid_file = os.path.join(self.temp_dir, "invalid.fractal")
        
        # 無効なJSONファイルを作成
        with open(invalid_file, 'w') as f:
            f.write("invalid json content")
        
        with self.assertRaises(ProjectFileError):
            self.project_manager.load_project(invalid_file)
    
    def test_recent_projects_management(self):
        """最近使用したプロジェクトの管理機能をテスト"""
        file_path1 = os.path.join(self.temp_dir, "project1")
        file_path2 = os.path.join(self.temp_dir, "project2")
        
        # 初期状態では空のリスト
        self.assertEqual(len(self.project_manager.get_recent_projects()), 0)
        
        # プロジェクトを保存
        self.project_manager.save_project(self.test_project, file_path1)
        
        # 最近使用したプロジェクトリストに追加されることを確認
        recent_projects = self.project_manager.get_recent_projects()
        self.assertEqual(len(recent_projects), 1)
        self.assertEqual(recent_projects[0]['name'], "テストプロジェクト")
        self.assertTrue(recent_projects[0]['file_path'].endswith("project1.fractal"))
        
        # 別のプロジェクトを保存
        project2 = self._create_test_project()
        project2.name = "テストプロジェクト2"
        self.project_manager.save_project(project2, file_path2)
        
        # リストが更新されることを確認
        recent_projects = self.project_manager.get_recent_projects()
        self.assertEqual(len(recent_projects), 2)
        # 最新のプロジェクトが先頭に来ることを確認
        self.assertEqual(recent_projects[0]['name'], "テストプロジェクト2")
    
    def test_remove_from_recent_projects(self):
        """最近使用したプロジェクトからの削除機能をテスト"""
        file_path = os.path.join(self.temp_dir, "project_to_remove")
        
        # プロジェクトを保存
        self.project_manager.save_project(self.test_project, file_path)
        
        # リストに追加されることを確認
        self.assertEqual(len(self.project_manager.get_recent_projects()), 1)
        
        # リストから削除
        self.project_manager.remove_from_recent_projects(file_path + ".fractal")
        
        # リストが空になることを確認
        self.assertEqual(len(self.project_manager.get_recent_projects()), 0)
    
    def test_clear_recent_projects(self):
        """最近使用したプロジェクトリストのクリア機能をテスト"""
        file_path = os.path.join(self.temp_dir, "project_to_clear")
        
        # プロジェクトを保存
        self.project_manager.save_project(self.test_project, file_path)
        
        # リストに追加されることを確認
        self.assertEqual(len(self.project_manager.get_recent_projects()), 1)
        
        # リストをクリア
        self.project_manager.clear_recent_projects()
        
        # リストが空になることを確認
        self.assertEqual(len(self.project_manager.get_recent_projects()), 0)


class TestFractalProject(unittest.TestCase):
    """FractalProjectクラスのテストクラス"""
    
    def setUp(self):
        """テスト前の準備"""
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """テスト後のクリーンアップ"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_save_to_file_method(self):
        """FractalProject.save_to_fileメソッドのテスト"""
        project = create_default_project("テスト保存プロジェクト")
        file_path = os.path.join(self.temp_dir, "test_save")
        
        # save_to_fileメソッドを呼び出し
        project.save_to_file(file_path)
        
        # ファイルが作成されることを確認
        self.assertTrue(os.path.exists(file_path + ".fractal"))
        
        # プロジェクトのfile_pathが更新されることを確認
        self.assertEqual(project.file_path, file_path + ".fractal")
    
    def test_load_from_file_method(self):
        """FractalProject.load_from_fileメソッドのテスト"""
        # まずプロジェクトを保存
        original_project = create_default_project("テスト読み込みプロジェクト")
        file_path = os.path.join(self.temp_dir, "test_load")
        original_project.save_to_file(file_path)
        
        # load_from_fileメソッドを呼び出し
        loaded_project = FractalProject.load_from_file(file_path + ".fractal")
        
        # データが正しく読み込まれることを確認
        self.assertEqual(loaded_project.name, "テスト読み込みプロジェクト")
        self.assertEqual(loaded_project.fractal_type, "mandelbrot")
        self.assertEqual(loaded_project.file_path, file_path + ".fractal")


class TestCreateDefaultProject(unittest.TestCase):
    """create_default_project関数のテストクラス"""
    
    def test_create_default_project_returns_valid_project(self):
        """デフォルトプロジェクト作成で有効なプロジェクトが返されることをテスト"""
        project = create_default_project("デフォルトテスト")
        
        # 基本プロパティの確認
        self.assertEqual(project.name, "デフォルトテスト")
        self.assertEqual(project.fractal_type, "mandelbrot")
        
        # パラメータの確認
        self.assertEqual(project.parameters.max_iterations, 1000)
        self.assertEqual(project.parameters.image_size, (800, 600))
        
        # 複素領域の確認（マンデルブロ集合の標準表示範囲）
        self.assertEqual(project.parameters.region.top_left.real, -2.5)
        self.assertEqual(project.parameters.region.top_left.imaginary, 1.5)
        self.assertEqual(project.parameters.region.bottom_right.real, 1.5)
        self.assertEqual(project.parameters.region.bottom_right.imaginary, -1.5)
        
        # カラーパレットの確認
        self.assertEqual(project.color_palette.name, "Rainbow")
        self.assertEqual(len(project.color_palette.color_stops), 7)
        self.assertEqual(project.color_palette.interpolation_mode, InterpolationMode.LINEAR)
    
    def test_create_default_project_with_default_name(self):
        """デフォルト名でプロジェクト作成をテスト"""
        project = create_default_project()
        
        self.assertEqual(project.name, "新しいプロジェクト")


if __name__ == '__main__':
    unittest.main()