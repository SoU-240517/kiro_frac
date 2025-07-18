"""
プラグインシステムの基底クラスとインターフェース。
フラクタル生成器を拡張するためのプラグインアーキテクチャを定義します。
"""
import os
import sys
import importlib
import importlib.util
import traceback
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Any, List, Optional, Set
from pathlib import Path
from ..generators.base import FractalGenerator


@dataclass
class PluginMetadata:
    """フラクタルプラグインのメタデータ。"""
    name: str
    version: str
    author: str
    description: str
    min_app_version: str = "1.0.0"
    dependencies: List[str] = None
    
    def __post_init__(self):
        """デフォルト値を初期化。"""
        if self.dependencies is None:
            self.dependencies = []


class PluginError(Exception):
    """プラグイン関連のエラー。"""
    pass


class PluginLoadError(PluginError):
    """プラグイン読み込みエラー。"""
    pass


class PluginValidationError(PluginError):
    """プラグイン検証エラー。"""
    pass


class FractalPlugin(ABC):
    """フラクタルプラグインの抽象基底クラス。"""
    
    @property
    @abstractmethod
    def metadata(self) -> PluginMetadata:
        """このプラグインのメタデータを取得。"""
        pass
    
    @abstractmethod
    def create_generator(self) -> FractalGenerator:
        """
        このプラグインが提供するフラクタル生成器のインスタンスを作成。
        
        Returns:
            フラクタル生成器の新しいインスタンス
        """
        pass
    
    def initialize(self) -> bool:
        """
        プラグインを初期化。プラグインが読み込まれる際に呼び出される。
        
        Returns:
            初期化が成功した場合True、失敗した場合False
        """
        return True
    
    def cleanup(self) -> None:
        """プラグインがアンロードされる際にリソースをクリーンアップ。"""
        pass
    
    def get_configuration_schema(self) -> Optional[Dict[str, Any]]:
        """
        このプラグインの設定スキーマを取得。
        
        Returns:
            設定オプションを記述する辞書、または設定がない場合None
        """
        return None


