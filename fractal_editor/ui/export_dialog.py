"""
画像エクスポートダイアログの実装
PNG、JPEG形式での画像出力と解像度指定機能を提供
"""

import os
from typing import Optional, Tuple, Dict, Any
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QPushButton, QComboBox, QSpinBox,
    QCheckBox, QSlider, QGroupBox, QFileDialog,
    QProgressDialog, QMessageBox, QDoubleSpinBox,
    QButtonGroup, QRadioButton
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QPixmap, QIcon
import numpy as np

from ..services.image_renderer import RenderSettings, RenderingEngine


class ExportProgressDialog(QProgressDialog):
    """高解像度画像生成の進行状況表示ダイアログ"""
    
    def __init__(self, parent=None):
        super().__init__("画像を生成中...", "キャンセル", 0, 100, parent)
        self.setWindowTitle("画像エクスポート")
        self.setWindowModality(Qt.WindowModality.WindowModal)
        self.setMinimumDuration(1000)  # 1秒後に表示
        self.setAutoClose(True)
        self.setAutoReset(True)
        
        # キャンセル処理
        self.canceled.connect(self._on_canceled)
        self._is_canceled = False
    
    def _on_canceled(self):
        """キャンセルボタンが押された時の処理"""
        self._is_canceled = True
        self.setLabelText("キャンセル中...")
    
    def is_canceled(self) -> bool:
        """キャンセルされたかどうかを確認"""
        return self._is_canceled
    
    def update_progress(self, value: int, message: str = None):
        """進行状況を更新"""
        if not self._is_canceled:
            self.setValue(value)
            if message:
                self.setLabelText(message)


class ImageExportWorker(QThread):
    """画像エクスポート処理を別スレッドで実行するワーカー"""
    
    progress_updated = pyqtSignal(int, str)  # 進行状況, メッセージ
    export_completed = pyqtSignal(str)  # 成功時のファイルパス
    export_failed = pyqtSignal(str)  # エラーメッセージ
    
    def __init__(self, iteration_data: np.ndarray, max_iterations: int,
                 filepath: str, export_settings: Dict[str, Any]):
        super().__init__()
        self.iteration_data = iteration_data
        self.max_iterations = max_iterations
        self.filepath = filepath
        self.export_settings = export_settings
        self._is_canceled = False
    
    def cancel(self):
        """エクスポート処理をキャンセル"""
        self._is_canceled = True
    
    def run(self):
        """エクスポート処理を実行"""
        try:
            self.progress_updated.emit(10, "レンダリングエンジンを初期化中...")
            
            if self._is_canceled:
                return
            
            # レンダリングエンジンを初期化
            rendering_engine = RenderingEngine()
            
            self.progress_updated.emit(20, "レンダリング設定を適用中...")
            
            # レンダリング設定を作成
            render_settings = RenderSettings(
                anti_aliasing=self.export_settings.get('anti_aliasing', True),
                brightness=self.export_settings.get('brightness', 1.0),
                contrast=self.export_settings.get('contrast', 1.0),
                gamma=self.export_settings.get('gamma', 1.0)
            )
            
            if self._is_canceled:
                return
            
            self.progress_updated.emit(40, "画像を生成中...")
            
            # 画像をエクスポート
            rendering_engine.export_image(
                iteration_data=self.iteration_data,
                max_iterations=self.max_iterations,
                filepath=self.filepath,
                high_resolution=self.export_settings.get('high_resolution', False),
                scale_factor=self.export_settings.get('scale_factor', 2),
                quality=self.export_settings.get('quality', 95),
                settings=render_settings
            )
            
            if self._is_canceled:
                return
            
            self.progress_updated.emit(90, "ファイルを保存中...")
            
            # 少し待機（ファイル書き込み完了を確認）
            self.msleep(500)
            
            if self._is_canceled:
                return
            
            self.progress_updated.emit(100, "完了")
            self.export_completed.emit(self.filepath)
            
        except Exception as e:
            self.export_failed.emit(str(e))


