"""
数据模型模块初始化文件
"""

# 仅保留用户模型
from .user import User

__all__ = [
    "User"
]

__version__ = "0.2.0"