#!/usr/bin/env python3
"""
深圳边界数据获取和存储脚本
根据可行性文档，调用天地图行政区划API获取深圳市边界数据并存储到MongoDB
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from typing import Dict, List, Optional

import httpx
import pymongo
from bson import ObjectId
from shapely.geometry import MultiPolygon, Point, Polygon
from shapely.wkt import loads
from dotenv import load_dotenv

# 加载.env文件
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('../Logs/shenzhen_boundary.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class ShenzhenBoundaryService:
    """深圳市边界数据服务"""
    
    def __init__(self, mongodb_url: str = "mongodb://localhost:27017", database_name: str = "MapTools"):
        """初始化服务"""
        self.mongodb_url = mongodb_url
        self.database_name = database_name
        self.db_client = None
        self.db = None
        self.areas_collection = None
        
        # 获取天地图配置
        self.api_key = "a76af8af7a9db866b58634b60defd1b8"  # 浏览器端API密钥
        self.administrative_api_url = "http://api.tianditu.gov.cn/v2/administrative"
        
        if not self.api_key:
            raise ValueError("天地图API密钥未配置，请在.env文件中设置TIANDITU_API_KEY")
    
    async def connect_mongodb(self):
        """连接MongoDB数据库"""
        try:
            self.db_client = pymongo.MongoClient(self.mongodb_url)
            self.db = self.db_client[self.database_name]
            self.areas_collection = self.db.administrative_areas
            
            # 测试连接
            self.db_client.admin.command('ping')
            logger.info(f"成功连接到MongoDB: {self.mongodb_url}")
            
        except Exception as e:
            logger.error(f"连接MongoDB失败: {e}")
            raise
    
    async def get_shenzhen_boundary(self) -> Dict:
        """获取深圳市行政区划边界数据（从本地GeoJSON文件）"""
        logger.info("开始读取深圳市边界数据...")

        try:
            # 读取本地GeoJSON文件
            geojson_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "深圳市_市.geojson")
            
            with open(geojson_path, 'r', encoding='utf-8') as f:
                geojson_data = json.load(f)
            
            logger.info("成功读取本地GeoJSON文件")
            
            # 转换为API响应格式
            feature = geojson_data['features'][0]
            properties = feature['properties']
            geometry = feature['geometry']
            
            # 计算中心点
            coordinates = geometry['coordinates'][0][0]  # 第一个多边形的外环
            lng_sum = sum(coord[0] for coord in coordinates)
            lat_sum = sum(coord[1] for coord in coordinates)
            center_lng = lng_sum / len(coordinates)
            center_lat = lat_sum / len(coordinates)
            
            # 构建API响应格式
            api_response = {
                "status": 200,
                "message": "成功",
                "data": {
                    "district": [{
                        "gb": properties['gb'],
                        "name": properties['name'],
                        "level": 3,
                        "center": {
                            "lng": center_lng,
                            "lat": center_lat
                        },
                        "boundary": geometry
                    }]
                }
            }
            
            logger.info(f"成功解析边界数据: {properties['name']} (GB: {properties['gb']})")
            return api_response

        except FileNotFoundError:
            logger.error(f"GeoJSON文件不存在: {geojson_path}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"GeoJSON文件格式错误: {e}")
            raise
        except Exception as e:
            logger.error(f"读取深圳市边界数据失败: {e}")
            raise
    
    def _geometry_to_wkt(self, geometry: Dict) -> str:
        """将GeoJSON几何数据转换为WKT格式"""
        try:
            if geometry['type'] == 'MultiPolygon':
                polygons = []
                for polygon_coords in geometry['coordinates']:
                    # 外环
                    exterior = ', '.join([f"{coord[0]} {coord[1]}" for coord in polygon_coords[0]])
                    polygon_wkt = f"({exterior})"
                    polygons.append(polygon_wkt)
                
                return f"MULTIPOLYGON({', '.join(polygons)})"
            else:
                raise ValueError(f"不支持的几何类型: {geometry['type']}")
                
        except Exception as e:
            logger.error(f"几何数据转换失败: {e}")
            raise
    
    def parse_boundary_geometry(self, district_data: Dict) -> MultiPolygon:
        """解析边界几何数据"""
        try:
            boundary_geojson = district_data.get("boundary", {})
            if not boundary_geojson:
                raise ValueError("边界数据为空")

            # 直接使用GeoJSON格式构建MultiPolygon
            if boundary_geojson['type'] == 'MultiPolygon':
                polygons = []
                for polygon_coords in boundary_geojson['coordinates']:
                    # 外环坐标
                    exterior_coords = polygon_coords[0]
                    polygon = Polygon(exterior_coords)
                    polygons.append(polygon)
                
                geometry = MultiPolygon(polygons)
            else:
                raise ValueError(f"不支持的几何类型: {boundary_geojson['type']}")

            logger.info(f"成功解析边界几何数据，包含 {len(geometry.geoms)} 个多边形")
            return geometry

        except Exception as e:
            logger.error(f"解析边界几何数据失败: {e}")
            raise
    
    def create_boundary_document(self, district_data: Dict, boundary_geom: MultiPolygon) -> Dict:
        """创建边界数据文档"""
        try:
            # 提取中心点坐标
            center = district_data.get("center", {})
            
            # 将几何数据转换为GeoJSON格式
            geojson_geometry = {
                "type": "MultiPolygon",
                "coordinates": [list(polygon.exterior.coords) for polygon in boundary_geom.geoms]
            }
            
            document = {
                "_id": ObjectId(),
                "gb_code": district_data.get("gb", "156440300"),
                "name": district_data.get("name", "深圳市"),
                "level": district_data.get("level", 3),
                "boundary": geojson_geometry,
                "center": {
                    "lng": center.get("lng", 114.0579),
                    "lat": center.get("lat", 22.5431)
                },
                "created_at": datetime.now(),
                "updated_at": datetime.now(),
                "source": "tianditu_administrative_api",
                "api_version": "v2"
            }
            
            logger.info(f"创建边界文档: {document['name']} (GB: {document['gb_code']})")
            return document
            
        except Exception as e:
            logger.error(f"创建边界文档失败: {e}")
            raise
    
    async def save_boundary_to_mongodb(self, boundary_doc: Dict) -> str:
        """保存深圳市边界数据到MongoDB"""
        try:
            # 检查是否已存在相同GB代码的边界数据
            existing = self.areas_collection.find_one({"gb_code": boundary_doc["gb_code"]})
            
            if existing:
                # 更新现有数据
                boundary_doc["updated_at"] = datetime.now()
                result = self.areas_collection.update_one(
                    {"gb_code": boundary_doc["gb_code"]},
                    {"$set": boundary_doc}
                )
                logger.info(f"更新深圳市边界数据: {result.modified_count} 条记录")
                return str(existing["_id"])
            else:
                # 插入新数据
                result = self.areas_collection.insert_one(boundary_doc)
                logger.info(f"插入深圳市边界数据: {result.inserted_id}")
                return str(result.inserted_id)
                
        except Exception as e:
            logger.error(f"保存边界数据到MongoDB失败: {e}")
            raise
    
    async def create_spatial_index(self):
        """创建地理空间索引"""
        try:
            # 为boundary字段创建2dsphere索引
            self.areas_collection.create_index([("boundary", "2dsphere")])
            logger.info("成功创建boundary字段的2dsphere索引")
            
            # 为gb_code字段创建索引
            self.areas_collection.create_index([("gb_code", 1)])
            logger.info("成功创建gb_code字段索引")
            
            # 为level字段创建索引
            self.areas_collection.create_index([("level", 1)])
            logger.info("成功创建level字段索引")
            
        except Exception as e:
            logger.error(f"创建索引失败: {e}")
            raise
    
    async def verify_boundary_data(self, boundary_doc: Dict) -> bool:
        """验证边界数据的有效性"""
        try:
            # 检查必要字段
            required_fields = ["gb_code", "name", "boundary", "center"]
            for field in required_fields:
                if field not in boundary_doc:
                    logger.error(f"缺少必要字段: {field}")
                    return False
            
            # 验证几何数据
            boundary_geom = boundary_doc["boundary"]
            if boundary_geom["type"] != "MultiPolygon":
                logger.error(f"几何类型错误: {boundary_geom['type']}")
                return False
            
            # 验证中心点坐标
            center = boundary_doc["center"]
            if not isinstance(center.get("lng"), (int, float)) or not isinstance(center.get("lat"), (int, float)):
                logger.error("中心点坐标格式错误")
                return False
            
            # 验证坐标范围（深圳大致范围）
            lng, lat = center["lng"], center["lat"]
            if not (113.0 <= lng <= 115.0) or not (22.0 <= lat <= 23.0):
                logger.warning(f"中心点坐标可能不在深圳范围内: ({lng}, {lat})")
            
            logger.info("边界数据验证通过")
            return True
            
        except Exception as e:
            logger.error(f"验证边界数据失败: {e}")
            return False
    
    async def test_point_in_shenzhen(self, boundary_doc: Dict, test_points: List[Dict]) -> None:
        """测试点是否在深圳范围内"""
        try:
            # 重新构建几何对象用于测试
            boundary_geom = MultiPolygon([
                Polygon(coords) for coords in boundary_doc["boundary"]["coordinates"]
            ])
            
            logger.info("开始测试点是否在深圳范围内...")
            
            for i, point in enumerate(test_points):
                point_geom = Point(point["lng"], point["lat"])
                is_inside = boundary_geom.contains(point_geom)
                
                status = "在深圳内" if is_inside else "不在深圳内"
                logger.info(f"测试点 {i+1}: ({point['lng']}, {point['lat']}) - {status}")
                
        except Exception as e:
            logger.error(f"测试点范围失败: {e}")
    
    async def run(self):
        """运行主流程"""
        try:
            logger.info("=== 深圳边界数据获取和存储开始 ===")
            
            # 连接MongoDB
            await self.connect_mongodb()
            
            # 获取深圳市边界数据
            api_data = await self.get_shenzhen_boundary()
            
            # 解析边界几何数据
            district_data = api_data["data"]["district"][0]
            boundary_geom = self.parse_boundary_geometry(district_data)
            
            # 创建边界文档
            boundary_doc = self.create_boundary_document(district_data, boundary_geom)
            
            # 验证边界数据
            if not await self.verify_boundary_data(boundary_doc):
                raise Exception("边界数据验证失败")
            
            # 保存到MongoDB
            doc_id = await self.save_boundary_to_mongodb(boundary_doc)
            
            # 创建索引
            await self.create_spatial_index()
            
            # 测试点范围验证
            test_points = [
                {"lng": 114.0579, "lat": 22.5431},  # 深圳中心
                {"lng": 113.0000, "lat": 23.0000},  # 不在深圳
                {"lng": 114.1000, "lat": 22.6000},  # 在深圳
                {"lng": 115.0000, "lat": 25.0000},  # 不在深圳
            ]
            await self.test_point_in_shenzhen(boundary_doc, test_points)
            
            logger.info(f"=== 深圳边界数据获取和存储完成，文档ID: {doc_id} ===")
            
        except Exception as e:
            logger.error(f"运行失败: {e}")
            raise
        finally:
            if self.db_client:
                self.db_client.close()
                logger.info("MongoDB连接已关闭")


async def main():
    """主函数"""
    try:
        # 从环境变量获取MongoDB配置
        mongodb_url = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
        database_name = os.getenv("MONGODB_DATABASE", "MapTools")
        
        # 创建服务实例
        service = ShenzhenBoundaryService(mongodb_url, database_name)
        
        # 运行服务
        await service.run()
        
    except Exception as e:
        logger.error(f"程序执行失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
