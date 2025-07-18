"""
エラーハンドリングシステムのテスト
"""
import unittest
import tempfile
import os
from pathlib import Path
from fractal_editor.services.error_handling import (
    ErrorHandlingService,
    FractalCalculationException,
    FormulaValidationError,
    FormulaEvaluationError,
    PluginLoadError,
    ImageExportError,
    ProjectFileError,
    MemoryError,
    UIError
)
from fractal_editor.models.data_models import (
    FractalParameters,
    ComplexRegion,
    ComplexNumber
)


class TestErrorHandlingService(unittest.TestCase):
    """エラーハンドリングサービスのテストクラス"""
    
    def setUp(self):
        """テスト前の準備"""
        self.error_service = ErrorHandlingService()
        self.error_service.clear_error_history()
    
    def test_singleton_pattern(self):
        """シングルトンパターンのテスト"""
        service1 = ErrorHandlingService()
        service2 = ErrorHandlingService()
        self.assertIs(service1, service2)
    
    def test_fractal_calculation_error_handling(self):
        """フラクタル計算エラーハンドリングのテスト"""
        # テスト用パラメータを作成
        parameters = FractalParameters(
            region=ComplexRegion(
                top_left=ComplexNumber(-2.0, 1.0),
                bottom_right=ComplexNumber(1.0, -1.0)
            ),
            max_iterations=100,
            image_size=(800, 600),
            custom_parameters={}
        )
        
        # エラーを作成して処理
        error = FractalCalculationException("計算でオーバーフローが発生", parameters, "iteration")
        self.error_service.handle_calculation_error(error)
        
        # エラーが記録されたことを確認
        stats = self.error_service.get_error_statistics()
        self.assertEqual(stats['total_errors'], 1)
        self.assertIn('FractalCalculation', stats['error_types'])
    
    def test_formula_validation_error_handling(self):
        """数式検証エラーハンドリングのテスト"""
        error = FormulaValidationError("無効な数式です")
        self.error_service.handle_formula_error(error)
        
        stats = self.error_service.get_error_statistics()
        self.assertEqual(stats['total_errors'], 1)
        self.assertIn('FormulaValidation', stats['error_types'])
    
    def test_formula_evaluation_error_handling(self):
        """数式評価エラーハンドリングのテスト"""
        error = FormulaEvaluationError("数式の評価に失敗しました")
        self.error_service.handle_formula_error(error)
        
        stats = self.error_service.get_error_statistics()
        self.assertEqual(stats['total_errors'], 1)
        self.assertIn('FormulaEvaluation', stats['error_types'])
    
    def test_plugin_error_handling(self):
        """プラグインエラーハンドリングのテスト"""
        error = PluginLoadError("プラグインの読み込みに失敗", "TestPlugin", "/path/to/plugin")
        self.error_service.handle_plugin_error(error)
        
        stats = self.error_service.get_error_statistics()
        self.assertEqual(stats['total_errors'], 1)
        self.assertIn('PluginLoad', stats['error_types'])
    
    def test_image_export_error_handling(self):
        """画像出力エラーハンドリングのテスト"""
        error = ImageExportError("画像の保存に失敗", "/path/to/image.png", "PNG")
        self.error_service.handle_image_export_error(error)
        
        stats = self.error_service.get_error_statistics()
        self.assertEqual(stats['total_errors'], 1)
        self.assertIn('ImageExport', stats['error_types'])
    
    def test_project_file_error_handling(self):
        """プロジェクトファイルエラーハンドリングのテスト"""
        error = ProjectFileError("ファイルの読み込みに失敗", "/path/to/project.json", "load")
        self.error_service.handle_project_file_error(error)
        
        stats = self.error_service.get_error_statistics()
        self.assertEqual(stats['total_errors'], 1)
        self.assertIn('ProjectFile', stats['error_types'])
    
    def test_memory_error_handling(self):
        """メモリエラーハンドリングのテスト"""
        error = MemoryError("メモリが不足しています", 1024*1024*100)  # 100MB
        self.error_service.handle_memory_error(error)
        
        stats = self.error_service.get_error_statistics()
        self.assertEqual(stats['total_errors'], 1)
        self.assertIn('Memory', stats['error_types'])
    
    def test_ui_error_handling(self):
        """UIエラーハンドリングのテスト"""
        error = UIError("ウィジェットの初期化に失敗", "FractalWidget")
        self.error_service.handle_ui_error(error)
        
        stats = self.error_service.get_error_statistics()
        self.assertEqual(stats['total_errors'], 1)
        self.assertIn('UI', stats['error_types'])
    
    def test_general_error_handling(self):
        """一般エラーハンドリングのテスト"""
        error = ValueError("一般的なエラー")
        self.error_service.handle_general_error(error, "テストコンテキスト")
        
        stats = self.error_service.get_error_statistics()
        self.assertEqual(stats['total_errors'], 1)
        self.assertIn('General', stats['error_types'])
    
    def test_critical_error_handling(self):
        """クリティカルエラーハンドリングのテスト"""
        error = RuntimeError("クリティカルエラー")
        self.error_service.handle_critical_error(error, "システム初期化")
        
        stats = self.error_service.get_error_statistics()
        self.assertEqual(stats['total_errors'], 1)
        self.assertIn('Critical', stats['error_types'])
    
    def test_error_history_limit(self):
        """エラー履歴の制限テスト"""
        # 105個のエラーを生成（制限は100）
        for i in range(105):
            error = ValueError(f"テストエラー {i}")
            self.error_service.handle_general_error(error)
        
        stats = self.error_service.get_error_statistics()
        self.assertEqual(stats['total_errors'], 105)
        self.assertEqual(len(self.error_service.error_history), 100)  # 最新100件のみ保持
    
    def test_clear_error_history(self):
        """エラー履歴クリアのテスト"""
        # いくつかエラーを生成
        for i in range(5):
            error = ValueError(f"テストエラー {i}")
            self.error_service.handle_general_error(error)
        
        # 履歴をクリア
        self.error_service.clear_error_history()
        
        stats = self.error_service.get_error_statistics()
        self.assertEqual(stats['total_errors'], 0)
        self.assertEqual(len(self.error_service.error_history), 0)
    
    def test_export_error_log(self):
        """エラーログエクスポートのテスト"""
        # テストエラーを生成
        error = ValueError("エクスポートテスト用エラー")
        self.error_service.handle_general_error(error, "テスト")
        
        # 一時ファイルにエクスポート
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as temp_file:
            temp_path = temp_file.name
        
        try:
            result = self.error_service.export_error_log(temp_path)
            self.assertTrue(result)
            
            # ファイルが作成されたことを確認
            self.assertTrue(os.path.exists(temp_path))
            
            # ファイル内容を確認
            with open(temp_path, 'r', encoding='utf-8') as f:
                content = f.read()
                self.assertIn("フラクタルエディタ エラーレポート", content)
                self.assertIn("エクスポートテスト用エラー", content)
        
        finally:
            # 一時ファイルを削除
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    def test_multiple_error_types_statistics(self):
        """複数のエラータイプの統計テスト"""
        # 異なるタイプのエラーを生成
        self.error_service.handle_general_error(ValueError("一般エラー1"))
        self.error_service.handle_general_error(ValueError("一般エラー2"))
        self.error_service.handle_formula_error(FormulaValidationError("数式エラー"))
        self.error_service.handle_ui_error(UIError("UIエラー"))
        
        stats = self.error_service.get_error_statistics()
        self.assertEqual(stats['total_errors'], 4)
        self.assertEqual(stats['error_types']['General'], 2)
        self.assertEqual(stats['error_types']['FormulaValidation'], 1)
        self.assertEqual(stats['error_types']['UI'], 1)


