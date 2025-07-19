# 技術スタック

## 開発環境

- **Python**: 3.8以上（推奨: 3.11）
- **OS**: Windows（win32プラットフォーム）
- **シェル**: cmd

## 主要依存関係

### コア依存関係
- **PyQt6** (>=6.4.0): GUIフレームワーク
- **NumPy** (>=1.24.0): 数値計算
- **Pillow** (>=9.5.0): 画像処理

### 開発・テスト依存関係
- **pytest** (>=7.0.0): テストフレームワーク
- **pytest-qt** (>=4.2.0): PyQt6テスト支援

### 追加依存関係
- **multiprocessing-logging** (>=0.3.4): 並列処理ログ
- **psutil** (>=5.9.0): システムリソース監視

## ビルド・テストコマンド

### 環境セットアップ
```cmd
# 依存関係インストール
pip install -r requirements.txt

# 開発モードでインストール
pip install -e .
```

### アプリケーション実行
```cmd
# メインアプリケーション起動
python fractal_editor/main.py

# または
fractal-editor
```

### テスト実行
```cmd
# 統合テスト検証（推奨・高速）
python test_integration_verification.py

# 基本統合テスト
python test_integration_comprehensive.py

# UI応答性テスト
python test_ui_responsiveness_integration.py

# 全統合テスト実行
python run_integration_tests.py

# Windowsバッチファイル使用
run_tests.bat
```

### プロジェクト構造検証
```cmd
python verify_project_structure.py
```

## パッケージ管理

- **setup.py**: パッケージ設定
- **requirements.txt**: 依存関係定義
- エントリーポイント: `fractal-editor=fractal_editor.main:main`

## ログ設定

- **ログディレクトリ**: `logs/`
- **メインログ**: `logs/fractal_editor.log`
- **エラーログ**: `logs/errors.log`
- **JSON形式ログ**: `logs/fractal_editor.json`