class PluginManager:
    """プラグインの読み込み、アンロード、実行を管理。"""
    
    def __init__(self):
        self._loaded_plugins: Dict[str, FractalPlugin] = {}
        self._plugin_paths: List[str] = []
        self._disabled_plugins: Set[str] = set()
        self._plugin_modules: Dict[str, Any] = {}
        self._plugin_errors: Dict[str, str] = {}
    
    def add_plugin_path(self, path: str) -> None:
        """
        プラグインを検索するディレクトリパスを追加。
        
        Args:
            path: プラグインを検索するディレクトリパス
        """
        if path not in self._plugin_paths:
            self._plugin_paths.append(path)
    
    def discover_plugins(self) -> List[str]:
        """
        プラグインパスからプラグインファイルを発見。
        
        Returns:
            発見されたプラグインファイルのパスのリスト
        """
        plugin_files = []
        
        for plugin_path in self._plugin_paths:
            path_obj = Path(plugin_path)
            if not path_obj.exists():
                continue
                
            # .pyファイルを検索
            for py_file in path_obj.glob("*.py"):
                if py_file.name != "__init__.py":
                    plugin_files.append(str(py_file))
            
            # サブディレクトリ内の__init__.pyも検索
            for subdir in path_obj.iterdir():
                if subdir.is_dir():
                    init_file = subdir / "__init__.py"
                    if init_file.exists():
                        plugin_files.append(str(init_file))
        
        return plugin_files
    
    def load_plugin_from_file(self, file_path: str) -> bool:
        """
        ファイルからプラグインを読み込み。
        
        Args:
            file_path: プラグインファイルのパス
            
        Returns:
            プラグインが正常に読み込まれた場合True、失敗した場合False
        """
        try:
            # モジュール名を生成
            file_path_obj = Path(file_path)
            module_name = f"plugin_{file_path_obj.stem}_{hash(file_path) % 10000}"
            
            # モジュールを動的に読み込み
            spec = importlib.util.spec_from_file_location(module_name, file_path)
            if spec is None or spec.loader is None:
                raise PluginLoadError(f"プラグインファイルの仕様を読み込めません: {file_path}")
            
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)
            
            # プラグインクラスを検索
            plugin_classes = []
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (isinstance(attr, type) and 
                    issubclass(attr, FractalPlugin) and 
                    attr != FractalPlugin):
                    plugin_classes.append(attr)
            
            if not plugin_classes:
                raise PluginLoadError(f"プラグインクラスが見つかりません: {file_path}")
            
            # 複数のプラグインクラスがある場合は最初のものを使用
            plugin_class = plugin_classes[0]
            
            # プラグインを読み込み
            success = self.load_plugin(plugin_class)
            if success:
                self._plugin_modules[file_path] = module
                # エラー履歴をクリア
                if file_path in self._plugin_errors:
                    del self._plugin_errors[file_path]
            
            return success
            
        except Exception as e:
            error_msg = f"プラグイン読み込みエラー: {str(e)}\n{traceback.format_exc()}"
            self._plugin_errors[file_path] = error_msg
            print(error_msg)
            return False
    
    def load_all_plugins(self) -> Dict[str, bool]:
        """
        すべてのプラグインパスからプラグインを読み込み。
        
        Returns:
            ファイルパスと読み込み結果の辞書
        """
        results = {}
        plugin_files = self.discover_plugins()
        
        for file_path in plugin_files:
            results[file_path] = self.load_plugin_from_file(file_path)
        
        return results
    
    def load_plugin(self, plugin_class: type[FractalPlugin]) -> bool:
        """
        プラグインクラスからプラグインを読み込み。
        
        Args:
            plugin_class: 読み込むプラグインクラス
            
        Returns:
            プラグインが正常に読み込まれた場合True、失敗した場合False
        """
        try:
            # プラグインインスタンスを作成
            plugin_instance = plugin_class()
            metadata = plugin_instance.metadata
            
            # プラグインが無効化されているかチェック
            if metadata.name in self._disabled_plugins:
                return False
            
            # プラグインが既に読み込まれているかチェック
            if metadata.name in self._loaded_plugins:
                return False
            
            # プラグインを検証
            self._validate_plugin(plugin_instance)
            
            # プラグインを初期化
            if not plugin_instance.initialize():
                raise PluginLoadError(f"プラグインの初期化に失敗: {metadata.name}")
            
            # プラグインを登録
            self._loaded_plugins[metadata.name] = plugin_instance
            
            # 生成器をグローバルレジストリに登録
            try:
                from ..generators.base import fractal_registry
                generator_instance = plugin_instance.create_generator()
                fractal_registry.register(type(generator_instance))
            except Exception as e:
                # 生成器の登録に失敗した場合はプラグインをアンロード
                self._loaded_plugins.pop(metadata.name, None)
                plugin_instance.cleanup()
                raise PluginLoadError(f"フラクタル生成器の登録に失敗: {e}")
            
            print(f"プラグインを読み込みました: {metadata.name} v{metadata.version}")
            return True
            
        except Exception as e:
            error_msg = f"プラグイン読み込みエラー: {str(e)}"
            print(error_msg)
            return False
    
    def _validate_plugin(self, plugin: FractalPlugin) -> None:
        """
        プラグインの妥当性を検証。
        
        Args:
            plugin: 検証するプラグイン
            
        Raises:
            PluginValidationError: プラグインが無効な場合
        """
        metadata = plugin.metadata
        
        # 必須フィールドの検証
        if not metadata.name or not metadata.name.strip():
            raise PluginValidationError("プラグイン名が空です")
        
        if not metadata.version or not metadata.version.strip():
            raise PluginValidationError("プラグインバージョンが空です")
        
        if not metadata.author or not metadata.author.strip():
            raise PluginValidationError("プラグイン作者が空です")
        
        # 生成器の作成をテスト
        try:
            generator = plugin.create_generator()
            if not isinstance(generator, FractalGenerator):
                raise PluginValidationError("create_generator()はFractalGeneratorのインスタンスを返す必要があります")
        except Exception as e:
            raise PluginValidationError(f"フラクタル生成器の作成に失敗: {e}")
    
    def unload_plugin(self, plugin_name: str) -> bool:
        """
        名前でプラグインをアンロード。
        
        Args:
            plugin_name: アンロードするプラグインの名前
            
        Returns:
            プラグインが正常にアンロードされた場合True、失敗した場合False
        """
        if plugin_name not in self._loaded_plugins:
            return False
        
        try:
            plugin = self._loaded_plugins[plugin_name]
            
            # フラクタルレジストリから生成器を削除
            try:
                from ..generators.base import fractal_registry
                generator_instance = plugin.create_generator()
                fractal_registry.unregister(type(generator_instance))
            except Exception as e:
                print(f"フラクタル生成器の登録解除に失敗: {e}")
            
            # プラグインをクリーンアップ
            plugin.cleanup()
            del self._loaded_plugins[plugin_name]
            
            print(f"プラグインをアンロードしました: {plugin_name}")
            return True
            
        except Exception as e:
            error_msg = f"プラグインアンロードエラー {plugin_name}: {e}"
            print(error_msg)
            return False
    
    def get_loaded_plugins(self) -> List[str]:
        """
        読み込まれたプラグイン名のリストを取得。
        
        Returns:
            読み込まれたプラグイン名のリスト
        """
        return list(self._loaded_plugins.keys())
    
    def get_plugin_info(self, plugin_name: str) -> Optional[PluginMetadata]:
        """
        読み込まれたプラグインの情報を取得。
        
        Args:
            plugin_name: プラグインの名前
            
        Returns:
            プラグインメタデータ、またはプラグインが読み込まれていない場合None
        """
        if plugin_name not in self._loaded_plugins:
            return None
        
        return self._loaded_plugins[plugin_name].metadata
    
    def get_plugin_errors(self) -> Dict[str, str]:
        """
        プラグイン読み込みエラーの履歴を取得。
        
        Returns:
            ファイルパスとエラーメッセージの辞書
        """
        return self._plugin_errors.copy()
    
    def clear_plugin_errors(self) -> None:
        """プラグインエラー履歴をクリア。"""
        self._plugin_errors.clear()
    
    def disable_plugin(self, plugin_name: str) -> None:
        """
        プラグインを無効化（読み込みを防止）。
        
        Args:
            plugin_name: 無効化するプラグインの名前
        """
        self._disabled_plugins.add(plugin_name)
        
        # 現在読み込まれている場合はアンロード
        if plugin_name in self._loaded_plugins:
            self.unload_plugin(plugin_name)
    
    def enable_plugin(self, plugin_name: str) -> None:
        """
        以前に無効化されたプラグインを有効化。
        
        Args:
            plugin_name: 有効化するプラグインの名前
        """
        self._disabled_plugins.discard(plugin_name)
    
    def is_plugin_disabled(self, plugin_name: str) -> bool:
        """
        プラグインが無効化されているかチェック。
        
        Args:
            plugin_name: チェックするプラグインの名前
            
        Returns:
            プラグインが無効化されている場合True、そうでなければFalse
        """
        return plugin_name in self._disabled_plugins
    
    def reload_plugin(self, plugin_name: str) -> bool:
        """
        プラグインを再読み込み。
        
        Args:
            plugin_name: 再読み込みするプラグインの名前
            
        Returns:
            再読み込みが成功した場合True、失敗した場合False
        """
        # プラグインがロードされていない場合は失敗
        if plugin_name not in self._loaded_plugins:
            return False
        
        # 対応するファイルパスを見つける
        file_path = None
        for path, module in self._plugin_modules.items():
            try:
                # モジュールからプラグインクラスを検索
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if (isinstance(attr, type) and 
                        issubclass(attr, FractalPlugin) and 
                        attr != FractalPlugin):
                        temp_plugin = attr()
                        if temp_plugin.metadata.name == plugin_name:
                            file_path = path
                            break
                if file_path:
                    break
            except Exception:
                continue
        
        if not file_path:
            return False
        
        # プラグインをアンロードして再読み込み
        self.unload_plugin(plugin_name)
        return self.load_plugin_from_file(file_path)
    
    def get_plugin_statistics(self) -> Dict[str, Any]:
        """
        プラグインシステムの統計情報を取得。
        
        Returns:
            統計情報の辞書
        """
        return {
            "loaded_plugins": len(self._loaded_plugins),
            "disabled_plugins": len(self._disabled_plugins),
            "plugin_paths": len(self._plugin_paths),
            "plugin_errors": len(self._plugin_errors),
            "loaded_plugin_names": list(self._loaded_plugins.keys()),
            "disabled_plugin_names": list(self._disabled_plugins)
        }


# グローバルプラグインマネージャーインスタンス
plugin_manager = PluginManager()