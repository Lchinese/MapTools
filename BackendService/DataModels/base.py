"""
基础数据模型
提供所有数据模型的基类和通用功能
"""

from sqlalchemy import Column, Integer, String, DateTime, Text, Float, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
from typing import Any, Dict

# 创建基础模型类
Base = declarative_base()


class BaseModel(Base):
    """基础模型类，包含通用字段"""
    __abstract__ = True
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        将模型实例转换为字典
        
        Returns:
            Dict[str, Any]: 模型数据字典
        """
        result = {}
        for column in self.__table__.columns:
            value = getattr(self, column.name)
            if isinstance(value, datetime):
                result[column.name] = value.isoformat()
            else:
                result[column.name] = value
        return result
    
    def update_from_dict(self, data: Dict[str, Any]) -> None:
        """
        从字典更新模型实例
        
        Args:
            data: 包含更新数据的字典
        """
        for key, value in data.items():
            if hasattr(self, key) and key not in ['id', 'created_at', 'updated_at']:
                setattr(self, key, value)
    
    def __repr__(self) -> str:
        """返回模型的字符串表示"""
        return f"<{self.__class__.__name__}(id={self.id})>"


class TimestampMixin:
    """时间戳混入类"""
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class SoftDeleteMixin:
    """软删除混入类"""
    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    
    def soft_delete(self) -> None:
        """软删除记录"""
        self.is_deleted = True
        self.deleted_at = func.now()
    
    def restore(self) -> None:
        """恢复软删除的记录"""
        self.is_deleted = False
        self.deleted_at = None


class AuditMixin:
    """审计混入类"""
    created_by = Column(String(100), nullable=True)
    updated_by = Column(String(100), nullable=True)
    
    def set_created_by(self, user_id: str) -> None:
        """设置创建者"""
        self.created_by = user_id
    
    def set_updated_by(self, user_id: str) -> None:
        """设置更新者"""
        self.updated_by = user_id