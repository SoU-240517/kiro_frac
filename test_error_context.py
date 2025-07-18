"""
エラーコンテキストシステムのテスト
"""
import unittest
from fractal_editor.services.error_context import (
    ErrorContext,
    handle_fractal_errors,
    handle_formula_errors,
    handle_plugin_errors,
    handle_ui_errors,
    safe_execute,
    ErrorRecovery
)
from fractal_editor.services.error_handling import (
    FractalCalculationException,
    FormulaValidationError,
    PluginLoadError,
    UIError
)
from fractal_editor.models.data_models import (
    FractalParameters,
    ComplexRegion,
    ComplexNumber
)


class TestErrorContext(unittest.TestCase):
    """エラーコンテキストのテストクラス"""
    
    def setUp(self):
        """テスト前の準備"""
        self.error_context = ErrorContext()
        self.error_context.error_service.clear_error_history()
    
    def test_fractal_calculation_context(self):
        """フラクタル計算コンテキストのテスト"""
        parameters = FractalParameters(
            region=ComplexRegion(
                top_left=ComplexNumber(-2.0, 1.0),
                bottom_right=ComplexNumber(1.0, -1.0)
            ),
            max_iterations=100,
            image_size=(800, 600),
            custom_parameters={}
        )
        
        # 一般的な例外がFractalCalculationExceptionに変換されることをテスト
        with self.assertRaises(ValueError):  # 元の例外が再発生される
            with self.error_context.fractal_calculation(parameters, "test_stage"):
                raise ValueError("テスト用エラー")
        
        stats = self.error_context.error_service.get_error_statistics()
        self.assertEqual(stats['total_errors'], 1)
        self.assertIn('FractalCalculation', stats['error_types'])
    
    def test_formula_processing_context(self):
        """数式処理コンテキストのテスト"""
        with self.assertRaises(FormulaValidationError):
            with self.error_context.formula_processing():
                raise FormulaValidationError("無効な数式")
        
        stats = self.error_context.error_service.get_error_statistics()
        self.assertEqual(stats['total_errors'], 1)
        self.assertIn('FormulaValidation', stats['error_types'])
    
    def test_plugin_operation_context(self):
        """プラグイン操作コンテキストのテスト"""
        with self.assertRaises(PluginLoadError):
            with self.error_context.plugin_operation("TestPlugin", "/path/to/plugin"):
                raise ValueError("プラグインエラー")
        
        stats = self.error_context.error_service.get_error_statistics()
        self.assertEqual(stats['total_errors'], 1)
        self.assertIn('PluginLoad', stats['error_types'])
    
    def test_ui_operation_context(self):
        """UI操作コンテキストのテスト"""
        with self.assertRaises(UIError):
            with self.error_context.ui_operation("TestWidget"):
                raise ValueError("UIエラー")
        
        stats = self.error_context.error_service.get_error_statistics()
        self.assertEqual(stats['total_errors'], 1)
        self.assertIn('UI', stats['error_types'])


class TestErrorDecorators(unittest.TestCase):
    """エラーハンドリングデコレータのテストクラス"""
    
    def setUp(self):
        """テスト前の準備"""
        from fractal_editor.services.error_context import error_context
        error_context.error_service.clear_error_history()
    
    def test_handle_formula_errors_decorator(self):
        """数式エラーハンドリングデコレータのテスト"""
        @handle_formula_errors
        def test_formula_function():
            raise FormulaValidationError("デコレータテスト用エラー")
        
        with self.assertRaises(FormulaValidationError):
            test_formula_function()
    
    def test_handle_plugin_errors_decorator(self):
        """プラグインエラーハンドリングデコレータのテスト"""
        @handle_plugin_errors("TestPlugin", "/test/path")
        def test_plugin_function():
            raise ValueError("プラグインテスト用エラー")
        
        with self.assertRaises(PluginLoadError):
            test_plugin_function()
    
    def test_handle_ui_errors_decorator(self):
        """UIエラーハンドリングデコレータのテスト"""
        @handle_ui_errors("TestComponent")
        def test_ui_function():
            raise ValueError("UIテスト用エラー")
        
        with self.assertRaises(UIError):
            test_ui_function()


