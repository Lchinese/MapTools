"""
数据验证层
提供 Pydantic 数据模型和验证功能
"""

from .trajectory import (
    TrajectoryCreate,
    TrajectoryUpdate,
    TrajectoryResponse,
    TrajectoryListResponse,
    TrajectoryUploadResponse,
    TrajectoryDeleteResponse,
    TrajectoryQueryParams,
    FileResponse,
    FileCreate,
    RoadNetworkCreate,
    RoadNetworkResponse,
    RoadSegmentCreate,
    RoadSegmentResponse,
    UserCreate,
    UserLogin,
    UserResponse
)

# 从 DataModels 导入枚举
from DataModels.enums import DataSource, DataCategory, TrajectoryStatus

from .matching import (
    MatchingRequest,
    MatchingStartResponse,
    MatchingStatusResponse,
    MatchingResultResponse,
    MatchingTaskQueryParams,
    MatchingTaskListResponse,
    MatchingAlgorithm
)

__all__ = [
    # Trajectory schemas
    "TrajectoryCreate",
    "TrajectoryUpdate",
    "TrajectoryResponse",
    "TrajectoryListResponse",
    "TrajectoryUploadResponse",
    "TrajectoryDeleteResponse",
    "TrajectoryQueryParams",
    "FileResponse",
    "FileCreate",
    "RoadNetworkCreate",
    "RoadNetworkResponse",
    "RoadSegmentCreate",
    "RoadSegmentResponse",
    "UserCreate",
    "UserLogin",
    "UserResponse",
    
    # Enums (from DataModels)
    "DataSource",
    "DataCategory",
    "TrajectoryStatus",
    
    # Matching schemas
    "MatchingRequest",
    "MatchingStartResponse",
    "MatchingStatusResponse",
    "MatchingResultResponse",
    "MatchingTaskQueryParams",
    "MatchingTaskListResponse",
    "MatchingAlgorithm"
]

__version__ = "0.1.0"