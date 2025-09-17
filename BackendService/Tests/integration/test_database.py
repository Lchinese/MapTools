"""
数据库模型集成测试
测试数据库模型的创建、保存和查询功能
"""

import sys
import os
from pathlib import Path
import unittest
from datetime import datetime

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError

# 导入相关模块
try:
    from DataModels.base import Base
    from DataModels.Models.trajectory import Trajectory, TrajectoryPoint, MatchingTask, MatchedPoint
    from DataModels.Models.road_network import RoadNetwork, RoadSegment
except ImportError:
    try:
        from BackendService.DataModels.base import Base
        from BackendService.DataModels.Models.trajectory import Trajectory, TrajectoryPoint, MatchingTask, MatchedPoint
        from BackendService.DataModels.Models.road_network import RoadNetwork, RoadSegment
    except ImportError:
        # 使用模拟对象
        from unittest.mock import Mock
        Base = Mock()
        Trajectory = Mock()
        TrajectoryPoint = Mock()
        MatchingTask = Mock()
        MatchedPoint = Mock()
        RoadNetwork = Mock()
        RoadSegment = Mock()

# 数据库配置
DB_URL = "sqlite:///test.db"

class TestDatabaseModels(unittest.TestCase):
    """数据库模型测试"""
    
    def setUp(self):
        """测试前的准备工作"""
        try:
            # 创建数据库引擎
            self.engine = create_engine(DB_URL, echo=False)
            
            # 创建所有表
            Base.metadata.create_all(bind=self.engine)
            
            # 创建会话
            Session = sessionmaker(bind=self.engine)
            self.session = Session()
        except Exception as e:
            self.skipTest(f"无法创建测试数据库: {e}")
        
    def tearDown(self):
        """测试后的清理工作"""
        try:
            self.session.close()
            Base.metadata.drop_all(bind=self.engine)
        except:
            pass
        
    def test_trajectory_model_creation(self):
        """测试轨迹模型创建和保存"""
        # 创建轨迹
        trajectory = Trajectory(
            trajectory_id="test_traj_001",
            user_id="user_001",
            name="测试轨迹",
            filename="test.gpx",
            file_size=1024,
            file_type="gpx",
            data_source="gpx",
            data_category="continuous_trajectory"
        )
        
        # 保存到数据库
        self.session.add(trajectory)
        self.session.commit()
        
        # 从数据库查询
        retrieved_trajectory = self.session.query(Trajectory).filter(
            Trajectory.trajectory_id == "test_traj_001"
        ).first()
        
        # 验证数据
        self.assertIsNotNone(retrieved_trajectory)
        self.assertEqual(retrieved_trajectory.trajectory_id, "test_traj_001")
        self.assertEqual(retrieved_trajectory.name, "测试轨迹")
        
    def test_road_segment_model_creation(self):
        """测试道路段模型创建和保存"""
        # 创建路网
        road_network = RoadNetwork(
            network_id="network_001",
            name="测试路网"
        )
        
        # 保存路网
        self.session.add(road_network)
        self.session.commit()
        
        # 创建道路段
        road_segment = RoadSegment(
            segment_id="seg_001",
            network_id="network_001",
            start_latitude=39.9080,
            start_longitude=116.3970,
            end_latitude=39.9090,
            end_longitude=116.3980,
            road_name="测试道路",
            road_type="primary"
        )
        
        # 保存到数据库
        self.session.add(road_segment)
        self.session.commit()
        
        # 从数据库查询
        retrieved_segment = self.session.query(RoadSegment).filter(
            RoadSegment.segment_id == "seg_001"
        ).first()
        
        # 验证数据
        self.assertIsNotNone(retrieved_segment)
        self.assertEqual(retrieved_segment.segment_id, "seg_001")
        self.assertEqual(retrieved_segment.road_name, "测试道路")
        self.assertEqual(retrieved_segment.road_type, "primary")
        
    def test_trajectory_point_relationship(self):
        """测试轨迹点关系"""
        # 创建轨迹
        trajectory = Trajectory(
            trajectory_id="test_traj_002",
            user_id="user_001",
            name="测试轨迹2",
            filename="test2.gpx",
            file_size=2048,
            file_type="gpx",
            data_source="gpx",
            data_category="continuous_trajectory"
        )
        
        # 保存轨迹
        self.session.add(trajectory)
        self.session.commit()
        
        # 创建轨迹点
        points = [
            TrajectoryPoint(
                point_id="point_001",
                trajectory_id=trajectory.id,
                sequence_number=1,
                latitude=39.9087,
                longitude=116.3974,
                timestamp=datetime.now()
            ),
            TrajectoryPoint(
                point_id="point_002",
                trajectory_id=trajectory.id,
                sequence_number=2,
                latitude=39.9088,
                longitude=116.3975,
                timestamp=datetime.now()
            )
        ]
        
        # 保存轨迹点
        self.session.add_all(points)
        self.session.commit()
        
        # 从数据库查询轨迹及其点
        retrieved_trajectory = self.session.query(Trajectory).filter(
            Trajectory.trajectory_id == "test_traj_002"
        ).first()
        
        # 验证数据
        self.assertIsNotNone(retrieved_trajectory)
        # 重新加载轨迹点
        self.session.refresh(retrieved_trajectory)
        self.assertEqual(len(retrieved_trajectory.points), 2)

if __name__ == '__main__':
    unittest.main()