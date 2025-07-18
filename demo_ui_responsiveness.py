"""
UI応答性最適化のデモンストレーション

このデモでは、バックグラウンド計算、プログレッシブレンダリング、
リアルタイムプレビューなどのUI応答性最適化機能を実際に動作させて確認します。
"""

import sys
import time
import numpy as np
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QPushButton, QLabel, QSlider, QTextEdit, QGroupBox
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont

from fractal_editor.services.background_calculator import (
    BackgroundCalculationService, ResponsiveUIManager, 
    get_background_calculation_service, get_responsive_ui_manager
)
from fractal_editor.ui.main_window import MainWindow
from fractal_editor.ui.fractal_widget import FractalWidget
from fractal_editor.models.data_models import FractalParameters, ComplexRegion, ComplexNumber
from fractal_editor.generators.mandelbrot import MandelbrotGenerator


class UIResponsivenessDemo(QMainWindow):
    """UI応答性最適化のデモウィンドウ"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("UI応答性最適化デモ")
        self.setGeometry(100, 100, 1200, 800)
        
        # サービスを初期化
        self.background_service = get_background_calculation_service()
        self.responsive_ui_manager = get_responsive_ui_manager()
        
        # フラクタル生成器
        self.mandelbrot_generator = MandelbrotGenerator()
        
        # デモ用の状態
        self.demo_running = False
        self.current_calculation_count = 0
        self.total_calculations = 0
        
        # UIを設定
        self._setup_ui()
        self._connect_signals()
        
        # 初期パフォーマンス最適化
        self.responsive_ui_manager.optimize_for_system_performance()
        
        print("UI応答性最適化デモを開始しました")
        print("各ボタンをクリックして機能をテストしてください")
    
    def _setup_ui(self):
        """UIを設定"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout(central_widget)
        
        # 左側：コントロールパネル
        control_panel = self._create_control_panel()
        main_layout.addWidget(control_panel, 1)
        
        # 右側：フラクタル表示とログ
        display_panel = self._create_display_panel()
        main_layout.addWidget(display_panel, 2)
    
    def _create_control_panel(self) -> QWidget:
        """コントロールパネルを作成"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # タイトル
        title = QLabel("UI応答性最適化デモ")
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # バックグラウンド計算テスト
        bg_group = QGroupBox("バックグラウンド計算")
        bg_layout = QVBoxLayout(bg_group)
        
        self.start_bg_btn = QPushButton("バックグラウンド計算開始")
        self.start_bg_btn.clicked.connect(self._start_background_calculation)
        bg_layout.addWidget(self.start_bg_btn)
        
        self.cancel_bg_btn = QPushButton("計算キャンセル")
        self.cancel_bg_btn.clicked.connect(self._cancel_calculation)
        self.cancel_bg_btn.setEnabled(False)
        bg_layout.addWidget(self.cancel_bg_btn)
        
        layout.addWidget(bg_group)
        
        # プログレッシブレンダリングテスト
        prog_group = QGroupBox("プログレッシブレンダリング")
        prog_layout = QVBoxLayout(prog_group)
        
        self.start_prog_btn = QPushButton("プログレッシブレンダリング開始")
        self.start_prog_btn.clicked.connect(self._start_progressive_rendering)
        prog_layout.addWidget(self.start_prog_btn)
        
        # ステージ数スライダー
        prog_layout.addWidget(QLabel("ステージ数:"))
        self.stages_slider = QSlider(Qt.Orientation.Horizontal)
        self.stages_slider.setRange(2, 8)
        self.stages_slider.setValue(4)
        self.stages_slider.valueChanged.connect(self._update_stages_label)
        prog_layout.addWidget(self.stages_slider)
        
        self.stages_label = QLabel("4 ステージ")
        prog_layout.addWidget(self.stages_label)
        
        layout.addWidget(prog_group)
        
        # リアルタイムプレビューテスト
        preview_group = QGroupBox("リアルタイムプレビュー")
        preview_layout = QVBoxLayout(preview_group)
        
        self.preview_enabled_btn = QPushButton("プレビュー有効")
        self.preview_enabled_btn.setCheckable(True)
        self.preview_enabled_btn.setChecked(True)
        self.preview_enabled_btn.clicked.connect(self._toggle_preview)
        preview_layout.addWidget(self.preview_enabled_btn)
        
        # プレビュー遅延スライダー
        preview_layout.addWidget(QLabel("プレビュー遅延 (ms):"))
        self.delay_slider = QSlider(Qt.Orientation.Horizontal)
        self.delay_slider.setRange(100, 2000)
        self.delay_slider.setValue(500)
        self.delay_slider.valueChanged.connect(self._update_delay_label)
        preview_layout.addWidget(self.delay_slider)
        
        self.delay_label = QLabel("500 ms")
        preview_layout.addWidget(self.delay_label)
        
        layout.addWidget(preview_group)
        
        # パフォーマンス監視
        perf_group = QGroupBox("パフォーマンス監視")
        perf_layout = QVBoxLayout(perf_group)
        
        self.monitor_btn = QPushButton("パフォーマンス監視開始")
        self.monitor_btn.setCheckable(True)
        self.monitor_btn.clicked.connect(self._toggle_monitoring)
        perf_layout.addWidget(self.monitor_btn)
        
        self.optimize_btn = QPushButton("パフォーマンス最適化")
        self.optimize_btn.clicked.connect(self._optimize_performance)
        perf_layout.addWidget(self.optimize_btn)
        
        layout.addWidget(perf_group)
        
        # ストレステスト
        stress_group = QGroupBox("ストレステスト")
        stress_layout = QVBoxLayout(stress_group)
        
        self.stress_btn = QPushButton("ストレステスト開始")
        self.stress_btn.clicked.connect(self._start_stress_test)
        stress_layout.addWidget(self.stress_btn)
        
        self.stop_stress_btn = QPushButton("ストレステスト停止")
        self.stop_stress_btn.clicked.connect(self._stop_stress_test)
        self.stop_stress_btn.setEnabled(False)
        stress_layout.addWidget(self.stop_stress_btn)
        
        layout.addWidget(stress_group)
        
        layout.addStretch()
        
        return panel
    
    def _create_display_panel(self) -> QWidget:
        """表示パネルを作成"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # フラクタル表示ウィジェット
        self.fractal_widget = FractalWidget()
        self.fractal_widget.setMinimumHeight(300)
        layout.addWidget(self.fractal_widget)
        
        # ログ表示
        log_label = QLabel("ログ:")
        layout.addWidget(log_label)
        
        self.log_text = QTextEdit()
        self.log_text.setMaximumHeight(200)
        self.log_text.setReadOnly(True)
        layout.addWidget(self.log_text)
        
        # ステータス表示
        self.status_label = QLabel("準備完了")
        layout.addWidget(self.status_label)
        
        return panel
    
    def _connect_signals(self):
        """シグナルを接続"""
        # バックグラウンド計算サービスのシグナル
        self.background_service.calculation_started.connect(self._on_calculation_started)
        self.background_service.calculation_completed.connect(self._on_calculation_completed)
        self.background_service.calculation_cancelled.connect(self._on_calculation_cancelled)
        self.background_service.calculation_error.connect(self._on_calculation_error)
        
        # パフォーマンス監視タイマー
        self.monitor_timer = QTimer()
        self.monitor_timer.timeout.connect(self._update_performance_info)
        self.monitor_timer.setInterval(1000)  # 1秒間隔
        
        # ストレステスト用タイマー
        self.stress_timer = QTimer()
        self.stress_timer.timeout.connect(self._execute_stress_calculation)
        self.stress_timer.setInterval(2000)  # 2秒間隔
    
    def _log_message(self, message: str):
        """ログメッセージを追加"""
        timestamp = time.strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        self.log_text.append(log_entry)
        print(log_entry)  # コンソールにも出力
    
    def _update_status(self, status: str):
        """ステータスを更新"""
        self.status_label.setText(f"ステータス: {status}")
    
    def _start_background_calculation(self):
        """バックグラウンド計算を開始"""
        if self.background_service.is_calculating():
            self._log_message("既に計算が実行中です")
            return
        
        # テスト用のフラクタルパラメータ
        params = FractalParameters(
            region=ComplexRegion(
                top_left=ComplexNumber(-2.0, 1.0),
                bottom_right=ComplexNumber(1.0, -1.0)
            ),
            max_iterations=1000,
            image_size=(400, 300),
            custom_parameters={}
        )
        
        success = self.background_service.start_calculation(
            self.mandelbrot_generator.calculate,
            params,
            show_progress=True,
            parent_widget=self
        )
        
        if success:
            self._log_message("バックグラウンド計算を開始しました")
        else:
            self._log_message("バックグラウンド計算の開始に失敗しました")
    
    def _cancel_calculation(self):
        """計算をキャンセル"""
        self.background_service.cancel_calculation()
        self._log_message("計算キャンセルを要求しました")
    
    def _start_progressive_rendering(self):
        """プログレッシブレンダリングを開始"""
        stages = self.stages_slider.value()
        self._log_message(f"プログレッシブレンダリングを開始 ({stages}ステージ)")
        
        # テスト用パラメータ
        base_params = FractalParameters(
            region=ComplexRegion(
                top_left=ComplexNumber(-2.0, 1.0),
                bottom_right=ComplexNumber(1.0, -1.0)
            ),
            max_iterations=800,
            image_size=(600, 450),
            custom_parameters={}
        )
        
        # プログレッシブレンダリングを実行
        self._execute_progressive_stages(base_params, stages)
    
    def _execute_progressive_stages(self, base_params, total_stages):
        """プログレッシブレンダリングのステージを実行"""
        self.progressive_stage = 0
        self.progressive_total_stages = total_stages
        self.progressive_base_params = base_params
        
        self._execute_next_progressive_stage()
    
    def _execute_next_progressive_stage(self):
        """次のプログレッシブステージを実行"""
        if self.progressive_stage >= self.progressive_total_stages:
            self._log_message("プログレッシブレンダリング完了")
            return
        
        # 現在ステージのパラメータを作成
        stage_params = self.responsive_ui_manager.create_progressive_parameters(
            self.progressive_base_params,
            self.progressive_stage,
            self.progressive_total_stages
        )
        
        self._log_message(f"ステージ {self.progressive_stage + 1}/{self.progressive_total_stages} を実行中...")
        
        # 計算を実行
        result = self.mandelbrot_generator.calculate(stage_params)
        
        # 結果を表示
        if hasattr(result, 'iteration_data'):
            # 画像データを生成（簡略化）
            image_data = self._create_image_from_iterations(result.iteration_data)
            self.fractal_widget.set_progressive_image(
                image_data, 
                self.progressive_stage, 
                self.progressive_total_stages,
                stage_params.region
            )
        
        # 次のステージをスケジュール
        self.progressive_stage += 1
        QTimer.singleShot(500, self._execute_next_progressive_stage)
    
    def _create_image_from_iterations(self, iteration_data: np.ndarray) -> np.ndarray:
        """反復回数データから画像を生成"""
        # 簡単なカラーマッピング
        normalized = (iteration_data / iteration_data.max() * 255).astype(np.uint8)
        
        # RGB画像を作成
        height, width = normalized.shape
        rgb_image = np.zeros((height, width, 3), dtype=np.uint8)
        
        # 簡単なカラーマッピング（青から赤へのグラデーション）
        rgb_image[:, :, 0] = normalized  # 赤チャンネル
        rgb_image[:, :, 2] = 255 - normalized  # 青チャンネル
        
        return rgb_image
    
    def _toggle_preview(self):
        """プレビューの有効/無効を切り替え"""
        enabled = self.preview_enabled_btn.isChecked()
        self.responsive_ui_manager.enable_preview_mode(enabled)
        
        status = "有効" if enabled else "無効"
        self.preview_enabled_btn.setText(f"プレビュー{status}")
        self._log_message(f"リアルタイムプレビューを{status}にしました")
    
    def _update_stages_label(self):
        """ステージ数ラベルを更新"""
        stages = self.stages_slider.value()
        self.stages_label.setText(f"{stages} ステージ")
    
    def _update_delay_label(self):
        """遅延ラベルを更新"""
        delay = self.delay_slider.value()
        self.delay_label.setText(f"{delay} ms")
    
    def _toggle_monitoring(self):
        """パフォーマンス監視の開始/停止"""
        if self.monitor_btn.isChecked():
            self.monitor_timer.start()
            self.monitor_btn.setText("監視停止")
            self._log_message("パフォーマンス監視を開始しました")
        else:
            self.monitor_timer.stop()
            self.monitor_btn.setText("パフォーマンス監視開始")
            self._log_message("パフォーマンス監視を停止しました")
    
    def _update_performance_info(self):
        """パフォーマンス情報を更新"""
        responsiveness = self.responsive_ui_manager.monitor_ui_responsiveness()
        calc_stats = self.background_service.get_calculation_statistics()
        
        perf_info = (
            f"UI応答性: {responsiveness['responsiveness']} "
            f"({responsiveness['response_time_ms']:.1f}ms), "
            f"計算状態: {calc_stats.get('status', 'idle')}"
        )
        
        self._update_status(perf_info)
    
    def _optimize_performance(self):
        """パフォーマンスを最適化"""
        self._log_message("パフォーマンス最適化を実行中...")
        
        # UI応答性管理の最適化
        self.responsive_ui_manager.optimize_for_system_performance()
        
        # フラクタルウィジェットの最適化
        self.fractal_widget.optimize_for_performance()
        
        # 最適化後の情報を取得
        responsiveness = self.responsive_ui_manager.monitor_ui_responsiveness()
        
        self._log_message(
            f"最適化完了: UI応答性 = {responsiveness['responsiveness']}, "
            f"応答時間 = {responsiveness['response_time_ms']:.1f}ms"
        )
    
    def _start_stress_test(self):
        """ストレステストを開始"""
        self.demo_running = True
        self.current_calculation_count = 0
        self.total_calculations = 20  # 20回の計算を実行
        
        self.stress_btn.setEnabled(False)
        self.stop_stress_btn.setEnabled(True)
        
        self.stress_timer.start()
        self._log_message(f"ストレステストを開始 (計算回数: {self.total_calculations})")
    
    def _stop_stress_test(self):
        """ストレステストを停止"""
        self.demo_running = False
        self.stress_timer.stop()
        
        self.stress_btn.setEnabled(True)
        self.stop_stress_btn.setEnabled(False)
        
        self._log_message("ストレステストを停止しました")
    
    def _execute_stress_calculation(self):
        """ストレステスト用の計算を実行"""
        if not self.demo_running or self.current_calculation_count >= self.total_calculations:
            self._stop_stress_test()
            return
        
        if self.background_service.is_calculating():
            self._log_message("前の計算がまだ実行中です。スキップします。")
            return
        
        self.current_calculation_count += 1
        
        # ランダムなパラメータで計算
        import random
        zoom = random.uniform(1.0, 10.0)
        center_x = random.uniform(-2.0, 1.0)
        center_y = random.uniform(-1.0, 1.0)
        
        region_size = 3.0 / zoom
        params = FractalParameters(
            region=ComplexRegion(
                top_left=ComplexNumber(center_x - region_size/2, center_y + region_size/2),
                bottom_right=ComplexNumber(center_x + region_size/2, center_y - region_size/2)
            ),
            max_iterations=random.randint(200, 800),
            image_size=(random.randint(200, 400), random.randint(150, 300)),
            custom_parameters={}
        )
        
        success = self.background_service.start_calculation(
            self.mandelbrot_generator.calculate,
            params,
            show_progress=False,
            parent_widget=self
        )
        
        if success:
            self._log_message(f"ストレステスト計算 {self.current_calculation_count}/{self.total_calculations} を開始")
        else:
            self._log_message(f"ストレステスト計算 {self.current_calculation_count} の開始に失敗")
    
    def _on_calculation_started(self):
        """計算開始時の処理"""
        self.start_bg_btn.setEnabled(False)
        self.cancel_bg_btn.setEnabled(True)
        self._update_status("計算中...")
    
    def _on_calculation_completed(self, result):
        """計算完了時の処理"""
        self.start_bg_btn.setEnabled(True)
        self.cancel_bg_btn.setEnabled(False)
        
        if hasattr(result, 'calculation_time'):
            self._log_message(f"計算完了 (時間: {result.calculation_time:.2f}秒)")
            
            # 結果を表示
            if hasattr(result, 'iteration_data'):
                image_data = self._create_image_from_iterations(result.iteration_data)
                self.fractal_widget.set_fractal_image(image_data, result.region)
        else:
            self._log_message("計算完了")
        
        self._update_status("準備完了")
    
    def _on_calculation_cancelled(self):
        """計算キャンセル時の処理"""
        self.start_bg_btn.setEnabled(True)
        self.cancel_bg_btn.setEnabled(False)
        self._log_message("計算がキャンセルされました")
        self._update_status("キャンセル済み")
    
    def _on_calculation_error(self, error_message):
        """計算エラー時の処理"""
        self.start_bg_btn.setEnabled(True)
        self.cancel_bg_btn.setEnabled(False)
        self._log_message(f"計算エラー: {error_message}")
        self._update_status("エラー")


def main():
    """メイン関数"""
    print("UI応答性最適化デモを開始します...")
    
    # PyQt6アプリケーションを作成
    app = QApplication(sys.argv)
    
    try:
        # デモウィンドウを作成・表示
        demo = UIResponsivenessDemo()
        demo.show()
        
        print("\n=== UI応答性最適化デモ ===")
        print("このデモでは以下の機能をテストできます:")
        print("1. バックグラウンド計算 - UIをブロックしない計算")
        print("2. プログレッシブレンダリング - 段階的な品質向上")
        print("3. リアルタイムプレビュー - パラメータ変更時の即座な反映")
        print("4. パフォーマンス監視 - UI応答性の監視")
        print("5. ストレステスト - 連続計算による負荷テスト")
        print("\n各ボタンをクリックして機能を試してください。")
        print("ウィンドウを閉じるとデモが終了します。")
        
        # アプリケーションを実行
        sys.exit(app.exec())
        
    except Exception as e:
        print(f"デモ実行中にエラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()