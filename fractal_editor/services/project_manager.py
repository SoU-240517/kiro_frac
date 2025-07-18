"""
フラクタルプロジェクトの保存・読み込み機能

このモジュールは、フラクタルプロジェクトのファイルI/O機能と
最近使用したプロジェクトの管理機能を提供します。
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import asdict

from ..models.data_models import (
    FractalProject, FractalParameters, ColorPalette, ComplexRegion, 
    ComplexNumber, ColorStop, InterpolationMode
)


class ProjectFileError(Exception):
    """プロジェクトファイル関連のエラー"""
    pass


class ProjectManager:
    """フラクタルプロジェクトの管理クラス"""
    
    PROJECT_FILE_EXTENSION = ".fractal"
    PROJECT_FILE_VERSION = "1.0"
    
    def __init__(self, settings_dir: Optional[str] = None):
        """
        プロジェクトマネージャーを初期化
        
        Args:
            settings_dir: 設定ディレクトリのパス（Noneの場合はデフォルト）
        """
        if settings_dir is None:
            # デフォルトの設定ディレクトリを使用
            self.settings_dir = Path.home() / ".fractal_editor"
        else:
            self.settings_dir = Path(settings_dir)
        
        self.settings_dir.mkdir(exist_ok=True)
        self.recent_projects_file = self.settings_dir / "recent_projects.json"
        
        # 最近使用したプロジェクトのリストを初期化
        self._recent_projects: List[Dict[str, Any]] = []
        self._load_recent_projects()
    
    def save_project(self, project: FractalProject, file_path: str) -> None:
        """
        プロジェクトをファイルに保存
        
        Args:
            project: 保存するプロジェクト
            file_path: 保存先ファイルパス
            
        Raises:
            ProjectFileError: 保存に失敗した場合
        """
        try:
            # ファイルパスを正規化
            file_path = os.path.abspath(file_path)
            
            # 拡張子を確認・追加
            if not file_path.endswith(self.PROJECT_FILE_EXTENSION):
                file_path += self.PROJECT_FILE_EXTENSION
            
            # プロジェクトデータをJSONに変換
            project_data = self._project_to_dict(project)
            
            # ファイルに保存
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(project_data, f, indent=2, ensure_ascii=False)
            
            # プロジェクトのファイルパスと最終更新日時を更新
            project.file_path = file_path
            project.last_modified = datetime.now()
            
            # 最近使用したプロジェクトリストに追加
            self._add_to_recent_projects(project)
            
        except Exception as e:
            raise ProjectFileError(f"Failed to save project: {e}") from e
    
    def load_project(self, file_path: str) -> FractalProject:
        """
        ファイルからプロジェクトを読み込み
        
        Args:
            file_path: 読み込むファイルパス
            
        Returns:
            読み込まれたプロジェクト
            
        Raises:
            ProjectFileError: 読み込みに失敗した場合
        """
        try:
            # ファイルの存在確認
            if not os.path.exists(file_path):
                raise ProjectFileError(f"Project file not found: {file_path}")
            
            # ファイルから読み込み
            with open(file_path, 'r', encoding='utf-8') as f:
                project_data = json.load(f)
            
            # バージョンチェック
            file_version = project_data.get('version', '1.0')
            if file_version != self.PROJECT_FILE_VERSION:
                # 将来的にバージョン変換処理を追加
                pass
            
            # プロジェクトオブジェクトに変換
            project = self._dict_to_project(project_data)
            project.file_path = os.path.abspath(file_path)
            
            # 最近使用したプロジェクトリストに追加
            self._add_to_recent_projects(project)
            
            return project
            
        except json.JSONDecodeError as e:
            raise ProjectFileError(f"Invalid project file format: {e}") from e
        except Exception as e:
            raise ProjectFileError(f"Failed to load project: {e}") from e
    
    def get_recent_projects(self) -> List[Dict[str, Any]]:
        """
        最近使用したプロジェクトのリストを取得
        
        Returns:
            最近使用したプロジェクトの情報リスト
        """
        return self._recent_projects.copy()
    
    def clear_recent_projects(self) -> None:
        """最近使用したプロジェクトのリストをクリア"""
        self._recent_projects.clear()
        self._save_recent_projects()
    
    def remove_from_recent_projects(self, file_path: str) -> None:
        """
        指定されたファイルパスのプロジェクトを最近使用したリストから削除
        
        Args:
            file_path: 削除するプロジェクトのファイルパス
        """
        file_path = os.path.abspath(file_path)
        self._recent_projects = [
            p for p in self._recent_projects 
            if p.get('file_path') != file_path
        ]
        self._save_recent_projects()
    
    def _project_to_dict(self, project: FractalProject) -> Dict[str, Any]:
        """
        プロジェクトオブジェクトを辞書に変換
        
        Args:
            project: 変換するプロジェクト
            
        Returns:
            プロジェクトデータの辞書
        """
        return {
            'version': self.PROJECT_FILE_VERSION,
            'metadata': {
                'created_at': datetime.now().isoformat(),
                'application': 'Fractal Editor'
            },
            'project': {
                'name': project.name,
                'fractal_type': project.fractal_type,
                'last_modified': project.last_modified.isoformat(),
                'parameters': {
                    'region': {
                        'top_left': {
                            'real': project.parameters.region.top_left.real,
                            'imaginary': project.parameters.region.top_left.imaginary
                        },
                        'bottom_right': {
                            'real': project.parameters.region.bottom_right.real,
                            'imaginary': project.parameters.region.bottom_right.imaginary
                        }
                    },
                    'max_iterations': project.parameters.max_iterations,
                    'image_size': {
                        'width': project.parameters.image_size[0],
                        'height': project.parameters.image_size[1]
                    },
                    'custom_parameters': project.parameters.custom_parameters
                },
                'color_palette': {
                    'name': project.color_palette.name,
                    'interpolation_mode': project.color_palette.interpolation_mode.value,
                    'color_stops': [
                        {
                            'position': stop.position,
                            'color': {
                                'r': stop.color[0],
                                'g': stop.color[1],
                                'b': stop.color[2]
                            }
                        }
                        for stop in project.color_palette.color_stops
                    ]
                }
            }
        }
    
    def _dict_to_project(self, data: Dict[str, Any]) -> FractalProject:
        """
        辞書からプロジェクトオブジェクトを作成
        
        Args:
            data: プロジェクトデータの辞書
            
        Returns:
            プロジェクトオブジェクト
        """
        project_data = data['project']
        
        # ComplexRegionを復元
        region_data = project_data['parameters']['region']
        region = ComplexRegion(
            top_left=ComplexNumber(
                region_data['top_left']['real'],
                region_data['top_left']['imaginary']
            ),
            bottom_right=ComplexNumber(
                region_data['bottom_right']['real'],
                region_data['bottom_right']['imaginary']
            )
        )
        
        # FractalParametersを復元
        params_data = project_data['parameters']
        parameters = FractalParameters(
            region=region,
            max_iterations=params_data['max_iterations'],
            image_size=(
                params_data['image_size']['width'],
                params_data['image_size']['height']
            ),
            custom_parameters=params_data.get('custom_parameters', {})
        )
        
        # ColorPaletteを復元
        palette_data = project_data['color_palette']
        color_stops = []
        for stop_data in palette_data['color_stops']:
            color_stops.append(ColorStop(
                position=stop_data['position'],
                color=(
                    stop_data['color']['r'],
                    stop_data['color']['g'],
                    stop_data['color']['b']
                )
            ))
        
        color_palette = ColorPalette(
            name=palette_data['name'],
            color_stops=color_stops,
            interpolation_mode=InterpolationMode(palette_data['interpolation_mode'])
        )
        
        # FractalProjectを作成
        return FractalProject(
            name=project_data['name'],
            fractal_type=project_data['fractal_type'],
            parameters=parameters,
            color_palette=color_palette,
            last_modified=datetime.fromisoformat(project_data['last_modified'])
        )
    
    def _add_to_recent_projects(self, project: FractalProject) -> None:
        """
        プロジェクトを最近使用したリストに追加
        
        Args:
            project: 追加するプロジェクト
        """
        if not project.file_path:
            return
        
        # 既存のエントリを削除（重複を避けるため）
        self._recent_projects = [
            p for p in self._recent_projects 
            if p.get('file_path') != project.file_path
        ]
        
        # 新しいエントリを先頭に追加
        recent_entry = {
            'name': project.name,
            'file_path': project.file_path,
            'fractal_type': project.fractal_type,
            'last_modified': project.last_modified.isoformat(),
            'last_accessed': datetime.now().isoformat()
        }
        
        self._recent_projects.insert(0, recent_entry)
        
        # リストサイズを制限（デフォルト10件）
        max_recent = 10  # 設定から取得するように後で変更
        if len(self._recent_projects) > max_recent:
            self._recent_projects = self._recent_projects[:max_recent]
        
        # ファイルに保存
        self._save_recent_projects()
    
    def _load_recent_projects(self) -> None:
        """最近使用したプロジェクトのリストをファイルから読み込み"""
        try:
            if self.recent_projects_file.exists():
                with open(self.recent_projects_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self._recent_projects = data.get('recent_projects', [])
                    
                # 存在しないファイルを除外
                self._recent_projects = [
                    p for p in self._recent_projects
                    if os.path.exists(p.get('file_path', ''))
                ]
        except Exception:
            # エラーが発生した場合は空のリストで初期化
            self._recent_projects = []
    
    def _save_recent_projects(self) -> None:
        """最近使用したプロジェクトのリストをファイルに保存"""
        try:
            data = {
                'version': '1.0',
                'last_updated': datetime.now().isoformat(),
                'recent_projects': self._recent_projects
            }
            
            with open(self.recent_projects_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception:
            # 保存に失敗しても処理を続行
            pass


def create_default_project(name: str = "新しいプロジェクト") -> FractalProject:
    """
    デフォルト設定でプロジェクトを作成
    
    Args:
        name: プロジェクト名
        
    Returns:
        デフォルト設定のプロジェクト
    """
    # デフォルトの複素平面領域（マンデルブロ集合の標準表示範囲）
    region = ComplexRegion(
        top_left=ComplexNumber(-2.5, 1.5),
        bottom_right=ComplexNumber(1.5, -1.5)
    )
    
    # デフォルトパラメータ
    parameters = FractalParameters(
        region=region,
        max_iterations=1000,
        image_size=(800, 600),
        custom_parameters={}
    )
    
    # デフォルトカラーパレット（レインボー）
    color_palette = ColorPalette(
        name="Rainbow",
        color_stops=[
            ColorStop(0.0, (0, 0, 0)),      # 黒
            ColorStop(0.16, (255, 0, 0)),   # 赤
            ColorStop(0.33, (255, 255, 0)), # 黄
            ColorStop(0.5, (0, 255, 0)),    # 緑
            ColorStop(0.66, (0, 255, 255)), # シアン
            ColorStop(0.83, (0, 0, 255)),   # 青
            ColorStop(1.0, (255, 0, 255))   # マゼンタ
        ],
        interpolation_mode=InterpolationMode.LINEAR
    )
    
    return FractalProject(
        name=name,
        fractal_type="mandelbrot",
        parameters=parameters,
        color_palette=color_palette
    )