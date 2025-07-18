"""
拡張テンプレートマネージャーのテスト

プリセット式テンプレートのライブラリとユーザーカスタム式の
保存・読み込み機能をテストします。
"""

import sys
import unittest
import tempfile
import shutil
from pathlib import Path
from PyQt6.QtWidgets import QApplication

from fractal_editor.services.template_manager import (
    EnhancedTemplateManager, CustomTemplate, TemplateStorage
)
from fractal_editor.services.formula_parser import FormulaTemplate, FormulaValidationError


class TestTemplateStorage(unittest.TestCase):
    """テンプレートストレージのテストクラス"""
    
    def setUp(self):
        """各テストの前処理"""
        # 一時ディレクトリを作成
        self.temp_dir = tempfile.mkdtemp()
        self.storage = TemplateStorage(self.temp_dir)
    
    def tearDown(self):
        """各テストの後処理"""
        # 一時ディレクトリを削除
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_storage_initialization(self):
        """ストレージの初期化テスト"""
        self.assertTrue(self.storage.storage_dir.exists())
        self.assertEqual(str(self.storage.storage_dir), self.temp_dir)
    
    def test_save_and_load_custom_templates(self):
        """カスタムテンプレートの保存・読み込みテスト"""
        # テストテンプレートを作成
        template1 = CustomTemplate(
            name="Test Template 1",
            formula="z**2 + c",
            description="Test description 1",
            author="Test Author"
        )
        
        template2 = CustomTemplate(
            name="Test Template 2",
            formula="z**3 + c",
            description="Test description 2",
            author="Test Author",
            tags=["test", "cubic"]
        )
        
        templates = {
            template1.name: template1,
            template2.name: template2
        }
        
        # 保存
        success = self.storage.save_custom_templates(templates)
        self.assertTrue(success)
        
        # 読み込み
        loaded_templates = self.storage.load_custom_templates()
        
        # 検証
        self.assertEqual(len(loaded_templates), 2)
        self.assertIn("Test Template 1", loaded_templates)
        self.assertIn("Test Template 2", loaded_templates)
        
        loaded_template1 = loaded_templates["Test Template 1"]
        self.assertEqual(loaded_template1.formula, "z**2 + c")
        self.assertEqual(loaded_template1.author, "Test Author")
        
        loaded_template2 = loaded_templates["Test Template 2"]
        self.assertEqual(loaded_template2.tags, ["test", "cubic"])
    
    def test_settings_save_and_load(self):
        """設定の保存・読み込みテスト"""
        # カスタム設定
        custom_settings = {
            "default_author": "Test User",
            "max_backups": 10,
            "sort_order": "date"
        }
        
        # 保存
        success = self.storage.save_settings(custom_settings)
        self.assertTrue(success)
        
        # 読み込み
        loaded_settings = self.storage.load_settings()
        
        # 検証（デフォルト設定とマージされる）
        self.assertEqual(loaded_settings["default_author"], "Test User")
        self.assertEqual(loaded_settings["max_backups"], 10)
        self.assertEqual(loaded_settings["sort_order"], "date")
        self.assertIn("auto_backup", loaded_settings)  # デフォルト設定も含まれる
    
    def test_template_export_import(self):
        """テンプレートのエクスポート・インポートテスト"""
        # テストテンプレートを作成
        template = CustomTemplate(
            name="Export Test",
            formula="sin(z) + c",
            description="Export test template",
            author="Export Tester",
            tags=["export", "test"]
        )
        
        # エクスポート
        export_file = Path(self.temp_dir) / "exported_template.json"
        success = self.storage.export_template(template, str(export_file))
        self.assertTrue(success)
        self.assertTrue(export_file.exists())
        
        # インポート
        imported_template = self.storage.import_template(str(export_file))
        self.assertIsNotNone(imported_template)
        
        # 検証
        self.assertEqual(imported_template.name, template.name)
        self.assertEqual(imported_template.formula, template.formula)
        self.assertEqual(imported_template.description, template.description)
        self.assertEqual(imported_template.author, template.author)
        self.assertEqual(imported_template.tags, template.tags)


