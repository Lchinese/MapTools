"""
轨迹相关数据验证模式
定义轨迹相关的Pydantic模型用于数据验证
"""

from pydantic import BaseModel, Field, validator, ConfigDict
from typing import List, Optional, Dict, Any, Union
from datetime import datetime

from DataModels.enums import TrajectoryStatus, DataSource, DataCategory


class TrajectoryPointBase(BaseModel):
    """轨迹点基础模型"""
    latitude: float = Field(..., ge=-90, le=90, description="纬度")
    longitude: float = Field(..., ge=-180, le=180, description="经度")
    timestamp: datetime = Field(..., description="时间戳")
    elevation: Optional[float] = Field(None, ge=0, description="海拔高度（米）")
    speed: Optional[float] = Field(None, ge=0, le=500, description="速度（km/h）")
    direction: Optional[float] = Field(None, ge=0, le=360, description="方向角（度）")
    accuracy: Optional[float] = Field(None, ge=0, description="精度（米）")
    
    @validator('latitude')
    def validate_latitude(cls, v):
        if not -90 <= v <= 90:
            raise ValueError('纬度必须在-90到90之间')
        return v
    
    @validator('longitude')
    def validate_longitude(cls, v):
        if not -180 <= v <= 180:
            raise ValueError('经度必须在-180到180之间')
        return v


class TrajectoryPointCreate(TrajectoryPointBase):
    """创建轨迹点模型"""
    pass


class TrajectoryPointResponse(TrajectoryPointBase):
    """轨迹点响应模型"""
    id: int
    trajectory_id: int
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class TrajectoryBase(BaseModel):
    """轨迹基础模型"""
    name: Optional[str] = Field(None, max_length=255, description="轨迹名称")
    description: Optional[str] = Field(None, description="轨迹描述")
    filename: str = Field(..., max_length=255, description="原始文件名")
    file_size: int = Field(..., ge=0, description="文件大小（字节）")
    file_type: str = Field(..., max_length=50, description="文件类型")
    data_source: DataSource = Field(..., description="数据源类型")
    data_category: DataCategory = Field(..., description="数据类别")
    vehicle_id: Optional[str] = Field(None, max_length=100, description="车辆ID")
    passenger_id: Optional[str] = Field(None, max_length=100, description="乘客ID")


class TrajectoryCreate(TrajectoryBase):
    """创建轨迹模型"""
    pass


class TrajectoryUpdate(BaseModel):
    """更新轨迹模型"""
    name: Optional[str] = Field(None, max_length=255, description="轨迹名称")
    description: Optional[str] = Field(None, description="轨迹描述")
    status: Optional[TrajectoryStatus] = Field(None, description="处理状态")


class TrajectoryResponse(TrajectoryBase):
    """轨迹响应模型"""
    id: int
    point_count: int = Field(0, description="轨迹点数量")
    total_distance: Optional[float] = Field(None, description="总距离（米）")
    duration: Optional[int] = Field(None, description="持续时间（秒）")
    bounds_min_lat: Optional[float] = Field(None, description="最小纬度")
    bounds_max_lat: Optional[float] = Field(None, description="最大纬度")
    bounds_min_lng: Optional[float] = Field(None, description="最小经度")
    bounds_max_lng: Optional[float] = Field(None, description="最大经度")
    status: TrajectoryStatus = Field(TrajectoryStatus.UPLOADED, description="处理状态")
    processing_started_at: Optional[datetime] = Field(None, description="处理开始时间")
    processing_completed_at: Optional[datetime] = Field(None, description="处理完成时间")
    error_message: Optional[str] = Field(None, description="错误信息")
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class TrajectoryDetailResponse(TrajectoryResponse):
    """轨迹详情响应模型"""
    points: List[TrajectoryPointResponse] = Field(default_factory=list, description="轨迹点列表")


class TrajectoryListResponse(BaseModel):
    """轨迹列表响应模型"""
    trajectories: List[TrajectoryResponse]
    total: int = Field(..., description="总数量")
    page: int = Field(..., ge=1, description="当前页码")
    limit: int = Field(..., ge=1, le=100, description="每页数量")
    pages: int = Field(..., ge=1, description="总页数")


class TrajectoryUploadResponse(BaseModel):
    """轨迹上传响应模型"""
    trajectory_id: str = Field(..., description="轨迹ID")
    filename: str = Field(..., description="文件名")
    file_size: int = Field(..., description="文件大小（字节）")
    point_count: int = Field(..., description="轨迹点数量")
    upload_time: datetime = Field(..., description="上传时间")
    status: TrajectoryStatus = Field(..., description="状态")


class TrajectoryDeleteResponse(BaseModel):
    """轨迹删除响应模型"""
    trajectory_id: str = Field(..., description="轨迹ID")
    deleted_at: datetime = Field(..., description="删除时间")


class BoundingBox(BaseModel):
    """边界框模型"""
    min_lat: float = Field(..., ge=-90, le=90, description="最小纬度")
    max_lat: float = Field(..., ge=-90, le=90, description="最大纬度")
    min_lng: float = Field(..., ge=-180, le=180, description="最小经度")
    max_lng: float = Field(..., ge=-180, le=180, description="最大经度")
    
    @validator('max_lat')
    def validate_max_lat(cls, v, values):
        if 'min_lat' in values and v <= values['min_lat']:
            raise ValueError('最大纬度必须大于最小纬度')
        return v
    
    @validator('max_lng')
    def validate_max_lng(cls, v, values):
        if 'min_lng' in values and v <= values['min_lng']:
            raise ValueError('最大经度必须大于最小经度')
        return v


class TrajectoryStatistics(BaseModel):
    """轨迹统计信息模型"""
    total_points: int = Field(..., ge=0, description="总点数")
    total_distance: float = Field(..., ge=0, description="总距离（米）")
    duration: int = Field(..., ge=0, description="持续时间（秒）")
    avg_speed: Optional[float] = Field(None, ge=0, description="平均速度（km/h）")
    max_speed: Optional[float] = Field(None, ge=0, description="最大速度（km/h）")
    bounds: BoundingBox = Field(..., description="边界框")


class FileUploadRequest(BaseModel):
    """文件上传请求模型"""
    name: Optional[str] = Field(None, max_length=255, description="轨迹名称")
    description: Optional[str] = Field(None, description="轨迹描述")
    data_type: DataSource = Field(DataSource.AUTO, description="数据类型")


class TrajectoryQueryParams(BaseModel):
    """轨迹查询参数模型"""
    page: int = Field(1, ge=1, description="页码")
    limit: int = Field(20, ge=1, le=100, description="每页数量")
    status: Optional[TrajectoryStatus] = Field(None, description="轨迹状态")
    data_source: Optional[DataSource] = Field(None, description="数据源类型")
    start_date: Optional[datetime] = Field(None, description="开始日期")
    end_date: Optional[datetime] = Field(None, description="结束日期")
    vehicle_id: Optional[str] = Field(None, max_length=100, description="车辆ID")
    
    @validator('end_date')
    def validate_end_date(cls, v, values):
        if v and 'start_date' in values and values['start_date'] and v <= values['start_date']:
            raise ValueError('结束日期必须大于开始日期')
        return v