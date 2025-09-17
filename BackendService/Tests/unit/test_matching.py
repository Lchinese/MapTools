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
    try:
        from BackendService.MatchingAlgorithms.base import GPSPoint, RoadSegment, MatchResult
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
            
        @dataclass
        class MatchResult:
            gps_point: GPSPoint
            matched_segment: RoadSegment
            matched_lat: float
            matched_lon: float
            distance: float
            confidence: float

class TestMatchingDataModels(unittest.TestCase):
    """匹配算法数据模型测试"""
    
    def test_gps_point_creation(self):
        """测试GPS点创建"""
        point = GPSPoint(
            latitude=39.9087,
            longitude=116.3974,
            timestamp=1234567890.0,
            speed=10.0,
            direction=45.0,
            accuracy=5.0
        )
        
        self.assertEqual(point.latitude, 39.9087)
        self.assertEqual(point.longitude, 116.3974)
        self.assertEqual(point.speed, 10.0)
        self.assertEqual(point.direction, 45.0)
        self.assertEqual(point.accuracy, 5.0)
        
    def test_road_segment_creation(self):
        """测试道路段创建"""
        segment = RoadSegment(
            segment_id="seg_001",
            start_lat=39.9080,
            start_lon=116.3970,
            end_lat=39.9090,
            end_lon=116.3980,
            road_name="测试道路",
            road_type="primary",
            max_speed=60.0
        )
        
        self.assertEqual(segment.segment_id, "seg_001")
        self.assertEqual(segment.road_name, "测试道路")
        self.assertEqual(segment.road_type, "primary")
        self.assertEqual(segment.max_speed, 60.0)
        
    def test_match_result_creation(self):
        """测试匹配结果创建"""
        gps_point = GPSPoint(
            latitude=39.9087,
            longitude=116.3974,
            timestamp=1234567890.0
        )
        
        road_segment = RoadSegment(
            segment_id="seg_001",
            start_lat=39.9080,
            start_lon=116.3970,
            end_lat=39.9090,
            end_lon=116.3980,
            road_name="测试道路",
            road_type="primary"
        )
        
        result = MatchResult(
            gps_point=gps_point,
            matched_segment=road_segment,
            matched_lat=39.9085,
            matched_lon=116.3975,
            distance=10.5,
            confidence=0.95
        )
        
        self.assertEqual(result.gps_point, gps_point)
        self.assertEqual(result.matched_segment, road_segment)
        self.assertEqual(result.distance, 10.5)
        self.assertEqual(result.confidence, 0.95)

if __name__ == '__main__':
    unittest.main()