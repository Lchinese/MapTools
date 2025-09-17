"""
数据模型定义目录
包含所有数据库表对应的模型类
"""

from .trajectory import (
    Trajectory, 
    TrajectoryPoint, 
    MatchingTask, 
    MatchedPoint, 
    RoadNetwork, 
    RoadSegment,
    File,
    LogLevel,
    TrajectoryStatus,
    DataSource,
    DataCategory
)

__all__ = [
    "Trajectory",
    "TrajectoryPoint",
    "MatchingTask",
    "MatchedPoint",
    "RoadNetwork",
    "RoadSegment",
    "File",
    "LogLevel",
    "TrajectoryStatus",
    "DataSource",
    "DataCategory"
]

__version__ = "0.1.0"