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
router = APIRouter(prefix="/api/v1", tags=["路网管理"])


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
        logger.info(f"获取路网列表: skip={skip}, limit={limit}, active_only={active_only}")
        
        query = db.query(RoadNetwork)
        if active_only:
            query = query.filter(RoadNetwork.is_active == True)
        
        road_networks = query.offset(skip).limit(limit).all()
        
        logger.info(f"成功获取路网列表: 共{len(road_networks)}条记录")
        
        return road_networks
    except Exception as e:
        logger.error(f"获取路网列表失败: {e}", exc_info=True)
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
        logger.info(f"获取路网详情: network_id={network_id}")
        
        road_network = db.query(RoadNetwork).filter(
            RoadNetwork.network_id == network_id
        ).first()
        
        if not road_network:
            logger.warning(f"路网不存在: network_id={network_id}")
            raise HTTPException(status_code=404, detail="路网不存在")
        
        logger.info(f"成功获取路网详情: network_id={network_id}")
        
        return road_network
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取路网详情失败: {e}", exc_info=True)
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
        logger.info(f"获取路网统计信息: network_id={network_id}")
        
        road_network = db.query(RoadNetwork).filter(
            RoadNetwork.network_id == network_id
        ).first()
        
        if not road_network:
            logger.warning(f"路网不存在: network_id={network_id}")
            raise HTTPException(status_code=404, detail="路网不存在")
        
        stats = {
            "network_id": road_network.network_id,
            "statistics": {
                "total_roads": road_network.total_roads or 0,
                "total_length": float(road_network.total_length) if road_network.total_length else 0.0,
                "road_types": {},  # 简化实现
                "coverage_area": 0.0  # 简化实现
            },
            "last_updated": road_network.updated_at
        }
        
        logger.info(f"成功获取路网统计信息: network_id={network_id}")
        
        return {
            "success": True,
            "data": stats
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取路网统计信息失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="获取路网统计信息失败")


@router.post("/roadnetworks", response_model=RoadNetworkResponse)
async def create_road_network(
    road_network: RoadNetworkCreate,
    db: Session = Depends(get_db)
) -> RoadNetworkResponse:
    """
    创建路网
    
    Args:
        road_network: 路网创建数据
        db: 数据库会话
        
    Returns:
        RoadNetworkResponse: 创建的路网
    """
    try:
        logger.info(f"创建路网: network_id={road_network.network_id}")
        
        # 检查路网是否已存在
        existing = db.query(RoadNetwork).filter(
            RoadNetwork.network_id == road_network.network_id
        ).first()
        
        if existing:
            logger.warning(f"路网已存在: network_id={road_network.network_id}")
            raise HTTPException(status_code=400, detail="路网已存在")
        
        # 创建路网
        db_road_network = RoadNetwork(**road_network.dict())
        db.add(db_road_network)
        db.commit()
        db.refresh(db_road_network)
        
        logger.info(f"成功创建路网: network_id={road_network.network_id}")
        
        return db_road_network
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建路网失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="创建路网失败")


@router.put("/roadnetworks/{network_id}", response_model=RoadNetworkResponse)
async def update_road_network(
    network_id: str,
    road_network: RoadNetworkCreate,
    db: Session = Depends(get_db)
) -> RoadNetworkResponse:
    """
    更新路网
    
    Args:
        network_id: 路网ID
        road_network: 路网更新数据
        db: 数据库会话
        
    Returns:
        RoadNetworkResponse: 更新的路网
    """
    try:
        logger.info(f"更新路网: network_id={network_id}")
        
        # 查询路网
        db_road_network = db.query(RoadNetwork).filter(
            RoadNetwork.network_id == network_id
        ).first()
        
        if not db_road_network:
            logger.warning(f"路网不存在: network_id={network_id}")
            raise HTTPException(status_code=404, detail="路网不存在")
        
        # 更新路网
        for key, value in road_network.dict().items():
            setattr(db_road_network, key, value)
        
        db.commit()
        db.refresh(db_road_network)
        
        logger.info(f"成功更新路网: network_id={network_id}")
        
        return db_road_network
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新路网失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="更新路网失败")


@router.delete("/roadnetworks/{network_id}")
async def delete_road_network(
    network_id: str,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    删除路网
    
    Args:
        network_id: 路网ID
        db: 数据库会话
        
    Returns:
        Dict[str, Any]: 删除结果
    """
    try:
        logger.info(f"删除路网: network_id={network_id}")
        
        # 查询路网
        db_road_network = db.query(RoadNetwork).filter(
            RoadNetwork.network_id == network_id
        ).first()
        
        if not db_road_network:
            logger.warning(f"路网不存在: network_id={network_id}")
            raise HTTPException(status_code=404, detail="路网不存在")
        
        # 删除路网
        db.delete(db_road_network)
        db.commit()
        
        logger.info(f"成功删除路网: network_id={network_id}")
        
        return {
            "success": True,
            "message": "路网删除成功"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除路网失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="删除路网失败")