"""
匹配算法测试模块
"""

import sys
import os
from pathlib import Path
import unittest

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from MatchingAlgorithms.base import GPSPoint, RoadSegment
# from MatchingAlgorithms.Algorithms.greedy_algorithm import GreedyMatchingAlgorithm

class TestMatchingAlgorithm(unittest.TestCase):
    """匹配算法测试"""
    
    def setUp(self):
        """测试前的准备工作"""
        # 创建GPS点列表
        self.gps_points = [
            GPSPoint(39.9087, 116.3974, 1),
            GPSPoint(39.9088, 116.3975, 2),
            GPSPoint(39.9089, 116.3976, 3)
        ]
        
        # 创建道路线段列表
        self.road_segments = [
            RoadSegment("1", 39.9080, 116.3970, 39.9090, 116.3980),
            RoadSegment("2", 39.9090, 116.3980, 39.9100, 116.3990)
        ]
        
    def test_gps_point_creation(self):
        """测试GPS点创建"""
        point = GPSPoint(39.9087, 116.3974, 1)
        self.assertEqual(point.latitude, 39.9087)
        self.assertEqual(point.longitude, 116.3974)
        self.assertEqual(point.timestamp, 1)
        
    def test_road_segment_creation(self):
        """测试道路线段创建"""
        segment = RoadSegment("1", 39.9080, 116.3970, 39.9090, 116.3980)
        self.assertEqual(segment.segment_id, "1")
        self.assertEqual(segment.start_lat, 39.9080)
        self.assertEqual(segment.start_lon, 116.3970)
        self.assertEqual(segment.end_lat, 39.9090)
        self.assertEqual(segment.end_lon, 116.3980)

if __name__ == '__main__':
    unittest.main()
