"""
数式パーサーとバリデーター

このモジュールは、ユーザー定義の数式を安全に解析・評価するためのクラスを提供します。
ASTベースの検証システムにより、危険なコードの実行を防ぎます。
"""

import ast
import operator
import math
import cmath
from typing import Dict, Any, Set, Union, Callable
from dataclasses import dataclass


class FormulaValidationError(Exception):
    """数式検証エラー"""
    pass


class FormulaEvaluationError(Exception):
    """数式評価エラー"""
    pass


@dataclass
class FormulaTemplate:
    """式テンプレートを表現するデータクラス"""
    name: str
    formula: str
    description: str
    example_params: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.example_params is None:
            self.example_params = {}


class FormulaParser:
    """複素数式を解析・評価するクラス"""
    
    # 許可された演算子と対応する関数
    ALLOWED_OPERATORS = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.Pow: operator.pow,
        ast.USub: operator.neg,
        ast.UAdd: operator.pos,
        ast.Mod: operator.mod,
    }
    
    # 許可された関数と対応する実装
    ALLOWED_FUNCTIONS = {
        # 基本数学関数
        'sin': cmath.sin,
        'cos': cmath.cos,
        'tan': cmath.tan,
        'sinh': cmath.sinh,
        'cosh': cmath.cosh,
        'tanh': cmath.tanh,
        'asin': cmath.asin,
        'acos': cmath.acos,
        'atan': cmath.atan,
        'asinh': cmath.asinh,
        'acosh': cmath.acosh,
        'atanh': cmath.atanh,
        
        # 指数・対数関数
        'exp': cmath.exp,
        'log': cmath.log,
        'log10': cmath.log10,
        'sqrt': cmath.sqrt,
        
        # 複素数関数
        'abs': abs,
        'conj': lambda x: x.conjugate() if hasattr(x, 'conjugate') else complex(x).conjugate(),
        'real': lambda x: x.real if hasattr(x, 'real') else complex(x).real,
        'imag': lambda x: x.imag if hasattr(x, 'imag') else complex(x).imag,
        'phase': cmath.phase,
        'polar': cmath.polar,
        'rect': cmath.rect,
        
        # その他の数学関数
        'floor': math.floor,
        'ceil': math.ceil,
        'round': round,
        'min': min,
        'max': max,
    }
    
    # 許可された変数名
    ALLOWED_VARIABLES = {
        'z',    # 現在の複素数値
        'c',    # 複素数パラメータ
        'n',    # 反復回数
        'pi',   # 円周率
        'e',    # 自然対数の底
        'i',    # 虚数単位
        'j',    # 虚数単位（Python形式）
    }
    
    # 許可された定数
    ALLOWED_CONSTANTS = {
        'pi': math.pi,
        'e': math.e,
        'i': 1j,
        'j': 1j,
    }
    
    def __init__(self, formula: str):
        """
        数式パーサーを初期化
        
        Args:
            formula: 解析する数式文字列
            
        Raises:
            FormulaValidationError: 数式が無効な場合
        """
        self.formula = formula.strip()
        self.compiled_formula = None
        self._ast_tree = None
        self._validate_and_compile()
    
    def _validate_and_compile(self) -> None:
        """数式の妥当性を検証し、コンパイルする"""
        if not self.formula:
            raise FormulaValidationError("Formula cannot be empty")
        
        try:
            # 数式をASTに解析
            self._ast_tree = ast.parse(self.formula, mode='eval')
            
            # ASTの安全性を検証
            self._validate_ast(self._ast_tree)
            
            # 数式をコンパイル
            self.compiled_formula = compile(self._ast_tree, '<formula>', 'eval')
            
        except SyntaxError as e:
            raise FormulaValidationError(f"Syntax error in formula: {e}")
        except ValueError as e:
            raise FormulaValidationError(f"Invalid formula: {e}")
        except Exception as e:
            raise FormulaValidationError(f"Unexpected error parsing formula: {e}")
    
    def _validate_ast(self, node: ast.AST) -> None:
        """ASTノードの安全性を再帰的に検証"""
        if isinstance(node, ast.Expression):
            self._validate_ast(node.body)
            
        elif isinstance(node, ast.BinOp):
            # 二項演算子の検証
            if type(node.op) not in self.ALLOWED_OPERATORS:
                raise ValueError(f"Operator {type(node.op).__name__} is not allowed")
            self._validate_ast(node.left)
            self._validate_ast(node.right)
            
        elif isinstance(node, ast.UnaryOp):
            # 単項演算子の検証
            if type(node.op) not in self.ALLOWED_OPERATORS:
                raise ValueError(f"Unary operator {type(node.op).__name__} is not allowed")
            self._validate_ast(node.operand)
            
        elif isinstance(node, ast.Call):
            # 関数呼び出しの検証
            if not isinstance(node.func, ast.Name):
                raise ValueError("Only simple function calls are allowed")
            
            func_name = node.func.id
            if func_name not in self.ALLOWED_FUNCTIONS:
                raise ValueError(f"Function '{func_name}' is not allowed")
            
            # 引数の数をチェック（ほとんどの数学関数は1つの引数を期待）
            if func_name in ['min', 'max']:
                # min, maxは複数の引数を受け取る
                if len(node.args) < 2:
                    raise ValueError(f"Function '{func_name}' requires at least 2 arguments")
            elif func_name in ['rect']:
                # rectは2つの引数を受け取る
                if len(node.args) != 2:
                    raise ValueError(f"Function '{func_name}' requires exactly 2 arguments")
            else:
                # その他の関数は1つの引数を期待
                if len(node.args) != 1:
                    raise ValueError(f"Function '{func_name}' requires exactly 1 argument")
            
            # 引数の検証
            for arg in node.args:
                self._validate_ast(arg)
            
            # キーワード引数は許可しない
            if node.keywords:
                raise ValueError("Keyword arguments are not allowed in functions")
                
        elif isinstance(node, ast.Constant):
            # 定数の検証（Python 3.8+）
            if not isinstance(node.value, (int, float, complex)):
                raise ValueError(f"Constant type {type(node.value)} is not allowed")
                
        elif isinstance(node, ast.Num):
            # 数値の検証（Python 3.7以前の互換性）
            if not isinstance(node.n, (int, float, complex)):
                raise ValueError(f"Number type {type(node.n)} is not allowed")
                
        elif isinstance(node, ast.Name):
            # 変数名の検証
            if node.id not in self.ALLOWED_VARIABLES:
                raise ValueError(f"Variable '{node.id}' is not allowed")
                
        elif isinstance(node, ast.Compare):
            # 比較演算子（将来の拡張用）
            raise ValueError("Comparison operators are not allowed")
            
        elif isinstance(node, ast.BoolOp):
            # ブール演算子
            raise ValueError("Boolean operators are not allowed")
            
        elif isinstance(node, (ast.List, ast.Tuple, ast.Dict)):
            # コレクション型
            raise ValueError("Collections (list, tuple, dict) are not allowed")
            
        elif isinstance(node, ast.Attribute):
            # 属性アクセス
            raise ValueError("Attribute access is not allowed")
            
        elif isinstance(node, ast.Subscript):
            # インデックスアクセス
            raise ValueError("Subscript access is not allowed")
            
        else:
            raise ValueError(f"AST node type {type(node).__name__} is not allowed")
    
    def evaluate(self, z: complex, c: complex, n: int) -> complex:
        """
        数式を評価する
        
        Args:
            z: 現在の複素数値
            c: 複素数パラメータ
            n: 反復回数
            
        Returns:
            評価結果の複素数
            
        Raises:
            FormulaEvaluationError: 評価中にエラーが発生した場合
        """
        if not self.compiled_formula:
            raise RuntimeError("Formula not compiled")
        
        # 評価コンテキストを構築
        context = {
            'z': z,
            'c': c,
            'n': n,
            **self.ALLOWED_CONSTANTS,
            **self.ALLOWED_FUNCTIONS
        }
        
        try:
            # 数式を評価（builtinsを無効化してセキュリティを確保）
            result = eval(self.compiled_formula, {"__builtins__": {}}, context)
            
            # 結果を複素数に変換
            if isinstance(result, (int, float)):
                return complex(result, 0)
            elif isinstance(result, complex):
                return result
            else:
                raise ValueError(f"Formula must return a number, got {type(result)}")
                
        except ZeroDivisionError:
            raise FormulaEvaluationError("Division by zero in formula")
        except OverflowError:
            raise FormulaEvaluationError("Numerical overflow in formula")
        except ValueError as e:
            raise FormulaEvaluationError(f"Value error in formula: {e}")
        except Exception as e:
            raise FormulaEvaluationError(f"Error evaluating formula: {e}")
    
    def get_used_variables(self) -> Set[str]:
        """
        数式で使用されている変数名を取得
        
        Returns:
            使用されている変数名のセット
        """
        if not self._ast_tree:
            return set()
        
        variables = set()
        
        def collect_variables(node: ast.AST):
            if isinstance(node, ast.Name) and node.id in self.ALLOWED_VARIABLES:
                variables.add(node.id)
            for child in ast.iter_child_nodes(node):
                collect_variables(child)
        
        collect_variables(self._ast_tree)
        return variables
    
    def get_complexity_score(self) -> float:
        """
        数式の複雑度スコアを計算
        
        Returns:
            複雑度スコア（高いほど複雑）
        """
        if not self._ast_tree:
            return 0.0
        
        score = 0.0
        
        def calculate_complexity(node: ast.AST):
            nonlocal score
            
            if isinstance(node, ast.Expression):
                # Expression ノードは子ノードを処理するだけ
                pass
            elif isinstance(node, (ast.BinOp, ast.UnaryOp)):
                score += 1.0
            elif isinstance(node, ast.Call):
                score += 2.0  # 関数呼び出しは少し重い
            elif isinstance(node, ast.Name):
                if node.id in self.ALLOWED_VARIABLES:
                    score += 0.5  # 変数参照
            elif isinstance(node, (ast.Constant, ast.Num)):
                score += 0.1  # 定数
            
            for child in ast.iter_child_nodes(node):
                calculate_complexity(child)
        
        calculate_complexity(self._ast_tree)
        return score
    
    def validate_syntax_only(self) -> bool:
        """
        構文のみを検証（評価は行わない）
        
        Returns:
            構文が正しい場合True
        """
        try:
            self._validate_and_compile()
            return True
        except FormulaValidationError:
            return False
    
    @classmethod
    def validate_syntax_only(cls, formula: str) -> bool:
        """
        構文のみを検証（クラスメソッド版）
        
        Args:
            formula: 検証する数式
            
        Returns:
            構文が正しい場合True
        """
        try:
            cls(formula)
            return True
        except FormulaValidationError:
            return False
    
    @classmethod
    def test_formula(cls, formula: str, test_cases: list = None) -> Dict[str, Any]:
        """
        数式をテストケースで検証
        
        Args:
            formula: テストする数式
            test_cases: テストケースのリスト [(z, c, n, expected), ...]
            
        Returns:
            テスト結果の辞書
        """
        if test_cases is None:
            test_cases = [
                (0+0j, 0+0j, 0, None),  # 基本ケース
                (1+1j, 0.5+0.5j, 1, None),  # 一般的なケース
                (2+0j, -1+0j, 10, None),  # 実数ケース
            ]
        
        try:
            parser = cls(formula)
            results = []
            
            for i, test_case in enumerate(test_cases):
                z, c, n = test_case[:3]
                expected = test_case[3] if len(test_case) > 3 else None
                
                try:
                    result = parser.evaluate(z, c, n)
                    success = True
                    error = None
                    
                    if expected is not None:
                        # 期待値との比較（複素数の場合は近似比較）
                        if abs(result - expected) > 1e-10:
                            success = False
                            error = f"Expected {expected}, got {result}"
                            
                except Exception as e:
                    result = None
                    success = False
                    error = str(e)
                
                results.append({
                    'test_case': i,
                    'input': {'z': z, 'c': c, 'n': n},
                    'result': result,
                    'success': success,
                    'error': error
                })
            
            return {
                'formula': formula,
                'valid': True,
                'complexity': parser.get_complexity_score(),
                'variables': list(parser.get_used_variables()),
                'test_results': results,
                'all_tests_passed': all(r['success'] for r in results)
            }
            
        except FormulaValidationError as e:
            return {
                'formula': formula,
                'valid': False,
                'error': str(e),
                'test_results': []
            }


