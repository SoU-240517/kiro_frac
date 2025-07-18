#!/usr/bin/env python3
"""
パフォーマンスベンチマークテスト

フラクタルエディタの各コンポーネントのパフォーマンスを測定し、
ベンチマーク結果を出力します。
"""

import time
import sys
import os
import gc
import json
from datetime import datetime
import numpy as np

# プロジェクトのパスを追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'fractal_editor'))

from fractal_editor.models.data_models import (
    ComplexNumber, ComplexRegion, FractalParameters
)
from fractal_editor.generators.mandelbrot import MandelbrotGenerator
from fractal_editor.generators.julia import JuliaGenerator
from fractal_editor.generators.custom_formula import CustomFormulaGenerator
from fractal_editor.services.parallel_calculator import ParallelCalculator
from fractal_editor.services.image_renderer import ImageRenderer
from fractal_editor.services.color_system import ColorPalette, ColorStop

class PerformanceBenchmark:
    """パフォーマンスベンチマーククラス"""
    
    def __init__(self):
        self.results = {}
        self.start_time = None
    
    def start_timer(self):
        """タイマー開始"""
        gc.collect()  # ガベージコレクション実行
        self.start_time = time.perf_counter()
    
    def end_timer(self, test_name):
        """タイマー終了と結果記録"""
        if self.start_time is None:
            raise ValueError("タイマーが開始されていません")
        
        elapsed = time.perf_counter() - self.start_time
        self.results[test_name] = elapsed
        print(f"{test_name}: {elapsed:.4f}秒")
        return elapsed
    
    def benchmark_mandelbrot_generation(self):
        """マンデルブロ集合生成のベンチマーク"""
        print("\n=== マンデルブロ集合生成ベンチマーク ===")
        
        generator = MandelbrotGenerator()
        region = ComplexRegion(
            top_left=ComplexNumber(-2.0, 1.0),
            bottom_right=ComplexNumber(1.0, -1.0)
        )
        
        # 異なる画像サイズでのテスト
        sizes = [(200, 200), (500, 500), (1000, 1000)]
        iterations = [100, 500, 1000]
        
        for size in sizes:
            for max_iter in iterations:
                params = FractalParameters(
                    region=region,
                    max_iterations=max_iter,
                    image_size=size,
                    custom_parameters={}
                )
                
                test_name = f"Mandelbrot_{size[0]}x{size[1]}_{max_iter}iter"
                
                self.start_timer()
                result = generator.calculate(params)
                self.end_timer(test_name)
                
                # メモリ使用量の確認
                memory_mb = result.iteration_data.nbytes / 1024 / 1024
                print(f"  メモリ使用量: {memory_mb:.2f}MB")
    
    def benchmark_julia_generation(self):
        """ジュリア集合生成のベンチマーク"""
        print("\n=== ジュリア集合生成ベンチマーク ===")
        
        generator = JuliaGenerator()
        region = ComplexRegion(
            top_left=ComplexNumber(-2.0, 2.0),
            bottom_right=ComplexNumber(2.0, -2.0)
        )
        
        # 異なるcパラメータでのテスト
        c_values = [
            (-0.7, 0.27015),
            (-0.8, 0.156),
            (0.285, 0.01)
        ]
        
        for c_real, c_imag in c_values:
            params = FractalParameters(
                region=region,
                max_iterations=500,
                image_size=(800, 800),
                custom_parameters={'c_real': c_real, 'c_imaginary': c_imag}
            )
            
            test_name = f"Julia_c({c_real},{c_imag})"
            
            self.start_timer()
            result = generator.calculate(params)
            self.end_timer(test_name)
    
    def benchmark_custom_formula(self):
        """カスタム式生成のベンチマーク"""
        print("\n=== カスタム式生成ベンチマーク ===")
        
        formulas = [
            ("z**2 + c", "二次式"),
            ("z**3 + c", "三次式"),
            ("sin(z) + c", "三角関数"),
            ("exp(z) + c", "指数関数")
        ]
        
        region = ComplexRegion(
            top_left=ComplexNumber(-1.5, 1.5),
            bottom_right=ComplexNumber(1.5, -1.5)
        )
        
        for formula, name in formulas:
            try:
                generator = CustomFormulaGenerator(formula, name)
                params = FractalParameters(
                    region=region,
                    max_iterations=200,
                    image_size=(600, 600),
                    custom_parameters={}
                )
                
                test_name = f"CustomFormula_{name}"
                
                self.start_timer()
                result = generator.calculate(params)
                self.end_timer(test_name)
                
            except Exception as e:
                print(f"  {name}: エラー - {e}")
    
    def benchmark_parallel_calculation(self):
        """並列計算のベンチマーク"""
        print("\n=== 並列計算ベンチマーク ===")
        
        generator = MandelbrotGenerator()
        region = ComplexRegion(
            top_left=ComplexNumber(-2.0, 1.0),
            bottom_right=ComplexNumber(1.0, -1.0)
        )
        params = FractalParameters(
            region=region,
            max_iterations=1000,
            image_size=(1200, 1200),
            custom_parameters={}
        )
        
        # 逐次計算
        self.start_timer()
        sequential_result = generator.calculate(params)
        sequential_time = self.end_timer("Sequential_1200x1200")
        
        # 異なるスレッド数での並列計算
        thread_counts = [2, 4, 8]
        
        for thread_count in thread_counts:
            try:
                parallel_calc = ParallelCalculator(thread_count=thread_count)
                
                test_name = f"Parallel_{thread_count}threads"
                
                self.start_timer()
                parallel_result = parallel_calc.calculate_fractal(generator, params)
                parallel_time = self.end_timer(test_name)
                
                # スピードアップ計算
                speedup = sequential_time / parallel_time
                print(f"  スピードアップ: {speedup:.2f}x")
                
            except Exception as e:
                print(f"  {thread_count}スレッド: エラー - {e}")
    
    def benchmark_image_rendering(self):
        """画像レンダリングのベンチマーク"""
        print("\n=== 画像レンダリングベンチマーク ===")
        
        # テスト用フラクタルデータ生成
        generator = MandelbrotGenerator()
        region = ComplexRegion(
            top_left=ComplexNumber(-2.0, 1.0),
            bottom_right=ComplexNumber(1.0, -1.0)
        )
        
        sizes = [(500, 500), (1000, 1000), (2000, 2000)]
        
        for size in sizes:
            params = FractalParameters(
                region=region,
                max_iterations=500,
                image_size=size,
                custom_parameters={}
            )
            
            # フラクタル計算
            fractal_result = generator.calculate(params)
            
            # カラーパレット作成
            color_stops = [
                ColorStop(0.0, (0, 0, 128)),
                ColorStop(0.5, (255, 255, 0)),
                ColorStop(1.0, (255, 0, 0))
            ]
            palette = ColorPalette("ベンチマークパレット", color_stops)
            
            # 画像レンダリング
            renderer = ImageRenderer()
            
            test_name = f"ImageRender_{size[0]}x{size[1]}"
            
            self.start_timer()
            image = renderer.render_fractal(fractal_result, palette)
            self.end_timer(test_name)
            
            # 画像サイズ確認
            print(f"  画像サイズ: {image.size}")
    
    def benchmark_memory_efficiency(self):
        """メモリ効率のベンチマーク"""
        print("\n=== メモリ効率ベンチマーク ===")
        
        try:
            import psutil
            process = psutil.Process()
        except ImportError:
            print("psutilが利用できません。メモリベンチマークをスキップします。")
            return
        
        generator = MandelbrotGenerator()
        region = ComplexRegion(
            top_left=ComplexNumber(-2.0, 1.0),
            bottom_right=ComplexNumber(1.0, -1.0)
        )
        
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        print(f"初期メモリ使用量: {initial_memory:.2f}MB")
        
        # 大きなフラクタル計算を複数回実行
        for i in range(5):
            params = FractalParameters(
                region=region,
                max_iterations=500,
                image_size=(1500, 1500),
                custom_parameters={}
            )
            
            result = generator.calculate(params)
            current_memory = process.memory_info().rss / 1024 / 1024
            print(f"計算{i+1}後のメモリ使用量: {current_memory:.2f}MB")
            
            # 明示的にメモリ解放
            del result
            gc.collect()
        
        final_memory = process.memory_info().rss / 1024 / 1024
        memory_increase = final_memory - initial_memory
        print(f"最終メモリ使用量: {final_memory:.2f}MB")
        print(f"メモリ増加量: {memory_increase:.2f}MB")
        
        self.results['memory_increase_mb'] = memory_increase
    
    def save_results(self, filename="benchmark_results.json"):
        """ベンチマーク結果をファイルに保存"""
        results_data = {
            'timestamp': datetime.now().isoformat(),
            'python_version': sys.version,
            'platform': sys.platform,
            'results': self.results
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results_data, f, indent=2, ensure_ascii=False)
        
        print(f"\nベンチマーク結果を保存しました: {filename}")
    
    def print_summary(self):
        """結果サマリーを表示"""
        print("\n" + "=" * 60)
        print("ベンチマーク結果サマリー")
        print("=" * 60)
        
        # 最も高速なテスト
        fastest_test = min(self.results.items(), key=lambda x: x[1])
        print(f"最高速テスト: {fastest_test[0]} ({fastest_test[1]:.4f}秒)")
        
        # 最も低速なテスト
        slowest_test = max(self.results.items(), key=lambda x: x[1])
        print(f"最低速テスト: {slowest_test[0]} ({slowest_test[1]:.4f}秒)")
        
        # 平均実行時間
        avg_time = sum(self.results.values()) / len(self.results)
        print(f"平均実行時間: {avg_time:.4f}秒")
        
        # パフォーマンス評価
        if avg_time < 1.0:
            print("パフォーマンス評価: 優秀")
        elif avg_time < 5.0:
            print("パフォーマンス評価: 良好")
        elif avg_time < 15.0:
            print("パフォーマンス評価: 普通")
        else:
            print("パフォーマンス評価: 改善が必要")


def main():
    """メイン実行関数"""
    print("フラクタルエディタ パフォーマンスベンチマーク")
    print("=" * 60)
    print(f"開始時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    benchmark = PerformanceBenchmark()
    
    try:
        # 各ベンチマークを実行
        benchmark.benchmark_mandelbrot_generation()
        benchmark.benchmark_julia_generation()
        benchmark.benchmark_custom_formula()
        benchmark.benchmark_parallel_calculation()
        benchmark.benchmark_image_rendering()
        benchmark.benchmark_memory_efficiency()
        
        # 結果保存と表示
        benchmark.save_results()
        benchmark.print_summary()
        
        print(f"\n終了時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("ベンチマークが完了しました。")
        
    except KeyboardInterrupt:
        print("\nベンチマークが中断されました。")
        return 1
    except Exception as e:
        print(f"\nベンチマーク実行中にエラーが発生しました: {e}")
        return 1
    
    return 0


if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)