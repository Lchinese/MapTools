"""
地图匹配算法基类和工厂
定义所有匹配算法必须实现的接口，并提供算法创建和管理功能
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Tuple, Type
import numpy as np
from dataclasses import dataclass


@dataclass
class GPSPoint:
    """GPS轨迹点数据结构"""
    latitude: float
    longitude: float
    timestamp: float
    speed: float = None
    direction: float = None
    accuracy: float = None


@dataclass
class RoadSegment:
    """道路段数据结构"""
    segment_id: str
    start_lat: float
    start_lon: float
    end_lat: float
    end_lon: float
    road_name: str = None
    road_type: str = None
    max_speed: float = None


@dataclass
class MatchResult:
    """匹配结果数据结构"""
    gps_point: GPSPoint
    matched_segment: RoadSegment
    matched_lat: float
    matched_lon: float
    distance: float
    confidence: float


class MatchingAlgorithm(ABC):
    """地图匹配算法基类"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        初始化算法
        
        Args:
            config: 算法配置参数
        """
        self.config = config or {}
        self.road_network = None
    
    @abstractmethod
    def load_road_network(self, road_data: List[RoadSegment]) -> None:
        """
        加载道路网络数据
        
        Args:
            road_data: 道路段数据列表
        """
        pass
    
    @abstractmethod
    def match_trajectory(self, gps_points: List[GPSPoint]) -> List[MatchResult]:
        """
        匹配GPS轨迹到道路网络
        
        Args:
            gps_points: GPS轨迹点列表
            
        Returns:
            匹配结果列表
        """
        pass
    
    @abstractmethod
    def get_algorithm_name(self) -> str:
        """
        获取算法名称
        
        Returns:
            算法名称
        """
        pass
    
    def calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        计算两点间的距离（米）
        使用Haversine公式计算球面距离
        
        Args:
            lat1, lon1: 第一个点的纬度和经度
            lat2, lon2: 第二个点的纬度和经度
            
        Returns:
            距离（米）
        """
        from math import radians, cos, sin, asin, sqrt
        
        # 将十进制度数转化为弧度
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        
        # Haversine公式
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))
        
        # 地球半径（米）
        r = 6371000
        return c * r
    
    def point_to_segment_distance(self, point_lat: float, point_lon: float, 
                                 segment: RoadSegment) -> Tuple[float, float, float]:
        """
        计算点到线段的最短距离
        
        Args:
            point_lat, point_lon: 点的坐标
            segment: 道路段
            
        Returns:
            (最短距离, 匹配点纬度, 匹配点经度)
        """
        # 将线段端点坐标
        A_lat, A_lon = segment.start_lat, segment.start_lon
        B_lat, B_lon = segment.end_lat, segment.end_lon
        P_lat, P_lon = point_lat, point_lon
        
        # 计算向量
        AB_lat = B_lat - A_lat
        AB_lon = B_lon - A_lon
        AP_lat = P_lat - A_lat
        AP_lon = P_lon - A_lon
        
        # 计算投影参数t
        AB_dot_AB = AB_lat * AB_lat + AB_lon * AB_lon
        if AB_dot_AB == 0:
            # 线段退化为点
            return self.calculate_distance(P_lat, P_lon, A_lat, A_lon), A_lat, A_lon
        
        AB_dot_AP = AB_lat * AP_lat + AB_lon * AP_lon
        t = max(0, min(1, AB_dot_AP / AB_dot_AB))
        
        # 计算投影点坐标
        proj_lat = A_lat + t * AB_lat
        proj_lon = A_lon + t * AB_lon
        
        # 计算距离
        distance = self.calculate_distance(P_lat, P_lon, proj_lat, proj_lon)
        
        return distance, proj_lat, proj_lon


class AlgorithmFactory:
    """算法工厂类"""
    
    # 注册的算法类型
    _algorithms: Dict[str, Type['MatchingAlgorithm']] = {}
    
    @classmethod
    def create_algorithm(cls, algorithm_type: str, config: Dict[str, Any] = None) -> 'MatchingAlgorithm':
        """
        创建指定类型的算法实例
        
        Args:
            algorithm_type: 算法类型
            config: 算法配置参数
            
        Returns:
            算法实例
            
        Raises:
            ValueError: 不支持的算法类型
        """
        if algorithm_type not in cls._algorithms:
            available_types = ', '.join(cls._algorithms.keys())
            raise ValueError(f"不支持的算法类型: {algorithm_type}. 可用类型: {available_types}")
        
        algorithm_class = cls._algorithms[algorithm_type]
        return algorithm_class(config)
    
    @classmethod
    def get_available_algorithms(cls) -> list:
        """
        获取所有可用的算法类型
        
        Returns:
            算法类型列表
        """
        return list(cls._algorithms.keys())
    
    @classmethod
    def register_algorithm(cls, algorithm_type: str, algorithm_class: Type['MatchingAlgorithm']):
        """
        注册新的算法类型
        
        Args:
            algorithm_type: 算法类型名称
            algorithm_class: 算法类
        """
        cls._algorithms[algorithm_type] = algorithm_class
    
    @classmethod
    def get_algorithm_info(cls, algorithm_type: str) -> Dict[str, Any]:
        """
        获取算法信息
        
        Args:
            algorithm_type: 算法类型
            
        Returns:
            算法信息字典
        """
        if algorithm_type not in cls._algorithms:
            return {}
        
        algorithm_class = cls._algorithms[algorithm_type]
        
        # 创建临时实例获取算法名称
        temp_instance = algorithm_class()
        
        return {
            'type': algorithm_type,
            'name': temp_instance.get_algorithm_name(),
            'class': algorithm_class.__name__,
            'module': algorithm_class.__module__
        }


def create_matching_algorithm(algorithm_type: str = 'distance_matching', 
                            config: Dict[str, Any] = None) -> 'MatchingAlgorithm':
    """
    便捷函数：创建地图匹配算法
    
    Args:
        algorithm_type: 算法类型，默认为 'distance_matching'
        config: 算法配置参数
        
    Returns:
        算法实例
    """
    return AlgorithmFactory.create_algorithm(algorithm_type, config)


# 默认配置
DEFAULT_CONFIGS = {
    'distance_matching': {
        'max_distance': 1000,  # 最大匹配距离1000米
        'use_speed_filter': True,
        'max_speed': 200  # 最大合理速度200km/h
    },
    # 未来可以添加其他算法的默认配置
}


def get_default_config(algorithm_type: str) -> Dict[str, Any]:
    """
    获取算法的默认配置
    
    Args:
        algorithm_type: 算法类型
        
    Returns:
        默认配置字典
    """
    return DEFAULT_CONFIGS.get(algorithm_type, {})


# 延迟导入，避免循环依赖
def _register_algorithms():
    """注册所有可用的算法"""
    try:
        from .Algorithms.distance_matching import DistanceMatchingAlgorithm
        AlgorithmFactory.register_algorithm('distance_matching', DistanceMatchingAlgorithm)
    except ImportError:
        pass  # 如果算法模块不存在，跳过注册


# 自动注册算法
_register_algorithms()