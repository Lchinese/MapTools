"""
数据验证层
提供 Pydantic 数据模型和验证功能
"""

# 用户相关
from .user import UserCreate, UserLogin, UserResponse

# 轨迹相关
from .trajectory import (
    TrajectoryCreate, TrajectoryUpdate, TrajectoryResponse,
    TrajectoryListResponse, TrajectoryUploadResponse, TrajectoryDeleteResponse,
    TrajectoryQueryParams, TrajectoryPointCreate, TrajectoryPointResponse,
    TrajectoryDetailResponse, BoundingBox, TrajectoryStatistics, FileUploadRequest
)

# 路网相关
from .road_network import (
    RoadNetworkCreate, RoadNetworkResponse, RoadSegmentCreate, RoadSegmentResponse
)

# 文件相关
from .file import FileCreate, FileResponse

# 系统日志相关
from .system_log import SystemLogCreate, SystemLogResponse

# 匹配相关
from .matching import (
    MatchingRequest, MatchingStartResponse, MatchingStatusResponse,
    MatchingResultResponse, MatchingTaskQueryParams, MatchingTaskListResponse,
    MatchingAlgorithm
)

# 从 DataModels 导入枚举
from DataModels.enums import DataSource, DataCategory, TrajectoryStatus, LogLevel

__all__ = [
    # 用户相关
    "UserCreate", "UserLogin", "UserResponse",
    
    # 轨迹相关
    "TrajectoryCreate", "TrajectoryUpdate", "TrajectoryResponse",
    "TrajectoryListResponse", "TrajectoryUploadResponse", "TrajectoryDeleteResponse",
    "TrajectoryQueryParams", "TrajectoryPointCreate", "TrajectoryPointResponse",
    "TrajectoryDetailResponse", "BoundingBox", "TrajectoryStatistics", "FileUploadRequest",
    
    # 路网相关
    "RoadNetworkCreate", "RoadNetworkResponse", "RoadSegmentCreate", "RoadSegmentResponse",
    
    # 文件相关
    "FileCreate", "FileResponse",
    
    # 系统日志相关
    "SystemLogCreate", "SystemLogResponse",
    
    # 匹配相关
    "MatchingRequest", "MatchingStartResponse", "MatchingStatusResponse",
    "MatchingResultResponse", "MatchingTaskQueryParams", "MatchingTaskListResponse",
    "MatchingAlgorithm",
    
    # 枚举类型
    "DataSource", "DataCategory", "TrajectoryStatus", "LogLevel"
]

__version__ = "0.2.0"