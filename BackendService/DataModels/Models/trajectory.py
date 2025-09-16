"""
轨迹数据模型
定义轨迹相关的数据库模型
"""

from sqlalchemy import Column, Integer, String, DateTime, Text, Float, Boolean, ForeignKey, Index, Enum as SQLEnum
from sqlalchemy.dialects.mysql import LONGTEXT
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from geoalchemy2 import Geometry
from datetime import datetime
from typing import List, Optional
import enum

from ..base import BaseModel, TimestampMixin, SoftDeleteMixin, AuditMixin


class TrajectoryStatus(enum.Enum):
    """轨迹状态枚举"""
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class DataSource(enum.Enum):
    """数据源类型枚举"""
    TAXI_GPS = "taxi_gps"
    BUS_CARD = "bus_card"
    METRO_CARD = "metro_card"
    TAXI_TRANSACTION = "taxi_transaction"
    BUS_GPS = "bus_gps"
    GPX = "gpx"
    CSV = "csv"
    AUTO = "auto"


class DataCategory(enum.Enum):
    """数据类别枚举"""
    CONTINUOUS_TRAJECTORY = "continuous_trajectory"
    ORIGIN_DESTINATION = "origin_destination"
    TIME_RANGE = "time_range"


class LogLevel(enum.Enum):
    """日志级别枚举"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class Trajectory(BaseModel, TimestampMixin, SoftDeleteMixin, AuditMixin):
    """轨迹模型"""
    __tablename__ = "trajectories"
    
    # 主键
    trajectory_id = Column(String(36), primary_key=True, comment="轨迹ID")
    
    # 基本信息
    user_id = Column(String(36), nullable=False, comment="用户ID")
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
        Index('idx_trajectory_status', 'status'),
        Index('idx_trajectory_created_at', 'created_at'),
        Index('idx_trajectory_vehicle_id', 'vehicle_id'),
        Index('idx_trajectory_data_source', 'data_source'),
    )
    
    def __repr__(self) -> str:
        return f"<Trajectory(id={self.id}, name='{self.name}', status='{self.status}')>"


class TrajectoryPoint(BaseModel, TimestampMixin):
    """轨迹点模型"""
    __tablename__ = "trajectory_points"
    
    # 主键
    point_id = Column(String(36), primary_key=True, comment="点ID")
    
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
    )
    
    def __repr__(self) -> str:
        return f"<TrajectoryPoint(id={self.id}, lat={self.latitude}, lng={self.longitude})>"


class MatchingTask(BaseModel, TimestampMixin, SoftDeleteMixin):
    """地图匹配任务模型"""
    __tablename__ = "matching_tasks"
    
    # 主键
    task_id = Column(String(36), primary_key=True, comment="任务ID")
    
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
        Index('idx_task_trajectory_id', 'trajectory_id'),
        Index('idx_task_status', 'status'),
        Index('idx_task_created_at', 'created_at'),
    )
    
    def __repr__(self) -> str:
        return f"<MatchingTask(id={self.id}, task_id='{self.task_id}', status='{self.status}')>"


class MatchedPoint(BaseModel, TimestampMixin):
    """匹配点模型"""
    __tablename__ = "matched_points"
    
    # 主键
    matched_point_id = Column(String(36), primary_key=True, comment="匹配点ID")
    
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
        Index('idx_matched_trajectory_id', 'trajectory_id'),
        Index('idx_matched_task_id', 'matching_task_id'),
        Index('idx_matched_original_point_id', 'original_point_id'),
        Index('idx_matched_geom', 'matched_geom', mysql_length={'matched_geom': 32}),
    )
    
    def __repr__(self) -> str:
        return f"<MatchedPoint(id={self.id}, distance={self.distance:.2f}m, confidence={self.confidence:.3f})>"


class User(BaseModel, TimestampMixin, SoftDeleteMixin):
    """用户模型"""
    __tablename__ = "users"
    
    user_id = Column(String(36), unique=True, nullable=False, comment="用户ID")
    username = Column(String(50), unique=True, nullable=False, comment="用户名")
    email = Column(String(100), unique=True, nullable=False, comment="邮箱")
    password_hash = Column(String(255), nullable=False, comment="密码哈希")
    full_name = Column(String(100), nullable=True, comment="全名")
    avatar_url = Column(String(500), nullable=True, comment="头像URL")
    is_active = Column(Boolean, default=True, comment="是否激活")
    is_admin = Column(Boolean, default=False, comment="是否管理员")
    last_login_at = Column(DateTime(timezone=True), nullable=True, comment="最后登录时间")
    
    # 关联关系
    trajectories = relationship("Trajectory", back_populates="user", cascade="all, delete-orphan")
    
    # 索引
    __table_args__ = (
        Index('idx_user_username', 'username'),
        Index('idx_user_email', 'email'),
        Index('idx_user_created_at', 'created_at'),
    )
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}')>"


class RoadNetwork(BaseModel, TimestampMixin):
    """路网模型"""
    __tablename__ = "road_networks"
    
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
    
    # 关联关系
    road_segments = relationship("RoadSegment", back_populates="road_network", cascade="all, delete-orphan")
    
    # 索引
    __table_args__ = (
        Index('idx_road_network_id', 'network_id'),
        Index('idx_road_network_active', 'is_active'),
    )
    
    def __repr__(self) -> str:
        return f"<RoadNetwork(id={self.id}, network_id='{self.network_id}', name='{self.name}')>"


class RoadSegment(BaseModel, TimestampMixin):
    """道路段模型"""
    __tablename__ = "road_segments"
    
    # 关联信息
    network_id = Column(String(100), ForeignKey("road_networks.network_id"), nullable=False, comment="路网ID")
    
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
    
    # 关联关系
    road_network = relationship("RoadNetwork", back_populates="road_segments")
    
    # 索引
    __table_args__ = (
        Index('idx_road_segment_network_id', 'network_id'),
        Index('idx_road_segment_id', 'segment_id'),
        Index('idx_road_segment_type', 'road_type'),
        Index('idx_road_segment_geom', 'geom', mysql_length={'geom': 32}),
    )
    
    def __repr__(self) -> str:
        return f"<RoadSegment(id={self.id}, segment_id='{self.segment_id}', road_name='{self.road_name}')>"


class File(BaseModel, TimestampMixin, SoftDeleteMixin):
    """文件模型"""
    __tablename__ = "files"
    
    file_id = Column(String(36), unique=True, nullable=False, comment="文件ID")
    user_id = Column(String(36), nullable=True, comment="用户ID")
    filename = Column(String(255), nullable=False, comment="文件名")
    original_filename = Column(String(255), nullable=False, comment="原始文件名")
    file_path = Column(String(500), nullable=False, comment="文件路径")
    file_size = Column(Integer, nullable=False, comment="文件大小（字节）")
    file_type = Column(String(50), nullable=False, comment="文件类型")
    mime_type = Column(String(100), nullable=True, comment="MIME类型")
    
    # 处理状态
    status = Column(SQLEnum(TrajectoryStatus), default=TrajectoryStatus.UPLOADED, comment="处理状态")
    error_message = Column(Text, nullable=True, comment="错误信息")
    
    # 关联信息
    trajectory_id = Column(Integer, ForeignKey("trajectories.id"), nullable=True, comment="关联轨迹ID")
    
    # 元数据
    metadata = Column(LONGTEXT, nullable=True, comment="文件元数据")
    
    # 关联关系
    trajectory = relationship("Trajectory", back_populates="files")
    
    # 索引
    __table_args__ = (
        Index('idx_file_user_id', 'user_id'),
        Index('idx_file_trajectory_id', 'trajectory_id'),
        Index('idx_file_type', 'file_type'),
        Index('idx_file_status', 'status'),
        Index('idx_file_created_at', 'created_at'),
    )
    
    def __repr__(self) -> str:
        return f"<File(id={self.id}, file_id='{self.file_id}', filename='{self.filename}')>"


class SystemLog(BaseModel, TimestampMixin):
    """系统日志模型"""
    __tablename__ = "system_logs"
    
    log_id = Column(String(36), unique=True, nullable=False, comment="日志ID")
    user_id = Column(String(36), nullable=True, comment="用户ID")
    
    # 日志信息
    level = Column(SQLEnum(LogLevel), nullable=False, comment="日志级别")
    module = Column(String(100), nullable=False, comment="模块名称")
    action = Column(String(100), nullable=False, comment="操作名称")
    message = Column(Text, nullable=False, comment="日志消息")
    
    # 请求信息
    request_id = Column(String(36), nullable=True, comment="请求ID")
    ip_address = Column(String(45), nullable=True, comment="IP地址")
    user_agent = Column(Text, nullable=True, comment="用户代理")
    
    # 额外数据
    extra_data = Column(LONGTEXT, nullable=True, comment="额外数据")
    
    # 索引
    __table_args__ = (
        Index('idx_log_user_id', 'user_id'),
        Index('idx_log_level', 'level'),
        Index('idx_log_module', 'module'),
        Index('idx_log_action', 'action'),
        Index('idx_log_created_at', 'created_at'),
        Index('idx_log_request_id', 'request_id'),
    )
    
    def __repr__(self) -> str:
        return f"<SystemLog(id={self.id}, level='{self.level}', module='{self.module}')>"