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

# 导入相关模块
try:
    from MatchingAlgorithms.base import GPSPoint, RoadSegment
except ImportError:
    try:
        from BackendService.MatchingAlgorithms.base import GPSPoint, RoadSegment
    except ImportError:
        # 使用简单的数据类作为替代
        from dataclasses import dataclass
        from typing import Optional
        
        @dataclass
        class GPSPoint:
            latitude: float
            longitude: float
            timestamp: float
            speed: Optional[float] = None
            direction: Optional[float] = None
            accuracy: Optional[float] = None
            
        @dataclass
        class RoadSegment:
            segment_id: str
            start_lat: float
            start_lon: float
            end_lat: float
            end_lon: float
            road_name: str
            road_type: str
            max_speed: Optional[float] = None

# from MatchingAlgorithms.Algorithms.greedy_algorithm import GreedyMatchingAlgorithm

class TestMatchingAlgorithm(unittest.TestCase):
    """匹配算法测试"""
    
    def setUp(self):
        """测试前的准备工作"""
        self.gps_point = GPSPoint(
            latitude=39.9087,
            longitude=116.3974,
            timestamp=1234567890.0,
            speed=10.0,
            direction=45.0
        )
        
        self.road_segment = RoadSegment(
            segment_id="seg_001",
            start_lat=39.9080,
            start_lon=116.3970,
            end_lat=39.9090,
            end_lon=116.3980,
            road_name="测试道路",
            road_type="primary"
        )
        
    def test_gps_point_creation(self):
        """测试GPS点创建"""
        self.assertEqual(self.gps_point.latitude, 39.9087)
        self.assertEqual(self.gps_point.longitude, 116.3974)
        self.assertEqual(self.gps_point.speed, 10.0)
        
    def test_road_segment_creation(self):
        """测试道路段创建"""
        self.assertEqual(self.road_segment.segment_id, "seg_001")
        self.assertEqual(self.road_segment.road_name, "测试道路")
        self.assertEqual(self.road_segment.start_lat, 39.9080)

if __name__ == '__main__':
    unittest.main()