"""
集成算法（选举机制）
整合多个地图匹配算法的结果，通过选举机制选择最佳匹配结果
"""

from typing import List, Dict, Any, Tuple
import numpy as np
from ..base import MatchingAlgorithm, GPSPoint, RoadSegment, MatchResult


class EnsembleMatchingAlgorithm(MatchingAlgorithm):
    """集成匹配算法（选举机制）"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        初始化集成匹配算法
        
        Args:
            config: 算法配置参数
                - algorithms: 要使用的算法列表，默认['distance_matching', 'greedy']
                - weights: 各算法的权重，默认均等权重
                - voting_method: 投票方法 ('majority', 'weighted', 'confidence')
                - consensus_threshold: 一致性阈值，默认0.5
        """
        super().__init__(config)
        self.algorithms_config = self.config.get('algorithms', ['distance_matching', 'greedy'])
        self.weights = self.config.get('weights', [1.0/len(self.algorithms_config)] * len(self.algorithms_config))
        self.voting_method = self.config.get('voting_method', 'confidence')  # 'majority', 'weighted', 'confidence'
        self.consensus_threshold = self.config.get('consensus_threshold', 0.5)
        self.algorithm_instances = []
        self.road_segments = []
        
    def load_road_network(self, road_data: List[RoadSegment]) -> None:
        """
        加载道路网络数据到所有算法实例
        
        Args:
            road_data: 道路段数据列表
        """
        self.road_segments = road_data
        
        # 创建并初始化所有算法实例
        self.algorithm_instances = []
        for algo_name in self.algorithms_config:
            try:
                from .. import create_matching_algorithm
                algo_instance = create_matching_algorithm(algo_name, self.config)
                algo_instance.load_road_network(road_data)
                self.algorithm_instances.append(algo_instance)
            except Exception as e:
                print(f"警告: 无法创建算法 {algo_name}: {str(e)}")
        
        print(f"已加载 {len(self.algorithm_instances)} 个算法实例")
    
    def match_trajectory(self, gps_points: List[GPSPoint]) -> List[MatchResult]:
        """
        使用选举机制匹配GPS轨迹到道路网络
        
        Args:
            gps_points: GPS轨迹点列表
            
        Returns:
            匹配结果列表
        """
        if not self.algorithm_instances:
            raise ValueError("没有可用的算法实例，请先调用 load_road_network()")
        
        if not gps_points:
            return []
        
        results = []
        
        # 对每个GPS点进行匹配
        for i, gps_point in enumerate(gps_points):
            # 获取所有算法的匹配结果
            individual_results = []
            for j, algo in enumerate(self.algorithm_instances):
                try:
                    result = self._match_single_point(algo, gps_point)
                    if result:
                        individual_results.append((j, result))
                except Exception as e:
                    print(f"算法 {self.algorithms_config[j]} 匹配点 {i} 失败: {str(e)}")
                    continue
            
            # 使用选举机制选择最佳结果
            if individual_results:
                best_result = self._elect_best_result(individual_results, gps_point)
                if best_result:
                    results.append(best_result)
            else:
                print(f"GPS点 {i} 未获得任何算法的匹配结果")
        
        return results
    
    def _match_single_point(self, algorithm: MatchingAlgorithm, gps_point: GPSPoint) -> MatchResult:
        """
        使用单个算法匹配单个GPS点
        
        Args:
            algorithm: 匹配算法实例
            gps_point: GPS轨迹点
            
        Returns:
            匹配结果
        """
        # 创建一个只包含当前点的列表进行匹配
        results = algorithm.match_trajectory([gps_point])
        return results[0] if results else None
    
    def _elect_best_result(self, results: List[Tuple[int, MatchResult]], gps_point: GPSPoint) -> MatchResult:
        """
        使用选举机制选择最佳匹配结果
        
        Args:
            results: 各算法的匹配结果列表，格式为[(算法索引, 匹配结果), ...]
            gps_point: 原始GPS点
            
        Returns:
            选举出的最佳匹配结果
        """
        if not results:
            return None
            
        if len(results) == 1:
            return results[0][1]
        
        # 根据投票方法选择最佳结果
        if self.voting_method == 'majority':
            return self._majority_voting(results, gps_point)
        elif self.voting_method == 'weighted':
            return self._weighted_voting(results, gps_point)
        elif self.voting_method == 'confidence':
            return self._confidence_voting(results, gps_point)
        else:
            # 默认使用置信度投票
            return self._confidence_voting(results, gps_point)
    
    def _majority_voting(self, results: List[Tuple[int, MatchResult]], gps_point: GPSPoint) -> MatchResult:
        """
        多数投票法：选择获得最多算法支持的道路段
        
        Args:
            results: 各算法的匹配结果列表
            gps_point: 原始GPS点
            
        Returns:
            投票选出的最佳匹配结果
        """
        # 统计各道路段获得的票数
        segment_votes = {}
        for algo_idx, result in results:
            segment_id = result.matched_segment.segment_id
            if segment_id not in segment_votes:
                segment_votes[segment_id] = {
                    'count': 0,
                    'results': []
                }
            segment_votes[segment_id]['count'] += 1
            segment_votes[segment_id]['results'].append((algo_idx, result))
        
        # 找到得票最多的道路段
        max_votes = 0
        best_segment_id = None
        for segment_id, vote_info in segment_votes.items():
            if vote_info['count'] > max_votes:
                max_votes = vote_info['count']
                best_segment_id = segment_id
        
        # 检查是否达到一致性阈值
        total_algorithms = len(self.algorithm_instances)
        consensus_ratio = max_votes / total_algorithms
        if consensus_ratio < self.consensus_threshold:
            # 未达到阈值，使用置信度加权
            return self._confidence_voting(results, gps_point)
        
        # 计算该道路段的平均匹配结果
        best_results = segment_votes[best_segment_id]['results']
        return self._average_results(best_results, gps_point)
    
    def _weighted_voting(self, results: List[Tuple[int, MatchResult]], gps_point: GPSPoint) -> MatchResult:
        """
        加权投票法：根据算法权重选择最佳道路段
        
        Args:
            results: 各算法的匹配结果列表
            gps_point: 原始GPS点
            
        Returns:
            投票选出的最佳匹配结果
        """
        # 统计各道路段的加权票数
        segment_votes = {}
        for algo_idx, result in results:
            segment_id = result.matched_segment.segment_id
            weight = self.weights[algo_idx] if algo_idx < len(self.weights) else 1.0/len(results)
            
            if segment_id not in segment_votes:
                segment_votes[segment_id] = {
                    'weighted_count': 0,
                    'results': []
                }
            segment_votes[segment_id]['weighted_count'] += weight
            segment_votes[segment_id]['results'].append((algo_idx, result))
        
        # 找到加权票数最多的道路段
        max_weighted_votes = 0
        best_segment_id = None
        for segment_id, vote_info in segment_votes.items():
            if vote_info['weighted_count'] > max_weighted_votes:
                max_weighted_votes = vote_info['weighted_count']
                best_segment_id = segment_id
        
        # 计算该道路段的平均匹配结果
        best_results = segment_votes[best_segment_id]['results']
        return self._average_results(best_results, gps_point)
    
    def _confidence_voting(self, results: List[Tuple[int, MatchResult]], gps_point: GPSPoint) -> MatchResult:
        """
        置信度投票法：根据匹配置信度选择最佳道路段
        
        Args:
            results: 各算法的匹配结果列表
            gps_point: 原始GPS点
            
        Returns:
            投票选出的最佳匹配结果
        """
        # 计算各道路段的置信度加权得分
        segment_scores = {}
        for algo_idx, result in results:
            segment_id = result.matched_segment.segment_id
            weight = self.weights[algo_idx] if algo_idx < len(self.weights) else 1.0/len(results)
            confidence = result.confidence
            
            if segment_id not in segment_scores:
                segment_scores[segment_id] = {
                    'total_score': 0,
                    'total_weight': 0,
                    'results': []
                }
            segment_scores[segment_id]['total_score'] += confidence * weight
            segment_scores[segment_id]['total_weight'] += weight
            segment_scores[segment_id]['results'].append((algo_idx, result))
        
        # 找到得分最高的道路段
        max_score = 0
        best_segment_id = None
        for segment_id, score_info in segment_scores.items():
            avg_score = score_info['total_score'] / score_info['total_weight']
            if avg_score > max_score:
                max_score = avg_score
                best_segment_id = segment_id
        
        # 计算该道路段的平均匹配结果
        best_results = segment_scores[best_segment_id]['results']
        return self._average_results(best_results, gps_point)
    
    def _average_results(self, results: List[Tuple[int, MatchResult]], gps_point: GPSPoint) -> MatchResult:
        """
        对多个匹配结果进行平均，生成最终结果
        
        Args:
            results: 同一道路段的匹配结果列表
            gps_point: 原始GPS点
            
        Returns:
            平均后的匹配结果
        """
        if not results:
            return None
        
        # 计算各项指标的平均值
        total_distance = sum(r.distance for _, r in results)
        total_confidence = sum(r.confidence for _, r in results)
        total_matched_lat = sum(r.matched_lat for _, r in results)
        total_matched_lon = sum(r.matched_lon for _, r in results)
        
        count = len(results)
        avg_distance = total_distance / count
        avg_confidence = total_confidence / count
        avg_matched_lat = total_matched_lat / count
        avg_matched_lon = total_matched_lon / count
        
        # 使用第一个结果的道路段信息（它们应该是相同的）
        matched_segment = results[0][1].matched_segment
        
        # 创建最终结果
        final_result = MatchResult(
            gps_point=gps_point,
            matched_segment=matched_segment,
            matched_lat=avg_matched_lat,
            matched_lon=avg_matched_lon,
            distance=avg_distance,
            confidence=avg_confidence
        )
        
        return final_result
    
    def get_algorithm_name(self) -> str:
        """获取算法名称"""
        return "EnsembleMatching"
    
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