#!/usr/bin/env python3
"""
测试修复后的代码
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent))

def test_imports():
    """测试导入"""
    try:
        print("测试数据模型导入...")
        from DataModels.Models.trajectory import (
            Trajectory, TrajectoryPoint, MatchingTask, MatchedPoint,
            User, RoadNetwork, RoadSegment, File, SystemLog,
            TrajectoryStatus, DataSource, DataCategory, LogLevel
        )
        print("✓ 数据模型导入成功")
        
        print("测试数据模式导入...")
        from DataSchemas.trajectory import (
            TrajectoryCreate, TrajectoryResponse, UserCreate, UserResponse,
            RoadNetworkCreate, RoadNetworkResponse, FileCreate, FileResponse
        )
        print("✓ 数据模式导入成功")
        
        print("测试API端点导入...")
        from ApiEndpoints.health import router as health_router
        from ApiEndpoints.trajectory import router as trajectory_router
        from ApiEndpoints.matching import router as matching_router
        from ApiEndpoints.road_network import router as road_network_router
        from ApiEndpoints.file_management import router as file_management_router
        from ApiEndpoints.origin_destination import router as origin_destination_router
        print("✓ API端点导入成功")
        
        print("测试算法导入...")
        from MatchingAlgorithms.base import MatchingAlgorithm, AlgorithmFactory
        from MatchingAlgorithms.Algorithms.distance_matching import DistanceMatchingAlgorithm
        print("✓ 算法导入成功")
        
        print("测试业务服务导入...")
        from BusinessServices.trajectory_service import TrajectoryService
        from BusinessServices.matching_service import MatchingService
        print("✓ 业务服务导入成功")
        
        print("测试工具导入...")
        from UtilityTools.file_utils import FileProcessor, TrajectoryFileProcessor
        from UtilityTools.validators import DataValidator
        print("✓ 工具导入成功")
        
        print("\n所有导入测试通过！")
        return True
        
    except Exception as e:
        print(f"✗ 导入测试失败: {e}")
        return False

def test_algorithm_creation():
    """测试算法创建"""
    try:
        print("\n测试算法创建...")
        from MatchingAlgorithms.base import create_matching_algorithm
        
        # 创建距离匹配算法
        algorithm = create_matching_algorithm('distance_matching')
        print(f"✓ 创建算法成功: {algorithm.get_algorithm_name()}")
        
        # 测试算法配置
        config = {
            'max_distance': 500,
            'use_speed_filter': True,
            'max_speed': 150
        }
        algorithm_with_config = create_matching_algorithm('distance_matching', config)
        print(f"✓ 创建带配置的算法成功: {algorithm_with_config.get_algorithm_name()}")
        
        return True
        
    except Exception as e:
        print(f"✗ 算法创建测试失败: {e}")
        return False

def test_data_validation():
    """测试数据验证"""
    try:
        print("\n测试数据验证...")
        from UtilityTools.validators import DataValidator
        
        # 测试坐标验证
        assert DataValidator.validate_coordinates(39.9042, 116.4074) == True
        assert DataValidator.validate_coordinates(91, 116.4074) == False
        print("✓ 坐标验证测试通过")
        
        # 测试速度验证
        assert DataValidator.validate_speed(60) == True
        assert DataValidator.validate_speed(300) == False
        print("✓ 速度验证测试通过")
        
        # 测试方向验证
        assert DataValidator.validate_direction(180) == True
        assert DataValidator.validate_direction(400) == False
        print("✓ 方向验证测试通过")
        
        return True
        
    except Exception as e:
        print(f"✗ 数据验证测试失败: {e}")
        return False

def main():
    """主函数"""
    print("开始测试修复后的代码...")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_algorithm_creation,
        test_data_validation
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 50)
    print(f"测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过！代码修复成功！")
        return True
    else:
        print("❌ 部分测试失败，需要进一步修复")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
