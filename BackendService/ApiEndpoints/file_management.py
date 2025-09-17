"""
文件管理API接口
提供文件上传、下载、删除等操作
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query, Response
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import logging
import os
from pathlib import Path

from CoreConfig.database import get_db
from CoreConfig.logging import get_logger
from DataModels.Models.trajectory import File as FileModel
from DataSchemas.trajectory import FileResponse, FileCreate
from UtilityTools.file_utils import FileProcessor

logger = get_logger(__name__)
router = APIRouter(prefix="/api/v1", tags=["文件管理"])


@router.get("/files", response_model=List[FileResponse])
async def get_files(
    skip: int = Query(0, ge=0, description="跳过数量"),
    limit: int = Query(100, ge=1, le=1000, description="限制数量"),
    file_type: Optional[str] = Query(None, description="文件类型过滤"),
    user_id: Optional[str] = Query(None, description="用户ID过滤"),
    db: Session = Depends(get_db)
) -> List[FileResponse]:
    """
    获取文件列表
    
    Args:
        skip: 跳过数量
        limit: 限制数量
        file_type: 文件类型过滤
        user_id: 用户ID过滤
        db: 数据库会话
        
    Returns:
        List[FileResponse]: 文件列表
    """
    try:
        logger.info(f"获取文件列表: skip={skip}, limit={limit}, file_type={file_type}, user_id={user_id}")
        
        query = db.query(FileModel)
        
        if file_type:
            query = query.filter(FileModel.file_type == file_type)
        if user_id:
            query = query.filter(FileModel.user_id == user_id)
        
        files = query.offset(skip).limit(limit).all()
        
        logger.info(f"成功获取文件列表: 共{len(files)}条记录")
        
        return files
    except Exception as e:
        logger.error(f"获取文件列表失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="获取文件列表失败")


@router.get("/files/{file_id}", response_model=FileResponse)
async def get_file(
    file_id: str,
    db: Session = Depends(get_db)
) -> FileResponse:
    """
    获取指定文件详情
    
    Args:
        file_id: 文件ID
        db: 数据库会话
        
    Returns:
        FileResponse: 文件详情
    """
    try:
        logger.info(f"获取文件详情: file_id={file_id}")
        
        file_record = db.query(FileModel).filter(
            FileModel.file_id == file_id
        ).first()
        
        if not file_record:
            logger.warning(f"文件不存在: file_id={file_id}")
            raise HTTPException(status_code=404, detail="文件不存在")
        
        logger.info(f"成功获取文件详情: file_id={file_id}")
        
        return file_record
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取文件详情失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="获取文件详情失败")


@router.post("/files/upload")
async def upload_file(
    file: UploadFile = File(...),
    user_id: Optional[str] = Query(None, description="用户ID"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    上传文件
    
    Args:
        file: 上传的文件
        user_id: 用户ID
        db: 数据库会话
        
    Returns:
        Dict[str, Any]: 上传结果
    """
    try:
        logger.info(f"上传文件: filename={file.filename}, user_id={user_id}")
        
        # 读取文件内容
        file_content = await file.read()
        file_size = len(file_content)
        
        # 保存文件到磁盘
        file_processor = FileProcessor()
        file_path = file_processor.save_file(file_content, file.filename)
        
        # 创建文件记录
        file_record = FileModel(
            file_id=str(file_path.name),  # 简化实现
            user_id=user_id or "anonymous",
            filename=file.filename,
            original_filename=file.filename,
            file_path=str(file_path),
            file_size=file_size,
            file_type=file.filename.split('.')[-1].lower() if '.' in file.filename else "unknown",
            mime_type=file.content_type or "application/octet-stream",
            status="uploaded"
        )
        
        db.add(file_record)
        db.commit()
        db.refresh(file_record)
        
        logger.info(f"文件上传成功: file_id={file_record.file_id}, filename={file.filename}")
        
        return {
            "success": True,
            "data": {
                "file_id": file_record.file_id,
                "filename": file.filename,
                "file_size": file_size,
                "status": "uploaded"
            },
            "message": "文件上传成功"
        }
    except Exception as e:
        logger.error(f"文件上传失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"文件上传失败: {str(e)}")


@router.delete("/files/{file_id}")
async def delete_file(
    file_id: str,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    删除文件
    
    Args:
        file_id: 文件ID
        db: 数据库会话
        
    Returns:
        Dict[str, Any]: 删除结果
    """
    try:
        logger.info(f"删除文件: file_id={file_id}")
        
        # 查询文件记录
        file_record = db.query(FileModel).filter(
            FileModel.file_id == file_id
        ).first()
        
        if not file_record:
            logger.warning(f"文件不存在: file_id={file_id}")
            raise HTTPException(status_code=404, detail="文件不存在")
        
        # 删除磁盘文件
        try:
            file_path = Path(file_record.file_path)
            if file_path.exists():
                file_path.unlink()
        except Exception as e:
            logger.warning(f"删除磁盘文件失败: {e}")
        
        # 删除数据库记录
        db.delete(file_record)
        db.commit()
        
        logger.info(f"文件删除成功: file_id={file_id}")
        
        return {
            "success": True,
            "data": {
                "file_id": file_id,
                "deleted_at": file_record.updated_at
            },
            "message": "文件删除成功"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除文件失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"删除文件失败: {str(e)}")


@router.get("/files/{file_id}/download")
async def download_file(
    file_id: str,
    db: Session = Depends(get_db)
):
    """
    下载文件
    
    Args:
        file_id: 文件ID
        db: 数据库会话
        
    Returns:
        Response: 文件下载响应
    """
    try:
        logger.info(f"下载文件: file_id={file_id}")
        
        # 查询文件记录
        file_record = db.query(FileModel).filter(
            FileModel.file_id == file_id
        ).first()
        
        if not file_record:
            logger.warning(f"文件不存在: file_id={file_id}")
            raise HTTPException(status_code=404, detail="文件不存在")
        
        # 检查文件是否存在
        file_path = Path(file_record.file_path)
        if not file_path.exists():
            logger.warning(f"文件不存在于磁盘: file_path={file_path}")
            raise HTTPException(status_code=404, detail="文件不存在于磁盘")
        
        # 读取文件内容
        with open(file_path, "rb") as f:
            content = f.read()
        
        logger.info(f"文件下载成功: file_id={file_id}, 大小={len(content)}字节")
        
        return Response(
            content=content,
            media_type=file_record.mime_type,
            headers={
                "Content-Disposition": f"attachment; filename={file_record.filename}"
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"文件下载失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"文件下载失败: {str(e)}")


@router.get("/datasources/supported")
async def get_supported_data_sources() -> Dict[str, Any]:
    """
    获取支持的数据源类型
    
    Returns:
        Dict[str, Any]: 支持的数据源列表
    """
    try:
        from ..DataSchemas.trajectory import DataSource
        
        data_sources = [
            {
                "type": source.value,
                "name": source.name,
                "description": _get_data_source_description(source),
                "file_extensions": _get_data_source_extensions(source)
            }
            for source in DataSource
        ]
        
        return {
            "success": True,
            "data": {
                "data_sources": data_sources,
                "total": len(data_sources)
            }
        }
    except Exception as e:
        logger.error(f"获取支持的数据源失败: {e}")
        raise HTTPException(status_code=500, detail="获取支持的数据源失败")


@router.post("/datasources/parse")
async def parse_data_file(
    file: UploadFile = File(...),
    data_source: Optional[str] = Query(None, description="数据源类型"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    解析数据文件
    
    Args:
        file: 上传的文件
        data_source: 数据源类型
        db: 数据库会话
        
    Returns:
        Dict[str, Any]: 解析结果
    """
    try:
        from ..DataSchemas.trajectory import DataSource
        from ..UtilityTools.file_utils import TrajectoryFileProcessor
        
        # 创建文件处理器
        processor = TrajectoryFileProcessor()
        
        # 保存文件
        file_content = await file.read()
        file_path = processor.save_uploaded_file(file_content, file.filename)
        
        # 解析文件
        data_source_enum = None
        if data_source:
            try:
                data_source_enum = DataSource(data_source)
            except ValueError:
                raise HTTPException(status_code=400, detail="不支持的数据源类型")
        
        points, detected_source, category = processor.parse_file(
            file_path, data_source_enum
        )
        
        return {
            "success": True,
            "data": {
                "filename": file.filename,
                "file_size": file_path.stat().st_size,
                "data_source": detected_source.value,
                "data_category": category.value,
                "point_count": len(points),
                "points": [
                    {
                        "latitude": point.latitude,
                        "longitude": point.longitude,
                        "timestamp": point.timestamp.isoformat(),
                        "elevation": point.elevation,
                        "speed": point.speed,
                        "direction": point.direction,
                        "accuracy": point.accuracy
                    }
                    for point in points[:10]  # 只返回前10个点作为预览
                ]
            },
            "message": "文件解析成功"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"文件解析失败: {e}")
        raise HTTPException(status_code=500, detail="文件解析失败")


def _get_data_source_description(source) -> str:
    """获取数据源描述"""
    descriptions = {
        "taxi_gps": "出租车GPS轨迹数据",
        "bus_card": "公交刷卡数据",
        "metro_card": "地铁刷卡数据",
        "taxi_transaction": "出租车交易数据",
        "bus_gps": "公交GPS运行数据",
        "gpx": "GPX格式轨迹数据",
        "csv": "CSV格式数据",
        "auto": "自动检测"
    }
    return descriptions.get(source.value, "未知数据源")


def _get_data_source_extensions(source) -> List[str]:
    """获取数据源支持的文件扩展名"""
    extensions = {
        "taxi_gps": [".txt", ".csv"],
        "bus_card": [".txt", ".csv"],
        "metro_card": [".txt", ".csv"],
        "taxi_transaction": [".txt", ".csv"],
        "bus_gps": [".txt", ".csv"],
        "gpx": [".gpx"],
        "csv": [".csv"],
        "auto": [".txt", ".csv", ".gpx"]
    }
    return extensions.get(source.value, [])
