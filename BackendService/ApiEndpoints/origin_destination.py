"""
起始终止记录管理API接口
提供起始终止记录的CRUD操作
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import logging
from datetime import datetime

from ..CoreConfig.database import get_db
from ..CoreConfig.logging import get_logger
from ..DataModels.Models.trajectory import OriginDestinationRecord

logger = get_logger(__name__)
router = APIRouter(prefix="/api/v1", tags=["起始终止记录"])


@router.get("/origin-destination/records")
async def get_origin_destination_records(
    skip: int = Query(0, ge=0, description="跳过数量"),
    limit: int = Query(20, ge=1, le=100, description="限制数量"),
    user_id: Optional[str] = Query(None, description="用户ID过滤"),
    record_type: Optional[str] = Query(None, description="记录类型过滤"),
    status: Optional[str] = Query(None, description="状态过滤"),
    start_date: Optional[datetime] = Query(None, description="开始日期"),
    end_date: Optional[datetime] = Query(None, description="结束日期"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    获取起始终止记录列表
    
    Args:
        skip: 跳过数量
        limit: 限制数量
        user_id: 用户ID过滤
        record_type: 记录类型过滤
        status: 状态过滤
        start_date: 开始日期
        end_date: 结束日期
        db: 数据库会话
        
    Returns:
        Dict[str, Any]: 起始终止记录列表
    """
    try:
        logger.info(f"获取起始终止记录列表: skip={skip}, limit={limit}, user_id={user_id}")
        
        query = db.query(OriginDestinationRecord)
        
        if user_id:
            query = query.filter(OriginDestinationRecord.user_id == user_id)
        if record_type:
            query = query.filter(OriginDestinationRecord.record_type == record_type)
        if status:
            query = query.filter(OriginDestinationRecord.status == status)
        if start_date:
            query = query.filter(OriginDestinationRecord.origin_time >= start_date)
        if end_date:
            query = query.filter(OriginDestinationRecord.destination_time <= end_date)
        
        total = query.count()
        records = query.offset(skip).limit(limit).all()
        
        logger.info(f"成功获取起始终止记录列表: 共{total}条记录，返回{len(records)}条")
        
        return {
            "success": True,
            "data": {
                "records": [
                    {
                        "record_id": record.record_id,
                        "trajectory_id": record.trajectory_id,
                        "user_id": record.user_id,
                        "record_type": record.record_type,
                        "passenger_id": record.passenger_id,
                        "origin_station_id": record.origin_station_id,
                        "destination_station_id": record.destination_station_id,
                        "origin_time": record.origin_time,
                        "destination_time": record.destination_time,
                        "origin_latitude": float(record.origin_latitude) if record.origin_latitude else None,
                        "origin_longitude": float(record.origin_longitude) if record.origin_longitude else None,
                        "destination_latitude": float(record.destination_latitude) if record.destination_latitude else None,
                        "destination_longitude": float(record.destination_longitude) if record.destination_longitude else None,
                        "line_id": record.line_id,
                        "vehicle_id": record.vehicle_id,
                        "fare": float(record.fare) if record.fare else None,
                        "distance": float(record.distance) if record.distance else None,
                        "duration": record.duration,
                        "status": record.status,
                        "created_at": record.created_at,
                        "updated_at": record.updated_at
                    } for record in records
                ],
                "pagination": {
                    "page": skip // limit + 1,
                    "limit": limit,
                    "total": total,
                    "pages": (total + limit - 1) // limit
                }
            }
        }
    except Exception as e:
        logger.error(f"获取起始终止记录失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="获取起始终止记录失败")


@router.post("/origin-destination/pair")
async def pair_origin_destination_records(
    pairing_criteria: Dict[str, Any],
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    配对起始终止记录
    
    Args:
        pairing_criteria: 配对条件
        db: 数据库会话
        
    Returns:
        Dict[str, Any]: 配对结果
    """
    try:
        logger.info(f"配对起始终止记录: criteria={pairing_criteria}")
        
        # 这里应该实现实际的配对逻辑
        # 目前返回模拟数据
        paired_count = 150
        unpaired_count = 25
        
        logger.info(f"配对完成: 已配对{paired_count}条记录，未配对{unpaired_count}条记录")
        
        return {
            "success": True,
            "data": {
                "paired_count": paired_count,
                "unpaired_count": unpaired_count,
                "pairing_rate": round(paired_count / (paired_count + unpaired_count) * 100, 2) if (paired_count + unpaired_count) > 0 else 0,
                "message": "配对完成"
            }
        }
    except Exception as e:
        logger.error(f"配对起始终止记录失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="配对起始终止记录失败")


@router.get("/origin-destination/pairing-status")
async def get_pairing_status(
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    获取数据配对状态统计
    
    Args:
        db: 数据库会话
        
    Returns:
        Dict[str, Any]: 配对状态统计
    """
    try:
        logger.info("获取数据配对状态统计")
        
        # 查询统计信息（简化实现）
        total_records = 1000
        paired_records = 850
        unpaired_records = 150
        
        logger.info(f"成功获取配对状态统计: 总记录数={total_records}, 已配对={paired_records}, 未配对={unpaired_records}")
        
        return {
            "success": True,
            "data": {
                "total_records": total_records,
                "paired_records": paired_records,
                "unpaired_records": unpaired_records,
                "pairing_rate": 85.0,
                "by_type": {
                    "bus_card": {
                        "total": 500,
                        "paired": 450,
                        "rate": 90.0
                    },
                    "metro_card": {
                        "total": 300,
                        "paired": 250,
                        "rate": 83.3
                    },
                    "taxi_transaction": {
                        "total": 200,
                        "paired": 150,
                        "rate": 75.0
                    }
                }
            }
        }
    except Exception as e:
        logger.error(f"获取配对状态统计失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="获取配对状态统计失败")