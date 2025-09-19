"""
系统日志数据验证模式
定义系统日志相关的Pydantic模型用于数据验证
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any
from datetime import datetime

from DataModels.enums import LogLevel


class SystemLogBase(BaseModel):
    """系统日志基础模型"""
    level: LogLevel = Field(..., description="日志级别")
    module: str = Field(..., max_length=100, description="模块名称")
    action: str = Field(..., max_length=100, description="操作名称")
    message: str = Field(..., description="日志消息")
    request_id: Optional[str] = Field(None, max_length=36, description="请求ID")
    ip_address: Optional[str] = Field(None, max_length=45, description="IP地址")
    user_agent: Optional[str] = Field(None, description="用户代理")
    extra_data: Optional[Dict[str, Any]] = Field(None, description="额外数据")


class SystemLogCreate(SystemLogBase):
    """创建系统日志模型"""
    user_id: Optional[str] = Field(None, max_length=36, description="用户ID")


class SystemLogResponse(SystemLogBase):
    """系统日志响应模型"""
    log_id: str = Field(..., description="日志ID")
    user_id: Optional[str] = Field(None, description="用户ID")
    created_at: datetime = Field(..., description="创建时间")
    
    model_config = ConfigDict(from_attributes=True)
