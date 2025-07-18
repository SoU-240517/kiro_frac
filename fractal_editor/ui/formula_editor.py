"""
式エディタウィジェット

構文ハイライト機能付きテキストエディタ、リアルタイム構文検証、
式テンプレート選択機能を提供する式エディタUIコンポーネント。
"""

import re
from typing import Optional, Dict, Any, List, Callable
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QLabel, 
    QComboBox, QPushButton, QSplitter, QGroupBox, QListWidget,
    QListWidgetItem, QTextBrowser, QMessageBox, QFrame,
    QScrollArea, QSizePolicy
)
from PyQt6.QtCore import (
    Qt, QTimer, pyqtSignal, QThread, pyqtSlot
)
from PyQt6.QtGui import (
    QTextCharFormat, QColor, QFont, QSyntaxHighlighter,
    QTextDocument, QTextCursor, QPalette
)

from ..services.formula_parser import (
    FormulaParser, FormulaValidationError, FormulaEvaluationError,
    FormulaTemplate
)
from ..services.template_manager import enhanced_template_manager


class FormulaSyntaxHighlighter(QSyntaxHighlighter):
    """数式用の構文ハイライター"""
    
    def __init__(self, parent: QTextDocument):
        super().__init__(parent)
        self._setup_highlighting_rules()
    
    def _setup_highlighting_rules(self):
        """ハイライトルールを設定"""
        self.highlighting_rules = []
        
        # 数値のハイライト
        number_format = QTextCharFormat()
        number_format.setForeground(QColor(0, 0, 255))  # 青色
        number_pattern = r'\b\d+\.?\d*\b'
        self.highlighting_rules.append((re.compile(number_pattern), number_format))
        
        # 変数のハイライト
        variable_format = QTextCharFormat()
        variable_format.setForeground(QColor(128, 0, 128))  # 紫色
        variable_format.setFontWeight(QFont.Weight.Bold)
        variables = ['z', 'c', 'n', 'pi', 'e', 'i', 'j']
        for var in variables:
            pattern = rf'\b{var}\b'
            self.highlighting_rules.append((re.compile(pattern), variable_format))
        
        # 関数のハイライト
        function_format = QTextCharFormat()
        function_format.setForeground(QColor(0, 128, 0))  # 緑色
        function_format.setFontWeight(QFont.Weight.Bold)
        functions = [
            'sin', 'cos', 'tan', 'sinh', 'cosh', 'tanh',
            'asin', 'acos', 'atan', 'asinh', 'acosh', 'atanh',
            'exp', 'log', 'log10', 'sqrt', 'abs', 'conj',
            'real', 'imag', 'phase', 'polar', 'rect',
            'floor', 'ceil', 'round', 'min', 'max'
        ]
        for func in functions:
            pattern = rf'\b{func}\b(?=\()'
            self.highlighting_rules.append((re.compile(pattern), function_format))
        
        # 演算子のハイライト
        operator_format = QTextCharFormat()
        operator_format.setForeground(QColor(255, 0, 0))  # 赤色
        operator_format.setFontWeight(QFont.Weight.Bold)
        operators = [r'\+', r'-', r'\*', r'/', r'\*\*', r'%', r'=']
        for op in operators:
            self.highlighting_rules.append((re.compile(op), operator_format))
        
        # 括弧のハイライト
        bracket_format = QTextCharFormat()
        bracket_format.setForeground(QColor(255, 165, 0))  # オレンジ色
        bracket_format.setFontWeight(QFont.Weight.Bold)
        bracket_pattern = r'[(){}[\]]'
        self.highlighting_rules.append((re.compile(bracket_pattern), bracket_format))
        
        # エラー部分のハイライト（後で動的に追加）
        self.error_format = QTextCharFormat()
        self.error_format.setBackground(QColor(255, 200, 200))  # 薄い赤色背景
        self.error_format.setUnderlineColor(QColor(255, 0, 0))
        self.error_format.setUnderlineStyle(QTextCharFormat.UnderlineStyle.WaveUnderline)
    
    def highlightBlock(self, text: str):
        """テキストブロックをハイライト"""
        # 基本的なハイライトルールを適用
        for pattern, format_obj in self.highlighting_rules:
            for match in pattern.finditer(text):
                start, end = match.span()
                self.setFormat(start, end - start, format_obj)
    
    def highlight_error(self, start_pos: int, length: int):
        """エラー部分をハイライト"""
        cursor = QTextCursor(self.document())
        cursor.setPosition(start_pos)
        cursor.setPosition(start_pos + length, QTextCursor.MoveMode.KeepAnchor)
        cursor.setCharFormat(self.error_format)


