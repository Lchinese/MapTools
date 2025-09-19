"""
文件相关数据模型
定义文件管理相关的数据库模型
"""

from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, ForeignKey, Index, Enum as SQLEnum
from sqlalchemy.dialects.mysql import LONGTEXT
from sqlalchemy.orm import relationship
from datetime import datetime

from ..base import BaseModel, TimestampMixin, SoftDeleteMixin
from ..enums import TrajectoryStatus


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
    trajectory_id = Column(String(36), ForeignKey("trajectories.trajectory_id"), nullable=True, comment="关联轨迹ID")
    
    # 元数据
    file_metadata = Column(LONGTEXT, nullable=True, comment="文件元数据")
    
    # 关联关系
    trajectory = relationship("Trajectory", back_populates="files")
    
    # 索引
    __table_args__ = (
        Index('idx_file_id', 'file_id'),
        Index('idx_file_user_id', 'user_id'),
        Index('idx_file_trajectory_id', 'trajectory_id'),
        Index('idx_file_type', 'file_type'),
        Index('idx_file_status', 'status'),
        Index('idx_file_created_at', 'created_at'),
    )
    
    def __repr__(self) -> str:
        return f"<File(id={self.id}, file_id='{self.file_id}', filename='{self.filename}')>"
