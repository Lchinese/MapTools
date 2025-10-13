"""
地图匹配API端点
提供GPS数据解析和道路匹配功能
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any, Optional
import logging
from pydantic import BaseModel
import requests
import json

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

class OSRMRequest(BaseModel):
    """OSRM请求模型"""
    waypoints: List[Dict[str, Any]]

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
        # 直接从修正轨迹集合获取GPS数据
        import pymongo
        client = pymongo.MongoClient('localhost', 27017)
        db = client['MapTools']
        
        gps_points = []
        for i in range(1, 31):
            collection_name = f"corrected_trajectories_{i:02d}"
            if collection_name in db.list_collection_names():
                collection = db[collection_name]
                # 获取第一个有轨迹点的文档
                doc = collection.find_one({"trajectory_points": {"$exists": True, "$ne": []}})
                if doc and doc.get("trajectory_points"):
                    trajectory_points = doc.get("trajectory_points", [])
                    # 限制数量
                    if limit and limit > 0:
                        trajectory_points = trajectory_points[:limit]
                    
                    for j, point in enumerate(trajectory_points):
                        gps_point = {
                            'id': j + 1,
                            'plate_number': doc.get('plate_number', ''),
                            'datetime': point.get('datetime', ''),
                            'longitude': float(point.get('longitude', 0)),
                            'latitude': float(point.get('latitude', 0)),
                            'speed': float(point.get('speed', 0)),
                            'heading': float(point.get('heading', 0)),
                            'is_valid': point.get('is_valid', True)
                        }
                        gps_points.append(gps_point)
                    
                    if gps_points:  # 找到数据就退出
                        break
        
        client.close()
        
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
async def get_road_network(
    limit: Optional[int] = Query(None, description="限制返回的道路数量，用于性能优化"),
    zoom_level: Optional[int] = Query(None, description="地图缩放级别，用于LOD优化")
):
    """获取道路网络数据"""
    try:
        roads = road_matcher.roads
        
        logger.info(f"道路网络API: 返回所有 {len(roads)} 条道路")
        
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

@router.post("/osrm-route")
async def get_osrm_route(request: OSRMRequest):
    """通过OSRM获取路径规划（代理接口）"""
    try:
        waypoints = request.waypoints
        
        if len(waypoints) < 2:
            raise HTTPException(status_code=400, detail="至少需要2个路径点")
        
        # 构建OSRM请求URL
        coordinates = []
        for point in waypoints:
            longitude = point.get('longitude')
            latitude = point.get('latitude')
            if longitude is not None and latitude is not None:
                coordinates.append(f"{longitude},{latitude}")
        
        if len(coordinates) < 2:
            raise HTTPException(status_code=400, detail="有效的坐标点不足")
        
        coordinates_str = ";".join(coordinates)
        # 允许通过环境变量覆盖 OSRM 基础地址，默认使用官方公共服务
        osrm_base_url = os.getenv("OSRM_BASE_URL", "http://router.project-osrm.org")
        osrm_url = f"{osrm_base_url}/route/v1/driving/{coordinates_str}?overview=full&geometries=geojson&steps=false"
        
        logger.info(f"OSRM请求URL: {osrm_url}")
        
        # 发送请求到OSRM：显式禁用系统代理，避免企业代理/本地代理干扰
        session = requests.Session()
        session.trust_env = False  # 不从环境继承 HTTP(S)_PROXY
        response = session.get(osrm_url, timeout=20, proxies={})
        
        if response.status_code != 200:
            logger.error(f"OSRM请求失败，状态码: {response.status_code}")
            raise HTTPException(status_code=500, detail=f"OSRM服务请求失败: {response.status_code}")
        
        # 解析响应
        osrm_data = response.json()
        
        logger.info(f"OSRM响应成功，返回路径数据")
        return {
            "success": True,
            "data": osrm_data,
            "message": "OSRM路径规划成功"
        }
        
    except requests.exceptions.Timeout:
        logger.error("OSRM请求超时")
        raise HTTPException(status_code=504, detail="OSRM服务请求超时")
    except requests.exceptions.RequestException as e:
        logger.error(f"OSRM请求异常: {e}")
        raise HTTPException(status_code=502, detail=f"OSRM服务连接失败: {str(e)}")
    except Exception as e:
        logger.error(f"OSRM路径规划失败: {e}")
        raise HTTPException(status_code=500, detail=f"OSRM路径规划失败: {str(e)}")