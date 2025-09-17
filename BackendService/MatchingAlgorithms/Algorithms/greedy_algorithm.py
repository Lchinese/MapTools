"""
最近邻算法（贪心算法）
基于轨迹点的连续性和道路网络拓扑结构进行匹配
"""

from typing import List, Dict, Any
import numpy as np
from ..base import MatchingAlgorithm, GPSPoint, RoadSegment, MatchResult


class GreedyMatchingAlgorithm(MatchingAlgorithm):
    """最近邻匹配算法"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        初始化最近邻匹配算法
        
        Args:
            config: 算法配置参数
                - max_distance: 最大匹配距离（米），默认1000
                - use_speed_filter: 是否使用速度过滤，默认True
                - max_speed: 最大合理速度（km/h），默认200
                - use_topology: 是否使用道路拓扑信息，默认True
        """
        super().__init__(config)
        self.max_distance = self.config.get('max_distance', 1000)  # 最大匹配距离1000米
        self.use_speed_filter = self.config.get('use_speed_filter', True)
        self.max_speed = self.config.get('max_speed', 200)  # 最大合理速度200km/h
        self.use_topology = self.config.get('use_topology', True)  # 使用道路拓扑信息
        self.road_segments = []
        self.last_matched_segment = None  # 上一个匹配的道路段
        
    def load_road_network(self, road_data: List[RoadSegment]) -> None:
        """
        加载道路网络数据
        
        Args:
            road_data: 道路段数据列表
        """
        self.road_segments = road_data
        print(f"已加载 {len(self.road_segments)} 条道路段")
    
    def match_trajectory(self, gps_points: List[GPSPoint]) -> List[MatchResult]:
        """
        匹配GPS轨迹到道路网络（使用贪心算法）
        
        Args:
            gps_points: GPS轨迹点列表
            
        Returns:
            匹配结果列表
        """
        if not self.road_segments:
            raise ValueError("道路网络未加载，请先调用 load_road_network()")
        
        results = []
        self.last_matched_segment = None  # 重置上一个匹配段
        
        for i, gps_point in enumerate(gps_points):
            # 速度过滤
            if self.use_speed_filter and gps_point.speed is not None:
                if gps_point.speed > self.max_speed:
                    print(f"跳过异常速度点: {gps_point.speed} km/h")
                    continue
            
            # 寻找最佳匹配的道路段
            best_match = self._find_best_segment(gps_point, i)
            
            if best_match:
                results.append(best_match)
                self.last_matched_segment = best_match.matched_segment
            else:
                print(f"GPS点 {i} 未找到匹配的道路段")
        
        return results
    
    def _find_best_segment(self, gps_point: GPSPoint, point_index: int) -> MatchResult:
        """
        为单个GPS点找到最佳匹配的道路段（考虑拓扑连续性）
        
        Args:
            gps_point: GPS轨迹点
            point_index: 点的索引
            
        Returns:
            匹配结果，如果未找到则返回None
        """
        min_distance = float('inf')
        best_segment = None
        best_proj_lat = None
        best_proj_lon = None
        
        # 如果使用拓扑信息且有上一个匹配段，则优先考虑邻近段
        candidate_segments = self.road_segments
        if self.use_topology and self.last_matched_segment and point_index > 0:
            # 获取与上一个匹配段连接的候选段
            connected_segments = self._get_connected_segments(self.last_matched_segment)
            if connected_segments:
                candidate_segments = connected_segments
        
        # 在候选段中寻找
        for segment in candidate_segments:
            # 计算点到线段的最短距离
            distance, proj_lat, proj_lon = self.point_to_segment_distance(
                gps_point.latitude, gps_point.longitude, segment
            )
            
            # 更新最近距离
            if distance < min_distance:
                min_distance = distance
                best_segment = segment
                best_proj_lat = proj_lat
                best_proj_lon = proj_lon
        
        # 检查是否在最大匹配距离内
        if min_distance <= self.max_distance:
            # 计算置信度（距离越近置信度越高）
            confidence = max(0, 1 - min_distance / self.max_distance)
            
            return MatchResult(
                gps_point=gps_point,
                matched_segment=best_segment,
                matched_lat=best_proj_lat,
                matched_lon=best_proj_lon,
                distance=min_distance,
                confidence=confidence
            )
        else:
            return None
    
    def _get_connected_segments(self, segment: RoadSegment) -> List[RoadSegment]:
        """
        获取与指定道路段连接的邻近段
        
        Args:
            segment: 道路段
            
        Returns:
            连接的道路段列表
        """
        connected = []
        for seg in self.road_segments:
            # 检查是否与当前段连接（共享端点）
            if (abs(seg.start_lat - segment.start_lat) < 1e-6 and 
                abs(seg.start_lon - segment.start_lon) < 1e-6) or \
               (abs(seg.start_lat - segment.end_lat) < 1e-6 and 
                abs(seg.start_lon - segment.end_lon) < 1e-6) or \
               (abs(seg.end_lat - segment.start_lat) < 1e-6 and 
                abs(seg.end_lon - segment.start_lon) < 1e-6) or \
               (abs(seg.end_lat - segment.end_lat) < 1e-6 and 
                abs(seg.end_lon - segment.end_lon) < 1e-6):
                connected.append(seg)
        
        return connected
    
    def get_algorithm_name(self) -> str:
        """获取算法名称"""
        return "GreedyMatching"
    
    def get_statistics(self, results: List[MatchResult]) -> Dict[str, Any]:
        """
        获取匹配统计信息
        
        Args:
            results: 匹配结果列表
            
        Returns:
            统计信息字典
        """
        if not results:
            return {
                "total_points": 0,
                "matched_points": 0,
                "match_rate": 0,
                "avg_distance": 0,
                "avg_confidence": 0
            }
        
        total_points = len(results)
        matched_points = len([r for r in results if r is not None])
        match_rate = matched_points / total_points if total_points > 0 else 0
        
        distances = [r.distance for r in results if r is not None]
        confidences = [r.confidence for r in results if r is not None]
        
        return {
            "total_points": total_points,
            "matched_points": matched_points,
            "match_rate": match_rate,
            "avg_distance": np.mean(distances) if distances else 0,
            "avg_confidence": np.mean(confidences) if confidences else 0,
            "min_distance": np.min(distances) if distances else 0,
            "max_distance": np.max(distances) if distances else 0
        }