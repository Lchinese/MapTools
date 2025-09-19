"""
公共枚举定义
定义项目中使用的所有枚举类型
"""

from enum import Enum


class TrajectoryStatus(str, Enum):
    """轨迹状态枚举"""
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class DataSource(str, Enum):
    """数据源类型枚举"""
    TAXI_GPS = "taxi_gps"
    BUS_CARD = "bus_card"
    METRO_CARD = "metro_card"
    TAXI_TRANSACTION = "taxi_transaction"
    BUS_GPS = "bus_gps"
    GPX = "gpx"
    CSV = "csv"
    AUTO = "auto"


class DataCategory(str, Enum):
    """数据类别枚举"""
    CONTINUOUS_TRAJECTORY = "continuous_trajectory"
    ORIGIN_DESTINATION = "origin_destination"
    TIME_RANGE = "time_range"


class LogLevel(str, Enum):
    """日志级别枚举"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class TaskStatus(str, Enum):
    """任务状态枚举"""
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class FileStatus(str, Enum):
    """文件状态枚举"""
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
