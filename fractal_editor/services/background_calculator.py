"""
バックグラウンド計算サービス

このモジュールは、UIをブロックしないバックグラウンドでのフラクタル計算と
プログレスバー、キャンセレーション機能を提供します。
"""

import threading
import time
import queue
import psutil
import gc
from typing import Callable, Any, Optional, Dict, List
from dataclasses import dataclass
from enum import Enum
import logging
from PyQt6.QtCore import QObject, QThread, pyqtSignal, QTimer
from PyQt6.QtWidgets import QProgressDialog, QApplication, QLabel, QVBoxLayout


class CalculationStatus(Enum):
    """計算ステータス"""
    IDLE = "idle"
    PREPARING = "preparing"
    CALCULATING = "calculating"
    FINALIZING = "finalizing"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    ERROR = "error"


@dataclass
class CalculationProgress:
    """計算進行状況"""
    status: CalculationStatus
    current_step: int
    total_steps: int
    elapsed_time: float
    estimated_remaining_time: float
    message: str = ""
    memory_usage_mb: float = 0.0
    cpu_usage_percent: float = 0.0
    
    @property
    def progress_percentage(self) -> float:
        """進行率（0-100%）"""
        if self.total_steps == 0:
            return 0.0
        return min(100.0, (self.current_step / self.total_steps) * 100.0)
    
    @property
    def is_complete(self) -> bool:
        """計算完了かどうか"""
        return self.status in [CalculationStatus.COMPLETED, CalculationStatus.CANCELLED, CalculationStatus.ERROR]


