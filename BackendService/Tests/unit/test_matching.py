"""
匹配算法单元测试
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
    from MatchingAlgorithms.base import GPSPoint, RoadSegment, MatchResult
except ImportError:
    from BackendService.MatchingAlgorithms.base import GPSPoint, RoadSegment, MatchResult

class TestMatchingDataModels(unittest.TestCase):
    """匹配算法数据模型测试"""
    
    def setUp(self):
        """测试前的准备工作"""
        # 创建GPS点
        self.gps_point = GPSPoint(
            latitude=39.9087,
            longitude=116.3974,
            timestamp=1000,
            speed=10.0,
            direction=45.0,
            accuracy=5.0
        )
        
        # 创建道路段
        self.road_segment = RoadSegment(
            segment_id="seg_001",
            start_lat=39.9080,
            start_lon=116.3970,
            end_lat=39.9090,
            end_lon=116.3980,
            road_name="测试道路",
            road_type="primary",
            max_speed=60.0
        )
        
        # 创建匹配结果
        self.match_result = MatchResult(
            gps_point=self.gps_point,
            matched_segment=self.road_segment,
            matched_lat=39.9085,
            matched_lon=116.3975,
            distance=5.0,
            confidence=0.95
        )
        
    def test_gps_point_creation(self):
        """测试GPS点创建"""
        gps_point = GPSPoint(
            latitude=39.9087,
            longitude=116.3974,
            timestamp=1000,
            speed=10.0,
            direction=45.0,
            accuracy=5.0
        )
        
        self.assertEqual(gps_point.latitude, 39.9087)
        self.assertEqual(gps_point.longitude, 116.3974)
        self.assertEqual(gps_point.timestamp, 1000)
        self.assertEqual(gps_point.speed, 10.0)
        self.assertEqual(gps_point.direction, 45.0)
        self.assertEqual(gps_point.accuracy, 5.0)
        
    def test_road_segment_creation(self):
        """测试道路段创建"""
        road_segment = RoadSegment(
            segment_id="seg_001",
            start_lat=39.9080,
            start_lon=116.3970,
            end_lat=39.9090,
            end_lon=116.3980,
            road_name="测试道路",
            road_type="primary",
            max_speed=60.0
        )
        
        self.assertEqual(road_segment.segment_id, "seg_001")
        self.assertEqual(road_segment.start_lat, 39.9080)
        self.assertEqual(road_segment.start_lon, 116.3970)
        self.assertEqual(road_segment.end_lat, 39.9090)
        self.assertEqual(road_segment.end_lon, 116.3980)
        self.assertEqual(road_segment.road_name, "测试道路")
        self.assertEqual(road_segment.road_type, "primary")
        self.assertEqual(road_segment.max_speed, 60.0)
        
    def test_match_result_creation(self):
        """测试匹配结果创建"""
        match_result = MatchResult(
            gps_point=self.gps_point,
            matched_segment=self.road_segment,
            matched_lat=39.9085,
            matched_lon=116.3975,
            distance=5.0,
            confidence=0.95
        )
        
        self.assertEqual(match_result.gps_point, self.gps_point)
        self.assertEqual(match_result.matched_segment, self.road_segment)
        self.assertEqual(match_result.matched_lat, 39.9085)
        self.assertEqual(match_result.matched_lon, 116.3975)
        self.assertEqual(match_result.distance, 5.0)
        self.assertEqual(match_result.confidence, 0.95)

if __name__ == '__main__':
    unittest.main()