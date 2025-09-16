"""
日志系统配置文件
根据日志系统设计文档配置各种日志参数
"""

import os
import logging
from typing import Dict, Any, List
from pathlib import Path

# 基础配置
BASE_LOG_DIR = Path("logs")
BASE_LOG_DIR.mkdir(exist_ok=True)

# 环境配置
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
DEBUG_MODE = os.getenv("DEBUG", "false").lower() == "true"

# 日志级别配置
LOG_LEVELS = {
    "development": "DEBUG",
    "testing": "INFO", 
    "staging": "INFO",
    "production": "WARNING"
}

# 当前环境日志级别
CURRENT_LOG_LEVEL = LOG_LEVELS.get(ENVIRONMENT, "INFO")

# 日志格式配置
LOG_FORMATS = {
    "detailed": "%(asctime)s [%(levelname)s] %(name)s %(funcName)s:%(lineno)d - %(message)s",
    "json": "%(asctime)s %(levelname)s %(name)s %(funcName)s:%(lineno)d %(message)s",
    "simple": "%(levelname)s %(name)s - %(message)s"
}

# 模块日志配置
MODULE_LOGGING_CONFIG: Dict[str, Dict[str, Any]] = {
    "MatchingAlgorithms": {
        "level": "DEBUG" if DEBUG_MODE else "INFO",
        "handlers": ["file", "console"],
        "format": "detailed",
        "file_name": "matching.log"
    },
    "DataModels": {
        "level": "INFO",
        "handlers": ["file", "database"],
        "format": "json",
        "file_name": "data.log"
    },
    "ApiEndpoints": {
        "level": "INFO",
        "handlers": ["file", "console"],
        "format": "json",
        "file_name": "api.log"
    },
    "BusinessServices": {
        "level": "INFO",
        "handlers": ["file"],
        "format": "json",
        "file_name": "business.log"
    },
    "AsyncTasks": {
        "level": "INFO",
        "handlers": ["file", "console"],
        "format": "json",
        "file_name": "celery.log"
    },
    "UtilityTools": {
        "level": "WARNING",
        "handlers": ["file"],
        "format": "simple",
        "file_name": "utils.log"
    },
    "LoggingSystem": {
        "level": "INFO",
        "handlers": ["file"],
        "format": "detailed",
        "file_name": "logging.log"
    }
}

# 日志轮转配置
ROTATION_CONFIG = {
    "max_bytes": 100 * 1024 * 1024,  # 100MB
    "backup_count": 10,
    "when": "midnight",
    "interval": 1,
    "retention_days": 30
}

# 文件处理器配置
FILE_HANDLERS = {
    "app": {
        "filename": BASE_LOG_DIR / "app" / "app.log",
        "level": CURRENT_LOG_LEVEL,
        "format": "json",
        "rotation": "daily",
        "retention": 30
    },
    "error": {
        "filename": BASE_LOG_DIR / "error" / "error.log",
        "level": "ERROR",
        "format": "json",
        "rotation": "daily",
        "retention": 30
    },
    "matching": {
        "filename": BASE_LOG_DIR / "matching" / "matching.log",
        "level": "DEBUG",
        "format": "detailed",
        "rotation": "daily",
        "retention": 30
    },
    "api": {
        "filename": BASE_LOG_DIR / "api" / "api.log",
        "level": "INFO",
        "format": "json",
        "rotation": "daily",
        "retention": 30
    }
}

# 控制台处理器配置
CONSOLE_HANDLER = {
    "level": CURRENT_LOG_LEVEL,
    "format": "detailed" if DEBUG_MODE else "simple",
    "colorize": True
}

# 数据库处理器配置
DATABASE_HANDLER = {
    "level": "INFO",
    "table_name": "system_logs",
    "format": "json"
}

# 性能配置
PERFORMANCE_CONFIG = {
    "async_logging": True,
    "buffer_size": 10 * 1024 * 1024,  # 10MB
    "flush_interval": 5,  # seconds
    "max_memory_usage": 50 * 1024 * 1024  # 50MB
}

# 安全配置
SECURITY_CONFIG = {
    "sensitive_fields": [
        "password", "token", "secret", "key", "auth",
        "database_url", "redis_url", "api_key"
    ],
    "mask_pattern": "***",
    "enable_audit": True
}

# 监控配置
MONITORING_CONFIG = {
    "enable_metrics": True,
    "metrics_interval": 60,  # seconds
    "alert_thresholds": {
        "error_rate": 0.05,  # 5%
        "disk_usage": 0.8,   # 80%
        "memory_usage": 0.9  # 90%
    }
}

# 告警配置
ALERT_CONFIG = {
    "high_error_rate": {
        "condition": "error_rate > 5%",
        "duration": "5m",
        "action": "send_email"
    },
    "disk_space": {
        "condition": "disk_usage > 80%",
        "duration": "1m", 
        "action": "cleanup_logs"
    },
    "critical_errors": {
        "condition": "critical_errors > 0",
        "duration": "0m",
        "action": "immediate_notification"
    }
}

# 日志文件路径配置
LOG_PATHS = {
    "app": BASE_LOG_DIR / "app",
    "matching": BASE_LOG_DIR / "matching", 
    "api": BASE_LOG_DIR / "api",
    "error": BASE_LOG_DIR / "error",
    "business": BASE_LOG_DIR / "business",
    "celery": BASE_LOG_DIR / "celery",
    "utils": BASE_LOG_DIR / "utils",
    "logging": BASE_LOG_DIR / "logging"
}

# 创建日志目录
for path in LOG_PATHS.values():
    path.mkdir(parents=True, exist_ok=True)

# 导出配置
__all__ = [
    "CURRENT_LOG_LEVEL",
    "LOG_FORMATS", 
    "MODULE_LOGGING_CONFIG",
    "ROTATION_CONFIG",
    "FILE_HANDLERS",
    "CONSOLE_HANDLER",
    "DATABASE_HANDLER",
    "PERFORMANCE_CONFIG",
    "SECURITY_CONFIG",
    "MONITORING_CONFIG",
    "ALERT_CONFIG",
    "LOG_PATHS",
    "ENVIRONMENT",
    "DEBUG_MODE"
]