class TestCustomTemplate(unittest.TestCase):
    """カスタムテンプレートのテストクラス"""
    
    def test_custom_template_creation(self):
        """カスタムテンプレートの作成テスト"""
        template = CustomTemplate(
            name="Test Template",
            formula="z**2 + c",
            description="Test description",
            author="Test Author",
            tags=["test", "mandelbrot"]
        )
        
        self.assertEqual(template.name, "Test Template")
        self.assertEqual(template.formula, "z**2 + c")
        self.assertEqual(template.description, "Test description")
        self.assertEqual(template.author, "Test Author")
        self.assertEqual(template.tags, ["test", "mandelbrot"])
        self.assertIsNotNone(template.created_date)
        self.assertIsNotNone(template.modified_date)
    
    def test_to_formula_template_conversion(self):
        """FormulaTemplateへの変換テスト"""
        custom_template = CustomTemplate(
            name="Conversion Test",
            formula="z**3 + c",
            description="Conversion test template",
            example_params={"max_iterations": 100}
        )
        
        formula_template = custom_template.to_formula_template()
        
        self.assertIsInstance(formula_template, FormulaTemplate)
        self.assertEqual(formula_template.name, custom_template.name)
        self.assertEqual(formula_template.formula, custom_template.formula)
        self.assertEqual(formula_template.description, custom_template.description)
        self.assertEqual(formula_template.example_params, custom_template.example_params)
    
    def test_from_formula_template_conversion(self):
        """FormulaTemplateからの変換テスト"""
        formula_template = FormulaTemplate(
            name="Original Template",
            formula="exp(z) + c",
            description="Original description",
            example_params={"max_iterations": 50}
        )
        
        custom_template = CustomTemplate.from_formula_template(
            formula_template, 
            author="Converter"
        )
        
        self.assertEqual(custom_template.name, formula_template.name)
        self.assertEqual(custom_template.formula, formula_template.formula)
        self.assertEqual(custom_template.description, formula_template.description)
        self.assertEqual(custom_template.example_params, formula_template.example_params)
        self.assertEqual(custom_template.author, "Converter")


class TestEnhancedTemplateManager(unittest.TestCase):
    """拡張テンプレートマネージャーのテストクラス"""
    
    def setUp(self):
        """各テストの前処理"""
        # 一時ディレクトリを作成
        self.temp_dir = tempfile.mkdtemp()
        self.manager = EnhancedTemplateManager(self.temp_dir)
    
    def tearDown(self):
        """各テストの後処理"""
        # 一時ディレクトリを削除
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_manager_initialization(self):
        """マネージャーの初期化テスト"""
        self.assertIsNotNone(self.manager.builtin_templates)
        self.assertGreater(len(self.manager.builtin_templates), 0)
        self.assertIsInstance(self.manager.custom_templates, dict)
        self.assertIsInstance(self.manager.settings, dict)
    
    def test_builtin_template_access(self):
        """組み込みテンプレートのアクセステスト"""
        template_names = self.manager.list_templates(include_custom=False)
        self.assertGreater(len(template_names), 0)
        
        # 最初のテンプレートを取得
        first_template_name = template_names[0]
        template = self.manager.get_template(first_template_name)
        
        self.assertIsInstance(template, FormulaTemplate)
        self.assertEqual(template.name, first_template_name)
        self.assertIsNotNone(template.formula)
        self.assertIsNotNone(template.description)
    
    def test_custom_template_management(self):
        """カスタムテンプレート管理テスト"""
        # カスタムテンプレートを追加
        success = self.manager.create_template_from_formula(
            name="Custom Test",
            formula="z**4 + c",
            description="Custom test template",
            author="Test User",
            tags=["custom", "test"]
        )
        self.assertTrue(success)
        
        # テンプレートが追加されたことを確認
        template_names = self.manager.list_templates(include_builtin=False)
        self.assertIn("Custom Test", template_names)
        
        # テンプレートを取得
        template = self.manager.get_template("Custom Test")
        self.assertEqual(template.formula, "z**4 + c")
        self.assertEqual(template.description, "Custom test template")
        
        # テンプレート情報を取得
        info = self.manager.get_template_info("Custom Test")
        self.assertEqual(info["type"], "custom")
        self.assertEqual(info["author"], "Test User")
        self.assertEqual(info["tags"], ["custom", "test"])
        
        # テンプレートを削除
        success = self.manager.remove_custom_template("Custom Test")
        self.assertTrue(success)
        
        # 削除されたことを確認
        template_names = self.manager.list_templates(include_builtin=False)
        self.assertNotIn("Custom Test", template_names)
    
    def test_template_search(self):
        """テンプレート検索テスト"""
        # カスタムテンプレートを追加
        self.manager.create_template_from_formula(
            name="Search Test 1",
            formula="sin(z) + c",
            description="Sine fractal for search test",
            tags=["trigonometric", "search"]
        )
        
        self.manager.create_template_from_formula(
            name="Search Test 2",
            formula="cos(z) + c",
            description="Cosine fractal for search test",
            tags=["trigonometric", "search"]
        )
        
        # 名前で検索
        results = self.manager.search_templates("Search Test")
        self.assertEqual(len(results), 2)
        
        # 説明で検索
        results = self.manager.search_templates("sine")
        self.assertGreater(len(results), 0)
        
        # 数式で検索
        results = self.manager.search_templates("sin(z)")
        self.assertGreater(len(results), 0)
        
        # タグで検索
        tag_results = self.manager.get_templates_by_tag("trigonometric")
        self.assertEqual(len(tag_results), 2)
    
    def test_invalid_formula_handling(self):
        """無効な数式の処理テスト"""
        # 無効な数式でテンプレート作成を試行
        success = self.manager.create_template_from_formula(
            name="Invalid Test",
            formula="invalid_function(z) + unknown_var",
            description="This should fail"
        )
        self.assertFalse(success)
        
        # テンプレートが作成されていないことを確認
        template_names = self.manager.list_templates(include_builtin=False)
        self.assertNotIn("Invalid Test", template_names)
    
    def test_template_export_import(self):
        """テンプレートのエクスポート・インポートテスト"""
        # カスタムテンプレートを作成
        self.manager.create_template_from_formula(
            name="Export Import Test",
            formula="z**5 + c",
            description="Export import test template",
            author="Export Tester"
        )
        
        # エクスポート
        export_file = Path(self.temp_dir) / "test_export.json"
        success = self.manager.export_template("Export Import Test", str(export_file))
        self.assertTrue(success)
        self.assertTrue(export_file.exists())
        
        # テンプレートを削除
        self.manager.remove_custom_template("Export Import Test")
        
        # インポート
        success = self.manager.import_template(str(export_file))
        self.assertTrue(success)
        
        # インポートされたことを確認
        template_names = self.manager.list_templates(include_builtin=False)
        self.assertIn("Export Import Test", template_names)
        
        template = self.manager.get_template("Export Import Test")
        self.assertEqual(template.formula, "z**5 + c")
    
    def test_settings_management(self):
        """設定管理テスト"""
        # 設定を取得
        settings = self.manager.get_settings()
        self.assertIsInstance(settings, dict)
        self.assertIn("default_author", settings)
        
        # 設定を更新
        new_settings = {"default_author": "New Author", "sort_order": "date"}
        success = self.manager.update_settings(new_settings)
        self.assertTrue(success)
        
        # 更新された設定を確認
        updated_settings = self.manager.get_settings()
        self.assertEqual(updated_settings["default_author"], "New Author")
        self.assertEqual(updated_settings["sort_order"], "date")
    
    def test_statistics(self):
        """統計情報テスト"""
        # 初期統計
        stats = self.manager.get_statistics()
        self.assertIsInstance(stats, dict)
        self.assertIn("builtin_count", stats)
        self.assertIn("custom_count", stats)
        self.assertIn("total_count", stats)
        
        initial_custom_count = stats["custom_count"]
        
        # カスタムテンプレートを追加
        self.manager.create_template_from_formula(
            name="Stats Test",
            formula="z**6 + c",
            description="Statistics test template"
        )
        
        # 統計を再取得
        updated_stats = self.manager.get_statistics()
        self.assertEqual(updated_stats["custom_count"], initial_custom_count + 1)
        self.assertEqual(
            updated_stats["total_count"], 
            updated_stats["builtin_count"] + updated_stats["custom_count"]
        )


