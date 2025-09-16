"""
地理计算工具测试
"""

import pytest
from BackendService.UtilityTools.geo_utils import GeoUtils, Point, BoundingBox


class TestGeoUtils:
    """地理计算工具测试类"""
    
    def test_haversine_distance(self):
        """测试Haversine距离计算"""
        # 测试北京到上海的距离（约1067公里）
        beijing_lat, beijing_lon = 39.9042, 116.4074
        shanghai_lat, shanghai_lon = 31.2304, 121.4737
        
        distance = GeoUtils.haversine_distance(
            beijing_lat, beijing_lon, shanghai_lat, shanghai_lon
        )
        
        # 允许5%的误差
        expected_distance = 1067000  # 米
        assert abs(distance - expected_distance) / expected_distance < 0.05
    
    def test_point_to_line_distance(self):
        """测试点到线段距离计算"""
        # 测试点到线段的距离
        point_lat, point_lon = 0, 0
        line_start_lat, line_start_lon = 0, 1
        line_end_lat, line_end_lon = 0, 2
        
        distance, proj_lat, proj_lon = GeoUtils.point_to_line_distance(
            point_lat, point_lon, line_start_lat, line_start_lon, 
            line_end_lat, line_end_lon
        )
        
        # 点到线段的距离应该是1（经度差）
        assert abs(distance - 111320) < 1000  # 大约1度经度的米数
        assert proj_lat == 0
        assert proj_lon == 1
    
    def test_bearing(self):
        """测试方位角计算"""
        # 测试正北方向
        lat1, lon1 = 0, 0
        lat2, lon2 = 1, 0
        
        bearing = GeoUtils.bearing(lat1, lon1, lat2, lon2)
        assert abs(bearing - 0) < 1  # 正北方向
    
    def test_midpoint(self):
        """测试中点计算"""
        lat1, lon1 = 0, 0
        lat2, lon2 = 2, 2
        
        mid_lat, mid_lon = GeoUtils.midpoint(lat1, lon1, lat2, lon2)
        
        assert abs(mid_lat - 1) < 0.01
        assert abs(mid_lon - 1) < 0.01
    
    def test_bounding_box(self):
        """测试边界框计算"""
        points = [
            Point(39.9, 116.3),
            Point(40.0, 116.4),
            Point(39.95, 116.35)
        ]
        
        bbox = GeoUtils.calculate_bounding_box(points)
        
        assert bbox.min_lat == 39.9
        assert bbox.max_lat == 40.0
        assert bbox.min_lng == 116.3
        assert bbox.max_lng == 116.4
    
    def test_bounding_box_contains(self):
        """测试边界框包含检查"""
        bbox = BoundingBox(39.9, 40.0, 116.3, 116.4)
        
        # 在边界框内的点
        point_inside = Point(39.95, 116.35)
        assert bbox.contains(point_inside)
        
        # 在边界框外的点
        point_outside = Point(40.1, 116.5)
        assert not bbox.contains(point_outside)
    
    def test_trajectory_statistics(self):
        """测试轨迹统计计算"""
        points = [
            Point(39.9042, 116.4074, timestamp=0),
            Point(39.9043, 116.4075, timestamp=1),
            Point(39.9044, 116.4076, timestamp=2)
        ]
        
        stats = GeoUtils.calculate_trajectory_statistics(points)
        
        assert stats['total_points'] == 3
        assert stats['total_distance'] > 0
        assert stats['bounds'] is not None
    
    def test_coordinate_validation(self):
        """测试坐标验证"""
        # 有效坐标
        valid_point = Point(39.9042, 116.4074)
        assert valid_point.latitude == 39.9042
        assert valid_point.longitude == 116.4074
        
        # 无效坐标应该抛出异常
        with pytest.raises(ValueError):
            Point(91, 116.4074)  # 纬度超出范围
        
        with pytest.raises(ValueError):
            Point(39.9042, 181)  # 经度超出范围
    
    def test_bounding_box_validation(self):
        """测试边界框验证"""
        # 有效边界框
        valid_bbox = BoundingBox(39.9, 40.0, 116.3, 116.4)
        assert valid_bbox.min_lat == 39.9
        
        # 无效边界框应该抛出异常
        with pytest.raises(ValueError):
            BoundingBox(40.0, 39.9, 116.3, 116.4)  # 最小纬度大于最大纬度
