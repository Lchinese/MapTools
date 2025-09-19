"""
数据模型模块初始化文件
"""

from .base import Base, BaseModel, TimestampMixin, SoftDeleteMixin, AuditMixin
from .enums import TrajectoryStatus, DataSource, DataCategory, LogLevel, TaskStatus, FileStatus

# 导入所有模型
from .Models.trajectory import (
    Trajectory, TrajectoryPoint, MatchingTask, MatchedPoint, 
    User, RoadNetwork, RoadSegment, File, SystemLog
)

__all__ = [
    # 基础类
    "Base", 
    "BaseModel", 
    "TimestampMixin", 
    "SoftDeleteMixin", 
    "AuditMixin",
    
    # 枚举类型
    "TrajectoryStatus",
    "DataSource", 
    "DataCategory",
    "LogLevel",
    "TaskStatus",
    "FileStatus",
    
    # 数据模型
    "Trajectory",
    "TrajectoryPoint", 
    "MatchingTask",
    "MatchedPoint",
    "User",
    "RoadNetwork",
    "RoadSegment",
    "File",
    "SystemLog"
]

__version__ = "0.2.0"