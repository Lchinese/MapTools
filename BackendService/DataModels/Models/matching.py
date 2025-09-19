"""
匹配相关数据模型
定义地图匹配相关的数据库模型
"""

from sqlalchemy import Column, Integer, String, DateTime, Text, Float, Boolean, ForeignKey, Index
from sqlalchemy.dialects.mysql import LONGTEXT
from sqlalchemy.orm import relationship
from geoalchemy2 import Geometry
from datetime import datetime

from ..base import BaseModel, TimestampMixin, SoftDeleteMixin


class MatchingTask(BaseModel, TimestampMixin, SoftDeleteMixin):
    """地图匹配任务模型"""
    __tablename__ = "matching_tasks"
    
    # 业务主键
    task_id = Column(String(36), unique=True, nullable=False, comment="任务ID")
    
    # 关联信息
    trajectory_id = Column(String(36), ForeignKey("trajectories.trajectory_id"), nullable=False, comment="轨迹ID")
    user_id = Column(String(36), nullable=False, comment="用户ID")
    algorithm = Column(String(50), nullable=False, comment="匹配算法")
    parameters = Column(LONGTEXT, nullable=True, comment="算法参数（JSON格式）")
    
    # 状态信息
    status = Column(String(50), default="queued", comment="任务状态")
    progress = Column(Integer, default=0, comment="处理进度（0-100）")
    
    # 时间信息
    started_at = Column(DateTime(timezone=True), nullable=True, comment="开始时间")
    completed_at = Column(DateTime(timezone=True), nullable=True, comment="完成时间")
    estimated_duration = Column(Integer, nullable=True, comment="预计持续时间（秒）")
    
    # 结果信息
    matched_points_count = Column(Integer, default=0, comment="匹配点数量")
    unmatched_points_count = Column(Integer, default=0, comment="未匹配点数量")
    accuracy = Column(Float, nullable=True, comment="匹配精度")
    processing_time = Column(Float, nullable=True, comment="处理时间（秒）")
    error_message = Column(Text, nullable=True, comment="错误信息")
    
    # 关联关系
    trajectory = relationship("Trajectory", back_populates="matching_tasks")
    matched_points = relationship("MatchedPoint", back_populates="matching_task", cascade="all, delete-orphan")
    
    # 索引
    __table_args__ = (
        Index('idx_task_id', 'task_id'),
        Index('idx_task_trajectory_id', 'trajectory_id'),
        Index('idx_task_status', 'status'),
        Index('idx_task_created_at', 'created_at'),
    )
    
    def __repr__(self) -> str:
        return f"<MatchingTask(id={self.id}, task_id='{self.task_id}', status='{self.status}')>"


class MatchedPoint(BaseModel, TimestampMixin):
    """匹配点模型"""
    __tablename__ = "matched_points"
    
    # 业务主键
    matched_point_id = Column(String(36), unique=True, nullable=False, comment="匹配点ID")
    
    # 关联信息
    trajectory_id = Column(String(36), ForeignKey("trajectories.trajectory_id"), nullable=False, comment="轨迹ID")
    matching_task_id = Column(String(36), ForeignKey("matching_tasks.task_id"), nullable=False, comment="匹配任务ID")
    original_point_id = Column(String(36), ForeignKey("trajectory_points.point_id"), nullable=False, comment="原始轨迹点ID")
    road_segment_id = Column(String(100), nullable=True, comment="匹配的道路段ID")
    
    # 原始坐标
    original_latitude = Column(Float, nullable=False, comment="原始纬度")
    original_longitude = Column(Float, nullable=False, comment="原始经度")
    
    # 匹配坐标
    matched_latitude = Column(Float, nullable=False, comment="匹配纬度")
    matched_longitude = Column(Float, nullable=False, comment="匹配经度")
    matched_geom = Column(Geometry('POINT', srid=4326), nullable=True, comment="匹配点空间几何对象")
    matched_timestamp = Column(DateTime(timezone=True), nullable=True, comment="匹配时间戳")
    elevation = Column(Float, nullable=True, comment="海拔高度（米）")
    
    # 匹配信息
    distance = Column(Float, nullable=False, comment="匹配距离（米）")
    confidence = Column(Float, nullable=False, comment="匹配置信度（0-1）")
    
    # 道路信息
    road_name = Column(String(255), nullable=True, comment="道路名称")
    road_type = Column(String(50), nullable=True, comment="道路类型")
    
    # 关联关系
    trajectory = relationship("Trajectory")
    matching_task = relationship("MatchingTask", back_populates="matched_points")
    original_point = relationship("TrajectoryPoint", back_populates="matched_points")
    
    # 索引
    __table_args__ = (
        Index('idx_matched_point_id', 'matched_point_id'),
        Index('idx_matched_trajectory_id', 'trajectory_id'),
        Index('idx_matched_task_id', 'matching_task_id'),
        Index('idx_matched_original_point_id', 'original_point_id'),
        Index('idx_matched_geom', 'matched_geom', mysql_length={'matched_geom': 32}),
    )
    
    def __repr__(self) -> str:
        return f"<MatchedPoint(id={self.id}, distance={self.distance:.2f}m, confidence={self.confidence:.3f})>"
