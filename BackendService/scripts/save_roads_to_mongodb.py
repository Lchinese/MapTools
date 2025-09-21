#!/usr/bin/env python3
"""
将天地图WFS道路数据保存到MongoDB的脚本
"""

import sys
import os
import json
from datetime import datetime
from typing import List, Dict, Any

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import pymongo
from UtilityTools.road_matching import RoadMatcher
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def connect_to_mongodb(db_name: str = "MapTools", collection_name: str = "road_network"):
    """
    连接到MongoDB数据库
    
    Args:
        db_name (str): 数据库名称
        collection_name (str): 集合名称
    
    Returns:
        tuple: (collection, client) MongoDB集合对象和客户端连接
    """
    try:
        client = pymongo.MongoClient('localhost', 27017, serverSelectionTimeoutMS=5000)
        # 测试连接
        client.server_info()
        db = client[db_name]
        collection = db[collection_name]
        logger.info(f"成功连接到MongoDB: {db_name}.{collection_name}")
        return collection, client
    except Exception as e:
        logger.error(f"连接MongoDB失败: {e}")
        return None, None

def save_roads_to_mongodb():
    """
    将道路数据保存到MongoDB
    """
    try:
        # 1. 创建道路匹配器实例，加载道路数据
        logger.info("开始加载天地图WFS道路数据...")
        road_matcher = RoadMatcher()
        
        if not road_matcher.roads:
            logger.error("没有加载到任何道路数据")
            return False
        
        logger.info(f"成功加载 {len(road_matcher.roads)} 条道路数据")
        
        # 2. 连接到MongoDB
        collection, client = connect_to_mongodb()
        if collection is None:
            return False
        
        # 3. 清空现有道路数据（可选）
        logger.info("清空现有道路数据...")
        collection.delete_many({})
        
        # 4. 准备批量插入的数据
        roads_data = []
        for i, road in enumerate(road_matcher.roads):
            road_doc = {
                "road_id": road.get('id', f'road_{i}'),
                "name": road.get('name', f'未命名道路_{i}'),
                "type": road.get('type', 'unknown'),
                "points": road.get('points', []),
                "created_at": datetime.now(),
                "updated_at": datetime.now(),
                "source": "tianditu_wfs",
                "bbox": {
                    "min_lon": min([p[0] for p in road.get('points', [])]) if road.get('points') else 0,
                    "max_lon": max([p[0] for p in road.get('points', [])]) if road.get('points') else 0,
                    "min_lat": min([p[1] for p in road.get('points', [])]) if road.get('points') else 0,
                    "max_lat": max([p[1] for p in road.get('points', [])]) if road.get('points') else 0,
                },
                "point_count": len(road.get('points', [])),
                "metadata": {
                    "total_roads": len(road_matcher.roads),
                    "loaded_at": datetime.now().isoformat(),
                    "region": "深圳"
                }
            }
            roads_data.append(road_doc)
        
        # 5. 批量插入道路数据
        logger.info(f"开始批量插入 {len(roads_data)} 条道路数据到MongoDB...")
        
        # 分批插入，避免单次插入数据量过大
        batch_size = 1000
        total_inserted = 0
        
        for i in range(0, len(roads_data), batch_size):
            batch = roads_data[i:i + batch_size]
            result = collection.insert_many(batch)
            total_inserted += len(result.inserted_ids)
            logger.info(f"已插入 {total_inserted}/{len(roads_data)} 条道路数据")
        
        # 6. 创建索引
        logger.info("创建数据库索引...")
        collection.create_index("road_id")
        collection.create_index("type")
        collection.create_index("name")
        collection.create_index([("bbox.min_lon", 1), ("bbox.max_lon", 1)])
        collection.create_index([("bbox.min_lat", 1), ("bbox.max_lat", 1)])
        collection.create_index("created_at")
        
        # 7. 验证数据
        total_count = collection.count_documents({})
        logger.info(f"验证完成，MongoDB中共有 {total_count} 条道路数据")
        
        # 8. 保存统计信息
        stats = {
            "total_roads": total_count,
            "saved_at": datetime.now().isoformat(),
            "source": "tianditu_wfs",
            "region": "深圳",
            "bbox": "113.812401,22.503099,114.269966,22.748068"
        }
        
        # 保存统计信息到单独的集合
        stats_collection = client["MapTools"]["road_network_stats"]
        stats_collection.delete_many({})  # 清空旧统计
        stats_collection.insert_one(stats)
        
        logger.info("✅ 道路数据保存完成！")
        logger.info(f"📊 统计信息: 总计 {stats['total_roads']} 条道路，保存时间: {stats['saved_at']}")
        
        return True
        
    except Exception as e:
        logger.error(f"保存道路数据失败: {e}")
        return False
    finally:
        if 'client' in locals():
            client.close()

def query_roads_from_mongodb(limit: int = 5):
    """
    从MongoDB查询道路数据（用于验证）
    
    Args:
        limit (int): 查询数量限制
    """
    try:
        collection, client = connect_to_mongodb()
        if collection is None:
            return
        
        logger.info(f"从MongoDB查询前 {limit} 条道路数据:")
        
        roads = collection.find().limit(limit)
        for i, road in enumerate(roads, 1):
            logger.info(f"  {i}. ID: {road['road_id']}, 名称: {road['name']}, 类型: {road['type']}, 点数: {road['point_count']}")
        
        # 查询统计信息
        stats_collection = client["MapTools"]["road_network_stats"]
        stats = stats_collection.find_one()
        if stats:
            logger.info(f"📊 道路网络统计: 总计 {stats['total_roads']} 条道路")
        
    except Exception as e:
        logger.error(f"查询道路数据失败: {e}")
    finally:
        if 'client' in locals():
            client.close()

if __name__ == "__main__":
    logger.info("🚀 开始执行道路数据保存脚本...")
    
    # 保存道路数据到MongoDB
    success = save_roads_to_mongodb()
    
    if success:
        logger.info("✅ 脚本执行成功！")
        
        # 验证数据
        logger.info("🔍 验证保存的数据...")
        query_roads_from_mongodb(5)
    else:
        logger.error("❌ 脚本执行失败！")
        sys.exit(1)
