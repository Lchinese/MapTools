"""
路网匹配功能单元测试
测试道路匹配算法的核心功能
"""

import unittest
import sys
import os
from unittest.mock import Mock, patch

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from UtilityTools.road_matching import RoadMatcher
from UtilityTools.tianditu_wfs_service import TiandituWFSService

class TestRoadMatcher(unittest.TestCase):
    """道路匹配器测试"""
    
    def setUp(self):
        """设置测试环境"""
        # 使用模拟的道路数据
        self.mock_roads = [
            {
                'id': 'road_1',
                'name': '深南大道',
                'type': '主要道路',
                'points': [
                    (114.0, 22.5),
                    (114.1, 22.5),
                    (114.2, 22.5)
                ],
                'length': 1000.0
            },
            {
                'id': 'road_2',
                'name': '滨海大道',
                'type': '主要道路',
                'points': [
                    (114.0, 22.6),
                    (114.1, 22.6),
                    (114.2, 22.6)
                ],
                'length': 1000.0
            }
        ]
    
    def test_calculate_distance(self):
        """测试距离计算"""
        matcher = RoadMatcher()
        
        # 测试相同点
        distance = matcher.calculate_distance((114.0, 22.5), (114.0, 22.5))
        self.assertEqual(distance, 0.0, "相同点距离应该为0")
        
        # 测试不同点
        distance = matcher.calculate_distance((114.0, 22.5), (114.1, 22.5))
        self.assertGreater(distance, 0, "不同点距离应该大于0")
        self.assertLess(distance, 20000, "距离应该在合理范围内")
    
    def test_point_to_line_distance(self):
        """测试点到线段距离计算"""
        matcher = RoadMatcher()
        
        # 测试点到线段中点的距离
        point = (114.05, 22.5)
        line_start = (114.0, 22.5)
        line_end = (114.1, 22.5)
        
        distance, closest_point = matcher.point_to_line_distance(point, line_start, line_end)
        
        self.assertGreater(distance, 0, "距离应该大于0")
        self.assertIsInstance(closest_point, tuple, "最近点应该是元组")
        self.assertEqual(len(closest_point), 2, "最近点应该有两个坐标")
    
    def test_find_closest_road_point(self):
        """测试查找最近道路点"""
        # 模拟道路数据
        with patch.object(RoadMatcher, '__init__', lambda x: None):
            matcher = RoadMatcher()
            matcher.roads = self.mock_roads
            
            # 测试查找最近道路点
            gps_point = (114.05, 22.5)
            result = matcher.find_closest_road_point(gps_point)
            
            self.assertIn('road', result, "结果应该包含道路信息")
            self.assertIn('matched_point', result, "结果应该包含匹配点")
            self.assertIn('distance', result, "结果应该包含距离")
            self.assertIsInstance(result['distance'], (int, float), "距离应该是数字")
    
    def test_match_gps_to_roads(self):
        """测试GPS点匹配到道路"""
        # 模拟道路数据
        with patch.object(RoadMatcher, '__init__', lambda x: None):
            matcher = RoadMatcher()
            matcher.roads = self.mock_roads
            
            # 测试GPS点数据
            gps_points = [
                {
                    'id': 1,
                    'longitude': 114.05,
                    'latitude': 22.5,
                    'plate_number': '粤B12345',
                    'datetime': '2023-10-01T08:00:00',
                    'speed': 60,
                    'heading': 90,
                    'is_valid': True
                },
                {
                    'id': 2,
                    'longitude': 114.15,
                    'latitude': 22.6,
                    'plate_number': '粤B67890',
                    'datetime': '2023-10-01T08:01:00',
                    'speed': 50,
                    'heading': 180,
                    'is_valid': True
                }
            ]
            
            # 执行匹配
            matched_points = matcher.match_gps_to_roads(gps_points)
            
            self.assertEqual(len(matched_points), len(gps_points), "匹配结果数量应该与输入相同")
            
            for matched_point in matched_points:
                self.assertIn('original_gps', matched_point, "结果应该包含原始GPS数据")
                self.assertIn('matched_longitude', matched_point, "结果应该包含匹配经度")
                self.assertIn('matched_latitude', matched_point, "结果应该包含匹配纬度")
                self.assertIn('road_id', matched_point, "结果应该包含道路ID")
                self.assertIn('road_name', matched_point, "结果应该包含道路名称")
                self.assertIn('distance_to_road', matched_point, "结果应该包含到道路的距离")

