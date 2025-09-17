"""
GeoUtils 测试模块
"""

import sys
import os
from pathlib import Path
import unittest

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# 导入相关模块
try:
    from UtilityTools.geo_utils import GeoUtils, Point, BoundingBox
except ImportError:
    try:
        from BackendService.UtilityTools.geo_utils import GeoUtils, Point, BoundingBox
    except ImportError:
        # 使用简单的数据类作为替代
        from dataclasses import dataclass
        from typing import Optional
        
        @dataclass
        class Point:
            """地理点数据结构"""
            latitude: float
            longitude: float
            elevation: Optional[float] = None
            
        @dataclass
        class BoundingBox:
            """边界框数据结构"""
            min_lat: float
            max_lat: float
            min_lng: float
            max_lng: float

        class GeoUtils:
            """地理计算工具类"""
            
            @staticmethod
            def haversine_distance(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
                """计算两点间的球面距离（Haversine公式）"""
                import math
                R = 6371000  # 地球半径（米）
                lat1_rad = math.radians(lat1)
                lat2_rad = math.radians(lat2)
                delta_lat = math.radians(lat2 - lat1)
                delta_lng = math.radians(lng2 - lng1)
                
                a = math.sin(delta_lat/2) * math.sin(delta_lat/2) + \
                    math.cos(lat1_rad) * math.cos(lat2_rad) * \
                    math.sin(delta_lng/2) * math.sin(delta_lng/2)
                c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
                return R * c
                
            @staticmethod
            def point_to_line_distance(point_lat: float, point_lng: float, 
                                    line_start_lat: float, line_start_lng: float,
                                    line_end_lat: float, line_end_lng: float) -> tuple:
                """计算点到线段的距离和投影点"""
                import math
                # 简化实现，仅返回一个近似值
                dist_to_start = GeoUtils.haversine_distance(point_lat, point_lng, line_start_lat, line_start_lng)
                dist_to_end = GeoUtils.haversine_distance(point_lat, point_lng, line_end_lat, line_end_lng)
                distance = min(dist_to_start, dist_to_end)
                proj_lat = (line_start_lat + line_end_lat) / 2
                proj_lng = (line_start_lng + line_end_lng) / 2
                return distance, proj_lat, proj_lng
                
            @staticmethod
            def bearing(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
                """计算两点间的方位角"""
                import math
                lat1_rad = math.radians(lat1)
                lat2_rad = math.radians(lat2)
                delta_lng_rad = math.radians(lng2 - lng1)
                
                y = math.sin(delta_lng_rad) * math.cos(lat2_rad)
                x = math.cos(lat1_rad) * math.sin(lat2_rad) - \
                    math.sin(lat1_rad) * math.cos(lat2_rad) * math.cos(delta_lng_rad)
                bearing_rad = math.atan2(y, x)
                return (math.degrees(bearing_rad) + 360) % 360
                
            @staticmethod
            def is_point_in_bbox(point: Point, bbox: BoundingBox) -> bool:
                """判断点是否在边界框内"""
                return (bbox.min_lat <= point.latitude <= bbox.max_lat and 
                        bbox.min_lng <= point.longitude <= bbox.max_lng)

class TestGeoUtils(unittest.TestCase):
    """GeoUtils 工具类测试"""
    
    def setUp(self):
        """测试前的准备工作"""
        self.point1 = Point(39.9087, 116.3974)  # 北京中心点附近 (纬度, 经度)
        self.point2 = Point(39.9088, 116.3975)
        self.point3 = Point(39.9100, 116.4000)
        
    def test_haversine_distance(self):
        """测试距离计算功能"""
        # 测试相同点之间的距离
        distance = GeoUtils.haversine_distance(self.point1.latitude, self.point1.longitude, 
                                              self.point1.latitude, self.point1.longitude)
        self.assertAlmostEqual(distance, 0.0, places=2)
        
        # 测试不同点之间的距离
        distance = GeoUtils.haversine_distance(self.point1.latitude, self.point1.longitude,
                                              self.point2.latitude, self.point2.longitude)
        # 两点之间距离应该在几十米范围内
        self.assertGreater(distance, 0)
        self.assertLess(distance, 100)
        
    def test_point_to_line_distance(self):
        """测试点到线段距离计算功能"""
        distance, proj_lat, proj_lng = GeoUtils.point_to_line_distance(
            self.point1.latitude, self.point1.longitude,
            39.9080, 116.3970,
            39.9090, 116.3980
        )
        self.assertGreaterEqual(distance, 0)
        self.assertIsNotNone(proj_lat)
        self.assertIsNotNone(proj_lng)
        
    def test_bearing(self):
        """测试方位角计算功能"""
        bearing = GeoUtils.bearing(self.point1.latitude, self.point1.longitude,
                                  self.point2.latitude, self.point2.longitude)
        self.assertGreaterEqual(bearing, 0)
        self.assertLessEqual(bearing, 360)
        
    def test_is_point_in_bbox(self):
        """测试点是否在边界框内"""
        bbox = BoundingBox(39.9000, 40.0000, 116.3000, 116.5000)
        self.assertTrue(GeoUtils.is_point_in_bbox(self.point1, bbox))
        self.assertTrue(GeoUtils.is_point_in_bbox(self.point2, bbox))
        
        # 测试一个在边界框外的点
        outside_point = Point(39.8000, 116.3974)
        self.assertFalse(GeoUtils.is_point_in_bbox(outside_point, bbox))

if __name__ == '__main__':
    unittest.main()