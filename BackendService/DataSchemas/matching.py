"""
地图匹配数据验证模式
定义地图匹配相关的Pydantic模型用于数据验证
"""

from pydantic import BaseModel, Field, validator, ConfigDict
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from enum import Enum


class MatchingAlgorithm(str, Enum):
    """匹配算法枚举"""
    DISTANCE_MATCHING = "distance_matching"
    HMM = "hmm"
    GREEDY = "greedy"


class TaskStatus(str, Enum):
    """任务状态枚举"""
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class MatchingRequest(BaseModel):
    """地图匹配请求模型"""
    trajectory_id: str = Field(..., description="轨迹ID")
    algorithm: MatchingAlgorithm = Field(MatchingAlgorithm.DISTANCE_MATCHING, description="匹配算法")
    parameters: Optional[Dict[str, Any]] = Field(None, description="算法参数")
    road_network: str = Field("default", description="路网数据源")
    
    @validator('parameters')
    def validate_parameters(cls, v):
        if v is not None:
            # 验证距离匹配算法参数
            if 'max_distance' in v:
                if not isinstance(v['max_distance'], (int, float)) or v['max_distance'] <= 0:
                    raise ValueError('max_distance必须是正数')
            if 'max_speed' in v:
                if not isinstance(v['max_speed'], (int, float)) or v['max_speed'] <= 0:
                    raise ValueError('max_speed必须是正数')
        return v


class MatchingParameters(BaseModel):
    """匹配算法参数模型"""
    max_distance: float = Field(1000.0, ge=0, description="最大匹配距离（米）")
    use_speed_filter: bool = Field(True, description="是否使用速度过滤")
    max_speed: float = Field(200.0, ge=0, description="最大合理速度（km/h）")
    sigma: Optional[float] = Field(None, ge=0, description="HMM算法参数sigma")
    beta: Optional[float] = Field(None, ge=0, description="HMM算法参数beta")


class MatchingStartResponse(BaseModel):
    """匹配开始响应模型"""
    task_id: str = Field(..., description="任务ID")
    trajectory_id: str = Field(..., description="轨迹ID")
    algorithm: str = Field(..., description="匹配算法")
    status: TaskStatus = Field(..., description="任务状态")
    estimated_time: Optional[int] = Field(None, description="预计处理时间（秒）")
    created_at: datetime = Field(..., description="创建时间")


class MatchingStatusResponse(BaseModel):
    """匹配状态响应模型"""
    task_id: str = Field(..., description="任务ID")
    status: TaskStatus = Field(..., description="任务状态")
    progress: int = Field(0, ge=0, le=100, description="处理进度（百分比）")
    result: Optional[Dict[str, Any]] = Field(None, description="处理结果")
    created_at: datetime = Field(..., description="创建时间")
    completed_at: Optional[datetime] = Field(None, description="完成时间")


class MatchedPointResponse(BaseModel):
    """匹配点响应模型"""
    point_id: str = Field(..., description="轨迹点ID")
    original_lat: float = Field(..., ge=-90, le=90, description="原始纬度")
    original_lng: float = Field(..., ge=-180, le=180, description="原始经度")
    matched_lat: float = Field(..., ge=-90, le=90, description="匹配纬度")
    matched_lng: float = Field(..., ge=-180, le=180, description="匹配经度")
    road_id: Optional[str] = Field(None, description="道路段ID")
    road_name: Optional[str] = Field(None, description="道路名称")
    confidence: float = Field(..., ge=0, le=1, description="匹配置信度")
    distance: float = Field(..., ge=0, description="匹配距离（米）")


class MatchingStatistics(BaseModel):
    """匹配统计信息模型"""
    total_points: int = Field(..., ge=0, description="总点数")
    matched_points: int = Field(..., ge=0, description="匹配点数")
    unmatched_points: int = Field(..., ge=0, description="未匹配点数")
    accuracy: float = Field(..., ge=0, le=100, description="匹配精度（百分比）")
    avg_confidence: float = Field(..., ge=0, le=1, description="平均置信度")
    processing_time: float = Field(..., ge=0, description="处理时间（秒）")
    avg_distance: float = Field(..., ge=0, description="平均匹配距离（米）")
    min_distance: float = Field(..., ge=0, description="最小匹配距离（米）")
    max_distance: float = Field(..., ge=0, description="最大匹配距离（米）")


