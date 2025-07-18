"""
パラメータ調整UIの実装
動的パラメータUI生成とリアルタイムプレビュー更新機能を提供
"""

from PyQt6.QtWidgets import (
    QDockWidget, QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QSpinBox, QDoubleSpinBox, QSlider, QCheckBox, QLineEdit,
    QGroupBox, QPushButton, QComboBox, QScrollArea, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont
from typing import Dict, Any, List, Optional, Union
import math


class ParameterPanel(QDockWidget):
    """
    パラメータ調整用ドックウィジェット
    
    要件2.1, 2.2, 5.4に対応:
    - 動的パラメータUI生成システム
    - リアルタイムプレビュー更新
    - 直感的なパラメータ調整インターフェース
    """
    
    # シグナル定義
    parameter_changed = pyqtSignal(str, object)  # parameter_name, value
    parameters_reset = pyqtSignal()
    fractal_type_changed = pyqtSignal(str)
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__("パラメータ", parent)
        
        # ドックウィジェットの設定
        self.setObjectName("ParameterPanel")
        self.setMinimumWidth(280)
        self.setMaximumWidth(400)
        
        # メインウィジェットとレイアウト
        self.main_widget = QWidget()
        self.setWidget(self.main_widget)
        
        self.main_layout = QVBoxLayout(self.main_widget)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        self.main_layout.setSpacing(10)
        
        # パラメータ管理
        self.parameter_widgets: Dict[str, QWidget] = {}
        self.parameter_values: Dict[str, Any] = {}
        self.parameter_definitions: List = []
        
        # リアルタイム更新用タイマー
        self.update_timer = QTimer()
        self.update_timer.setSingleShot(True)
        self.update_timer.timeout.connect(self._emit_parameter_update)
        self.pending_updates: Dict[str, Any] = {}
        
        # UIの初期化
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """UIの初期設定"""
        # フラクタルタイプ選択
        self._setup_fractal_type_selector()
        
        # パラメータエリア（スクロール可能）
        self._setup_parameter_area()
        
        # コントロールボタン
        self._setup_control_buttons()
        
        # 初期状態の表示
        self._show_placeholder()
    
    def _setup_fractal_type_selector(self) -> None:
        """フラクタルタイプ選択UIを設定"""
        type_group = QGroupBox("フラクタルタイプ")
        type_layout = QVBoxLayout(type_group)
        
        self.fractal_type_combo = QComboBox()
        self.fractal_type_combo.addItems([
            "マンデルブロ集合",
            "ジュリア集合", 
            "カスタム式"
        ])
        self.fractal_type_combo.currentTextChanged.connect(self._on_fractal_type_changed)
        
        type_layout.addWidget(self.fractal_type_combo)
        self.main_layout.addWidget(type_group)
    
    def _setup_parameter_area(self) -> None:
        """パラメータ調整エリアを設定"""
        # スクロールエリア
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # パラメータコンテナ
        self.parameter_container = QWidget()
        self.parameter_layout = QVBoxLayout(self.parameter_container)
        self.parameter_layout.setContentsMargins(5, 5, 5, 5)
        self.parameter_layout.setSpacing(10)
        
        self.scroll_area.setWidget(self.parameter_container)
        self.main_layout.addWidget(self.scroll_area)
    
    def _setup_control_buttons(self) -> None:
        """コントロールボタンを設定"""
        button_layout = QHBoxLayout()
        
        # リセットボタン
        self.reset_button = QPushButton("リセット")
        self.reset_button.clicked.connect(self._reset_parameters)
        button_layout.addWidget(self.reset_button)
        
        # 適用ボタン
        self.apply_button = QPushButton("適用")
        self.apply_button.clicked.connect(self._apply_parameters)
        button_layout.addWidget(self.apply_button)
        
        self.main_layout.addLayout(button_layout)
    
    def _show_placeholder(self) -> None:
        """プレースホルダーを表示"""
        placeholder = QLabel("フラクタルタイプを選択してください")
        placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        placeholder.setStyleSheet("color: #888; font-style: italic;")
        self.parameter_layout.addWidget(placeholder)
    
    def _on_fractal_type_changed(self, fractal_type: str) -> None:
        """フラクタルタイプ変更時の処理"""
        # 英語名に変換
        type_mapping = {
            "マンデルブロ集合": "mandelbrot",
            "ジュリア集合": "julia",
            "カスタム式": "custom"
        }
        
        english_type = type_mapping.get(fractal_type, "mandelbrot")
        self.fractal_type_changed.emit(english_type)
    
    def set_parameter_definitions(self, definitions: List) -> None:
        """
        パラメータ定義を設定してUIを動的生成
        
        Args:
            definitions: ParameterDefinitionのリスト
        """
        self.parameter_definitions = definitions
        self._clear_parameters()
        self._generate_parameter_ui()
    
    def _clear_parameters(self) -> None:
        """既存のパラメータUIをクリア"""
        # 既存のウィジェットを削除
        for widget in self.parameter_widgets.values():
            widget.setParent(None)
            widget.deleteLater()
        
        # レイアウトをクリア
        while self.parameter_layout.count():
            child = self.parameter_layout.takeAt(0)
            if child.widget():
                child.widget().setParent(None)
                child.widget().deleteLater()
        
        self.parameter_widgets.clear()
        self.parameter_values.clear()
    
    def _generate_parameter_ui(self) -> None:
        """パラメータ定義に基づいてUIを動的生成"""
        if not self.parameter_definitions:
            self._show_placeholder()
            return
        
        for param_def in self.parameter_definitions:
            group_widget = self._create_parameter_group(param_def)
            if group_widget:
                self.parameter_layout.addWidget(group_widget)
        
        # 最後にストレッチを追加
        self.parameter_layout.addStretch()
    
    def _create_parameter_group(self, param_def) -> Optional[QGroupBox]:
        """個別パラメータのUIグループを作成"""
        group = QGroupBox(param_def.display_name)
        layout = QFormLayout(group)
        
        param_name = param_def.name
        param_type = param_def.parameter_type
        default_value = param_def.default_value
        
        # パラメータタイプに応じてウィジェットを作成
        widget = None
        
        if param_type == 'int':
            widget = self._create_int_widget(param_def)
        elif param_type == 'float':
            widget = self._create_float_widget(param_def)
        elif param_type == 'complex':
            widget = self._create_complex_widget(param_def)
        elif param_type == 'bool':
            widget = self._create_bool_widget(param_def)
        elif param_type == 'string' or param_type == 'formula':
            widget = self._create_string_widget(param_def)
        elif param_type == 'choice':
            widget = self._create_choice_widget(param_def)
        
        if widget:
            layout.addRow(widget)
            
            # 説明文があれば追加
            if param_def.description:
                desc_label = QLabel(param_def.description)
                desc_label.setWordWrap(True)
                desc_label.setStyleSheet("color: #666; font-size: 11px;")
                layout.addRow(desc_label)
            
            self.parameter_widgets[param_name] = widget
            self.parameter_values[param_name] = default_value
            
            return group
        
        return None
    
    def _create_int_widget(self, param_def) -> QWidget:
        """整数パラメータ用ウィジェット作成"""
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # スピンボックス
        spinbox = QSpinBox()
        spinbox.setValue(param_def.default_value)
        
        if param_def.min_value is not None:
            spinbox.setMinimum(param_def.min_value)
        else:
            spinbox.setMinimum(-999999)
            
        if param_def.max_value is not None:
            spinbox.setMaximum(param_def.max_value)
        else:
            spinbox.setMaximum(999999)
        
        spinbox.valueChanged.connect(
            lambda value: self._on_parameter_changed(param_def.name, value)
        )
        
        layout.addWidget(spinbox)
        
        # 特定のパラメータにはスライダーも追加
        if param_def.name in ['max_iterations', 'image_width', 'image_height']:
            slider = QSlider(Qt.Orientation.Horizontal)
            slider.setMinimum(spinbox.minimum())
            slider.setMaximum(min(spinbox.maximum(), 2000))  # スライダーの最大値を制限
            slider.setValue(param_def.default_value)
            
            # スピンボックスとスライダーを同期
            spinbox.valueChanged.connect(slider.setValue)
            slider.valueChanged.connect(spinbox.setValue)
            
            layout.addWidget(slider)
        
        return container
    
    def _create_float_widget(self, param_def) -> QWidget:
        """浮動小数点パラメータ用ウィジェット作成"""
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        
        spinbox = QDoubleSpinBox()
        spinbox.setValue(param_def.default_value)
        spinbox.setDecimals(6)
        
        if param_def.min_value is not None:
            spinbox.setMinimum(param_def.min_value)
        else:
            spinbox.setMinimum(-999999.0)
            
        if param_def.max_value is not None:
            spinbox.setMaximum(param_def.max_value)
        else:
            spinbox.setMaximum(999999.0)
        
        spinbox.valueChanged.connect(
            lambda value: self._on_parameter_changed(param_def.name, value)
        )
        
        layout.addWidget(spinbox)
        return container
    
    def _create_complex_widget(self, param_def) -> QWidget:
        """複素数パラメータ用ウィジェット作成"""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 実部
        real_layout = QHBoxLayout()
        real_layout.addWidget(QLabel("実部:"))
        real_spinbox = QDoubleSpinBox()
        real_spinbox.setDecimals(6)
        real_spinbox.setMinimum(-999.0)
        real_spinbox.setMaximum(999.0)
        
        if hasattr(param_def.default_value, 'real'):
            real_spinbox.setValue(param_def.default_value.real)
        else:
            real_spinbox.setValue(0.0)
        
        real_layout.addWidget(real_spinbox)
        layout.addLayout(real_layout)
        
        # 虚部
        imag_layout = QHBoxLayout()
        imag_layout.addWidget(QLabel("虚部:"))
        imag_spinbox = QDoubleSpinBox()
        imag_spinbox.setDecimals(6)
        imag_spinbox.setMinimum(-999.0)
        imag_spinbox.setMaximum(999.0)
        
        if hasattr(param_def.default_value, 'imag'):
            imag_spinbox.setValue(param_def.default_value.imag)
        else:
            imag_spinbox.setValue(0.0)
        
        imag_layout.addWidget(imag_spinbox)
        layout.addLayout(imag_layout)
        
        # 値変更時のコールバック
        def on_complex_changed():
            complex_value = complex(real_spinbox.value(), imag_spinbox.value())
            self._on_parameter_changed(param_def.name, complex_value)
        
        real_spinbox.valueChanged.connect(on_complex_changed)
        imag_spinbox.valueChanged.connect(on_complex_changed)
        
        # ウィジェットを保存（後でアクセスするため）
        container.real_spinbox = real_spinbox
        container.imag_spinbox = imag_spinbox
        
        return container
    
    def _create_bool_widget(self, param_def) -> QWidget:
        """ブールパラメータ用ウィジェット作成"""
        checkbox = QCheckBox(param_def.display_name)
        checkbox.setChecked(param_def.default_value)
        
        checkbox.toggled.connect(
            lambda checked: self._on_parameter_changed(param_def.name, checked)
        )
        
        return checkbox
    
    def _create_string_widget(self, param_def) -> QWidget:
        """文字列パラメータ用ウィジェット作成"""
        line_edit = QLineEdit()
        line_edit.setText(str(param_def.default_value))
        
        if param_def.parameter_type == 'formula':
            # 数式用のフォント設定
            font = QFont("Consolas", 10)
            line_edit.setFont(font)
            line_edit.setPlaceholderText("例: z**2 + c")
        
        line_edit.textChanged.connect(
            lambda text: self._on_parameter_changed(param_def.name, text)
        )
        
        return line_edit
    
    def _create_choice_widget(self, param_def) -> QWidget:
        """選択肢パラメータ用ウィジェット作成"""
        combo = QComboBox()
        
        # 選択肢を追加（param_def.choicesがあると仮定）
        if hasattr(param_def, 'choices') and param_def.choices:
            combo.addItems(param_def.choices)
            if param_def.default_value in param_def.choices:
                combo.setCurrentText(param_def.default_value)
        
        combo.currentTextChanged.connect(
            lambda text: self._on_parameter_changed(param_def.name, text)
        )
        
        return combo
    
    def _on_parameter_changed(self, param_name: str, value: Any) -> None:
        """パラメータ値変更時の処理"""
        self.parameter_values[param_name] = value
        
        # リアルタイム更新のためにタイマーをスケジュール
        self.pending_updates[param_name] = value
        self.update_timer.start(300)  # 300ms後に更新
    
    def _emit_parameter_update(self) -> None:
        """パラメータ更新シグナルを発信"""
        for param_name, value in self.pending_updates.items():
            self.parameter_changed.emit(param_name, value)
        
        self.pending_updates.clear()
    
    def _reset_parameters(self) -> None:
        """パラメータをデフォルト値にリセット"""
        for param_def in self.parameter_definitions:
            param_name = param_def.name
            default_value = param_def.default_value
            
            # UIウィジェットの値を更新
            if param_name in self.parameter_widgets:
                widget = self.parameter_widgets[param_name]
                self._set_widget_value(widget, param_def, default_value)
            
            self.parameter_values[param_name] = default_value
        
        self.parameters_reset.emit()
    
    def _apply_parameters(self) -> None:
        """現在のパラメータ値を即座に適用"""
        for param_name, value in self.parameter_values.items():
            self.parameter_changed.emit(param_name, value)
    
    def _set_widget_value(self, widget: QWidget, param_def, value: Any) -> None:
        """ウィジェットの値を設定"""
        param_type = param_def.parameter_type
        
        if param_type == 'int':
            if hasattr(widget, 'children'):
                for child in widget.children():
                    if isinstance(child, QSpinBox):
                        child.setValue(value)
                        break
        elif param_type == 'float':
            if hasattr(widget, 'children'):
                for child in widget.children():
                    if isinstance(child, QDoubleSpinBox):
                        child.setValue(value)
                        break
        elif param_type == 'complex':
            if hasattr(widget, 'real_spinbox') and hasattr(widget, 'imag_spinbox'):
                widget.real_spinbox.setValue(value.real if hasattr(value, 'real') else 0.0)
                widget.imag_spinbox.setValue(value.imag if hasattr(value, 'imag') else 0.0)
        elif param_type == 'bool':
            if isinstance(widget, QCheckBox):
                widget.setChecked(value)
        elif param_type in ['string', 'formula']:
            if isinstance(widget, QLineEdit):
                widget.setText(str(value))
        elif param_type == 'choice':
            if isinstance(widget, QComboBox):
                widget.setCurrentText(str(value))
    
    def get_parameter_values(self) -> Dict[str, Any]:
        """現在のパラメータ値を取得"""
        return self.parameter_values.copy()
    
    def set_parameter_value(self, param_name: str, value: Any) -> None:
        """特定のパラメータ値を設定"""
        if param_name in self.parameter_values:
            self.parameter_values[param_name] = value
            
            # 対応するウィジェットも更新
            if param_name in self.parameter_widgets:
                param_def = next(
                    (p for p in self.parameter_definitions if p.name == param_name), 
                    None
                )
                if param_def:
                    widget = self.parameter_widgets[param_name]
                    self._set_widget_value(widget, param_def, value)
    
    def enable_realtime_update(self, enabled: bool = True) -> None:
        """リアルタイム更新の有効/無効を切り替え"""
        if enabled:
            self.update_timer.setInterval(300)
        else:
            self.update_timer.stop()
    
    def get_current_fractal_type(self) -> str:
        """現在選択されているフラクタルタイプを取得"""
        type_mapping = {
            "マンデルブロ集合": "mandelbrot",
            "ジュリア集合": "julia",
            "カスタム式": "custom"
        }
        
        current_text = self.fractal_type_combo.currentText()
        return type_mapping.get(current_text, "mandelbrot")