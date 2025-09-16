"""
日志系统配置
提供统一的日志接口和配置管理
"""

import logging
import logging.config
import logging.handlers
import sys
import os
import json
from typing import Optional, Dict, Any
from pathlib import Path
from datetime import datetime


# 日志配置常量
LOG_LEVELS = {
    'DEBUG': logging.DEBUG,
    'INFO': logging.INFO,
    'WARNING': logging.WARNING,
    'ERROR': logging.ERROR,
    'CRITICAL': logging.CRITICAL
}

# 环境配置
ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')
DEBUG_MODE = os.getenv('DEBUG', 'false').lower() == 'true'
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO' if ENVIRONMENT == 'production' else 'DEBUG')

# 日志路径配置
LOG_BASE_DIR = Path('Logs')
LOG_PATHS = {
    'app': LOG_BASE_DIR / 'app',
    'error': LOG_BASE_DIR / 'error',
    'audit': LOG_BASE_DIR / 'audit',
    'performance': LOG_BASE_DIR / 'performance',
    'debug': LOG_BASE_DIR / 'debug'
}

# 轮转配置
ROTATION_CONFIG = {
    'max_bytes': 10 * 1024 * 1024,  # 10MB
    'backup_count': 5,
    'when': 'midnight',
    'interval': 1
}

# 性能配置
PERFORMANCE_CONFIG = {
    'buffer_size': 8192,
    'flush_interval': 5  # 秒
}

# 模块日志配置
MODULE_LOGGING_CONFIG = {
    'maptools': {
        'level': 'DEBUG',
        'handlers': ['file', 'console'],
        'file_name': 'app.log',
        'format': 'json'
    },
    'matching': {
        'level': 'INFO',
        'handlers': ['file', 'console'],
        'file_name': 'matching.log',
        'format': 'detailed'
    },
    'api': {
        'level': 'INFO',
        'handlers': ['file', 'console'],
        'file_name': 'api.log',
        'format': 'json'
    },
    'database': {
        'level': 'WARNING',
        'handlers': ['file'],
        'file_name': 'database.log',
        'format': 'json'
    },
    'audit': {
        'level': 'INFO',
        'handlers': ['file'],
        'file_name': 'audit.log',
        'format': 'audit'
    },
    'performance': {
        'level': 'INFO',
        'handlers': ['file'],
        'file_name': 'performance.log',
        'format': 'performance'
    }
}


class JSONFormatter(logging.Formatter):
    """JSON格式化器"""
    
    def format(self, record):
        log_entry = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'module': record.name,
            'function': record.funcName,
            'line': record.lineno,
            'message': record.getMessage(),
            'thread': record.thread,
            'process': record.process
        }
        
        # 添加额外信息
        if hasattr(record, 'extra') and record.extra:
            log_entry.update(record.extra)
        
        # 添加异常信息
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
        
        return json.dumps(log_entry, ensure_ascii=False)


