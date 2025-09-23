"""
保存原始轨迹数据到MongoDB的脚本
引用现有的按车辆分页查询功能，避免重复代码
"""

import pymongo
import logging
from datetime import datetime
from typing import Dict, List, Any
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入现有的轨迹查询功能
from UtilityTools.fetch_trajectory_data import (
    connect_to_mongodb, 
    fetch_all_trajectory_data,
    fetch_trajectory_data_by_plate,
    fetch_plate_numbers
)
from UtilityTools.road_matching import RoadMatcher

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('Logs/original_trajectory_save.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)


def save_original_trajectories_to_mongodb(
    source_db_name: str = "MapTools",
    target_db_name: str = "MapTools",
    batch_size: int = 100,
    match_to_roads: bool = True
):
    """
    将GPS轨迹数据保存到MongoDB的original_trajectories_xx集合
    
    Args:
        source_db_name: 源数据库名称
        target_db_name: 目标数据库名称
        batch_size: 批处理大小
        match_to_roads: 是否进行道路匹配（默认True）
    """
    logger.info("🚀 开始执行轨迹数据保存脚本...")
    
    try:
        # 1. 统一加载道路匹配器（如果需要道路匹配）
        road_matcher = None
        if match_to_roads:
            logger.info("加载道路网络数据...")
            road_matcher = RoadMatcher()
            logger.info(f"道路网络加载完成，共 {len(road_matcher.roads)} 条道路")
        
        # 2. 连接到MongoDB
        client = pymongo.MongoClient("mongodb://localhost:27017")
        source_db = client[source_db_name]
        target_db = client[target_db_name]
        
        # 3. 处理01到30的所有集合
        total_saved = 0
        total_skipped = 0
        start_time = datetime.now()
        
        for i in range(1, 31):
            collection_suffix = f"{i:02d}"  # 01, 02, 03, ..., 30
            source_collection_name = f"gps_points_{collection_suffix}"
            target_collection_name = f"original_trajectories_{collection_suffix}"
            
            logger.info(f"处理集合: {source_collection_name} -> {target_collection_name}")
            
            # 检查源集合是否存在
            if source_collection_name not in source_db.list_collection_names():
                logger.info(f"源集合 {source_collection_name} 不存在，跳过")
                continue
            
            # 获取源集合和目标集合
            source_collection = source_db[source_collection_name]
            target_collection = target_db[target_collection_name]
            
            # 检查源集合中的文档数量
            source_count = source_collection.count_documents({})
            logger.info(f"源集合 {source_collection_name} 共有 {source_count} 个GPS点")
            
            # 检查已存在的车牌号，避免重复存储
            trajectory_type = "matched_trajectory" if match_to_roads else "original_trajectory"
            existing_plates = set()
            existing_docs = target_collection.find({"type": trajectory_type}, {"plate_number": 1})
            for doc in existing_docs:
                existing_plates.add(doc["plate_number"])
            logger.info(f"已存在 {len(existing_plates)} 个车牌号的轨迹数据")
            
            # 获取所有车牌号
            all_plates = source_collection.distinct("plate_number")
            logger.info(f"从集合 {source_collection_name} 找到 {len(all_plates)} 个车牌号，开始处理...")
            
            # 分批处理每个车牌号的轨迹数据
            saved_count = 0
            skipped_count = 0
            processed_plates = 0
            
            for plate_number in all_plates:
                try:
                    # 检查是否已存在，避免重复存储
                    if plate_number in existing_plates:
                        skipped_count += 1
                        continue
                    
                    # 使用现有的按车牌查询功能
                    plate_data = fetch_trajectory_data_by_plate(
                        plate_number=plate_number,
                        db_name=source_db_name,
                        collection_name=source_collection_name,
                        match_to_roads=False  # 先获取原始数据
                    )
                    
                    if plate_data and plate_number in plate_data:
                        trajectory_points = plate_data[plate_number]
                    
                    if trajectory_points:
                        # 如果需要进行道路匹配
                        if match_to_roads and road_matcher:
                            try:
                                # 进行道路匹配
                                matched_points = road_matcher.match_gps_to_roads(trajectory_points)
                                
                                # 转换为轨迹点格式
                                matched_trajectory_points = []
                                for matched_point in matched_points:
                                    trajectory_point = {
                                        'plate_number': matched_point['original_gps']['plate_number'],
                                        'datetime': matched_point['original_gps']['datetime'],
                                        'longitude': matched_point['matched_longitude'],
                                        'latitude': matched_point['matched_latitude'],
                                        'speed': matched_point['original_gps']['speed'],
                                        'heading': matched_point['original_gps']['heading'],
                                        'is_valid': matched_point['original_gps']['is_valid'],
                                        'source_file': matched_point['original_gps']['source_file'],
                                        'road_id': matched_point['road_id'],
                                        'road_name': matched_point['road_name'],
                                        'road_type': matched_point['road_type'],
                                        'distance_to_road': matched_point['distance_to_road'],
                                        'matched': True
                                    }
                                    matched_trajectory_points.append(trajectory_point)
                                
                                trajectory_points = matched_trajectory_points
                            except Exception as e:
                                logger.error(f"道路匹配失败 {plate_number}: {e}")
                                continue
                        
                        # 准备保存的文档
                        trajectory_doc = {
                            "plate_number": plate_number,
                            "trajectory_points": trajectory_points,
                            "point_count": len(trajectory_points),
                            "first_point": trajectory_points[0] if trajectory_points else None,
                            "last_point": trajectory_points[-1] if trajectory_points else None,
                            "time_range": {
                                "start": trajectory_points[0]['datetime'] if trajectory_points else None,
                                "end": trajectory_points[-1]['datetime'] if trajectory_points else None
                            },
                            "bbox": {
                                "min_lon": min(point['longitude'] for point in trajectory_points),
                                "max_lon": max(point['longitude'] for point in trajectory_points),
                                "min_lat": min(point['latitude'] for point in trajectory_points),
                                "max_lat": max(point['latitude'] for point in trajectory_points)
                            },
                            "source": "gps_points_collection",
                            "created_at": datetime.now().isoformat(),
                            "type": trajectory_type
                        }
                        
                        # 插入到目标集合
                        target_collection.insert_one(trajectory_doc)
                        saved_count += 1
                
                    processed_plates += 1
                    
                    # 每处理100个车牌号输出一次进度
                    if processed_plates % 100 == 0:
                        elapsed = datetime.now() - start_time
                        logger.info(f"[{elapsed}] 进度: {processed_plates}/{len(all_plates)} | 已保存: {saved_count} | 跳过: {skipped_count}")
                        
                except Exception as e:
                    logger.error(f"处理车牌号 {plate_number} 时出错: {e}")
                    continue
            
            # 为当前集合创建索引
            logger.info(f"为集合 {target_collection_name} 创建索引...")
            target_collection.create_index([("plate_number", pymongo.ASCENDING)], unique=True)
            target_collection.create_index([("type", pymongo.ASCENDING)])
            target_collection.create_index([("point_count", pymongo.ASCENDING)])
            target_collection.create_index([
                ("bbox.min_lon", pymongo.ASCENDING), 
                ("bbox.max_lon", pymongo.ASCENDING), 
                ("bbox.min_lat", pymongo.ASCENDING), 
                ("bbox.max_lat", pymongo.ASCENDING)
            ])
            
            # 验证当前集合数据
            collection_saved = target_collection.count_documents({})
            logger.info(f"集合 {target_collection_name} 验证完成，共有 {collection_saved} 条轨迹数据")
            
            # 保存当前集合统计信息
            stats_doc = {
                "_id": f"metadata_{collection_suffix}",
                "total_trajectories": collection_saved,
                "total_plates_processed": processed_plates,
                "saved_at": datetime.now().isoformat(),
                "source": f"gps_points_{collection_suffix}",
                "type": "metadata"
            }
            
            target_collection.insert_one(stats_doc)
            
            # 累计统计
            total_saved += collection_saved
            total_skipped += skipped_count
            
            logger.info(f"集合 {source_collection_name} 处理完成: 保存 {saved_count} 条轨迹 | 跳过 {skipped_count} 个车牌")
        
        total_time = datetime.now() - start_time
        logger.info("✅ 所有轨迹数据保存完成！")
        logger.info(f"📊 总计: {total_saved} 条轨迹 | 跳过: {total_skipped} 个车牌 | 耗时: {total_time}")
        
        return True
        
    except Exception as e:
        logger.error(f"保存原始轨迹数据失败: {e}")
        logger.error("❌ 脚本执行失败！")
        return False
    finally:
        if 'client' in locals() and client:
            client.close()


def verify_saved_data():
    """验证保存的数据"""
    try:
        collection, client = connect_to_mongodb("MapTools", "original_trajectories")
        if collection is None:
            return
        
        # 获取统计信息
        stats = collection.find_one({"_id": "metadata"})
        if stats:
            logger.info(f"📊 保存统计: {stats}")
        
        # 获取示例数据
        sample = collection.find_one({"type": "original_trajectory"})
        if sample:
            logger.info(f"📝 示例轨迹: {sample['plate_number']} - {sample['point_count']} 个点")
            logger.info(f"   时间范围: {sample['time_range']['start']} 到 {sample['time_range']['end']}")
            logger.info(f"   边界框: {sample['bbox']}")
        
        client.close()
        
    except Exception as e:
        logger.error(f"验证数据时出错: {e}")


if __name__ == "__main__":
    logger.info("=" * 50)
    logger.info("原始轨迹数据保存脚本")
    logger.info("=" * 50)
    
    # 执行保存
    success = save_original_trajectories_to_mongodb()
    
    if success:
        # 验证保存的数据
        verify_saved_data()
        logger.info("🎉 脚本执行成功！")
    else:
        logger.error("💥 脚本执行失败！")
