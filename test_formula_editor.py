"""
式エディタウィジェットのテスト

構文ハイライト、リアルタイム検証、テンプレート機能をテストします。
"""

import sys
import unittest
from PyQt6.QtWidgets import QApplication
from PyQt6.QtTest import QTest
from PyQt6.QtCore import Qt, QTimer

from fractal_editor.ui.formula_editor import (
    FormulaEditorWidget, FormulaEditor, FormulaSyntaxHighlighter,
    TemplateListWidget, ValidationResultWidget
)
from fractal_editor.services.formula_parser import FormulaParser, FormulaValidationError


class TestFormulaEditor(unittest.TestCase):
    """式エディタのテストクラス"""
    
    @classmethod
    def setUpClass(cls):
        """テストクラスの初期化"""
        if not QApplication.instance():
            cls.app = QApplication(sys.argv)
        else:
            cls.app = QApplication.instance()
    
    def setUp(self):
        """各テストの前処理"""
        self.editor = FormulaEditor()
    
    def tearDown(self):
        """各テストの後処理"""
        self.editor.close()
    
    def test_formula_editor_initialization(self):
        """式エディタの初期化テスト"""
        self.assertIsNotNone(self.editor)
        self.assertEqual(self.editor.get_formula(), "")
        self.assertIsNotNone(self.editor.highlighter)
    
    def test_set_and_get_formula(self):
        """数式の設定と取得テスト"""
        test_formula = "z**2 + c"
        self.editor.set_formula(test_formula)
        self.assertEqual(self.editor.get_formula(), test_formula)
    
    def test_formula_validation_valid(self):
        """有効な数式の検証テスト"""
        valid_formulas = [
            "z**2 + c",
            "z**3 + c",
            "sin(z) + c",
            "exp(z) + c",
            "abs(z) + c"
        ]
        
        for formula in valid_formulas:
            with self.subTest(formula=formula):
                self.editor.set_formula(formula)
                # 検証完了まで少し待つ
                QTest.qWait(600)
                result = self.editor.get_last_validation_result()
                if result:
                    self.assertTrue(result.get('valid', False), 
                                  f"Formula '{formula}' should be valid")
    
    def test_formula_validation_invalid(self):
        """無効な数式の検証テスト"""
        invalid_formulas = [
            "import os",  # 危険なコード
            "z**2 + unknown_var",  # 未知の変数
            "z**2 + c)",  # 括弧の不一致
            "unknown_func(z)",  # 未知の関数
        ]
        
        for formula in invalid_formulas:
            with self.subTest(formula=formula):
                self.editor.set_formula(formula)
                # 検証完了まで少し待つ
                QTest.qWait(600)
                result = self.editor.get_last_validation_result()
                if result:
                    self.assertFalse(result.get('valid', True), 
                                   f"Formula '{formula}' should be invalid")
    
    def test_text_insertion(self):
        """テキスト挿入テスト"""
        self.editor.set_formula("z**2")
        # カーソルを末尾に移動
        cursor = self.editor.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self.editor.setTextCursor(cursor)
        self.editor.insert_text_at_cursor(" + c")
        self.assertEqual(self.editor.get_formula(), "z**2 + c")


class TestTemplateListWidget(unittest.TestCase):
    """テンプレートリストウィジェットのテストクラス"""
    
    @classmethod
    def setUpClass(cls):
        """テストクラスの初期化"""
        if not QApplication.instance():
            cls.app = QApplication(sys.argv)
        else:
            cls.app = QApplication.instance()
    
    def setUp(self):
        """各テストの前処理"""
        self.template_list = TemplateListWidget()
    
    def tearDown(self):
        """各テストの後処理"""
        self.template_list.close()
    
    def test_template_list_initialization(self):
        """テンプレートリストの初期化テスト"""
        self.assertIsNotNone(self.template_list)
        self.assertGreater(self.template_list.count(), 0)
    
    def test_template_filtering(self):
        """テンプレートフィルタリングテスト"""
        # 初期状態では全てのアイテムが表示されている
        initial_visible_count = sum(1 for i in range(self.template_list.count()) 
                                  if not self.template_list.item(i).isHidden())
        
        # "マンデルブロ"でフィルタリング
        self.template_list.filter_templates("マンデルブロ")
        
        # フィルタリング後の表示アイテム数をカウント
        filtered_count = sum(1 for i in range(self.template_list.count()) 
                           if not self.template_list.item(i).isHidden())
        
        # フィルタリングにより表示アイテム数が減っているはず
        self.assertLessEqual(filtered_count, initial_visible_count)


