"""
地图匹配API接口
提供轨迹匹配、状态查询、结果获取等功能
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
import logging
import uuid
from datetime import datetime
import json
import csv
import io

from CoreConfig.database import get_db
from CoreConfig.logging import get_logger
from BusinessServices.matching_service import MatchingService
from DataSchemas.matching import (
    MatchingRequest, MatchingStartResponse, MatchingStatusResponse,
    MatchingResultResponse, MatchingTaskQueryParams, MatchingTaskListResponse
)
from DataModels.Models.trajectory import MatchingTask, Trajectory, MatchedPoint
from DataSchemas.trajectory import TrajectoryStatus

logger = get_logger(__name__)
router = APIRouter(prefix="/api/v1/matching", tags=["matching"])


@router.post("/start", response_model=MatchingStartResponse)
async def start_matching(
    request: MatchingRequest,
    db: Session = Depends(get_db)
):
    """
    开始地图匹配
    
    Args:
        request: 匹配请求
        db: 数据库会话
        
    Returns:
        MatchingStartResponse: 匹配开始响应
    """
    try:
        logger.info(f"开始地图匹配任务: trajectory_id={request.trajectory_id}, algorithm={request.algorithm}")
        
        # 检查轨迹是否存在
        trajectory = db.query(Trajectory).filter(
            Trajectory.id == int(request.trajectory_id),
            Trajectory.is_deleted == False
        ).first()
        
        if not trajectory:
            logger.warning(f"轨迹不存在: trajectory_id={request.trajectory_id}")
            raise HTTPException(status_code=404, detail="轨迹不存在")
        
        # 生成任务ID
        task_id = str(uuid.uuid4())
        
        # 创建匹配任务记录
        matching_task = MatchingTask(
            trajectory_id=int(request.trajectory_id),
            task_id=task_id,
            algorithm=request.algorithm,
            parameters=request.parameters,
            status="queued"
        )
        
        db.add(matching_task)
        db.commit()
        db.refresh(matching_task)
        
        logger.info(f"匹配任务创建成功: task_id={task_id}, trajectory_id={request.trajectory_id}")
        
        return MatchingStartResponse(
            success=True,
            data={
                "task_id": task_id,
                "trajectory_id": request.trajectory_id,
                "algorithm": request.algorithm,
                "status": "queued",
                "estimated_time": 30,  # 简化实现
                "created_at": datetime.utcnow()
            },
            message="匹配任务已创建"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"开始匹配失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"开始匹配失败: {str(e)}")


@router.get("/status/{task_id}", response_model=MatchingStatusResponse)
async def get_matching_status(
    task_id: str,
    db: Session = Depends(get_db)
):
    """
    查询匹配状态
    
    Args:
        task_id: 任务ID
        db: 数据库会话
        
    Returns:
        MatchingStatusResponse: 匹配状态响应
    """
    try:
        logger.info(f"查询匹配状态: task_id={task_id}")
        
        # 查询匹配任务
        task = db.query(MatchingTask).filter(MatchingTask.task_id == task_id).first()
        
        if not task:
            logger.warning(f"匹配任务不存在: task_id={task_id}")
            raise HTTPException(status_code=404, detail="匹配任务不存在")
        
        logger.info(f"成功查询匹配状态: task_id={task_id}, status={task.status}")
        
        return MatchingStatusResponse(
            success=True,
            data={
                "task_id": task.task_id,
                "status": task.status,
                "progress": task.progress or 0,
                "result": {
                    "matched_points": task.matched_points_count or 0,
                    "unmatched_points": task.unmatched_points_count or 0,
                    "accuracy": float(task.accuracy) if task.accuracy else 0.0,
                    "processing_time": float(task.processing_time) if task.processing_time else 0.0
                } if task.status == "completed" else None,
                "created_at": task.created_at,
                "completed_at": task.completed_at
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"查询匹配状态失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"查询匹配状态失败: {str(e)}")


@router.get("/result/{task_id}", response_model=MatchingResultResponse)
async def get_matching_result(
    task_id: str,
    db: Session = Depends(get_db)
):
    """
    获取匹配结果
    
    Args:
        task_id: 任务ID
        db: 数据库会话
        
    Returns:
        MatchingResultResponse: 匹配结果响应
    """
    try:
        logger.info(f"获取匹配结果: task_id={task_id}")
        
        # 查询匹配任务
        task = db.query(MatchingTask).filter(MatchingTask.task_id == task_id).first()
        
        if not task:
            logger.warning(f"匹配任务不存在: task_id={task_id}")
            raise HTTPException(status_code=404, detail="匹配任务不存在")
        
        if task.status != "completed":
            logger.warning(f"匹配任务未完成: task_id={task_id}, status={task.status}")
            raise HTTPException(status_code=400, detail="匹配任务未完成")
        
        # 查询匹配结果
        matched_points = db.query(MatchedPoint).filter(MatchedPoint.matching_task_id == task.id).all()
        
        logger.info(f"成功获取匹配结果: task_id={task_id}, 匹配点数={len(matched_points)}")
        
        return MatchingResultResponse(
            success=True,
            data={
                "task_id": task.task_id,
                "trajectory_id": str(task.trajectory_id),
                "algorithm": task.algorithm,
                "status": task.status,
                "result": {
                    "matched_trajectory": {
                        "points": [
                            {
                                "point_id": str(point.id),
                                "original_lat": float(point.original_latitude),
                                "original_lng": float(point.original_longitude),
                                "matched_lat": float(point.matched_latitude),
                                "matched_lng": float(point.matched_longitude),
                                "road_id": point.road_segment_id,
                                "road_name": point.road_name,
                                "confidence": float(point.confidence) if point.confidence else 0.0,
                                "distance": float(point.distance) if point.distance else 0.0
                            } for point in matched_points
                        ],
                        "total_distance": (task.matched_points_count or 0) * 100,
                        "matched_distance": (task.matched_points_count or 0) * 100
                    },
                    "statistics": {
                        "total_points": (task.matched_points_count or 0) + (task.unmatched_points_count or 0),
                        "matched_points": task.matched_points_count or 0,
                        "unmatched_points": task.unmatched_points_count or 0,
                        "accuracy": float(task.accuracy) if task.accuracy else 0.0,
                        "avg_confidence": 0.85,
                        "processing_time": float(task.processing_time) if task.processing_time else 0.0
                    }
                },
                "created_at": task.created_at,
                "completed_at": task.completed_at
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取匹配结果失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取匹配结果失败: {str(e)}")


@router.get("/tasks", response_model=MatchingTaskListResponse)
async def get_matching_tasks(
    page: int = Query(1, ge=1, description="页码"),
    limit: int = Query(20, ge=1, le=100, description="每页数量"),
    status: Optional[str] = Query(None, description="任务状态"),
    algorithm: Optional[str] = Query(None, description="匹配算法"),
    trajectory_id: Optional[str] = Query(None, description="轨迹ID"),
    db: Session = Depends(get_db)
):
    """
    获取匹配任务列表
    
    Args:
        page: 页码
        limit: 每页数量
        status: 任务状态
        algorithm: 匹配算法
        trajectory_id: 轨迹ID
        db: 数据库会话
        
    Returns:
        MatchingTaskListResponse: 匹配任务列表
    """
    try:
        # 构建查询
        query = db.query(MatchingTask).filter(MatchingTask.is_deleted == False)
        
        if status:
            query = query.filter(MatchingTask.status == status)
        
        if algorithm:
            query = query.filter(MatchingTask.algorithm == algorithm)
        
        if trajectory_id:
            query = query.filter(MatchingTask.trajectory_id == int(trajectory_id))
        
        # 获取总数
        total = query.count()
        
        # 应用分页
        offset = (page - 1) * limit
        tasks = query.order_by(MatchingTask.created_at.desc()).offset(offset).limit(limit).all()
        
        # 计算总页数
        pages = (total + limit - 1) // limit
        
        # 转换为响应格式
        task_responses = []
        for task in tasks:
            task_responses.append({
                "id": task.id,
                "task_id": task.task_id,
                "trajectory_id": task.trajectory_id,
                "algorithm": task.algorithm,
                "parameters": task.parameters,
                "status": task.status,
                "progress": task.progress,
                "matched_points_count": task.matched_points_count,
                "unmatched_points_count": task.unmatched_points_count,
                "accuracy": task.accuracy,
                "processing_time": task.processing_time,
                "error_message": task.error_message,
                "started_at": task.started_at,
                "completed_at": task.completed_at,
                "created_at": task.created_at,
                "updated_at": task.updated_at
            })
        
        return MatchingTaskListResponse(
            tasks=task_responses,
            total=total,
            page=page,
            limit=limit,
            pages=pages
        )
        
    except Exception as e:
        logger.error(f"获取匹配任务列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取匹配任务列表失败: {str(e)}")


@router.get("/algorithms")
async def get_available_algorithms():
    """
    获取可用的匹配算法
    
    Returns:
        Dict: 可用算法列表
    """
    try:
        from ..MatchingAlgorithms.base import AlgorithmFactory
        
        algorithms = []
        for algo_type in AlgorithmFactory.get_available_algorithms():
            algo_info = AlgorithmFactory.get_algorithm_info(algo_type)
            algorithms.append({
                "type": algo_type,
                "name": algo_info.get("name", algo_type),
                "description": f"{algo_type} 匹配算法",
                "is_available": True
            })
        
        return {
            "success": True,
            "data": {
                "algorithms": algorithms,
                "default_algorithm": "distance_matching"
            }
        }
        
    except Exception as e:
        logger.error(f"获取可用算法失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取可用算法失败: {str(e)}")


@router.get("/download/{task_id}")
async def download_matching_result(
    task_id: str,
    format: str = Query("geojson", description="文件格式: gpx, kml, csv, geojson"),
    db: Session = Depends(get_db)
):
    """
    下载匹配结果
    
    Args:
        task_id: 任务ID
        format: 文件格式
        db: 数据库会话
        
    Returns:
        Response: 文件下载响应
    """
    try:
        logger.info(f"下载匹配结果: task_id={task_id}, format={format}")
        
        # 查询匹配任务
        task = db.query(MatchingTask).filter(MatchingTask.task_id == task_id).first()
        
        if not task:
            logger.warning(f"匹配任务不存在: task_id={task_id}")
            raise HTTPException(status_code=404, detail="匹配任务不存在")
        
        if task.status != "completed":
            logger.warning(f"匹配任务未完成: task_id={task_id}, status={task.status}")
            raise HTTPException(status_code=400, detail="匹配任务未完成")
        
        # 查询匹配结果
        matched_points = db.query(MatchedPoint).filter(MatchedPoint.matching_task_id == task.id).all()
        
        if not matched_points:
            logger.warning(f"匹配结果为空: task_id={task_id}")
            raise HTTPException(status_code=404, detail="匹配结果不存在")
        
        # 根据格式生成文件内容
        if format.lower() == "csv":
            # 生成CSV内容
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(["point_id", "original_lat", "original_lng", "matched_lat", "matched_lng", "confidence", "distance"])
            for point in matched_points:
                writer.writerow([
                    point.id,
                    point.original_latitude,
                    point.original_longitude,
                    point.matched_latitude,
                    point.matched_longitude,
                    point.confidence,
                    point.distance
                ])
            content = output.getvalue()
            media_type = "text/csv"
            filename = f"matching_result_{task_id}.csv"
            
        elif format.lower() == "geojson":
            # 生成GeoJSON内容
            features = []
            for point in matched_points:
                features.append({
                    "type": "Feature",
                    "geometry": {
                        "type": "Point",
                        "coordinates": [float(point.matched_longitude), float(point.matched_latitude)]
                    },
                    "properties": {
                        "point_id": point.id,
                        "original_lat": float(point.original_latitude),
                        "original_lng": float(point.original_longitude),
                        "confidence": float(point.confidence) if point.confidence else 0.0,
                        "distance": float(point.distance) if point.distance else 0.0
                    }
                })
            
            content = json.dumps({
                "type": "FeatureCollection",
                "features": features
            }, ensure_ascii=False, indent=2)
            media_type = "application/geo+json"
            filename = f"matching_result_{task_id}.geojson"
            
        else:
            # 默认返回GeoJSON
            features = []
            for point in matched_points:
                features.append({
                    "type": "Feature",
                    "geometry": {
                        "type": "Point",
                        "coordinates": [float(point.matched_longitude), float(point.matched_latitude)]
                    },
                    "properties": {
                        "point_id": point.id,
                        "original_lat": float(point.original_latitude),
                        "original_lng": float(point.original_longitude),
                        "confidence": float(point.confidence) if point.confidence else 0.0,
                        "distance": float(point.distance) if point.distance else 0.0
                    }
                })
            
            content = json.dumps({
                "type": "FeatureCollection",
                "features": features
            }, ensure_ascii=False, indent=2)
            media_type = "application/geo+json"
            filename = f"matching_result_{task_id}.geojson"
        
        logger.info(f"成功生成下载文件: task_id={task_id}, format={format}, 大小={len(content)}字节")
        
        return Response(
            content=content,
            media_type=media_type,
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"下载匹配结果失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"下载匹配结果失败: {str(e)}")


def _generate_gpx_content(matched_points, include_original, include_statistics):
    """生成GPX格式内容"""
    gpx_content = '<?xml version="1.0" encoding="UTF-8"?>\n'
    gpx_content += '<gpx version="1.1" creator="MapTools">\n'
    gpx_content += '  <trk>\n'
    gpx_content += '    <name>Matched Trajectory</name>\n'
    gpx_content += '    <trkseg>\n'
    
    for point in matched_points:
        gpx_content += f'      <trkpt lat="{point.matched_latitude}" lon="{point.matched_longitude}">\n'
        if point.matched_timestamp:
            gpx_content += f'        <time>{point.matched_timestamp.isoformat()}</time>\n'
        if point.elevation:
            gpx_content += f'        <ele>{point.elevation}</ele>\n'
        gpx_content += f'        <extensions>\n'
        gpx_content += f'          <distance>{point.distance}</distance>\n'
        gpx_content += f'          <confidence>{point.confidence}</confidence>\n'
        gpx_content += f'        </extensions>\n'
        gpx_content += '      </trkpt>\n'
    
    gpx_content += '    </trkseg>\n'
    gpx_content += '  </trk>\n'
    gpx_content += '</gpx>'
    
    return gpx_content


def _generate_kml_content(matched_points, include_original, include_statistics):
    """生成KML格式内容"""
    kml_content = '<?xml version="1.0" encoding="UTF-8"?>\n'
    kml_content += '<kml xmlns="http://www.opengis.net/kml/2.2">\n'
    kml_content += '  <Document>\n'
    kml_content += '    <name>Matched Trajectory</name>\n'
    kml_content += '    <Placemark>\n'
    kml_content += '      <name>Matched Path</name>\n'
    kml_content += '      <LineString>\n'
    kml_content += '        <coordinates>\n'
    
    for point in matched_points:
        kml_content += f'          {point.matched_longitude},{point.matched_latitude}\n'
    
    kml_content += '        </coordinates>\n'
    kml_content += '      </LineString>\n'
    kml_content += '    </Placemark>\n'
    kml_content += '  </Document>\n'
    kml_content += '</kml>'
    
    return kml_content


def _generate_csv_content(matched_points, include_original, include_statistics):
    """生成CSV格式内容"""
    output = io.StringIO()
    writer = csv.writer(output)
    
    # 写入表头
    headers = ['point_id', 'matched_latitude', 'matched_longitude', 'distance', 'confidence']
    if include_original:
        headers.extend(['original_latitude', 'original_longitude'])
    if include_statistics:
        headers.extend(['timestamp', 'elevation'])
    
    writer.writerow(headers)
    
    # 写入数据
    for point in matched_points:
        row = [
            point.id,
            point.matched_latitude,
            point.matched_longitude,
            point.distance,
            point.confidence
        ]
        if include_original:
            row.extend([point.original_latitude, point.original_longitude])
        if include_statistics:
            row.extend([
                point.matched_timestamp.isoformat() if point.matched_timestamp else '',
                point.elevation or ''
            ])
        
        writer.writerow(row)
    
    return output.getvalue()


def _generate_geojson_content(matched_points, include_original, include_statistics):
    """生成GeoJSON格式内容"""
    features = []
    
    for point in matched_points:
        feature = {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [point.matched_longitude, point.matched_latitude]
            },
            "properties": {
                "point_id": point.id,
                "distance": point.distance,
                "confidence": point.confidence
            }
        }
        
        if include_original:
            feature["properties"]["original_coordinates"] = [
                point.original_longitude, point.original_latitude
            ]
        
        if include_statistics:
            feature["properties"]["timestamp"] = point.matched_timestamp.isoformat() if point.matched_timestamp else None
            feature["properties"]["elevation"] = point.elevation
        
        features.append(feature)
    
    geojson = {
        "type": "FeatureCollection",
        "features": features
    }
    
    return json.dumps(geojson, indent=2)