"""
メインウィンドウの実装
PyQt6を使用したフラクタルエディタのメインウィンドウ
"""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QMenuBar, QToolBar, QStatusBar, QDockWidget,
    QLabel, QProgressBar, QSplitter
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QIcon, QKeySequence, QAction
from typing import Optional

from .formula_editor import FormulaEditorWidget


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
        
        # フラクタル表示エリア用のプレースホルダー
        self.fractal_display_area = QWidget()
        self.fractal_display_area.setMinimumSize(400, 300)
        self.fractal_display_area.setStyleSheet("""
            QWidget {
                background-color: #2b2b2b;
                border: 1px solid #555;
            }
        """)
        
        # プレースホルダーラベル
        placeholder_layout = QVBoxLayout(self.fractal_display_area)
        placeholder_label = QLabel("フラクタル表示エリア")
        placeholder_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        placeholder_label.setStyleSheet("color: #888; font-size: 14px;")
        placeholder_layout.addWidget(placeholder_label)
        
        self.main_splitter.addWidget(self.fractal_display_area)
    
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
        self.status_label = QLabel("準備完了")
        status_bar.addWidget(self.status_label)
        
        # 中央：進行状況バー（通常は非表示）
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setMaximumWidth(200)
        status_bar.addPermanentWidget(self.progress_bar)
        
        # 右側：計算時間表示
        self.calculation_time_label = QLabel("")
        status_bar.addPermanentWidget(self.calculation_time_label)
        
        # 初期メッセージ
        status_bar.showMessage("フラクタルエディタへようこそ", 3000)
    
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
        return self.fractal_display_area
    
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