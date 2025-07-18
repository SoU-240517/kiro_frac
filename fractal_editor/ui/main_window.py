"""
メインウィンドウの実装
PyQt6を使用したフラクタルエディタのメインウィンドウ
"""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QMenuBar, QToolBar, QStatusBar, QDockWidget,
    QLabel, QProgressBar, QSplitter, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QIcon, QKeySequence, QAction
from typing import Optional

from .formula_editor import FormulaEditorWidget
from .fractal_widget import FractalWidget
from ..generators.mandelbrot import MandelbrotGenerator
from ..generators.julia import JuliaGenerator
from ..generators.custom_formula import CustomFormulaGenerator
from ..models.data_models import FractalParameters, ComplexNumber, ComplexRegion
from ..services.background_calculator import (
    BackgroundCalculationService, get_background_calculation_service,
    get_responsive_ui_manager
)


class MainWindow(QMainWindow):
    """
    フラクタルエディタのメインウィンドウクラス

    要件5.1に対応:
    - 明確で整理されたメインウィンドウを表示
    - メニューバー、ツールバー、ステータスバーを提供
    - ドッキング可能なパネルレイアウト
    """

    # シグナル定義
    fractal_type_changed = pyqtSignal(str)
    export_requested = pyqtSignal()
    settings_requested = pyqtSignal()
    formula_applied = pyqtSignal(str)  # 数式が適用されたときのシグナル

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setWindowTitle("フラクタルエディタ")
        self.setMinimumSize(1024, 768)

        # エクスポートコントローラーは遅延初期化
        self.export_controller = None

        # バックグラウンド計算サービスを初期化
        self.background_service = get_background_calculation_service()
        self.responsive_ui_manager = get_responsive_ui_manager()

        # 計算キャンセル用のアクション
        self.cancel_action = None

        # 中央ウィジェットとレイアウトの設定
        self._setup_central_widget()

        # メニューバーの設定
        self._setup_menu_bar()

        # ツールバーの設定
        self._setup_toolbar()

        # ステータスバーの設定
        self._setup_status_bar()

        # ドッキングパネルの設定
        self._setup_dock_widgets()

        # ウィンドウの初期状態設定
        self._setup_window_state()

        # バックグラウンド計算の設定
        self._setup_background_calculation()

        # シグナル接続
        self._connect_signals()

    def _setup_central_widget(self) -> None:
        """中央ウィジェットとメインレイアウトを設定"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # メインレイアウト（水平分割）
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(5, 5, 5, 5)

        # スプリッターを使用してリサイズ可能なレイアウト
        self.main_splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(self.main_splitter)

        # フラクタル表示エリアをFractalWidgetに差し替え
        self.fractal_widget = FractalWidget()
        self.main_splitter.addWidget(self.fractal_widget)

    def _setup_menu_bar(self) -> None:
        """メニューバーを設定"""
        menubar = self.menuBar()

        # ファイルメニュー
        file_menu = menubar.addMenu("ファイル(&F)")

        # 新規プロジェクト
        new_action = QAction("新規プロジェクト(&N)", self)
        new_action.setShortcut(QKeySequence.StandardKey.New)
        new_action.setStatusTip("新しいフラクタルプロジェクトを作成")
        file_menu.addAction(new_action)

        # プロジェクトを開く
        open_action = QAction("プロジェクトを開く(&O)", self)
        open_action.setShortcut(QKeySequence.StandardKey.Open)
        open_action.setStatusTip("既存のプロジェクトを開く")
        file_menu.addAction(open_action)

        # プロジェクトを保存
        save_action = QAction("プロジェクトを保存(&S)", self)
        save_action.setShortcut(QKeySequence.StandardKey.Save)
        save_action.setStatusTip("現在のプロジェクトを保存")
        file_menu.addAction(save_action)

        file_menu.addSeparator()

        # 画像をエクスポート
        export_action = QAction("画像をエクスポート(&E)", self)
        export_action.setShortcut(QKeySequence("Ctrl+E"))
        export_action.setStatusTip("フラクタル画像をファイルに出力")
        export_action.triggered.connect(self.export_requested.emit)
        file_menu.addAction(export_action)

        file_menu.addSeparator()

        # 終了
        exit_action = QAction("終了(&X)", self)
        exit_action.setShortcut(QKeySequence.StandardKey.Quit)
        exit_action.setStatusTip("アプリケーションを終了")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # フラクタルメニュー
        fractal_menu = menubar.addMenu("フラクタル(&R)")

        # マンデルブロ集合
        mandelbrot_action = QAction("マンデルブロ集合(&M)", self)
        mandelbrot_action.setStatusTip("マンデルブロ集合を生成")
        mandelbrot_action.triggered.connect(lambda: self.fractal_type_changed.emit("mandelbrot"))
        fractal_menu.addAction(mandelbrot_action)

        # ジュリア集合
        julia_action = QAction("ジュリア集合(&J)", self)
        julia_action.setStatusTip("ジュリア集合を生成")
        julia_action.triggered.connect(lambda: self.fractal_type_changed.emit("julia"))
        fractal_menu.addAction(julia_action)

        # カスタム式
        custom_action = QAction("カスタム式(&C)", self)
        custom_action.setStatusTip("カスタム数式でフラクタルを生成")
        custom_action.triggered.connect(lambda: self.fractal_type_changed.emit("custom"))
        fractal_menu.addAction(custom_action)

        # 表示メニュー
        view_menu = menubar.addMenu("表示(&V)")

        # パネル表示切り替え用のアクションは後でドックウィジェット作成時に追加

        # ツールメニュー
        tools_menu = menubar.addMenu("ツール(&T)")

        # 設定
        settings_action = QAction("設定(&S)", self)
        settings_action.setStatusTip("アプリケーション設定を開く")
        settings_action.triggered.connect(self.settings_requested.emit)
        tools_menu.addAction(settings_action)

        # ヘルプメニュー
        help_menu = menubar.addMenu("ヘルプ(&H)")

        # 式エディタヘルプ
        formula_help_action = QAction("式エディタヘルプ(&F)", self)
        formula_help_action.setStatusTip("式エディタの使い方を表示")
        formula_help_action.triggered.connect(self._show_formula_help)
        help_menu.addAction(formula_help_action)

        help_menu.addSeparator()

        # バージョン情報
        about_action = QAction("バージョン情報(&A)", self)
        about_action.setStatusTip("アプリケーションについて")
        help_menu.addAction(about_action)

    def _setup_toolbar(self) -> None:
        """ツールバーを設定"""
        # メインツールバー
        main_toolbar = self.addToolBar("メイン")
        main_toolbar.setObjectName("MainToolBar")

        # フラクタルタイプ選択ボタン
        mandelbrot_action = QAction("マンデルブロ", self)
        mandelbrot_action.setStatusTip("マンデルブロ集合")
        mandelbrot_action.triggered.connect(lambda: self.fractal_type_changed.emit("mandelbrot"))
        main_toolbar.addAction(mandelbrot_action)

        julia_action = QAction("ジュリア", self)
        julia_action.setStatusTip("ジュリア集合")
        julia_action.triggered.connect(lambda: self.fractal_type_changed.emit("julia"))
        main_toolbar.addAction(julia_action)

        custom_action = QAction("カスタム", self)
        custom_action.setStatusTip("カスタム式")
        custom_action.triggered.connect(lambda: self.fractal_type_changed.emit("custom"))
        main_toolbar.addAction(custom_action)

        main_toolbar.addSeparator()

        # エクスポートボタン
        export_action = QAction("エクスポート", self)
        export_action.setStatusTip("画像をエクスポート")
        export_action.triggered.connect(self.export_requested.emit)
        main_toolbar.addAction(export_action)

    def _setup_status_bar(self) -> None:
        """ステータスバーを設定"""
        status_bar = self.statusBar()

        # 左側：一般的なステータスメッセージ
        self.status_label = QLabel("フラクタルエディタへようこそ")
        status_bar.addWidget(self.status_label)

        # 中央：進行状況バー（通常は非表示）
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setMaximumWidth(200)
        status_bar.addPermanentWidget(self.progress_bar)

        # 右側：計算時間表示
        self.calculation_time_label = QLabel("")
        status_bar.addPermanentWidget(self.calculation_time_label)

        # 3秒後に "準備完了" に変更
        QTimer.singleShot(3000, lambda: self.status_label.setText("準備完了"))

    def _setup_dock_widgets(self) -> None:
        """ドッキング可能なパネルを設定"""
        # パラメータパネル（右側）
        self.parameter_dock = QDockWidget("パラメータ", self)
        self.parameter_dock.setObjectName("ParameterDock")
        self.parameter_dock.setAllowedAreas(
            Qt.DockWidgetArea.LeftDockWidgetArea |
            Qt.DockWidgetArea.RightDockWidgetArea
        )

        # パラメータパネル用のプレースホルダー
        parameter_placeholder = QWidget()
        parameter_placeholder.setMinimumWidth(250)
        placeholder_layout = QVBoxLayout(parameter_placeholder)
        placeholder_label = QLabel("パラメータ調整パネル")
        placeholder_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        placeholder_layout.addWidget(placeholder_label)

        self.parameter_dock.setWidget(parameter_placeholder)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.parameter_dock)

        # カラーパレットパネル（右側下部）
        self.color_dock = QDockWidget("カラーパレット", self)
        self.color_dock.setObjectName("ColorDock")
        self.color_dock.setAllowedAreas(
            Qt.DockWidgetArea.LeftDockWidgetArea |
            Qt.DockWidgetArea.RightDockWidgetArea |
            Qt.DockWidgetArea.BottomDockWidgetArea
        )

        # カラーパネル用のプレースホルダー
        color_placeholder = QWidget()
        color_placeholder.setMinimumWidth(250)
        color_placeholder.setMinimumHeight(150)
        color_layout = QVBoxLayout(color_placeholder)
        color_label = QLabel("カラーパレット設定")
        color_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        color_layout.addWidget(color_label)

        self.color_dock.setWidget(color_placeholder)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.color_dock)

        # 式エディタパネル（下部）
        self.formula_dock = QDockWidget("式エディタ", self)
        self.formula_dock.setObjectName("FormulaDock")
        self.formula_dock.setAllowedAreas(
            Qt.DockWidgetArea.BottomDockWidgetArea |
            Qt.DockWidgetArea.TopDockWidgetArea
        )

        # 式エディタウィジェット
        self.formula_editor = FormulaEditorWidget()
        self.formula_editor.setMinimumHeight(200)

        # 式エディタのシグナルを接続
        self.formula_editor.formula_applied.connect(self.formula_applied.emit)

        self.formula_dock.setWidget(self.formula_editor)
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, self.formula_dock)

        # 初期状態では式エディタを非表示
        self.formula_dock.setVisible(False)

        # ドックウィジェットを縦に並べる
        self.splitDockWidget(self.parameter_dock, self.color_dock, Qt.Orientation.Vertical)

        # 表示メニューにパネル切り替えアクションを追加
        view_menu = self.menuBar().actions()[2].menu()  # "表示"メニュー

        view_menu.addAction(self.parameter_dock.toggleViewAction())
        view_menu.addAction(self.color_dock.toggleViewAction())
        view_menu.addAction(self.formula_dock.toggleViewAction())

    def _setup_window_state(self) -> None:
        """ウィンドウの初期状態を設定"""
        # ウィンドウを中央に配置
        self.resize(1200, 800)

        # ドックウィジェットのサイズ調整
        self.resizeDocks(
            [self.parameter_dock, self.color_dock],
            [300, 200],
            Qt.Orientation.Vertical
        )

    def set_status_message(self, message: str, timeout: int = 0) -> None:
        """ステータスバーにメッセージを表示"""
        self.statusBar().showMessage(message, timeout)

    def set_calculation_time(self, time_seconds: float) -> None:
        """計算時間をステータスバーに表示"""
        self.calculation_time_label.setText(f"計算時間: {time_seconds:.2f}秒")

    def show_progress(self, show: bool = True) -> None:
        """進行状況バーの表示/非表示を切り替え"""
        self.progress_bar.setVisible(show)
        if not show:
            self.progress_bar.setValue(0)

    def set_progress(self, value: int) -> None:
        """進行状況バーの値を設定（0-100）"""
        self.progress_bar.setValue(value)

    def get_fractal_display_area(self) -> QWidget:
        """フラクタル表示エリアのウィジェットを取得"""
        return self.fractal_widget

    def get_parameter_dock(self) -> QDockWidget:
        """パラメータドックウィジェットを取得"""
        return self.parameter_dock

    def get_color_dock(self) -> QDockWidget:
        """カラードックウィジェットを取得"""
        return self.color_dock

    def get_formula_dock(self) -> QDockWidget:
        """式エディタドックウィジェットを取得"""
        return self.formula_dock

    def show_formula_editor(self, show: bool = True) -> None:
        """式エディタパネルの表示/非表示を切り替え"""
        self.formula_dock.setVisible(show)

    def _show_formula_help(self) -> None:
        """式エディタのヘルプを表示"""
        self.formula_editor.show_help()

    def get_formula_editor(self) -> FormulaEditorWidget:
        """式エディタウィジェットを取得"""
        return self.formula_editor

    def _setup_background_calculation(self) -> None:
        """バックグラウンド計算の設定"""
        # バックグラウンド計算サービスのシグナルを接続
        self.background_service.calculation_started.connect(self._on_calculation_started)
        self.background_service.calculation_completed.connect(self._on_calculation_completed)
        self.background_service.calculation_cancelled.connect(self._on_calculation_cancelled)
        self.background_service.calculation_error.connect(self._on_calculation_error)

        # キャンセルアクションを作成（初期は無効）
        self.cancel_action = QAction("計算をキャンセル", self)
        self.cancel_action.setShortcut(QKeySequence("Escape"))
        self.cancel_action.setStatusTip("現在の計算をキャンセル")
        self.cancel_action.triggered.connect(self._cancel_calculation)
        self.cancel_action.setEnabled(False)

        # ツールバーにキャンセルボタンを追加
        main_toolbar = self.findChild(QToolBar, "MainToolBar")
        if main_toolbar:
            main_toolbar.addSeparator()
            main_toolbar.addAction(self.cancel_action)

        # UI応答性の最適化設定
        self.responsive_ui_manager.optimize_for_system_performance()

        # プログレッシブレンダリング用のタイマー
        self.progressive_timer = QTimer()
        self.progressive_timer.setSingleShot(True)
        self.progressive_timer.timeout.connect(self._start_progressive_rendering)

        # リアルタイムプレビュー用の設定
        self.preview_enabled = True
        self.preview_delay_ms = 500  # プレビュー開始までの遅延
        self.last_parameter_change_time = 0

    def start_background_calculation(self, calculation_func, parameters, show_progress: bool = True) -> bool:
        """
        バックグラウンド計算を開始

        Args:
            calculation_func: 計算関数
            parameters: 計算パラメータ
            show_progress: プログレスダイアログを表示するか

        Returns:
            計算開始に成功した場合True
        """
        if self.background_service.is_calculating():
            QMessageBox.warning(
                self, "計算中",
                "既に計算が実行中です。現在の計算が完了してから再試行してください。"
            )
            return False

        return self.background_service.start_calculation(
            calculation_func, parameters, show_progress, self
        )

    def _cancel_calculation(self) -> None:
        """計算をキャンセル"""
        if self.background_service.is_calculating():
            reply = QMessageBox.question(
                self, "計算キャンセル",
                "現在の計算をキャンセルしますか？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.Yes:
                self.background_service.cancel_calculation()

    def _on_calculation_started(self) -> None:
        """計算開始時の処理"""
        self.set_status_message("フラクタル計算を開始しました...")
        self.show_progress(True)
        self.cancel_action.setEnabled(True)

        # UI要素を無効化（計算中は操作を制限）
        self._set_ui_enabled_during_calculation(False)

    def _on_calculation_completed(self, result) -> None:
        """計算完了時の処理"""
        self.show_progress(False)
        self.cancel_action.setEnabled(False)

        # 計算時間を表示
        if hasattr(result, 'calculation_time'):
            self.set_calculation_time(result.calculation_time)

        # メモリ使用量情報を表示
        if hasattr(result, 'metadata') and 'memory_usage_mb' in result.metadata:
            memory_mb = result.metadata['memory_usage_mb']
            self.set_status_message(
                f"計算完了 (メモリ使用量: {memory_mb:.1f}MB)", 5000
            )
        else:
            self.set_status_message("フラクタル計算が完了しました", 3000)

        # UI要素を再有効化
        self._set_ui_enabled_during_calculation(True)

        # エクスポート用にフラクタルデータを設定
        if hasattr(result, 'parameters'):
            max_iterations = result.parameters.max_iterations
            self.set_fractal_data_for_export(result, max_iterations)

    def _on_calculation_cancelled(self) -> None:
        """計算キャンセル時の処理"""
        self.show_progress(False)
        self.cancel_action.setEnabled(False)
        self.set_status_message("計算がキャンセルされました", 3000)

        # UI要素を再有効化
        self._set_ui_enabled_during_calculation(True)

    def _on_calculation_error(self, error_message: str) -> None:
        """計算エラー時の処理"""
        self.show_progress(False)
        self.cancel_action.setEnabled(False)
        self.set_status_message(f"計算エラー: {error_message}", 5000)

        # エラーダイアログを表示
        QMessageBox.critical(
            self, "計算エラー",
            f"フラクタル計算でエラーが発生しました:\n\n{error_message}"
        )

        # UI要素を再有効化
        self._set_ui_enabled_during_calculation(True)

    def _set_ui_enabled_during_calculation(self, enabled: bool) -> None:
        """計算中のUI要素の有効/無効を切り替え"""
        # フラクタルタイプ変更ボタンを無効化/有効化
        main_toolbar = self.findChild(QToolBar, "MainToolBar")
        if main_toolbar:
            for action in main_toolbar.actions():
                if action.text() in ["マンデルブロ", "ジュリア", "カスタム"]:
                    action.setEnabled(enabled)

        # メニューの一部項目を無効化/有効化
        menubar = self.menuBar()
        for menu_action in menubar.actions():
            menu = menu_action.menu()
            if menu and menu.title().startswith("フラクタル"):
                for action in menu.actions():
                    action.setEnabled(enabled)

    def get_calculation_statistics(self) -> dict:
        """現在の計算統計情報を取得"""
        return self.background_service.get_calculation_statistics()

    def is_calculating(self) -> bool:
        """現在計算中かどうか"""
        return self.background_service.is_calculating()

    def _connect_signals(self) -> None:
        """シグナルを接続"""
        # エクスポート要求シグナルをエクスポートコントローラーに接続
        self.export_requested.connect(self._handle_export_request)
        # fractal_type_changedシグナルで画像生成
        self.fractal_type_changed.connect(self._on_fractal_type_changed)
        # パラメータパネルのシグナルも接続（後でパネル生成時に上書き可）
        if hasattr(self, 'parameter_panel'):
            self.parameter_panel.parameter_changed.connect(self._on_parameter_changed)

    def _handle_export_request(self) -> None:
        """エクスポート要求を処理"""
        try:
            # エクスポートコントローラーを遅延初期化
            if self.export_controller is None:
                self._initialize_export_controller()

            success = self.export_controller.show_export_dialog()
            if success:
                self.set_status_message("画像エクスポートが完了しました", 3000)
            else:
                self.set_status_message("エクスポートがキャンセルされました", 2000)
        except Exception as e:
            self.set_status_message(f"エクスポートエラー: {str(e)}", 5000)

    def _initialize_export_controller(self) -> None:
        """エクスポートコントローラーを初期化"""
        from ..controllers.export_controller import ExportController
        self.export_controller = ExportController(self)
        self.export_controller.initialize()

    def set_fractal_data_for_export(self, fractal_result, max_iterations: int) -> None:
        """エクスポート用のフラクタルデータを設定"""
        if self.export_controller is None:
            self._initialize_export_controller()
        self.export_controller.set_fractal_data(fractal_result, max_iterations)

    def get_export_controller(self):
        """エクスポートコントローラーを取得"""
        if self.export_controller is None:
            self._initialize_export_controller()
        return self.export_controller

    def enable_realtime_preview(self, enabled: bool = True) -> None:
        """
        リアルタイムプレビューの有効/無効を設定

        Args:
            enabled: リアルタイムプレビューを有効にするか
        """
        self.preview_enabled = enabled
        if enabled:
            self.set_status_message("リアルタイムプレビューが有効になりました", 2000)
        else:
            self.set_status_message("リアルタイムプレビューが無効になりました", 2000)

    def start_preview_calculation(self, calculation_func, parameters) -> None:
        """
        プレビュー用の低解像度計算を開始

        Args:
            calculation_func: 計算関数
            parameters: 計算パラメータ
        """
        if not self.preview_enabled or self.background_service.is_calculating():
            return

        # プレビュー用パラメータを作成
        preview_params = self.responsive_ui_manager.create_preview_parameters(parameters)

        # プレビュー計算を開始（プログレスダイアログは表示しない）
        self.background_service.start_calculation(
            calculation_func, preview_params, show_progress=False, parent_widget=self
        )

        self.set_status_message("プレビュー計算中...", 1000)

    def schedule_preview_update(self, calculation_func, parameters) -> None:
        """
        プレビュー更新をスケジュール（遅延実行）

        Args:
            calculation_func: 計算関数
            parameters: 計算パラメータ
        """
        import time
        self.last_parameter_change_time = time.time()

        # 既存のタイマーをリセット
        self.progressive_timer.stop()

        # 遅延後にプレビューを開始
        self.progressive_timer.timeout.disconnect()
        self.progressive_timer.timeout.connect(
            lambda: self._delayed_preview_start(calculation_func, parameters)
        )
        self.progressive_timer.start(self.preview_delay_ms)

    def _delayed_preview_start(self, calculation_func, parameters) -> None:
        """遅延後のプレビュー開始処理"""
        import time

        # パラメータ変更から十分時間が経過している場合のみ実行
        if time.time() - self.last_parameter_change_time >= (self.preview_delay_ms / 1000.0):
            self.start_preview_calculation(calculation_func, parameters)

    def _start_progressive_rendering(self) -> None:
        """プログレッシブレンダリングを開始"""
        # この関数は外部から設定される計算関数とパラメータで呼び出される
        # 実際の実装は統合時に完成される
        pass

    def start_progressive_calculation(self, calculation_func, parameters, stages: int = 4) -> None:
        """
        プログレッシブレンダリング計算を開始

        Args:
            calculation_func: 計算関数
            parameters: 計算パラメータ
            stages: プログレッシブレンダリングのステージ数
        """
        if self.background_service.is_calculating():
            return

        self.progressive_stages = stages
        self.progressive_current_stage = 0
        self.progressive_calculation_func = calculation_func
        self.progressive_original_params = parameters

        # 最初のステージを開始
        self._execute_progressive_stage()

    def _execute_progressive_stage(self) -> None:
        """プログレッシブレンダリングの現在ステージを実行"""
        if self.progressive_current_stage >= self.progressive_stages:
            return

        # 現在ステージ用のパラメータを作成
        stage_params = self.responsive_ui_manager.create_progressive_parameters(
            self.progressive_original_params,
            self.progressive_current_stage,
            self.progressive_stages
        )

        # ステージ計算を開始
        success = self.background_service.start_calculation(
            self.progressive_calculation_func,
            stage_params,
            show_progress=(self.progressive_current_stage == self.progressive_stages - 1),
            parent_widget=self
        )

        if success:
            stage_info = f"プログレッシブレンダリング ステージ {self.progressive_current_stage + 1}/{self.progressive_stages}"
            self.set_status_message(stage_info, 2000)

    def _on_progressive_stage_completed(self, result) -> None:
        """プログレッシブレンダリングのステージ完了処理"""
        # 結果を表示（フラクタルウィジェットに送信）
        # この部分は統合時に実装

        # 次のステージに進む
        self.progressive_current_stage += 1

        if self.progressive_current_stage < self.progressive_stages:
            # 次のステージを実行
            QTimer.singleShot(100, self._execute_progressive_stage)
        else:
            # 全ステージ完了
            self.set_status_message("プログレッシブレンダリング完了", 3000)

    def set_preview_delay(self, delay_ms: int) -> None:
        """
        プレビュー開始遅延時間を設定

        Args:
            delay_ms: 遅延時間（ミリ秒）
        """
        self.preview_delay_ms = max(100, delay_ms)  # 最小100ms

    def get_ui_responsiveness_info(self) -> dict:
        """UI応答性情報を取得"""
        responsiveness = self.responsive_ui_manager.monitor_ui_responsiveness()
        calculation_stats = self.get_calculation_statistics()

        return {
            'ui_responsiveness': responsiveness,
            'calculation_status': calculation_stats,
            'preview_enabled': self.preview_enabled,
            'preview_delay_ms': self.preview_delay_ms,
            'is_calculating': self.is_calculating()
        }

    def optimize_ui_performance(self) -> None:
        """UI パフォーマンスを最適化"""
        # システムパフォーマンスに基づいて設定を調整
        self.responsive_ui_manager.optimize_for_system_performance()

        # 応答性情報を取得
        responsiveness = self.responsive_ui_manager.monitor_ui_responsiveness()

        # パフォーマンスに基づいてプレビュー設定を調整
        if responsiveness['responsiveness'] == 'poor':
            self.set_preview_delay(1000)  # 遅延を増加
            self.responsive_ui_manager.enable_preview_mode(True, 0.2)  # より小さなプレビュー
        elif responsiveness['responsiveness'] == 'acceptable':
            self.set_preview_delay(750)
            self.responsive_ui_manager.enable_preview_mode(True, 0.25)
        else:
            self.set_preview_delay(500)  # デフォルト
            self.responsive_ui_manager.enable_preview_mode(True, 0.3)

        performance_msg = f"UI最適化完了 (応答性: {responsiveness['responsiveness']})"
        self.set_status_message(performance_msg, 3000)

    def _on_fractal_type_changed(self, fractal_type: str):
        """フラクタル種別が変更されたときの処理"""
        self._generate_and_display_fractal(fractal_type)

    def _on_parameter_changed(self, param_name, value):
        """パラメータが変更されたときの処理"""
        # 現在のフラクタル種別で再描画
        fractal_type = self.parameter_panel.get_current_fractal_type() if hasattr(self, 'parameter_panel') else 'mandelbrot'
        self._generate_and_display_fractal(fractal_type)

    def _generate_and_display_fractal(self, fractal_type: str):
        """指定された種別・パラメータでフラクタル画像を生成し表示"""
        # パラメータ取得
        params = self.parameter_panel.get_parameter_values() if hasattr(self, 'parameter_panel') else {}
        # 画像サイズをウィジェットから取得
        size = self.fractal_widget.size()
        width, height = size.width(), size.height()
        if width == 0 or height == 0:
            width, height = 600, 400  # 初期化時などサイズが0の場合のフォールバック

        # ウィジェットのアスペクト比に合わせて描画領域を調整
        aspect_ratio = width / height if height > 0 else 1.0
        center_real = -0.5
        height_complex = 3.0
        width_complex = height_complex * aspect_ratio

        region = ComplexRegion(
            top_left=ComplexNumber(center_real - width_complex / 2, height_complex / 2),
            bottom_right=ComplexNumber(center_real + width_complex / 2, -height_complex / 2)
        )
        max_iterations = params.get('max_iterations', 100)
        # FractalParameters生成
        fp = FractalParameters(
            image_size=(width, height),
            max_iterations=max_iterations,
            region=region,
            custom_parameters=params
        )
        # ジェネレータ選択
        if fractal_type == 'mandelbrot':
            generator = MandelbrotGenerator()
        elif fractal_type == 'julia':
            generator = JuliaGenerator()
        elif fractal_type == 'custom':
            formula = params.get('formula', 'z**2 + c')
            generator = CustomFormulaGenerator(formula)
        else:
            generator = MandelbrotGenerator()
        # 計算
        try:
            result = generator.calculate(fp)
            # iteration_dataを画像化
            img = self._iteration_data_to_qpixmap(result.iteration_data)
            self.fractal_widget.set_fractal_pixmap(img)
        except Exception as e:
            self.fractal_widget.show_error(str(e))

    def _iteration_data_to_qpixmap(self, iteration_data):
        """iteration_data(numpy配列)をQPixmapに変換"""
        import numpy as np
        from PyQt6.QtGui import QImage, QPixmap
        # 正規化してグレースケール画像化
        norm = (iteration_data.astype(np.float32) / iteration_data.max()) * 255.0
        arr = norm.astype(np.uint8)
        h, w = arr.shape
        qimg = QImage(arr.data, w, h, w, QImage.Format.Format_Grayscale8)
        return QPixmap.fromImage(qimg)
