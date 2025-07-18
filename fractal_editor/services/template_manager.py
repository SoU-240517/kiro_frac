"""
式テンプレートマネージャー

プリセット式テンプレートのライブラリとユーザーカスタム式の
保存・読み込み機能を提供します。
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime

from .formula_parser import FormulaTemplate, FormulaParser, FormulaValidationError


@dataclass
class CustomTemplate:
    """カスタムテンプレートのデータクラス"""
    name: str
    formula: str
    description: str
    author: str = ""
    created_date: str = ""
    modified_date: str = ""
    tags: List[str] = None
    example_params: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.example_params is None:
            self.example_params = {}
        if not self.created_date:
            self.created_date = datetime.now().isoformat()
        if not self.modified_date:
            self.modified_date = self.created_date
    
    def to_formula_template(self) -> FormulaTemplate:
        """FormulaTemplateオブジェクトに変換"""
        return FormulaTemplate(
            name=self.name,
            formula=self.formula,
            description=self.description,
            example_params=self.example_params
        )
    
    @classmethod
    def from_formula_template(cls, template: FormulaTemplate, author: str = "") -> 'CustomTemplate':
        """FormulaTemplateから作成"""
        return cls(
            name=template.name,
            formula=template.formula,
            description=template.description,
            author=author,
            example_params=template.example_params or {}
        )


class TemplateStorage:
    """テンプレートの永続化を管理するクラス"""
    
    def __init__(self, storage_dir: str = None):
        """
        テンプレートストレージを初期化
        
        Args:
            storage_dir: テンプレートを保存するディレクトリ
        """
        if storage_dir is None:
            # デフォルトのストレージディレクトリ
            home_dir = Path.home()
            storage_dir = home_dir / ".fractal_editor" / "templates"
        
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        # カスタムテンプレートファイル
        self.custom_templates_file = self.storage_dir / "custom_templates.json"
        
        # ユーザー設定ファイル
        self.settings_file = self.storage_dir / "template_settings.json"
        
        # デフォルト設定
        self.default_settings = {
            "auto_backup": True,
            "max_backups": 5,
            "sort_order": "name",  # "name", "date", "author"
            "show_builtin": True,
            "show_custom": True,
            "default_author": ""
        }
    
    def load_custom_templates(self) -> Dict[str, CustomTemplate]:
        """カスタムテンプレートを読み込み"""
        if not self.custom_templates_file.exists():
            return {}
        
        try:
            with open(self.custom_templates_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            templates = {}
            for name, template_data in data.items():
                try:
                    template = CustomTemplate(**template_data)
                    templates[name] = template
                except (TypeError, ValueError) as e:
                    print(f"Warning: Failed to load template '{name}': {e}")
                    continue
            
            return templates
            
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error loading custom templates: {e}")
            return {}
    
    def save_custom_templates(self, templates: Dict[str, CustomTemplate]) -> bool:
        """カスタムテンプレートを保存"""
        try:
            # バックアップを作成
            if self.custom_templates_file.exists():
                self._create_backup()
            
            # テンプレートを辞書に変換
            data = {}
            for name, template in templates.items():
                data[name] = asdict(template)
            
            # ファイルに保存
            with open(self.custom_templates_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            return True
            
        except (IOError, json.JSONEncodeError) as e:
            print(f"Error saving custom templates: {e}")
            return False
    
    def _create_backup(self) -> None:
        """バックアップファイルを作成"""
        if not self.custom_templates_file.exists():
            return
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = self.storage_dir / f"custom_templates_backup_{timestamp}.json"
        
        try:
            import shutil
            shutil.copy2(self.custom_templates_file, backup_file)
            
            # 古いバックアップを削除
            self._cleanup_old_backups()
            
        except IOError as e:
            print(f"Warning: Failed to create backup: {e}")
    
    def _cleanup_old_backups(self) -> None:
        """古いバックアップファイルを削除"""
        try:
            settings = self.load_settings()
            max_backups = settings.get("max_backups", 5)
            
            # バックアップファイルを取得
            backup_files = list(self.storage_dir.glob("custom_templates_backup_*.json"))
            
            # 作成日時でソート（新しい順）
            backup_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
            
            # 古いファイルを削除
            for old_backup in backup_files[max_backups:]:
                old_backup.unlink()
                
        except Exception as e:
            print(f"Warning: Failed to cleanup old backups: {e}")
    
    def load_settings(self) -> Dict[str, Any]:
        """設定を読み込み"""
        if not self.settings_file.exists():
            return self.default_settings.copy()
        
        try:
            with open(self.settings_file, 'r', encoding='utf-8') as f:
                settings = json.load(f)
            
            # デフォルト設定とマージ
            merged_settings = self.default_settings.copy()
            merged_settings.update(settings)
            
            return merged_settings
            
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error loading settings: {e}")
            return self.default_settings.copy()
    
    def save_settings(self, settings: Dict[str, Any]) -> bool:
        """設定を保存"""
        try:
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=2, ensure_ascii=False)
            return True
            
        except (IOError, json.JSONEncodeError) as e:
            print(f"Error saving settings: {e}")
            return False
    
    def export_template(self, template: CustomTemplate, file_path: str) -> bool:
        """テンプレートを個別ファイルにエクスポート"""
        try:
            data = asdict(template)
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True
            
        except (IOError, json.JSONEncodeError) as e:
            print(f"Error exporting template: {e}")
            return False
    
    def import_template(self, file_path: str) -> Optional[CustomTemplate]:
        """個別ファイルからテンプレートをインポート"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            template = CustomTemplate(**data)
            
            # 数式の妥当性を検証
            FormulaParser(template.formula)
            
            return template
            
        except (json.JSONDecodeError, IOError, TypeError, ValueError, FormulaValidationError) as e:
            print(f"Error importing template: {e}")
            return None


