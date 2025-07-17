"""
Error handling service for the Fractal Editor application.
"""
import logging
from typing import Union
from ..models.data_models import FractalParameters


class FractalCalculationException(Exception):
    """Exception raised during fractal calculation."""
    
    def __init__(self, message: str, parameters: FractalParameters, stage: str):
        super().__init__(message)
        self.parameters = parameters
        self.stage = stage


class FormulaValidationError(Exception):
    """Exception raised when formula validation fails."""
    pass


class FormulaEvaluationError(Exception):
    """Exception raised when formula evaluation fails."""
    pass


class PluginLoadError(Exception):
    """Exception raised when plugin loading fails."""
    
    def __init__(self, message: str, plugin_name: str = "", plugin_path: str = ""):
        super().__init__(message)
        self.plugin_name = plugin_name
        self.plugin_path = plugin_path


class ErrorHandlingService:
    """Service for handling application errors."""
    
    def __init__(self):
        """Initialize the error handling service."""
        self.logger = logging.getLogger(__name__)
        self._setup_logging()
    
    def _setup_logging(self) -> None:
        """Set up logging configuration."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('fractal_editor.log'),
                logging.StreamHandler()
            ]
        )
    
    def handle_calculation_error(self, ex: FractalCalculationException) -> None:
        """Handle fractal calculation errors."""
        self.logger.error(f"Fractal calculation failed at stage: {ex.stage}, Error: {ex}")
        # UI notification will be implemented when PyQt6 UI is ready
        print(f"計算エラー: フラクタル計算でエラーが発生しました: {ex}")
    
    def handle_formula_error(self, ex: Union[FormulaValidationError, FormulaEvaluationError]) -> None:
        """Handle formula validation and evaluation errors."""
        self.logger.error(f"Formula error: {ex}")
        # UI notification will be implemented when PyQt6 UI is ready
        print(f"数式エラー: 数式にエラーがあります: {ex}")
        print("使用可能な変数: z, c, n")
        print("使用可能な関数: sin, cos, tan, exp, log, sqrt, abs, conj")
    
    def handle_general_error(self, ex: Exception, context: str = "") -> None:
        """Handle general application errors."""
        self.logger.error(f"General error in {context}: {ex}")
        print(f"エラー: {context}で問題が発生しました: {ex}")