class ImageExportDialog(QDialog):
    """
    画像エクスポートダイアログ
    
    要件4.1-4.5に対応:
    - PNG、JPEG形式での画像出力
    - 解像度指定機能
    - ファイル形式選択ダイアログ
    - 高解像度画像生成の進行状況表示
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("画像エクスポート")
        self.setModal(True)
        self.resize(500, 600)
        
        # エクスポート用データ
        self.iteration_data: Optional[np.ndarray] = None
        self.max_iterations: int = 1000
        
        # ワーカースレッド
        self.export_worker: Optional[ImageExportWorker] = None
        self.progress_dialog: Optional[ExportProgressDialog] = None
        
        self._setup_ui()
        self._connect_signals()
        self._load_default_settings()
    
    def _setup_ui(self):
        """UIを設定"""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        
        # ファイル設定グループ
        file_group = self._create_file_settings_group()
        layout.addWidget(file_group)
        
        # 画像設定グループ
        image_group = self._create_image_settings_group()
        layout.addWidget(image_group)
        
        # レンダリング設定グループ
        render_group = self._create_render_settings_group()
        layout.addWidget(render_group)
        
        # プレビューグループ
        preview_group = self._create_preview_group()
        layout.addWidget(preview_group)
        
        # ボタン
        button_layout = self._create_button_layout()
        layout.addLayout(button_layout)
    
    def _create_file_settings_group(self) -> QGroupBox:
        """ファイル設定グループを作成"""
        group = QGroupBox("ファイル設定")
        layout = QGridLayout(group)
        
        # ファイルパス
        layout.addWidget(QLabel("保存先:"), 0, 0)
        self.filepath_edit = QLineEdit()
        self.filepath_edit.setPlaceholderText("エクスポートするファイルのパスを選択...")
        layout.addWidget(self.filepath_edit, 0, 1)
        
        self.browse_button = QPushButton("参照...")
        self.browse_button.clicked.connect(self._browse_file)
        layout.addWidget(self.browse_button, 0, 2)
        
        # ファイル形式
        layout.addWidget(QLabel("形式:"), 1, 0)
        self.format_combo = QComboBox()
        self.format_combo.addItems(["PNG (*.png)", "JPEG (*.jpg)"])
        self.format_combo.currentTextChanged.connect(self._on_format_changed)
        layout.addWidget(self.format_combo, 1, 1, 1, 2)
        
        return group
    
    def _create_image_settings_group(self) -> QGroupBox:
        """画像設定グループを作成"""
        group = QGroupBox("画像設定")
        layout = QGridLayout(group)
        
        # 解像度設定
        layout.addWidget(QLabel("解像度:"), 0, 0)
        
        # 解像度タイプ選択
        self.resolution_group = QButtonGroup()
        
        self.standard_radio = QRadioButton("標準解像度")
        self.standard_radio.setChecked(True)
        self.resolution_group.addButton(self.standard_radio, 0)
        layout.addWidget(self.standard_radio, 0, 1)
        
        self.high_res_radio = QRadioButton("高解像度")
        self.resolution_group.addButton(self.high_res_radio, 1)
        layout.addWidget(self.high_res_radio, 0, 2)
        
        # 標準解像度設定
        layout.addWidget(QLabel("幅:"), 1, 0)
        self.width_spin = QSpinBox()
        self.width_spin.setRange(100, 8192)
        self.width_spin.setValue(1920)
        self.width_spin.setSuffix(" px")
        layout.addWidget(self.width_spin, 1, 1)
        
        layout.addWidget(QLabel("高さ:"), 1, 2)
        self.height_spin = QSpinBox()
        self.height_spin.setRange(100, 8192)
        self.height_spin.setValue(1080)
        self.height_spin.setSuffix(" px")
        layout.addWidget(self.height_spin, 1, 3)
        
        # 高解像度設定
        layout.addWidget(QLabel("倍率:"), 2, 0)
        self.scale_spin = QSpinBox()
        self.scale_spin.setRange(2, 8)
        self.scale_spin.setValue(2)
        self.scale_spin.setSuffix("x")
        self.scale_spin.setEnabled(False)
        layout.addWidget(self.scale_spin, 2, 1)
        
        # JPEG品質設定
        layout.addWidget(QLabel("JPEG品質:"), 3, 0)
        self.quality_spin = QSpinBox()
        self.quality_spin.setRange(1, 100)
        self.quality_spin.setValue(95)
        self.quality_spin.setSuffix("%")
        self.quality_spin.setEnabled(False)  # 初期状態ではPNGが選択されているため無効
        layout.addWidget(self.quality_spin, 3, 1)
        
        # 解像度タイプ変更時の処理
        self.resolution_group.buttonToggled.connect(self._on_resolution_type_changed)
        
        return group
    
    def _create_render_settings_group(self) -> QGroupBox:
        """レンダリング設定グループを作成"""
        group = QGroupBox("レンダリング設定")
        layout = QGridLayout(group)
        
        # アンチエイリアシング
        self.anti_aliasing_check = QCheckBox("アンチエイリアシング")
        self.anti_aliasing_check.setChecked(True)
        layout.addWidget(self.anti_aliasing_check, 0, 0, 1, 2)
        
        # 明度調整
        layout.addWidget(QLabel("明度:"), 1, 0)
        self.brightness_spin = QDoubleSpinBox()
        self.brightness_spin.setRange(0.1, 2.0)
        self.brightness_spin.setValue(1.0)
        self.brightness_spin.setSingleStep(0.1)
        self.brightness_spin.setDecimals(1)
        layout.addWidget(self.brightness_spin, 1, 1)
        
        # コントラスト調整
        layout.addWidget(QLabel("コントラスト:"), 2, 0)
        self.contrast_spin = QDoubleSpinBox()
        self.contrast_spin.setRange(0.1, 2.0)
        self.contrast_spin.setValue(1.0)
        self.contrast_spin.setSingleStep(0.1)
        self.contrast_spin.setDecimals(1)
        layout.addWidget(self.contrast_spin, 2, 1)
        
        # ガンマ補正
        layout.addWidget(QLabel("ガンマ:"), 3, 0)
        self.gamma_spin = QDoubleSpinBox()
        self.gamma_spin.setRange(0.1, 3.0)
        self.gamma_spin.setValue(1.0)
        self.gamma_spin.setSingleStep(0.1)
        self.gamma_spin.setDecimals(1)
        layout.addWidget(self.gamma_spin, 3, 1)
        
        return group
    
    def _create_preview_group(self) -> QGroupBox:
        """プレビューグループを作成"""
        group = QGroupBox("プレビュー")
        layout = QVBoxLayout(group)
        
        # プレビュー情報
        self.preview_label = QLabel("設定を変更するとプレビュー情報が更新されます")
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setStyleSheet("""
            QLabel {
                border: 1px solid #ccc;
                padding: 10px;
                background-color: #f9f9f9;
                min-height: 60px;
            }
        """)
        layout.addWidget(self.preview_label)
        
        return group
    
    def _create_button_layout(self) -> QHBoxLayout:
        """ボタンレイアウトを作成"""
        layout = QHBoxLayout()
        layout.addStretch()
        
        # プレビュー更新ボタン
        self.preview_button = QPushButton("プレビュー更新")
        self.preview_button.clicked.connect(self._update_preview)
        layout.addWidget(self.preview_button)
        
        # エクスポートボタン
        self.export_button = QPushButton("エクスポート")
        self.export_button.clicked.connect(self._start_export)
        self.export_button.setDefault(True)
        layout.addWidget(self.export_button)
        
        # キャンセルボタン
        self.cancel_button = QPushButton("キャンセル")
        self.cancel_button.clicked.connect(self.reject)
        layout.addWidget(self.cancel_button)
        
        return layout
    
    def _connect_signals(self):
        """シグナルを接続"""
        # 設定変更時にプレビューを自動更新
        self.width_spin.valueChanged.connect(self._update_preview)
        self.height_spin.valueChanged.connect(self._update_preview)
        self.scale_spin.valueChanged.connect(self._update_preview)
        self.quality_spin.valueChanged.connect(self._update_preview)
        self.anti_aliasing_check.toggled.connect(self._update_preview)
        self.brightness_spin.valueChanged.connect(self._update_preview)
        self.contrast_spin.valueChanged.connect(self._update_preview)
        self.gamma_spin.valueChanged.connect(self._update_preview)
    
    def _load_default_settings(self):
        """デフォルト設定を読み込み"""
        # デフォルトのファイルパスを設定
        home_dir = os.path.expanduser("~")
        default_path = os.path.join(home_dir, "Desktop", "fractal_export.png")
        self.filepath_edit.setText(default_path)
        
        # プレビューを更新
        self._update_preview()
    
    def _browse_file(self):
        """ファイル保存ダイアログを表示"""
        current_format = self.format_combo.currentText()
        
        if "PNG" in current_format:
            filter_str = "PNG画像 (*.png);;すべてのファイル (*)"
            default_ext = ".png"
        else:
            filter_str = "JPEG画像 (*.jpg *.jpeg);;すべてのファイル (*)"
            default_ext = ".jpg"
        
        current_path = self.filepath_edit.text()
        if not current_path:
            current_path = os.path.join(os.path.expanduser("~"), "Desktop", f"fractal_export{default_ext}")
        
        filepath, _ = QFileDialog.getSaveFileName(
            self, "画像を保存", current_path, filter_str
        )
        
        if filepath:
            self.filepath_edit.setText(filepath)
            self._update_preview()
    
    def _on_format_changed(self, format_text: str):
        """ファイル形式変更時の処理"""
        is_jpeg = "JPEG" in format_text
        self.quality_spin.setEnabled(is_jpeg)
        
        # ファイルパスの拡張子を更新
        current_path = self.filepath_edit.text()
        if current_path:
            base_path = os.path.splitext(current_path)[0]
            if is_jpeg:
                new_path = base_path + ".jpg"
            else:
                new_path = base_path + ".png"
            self.filepath_edit.setText(new_path)
        
        self._update_preview()
    
    def _on_resolution_type_changed(self, button, checked: bool):
        """解像度タイプ変更時の処理"""
        if checked:
            is_high_res = button == self.high_res_radio
            self.scale_spin.setEnabled(is_high_res)
            self.width_spin.setEnabled(not is_high_res)
            self.height_spin.setEnabled(not is_high_res)
            self._update_preview()
    
    def _update_preview(self):
        """プレビュー情報を更新"""
        try:
            # 設定を取得
            is_high_res = self.high_res_radio.isChecked()
            format_text = self.format_combo.currentText()
            
            if is_high_res:
                # 現在の画像サイズから高解像度サイズを計算
                if self.iteration_data is not None:
                    current_height, current_width = self.iteration_data.shape
                    scale = self.scale_spin.value()
                    final_width = current_width * scale
                    final_height = current_height * scale
                else:
                    final_width = 800 * self.scale_spin.value()
                    final_height = 600 * self.scale_spin.value()
            else:
                final_width = self.width_spin.value()
                final_height = self.height_spin.value()
            
            # ファイルサイズの概算
            if "PNG" in format_text:
                # PNGは圧縮率が低いため、より大きなサイズ
                estimated_size_mb = (final_width * final_height * 3) / (1024 * 1024)
            else:
                # JPEGは圧縮率が高い
                quality_factor = self.quality_spin.value() / 100.0
                estimated_size_mb = (final_width * final_height * 3 * quality_factor) / (1024 * 1024 * 10)
            
            # プレビュー情報を表示
            preview_text = f"""
