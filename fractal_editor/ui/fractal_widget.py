"""
フラクタル表示ウィジェットの実装
マウスによるパン・ズーム機能とリアルタイム画像更新機能を提供
"""

from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QApplication
from PyQt6.QtCore import Qt, pyqtSignal, QPoint, QTimer
from PyQt6.QtGui import QPainter, QPixmap, QWheelEvent, QMouseEvent, QPaintEvent
from typing import Optional, Tuple
import numpy as np
from PIL import Image
from ..services.background_calculator import get_responsive_ui_manager


class FractalWidget(QWidget):
    """
    フラクタル表示用カスタムウィジェット

    要件5.2, 5.3, 2.4に対応:
    - マウスによるパン・ズーム機能
    - リアルタイム画像更新機能
    - 直感的なユーザーインタラクション
    """

    # シグナル定義
    region_changed = pyqtSignal(object)  # ComplexRegion
    zoom_changed = pyqtSignal(float)
    pan_changed = pyqtSignal(float, float)  # dx, dy

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)

        # ウィジェットの基本設定
        self.setMinimumSize(400, 300)
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        # フラクタル画像関連
        self.fractal_pixmap: Optional[QPixmap] = None
        self.original_image: Optional[np.ndarray] = None

        # パン・ズーム関連の状態
        self.zoom_factor = 1.0
        self.pan_offset = QPoint(0, 0)
        self.last_pan_point = QPoint()
        self.is_panning = False

        # 複素平面の表示範囲
        self.complex_region = None
        self.original_region = None

        # リアルタイム更新用タイマー
        self.update_timer = QTimer()
        self.update_timer.setSingleShot(True)
        self.update_timer.timeout.connect(self._emit_region_changed)

        # UI応答性管理
        self.responsive_ui_manager = get_responsive_ui_manager()

        # UI更新タイマー（応答性維持用）
        self.ui_update_timer = QTimer()
        self.ui_update_timer.timeout.connect(self._process_events)
        self.ui_update_timer.setInterval(50)  # 50ms間隔

        # マウス操作の設定
        self.zoom_sensitivity = 0.1
        self.min_zoom = 0.1
        self.max_zoom = 100.0

        # 初期表示用のプレースホルダー
        self._setup_placeholder()

    def _setup_placeholder(self) -> None:
        """初期表示用のプレースホルダーを設定"""
        self.setStyleSheet("""
            QWidget {
                background-color: #2b2b2b;
                border: 1px solid #555;
            }
        """)

    def set_fractal_image(self, image_array: np.ndarray, complex_region=None) -> None:
        """
        フラクタル画像を設定

        Args:
            image_array: NumPy配列形式の画像データ (RGB)
            complex_region: 画像に対応する複素平面の範囲
        """
        if image_array is None:
            return

        # NumPy配列をPIL Imageに変換
        if image_array.dtype != np.uint8:
            # 0-255の範囲に正規化
            image_array = ((image_array - image_array.min()) /
                          (image_array.max() - image_array.min()) * 255).astype(np.uint8)

        # RGB配列をPIL Imageに変換
        if len(image_array.shape) == 3 and image_array.shape[2] == 3:
            pil_image = Image.fromarray(image_array, 'RGB')
        else:
            # グレースケールの場合
            pil_image = Image.fromarray(image_array, 'L').convert('RGB')

        # PIL ImageをQPixmapに変換
        image_bytes = pil_image.tobytes('raw', 'RGB')
        qimage = QPixmap()
        qimage.loadFromData(image_bytes)

        # 実際にはQImageを経由する必要がある
        from PyQt6.QtGui import QImage
        height, width = image_array.shape[:2]
        if len(image_array.shape) == 3:
            bytes_per_line = 3 * width
            qimage = QImage(image_array.data, width, height, bytes_per_line, QImage.Format.Format_RGB888)
        else:
            bytes_per_line = width
            qimage = QImage(image_array.data, width, height, bytes_per_line, QImage.Format.Format_Grayscale8)
            qimage = qimage.convertToFormat(QImage.Format.Format_RGB888)

        self.fractal_pixmap = QPixmap.fromImage(qimage)
        self.original_image = image_array.copy()

        # 複素平面の範囲を設定
        if complex_region is not None:
            self.complex_region = complex_region
            if self.original_region is None:
                self.original_region = complex_region

        # 表示を更新
        self.update()

    def set_fractal_pixmap(self, pixmap):
        """QPixmapを表示"""
        self.fractal_pixmap = pixmap
        self.update()

    def show_error(self, message: str):
        """エラーメッセージを表示（簡易版）"""
        self.fractal_pixmap = None
        self._error_message = message
        self.update()

    def paintEvent(self, event: QPaintEvent) -> None:
        """ウィジェットの描画イベント"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        if self.fractal_pixmap is None:
            # プレースホルダーを描画
            painter.fillRect(self.rect(), Qt.GlobalColor.darkGray)
            painter.setPen(Qt.GlobalColor.lightGray)
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter,
                           "フラクタル画像を生成してください")
            return

        # 画像のスケーリングと位置計算
        widget_size = self.size()
        pixmap_size = self.fractal_pixmap.size()

        # アスペクト比を保持してスケーリング
        scale_x = widget_size.width() / pixmap_size.width()
        scale_y = widget_size.height() / pixmap_size.height()
        scale = min(scale_x, scale_y) * self.zoom_factor

        scaled_width = int(pixmap_size.width() * scale)
        scaled_height = int(pixmap_size.height() * scale)

        # 中央配置の計算
        x = (widget_size.width() - scaled_width) // 2 + self.pan_offset.x()
        y = (widget_size.height() - scaled_height) // 2 + self.pan_offset.y()

        # 画像を描画
        scaled_pixmap = self.fractal_pixmap.scaled(
            scaled_width, scaled_height,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )

        painter.drawPixmap(x, y, scaled_pixmap)

        # ズーム情報を表示
        if self.zoom_factor != 1.0:
            painter.setPen(Qt.GlobalColor.white)
            zoom_text = f"ズーム: {self.zoom_factor:.2f}x"
            painter.drawText(10, 20, zoom_text)

    def wheelEvent(self, event: QWheelEvent) -> None:
        """マウスホイールによるズーム処理"""
        # ズーム中心点を取得
        zoom_center = event.position().toPoint()

        # ズーム前の座標を記録
        old_zoom = self.zoom_factor

        # ズーム倍率を計算
        delta = event.angleDelta().y()
        zoom_in = delta > 0

        if zoom_in:
            new_zoom = self.zoom_factor * (1.0 + self.zoom_sensitivity)
        else:
            new_zoom = self.zoom_factor * (1.0 - self.zoom_sensitivity)

        # ズーム範囲を制限
        new_zoom = max(self.min_zoom, min(self.max_zoom, new_zoom))

        if new_zoom != self.zoom_factor:
            # ズーム中心を基準にパンオフセットを調整
            zoom_ratio = new_zoom / old_zoom

            widget_center = QPoint(self.width() // 2, self.height() // 2)
            center_to_zoom = zoom_center - widget_center

            # パンオフセットを調整してズーム中心を維持
            self.pan_offset = QPoint(
                int(self.pan_offset.x() * zoom_ratio - center_to_zoom.x() * (zoom_ratio - 1)),
                int(self.pan_offset.y() * zoom_ratio - center_to_zoom.y() * (zoom_ratio - 1))
            )

            self.zoom_factor = new_zoom
            self.update()

            # ズーム変更シグナルを発信
            self.zoom_changed.emit(self.zoom_factor)

            # 遅延して領域変更を通知
            self._schedule_region_update()

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """マウス押下イベント"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_panning = True
            self.last_pan_point = event.position().toPoint()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        """マウス移動イベント"""
        if self.is_panning and event.buttons() & Qt.MouseButton.LeftButton:
            # パン操作
            current_point = event.position().toPoint()
            delta = current_point - self.last_pan_point

            self.pan_offset += delta
            self.last_pan_point = current_point

            self.update()

            # パン変更シグナルを発信
            self.pan_changed.emit(delta.x(), delta.y())

            # 遅延して領域変更を通知
            self._schedule_region_update()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        """マウス解放イベント"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_panning = False
            self.setCursor(Qt.CursorShape.ArrowCursor)

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        """マウスダブルクリックイベント - ズームリセット"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.reset_view()

    def reset_view(self) -> None:
        """表示をリセット（ズーム1.0、パンオフセット0）"""
        self.zoom_factor = 1.0
        self.pan_offset = QPoint(0, 0)
        self.update()

        # リセット後の状態を通知
        self.zoom_changed.emit(self.zoom_factor)
        self._schedule_region_update()

    def _schedule_region_update(self) -> None:
        """領域変更の通知をスケジュール（遅延実行）"""
        self.update_timer.start(100)  # 100ms後に実行

    def _emit_region_changed(self) -> None:
        """領域変更シグナルを発信"""
        if self.complex_region is not None:
            new_region = self._calculate_visible_region()
            self.region_changed.emit(new_region)

    def _calculate_visible_region(self):
        """現在の表示状態から可視領域を計算"""
        if self.original_region is None:
            return None

        # 元の領域のサイズ
        original_width = self.original_region.width
        original_height = self.original_region.height

        # ズームとパンを考慮した新しい領域を計算
        # これは簡略化された実装で、実際にはより複雑な座標変換が必要
        zoom_width = original_width / self.zoom_factor
        zoom_height = original_height / self.zoom_factor

        # パンオフセットを複素平面座標に変換
        widget_size = self.size()
        pan_x_ratio = self.pan_offset.x() / widget_size.width()
        pan_y_ratio = self.pan_offset.y() / widget_size.height()

        pan_complex_x = pan_x_ratio * zoom_width
        pan_complex_y = pan_y_ratio * zoom_height

        # 新しい領域の中心を計算
        original_center_x = (self.original_region.top_left.real + self.original_region.bottom_right.real) / 2
        original_center_y = (self.original_region.top_left.imaginary + self.original_region.bottom_right.imaginary) / 2

        new_center_x = original_center_x - pan_complex_x
        new_center_y = original_center_y + pan_complex_y

        # 新しい領域を作成
        from ..models.data_models import ComplexRegion, ComplexNumber

        new_top_left = ComplexNumber(
            new_center_x - zoom_width / 2,
            new_center_y + zoom_height / 2
        )
        new_bottom_right = ComplexNumber(
            new_center_x + zoom_width / 2,
            new_center_y - zoom_height / 2
        )

        return ComplexRegion(new_top_left, new_bottom_right)

    def get_zoom_factor(self) -> float:
        """現在のズーム倍率を取得"""
        return self.zoom_factor

    def set_zoom_factor(self, zoom: float) -> None:
        """ズーム倍率を設定"""
        zoom = max(self.min_zoom, min(self.max_zoom, zoom))
        if zoom != self.zoom_factor:
            self.zoom_factor = zoom
            self.update()
            self.zoom_changed.emit(self.zoom_factor)

    def get_pan_offset(self) -> Tuple[int, int]:
        """現在のパンオフセットを取得"""
        return (self.pan_offset.x(), self.pan_offset.y())

    def set_pan_offset(self, x: int, y: int) -> None:
        """パンオフセットを設定"""
        self.pan_offset = QPoint(x, y)
        self.update()
        self.pan_changed.emit(x, y)

    def _process_events(self) -> None:
        """UI応答性維持のためのイベント処理"""
        self.responsive_ui_manager.process_events_periodically()

    def start_responsive_mode(self) -> None:
        """応答性維持モードを開始"""
        self.ui_update_timer.start()

    def stop_responsive_mode(self) -> None:
        """応答性維持モードを停止"""
        self.ui_update_timer.stop()

    def set_responsive_update_interval(self, interval_ms: int) -> None:
        """応答性維持の更新間隔を設定"""
        self.ui_update_timer.setInterval(max(10, interval_ms))
        self.responsive_ui_manager.set_update_interval(interval_ms)

    def clear_image(self) -> None:
        """表示画像をクリア"""
        self.fractal_pixmap = None
        self.original_image = None
        self.complex_region = None
        self.original_region = None
        self.stop_responsive_mode()  # 応答性モードも停止
        self.update()

    def save_image(self, file_path: str) -> bool:
        """現在の表示画像をファイルに保存"""
        if self.fractal_pixmap is None:
            return False

        try:
            return self.fractal_pixmap.save(file_path)
        except Exception:
            return False

    def set_progressive_image(self, image_array: np.ndarray, stage: int, total_stages: int, complex_region=None) -> None:
        """
        プログレッシブレンダリング用の画像を設定

        Args:
            image_array: NumPy配列形式の画像データ
            stage: 現在のステージ
            total_stages: 総ステージ数
            complex_region: 画像に対応する複素平面の範囲
        """
        # 通常の画像設定を実行
        self.set_fractal_image(image_array, complex_region)

        # プログレッシブレンダリング情報を表示
        if stage < total_stages - 1:
            # 最終ステージでない場合は、低品質であることを示す
            self.setToolTip(f"プログレッシブレンダリング中... ステージ {stage + 1}/{total_stages}")
        else:
            # 最終ステージの場合はツールチップをクリア
            self.setToolTip("")

    def enable_smooth_updates(self, enabled: bool = True) -> None:
        """
        スムーズな画像更新を有効/無効にする

        Args:
            enabled: スムーズ更新を有効にするか
        """
        if enabled:
            # 更新間隔を短くして滑らかに
            self.ui_update_timer.setInterval(30)  # 30ms間隔
            self.update_timer.setInterval(50)     # 50ms遅延
        else:
            # デフォルト設定に戻す
            self.ui_update_timer.setInterval(50)  # 50ms間隔
            self.update_timer.setInterval(100)    # 100ms遅延

    def set_quality_mode(self, high_quality: bool = True) -> None:
        """
        表示品質モードを設定

        Args:
            high_quality: 高品質モードを有効にするか
        """
        if high_quality:
            # 高品質レンダリング設定
            self.zoom_sensitivity = 0.05  # より細かいズーム
            self.min_zoom = 0.01
            self.max_zoom = 1000.0
        else:
            # 高速レンダリング設定
            self.zoom_sensitivity = 0.1   # デフォルト
            self.min_zoom = 0.1
            self.max_zoom = 100.0

    def get_display_statistics(self) -> dict:
        """表示統計情報を取得"""
        stats = {
            'zoom_factor': self.zoom_factor,
            'pan_offset': (self.pan_offset.x(), self.pan_offset.y()),
            'has_image': self.fractal_pixmap is not None,
            'widget_size': (self.width(), self.height()),
            'responsive_mode_active': self.ui_update_timer.isActive(),
            'update_interval_ms': self.ui_update_timer.interval()
        }

        if self.fractal_pixmap:
            stats['image_size'] = (self.fractal_pixmap.width(), self.fractal_pixmap.height())

        if self.complex_region:
            stats['complex_region'] = {
                'width': self.complex_region.width,
                'height': self.complex_region.height,
                'center_real': (self.complex_region.top_left.real + self.complex_region.bottom_right.real) / 2,
                'center_imag': (self.complex_region.top_left.imaginary + self.complex_region.bottom_right.imaginary) / 2
            }

        return stats

    def optimize_for_performance(self) -> None:
        """パフォーマンス最適化を実行"""
        # UI応答性管理からパフォーマンス情報を取得
        responsiveness = self.responsive_ui_manager.monitor_ui_responsiveness()

        # パフォーマンスに基づいて設定を調整
        if responsiveness['responsiveness'] == 'poor':
            # パフォーマンスが悪い場合
            self.enable_smooth_updates(False)
            self.set_quality_mode(False)
            self.set_responsive_update_interval(100)  # 更新頻度を下げる
        elif responsiveness['responsiveness'] == 'acceptable':
            # 中程度のパフォーマンス
            self.enable_smooth_updates(True)
            self.set_quality_mode(False)
            self.set_responsive_update_interval(75)
        else:
            # 高パフォーマンス
            self.enable_smooth_updates(True)
            self.set_quality_mode(True)
            self.set_responsive_update_interval(50)

    def handle_parameter_change(self, calculation_func, parameters) -> None:
        """
        パラメータ変更時の処理（リアルタイムプレビュー用）

        Args:
            calculation_func: 計算関数
            parameters: 新しいパラメータ
        """
        # 応答性維持モードを開始
        self.start_responsive_mode()

        # プレビュー用パラメータでの計算をスケジュール
        # この処理は親ウィンドウ（MainWindow）に委譲
        parent_window = self.window()
        if hasattr(parent_window, 'schedule_preview_update'):
            parent_window.schedule_preview_update(calculation_func, parameters)

    def enterEvent(self, event) -> None:
        """マウスがウィジェットに入った時の処理"""
        super().enterEvent(event)
        # マウスオーバー時に応答性モードを開始
        self.start_responsive_mode()

    def leaveEvent(self, event) -> None:
        """マウスがウィジェットから出た時の処理"""
        super().leaveEvent(event)
        # マウスが離れた時に応答性モードを停止（パフォーマンス節約）
        if not self.is_panning:
            self.stop_responsive_mode()
