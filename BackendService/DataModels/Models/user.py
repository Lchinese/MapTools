"""
用户数据模型
定义用户认证相关的数据库模型
"""

from sqlalchemy import Column, String, Boolean, DateTime, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ..base import BaseModel, TimestampMixin, SoftDeleteMixin


class User(BaseModel, TimestampMixin, SoftDeleteMixin):
    """用户模型"""
    __tablename__ = "users"
    
    # 用户基本信息
    user_id = Column(String(36), unique=True, nullable=False, comment="用户ID")
    username = Column(String(50), unique=True, nullable=False, comment="用户名")
    email = Column(String(100), unique=True, nullable=False, comment="邮箱")
    password_hash = Column(String(255), nullable=False, comment="密码哈希")
    full_name = Column(String(100), nullable=True, comment="全名")
    phone = Column(String(20), nullable=True, comment="手机号")
    avatar_url = Column(String(500), nullable=True, comment="头像URL")
    
    # 状态信息
    is_active = Column(Boolean, default=True, nullable=False, comment="是否激活")
    is_admin = Column(Boolean, default=False, nullable=False, comment="是否管理员")
    last_login_at = Column(DateTime(timezone=True), nullable=True, comment="最后登录时间")
    
    # 关联关系
    # 注意：由于轨迹数据现在存储在文件系统中，移除了与轨迹相关的关联关系
    
    # 索引
    __table_args__ = (
        Index('idx_user_id', 'user_id'),
        Index('idx_username', 'username'),
        Index('idx_email', 'email'),
        {'extend_existing': True}
    )
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}')>"