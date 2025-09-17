"""
核心配置层
提供系统配置、数据库连接、日志等核心功能
"""

from .settings import get_settings
from .database import get_db, create_tables, check_connection
from .logging import setup_logging, get_logger

__all__ = [
    "get_settings",
    "get_db",
    "create_tables",
    "check_connection",
    "setup_logging",
    "get_logger"
]

__version__ = "0.1.0"