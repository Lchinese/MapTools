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

from UtilityTools.geo_utils import GeoUtils, Point, BoundingBox

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
        # 由于是相邻点，距离应该很小
        self.assertGreater(distance, 0)
        self.assertLess(distance, 100)  # 假设距离小于100米
        
    def test_is_point_in_bbox(self):
        """测试点是否在边界框内"""
        # 创建一个边界框
        bbox = BoundingBox(39.9000, 39.9200, 116.3900, 116.4100)
        
        # 测试在边界框内的点
        inside_point = Point(39.9087, 116.3974)
        self.assertTrue(bbox.contains(inside_point))
        
        # 测试在边界框外的点
        outside_point = Point(39.8900, 116.3800)
        self.assertFalse(bbox.contains(outside_point))
        
    def test_bearing(self):
        """测试方位角计算"""
        # 简单测试方位角计算
        bearing = GeoUtils.bearing(self.point1.latitude, self.point1.longitude,
                                  self.point2.latitude, self.point2.longitude)
        self.assertIsInstance(bearing, float)
        self.assertGreaterEqual(bearing, 0)
        self.assertLessEqual(bearing, 360)
        
    def test_point_to_line_distance(self):
        """测试点到线段的距离计算"""
        # 创建一个线段
        segment_start = Point(39.9080, 116.3970)
        segment_end = Point(39.9090, 116.3980)
        
        # 计算点到线段的距离
        distance, proj_lat, proj_lon = GeoUtils.point_to_line_distance(
            self.point1.latitude, self.point1.longitude,
            segment_start.latitude, segment_start.longitude,
            segment_end.latitude, segment_end.longitude)
        self.assertIsInstance(distance, float)
        self.assertIsInstance(proj_lat, float)
        self.assertIsInstance(proj_lon, float)
        
if __name__ == '__main__':
    unittest.main()