class FormulaValidationWorker(QThread):
    """バックグラウンドで数式検証を行うワーカースレッド"""
    
    validation_completed = pyqtSignal(dict)  # 検証結果を送信
    
    def __init__(self, formula: str):
        super().__init__()
        self.formula = formula
    
    def run(self):
        """検証を実行"""
        try:
            result = FormulaParser.test_formula(self.formula)
            self.validation_completed.emit(result)
        except Exception as e:
            error_result = {
                'formula': self.formula,
                'valid': False,
                'error': str(e),
                'test_results': []
            }
            self.validation_completed.emit(error_result)


class FormulaEditor(QTextEdit):
    """構文ハイライト機能付きの数式エディタ"""
    
    formula_changed = pyqtSignal(str)  # 数式が変更されたときのシグナル
    validation_result = pyqtSignal(dict)  # 検証結果のシグナル
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # エディタの設定
        self.setFont(QFont("Consolas", 12))
        self.setTabStopDistance(40)
        self.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        
        # 構文ハイライターを設定
        self.highlighter = FormulaSyntaxHighlighter(self.document())
        
        # 検証用のタイマー（入力後少し待ってから検証）
        self.validation_timer = QTimer()
        self.validation_timer.setSingleShot(True)
        self.validation_timer.timeout.connect(self._validate_formula)
        
        # 検証ワーカー
        self.validation_worker = None
        
        # テキスト変更時の処理
        self.textChanged.connect(self._on_text_changed)
        
        # プレースホルダーテキスト
        self.setPlaceholderText("数式を入力してください (例: z**2 + c)")
        
        # 初期状態
        self._last_validation_result = None
    
    def _on_text_changed(self):
        """テキストが変更されたときの処理"""
        formula = self.toPlainText().strip()
        self.formula_changed.emit(formula)
        
        # 検証タイマーをリセット（500ms後に検証実行）
        self.validation_timer.stop()
        if formula:
            self.validation_timer.start(500)
        else:
            # 空の場合は即座に結果をクリア
            self._clear_validation_result()
    
    def _validate_formula(self):
        """数式を検証"""
        formula = self.toPlainText().strip()
        if not formula:
            return
        
        # 既存のワーカーがあれば停止
        if self.validation_worker and self.validation_worker.isRunning():
            self.validation_worker.terminate()
            self.validation_worker.wait()
        
        # 新しいワーカーで検証開始
        self.validation_worker = FormulaValidationWorker(formula)
        self.validation_worker.validation_completed.connect(self._on_validation_completed)
        self.validation_worker.start()
    
    @pyqtSlot(dict)
    def _on_validation_completed(self, result: dict):
        """検証完了時の処理"""
        self._last_validation_result = result
        self.validation_result.emit(result)
        
        # エラーがある場合はハイライト
        if not result.get('valid', False):
            self._highlight_syntax_errors(result.get('error', ''))
    
    def _highlight_syntax_errors(self, error_message: str):
        """構文エラーをハイライト"""
        # 簡単なエラーハイライト（実際の実装では更に詳細に）
        if 'syntax error' in error_message.lower():
            # 構文エラーの場合、全体を薄くハイライト
            cursor = QTextCursor(self.document())
            cursor.select(QTextCursor.SelectionType.Document)
            format_obj = QTextCharFormat()
            format_obj.setBackground(QColor(255, 240, 240))
            cursor.setCharFormat(format_obj)
    
    def _clear_validation_result(self):
        """検証結果をクリア"""
        self._last_validation_result = None
        self.validation_result.emit({'valid': True, 'formula': '', 'error': None})
    
    def set_formula(self, formula: str):
        """数式を設定"""
        self.setPlainText(formula)
    
    def get_formula(self) -> str:
        """現在の数式を取得"""
        return self.toPlainText().strip()
    
    def get_last_validation_result(self) -> Optional[Dict[str, Any]]:
        """最後の検証結果を取得"""
        return self._last_validation_result
    
    def insert_text_at_cursor(self, text: str):
        """カーソル位置にテキストを挿入"""
        cursor = self.textCursor()
        cursor.insertText(text)
        self.setTextCursor(cursor)


