"""
统一日志配置模块
提供与Java端一致的日志格式和配置
"""

import logging
import logging.config
import json
import os
from pathlib import Path

# 默认日志配置
DEFAULT_LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s [%(threadName)s] %(levelname)-5s %(name)s - %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        },
        'json': {
            'format': '{"@timestamp": "%(asctime)s", "level": "%(levelname)s", "logger_name": "%(name)s", "message": "%(message)s", "thread_name": "%(threadName)s"}',
            'datefmt': '%Y-%m-%dT%H:%M:%SZ'
        },
        'detailed': {
            'format': '%(asctime)s [%(threadName)s] %(levelname)-5s %(name)s:%(lineno)d - %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'INFO',
            'formatter': 'standard',
            'stream': 'ext://sys.stdout'
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'level': 'INFO',
            'formatter': 'standard',
            'filename': 'shared_logs/app/app.log',
            'maxBytes': 104857600,  # 100MB
            'backupCount': 10
        },
        'error_file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'level': 'ERROR',
            'formatter': 'standard',
            'filename': 'shared_logs/error/error.log',
            'maxBytes': 104857600,  # 100MB
            'backupCount': 10
        },
        'json_file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'level': 'INFO',
            'formatter': 'json',
            'filename': 'shared_logs/app/app.json',
            'maxBytes': 104857600,  # 100MB
            'backupCount': 10
        },
        'json_error_file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'level': 'ERROR',
            'formatter': 'json',
            'filename': 'shared_logs/error/error.json',
            'maxBytes': 104857600,  # 100MB
            'backupCount': 10
        }
    },
    'loggers': {
        '': {  # root logger
            'handlers': ['console', 'file', 'error_file', 'json_file', 'json_error_file'],
            'level': 'INFO',
            'propagate': False
        }
    }
}


def setup_logging():
    """
    设置统一日志配置
    """
    # 确保日志目录存在
    log_dirs = [
        'shared_logs/app',
        'shared_logs/error',
        'shared_logs/trajectory',
        'shared_logs/business'
    ]
    
    for log_dir in log_dirs:
        Path(log_dir).mkdir(parents=True, exist_ok=True)
    
    # 应用日志配置
    logging.config.dictConfig(DEFAULT_LOGGING_CONFIG)
    
    return logging.getLogger(__name__)


def get_logger(name: str = None):
    """
    获取配置好的日志记录器
    
    Args:
        name: 日志记录器名称
        
    Returns:
        logging.Logger: 配置好的日志记录器
    """
    if name is None:
        name = __name__
    
    return logging.getLogger(name)


# 初始化日志配置
logger = setup_logging()