class TestTiandituWFSService(unittest.TestCase):
    """天地图WFS服务测试"""
    
    def setUp(self):
        """设置测试环境"""
        self.service = TiandituWFSService()
    
    def test_haversine_distance(self):
        """测试Haversine距离计算"""
        # 测试相同点
        distance = self.service._haversine_distance(114.0, 22.5, 114.0, 22.5)
        self.assertEqual(distance, 0.0, "相同点距离应该为0")
        
        # 测试不同点
        distance = self.service._haversine_distance(114.0, 22.5, 114.1, 22.5)
        self.assertGreater(distance, 0, "不同点距离应该大于0")
        self.assertLess(distance, 20000, "距离应该在合理范围内")
    
    def test_extract_road_name(self):
        """测试提取道路名称"""
        # 测试有名称的情况
        properties = {'NAME': '深南大道'}
        name = self.service._extract_road_name(properties)
        self.assertEqual(name, '深南大道', "应该正确提取道路名称")
        
        # 测试无名称的情况
        properties = {}
        name = self.service._extract_road_name(properties)
        self.assertEqual(name, '未命名道路', "无名称时应该返回默认值")
    
    def test_extract_road_type(self):
        """测试提取道路类型"""
        # 测试有类型的情况
        properties = {'TYPE': '主要道路'}
        road_type = self.service._extract_road_type(properties, 'LRDL')
        self.assertEqual(road_type, '主要道路', "应该正确提取道路类型")
        
        # 测试无类型的情况
        properties = {}
        road_type = self.service._extract_road_type(properties, 'LRDL')
        self.assertEqual(road_type, '主要道路', "无类型时应该根据图层推断")
    
    def test_calculate_road_length(self):
        """测试计算道路长度"""
        # 测试直线道路
        points = [(114.0, 22.5), (114.1, 22.5)]
        length = self.service._calculate_road_length(points)
        self.assertGreater(length, 0, "道路长度应该大于0")
        
        # 测试单点道路
        points = [(114.0, 22.5)]
        length = self.service._calculate_road_length(points)
        self.assertEqual(length, 0.0, "单点道路长度应该为0")
    
    def test_create_road_from_coordinates(self):
        """测试从坐标创建道路对象"""
        coordinates = [[114.0, 22.5], [114.1, 22.5]]
        properties = {'NAME': '深南大道', 'TYPE': '主要道路'}
        feature_id = 'feature_123'
        layer_name = 'LRDL'
        
        road = self.service._create_road_from_coordinates(
            coordinates, properties, feature_id, layer_name
        )
        
        self.assertIsNotNone(road, "应该成功创建道路对象")
        self.assertEqual(road['name'], '深南大道', "道路名称应该正确")
        self.assertEqual(road['type'], '主要道路', "道路类型应该正确")
        self.assertEqual(len(road['points']), 2, "道路点数量应该正确")
        self.assertGreater(road['length'], 0, "道路长度应该大于0")
    
    def test_get_road_statistics(self):
        """测试获取道路统计信息"""
        roads = [
            {
                'id': 'road_1',
                'name': '深南大道',
                'type': '主要道路',
                'length': 1000.0,
                'layer': 'LRDL'
            },
            {
                'id': 'road_2',
                'name': '滨海大道',
                'type': '主要道路',
                'length': 2000.0,
                'layer': 'LRDL'
            }
        ]
        
        stats = self.service.get_road_statistics(roads)
        
        self.assertEqual(stats['total_roads'], 2, "总道路数应该正确")
        self.assertEqual(stats['total_length'], 3000.0, "总长度应该正确")
        self.assertEqual(stats['average_length'], 1500.0, "平均长度应该正确")
        self.assertIn('主要道路', stats['road_types'], "道路类型统计应该正确")
        self.assertIn('LRDL', stats['layers'], "图层统计应该正确")

class TestRoadMatchingIntegration(unittest.TestCase):
    """道路匹配集成测试"""
    
    def test_full_matching_workflow(self):
        """测试完整的匹配工作流程"""
        # 模拟GPS点数据
        gps_points = [
            {
                'id': 1,
                'longitude': 114.05,
                'latitude': 22.5,
                'plate_number': '粤B12345',
                'datetime': '2023-10-01T08:00:00',
                'speed': 60,
                'heading': 90,
                'is_valid': True
            }
        ]
        
        # 模拟道路数据
        mock_roads = [
            {
                'id': 'road_1',
                'name': '深南大道',
                'type': '主要道路',
                'points': [
                    (114.0, 22.5),
                    (114.1, 22.5)
                ],
                'length': 1000.0
            }
        ]
        
        # 使用模拟数据创建匹配器
        with patch.object(RoadMatcher, '__init__', lambda x: None):
            matcher = RoadMatcher()
            matcher.roads = mock_roads
            
            # 执行匹配
            matched_points = matcher.match_gps_to_roads(gps_points)
            
            # 验证结果
            self.assertEqual(len(matched_points), 1, "应该有一个匹配结果")
            
            matched_point = matched_points[0]
            self.assertEqual(matched_point['road_name'], '深南大道', "应该匹配到正确的道路")
            self.assertGreater(matched_point['distance_to_road'], 0, "距离应该大于0")

def run_road_matching_tests():
    """运行道路匹配测试"""
    print("=== 道路匹配功能单元测试 ===")
    
    # 创建测试套件
    suite = unittest.TestSuite()
    
    # 添加测试类
    test_classes = [
        TestRoadMatcher,
        TestTiandituWFSService,
        TestRoadMatchingIntegration
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 输出结果
    print(f"\n测试结果:")
    print(f"  运行测试: {result.testsRun}")
    print(f"  失败: {len(result.failures)}")
    print(f"  错误: {len(result.errors)}")
    print(f"  成功率: {(result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100:.2f}%")
    
    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_road_matching_tests()
    exit(0 if success else 1)
