"""
轨迹相关数据模型
定义轨迹相关的数据库模型
"""

from sqlalchemy import Column, Integer, String, DateTime, Text, Float, Boolean, ForeignKey, Index, Enum as SQLEnum
from sqlalchemy.dialects.mysql import LONGTEXT
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from geoalchemy2 import Geometry
from datetime import datetime
from typing import List, Optional

from ..base import BaseModel, TimestampMixin, SoftDeleteMixin, AuditMixin
from ..enums import TrajectoryStatus, DataSource, DataCategory


class Trajectory(BaseModel, TimestampMixin, SoftDeleteMixin, AuditMixin):
    """轨迹模型"""
    __tablename__ = "trajectories"
    
    # 业务主键
    trajectory_id = Column(String(36), unique=True, nullable=False, comment="轨迹ID")
    
    # 基本信息
    user_id = Column(String(36), ForeignKey("users.user_id"), nullable=False, comment="用户ID")
    name = Column(String(200), nullable=False, comment="轨迹名称")
    description = Column(Text, nullable=True, comment="轨迹描述")
    filename = Column(String(255), nullable=False, comment="原始文件名")
    file_path = Column(String(500), nullable=True, comment="文件存储路径")
    file_size = Column(Integer, nullable=False, comment="文件大小（字节）")
    file_type = Column(String(50), nullable=False, comment="文件类型（gpx, csv, txt等）")
    
    # 数据源信息
    data_source = Column(SQLEnum(DataSource), nullable=False, comment="数据源类型")
    data_category = Column(SQLEnum(DataCategory), nullable=False, comment="数据类别")
    vehicle_id = Column(String(100), nullable=True, comment="车辆ID")
    passenger_id = Column(String(100), nullable=True, comment="乘客ID")
    
    # 轨迹统计信息
    point_count = Column(Integer, default=0, comment="轨迹点数量")
    total_distance = Column(Float, nullable=True, comment="总距离（米）")
    duration = Column(Integer, nullable=True, comment="持续时间（秒）")
    
    # 空间信息
    bounds_min_lat = Column(Float, nullable=True, comment="最小纬度")
    bounds_max_lat = Column(Float, nullable=True, comment="最大纬度")
    bounds_min_lng = Column(Float, nullable=True, comment="最小经度")
    bounds_max_lng = Column(Float, nullable=True, comment="最大经度")
    
    # 状态信息
    status = Column(SQLEnum(TrajectoryStatus), default=TrajectoryStatus.UPLOADED, comment="处理状态")
    processing_started_at = Column(DateTime(timezone=True), nullable=True, comment="处理开始时间")
    processing_completed_at = Column(DateTime(timezone=True), nullable=True, comment="处理完成时间")
    error_message = Column(Text, nullable=True, comment="错误信息")
    
    # 关联关系
    user = relationship("User", back_populates="trajectories")
    points = relationship("TrajectoryPoint", back_populates="trajectory", cascade="all, delete-orphan")
    matching_tasks = relationship("MatchingTask", back_populates="trajectory", cascade="all, delete-orphan")
    files = relationship("File", back_populates="trajectory", cascade="all, delete-orphan")
    
    # 索引
    __table_args__ = (
        Index('idx_trajectory_id', 'trajectory_id'),
        Index('idx_trajectory_status', 'status'),
        Index('idx_trajectory_created_at', 'created_at'),
        Index('idx_trajectory_vehicle_id', 'vehicle_id'),
        Index('idx_trajectory_data_source', 'data_source'),
        {'extend_existing': True}
    )
    
    def __repr__(self) -> str:
        return f"<Trajectory(id={self.id}, name='{self.name}', status='{self.status}')>"


class TrajectoryPoint(BaseModel, TimestampMixin):
    """轨迹点模型"""
    __tablename__ = "trajectory_points"
    
    # 业务主键
    point_id = Column(String(36), unique=True, nullable=False, comment="点ID")
    
    # 关联信息
    trajectory_id = Column(String(36), ForeignKey("trajectories.trajectory_id"), nullable=False, comment="轨迹ID")
    sequence_number = Column(Integer, nullable=False, comment="序列号")
    
    # 空间信息
    latitude = Column(Float, nullable=False, comment="纬度")
    longitude = Column(Float, nullable=False, comment="经度")
    elevation = Column(Float, nullable=True, comment="海拔高度（米）")
    geom = Column(Geometry('POINT', srid=4326), nullable=True, comment="空间几何对象")
    
    # 时间信息
    timestamp = Column(DateTime(timezone=True), nullable=False, comment="时间戳")
    
    # 运动信息
    speed = Column(Float, nullable=True, comment="速度（km/h）")
    direction = Column(Float, nullable=True, comment="方向角（度）")
    accuracy = Column(Float, nullable=True, comment="精度（米）")
    
    # 其他属性
    raw_data = Column(LONGTEXT, nullable=True, comment="原始数据（JSON格式）")
    
    # 关联关系
    trajectory = relationship("Trajectory", back_populates="points")
    matched_points = relationship("MatchedPoint", back_populates="original_point", cascade="all, delete-orphan")
    
    # 索引
    __table_args__ = (
        Index('idx_point_trajectory_id', 'trajectory_id'),
        Index('idx_point_timestamp', 'timestamp'),
        Index('idx_point_geom', 'geom', mysql_length={'geom': 32}),
        {'extend_existing': True}
    )
    
    def __repr__(self) -> str:
        return f"<TrajectoryPoint(id={self.id}, point_id='{self.point_id}', sequence_number={self.sequence_number})>"