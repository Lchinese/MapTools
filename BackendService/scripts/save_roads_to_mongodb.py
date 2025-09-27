#!/usr/bin/env python3
"""
将天地图WFS深圳区域完整道路数据保存到MongoDB的脚本
支持网格化分批加载，获取更完整的道路网络
"""

import sys
import os
import json
import requests
import time
from datetime import datetime
from typing import List, Dict, Any, Tuple

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import pymongo
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

def load_complete_shenzhen_roads():
    """
    加载深圳区域完整道路数据
    使用网格化分批加载策略
    """
    # 深圳完整边界框 (扩大范围)
    shenzhen_bbox = {
        "min_lon": 113.7,
        "max_lon": 114.5, 
        "min_lat": 22.4,
        "max_lat": 22.9
    }
    
    # 将深圳分为多个网格进行分批加载
    grid_size = 0.1  # 每个网格0.1度
    grids = []
    
    for lon in [shenzhen_bbox["min_lon"] + i * grid_size for i in range(int((shenzhen_bbox["max_lon"] - shenzhen_bbox["min_lon"]) / grid_size) + 1)]:
        for lat in [shenzhen_bbox["min_lat"] + i * grid_size for i in range(int((shenzhen_bbox["max_lat"] - shenzhen_bbox["min_lat"]) / grid_size) + 1)]:
            if lon < shenzhen_bbox["max_lon"] and lat < shenzhen_bbox["max_lat"]:
                grids.append({
                    "min_lon": lon,
                    "max_lon": min(lon + grid_size, shenzhen_bbox["max_lon"]),
                    "min_lat": lat,
                    "max_lat": min(lat + grid_size, shenzhen_bbox["max_lat"])
                })
    
    logger.info(f"将深圳区域分为 {len(grids)} 个网格进行分批加载")
    
    # 实际可用的道路图层类型
    road_layers = [
        'TDTService:LRDL',  # 主要道路
        'TDTService:LRRL'   # 次要道路
    ]
    
    all_roads = []
    road_id_set = set()  # 用于去重
    
    for grid_idx, grid in enumerate(grids):
        logger.info(f"处理网格 {grid_idx + 1}/{len(grids)}: {grid['min_lon']:.3f},{grid['min_lat']:.3f} - {grid['max_lon']:.3f},{grid['max_lat']:.3f}")
        
        bbox_str = f"{grid['min_lon']},{grid['min_lat']},{grid['max_lon']},{grid['max_lat']}"
        
        for layer_name in road_layers:
            try:
                roads = load_roads_from_wfs(layer_name, bbox_str)
                if roads:
                    # 去重处理
                    for road in roads:
                        road_id = road.get('id', f"{layer_name}_{len(all_roads)}")
                        if road_id not in road_id_set:
                            road_id_set.add(road_id)
                            all_roads.append(road)
                    
                    logger.info(f"  图层 {layer_name}: 加载 {len(roads)} 条道路，累计 {len(all_roads)} 条")
                
                # 避免请求过于频繁
                time.sleep(0.5)
                
            except Exception as e:
                logger.warning(f"  图层 {layer_name} 加载失败: {e}")
                continue
    
    logger.info(f"✅ 深圳区域完整道路数据加载完成，总计 {len(all_roads)} 条道路")
    return all_roads

def load_roads_from_wfs(layer_name: str, bbox: str) -> List[Dict[str, Any]]:
    """
    从天地图WFS服务加载指定图层的道路数据
    """
    wfs_url = "http://gisserver.tianditu.gov.cn/TDTService/wfs"
    
    params = {
        'service': 'WFS',
        'version': '1.1.0',
        'request': 'GetFeature',
        'typeName': layer_name,
        'outputFormat': 'application/json',
        'srsName': 'EPSG:4326',
        'bbox': f'{bbox},EPSG:4326',
        'maxFeatures': 10000  # 增加最大特征数
    }
    
    try:
        response = requests.get(wfs_url, params=params, timeout=60)
        response.raise_for_status()
        
        data = response.json()
        roads = []
        
        for feature in data.get('features', []):
            properties = feature.get('properties', {})
            geometry = feature.get('geometry', {})
            
            if geometry and geometry['type'] in ['MultiLineString', 'LineString']:
                # 处理MultiLineString和LineString
                coordinates_list = []
                if geometry['type'] == 'MultiLineString':
                    coordinates_list = geometry['coordinates']
                else:
                    coordinates_list = [geometry['coordinates']]
                
                for coords in coordinates_list:
                    if len(coords) >= 2:
                        points = [(lon, lat) for lon, lat in coords]
                        roads.append({
                            'id': f"{layer_name}_{properties.get('OBJECTID', len(roads))}",
                            'name': properties.get('NAME', f'未命名道路_{len(roads)}'),
                            'type': properties.get('TYPE', layer_name),
                            'points': points
                        })
        
        return roads
        
    except Exception as e:
        logger.error(f"从WFS加载图层 {layer_name} 失败: {e}")
        return []

