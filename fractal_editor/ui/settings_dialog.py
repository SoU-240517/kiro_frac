"""
設定ダイアログUI

アプリケーション設定を変更するためのダイアログウィンドウを提供します。
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget,
    QLabel, QSpinBox, QDoubleSpinBox, QCheckBox, QComboBox,
    QPushButton, QGroupBox, QGridLayout, QSlider, QLineEdit,
    QMessageBox, QFileDialog, QProgressBar
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QIcon
from typing import Optional

from ..models.app_settings import AppSettings, SettingsManager


class SettingsDialog(QDialog):
    """設定ダイアログクラス"""
    
    # 設定変更時に発行されるシグナル
    settings_changed = pyqtSignal(AppSettings)
    
    def __init__(self, settings_manager: SettingsManager, parent=None):
        super().__init__(parent)
        self.settings_manager = settings_manager
        self.current_settings = settings_manager.get_settings()
        self.temp_settings = AppSettings(**self.current_settings.to_dict())
        
        self.init_ui()
        self.load_settings_to_ui()
        
    def init_ui(self):
        """UIを初期化"""
        self.setWindowTitle("環境設定")
        self.setModal(True)
        self.resize(600, 500)
        
        # メインレイアウト
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)
        
        # タブウィジェット
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)
        
        # 各タブを作成
        self.create_general_tab()
        self.create_rendering_tab()
        self.create_performance_tab()
        self.create_ui_tab()
        self.create_export_tab()
        
        # ボタンレイアウト
        button_layout = QHBoxLayout()
        
        # デフォルトに戻すボタン
        self.reset_button = QPushButton("デフォルトに戻す")
        self.reset_button.clicked.connect(self.reset_to_defaults)
        button_layout.addWidget(self.reset_button)
        
        # バックアップボタン
        self.backup_button = QPushButton("設定をバックアップ")
        self.backup_button.clicked.connect(self.backup_settings)
        button_layout.addWidget(self.backup_button)
        
        # 復元ボタン
        self.restore_button = QPushButton("バックアップから復元")
        self.restore_button.clicked.connect(self.restore_settings)
        button_layout.addWidget(self.restore_button)
        
        button_layout.addStretch()
        
        # OK/キャンセルボタン
        self.ok_button = QPushButton("OK")
        self.ok_button.clicked.connect(self.accept_settings)
        button_layout.addWidget(self.ok_button)
        
        self.cancel_button = QPushButton("キャンセル")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)
        
        main_layout.addLayout(button_layout)
    
    def create_general_tab(self):
        """一般設定タブを作成"""
        tab = QWidget()
        layout = QVBoxLayout()
        tab.setLayout(layout)
        
        # フラクタル計算設定グループ
        fractal_group = QGroupBox("フラクタル計算設定")
        fractal_layout = QGridLayout()
        fractal_group.setLayout(fractal_layout)
        
        # デフォルト最大反復回数
        fractal_layout.addWidget(QLabel("デフォルト最大反復回数:"), 0, 0)
        self.max_iterations_spin = QSpinBox()
        self.max_iterations_spin.setRange(10, 10000)
        self.max_iterations_spin.setSuffix(" 回")
        fractal_layout.addWidget(self.max_iterations_spin, 0, 1)
        
        # デフォルト画像サイズ
        fractal_layout.addWidget(QLabel("デフォルト画像サイズ:"), 1, 0)
        size_layout = QHBoxLayout()
        self.image_width_spin = QSpinBox()
        self.image_width_spin.setRange(100, 4000)
        self.image_width_spin.setSuffix(" px")
        size_layout.addWidget(self.image_width_spin)
        size_layout.addWidget(QLabel("×"))
        self.image_height_spin = QSpinBox()
        self.image_height_spin.setRange(100, 4000)
        self.image_height_spin.setSuffix(" px")
        size_layout.addWidget(self.image_height_spin)
        fractal_layout.addLayout(size_layout, 1, 1)
        
        # デフォルトカラーパレット
        fractal_layout.addWidget(QLabel("デフォルトカラーパレット:"), 2, 0)
        self.color_palette_combo = QComboBox()
        self.color_palette_combo.addItems([
            "Rainbow", "Grayscale", "Hot", "Cool", "Plasma", "Viridis"
        ])
        fractal_layout.addWidget(self.color_palette_combo, 2, 1)
        
        layout.addWidget(fractal_group)
        layout.addStretch()
        
        self.tab_widget.addTab(tab, "一般")
    
    def create_rendering_tab(self):
        """レンダリング設定タブを作成"""
        tab = QWidget()
        layout = QVBoxLayout()
        tab.setLayout(layout)
        
        # レンダリング設定グループ
        rendering_group = QGroupBox("レンダリング設定")
        rendering_layout = QGridLayout()
        rendering_group.setLayout(rendering_layout)
        
        # アンチエイリアシング
        self.anti_aliasing_check = QCheckBox("アンチエイリアシングを有効にする")
        rendering_layout.addWidget(self.anti_aliasing_check, 0, 0, 1, 2)
        
        # 明度調整
        rendering_layout.addWidget(QLabel("明度調整:"), 1, 0)
        brightness_layout = QHBoxLayout()
        self.brightness_slider = QSlider(Qt.Orientation.Horizontal)
        self.brightness_slider.setRange(10, 300)
        self.brightness_slider.setValue(100)
        self.brightness_label = QLabel("1.0")
        self.brightness_slider.valueChanged.connect(
            lambda v: self.brightness_label.setText(f"{v/100:.1f}")
        )
        brightness_layout.addWidget(self.brightness_slider)
        brightness_layout.addWidget(self.brightness_label)
        rendering_layout.addLayout(brightness_layout, 1, 1)
        
        # コントラスト調整
        rendering_layout.addWidget(QLabel("コントラスト調整:"), 2, 0)
        contrast_layout = QHBoxLayout()
        self.contrast_slider = QSlider(Qt.Orientation.Horizontal)
        self.contrast_slider.setRange(10, 300)
        self.contrast_slider.setValue(100)
        self.contrast_label = QLabel("1.0")
        self.contrast_slider.valueChanged.connect(
            lambda v: self.contrast_label.setText(f"{v/100:.1f}")
        )
        contrast_layout.addWidget(self.contrast_slider)
        contrast_layout.addWidget(self.contrast_label)
        rendering_layout.addLayout(contrast_layout, 2, 1)
        
        layout.addWidget(rendering_group)
        layout.addStretch()
        
        self.tab_widget.addTab(tab, "レンダリング")
    
    def create_performance_tab(self):
        """パフォーマンス設定タブを作成"""
        tab = QWidget()
        layout = QVBoxLayout()
        tab.setLayout(layout)
        
        # パフォーマンス設定グループ
        performance_group = QGroupBox("パフォーマンス設定")
        performance_layout = QGridLayout()
        performance_group.setLayout(performance_layout)
        
        # スレッド数
        performance_layout.addWidget(QLabel("計算スレッド数:"), 0, 0)
        self.thread_count_spin = QSpinBox()
        self.thread_count_spin.setRange(1, 32)
        performance_layout.addWidget(self.thread_count_spin, 0, 1)
        
        # 並列計算
        self.parallel_computation_check = QCheckBox("並列計算を有効にする")
        performance_layout.addWidget(self.parallel_computation_check, 1, 0, 1, 2)
        
        # メモリ制限
        performance_layout.addWidget(QLabel("メモリ制限:"), 2, 0)
        self.memory_limit_spin = QSpinBox()
        self.memory_limit_spin.setRange(128, 8192)
        self.memory_limit_spin.setSuffix(" MB")
        performance_layout.addWidget(self.memory_limit_spin, 2, 1)
        
        layout.addWidget(performance_group)
        layout.addStretch()
        
        self.tab_widget.addTab(tab, "パフォーマンス")
    
    def create_ui_tab(self):
        """UI設定タブを作成"""
        tab = QWidget()
        layout = QVBoxLayout()
        tab.setLayout(layout)
        
        # UI設定グループ
        ui_group = QGroupBox("ユーザーインターフェース設定")
        ui_layout = QGridLayout()
        ui_group.setLayout(ui_layout)
        
        # 自動保存間隔
        ui_layout.addWidget(QLabel("自動保存間隔:"), 0, 0)
        self.auto_save_spin = QSpinBox()
        self.auto_save_spin.setRange(30, 3600)
        self.auto_save_spin.setSuffix(" 秒")
        ui_layout.addWidget(self.auto_save_spin, 0, 1)
        
        # 最近使用したプロジェクト数
        ui_layout.addWidget(QLabel("最近使用したプロジェクト数:"), 1, 0)
        self.recent_projects_spin = QSpinBox()
        self.recent_projects_spin.setRange(1, 50)
        ui_layout.addWidget(self.recent_projects_spin, 1, 1)
        
        # 計算進行状況表示
        self.show_progress_check = QCheckBox("計算進行状況を表示する")
        ui_layout.addWidget(self.show_progress_check, 2, 0, 1, 2)
        
        # リアルタイムプレビュー
        self.realtime_preview_check = QCheckBox("リアルタイムプレビューを有効にする")
        ui_layout.addWidget(self.realtime_preview_check, 3, 0, 1, 2)
        
        layout.addWidget(ui_group)
        layout.addStretch()
        
        self.tab_widget.addTab(tab, "UI")
    
    def create_export_tab(self):
        """エクスポート設定タブを作成"""
        tab = QWidget()
        layout = QVBoxLayout()
        tab.setLayout(layout)
        
        # エクスポート設定グループ
        export_group = QGroupBox("エクスポート設定")
        export_layout = QGridLayout()
        export_group.setLayout(export_layout)
        
        # デフォルトエクスポート形式
        export_layout.addWidget(QLabel("デフォルトエクスポート形式:"), 0, 0)
        self.export_format_combo = QComboBox()
        self.export_format_combo.addItems(["PNG", "JPEG", "BMP", "TIFF"])
        export_layout.addWidget(self.export_format_combo, 0, 1)
        
        # デフォルトエクスポート品質
        export_layout.addWidget(QLabel("デフォルトエクスポート品質:"), 1, 0)
        quality_layout = QHBoxLayout()
        self.export_quality_slider = QSlider(Qt.Orientation.Horizontal)
        self.export_quality_slider.setRange(1, 100)
        self.export_quality_label = QLabel("95")
        self.export_quality_slider.valueChanged.connect(
            lambda v: self.export_quality_label.setText(str(v))
        )
        quality_layout.addWidget(self.export_quality_slider)
        quality_layout.addWidget(self.export_quality_label)
        export_layout.addLayout(quality_layout, 1, 1)
        
        # 自動バックアップ
        self.auto_backup_check = QCheckBox("自動バックアップを有効にする")
        export_layout.addWidget(self.auto_backup_check, 2, 0, 1, 2)
        
        layout.addWidget(export_group)
        layout.addStretch()
        
        self.tab_widget.addTab(tab, "エクスポート")
    
    def load_settings_to_ui(self):
        """現在の設定をUIに読み込み"""
        settings = self.temp_settings
        
        # 一般設定
        self.max_iterations_spin.setValue(settings.default_max_iterations)
        self.image_width_spin.setValue(settings.default_image_size[0])
        self.image_height_spin.setValue(settings.default_image_size[1])
        
        # カラーパレット
        index = self.color_palette_combo.findText(settings.default_color_palette)
        if index >= 0:
            self.color_palette_combo.setCurrentIndex(index)
        
        # レンダリング設定
        self.anti_aliasing_check.setChecked(settings.enable_anti_aliasing)
        self.brightness_slider.setValue(int(settings.brightness_adjustment * 100))
        self.contrast_slider.setValue(int(settings.contrast_adjustment * 100))
        
        # パフォーマンス設定
        self.thread_count_spin.setValue(settings.thread_count)
        self.parallel_computation_check.setChecked(settings.enable_parallel_computation)
        self.memory_limit_spin.setValue(settings.memory_limit_mb)
        
        # UI設定
        self.auto_save_spin.setValue(settings.auto_save_interval)
        self.recent_projects_spin.setValue(settings.recent_projects_count)
        self.show_progress_check.setChecked(settings.show_calculation_progress)
        self.realtime_preview_check.setChecked(settings.enable_realtime_preview)
        
        # エクスポート設定
        export_index = self.export_format_combo.findText(settings.default_export_format)
        if export_index >= 0:
            self.export_format_combo.setCurrentIndex(export_index)
        self.export_quality_slider.setValue(settings.default_export_quality)
        self.auto_backup_check.setChecked(settings.auto_backup_enabled)
    
    def save_ui_to_settings(self):
        """UIの値を設定に保存"""
        # 一般設定
        self.temp_settings.default_max_iterations = self.max_iterations_spin.value()
        self.temp_settings.default_image_size = (
            self.image_width_spin.value(),
            self.image_height_spin.value()
        )
        self.temp_settings.default_color_palette = self.color_palette_combo.currentText()
        
        # レンダリング設定
        self.temp_settings.enable_anti_aliasing = self.anti_aliasing_check.isChecked()
        self.temp_settings.brightness_adjustment = self.brightness_slider.value() / 100.0
        self.temp_settings.contrast_adjustment = self.contrast_slider.value() / 100.0
        
        # パフォーマンス設定
        self.temp_settings.thread_count = self.thread_count_spin.value()
        self.temp_settings.enable_parallel_computation = self.parallel_computation_check.isChecked()
        self.temp_settings.memory_limit_mb = self.memory_limit_spin.value()
        
        # UI設定
        self.temp_settings.auto_save_interval = self.auto_save_spin.value()
        self.temp_settings.recent_projects_count = self.recent_projects_spin.value()
        self.temp_settings.show_calculation_progress = self.show_progress_check.isChecked()
        self.temp_settings.enable_realtime_preview = self.realtime_preview_check.isChecked()
        
        # エクスポート設定
        self.temp_settings.default_export_format = self.export_format_combo.currentText()
        self.temp_settings.default_export_quality = self.export_quality_slider.value()
        self.temp_settings.auto_backup_enabled = self.auto_backup_check.isChecked()
    
    def accept_settings(self):
        """設定を適用してダイアログを閉じる"""
        self.save_ui_to_settings()
        
        # 設定の妥当性を検証
        if not self.temp_settings.validate():
            QMessageBox.warning(
                self,
                "設定エラー",
                "入力された設定値に問題があります。値を確認してください。"
            )
            return
        
        # 設定を保存
        if self.settings_manager.save_settings(self.temp_settings):
            self.settings_changed.emit(self.temp_settings)
            self.accept()
        else:
            QMessageBox.critical(
                self,
                "保存エラー",
                "設定の保存に失敗しました。"
            )
    
    def reset_to_defaults(self):
        """設定をデフォルト値にリセット"""
        reply = QMessageBox.question(
            self,
            "設定リセット",
            "すべての設定をデフォルト値に戻しますか？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.temp_settings = AppSettings()
            self.load_settings_to_ui()
    
    def backup_settings(self):
        """設定をバックアップ"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "設定をバックアップ",
            "fractal_editor_settings_backup.json",
            "JSON Files (*.json)"
        )
        
        if file_path:
            if self.settings_manager.backup_settings(file_path):
                QMessageBox.information(
                    self,
                    "バックアップ完了",
                    f"設定のバックアップが完了しました。\n{file_path}"
                )
            else:
                QMessageBox.critical(
                    self,
                    "バックアップエラー",
                    "設定のバックアップに失敗しました。"
                )
    
    def restore_settings(self):
        """バックアップから設定を復元"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "バックアップから復元",
            "",
            "JSON Files (*.json)"
        )
        
        if file_path:
            reply = QMessageBox.question(
                self,
                "設定復元",
                "現在の設定を上書きしてバックアップから復元しますか？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                if self.settings_manager.restore_from_backup(file_path):
                    self.temp_settings = self.settings_manager.get_settings()
                    self.load_settings_to_ui()
                    QMessageBox.information(
                        self,
                        "復元完了",
                        "設定の復元が完了しました。"
                    )
                else:
                    QMessageBox.critical(
                        self,
                        "復元エラー",
                        "設定の復元に失敗しました。"
                    )