# プリセット式テンプレート
FORMULA_TEMPLATES = [
    FormulaTemplate(
        name="マンデルブロ集合",
        formula="z**2 + c",
        description="古典的なマンデルブロ集合の式",
        example_params={'max_iterations': 100}
    ),
    FormulaTemplate(
        name="ジュリア集合",
        formula="z**2 + c",
        description="ジュリア集合（cは固定パラメータ）",
        example_params={'c': -0.7269 + 0.1889j, 'max_iterations': 100}
    ),
    FormulaTemplate(
        name="バーニングシップ",
        formula="(abs(real(z)) + abs(imag(z))*1j)**2 + c",
        description="バーニングシップフラクタル",
        example_params={'max_iterations': 100}
    ),
    FormulaTemplate(
        name="三次マンデルブロ",
        formula="z**3 + c",
        description="三次のマンデルブロ集合",
        example_params={'max_iterations': 100}
    ),
    FormulaTemplate(
        name="四次マンデルブロ",
        formula="z**4 + c",
        description="四次のマンデルブロ集合",
        example_params={'max_iterations': 100}
    ),
    FormulaTemplate(
        name="指数フラクタル",
        formula="exp(z) + c",
        description="指数関数ベースのフラクタル",
        example_params={'max_iterations': 50}
    ),
    FormulaTemplate(
        name="正弦フラクタル",
        formula="sin(z) + c",
        description="正弦関数ベースのフラクタル",
        example_params={'max_iterations': 50}
    ),
    FormulaTemplate(
        name="余弦フラクタル",
        formula="cos(z) + c",
        description="余弦関数ベースのフラクタル",
        example_params={'max_iterations': 50}
    ),
    FormulaTemplate(
        name="双曲正弦フラクタル",
        formula="sinh(z) + c",
        description="双曲正弦関数ベースのフラクタル",
        example_params={'max_iterations': 50}
    ),
    FormulaTemplate(
        name="対数フラクタル",
        formula="log(z) + c",
        description="対数関数ベースのフラクタル",
        example_params={'max_iterations': 50}
    ),
    FormulaTemplate(
        name="平方根フラクタル",
        formula="sqrt(z) + c",
        description="平方根関数ベースのフラクタル",
        example_params={'max_iterations': 100}
    ),
    FormulaTemplate(
        name="複合式1",
        formula="z**2 + c / (z + 1)",
        description="複合的な数式の例",
        example_params={'max_iterations': 100}
    ),
    FormulaTemplate(
        name="複合式2",
        formula="sin(z**2) + c",
        description="三角関数と多項式の組み合わせ",
        example_params={'max_iterations': 100}
    ),
    FormulaTemplate(
        name="フェニックス",
        formula="z**2 + c + 0.5*conj(z)",
        description="フェニックスフラクタル",
        example_params={'max_iterations': 100}
    ),
    FormulaTemplate(
        name="マグネット1",
        formula="((z**2 + c - 1) / (2*z + c - 2))**2",
        description="マグネットフラクタル タイプ1",
        example_params={'max_iterations': 100}
    )
]