class TestSafeExecute(unittest.TestCase):
    """safe_execute関数のテストクラス"""
    
    def test_safe_execute_success(self):
        """safe_execute成功ケースのテスト"""
        def success_function():
            return "成功"
        
        result = safe_execute(success_function, context="テスト")
        self.assertEqual(result, "成功")
    
    def test_safe_execute_failure_with_default(self):
        """safe_execute失敗時のデフォルト値返却テスト"""
        def failure_function():
            raise ValueError("エラー")
        
        result = safe_execute(failure_function, default_return="デフォルト", context="テスト")
        self.assertEqual(result, "デフォルト")
    
    def test_safe_execute_failure_with_none_default(self):
        """safe_execute失敗時のNoneデフォルト値テスト"""
        def failure_function():
            raise ValueError("エラー")
        
        result = safe_execute(failure_function, context="テスト")
        self.assertIsNone(result)


class TestErrorRecovery(unittest.TestCase):
    """エラー回復機能のテストクラス"""
    
    def setUp(self):
        """テスト前の準備"""
        self.error_recovery = ErrorRecovery()
        self.error_recovery.error_service.clear_error_history()
    
    def test_retry_with_fallback_success_on_first_try(self):
        """最初の試行で成功するケースのテスト"""
        def primary_func():
            return "プライマリ成功"
        
        def fallback_func():
            return "フォールバック"
        
        result = self.error_recovery.retry_with_fallback(
            primary_func, fallback_func, context="テスト"
        )
        self.assertEqual(result, "プライマリ成功")
    
    def test_retry_with_fallback_success_on_retry(self):
        """リトライで成功するケースのテスト"""
        self.attempt_count = 0
        
        def primary_func():
            self.attempt_count += 1
            if self.attempt_count < 2:
                raise ValueError("一時的なエラー")
            return "プライマリ成功"
        
        def fallback_func():
            return "フォールバック"
        
        result = self.error_recovery.retry_with_fallback(
            primary_func, fallback_func, max_retries=3, context="テスト"
        )
        self.assertEqual(result, "プライマリ成功")
        self.assertEqual(self.attempt_count, 2)
    
    def test_retry_with_fallback_uses_fallback(self):
        """フォールバック関数が使用されるケースのテスト"""
        def primary_func():
            raise ValueError("プライマリエラー")
        
        def fallback_func():
            return "フォールバック成功"
        
        result = self.error_recovery.retry_with_fallback(
            primary_func, fallback_func, max_retries=2, context="テスト"
        )
        self.assertEqual(result, "フォールバック成功")
    
    def test_graceful_degradation_high_quality_success(self):
        """高品質処理が成功するケースのテスト"""
        def high_quality():
            return "高品質結果"
        
        def medium_quality():
            return "中品質結果"
        
        def low_quality():
            return "低品質結果"
        
        result = self.error_recovery.graceful_degradation(
            high_quality, medium_quality, low_quality, context="テスト"
        )
        self.assertEqual(result, "高品質結果")
    
    def test_graceful_degradation_medium_quality_success(self):
        """中品質処理が成功するケースのテスト"""
        def high_quality():
            raise ValueError("高品質エラー")
        
        def medium_quality():
            return "中品質結果"
        
        def low_quality():
            return "低品質結果"
        
        result = self.error_recovery.graceful_degradation(
            high_quality, medium_quality, low_quality, context="テスト"
        )
        self.assertEqual(result, "中品質結果")
    
    def test_graceful_degradation_low_quality_success(self):
        """低品質処理が成功するケースのテスト"""
        def high_quality():
            raise ValueError("高品質エラー")
        
        def medium_quality():
            raise ValueError("中品質エラー")
        
        def low_quality():
            return "低品質結果"
        
        result = self.error_recovery.graceful_degradation(
            high_quality, medium_quality, low_quality, context="テスト"
        )
        self.assertEqual(result, "低品質結果")
    
    def test_graceful_degradation_all_fail(self):
        """全ての品質レベルが失敗するケースのテスト"""
        def high_quality():
            raise ValueError("高品質エラー")
        
        def medium_quality():
            raise ValueError("中品質エラー")
        
        def low_quality():
            raise ValueError("低品質エラー")
        
        with self.assertRaises(ValueError):
            self.error_recovery.graceful_degradation(
                high_quality, medium_quality, low_quality, context="テスト"
            )


if __name__ == '__main__':
    unittest.main()