class BackgroundCalculationWorker(QThread):
    """
    バックグラウンド計算ワーカースレッド
    
    フラクタル計算をメインUIスレッドとは別のスレッドで実行し、
    進行状況を定期的に報告します。
    """
    
    # シグナル定義
    progress_updated = pyqtSignal(CalculationProgress)
    calculation_completed = pyqtSignal(object)  # 計算結果
    calculation_error = pyqtSignal(str)  # エラーメッセージ
    
    def __init__(self, calculation_func: Callable, parameters: Any, parent=None):
        """
        バックグラウンド計算ワーカーを初期化
        
        Args:
            calculation_func: 実行する計算関数
            parameters: 計算パラメータ
            parent: 親オブジェクト
        """
        super().__init__(parent)
        self.calculation_func = calculation_func
        self.parameters = parameters
        self.logger = logging.getLogger('fractal_editor.background_calculator')
        
        self._cancel_requested = False
        self._start_time = 0.0
        self._current_progress = CalculationProgress(
            status=CalculationStatus.IDLE,
            current_step=0,
            total_steps=1,
            elapsed_time=0.0,
            estimated_remaining_time=0.0
        )
    
    def request_cancellation(self) -> None:
        """計算のキャンセルを要求"""
        self._cancel_requested = True
        self.logger.info("計算キャンセルが要求されました")
    
    def run(self) -> None:
        """ワーカースレッドのメイン処理"""
        try:
            self._start_time = time.time()
            
            # 準備段階
            self._update_progress(CalculationStatus.PREPARING, 0, 100, "計算準備中...")
            
            if self._cancel_requested:
                self._handle_cancellation()
                return
            
            # 計算実行
            self._update_progress(CalculationStatus.CALCULATING, 10, 100, "フラクタル計算中...")
            
            # プログレスコールバックを設定
            def progress_callback(progress_info):
                if hasattr(progress_info, 'current_step'):
                    # 並列計算からの進行状況
                    current = 10 + int(progress_info.current_step / progress_info.total_steps * 80)
                    self._update_progress(
                        CalculationStatus.CALCULATING, 
                        current, 100,
                        f"計算中... ({progress_info.current_step}/{progress_info.total_steps})"
                    )
                else:
                    # 単純な進行率
                    current = 10 + int(progress_info * 80)
                    self._update_progress(
                        CalculationStatus.CALCULATING, 
                        current, 100,
                        f"計算中... {progress_info*100:.1f}%"
                    )
                
                # キャンセルチェック
                if self._cancel_requested:
                    raise InterruptedError("計算がキャンセルされました")
            
            # 計算関数が並列計算をサポートしているかチェック
            if hasattr(self.calculation_func, '__self__') and hasattr(self.calculation_func.__self__, 'calculate_fractal_parallel'):
                # 並列計算を使用
                result = self.calculation_func.__self__.calculate_fractal_parallel(
                    self.calculation_func,
                    self.parameters,
                    progress_callback
                )
            else:
                # 通常の計算を使用
                result = self.calculation_func(self.parameters)
            
            if self._cancel_requested:
                self._handle_cancellation()
                return
            
            # 最終処理
            self._update_progress(CalculationStatus.FINALIZING, 95, 100, "結果処理中...")
            time.sleep(0.1)  # UI更新のための短い待機
            
            # 完了
            self._update_progress(CalculationStatus.COMPLETED, 100, 100, "計算完了")
            self.calculation_completed.emit(result)
            
        except InterruptedError:
            self._handle_cancellation()
        except Exception as e:
            self._handle_error(str(e))
    
    def _update_progress(self, status: CalculationStatus, current: int, total: int, message: str = "") -> None:
        """進行状況を更新"""
        elapsed_time = time.time() - self._start_time
        
        # 残り時間を推定
        if current > 0 and status == CalculationStatus.CALCULATING:
            estimated_total_time = elapsed_time * total / current
            estimated_remaining_time = max(0, estimated_total_time - elapsed_time)
        else:
            estimated_remaining_time = 0.0
        
        self._current_progress = CalculationProgress(
            status=status,
            current_step=current,
            total_steps=total,
            elapsed_time=elapsed_time,
            estimated_remaining_time=estimated_remaining_time,
            message=message
        )
        
        self.progress_updated.emit(self._current_progress)
    
    def _handle_cancellation(self) -> None:
        """キャンセル処理"""
        self._update_progress(CalculationStatus.CANCELLED, 0, 100, "計算がキャンセルされました")
        self.logger.info("計算がキャンセルされました")
    
    def _handle_error(self, error_message: str) -> None:
        """エラー処理"""
        self._update_progress(CalculationStatus.ERROR, 0, 100, f"エラー: {error_message}")
        self.calculation_error.emit(error_message)
        self.logger.error(f"バックグラウンド計算エラー: {error_message}")


