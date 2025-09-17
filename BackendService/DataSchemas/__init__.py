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
    DataSource,
    DataCategory,
    TrajectoryStatus,
    FileResponse,
    FileCreate,
    RoadNetworkCreate,
    RoadNetworkResponse,
    RoadSegmentCreate,
    RoadSegmentResponse
)

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
    "DataSource",
    "DataCategory",
    "TrajectoryStatus",
    "FileResponse",
    "FileCreate",
    "RoadNetworkCreate",
    "RoadNetworkResponse",
    "RoadSegmentCreate",
    "RoadSegmentResponse",
    
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