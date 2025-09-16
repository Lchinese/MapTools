"""
日志格式化器配置
提供各种日志格式的格式化器
"""

import json
import logging
import traceback
from datetime import datetime
from typing import Any, Dict, Optional
from LoggingSystem.config import SECURITY_CONFIG


class JSONFormatter(logging.Formatter):
    """JSON格式日志格式化器"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.sensitive_fields = SECURITY_CONFIG["sensitive_fields"]
        self.mask_pattern = SECURITY_CONFIG["mask_pattern"]
    
    def format(self, record: logging.LogRecord) -> str:
        """格式化日志记录为JSON格式"""
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "module": record.name,
            "function": record.funcName,
            "line": record.lineno,
            "message": record.getMessage(),
            "process_id": record.process,
            "thread_id": record.thread,
        }
        
        # 添加请求ID（如果存在）
        if hasattr(record, 'request_id'):
            log_data["request_id"] = record.request_id
            
        # 添加用户ID（如果存在）
        if hasattr(record, 'user_id'):
            log_data["user_id"] = record.user_id
            
        # 添加轨迹ID（如果存在）
        if hasattr(record, 'trajectory_id'):
            log_data["trajectory_id"] = record.trajectory_id
            
        # 添加执行时间（如果存在）
        if hasattr(record, 'duration_ms'):
            log_data["duration_ms"] = record.duration_ms
            
        # 添加错误信息（如果是错误日志）
        if record.levelno >= logging.ERROR:
            log_data["error_type"] = record.exc_info[0].__name__ if record.exc_info else None
            log_data["error_code"] = getattr(record, 'error_code', None)
            if record.exc_info:
                log_data["stack_trace"] = traceback.format_exception(*record.exc_info)
        
        # 添加额外信息
        if hasattr(record, 'extra') and record.extra:
            # 脱敏处理
            extra_data = self._mask_sensitive_data(record.extra)
            log_data["extra"] = extra_data
            
        return json.dumps(log_data, ensure_ascii=False, default=str)


class DetailedFormatter(logging.Formatter):
    """详细格式日志格式化器"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.sensitive_fields = SECURITY_CONFIG["sensitive_fields"]
        self.mask_pattern = SECURITY_CONFIG["mask_pattern"]
    
    def format(self, record: logging.LogRecord) -> str:
        """格式化日志记录为详细格式"""
        # 基础格式
        timestamp = datetime.fromtimestamp(record.created).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        level = record.levelname.ljust(8)
        module = record.name
        function = f"{record.funcName}:{record.lineno}"
        message = record.getMessage()
        
        # 构建基础日志行
        log_line = f"[{timestamp}] [{level}] {module} {function} - {message}"
        
        # 添加额外信息
        if hasattr(record, 'extra') and record.extra:
            extra_data = self._mask_sensitive_data(record.extra)
            extra_str = " | ".join([f"{k}={v}" for k, v in extra_data.items()])
            log_line += f" | {extra_str}"
            
        # 添加请求信息
        if hasattr(record, 'request_id'):
            log_line += f" | req_id={record.request_id}"
            
        # 添加执行时间
        if hasattr(record, 'duration_ms'):
            log_line += f" | duration={record.duration_ms}ms"
            
        # 添加错误信息
        if record.exc_info:
            log_line += f"\n{traceback.format_exc()}"
            
        return log_line


class SimpleFormatter(logging.Formatter):
    """简单格式日志格式化器"""
    
    def format(self, record: logging.LogRecord) -> str:
        """格式化日志记录为简单格式"""
        level = record.levelname
        module = record.name
        message = record.getMessage()
        return f"{level} {module} - {message}"


class AuditFormatter(logging.Formatter):
    """审计日志格式化器"""
    
    def format(self, record: logging.LogRecord) -> str:
        """格式化审计日志记录"""
        timestamp = datetime.utcnow().isoformat() + "Z"
        user_id = getattr(record, 'user_id', 'system')
        action = getattr(record, 'action', 'unknown')
        resource = getattr(record, 'resource', 'unknown')
        result = getattr(record, 'result', 'unknown')
        ip_address = getattr(record, 'ip_address', 'unknown')
        
        audit_data = {
            "timestamp": timestamp,
            "type": "audit",
            "user_id": user_id,
            "action": action,
            "resource": resource,
            "result": result,
            "ip_address": ip_address,
            "message": record.getMessage()
        }
        
        return json.dumps(audit_data, ensure_ascii=False)


class PerformanceFormatter(logging.Formatter):
    """性能日志格式化器"""
    
    def format(self, record: logging.LogRecord) -> str:
        """格式化性能日志记录"""
        timestamp = datetime.utcnow().isoformat() + "Z"
        
        perf_data = {
            "timestamp": timestamp,
            "type": "performance",
            "module": record.name,
            "function": record.funcName,
            "duration_ms": getattr(record, 'duration_ms', 0),
            "memory_mb": getattr(record, 'memory_mb', 0),
            "cpu_percent": getattr(record, 'cpu_percent', 0),
            "message": record.getMessage()
        }
        
        return json.dumps(perf_data, ensure_ascii=False)


def _mask_sensitive_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
    """脱敏处理敏感数据"""
    if not isinstance(data, dict):
        return data
        
    masked_data = {}
    for key, value in data.items():
        if any(sensitive in key.lower() for sensitive in self.sensitive_fields):
            masked_data[key] = self.mask_pattern
        elif isinstance(value, dict):
            masked_data[key] = self._mask_sensitive_data(value)
        else:
            masked_data[key] = value
            
    return masked_data


# 为所有格式化器添加脱敏方法
JSONFormatter._mask_sensitive_data = _mask_sensitive_data
DetailedFormatter._mask_sensitive_data = _mask_sensitive_data


# 导出格式化器
__all__ = [
    "JSONFormatter",
    "DetailedFormatter", 
    "SimpleFormatter",
    "AuditFormatter",
    "PerformanceFormatter"
]
