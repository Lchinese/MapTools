"""
路网数据模型
定义道路网络相关的数据库模型
"""

from sqlalchemy import Column, Integer, String, DateTime, Text, Float, Boolean, Index, ForeignKey
from sqlalchemy.dialects.mysql import LONGTEXT
from sqlalchemy.sql import func
from geoalchemy2 import Geometry
from datetime import datetime

from ..base import BaseModel, TimestampMixin


class RoadNetwork(BaseModel, TimestampMixin):
    """路网模型"""
    __tablename__ = "road_networks"
    
    # 基本信息
    network_id = Column(String(100), unique=True, nullable=False, comment="路网ID")
    name = Column(String(255), nullable=False, comment="路网名称")
    description = Column(Text, nullable=True, comment="路网描述")
    version = Column(String(50), nullable=True, comment="版本号")
    
    # 覆盖范围
    bounds_min_lat = Column(Float, nullable=True, comment="最小纬度")
    bounds_max_lat = Column(Float, nullable=True, comment="最大纬度")
    bounds_min_lng = Column(Float, nullable=True, comment="最小经度")
    bounds_max_lng = Column(Float, nullable=True, comment="最大经度")
    coverage_area = Column(Float, nullable=True, comment="覆盖面积（平方公里）")
    
    # 统计信息
    total_roads = Column(Integer, default=0, comment="道路总数")
    total_length = Column(Float, nullable=True, comment="总长度（米）")
    
    # 数据源信息
    data_source = Column(String(100), nullable=True, comment="数据源")
    data_format = Column(String(50), nullable=True, comment="数据格式")
    coordinate_system = Column(String(50), default="EPSG:4326", comment="坐标系")
    
    # 状态信息
    is_active = Column(Boolean, default=True, comment="是否激活")
    last_updated = Column(DateTime(timezone=True), nullable=True, comment="最后更新时间")
    
    # 索引
    __table_args__ = (
        Index('idx_road_network_id', 'network_id'),
        Index('idx_road_network_active', 'is_active'),
        {'extend_existing': True}
    )
    
    def __repr__(self) -> str:
        return f"<RoadNetwork(id={self.id}, network_id='{self.network_id}', name='{self.name}')>"


class RoadSegment(BaseModel, TimestampMixin):
    """道路段模型"""
    __tablename__ = "road_segments"
    
    # 关联信息
    network_id = Column(String(100), ForeignKey('road_networks.network_id'), nullable=False, comment="路网ID")
    
    # 基本信息
    segment_id = Column(String(100), nullable=False, comment="道路段ID")
    road_name = Column(String(255), nullable=True, comment="道路名称")
    road_type = Column(String(50), nullable=True, comment="道路类型")
    
    # 空间信息
    start_latitude = Column(Float, nullable=False, comment="起点纬度")
    start_longitude = Column(Float, nullable=False, comment="起点经度")
    end_latitude = Column(Float, nullable=False, comment="终点纬度")
    end_longitude = Column(Float, nullable=False, comment="终点经度")
    geom = Column(Geometry('LINESTRING', srid=4326), nullable=True, comment="空间几何对象")
    
    # 道路属性
    length = Column(Float, nullable=True, comment="长度（米）")
    max_speed = Column(Float, nullable=True, comment="最大限速（km/h）")
    one_way = Column(Boolean, default=False, comment="是否单行道")
    
    # 其他属性
    properties = Column(LONGTEXT, nullable=True, comment="其他属性（JSON格式）")
    
    # 索引
    __table_args__ = (
        Index('idx_road_segment_network_id', 'network_id'),
        Index('idx_road_segment_id', 'segment_id'),
        Index('idx_road_segment_type', 'road_type'),
        Index('idx_road_segment_geom', 'geom', mysql_length={'geom': 32}),
        {'extend_existing': True}
    )
    
    def __repr__(self) -> str:
        return f"<RoadSegment(id={self.id}, segment_id='{self.segment_id}', road_name='{self.road_name}')>"


class RoadNode(BaseModel, TimestampMixin):
    """道路节点模型"""
    __tablename__ = "road_nodes"
    
    # 关联信息
    network_id = Column(String(100), ForeignKey('road_networks.network_id'), nullable=False, comment="路网ID")
    
    # 基本信息
    node_id = Column(String(100), nullable=False, comment="节点ID")
    latitude = Column(Float, nullable=False, comment="纬度")
    longitude = Column(Float, nullable=False, comment="经度")
    node_type = Column(String(50), nullable=True, comment="节点类型")
    
    # 其他属性
    properties = Column(LONGTEXT, nullable=True, comment="其他属性（JSON格式）")
    
    # 索引
    __table_args__ = (
        Index('idx_road_node_network_id', 'network_id'),
        Index('idx_road_node_id', 'node_id'),
        Index('idx_road_node_type', 'node_type'),
        {'extend_existing': True}
    )
    
    def __repr__(self) -> str:
        return f"<RoadNode(id={self.id}, node_id='{self.node_id}', node_type='{self.node_type}')>"