class MatchedTrajectory(BaseModel):
    """匹配轨迹模型"""
    points: List[MatchedPointResponse] = Field(..., description="匹配点列表")
    total_distance: float = Field(..., ge=0, description="总距离（米）")
    matched_distance: float = Field(..., ge=0, description="匹配距离（米）")


class MatchingResultResponse(BaseModel):
    """匹配结果响应模型"""
    task_id: str = Field(..., description="任务ID")
    trajectory_id: str = Field(..., description="轨迹ID")
    algorithm: str = Field(..., description="匹配算法")
    status: TaskStatus = Field(..., description="任务状态")
    result: Optional[Dict[str, Any]] = Field(None, description="匹配结果")
    created_at: datetime = Field(..., description="创建时间")
    completed_at: Optional[datetime] = Field(None, description="完成时间")


class MatchingResultDetail(BaseModel):
    """匹配结果详情模型"""
    matched_trajectory: MatchedTrajectory = Field(..., description="匹配轨迹")
    statistics: MatchingStatistics = Field(..., description="统计信息")


class MatchingTaskResponse(BaseModel):
    """匹配任务响应模型"""
    id: int
    task_id: str = Field(..., description="任务ID")
    trajectory_id: int = Field(..., description="轨迹ID")
    algorithm: str = Field(..., description="匹配算法")
    parameters: Optional[Dict[str, Any]] = Field(None, description="算法参数")
    status: TaskStatus = Field(..., description="任务状态")
    progress: int = Field(0, ge=0, le=100, description="处理进度")
    matched_points_count: int = Field(0, ge=0, description="匹配点数量")
    unmatched_points_count: int = Field(0, ge=0, description="未匹配点数量")
    accuracy: Optional[float] = Field(None, ge=0, le=100, description="匹配精度")
    processing_time: Optional[float] = Field(None, ge=0, description="处理时间")
    error_message: Optional[str] = Field(None, description="错误信息")
    started_at: Optional[datetime] = Field(None, description="开始时间")
    completed_at: Optional[datetime] = Field(None, description="完成时间")
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class MatchingTaskListResponse(BaseModel):
    """匹配任务列表响应模型"""
    tasks: List[MatchingTaskResponse]
    total: int = Field(..., description="总数量")
    page: int = Field(..., ge=1, description="当前页码")
    limit: int = Field(..., ge=1, le=100, description="每页数量")
    pages: int = Field(..., ge=1, description="总页数")


class MatchingTaskQueryParams(BaseModel):
    """匹配任务查询参数模型"""
    page: int = Field(1, ge=1, description="页码")
    limit: int = Field(20, ge=1, le=100, description="每页数量")
    status: Optional[TaskStatus] = Field(None, description="任务状态")
    algorithm: Optional[MatchingAlgorithm] = Field(None, description="匹配算法")
    trajectory_id: Optional[str] = Field(None, description="轨迹ID")
    start_date: Optional[datetime] = Field(None, description="开始日期")
    end_date: Optional[datetime] = Field(None, description="结束日期")
    
    @validator('end_date')
    def validate_end_date(cls, v, values):
        if v and 'start_date' in values and values['start_date'] and v <= values['start_date']:
            raise ValueError('结束日期必须大于开始日期')
        return v


class DownloadFormat(str, Enum):
    """下载格式枚举"""
    GPX = "gpx"
    KML = "kml"
    CSV = "csv"
    GEOJSON = "geojson"


class MatchingDownloadRequest(BaseModel):
    """匹配结果下载请求模型"""
    format: DownloadFormat = Field(DownloadFormat.GPX, description="下载格式")
    include_original: bool = Field(False, description="是否包含原始轨迹")
    include_statistics: bool = Field(True, description="是否包含统计信息")


class AlgorithmInfo(BaseModel):
    """算法信息模型"""
    type: str = Field(..., description="算法类型")
    name: str = Field(..., description="算法名称")
    description: Optional[str] = Field(None, description="算法描述")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="算法参数")
    is_available: bool = Field(True, description="是否可用")


class AvailableAlgorithmsResponse(BaseModel):
    """可用算法响应模型"""
    algorithms: List[AlgorithmInfo] = Field(..., description="可用算法列表")
    default_algorithm: str = Field(..., description="默认算法")