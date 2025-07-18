"""
メモリ管理と最適化サービス

このモジュールは、フラクタル計算における効率的なメモリ使用量管理と
大規模計算時のメモリリーク防止策を提供します。
"""

import gc
import os
import psutil
import numpy as np
import threading
import time
import weakref
from typing import Dict, Any, Optional, List, Callable, Tuple
from dataclasses import dataclass
from enum import Enum
import logging
from contextlib import contextmanager


class MemoryPriority(Enum):
    """メモリ使用の優先度"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class MemoryUsageInfo:
    """メモリ使用量情報"""
    total_memory: int  # 総メモリ量（バイト）
    available_memory: int  # 利用可能メモリ量（バイト）
    used_memory: int  # 使用中メモリ量（バイト）
    process_memory: int  # プロセスメモリ使用量（バイト）
    memory_percent: float  # メモリ使用率（%）
    
    @property
    def available_mb(self) -> float:
        """利用可能メモリ量（MB）"""
        return self.available_memory / (1024 * 1024)
    
    @property
    def used_mb(self) -> float:
        """使用中メモリ量（MB）"""
        return self.used_memory / (1024 * 1024)
    
    @property
    def process_mb(self) -> float:
        """プロセスメモリ使用量（MB）"""
        return self.process_memory / (1024 * 1024)


@dataclass
class MemoryAllocation:
    """メモリ割り当て情報"""
    id: str
    size: int  # バイト
    priority: MemoryPriority
    timestamp: float
    description: str
    weak_ref: Optional[weakref.ref] = None


class MemoryManager:
    """
    メモリ管理サービス
    
    フラクタル計算における効率的なメモリ使用量管理と
    メモリリーク防止機能を提供します。
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        """シングルトンパターンの実装"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """メモリマネージャーを初期化"""
        if hasattr(self, '_initialized'):
            return
        self._initialized = True
        
        self.logger = logging.getLogger('fractal_editor.memory_manager')
        self.allocations: Dict[str, MemoryAllocation] = {}
        self.allocation_counter = 0
        self._monitoring_active = False
        self._monitor_thread = None
        self._cleanup_callbacks: List[Callable[[], None]] = []
        
        # メモリ制限設定
        self.memory_warning_threshold = 0.8  # 80%で警告
        self.memory_critical_threshold = 0.9  # 90%で緊急処理
        self.max_array_size_mb = 512  # 単一配列の最大サイズ（MB）
        
        # 統計情報
        self.peak_memory_usage = 0
        self.total_allocations = 0
        self.total_deallocations = 0
        
        self.logger.info("メモリマネージャーが初期化されました")
    
    def get_memory_info(self) -> MemoryUsageInfo:
        """現在のメモリ使用量情報を取得"""
        try:
            # システムメモリ情報
            memory = psutil.virtual_memory()
            
            # プロセスメモリ情報
            process = psutil.Process()
            process_memory = process.memory_info().rss
            
            return MemoryUsageInfo(
                total_memory=memory.total,
                available_memory=memory.available,
                used_memory=memory.used,
                process_memory=process_memory,
                memory_percent=memory.percent
            )
        except Exception as e:
            self.logger.error(f"メモリ情報の取得に失敗: {e}")
            # フォールバック値を返す
            return MemoryUsageInfo(
                total_memory=8 * 1024 * 1024 * 1024,  # 8GB仮定
                available_memory=4 * 1024 * 1024 * 1024,  # 4GB仮定
                used_memory=4 * 1024 * 1024 * 1024,  # 4GB仮定
                process_memory=512 * 1024 * 1024,  # 512MB仮定
                memory_percent=50.0
            )
    
    def check_memory_availability(self, required_bytes: int) -> bool:
        """
        指定されたサイズのメモリが利用可能かチェック
        
        Args:
            required_bytes: 必要なメモリサイズ（バイト）
            
        Returns:
            メモリが利用可能な場合True
        """
        memory_info = self.get_memory_info()
        
        # 安全マージンを考慮（要求サイズの1.5倍）
        safe_required = int(required_bytes * 1.5)
        
        if memory_info.available_memory < safe_required:
            self.logger.warning(
                f"メモリ不足: 要求={required_bytes/1024/1024:.1f}MB, "
                f"利用可能={memory_info.available_mb:.1f}MB"
            )
            return False
        
        return True
    
    def estimate_fractal_memory_usage(self, width: int, height: int, 
                                    max_iterations: int, dtype=np.int32) -> int:
        """
        フラクタル計算に必要なメモリ使用量を推定
        
        Args:
            width: 画像幅
            height: 画像高さ
            max_iterations: 最大反復回数
            dtype: データ型
            
        Returns:
            推定メモリ使用量（バイト）
        """
        # 基本配列のサイズ
        base_array_size = width * height * np.dtype(dtype).itemsize
        
        # 計算中に必要な追加メモリ（座標配列、中間結果など）
        coordinate_arrays = 2 * max(width, height) * np.dtype(np.float64).itemsize
        intermediate_memory = base_array_size * 0.5  # 中間結果用
        
        # 並列処理時の追加メモリ
        parallel_overhead = base_array_size * 0.3
        
        total_memory = base_array_size + coordinate_arrays + intermediate_memory + parallel_overhead
        
        self.logger.debug(
            f"メモリ使用量推定: {width}x{height}, "
            f"基本={base_array_size/1024/1024:.1f}MB, "
            f"総計={total_memory/1024/1024:.1f}MB"
        )
        
        return int(total_memory)
    
    def allocate_array(self, shape: Tuple[int, ...], dtype=np.int32, 
                      priority: MemoryPriority = MemoryPriority.NORMAL,
                      description: str = "") -> Optional[np.ndarray]:
        """
        メモリ管理された配列を割り当て
        
        Args:
            shape: 配列の形状
            dtype: データ型
            priority: メモリ優先度
            description: 割り当ての説明
            
        Returns:
            割り当てられた配列、失敗時はNone
        """
        try:
            # メモリサイズを計算
            size = np.prod(shape) * np.dtype(dtype).itemsize
            
            # メモリ可用性をチェック
            if not self.check_memory_availability(size):
                self.logger.error(f"配列割り当て失敗: メモリ不足 ({size/1024/1024:.1f}MB)")
                return None
            
            # 単一配列サイズ制限チェック
            size_mb = size / (1024 * 1024)
            if size_mb > self.max_array_size_mb:
                self.logger.error(
                    f"配列サイズが制限を超過: {size_mb:.1f}MB > {self.max_array_size_mb}MB"
                )
                return None
            
            # 配列を割り当て
            array = np.zeros(shape, dtype=dtype)
            
            # 割り当て情報を記録
            allocation_id = f"array_{self.allocation_counter}"
            self.allocation_counter += 1
            
            allocation = MemoryAllocation(
                id=allocation_id,
                size=size,
                priority=priority,
                timestamp=time.time(),
                description=description or f"Array {shape} {dtype}",
                weak_ref=weakref.ref(array, self._cleanup_allocation_callback(allocation_id))
            )
            
            self.allocations[allocation_id] = allocation
            self.total_allocations += 1
            
            # ピークメモリ使用量を更新
            current_usage = self.get_total_allocated_memory()
            if current_usage > self.peak_memory_usage:
                self.peak_memory_usage = current_usage
            
            self.logger.debug(
                f"配列割り当て成功: {allocation_id}, {size_mb:.1f}MB, {description}"
            )
            
            return array
            
        except MemoryError as e:
            self.logger.error(f"メモリ不足で配列割り当て失敗: {e}")
            self._trigger_emergency_cleanup()
            return None
        except Exception as e:
            self.logger.error(f"配列割り当てでエラー: {e}")
            return None
    
    def _cleanup_allocation_callback(self, allocation_id: str) -> Callable[[Any], None]:
        """割り当て解放時のコールバック関数を生成"""
        def callback(weak_ref):
            if allocation_id in self.allocations:
                allocation = self.allocations.pop(allocation_id)
                self.total_deallocations += 1
                self.logger.debug(f"配列解放: {allocation_id}, {allocation.size/1024/1024:.1f}MB")
        return callback
    
    def get_total_allocated_memory(self) -> int:
        """現在割り当て中の総メモリ量を取得（バイト）"""
        return sum(alloc.size for alloc in self.allocations.values())
    
    def force_garbage_collection(self) -> Dict[str, int]:
        """強制的にガベージコレクションを実行"""
        self.logger.info("強制ガベージコレクション開始")
        
        # 無効な弱参照を削除
        invalid_allocations = []
        for alloc_id, allocation in self.allocations.items():
            if allocation.weak_ref is None or allocation.weak_ref() is None:
                invalid_allocations.append(alloc_id)
        
        for alloc_id in invalid_allocations:
            self.allocations.pop(alloc_id, None)
        
        # ガベージコレクション実行
        collected = {
            'generation_0': gc.collect(0),
            'generation_1': gc.collect(1),
            'generation_2': gc.collect(2)
        }
        
        total_collected = sum(collected.values())
        self.logger.info(f"ガベージコレクション完了: {total_collected}オブジェクト回収")
        
        return collected
    
    def _trigger_emergency_cleanup(self) -> None:
        """緊急時のメモリクリーンアップ"""
        self.logger.warning("緊急メモリクリーンアップ開始")
        
        # 低優先度の割り当てを解放
        low_priority_allocations = [
            alloc_id for alloc_id, alloc in self.allocations.items()
            if alloc.priority == MemoryPriority.LOW
        ]
        
        for alloc_id in low_priority_allocations:
            allocation = self.allocations.pop(alloc_id, None)
            if allocation and allocation.weak_ref:
                obj = allocation.weak_ref()
                if obj is not None:
                    del obj
        
        # 強制ガベージコレクション
        self.force_garbage_collection()
        
        # 登録されたクリーンアップコールバックを実行
        for callback in self._cleanup_callbacks:
            try:
                callback()
            except Exception as e:
                self.logger.error(f"クリーンアップコールバックエラー: {e}")
        
        self.logger.info("緊急メモリクリーンアップ完了")
    
    def register_cleanup_callback(self, callback: Callable[[], None]) -> None:
        """メモリクリーンアップ時に実行するコールバックを登録"""
        self._cleanup_callbacks.append(callback)
    
    def start_memory_monitoring(self, interval: float = 5.0) -> None:
        """メモリ監視を開始"""
        if self._monitoring_active:
            return
        
        self._monitoring_active = True
        self._monitor_thread = threading.Thread(
            target=self._memory_monitor_loop,
            args=(interval,),
            daemon=True
        )
        self._monitor_thread.start()
        self.logger.info(f"メモリ監視開始: {interval}秒間隔")
    
    def stop_memory_monitoring(self) -> None:
        """メモリ監視を停止"""
        self._monitoring_active = False
        if self._monitor_thread and self._monitor_thread.is_alive():
            self._monitor_thread.join(timeout=1.0)
        self.logger.info("メモリ監視停止")
    
    def _memory_monitor_loop(self, interval: float) -> None:
        """メモリ監視ループ"""
        while self._monitoring_active:
            try:
                memory_info = self.get_memory_info()
                memory_percent = memory_info.memory_percent / 100.0
                
                if memory_percent >= self.memory_critical_threshold:
                    self.logger.critical(
                        f"メモリ使用量が危険レベル: {memory_percent*100:.1f}%"
                    )
                    self._trigger_emergency_cleanup()
                elif memory_percent >= self.memory_warning_threshold:
                    self.logger.warning(
                        f"メモリ使用量が警告レベル: {memory_percent*100:.1f}%"
                    )
                    self.force_garbage_collection()
                
                time.sleep(interval)
            except Exception as e:
                self.logger.error(f"メモリ監視エラー: {e}")
                time.sleep(interval)
    
    @contextmanager
    def memory_context(self, description: str = ""):
        """メモリ管理コンテキストマネージャー"""
        start_memory = self.get_memory_info().process_memory
        start_allocations = len(self.allocations)
        
        self.logger.debug(f"メモリコンテキスト開始: {description}")
        
        try:
            yield self
        finally:
            # コンテキスト終了時のクリーンアップ
            self.force_garbage_collection()
            
            end_memory = self.get_memory_info().process_memory
            end_allocations = len(self.allocations)
            
            memory_diff = end_memory - start_memory
            allocation_diff = end_allocations - start_allocations
            
            self.logger.debug(
                f"メモリコンテキスト終了: {description}, "
                f"メモリ変化={memory_diff/1024/1024:.1f}MB, "
                f"割り当て変化={allocation_diff}"
            )
    
    def get_memory_statistics(self) -> Dict[str, Any]:
        """メモリ使用統計を取得"""
        memory_info = self.get_memory_info()
        
        return {
            'current_memory_info': {
                'total_mb': memory_info.total_memory / (1024 * 1024),
                'available_mb': memory_info.available_mb,
                'used_mb': memory_info.used_mb,
                'process_mb': memory_info.process_mb,
                'usage_percent': memory_info.memory_percent
            },
            'allocation_statistics': {
                'active_allocations': len(self.allocations),
                'total_allocated_mb': self.get_total_allocated_memory() / (1024 * 1024),
                'peak_memory_mb': self.peak_memory_usage / (1024 * 1024),
                'total_allocations': self.total_allocations,
                'total_deallocations': self.total_deallocations
            },
            'configuration': {
                'warning_threshold': self.memory_warning_threshold,
                'critical_threshold': self.memory_critical_threshold,
                'max_array_size_mb': self.max_array_size_mb
            }
        }
    
    def optimize_for_large_computation(self, width: int, height: int, 
                                     max_iterations: int) -> Dict[str, Any]:
        """
        大規模計算用の最適化設定を提案
        
        Args:
            width: 画像幅
            height: 画像高さ
            max_iterations: 最大反復回数
            
        Returns:
            最適化提案
        """
        estimated_memory = self.estimate_fractal_memory_usage(width, height, max_iterations)
        memory_info = self.get_memory_info()
        
        recommendations = {
            'estimated_memory_mb': estimated_memory / (1024 * 1024),
            'available_memory_mb': memory_info.available_mb,
            'memory_sufficient': estimated_memory < memory_info.available_memory * 0.7,
            'recommendations': []
        }
        
        if not recommendations['memory_sufficient']:
            # メモリ不足時の推奨事項
            if estimated_memory > memory_info.available_memory:
                # 画像サイズ削減を提案
                scale_factor = (memory_info.available_memory * 0.6 / estimated_memory) ** 0.5
                new_width = int(width * scale_factor)
                new_height = int(height * scale_factor)
                
                recommendations['recommendations'].append({
                    'type': 'reduce_image_size',
                    'current_size': (width, height),
                    'suggested_size': (new_width, new_height),
                    'description': f'画像サイズを {new_width}x{new_height} に削減'
                })
            
            if max_iterations > 1000:
                # 反復回数削減を提案
                suggested_iterations = min(1000, max_iterations // 2)
                recommendations['recommendations'].append({
                    'type': 'reduce_iterations',
                    'current_iterations': max_iterations,
                    'suggested_iterations': suggested_iterations,
                    'description': f'最大反復回数を {suggested_iterations} に削減'
                })
            
            # チャンク処理を提案
            recommendations['recommendations'].append({
                'type': 'enable_chunking',
                'description': 'チャンク処理を有効にして段階的に計算'
            })
        
        return recommendations


# メモリ効率的な配列操作ユーティリティ
class MemoryEfficientArrayOps:
    """メモリ効率的な配列操作ユーティリティ"""
    
    @staticmethod
    def create_chunked_array(total_shape: Tuple[int, ...], chunk_size: int, 
                           dtype=np.int32) -> List[np.ndarray]:
        """
        大きな配列をチャンクに分割して作成
        
        Args:
            total_shape: 全体の配列形状
            chunk_size: チャンクサイズ（行数）
            dtype: データ型
            
        Returns:
            チャンク配列のリスト
        """
        memory_manager = MemoryManager()
        chunks = []
        
        height = total_shape[0]
        width = total_shape[1] if len(total_shape) > 1 else 1
        
        for start_row in range(0, height, chunk_size):
            end_row = min(start_row + chunk_size, height)
            chunk_height = end_row - start_row
            
            if len(total_shape) == 1:
                chunk_shape = (chunk_height,)
            else:
                chunk_shape = (chunk_height, width)
            
            chunk = memory_manager.allocate_array(
                chunk_shape, dtype,
                priority=MemoryPriority.NORMAL,
                description=f"Chunk {start_row}-{end_row}"
            )
            
            if chunk is not None:
                chunks.append(chunk)
            else:
                # メモリ不足の場合、既存のチャンクを解放
                chunks.clear()
                memory_manager.force_garbage_collection()
                raise MemoryError(f"チャンク作成に失敗: {chunk_shape}")
        
        return chunks
    
    @staticmethod
    def combine_chunks(chunks: List[np.ndarray]) -> np.ndarray:
        """チャンクを結合して単一の配列を作成"""
        if not chunks:
            raise ValueError("チャンクが空です")
        
        memory_manager = MemoryManager()
        
        # 結合後の形状を計算
        total_height = sum(chunk.shape[0] for chunk in chunks)
        if len(chunks[0].shape) > 1:
            width = chunks[0].shape[1]
            result_shape = (total_height, width)
        else:
            result_shape = (total_height,)
        
        # 結果配列を割り当て
        result = memory_manager.allocate_array(
            result_shape, chunks[0].dtype,
            priority=MemoryPriority.HIGH,
            description="Combined chunks result"
        )
        
        if result is None:
            raise MemoryError("結合結果配列の割り当てに失敗")
        
        # チャンクを結合
        current_row = 0
        for chunk in chunks:
            chunk_height = chunk.shape[0]
            result[current_row:current_row + chunk_height] = chunk
            current_row += chunk_height
        
        return result