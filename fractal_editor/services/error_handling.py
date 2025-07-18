"""
フラクタルエディタアプリケーション用のエラーハンドリングサービス
"""
import logging
import os
import sys
from datetime import datetime
from typing import Union, Optional, Dict, Any
from pathlib import Path
from ..models.data_models import FractalParameters


class FractalCalculationException(Exception):
    """フラクタル計算中に発生する例外"""
    
    def __init__(self, message: str, parameters: FractalParameters, stage: str):
        super().__init__(message)
        self.parameters = parameters
        self.stage = stage


class FormulaValidationError(Exception):
    """数式検証が失敗した時に発生する例外"""
    pass


class FormulaEvaluationError(Exception):
    """数式評価が失敗した時に発生する例外"""
    pass


class PluginLoadError(Exception):
    """プラグイン読み込みが失敗した時に発生する例外"""
    
    def __init__(self, message: str, plugin_name: str = "", plugin_path: str = ""):
        super().__init__(message)
        self.plugin_name = plugin_name
        self.plugin_path = plugin_path


class ImageExportError(Exception):
    """画像出力が失敗した時に発生する例外"""
    
    def __init__(self, message: str, file_path: str = "", format_type: str = ""):
        super().__init__(message)
        self.file_path = file_path
        self.format_type = format_type


class ProjectFileError(Exception):
    """プロジェクトファイル操作が失敗した時に発生する例外"""
    
    def __init__(self, message: str, file_path: str = "", operation: str = ""):
        super().__init__(message)
        self.file_path = file_path
        self.operation = operation


class MemoryError(Exception):
    """メモリ不足エラー"""
    
    def __init__(self, message: str, requested_size: int = 0):
        super().__init__(message)
        self.requested_size = requested_size


class UIError(Exception):
    """UI関連のエラー"""
    
    def __init__(self, message: str, component: str = ""):
        super().__init__(message)
        self.component = component


