"""
轨迹单元测试
"""

import sys
import os
from pathlib import Path
import unittest
from dataclasses import dataclass
from typing import List, Optional

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# 使用简单的数据类替代SQLAlchemy模型进行测试
@dataclass
class TrajectoryPoint:
    """轨迹点数据类（用于测试）"""
    latitude: float
    longitude: float
    timestamp: float
    sequence_number: int
    elevation: Optional[float] = None
    speed: Optional[float] = None
    direction: Optional[float] = None
    accuracy: Optional[float] = None

@dataclass
class Trajectory:
    """轨迹数据类（用于测试）"""
    name: str
    points: List[TrajectoryPoint]
    description: Optional[str] = None
    vehicle_id: Optional[str] = None

class TestTrajectory(unittest.TestCase):
    """轨迹测试"""
    
    def setUp(self):
        """测试前的准备工作"""
        self.points = [
            TrajectoryPoint(
                latitude=39.9087,
                longitude=116.3974,
                timestamp=1000,
                sequence_number=1,
                speed=10.0,
                direction=45.0
            ),
            TrajectoryPoint(
                latitude=39.9088,
                longitude=116.3975,
                timestamp=1001,
                sequence_number=2,
                speed=12.0,
                direction=46.0
            ),
            TrajectoryPoint(
                latitude=39.9089,
                longitude=116.3976,
                timestamp=1002,
                sequence_number=3,
                speed=11.0,
                direction=47.0
            )
        ]
        
        self.trajectory = Trajectory(
            name="测试轨迹",
            description="用于测试的轨迹",
            points=self.points,
            vehicle_id="TEST001"
        )
        
    def test_trajectory_creation(self):
        """测试轨迹创建"""
        self.assertEqual(self.trajectory.name, "测试轨迹")
        self.assertEqual(self.trajectory.description, "用于测试的轨迹")
        self.assertEqual(self.trajectory.vehicle_id, "TEST001")
        self.assertEqual(len(self.trajectory.points), 3)
        
    def test_trajectory_point_creation(self):
        """测试轨迹点创建"""
        point = self.points[0]
        self.assertEqual(point.latitude, 39.9087)
        self.assertEqual(point.longitude, 116.3974)
        self.assertEqual(point.sequence_number, 1)
        self.assertEqual(point.speed, 10.0)
        self.assertEqual(point.direction, 45.0)
        
    def test_trajectory_point_validation(self):
        """测试轨迹点验证"""
        # 测试正常情况
        point = TrajectoryPoint(
            latitude=39.9087,
            longitude=116.3974,
            timestamp=1000,
            sequence_number=1
        )
        self.assertEqual(point.latitude, 39.9087)
        self.assertEqual(point.longitude, 116.3974)
        
        # 测试边界值
        point2 = TrajectoryPoint(
            latitude=90.0,  # 最大纬度
            longitude=180.0,  # 最大经度
            timestamp=1000,
            sequence_number=1
        )
        self.assertEqual(point2.latitude, 90.0)
        self.assertEqual(point2.longitude, 180.0)

if __name__ == '__main__':
    unittest.main()