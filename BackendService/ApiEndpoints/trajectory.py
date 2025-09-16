"""
轨迹管理API接口
提供轨迹上传、查询、删除等功能
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import logging

from ..CoreConfig.database import get_db
from ..CoreConfig.logging import get_logger
from ..BusinessServices.trajectory_service import TrajectoryService
from ..DataSchemas.trajectory import (
    TrajectoryResponse, TrajectoryListResponse, TrajectoryQueryParams,
    TrajectoryUploadResponse, TrajectoryDeleteResponse, DataSource
)
from ..UtilityTools.file_utils import TrajectoryFileProcessor
from ..UtilityTools.validators import FileValidator

logger = get_logger(__name__)
router = APIRouter(prefix="/api/v1/trajectories", tags=["trajectories"])


@router.post("/upload", response_model=TrajectoryUploadResponse)
async def upload_trajectory(
    file: UploadFile = File(..., description="轨迹文件"),
    name: Optional[str] = Form(None, description="轨迹名称"),
    description: Optional[str] = Form(None, description="轨迹描述"),
    data_type: Optional[DataSource] = Form(DataSource.AUTO, description="数据类型"),
    db: Session = Depends(get_db)
):
    """
    上传轨迹文件
    
    Args:
        file: 上传的文件
        name: 轨迹名称
        description: 轨迹描述
        data_type: 数据类型
        db: 数据库会话
        
    Returns:
        TrajectoryUploadResponse: 上传结果
    """
    try:
        # 验证文件
        file_content = await file.read()
        file_size = len(file_content)
        
        # 文件验证
        validation_result = FileValidator.validate_upload_request(
            filename=file.filename,
            file_size=file_size,
            max_size=10 * 1024 * 1024,  # 10MB
            allowed_types=[".gpx", ".csv", ".txt", ".kml"]
        )
        
        if not validation_result["valid"]:
            raise HTTPException(
                status_code=400,
                detail=f"文件验证失败: {', '.join(validation_result['errors'])}"
            )
        
        # 保存文件
        file_processor = TrajectoryFileProcessor()
        file_path = file_processor.save_uploaded_file(file_content, file.filename)
        
        try:
            # 解析文件
            points, detected_source, data_category = file_processor.parse_file(
                file_path, data_type
            )
            
            # 创建轨迹服务
            trajectory_service = TrajectoryService(db)
            
            # 创建轨迹数据
            from ..DataSchemas.trajectory import TrajectoryCreate
            trajectory_data = TrajectoryCreate(
                name=name or file.filename,
                description=description,
                filename=file.filename,
                file_size=file_size,
                file_type=file.filename.split('.')[-1].lower(),
                data_source=detected_source,
                data_category=data_category
            )
            
            # 创建轨迹
            trajectory = trajectory_service.create_trajectory(
                trajectory_data, str(file_path), points
            )
            
            logger.info(f"轨迹上传成功: ID={trajectory.id}, 文件名={file.filename}")
            
            return TrajectoryUploadResponse(
                trajectory_id=str(trajectory.id),
                filename=file.filename,
                file_size=file_size,
                point_count=len(points),
                upload_time=trajectory.created_at,
                status=trajectory.status
            )
            
        except Exception as e:
            # 清理文件
            file_processor.cleanup_file(file_path)
            raise e
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"轨迹上传失败: {e}")
        raise HTTPException(status_code=500, detail=f"轨迹上传失败: {str(e)}")


@router.get("", response_model=TrajectoryListResponse)
async def get_trajectories(
    page: int = Query(1, ge=1, description="页码"),
    limit: int = Query(20, ge=1, le=100, description="每页数量"),
    status: Optional[str] = Query(None, description="轨迹状态"),
    data_source: Optional[str] = Query(None, description="数据源类型"),
    vehicle_id: Optional[str] = Query(None, description="车辆ID"),
    start_date: Optional[str] = Query(None, description="开始日期"),
    end_date: Optional[str] = Query(None, description="结束日期"),
    db: Session = Depends(get_db)
):
    """
    获取轨迹列表
    
    Args:
        page: 页码
        limit: 每页数量
        status: 轨迹状态
        data_source: 数据源类型
        vehicle_id: 车辆ID
        start_date: 开始日期
        end_date: 结束日期
        db: 数据库会话
        
    Returns:
        TrajectoryListResponse: 轨迹列表
    """
    try:
        # 构建查询参数
        query_params = TrajectoryQueryParams(
            page=page,
            limit=limit,
            status=status,
            data_source=data_source,
            vehicle_id=vehicle_id,
            start_date=start_date,
            end_date=end_date
        )
        
        # 获取轨迹列表
        trajectory_service = TrajectoryService(db)
        result = trajectory_service.get_trajectory_list(query_params)
        
        return result
        
    except Exception as e:
        logger.error(f"获取轨迹列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取轨迹列表失败: {str(e)}")


@router.get("/{trajectory_id}", response_model=TrajectoryResponse)
async def get_trajectory(
    trajectory_id: int,
    db: Session = Depends(get_db)
):
    """
    获取轨迹详情
    
    Args:
        trajectory_id: 轨迹ID
        db: 数据库会话
        
    Returns:
        TrajectoryResponse: 轨迹详情
    """
    try:
        trajectory_service = TrajectoryService(db)
        trajectory = trajectory_service.get_trajectory(trajectory_id)
        
        if not trajectory:
            raise HTTPException(status_code=404, detail="轨迹不存在")
        
        return trajectory
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取轨迹详情失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取轨迹详情失败: {str(e)}")


@router.delete("/{trajectory_id}", response_model=TrajectoryDeleteResponse)
async def delete_trajectory(
    trajectory_id: int,
    db: Session = Depends(get_db)
):
    """
    删除轨迹
    
    Args:
        trajectory_id: 轨迹ID
        db: 数据库会话
        
    Returns:
        TrajectoryDeleteResponse: 删除结果
    """
    try:
        trajectory_service = TrajectoryService(db)
        success = trajectory_service.delete_trajectory(trajectory_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="轨迹不存在")
        
        from datetime import datetime
        return TrajectoryDeleteResponse(
            trajectory_id=str(trajectory_id),
            deleted_at=datetime.utcnow()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除轨迹失败: {e}")
        raise HTTPException(status_code=500, detail=f"删除轨迹失败: {str(e)}")


@router.get("/{trajectory_id}/points")
async def get_trajectory_points(
    trajectory_id: int,
    limit: int = Query(1000, ge=1, le=10000, description="限制数量"),
    offset: int = Query(0, ge=0, description="偏移量"),
    db: Session = Depends(get_db)
):
    """
    获取轨迹点列表
    
    Args:
        trajectory_id: 轨迹ID
        limit: 限制数量
        offset: 偏移量
        db: 数据库会话
        
    Returns:
        List[Dict]: 轨迹点列表
    """
    try:
        trajectory_service = TrajectoryService(db)
        points = trajectory_service.get_trajectory_points(trajectory_id, limit, offset)
        
        return {
            "success": True,
            "data": {
                "trajectory_id": trajectory_id,
                "points": points,
                "total": len(points)
            }
        }
        
    except Exception as e:
        logger.error(f"获取轨迹点失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取轨迹点失败: {str(e)}")


@router.get("/{trajectory_id}/statistics")
async def get_trajectory_statistics(
    trajectory_id: int,
    db: Session = Depends(get_db)
):
    """
    获取轨迹统计信息
    
    Args:
        trajectory_id: 轨迹ID
        db: 数据库会话
        
    Returns:
        Dict: 统计信息
    """
    try:
        trajectory_service = TrajectoryService(db)
        statistics = trajectory_service.get_trajectory_statistics(trajectory_id)
        
        if not statistics:
            raise HTTPException(status_code=404, detail="轨迹不存在")
        
        return {
            "success": True,
            "data": statistics
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取轨迹统计信息失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取轨迹统计信息失败: {str(e)}")