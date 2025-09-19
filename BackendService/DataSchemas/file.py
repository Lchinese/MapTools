"""
文件相关数据验证模式
定义文件管理相关的Pydantic模型用于数据验证
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime

from DataModels.enums import TrajectoryStatus


class FileBase(BaseModel):
    """文件基础模型"""
    filename: str = Field(..., max_length=255, description="文件名")
    original_filename: str = Field(..., max_length=255, description="原始文件名")
    file_size: int = Field(..., ge=0, description="文件大小（字节）")
    file_type: str = Field(..., max_length=50, description="文件类型")
    mime_type: Optional[str] = Field(None, max_length=100, description="MIME类型")


class FileCreate(FileBase):
    """创建文件模型"""
    file_path: str = Field(..., max_length=500, description="文件路径")
    user_id: Optional[str] = Field(None, max_length=36, description="用户ID")


class FileResponse(FileBase):
    """文件响应模型"""
    file_id: str = Field(..., description="文件ID")
    user_id: Optional[str] = Field(None, description="用户ID")
    file_path: str = Field(..., description="文件路径")
    status: TrajectoryStatus = Field(..., description="处理状态")
    error_message: Optional[str] = Field(None, description="错误信息")
    trajectory_id: Optional[int] = Field(None, description="关联轨迹ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    
    model_config = ConfigDict(from_attributes=True)
