"""
地图匹配算法测试
"""

import pytest
from BackendService.MatchingAlgorithms.base import GPSPoint, RoadSegment, DistanceMatchingAlgorithm


class TestDistanceMatchingAlgorithm:
    """最短距离匹配算法测试类"""
    
    def setup_method(self):
        """测试前准备"""
        self.algorithm = DistanceMatchingAlgorithm({
            'max_distance': 1000,
            'use_speed_filter': True,
            'max_speed': 200
        })
        
        # 创建测试道路段
        self.road_segments = [
            RoadSegment(
                segment_id="road_001",
                start_lat=39.9042,
                start_lon=116.4074,
                end_lat=39.9043,
                end_lon=116.4075,
                road_name="测试道路1",
                road_type="highway"
            ),
            RoadSegment(
                segment_id="road_002",
                start_lat=39.9044,
                start_lon=116.4076,
                end_lat=39.9045,
                end_lon=116.4077,
                road_name="测试道路2",
                road_type="primary"
            )
        ]
        
        # 加载道路网络
        self.algorithm.load_road_network(self.road_segments)
    
    def test_algorithm_initialization(self):
        """测试算法初始化"""
        assert self.algorithm.max_distance == 1000
        assert self.algorithm.use_speed_filter == True
        assert self.algorithm.max_speed == 200
        assert self.algorithm.get_algorithm_name() == "DistanceMatching"
    
    def test_load_road_network(self):
        """测试加载道路网络"""
        assert len(self.algorithm.road_segments) == 2
        assert self.algorithm.road_segments[0].segment_id == "road_001"
    
    def test_match_trajectory_success(self):
        """测试轨迹匹配成功"""
        # 创建GPS轨迹点
        gps_points = [
            GPSPoint(
                latitude=39.9042,
                longitude=116.4074,
                timestamp=0,
                speed=50.0,
                direction=90.0
            ),
            GPSPoint(
                latitude=39.9043,
                longitude=116.4075,
                timestamp=1,
                speed=55.0,
                direction=95.0
            )
        ]
        
        # 执行匹配
        results = self.algorithm.match_trajectory(gps_points)
        
        # 验证结果
        assert len(results) == 2
        assert results[0] is not None
        assert results[1] is not None
        assert results[0].matched_segment.segment_id == "road_001"
        assert results[0].confidence > 0
        assert results[0].distance < self.algorithm.max_distance
    
    def test_match_trajectory_with_speed_filter(self):
        """测试带速度过滤的轨迹匹配"""
        # 创建包含异常速度的GPS轨迹点
        gps_points = [
            GPSPoint(
                latitude=39.9042,
                longitude=116.4074,
                timestamp=0,
                speed=50.0,  # 正常速度
                direction=90.0
            ),
            GPSPoint(
                latitude=39.9043,
                longitude=116.4075,
                timestamp=1,
                speed=300.0,  # 异常速度，应该被过滤
                direction=95.0
            ),
            GPSPoint(
                latitude=39.9044,
                longitude=116.4076,
                timestamp=2,
                speed=60.0,  # 正常速度
                direction=100.0
            )
        ]
        
        # 执行匹配
        results = self.algorithm.match_trajectory(gps_points)
        
        # 验证结果（异常速度的点应该被过滤掉）
        assert len(results) == 2  # 只有2个正常速度的点
    
    def test_match_trajectory_no_road_network(self):
        """测试未加载道路网络时的错误处理"""
        algorithm = DistanceMatchingAlgorithm()
        
        gps_points = [
            GPSPoint(latitude=39.9042, longitude=116.4074, timestamp=0)
        ]
        
        with pytest.raises(ValueError, match="道路网络未加载"):
            algorithm.match_trajectory(gps_points)
    
    def test_get_statistics(self):
        """测试统计信息计算"""
        # 创建匹配结果
        results = [
            type('MatchResult', (), {
                'distance': 10.0,
                'confidence': 0.9
            })(),
            type('MatchResult', (), {
                'distance': 20.0,
                'confidence': 0.8
            })(),
            None  # 未匹配的点
        ]
        
        stats = self.algorithm.get_statistics(results)
        
        assert stats['total_points'] == 3
        assert stats['matched_points'] == 2
        assert stats['match_rate'] == 2/3
        assert stats['avg_distance'] == 15.0
        assert stats['avg_confidence'] == 0.85
        assert stats['min_distance'] == 10.0
        assert stats['max_distance'] == 20.0
    
    def test_get_statistics_empty(self):
        """测试空结果统计"""
        stats = self.algorithm.get_statistics([])
        
        assert stats['total_points'] == 0
        assert stats['matched_points'] == 0
        assert stats['match_rate'] == 0
        assert stats['avg_distance'] == 0
        assert stats['avg_confidence'] == 0
    
    def test_point_to_segment_distance(self):
        """测试点到线段距离计算"""
        # 测试点到线段的最短距离
        point_lat, point_lon = 39.9042, 116.4074
        segment = self.road_segments[0]
        
        distance, proj_lat, proj_lon = self.algorithm.point_to_segment_distance(
            point_lat, point_lon, segment
        )
        
        assert distance >= 0
        assert proj_lat is not None
        assert proj_lon is not None
    
    def test_calculate_distance(self):
        """测试距离计算"""
        # 测试相同点的距离
        distance = self.algorithm.calculate_distance(39.9042, 116.4074, 39.9042, 116.4074)
        assert distance == 0
        
        # 测试不同点的距离
        distance = self.algorithm.calculate_distance(39.9042, 116.4074, 39.9043, 116.4075)
        assert distance > 0
