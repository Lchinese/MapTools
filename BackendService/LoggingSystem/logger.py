"""
核心日志器
提供统一的日志接口和配置管理
"""

import logging
import logging.config
import sys
from typing import Optional, Dict, Any
from pathlib import Path

from LoggingSystem.config import (
    CURRENT_LOG_LEVEL,
    MODULE_LOGGING_CONFIG,
    ENVIRONMENT,
    DEBUG_MODE
)
from LoggingSystem.handlers import (
    create_file_handler,
    create_console_handler,
    create_database_handler,
    create_audit_handler,
    create_performance_handler
)


class MapToolsLogger:
    """MapTools 项目日志器"""
    
    _loggers: Dict[str, logging.Logger] = {}
    _initialized = False
    
    @classmethod
    def initialize(cls, db_connection=None):
        """初始化日志系统"""
        if cls._initialized:
            return
            
        # 配置根日志器
        cls._setup_root_logger()
        
        # 配置模块日志器
        cls._setup_module_loggers(db_connection)
        
        cls._initialized = True
    
    @classmethod
    def _setup_root_logger(cls):
        """设置根日志器"""
        root_logger = logging.getLogger()
        root_logger.setLevel(CURRENT_LOG_LEVEL)
        
        # 清除现有处理器
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        
        # 添加控制台处理器
        if DEBUG_MODE or ENVIRONMENT == "development":
            console_handler = create_console_handler(CURRENT_LOG_LEVEL)
            root_logger.addHandler(console_handler)
        
        # 添加文件处理器
        file_handler = create_file_handler("app", CURRENT_LOG_LEVEL, "json")
        root_logger.addHandler(file_handler)
        
        # 添加错误处理器
        error_handler = create_file_handler("error", "ERROR", "json")
        root_logger.addHandler(error_handler)
    
    @classmethod
    def _setup_module_loggers(cls, db_connection=None):
        """设置模块日志器"""
        for module_name, config in MODULE_LOGGING_CONFIG.items():
            logger = logging.getLogger(module_name)
            logger.setLevel(getattr(logging, config["level"]))
            
            # 清除现有处理器
            for handler in logger.handlers[:]:
                logger.removeHandler(handler)
            
            # 添加处理器
            for handler_type in config["handlers"]:
                if handler_type == "file":
                    handler = create_file_handler(
                        config["file_name"].replace(".log", ""),
                        config["level"],
                        config["format"]
                    )
                    logger.addHandler(handler)
                    
                elif handler_type == "console":
                    handler = create_console_handler(config["level"])
                    logger.addHandler(handler)
                    
                elif handler_type == "database" and db_connection:
                    handler = create_database_handler(db_connection)
                    logger.addHandler(handler)
            
            # 不传播到根日志器
            logger.propagate = False
            
            cls._loggers[module_name] = logger
    
    @classmethod
    def get_logger(cls, name: str) -> logging.Logger:
        """获取日志器"""
        if not cls._initialized:
            cls.initialize()
        
        # 如果请求的是模块日志器
        if name in cls._loggers:
            return cls._loggers[name]
        
        # 创建新的日志器
        logger = logging.getLogger(name)
        logger.setLevel(CURRENT_LOG_LEVEL)
        
        # 添加默认处理器
        if DEBUG_MODE or ENVIRONMENT == "development":
            console_handler = create_console_handler(CURRENT_LOG_LEVEL)
            logger.addHandler(console_handler)
        
        file_handler = create_file_handler("app", CURRENT_LOG_LEVEL, "json")
        logger.addHandler(file_handler)
        
        return logger


def get_logger(name: str) -> logging.Logger:
    """获取日志器的便捷函数"""
    return MapToolsLogger.get_logger(name)


def setup_logging(
    level: str = None,
    environment: str = None,
    db_connection=None,
    config_file: str = None
):
    """设置日志系统"""
    if config_file and Path(config_file).exists():
        # 从配置文件加载
        logging.config.fileConfig(config_file)
    else:
        # 使用代码配置
        if level:
            import os
            os.environ["LOG_LEVEL"] = level
        if environment:
            import os
            os.environ["ENVIRONMENT"] = environment
            
        MapToolsLogger.initialize(db_connection)


class LoggerMixin:
    """日志器混入类"""
    
    @property
    def logger(self) -> logging.Logger:
        """获取当前类的日志器"""
        if not hasattr(self, '_logger'):
            self._logger = get_logger(self.__class__.__module__)
        return self._logger


def log_function_call(func):
    """函数调用日志装饰器"""
    def wrapper(*args, **kwargs):
        logger = get_logger(func.__module__)
        logger.debug(f"调用函数: {func.__name__}", extra={
            "function": func.__name__,
            "args_count": len(args),
            "kwargs_keys": list(kwargs.keys())
        })
        
        try:
            result = func(*args, **kwargs)
            logger.debug(f"函数 {func.__name__} 执行成功")
            return result
        except Exception as e:
            logger.error(f"函数 {func.__name__} 执行失败: {str(e)}", exc_info=True)
            raise
    
    return wrapper


def log_performance(func):
    """性能日志装饰器"""
    import time
    
    def wrapper(*args, **kwargs):
        logger = get_logger(func.__module__)
        start_time = time.time()
        
        try:
            result = func(*args, **kwargs)
            duration = (time.time() - start_time) * 1000  # 转换为毫秒
            
            logger.info(f"函数 {func.__name__} 执行完成", extra={
                "function": func.__name__,
                "duration_ms": duration,
                "performance": True
            })
            
            return result
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            logger.error(f"函数 {func.__name__} 执行失败", extra={
                "function": func.__name__,
                "duration_ms": duration,
                "error": str(e),
                "performance": True
            })
            raise
    
    return wrapper


def log_audit(action: str, resource: str = None, user_id: str = None):
    """审计日志装饰器"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            logger = get_logger("audit")
            
            # 记录操作开始
            logger.info(f"审计: {action}", extra={
                "action": action,
                "resource": resource or func.__name__,
                "user_id": user_id,
                "audit": True
            })
            
            try:
                result = func(*args, **kwargs)
                
                # 记录操作成功
                logger.info(f"审计: {action} 成功", extra={
                    "action": action,
                    "resource": resource or func.__name__,
                    "user_id": user_id,
                    "result": "success",
                    "audit": True
                })
                
                return result
            except Exception as e:
                # 记录操作失败
                logger.error(f"审计: {action} 失败", extra={
                    "action": action,
                    "resource": resource or func.__name__,
                    "user_id": user_id,
                    "result": "failed",
                    "error": str(e),
                    "audit": True
                })
                raise
        
        return wrapper
    return decorator


# 导出函数和类
__all__ = [
    "MapToolsLogger",
    "get_logger",
    "setup_logging",
    "LoggerMixin",
    "log_function_call",
    "log_performance", 
    "log_audit"
]
