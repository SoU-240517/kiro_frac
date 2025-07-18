"""
アプリケーション設定管理モジュール

このモジュールはアプリケーションの設定を管理し、JSON形式での永続化を提供します。
"""

import os
import json
from dataclasses import dataclass, asdict
from typing import Tuple, Dict, Any, Optional
from pathlib import Path


@dataclass
class AppSettings:
    """アプリケーション設定を管理するデータクラス"""
    
    # フラクタル計算設定
    default_max_iterations: int = 1000
    default_image_size: Tuple[int, int] = (800, 600)
    default_color_palette: str = "Rainbow"
    
    # レンダリング設定
    enable_anti_aliasing: bool = True
    brightness_adjustment: float = 1.0
    contrast_adjustment: float = 1.0
    
    # パフォーマンス設定
    thread_count: int = 4
    enable_parallel_computation: bool = True
    memory_limit_mb: int = 1024
    
    # UI設定
    auto_save_interval: int = 300  # 秒
    recent_projects_count: int = 10
    show_calculation_progress: bool = True
    enable_realtime_preview: bool = True
    
    # ファイル設定
    default_export_format: str = "PNG"
    default_export_quality: int = 95
    auto_backup_enabled: bool = True
    
    def __post_init__(self):
        """初期化後の処理"""
        # CPUコア数に基づいてスレッド数を調整（デフォルト値の場合のみ）
        if self.thread_count == 4 and (os.cpu_count() or 4) != 4:
            self.thread_count = max(1, os.cpu_count() or 4)
    
    def to_dict(self) -> Dict[str, Any]:
        """設定を辞書形式に変換"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AppSettings':
        """辞書から設定オブジェクトを作成"""
        # 不正なキーを除外
        valid_keys = {field.name for field in cls.__dataclass_fields__.values()}
        filtered_data = {k: v for k, v in data.items() if k in valid_keys}
        return cls(**filtered_data)
    
    def validate(self) -> bool:
        """設定値の妥当性を検証"""
        try:
            # 基本的な範囲チェック
            if self.default_max_iterations < 10 or self.default_max_iterations > 10000:
                return False
            
            if self.default_image_size[0] < 100 or self.default_image_size[1] < 100:
                return False
            
            if self.thread_count < 1 or self.thread_count > 32:
                return False
            
            if self.auto_save_interval < 30 or self.auto_save_interval > 3600:
                return False
            
            if self.recent_projects_count < 1 or self.recent_projects_count > 50:
                return False
            
            if self.brightness_adjustment < 0.1 or self.brightness_adjustment > 3.0:
                return False
            
            if self.contrast_adjustment < 0.1 or self.contrast_adjustment > 3.0:
                return False
            
            if self.memory_limit_mb < 128 or self.memory_limit_mb > 8192:
                return False
            
            if self.default_export_quality < 1 or self.default_export_quality > 100:
                return False
            
            return True
            
        except (TypeError, ValueError, AttributeError):
            return False


class SettingsManager:
    """設定の保存・読み込みを管理するクラス"""
    
    def __init__(self, settings_file: Optional[str] = None):
        """
        設定マネージャーを初期化
        
        Args:
            settings_file: 設定ファイルのパス（Noneの場合はデフォルトパスを使用）
        """
        if settings_file is None:
            # デフォルトの設定ファイルパス
            app_data_dir = Path.home() / ".fractal_editor"
            app_data_dir.mkdir(exist_ok=True)
            self.settings_file = app_data_dir / "settings.json"
        else:
            self.settings_file = Path(settings_file)
        
        self._settings: Optional[AppSettings] = None
    
    def load_settings(self) -> AppSettings:
        """設定をファイルから読み込み"""
        try:
            if self.settings_file.exists():
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                settings = AppSettings.from_dict(data)
                
                # 設定の妥当性を検証
                if not settings.validate():
                    print(f"警告: 設定ファイルに無効な値が含まれています。デフォルト設定を使用します。")
                    settings = AppSettings()
                
                self._settings = settings
                return settings
            else:
                # 設定ファイルが存在しない場合はデフォルト設定を作成
                settings = AppSettings()
                self.save_settings(settings)
                self._settings = settings
                return settings
                
        except (json.JSONDecodeError, IOError, KeyError) as e:
            print(f"設定ファイルの読み込みに失敗しました: {e}")
            print("デフォルト設定を使用します。")
            settings = AppSettings()
            self._settings = settings
            return settings
    
    def save_settings(self, settings: AppSettings) -> bool:
        """設定をファイルに保存"""
        try:
            # 設定の妥当性を検証
            if not settings.validate():
                print("エラー: 無効な設定値のため保存できません。")
                return False
            
            # ディレクトリが存在しない場合は作成
            self.settings_file.parent.mkdir(parents=True, exist_ok=True)
            
            # JSON形式で保存
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings.to_dict(), f, indent=2, ensure_ascii=False)
            
            self._settings = settings
            print(f"設定を保存しました: {self.settings_file}")
            return True
            
        except (IOError, TypeError) as e:
            print(f"設定ファイルの保存に失敗しました: {e}")
            return False
    
    def get_settings(self) -> AppSettings:
        """現在の設定を取得（キャッシュされた設定または新規読み込み）"""
        if self._settings is None:
            return self.load_settings()
        return self._settings
    
    def reset_to_defaults(self) -> AppSettings:
        """設定をデフォルト値にリセット"""
        default_settings = AppSettings()
        self.save_settings(default_settings)
        return default_settings
    
    def backup_settings(self, backup_path: Optional[str] = None) -> bool:
        """設定のバックアップを作成"""
        try:
            if backup_path is None:
                backup_path = str(self.settings_file.with_suffix('.json.backup'))
            
            current_settings = self.get_settings()
            
            with open(backup_path, 'w', encoding='utf-8') as f:
                json.dump(current_settings.to_dict(), f, indent=2, ensure_ascii=False)
            
            print(f"設定のバックアップを作成しました: {backup_path}")
            return True
            
        except (IOError, TypeError) as e:
            print(f"設定のバックアップに失敗しました: {e}")
            return False
    
    def restore_from_backup(self, backup_path: str) -> bool:
        """バックアップから設定を復元"""
        try:
            with open(backup_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            settings = AppSettings.from_dict(data)
            
            if settings.validate():
                return self.save_settings(settings)
            else:
                print("エラー: バックアップファイルに無効な設定が含まれています。")
                return False
                
        except (json.JSONDecodeError, IOError, KeyError) as e:
            print(f"バックアップファイルの復元に失敗しました: {e}")
            return False


# グローバル設定マネージャーインスタンス
_settings_manager = None

def get_settings_manager() -> SettingsManager:
    """グローバル設定マネージャーを取得"""
    global _settings_manager
    if _settings_manager is None:
        _settings_manager = SettingsManager()
    return _settings_manager

def get_app_settings() -> AppSettings:
    """現在のアプリケーション設定を取得"""
    return get_settings_manager().get_settings()