class TemplateListWidget(QListWidget):
    """式テンプレートのリストウィジェット"""
    
    template_selected = pyqtSignal(FormulaTemplate)  # テンプレートが選択されたときのシグナル
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._load_templates()
        
        # アイテムがクリックされたときの処理
        self.itemClicked.connect(self._on_item_clicked)
        
        # ダブルクリックで適用
        self.itemDoubleClicked.connect(self._on_item_double_clicked)
    
    def _load_templates(self):
        """テンプレートを読み込み"""
        templates = enhanced_template_manager.get_all_templates()
        
        for name, template in templates.items():
            item = QListWidgetItem(name)
            item.setData(Qt.ItemDataRole.UserRole, template)
            item.setToolTip(f"{template.description}\n数式: {template.formula}")
            self.addItem(item)
    
    def _on_item_clicked(self, item: QListWidgetItem):
        """アイテムがクリックされたときの処理"""
        template = item.data(Qt.ItemDataRole.UserRole)
        if template:
            self.template_selected.emit(template)
    
    def _on_item_double_clicked(self, item: QListWidgetItem):
        """アイテムがダブルクリックされたときの処理"""
        # ダブルクリックでは特別な処理は行わない（シングルクリックと同じ）
        pass
    
    def filter_templates(self, query: str):
        """テンプレートをフィルタリング"""
        query_lower = query.lower()
        
        for i in range(self.count()):
            item = self.item(i)
            template = item.data(Qt.ItemDataRole.UserRole)
            
            # 名前、説明、数式のいずれかにクエリが含まれているかチェック
            visible = (
                query_lower in template.name.lower() or
                query_lower in template.description.lower() or
                query_lower in template.formula.lower()
            )
            
            item.setHidden(not visible)


class TemplateDetailWidget(QTextBrowser):
    """テンプレートの詳細表示ウィジェット"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMaximumHeight(150)
        self._clear_content()
    
    def show_template(self, template: FormulaTemplate):
        """テンプレートの詳細を表示"""
        html = f"""
        <h3>{template.name}</h3>
        <p><strong>数式:</strong> <code>{template.formula}</code></p>
        <p><strong>説明:</strong> {template.description}</p>
        """
        
        if template.example_params:
            html += "<p><strong>推奨パラメータ:</strong></p><ul>"
            for key, value in template.example_params.items():
                html += f"<li>{key}: {value}</li>"
            html += "</ul>"
        
        self.setHtml(html)
    
    def _clear_content(self):
        """内容をクリア"""
        self.setHtml("<p>テンプレートを選択してください</p>")


class ValidationResultWidget(QFrame):
    """検証結果表示ウィジェット"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self._clear_result()
    
    def _setup_ui(self):
        """UIを設定"""
        layout = QVBoxLayout(self)
        
        # ステータスラベル
        self.status_label = QLabel()
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)
        
        # 詳細情報（スクロール可能）
        self.detail_browser = QTextBrowser()
        self.detail_browser.setMaximumHeight(100)
        layout.addWidget(self.detail_browser)
        
        # フレームのスタイル
        self.setFrameStyle(QFrame.Shape.StyledPanel)
        self.setLineWidth(1)
    
    def show_result(self, result: Dict[str, Any]):
        """検証結果を表示"""
        if not result:
            self._clear_result()
            return
        
        formula = result.get('formula', '')
        valid = result.get('valid', False)
        error = result.get('error', '')
        
        if valid:
            # 成功の場合
            self.status_label.setText("✅ 数式は有効です")
            self.status_label.setStyleSheet("color: green; font-weight: bold;")
            
            # 詳細情報
            complexity = result.get('complexity', 0)
            variables = result.get('variables', [])
            
            detail_html = f"""
            <p><strong>複雑度スコア:</strong> {complexity:.1f}</p>
            <p><strong>使用変数:</strong> {', '.join(variables) if variables else 'なし'}</p>
            """
            
            test_results = result.get('test_results', [])
            if test_results:
                all_passed = result.get('all_tests_passed', False)
                detail_html += f"<p><strong>テスト結果:</strong> {'✅ 全て成功' if all_passed else '⚠️ 一部失敗'}</p>"
            
            self.detail_browser.setHtml(detail_html)
            
        else:
            # エラーの場合
            self.status_label.setText(f"❌ エラー: {error}")
            self.status_label.setStyleSheet("color: red; font-weight: bold;")
            
            # エラーの詳細
            detail_html = f"""
            <p><strong>数式:</strong> <code>{formula}</code></p>
            <p><strong>エラー詳細:</strong> {error}</p>
            <p><strong>ヒント:</strong></p>
            <ul>
                <li>使用可能な変数: z, c, n, pi, e, i, j</li>
                <li>使用可能な関数: sin, cos, exp, log, sqrt, abs など</li>
                <li>括弧の対応を確認してください</li>
            </ul>
            """
            self.detail_browser.setHtml(detail_html)
    
    def _clear_result(self):
        """結果をクリア"""
        self.status_label.setText("数式を入力してください")
        self.status_label.setStyleSheet("color: gray;")
        self.detail_browser.setHtml("")


