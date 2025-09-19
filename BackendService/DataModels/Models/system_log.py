"""
系统日志数据模型
定义系统日志相关的数据库模型
"""

from sqlalchemy import Column, Integer, String, DateTime, Text, Index, Enum as SQLEnum
from sqlalchemy.dialects.mysql import LONGTEXT
from datetime import datetime

from ..base import BaseModel, TimestampMixin
from ..enums import LogLevel


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
        Index('idx_log_id', 'log_id'),
        Index('idx_log_user_id', 'user_id'),
        Index('idx_log_level', 'level'),
        Index('idx_log_module', 'module'),
        Index('idx_log_action', 'action'),
        Index('idx_log_created_at', 'created_at'),
        Index('idx_log_request_id', 'request_id'),
    )
    
    def __repr__(self) -> str:
        return f"<SystemLog(id={self.id}, level='{self.level}', module='{self.module}')>"
