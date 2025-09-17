"""
GoTrackIt 适配器
适配GoTrackIt地图匹配算法的接口
"""

from typing import List, Dict, Any
import numpy as np
from ..base import MatchingAlgorithm, GPSPoint, RoadSegment, MatchResult


class GoTrackItAdapter(MatchingAlgorithm):
    """GoTrackIt算法适配器"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        初始化GoTrackIt适配器
        
        Args:
            config: 算法配置参数
                - max_distance: 最大匹配距离（米），默认1000
                - use_speed_filter: 是否使用速度过滤，默认True
                - max_speed: 最大合理速度（km/h），默认200
                - transition_probability_threshold: 转移概率阈值，默认0.1
        """
        super().__init__(config)
        self.max_distance = self.config.get('max_distance', 1000)  # 最大匹配距离1000米
        self.use_speed_filter = self.config.get('use_speed_filter', True)
        self.max_speed = self.config.get('max_speed', 200)  # 最大合理速度200km/h
        self.transition_threshold = self.config.get('transition_probability_threshold', 0.1)
        self.road_segments = []
        self.segment_graph = {}  # 道路段连接图
        
    def load_road_network(self, road_data: List[RoadSegment]) -> None:
        """
        加载道路网络数据并构建连接图
        
        Args:
            road_data: 道路段数据列表
        """
        self.road_segments = road_data
        self._build_segment_graph()
        print(f"已加载 {len(self.road_segments)} 条道路段，并构建连接图")
    
    def _build_segment_graph(self) -> None:
        """
        构建道路段连接图
        """
        # 初始化连接图
        self.segment_graph = {segment.segment_id: [] for segment in self.road_segments}
        
        # 构建连接关系
        for i, seg1 in enumerate(self.road_segments):
            for j, seg2 in enumerate(self.road_segments):
                if i != j:
                    # 检查是否连接（共享端点）
                    if self._segments_connected(seg1, seg2):
                        self.segment_graph[seg1.segment_id].append(seg2.segment_id)
    
    def _segments_connected(self, seg1: RoadSegment, seg2: RoadSegment) -> bool:
        """
        检查两个道路段是否连接
        
        Args:
            seg1: 第一个道路段
            seg2: 第二个道路段
            
        Returns:
            是否连接
        """
        # 检查是否共享端点
        return (abs(seg1.start_lat - seg2.start_lat) < 1e-6 and 
                abs(seg1.start_lon - seg2.start_lon) < 1e-6) or \
               (abs(seg1.start_lat - seg2.end_lat) < 1e-6 and 
                abs(seg1.start_lon - seg2.end_lon) < 1e-6) or \
               (abs(seg1.end_lat - seg2.start_lat) < 1e-6 and 
                abs(seg1.end_lon - seg2.start_lon) < 1e-6) or \
               (abs(seg1.end_lat - seg2.end_lat) < 1e-6 and 
                abs(seg1.end_lon - seg2.end_lon) < 1e-6)
    
    def match_trajectory(self, gps_points: List[GPSPoint]) -> List[MatchResult]:
        """
        使用GoTrackIt算法匹配GPS轨迹到道路网络
        
        Args:
            gps_points: GPS轨迹点列表
            
        Returns:
            匹配结果列表
        """
        if not self.road_segments:
            raise ValueError("道路网络未加载，请先调用 load_road_network()")
        
        if not gps_points:
            return []
        
        # 初始化结果列表
        results = []
        
        # 计算每个点到所有道路段的观测概率
        observation_probs = self._calculate_observation_probabilities(gps_points)
        
        # 计算道路段之间的转移概率
        transition_probs = self._calculate_transition_probabilities()
        
        # 使用Viterbi算法进行匹配
        best_path = self._viterbi_algorithm(gps_points, observation_probs, transition_probs)
        
        # 根据最佳路径生成匹配结果
        for i, segment_id in enumerate(best_path):
            if segment_id is not None:
                segment = self._get_segment_by_id(segment_id)
                if segment:
                    gps_point = gps_points[i]
                    distance, proj_lat, proj_lon = self.point_to_segment_distance(
                        gps_point.latitude, gps_point.longitude, segment
                    )
                    
                    # 计算置信度
                    confidence = observation_probs[i].get(segment_id, 0)
                    
                    result = MatchResult(
                        gps_point=gps_point,
                        matched_segment=segment,
                        matched_lat=proj_lat,
                        matched_lon=proj_lon,
                        distance=distance,
                        confidence=confidence
                    )
                    results.append(result)
        
        return results
    
    def _calculate_observation_probabilities(self, gps_points: List[GPSPoint]) -> List[Dict[str, float]]:
        """
        计算每个GPS点对各道路段的观测概率
        
        Args:
            gps_points: GPS轨迹点列表
            
        Returns:
            观测概率列表，每个元素是一个字典，键为道路段ID，值为概率
        """
        observation_probs = []
        
        for gps_point in gps_points:
            probs = {}
            total_prob = 0
            
            # 速度过滤
            if self.use_speed_filter and gps_point.speed is not None:
                if gps_point.speed > self.max_speed:
                    # 异常速度点，所有道路段概率为0
                    observation_probs.append({})
                    continue
            
            # 计算每个道路段的观测概率
            for segment in self.road_segments:
                distance, _, _ = self.point_to_segment_distance(
                    gps_point.latitude, gps_point.longitude, segment
                )
                
                # 基于距离计算观测概率（高斯分布）
                if distance <= self.max_distance:
                    prob = np.exp(-0.5 * (distance / (self.max_distance / 3)) ** 2)
                    probs[segment.segment_id] = prob
                    total_prob += prob
            
            # 归一化概率
            if total_prob > 0:
                for segment_id in probs:
                    probs[segment_id] /= total_prob
            
            observation_probs.append(probs)
        
        return observation_probs
    
    def _calculate_transition_probabilities(self) -> Dict[str, Dict[str, float]]:
        """
        计算道路段之间的转移概率
        
        Returns:
            转移概率字典，格式为 {from_segment_id: {to_segment_id: probability}}
        """
        transition_probs = {}
        
        for from_segment in self.road_segments:
            from_id = from_segment.segment_id
            transition_probs[from_id] = {}
            
            # 获取连接的道路段
            connected_segments = self.segment_graph.get(from_id, [])
            
            if connected_segments:
                # 均匀分配概率到连接的道路段
                prob = 1.0 / len(connected_segments)
                for to_segment_id in connected_segments:
                    transition_probs[from_id][to_segment_id] = prob
            else:
                # 如果没有连接的道路段，则转移到所有道路段的概率相等
                prob = 1.0 / len(self.road_segments) if self.road_segments else 0
                for segment in self.road_segments:
                    transition_probs[from_id][segment.segment_id] = prob
        
        return transition_probs
    
    def _viterbi_algorithm(self, gps_points: List[GPSPoint], 
                          observation_probs: List[Dict[str, float]], 
                          transition_probs: Dict[str, Dict[str, float]]) -> List[str]:
        """
        Viterbi算法实现，用于找到最佳匹配路径
        
        Args:
            gps_points: GPS轨迹点列表
            observation_probs: 观测概率
            transition_probs: 转移概率
            
        Returns:
            最佳道路段路径列表
        """
        if not gps_points or not observation_probs:
            return []
        
        n_points = len(gps_points)
        n_segments = len(self.road_segments)
        
        if n_points == 0 or n_segments == 0:
            return []
        
        # 初始化Viterbi表和路径表
        viterbi = [{} for _ in range(n_points)]
        path = [{} for _ in range(n_points)]
        
        # 初始化第一个点
        for segment in self.road_segments:
            segment_id = segment.segment_id
            obs_prob = observation_probs[0].get(segment_id, 0)
            viterbi[0][segment_id] = obs_prob  # 初始状态概率设为观测概率
        
        # 动态规划填表
        for t in range(1, n_points):
            for segment in self.road_segments:
                segment_id = segment.segment_id
                max_prob = 0
                best_prev_segment = None
                
                # 查找最佳的前一状态
                for prev_segment in self.road_segments:
                    prev_segment_id = prev_segment.segment_id
                    if prev_segment_id in viterbi[t-1]:
                        # 计算转移概率
                        trans_prob = transition_probs.get(prev_segment_id, {}).get(segment_id, 0)
                        # 如果转移概率太小，跳过
                        if trans_prob < self.transition_threshold:
                            continue
                            
                        # 计算概率
                        prob = viterbi[t-1][prev_segment_id] * trans_prob
                        
                        if prob > max_prob:
                            max_prob = prob
                            best_prev_segment = prev_segment_id
                
                # 计算当前状态的概率
                obs_prob = observation_probs[t].get(segment_id, 0)
                viterbi[t][segment_id] = max_prob * obs_prob
                path[t][segment_id] = best_prev_segment
        
        # 回溯找到最佳路径
        best_path = [None] * n_points
        # 找到最后一个点的最佳状态
        max_prob = 0
        best_last_segment = None
        for segment in self.road_segments:
            segment_id = segment.segment_id
            if viterbi[n_points-1].get(segment_id, 0) > max_prob:
                max_prob = viterbi[n_points-1][segment_id]
                best_last_segment = segment_id
        
        if best_last_segment is not None:
            best_path[n_points-1] = best_last_segment
            
            # 回溯路径
            for t in range(n_points-2, -1, -1):
                best_path[t] = path[t+1][best_path[t+1]]
        
        return best_path
    
    def _get_segment_by_id(self, segment_id: str) -> RoadSegment:
        """
        根据ID获取道路段
        
        Args:
            segment_id: 道路段ID
            
        Returns:
            道路段对象，如果未找到则返回None
        """
        for segment in self.road_segments:
            if segment.segment_id == segment_id:
                return segment
        return None
    
    def get_algorithm_name(self) -> str:
        """获取算法名称"""
        return "GoTrackIt"
    
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