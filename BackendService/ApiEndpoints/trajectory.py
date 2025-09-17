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
            
            logger.info(f"轨迹上传成功: ID={trajectory.id}, 文件名={file.filename}, 点数={len(points)}")
            
            return TrajectoryUploadResponse(
                success=True,
                data={
                    "trajectory_id": str(trajectory.id),
                    "filename": file.filename,
                    "file_size": file_size,
                    "point_count": len(points),
                    "upload_time": datetime.utcnow()
                },
                message="文件上传成功"
            )
            
        except Exception as e:
            # 如果解析或创建轨迹失败，删除已保存的文件
            try:
                file_path.unlink()
            except:
                pass
            raise e
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"上传轨迹文件失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"上传轨迹文件失败: {str(e)}")


@router.get("", response_model=TrajectoryListResponse)
async def get_trajectories(
    skip: int = Query(0, ge=0, description="跳过数量"),
    limit: int = Query(20, ge=1, le=100, description="每页数量"),
    status: Optional[str] = Query(None, description="轨迹状态"),
    start_date: Optional[datetime] = Query(None, description="开始日期"),
    end_date: Optional[datetime] = Query(None, description="结束日期"),
    db: Session = Depends(get_db)
):
    """
    获取轨迹列表
    
    Args:
        skip: 跳过数量
        limit: 每页数量
        status: 轨迹状态
        start_date: 开始日期
        end_date: 结束日期
        db: 数据库会话
        
    Returns:
        TrajectoryListResponse: 轨迹列表
    """
    try:
        logger.info(f"获取轨迹列表: skip={skip}, limit={limit}, status={status}")
        
        query = db.query(Trajectory).filter(Trajectory.is_deleted == False)
        
        if status:
            query = query.filter(Trajectory.status == status)
        
        if start_date:
            query = query.filter(Trajectory.created_at >= start_date)
            
        if end_date:
            query = query.filter(Trajectory.created_at <= end_date)
        
        total = query.count()
        trajectories = query.offset(skip).limit(limit).all()
        
        logger.info(f"成功获取轨迹列表: 共{total}条记录，返回{len(trajectories)}条")
        
        return TrajectoryListResponse(
            success=True,
            data={
                "trajectories": trajectories,
                "pagination": {
                    "page": skip // limit + 1,
                    "limit": limit,
                    "total": total,
                    "pages": (total + limit - 1) // limit
                }
            }
        )
        
    except Exception as e:
        logger.error(f"获取轨迹列表失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取轨迹列表失败: {str(e)}")


@router.get("/{trajectory_id}", response_model=TrajectoryResponse)
async def get_trajectory(
    trajectory_id: int,
    db: Session = Depends(get_db)
):
    """
    获取指定轨迹详情
    
    Args:
        trajectory_id: 轨迹ID
        db: 数据库会话
        
    Returns:
        TrajectoryResponse: 轨迹详情
    """
    try:
        logger.info(f"获取轨迹详情: trajectory_id={trajectory_id}")
        
        trajectory = db.query(Trajectory).filter(
            Trajectory.id == trajectory_id,
            Trajectory.is_deleted == False
        ).first()
        
        if not trajectory:
            logger.warning(f"轨迹不存在: trajectory_id={trajectory_id}")
            raise HTTPException(status_code=404, detail="轨迹不存在")
        
        logger.info(f"成功获取轨迹详情: trajectory_id={trajectory_id}")
        
        return TrajectoryResponse(
            success=True,
            data=trajectory
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取轨迹详情失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取轨迹详情失败: {str(e)}")


@router.delete("/{trajectory_id}", response_model=TrajectoryDeleteResponse)
async def delete_trajectory(
    trajectory_id: int,
    db: Session = Depends(get_db)
):
    """
    删除指定轨迹
    
    Args:
        trajectory_id: 轨迹ID
        db: 数据库会话
        
    Returns:
        TrajectoryDeleteResponse: 删除结果
    """
    try:
        logger.info(f"删除轨迹: trajectory_id={trajectory_id}")
        
        trajectory = db.query(Trajectory).filter(
            Trajectory.id == trajectory_id,
            Trajectory.is_deleted == False
        ).first()
        
        if not trajectory:
            logger.warning(f"轨迹不存在: trajectory_id={trajectory_id}")
            raise HTTPException(status_code=404, detail="轨迹不存在")
        
        # 标记为已删除
        trajectory.is_deleted = True
        db.commit()
        
        logger.info(f"成功删除轨迹: trajectory_id={trajectory_id}")
        
        return TrajectoryDeleteResponse(
            success=True,
            data={
                "trajectory_id": str(trajectory_id),
                "deleted_at": datetime.utcnow()
            },
            message="轨迹删除成功"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除轨迹失败: {e}", exc_info=True)
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