"""
地图匹配业务服务
提供轨迹匹配的业务逻辑
"""

from typing import List, Dict, Any, Optional
import time
from MatchingAlgorithms.base import create_matching_algorithm, get_default_config
from MatchingAlgorithms.base import GPSPoint, RoadSegment, MatchResult
from UtilityTools.geo_utils import GeoUtils


class MatchingService:
    """地图匹配业务服务"""
    
    def __init__(self, algorithm_type: str = 'distance_matching', config: Dict[str, Any] = None):
        """
        初始化匹配服务
        
        Args:
            algorithm_type: 算法类型
            config: 算法配置参数
        """
        self.algorithm_type = algorithm_type
        self.config = config or get_default_config(algorithm_type)
        self.algorithm = create_matching_algorithm(algorithm_type, self.config)
        self.road_network_loaded = False
    
    def load_road_network(self, road_data: List[Dict[str, Any]]) -> None:
        """
        加载道路网络数据
        
        Args:
            road_data: 道路数据列表，每个元素包含道路段信息
        """
        # 转换数据格式
        road_segments = []
        for road in road_data:
            segment = RoadSegment(
                segment_id=road.get('segment_id', ''),
                start_lat=road.get('start_lat', 0),
                start_lon=road.get('start_lon', 0),
                end_lat=road.get('end_lat', 0),
                end_lon=road.get('end_lon', 0),
                road_name=road.get('road_name', ''),
                road_type=road.get('road_type', ''),
                max_speed=road.get('max_speed', None)
            )
            road_segments.append(segment)
        
        self.algorithm.load_road_network(road_segments)
        self.road_network_loaded = True
    
    def match_trajectory(self, gps_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        匹配GPS轨迹到道路网络
        
        Args:
            gps_data: GPS轨迹数据列表
            
        Returns:
            Dict[str, Any]: 匹配结果
        """
        if not self.road_network_loaded:
            raise ValueError("道路网络未加载，请先调用 load_road_network()")
        
        # 转换GPS数据格式
        gps_points = []
        for point_data in gps_data:
            from ..MatchingAlgorithms.base import GPSPoint
            gps_point = GPSPoint(
                latitude=point_data['latitude'],
                longitude=point_data['longitude'],
                timestamp=point_data.get('timestamp', 0),
                speed=point_data.get('speed'),
                direction=point_data.get('direction'),
                accuracy=point_data.get('accuracy')
            )
            gps_points.append(gps_point)
        
        # 执行匹配
        start_time = time.time()
        results = self.algorithm.match_trajectory(gps_points)
        processing_time = time.time() - start_time
        
        # 计算统计信息
        statistics = self.algorithm.get_statistics(results)
        statistics['processing_time'] = processing_time
        
        # 转换结果格式
        matched_points = []
        for result in results:
            if result:
                matched_points.append({
                    'original_lat': result.gps_point.latitude,
                    'original_lng': result.gps_point.longitude,
                    'matched_lat': result.matched_lat,
                    'matched_lng': result.matched_lon,
                    'road_id': result.matched_segment.segment_id,
                    'road_name': result.matched_segment.road_name,
                    'confidence': result.confidence,
                    'distance': result.distance
                })
        
        return {
            'matched_points': matched_points,
            'statistics': statistics,
            'algorithm': self.algorithm_type,
            'parameters': self.config
        }
        """
        匹配GPS轨迹
        
        Args:
            gps_data: GPS数据列表，每个元素包含轨迹点信息
            
        Returns:
            匹配结果字典
        """
        if not self.road_network_loaded:
            raise ValueError("道路网络未加载，请先调用 load_road_network()")
        
        # 转换GPS数据格式
        gps_points = []
        for point_data in gps_data:
            point = GPSPoint(
                latitude=point_data.get('latitude', 0),
                longitude=point_data.get('longitude', 0),
                timestamp=point_data.get('timestamp', 0),
                speed=point_data.get('speed', None),
                direction=point_data.get('direction', None),
                accuracy=point_data.get('accuracy', None)
            )
            gps_points.append(point)
        
        # 执行匹配
        start_time = time.time()
        results = self.algorithm.match_trajectory(gps_points)
        end_time = time.time()
        
        # 转换结果格式
        matched_results = []
        for result in results:
            if result:
                matched_results.append({
                    'gps_point': {
                        'latitude': result.gps_point.latitude,
                        'longitude': result.gps_point.longitude,
                        'timestamp': result.gps_point.timestamp,
                        'speed': result.gps_point.speed,
                        'direction': result.gps_point.direction
                    },
                    'matched_segment': {
                        'segment_id': result.matched_segment.segment_id,
                        'road_name': result.matched_segment.road_name,
                        'road_type': result.matched_segment.road_type
                    },
                    'matched_position': {
                        'latitude': result.matched_lat,
                        'longitude': result.matched_lon
                    },
                    'distance': result.distance,
                    'confidence': result.confidence
                })
        
        # 获取统计信息
        stats = self.algorithm.get_statistics(results)
        
        return {
            'success': True,
            'algorithm_type': self.algorithm_type,
            'total_points': len(gps_points),
            'matched_points': len(matched_results),
            'match_rate': len(matched_results) / len(gps_points) if gps_points else 0,
            'processing_time': end_time - start_time,
            'statistics': stats,
            'results': matched_results
        }
    
    def match_trajectory_from_file(self, file_path: str, file_type: str = 'auto') -> Dict[str, Any]:
        """
        从文件匹配轨迹
        
        Args:
            file_path: 文件路径
            file_type: 文件类型
            
        Returns:
            匹配结果字典
        """
        # 这里应该根据文件类型解析GPS数据
        # 暂时返回空结果，实际实现需要根据具体文件格式解析
        raise NotImplementedError("文件解析功能待实现")
    
    def get_algorithm_info(self) -> Dict[str, Any]:
        """
        获取当前算法信息
        
        Returns:
            算法信息字典
        """
        return {
            'algorithm_type': self.algorithm_type,
            'algorithm_name': self.algorithm.get_algorithm_name(),
            'config': self.config,
            'road_network_loaded': self.road_network_loaded
        }
    
    def switch_algorithm(self, algorithm_type: str, config: Dict[str, Any] = None) -> None:
        """
        切换算法
        
        Args:
            algorithm_type: 新的算法类型
            config: 新的配置参数
        """
        self.algorithm_type = algorithm_type
        self.config = config or get_default_config(algorithm_type)
        self.algorithm = create_matching_algorithm(algorithm_type, self.config)
        self.road_network_loaded = False  # 需要重新加载道路网络
    
    def validate_gps_data(self, gps_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        验证GPS数据
        
        Args:
            gps_data: GPS数据列表
            
        Returns:
            验证结果字典
        """
        if not gps_data:
            return {'valid': False, 'error': 'GPS数据为空'}
        
        errors = []
        warnings = []
        
        for i, point in enumerate(gps_data):
            # 检查必需字段
            if 'latitude' not in point or 'longitude' not in point:
                errors.append(f"点 {i}: 缺少经纬度信息")
                continue
            
            lat = point['latitude']
            lon = point['longitude']
            
            # 检查坐标范围
            if not (-90 <= lat <= 90):
                errors.append(f"点 {i}: 纬度超出范围 {lat}")
            
            if not (-180 <= lon <= 180):
                errors.append(f"点 {i}: 经度超出范围 {lon}")
            
            # 检查速度
            if 'speed' in point and point['speed'] is not None:
                speed = point['speed']
                if speed < 0:
                    warnings.append(f"点 {i}: 速度为负值 {speed}")
                elif speed > 300:  # 300 km/h
                    warnings.append(f"点 {i}: 速度异常高 {speed} km/h")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings,
            'total_points': len(gps_data)
        }