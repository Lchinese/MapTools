"""
异步任务层
提供 Celery 异步任务处理功能
"""

# 导入 Celery 应用
from .celery_app import celery_app

# 导入任务
from . import tasks

__all__ = [
    "celery_app",
    "tasks"
]

__version__ = "0.1.0"