def run_template_manager_tests():
    """テンプレートマネージャーのテストを実行"""
    # テストスイートを作成
    loader = unittest.TestLoader()
    test_suite = unittest.TestSuite()
    
    # テストケースを追加
    test_suite.addTests(loader.loadTestsFromTestCase(TestTemplateStorage))
    test_suite.addTests(loader.loadTestsFromTestCase(TestCustomTemplate))
    test_suite.addTests(loader.loadTestsFromTestCase(TestEnhancedTemplateManager))
    
    # テストランナーを作成して実行
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    try:
        # テストを実行
        success = run_template_manager_tests()
        
        if success:
            print("\n✅ 全てのテンプレートマネージャーテストが成功しました！")
            
            # 簡単なデモも実行
            print("\n🎨 テンプレートマネージャーのデモを実行します...")
            
            # 一時ディレクトリでデモ
            with tempfile.TemporaryDirectory() as temp_dir:
                demo_manager = EnhancedTemplateManager(temp_dir)
                
                print(f"組み込みテンプレート数: {len(demo_manager.builtin_templates)}")
                
                # カスタムテンプレートを作成
                demo_manager.create_template_from_formula(
                    name="デモテンプレート",
                    formula="z**2 + c * sin(z)",
                    description="デモ用のカスタムテンプレート",
                    author="デモユーザー",
                    tags=["demo", "custom"]
                )
                
                print("カスタムテンプレートを作成しました")
                
                # 統計情報を表示
                stats = demo_manager.get_statistics()
                print(f"統計情報: {stats}")
                
                # 検索テスト
                search_results = demo_manager.search_templates("デモ")
                print(f"検索結果: {len(search_results)}件")
                
        else:
            print("\n❌ 一部のテストが失敗しました。")
            sys.exit(1)
        
    except Exception as e:
        print(f"❌ テスト実行中にエラーが発生しました: {e}")
        sys.exit(1)