class ErrorHandlingService:
    """アプリケーションエラーを処理するサービス"""
    
    _instance = None
    
    def __new__(cls):
        """シングルトンパターンの実装"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """エラーハンドリングサービスを初期化"""
        if hasattr(self, '_initialized'):
            return
        self._initialized = True
        
        self.logger = logging.getLogger('fractal_editor')
        self.error_count = 0
        self.error_history = []
        self._setup_logging()
    
    def _setup_logging(self) -> None:
        """ロギング設定をセットアップ"""
        from .logging_config import LoggingConfig
        
        # ロギング設定を初期化
        LoggingConfig.setup_logging()
        
        # フラクタルエディタ用のロガーを取得
        self.logger = logging.getLogger('fractal_editor.error_handling')
        
        self.logger.info("エラーハンドリングサービスが初期化されました")
    
    def _record_error(self, error_type: str, message: str, details: Dict[str, Any] = None) -> None:
        """エラーを記録"""
        self.error_count += 1
        error_record = {
            'timestamp': datetime.now(),
            'type': error_type,
            'message': message,
            'details': details or {},
            'count': self.error_count
        }
        self.error_history.append(error_record)
        
        # 履歴を最新100件に制限
        if len(self.error_history) > 100:
            self.error_history = self.error_history[-100:]
    
    def handle_calculation_error(self, ex: FractalCalculationException) -> None:
        """フラクタル計算エラーを処理"""
        error_details = {
            'stage': ex.stage,
            'parameters': {
                'max_iterations': ex.parameters.max_iterations,
                'image_size': ex.parameters.image_size,
                'region': f"{ex.parameters.region.top_left} to {ex.parameters.region.bottom_right}"
            }
        }
        
        self.logger.error(f"フラクタル計算エラー - ステージ: {ex.stage}, エラー: {ex}")
        self._record_error('FractalCalculation', str(ex), error_details)
        
        # UI通知（将来のPyQt6実装用）
        print(f"計算エラー: フラクタル計算でエラーが発生しました: {ex}")
    
    def handle_formula_error(self, ex: Union[FormulaValidationError, FormulaEvaluationError]) -> None:
        """数式エラーを処理"""
        error_type = 'FormulaValidation' if isinstance(ex, FormulaValidationError) else 'FormulaEvaluation'
        
        self.logger.error(f"数式エラー ({error_type}): {ex}")
        self._record_error(error_type, str(ex))
        
        print(f"数式エラー: 数式にエラーがあります: {ex}")
        print("使用可能な変数: z, c, n")
        print("使用可能な関数: sin, cos, tan, exp, log, sqrt, abs, conj")
    
    def handle_plugin_error(self, ex: PluginLoadError) -> None:
        """プラグインエラーを処理"""
        error_details = {
            'plugin_name': ex.plugin_name,
            'plugin_path': ex.plugin_path
        }
        
        self.logger.error(f"プラグインエラー - 名前: {ex.plugin_name}, パス: {ex.plugin_path}, エラー: {ex}")
        self._record_error('PluginLoad', str(ex), error_details)
        
        print(f"プラグインエラー: プラグイン '{ex.plugin_name}' の読み込みに失敗しました: {ex}")
    
    def handle_image_export_error(self, ex: ImageExportError) -> None:
        """画像出力エラーを処理"""
        error_details = {
            'file_path': ex.file_path,
            'format_type': ex.format_type
        }
        
        self.logger.error(f"画像出力エラー - ファイル: {ex.file_path}, 形式: {ex.format_type}, エラー: {ex}")
        self._record_error('ImageExport', str(ex), error_details)
        
        print(f"画像出力エラー: 画像の保存に失敗しました: {ex}")
    
    def handle_project_file_error(self, ex: ProjectFileError) -> None:
        """プロジェクトファイルエラーを処理"""
        error_details = {
            'file_path': ex.file_path,
            'operation': ex.operation
        }
        
        self.logger.error(f"プロジェクトファイルエラー - 操作: {ex.operation}, ファイル: {ex.file_path}, エラー: {ex}")
        self._record_error('ProjectFile', str(ex), error_details)
        
        print(f"ファイルエラー: プロジェクトファイルの{ex.operation}に失敗しました: {ex}")
    
    def handle_memory_error(self, ex: MemoryError) -> None:
        """メモリエラーを処理"""
        error_details = {
            'requested_size': ex.requested_size
        }
        
        self.logger.error(f"メモリエラー - 要求サイズ: {ex.requested_size}, エラー: {ex}")
        self._record_error('Memory', str(ex), error_details)
        
        print(f"メモリエラー: メモリが不足しています。画像サイズや反復回数を減らしてください: {ex}")
    
    def handle_ui_error(self, ex: UIError) -> None:
        """UIエラーを処理"""
        error_details = {
            'component': ex.component
        }
        
        self.logger.error(f"UIエラー - コンポーネント: {ex.component}, エラー: {ex}")
        self._record_error('UI', str(ex), error_details)
        
        print(f"UIエラー: ユーザーインターフェースでエラーが発生しました: {ex}")
    
    def handle_general_error(self, ex: Exception, context: str = "") -> None:
        """一般的なエラーを処理"""
        error_details = {
            'context': context,
            'exception_type': type(ex).__name__
        }
        
        self.logger.error(f"一般エラー - コンテキスト: {context}, エラー: {ex}", exc_info=True)
        self._record_error('General', str(ex), error_details)
        
        print(f"エラー: {context}で問題が発生しました: {ex}")
    
    def handle_critical_error(self, ex: Exception, context: str = "") -> None:
        """クリティカルエラーを処理（アプリケーション終了を伴う可能性）"""
        error_details = {
            'context': context,
            'exception_type': type(ex).__name__,
            'critical': True
        }
        
        self.logger.critical(f"クリティカルエラー - コンテキスト: {context}, エラー: {ex}", exc_info=True)
        self._record_error('Critical', str(ex), error_details)
        
        print(f"クリティカルエラー: アプリケーションで重大なエラーが発生しました: {ex}")
        print("アプリケーションを再起動することをお勧めします。")
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """エラー統計を取得"""
        if not self.error_history:
            return {'total_errors': 0, 'error_types': {}}
        
        error_types = {}
        for error in self.error_history:
            error_type = error['type']
            error_types[error_type] = error_types.get(error_type, 0) + 1
        
        return {
            'total_errors': self.error_count,
            'error_types': error_types,
            'recent_errors': self.error_history[-10:] if len(self.error_history) >= 10 else self.error_history
        }
    
    def clear_error_history(self) -> None:
        """エラー履歴をクリア"""
        self.error_history.clear()
        self.error_count = 0
        self.logger.info("エラー履歴がクリアされました")
    
    def export_error_log(self, file_path: str) -> bool:
        """エラーログをファイルにエクスポート"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write("フラクタルエディタ エラーレポート\n")
                f.write(f"生成日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"総エラー数: {self.error_count}\n\n")
                
                for i, error in enumerate(self.error_history, 1):
                    f.write(f"エラー #{i}\n")
                    f.write(f"時刻: {error['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"タイプ: {error['type']}\n")
                    f.write(f"メッセージ: {error['message']}\n")
                    if error['details']:
                        f.write(f"詳細: {error['details']}\n")
                    f.write("-" * 50 + "\n")
            
            self.logger.info(f"エラーログが {file_path} にエクスポートされました")
            return True
        except Exception as e:
            self.logger.error(f"エラーログのエクスポートに失敗: {e}")
            return False