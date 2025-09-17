"""
API 路由层
提供 RESTful API 接口
"""

from .trajectory import router as trajectory_router
from .matching import router as matching_router
from .health import router as health_router

__all__ = [
    "trajectory_router",
    "matching_router", 
    "health_router"
]

__version__ = "0.1.0"