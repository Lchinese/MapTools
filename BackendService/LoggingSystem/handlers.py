"""
日志处理器配置
提供各种日志输出处理器
"""

import os
import sys
import logging
import logging.handlers
from pathlib import Path
from typing import Optional, Dict, Any
from LoggingSystem.config import (
    ROTATION_CONFIG, 
    PERFORMANCE_CONFIG,
    LOG_PATHS,
    DATABASE_HANDLER
)
from LoggingSystem.formatters import (
    JSONFormatter,
    DetailedFormatter,
    SimpleFormatter,
    AuditFormatter,
    PerformanceFormatter
)


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


class TimedRotatingFileHandler(logging.handlers.TimedRotatingFileHandler):
    """时间轮转文件处理器"""
    
    def __init__(self, filename: str, **kwargs):
        # 确保目录存在
        Path(filename).parent.mkdir(parents=True, exist_ok=True)
        
        super().__init__(
            filename=filename,
            when=ROTATION_CONFIG["when"],
            interval=ROTATION_CONFIG["interval"],
            backupCount=ROTATION_CONFIG["backup_count"],
            encoding='utf-8'
        )


class DatabaseHandler(logging.Handler):
    """数据库日志处理器"""
    
    def __init__(self, db_connection=None, table_name: str = "system_logs"):
        super().__init__()
        self.db_connection = db_connection
        self.table_name = table_name
        self._buffer = []
        
    def emit(self, record: logging.LogRecord):
        """发送日志记录到数据库"""
        try:
            log_data = {
                'timestamp': record.created,
                'level': record.levelname,
                'module': record.name,
                'function': record.funcName,
                'line': record.lineno,
                'message': record.getMessage(),
                'extra': getattr(record, 'extra', {})
            }
            
            # 添加到缓冲区
            self._buffer.append(log_data)
            
            # 批量插入
            if len(self._buffer) >= 10:
                self._flush_buffer()
                
        except Exception:
            self.handleError(record)
    
    def _flush_buffer(self):
        """刷新缓冲区到数据库"""
        if not self._buffer or not self.db_connection:
            return
            
        try:
            # 这里需要根据实际的数据库连接实现
            # 示例使用SQLAlchemy
            pass
        except Exception:
            pass
        finally:
            self._buffer.clear()


class ConsoleHandler(logging.StreamHandler):
    """控制台处理器"""
    
    def __init__(self, stream=None):
        super().__init__(stream or sys.stdout)
        
    def emit(self, record: logging.LogRecord):
        """发送日志记录到控制台"""
        try:
            # 根据日志级别设置颜色
            if record.levelno >= logging.ERROR:
                # 红色
                color_code = '\033[91m'
            elif record.levelno >= logging.WARNING:
                # 黄色
                color_code = '\033[93m'
            elif record.levelno >= logging.INFO:
                # 绿色
                color_code = '\033[92m'
            else:
                # 默认颜色
                color_code = '\033[0m'
            
            # 重置颜色
            reset_code = '\033[0m'
            
            # 格式化并输出
            formatted = self.format(record)
            self.stream.write(f"{color_code}{formatted}{reset_code}\n")
            self.stream.flush()
            
        except Exception:
            self.handleError(record)


class RemoteHandler(logging.Handler):
    """远程日志处理器"""
    
    def __init__(self, remote_url: str, timeout: int = 5):
        super().__init__()
        self.remote_url = remote_url
        self.timeout = timeout
        self._buffer = []
        
    def emit(self, record: logging.LogRecord):
        """发送日志记录到远程服务"""
        try:
            log_data = {
                'timestamp': record.created,
                'level': record.levelname,
                'module': record.name,
                'message': record.getMessage(),
                'extra': getattr(record, 'extra', {})
            }
            
            # 添加到缓冲区
            self._buffer.append(log_data)
            
            # 批量发送
            if len(self._buffer) >= 50:
                self._flush_buffer()
                
        except Exception:
            self.handleError(record)
    
    def _flush_buffer(self):
        """刷新缓冲区到远程服务"""
        if not self._buffer:
            return
            
        try:
            # 这里需要实现HTTP请求发送
            # 示例使用requests
            pass
        except Exception:
            pass
        finally:
            self._buffer.clear()


def create_file_handler(
    log_type: str, 
    level: str = "INFO",
    format_type: str = "json"
) -> logging.Handler:
    """创建文件处理器"""
    log_path = LOG_PATHS.get(log_type, LOG_PATHS["app"])
    filename = log_path / f"{log_type}.log"
    
    handler = AsyncFileHandler(str(filename))
    handler.setLevel(getattr(logging, level.upper()))
    
    # 设置格式化器
    if format_type == "json":
        formatter = JSONFormatter()
    elif format_type == "detailed":
        formatter = DetailedFormatter()
    else:
        formatter = SimpleFormatter()
    
    handler.setFormatter(formatter)
    return handler


def create_console_handler(level: str = "INFO") -> logging.Handler:
    """创建控制台处理器"""
    handler = ConsoleHandler()
    handler.setLevel(getattr(logging, level.upper()))
    formatter = DetailedFormatter()
    handler.setFormatter(formatter)
    return handler


def create_database_handler(db_connection=None) -> logging.Handler:
    """创建数据库处理器"""
    handler = DatabaseHandler(db_connection)
    handler.setLevel(getattr(logging, DATABASE_HANDLER["level"]))
    formatter = JSONFormatter()
    handler.setFormatter(formatter)
    return handler


def create_audit_handler() -> logging.Handler:
    """创建审计日志处理器"""
    filename = LOG_PATHS["app"] / "audit.log"
    handler = AsyncFileHandler(str(filename))
    handler.setLevel(logging.INFO)
    formatter = AuditFormatter()
    handler.setFormatter(formatter)
    return handler


def create_performance_handler() -> logging.Handler:
    """创建性能日志处理器"""
    filename = LOG_PATHS["app"] / "performance.log"
    handler = AsyncFileHandler(str(filename))
    handler.setLevel(logging.INFO)
    formatter = PerformanceFormatter()
    handler.setFormatter(formatter)
    return handler


# 导出处理器
__all__ = [
    "AsyncFileHandler",
    "TimedRotatingFileHandler", 
    "DatabaseHandler",
    "ConsoleHandler",
    "RemoteHandler",
    "create_file_handler",
    "create_console_handler",
    "create_database_handler",
    "create_audit_handler",
    "create_performance_handler"
]