class EnhancedTemplateManager:
    """拡張されたテンプレートマネージャー"""
    
    def __init__(self, storage_dir: str = None):
        """
        拡張テンプレートマネージャーを初期化
        
        Args:
            storage_dir: テンプレートを保存するディレクトリ
        """
        # ストレージを初期化
        self.storage = TemplateStorage(storage_dir)
        
        # 組み込みテンプレート（formula_parser.pyから）
        from .formula_parser import FORMULA_TEMPLATES
        self.builtin_templates = {template.name: template for template in FORMULA_TEMPLATES}
        
        # カスタムテンプレートを読み込み
        self.custom_templates = self.storage.load_custom_templates()
        
        # 設定を読み込み
        self.settings = self.storage.load_settings()
    
    def get_template(self, name: str) -> FormulaTemplate:
        """
        テンプレートを名前で取得
        
        Args:
            name: テンプレート名
            
        Returns:
            FormulaTemplate オブジェクト
            
        Raises:
            KeyError: テンプレートが見つからない場合
        """
        # カスタムテンプレートを優先
        if name in self.custom_templates:
            return self.custom_templates[name].to_formula_template()
        elif name in self.builtin_templates:
            return self.builtin_templates[name]
        else:
            raise KeyError(f"Template '{name}' not found")
    
    def list_templates(self, include_builtin: bool = True, include_custom: bool = True) -> List[str]:
        """
        利用可能なテンプレート名のリストを取得
        
        Args:
            include_builtin: 組み込みテンプレートを含めるか
            include_custom: カスタムテンプレートを含めるか
            
        Returns:
            テンプレート名のリスト
        """
        templates = []
        
        if include_builtin and self.settings.get("show_builtin", True):
            templates.extend(self.builtin_templates.keys())
        
        if include_custom and self.settings.get("show_custom", True):
            templates.extend(self.custom_templates.keys())
        
        # ソート順に従って並び替え
        sort_order = self.settings.get("sort_order", "name")
        if sort_order == "name":
            templates.sort()
        elif sort_order == "date":
            # カスタムテンプレートの日付でソート（組み込みは最初）
            def sort_key(name):
                if name in self.custom_templates:
                    return self.custom_templates[name].modified_date
                else:
                    return "0000-00-00"  # 組み込みテンプレートは最初
            templates.sort(key=sort_key, reverse=True)
        
        return templates
    
    def get_all_templates(self) -> Dict[str, FormulaTemplate]:
        """
        すべてのテンプレートを取得
        
        Returns:
            テンプレート名をキーとする辞書
        """
        result = {}
        
        if self.settings.get("show_builtin", True):
            result.update(self.builtin_templates)
        
        if self.settings.get("show_custom", True):
            for name, custom_template in self.custom_templates.items():
                result[name] = custom_template.to_formula_template()
        
        return result
    
    def add_custom_template(self, template: CustomTemplate) -> bool:
        """
        カスタムテンプレートを追加
        
        Args:
            template: 追加するテンプレート
            
        Returns:
            成功した場合True
        """
        try:
            # 数式の妥当性を検証
            FormulaParser(template.formula)
            
            # 修正日時を更新
            template.modified_date = datetime.now().isoformat()
            
            # テンプレートを追加
            self.custom_templates[template.name] = template
            
            # 保存
            return self.storage.save_custom_templates(self.custom_templates)
            
        except FormulaValidationError as e:
            print(f"Invalid formula in template: {e}")
            return False
    
    def update_custom_template(self, name: str, template: CustomTemplate) -> bool:
        """
        カスタムテンプレートを更新
        
        Args:
            name: 更新するテンプレート名
            template: 新しいテンプレートデータ
            
        Returns:
            成功した場合True
        """
        if name not in self.custom_templates:
            return False
        
        try:
            # 数式の妥当性を検証
            FormulaParser(template.formula)
            
            # 作成日時を保持、修正日時を更新
            old_template = self.custom_templates[name]
            template.created_date = old_template.created_date
            template.modified_date = datetime.now().isoformat()
            
            # テンプレートを更新
            self.custom_templates[name] = template
            
            # 保存
            return self.storage.save_custom_templates(self.custom_templates)
            
        except FormulaValidationError as e:
            print(f"Invalid formula in template: {e}")
            return False
    
    def remove_custom_template(self, name: str) -> bool:
        """
        カスタムテンプレートを削除
        
        Args:
            name: 削除するテンプレート名
            
        Returns:
            削除に成功した場合True
        """
        if name in self.custom_templates:
            del self.custom_templates[name]
            return self.storage.save_custom_templates(self.custom_templates)
        return False
    
    def search_templates(self, query: str, include_builtin: bool = True, include_custom: bool = True) -> List[FormulaTemplate]:
        """
        テンプレートを検索
        
        Args:
            query: 検索クエリ
            include_builtin: 組み込みテンプレートを含めるか
            include_custom: カスタムテンプレートを含めるか
            
        Returns:
            マッチしたテンプレートのリスト
        """
        query_lower = query.lower()
        results = []
        
        # 組み込みテンプレートを検索
        if include_builtin and self.settings.get("show_builtin", True):
            for template in self.builtin_templates.values():
                if (query_lower in template.name.lower() or 
                    query_lower in template.description.lower() or
                    query_lower in template.formula.lower()):
                    results.append(template)
        
        # カスタムテンプレートを検索
        if include_custom and self.settings.get("show_custom", True):
            for custom_template in self.custom_templates.values():
                template = custom_template.to_formula_template()
                if (query_lower in template.name.lower() or 
                    query_lower in template.description.lower() or
                    query_lower in template.formula.lower() or
                    query_lower in custom_template.author.lower() or
                    any(query_lower in tag.lower() for tag in custom_template.tags)):
                    results.append(template)
        
        return results
    
    def get_templates_by_tag(self, tag: str) -> List[FormulaTemplate]:
        """
        タグでテンプレートを取得
        
        Args:
            tag: 検索するタグ
            
        Returns:
            マッチしたテンプレートのリスト
        """
        results = []
        tag_lower = tag.lower()
        
        for custom_template in self.custom_templates.values():
            if any(tag_lower == t.lower() for t in custom_template.tags):
                results.append(custom_template.to_formula_template())
        
        return results
    
    def get_template_info(self, name: str) -> Dict[str, Any]:
        """
        テンプレートの詳細情報を取得
        
        Args:
            name: テンプレート名
            
        Returns:
            テンプレート情報の辞書
        """
        if name in self.custom_templates:
            custom_template = self.custom_templates[name]
            return {
                'name': custom_template.name,
                'formula': custom_template.formula,
                'description': custom_template.description,
                'author': custom_template.author,
                'created_date': custom_template.created_date,
                'modified_date': custom_template.modified_date,
                'tags': custom_template.tags,
                'example_params': custom_template.example_params,
                'type': 'custom'
            }
        elif name in self.builtin_templates:
            template = self.builtin_templates[name]
            return {
                'name': template.name,
                'formula': template.formula,
                'description': template.description,
                'example_params': template.example_params,
                'type': 'builtin'
            }
        else:
            raise KeyError(f"Template '{name}' not found")
    
    def export_template(self, name: str, file_path: str) -> bool:
        """
        テンプレートをファイルにエクスポート
        
        Args:
            name: エクスポートするテンプレート名
            file_path: 出力ファイルパス
            
        Returns:
            成功した場合True
        """
        if name in self.custom_templates:
            return self.storage.export_template(self.custom_templates[name], file_path)
        elif name in self.builtin_templates:
            # 組み込みテンプレートをカスタムテンプレート形式でエクスポート
            builtin = self.builtin_templates[name]
            custom = CustomTemplate.from_formula_template(builtin)
            return self.storage.export_template(custom, file_path)
        else:
            return False
    
    def import_template(self, file_path: str, overwrite: bool = False) -> bool:
        """
        ファイルからテンプレートをインポート
        
        Args:
            file_path: インポートするファイルパス
            overwrite: 既存テンプレートを上書きするか
            
        Returns:
            成功した場合True
        """
        template = self.storage.import_template(file_path)
        if template is None:
            return False
        
        # 名前の重複チェック
        if template.name in self.custom_templates and not overwrite:
            print(f"Template '{template.name}' already exists. Use overwrite=True to replace.")
            return False
        
        return self.add_custom_template(template)
    
    def get_settings(self) -> Dict[str, Any]:
        """設定を取得"""
        return self.settings.copy()
    
    def update_settings(self, new_settings: Dict[str, Any]) -> bool:
        """
        設定を更新
        
        Args:
            new_settings: 新しい設定
            
        Returns:
            成功した場合True
        """
        self.settings.update(new_settings)
        return self.storage.save_settings(self.settings)
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        テンプレートの統計情報を取得
        
        Returns:
            統計情報の辞書
        """
        return {
            'builtin_count': len(self.builtin_templates),
            'custom_count': len(self.custom_templates),
            'total_count': len(self.builtin_templates) + len(self.custom_templates),
            'storage_dir': str(self.storage.storage_dir),
            'last_modified': max(
                (template.modified_date for template in self.custom_templates.values()),
                default="N/A"
            )
        }
    
    def create_template_from_formula(self, name: str, formula: str, description: str = "", 
                                   author: str = "", tags: List[str] = None) -> bool:
        """
        数式から新しいテンプレートを作成
        
        Args:
            name: テンプレート名
            formula: 数式
            description: 説明
            author: 作成者
            tags: タグのリスト
            
        Returns:
            成功した場合True
        """
        if tags is None:
            tags = []
        
        if not author:
            author = self.settings.get("default_author", "")
        
        template = CustomTemplate(
            name=name,
            formula=formula,
            description=description,
            author=author,
            tags=tags
        )
        
        return self.add_custom_template(template)


# グローバルインスタンス
enhanced_template_manager = EnhancedTemplateManager()