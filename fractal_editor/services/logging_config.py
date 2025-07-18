"""
ロギング設定管理モジュール
"""
import logging
import logging.config
from pathlib import Path
from typing import Dict, Any
import json


class LoggingConfig:
    """ロギング設定を管理するクラス"""
    
    DEFAULT_CONFIG = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'detailed': {
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
                'datefmt': '%Y-%m-%d %H:%M:%S'
            },
            'simple': {
                'format': '%(levelname)s - %(message)s'
            },
            'json': {
                'format': '{"timestamp": "%(asctime)s", "logger": "%(name)s", "level": "%(levelname)s", "function": "%(funcName)s", "line": %(lineno)d, "message": "%(message)s"}',
                'datefmt': '%Y-%m-%d %H:%M:%S'
            }
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'level': 'WARNING',
                'formatter': 'simple',
                'stream': 'ext://sys.stdout'
            },
            'file': {
                'class': 'logging.handlers.RotatingFileHandler',
                'level': 'DEBUG',
                'formatter': 'detailed',
                'filename': 'logs/fractal_editor.log',
                'maxBytes': 10485760,  # 10MB
                'backupCount': 5,
                'encoding': 'utf-8'
            },
            'error_file': {
                'class': 'logging.handlers.RotatingFileHandler',
                'level': 'ERROR',
                'formatter': 'detailed',
                'filename': 'logs/errors.log',
                'maxBytes': 5242880,  # 5MB
                'backupCount': 3,
                'encoding': 'utf-8'
            },
            'json_file': {
                'class': 'logging.handlers.RotatingFileHandler',
                'level': 'INFO',
                'formatter': 'json',
                'filename': 'logs/fractal_editor.json',
                'maxBytes': 10485760,  # 10MB
                'backupCount': 3,
                'encoding': 'utf-8'
            }
        },
        'loggers': {
            'fractal_editor': {
                'level': 'DEBUG',
                'handlers': ['console', 'file', 'error_file', 'json_file'],
                'propagate': False
            },
            'fractal_editor.calculation': {
                'level': 'INFO',
                'handlers': ['file', 'error_file'],
                'propagate': False
            },
            'fractal_editor.ui': {
                'level': 'WARNING',
                'handlers': ['console', 'file', 'error_file'],
                'propagate': False
            },
            'fractal_editor.plugins': {
                'level': 'INFO',
                'handlers': ['file', 'error_file'],
                'propagate': False
            }
        },
        'root': {
            'level': 'WARNING',
            'handlers': ['console']
        }
    }
    
    @classmethod
    def setup_logging(cls, config_path: str = None, log_level: str = None) -> None:
        """ロギングを設定する
        
        Args:
            config_path: カスタム設定ファイルのパス
            log_level: ログレベル（DEBUG, INFO, WARNING, ERROR, CRITICAL）
        """
        # ログディレクトリを作成
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        # 設定を読み込み
        if config_path and Path(config_path).exists():
            config = cls._load_config_from_file(config_path)
        else:
            config = cls.DEFAULT_CONFIG.copy()
        
        # ログレベルを上書き
        if log_level:
            cls._override_log_level(config, log_level.upper())
        
        # ロギング設定を適用
        logging.config.dictConfig(config)
    
    @classmethod
    def _load_config_from_file(cls, config_path: str) -> Dict[str, Any]:
        """設定ファイルから設定を読み込む"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"設定ファイルの読み込みに失敗しました: {e}")
            print("デフォルト設定を使用します")
            return cls.DEFAULT_CONFIG.copy()
    
    @classmethod
    def _override_log_level(cls, config: Dict[str, Any], log_level: str) -> None:
        """ログレベルを上書きする"""
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if log_level not in valid_levels:
            print(f"無効なログレベル: {log_level}. 有効な値: {valid_levels}")
            return
        
        # 全てのロガーのレベルを更新
        for logger_name in config.get('loggers', {}):
            config['loggers'][logger_name]['level'] = log_level
        
        # ルートロガーのレベルも更新
        if 'root' in config:
            config['root']['level'] = log_level
    
    @classmethod
    def create_custom_config(cls, output_path: str) -> None:
        """カスタム設定ファイルを作成する"""
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(cls.DEFAULT_CONFIG, f, indent=2, ensure_ascii=False)
            print(f"設定ファイルを作成しました: {output_path}")
        except Exception as e:
            print(f"設定ファイルの作成に失敗しました: {e}")
    
    @classmethod
    def get_logger(cls, name: str) -> logging.Logger:
        """指定された名前のロガーを取得する"""
        return logging.getLogger(name)


# 便利な関数
def get_fractal_logger(module_name: str = None) -> logging.Logger:
    """フラクタルエディタ用のロガーを取得する
    
    Args:
        module_name: モジュール名（例: 'calculation', 'ui', 'plugins'）
    
    Returns:
        設定されたロガー
    """
    if module_name:
        logger_name = f"fractal_editor.{module_name}"
    else:
        logger_name = "fractal_editor"
    
    return logging.getLogger(logger_name)


def log_performance(func):
    """パフォーマンス測定用デコレータ"""
    import time
    import functools
    
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        logger = get_fractal_logger('performance')
        start_time = time.time()
        
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            logger.info(f"{func.__name__} 実行時間: {execution_time:.4f}秒")
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"{func.__name__} エラー発生 (実行時間: {execution_time:.4f}秒): {e}")
            raise
    
    return wrapper


def log_method_call(func):
    """メソッド呼び出しログ用デコレータ"""
    import functools
    
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        logger = get_fractal_logger('method_calls')
        class_name = args[0].__class__.__name__ if args else "Unknown"
        logger.debug(f"{class_name}.{func.__name__} 呼び出し")
        
        try:
            result = func(*args, **kwargs)
            logger.debug(f"{class_name}.{func.__name__} 正常終了")
            return result
        except Exception as e:
            logger.error(f"{class_name}.{func.__name__} エラー: {e}")
            raise
    
    return wrapper