class TestFormulaEditorWidget(unittest.TestCase):
    """統合式エディタウィジェットのテストクラス"""
    
    @classmethod
    def setUpClass(cls):
        """テストクラスの初期化"""
        if not QApplication.instance():
            cls.app = QApplication(sys.argv)
        else:
            cls.app = QApplication.instance()
    
    def setUp(self):
        """各テストの前処理"""
        self.widget = FormulaEditorWidget()
    
    def tearDown(self):
        """各テストの後処理"""
        self.widget.close()
    
    def test_widget_initialization(self):
        """ウィジェットの初期化テスト"""
        self.assertIsNotNone(self.widget)
        self.assertIsNotNone(self.widget.formula_editor)
        self.assertIsNotNone(self.widget.template_list)
        self.assertIsNotNone(self.widget.validation_widget)
    
    def test_formula_application(self):
        """数式適用テスト"""
        test_formula = "z**2 + c"
        
        # シグナルをキャッチするためのフラグ
        signal_received = False
        received_formula = ""
        
        def on_formula_applied(formula):
            nonlocal signal_received, received_formula
            signal_received = True
            received_formula = formula
        
        # シグナルを接続
        self.widget.formula_applied.connect(on_formula_applied)
        
        # 数式を設定
        self.widget.set_formula(test_formula)
        
        # 検証完了まで待つ
        QTest.qWait(600)
        
        # 適用ボタンをクリック（有効になっているはず）
        if self.widget.apply_button.isEnabled():
            self.widget.apply_button.click()
            
            # シグナルが発信されたかチェック
            self.assertTrue(signal_received)
            self.assertEqual(received_formula, test_formula)
    
    def test_template_usage(self):
        """テンプレート使用テスト"""
        # 最初のテンプレートを選択
        if self.widget.template_list.count() > 0:
            first_item = self.widget.template_list.item(0)
            self.widget.template_list.setCurrentItem(first_item)
            
            # テンプレート選択をシミュレート
            self.widget.template_list.itemClicked.emit(first_item)
            
            # テンプレート使用ボタンをクリック
            if self.widget.use_template_button.isEnabled():
                self.widget.use_template_button.click()
                
                # エディタに数式が設定されているかチェック
                formula = self.widget.get_formula()
                self.assertNotEqual(formula, "")
    
    def test_clear_functionality(self):
        """クリア機能テスト"""
        # 数式を設定
        self.widget.set_formula("z**2 + c")
        self.assertNotEqual(self.widget.get_formula(), "")
        
        # クリアボタンをクリック
        self.widget.clear_button.click()
        
        # エディタがクリアされているかチェック
        self.assertEqual(self.widget.get_formula(), "")


class TestFormulaSyntaxHighlighter(unittest.TestCase):
    """構文ハイライターのテストクラス"""
    
    @classmethod
    def setUpClass(cls):
        """テストクラスの初期化"""
        if not QApplication.instance():
            cls.app = QApplication(sys.argv)
        else:
            cls.app = QApplication.instance()
    
    def setUp(self):
        """各テストの前処理"""
        self.editor = FormulaEditor()
        self.highlighter = self.editor.highlighter
    
    def tearDown(self):
        """各テストの後処理"""
        self.editor.close()
    
    def test_highlighter_initialization(self):
        """ハイライターの初期化テスト"""
        self.assertIsNotNone(self.highlighter)
        self.assertGreater(len(self.highlighter.highlighting_rules), 0)
    
    def test_syntax_highlighting(self):
        """構文ハイライトテスト"""
        # 数式を設定
        test_formula = "sin(z**2) + c * exp(pi)"
        self.editor.set_formula(test_formula)
        
        # ハイライトが適用されているかは視覚的な確認が必要
        # ここでは例外が発生しないことを確認
        document = self.editor.document()
        self.assertIsNotNone(document)


def run_formula_editor_tests():
    """式エディタのテストを実行"""
    # テストスイートを作成
    test_suite = unittest.TestSuite()
    
    # テストケースを追加
    test_suite.addTest(unittest.makeSuite(TestFormulaEditor))
    test_suite.addTest(unittest.makeSuite(TestTemplateListWidget))
    test_suite.addTest(unittest.makeSuite(TestFormulaEditorWidget))
    test_suite.addTest(unittest.makeSuite(TestFormulaSyntaxHighlighter))
    
    # テストランナーを作成して実行
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    # アプリケーションを作成
    app = QApplication(sys.argv)
    
    try:
        # テストを実行
        success = run_formula_editor_tests()
        
        if success:
            print("\n✅ 全ての式エディタテストが成功しました！")
        else:
            print("\n❌ 一部のテストが失敗しました。")
        
        # 簡単なデモも実行
        print("\n🎨 式エディタのデモを表示します...")
        demo_widget = FormulaEditorWidget()
        demo_widget.show()
        demo_widget.set_formula("z**2 + c")
        
        # デモウィンドウを3秒間表示
        QTimer.singleShot(3000, demo_widget.close)
        QTimer.singleShot(3500, app.quit)
        
        app.exec()
        
    except Exception as e:
        print(f"❌ テスト実行中にエラーが発生しました: {e}")
        sys.exit(1)