class ProgressDialog(QProgressDialog):
    """
    カスタムプログレスダイアログ
    
    フラクタル計算の進行状況を表示し、キャンセル機能を提供します。
    """
    
    def __init__(self, title: str = "フラクタル計算中", parent=None):
        """
        プログレスダイアログを初期化
        
        Args:
            title: ダイアログのタイトル
            parent: 親ウィジェット
        """
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setLabelText("計算準備中...")
        self.setRange(0, 100)
        self.setValue(0)
        self.setModal(True)
        self.setAutoClose(False)
        self.setAutoReset(False)
        
        # 詳細情報表示用
        self._detailed_info = ""
        self._start_time = time.time()
    
    def update_progress(self, progress: CalculationProgress) -> None:
        """進行状況を更新"""
        self.setValue(int(progress.progress_percentage))
        
        # メッセージを更新
        message = progress.message
        if progress.estimated_remaining_time > 0:
            remaining_minutes = int(progress.estimated_remaining_time // 60)
            remaining_seconds = int(progress.estimated_remaining_time % 60)
            if remaining_minutes > 0:
                message += f" (残り約{remaining_minutes}分{remaining_seconds}秒)"
            else:
                message += f" (残り約{remaining_seconds}秒)"
        
        self.setLabelText(message)
        
        # 詳細情報を更新
        elapsed_minutes = int(progress.elapsed_time // 60)
        elapsed_seconds = int(progress.elapsed_time % 60)
        self._detailed_info = (
            f"ステータス: {progress.status.value}\n"
            f"進行状況: {progress.current_step}/{progress.total_steps} ({progress.progress_percentage:.1f}%)\n"
            f"経過時間: {elapsed_minutes}分{elapsed_seconds}秒"
        )
        
        # 完了時の処理
        if progress.is_complete:
            if progress.status == CalculationStatus.COMPLETED:
                self.setLabelText("計算完了")
            elif progress.status == CalculationStatus.CANCELLED:
                self.setLabelText("計算がキャンセルされました")
            elif progress.status == CalculationStatus.ERROR:
                self.setLabelText("計算でエラーが発生しました")
    
    def get_detailed_info(self) -> str:
        """詳細情報を取得"""
        return self._detailed_info


class BackgroundCalculationService(QObject):
    """
    バックグラウンド計算サービス
    
    UIをブロックしないフラクタル計算の管理と
    プログレス表示、キャンセレーション機能を提供します。
    """
    
    # シグナル定義
    calculation_started = pyqtSignal()
    calculation_completed = pyqtSignal(object)  # 計算結果
    calculation_cancelled = pyqtSignal()
    calculation_error = pyqtSignal(str)  # エラーメッセージ
    
    def __init__(self, parent=None):
        """バックグラウンド計算サービスを初期化"""
        super().__init__(parent)
        self.logger = logging.getLogger('fractal_editor.background_calculation_service')
        
        self._current_worker = None
        self._progress_dialog = None
        self._calculation_queue = queue.Queue()
        self._is_calculating = False
        
        # UI更新タイマー
        self._ui_update_timer = QTimer()
        self._ui_update_timer.timeout.connect(self._update_ui)
        self._ui_update_timer.setInterval(100)  # 100ms間隔でUI更新
    
    def is_calculating(self) -> bool:
        """現在計算中かどうか"""
        return self._is_calculating
    
    def start_calculation(self, calculation_func: Callable, parameters: Any, 
                         show_progress: bool = True, parent_widget=None) -> bool:
        """
        バックグラウンド計算を開始
        
        Args:
            calculation_func: 実行する計算関数
            parameters: 計算パラメータ
            show_progress: プログレスダイアログを表示するか
            parent_widget: 親ウィジェット
            
        Returns:
            計算開始に成功した場合True
        """
        if self._is_calculating:
            self.logger.warning("既に計算が実行中です")
            return False
        
        try:
            # ワーカースレッドを作成
            self._current_worker = BackgroundCalculationWorker(calculation_func, parameters)
            
            # シグナルを接続
            self._current_worker.progress_updated.connect(self._on_progress_updated)
            self._current_worker.calculation_completed.connect(self._on_calculation_completed)
            self._current_worker.calculation_error.connect(self._on_calculation_error)
            
            # プログレスダイアログを表示
            if show_progress:
                self._progress_dialog = ProgressDialog("フラクタル計算中", parent_widget)
                self._progress_dialog.canceled.connect(self.cancel_calculation)
                self._progress_dialog.show()
            
            # 計算開始
            self._is_calculating = True
            self._current_worker.start()
            self._ui_update_timer.start()
            
            self.calculation_started.emit()
            self.logger.info("バックグラウンド計算を開始しました")
            
            return True
            
        except Exception as e:
            self.logger.error(f"バックグラウンド計算の開始に失敗: {e}")
            self._cleanup()
            return False
    
    def cancel_calculation(self) -> None:
        """現在の計算をキャンセル"""
        if not self._is_calculating or not self._current_worker:
            return
        
        self.logger.info("計算キャンセルを要求")
        self._current_worker.request_cancellation()
        
        # 並列計算のキャンセルも試行
        if hasattr(self._current_worker.calculation_func, '__self__'):
            calc_obj = self._current_worker.calculation_func.__self__
            if hasattr(calc_obj, 'cancel_computation'):
                calc_obj.cancel_computation()
    
    def _on_progress_updated(self, progress: CalculationProgress) -> None:
        """進行状況更新時の処理"""
        if self._progress_dialog:
            self._progress_dialog.update_progress(progress)
        
        # アプリケーションイベントを処理（UI応答性維持）
        QApplication.processEvents()
    
    def _on_calculation_completed(self, result: Any) -> None:
        """計算完了時の処理"""
        self.logger.info("バックグラウンド計算が完了しました")
        
        if self._progress_dialog:
            self._progress_dialog.close()
        
        self.calculation_completed.emit(result)
        self._cleanup()
    
    def _on_calculation_error(self, error_message: str) -> None:
        """計算エラー時の処理"""
        self.logger.error(f"バックグラウンド計算エラー: {error_message}")
        
        if self._progress_dialog:
            self._progress_dialog.close()
        
        self.calculation_error.emit(error_message)
        self._cleanup()
    
    def _update_ui(self) -> None:
        """UI更新処理"""
        # アプリケーションイベントを処理
        QApplication.processEvents()
        
        # ワーカーの状態をチェック
        if self._current_worker and not self._current_worker.isRunning():
            if self._current_worker.isFinished():
                # ワーカーが終了している場合
                if not self._current_worker._cancel_requested:
                    # 正常終了またはエラー終了の場合、既にシグナルが発行されているはず
                    pass
                else:
                    # キャンセル終了の場合
                    self.calculation_cancelled.emit()
                    self._cleanup()
    
    def _cleanup(self) -> None:
        """リソースのクリーンアップ"""
        self._is_calculating = False
        self._ui_update_timer.stop()
        
        if self._current_worker:
            if self._current_worker.isRunning():
                self._current_worker.quit()
                self._current_worker.wait(3000)  # 3秒待機
            self._current_worker = None
        
        if self._progress_dialog:
            self._progress_dialog.close()
            self._progress_dialog = None
    
    def get_calculation_statistics(self) -> Dict[str, Any]:
        """計算統計情報を取得"""
        if not self._current_worker:
            return {'status': 'idle'}
        
        progress = self._current_worker._current_progress
        return {
            'status': progress.status.value,
            'progress_percentage': progress.progress_percentage,
            'elapsed_time': progress.elapsed_time,
            'estimated_remaining_time': progress.estimated_remaining_time,
            'message': progress.message
        }


class ResponsiveUIManager:
    """
    UI応答性管理クラス
    
    長時間の処理中でもUIの応答性を維持するための機能を提供します。
    """
    
    def __init__(self):
        """UI応答性管理を初期化"""
        self.logger = logging.getLogger('fractal_editor.responsive_ui_manager')
        self._update_interval = 50  # ms
        self._last_update_time = 0
        self._preview_enabled = True
        self._preview_scale = 0.25  # プレビュー用スケール（1/4サイズ）
        self._progressive_rendering = True
        self._ui_freeze_threshold = 100  # ms - UI凍結を防ぐ閾値
    
    def process_events_periodically(self) -> None:
        """定期的にイベント処理を実行"""
        current_time = time.time() * 1000  # ms
        if current_time - self._last_update_time > self._update_interval:
            QApplication.processEvents()
            self._last_update_time = current_time
    
    def set_update_interval(self, interval_ms: int) -> None:
        """更新間隔を設定"""
        self._update_interval = max(10, interval_ms)  # 最小10ms
    
    def enable_preview_mode(self, enabled: bool = True, scale: float = 0.25) -> None:
        """
        プレビューモードの有効/無効を設定
        
        Args:
            enabled: プレビューモードを有効にするか
            scale: プレビュー用のスケール（0.1-1.0）
        """
        self._preview_enabled = enabled
        self._preview_scale = max(0.1, min(1.0, scale))
        self.logger.info(f"プレビューモード: {'有効' if enabled else '無効'}, スケール: {self._preview_scale}")
    
    def enable_progressive_rendering(self, enabled: bool = True) -> None:
        """
        プログレッシブレンダリングの有効/無効を設定
        
        Args:
            enabled: プログレッシブレンダリングを有効にするか
        """
        self._progressive_rendering = enabled
        self.logger.info(f"プログレッシブレンダリング: {'有効' if enabled else '無効'}")
    
    def create_preview_parameters(self, original_params) -> Any:
        """
        プレビュー用の低解像度パラメータを作成
        
        Args:
            original_params: 元のフラクタルパラメータ
            
        Returns:
            プレビュー用パラメータ
        """
        if not self._preview_enabled:
            return original_params
        
        from ..models.data_models import FractalParameters
        
        # 解像度を下げる
        original_width, original_height = original_params.image_size
        preview_width = max(64, int(original_width * self._preview_scale))
        preview_height = max(64, int(original_height * self._preview_scale))
        
        # 反復回数も調整（プレビューでは少なくする）
        preview_iterations = max(50, min(200, original_params.max_iterations // 2))
        
        preview_params = FractalParameters(
            region=original_params.region,
            max_iterations=preview_iterations,
            image_size=(preview_width, preview_height),
            custom_parameters=original_params.custom_parameters.copy()
        )
        
        # プレビューフラグを追加
        preview_params.custom_parameters['_is_preview'] = True
        preview_params.custom_parameters['_original_size'] = (original_width, original_height)
        
        self.logger.debug(
            f"プレビューパラメータ作成: {original_width}x{original_height} -> "
            f"{preview_width}x{preview_height}, 反復: {original_params.max_iterations} -> {preview_iterations}"
        )
        
        return preview_params
    
    def create_progressive_parameters(self, original_params, stage: int, total_stages: int = 4) -> Any:
        """
        プログレッシブレンダリング用のパラメータを作成
        
        Args:
            original_params: 元のフラクタルパラメータ
            stage: 現在のステージ（0から開始）
            total_stages: 総ステージ数
            
        Returns:
            プログレッシブレンダリング用パラメータ
        """
        if not self._progressive_rendering or stage >= total_stages:
            return original_params
        
        from ..models.data_models import FractalParameters
        
        # ステージに応じて解像度と品質を段階的に向上
        stage_ratio = (stage + 1) / total_stages
        
        original_width, original_height = original_params.image_size
        stage_width = max(64, int(original_width * stage_ratio))
        stage_height = max(64, int(original_height * stage_ratio))
        
        # 反復回数も段階的に増加
        min_iterations = 50
        stage_iterations = int(min_iterations + (original_params.max_iterations - min_iterations) * stage_ratio)
        
        progressive_params = FractalParameters(
            region=original_params.region,
            max_iterations=stage_iterations,
            image_size=(stage_width, stage_height),
            custom_parameters=original_params.custom_parameters.copy()
        )
        
        # プログレッシブフラグを追加
        progressive_params.custom_parameters['_is_progressive'] = True
        progressive_params.custom_parameters['_stage'] = stage
        progressive_params.custom_parameters['_total_stages'] = total_stages
        progressive_params.custom_parameters['_original_size'] = (original_width, original_height)
        
        self.logger.debug(
            f"プログレッシブパラメータ作成: ステージ{stage+1}/{total_stages}, "
            f"サイズ: {stage_width}x{stage_height}, 反復: {stage_iterations}"
        )
        
        return progressive_params
    
    def create_responsive_loop(self, total_iterations: int, update_frequency: int = 100):
        """
        応答性を保つループ処理のジェネレータ
        
        Args:
            total_iterations: 総反復回数
            update_frequency: UI更新頻度（何回に1回更新するか）
            
        Yields:
            現在の反復回数
        """
        last_ui_update = time.time() * 1000
        
        for i in range(total_iterations):
            yield i
            
            current_time = time.time() * 1000
            
            # UI凍結防止のための強制更新
            if current_time - last_ui_update > self._ui_freeze_threshold:
                QApplication.processEvents()
                last_ui_update = current_time
            
            # 定期的なUI更新
            elif i % update_frequency == 0:
                self.process_events_periodically()
                
                # 進行状況をログ出力（デバッグ用）
                if i % (update_frequency * 10) == 0:
                    progress = (i / total_iterations) * 100
                    self.logger.debug(f"処理進行状況: {progress:.1f}% ({i}/{total_iterations})")
    
    def create_adaptive_update_frequency(self, total_iterations: int, target_fps: int = 30) -> int:
        """
        目標FPSに基づいて適応的な更新頻度を計算
        
        Args:
            total_iterations: 総反復回数
            target_fps: 目標FPS
            
        Returns:
            適応的な更新頻度
        """
        # 1秒間に何回更新するかを計算
        updates_per_second = target_fps
        
        # 総処理時間を推定（経験的な値）
        estimated_total_time = max(1.0, total_iterations / 100000)  # 100k反復/秒と仮定
        
        # 総更新回数を計算
        total_updates = int(estimated_total_time * updates_per_second)
        
        # 更新頻度を計算
        if total_updates > 0:
            update_frequency = max(1, total_iterations // total_updates)
        else:
            update_frequency = max(1, total_iterations // 100)  # デフォルト
        
        self.logger.debug(
            f"適応的更新頻度: {update_frequency} (総反復: {total_iterations}, "
            f"推定時間: {estimated_total_time:.1f}s, 目標FPS: {target_fps})"
        )
        
        return update_frequency
    
    def monitor_ui_responsiveness(self) -> Dict[str, float]:
        """
        UI応答性を監視し、統計情報を返す
        
        Returns:
            UI応答性統計
        """
        start_time = time.time()
        
        # 短いイベント処理を実行してレスポンス時間を測定
        QApplication.processEvents()
        
        response_time = (time.time() - start_time) * 1000  # ms
        
        # 応答性評価
        if response_time < 16:  # 60 FPS相当
            responsiveness = "excellent"
        elif response_time < 33:  # 30 FPS相当
            responsiveness = "good"
        elif response_time < 100:
            responsiveness = "acceptable"
        else:
            responsiveness = "poor"
        
        return {
            'response_time_ms': response_time,
            'responsiveness': responsiveness,
            'target_fps': 60 if response_time < 16 else (30 if response_time < 33 else 10),
            'recommended_update_interval': max(10, int(response_time * 2))
        }
    
    def optimize_for_system_performance(self) -> None:
        """システムパフォーマンスに基づいてUI設定を最適化"""
        responsiveness = self.monitor_ui_responsiveness()
        
        # 応答性に基づいて設定を調整
        if responsiveness['responsiveness'] == 'poor':
            # パフォーマンスが悪い場合は更新頻度を下げる
            self.set_update_interval(100)
            self.enable_preview_mode(True, 0.2)  # より小さなプレビュー
            self.logger.warning("システムパフォーマンスが低いため、UI設定を最適化しました")
        elif responsiveness['responsiveness'] == 'acceptable':
            self.set_update_interval(75)
            self.enable_preview_mode(True, 0.25)
        else:
            # パフォーマンスが良い場合はデフォルト設定
            self.set_update_interval(50)
            self.enable_preview_mode(True, 0.3)
        
        self.logger.info(
            f"UI最適化完了: 応答性={responsiveness['responsiveness']}, "
            f"応答時間={responsiveness['response_time_ms']:.1f}ms"
        )


# グローバルインスタンス
_background_service = None
_responsive_ui_manager = None

def get_background_calculation_service() -> BackgroundCalculationService:
    """バックグラウンド計算サービスのシングルトンインスタンスを取得"""
    global _background_service
    if _background_service is None:
        _background_service = BackgroundCalculationService()
    return _background_service

def get_responsive_ui_manager() -> ResponsiveUIManager:
    """UI応答性管理のシングルトンインスタンスを取得"""
    global _responsive_ui_manager
    if _responsive_ui_manager is None:
        _responsive_ui_manager = ResponsiveUIManager()
    return _responsive_ui_manager