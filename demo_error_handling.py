"""
エラーハンドリングシステムのデモンストレーション
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fractal_editor.services.error_handling import (
    ErrorHandlingService,
    FractalCalculationException,
    FormulaValidationError,
    PluginLoadError,
    ImageExportError,
    ProjectFileError,
    MemoryError,
    UIError
)
from fractal_editor.services.logging_config import LoggingConfig, get_fractal_logger, log_performance
from fractal_editor.models.data_models import (
    FractalParameters,
    ComplexRegion,
    ComplexNumber
)
import time


def demo_error_handling():
    """エラーハンドリングシステムのデモ"""
    print("=== フラクタルエディタ エラーハンドリングシステム デモ ===\n")
    
    # ロギング設定を初期化
    LoggingConfig.setup_logging()
    
    # エラーハンドリングサービスを取得
    error_service = ErrorHandlingService()
    
    # 各種ロガーを取得
    main_logger = get_fractal_logger()
    calc_logger = get_fractal_logger('calculation')
    ui_logger = get_fractal_logger('ui')
    
    print("1. 基本的なログ出力テスト")
    main_logger.info("アプリケーションが開始されました")
    calc_logger.debug("計算モジュールが初期化されました")
    ui_logger.warning("UIコンポーネントで警告が発生しました")
    print()
    
    print("2. フラクタル計算エラーのテスト")
    try:
        parameters = FractalParameters(
            region=ComplexRegion(
                top_left=ComplexNumber(-2.0, 1.0),
                bottom_right=ComplexNumber(1.0, -1.0)
            ),
            max_iterations=1000,
            image_size=(4000, 4000),  # 大きなサイズ
            custom_parameters={}
        )
        raise FractalCalculationException("数値オーバーフローが発生しました", parameters, "iteration_calculation")
    except FractalCalculationException as e:
        error_service.handle_calculation_error(e)
    print()
    
    print("3. 数式エラーのテスト")
    try:
        raise FormulaValidationError("無効な数式: 'import os; os.system(\"rm -rf /\")'")
    except FormulaValidationError as e:
        error_service.handle_formula_error(e)
    print()
    
    print("4. プラグインエラーのテスト")
    try:
        raise PluginLoadError("プラグインファイルが見つかりません", "CustomFractal", "/plugins/custom_fractal.py")
    except PluginLoadError as e:
        error_service.handle_plugin_error(e)
    print()
    
    print("5. 画像出力エラーのテスト")
    try:
        raise ImageExportError("ディスク容量が不足しています", "/output/fractal_4k.png", "PNG")
    except ImageExportError as e:
        error_service.handle_image_export_error(e)
    print()
    
    print("6. メモリエラーのテスト")
    try:
        raise MemoryError("メモリ不足: 8K解像度の画像生成に失敗", 8192*8192*4)  # 256MB
    except MemoryError as e:
        error_service.handle_memory_error(e)
    print()
    
    print("7. UIエラーのテスト")
    try:
        raise UIError("ウィンドウの初期化に失敗しました", "MainWindow")
    except UIError as e:
        error_service.handle_ui_error(e)
    print()
    
    print("8. 一般エラーのテスト")
    try:
        raise ValueError("予期しないエラーが発生しました")
    except ValueError as e:
        error_service.handle_general_error(e, "設定ファイル読み込み")
    print()
    
    print("9. クリティカルエラーのテスト")
    try:
        raise RuntimeError("システムの重要なコンポーネントが応答しません")
    except RuntimeError as e:
        error_service.handle_critical_error(e, "システム初期化")
    print()
    
    print("10. エラー統計の表示")
    stats = error_service.get_error_statistics()
    print(f"総エラー数: {stats['total_errors']}")
    print("エラータイプ別統計:")
    for error_type, count in stats['error_types'].items():
        print(f"  {error_type}: {count}件")
    print()
    
    print("11. 最近のエラー履歴")
    recent_errors = stats['recent_errors']
    for i, error in enumerate(recent_errors[-3:], 1):  # 最新3件を表示
        print(f"  {i}. [{error['timestamp'].strftime('%H:%M:%S')}] {error['type']}: {error['message']}")
    print()
    
    print("12. エラーログのエクスポートテスト")
    export_path = "error_report_demo.txt"
    if error_service.export_error_log(export_path):
        print(f"エラーレポートが {export_path} に出力されました")
        
        # ファイルの最初の数行を表示
        try:
            with open(export_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()[:10]  # 最初の10行
                print("エクスポートされたファイルの内容（抜粋）:")
                for line in lines:
                    print(f"  {line.rstrip()}")
        except Exception as e:
            print(f"ファイル読み込みエラー: {e}")
    print()
    
    print("13. パフォーマンス測定デコレータのテスト")
    
    @log_performance
    def sample_calculation():
        """サンプル計算関数"""
        time.sleep(0.1)  # 計算をシミュレート
        return "計算完了"
    
    result = sample_calculation()
    print(f"計算結果: {result}")
    print()
    
    print("=== デモ完了 ===")
    print("ログファイルを確認してください:")
    print("  - logs/fractal_editor.log (詳細ログ)")
    print("  - logs/errors.log (エラーのみ)")
    print("  - logs/fractal_editor.json (JSON形式)")
    print(f"  - {export_path} (エラーレポート)")


if __name__ == "__main__":
    demo_error_handling()