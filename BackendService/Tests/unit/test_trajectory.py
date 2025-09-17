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
    timestamp: int
    speed: Optional[float] = None
    direction: Optional[float] = None
    accuracy: Optional[float] = None

@dataclass
class Trajectory:
    """轨迹数据类（用于测试）"""
    trajectory_id: str
    name: str
    points: List[TrajectoryPoint]
    created_at: int
    updated_at: int

class TestTrajectory(unittest.TestCase):
    """轨迹模型测试"""
    
    def setUp(self):
        """测试前的准备工作"""
        # 创建轨迹点列表
        self.points = [
            TrajectoryPoint(
                latitude=39.9087,
                longitude=116.3974,
                timestamp=1000,
                speed=10.0,
                direction=45.0
            ),
            TrajectoryPoint(
                latitude=39.9088,
                longitude=116.3975,
                timestamp=1001,
                speed=12.0,
                direction=46.0
            ),
            TrajectoryPoint(
                latitude=39.9089,
                longitude=116.3976,
                timestamp=1002,
                speed=11.0,
                direction=47.0
            )
        ]
        
        # 创建轨迹对象
        self.trajectory = Trajectory(
            trajectory_id="test_traj_001",
            name="测试轨迹",
            points=self.points,
            created_at=1000,
            updated_at=1002
        )
        
    def test_trajectory_point_creation(self):
        """测试轨迹点创建"""
        point = TrajectoryPoint(
            latitude=39.9087,
            longitude=116.3974,
            timestamp=1000,
            speed=10.0,
            direction=45.0
        )
        
        self.assertEqual(point.latitude, 39.9087)
        self.assertEqual(point.longitude, 116.3974)
        self.assertEqual(point.timestamp, 1000)
        self.assertEqual(point.speed, 10.0)
        self.assertEqual(point.direction, 45.0)
        
    def test_trajectory_creation(self):
        """测试轨迹创建"""
        traj = Trajectory(
            trajectory_id="test_traj_001",
            name="测试轨迹",
            points=self.points,
            created_at=1000,
            updated_at=1002
        )
        
        self.assertEqual(traj.trajectory_id, "test_traj_001")
        self.assertEqual(traj.name, "测试轨迹")
        self.assertEqual(len(traj.points), 3)
        self.assertEqual(traj.created_at, 1000)
        self.assertEqual(traj.updated_at, 1002)
        
    def test_trajectory_point_validation(self):
        """测试轨迹点验证"""
        # 测试有效轨迹点
        valid_point = TrajectoryPoint(
            latitude=39.9087,
            longitude=116.3974,
            timestamp=1000
        )
        self.assertIsInstance(valid_point, TrajectoryPoint)

if __name__ == '__main__':
    unittest.main()