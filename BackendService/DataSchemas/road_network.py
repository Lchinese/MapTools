"""
路网相关数据验证模式
定义路网相关的Pydantic模型用于数据验证
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime


class RoadNetworkBase(BaseModel):
    """路网基础模型"""
    network_id: str = Field(..., max_length=100, description="路网ID")
    name: str = Field(..., max_length=255, description="路网名称")
    description: Optional[str] = Field(None, description="路网描述")
    version: Optional[str] = Field(None, max_length=50, description="版本号")
    data_source: Optional[str] = Field(None, max_length=100, description="数据源")
    data_format: Optional[str] = Field(None, max_length=50, description="数据格式")
    coordinate_system: str = Field("EPSG:4326", max_length=50, description="坐标系")


class RoadNetworkCreate(RoadNetworkBase):
    """创建路网模型"""
    pass


class RoadNetworkResponse(RoadNetworkBase):
    """路网响应模型"""
    id: int = Field(..., description="路网ID")
    bounds_min_lat: Optional[float] = Field(None, description="最小纬度")
    bounds_max_lat: Optional[float] = Field(None, description="最大纬度")
    bounds_min_lng: Optional[float] = Field(None, description="最小经度")
    bounds_max_lng: Optional[float] = Field(None, description="最大经度")
    coverage_area: Optional[float] = Field(None, description="覆盖面积（平方公里）")
    total_roads: int = Field(0, description="道路总数")
    total_length: Optional[float] = Field(None, description="总长度（米）")
    is_active: bool = Field(True, description="是否激活")
    last_updated: Optional[datetime] = Field(None, description="最后更新时间")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    
    model_config = ConfigDict(from_attributes=True)


class RoadSegmentBase(BaseModel):
    """道路段基础模型"""
    segment_id: str = Field(..., max_length=100, description="道路段ID")
    road_name: Optional[str] = Field(None, max_length=255, description="道路名称")
    road_type: Optional[str] = Field(None, max_length=50, description="道路类型")
    start_latitude: float = Field(..., ge=-90, le=90, description="起点纬度")
    start_longitude: float = Field(..., ge=-180, le=180, description="起点经度")
    end_latitude: float = Field(..., ge=-90, le=90, description="终点纬度")
    end_longitude: float = Field(..., ge=-180, le=180, description="终点经度")
    length: Optional[float] = Field(None, ge=0, description="长度（米）")
    max_speed: Optional[float] = Field(None, ge=0, description="最大限速（km/h）")
    one_way: bool = Field(False, description="是否单行道")


class RoadSegmentCreate(RoadSegmentBase):
    """创建道路段模型"""
    network_id: str = Field(..., max_length=100, description="路网ID")


class RoadSegmentResponse(RoadSegmentBase):
    """道路段响应模型"""
    id: int = Field(..., description="道路段ID")
    network_id: str = Field(..., description="路网ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    
    model_config = ConfigDict(from_attributes=True)