class FormulaTemplateManager:
    """式テンプレートを管理するクラス"""
    
    def __init__(self):
        self._templates = {template.name: template for template in FORMULA_TEMPLATES}
        self._custom_templates = {}
    
    def get_template(self, name: str) -> FormulaTemplate:
        """
        テンプレートを名前で取得
        
        Args:
            name: テンプレート名
            
        Returns:
            FormulaTemplate オブジェクト
            
        Raises:
            KeyError: テンプレートが見つからない場合
        """
        if name in self._templates:
            return self._templates[name]
        elif name in self._custom_templates:
            return self._custom_templates[name]
        else:
            raise KeyError(f"Template '{name}' not found")
    
    def list_templates(self) -> list[str]:
        """
        利用可能なテンプレート名のリストを取得
        
        Returns:
            テンプレート名のリスト
        """
        return list(self._templates.keys()) + list(self._custom_templates.keys())
    
    def get_all_templates(self) -> Dict[str, FormulaTemplate]:
        """
        すべてのテンプレートを取得
        
        Returns:
            テンプレート名をキーとする辞書
        """
        result = self._templates.copy()
        result.update(self._custom_templates)
        return result
    
    def add_custom_template(self, template: FormulaTemplate) -> None:
        """
        カスタムテンプレートを追加
        
        Args:
            template: 追加するテンプレート
        """
        # 数式の妥当性を検証
        try:
            FormulaParser(template.formula)
        except FormulaValidationError as e:
            raise ValueError(f"Invalid formula in template: {e}")
        
        self._custom_templates[template.name] = template
    
    def remove_custom_template(self, name: str) -> bool:
        """
        カスタムテンプレートを削除
        
        Args:
            name: 削除するテンプレート名
            
        Returns:
            削除に成功した場合True
        """
        if name in self._custom_templates:
            del self._custom_templates[name]
            return True
        return False
    
    def search_templates(self, query: str) -> list[FormulaTemplate]:
        """
        テンプレートを検索
        
        Args:
            query: 検索クエリ
            
        Returns:
            マッチしたテンプレートのリスト
        """
        query_lower = query.lower()
        results = []
        
        all_templates = self.get_all_templates()
        for template in all_templates.values():
            if (query_lower in template.name.lower() or 
                query_lower in template.description.lower() or
                query_lower in template.formula.lower()):
                results.append(template)
        
        return results


# グローバルテンプレートマネージャーインスタンス
template_manager = FormulaTemplateManager()