def save_roads_to_mongodb():
    """
    将道路数据保存到MongoDB
    """
    try:
        # 1. 加载深圳区域完整道路数据
        logger.info("开始加载深圳区域完整道路数据...")
        all_roads = load_complete_shenzhen_roads()
        
        if not all_roads:
            logger.error("没有加载到任何道路数据")
            return False
        
        logger.info(f"成功加载 {len(all_roads)} 条道路数据")
        
        # 2. 连接到MongoDB
        collection, client = connect_to_mongodb()
        if collection is None:
            return False
        
        # 3. 清空现有道路数据（可选）
        logger.info("清空现有道路数据...")
        collection.delete_many({})
        
        # 4. 准备批量插入的数据
        roads_data = []
        for i, road in enumerate(all_roads):
            points = road.get('points', [])
            if not points:
                continue
                
            road_doc = {
                "road_id": road.get('id', f'road_{i}'),
                "name": road.get('name', f'未命名道路_{i}'),
                "type": road.get('type', 'unknown'),
                "points": points,
                "created_at": datetime.now(),
                "updated_at": datetime.now(),
                "source": "tianditu_wfs_complete",
                "bbox": {
                    "min_lon": min([p[0] for p in points]) if points else 0,
                    "max_lon": max([p[0] for p in points]) if points else 0,
                    "min_lat": min([p[1] for p in points]) if points else 0,
                    "max_lat": max([p[1] for p in points]) if points else 0,
                },
                "point_count": len(points),
                "metadata": {
                    "total_roads": len(all_roads),
                    "loaded_at": datetime.now().isoformat(),
                    "region": "深圳完整区域",
                    "grid_loading": True,
                    "layers_loaded": ['TDTService:LRDL', 'TDTService:LRRL']
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
        
        # 8. 保存统计信息到主集合的元数据文档
        stats_doc = {
            "_id": "metadata",
            "total_roads": total_count,
            "saved_at": datetime.now().isoformat(),
            "source": "tianditu_wfs_complete",
            "region": "深圳完整区域",
            "bbox": "113.7,22.4,114.5,22.9",
            "type": "metadata",
            "grid_loading": True,
                    "layers_loaded": ['TDTService:LRDL', 'TDTService:LRRL'],
            "grid_size": 0.1,
            "total_grids": len(grids) if 'grids' in locals() else 0
        }
        
        # 保存统计信息到主集合
        collection.insert_one(stats_doc)
        
        logger.info("✅ 道路数据保存完成！")
        logger.info(f"📊 统计信息: 总计 {stats_doc['total_roads']} 条道路，保存时间: {stats_doc['saved_at']}")
        
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
        stats = collection.find_one({"_id": "metadata"})
        if stats:
            logger.info(f"📊 道路网络统计: 总计 {stats['total_roads']} 条道路")
        
    except Exception as e:
        logger.error(f"查询道路数据失败: {e}")
    finally:
        if 'client' in locals():
            client.close()

if __name__ == "__main__":
    logger.info("🚀 开始执行深圳区域完整道路数据保存脚本...")
    logger.info("📋 加载策略: 网格化分批加载，2个道路图层")
    logger.info("🗺️  覆盖区域: 深圳完整区域 (113.7,22.4 - 114.5,22.9)")
    
    # 保存道路数据到MongoDB
    success = save_roads_to_mongodb()
    
    if success:
        logger.info("✅ 脚本执行成功！")
        
        # 验证数据
        logger.info("🔍 验证保存的数据...")
        query_roads_from_mongodb(10)
    else:
        logger.error("❌ 脚本执行失败！")
        sys.exit(1)