解像度: {final_width} x {final_height} ピクセル
形式: {format_text.split(' ')[0]}
推定ファイルサイズ: {estimated_size_mb:.1f} MB
アンチエイリアシング: {'有効' if self.anti_aliasing_check.isChecked() else '無効'}
明度: {self.brightness_spin.value():.1f} / コントラスト: {self.contrast_spin.value():.1f}
            """.strip()
            
            self.preview_label.setText(preview_text)
            
            # エクスポートボタンの有効/無効を制御
            has_filepath = bool(self.filepath_edit.text().strip())
            has_data = self.iteration_data is not None
            self.export_button.setEnabled(has_filepath and has_data)
            
        except Exception as e:
            self.preview_label.setText(f"プレビュー更新エラー: {str(e)}")
    
    def _start_export(self):
        """エクスポート処理を開始"""
        if self.iteration_data is None:
            QMessageBox.warning(self, "エラー", "エクスポートするフラクタルデータがありません。")
            return
        
        filepath = self.filepath_edit.text().strip()
        if not filepath:
            QMessageBox.warning(self, "エラー", "保存先ファイルパスを指定してください。")
            return
        
        # ディレクトリが存在するかチェック
        directory = os.path.dirname(filepath)
        if directory and not os.path.exists(directory):
            try:
                os.makedirs(directory, exist_ok=True)
            except Exception as e:
                QMessageBox.critical(self, "エラー", f"ディレクトリを作成できませんでした: {str(e)}")
                return
        
        # エクスポート設定を収集
        export_settings = {
            'high_resolution': self.high_res_radio.isChecked(),
            'scale_factor': self.scale_spin.value(),
            'quality': self.quality_spin.value(),
            'anti_aliasing': self.anti_aliasing_check.isChecked(),
            'brightness': self.brightness_spin.value(),
            'contrast': self.contrast_spin.value(),
            'gamma': self.gamma_spin.value()
        }
        
        # 進行状況ダイアログを作成
        self.progress_dialog = ExportProgressDialog(self)
        
        # ワーカースレッドを作成
        self.export_worker = ImageExportWorker(
            self.iteration_data, self.max_iterations, filepath, export_settings
        )
        
        # シグナルを接続
        self.export_worker.progress_updated.connect(self.progress_dialog.update_progress)
        self.export_worker.export_completed.connect(self._on_export_completed)
        self.export_worker.export_failed.connect(self._on_export_failed)
        self.progress_dialog.canceled.connect(self.export_worker.cancel)
        
        # エクスポート開始
        self.export_worker.start()
        self.progress_dialog.exec()
    
    def _on_export_completed(self, filepath: str):
        """エクスポート完了時の処理"""
        if self.progress_dialog:
            self.progress_dialog.close()
        
        QMessageBox.information(
            self, "エクスポート完了", 
            f"画像を正常にエクスポートしました:\n{filepath}"
        )
        self.accept()
    
    def _on_export_failed(self, error_message: str):
        """エクスポート失敗時の処理"""
        if self.progress_dialog:
            self.progress_dialog.close()
        
        QMessageBox.critical(
            self, "エクスポートエラー", 
            f"画像のエクスポートに失敗しました:\n{error_message}"
        )
    
    def set_fractal_data(self, iteration_data: np.ndarray, max_iterations: int):
        """エクスポートするフラクタルデータを設定"""
        self.iteration_data = iteration_data
        self.max_iterations = max_iterations
        self._update_preview()
    
    def get_export_settings(self) -> Dict[str, Any]:
        """現在のエクスポート設定を取得"""
        return {
            'filepath': self.filepath_edit.text(),
            'format': self.format_combo.currentText(),
            'high_resolution': self.high_res_radio.isChecked(),
            'width': self.width_spin.value(),
            'height': self.height_spin.value(),
            'scale_factor': self.scale_spin.value(),
            'quality': self.quality_spin.value(),
            'anti_aliasing': self.anti_aliasing_check.isChecked(),
            'brightness': self.brightness_spin.value(),
            'contrast': self.contrast_spin.value(),
            'gamma': self.gamma_spin.value()
        }