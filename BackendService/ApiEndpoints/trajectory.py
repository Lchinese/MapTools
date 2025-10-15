"""
轨迹数据API端点
提供从MongoDB获取轨迹数据的功能
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Dict, List, Optional
import logging

from UtilityTools.fetch_trajectory_data import (
    fetch_all_trajectory_data, 
    fetch_trajectory_data_by_plate,
    fetch_plate_numbers
)
import pymongo
from UtilityTools.road_matching import RoadMatcher

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/trajectory", tags=["轨迹数据"])

# 创建道路匹配器实例
road_matcher = RoadMatcher()

@router.get("/original")
async def get_original_trajectory_data(
    page: int = Query(1, description="页码", ge=1),
    page_size: int = Query(20, description="每页车辆数量", ge=1, le=100),
    plate_number: Optional[str] = Query(None, description="指定车牌号")
):
    """
    从数据库获取原始轨迹数据（分页查询）
    
    Args:
        page (int): 页码
        page_size (int): 每页车辆数量
        plate_number (str, optional): 指定车牌号
        
    Returns:
        Dict: 原始轨迹数据
    """
    try:
        # 连接到MongoDB
        client = pymongo.MongoClient('localhost', 27017)
        db = client['MapTools']
        collection = db['original_trajectories']
        
        # 构建查询条件
        query = {"type": "original_trajectory"}
        if plate_number:
            query["plate_number"] = plate_number
        
        # 计算跳过的文档数量
        skip = (page - 1) * page_size
        
        # 查询数据
        cursor = collection.find(query).skip(skip).limit(page_size)
        trajectories = list(cursor)
        
        # 获取总数
        total_count = collection.count_documents(query)
        total_pages = (total_count + page_size - 1) // page_size
        
        # 转换为前端需要的格式
        trajectory_data = {}
        for doc in trajectories:
            plate_num = doc['plate_number']
            trajectory_data[plate_num] = doc['trajectory_points']
        
        client.close()
        
        logger.info(f"成功获取第 {page} 页原始轨迹数据，共 {len(trajectory_data)} 辆车")
        
        return {
            "success": True,
            "data": trajectory_data,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total_count": total_count,
                "total_pages": total_pages
            },
            "message": f"成功获取第 {page} 页原始轨迹数据"
        }
        
    except Exception as e:
        logger.error(f"获取原始轨迹数据失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取原始轨迹数据失败: {str(e)}")

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

@router.get("/first-day-first-vehicle")
async def get_first_day_first_vehicle_trajectory():
    """
    获取第一天第一辆车的轨迹数据（用于初始化）
    
    Returns:
        Dict: 第一辆车的轨迹数据
    """
    try:
        # 连接到MongoDB
        client = pymongo.MongoClient('localhost', 27017)
        db = client['MapTools']
        
        # 查找第一个有数据的集合
        collections = []
        for i in range(1, 31):  # 检查01到30的集合
            collection_name = f"original_trajectories_{i:02d}"
            if collection_name in db.list_collection_names():
                collection = db[collection_name]
                # 查找第一个轨迹文档（原始轨迹或匹配轨迹都可以）
                first_doc = collection.find_one({"type": {"$in": ["original_trajectory", "matched_trajectory"]}})
                if first_doc:
                    collections.append((i, collection_name, first_doc))
                    break
        
        if not collections:
            raise HTTPException(status_code=404, detail="未找到任何轨迹数据")
        
        collection_index, collection_name, first_doc = collections[0]
        plate_number = first_doc['plate_number']
        trajectory_points = first_doc['trajectory_points']
        
        client.close()
        
        logger.info(f"成功获取第一天第一辆车 {plate_number} 的轨迹数据，共 {len(trajectory_points)} 个轨迹点")
        
        return {
            "success": True,
            "plate_number": plate_number,
            "data": trajectory_points,
            "collection": collection_name,
            "point_count": len(trajectory_points),
            "message": f"成功获取第一天第一辆车 {plate_number} 的轨迹数据"
        }
        
    except Exception as e:
        logger.error(f"获取第一天第一辆车轨迹数据失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取第一天第一辆车轨迹数据失败: {str(e)}")

@router.get("/single-vehicle")
async def get_single_vehicle_trajectory(
    plate_number: str = Query(..., description="车牌号"),
    start_time: str = Query(..., description="开始时间 (YYYY-MM-DD HH:mm:ss)"),
    end_time: str = Query(..., description="结束时间 (YYYY-MM-DD HH:mm:ss)"),
    match_to_roads: bool = Query(False, description="是否进行道路匹配")
):
    """
    根据车牌号和时间范围获取单车辆轨迹数据
    
    Args:
        plate_number (str): 车牌号
        start_time (str): 开始时间
        end_time (str): 结束时间
        match_to_roads (bool): 是否进行道路匹配
        
    Returns:
        Dict: 单车辆轨迹数据
    """
    try:
        # 连接到MongoDB
        client = pymongo.MongoClient('localhost', 27017)
        db = client['MapTools']
        
        # 查找包含该车牌号的集合
        trajectory_data = None
        for i in range(1, 31):
            collection_name = f"original_trajectories_{i:02d}"
            if collection_name in db.list_collection_names():
                collection = db[collection_name]
                # 先尝试查找指定类型的轨迹
                doc = collection.find_one({
                    "plate_number": plate_number,
                    "type": "matched_trajectory" if match_to_roads else "original_trajectory"
                })
                
                # 如果没找到，尝试查找任何类型的轨迹
                if not doc:
                    doc = collection.find_one({
                        "plate_number": plate_number
                    })
                if doc:
                    trajectory_data = doc['trajectory_points']
                    break
        
        if not trajectory_data:
            raise HTTPException(status_code=404, detail=f"未找到车牌号为 {plate_number} 的轨迹数据")
        
        # 过滤时间范围内的轨迹点
        from datetime import datetime
        start_dt = datetime.strptime(start_time, '%Y-%m-%d %H:%M:%S')
        end_dt = datetime.strptime(end_time, '%Y-%m-%d %H:%M:%S')
        
        filtered_points = []
        for point in trajectory_data:
            try:
                # 尝试不同的时间格式解析
                point_datetime = point['datetime']
                if isinstance(point_datetime, str):
                    # 如果是字符串，尝试解析
                    if 'T' in point_datetime:
                        point_dt = datetime.fromisoformat(point_datetime.replace('Z', '+00:00'))
                    else:
                        # 尝试标准格式
                        point_dt = datetime.strptime(point_datetime, '%Y-%m-%d %H:%M:%S')
                else:
                    # 如果已经是datetime对象
                    point_dt = point_datetime
                
                if start_dt <= point_dt <= end_dt:
                    filtered_points.append(point)
            except Exception as e:
                logger.warning(f"解析时间失败: {point.get('datetime')}, 错误: {e}")
                continue
        
        client.close()
        
        logger.info(f"成功获取车牌号 {plate_number} 在 {start_time} 到 {end_time} 的轨迹数据，共 {len(filtered_points)} 个轨迹点")
        
        return {
            "success": True,
            "data": filtered_points,
            "plate_number": plate_number,
            "time_range": {
                "start": start_time,
                "end": end_time
            },
            "point_count": len(filtered_points),
            "match_to_roads": match_to_roads,
            "message": f"成功获取车牌号 {plate_number} 的轨迹数据"
        }
        
    except Exception as e:
        logger.error(f"获取单车辆轨迹数据失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取单车辆轨迹数据失败: {str(e)}")

@router.get("/corrected")
async def get_corrected_trajectory_data(
    page: int = Query(1, description="页码", ge=1),
    page_size: int = Query(20, description="每页车辆数量", ge=1, le=100),
    plate_number: Optional[str] = Query(None, description="指定车牌号")
):
    """
    获取修正轨迹数据
    """
    try:
        client = pymongo.MongoClient('localhost', 27017)
        db = client['MapTools']
        
        # 查找修正轨迹集合
        corrected_collections = []
        for i in range(1, 31):
            collection_name = f"corrected_trajectories_{i:02d}"
            if collection_name in db.list_collection_names():
                collection = db[collection_name]
                if collection.count_documents({}) > 0:
                    corrected_collections.append(collection)
        
        if not corrected_collections:
            client.close()
            return {
                "success": False,
                "message": "未找到修正轨迹数据",
                "data": [],
                "total": 0,
                "page": page,
                "page_size": page_size
            }
        
        # 获取所有车牌号（与原始轨迹保持一致）
        all_plate_numbers = []
        for collection in corrected_collections:
            plates = collection.distinct("plate_number")
            all_plate_numbers.extend(plates)
        
        # 去重并排序
        unique_plates = sorted(list(set(all_plate_numbers)))
        
        if plate_number:
            # 查找指定车牌号
            if plate_number not in unique_plates:
                client.close()
                return {
                    "success": False,
                    "message": f"未找到车牌号 {plate_number} 的修正轨迹",
                    "data": [],
                    "total": 0,
                    "page": page,
                    "page_size": page_size
                }
            
            # 获取指定车牌号的修正轨迹
            trajectory_data = {}
            for collection in corrected_collections:
                doc = collection.find_one({"plate_number": plate_number})
                if doc:
                    trajectory_points = doc.get("trajectory_points", [])
                    if trajectory_points:
                        trajectory_data[plate_number] = trajectory_points
                        break
            
            client.close()
            return {
                "success": True,
                "message": f"成功获取车牌号 {plate_number} 的修正轨迹数据",
                "data": trajectory_data,
                "total": 1,
                "page": 1,
                "page_size": 1
            }
        
        # 分页获取车牌号
        total_plates = len(unique_plates)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        page_plates = unique_plates[start_idx:end_idx]
        
        # 获取这些车牌号的修正轨迹数据
        trajectory_data = {}
        for plate in page_plates:
            for collection in corrected_collections:
                doc = collection.find_one({"plate_number": plate})
                if doc:
                    trajectory_points = doc.get("trajectory_points", [])
                    if trajectory_points:
                        trajectory_data[plate] = trajectory_points
                        break
        
        client.close()
        
        return {
            "success": True,
            "message": f"成功获取第{page}页修正轨迹数据",
            "data": trajectory_data,
            "total": total_plates,
            "page": page,
            "page_size": page_size
        }
        
    except Exception as e:
        logger.error(f"获取修正轨迹数据失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取修正轨迹数据失败: {str(e)}")

@router.get("/corrected/single-vehicle")
async def get_single_vehicle_corrected_trajectory(
    plate_number: str = Query(..., description="车牌号"),
    start_time: str = Query(..., description="开始时间 (YYYY-MM-DD HH:mm:ss)"),
    end_time: str = Query(..., description="结束时间 (YYYY-MM-DD HH:mm:ss)")
):
    """
    根据车牌号和时间范围获取单车辆修正轨迹数据
    """
    try:
        # 连接到MongoDB
        client = pymongo.MongoClient('localhost', 27017)
        db = client['MapTools']
        
        # 查找包含该车牌号的修正轨迹集合
        trajectory_data = None
        for i in range(1, 31):
            collection_name = f"corrected_trajectories_{i:02d}"
            if collection_name in db.list_collection_names():
                collection = db[collection_name]
                doc = collection.find_one({"plate_number": plate_number})
                
                if doc:
                    trajectory_data = doc.get("trajectory_points", [])
                    if trajectory_data:
                        break
        
        if not trajectory_data:
            raise HTTPException(status_code=404, detail=f"未找到车牌号为 {plate_number} 的修正轨迹数据")
        
        # 过滤时间范围内的轨迹点
        from datetime import datetime
        start_dt = datetime.strptime(start_time, '%Y-%m-%d %H:%M:%S')
        end_dt = datetime.strptime(end_time, '%Y-%m-%d %H:%M:%S')
        
        filtered_points = []
        for point in trajectory_data:
            try:
                # 尝试不同的时间格式解析
                point_datetime = point['datetime']
                if isinstance(point_datetime, str):
                    # 如果是字符串，尝试解析
                    if 'CST' in point_datetime or 'GMT' in point_datetime:
                        # 处理英文格式: Fri Sep 02 07:36:57 CST 2016 (Java Date.toString()格式)
                        import re
                        # 直接使用正则表达式手动解析
                        match = re.match(r'(\w{3})\s+(\w{3})\s+(\d{1,2})\s+(\d{2}):(\d{2}):(\d{2})\s+\w{3}\s+(\d{4})', point_datetime)
                        if match:
                            day_name, month_name, day, hour, minute, second, year = match.groups()
                            month_map = {'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6,
                                       'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12}
                            point_dt = datetime(int(year), month_map[month_name], int(day), 
                                              int(hour), int(minute), int(second))
                        else:
                            raise ValueError(f"无法解析时间格式: {point_datetime}")
                    elif 'T' in point_datetime:
                        point_dt = datetime.fromisoformat(point_datetime.replace('Z', '+00:00'))
                    else:
                        # 尝试标准格式
                        point_dt = datetime.strptime(point_datetime, '%Y-%m-%d %H:%M:%S')
                else:
                    # 如果已经是datetime对象
                    point_dt = point_datetime
                
                if start_dt <= point_dt <= end_dt:
                    filtered_points.append(point)
            except Exception as e:
                logger.warning(f"解析修正轨迹时间失败: {point.get('datetime')}, 错误: {e}")
                continue
        
        client.close()
        
        logger.info(f"成功获取车牌号 {plate_number} 在 {start_time} 到 {end_time} 的修正轨迹数据，共 {len(filtered_points)} 个轨迹点")
        
        return {
            "success": True,
            "data": filtered_points,
            "plate_number": plate_number,
            "time_range": {
                "start": start_time,
                "end": end_time
            },
            "point_count": len(filtered_points),
            "message": f"成功获取车牌号 {plate_number} 的修正轨迹数据"
        }
        
    except Exception as e:
        logger.error(f"获取单车辆修正轨迹数据失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取单车辆修正轨迹数据失败: {str(e)}")