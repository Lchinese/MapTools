"""
算法实现目录
包含各种地图匹配算法的具体实现
"""

# 导入具体算法实现
from .distance_matching import DistanceMatchingAlgorithm
from .greedy_algorithm import GreedyMatchingAlgorithm
from .gotrackit_adapter import GoTrackItAdapter
from .ensemble_algorithm import EnsembleMatchingAlgorithm

__all__ = [
    "DistanceMatchingAlgorithm",
    "GreedyMatchingAlgorithm",
    "GoTrackItAdapter",
    "EnsembleMatchingAlgorithm"
]

__version__ = "0.1.0"