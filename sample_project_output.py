"""
サンプルプロジェクトファイルの出力

実際に保存されるプロジェクトファイルの内容を確認するためのスクリプト
"""

import json
from fractal_editor.services.project_manager import create_default_project, ProjectManager


def main():
    """メイン関数"""
    print("=== サンプルプロジェクトファイルの内容 ===\n")
    
    # デフォルトプロジェクトを作成
    project = create_default_project("サンプルプロジェクト")
    
    # プロジェクトマネージャーを作成
    manager = ProjectManager()
    
    # プロジェクトをJSONに変換（内部メソッドを使用）
    project_data = manager._project_to_dict(project)
    
    # JSONを整形して出力
    json_output = json.dumps(project_data, indent=2, ensure_ascii=False)
    print(json_output)
    
    print("\n=== ファイル構造の説明 ===")
    print("- version: プロジェクトファイルのバージョン")
    print("- metadata: ファイル作成情報")
    print("- project: プロジェクトの実際のデータ")
    print("  - name: プロジェクト名")
    print("  - fractal_type: フラクタルの種類")
    print("  - parameters: フラクタル計算パラメータ")
    print("    - region: 複素平面の表示領域")
    print("    - max_iterations: 最大反復回数")
    print("    - image_size: 画像サイズ")
    print("    - custom_parameters: カスタムパラメータ")
    print("  - color_palette: カラーパレット設定")
    print("    - name: パレット名")
    print("    - interpolation_mode: 色補間モード")
    print("    - color_stops: カラーストップの配列")


if __name__ == "__main__":
    main()