"""
路网管理API接口
提供路网数据的CRUD操作
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import logging

from ..CoreConfig.database import get_db
from ..CoreConfig.logging import get_logger
from ..DataModels.Models.trajectory import RoadNetwork, RoadSegment
from ..DataSchemas.trajectory import (
    RoadNetworkCreate, RoadNetworkResponse, 
    RoadSegmentCreate, RoadSegmentResponse
)

logger = get_logger(__name__)
router = APIRouter()


@router.get("/roadnetworks", response_model=List[RoadNetworkResponse])
async def get_road_networks(
    skip: int = Query(0, ge=0, description="跳过数量"),
    limit: int = Query(100, ge=1, le=1000, description="限制数量"),
    active_only: bool = Query(True, description="仅显示激活的路网"),
    db: Session = Depends(get_db)
) -> List[RoadNetworkResponse]:
    """
    获取路网列表
    
    Args:
        skip: 跳过数量
        limit: 限制数量
        active_only: 仅显示激活的路网
        db: 数据库会话
        
    Returns:
        List[RoadNetworkResponse]: 路网列表
    """
    try:
        query = db.query(RoadNetwork)
        if active_only:
            query = query.filter(RoadNetwork.is_active == True)
        
        road_networks = query.offset(skip).limit(limit).all()
        
        return road_networks
    except Exception as e:
        logger.error(f"获取路网列表失败: {e}")
        raise HTTPException(status_code=500, detail="获取路网列表失败")


@router.get("/roadnetworks/{network_id}", response_model=RoadNetworkResponse)
async def get_road_network(
    network_id: str,
    db: Session = Depends(get_db)
) -> RoadNetworkResponse:
    """
    获取指定路网详情
    
    Args:
        network_id: 路网ID
        db: 数据库会话
        
    Returns:
        RoadNetworkResponse: 路网详情
    """
    try:
        road_network = db.query(RoadNetwork).filter(
            RoadNetwork.network_id == network_id
        ).first()
        
        if not road_network:
            raise HTTPException(status_code=404, detail="路网不存在")
        
        return road_network
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取路网详情失败: {e}")
        raise HTTPException(status_code=500, detail="获取路网详情失败")


@router.get("/roadnetworks/{network_id}/stats")
async def get_road_network_stats(
    network_id: str,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    获取路网统计信息
    
    Args:
        network_id: 路网ID
        db: 数据库会话
        
    Returns:
        Dict[str, Any]: 路网统计信息
    """
    try:
        road_network = db.query(RoadNetwork).filter(
            RoadNetwork.network_id == network_id
        ).first()
        
        if not road_network:
            raise HTTPException(status_code=404, detail="路网不存在")
        
        # 获取道路段统计
        segments = db.query(RoadSegment).filter(
            RoadSegment.network_id == network_id
        ).all()
        
        total_segments = len(segments)
        total_length = sum(segment.length or 0 for segment in segments)
        
        # 按道路类型统计
        road_types = {}
        for segment in segments:
            road_type = segment.road_type or "unknown"
            road_types[road_type] = road_types.get(road_type, 0) + 1
        
        return {
            "success": True,
            "data": {
                "network_id": network_id,
                "name": road_network.name,
                "total_segments": total_segments,
                "total_length": total_length,
                "coverage_area": road_network.coverage_area,
                "road_types": road_types,
                "bounds": {
                    "min_lat": road_network.bounds_min_lat,
                    "max_lat": road_network.bounds_max_lat,
                    "min_lng": road_network.bounds_min_lng,
                    "max_lng": road_network.bounds_max_lng
                } if road_network.bounds_min_lat else None
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取路网统计失败: {e}")
        raise HTTPException(status_code=500, detail="获取路网统计失败")


@router.post("/roadnetworks", response_model=RoadNetworkResponse)
async def create_road_network(
    road_network: RoadNetworkCreate,
    db: Session = Depends(get_db)
) -> RoadNetworkResponse:
    """
    创建新路网
    
    Args:
        road_network: 路网创建数据
        db: 数据库会话
        
    Returns:
        RoadNetworkResponse: 创建的路网
    """
    try:
        # 检查路网ID是否已存在
        existing = db.query(RoadNetwork).filter(
            RoadNetwork.network_id == road_network.network_id
        ).first()
        
        if existing:
            raise HTTPException(status_code=400, detail="路网ID已存在")
        
        # 创建新路网
        db_road_network = RoadNetwork(**road_network.dict())
        db.add(db_road_network)
        db.commit()
        db.refresh(db_road_network)
        
        return db_road_network
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建路网失败: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="创建路网失败")


@router.get("/roadnetworks/{network_id}/segments", response_model=List[RoadSegmentResponse])
async def get_road_segments(
    network_id: str,
    skip: int = Query(0, ge=0, description="跳过数量"),
    limit: int = Query(100, ge=1, le=1000, description="限制数量"),
    road_type: Optional[str] = Query(None, description="道路类型过滤"),
    db: Session = Depends(get_db)
) -> List[RoadSegmentResponse]:
    """
    获取路网的道路段列表
    
    Args:
        network_id: 路网ID
        skip: 跳过数量
        limit: 限制数量
        road_type: 道路类型过滤
        db: 数据库会话
        
    Returns:
        List[RoadSegmentResponse]: 道路段列表
    """
    try:
        query = db.query(RoadSegment).filter(
            RoadSegment.network_id == network_id
        )
        
        if road_type:
            query = query.filter(RoadSegment.road_type == road_type)
        
        segments = query.offset(skip).limit(limit).all()
        
        return segments
    except Exception as e:
        logger.error(f"获取道路段列表失败: {e}")
        raise HTTPException(status_code=500, detail="获取道路段列表失败")


@router.post("/roadnetworks/{network_id}/segments", response_model=RoadSegmentResponse)
async def create_road_segment(
    network_id: str,
    segment: RoadSegmentCreate,
    db: Session = Depends(get_db)
) -> RoadSegmentResponse:
    """
    为路网添加道路段
    
    Args:
        network_id: 路网ID
        segment: 道路段创建数据
        db: 数据库会话
        
    Returns:
        RoadSegmentResponse: 创建的道路段
    """
    try:
        # 检查路网是否存在
        road_network = db.query(RoadNetwork).filter(
            RoadNetwork.network_id == network_id
        ).first()
        
        if not road_network:
            raise HTTPException(status_code=404, detail="路网不存在")
        
        # 创建新道路段
        segment_data = segment.dict()
        segment_data['network_id'] = network_id
        
        db_segment = RoadSegment(**segment_data)
        db.add(db_segment)
        db.commit()
        db.refresh(db_segment)
        
        return db_segment
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建道路段失败: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="创建道路段失败")
