"""
API 路由层
提供 RESTful API 接口（当前版本仅保留健康检查与认证相关路由）
"""

from .health import router as health_router
from .auth import router as auth_router
from .matching import router as matching_router

__all__ = [
    "health_router",
    "auth_router",
    "matching_router"
]

__version__ = "0.2.0"