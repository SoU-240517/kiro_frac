# プロジェクト構造

## アーキテクチャパターン

フラクタルエディタは**レイヤードアーキテクチャ**とMVCパターンを採用しています。

## ディレクトリ構造

```
fractal_editor/
├── main.py                 # アプリケーションエントリーポイント
├── __init__.py            # パッケージ初期化・公開API定義
├── controllers/           # コントローラー層
│   ├── base.py           # 基底コントローラークラス
│   └── export_controller.py
├── models/               # データモデル層
│   ├── data_models.py    # コアデータ構造
│   ├── app_settings.py   # アプリケーション設定
│   └── interfaces.py     # インターフェース定義
├── generators/           # フラクタル生成器
│   ├── base.py          # 基底生成器クラス
│   ├── mandelbrot.py    # マンデルブロ集合
│   ├── julia.py         # ジュリア集合
│   ├── custom_formula.py # カスタム数式
│   └── parallel.py      # 並列計算対応
├── services/            # ビジネスロジック・サービス層
│   ├── error_handling.py    # エラーハンドリング
│   ├── parallel_calculator.py # 並列計算
│   ├── color_system.py     # 色彩システム
│   ├── image_renderer.py   # 画像レンダリング
│   ├── project_manager.py  # プロジェクト管理
│   └── formula_parser.py   # 数式解析
├── ui/                  # ユーザーインターフェース層
│   ├── main_window.py   # メインウィンドウ
│   ├── fractal_widget.py # フラクタル表示
│   ├── parameter_panel.py # パラメータ調整
│   └── export_dialog.py  # エクスポート画面
└── plugins/             # プラグインシステム
    ├── base.py          # プラグイン基底クラス
    ├── developer_api.py # 開発者向けAPI
    ├── template_generator.py # テンプレート生成
    └── samples/         # サンプルプラグイン
```

## 命名規則

### ファイル・ディレクトリ
- **snake_case**: ファイル名、ディレクトリ名
- **複数形**: コレクションを表すディレクトリ（controllers, models, services）

### Python コード
- **PascalCase**: クラス名（`FractalGenerator`, `MainController`）
- **snake_case**: 関数名、変数名、メソッド名
- **UPPER_CASE**: 定数

### 日本語コメント
- ドキュメント文字列は英語
- インラインコメントは日本語可
- ログメッセージは日本語

## レイヤー責任

### Controllers層
- ユーザー入力の処理
- UI-ビジネスロジック間の調整
- アプリケーションフロー制御

### Models層
- データ構造定義
- ビジネスルール
- 状態管理

### Services層
- ビジネスロジック実装
- 外部リソースアクセス
- 横断的関心事（ログ、エラー処理）

### UI層
- ユーザーインターフェース
- イベント処理
- 表示ロジック

### Generators層
- フラクタル計算アルゴリズム
- 数学的処理
- 並列計算対応

### Plugins層
- 拡張機能
- 動的ロード機能
- 開発者API

## 依存関係ルール

- **上位層 → 下位層**: Controllers → Services → Models
- **UI層**: Controllers経由でのみServices層にアクセス
- **循環依存禁止**: レイヤー間の循環参照は避ける
- **インターフェース活用**: 抽象化による疎結合