class FormulaEditorWidget(QWidget):
    """式エディタの統合ウィジェット"""
    
    formula_applied = pyqtSignal(str)  # 数式が適用されたときのシグナル
    formula_changed = pyqtSignal(str)  # 数式が変更されたときのシグナル
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self._connect_signals()
        self._current_template = None
    
    def _setup_ui(self):
        """UIを設定"""
        layout = QVBoxLayout(self)
        
        # メインスプリッター（横分割）
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(main_splitter)
        
        # 左側：エディタ部分
        editor_widget = QWidget()
        editor_layout = QVBoxLayout(editor_widget)
        
        # エディタのタイトル
        editor_title = QLabel("数式エディタ")
        editor_title.setStyleSheet("font-weight: bold; font-size: 14px;")
        editor_layout.addWidget(editor_title)
        
        # 数式エディタ
        self.formula_editor = FormulaEditor()
        editor_layout.addWidget(self.formula_editor)
        
        # 検証結果表示
        validation_group = QGroupBox("検証結果")
        validation_layout = QVBoxLayout(validation_group)
        self.validation_widget = ValidationResultWidget()
        validation_layout.addWidget(self.validation_widget)
        editor_layout.addWidget(validation_group)
        
        # 適用ボタン
        button_layout = QHBoxLayout()
        self.apply_button = QPushButton("数式を適用")
        self.apply_button.setEnabled(False)
        self.clear_button = QPushButton("クリア")
        button_layout.addWidget(self.apply_button)
        button_layout.addWidget(self.clear_button)
        button_layout.addStretch()
        editor_layout.addLayout(button_layout)
        
        main_splitter.addWidget(editor_widget)
        
        # 右側：テンプレート部分
        template_widget = QWidget()
        template_layout = QVBoxLayout(template_widget)
        
        # テンプレートのタイトル
        template_title = QLabel("式テンプレート")
        template_title.setStyleSheet("font-weight: bold; font-size: 14px;")
        template_layout.addWidget(template_title)
        
        # テンプレートリスト
        self.template_list = TemplateListWidget()
        template_layout.addWidget(self.template_list)
        
        # テンプレート詳細
        detail_group = QGroupBox("テンプレート詳細")
        detail_layout = QVBoxLayout(detail_group)
        self.template_detail = TemplateDetailWidget()
        detail_layout.addWidget(self.template_detail)
        
        # テンプレート操作ボタン
        template_button_layout = QHBoxLayout()
        self.use_template_button = QPushButton("使用")
        self.use_template_button.setEnabled(False)
        self.save_template_button = QPushButton("保存")
        self.delete_template_button = QPushButton("削除")
        self.delete_template_button.setEnabled(False)
        
        template_button_layout.addWidget(self.use_template_button)
        template_button_layout.addWidget(self.save_template_button)
        template_button_layout.addWidget(self.delete_template_button)
        detail_layout.addLayout(template_button_layout)
        
        template_layout.addWidget(detail_group)
        
        main_splitter.addWidget(template_widget)
        
        # スプリッターの初期サイズ設定
        main_splitter.setSizes([400, 300])
    
    def _connect_signals(self):
        """シグナルを接続"""
        # エディタからのシグナル
        self.formula_editor.formula_changed.connect(self.formula_changed.emit)
        self.formula_editor.validation_result.connect(self._on_validation_result)
        
        # テンプレートからのシグナル
        self.template_list.template_selected.connect(self._on_template_selected)
        
        # ボタンのシグナル
        self.apply_button.clicked.connect(self._on_apply_clicked)
        self.clear_button.clicked.connect(self._on_clear_clicked)
        self.use_template_button.clicked.connect(self._on_use_template_clicked)
        self.save_template_button.clicked.connect(self._on_save_template_clicked)
        self.delete_template_button.clicked.connect(self._on_delete_template_clicked)
    
    def _on_validation_result(self, result: Dict[str, Any]):
        """検証結果を受信"""
        self.validation_widget.show_result(result)
        
        # 適用ボタンの有効/無効を切り替え
        valid = result.get('valid', False)
        has_formula = bool(result.get('formula', '').strip())
        self.apply_button.setEnabled(valid and has_formula)
    
    def _on_template_selected(self, template: FormulaTemplate):
        """テンプレートが選択された"""
        self._current_template = template
        self.template_detail.show_template(template)
        self.use_template_button.setEnabled(True)
    
    def _on_apply_clicked(self):
        """適用ボタンがクリックされた"""
        formula = self.formula_editor.get_formula()
        if formula:
            self.formula_applied.emit(formula)
    
    def _on_clear_clicked(self):
        """クリアボタンがクリックされた"""
        self.formula_editor.clear()
    
    def _on_use_template_clicked(self):
        """テンプレート使用ボタンがクリックされた"""
        if self._current_template:
            self.formula_editor.set_formula(self._current_template.formula)
    
    def set_formula(self, formula: str):
        """数式を設定"""
        self.formula_editor.set_formula(formula)
    
    def get_formula(self) -> str:
        """現在の数式を取得"""
        return self.formula_editor.get_formula()
    
    def get_current_template(self) -> Optional[FormulaTemplate]:
        """現在選択されているテンプレートを取得"""
        return self._current_template
    
    def _on_save_template_clicked(self):
        """テンプレート保存ボタンがクリックされた"""
        formula = self.formula_editor.get_formula()
        if not formula:
            QMessageBox.warning(self, "警告", "保存する数式を入力してください。")
            return
        
        # 数式の妥当性を確認
        result = self.formula_editor.get_last_validation_result()
        if not result or not result.get('valid', False):
            QMessageBox.warning(self, "警告", "有効な数式を入力してください。")
            return
        
        # テンプレート保存ダイアログを表示
        self._show_save_template_dialog(formula)
    
    def _on_delete_template_clicked(self):
        """テンプレート削除ボタンがクリックされた"""
        if not self._current_template:
            return
        
        # 組み込みテンプレートは削除できない
        template_info = enhanced_template_manager.get_template_info(self._current_template.name)
        if template_info.get('type') == 'builtin':
            QMessageBox.information(self, "情報", "組み込みテンプレートは削除できません。")
            return
        
        # 削除確認
        reply = QMessageBox.question(
            self, "確認", 
            f"テンプレート '{self._current_template.name}' を削除しますか？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            if enhanced_template_manager.remove_custom_template(self._current_template.name):
                QMessageBox.information(self, "成功", "テンプレートを削除しました。")
                self._refresh_template_list()
                self.template_detail._clear_content()
                self._current_template = None
                self.use_template_button.setEnabled(False)
                self.delete_template_button.setEnabled(False)
            else:
                QMessageBox.critical(self, "エラー", "テンプレートの削除に失敗しました。")
    
    def _show_save_template_dialog(self, formula: str):
        """テンプレート保存ダイアログを表示"""
        from PyQt6.QtWidgets import QDialog, QFormLayout, QLineEdit, QTextEdit, QDialogButtonBox
        
        dialog = QDialog(self)
        dialog.setWindowTitle("テンプレートを保存")
        dialog.setModal(True)
        dialog.resize(400, 300)
        
        layout = QFormLayout(dialog)
        
        # 名前入力
        name_edit = QLineEdit()
        name_edit.setPlaceholderText("テンプレート名を入力")
        layout.addRow("名前:", name_edit)
        
        # 説明入力
        description_edit = QTextEdit()
        description_edit.setPlaceholderText("テンプレートの説明を入力")
        description_edit.setMaximumHeight(80)
        layout.addRow("説明:", description_edit)
        
        # 作成者入力
        author_edit = QLineEdit()
        settings = enhanced_template_manager.get_settings()
        author_edit.setText(settings.get('default_author', ''))
        author_edit.setPlaceholderText("作成者名（省略可）")
        layout.addRow("作成者:", author_edit)
        
        # タグ入力
        tags_edit = QLineEdit()
        tags_edit.setPlaceholderText("タグをカンマ区切りで入力（省略可）")
        layout.addRow("タグ:", tags_edit)
        
        # 数式表示（読み取り専用）
        formula_edit = QLineEdit(formula)
        formula_edit.setReadOnly(True)
        layout.addRow("数式:", formula_edit)
        
        # ボタン
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addRow(buttons)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            name = name_edit.text().strip()
            if not name:
                QMessageBox.warning(self, "警告", "テンプレート名を入力してください。")
                return
            
            description = description_edit.toPlainText().strip()
            author = author_edit.text().strip()
            tags_text = tags_edit.text().strip()
            tags = [tag.strip() for tag in tags_text.split(',') if tag.strip()] if tags_text else []
            
            # テンプレートを作成
            success = enhanced_template_manager.create_template_from_formula(
                name=name,
                formula=formula,
                description=description,
                author=author,
                tags=tags
            )
            
            if success:
                QMessageBox.information(self, "成功", f"テンプレート '{name}' を保存しました。")
                self._refresh_template_list()
                
                # 作成者をデフォルトとして保存
                if author:
                    settings['default_author'] = author
                    enhanced_template_manager.update_settings(settings)
            else:
                QMessageBox.critical(self, "エラー", "テンプレートの保存に失敗しました。")
    
    def _refresh_template_list(self):
        """テンプレートリストを更新"""
        self.template_list.clear()
        self.template_list._load_templates()
    
    def _on_template_selected(self, template: FormulaTemplate):
        """テンプレートが選択された"""
        self._current_template = template
        self.template_detail.show_template(template)
        self.use_template_button.setEnabled(True)
        
        # カスタムテンプレートの場合のみ削除ボタンを有効化
        try:
            template_info = enhanced_template_manager.get_template_info(template.name)
            is_custom = template_info.get('type') == 'custom'
            self.delete_template_button.setEnabled(is_custom)
        except KeyError:
            self.delete_template_button.setEnabled(False)
    
    def refresh_templates(self):
        """テンプレートを再読み込み"""
        self._refresh_template_list()
    
    def show_help(self):
        """ヘルプダイアログを表示"""
        help_text = """
        <h2>数式エディタの使い方</h2>
        
        <h3>基本的な使い方</h3>
        <ul>
            <li>左側のエディタに数式を入力します</li>
            <li>右側のテンプレートから既存の式を選択できます</li>
            <li>入力した数式は自動的に検証されます</li>
            <li>「数式を適用」ボタンで数式を確定します</li>
        </ul>
        
        <h3>テンプレート機能</h3>
        <ul>
            <li>「使用」ボタンでテンプレートの数式をエディタに読み込み</li>
            <li>「保存」ボタンで現在の数式をテンプレートとして保存</li>
            <li>「削除」ボタンでカスタムテンプレートを削除（組み込みは削除不可）</li>
        </ul>
        
        <h3>使用可能な要素</h3>
        <p><strong>変数:</strong> z, c, n, pi, e, i, j</p>
        <p><strong>演算子:</strong> +, -, *, /, **, %</p>
        <p><strong>関数:</strong></p>
        <ul>
            <li>三角関数: sin, cos, tan, sinh, cosh, tanh</li>
            <li>逆三角関数: asin, acos, atan, asinh, acosh, atanh</li>
            <li>指数・対数: exp, log, log10, sqrt</li>
            <li>複素数: abs, conj, real, imag, phase, polar, rect</li>
            <li>その他: floor, ceil, round, min, max</li>
        </ul>
        
        <h3>数式の例</h3>
        <ul>
            <li><code>z**2 + c</code> - マンデルブロ集合</li>
            <li><code>z**3 + c</code> - 三次マンデルブロ</li>
            <li><code>sin(z) + c</code> - 正弦フラクタル</li>
            <li><code>exp(z) + c</code> - 指数フラクタル</li>
        </ul>
        """
        
        msg = QMessageBox()
        msg.setWindowTitle("数式エディタ ヘルプ")
        msg.setTextFormat(Qt.TextFormat.RichText)
        msg.setText(help_text)
        msg.exec()