#!/usr/bin/env python3
"""
統合テスト結果分析ツール
統合テストの実行結果を分析し、詳細なレポートを生成する
"""

import json
import sys
import os
import glob
from datetime import datetime
from typing import Dict, List, Any, Optional
import matplotlib.pyplot as plt
import numpy as np


class TestResultAnalyzer:
    """統合テスト結果分析クラス"""
    
    def __init__(self):
        self.reports: List[Dict[str, Any]] = []
        self.analysis_results: Dict[str, Any] = {}
    
    def load_reports(self, pattern: str = "integration_test_report_*.json") -> int:
        """テストレポートファイルを読み込み"""
        report_files = glob.glob(pattern)
        
        for file_path in report_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    report = json.load(f)
                    report['file_path'] = file_path
                    self.reports.append(report)
            except Exception as e:
                print(f"警告: {file_path}の読み込みに失敗: {e}")
        
        print(f"{len(self.reports)}個のテストレポートを読み込みました")
        return len(self.reports)
    
    def analyze_performance_trends(self) -> Dict[str, Any]:
        """パフォーマンス傾向を分析"""
        if not self.reports:
            return {}
        
        # 実行時間の傾向
        execution_times = []
        timestamps = []
        
        for report in self.reports:
            if 'test_run_info' in report:
                duration = report['test_run_info'].get('duration_seconds', 0)
                timestamp = report['test_run_info'].get('start_time', '')
                
                if duration > 0 and timestamp:
                    execution_times.append(duration)
                    timestamps.append(datetime.fromisoformat(timestamp.replace('Z', '+00:00')))
        
        if execution_times:
            performance_analysis = {
                'average_execution_time': np.mean(execution_times),
                'min_execution_time': np.min(execution_times),
                'max_execution_time': np.max(execution_times),
                'execution_time_std': np.std(execution_times),
                'total_runs': len(execution_times),
                'timestamps': [ts.isoformat() for ts in timestamps],
                'execution_times': execution_times
            }
        else:
            performance_analysis = {'error': 'パフォーマンスデータが見つかりません'}
        
        return performance_analysis
    
    def analyze_success_rates(self) -> Dict[str, Any]:
        """成功率を分析"""
        if not self.reports:
            return {}
        
        success_counts = {}
        total_counts = {}
        
        for report in self.reports:
            if 'test_results' in report:
                for test_name, result in report['test_results'].items():
                    if test_name not in total_counts:
                        total_counts[test_name] = 0
                        success_counts[test_name] = 0
                    
                    total_counts[test_name] += 1
                    if result.get('success', False):
                        success_counts[test_name] += 1
        
        success_rates = {}
        for test_name in total_counts:
            if total_counts[test_name] > 0:
                success_rates[test_name] = success_counts[test_name] / total_counts[test_name]
        
        return {
            'success_rates': success_rates,
            'total_counts': total_counts,
            'success_counts': success_counts,
            'overall_success_rate': np.mean(list(success_rates.values())) if success_rates else 0
        }
    
    def analyze_error_patterns(self) -> Dict[str, Any]:
        """エラーパターンを分析"""
        if not self.reports:
            return {}
        
        error_counts = {}
        error_details = []
        
        for report in self.reports:
            if 'test_results' in report:
                for test_name, result in report['test_results'].items():
                    if not result.get('success', True) and result.get('error'):
                        error_msg = result['error']
                        
                        # エラーメッセージの分類
                        if error_msg not in error_counts:
                            error_counts[error_msg] = 0
                        error_counts[error_msg] += 1
                        
                        error_details.append({
                            'test_name': test_name,
                            'error': error_msg,
                            'timestamp': report.get('test_run_info', {}).get('start_time', ''),
                            'file_path': report.get('file_path', '')
                        })
        
        return {
            'error_counts': error_counts,
            'error_details': error_details,
            'total_errors': len(error_details),
            'unique_errors': len(error_counts)
        }
    
    def analyze_system_compatibility(self) -> Dict[str, Any]:
        """システム互換性を分析"""
        if not self.reports:
            return {}
        
        system_info = {}
        dependency_info = {}
        
        for report in self.reports:
            # システム情報の収集
            if 'system_info' in report:
                sys_info = report['system_info']
                platform = sys_info.get('platform', 'unknown')
                python_version = sys_info.get('python_version', 'unknown')
                
                key = f"{platform}_{python_version}"
                if key not in system_info:
                    system_info[key] = {'count': 0, 'success': 0}
                
                system_info[key]['count'] += 1
                if report.get('test_run_info', {}).get('overall_success', False):
                    system_info[key]['success'] += 1
            
            # 依存関係情報の収集
            if 'dependencies' in report:
                for dep_name, dep_version in report['dependencies'].items():
                    if dep_name not in dependency_info:
                        dependency_info[dep_name] = {}
                    
                    if dep_version not in dependency_info[dep_name]:
                        dependency_info[dep_name][dep_version] = {'count': 0, 'success': 0}
                    
                    dependency_info[dep_name][dep_version]['count'] += 1
                    if report.get('test_run_info', {}).get('overall_success', False):
                        dependency_info[dep_name][dep_version]['success'] += 1
        
        return {
            'system_compatibility': system_info,
            'dependency_compatibility': dependency_info
        }
    
    def generate_comprehensive_analysis(self) -> Dict[str, Any]:
        """包括的な分析を実行"""
        print("統合テスト結果の包括的分析を実行中...")
        
        self.analysis_results = {
            'analysis_timestamp': datetime.now().isoformat(),
            'total_reports': len(self.reports),
            'performance_trends': self.analyze_performance_trends(),
            'success_rates': self.analyze_success_rates(),
            'error_patterns': self.analyze_error_patterns(),
            'system_compatibility': self.analyze_system_compatibility()
        }
        
        return self.analysis_results
    
    def generate_text_report(self) -> str:
        """テキスト形式のレポートを生成"""
        if not self.analysis_results:
            self.generate_comprehensive_analysis()
        
        report_lines = [
            "=" * 60,
            "統合テスト結果分析レポート",
            "=" * 60,
            f"分析日時: {self.analysis_results['analysis_timestamp']}",
            f"分析対象レポート数: {self.analysis_results['total_reports']}",
            ""
        ]
        
        # パフォーマンス分析
        perf = self.analysis_results.get('performance_trends', {})
        if 'average_execution_time' in perf:
            report_lines.extend([
                "パフォーマンス分析:",
                f"  平均実行時間: {perf['average_execution_time']:.2f}秒",
                f"  最短実行時間: {perf['min_execution_time']:.2f}秒",
                f"  最長実行時間: {perf['max_execution_time']:.2f}秒",
                f"  標準偏差: {perf['execution_time_std']:.2f}秒",
                f"  総実行回数: {perf['total_runs']}回",
                ""
            ])
        
        # 成功率分析
        success = self.analysis_results.get('success_rates', {})
        if 'overall_success_rate' in success:
            report_lines.extend([
                "成功率分析:",
                f"  全体成功率: {success['overall_success_rate']*100:.1f}%",
                ""
            ])
            
            if 'success_rates' in success:
                report_lines.append("  テスト別成功率:")
                for test_name, rate in success['success_rates'].items():
                    total = success['total_counts'].get(test_name, 0)
                    report_lines.append(f"    {test_name}: {rate*100:.1f}% ({total}回実行)")
                report_lines.append("")
        
        # エラー分析
        errors = self.analysis_results.get('error_patterns', {})
        if 'total_errors' in errors:
            report_lines.extend([
                "エラー分析:",
                f"  総エラー数: {errors['total_errors']}",
                f"  ユニークエラー数: {errors['unique_errors']}",
                ""
            ])
            
            if errors.get('error_counts'):
                report_lines.append("  頻出エラー:")
                sorted_errors = sorted(errors['error_counts'].items(), 
                                     key=lambda x: x[1], reverse=True)
                for error_msg, count in sorted_errors[:5]:  # 上位5つ
                    report_lines.append(f"    {count}回: {error_msg[:80]}...")
                report_lines.append("")
        
        # システム互換性分析
        compat = self.analysis_results.get('system_compatibility', {})
        if 'system_compatibility' in compat:
            report_lines.extend([
                "システム互換性分析:",
                "  プラットフォーム別成功率:"
            ])
            
            for platform, stats in compat['system_compatibility'].items():
                success_rate = stats['success'] / stats['count'] * 100 if stats['count'] > 0 else 0
                report_lines.append(f"    {platform}: {success_rate:.1f}% ({stats['success']}/{stats['count']})")
            report_lines.append("")
        
        # 推奨事項
        report_lines.extend([
            "推奨事項:",
            self._generate_recommendations(),
            ""
        ])
        
        return "\n".join(report_lines)
    
    def _generate_recommendations(self) -> str:
        """分析結果に基づく推奨事項を生成"""
        recommendations = []
        
        # パフォーマンス推奨事項
        perf = self.analysis_results.get('performance_trends', {})
        if 'average_execution_time' in perf:
            if perf['average_execution_time'] > 300:  # 5分以上
                recommendations.append("  - 実行時間が長いため、テストの並列化を検討してください")
            if perf['execution_time_std'] > perf['average_execution_time'] * 0.5:
                recommendations.append("  - 実行時間のばらつきが大きいため、環境の安定化を検討してください")
        
        # 成功率推奨事項
        success = self.analysis_results.get('success_rates', {})
        if 'overall_success_rate' in success:
            if success['overall_success_rate'] < 0.8:  # 80%未満
                recommendations.append("  - 成功率が低いため、テストの安定性向上が必要です")
            
            if 'success_rates' in success:
                for test_name, rate in success['success_rates'].items():
                    if rate < 0.5:  # 50%未満
                        recommendations.append(f"  - {test_name}の成功率が低いため、優先的に修正してください")
        
        # エラー推奨事項
        errors = self.analysis_results.get('error_patterns', {})
        if errors.get('total_errors', 0) > 0:
            recommendations.append("  - エラーログを確認し、頻出エラーから優先的に対処してください")
        
        if not recommendations:
            recommendations.append("  - 現在の統合テストは良好な状態です。継続的な監視を推奨します")
        
        return "\n".join(recommendations)
    
    def save_analysis_report(self, filename: str = None) -> str:
        """分析レポートをファイルに保存"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"test_analysis_report_{timestamp}.txt"
        
        report_text = self.generate_text_report()
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(report_text)
            print(f"分析レポートを保存しました: {filename}")
            return filename
        except Exception as e:
            print(f"レポート保存エラー: {e}")
            return ""
    
    def save_analysis_json(self, filename: str = None) -> str:
        """分析結果をJSONファイルに保存"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"test_analysis_data_{timestamp}.json"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.analysis_results, f, indent=2, ensure_ascii=False)
            print(f"分析データを保存しました: {filename}")
            return filename
        except Exception as e:
            print(f"分析データ保存エラー: {e}")
            return ""


def main():
    """メイン実行関数"""
    print("統合テスト結果分析ツール")
    print("=" * 40)
    
    analyzer = TestResultAnalyzer()
    
    # テストレポートの読み込み
    report_count = analyzer.load_reports()
    
    if report_count == 0:
        print("テストレポートが見つかりません。")
        print("統合テストを実行してからこのツールを使用してください。")
        return 1
    
    # 分析の実行
    analyzer.generate_comprehensive_analysis()
    
    # レポートの生成と表示
    report_text = analyzer.generate_text_report()
    print("\n" + report_text)
    
    # ファイルへの保存
    text_file = analyzer.save_analysis_report()
    json_file = analyzer.save_analysis_json()
    
    print(f"\n分析完了:")
    print(f"  テキストレポート: {text_file}")
    print(f"  JSONデータ: {json_file}")
    
    return 0


if __name__ == '__main__':
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n分析が中断されました。")
        sys.exit(1)
    except Exception as e:
        print(f"予期しないエラーが発生しました: {e}")
        sys.exit(1)