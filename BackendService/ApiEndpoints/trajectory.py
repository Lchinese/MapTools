"""
轨迹数据API端点
提供从MongoDB获取轨迹数据的功能
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Dict, List, Optional
import logging

from ..UtilityTools.fetch_trajectory_data import (
    fetch_all_trajectory_data, 
    fetch_trajectory_data_by_plate,
    fetch_plate_numbers
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/trajectory", tags=["轨迹数据"])

# 创建道路匹配器实例
road_matcher = RoadMatcher()

@router.get("/batch")
async def get_batch_trajectory_data(
    limit: int = Query(50, description="车辆数量限制", ge=1, le=1000),
    match_to_roads: bool = Query(False, description="是否进行道路匹配")
):
    """
    批量获取指定数量车辆的轨迹数据
    
    Args:
        limit (int): 车辆数量限制
        match_to_roads (bool): 是否进行道路匹配
        
    Returns:
        Dict: 车辆轨迹数据
    """
    try:
        # 获取指定数量的车牌号
        plate_numbers, total, total_pages = fetch_plate_numbers(1, limit)
        
        # 获取这些车辆的轨迹数据
        batch_trajectory_data = {}
        for plate_number in plate_numbers:
            vehicle_data = fetch_trajectory_data_by_plate(plate_number)
            if vehicle_data and plate_number in vehicle_data:
                batch_trajectory_data[plate_number] = vehicle_data[plate_number]
        
        # 如果需要进行道路匹配
        if match_to_roads:
            matched_data = {}
            for plate_number, points in batch_trajectory_data.items():
                # 将轨迹点转换为道路匹配器需要的格式
                gps_points = []
                for i, point in enumerate(points):
                    gps_points.append({
                        'id': i,
                        'longitude': point['longitude'],
                        'latitude': point['latitude'],
                        'plate_number': point['plate_number'],
                        'datetime': point['datetime'],
                        'speed': point.get('speed', 0),
                        'heading': point.get('heading', 0),
                        'is_valid': point.get('is_valid', True)
                    })
                
                # 进行道路匹配
                matched_points = road_matcher.match_gps_to_roads(gps_points)
                matched_data[plate_number] = matched_points
            
            logger.info(f"成功批量获取并匹配 {len(matched_data)} 辆车的轨迹数据")
            return {
                "success": True,
                "data": matched_data,
                "message": f"成功获取并匹配 {len(matched_data)} 辆车的轨迹数据",
                "matched": True
            }
        else:
            logger.info(f"成功批量获取 {len(batch_trajectory_data)} 辆车的轨迹数据")
            return {
                "success": True,
                "data": batch_trajectory_data,
                "message": f"成功获取 {len(batch_trajectory_data)} 辆车的轨迹数据",
                "matched": False
            }
    except Exception as e:
        logger.error(f"批量获取轨迹数据失败: {e}")
        raise HTTPException(status_code=500, detail=f"批量获取轨迹数据失败: {str(e)}")

@router.get("/all")
async def get_all_trajectory_data(
    page: int = Query(1, description="页码", ge=1),
    page_size: int = Query(10, description="每页车辆数", ge=1, le=100)
):
    """
    分页获取车辆列表（仅车牌号）
    
    Args:
        page (int): 页码
        page_size (int): 每页车辆数
        
    Returns:
        Dict: 车牌号列表和分页信息
    """
    try:
        # 分页获取车牌号
        plate_numbers, total, total_pages = fetch_plate_numbers(page, page_size)
        
        logger.info(f"获取车辆列表，第 {page} 页，共 {total_pages} 页，总计 {total} 辆车")
        return {
            "success": True,
            "data": {
                "plate_numbers": plate_numbers,
                "pagination": {
                    "current_page": page,
                    "page_size": page_size,
                    "total_items": total,
                    "total_pages": total_pages
                }
            },
            "message": "成功获取车辆列表"
        }
    except Exception as e:
        logger.error(f"获取车辆列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取车辆列表失败: {str(e)}")

@router.get("/by-plate")
async def get_trajectory_data_by_plate(
    plate_number: str = Query(..., description="车牌号")
):
    """
    根据车牌号获取轨迹数据
    
    Args:
        plate_number (str): 车牌号
        
    Returns:
        Dict[str, List[Dict[str, any]]]: 以车牌号为键，轨迹点列表为值的字典
    """
    try:
        trajectory_data = fetch_trajectory_data_by_plate(plate_number)
        if not trajectory_data or plate_number not in trajectory_data:
            raise HTTPException(status_code=404, detail=f"未找到车牌号为 {plate_number} 的轨迹数据")
        
        logger.info(f"成功获取车牌号 {plate_number} 的轨迹数据，共 {len(trajectory_data[plate_number])} 个轨迹点")
        return {
            "success": True,
            "data": trajectory_data,
            "message": f"成功获取车牌号 {plate_number} 的轨迹数据"
        }
    except Exception as e:
        logger.error(f"获取轨迹数据失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取轨迹数据失败: {str(e)}")

@router.get("/plates")
async def get_all_plate_numbers():
    """
    获取所有车牌号列表
    
    Returns:
        List[str]: 车牌号列表
    """
    try:
        # 获取所有车牌号
        plate_numbers, total, total_pages = fetch_plate_numbers(1, 10000)  # 获取最多10000个车牌号
        
        logger.info(f"成功获取 {len(plate_numbers)} 个车牌号")
        return {
            "success": True,
            "data": {
                "plate_numbers": plate_numbers,
                "count": len(plate_numbers)
            },
            "message": "成功获取所有车牌号"
        }
    except Exception as e:
        logger.error(f"获取车牌号列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取车牌号列表失败: {str(e)}")

@router.get("/summary")
async def get_trajectory_summary(
    plate_number: str = Query(..., description="车牌号")
):
    """
    获取指定车辆轨迹数据的摘要信息（不包含具体轨迹点）
    
    Args:
        plate_number (str): 车牌号
        
    Returns:
        Dict: 轨迹摘要信息
    """
    try:
        trajectory_data = fetch_trajectory_data_by_plate(plate_number)
        if not trajectory_data or plate_number not in trajectory_data:
            raise HTTPException(status_code=404, detail=f"未找到车牌号为 {plate_number} 的轨迹数据")
        
        points = trajectory_data[plate_number]
        if not points:
            return {
                "success": True,
                "data": {
                    "plate_number": plate_number,
                    "point_count": 0,
                    "time_range": None,
                    "geo_bounds": None
                },
                "message": f"车辆 {plate_number} 无轨迹数据"
            }
        
        # 计算摘要信息
        point_count = len(points)
        
        # 时间范围
        timestamps = [point['datetime'] for point in points]
        time_range = {
            "start": min(timestamps),
            "end": max(timestamps)
        }
        
        # 地理边界
        longitudes = [point['longitude'] for point in points]
        latitudes = [point['latitude'] for point in points]
        geo_bounds = {
            "min_longitude": min(longitudes),
            "max_longitude": max(longitudes),
            "min_latitude": min(latitudes),
            "max_latitude": max(latitudes)
        }
        
        summary = {
            "plate_number": plate_number,
            "point_count": point_count,
            "time_range": time_range,
            "geo_bounds": geo_bounds
        }
        
        logger.info(f"成功获取车牌号 {plate_number} 的轨迹摘要信息")
        return {
            "success": True,
            "data": summary,
            "message": f"成功获取车牌号 {plate_number} 的轨迹摘要信息"
        }
    except Exception as e:
        logger.error(f"获取轨迹摘要信息失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取轨迹摘要信息失败: {str(e)}")