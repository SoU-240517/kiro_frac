"""
画像エクスポート機能のコントローラー
メインウィンドウとエクスポートダイアログを連携させる
"""

from typing import Optional, Dict, Any
import numpy as np
from PyQt6.QtWidgets import QWidget, QMessageBox

from .base import BaseController
from ..ui.export_dialog import ImageExportDialog
from ..services.image_renderer import RenderingEngine, RenderSettings
from ..models.data_models import FractalResult


class ExportController(BaseController):
    """
    画像エクスポート機能のコントローラー
    
    要件4.1-4.5に対応:
    - PNG、JPEG形式での画像出力の制御
    - 解像度指定とファイル形式選択の管理
    - 高解像度画像生成の進行状況管理
    """
    
    def __init__(self, parent_widget: Optional[QWidget] = None):
        super().__init__()
        self.parent_widget = parent_widget
        self.rendering_engine = RenderingEngine()
        self.export_dialog: Optional[ImageExportDialog] = None
        
        # 現在のフラクタルデータ
        self.current_fractal_result: Optional[FractalResult] = None
        self.current_max_iterations: int = 1000
        
        # エクスポート履歴
        self.export_history: list = []
        self.last_export_settings: Optional[Dict[str, Any]] = None
    
    def initialize(self) -> None:
        """コントローラーを初期化"""
        try:
            self.error_service.logger.info("Initializing Export Controller...")
            
            # レンダリングエンジンの初期化確認
            if not self.rendering_engine:
                raise RuntimeError("Rendering engine initialization failed")
            
            self._initialized = True
            self.error_service.logger.info("Export Controller initialized successfully")
            
        except Exception as e:
            self.error_service.handle_general_error(e, "export controller initialization")
            raise
    
    def set_fractal_data(self, fractal_result: FractalResult, max_iterations: int) -> None:
        """エクスポート用のフラクタルデータを設定"""
        self.current_fractal_result = fractal_result
        self.current_max_iterations = max_iterations
        
        self.error_service.logger.info(
            f"Fractal data set for export: {fractal_result.iteration_data.shape} "
            f"with {max_iterations} max iterations"
        )
    
    def show_export_dialog(self) -> bool:
        """
        エクスポートダイアログを表示
        
        Returns:
            bool: エクスポートが実行された場合True、キャンセルされた場合False
        """
        if not self.current_fractal_result:
            QMessageBox.warning(
                self.parent_widget,
                "エクスポートエラー",
                "エクスポートするフラクタルデータがありません。\n"
                "まずフラクタルを生成してください。"
            )
            return False
        
        try:
            # エクスポートダイアログを作成
            self.export_dialog = ImageExportDialog(self.parent_widget)
            
            # フラクタルデータを設定
            self.export_dialog.set_fractal_data(
                self.current_fractal_result.iteration_data,
                self.current_max_iterations
            )
            
            # 前回の設定があれば復元
            if self.last_export_settings:
                self._restore_export_settings(self.last_export_settings)
            
            # ダイアログを表示
            result = self.export_dialog.exec()
            
            if result == ImageExportDialog.DialogCode.Accepted:
                # エクスポート設定を保存
                self.last_export_settings = self.export_dialog.get_export_settings()
                self._add_to_export_history(self.last_export_settings)
                
                self.error_service.logger.info(
                    f"Image exported successfully: {self.last_export_settings.get('filepath')}"
                )
                return True
            else:
                self.error_service.logger.info("Export canceled by user")
                return False
                
        except Exception as e:
            self.error_service.handle_general_error(e, "export dialog display")
            QMessageBox.critical(
                self.parent_widget,
                "エクスポートエラー",
                f"エクスポートダイアログの表示中にエラーが発生しました:\n{str(e)}"
            )
            return False
        finally:
            self.export_dialog = None
    
    def quick_export(self, filepath: str, format_type: str = "PNG", 
                    high_resolution: bool = False, scale_factor: int = 2) -> bool:
        """
        クイックエクスポート機能（ダイアログなし）
        
        Args:
            filepath: 保存先ファイルパス
            format_type: ファイル形式 ("PNG" または "JPEG")
            high_resolution: 高解像度出力するかどうか
            scale_factor: 高解像度の倍率
            
        Returns:
            bool: エクスポートが成功した場合True
        """
        if not self.current_fractal_result:
            self.error_service.logger.error("No fractal data available for quick export")
            return False
        
        try:
            # デフォルトのレンダリング設定を使用
            render_settings = RenderSettings()
            
            # エクスポート実行
            self.rendering_engine.export_image(
                iteration_data=self.current_fractal_result.iteration_data,
                max_iterations=self.current_max_iterations,
                filepath=filepath,
                high_resolution=high_resolution,
                scale_factor=scale_factor,
                quality=95,  # JPEG用のデフォルト品質
                settings=render_settings
            )
            
            # エクスポート履歴に追加
            export_settings = {
                'filepath': filepath,
                'format': format_type,
                'high_resolution': high_resolution,
                'scale_factor': scale_factor,
                'timestamp': self._get_current_timestamp()
            }
            self._add_to_export_history(export_settings)
            
            self.error_service.logger.info(f"Quick export completed: {filepath}")
            return True
            
        except Exception as e:
            self.error_service.handle_general_error(e, "quick export")
            return False
    
    def get_export_history(self) -> list:
        """エクスポート履歴を取得"""
        return self.export_history.copy()
    
    def clear_export_history(self) -> None:
        """エクスポート履歴をクリア"""
        self.export_history.clear()
        self.error_service.logger.info("Export history cleared")
    
    def get_last_export_settings(self) -> Optional[Dict[str, Any]]:
        """最後のエクスポート設定を取得"""
        return self.last_export_settings.copy() if self.last_export_settings else None
    
    def set_color_mapper(self, color_mapper) -> None:
        """レンダリングエンジンのカラーマッパーを設定"""
        self.rendering_engine.set_color_mapper(color_mapper)
        self.error_service.logger.info("Color mapper updated for export")
    
    def get_supported_formats(self) -> list:
        """サポートされているファイル形式を取得"""
        return [
            {"name": "PNG", "extension": ".png", "description": "PNG画像 (可逆圧縮)"},
            {"name": "JPEG", "extension": ".jpg", "description": "JPEG画像 (非可逆圧縮)"}
        ]
    
    def validate_export_settings(self, settings: Dict[str, Any]) -> tuple:
        """
        エクスポート設定を検証
        
        Args:
            settings: エクスポート設定辞書
            
        Returns:
            tuple: (is_valid: bool, error_message: str)
        """
        try:
            # ファイルパスの検証
            filepath = settings.get('filepath', '').strip()
            if not filepath:
                return False, "ファイルパスが指定されていません"
            
            # 解像度の検証
            if settings.get('high_resolution', False):
                scale_factor = settings.get('scale_factor', 2)
                if not 2 <= scale_factor <= 8:
                    return False, "高解像度の倍率は2-8の範囲で指定してください"
            else:
                width = settings.get('width', 1920)
                height = settings.get('height', 1080)
                if not (100 <= width <= 8192) or not (100 <= height <= 8192):
                    return False, "解像度は100-8192ピクセルの範囲で指定してください"
            
            # JPEG品質の検証
            if 'JPEG' in settings.get('format', ''):
                quality = settings.get('quality', 95)
                if not 1 <= quality <= 100:
                    return False, "JPEG品質は1-100の範囲で指定してください"
            
            # レンダリング設定の検証
            brightness = settings.get('brightness', 1.0)
            contrast = settings.get('contrast', 1.0)
            gamma = settings.get('gamma', 1.0)
            
            if not 0.1 <= brightness <= 2.0:
                return False, "明度は0.1-2.0の範囲で指定してください"
            if not 0.1 <= contrast <= 2.0:
                return False, "コントラストは0.1-2.0の範囲で指定してください"
            if not 0.1 <= gamma <= 3.0:
                return False, "ガンマは0.1-3.0の範囲で指定してください"
            
            return True, ""
            
        except Exception as e:
            return False, f"設定検証中にエラーが発生しました: {str(e)}"
    
    def _restore_export_settings(self, settings: Dict[str, Any]) -> None:
        """エクスポートダイアログに前回の設定を復元"""
        if not self.export_dialog:
            return
        
        try:
            # ファイルパス
            if 'filepath' in settings:
                self.export_dialog.filepath_edit.setText(settings['filepath'])
            
            # ファイル形式
            if 'format' in settings:
                from PyQt6.QtCore import Qt
                format_text = settings['format']
                index = self.export_dialog.format_combo.findText(format_text, 
                                                               Qt.MatchFlag.MatchContains)
                if index >= 0:
                    self.export_dialog.format_combo.setCurrentIndex(index)
            
            # 解像度設定
            if settings.get('high_resolution', False):
                self.export_dialog.high_res_radio.setChecked(True)
                if 'scale_factor' in settings:
                    self.export_dialog.scale_spin.setValue(settings['scale_factor'])
            else:
                self.export_dialog.standard_radio.setChecked(True)
                if 'width' in settings:
                    self.export_dialog.width_spin.setValue(settings['width'])
                if 'height' in settings:
                    self.export_dialog.height_spin.setValue(settings['height'])
            
            # その他の設定
            if 'quality' in settings:
                self.export_dialog.quality_spin.setValue(settings['quality'])
            if 'anti_aliasing' in settings:
                self.export_dialog.anti_aliasing_check.setChecked(settings['anti_aliasing'])
            if 'brightness' in settings:
                self.export_dialog.brightness_spin.setValue(settings['brightness'])
            if 'contrast' in settings:
                self.export_dialog.contrast_spin.setValue(settings['contrast'])
            if 'gamma' in settings:
                self.export_dialog.gamma_spin.setValue(settings['gamma'])
                
        except Exception as e:
            self.error_service.logger.warning(f"Failed to restore export settings: {str(e)}")
    
    def _add_to_export_history(self, settings: Dict[str, Any]) -> None:
        """エクスポート履歴に追加"""
        history_entry = settings.copy()
        history_entry['timestamp'] = self._get_current_timestamp()
        
        self.export_history.append(history_entry)
        
        # 履歴の上限を設定（最新の20件まで保持）
        if len(self.export_history) > 20:
            self.export_history = self.export_history[-20:]
    
    def _get_current_timestamp(self) -> str:
        """現在のタイムスタンプを取得"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")