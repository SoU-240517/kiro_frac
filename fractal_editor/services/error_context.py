"""
エラーハンドリングのコンテキスト管理とヘルパー関数
"""
import functools
from typing import Any, Callable, Optional, Type, Union
from contextlib import contextmanager
from .error_handling import (
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


class ErrorContext:
    """エラーハンドリングのコンテキスト管理クラス"""
    
    def __init__(self):
        self.error_service = ErrorHandlingService()
    
    @contextmanager
    def fractal_calculation(self, parameters=None, stage: str = "unknown"):
        """フラクタル計算のエラーコンテキスト"""
        try:
            yield
        except Exception as e:
            if isinstance(e, FractalCalculationException):
                self.error_service.handle_calculation_error(e)
            else:
                # 一般的な例外をフラクタル計算例外に変換
                calc_error = FractalCalculationException(str(e), parameters, stage)
                self.error_service.handle_calculation_error(calc_error)
            raise
    
    @contextmanager
    def formula_processing(self):
        """数式処理のエラーコンテキスト"""
        try:
            yield
        except (FormulaValidationError, FormulaEvaluationError) as e:
            self.error_service.handle_formula_error(e)
            raise
        except Exception as e:
            # 一般的な例外を数式エラーに変換
            formula_error = FormulaEvaluationError(f"数式処理エラー: {e}")
            self.error_service.handle_formula_error(formula_error)
            raise formula_error
    
    @contextmanager
    def plugin_operation(self, plugin_name: str = "", plugin_path: str = ""):
        """プラグイン操作のエラーコンテキスト"""
        try:
            yield
        except PluginLoadError as e:
            self.error_service.handle_plugin_error(e)
            raise
        except Exception as e:
            plugin_error = PluginLoadError(str(e), plugin_name, plugin_path)
            self.error_service.handle_plugin_error(plugin_error)
            raise plugin_error
    
    @contextmanager
    def image_export(self, file_path: str = "", format_type: str = ""):
        """画像出力のエラーコンテキスト"""
        try:
            yield
        except ImageExportError as e:
            self.error_service.handle_image_export_error(e)
            raise
        except Exception as e:
            export_error = ImageExportError(str(e), file_path, format_type)
            self.error_service.handle_image_export_error(export_error)
            raise export_error
    
    @contextmanager
    def project_file_operation(self, file_path: str = "", operation: str = ""):
        """プロジェクトファイル操作のエラーコンテキスト"""
        try:
            yield
        except ProjectFileError as e:
            self.error_service.handle_project_file_error(e)
            raise
        except Exception as e:
            file_error = ProjectFileError(str(e), file_path, operation)
            self.error_service.handle_project_file_error(file_error)
            raise file_error
    
    @contextmanager
    def memory_intensive_operation(self, requested_size: int = 0):
        """メモリ集約的操作のエラーコンテキスト"""
        try:
            yield
        except MemoryError as e:
            self.error_service.handle_memory_error(e)
            raise
        except (MemoryError, OSError) as e:
            memory_error = MemoryError(str(e), requested_size)
            self.error_service.handle_memory_error(memory_error)
            raise memory_error
    
    @contextmanager
    def ui_operation(self, component: str = ""):
        """UI操作のエラーコンテキスト"""
        try:
            yield
        except UIError as e:
            self.error_service.handle_ui_error(e)
            raise
        except Exception as e:
            ui_error = UIError(str(e), component)
            self.error_service.handle_ui_error(ui_error)
            raise ui_error
    
    @contextmanager
    def general_operation(self, context: str = ""):
        """一般的な操作のエラーコンテキスト"""
        try:
            yield
        except Exception as e:
            self.error_service.handle_general_error(e, context)
            raise


# グローバルなエラーコンテキストインスタンス
error_context = ErrorContext()


def handle_fractal_errors(parameters=None, stage: str = "unknown"):
    """フラクタル計算エラーを処理するデコレータ"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            with error_context.fractal_calculation(parameters, stage):
                return func(*args, **kwargs)
        return wrapper
    return decorator


def handle_formula_errors(func: Callable) -> Callable:
    """数式処理エラーを処理するデコレータ"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        with error_context.formula_processing():
            return func(*args, **kwargs)
    return wrapper


def handle_plugin_errors(plugin_name: str = "", plugin_path: str = ""):
    """プラグインエラーを処理するデコレータ"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            with error_context.plugin_operation(plugin_name, plugin_path):
                return func(*args, **kwargs)
        return wrapper
    return decorator


def handle_image_export_errors(file_path: str = "", format_type: str = ""):
    """画像出力エラーを処理するデコレータ"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            with error_context.image_export(file_path, format_type):
                return func(*args, **kwargs)
        return wrapper
    return decorator


def handle_ui_errors(component: str = ""):
    """UIエラーを処理するデコレータ"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            with error_context.ui_operation(component):
                return func(*args, **kwargs)
        return wrapper
    return decorator


def handle_general_errors(context: str = ""):
    """一般エラーを処理するデコレータ"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            with error_context.general_operation(context):
                return func(*args, **kwargs)
        return wrapper
    return decorator


def safe_execute(func: Callable, *args, default_return=None, context: str = "", **kwargs) -> Any:
    """安全に関数を実行し、エラーが発生した場合はデフォルト値を返す"""
    try:
        with error_context.general_operation(context):
            return func(*args, **kwargs)
    except Exception:
        return default_return


class ErrorRecovery:
    """エラー回復機能を提供するクラス"""
    
    def __init__(self):
        self.error_service = ErrorHandlingService()
    
    def retry_with_fallback(self, 
                           primary_func: Callable, 
                           fallback_func: Callable, 
                           max_retries: int = 3,
                           context: str = "") -> Any:
        """プライマリ関数を実行し、失敗した場合はフォールバック関数を実行"""
        last_exception = None
        
        for attempt in range(max_retries):
            try:
                with error_context.general_operation(f"{context} (試行 {attempt + 1})"):
                    return primary_func()
            except Exception as e:
                last_exception = e
                if attempt < max_retries - 1:
                    continue
        
        # 全ての試行が失敗した場合、フォールバック関数を実行
        try:
            with error_context.general_operation(f"{context} (フォールバック)"):
                return fallback_func()
        except Exception as fallback_error:
            # フォールバックも失敗した場合、最後の例外を再発生
            self.error_service.handle_general_error(
                last_exception, 
                f"{context} - プライマリとフォールバック両方が失敗"
            )
            raise last_exception
    
    def graceful_degradation(self, 
                           high_quality_func: Callable,
                           medium_quality_func: Callable,
                           low_quality_func: Callable,
                           context: str = "") -> Any:
        """品質を段階的に下げながら処理を実行"""
        functions = [
            (high_quality_func, "高品質"),
            (medium_quality_func, "中品質"),
            (low_quality_func, "低品質")
        ]
        
        for func, quality in functions:
            try:
                with error_context.general_operation(f"{context} ({quality})"):
                    return func()
            except Exception as e:
                if quality == "低品質":  # 最後の選択肢
                    self.error_service.handle_general_error(e, f"{context} - 全ての品質レベルで失敗")
                    raise
                continue


# グローバルなエラー回復インスタンス
error_recovery = ErrorRecovery()