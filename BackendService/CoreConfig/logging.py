"""
日志配置模块
提供统一的日志配置和管理
"""

import os
import logging
import logging.config
from logging.handlers import RotatingFileHandler
from typing import Dict, Any
from pathlib import Path

from .settings import get_settings

# 获取配置
settings = get_settings()


def setup_logging():
    """设置日志配置"""
    # 创建日志目录
    log_dir = Path(settings.LOG_DIR)
    log_dir.mkdir(exist_ok=True)
    
    # 创建子目录
    (log_dir / "app").mkdir(exist_ok=True)
    (log_dir / "error").mkdir(exist_ok=True)
    (log_dir / "audit").mkdir(exist_ok=True)
    (log_dir / "performance").mkdir(exist_ok=True)
    (log_dir / "matching").mkdir(exist_ok=True)
    (log_dir / "api").mkdir(exist_ok=True)
    (log_dir / "business").mkdir(exist_ok=True)
    (log_dir / "celery").mkdir(exist_ok=True)
    (log_dir / "utils").mkdir(exist_ok=True)
    (log_dir / "trajectory").mkdir(exist_ok=True)  # 添加轨迹处理日志目录
    
    # 日志配置字典
    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "detailed": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S"
            },
            "json": {
                "format": '{"timestamp": "%(asctime)s", "logger": "%(name)s", "level": "%(levelname)s", "file": "%(filename)s", "line": %(lineno)d, "message": "%(message)s"}',
                "datefmt": "%Y-%m-%d %H:%M:%S"
            },
            "simple": {
                "format": "%(levelname)s - %(message)s"
            },
            "audit": {
                "format": "%(asctime)s - AUDIT - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S"
            },
            "performance": {
                "format": "%(asctime)s - PERFORMANCE - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S"
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": settings.LOG_LEVEL,
                "formatter": "detailed",
                "stream": "ext://sys.stdout"
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": settings.LOG_LEVEL,
                "formatter": "json",
                "filename": str(log_dir / "app" / "app.log"),
                "maxBytes": settings.LOG_MAX_SIZE,
                "backupCount": settings.LOG_BACKUP_COUNT,
                "encoding": "utf-8"
            },
            "error": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "ERROR",
                "formatter": "json",
                "filename": str(log_dir / "error" / "error.log"),
                "maxBytes": settings.LOG_MAX_SIZE,
                "backupCount": settings.LOG_BACKUP_COUNT,
                "encoding": "utf-8"
            },
            "matching": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "DEBUG",
                "formatter": "detailed",
                "filename": str(log_dir / "matching" / "matching.log"),
                "maxBytes": settings.LOG_MAX_SIZE,
                "backupCount": settings.LOG_BACKUP_COUNT,
                "encoding": "utf-8"
            },
            "api": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "INFO",
                "formatter": "detailed",
                "filename": str(log_dir / "api" / "api.log"),
                "maxBytes": settings.LOG_MAX_SIZE,
                "backupCount": settings.LOG_BACKUP_COUNT,
                "encoding": "utf-8"
            },
            "business": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "INFO",
                "formatter": "detailed",
                "filename": str(log_dir / "business" / "business.log"),
                "maxBytes": settings.LOG_MAX_SIZE,
                "backupCount": settings.LOG_BACKUP_COUNT,
                "encoding": "utf-8"
            },
            "celery": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "INFO",
                "formatter": "detailed",
                "filename": str(log_dir / "celery" / "celery.log"),
                "maxBytes": settings.LOG_MAX_SIZE,
                "backupCount": settings.LOG_BACKUP_COUNT,
                "encoding": "utf-8"
            },
            "utils": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "WARNING",
                "formatter": "detailed",
                "filename": str(log_dir / "utils" / "utils.log"),
                "maxBytes": settings.LOG_MAX_SIZE,
                "backupCount": settings.LOG_BACKUP_COUNT,
                "encoding": "utf-8"
            },
            "audit": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "INFO",
                "formatter": "audit",
                "filename": str(log_dir / "audit" / "audit.log"),
                "maxBytes": settings.LOG_MAX_SIZE,
                "backupCount": settings.LOG_BACKUP_COUNT,
                "encoding": "utf-8"
            },
            "performance": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "INFO",
                "formatter": "performance",
                "filename": str(log_dir / "performance" / "performance.log"),
                "maxBytes": settings.LOG_MAX_SIZE,
                "backupCount": settings.LOG_BACKUP_COUNT,
                "encoding": "utf-8"
            },
            "trajectory": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "INFO",
                "formatter": "detailed",
                "filename": str(log_dir / "trajectory" / "trajectory.log"),
                "maxBytes": settings.LOG_MAX_SIZE,
                "backupCount": settings.LOG_BACKUP_COUNT,
                "encoding": "utf-8"
            }
        },
        "loggers": {
            "": {  # root logger
                "level": settings.LOG_LEVEL,
                "handlers": ["console", "file", "error"],
                "propagate": False
            },
            "MatchingAlgorithms": {
                "level": "DEBUG",
                "handlers": ["matching"],
                "propagate": False
            },
            "DataModels": {
                "level": "INFO",
                "handlers": ["file"],
                "propagate": False
            },
            "ApiEndpoints": {
                "level": "INFO",
                "handlers": ["api", "console"],
                "propagate": False
            },
            "BusinessServices": {
                "level": "INFO",
                "handlers": ["business"],
                "propagate": False
            },
            "AsyncTasks": {
                "level": "INFO",
                "handlers": ["celery", "console"],
                "propagate": False
            },
            "UtilityTools": {
                "level": "WARNING",
                "handlers": ["utils"],
                "propagate": False
            },
            "audit": {
                "level": "INFO",
                "handlers": ["audit"],
                "propagate": False
            },
            "performance": {
                "level": "INFO",
                "handlers": ["performance"],
                "propagate": False
            },
            "trajectory": {
                "level": "INFO",
                "handlers": ["trajectory"],
                "propagate": False
            }
        }
    }
    
    # 应用配置
    logging.config.dictConfig(logging_config)
    
    # 设置第三方库日志级别
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.pool").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("celery").setLevel(logging.INFO)


def get_logger(name: str) -> logging.Logger:
    """
    获取指定名称的日志器
    
    Args:
        name: 日志器名称
        
    Returns:
        logging.Logger: 日志器实例
    """
    return logging.getLogger(name)


def get_audit_logger() -> logging.Logger:
    """获取审计日志器"""
    return logging.getLogger("audit")


def get_performance_logger() -> logging.Logger:
    """获取性能日志器"""
    return logging.getLogger("performance")


# 性能监控装饰器
def log_performance(func):
    """性能监控装饰器"""
    def wrapper(*args, **kwargs):
        import time
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            get_performance_logger().info(f"{func.__name__} executed in {execution_time:.4f}s")
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            get_performance_logger().error(f"{func.__name__} failed after {execution_time:.4f}s: {e}")
            raise
    return wrapper


# 审计日志装饰器
def log_audit(action: str):
    """审计日志装饰器"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            get_audit_logger().info(f"Action: {action}, Function: {func.__name__}")
            try:
                result = func(*args, **kwargs)
                get_audit_logger().info(f"Action: {action} completed successfully")
                return result
            except Exception as e:
                get_audit_logger().error(f"Action: {action} failed: {e}")
                raise
        return wrapper
    return decorator