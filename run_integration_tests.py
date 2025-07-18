#!/usr/bin/env python3
"""
フラクタルエディタ統合テストランナー
全ての統合テストを実行し、詳細なレポートを生成する
"""

import sys
import os
import time
import json
import subprocess
from datetime import datetime
from pathlib import Path
import unittest
from io import StringIO

# プロジェクトパスを追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'fractal_editor'))

# テストモジュールのインポート
try:
    from test_integration_comprehensive import run_integration_tests
    from test_ui_responsiveness_integration import run_ui_responsiveness_tests
    INTEGRATION_TESTS_AVAILABLE = True
except ImportError as e:
    print(f"警告: 統合テストモジュールのインポートに失敗: {e}")
    INTEGRATION_TESTS_AVAILABLE = False


class IntegrationTestRunner:
    """統合テストランナークラス"""
    
    def __init__(self):
        self.results = {}
        self.start_time = None
        self.end_time = None
        self.report_file = f"integration_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    def run_all_tests(self):
        """全ての統合テストを実行"""
        print("=" * 60)
        print("フラクタルエディタ統合テストスイート実行開始")
        print("=" * 60)
        
        self.start_time = datetime.now()
        
        # システム情報の収集
        self._collect_system_info()
        
        # 各テストスイートの実行
        test_suites = [
            ("基本統合テスト", self._run_basic_integration_tests),
            ("UI応答性テスト", self._run_ui_responsiveness_tests),
            ("パフォーマンステスト", self._run_performance_tests),
            ("エラーハンドリングテスト", self._run_error_handling_tests),
        ]
        
        for suite_name, test_function in test_suites:
            print(f"\n{'-' * 40}")
            print(f"{suite_name}を実行中...")
            print(f"{'-' * 40}")
            
            try:
                result = test_function()
                self.results[suite_name] = {
                    'success': result,
                    'timestamp': datetime.now().isoformat(),
                    'error': None
                }
            except Exception as e:
                print(f"エラー: {suite_name}の実行中に例外が発生: {e}")
                self.results[suite_name] = {
                    'success': False,
                    'timestamp': datetime.now().isoformat(),
                    'error': str(e)
                }
        
        self.end_time = datetime.now()
        
        # レポートの生成と表示
        self._generate_report()
        self._display_summary()
        
        return self._overall_success()
    
    def _collect_system_info(self):
        """システム情報を収集"""
        import platform
        
        system_info = {
            'platform': platform.platform(),
            'python_version': platform.python_version(),
            'architecture': platform.architecture(),
            'processor': platform.processor(),
            'timestamp': datetime.now().isoformat()
        }
        
        # 依存関係の確認
        dependencies = {}
        required_packages = ['numpy', 'PyQt6', 'Pillow', 'psutil']
        
        for package in required_packages:
            try:
                module = __import__(package)
                if hasattr(module, '__version__'):
                    dependencies[package] = module.__version__
                else:
                    dependencies[package] = 'インストール済み'
            except ImportError:
                dependencies[package] = '未インストール'
        
        self.results['system_info'] = system_info
        self.results['dependencies'] = dependencies
        
        print("システム情報:")
        print(f"  プラットフォーム: {system_info['platform']}")
        print(f"  Python: {system_info['python_version']}")
        print(f"  アーキテクチャ: {system_info['architecture'][0]}")
        
        print("\n依存関係:")
        for package, version in dependencies.items():
            print(f"  {package}: {version}")
    
    def _run_basic_integration_tests(self):
        """基本統合テストの実行"""
        if not INTEGRATION_TESTS_AVAILABLE:
            print("統合テストモジュールが利用できません")
            return False
        
        try:
            return run_integration_tests()
        except Exception as e:
            print(f"基本統合テストでエラー: {e}")
            return False
    
    def _run_ui_responsiveness_tests(self):
        """UI応答性テストの実行"""
        if not INTEGRATION_TESTS_AVAILABLE:
            print("UI応答性テストモジュールが利用できません")
            return False
        
        try:
            return run_ui_responsiveness_tests()
        except Exception as e:
            print(f"UI応答性テストでエラー: {e}")
            return False
    
    def _run_performance_tests(self):
        """パフォーマンステストの実行"""
        print("パフォーマンステストを実行中...")
        
        try:
            # 既存のパフォーマンステストファイルを実行
            performance_tests = [
                'test_performance_benchmarks.py',
                'test_performance_optimization.py'
            ]
            
            all_passed = True
            for test_file in performance_tests:
                if os.path.exists(test_file):
                    print(f"  {test_file}を実行中...")
                    result = subprocess.run([
                        sys.executable, test_file
                    ], capture_output=True, text=True)
                    
                    if result.returncode != 0:
                        print(f"    失敗: {result.stderr}")
                        all_passed = False
                    else:
                        print(f"    成功")
                else:
                    print(f"  {test_file}が見つかりません")
            
            return all_passed
            
        except Exception as e:
            print(f"パフォーマンステストでエラー: {e}")
            return False
    
    def _run_error_handling_tests(self):
        """エラーハンドリングテストの実行"""
        print("エラーハンドリングテストを実行中...")
        
        try:
            # 既存のエラーハンドリングテストファイルを実行
            error_tests = [
                'test_error_handling.py',
                'test_error_context.py'
            ]
            
            all_passed = True
            for test_file in error_tests:
                if os.path.exists(test_file):
                    print(f"  {test_file}を実行中...")
                    result = subprocess.run([
                        sys.executable, test_file
                    ], capture_output=True, text=True)
                    
                    if result.returncode != 0:
                        print(f"    失敗: {result.stderr}")
                        all_passed = False
                    else:
                        print(f"    成功")
                else:
                    print(f"  {test_file}が見つかりません")
            
            return all_passed
            
        except Exception as e:
            print(f"エラーハンドリングテストでエラー: {e}")
            return False
    
    def _generate_report(self):
        """詳細レポートの生成"""
        report = {
            'test_run_info': {
                'start_time': self.start_time.isoformat(),
                'end_time': self.end_time.isoformat(),
                'duration_seconds': (self.end_time - self.start_time).total_seconds(),
                'overall_success': self._overall_success()
            },
            'system_info': self.results.get('system_info', {}),
            'dependencies': self.results.get('dependencies', {}),
            'test_results': {k: v for k, v in self.results.items() 
                           if k not in ['system_info', 'dependencies']}
        }
        
        # JSONレポートの保存
        try:
            with open(self.report_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            print(f"\n詳細レポートを保存しました: {self.report_file}")
        except Exception as e:
            print(f"レポート保存エラー: {e}")
    
    def _display_summary(self):
        """結果サマリーの表示"""
        print("\n" + "=" * 60)
        print("統合テスト実行結果サマリー")
        print("=" * 60)
        
        duration = (self.end_time - self.start_time).total_seconds()
        print(f"実行時間: {duration:.2f}秒")
        
        # テストスイート別結果
        test_results = {k: v for k, v in self.results.items() 
                       if k not in ['system_info', 'dependencies']}
        
        passed = sum(1 for result in test_results.values() if result['success'])
        total = len(test_results)
        
        print(f"\nテストスイート結果: {passed}/{total} 成功")
        
        for suite_name, result in test_results.items():
            status = "✓ 成功" if result['success'] else "✗ 失敗"
            print(f"  {suite_name}: {status}")
            if result['error']:
                print(f"    エラー: {result['error']}")
        
        # 全体的な成功/失敗
        overall_success = self._overall_success()
        print(f"\n全体結果: {'✓ 成功' if overall_success else '✗ 失敗'}")
        
        if not overall_success:
            print("\n改善が必要な領域:")
            for suite_name, result in test_results.items():
                if not result['success']:
                    print(f"  - {suite_name}")
    
    def _overall_success(self):
        """全体的な成功判定"""
        test_results = {k: v for k, v in self.results.items() 
                       if k not in ['system_info', 'dependencies']}
        return all(result['success'] for result in test_results.values())


def main():
    """メイン実行関数"""
    runner = IntegrationTestRunner()
    success = runner.run_all_tests()
    
    if success:
        print("\n🎉 全ての統合テストが成功しました！")
        return 0
    else:
        print("\n❌ 一部のテストが失敗しました。詳細は上記を確認してください。")
        return 1


if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)