#!/usr/bin/env python3
"""
統合テスト検証スクリプト
統合テストスイートが正しく動作することを確認する
"""

import sys
import os
import unittest
import tempfile
import shutil
from unittest.mock import Mock, patch

# プロジェクトパスを追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'fractal_editor'))

# 基本的なインポートテスト
def test_imports():
    """必要なモジュールがインポートできることを確認"""
    print("インポートテストを実行中...")
    
    try:
        from fractal_editor.models.data_models import ComplexNumber, ComplexRegion, FractalParameters
        print("✓ データモデルのインポート成功")
    except ImportError as e:
        print(f"✗ データモデルのインポート失敗: {e}")
        return False
    
    try:
        from fractal_editor.generators.mandelbrot import MandelbrotGenerator
        from fractal_editor.generators.julia import JuliaGenerator
        print("✓ フラクタル生成器のインポート成功")
    except ImportError as e:
        print(f"✗ フラクタル生成器のインポート失敗: {e}")
        return False
    
    try:
        from fractal_editor.services.color_system import ColorPalette, ColorMapper
        from fractal_editor.services.image_renderer import ImageRenderer
        print("✓ サービスクラスのインポート成功")
    except ImportError as e:
        print(f"✗ サービスクラスのインポート失敗: {e}")
        return False
    
    return True


def test_basic_functionality():
    """基本機能の動作確認"""
    print("\n基本機能テストを実行中...")
    
    try:
        from fractal_editor.models.data_models import ComplexNumber, ComplexRegion, FractalParameters
        from fractal_editor.generators.mandelbrot import MandelbrotGenerator
        
        # 基本的なフラクタル生成テスト
        parameters = FractalParameters(
            region=ComplexRegion(
                top_left=ComplexNumber(-2.0, 1.0),
                bottom_right=ComplexNumber(1.0, -1.0)
            ),
            max_iterations=50,
            image_size=(100, 100),
            custom_parameters={}
        )
        
        generator = MandelbrotGenerator()
        result = generator.calculate(parameters)
        
        if result is None:
            print("✗ フラクタル生成結果がNone")
            return False
        
        if result.iteration_data.shape != (100, 100):
            print(f"✗ 期待されるサイズ(100, 100)と異なる: {result.iteration_data.shape}")
            return False
        
        print("✓ 基本的なフラクタル生成成功")
        return True
        
    except Exception as e:
        print(f"✗ 基本機能テスト失敗: {e}")
        return False


def test_integration_test_files():
    """統合テストファイルの存在と基本構造を確認"""
    print("\n統合テストファイル検証中...")
    
    test_files = [
        'test_integration_comprehensive.py',
        'test_ui_responsiveness_integration.py'
    ]
    
    runner_files = [
        'run_integration_tests.py'
    ]
    
    # テストファイルの検証
    for file_name in test_files:
        if not os.path.exists(file_name):
            print(f"✗ 必要なテストファイルが見つかりません: {file_name}")
            return False
        
        # ファイルの基本的な構造チェック
        try:
            with open(file_name, 'r', encoding='utf-8') as f:
                content = f.read()
                
            if 'unittest' not in content:
                print(f"✗ {file_name}にunittestが含まれていません")
                return False
                
            if 'class Test' not in content:
                print(f"✗ {file_name}にテストクラスが含まれていません")
                return False
                
        except Exception as e:
            print(f"✗ {file_name}の読み込みエラー: {e}")
            return False
    
    # ランナーファイルの検証
    for file_name in runner_files:
        if not os.path.exists(file_name):
            print(f"✗ 必要なランナーファイルが見つかりません: {file_name}")
            return False
        
        try:
            with open(file_name, 'r', encoding='utf-8') as f:
                content = f.read()
                
            if 'def main' not in content:
                print(f"✗ {file_name}にmain関数が含まれていません")
                return False
                
        except Exception as e:
            print(f"✗ {file_name}の読み込みエラー: {e}")
            return False
    
    print("✓ 統合テストファイルの構造確認完了")
    return True


def test_mock_integration_run():
    """統合テストの模擬実行"""
    print("\n統合テスト模擬実行中...")
    
    try:
        # 統合テストの一部を実際に実行してみる
        from test_integration_comprehensive import IntegrationTestBase
        
        # テスト用の一時ディレクトリを作成
        temp_dir = tempfile.mkdtemp(prefix='integration_test_verification_')
        
        try:
            # 基本的なテストクラスのインスタンス化
            test_instance = IntegrationTestBase()
            test_instance.temp_dir = temp_dir
            test_instance.setUp()
            
            # テストパラメータの確認
            if test_instance.test_parameters is None:
                print("✗ テストパラメータが設定されていません")
                return False
            
            print("✓ 統合テストクラスの基本動作確認完了")
            return True
            
        finally:
            # 一時ディレクトリのクリーンアップ
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
                
    except Exception as e:
        print(f"✗ 統合テスト模擬実行失敗: {e}")
        return False


def run_verification():
    """統合テスト検証の実行"""
    print("=" * 50)
    print("統合テスト検証スクリプト実行開始")
    print("=" * 50)
    
    tests = [
        ("インポートテスト", test_imports),
        ("基本機能テスト", test_basic_functionality),
        ("統合テストファイル検証", test_integration_test_files),
        ("統合テスト模擬実行", test_mock_integration_run),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_function in tests:
        print(f"\n{'-' * 30}")
        print(f"{test_name}")
        print(f"{'-' * 30}")
        
        try:
            if test_function():
                passed += 1
                print(f"✓ {test_name} 成功")
            else:
                print(f"✗ {test_name} 失敗")
        except Exception as e:
            print(f"✗ {test_name} 例外発生: {e}")
    
    print(f"\n" + "=" * 50)
    print("統合テスト検証結果")
    print("=" * 50)
    print(f"成功: {passed}/{total}")
    print(f"成功率: {(passed/total)*100:.1f}%")
    
    if passed == total:
        print("🎉 全ての検証が成功しました！統合テストスイートは正常に動作します。")
        return True
    else:
        print("❌ 一部の検証が失敗しました。統合テストスイートに問題がある可能性があります。")
        return False


if __name__ == '__main__':
    success = run_verification()
    sys.exit(0 if success else 1)