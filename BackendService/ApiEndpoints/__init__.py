"""
API 路由层
提供 RESTful API 接口（当前版本仅保留健康检查与认证相关路由）
"""

from .health import router as health_router

__all__ = [
    "health_router"
]

__version__ = "0.2.0"