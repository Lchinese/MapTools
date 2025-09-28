#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
道路数据分类和MongoDB存储脚本
按照是否有name和是否是道路两个标准分为4类
"""

import json
import pymongo
from datetime import datetime
from typing import Dict, List, Any
import logging
from tqdm import tqdm
import hashlib
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class 道路分类器:
    """道路数据分类器"""
    
    def __init__(self, mongodb_uri: str = None, database_name: str = None):
        """初始化分类器"""
        # 从环境变量读取配置，如果没有则使用默认值
        self.mongodb_uri = mongodb_uri or os.getenv("MONGODB_URL", "mongodb://localhost:27017/")
        self.database_name = database_name or os.getenv("MONGODB_DATABASE", "MapTools")
        self.client = None
        self.db = None
        self.已存在要素ID = set()  # 用于防重复
        
        # 道路类型定义
        self.道路类型列表 = [
            "motorway", "trunk", "primary", "secondary", "tertiary", 
            "unclassified", "residential", "service", "motorway_link",
            "trunk_link", "primary_link", "secondary_link", "tertiary_link",
            "living_street", "pedestrian", "track", "bus_guideway",
            "escape", "raceway", "road", "services"
        ]
        
        # 非道路类型定义
        self.非道路类型列表 = [
            "footway", "bridleway", "steps", "corridor", "path",
            "cycleway", "busway", "platform", "bus_stop", "crossing",
            "elevator", "emergency_bay", "give_way", "mini_roundabout",
            "motorway_junction", "passing_place", "rest_area", "speed_camera",
            "stop", "street_lamp", "traffic_signals", "turning_circle"
        ]
    
    def 连接数据库(self):
        """连接到MongoDB数据库"""
        try:
            self.client = pymongo.MongoClient(self.mongodb_uri)
            self.db = self.client[self.database_name]
            logger.info(f"成功连接到MongoDB数据库: {self.database_name}")
            
            # 加载已存在的要素ID，防止重复
            self.加载已存在要素ID()
            
            return True
        except Exception as e:
            logger.error(f"连接MongoDB失败: {e}")
            return False
    
    def 加载已存在要素ID(self):
        """加载已存在的要素ID，用于防重复"""
        try:
            # 从道路数据集合加载
            道路结果 = self.db["道路数据"].find({}, {"features.properties.@id": 1})
            for 文档 in 道路结果:
                if "features" in 文档:
                    for 要素 in 文档["features"]:
                        if "properties" in 要素 and "@id" in 要素["properties"]:
                            self.已存在要素ID.add(要素["properties"]["@id"])
            
            # 从非道路数据集合加载
            非道路结果 = self.db["非道路数据"].find({}, {"features.properties.@id": 1})
            for 文档 in 非道路结果:
                if "features" in 文档:
                    for 要素 in 文档["features"]:
                        if "properties" in 要素 and "@id" in 要素["properties"]:
                            self.已存在要素ID.add(要素["properties"]["@id"])
            
            logger.info(f"已加载 {len(self.已存在要素ID)} 个已存在的要素ID")
            
        except Exception as e:
            logger.warning(f"加载已存在要素ID时出错: {e}")
            self.已存在要素ID = set()
    
    def 生成要素唯一标识(self, feature: Dict[str, Any]) -> str:
        """生成要素的唯一标识"""
        properties = feature.get("properties", {})
        geometry = feature.get("geometry", {})
        
        # 使用@id作为主要标识
        if "@id" in properties:
            return properties["@id"]
        
        # 如果没有@id，使用几何坐标生成哈希
        if "coordinates" in geometry:
            coord_str = str(geometry["coordinates"])
            return hashlib.md5(coord_str.encode()).hexdigest()
        
        # 最后使用整个要素的哈希
        feature_str = json.dumps(feature, sort_keys=True)
        return hashlib.md5(feature_str.encode()).hexdigest()
    
    def 检查是否重复(self, feature: Dict[str, Any]) -> bool:
        """检查要素是否已存在"""
        唯一标识 = self.生成要素唯一标识(feature)
        return 唯一标识 in self.已存在要素ID
    
    def 判断是否为道路(self, properties: Dict[str, Any]) -> bool:
        """判断要素是否为道路"""
        highway = properties.get("highway", "")
        return highway in self.道路类型列表
    
    def 判断是否有名称(self, properties: Dict[str, Any]) -> bool:
        """判断要素是否有名称"""
        return "name" in properties and properties["name"] and properties["name"].strip() != ""
    
    def 判断是否为服务区内部道路(self, properties: Dict[str, Any]) -> bool:
        """判断是否为服务区内部道路"""
        # 检查service字段
        service_type = properties.get("service", "")
        服务区内部类型 = [
            "driveway", "parking_aisle", "alley", "emergency_access", 
            "site_access", "station_access", "station_aisle", "drive-through"
        ]
        
        # 检查highway类型为service且没有具体名称
        highway = properties.get("highway", "")
        if highway == "service" and service_type in 服务区内部类型:
            return True
        
        # 检查是否在服务区范围内（通过名称判断）
        name = properties.get("name", "").lower()
        if any(keyword in name for keyword in ["服务区", "service", "rest", "area"]):
            return True
        
        return False
    
    def 分类要素(self, feature: Dict[str, Any]) -> str:
        """对单个要素进行分类"""
        properties = feature.get("properties", {})
        
        是否有名称 = self.判断是否有名称(properties)
        是否为服务区内部道路 = self.判断是否为服务区内部道路(properties)
        
        # 4个分类：有/无名称 × 是/非服务区内部道路
        if 是否有名称 and 是否为服务区内部道路:
            return "有名称_服务区内部"
        elif 是否有名称 and not 是否为服务区内部道路:
            return "有名称_非服务区内部"
        elif not 是否有名称 and 是否为服务区内部道路:
            return "无名称_服务区内部"
        else:
            return "无名称_非服务区内部"
    
    def 处理GeoJSON文件(self, file_path: str):
        """处理GeoJSON文件并分类存储"""
        logger.info(f"开始处理文件: {file_path}")
        
        # 统计信息
        统计信息 = {
            "有名称_服务区内部": 0,
            "有名称_非服务区内部": 0,
            "无名称_服务区内部": 0,
            "无名称_非服务区内部": 0,
            "总处理数量": 0,
            "错误数量": 0
        }
        
        # 分类数据存储
        分类数据 = {
            "有名称_服务区内部": [],
            "有名称_非服务区内部": [],
            "无名称_服务区内部": [],
            "无名称_非服务区内部": []
        }
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                # 读取文件头部信息
                first_line = f.readline().strip()
                if not first_line.startswith('{'):
                    logger.error("文件格式错误，不是有效的JSON文件")
                    return False
                
                # 重新开始读取
                f.seek(0)
                content = f.read()
                
                # 解析JSON
                data = json.loads(content)
                
                if data.get("type") != "FeatureCollection":
                    logger.error("不是有效的GeoJSON FeatureCollection")
                    return False
                
                features = data.get("features", [])
                logger.info(f"文件包含 {len(features)} 个要素")
                
                # 处理每个要素（带进度条，边解析边存储）
                import time
                开始时间 = time.time()
                批次大小 = 1000  # 每1000个要素存储一次
                
                with tqdm(total=len(features), desc="王校长！处理要素", unit="个", 
                         bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]') as pbar:
                    for i, feature in enumerate(features):
                        try:
                            # 检查是否重复
                            if self.检查是否重复(feature):
                                统计信息["重复跳过"] = 统计信息.get("重复跳过", 0) + 1
                                pbar.set_postfix({
                                    "跳过": 统计信息.get("重复跳过", 0),
                                    "错误": 统计信息.get("错误数量", 0)
                                })
                                pbar.update(1)
                                continue
                            
                            分类结果 = self.分类要素(feature)
                            分类数据[分类结果].append(feature)
                            统计信息[分类结果] += 1
                            统计信息["总处理数量"] += 1
                            
                            # 将新要素ID添加到已存在集合中
                            唯一标识 = self.生成要素唯一标识(feature)
                            self.已存在要素ID.add(唯一标识)
                            
                            # 每处理1000个要素就存储一次
                            if (i + 1) % 批次大小 == 0:
                                self.存储分类数据到数据库(分类数据)
                                # 清空已存储的数据，避免重复
                                for 分类名称 in 分类数据:
                                    分类数据[分类名称] = []
                            
                            # 更新进度条
                            pbar.set_postfix({
                                "跳过": 统计信息.get("重复跳过", 0),
                                "错误": 统计信息.get("错误数量", 0)
                            })
                            pbar.update(1)
                                
                        except Exception as e:
                            logger.error(f"处理第 {i + 1} 个要素时出错: {e}")
                            统计信息["错误数量"] += 1
                            pbar.set_postfix({
                                "跳过": 统计信息.get("重复跳过", 0),
                                "错误": 统计信息.get("错误数量", 0)
                            })
                            pbar.update(1)
                    
                    # 处理剩余的数据
                    if 统计信息["总处理数量"] % 批次大小 != 0:
                        self.存储分类数据到数据库(分类数据)
                
                # 计算完成时间
                完成时间 = time.time()
                总耗时 = 完成时间 - 开始时间
                print(f"\n✅ 处理完成！总耗时: {总耗时:.2f}秒")
                
                # 打印统计结果
                self.打印统计结果(统计信息)
                
                return True
                
        except Exception as e:
            logger.error(f"处理文件时出错: {e}")
            return False
    
    def 存储分类数据到数据库(self, 分类数据: Dict[str, List]):
        """存储分类数据到数据库（边解析边存储，每条道路一个文档）"""
        try:
            集合名称 = os.getenv("MONGODB_COLLECTION_ROADS", "道路数据")
            
            # 每条道路存储为一个独立文档
            文档列表 = []
            for 分类名称, 要素列表 in 分类数据.items():
                for 要素 in 要素列表:
                    # 为每个要素创建独立文档
                    道路文档 = {
                        "type": "Feature",
                        "分类名称": 分类名称,
                        "创建时间": datetime.now(),
                        "properties": 要素.get("properties", {}),
                        "geometry": 要素.get("geometry", {}),
                        "id": 要素.get("id", "")
                    }
                    文档列表.append(道路文档)
            
            if 文档列表:
                # 批量插入所有道路文档
                result = self.db[集合名称].insert_many(文档列表)
                logger.info(f"存储 {len(文档列表)} 条道路数据, 文档ID范围: {result.inserted_ids[0]} - {result.inserted_ids[-1]}")
            
        except Exception as e:
            logger.error(f"存储分类数据到数据库时出错: {e}")
    
    def 存储到数据库(self, 分类数据: Dict[str, List], 统计信息: Dict[str, int]):
        """将分类数据存储到MongoDB"""
        try:
            # 统一存储到道路数据集合
            集合名称 = os.getenv("MONGODB_COLLECTION_ROADS", "道路数据")
            
            # 合并所有分类数据
            所有数据 = []
            
            for 分类名称, 要素列表 in 分类数据.items():
                if 要素列表:
                    所有数据.extend(要素列表)
                    logger.info(f"分类 '{分类名称}': {len(要素列表)} 个要素")
            
            # 按分类存储数据
            for 分类名称, 要素列表 in 分类数据.items():
                if 要素列表:
                    # 创建分类文档
                    分类文档 = {
                        "type": "FeatureCollection",
                        "分类名称": 分类名称,
                        "要素数量": len(要素列表),
                        "创建时间": datetime.now(),
                        "features": 要素列表
                    }
                    
                    result = self.db[集合名称].insert_one(分类文档)
                    logger.info(f"存储分类 '{分类名称}': {len(要素列表)} 个要素, 文档ID: {result.inserted_id}")
            
            logger.info(f"道路数据存储完成: 共 {len(所有数据)} 个要素, 分 {len([k for k, v in 分类数据.items() if v])} 个分类存储")
            
            # 打印统计结果
            self.打印统计结果(统计信息)
            
        except Exception as e:
            logger.error(f"存储到数据库时出错: {e}")
    
    def 打印统计结果(self, 统计信息: Dict[str, int]):
        """打印统计结果"""
        print("\n" + "="*60)
        print("王校长！道路分类统计结果")
        print("="*60)
        print(f"总处理数量: {统计信息['总处理数量']:,}")
        print(f"重复跳过: {统计信息.get('重复跳过', 0):,}")
        print(f"错误数量: {统计信息['错误数量']:,}")
        print("\n分类统计:")
        print(f"  有名称_服务区内部: {统计信息['有名称_服务区内部']:,} 个")
        print(f"  有名称_非服务区内部: {统计信息['有名称_非服务区内部']:,} 个")
        print(f"  无名称_服务区内部: {统计信息['无名称_服务区内部']:,} 个")
        print(f"  无名称_非服务区内部: {统计信息['无名称_非服务区内部']:,} 个")
        
        # 计算百分比
        总数 = 统计信息['总处理数量']
        if 总数 > 0:
            print("\n百分比统计:")
            for 分类, 数量 in 统计信息.items():
                if 分类 not in ['总处理数量', '错误数量']:
                    百分比 = (数量 / 总数) * 100
                    print(f"  {分类}: {百分比:.2f}%")
        
        print("="*60)
    
    def 查询分类数据(self):
        """查询分类数据"""
        try:
            集合名称 = "道路数据"
            
            # 查询所有数据
            结果 = list(self.db[集合名称].find())
            
            print(f"\n查询道路数据:")
            print(f"总文档数量: {len(结果)}")
            
            # 按分类统计
            分类统计 = {}
            for 文档 in 结果:
                分类名称 = 文档.get('分类名称', '未知')
                分类统计[分类名称] = 分类统计.get(分类名称, 0) + 1
            
            print(f"\n分类统计:")
            for 分类名称, 数量 in 分类统计.items():
                print(f"  {分类名称}: {数量} 条道路")
            
            # 显示前几条数据示例
            print(f"\n前5条数据示例:")
            for i, 文档 in enumerate(结果[:5]):
                print(f"  文档 {i+1}:")
                print(f"    分类名称: {文档.get('分类名称', 'N/A')}")
                print(f"    道路ID: {文档.get('id', 'N/A')}")
                print(f"    创建时间: {文档.get('创建时间', 'N/A')}")
                print(f"    属性数量: {len(文档.get('properties', {}))}")
                print("-" * 30)
            
            return 结果
            
        except Exception as e:
            logger.error(f"查询数据时出错: {e}")
            return []
    
    def 关闭连接(self):
        """关闭数据库连接"""
        if self.client:
            self.client.close()
            logger.info("数据库连接已关闭")

def main():
    """主函数"""
    print("王校长！开始道路数据分类和存储...")
    
    # 创建分类器
    分类器 = 道路分类器()
    
    # 连接数据库
    if not 分类器.连接数据库():
        return
    
    try:
        # 处理GeoJSON文件（从环境变量读取文件路径）
        文件路径 = os.getenv("GEOJSON_FILE_PATH", "map.geojson")
        成功 = 分类器.处理GeoJSON文件(文件路径)
        
        if 成功:
            print("\n王校长，道路分类和存储完成！")
            
            # 查询数据信息
            print("\n查询数据信息...")
            分类器.查询分类数据()
        else:
            print("处理失败！")
    
    finally:
        # 关闭连接
        分类器.关闭连接()

if __name__ == "__main__":
    main()