class TestCustomExceptions(unittest.TestCase):
    """カスタム例外クラスのテスト"""
    
    def test_fractal_calculation_exception(self):
        """FractalCalculationExceptionのテスト"""
        parameters = FractalParameters(
            region=ComplexRegion(
                top_left=ComplexNumber(-2.0, 1.0),
                bottom_right=ComplexNumber(1.0, -1.0)
            ),
            max_iterations=100,
            image_size=(800, 600),
            custom_parameters={}
        )
        
        ex = FractalCalculationException("テストメッセージ", parameters, "calculation")
        self.assertEqual(str(ex), "テストメッセージ")
        self.assertEqual(ex.stage, "calculation")
        self.assertEqual(ex.parameters.max_iterations, 100)
    
    def test_plugin_load_error(self):
        """PluginLoadErrorのテスト"""
        ex = PluginLoadError("プラグイン読み込みエラー", "TestPlugin", "/path/to/plugin")
        self.assertEqual(str(ex), "プラグイン読み込みエラー")
        self.assertEqual(ex.plugin_name, "TestPlugin")
        self.assertEqual(ex.plugin_path, "/path/to/plugin")
    
    def test_image_export_error(self):
        """ImageExportErrorのテスト"""
        ex = ImageExportError("画像出力エラー", "/path/to/image.png", "PNG")
        self.assertEqual(str(ex), "画像出力エラー")
        self.assertEqual(ex.file_path, "/path/to/image.png")
        self.assertEqual(ex.format_type, "PNG")
    
    def test_project_file_error(self):
        """ProjectFileErrorのテスト"""
        ex = ProjectFileError("ファイルエラー", "/path/to/project.json", "save")
        self.assertEqual(str(ex), "ファイルエラー")
        self.assertEqual(ex.file_path, "/path/to/project.json")
        self.assertEqual(ex.operation, "save")
    
    def test_memory_error(self):
        """MemoryErrorのテスト"""
        ex = MemoryError("メモリ不足", 1024)
        self.assertEqual(str(ex), "メモリ不足")
        self.assertEqual(ex.requested_size, 1024)
    
    def test_ui_error(self):
        """UIErrorのテスト"""
        ex = UIError("UIエラー", "MainWindow")
        self.assertEqual(str(ex), "UIエラー")
        self.assertEqual(ex.component, "MainWindow")


if __name__ == '__main__':
    unittest.main()