class DetailedFormatter(logging.Formatter):
    """详细格式化器"""
    
    def __init__(self):
        super().__init__(
            fmt='%(asctime)s | %(levelname)-8s | %(name)-20s | %(funcName)-15s | %(lineno)-4d | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )


class SimpleFormatter(logging.Formatter):
    """简单格式化器"""
    
    def __init__(self):
        super().__init__(
            fmt='%(asctime)s | %(levelname)s | %(message)s',
            datefmt='%H:%M:%S'
        )


class AuditFormatter(logging.Formatter):
    """审计格式化器"""
    
    def format(self, record):
        return f"[AUDIT] {datetime.fromtimestamp(record.created).isoformat()} | {record.getMessage()}"


class PerformanceFormatter(logging.Formatter):
    """性能格式化器"""
    
    def format(self, record):
        duration = getattr(record, 'duration_ms', 0)
        return f"[PERF] {datetime.fromtimestamp(record.created).isoformat()} | {record.funcName} | {duration}ms | {record.getMessage()}"


class AsyncFileHandler(logging.handlers.RotatingFileHandler):
    """异步文件处理器"""
    
    def __init__(self, filename: str, **kwargs):
        # 确保目录存在
        Path(filename).parent.mkdir(parents=True, exist_ok=True)
        
        super().__init__(
            filename=filename,
            maxBytes=ROTATION_CONFIG["max_bytes"],
            backupCount=ROTATION_CONFIG["backup_count"],
            encoding='utf-8'
        )
        
        # 设置缓冲区
        self.buffer_size = PERFORMANCE_CONFIG["buffer_size"]
        self._buffer = []
        self._last_flush = 0
    
    def emit(self, record: logging.LogRecord):
        """异步发送日志记录"""
        try:
            # 添加到缓冲区
            self._buffer.append(self.format(record))
            
            # 检查是否需要刷新
            if (len(self._buffer) >= 100 or
                len(''.join(self._buffer)) >= self.buffer_size):
                self._flush_buffer()
        
        except Exception:
            self.handleError(record)
    
    def _flush_buffer(self):
        """刷新缓冲区"""
        if self._buffer:
            try:
                for log_entry in self._buffer:
                    self.stream.write(log_entry + '\n')
                self.stream.flush()
                self._buffer.clear()
            except Exception:
                pass


class ConsoleHandler(logging.StreamHandler):
    """控制台处理器"""
    
    def __init__(self, stream=None):
        super().__init__(stream or sys.stdout)
    
    def emit(self, record: logging.LogRecord):
        """发送日志记录到控制台"""
        try:
            # 根据日志级别设置颜色
            if record.levelno >= logging.ERROR:
                color_code = '\033[91m'  # 红色
            elif record.levelno >= logging.WARNING:
                color_code = '\033[93m'  # 黄色
            elif record.levelno >= logging.INFO:
                color_code = '\033[92m'  # 绿色
            else:
                color_code = '\033[0m'   # 默认颜色
            
            reset_code = '\033[0m'
            
            # 格式化并输出
            formatted = self.format(record)
            self.stream.write(f"{color_code}{formatted}{reset_code}\n")
            self.stream.flush()
        
        except Exception:
            self.handleError(record)


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
        root_logger.setLevel(LOG_LEVELS.get(LOG_LEVEL, logging.INFO))
        
        # 清除现有处理器
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        
        # 添加控制台处理器
        if DEBUG_MODE or ENVIRONMENT == "development":
            console_handler = cls._create_console_handler(LOG_LEVEL)
            root_logger.addHandler(console_handler)
        
        # 添加文件处理器
        file_handler = cls._create_file_handler("app", LOG_LEVEL, "json")
        root_logger.addHandler(file_handler)
        
        # 添加错误处理器
        error_handler = cls._create_file_handler("error", "ERROR", "json")
        root_logger.addHandler(error_handler)
    
    @classmethod
    def _setup_module_loggers(cls, db_connection=None):
        """设置模块日志器"""
        for module_name, config in MODULE_LOGGING_CONFIG.items():
            logger = logging.getLogger(module_name)
            logger.setLevel(LOG_LEVELS.get(config["level"], logging.INFO))
            
            # 清除现有处理器
            for handler in logger.handlers[:]:
                logger.removeHandler(handler)
            
            # 添加处理器
            for handler_type in config["handlers"]:
                if handler_type == "file":
                    handler = cls._create_file_handler(
                        config["file_name"].replace(".log", ""),
                        config["level"],
                        config["format"]
                    )
                    logger.addHandler(handler)
                
                elif handler_type == "console":
                    handler = cls._create_console_handler(config["level"])
                    logger.addHandler(handler)
            
            # 不传播到根日志器
            logger.propagate = False
            cls._loggers[module_name] = logger
    
    @classmethod
    def _create_file_handler(cls, log_type: str, level: str, format_type: str) -> logging.Handler:
        """创建文件处理器"""
        log_path = LOG_PATHS.get(log_type, LOG_PATHS["app"])
        filename = log_path / f"{log_type}.log"
        
        handler = AsyncFileHandler(str(filename))
        handler.setLevel(LOG_LEVELS.get(level.upper(), logging.INFO))
        
        # 设置格式化器
        if format_type == "json":
            formatter = JSONFormatter()
        elif format_type == "detailed":
            formatter = DetailedFormatter()
        elif format_type == "audit":
            formatter = AuditFormatter()
        elif format_type == "performance":
            formatter = PerformanceFormatter()
        else:
            formatter = SimpleFormatter()
        
        handler.setFormatter(formatter)
        return handler
    
    @classmethod
    def _create_console_handler(cls, level: str) -> logging.Handler:
        """创建控制台处理器"""
        handler = ConsoleHandler()
        handler.setLevel(LOG_LEVELS.get(level.upper(), logging.INFO))
        formatter = DetailedFormatter()
        handler.setFormatter(formatter)
        return handler
    
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
        logger.setLevel(LOG_LEVELS.get(LOG_LEVEL, logging.INFO))
        
        # 添加默认处理器
        if DEBUG_MODE or ENVIRONMENT == "development":
            console_handler = cls._create_console_handler(LOG_LEVEL)
            logger.addHandler(console_handler)
        
        file_handler = cls._create_file_handler("app", LOG_LEVEL, "json")
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
            os.environ["LOG_LEVEL"] = level
        if environment:
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
    "log_audit",
    "JSONFormatter",
    "DetailedFormatter",
    "SimpleFormatter",
    "AuditFormatter",
    "PerformanceFormatter",
    "AsyncFileHandler",
    "ConsoleHandler"
]
