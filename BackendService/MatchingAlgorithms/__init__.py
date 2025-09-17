"""
算法模块
提供可插拔的地图匹配算法实现
"""

from .base import (
    MatchingAlgorithm,
    AlgorithmFactory,
    create_matching_algorithm
)

# 注册所有可用的算法
def _register_algorithms():
    """注册所有可用的算法"""
    try:
        from .Algorithms.distance_matching import DistanceMatchingAlgorithm
        AlgorithmFactory.register_algorithm('distance_matching', DistanceMatchingAlgorithm)
    except ImportError:
        pass  # 如果算法模块不存在，跳过注册
        
    try:
        from .Algorithms.greedy_algorithm import GreedyMatchingAlgorithm
        AlgorithmFactory.register_algorithm('greedy', GreedyMatchingAlgorithm)
    except ImportError:
        pass  # 如果算法模块不存在，跳过注册
        
    try:
        from .Algorithms.gotrackit_adapter import GoTrackItAdapter
        AlgorithmFactory.register_algorithm('gotrackit', GoTrackItAdapter)
    except ImportError:
        pass  # 如果算法模块不存在，跳过注册
        
    try:
        from .Algorithms.ensemble_algorithm import EnsembleMatchingAlgorithm
        AlgorithmFactory.register_algorithm('ensemble', EnsembleMatchingAlgorithm)
    except ImportError:
        pass  # 如果算法模块不存在，跳过注册


# 自动注册算法
_register_algorithms()

__all__ = [
    "MatchingAlgorithm",
    "AlgorithmFactory",
    "create_matching_algorithm"
]

__version__ = "0.1.0"