"""
地图匹配API端点
提供GPS数据解析和道路匹配功能
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any, Optional
import logging
from pydantic import BaseModel

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from UtilityTools.gps_parser import GPSDataParser
from UtilityTools.road_matching import RoadMatcher

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/matching", tags=["地图匹配"])

# 数据模型
class GPSPoint(BaseModel):
    """GPS点模型"""
    id: int
    longitude: float
    latitude: float
    plate_number: str
    datetime: str
    speed: float
    heading: float
    is_valid: bool

class MatchedPoint(BaseModel):
    """匹配后的点模型"""
    original_gps: GPSPoint
    matched_longitude: float
    matched_latitude: float
    road_id: str
    road_name: str
    road_type: str
    distance_to_road: float

class MatchingResult(BaseModel):
    """匹配结果模型"""
    total_points: int
    matched_points: int
    original_points: List[GPSPoint]
    matched_points_data: List[MatchedPoint]

class RoadNetwork(BaseModel):
    """道路网络模型"""
    roads: List[Dict[str, Any]]

# 全局实例
gps_parser = GPSDataParser()
road_matcher = RoadMatcher()

@router.get("/gps-data", response_model=List[GPSPoint])
async def get_gps_data(
    limit: Optional[int] = Query(100, description="返回的GPS点数量限制"),
    valid_only: bool = Query(True, description="是否只返回有效的GPS点")
):
    """获取GPS数据"""
    try:
        # 解析GPS数据
        gps_points = gps_parser.parse_sample_data()
        
        if not gps_points:
            raise HTTPException(status_code=404, detail="未找到GPS数据")
        
        # 过滤有效点
        if valid_only:
            gps_points = gps_parser.filter_valid_points(gps_points)
        
        # 限制数量
        if limit and limit > 0:
            gps_points = gps_points[:limit]
        
        # 转换为响应模型
        result = []
        for point in gps_points:
            result.append(GPSPoint(
                id=point['id'],
                longitude=point['longitude'],
                latitude=point['latitude'],
                plate_number=point['plate_number'],
                datetime=point['datetime'],
                speed=point['speed'],
                heading=point['heading'],
                is_valid=point['is_valid']
            ))
        
        logger.info(f"返回 {len(result)} 个GPS点")
        return result
        
    except Exception as e:
        logger.error(f"获取GPS数据失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取GPS数据失败: {str(e)}")

@router.get("/match", response_model=MatchingResult)
async def match_gps_to_roads(
    limit: Optional[int] = Query(None, description="匹配的GPS点数量限制，不设置则返回所有点"),
    valid_only: bool = Query(True, description="是否只匹配有效的GPS点")
):
    """将GPS点匹配到道路"""
    try:
        # 获取GPS数据
        gps_points = gps_parser.parse_sample_data()
        
        if not gps_points:
            raise HTTPException(status_code=404, detail="未找到GPS数据")
        
        # 过滤有效点
        if valid_only:
            gps_points = gps_parser.filter_valid_points(gps_points)
        
        # 限制数量
        if limit and limit > 0:
            gps_points = gps_points[:limit]
        
        # 进行道路匹配
        matched_points = road_matcher.match_gps_to_roads(gps_points)
        
        # 转换为响应模型
        original_points = []
        matched_points_data = []
        
        for matched_point in matched_points:
            original = matched_point['original_gps']
            original_points.append(GPSPoint(
                id=original['id'],
                longitude=original['longitude'],
                latitude=original['latitude'],
                plate_number=original['plate_number'],
                datetime=original['datetime'],
                speed=original['speed'],
                heading=original['heading'],
                is_valid=original['is_valid']
            ))
            
            matched_points_data.append(MatchedPoint(
                original_gps=original_points[-1],
                matched_longitude=matched_point['matched_longitude'],
                matched_latitude=matched_point['matched_latitude'],
                road_id=matched_point['road_id'],
                road_name=matched_point['road_name'],
                road_type=matched_point['road_type'],
                distance_to_road=matched_point['distance_to_road']
            ))
        
        result = MatchingResult(
            total_points=len(gps_points),
            matched_points=len(matched_points_data),
            original_points=original_points,
            matched_points_data=matched_points_data
        )
        
        logger.info(f"完成 {len(matched_points_data)} 个GPS点的道路匹配")
        return result
        
    except Exception as e:
        logger.error(f"道路匹配失败: {e}")
        raise HTTPException(status_code=500, detail=f"道路匹配失败: {str(e)}")

@router.get("/road-network", response_model=RoadNetwork)
async def get_road_network():
    """获取道路网络数据"""
    try:
        roads = road_matcher.roads
        return RoadNetwork(roads=roads)
        
    except Exception as e:
        logger.error(f"获取道路网络失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取道路网络失败: {str(e)}")

@router.get("/vehicles", response_model=Dict[str, List[GPSPoint]])
async def get_vehicles_data(
    limit: Optional[int] = Query(10, description="返回的车辆数量限制")
):
    """按车辆分组获取GPS数据"""
    try:
        # 解析GPS数据
        gps_points = gps_parser.parse_sample_data()
        
        if not gps_points:
            raise HTTPException(status_code=404, detail="未找到GPS数据")
        
        # 按车辆分组
        vehicles = gps_parser.group_by_vehicle(gps_points)
        
        # 限制车辆数量
        if limit and limit > 0:
            vehicles = dict(list(vehicles.items())[:limit])
        
        # 转换为响应模型
        result = {}
        for plate_number, points in vehicles.items():
            vehicle_points = []
            for point in points:
                vehicle_points.append(GPSPoint(
                    id=point['id'],
                    longitude=point['longitude'],
                    latitude=point['latitude'],
                    plate_number=point['plate_number'],
                    datetime=point['datetime'],
                    speed=point['speed'],
                    heading=point['heading'],
                    is_valid=point['is_valid']
                ))
            result[plate_number] = vehicle_points
        
        logger.info(f"返回 {len(result)} 辆车的GPS数据")
        return result
        
    except Exception as e:
        logger.error(f"获取车辆数据失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取车辆数据失败: {str(e)}")

@router.get("/matched-points")
async def get_matched_points(
    limit: Optional[int] = Query(100, description="返回的匹配点数量限制")
):
    """获取已匹配的GPS点数据"""
    try:
        # 获取GPS数据
        gps_points = gps_parser.parse_sample_data()
        
        if not gps_points:
            raise HTTPException(status_code=404, detail="未找到GPS数据")
        
        # 过滤有效点
        gps_points = gps_parser.filter_valid_points(gps_points)
        
        # 限制数量
        if limit and limit > 0:
            gps_points = gps_points[:limit]
        
        # 进行道路匹配
        matched_points = road_matcher.match_gps_to_roads(gps_points)
        
        logger.info(f"返回 {len(matched_points)} 个匹配点")
        return {
            "success": True,
            "data": {
                "matched_points": matched_points
            },
            "message": f"成功获取 {len(matched_points)} 个匹配点"
        }
        
    except Exception as e:
        logger.error(f"获取匹配点数据失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取匹配点数据失败: {str(e)}")